import os, json, re, subprocess
from urllib.parse import unquote
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LIST_FILE = os.path.join(BASE_DIR, 'list.txt')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')

def translate_status(line):
    if "does not pass filter" in line or "is_live" in line: return "📡 正在直播 (等待下播合成)"
    if "already been recorded" in line: return "✅ 已存在完整录像存档"
    if "|" in line and "%" in line:
        parts = line.split('|')
        return f"🚀 正在高速下载: {parts[0].strip()}"
    if "Downloading" in line: return "📡 正在解析视频流数据..."
    if "Merging" in line: return "📦 正在封装 MP4 文件..."
    if "Finished" in line: return "🔍 录制任务圆满完成"
    return "🔍 深度扫描比对中..."

class MonitorHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return

    def do_POST(self):
        if self.path == '/api/manual_download':
            content_length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            video_url = data.get('url')
            if video_url:
                cmd = [
                    "yt-dlp", "--proxy", "http://127.0.0.1:7890",
                    "--retries", "infinite", "--fragment-retries", "infinite",
                    "--abort-on-unavailable-fragment", "--fixup", "force",
                    "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format", "mp4", "--download-archive", "archive.txt",
                    "-o", "Downloads/Manual/[%(upload_date)s] %(title)s.%(ext)s",
                    video_url
                ]
                subprocess.Popen(cmd, shell=False)
                self._send_json({"status": "ok"})

        elif self.path == '/api/update_list':
            content_length = int(self.headers['Content-Length'])
            new_list = json.loads(self.rfile.read(content_length).decode('utf-8'))
            with open(LIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_list))
            self._send_json({"status": "ok"})

    def do_GET(self):
        if self.path == '/':
            self._send_html(INDEX_FILE)
        elif self.path == '/api/status':
            status_list = []
            if os.path.exists(LOG_DIR):
                for f_name in os.listdir(LOG_DIR):
                    if f_name.endswith('.log'):
                        try:
                            f_path = os.path.join(LOG_DIR, f_name)
                            with open(f_path, 'rb') as f:
                                f.seek(0, 2)
                                f.seek(max(0, f.tell() - 1024))
                                raw = f.read().decode('gbk', errors='ignore')
                                lines = [l.strip() for l in raw.splitlines() if l.strip()]
                                last = lines[-1] if lines else ""
                                status_list.append({
                                    "id": f_name.replace('.log', ''),
                                    "status": translate_status(last),
                                    "raw": last
                                })
                        except: pass
            self._send_json(status_list)
        elif self.path == '/api/list':
            urls = []
            if os.path.exists(LIST_FILE):
                with open(LIST_FILE, 'r', encoding='utf-8') as f:
                    urls = [l.strip() for l in f if l.strip()]
            self._send_json(urls)
        
        # --- 核心修复区：双重判定日志文件名 ---
        elif self.path.startswith('/api/log/'):
            raw_name = self.path.split('/')[-1]
            decoded_name = unquote(raw_name) 
            
            # 兼容处理：检查是否存在编码名称的文件，或解码名称的文件
            path_raw = os.path.join(LOG_DIR, f"{raw_name}.log")
            path_decoded = os.path.join(LOG_DIR, f"{decoded_name}.log")
            log_path = path_raw if os.path.exists(path_raw) else path_decoded

            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            if os.path.exists(log_path):
                with open(log_path, 'rb') as f:
                    f.seek(0, 2)
                    f.seek(max(0, f.tell() - 3000))
                    self.wfile.write(f.read().decode('gbk', errors='ignore').encode('utf-8'))
            else:
                self.wfile.write("[系统提示] 等待产生日志记录...".encode('utf-8'))
        else:
            super().do_GET()

    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_html(self, path):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        with open(path, 'r', encoding='utf-8') as f:
            self.wfile.write(f.read().encode('utf-8'))

if __name__ == '__main__':
    for d in ["logs", "Downloads/Manual"]:
        if not os.path.exists(d): os.makedirs(d)
    print(f"=======================================")
    print(f" Server started at http://localhost:38848")
    print(f"=======================================")
    HTTPServer(('0.0.0.0', 38848), MonitorHandler).serve_forever()