#!/usr/bin/env bash
# PreToolUse(Bash) hook — when the command LOOKS LIKE a `git push` invocation, run a
# 3-lens kiro_review.py pass (correctness/security/scope — see kiro_review.py's
# _LENSES) over the commit range about to be pushed, and block (exit 2) if it finds
# anything at/above the configured push_block level (default: warning — one tier
# stricter than the commit gate's, since this is the last checkpoint before content
# leaves the machine). A CRITICAL finding is a plain block; a WARNING-only set (no
# critical) is framed as "CHAIR JUDGMENT REQUIRED" — a hook can't call Claude, so the
# only way to hand a verdict to the chair is exit 2 + stderr, which the calling agent
# then reads and judges before deciding whether to bypass. Same ADVISORY-gate caveats
# as pre-commit-review.sh apply (regex matching over Bash tool_input text, not a
# security boundary). OPT-IN — `review.on_push` defaults to false: this range's diff
# CONTENT is sent to Kiro's backend, 3 times (once per lens). Fails OPEN on any
# internal error, missing/unauthenticated kiro-cli, or an unresolvable push range — a
# broken reviewer must never wedge a push.
set -euo pipefail

if [ "${KIRO_REVIEW:-}" = "off" ]; then
  exit 0
fi

SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"

# Same rationale as pre-commit-review.sh: `.claude/kiro.local.json` (holding
# `review.on_push`) lives at the repo root, not this hook's cwd.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

# Same reason as pre-commit-review.sh for doing boundary matching in Python, and for
# saving the payload to a file rather than a bash variable.
PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT
cat > "$PAYLOAD_FILE"

if ! python3 "$SK/hook_match.py" git-push < "$PAYLOAD_FILE"; then
  exit 0
fi

# Same inline-bypass rationale as pre-commit-review.sh: `KIRO_REVIEW=off git push ...`
# is only ever real environment for the eventual `git push` subprocess, never for this
# hook's own process — recognized directly in the payload text instead.
if python3 "$SK/hook_match.py" bypass push < "$PAYLOAD_FILE"; then
  exit 0
fi

if ! python3 "$SK/kiro_config.py" review-on-push --root "$ROOT" >/dev/null 2>&1; then
  exit 0
fi

# SKIP (fail-open) when the push invocation may not correspond to the range this hook
# would diff (@{upstream}...HEAD, or the trunk merge-base) — see hook_match.py's
# push-scope-mismatch docstring for the exact mismatch classes (an inline
# KIRO_REVIEW=off bypass on that occurrence, repo/tree redirect, a preceding
# cd/pushd, a preceding git commit in the same invocation whose content the diff
# would miss, --delete/--dry-run with nothing to review, or a refspec/multiref push
# the computed range doesn't describe).
if python3 "$SK/hook_match.py" push-scope-mismatch < "$PAYLOAD_FILE"; then
  echo "⚠️  kiro review SKIPPED (fail-open): this push invocation may not correspond to" \
       "the range this hook would diff (-C/--git-dir/--work-tree/GIT_DIR=/" \
       "GIT_WORK_TREE=, a preceding cd/pushd, a preceding git commit in the same" \
       "invocation whose content the diff would miss, --delete/--dry-run with" \
       "nothing to review, or an explicit refspec) — reviewing the wrong range" \
       "could wrongly block this push. Run" \
       "/kiro:review --range --lenses correctness,security,scope on the right scope" \
       "if needed." >&2
  exit 0
fi

python3 "$SK/kiro_review.py" --range --lenses correctness,security,scope --root "$ROOT" 1>&2
exit $?
