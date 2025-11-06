# 🚀 快速参考卡片

## 📍 重要链接

| 项目 | 链接 |
|------|------|
| **仓库主页** | https://github.com/Zynqor/AceGuard |
| **Actions构建** | https://github.com/Zynqor/AceGuard/actions |
| **Releases下载** | https://github.com/Zynqor/AceGuard/releases |
| **Issues反馈** | https://github.com/Zynqor/AceGuard/issues |

## 📦 快速下载

### 当前状态
- ✅ 代码已全部推送
- ✅ GitHub Actions已配置
- ⏳ 等待构建完成（约5-10分钟）

### 下载构建产物

#### 方法1：从Actions下载（开发版本）
1. 访问：https://github.com/Zynqor/AceGuard/actions
2. 点击最新的成功构建
3. 下载底部的 Artifacts
4. 解压使用

#### 方法2：创建Release（正式版本）
1. 访问：https://github.com/Zynqor/AceGuard/releases
2. 点击 "Draft a new release"
3. 填写：
   - Tag: `v1.0.0`
   - Target: `claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT`
   - Title: `v1.0.0 - 首次发布`
4. 发布后自动构建

## ⚡ 快速使用

### GUI版本（推荐）

```
1. 右键 → 以管理员身份运行 AceGuard.exe
2. 点击"添加"
3. 输入：
   - 进程名称: AceGuard.exe
   - CPU核心: 0,1
   - 优先级: IDLE
4. 点击"开始监控"
```

### 命令行版本

```bash
# 单次应用
AceGuard-CLI.exe --name "AceGuard.exe" --affinity 0,1 --priority IDLE

# 持续监控
AceGuard-CLI.exe --config config.json --monitor
```

## 🎯 常用配置

### 严格限制（推荐用于反作弊程序）
```json
{
  "name": "AceGuard.exe",
  "affinity": [0],        // 只用1个核心
  "priority": "IDLE"      // 最低优先级
}
```

### 中等限制
```json
{
  "name": "Program.exe",
  "affinity": [0, 1],     // 使用2个核心
  "priority": "BELOW_NORMAL"
}
```

### 轻度限制
```json
{
  "name": "Service.exe",
  "affinity": [0, 1, 2, 3],  // 使用4个核心
  "priority": "NORMAL"
}
```

## 📚 文档速查

| 问题 | 查看文档 |
|------|---------|
| 如何使用GUI？ | `USAGE_GUIDE.md` |
| 命令行示例？ | `EXAMPLES.md` |
| 有什么风险？ | `WARNINGS.md` |
| 如何构建？ | `BUILD.md` |
| 如何发布？ | `RELEASE_INSTRUCTIONS.md` |
| 功能说明？ | `README.md` |

## 🔧 故障排除

### 问题：Actions构建失败

**解决步骤：**
1. 进入 Actions 页面查看日志
2. 检查错误信息
3. 常见原因：
   - 依赖安装失败 → 检查 requirements.txt
   - 编译失败 → 检查 .spec 文件
   - 权限问题 → 检查 GitHub token

### 问题：无法下载Artifacts

**解决步骤：**
1. 确保构建成功（绿色勾号）
2. 滚动到构建页面底部
3. 查看 "Artifacts" 部分
4. 如果没有，检查workflow配置

### 问题：程序运行报错

**常见原因：**
- ❌ 没有管理员权限 → 右键"以管理员身份运行"
- ❌ 进程名称错误 → 检查任务管理器中的准确名称
- ❌ 杀毒软件拦截 → 添加到白名单

## ⚠️ 重要提醒

### 使用风险
- ❌ **可能导致游戏账号被封禁**
- ❌ **可能违反服务条款**
- ❌ **仅供学习研究使用**

### 安全使用
- ✅ 仅用于教育目的
- ✅ 不用于在线竞技游戏
- ✅ 自行承担所有风险

## 📊 项目文件一览

### 核心程序
- `process_manager.py` - 命令行版本
- `process_manager_gui.py` - GUI版本

### 配置文件
- `config.json` - 配置模板
- `build.spec` - GUI打包配置
- `build_cli.spec` - CLI打包配置

### 文档（7个）
- `README.md` - 主文档
- `USAGE_GUIDE.md` - 使用指南
- `EXAMPLES.md` - 示例集合
- `WARNINGS.md` - 安全警告
- `BUILD.md` - 构建说明
- `RELEASE_INSTRUCTIONS.md` - 发布说明
- `QUICK_REFERENCE.md` - 快速参考（本文档）

### CI/CD
- `.github/workflows/build-release.yml` - 自动构建

## 🎨 功能特性速览

| 功能 | GUI | CLI |
|------|-----|-----|
| CPU亲和性 | ✅ | ✅ |
| 优先级设置 | ✅ | ✅ |
| 持续监控 | ✅ | ✅ |
| 进程列表 | ✅ | ❌ |
| 实时日志 | ✅ | ✅ |
| 系统托盘 | ✅ | ❌ |
| 开机自启 | ✅ | ❌ |
| 配置文件 | ✅ | ✅ |

## 💡 使用技巧

### 1. 开机自动限制
- 启用GUI的"开机自启动"
- 添加要限制的进程
- 启动"持续监控"
- 最小化到托盘

### 2. 批量管理
- 直接编辑 `config.json`
- 添加多个进程配置
- 通过GUI或CLI加载

### 3. 临时测试
- 使用CLI的单次模式
- 不启动监控
- 观察效果后决定是否持续

## 🎯 下一步操作清单

- [ ] 访问 Actions 查看构建状态
- [ ] 等待构建完成（5-10分钟）
- [ ] 下载并测试exe文件
- [ ] 如果满意，创建正式Release
- [ ] 根据需要调整配置

## 📞 获取帮助

遇到问题？按以下顺序查找答案：

1. **查看文档** - 7个文档涵盖所有方面
2. **检查日志** - GUI右侧或命令行输出
3. **查看Issues** - 可能有人遇到相同问题
4. **提交Issue** - 详细描述问题和环境

## ✨ 项目统计

- **总代码**: 1,500+ 行
- **总文档**: 15,000+ 字
- **功能数量**: 15+ 个
- **示例数量**: 25+ 个
- **开发时间**: 1天
- **许可证**: MIT

---

**快速参考卡片 v1.0**

保存此文档以便快速查找信息！

如有疑问，查看 `USAGE_GUIDE.md` 获取详细说明。
