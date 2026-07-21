#!/usr/bin/env bash
# e2e-smoke-observe.sh — aml observe.py: 메트릭 집계 / 측정 줄 / fail-open
# (Task 2에서 Langfuse dry-run 파트 B가 추가된다.)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OBSERVE="$HERE/../aml/scripts/observe.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }

[ -f "$OBSERVE" ] || fail "observe.py not found: $OBSERVE"

PROJ="$TMP/proj"; mkdir -p "$PROJ"; cd "$PROJ"

# ── 가짜 transcript: 인코딩된 cwd 디렉터리에 세션 JSONL 하나 ─────────────
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

# A1. 단일 모델 창 (haiku 레코드만 포함)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 단일")"
echo "$OUT" | grep -q '^metrics: claude-haiku-4-5'   || fail "A1 model: $OUT"
echo "$OUT" | grep -q 'tokens 100 in / 50 out'       || fail "A1 tokens: $OUT"
echo "$OUT" | grep -q 'est. cost \$'                 || fail "A1 cost: $OUT"

# A2. 다중 모델 창 (opus 2건 + haiku 1건, 2020년 레코드는 창 밖)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T00:00:00Z --label "1.1 다중")"
echo "$OUT" | grep -q '^metrics: '                    || fail "A2 prefix: $OUT"
echo "$OUT" | grep -q 'claude-opus-4-8'               || fail "A2 opus: $OUT"
echo "$OUT" | grep -q 'claude-haiku-4-5'              || fail "A2 haiku: $OUT"
echo "$OUT" | grep -q '1.5k in'                       || fail "A2 opus input sum: $OUT"
echo "$OUT" | grep -q 'est. cost \$0.03'              || fail "A2 total cost: $OUT"

# A3. fail-open — transcript 루트가 없어도 exit 0 + 수집 불가
if ! OUT="$(AML_CLAUDE_PROJECTS_DIR="$TMP/none" python3 "$OBSERVE" task-done --since 2026-07-01T00:00:00Z --label x)"; then
  fail "A3 must exit 0"
fi
echo "$OUT" | grep -q 'unavailable'                   || fail "A3 message: $OUT"

echo "OK: part A passed"

# ── 파트 B: Langfuse opt-in ────────────────────────────────────────────────
# B1. config 부재 → off → 측정 줄 1행뿐 (dry-run이어도 배치 출력 없음)
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 단일" --dry-run)"
[ "$(printf '%s\n' "$OUT" | wc -l)" -eq 1 ] || fail "B1 off must print 1 line: $OUT"

# B2. config on + --dry-run → 2행째가 배치 JSON, 구조 검증
mkdir -p .aml
printf 'langfuse: "on"\nlangfuse_host: ""\n' > .aml/config.yaml
OUT="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 단일" \
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
' || fail "B2 batch structure"

# B3. 결정적 id — 같은 since/label 로 두 번 실행하면 id 집합 동일
ids() { printf '%s\n' "$1" | sed -n '2p' | python3 -c 'import json,sys; print(sorted(e["id"] for e in json.load(sys.stdin)["batch"]))'; }
OUT2="$(python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label "1.2 단일" \
        --feature "테스트 기능" --note "테스트 3개 통과" --dry-run)"
[ "$(ids "$OUT")" = "$(ids "$OUT2")" ] || fail "B3 ids must be deterministic"

# B4. on + 자격증명 없음 + dry-run 아님 → 전송 생략 경고(stderr), exit 0, 측정 줄은 stdout
ERR="$TMP/err"
if ! OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY \
      python3 "$OBSERVE" task-done --since 2026-07-01T01:00:00Z --label x 2>"$ERR")"; then
  fail "B4 must exit 0"
fi
echo "$OUT" | grep -q '^metrics: '     || fail "B4 stdout: $OUT"
grep -q 'skipping send' "$ERR"         || fail "B4 stderr: $(cat "$ERR")"

# B5. ping — 자격증명 없으면 WARN, exit 0
if ! OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY python3 "$OBSERVE" ping)"; then
  fail "B5 must exit 0"
fi
echo "$OUT" | grep -q '^WARN:'         || fail "B5: $OUT"

# ── 파트 C: 명령 md 배선 + 스테이징 경로 (리뷰 반영 M1) ────────────────────
AMLDIR="$HERE/../aml"
grep -q 'scripts/observe.py" task-done --since' "$AMLDIR/commands/go.md" || fail "C1 go.md wiring"
grep -q 'scripts/observe.py" ping' "$AMLDIR/commands/doctor.md"          || fail "C1 doctor.md wiring"
grep -q '^- 측정:' "$AMLDIR/templates/progress.template.md"              || fail "C1 template line"

# install.sh 스테이징 사본에서 같은 상대 경로(<플러그인 루트>/scripts/observe.py)로 실행되는지
AUTOMIX_LIGHT_MARKETPLACE_DIR="$TMP/stage" bash "$HERE/../install.sh" >/dev/null
OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY python3 "$TMP/stage/aml/scripts/observe.py" task-done --since 2026-07-01T01:00:00Z --label staged 2>/dev/null)"
echo "$OUT" | grep -q '^metrics: '                                       || fail "C2 staged copy: $OUT"

echo "OK: e2e-smoke-observe passed"
