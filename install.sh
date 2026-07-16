#!/usr/bin/env bash
# install.sh — automix-light 마켓플레이스를 안정된 경로에 스테이징하고
# Claude Code 안에서 실행할 /plugin 명령을 안내한다.
#
# 사용법 (마켓플레이스 루트에서):
#   $ cd automix-light
#   $ ./install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${AUTOMIX_LIGHT_MARKETPLACE_DIR:-$HOME/.claude-marketplaces/automix-light}"

echo "automix-light installer"
echo "─────────────────────────────────────────────────"
echo "Source: $SCRIPT_DIR"
echo "Target: $TARGET"
echo

# 1. 마켓플레이스 루트인지 확인
if [[ ! -f "$SCRIPT_DIR/.claude-plugin/marketplace.json" ]]; then
  echo "ERROR: $SCRIPT_DIR/.claude-plugin/marketplace.json 이 없습니다." >&2
  echo "       marketplace.json 이 있는 automix-light 루트에서 실행하세요." >&2
  exit 1
fi

# 2. JSON 매니페스트 검증 (python3 가 있을 때만)
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import json; json.load(open('$SCRIPT_DIR/.claude-plugin/marketplace.json'))" \
    || { echo "ERROR: marketplace.json 이 올바른 JSON이 아닙니다" >&2; exit 1; }
  python3 -c "import json; json.load(open('$SCRIPT_DIR/aml/.claude-plugin/plugin.json'))" \
    || { echo "ERROR: plugin.json 이 올바른 JSON이 아닙니다" >&2; exit 1; }
fi

# 3. 안정된 경로로 복사 (기존 설치는 백업)
mkdir -p "$(dirname "$TARGET")"
if [[ -d "$TARGET" ]]; then
  echo "기존 설치를 ${TARGET}.bak 으로 백업합니다"
  rm -rf "${TARGET}.bak"
  mv "$TARGET" "${TARGET}.bak"
fi
cp -r "$SCRIPT_DIR" "$TARGET"

# 4. 다음 단계 안내
cat <<EOF
✓ 스테이징 완료: $TARGET

다음 단계 — Claude Code 안에서 실행하세요:

  1. 마켓플레이스 추가:
     /plugin marketplace add $TARGET

  2. 플러그인 설치:
     /plugin install aml@automix-light

  3. 확인:
     /help                  # /aml:new, /aml:go, /aml:status 가 보여야 함

EOF
