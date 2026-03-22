#!/bin/bash
# sync-plugin-cache.sh — Detect and fix stale plugin cache files
# Usage: ./scripts/sync-plugin-cache.sh [--fix]
#
# Compares source plugin files with cached versions at
# ~/.claude/plugins/cache/oh-my-cloud-skills/<plugin>/<version>/
# Reports stale files. With --fix, copies source to cache.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CACHE_BASE="$HOME/.claude/plugins/cache/oh-my-cloud-skills"
SRC_BASE="$PROJECT_DIR/plugins"

FIX_MODE=false
STALE_COUNT=0
CHECKED_COUNT=0

if [[ "${1:-}" == "--fix" ]]; then
  FIX_MODE=true
fi

for plugin in aws-content-plugin aws-ops-plugin kiro-power-converter; do
  PLUGIN_JSON="$SRC_BASE/$plugin/.claude-plugin/plugin.json"
  if [[ ! -f "$PLUGIN_JSON" ]]; then
    echo "SKIP: $plugin — plugin.json not found"
    continue
  fi

  VER=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['version'])")
  CACHE_DIR="$CACHE_BASE/$plugin/$VER"

  if [[ ! -d "$CACHE_DIR" ]]; then
    echo "SKIP: $plugin v$VER — no cache directory at $CACHE_DIR"
    continue
  fi

  echo "Checking $plugin v$VER..."

  while IFS= read -r -d '' src_file; do
    REL="${src_file#$SRC_BASE/$plugin/}"
    CACHED="$CACHE_DIR/$REL"
    [[ -f "$CACHED" ]] || continue

    ((CHECKED_COUNT++))

    if ! diff -q "$src_file" "$CACHED" >/dev/null 2>&1; then
      echo "  STALE: $REL"
      ((STALE_COUNT++))
      if $FIX_MODE; then
        mkdir -p "$(dirname "$CACHED")"
        cp "$src_file" "$CACHED"
        echo "    FIXED: copied source → cache"
      fi
    fi
  done < <(find "$SRC_BASE/$plugin" \( -name "*.md" -o -name "*.py" -o -name "*.json" -o -name "*.js" -o -name "*.css" \) -not -path "*/node_modules/*" -print0)
done

echo ""
echo "Summary: $CHECKED_COUNT files checked, $STALE_COUNT stale"
if [[ $STALE_COUNT -gt 0 ]] && ! $FIX_MODE; then
  echo "Run with --fix to update cache: ./scripts/sync-plugin-cache.sh --fix"
  exit 1
fi
