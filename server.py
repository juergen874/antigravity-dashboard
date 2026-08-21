#!/data/data/com.termux/files/usr/bin/env python3
"""
Antigravity CLI - Lightweight Mobile Web Dashboard Server
Zero-dependency Python 3 Backend using standard library http.server & sqlite3.
"""

import os
import sys
import json
import time
import uuid
import base64
import sqlite3
import socket
import mimetypes
import subprocess
import urllib.parse
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Lock
from datetime import datetime

PORT = int(os.environ.get("PORT", 8080))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "history.db")

# Ensure directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# State management
current_state = {
    "cwd": os.path.expanduser("~"),
    "model": "Gemini 3.7 Flash",
    "agent_mode": "Autonomous Code Agent",
    "connected_since": time.time(),
    "version": "1.0.0"
}
state_lock = Lock()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                images TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

def get_local_ips():
    ips = ["127.0.0.1"]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        if local_ip not in ips:
            ips.append(local_ip)
    except Exception:
        pass
    try:
        res = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=2)
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet ") or "inet " in line:
                parts = line.split()
                idx = parts.index("inet") if "inet" in parts else -1
                if idx != -1 and idx + 1 < len(parts):
                    ip = parts[idx + 1]
                    if ip not in ips and not ip.startswith("127."):
                        ips.append(ip)
    except Exception:
        pass
    return ips

def execute_shell_command(cmd, cwd):
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = round(time.time() - start, 2)
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration": f"{elapsed}s"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out after 30s",
            "duration": ">30s"
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": "0s"
        }

class AntigravityHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Clean logging format
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]} -> {args[2]}\n")

    def send_json_response(self, data, status_code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            return self.serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")

        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = os.path.join(STATIC_DIR, rel_path)
            if not os.path.abspath(file_path).startswith(os.path.abspath(STATIC_DIR)):
                self.send_error(403, "Access denied")
                return
            return self.serve_file(file_path)

        elif path.startswith("/uploads/"):
            rel_path = path[len("/uploads/"):]
            file_path = os.path.join(UPLOADS_DIR, rel_path)
            if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOADS_DIR)):
                self.send_error(403, "Access denied")
                return
            return self.serve_file(file_path)

        elif path == "/api/status":
            with state_lock:
                cwd = current_state["cwd"]
                model = current_state["model"]
                agent_mode = current_state["agent_mode"]
                uptime = round(time.time() - current_state["connected_since"])

            with get_db() as conn:
                count = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]

            return self.send_json_response({
                "status": "online",
                "cwd": cwd,
                "model": model,
                "agent_mode": agent_mode,
                "uptime_seconds": uptime,
                "total_messages": count,
                "platform": "Termux / Linux (ARM64)" if "com.termux" in sys.executable else sys.platform,
                "server_time": datetime.now().isoformat(),
                "ips": get_local_ips()
            })

        elif path == "/api/history":
            with get_db() as conn:
                rows = conn.execute("SELECT * FROM messages ORDER BY created_at ASC").fetchall()
                messages = []
                for r in rows:
                    images = []
                    metadata = {}
                    if r["images"]:
                        try:
                            images = json.loads(r["images"])
                        except Exception:
                            pass
                    if r["metadata"]:
                        try:
                            metadata = json.loads(r["metadata"])
                        except Exception:
                            pass
                    messages.append({
                        "id": r["id"],
                        "role": r["role"],
                        "content": r["content"],
                        "images": images,
                        "metadata": metadata,
                        "created_at": r["created_at"]
                    })
            return self.send_json_response({"messages": messages})

        elif path == "/api/files":
            query = urllib.parse.parse_qs(parsed.query)
            target_dir = query.get("path", [current_state["cwd"]])[0]
            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                target_dir = current_state["cwd"]

            items = []
            try:
                parent = os.path.dirname(os.path.abspath(target_dir))
                for entry in sorted(os.scandir(target_dir), key=lambda e: (not e.is_dir(), e.name.lower())):
                    try:
                        stat = entry.stat()
                        items.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": entry.is_dir(),
                            "size": stat.st_size if not entry.is_dir() else None,
                            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        })
                    except Exception:
                        pass
                return self.send_json_response({
                    "current_path": os.path.abspath(target_dir),
                    "parent_path": parent if parent != target_dir else None,
                    "items": items
                })
            except Exception as e:
                return self.send_json_response({"error": str(e)}, status_code=500)

        elif path == "/api/stream":
            self.handle_sse()
            return

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        if path == "/api/cd":
            try:
                data = json.loads(body_bytes.decode("utf-8"))
                target = data.get("path", "").strip()
                if not target:
                    return self.send_json_response({"error": "Path required"}, 400)
                expanded = os.path.expanduser(target)
                if not os.path.isabs(expanded):
                    expanded = os.path.abspath(os.path.join(current_state["cwd"], expanded))
                if os.path.exists(expanded) and os.path.isdir(expanded):
                    with state_lock:
                        current_state["cwd"] = expanded
                    return self.send_json_response({"success": True, "cwd": expanded})
                else:
                    return self.send_json_response({"error": f"Directory '{target}' not found"}, 404)
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        elif path == "/api/upload":
            try:
                content_type = self.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = json.loads(body_bytes.decode("utf-8"))
                    filename = data.get("filename", "upload.jpg")
                    b64_data = data.get("data", "")
                    if "," in b64_data:
                        b64_data = b64_data.split(",", 1)[1]
                    file_bytes = base64.b64decode(b64_data)
                else:
                    filename = self.headers.get("X-Filename", f"photo_{int(time.time())}.jpg")
                    file_bytes = body_bytes

                unique_name = f"{uuid.uuid4().hex[:12]}_{filename}"
                save_path = os.path.join(UPLOADS_DIR, unique_name)

                with open(save_path, "wb") as f:
                    f.write(file_bytes)

                url = f"/uploads/{unique_name}"
                return self.send_json_response({
                    "success": True,
                    "url": url,
                    "filename": filename,
                    "size": len(file_bytes)
                })
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        elif path == "/api/exec":
            try:
                data = json.loads(body_bytes.decode("utf-8"))
                cmd = data.get("command", "").strip()
                if not cmd:
                    return self.send_json_response({"error": "Command required"}, 400)
                res = execute_shell_command(cmd, current_state["cwd"])
                return self.send_json_response(res)
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        elif path == "/api/chat":
            try:
                data = json.loads(body_bytes.decode("utf-8"))
                user_msg = data.get("message", "").strip()
                images = data.get("images", [])

                if not user_msg and not images:
                    return self.send_json_response({"error": "Empty message"}, 400)

                msg_id = str(uuid.uuid4())
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO messages (id, role, content, images, metadata) VALUES (?, ?, ?, ?, ?)",
                        (msg_id, "user", user_msg, json.dumps(images), json.dumps({"source": "web_dashboard"}))
                    )
                    conn.commit()

                # Process response
                response_data = self.process_agent_response(user_msg, images)

                resp_id = str(uuid.uuid4())
                with get_db() as conn:
                    conn.execute(
                        "INSERT INTO messages (id, role, content, images, metadata) VALUES (?, ?, ?, ?, ?)",
                        (resp_id, "assistant", response_data["content"], json.dumps(response_data.get("images", [])), json.dumps(response_data.get("metadata", {})))
                    )
                    conn.commit()

                return self.send_json_response({
                    "id": resp_id,
                    "role": "assistant",
                    "content": response_data["content"],
                    "images": response_data.get("images", []),
                    "metadata": response_data.get("metadata", {}),
                    "created_at": datetime.now().isoformat()
                })
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/history":
            with get_db() as conn:
                conn.execute("DELETE FROM messages")
                conn.commit()
            return self.send_json_response({"success": True, "message": "History cleared"})
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, file_path, content_type=None):
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, "File not found")
            return
        try:
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"

            stat = os.stat(file_path)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(stat.st_size))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
        except Exception as e:
            sys.stderr.write(f"Error serving {file_path}: {e}\n")

    def handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Send initial connected heartbeat
        try:
            self.wfile.write(b"data: {\"type\": \"connected\", \"message\": \"Antigravity Stream Connected\"}\n\n")
            self.wfile.flush()
            while True:
                time.sleep(15)
                self.wfile.write(f"data: {{\"type\": \"heartbeat\", \"timestamp\": {int(time.time())}}}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def process_agent_response(self, message, images):
        raw = message.strip()
        cwd = current_state["cwd"]

        # Check for Slash Commands
        if raw.startswith("/"):
            parts = raw.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == "/help":
                return {
                    "content": (
                        "### 🚀 Antigravity CLI Slash Commands\n\n"
                        "Hier sind die verfügbaren Befehle im mobilen Dashboard:\n\n"
                        "| Befehl | Beschreibung |\n"
                        "| :--- | :--- |\n"
                        "| `/help` | Zeigt diese Hilfe-Übersicht an |\n"
                        "| `/run <command>` oder `!<command>` | Führt einen Shell-Befehl direkt in Termux aus |\n"
                        "| `/cd <pfad>` | Wechselt das aktive Arbeitsverzeichnis |\n"
                        "| `/pwd` | Zeigt den aktuellen Pfad an |\n"
                        "| `/ls` | Listet Dateien im aktuellen Pfad auf |\n"
                        "| `/status` | Zeigt System- & Dashboard-Statusdetails |\n"
                        "| `/goal <ziel>` | Setzt ein autonomes Ziel mit iterativer Problemlösung |\n"
                        "| `/plan <task>` | Erstellt einen mehrstufigen Implementierungsplan |\n"
                        "| `/clear` | Leert den Chatverlauf |\n\n"
                        "> [!TIP]\n"
                        "> **Tipp:** Du kannst auch Bilder und Fotos anhängen, das Mikrofon für Push-to-Talk Spracheingabe nutzen oder Screenshots per Paste einfügen!"
                    ),
                    "metadata": {"type": "command_output", "cmd": "/help"}
                }

            elif cmd == "/status":
                ips = get_local_ips()
                ip_list = ", ".join(f"`{ip}`" for ip in ips)
                return {
                    "content": (
                        "### 📊 System- und Dashboard-Status\n\n"
                        f"- **Arbeitsverzeichnis (`cwd`):** `{cwd}`\n"
                        f"- **Aktives Modell:** `Gemini 3.7 Flash`\n"
                        f"- **Betriebssystem:** Linux / Android Termux\n"
                        f"- **Dashboard-IPs:** {ip_list}\n"
                        f"- **Port:** `{PORT}`\n"
                        f"- **Server-Uhrzeit:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
                        "> [!NOTE]\n"
                        "> Die Web Speech API und Foto-Uploads sind im Mobilbrowser voll aktiviert."
                    ),
                    "metadata": {"type": "status"}
                }

            elif cmd == "/cd":
                if not arg:
                    return {"content": "> [!WARNING]\n> Bitte gib einen Pfad an: `/cd <pfad>`"}
                expanded = os.path.expanduser(arg)
                if not os.path.isabs(expanded):
                    expanded = os.path.abspath(os.path.join(cwd, expanded))
                if os.path.exists(expanded) and os.path.isdir(expanded):
                    with state_lock:
                        current_state["cwd"] = expanded
                    return {
                        "content": f"> [!NOTE]\n> Arbeitsverzeichnis gewechselt zu: `{expanded}`",
                        "metadata": {"action": "cd", "new_cwd": expanded}
                    }
                else:
                    return {"content": f"> [!CAUTION]\n> Verzeichnis nicht gefunden: `{arg}`"}

            elif cmd == "/pwd":
                return {"content": f"📁 **Aktueller Pfad:** `{cwd}`"}

            elif cmd == "/ls":
                res = execute_shell_command("ls -lah", cwd)
                return {
                    "content": f"### 📂 Dateiliste in `{cwd}`\n```bash\n{res['stdout'] or res['stderr']}\n```",
                    "metadata": {"action": "ls"}
                }

            elif cmd == "/run" or cmd.startswith("/exec"):
                if not arg:
                    return {"content": "> [!WARNING]\n> Bitte gib einen Befehl an: `/run <command>`"}
                res = execute_shell_command(arg, cwd)
                status_icon = "✅" if res["success"] else "❌"
                out = res["stdout"] if res["stdout"] else ""
                err = f"\n[stderr]\n{res['stderr']}" if res["stderr"] else ""
                return {
                    "content": (
                        f"### {status_icon} Befehl: `{arg}`\n"
                        f"- **Exit Code:** `{res['returncode']}` | **Dauer:** `{res['duration']}` | **Pfad:** `{cwd}`\n\n"
                        f"```bash\n{out}{err}\n```"
                    ),
                    "metadata": {"action": "run", "success": res["success"], "code": res["returncode"]}
                }

            elif cmd == "/plan":
                return {
                    "content": (
                        f"### 📋 Implementierungsplan: {arg or 'Aufgabe'}\n\n"
                        "1. **Analyse & Kontext:** Prüfung der Umgebungsanforderungen und betroffenen Dateien in `{cwd}`.\n"
                        "2. **Architektur-Entwurf:** Strukturierung der Module und Schnittstellen.\n"
                        "3. **Schrittweise Umsetzung:** Durchführung der Änderungen mit Tests.\n"
                        "4. **Validierung:** Ausführen der Testläufe und Verifikation im Dashboard.\n\n"
                        "> [!TIP]\n"
                        "> Bestätige mit `/goal` oder sende eine Anweisung, um sofort zu starten."
                    ),
                    "metadata": {"type": "plan"}
                }

            elif cmd == "/goal":
                return {
                    "content": (
                        f"### 🎯 Autonomes Ziel aktiviert: {arg or 'Aufgabe'}\n\n"
                        "> [!IMPORTANT]\n"
                        "> Der Agent arbeitet autonom am Erreichen dieses Ziels und berichtet Zwischenschritte.\n\n"
                        f"- **Fokus:** `{arg}`\n"
                        f"- **Workspace:** `{cwd}`\n"
                        f"- **Status:** Initialisiert & bereit für nächste Instruktionen."
                    ),
                    "metadata": {"type": "goal"}
                }

        # Direct shell command shorthand with '!'
        if raw.startswith("!"):
            cmd_to_run = raw[1:].strip()
            res = execute_shell_command(cmd_to_run, cwd)
            status_icon = "✅" if res["success"] else "❌"
            out = res["stdout"] if res["stdout"] else ""
            err = f"\n[stderr]\n{res['stderr']}" if res["stderr"] else ""
            return {
                "content": (
                    f"### {status_icon} Shell: `{cmd_to_run}`\n"
                    f"- **Exit Code:** `{res['returncode']}` | **Dauer:** `{res['duration']}`\n\n"
                    f"```bash\n{out}{err}\n```"
                ),
                "metadata": {"action": "exec", "success": res["success"]}
            }

        # Handling Image-attached questions
        image_context = ""
        if images:
            image_context = f"\n\n> [!NOTE]\n> *Empfangene Bilder:* {len(images)} Bild(er) angehängt zur visuellen Analyse."

        # Smart assistant contextual responses
        return {
            "content": (
                f"Ich habe deine Nachricht erhalten:\n\n"
                f"> {message}\n\n"
                f"{image_context}\n\n"
                f"**Verfügbare Aktionen in `{cwd}`:**\n"
                f"- Shell-Befehl ausführen: `!<befehl>` oder `/run <befehl>`\n"
                f"- Verzeichnis wechseln: `/cd <pfad>`\n"
                f"- Dateien anzeigen: `/ls`\n"
                f"- Hilfe aufrufen: `/help`\n\n"
                f"Wie kann ich dich bei der Entwicklung oder Konfiguration unterstützen?"
            ),
            "images": [],
            "metadata": {"tokens": len(message.split()) * 2, "model": current_state["model"]}
        }

def run_server(port=PORT):
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, AntigravityHandler)
    ips = get_local_ips()
    print(f"\n=======================================================")
    print(f"🚀 Antigravity Mobile Web Dashboard gestartet!")
    print(f"-------------------------------------------------------")
    print(f"📱 Lokale URL:     http://localhost:{port}")
    for ip in ips:
        if not ip.startswith("127."):
            print(f"🌐 Mobil / WLAN:   http://{ip}:{port}")
    print(f"📁 Workspace Pfad: {current_state['cwd']}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server beendet.")
        httpd.server_close()

if __name__ == "__main__":
    p = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        p = int(sys.argv[1])
    run_server(p)
