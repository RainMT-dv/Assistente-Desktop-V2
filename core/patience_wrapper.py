"""
patience_wrapper.py - Wrapper de Paciência para Inatividade

Monitora inatividade do usuário e dispara callback quando limite é atingido.
Usado para reengajar o usuário após período sem interação.
"""

import threading
import time
import random
from typing import Callable, Optional
from datetime import datetime

from .logger import log


class PatienceWrapper:
    """
    Monitor de inatividade com timer.
    
    Após X segundos sem interação do usuário, dispara um callback.
    O callback pode ser usado para:
    - Reengajar o usuário com pergunta
    - Executar skill proativa
    - Comentar sobre o silêncio
    """
    
    def __init__(
        self,
        inactivity_threshold: float = 10.0,
        callback: Optional[Callable[[], None]] = None,
        reset_on_trigger: bool = True
    ):
        """
        Inicializa o PatienceWrapper.
        
        Args:
            inactivity_threshold: Segundos de inatividade para disparar callback (padrão: 10)
            callback: Função a ser chamada quando inatividade atingir threshold
            reset_on_trigger: Se True, reseta o timer após disparar callback
        """
        self.inactivity_threshold = inactivity_threshold
        self.callback = callback
        self.reset_on_trigger = reset_on_trigger
        
        self._timer: Optional[threading.Timer] = None
        self._last_activity: float = time.time()
        self._lock = threading.Lock()
        self._running = False
        self._trigger_count = 0
        
        # Mensagens variadas para reengajamento (evitar repetição monótona)
        self.reengage_messages = [
            "Ei, continua ai? To te ouvindo...",
            "Ficou mudo de repente? O que aconteceu?",
            "Ta dormindo em? Acorda!",
            "Oi? Terra chamando usuario...",
            "Continua ai ou desistiu?",
            "To esperando... nao shiesta.",
            "Esqueceu de mim ja? Que triste.",
            "Vai falar ou vai ficar olhando?",
            "Bot, ta ai? Me confirma.",
            "... Alô? Perdi o sinal?",
            "Ainda vivo ai? Responde qualquer coisa.",
            "Foi pegar café? Me avisa quando voltar."
        ]
        
    def start(self):
        """Inicia o monitor de inatividade."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._last_activity = time.time()
            self._schedule_timer()
        log('PATIENCE', f'Monitor iniciado (threshold: {self.inactivity_threshold}s)')
    
    def stop(self):
        """Para o monitor de inatividade."""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
        log('PATIENCE', 'Monitor parado')
    
    def _schedule_timer(self):
        """Agenda o próximo timer."""
        if not self._running:
            return
            
        # Cancela timer anterior se existir
        if self._timer:
            self._timer.cancel()
        
        # Calcula tempo restante
        elapsed = time.time() - self._last_activity
        remaining = max(0.1, self.inactivity_threshold - elapsed)
        
        # Agenda novo timer
        self._timer = threading.Timer(remaining, self._on_timeout)
        self._timer.daemon = True
        self._timer.start()
    
    def _on_timeout(self):
        """Chamado quando timer expira (inatividade atingiu threshold)."""
        with self._lock:
            if not self._running:
                return
            
            elapsed = time.time() - self._last_activity
            if elapsed < self.inactivity_threshold:
                # Atividade ocorreu enquanto timer aguardava, reagenda
                self._schedule_timer()
                return
            
            # Threshold atingido!
            self._trigger_count += 1
            log('PATIENCE', f'Inatividade detectada ({self.inactivity_threshold}s) - Trigger #{self._trigger_count}')
            
            # Chama callback se definido
            if self.callback:
                try:
                    self.callback()
                except Exception as e:
                    print(f"[PATIENCE] Erro no callback: {e}")
            
            # Reseta ou reagenda
            if self.reset_on_trigger:
                self._last_activity = time.time()
                self._schedule_timer()
            else:
                self._running = False
    
    def poke(self):
        """
        Registra atividade do usuário (reset timer).
        Chame sempre que houver interação do usuário.
        """
        with self._lock:
            self._last_activity = time.time()
            was_running = self._running
        
        # Reagenda timer fora do lock para evitar deadlock
        if was_running:
            self._schedule_timer()
    
    def reset_timer(self):
        """Alias público para poke() - reseta o timer de inatividade."""
        self.poke()
        log('PATIENCE', 'Timer resetado por interacao do usuario')
    
    def get_random_reengage_message(self) -> str:
        """Retorna uma mensagem de reengajamento aleatória."""
        return random.choice(self.reengage_messages)
    
    def get_inactivity_seconds(self) -> float:
        """Retorna segundos desde última atividade."""
        return time.time() - self._last_activity
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do monitor."""
        return {
            "threshold": self.inactivity_threshold,
            "running": self._running,
            "trigger_count": self._trigger_count,
            "inactivity_seconds": self.get_inactivity_seconds(),
            "last_activity": datetime.fromtimestamp(self._last_activity).isoformat()
        }


