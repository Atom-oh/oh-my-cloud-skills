#!/usr/bin/env python3
"""Build bounded reviewer context from a verified, trusted-base checkout."""
import argparse
import json
from pathlib import Path
import re
import runpy

SOURCE_ROOT = Path(__file__).resolve().parents[2]
CHECKER = runpy.run_path(str(
    SOURCE_ROOT / "plugins/co-agent/skills/co-agent/scripts/check_ai_context.py"
))
AGENTS_CAP = 6144
CONTEXT_CAP = 8192
NON_PROCEDURES = {"README.md", "CLAUDE.md", "AGENTS.md"}


def inside(root, path):
    if root not in path.resolve().parents:
        raise ValueError("Review context path escapes the base checkout")
    return path


def read_json(root, path):
    return json.loads(inside(root, path).read_text(encoding="utf-8"))


def build_context(root):
    root = root.resolve()
    claude = inside(root, root / "CLAUDE.md").read_text(encoding="utf-8")
    agents = inside(root, root / "AGENTS.md")
    problems = CHECKER["_file_problems"](str(agents), CHECKER["claude_sha"](claude), AGENTS_CAP)
    if problems:
        raise ValueError("Base AGENTS.md cannot be forwarded: " + "; ".join(problems))
    facts = {"plugins": {}, "source_procedures": 0, "codex_entries": 0}
    for manifest in sorted(root.glob("plugins/*/.claude-plugin/plugin.json")):
        package = manifest.parents[1]
        inside(root, package)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", package.name):
            raise ValueError("Invalid base plugin directory name")
        read_json(root, manifest)
        inventory = read_json(root, package / ".codex-plugin/inventory.json")
        entries = inventory.get("skills") if isinstance(inventory, dict) else None
        if (not isinstance(inventory, dict) or inventory.get("plugin") != package.name
                or not isinstance(entries, list)):
            raise ValueError("Invalid base Codex inventory")
        counts = {
            kind: sum(path.is_file() and path.name not in NON_PROCEDURES
                      for path in package.glob(pattern))
            for kind, pattern in (
                ("skills", "skills/*/SKILL.md"),
                ("commands", "commands/*.md"),
                ("agents", "agents/*.md"),
            )
        }
        facts["plugins"][package.name] = {"sources": counts, "codex_entries": len(entries)}
        facts["source_procedures"] += sum(counts.values())
        facts["codex_entries"] += len(entries)
    if not facts["plugins"]:
        raise ValueError("No plugin inventory in the base checkout")
    text = (
        "# Trusted base review context\n\n"
        "This context describes the base checkout, not the proposed PR HEAD. "
        "A PR may intentionally change these facts; verify its complete diff. "
        "Do not infer that a base helper is absent merely because it has no diff hunk.\n\n"
        + agents.read_text(encoding="utf-8").strip()
        + "\n\n## Machine-derived base inventory\n\n```json\n"
        + json.dumps(facts, indent=2, sort_keys=True)
        + "\n```\n"
    )
    size = len(text.encode("utf-8"))
    if size > CONTEXT_CAP:
        agent_size = agents.stat().st_size
        raise ValueError(
            f"Assembled context {size} B exceeds {CONTEXT_CAP} B: "
            f"AGENTS.md={agent_size}/{AGENTS_CAP} B, facts/header={size - agent_size} B"
        )
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        text = build_context(args.root)
        args.output.write_text(text, encoding="utf-8")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Review context unavailable: {exc}\n")
    print(f"Verified base context: {len(text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
