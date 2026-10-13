#!/usr/bin/env python3
"""Cheap poll signal: has anything worth a full review-evidence pull happened?

Compares HEAD, human review decision, merge state and required-check states
against the last snapshot recorded in state.json. Read-only — prints a JSON
verdict; the caller (review-state.md) persists the returned snapshot.
"""
import argparse
import json
import subprocess
import sys


def run_gh(args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout, result.stderr


def required_checks(pr, repo):
    rc, out, err = run_gh(
        ["pr", "checks", pr, "--repo", repo, "--required", "--json", "name,bucket,state"])
    if rc == 0:
        return json.loads(out)
    # gh's documented shape for "no required checks configured" — not a failure.
    if rc == 1 and not out.strip() and "no required checks reported on" in err:
        return []
    raise RuntimeError(f"gh pr checks failed: {err.strip()}")


def snapshot(pr, repo):
    rc, out, err = run_gh(
        ["pr", "view", pr, "--repo", repo, "--json", "headRefOid,reviewDecision,mergeStateStatus"])
    if rc != 0:
        raise RuntimeError(f"gh pr view failed: {err.strip()}")
    view = json.loads(out)
    checks = sorted(required_checks(pr, repo), key=lambda c: c.get("name", ""))
    return {
        "head": view.get("headRefOid"),
        "review_decision": view.get("reviewDecision"),
        "merge_state_status": view.get("mergeStateStatus"),
        "checks": [[c.get("name"), c.get("bucket"), c.get("state")] for c in checks],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--previous", help="Prior snapshot as a JSON string, or omitted/empty for none.")
    args = parser.parse_args()
    try:
        current = snapshot(args.pr, args.repo)
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        print(f"poll probe: {error}", file=sys.stderr)
        return 1
    previous = None
    if args.previous:
        try:
            previous = json.loads(args.previous)
        except json.JSONDecodeError:
            previous = None  # treat an unparsable prior snapshot as "no snapshot yet"
    print(json.dumps({"changed": previous != current, "snapshot": current}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
