# Live GitHub Metrics for /generate-readme — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local helper that fetches live GitHub metrics and emits a centered, self-updating shields.io badge block, then wire it into project-init's `/generate-readme`.

**Architecture:** A new stdlib-only Python helper (`fetch_github_metrics.py`) detects `owner/repo` from the git remote, fetches metrics via `gh` with an unauthenticated `urllib` fallback, detects PyPI/CI locally, and prints either a metrics JSON or a ready-to-paste centered badge block. `generate-readme.md` gets a minimal edit to call it (and is added to the upstream-sync exclude list). The shared `readme-template.md` documents the badge block so `/init-project` inherits the same header with no edit.

**Tech Stack:** Python 3 (stdlib: subprocess, json, re, argparse, urllib), Bash TAP tests (`tests/run-all.sh`), Markdown command/skill files.

## Global Constraints

- Helper is **stdlib-only** — no third-party imports, no `pip install`.
- Helper **never raises to the shell**: any failure prints `{"available": false}` and exits `0`.
- Degradation chain: `gh api` → unauthenticated `urllib` HTTP → `{"available": false}` (caller falls back to git-only).
- No new test framework — bash tests sourced by `tests/run-all.sh`, using its `assert_*` helpers; tests require **no network** (dry-run + fixtures only).
- Badges are **self-updating** shields.io URLs (need only `owner/repo`); version badge uses `github/v/tag` (tags lead releases in this repo).
- `commands/generate-readme.md` diverges from upstream once edited → must be added to the exclude list in `references/upstream-sync.md`.
- `init-project.md` is **not** edited (it inherits the header via the shared `readme-template.md`).

---

### Task 1: `fetch_github_metrics.py` helper + tests

**Files:**
- Create: `plugins/project-init/skills/project-scaffolder/scripts/fetch_github_metrics.py`
- Test: `tests/structure/test-generate-readme-metrics.sh`

**Interfaces:**
- Produces (module-level, importable by the test):
  - `parse_remote(url: str) -> str | None` — `"owner/repo"` for any GitHub remote form, else `None`.
  - `detect_repo(root: str) -> str | None` — runs `git -C root remote get-url origin`, returns `parse_remote(...)`.
  - `fetch(repo: str) -> tuple[dict, bool]` — `(metrics, available)`.
  - `detect_pypi(root) -> str | None`, `detect_ci(root) -> str | None`.
  - `badge_block(m: dict, root: str) -> str` — centered Markdown badge block.
- CLI: `python3 fetch_github_metrics.py [--repo O/R] [--dir PATH] [--dry-run] [--json]`.
  `--dry-run` reads a metrics dict from stdin (no network); `--json` prints metrics; default prints the badge block.

- [ ] **Step 1: Write the failing test**

Create `tests/structure/test-generate-readme-metrics.sh`:

```bash
# tests/structure/test-generate-readme-metrics.sh (sourced by run-all.sh — no shebang, no exit)
# Regression tests for project-init's GitHub-metrics helper used by /generate-readme.

FGM="plugins/project-init/skills/project-scaffolder/scripts/fetch_github_metrics.py"
assert_file_exists "$FGM" "fetch_github_metrics.py exists"

# --- remote parsing: every GitHub URL form -> owner/repo; non-GitHub -> NONE
_fp() { python3 -c "
import sys; sys.path.insert(0,'plugins/project-init/skills/project-scaffolder/scripts')
import fetch_github_metrics as f
print(f.parse_remote('$1') or 'NONE')
" 2>/dev/null; }
assert_eq "o/r"  "$(_fp 'git@github.com:o/r.git')"       "parse SSH scp-style remote"
assert_eq "o/r"  "$(_fp 'https://github.com/o/r')"       "parse HTTPS remote"
assert_eq "o/r"  "$(_fp 'https://github.com/o/r.git')"   "parse HTTPS .git remote"
assert_eq "o/r"  "$(_fp 'ssh://git@github.com/o/r.git')" "parse ssh:// remote"
assert_eq "NONE" "$(_fp 'https://gitlab.com/o/r')"       "non-GitHub remote -> NONE"

# --- dry-run badge emission (no network); empty dir => no pypi/ci badges
_TMP=$(mktemp -d)
_B=$(echo '{"repo":"o/r","license":"MIT","default_branch":"main"}' | python3 "$FGM" --dry-run --dir "$_TMP" 2>/dev/null)
assert_contains "$_B" '<div align="center">' "badge block is centered"
assert_contains "$_B" 'github/stars/o/r'     "badge block has stars"
assert_contains "$_B" 'github/forks/o/r'     "badge block has forks"
assert_grep_no_match "pypi/v" "$_B"          "no PyPI badge without pyproject"

# --- PyPI detection adds version + downloads badges
printf '[project]\nname = "mypkg"\n' > "$_TMP/pyproject.toml"
_BP=$(echo '{"repo":"o/r","license":"MIT","default_branch":"main"}' | python3 "$FGM" --dry-run --dir "$_TMP" 2>/dev/null)
assert_contains "$_BP" 'pypi/v/mypkg'  "PyPI badge when pyproject present"
assert_contains "$_BP" 'pepy/dt/mypkg' "downloads badge when pyproject present"
rm -rf "$_TMP"

# --- graceful fallback: empty/unparseable metrics -> available:false, never errors
_FB=$(echo '{}' | python3 "$FGM" --dry-run 2>/dev/null)
assert_contains "$_FB" '"available": false' "empty metrics -> available:false"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -E "fetch_github_metrics|parse .* remote|badge block"`
Expected: `not ok … fetch_github_metrics.py exists` (file missing) and the dependent assertions fail.

