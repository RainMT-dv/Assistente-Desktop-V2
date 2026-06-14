"""
skill_system.py - Sistema de Skills Autônomas

Skills são capacidades da IA para realizar ações proativas baseadas em contexto.
Diferente do ProactiveEngine (temporizado), skills são disparadas por contexto.
"""

import json
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .logger import log


class Skill(ABC):
    """
    Classe base para todas as skills autônomas.
    
    Cada skill implementa:
    - name: identificador único
    - cooldown: tempo mínimo entre execuções
    - should_trigger(): decide se deve executar baseado em contexto
    - execute(): ação a ser realizada
    """
    
    def __init__(self, name: str, cooldown_seconds: int = 300):
        self.name = name
        self.cooldown_seconds = cooldown_seconds
        self.last_execution: Optional[datetime] = None
        self.trigger_count: int = 0
        self.enabled: bool = True
    
    def can_execute(self) -> bool:
        """Verifica se cooldown passou e skill está habilitada."""
        if not self.enabled:
            return False
        if self.last_execution is None:
            return True
        elapsed = (datetime.now() - self.last_execution).total_seconds()
        return elapsed >= self.cooldown_seconds
    
    @abstractmethod
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        Decide se a skill deve ser disparada baseada no contexto.
        
        Args:
            context: Dict com informações do ambiente (última_msg, inatividade, etc)
            
        Returns:
            True se deve executar, False caso contrário
        """
        pass
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Executa a skill e retorna mensagem opcional para falar.
        
        Args:
            context: Dict com informações do ambiente
            
        Returns:
            Mensagem para TTS ou None se não há nada a dizer
        """
        pass
    
    def record_execution(self):
        """Registra que a skill foi executada."""
        self.last_execution = datetime.now()
        self.trigger_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da skill."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "trigger_count": self.trigger_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "cooldown_seconds": self.cooldown_seconds,
            "can_execute": self.can_execute()
        }


class CommentSkill(Skill):
    """
    Skill para comentar sobre o contexto atual.
    Dispara quando há contexto interessante para comentar.
    """
    
    COMMENTS = {
        "inatividade": [
            "Tá aí ainda ou foi farmar recursos no Minecraft?",
            "Tô esperando... e esperando... e esperando...",
            "Ei, sumiu? Foi stombar em algum lugar?",
            "Aloooo? Tem alguém aí?",
            "Tá ocupado ou só me ignorando mesmo?",
        ],
        "longa_sessao": [
            "Já tá aí há um tempo, hein. Vai fazer uma pausa não?",
            "Já viu as horas? Tá farmando XP desde cedo.",
            "Ei, não esquece de piscar, não. Tá na frente do PC faz tempo.",
        ],
        "silencio": [
            "Que silêncio... Tá estranho isso.",
            "Tá muito quieto. Tá tudo bem aí?",
            "Hmmm... tá suspeito esse silêncio.",
        ],
        "retorno": [
            "Voltou! Achou que eu não ia notar?",
            "Ei, sumido! O que tava fazendo?",
            "Ah, lembrou que eu existo! Que honra.",
        ]
    }
    
    def __init__(self):
        super().__init__(name="comment", cooldown_seconds=180)
        self.last_context_type: Optional[str] = None
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Dispara se há contexto relevante e passou cooldown."""
        if not self.can_execute():
            return False
        
        inatividade = context.get("inactivity_seconds", 0)
        ultima_msg = context.get("last_message", "")
        
        # Se inatividade > 5 min, comenta
        if inatividade > 300:
            self.last_context_type = "inatividade"
            return True
        
        # Se sessão longa (>30 min) e última mensagem foi há tempo
        session_time = context.get("session_seconds", 0)
        if session_time > 1800 and inatividade > 60:
            self.last_context_type = "longa_sessao"
            return True
        
        return False
    
    def execute(self, context: Dict[str, Any]) -> Optional[str]:
        """Retorna um comentário apropriado."""
        self.record_execution()
        
        context_type = self.last_context_type or "silencio"
        comments = self.COMMENTS.get(context_type, self.COMMENTS["silencio"])
        
        return f"[Neutra] {random.choice(comments)}"


class ContextReactionSkill(Skill):
    """
    Skill para reagir a eventos específicos do contexto.
    """
    
    REACTIONS = {
        "screenshot_change": [
            "Viu algo interessante aí na tela?",
            "Mudou de tela... o que tá vendo agora?",
            "Ei, trocou de janela! Tá fazendo o que?",
        ],
        "clipboard_text": [
            "Copiou algo aí? Quer que eu veja?",
            "Hmm, copiou texto... é importante?",
            "Tá copiando coisa aí. Tá trabalhando?",
        ]
    }
    
    def __init__(self):
        super().__init__(name="context_reaction", cooldown_seconds=120)
        self.triggered_events: set = set()
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Dispara se detectou evento novo no contexto."""
        if not self.can_execute():
            return False
        
        # Verifica eventos
        events = context.get("events", [])
        for event in events:
            if event in self.REACTIONS and event not in self.triggered_events:
                self.triggered_events.add(event)
                self.last_context_type = event
                return True
        
        return False
    
    def execute(self, context: Dict[str, Any]) -> Optional[str]:
        """Retorna reação ao evento."""
        self.record_execution()
        
        event = getattr(self, 'last_context_type', 'screenshot_change')
        reactions = self.REACTIONS.get(event, ["Hmm, interessante..."])
        
        return f"[Neutra] {random.choice(reactions)}"


