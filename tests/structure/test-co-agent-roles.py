"""Structural contracts for co-agent role consolidation, not host-runtime proof.

No real peer CLI is invoked. Markdown assertions protect routing and safety text;
they do not demonstrate that a host obeyed those instructions at runtime.
"""
import ast
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "plugins/co-agent"
CLAUDE_PACKAGE = ROOT / "packages/claude/co-agent"
CODEX_PACKAGE = ROOT / "packages/codex/co-agent"
PACKAGES = (CLAUDE_PACKAGE, CODEX_PACKAGE)
CODEX_ROOTS = (SOURCE, CODEX_PACKAGE)
ANALYSIS = "skills/co-agent/references/harness-analysis.md"
ROLES = {
    "gate-chair": {
        "tools": "Read, Write, Glob, Grep, Bash",
        "model": "opus",
        "effort": "xhigh",
        "memory": "project",
    },
    "pr-autofix-planner": {
        "tools": "Read, Grep, Glob",
        "model": "opus",
        "effort": "xhigh",
    },
    "pr-autofix-implementer": {
        "tools": "Read, Write, Edit, Grep, Glob",
        "model": "opus",
        "effort": "medium",
    },
}
ENTRIES = set(ROLES) | {
    "co-agent", "configure", "consensus", "decision-reconcile", "harness",
    "pr-autofix", "setup", "sync-context",
}
REMOVED_AGENT_PATHS = {"agents/co-agent.md", "agents/harness-analyst.md"}


def read(path):
    return path.read_text(encoding="utf-8")


def load_json(path):
    return json.loads(read(path))


def compact(text):
    return " ".join(text.split())


def frontmatter_scalar(path, key):
    """Read only scalar fields used here, not a general-purpose YAML parser."""
    parts = read(path).split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise AssertionError(f"Missing frontmatter: {path}")
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", parts[1], re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


class RoleInventoryTests(unittest.TestCase):
    def test_exactly_three_source_and_packaged_agent_files(self):
        for root in (SOURCE, *PACKAGES):
            with self.subTest(root=root):
                self.assertEqual(set(ROLES), {path.stem for path in (root / "agents").glob("*.md")})

    def test_claude_manifests_and_assignments_register_only_retained_roles(self):
        manifests = (
            ROOT / "hosts/claude/co-agent/plugin.json",
            SOURCE / ".claude-plugin/plugin.json",
            CLAUDE_PACKAGE / ".claude-plugin/plugin.json",
        )
        for path in manifests:
            with self.subTest(path=path):
                registered = load_json(path)["agents"]
                self.assertEqual(3, len(registered))
                self.assertEqual({f"./agents/{name}.md" for name in ROLES}, set(registered))
        assignments = load_json(ROOT / "hosts/claude/co-agent/agents.json")
        self.assertEqual({f"{name}.md": fields for name, fields in ROLES.items()}, assignments)

    def test_role_tool_model_effort_and_memory_boundaries(self):
        for root in (SOURCE, *PACKAGES):
            for name, expected in ROLES.items():
                with self.subTest(root=root, role=name):
                    path = root / f"agents/{name}.md"
                    self.assertEqual(name, frontmatter_scalar(path, "name"))
                    for key in ("tools", "model", "effort", "memory"):
                        self.assertEqual(expected.get(key), frontmatter_scalar(path, key))
        chair = compact(read(SOURCE / "agents/gate-chair.md"))
        planner = compact(read(SOURCE / "agents/pr-autofix-planner.md"))
        implementer = compact(read(SOURCE / "agents/pr-autofix-implementer.md"))
        self.assertIn("This agent never fans out.", chair)
        self.assertIn("You judge; you never edit.", planner)
        self.assertIn("You have no shell and no network", implementer)
        self.assertIn("Work ONLY inside the worktree path", implementer)

    def test_codex_has_eleven_entries_with_one_canonical_coagent_source(self):
        for root in CODEX_ROOTS:
            with self.subTest(root=root):
                metadata = root / ".codex-plugin"
                inventory = load_json(metadata / "inventory.json")
                self.assertEqual("co-agent", inventory["plugin"])
                self.assertEqual(11, len(inventory["skills"]))
                entries = {entry["name"]: entry for entry in inventory["skills"]}
                self.assertEqual(ENTRIES, set(entries))
                self.assertEqual(["skills/co-agent/SKILL.md"], entries["co-agent"]["sources"])
                self.assertEqual(
                    ENTRIES,
                    {path.name for path in (metadata / "skills").iterdir() if path.is_dir()},
                )
                for name, entry in entries.items():
                    self.assertTrue((root / entry["path"]).is_file(), name)
                    self.assertTrue(REMOVED_AGENT_PATHS.isdisjoint(entry["sources"]), name)
                entry_text = read(root / entries["co-agent"]["path"])
                self.assertIn("skills/co-agent/SKILL.md", entry_text)
                self.assertNotIn("agents/co-agent.md", entry_text)
                self.assertIn("Codex reasoning intent: xhigh", entry_text)

    def test_removed_agents_and_analyst_metadata_are_not_shipped(self):
        for root in (SOURCE, *PACKAGES):
            with self.subTest(root=root):
                for relative in REMOVED_AGENT_PATHS:
                    self.assertFalse((root / relative).exists(), relative)
                self.assertFalse((root / ".codex-plugin/skills/harness-analyst").exists())
                for path in root.rglob("*"):
                    self.assertNotIn("harness-analyst", path.parts)
        for root in PACKAGES:
            with self.subTest(inventory=root):
                files = load_json(root / "package-inventory.json")["files"]
                self.assertTrue(REMOVED_AGENT_PATHS.isdisjoint(files))
                self.assertFalse(any("harness-analyst" in path for path in files))
                self.assertIn(ANALYSIS, files)

    def test_codex_reasoning_and_explicit_specialists_remain_separate(self):
        execution = load_json(ROOT / "hosts/codex/co-agent/execution.json")
        self.assertEqual(
            {"co-agent": "xhigh", **{name: fields["effort"] for name, fields in ROLES.items()}},
            execution["reasoning"],
        )
        self.assertEqual(set(ROLES), set(execution["explicit_skills"]))
        self.assertEqual(3, len(execution["explicit_skills"]))
        for root in CODEX_ROOTS:
            for name in ROLES:
                with self.subTest(root=root, role=name):
                    metadata = read(root / f".codex-plugin/skills/{name}/agents/openai.yaml")
                    self.assertIn("allow_implicit_invocation: false", metadata)


