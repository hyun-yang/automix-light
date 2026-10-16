#!/usr/bin/env bash
# e2e-smoke-observe.sh — aml observe.py: 측정값 합산 / 측정 줄 / fail-open
# (파트 B 는 Langfuse dry-run 을 함께 확인한다.)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OBSERVE="$HERE/../aml/scripts/observe.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail() { echo "실패: $*" >&2; exit 1; }

[ -f "$OBSERVE" ] || fail "observe.py 를 찾을 수 없음: $OBSERVE"

PROJ="$TMP/proj"; mkdir -p "$PROJ"; cd "$PROJ"

# ── 가짜 세션 기록: 인코딩된 cwd 폴더 아래 세션 JSONL 하나 ───────────────────
ENC="$(python3 -c 'import os,re; print(re.sub(r"[^A-Za-z0-9]","-",os.path.realpath(os.getcwd())))')"
TR="$TMP/projects/$ENC"; mkdir -p "$TR"
cat > "$TR/session.jsonl" <<EOF
{"type":"assistant","timestamp":"2026-07-01T00:00:10Z","cwd":"$PROJ","message":{"model":"claude-opus-4-8","usage":{"input_tokens":1000,"output_tokens":500,"cache_creation_input_tokens":200,"cache_read_input_tokens":8000}}}
{"type":"assistant","timestamp":"2026-07-01T00:01:00Z","message":{"model":"claude-opus-4-8","usage":{"input_tokens":500,"output_tokens":250,"cache_creation_input_tokens":0,"cache_read_input_tokens":2000}}}
{"type":"user","timestamp":"2026-07-01T00:01:30Z","message":{}}
{"type":"assistant","timestamp":"2026-07-01T02:00:00Z","message":{"model":"claude-haiku-4-5","usage":{"input_tokens":100,"output_tokens":50}}}
{"type":"assistant","timestamp":"2020-01-01T00:00:00Z","message":{"model":"claude-opus-4-8","usage":{"input_tokens":99999,"output_tokens":99999}}}
EOF
export AML_CLAUDE_PROJECTS_DIR="$TMP/projects"

# A1. 모델 하나짜리 구간 (haiku 기록만 들어온다)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 하나")"
echo "$OUT" | grep -q '^측정: claude-haiku-4-5'      || fail "A1 모델: $OUT"
echo "$OUT" | grep -q '토큰 입력 100 / 출력 50'      || fail "A1 토큰: $OUT"
echo "$OUT" | grep -q '예상 비용 \$'                 || fail "A1 비용: $OUT"

# A2. 모델 여럿인 구간 (opus 2개 + haiku 1개; 2020년 기록은 구간 밖)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T00:00:00Z --label "1.1 여럿")"
echo "$OUT" | grep -q '^측정: '                       || fail "A2 머리말: $OUT"
echo "$OUT" | grep -q 'claude-opus-4-8'               || fail "A2 opus: $OUT"
echo "$OUT" | grep -q 'claude-haiku-4-5'              || fail "A2 haiku: $OUT"
echo "$OUT" | grep -q '입력 1.5k'                     || fail "A2 opus 입력 합계: $OUT"
echo "$OUT" | grep -q '예상 비용 \$0.03'              || fail "A2 총비용: $OUT"

# A3. fail-open — 기록 폴더 자체가 없어도 종료 코드 0 + "기록 없음"
if ! OUT="$(AML_CLAUDE_PROJECTS_DIR="$TMP/none" python3 "$OBSERVE" task-done --since 2026-07-01T00:00:00Z --label x)"; then
  fail "A3 는 종료 코드 0 이어야 함"
fi
echo "$OUT" | grep -q '기록 없음'                     || fail "A3 메시지: $OUT"

echo "정상: 파트 A 통과"

# ── 파트 B: Langfuse 켜기 ────────────────────────────────────────────────────
# B1. 설정 파일 없음 → 꺼짐 → 측정 줄만 (--dry-run 이어도 배치 출력 없음)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 하나" --dry-run)"
[ "$(printf '%s\n' "$OUT" | wc -l)" -eq 1 ] || fail "B1 꺼짐이면 1줄만 나와야 함: $OUT"

