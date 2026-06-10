# test-reactive-pptx-tokens.sh — PPTX/brand extraction drives core design tokens
# Sourced by run-all.sh (set -euo pipefail) — no shebang / no exit.
RP="plugins/aws-content-plugin/skills/reactive-presentation"

# --- theme.css wires --accent THROUGH the brand token --pptx-accent1 ---
TC="$(cat "$RP/assets/theme.css" 2>/dev/null || true)"
assert_grep_match "var\(--pptx-accent1\b" "$TC" "theme.css wires --accent through brand token --pptx-accent1"

U=$( { grep -oE "var\(--pptx" "$RP/assets/theme.css" 2>/dev/null || true; } | wc -l | tr -d ' ')
assert_grep_match "^[1-9]" "$U" "theme.css consumes >=1 brand token (was 0)"

# --- extractor's CSSGenerator emits brand/role tokens, not legacy component colors ---
GENOUT="$(cd "$RP" && python3 -c "
import sys; sys.path.insert(0,'scripts')
import extract_pptx_theme as e
manifest = {
    'source_file': 'synthetic.pptx',
    'theme_name': 'Synthetic',
    'colors': {
        'accent1': '#11AA22', 'accent2': '#2233CC',
        'dk1': '#101010', 'lt1': '#FFFFFF',
        'dk2': '#0A0B10', 'lt2': '#E8EAF0',
    },
}
print(e.CSSGenerator(manifest).generate())
" 2>/dev/null || true)"
assert_grep_match "\-\-pptx-accent1|\-\-accent" "$GENOUT" "override generator emits brand/role tokens"
assert_grep_match "11AA22" "$GENOUT" "override generator carries extracted accent1 color into tokens"
