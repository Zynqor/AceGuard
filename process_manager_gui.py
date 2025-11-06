#!/usr/bin/env python3
"""
AceGuard 进程资源限制工具 - Win11风格GUI版本

带有Win11浅色风格的图形界面，支持基于进程路径的监控。
"""

import sys
import os
import time
import json
import threading
import ctypes
from typing import List, Optional, Dict
from enum import IntEnum
import winreg
from tkinter import filedialog

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    print("错误: 无法导入tkinter")
    sys.exit(1)

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# 导入核心功能
from process_manager import (
    ProcessManager, Priority, PRIORITY_MAP,
    check_admin, get_process_by_path,
    affinity_list_to_mask, mask_to_affinity_list
)


# Win11浅色主题配色
WIN11_COLORS = {
    'bg': '#F3F3F3',              # 主背景
    'card_bg': '#FFFFFF',         # 卡片背景
    'border': '#E5E5E5',          # 边框
    'text': '#1C1C1C',            # 主文字
    'text_secondary': '#6B6B6B',  # 次要文字
    'accent': '#0067C0',          # 强调色 - 更深的蓝
    'accent_hover': '#005A9E',    # 强调色悬停
    'success': '#0F7B0F',         # 成功 - 深绿
    'warning': '#F7630C',         # 警告 - 橙色
    'danger': '#C42B1C',          # 危险 - 深红
    'button_bg': '#FBFBFB',       # 按钮背景
    'button_hover': '#F5F5F5',    # 按钮悬停
}


class AutostartManager:
    """Windows开机自启动管理"""
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "AceGuardManager"

    @staticmethod
    def is_enabled() -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutostartManager.REG_PATH, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, AutostartManager.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False

    @staticmethod
    def enable(exe_path: str) -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutostartManager.REG_PATH, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, AutostartManager.APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}" --minimized')
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"启用开机自启动失败: {e}")
            return False

    @staticmethod
    def disable() -> bool:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AutostartManager.REG_PATH, 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, AutostartManager.APP_NAME)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return True
        except Exception as e:
            print(f"禁用开机自启动失败: {e}")
            return False


class ModernButton(tk.Canvas):
    """Win11风格的现代化按钮"""

    def __init__(self, parent, text="", command=None, width=120, height=36,
                 bg_color=None, fg_color=None, hover_color=None, **kwargs):
        self.bg_color = bg_color or WIN11_COLORS['accent']
        self.fg_color = fg_color or '#FFFFFF'
        self.hover_color = hover_color or WIN11_COLORS['accent_hover']
        self.command = command

        super().__init__(parent, width=width, height=height,
                        bg=WIN11_COLORS['card_bg'],
                        highlightthickness=0, **kwargs)

        # 绘制圆角矩形按钮
        self.rect = self.create_rectangle(2, 2, width-2, height-2,
                                          fill=self.bg_color,
                                          outline='',
                                          width=0)
        self.text_id = self.create_text(width//2, height//2,
                                       text=text,
                                       fill=self.fg_color,
                                       font=('Segoe UI', 10, 'bold'))

        # 绑定事件
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

    def _on_enter(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)
        self.config(cursor='hand2')

    def _on_leave(self, event):
        self.itemconfig(self.rect, fill=self.bg_color)
        self.config(cursor='')

    def _on_click(self, event):
        if self.command:
            self.command()


