# 🚀 快速创建 Release 指南

## 方法1: 通过GitHub网页（推荐 - 最简单）

### 步骤：

1. **打开Release创建页面**
   ```
   https://github.com/Zynqor/AceGuard/releases/new
   ```

2. **填写以下信息：**

   - **Choose a tag**: 输入 `v1.0.0` 并点击 "Create new tag: v1.0.0 on publish"

   - **Target**: 选择分支 `claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT`

   - **Release title**:
     ```
     v1.0.0 - 首个正式版本 🎉
     ```

   - **Describe this release**: 复制以下内容（或直接复制 `RELEASE_NOTES_v1.0.0.md` 的内容）

3. **发布Release：**
   - 确保 "Set as the latest release" 已勾选
   - 点击 **"Publish release"** 按钮

4. **等待自动构建：**
   - GitHub Actions会自动开始构建（约5-10分钟）
   - 查看构建状态：https://github.com/Zynqor/AceGuard/actions
   - 构建完成后，可执行文件会自动上传到Release页面

---

## 方法2: 使用Python脚本（需要GitHub Token）

### 步骤：

1. **获取GitHub Personal Access Token:**
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token" -> "Generate new token (classic)"
   - 勾选 `repo` 权限
   - 点击 "Generate token" 并复制token

2. **运行脚本：**
   ```bash
   # 方式1: 通过环境变量
   export GITHUB_TOKEN=your_token_here
   python3 create_release.py

   # 方式2: 通过命令行参数
   python3 create_release.py your_token_here

   # 方式3: 通过git配置
   git config --global github.token your_token_here
   python3 create_release.py
   ```

---

## 方法3: 使用Git命令行

### 步骤：

1. **创建并推送tag:**
   ```bash
   git tag -a v1.0.0 -m "v1.0.0 - 首个正式版本"
   git push origin v1.0.0
   ```

2. **等待GitHub Actions自动创建Release**
   - 推送tag后，GitHub Actions会自动触发
   - 构建完成后会自动创建Release并上传文件

---

## Release描述内容（复制到GitHub）

```markdown
## ✨ 核心功能

- ✅ **Win11风格界面** - 现代化圆角按钮，专业配色
- ✅ **基于路径的监控** - 精确匹配进程可执行文件
- ✅ **CPU亲和性设置** - 限制进程使用的CPU核心
- ✅ **进程优先级设置** - 5个优先级级别可选
- ✅ **持续监控模式** - 自动重新应用设置，防止反作弊程序修改
- ✅ **系统托盘** - 最小化到系统托盘，后台运行
- ✅ **开机自启动** - 支持Windows开机自动启动
- ✅ **配置持久化** - 设置自动保存，重启后继续有效

## 📦 下载说明

**推荐下载：** `AceGuard-Windows-x64.zip` (包含完整文件和文档)

或者单独下载：
- `AceGuard.exe` - GUI图形界面版本（推荐）
- `AceGuard-CLI.exe` - 命令行版本

## 🚀 快速开始

1. 下载 `AceGuard-Windows-x64.zip`
2. 解压到任意目录
3. **以管理员身份运行** `AceGuard.exe`
4. 点击 "➕ 添加" 按钮
5. 选择要限制的进程exe文件（或手动输入路径）
6. 设置CPU核心和优先级
7. 点击 "▶ 开始监控"

## 🎨 界面优化

### v1.0.0 改进：
- ✅ 圆角按钮设计（6px圆角）
- ✅ 改善按钮颜色对比度
- ✅ 修复Treeview表头和内容对齐
- ✅ 优化控制按钮布局（Grid 2+1设计）
- ✅ 统一悬停效果
- ✅ 1200x760窗口尺寸

## ⚠️ 重要警告

**使用本工具修改反作弊程序（如AceGuard、EasyAntiCheat、BattlEye等）可能导致游戏账号被封禁！**

本工具设计初衷是用于：
- ✅ 学习Windows进程管理机制
- ✅ 研究CPU亲和性和优先级的影响
- ✅ 限制合法程序的资源占用
- ❌ **不推荐**用于修改反作弊程序

**使用者需自行承担所有风险！**

详细说明请查看 `WARNINGS.md`

## 📖 文档

- `README.md` - 完整使用说明和技术细节
- `WARNINGS.md` - 安全警告和风险说明
- `EXAMPLES.md` - 25+ 详细使用示例
- `config.json` - 配置文件示例

## 💻 系统要求

- **操作系统**: Windows 7/8/10/11 (64位)
- **权限要求**: 必须以管理员身份运行
- **依赖**: 无需安装Python或其他运行时

## 🔧 技术细节

- **语言**: Python 3.10
- **GUI框架**: Tkinter (Win11风格)
- **打包工具**: PyInstaller (单文件exe)
- **核心库**: psutil, pystray
- **Windows API**: SetProcessAffinityMask, SetPriorityClass

## 🐛 问题反馈

如遇到问题，请在 [Issues](https://github.com/Zynqor/AceGuard/issues) 页面反馈。

## 📄 许可证

本项目采用 MIT 许可证。

---

**感谢使用 AceGuard! 🎉**
```

---

## ⚡ 推荐使用方法1（网页方式）

这是最简单、最可靠的方式。只需要：
1. 打开链接
2. 填写信息
3. 点击发布
4. 等待自动构建完成

**预计总耗时：2分钟填写 + 10分钟构建 = 12分钟**

构建完成后，用户就可以直接下载 `AceGuard.exe` 使用了！