# B2. 설정 on + --dry-run → 둘째 줄이 배치 JSON; 구조를 확인한다
mkdir -p .aml
printf 'langfuse: "on"\nlangfuse_host: ""\n' > .aml/config.yaml
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 하나" \
       --feature "테스트 기능" --note "테스트 3개 통과" --dry-run)"
printf '%s\n' "$OUT" | sed -n '2p' | python3 -c '
import json, sys
b = json.load(sys.stdin)["batch"]
types = sorted(e["type"] for e in b)
assert types == ["event-create", "generation-create", "trace-create"], types
tr = next(e for e in b if e["type"] == "trace-create")
assert tr["body"]["sessionId"] == "테스트 기능", tr["body"]
assert tr["body"]["id"].startswith("aml-"), tr["body"]["id"]
gen = next(e for e in b if e["type"] == "generation-create")
assert gen["body"]["model"] == "claude-haiku-4-5", gen["body"]["model"]
assert gen["body"]["usageDetails"]["input"] == 100, gen["body"]["usageDetails"]
ev = next(e for e in b if e["type"] == "event-create")
assert ev["body"]["metadata"]["note"] == "테스트 3개 통과", ev["body"]
' || fail "B2 배치 구조"

# B3. id 는 결정적 — 같은 since/label 을 두 번 실행하면 id 집합이 같아야 한다
ids() { printf '%s\n' "$1" | sed -n '2p' | python3 -c 'import json,sys; print(sorted(e["id"] for e in json.load(sys.stdin)["batch"]))'; }
OUT2="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 하나" \
        --feature "테스트 기능" --note "테스트 3개 통과" --dry-run)"
[ "$(ids "$OUT")" = "$(ids "$OUT2")" ] || fail "B3 id 는 결정적이어야 함"

# B3b. 한글 라벨이 trace id 에 그대로 남는다 (라벨 구분이 사라지지 않는다)
printf '%s\n' "$OUT" | sed -n '2p' | python3 -c '
import json, sys
tr = next(e for e in json.load(sys.stdin)["batch"] if e["type"] == "trace-create")
assert "하나" in tr["body"]["id"], tr["body"]["id"]
' || fail "B3b 한글 라벨 slug"

# B3c. ASCII 가 아닌 기능명/메모가 그대로 왕복한다 (유니코드가 깨지지 않는다)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label x \
       --feature "café-日本語-🎯" --note "ASCII 아닌 메모" --dry-run)"
printf '%s\n' "$OUT" | sed -n '2p' | python3 -c '
import json, sys
tr = next(e for e in json.load(sys.stdin)["batch"] if e["type"] == "trace-create")
assert tr["body"]["sessionId"] == "café-日本語-🎯", tr["body"]["sessionId"]
' || fail "B3c ASCII 아닌 값 왕복"

# B4. on + 키 없음 + dry-run 아님 → 전송 건너뜀 경고(stderr), 종료 코드 0, stdout 에는 측정 줄
ERR="$TMP/err"
if ! OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY \
      python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label x 2>"$ERR")"; then
  fail "B4 는 종료 코드 0 이어야 함"
fi
echo "$OUT" | grep -q '^측정: '          || fail "B4 stdout: $OUT"
grep -q '전송을 건너뜁니다' "$ERR"       || fail "B4 stderr: $(cat "$ERR")"

# B5. ping — 키가 없으면 경고, 종료 코드 0
if ! OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY python3 "$OBSERVE" ping)"; then
  fail "B5 는 종료 코드 0 이어야 함"
fi
echo "$OUT" | grep -q '^경고:'           || fail "B5: $OUT"

