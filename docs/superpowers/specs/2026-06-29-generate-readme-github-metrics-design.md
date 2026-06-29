# Design — Live GitHub metrics + langgraph-style header for `/generate-readme`

- **Date**: 2026-06-29
- **Plugin**: `project-init`
- **Status**: Approved (design phase)
- **Scope**: Add live GitHub-API metrics + self-updating, centered shields.io badge header to the README generator. Degrade gracefully to today's git-only flow.

## Problem

`project-init`'s `/generate-readme` produces bilingual READMEs with shields.io badges, but it only sources metadata from **local git** (`git remote`, `git describe`, the `LICENSE` file). It never queries GitHub, so generated READMEs lack the polished, live "project health" header users expect — the look of, e.g., the LangGraph README (centered logo → tagline → a centered badge row of license / version / downloads).

## Goal

When `/generate-readme` runs, automatically fetch **live repository metrics** (stars, forks, watchers, open issues, license, latest release/tag, description, primary language) and emit a **centered, self-updating badge header** in the LangGraph aesthetic — while keeping the existing bilingual EN/KO structure and language toggle. If GitHub is unreachable (no `gh`, offline, private repo, no remote), fall back to the current git-only behavior with a note.

Non-goals (deliberately out of scope, per scoping decision):
- Repo-type preset templates (demo/skill/tool/library section + badge presets).
- Interactive structured content prompts beyond what `/generate-readme` already collects.
- Frozen/snapshot metric numbers as the primary header (badges stay self-updating; a snapshot stats line is optional).

## Approach

A **new local-only helper script** does the fetch + Markdown emission; the upstream command file gets a **minimal edit** to call it. This keeps the divergence surface tiny and the logic testable.

### Component 1 — `skills/project-scaffolder/scripts/fetch_github_metrics.py` (new, local-only)

Single-purpose CLI. **What it does / how it's used / what it depends on:**

- **Input**: optional `--repo owner/name` (else auto-detect), `--dir <path>` (repo root; default cwd), `--dry-run` (format from a fixture JSON on stdin, no network), `--json` (emit only the metrics JSON).
- **Owner/repo detection**: parse `git -C <dir> remote get-url origin`, handling all common forms:
  - `git@github.com:owner/repo.git`
  - `https://github.com/owner/repo(.git)`
  - `ssh://git@github.com/owner/repo.git`
  - Non-GitHub remotes → emit nothing fetchable, signal git-only fallback.
- **Fetch (degradation chain)**:
  1. `gh api repos/{owner}/{repo}` and `gh api repos/{owner}/{repo}/releases/latest` (authenticated, best).
  2. If `gh` absent/unauthenticated → unauthenticated `curl -fsSL https://api.github.com/repos/{owner}/{repo}` (+ `/releases/latest`). Tolerate rate-limit/404.
  3. If both fail → return `{available: false}`; caller uses git-only flow.
- **Metrics collected**: `description`, `license.spdx_id`, `stargazers_count`, `forks_count`, `subscribers_count`, `open_issues_count`, latest release `tag_name` (fallback to `git describe`), `default_branch`, `language`, `homepage`, `archived`.
- **Ecosystem detection** (local files, no network):
  - PyPI: `pyproject.toml` / `setup.cfg` / `setup.py` → derive package name → enable `pypi/v` + `pepy/dt` (downloads) badges.
  - CI: any `.github/workflows/*.y*ml` → enable an Actions workflow-status badge for the default branch.
- **Output**:
  - `--json`: the metrics dict (for the command to read fields).
  - default: a ready-to-paste **centered badge block** (see Component 2) + an optional one-line snapshot stats comment.
- **Reliability**: never raises to the shell — wraps fetch/parse in try/except, prints a diagnostic to stderr, exits `0` with `{available:false}` so the command always proceeds.

### Component 2 — Badge block (LangGraph aesthetic, bilingual-aware)

Centered, self-updating shields.io badges (shields queries GitHub/PyPI itself, so numbers stay live without regeneration):

```markdown
<div align="center">

![License](https://img.shields.io/github/license/OWNER/REPO?style=flat-square)
![Release](https://img.shields.io/github/v/release/OWNER/REPO?style=flat-square)
![Stars](https://img.shields.io/github/stars/OWNER/REPO?style=flat-square&logo=github)
![CI](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/CI_FILE?branch=BRANCH&style=flat-square)
<!-- when PyPI detected: -->
![PyPI](https://img.shields.io/pypi/v/PKG?style=flat-square&logo=pypi)
![Downloads](https://img.shields.io/pepy/dt/PKG?style=flat-square)

</div>
```

