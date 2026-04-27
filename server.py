import os, json, re, subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LIST_FILE = os.path.join(BASE_DIR, 'list.txt')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')

def translate_status(line):
    if "does not pass filter" in line or "is_live" in line: return "📡 等待下播..."
    if "already been recorded" in line: return "✅ 已在存档中"
    if "|" in line and "%" in line:
        parts = line.split('|')
        return f"🚀 正在下载: {parts[0].strip()}"
    if "Downloading" in line: return "📡 获取数据流..."
    if "Merging" in line: return "📦 封装视频中..."
    if "Finished" in line: return "🔍 任务完成"
    return "🔍 扫描中..."

class MonitorHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return # 静默日志

    def do_POST(self):
        # 1. 处理手动补录
        if self.path == '/api/manual_download':
            content_length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            video_url = data.get('url')
            if video_url:
                # 注入终极防漏参数
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

        # 2. 修改 list.txt (同步侧边栏操作)
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
                            # 使用二进制读取最后 1KB，防止编码错误和文件锁
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
        elif self.path.startswith('/api/log/'):
            name = self.path.split('/')[-1]
            log_path = os.path.join(LOG_DIR, f"{name}.log")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            if os.path.exists(log_path):
                with open(log_path, 'rb') as f:
                    f.seek(0, 2)
                    f.seek(max(0, f.tell() - 3000))
                    self.wfile.write(f.read().decode('gbk', errors='ignore').encode('utf-8'))
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
    print(f"Server started at http://localhost:38848")
    HTTPServer(('0.0.0.0', 38848), MonitorHandler).serve_forever()