class ProcessManagerGUI:
    """Win11风格进程管理器GUI"""

    def __init__(self, start_minimized=False):
        self.root = tk.Tk()
        self.root.title("AceGuard 进程资源限制工具")
        self.root.geometry("1200x760")
        self.root.configure(bg=WIN11_COLORS['bg'])
        self.root.resizable(True, True)

        # 设置Win11风格
        self.setup_styles()

        # 检查管理员权限
        if not check_admin():
            messagebox.showerror(
                "权限错误",
                "需要管理员权限运行！\n\n请右键点击程序，选择'以管理员身份运行'。"
            )
            sys.exit(1)

        # 初始化进程管理器
        try:
            self.pm = ProcessManager()
        except Exception as e:
            messagebox.showerror("初始化错误", f"初始化进程管理器失败:\n{e}")
            sys.exit(1)

        # 配置数据
        self.config_file = "config.json"
        self.config = self.load_config()

        # 监控线程
        self.monitor_thread = None
        self.monitor_running = False
        self.monitor_interval = 5

        # 系统托盘
        self.tray_icon = None

        # 构建UI
        self.build_ui()

        # 加载保存的配置
        self.load_saved_processes()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 如果指定最小化启动
        if start_minimized:
            self.root.after(100, self.minimize_to_tray)

    def setup_styles(self):
        """配置Win11风格样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # Treeview样式
        style.configure("Modern.Treeview",
                       background=WIN11_COLORS['card_bg'],
                       foreground=WIN11_COLORS['text'],
                       fieldbackground=WIN11_COLORS['card_bg'],
                       borderwidth=0,
                       rowheight=28,
                       font=('Segoe UI', 10))
        style.configure("Modern.Treeview.Heading",
                       background=WIN11_COLORS['bg'],
                       foreground=WIN11_COLORS['text'],
                       borderwidth=1,
                       relief='flat',
                       font=('Segoe UI', 10, 'bold'))
        style.map('Modern.Treeview',
                 background=[('selected', WIN11_COLORS['accent'])],
                 foreground=[('selected', '#FFFFFF')])
        style.map('Modern.Treeview.Heading',
                 background=[('active', WIN11_COLORS['border'])])

    def build_ui(self):
        """构建用户界面"""
        # 顶部标题栏
        title_frame = tk.Frame(self.root, bg=WIN11_COLORS['card_bg'], height=64)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        # 标题
        title_label = tk.Label(
            title_frame,
            text="AceGuard 进程资源限制工具",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 18, 'bold')
        )
        title_label.pack(side=tk.LEFT, padx=24, pady=16)

        # 警告标签
        warning_label = tk.Label(
            title_frame,
            text="⚠ 仅供学习研究使用",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['warning'],
            font=('Segoe UI', 10)
        )
        warning_label.pack(side=tk.RIGHT, padx=24)

        # 分隔线
        separator = tk.Frame(self.root, bg=WIN11_COLORS['border'], height=1)
        separator.pack(fill=tk.X)

        # 主容器
        main_container = tk.Frame(self.root, bg=WIN11_COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # 左侧面板 - 进程列表
        left_panel = tk.Frame(main_container, bg=WIN11_COLORS['card_bg'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        # 左侧标题
        left_header = tk.Frame(left_panel, bg=WIN11_COLORS['card_bg'])
        left_header.pack(fill=tk.X, padx=20, pady=(16, 12))

        left_title = tk.Label(
            left_header,
            text="监控列表",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 13, 'bold')
        )
        left_title.pack(side=tk.LEFT)

        # 进程列表（Treeview）
        tree_container = tk.Frame(left_panel, bg=WIN11_COLORS['card_bg'])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))

        # 创建Treeview
        self.process_tree = ttk.Treeview(
            tree_container,
            columns=("path", "affinity", "priority", "status"),
            show="headings",
            style="Modern.Treeview",
            selectmode='browse'
        )

        # 设置列标题和宽度
        self.process_tree.heading("path", text="进程路径", anchor='w')
        self.process_tree.heading("affinity", text="CPU核心", anchor='center')
        self.process_tree.heading("priority", text="优先级", anchor='center')
        self.process_tree.heading("status", text="状态", anchor='center')

        # 设置列宽度和对齐
        self.process_tree.column("path", width=360, minwidth=200, anchor='w', stretch=True)
        self.process_tree.column("affinity", width=110, minwidth=80, anchor='center', stretch=False)
        self.process_tree.column("priority", width=110, minwidth=80, anchor='center', stretch=False)
        self.process_tree.column("status", width=90, minwidth=70, anchor='center', stretch=False)

        # 滚动条
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.process_tree.yview)
        self.process_tree.configure(yscrollcommand=scrollbar.set)

        self.process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮容器
        button_frame = tk.Frame(left_panel, bg=WIN11_COLORS['card_bg'])
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # 左侧按钮组
        left_buttons = tk.Frame(button_frame, bg=WIN11_COLORS['card_bg'])
        left_buttons.pack(side=tk.LEFT)

        self.add_btn = ModernButton(
            left_buttons,
            text="➕ 添加",
            command=self.add_process,
            width=100,
            height=38,
            bg_color=WIN11_COLORS['accent']
        )
        self.add_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.edit_btn = ModernButton(
            left_buttons,
            text="✏️ 编辑",
            command=self.edit_process,
            width=100,
            height=38,
            bg_color=WIN11_COLORS['button_bg'],
            fg_color=WIN11_COLORS['text'],
            hover_color=WIN11_COLORS['button_hover']
        )
        self.edit_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.delete_btn = ModernButton(
            left_buttons,
            text="🗑️ 删除",
            command=self.delete_process,
            width=100,
            height=38,
            bg_color=WIN11_COLORS['danger'],
            hover_color='#A81810'
        )
        self.delete_btn.pack(side=tk.LEFT)

        # 右侧面板 - 控制和日志
        right_panel = tk.Frame(main_container, bg=WIN11_COLORS['bg'], width=420)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_panel.pack_propagate(False)

        # 控制面板
        control_card = tk.Frame(right_panel, bg=WIN11_COLORS['card_bg'])
        control_card.pack(fill=tk.X, pady=(0, 12))

        control_header = tk.Frame(control_card, bg=WIN11_COLORS['card_bg'])
        control_header.pack(fill=tk.X, padx=20, pady=(16, 12))

        control_title = tk.Label(
            control_header,
            text="控制面板",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 13, 'bold')
        )
        control_title.pack(side=tk.LEFT)

        # 监控间隔设置
        interval_frame = tk.Frame(control_card, bg=WIN11_COLORS['card_bg'])
        interval_frame.pack(fill=tk.X, padx=20, pady=(0, 12))

        tk.Label(
            interval_frame,
            text="监控间隔:",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.interval_var = tk.StringVar(value="5")
        interval_spin = tk.Spinbox(
            interval_frame,
            from_=1,
            to=60,
            textvariable=self.interval_var,
            width=6,
            font=('Segoe UI', 10),
            bd=1,
            relief=tk.SOLID,
            buttonbackground=WIN11_COLORS['button_bg']
        )
        interval_spin.pack(side=tk.LEFT, padx=10)

        tk.Label(
            interval_frame,
            text="秒",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        # 状态显示
        status_frame = tk.Frame(control_card, bg=WIN11_COLORS['card_bg'])
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 16))

        tk.Label(
            status_frame,
            text="状态:",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="○ 未运行")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text_secondary'],
            font=('Segoe UI', 10, 'bold')
        )
        status_label.pack(side=tk.LEFT, padx=10)

        # 控制按钮 - 使用Grid布局，2行x2列
        btn_container = tk.Frame(control_card, bg=WIN11_COLORS['card_bg'])
        btn_container.pack(fill=tk.X, padx=20, pady=(0, 16))

        # 第一行
        self.start_btn = ModernButton(
            btn_container,
            text="▶ 开始监控",
            command=self.start_monitor,
            width=180,
            height=42,
            bg_color=WIN11_COLORS['success']
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 8), pady=(0, 8), sticky='ew')

        self.stop_btn = ModernButton(
            btn_container,
            text="⏸ 停止监控",
            command=self.stop_monitor,
            width=180,
            height=42,
            bg_color=WIN11_COLORS['danger']
        )
        self.stop_btn.grid(row=0, column=1, padx=(0, 0), pady=(0, 8), sticky='ew')

        # 第二行
        self.apply_btn = ModernButton(
            btn_container,
            text="🔄 立即应用",
            command=self.apply_once,
            width=180,
            height=42,
            bg_color=WIN11_COLORS['button_bg'],
            fg_color=WIN11_COLORS['text'],
            hover_color=WIN11_COLORS['button_hover']
        )
        self.apply_btn.grid(row=1, column=0, columnspan=2, pady=(0, 0), sticky='ew')

        # 配置grid权重
        btn_container.grid_columnconfigure(0, weight=1)
        btn_container.grid_columnconfigure(1, weight=1)

        # 其他功能按钮
        other_buttons = tk.Frame(control_card, bg=WIN11_COLORS['card_bg'])
        other_buttons.pack(fill=tk.X, padx=20, pady=(0, 20))

        if HAS_PYSTRAY:
            tray_btn = ModernButton(
                other_buttons,
                text="📌 最小化到托盘",
                command=self.minimize_to_tray,
                width=368,
                height=38,
                bg_color=WIN11_COLORS['button_bg'],
                fg_color=WIN11_COLORS['text'],
                hover_color=WIN11_COLORS['button_hover']
            )
            tray_btn.pack(pady=(0, 8))

        autostart_btn = ModernButton(
            other_buttons,
            text="🚀 开机自启动",
            command=self.toggle_autostart,
            width=368,
            height=38,
            bg_color=WIN11_COLORS['button_bg'],
            fg_color=WIN11_COLORS['text'],
            hover_color=WIN11_COLORS['button_hover']
        )
        autostart_btn.pack()

        # 日志面板
        log_card = tk.Frame(right_panel, bg=WIN11_COLORS['card_bg'])
        log_card.pack(fill=tk.BOTH, expand=True)

        log_header = tk.Frame(log_card, bg=WIN11_COLORS['card_bg'])
        log_header.pack(fill=tk.X, padx=20, pady=(16, 12))

        log_title = tk.Label(
            log_header,
            text="运行日志",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 13, 'bold')
        )
        log_title.pack(side=tk.LEFT)

        # 日志文本框
        log_frame = tk.Frame(log_card, bg=WIN11_COLORS['card_bg'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Consolas', 9),
            bg='#FAFAFA',
            fg=WIN11_COLORS['text'],
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 清空日志按钮
        clear_btn = ModernButton(
            log_card,
            text="🗑️ 清空日志",
            command=self.clear_log,
            width=368,
            height=38,
            bg_color=WIN11_COLORS['button_bg'],
            fg_color=WIN11_COLORS['text'],
            hover_color=WIN11_COLORS['button_hover']
        )
        clear_btn.pack(padx=20, pady=(0, 20))

        # 初始日志
        self.log("✓ 程序已启动")
        self.log("✓ 管理员权限检查通过")
        self.log("等待添加监控进程...")

    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            pass
        return {"processes": []}

    def save_config(self):
        """保存配置到文件"""
        try:
            processes = []
            for item in self.process_tree.get_children():
                values = self.process_tree.item(item)['values']
                try:
                    affinity = [int(x.strip()) for x in values[1].strip('[]').split(',')]
                except:
                    affinity = []

                processes.append({
                    "path": values[0],
                    "affinity": affinity,
                    "priority": values[2]
                })

            config = {"processes": processes}

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.log("✓ 配置已保存")
            return True
        except Exception as e:
            self.log(f"✗ 保存配置失败: {e}")
            return False

    def load_saved_processes(self):
        """加载保存的进程配置"""
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        for proc in self.config.get('processes', []):
            affinity = proc.get('affinity', [])
            path = proc.get('path', '')

            self.process_tree.insert('', tk.END, values=(
                path,
                str(affinity),
                proc.get('priority', 'NORMAL'),
                '待检测'
            ))

    def add_process(self):
        """添加新进程"""
        dialog = ProcessEditDialog(self.root, "添加进程")
        if dialog.result:
            self.process_tree.insert('', tk.END, values=(
                dialog.result['path'],
                str(dialog.result['affinity']),
                dialog.result['priority'],
                '待检测'
            ))
            self.save_config()
            self.log(f"✓ 已添加: {os.path.basename(dialog.result['path'])}")

    def edit_process(self):
        """编辑选中的进程"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个进程")
            return

        item = selection[0]
        values = self.process_tree.item(item)['values']

        try:
            affinity = [int(x.strip()) for x in values[1].strip('[]').split(',')]
        except:
            affinity = [0]

        dialog = ProcessEditDialog(
            self.root,
            "编辑进程",
            path=values[0],
            affinity=affinity,
            priority=values[2]
        )

        if dialog.result:
            self.process_tree.item(item, values=(
                dialog.result['path'],
                str(dialog.result['affinity']),
                dialog.result['priority'],
                '待检测'
            ))
            self.save_config()
            self.log(f"✓ 已更新: {os.path.basename(dialog.result['path'])}")

    def delete_process(self):
        """删除选中的进程"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个进程")
            return

        if messagebox.askyesno("确认", "确定要删除选中的进程吗？"):
            for item in selection:
                values = self.process_tree.item(item)['values']
                self.process_tree.delete(item)
                self.log(f"✓ 已删除: {os.path.basename(values[0])}")
            self.save_config()

    def start_monitor(self):
        """开始监控"""
        try:
            self.monitor_interval = int(self.interval_var.get())
        except:
            messagebox.showerror("错误", "监控间隔必须是数字")
            return

        if not self.process_tree.get_children():
            messagebox.showwarning("提示", "请先添加要监控的进程")
            return

        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.status_var.set("● 监控中")
        self.log("▶ 开始监控")

    def stop_monitor(self):
        """停止监控"""
        self.monitor_running = False
        self.status_var.set("○ 已停止")
        self.log("⏸ 监控已停止")

    def apply_once(self):
        """立即应用一次设置"""
        self.log("🔄 立即应用设置...")
        self.apply_settings()

    def monitor_loop(self):
        """监控循环"""
        while self.monitor_running:
            self.apply_settings()
            time.sleep(self.monitor_interval)

    def apply_settings(self):
        """应用设置到所有进程"""
        for item in self.process_tree.get_children():
            values = self.process_tree.item(item)['values']
            path = values[0]

            try:
                affinity = [int(x.strip()) for x in values[1].strip('[]').split(',')]
            except:
                affinity = []

            priority = values[2]

            # 根据路径查找进程
            pids = get_process_by_path(path)

            if pids:
                success = True
                for pid in pids:
                    if affinity:
                        mask = affinity_list_to_mask(affinity)
                        if not self.pm.set_affinity(pid, mask):
                            success = False

                    if priority:
                        priority_value = PRIORITY_MAP.get(priority.upper())
                        if priority_value:
                            if not self.pm.set_priority(pid, priority_value):
                                success = False

                status = "✓ 已应用" if success else "✗ 失败"
                self.process_tree.item(item, values=(path, values[1], priority, status))
                display_name = os.path.basename(path)
                self.log(f"[{time.strftime('%H:%M:%S')}] {display_name} (PID:{pids}) {status}")
            else:
                self.process_tree.item(item, values=(path, values[1], priority, "未运行"))

    def log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("✓ 日志已清空")

    def toggle_autostart(self):
        """切换开机自启动"""
        if AutostartManager.is_enabled():
            if messagebox.askyesno("开机自启动", "当前已启用，是否禁用？"):
                if AutostartManager.disable():
                    messagebox.showinfo("成功", "已禁用开机自启动")
                    self.log("✓ 已禁用开机自启动")
        else:
            if messagebox.askyesno("开机自启动", "是否启用开机自启动？"):
                exe_path = os.path.abspath(sys.argv[0])
                if AutostartManager.enable(exe_path):
                    messagebox.showinfo("成功", "已启用开机自启动")
                    self.log("✓ 已启用开机自启动")

    def minimize_to_tray(self):
        """最小化到系统托盘"""
        if not HAS_PYSTRAY:
            messagebox.showwarning("警告", "系统托盘功能不可用")
            return

        self.root.withdraw()

        if self.tray_icon is None:
            self.create_tray_icon()

    def create_tray_icon(self):
        """创建系统托盘图标"""
        image = Image.new('RGB', (64, 64), color=WIN11_COLORS['accent'])
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')

        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self.show_window),
            pystray.MenuItem("开始监控", self.start_monitor_from_tray),
            pystray.MenuItem("停止监控", self.stop_monitor_from_tray),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit_from_tray)
        )

        self.tray_icon = pystray.Icon("AceGuard", image, "AceGuard", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()

    def start_monitor_from_tray(self, icon=None, item=None):
        self.root.after(0, self.start_monitor)

    def stop_monitor_from_tray(self, icon=None, item=None):
        self.root.after(0, self.stop_monitor)

    def quit_from_tray(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.quit_app)

    def on_closing(self):
        """关闭窗口事件"""
        if HAS_PYSTRAY and messagebox.askyesnocancel("退出", "是否最小化到托盘？\n\n是=托盘\n否=退出"):
            self.minimize_to_tray()
        else:
            self.quit_app()

    def quit_app(self):
        """退出应用"""
        self.monitor_running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def run(self):
        """运行主循环"""
        self.root.mainloop()


class ProcessEditDialog:
    """进程编辑对话框 - Win11风格"""

    def __init__(self, parent, title, path="", affinity=None, priority="NORMAL"):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("620x420")
        self.dialog.configure(bg=WIN11_COLORS['bg'])
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 主容器
        container = tk.Frame(self.dialog, bg=WIN11_COLORS['card_bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # 标题
        title_label = tk.Label(
            container,
            text=title,
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 15, 'bold')
        )
        title_label.pack(pady=(12, 24))

        # 进程路径
        tk.Label(
            container,
            text="进程路径:",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 6))

        path_frame = tk.Frame(container, bg=WIN11_COLORS['card_bg'])
        path_frame.pack(fill=tk.X, pady=(0, 6))

        self.path_var = tk.StringVar(value=path)
        path_entry = tk.Entry(
            path_frame,
            textvariable=self.path_var,
            font=('Segoe UI', 10),
            relief=tk.SOLID,
            bd=1
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = ModernButton(
            path_frame,
            text="📁 浏览",
            command=self.browse_file,
            width=90,
            height=34,
            bg_color=WIN11_COLORS['accent']
        )
        browse_btn.pack(side=tk.RIGHT)

        tk.Label(
            container,
            text="例如: C:\\Program Files\\Game\\AceGuard.exe",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor=tk.W, pady=(0, 16))

        # CPU核心
        tk.Label(
            container,
            text="CPU核心 (逗号分隔):",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 6))

        affinity_str = ",".join(map(str, affinity)) if affinity else "0,1"
        self.affinity_var = tk.StringVar(value=affinity_str)
        affinity_entry = tk.Entry(
            container,
            textvariable=self.affinity_var,
            font=('Segoe UI', 10),
            relief=tk.SOLID,
            bd=1
        )
        affinity_entry.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            container,
            text="例如: 0,1,2,3 表示使用前4个核心",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text_secondary'],
            font=('Segoe UI', 9)
        ).pack(anchor=tk.W, pady=(0, 16))

        # 优先级
        tk.Label(
            container,
            text="优先级:",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text'],
            font=('Segoe UI', 10, 'bold')
        ).pack(anchor=tk.W, pady=(0, 6))

        self.priority_var = tk.StringVar(value=priority)
        priority_combo = ttk.Combobox(
            container,
            textvariable=self.priority_var,
            values=list(PRIORITY_MAP.keys()),
            state="readonly",
            font=('Segoe UI', 10)
        )
        priority_combo.pack(fill=tk.X, pady=(0, 6))

        # 优先级说明
        priority_desc = {
            "IDLE": "空闲 - 仅在系统空闲时运行",
            "BELOW_NORMAL": "低于正常",
            "NORMAL": "正常",
            "ABOVE_NORMAL": "高于正常",
            "HIGH": "高",
            "REALTIME": "实时 (危险！)"
        }

        desc_label = tk.Label(
            container,
            text="",
            bg=WIN11_COLORS['card_bg'],
            fg=WIN11_COLORS['text_secondary'],
            font=('Segoe UI', 9)
        )
        desc_label.pack(anchor=tk.W, pady=(0, 24))

        def update_desc(*args):
            desc_label.config(text=priority_desc.get(self.priority_var.get(), ""))

        self.priority_var.trace('w', update_desc)
        update_desc()

        # 按钮
        btn_frame = tk.Frame(container, bg=WIN11_COLORS['card_bg'])
        btn_frame.pack(pady=20)

        ok_btn = ModernButton(
            btn_frame,
            text="✓ 确定",
            command=self.ok,
            width=120,
            height=40,
            bg_color=WIN11_COLORS['success']
        )
        ok_btn.pack(side=tk.LEFT, padx=6)

        cancel_btn = ModernButton(
            btn_frame,
            text="✗ 取消",
            command=self.cancel,
            width=120,
            height=40,
            bg_color=WIN11_COLORS['button_bg'],
            fg_color=WIN11_COLORS['text'],
            hover_color=WIN11_COLORS['button_hover']
        )
        cancel_btn.pack(side=tk.LEFT, padx=6)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def browse_file(self):
        """浏览选择exe文件"""
        filename = filedialog.askopenfilename(
            title="选择可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if filename:
            self.path_var.set(filename)

    def ok(self):
        """确定按钮"""
        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("错误", "进程路径不能为空")
            return

        if not os.path.exists(path):
            if not messagebox.askyesno("警告", f"路径不存在:\n{path}\n\n是否仍然添加？"):
                return

        try:
            affinity_str = self.affinity_var.get().strip()
            affinity = [int(x.strip()) for x in affinity_str.split(',')]
            if not affinity:
                raise ValueError()
        except:
            messagebox.showerror("错误", "CPU核心格式错误\n\n请使用逗号分隔的数字")
            return

        priority = self.priority_var.get()

        self.result = {
            'path': path,
            'affinity': affinity,
            'priority': priority
        }

        self.dialog.destroy()

    def cancel(self):
        """取消按钮"""
        self.dialog.destroy()


def main():
    """主函数"""
    start_minimized = '--minimized' in sys.argv

    app = ProcessManagerGUI(start_minimized=start_minimized)
    app.run()


if __name__ == '__main__':
    main()