class HostAnalysisProcedureTests(unittest.TestCase):
    def setUp(self):
        self.configure = read(SOURCE / "commands/configure.md")
        self.analysis = read(SOURCE / ANALYSIS)
        self.normalized = compact(self.analysis)

    def assert_analysis_phrases(self, *phrases):
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.normalized)

    def test_analyze_dispatch_precedes_helper_and_cannot_fall_through(self):
        dispatch = self.configure.index("## Dispatch before helper calls")
        helper = self.configure.index("## Helper")
        self.assertLess(dispatch, helper)
        branch = compact(self.configure[dispatch:helper])
        for phrase in (
            "analyze [session-dir]", ANALYSIS, "current host",
            "has no `analyze` subcommand", "never forward `analyze` or raw `$ARGUMENTS`",
            "without falling through", "explicit user-authorized `set` request",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, branch)

    def test_harness_h5_offers_same_analysis_without_automatic_spawn(self):
        harness = compact(read(SOURCE / "commands/harness.md").split("## H5 — Report", 1)[1])
        self.assertIn('/co-agent:configure analyze "$ORCH_ROOT/.claude/co-agent-consensus"', harness)
        self.assertIn(ANALYSIS, harness)
        self.assertIn("Do not run it automatically or spawn an analyst", harness)
        self.assertNotIn("agents/harness-analyst.md", harness)

    def test_analysis_keeps_read_only_no_fanout_and_explicit_apply_contract(self):
        self.assert_analysis_phrases(
            "Read existing telemetry and configuration only",
            "Do not spawn an analyst, call peer CLIs, run setup/probes",
            "Never write defaults, user/local config, telemetry, reports or agent memory",
            "Do not run `co_agent_config.py set`",
            "A request to analyze is **not** permission to apply",
            "A separate explicit user request must authorize the exact settings and scope",
            "**Applied changes: none.**",
        )

    def test_analysis_counts_plan_gate_rows_and_requires_evidence(self):
        self.assert_analysis_phrases(
            "**Fewer than 3 recorded runs: observations only, no proposals.**",
            "**Count runs as the number of `plan-gate` rows**",
            "not all TSV rows",
            "State the n for each proposal",
            "evidence citations (file + rows/fields)",
            "exact `/co-agent:configure set ...` commands",
            "**no duration, model or call count fields**",
        )
        self.assertIn("`set timeout <seconds>`", self.analysis)
        self.assertNotIn("set <ai> timeout", self.analysis)
        self.assertIn("`set <ai> context_limit <tokens>` only against verified model capacity", self.analysis)
        self.assertIn("Trimming the `models` list does not change that threshold", self.analysis)

    def test_analysis_retains_per_peer_billing_and_memory_caveats(self):
        self.assert_analysis_phrases(
            "Billing is a **per-peer attribute**",
            'never downgrade its model merely to "save tokens"',
            "cite its recorded call volume",
            "preserve mandatory gate coverage",
            "model/effort and project memory are not inherited",
            "do not silently read, move, import or delete them",
        )
        self.assertIn("confirmed included subscription access", self.configure)
        self.assertNotIn("flat-rate) CLI (the default assumption)", self.configure)

    def test_analysis_procedure_is_present_and_identical_in_both_packages(self):
        for root in PACKAGES:
            with self.subTest(root=root):
                self.assertEqual(self.analysis, read(root / ANALYSIS))

    def test_config_helper_does_not_register_analyze_as_a_cli_command(self):
        tree = ast.parse(read(SOURCE / "skills/co-agent/scripts/co_agent_config.py"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        command_literals = {
            node.value for node in ast.walk(main)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        self.assertIn("show", command_literals)
        self.assertIn("set", command_literals)
        self.assertNotIn("analyze", command_literals)
        self.assertFalse(any(isinstance(node, ast.FunctionDef) and node.name == "cmd_analyze" for node in tree.body))


if __name__ == "__main__":
    unittest.main()
