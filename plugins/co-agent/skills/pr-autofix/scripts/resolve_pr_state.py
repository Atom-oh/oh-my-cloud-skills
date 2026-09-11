#!/usr/bin/env python3
"""Resolve PR/state precedence without writes; reuse the canonical jq schema."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

TAIL = Path(".claude/co-agent-consensus/pr-autofix")


class StateError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise StateError(message)


def number(value):
    require(type(value) is int and 0 < value <= 9007199254740991,
            "state PR must be a positive safe integer.")
    return value


def plain_path(path, root):
    path = path.absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            parent, target = part.parent.resolve(), part.resolve()
            # Workspace/OS ancestors may be aliases; paths within the repository
            # or aliases directly into its state tail may not redirect state access.
            require(parent != root and root not in parent.parents and root not in target.parents,
                    "state path inside the repository must not contain symlinks.")
    return path.resolve()


def read_state(path):
    require(path.is_file() and path.stat().st_size > 0,
            "supplied/existing state is missing, empty or not a regular file; do not reset it.")
    contents = path.read_bytes()
    data = json.loads(contents)
    require(isinstance(data, dict), "state must contain one JSON object.")
    result = subprocess.run(
        ["jq", "-L", str(Path(__file__).resolve().parent), "-se",
         'include "review_state"; length == 1 and (.[0] | valid_state)'],
        input=contents, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=10,
    )
    require(result.returncode == 0, "invalid state; preserve its bytes and repair from evidence.")
    return number(data.get("pr"))


def resolve(root, pr=None, state=None):
    root = Path(root).resolve()
    require(root.is_dir(), "repository root is unavailable.")
    selected = None
    if pr not in (None, ""):
        require(re.fullmatch(r"[1-9][0-9]{0,15}", pr) is not None,
                "explicit PR_NUMBER must be a positive safe integer.")
        selected = number(int(pr))
    supplied = None
    if state is not None:
        require(bool(state), "supplied STATE is empty; do not fall back to branch discovery.")
        supplied = plain_path(Path(state), root)
        try:
            relative = supplied.relative_to(root / TAIL)
        except ValueError:
            raise StateError("STATE must be this repository's canonical pr-N/state.json; foreign state is not adopted.")
        require(len(relative.parts) == 2 and relative.name == "state.json" and
                re.fullmatch(r"pr-([1-9][0-9]{0,15})", relative.parts[0]) is not None,
                "STATE must use the canonical pr-N/state.json layout.")
        saved = number(int(relative.parts[0][3:]))
        require(selected is None or selected == saved,
                "explicit PR_NUMBER differs from the canonical state path; preserve state and select the intended PR.")
        require(read_state(supplied) == saved,
                "state .pr differs from its canonical pr-N directory; preserve it and repair explicitly.")
        selected = saved
    if selected is None:
        return {"pr": None, "state": None}
    canonical = plain_path(root / TAIL / f"pr-{selected}" / "state.json", root)
    require(supplied is None or supplied == canonical,
            "STATE must be this repository's canonical pr-N/state.json; foreign state is not adopted.")
    if supplied is None and canonical.exists():
        require(read_state(canonical) == selected,
                "existing canonical state belongs to a different PR; do not reset it.")
    return {"pr": selected, "state": str(canonical)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--pr")
    parser.add_argument("--state")
    args = parser.parse_args()
    try:
        result = resolve(args.root, args.pr, args.state)
    except StateError as error:
        print("PR state: " + str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print("PR state: unreadable/invalid state or unavailable jq; preserve state without resetting.",
              file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
