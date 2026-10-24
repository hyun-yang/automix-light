#!/usr/bin/env python3
"""Copilot 안전망 공통 판정. 입력 명령을 실행하지 않는다."""
import fnmatch
import json
import os
from pathlib import Path
import re
import sys


def project_path(value):
    # Git Bash가 Windows Python에 전달하는 /c/... 및 /tmp/... 경로.
    if os.name == 'nt' and isinstance(value, str):
        if re.match(r'^/[a-zA-Z]/', value):
            value = value[1] + ':' + value[2:]
        elif value.startswith('/tmp/'):
            value = str(Path(os.environ.get('AML_GUARD_TEMP_ROOT', os.environ.get('TEMP', '.'))) / value[5:])
    return Path(value)


def reason(data):
    root = project_path(data.get('cwd') or os.getcwd())
    if not root.is_dir():
        root = Path.cwd()
    if not all((root / name).is_file() for name in ('spec.md', 'task.md')):
        return None
    config = root / '.aml/config.yaml'
    if config.is_file() and re.search(r'^\s*guard:\s*"?off"?\s*$', config.read_text(encoding='utf-8'), re.M):
        return None
    name = data.get('toolName') or data.get('tool_name') or ''
    args = data.get('toolArgs', data.get('tool_input'))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {'command': args}
    if not isinstance(args, dict):
        args = {}
    if name not in ('bash', 'Bash', 'powershell'):
        if not (root / '.aml/FIXING').is_file():
            return None
        paths = [args[k] for k in ('path', 'file_path', 'filePath') if isinstance(args.get(k), str)]
        for value in args.values():
            if isinstance(value, str):
                paths.extend(re.findall(r'^\*\*\* (?:Update|Add|Delete) File: (.+)$', value, re.M))
        patterns = ('*/tests/*', '*/test/*', '*/__tests__/*', 'tests/*', 'test/*', '__tests__/*', '*test_*.py', '*_test.py', '*_test.go', '*_test.rb', '*_spec.rb', '*_test.dart', '*.test.js', '*.test.jsx', '*.test.ts', '*.test.tsx', '*.spec.js', '*.spec.jsx', '*.spec.ts', '*.spec.tsx', '*.spec.dart', '*Test.java', '*Tests.cs')
        if any(fnmatch.fnmatchcase(p.strip().replace('\\', '/'), pattern) for p in paths for pattern in patterns):
            return '지금은 버그를 고치는 중입니다(.aml/FIXING).\n→ 테스트는 그대로 두고 코드를 고쳐서 통과시키세요. 테스트 자체가 잘못된 경우에만 .aml/FIXING 표시를 지운 뒤 다시 시도하세요.'
        return None
    cmd = args.get('command') or ''
    if not isinstance(cmd, str):
        return None
    if re.search(r'(>|>>)\s*[^\s]*\.env', cmd) or re.search(r'git\s+add\s[^;&|]*\.env', cmd):
        return '비밀키가 저장소에 들어갈 수 있습니다.\n→ .env는 저장소에 넣지 말고 .gitignore에 적어 두세요. 값을 바꿀 때는 사람이 확인하세요.'
    if re.search(r'git\s+push[^;&|]*--force(\s|$)', cmd) and not re.search(r'git\s+push[^;&|]*--force-with-lease', cmd):
        return '강제 푸시는 이미 올라간 기록을 덮어씁니다.\n→ 꼭 필요하면 --force-with-lease를 쓰세요.'
    if re.search(r'git\s+reset[^;&|]*--hard', cmd):
        return '하드 리셋은 저장하지 않은 작업을 되돌릴 수 없게 지웁니다.\n→ 잠깐 치우려면 git stash, 기록을 되돌리려면 git revert를 쓰세요. 정말 버릴 때는 직접 터미널에서 실행하세요.'
    if re.search(r'(^|[\s;&|(])rm\s+(-[^\s]*[rR][^\s]*\s+)+(/|~|\.|\*|\./\*|/\*|\$HOME)(\s|$)', cmd):
        return '이 명령은 폴더를 통째로, 되돌릴 수 없게 지웁니다.\n→ 지울 대상을 정확히 적어 주세요(예: rm -rf build). 정말 이대로 지우려면 직접 터미널에서 실행하세요.'
    return None


def main():
    try:
        sys.stdin.reconfigure(encoding='utf-8-sig')
        sys.stdout.reconfigure(encoding='utf-8', newline='\n')
        sys.stderr.reconfigure(encoding='utf-8', newline='\n')
        message = reason(json.load(sys.stdin))
        if message:
            message = '❌ aml 안전망이 막았습니다 — ' + message
            print(json.dumps({'permissionDecision': 'deny', 'permissionDecisionReason': message}, ensure_ascii=False))
            print(message, file=sys.stderr)
            return 2
    except Exception:
        # 기존 정책: 입력/실행 환경 문제로 전체 작업을 막지 않는다.
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
