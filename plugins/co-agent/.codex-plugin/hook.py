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
                # A move affects the original path as well as its destination.
                changes.append((line[len("*** Move to: "):], "Edit"))
    return list(dict.fromkeys(changes))


def project_root(cwd):
    try:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return cwd
    # Preserve spaces in real directory names; remove only Git's line ending.
    top = result.stdout.rstrip("\r\n")
    return Path(top).resolve() if result.returncode == 0 and top else cwd


class AggregationError(ValueError):
    """A per-file result cannot safely describe the original apply_patch call."""


def merge_identical(values, excluded):
    merged = {}
    for value in values:
        for key, item in value.items():
            if key in excluded:
                continue
            if key in merged and json.dumps(merged[key], sort_keys=True) != json.dumps(item, sort_keys=True):
                raise AggregationError(f"conflicting {key} values")
            merged[key] = item
    return merged


def merge_text(values, key):
    texts = []
    for value in values:
        text = value.get(key)
        if text is not None and not isinstance(text, str):
            raise AggregationError(f"{key} must be text")
        if text:
            texts.append(text)
    return "\n".join(dict.fromkeys(texts))


def aggregate(outputs, event, complete_coverage):
    if event not in ("PreToolUse", "PostToolUse"):
        raise AggregationError(f"per-file translation is unsupported for {event}")
    values = []
    specifics = []
    for output in outputs:
        try:
            value = json.loads(output) if output.strip() else {}
        except json.JSONDecodeError:
            value = {"hookSpecificOutput": {"additionalContext": output.strip()}}
        if not isinstance(value, dict):
            # A numeric/quoted status line is still plain output, not a hook envelope.
            value = {"hookSpecificOutput": {"additionalContext": output.strip()}}
        specific = value.get("hookSpecificOutput", {})
        if not isinstance(specific, dict):
            raise AggregationError("hookSpecificOutput must be an object")
        if specific.get("hookEventName", event) != event:
            raise AggregationError("hookEventName differs from the installed event")
        # Edit/Write rewrites describe synthetic per-file inputs, not a complete
        # patch. Require a native apply_patch handler rather than losing changes.
        for key in ("updatedInput", "updatedMCPToolOutput", "updatedPermissions"):
            if key in value or key in specific:
                raise AggregationError(f"{key} requires a native apply_patch handler")
        if "suppressOutput" in value or "suppressOutput" in specific:
            raise AggregationError(f"suppressOutput is unsupported for {event}")
        if "continue" in value and not isinstance(value["continue"], bool):
            raise AggregationError("continue must be boolean")
        if event == "PreToolUse" and "stopReason" in value and value.get("continue") is not False:
            raise AggregationError("stopReason requires continue:false for translation")
        if event == "PostToolUse" and any(
            key in specific for key in ("permissionDecision", "permissionDecisionReason")
        ):
            raise AggregationError("permissionDecision fields are unsupported for PostToolUse")
        if value.get("decision") not in (None, "block"):
            raise AggregationError("unsupported decision requires a native apply_patch handler")
        if specific.get("permissionDecision") not in (None, "allow", "ask", "deny"):
            raise AggregationError("unsupported permissionDecision")
        values.append(value)
        specifics.append(specific)

    merged = merge_identical(values, {
        "hookSpecificOutput", "continue", "decision", "reason", "stopReason", "systemMessage",
    })
    specific = merge_identical(specifics, {
        "additionalContext", "permissionDecision", "permissionDecisionReason",
    })
    specific["hookEventName"] = event
    stopped = any(value.get("continue") is False for value in values)
    blocked = any(value.get("decision") == "block" for value in values)
    decisions = [value.get("permissionDecision") for value in specifics]
    if event == "PreToolUse" and (stopped or blocked or "deny" in decisions):
        decision = "deny"
        reasons = [
            merge_text([v for v in specifics if v.get("permissionDecision") == "deny"],
                       "permissionDecisionReason"),
            merge_text([v for v in values if v.get("decision") == "block"], "reason"),
            merge_text([v for v in values if v.get("continue") is False], "stopReason"),
        ]
        reason = "\n".join(dict.fromkeys(text for text in reasons if text)) or "Blocked by source hook."
    elif "ask" in decisions:
        # Codex currently treats ask as a hook failure and then runs the tool.
        decision = "deny"
        reason = "Manual approval required by source hook."
        detail = merge_text([v for v in specifics if v.get("permissionDecision") == "ask"],
                            "permissionDecisionReason")
        if detail:
            reason += "\n" + detail
    elif complete_coverage and decisions and all(item == "allow" for item in decisions):
        decision = "allow"
        reason = merge_text(specifics, "permissionDecisionReason")
    else:
        decision = None
    if decision:
        specific["permissionDecision"] = decision
        if reason:
            specific["permissionDecisionReason"] = reason
    if event == "PostToolUse" and any("continue" in value for value in values):
        merged["continue"] = not stopped
    if event == "PostToolUse" and blocked:
        merged["decision"] = "block"
    for key in ("reason", "stopReason", "systemMessage"):
        text = merge_text(values, key)
        if text and (event == "PostToolUse" or key == "systemMessage"):
            merged[key] = text
    context = merge_text(specifics, "additionalContext")
    if context:
        specific["additionalContext"] = context
    merged["hookSpecificOutput"] = specific
    return merged


