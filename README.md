WebRTC Virtual Camera (虚拟摄像头无缝切换助手)
基于 Python 和 Selenium 开发的 WebRTC 虚拟摄像头注入工具。通过底层劫持浏览器的 `getUserMedia` API，将原本的真实物理摄像头画面替换为本地指定的 MP4 视频。
本项目专门针对需要频繁切换视频源的场景（如网课学习、自动化测试、网页会议）进行了重构，支持**在不关闭浏览器的情况下无缝切换后台视频流**。

## 核心特性

无缝热切换：随时在工具界面更换 MP4 视频，无需重启浏览器，新页面或重开摄像头即刻生效。
底层 API 劫持：通过 CDP 注入 JavaScript 劫持 WebRTC 协议，兼容绝大多数主流网页视频应用（如 Jitsi, 腾讯会议 Web 端, 各类网课平台）。
权限自动绕过：自动静默同意浏览器的麦克风和摄像头权限请求。
隔离的浏览器环境：支持设置“账号标识”，不同标识对应独立的浏览器缓存与 Cookie，实现多开防串号。
 友好的 GUI 界面：基于 Tkinter 打造，带运行日志监控，小白也能轻松上手。

##  技术栈
- **Python 3.x**
- **Selenium** (自动化控制)
- **Microsoft Edge WebDriver** (浏览器驱动)
- **Tkinter** (原生 GUI)
- **HTTP Server + WebRTC (JS)** (本地媒体流分发)

##  快速开始

### 1. 环境准备
确保你的电脑已安装 [Python](https://www.python.org/)，然后克隆本仓库并安装依赖库：
```bash
git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd 你的仓库名
pip install selenium
