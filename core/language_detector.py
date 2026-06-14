"""Language Detector - Detecção simples de idioma. PASSO 12."""

from typing import Dict, Optional


class LanguageDetector:
    """Detector simples de idioma baseado em palavras-chave."""
    
    # Palavras identificadoras por idioma
    LANGUAGE_MARKERS = {
        'pt': ['oi', 'olá', 'bom dia', 'boa tarde', 'como vai', 'tudo bem', 
               'obrigado', 'por favor', 'sim', 'não', 'você', 'está', 'muito'],
        'en': ['hello', 'hi', 'good morning', 'good afternoon', 'how are you',
               'thank you', 'please', 'yes', 'no', 'you', 'are', 'very', 'the'],
        'es': ['hola', 'buenos días', 'buenas tardes', 'cómo estás', 'gracias',
               'por favor', 'sí', 'no', 'tú', 'estás', 'muy', 'el'],
        'fr': ['bonjour', 'salut', 'bonsoir', 'comment allez-vous', 'merci',
               's\'il vous plaît', 'oui', 'non', 'vous', 'êtes', 'très', 'le'],
    }
    
    # Respostas de detecção de idioma
    LANGUAGE_RESPONSES = {
        'pt': "Tô falando português, seu doido!",
        'en': "I can speak English if you want, but I'm cooler in Portuguese!",
        'es': "¡Hablo español también, pero prefiero portugués, está más chulo!",
        'fr': "Je parle un peu français, mais le portugais c'est plus cool!",
    }
    
    @classmethod
    def detect(cls, text: str) -> str:
        """
        Detecta idioma do texto.
        
        Returns:
            Código do idioma ('pt', 'en', 'es', 'fr')
        """
        text_lower = text.lower()
        scores = {}
        
        for lang, markers in cls.LANGUAGE_MARKERS.items():
            score = sum(1 for marker in markers if marker in text_lower)
            scores[lang] = score
        
        # Retorna idioma com maior score, ou 'pt' como padrão
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'pt'  # Default
    
    @classmethod
    def should_switch_response(cls, detected_lang: str, current_lang: str = 'pt') -> Optional[str]:
        """
        Retorna mensagem se detectar mudança de idioma.
        
        Returns:
            Mensagem de resposta ou None
        """
        if detected_lang != current_lang:
            return cls.LANGUAGE_RESPONSES.get(detected_lang)
        return None
    
    @classmethod
    def get_system_prompt_modifier(cls, lang: str) -> str:
        """Retorna modificador de system prompt para idioma."""
        modifiers = {
            'pt': "",  # Português é o default
            'en': "The user is speaking English. You can respond in English but keep your personality - sarcastic, confident, and playful.",
            'es': "El usuario habla español. Puedes responder en español manteniendo tu personalidad - sarcástica, segura y juguetona.",
            'fr': "L'utilisateur parle français. Tu peux répondre en français en gardant ta personnalité - sarcastique, sûre de toi et ludique.",
        }
        return modifiers.get(lang, "")


def detect_language(text: str) -> str:
    """Função utilitária para detectar idioma."""
    return LanguageDetector.detect(text)


if __name__ == "__main__":
    # Testes
    test_phrases = [
        "Olá, como você está?",
        "Hello, how are you today?",
        "Hola, ¿cómo estás?",
        "Bonjour, comment allez-vous?",
    ]
    
    for phrase in test_phrases:
        lang = LanguageDetector.detect(phrase)
        response = LanguageDetector.should_switch_response(lang)
        print(f"'{phrase}' -> {lang}")
        if response:
            print(f"  Resposta: {response}")
