---
description: Run the same Kiro-powered review the pre-commit hook runs, on demand — against staged changes by default, or specific paths.
allowed-tools: Bash(python3:*)
---

# kiro: review

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"` and
`ROOT="$(git rev-parse --show-toplevel)"` — pass `--root "$ROOT"` (not `.`) so the
review reads the repo-root `.claude/kiro.local.json` regardless of the cwd, same as the
pre-commit hook does.

**Before running, tell the user this one-line caution (every invocation, not just the
first):** the Kiro reviewer reads the diff via `fs_read`, which is not path-restricted —
a prompt-injection payload inside an untrusted diff could direct it to read an unrelated
file and include it in the response sent to Kiro's backend. Only review diffs whose
authorship you trust (typically your own changes). This matters here specifically
because `/kiro:review` is always available even while the automatic hook's
`review.on_commit` is off — the off-default protects the automatic path, not this
manual one.

Run the review against staged changes (default) or the paths given in `$ARGUMENTS`:

```bash
python3 "$SK/kiro_review.py" --staged --root "$ROOT"
```

Or, if the user gave specific paths, pass each path as its **own quoted argv token**
after `--` — never splice the raw `$ARGUMENTS` string in unquoted (it can carry shell
metacharacters that the shell would re-interpret before `kiro_review.py` sees them).
This reviews the **full working-tree diff** for those paths (staged + unstaged) — not
staged-only — so an in-progress edit that hasn't been `git add`ed yet is still
reviewable:

```bash
# one quoted token per path the user named — e.g. two files:
python3 "$SK/kiro_review.py" --root "$ROOT" -- "src/foo.py" "src/bar.py"
```

This runs even if `review.on_commit` is off (that setting only gates the automatic
pre-commit hook, not a manual `/kiro:review`). Report the findings as printed — advisory
findings are informational; a `critical` finding (or whatever `review.block` is set to)
means `git commit` would currently be blocked by the hook until it's fixed.
