import os, json, re, subprocess, signal, sys, threading, time
from datetime import datetime
from urllib.parse import unquote
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# ── 配置加载 ──────────────────────────────────────────────
def load_config():
    default_config = {
        "server": {"host": "0.0.0.0", "port": 38848},
        "yt_dlp": {
            "proxy": "http://127.0.0.1:7890",
            "retries": "infinite",
            "fragment_retries": "infinite",
            "retry_sleep": 10,
            "extractor_retries": 10,
            "concurrent_fragments": 4,
            "max_height": 1080,
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_format": "mp4",
            "playlist_items": "1-5",
            "match_filter": "live_status = was_live"
        },
        "paths": {
            "downloads": "Downloads",
            "manual_downloads": "Downloads/Manual",
            "logs": "logs",
            "archive": "archive.txt",
            "list_file": "list.txt"
        },
        "polling": {
            "interval_seconds": 300,
            "max_log_size_bytes": 5242880
        }
    }
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for key, val in default_config.items():
            if key not in cfg:
                cfg[key] = val
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    cfg[key].setdefault(sub_key, sub_val)
        return cfg
    except Exception:
        print("[警告] 配置文件损坏，使用默认配置")
        return default_config

CONFIG = load_config()

LOG_DIR = os.path.join(BASE_DIR, CONFIG['paths']['logs'])
LIST_FILE = os.path.join(BASE_DIR, CONFIG['paths']['list_file'])
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')
ARCHIVE_FILE = os.path.join(BASE_DIR, CONFIG['paths']['archive'])
MAX_LOG_BYTES = CONFIG['polling']['max_log_size_bytes']

# ── 进程注册表 ────────────────────────────────────────────
process_registry = {}
registry_lock = threading.Lock()

# ── 文件锁 ────────────────────────────────────────────────
file_lock = threading.Lock()
server_start_time = time.time()

# ── 工具函数 ──────────────────────────────────────────────
def rotate_log(log_path):
    if os.path.exists(log_path) and os.path.getsize(log_path) > MAX_LOG_BYTES:
        base, ext = os.path.splitext(log_path)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        try:
            os.rename(log_path, f"{base}_{ts}{ext}")
        except OSError:
            pass

def translate_status(line):
    if "ERROR" in line:
        return "\u274c \u4e0b\u8f7d\u51fa\u9519\uff0c\u6b63\u5728\u91cd\u8bd5"
    if "does not pass filter" in line or "is_live" in line:
        return "\U0001f534 \u76f4\u64ad\u4e2d (\u7ed3\u675f\u540e\u81ea\u52a8\u4e0b\u8f7d)"
    if "already been recorded" in line:
        return "\u2705 \u5df2\u4e0b\u8f7d\u8fc7\uff0c\u8df3\u8fc7"
    if "|" in line and "%" in line:
        parts = line.split('|')
        return f"\U0001f4e1 \u4e0b\u8f7d\u4e2d: {parts[0].strip()}"
    if "Downloading" in line:
        return "\U0001f503 \u6b63\u5728\u5206\u6790\u89c6\u9891\u6d41..."
    if "Merging" in line:
        return "\U0001f4e6 \u6b63\u5728\u5408\u6210\u89c6\u9891..."
    if "Finished" in line:
        return "\u2705 \u4e0b\u8f7d\u5b8c\u6210"
    return "\U0001f4ad \u7b49\u5f85\u4e2d..."

