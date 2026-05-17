# -*- encoding: utf-8 -*-
"""
DouyinLiveRecorder GUI - 现代化界面
作者: Hmily
项目: DouyinLiveRecorder
设计: 现代深色主题 + 扁平化风格 + 流畅动效
"""
from __future__ import annotations

import os
import sys
import subprocess
import threading
import queue
import re
import configparser
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from datetime import datetime
from typing import Any

import pystray
from PIL import Image, ImageDraw


# ─── 现代化配色方案 ─────────────────────────────────────────
class Theme:
    """现代化深色主题配色"""
    BG_PRIMARY = "#0d1117"
    BG_SECONDARY = "#161b22"
    BG_CARD = "#21262d"
    BG_INPUT = "#0d1117"
    
    ACCENT_PRIMARY = "#58a6ff"
    ACCENT_SUCCESS = "#3fb950"
    ACCENT_DANGER = "#f85149"
    ACCENT_WARNING = "#d29922"
    ACCENT_PURPLE = "#a371f7"
    
    TEXT_PRIMARY = "#f0f6fc"
    TEXT_SECONDARY = "#8b949e"
    TEXT_MUTED = "#484f58"
    
    BORDER = "#30363d"
    BORDER_HOVER = "#58a6ff"
    
    GRADIENT_START = "#1f6feb"
    GRADIENT_END = "#388bfd"
    
    @classmethod
    def gradient(cls, width: int, height: int, steps: int = 100) -> list:
        """生成渐变色列表"""
        colors = []
        for i in range(steps):
            ratio = i / (steps - 1)
            r = int(0x1f + (0x38 - 0x1f) * ratio)
            g = int(0x6f + (0x8b - 0x6f) * ratio)
            b = int(0xeb + (0xfd - 0xeb) * ratio)
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        return colors


