"""Audio capture pipeline with VAD, echo cancellation, and Push-to-Talk support."""

import queue
import threading
import time
from typing import Callable, Optional

import numpy as np

try:
    import pyaudio
    _PYAUDIO_AVAILABLE = True
except ImportError:
    _PYAUDIO_AVAILABLE = False
    pyaudio = None  # type: ignore

try:
    from pynput import keyboard
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False
    keyboard = None  # type: ignore

# Colors for terminal output
COLOR_GREEN = "\033[92m"
COLOR_BLUE = "\033[94m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


class AudioPipeline:
    """Audio capture pipeline with VAD and echo cancellation."""

    def __init__(self, config: dict, on_speech_callback: Callable[[np.ndarray], None]):
        """
        Initialize audio pipeline.

        Args:
            config: Configuration dict with audio settings
            on_speech_callback: Callback function called when speech is detected
        """
        if not _PYAUDIO_AVAILABLE:
            raise ImportError("PyAudio não está instalado. Instale com: pip install PyAudio")

        self.config = config
        self.on_speech_callback = on_speech_callback

        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.chunk_size = config.get("chunk_size", 4096)
        self.silence_threshold = config.get("silence_threshold", 500)
        self.max_silence_chunks = config.get("max_silence_chunks", 30)
        self.min_speech_duration = config.get("min_speech_duration", 0.5)

        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.is_running = False
        self._is_speaking = False
        self._stream: Optional[pyaudio.Stream] = None
        self._pa: Optional[pyaudio.PyAudio] = None
        self._processing_thread: Optional[threading.Thread] = None

        # Speech detection state
        self._speech_buffer: list[np.ndarray] = []
        self._silence_counter = 0
        self._in_speech = False

    def set_speaking(self, state: bool) -> None:
        """
        Set speaking state for echo cancellation.

        Args:
            state: True if TTS is currently speaking
        """
        self._is_speaking = state
        if state:
            # Clear queue when starting to speak (discard stale audio)
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
        else:
            # Small delay after speaking stops (anti-echo)
            time.sleep(0.5)

    def _audio_callback(self, in_data: bytes, frame_count: int, time_info: dict, status: int):
        """PyAudio callback - called for each audio chunk."""
        if self._is_speaking:
            # Discard audio while TTS is speaking (echo cancellation)
            return (None, pyaudio.paContinue)

        try:
            self.audio_queue.put_nowait(in_data)
        except queue.Full:
            pass

        return (None, pyaudio.paContinue)

    def _processing_loop(self) -> None:
        """Main processing loop (runs in daemon thread)."""
        while self.is_running:
            try:
                # Get audio chunk from queue
                chunk_bytes = self.audio_queue.get(timeout=0.1)

                # Convert bytes to numpy array
                chunk_np = np.frombuffer(chunk_bytes, dtype=np.int16)

                # Calculate RMS energy
                energy = np.sqrt(np.mean(chunk_np.astype(np.float64) ** 2))

                if energy > self.silence_threshold:
                    # Speech detected
                    if not self._in_speech:
                        self._in_speech = True
                        self._speech_buffer = []
                        self._silence_counter = 0
                    self._speech_buffer.append(chunk_np)
                else:
                    # Silence
                    if self._in_speech:
                        self._silence_counter += 1
                        self._speech_buffer.append(chunk_np)

                        # Check if speech ended
                        if self._silence_counter >= self.max_silence_chunks:
                            self._finalize_speech()
                            self._in_speech = False
                            self._speech_buffer = []
                            self._silence_counter = 0

                # Force finalize if buffer too large (15 seconds - proteção anti-TV)
                buffer_duration = len(self._speech_buffer) * self.chunk_size / self.sample_rate
                if buffer_duration > 15:
                    print(f"\n{COLOR_YELLOW}[AVISO] Áudio muito longo ({buffer_duration:.1f}s) - descartando (possível TV/ruído){COLOR_RESET}")
                    self._in_speech = False
                    self._speech_buffer = []
                    self._silence_counter = 0

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ERRO] Erro no processing loop: {e}")

    def _finalize_speech(self) -> None:
        """Finalize speech detection and trigger callback."""
        if not self._speech_buffer:
            return

        # Concatenate all chunks
        audio_np = np.concatenate(self._speech_buffer)

        # Check minimum duration
        duration = len(audio_np) / self.sample_rate
        if duration < self.min_speech_duration:
            return

        print(f"[INFO] Fala detectada: {duration:.2f}s, {len(audio_np)} samples")

        # Call callback
        try:
            self.on_speech_callback(audio_np)
        except Exception as e:
            print(f"[ERRO] Erro no callback de fala: {e}")

    def start(self) -> None:
        """Start the audio pipeline."""
        if not _PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio não disponível")

        print("[INFO] Iniciando AudioPipeline...")

        self._pa = pyaudio.PyAudio()

        # Open stream
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback,
        )

        self.is_running = True

        # Start processing thread
        self._processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._processing_thread.start()

        print("[INFO] AudioPipeline iniciado (mic ativo)")

    def stop(self) -> None:
        """Stop the audio pipeline."""
        print("[INFO] Parando AudioPipeline...")
        self.is_running = False

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._pa:
            self._pa.terminate()
            self._pa = None

        print("[INFO] AudioPipeline parado")


