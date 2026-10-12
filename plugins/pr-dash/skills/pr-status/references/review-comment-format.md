# AI review comment: trust rules

The CI review posts and then edits one PR comment. pr-dash's pane and this skill read
it the same way, mirroring co-agent pr-autofix's gate parsing.

## Which comment

- Author login is `github-actions` or `github-actions[bot]`. Comments by anyone else
  are ignored, even when they contain the marker or a status line.
- The body contains the marker `<!-- oh-my-cloud-skills-pr-review -->`.
- With several such comments, use the newest by `createdAt`.

## Which lines count

Ignore, as co-agent's `review_gate.py` does: fenced code (a fence of 3+ backticks
or tildes closes only with the same character and at least the same length),
indented code (4 spaces or a tab), block quotes (`>` lines and the lazy
continuation lines after them, up to a blank line, heading, list item or fence) and
HTML comments (`<!-- … -->`, including multi-line ones). Trim the remaining lines,
then read:

| Field | Pattern | Example |
|---|---|---|
| Status | first line starting `**Status: X**`, X in PASSED, BLOCKED, ERROR, PENDING | `**Status: BLOCKED** — CRITICAL/MAJOR issues must be resolved before merge` |
| Reviewed commit | ``Triggered by commit `<sha>` `` | ``_Triggered by commit `4248c37…` · workflow: …_`` |
| Reviewer cells | line starting `_Cells (model):` | `_Cells (model): codex/FULL kiro-opus/FULL _` |
| Findings | list items marked `-`, `+`, `*`, `1.` or `1)` under `### CRITICAL`, `### MAJOR`, `### MINOR` until the next heading | `- **Gate bypass in merge helper** (confirmed). …` |

A severity section that contains only `None.` (or `None`, `없음`), with or without a
list marker, has no findings.
The review is for the current head when the head SHA equals the reviewed commit or
starts with it; otherwise it is stale and describes an older commit.
