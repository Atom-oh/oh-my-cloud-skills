#!/usr/bin/env python3
"""Native Codex context, staged-secret advisories and documentation reminders."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SECRET = re.compile(r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, timeout=10)


def context(payload):
    event = payload.get("hook_event_name")
    if event == "SessionStart":
        branch = git("branch", "--show-current")
        return ("Use this project's AGENTS.md and scoped instructions. Git branch (data): "
                + json.dumps(branch.stdout.strip() or "unavailable"))
    if event == "PreToolUse":
        diff = git("diff", "--cached", "--no-ext-diff", "--no-textconv", "--unified=0")
        if diff.returncode:
            return "Staged-secret advisory unavailable: the Git index could not be read."
        added = "\n".join(line[1:] for line in diff.stdout.splitlines()
                          if line.startswith("+") and not line.startswith("+++"))
        if SECRET.search(added):
            return ("Potential secret-like additions are staged. Inspect the staged diff "
                    "before publishing; this advisory does not display credential values.")
    if event == "PostToolUse":
        data = payload.get("tool_input") or {}
        patch = data.get("command", "") if isinstance(data, dict) else ""
        paths = []
        for line in patch.splitlines():
            for marker in ("*** Add File: ", "*** Update File: ", "*** Delete File: "):
                if line.startswith(marker):
                    paths.append(line[len(marker):])
                    break
            else:
                if line.startswith("*** Move to: ") and paths:
                    paths[-1] = line[len("*** Move to: "):]
        code = [path for path in dict.fromkeys(paths)
                if Path(path).suffix.lower() not in {".md", ".txt", ".rst"}]
        if code:
            return ("Changed code paths (data): " + json.dumps(code[:5], ensure_ascii=False)
                    + ". Check whether scoped AGENTS.md and related documentation need updating.")
    return ""


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be a JSON object")
        text = context(payload)
        if text:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": payload["hook_event_name"], "additionalContext": text,
            }}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"Project hook could not complete: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