def main():
    adapter = Path(__file__).resolve().parent
    root = adapter.parent
    translated = False
    try:
        config = json.loads((adapter / "hook-handlers.json").read_text(encoding="utf-8"))
        handler = config["handlers"][int(sys.argv[1])]
        payload = json.load(sys.stdin)
        event = handler["event"]
        if payload.get("hook_event_name") != event:
            raise ValueError("hook event does not match the installed handler")
        cwd = Path(payload["cwd"]).resolve()
        env = dict(os.environ, PLUGIN_ROOT=str(root), CLAUDE_PLUGIN_ROOT=str(root),
                   CLAUDE_PROJECT_DIR=str(project_root(cwd)))
        if config["plugin"] == "co-agent":
            env["CO_AGENT_HOST"] = "codex"
        inputs = [payload]
        complete_coverage = True
        matcher = handler.get("matcher", "")
        if payload.get("tool_name") == "apply_patch" and matcher not in ("", "*") and any(
            re.search(matcher, alias) is not None for alias in ("Edit", "Write")
        ):
            translated = True
            inputs = []
            changes = patch_changes(payload.get("tool_input", {}).get("command", ""))
            for path, tool in changes:
                if re.search(matcher, tool) is None:
                    continue
                # No command interpolation: the path is passed only as stdin JSON.
                absolute = str((cwd / path).resolve())
                inputs.append({
                    **payload, "tool_name": tool,
                    "tool_input": {**payload.get("tool_input", {}), "file_path": absolute},
                })
            complete_coverage = len(inputs) == len(changes)
        outputs = []
        for item in inputs:
            result = subprocess.run(
                ["bash", "-c", handler["command"]], cwd=cwd, env=env,
                input=json.dumps(item), capture_output=True, text=True,
            )
            if result.stderr:
                sys.stderr.write(result.stderr)
            if result.returncode:
                if translated:
                    previous = aggregate(outputs, event, False)
                    reasons = [previous.get("reason"), previous.get("stopReason"),
                               previous["hookSpecificOutput"].get("permissionDecisionReason")]
                    for reason in dict.fromkeys(text for text in reasons if text):
                        print(reason, file=sys.stderr)
                    raise AggregationError(f"child exited with code {result.returncode}; incomplete file checks")
                sys.stdout.write(result.stdout)
                return result.returncode
            # Silent hooks still count: missing coverage must never imply allow.
            outputs.append(result.stdout)
        if not translated:
            # Preserve legacy blocking decisions and all event-specific fields.
            sys.stdout.write("".join(outputs))
        elif any(output.strip() for output in outputs):
            print(json.dumps(aggregate(outputs, event, complete_coverage)))
        return 0
    except AggregationError as exc:
        print(f"Codex plugin hook cannot aggregate apply_patch: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, IndexError, TypeError, re.error) as exc:
        print(f"Codex plugin hook failed: {exc}", file=sys.stderr)
        return 2 if translated else 1


if __name__ == "__main__":
    sys.exit(main())
