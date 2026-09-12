#!/usr/bin/env python3
"""Adapt trusted bundled command hooks to Codex's multi-file patch payload."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def patch_changes(patch):
    changes = []
    for line in patch.splitlines():
        for marker, tool in (("*** Add File: ", "Write"), ("*** Update File: ", "Edit"),
                             ("*** Delete File: ", "Edit")):
            if line.startswith(marker):
                changes.append((line[len(marker):], tool))
                break
        else:
            if line.startswith("*** Move to: ") and changes:
                changes[-1] = (line[len("*** Move to: "):], changes[-1][1])
    return list(dict.fromkeys(changes))


def main():
    adapter = Path(__file__).resolve().parent
    root = adapter.parent
    try:
        config = json.loads((adapter / "hook-handlers.json").read_text(encoding="utf-8"))
        handler = config["handlers"][int(sys.argv[1])]
        payload = json.load(sys.stdin)
        event = handler["event"]
        if payload.get("hook_event_name") != event:
            raise ValueError("hook event does not match the installed handler")
        cwd = Path(payload["cwd"]).resolve()
        env = dict(os.environ, PLUGIN_ROOT=str(root), CLAUDE_PLUGIN_ROOT=str(root),
                   CLAUDE_PROJECT_DIR=str(cwd))
        if config["plugin"] == "co-agent":
            env["CO_AGENT_HOST"] = "codex"
        inputs = [payload]
        if payload.get("tool_name") == "apply_patch" and any(
            alias in handler.get("matcher", "") for alias in ("Edit", "Write")
        ):
            inputs = []
            for path, tool in patch_changes(payload.get("tool_input", {}).get("command", "")):
                if re.search(handler["matcher"], tool) is None:
                    continue
                # No command interpolation: the path is passed only as stdin JSON.
                absolute = str((cwd / path).resolve())
                inputs.append({
                    **payload, "tool_name": tool,
                    "tool_input": {**payload.get("tool_input", {}), "file_path": absolute},
                })
        outputs = []
        for item in inputs:
            result = subprocess.run(
                ["bash", "-c", handler["command"]], cwd=cwd, env=env,
                input=json.dumps(item), capture_output=True, text=True,
            )
            if result.stderr:
                sys.stderr.write(result.stderr)
            if result.returncode:
                sys.stdout.write(result.stdout)
                return result.returncode
            if result.stdout.strip():
                outputs.append(result.stdout)
        if len(inputs) == 1:
            # Preserve legacy blocking decisions and all event-specific fields.
            sys.stdout.write("".join(outputs))
        elif outputs:
            messages = []
            warnings = []
            for output in outputs:
                value = json.loads(output)
                specific = value.get("hookSpecificOutput", {})
                if specific.get("additionalContext"):
                    messages.append(specific["additionalContext"])
                if value.get("systemMessage"):
                    warnings.append(value["systemMessage"])
                if value.get("continue") is False or value.get("decision") == "block":
                    print(output, end="")
                    return 0
                if specific.get("permissionDecision") in ("deny", "ask"):
                    print(output, end="")
                    return 0
            value = {"hookSpecificOutput": {
                "hookEventName": event, "additionalContext": "\n".join(dict.fromkeys(messages)),
            }}
            if warnings:
                value["systemMessage"] = "\n".join(dict.fromkeys(warnings))
            print(json.dumps(value))
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        print(f"Codex plugin hook failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
