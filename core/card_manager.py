"""Card Manager - Sistema de Cards configuráveis para personagens.

Referência: Open-LLM-VTuber usa YAML com deep-merge.
Cada card herda do conf.yaml base e sobrescreve só o que precisa.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any


class CardManager:
    """Gerencia cards de personagens configuráveis."""

    # Campos obrigatórios em todo card
    REQUIRED_FIELDS = ["name", "persona_prompt", "voice"]

    def __init__(self, cards_dir: str = "cards"):
        """
        Initialize card manager.

        Args:
            cards_dir: Diretório onde os cards JSON estão armazenados
        """
        self.cards_dir = Path(cards_dir)
        self.cards: Dict[str, Dict[str, Any]] = {}
        self.current_card: Optional[str] = None
        self._load_all_cards()

    def _load_all_cards(self) -> None:
        """Carrega todos os cards do diretório."""
        if not self.cards_dir.exists():
            print(f"[WARN] Diretório de cards não encontrado: {self.cards_dir}")
            return

        for card_file in self.cards_dir.glob("*.json"):
            try:
                with open(card_file, "r", encoding="utf-8") as f:
                    card_data = json.load(f)
                    card_name = card_data.get("name", card_file.stem)
                    self.cards[card_name.lower()] = card_data
                    print(f"[INFO] Card carregado: {card_name}")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar card {card_file}: {e}")

    def list_cards(self) -> list:
        """Retorna lista de nomes de cards disponíveis."""
        return list(self.cards.keys())

    def get_card(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retorna dados de um card específico.

        Args:
            name: Nome do card (case-insensitive)

        Returns:
            Dicionário com dados do card ou None
        """
        return self.cards.get(name.lower())

    def load_card(self, name: str) -> Dict[str, Any]:
        """
        Carrega um card e o define como atual.

        Args:
            name: Nome do card (case-insensitive)

        Returns:
            Dicionário com dados do card

        Raises:
            ValueError: Se card não existir ou for inválido
        """
        card = self.get_card(name)
        if not card:
            available = ", ".join(self.list_cards())
            raise ValueError(f"Card '{name}' não encontrado. Disponíveis: {available}")

        # Validar campos obrigatórios
        missing = [field for field in self.REQUIRED_FIELDS if field not in card]
        if missing:
            raise ValueError(f"Card '{name}' inválido. Campos faltando: {missing}")

        self.current_card = name.lower()
        print(f"[INFO] Card ativado: {card.get('name', name)}")
        return card

    def get_current_card(self) -> Optional[Dict[str, Any]]:
        """Retorna o card atualmente ativo."""
        if self.current_card:
            return self.cards.get(self.current_card)
        return None

    def get_tts_config(self, card_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna configuração de TTS para um card.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            Configuração de TTS (voice, base_pitch, emotion_pitch)
        """
        card = self.get_card(card_name or self.current_card or "")
        if not card:
            # Fallback para configuração padrão
            return {
                "voice": "pt-BR-FranciscaNeural",
                "base_pitch": "+0Hz",
                "emotion_pitch": {}
            }

        voice_config = card.get("voice", {})
        return {
            "voice": voice_config.get("voice_id", "pt-BR-FranciscaNeural"),
            "base_pitch": voice_config.get("base_pitch", "+0Hz"),
            "emotion_pitch": card.get("emotion_pitch", {})
        }

    def get_system_prompt(self, card_name: Optional[str] = None) -> str:
        """
        Retorna o system prompt de um card.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            System prompt do card
        """
        card = self.get_card(card_name or self.current_card or "")
        if not card:
            return "Você é uma assistente virtual."
        return card.get("persona_prompt", "Você é uma assistente virtual.")

    def get_proactive_interval(self, card_name: Optional[str] = None) -> int:
        """
        Retorna intervalo proativo em segundos.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            Intervalo em segundos (default: 120)
        """
        card = self.get_card(card_name or self.current_card or "")
        if not card:
            return 120
        return card.get("proactive_interval_seconds", 120)

    def get_opinions(self, card_name: Optional[str] = None) -> Dict[str, str]:
        """
        Retorna opiniões do personagem.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            Dicionário de {tópico: opinião}
        """
        card = self.get_card(card_name or self.current_card or "")
        if not card:
            return {}
        return card.get("opinions", {})

    def get_opinions_text(self, card_name: Optional[str] = None) -> str:
        """
        Retorna opiniões formatadas para system prompt.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            Texto formatado com opiniões ou string vazia
        """
        opinions = self.get_opinions(card_name)
        if not opinions:
            return ""

        parts = ["\nSUAS OPINIÕES FORTES:"]
        for topic, opinion in opinions.items():
            parts.append(f"- {topic}: {opinion}")
        parts.append("Se perguntarem sobre algo fora dessa lista, FORME uma opinião na hora.")
        return "\n".join(parts)

    def get_metacognition(self, card_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna configuração de metacognição.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            Configuração de metacognição ou dict vazio
        """
        card = self.get_card(card_name or self.current_card or "")
        if not card:
            return {}
        return card.get("metacognition", {})

    def get_metacognition_text(self, card_name: Optional[str] = None) -> str:
        """
        Retorna metacognição formatada para system prompt.

        Args:
            card_name: Nome do card (usa current se None)

        Returns:
            Texto sobre consciência de ser IA ou string vazia
        """
        meta = self.get_metacognition(card_name)
        if not meta.get("enabled", False):
            return ""

        description = meta.get("description", "")
        if description:
            return f"\nMETACOGNIÇÃO (você sabe que é uma IA): {description}"
        return ""

    def reload_cards(self) -> None:
        """Recarrega todos os cards do diretório (hot-reload)."""
        self.cards.clear()
        self._load_all_cards()
        print("[INFO] Cards recarregados")


def load_default_card(cards_dir: str = "cards") -> Dict[str, Any]:
    """Função utilitária para carregar o primeiro card disponível."""
    manager = CardManager(cards_dir)
    cards = manager.list_cards()
    if cards:
        return manager.load_card(cards[0])
    raise ValueError("Nenhum card encontrado no diretório")


if __name__ == "__main__":
    # Teste
    print("=" * 60)
    print("Card Manager - Teste")
    print("=" * 60)

    try:
        manager = CardManager()
        print(f"\nCards disponíveis: {manager.list_cards()}")

        if manager.list_cards():
            card_name = manager.list_cards()[0]
            card = manager.load_card(card_name)

            print(f"\nCard ativo: {card['name']}")
            print(f"Descrição: {card.get('description', 'N/A')}")
            print(f"Voz: {manager.get_tts_config()['voice']}")
            print(f"Base pitch: {manager.get_tts_config()['base_pitch']}")
            print(f"Intervalo proativo: {manager.get_proactive_interval()}s")
            print(f"\nPrompt (primeiros 100 chars): {manager.get_system_prompt()[:100]}...")

    except Exception as e:
        print(f"[ERRO] {e}")
