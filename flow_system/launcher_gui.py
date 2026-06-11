# -*- encoding: utf-8 -*-
"""
成品追溯与客户管理系统 - GUI 启动器
"""
import sys
import os
import threading
import socket
import webbrowser
import tkinter as tk
import tkinter.ttk as ttk  # 显式导入 ttk，PyInstaller 打包需要
from tkinter import scrolledtext, messagebox
from datetime import datetime

# 版本信息
VERSION = "v1.38"
APP_NAME = "成品追溯与客户管理系统"
BUILD_DATE = "2026-06-10"

# 更新日志（最新在上）
UPDATE_LOG = [
    "v1.38 (2026-06-10)：外箱日期显示优化——2026年6月及以后使用YC前缀，之前使用YY前缀",
    "v1.37 (2026-05-12)：优化新增流向提交体验，提交成功后立即更新主页列表；后端预取客户和生产时间段减少列表加载延迟；重新打包并恢复新版运行目录数据库",
    "v1.36 (2026-04-27)：允许只填区域码提交流向记录，区域码未注册时后端自动创建客户（名称/地址可选填）",
    "v1.35 (2026-04-15)：批号字段禁用浏览器原生验证；提交后直接插入新记录消除延迟；修复前端构建路径",
    "v1.34 (2026-04-15)：重新构建前端+打包，排序改为升序（最新录入的排在最后）",
    "v1.33 (2026-04-15)：排序改为倒序——最新录入的记录（最大ID）显示在最前面",
    "v1.32 (2026-04-15)：从备份恢复ShipmentTracking.vue，分组键改为4字段（日期+区域码+物料编号+物料描述），按录入顺序显示",
    "v1.31 (2026-04-14)：排序改为按录入顺序（ID）而非发货日期——最后补录的记录显示在列表末尾",
    "v1.29 (2026-04-14)：移除fOnlyRecords特殊处理，含F记录统一走分组逻辑",
    "v1.24 (2026-04-13)：含F的流向记录不再参与分组——无论外箱日期/批次/规格/线别是否一致，F记录均单独成行显示",
    "v1.23 (2026-04-13)：提交成功后前端直接插入新记录——不再请求全量API，提交后延迟从2-3秒降至瞬间完成",
    "v1.22 (2026-04-13)：禁用浏览器原生HTML5验证——解决批号字段触发验证时光标乱跳问题（novalidate）",
    "v1.20 (2026-04-12)：合并 C盘开发库 2025年数据——新增3567条记录（2025-06至12月），exe数据库现共6013条",
    "v1.19 (2026-04-12)：关闭后端分页——API 不再限制50条，一次返回全部数据",
    "v1.18 (2026-04-12)：列表标题新增记录数显示（已加载N条、当前筛选N条）；确认数据库无2025年数据；确认2026年1-4月数据完整",
    "v1.17 (2026-04-12)：修复前端分页响应兼容——shipments 数组解析错误；修复运行时 forEach is not a function",
    "v1.16 (2026-04-12)：禁用 UPX 压缩（DLL 运行时加载错误修复）",
    "v1.15 (2026-04-12)：修复前端构建路径——v1.14 前端代码实际未打包进 exe；页面空白问题根因已修复",
    "v1.14 (2026-04-12)：优化提交延迟——提交后不再全量刷新；alert 改 toast；轮询60秒；DRF分页",
    "v1.13 (2026-04-12)：恢复 api/ 源码目录（从 C 盘备份复制，修复 No module named 'api.urls'）",
    "v1.12 (2026-04-12)：修复 Django 5.x 兼容问题（LOGGING mail_admins → NullHandler）；spec datas 改为指向源目录而非 _internal",
]

# 路径配置
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    DIST_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DIST_DIR = BASE_DIR

PROJECT_DIR = os.path.dirname(BASE_DIR) if BASE_DIR.endswith('flow_system') else BASE_DIR

# Django 配置
DJANGO_FLOW_SYSTEM = os.path.join(BASE_DIR, 'flow_system')
DJANGO_SETTINGS = os.path.join(BASE_DIR, 'flow_system', 'flow_system')
sys.path.insert(0, DJANGO_FLOW_SYSTEM)
sys.path.insert(0, DJANGO_SETTINGS)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# 端口配置
DEFAULT_PORT = 8002


