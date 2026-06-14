"""Main entry point for Desktop Assistant V2 with voice + dashboard support."""

# Load .env antes de qualquer import (silencia avisos do dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass  # dotenv não é obrigatório

import asyncio
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time as time_module
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pygame

# Importar utilitario de logging com timestamp
from core.logger import log


# ========== OLLAMA LOCAL FALLBACK ==========
def start_ollama_background():
    """Inicia o servidor da Ollama em background, detectando o caminho automaticamente."""
    import shutil

    # 1. Tenta encontrar o ollama no PATH do sistema
    ollama_exe = shutil.which("ollama")

    # 2. Fallback: caminho padrão de instalação no Windows
    if not ollama_exe:
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        fallback = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
        if os.path.exists(fallback):
            ollama_exe = fallback

    if not ollama_exe:
        log('WARN', 'Ollama não encontrada. Fallback local desativado.')
        return

    try:
        # CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            [ollama_exe, "serve"],
            creationflags=0x08000000,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        log('INFO', f'Servidor Ollama local iniciado via: {ollama_exe}')
    except Exception as e:
        log('WARN', f'Erro ao iniciar Ollama: {e}')


async def warmup_ollama():
    """Faz warmup do modelo Ollama usando aiohttp (já instalado)"""
    await asyncio.sleep(5)
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": "gemma4:e2b", "prompt": "", "stream": False},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    log('INFO', 'Modelo local (gemma4:e2b) carregado na memória.')
                else:
                    log('INFO', f'Ollama respondeu com status {response.status}')
    except Exception as e:
        log('INFO', f'Ollama não respondeu ao warmup: {e}')

# Inicia Ollama em background antes de tudo (fallback local)
start_ollama_background()

# Setup paths
BASE_DIR = Path(__file__).parent
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))

# Warmup do modelo local em thread separada (async com asyncio.run)
threading.Thread(target=lambda: asyncio.run(warmup_ollama()), daemon=True).start()

# Import log servers para dashboard (portas 5001-5004)
try:
    from dashboard.log_server import LogServer
    _LOG_SERVERS_AVAILABLE = True
except ImportError:
    _LOG_SERVERS_AVAILABLE = False
    LogServer = None  # type: ignore

# Import constants (sempre disponível, módulo simples)
try:
    from core import constants as const
except ImportError:
    # Fallback: define constantes localmente se import falhar
    class _FallbackConst:
        PROACTIVE_INTERVAL_NORMAL = 120
        PROACTIVE_GRACE_PERIOD = 45
        # TTS chunking constants DEPRECATED - não usados mais
        # TTS_MAX_CHUNK_LENGTH = 120
        # TTS_MIN_CHUNK_LENGTH = 40
        # TTS_GAPLESS_THRESHOLD = 200
        MEMORY_RECENT_DAYS = 3
        AUDIO_PYGAME_FREQUENCY = 22050
        AUDIO_PYGAME_BUFFER = 512
        CLIPBOARD_DISPLAY_MAX = 200
        LOG_SERVER_AI_PORT = 5002
        LOG_SERVER_VOICE_PORT = 5003
        LOG_SERVER_LLM_PORT = 5004
        LOG_SERVER_TTS_PORT = 5005
    const = _FallbackConst()  # type: ignore

# Import V2 enhanced modules: Card Manager, Proactive Engine, Memory, Mood, Context, PTT
try:
    from core import CardManager, ProactiveEngine, MemoryManager, ContextBacklog
    from core.llm_fallback import chat_completion  # Nova API multi-provedor
    from core.audio_pipeline import PTTPipeline  # PTT support
    _V2_ENHANCED_AVAILABLE = True
    _PTT_AVAILABLE = True
except ImportError as e:
    _V2_ENHANCED_AVAILABLE = False
    _PTT_AVAILABLE = False
    CardManager = None  # type: ignore
    ProactiveEngine = None  # type: ignore
    MemoryManager = None  # type: ignore
    MoodEngine = None  # type: ignore
    ContextBacklog = None  # type: ignore
    PTTPipeline = None  # type: ignore
    chat_completion = None  # type: ignore
    log('WARN', f'Alguns módulos V2 não disponíveis: {e}')

# NOVO: Importar novos módulos autônomos (SkillSystem, ContextLogger, TextCapture, WritingMode)
try:
    from core.skill_system import SkillSystem, CommentSkill as AutonomousCommentSkill, Skill
    # PatienceWrapper removido - não utilizado
    # from core.patience_wrapper import PatienceWrapper, PatienceManager
    from core.context_logger import ContextLogger
    from core.text_capture import TextCapture
    from core.writing_mode import WritingMode
    _NEW_MODULES_AVAILABLE = True
    log('INFO', 'Novos módulos autônomos importados com sucesso')
except ImportError as e:
    _NEW_MODULES_AVAILABLE = False
    SkillSystem = None
    AutonomousCommentSkill = None
    Skill = None
    # PatienceWrapper removido
    PatienceWrapper = None
    PatienceManager = None
    ContextLogger = None
    TextCapture = None
    WritingMode = None
    log('WARN', f'Novos módulos autônomos não disponíveis: {e}')

# Colors for terminal output
COLOR_GREEN = "\033[92m"
COLOR_BLUE = "\033[94m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


def print_header():
    """Print ASCII art header."""
    header = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🤖 ASSISTENTE DESKTOP V2                           ║
║        Voz + Emoção + Dashboard em Tempo Real                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(COLOR_GREEN + header + COLOR_RESET)


def load_config(path: str) -> dict:
    """Load a JSON config file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log('ERROR', f'Falha ao carregar {path}: {e}')
        return {}


def remove_emojis(text: str) -> str:
    """Remove emojis from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()


