#!/usr/bin/env bash
# install.sh — stage the automix-light marketplace at a stable path and
# print the /plugin commands to run inside Claude Code.
#
# Usage (from the marketplace root):
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

# 1. Confirm this is the marketplace root
if [[ ! -f "$SCRIPT_DIR/.claude-plugin/marketplace.json" ]]; then
  echo "ERROR: $SCRIPT_DIR/.claude-plugin/marketplace.json not found." >&2
  echo "       Run this from the automix-light root that has marketplace.json." >&2
  exit 1
fi

# 2. Validate the JSON manifests (only when python3 is available)
if command -v python3 >/dev/null 2>&1; then
  python3 -c "import json; json.load(open('$SCRIPT_DIR/.claude-plugin/marketplace.json'))" \
    || { echo "ERROR: marketplace.json is not valid JSON" >&2; exit 1; }
  python3 -c "import json; json.load(open('$SCRIPT_DIR/aml/.claude-plugin/plugin.json'))" \
    || { echo "ERROR: plugin.json is not valid JSON" >&2; exit 1; }
fi

# 3. Copy to the stable path (back up any existing install)
mkdir -p "$(dirname "$TARGET")"
if [[ -d "$TARGET" ]]; then
  echo "Backing up the existing install to ${TARGET}.bak"
  rm -rf "${TARGET}.bak"
  mv "$TARGET" "${TARGET}.bak"
fi
cp -r "$SCRIPT_DIR" "$TARGET"

# 4. Next steps
cat <<EOF
✓ Staged: $TARGET

Next — run these inside Claude Code:

  1. Add the marketplace:
     /plugin marketplace add $TARGET

  2. Install the plugin:
     /plugin install aml@automix-light

  3. Verify:
     /help                  # /aml:new, /aml:go, /aml:status should appear

EOF
