# Review-Memory Maintenance — Host-Only Procedure

Read from SKILL.md §5b after `push`. The host — never the planner/implementer — updates
`docs/pr-review/review-memory.md` as a **separate follow-up commit + push, AFTER the
fix push, never between commit and push**: `cmd_push` refuses to push unless `HEAD`
still equals the SHA `cmd_commit` recorded, so an intervening memory commit would move
HEAD and make every push fail.

## Update steps

- Append `MEMORY CANDIDATES` items **after de-duplication**, tagged with source `PR #N`.
- Parse `PANEL-QUALITY: <cell>=<unsupported>/<total>` lines (the chair's fixed output
  format) and increment the matching row of the "panel-cell judgment quality" table —
  add the row if absent. Parse failure or a missing section → skip silently (fail-open).
- Cap each section at its newest 30 lines and the whole file at 200 lines.
- Commit and push it directly (plain `git`, not `land_delta.sh` — the memory file is a
  host edit outside the worktree/landed-file set that script tracks, and it hard-denies
  this exact path, by design):
  `git add docs/pr-review/review-memory.md && git commit -m "docs: update PR review memory (PR #N)" && git push`.
  If this push fails (e.g. someone else pushed meanwhile), `git pull --rebase` once and
  retry — a lost memory update is not worth blocking the loop over; report and move on
  if it still fails.

## Threshold advisory (never auto-apply)

After updating the table, if any cell reaches cumulative `unsupported >= 5` AND
`unsupported/total >= 0.5`, tell the user to run
`python3 scripts/pr-review/panel_config.py set <cell> enabled false --root .` and to
write an ADR (ADR-012 precedent). Auto-disabling is forbidden — it collapses panel
coverage and risks fail-closed.
