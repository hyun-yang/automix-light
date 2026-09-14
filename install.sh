#!/usr/bin/env bash
# install.sh — automix-light 마켓플레이스를 고정된 경로에 복사하고,
# Claude Code 안에서 실행할 /plugin 명령을 출력한다.
#
# 사용법 (마켓플레이스 루트에서):
#   $ cd automix-light
#   $ ./install.sh

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
  echo "      marketplace.json 이 있는 automix-light 루트에서 실행하세요." >&2
  exit 1
fi

# 2. JSON 파일 검사 (python3 이 있을 때만)
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import json; json.load(open('$SCRIPT_DIR/.claude-plugin/marketplace.json'))" \
    || { echo "오류: marketplace.json 이 올바른 JSON 이 아닙니다" >&2; exit 1; }
  python3 -c "import json; json.load(open('$SCRIPT_DIR/aml/.claude-plugin/plugin.json'))" \
    || { echo "오류: plugin.json 이 올바른 JSON 이 아닙니다" >&2; exit 1; }
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
cat <<MSG
✓ 복사 완료: $TARGET

다음 — Claude Code 안에서 실행하세요:

  1. 마켓플레이스 추가:
     /plugin marketplace add $TARGET

  2. 플러그인 설치:
     /plugin install aml@automix-light

  3. 확인:
     /help                  # /aml:new, /aml:go, /aml:review, /aml:next 가 보이면 됩니다

MSG
