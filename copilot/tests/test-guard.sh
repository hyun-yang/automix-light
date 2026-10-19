#!/usr/bin/env bash
# test-guard.sh — Copilot 판 aml 안전망(hooks/aml-guard.sh) 확인
#
# 훅은 세 가지만 막고, aml 프로젝트가 아닌 곳에서는 아무것도 하지 않으며,
# 무슨 일이 있어도 0(통과) 또는 2(막음)로만 끝나야 한다 — Copilot 은 그 밖의 코드를 "막음"으로 처리한다.
# Copilot 을 부르지 않고, Copilot 의 preToolUse 입력 모양을 흉내 내 검사한다.
# 사용법 (저장소 루트에서): bash copilot/tests/test-guard.sh

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD="$HERE/../aml/hooks/aml-guard.sh"
[[ -f "$GUARD" ]] || { echo "실패: 훅 파일이 없습니다: $GUARD" >&2; exit 1; }
bash -n "$GUARD" || { echo "실패: 훅 셸 문법 오류" >&2; exit 1; }

TMP="$(mktemp -d)"
PLAIN="$(mktemp -d)"        # aml 프로젝트가 아닌 폴더
trap 'rm -rf "$TMP" "$PLAIN"' EXIT

printf '# spec\n' > "$TMP/spec.md"
printf '# task\n' > "$TMP/task.md"

# check <설명> <기대 종료코드> <입력 JSON>
check() {
  local desc="$1" want="$2" json="$3" out code
  # 시험을 돌리는 폴더가 aml 프로젝트여도 결과가 같도록, 훅은 빈 폴더에서 돌린다.
  out=$(cd "$PLAIN" && printf '%s' "$json" | bash "$GUARD" 2>&1); code=$?
  if [[ "$code" != "$want" ]]; then
    echo "실패: $desc — 기대 종료코드 $want, 실제 $code" >&2
    echo "      출력: $out" >&2
    exit 1
  fi
  # 막았다면 이유와 해결 방법이 함께 있어야 한다.
  if [[ "$want" == "2" ]]; then
    echo "$out" | grep -q "aml 안전망이 막았습니다" || { echo "실패: $desc — 막은 이유가 없습니다" >&2; exit 1; }
    echo "$out" | grep -q "→" || { echo "실패: $desc — 해결 방법(→)이 없습니다" >&2; exit 1; }
    # Copilot 은 stdout 의 permissionDecisionReason 을 막은 이유로 보여 준다(stderr 는 보이지 않는다).
    stdout=$(cd "$PLAIN" && printf '%s' "$json" | bash "$GUARD" 2>/dev/null)
    printf '%s' "$stdout" | python3 -c '
import json, sys
d = json.load(sys.stdin)
assert d.get("permissionDecision") == "deny"
r = d.get("permissionDecisionReason", "")
assert "aml 안전망이 막았습니다" in r and "→" in r
' 2>/dev/null || { echo "실패: $desc — stdout 에 막은 이유(permissionDecisionReason)가 없습니다: $stdout" >&2; exit 1; }
  fi
}