class PatienceManager:
    """
    Gerenciador de múltiplos PatienceWrappers com diferentes thresholds.
    Permite callbacks em cascata (10s, 30s, 60s, etc).
    """
    
    def __init__(self):
        self.wrappers: dict[str, PatienceWrapper] = {}
        self._lock = threading.Lock()
    
    def add(
        self,
        name: str,
        threshold: float,
        callback: Callable[[], None],
        reset_on_trigger: bool = True
    ) -> PatienceWrapper:
        """
        Adiciona um novo wrapper.
        
        Args:
            name: Identificador único
            threshold: Segundos de inatividade
            callback: Função a chamar
            reset_on_trigger: Se reseta após trigger
            
        Returns:
            Instância do PatienceWrapper criada
        """
        with self._lock:
            wrapper = PatienceWrapper(threshold, callback, reset_on_trigger)
            self.wrappers[name] = wrapper
            log('PATIENCE', f'Adicionado: {name} ({threshold}s)')
            return wrapper
    
    def start_all(self):
        """Inicia todos os wrappers."""
        for name, wrapper in self.wrappers.items():
            wrapper.start()
    
    def stop_all(self):
        """Para todos os wrappers."""
        for wrapper in self.wrappers.values():
            wrapper.stop()
    
    def poke_all(self):
        """Registra atividade em todos os wrappers."""
        for wrapper in self.wrappers.values():
            wrapper.poke()
    
    def remove(self, name: str) -> bool:
        """Remove um wrapper pelo nome."""
        with self._lock:
            if name in self.wrappers:
                self.wrappers[name].stop()
                del self.wrappers[name]
                return True
            return False
    
    def get_stats(self) -> dict:
        """Retorna estatísticas de todos os wrappers."""
        return {
            name: wrapper.get_stats()
            for name, wrapper in self.wrappers.items()
        }


# ============== FUNÇÕES DE CONVENIÊNCIA ==============

_default_wrapper: Optional[PatienceWrapper] = None


def start_default_patience(callback: Callable[[], None], threshold: float = 10.0):
    """Inicia wrapper padrão com callback simples."""
    global _default_wrapper
    _default_wrapper = PatienceWrapper(threshold, callback)
    _default_wrapper.start()
    return _default_wrapper


def stop_default_patience():
    """Para wrapper padrão."""
    global _default_wrapper
    if _default_wrapper:
        _default_wrapper.stop()
        _default_wrapper = None


def poke_default():
    """Registra atividade no wrapper padrão."""
    if _default_wrapper:
        _default_wrapper.poke()


# ============== TESTES ==============

if __name__ == "__main__":
    import time
    
    print("=" * 50)
    print("TESTE: PatienceWrapper")
    print("=" * 50)
    
    triggered = []
    
    def on_trigger_10s():
        triggered.append("10s")
        print(f"   [CALLBACK] Trigger 10s! (total: {triggered})")
    
    def on_trigger_5s():
        triggered.append("5s")
        print(f"   [CALLBACK] Trigger 5s! (total: {triggered})")
    
    # Test 1: Manager com múltiplos timers
    print("\n1. Teste com múltiplos thresholds:")
    manager = PatienceManager()
    manager.add("curto", 5.0, on_trigger_5s)
    manager.add("longo", 10.0, on_trigger_10s)
    manager.start_all()
    
    print("   Aguardando 6 segundos...")
    time.sleep(6)
    print(f"   Stats: {manager.get_stats()}")
    
    print("   \nAguardando mais 5 segundos...")
    time.sleep(5)
    print(f"   Stats: {manager.get_stats()}")
    
    manager.stop_all()
    
    # Test 2: Poke/reset
    print("\n2. Teste de poke (reset):")
    triggered.clear()
    
    wrapper = PatienceWrapper(3.0, on_trigger_5s)
    wrapper.start()
    
    print("   Esperando 2s...")
    time.sleep(2)
    print(f"   Inatividade: {wrapper.get_inactivity_seconds():.1f}s")
    
    print("   Poke! Resetando timer...")
    wrapper.poke()
    time.sleep(2)
    print(f"   Inatividade após poke: {wrapper.get_inactivity_seconds():.1f}s")
    
    print("   Esperando 3s para trigger...")
    time.sleep(3.5)
    
    wrapper.stop()
    
    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print(f"Triggers disparados: {triggered}")
    print("=" * 50)