class SkillSystem:
    """
    Gerenciador central de skills autônomas.
    Coordena múltiplas skills e decide qual executar.
    """
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.enabled: bool = True
        self._register_default_skills()
    
    def _register_default_skills(self):
        """Registra as skills padrão do sistema."""
        self.register(CommentSkill())
        self.register(ContextReactionSkill())
    
    def register(self, skill: Skill):
        """Registra uma nova skill no sistema."""
        self.skills[skill.name] = skill
        log('SKILL', f'Registrada: {skill.name} (cooldown: {skill.cooldown_seconds}s)')

    def add_skill(self, skill: Skill):
        """Alias para register() - compatibilidade com código antigo."""
        return self.register(skill)
    
    def unregister(self, name: str) -> bool:
        """Remove uma skill do sistema."""
        if name in self.skills:
            del self.skills[name]
            log('SKILL', f'Removida: {name}')
            return True
        return False
    
    def enable(self, name: Optional[str] = None):
        """Habilita skill específica ou todas."""
        if name:
            if name in self.skills:
                self.skills[name].enabled = True
                log('SKILL', f'Habilitada: {name}')
        else:
            self.enabled = True
            for skill in self.skills.values():
                skill.enabled = True
            log('SKILL', 'Todas as skills habilitadas')

    def enable_all(self):
        """Alias para enable() sem argumentos - habilita todas as skills."""
        return self.enable()
    
    def disable(self, name: Optional[str] = None):
        """Desabilita skill específica ou todas."""
        if name:
            if name in self.skills:
                self.skills[name].enabled = False
                log('SKILL', f'Desabilitada: {name}')
        else:
            self.enabled = False
            for skill in self.skills.values():
                skill.enabled = False
            log('SKILL', 'Todas as skills desabilitadas')
    
    def evaluate(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Avalia todas as skills e executa a primeira que disparar.
        
        Args:
            context: Contexto atual do ambiente
            
        Returns:
            Mensagem da skill executada ou None
        """
        if not self.enabled:
            return None
        
        for name, skill in self.skills.items():
            if not skill.enabled:
                continue
            
            try:
                if skill.should_trigger(context):
                    log('SKILL', f'Trigger: {name}')
                    message = skill.execute(context)
                    if message:
                        return message
            except Exception as e:
                log('SKILL', f'Erro em {name}: {e}')
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de todas as skills."""
        return {
            "system_enabled": self.enabled,
            "skills_count": len(self.skills),
            "skills": {name: skill.get_stats() for name, skill in self.skills.items()}
        }
    
    def to_json(self) -> str:
        """Serializa estatísticas para JSON."""
        return json.dumps(self.get_stats(), indent=2, default=str)


# Singleton para uso global
_skill_system: Optional[SkillSystem] = None


def get_skill_system() -> SkillSystem:
    """Retorna instância global do SkillSystem."""
    global _skill_system
    if _skill_system is None:
        _skill_system = SkillSystem()
    return _skill_system


# ============== TESTES ==============

if __name__ == "__main__":
    print("=" * 50)
    print("TESTE: Skill System")
    print("=" * 50)
    
    # Cria sistema
    system = SkillSystem()
    
    # Testa com contexto vazio
    print("\n1. Teste com contexto vazio:")
    msg = system.evaluate({"inactivity_seconds": 0})
    print(f"   Resultado: {msg}")
    
    # Testa com inatividade alta
    print("\n2. Teste com inatividade de 6 minutos:")
    msg = system.evaluate({
        "inactivity_seconds": 360,
        "last_message": ""
    })
    print(f"   Resultado: {msg}")
    
    # Testa stats
    print("\n3. Estatísticas:")
    print(system.to_json())
    
    # Testa disable/enable
    print("\n4. Teste disable/enable:")
    system.disable("comment")
    msg = system.evaluate({"inactivity_seconds": 400})
    print(f"   Com skill 'comment' desabilitada: {msg}")
    
    system.enable("comment")
    print("   Skill 'comment' reabilitada")
    
    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print("=" * 50)
