---
description: Run the same Kiro-powered review the pre-commit hook runs, on demand — against staged changes by default, or specific paths.
allowed-tools: Bash(python3:*), AskUserQuestion
---

# kiro: review

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`. `kiro_review.py` resolves
the repo root itself (`git rev-parse --show-toplevel`) when `--root` is omitted, so it
reads the repo-root `.claude/kiro.local.json` regardless of cwd, same as the hooks —
pass `--root` only to target a DIFFERENT repo than the cwd's.

**Reviewer read-scoping:** the plugin-generated `kiro-reviewer` agent's `preToolUse`
hook confines `fs_read` to the isolated temp dir holding only the diff, so a
prompt-injection payload in an untrusted diff can't read an unrelated file (e.g.
credentials). `kiro_review.py` verifies that agent file is untampered before using it;
**if it's missing or fails verification, the DEFAULT is to SKIP the review entirely
(fail-open) — never a silent unguarded fallback.** On a skip, tell the user and offer
`/kiro:setup` as the fix. Only if they explicitly want to review anyway with no guard,
confirm via `AskUserQuestion` **before** running anything, then re-run with
`--allow-unguarded` — never pass that flag without the confirmation happening first.

Run the review against staged changes (default) or the paths given in `$ARGUMENTS`:

```bash
python3 "$SK/kiro_review.py" --staged --progress
```

**Pass `--progress` and run in a BACKGROUND Bash, polling the output** — kiro-cli has no
machine-readable event stream (`references/kiro-headless.md` → "Watching a run"), so
`--progress` tails kiro's own output to stderr as it arrives, prefixed `[kiro:<lens>]`,
with a 15s heartbeat; foreground shows nothing until the whole call returns (up to
`review.timeout`, ×3 lenses in `--range` mode). The **findings** are what the final
output prints; progress lines are just progress.

If the user gave specific paths, pass each as its **own quoted argv token** after `--` —
never splice the raw `$ARGUMENTS` string in unquoted (it can carry shell metacharacters
the shell would re-interpret before `kiro_review.py` sees them). Path mode reviews the
**full working-tree diff** for those paths (staged + unstaged), so an un-`git add`ed
edit is still reviewable:

```bash
# one quoted token per path the user named — e.g. two files:
python3 "$SK/kiro_review.py" --progress -- "src/foo.py" "src/bar.py"
```

This runs even if `review.on_commit` is off (that setting only gates the automatic
hook). Report the findings as printed — advisory findings are informational; a
`critical` finding (or whatever `review.block` is set to) means `git commit` would
currently be blocked by the hook until it's fixed.

To run the same 3-lens pass the pre-push hook runs (correctness/security/scope, in
parallel, over `@{upstream}...HEAD` or the trunk merge-base fallback), on demand — this
works even if `review.on_push` is off:

```bash
python3 "$SK/kiro_review.py" --range --lenses correctness,security,scope --progress
```

A `critical` finding is framed `BLOCKED`; a `warning`-only set is framed
`CHAIR JUDGMENT REQUIRED` — read each finding against the actual change and judge
whether it's acceptable for this push before deciding to proceed.

If the run reported a skip (missing/tampered reviewer agent) and the user, after being
told, explicitly asks to review anyway:

```bash
# only after AskUserQuestion confirmation — never pass this speculatively
python3 "$SK/kiro_review.py" --staged --allow-unguarded
```
