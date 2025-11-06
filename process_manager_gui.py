#!/usr/bin/env python3
"""
AceGuard 进程资源限制工具 - GUI版本

带有图形界面的Windows进程管理工具，支持系统托盘和开机自启动。
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
    print("警告: 未安装pystray，系统托盘功能将不可用")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("警告: 未安装psutil库")

# 导入核心功能
from process_manager import (
    ProcessManager, Priority, PRIORITY_MAP,
    check_admin, get_process_by_name,
    affinity_list_to_mask, mask_to_affinity_list
)


class AutostartManager:
    """Windows开机自启动管理"""

    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "AceGuardManager"

    @staticmethod
    def is_enabled() -> bool:
        """检查是否已启用开机自启动"""
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
        """启用开机自启动"""
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
        """禁用开机自启动"""
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


class ProcessManagerGUI:
    """进程管理器GUI主窗口"""

    def __init__(self, start_minimized=False):
        self.root = tk.Tk()
        self.root.title("AceGuard 进程资源限制工具")
        self.root.geometry("900x700")

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

    def build_ui(self):
        """构建用户界面"""
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="加载配置", command=self.load_config_file)
        file_menu.add_command(label="保存配置", command=self.save_config_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_app)

        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="开机自启动", command=self.toggle_autostart)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

        # 顶部警告区域
        warning_frame = tk.Frame(self.root, bg="#ff6b6b", padx=10, pady=5)
        warning_frame.pack(fill=tk.X)

        warning_label = tk.Label(
            warning_frame,
            text="⚠️ 警告: 使用本工具修改反作弊程序可能导致账号封禁！仅供学习研究使用。",
            bg="#ff6b6b",
            fg="white",
            font=("Arial", 10, "bold")
        )
        warning_label.pack()

        # 创建主容器
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：进程列表
        left_frame = tk.LabelFrame(main_frame, text="进程列表", padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 进程列表
        self.process_tree = ttk.Treeview(
            left_frame,
            columns=("name", "affinity", "priority", "status"),
            show="headings",
            height=15
        )
        self.process_tree.heading("name", text="进程名称")
        self.process_tree.heading("affinity", text="CPU核心")
        self.process_tree.heading("priority", text="优先级")
        self.process_tree.heading("status", text="状态")

        self.process_tree.column("name", width=200)
        self.process_tree.column("affinity", width=150)
        self.process_tree.column("priority", width=120)
        self.process_tree.column("status", width=80)

        self.process_tree.pack(fill=tk.BOTH, expand=True)

        # 进程列表按钮
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(btn_frame, text="➕ 添加", command=self.add_process, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="✏️ 编辑", command=self.edit_process, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ 删除", command=self.delete_process, width=10).pack(side=tk.LEFT, padx=2)

        # 右侧：控制面板和日志
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 控制面板
        control_frame = tk.LabelFrame(right_frame, text="控制面板", padx=10, pady=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 监控间隔设置
        interval_frame = tk.Frame(control_frame)
        interval_frame.pack(fill=tk.X, pady=5)

        tk.Label(interval_frame, text="监控间隔:").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="5")
        tk.Spinbox(
            interval_frame,
            from_=1,
            to=60,
            textvariable=self.interval_var,
            width=5
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(interval_frame, text="秒").pack(side=tk.LEFT)

        # 监控状态
        self.status_var = tk.StringVar(value="未运行")
        status_label = tk.Label(
            control_frame,
            textvariable=self.status_var,
            font=("Arial", 10, "bold")
        )
        status_label.pack(pady=5)

        # 控制按钮
        btn_control_frame = tk.Frame(control_frame)
        btn_control_frame.pack(fill=tk.X, pady=5)

        self.start_btn = tk.Button(
            btn_control_frame,
            text="▶️ 开始监控",
            command=self.start_monitor,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            btn_control_frame,
            text="⏸️ 停止监控",
            command=self.stop_monitor,
            bg="#f44336",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_control_frame,
            text="🔄 立即应用",
            command=self.apply_once,
            width=12
        ).pack(side=tk.LEFT, padx=5)

        # 系统托盘按钮
        if HAS_PYSTRAY:
            tk.Button(
                control_frame,
                text="📌 最小化到托盘",
                command=self.minimize_to_tray,
                width=20
            ).pack(pady=5)

        # 日志区域
        log_frame = tk.LabelFrame(right_frame, text="运行日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            width=50,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志按钮
        log_btn_frame = tk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(log_btn_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT)

        # 初始日志
        self.log("程序已启动，等待操作...")
        self.log(f"当前权限: 管理员 ✓")

    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"加载配置文件失败: {e}")

        return {"processes": []}

    def save_config(self):
        """保存配置到文件"""
        try:
            # 从树视图收集配置
            processes = []
            for item in self.process_tree.get_children():
                values = self.process_tree.item(item)['values']
                affinity_str = values[1]
                # 解析亲和性字符串
                try:
                    affinity = [int(x.strip()) for x in affinity_str.strip('[]').split(',')]
                except:
                    affinity = []

                processes.append({
                    "name": values[0],
                    "affinity": affinity,
                    "priority": values[2]
                })

            config = {"processes": processes}

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.log("配置已保存")
            return True
        except Exception as e:
            self.log(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败:\n{e}")
            return False

    def load_config_file(self):
        """从菜单加载配置文件"""
        self.config = self.load_config()
        self.load_saved_processes()
        self.log("配置已重新加载")

    def save_config_file(self):
        """从菜单保存配置文件"""
        if self.save_config():
            messagebox.showinfo("成功", "配置已保存到 config.json")

    def load_saved_processes(self):
        """加载保存的进程配置到列表"""
        # 清空现有列表
        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        # 加载进程
        for proc in self.config.get('processes', []):
            affinity = proc.get('affinity', [])
            self.process_tree.insert('', tk.END, values=(
                proc.get('name', ''),
                str(affinity),
                proc.get('priority', 'NORMAL'),
                '待检测'
            ))

    def add_process(self):
        """添加新进程"""
        dialog = ProcessEditDialog(self.root, "添加进程")
        if dialog.result:
            self.process_tree.insert('', tk.END, values=(
                dialog.result['name'],
                str(dialog.result['affinity']),
                dialog.result['priority'],
                '待检测'
            ))
            self.save_config()

    def edit_process(self):
        """编辑选中的进程"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个进程")
            return

        item = selection[0]
        values = self.process_tree.item(item)['values']

        # 解析亲和性
        try:
            affinity = [int(x.strip()) for x in values[1].strip('[]').split(',')]
        except:
            affinity = [0]

        dialog = ProcessEditDialog(
            self.root,
            "编辑进程",
            name=values[0],
            affinity=affinity,
            priority=values[2]
        )

        if dialog.result:
            self.process_tree.item(item, values=(
                dialog.result['name'],
                str(dialog.result['affinity']),
                dialog.result['priority'],
                '待检测'
            ))
            self.save_config()

    def delete_process(self):
        """删除选中的进程"""
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个进程")
            return

        if messagebox.askyesno("确认", "确定要删除选中的进程吗？"):
            for item in selection:
                self.process_tree.delete(item)
            self.save_config()

    def start_monitor(self):
        """开始监控"""
        try:
            self.monitor_interval = int(self.interval_var.get())
        except:
            messagebox.showerror("错误", "监控间隔必须是数字")
            return

        if not self.process_tree.get_children():
            messagebox.showwarning("警告", "请先添加要监控的进程")
            return

        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("监控中...")
        self.log("开始监控进程...")

    def stop_monitor(self):
        """停止监控"""
        self.monitor_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        self.log("监控已停止")

    def apply_once(self):
        """立即应用一次设置"""
        self.log("立即应用设置...")
        self.apply_settings()

    def monitor_loop(self):
        """监控循环（在后台线程运行）"""
        while self.monitor_running:
            self.apply_settings()
            time.sleep(self.monitor_interval)

    def apply_settings(self):
        """应用设置到所有配置的进程"""
        for item in self.process_tree.get_children():
            values = self.process_tree.item(item)['values']
            name = values[0]

            # 解析亲和性
            try:
                affinity = [int(x.strip()) for x in values[1].strip('[]').split(',')]
            except:
                affinity = []

            priority = values[2]

            # 查找进程
            pids = get_process_by_name(name)

            if pids:
                success = True
                for pid in pids:
                    # 设置亲和性
                    if affinity:
                        mask = affinity_list_to_mask(affinity)
                        if not self.pm.set_affinity(pid, mask):
                            success = False

                    # 设置优先级
                    if priority:
                        priority_value = PRIORITY_MAP.get(priority.upper())
                        if priority_value:
                            if not self.pm.set_priority(pid, priority_value):
                                success = False

                status = "✓ 已应用" if success else "✗ 失败"
                self.process_tree.item(item, values=(name, values[1], priority, status))
                self.log(f"[{time.strftime('%H:%M:%S')}] {name} (PID: {pids}) - {status}")
            else:
                self.process_tree.item(item, values=(name, values[1], priority, "未找到"))

    def log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def toggle_autostart(self):
        """切换开机自启动"""
        if AutostartManager.is_enabled():
            if messagebox.askyesno("开机自启动", "当前已启用开机自启动，是否禁用？"):
                if AutostartManager.disable():
                    messagebox.showinfo("成功", "已禁用开机自启动")
                    self.log("已禁用开机自启动")
                else:
                    messagebox.showerror("错误", "禁用开机自启动失败")
        else:
            if messagebox.askyesno("开机自启动", "是否启用开机自启动？\n\n程序将在系统启动时自动运行并最小化到托盘。"):
                exe_path = os.path.abspath(sys.argv[0])
                if AutostartManager.enable(exe_path):
                    messagebox.showinfo("成功", "已启用开机自启动")
                    self.log("已启用开机自启动")
                else:
                    messagebox.showerror("错误", "启用开机自启动失败")

    def minimize_to_tray(self):
        """最小化到系统托盘"""
        if not HAS_PYSTRAY:
            messagebox.showwarning("警告", "系统托盘功能不可用\n请安装: pip install pystray pillow")
            return

        self.root.withdraw()  # 隐藏主窗口

        if self.tray_icon is None:
            # 创建托盘图标
            self.create_tray_icon()

    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建一个简单的图标
        image = Image.new('RGB', (64, 64), color='#4CAF50')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')

        # 创建菜单
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self.show_window),
            pystray.MenuItem("开始监控", self.start_monitor_from_tray),
            pystray.MenuItem("停止监控", self.stop_monitor_from_tray),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit_from_tray)
        )

        self.tray_icon = pystray.Icon("AceGuard", image, "AceGuard 进程管理器", menu)

        # 在新线程中运行托盘图标
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """显示主窗口"""
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 置顶
        self.root.focus_force()  # 获取焦点

    def start_monitor_from_tray(self, icon=None, item=None):
        """从托盘启动监控"""
        self.root.after(0, self.start_monitor)

    def stop_monitor_from_tray(self, icon=None, item=None):
        """从托盘停止监控"""
        self.root.after(0, self.stop_monitor)

    def quit_from_tray(self, icon=None, item=None):
        """从托盘退出"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.quit_app)

    def on_closing(self):
        """关闭窗口事件"""
        if HAS_PYSTRAY and messagebox.askyesnocancel("退出", "是否最小化到托盘？\n\n是=最小化到托盘\n否=直接退出"):
            self.minimize_to_tray()
        else:
            self.quit_app()

    def quit_app(self):
        """退出应用"""
        self.monitor_running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于",
            "AceGuard 进程资源限制工具\n\n"
            "版本: 1.0.0\n"
            "作者: Zynqor\n\n"
            "功能:\n"
            "• 设置进程CPU亲和性\n"
            "• 设置进程优先级\n"
            "• 持续监控和自动应用\n"
            "• 系统托盘和开机自启动\n\n"
            "⚠️ 警告: 仅供学习研究使用！"
        )

    def run(self):
        """运行主循环"""
        self.root.mainloop()


class ProcessEditDialog:
    """进程编辑对话框"""

    def __init__(self, parent, title, name="", affinity=None, priority="NORMAL"):
        self.result = None

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 进程名称
        tk.Label(self.dialog, text="进程名称:").pack(pady=(10, 0))
        self.name_var = tk.StringVar(value=name)
        tk.Entry(self.dialog, textvariable=self.name_var, width=40).pack(pady=5)
        tk.Label(self.dialog, text="例如: AceGuard.exe", font=("Arial", 8), fg="gray").pack()

        # CPU亲和性
        tk.Label(self.dialog, text="CPU核心 (逗号分隔):").pack(pady=(10, 0))
        affinity_str = ",".join(map(str, affinity)) if affinity else "0,1"
        self.affinity_var = tk.StringVar(value=affinity_str)
        tk.Entry(self.dialog, textvariable=self.affinity_var, width=40).pack(pady=5)
        tk.Label(self.dialog, text="例如: 0,1,2,3 表示使用前4个核心", font=("Arial", 8), fg="gray").pack()

        # 优先级
        tk.Label(self.dialog, text="优先级:").pack(pady=(10, 0))
        self.priority_var = tk.StringVar(value=priority)
        priority_combo = ttk.Combobox(
            self.dialog,
            textvariable=self.priority_var,
            values=list(PRIORITY_MAP.keys()),
            state="readonly",
            width=37
        )
        priority_combo.pack(pady=5)

        # 优先级说明
        priority_desc = {
            "IDLE": "空闲 - 仅在系统空闲时运行",
            "BELOW_NORMAL": "低于正常",
            "NORMAL": "正常",
            "ABOVE_NORMAL": "高于正常",
            "HIGH": "高",
            "REALTIME": "实时 (危险！)"
        }

        desc_label = tk.Label(self.dialog, text="", font=("Arial", 8), fg="gray")
        desc_label.pack()

        def update_desc(*args):
            desc_label.config(text=priority_desc.get(self.priority_var.get(), ""))

        self.priority_var.trace('w', update_desc)
        update_desc()

        # 按钮
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="确定", command=self.ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=self.cancel, width=10).pack(side=tk.LEFT, padx=5)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self.dialog.wait_window()

    def ok(self):
        """确定按钮"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("错误", "进程名称不能为空")
            return

        # 解析亲和性
        try:
            affinity_str = self.affinity_var.get().strip()
            affinity = [int(x.strip()) for x in affinity_str.split(',')]
            if not affinity:
                raise ValueError()
        except:
            messagebox.showerror("错误", "CPU核心格式错误\n\n请使用逗号分隔的数字，例如: 0,1,2,3")
            return

        priority = self.priority_var.get()

        self.result = {
            'name': name,
            'affinity': affinity,
            'priority': priority
        }

        self.dialog.destroy()

    def cancel(self):
        """取消按钮"""
        self.dialog.destroy()


def main():
    """主函数"""
    # 检查命令行参数
    start_minimized = '--minimized' in sys.argv

    # 创建并运行GUI
    app = ProcessManagerGUI(start_minimized=start_minimized)
    app.run()


if __name__ == '__main__':
    main()