# sh <설명> <기대> <cwd> <명령>        — bash 도구
sh_() {
  local json
  json=$(CWD="$3" CMD="$4" python3 -c '
import json, os
print(json.dumps({"sessionId": "s1", "timestamp": 1, "cwd": os.environ["CWD"],
                  "toolName": "bash", "toolArgs": {"command": os.environ["CMD"], "description": "x"}}))')
  check "$1" "$2" "$json"
}

# file <설명> <기대> <도구> <cwd> <경로>   — 파일을 만들거나 고치는 도구
file_() {
  local json
  json=$(TOOL="$3" CWD="$4" FP="$5" python3 -c '
import json, os
print(json.dumps({"sessionId": "s1", "timestamp": 1, "cwd": os.environ["CWD"],
                  "toolName": os.environ["TOOL"], "toolArgs": {"path": os.environ["FP"], "new_str": "x"}}))')
  check "$1" "$2" "$json"
}

FORCE_PUSH='git push --force origin main'
LEASE_PUSH='git push --force-with-lease origin main'

# ── A. 범위: aml 프로젝트에서만 동작한다 ─────────────────────────────────────
sh_ "A1 비-aml 폴더의 .env 리다이렉트"  0 "$PLAIN" 'echo KEY=1 >> .env'
sh_ "A2 비-aml 폴더의 강제 푸시"        0 "$PLAIN" "$FORCE_PUSH"
sh_ "A3 aml 폴더의 평범한 명령"         0 "$TMP"   'ls -la'
echo "정상: A 통과 (범위 제한)"

# ── B. 가드 1 — 비밀키 ───────────────────────────────────────────────────────
sh_ "B1 .env 덮어쓰기"        2 "$TMP" 'echo KEY=1 > .env'
sh_ "B2 .env 이어쓰기"        2 "$TMP" 'echo KEY=1 >> .env.local'
sh_ "B3 git add .env"         2 "$TMP" 'git add .env'
sh_ "B4 평범한 리다이렉트"    0 "$TMP" 'echo hi > out.txt'
sh_ "B5 .env 읽기는 통과"     0 "$TMP" 'cat .env'
echo "정상: B 통과 (비밀키)"

# ── C. 가드 3 — 되돌릴 수 없는 명령 ──────────────────────────────────────────
sh_ "C1 강제 푸시"                  2 "$TMP" "$FORCE_PUSH"
sh_ "C2 --force-with-lease 는 통과" 0 "$TMP" "$LEASE_PUSH"
sh_ "C3 하드 리셋"                  2 "$TMP" 'git reset --hard HEAD~1'
sh_ "C4 통째로 지우기 (홈)"         2 "$TMP" 'rm -rf ~'
sh_ "C5 통째로 지우기 (현재 폴더)"  2 "$TMP" 'rm -rf .'
sh_ "C6 대상이 분명한 지우기"       0 "$TMP" 'rm -rf build'
sh_ "C7 평범한 push"                0 "$TMP" 'git push origin main'
sh_ "C8 여러 줄 명령 안의 하드 리셋" 2 "$TMP" $'git status\ngit reset --hard'
echo "정상: C 통과 (되돌릴 수 없는 명령)"

# ── D. 가드 2 — 고치는 중 테스트 파일 보호 ───────────────────────────────────
file_ "D1 표시 없으면 테스트 파일도 통과" 0 edit "$TMP" "$TMP/tests/test_app.py"
mkdir -p "$TMP/.aml" && touch "$TMP/.aml/FIXING"
file_ "D2 고치는 중 테스트 파일 (edit)"    2 edit   "$TMP" "$TMP/tests/test_app.py"
file_ "D3 고치는 중 테스트 파일 (create)"  2 create "$TMP" "$TMP/src/app.spec.ts"
file_ "D4 고치는 중 이름 끝이 _test.py"    2 edit   "$TMP" "$TMP/src/app_test.py"
file_ "D5 고치는 중 소스 파일은 통과"      0 edit   "$TMP" "$TMP/src/app.py"
sh_   "D6 고치는 중 bash 는 이 가드와 무관" 0 "$TMP" 'ls tests/'
PATCH=$'*** Begin Patch\n*** Update File: src/app.py\n@@\n-a\n+b\n*** Update File: tests/test_app.py\n@@\n-a\n+b\n*** End Patch'
json=$(CWD="$TMP" P="$PATCH" python3 -c '
import json, os
print(json.dumps({"sessionId": "s1", "timestamp": 1, "cwd": os.environ["CWD"],
                  "toolName": "apply_patch", "toolArgs": {"input": os.environ["P"]}}))')
check "D7 고치는 중 패치 안에 테스트 파일" 2 "$json"
rm -f "$TMP/.aml/FIXING"
file_ "D8 표시를 지우면 다시 통과"        0 edit "$TMP" "$TMP/tests/test_app.py"
echo "정상: D 통과 (테스트 파일 보호)"

# ── E. 끄기 + 0·2 로만 끝나기 ────────────────────────────────────────────────
printf 'guard: "off"\n' > "$TMP/.aml/config.yaml"
sh_ "E1 guard off — 비밀키 통과"    0 "$TMP" 'echo KEY=1 >> .env'
sh_ "E2 guard off — 강제 푸시 통과" 0 "$TMP" "$FORCE_PUSH"
printf 'guard: "on"\n' > "$TMP/.aml/config.yaml"
sh_ "E3 guard on — 다시 막는다"     2 "$TMP" 'echo KEY=1 >> .env'
rm -f "$TMP/.aml/config.yaml"

check "E4 깨진 JSON 은 통과"        0 'not json at all'
check "E5 빈 입력은 통과"           0 ''
check "E6 모르는 도구는 통과"       0 "{\"cwd\": \"$TMP\", \"toolName\": \"web_fetch\", \"toolArgs\": {\"url\": \"https://x\"}}"
check "E7 toolArgs 가 JSON 문자열" 2 "{\"cwd\": \"$TMP\", \"toolName\": \"bash\", \"toolArgs\": \"{\\\"command\\\": \\\"git reset --hard\\\"}\"}"
check "E8 toolArgs 가 없음"         0 "{\"cwd\": \"$TMP\", \"toolName\": \"bash\"}"
check "E9 없는 cwd"                 0 '{"cwd": "/없는/폴더", "toolName": "bash", "toolArgs": {"command": "git reset --hard"}}'
# python3 이 없으면 통과 (PATH 에서 python3 만 빼고 bash 는 남긴다)
NOPY="$(mktemp -d)"; ln -s "$(command -v bash)" "$NOPY/bash"
out=$(printf '{"cwd": "%s", "toolName": "bash", "toolArgs": {"command": "git reset --hard"}}' "$TMP" | PATH="$NOPY" "$NOPY/bash" "$GUARD" 2>&1); code=$?
rm -rf "$NOPY"
[[ "$code" == "0" ]] || { echo "실패: E10 python3 이 없으면 통과해야 합니다 (종료코드 $code)" >&2; exit 1; }
echo "정상: E 통과 (끄기 + 0·2 로만 끝남)"

# ── F. 플러그인 연결 ─────────────────────────────────────────────────────────
python3 - "$HERE/../aml" <<'PY'
import json, os, sys
root = sys.argv[1]
pj = json.load(open(os.path.join(root, "plugin.json")))
assert pj.get("hooks") == "hooks.json", "plugin.json 의 hooks 가 hooks.json 을 가리켜야 합니다: %r" % pj.get("hooks")
hj = json.load(open(os.path.join(root, "hooks.json")))
assert hj.get("version") == 1, "hooks.json 의 version 은 1 이어야 합니다"
entries = hj.get("hooks", {}).get("preToolUse", [])
assert entries, "hooks.json 에 preToolUse 훅이 없습니다"
cmd = entries[0].get("bash", "")
assert "${PLUGIN_ROOT}/hooks/aml-guard.sh" in cmd, "훅 명령이 ${PLUGIN_ROOT}/hooks/aml-guard.sh 를 가리켜야 합니다: %r" % cmd
assert 0 < entries[0].get("timeoutSec", 30) <= 30, "timeoutSec 이 이상합니다"
PY
[[ $? == 0 ]] || exit 1
echo "정상: F 통과 (플러그인 연결)"

echo "정상: test-guard 통과"
