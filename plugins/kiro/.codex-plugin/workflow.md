# Kiro delegation in Codex

References to Claude planning, reviewing or committing in the shared procedures
mean the current host, Codex. Kiro remains the external implementer or reviewer.
Use `setup`, `configure`, `delegate` or `review` according to the requested task.
Read-only review must not route into the write-capable delegation pipeline.

The `setup`, `configure` and `review` entries contain Codex invocation procedures.
Use their installed `run.py` commands rather than expanding Claude placeholders.
`kiro_codex.py doctor` diagnoses local setup without writing files; `doctor --probe`
checks actual authentication with the configured review model and effort.
`kiro_codex.py review` runs without tool privileges or consumer agent files and
returns structured PASS/FAIL/ERROR/NO_CHANGES results. Errors, partial coverage and
oversized inputs are never reported as a successful review. Automatic hooks retain
their separate opt-in and failure rules.

Retain the worktree capture and scope checks. The separate opt-in to grant Kiro
`execute_bash` remains a trust decision; a worktree is not a shell sandbox.
Load the shared delegate agent procedure rather than treating its Claude
frontmatter as a native Codex agent configuration.
