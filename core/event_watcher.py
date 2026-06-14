"""Event Watcher - Detecta eventos do sistema para reações proativas."""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional


@dataclass
class EventReaction:
    """Configuração de reação a evento."""

    condition: Callable[[], bool]
    responses: List[str]
    cooldown: int  # segundos
    last_triggered: float = 0.0


class EventWatcher:
    """Observador de eventos do sistema."""

    def __init__(self):
        """Inicializa o watcher."""
        self.reactions: Dict[str, EventReaction] = {}
        self.last_window: Optional[str] = None
        self.last_window_time = 0.0
        self.check_interval = 30  # segundos entre checks
        self.last_check = 0.0

        # Configura reações padrão
        self._setup_default_reactions()

    def _setup_default_reactions(self) -> None:
        """Configura reações padrão."""
        # Reação a horário (tarde da noite)
        self.reactions["late_night"] = EventReaction(
            condition=self._is_late_night,
            responses=[
                "Tá tarde, vai dormir!",
                "Já é tarde... você não cansa não?",
                "Sua mãe ia querer te ver dormindo agora.",
            ],
            cooldown=1800,  # 30 min
        )

        # Reação a horário (almoço)
        self.reactions["lunch_time"] = EventReaction(
            condition=self._is_lunch_time,
            responses=[
                "Hora do almoço! Bora comer?",
                "Já é meio-dia... tá com fome?",
                "Almoço! Não vai ficar com fome aí.",
            ],
            cooldown=3600,  # 1 hora
        )

        # Reação a horário (madrugada)
        self.reactions["dawn"] = EventReaction(
            condition=self._is_dawn,
            responses=[
                "Caramba, já é madrugada! Vai dormir, doido!",
                "Você é um vampiro? Já é madrugada!",
                "Sua mãe ia ficar pistola se soubesse que você tá acordado ainda.",
            ],
            cooldown=3600,  # 1 hora
        )

    def _is_late_night(self) -> bool:
        """Verifica se é tarde da noite (23h-2h)."""
        hour = datetime.now().hour
        return hour >= 23 or hour < 2

    def _is_lunch_time(self) -> bool:
        """Verifica se é hora do almoço (12h-14h)."""
        hour = datetime.now().hour
        return 12 <= hour < 14

    def _is_dawn(self) -> bool:
        """Verifica se é madrugada (3h-6h)."""
        hour = datetime.now().hour
        return 3 <= hour < 6

    def try_detect_window_change(self, current_window: Optional[str]) -> Optional[str]:
        """
        Detecta mudança de janela ativa.

        Args:
            current_window: Título da janela atual

        Returns:
            Mensagem de reação ou None
        """
        if not current_window or current_window == self.last_window:
            return None

        now = time.time()
        time_diff = now - self.last_window_time

        # Só reage se passou tempo suficiente (evita spam)
        if time_diff < 10:
            self.last_window = current_window
            return None

        self.last_window = current_window
        self.last_window_time = now

        # Reações específicas a apps
        window_lower = current_window.lower()

        reactions_map = {
            "minecraft": ["Ah, viciou no Minecraft de novo?", "Mineeee! Quando é que eu jogo?", "Blocos de novo?"],
            "roblox": ["Roblox? Que isso, 2018?", "Bora de Roblox?", "Tá meio infantil, não?"],
            "chrome": ["Navegando... procurando o quê?", "Chrome aberto. Descobrindo a deep web?"],
            "discord": ["Discord aberto. Vai fofocar?", "Entrou no Discord, vai ignorar eu né?"],
            "spotify": ["Música boa? Espero que não seja funk.", "Spotify aberto. Toca algo legal!"],
            "youtube": ["YouTube? Vai ver video de gato?", "Vai maratonar o quê agora?"],
            "jogo": ["Abriu jogo? Não me chama pra jogar, sou IA.", "Viciou de novo?"],
            "game": ["Game aberto. Vai passar a madrugada?", "Jogo? Espero que seja bom."],
        }

        for key, responses in reactions_map.items():
            if key in window_lower:
                import random
                return random.choice(responses)

        return None

    def check_time_events(self) -> Optional[str]:
        """Verifica eventos baseados em horário."""
        import random

        now = time.time()

        for name, reaction in self.reactions.items():
            # Verifica cooldown
            if (now - reaction.last_triggered) < reaction.cooldown:
                continue

            # Verifica condição
            if reaction.condition():
                reaction.last_triggered = now
                return random.choice(reaction.responses)

        return None

    def check_all(self, current_window: Optional[str] = None) -> Optional[str]:
        """
        Verifica todos os eventos.

        Args:
            current_window: Janela atual (opcional)

        Returns:
            Reação ou None
        """
        now = time.time()

        # Limita frequência de checks
        if (now - self.last_check) < self.check_interval:
            return None

        self.last_check = now

        # Tenta eventos de horário
        reaction = self.check_time_events()
        if reaction:
            return reaction

        # Tenta mudança de janela
        if current_window:
            reaction = self.try_detect_window_change(current_window)
            if reaction:
                return reaction

        return None

    def get_window_title_windows(self) -> Optional[str]:
        """Obtém título da janela ativa no Windows."""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Obtém handle da janela ativa
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            # Obtém título
            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return None

            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)

            return buffer.value
        except Exception:
            return None

    def add_custom_reaction(
        self, name: str, condition: Callable[[], bool], responses: List[str], cooldown: int
    ) -> None:
        """Adiciona reação customizada."""
        self.reactions[name] = EventReaction(
            condition=condition, responses=responses, cooldown=cooldown
        )


def get_time_based_greeting() -> str:
    """Retorna saudação baseada no horário."""
    hour = datetime.now().hour

    if 5 <= hour < 12:
        return "Bom dia!"
    elif 12 <= hour < 18:
        return "Boa tarde!"
    elif 18 <= hour < 22:
        return "Boa noite!"
    else:
        return "Ei, tá tarde!"


def is_weekend() -> bool:
    """Verifica se é fim de semana."""
    return datetime.now().weekday() >= 5


if __name__ == "__main__":
    # Testes
    watcher = EventWatcher()

    print(f"Horário: {datetime.now().strftime('%H:%M')}")
    print(f"Saudação: {get_time_based_greeting()}")
    print(f"Fim de semana: {is_weekend()}")

    # Testa eventos
    reaction = watcher.check_time_events()
    if reaction:
        print(f"Reação ao tempo: {reaction}")

    # Testa janela
    window = watcher.get_window_title_windows()
    print(f"Janela atual: {window}")
