#!/usr/bin/env bash
# aml-guard.sh — 초보자 안전망 (PreToolUse 훅).
#
# 되돌리기 어려운 일 세 가지만 막는다:
#   1. 비밀키가 저장소에 들어가는 것 (.env)
#   2. 버그를 고치는 중에 테스트 파일을 고치는 것 (.aml/FIXING 이 있을 때)
#   3. 되돌릴 수 없는 명령 (강제 푸시 · 하드 리셋 · 통째로 지우기)
#
# 원칙:
#   - spec.md 와 task.md 가 있는 aml 프로젝트에서만 동작한다. 다른 저장소에는 아무 영향이 없다.
#   - 막을 때는 왜 막았는지와 어떻게 하면 되는지를 함께 말한다.
#   - 무슨 일이 있어도 작업을 방해하지 않는다 — python3 이 없거나 입력이 이상하면 그냥 통과(exit 0).
#   - 끄려면 .aml/config.yaml 에 guard: "off".
#
# 종료 코드: 0 = 통과, 2 = 막음(메시지는 stderr 로 Claude 에게 전달된다).

set -uo pipefail

command -v python3 >/dev/null 2>&1 || exit 0

INPUT=$(cat 2>/dev/null || echo "")
[[ -z "$INPUT" ]] && exit 0

# 한 번의 python 호출로 네 가지를 뽑는다.
# 1줄 = tool_name, 2줄 = cwd, 3줄 = file_path, 나머지 전부 = command
# (도구 이름과 경로에는 줄바꿈이 없지만 명령에는 있을 수 있으므로 명령을 맨 뒤에 둔다.)
PARSED=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    inp = d.get("tool_input") or {}
    if not isinstance(inp, dict):
        inp = {}
    print(d.get("tool_name", "") or "")
    print(d.get("cwd", "") or "")
    print(inp.get("file_path") or inp.get("notebook_path") or "")
    print(inp.get("command", "") or "", end="")
except Exception:
    pass
' 2>/dev/null || echo "")

[[ -z "$PARSED" ]] && exit 0

TOOL_NAME="${PARSED%%$'\n'*}"
R1="${PARSED#*$'\n'}"; [[ "$R1" == "$PARSED" ]] && R1=""
CWD="${R1%%$'\n'*}"
R2="${R1#*$'\n'}"; [[ "$R2" == "$R1" ]] && R2=""
FILE_PATH="${R2%%$'\n'*}"
CMD="${R2#*$'\n'}"; [[ "$CMD" == "$R2" ]] && CMD=""

[[ -z "$TOOL_NAME" ]] && exit 0

ROOT="${CWD:-$PWD}"
[[ -d "$ROOT" ]] || ROOT="$PWD"

# aml 프로젝트가 아니면 아무것도 하지 않는다.
[[ -f "$ROOT/spec.md" && -f "$ROOT/task.md" ]] || exit 0

# 껐으면 아무것도 하지 않는다.
if [[ -f "$ROOT/.aml/config.yaml" ]] \
   && grep -qE '^[[:space:]]*guard:[[:space:]]*"?off"?[[:space:]]*$' "$ROOT/.aml/config.yaml" 2>/dev/null; then
  exit 0
fi