# ── 파트 C: 명령 md 연결 + 복사본 경로 ──────────────────────────────────────
AMLDIR="$HERE/../aml"
grep -q 'scripts/observe.py" task-done --since' "$AMLDIR/commands/go.md" || fail "C1 go.md 연결"
grep -q 'scripts/observe.py" ping' "$AMLDIR/commands/doctor.md"          || fail "C1 doctor.md 연결"
grep -q '측정:' "$AMLDIR/templates/progress.template.md"                 || fail "C1 템플릿 측정 줄"

# C3. 준비물 점검(CLAUDE.md + git) 연결
[ -f "$AMLDIR/templates/claude.template.md" ]                            || fail "C3 CLAUDE 템플릿"
grep -q 'claude.template.md' "$AMLDIR/commands/new.md"                   || fail "C3 new.md 템플릿 연결"
grep -q 'git init' "$AMLDIR/commands/new.md"                             || fail "C3 new.md git 준비"
grep -q 'CLAUDE.md' "$AMLDIR/commands/doctor.md"                         || fail "C3 doctor.md 점검"

# C4. v0.6.0 아티팩트 사슬 — 템플릿 7개와 명령 7개가 모두 있고 서로를 가리킨다
for t in intent spec task progress claude review skill; do
  [ -f "$AMLDIR/templates/$t.template.md" ]                              || fail "C4 템플릿 없음: $t"
done
for c in new go review next rule status doctor; do
  [ -f "$AMLDIR/commands/$c.md" ]                                        || fail "C4 명령 없음: $c"
done
grep -q 'intent.template.md' "$AMLDIR/commands/new.md"                   || fail "C4 new.md → intent 템플릿"
grep -q 'REVIEW.md' "$AMLDIR/commands/new.md"                            || fail "C4 new.md → REVIEW.md"
grep -q '.claude/skills' "$AMLDIR/commands/new.md"                       || fail "C4 new.md → 규칙 카드"
grep -q '걱정되는 것' "$AMLDIR/templates/spec.template.md"               || fail "C4 spec 템플릿 걱정되는 것"
grep -q '바뀌는 파일' "$AMLDIR/templates/task.template.md"               || fail "C4 task 템플릿 계획 항목"
grep -q '확인하는 법' "$AMLDIR/templates/claude.template.md"             || fail "C4 claude 템플릿 확인하는 법"

# C5. 구현 루프 — 고치는 중 표시 · 독립 확인 · 리뷰 · 다음 바퀴로 이어진다
grep -q '.aml/FIXING' "$AMLDIR/commands/go.md"                           || fail "C5 go.md FIXING"
grep -q 'aml:verifier' "$AMLDIR/commands/go.md"                          || fail "C5 go.md verifier"
grep -q '/aml:review' "$AMLDIR/commands/go.md"                           || fail "C5 go.md → review"
grep -q '/aml:next' "$AMLDIR/commands/go.md"                             || fail "C5 go.md → next"
grep -q 'review.template.md' "$AMLDIR/commands/review.md"                || fail "C5 review.md → 템플릿"
grep -q '/aml:rule' "$AMLDIR/commands/review.md"                         || fail "C5 review.md → rule"
grep -q 'skill.template.md' "$AMLDIR/commands/rule.md"                   || fail "C5 rule.md → 규칙 카드 템플릿"
grep -q 'intent.md' "$AMLDIR/commands/next.md"                           || fail "C5 next.md → intent"
grep -q 'observe.py" summary' "$AMLDIR/commands/status.md"               || fail "C5 status.md → summary"
grep -q 'FIXING' "$AMLDIR/commands/doctor.md"                            || fail "C5 doctor.md FIXING 점검"
grep -q '안전망' "$AMLDIR/commands/doctor.md"                            || fail "C5 doctor.md 안전망 점검"

# C6. 도우미 · 안전망 · 참고 문서
[ -f "$AMLDIR/agents/verifier.md" ]                                      || fail "C6 verifier 없음"
grep -q '^tools: Read, Bash, Grep, Glob$' "$AMLDIR/agents/verifier.md"   || fail "C6 verifier 는 읽기 전용이어야 함"
[ -x "$AMLDIR/hooks/aml-guard.sh" ]                                      || fail "C6 안전망 실행 권한"
for r in artifact-chain autonomy-and-guardrails next-steps; do
  [ -f "$AMLDIR/references/$r.md" ]                                      || fail "C6 참고 문서 없음: $r"
