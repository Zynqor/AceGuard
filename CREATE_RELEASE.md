# 如何创建Release

## 🚀 通过GitHub网页创建Release（推荐）

### 步骤1：访问Releases页面

访问：
```
https://github.com/Zynqor/AceGuard/releases
```

### 步骤2：点击"Draft a new release"

在页面右上角找到绿色的 **"Draft a new release"** 按钮并点击。

### 步骤3：填写Release信息

**标签版本 (Tag):**
```
v1.0.0
```

**选择分支 (Target):**
```
claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT
```

**Release标题 (Title):**
```
v1.0.0 - 首个正式版本 🎉
```

**描述 (Description):**

复制粘贴 `RELEASE_NOTES_v1.0.0.md` 的内容

或者使用简化版：

```markdown
## AceGuard v1.0.0 - 首个正式版本

### ✨ 核心功能

- 🎯 基于路径的精确进程监控
- 🎨 Win11浅色风格界面
- ⚙️ CPU亲和性和优先级设置
- 📊 持续监控模式
- 💾 配置自动保存
- 🚀 开机自启动
- 📌 系统托盘

### 📦 下载

**推荐：** `AceGuard-Windows-x64.zip` (完整包)

或单独下载：
- `AceGuard.exe` - GUI版本（推荐）
- `AceGuard-CLI.exe` - 命令行版本

### 🚀 快速开始

1. 下载并解压
2. 以管理员身份运行 `AceGuard.exe`
3. 添加进程并设置限制
4. 开始监控

### ⚠️ 警告

使用本工具修改反作弊程序可能导致账号封禁！仅供学习研究。

### 💻 系统要求

- Windows 7/8/10/11 (64位)
- 管理员权限
- 无需Python环境

详细说明请查看压缩包内的文档。

---

**首个正式版本** - 功能完整、界面美观！
```

### 步骤4：发布

1. 确认信息无误
2. 点击底部的绿色 **"Publish release"** 按钮
3. 等待GitHub Actions自动构建（约5-10分钟）
4. 构建完成后，文件会自动上传到Release

## 🎯 Release会自动包含

GitHub Actions会自动编译并上传：
- ✅ `AceGuard-Windows-x64.zip` - 完整包
- ✅ `AceGuard.exe` - GUI版本
- ✅ `AceGuard-CLI.exe` - CLI版本

## 📝 检查构建状态

访问Actions页面查看构建进度：
```
https://github.com/Zynqor/AceGuard/actions
```

## ✅ 完成！

Release创建完成后，用户可以直接下载使用！

---

## 📌 重要提示

1. **分支选择**：必须选择正确的分支 `claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT`
2. **等待构建**：发布后等待Actions构建完成
3. **检查文件**：确认所有文件都已上传

## 🎊 发布后

- 分享Release链接
- 在README中更新下载链接
- 通知用户新版本发布

祝发布顺利！
