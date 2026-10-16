#!/usr/bin/env bash
# e2e-smoke-guard.sh — aml 안전망(hooks/aml-guard.sh) 확인
#
# 훅은 세 가지만 막고, aml 프로젝트가 아닌 곳에서는 아무것도 하지 않으며,
# 무슨 일이 있어도 fail-open(통과) 이어야 한다. Claude 를 부르지 않고 검사한다.

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

# run <설명> <기대 종료코드> <tool_name> <cwd> <file_path> <command>
run() {
  local desc="$1" want="$2" tool="$3" cwd="$4" fp="$5" cmd="$6"
  local json out code
  json=$(TOOL="$tool" CWD="$cwd" FP="$fp" CMD="$cmd" python3 -c '
import json, os
print(json.dumps({
    "tool_name": os.environ["TOOL"],
    "cwd": os.environ["CWD"],
    "tool_input": {"file_path": os.environ["FP"], "command": os.environ["CMD"]},
}))')
  out=$(printf '%s' "$json" | bash "$GUARD" 2>&1); code=$?
  if [[ "$code" != "$want" ]]; then
    echo "실패: $desc — 기대 종료코드 $want, 실제 $code" >&2
    echo "      출력: $out" >&2
    exit 1
  fi
  # 막았다면 이유와 해결 방법이 함께 있어야 한다.
  if [[ "$want" == "2" ]]; then
    echo "$out" | grep -q "aml 안전망이 막았습니다" || { echo "실패: $desc — 막은 이유가 없습니다" >&2; exit 1; }
    echo "$out" | grep -q "→" || { echo "실패: $desc — 해결 방법(→)이 없습니다" >&2; exit 1; }
  fi
}

FORCE_PUSH='git push --force origin main'
LEASE_PUSH='git push --force-with-lease origin main'

# ── A. 범위: aml 프로젝트에서만 동작한다 ─────────────────────────────────────
run "A1 비-aml 폴더의 .env 리다이렉트"  0 Bash "$PLAIN" "" 'echo KEY=1 >> .env'
run "A2 비-aml 폴더의 강제 푸시"        0 Bash "$PLAIN" "" "$FORCE_PUSH"
run "A3 aml 폴더의 평범한 명령"         0 Bash "$TMP"   "" 'ls -la'
echo "정상: A 통과 (범위 제한)"

# ── B. 가드 1 — 비밀키 ───────────────────────────────────────────────────────
run "B1 .env 덮어쓰기"        2 Bash "$TMP" "" 'echo KEY=1 > .env'
run "B2 .env 이어쓰기"        2 Bash "$TMP" "" 'echo KEY=1 >> .env.local'
run "B3 git add .env"         2 Bash "$TMP" "" 'git add .env'
run "B4 평범한 리다이렉트"    0 Bash "$TMP" "" 'echo hi > out.txt'
run "B5 .env 읽기는 통과"     0 Bash "$TMP" "" 'cat .env'
echo "정상: B 통과 (비밀키)"

# ── C. 가드 3 — 되돌릴 수 없는 명령 ──────────────────────────────────────────
run "C1 강제 푸시"                  2 Bash "$TMP" "" "$FORCE_PUSH"
run "C2 --force-with-lease 는 통과" 0 Bash "$TMP" "" "$LEASE_PUSH"
run "C3 하드 리셋"                  2 Bash "$TMP" "" 'git reset --hard HEAD~1'
run "C4 통째로 지우기 (홈)"         2 Bash "$TMP" "" 'rm -rf ~'
run "C5 통째로 지우기 (현재 폴더)"  2 Bash "$TMP" "" 'rm -rf .'
run "C6 대상이 분명한 지우기"       0 Bash "$TMP" "" 'rm -rf build'
run "C7 평범한 push"                0 Bash "$TMP" "" 'git push origin main'
echo "정상: C 통과 (되돌릴 수 없는 명령)"

# ── D. 가드 2 — 고치는 중 테스트 파일 보호 ───────────────────────────────────
run "D1 표시 없으면 테스트 파일도 통과" 0 Edit "$TMP" "$TMP/tests/test_app.py" ""
mkdir -p "$TMP/.aml" && touch "$TMP/.aml/FIXING"
run "D2 고치는 중 테스트 파일"          2 Edit  "$TMP" "$TMP/tests/test_app.py" ""
run "D3 고치는 중 spec 파일"            2 Write "$TMP" "$TMP/src/app.spec.ts"   ""
run "D4 고치는 중 소스 파일은 통과"     0 Edit  "$TMP" "$TMP/src/app.py"        ""
run "D5 고치는 중 Bash 는 이 가드와 무관" 0 Bash "$TMP" "" 'ls tests/'
rm -f "$TMP/.aml/FIXING"
run "D6 표시를 지우면 다시 통과"        0 Edit "$TMP" "$TMP/tests/test_app.py" ""
echo "정상: D 통과 (테스트 파일 보호)"

# ── E. 끄기 + fail-open ──────────────────────────────────────────────────────
printf 'guard: "off"\n' > "$TMP/.aml/config.yaml"
run "E1 guard off — 비밀키 통과"   0 Bash "$TMP" "" 'echo KEY=1 >> .env'
run "E2 guard off — 강제 푸시 통과" 0 Bash "$TMP" "" "$FORCE_PUSH"
printf 'guard: "on"\n' > "$TMP/.aml/config.yaml"
run "E3 guard on — 다시 막는다"    2 Bash "$TMP" "" 'echo KEY=1 >> .env'
rm -f "$TMP/.aml/config.yaml"

# 깨진 입력 / 빈 입력 / 모르는 도구 → 통과
out=$(printf 'not json at all' | bash "$GUARD" 2>&1); code=$?
[[ "$code" == "0" ]] || { echo "실패: E4 깨진 JSON 은 통과해야 합니다 (종료코드 $code)" >&2; exit 1; }
out=$(printf '' | bash "$GUARD" 2>&1); code=$?
[[ "$code" == "0" ]] || { echo "실패: E5 빈 입력은 통과해야 합니다 (종료코드 $code)" >&2; exit 1; }
run "E6 모르는 도구는 통과" 0 WebFetch "$TMP" "" ""
echo "정상: E 통과 (끄기 + fail-open)"

# ── F. 플러그인 연결 ─────────────────────────────────────────────────────────
PJ="$HERE/../aml/.claude-plugin/plugin.json"
python3 - "$PJ" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
hooks = d.get("hooks", {}).get("PreToolUse", [])
assert hooks, "plugin.json 에 PreToolUse 훅이 없습니다"
entry = hooks[0]
assert "Edit" in entry.get("matcher", "") and "Bash" in entry.get("matcher", ""), \
    "matcher 에 Bash 와 Edit 가 모두 있어야 합니다: %r" % entry.get("matcher")
cmd = entry["hooks"][0]["command"]
assert "aml-guard.sh" in cmd and "CLAUDE_PLUGIN_ROOT" in cmd, \
    "훅 명령이 ${CLAUDE_PLUGIN_ROOT}/hooks/aml-guard.sh 를 가리켜야 합니다: %r" % cmd
PY
[[ $? == 0 ]] || exit 1
echo "정상: F 통과 (플러그인 연결)"

echo "정상: e2e-smoke-guard 통과"
