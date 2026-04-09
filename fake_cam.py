import os
import threading
import http.server
import socketserver
import urllib.parse
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from selenium import webdriver
from selenium.webdriver.edge.options import Options

class VirtualCamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WebRTC 虚拟摄像头劫持工具 (无缝切换版)")
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        self.driver = None
        self.server_thread = None
        self.server_port = 8080
        self.httpd = None
        self.is_running = False
        
        # 核心：保存当前正在使用的视频绝对路径
        self.current_video_path = ""

        self.setup_ui()

    def setup_ui(self):
        # 1. 视频选择区
        tk.Label(self.root, text="1. 选择本地 MP4 视频:", font=("Arial", 10, "bold")).place(x=20, y=10)
        self.video_entry = tk.Entry(self.root, width=50)
        self.video_entry.place(x=20, y=35)
        tk.Button(self.root, text="浏览...", command=self.select_video).place(x=385, y=30)
        
        # 新增：实时无缝切换视频按钮
        self.update_video_btn = tk.Button(self.root, text="🔄 无缝更换视频", fg="blue", command=self.update_live_video, state=tk.DISABLED)
        self.update_video_btn.place(x=450, y=30)

        # 2. 目标网址区
        tk.Label(self.root, text="2. 输入目标网址 (登录页或会议链接):", font=("Arial", 10, "bold")).place(x=20, y=70)
        self.url_entry = tk.Entry(self.root, width=65)
        self.url_entry.place(x=20, y=95)
        # 默认使用 Jitsi 视频会议作为测试
        self.url_entry.insert(0, "https://meet.jit.si/TestRoom123")

        # 3. 账号隔离配置区
        tk.Label(self.root, text="3. 账号标识 (自动记忆不同账号的登录状态):", font=("Arial", 10, "bold")).place(x=20, y=130)
        self.profile_entry = tk.Entry(self.root, width=30)
        self.profile_entry.place(x=20, y=155)
        self.profile_entry.insert(0, "Default_User")

        # 4. 控制按钮区
        self.start_btn = tk.Button(self.root, text="▶ 启动虚拟摄像头", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), command=self.start_process_thread)
        self.start_btn.place(x=120, y=200, width=150, height=40)

        self.stop_btn = tk.Button(self.root, text="⏹ 停止并关闭浏览器", bg="#f44336", fg="white", font=("Arial", 11, "bold"), command=self.stop_process, state=tk.DISABLED)
        self.stop_btn.place(x=320, y=200, width=150, height=40)

        # 5. 日志输出区
        tk.Label(self.root, text="运行日志:", font=("Arial", 9)).place(x=20, y=250)
        self.log_text = scrolledtext.ScrolledText(self.root, width=76, height=14, state='disabled', bg="#f0f0f0")
        self.log_text.place(x=20, y=270)
        
        self.log("系统就绪。支持在不关闭浏览器的情况下无缝更换视频。")

    def log(self, message):
        """向日志框输出信息"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def select_video(self):
        """选择视频文件"""
        file_path = filedialog.askopenfilename(
            title="选择 MP4 视频文件",
            filetypes=[("MP4 Videos", "*.mp4"), ("All Files", "*.*")]
        )
        if file_path:
            self.video_entry.delete(0, tk.END)
            self.video_entry.insert(0, file_path)

    def update_live_video(self):
        """在运行过程中实时更新后台视频路径"""
        new_path = self.video_entry.get().strip()
        if not new_path or not os.path.exists(new_path):
            messagebox.showerror("错误", "请先选择一个有效的视频文件！")
            return
        
        self.current_video_path = new_path
        self.log(f"🔄 视频源已后台切换为: {os.path.basename(new_path)}")
        self.log("💡 提示：进入下一节课时会自动生效。如果在当前页面，关闭摄像头再重新打开即可生效。")

    def start_local_server(self):
        """带 CORS 跨域且支持动态路径映射的本地视频流服务器"""
        app_instance = self # 捕获当前实例以便获取动态视频路径

        class DynamicCORSRequestHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                # 核心拦截逻辑：无论注入脚本请求什么，只要匹配到虚拟路径，就返回我们实时指定的物理文件
                if path == '/virtual_cam_stream.mp4':
                    return app_instance.current_video_path
                return super().translate_path(path)

            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
                super().end_headers()
                
            def log_message(self, format, *args):
                pass # 静默服务器日志，避免刷屏

        socketserver.TCPServer.allow_reuse_address = True
        try:
            self.httpd = socketserver.TCPServer(("", self.server_port), DynamicCORSRequestHandler)
            self.log(f"[服务器] 动态视频转发服务运行中 (端口: {self.server_port})")
            self.httpd.serve_forever()
        except Exception as e:
            self.log(f"[服务器错误] 端口可能被占用: {e}")

    def run_browser(self, target_url, profile_name):
        """运行 Edge 并注入 WebRTC 劫持脚本"""
        edge_options = Options()
        edge_options.add_argument("--use-fake-ui-for-media-stream")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)

        safe_profile_name = "".join(x for x in profile_name if x.isalnum() or x in "._-")
        if not safe_profile_name:
            safe_profile_name = "Default_User"
        
        profile_path = os.path.join(os.getcwd(), f"EdgeData_{safe_profile_name}")
        edge_options.add_argument(f"--user-data-dir={profile_path}")

        try:
            self.log(f"[浏览器] 正在启动 Edge 并加载缓存: {safe_profile_name}")
            self.driver = webdriver.Edge(options=edge_options)

            # 注意：这里的 video.src 被改成了固定的虚拟路径
            js_injection = f"""
            const originalGetUserMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = async function(constraints) {{
                if (constraints && constraints.video) {{
                    console.log("🔒 成功拦截摄像头请求，正在载入虚拟视频流...");
                    const video = document.createElement('video');
                    // 请求固定的虚拟接口，Python 服务端会动态返回文件
                    video.src = 'http://127.0.0.1:{self.server_port}/virtual_cam_stream.mp4';
                    video.loop = true;
                    video.muted = true;
                    video.crossOrigin = "anonymous";
                    
                    return new Promise((resolve, reject) => {{
                        video.oncanplay = async () => {{
                            try {{
                                await video.play();
                                resolve(video.captureStream());
                            }} catch (e) {{
                                reject(e);
                            }}
                        }};
                        video.onerror = (e) => reject(new DOMException("视频文件无法加载", "NotSupportedError"));
                    }});
                }}
                // 如果只请求了麦克风，则放行原生调用
                return originalGetUserMedia(constraints);
            }};
            """
            
            # 使用 CDP 在每个新页面加载前注入 JS
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": js_injection
            })

            self.log(f"[浏览器] 正在访问: {target_url}")
            self.driver.get(target_url)
            self.log("✅ 劫持已就绪！现在可以正常使用了。")

        except Exception as e:
            self.log(f"❌ 运行报错: {e}\n(请检查是否已安装 Edge 浏览器及对应驱动)")
            self.stop_process()

    def start_process_thread(self):
        """开启新线程以防阻塞 UI"""
        video_path = self.video_entry.get().strip()
        target_url = self.url_entry.get().strip()
        profile_name = self.profile_entry.get().strip()

        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("错误", "请选择有效的 MP4 视频！")
            return
            
        if not target_url.startswith("http"):
            messagebox.showerror("错误", "请输入正确的网址 (需包含 http/https)！")
            return

        # 记录当前要播放的视频
        self.current_video_path = video_path

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.update_video_btn.config(state=tk.NORMAL)
        self.is_running = True

        # 1. 启动本地服务器 (仅当未启动时)
        if not self.httpd:
            self.server_thread = threading.Thread(target=self.start_local_server, daemon=True)
            self.server_thread.start()

        # 2. 启动浏览器
        threading.Thread(target=self.run_browser, args=(target_url, profile_name), daemon=True).start()

    def stop_process(self):
        """停止流程清理资源"""
        self.log("正在关闭浏览器并释放资源...")
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_video_btn.config(state=tk.DISABLED)
        self.is_running = False
        self.log("🛑 已完全停止。")

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualCamApp(root)
    root.mainloop()