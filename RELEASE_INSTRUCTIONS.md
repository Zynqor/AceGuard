# 发布新版本说明

## 如何发布新版本到Release

GitHub Actions已经配置好自动编译和发布功能。按照以下步骤操作：

### 步骤1: 合并代码到主分支

首先，将当前分支合并到主分支（如果有）：

```bash
# 切换到主分支
git checkout main  # 或 master

# 合并当前分支
git merge claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT

# 推送到远程
git push origin main
```

### 步骤2: 创建版本标签

```bash
# 确保在主分支上
git checkout main  # 或 master

# 创建标签 (版本号格式: v1.0.0)
git tag v1.0.0

# 推送标签到GitHub
git push origin v1.0.0
```

### 步骤3: 自动构建和发布

推送标签后，GitHub Actions会自动：

1. ✅ 在Windows环境编译代码
2. ✅ 生成 `AceGuard.exe`（GUI版本）
3. ✅ 生成 `AceGuard-CLI.exe`（命令行版本）
4. ✅ 打包成 `AceGuard-Windows-x64.zip`
5. ✅ 创建GitHub Release
6. ✅ 上传所有文件到Release

### 步骤4: 查看Release

访问仓库的Releases页面：
```
https://github.com/Zynqor/AceGuard/releases
```

你将看到新发布的版本，包含：
- AceGuard-Windows-x64.zip（完整包）
- AceGuard.exe（GUI版本）
- AceGuard-CLI.exe（CLI版本）

## 版本号规范

使用语义化版本号：`vMAJOR.MINOR.PATCH`

- `v1.0.0` - 初始发布
- `v1.1.0` - 新增功能
- `v1.0.1` - Bug修复

示例：
```bash
git tag v1.0.0   # 初始版本
git tag v1.1.0   # 添加新功能
git tag v1.0.1   # 修复bug
```

## 手动触发构建

也可以在GitHub网页上手动触发：

1. 进入仓库页面
2. 点击 "Actions" 标签
3. 选择 "Build and Release" 工作流
4. 点击 "Run workflow"
5. 选择分支
6. 点击绿色的 "Run workflow" 按钮

注意：手动触发不会创建Release，只会生成构建产物。

## 常见问题

### Q: 如何修改Release说明？

A: 在 `.github/workflows/build-release.yml` 文件的 `body:` 部分修改。

### Q: 构建失败怎么办？

A: 检查GitHub Actions日志：
1. 进入 Actions 页面
2. 点击失败的工作流
3. 查看详细日志
4. 修复问题后重新推送标签

### Q: 如何删除错误的Release？

A:
```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push --delete origin v1.0.0

# 在GitHub上手动删除Release
```

### Q: 如何测试构建？

A: 使用本地构建：
```bash
pip install -r requirements.txt
pyinstaller build.spec
pyinstaller build_cli.spec
```

## 下一步

创建标签后，等待几分钟让GitHub Actions完成构建。

检查进度：
```
https://github.com/Zynqor/AceGuard/actions
```

完成后下载测试：
```
https://github.com/Zynqor/AceGuard/releases
```

祝发布顺利！🎉
