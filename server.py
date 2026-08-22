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
import code_analyzer

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
    "version": "1.0.0",
    "conversation_id": None
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

def resolve_file_path(target_file, cwd):
    expanded = os.path.expanduser(target_file)
    if os.path.isabs(expanded):
        return expanded
    c1 = os.path.abspath(os.path.join(cwd, expanded))
    if os.path.exists(c1):
        return c1
    c2 = os.path.abspath(os.path.join(BASE_DIR, expanded))
    if os.path.exists(c2):
        return c2
    return c1

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

def ensure_storage_symlinks():
    storage_base = os.path.expanduser("~/storage")
    os.makedirs(storage_base, exist_ok=True)
    mapping = {
        "shared": "/storage/emulated/0",
        "downloads": "/storage/emulated/0/Download",
        "dcim": "/storage/emulated/0/DCIM",
        "pictures": "/storage/emulated/0/Pictures",
        "music": "/storage/emulated/0/Music",
        "movies": "/storage/emulated/0/Movies"
    }
    for name, target in mapping.items():
        link_path = os.path.join(storage_base, name)
        if not os.path.exists(link_path) and not os.path.islink(link_path):
            try:
                os.symlink(target, link_path)
            except Exception:
                pass

def get_termux_storage_status():
    storage_base = os.path.expanduser("~/storage")
    exists = os.path.exists(storage_base) and os.path.isdir(storage_base)
    folders = {}
    known_targets = ["downloads", "dcim", "pictures", "shared", "movies", "music"]
    if exists:
        for name in known_targets:
            p = os.path.join(storage_base, name)
            is_valid = os.path.exists(p)
            readable = False
            item_count = 0
            if is_valid:
                try:
                    item_count = len(os.listdir(p))
                    readable = True
                except Exception:
                    readable = False
            folders[name] = {
                "path": p,
                "exists": is_valid,
                "readable": readable,
                "items": item_count
            }
    return {
        "storage_dir": storage_base,
        "exists": exists,
        "folders": folders,
        "has_downloads": folders.get("downloads", {}).get("readable", False)
    }

def run_termux_setup_storage():
    out = ""
    try:
        proc = subprocess.run("echo y | termux-setup-storage", shell=True, capture_output=True, text=True, timeout=10)
        out = (proc.stdout + "\n" + proc.stderr).strip()
    except Exception as e:
        out = str(e)
    
    ensure_storage_symlinks()
    status = get_termux_storage_status()
    return {
        "success": status["exists"],
        "output": out,
        "status": status,
        "message": "Termux Storage wurde eingerichtet. Falls Android nach Zugriffsberechtigungen fragt, bitte auf 'Zulassen' tippen."
    }

def execute_shell_command(cmd, cwd):
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=45
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
            "stderr": "Command timed out after 45s",
            "duration": ">45s"
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "duration": "0s"
        }

