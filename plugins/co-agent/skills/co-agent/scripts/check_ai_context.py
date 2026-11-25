#!/usr/bin/env python3
"""Validate / check staleness of co-agent-generated AGENTS.md context.

co-agent keeps one lean, shared AGENTS.md for supported peers (the reviewed format from
sync-context, or the legacy format distilled from CLAUDE.md):
  - AGENTS.md  → Codex CLI auto-loads it from the repo root (32 KiB project-doc cap;
                 merged git-root→cwd). Kiro's .kiro/steering/project-context.md
                 bridges to this SAME file via #[[file:AGENTS.md]] (not CLAUDE.md
                 directly — see ai-cli-adapters.md for the consistency rationale).

The current host (the co-agent skill) writes AGENTS.md; this script does the mechanical checks:
staleness vs CLAUDE.md, size caps, the generated marker, and a secret scan. It is
NOT the distiller — distillation is performed by the host.

Usage:
  python3 check_ai_context.py [project_dir]          # check (exit 1 if stale/oversized/missing)
  python3 check_ai_context.py [project_dir] --emit-marker   # print the marker line to embed when generating
  python3 check_ai_context.py [project_dir] --verify <file> # exit 0 ONLY if <file> is co-agent-generated,
                                                              # fresh vs CLAUDE.md, within cap, and secret-free —
                                                              # silent (no stdout), for scripted gates like the
                                                              # peer context handoff (unlike the default mode, a
                                                              # MISSING or hand-written file is a fail here, not
                                                              # a note: "safe to hand to a third-party AI" must
                                                              # be a strict yes/no, not "nothing to report")
  python3 check_ai_context.py [project_dir] --check-candidate <file>
      # exit 0 ONLY if <file> exists, starts with REVIEWED_MARKER and passes
      # reviewed_problems() (line/byte caps, secrets); prints each problem

Reviewed format (sync-context output): line 1 is exactly REVIEWED_MARKER; no CLAUDE.md
sha applies. --verify AGENTS.md checks it silently; default mode needs no CLAUDE.md for it
and still runs the RESIDUAL_SCAN secret audit.

Legacy generated marker (must be on/near line 1 of a sha-bearing file):
  <!-- generated-by: co-agent · source: CLAUDE.md · claude-md-sha: <sha12> · generated-at: <date> -->
"""
import sys
import os
import re
import hashlib
import datetime

