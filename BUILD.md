# 构建说明

## 自动构建（GitHub Actions）

本项目配置了GitHub Actions自动构建，每次推送标签时会自动编译并发布到Releases。

### 创建新版本发布

```bash
# 1. 确保所有更改已提交
git add .
git commit -m "准备发布 v1.0.0"

# 2. 创建标签
git tag v1.0.0

# 3. 推送标签
git push origin v1.0.0

# GitHub Actions会自动：
# - 编译Windows可执行文件
# - 创建ZIP压缩包
# - 发布到GitHub Releases
```

### 手动触发构建

也可以在GitHub仓库的 Actions 页面手动触发构建工作流。

## 本地构建

### Windows平台

#### 前置要求

1. 安装Python 3.7+
2. 安装依赖：

```bash
pip install -r requirements.txt
```

#### 构建GUI版本

```bash
pyinstaller build.spec
```

编译后的文件在 `dist/AceGuard.exe`

#### 构建CLI版本

```bash
pyinstaller build_cli.spec
```

编译后的文件在 `dist/AceGuard-CLI.exe`

#### 构建完整发布包

```bash
# Windows PowerShell
python -m pip install --upgrade pip
pip install -r requirements.txt

# 构建两个版本
pyinstaller build.spec
pyinstaller build_cli.spec

# 创建发布目录
mkdir dist\release

# 复制文件
Copy-Item dist\AceGuard.exe dist\release\
Copy-Item dist\AceGuard-CLI.exe dist\release\
Copy-Item config.json dist\release\
Copy-Item config.example.json dist\release\
Copy-Item README.md dist\release\
Copy-Item WARNINGS.md dist\release\
Copy-Item EXAMPLES.md dist\release\
Copy-Item LICENSE dist\release\

# 创建ZIP
Compress-Archive -Path dist\release\* -DestinationPath AceGuard-Windows-x64.zip
```

## PyInstaller配置说明

### build.spec (GUI版本)

- `console=False`: 不显示控制台窗口
- `uac_admin=True`: 请求管理员权限
- `upx=True`: 使用UPX压缩可执行文件
- 包含所有必要的依赖库

### build_cli.spec (CLI版本)

- `console=True`: 显示控制台窗口
- `uac_admin=True`: 请求管理员权限
- 适合命令行使用

## 常见问题

### 1. 编译失败：找不到模块

确保所有依赖都已安装：

```bash
pip install -r requirements.txt
```

### 2. 生成的exe文件太大

- 已启用UPX压缩
- 可以手动运行UPX进一步压缩：

```bash
upx --best --lzma dist\AceGuard.exe
```

### 3. Windows Defender报警

编译的exe可能被杀毒软件误报，这是正常的（因为请求管理员权限）。可以：

- 添加到白名单
- 使用代码签名证书签名（需要购买）

### 4. 在其他电脑上无法运行

确保：

- 目标系统是Windows 7/8/10/11 64位
- 以管理员身份运行
- 关闭杀毒软件或添加例外

## 版本号管理

遵循语义化版本规范：

- `v1.0.0` - 主版本.次版本.修订号
- 主版本：不兼容的API更改
- 次版本：向后兼容的功能新增
- 修订号：向后兼容的问题修正

## 发布检查清单

发布新版本前确认：

- [ ] 所有功能正常工作
- [ ] 更新了README.md
- [ ] 更新了EXAMPLES.md（如有新功能）
- [ ] 更新了版本号
- [ ] 测试了编译后的可执行文件
- [ ] 更新了CHANGELOG（如果有）
- [ ] 创建了Git标签
- [ ] 推送到GitHub

## 技术栈

- Python 3.10
- tkinter (GUI)
- psutil (进程管理)
- pystray (系统托盘)
- Pillow (图像处理)
- PyInstaller (打包)
- GitHub Actions (CI/CD)
