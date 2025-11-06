# 使用示例

本文档提供了各种使用场景的详细示例。

## 基础使用

### 1. 查看帮助信息

```bash
python process_manager.py --help
```

### 2. 检查是否有管理员权限

程序会自动检查，如果没有管理员权限会提示：

```
✗ 权限错误: 需要管理员权限运行！请以管理员身份运行此程序。
```

**解决方法**：
- Windows: 右键点击"命令提示符"或"PowerShell"，选择"以管理员身份运行"
- 然后再执行命令

## 命令行模式示例

### 3. 限制单个进程（按进程名）

限制AceGuard.exe只使用2个CPU核心（核心0和1），并设置为最低优先级：

```bash
python process_manager.py --name "AceGuard.exe" --affinity 0,1 --priority IDLE
```

输出示例：
```
======================================================================
⚠️  警告: 使用本工具修改反作弊程序可能导致账号封禁！
⚠️  仅供学习研究使用，使用者需自行承担所有风险。
======================================================================

找到 1 个匹配的进程: [1234]

处理进程 PID=1234:
  当前CPU亲和性: [0, 1, 2, 3, 4, 5, 6, 7]
  当前优先级: NORMAL
✓ 成功设置进程 1234 的CPU亲和性: 核心 [0, 1]
✓ 成功设置进程 1234 的优先级: IDLE

✓ 操作完成
```

### 4. 限制进程（按PID）

如果你知道进程的PID，可以直接指定：

```bash
python process_manager.py --pid 1234 --affinity 0,1,2,3 --priority BELOW_NORMAL
```

### 5. 只设置CPU亲和性

```bash
python process_manager.py --name "GameClient.exe" --affinity 0,2,4,6
```

这会将进程限制在偶数编号的CPU核心上。

### 6. 只设置优先级

```bash
python process_manager.py --name "Background.exe" --priority IDLE
```

### 7. 持续监控模式

程序会每5秒检查一次，如果发现目标进程就自动应用设置：

```bash
python process_manager.py --name "AceGuard.exe" --affinity 0,1 --priority IDLE --monitor
```

输出示例：
```
开始监控模式，每 5 秒检查一次...
按 Ctrl+C 停止监控

[14:30:15] 检测到进程 AceGuard.exe: [1234]
✓ 成功设置进程 1234 的CPU亲和性: 核心 [0, 1]
✓ 成功设置进程 1234 的优先级: IDLE

[14:30:20] 检测到进程 AceGuard.exe: [1234]
✓ 成功设置进程 1234 的CPU亲和性: 核心 [0, 1]
✓ 成功设置进程 1234 的优先级: IDLE
```

按 `Ctrl+C` 停止监控。

### 8. 自定义监控间隔

每10秒检查一次：

```bash
python process_manager.py --name "AceGuard.exe" --affinity 0,1 --priority IDLE --monitor --interval 10
```

## 配置文件模式示例

### 9. 使用默认配置文件

创建 `config.json`：

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

运行：

```bash
python process_manager.py --config config.json
```

### 10. 管理多个进程

`config.json`：

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
    },
    {
      "name": "GameGuard.exe",
      "affinity": [0, 1, 2, 3],
      "priority": "NORMAL"
    }
  ]
}
```

运行：

```bash
python process_manager.py --config config.json
```

### 11. 配置文件 + 监控模式

```bash
python process_manager.py --config config.json --monitor
```

这会持续监控配置文件中的所有进程。

### 12. 配置文件 + 自定义间隔

```bash
python process_manager.py --config config.json --monitor --interval 3
```

## CPU亲和性配置示例

### 13. 不同的CPU核心配置

假设你有8核CPU（核心0-7）：

**只使用第一个核心**：
```bash
--affinity 0
```

**使用前4个核心**：
```bash
--affinity 0,1,2,3
```

**只使用偶数核心**：
```bash
--affinity 0,2,4,6
```

**只使用奇数核心**：
```bash
--affinity 1,3,5,7
```

**使用除第一个核心外的所有核心**：
```bash
--affinity 1,2,3,4,5,6,7
```

**使用最后两个核心**：
```bash
--affinity 6,7
```

### 14. 为不同类型的程序设置不同策略

**限制反作弊程序（严格限制）**：
```json
{
  "name": "AntiCheat.exe",
  "affinity": [0],
  "priority": "IDLE"
}
```

**限制后台服务（中等限制）**：
```json
{
  "name": "Background.exe",
  "affinity": [0, 1, 2, 3],
  "priority": "BELOW_NORMAL"
}
```

**保持游戏高性能**：
```json
{
  "name": "Game.exe",
  "affinity": [4, 5, 6, 7],
  "priority": "HIGH"
}
```

## 优先级配置示例

### 15. 各优先级的使用场景

**IDLE（空闲）**：
```bash
--priority IDLE
```
- 仅在系统完全空闲时运行
- 适合：非关键后台任务、数据备份

**BELOW_NORMAL（低于正常）**：
```bash
--priority BELOW_NORMAL
```
- 低于正常优先级但仍会定期运行
- 适合：后台监控程序、日志服务

**NORMAL（正常）**：
```bash
--priority NORMAL
```
- 默认优先级
- 适合：大多数应用程序

**ABOVE_NORMAL（高于正常）**：
```bash
--priority ABOVE_NORMAL
```
- 略高于普通应用
- 适合：需要快速响应的应用

**HIGH（高）**：
```bash
--priority HIGH
```
- 高优先级
- 适合：实时应用、游戏

**REALTIME（实时）**：
```bash
--priority REALTIME
```
- ⚠️ **危险！不推荐使用！**
- 可能导致系统无响应
- 仅用于关键实时系统

## Python脚本集成示例

### 16. 在Python脚本中使用

创建 `my_script.py`：

```python
from process_manager import ProcessManager

