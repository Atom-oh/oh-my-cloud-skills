#!/usr/bin/env bash
# Shared review helpers: isolated slots, result accounting and output scrubbing.
set -uo pipefail

# Clear old slots on reuse; validate the root before constructing a removal path.
ensure_slots() {
  [ -n "$1" ] || { echo "ensure_slots: \$1(workdir) must not be empty" >&2; return 1; }
  rm -rf "$1/slot"; mkdir -p "$1/slot"
}

# A response needs nonempty stdout AND a successful final CLI exit.
# Missing exit evidence is failure, not a vote. Arguments: slot, label, response list.
record_result() {
  local slot="$1" label="$2" responded="$3"
  local rc; rc="$(cat "$slot.rc" 2>/dev/null || echo 1)"
  if [ -s "$slot" ] && [ "$rc" = "0" ]; then
    echo "$label" >> "$responded"
  else
    echo "[skip] $label (exit=$rc)" >&2
    : > "$slot"  # Keep failed slots empty.
  fi
  rm -f "$slot.rc"
}

# Diagnostics are defense in depth, not a read sandbox. Scrub credentials before
# clipping, use a file to avoid pipefail/SIGPIPE, then flatten annotation newlines.
chair_err_excerpt() {  # $1=stderr file, $2=byte cap (default 500)
  local f="$1" cap="${2:-500}" tmp
  [ -f "$f" ] || return 0
  tmp="$(mktemp)"
  scrub_secrets < "$f" > "$tmp"
  head -c "$cap" "$tmp" | tr '\n\r' '  '
  rm -f "$tmp"
}

# Optional memory may be absent. Exclude quality rankings from reviewer input.
# Support the historical Korean heading as input data. File-based clipping avoids
# SIGPIPE; mark a clipped optional excerpt rather than pretending it is complete.
memory_excerpt() {  # $1=memory file, $2=byte cap (default 4000)
  local f="$1" cap="${2:-4000}" tmp size
  [ -f "$f" ] || return 0
  tmp="$(mktemp)"
  awk '
    /^## (패널 셀 판단 질|Panel-cell judgment quality)/ { skip = 1; next }
    skip && /^## / { skip = 0 }
    skip { next }
    { print }
  ' "$f" > "$tmp"
  size="$(wc -c < "$tmp")"
  head -c "$cap" "$tmp"
  if [ "$size" -gt "$cap" ]; then
    printf '\n[...MEMORY TRUNCATED at %sB...]\n' "$cap"
  fi
  rm -f "$tmp"
  return 0
}

# Legacy lexical parser: preserve last-match/trailing-text compatibility for callers.
# It is not an acceptance gate. chair_valid and CI use review_gate.py to validate
# unquoted decisions against the final Issues structure.
verdict_of() {  # $1=review path; stdout: PASS, FAIL or empty
  [ -f "$1" ] || return 0
  grep -oE '^VERDICT: (PASS|FAIL)' "$1" | tail -1 | awk '{print $2}'
}

# Keep verdict_of lexical compatibility; acceptance also requires structured Issues
# and complete configured coverage. This same validator ships with the PRAF template.
review_gate() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  python3 "$script_dir/../../plugins/co-agent/skills/pr-autofix/scripts/review_gate.py" \
    markdown "$1" --work-dir "$2" \
    --chair-error "${chair_error:-0}" --l1-failed "${l1_failed:-0}" \
    --diff-truncated "${panel_truncated:-0}" "${@:3}"
}

scrub_secrets() {
  # Redact whole multiline PEM bodies, including unterminated blocks.
  awk '
    BEGIN { skip = 0 }
    /^-----BEGIN [A-Z ]*PRIVATE KEY-----/ { print "[REDACTED-PRIVATE-KEY]"; skip = 1; next }
    skip && /^-----END [A-Z ]*PRIVATE KEY-----/ { skip = 0; next }
    skip { next }
    { print }
    END { if (skip) print "[REDACTED-UNTERMINATED-PEM-BLOCK]" }
  ' | sed -E \
    -e 's/A(KIA|SIA)[0-9A-Z]{16}/[REDACTED-AWS-KEY]/g' \
    -e 's/gh[pousr]_[A-Za-z0-9]{30,}/[REDACTED-GH-TOKEN]/g' \
    -e 's/github_pat_[A-Za-z0-9_]{30,}/[REDACTED-GH-TOKEN]/g' \
    -e 's/xox[abprs]-[A-Za-z0-9-]{10,}/[REDACTED-SLACK-TOKEN]/g' \
    -e 's/(^|[^A-Za-z0-9_])sk-(proj-|ant-)?[A-Za-z0-9_-]{20,}/\1[REDACTED-API-KEY]/g' \
    -e 's/AIza[0-9A-Za-z_-]{30,}/[REDACTED-GOOGLE-KEY]/g' \
    -e 's/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/[REDACTED-JWT]/g' \
    -e 's/((api[_-]?key|aws_secret_access_key|aws_access_key_id|access[_-]?token|client[_-]?secret|secret|passwd|password|token)['"'"'"]?[[:space:]]*[:=][[:space:]]*['"'"'"])[^'"'"'"]{8,}(['"'"'"])/\1[REDACTED]\3/gI' \
    -e 's/((^|[^A-Za-z0-9_])(api[_-]?key|aws_secret_access_key|aws_access_key_id|access[_-]?token|client[_-]?secret|secret|passwd|password|token)[[:space:]]*[:=][[:space:]]*)[A-Za-z0-9/+_-]{16,}/\1[REDACTED]/gI'
}
