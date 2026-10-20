#!/usr/bin/env bash
# install.sh — automix-light 마켓플레이스를 고정된 경로에 복사하고,
# Claude Code 안에서 실행할 /plugin 명령을 출력한다.
#
# 사용법 (저장소 루트에서):
#   $ cd automix-light
#   $ bash claude-code/install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${AUTOMIX_LIGHT_MARKETPLACE_DIR:-$HOME/.claude-marketplaces/automix-light}"

echo "automix-light 설치 도구"
echo "─────────────────────────────────────────────────"
echo "원본: $SCRIPT_DIR"
echo "대상: $TARGET"
echo

# 1. 여기가 마켓플레이스 루트인지 확인
if [[ ! -f "$SCRIPT_DIR/.claude-plugin/marketplace.json" ]]; then
  echo "오류: $SCRIPT_DIR/.claude-plugin/marketplace.json 이 없습니다." >&2
  echo "      저장소의 claude-code/install.sh 를 그대로 실행하세요 (예: bash claude-code/install.sh)." >&2
  exit 1
fi

# 2. JSON 파일 검사 (실제로 실행되는 파이썬이 있을 때만)
#    Windows 의 python3 는 Microsoft Store 바로가기일 수 있어서,
#    이름이 있는지가 아니라 실제로 돌아가는지로 고른다 (python3 → python → py -3).
PY=()
for cand in "python3" "python" "py -3"; do
  if $cand -c "import sys" >/dev/null 2>&1; then
    read -r -a PY <<<"$cand"
    break
  fi
done
if (( ${#PY[@]} )); then
  # 경로는 인자로 넘긴다 — Git Bash 가 /c/... 를 Windows 파이썬이 아는 C:/... 로 바꿔 준다.
  # 한글이 들어 있으므로 UTF-8 로 읽는다 (Windows 파이썬의 기본 인코딩은 UTF-8 이 아니다).
  check_json='import json, sys; json.load(open(sys.argv[1], encoding="utf-8"))'
  "${PY[@]}" -c "$check_json" "$SCRIPT_DIR/.claude-plugin/marketplace.json" \
    || { echo "오류: marketplace.json 이 올바른 JSON 이 아닙니다" >&2; exit 1; }
  "${PY[@]}" -c "$check_json" "$SCRIPT_DIR/aml/.claude-plugin/plugin.json" \
    || { echo "오류: plugin.json 이 올바른 JSON 이 아닙니다" >&2; exit 1; }
else
  echo "참고: 실행되는 파이썬을 찾지 못해 JSON 검사를 건너뜁니다 (설치는 계속합니다)"
fi

# 3. 고정 경로로 복사 (기존 설치본은 백업)
#    마켓플레이스에 필요한 것만 옮긴다 — .git/.venv/.idea 는 복사하지 않는다.
mkdir -p "$(dirname "$TARGET")"
if [[ -d "$TARGET" ]]; then
  echo "기존 설치본을 ${TARGET}.bak 으로 백업합니다"
  rm -rf "${TARGET}.bak"
  mv "$TARGET" "${TARGET}.bak"
fi
mkdir -p "$TARGET"
cp -r "$SCRIPT_DIR/.claude-plugin" "$SCRIPT_DIR/aml" "$TARGET/"

# 4. 다음 단계
#    Windows(Git Bash)에서는 /c/Users/... 를 Claude Code 에 그대로 넣을 수 있는 C:/Users/... 로 바꿔 보여 준다.
SHOW_TARGET="$TARGET"
if command -v cygpath >/dev/null 2>&1; then
  SHOW_TARGET="$(cygpath -m "$TARGET")"
fi
cat <<MSG
✓ 복사 완료: $SHOW_TARGET

다음 — Claude Code 안에서 실행하세요:

  1. 마켓플레이스 추가:
     /plugin marketplace add $SHOW_TARGET

  2. 플러그인 설치:
     /plugin install aml@automix-light

  3. 확인:
     /help                  # /aml:new, /aml:go, /aml:review, /aml:next 가 보이면 됩니다

MSG