class ModernStyles:
    """现代化样式配置"""
    
    FONT_TITLE = ("Segoe UI", 16, "bold")
    FONT_SUBTITLE = ("Segoe UI", 12, "bold")
    FONT_BODY = ("Segoe UI", 10)
    FONT_MONO = ("Cascadia Code", "Consolas", 9)
    FONT_SMALL = ("Segoe UI", 8)
    
    PAD_X = 15
    PAD_Y = 10
    PAD_CARD = 12
    BORDER_RADIUS = 8
    
    @classmethod
    def apply(cls, root: tk.Tk) -> None:
        """应用全局样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 全局背景
        style.configure('.', background=Theme.BG_PRIMARY)
        style.configure('TFrame', background=Theme.BG_PRIMARY)
        style.configure('TLabelframe', background=Theme.BG_PRIMARY, foreground=Theme.TEXT_PRIMARY)
        style.configure('TLabelframe.Label', background=Theme.BG_PRIMARY, foreground=Theme.TEXT_SECONDARY, font=cls.FONT_SMALL)
        
        # 按钮样式
        cls._style_buttons(style)
        
        # 标签样式
        style.configure('Title.TLabel', background=Theme.BG_PRIMARY, foreground=Theme.TEXT_PRIMARY, font=cls.FONT_TITLE)
        style.configure('Subtitle.TLabel', background=Theme.BG_PRIMARY, foreground=Theme.TEXT_SECONDARY, font=cls.FONT_BODY)
        style.configure('Body.TLabel', background=Theme.BG_PRIMARY, foreground=Theme.TEXT_PRIMARY, font=cls.FONT_BODY)
        style.configure('Muted.TLabel', background=Theme.BG_PRIMARY, foreground=Theme.TEXT_MUTED, font=cls.FONT_SMALL)
        
        # 输入框样式
        style.configure('Modern.TEntry', fieldbackground=Theme.BG_INPUT, foreground=Theme.TEXT_PRIMARY, borderwidth=0)
        
        # 滚动条样式
        cls._style_scrollbar(style)
        
    @classmethod
    def _style_buttons(cls, style: ttk.Style) -> None:
        """按钮样式"""
        # 开始按钮 - 绿色渐变
        style.configure('Start.TButton', 
                       background=Theme.ACCENT_SUCCESS, 
                       foreground='white',
                       font=cls.FONT_BODY,
                       padding=(20, 8))
        style.map('Start.TButton',
                  background=[('active', '#2ea043'), ('pressed', '#238636')],
                  foreground=[('disabled', Theme.TEXT_MUTED)])
        
        # 停止按钮 - 红色
        style.configure('Stop.TButton',
                       background=Theme.ACCENT_DANGER,
                       foreground='white',
                       font=cls.FONT_BODY,
                       padding=(20, 8))
        style.map('Stop.TButton',
                  background=[('active', '#da3633'), ('pressed', '#b62324')],
                  foreground=[('disabled', Theme.TEXT_MUTED)])
        
        # 操作按钮 - 蓝色边框
        style.configure('Action.TButton',
                       background='transparent',
                       foreground=Theme.ACCENT_PRIMARY,
                       font=cls.FONT_BODY,
                       padding=(15, 6),
                       relief='flat',
                       borderwidth=1,
                       bordercolor=Theme.ACCENT_PRIMARY)
        style.map('Action.TButton',
                  background=[('active', Theme.ACCENT_PRIMARY), ('pressed', '#1f6feb')],
                  foreground=[('active', 'white'), ('pressed', 'white'), ('disabled', Theme.TEXT_MUTED)])
        
        # 托盘按钮 - 透明边框
        style.configure('Tray.TButton',
                       background='transparent',
                       foreground=Theme.TEXT_SECONDARY,
                       font=cls.FONT_SMALL,
                       padding=(12, 5),
                       relief='flat',
                       borderwidth=1,
                       bordercolor=Theme.BORDER)
        style.map('Tray.TButton',
                  background=[('active', Theme.BG_CARD)],
                  foreground=[('active', Theme.TEXT_PRIMARY)])
        
        # 退出按钮 - 警告色
        style.configure('Exit.TButton',
                       background='transparent',
                       foreground=Theme.ACCENT_DANGER,
                       font=cls.FONT_SMALL,
                       padding=(12, 5),
                       relief='flat',
                       borderwidth=1,
                       bordercolor=Theme.ACCENT_DANGER)
        style.map('Exit.TButton',
                  background=[('active', Theme.ACCENT_DANGER)],
                  foreground=[('active', 'white')])
    
    @classmethod
    def _style_scrollbar(cls, style: ttk.Style) -> None:
        """滚动条样式"""
        style.configure('Modern.Vertical.TScrollbar',
                       background=Theme.BG_CARD,
                       troughcolor=Theme.BG_PRIMARY,
                       bordercolor=Theme.BG_PRIMARY,
                       arrowcolor=Theme.TEXT_SECONDARY,
                       thickness=8)
        style.map('Modern.Vertical.TScrollbar',
                  background=[('active', Theme.ACCENT_PRIMARY), ('pressed', '#1f6feb')])


def _create_rounded_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, 
                         radius: int = 20, **kwargs) -> int:
    """在 Canvas 上绘制圆角矩形"""
    points = []
    r = radius
    d = r * 2
    
    points.extend([x1 + r, y1])
    points.extend([x2 - r, y1])
    points.extend([x2, y1, x2, y1 + r])
    points.extend([x2, y2 - r])
    points.extend([x2, y2, x2 - r, y2])
    points.extend([x1 + r, y2])
    points.extend([x1, y2, x1, y2 - r])
    points.extend([x1, y1 + r])
    points.extend([x1, y1, x1 + r, y1])
    
    return canvas.create_polygon(points, smooth=True, **kwargs)


class CardFrame(ttk.Frame):
    """现代化卡片容器"""
    
    def __init__(self, parent: tk.Misc, title: str = "", **kwargs):
        bg = kwargs.pop('background', Theme.BG_CARD)
        super().__init__(parent, **kwargs)
        
        self.configure(style='Card.TFrame', padding=ModernStyles.PAD_CARD)
        
        if title:
            self.title_label = ttk.Label(self, text=title.upper(), style='CardTitle.TLabel')
            self.title_label.pack(anchor='w', pady=(0, 8))


class GradientBanner(ttk.Frame):
    """渐变标题横幅"""
    
    def __init__(self, parent: tk.Misc, title: str, subtitle: str = "", **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style='Banner.TFrame', padding=(20, 15))
        
        self.canvas = tk.Canvas(self, bg=Theme.BG_SECONDARY, highlightthickness=0, height=50)
        self.canvas.pack(fill='x', expand=True)
        
        self._draw_gradient()
        
        self.canvas.create_text(15, 25, text=title, anchor='w', 
                               font=ModernStyles.FONT_TITLE, fill=Theme.TEXT_PRIMARY)
        if subtitle:
            self.canvas.create_text(15, 45, text=subtitle, anchor='w',
                                 font=ModernStyles.FONT_SMALL, fill=Theme.TEXT_SECONDARY)
    
    def _draw_gradient(self) -> None:
        """绘制渐变背景"""
        width = 800
        colors = Theme.gradient(width, 50)
        segment_width = width / len(colors)
        
        for i, color in enumerate(colors):
            x = i * segment_width
            self.canvas.create_line(x, 0, x, 50, fill=color, width=segment_width + 1)


class StatusIndicator(ttk.Frame):
    """现代化状态指示器"""
    
    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style='Indicator.TFrame')
        
        self.canvas = tk.Canvas(self, width=12, height=12, bg=Theme.BG_PRIMARY,
                               highlightthickness=0)
        self.canvas.pack(side='left', padx=(0, 8))
        
        self._dot = self.canvas.create_oval(2, 2, 10, 10, fill=Theme.TEXT_MUTED, outline='')
        self._glow = self.canvas.create_oval(0, 0, 12, 12, fill='', outline='')
        
        self.status = False
    
    def set_running(self) -> None:
        """设置为运行状态"""
        self.status = True
        self.canvas.itemconfig(self._dot, fill=Theme.ACCENT_SUCCESS)
        self.canvas.itemconfig(self._glow, outline=Theme.ACCENT_SUCCESS, width=2)
    
    def set_stopped(self) -> None:
        """设置为停止状态"""
        self.status = False
        self.canvas.itemconfig(self._dot, fill=Theme.ACCENT_DANGER)
        self.canvas.itemconfig(self._glow, outline='')


class ModernTextWidget(ttk.Frame):
    """现代化文本控件（带圆角边框）"""
    
    def __init__(self, parent: tk.Misc, readonly: bool = False, **kwargs):
        height = kwargs.pop('height', 10)
        mono = kwargs.pop('mono', True)
        bg_color = kwargs.pop('bg', Theme.BG_PRIMARY)
        fg_color = kwargs.pop('fg', Theme.TEXT_PRIMARY)
        
        super().__init__(parent, **kwargs)
        self.configure(style='TextFrame.TFrame')
        
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0,
                               height=height * 15)
        self.canvas.pack(fill='both', expand=True)
        
        self._border = _create_rounded_rect(self.canvas, 0, 0, 400, height * 15,
                                           radius=6, fill=bg_color, outline=Theme.BORDER, width=1)
        
        self.text_widget = tk.Text(self.canvas, bg=bg_color, fg=fg_color,
                                  font=ModernStyles.FONT_MONO if mono else ModernStyles.FONT_BODY,
                                  wrap='word', relief='flat', borderwidth=0,
                                  insertbackground=Theme.TEXT_PRIMARY,
                                  selectbackground=Theme.ACCENT_PRIMARY,
                                  selectforeground='white',
                                  padx=10, pady=8,
                                  state='disabled' if readonly else 'normal')
        
        self._text_window = self.canvas.create_window(5, 5, anchor='nw',
                                                     window=self.text_widget,
                                                     width=390, height=height * 15 - 10)
        
        if readonly:
            self.text_widget.tag_configure('error', foreground='#ff7b72')
            self.text_widget.tag_configure('info', foreground=Theme.TEXT_PRIMARY)
            self.text_widget.tag_configure('success', foreground=Theme.ACCENT_SUCCESS)
    
    def insert(self, index: str, text: str, tags: str | None = None) -> None:
        self.text_widget.config(state='normal')
        self.text_widget.insert(index, text, tags)
        self.text_widget.config(state='disabled')
        self.text_widget.see('end')
    
    def delete(self, index1: str, index2: str = None) -> None:
        self.text_widget.config(state='normal')
        self.text_widget.delete(index1, index2)
        self.text_widget.config(state='disabled')


# ─── 系统托盘管理器 ─────────────────────────────────────────
class SystemTray:
    """系统托盘管理器 - 现代化图标"""
    
    def __init__(self, gui_app: 'LiveRecorderGUI'):
        self.gui = gui_app
        self.icon: pystray.Icon | None = None
        self.running = False
    
    def create_icon_image(self) -> Image.Image:
        """创建现代化托盘图标"""
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        draw.rounded_rectangle([(4, 4), (60, 60)], radius=12, fill='#1f6feb')
        
        draw.ellipse([(20, 18), (44, 42)], fill='white')
        draw.ellipse([(26, 24), (38, 36)], fill='#1f6feb')
        
        points = [(28, 48), (32, 54), (36, 48)]
        draw.polygon(points, fill='white')
        
        return img
    
    def on_show(self, _icon: pystray.Icon | None = None) -> None:
        if self.gui.root:
            self.gui.root.deiconify()
            self.gui.root.lift()
    
    def on_exit(self, _icon: pystray.Icon | None = None) -> None:
        self.gui.quit_application()
    
    def on_minimize(self, _icon: pystray.Icon | None = None) -> None:
        if self.gui.root:
            self.gui.root.withdraw()
    
    def run(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem('显示主界面', self.on_show, default=True),
            pystray.MenuItem('最小化到托盘', self.on_minimize),
            pystray.MenuItem('退出程序', self.on_exit)
        )
        
        self.icon = pystray.Icon(
            'LiveRecorder',
            self.create_icon_image(),
            '直播录制器',
            menu
        )
        self.running = True
        self.icon.run()
    
    def stop(self) -> None:
        if self.icon and self.running:
            self.icon.stop()
            self.running = False
    
    def notify(self, message: str, title: str = '直播录制器') -> None:
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass


# ─── 高级设置窗口 ───────────────────────────────────────────
class AdvancedSettingsWindow:
    """高级设置窗口 - 现代化风格"""
    
    def __init__(self, parent: tk.Toplevel | tk.Tk, config_file: str, log_callback: Any = None):
        self.config_file = config_file
        self.log_callback = log_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("高级设置")
        self.window.geometry("800x600")
        self.window.configure(bg=Theme.BG_PRIMARY)
        self.window.transient(parent)
        self.window.grab_set()
        
        self._center_window()
        self._setup_ui()
        self._load_config()
    
    def _center_window(self) -> None:
        self.window.update_idletasks()
        x = self.window.winfo_toplevel().winfo_x() + 100
        y = self.window.winfo_toplevel().winfo_y() + 50
        self.window.geometry(f"800x600+{x}+{y}")
    
    def _setup_ui(self) -> None:
        header = tk.Frame(self.window, bg=Theme.BG_SECONDARY, pady=15)
        header.pack(fill='x')
        
        tk.Label(header, text="⚙️ 配置文件编辑器", bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_PRIMARY, font=ModernStyles.FONT_SUBTITLE).pack(padx=20, anchor='w')
        
        content = ttk.Frame(self.window, padding=15)
        content.pack(fill='both', expand=True)
        
        card = CardFrame(content, title="config/config.ini")
        card.pack(fill='both', expand=True)
        
        text_frame = tk.Frame(card, bg=Theme.BG_PRIMARY)
        text_frame.pack(fill='both', expand=True, pady=(5, 10))
        
        self.config_text = tk.Text(text_frame, bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY,
                                   font=ModernStyles.FONT_MONO, wrap='word', relief='flat',
                                   insertbackground=Theme.TEXT_PRIMARY, padx=12, pady=10,
                                   highlightthickness=1, highlightcolor=Theme.ACCENT_PRIMARY,
                                   highlightbackground=Theme.BORDER)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.config_text.yview,
                                  style='Modern.Vertical.TScrollbar')
        self.config_text.configure(yscrollcommand=scrollbar.set)
        
        self.config_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        btn_frame = tk.Frame(self.window, bg=Theme.BG_SECONDARY, pady=12)
        btn_frame.pack(fill='x')
        
        save_btn = ttk.Button(btn_frame, text="💾 保存配置", command=self.save_config,
                             style='Start.TButton')
        save_btn.pack(side='left', padx=20)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=self.window.destroy,
                               style='Action.TButton')
        cancel_btn.pack(side='left')
    
    def _load_config(self) -> None:
        try:
            with open(self.config_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            self.config_text.delete('1.0', 'end')
            self.config_text.insert('1.0', content)
        except FileNotFoundError:
            self.config_text.insert('1.0', "# 配置文件不存在")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")
    
    def save_config(self) -> None:
        try:
            content = self.config_text.get('1.0', 'end-1c')
            with open(self.config_file, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            messagebox.showinfo("成功", "配置已保存！")
            if self.log_callback:
                self.log_callback("高级设置已保存")
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {e}")


def _save_text_widget_to_file(text_widget: tk.Text, file_path: str) -> None:
    content = text_widget.get('1.0', 'end-1c')
    if content and not content.endswith('\n'):
        content += '\n'
    with open(file_path, 'w', encoding='utf-8-sig') as f:
        f.write(content)


# ─── 主 GUI 类 ───────────────────────────────────────────────
class LiveRecorderGUI:
    """直播录制 GUI - 现代化界面"""
    
    ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')
    _MAX_LOG_LINES = 1000
    _LOG_TRIM_TO = 800
    _LOG_FLUSH_INTERVAL = 200
    _STATUS_REFRESH_INTERVAL = 10000
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("直播录制器")
        self.root.geometry("950x750")
        self.root.minsize(800, 600)
        self.root.configure(bg=Theme.BG_PRIMARY)
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.url_config_file = os.path.join(self.script_dir, "config", "URL_config.ini")
        self.main_config_file = os.path.join(self.script_dir, "config", "config.ini")
        self.downloads_dir = os.path.join(self.script_dir, "downloads")
        
        self._process_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._process_pid: int | None = None
        self._running = False
        
        self.output_thread: threading.Thread | None = None
        self.system_tray: SystemTray | None = None
        self.tray_thread: threading.Thread | None = None
        
        self._last_url_config_mtime = 0.0
        self._refresh_job_id: str | None = None
        self._status_cache_mtime = 0.0
        self._status_cache: tuple[str, str] | None = None
        
        self._log_queue: queue.Queue[list[tuple[str, str]] | None] = queue.Queue()
        self._log_flush_job_id: str | None = None
        self._log_queue_has_data = False
        
        ModernStyles.apply(self.root)
        self._setup_ui()
        self._load_config()
        self._schedule_log_flush()
        self._schedule_status_refresh()
    
    @property
    def process(self) -> subprocess.Popen[str] | None:
        with self._process_lock:
            return self._process
    
    @process.setter
    def process(self, value: subprocess.Popen[str] | None) -> None:
        with self._process_lock:
            self._process = value
    
    @property
    def process_pid(self) -> int | None:
        with self._process_lock:
            return self._process_pid
    
    @process_pid.setter
    def process_pid(self, value: int | None) -> None:
        with self._process_lock:
            self._process_pid = value
    
    @property
    def running(self) -> bool:
        with self._process_lock:
            return self._running
    
    @running.setter
    def running(self, value: bool) -> None:
        with self._process_lock:
            self._running = value
    
    def _setup_ui(self) -> None:
        """构建现代化界面"""
        GradientBanner(self.root, "直播录制器", "多平台直播录制工具")
        
        main_content = ttk.Frame(self.root, padding=15)
        main_content.pack(fill='both', expand=True)
        
        self._build_control_section(main_content)
        self._build_url_section(main_content)
        self._build_log_section(main_content)
        self._build_status_bar()
    
    def _build_control_section(self, parent: ttk.Frame) -> None:
        """控制区域"""
        control_card = CardFrame(parent, title="控制台")
        control_card.pack(fill='x', pady=(0, 12))
        
        btn_row = ttk.Frame(control_card)
        btn_row.pack(fill='x')
        
        left_btns = ttk.Frame(btn_row)
        left_btns.pack(side='left')
        
        self.start_btn = ttk.Button(left_btns, text="▶  开始录制", command=self.start_recording,
                                   style='Start.TButton')
        self.start_btn.grid(row=0, column=0, padx=(0, 8))
        
        self.stop_btn = ttk.Button(left_btns, text="■  停止录制", command=self.stop_recording,
                                  style='Stop.TButton', state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=8)
        
        self.status_indicator = StatusIndicator(left_btns)
        self.status_indicator.grid(row=0, column=2, padx=(15, 5))
        
        self.status_label = ttk.Label(left_btns, text="等待开始", style='Body.TLabel')
        self.status_label.grid(row=0, column=3, padx=(5, 0))
        
        right_btns = ttk.Frame(btn_row)
        right_btns.pack(side='right')
        
        ttk.Button(right_btns, text="📂  打开目录", command=self.open_downloads_folder,
                  style='Action.TButton').grid(row=0, column=0, padx=6)
        
        ttk.Button(right_btns, text="⚙️  高级设置", command=self.open_advanced_settings,
                  style='Action.TButton').grid(row=0, column=1, padx=6)
        
        ttk.Button(right_btns, text="📥  最小化托盘", command=self.minimize_to_tray,
                  style='Tray.TButton').grid(row=0, column=2, padx=6)
        
        ttk.Button(right_btns, text="✕  退出程序", command=self.quit_application,
                  style='Exit.TButton').grid(row=0, column=3, padx=6)
    
    def _build_url_section(self, parent: ttk.Frame) -> None:
        """URL 配置区域"""
        url_card = CardFrame(parent, title="直播地址配置")
        url_card.pack(fill='both', expand=True, pady=(0, 12))
        
        hint_frame = tk.Frame(url_card, bg=Theme.BG_CARD)
        hint_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(hint_frame, text="💡 格式: 每行一个链接，支持 # 注释 | 支持画质,链接,主播:名称",
                bg=Theme.BG_CARD, fg=Theme.TEXT_SECONDARY,
                font=ModernStyles.FONT_SMALL).pack(anchor='w', padx=5, pady=5)
        
        self.config_text = ModernTextWidget(url_card, height=8, bg=Theme.BG_PRIMARY)
        self.config_text.pack(fill='both', expand=True, padx=3, pady=3)
        
        btn_row = ttk.Frame(url_card)
        btn_row.pack(fill='x', pady=(8, 0))
        
        self.save_btn = ttk.Button(btn_row, text="💾 保存配置", command=self.save_config,
                                  style='Start.TButton')
        self.save_btn.pack(side='left', padx=5)
        
        self.reload_btn = ttk.Button(btn_row, text="🔄 重新读取", command=self._load_config,
                                    style='Action.TButton')
        self.reload_btn.pack(side='left', padx=5)
    
    def _build_log_section(self, parent: ttk.Frame) -> None:
        """日志显示区域"""
        log_card = CardFrame(parent, title="运行日志")
        log_card.pack(fill='both', expand=True)
        
        self.log_text = ModernTextWidget(log_card, height=12, readonly=True,
                                         bg='#0d1117', fg='#00ff00')
        self.log_text.pack(fill='both', expand=True, padx=3, pady=3)
    
    def _build_status_bar(self) -> None:
        """状态栏"""
        status_bar = tk.Frame(self.root, bg=Theme.BG_SECONDARY, pady=6)
        status_bar.pack(side='bottom', fill='x')
        
        self.status_var = tk.StringVar()
        self.status_label_widget = tk.Label(status_bar, textvariable=self.status_var,
                                          bg=Theme.BG_SECONDARY, fg=Theme.TEXT_SECONDARY,
                                          font=ModernStyles.FONT_SMALL, anchor='w')
        self.status_label_widget.pack(side='left', padx=15)
    
    def _load_config(self) -> None:
        config_dir = os.path.dirname(self.url_config_file)
        os.makedirs(config_dir, exist_ok=True)
        
        if not os.path.exists(self.url_config_file):
            with open(self.url_config_file, 'w', encoding='utf-8-sig') as f:
                f.write("")
        
        try:
            with open(self.url_config_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            current_content = self.config_text.text_widget.get('1.0', 'end-1c')
            if content == current_content:
                self._last_url_config_mtime = os.path.getmtime(self.url_config_file)
                return
            
            self.config_text.text_widget.config(state='normal')
            self.config_text.text_widget.delete('1.0', 'end')
            self.config_text.text_widget.insert('1.0', content)
            self.config_text.text_widget.config(state='disabled')
            self._last_url_config_mtime = os.path.getmtime(self.url_config_file)
        except Exception as e:
            self._log(f"加载配置失败: {e}", "error")
    
    def save_config(self) -> None:
        try:
            content = self.config_text.text_widget.get('1.0', 'end-1c')
            with open(self.url_config_file, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            self._last_url_config_mtime = os.path.getmtime(self.url_config_file)
            self._log("URL 配置已保存")
            messagebox.showinfo("成功", "配置已保存！")
        except Exception as e:
            self._log(f"保存配置失败: {e}", "error")
            messagebox.showerror("错误", f"保存失败: {e}")
    
    def _get_dynamic_status_info(self) -> tuple[str, str, str]:
        check_interval = "120秒"
        output_format = "ts"
        
        if not os.path.exists(self.main_config_file):
            return check_interval, output_format, self._tray_status_str()
        
        try:
            file_mtime = os.path.getmtime(self.main_config_file)
            if self._status_cache is not None and file_mtime == self._status_cache_mtime:
                ci, ofmt = self._status_cache
                return ci, ofmt, self._tray_status_str()
            
            config = configparser.ConfigParser()
            config.optionxform = lambda optionstr: optionstr
            config.read(self.main_config_file, encoding='utf-8-sig')
            
            if '录制设置' in config:
                interval = config['录制设置'].get('循环时间(秒)', '120')
                check_interval = f"{interval}秒"
                
                fmt = config['录制设置'].get('视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频', 'ts')
                output_format = fmt
            
            self._status_cache = (check_interval, output_format)
            self._status_cache_mtime = file_mtime
        except Exception:
            pass
        
        return check_interval, output_format, self._tray_status_str()
    
    def _tray_status_str(self) -> str:
        return "已启用" if self.system_tray and self.system_tray.running else "未启动"
    
    def open_downloads_folder(self) -> None:
        downloads_path = self.downloads_dir
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path, exist_ok=True)
        
        try:
            if sys.platform == 'win32':
                os.startfile(downloads_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', downloads_path])
            else:
                subprocess.Popen(['xdg-open', downloads_path])
            self._log(f"已打开: {downloads_path}")
        except Exception as e:
            self._log(f"打开目录失败: {e}", "error")
    
    def open_advanced_settings(self) -> None:
        AdvancedSettingsWindow(self.root, self.main_config_file, self._log)
    
    def start_recording(self) -> None:
        if self.process is not None:
            messagebox.showwarning("警告", "录制已在运行中！")
            return
        
        try:
            main_py = os.path.join(self.script_dir, "main.py")
            
            startupinfo = None
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            
            proc = subprocess.Popen(
                [sys.executable, main_py],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                cwd=self.script_dir,
                env=env,
                startupinfo=startupinfo,
                creationflags=creation_flags
            )
            
            self.process = proc
            self.process_pid = proc.pid
            self.running = True
            self.start_btn.state(['disabled'])
            self.stop_btn.state(['!disabled'])
            
            self.status_indicator.set_running()
            self.status_label.config(text="正在录制...")
            self._update_status_bar()
            
            self.output_thread = threading.Thread(target=self._read_output, daemon=True)
            self.output_thread.start()
            
            self._log("─" * 50)
            self._log(f"[{self._get_timestamp()}] 录制已启动 (PID: {proc.pid})")
            self._log(f"Python: {sys.executable}")
            self._log("─" * 50)
            
        except Exception as e:
            self._log(f"启动失败: {e}", "error")
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def stop_recording(self) -> None:
        proc = self.process
        pid = self.process_pid
        
        if proc is None:
            messagebox.showwarning("警告", "没有正在运行的录制进程！")
            return
        
        self._log(f"[{self._get_timestamp()}] 正在停止录制...")
        
        if sys.platform == 'win32':
            proc.terminate()
        else:
            import signal
            os.kill(proc.pid, signal.SIGINT)
        
        def _wait_and_update_ui() -> None:
            terminated = False
            try:
                proc.wait(timeout=3)
                terminated = True
                self._log("进程已优雅退出")
            except subprocess.TimeoutExpired:
                self._log("进程未能及时退出，尝试强制终止...")
            
            if not terminated and proc.poll() is None:
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                    self._log("进程已强制终止")
                except subprocess.TimeoutExpired:
                    self._log("警告：进程可能仍在运行！")
                except Exception as e:
                    self._log(f"强制终止失败: {e}")
            
            self.running = False
            self.process = None
            self.process_pid = None
            
            self.root.after(0, self._on_recording_stopped)
        
        threading.Thread(target=_wait_and_update_ui, daemon=True).start()
    
    def _on_recording_stopped(self) -> None:
        self.start_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])
        self.status_indicator.set_stopped()
        self.status_label.config(text="等待开始")
        self._update_status_bar()
        self._log(f"[{self._get_timestamp()}] 录制已停止")
        self._log("─" * 50)
        self._flush_log_queue()
    
    def _read_output(self) -> None:
        batch: list[tuple[str, str]] = []
        batch_size = 10
        
        def flush_batch() -> None:
            nonlocal batch
            if batch:
                self._log_queue.put(batch)
                self._log_queue_has_data = True
                if self._log_flush_job_id is None:
                    self._log_flush_job_id = self.root.after(self._LOG_FLUSH_INTERVAL, self._schedule_log_flush)
                batch = []
        
        while True:
            proc = self.process
            if proc is None or proc.stdout is None:
                flush_batch()
                self._log_queue.put(None)
                self._log_queue_has_data = True
                break
            
            try:
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        flush_batch()
                        self.running = False
                        self._log_queue.put(None)
                        self._log_queue_has_data = True
                        break
                    continue
                
                clean_line = self.ANSI_ESCAPE_PATTERN.sub('', line.rstrip())
                batch.append((clean_line, "info"))
                
                if len(batch) >= batch_size:
                    flush_batch()
            
            except (ValueError, OSError) as e:
                error_msg = str(e)
                flush_batch()
                self._log_queue.put([(f"输出流已关闭: {error_msg}", "error")])
                self._log_queue.put(None)
                self._log_queue_has_data = True
                self.running = False
                break
            except Exception as e:
                error_msg = str(e)
                flush_batch()
                self._log_queue.put([(f"读取错误: {error_msg}", "error")])
                self._log_queue.put(None)
                self._log_queue_has_data = True
                self.running = False
                break
        
        flush_batch()
    
    def _schedule_log_flush(self) -> None:
        messages: list[tuple[str, str]] = []
        process_ended = False
        
        while True:
            try:
                item = self._log_queue.get_nowait()
                if item is None:
                    process_ended = True
                else:
                    messages.extend(item)
            except queue.Empty:
                break
        
        if messages:
            for message, level in messages:
                timestamp = self._get_timestamp()
                display_text = f"[{timestamp}] {message}\n"
                tag = level
                
                self.log_text.insert('end', display_text, tag)
            
            total_lines = int(self.log_text.text_widget.index('end-1c').split('.')[0])
            if total_lines > self._MAX_LOG_LINES:
                trim_count = total_lines - self._LOG_TRIM_TO
                self.log_text.text_widget.config(state='normal')
                self.log_text.text_widget.delete('1.0', f'{trim_count + 1}.0')
                self.log_text.text_widget.config(state='disabled')
            
            self.log_text.text_widget.see('end')
            self._log_queue_has_data = False
        
        if process_ended:
            self._process_ended()
        
        if self._log_queue_has_data or not self._log_queue.empty():
            self._log_flush_job_id = self.root.after(self._LOG_FLUSH_INTERVAL, self._schedule_log_flush)
        else:
            self._log_flush_job_id = None
    
    def _process_ended(self) -> None:
        self.running = False
        self.process = None
        self.process_pid = None
        self.start_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])
        
        self.status_indicator.set_stopped()
        self.status_label.config(text="等待开始")
        self._update_status_bar()
        
        self._log("─" * 50)
        self._log(f"[{self._get_timestamp()}] 录制进程已结束")
        self._log("─" * 50)
    
    def _log(self, message: str, level: str = "info") -> None:
        self._log_queue.put([(message, level)])
        self._log_queue_has_data = True
        if self._log_flush_job_id is None:
            self._log_flush_job_id = self.root.after(self._LOG_FLUSH_INTERVAL, self._schedule_log_flush)
    
    def _flush_log_queue(self) -> None:
        if self._log_flush_job_id:
            self.root.after_cancel(self._log_flush_job_id)
            self._log_flush_job_id = None
        self._schedule_log_flush()
        if self._log_queue_has_data or not self._log_queue.empty():
            self._log_flush_job_id = self.root.after(self._LOG_FLUSH_INTERVAL, self._schedule_log_flush)
    
    @staticmethod
    def _get_timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _update_status_bar(self) -> None:
        check_interval, output_format, tray_status = self._get_dynamic_status_info()
        
        pid = self.process_pid
        if pid is not None:
            status_text = f"运行中 (PID: {pid})  |  检测间隔: {check_interval}  |  格式: {output_format}  |  托盘: {tray_status}"
        else:
            status_text = f"等待中  |  检测间隔: {check_interval}  |  格式: {output_format}  |  托盘: {tray_status}"
        
        self.status_var.set(status_text)
    
    def _schedule_status_refresh(self) -> None:
        self._update_status_bar()
        self._watch_url_config()
        self._refresh_job_id = self.root.after(self._STATUS_REFRESH_INTERVAL, self._schedule_status_refresh)
    
    def _watch_url_config(self) -> None:
        if not os.path.exists(self.url_config_file):
            return
        try:
            current_mtime = os.path.getmtime(self.url_config_file)
            if current_mtime != self._last_url_config_mtime:
                self._load_config()
        except OSError:
            pass
    
    def minimize_to_tray(self) -> None:
        self.root.withdraw()
        if self.system_tray:
            self.system_tray.notify('程序已最小化到系统托盘')
    
    def quit_application(self) -> None:
        if self.process is not None:
            if messagebox.askokcancel("退出确认", "录制正在后台进行，确定要退出吗？"):
                self.stop_recording()
            else:
                return
        
        self._log("正在清理...")
        threading.Thread(target=self._cleanup_zombie_ffmpeg, daemon=True).start()
        
        if self._log_flush_job_id:
            self.root.after_cancel(self._log_flush_job_id)
            self._log_flush_job_id = None
        
        if self._refresh_job_id:
            self.root.after_cancel(self._refresh_job_id)
            self._refresh_job_id = None
        
        if self.system_tray:
            self.system_tray.stop()
        
        self.root.quit()
        self.root.destroy()
    
    def _cleanup_zombie_ffmpeg(self) -> None:
        current_pid = os.getpid()
        
        try:
            if sys.platform == 'win32':
                subprocess.run(
                    ['taskkill', '/F', '/FI', 'IMAGENAME eq ffmpeg.exe', '/FI', f'PARENTPID eq {current_pid}'],
                    capture_output=True, timeout=3
                )
                self._log("ffmpeg 进程已清理")
            else:
                subprocess.run(
                    ['pkill', '-P', str(current_pid), '-x', 'ffmpeg'],
                    capture_output=True, timeout=3
                )
                self._log("ffmpeg 进程已清理")
        except Exception as e:
            self._log(f"清理进程: {e}")
    
    def on_closing(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("关闭选项")
        dialog.geometry("320x140")
        dialog.resizable(False, False)
        dialog.configure(bg=Theme.BG_SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 320) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 140) // 2
        dialog.geometry(f"320x140+{x}+{y}")
        
        tk.Label(dialog, text="请选择关闭方式：", bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_PRIMARY, font=ModernStyles.FONT_BODY).pack(pady=15)
        
        btn_frame = tk.Frame(dialog, bg=Theme.BG_SECONDARY)
        btn_frame.pack(pady=10)
        
        def minimize_and_close() -> None:
            self.minimize_to_tray()
            dialog.destroy()
        
        def quit_and_close() -> None:
            self.quit_application()
            dialog.destroy()
        
        btn1 = ttk.Button(btn_frame, text="📥 最小化到托盘", command=minimize_and_close,
                         style='Tray.TButton')
        btn1.grid(row=0, column=0, padx=8)
        
        btn2 = ttk.Button(btn_frame, text="✕ 彻底退出", command=quit_and_close,
                         style='Exit.TButton')
        btn2.grid(row=0, column=1, padx=8)


def main() -> None:
    root = tk.Tk()
    
    try:
        root.tk.call('tk', 'scaling', 1.5)
    except Exception:
        pass
    
    app = LiveRecorderGUI(root)
    
    app.system_tray = SystemTray(app)
    app.tray_thread = threading.Thread(target=app.system_tray.run, daemon=True)
    app.tray_thread.start()
    
    app.status_indicator.set_stopped()
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
