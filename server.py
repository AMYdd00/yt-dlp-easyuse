import os, json, re
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LIST_FILE = os.path.join(BASE_DIR, 'list.txt')
INDEX_FILE = os.path.join(BASE_DIR, 'index.html')

def translate_status(line):
    if "does not pass filter" in line or "is_live" in line: 
        return "📡 监控中: 正在直播 (等待下播)"
    if "has already been recorded" in line: 
        return "✅ 存档已存在"
    if "|" in line and "%" in line:
        parts = line.split('|')
        return f"🚀 正在下载: {parts[0].strip()}"
    if "Downloading" in line: return "📡 获取流中..."
    if "Merging" in line: return "📦 封装中..."
    if "Finished" in line: return "🔍 巡检完成"
    return "🔍 监视中..."

class MonitorHandler(SimpleHTTPRequestHandler):
    # 屏蔽掉每秒一次的 GET 日志输出，让 CMD 彻底安静
    def log_message(self, format, *args):
        return

    def do_GET(self):
        # 1. 首页
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            else:
                self.wfile.write(b"Error: index.html not found.")

        # 2. 状态 API
        elif self.path == '/api/status':
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

        # 3. 频道列表 API (补全这里，解决 404)
        elif self.path == '/api/list':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            urls = []
            if os.path.exists(LIST_FILE):
                with open(LIST_FILE, 'r', encoding='utf-8') as f:
                    urls = [l.strip() for l in f if l.strip()]
            self.wfile.write(json.dumps(urls).encode('utf-8'))

        # 4. 日志详情 API
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
                    f.seek(max(0, f.tell() - 3000))
                    content = f.read().decode('gbk', errors='ignore')
                    self.wfile.write(content.encode('utf-8'))
        else:
            super().do_GET()

if __name__ == '__main__':
    print("=======================================")
    print(" 监控矩阵已启动: http://localhost:38848")
    print(" 提示: 访问请求日志已静默处理")
    print("=======================================")
    HTTPServer(('0.0.0.0', 38848), MonitorHandler).serve_forever()