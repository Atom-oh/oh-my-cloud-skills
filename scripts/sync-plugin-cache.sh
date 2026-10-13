#!/bin/bash
# Inspect both hosts' cache files against their generated installation packages.
# Usage: ./scripts/sync-plugin-cache.sh [--host claude|codex|all] [--fix]
#
# This diagnoses cached copies, not which version an existing session loaded.
# --fix only refreshes a matching-version isolated package; it never upgrades
# old versions or removes the other host's files from an old combined package.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FIX_MODE=false
HOST_SELECTION=all
STATE_ROOT="$HOME"
STALE_COUNT=0
UNRESOLVED_COUNT=0
CHECKED_COUNT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fix) FIX_MODE=true; shift ;;
    --host) HOST_SELECTION="${2:?--host requires claude, codex or all}"; shift 2 ;;
    --state-root) STATE_ROOT="${2:?--state-root requires a path}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
case "$HOST_SELECTION" in
  all) HOSTS=(claude codex) ;;
  claude|codex) HOSTS=("$HOST_SELECTION") ;;
  *) echo "--host requires claude, codex or all" >&2; exit 2 ;;
esac

PLUGIN_LIST=$(python3 - "$PROJECT_DIR/hosts/catalog.json" <<'PY'
import json,sys
for name in sorted(json.load(open(sys.argv[1]))["plugins"]):
    print(name)
PY
)
mapfile -t PLUGINS <<< "$PLUGIN_LIST"
for HOST in "${HOSTS[@]}"; do
CACHE_BASE="$STATE_ROOT/.$HOST/plugins/cache/oh-my-cloud-skills"
SRC_BASE="$PROJECT_DIR/packages/$HOST"
OTHER_HOST=claude
[[ "$HOST" == claude ]] && OTHER_HOST=codex
for plugin in "${PLUGINS[@]}"; do
  PLUGIN_JSON="$SRC_BASE/$plugin/.$HOST-plugin/plugin.json"
  if [[ ! -f "$PLUGIN_JSON" ]]; then
    echo "Generate $HOST/$plugin first with scripts/sync-codex-plugins.py" >&2
    exit 2
  fi

  VER=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$PLUGIN_JSON")
  CACHE_DIR="$CACHE_BASE/$plugin/$VER"
  if [[ ! -d "$CACHE_DIR" && -f "$CACHE_BASE/$plugin/local/.$HOST-plugin/plugin.json" ]]; then
    LOCAL_VER=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
      "$CACHE_BASE/$plugin/local/.$HOST-plugin/plugin.json")
    [[ "$LOCAL_VER" != "$VER" ]] || CACHE_DIR="$CACHE_BASE/$plugin/local"
  fi

  if [[ ! -d "$CACHE_DIR" ]]; then
    if [[ -d "$CACHE_BASE/$plugin" ]]; then
      echo "STALE CACHE: $HOST/$plugin has no $VER package; update/reinstall through $HOST."
      STALE_COUNT=$((STALE_COUNT + 1))
      UNRESOLVED_COUNT=$((UNRESOLVED_COUNT + 1))
    fi
    continue
  fi

  if [[ -e "$CACHE_DIR/.$OTHER_HOST-plugin" ]]; then
    echo "COMBINED CACHE: $HOST/$plugin v$VER contains $OTHER_HOST metadata; reinstall through $HOST."
    STALE_COUNT=$((STALE_COUNT + 1))
    UNRESOLVED_COUNT=$((UNRESOLVED_COUNT + 1))
    continue
  fi
  if [[ -L "$CACHE_DIR" ]] || [[ -n "$(find "$CACHE_DIR" -type l -print -quit)" ]]; then
    echo "LINKED CACHE: $HOST/$plugin v$VER; reinstall through $HOST."
    STALE_COUNT=$((STALE_COUNT + 1))
    UNRESOLVED_COUNT=$((UNRESOLVED_COUNT + 1))
    continue
  fi
  echo "Checking $HOST/$plugin v$VER..."

  while IFS= read -r -d '' src_file; do
    REL="${src_file#$SRC_BASE/$plugin/}"
    CACHED="$CACHE_DIR/$REL"
    # Not ((CHECKED_COUNT++)): under set -e a post-increment from 0 returns
    # status 1 (the OLD value) and kills the script on the very first file.
    CHECKED_COUNT=$((CHECKED_COUNT + 1))

    if [[ -L "$CACHED" ]]; then
      echo "LINKED CACHE FILE: $HOST/$plugin/$REL; reinstall through $HOST."
      STALE_COUNT=$((STALE_COUNT + 1))
      UNRESOLVED_COUNT=$((UNRESOLVED_COUNT + 1))
      continue
    fi
    if ! diff -q "$src_file" "$CACHED" >/dev/null 2>&1 || [[ -x "$src_file" && ! -x "$CACHED" || ! -x "$src_file" && -x "$CACHED" ]]; then
      echo "  STALE: $REL"
      STALE_COUNT=$((STALE_COUNT + 1))
      if $FIX_MODE; then
        mkdir -p "$(dirname "$CACHED")"
        cp -p "$src_file" "$CACHED"
        echo "    FIXED: copied source → cache"
      fi
    fi
  done < <(find "$SRC_BASE/$plugin" -type f -print0)
done
done

echo ""
echo "Summary: $CHECKED_COUNT files checked, $STALE_COUNT stale"
if [[ $STALE_COUNT -gt 0 ]] && ! $FIX_MODE; then
  echo "Run with --fix to update cache: ./scripts/sync-plugin-cache.sh --fix"
  exit 1
fi
if $FIX_MODE; then
  echo "Restart the host after changes; updated hooks remain subject to host trust."
fi
[[ "$UNRESOLVED_COUNT" -eq 0 ]] || exit 1