class PTTPipeline(AudioPipeline):
    """Push-to-Talk audio pipeline - only records when Right Ctrl is held.

    Usa pynput para detectar especificamente o Right Ctrl (ctrl_r).
    PyAudio fica sempre rodando em background, mas só armazena quando PTT ativo.
    """

    def __init__(
        self,
        config: dict,
        on_speech_callback: Callable[[np.ndarray], None],
        ptt_key: str = "right ctrl"
    ):
        """
        Initialize PTT audio pipeline.

        Args:
            config: Configuration dict with audio settings
            on_speech_callback: Callback function called when speech segment is complete
            ptt_key: Ignorado - sempre usa Right Ctrl (ctrl_r)
        """
        super().__init__(config, on_speech_callback)

        if not _PYNPUT_AVAILABLE:
            raise ImportError("pynput não está instalado. Instale com: pip install pynput")

        # Debounce flag - evita spam de gravação
        self.is_currently_recording = False

        # Buffer de audio PTT - armazena bytes brutos do PyAudio
        self._ptt_buffer_bytes: list[bytes] = []

        # Listener do pynput
        self._keyboard_listener: Optional[keyboard.Listener] = None

    def _on_pynput_press(self, key) -> bool:
        """Callback quando tecla é pressionada - SÓ Right Ctrl ativa."""
        # Verifica se é EXATAMENTE o Right Ctrl (ctrl_r)
        if key == keyboard.Key.ctrl_r:
            # Debounce: só começa se NÃO estiver gravando
            if not self.is_currently_recording:
                self.is_currently_recording = True
                self._ptt_buffer_bytes = []  # Limpa buffer anterior
                print(f"\n{COLOR_GREEN}[PTT] Gravando... (solte Right Ctrl para enviar){COLOR_RESET}")
        return True  # Continua escutando

    def _on_pynput_release(self, key) -> bool:
        """Callback quando tecla é solta - SÓ Right Ctrl para."""
        if key == keyboard.Key.ctrl_r:
            # Só para se estiver gravando
            if self.is_currently_recording:
                self.is_currently_recording = False
                print(f"\n{COLOR_YELLOW}[PTT] Parando gravacao...{COLOR_RESET}")
                self._finalize_ptt_speech()
        return True  # Continua escutando

    def _finalize_ptt_speech(self) -> None:
        """Finalize PTT speech e envia para transcrição."""
        if not self._ptt_buffer_bytes:
            print(f"{COLOR_YELLOW}[PTT] Nenhum audio capturado{COLOR_RESET}")
            return

        try:
            # Junta todos os bytes do buffer
            audio_bytes = b''.join(self._ptt_buffer_bytes)

            # Converte bytes para numpy array (int16)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

            # Verifica duração mínima
            duration = len(audio_np) / self.sample_rate
            if duration < self.min_speech_duration:
                print(f"{COLOR_YELLOW}[PTT] Audio muito curto ({duration:.2f}s), ignorando{COLOR_RESET}")
                return

            print(f"{COLOR_GREEN}[PTT] Audio capturado: {duration:.2f}s, {len(audio_np)} samples{COLOR_RESET}")

            # Chama callback com o audio completo
            self.on_speech_callback(audio_np)

        except Exception as e:
            print(f"{COLOR_RED}[ERRO] PTT: Erro ao finalizar: {e}{COLOR_RESET}")

    def _ptt_processing_loop(self) -> None:
        """PTT processing loop - PyAudio sempre lendo, só armazena quando PTT ativo."""
        print(f"{COLOR_BLUE}[PTT] Aguardando Right Ctrl...{COLOR_RESET}")

        while self.is_running:
            try:
                # SEMPRE lê da fila (PyAudio rodando em background)
                chunk_bytes = self.audio_queue.get(timeout=0.1)

                # SÓ armazena se estiver gravando (Right Ctrl pressionado)
                if self.is_currently_recording:
                    self._ptt_buffer_bytes.append(chunk_bytes)

                    # Proteção: limite de 15 segundos
                    buffer_duration = len(self._ptt_buffer_bytes) * self.chunk_size / self.sample_rate
                    if buffer_duration > 15:
                        print(f"\n{COLOR_YELLOW}[PTT] Limite de 15s atingido, finalizando...{COLOR_RESET}")
                        self.is_currently_recording = False
                        self._finalize_ptt_speech()
                        self._ptt_buffer_bytes = []

            except queue.Empty:
                continue
            except Exception as e:
                print(f"{COLOR_RED}[ERRO] PTT: Erro no loop: {e}{COLOR_RESET}")

    def start(self) -> None:
        """Start the PTT audio pipeline com pynput listener."""
        if not _PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio não disponível")
        if not _PYNPUT_AVAILABLE:
            raise RuntimeError("pynput não disponível. Instale: pip install pynput")

        print(f"{COLOR_GREEN}[INFO] Iniciando PTTPipeline (Right Ctrl)...{COLOR_RESET}")

        # Inicializa PyAudio
        self._pa = pyaudio.PyAudio()

        # Abre stream de audio (sempre capturando em background)
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback,
        )

        self.is_running = True

        # Inicia listener do pynput em thread separada
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_pynput_press,
            on_release=self._on_pynput_release
        )
        self._keyboard_listener.start()

        # Inicia thread de processamento de audio
        self._processing_thread = threading.Thread(target=self._ptt_processing_loop, daemon=True)
        self._processing_thread.start()

        print(f"{COLOR_GREEN}[INFO] PTTPipeline iniciado - segure Right Ctrl para falar{COLOR_RESET}")

    def stop(self) -> None:
        """Stop the PTT audio pipeline."""
        print(f"{COLOR_GREEN}[INFO] Parando PTTPipeline...{COLOR_RESET}")
        self.is_running = False

        # Para o listener do teclado
        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except:
                pass
            self._keyboard_listener = None

        # Para o stream de audio
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        # Termina PyAudio
        if self._pa:
            self._pa.terminate()
            self._pa = None

        print(f"{COLOR_GREEN}[INFO] PTTPipeline parado{COLOR_RESET}")


if __name__ == "__main__":
    if not _PYAUDIO_AVAILABLE:
        print("[ERRO] PyAudio não instalado. Instale com: pip install PyAudio")
        exit(1)

    print("[INFO] Testando AudioPipeline...")

    def on_speech(audio_np: np.ndarray) -> None:
        print(f"[INFO] Callback chamado: {len(audio_np)} samples")

    config = {
        "sample_rate": 16000,
        "channels": 1,
        "chunk_size": 4096,
        "silence_threshold": 500,
        "max_silence_chunks": 30,
        "min_speech_duration": 0.5,
    }

    pipeline = AudioPipeline(config, on_speech)

    try:
        pipeline.start()
        print("[INFO] Fale algo (ou pressione Ctrl+C)...")
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n[INFO] Interrompido")
    finally:
        pipeline.stop()
