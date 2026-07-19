---
description: Run the same Kiro-powered review the pre-commit hook runs, on demand — against staged changes by default, or specific paths.
allowed-tools: Bash(python3:*)
---

# kiro: review

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`.

Run the review against staged changes (default) or the paths given in `$ARGUMENTS`:

```bash
python3 "$SK/kiro_review.py" --staged --root .
```

Or, if the user gave specific paths, pass each path as its **own quoted argv token**
after `--` — never splice the raw `$ARGUMENTS` string in unquoted (it can carry shell
metacharacters that the shell would re-interpret before `kiro_review.py` sees them).
This reviews the **full working-tree diff** for those paths (staged + unstaged) — not
staged-only — so an in-progress edit that hasn't been `git add`ed yet is still
reviewable:

```bash
# one quoted token per path the user named — e.g. two files:
python3 "$SK/kiro_review.py" --root . -- "src/foo.py" "src/bar.py"
```

This runs even if `review.on_commit` is off (that setting only gates the automatic
pre-commit hook, not a manual `/kiro:review`). Report the findings as printed — advisory
findings are informational; a `critical` finding (or whatever `review.block` is set to)
means `git commit` would currently be blocked by the hook until it's fixed.
