import os, json, subprocess, time, signal, sys, re, threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

def load_config():
    default = {
        "yt_dlp": {
            "proxy": "http://127.0.0.1:7890",
            "retries": "infinite", "fragment_retries": "infinite",
            "retry_sleep": 10, "extractor_retries": 10,
            "concurrent_fragments": 4,
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_format": "mp4", "playlist_items": "1-5",
            "match_filter": "live_status = was_live"
        },
        "paths": {"downloads": "Downloads", "logs": "logs", "archive": "archive.txt", "list_file": "list.txt"},
        "polling": {"interval_seconds": 300, "max_log_size_bytes": 5242880}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            cfg = json.load(open(CONFIG_FILE, encoding="utf-8"))
            for k, v in default.items():
                cfg.setdefault(k, v)
                if isinstance(v, dict):
                    for sk, sv in v.items():
                        cfg[k].setdefault(sk, sv)
            return cfg
        except Exception:
            pass
    return default

CONFIG = load_config()
YT = CONFIG["yt_dlp"]
PATHS = CONFIG["paths"]
POLL_SECONDS = CONFIG["polling"]["interval_seconds"]
LOG_DIR = os.path.join(BASE_DIR, PATHS["logs"])
LIST_FILE = os.path.join(BASE_DIR, PATHS["list_file"])
ARCHIVE = os.path.join(BASE_DIR, PATHS["archive"])

os.makedirs(LOG_DIR, exist_ok=True)

# Create channel folders on startup
for url in read_list():
    name = extract_name(url)
    out_dir = os.path.join(BASE_DIR, PATHS["downloads"], name)
    os.makedirs(out_dir, exist_ok=True)
    print(f"  Folder: {name}/")
active_processes = {}

def read_list():
    if os.path.exists(LIST_FILE):
        with open(LIST_FILE, encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip()]
    return []

def extract_name(url):
    m = re.search(r"@([^/\\?]+)", url)
    raw = m.group(1) if m else (url.rsplit("/", 1)[-1] if "/" in url else "unknown")
    return urllib.parse.unquote(raw)

def pid_file(name):
    return os.path.join(LOG_DIR, f"{name}.pid")

def is_running(name):
    pf = pid_file(name)
    if not os.path.exists(pf):
        return False
    try:
        with open(pf) as f:
            pid = int(f.read().strip())
        if sys.platform == "win32":
            r = subprocess.run(["tasklist", "/fi", f"PID eq {pid}", "/fo", "csv"],
                               capture_output=True, text=True, timeout=5)
            if str(pid) in r.stdout:
                return True
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        pass
    try:
        os.remove(pf)
    except Exception:
        pass
    return False

def start_download(name, url):
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    pf = pid_file(name)
    out_dir = os.path.join(BASE_DIR, PATHS["downloads"], name)
    os.makedirs(out_dir, exist_ok=True)
    out_tpl = os.path.join(out_dir, "[%%(upload_date)s] %%(title)s.%%(ext)s")

    cmd = [
        "yt-dlp",
        "--proxy", YT["proxy"],
        "--retries", str(YT["retries"]),
        "--fragment-retries", str(YT["fragment_retries"]),
        "--retry-sleep", str(YT.get("retry_sleep", 10)),
        "--extractor-retries", str(YT["extractor_retries"]),
        "--abort-on-unavailable-fragment",
        "--concurrent-fragments", str(YT["concurrent_fragments"]),
        "--fixup", "force",
        "--embed-metadata",
        "-f", YT["format"],
        "--merge-output-format", YT["merge_format"],
        "--download-archive", ARCHIVE,
        "--playlist-items", str(YT.get("playlist_items", "1-5")),
        "--match-filter", YT.get("match_filter", "live_status = was_live"),
        "--newline",
        "-o", out_tpl,
        url
    ]

    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW

    with open(log_file, "w", encoding="utf-8") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, creationflags=flags)

    try:
        with open(pf, "w") as f:
            f.write(str(proc.pid))
    except Exception:
        pass

    print(f"[+] 已启动: {name} (PID: {proc.pid})")

    def cleanup():
        proc.wait()
        try:
            if os.path.exists(pf):
                with open(pf) as f:
                    if f.read().strip() == str(proc.pid):
                        os.remove(pf)
        except Exception:
            pass
        active_processes.pop(name, None)
        print(f"[-] 已完成: {name}")

    threading.Thread(target=cleanup, daemon=True).start()
    return proc

def main():
    print("=" * 40)
    print(" YT-DLP Worker (Python 调度)")
    print(f" 轮询间隔: {POLL_SECONDS}s")
    print("=" * 40)

    while True:
        urls = read_list()
        if not urls:
            print(f"[!] list.txt 为空，等待中...")
        else:
            for url in urls:
                name = extract_name(url)
                if name in active_processes:
                    p = active_processes[name]
                    if p.poll() is not None:
                        del active_processes[name]
                    else:
                        continue
                if is_running(name):
                    print(f"[=] {name} 运行中，跳过")
                    continue
                print(f"[+] 空闲频道: {name}")
                try:
                    start_download(name, url)
                except FileNotFoundError:
                    print("[!] 找不到 yt-dlp.exe，请确认已安装")
                    time.sleep(60)
                except Exception as e:
                    print(f"[!] 启动失败 {name}: {e}")
        time.sleep(POLL_SECONDS)

if __name__ == "__main__":
    write_own_pid()
    try:
        main()
    except KeyboardInterrupt:
        print("\n[系统] 正在退出...")
        for name, p in list(active_processes.items()):
            if p.poll() is None:
                print(f"  终止: {name}")
                p.terminate()