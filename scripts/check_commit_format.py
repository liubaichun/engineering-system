#!/usr/bin/env python3
"""检查 Git Commit 消息格式"""
import sys
import re
import os

COMMIT_FORMAT = r'^(feat|fix|docs|style|refactor|perf|chore)(\([a-zA-Z0-9_-]+\))?: .+$'

# 获取commit消息
if len(sys.argv) > 1:
    arg = sys.argv[1]
    # 如果是文件路径，读取文件内容
    if os.path.isfile(arg):
        with open(arg, 'r') as f:
            commit_msg = f.read().strip()
    else:
        # 直接是commit消息
        commit_msg = arg.strip()
else:
    commit_msg = sys.stdin.read().strip()

if not re.match(COMMIT_FORMAT, commit_msg):
    print(f"❌ Commit 格式错误: {commit_msg}")
    print(f"正确格式: <类型>(<模块>): <描述>")
    print(f"类型: feat, fix, docs, style, refactor, perf, chore")
    sys.exit(1)
else:
    print(f"✅ Commit 格式正确: {commit_msg}")
    sys.exit(0)