def execute_agy_agent(prompt, cwd, conversation_id=None, images=None):
    """
    Executes the prompt using the official Antigravity CLI (agy) in print mode.
    Maintains conversation session if conversation_id is provided.
    """
    augmented_prompt = prompt
    if images:
        img_paths = []
        for img_url in images:
            filename = os.path.basename(img_url)
            full_path = os.path.join(UPLOADS_DIR, filename)
            if os.path.exists(full_path):
                img_paths.append(full_path)
        if img_paths:
            augmented_prompt += f"\n\n[Hinweis: Der Benutzer hat folgende Bilddatei(en) auf dem Gerät hochgeladen: {', '.join(img_paths)}]"

    cmd = ["agy", "--dangerously-skip-permissions", "--output-format", "json"]
    if conversation_id:
        cmd.extend(["--conversation", conversation_id])
    
    cmd.extend(["--print", augmented_prompt])

    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=240
        )
        elapsed = round(time.time() - start_time, 2)

        if proc.returncode == 0 and proc.stdout.strip():
            try:
                data = json.loads(proc.stdout.strip())
                response_text = data.get("response", "").strip()
                new_conv_id = data.get("conversation_id", conversation_id)
                usage = data.get("usage", {})
                return {
                    "success": True,
                    "content": response_text or "(Keine Textausgabe)",
                    "conversation_id": new_conv_id,
                    "duration": f"{elapsed}s",
                    "usage": usage,
                    "metadata": {
                        "agent": "Antigravity CLI",
                        "conversation_id": new_conv_id,
                        "duration": f"{elapsed}s",
                        "tokens": usage.get("total_tokens", 0)
                    }
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "content": proc.stdout.strip(),
                    "conversation_id": conversation_id,
                    "duration": f"{elapsed}s",
                    "metadata": {"agent": "Antigravity CLI", "duration": f"{elapsed}s"}
                }
        else:
            err_msg = proc.stderr.strip() or proc.stdout.strip() or "Unbekannter Fehler bei der Ausführung"
            return {
                "success": False,
                "content": f"> [!CAUTION]\n> **Antigravity CLI Fehler (Code {proc.returncode}):**\n\n```text\n{err_msg}\n```",
                "conversation_id": conversation_id,
                "duration": f"{elapsed}s",
                "metadata": {"error": True, "code": proc.returncode}
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "content": "> [!CAUTION]\n> **Timeout:** Die KI-Antwort hat das Zeitlimit von 240 Sekunden überschritten.",
            "conversation_id": conversation_id,
            "duration": ">240s",
            "metadata": {"timeout": True}
        }
    except Exception as e:
        return {
            "success": False,
            "content": f"> [!CAUTION]\n> **Systemfehler beim Starten von `agy`:**\n\n```text\n{str(e)}\n```",
            "conversation_id": conversation_id,
            "duration": "0s",
            "metadata": {"error": True}
        }

class AntigravityHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, format, *args):
        try:
            msg = format % args if args else format
            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        except Exception:
            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {format}\n")

    def send_json_response(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            self.wfile.write(body)
            self.wfile.flush()
        except Exception:
            pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        try:
            self._handle_get()
        except Exception as e:
            try:
                self.send_json_response({"error": str(e)}, 500)
            except Exception:
                pass

    def _handle_get(self):
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
                conv_id = current_state.get("conversation_id")
                uptime = round(time.time() - current_state["connected_since"])

            with get_db() as conn:
                count = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]

            return self.send_json_response({
                "status": "online",
                "cwd": cwd,
                "model": model,
                "agent_mode": agent_mode,
                "conversation_id": conv_id,
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

        elif path == "/api/storage/status":
            status = get_termux_storage_status()
            return self.send_json_response(status)

        elif path == "/api/file/download":
            query = urllib.parse.parse_qs(parsed.query)
            target_file = query.get("path", [""])[0]
            if not target_file:
                return self.send_json_response({"error": "Path required"}, 400)
            with state_lock:
                cwd = current_state["cwd"]
            expanded = resolve_file_path(target_file, cwd)
            if not os.path.exists(expanded) or os.path.isdir(expanded):
                return self.send_json_response({"error": f"Datei '{target_file}' nicht gefunden"}, 404)
            
            filename = os.path.basename(expanded)
            content_type, _ = mimetypes.guess_type(expanded)
            if not content_type:
                content_type = "application/octet-stream"
            
            try:
                stat = os.stat(expanded)
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(stat.st_size))
                self.send_header("Content-Disposition", f'attachment; filename="{urllib.parse.quote(filename)}"')
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                with open(expanded, "rb") as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
                return
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        elif path == "/api/files":
            query = urllib.parse.parse_qs(parsed.query)
            target_dir = query.get("path", [current_state["cwd"]])[0]
            target_dir = os.path.expanduser(target_dir)
            if not os.path.isabs(target_dir):
                target_dir = os.path.abspath(os.path.join(current_state["cwd"], target_dir))
            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                target_dir = current_state["cwd"]

            items = []
            try:
                parent = os.path.dirname(os.path.abspath(target_dir))
                for entry in sorted(os.scandir(target_dir), key=lambda e: (not e.is_dir(), e.name.lower())):
                    try:
                        stat = entry.stat()
                        is_directory = entry.is_dir()
                        items.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": is_directory,
                            "size": stat.st_size if not is_directory else None,
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

        elif path == "/api/file/read":
            query = urllib.parse.parse_qs(parsed.query)
            target_file = query.get("path", [""])[0]
            if not target_file:
                return self.send_json_response({"error": "Path required"}, 400)
            with state_lock:
                cwd = current_state["cwd"]
            expanded = resolve_file_path(target_file, cwd)
            if not os.path.exists(expanded) or os.path.isdir(expanded):
                return self.send_json_response({"error": f"Datei '{target_file}' nicht gefunden"}, 404)
            try:
                stat = os.stat(expanded)
                with open(expanded, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(1000000)
                return self.send_json_response({
                    "success": True,
                    "filename": os.path.basename(expanded),
                    "path": expanded,
                    "size": stat.st_size,
                    "is_py": expanded.endswith(".py"),
                    "content": content
                })
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        elif path == "/api/analyze":
            query = urllib.parse.parse_qs(parsed.query)
            target_file = query.get("path", [""])[0]
            if not target_file:
                return self.send_json_response({"error": "Path required"}, 400)
            with state_lock:
                cwd = current_state["cwd"]
            expanded = resolve_file_path(target_file, cwd)
            if not os.path.exists(expanded):
                return self.send_json_response({"error": f"Datei '{target_file}' nicht gefunden"}, 404)
            try:
                res = code_analyzer.analyze_file(expanded)
                return self.send_json_response(res)
            except Exception as e:
                return self.send_json_response({"success": False, "error": str(e)}, 500)

        elif path == "/api/stream":
            self.handle_sse()
            return

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        try:
            self._handle_post()
        except Exception as e:
            try:
                self.send_json_response({"error": str(e)}, 500)
            except Exception:
                pass

    def _handle_post(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        if path == "/api/setup-storage":
            try:
                res = run_termux_setup_storage()
                return self.send_json_response(res)
            except Exception as e:
                return self.send_json_response({"error": str(e)}, 500)

        elif path == "/api/cd":
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

        elif path == "/api/file/save":
            try:
                data = json.loads(body_bytes.decode("utf-8"))
                target = data.get("path", "").strip()
                content = data.get("content", "")
                if not target:
                    return self.send_json_response({"error": "Path required"}, 400)
                with state_lock:
                    cwd = current_state["cwd"]
                expanded = resolve_file_path(target, cwd)
                os.makedirs(os.path.dirname(expanded), exist_ok=True)
                with open(expanded, "w", encoding="utf-8") as f:
                    f.write(content)
                stat = os.stat(expanded)
                return self.send_json_response({
                    "success": True,
                    "path": expanded,
                    "size": stat.st_size,
                    "message": f"Datei '{os.path.basename(expanded)}' erfolgreich gespeichert ({stat.st_size} Bytes)"
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
            with state_lock:
                current_state["conversation_id"] = None
            return self.send_json_response({"success": True, "message": "History cleared and session reset"})
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
        with state_lock:
            cwd = current_state["cwd"]
            conv_id = current_state.get("conversation_id")

        # 1. Quick local Slash Commands
        if raw.startswith("/"):
            parts = raw.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == "/help":
                return {
                    "content": (
                        "### ⚡ Antigravity KI & Dashboard Hilfe\n\n"
                        "Das Dashboard ist direkt mit der **Antigravity KI-Engine** (`agy`) verbunden.\n\n"
                        "| Befehl / Eingabe | Beschreibung |\n"
                        "| :--- | :--- |\n"
                        "| *Jeder Freitext-Prompt* | Wird direkt von der Antigravity KI (Gemini 3.7) beantwortet & ausgeführt |\n"
                        "| `!<befehl>` oder `/run <cmd>` | Führt einen Shell-Befehl direkt in Termux aus |\n"
                        "| `/setup-storage` | Richtet Termux Storage ein (`termux-setup-storage`) & verknüpft Downloads |\n"
                        "| `/storage [ordner]` | Zeigt Speicherordner oder wechselt direkt (z. B. `/storage downloads`) |\n"
                        "| `/cd <pfad>` | Wechselt das Arbeitsverzeichnis |\n"
                        "| `/pwd` | Zeigt den aktuellen Pfad an |\n"
                        "| `/ls` | Listet Dateien im aktuellen Pfad auf |\n"
                        "| `/status` | Zeigt System- & Dashboard-Statusdetails |\n"
                        "| `/clear` | Leert den Chatverlauf & startet neue KI-Session |\n\n"
                        "> [!TIP]\n"
                        "> Klicke oben auf **📥 /storage downloads**, um sofort auf deinen Android Download-Ordner zuzugreifen!"
                    ),
                    "metadata": {"type": "command_output", "cmd": "/help"}
                }

            elif cmd == "/setup-storage":
                res = run_termux_setup_storage()
                folders = res["status"]["folders"]
                dl_status = "✅ Bereit" if folders.get("downloads", {}).get("readable") else "⚠️ Nicht bereit"
                dcim_status = "✅ Bereit" if folders.get("dcim", {}).get("readable") else "⚠️ Nicht bereit"
                shared_status = "✅ Bereit" if folders.get("shared", {}).get("readable") else "⚠️ Nicht bereit"
                
                content = (
                    "### 📱 Termux Storage Setup\n\n"
                    f"{res['message']}\n\n"
                    "| Speicherbereich | Pfad | Status | Elemente |\n"
                    "| :--- | :--- | :--- | :--- |\n"
                    f"| 📥 **Downloads** | `~/storage/downloads` | {dl_status} | {folders.get('downloads', {}).get('items', 0)} Dateien |\n"
                    f"| 📷 **DCIM / Kamera** | `~/storage/dcim` | {dcim_status} | {folders.get('dcim', {}).get('items', 0)} Dateien |\n"
                    f"| 🖼️ **Bilder** | `~/storage/pictures` | {'✅ Bereit' if folders.get('pictures', {}).get('readable') else '⚠️ Nicht bereit'} | {folders.get('pictures', {}).get('items', 0)} Dateien |\n"
                    f"| 📱 **Shared Storage** | `~/storage/shared` | {shared_status} | {folders.get('shared', {}).get('items', 0)} Dateien |\n\n"
                    "> [!TIP]\n"
                    "> Nutze `/storage downloads` oder klicke oben auf **📥 /storage downloads**, um direkt in deinen Download-Ordner zu wechseln!"
                )
                return {
                    "content": content,
                    "metadata": {"type": "storage_setup", "success": res["success"]}
                }

            elif cmd == "/storage":
                status = get_termux_storage_status()
                folders = status["folders"]
                
                if arg:
                    target_key = arg.lower().strip()
                    if target_key in ["dl", "download", "downloads"]:
                        target_dir = os.path.expanduser("~/storage/downloads")
                    elif target_key in ["dcim", "camera", "kamera", "fotos"]:
                        target_dir = os.path.expanduser("~/storage/dcim")
                    elif target_key in ["pic", "pics", "pictures", "bilder"]:
                        target_dir = os.path.expanduser("~/storage/pictures")
                    elif target_key in ["shared", "sdcard", "intern"]:
                        target_dir = os.path.expanduser("~/storage/shared")
                    else:
                        target_dir = os.path.expanduser(f"~/storage/{target_key}")

                    if os.path.exists(target_dir) and os.path.isdir(target_dir):
                        with state_lock:
                            current_state["cwd"] = os.path.abspath(target_dir)
                        ls_res = execute_shell_command("ls -lah", target_dir)
                        return {
                            "content": (
                                f"> [!NOTE]\n> Arbeitsverzeichnis gewechselt zu: `{target_dir}`\n\n"
                                f"### 📂 Dateien in `{os.path.basename(target_dir)}`:\n```bash\n{ls_res['stdout'] or ls_res['stderr']}\n```"
                            ),
                            "metadata": {"action": "cd", "new_cwd": target_dir}
                        }
                    else:
                        return {
                            "content": f"> [!CAUTION]\n> Speicherordner `{target_dir}` ist nicht verfügbar. Bitte führe `/setup-storage` aus."
                        }

                content = (
                    "### 📱 Termux Storage Übersicht\n\n"
                    "Folgende Android-Speicherordner sind verknüpft:\n\n"
                    f"- 📥 **Downloads:** `~/storage/downloads` ({folders.get('downloads', {}).get('items', 0)} Elemente) — Befehl: `/storage downloads`\n"
                    f"- 📷 **DCIM / Kamera:** `~/storage/dcim` ({folders.get('dcim', {}).get('items', 0)} Elemente) — Befehl: `/storage dcim`\n"
                    f"- 🖼️ **Bilder:** `~/storage/pictures` ({folders.get('pictures', {}).get('items', 0)} Elemente) — Befehl: `/storage pictures`\n"
                    f"- 📱 **Shared Storage:** `~/storage/shared` ({folders.get('shared', {}).get('items', 0)} Elemente) — Befehl: `/storage shared`\n\n"
                    "> [!TIP]\n"
                    "> Du kannst auch das Ordner-Icon **📁** in der Leiste oben antippen, um den Download-Ordner grafisch zu durchsuchen und Dateien herunterzuladen!"
                )
                return {
                    "content": content,
                    "metadata": {"type": "storage_info"}
                }

            elif cmd == "/status":
                ips = get_local_ips()
                ip_list = ", ".join(f"`{ip}`" for ip in ips)
                return {
                    "content": (
                        "### 📊 System- und Dashboard-Status\n\n"
                        f"- **KI-Engine:** `Antigravity CLI Agent (Gemini 3.7)`\n"
                        f"- **Arbeitsverzeichnis (`cwd`):** `{cwd}`\n"
                        f"- **Aktive Session ID:** `{conv_id or 'Neu / Noch nicht initialisiert'}`\n"
                        f"- **Betriebssystem:** Linux / Android Termux\n"
                        f"- **Dashboard-IPs:** {ip_list}\n"
                        f"- **Port:** `{PORT}`\n"
                        f"- **Server-Uhrzeit:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
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

            elif cmd == "/analyze":
                if not arg:
                    return {"content": "> [!WARNING]\n> Bitte gib eine Python-Datei an: `/analyze <datei.py>`"}
                expanded = resolve_file_path(arg, cwd)
                if not os.path.exists(expanded):
                    return {"content": f"> [!CAUTION]\n> Datei nicht gefunden: `{arg}`"}
                res = code_analyzer.analyze_file(expanded)
                if not res.get("success"):
                    return {"content": f"> [!CAUTION]\n> **Analysefehler:** {res.get('error')}"}

                stats = res.get("stats", {})
                fn_list = "\n".join([f"- `def {f['name']}({', '.join(f['args'])})` (Zeile {f['lineno']})" for f in res.get("functions", [])]) or "_Keine Funktionen_"
                cls_list = "\n".join([f"- `class {c['name']}` ({len(c['methods'])} Methoden, Zeile {c['lineno']})" for c in res.get("classes", [])]) or "_Keine Klassen_"
                imp_list = ", ".join([f"`{i.get('module') or i.get('name')}`" for i in res.get("imports", [])]) or "_Keine_"

                content = (
                    f"### 🔬 Code-Analyse: `{res['filename']}`\n\n"
                    f"**Statistik:** `{stats.get('total_lines')} Zeilen` (`{stats.get('code_lines')} Code`, `{stats.get('comment_lines')} Kommentare`)\n\n"
                    f"#### 🌐 Imports ({stats.get('imports_count')}):\n{imp_list}\n\n"
                    f"#### 📦 Klassen ({stats.get('classes_count')}):\n{cls_list}\n\n"
                    f"#### ⚙️ Funktionen ({stats.get('functions_count')}):\n{fn_list}\n\n"
                    f"#### 📊 Ablaufdiagramm:\n```mermaid\n{res.get('mermaid')}\n```"
                )
                return {"content": content, "metadata": {"type": "code_analysis", "file": res["filename"]}}

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

        # 2. Direct shell command shorthand with '!'
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

        # 3. Live AI Agent execution via Antigravity CLI
        agent_res = execute_agy_agent(raw, cwd, conversation_id=conv_id, images=images)
        if agent_res.get("conversation_id"):
            with state_lock:
                current_state["conversation_id"] = agent_res["conversation_id"]

        return {
            "content": agent_res["content"],
            "images": [],
            "metadata": agent_res.get("metadata", {})
        }

class AntigravityServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server(port=PORT):
    server_address = ("0.0.0.0", port)
    AntigravityServer.allow_reuse_address = True
    httpd = AntigravityServer(server_address, AntigravityHandler)
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
