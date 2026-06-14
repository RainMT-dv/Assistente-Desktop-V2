"""Proactive Speaking Engine - Fala proativa quando usuário está em silêncio.

Referência: Open-LLM-VTuber - Frontend manda ai-speak-signal → backend usa prompt
especial que NÃO salva no histórico (skip_memory: True, skip_history: True).
"""

import asyncio
import threading
import time
from typing import Callable, Optional, Dict, Any


class ProactiveEngine:
    """Engine para fala proativa baseada em timer de silêncio."""

    # Prompts proativos - rodam em ciclo para variedade
    PROACTIVE_PROMPTS = [
        "Diga algo casual e engajante. Seja breve (1-2 frases).",
        "Comente algo interessante ou faça uma pergunta casual. Curto.",
        "Quebre o silêncio com algo divertido ou curioso. 1-2 frases.",
        "Fale algo que uma amiga diria depois de um silêncio. Breve.",
    ]

    def __init__(
        self,
        interval_seconds: int = 120,
        callback: Optional[Callable[[str], None]] = None,
        grace_period: int = 45
    ):
        """
        Initialize proactive engine.

        Args:
            interval_seconds: Tempo de silêncio antes de falar (default: 120s)
            callback: Função chamada quando deve falar proativamente
            grace_period: Período de graça após interação do usuário (default: 45s)
        """
        # Cooldown adaptativo: grace period (curto) vs normal (longo)
        self.normal_interval = interval_seconds  # 120s - cooldown padrão
        self.grace_period = grace_period       # 45s - após interação do usuário
        self.current_interval = self.normal_interval  # Intervalo atual (muda dinamicamente)
        
        self.callback = callback
        self.last_interaction_time = time.time()
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._prompt_index = 0
        self._in_grace_period = False  # Flag para tracking do estado

    def _get_next_prompt(self) -> str:
        """Retorna próximo prompt proativo (rotaciona lista)."""
        prompt = self.PROACTIVE_PROMPTS[self._prompt_index]
        self._prompt_index = (self._prompt_index + 1) % len(self.PROACTIVE_PROMPTS)
        return prompt

    def _timer_loop(self) -> None:
        """Loop do timer em thread separada com cooldown adaptativo."""
        while not self._stop_event.is_set():
            # Esperar 1 segundo por iteração para permitir stop rápido
            self._stop_event.wait(1)

            if not self._running or self._stop_event.is_set():
                continue

            elapsed = time.time() - self.last_interaction_time

            if elapsed >= self.current_interval:
                # COOLDOWN ADAPTATIVO: Verificar qual intervalo expirou
                if self._in_grace_period:
                    # Grace period acabou -> usuário ficou inativo, voltar para normal
                    self._in_grace_period = False
                    self.current_interval = self.normal_interval
                    self.last_interaction_time = time.time()  # Reset timer para novo intervalo
                    print(f"[PROATIVO] Grace period ({self.grace_period}s) expirado - Usuário inativo. Voltando para cooldown normal: {self.normal_interval}s")
                    # NÃO gera resposta proativa ainda - apenas troca o intervalo
                else:
                    # Cooldown normal expirou -> gerar resposta proativa
                    if self.callback:
                        try:
                            self.callback()  # Callback sem argumentos - Skill Manager fornece a ação
                        except Exception as e:
                            print(f"[ERRO] Falha no callback proativo: {e}")

                    # Reset timer para não spammar (mantém intervalo normal)
                    self.last_interaction_time = time.time()

    def start(self) -> None:
        """Inicia o timer de fala proativa."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()
        print(f"[INFO] Proactive engine iniciado (intervalo: {self.normal_interval}s)")

    def stop(self) -> None:
        """Para o timer de fala proativa."""
        self._running = False
        self._stop_event.set()

        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2)

        print("[INFO] Proactive engine parado")

    def reset_timer(self) -> None:
        """Reseta o timer de silêncio com cooldown adaptativo (chamar quando usuário fala)."""
        self.last_interaction_time = time.time()
        
        # COOLDOWN ADAPTATIVO: Sempre resetar para grace period após interação do usuário
        # Isso evita que a IA fale proativo logo após uma resposta
        if not self._in_grace_period:
            self._in_grace_period = True
            self.current_interval = self.grace_period
            print(f"[PROATIVO] Timer resetado - Grace period: {self.grace_period}s (usuário ativo)")
        else:
            # Já está em grace period, apenas atualiza o timestamp (usuário continua ativo)
            print(f"[PROATIVO] Timer resetado - Grace period continua: {self.grace_period}s (usuário ainda ativo)")

    def update_interval(self, seconds: int) -> None:
        """Atualiza o intervalo de silêncio normal (não grace period)."""
        self.normal_interval = max(30, seconds)  # Mínimo 30s
        # Se não está em grace period, atualiza o current também
        if not self._in_grace_period:
            self.current_interval = self.normal_interval
        print(f"[INFO] Intervalo proativo atualizado: {self.normal_interval}s (grace period: {self.grace_period}s)")

    def is_running(self) -> bool:
        """Retorna True se engine está rodando."""
        return self._running

    def get_remaining_seconds(self) -> float:
        """Retorna segundos restantes até próxima ação (grace period ou proativa)."""
        if not self._running:
            return -1
        elapsed = time.time() - self.last_interaction_time
        return max(0, self.current_interval - elapsed)
    
    def is_user_active(self) -> bool:
        """Retorna True se usuário está em grace period (ativo recentemente)."""
        if not self._running:
            return False
        elapsed = time.time() - self.last_interaction_time
        return self._in_grace_period and elapsed < self.grace_period
    
    def get_status(self) -> dict:
        """Retorna status completo do engine para debug."""
        elapsed = time.time() - self.last_interaction_time
        return {
            "running": self._running,
            "in_grace_period": self._in_grace_period,
            "grace_period": self.grace_period,
            "normal_interval": self.normal_interval,
            "current_interval": self.current_interval,
            "remaining": self.get_remaining_seconds(),
            "elapsed": elapsed,
            "user_active": self.is_user_active()
        }


# Constante do prompt proativo para uso externo
PROACTIVE_PROMPT_TEMPLATE = """O usuário está em silêncio há um tempo. {instruction}

IMPORTANTE:
- Seja breve (1-2 frases)
- Não mencione explicitamente que o usuário está em silêncio
- Não use emojis
- Mantenha sua personalidade"""


def format_proactive_prompt(instruction: str) -> str:
    """Formata prompt proativo completo."""
    return PROACTIVE_PROMPT_TEMPLATE.format(instruction=instruction)


if __name__ == "__main__":
    # Teste
    print("=" * 60)
    print("Proactive Engine - Teste")
    print("=" * 60)

    def on_proactive(prompt: str) -> None:
        print(f"\n🎯 PROATIVO DISPARADO!")
        print(f"   Prompt: {prompt}")
        print(f"   Hora: {time.strftime('%H:%M:%S')}")

    engine = ProactiveEngine(interval_seconds=5, callback=on_proactive)

    print(f"\nTimer iniciado (5s para teste)")
    print("Simulando interação em 3s...")

    engine.start()

    # Simular interação após 3s
    time.sleep(3)
    print(f"\n👤 Usuário interagiu - timer resetado")
    engine.reset_timer()

    # Esperar mais 5s para ver disparo
    print("Aguardando disparo proativo (5s)...")
    time.sleep(6)

    engine.stop()
    print("\n✅ Teste concluído")
