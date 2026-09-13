#!/usr/bin/env bash
# Fan out configured cells across supplied prompts; production uses one FULL prompt.
# Codex receives stdin; Kiro receives bounded embedded text with no file tools.
# Each cell has a shared total deadline, bounded retries and isolated output.
set -uo pipefail
DIFF="$(realpath "$1" 2>/dev/null)" \
  || { echo "run-panel.sh: realpath failed to resolve diff path: $1" >&2; exit 1; }
LENSES_DIR="$2"; WORK="$3"
# Guard roots before removal/path construction and reject a silent empty prompt set.
[ -n "$LENSES_DIR" ] || { echo "run-panel.sh: lenses_dir (\$2) must not be empty" >&2; exit 1; }
[ -n "$WORK" ] || { echo "run-panel.sh: workdir (\$3) must not be empty" >&2; exit 1; }
# Cell commands change cwd: normalize work paths and fail if preparation fails.
mkdir -p "$WORK" || { echo "run-panel.sh: failed to create workdir: $WORK" >&2; exit 1; }
WORK="$(realpath "$WORK")" \
  || { echo "run-panel.sh: realpath failed to resolve workdir: $WORK" >&2; exit 1; }
T="${PANEL_TIMEOUT:-300}"
RETRIES="${PANEL_RETRIES:-3}"
CELL_BUDGET_MAX=2147483647
for budget_value in "$T" "$RETRIES"; do
  [[ "$budget_value" =~ ^[1-9][0-9]{0,9}$ ]] && [ "$budget_value" -le "$CELL_BUDGET_MAX" ] \
    || { echo "run-panel.sh: budget values PANEL_TIMEOUT/PANEL_RETRIES must be integers in 1..2147483647 without leading zeros" >&2; exit 1; }
done
[ "$T" -le "$((CELL_BUDGET_MAX / RETRIES))" ] \
  || { echo "run-panel.sh: total cell budget exceeds 2147483647 seconds" >&2; exit 1; }
CELL_BUDGET=$((T * RETRIES))
DIR="$(cd "$(dirname "$0")" && pwd)"; . "$DIR/lib.sh"
ensure_slots "$WORK"
SLOT="$WORK/slot"; RESP="$WORK/responded.txt"; : > "$RESP"
: > "$WORK/expected.txt" || exit 1
# Reusing a workdir must not carry old coverage/truncation evidence into a new run.
rm -f "$WORK/coverage-severe.flag" "$WORK/kiro-diff-truncated.flag"
# Load the validated configured roster, not a hardcoded model list. A configuration
# error is not an intentionally disabled cell; check subprocess status explicitly.
CFG="$DIR/panel_config.py"
# Anchor configuration at this repository, with the documented test override.
# An arbitrary caller cwd must not silently ignore local review configuration.
REPO_ROOT="${PR_REVIEW_CONFIG_ROOT:-$DIR/../..}"
if ! KIRO_CELLS_RAW="$(python3 "$CFG" kiro-cells --root "$REPO_ROOT")"; then
  echo "run-panel.sh: panel_config.py kiro-cells failed (malformed/wrong-shape config?) — refusing to run with an unverified roster" >&2
  exit 1
fi
KIRO_MODELS=()
[ -n "$KIRO_CELLS_RAW" ] && mapfile -t KIRO_MODELS <<< "$KIRO_CELLS_RAW"

python3 "$CFG" codex-enabled --root "$REPO_ROOT"; CODEX_RC=$?
case "$CODEX_RC" in
  0) CODEX_ENABLED=1 ;;
  1) CODEX_ENABLED=0 ;;
  *) echo "run-panel.sh: panel_config.py codex-enabled failed (exit $CODEX_RC; malformed/wrong-shape config?) — refusing to run" >&2
     exit 1 ;;
esac

# Expected tags come from enabled cells. Reject an empty or ambiguous roster.
ALL_TAGS=()
[ "$CODEX_ENABLED" = 1 ] && ALL_TAGS+=(codex)
ALL_TAGS+=("${KIRO_MODELS[@]##*:}")
if [ "${#ALL_TAGS[@]}" -eq 0 ]; then
  echo "run-panel.sh: panel has zero enabled cells (codex + all kiro cells disabled) — refusing an empty-panel PASS" >&2
  exit 1
fi