- [ ] **Step 3: Write the helper**

Create `plugins/project-init/skills/project-scaffolder/scripts/fetch_github_metrics.py`:

```python
#!/usr/bin/env python3
"""Fetch live GitHub repo metrics and emit a centered shields.io badge block for README
generation (project-init /generate-readme). Degrades: gh CLI -> unauthenticated HTTP ->
git-only. NEVER raises to the shell — prints {"available": false} and exits 0 on any failure."""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

_REMOTE_RE = re.compile(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


def parse_remote(url):
    m = _REMOTE_RE.search(url or "")
    return f"{m.group('owner')}/{m.group('repo')}" if m else None


def detect_repo(root):
    try:
        r = subprocess.run(["git", "-C", root, "remote", "get-url", "origin"],
                           capture_output=True, text=True, timeout=10)
        return parse_remote(r.stdout.strip()) if r.returncode == 0 else None
    except Exception:
        return None


def _gh_api(path):
    try:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return None


def _http_api(path):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "oh-my-cloud-skills"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch(repo):
    """Return (metrics, available). Try gh, then unauthenticated HTTP."""
    data = _gh_api(f"repos/{repo}") or _http_api(f"repos/{repo}")
    if not data:
        return {}, False
    rel = _gh_api(f"repos/{repo}/releases/latest") or _http_api(f"repos/{repo}/releases/latest") or {}
    return {
        "repo": repo,
        "description": data.get("description"),
        "license": (data.get("license") or {}).get("spdx_id"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "watchers": data.get("subscribers_count"),
        "open_issues": data.get("open_issues_count"),
        "language": data.get("language"),
        "default_branch": data.get("default_branch", "main"),
        "homepage": data.get("homepage"),
        "archived": data.get("archived", False),
        "latest_release": rel.get("tag_name"),
    }, True


def detect_pypi(root):
    py = os.path.join(root, "pyproject.toml")
    if os.path.isfile(py):
        m = re.search(r'(?m)^\s*name\s*=\s*["\']([A-Za-z0-9._-]+)["\']',
                      open(py, encoding="utf-8").read())
        if m:
            return m.group(1)
    cfg = os.path.join(root, "setup.cfg")
    if os.path.isfile(cfg):
        m = re.search(r'(?m)^\s*name\s*=\s*([A-Za-z0-9._-]+)', open(cfg, encoding="utf-8").read())
        if m:
            return m.group(1)
    return None


def detect_ci(root):
    d = os.path.join(root, ".github", "workflows")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith((".yml", ".yaml")):
                return f
    return None


def badge_block(m, root):
    repo = m["repo"]
    branch = m.get("default_branch") or "main"
    b = []
    if m.get("license"):
        b.append(f"[![license](https://img.shields.io/github/license/{repo}?color=yellow)](LICENSE)")
    b.append(f"[![version](https://img.shields.io/github/v/tag/{repo}?label=version&color=green)]"
             f"(https://github.com/{repo}/tags)")
    b.append(f"[![stars](https://img.shields.io/github/stars/{repo}?logo=github)]"
             f"(https://github.com/{repo}/stargazers)")
    b.append(f"[![forks](https://img.shields.io/github/forks/{repo}?logo=github)]"
             f"(https://github.com/{repo}/network/members)")
    pkg = detect_pypi(root)
    if pkg:
        b.append(f"[![PyPI](https://img.shields.io/pypi/v/{pkg}?logo=pypi)](https://pypi.org/project/{pkg}/)")
        b.append(f"[![downloads](https://img.shields.io/pepy/dt/{pkg})](https://pepy.tech/project/{pkg})")
    ci = detect_ci(root)
    if ci:
        b.append(f"[![CI](https://img.shields.io/github/actions/workflow/status/{repo}/{ci}"
                 f"?branch={branch}&label=CI&logo=github)]"
                 f"(https://github.com/{repo}/actions/workflows/{ci})")
    return '<div align="center">\n\n' + "\n".join(b) + '\n\n</div>'


def main():
    ap = argparse.ArgumentParser(description="Live GitHub metrics + badge block for README generation.")
    ap.add_argument("--repo", help="owner/repo (else auto-detect from git remote)")
    ap.add_argument("--dir", default=".", help="repo root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true", help="read metrics JSON from stdin; no network")
    ap.add_argument("--json", action="store_true", help="print metrics JSON instead of the badge block")
    a = ap.parse_args()
    try:
        if a.dry_run:
            m = json.load(sys.stdin)
            available = bool(m.get("repo"))
        else:
            repo = a.repo or detect_repo(a.dir)
            if not repo:
                print(json.dumps({"available": False, "reason": "no GitHub remote"}))
                return 0
            m, available = fetch(repo)
            m["available"] = available
        if not available:
            print(json.dumps({"available": False}))
            return 0
        print(json.dumps(m, indent=2) if a.json else badge_block(m, a.dir))
        return 0
    except Exception as e:                       # never wedge README generation
        sys.stderr.write(f"[fetch_github_metrics] {e!r}\n")
        print(json.dumps({"available": False}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `bash tests/run-all.sh 2>&1 | grep -E "fetch_github_metrics|parse .* remote|badge block|PyPI|available:false"`
Expected: all the new assertions print `ok`. Then run the full suite and confirm no new failures:
`bash tests/run-all.sh 2>&1 | tail -1` (the pre-existing 14 environmental failures may remain; total ok count rises).

- [ ] **Step 5: Commit**

```bash
git add plugins/project-init/skills/project-scaffolder/scripts/fetch_github_metrics.py tests/structure/test-generate-readme-metrics.sh
git commit -m "feat(project-init): GitHub-metrics helper for /generate-readme (live badge block)"
```

---

### Task 2: Wire `/generate-readme` + docs + upstream-sync exclude

**Files:**
- Modify: `plugins/project-init/commands/generate-readme.md` (frontmatter `allowed-tools`; new Step 2.5; Step 7 checklist)
- Modify: `plugins/project-init/skills/project-scaffolder/references/readme-template.md` (badge block + selection rules)
- Modify: `plugins/project-init/references/upstream-sync.md` (exclude `commands/generate-readme.md`)
- Test: `tests/structure/test-generate-readme-metrics.sh` (append wiring assertions)

**Interfaces:**
- Consumes: `fetch_github_metrics.py` (Task 1) — `python3 .../fetch_github_metrics.py` prints a badge block or `{"available": false}`.

- [ ] **Step 1: Append wiring assertions to the test (write the failing test)**

Append to `tests/structure/test-generate-readme-metrics.sh`:

```bash
# --- /generate-readme is wired to the helper and permitted to run it
GR="plugins/project-init/commands/generate-readme.md"
assert_grep_match "fetch_github_metrics\\.py" "$(cat "$GR")"     "generate-readme references the metrics helper"
assert_grep_match "Bash\\(gh:\\*\\)"          "$(cat "$GR")"     "generate-readme allows gh"
assert_grep_match "Bash\\(python3:\\*\\)"     "$(cat "$GR")"     "generate-readme allows python3"
# --- the upstream-sync exclude list protects the diverged command
US="plugins/project-init/references/upstream-sync.md"
assert_grep_match "commands/generate-readme\\.md" "$(cat "$US")" "upstream-sync excludes generate-readme.md"
```

- [ ] **Step 2: Run to verify it fails**

Run: `bash tests/run-all.sh 2>&1 | grep -E "references the metrics helper|allows gh|allows python3|upstream-sync excludes"`
Expected: these four assertions print `not ok` (not yet wired).

- [ ] **Step 3: Edit `generate-readme.md` — allowed-tools**

In `plugins/project-init/commands/generate-readme.md` frontmatter, replace the `allowed-tools` line:

```yaml
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(find:*), Bash(git log:*), Bash(git remote:*), Bash(git describe:*), Bash(git tag:*), Bash(gh:*), Bash(python3:*), Glob, Grep
```

- [ ] **Step 4: Edit `generate-readme.md` — add Step 2.5**

Insert after Step 2 (before "## Step 3"):

````markdown
## Step 2.5: Fetch Live GitHub Metrics

Fetch live repository metrics and a ready-to-paste centered badge block. The helper degrades
gracefully (gh → unauthenticated HTTP → git-only) and never fails the command:

```bash
python3 skills/project-scaffolder/scripts/fetch_github_metrics.py
```

- If it prints a `<div align="center">…</div>` badge block, use it verbatim as the badge row in
  the top layout (Step 6), and read fields with `--json` to fill the Overview description/license
  when not already known.
- If it prints `{"available": false}` (no GitHub remote / offline / private with no `gh` auth),
  continue with the git-only detection from Step 2 and note "metrics unavailable" in the Step 8
  summary. Badges still render from `git remote` data and self-update once the repo is on GitHub.
````

- [ ] **Step 5: Edit `generate-readme.md` — Step 7 checklist**

Add to the Step 7 validation checklist:

```markdown
- [ ] Badge row is wrapped in `<div align="center">` and includes the live badges from Step 2.5 (or git-only badges if metrics were unavailable)
```

- [ ] **Step 6: Document the badge block in `readme-template.md`**

Add a section to `plugins/project-init/skills/project-scaffolder/references/readme-template.md`:

````markdown
## Badge header (centered, self-updating)

Wrap the badge block in `<div align="center">`. Always include license, version
(`github/v/tag`), stars, and forks. Add a CI badge when a `.github/workflows/*.yml` exists, and
PyPI version + downloads badges only when a PyPI package is detected (`pyproject.toml`/`setup.cfg`).
Skip any badge whose data is unavailable rather than rendering a broken one. Place the EN/KO
language toggle on its own line above the metric row. All badges are shields.io and self-updating
(they need only `owner/repo`).

```markdown
<div align="center">

<lang-toggle line>

[![license](https://img.shields.io/github/license/OWNER/REPO?color=yellow)](LICENSE)
[![version](https://img.shields.io/github/v/tag/OWNER/REPO?label=version&color=green)](https://github.com/OWNER/REPO/tags)
[![stars](https://img.shields.io/github/stars/OWNER/REPO?logo=github)](https://github.com/OWNER/REPO/stargazers)
[![forks](https://img.shields.io/github/forks/OWNER/REPO?logo=github)](https://github.com/OWNER/REPO/network/members)

</div>
```
````

- [ ] **Step 7: Add `generate-readme.md` to the upstream-sync exclude list**

In `plugins/project-init/references/upstream-sync.md`:
1. Add `--exclude='commands/generate-readme.md'` to the `rsync` snippet.
2. Add `--exclude=generate-readme.md` to the `diff -rq` snippet.
3. Add a bullet under "Locally-diverged files (excluded from sync):":
   `- `commands/generate-readme.md` — adds a local-only GitHub-metrics fetch step (Step 2.5) + `Bash(gh:*)`/`Bash(python3:*)`. Excluded because it's a live-badge feature that doesn't exist upstream.`

- [ ] **Step 8: Run the full suite to verify everything passes**

Run: `python3 scripts/test-plugins.py && python3 scripts/test-codex-plugins.py && bash tests/run-all.sh 2>&1 | grep -E "references the metrics helper|allows gh|allows python3|upstream-sync excludes"`
Expected: validators PASS; the four wiring assertions print `ok`. Confirm no new failures vs. the pre-existing 14: `bash tests/run-all.sh 2>&1 | tail -1`.

- [ ] **Step 9: Commit**

```bash
git add plugins/project-init/commands/generate-readme.md plugins/project-init/skills/project-scaffolder/references/readme-template.md plugins/project-init/references/upstream-sync.md tests/structure/test-generate-readme-metrics.sh
git commit -m "feat(project-init): wire /generate-readme to live GitHub metrics + exclude from upstream sync"
```

---

## Self-Review

**Spec coverage:** Helper (Component 1) → Task 1. Badge block + selection rules (Component 2) → `badge_block()` in Task 1 + `readme-template.md` in Task 2 Step 6. Command edit (Component 3) → Task 2 Steps 3–5. Template doc (Component 4) → Task 2 Step 6. Upstream-sync (Component 5) → Task 2 Step 7. `/init-project` reconciliation → satisfied by editing only the shared template, not `init-project.md` (Global Constraints). Testing section → Task 1 test + Task 2 wiring assertions, all no-network. Degradation matrix → `fetch()`/`main()` fallback chain + Step 2.5 "available:false" branch.

**Placeholder scan:** No TBD/TODO. `OWNER/REPO`/`<lang-toggle line>` in the template doc are intentional template tokens, not plan placeholders. All code steps show complete code.

**Type consistency:** `parse_remote`/`detect_repo`/`fetch`/`detect_pypi`/`detect_ci`/`badge_block` names match between the helper, the tests, and the Interfaces blocks. `--dry-run`/`--json`/`--dir`/`--repo` flags match between helper `argparse` and the tests.

**Deviation from spec (noted):** the helper uses stdlib `urllib` for the unauthenticated fallback instead of shelling to `curl` — cleaner, no `curl` dependency, so `generate-readme.md` allowed-tools needs only `Bash(gh:*)` + `Bash(python3:*)` (not `Bash(curl:*)`).
