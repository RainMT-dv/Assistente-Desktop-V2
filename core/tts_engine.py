"""Text-to-Speech engine using Edge-TTS with emotional profiles."""

import asyncio
import json
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

import edge_tts

from .logger import log
import pygame

# Técnica Neuro-sama: pitch base para soar adolescente
# Edge-TTS 7.2.8 SÓ aceita formato Hz (+/-\d+Hz), REJEITA semitones (st)
# +4Hz = efeito adolescente sutil e natural (estilo Neuro-sama)
# Ajuste manualmente: "+4Hz" (subtil), "+6Hz" (mais agudo), "+8Hz" (muito agudo)
BASE_PITCH = "+4Hz"  # Valores possíveis: "+4Hz", "+6Hz", "+8Hz", "+10Hz"

# Pitch limits para clamping (evitar distorção excessiva)
MIN_PITCH_HZ = -50
MAX_PITCH_HZ = +50


def combine_pitch(base_pitch: str, emotion_pitch: str) -> str:
    r"""
    Combine BASE_PITCH with emotion pitch adjustment (Hz only).
    Edge-TTS 7.2.8 only accepts format: "+/-\d+Hz"
    
    Examples:
        combine_pitch("+4Hz", "+2Hz") → "+6Hz"
        combine_pitch("+4Hz", "-3Hz") → "+1Hz"
    
    Args:
        base_pitch: Base pitch value (e.g., "+4Hz")
        emotion_pitch: Emotion pitch adjustment (e.g., "+2Hz", "-3Hz")
    
    Returns:
        Combined pitch string in edge-tts format ("+6Hz")
    """
    def parse_hz(pitch_str: str) -> int:
        """Parse pitch string to integer Hz value."""
        pitch_str = pitch_str.strip()
        if not pitch_str.lower().endswith("hz"):
            return 0
        try:
            # Remove 'Hz' and extract numeric value with sign
            numeric = pitch_str.lower().replace("hz", "").strip()
            return int(numeric)
        except ValueError:
            return 0
    
    base_val = parse_hz(base_pitch)
    emotion_val = parse_hz(emotion_pitch)
    combined = base_val + emotion_val
    
    # Clamp to valid range
    combined = max(MIN_PITCH_HZ, min(MAX_PITCH_HZ, combined))
    
    # Format result (always "+XHz" or "-XHz")
    if combined >= 0:
        return f"+{combined}Hz"
    else:
        return f"{combined}Hz"


def clean_tts_text(text: str) -> str:
    """
    Limpa texto para TTS - remove emojis e caracteres especiais.
    
    Args:
        text: Texto original
        
    Returns:
        Texto limpo para TTS
    """
    import re
    
    # Remove emojis (ranges Unicode de emojis comuns)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Remove caracteres especiais que não são fala
    text = re.sub(r'[*#_~|\[\](){}]', '', text)
    
    # Remove múltiplos espaços
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