def build_ytdlp_cmd(url, output_dir, extra_opts=None):
    yt = CONFIG['yt_dlp']
    cmd = [
        "yt-dlp",
        "--proxy", yt['proxy'],
        "--retries", str(yt['retries']),
        "--fragment-retries", str(yt['fragment_retries']),
        "--retry-sleep", str(yt.get('retry_sleep', 10)),
        "--extractor-retries", str(yt['extractor_retries']),
        "--abort-on-unavailable-fragment",
        "--concurrent-fragments", str(yt['concurrent_fragments']),
        "--fixup", "force",
        "--embed-metadata",
        "-f", yt['format'],
        "--merge-output-format", yt['merge_format'],
        "--download-archive", ARCHIVE_FILE,
        "--newline",
    ]
    playlist_items = yt.get('playlist_items')
    if playlist_items:
        cmd.extend(["--playlist-items", str(playlist_items)])
    match_filter = yt.get('match_filter')
    if match_filter:
        cmd.extend(["--match-filter", match_filter])
    if extra_opts:
        cmd.extend(extra_opts)
    cmd.extend(["-o", output_dir, url])
    return cmd

def read_list():
    with file_lock:
        if not os.path.exists(LIST_FILE):
            return []
        with open(LIST_FILE, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f if l.strip()]

def write_list(urls):
    with file_lock:
        with open(LIST_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(urls))

def read_log_tail(log_path, max_bytes=3000):
    try:
        size = os.path.getsize(log_path)
        with open(log_path, 'rb') as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                f.readline()
            return f.read().decode('gbk', errors='ignore')
    except OSError:
        return ""

def get_log_files():
    if not os.path.isdir(LOG_DIR):
        return []
    try:
        return sorted([f for f in os.listdir(LOG_DIR) if f.endswith('.log')])
    except OSError:
        return []

# ── HTTP 处理器 ──────────────────────────────────────────
class MonitorHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    # ── POST ──
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self._send_json({"error": "Invalid request"}, 400)
            return

        handlers = {
            '/api/manual_download': self._manual_download,
            '/api/update_list': self._update_list,
            '/api/kill': self._kill_process,
        }
        handler = handlers.get(self.path)
        if handler:
            handler(data)
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def _manual_download(self, data):
        url = (data.get('url') or '').strip()
        if not url:
            self._send_json({"error": "URL required"}, 400)
            return
        out_dir = os.path.join(BASE_DIR, CONFIG['paths']['manual_downloads'])
        os.makedirs(out_dir, exist_ok=True)
        output_template = os.path.join(out_dir, "[%(upload_date)s] %(title)s.%(ext)s")
        cmd = build_ytdlp_cmd(url, output_template, extra_opts=["--playlist-items", "1"])
        try:
            proc = subprocess.Popen(cmd, shell=False)
            name = f"manual_{int(time.time())}"
            with registry_lock:
                process_registry[name] = {
                    "process": proc, "url": url,
                    "start_time": time.time(), "type": "manual"
                }
            self._send_json({"status": "ok", "name": name})
        except OSError as e:
            self._send_json({"error": f"Failed to start: {e}"}, 500)

    def _update_list(self, data):
        if not isinstance(data, list):
            self._send_json({"error": "Expected array"}, 400)
            return
        write_list(data)
        self._send_json({"status": "ok"})

    def _kill_process(self, data):
        name = data.get('name', '')
        with registry_lock:
            info = process_registry.get(name)
            if not info:
                self._send_json({"error": "Process not found"}, 404)
                return
            proc = info["process"]
            if proc.poll() is None:
                proc.terminate()
                def wait_kill():
                    try:
                        proc.wait(timeout=10)
                        with registry_lock:
                            process_registry.pop(name, None)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                threading.Thread(target=wait_kill, daemon=True).start()
                self._send_json({"status": "ok", "message": f"Terminating {name}"})
            else:
                process_registry.pop(name, None)
                self._send_json({"status": "ok", "message": "Already stopped"})

    # ── GET ──
    def do_GET(self):
        try:
            handlers = {
                '/': lambda: self._send_html(INDEX_FILE),
                '/api/status': self._get_status,
                '/api/list': self._get_list,
                '/api/processes': self._get_processes,
                '/api/health': self._get_health,
            }
            handler = handlers.get(self.path)
            if handler:
                handler()
            elif self.path.startswith('/api/log/'):
                self._get_log()
            else:
                super().do_GET()
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _get_status(self):
        results = []
        running_names = set()
        with registry_lock:
            for name, info in process_registry.items():
                if info["process"].poll() is None:
                    running_names.add(name)

        for f_name in get_log_files():
            try:
                f_path = os.path.join(LOG_DIR, f_name)
                raw = read_log_tail(f_path, max_bytes=1024)
                lines = [l.strip() for l in raw.splitlines() if l.strip()]
                last = lines[-1] if lines else ""
                cname = f_name.replace('.log', '')
                results.append({
                    "id": cname,
                    "status": translate_status(last),
                    "raw": last,
                    "running": cname in running_names
                })
            except Exception:
                continue
        self._send_json(results)

    def _get_list(self):
        self._send_json(read_list())

    def _get_processes(self):
        with registry_lock:
            alive = {}
            for name, info in process_registry.items():
                if info["process"].poll() is None:
                    alive[name] = {
                        "url": info["url"],
                        "start_time": info["start_time"],
                        "type": info.get("type", "unknown"),
                        "elapsed": int(time.time() - info["start_time"]),
                    }
            self._send_json(alive)

    def _get_health(self):
        with registry_lock:
            active = sum(1 for p in process_registry.values() if p["process"].poll() is None)
        self._send_json({
            "status": "healthy",
            "uptime": int(time.time() - server_start_time),
            "active_processes": active,
            "log_files": len(get_log_files()),
            "port": CONFIG['server']['port']
        })

    def _get_log(self):
        raw_name = self.path.split('/')[-1]
        decoded_name = unquote(raw_name)
        path_raw = os.path.join(LOG_DIR, f"{raw_name}.log")
        path_decoded = os.path.join(LOG_DIR, f"{decoded_name}.log")
        log_path = path_raw if os.path.exists(path_raw) else path_decoded

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()

        if os.path.exists(log_path):
            rotate_log(log_path)
            self.wfile.write(read_log_tail(log_path).encode('utf-8'))
        else:
            self.wfile.write("[系统提示] 等待产生日志记录...".encode('utf-8'))

    # ── 工具方法 ──
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _send_html(self, path):
        if not os.path.exists(path):
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        with open(path, 'rb') as f:
            self.wfile.write(f.read())

