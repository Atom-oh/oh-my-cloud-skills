#!/usr/bin/env bash
# PreToolUse(Bash) hook — when the command LOOKS LIKE a `git push` invocation, run
# atlas_sync.py over the range about to be pushed so drifted atlas docs are fixed and
# committed BEFORE the push executes, letting the `docs(atlas): sync ...` commit ride
# along in that same push. Same ADVISORY-gate caveats as the kiro hooks apply (regex
# matching over Bash tool_input text, not a security boundary). OPT-IN —
# `sync.on_push` defaults to false: enabling it sends covered-file diff CONTENT to
# Anthropic on every push. Fails OPEN on any internal error, missing claude binary, or
# an unresolvable range — a doc-syncer that can wedge a push is worse than one that
# occasionally misses a stale doc.
# NOT a bare `set -e`: under `-e` alone, `${CLAUDE_PLUGIN_ROOT}` being unset (no
# default expansion below) or `mktemp` failing would exit non-zero WITHOUT the
# stderr advisory this hook's whole contract promises ("every failure path prints
# an advisory and exits 0") — a silent exit 1 satisfies "never blocks" (PreToolUse
# only blocks on exit 2) but breaks the stronger, separately documented promise.
# `-u` and `pipefail` stay: they only matter for commands this file writes itself,
# and every guard below is explicit rather than relying on them to trip.
set -uo pipefail

if [ "${ATLAS_SYNC:-}" = "off" ]; then
  exit 0
fi

if [ -z "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  echo "atlas-sync: CLAUDE_PLUGIN_ROOT is unset — skipping doc sync" >&2
  exit 0
fi
SK="${CLAUDE_PLUGIN_ROOT}/skills/atlas/scripts"

# Same rationale as the kiro hooks: `.claude/atlas.local.json` (holding
# `sync.on_push`) lives at the repo root, not this hook's cwd.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

# Same reason as the kiro hooks for doing boundary matching in Python, and for saving
# the payload to a file rather than a bash variable.
PAYLOAD_FILE="$(mktemp)" || { echo "atlas-sync: mktemp failed — skipping doc sync" >&2; exit 0; }
trap 'rm -f "$PAYLOAD_FILE"' EXIT
cat > "$PAYLOAD_FILE"

if ! python3 "$SK/hook_match.py" git-push < "$PAYLOAD_FILE"; then
  exit 0
fi

# hook_match.py was copied verbatim from the kiro plugin, so its `bypass push` mode
# recognises the literal `KIRO_REVIEW=off` — kept as-is because it is harmless and it
# usefully means `KIRO_REVIEW=off git push ...` skips atlas too.
if python3 "$SK/hook_match.py" bypass push < "$PAYLOAD_FILE"; then
  exit 0
fi

# Atlas's OWN inline bypass (`ATLAS_SYNC=off git push ...`): hook_match.py's
# _BYPASS_ENV_RE is hardcoded to `KIRO_REVIEW=off`, so it does not know this token.
# Grepping the raw payload is coarser than hook_match.py's boundary grammar (it would
# also match the token inside an unrelated quoted string), but the only consequence of
# a coarse match here is an EXTRA SKIP, which is the fail-open-safe direction — the
# opposite mistake, missing a real bypass, would run a sync the user explicitly asked
# to skip.
if grep -Eq '(^|[[:space:];&|])ATLAS_SYNC=off' "$PAYLOAD_FILE"; then
  exit 0
fi

if ! python3 "$SK/atlas_config.py" sync-on-push --root "$ROOT" >/dev/null 2>&1; then
  exit 0
fi

# SKIP (fail-open) when the push invocation may not correspond to the range this hook
# would sync against (@{upstream}...HEAD, or the trunk merge-base) — see
# hook_match.py's push-scope-mismatch docstring for the exact mismatch classes
# (repo/tree redirect, a preceding cd/pushd, a preceding git commit in the same
# invocation whose content the diff would miss, or --delete with nothing to sync).
if python3 "$SK/hook_match.py" push-scope-mismatch < "$PAYLOAD_FILE"; then
  echo "⚠️  atlas sync SKIPPED (fail-open): this push invocation may not correspond to" \
       "the range this hook would sync against (-C/--git-dir/--work-tree/GIT_DIR=/" \
       "GIT_WORK_TREE=, a preceding cd/pushd, a preceding git commit in the same" \
       "invocation whose content the diff would miss, or --delete with nothing to" \
       "sync) — syncing against the wrong range could rewrite docs to the wrong code." \
       "Run /atlas:sync on the right scope if needed." >&2
  exit 0
fi

# Deliberate difference from the kiro original, which ends by propagating
# kiro_review.py's exit status because it is a BLOCKING gate: this hook must NEVER
# block — a doc-syncer that can wedge a push is
# worse than one that occasionally misses a stale doc. atlas_sync.py's stdout is
# redirected to stderr so hook output never lands on stdout, and the hook ends with a
# plain `exit 0` regardless of what atlas_sync.py returned.
python3 "$SK/atlas_sync.py" --root "$ROOT" 1>&2 || true
exit 0