class TTSEngine:
    """TTS engine with emotional profile support using Edge-TTS."""

    def __init__(self, config_path: str = "config/settings.json", emotion_profiles_path: str = "config/emotion_profiles.json"):
        """
        Initialize the TTS engine.

        Args:
            config_path: Path to settings.json
            emotion_profiles_path: Path to emotion_profiles.json
        """
        self.config_path = config_path
        self.emotion_profiles_path = emotion_profiles_path
        self.config = {}
        self.emotion_profiles = {}
        self.voice = "pt-BR-FranciscaNeural"
        self.engine = "edge-tts"
        self.output_dir = "audio_output"
        self._file_counter = 0

        self._load_configs()
        self._ensure_output_dir()

    def _load_configs(self) -> None:
        """Load configuration files."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            with open(self.emotion_profiles_path, "r", encoding="utf-8") as f:
                self.emotion_profiles = json.load(f)

            self.voice = self.config.get("tts", {}).get("voice", "pt-BR-FranciscaNeural")
            self.engine = self.config.get("tts", {}).get("engine", "edge-tts")
            self.output_dir = self.config.get("paths", {}).get("audio_output_dir", "audio_output")

            log('TTS', f'✓ TTS Engine carregado: voice={self.voice}, engine={self.engine}')
        except FileNotFoundError as e:
            log('TTS', f'✗ Arquivo de configuração não encontrado: {e}')
            raise
        except json.JSONDecodeError as e:
            log('TTS', f'✗ JSON inválido: {e}')
            raise

    def _ensure_output_dir(self) -> None:
        """Create audio output directory if it doesn't exist."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        log('TTS', f'✓ Diretório de áudio: {os.path.abspath(self.output_dir)}')

    def _generate_filename(self, emotion: str) -> str:
        """Generate unique filename for audio output."""
        self._file_counter += 1
        return f"tts_{self._file_counter:04d}_{emotion}.mp3"

    def _get_edge_tts_config(self, emotion: str) -> Dict:
        """Get edge_tts config for an emotion (rate, pitch, volume)."""
        profile = self.emotion_profiles.get(emotion, self.emotion_profiles.get("Neutra", {}))
        return profile.get("edge_tts", {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"})

    async def generate_audio(self, text: str, emotion: str = "Neutra", output_path: Optional[str] = None) -> str:
        """
        Generate audio file from text with emotional profile.

        Args:
            text: Text to synthesize
            emotion: Emotion name (must exist in emotion_profiles.json)
            output_path: Custom output path (auto-generated if None)

        Returns:
            Path to generated audio file
        """
        if self.engine == "azure":
            raise NotImplementedError("Azure TTS ainda não implementado. Use 'edge-tts'.")

        # LIMPEZA: Remove emojis e caracteres especiais antes do TTS
        clean_text = clean_tts_text(text)
        
        if not clean_text:
            log('TTS', '✗ Texto vazio após limpeza, nada para sintetizar')
            raise ValueError("Texto vazio após limpeza")

        # Get edge_tts config for this emotion
        edge_config = self._get_edge_tts_config(emotion)

        # Combine BASE_PITCH with emotion pitch (Técnica Neuro-sama)
        emotion_pitch = edge_config.get("pitch", "+0Hz")
        final_pitch = combine_pitch(BASE_PITCH, emotion_pitch)

        # PROTEÇÃO: textos curtos (<30 chars) usam pitch neutro (+0Hz)
        # edge-tts retorna vazio com pitch alto em chunks curtos
        if len(clean_text) < 30:
            final_pitch = "+0Hz"
            emotion_pitch = "+0Hz"

        # Generate output path if not provided
        if output_path is None:
            filename = self._generate_filename(emotion)
            output_path = os.path.join(self.output_dir, filename)

        try:
            # Try with combined pitch first (Técnica Neuro-sama)
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice,
                rate=edge_config.get("rate", "+0%"),
                pitch=final_pitch,
                volume=edge_config.get("volume", "+0%"),
            )
            await communicate.save(output_path)
            log('TTS', f'✓ Áudio gerado: {output_path} (pitch={final_pitch})')
            return output_path
        except Exception as e:
            # Fallback: try with just emotion pitch (without BASE_PITCH)
            log('TTS', f'✗ Falha com pitch combinado \'{final_pitch}\': {e}')
            log('TTS', f'✗ Tentando fallback com pitch da emoção: {emotion_pitch}')
            try:
                communicate = edge_tts.Communicate(
                    text=clean_text,
                    voice=self.voice,
                    rate=edge_config.get("rate", "+0%"),
                    pitch=emotion_pitch,
                    volume=edge_config.get("volume", "+0%"),
                )
                await communicate.save(output_path)
                log('TTS', f'✓ Áudio gerado (fallback): {output_path}')
                return output_path
            except Exception as e2:
                log('TTS', f'✗ Falha ao gerar áudio (fallback também falhou): {e2}')
                raise

    async def generate_audio_bytes(self, text: str, emotion: str = "Neutra", full_text_fallback: str = None) -> bytes:
        """
        Generate audio bytes from text with emotional profile.

        Args:
            text: Text to synthesize (chunk)
            emotion: Emotion name
            full_text_fallback: Texto completo original para fallback se chunk falhar

        Returns:
            Audio bytes (MP3)
        """
        # LIMPEZA: Remove emojis e caracteres especiais antes do TTS
        clean_text = clean_tts_text(text)
        
        if not clean_text:
            log('TTS', '✗ Texto vazio após limpeza, tentando fallback completo')
            # FALLBACK: tenta o texto completo se este chunk está vazio
            if full_text_fallback:
                clean_fallback = clean_tts_text(full_text_fallback)
                if clean_fallback:
                    log('TTS', '✓ Usando texto completo como fallback')
                    return await self._generate_audio_bytes_single(clean_fallback, emotion)
            raise ValueError("Texto vazio após limpeza e sem fallback válido")

        try:
            return await self._generate_audio_bytes_single(clean_text, emotion)
        except Exception as e:
            log('TTS', f'✗ Falha ao gerar chunk: {e}')
            # FALLBACK: tenta o texto completo se o chunk falhou
            if full_text_fallback:
                clean_fallback = clean_tts_text(full_text_fallback)
                if clean_fallback and clean_fallback != clean_text:
                    log('TTS', f'✗ Fallback para texto completo ({len(clean_fallback)} chars)')
                    try:
                        return await self._generate_audio_bytes_single(clean_fallback, emotion)
                    except Exception as e2:
                        log('TTS', f'✗ Fallback completo também falhou: {e2}')
            raise

    async def _generate_audio_bytes_single(self, clean_text: str, emotion: str = "Neutra") -> bytes:
        """
        Internal: generate audio from already-cleaned text.
        
        Args:
            clean_text: Texto já limpo (sem emojis)
            emotion: Emotion name
            
        Returns:
            Audio bytes (MP3)
        """
        edge_config = self._get_edge_tts_config(emotion)

        # Combine BASE_PITCH with emotion pitch (Técnica Neuro-sama)
        emotion_pitch = edge_config.get("pitch", "+0Hz")
        final_pitch = combine_pitch(BASE_PITCH, emotion_pitch)

        # PROTEÇÃO: textos curtos (<30 chars) usam pitch neutro (+0Hz)
        if len(clean_text) < 30:
            final_pitch = "+0Hz"
            emotion_pitch = "+0Hz"

        try:
            # Try with combined pitch first
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice,
                rate=edge_config.get("rate", "+0%"),
                pitch=final_pitch,
                volume=edge_config.get("volume", "+0%"),
            )

            audio_buffer = BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

            return audio_buffer.getvalue()
        except Exception as e:
            # Fallback: try with just emotion pitch
            log('TTS', f'✗ Falha com pitch \'{final_pitch}\', tentando \'{emotion_pitch}\'')
            try:
                communicate = edge_tts.Communicate(
                    text=clean_text,
                    voice=self.voice,
                    rate=edge_config.get("rate", "+0%"),
                    pitch=emotion_pitch,
                    volume=edge_config.get("volume", "+0%"),
                )

                audio_buffer = BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.write(chunk["data"])

                return audio_buffer.getvalue()
            except Exception as e2:
                log('TTS', f'✗ Falha ao gerar áudio (ambos pitches falharam): {e2}')
                raise

    def play_audio_file(self, path: str) -> None:
        """Play audio file using pygame mixer."""
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            log('TTS', f'✗ Falha ao reproduzir áudio: {e}')
        finally:
            pygame.mixer.music.unload()

    def play_audio_bytes(self, audio_bytes: bytes) -> None:
        """Play audio bytes using pygame mixer."""
        try:
            sound = pygame.mixer.Sound(BytesIO(audio_bytes))
            channel = sound.play()
            if channel:
                while channel.get_busy():
                    time.sleep(0.05)
        except Exception as e:
            log('TTS', f'✗ Falha ao reproduzir áudio bytes: {e}')

    async def speak(self, text: str, emotion: str = "Neutra", use_bytes: bool = True) -> None:
        """
        Generate and play audio in one call.

        Args:
            text: Text to speak
            emotion: Emotion name
            use_bytes: If True, use BytesIO playback; else use file
        """
        if use_bytes:
            audio_bytes = await self.generate_audio_bytes(text, emotion)
            self.play_audio_bytes(audio_bytes)
        else:
            path = await self.generate_audio(text, emotion)
            self.play_audio_file(path)

    async def speak_gapless(self, chunks: list, emotion: str = "Neutra") -> None:
        """
        GAPLESS TTS: Toca múltiplos chunks em sequência sem pausas.

        Usa pygame.mixer.music.queue() para enfileirar chunks.
        O Pygame toca um após o outro automaticamente sem delay.
        Não precisa de FFMPEG ou pydub.

        Args:
            chunks: Lista de strings (chunks de texto)
            emotion: Emoção para o TTS
        """
        if not chunks:
            return

        # Se só tem 1 chunk, toca direto
        if len(chunks) == 1:
            audio_bytes = await self.generate_audio_bytes(chunks[0], emotion)
            self.play_audio_bytes(audio_bytes)
            return

        log('TTS', f'✓ GAPLESS: Gerando {len(chunks)} chunks...')

        # Gera todos os arquivos de áudio primeiro
        chunk_files = []
        for i, chunk in enumerate(chunks):
            try:
                # Gera arquivo temporário para cada chunk
                filename = f"chunk_{i:03d}_{int(time.time())}.mp3"
                filepath = os.path.join(self.output_dir, filename)
                await self.generate_audio(chunk, emotion, filepath)
                chunk_files.append(filepath)
            except Exception as e:
                log('TTS', f'✗ Falha no chunk {i+1}: {e}')
                continue

        if not chunk_files:
            log('TTS', '✗ Nenhum áudio gerado')
            return

        if len(chunk_files) == 1:
            # Só gerou 1, toca direto
            self.play_audio_file(chunk_files[0])
        else:
            # GAPLESS: Carrega primeiro e enfileira o resto
            log('TTS', f'✓ Tocando {len(chunk_files)} chunks em sequência...')
            pygame.mixer.music.load(chunk_files[0])
            pygame.mixer.music.play()

            # Enfileira os próximos (pygame toca automaticamente um após o outro)
            for filepath in chunk_files[1:]:
                pygame.mixer.music.queue(filepath)

            # Aguarda tudo terminar
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)

        # Limpa arquivos temporários
        for filepath in chunk_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass

        log('TTS', f'✓ GAPLESS: Reprodução completa')

    async def list_voices(self, language: str = "pt-BR") -> List[Dict]:
        """
        List available voices for a language.

        Args:
            language: Language code (e.g., "pt-BR", "en-US")

        Returns:
            List of voice dictionaries
        """
        try:
            voices = await edge_tts.list_voices()
            filtered = [v for v in voices if language.lower() in v.get("Locale", "").lower()]
            return filtered
        except Exception as e:
            log('TTS', f'✗ Falha ao listar vozes: {e}')
            return []

    async def test_all_emotions(self, output_dir: Optional[str] = None) -> List[str]:
        """
        Generate test audio for each emotion profile.

        Args:
            output_dir: Directory for test files

        Returns:
            List of generated file paths
        """
        test_text = "Olá! Este é um teste de emoção na minha voz."
        output_dir = output_dir or self.output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        generated = []
        for emotion in self.emotion_profiles.keys():
            filename = f"test_{emotion}.mp3"
            output_path = os.path.join(output_dir, filename)
            try:
                await self.generate_audio(test_text, emotion, output_path)
                generated.append(output_path)
            except Exception as e:
                log('TTS', f'✗ Falha ao gerar teste para {emotion}: {e}')

        log('TTS', f'✓ {len(generated)} arquivos de teste gerados em {output_dir}')
        return generated


if __name__ == "__main__":
    async def main():
        engine = TTSEngine("../config/settings.json", "../config/emotion_profiles.json")
        log('TTS', '=== TTS Engine Demo ===')
        log('TTS', f'Profiles: {list(engine.emotion_profiles.keys())}')

        # Test single generation
        path = await engine.generate_audio("Oi! Tudo bem com você?", "Feliz")
        log('TTS', f'✓ Gerado: {path}')

        # Test bytes generation
        audio_bytes = await engine.generate_audio_bytes("Teste em memória!", "Feliz")
        log('TTS', f'✓ Audio gerado: {len(audio_bytes)} bytes (memória)')

    asyncio.run(main())
