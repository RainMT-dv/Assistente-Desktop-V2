"""Memory Manager - Sistema de memória persistente do Assistente."""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .logger import log


class MemoryManager:
    """Sistema de memória persistente do Assistente."""

    def __init__(self, filepath: str = "data/memories.json"):
        """Inicializa o gerenciador de memória."""
        self.filepath = filepath
        self.data = self._load_data()
        self.last_seen = self._load_last_seen()

    def _load_data(self) -> Dict:
        """Carrega memórias do arquivo JSON."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                log('ERROR', f'Falha ao carregar memórias: {e}')
        
        # Estrutura padrão
        return {
            "user_profile": {
                "name": None,
                "location": None,
                "interests": [],
                "preferences": {},
                "birthday": None,
                "age": None
            },
            "facts": [],
            "conversation_summaries": [],
            "last_seen": None,
            "session_log": []
        }

    def _load_last_seen(self) -> Optional[datetime]:
        """Carrega timestamp do último acesso."""
        last_seen_str = self.data.get("last_seen")
        if last_seen_str:
            try:
                return datetime.fromisoformat(last_seen_str)
            except ValueError as e:
                log('ERROR', f'Falha ao parsear data: {e}')
        return None

    def save(self) -> None:
        """Salva memórias no arquivo JSON."""
        # Garante que o diretório existe
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        self.data["last_seen"] = datetime.now().isoformat()
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def save_user_fact(self, fact: str) -> None:
        """Salva um fato sobre o usuário."""
        fact = fact.strip()
        if not fact or fact in self.data["facts"]:
            return
        
        self.data["facts"].append(fact)
        self._update_profile_from_fact(fact)
        print(f"[MEMÓRIA] Fato salvo: {fact}")

    def _update_profile_from_fact(self, fact: str) -> None:
        """Atualiza perfil automaticamente baseado no fato."""
        fact_lower = fact.lower()
        
        # Detectar nome
        name_patterns = [
            r'(?:me chamo|meu nome é|sou o|sou a|call me|my name is)\s+(\w+)',
            r'(?:pode me chamar de)\s+(\w+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, fact_lower)
            if match:
                self.data["user_profile"]["name"] = match.group(1).capitalize()
                break
        
        # Detectar idade
        age_patterns = [
            r'(?:tenho|sou)\s+(\d+)\s*(?:anos?|years?)',
            r'(?:minha idade é|idade:)\s*(\d+)',
        ]
        for pattern in age_patterns:
            match = re.search(pattern, fact_lower)
            if match:
                self.data["user_profile"]["age"] = int(match.group(1))
                break
        
        # Detectar localização
        location_patterns = [
            r'(?:sou de|moro em|vivo em|sou do|sou da)\s+([\w\s-]+?)(?:\s+(?:e|mas|\.))?',
            r'(?:moro em|localização:)\s+([\w\s-]+)',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, fact_lower)
            if match:
                self.data["user_profile"]["location"] = match.group(1).strip()
                break
        
        # Detectar interesses
        interest_keywords = [
            "gosto de", "adoro", "curto", "amo", "sou fã", "me interesso",
            "hobby", "passatempo", "interesse", "gosto muito"
        ]
        for keyword in interest_keywords:
            if keyword in fact_lower:
                # Extrair o que vem depois
                parts = fact_lower.split(keyword)
                if len(parts) > 1:
                    interest = parts[1].strip().rstrip('.').split(',')[0].split(' e ')[0]
                    interest = interest.strip()
                    if interest and len(interest) > 2 and interest not in self.data["user_profile"]["interests"]:
                        self.data["user_profile"]["interests"].append(interest.capitalize())
                break

    def get_user_profile(self) -> Dict:
        """Retorna perfil do usuário acumulado."""
        return self.data["user_profile"]

    def get_profile_summary(self) -> str:
        """Retorna resumo formatado do perfil para system prompt."""
        profile = self.data["user_profile"]
        parts = []
        
        if profile.get("name"):
            parts.append(f"Nome: {profile['name']}")
        if profile.get("age"):
            parts.append(f"Idade: {profile['age']} anos")
        if profile.get("location"):
            parts.append(f"Local: {profile['location']}")
        if profile.get("interests"):
            parts.append(f"Interesses: {', '.join(profile['interests'][:5])}")
        if profile.get("birthday"):
            parts.append(f"Aniversário: {profile['birthday']}")
        
        if parts:
            return "PERFIL DO USUÁRIO: " + " | ".join(parts)
        return ""

    def save_conversation_summary(self, date: str, summary: str) -> None:
        """Salva resumo de conversa do dia."""
        entry = {
            "date": date,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        # Remove entrada do mesmo dia se existir
        self.data["conversation_summaries"] = [
            s for s in self.data["conversation_summaries"] 
            if s.get("date") != date
        ]
        
        self.data["conversation_summaries"].append(entry)
        
        # Mantém apenas os últimos 30 dias
        self.data["conversation_summaries"] = self.data["conversation_summaries"][-30:]
        print(f"[MEMÓRIA] Resumo salvo: {date}")

    def get_recent_summaries(self, days: int = 3) -> List[Dict]:
        """Retorna resumos dos últimos N dias."""
        return self.data["conversation_summaries"][-days:]

    def get_context_for_prompt(self, days: int = 3) -> str:
        """
        Retorna contexto completo de memória formatado para o system prompt.
        Combina perfil do usuário + resumos recentes.
        
        Returns:
            String formatada com contexto de memória
        """
        parts = []
        
        # Perfil do usuário
        profile_summary = self.get_profile_summary()
        if profile_summary:
            parts.append(profile_summary)
        
        # Resumos recentes
        summaries_text = self.get_summaries_text(days=days)
        if summaries_text:
            parts.append(summaries_text)
        
        if parts:
            return "\n\nMEMÓRIA DE LONGO PRAZO:\n" + "\n".join(parts)
        return ""

    def get_summaries_text(self, days: int = 3) -> str:
        """Retorna resumos formatados para system prompt."""
        summaries = self.get_recent_summaries(days)
        if not summaries:
            return ""
        
        parts = ["ÚLTIMAS CONVERSAS:"]
        for s in summaries:
            parts.append(f"  {s['date']}: {s['summary']}")
        
        return "\n".join(parts)

    def search_memories(self, query: str) -> List[str]:
        """Busca memórias por keyword."""
        query_lower = query.lower()
        results = []
        
        # Busca em fatos
        for fact in self.data["facts"]:
            if query_lower in fact.lower():
                results.append(fact)
        
        # Busca em interesses
        for interest in self.data["user_profile"].get("interests", []):
            if query_lower in interest.lower():
                results.append(f"Usuário gosta de: {interest}")
        
        return results

    def extract_facts_from_message(self, user_text: str, ai_response: str) -> None:
        """Extrai automaticamente fatos importantes da conversa."""
        user_lower = user_text.lower()
        
        # Padrões de fatos
        fact_indicators = [
            # Nome
            (r'(?:me chamo|meu nome é|sou o|sou a|call me)\s+(\w+)', "Usuário se chama {}"),
            # Idade
            (r'(?:tenho|sou)\s+(\d+)\s*(?:anos?|years?)', "Usuário tem {} anos"),
            # Local
            (r'(?:sou de|moro em|vivo em)\s+([\w\s-]+?)(?:\s+(?:e|mas|\.))?', "Usuário é de {}"),
            # Gostos
            (r'(?:gosto de|adoro|curto|amo)\s+([\w\s]+?)(?:\s+(?:porque|mas|e|\.))?', "Usuário gosta de {}"),
        ]
        
        for pattern, template in fact_indicators:
            match = re.search(pattern, user_lower)
            if match:
                fact = template.format(match.group(1).strip())
                self.save_user_fact(fact)

    def get_last_seen(self) -> Optional[datetime]:
        """Retorna timestamp do último acesso."""
        return self.last_seen

    def update_last_seen(self) -> None:
        """Atualiza timestamp do último acesso."""
        self.last_seen = datetime.now()
        self.data["last_seen"] = self.last_seen.isoformat()

    def log_session_event(self, event: str) -> None:
        """Loga evento da sessão atual."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event
        }
        self.data["session_log"].append(entry)
        
        # Mantém apenas últimos 100 eventos
        self.data["session_log"] = self.data["session_log"][-100:]

    def get_session_topics(self) -> List[str]:
        """Extrai tópicos da sessão atual para resumo."""
        # Simples: retorna os fatos salvos na sessão
        return self.data["facts"][-10:] if self.data["facts"] else []

    def generate_daily_summary(self) -> str:
        """Gera resumo do dia baseado nos logs da sessão."""
        today = datetime.now().strftime("%Y-%m-%d")
        topics = self.get_session_topics()
        
        if not topics:
            return f"Conversa casual em {today}"
        
        return f"Conversamos sobre: {', '.join(topics[:5])}"


if __name__ == "__main__":
    # Testes
    mm = MemoryManager("test_memories.json")
    
    mm.save_user_fact("Usuário se chama Arthur")
    mm.save_user_fact("Usuário tem 14 anos")
    mm.save_user_fact("Usuário é de Cariacica-ES")
    mm.save_user_fact("Usuário gosta de Minecraft e IA")
    
    print("Perfil:", mm.get_user_profile())
    print("Resumo:", mm.get_profile_summary())
    
    mm.save_conversation_summary("2026-04-25", "Conversamos sobre Minecraft e corrigimos bugs")
    print("Recentes:", mm.get_summaries_text())
    
    mm.save()
    print(f"Salvo em: {mm.filepath}")
