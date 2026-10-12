// Captured from gh pr view --json on PR #253 (blocked: edited variant). Test data only.
export default {
 "baseRefName": "main",
 "comments": [
  {
   "author": {
    "login": "github-actions"
   },
   "authorAssociation": "NONE",
   "body": "<!-- oh-my-cloud-skills-pr-review -->\n<!-- review-run: 38216597186/1 -->\n## AI Code Review (Claude Fable 5.1 chair; configured peer panel)\n\n_Cells (model): codex/FULL kiro-opus/FULL kiro-gpt/FULL _\n\n**Status: PASSED** — No blocking issues found\nExplicit Issues contain no active CRITICAL or MAJOR findings\n\n## Summary\nThe PR removes co-agent's `commands/pr-autofix.md` wrapper so Claude Code registers a single `co-agent:pr-autofix` entry, and it updates every dependent artifact in the same change. I verified against base that the only four references to the deleted file are the Claude manifest, the Codex inventory, the generated Codex entry and the upstream-sync note, all of which the diff edits, and that the generator derives inventory sources from file globs with no alias or explicit-command entry keyed on this command, so the regenerated outputs match what the generator would produce. Counts in architecture, onboarding and runtime-verification docs are consistent with the base inventory minus one command (co-agent commands 6 to 5, procedures 71 to 70, entries unchanged at 69 because the entry already combined two sources).\n\n## Issues\n### CRITICAL\nNone.\n### MAJOR\nNone.\n### MINOR\nNone.\n\n## Dismissed findings\n- kiro-opus advisory about a widened tool-permission surface: not supported. The removed wrapper's `allowed-tools` field pre-approved a tool list for the command; the retained skill's frontmatter has only `name` and `description`, so invoking the skill inherits ordinary host permission prompting. The change narrows, not widens, pre-approved tooling. The panel cell labelled it unverified rather than a finding, so it is recorded here only for completeness.\n\n## Suggestions\n- The generated `.codex-plugin/workflow.md` still lists `pr-autofix` among the entry skills; that remains accurate because the Codex entry survives. No change needed.\n- The public overview page states that Codex exposes workflows including command wrappers; this is still true for the remaining co-agent commands. No change needed.\n- The Korean locale page keeps its co-agent-5 fragment identifier and gains a matching paragraph, preserving ADR-023 parity. I could not independently recompute the updated `source-hashes.json` digest without a shell; the Codex cell reports it matched, and the public-site coverage check in CI is the authoritative verification.\n\n### MEMORY CANDIDATES\n- Known false-positive pattern: removing a command wrapper that duplicated a skill does not widen tool permissions. A command's `allowed-tools` field pre-approves tools; a skill without that field falls back to normal prompting. Verify the skill frontmatter before alleging a privilege change.\n\n## Verdict\n\n---\n_Triggered by commit `4248c371f9134f5247e7f6389da0265fc316a740` · workflow: `.github/workflows/pr-review.yml`_\n",
   "createdAt": "2026-10-12T06:58:08Z",
   "includesCreatedEdit": true,
   "isMinimized": false,
   "minimizedReason": "",
   "url": "https://github.com/Atom-oh/oh-my-cloud-skills/pull/253#issuecomment-6119340750",
   "viewerDidAuthor": false
  }
 ],
 "headRefName": "fix/co-agent-pr-autofix-dedupe",
 "headRefOid": "4248c371f9134f5247e7f6389da0265fc316a740",
 "mergeable": "UNKNOWN",
 "number": 253,
 "state": "MERGED",
 "statusCheckRollup": [
  {
   "__typename": "CheckRun",
   "completedAt": "2026-10-12T07:19:13Z",
   "conclusion": "SUCCESS",
   "detailsUrl": "https://github.com/Atom-oh/oh-my-cloud-skills/actions/runs/38216597186/job/114702680908",
   "name": "AI Code Review",
   "startedAt": "2026-10-12T07:14:10Z",
   "status": "COMPLETED",
   "workflowName": "AI Code Review"
  },
  {
   "__typename": "CheckRun",
   "completedAt": "2026-10-12T07:14:10Z",
   "conclusion": "SUCCESS",
   "detailsUrl": "https://github.com/Atom-oh/oh-my-cloud-skills/actions/runs/38216599393/job/114702685946",
   "name": "Codex package validation",
   "startedAt": "2026-10-12T07:14:04Z",
   "status": "COMPLETED",
   "workflowName": "Codex package validation"
  },
  {
   "__typename": "CheckRun",
   "completedAt": "2026-10-12T07:17:26Z",
   "conclusion": "SUCCESS",
   "detailsUrl": "https://github.com/Atom-oh/oh-my-cloud-skills/actions/runs/38216599436/job/114702685924",
   "name": "Documentation site validation",
   "startedAt": "2026-10-12T07:14:04Z",
   "status": "COMPLETED",
   "workflowName": "Documentation site validation"
  }
 ],
 "title": "fix(co-agent): drop duplicate pr-autofix command registration",
 "url": "https://github.com/Atom-oh/oh-my-cloud-skills/pull/253"
}
