#!/usr/bin/env python3
"""Parse a writing-plans implementation plan (.md) into structured tasks.

A plan has `### Task N: <title>` sections, each with a `**Files:**` block listing
`Create:`/`Modify:`/`Test:` paths and one or more `- [ ]` checkbox steps. This extracts
that structure so the consensus pipeline knows the task list and the ALLOWED FILE SET
(used for scope-lock in Stage B) without re-reading prose.

NOTE: file paths MUST be backtick-wrapped — `- Create: ` + backtick + path + backtick.
Bare paths (no backticks) are silently ignored, which yields an EMPTY allowed-file set
and makes scope_guard reject every edit. Plan generators must emit backticks.

Usage:
  parse_plan.py <plan.md>            # JSON: [{n,title,files:[...],steps:N}]
  parse_plan.py <plan.md> --files    # unique declared file paths, one per line
  parse_plan.py <plan.md> --count    # number of tasks
Exit 0 ok / 2 usage/read error.
"""
import sys
import re
import json

TASK_RE = re.compile(r"^#{2,3}\s+Task\s+(\d+)\s*:\s*(.+?)\s*$", re.M)
FILE_RE = re.compile(r"^\s*-\s*(?:Create|Modify|Test)\s*:\s*`([^`]+)`", re.M)
STEP_RE = re.compile(r"^\s*-\s*\[\s?\]", re.M)


def parse(text):
    tasks = []
    matches = list(TASK_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        files = []
        for fm in FILE_RE.finditer(body):
            # a Files entry may carry a line range like path:123-145 — keep just the path
            files.append(fm.group(1).split(":")[0].strip())
        tasks.append({
            "n": int(m.group(1)),
            "title": m.group(2).strip(),
            "files": list(dict.fromkeys(files)),
            "steps": len(STEP_RE.findall(body)),
        })
    return tasks


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    try:
        with open(args[0], encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"❌ cannot read {args[0]}: {e}", file=sys.stderr)
        return 2
    tasks = parse(text)
    if "--count" in sys.argv[1:]:
        print(len(tasks))
    elif "--files" in sys.argv[1:]:
        seen = []
        for t in tasks:
            for f in t["files"]:
                if f not in seen:
                    seen.append(f)
        print("\n".join(seen))
    else:
        print(json.dumps(tasks, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