done
grep -q 'autonomy-and-guardrails.md' "$AMLDIR/commands/rule.md"          || fail "C6 rule.md → 안전망 문서"
grep -q 'next-steps.md' "$AMLDIR/commands/next.md"                       || fail "C6 next.md → 다음 단계 문서"

# 복사본도 같은 상대 경로(<플러그인 루트>/scripts/observe.py)에서 실행된다
AUTOMIX_LIGHT_MARKETPLACE_DIR="$TMP/stage" bash "$HERE/../install.sh" >/dev/null
OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY python3 "$TMP/stage/aml/scripts/observe.py" task-done --since 2026-07-01T01:00:00Z --label staged 2>/dev/null)"
echo "$OUT" | grep -q '^측정: '                                          || fail "C2 복사본: $OUT"
[ -f "$TMP/stage/aml/templates/claude.template.md" ]                     || fail "C2 복사본 템플릿"
[ -x "$TMP/stage/aml/hooks/aml-guard.sh" ]                               || fail "C2 복사본 안전망"
[ -f "$TMP/stage/aml/agents/verifier.md" ]                               || fail "C2 복사본 verifier"
[ -f "$TMP/stage/aml/references/next-steps.md" ]                         || fail "C2 복사본 참고 문서"

echo "정상: 파트 C 통과"

# ── 파트 D: 진행 기록 요약 (observe.py summary) ──────────────────────────────
cat > "$TMP/progress.md" <<'PROG'
# 진행 기록

## 2026-09-06 — 둘째
- 측정: claude-opus-4-8 · 4분 32초 · 토큰 입력 12.3k / 출력 4.1k (캐시 읽기 88k / 쓰기 2.1k) · 예상 비용 $0.42
- 리뷰: 중요 0 · 사소 2

## 2026-09-05 — 첫째
- 측정: 1시간 3분 · claude-opus-4-8(입력 5.0k/출력 1.2k) + claude-haiku-4-5(입력 900/출력 300) · 예상 비용 $1.10
- 측정: 기록 없음 (세션 기록을 찾지 못했습니다)
- <observe.py 출력을 그대로 — `측정: …` 한 줄: 모델 · 걸린 시간 · 토큰 · 예상 비용>
PROG
OUT="$(python3 "$OBSERVE" summary "$TMP/progress.md")" || fail "D1 종료 코드"
echo "$OUT" | grep -q '작업 3개'                                         || fail "D1 작업 수: $OUT"
echo "$OUT" | grep -q '총 1시간 7분'                                     || fail "D1 걸린 시간: $OUT"
echo "$OUT" | grep -q '예상 비용 합계 \$1.52'                            || fail "D1 비용 합계: $OUT"
echo "$OUT" | grep -q 'claude-opus-4-8 2회'                              || fail "D1 모델 집계: $OUT"
echo "$OUT" | grep -q '측정 없는 작업: 1개'                              || fail "D1 측정 없는 작업: $OUT"

# D2. 측정 줄이 없는 파일 / 아예 없는 파일 — 둘 다 종료 코드 0
printf '# 진행 기록\n\n아직 아무것도 없습니다.\n' > "$TMP/empty.md"
OUT="$(python3 "$OBSERVE" summary "$TMP/empty.md")" || fail "D2 종료 코드"
echo "$OUT" | grep -q '측정 줄이 아직 없습니다'                          || fail "D2: $OUT"
OUT="$(python3 "$OBSERVE" summary "$TMP/없는파일.md")" || fail "D3 종료 코드(없는 파일도 0)"
echo "$OUT" | grep -q '읽지 못했습니다'                                  || fail "D3: $OUT"
echo "정상: 파트 D 통과"

echo "정상: e2e-smoke-observe 통과"
