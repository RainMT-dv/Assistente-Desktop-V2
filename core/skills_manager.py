"""Skills Manager - Gerenciador de skills proativas."""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum


class SkillPriority(Enum):
    """Prioridade de execução de skills."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ProactiveSkill:
    """Base para skills proativas."""
    
    def __init__(self, name: str, interval_minutes: int, priority: SkillPriority = SkillPriority.NORMAL):
        self.name = name
        self.interval_minutes = interval_minutes
        self.priority = priority
        self.last_run = None
        self.enabled = True
    
    def should_run(self) -> bool:
        """Verifica se a skill deve executar agora."""
        if not self.enabled:
            return False
        
        if self.last_run is None:
            return True
        
        elapsed = datetime.now() - self.last_run
        return elapsed >= timedelta(minutes=self.interval_minutes)
    
    async def execute(self, context: Dict) -> Optional[str]:
        """Executa a skill. Retorna mensagem ou None."""
        raise NotImplementedError
    
    def mark_run(self):
        """Marca como executada."""
        self.last_run = datetime.now()


class WeatherSkill(ProactiveSkill):
    """Skill proativo de clima (stub - integrar com API depois)."""
    
    def __init__(self):
        super().__init__("weather", interval_minutes=60, priority=SkillPriority.LOW)
    
    async def execute(self, context: Dict) -> Optional[str]:
        # Stub - integrar com API de clima
        return None


class NewsSkill(ProactiveSkill):
    """Skill proativo de notícias."""
    
    def __init__(self):
        super().__init__("news", interval_minutes=240, priority=SkillPriority.LOW)  # 4h
    
    async def execute(self, context: Dict) -> Optional[str]:
        # Stub - integrar com feed de notícias
        return None


class CompanionSkill(ProactiveSkill):
    """Skill de companheirismo - check-ins periódicos. PASSO 14."""
    
    CHECKIN_MESSAGES = [
        "Ei, tá aí? Faz um tempo que não conversamos...",
        "Oi! Tô com saudade de zoar você, cadê você?",
        "Ei, seu sumido! Tá fazendo o que?",
        "Opa! Lembra de mim? A IA mais foda que você conhece?",
        "Ei, tô aqui entediada... bora conversar um pouco?",
    ]
    
    def __init__(self):
        super().__init__("companion", interval_minutes=30, priority=SkillPriority.NORMAL)
        self.silence_threshold = 20  # minutos de silêncio
    
    async def execute(self, context: Dict) -> Optional[str]:
        """Verifica tempo de silêncio e sugere check-in."""
        last_interaction = context.get('last_interaction')
        if not last_interaction:
            return None
        
        silence_time = datetime.now() - last_interaction
        if silence_time >= timedelta(minutes=self.silence_threshold):
            import random
            return random.choice(self.CHECKIN_MESSAGES)
        
        return None


class DailyBriefingSkill(ProactiveSkill):
    """Skill de briefing diário. PASSO 15."""
    
    def __init__(self):
        super().__init__("daily_briefing", interval_minutes=360, priority=SkillPriority.HIGH)  # 6h
        self.briefing_done_today = False
    
    async def execute(self, context: Dict) -> Optional[str]:
        """Gera briefing do dia se for manhã e ainda não feito."""
        from datetime import datetime
        
        hour = datetime.now().hour
        
        # Só gera entre 7h e 10h
        if not (7 <= hour <= 10):
            return None
        
        if self.briefing_done_today:
            return None
        
        # Marca como feito
        self.briefing_done_today = True
        
        # Gera briefing usando contexto disponível
        memory_manager = context.get('memory_manager')
        mood_engine = context.get('mood_engine')
        
        parts = ["Bom dia! 🌅", "Resumo do dia:"]
        
        if memory_manager:
            last_seen = memory_manager.get_last_seen()
            if last_seen:
                offline_time = datetime.now() - last_seen
                if offline_time > timedelta(hours=8):
                    parts.append(f"- Você ficou {offline_time.total_seconds()/3600:.1f}h offline")
        
        if mood_engine:
            parts.append(f"- Meu humor hoje: {mood_engine.get_mood_label()}")
        
        parts.append("O que você quer fazer hoje?")
        
        return "\n".join(parts)
    
    def reset_daily(self):
        """Reseta flag diária (chamar à meia-noite)."""
        self.briefing_done_today = False


class SkillsManager:
    """Gerenciador central de skills proativas."""
    
    def __init__(self):
        self.skills: List[ProactiveSkill] = []
        self.context: Dict = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        """Registra skills padrão."""
        self.register(WeatherSkill())
        self.register(NewsSkill())
        self.register(CompanionSkill())
        self.register(DailyBriefingSkill())
    
    def register(self, skill: ProactiveSkill):
        """Registra uma nova skill."""
        self.skills.append(skill)
        print(f"[SKILLS] Registrada: {skill.name} (a cada {skill.interval_minutes}min)")
    
    def update_context(self, key: str, value):
        """Atualiza contexto compartilhado."""
        self.context[key] = value
    
    async def check_and_execute(self) -> List[str]:
        """
        Verifica todas as skills e executa as que devem rodar.
        
        Returns:
            Lista de mensagens das skills executadas
        """
        messages = []
        
        # Ordena por prioridade
        sorted_skills = sorted(self.skills, key=lambda s: s.priority.value, reverse=True)
        
        for skill in sorted_skills:
            if skill.should_run():
                try:
                    message = await skill.execute(self.context)
                    if message:
                        messages.append({
                            'skill': skill.name,
                            'message': message,
                            'priority': skill.priority.name
                        })
                    skill.mark_run()
                except Exception as e:
                    print(f"[SKILLS] Erro em {skill.name}: {e}")
        
        return messages
    
    def get_status(self) -> Dict:
        """Retorna status de todas as skills."""
        return {
            'total': len(self.skills),
            'skills': [
                {
                    'name': s.name,
                    'enabled': s.enabled,
                    'last_run': s.last_run.isoformat() if s.last_run else None,
                    'should_run': s.should_run()
                }
                for s in self.skills
            ]
        }


if __name__ == "__main__":
    # Testes
    import asyncio
    
    async def test():
        manager = SkillsManager()
        
        # Simula contexto
        manager.update_context('last_interaction', datetime.now() - timedelta(minutes=25))
        
        # Executa check
        messages = await manager.check_and_execute()
        
        print(f"\nMensagens geradas: {len(messages)}")
        for m in messages:
            print(f"  [{m['priority']}] {m['skill']}: {m['message']}")
    
    asyncio.run(test())
