#!/usr/bin/env bash
# test-package.sh — Codex 판 aml 패키지 구조 검사.
#   A. 스킬 7개의 이름·설명   B. 패키지 안 링크가 모두 패키지 안을 가리킴
#   C. 패키지만 따로 복사해도 리소스·측정 스크립트가 동작 (형제 폴더 없이)
#   D. (codex 가 있으면) 격리한 CODEX_HOME 에서 설치하면 캐시에 스킬 7개
#   E. 문서·스킬에 옛 이름 표기(aml-go, $aml:aml-go 등)가 남지 않음
# 사용법 (저장소 루트에서): bash codex/tests/test-package.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_DIR="$(cd "$HERE/.." && pwd)"
PKG="$CODEX_DIR/aml"
SKILLS="new go review next rule status doctor"

fail() { echo "실패: $*" >&2; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 패키지 폴더 하나를 받아 구조를 검사한다 (원본과 복사본에 똑같이 쓴다)
check_package() {
  local pkg="$1" s n
  python3 - "$pkg" <<'PY' || exit 1
import json, re, sys
from pathlib import Path
pkg = Path(sys.argv[1]).resolve()
def fail(msg):
    print("실패: " + msg, file=sys.stderr); sys.exit(1)
m = json.loads((pkg / ".codex-plugin" / "plugin.json").read_text())
if m.get("name") != "aml" or m.get("skills") != "./skills/":
    fail("plugin.json 의 name/skills 가 다릅니다")
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
    if grep -n 'CLAUDE_PLUGIN_ROOT\|/aml:' "$pkg/skills/$s/SKILL.md" | grep -v 'Claude Code' >&2; then
      fail "A $s 에 Claude 판 경로·호출이 있습니다"
    fi
  done
  [ "$(find "$pkg/skills" -name SKILL.md | wc -l)" -eq 7 ] || fail "A 스킬이 7개가 아닙니다"
  for f in templates/agents.template.md templates/skill.template.md references/switching.md \
           references/verification.md references/telemetry.md scripts/observe.py; do
    [ -f "$pkg/$f" ] || fail "C 리소스 없음: $f"
  done
}

check_package "$PKG"
echo "정상: A·B 통과 (스킬 7개, 링크는 패키지 안)"

# C. 패키지만 따로 복사 — 형제 폴더(claude-code/, codex/tests) 없이
cp -r "$PKG" "$TMP/aml"
check_package "$TMP/aml"
mkdir -p "$TMP/proj"
printf '# 진행 기록\n- 측정: gpt-test · 1분 0초 · 토큰 입력 10 / 출력 5 (캐시 읽기 0) · 비용 미산정\n' > "$TMP/proj/progress.md"
OUT="$(cd "$TMP/proj" && python3 "$TMP/aml/scripts/observe.py" summary progress.md)"
echo "$OUT" | grep -q '^요약: 작업 1개' || fail "C 복사본 summary: $OUT"
OUT="$(cd "$TMP/proj" && env -u CODEX_THREAD_ID -u CODEX_SESSION_ID python3 "$TMP/aml/scripts/observe.py" task-done --since 2026-10-17T00:00:00Z --label x)"
[ "${OUT#측정: 기록 없음}" != "$OUT" ] || fail "C 복사본 task-done: $OUT"
echo "정상: C 통과 (패키지만 복사해도 동작)"

# D. 실제 Codex CLI 로 격리 설치 (없으면 건너뜀 — 실제 ~/.codex 는 건드리지 않음)
if command -v codex >/dev/null 2>&1; then
  export CODEX_HOME="$TMP/codex-home"; mkdir -p "$CODEX_HOME"
  codex plugin marketplace add "$CODEX_DIR" >/dev/null 2>&1 || fail "D 마켓플레이스 등록 실패"
  codex plugin add aml@automix-light >/dev/null 2>&1 || fail "D 플러그인 설치 실패"
  codex plugin list 2>/dev/null | grep -q 'aml@automix-light *installed, enabled' || fail "D 설치 목록에 aml 없음"
  CACHE="$(find "$CODEX_HOME/plugins/cache" -mindepth 3 -maxdepth 3 -type d | head -1)"
  [ "$(find "$CACHE/skills" -name SKILL.md | wc -l)" -eq 7 ] || fail "D 설치본 스킬이 7개가 아닙니다"
  check_package "$CACHE"
  # 모델을 부르지 않고 Codex 가 보게 될 스킬 목록만 뽑아 본다 — 플러그인 스킬은 aml:go 처럼 보인다
  mkdir -p "$TMP/empty" && (cd "$TMP/empty" && codex debug prompt-input "점검" >"$TMP/prompt.json" 2>/dev/null) \
    || fail "D codex debug prompt-input 실패"
  for s in $SKILLS; do
    grep -q -- "- aml:$s: " "$TMP/prompt.json" || fail "D Codex 스킬 목록에 aml:$s 가 없습니다"
  done
  grep -q -- "- aml:aml-" "$TMP/prompt.json" && fail "D Codex 스킬 목록에 옛 이름 aml:aml-* 이 있습니다"
  echo "정상: D 통과 (격리 설치본에 스킬 7개, Codex 목록에 aml:go 등 7개)"
else
  echo "건너뜀: D (codex 명령 없음)"
fi

# E. 옛 이름 표기 — 보관 문서(codex/docs)와 진행 기록은 그때의 기록이라 보지 않는다
OLD='aml-(new|go|review|next|rule|status|doctor)([^a-z0-9-]|$)'
if grep -rnIE "$OLD" "$PKG" "$CODEX_DIR/README.md" "$CODEX_DIR/../README.md" >&2; then
  fail "E 옛 이름 표기가 남아 있습니다 — \$aml:go 꼴로 고치세요"
fi
echo "정상: E 통과 (옛 이름 표기 없음)"

echo "정상: test-package 통과"
