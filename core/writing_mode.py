"""
writing_mode.py - Modo Escrita/Ditado Ativo

Neste modo, a IA monitora o que o usuário está digitando e faz comentários
em tempo real sobre o texto sendo escrito.

Funciona detectando mudanças no clipboard (Ctrl+C/Ctrl+X) ou integração
com o sistema de captura de teclas.

Útil para:
- Revisão colaborativa de textos
- Brainstorming com comentários da IA
- Ditado onde IA corrige/expande ideias
"""

import threading
import time
from typing import Callable, Optional, List
from datetime import datetime
from dataclasses import dataclass

from .logger import log


@dataclass
class WritingSession:
    """Registra uma sessão de escrita."""
    start_time: datetime
    text: str
    comments: List[str]
    active: bool = True


class WritingMode:
    """
    Modo escrita ativa com comentários da IA.
    
    Detecta quando usuário está digitando e faz comentários contextuais.
    """
    
    # Frases para comentar durante escrita
    COMMENTS = [
        "Hmm, interessante continuação...",
        "Essa frase tá ficando boa hein...",
        "Não esquece de revisar depois...",
        "Tá fluindo bem esse texto...",
        "Cuidado com a pontuação aí...",
        "Isso aí vai ficar épico quando terminar...",
        "Tá escrevendo rápido, hein?",
        "Essa ideia tá boa, continua...",
        "Já pensou em desenvolver mais isso?",
        "Tá ficando comprido, mas vai dar certo...",
    ]
    
    ENCOURAGEMENTS = [
        "Boa! Continua assim...",
        "Tá indo bem, não para não...",
        "Isso aí, mete bronca...",
        "Vai que dá certo...",
        "Confia no processo...",
    ]
    
    def __init__(
        self,
        comment_interval: float = 30.0,
        min_text_length: int = 20,
        on_comment: Optional[Callable[[str], None]] = None,
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None
    ):
        """
        Inicializa o WritingMode.
        
        Args:
            comment_interval: Segundos entre comentários automáticos
            min_text_length: Tamanho mínimo do texto para começar a comentar
            on_comment: Callback quando há comentário para falar
            on_start: Callback quando modo inicia
            on_stop: Callback quando modo para
        """
        self.comment_interval = comment_interval
        self.min_text_length = min_text_length
        self.on_comment = on_comment
        self.on_start = on_start
        self.on_stop = on_stop
        
        self._active = False
        self._session: Optional[WritingSession] = None
        self._last_text = ""
        self._last_comment_time = 0.0
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Estatísticas
        self.sessions_count = 0
        self.total_comments = 0
    
    def start(self, initial_text: str = ""):
        """Inicia o modo escrita."""
        with self._lock:
            if self._active:
                return
            self._active = True
            self._stop_event.clear()
        
        self._session = WritingSession(
            start_time=datetime.now(),
            text=initial_text,
            comments=[]
        )
        self._last_text = initial_text
        self.sessions_count += 1
        
        # Inicia thread de monitoramento
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        print(f"[WRITING_MODE] Iniciado (intervalo: {self.comment_interval}s)")
        
        if self.on_start:
            try:
                self.on_start()
            except Exception as e:
                print(f"[WRITING_MODE] Erro no on_start: {e}")
    
    def stop(self) -> Optional[WritingSession]:
        """
        Para o modo escrita.
        
        Returns:
            Sessão completa com todos os dados
        """
        with self._lock:
            if not self._active:
                return self._session
            self._active = False
        
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=2.0)
        
        if self._session:
            self._session.active = False
        
        print(f"[WRITING_MODE] Parado (sessão: {len(self._session.comments if self._session else [])} comentários)")
        
        if self.on_stop:
            try:
                self.on_stop()
            except Exception as e:
                print(f"[WRITING_MODE] Erro no on_stop: {e}")
        
        return self._session
    
    def _monitor_loop(self):
        """Loop de monitoramento do modo escrita."""
        while not self._stop_event.is_set():
            try:
                self._check_for_changes()
            except Exception as e:
                print(f"[WRITING_MODE] Erro no loop: {e}")
            
            # Espera com evento para parada rápida
            self._stop_event.wait(timeout=1.0)
    
    def _check_for_changes(self):
        """Verifica se houve mudanças no texto e faz comentários."""
        if not self._session:
            return
        
        # Obtém texto atual (pode vir de integração com sistema)
        current_text = self._get_current_text()
        
        if current_text == self._last_text:
            return
        
        # Detecta se é escrita ativa (mudanças frequentes)
        now = time.time()
        time_since_last = now - self._last_comment_time
        
        # Decide se faz comentário
        should_comment = False
        comment = ""
        
        # Comentário por intervalo
        if time_since_last >= self.comment_interval:
            if len(current_text) >= self.min_text_length:
                should_comment = True
                comment = self._generate_comment(current_text)
        
        # Comentário especial: muito texto escrito rapidamente
        added_length = len(current_text) - len(self._last_text)
        if added_length > 100 and time_since_last < 10:
            should_comment = True
            comment = random.choice(self.ENCOURAGEMENTS)
        
        if should_comment and comment:
            self._make_comment(comment)
            self._last_comment_time = now
        
        # Atualiza estado
        self._session.text = current_text
        self._last_text = current_text
    
    def _get_current_text(self) -> str:
        """
        Obtém texto atual sendo escrito.
        
        Por padrão, tenta obter do clipboard ou retorna último conhecido.
        Pode ser sobrescrito para integração com outras fontes.
        """
        try:
            # Tenta obter do clipboard
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData()
                    if isinstance(text, str):
                        return text
            finally:
                win32clipboard.CloseClipboard()
        except:
            pass
        
        return self._last_text
    
    def _generate_comment(self, text: str) -> str:
        """Gera comentário baseado no texto atual."""
        import random
        
        # Se texto está muito longo, comenta sobre isso
        if len(text) > 500:
            return "Tá escrevendo um livro aí? Isso tá ficando grande hein..."
        
        # Se texto curto, encorajamento genérico
        if len(text) < 100:
            return random.choice(self.ENCOURAGEMENTS)
        
        # Comentário genérico
        return random.choice(self.COMMENTS)
    
    def _make_comment(self, comment: str):
        """Registra e dispara comentário."""
        if self._session:
            self._session.comments.append(comment)
        
        self.total_comments += 1
        
        log('WRITING_MODE', f'Comentário: {comment}')
        
        if self.on_comment:
            try:
                self.on_comment(comment)
            except Exception as e:
                log('WRITING_MODE', f'Erro no on_comment: {e}')
    
    def force_comment(self, comment: str):
        """Força um comentário específico imediatamente."""
        self._make_comment(comment)
        self._last_comment_time = time.time()
    
    def update_text(self, text: str):
        """
        Atualiza texto manualmente (para integração externa).
        
        Args:
            text: Texto atual sendo escrito
        """
        self._last_text = text
        if self._session:
            self._session.text = text
    
    def is_active(self) -> bool:
        """Retorna True se modo está ativo."""
        return self._active
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do modo escrita."""
        return {
            "active": self._active,
            "sessions_count": self.sessions_count,
            "total_comments": self.total_comments,
            "current_session": {
                "duration_seconds": (datetime.now() - self._session.start_time).total_seconds() if self._session else 0,
                "text_length": len(self._session.text) if self._session else 0,
                "comments_count": len(self._session.comments) if self._session else 0
            } if self._session else None
        }
    
    def get_current_text(self) -> str:
        """Retorna texto atual da sessão."""
        return self._session.text if self._session else ""
    
    def get_comments(self) -> List[str]:
        """Retorna comentários da sessão atual."""
        return self._session.comments if self._session else []


class WritingModeIntegration:
    """
    Integração do WritingMode com o sistema principal.
    Permite ativar o modo via comandos de voz ou interface.
    """
    
    def __init__(self, core_system):
        """
        Inicializa integração.
        
        Args:
            core_system: Referência ao sistema principal (com tts, chat, etc)
        """
        self.core = core_system
        self.writing_mode: Optional[WritingMode] = None
        self._setup()
    
    def _setup(self):
        """Configura o WritingMode com callbacks do sistema."""
        def on_comment(comment: str):
            # Envia comentário para TTS
            if hasattr(self.core, 'tts'):
                # Adiciona [Neutra] para emotion parser
                self.core.tts.speak(f"[Neutra] {comment}")
        
        def on_start():
            if hasattr(self.core, 'tts'):
                self.core.tts.speak("[Feliz] Modo escrita ativado! Vou ficar de olho no que você escrever.")
        
        def on_stop():
            if hasattr(self.core, 'tts'):
                self.core.tts.speak("[Neutra] Modo escrita desativado.")
        
        self.writing_mode = WritingMode(
            comment_interval=45.0,  # Comenta a cada 45s
            on_comment=on_comment,
            on_start=on_start,
            on_stop=on_stop
        )
    
    def start(self):
        """Inicia modo escrita."""
        if self.writing_mode:
            self.writing_mode.start()
    
    def stop(self):
        """Para modo escrita."""
        if self.writing_mode:
            return self.writing_mode.stop()
        return None
    
    def toggle(self) -> bool:
        """
        Alterna modo escrita.
        
        Returns:
            True se ativou, False se desativou
        """
        if self.writing_mode and self.writing_mode.is_active():
            self.stop()
            return False
        else:
            self.start()
            return True


# ============== FUNÇÕES DE CONVENIÊNCIA ==============

_default_writing_mode: Optional[WritingMode] = None


def start_writing_mode(
    on_comment: Optional[Callable[[str], None]] = None,
    interval: float = 30.0
) -> WritingMode:
    """
    Inicia modo escrita simples.
    
    Args:
        on_comment: Callback para comentários
        interval: Intervalo entre comentários
        
    Returns:
        Instância do WritingMode
    """
    global _default_writing_mode
    _default_writing_mode = WritingMode(
        comment_interval=interval,
        on_comment=on_comment
    )
    _default_writing_mode.start()
    return _default_writing_mode


def stop_writing_mode() -> Optional[WritingSession]:
    """Para modo escrita padrão."""
    global _default_writing_mode
    if _default_writing_mode:
        return _default_writing_mode.stop()
    return None


# ============== TESTES ==============

if __name__ == "__main__":
    import random
    
    log('WRITING_MODE', "=" * 50)
    log('WRITING_MODE', "TESTE: WritingMode")
    log('WRITING_MODE', "=" * 50)
    
    comments_received = []
    
    def on_comment(comment):
        comments_received.append(comment)
        log('WRITING_MODE', f"   [CALLBACK] {comment}")
    
    def on_start():
        log('WRITING_MODE', "   [CALLBACK] Modo iniciado!")
    
    def on_stop():
        log('WRITING_MODE', "   [CALLBACK] Modo parado!")
    
    # Cria modo
    mode = WritingMode(
        comment_interval=3.0,  # 3s para teste rápido
        min_text_length=10,
        on_comment=on_comment,
        on_start=on_start,
        on_stop=on_stop
    )
    
    log('WRITING_MODE', "\n1. Iniciando modo escrita...")
    mode.start()
    
    log('WRITING_MODE', "\n2. Simulando digitação...")
    time.sleep(1)
    
    # Simula texto sendo escrito
    test_texts = [
        "Olá,",
        "Olá, mundo",
        "Olá, mundo! Isso",
        "Olá, mundo! Isso é um teste de",
        "Olá, mundo! Isso é um teste de escrita contínua onde a IA faz comentários sobre o que estou digitando em tempo real.",
    ]
    
    for text in test_texts:
        mode.update_text(text)
        log('WRITING_MODE', f"   Texto atual: {text[:50]}...")
        time.sleep(3.5)  # Acima do intervalo para trigger
    
    log('WRITING_MODE', "\n3. Parando modo...")
    session = mode.stop()
    
    log('WRITING_MODE', f"\n4. Resumo da sessão:")
    log('WRITING_MODE', f"   - Duração: {(session.start_time - datetime.now()).total_seconds():.1f}s")
    log('WRITING_MODE', f"   - Texto final: {len(session.text)} chars")
    log('WRITING_MODE', f"   - Comentários: {len(session.comments)}")
    for i, c in enumerate(session.comments, 1):
        log('WRITING_MODE', f"     {i}. {c}")
    
    log('WRITING_MODE', "\n" + "=" * 50)
    log('WRITING_MODE', "TESTES CONCLUÍDOS")
    log('WRITING_MODE', "=" * 50)
    print("=" * 50)
