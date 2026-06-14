"""Voice Commands - Processador de comandos de voz do Assistente."""

import random
import re
from datetime import datetime
from typing import Optional, Tuple


class VoiceCommandProcessor:
    """Processa comandos de voz baseado em pattern matching."""

    wake_words = ["assistente", "computador", "hey assistente", "oi assistente"]

    command_patterns = {
        "abrir_app": {
            "patterns": [
                r"\b(abre|abrir|abra)\s+(?:o\s+|a\s+)?(.+)",
                r"\b(abre|abrir|abra)\s+(.+)",
            ],
            "action": "open_app",
        },
        "ler_tela": {
            "patterns": [
                r"\b(l[êe]\s+a\s+tela|ler\s+a\s+tela|o\s+que\s+tem\s+na\s+tela|descreve\s+a\s+tela|o\s+que\s+v[êe]\s+na\s+tela)\b",
            ],
            "action": "read_screen",
        },
        "vision_tela": {
            "patterns": [
                r"\b(o\s+que\s+t[áa]\s+na\s+tela|olha\s+a\s+tela|veja\s+a\s+tela|o\s+que\s+voc[êe]\s+v[êe]|descreve\s+o\s+que\s+v[êe]\s+na\s+tela|o\s+que\s+t[áa]\s+acontecendo\s+na\s+tela)\b",
                r"\b(o\s+que\s+t[áa]\s+na\s+tela|o\s+que\s+voc[êe]\s+est[áa]\s+vendo|comenta\s+a\s+tela|analisa\s+a\s+tela|veja\s+(?:minha|essa)?\s*tela)\b",
            ],
            "action": "vision_screen",
        },
        "ler_clipboard": {
            "patterns": [
                r"\b(l[êe]\s+(?:o\s+)?clipboard|ler\s+(?:o\s+)?clipboard|o\s+que\s+copiei|(?:o\s+)?que\s+t[áa]\s+na\s+.[rea\s+de\s+transfer[êe]ncia|clipboard)\b",
            ],
            "action": "read_clipboard",
        },
        "que_horas": {
            "patterns": [
                r"\b(que\s+horas\s+s[ãa]o|que\s+hora\s+[ée]|me\s+diz\s+as\s+horas|hor[áa]rio|qu[êe]\s+horas)\b",
            ],
            "action": "tell_time",
        },
        "fechar": {
            "patterns": [
                r"\b(fecha|sair|tchau|at[ée]\s+logo|vai\s+embora)\b",
            ],
            "action": "exit",
        },
        "limpar_historico": {
            "patterns": [
                r"\b(limpa\s+(?:o\s+)?hist[óo]rico|apaga\s+(?:o\s+)?hist[óo]rico|esquece\s+(?:o\s+)?que\s+eu\s+disse)\b",
            ],
            "action": "clear_history",
        },
        "status": {
            "patterns": [
                r"\b(como\s+voc[êe]\s+t[áa]|qual\s+[ée]\s+o\s+seu\s+status|status|como\s+est[áa])\b",
            ],
            "action": "status",
        },
        "modo_voz": {
            "patterns": [
                r"\b(ativar\s+voz|modo\s+voz|come[çc]a\s+a\s+ouvir|me\s+escuta)\b",
            ],
            "action": "enable_voice",
        },
        "modo_texto": {
            "patterns": [
                r"\b(desativar\s+voz|para\s+de\s+ouvir|modo\s+texto|s[óo]\s+texto)\b",
            ],
            "action": "disable_voice",
        },
    }

    def __init__(self, wake_words=None):
        """Inicializa o processador de comandos."""
        if wake_words:
            self.wake_words = wake_words
        self.last_command_time = 0
        self.cooldown_seconds = 2  # Cooldown entre comandos

    def process(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Processa texto e retorna (action, param) ou (None, None) se não for comando.

        Args:
            text: Texto reconhecido do STT

        Returns:
            Tuple de (action, param) ou (None, None)
        """
        if not text:
            return None, None

        text_lower = text.lower().strip()

        # Remove wake words do início
        for wake in self.wake_words:
            if text_lower.startswith(wake):
                text_lower = text_lower[len(wake) :].strip()
                # Remove pontuação restante
                text_lower = re.sub(r"^[\s,\-!?.]+", "", text_lower)
                break

        # Verifica cada tipo de comando
        for cmd_name, cmd_config in self.command_patterns.items():
            for pattern in cmd_config["patterns"]:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    action = cmd_config["action"]

                    # Extrai parâmetro se houver grupos de captura
                    if match.groups():
                        if action == "open_app":
                            # Para abrir app, pega o último grupo (nome do app)
                            param = match.groups()[-1].strip()
                            return action, param

                    return action, None

        return None, None

    def is_wake_word(self, text: str) -> bool:
        """Verifica se o texto contém wake word."""
        if not text:
            return False
        text_lower = text.lower().strip()
        return any(wake in text_lower for wake in self.wake_words)

    def format_response(self, action: str, param: Optional[str] = None) -> str:
        """Formata resposta para ação executada com variações naturais."""
        responses = {
            "open_app": [
                f"Abrindo {param}..." if param else "O que você quer abrir?",
                f"Já vou abrir {param}..." if param else "O que abrir?",
                f"Só um segundo, abrindo {param}..." if param else "Fala qual app."
            ],
            "read_screen": [
                "Deixa eu ver o que tem aí...",
                "Vou dar uma olhada...",
                "Deixa eu ver a tela...",
                "Olhando agora..."
            ],
            "read_clipboard": [
                "Vou olhar o que você copiou...",
                "Deixa eu ver o clipboard...",
                "O que tem no clipboard? Olhando...",
                "Checando o que você copiou..."
            ],
            "tell_time": [self._get_time_string()],
            "exit": [
                "Até logo!",
                "Falou!",
                "Vou ficar por aqui. Até mais!",
                "Tchau! Quando precisar é só chamar."
            ],
            "clear_history": [
                "Histórico limpo. O que foi que a gente tava falando mesmo?",
                "Memória apagada. Quem é você de novo? Brincadeira!",
                "Limpei tudo. Vamos começar do zero?",
                "Histórico deletado. O que a gente conversou? Nem lembro."
            ],
            "status": [
                "Tô funcionando de boa!",
                "Tudo certo por aqui!",
                "Operacional! E você?",
                "Rodando lisinha. Tô bem!"
            ],
            "enable_voice": [
                "Modo voz ativado! Pode falar.",
                "Ouvindo você! Fala aí.",
                "Voz ativada. Pode mandar verbalmente!",
                "Te ouvindo agora. Fala!"
            ],
            "disable_voice": [
                "Ok, vou ficar quieta. Só manda no texto.",
                "Desativando voz. Só texto agora.",
                "Vou calar a boca. Manda no chat.",
                "Silêncio ativado. Só escrevendo agora."
            ],
            "vision_screen": [
                "Deixa eu dar uma olhada...",
                "Vou ver o que você tá vendo...",
                "Olhando sua tela...",
                "Deixa eu ver isso aí..."
            ],
            "vision_error": [
                "Minha visão tá embaçada, não consigo ver a tela agora!",
                "Não tô conseguindo ver a tela. Algum problema técnico?",
                "Visão falhando. Não consigo capturar a tela!",
                "Tô com a vista ruim hoje. Erro ao capturar tela!"
            ],
        }
        action_responses = responses.get(action, ["Comando executado."])
        return random.choice(action_responses)

    def _get_time_string(self) -> str:
        """Retorna hora atual formatada."""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        # Formatação informal
        if minute == 0:
            return f"São {hour} em ponto."
        elif minute < 10:
            return f"São {hour} e {minute:02d}."
        elif minute == 15:
            return f"São {hour} e quinze."
        elif minute == 30:
            return f"São {hour} e meia."
        elif minute == 45:
            return f"São {hour} e quarenta e cinco."
        else:
            return f"São {hour} e {minute:02d}."


if __name__ == "__main__":
    # Testes
    processor = VoiceCommandProcessor()

    test_inputs = [
        "assistente abre o chrome",
        "hey assistente, que horas são?",
        "ei assistente, lê a tela",
        "o que tem na tela?",
        "ler clipboard",
        "o que eu copiei?",
        "tchau assistente",
        "limpa o histórico",
        "como você tá?",
        "isso não é um comando",
    ]

    print("Testando comandos de voz:")
    for text in test_inputs:
        action, param = processor.process(text)
        if action:
            response = processor.format_response(action, param)
            print(f"'{text}' -> {action} (param: {param}) -> '{response}'")
        else:
            print(f"'{text}' -> (não é comando)")
