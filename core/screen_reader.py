"""Screen Reader - Captura de tela e clipboard para visão do Assistente."""

import base64
import io
import os
from pathlib import Path

import pyperclip


class ScreenReader:
    """Captura de tela otimizada + clipboard (baseado na Shogun da Miyauti)."""

    def __init__(self, data_dir: str = "data"):
        """Inicializa o screen reader."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def capture_screen(self, monitor: int = 1) -> str:
        """Captura screenshot e salva otimizado."""
        try:
            import mss
            from PIL import Image
        except ImportError:
            raise ImportError("Instale: pip install mss pillow")

        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[monitor])
            img = Image.frombytes(
                "RGB", (screenshot.width, screenshot.height), screenshot.rgb
            )

            # Resize pra 400px altura (reduz tokens do vision)
            target_height = 400
            aspect = img.width / img.height
            new_width = int(target_height * aspect)
            img = img.resize((new_width, target_height), Image.LANCZOS)

            path = self.data_dir / "screenshot.jpg"
            img.save(path, "JPEG", quality=70, optimize=True, progressive=True)
            return str(path)

    def capture_screen_base64(self, monitor: int = 1) -> str:
        """Captura screenshot e retorna base64 (pra mandar pro LLM vision)."""
        try:
            import mss
            from PIL import Image
        except ImportError:
            raise ImportError("Instale: pip install mss pillow")

        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[monitor])
            img = Image.frombytes(
                "RGB", (screenshot.width, screenshot.height), screenshot.rgb
            )

            target_height = 400
            aspect = img.width / img.height
            new_width = int(target_height * aspect)
            img = img.resize((new_width, target_height), Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def read_clipboard(self) -> str:
        """Lê texto da área de transferência."""
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""

    def has_image_in_clipboard(self) -> bool:
        """Verifica se há imagem no clipboard."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            return img is not None
        except Exception:
            return False

    def get_clipboard_image_base64(self) -> str | None:
        """Retorna imagem do clipboard como base64, se existir."""
        try:
            from PIL import Image, ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                return None

            # Resize otimizado
            target_height = 400
            aspect = img.width / img.height
            new_width = int(target_height * aspect)
            img = img.resize((new_width, target_height), Image.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        except Exception:
            return None


def create_vision_messages(prompt_text: str, base64_image: str) -> list:
    """Cria mensagens formatadas para LLM vision (OpenRouter/Gemma)."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ],
        }
    ]


if __name__ == "__main__":
    # Teste
    reader = ScreenReader()

    print("Testando captura de tela...")
    try:
        path = reader.capture_screen()
        print(f"Screenshot salvo: {path}")

        b64 = reader.capture_screen_base64()
        print(f"Base64 length: {len(b64)} chars")
    except ImportError as e:
        print(f"Dependências não instaladas: {e}")

    print(f"\nClipboard: {reader.read_clipboard()[:100]}...")