def clean_text_for_tts(text: str) -> str:
    """Clean text for TTS - remove extra tags, emojis, and weird chars."""
    text = re.sub(r'\[\w+\]', '', text)  # remove tags sobrando
    text = remove_emojis(text)
    text = text.replace('¬', '').replace('•', '').replace('*', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class Assistant:
    """Main assistant class."""

    def __init__(self):
        self.config = load_config("config/settings.json")
        self.brain = load_config("config/brain.json")

        # Initialize modules
        self.tts = None
        self.chat = None
        self.parser = None
        self.launcher = None
        self.stt = None
        self.audio_emotion = None
        self.audio_pipeline = None
        self.dashboard = None

        # Log servers para dashboard (AI, Voice, LLM, TTS logs)
        self.ai_log = None
        self.voice_log = None
        self.llm_log = None
        self.tts_log = None

        # V2 Enhanced modules para funcionalidades avançadas
        self.card_manager = None
        self.proactive_engine = None
        self.proactive_skill_manager = None
        
        # Memory Manager para memória de longo prazo
        self.memory_manager = None
        
        # Mood Engine para humor persistente (-10 a +10)
        self.mood_engine = None
        
        # Context Backlog para tópicos pendentes
        self.context_backlog = None
        
        # Novos módulos V2
        self.screen_reader = None
        self.voice_commands = None
        self.event_watcher = None

        # NOVO: Módulos autônomos (SkillSystem, Patience, ContextLogger, TextCapture, WritingMode)
        self.skill_system = None
        self.patience_wrapper = None
        self.context_logger = None
        self.text_capture = None
        self.writing_mode = None

        # PTT mode
        self.ptt_pipeline = None

        # Mode flags
        self.voice_mode = False
        self.dashboard_running = False

        # NOVO: Atributos auxiliares para novos módulos
        self._pending_patience_message = None
        self._captured_text = None

    def initialize(self) -> bool:
        """Initialize all modules."""
        try:
            from core import TTSEngine, ChatManager, EmotionParser, AppLauncher

            log('INFO', 'Inicializando módulos core...')

            # Inicializa log servers PRIMEIRO (antes de ChatManager precisar do llm_log)
            self._init_log_servers()

            # Inicializa Card Manager primeiro (para carregar config do card)
            if _V2_ENHANCED_AVAILABLE and CardManager:
                self.card_manager = CardManager("cards")
                card_name = self.config.get("assistant", {}).get("selected_card", "assistente")
                card = self.card_manager.load_card(card_name)
                log('CARD', f'Card carregado: {card["name"]}')

            self.tts = TTSEngine("config/settings.json", "config/emotion_profiles.json")

            # Aplica config do card ao TTS (voice, pitch)
            if self.card_manager:
                tts_config = self.card_manager.get_tts_config()
                # Note: TTSEngine needs methods to set voice/pitch or we pass at init
                log('TTS', f'Config TTS do card: voice={tts_config["voice"]}, pitch={tts_config["base_pitch"]}')

            self.chat = ChatManager(
                "config/settings.json",
                "config/brain.json",
                "config/slang_dictionary.json",
                "config/emotion_guidance.json",
                llm_log=self.llm_log,  # Passa llm_log para ChatManager logar requests LLM
            )

            # Aplica system prompt do card + opiniões + metacognição
            if self.card_manager:
                system_prompt = self.card_manager.get_system_prompt()
                log('CHAT', f'System prompt loaded from card ({len(system_prompt)} chars)')
                
                # Injetar opiniões no ChatManager
                opinions_text = self.card_manager.get_opinions_text()
                if opinions_text:
                    self.chat.set_opinions_context(opinions_text)
                    log('CHAT', 'Opiniões injetadas no contexto')
                
                # Injetar metacognição no ChatManager
                meta_text = self.card_manager.get_metacognition_text()
                if meta_text:
                    self.chat.set_metacognition_context(meta_text)
                    log('CHAT', 'Metacognição injetada no contexto')

            self.parser = EmotionParser()
            self.launcher = AppLauncher("config/apps.json")

            # Initialize pygame mixer
            pygame.mixer.init(frequency=const.AUDIO_PYGAME_FREQUENCY, size=-16, channels=2, buffer=const.AUDIO_PYGAME_BUFFER)
            log('INFO', 'Sistema de áudio inicializado')

            # Try to initialize optional V2 modules
            self._init_voice_modules()
            self._init_dashboard()

            # Inicializa Proactive Engine com cooldown adaptativo (grace period)
            if _V2_ENHANCED_AVAILABLE and ProactiveEngine and self.stt:
                interval = const.PROACTIVE_INTERVAL_NORMAL
                if self.card_manager:
                    interval = self.card_manager.get_proactive_interval()
                self._init_proactive_engine(interval, grace_period=const.PROACTIVE_GRACE_PERIOD)

            # Inicializa Memory Manager para memória persistente
            if MemoryManager:
                self.memory_manager = MemoryManager("data/memories.json")
                profile = self.memory_manager.get_user_profile()
                log('MEMORY', f'Memory Manager carregado (usuário: {profile.get("name", "desconhecido")})')
                
                # Injeta contexto de memória no ChatManager (últimas conversas)
                if self.chat:
                    memory_context = self.memory_manager.get_context_for_prompt(days=const.MEMORY_RECENT_DAYS)
                    if memory_context:
                        # Divide em profile e summaries para manter compatibilidade
                        parts = memory_context.split("\n\nÚLTIMAS CONVERSAS:")
                        profile_summary = parts[0].replace("\n\nMEMÓRIA DE LONGO PRAZO:\n", "") if parts else ""
                        summaries_text = "ÚLTIMAS CONVERSAS:" + parts[1] if len(parts) > 1 else ""
                        self.chat.set_memory_context(profile_summary, summaries_text)
                        log('MEMORY', 'Contexto de memória injetado no LLM')
            
            # Mood Engine removido - não utilizado
            # if MoodEngine:
            #     self.mood_engine = MoodEngine("data/mood.json")
            #     log('MOOD', f'Mood Engine carregado: {self.mood_engine.get_mood_display()}')
            #     
            #     # Injeta contexto de mood no ChatManager
            #     if self.chat and self.mood_engine:
            #         mood_prompt = self.mood_engine.get_mood_prompt()
            #         if mood_prompt:
            #             self.chat.set_mood_context(mood_prompt)
            #             log('MOOD', 'Contexto de mood injetado no LLM')
            self.mood_engine = None  # Desativado
            
            # Inicializa Context Backlog para tópicos de conversa pendentes
            if ContextBacklog:
                self.context_backlog = ContextBacklog("data/context_backlog.json")
                stats = self.context_backlog.get_stats()
                log('INFO', f'Context Backlog carregado ({stats["pending"]} pendentes)')
            
            # Initialize Screen Reader
            try:
                from core import ScreenReader
                self.screen_reader = ScreenReader()
                log('SCREEN', 'Screen Reader carregado')
            except Exception as e:
                log('WARN', f'Screen Reader não disponível: {e}')
            
            try:
                from core import VoiceCommandProcessor
                wake_words = self.config.get("assistant", {}).get("wake_words", None)
                self.voice_commands = VoiceCommandProcessor(wake_words)
                log('VOICE', 'Voice Commands carregado')
            except Exception as e:
                log('WARN', f'Voice Commands não disponível: {e}')

            # Initialize Proactive Skill Manager (Shogun-style)
            try:
                from core import ProactiveSkillManager
                self.proactive_skill_manager = ProactiveSkillManager(screen_reader=self.screen_reader)
                log('SKILL', 'Proactive Skill Manager carregado (Shogun-style)')
            except Exception as e:
                log('WARN', f'Proactive Skill Manager não disponível: {e}')
            
            # Initialize Event Watcher
            try:
                from core import EventWatcher
                self.event_watcher = EventWatcher()
                log('EVENT', 'Event Watcher carregado')
            except Exception as e:
                log('WARN', f'Event Watcher não disponível: {e}')

            # NOVO: Initialize ContextLogger (salva contextos LLM em JSON)
            try:
                if ContextLogger:
                    self.context_logger = ContextLogger(output_dir="logs/contexts")
                    # Conectar ao chat_manager se possível
                    if self.chat and hasattr(self.chat, 'set_context_logger'):
                        self.chat.set_context_logger(self.context_logger)
                    elif self.chat:
                        self.chat.context_logger = self.context_logger
                    log('CONTEXT_LOGGER', 'Context Logger inicializado (logs/contexts/)')
            except Exception as e:
                log('WARN', f'Context Logger não disponível: {e}')

            # NOVO: Initialize SkillSystem (skills autônomas com cooldown)
            try:
                if SkillSystem and AutonomousCommentSkill:
                    self.skill_system = SkillSystem()
                    # Adicionar CommentSkill para comentários autônomos
                    comment_skill = AutonomousCommentSkill()
                    self.skill_system.add_skill(comment_skill)
                    self.skill_system.enable_all()
                    log('SKILL', f'Skill System inicializado com {len(self.skill_system.skills)} skill(s)')
            except Exception as e:
                log('WARN', f'Skill System não disponível: {e}')

            # NOVO: PatienceWrapper removido - não utilizado
            # try:
            #     if PatienceWrapper:
            #         def on_patience_trigger():
            #             if self.tts and self.chat:
            #                 msg = "[Neutra] Ei, continua aí? Tô te ouvindo..."
            #                 log('PATIENCE', f'Reengajamento: {msg}')
            #                 self._pending_patience_message = msg
            #         
            #         self.patience_wrapper = PatienceWrapper(
            #             inactivity_threshold=10.0,
            #             callback=on_patience_trigger,
            #             reset_on_trigger=True
            #         )
            #         self.patience_wrapper.start()
            #         log('PATIENCE', 'Patience Wrapper iniciado (10s inatividade)')
            # except Exception as e:
            #     log('WARN', f'Patience Wrapper não disponível: {e}')
            self.patience_wrapper = None  # Desativado

            # NOVO: Initialize TextCapture (monitora clipboard)
            try:
                if TextCapture:
                    def on_text_captured(text: str):
                        log('TEXT_CAPTURE', f'Texto capturado: {text[:50]}...')
                        # Se WritingMode estiver ativo, envia para lá
                        if self.writing_mode and hasattr(self.writing_mode, 'is_active') and self.writing_mode.is_active():
                            if hasattr(self.writing_mode, 'update_text'):
                                self.writing_mode.update_text(text)
                        # Marca que há texto novo para possível processamento
                        self._captured_text = text
                    
                    self.text_capture = TextCapture(
                        poll_interval=1.0,
                        callback=on_text_captured,
                        min_length=5
                    )
                    # Inicia desabilitado, usuário ativa via comando
                    log('TEXT_CAPTURE', "Text Capture inicializado (desabilitado, use '/ativar clipboard')")
            except Exception as e:
                log('WARN', f'Text Capture não disponível: {e}')

            # NOVO: Initialize WritingMode (modo ditado/comentários)
            try:
                if WritingMode:
                    def on_writing_comment(comment: str):
                        if self.tts:
                            # Gera áudio do comentário
                            asyncio.create_task(self._speak_simple(f"[Neutra] {comment}"))
                    
                    self.writing_mode = WritingMode(
                        comment_interval=30.0,
                        min_text_length=20,
                        on_comment=on_writing_comment
                    )
                    log('WRITING_MODE', "Writing Mode inicializado (desabilitado, use '/modo escrita')")
            except Exception as e:
                log('WARN', f'Writing Mode não disponível: {e}')
            
            # Verificar aniversário
            self._check_birthday()

            return True
        except Exception as e:
            log('ERROR', f'Falha ao inicializar: {e}')
            return False

    def _init_log_servers(self) -> None:
        """Initialize log servers para dashboard (portas 5001-5004)."""
        if not _LOG_SERVERS_AVAILABLE:
            log('WARN', 'Log servers não disponíveis')
            return

        # Inicializa cada log server individualmente com try/except
        # para que um falhando não impeça os outros de funcionar
        try:
            self.ai_log = LogServer("Comunicação AI", const.LOG_SERVER_AI_PORT, "Mensagens e respostas do chat")
            self.ai_log.start()
            log('DASHBOARD', f'AI Log Server iniciado na porta {const.LOG_SERVER_AI_PORT}')
        except Exception as e:
            log('WARN', f'AI Log Server não iniciado (porta {const.LOG_SERVER_AI_PORT}): {e}')
            self.ai_log = None

        try:
            self.voice_log = LogServer("Voice/STT", const.LOG_SERVER_VOICE_PORT, "Reconhecimento de voz")
            self.voice_log.start()
            log('DASHBOARD', f'Voice Log Server iniciado na porta {const.LOG_SERVER_VOICE_PORT}')
        except Exception as e:
            log('WARN', f'Voice Log Server não iniciado (porta {const.LOG_SERVER_VOICE_PORT}): {e}')
            self.voice_log = None

        try:
            self.llm_log = LogServer("LLM Interno", const.LOG_SERVER_LLM_PORT, "Requests e respostas do modelo")
            self.llm_log.start()
            log('DASHBOARD', f'LLM Log Server iniciado na porta {const.LOG_SERVER_LLM_PORT}')
        except Exception as e:
            log('WARN', f'LLM Log Server não iniciado (porta {const.LOG_SERVER_LLM_PORT}): {e}')
            self.llm_log = None

        try:
            self.tts_log = LogServer("TTS", const.LOG_SERVER_TTS_PORT, "Síntese de fala")
            self.tts_log.start()
            log('DASHBOARD', f'TTS Log Server iniciado na porta {const.LOG_SERVER_TTS_PORT}')
        except Exception as e:
            log('WARN', f'TTS Log Server não iniciado (porta {const.LOG_SERVER_TTS_PORT}): {e}')
            self.tts_log = None

    def _init_voice_modules(self) -> None:
        """Initialize voice/STT modules if available."""
        try:
            from core import STTEngine, AudioEmotionDetector, AudioPipeline

            if STTEngine.is_available():
                stt_config = self.config.get("stt", {})
                self.stt = STTEngine(stt_config)
                log('STT', 'STT Engine carregado')

            if AudioEmotionDetector is not None:
                audio_config = self.config.get("audio", {})
                self.audio_emotion = AudioEmotionDetector(audio_config)
                log('STT', 'Audio Emotion Detector carregado')

            if AudioPipeline is not None and self.stt is not None:
                audio_config = self.config.get("audio", {})
                self.audio_pipeline = AudioPipeline(audio_config, self._on_speech_detected)
                log('STT', 'Audio Pipeline carregado')

        except ImportError as e:
            log('WARN', f'Módulos de voz não disponíveis: {e}')
        except Exception as e:
            log('WARN', f'Erro ao carregar módulos de voz: {e}')

    def _init_dashboard(self) -> None:
        """Initialize dashboard if available."""
        try:
            from dashboard import DashboardServer

            if DashboardServer.is_available():
                dash_config = self.config.get("dashboard", {})
                self.dashboard = DashboardServer(
                    host=dash_config.get("host", "0.0.0.0"),
                    port=dash_config.get("port", 5000),
                    assistant_ref=self,
                )
                log('DASHBOARD', 'Dashboard carregado')
        except ImportError as e:
            log('WARN', f'Dashboard não disponível: {e}')
        except Exception as e:
            log('WARN', f'Erro ao carregar dashboard: {e}')

    def _init_proactive_engine(self, interval_seconds: int = const.PROACTIVE_INTERVAL_NORMAL, grace_period: int = const.PROACTIVE_GRACE_PERIOD) -> None:
        """Initialize proactive speaking engine com cooldown adaptativo (grace period)."""
        try:
            def proactive_callback() -> None:
                """Callback when proactive engine triggers."""
                # Pega ação disponível do Skill Manager (Shogun-style)
                if self.proactive_skill_manager:
                    action_data = self.proactive_skill_manager.get_next_action()
                    if action_data:
                        # action_data é (action_name, prompt)
                        asyncio.run(self._generate_proactive_response(action_data))

            # COOLDOWN ADAPTATIVO: grace_period curto após interação, normal depois
            self.proactive_engine = ProactiveEngine(
                interval_seconds=interval_seconds,
                callback=proactive_callback,
                grace_period=grace_period
            )
            self.proactive_engine.start()
            log('PROACTIVE', f'Proactive engine iniciado (normal: {interval_seconds}s, grace: {grace_period}s)')
        except Exception as e:
            log('WARN', f'Erro ao iniciar proactive engine: {e}')

    async def _get_greeting(self) -> str:
        """Gera saudação dinâmica via LLM baseada em horário e tempo offline."""
        from datetime import datetime

        now = datetime.now()
        hour = now.hour

        # Verificar tempo offline do memory_manager
        last_seen = None
        if self.memory_manager:
            last_seen = self.memory_manager.get_last_seen()

        context_prompt = None

        if last_seen:
            time_diff = now - last_seen
            hours_offline = time_diff.total_seconds() / 3600

            if hours_offline > 24:
                context_prompt = f"O usuário esteve ausente por {int(hours_offline)} horas. Cumprimente de forma dramática, como se tivesse sentido muita falta. Máx 15 palavras."
            elif hours_offline > 8:
                context_prompt = f"O usuário esteve ausente por {int(hours_offline)} horas. Cumprimente de forma casual e levemente sarcástica. Máx 15 palavras."
            elif hours_offline > 2:
                context_prompt = "O usuário voltou depois de algumas horas. Cumprimente rapidamente. Máx 15 palavras."

        # Se não há contexto de offline, usar horário
        if not context_prompt:
            if 5 <= hour < 12:
                context_prompt = f"São {now.strftime('%H:%M')} da manhã. Cumprimente o usuário de forma engraçada sobre café/acordar cedo. Seja debochada. Máx 15 palavras."
            elif 12 <= hour < 18:
                context_prompt = f"São {now.strftime('%H:%M')} da tarde. Cumprimente sobre almoço ou produtividade. Seja sarcástica. Máx 15 palavras."
            elif 18 <= hour < 22:
                context_prompt = f"São {now.strftime('%H:%M')} da noite. Cumprimente sobre o fim do dia. Seja cínica mas gentil. Máx 15 palavras."
            else:
                context_prompt = f"São {now.strftime('%H:%M')} da madrugada. Cobre do usuário por estar acordado. Seja direta e debochada. Máx 15 palavras."

        # Chamar LLM para gerar saudação única
        try:
            if self.chat and hasattr(self.chat, 'generate_greeting'):
                greeting = await self.chat.generate_greeting(context_prompt)
                return greeting
        except Exception as e:
            log('ERROR', f'Erro ao gerar saudação via LLM: {e}')

        # Fallback mínimo se falhar
        assistant_name = self.config.get("assistant", {}).get("name", "Assistente")
        return f"Oi! {assistant_name} na área."

    def _check_birthday(self) -> None:
        """Verifica se hoje é aniversário do usuário."""
        if not self.memory_manager:
            return
            
        profile = self.memory_manager.get_user_profile()
        birthday = profile.get("birthday")
        
        if not birthday:
            return
            
        from datetime import datetime
        today = datetime.now()
        
        try:
            # Formato esperado: DD/MM ou DD/MM/YYYY
            if "/" in birthday:
                parts = birthday.split("/")
                birth_day = int(parts[0])
                birth_month = int(parts[1])
                
                if today.day == birth_day and today.month == birth_month:
                    print(f"{COLOR_GREEN}[INFO] Hoje é aniversário do usuário!{COLOR_RESET}")
                    # Poderia disparar uma saudação especial aqui
        except Exception:
            pass

    async def _handle_voice_command(self, action: str, param: str | None, user_text: str) -> bool:
        """
        Processa comandos de voz.
        
        Returns:
            True se processou como comando, False se deve ir pro LLM
        """
        if not action:
            return False
            
        print(f"{COLOR_YELLOW}[COMANDO] {action} (param: {param}){COLOR_RESET}")
        
        if action == "open_app":
            if param and self.launcher:
                success, msg = self.launcher.launch(param)
                print(f"{COLOR_GREEN if success else COLOR_RED}{msg}{COLOR_RESET}")
                if success:
                    await self._speak_simple("Abriu.")
            else:
                await self._speak_simple("O que você quer abrir?")
            return True
            
        elif action == "read_screen":
            await self._handle_read_screen()
            return True

        elif action == "vision_screen":
            await self._handle_vision_screen()
            return True

        elif action == "read_clipboard":
            await self._handle_read_clipboard()
            return True
            
        elif action == "tell_time":
            if self.voice_commands:
                response = self.voice_commands.format_response(action)
                await self._speak_simple(response)
            return True
            
        elif action == "clear_history":
            if self.chat:
                self.chat.clear_history()
            await self._speak_simple("Histórico limpo.")
            return True
            
        elif action == "exit":
            await self._speak_simple("Até logo!")
            raise SystemExit
            
        return False

    async def _handle_read_screen(self) -> None:
        """Captura tela e envia pro LLM vision."""
        if not self.screen_reader:
            await self._speak_simple("Screen reader não disponível.")
            return

        try:
            await self._speak_simple("Deixa eu ver...")

            # Captura screenshot
            base64_img = self.screen_reader.capture_screen_base64()

            # Cria mensagens para vision
            from core.screen_reader import create_vision_messages
            messages = create_vision_messages(
                "Descreva o que vê nesta captura de tela de forma breve e debochada.",
                base64_img
            )

            # Chama LLM com a imagem
            # Adiciona system prompt
            full_messages = [
                {"role": "system", "content": self.chat._build_system_prompt()},
                messages[0]
            ]

            response = await chat_completion(full_messages, mode="vision")

            if response:
                emotion = self.parser.classify_emotion(response)
                log('SCREEN', f'IA (visão): [{emotion}] {response}')
                await self._speak_response(response, emotion)

        except Exception as e:
            log('ERROR', f'Falha ao ler tela: {e}')
            await self._speak_simple("Não consegui ver a tela.")

    async def _handle_vision_screen(self, user_prompt: str = None) -> None:
        """Comando de voz/texto: Captura tela e comenta (modo vision com chat_manager).

        Args:
            user_prompt: Prompt opcional do usuário (ex: "veja minha tela")
        """
        if not self.screen_reader or not self.chat:
            await self._speak_simple("Minha visão tá embaçada, não consigo ver a tela agora!")
            return

        try:
            await self._speak_simple("Deixa eu dar uma olhada...")

            # Captura screenshot
            base64_img = self.screen_reader.capture_screen_base64()

            # Usa prompt do usuário ou default
            vision_prompt = user_prompt if user_prompt else "O que você vê na tela? Faça um comentário curto e debochado."

            # Usa chat_with_vision do ChatManager
            response = await self.chat.chat_with_vision(
                vision_prompt,
                base64_img,
                user_emotion="neutral"
            )

            if response:
                emotion = self.parser.classify_emotion(response)
                log('SCREEN', f'IA (visão cmd): [{emotion}] {response}')
                await self._speak_response(response, emotion)

        except Exception as e:
            log('ERROR', f'Falha na visão: {e}')
            await self._speak_simple("Minha visão tá embaçada, não consigo ver a tela agora!")

    async def _handle_read_clipboard(self) -> None:
        """Lê clipboard e envia pro LLM."""
        if not self.screen_reader:
            await self._speak_simple("Clipboard não disponível.")
            return
            
        try:
            text = self.screen_reader.read_clipboard()
            
            if not text:
                await self._speak_simple("Não tem nada no clipboard.")
                return
                
            # Trunca se for muito longo
            display_text = text[:const.CLIPBOARD_DISPLAY_MAX] + "..." if len(text) > const.CLIPBOARD_DISPLAY_MAX else text
            print(f"{COLOR_BLUE}Clipboard: {display_text}{COLOR_RESET}")
            
            # Envia pro LLM
            prompt = f"O usuário copiou isso: \"{display_text}\". Faça um comentário breve e debochado sobre."
            response = await self.chat.chat(prompt, user_emotion="neutral")
            
            if response:
                emotion = self.parser.classify_emotion(response)
                await self._speak_response(response, emotion)
                
        except Exception as e:
            print(f"{COLOR_RED}[ERRO] Falha ao ler clipboard: {e}{COLOR_RESET}")
            await self._speak_simple("Não consegui ler o clipboard.")

    async def _speak_simple(self, text: str) -> None:
        """Fala texto simples sem adicionar ao histórico."""
        try:
            emotion = self.parser.classify_emotion(text) if self.parser else "Neutra"
            clean_text = clean_text_for_tts(text)
            
            audio_bytes = await self.tts.generate_audio_bytes(clean_text, emotion)
            self._play_bytes(audio_bytes)
        except Exception as e:
            print(f"{COLOR_YELLOW}[AVISO] Erro no TTS simples: {e}{COLOR_RESET}")

    async def _speak_response(self, text: str, emotion: str) -> None:
        """Fala uma resposta formatada."""
        try:
            clean_text = clean_text_for_tts(text)
            audio_bytes = await self.tts.generate_audio_bytes(clean_text, emotion)
            self._play_bytes(audio_bytes)
        except Exception as e:
            print(f"{COLOR_YELLOW}[AVISO] Erro no TTS: {e}{COLOR_RESET}")

    async def _generate_proactive_response(self, action_data: tuple) -> None:
        """Generate a proactive response usando sistema Shogun-style de skills com cooldowns."""
        try:
            # action_data é uma tupla (action_name, prompt) do CommentSkill
            if not action_data or len(action_data) != 2:
                return

            action_name, base_prompt = action_data

            # Injetar contexto da conversa no prompt
            if self.chat:
                recent_context = self.chat.get_recent_context(limit=3)
                context_prompt = f"[Contexto recente da conversa]: {recent_context}\n\n[Prompt da ação]: {base_prompt}"
            else:
                context_prompt = base_prompt

            # Formata prompt proativo completo
            from core.proactive_engine import format_proactive_prompt
            full_prompt = format_proactive_prompt(context_prompt)

            # Detecta se é skill de visão
            is_vision_skill = action_name == "comentar_tela"

            if is_vision_skill and self.screen_reader and self.chat:
                # SKILL DE VISÃO PROATIVA
                try:
                    base64_img = self.screen_reader.capture_screen_base64()
                    response = await self.chat.chat_with_vision(full_prompt, base64_img, user_emotion="neutral")
                except Exception as e:
                    print(f"[ERRO] Falha na visão proativa: {e}")
                    response = "Minha visão tá embaçada, não consigo ver a tela agora!"
            else:
                # Resposta normal sem visão
                response = await self._call_llm_without_history(full_prompt)

            if response:
                # Classify emotion
                emotion = self.parser.classify_emotion(response)
                clean_text = remove_emojis(response)

                # Log CLARO que é proativo com nome da ação
                print(f"{COLOR_GREEN}IA [Proativo - {action_name}]: [{emotion}] {clean_text}{COLOR_RESET}")

                # Log no dashboard
                if self.ai_log:
                    self.ai_log.info(f"Proativo ({action_name}): {clean_text}")

                # TTS direto (chunking desativado)
                audio_bytes = await self.tts.generate_audio_bytes(clean_text, emotion)
                self._play_bytes(audio_bytes)

                # Broadcast to dashboard
                if self.dashboard and self.dashboard_running:
                    self.dashboard.broadcast_chat_message(f"[Proativo: {action_name}]", clean_text, emotion, "neutral")

        except Exception as e:
            print(f"[ERRO] Falha na resposta proativa: {e}")

    async def _call_llm_without_history(self, prompt: str) -> str:
        """Call LLM sem adicionar à conversa (para prompts proativos que não são memória)."""
        # Build temporary messages without saving
        messages = [{"role": "system", "content": self.chat._build_system_prompt()}]
        messages.append({"role": "user", "content": prompt})

        # Call LLM via multi-provider fallback
        return await chat_completion(messages, mode="text")

    def _on_speech_detected(self, audio_np) -> None:
        """Callback when speech is detected in voice mode."""
        import numpy as np

        try:
            sample_rate = self.config.get("audio", {}).get("sample_rate", 16000)

            # Log de captura de áudio para dashboard
            if self.voice_log:
                self.voice_log.info("Fala detectada", {"samples": len(audio_np), "duration": round(len(audio_np) / sample_rate, 2)})

            # 1. Detect user emotion (se disponível)
            if self.audio_emotion is not None:
                user_emotion, confidence = self.audio_emotion.detect(audio_np, sample_rate)
                self.chat.update_user_emotion(user_emotion, confidence)
                self.brain["user_emotion"] = user_emotion

                # Log de detecção de emoção para dashboard
                if self.voice_log:
                    self.voice_log.info(f"Emoção detectada: {user_emotion}", {"confidence": round(confidence, 2)})
            else:
                # Fallback: emoção neutra se detector não disponível
                user_emotion = "neutral"
                self.brain["user_emotion"] = user_emotion

            # 2. Transcribe
            stt_start = time_module.time()
            text = self.stt.transcribe_buffer(audio_np, sample_rate)
            stt_time = time_module.time() - stt_start

            # Log de transcrição STT para dashboard
            if self.voice_log and text:
                self.voice_log.info(f"Transcrição: {text}", {"language": "pt", "device": self.stt.device if self.stt else "unknown"})

            if not text or not text.strip():
                if self.voice_log:
                    self.voice_log.warn("Transcrição vazia")
                return

            print(f"{COLOR_BLUE}Você (voz): {text}{COLOR_RESET}")

            # COOLDOWN ADAPTATIVO: Reset timer quando usuário fala (grace period)
            if self.proactive_engine:
                self.proactive_engine.reset_timer()

            # NOVO: Verificar comandos de voz antes de mandar pro LLM
            if self.voice_commands:
                action, param = self.voice_commands.process(text)
                if action:
                    # É um comando de voz - processa e não manda pro LLM
                    is_command = asyncio.run(self._handle_voice_command(action, param, text))
                    if is_command:
                        return

            # 3. Process through chat (só chega aqui se não for comando)
            # Passa stt_time para métricas
            asyncio.run(self._process_and_respond(text, user_emotion, stt_time))

        except Exception as e:
            print(f"{COLOR_RED}[ERRO] Erro no processamento de voz: {e}{COLOR_RESET}")
            if self.voice_log:
                self.voice_log.error(f"Erro no processamento de voz: {e}")

    async def _process_and_respond(self, user_text: str, user_emotion: str = "neutral", stt_time: float = 0.0) -> None:
        """Process user input and generate response."""
        start_time = time_module.time()  # Marca início do processamento

        try:
            # Log mensagem do usuário para dashboard
            if self.ai_log:
                self.ai_log.info(f"User: {user_text}", {"user_emotion": user_emotion})

            # Injeta contexto de backlog (tópicos pendentes) antes do chat
            if self.context_backlog:
                backlog_text = self.context_backlog.get_context_injection()
                if backlog_text:
                    self.chat.set_backlog_context(backlog_text)
                    # Marca como processado
                    pending = self.context_backlog.get_pending()
                    self.context_backlog.mark_all_processed([p['id'] for p in pending])
                else:
                    self.chat.set_backlog_context("")

            # Obtém resposta pura do LLM (sem tags de emoção)
            llm_start = time_module.time()
            raw_response = await self.chat.chat(user_text, user_emotion=user_emotion)
            llm_time = time_module.time() - llm_start

            # Detecta emoção do usuário no texto para contexto empático
            detected_user_emotion = self.parser.detect_user_emotion(user_text)
            # Override se detectamos algo mais específico que o áudio não pegou
            if detected_user_emotion != "Neutra":
                user_emotion = detected_user_emotion

            # Classifica emoção localmente baseada no conteúdo + contexto do usuário
            emotion = self.parser.classify_emotion(raw_response, user_emotion=user_emotion)
            clean_text = raw_response  # No tags to remove

            # Log resposta da IA com emoção classificada para dashboard
            assistant_name = self.config.get("assistant", {}).get("name", "Assistente")
            if self.ai_log:
                self.ai_log.info(f"{assistant_name}: {clean_text}", {"emotion": emotion, "user_emotion": user_emotion})

            # Extrai fatos da conversa para memória de longo prazo
            if self.memory_manager:
                self.memory_manager.extract_facts_from_message(user_text, clean_text)
                self.memory_manager.log_session_event(f"User: {user_text[:50]}... | {assistant_name}: {clean_text[:50]}...")
            
            # Mood Engine removido - não utilizado
            # if self.mood_engine:
            #     self.mood_engine.update_mood(user_emotion, user_text)
            #     self.mood_engine.decay_mood()
            #     if self.chat:
            #         mood_prompt = self.mood_engine.get_mood_prompt()
            #         self.chat.set_mood_context(mood_prompt)

            # Update brain
            self.chat.update_brain(emotion, 0.7)
            self.brain["current_emotion"] = emotion
            self.brain["interaction_count"] = self.brain.get("interaction_count", 0) + 1

            # Display (clean for terminal)
            clean_text_display = remove_emojis(clean_text)
            log('CHAT', f'[{emotion}] {clean_text_display}')

            # Prepara texto para TTS (remove emojis e caracteres especiais)
            tts_text = remove_emojis(clean_text)
            tts_text = tts_text.replace('¬', '').replace('•', '').replace('*', '')
            tts_text = re.sub(r'\s+', ' ', tts_text).strip()

            # TTS: Gera áudio inteiro como um único arquivo (sem chunking)
            # Chunking desativado - gera áudio completo mais rápido e sem cortes
            if self.audio_pipeline:
                self.audio_pipeline.set_speaking(True)
            try:
                tts_start = time_module.time()
                
                # Gera áudio inteiro de uma vez (mais rápido, sem cortes)
                audio_bytes = await self.tts.generate_audio_bytes(tts_text, emotion)
                self._play_bytes(audio_bytes)

                tts_time = time_module.time() - tts_start
                tts_elapsed_ms = tts_time * 1000

                # Métricas de performance
                total_time = time_module.time() - start_time
                stt_str = f"STT: {stt_time:.1f}s | " if stt_time > 0 else ""
                log('PERF', f'{stt_str}LLM: {llm_time:.1f}s | TTS: {tts_time:.1f}s | Total: {total_time:.1f}s')

                if self.tts_log:
                    self.tts_log.info(f"TTS gerado", {
                        "text": tts_text[:50] + "..." if len(tts_text) > 50 else tts_text,
                        "emotion": emotion,
                        "time_ms": round(tts_elapsed_ms, 1),
                        "chunks": 1
                    })

            except Exception as e:
                log('ERROR', f'Falha no TTS: {e}')
                # Fallback: tenta texto completo
                try:
                    audio_bytes = await self.tts.generate_audio_bytes(tts_text, emotion)
                    self._play_bytes(audio_bytes)
                except Exception as fallback_e:
                    log('ERROR', f'Fallback TTS também falhou: {fallback_e}')
                    raise
            finally:
                if self.audio_pipeline:
                    self.audio_pipeline.set_speaking(False)

            # Broadcast to dashboard
            if self.dashboard and self.dashboard_running:
                self.dashboard.broadcast_chat_message(user_text, clean_text, emotion, user_emotion)
                self.dashboard.broadcast_emotion_change(emotion, user_emotion)

        except Exception as e:
            log('ERROR', f'Erro ao processar: {e}')
            if self.ai_log:
                self.ai_log.error(f"Erro no processamento: {e}")

    async def process_text_input(self, text: str) -> None:
        """Process text input (for dashboard/repl)."""
        # Inicia timer para modo texto (STT = 0 pois é texto)
        start_time = time_module.time()

        # COOLDOWN ADAPTATIVO: Reset proactive timer quando usuário manda texto
        if self.proactive_engine:
            self.proactive_engine.reset_timer()
        
        # NOVO: Reset PatienceWrapper quando usuário interage
        if self.patience_wrapper:
            self.patience_wrapper.poke()

        # DEBUG: Log do input recebido
        log('DEBUG', f"process_text_input: '{text}'")

        # Verificar comandos de voz primeiro (inclui visão)
        if self.voice_commands:
            action, param = self.voice_commands.process(text)
            log('DEBUG', f'voice_commands.process retornou: action={action}, param={param}')
            if action:
                is_command = await self._handle_voice_command(action, param, text)
                log('DEBUG', f'_handle_voice_command retornou: {is_command}')
                if is_command:
                    return

        # BUGFIX: Fallback para keywords de visão que o regex pode não pegar
        # Inclui variações com possessivos (minha/sua) e artigos (a/minha/essa)
        vision_keywords = [
            # Variações comuns
            "veja a tela", "ver a tela", "o que tá na tela", "olha a tela",
            "descreve a tela", "o que você vê", "comenta a tela", "analisa a tela",
            "o que tem na tela", "o que está acontecendo", "me descreve a tela",
            # Variações com possessivos (BUGFIX: adicionadas)
            "olha minha tela", "veja minha tela", "descreve minha tela",
            "olha essa tela", "veja essa tela", "o que tem aqui",
            "o que você vê na tela", "o que você vê aqui",
            # Comandos curtos
            "analisa isso", "comenta isso", "olha isso", "o que é isso"
        ]
        if any(keyword in text.lower() for keyword in vision_keywords):
            await self._handle_vision_screen(user_prompt=text)
            # Métricas para comando de visão
            total_time = time_module.time() - start_time
            log('PERF', f'Vision: {total_time:.1f}s')
            return

        await self._process_and_respond(text, self.brain.get("user_emotion", "neutral"), 0.0)

    def _play_bytes(self, audio_bytes: bytes) -> None:
        """Play audio bytes."""
        try:
            sound = pygame.mixer.Sound(BytesIO(audio_bytes))
            channel = sound.play()
            if channel:
                while channel.get_busy():
                    time_module.sleep(0.05)
        except Exception as e:
            print(f"{COLOR_YELLOW}[AVISO] Erro ao reproduzir áudio: {e}{COLOR_RESET}")

    def start_dashboard(self) -> None:
        """Start dashboard in background thread."""
        if self.dashboard:
            self.dashboard.start(blocking=False)
            self.dashboard_running = True

    def start_voice_mode(self) -> None:
        """Start voice mode."""
        if self.audio_pipeline:
            self.audio_pipeline.start()
            self.voice_mode = True
            print(f"{COLOR_GREEN}[INFO] Modo voz ativado. Fale algo!{COLOR_RESET}")
        else:
            print(f"{COLOR_YELLOW}[AVISO] Pipeline de áudio não disponível{COLOR_RESET}")

    def stop_voice_mode(self) -> None:
        """Stop voice mode."""
        if self.audio_pipeline:
            self.audio_pipeline.stop()
            self.voice_mode = False

    def start_ptt_mode(self) -> None:
        """Start Push-to-Talk voice mode."""
        if not _PTT_AVAILABLE or not PTTPipeline:
            print(f"{COLOR_YELLOW}[AVISO] PTT não disponível. Instale: pip install pynput{COLOR_RESET}")
            return

        try:
            # Create PTT pipeline with same config
            audio_config = self.config.get("audio", {})
            self.ptt_pipeline = PTTPipeline(
                audio_config,
                self._on_speech_detected,
                ptt_key="right ctrl"
            )
            self.ptt_pipeline.start()
            self.voice_mode = True
            print(f"{COLOR_GREEN}[INFO] PTT ativado. Segure Right Ctrl para falar!{COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_RED}[ERRO] Falha ao iniciar PTT: {e}{COLOR_RESET}")
            self.ptt_pipeline = None

    def stop_ptt_mode(self) -> None:
        """Stop Push-to-Talk voice mode."""
        if self.ptt_pipeline:
            self.ptt_pipeline.stop()
            self.ptt_pipeline = None
            self.voice_mode = False
            print(f"{COLOR_GREEN}[INFO] PTT desativado{COLOR_RESET}")

    def repl_loop(self) -> None:
        """REPL loop for text mode."""
        print(f"\n{COLOR_YELLOW}Comandos: /apps, /abrir <app>, /emocoes, /testarvoz, /limpar, /ajuda, /voz, /dashboard, /sair{COLOR_RESET}\n")
        print(f"{COLOR_YELLOW}NOVOS: /modo escrita, /ativar clipboard, /desativar clipboard, /skills{COLOR_RESET}\n")

        while True:
            try:
                # NOVO: Verifica skills autônomas (chama a cada ~5 segundos aproximadamente)
                if self.skill_system and hasattr(self.skill_system, 'check_and_execute'):
                    try:
                        self.skill_system.check_and_execute()
                    except Exception:
                        pass  # Silencioso para não poluir o REPL
                user_input = input(f"{COLOR_BLUE}Você: {COLOR_RESET}").strip()

                if not user_input:
                    continue

                # Exit commands
                if user_input.lower() in ("sair", "exit", "quit", "tchau", "bye") or user_input.lower() == "/sair":
                    print(f"{COLOR_GREEN}[Neutra] Tchau! Até mais!{COLOR_RESET}")
                    break

                # Comandos com / prefix são tratados LOCALMENTE (não vão para o LLM)
                if user_input.startswith("/"):
                    cmd_parts = user_input[1:].split(maxsplit=1)
                    cmd = cmd_parts[0].lower() if cmd_parts else ""
                    args = cmd_parts[1] if len(cmd_parts) > 1 else ""

                    # Comando /emocoes: local only, lista emoções disponíveis
                    if cmd in ("emocoes", "emoções"):
                        print(f"""
{COLOR_YELLOW}🎭 Emoções Disponíveis (simplificado):{COLOR_RESET}
  {COLOR_GREEN}Feliz, Neutra{COLOR_RESET}
""")
                        continue  # NÃO manda pra LLM

                    # Comando /ajuda: local only, mostra ajuda
                    elif cmd in ("ajuda", "help"):
                        print("""
Comandos disponíveis:
  /apps         - Lista apps instalados
  /abrir <app>  - Abre um aplicativo
  /emocoes      - Lista emoções disponíveis
  /testarvoz    - Testa emoções do TTS (Feliz/Neutra)
  /limpar       - Limpa histórico de conversa
  /ajuda        - Mostra esta ajuda
  /sair         - Encerra o programa
  
NOVOS COMANDOS:
  /modo escrita         - Ativa/desativa modo escrita (IA comenta)
  /ativar clipboard     - Ativa captura de texto do clipboard
  /desativar clipboard  - Desativa captura de texto
  /skills               - Mostra status das skills autônomas
""")
                        continue  # NÃO manda pra LLM

                    # Comando /apps: local only, lista apps disponíveis
                    elif cmd == "apps":
                        apps = self.launcher.list_apps()
                        print(f"{COLOR_YELLOW}Apps disponíveis:{COLOR_RESET} {', '.join(apps) if apps else 'Nenhum'}")
                        continue  # NÃO manda pra LLM

                    # Comando /abrir: local only, abre aplicativo
                    elif cmd == "abrir":
                        if not args:
                            print(f"{COLOR_YELLOW}Uso: /abrir <app>{COLOR_RESET}")
                        else:
                            success, msg = self.launcher.launch(args)
                            print(f"{COLOR_GREEN if success else COLOR_RED}{msg}{COLOR_RESET}")
                        continue  # NÃO manda pra LLM

                    # Comando /testarvoz: local only, testa emoções do TTS
                    elif cmd == "testarvoz":
                        print(f"{COLOR_YELLOW}[INFO] Testando emoções do TTS...{COLOR_RESET}")
                        asyncio.run(self.tts.test_all_emotions())
                        continue  # NÃO manda pra LLM

                    # Comando /limpar: local only, limpa histórico de chat
                    elif cmd == "limpar":
                        self.chat.clear_history()
                        print(f"{COLOR_GREEN}[Neutra] Histórico limpo!{COLOR_RESET}")
                        continue  # NÃO manda pra LLM

                    # Comando /sair: local only, sai do programa
                    elif cmd == "sair":
                        print(f"{COLOR_GREEN}[Neutra] Tchau! Até mais!{COLOR_RESET}")
                        break

                    # Comandos que ainda precisam de processamento especial
                    elif cmd == "voz":
                        if not self.voice_mode:
                            self.start_voice_mode()
                            print(f"{COLOR_GREEN}[INFO] Modo voz ativado. Digite /texto para voltar.{COLOR_RESET}")
                        else:
                            print(f"{COLOR_YELLOW}[INFO] Já está em modo voz{COLOR_RESET}")
                        continue

                    elif cmd == "texto":
                        if self.voice_mode:
                            self.stop_voice_mode()
                            print(f"{COLOR_GREEN}[INFO] Modo texto ativado.{COLOR_RESET}")
                        continue

                    elif cmd == "dashboard":
                        self.start_dashboard()
                        dash_config = self.config.get("dashboard", {})
                        port = dash_config.get("port", 5000)
                        print(f"{COLOR_GREEN}[INFO] Dashboard em http://localhost:{port}{COLOR_RESET}")
                        continue

                    elif cmd == "status":
                        assistant_name = self.config.get("assistant", {}).get("name", "Assistente")
                        print(f"{COLOR_GREEN}[Neutra] {assistant_name}: {self.brain.get('current_emotion', 'Neutra')}, Usuário: {self.brain.get('user_emotion', 'neutral')}{COLOR_RESET}")
                        continue

                    # NOVO: Comando /modo escrita - Ativa/desativa modo escrita
                    elif cmd in ("modo escrita", "escrita"):
                        if self.writing_mode:
                            if self.writing_mode.is_active():
                                self.writing_mode.stop()
                                print(f"{COLOR_GREEN}[INFO] Modo escrita desativado{COLOR_RESET}")
                            else:
                                self.writing_mode.start()
                                print(f"{COLOR_GREEN}[INFO] Modo escrita ativado. A IA vai comentar enquanto você digita.{COLOR_RESET}")
                        else:
                            print(f"{COLOR_YELLOW}[AVISO] Writing Mode não disponível{COLOR_RESET}")
                        continue

                    # NOVO: Comando /ativar clipboard
                    elif cmd in ("ativar clipboard", "clipboard on"):
                        if self.text_capture:
                            self.text_capture.start()
                            print(f"{COLOR_GREEN}[INFO] Captura de clipboard ativada{COLOR_RESET}")
                        else:
                            print(f"{COLOR_YELLOW}[AVISO] Text Capture não disponível{COLOR_RESET}")
                        continue

                    # NOVO: Comando /desativar clipboard
                    elif cmd in ("desativar clipboard", "clipboard off"):
                        if self.text_capture:
                            self.text_capture.stop()
                            print(f"{COLOR_GREEN}[INFO] Captura de clipboard desativada{COLOR_RESET}")
                        else:
                            print(f"{COLOR_YELLOW}[AVISO] Text Capture não disponível{COLOR_RESET}")
                        continue

                    # NOVO: Comando /skills - Mostra status das skills
                    elif cmd == "skills":
                        if self.skill_system:
                            stats = self.skill_system.get_stats()
                            print(f"{COLOR_YELLOW}Skills Autônomas:{COLOR_RESET}")
                            print(f"  Ativas: {stats.get('active_count', 0)}")
                            print(f"  Totais: {stats.get('total_count', 0)}")
                            for skill_name, skill in stats.get('skills', {}).items():
                                status = "✅" if skill.get('enabled') else "❌"
                                print(f"  {status} {skill.get('name')} (cooldown: {skill.get('cooldown_remaining', 0):.0f}s)")
                        else:
                            print(f"{COLOR_YELLOW}[AVISO] Skill System não disponível{COLOR_RESET}")
                        continue

                    # Comando não reconhecido: manda para o LLM como mensagem normal
                    else:
                        # Não é comando conhecido, trata como mensagem normal
                        pass  # Fall through to normal chat flow

                # Normal chat flow (comandos desconhecidos ou mensagens sem /)
                if not user_input.startswith("/"):
                    asyncio.run(self._process_and_respond(user_input))

            except KeyboardInterrupt:
                print(f"\n{COLOR_GREEN}[Neutra] Interrompido. Até logo!{COLOR_RESET}")
                break
            except Exception as e:
                print(f"{COLOR_RED}[ERRO] {e}{COLOR_RESET}")

        # Cleanup
        if self.voice_mode:
            if self.ptt_pipeline:
                self.stop_ptt_mode()
            else:
                self.stop_voice_mode()
        if self.dashboard:
            self.dashboard.stop()
        pygame.mixer.quit()


def main():
    """Main entry point."""
    print_header()

    assistant = Assistant()

    if not assistant.initialize():
        print(f"{COLOR_RED}[ERRO FATAL] Não foi possível inicializar o assistente{COLOR_RESET}")
        sys.exit(1)

    # Welcome message - SAUDAÇÃO DINÂMICA VIA LLM
    greeting = asyncio.run(assistant._get_greeting())
    welcome_text = f"[Feliz] {greeting}"
    print(f"{COLOR_GREEN}{welcome_text}{COLOR_RESET}")

    try:
        emotion, clean_welcome = assistant.parser.parse(welcome_text)
        clean_welcome = remove_emojis(clean_welcome)
        audio_path = asyncio.run(assistant.tts.generate_audio(clean_welcome, emotion))
        assistant.tts.play_audio_file(audio_path)
    except Exception as e:
        print(f"{COLOR_YELLOW}[AVISO] Erro na boas-vindas: {e}{COLOR_RESET}")

    # Ask mode
    print("\n" + "=" * 50)
    print("Escolha o modo:")
    print("1. Texto (REPL)")
    if assistant.audio_pipeline:
        print("2. Voz (VAD contínuo - ouve tudo)")
        if _PTT_AVAILABLE and PTTPipeline:
            print("3. Voz (Push-to-Talk - Right Ctrl)")
    if assistant.dashboard:
        print("4. Dashboard (web)")
    print("=" * 50)

    # Build valid choices based on availability
    valid_choices = ["1"]
    if assistant.audio_pipeline:
        valid_choices.append("2")
        if _PTT_AVAILABLE and PTTPipeline:
            valid_choices.append("3")
    if assistant.dashboard:
        valid_choices.append("4")

    try:
        choice = input(f"Escolha ({'/'.join(valid_choices)}): ").strip()
    except KeyboardInterrupt:
        print("\n[INFO] Saindo...")
        sys.exit(0)

    if choice == "2" and assistant.audio_pipeline:
        assistant.start_voice_mode()
        print(f"{COLOR_GREEN}[INFO] Modo voz (VAD) ativado. Ouvindo continuamente...{COLOR_RESET}")
        print(f"{COLOR_YELLOW}[AVISO] Proteção anti-TV: áudio >15s será descartado{COLOR_RESET}")
        try:
            while True:
                time_module.sleep(1)
        except KeyboardInterrupt:
            assistant.stop_voice_mode()
    elif choice == "3" and _PTT_AVAILABLE and PTTPipeline:
        assistant.start_ptt_mode()
        print(f"{COLOR_GREEN}[INFO] Modo Push-to-Talk ativado.{COLOR_RESET}")
        print(f"{COLOR_BLUE}[INFO] Segure RIGHT CTRL para falar, solte para enviar{COLOR_RESET}")
        try:
            while True:
                time_module.sleep(1)
        except KeyboardInterrupt:
            assistant.stop_ptt_mode()
    elif choice == "4" and assistant.dashboard:
        assistant.start_dashboard()
        dash_config = assistant.config.get("dashboard", {})
        port = dash_config.get("port", 5000)
        print(f"[INFO] Dashboard em http://localhost:{port}")
        print("[INFO] Pressione Ctrl+C para parar.")
        try:
            while True:
                time_module.sleep(1)
        except KeyboardInterrupt:
            assistant.dashboard.stop()
    else:
        assistant.repl_loop()

    # Salva memórias e gera resumo do dia ao encerrar
    if assistant.memory_manager:
        try:
            # Gerar resumo do dia usando LLM se disponível
            session_topics = assistant.memory_manager.get_session_topics()
            today = datetime.now().strftime("%Y-%m-%d")
            
            if assistant.chat and session_topics:
                # Gerar resumo mais elaborado com LLM
                try:
                    topics_text = "\n".join([f"- {t}" for t in session_topics])
                    summary_prompt = f"Resuma em 1 frase curta os seguintes tópicos de conversa de hoje:\n{topics_text}"
                    
                    summary = asyncio.run(assistant.chat.chat(summary_prompt, user_emotion="neutral"))
                    # Limpa o histórico da mensagem de summary (não deve ficar no contexto)
                    assistant.chat.history = assistant.chat.history[:-2] if len(assistant.chat.history) >= 2 else []
                except Exception:
                    # Fallback para resumo simples
                    summary = assistant.memory_manager.generate_daily_summary()
            else:
                summary = assistant.memory_manager.generate_daily_summary()
            
            assistant.memory_manager.save_conversation_summary(today, summary)
            
            # Atualizar last_seen
            assistant.memory_manager.update_last_seen()
            
            # Salvar no arquivo
            assistant.memory_manager.save()
            log('MEMORY', f'Memórias salvas. Resumo do dia: {summary}')
        except Exception as e:
            log('WARN', f'Erro ao salvar memórias: {e}')

    # Salva estado do mood ao encerrar
    # if assistant.mood_engine:
    #     try:
    #         assistant.mood_engine.save()
    #         print(f"{COLOR_GREEN}[INFO] Mood salvo: {assistant.mood_engine.get_mood_display()}{COLOR_RESET}")
    #     except Exception as e:
    #         print(f"{COLOR_YELLOW}[AVISO] Erro ao salvar mood: {e}{COLOR_RESET}")

    # Salva context backlog e limpa itens antigos ao encerrar
    if assistant.context_backlog:
        try:
            assistant.context_backlog.clear_old_items(days=7)  # Limpa itens antigos
            assistant.context_backlog.save()
            stats = assistant.context_backlog.get_stats()
            print(f"{COLOR_GREEN}[INFO] Backlog salvo ({stats['pending']} pendentes){COLOR_RESET}")
        except Exception as e:
            print(f"{COLOR_YELLOW}[AVISO] Erro ao salvar backlog: {e}{COLOR_RESET}")

    print(f"{COLOR_GREEN}[INFO] Até mais!{COLOR_RESET}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{COLOR_RED}[ERRO FATAL] {e}{COLOR_RESET}")
        sys.exit(1)
