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
# ADR-011 records residual risk; ADR-013 closes the prior Kiro fs_read grant.
chair_err_excerpt() {  # $1=stderr file, $2=byte cap (default 500)
  local f="$1" cap="${2:-500}" tmp
  [ -f "$f" ] || return 0
  tmp="$(mktemp)"
  scrub_secrets < "$f" > "$tmp"
  head -c "$cap" "$tmp" | tr '\n\r' '  '
  rm -f "$tmp"
}

# Optional memory may be absent. Exclude quality rankings from reviewer input.
# Match "Panel-cell judgment quality" and its historical Korean input alias.
# File-based clipping avoids SIGPIPE; an ASCII marker remains intact even when
# byte clipping splits a UTF-8 character at the end of the optional excerpt.
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

# Interpret anchored CLI diagnostics, never general words in echoed review data.
# Output: failure-kind<TAB>diagnostic. Empty output means no known failure.
provider_diagnostic() {
  python3 - "$1" <<'PY'
import re, sys
ansi = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")
log_prefix = re.compile(r"^(?:\[(?:error|fatal|warning|warn|info)\]|(?:error|fatal|warning|warn|info)\s*:)\s*", re.I)
model_code = re.compile(r"\b(?:INVALID_MODEL_ID|ModelNotFoundException|invalid_model|model_not_found)\b", re.I)
transient_code = re.compile(r"\b(?:ThrottlingException|TooManyRequestsException|ServiceQuotaExceededException|RESOURCE_EXHAUSTED)\b", re.I)
usage_code = re.compile(r"\b(?:MONTHLY_REQUEST_COUNT|UsageLimitReachedError|insufficient_quota)\b", re.I)
account_limit = re.compile(r"(?:insufficient credits|monthly request limit (?:reached|exceeded)|usage limit (?:reached|exceeded)|billing hard limit reached|you have reached (?:the limit for overages|your (?:monthly|usage|credit) limit))\b", re.I)
def classify(line):
    body = log_prefix.sub("", line)
    diagnostic_prefix = body != line or line.startswith("An error occurred (")
    if model_code.match(body) or (diagnostic_prefix and model_code.search(body)):
        return "model_selection"
    if re.match(r"failed to set model\b|(?:invalid|unknown|unsupported)\s+model\b|model\s+.{0,100}\s+(?:not found|not available|unsupported)\b", body, re.I):
        return "model_selection"
    if re.match(r"no agent with name\b|Json supplied at .* is invalid\b", body, re.I):
        return "agent_fallback"
    if re.match(r"(?:falling back|using (?:a )?fallback|fallback model)\b", body, re.I):
        return "agent_fallback" if re.search(r"agent|user specified default", body, re.I) else "model_fallback"
    if (usage_code.match(body) or (diagnostic_prefix and usage_code.search(body))
            or account_limit.match(body) or re.match(r"quota exceeded\b", body, re.I)
            or ((diagnostic_prefix or transient_code.match(body)) and account_limit.search(body))):
        return "usage_limit"
    if transient_code.match(body) or (diagnostic_prefix and transient_code.search(body)) or re.match(r"rate limit exceeded\b", body, re.I):
        return "transient_service"
    return None
try:
    fence = None
    diff_context = False
    failure = None
    reset_recorded = False
    with open(sys.argv[1], encoding="utf-8", errors="replace") as source:
        for raw in source:
            raw = ansi.sub("", raw)
            line = raw.strip()
            # Unified-diff framing must be handled before Markdown fences: a
            # single-space context fence is data, not a stderr formatting fence.
            if raw.startswith(("diff --git ", "@@ ")):
                diff_context = True
                continue
            if diff_context:
                if not line or raw.startswith((" ", "+", "-", "\\", "index ",
                        "old mode ", "new mode ", "new file mode ", "deleted file mode ",
                        "similarity index ", "rename from ", "rename to ")):
                    continue
                diff_context = False
            if raw.startswith(("    ", "\t")) or line.startswith(("+", "-", ">", "|")):
                continue
            marker = re.match(r"^(`{3,}|~{3,})", line)
            if marker:
                token = marker[1]
                if fence is None:
                    fence = token
                elif token[0] == fence[0] and len(token) >= len(fence):
                    fence = None
                continue
            if fence:
                continue
            kind = classify(line)
            if kind and (failure is None or (failure.startswith("transient_service\t") and kind != "transient_service")):
                failure = kind + "\t" + line.replace("\t", " ")
            if failure and failure.startswith("usage_limit\t") and not reset_recorded and re.match(
                    r"(?:The |Your )?(?:request )?limits reset on\b", line, re.I):
                failure += "; " + line.replace("\t", " ")
                reset_recorded = True
    if failure:
        print(failure)
except OSError:
    print("diagnostic_read_error\tProvider diagnostic file could not be read")
PY
}

# Service throttles retain the existing bounded retries. Model selection, implicit
# fallback and account usage failures are terminal for this review attempt.
provider_diagnostic_terminal() {
  case "$1" in
    transient_service$'\t'*) return 1 ;;
    '') return 1 ;;
    *) return 0 ;;
  esac
}
