"""
text_capture.py - Captura de Texto via Clipboard

Monitora o clipboard para detectar quando o usuário copia texto.
Útil para:
- Capturar texto selecionado em qualquer aplicação
- Permitir que a IA comente sobre o texto copiado
- Integração com sistema de contexto multimodal

Funciona por polling do clipboard a cada X segundos.
"""

import threading
import time
from typing import Callable, Optional
from datetime import datetime

from .logger import log


class TextCapture:
    """
    Monitor de clipboard para captura de texto selecionado.
    
    Detecta mudanças no conteúdo textual do clipboard e dispara callback.
    """
    
    def __init__(
        self,
        poll_interval: float = 1.0,
        min_length: int = 3,
        max_length: int = 5000,
        callback: Optional[Callable[[str], None]] = None,
        ignore_duplicates: bool = True
    ):
        """
        Inicializa o TextCapture.
        
        Args:
            poll_interval: Intervalo em segundos entre verificações do clipboard
            min_length: Tamanho mínimo do texto para disparar callback
            max_length: Tamanho máximo do texto (trunca se maior)
            callback: Função a chamar quando novo texto é detectado
            ignore_duplicates: Se True, ignora textos iguais ao anterior
        """
        self.poll_interval = poll_interval
        self.min_length = min_length
        self.max_length = max_length
        self.callback = callback
        self.ignore_duplicates = ignore_duplicates
        
        self._last_text: str = ""
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._capture_count = 0
        self._last_capture_time: Optional[datetime] = None
    
    def start(self):
        """Inicia o monitoramento do clipboard."""
        with self._lock:
            if self._running:
                return
            self._running = True
        
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        log('TEXT_CAPTURE', f'Monitor iniciado (intervalo: {self.poll_interval}s)')
    
    def stop(self):
        """Para o monitoramento."""
        with self._lock:
            self._running = False
        
        if self._thread:
            self._thread.join(timeout=2.0)
        
        log('TEXT_CAPTURE', 'Monitor parado')
    
    def _get_clipboard_text(self) -> Optional[str]:
        """
        Obtém texto atual do clipboard.
        
        Returns:
            Texto do clipboard ou None se não disponível/não é texto
        """
        try:
            import win32clipboard
            
            win32clipboard.OpenClipboard()
            try:
                # Verifica se é texto
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT) or \
                   win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData()
                    if isinstance(data, bytes):
                        return data.decode('utf-8', errors='ignore')
                    return str(data)
            finally:
                win32clipboard.CloseClipboard()
                
        except ImportError:
            # Fallback usando tkinter (mais lento mas universal)
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()
                text = root.clipboard_get()
                root.destroy()
                return text
            except:
                return None
        except Exception as e:
            # Silenciosamente retorna None em erros
            return None
        
        return None
    
    def _poll_loop(self):
        """Loop principal de polling."""
        while True:
            with self._lock:
                if not self._running:
                    break
            
            try:
                self._check_clipboard()
            except Exception as e:
                print(f"[TEXT_CAPTURE] Erro: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_clipboard(self):
        """Verifica se há novo texto no clipboard."""
        text = self._get_clipboard_text()
        
        if text is None:
            return
        
        # Limpa e normaliza
        text = text.strip()
        
        # Verifica tamanho mínimo
        if len(text) < self.min_length:
            return
        
        # Verifica duplicata
        if self.ignore_duplicates and text == self._last_text:
            return
        
        # Atualiza estado
        self._last_text = text
        self._capture_count += 1
        self._last_capture_time = datetime.now()
        
        # Trunca se necessário
        if len(text) > self.max_length:
            text = text[:self.max_length] + "..."
        
        log('TEXT_CAPTURE', f'Novo texto capturado: {text[:50]}...')
        
        # Dispara callback
        if self.callback:
            try:
                self.callback(text)
            except Exception as e:
                print(f"[TEXT_CAPTURE] Erro no callback: {e}")
    
    def get_last_text(self) -> str:
        """Retorna último texto capturado."""
        return self._last_text
    
    def get_stats(self) -> dict:
        """Retorna estatísticas de captura."""
        return {
            "running": self._running,
            "capture_count": self._capture_count,
            "last_capture": self._last_capture_time.isoformat() if self._last_capture_time else None,
            "last_text_preview": self._last_text[:100] if self._last_text else "",
            "poll_interval": self.poll_interval
        }
    
    def clear_history(self):
        """Limpa histórico de capturas."""
        self._last_text = ""
        self._capture_count = 0
        self._last_capture_time = None
        print("[TEXT_CAPTURE] Histórico limpo")


class SmartTextCapture(TextCapture):
    """
    Versão inteligente com filtros adicionais.
    Ignora certos tipos de texto (URLs, paths, código, etc).
    """
    
    # Padrões para ignorar
    IGNORE_PATTERNS = [
        r'^https?://',  # URLs
        r'^C:\\\\',      # Windows paths
        r'^/usr/',      # Unix paths
        r'^\d{4}-\d{2}-\d{2}$',  # Datas ISO
        r'^\d{1,2}/\d{1,2}/\d{2,4}$',  # Datas BR
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import re
        self._patterns = [re.compile(p) for p in self.IGNORE_PATTERNS]
    
    def _check_clipboard(self):
        """Verifica com filtros adicionais."""
        text = self._get_clipboard_text()
        
        if text is None:
            return
        
        text = text.strip()
        
        # Ignora se match algum padrão
        for pattern in self._patterns:
            if pattern.match(text):
                return
        
        # Verifica se parece código (muitos caracteres especiais)
        special_ratio = sum(1 for c in text if c in '{}[]()<>/\\|;:') / max(len(text), 1)
        if special_ratio > 0.1 and len(text) > 100:
            # Provavelmente código, ignora
            return
        
        # Continua com lógica normal
        super()._check_clipboard()


# ============== FUNÇÕES DE CONVENIÊNCIA ==============

_default_capture: Optional[TextCapture] = None


def start_text_capture(
    callback: Callable[[str], None],
    poll_interval: float = 1.0
) -> TextCapture:
    """
    Inicia captura de texto com callback simples.
    
    Args:
        callback: Função(texto) a chamar quando texto é capturado
        poll_interval: Intervalo de polling em segundos
        
    Returns:
        Instância do TextCapture
    """
    global _default_capture
    _default_capture = TextCapture(
        poll_interval=poll_interval,
        callback=callback
    )
    _default_capture.start()
    return _default_capture


def stop_text_capture():
    """Para captura de texto padrão."""
    global _default_capture
    if _default_capture:
        _default_capture.stop()
        _default_capture = None


def get_captured_text() -> str:
    """Retorna último texto capturado."""
    if _default_capture:
        return _default_capture.get_last_text()
    return ""


# ============== TESTES ==============

if __name__ == "__main__":
    print("=" * 50)
    print("TESTE: TextCapture")
    print("=" * 50)
    print("\nCopie algum texto para testar...")
    print("(Ctrl+C em qualquer lugar)")
    print("Pressione Ctrl+C aqui para parar\n")
    
    captured_texts = []
    
    def on_capture(text):
        captured_texts.append(text)
        print(f"   [CALLBACK] Capturado: {text[:60]}...")
    
    # Testa TextCapture normal
    capture = TextCapture(
        poll_interval=0.5,
        callback=on_capture,
        min_length=5
    )
    capture.start()
    
    try:
        import signal
        
        def signal_handler(sig, frame):
            raise KeyboardInterrupt()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Aguarda por tempo ou até interrompido
        time.sleep(30)
        
    except KeyboardInterrupt:
        pass
    finally:
        capture.stop()
    
    print(f"\n   Total capturado: {len(captured_texts)} textos")
    print(f"   Stats: {capture.get_stats()}")
    
    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print("=" * 50)
