#!/usr/bin/env python3
"""检查 Git Commit 消息格式"""
import sys
import re

COMMIT_FORMAT = r'^(feat|fix|docs|style|refactor|perf|chore)(\([a-zA-Z0-9_-]+\))?: .{1,50}'

commit_msg = sys.argv[1] if len(sys.argv) > 1 else input("请输入 commit 消息: ")

if not re.match(COMMIT_FORMAT, commit_msg):
    print(f"❌ Commit 格式错误: {commit_msg}")
    print(f"正确格式: <类型>(<模块>): <描述>")
    print(f"类型: feat, fix, docs, style, refactor, perf, chore")
    sys.exit(1)
else:
    print(f"✅ Commit 格式正确: {commit_msg}")
