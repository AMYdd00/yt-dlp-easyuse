# 📺 YT-DLP 录播监控

> 基于 `yt-dlp` 的直播回放自动监控工具，带 Web 管理界面。  
> 直播结束后自动下载，杜绝网络卡顿导致的录制文件损坏。

---

## ✨ 特性

- **智能监控** — 检测到直播结束后自动触发下载，不遗漏任何 VOD
- **Python 调度** — 取代传统批处理循环，彻底解决 URL 特殊字符 & 引号嵌套问题
- **Web 管理界面** — 可视化查看频道状态、实时日志、手动添加/删除频道
- **单次补录** — 支持手动输入任意视频链接进行强制下载
- **自动分类** — 按 `Downloads/主播名/` 归文件夹，命名格式 `[日期] 标题.mp4`
- **防重复** — 内置 `archive.txt` 记录，已下载视频自动跳过
- **轻量静默** — yt-dlp 后台无声运行，日志定向输出，不弹额外窗口
- **配置集中** — 代理、格式、重试策略等所有参数统一在 `config.json` 管理

---

## 🛠️ 安装

### 1. 安装系统组件 (通过 Winget)

```powershell
winget install Python.Python.3.11
winget install Gyan.FFmpeg
winget install OpenJS.NodeJS
```

> 安装完成后**关闭并重启终端**，使环境变量生效。

### 2. 安装 yt-dlp

```powershell
pip install -U yt-dlp
```

### 3. 下载本项目

```powershell
git clone https://github.com/AMYdd00/yt-dlp-easyuse.git
```

---

## 🚀 快速启动

### 第一步：配置代理

用记事本打开 `config.json`，修改 `proxy` 字段为你的代理地址：

```json
{
  "yt_dlp": {
    "proxy": "http://127.0.0.1:7890"
  }
}
```

### 第二步：启动

| 方式 | 说明 |
|------|------|
| 双击 `run.bat` | 有控制台窗口，按 `X` 键退出 |
| 双击 `start_hidden.vbs` | 完全静默后台运行 |

启动后浏览器打开 **http://localhost:38848** 进入管理界面。

### 第三步：添加频道

1. 在侧边栏输入频道的 **Streams 页面链接**（如 `https://www.youtube.com/@necomakarin/streams`）
2. 点击「添加到监控」即可

> ⚠️ 注意结尾是 `/streams`，不是 `/live`

### 手动补录

1. 复制要下载的视频链接（如 `https://www.youtube.com/watch?v=iz6AspeszIQ`）
2. 粘贴到侧边栏「手动下载」输入框
3. 点击「开始下载」

---

## 📁 文件结构

```
📁 yt-dlp-easyuse/
├── 📄 server.py          # Web API 服务 (端口 38848)
├── 📄 worker.py          # Python 下载调度器
├── 📄 index.html         # Web 管理界面
├── 📄 config.json        # 统一配置 (代理/格式/重试等)
├── 📄 list.txt           # 监控频道列表
├── 📄 archive.txt        # 已下载记录 (yt-dlp 自动维护)
├── 📄 run.bat            # 启动脚本 (有窗口)
├── 📄 start_hidden.vbs   # 启动脚本 (无窗口)
├── 📄 stop.bat           # 停止脚本 (仅杀 38848 端口)
├── 📁 Downloads\         # 下载文件自动归类
│   ├── 📁 主播名A\
│   ├── 📁 主播名B\
│   └── 📁 Manual\        # 手动补录专用
└── 📁 logs\              # 运行日志
    ├── 📄 主播名A.log
    ├── 📄 主播名B.log
    └── ...
```

---

## ⚙️ 配置说明

所有参数集中在 `config.json`，无需修改代码：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 38848
  },
  "yt_dlp": {
    "proxy": "http://127.0.0.1:7890",
    "retries": "infinite",
    "fragment_retries": "infinite",
    "retry_sleep": 10,
    "extractor_retries": 10,
    "concurrent_fragments": 4,
    "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "merge_format": "mp4",
    "playlist_items": "1-5",
    "match_filter": "live_status = was_live"
  },
  "paths": {
    "downloads": "Downloads",
    "logs": "logs",
    "archive": "archive.txt",
    "list_file": "list.txt"
  },
  "polling": {
    "interval_seconds": 300
  }
}
```

---

## 🖥️ Web 界面

| 功能 | 说明 |
|------|------|
| 频道列表 | 显示所有监控频道状态、实时日志、下载进度 |
| 状态指示 | 🟢 下载中 / 🟡 直播中 / ⚪ 等待中 |
| 添加频道 | 输入 stream 链接加入监控队列 |
| 删除频道 | 防误触机制，需二次确认 |
| 手动下载 | 单次强制下载任意视频 |
| 主题切换 | 深色/浅色模式 |
| 引擎状态 | 顶部徽章显示服务运行健康度 |

---

## 🔄 架构说明

```
list.txt ──> worker.py ──> yt-dlp ──> Downloads/主播名/
                 │
                 ├── PID 文件 (进程管理)
                 └── 日志文件 (logs/*.log)
                                  │
index.html <── server.py <────────┘
                 │
                 └── 端口 38848
```

- **worker.py** — 独立进程，轮询 `list.txt`，管理下载任务
- **server.py** — 独立进程，提供 Web API 和静态文件服务
- 两者互不干扰，可独立启停

---

## ❓ 常见问题

### 无法下载
- 检查 `config.json` 中的 `proxy` 端口是否与代理软件一致
- 确认 yt-dlp 已正确安装：`yt-dlp --version`

### 网页打不开
- 检查 38848 端口是否被占用：`netstat -ano | findstr :38848`
- 双击 `stop.bat` 后重新运行 `run.bat`

### 下载到一半出错
- 内置无限重试 + 分片重试机制，网络恢复后会自动续传
- 可调整 `config.json` 中的 `retry_sleep` 间隔

### stop.bat 杀了其他 Python 进程？
- `stop.bat` 已优化为仅杀 38848 端口和 yt-dlp 进程，不影响其他 Python 应用

---

## 📝 TODO

- [x] 添加单次下载录播选项
- [ ] 一键打开下载目录
- [ ] 整合 AI 识别生成字幕并翻译

---

## 💖 鸣谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — 强大的核心下载引擎
- [FFmpeg](https://ffmpeg.org) — 无敌的音视频处理工具
- [Gemini](https://gemini.google.com) — 强大的AI，生成初始代码
- [DeepSeek V4 Pro](https://chat.deepseek.com) — 架构重构、Python 调度器、Web UI 优化、错误修复与稳定性增强