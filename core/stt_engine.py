"""Speech-to-Text engine using faster-whisper with noise filtering."""

import os
import tempfile
import time
import wave
from typing import Optional, Tuple

import numpy as np

# Optional import - gracefully handle if not available
try:
    from faster_whisper import WhisperModel
    _FASTER_WHISPER_AVAILABLE = True
except ImportError:
    _FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None  # type: ignore

try:
    from scipy import signal
    _SCIPY_AVAILABLE = True
except ImportError:
    _SCIPY_AVAILABLE = False


class STTEngine:
    """Speech-to-Text engine using faster-whisper with noise filtering."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the STT engine.

        Args:
            config: Configuration dict with keys like model_size, device, compute_type, etc.
        """
        if not _FASTER_WHISPER_AVAILABLE:
            raise ImportError("faster-whisper não está instalado. Instale com: pip install faster-whisper")

        self.config = config or {}

        # MUDANÇA 2: Auto-detect GPU and configure model
        device, compute_type = self._detect_device()
        model_size = self.config.get("model_gpu", "small") if device == "cuda" else self.config.get("model_cpu", "base")

        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = self.config.get("language", "pt")
        self.beam_size = self.config.get("beam_size", 5)
        self.noise_filter_enabled = self.config.get("noise_filter_enabled", True)
        self.highpass_freq = self.config.get("noise_filter_highpass", 80)
        self.lowpass_freq = self.config.get("noise_filter_lowpass", 7500)

        # MUDANÇA 2: VAD settings from config
        self.vad_filter = self.config.get("vad_filter", True)
        self.vad_min_silence_ms = self.config.get("vad_min_silence_ms", 500)
        self.vad_speech_pad_ms = self.config.get("vad_speech_pad_ms", 200)

        self.model: Optional[WhisperModel] = None
        self._load_model()

    def _detect_device(self) -> Tuple[str, str]:
        """Detect best available device (GPU or CPU)."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"[INFO] GPU detectada: {gpu_name}")
                # GPUs com compute capability < 7.0 não suportam int8_float16
                # GTX 1050 Ti, 1030, MX series, etc → usar int8
                capability = torch.cuda.get_device_capability(0)
                if capability[0] < 7:
                    print(f"[INFO] Compute capability {capability[0]}.{capability[1]} - usando int8")
                    return ("cuda", "int8")
                print(f"[INFO] Compute capability {capability[0]}.{capability[1]} - usando int8_float16")
                return ("cuda", "int8_float16")
        except ImportError:
            pass
        print("[INFO] GPU não disponível, usando CPU")
        return ("cpu", "int8")

    def _load_model(self) -> None:
        """Load the Whisper model."""
        try:
            print(f"[INFO] Whisper: model={self.model_size}, device={self.device}, compute_type={self.compute_type}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root="models"
            )
            print(f"[INFO] Modelo Whisper carregado com sucesso")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar modelo Whisper: {e}")
            raise

    def apply_noise_filter(self, audio_np: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Apply highpass and lowpass filters to remove noise.

        Args:
            audio_np: Audio samples as numpy array (int16 or float)
            sample_rate: Sample rate in Hz

        Returns:
            Filtered audio as np.int16
        """
        if not _SCIPY_AVAILABLE:
            print("[AVISO] scipy não disponível, filtro de ruído desabilitado")
            return audio_np.astype(np.int16)

        # Convert to float64 for processing
        audio_float = audio_np.astype(np.float64)

        # Normalize if int16
        if audio_np.dtype == np.int16:
            audio_float = audio_float / 32768.0

        nyquist = sample_rate / 2

        # Highpass filter (remove rumble/breath pops below 80Hz)
        if self.highpass_freq > 0:
            highpass_norm = self.highpass_freq / nyquist
            b_high, a_high = signal.butter(4, highpass_norm, btype='high')
            audio_float = signal.lfilter(b_high, a_high, audio_float)

        # Lowpass filter (remove high freq noise above 7500Hz)
        if self.lowpass_freq < nyquist:
            lowpass_norm = self.lowpass_freq / nyquist
            b_low, a_low = signal.butter(4, lowpass_norm, btype='low')
            audio_float = signal.lfilter(b_low, a_low, audio_float)

        # Convert back to int16
        audio_float = np.clip(audio_float, -1.0, 1.0)
        return (audio_float * 32767).astype(np.int16)

    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("Modelo Whisper não carregado")

        try:
            # MUDANÇA 2: Enhanced VAD with config parameters + condition_on_previous_text=False
            # condition_on_previous_text=False evita duplicação/alucinação (race condition)
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=self.beam_size,
                vad_filter=self.vad_filter,
                vad_parameters=dict(
                    min_silence_duration_ms=self.vad_min_silence_ms,
                    speech_pad_ms=self.vad_speech_pad_ms
                ),
                condition_on_previous_text=False,  # CRÍTICO: previne duplicação
            )

            # Join all segment texts
            text_parts = [segment.text.strip() for segment in segments]
            result = " ".join(text_parts).strip()

            return result
        except Exception as e:
            print(f"[ERRO] Falha na transcrição: {e}")
            return ""

    def transcribe_buffer(self, audio_np: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe audio from a numpy buffer.

        Args:
            audio_np: Audio samples as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("Modelo Whisper não carregado")

        # MUDANÇA 2: Performance logging
        audio_duration = len(audio_np) / sample_rate
        start_time = time.time()

        # Apply noise filter if enabled
        if self.noise_filter_enabled:
            audio_np = self.apply_noise_filter(audio_np, sample_rate)

        # Save to temporary WAV file
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = tmp.name

            # Write WAV file
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_np.tobytes())

            # Transcribe
            result = self.transcribe_file(temp_path)

            # MUDANÇA 2: Log performance metrics
            elapsed = time.time() - start_time
            ratio = audio_duration / elapsed if elapsed > 0 else 0
            print(f"[INFO] STT: {audio_duration:.2f}s audio em {elapsed:.2f}s (ratio: {ratio:.1f}x)")

            return result

        except Exception as e:
            print(f"[ERRO] Falha na transcrição do buffer: {e}")
            return ""

        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

    @staticmethod
    def is_available() -> bool:
        """Check if faster-whisper is available."""
        return _FASTER_WHISPER_AVAILABLE


if __name__ == "__main__":
    if not STTEngine.is_available():
        print("[ERRO] faster-whisper não instalado. Instale com: pip install faster-whisper")
        exit(1)

    # Test with dummy config
    config = {
        "model_size": "base",
        "device": "cpu",
        "compute_type": "int8",
        "language": "pt",
        "beam_size": 5,
        "noise_filter_enabled": True,
    }

    print("[INFO] Testando STTEngine...")
    engine = STTEngine(config)

    # Test noise filter with dummy data
    print("\n[INFO] Testando filtro de ruído...")
    dummy_audio = np.random.randint(-1000, 1000, size=16000, dtype=np.int16)
    filtered = engine.apply_noise_filter(dummy_audio, 16000)
    print(f"  Input: {len(dummy_audio)} samples, dtype={dummy_audio.dtype}")
    print(f"  Output: {len(filtered)} samples, dtype={filtered.dtype}")
    print("[INFO] STT Engine pronto para uso")
