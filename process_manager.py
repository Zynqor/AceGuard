#!/usr/bin/env python3
"""
AceGuard 进程资源限制工具

用于设置Windows进程的CPU亲和性和优先级，限制特定程序的资源占用。

⚠️ 警告：使用本工具修改反作弊程序可能导致账号封禁！
仅供学习研究使用，使用者需自行承担所有风险。
"""

import sys
import time
import json
import argparse
import ctypes
from typing import List, Optional, Dict
from enum import IntEnum

# 尝试导入psutil，提供更好的跨平台支持
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("警告: 未安装psutil库，某些功能可能受限")
    print("安装命令: pip install psutil")


# Windows优先级常量
class Priority(IntEnum):
    """Windows进程优先级"""
    IDLE = 0x40              # 空闲 - 仅在系统空闲时运行
    BELOW_NORMAL = 0x4000    # 低于正常
    NORMAL = 0x20            # 正常
    ABOVE_NORMAL = 0x8000    # 高于正常
    HIGH = 0x80              # 高
    REALTIME = 0x100         # 实时 - 危险！


# 优先级名称映射
PRIORITY_MAP = {
    "IDLE": Priority.IDLE,
    "BELOW_NORMAL": Priority.BELOW_NORMAL,
    "NORMAL": Priority.NORMAL,
    "ABOVE_NORMAL": Priority.ABOVE_NORMAL,
    "HIGH": Priority.HIGH,
    "REALTIME": Priority.REALTIME,
}


def check_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_process_by_name(process_name: str) -> List[int]:
    """
    根据进程名称获取所有匹配的进程PID

    Args:
        process_name: 进程名称，如 "AceGuard.exe"

    Returns:
        进程PID列表
    """
    pids = []

    if HAS_PSUTIL:
        # 使用psutil查找进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    else:
        # Windows平台使用ctypes直接调用Windows API
        if sys.platform == 'win32':
            import ctypes.wintypes as wintypes

            # 这里可以使用CreateToolhelp32Snapshot等API
            # 为简化示例，建议安装psutil
            print("请安装psutil以获得完整功能: pip install psutil")

    return pids


def affinity_list_to_mask(cores: List[int]) -> int:
    """
    将核心列表转换为亲和性掩码

    Args:
        cores: CPU核心列表，如 [0, 1, 2, 3]

    Returns:
        亲和性掩码（位图）

    Example:
        [0, 1] -> 0b11 = 3
        [0, 2, 4] -> 0b10101 = 21
    """
    mask = 0
    for core in cores:
        mask |= (1 << core)
    return mask


def mask_to_affinity_list(mask: int) -> List[int]:
    """
    将亲和性掩码转换为核心列表

    Args:
        mask: 亲和性掩码

    Returns:
        CPU核心列表
    """
    cores = []
    core = 0
    while mask:
        if mask & 1:
            cores.append(core)
        mask >>= 1
        core += 1
    return cores


