import os, json, re
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LIST_FILE = os.path.join(BASE_DIR, 'list.txt')

def translate_status(line):
    """把日志里的英文逻辑转换成中文显示"""
    if "does not pass filter" in line: return "🔴 已捕获到直播 (等待直播结束后下载)"
    if "has already been recorded" in line: return "✅ 存档库已存在 (跳过)"
    if "|" in line:
        parts = line.split('|')
        return f"🚀 正在下载录播: {parts[0].strip()} | 速度: {parts[1].strip()}"
    if "Downloading" in line: return "📡 正在获取视频流..."
    if "Merging" in line: return "📦 正在封装 MP4..."
    if "Finished" in line: return "🎉 下载完成！"
    return "🔍 正在监视中..."

class MonitorHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            status_list = []
            if os.path.exists(LOG_DIR):
                for f_name in os.listdir(LOG_DIR):
                    if f_name.endswith('.log'):
                        try:
                            f_path = os.path.join(LOG_DIR, f_name)
                            fd = os.open(f_path, os.O_RDONLY | os.O_BINARY)
                            with os.fdopen(fd, 'rb') as f:
                                f.seek(0, 2)
                                f.seek(max(0, f.tell() - 1024))
                                raw = f.read().decode('gbk', errors='ignore')
                                lines = [l.strip() for l in raw.splitlines() if l.strip()]
                                last_line = lines[-1] if lines else ""
                                status_list.append({
                                    "id": f_name.replace('.log', ''),
                                    "status": translate_status(last_line),
                                    "raw": last_line
                                })
                        except: pass
            self.wfile.write(json.dumps(status_list).encode('utf-8'))
        
        elif self.path.startswith('/api/log/'):
            name = self.path.split('/')[-1]
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            log_path = os.path.join(LOG_DIR, f"{name}.log")
            if os.path.exists(log_path):
                fd = os.open(log_path, os.O_RDONLY | os.O_BINARY)
                with os.fdopen(fd, 'rb') as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 3000))
                    # 读出来是 GBK，转成网页通用的 UTF-8 发送
                    content = f.read().decode('gbk', errors='ignore')
                    self.wfile.write(content.encode('utf-8'))
        
        elif self.path == '/api/list':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            urls = []
            if os.path.exists(LIST_FILE):
                with open(LIST_FILE, 'r', encoding='utf-8') as f:
                    urls = [l.strip() for l in f if l.strip()]
            self.wfile.write(json.dumps(urls).encode('utf-8'))
        else: super().do_GET()

    def do_POST(self):
        if self.path == '/api/update_list':
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            with open(LIST_FILE, 'w', encoding='utf-8') as f:
                f.write('\n'.join(data))
            self.send_response(200)
            self.end_headers()

print("Web Server On: http://localhost:38848")
HTTPServer(('0.0.0.0', 38848), MonitorHandler).serve_forever()
