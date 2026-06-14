"""Emotion parser module for extracting emotion tags from LLM responses."""

import re
from typing import Tuple, Dict, List

# Emotion keywords simplificado - apenas 2 emoções para V2
EMOTION_KEYWORDS: Dict[str, List[str]] = {
    "Feliz": [
        "feliz", "alegre", "contente", "animada", "legal", "top", "incrível", "maravilhoso",
        "amei", "adorei", "show", "massa", "demais", "genial", "perfeito",
        "yeah", "eba", "oba", "uhul", "haha", "kkk", "rsrs", "muito bom",
        "amor", "sorrindo", "felizão", "felizona", "joia", "blz", "tudo certo",
        "tranquilo", "de boa", "maravilha", "fantástico", "brilhante"
    ]
}

# Negation words that invert emotion polarity
NEGATION_WORDS = ["não", "nunca", "nem", "nada de", "longe de", "sem", "jamais"]

# Emotion emoji mappings simplificado
EMOJI_MAP = {
    "😍": "Feliz", "🥰": "Feliz", "😊": "Feliz", "🙂": "Feliz", "😀": "Feliz", "😃": "Feliz",
    "🎉": "Feliz", "🎊": "Feliz", "🔥": "Feliz", "✨": "Feliz", "⚡": "Feliz"
}

# Priority order simplificado
EMOTION_PRIORITY = ["Feliz", "Neutra"]

# Emotion aliases simplificado (2 emoções para V2)
EMOTION_ALIASES = {
    "Feliz": ["feliz", "alegre", "contente", "animada", "cheerful", "happy"],
    "Neutra": ["neutra", "neutro", "normal", "neutral"]
}

# Build reverse mapping: alias -> canonical
_ALIAS_TO_CANONICAL = {}
for canonical, aliases in EMOTION_ALIASES.items():
    _ALIAS_TO_CANONICAL[canonical.lower()] = canonical
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical

# Regex to match emotion tag at the START of string: [Emotion]
_EMOTION_TAG_REGEX = re.compile(r'^\[([^\]]+)\]\s*')


class EmotionParser:
    """Parser for extracting emotion tags from text responses."""

    def __init__(self):
        """Initialize the emotion parser."""
        self.valid_emotions = set(EMOTION_ALIASES.keys())

    def parse(self, text: str) -> Tuple[str, str]:
        """
        Parse emotion tag from the beginning of text.

        Args:
            text: Text that may start with [Emotion] tag

        Returns:
            Tuple of (emotion_name, clean_text)
        """
        return parse_emotion_tag(text)

    def validate(self, emotion: str) -> str:
        """
        Validate and normalize an emotion name.

        Args:
            emotion: Raw emotion string

        Returns:
            Canonical emotion name or "Neutra" if unknown
        """
        return validate_emotion(emotion)

    def detect_user_emotion(self, user_text: str) -> str:
        """
        Detecta emoção do usuário baseada no input dele.
        Retorna apenas Feliz ou Neutra (simplificado).
        
        Args:
            user_text: Texto do usuário
            
        Returns:
            Nome da emoção detectada (Feliz ou Neutra)
        """
        if not user_text or not user_text.strip():
            return "Neutra"
            
        text_lower = user_text.lower()
        
        happy_keywords = [
            "feliz", "alegre", "contente", "animado", "animada", "amo isso",
            "adorei", "maravilhoso", "incrível", "top", "demais", "genial",
            "bom", "boa", "ótimo", "ótima", "legal", "massa", "show"
        ]
        
        for kw in happy_keywords:
            if kw in text_lower:
                return "Feliz"
                
        return "Neutra"

    def classify_emotion(self, text: str, user_emotion: str = None) -> str:
        """
        Classify emotion from text - versão simplificada (apenas Feliz/Neutra).

        Args:
            text: Text to classify (AI response)
            user_emotion: Emoção detectada do usuário (optional, for context boost)

        Returns:
            Canonical emotion name (Feliz ou Neutra)
        """
        if not text or not text.strip():
            return "Neutra"

        # Initialize scores
        emotion_scores: Dict[str, int] = {"Feliz": 0, "Neutra": 0}
        
        # BOOST: Se usuário está feliz, a IA também fica mais feliz
        if user_emotion == "Feliz":
            emotion_scores["Feliz"] += 5

        # Pattern detection
        repeated_chars = re.findall(r'(.)\1{2,}', text.lower())
        multi_exclamation = bool(re.search(r'[!]{2,}', text))

        # Score keywords
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                kw_lower = kw.lower()
                if re.search(r'\b' + re.escape(kw_lower) + r'\b', text.lower()):
                    emotion_scores[emotion] += 3
                    if repeated_chars:
                        emotion_scores[emotion] += 2

        # Emoji scoring
        for emoji, emotion in EMOJI_MAP.items():
            if emoji in text:
                emotion_scores[emotion] += 4

        # Pattern bonuses
        if multi_exclamation:
            emotion_scores["Feliz"] += 2

        # Find max score
        max_score = max(emotion_scores.values())

        # If nothing detected or all scores <= 0, return Neutra
        if max_score <= 0:
            return "Neutra"

        # Get all emotions with max score
        top_emotions = [e for e, s in emotion_scores.items() if s == max_score]

        # Tie-breaking by priority order
        for emotion in EMOTION_PRIORITY:
            if emotion in top_emotions:
                return emotion

        return "Neutra"


def parse_emotion_tag(text: str) -> Tuple[str, str]:
    """
    Extract emotion tag from the beginning of text.
    Removes ALL consecutive tags at the beginning, keeping only the first emotion.

    Args:
        text: Text that may start with [Emotion] tag(s)

    Returns:
        Tuple of (emotion_name, clean_text_without_any_tags)
    """
    if not text:
        return ("Neutra", "")

    match = _EMOTION_TAG_REGEX.match(text)
    if not match:
        return ("Neutra", text)

    raw_emotion = match.group(1).strip()
    remaining = text[match.end():].strip()

    # Loop to consume any additional tags at the beginning
    while True:
        extra_match = _EMOTION_TAG_REGEX.match(remaining)
        if not extra_match:
            break
        remaining = remaining[extra_match.end():].strip()

    emotion = validate_emotion(raw_emotion)
    return (emotion, remaining)


def validate_emotion(emotion: str) -> str:
    """
    Validate and normalize an emotion name to its canonical form.

    Args:
        emotion: Raw emotion string (e.g., "feliz", "Feliz", "happy")

    Returns:
        Canonical emotion name (e.g., "Feliz") or "Neutra" if unknown
    """
    if not emotion:
        return "Neutra"

    normalized = emotion.strip().lower()
    canonical = _ALIAS_TO_CANONICAL.get(normalized)

    if canonical:
        return canonical

    # Check for case-insensitive exact match with canonical names
    for valid in EMOTION_ALIASES.keys():
        if normalized == valid.lower():
            return valid

    return "Neutra"


if __name__ == "__main__":
    # Simple tests - versão simplificada (2 emoções)
    test_cases = [
        "[Feliz] E aí! Bora jogar!",
        "[Neutra] Ok, entendi.",
        "Sem tag nenhuma",
        "",
    ]

    print("[INFO] Testando EmotionParser (2 emoções V2 - simplificado):")
    for test in test_cases:
        emotion, text = parse_emotion_tag(test)
        print(f"  Entrada: {repr(test)}")
        print(f"  Saída: emotion={emotion}, text={repr(text)}\n")
