---
description: Run the same Kiro-powered review the pre-commit hook runs, on demand — against staged changes by default, or specific paths.
allowed-tools: Bash(python3:*), AskUserQuestion
---

# kiro: review

$ARGUMENTS

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"`. `kiro_review.py` resolves
the repo root itself (`git rev-parse --show-toplevel`, run as a python3 subprocess — not
a `Bash` tool call, so it stays inside this command's `Bash(python3:*)` allowed-tools
scope) whenever `--root` is omitted, so it reads the repo-root `.claude/kiro.local.json`
regardless of the cwd, same as the pre-commit hook does. Pass `--root` explicitly only
if you need to point at a DIFFERENT repo than the cwd's.

**Reviewer read-scoping:** when the plugin-generated `kiro-reviewer` agent exists
(`/kiro:setup` writes it), its `preToolUse` hook confines `fs_read` to the isolated
temp dir holding only the diff — a prompt-injection payload in an untrusted diff that
tries to read an unrelated file (e.g. credentials) is refused at the tool layer.
`kiro_review.py` verifies the agent file is untampered before using it; **if it's
missing or fails verification, the DEFAULT is to SKIP the review entirely (fail-open) —
never a silent unguarded fallback.** A warning printed right before an already-unguarded
call runs is not a real chance for anyone to object to it, so this command no longer
runs one that way. If the skip happens, tell the user and offer `/kiro:setup` as the fix;
only if they explicitly want to review anyway despite no guard (rare — e.g. urgent,
authorship already trusted, `/kiro:setup` isn't convenient right now) use
`AskUserQuestion` to confirm **before** running anything, then re-run with
`--allow-unguarded`. Never pass `--allow-unguarded` without that confirmation happening
first.

Run the review against staged changes (default) or the paths given in `$ARGUMENTS`:

```bash
python3 "$SK/kiro_review.py" --staged --progress
```

**Always pass `--progress` here, and run the command in a BACKGROUND Bash**, polling its
output. kiro-cli has no `stream-json`-style machine-readable stream (verified 2026-07 —
see `references/kiro-headless.md` "Watching a run"), so `--progress` tails kiro's own
human-readable output to stderr as it arrives, prefixed `[kiro:<lens>]`, with a 15s
"still running" heartbeat. Foreground, nothing appears until the whole call returns
(up to `review.timeout`, ×3 lenses in `--range` mode) — that blind wait is the only
reason to omit the flag, and there isn't one for an interactive command. Report progress
lines only as progress; the **findings** are what the final output prints.

Or, if the user gave specific paths, pass each path as its **own quoted argv token**
after `--` — never splice the raw `$ARGUMENTS` string in unquoted (it can carry shell
metacharacters that the shell would re-interpret before `kiro_review.py` sees them).
This reviews the **full working-tree diff** for those paths (staged + unstaged) — not
staged-only — so an in-progress edit that hasn't been `git add`ed yet is still
reviewable:

```bash
# one quoted token per path the user named — e.g. two files:
python3 "$SK/kiro_review.py" --progress -- "src/foo.py" "src/bar.py"
```

This runs even if `review.on_commit` is off (that setting only gates the automatic
pre-commit hook, not a manual `/kiro:review`). Report the findings as printed — advisory
findings are informational; a `critical` finding (or whatever `review.block` is set to)
means `git commit` would currently be blocked by the hook until it's fixed.

To run the same 3-lens pass the pre-push hook runs (correctness/security/scope, in
parallel, over the commit range about to be pushed — `@{upstream}...HEAD`, falling back
to the trunk merge-base), on demand:

```bash
python3 "$SK/kiro_review.py" --range --lenses correctness,security,scope --progress
```

This works even if `review.on_push` is off. A `critical` finding is framed as
`BLOCKED`; a `warning`-only set (no critical) is framed as `CHAIR JUDGMENT REQUIRED` —
read each finding against the actual change and judge whether it's acceptable for this
push before deciding to proceed.

If the run reported a skip (missing/tampered reviewer agent) and the user, after being
told, explicitly asks to review anyway:

```bash
# only after AskUserQuestion confirmation — never pass this speculatively
python3 "$SK/kiro_review.py" --staged --allow-unguarded
```