class ProcessManager:
    """进程管理器 - 用于设置进程优先级和CPU亲和性"""

    def __init__(self):
        """初始化进程管理器"""
        if sys.platform != 'win32':
            raise OSError("本工具仅支持Windows平台")

        if not check_admin():
            raise PermissionError("需要管理员权限运行！请以管理员身份运行此程序。")

        # 加载Windows API
        self.kernel32 = ctypes.windll.kernel32

        # Windows常量
        self.PROCESS_SET_INFORMATION = 0x0200
        self.PROCESS_QUERY_INFORMATION = 0x0400

    def open_process(self, pid: int):
        """
        打开进程句柄

        Args:
            pid: 进程ID

        Returns:
            进程句柄
        """
        handle = self.kernel32.OpenProcess(
            self.PROCESS_SET_INFORMATION | self.PROCESS_QUERY_INFORMATION,
            False,
            pid
        )

        if not handle:
            raise OSError(f"无法打开进程 PID={pid}，错误代码: {ctypes.get_last_error()}")

        return handle

    def set_affinity(self, pid: int, affinity_mask: int) -> bool:
        """
        设置进程CPU亲和性

        Args:
            pid: 进程ID
            affinity_mask: CPU亲和性掩码

        Returns:
            是否成功
        """
        try:
            handle = self.open_process(pid)

            result = self.kernel32.SetProcessAffinityMask(handle, affinity_mask)
            self.kernel32.CloseHandle(handle)

            if result:
                cores = mask_to_affinity_list(affinity_mask)
                print(f"✓ 成功设置进程 {pid} 的CPU亲和性: 核心 {cores}")
                return True
            else:
                error = ctypes.get_last_error()
                print(f"✗ 设置进程 {pid} 的CPU亲和性失败，错误代码: {error}")
                return False

        except Exception as e:
            print(f"✗ 设置进程 {pid} 的CPU亲和性时出错: {e}")
            return False

    def set_priority(self, pid: int, priority: int) -> bool:
        """
        设置进程优先级

        Args:
            pid: 进程ID
            priority: 优先级（使用Priority枚举）

        Returns:
            是否成功
        """
        try:
            handle = self.open_process(pid)

            result = self.kernel32.SetPriorityClass(handle, priority)
            self.kernel32.CloseHandle(handle)

            if result:
                priority_name = [k for k, v in PRIORITY_MAP.items() if v == priority][0]
                print(f"✓ 成功设置进程 {pid} 的优先级: {priority_name}")
                return True
            else:
                error = ctypes.get_last_error()
                print(f"✗ 设置进程 {pid} 的优先级失败，错误代码: {error}")
                return False

        except Exception as e:
            print(f"✗ 设置进程 {pid} 的优先级时出错: {e}")
            return False

    def get_current_affinity(self, pid: int) -> Optional[List[int]]:
        """获取进程当前的CPU亲和性"""
        if HAS_PSUTIL:
            try:
                proc = psutil.Process(pid)
                return proc.cpu_affinity()
            except:
                pass
        return None

    def get_current_priority(self, pid: int) -> Optional[str]:
        """获取进程当前的优先级"""
        if HAS_PSUTIL:
            try:
                proc = psutil.Process(pid)
                nice = proc.nice()
                # psutil使用nice值，需要转换
                # 这是简化版本
                if nice == psutil.IDLE_PRIORITY_CLASS:
                    return "IDLE"
                elif nice == psutil.BELOW_NORMAL_PRIORITY_CLASS:
                    return "BELOW_NORMAL"
                elif nice == psutil.NORMAL_PRIORITY_CLASS:
                    return "NORMAL"
                elif nice == psutil.ABOVE_NORMAL_PRIORITY_CLASS:
                    return "ABOVE_NORMAL"
                elif nice == psutil.HIGH_PRIORITY_CLASS:
                    return "HIGH"
                elif nice == psutil.REALTIME_PRIORITY_CLASS:
                    return "REALTIME"
            except:
                pass
        return None

    def set_process_limits(self,
                          process_name: Optional[str] = None,
                          pid: Optional[int] = None,
                          affinity_mask: Optional[List[int]] = None,
                          priority: Optional[str] = None) -> bool:
        """
        设置进程的资源限制

        Args:
            process_name: 进程名称
            pid: 进程ID（如果指定则忽略process_name）
            affinity_mask: CPU核心列表，如 [0, 1, 2]
            priority: 优先级名称，如 "IDLE", "BELOW_NORMAL"

        Returns:
            是否成功
        """
        # 获取进程PID列表
        if pid:
            pids = [pid]
        elif process_name:
            pids = get_process_by_name(process_name)
            if not pids:
                print(f"✗ 未找到进程: {process_name}")
                return False
            print(f"找到 {len(pids)} 个匹配的进程: {pids}")
        else:
            print("✗ 必须指定process_name或pid")
            return False

        success = True

        # 对每个进程应用设置
        for pid in pids:
            print(f"\n处理进程 PID={pid}:")

            # 显示当前状态
            current_affinity = self.get_current_affinity(pid)
            current_priority = self.get_current_priority(pid)
            if current_affinity:
                print(f"  当前CPU亲和性: {current_affinity}")
            if current_priority:
                print(f"  当前优先级: {current_priority}")

            # 设置CPU亲和性
            if affinity_mask is not None:
                mask = affinity_list_to_mask(affinity_mask)
                if not self.set_affinity(pid, mask):
                    success = False

            # 设置优先级
            if priority is not None:
                priority_value = PRIORITY_MAP.get(priority.upper())
                if priority_value is None:
                    print(f"✗ 无效的优先级: {priority}")
                    success = False
                else:
                    if not self.set_priority(pid, priority_value):
                        success = False

        return success

    def monitor(self,
                config: Dict,
                interval: int = 5):
        """
        持续监控模式 - 定期检查并重新应用设置

        Args:
            config: 配置字典
            interval: 检查间隔（秒）
        """
        print(f"\n开始监控模式，每 {interval} 秒检查一次...")
        print("按 Ctrl+C 停止监控\n")

        try:
            while True:
                for process_config in config.get('processes', []):
                    name = process_config.get('name')
                    affinity = process_config.get('affinity')
                    priority = process_config.get('priority')

                    if name:
                        pids = get_process_by_name(name)
                        if pids:
                            print(f"[{time.strftime('%H:%M:%S')}] 检测到进程 {name}: {pids}")
                            for pid in pids:
                                if affinity:
                                    mask = affinity_list_to_mask(affinity)
                                    self.set_affinity(pid, mask)
                                if priority:
                                    priority_value = PRIORITY_MAP.get(priority.upper())
                                    if priority_value:
                                        self.set_priority(pid, priority_value)

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n监控已停止")