# ── 가드 2: 고치는 중에는 테스트 파일을 지킨다 (Edit/Write 계열) ─────────────
if [[ "$TOOL_NAME" == "Edit" || "$TOOL_NAME" == "Write" || "$TOOL_NAME" == "NotebookEdit" ]]; then
  if [[ -f "$ROOT/.aml/FIXING" && -n "$FILE_PATH" ]]; then
    case "$FILE_PATH" in
      */tests/*|*/test/*|*/__tests__/*|tests/*|test/*|__tests__/*|\
      *test_*.py|*_test.py|*_test.go|*_test.rb|*_spec.rb|*_test.dart|\
      *.test.js|*.test.jsx|*.test.ts|*.test.tsx|\
      *.spec.js|*.spec.jsx|*.spec.ts|*.spec.tsx|*.spec.dart|*Test.java|*Tests.cs)
        cat >&2 <<'MSG'
❌ aml 안전망이 막았습니다 — 지금은 버그를 고치는 중입니다(.aml/FIXING).
   테스트 파일을 고치면 버그가 사라지는 게 아니라, 버그를 잡아 주던 확인이 사라집니다.
   → 테스트는 그대로 두고 코드를 고쳐서 통과시키세요.
   → 테스트 자체가 잘못 쓰인 경우에만: rm .aml/FIXING 로 표시를 지운 뒤 다시 시도하세요.
MSG
        exit 2
        ;;
    esac
  fi
  exit 0
fi

# 나머지 가드는 Bash 명령에만 해당한다.
[[ "$TOOL_NAME" == "Bash" ]] || exit 0
[[ -z "$CMD" ]] && exit 0

# ── 가드 1: 비밀키를 저장소에 넣지 않는다 ────────────────────────────────────
if echo "$CMD" | grep -qE '(>|>>)[[:space:]]*[^[:space:]]*\.env' \
   || echo "$CMD" | grep -qE 'git[[:space:]]+add[[:space:]][^;&|]*\.env'; then
  cat >&2 <<'MSG'
❌ aml 안전망이 막았습니다 — 비밀키가 저장소에 들어갈 수 있습니다.
   .env 같은 파일에는 비밀번호나 API 키가 들어갑니다. 저장소에 한 번 들어가면
   나중에 지워도 기록에는 남습니다.
   → .env 는 저장소에 넣지 말고 .gitignore 에 적어 두세요.
   → 값을 바꿔야 하면 Claude 에게 "이 값을 .env 에 넣어 줘" 라고 말하고 눈으로 확인하세요.
MSG
  exit 2
fi

# ── 가드 3: 되돌릴 수 없는 명령 ──────────────────────────────────────────────
FORCE_RE='git[[:space:]]+push[^;&|]*--force([[:space:]]|$)'
LEASE_RE='git[[:space:]]+push[^;&|]*--force-with-lease'
if echo "$CMD" | grep -qE "$FORCE_RE" && ! echo "$CMD" | grep -qE "$LEASE_RE"; then
  cat >&2 <<'MSG'
❌ aml 안전망이 막았습니다 — 강제 푸시는 이미 올라간 기록을 덮어씁니다.
   → 꼭 필요하면 --force-with-lease 를 쓰세요. 다른 사람 작업을 덮어쓰게 되면 알아서 멈춥니다.
MSG
  exit 2
fi

if echo "$CMD" | grep -qE 'git[[:space:]]+reset[^;&|]*--hard'; then
  cat >&2 <<'MSG'
❌ aml 안전망이 막았습니다 — 하드 리셋은 저장하지 않은 작업을 되돌릴 수 없게 지웁니다.
   → 잠깐 치워 두려면: git stash  (나중에 git stash pop 으로 되돌립니다)
   → 특정 커밋으로 돌아가려면: git revert <커밋>  (기록을 지우지 않고 되돌립니다)
   → 정말 버려야 한다면 사용자가 직접 터미널에서 실행하세요.
MSG
  exit 2
fi

if echo "$CMD" | grep -qE '(^|[[:space:];&|(])rm[[:space:]]+(-[^[:space:]]*[rR][^[:space:]]*[[:space:]]+)+(/|~|\.|\*|\./\*|/\*|\$HOME)([[:space:]]|$)'; then
  cat >&2 <<'MSG'
❌ aml 안전망이 막았습니다 — 이 명령은 폴더를 통째로, 되돌릴 수 없게 지웁니다.
   → 지울 대상을 정확히 적어 주세요 (예: rm -rf build).
   → 정말 이대로 지워야 한다면 사용자가 직접 터미널에서 실행하세요.
MSG
  exit 2
fi

exit 0