class LogRedirector:
    """将 stdout/stderr 重定向到日志文本框"""
    def __init__(self, text_widget, tag="info"):
        self.text_widget = text_widget
        self.tag = tag
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        if '\n' in string:
            lines = self.buffer.split('\n')
            self.buffer = lines[-1]
            for line in lines[:-1]:
                self._insert_line(line)
        if string and not string.endswith('\n'):
            self.buffer += string

    def _insert_line(self, line):
        if not line.strip():
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.configure(state='normal')

        # 根据日志类型设置颜色
        if '[ERROR]' in line or 'Error' in line or 'Traceback' in line:
            self.text_widget.insert('end', f"[{timestamp}] ", "time")
            self.text_widget.insert('end', line + "\n", "error")
        elif '[WARN]' in line or 'Warning' in line:
            self.text_widget.insert('end', f"[{timestamp}] ", "time")
            self.text_widget.insert('end', line + "\n", "warn")
        elif 'started' in line.lower() or 'running' in line.lower() or 'OK' in line:
            self.text_widget.insert('end', f"[{timestamp}] ", "time")
            self.text_widget.insert('end', line + "\n", "success")
        else:
            self.text_widget.insert('end', f"[{timestamp}] ", "time")
            self.text_widget.insert('end', line + "\n", "info")

        self.text_widget.see('end')
        self.text_widget.configure(state='disabled')

    def flush(self):
        pass


