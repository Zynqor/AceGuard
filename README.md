# AceGuard 进程资源限制工具

一个用于限制Windows进程CPU使用率和优先级的工具，可以防止某些程序（如反作弊软件）占用过多系统资源。

## ⚠️ 重要警告

**使用本工具修改反作弊程序（如AceGuard、EasyAntiCheat等）可能会：**
- 被检测为作弊行为
- 导致游戏账号被封禁
- 违反游戏服务条款
- 触发反作弊系统的保护机制

**本工具仅供学习研究使用，使用者需自行承担所有风险！**

## 功能特性

- ✅ 设置进程CPU亲和性（限制使用的CPU核心）
- ✅ 设置进程优先级（控制CPU时间分配）
- ✅ 支持按进程名称或PID操作
- ✅ 支持配置文件批量管理
- ✅ 持续监控模式，自动重新应用设置
- ✅ 需要管理员权限运行

## CPU亲和性和优先级说明

### CPU亲和性（Affinity）
- **作用**：限制进程只能在指定的CPU核心上运行
- **效果**：
  - 将进程限制在少数核心上，为其他程序留出资源
  - 例如：8核CPU中只允许使用核心0和1（2个核心）
  - 可以有效降低进程的最大CPU占用率

### 优先级（Priority）
- **作用**：控制操作系统调度器分配CPU时间的优先级
- **可用级别**：
  - `REALTIME` (实时) - 最高优先级，慎用！
  - `HIGH` (高)
  - `ABOVE_NORMAL` (高于正常)
  - `NORMAL` (正常) - 默认值
  - `BELOW_NORMAL` (低于正常)
  - `IDLE` (空闲) - 仅在系统空闲时运行
- **效果**：低优先级进程会在高优先级进程需要CPU时让出资源

## 系统要求

- Windows 7/8/10/11
- Python 3.7+
- 管理员权限

## 安装

```bash
# 克隆仓库
git clone https://github.com/Zynqor/AceGuard.git
cd AceGuard

# 安装依赖
pip install psutil
```

## 使用方法

### 方法1：配置文件模式（推荐）

1. 编辑 `config.json` 配置文件：

```json
{
  "processes": [
    {
      "name": "AceGuard.exe",
      "affinity": [0, 1],
      "priority": "IDLE"
    }
  ]
}
```

2. 以管理员身份运行：

```bash
python process_manager.py --config config.json --monitor
```

### 方法2：命令行模式

```bash
# 设置单个进程
python process_manager.py --name "AceGuard.exe" --affinity 0,1 --priority IDLE

# 持续监控模式（自动重新应用设置）
python process_manager.py --name "AceGuard.exe" --affinity 0,1 --priority IDLE --monitor
```

### 方法3：Python脚本调用

```python
from process_manager import ProcessManager

pm = ProcessManager()

# 设置进程
pm.set_process_limits(
    process_name="AceGuard.exe",
    affinity_mask=[0, 1],  # 只使用核心0和1
    priority="IDLE"        # 设置为最低优先级
)

# 持续监控模式
pm.monitor(interval=5)  # 每5秒检查一次
```

## 配置说明

### 亲和性配置
- `affinity`: CPU核心列表，例如 `[0, 1, 2, 3]` 表示只使用前4个核心
- 核心编号从0开始
- 可以使用任意组合，如 `[0, 2, 4, 6]` 只使用偶数核心

### 优先级配置
可选值：
- `REALTIME` - 实时（危险！可能导致系统不稳定）
- `HIGH` - 高
- `ABOVE_NORMAL` - 高于正常
- `NORMAL` - 正常
- `BELOW_NORMAL` - 低于正常
- `IDLE` - 空闲（推荐用于限制资源）

## 工作原理

1. **进程发现**：通过进程名称查找目标进程PID
2. **权限提升**：以管理员权限打开进程句柄
3. **应用设置**：
   - 使用 `SetProcessAffinityMask` 设置CPU亲和性
   - 使用 `SetPriorityClass` 设置优先级
4. **持续监控**（可选）：定期检查并重新应用设置

## 实际应用场景

### 限制反作弊程序
```json
{
  "processes": [
    {
      "name": "AceGuard.exe",
      "affinity": [0, 1],      // 只用2个核心
      "priority": "BELOW_NORMAL"  // 低优先级
    }
  ]
}
```

### 限制多个程序
```json
{
  "processes": [
    {
      "name": "AceGuard.exe",
      "affinity": [0],
      "priority": "IDLE"
    },
    {
      "name": "EasyAntiCheat.exe",
      "affinity": [0, 1],
      "priority": "BELOW_NORMAL"
    }
  ]
}
```

## 技术限制

1. **需要管理员权限**：修改其他进程需要提升权限
2. **反作弊对抗**：
   - 反作弊程序可能检测并恢复自己的设置
   - 可能将此行为标记为可疑操作
   - 建议使用监控模式持续重新应用
3. **受保护进程**：某些系统级进程可能无法修改
4. **封号风险**：使用本工具可能导致游戏账号被封禁

## 免责声明

本工具仅供教育和研究目的使用。作者不对使用本工具造成的任何后果负责，包括但不限于：
- 游戏账号被封禁
- 违反服务条款
- 系统不稳定
- 数据丢失

使用者需自行评估风险并承担所有后果。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 相关资源

- [Windows进程和线程函数文档](https://docs.microsoft.com/en-us/windows/win32/procthread/process-and-thread-functions)
- [psutil文档](https://psutil.readthedocs.io/)
