# 🔧 修复 GitHub Actions 权限错误

## ❌ 错误信息
```
Run softprops/action-gh-release@v1
⚠️ Unexpected error fetching GitHub release for tag refs/tags/v1.0.0:
HttpError: Resource not accessible by integration
Error: Resource not accessible by integration
```

## ✅ 已修复
我已经修复了workflow配置，添加了必要的权限：
```yaml
permissions:
  contents: write  # 允许创建Release和上传文件
```

## 🚀 现在请按以下方式重新触发构建

### 方法1: 重新运行失败的Workflow（最简单）

1. **访问Actions页面**：
   ```
   https://github.com/Zynqor/AceGuard/actions
   ```

2. **找到失败的workflow运行**
   - 点击失败的 "Build and Release" workflow

3. **重新运行**
   - 点击右上角的 "Re-run all jobs" 按钮
   - 或点击 "Re-run failed jobs"

4. **等待完成**
   - 这次应该能成功创建Release并上传文件
   - 约5-10分钟完成

---

### 方法2: 删除并重新创建Tag

如果方法1不行，使用这个方法：

#### 步骤A: 删除旧的Tag

1. **访问Tags页面**：
   ```
   https://github.com/Zynqor/AceGuard/tags
   ```

2. **找到 v1.0.0 tag**

3. **删除tag**：
   - 点击tag右侧的 "..." 菜单
   - 选择 "Delete tag"
   - 确认删除

#### 步骤B: 重新创建Tag

在项目目录执行以下命令：

```bash
# 创建tag
git tag -a v1.0.0 -m "v1.0.0 - 首个正式版本 🎉

✨ 核心功能:
- 基于路径的精确进程监控
- Win11浅色风格界面（圆角按钮）
- CPU亲和性和优先级设置
- 持续监控模式
- 配置自动保存
- 系统托盘和开机自启动

🎨 界面优化:
- 修复Treeview对齐问题
- 优化按钮布局和颜色对比度
- 6px圆角按钮
- 统一悬停效果

⚠️ 警告: 使用本工具修改反作弊程序可能导致账号封禁，仅供学习研究！"

# 推送tag（会自动触发workflow）
git push origin v1.0.0
```

如果遇到403错误，请在GitHub网页上操作：

1. **访问Releases创建页面**：
   ```
   https://github.com/Zynqor/AceGuard/releases/new
   ```

2. **填写信息**：
   - **Tag**: `v1.0.0`
   - **Target**: `claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT`
   - **Title**: `v1.0.0 - 首个正式版本 🎉`
   - **Description**: 复制 `RELEASE_NOTES_v1.0.0.md` 的内容

3. **创建Tag并发布**：
   - 确保 "Create a new tag: v1.0.0 on publish" 是选中状态
   - 点击 "Publish release"
   - 这会自动创建tag并触发workflow

---

### 方法3: 手动触发Workflow

1. **访问Actions页面**：
   ```
   https://github.com/Zynqor/AceGuard/actions
   ```

2. **选择workflow**：
   - 点击左侧的 "Build and Release"

3. **手动运行**：
   - 点击右侧的 "Run workflow" 按钮
   - 选择分支: `claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT`
   - 点击绿色的 "Run workflow" 按钮

4. **注意**：
   - 手动触发不会自动创建Release
   - 只会构建并上传artifacts
   - 如需Release，仍需手动在网页上创建

---

## 📊 验证修复成功

成功后你会看到：

1. **Workflow成功运行**
   - 绿色的✓标记

2. **Release自动创建**
   - 访问 https://github.com/Zynqor/AceGuard/releases
   - 看到 v1.0.0 Release

3. **文件自动上传**
   - `AceGuard-Windows-x64.zip`
   - `AceGuard.exe`
   - `AceGuard-CLI.exe`

---

## 💡 为什么会出现这个错误？

默认的 `GITHUB_TOKEN` 具有有限的权限。创建Release需要 `contents: write` 权限，这就是为什么我们需要在workflow中显式声明这个权限。

修复后的配置：
```yaml
permissions:
  contents: write  # 允许创建Release和上传文件
```

---

## 🎯 推荐操作

**最简单的方法是方法1** - 直接重新运行失败的workflow。

如果不行，使用**方法2的网页方式**创建Release，这样最可靠。

---

## 🆘 还有问题？

如果以上方法都不行，可以：

1. 检查仓库的Actions权限设置：
   - 访问仓库Settings → Actions → General
   - 确保 "Workflow permissions" 设置为 "Read and write permissions"

2. 查看详细的错误日志

3. 手动构建并上传（如果GitHub Actions一直有问题）

祝顺利！🚀
