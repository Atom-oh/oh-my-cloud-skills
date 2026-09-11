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
        }
        subprocess.run(["git", "init", "-q", str(self.repo)], env=self.env,
                       check=True, capture_output=True, text=True)
        (self.plugin / "probe.py").write_text(
            "import json, os, sys\n"
            "p = json.load(sys.stdin)\n"
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


if __name__ == "__main__":
    unittest.main()
