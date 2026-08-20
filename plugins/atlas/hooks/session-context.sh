#!/usr/bin/env bash
# SessionStart hook — emit the plugin banner AND the operative atlas reading rule,
# plus (when the toggle is on) a note that push-time auto-sync is armed.
#
# WHY THIS EXISTS: a plugin's own CLAUDE.md is NEVER injected into a consuming repo's
# session context (only the *project's* own CLAUDE.md files are). So a reading rule
# that lives only in `plugins/atlas/CLAUDE.md` is dead in every repo where atlas is
# installed as a plugin — the host would keep re-deriving knowledge from source with
# no error to explain why the atlas docs were never consulted. The one plugin-side
# channel whose output DOES land in context is a SessionStart hook, so the rule has to
# be emitted from here to be real. `plugins/atlas/CLAUDE.md` keeps the long rationale
# (it's still loaded when working ON this plugin); this script carries the minimum the
# host must know in ANY repo.
#
# Deliberate difference from kiro's session-routing.sh: kiro's routing blocks are
# gated on their toggles and quiet when off, but the reading rule below is the WHOLE
# POINT of this hook — it applies whether or not push-time sync is enabled, so it
# prints unconditionally. Only the sync.on_push note is toggle-gated.
#
# NOT `set -e`: a non-zero SessionStart hook is a startup error, far worse than a
# silently missing toggle note.
set -uo pipefail

SK="${CLAUDE_PLUGIN_ROOT}/skills/atlas/scripts"

echo "atlas loaded. Per-topic repo wiki with push-time drift sync: /atlas:init · sync · add-doc · graph · configure."

# `--root` omitted on purpose: atlas_config.py resolves the repo root itself via
# `git rev-parse --show-toplevel`, so this works from any cwd the session starts in.
# Every call is best-effort (`|| echo` fallback) — a missing/broken config must never
# make SessionStart fail.
ATLAS_ROOT="$(python3 "$SK/atlas_config.py" atlas-root 2>/dev/null || echo docs/atlas)"

# The atlas root is printed by its own `echo` below, never inside the heredoc. Inside
# the quoted heredoc the `$ATLAS_ROOT` expansion would reach the host verbatim — and
# that variable does not exist in the ordinary Bash tool calls the host makes later.
# Left as its own `echo` rather than unquoting the heredoc: the prose is full of
# backticks, which an unquoted heredoc would run as command substitution.
echo ""
echo "[atlas] This repo keeps a per-topic doc wiki at: $ATLAS_ROOT"
cat <<'ATLAS'
[atlas] Reading rule (always in effect): before answering questions about this repo's
architecture or conventions, read the atlas root's `INDEX.md` FIRST. Choose which docs
to open by their `description` and `covers` fields in that index — only then read the
bodies of the chosen docs. Prefer an atlas doc over re-deriving the same knowledge
from source: the docs are drift-checked against `code_rev`, so a matching doc is the
cheaper and already-verified path to the same answer.
ATLAS

if python3 "$SK/atlas_config.py" sync-on-push >/dev/null 2>&1; then
  cat <<'ATLAS'

[atlas] sync.on_push is ON for this repo: just before a `git push`, drifted atlas docs
are auto-fixed and a `docs(atlas): sync ...` commit may be created so the fix rides
along in that same push.
ATLAS
fi

exit 0
