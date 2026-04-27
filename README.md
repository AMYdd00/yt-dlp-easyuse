# 📺 轻量直播监控脚本

一个完全使用AI编译，基于 `yt-dlp` 的自动化直播回放监控脚本工具，带有网页管理界面。

通过确认直播结束后才开始下载直播流，从而杜绝因为网络环境卡顿而导致录制文件出现问题

# 🛠️ 环境一键安装

请按下 `Win + X` 打开 **终端 (PowerShell)** 或 **命令提示符 (CMD)**，依次复制并运行以下指令

## 1. 安装系统组件 (通过 Winget)
使用 Windows 自带包管理器一键安装所有依赖工具：

### 安装 Python (运行环境)
```shell
winget install Python.Python.3.11
```
### 安装 FFmpeg (核心解码与合并组件)
```shell
winget install Gyan.FFmpeg
```
### 安装 Node.js (解析 YouTube 脚本需要)
```shell
winget install OpenJS.NodeJS
```
> **注意**：安装完成后，请关闭并重启终端，以使环境变量生效。

## 2. 安装 Python 依赖库

### 安装 yt-dlp
```shell
pip install -U yt-dlp
```
# 安装本项目

```shell
git clone https://github.com/AMYdd00/yt-dlp-easyuse.git ./yt-dlp-easyuse/
```

## 🚀 快速启动

1. **配置代理**：使用记事本打开 `run.bat` 修改你的代理地址（ `--proxy "http://127.0.0.1:7890"`）。
2. **一键运行**：双击项目根目录下的 **`run.bat`**。
   - 此时网页后端服务与监控逻辑将同时启动。
3. **访问管理界面**：在浏览器打开 `http://localhost:38848`。
4. **添加直播链接**：油管添加直播页面的链接，如“https://www.youtube.com/@necomakarin/streams” 注意最后是streams而不是直播间链接的live

## 📂 自动化规则
- **自动分类**：下载的视频按 `Downloads/主播名/` 自动归类。
- **智能命名**：文件命名格式为 `[上传日期] 视频标题.mp4`。
- **重复检查**：系统自动维护 `archive.txt` 库，下载过的视频不会二次抓取。
- **静默后台**：监控窗口仅显示关键动态，Web 访问日志已静默处理。

## 📝 TODO

- [ ] 一键打开下载目录
- [ ] 添加一次性下载录播选项
- [ ] 整合AI识别生成字幕并翻译功能


## ⚠️ 常见问题
- **无法下载**：请确认 `run.bat` 中的代理端口与你的科学上网软件一致。
- **网页打不开**：确认网络环境正常且本机的38848 端口未被占用。

## 💖 鸣谢 (Credits / Acknowledgements)

- [yt-dlp](https://github.com) - 核心下载引擎
- [FFmpeg](https://ffmpeg.org) - 强大的音视频处理工具
- [Gemini](https://gemini.google.com) - 提供所有代码

