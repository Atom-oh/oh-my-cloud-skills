"""Exercise installed hook routing with real local Git roots and JSON payloads."""

import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


BRIDGE = Path(__file__).resolve().parents[2] / "scripts/codex/hook.py"


class HookRoutingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="hook routing ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.plugin = self.root / "installed plugin"
        self.adapter = self.plugin / ".codex-plugin"
        self.adapter.mkdir(parents=True)
        shutil.copyfile(BRIDGE, self.adapter / "hook.py")
        self.repo = self.root / "consumer repo "
        self.repo.mkdir()
        self.cwd = self.repo / "nested directory"
        self.cwd.mkdir()
        self.env = {
            **os.environ, "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
            "CLAUDE_PROJECT_DIR": str(self.plugin),
            "PROBE_MODE": "", "PROBE_BLOCK_PATH": "",
            "PROBE_OUTPUTS": "",
        }
        subprocess.run(["git", "init", "-q", str(self.repo)], env=self.env,
                       check=True, capture_output=True, text=True)
        (self.plugin / "probe.py").write_text(
            "import json, os, sys\n"
            "p = json.load(sys.stdin)\n"
            "if os.environ['PROBE_OUTPUTS']:\n"
            "    outputs = json.loads(os.environ['PROBE_OUTPUTS'])\n"
            "    name = os.path.basename(p['tool_input'].get('file_path', ''))\n"
            "    value = outputs[name]\n"
            "    if isinstance(value, dict) and 'fixtureExit' in value:\n"
            "        print('fixture child error', file=sys.stderr)\n"
            "        sys.exit(value['fixtureExit'])\n"
            "    if isinstance(value, str): sys.stdout.write(value)\n"
            "    elif value is not None: print(json.dumps(value))\n"
            "    sys.exit(0)\n"
            "record = {'cwd': os.getcwd(), 'project': os.environ['CLAUDE_PROJECT_DIR'],\n"
            "          'tool': p['tool_name'], 'input': p['tool_input']}\n"
            "specific = {'hookEventName': p['hook_event_name'],\n"
            "            'additionalContext': json.dumps(record)}\n"
            "if p['tool_input'].get('file_path') == os.environ['PROBE_BLOCK_PATH'] or os.environ['PROBE_MODE'] == 'deny-bash':\n"
            "    if os.environ['PROBE_MODE'] == 'exit2':\n"
            "        print('old path blocked', file=sys.stderr)\n"
            "        sys.exit(2)\n"
            "    if os.environ['PROBE_MODE'] in ('deny', 'deny-bash'):\n"
            "        specific.update(permissionDecision='deny', permissionDecisionReason='old path blocked')\n"
            "print(json.dumps({'hookSpecificOutput': specific}))\n"
        )

    def invoke(self, matcher, patch="", event="PostToolUse", cwd=None, tool="apply_patch"):
        (self.adapter / "hook-handlers.json").write_text(json.dumps({
            "plugin": "fixture",
            "handlers": [{
                "event": event, "matcher": matcher,
                "command": f'{shlex.quote(sys.executable)} "$CLAUDE_PLUGIN_ROOT/probe.py"',
            }],
        }))
        payload = {"cwd": str(cwd or self.cwd), "hook_event_name": event,
                   "tool_name": tool, "tool_input": {"command": patch}}
        return subprocess.run(
            [sys.executable, "-B", str(self.adapter / "hook.py"), "0"],
            cwd=self.root, env=self.env, input=json.dumps(payload),
            capture_output=True, text=True, timeout=10,
        )

    def records(self, result):
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(result.stdout.strip(), "The matched hook received no payload")
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        return [json.loads(line) for line in context.splitlines()]

    def rename(self):
        old = self.cwd / "old $(touch injected).md"
        new = self.cwd / "new `touch injected`.md"
        old.write_text("before\n")
        old.rename(new)
        return old, new, (
            f"*** Begin Patch\n*** Update File: {old.name}\n"
            f"*** Move to: {new.name}\n@@\n-before\n+after\n*** End Patch\n"
        )

    def test_git_subdirectory_uses_project_root_and_preserves_process_cwd(self):
        record, = self.records(self.invoke("Bash", "printf fixture", tool="Bash"))
        self.assertEqual(str(self.repo), record["project"])
        self.assertEqual(str(self.cwd), record["cwd"])
        self.assertEqual({"command": "printf fixture"}, record["input"])

    def test_non_git_directory_falls_back_to_payload_cwd(self):
        cwd = self.root / "non git directory"
        cwd.mkdir()
        record, = self.records(self.invoke("Bash", "printf fixture", cwd=cwd, tool="Bash"))
        self.assertEqual(str(cwd), record["project"])
        self.assertEqual(str(cwd), record["cwd"])

    def test_rename_dispatches_old_and_new_paths_as_edit_via_json(self):
        old, new, patch = self.rename()
        records = self.records(self.invoke("^Edit$", patch))
        self.assertEqual([str(old), str(new)], [r["input"]["file_path"] for r in records])
        self.assertEqual(["Edit", "Edit"], [r["tool"] for r in records])
        self.assertTrue(all(r["input"]["command"] == patch for r in records))
        self.assertFalse(list(self.root.rglob("injected")))

    def test_regex_file_alias_is_recognized_without_literal_edit_substring(self):
        patch = "*** Begin Patch\n*** Update File: existing.md\n@@\n-a\n+b\n*** End Patch\n"
        record, = self.records(self.invoke("^Edi[t]$", patch))
        self.assertEqual("Edit", record["tool"])
        self.assertEqual(str(self.cwd / "existing.md"), record["input"]["file_path"])

    def test_multiedit_is_not_mistaken_for_edit_alias(self):
        patch = "*** Begin Patch\n*** Update File: existing.md\n@@\n-a\n+b\n*** End Patch\n"
        record, = self.records(self.invoke("MultiEdit|^apply_patch$", patch))
        self.assertEqual("apply_patch", record["tool"])
        self.assertEqual({"command": patch}, record["input"])

    def test_write_alias_does_not_receive_rename_edits(self):
        _, _, patch = self.rename()
        patch = patch.replace("*** End Patch", "*** Add File: created.md\n+new\n*** End Patch")
        record, = self.records(self.invoke("^Write$", patch))
        self.assertEqual("Write", record["tool"])
        self.assertEqual(str(self.cwd / "created.md"), record["input"]["file_path"])

    def test_mixed_patch_routes_add_move_and_delete_once_per_matching_alias(self):
        patch = ("*** Begin Patch\n*** Add File: new file.md\n+x\n"
                 "*** Update File: old.md\n*** Move to: moved.md\n@@\n-a\n+b\n"
                 "*** Delete File: removed.md\n*** End Patch\n")
        for matcher, names in (("Edit|Write", ["new file.md", "old.md", "moved.md", "removed.md"]),
                               ("Edit", ["old.md", "moved.md", "removed.md"]), ("Write", ["new file.md"])):
            with self.subTest(matcher=matcher):
                records = self.records(self.invoke(matcher, patch))
                self.assertEqual([str(self.cwd / name) for name in names],
                                 [r["input"]["file_path"] for r in records])

    def test_single_bash_denial_is_preserved(self):
        self.env["PROBE_MODE"] = "deny-bash"
        result = self.invoke("Bash", "git push", event="PreToolUse", tool="Bash")
        self.assertEqual(0, result.returncode, result.stderr)
        specific = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("deny", specific["permissionDecision"])
        self.assertEqual("old path blocked", specific["permissionDecisionReason"])

    def test_native_and_default_matchers_keep_original_patch_payload(self):
        patch = "*** Begin Patch\n*** Add File: created.md\n+new\n*** End Patch\n"
        for matcher in ("^apply_patch$", "", "*"):
            with self.subTest(matcher=matcher):
                record, = self.records(self.invoke(matcher, patch))
                self.assertEqual("apply_patch", record["tool"])
                self.assertEqual({"command": patch}, record["input"])

    def test_rename_preserves_json_denial_for_old_path(self):
        old, _, patch = self.rename()
        self.env.update(PROBE_MODE="deny", PROBE_BLOCK_PATH=str(old))
        result = self.invoke("Edit", patch, event="PreToolUse")
        self.assertEqual(0, result.returncode, result.stderr)
        specific = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("deny", specific.get("permissionDecision"))
        self.assertEqual("old path blocked", specific.get("permissionDecisionReason"))

    def test_rename_preserves_exit_two_block_for_old_path(self):
        old, _, patch = self.rename()
        self.env.update(PROBE_MODE="exit2", PROBE_BLOCK_PATH=str(old))
        result = self.invoke("Edit", patch, event="PreToolUse")
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("old path blocked", result.stderr)

    def outputs(self, values, event="PreToolUse", matcher="Edit"):
        self.env["PROBE_OUTPUTS"] = json.dumps({
            f"file-{index}.md": value for index, value in enumerate(values)
        })
        patch = "*** Begin Patch\n" + "".join(
            f"*** Update File: file-{index}.md\n@@\n-before\n+after\n"
            for index in range(len(values))
        ) + "*** End Patch\n"
        return self.invoke(matcher, patch, event=event)

    def permission(self, decision):
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": decision,
            "permissionDecisionReason": decision + " reason",
        }}

    def merged(self, values, event="PreToolUse"):
        result = self.outputs(values, event)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_deny_overrides_ask_in_either_file_order(self):
        for decisions in (("ask", "deny"), ("deny", "ask")):
            with self.subTest(decisions=decisions):
                output = self.merged([self.permission(d) for d in decisions])
                specific = output["hookSpecificOutput"]
                self.assertEqual("deny", specific["permissionDecision"])
                self.assertEqual("deny reason", specific["permissionDecisionReason"])

    def test_stop_and_block_override_ask_in_either_order(self):
        for control in ({"continue": False, "stopReason": "stop now"},
                        {"decision": "block", "reason": "block now"}):
            for values in ([self.permission("ask"), control],
                           [control, self.permission("ask")]):
                with self.subTest(values=values):
                    output = self.merged(values)
                    specific = output["hookSpecificOutput"]
                    self.assertEqual("deny", specific["permissionDecision"])
                    self.assertIn(control.get("reason", control.get("stopReason")),
                                  specific["permissionDecisionReason"])
                    self.assertTrue(all(key not in output for key in ("continue", "stopReason", "decision")))

    def test_ask_alone_becomes_supported_denial_not_permission(self):
        output = self.merged([self.permission("ask")])
        self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])
        self.assertIn("approval", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_nonzero_child_never_loses_prior_denial_or_allows_partial_coverage(self):
        for control in (self.permission("deny"), {"decision": "block", "reason": "block reason"},
                        {"continue": False, "stopReason": "stop reason"}, self.permission("allow")):
            for values in ([control, {"fixtureExit": 1}], [{"fixtureExit": 1}, control]):
                with self.subTest(values=values):
                    result = self.outputs(values)
                    self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                    self.assertEqual("", result.stdout)
        result = self.outputs([self.permission("deny"), {"fixtureExit": 1}])
        self.assertIn("deny reason", result.stderr)

    def test_plain_text_and_json_context_are_merged_with_warnings(self):
        notice = {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                        "additionalContext": "JSON notice"},
                  "systemMessage": "review this"}
        for values in (["plain notice\n", notice], [notice, "plain notice\n"]):
            output = self.merged(values, event="PostToolUse")
            self.assertEqual({"plain notice", "JSON notice"},
                             set(output["hookSpecificOutput"]["additionalContext"].splitlines()))
            self.assertEqual("review this", output["systemMessage"])

    def test_plain_json_scalar_status_is_context_and_silent_hooks_stay_silent(self):
        for text in ("42\n", '"status"\n', "true\n"):
            with self.subTest(text=text):
                output = self.merged([text, None], event="PostToolUse")
                self.assertEqual(text.strip(), output["hookSpecificOutput"]["additionalContext"])
        result = self.outputs([None, ""])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_allow_requires_every_input_including_silent_and_plain_results(self):
        allow = self.permission("allow")
        output = self.merged([allow, allow])
        self.assertEqual("allow", output["hookSpecificOutput"]["permissionDecision"])
        for neutral in (None, "", {}, "plain notice"):
            with self.subTest(neutral=neutral):
                for values in ([allow, neutral], [neutral, allow]):
                    output = self.merged(values)
                    self.assertNotIn("permissionDecision", output.get("hookSpecificOutput", {}))

    def test_allow_cannot_approve_unmatched_files_in_the_original_patch(self):
        self.env["PROBE_OUTPUTS"] = json.dumps({"created.md": self.permission("allow")})
        result = self.invoke("Write", "*** Begin Patch\n*** Add File: created.md\n+new\n"
                             "*** Update File: skipped.md\n@@\n-a\n+b\n*** End Patch\n",
                             event="PreToolUse")
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)
        self.assertNotIn("permissionDecision", output.get("hookSpecificOutput", {}))

    def test_identical_supported_metadata_is_preserved(self):
        value = {"continue": True, "systemMessage": "warning",
                 "hookSpecificOutput": {"hookEventName": "PostToolUse",
                                        "additionalContext": "notice"}}
        output = self.merged([value, value], event="PostToolUse")
        self.assertEqual(value, output)
        output = self.merged([value, {}], event="PostToolUse")
        self.assertEqual("warning", output["systemMessage"])

    def test_unknown_fields_cannot_invalidate_a_denial(self):
        deny = self.permission("deny")
        values = [
            {**deny, "fixtureMetadata": {"version": 1}},
            {"hookSpecificOutput": {**deny["hookSpecificOutput"],
                                    "fixtureMetadata": {"version": 1}}},
        ]
        for value in values:
            for outputs in ([value, {}], [value, value]):
                with self.subTest(outputs=outputs):
                    result = self.outputs(outputs)
                    self.assertEqual(2, result.returncode)
                    self.assertIn("fixtureMetadata", result.stderr)
                    self.assertFalse(result.stdout.strip())

    def test_unsupported_suppression_and_post_permission_fields_fail_closed(self):
        for event in ("PreToolUse", "PostToolUse"):
            for flag in (True, False):
                with self.subTest(event=event, flag=flag):
                    result = self.outputs([{"suppressOutput": flag}], event=event)
                    self.assertEqual(2, result.returncode)
                    self.assertEqual("", result.stdout)
        for values in ([self.permission("deny"), {"suppressOutput": True}],
                       [{"suppressOutput": True}, self.permission("deny")],
                       [{**self.permission("deny"), "suppressOutput": True}]):
            result = self.outputs(values)
            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
        for decision in ("allow", "ask", "deny"):
            value = self.permission(decision)
            value["hookSpecificOutput"]["hookEventName"] = "PostToolUse"
            result = self.outputs([value], event="PostToolUse")
            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)

    def test_post_tool_stop_preserves_all_context_and_stop_reason(self):
        stop = {"continue": False, "stopReason": "review required",
                "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "first"}}
        notice = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "second"},
                  "systemMessage": "warning"}
        output = self.merged([stop, notice], event="PostToolUse")
        self.assertFalse(output["continue"])
        self.assertEqual("review required", output["stopReason"])
        self.assertEqual("first\nsecond", output["hookSpecificOutput"]["additionalContext"])
        self.assertEqual("warning", output["systemMessage"])

    def test_pre_continue_true_is_removed_and_post_block_remains_feedback(self):
        output = self.merged([{"continue": True}, self.permission("deny")])
        self.assertNotIn("continue", output)
        self.assertEqual("deny", output["hookSpecificOutput"]["permissionDecision"])
        output = self.merged([{"decision": "block", "reason": "review result"}, {}],
                             event="PostToolUse")
        self.assertEqual("block", output["decision"])
        self.assertEqual("review result", output["reason"])
        self.assertNotIn("permissionDecision", output["hookSpecificOutput"])

    def test_per_file_rewrites_and_conflicting_fields_fail_closed(self):
        rewrite = self.permission("allow")
        rewrite["hookSpecificOutput"]["updatedInput"] = {"file_path": "replacement.md"}
        cases = [
            ([rewrite], "updatedInput"), ([rewrite, rewrite], "updatedInput"),
            ([{"suppressOutput": True}, {"suppressOutput": False}], "suppressOutput"),
            ([{"fixtureMetadata": "one"}, {"fixtureMetadata": "two"}], "fixtureMetadata"),
            ([{"hookSpecificOutput": {"fixtureMetadata": "one"}},
              {"hookSpecificOutput": {"fixtureMetadata": "two"}}], "fixtureMetadata"),
            ([{"hookSpecificOutput": {"updatedMCPToolOutput": {"value": "one"}}}, {}],
             "updatedMCPToolOutput"),
            ([{"hookSpecificOutput": {"hookEventName": "Stop"}}, {}], "hookEventName"),
        ]
        for values, field in cases:
            with self.subTest(field=field, count=len(values)):
                result = self.outputs(values)
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertIn(field, result.stderr)
                self.assertIn("apply_patch", result.stderr)
                self.assertFalse(result.stdout.strip())

    def test_native_input_keeps_untranslated_output_fields(self):
        value = self.permission("allow")
        value["hookSpecificOutput"]["updatedInput"] = {"command": "echo rewritten"}
        (self.plugin / "probe.py").write_text("print(" + repr(json.dumps(value)) + ")\n")
        result = self.invoke("Bash", "echo original", event="PreToolUse", tool="Bash")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(value, json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
