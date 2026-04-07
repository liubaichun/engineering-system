#!/usr/bin/env python3
"""检查 Git Commit 消息格式"""
import sys
import re
import os

COMMIT_FORMAT = r'^(feat|fix|docs|style|refactor|perf|chore)(\([a-zA-Z0-9_-]+\))?: .+$'
SKIP_PATTERNS = [r'^Merge ', r'^Revert ']

def should_skip(msg):
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, msg):
            return True
    return False

def check_format(msg):
    if should_skip(msg):
        print(f'⏭️ 跳过Merge/Revert commit: {msg}')
        return True
    if re.match(COMMIT_FORMAT, msg):
        print(f'✅ Commit 格式正确: {msg}')
        return True
    else:
        print(f'❌ Commit 格式错误: {msg}')
        print(f'正确格式: <类型>(<模块>): <描述>')
        print(f'类型: feat, fix, docs, style, refactor, perf, chore')
        return False

# 获取commit消息
if len(sys.argv) > 1:
    arg = sys.argv[1]
    if os.path.isfile(arg):
        with open(arg, 'r') as f:
            commit_msg = f.read().strip()
    else:
        commit_msg = arg.strip()
else:
    commit_msg = sys.stdin.read().strip()

success = check_format(commit_msg)
sys.exit(0 if success else 1)
