#!/usr/bin/env python3
"""Codex entry point: local diagnostics and complete, tool-free Kiro reviews."""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import kiro_config
import kiro_review
import kiro_setup


def emit(status, **fields):
    print(json.dumps({"status": status, **fields}, ensure_ascii=False))
    return {"PASS": 0, "READY": 0, "NO_CHANGES": 0, "FAIL": 2}.get(status, 1)


def doctor(root, probe):
    config = kiro_config.effective(str(root))
    binary = shutil.which("kiro-cli")
    version = None
    if binary:
        result = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode:
            return emit("ERROR", error="kiro-cli --version failed", cli=binary)
        version = result.stdout.strip()
    report = {
        "root": str(root),
        "plugin_root": str(Path(__file__).resolve().parents[3]),
        "cli": binary,
        "version": version,
        "config_path": kiro_config.local_path(str(root)),
        "review": {key: config.get("review", {}).get(key)
                   for key in ("model", "effort", "timeout", "block", "on_commit", "on_push", "push_block")},
        "delegate": {key: config.get("delegate", {}).get(key)
                     for key in ("model", "effort", "timeout", "parallel_tasks", "max_fix_rounds")},
        "authentication": "NOT_PROBED",
        "review_requires_project_agent": False,
    }
    if not binary:
        return emit("ABSENT", **report, error="Install Kiro CLI, then rerun setup.")
    if probe:
        review = config.get("review") or {}
        status, reason = kiro_setup.probe(
            model=review.get("model"), effort=kiro_config._effort(review.get("effort")))
        report["authentication"] = status
        if status != "READY":
            return emit(status, **report, error=reason)
    return emit("READY", **report)


def review(args, root):
    config = kiro_config.effective(str(root)).get("review") or {}
    timeout = config.get("timeout", 120)
    if type(timeout) is not int or timeout <= 0:
        return emit("ERROR", error="review.timeout must be a positive integer")
    block_key = "push_block" if args.range else "block"
    block = config.get(block_key, "warning" if args.range else "critical")
    if not isinstance(block, str) or block not in kiro_review.BLOCK_FLOOR:
        return emit("ERROR", error=f"review.{block_key} must be critical, warning or none")
    if args.paths and (args.range or args.diff is not None):
        return emit("ERROR", error="paths cannot be combined with --range or --diff")
    if args.diff is not None:
        if args.diff == "-":
            diff = sys.stdin.read()
        else:
            path = Path(args.diff).resolve()
            if not path.is_relative_to(root):
                return emit("ERROR", error="--diff must be inside --root; use stdin for prepared input")
            diff = path.read_text(encoding="utf-8")
        error = None
    elif args.range:
        revision, error = kiro_review._resolve_push_range(str(root))
        if error:
            return emit("ERROR", error=error)
        diff, error = kiro_review._range_diff(str(root), revision)
    else:
        paths = args.paths or (["."] if args.working_tree else [])
        diff, error = kiro_review._git_diff(
            str(root), paths, cached=args.staged or not paths, strict=True)
    if error:
        return emit("ERROR", error=error)
    if not diff.strip():
        return emit("NO_CHANGES", findings=[], coverage="empty")
    if len(diff.encode("utf-8")) > kiro_review._DIFF_CAP:
        return emit("ERROR", error=f"Input exceeds {kiro_review._DIFF_CAP} bytes; split the review scope.",
                    coverage="none")
    lenses = args.lenses.split(",") if args.lenses else None
    if lenses and (len(set(lenses)) != len(lenses)
                   or any(lens not in kiro_review._LENSES for lens in lenses)):
        return emit("ERROR", error="Use distinct lenses: correctness,security,scope")
    parameters = {
        "model": config.get("model"),
        "effort": kiro_config._effort(config.get("effort")),
        "timeout": timeout,
        "progress": args.progress,
        "no_tools": True,
    }
    if lenses:
        findings, errors, truncated = kiro_review.run_review_lenses(
            str(root), diff, lenses=lenses, **parameters)
    else:
        findings, error, truncated = kiro_review.run_review(str(root), diff, **parameters)
        errors = {"review": error} if error else {}
    if errors or truncated:
        return emit("ERROR", errors=errors, truncated=truncated,
                    findings=findings or [], coverage="incomplete")
    floor = kiro_review.BLOCK_FLOOR[block]
    blocking = any(kiro_review.SEVERITY_ORDER[finding["severity"]] >= floor
                   for finding in findings)
    return emit("FAIL" if blocking else "PASS", findings=findings, coverage="complete",
                model=parameters["model"], effort=parameters["effort"],
                lenses=lenses or ["review"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    diagnostics = commands.add_parser("doctor", help="Inspect local readiness; inference is opt-in")
    diagnostics.add_argument("--root", type=Path)
    diagnostics.add_argument("--probe", action="store_true")
    reviewer = commands.add_parser("review", help="Review without granting Kiro tool access")
    reviewer.add_argument("--root", type=Path)
    modes = reviewer.add_mutually_exclusive_group()
    modes.add_argument("--staged", action="store_true")
    modes.add_argument("--working-tree", action="store_true")
    modes.add_argument("--range", action="store_true")
    modes.add_argument("--diff", help="Prepared input inside --root, or '-' for stdin")
    reviewer.add_argument("--lenses")
    reviewer.add_argument("--progress", action="store_true")
    reviewer.add_argument("paths", nargs="*")
    args = parser.parse_args(argv)
    root = (args.root or Path(kiro_review._default_root())).resolve()
    try:
        if args.command == "doctor":
            return doctor(root, args.probe)
        return review(args, root)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return emit("ERROR", error=str(error))


if __name__ == "__main__":
    sys.exit(main())
