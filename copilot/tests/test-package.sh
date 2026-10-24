#!/usr/bin/env bash
# test-package.sh — Copilot 판 aml 패키지 구조 검사.
#   A. 스킬 7개의 이름·설명, 다른 판 전용 표기 없음   B. 패키지 안 링크가 모두 패키지 안을 가리킴
#   C. 패키지만 따로 복사해도 리소스·훅·측정 스크립트가 동작 (형제 폴더 없이)
#   D. (copilot 이 있으면) 격리한 COPILOT_HOME 에 설치하면 스킬 목록에 7개 — 모델은 부르지 않음
# 사용법 (저장소 루트에서): bash copilot/tests/test-package.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COPILOT_DIR="$(cd "$HERE/.." && pwd)"
PKG="$COPILOT_DIR/aml"
SKILLS="new go review next rule status doctor"

fail() { echo "실패: $*" >&2; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 패키지 폴더 하나를 받아 구조를 검사한다 (원본과 복사본에 똑같이 쓴다)
check_package() {
  local pkg="$1" s n f
  python3 - "$pkg" <<'PY' || exit 1
import json, re, sys
from pathlib import Path
pkg = Path(sys.argv[1]).resolve()
def fail(msg):
    print("실패: " + msg, file=sys.stderr); sys.exit(1)
m = json.loads((pkg / "plugin.json").read_text())
if (m.get("name"), m.get("skills"), m.get("agents"), m.get("hooks")) != ("aml", "skills/", "agents/", "hooks.json"):
    fail("plugin.json 의 name/skills/agents/hooks 가 다릅니다")
for p in pkg.rglob("*.md"):
    for t, _ in re.findall(r"\]\(([^)#\s]+)(#[^)]*)?\)", p.read_text()):
        if t.startswith(("http://", "https://")):
            continue
        tp = (p.parent / t).resolve()
        if not tp.exists():
            fail(f"{p.relative_to(pkg)} 의 링크 {t} 가 없습니다")
        if pkg not in tp.parents and tp != pkg:
            fail(f"{p.relative_to(pkg)} 의 링크 {t} 가 패키지 밖을 가리킵니다")
PY
  for s in $SKILLS; do
    [ -f "$pkg/skills/$s/SKILL.md" ] || fail "A 스킬 없음: $s"
    n="$(sed -n 's/^name: //p' "$pkg/skills/$s/SKILL.md" | head -1)"
    [ "$n" = "$s" ] || fail "A $s 의 name 이 '$n' 입니다"
    grep -q '^description: .\{20,\}' "$pkg/skills/$s/SKILL.md" || fail "A $s 의 description 이 비었거나 짧습니다"
    if grep -nE '\$aml[:-]|CLAUDE_PLUGIN_ROOT|CODEX_' "$pkg/skills/$s/SKILL.md" >&2; then
      fail "A $s 에 다른 판의 호출·경로가 있습니다 — Copilot 판은 /aml:go 꼴"
    fi
  done
  [ "$(find "$pkg/skills" -name SKILL.md | wc -l)" -eq 7 ] || fail "A 스킬이 7개가 아닙니다"
  # Codex 판에서 옮겨 오다 남기 쉬운 문구 — Copilot 판에는 훅이 있다
  if grep -rnE 'AML 전용 차단 훅이 없|~/\.codex|codex-measure' "$pkg" >&2; then
    fail "A Codex 판 전용 문구가 남아 있습니다"
  fi
  for f in hooks.json hooks/aml-guard.sh hooks/aml-guard.ps1 hooks/aml-guard.py agents/verifier.agent.md scripts/observe.py \
           templates/agents.template.md templates/skill.template.md \
           references/switching.md references/verification.md references/telemetry.md references/artifact-chain.md; do
    [ -f "$pkg/$f" ] || fail "C 리소스 없음: $f"
  done
  grep -q '^name: verifier$' "$pkg/agents/verifier.agent.md" || fail "C verifier 에이전트의 name 이 다릅니다"
}

# 마켓플레이스 파일이 플러그인을 바르게 가리키는지
python3 - "$COPILOT_DIR" <<'PY' || exit 1
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
def fail(msg):
    print("실패: " + msg, file=sys.stderr); sys.exit(1)
mk = json.loads((root / ".github" / "plugin" / "marketplace.json").read_text())
pj = json.loads((root / "aml" / "plugin.json").read_text())
if mk.get("name") != "automix-light":
    fail("marketplace.json 의 name 이 automix-light 가 아닙니다")
entry = [p for p in mk.get("plugins", []) if p.get("name") == "aml"]
if len(entry) != 1 or entry[0].get("source") != "./aml":
    fail("marketplace.json 이 ./aml 을 가리키지 않습니다")
if entry[0].get("version") != pj.get("version"):
    fail("marketplace.json 과 plugin.json 의 버전이 다릅니다")
if (root / ".claude-plugin").exists() or (root / "aml" / ".claude-plugin").exists():
    fail("Copilot 판에 .claude-plugin 이 있습니다 — Claude 판과 헷갈립니다")
PY

check_package "$PKG"
echo "정상: A·B 통과 (스킬 7개, 다른 판 표기 없음, 링크는 패키지 안)"

# C. 패키지만 따로 복사 — 형제 폴더(claude-code/, codex/, copilot/tests) 없이
cp -r "$PKG" "$TMP/aml"
check_package "$TMP/aml"
mkdir -p "$TMP/proj"
printf '# 진행 기록\n- 측정: gpt-test · 1분 0초 · 토큰 입력 10 / 출력 5 (캐시 읽기 0 / 쓰기 0) · 비용 미산정 · AI 크레딧 0.01\n' > "$TMP/proj/progress.md"
OUT="$(cd "$TMP/proj" && python3 -B "$TMP/aml/scripts/observe.py" summary progress.md)"
echo "$OUT" | grep -q '^요약: 작업 1개' || fail "C 복사본 summary: $OUT"
OUT="$(cd "$TMP/proj" && env -u COPILOT_AGENT_SESSION_ID python3 -B "$TMP/aml/scripts/observe.py" task-done --since 2026-10-19T00:00:00Z --label x)"
[ "${OUT#측정: 기록 없음}" != "$OUT" ] || fail "C 복사본 task-done: $OUT"
printf '# spec\n' > "$TMP/proj/spec.md"; printf '# task\n' > "$TMP/proj/task.md"
set +e
printf '{"cwd": "%s", "toolName": "bash", "toolArgs": {"command": "git push --force"}}' "$TMP/proj" \
  | (cd "$TMP/proj" && bash "$TMP/aml/hooks/aml-guard.sh" >/dev/null 2>&1); code=$?
set -e
[ "$code" = 2 ] || fail "C 복사본 훅이 강제 푸시를 막지 않았습니다 (종료 코드 $code)"
echo "정상: C 통과 (패키지만 복사해도 동작)"

# D. 실제 Copilot CLI 로 격리 설치 (없으면 건너뜀 — 실제 ~/.copilot 은 건드리지 않음)
if command -v copilot >/dev/null 2>&1; then
  export COPILOT_HOME="$TMP/copilot-home"; mkdir -p "$COPILOT_HOME"
  copilot plugin marketplace add "$COPILOT_DIR" >/dev/null 2>&1 || fail "D 마켓플레이스 등록 실패"
  copilot plugin install aml@automix-light >/dev/null 2>&1 || fail "D 플러그인 설치 실패"
  copilot plugin list --json 2>/dev/null | python3 -c '
import json, sys
ok = [p for p in json.load(sys.stdin) if p.get("name") == "aml" and p.get("marketplace") == "automix-light" and p.get("enabled")]
sys.exit(0 if ok else 1)' || fail "D 설치 목록에 켜진 aml@automix-light 가 없습니다"
  mkdir -p "$TMP/empty"
  (cd "$TMP/empty" && copilot skill list --json 2>/dev/null) | python3 -c '
import json, sys
names = sorted(s["name"] for s in json.load(sys.stdin) if s.get("source") == "plugin" and "/aml/skills/" in s.get("path", "").replace(chr(92), "/"))
want = sorted("new go review next rule status doctor".split())
if names != want:
    print("실패: D 스킬 목록이 다릅니다: %s" % names, file=sys.stderr); sys.exit(1)' || exit 1
  echo "정상: D 통과 (격리 설치본에 스킬 7개 — 대화 화면에서는 /aml:go 꼴로 보임)"
else
  echo "건너뜀: D (copilot 명령 없음)"
fi

echo "정상: test-package 통과"
