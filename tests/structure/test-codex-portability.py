#!/usr/bin/env python3
"""Behavioral packaging regressions; no network or model calls."""
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "scripts/sync-codex-plugins.py"


class PortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Test the generator against source inputs, independently of whether a
        # checkout has already published the generated adapters.
        cls.temporary = tempfile.TemporaryDirectory(prefix="codex generated ")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.generated = Path(cls.temporary.name)
        patterns = ("*/.claude-plugin/plugin.json", "*/.mcp.json",
                    "*/skills/*/SKILL.md", "*/commands/*.md", "*/agents/*.md")
        for pattern in patterns:
            for source in (ROOT / "plugins").glob(pattern):
                target = cls.generated / source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        shutil.copytree(ROOT / "scripts/codex", cls.generated / "scripts/codex")
        shutil.copyfile(ROOT / "scripts/sync-plugin-cache.sh", cls.generated / "scripts/sync-plugin-cache.sh")
        shutil.copytree(ROOT / "hosts", cls.generated / "hosts")
        target = cls.generated / ".claude-plugin/marketplace.json"
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / ".claude-plugin/marketplace.json", target)
        target = cls.generated / ".agents/plugins/marketplace.json"
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / ".agents/plugins/marketplace.json", target)
        subprocess.run([sys.executable, str(GENERATOR), "--root", str(cls.generated)],
                       check=True, capture_output=True, text=True)

    def test_generated_adapters_are_current(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.generated), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_rejects_modified_generated_entry(self):
        path = next((self.generated / "plugins").glob("*/.codex-plugin/skills/*/SKILL.md"))
        original = path.read_text()
        try:
            path.write_text(original + "\nUnreviewed drift.\n")
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--root", str(self.generated), "--check"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("stale Codex artifact", result.stdout)
        finally:
            path.write_text(original)

    def test_real_checkout_gate_cannot_skip_missing_or_downgraded_adapters(self):
        gate = ROOT / "tests/structure/test-codex-published.sh"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            shutil.copyfile(GENERATOR, root / "scripts/sync-codex-plugins.py")
            command = ["bash", "-euo", "pipefail", "-c",
                       'pass() { :; }; fail() { return 1; }; source "$1"', "fixture", str(gate)]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            manifest = root / "plugins/project-init/.codex-plugin/plugin.json"
            original = manifest.read_bytes()
            manifest.unlink()
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode, "missing package escaped the real-checkout gate")
            data = json.loads(original)
            data["skills"] = "./skills/"
            manifest.write_text(json.dumps(data))
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode, "downgraded package escaped the real-checkout gate")

    def head_workflow(self):
        path = ROOT / ".github/workflows/codex-validation.yml"
        self.assertTrue(path.is_file(), "Independent PR-head validation workflow is missing")
        source = path.read_text()
        extract = runpy.run_path(str(ROOT / "tests/structure/test-pr-review-template.py"))["template_steps"]
        return source, extract(source)

    def test_head_validation_runs_without_privileged_runner_or_credentials(self):
        source, steps = self.head_workflow()
        self.assertRegex(source, r"(?m)^  pull_request:\s*$")
        self.assertNotIn("pull_request_target", source)
        self.assertRegex(source, r"(?m)^    runs-on: ubuntu-latest\s*$")
        self.assertNotIn("self-hosted", source)
        permissions = re.search(r"(?m)^permissions:\n((?:  [^\n]*\n)+)", source)
        self.assertIsNotNone(permissions)
        self.assertEqual(["contents: read"], permissions[1].strip().splitlines())
        self.assertNotRegex(source, r"(?m)^ +(?:permissions|env|environment|if|paths|paths-ignore|continue-on-error):")
        self.assertNotIn("secrets.", source)
        checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual("${{ github.event.pull_request.head.sha }}", checkout["with"]["ref"])
        self.assertIs(False, checkout["with"]["persist-credentials"])

    def test_head_generator_change_and_outputs_pass_but_stale_output_fails(self):
        _, steps = self.head_workflow()
        check = next(step["run"] for step in steps
                     if step.get("name") == "Check all generated Codex artifacts")
        self.assertNotIn("--plugin", check, "The head check must cover every plugin")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            head_generator = root / "scripts/sync-codex-plugins.py"
            source = GENERATOR.read_text()
            before = "Read [Codex runtime guidance]"
            self.assertIn(before, source)
            head_generator.write_text(source.replace(before, "Read the [Codex runtime guidance]"))
            subprocess.run([sys.executable, str(head_generator)], cwd=root, check=True,
                           capture_output=True, text=True)
            # The former trusted-base byte check rejects a legitimate logic change.
            old = subprocess.run([sys.executable, str(GENERATOR), "--check", "--root", str(root)],
                                 capture_output=True, text=True)
            self.assertNotEqual(0, old.returncode)
            current = subprocess.run(["bash", "-euo", "pipefail", "-c", check],
                                     cwd=root, capture_output=True, text=True)
            self.assertEqual(0, current.returncode, current.stdout + current.stderr)
            artifact = next(root.glob("plugins/*/.codex-plugin/skills/*/SKILL.md"))
            artifact.write_text(artifact.read_text() + "\nStale generated output.\n")
            stale = subprocess.run(["bash", "-euo", "pipefail", "-c", check],
                                   cwd=root, capture_output=True, text=True)
            self.assertNotEqual(0, stale.returncode)
            self.assertIn("stale Codex artifact", stale.stdout)

    def test_relative_root_preserves_generated_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            before = set(root.glob("plugins/*/.codex-plugin/skills/*/SKILL.md"))
            self.assertTrue(before)
            for flags in ([], ["--check"]):
                result = subprocess.run(
                    [sys.executable, str(GENERATOR), "--root", ".", *flags],
                    cwd=root, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(all(path.is_file() for path in before),
                                "generation with a relative root deleted valid skills")

    def test_regeneration_removes_obsolete_skill_directory(self):
        plugin = next((self.generated / "plugins").iterdir())
        obsolete = plugin / ".codex-plugin/skills/obsolete/SKILL.md"
        obsolete.parent.mkdir(parents=True)
        obsolete.write_text("---\nname: obsolete\ndescription: Removed source\n---\n")
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--root", str(self.generated)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(obsolete.parent.exists())

    def test_scoped_generation_does_not_rewrite_other_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            other = root / "plugins/token-saver/.codex-plugin/runtime.md"
            changed = other.read_text() + "\nUnrelated pending change.\n"
            other.write_text(changed)
            for flags in ([], ["--check"]):
                result = subprocess.run(
                    [sys.executable, str(GENERATOR), "--root", str(root),
                     "--plugin", "kiro", *flags], capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(changed, other.read_text())
            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--root", str(root), "--check"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1, "full check must still detect unselected drift")

    def test_regeneration_updates_selected_marketplace_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            source = root / "hosts/catalog.json"
            manifest = json.loads(source.read_text())
            manifest["plugins"]["kiro"]["version"] = "9.8.7"
            source.write_text(json.dumps(manifest))
            market = root / ".agents/plugins/marketplace.json"
            before = json.loads(market.read_text())
            selected = next(p for p in before["plugins"] if p["name"] == "kiro")
            selected["policy"]["installation"] = "NOT_AVAILABLE"
            market.write_text(json.dumps(before))
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root),
                            "--plugin", "kiro"], check=True, capture_output=True)
            after = json.loads(market.read_text())
            actual = next(p for p in after["plugins"] if p["name"] == "kiro")
            self.assertEqual("9.8.7", actual["version"])
            self.assertEqual(selected["policy"], actual["policy"])
            self.assertEqual([p for p in before["plugins"] if p["name"] != "kiro"],
                             [p for p in after["plugins"] if p["name"] != "kiro"])

    def test_removed_optional_artifacts_fail_check_and_are_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            adapter = root / "plugins/project-init/.codex-plugin"
            guide = root / "scripts/codex/project-init.md"
            guide.unlink(missing_ok=True)
            args = [sys.executable, str(GENERATOR), "--root", str(root),
                    "--plugin", "project-init"]
            subprocess.run(args, check=True, capture_output=True)
            names = ("hook.py", "hooks.json", "hook-handlers.json", "mcp.json", "workflow.md")
            for name in names:
                (adapter / name).write_text("obsolete generated artifact\n")
            manual = adapter / "operator-notes.txt"
            manual.write_text("Keep this unowned file.\n")
            self.assertNotEqual(0, subprocess.run(args + ["--check"], capture_output=True).returncode)
            subprocess.run(args, check=True, capture_output=True)
            self.assertTrue(all(not (adapter / name).exists() for name in names))
            self.assertEqual("Keep this unowned file.\n", manual.read_text())
            self.assertEqual(0, subprocess.run(args + ["--check"], capture_output=True).returncode)

    def test_every_plugin_exposes_all_source_procedures(self):
        for plugin in sorted((self.generated / "plugins").iterdir()):
            if not (plugin / ".claude-plugin/plugin.json").is_file():
                continue
            with self.subTest(plugin=plugin.name):
                inventory = plugin / ".codex-plugin/inventory.json"
                self.assertTrue(inventory.is_file(), str(inventory))
                data = json.loads(inventory.read_text())
                actual = {s for entry in data["skills"] for s in entry["sources"]}
                expected = {
                    str(p.relative_to(plugin))
                    for pattern in ("skills/*/SKILL.md", "commands/*.md", "agents/*.md")
                    for p in plugin.glob(pattern)
                    if p.name not in {"README.md", "CLAUDE.md", "AGENTS.md"}
                }
                self.assertEqual(actual, expected)
                for entry in data["skills"]:
                    skill = plugin / entry["path"]
                    self.assertTrue(skill.is_file(), str(skill))
                    for source in entry["sources"]:
                        self.assertTrue((plugin / source).is_file(), source)

    def test_claude_only_migration_has_an_explicit_codex_target_guard(self):
        plugin = self.generated / "plugins/project-init"
        entry = (plugin / ".codex-plugin/skills/migrate-hooks/SKILL.md").read_text()
        self.assertIn("Migrate legacy Claude Code project hooks", entry)
        self.assertNotIn("Codex or Claude Code hook contract", entry)
        self.assertIn("no Claude migration is applicable", entry)
        self.assertIn("project trust and hook-trust sequence", entry)
        # Native adaptation changes the exposed entry, leaving the upstream command intact.
        self.assertEqual((ROOT / "plugins/project-init/commands/migrate-hooks.md").read_bytes(),
                         (plugin / "commands/migrate-hooks.md").read_bytes())

    def test_unknown_project_commands_keep_their_host_applicability(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            command = root / "plugins/project-init/commands/claude-only-fixture.md"
            command.write_text('---\nname: claude-only-fixture\n'
                               'description: "Inspect Claude Code-only project settings."\n---\nBody.\n')
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root)],
                           check=True, capture_output=True)
            entry = root / "plugins/project-init/.codex-plugin/skills/claude-only-fixture/SKILL.md"
            self.assertIn("Inspect Claude Code-only project settings.", entry.read_text())
            self.assertNotIn("Codex or Claude Code", entry.read_text())

    def test_internal_workers_and_duplicate_delegate_alias_require_explicit_selection(self):
        kiro = self.generated / "plugins/kiro/.codex-plugin/skills"
        for name in ("kiro-delegate-agent", "delegate"):
            policy = kiro / name / "agents/openai.yaml"
            text = policy.read_text()
            # `interface` is mandatory whenever agents/openai.yaml exists at all (see
            # test_openai_yaml_carries_no_key_outside_codex_plugin_validation) — assert
            # the policy line rather than the whole file, so that check owns the shape.
            self.assertIn("policy:\n  allow_implicit_invocation: false\n", text)
        for name in ("kiro-delegate", "configure"):
            self.assertFalse((kiro / name / "agents/openai.yaml").exists())
        # A combined canonical skill + specialist stays an automatic workflow entry.
        co = self.generated / "plugins/co-agent/.codex-plugin/skills/co-agent"
        self.assertFalse((co / "agents/openai.yaml").exists())

    def test_generated_file_hooks_explicitly_match_apply_patch(self):
        checked = 0
        for path in (self.generated / "plugins").glob("*/.codex-plugin/hook-handlers.json"):
            originals = json.loads(path.read_text())["handlers"]
            configured = json.loads((path.parent / "hooks.json").read_text())["hooks"]
            emitted = [(event, group.get("matcher", ""))
                       for event, groups in configured.items()
                       for group in groups for _ in group["hooks"]]
            self.assertEqual(len(originals), len(emitted))
            for original, (event, matcher) in zip(originals, emitted):
                if event in {"PreToolUse", "PostToolUse"} and any(
                    alias in original.get("matcher", "") for alias in ("Edit", "Write")
                ):
                    self.assertIsNotNone(re.search(matcher, "apply_patch"), matcher)
                    checked += 1
        self.assertGreater(checked, 0)

    def test_runner_uses_installed_root_preserves_cwd_argv_and_status(self):
        runner = ROOT / "scripts/codex/run.py"
        self.assertTrue(runner.is_file(), str(runner))
        with tempfile.TemporaryDirectory(prefix="codex portability ") as tmp:
            tmp = Path(tmp)
            plugin = tmp / "installed plugin"
            adapter = plugin / ".codex-plugin"
            adapter.mkdir(parents=True)
            shutil.copyfile(runner, adapter / "run.py")
            (adapter / "inventory.json").write_text(json.dumps({"plugin": "co-agent"}))
            helper = plugin / "skills/test/scripts/probe.py"
            helper.parent.mkdir(parents=True)
            helper.write_text(
                "import json, os, sys\n"
                "print(json.dumps({'cwd': os.getcwd(), 'args': sys.argv[1:], "
                "'root': os.environ['CLAUDE_PLUGIN_ROOT'], "
                "'host': os.environ['CO_AGENT_HOST']}))\nsys.exit(7)\n"
            )
            target = tmp / "user repository"
            target.mkdir()
            result = subprocess.run(
                [sys.executable, str(adapter / "run.py"),
                 "skills/test/scripts/probe.py", "space and $(literal)", "--flag"],
                cwd=target, capture_output=True, text=True,
                env={**os.environ, "CO_AGENT_HOST": "claude"},
            )
            self.assertEqual(result.returncode, 7, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output, {
                "cwd": str(target), "args": ["space and $(literal)", "--flag"],
                "root": str(plugin), "host": "codex",
            })

    def test_codex_reasoning_comes_from_its_own_execution_configuration(self):
        checked = 0
        for config in (self.generated / "hosts/codex").glob("*/execution.json"):
            for name, reasoning in json.loads(config.read_text())["reasoning"].items():
                entry = self.generated / "plugins" / config.parent.name / ".codex-plugin/skills" / name / "SKILL.md"
                self.assertIn(f"Codex reasoning intent: {reasoning}.", entry.read_text())
                self.assertNotIn("Source frontmatter:", entry.read_text())
                checked += 1
        self.assertGreater(checked, 0)

    def test_claude_hook_and_model_changes_do_not_change_codex_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            native = root / "plugins/aws-content-plugin/.codex-plugin"
            before = {p.relative_to(native): p.read_bytes() for p in native.rglob("*") if p.is_file()}
            config = root / "hosts/claude/aws-content-plugin/plugin.json"
            value = json.loads(config.read_text())
            value["hooks"] = {"SessionStart": [{"hooks": [{"type": "command", "command": "echo Claude-only"}]}]}
            config.write_text(json.dumps(value))
            agents = root / "hosts/claude/aws-content-plugin/agents.json"
            value = json.loads(agents.read_text())
            value["reactive-presentation-agent.md"]["model"] = "haiku"
            agents.write_text(json.dumps(value))
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root)], check=True, capture_output=True)
            self.assertEqual(before, {p.relative_to(native): p.read_bytes() for p in native.rglob("*") if p.is_file()})
            installed = root / "packages/claude/aws-content-plugin/agents/reactive-presentation-agent.md"
            self.assertRegex(installed.read_text(), r'(?m)^model: "haiku"$')
            self.assertIn('mcpServers:\n  - "playwright"', installed.read_text())

    def test_claude_execution_fields_are_not_inherited_from_shared_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            source = root / "plugins/project-init/agents/doc-sync-checker.md"
            original = source.read_text()
            source.write_text(original.replace("model: opus", "model: haiku\nmemory: project\neffort: low"))
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root)], check=True, capture_output=True)
            installed = root / "packages/claude/project-init/agents/doc-sync-checker.md"
            self.assertRegex(installed.read_text(), r'(?m)^model: "opus"$')
            self.assertNotRegex(installed.read_text(), r"(?m)^(memory|effort):")
            self.assertEqual(original.replace("model: opus", "model: haiku\nmemory: project\neffort: low"), source.read_text())

    def test_codex_hook_changes_do_not_change_claude_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            package = root / "packages/claude/aws-content-plugin"
            before = {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()}
            config = root / "hosts/codex/aws-content-plugin/hooks.json"
            value = json.loads(config.read_text())
            value["hooks"]["SessionStart"][0]["hooks"][0]["command"] = "echo Codex-only"
            config.write_text(json.dumps(value))
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root)], check=True, capture_output=True)
            self.assertEqual(before, {p.relative_to(package): p.read_bytes() for p in package.rglob("*") if p.is_file()})
            installed = root / "packages/codex/aws-content-plugin/.codex-plugin/hooks.json"
            self.assertEqual(value, json.loads(installed.read_text()))

    def test_both_host_packages_work_without_the_source_tree(self):
        with tempfile.TemporaryDirectory(prefix="separate hosts ") as tmp:
            root = Path(tmp) / "source"
            shutil.copytree(self.generated, root)
            source = root / "plugins/token-saver"
            (source / "shared-probe.py").write_text("from pathlib import Path\nprint(Path(__file__).with_name('asset.bin').read_bytes().hex())\n")
            (source / "asset.bin").write_bytes(b"\x00\xfffixture")
            (source / "shared-probe.py").chmod(0o755)
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root)], check=True, capture_output=True)
            installed = Path(tmp) / "installed"
            shutil.copytree(root / "packages", installed)
            shutil.rmtree(root)
            for host, other in (("claude", "codex"), ("codex", "claude")):
                package = installed / host / "token-saver"
                self.assertTrue((package / f".{host}-plugin/plugin.json").is_file())
                self.assertFalse((package / f".{other}-plugin").exists())
                self.assertTrue((package / "shared-probe.py").stat().st_mode & 0o111)
                result = subprocess.run([sys.executable, str(package / "shared-probe.py")], capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(b"\x00\xfffixture".hex(), result.stdout.strip())

    def test_package_check_rejects_and_prunes_foreign_host_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            foreign = root / "packages/codex/kiro/.claude-plugin/plugin.json"
            foreign.parent.mkdir()
            foreign.write_text("{}")
            args = [sys.executable, str(GENERATOR), "--root", str(root)]
            self.assertNotEqual(0, subprocess.run(args + ["--check"], capture_output=True).returncode)
            subprocess.run(args, check=True, capture_output=True)
            self.assertFalse(foreign.exists())

    def test_cache_inspection_and_fix_are_isolated_by_host_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            state = Path(tmp) / "state"
            shutil.copytree(self.generated, root)
            name = "token-saver"
            version = json.loads((root / "hosts/catalog.json").read_text())["plugins"][name]["version"]
            for host, directory in (("claude", version), ("codex", "local")):
                package = state / ("." + host) / "plugins/cache/oh-my-cloud-skills" / name / directory
                shutil.copytree(root / "packages" / host / name, package)
            args = ["bash", str(root / "scripts/sync-plugin-cache.sh"), "--state-root", str(state)]
            self.assertEqual(0, subprocess.run(args, capture_output=True).returncode)
            cached = state / ".codex/plugins/cache/oh-my-cloud-skills/token-saver/local"
            target = cached / "skills/concise-responses/SKILL.md"
            target.write_text("stale")
            self.assertNotEqual(0, subprocess.run(args, capture_output=True).returncode)
            self.assertEqual("stale", target.read_text(), "inspection must be read-only")
            result = subprocess.run(args + ["--host", "codex", "--fix"], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual((root / "packages/codex/token-saver/skills/concise-responses/SKILL.md").read_bytes(), target.read_bytes())
            foreign = cached / ".claude-plugin/plugin.json"
            foreign.parent.mkdir()
            foreign.write_text("{}")
            self.assertNotEqual(0, subprocess.run(args + ["--fix"], capture_output=True).returncode)
            self.assertTrue(foreign.is_file(), "combined installs require host reinstallation")

    def test_catalog_membership_adds_and_removes_both_host_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            shutil.copytree(root / "plugins/token-saver", root / "plugins/extra")
            for host in ("claude", "codex"):
                shutil.copytree(root / "hosts" / host / "token-saver", root / "hosts" / host / "extra")
            source = root / "plugins/extra/.claude-plugin/plugin.json"
            value = json.loads(source.read_text())
            value["name"] = "extra"
            source.write_text(json.dumps(value))
            handlers = root / "hosts/codex/extra/hook-handlers.json"
            value = json.loads(handlers.read_text())
            value["plugin"] = "extra"
            handlers.write_text(json.dumps(value))
            catalog = root / "hosts/catalog.json"
            value = json.loads(catalog.read_text())
            value["plugins"]["extra"] = {**value["plugins"]["token-saver"], "name": "extra"}
            catalog.write_text(json.dumps(value))
            args = [sys.executable, str(GENERATOR), "--root", str(root)]
            subprocess.run(args, check=True, capture_output=True)
            for host, market in (("claude", ".claude-plugin/marketplace.json"),
                                ("codex", ".agents/plugins/marketplace.json")):
                self.assertTrue((root / "packages" / host / "extra").is_dir())
                self.assertIn("extra", [p["name"] for p in json.loads((root / market).read_text())["plugins"]])
            value["plugins"].pop("extra")
            catalog.write_text(json.dumps(value))
            shutil.rmtree(root / "plugins/extra")
            for host in ("claude", "codex"):
                shutil.rmtree(root / "hosts" / host / "extra")
            subprocess.run(args, check=True, capture_output=True)
            for host, market in (("claude", ".claude-plugin/marketplace.json"),
                                ("codex", ".agents/plugins/marketplace.json")):
                self.assertFalse((root / "packages" / host / "extra").exists())
                self.assertNotIn("extra", [p["name"] for p in json.loads((root / market).read_text())["plugins"]])

    def test_claude_mod_registration_is_excluded_from_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(self.generated, root, dirs_exist_ok=True)
            plugin = root / "plugins/pr-dash"
            (plugin / "hooks").mkdir(exist_ok=True)
            (plugin / "hooks/hooks.json").write_text('{"modules":["./register.ts"]}')
            (plugin / "hooks/register.ts").write_text('// Claude-only mod fixture\n')
            subprocess.run([sys.executable, str(GENERATOR), "--root", str(root)], check=True, capture_output=True)
            self.assertTrue((root / "packages/claude/pr-dash/hooks/hooks.json").is_file())
            self.assertFalse((root / "packages/codex/pr-dash/hooks").exists())
            self.assertTrue((root / "packages/codex/pr-dash/.codex-plugin/skills/pr-status/SKILL.md").is_file())

    def test_openai_yaml_matches_codex_plugin_validation(self):
        # codex-cli 0.154.0's own plugin validator (validate_skill_agent_manifest,
        # confirmed against the copy at ~/.codex/skills/.system/plugin-creator —
        # not imported here since that path is this machine's local install, not
        # part of this repo/CI) runs on ANY skill shipping agents/openai.yaml at all,
        # and REQUIRES `interface.display_name`/`interface.short_description`
        # (non-empty) in addition to `policy.allow_implicit_invocation` — a
        # policy-only file, valid-looking YAML though it is, fails that validator
        # outright. Re-derive the same shape with pyyaml here (a test-only
        # dependency; the generator itself stays stdlib-only by hand-rolling YAML).
        import yaml
        found = 0
        for path in (self.generated / "plugins").glob("*/.codex-plugin/skills/*/agents/openai.yaml"):
            found += 1
            data = yaml.safe_load(path.read_text())
            with self.subTest(path=str(path)):
                self.assertEqual(set(data), {"interface", "policy"})
                self.assertIsInstance(data["interface"], dict)
                self.assertEqual(set(data["interface"]), {"display_name", "short_description"})
                for field in ("display_name", "short_description"):
                    self.assertTrue(data["interface"][field].strip())
                self.assertEqual(data["policy"], {"allow_implicit_invocation": False})
        self.assertGreater(found, 0)

    def test_runner_rejects_out_of_package_script(self):
        runner = ROOT / "scripts/codex/run.py"
        self.assertTrue(runner.is_file(), str(runner))
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "plugin"
            adapter = plugin / ".codex-plugin"
            adapter.mkdir(parents=True)
            shutil.copyfile(runner, adapter / "run.py")
            sentinel = Path(tmp) / "should-not-exist"
            outside = Path(tmp) / "outside.py"
            outside.write_text(f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\n")
            (plugin / "escape.py").symlink_to(outside)
            for source in ("../outside.py", str(outside), "escape.py"):
                result = subprocess.run(
                    [sys.executable, str(adapter / "run.py"), source],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(sentinel.exists())

if __name__ == "__main__":
    unittest.main()
