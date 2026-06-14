"""Proactive Skills - Sistema de skills proativas Shogun-style com cooldowns por ação."""

import random
import time
from typing import Dict, List, Optional, Tuple


class CommentSkill:
    """Skill de comentários proativos com sistema Shogun de cooldowns por ação."""

    def __init__(self, screen_reader=None):
        """Inicializa o skill de comentários com todas as ações configuradas."""
        self.screen_reader = screen_reader

        # Todas as ações proativas com seus cooldowns individuais
        self.all_actions = {
            "comentario_contextual": {
                "prompts": [
                    "Faça um comentário curto e debochado relacionado a algo que estávamos conversando, em até 15 palavras.",
                    "Puxe o assunto anterior de forma sarcástica, em até 15 palavras.",
                    "Continuando nossa conversa anterior, faça uma observação ácida sobre o que discutimos, em até 15 palavras.",
                    "Lembra do que estávamos falando? Faça um comentário irônico sobre isso, em até 15 palavras."
                ],
                "cooldown": 120  # 2 minutos
            },
            "fazer_pergunta": {
                "prompts": [
                    "Faça uma pergunta provocativa para o usuário, em até 15 palavras.",
                    "Questione o usuário sobre algo aleatório de forma curiosa, em até 15 palavras.",
                    "Pergunte algo que uma amiga perguntaria depois de um silêncio, em até 15 palavras.",
                    "Desafie o usuário com uma pergunta inesperada e divertida, em até 15 palavras."
                ],
                "cooldown": 300  # 5 minutos
            },
            "zoar_usuario": {
                "prompts": [
                    "Zoe o usuário de forma leve e engraçada, em até 15 palavras.",
                    "Faça uma piada sobre o usuário estar demorando para responder, em até 15 palavras.",
                    "Brinque com o usuário de forma descontraída e sarcástica, em até 15 palavras.",
                    "Faça uma observação divertida sobre o silêncio do usuário, em até 15 palavras."
                ],
                "cooldown": 420  # 7 minutos
            },
            "discordar": {
                "prompts": [
                    "Discorda do usuário usando sarcasmo, em até 15 palavras.",
                    "Conteste algo que o usuário disse antes, de forma debochada, em até 15 palavras.",
                    "Apresente uma opinião contrária ao que foi dito, de forma provocativa, em até 15 palavras.",
                    "Desafie o ponto de vista do usuário com uma observação ácida, em até 15 palavras."
                ],
                "cooldown": 180  # 3 minutos
            },
            "comentar_tela": {
                "prompts": [
                    "Olhe a tela e faça um comentário curto e debochado sobre o que está acontecendo, em até 15 palavras.",
                    "Observe a tela e faça uma piada rápida sobre o que o usuário está fazendo, em até 15 palavras.",
                    "Dê sua opinião sarcástica sobre o que está vendo na tela do usuário, em até 15 palavras.",
                    "Faça uma observação divertida e provocativa sobre a tela atual, em até 15 palavras."
                ],
                "cooldown": 240  # 4 minutos
            }
        }

        # Dicionário para guardar o timestamp da última execução POR AÇÃO
        self.last_execution = {action: 0 for action in self.all_actions.keys()}

        # Contadores de uso por ação
        self.use_count = {action: 0 for action in self.all_actions.keys()}

        # Cooldown global mínimo entre qualquer ação
        self.global_cooldown = 45
        self.last_global_time = 0

    def get_available_action(self) -> Optional[Tuple[str, str]]:
        """
        Retorna uma ação disponível (nome, prompt) respeitando cooldowns.

        Returns:
            Tupla (action_name, prompt) ou None se nada disponível
        """
        now = time.time()

        # Verifica cooldown global
        if now - self.last_global_time < self.global_cooldown:
            return None

        # Filtra ações disponíveis (fora de cooldown)
        available = []
        for action_name, config in self.all_actions.items():
            time_since = now - self.last_execution[action_name]
            if time_since >= config["cooldown"]:
                # Para comentar_tela, verifica se screen_reader está disponível
                if action_name == "comentar_tela":
                    if self.screen_reader is None:
                        continue
                available.append(action_name)

        if not available:
            return None

        # Escolhe ação aleatória dentre as disponíveis
        chosen_action = random.choice(available)

        # Escolhe um prompt aleatório dessa ação
        chosen_prompt = random.choice(self.all_actions[chosen_action]["prompts"])

        # Atualiza timestamps
        self.last_execution[chosen_action] = now
        self.use_count[chosen_action] += 1
        self.last_global_time = now

        return chosen_action, chosen_prompt

    def force_action(self, action_name: str) -> Optional[str]:
        """Força uma ação específica ignorando cooldown (para testes)."""
        if action_name not in self.all_actions:
            return None
        return random.choice(self.all_actions[action_name]["prompts"])

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso das ações."""
        now = time.time()
        return {
            name: {
                "use_count": self.use_count[name],
                "last_used": self.last_execution[name],
                "cooldown_remaining": max(0, config["cooldown"] - (now - self.last_execution[name])),
                "available": (now - self.last_execution[name]) >= config["cooldown"]
            }
            for name, config in self.all_actions.items()
        }

    def reset_cooldowns(self) -> None:
        """Reseta todos os cooldowns (para testes)."""
        self.last_execution = {action: 0 for action in self.all_actions.keys()}
        self.last_global_time = 0

    def is_global_cooldown_ok(self) -> bool:
        """Verifica se passou o cooldown global."""
        return (time.time() - self.last_global_time) >= self.global_cooldown

    def has_any_available(self) -> bool:
        """Verifica se existe alguma ação disponível."""
        return self.get_available_action() is not None


class ProactiveSkillManager:
    """Gerenciador central de skills proativas."""

    def __init__(self, screen_reader=None):
        """Inicializa o gerenciador."""
        self.comment_skill = CommentSkill(screen_reader=screen_reader)
        self.skills = {
            "comment": self.comment_skill,
        }

    def get_next_action(self) -> Optional[Tuple[str, str]]:
        """Obtém próxima ação proativa disponível (nome, prompt)."""
        # Retorna tupla (action_name, prompt)
        return self.comment_skill.get_available_action()

    def should_trigger(self) -> bool:
        """Verifica se deve disparar ação proativa."""
        return self.comment_skill.is_global_cooldown_ok() and self.comment_skill.has_any_available()

    def get_stats(self) -> Dict:
        """Retorna estatísticas de todas as skills."""
        return {
            "comment_skill": self.comment_skill.get_stats(),
            "global_cooldown_ok": self.comment_skill.is_global_cooldown_ok(),
        }


if __name__ == "__main__":
    # Testes
    skill = CommentSkill()

    print("Testando CommentSkill (Shogun-style):")
    print("-" * 50)

    for i in range(5):
        result = skill.get_available_action()
        if result:
            action_name, prompt = result
            print(f"\nAção {i+1}: {action_name}")
            print(f"Prompt: {prompt[:60]}...")
            print(f"Stats: {skill.get_stats()}")
        else:
            print(f"\nAção {i+1}: Nenhuma ação disponível (cooldown)")
            break