MANAGED = {"AGENTS.md": 32 * 1024}  # filename → soft size cap (bytes)
# Unmanaged context files may still be read by active or separately run external tools.
# Unmanaged context is not exempt from secret scanning.
RESIDUAL_SCAN = ("GEMINI.md",)
MARKER_RE = re.compile(r"generated-by:\s*co-agent")
SHA_RE = re.compile(r"claude-md-sha:\s*([0-9a-f]{12})")
SECRET_RE = re.compile(r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{30,}|(?:password|secret|api[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}", re.I)


REVIEWED_MARKER = "<!-- generated-by: co-agent · source: reviewed AGENTS.md -->"


def reviewed_problems(body):
    problems = []
    if len(body.splitlines()) > 200:
        problems.append("AGENTS.md exceeds the 200-line cap")
    if len(body.encode("utf-8")) > 10 * 1024:
        problems.append("AGENTS.md exceeds the 10 KiB cap")
    if SECRET_RE.search(body):
        problems.append("possible secret/credential in reviewed context")
    return problems


def is_reviewed(body):
    return body.splitlines()[:1] == [REVIEWED_MARKER]


def claude_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _file_problems(path, sha, cap=None):
    """Marker + freshness + (optional) size cap + secret checks for one generated file.
    Missing file or no marker both count as problems here — the caller decides whether
    that's a soft note (default report) or a hard fail (--verify)."""
    if not os.path.isfile(path):
        return ["missing"]
    with open(path, encoding="utf-8") as f:
        body = f.read()
    if is_reviewed(body):
        # Reviewed format: no CLAUDE.md sha to compare. Apply the reviewed line, byte and
        # secret checks plus the caller's own cap (AGENTS_CAP in scripts/pr-review/context.py).
        problems = reviewed_problems(body)
        size = len(body.encode("utf-8"))
        if cap is not None and size > cap:
            problems.append(f"{size} B > {cap} B cap; shorten the reviewed AGENTS.md")
        return problems
    if not MARKER_RE.search(body):
        return ["hand-written (no co-agent marker)"]
    problems = []
    if cap is not None:
        size = len(body.encode("utf-8"))
        if size > cap:
            problems.append(f"{size} B > {cap} B cap — distill further (CLI will truncate)")
    m = SHA_RE.search(body)
    if not m:
        problems.append("missing claude-md-sha in marker — regenerate")
    elif m.group(1) != sha:
        problems.append("STALE — CLAUDE.md changed since generation (run /co-agent sync-context)")
    if SECRET_RE.search(body):
        problems.append("possible secret/credential in generated context — remove before sharing with external AIs")
    return problems


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = args[0] if args else "."
    emit = "--emit-marker" in sys.argv[1:]
    verify_idx = sys.argv.index("--verify") + 1 if "--verify" in sys.argv else None
    verify_target = sys.argv[verify_idx] if verify_idx and verify_idx < len(sys.argv) else None

    if "--check-candidate" in sys.argv:
        index = sys.argv.index("--check-candidate") + 1
        if index >= len(sys.argv):
            print("--check-candidate requires a candidate file path")
            return 2
        candidate = sys.argv[index]
        if not os.path.isfile(candidate):
            print(f"Candidate file not found: {candidate}")
            return 1
        with open(candidate, encoding="utf-8") as f:
            body = f.read()
        if not is_reviewed(body):
            print("Candidate is missing the reviewed AGENTS.md marker")
            return 1
        problems = reviewed_problems(body)
        for problem in problems:
            print(problem)
        return int(bool(problems))

    # A reviewed AGENTS.md carries no CLAUDE.md sha. --verify checks only its reviewed caps
    # (silently); default mode skips the CLAUDE.md requirement but still runs the
    # RESIDUAL_SCAN audit and note output below (ADR-022).
    reviewed_body = None
    agents_path = os.path.join(root, "AGENTS.md")
    if not emit and verify_target in (None, "AGENTS.md") and os.path.isfile(agents_path):
        with open(agents_path, encoding="utf-8") as f:
            body = f.read()
        if is_reviewed(body):
            reviewed_body = body
    if reviewed_body is not None and verify_target:
        return int(bool(reviewed_problems(reviewed_body)))

    claude_path = os.path.join(root, "CLAUDE.md")
    if reviewed_body is None and not os.path.isfile(claude_path):
        if verify_target:
            return 1   # no CLAUDE.md → nothing was distilled → not safe to hand out
        print(f"❌ no CLAUDE.md in {root} — nothing to sync from.")
        return 2
    sha = None   # unused for a reviewed AGENTS.md, which may have no CLAUDE.md
    if os.path.isfile(claude_path):
        with open(claude_path, encoding="utf-8") as f:
            sha = claude_sha(f.read())

    if emit:
        today = datetime.date.today().isoformat()
        print(f"<!-- generated-by: co-agent · source: CLAUDE.md · claude-md-sha: {sha} · "
              f"generated-at: {today} · DO NOT EDIT — edit CLAUDE.md then run /co-agent sync-context -->")
        return 0

    if verify_target:
        cap = MANAGED.get(verify_target)
        return 1 if _file_problems(os.path.join(root, verify_target), sha, cap) else 0

    problems, notes = [], []
    for name, cap in MANAGED.items():
        if name == "AGENTS.md" and reviewed_body is not None:
            problems.extend(reviewed_problems(reviewed_body))
            continue
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            notes.append(f"{name}: not generated yet (run /co-agent sync-context)")
            continue
        with open(p, encoding="utf-8") as f:
            body = f.read()
        if not MARKER_RE.search(body):
            notes.append(f"{name}: hand-written (no co-agent marker) — leaving it alone")
            continue
        size = len(body.encode("utf-8"))
        if size > cap:
            problems.append(f"{name}: {size} B > {cap} B cap — distill further (CLI will truncate)")
        m = SHA_RE.search(body)
        if not m:
            problems.append(f"{name}: missing claude-md-sha in marker — regenerate")
        elif m.group(1) != sha:
            problems.append(f"{name}: STALE — CLAUDE.md changed since generation (run /co-agent sync-context)")
        if SECRET_RE.search(body):
            problems.append(f"{name}: possible secret/credential in generated context — remove before sharing with external AIs")

    # RESIDUAL_SCAN (unlike MANAGED) is secret-scanned only, never marker/staleness-checked:
    # co-agent never generated these files, so there's no CLAUDE.md-sha to compare against —
    # the only actionable risk on a residual file is a stale secret a third-party AI could load.
    for name in RESIDUAL_SCAN:
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        with open(p, encoding="utf-8") as f:
            body = f.read()
        if SECRET_RE.search(body):
            problems.append(f"{name}: residual unmanaged file with a possible secret — "
                            "remove the sensitive content before sharing it. Active or "
                            "separately run external tools may still load this file.")
        else:
            notes.append(f"{name}: residual unmanaged file present (not generated) — consider deleting")

    for n in notes:
        print(f"   • {n}")
    if problems:
        print(f"❌ AI context files need attention ({len(problems)}):")
        for p in problems:
            print(f"   • {p}")
        return 1
    if reviewed_body is not None:
        print("Reviewed AGENTS.md is within its line and byte caps, no secrets.")
        return 0
    print("✅ AGENTS.md is in sync with CLAUDE.md, within size cap, no secrets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
