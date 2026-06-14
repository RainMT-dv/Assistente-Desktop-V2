"""Core modules for the Desktop Assistant V2."""

from .logger import log
from .emotion_parser import EmotionParser, parse_emotion_tag, validate_emotion, EMOTION_ALIASES
from .tts_engine import TTSEngine
from .stt_engine import STTEngine
from .chat_manager import ChatManager
# AudioEmotionDetector importado no try/except abaixo
from .proactive_engine import ProactiveEngine, format_proactive_prompt
# TTSChunker removido - chunking desativado, áudio gerado inteiro
# from .tts_chunker import TTSChunker, chunk_text
from .card_manager import CardManager, load_default_card
from .app_launcher import AppLauncher
from .memory_manager import MemoryManager
# MoodEngine removido - não utilizado
# from .mood_engine import MoodEngine
from .context_backlog import ContextBacklog, BacklogPriority
from .screen_reader import ScreenReader, create_vision_messages
from .voice_commands import VoiceCommandProcessor
from .event_watcher import EventWatcher, get_time_based_greeting, is_weekend
from .proactive_skills import ProactiveSkillManager, CommentSkill
from .skill_system import SkillSystem, Skill, CommentSkill as AutonomousCommentSkill
# PatienceWrapper removido - não utilizado
# from .patience_wrapper import PatienceWrapper, PatienceManager
from .context_logger import ContextLogger, ChatManagerContextLogger
from .text_capture import TextCapture, SmartTextCapture
from .writing_mode import WritingMode, WritingModeIntegration
from . import constants

try:
    from .audio_emotion import AudioEmotionDetector
except ImportError:
    AudioEmotionDetector = None  # type: ignore

try:
    from .audio_pipeline import AudioPipeline
except ImportError:
    AudioPipeline = None  # type: ignore

__all__ = [
    "log",
    "EmotionParser",
    "parse_emotion_tag",
    "validate_emotion",
    "EMOTION_ALIASES",
    "TTSEngine",
    "ChatManager",
    "AppLauncher",
    "CardManager",
    "load_default_card",
    "ProactiveEngine",
    "format_proactive_prompt",
    "MemoryManager",
    # "MoodEngine",  # Removido
    "ContextBacklog",
    "CommentSkill",
    "ProactiveSkillManager",
    "SkillSystem",
    "Skill",
    "AutonomousCommentSkill",
    # "PatienceWrapper",  # Removido
    # "PatienceManager",
    "ContextLogger",
    "ChatManagerContextLogger",
    "TextCapture",
    "SmartTextCapture",
    "WritingMode",
    "WritingModeIntegration",
    "STTEngine",
    "AudioEmotionDetector",
    "AudioPipeline",
    "ScreenReader",
    "create_vision_messages",
    "VoiceCommandProcessor",
    "EventWatcher",
    "get_time_based_greeting",
    "is_weekend",
    "constants",
]
