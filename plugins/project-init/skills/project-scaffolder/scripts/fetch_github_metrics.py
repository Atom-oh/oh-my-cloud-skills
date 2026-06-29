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

_REMOTE_RE = re.compile(
    r"(?:^|@|//)github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


def parse_remote(url):
    # Normalize: drop a trailing slash, then a trailing .git, so
    # "…/o/r.git/" -> "o/r" (not "o/r.git").
    s = (url or "").strip()
    if s.endswith("/"):
        s = s[:-1]
    if s.endswith(".git"):
        s = s[:-4]
    m = _REMOTE_RE.search(s)
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