# ── 后台任务 ──────────────────────────────────────────────
def zombie_cleaner():
    while True:
        time.sleep(120)
        with registry_lock:
            dead = [n for n, i in process_registry.items() if i["process"].poll() is not None]
            for n in dead:
                del process_registry[n]

def graceful_shutdown(*args):
    print("\n[系统] 正在关闭所有任务...")
    with registry_lock:
        for name, info in process_registry.items():
            p = info["process"]
            if p.poll() is None:
                print(f"[系统] 终止: {name}")
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
    print("[系统] 服务器已关闭")
    sys.exit(0)

# ── 入口 ─────────────────────────────────────────────────
if __name__ == '__main__':
    for d in [CONFIG['paths']['logs'], CONFIG['paths']['manual_downloads']]:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

    # 优雅关闭
    if sys.platform != 'win32':
        signal.signal(signal.SIGINT, graceful_shutdown)
        signal.signal(signal.SIGTERM, graceful_shutdown)

    threading.Thread(target=zombie_cleaner, daemon=True).start()

    host, port = CONFIG['server']['host'], CONFIG['server']['port']
    print("=======================================")
    print(f" YT-DLP 监控服务 (优化版)")
    print(f" 地址: http://{host}:{port}")
    print(f" 配置: {CONFIG_FILE}")
    print(f" 日志: {LOG_DIR}")
    print("=======================================")

    try:
        HTTPServer((host, port), MonitorHandler).serve_forever()
    except OSError as e:
        print(f"[错误] 端口 {port} 被占用: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        graceful_shutdown()