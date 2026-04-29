c = open("README.md", encoding="utf-8").read()
old = "- [Gemini](https://gemini.google.com) — AI 辅助编码"
new = "- [Gemini](https://gemini.google.com) — 初始代码生成\n- [DeepSeek V4 Pro](https://chat.deepseek.com) — 架构重构、Python 调度器、Web UI 优化、错误修复与稳定性增强"
c = c.replace(old, new)
open("README.md", "w", encoding="utf-8").write(c)
print("Updated")