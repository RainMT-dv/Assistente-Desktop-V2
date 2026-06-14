"""Flask-SocketIO dashboard server for real-time web interface."""

import logging
import os
import sys
import threading
import time
from typing import Any, Optional

# Silencia logs do Flask/Werkzeug
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Import log do core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.logger import log

try:
    from flask import Flask, render_template, jsonify
    from flask_socketio import SocketIO, emit
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False
    Flask = None  # type: ignore
    SocketIO = None  # type: ignore
    render_template = jsonify = emit = None  # type: ignore


class DashboardServer:
    """Flask-SocketIO dashboard server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 5000, assistant_ref: Any = None):
        """
        Initialize the dashboard server.

        Args:
            host: Host to bind to
            port: Port to listen on
            assistant_ref: Reference to main assistant object
        """
        if not _FLASK_AVAILABLE:
            raise ImportError("Flask ou Flask-SocketIO não instalados. Instale com: pip install Flask Flask-SocketIO")

        self.host = host
        self.port = port
        self.assistant_ref = assistant_ref
        self.start_time = time.time()

        self.app = Flask(__name__, template_folder="templates")
        self.app.config["SECRET_KEY"] = "desktop-assistant-v2"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading")

        self._setup_routes()
        self._setup_socketio()

        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _format_uptime(self, seconds: int) -> str:
        """Format uptime as Xd Xh Xm Xs or Xh Xm Xs if less than 1 day. MUDANÇA 4."""
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        else:
            return f"{hours}h {minutes}m {secs}s"

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/api/status")
        def api_status():
            uptime_seconds = int(time.time() - self.start_time)
            
            # Obter mood se disponível
            mood_data = {}
            if self.assistant_ref and self.assistant_ref.mood_engine:
                mood_data = {
                    "mood": self.assistant_ref.mood_engine.get_mood_display(),
                    "mood_score": self.assistant_ref.mood_engine.mood,
                }
            
            assistant_name = self.assistant_ref.config.get("assistant", {}).get("name", "Assistente") if self.assistant_ref else "Assistente"
            card_name = self.assistant_ref.config.get("assistant", {}).get("selected_card", "assistente") if self.assistant_ref else "assistente"
            return jsonify({
                "status": "running",
                "uptime": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "current_emotion": self.assistant_ref.brain.get("current_emotion", "Neutra") if self.assistant_ref else "Neutra",
                "user_emotion": self.assistant_ref.brain.get("user_emotion", "neutral") if self.assistant_ref else "neutral",
                "interaction_count": self.assistant_ref.brain.get("interaction_count", 0) if self.assistant_ref else 0,
                "model": self.assistant_ref.chat.model if self.assistant_ref and self.assistant_ref.chat else "unknown",
                "assistant_name": assistant_name,
                "card_name": card_name,
                **mood_data,
            })

        @self.app.route("/api/memories")
        def api_memories():
            """Retorna memórias do usuário."""
            if not self.assistant_ref or not self.assistant_ref.memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            profile = self.assistant_ref.memory_manager.get_user_profile()
            facts = self.assistant_ref.memory_manager.data.get("facts", [])
            summaries = self.assistant_ref.memory_manager.get_recent_summaries(days=7)
            
            return jsonify({
                "profile": profile,
                "facts": facts[-20:],  # Últimos 20 fatos
                "summaries": summaries,
                "total_facts": len(facts),
            })

        @self.app.route("/api/mood")
        def api_mood():
            """Retorna mood atual."""
            if not self.assistant_ref or not self.assistant_ref.mood_engine:
                return jsonify({"error": "Mood engine not available"}), 503
            
            return jsonify({
                "mood": self.assistant_ref.mood_engine.get_mood_display(),
                "score": self.assistant_ref.mood_engine.mood,
                "label": self.assistant_ref.mood_engine.get_mood_label(),
            })

        @self.app.route("/api/export")
        def api_export():
            """Exporta histórico de conversa como texto."""
            if not self.assistant_ref or not self.assistant_ref.chat:
                return jsonify({"error": "Chat not available"}), 503
            
            assistant_name = self.assistant_ref.config.get("assistant", {}).get("name", "Assistente") if self.assistant_ref else "Assistente"
            history = self.assistant_ref.chat.history
            lines = [f"# Conversa com {assistant_name}\n", f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n", "-" * 40 + "\n\n"]
            
            for msg in history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if role == "user":
                    lines.append(f"Você: {content}\n\n")
                elif role == "assistant":
                    lines.append(f"{assistant_name}: {content}\n\n")
            
            export_text = "".join(lines)
            
            from flask import Response
            filename = f"conversa_{assistant_name.lower()}.txt"
            return Response(
                export_text,
                mimetype="text/plain",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        @self.app.route("/api/clear", methods=["POST"])
        def api_clear_history():
            """Limpa histórico de conversa."""
            if self.assistant_ref and self.assistant_ref.chat:
                self.assistant_ref.chat.clear_history()
                return jsonify({"success": True, "message": "Histórico limpo"})
            return jsonify({"error": "Chat not available"}), 503

    def _setup_socketio(self) -> None:
        """Setup SocketIO event handlers."""

        @self.socketio.on("connect")
        def handle_connect():
            log('DASHBOARD', 'Cliente conectado ao dashboard')
            self.broadcast_status()

        @self.socketio.on("disconnect")
        def handle_disconnect():
            log('DASHBOARD', 'Cliente desconectado do dashboard')

        @self.socketio.on("send_message")
        def handle_send_message(data):
            """Process text message via dashboard."""
            text = data.get("text", "").strip()
            if text and self.assistant_ref:
                # Process through assistant pipeline
                try:
                    import asyncio
                    asyncio.run(self.assistant_ref.process_text_input(text))
                except Exception as e:
                    log('ERROR', f'Erro ao processar mensagem: {e}')

        @self.socketio.on("request_status")
        def handle_request_status():
            self.broadcast_status()

        @self.socketio.on("request_memories")
        def handle_request_memories():
            """Envia memórias para o cliente."""
            if self.assistant_ref and self.assistant_ref.memory_manager:
                profile = self.assistant_ref.memory_manager.get_user_profile()
                facts = self.assistant_ref.memory_manager.data.get("facts", [])
                self.socketio.emit("memories_update", {
                    "profile": profile,
                    "facts_count": len(facts),
                    "recent_facts": facts[-10:],
                })

        @self.socketio.on("request_mood")
        def handle_request_mood():
            """Envia mood para o cliente."""
            if self.assistant_ref and self.assistant_ref.mood_engine:
                self.socketio.emit("mood_update", {
                    "mood": self.assistant_ref.mood_engine.get_mood_display(),
                    "score": self.assistant_ref.mood_engine.mood,
                })

        @self.socketio.on("clear_history")
        def handle_clear_history():
            """Limpa histórico via SocketIO."""
            if self.assistant_ref and self.assistant_ref.chat:
                self.assistant_ref.chat.clear_history()
                emit("history_cleared", {"success": True})
                self.broadcast_chat_message("[Sistema]", "Histórico limpo pelo usuário.", "Neutra", "neutral")

        @self.socketio.on("test_voice")
        def handle_test_voice():
            """Testa voz do TTS."""
            if self.assistant_ref and self.assistant_ref.tts:
                try:
                    import asyncio
                    asyncio.run(self.assistant_ref._speak_simple("Testando! Tô funcionando de boa."))
                    emit("voice_test", {"success": True})
                except Exception as e:
                    emit("voice_test", {"success": False, "error": str(e)})

    def broadcast_status(self) -> None:
        """Broadcast current status to all clients."""
        if not self._running:
            return

        uptime_seconds = int(time.time() - self.start_time)
        assistant_name = self.assistant_ref.config.get("assistant", {}).get("name", "Assistente") if self.assistant_ref else "Assistente"
        card_name = self.assistant_ref.config.get("assistant", {}).get("selected_card", "assistente") if self.assistant_ref else "assistente"
        status = {
            "status": "running",
            "current_emotion": self.assistant_ref.brain.get("current_emotion", "Neutra") if self.assistant_ref else "Neutra",
            "user_emotion": self.assistant_ref.brain.get("user_emotion", "neutral") if self.assistant_ref else "neutral",
            "interaction_count": self.assistant_ref.brain.get("interaction_count", 0) if self.assistant_ref else 0,
            "uptime": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "assistant_name": assistant_name,
            "card_name": card_name,
        }
        try:
            self.socketio.emit("status_update", status)
        except Exception as e:
            log('WARN', f'Falha ao broadcast status: {e}')

    def broadcast_chat_message(self, user_text: str, bot_text: str, emotion: str, user_emotion: str) -> None:
        """Broadcast a chat message to all clients."""
        if not self._running:
            return

        message = {
            "user_text": user_text,
            "bot_text": bot_text,
            "emotion": emotion,
            "user_emotion": user_emotion,
            "timestamp": int(time.time()),
        }
        try:
            self.socketio.emit("chat_message", message)
        except Exception as e:
            log('WARN', f'Falha ao broadcast chat: {e}')

    def broadcast_emotion_change(self, current_emotion: str, user_emotion: str) -> None:
        """Broadcast emotion change to all clients."""
        if not self._running:
            return

        data = {
            "current_emotion": current_emotion,
            "user_emotion": user_emotion,
            "timestamp": int(time.time()),
        }
        try:
            self.socketio.emit("emotion_change", data)
        except Exception as e:
            log('WARN', f'Falha ao broadcast emotion: {e}')

    def start(self, blocking: bool = False) -> None:
        """
        Start the dashboard server.

        Args:
            blocking: If True, block; otherwise run in daemon thread
        """
        if self._running:
            return

        self._running = True

        if blocking:
            log('DASHBOARD', f'Dashboard iniciado em http://{self.host}:{self.port}')
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False)
        else:
            self._thread = threading.Thread(
                target=self.socketio.run,
                args=(self.app,),
                kwargs={"host": self.host, "port": self.port, "debug": False},
                daemon=True,
            )
            self._thread.start()
            log('DASHBOARD', f'Dashboard iniciado em http://{self.host}:{self.port}')

    def stop(self) -> None:
        """Stop the dashboard server."""
        self._running = False
        log('DASHBOARD', 'Dashboard parado')

    @staticmethod
    def is_available() -> bool:
        """Check if Flask and Flask-SocketIO are available."""
        return _FLASK_AVAILABLE


if __name__ == "__main__":
    if not DashboardServer.is_available():
        log('ERROR', 'Flask ou Flask-SocketIO não instalados')
        exit(1)

    log('DASHBOARD', 'Testando DashboardServer...')

    class MockAssistant:
        def __init__(self):
            self.brain = {
                "current_emotion": "Feliz",
                "user_emotion": "neutral",
                "interaction_count": 42,
            }

        async def process_text_input(self, text: str) -> None:
            log('DASHBOARD', f'Processando: {text}')

    mock = MockAssistant()
    server = DashboardServer("0.0.0.0", 5000, mock)

    log('DASHBOARD', 'Iniciando servidor (Ctrl+C para parar)...')
    try:
        server.start(blocking=True)
    except KeyboardInterrupt:
        log('DASHBOARD', 'Parando...')
        server.stop()
