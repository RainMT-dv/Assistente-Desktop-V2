"""Context Backlog - Sistema de fila de contexto pendente."""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class BacklogPriority(Enum):
    """Prioridades do backlog."""
    LOW = 1      # Info geral
    MEDIUM = 2   # Contexto relevante
    HIGH = 3     # Urgente / importante
    CRITICAL = 4 # Must-mention


class ContextBacklog:
    """Sistema de fila de contexto pendente para a IA processar."""
    
    def __init__(self, filepath: str = "data/context_backlog.json"):
        """Inicializa o backlog de contexto."""
        self.filepath = filepath
        self.items: List[Dict] = []
        self.processed_today: List[str] = []  # IDs processados hoje
        self._load()
    
    def _load(self) -> None:
        """Carrega backlog do arquivo."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = data.get('items', [])
                    # Limpa processed_today se for outro dia
                    last_date = data.get('last_date', '')
                    today = datetime.now().strftime('%Y-%m-%d')
                    if last_date != today:
                        self.processed_today = []
                    else:
                        self.processed_today = data.get('processed_today', [])
            except (json.JSONDecodeError, IOError):
                pass
    
    def save(self) -> None:
        """Salva backlog no arquivo."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        
        data = {
            'items': self.items,
            'processed_today': self.processed_today,
            'last_date': datetime.now().strftime('%Y-%m-%d'),
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add(self, content: str, priority: BacklogPriority = BacklogPriority.MEDIUM,
            source: str = "system", auto_insert: bool = False) -> str:
        """
        Adiciona item ao backlog.
        
        Args:
            content: Texto do contexto a processar
            priority: Prioridade do item
            source: Origem (system, user, memory, etc)
            auto_insert: Se True, força inserção na próxima mensagem
        
        Returns:
            ID do item criado
        """
        item_id = f"{source}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.items)}"
        
        item = {
            'id': item_id,
            'content': content,
            'priority': priority.value,
            'priority_label': priority.name,
            'source': source,
            'created_at': datetime.now().isoformat(),
            'auto_insert': auto_insert,
            'processed': False,
            'processing_count': 0  # Quantas vezes tentou processar
        }
        
        self.items.append(item)
        
        # Mantém apenas últimos 50 itens
        if len(self.items) > 50:
            self.items = sorted(self.items, 
                              key=lambda x: (x['priority'], x['created_at']), 
                              reverse=True)[:50]
        
        print(f"[BACKLOG] Adicionado (P{priority.value}-{priority.name}): {content[:50]}...")
        return item_id
    
    def get_pending(self, max_items: int = 3, min_priority: BacklogPriority = BacklogPriority.LOW) -> List[Dict]:
        """
        Retorna itens pendentes para processamento.
        
        Args:
            max_items: Máximo de itens a retornar
            min_priority: Prioridade mínima
        
        Returns:
            Lista de itens pendentes ordenados por prioridade
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Filtra itens não processados e não processados hoje
        pending = [
            item for item in self.items 
            if not item.get('processed') 
            and item['id'] not in self.processed_today
            and item['priority'] >= min_priority.value
        ]
        
        # Auto-insert tem prioridade máxima
        auto_items = [item for item in pending if item.get('auto_insert')]
        regular_items = [item for item in pending if not item.get('auto_insert')]
        
        # Ordena por prioridade (maior primeiro)
        auto_items.sort(key=lambda x: x['priority'], reverse=True)
        regular_items.sort(key=lambda x: x['priority'], reverse=True)
        
        # Combina: auto-insert primeiro, depois regulares
        result = auto_items[:max_items]
        remaining = max_items - len(result)
        if remaining > 0:
            result.extend(regular_items[:remaining])
        
        return result
    
    def mark_processed(self, item_id: str) -> bool:
        """Marca item como processado."""
        for item in self.items:
            if item['id'] == item_id:
                item['processed'] = True
                item['processed_at'] = datetime.now().isoformat()
                if item_id not in self.processed_today:
                    self.processed_today.append(item_id)
                return True
        return False
    
    def mark_all_processed(self, item_ids: List[str]) -> None:
        """Marca múltiplos itens como processados."""
        for item_id in item_ids:
            self.mark_processed(item_id)
    
    def get_context_injection(self, max_items: int = 3) -> str:
        """
        Retorna texto para injetar no contexto da conversa.
        
        Returns:
            Texto formatado ou string vazia se não houver itens
        """
        pending = self.get_pending(max_items)
        
        if not pending:
            return ""
        
        lines = ["[CONTEXTO PENDENTE - mencione naturalmente na resposta:]"]
        for item in pending:
            lines.append(f"- {item['content']}")
            item['processing_count'] = item.get('processing_count', 0) + 1
            
            # Auto-mark como processado se foi usado
            if item.get('auto_insert'):
                self.mark_processed(item['id'])
        
        return "\n".join(lines)
    
    def should_inject(self) -> bool:
        """Verifica se há itens que devem ser injetados."""
        pending = self.get_pending(max_items=1)
        if not pending:
            return False
        
        # Só injeta se tiver auto_insert ou prioridade HIGH+
        item = pending[0]
        return item.get('auto_insert') or item['priority'] >= BacklogPriority.HIGH.value
    
    def clear_old_items(self, days: int = 7) -> int:
        """Limpa itens antigos já processados."""
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        
        original_count = len(self.items)
        self.items = [
            item for item in self.items 
            if not item.get('processed') or 
            datetime.fromisoformat(item['created_at']).timestamp() > cutoff
        ]
        
        removed = original_count - len(self.items)
        if removed > 0:
            print(f"[BACKLOG] Limpados {removed} itens antigos")
        return removed
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do backlog."""
        total = len(self.items)
        pending = len([i for i in self.items if not i.get('processed')])
        by_priority = {}
        for p in BacklogPriority:
            by_priority[p.name] = len([i for i in self.items if i['priority'] == p.value])
        
        return {
            'total_items': total,
            'pending': pending,
            'processed_today': len(self.processed_today),
            'by_priority': by_priority
        }


# Funções utilitárias para casos comuns
def create_backlog_reminder(text: str, priority: str = "MEDIUM") -> str:
    """Cria um lembrete no backlog."""
    backlog = ContextBacklog()
    p = BacklogPriority[priority.upper()]
    return backlog.add(text, p, source="reminder")


def create_user_backlog(user_text: str, ai_should_address: str, priority: str = "HIGH") -> str:
    """
    Cria backlog baseado em algo que o usuário mencionou.
    
    Args:
        user_text: O que o usuário disse
        ai_should_address: O que a IA deve abordar sobre isso
        priority: Prioridade
    """
    backlog = ContextBacklog()
    p = BacklogPriority[priority.upper()]
    content = f"Usuário mencionou: '{user_text[:50]}...' -> Abordar: {ai_should_address}"
    return backlog.add(content, p, source="user_context", auto_insert=True)


if __name__ == "__main__":
    # Testes
    backlog = ContextBacklog("test_backlog.json")
    
    print("Teste de ContextBacklog:")
    
    # Adiciona itens de teste
    backlog.add("Lembre: o usuário gosta de pizza", BacklogPriority.LOW, "memory")
    backlog.add("URGENTE: Usuário disse que está triste", BacklogPriority.CRITICAL, "user", auto_insert=True)
    backlog.add("Mencione o clima depois", BacklogPriority.MEDIUM, "proactive")
    
    # Pega pendentes
    pending = backlog.get_pending(max_items=2)
    print(f"\nItens pendentes: {len(pending)}")
    for p in pending:
        print(f"  - [{p['priority_label']}] {p['content'][:40]}...")
    
    # Testa injeção
    injection = backlog.get_context_injection()
    print(f"\nInjeção:\n{injection}")
    
    # Estatísticas
    print(f"\nStats: {backlog.get_stats()}")
    
    backlog.save()