class LauncherGUI:
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.geometry("680x520")
        self.root.resizable(True, True)
        self.root.minsize(580, 420)

        # 居中显示
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 680) // 2
        y = (screen_height - 520) // 2
        self.root.geometry(f"680x520+{x}+{y}")

        # 变量
        self.server_process = None
        self.server_running = False
        self.port = DEFAULT_PORT

        # UI 样式配置
        self.bg_color = "#1e1e1e"
        self.accent_color = "#0078d4"
        self.success_color = "#4caf50"
        self.error_color = "#f44336"
        self.warn_color = "#ff9800"
        self.text_color = "#d4d4d4"

        self._setup_styles()
        self._create_ui()

        # 窗口关闭时清理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 启动时自动检测端口并尝试启动
        self.root.after(500, self.auto_start)

    def _setup_styles(self):
        """配置 ttk 样式"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        # 配置颜色
        self.root.configure(bg=self.bg_color)

    def _create_ui(self):
        """创建 UI 组件"""

        # === 标题区域 ===
        header_frame = tk.Frame(self.root, bg=self.bg_color, pady=15)
        header_frame.pack(fill='x')

        # 系统图标和标题
        title_label = tk.Label(
            header_frame,
            text=f"⚙ {APP_NAME}",
            font=("Microsoft YaHei UI", 18, "bold"),
            fg="white",
            bg=self.bg_color
        )
        title_label.pack()

        # 版本和构建信息
        version_label = tk.Label(
            header_frame,
            text=f"版本 {VERSION}  |  构建日期 {BUILD_DATE}",
            font=("Microsoft YaHei UI", 10),
            fg="#888888",
            bg=self.bg_color
        )
        version_label.pack(pady=(5, 0))

        # === 状态区域 ===
        status_frame = tk.Frame(self.root, bg=self.bg_color, pady=10)
        status_frame.pack(fill='x')

        # 状态指示灯
        self.status_indicator = tk.Canvas(status_frame, width=20, height=20, bg=self.bg_color, highlightthickness=0)
        self.status_circle = self.status_indicator.create_oval(3, 3, 17, 17, fill="#666666", outline="")
        self.status_indicator.pack(side='left', padx=(20, 10))

        # 状态文字
        self.status_label = tk.Label(
            status_frame,
            text="正在启动...",
            font=("Microsoft YaHei UI", 12),
            fg=self.text_color,
            bg=self.bg_color
        )
        self.status_label.pack(side='left')

        # 访问按钮容器
        btn_frame = tk.Frame(self.root, bg=self.bg_color, pady=5)
        btn_frame.pack(fill='x')

        # 访问地址显示
        self.url_label = tk.Label(
            btn_frame,
            text=f"访问地址: http://localhost:{self.port}/",
            font=("Consolas", 11),
            fg="#569cd6",
            bg=self.bg_color
        )
        self.url_label.pack(side='left', padx=20)

        # 打开浏览器按钮
        self.open_btn = tk.Button(
            btn_frame,
            text="🌐 打开浏览器",
            font=("Microsoft YaHei UI", 10),
            bg=self.accent_color,
            fg="white",
            activebackground="#005a9e",
            activeforeground="white",
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            state='disabled',
            command=self.open_browser
        )
        self.open_btn.pack(side='right', padx=20)

        # === 日志区域 ===
        log_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=10)
        log_frame.pack(fill='both', expand=True)

        # 日志标题
        log_title = tk.Label(
            log_frame,
            text="📋 运行日志",
            font=("Microsoft YaHei UI", 10, "bold"),
            fg=self.text_color,
            bg=self.bg_color,
            anchor='w'
        )
        log_title.pack(anchor='w', pady=(0, 5))

        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap='word',
            font=("Consolas", 10),
            bg="#252526",
            fg=self.text_color,
            insertbackground='white',
            relief='flat',
            state='disabled',
            height=15
        )
        self.log_text.pack(fill='both', expand=True)

        # 配置日志文本标签颜色
        self.log_text.tag_config("time", foreground="#858585")
        self.log_text.tag_config("info", foreground=self.text_color)
        self.log_text.tag_config("success", foreground=self.success_color)
        self.log_text.tag_config("error", foreground=self.error_color)
        self.log_text.tag_config("warn", foreground=self.warn_color)

        # === 底部按钮区域 ===
        bottom_frame = tk.Frame(self.root, bg=self.bg_color, pady=12, padx=20)
        bottom_frame.pack(fill='x', side='bottom')

        # 左侧：端口配置
        port_frame = tk.Frame(bottom_frame, bg=self.bg_color)
        port_frame.pack(side='left')

        tk.Label(port_frame, text="端口:", font=("Microsoft YaHei UI", 10), fg=self.text_color, bg=self.bg_color).pack(side='left', padx=(0, 5))
        self.port_entry = tk.Entry(port_frame, font=("Consolas", 10), width=8, justify='center')
        self.port_entry.insert(0, str(self.port))
        self.port_entry.pack(side='left')

        # 右侧：控制按钮
        btn_right = tk.Frame(bottom_frame, bg=self.bg_color)
        btn_right.pack(side='right')

        self.refresh_btn = tk.Button(
            btn_right,
            text="🔄 重启服务",
            font=("Microsoft YaHei UI", 10),
            bg="#333333",
            fg="white",
            activebackground="#444444",
            activeforeground="white",
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.restart_server
        )
        self.refresh_btn.pack(side='left', padx=5)

        self.toggle_btn = tk.Button(
            btn_right,
            text="⏹ 停止服务",
            font=("Microsoft YaHei UI", 10),
            bg=self.error_color,
            fg="white",
            activebackground="#d32f2f",
            activeforeground="white",
            relief='flat',
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.toggle_server
        )
        self.toggle_btn.pack(side='left', padx=5)

        # 重定向标准输出到日志
        self.log_redirector = LogRedirector(self.log_text)
        sys.stdout = self.log_redirector
        sys.stderr = self.log_redirector

    def log(self, message, level="info"):
        """写入日志"""
        self.log_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")

        tag_map = {"info": "info", "success": "success", "error": "error", "warn": "warn"}
        tag = tag_map.get(level, "info")

        self.log_text.insert('end', f"[{timestamp}] ", "time")
        self.log_text.insert('end', message + "\n", tag)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def update_status(self, running, message):
        """更新状态显示"""
        self.server_running = running

        # 更新指示灯颜色
        color = self.success_color if running else "#666666"
        self.status_indicator.itemconfig(self.status_circle, fill=color)

        # 更新状态文字
        self.status_label.configure(text=message)

        # 更新按钮状态
        self.open_btn.configure(state='normal' if running else 'disabled')
        self.toggle_btn.configure(
            text="⏹ 停止服务" if running else "▶ 启动服务",
            bg=self.error_color if running else self.success_color
        )

    def is_port_in_use(self, port):
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def find_available_port(self, start_port=8002):
        """查找可用端口"""
        port = start_port
        while port < start_port + 100:
            if not self.is_port_in_use(port):
                return port
            port += 1
        return None

    def start_server(self):
        """启动 Django 服务器"""
        try:
            port = int(self.port_entry.get())
        except ValueError:
            self.log(f"端口号无效: {self.port_entry.get()}", "error")
            return

        # 检查端口是否可用
        if self.is_port_in_use(port):
            self.log(f"端口 {port} 已被占用，尝试查找其他端口...", "warn")
            new_port = self.find_available_port(port + 1)
            if new_port:
                port = new_port
                self.log(f"使用端口 {port}", "info")
                self.port_entry.delete(0, 'end')
                self.port_entry.delete(0, 'end')
                self.port_entry.insert(0, str(port))
            else:
                self.log("无法找到可用端口", "error")
                return

        self.port = port
        self.url_label.configure(text=f"访问地址: http://localhost:{self.port}/")
        self.log(f"正在启动 Django 服务 (端口 {self.port})...", "info")
        self.update_status(False, "正在启动...")

        def run_server():
            try:
                self._safe_log("检查运行环境...", "info")
                import django
                # 修复 Django 5.x：覆盖 DEFAULT_LOGGING，禁用已移除的 AdminEmailHandler
                import django.utils.log
                django.utils.log.DEFAULT_LOGGING = {
                    'version': 1,
                    'disable_existing_loggers': False,
                    'handlers': {
                        'console': {
                            'class': 'logging.StreamHandler',
                        },
                    },
                    'root': {
                        'level': 'WARNING',
                        'handlers': ['console'],
                    },
                }
                self._safe_log("初始化 Django...", "info")
                django.setup()
                from django.core.management import call_command
                self._safe_log("Django 初始化完成，正在启动 HTTP 服务...", "success")
                call_command('runserver', f'0.0.0.0:{self.port}', '--noreload')
            except Exception as e:
                import traceback
                err = traceback.format_exc()
                self._safe_log(f"服务器错误: {e}", "error")
                self._safe_log(err, "error")
                self.root.after(0, lambda: self.update_status(False, "启动失败"))

        thread = threading.Thread(target=run_server, daemon=True, name="django-server")
        thread.start()

        # 非阻塞等待：用 tkinter after 轮询端口
        self._check_start_count = 0
        self._poll_server_start()

    def _safe_log(self, message, level="info"):
        """从任意线程安全写入日志（通过 root.after 切换到主线程）"""
        self.root.after(0, lambda m=message, l=level: self.log(m, l))

    def _poll_server_start(self):
        """非阻塞轮询端口，直到服务启动或超时"""
        if self.is_port_in_use(self.port):
            self.log(f"✅ 服务已启动! http://localhost:{self.port}/", "success")
            self.update_status(True, "运行中")
            return
        self._check_start_count += 1
        if self._check_start_count >= 40:   # 最多等 20 秒
            self.log("服务启动超时，请检查日志", "error")
            self.update_status(False, "启动失败")
            return
        # 每 500ms 再查一次
        self.root.after(500, self._poll_server_start)

    def stop_server(self):
        """停止服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None

        # 杀掉所有监听该端口的进程
        import subprocess
        try:
            result = subprocess.run(
                f'netstat -ano | findstr :{self.port}',
                shell=True,
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split('\n'):
                if 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = int(parts[-1])
                        try:
                            subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                            self.log(f"已停止进程 PID={pid}", "info")
                        except:
                            pass
        except:
            pass

        self.update_status(False, "已停止")
        self.log("服务已停止", "info")

    def toggle_server(self):
        """切换服务器状态"""
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def restart_server(self):
        """重启服务器"""
        self.log("正在重启服务...", "info")
        if self.server_running or self.is_port_in_use(self.port):
            self.stop_server()
            # 延迟 1 秒后再启动，避免阻塞主线程
            self.root.after(1000, self.start_server)
        else:
            self.start_server()

    def open_browser(self):
        """打开浏览器"""
        url = f"http://localhost:{self.port}/"
        self.log(f"打开浏览器: {url}", "info")
        webbrowser.open(url)

    def auto_start(self):
        """自动检测并启动服务"""
        # 检查端口是否已被占用
        port = int(self.port_entry.get())
        if self.is_port_in_use(port):
            self.log(f"检测到端口 {port} 已被占用，服务可能已在运行", "warn")
            self.port = port
            self.url_label.configure(text=f"访问地址: http://localhost:{self.port}/")
            self.update_status(True, "运行中")
            self.open_btn.configure(state='normal')
            return

        # 自动启动服务
        self.start_server()

    def on_closing(self):
        """窗口关闭时的处理"""
        if self.server_running or self.is_port_in_use(self.port):
            if messagebox.askyesno("确认退出", "服务正在运行，确定要退出吗？"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    # 检查管理员权限提示
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        print("提示: 以管理员身份运行可避免端口权限问题")

    # 创建并运行 GUI
    app = LauncherGUI()
    app.root.mainloop()


if __name__ == '__main__':
    main()


