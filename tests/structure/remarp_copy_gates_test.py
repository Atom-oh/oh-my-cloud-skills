"""Regression tests for the Remarp copy gates: EM_DASH, AI_TONE (reactive-nav-detail Task 4)."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("remarp_copy_gates", SCRIPT)
remarp = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = remarp
SPEC.loader.exec_module(remarp)
FRONT = "---\nremarp: true\n---\n"
NOTES = "\n\n:::notes\n{timing: 1min}\n[요약]\n- 요약 한 줄입니다.\n:::\n"


class CopyGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remarp-copy-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def validate(self, target):
        with patch("sys.stdout"):
            return remarp.validate_presentation(target)

    def validate_text(self, text):
        return self.validate(self.write("check.md", FRONT + text))

    @staticmethod
    def rules(findings):
        return {(f["severity"], f["rule"]) for f in findings}

    @staticmethod
    def rule_ids(findings):
        return [f["rule"] for f in findings]

    def test_em_dash_warns_in_body_notes_and_detail(self):
        cases = (
            "## T\n\nA — B\n",
            "## T\n\nx\n\n:::notes\n{timing: 1min}\n[요약]\n- a&mdash;b\n:::\n",
            '## T\n\n[a]{detail=d}\n\n:::detail d "t"\nx · y\n:::\n',
            "## T\n\n:::html\n<p>a &#8212; b</p>\n:::\n",
            "## T\n\n가・나\n",
        )
        for src in cases:
            with self.subTest(src=src):
                self.assertIn(("WARNING", "EM_DASH"), self.rules(self.validate_text(src)))

    def test_em_dash_skips_code_and_urls(self):
        cases = (
            "## T\n\n`a — b`\n",
            "## T\n\n```\na — b\n```\n",
            "## T\n\n[l](https://x.com/a—b)\n",
            "## T\n\n:::html\n<code>&mdash;</code><pre>a — b</pre>\n:::\n",
            '## T\n\n:::html\n<div id="a·b">x</div>\n:::\n',
            "## T\n\n:::html\n<!-- a — b -->\n<p>x</p>\n:::\n",
        )
        for src in cases:
            with self.subTest(src=src):
                self.assertNotIn("EM_DASH", self.rule_ids(self.validate_text(src)))

    def test_em_dash_scans_visible_attributes(self):
        cases = (
            '## T\n\n:::html\n<span class="rp-detail" data-tip="a — b">x</span>\n:::\n',
            '## T\n\n:::html\n<img src="./a.png" alt="a — b">\n:::\n',
            '## T\n\n:::html\n<span title="a · b">x</span>\n:::\n',
        )
        for src in cases:
            with self.subTest(src=src):
                self.assertIn("EM_DASH", self.rule_ids(self.validate_text(src)))

    def test_ai_tone_arrows(self):
        self.assertIn("AI_TONE", self.rule_ids(self.validate_text("## T\n\na → b → c → d → e\n")))
        self.assertNotIn("AI_TONE", self.rule_ids(self.validate_text("## T\n\na → b → c → d\n")))
        self.assertNotIn("AI_TONE", self.rule_ids(self.validate_text(
            "## T\n\na -> b -> c -> d -> e -> f\n\n:::html\n<!-- x --><!-- y --><!-- z --><!-- w -->\n<p>z</p>\n:::\n")))
        self.assertNotIn("AI_TONE", self.rule_ids(self.validate_text(
            "## T\n\n`a → b → c → d → e`\n")))

    def test_ai_tone_label_repeats_deck_wide(self):
        label = "\n\n**한 줄 정리**: 요점입니다.\n"
        self.write("01-a.md", FRONT + "## A" + label + "\n---\n## B" + label)
        self.write("02-b.md", FRONT + "## C" + label)
        hits = [f for f in self.validate(self.root) if f["rule"] == "AI_TONE"]
        self.assertEqual(1, len(hits), hits)
        self.assertEqual("WARNING", hits[0]["severity"])

        two = Path(tempfile.mkdtemp(prefix="remarp-copy-two-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(two, ignore_errors=True))
        (two / "01-a.md").write_text(FRONT + "## A" + label + "\n---\n## B" + label, encoding="utf-8")
        self.assertEqual([], [f for f in self.validate(two) if f["rule"] == "AI_TONE"])

    def test_ai_tone_note_cliche(self):
        src = "## T\n\n본문\n\n:::notes\n{timing: 1min}\n[요약]\n- 꼭 기억해 두세요.\n:::\n"
        self.assertIn(("WARNING", "AI_TONE"), self.rules(self.validate_text(src)))

    def test_copy_gates_do_not_block_build(self):
        source = self.write("talk.md", FRONT + "## Title\n\nA — B → c → d → e → f\n" + NOTES)
        result = subprocess.run([sys.executable, str(SCRIPT), "build", str(source)],
                                capture_output=True, text=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)

    def test_copy_gates_scan_columns_tabs_and_detail_titles(self):
        cases = (
            "## T\n\n:::left\nA \u2014 B\n:::\n\n:::right\nx\n:::\n",
            '## T\n\n:::tab "A"\nA \u2014 B\n:::\n',
            '## T\n\n[a]{detail=d}\n\n:::detail d "A \u2014 B"\nbody\n:::\n',
            '## T\n\n[a]{tip="A \u2014 B"}\n',
        )
        for src in cases:
            with self.subTest(src=src):
                self.assertIn("EM_DASH", self.rule_ids(self.validate_text(src)))
        arrows = "## T\n\n:::left\na \u2192 b \u2192 c\n:::\n\n:::right\nd \u2192 e \u2192 f\n:::\n"
        self.assertIn("AI_TONE", self.rule_ids(self.validate_text(arrows)))

    def test_stray_backtick_does_not_hide_later_paragraphs(self):
        src = "## T\n\nan unpaired ` backtick here\n\nlater A \u2014 B and `code` end\n"
        self.assertIn("EM_DASH", self.rule_ids(self.validate_text(src)))


if __name__ == "__main__":
    unittest.main()