def load_config(config_file: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ 配置文件不存在: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ 配置文件格式错误: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AceGuard 进程资源限制工具 - 设置进程CPU亲和性和优先级',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用配置文件
  %(prog)s --config config.json

  # 设置单个进程
  %(prog)s --name AceGuard.exe --affinity 0,1 --priority IDLE

  # 持续监控模式
  %(prog)s --config config.json --monitor

  # 通过PID设置
  %(prog)s --pid 1234 --affinity 0,1,2,3 --priority BELOW_NORMAL

优先级选项:
  IDLE, BELOW_NORMAL, NORMAL, ABOVE_NORMAL, HIGH, REALTIME

⚠️  警告: 使用本工具可能导致游戏账号被封禁！仅供研究使用。
        """
    )

    parser.add_argument('--config', '-c',
                       help='配置文件路径 (JSON格式)')
    parser.add_argument('--name', '-n',
                       help='进程名称，如 AceGuard.exe')
    parser.add_argument('--pid', '-p', type=int,
                       help='进程ID')
    parser.add_argument('--affinity', '-a',
                       help='CPU核心列表，逗号分隔，如 0,1,2,3')
    parser.add_argument('--priority', '-P',
                       choices=['IDLE', 'BELOW_NORMAL', 'NORMAL', 'ABOVE_NORMAL', 'HIGH', 'REALTIME'],
                       help='进程优先级')
    parser.add_argument('--monitor', '-m', action='store_true',
                       help='启用持续监控模式')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='监控间隔（秒），默认5秒')

    args = parser.parse_args()

    # 检查参数
    if not args.config and not args.name and not args.pid:
        parser.print_help()
        sys.exit(1)

    # 显示警告
    print("=" * 70)
    print("⚠️  警告: 使用本工具修改反作弊程序可能导致账号封禁！")
    print("⚠️  仅供学习研究使用，使用者需自行承担所有风险。")
    print("=" * 70)
    print()

    try:
        pm = ProcessManager()

        if args.config:
            # 配置文件模式
            config = load_config(args.config)

            if args.monitor:
                # 持续监控
                pm.monitor(config, args.interval)
            else:
                # 单次应用
                for process_config in config.get('processes', []):
                    pm.set_process_limits(
                        process_name=process_config.get('name'),
                        affinity_mask=process_config.get('affinity'),
                        priority=process_config.get('priority')
                    )
        else:
            # 命令行模式
            affinity = None
            if args.affinity:
                affinity = [int(x.strip()) for x in args.affinity.split(',')]

            if args.monitor:
                # 监控模式
                config = {
                    'processes': [{
                        'name': args.name,
                        'affinity': affinity,
                        'priority': args.priority
                    }]
                }
                pm.monitor(config, args.interval)
            else:
                # 单次执行
                pm.set_process_limits(
                    process_name=args.name,
                    pid=args.pid,
                    affinity_mask=affinity,
                    priority=args.priority
                )

        print("\n✓ 操作完成")

    except PermissionError as e:
        print(f"\n✗ 权限错误: {e}")
        print("\n请以管理员身份运行此程序：")
        print("1. 右键点击命令提示符")
        print("2. 选择'以管理员身份运行'")
        print("3. 重新执行命令")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
