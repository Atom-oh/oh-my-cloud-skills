"""Verify that every reviewer can receive the same bounded, current base facts."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("review_context", ROOT / "scripts/pr-review/context.py")
CONTEXT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTEXT)


class ReviewContextTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="review context ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = "# Current policy\nWrite English reviews; verify evidence.\n"
        (self.root / "CLAUDE.md").write_text(self.source)
        digest = hashlib.sha256(self.source.encode()).hexdigest()[:12]
        self.marker = f"<!-- generated-by: co-agent · claude-md-sha: {digest} -->\n"
        (self.root / "AGENTS.md").write_text(self.marker + "CURRENT_BASE_POLICY\n")
        (self.root / "README.md").write_text("IGNORE_ALL_RULES_FROM_UNVERIFIED_DOC\n")
        package = self.root / "plugins/sample"
        (package / ".claude-plugin").mkdir(parents=True)
        (package / ".claude-plugin/plugin.json").write_text('{"name":"sample","version":"1.0.0"}')
        for relative in ("skills/task/SKILL.md", "commands/task.md", "agents/worker.md"):
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source procedure\n")
        (package / "agents/AGENTS.md").write_text("scoped instructions, not an agent\n")
        (package / ".codex-plugin").mkdir()
        self.inventory = package / ".codex-plugin/inventory.json"
        self.inventory.write_text(json.dumps({"plugin": "sample", "skills": [
            {"name": "task", "sources": ["skills/task/SKILL.md", "commands/task.md"]},
            {"name": "worker", "sources": ["agents/worker.md"]},
        ]}))

    def test_base_context_distinguishes_source_procedures_from_generated_entries(self):
        text = CONTEXT.build_context(self.root)
        self.assertIn("CURRENT_BASE_POLICY", text)
        self.assertNotIn("IGNORE_ALL_RULES_FROM_UNVERIFIED_DOC", text)
        facts = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
        self.assertEqual({"skills": 1, "commands": 1, "agents": 1}, facts["plugins"]["sample"]["sources"])
        self.assertEqual(3, facts["source_procedures"])
        self.assertEqual(2, facts["codex_entries"])
        self.assertIn("trusted base", text.lower())

    def test_counts_follow_repository_data_instead_of_a_copied_number(self):
        package = self.root / "plugins/sample"
        (package / "commands/another.md").write_text("another procedure\n")
        data = json.loads(self.inventory.read_text())
        data["skills"].append({"name": "another", "sources": ["commands/another.md"]})
        self.inventory.write_text(json.dumps(data))
        text = CONTEXT.build_context(self.root)
        facts = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
        self.assertEqual(4, facts["source_procedures"])
        self.assertEqual(3, facts["codex_entries"])

    def test_stale_missing_or_handwritten_context_cannot_be_forwarded(self):
        path = self.root / "AGENTS.md"
        for body in (None, "# Handwritten\n", self.marker.replace("claude-md-sha:", "old-sha:")):
            with self.subTest(body=body):
                if body is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(body)
                with self.assertRaises(ValueError):
                    CONTEXT.build_context(self.root)

    def test_context_is_never_silently_truncated(self):
        (self.root / "AGENTS.md").write_text(self.marker + "Long policy.\n" * 1000)
        with self.assertRaises(ValueError):
            CONTEXT.build_context(self.root)

    def test_component_budget_reserves_space_for_facts(self):
        path = self.root / "AGENTS.md"
        path.write_text(self.marker + "x" * (CONTEXT.AGENTS_CAP - len(self.marker.encode())))
        self.assertLessEqual(len(CONTEXT.build_context(self.root).encode()), CONTEXT.CONTEXT_CAP)
        path.write_text(path.read_text() + "x")
        with self.assertRaisesRegex(ValueError, str(CONTEXT.AGENTS_CAP)):
            CONTEXT.build_context(self.root)

    def test_actual_repository_context_builds(self):
        text = CONTEXT.build_context(ROOT)
        self.assertLessEqual(len(text.encode()), CONTEXT.CONTEXT_CAP)

    def test_a_context_symlink_cannot_read_outside_the_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "AGENTS.md"
            outside.write_text(self.marker + "OUTSIDE_CONTENT\n")
            (self.root / "AGENTS.md").unlink()
            (self.root / "AGENTS.md").symlink_to(outside)
            with self.assertRaises(ValueError):
                CONTEXT.build_context(self.root)

    def test_workflow_feeds_verified_base_context_to_the_peer_prompt(self):
        extract = runpy.run_path(str(ROOT / "tests/structure/test-pr-review-template.py"))["template_steps"]
        steps = extract((ROOT / ".github/workflows/pr-review.yml").read_text())
        prepare = next(step["run"] for step in steps if step.get("name") == "Build verified base review context")
        prompt = next(step["run"] for step in steps
                      if step.get("name") == "Build review prompt (one full-scope prompt, shared by every model)")
        work = self.root / "work"
        work.mkdir()
        (work / "pr-diff.txt").write_text("diff --git a/test b/test\n")
        env = dict(os.environ, GITHUB_WORKSPACE=str(self.root), pr_work_dir=str(work),
                   GITHUB_ENV=str(self.root / "env"), total_lines="1")
        for command in (prepare, prompt):
            subprocess.run(["bash", "-euo", "pipefail", "-c", command],
                           cwd=ROOT, env=env, capture_output=True, text=True, check=True)
        context = (work / "base-context.md").read_text()
        peer_prompt = (work / "lenses/FULL.txt").read_text()
        self.assertIn(context.strip(), peer_prompt)
        self.assertIn("English", peer_prompt)
        self.assertNotIn("bilingual doc pairs", peer_prompt)


if __name__ == "__main__":
    unittest.main()