# 创建管理器
pm = ProcessManager()

# 设置单个进程
pm.set_process_limits(
    process_name="AceGuard.exe",
    affinity_mask=[0, 1],
    priority="IDLE"
)

print("设置完成！")
```

### 17. 批量处理多个进程

```python
from process_manager import ProcessManager

pm = ProcessManager()

# 定义要处理的进程
processes = [
    {"name": "AceGuard.exe", "affinity": [0], "priority": "IDLE"},
    {"name": "EasyAntiCheat.exe", "affinity": [0, 1], "priority": "BELOW_NORMAL"},
]

# 批量应用
for proc in processes:
    pm.set_process_limits(
        process_name=proc["name"],
        affinity_mask=proc["affinity"],
        priority=proc["priority"]
    )
```

### 18. 定时任务

使用Windows任务计划程序在游戏启动时自动运行：

1. 创建批处理文件 `limit_aceguard.bat`：

```batch
@echo off
cd /d "%~dp0"
python process_manager.py --name "AceGuard.exe" --affinity 0,1 --priority IDLE --monitor --interval 5
```

2. 在任务计划程序中创建新任务：
   - 触发器：当特定程序启动时
   - 操作：运行 `limit_aceguard.bat`
   - 以管理员权限运行

## 高级应用场景

### 19. 为游戏优化（合理分配资源）

假设你有8核CPU，想要：
- 游戏使用核心4-7（4个核心）
- 反作弊程序限制在核心0-1（2个核心）
- 其他系统程序使用核心2-3（2个核心）

`config.json`：

```json
{
  "processes": [
    {
      "name": "Game.exe",
      "affinity": [4, 5, 6, 7],
      "priority": "HIGH"
    },
    {
      "name": "AntiCheat.exe",
      "affinity": [0, 1],
      "priority": "BELOW_NORMAL"
    }
  ]
}
```

### 20. 服务器资源管理

用于管理服务器上的多个服务：

```json
{
  "processes": [
    {
      "name": "database.exe",
      "affinity": [0, 1, 2, 3],
      "priority": "HIGH"
    },
    {
      "name": "webserver.exe",
      "affinity": [4, 5],
      "priority": "NORMAL"
    },
    {
      "name": "backup.exe",
      "affinity": [6],
      "priority": "IDLE"
    }
  ]
}
```

## 故障排除

### 21. 进程未找到

如果显示"未找到进程"：

1. 确认进程名称拼写正确（区分大小写）
2. 确认进程正在运行（打开任务管理器查看）
3. 尝试使用完整的进程名称，包括 `.exe` 扩展名

### 22. 权限被拒绝

如果显示权限错误：

1. 以管理员身份运行命令提示符/PowerShell
2. 某些系统进程可能受保护，无法修改
3. 反作弊程序可能有额外保护

### 23. 设置不生效

如果设置似乎不起作用：

1. 使用监控模式（`--monitor`）持续重新应用
2. 反作弊程序可能会恢复自己的设置
3. 某些程序可能拒绝或忽略优先级更改

## 安全建议

### 24. 测试配置

在应用到重要进程前，先在测试程序上验证：

```bash
# 测试一个简单的程序
python process_manager.py --name "notepad.exe" --affinity 0,1 --priority BELOW_NORMAL
```

### 25. 逐步调整

不要一次设置太严格的限制：

```bash
# 第一步：轻度限制
--affinity 0,1,2,3 --priority BELOW_NORMAL

# 如果没问题，再加强限制
--affinity 0,1 --priority IDLE
```

---

更多信息请参考 `README.md` 和 `WARNINGS.md`。
