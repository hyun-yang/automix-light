#!/usr/bin/env bash
# test-templates.sh — 공통 템플릿 5개(spec·task·progress·intent·review)가
# Claude 판과 Codex 판에서 글자까지 똑같은지, 한쪽 도구 전용 안내가 섞이지 않았는지 확인한다.
# 사용법 (저장소 루트에서): bash codex/tests/test-templates.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_T="$HERE/../../claude-code/aml/templates"
CODEX_T="$HERE/../aml/templates"
COMMON="spec task progress intent review"

fail() { echo "실패: $*" >&2; exit 1; }

# 두 폴더의 공통 템플릿이 모두 있고 내용이 같으면 0, 아니면 1
same_templates() {
  local a="$1" b="$2" t
  for t in $COMMON; do
    [ -f "$a/$t.template.md" ] && [ -f "$b/$t.template.md" ] || return 1
    cmp -s "$a/$t.template.md" "$b/$t.template.md" || return 1
  done
}

# A. 실제 두 패키지의 공통 템플릿이 완전히 같다
same_templates "$CLAUDE_T" "$CODEX_T" || {
  for t in $COMMON; do diff -u "$CLAUDE_T/$t.template.md" "$CODEX_T/$t.template.md" >&2 || true; done
  fail "A 공통 템플릿이 두 패키지에서 다릅니다 — 양쪽을 같이 고치세요"
}
echo "정상: A 통과 (공통 템플릿 5개 완전 일치)"

# B. 공통 템플릿에 한쪽 도구 전용 경로·호출이 없다
for t in $COMMON; do
  if grep -nE '/aml:|\$aml-|\.claude/|\.agents/|CLAUDE\.md|AGENTS\.md' "$CODEX_T/$t.template.md" >&2; then
    fail "B $t.template.md 에 도구 전용 안내가 있습니다 — 명령·스킬·전용 템플릿으로 옮기세요"
  fi
done
echo "정상: B 통과 (도구 전용 안내 없음)"

# C. 검사가 진짜로 잡는지: 시험 복사본 한쪽만 바꾸면 실패, 원래대로면 통과
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/a" "$TMP/b"
cp "$CLAUDE_T"/*.template.md "$TMP/a/"; cp "$CODEX_T"/*.template.md "$TMP/b/"
same_templates "$TMP/a" "$TMP/b" || fail "C1 원래 상태의 복사본이 다르다고 나옵니다"
for t in $COMMON; do
  cp "$TMP/b/$t.template.md" "$TMP/keep"
  echo "한쪽만 고친 줄" >> "$TMP/b/$t.template.md"
  same_templates "$TMP/a" "$TMP/b" && fail "C2 $t 를 한쪽만 고쳤는데 검사가 통과했습니다"
  mv "$TMP/keep" "$TMP/b/$t.template.md"
done
rm "$TMP/b/spec.template.md"
same_templates "$TMP/a" "$TMP/b" && fail "C3 한쪽에 파일이 없는데 검사가 통과했습니다"
echo "정상: C 통과 (한쪽만 바꾸면 실패)"

# D. 도구 전용 템플릿은 각자 자기 경로를 안내한다
grep -q 'AGENTS.md' "$CODEX_T/agents.template.md"        || fail "D agents.template.md 에 AGENTS.md 안내 없음"
grep -q '.agents/skills/' "$CODEX_T/skill.template.md"   || fail "D Codex skill.template.md 에 .agents/skills/ 안내 없음"
if grep -nE '/aml:|\.claude/|CLAUDE\.md' "$CODEX_T/agents.template.md" "$CODEX_T/skill.template.md" >&2; then
  fail "D Codex 전용 템플릿에 Claude 경로·호출이 있습니다"
fi
echo "정상: D 통과 (전용 템플릿 경로)"

echo "정상: test-templates 통과"