- Badge **selection rules**: always license + stars; add `github/v/release` (or tag) when a release/tag exists; add CI badge when a workflow exists; add PyPI version + downloads only when a PyPI package is detected. Skip any badge whose data is unavailable rather than rendering a broken one.
- The existing EN/KO `<a><img></a>` **language toggle** is preserved, placed under the centered badge row.
- Optional, off by default: a one-line `> ⭐ N stars · 🍴 N forks` snapshot line (a moment-in-time stat); the self-updating badges are the canonical source.

### Component 3 — `commands/generate-readme.md` edit (minimal; then sync-excluded)

- Add to `allowed-tools`: `Bash(gh:*)`, `Bash(curl:*)`, `Bash(python3:*)`.
- Insert **Step 2.5 — Fetch live GitHub metrics**: run `python3 skills/project-scaffolder/scripts/fetch_github_metrics.py`; if `available`, use its badge block in the top layout and fill Overview description/license/latest-release from the metrics; else continue with git-only detection and note it in the Step 8 summary.
- Update the Step 7 validation checklist to include the centered badge block.

### Component 4 — `readme-template.md` (already local-branch) update

Document the centered badge block, the GitHub-vs-PyPI badge-selection rules, and the degradation note, so the template is the single source of truth for header layout.

### Interaction with `/init-project` (no conflict)

`/init-project` **Step 12** also generates `README.md`, and it reads the **same**
`readme-template.md`. This is the reconciliation point, not a conflict:

- Putting the centered badge block + selection rules in the shared `readme-template.md`
  (Component 4) means **both** commands emit the identical langgraph-style header — `/init-project`
  inherits it for free, with **no edit to `init-project.md`**.
- The shields.io badge URLs only need `owner/repo` (filled from `git remote` — which `/init-project`
  already detects in its flow); the badges are **self-updating**, so they light up automatically
  once the repo is pushed to GitHub, even though a freshly-scaffolded project has no metrics yet.
- The **live-fetch helper** is therefore wired into `/generate-readme` **only** — the command run
  against a real, pushed repo where metrics and a description exist. `/init-project` deliberately
  does **not** call the helper: a brand-new repo usually has no remote (the fetch would no-op), and
  not editing `init-project.md` keeps the upstream-divergence surface to a single command file.
- Both commands keep their existing "if `README.md` exists, preserve user content" guard, so
  running `/generate-readme` after `/init-project` updates rather than clobbers.

> Decision: minimize divergence — only `generate-readme.md` gets the helper call; `init-project.md`
> stays pristine and gets the new header purely through the shared template. (Revisit only if we
> later want live metrics injected at scaffold time.)

### Component 5 — Upstream-sync handling

`commands/generate-readme.md` is currently an upstream-synced file. Adding it to the exclude list in `references/upstream-sync.md` (and its `diff`/`rsync` snippets) prevents a future upstream pull from clobbering the new Step 2.5. The new helper script and the already-local `readme-template.md` are not at risk (rsync without `--delete` won't touch new local files).

## Testing

New `tests/structure/test-generate-readme-metrics.sh` (sourced by `run-all.sh`):
- Remote-URL parsing: `git@github.com:o/r.git`, `https://github.com/o/r`, `https://github.com/o/r.git`, `ssh://git@github.com/o/r.git`, and a non-GitHub remote → all parse to the right `owner/repo` or signal fallback.
- `--dry-run` with a fixture metrics JSON on stdin → emits the expected centered badge block (PyPI present vs absent; CI present vs absent; no release).
- Fallback: simulated "no remote" / "not available" → exits 0 with `{available:false}` and emits no broken badge.
- No network is required by any test (all fetch paths are stubbed/dry-run).

## Degradation matrix

| Environment | Result |
|---|---|
| `gh` installed + authed | Full live metrics + all applicable badges |
| only `curl`, public repo | Public metrics + badges (no auth-only fields) |
| private repo, no `gh` auth | git-only flow + note |
| no remote / non-GitHub / offline | git-only flow (today's behavior) + note |

## Files touched

- **New**: `plugins/project-init/skills/project-scaffolder/scripts/fetch_github_metrics.py`
- **New**: `tests/structure/test-generate-readme-metrics.sh`
- **Edit**: `plugins/project-init/commands/generate-readme.md` (allowed-tools + Step 2.5 + validation) — add to sync-exclude
- **Edit**: `plugins/project-init/skills/project-scaffolder/references/readme-template.md` (badge block + rules)
- **Edit**: `plugins/project-init/references/upstream-sync.md` (exclude `commands/generate-readme.md`)
