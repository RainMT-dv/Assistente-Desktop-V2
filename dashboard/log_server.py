"""Log server for real-time logging dashboards. MUDANÇA 5."""

import logging
import threading
import time
from typing import Any, Dict, Optional

# Silencia logs do Flask/Werkzeug
logging.getLogger('werkzeug').setLevel(logging.ERROR)

try:
    from flask import Flask, render_template_string
    from flask_socketio import SocketIO, emit
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False
    Flask = None  # type: ignore
    SocketIO = None  # type: ignore
    emit = None  # type: ignore


# HTML template for log panels (shared by all categories)
LOG_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ category }} - Log Panel</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: #161b22;
            padding: 15px 20px;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        h1 { color: #58a6ff; font-size: 1.2rem; }
        .description { color: #8b949e; font-size: 0.85rem; }
        .connection-status {
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 0.8rem;
            flex-shrink: 0;
            margin-left: 15px;
        }
        .connected { background: #238636; color: #fff; }
        .disconnected { background: #da3633; color: #fff; }
        .filter-bar {
            display: flex;
            gap: 10px;
            align-items: center;
            padding: 10px 20px;
            background: #161b22;
            border-bottom: 1px solid #30363d;
        }
        .filter-btn {
            padding: 5px 12px;
            border: 1px solid #30363d;
            background: #21262d;
            color: #c9d1d9;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            white-space: nowrap;
        }
        .filter-btn.active { background: #58a6ff; color: #0d1117; }
        .filter-btn:hover { background: #30363d; }
        .stats {
            padding: 10px 20px;
            background: #161b22;
            border-bottom: 1px solid #30363d;
            font-size: 0.85rem;
            color: #8b949e;
        }
        .stats span { margin-right: 20px; }
        .stats .count { color: #58a6ff; font-weight: bold; }
        #logContainer {
            flex: 1;
            overflow-y: auto;
            padding: 10px 20px;
        }
        .log-entry {
            padding: 6px 0;
            border-bottom: 1px solid #21262d;
            font-size: 0.9rem;
            display: flex;
            gap: 10px;
        }
        .timestamp { color: #6e7681; min-width: 85px; }
        .level { min-width: 50px; font-weight: bold; }
        .level-INFO { color: #c9d1d9; }
        .level-WARN { color: #d29922; }
        .level-ERROR { color: #f85149; }
        .level-DEBUG { color: #8b949e; }
        .message { flex: 1; word-break: break-word; }
        .data { color: #58a6ff; font-size: 0.8rem; margin-left: 10px; }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>{{ category }}</h1>
            <div class="description">{{ description }}</div>
        </div>
        <div id="connectionStatus" class="connection-status disconnected">Offline</div>
    </header>

    <div class="filter-bar">
        <button class="filter-btn active" data-level="ALL">TODOS</button>
        <button class="filter-btn" data-level="INFO">INFO</button>
        <button class="filter-btn" data-level="WARN">WARN</button>
        <button class="filter-btn" data-level="ERROR">ERROR</button>
        <button class="filter-btn" data-level="DEBUG">DEBUG</button>
        <button class="filter-btn" onclick="clearLogs()">LIMPAR</button>
    </div>

    <div class="stats">
        <span>Total: <span class="count" id="totalCount">0</span></span>
        <span>INFO: <span class="count" id="infoCount">0</span></span>
        <span>WARN: <span class="count" id="warnCount">0</span></span>
        <span>ERROR: <span class="count" id="errorCount">0</span></span>
        <span>DEBUG: <span class="count" id="debugCount">0</span></span>
    </div>

    <div id="logContainer"></div>

    <script>
        const socket = io();
        const logContainer = document.getElementById('logContainer');
        const connectionStatus = document.getElementById('connectionStatus');
        let currentFilter = 'ALL';
        let logs = [];
        let counts = { INFO: 0, WARN: 0, ERROR: 0, DEBUG: 0 };

        // Connection status
        socket.on('connect', () => {
            connectionStatus.textContent = 'Online';
            connectionStatus.className = 'connection-status connected';
        });

        socket.on('disconnect', () => {
            connectionStatus.textContent = 'Offline';
            connectionStatus.className = 'connection-status disconnected';
        });

        // Log entries
        socket.on('log_entry', (data) => {
            logs.push(data);
            counts[data.level] = (counts[data.level] || 0) + 1;
            updateStats();
            if (currentFilter === 'ALL' || currentFilter === data.level) {
                appendLogEntry(data);
            }
        });

        function appendLogEntry(data) {
            const div = document.createElement('div');
            div.className = 'log-entry';
            div.innerHTML = `
                <span class="timestamp">${data.timestamp}</span>
                <span class="level level-${data.level}">${data.level}</span>
                <span class="message">${escapeHtml(data.message)}</span>
                ${data.data ? '<span class="data">' + escapeHtml(JSON.stringify(data.data)) + '</span>' : ''}
            `;
            logContainer.appendChild(div);
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        function updateStats() {
            document.getElementById('totalCount').textContent = logs.length;
            document.getElementById('infoCount').textContent = counts.INFO || 0;
            document.getElementById('warnCount').textContent = counts.WARN || 0;
            document.getElementById('errorCount').textContent = counts.ERROR || 0;
            document.getElementById('debugCount').textContent = counts.DEBUG || 0;
        }

        function clearLogs() {
            logs = [];
            counts = { INFO: 0, WARN: 0, ERROR: 0, DEBUG: 0 };
            logContainer.innerHTML = '';
            updateStats();
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Filter buttons
        document.querySelectorAll('.filter-btn[data-level]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn[data-level]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentFilter = btn.dataset.level;

                // Re-render logs
                logContainer.innerHTML = '';
                logs.forEach(log => {
                    if (currentFilter === 'ALL' || currentFilter === log.level) {
                        appendLogEntry(log);
                    }
                });
            });
        });
    </script>
</body>
</html>
'''


class LogServer:
    """Independent log server for a specific category. MUDANÇA 5."""

    def __init__(self, category_name: str, port: int, description: str = ""):
        """
        Initialize log server.

        Args:
            category_name: Category name (e.g., "Comunicação AI")
            port: Port number (e.g., 5002)
            description: Description shown in the panel
        """
        if not _FLASK_AVAILABLE:
            raise ImportError("Flask ou Flask-SocketIO não instalados")

        self.category = category_name
        self.port = port
        self.description = description

        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = f"log-server-{port}"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading")

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._entry_count = 0

        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""

        @self.app.route("/")
        def index():
            return render_template_string(
                LOG_PANEL_TEMPLATE,
                category=self.category,
                description=self.description
            )

    def log(self, level: str, message: str, data: Optional[Dict] = None) -> None:
        """
        Log a message.

        Args:
            level: Log level (INFO, WARN, ERROR, DEBUG)
            message: Log message
            data: Optional data dict
        """
        timestamp = time.strftime("%H:%M:%S")
        prefix = f"[{self.category.upper()}]"

        # Console output with colors
        colors = {
            "INFO": "\033[97m",   # White
            "WARN": "\033[93m",   # Yellow
            "ERROR": "\033[91m",  # Red
            "DEBUG": "\033[90m",  # Gray
        }
        reset = "\033[0m"
        color = colors.get(level, "")
        print(f"{color}{prefix} [{level}] {message}{reset}")

        # WebSocket broadcast
        if self._running:
            entry = {
                "timestamp": timestamp,
                "level": level,
                "category": self.category,
                "message": message,
                "data": data,
            }
            try:
                self.socketio.emit("log_entry", entry)
                self._entry_count += 1
            except Exception:
                pass

    def info(self, message: str, data: Optional[Dict] = None) -> None:
        """Log INFO level message."""
        self.log("INFO", message, data)

    def warn(self, message: str, data: Optional[Dict] = None) -> None:
        """Log WARN level message."""
        self.log("WARN", message, data)

    def error(self, message: str, data: Optional[Dict] = None) -> None:
        """Log ERROR level message."""
        self.log("ERROR", message, data)

    def debug(self, message: str, data: Optional[Dict] = None) -> None:
        """Log DEBUG level message."""
        self.log("DEBUG", message, data)

    def start(self) -> None:
        """Start the log server in a daemon thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self.socketio.run,
            args=(self.app,),
            kwargs={"host": "0.0.0.0", "port": self.port, "debug": False, "use_reloader": False},
            daemon=True,
        )
        self._thread.start()
        self.info(f"Log server '{self.category}' iniciado em http://localhost:{self.port}")

    def stop(self) -> None:
        """Stop the log server."""
        self._running = False
        self.info(f"Log server '{self.category}' parado")


if __name__ == "__main__":
    # Test
    server = LogServer("Test", 5002, "Test log server")
    server.start()

    # Simulate logs
    import random
    levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    messages = ["Mensagem de teste", "Algo aconteceu", "Erro detectado", "Debug info"]

    try:
        while True:
            level = random.choice(levels)
            msg = random.choice(messages)
            server.log(level, msg)
            time.sleep(2)
    except KeyboardInterrupt:
        server.stop()
