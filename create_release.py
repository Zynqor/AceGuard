#!/usr/bin/env python3
"""
自动创建GitHub Release的脚本
"""

import os
import sys
import json
import subprocess
from urllib import request, error
from urllib.parse import urlencode

def get_github_token():
    """获取GitHub token"""
    # 尝试从环境变量获取
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        return token

    # 尝试从git config获取
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'github.token'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass

    return None

def create_github_release(token, owner, repo, tag, branch, name, body, use_proxy=False):
    """创建GitHub Release"""
    if use_proxy:
        # 使用本地代理
        url = f'http://127.0.0.1:61352/api/repos/{owner}/{repo}/releases'
    else:
        url = f'https://api.github.com/repos/{owner}/{repo}/releases'

    data = {
        'tag_name': tag,
        'target_commitish': branch,
        'name': name,
        'body': body,
        'draft': False,
        'prerelease': False
    }

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

    if token:
        headers['Authorization'] = f'token {token}'

    req = request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return True, result
    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return False, f"HTTP {e.code}: {error_body}"
    except Exception as e:
        return False, str(e)

def main():
    print("=== AceGuard Release 创建工具 ===\n")

    # 配置
    OWNER = "Zynqor"
    REPO = "AceGuard"
    TAG = "v1.0.0"
    BRANCH = "claude/process-affinity-priority-tool-011CUrEAXg87phcLHNGnvgQT"
    NAME = "v1.0.0 - 首个正式版本 🎉"

    # 读取release notes
    try:
        with open('RELEASE_NOTES_v1.0.0.md', 'r', encoding='utf-8') as f:
            body = f.read()
    except FileNotFoundError:
        print("错误: 找不到 RELEASE_NOTES_v1.0.0.md")
        sys.exit(1)

    print(f"仓库: {OWNER}/{REPO}")
    print(f"标签: {TAG}")
    print(f"分支: {BRANCH}")
    print(f"名称: {NAME}")
    print()

    # 获取token（可选）
    token = get_github_token()

    if not token:
        print("⚠️  未找到GitHub token，将尝试使用本地代理")
        print()

    # 首先尝试使用本地代理（不需要token）
    print("正在尝试通过本地代理创建Release...")
    success, result = create_github_release(
        None, OWNER, REPO, TAG, BRANCH, NAME, body, use_proxy=True
    )

    # 如果本地代理失败，尝试使用GitHub API
    if not success and token:
        print("本地代理失败，尝试使用GitHub API...")
        success, result = create_github_release(
            token, OWNER, REPO, TAG, BRANCH, NAME, body, use_proxy=False
        )

    if success:
        print("✅ Release创建成功！")
        print(f"\n🔗 Release URL: {result.get('html_url')}")
        print(f"📦 上传URL: {result.get('upload_url')}")
        print()
        print("⚠️ 注意: GitHub Actions会自动编译并上传文件，请等待约5-10分钟")
        print("📊 查看构建状态: https://github.com/{}/{}/actions".format(OWNER, REPO))
    else:
        print(f"❌ 创建失败: {result}")
        print()
        print("请尝试手动在GitHub网站上创建Release：")
        print(f"1. 访问 https://github.com/{OWNER}/{REPO}/releases/new")
        print(f"2. 填写:")
        print(f"   - Tag: {TAG}")
        print(f"   - Target: {BRANCH}")
        print(f"   - Title: {NAME}")
        print(f"   - Description: 复制 RELEASE_NOTES_v1.0.0.md 的内容")
        print(f"3. 点击 'Publish release'")
        sys.exit(1)

if __name__ == '__main__':
    # 允许从命令行传入token
    if len(sys.argv) > 1:
        os.environ['GITHUB_TOKEN'] = sys.argv[1]

    main()
