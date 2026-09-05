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

# 복사본도 같은 상대 경로(<플러그인 루트>/scripts/observe.py)에서 실행된다
AUTOMIX_LIGHT_MARKETPLACE_DIR="$TMP/stage" bash "$HERE/../install.sh" >/dev/null
OUT="$(env -u LANGFUSE_PUBLIC_KEY -u LANGFUSE_SECRET_KEY python3 "$TMP/stage/aml/scripts/observe.py" task-done --since 2026-07-01T01:00:00Z --label staged 2>/dev/null)"
echo "$OUT" | grep -q '^측정: '                                          || fail "C2 복사본: $OUT"
[ -f "$TMP/stage/aml/templates/claude.template.md" ]                     || fail "C2 복사본 템플릿"

echo "정상: e2e-smoke-observe 통과"
