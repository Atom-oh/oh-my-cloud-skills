#!/usr/bin/env python3
"""Run a bundled helper without changing the consumer repository's cwd."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    adapter = Path(__file__).resolve().parent
    root = adapter.parent
    if len(sys.argv) < 2:
        print("usage: run.py <plugin-relative helper.py|helper.sh> [arguments...]", file=sys.stderr)
        return 2
    relative = Path(sys.argv[1])
    script = (root / relative).resolve()
    if relative.is_absolute() or root not in script.parents or not script.is_file():
        print("helper must be a file inside the installed plugin", file=sys.stderr)
        return 2
    interpreters = {".py": [sys.executable], ".sh": ["bash"]}
    if script.suffix not in interpreters:
        print("helper must be a Python or Bash script", file=sys.stderr)
        return 2
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(root), PLUGIN_ROOT=str(root))
    inventory = json.loads((adapter / "inventory.json").read_text(encoding="utf-8"))
    if inventory["plugin"] == "co-agent":
        env["CO_AGENT_HOST"] = "codex"
    result = subprocess.run(
        [*interpreters[script.suffix], str(script), *sys.argv[2:]], env=env,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