shopt -s nullglob
LENS_FILES=("$LENSES_DIR"/*.txt)
shopt -u nullglob
if [ "${#LENS_FILES[@]}" -eq 0 ]; then
  echo "run-panel.sh: no *.txt lens files found in $LENSES_DIR" >&2
  exit 1
fi
for lens_file in "${LENS_FILES[@]}"; do
  for tag in "${ALL_TAGS[@]}"; do
    printf '%s/%s\n' "$tag" "$(basename "$lens_file" .txt)"
  done
done > "$WORK/expected.txt" || exit 1

# Each cell shares the former worst-case budget across at most RETRIES attempts.
# Read Bash SECONDS without resetting it; never launch timeout with zero seconds.
#   try_panel <slot> <err> <launcher> <args...>
try_panel() {
  local slot="$1" err="$2" launcher="$3"; shift 3
  local a remaining rc=1 deadline=$((SECONDS + CELL_BUDGET))
  for ((a=1; a<=RETRIES; a++)); do
    remaining=$((deadline - SECONDS))
    if [ "$remaining" -le 0 ]; then
      rc=124
      echo "[timeout] $(basename "$slot" .md) exhausted ${CELL_BUDGET}s cell budget" >&2
      break
    fi
    [ "$a" -gt 1 ] && echo "[retry $((a - 1))/$RETRIES] $(basename "$slot" .md)" >&2
    "$launcher" "$remaining" "$@" > "$slot" 2>"$err" < "$DIFF" && rc=0 || rc=$?
    [ -s "$slot" ] && [ "$rc" -eq 0 ] && break
  done
  echo "$rc" > "$slot.rc"
}

launch_codex() {
  local limit="$1"; shift
  timeout --kill-after=5s "$limit" "$@"
}

# Kiro runs in isolated empty directories with no tools and an explicit agent file.
# This prevents automatic cwd context and inherited tools from changing its scope.
KIRO_CWD_BASE="$WORK/kiro-cwd"
[ -L "$KIRO_CWD_BASE" ] && { echo "run-panel.sh: \$KIRO_CWD_BASE is a symlink, refusing (TOCTOU guard)" >&2; exit 1; }
rm -rf "$KIRO_CWD_BASE"; mkdir -p "$KIRO_CWD_BASE"
kiro_env() {
  local cell_cwd="$1"; shift
  env -i PATH="$PATH" HOME="$cell_cwd" LANG="${LANG:-}" LC_ALL="${LC_ALL:-}" TMPDIR="${TMPDIR:-/tmp}" \
    ${KIRO_API_KEY:+KIRO_API_KEY="$KIRO_API_KEY"} "$@"
}
launch_kiro() {
  local limit="$1" cell_cwd="$2"; shift 2
  kiro_env "$cell_cwd" timeout --kill-after=5s "$limit" "$@"
}

# Kiro ignores stdin; embed bounded diff text, never ask it to read a file.
# The cap leaves room for prompt/context under the Linux single-argument limit.
KIRO_DIFF_CAP="${KIRO_DIFF_CAP:-100000}"
KIRO_DIFF_TEXT="$(head -c "$KIRO_DIFF_CAP" "$DIFF")"
# Record any truncated input; the semantic gate rejects incomplete required review.
if [ "${#KIRO_MODELS[@]}" -gt 0 ] && [ "$(wc -c < "$DIFF")" -gt "$KIRO_DIFF_CAP" ]; then
  KIRO_DIFF_TEXT+=$'\n[...TRUNCATED at '"$KIRO_DIFF_CAP"'B — full diff not sent to Kiro...]'
  echo "::warning::diff exceeds KIRO_DIFF_CAP (${KIRO_DIFF_CAP}B) — Kiro cells only see a truncated prefix" >&2
  : > "$WORK/kiro-diff-truncated.flag"
fi

for lens_file in "${LENS_FILES[@]}"; do
  lens="$(basename "$lens_file" .txt)"
  LENS_PROMPT="$(cat "$lens_file")"

  # Codex uses runner configuration; its catalog need not match Kiro model strings.
  if [ "$CODEX_ENABLED" = 1 ] && command -v codex >/dev/null 2>&1; then
    ( try_panel "$SLOT/codex-$lens.md" "$SLOT/codex-$lens.err" \
        launch_codex codex exec -s read-only --skip-git-repo-check "$LENS_PROMPT" ) &
  else echo "[skip] codex/$lens (disabled or binary absent)" >&2; : > "$SLOT/codex-$lens.md"; fi

  # Derive enabled Kiro calls and result tags from the same validated array.
  KIRO_INSTRUCTION="$LENS_PROMPT"$'\n\n'"Review ONLY the diff below; do not read or reference any other files:"$'\n\n'"$KIRO_DIFF_TEXT"
  for entry in "${KIRO_MODELS[@]}"; do
    m="${entry%%:*}"; tag="${entry##*:}"
    if command -v kiro-cli >/dev/null 2>&1; then
      CELL_CWD="$KIRO_CWD_BASE/$tag-$lens"; mkdir -p "$CELL_CWD"
      ( cd "$CELL_CWD" && try_panel "$SLOT/$tag-$lens.md" "$SLOT/$tag-$lens.err" \
          launch_kiro "$CELL_CWD" kiro-cli chat "$KIRO_INSTRUCTION" --model "$m" \
          --mode default --no-interactive --trust-tools= --wrap never ) &
    else echo "[skip] $tag/$lens (binary absent)" >&2; : > "$SLOT/$tag-$lens.md"; fi
  done
done

# Agy is not a CI roster cell. Local co-agent peer support is a separate contract.
wait

# Reuse the expected tags already computed from validated configuration.

# Aggregate the same cell/prompt pairs used for dispatch.
for lens_file in "${LENS_FILES[@]}"; do
  lens="$(basename "$lens_file" .txt)"
  [ "$CODEX_ENABLED" = 1 ] && record_result "$SLOT/codex-$lens.md" "codex/$lens" "$RESP"
  for entry in "${KIRO_MODELS[@]}"; do
    tag="${entry##*:}"; record_result "$SLOT/$tag-$lens.md" "$tag/$lens" "$RESP"
  done
done
echo "Panel responded ($(wc -l < "$RESP") / $(( ${#ALL_TAGS[@]} * ${#LENS_FILES[@]} )) cells): $(tr '\n' ' ' < "$RESP")"

# Record failed coverage. The semantic gate also checks every expected cell/prompt.
: > "$WORK/degraded-models.txt"
for model_tag in "${ALL_TAGS[@]}"; do
  # grep prints 0 and exits 1 on no match; do not append a second fallback zero.
  row_count="$(grep -c "^${model_tag}/" "$RESP" 2>/dev/null)"
  if [ "${row_count:-0}" -eq 0 ]; then
    echo "::warning::model '$model_tag' produced zero responses across all ${#LENS_FILES[@]} lenses — coverage degraded" >&2
    echo "$model_tag" >> "$WORK/degraded-models.txt"
  fi
done

# Record loss of independent vendor coverage; the semantic gate rejects it.
CODEX_DEAD=0
if [ "$CODEX_ENABLED" = 1 ] && grep -qx "codex" "$WORK/degraded-models.txt" 2>/dev/null; then
  CODEX_DEAD=1
fi
KIRO_TOTAL=${#KIRO_MODELS[@]}
# Preserve grep's one numeric result, including its no-match zero.
KIRO_DEGRADED_COUNT="$(grep -c "^kiro-" "$WORK/degraded-models.txt" 2>/dev/null)"
KIRO_ALL_DEAD=0
[ "$KIRO_TOTAL" -gt 0 ] && [ "${KIRO_DEGRADED_COUNT:-0}" -ge "$KIRO_TOTAL" ] && KIRO_ALL_DEAD=1
if [ "$CODEX_DEAD" = 1 ] || [ "$KIRO_ALL_DEAD" = 1 ]; then
  echo "::error::coverage collapsed to ≤1 vendor (codex dead=$CODEX_DEAD, kiro fully dead=$KIRO_ALL_DEAD) — no cross-vendor check remains; synthesize.sh surfaces this as a banner (ADR-016: no longer forces VERDICT)" >&2
  : > "$WORK/coverage-severe.flag"
fi

# Expose only scrubbed bounded diagnostics for empty slots.
for e in "$SLOT"/*.err; do
  [ -s "$e" ] || continue
  b="$(basename "$e" .err)"
  [ -s "$SLOT/$b.md" ] && continue   # A successful response needs no failure diagnostic.
  echo "--- [$b] skipped; stderr (last 25 lines, scrubbed) ---" >&2
  tail -25 "$e" | scrub_secrets >&2
done
