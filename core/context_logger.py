"""
context_logger.py - Logger de Contextos LLM para Debug

Salva todos os contextos que são enviados para o LLM em arquivos JSON,
permitindo análise posterior de:
- System prompts completos
- Histórico de mensagens
- Memórias injetadas
- Metacognição
- Backlogs

Útil para debugar problemas de contexto, histórico e comportamento da IA.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .logger import log


class ContextLogger:
    """
    Logger especializado para contextos LLM.
    
    Salva cada interação completa em JSON estruturado para análise.
    """
    
    def __init__(self, output_dir: str = "logs/contexts"):
        """
        Inicializa o ContextLogger.
        
        Args:
            output_dir: Diretório onde salvar os logs JSON
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.interaction_count = 0
        self.enabled = True
        
        log('CONTEXT_LOGGER', f'Iniciado em: {self.output_dir}')
    
    def log_interaction(
        self,
        messages: List[Dict[str, str]],
        user_input: str,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Loga uma interação completa com o LLM.
        
        Args:
            messages: Array completo de mensagens enviadas (inclui system + history)
            user_input: Input do usuário
            response: Resposta da IA
            metadata: Info adicional (emotion, mood, timestamp, etc)
            
        Returns:
            Caminho do arquivo JSON criado
        """
        if not self.enabled:
            return ""
        
        self.interaction_count += 1
        timestamp = datetime.now()
        
        # Monta o registro
        entry = {
            "session_id": self.session_id,
            "interaction_number": self.interaction_count,
            "timestamp": timestamp.isoformat(),
            "unix_timestamp": timestamp.timestamp(),
            "user_input": user_input,
            "response": response,
            "full_context": {
                "message_count": len(messages),
                "messages": messages  # Contexto completo enviado ao LLM
            },
            "metadata": metadata or {}
        }
        
        # Gera nome de arquivo
        filename = f"{self.session_id}_{self.interaction_count:04d}.json"
        filepath = self.output_dir / filename
        
        # Salva JSON formatado
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            log('CONTEXT_LOGGER', f'Salvo: {filename}')
            return str(filepath)
        except Exception as e:
            log('CONTEXT_LOGGER', f'Erro ao salvar: {e}')
            return ""
    
    def log_system_prompt(self, system_prompt: str, metadata: Optional[Dict] = None):
        """
        Loga o system prompt isoladamente para análise.
        
        Args:
            system_prompt: Texto do system prompt
            metadata: Metadados adicionais
        """
        if not self.enabled:
            return
        
        entry = {
            "session_id": self.session_id,
            "type": "system_prompt",
            "timestamp": datetime.now().isoformat(),
            "prompt": system_prompt,
            "prompt_length": len(system_prompt),
            "metadata": metadata or {}
        }
        
        filename = f"{self.session_id}_system.json"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            print(f"[CONTEXT_LOGGER] System prompt salvo: {filename}")
        except Exception as e:
            print(f"[CONTEXT_LOGGER] Erro ao salvar system prompt: {e}")
    
    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """
        Loga um erro durante interação com LLM.
        
        Args:
            error: Exceção ocorrida
            context: Contexto adicional quando erro ocorreu
        """
        if not self.enabled:
            return
        
        entry = {
            "session_id": self.session_id,
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        filename = f"{self.session_id}_error_{self.interaction_count:04d}.json"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            print(f"[CONTEXT_LOGGER] Erro salvo: {filename}")
        except Exception as e:
            print(f"[CONTEXT_LOGGER] Erro ao salvar erro: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do logger."""
        return {
            "session_id": self.session_id,
            "interaction_count": self.interaction_count,
            "output_dir": str(self.output_dir),
            "enabled": self.enabled
        }
    
    def get_recent_logs(self, count: int = 10) -> List[Path]:
        """
        Retorna os N logs mais recentes.
        
        Args:
            count: Quantidade de logs a retornar
            
        Returns:
            Lista de caminhos dos arquivos JSON
        """
        try:
            files = sorted(
                self.output_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            return files[:count]
        except Exception as e:
            print(f"[CONTEXT_LOGGER] Erro ao listar logs: {e}")
            return []
    
    def enable(self):
        """Habilita logging."""
        self.enabled = True
        print("[CONTEXT_LOGGER] Habilitado")
    
    def disable(self):
        """Desabilita logging."""
        self.enabled = False
        print("[CONTEXT_LOGGER] Desabilitado")
    
    def cleanup_old_logs(self, days: int = 7):
        """
        Remove logs mais antigos que X dias.
        
        Args:
            days: Número de dias para manter
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        try:
            for filepath in self.output_dir.glob("*.json"):
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime < cutoff:
                    filepath.unlink()
                    removed += 1
            
            print(f"[CONTEXT_LOGGER] Removidos {removed} logs antigos")
        except Exception as e:
            print(f"[CONTEXT_LOGGER] Erro ao limpar logs: {e}")


# ============== INTEGRAÇÃO COM CHAT_MANAGER ==============

class ChatManagerContextLogger:
    """
    Helper para integrar ContextLogger com ChatManager.
    Facilita log de interações completas.
    """
    
    def __init__(self, chat_manager, output_dir: str = "logs/contexts"):
        """
        Inicializa integração.
        
        Args:
            chat_manager: Instância do ChatManager
            output_dir: Diretório para logs
        """
        self.chat_manager = chat_manager
        self.logger = ContextLogger(output_dir)
    
    def log_current_state(self, user_input: str, response: str, emotion: str = "Neutra"):
        """
        Loga estado atual completo do ChatManager.
        
        Args:
            user_input: Input do usuário
            response: Resposta da IA
            emotion: Emoção detectada
        """
        # Monta contexto completo
        messages = []
        
        # System prompt
        if hasattr(self.chat_manager, 'system_prompt'):
            messages.append({
                "role": "system",
                "content": self.chat_manager.system_prompt
            })
        
        # History
        if hasattr(self.chat_manager, 'history'):
            messages.extend(self.chat_manager.history)
        
        # Mensagem atual
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Metadados
        metadata = {
            "emotion": emotion,
            "history_length": len(getattr(self.chat_manager, 'history', [])),
        }
        
        # Adiciona memória se disponível
        if hasattr(self.chat_manager, 'memory_context'):
            metadata["has_memory"] = bool(self.chat_manager.memory_context)
        
        if hasattr(self.chat_manager, 'mood_context'):
            metadata["mood"] = self.chat_manager.mood_context
        
        self.logger.log_interaction(messages, user_input, response, metadata)


# ============== FUNÇÕES DE CONVENIÊNCIA ==============

_default_logger: Optional[ContextLogger] = None


def get_context_logger(output_dir: str = "logs/contexts") -> ContextLogger:
    """Retorna instância global do ContextLogger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = ContextLogger(output_dir)
    return _default_logger


def log_interaction_simple(
    messages: List[Dict[str, str]],
    user_input: str,
    response: str,
    output_dir: str = "logs/contexts"
):
    """Função simples para logar interação sem instanciar classe."""
    logger = get_context_logger(output_dir)
    return logger.log_interaction(messages, user_input, response)


# ============== TESTES ==============

if __name__ == "__main__":
    print("=" * 50)
    print("TESTE: ContextLogger")
    print("=" * 50)
    
    # Cria logger
    logger = ContextLogger("logs/test_contexts")
    
    # Test 1: Log simples
    print("\n1. Teste de log simples:")
    messages = [
        {"role": "system", "content": "Você é uma IA de teste."},
        {"role": "user", "content": "Oi!"},
    ]
    filepath = logger.log_interaction(
        messages,
        "Oi!",
        "[Feliz] E aí! Tudo bem?",
        {"emotion": "Feliz", "test": True}
    )
    print(f"   Arquivo: {filepath}")
    
    # Test 2: System prompt
    print("\n2. Teste de system prompt:")
    logger.log_system_prompt(
        "Você é um assistente pessoal inteligente e prestativo.",
        {"version": "2.0"}
    )
    
    # Test 3: Error
    print("\n3. Teste de erro:")
    try:
        raise ValueError("Erro de teste")
    except Exception as e:
        logger.log_error(e, {"extra": "context"})
    
    # Test 4: Stats
    print("\n4. Estatísticas:")
    print(f"   {logger.get_stats()}")
    
    # Test 5: Listar logs
    print("\n5. Logs recentes:")
    recent = logger.get_recent_logs(5)
    for log in recent:
        print(f"   - {log.name}")
    
    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print("=" * 50)
