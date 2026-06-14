"""Constantes do assistente pessoal.

Centraliza valores mágicos (magic numbers) para facilitar manutenção.
"""

# =============================================================================
# PROACTIVE ENGINE - Cooldown Adaptativo
# =============================================================================
PROACTIVE_INTERVAL_NORMAL = 120      # Segundos entre falas proativas (usuário inativo)
PROACTIVE_GRACE_PERIOD = 45          # Segundos de grace period após interação
PROACTIVE_MIN_INTERVAL = 30        # Mínimo permitido para intervalos

# =============================================================================
# TTS - Text to Speech
# =============================================================================
# DEPRECATED: Constantes de chunking - não usadas desde que TTS passou a gerar
# áudio inteiro de uma vez (mais rápido, sem cortes). Mantidas para referência.
# TTS_MAX_CHUNK_LENGTH = 120           # DEPRECATED - não usar
# TTS_MIN_CHUNK_LENGTH = 40            # DEPRECATED - não usar
# TTS_GAPLESS_THRESHOLD = 200          # DEPRECATED - não usar

# =============================================================================
# CHAT / LLM
# =============================================================================
CHAT_MAX_HISTORY = 10                # Mensagens máximas no histórico
CLIPBOARD_DISPLAY_MAX = 200          # Caracteres máximos ao mostrar clipboard

# =============================================================================
# MEMORY
# =============================================================================
MEMORY_RECENT_DAYS = 3               # Dias de memória recente para contexto
MEMORY_MAX_HISTORY = 50              # Eventos máximos no histórico de mood

# =============================================================================
# AUDIO
# =============================================================================
AUDIO_SAMPLE_RATE = 16000            # Sample rate padrão para STT
AUDIO_PYGAME_FREQUENCY = 22050     # Frequência do pygame mixer
AUDIO_PYGAME_BUFFER = 512            # Buffer do pygame mixer

# =============================================================================
# DASHBOARD
# =============================================================================
DASHBOARD_DEFAULT_PORT = 5000        # Porta padrão do dashboard
LOG_SERVER_AI_PORT = 5002            # Porta do log server (AI)
LOG_SERVER_VOICE_PORT = 5003          # Porta do log server (Voice)
LOG_SERVER_LLM_PORT = 5004            # Porta do log server (LLM)
LOG_SERVER_TTS_PORT = 5005           # Porta do log server (TTS)
