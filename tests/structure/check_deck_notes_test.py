"""check_deck.py note lint: NOTE_OPERATING_INSTRUCTION and NOTE_MARK_IN_META (no browser)."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/check_deck.py"
COMPILER = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("check_deck_notes", SCRIPT)
check_deck = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_deck
SPEC.loader.exec_module(check_deck)

OP = "NOTE_OPERATING_INSTRUCTION"
META = "NOTE_MARK_IN_META"


def rules(text):
    return [r for r, _ in check_deck.lint_note_text(text)]


class NoteLintTest(unittest.TestCase):
    def test_flags_korean_operating_phrases(self):
        for phrase in ("아래 화살표로 넘겨 볼게요", "눌러 볼게요", "버튼을 누르면 됩니다",
                       "장면을 누를 때마다 바뀝니다", "화살표를 눌러서 진행합니다"):
            with self.subTest(phrase=phrase):
                self.assertIn(OP, rules("요점을 설명합니다. " + phrase))

    def test_flags_english_operating_phrases(self):
        for phrase in ("Press the down arrow now", "click the next button",
                       "PRESS DOWN to continue"):
            with self.subTest(phrase=phrase):
                self.assertIn(OP, rules("Intro. " + phrase))

    def test_plain_script_is_clean(self):
        self.assertEqual(rules("먼저 구조를 봅니다. ↓ 다음으로 비용을 비교합니다. ↓ 마지막입니다."), [])

    def test_ordinary_sentences_stay_clean(self):
        for s in ("아래 표에서 비용을 비교합니다.",
                  "화살표는 데이터 흐름의 방향을 나타냅니다.",
                  "이 버튼은 배포를 시작하는 역할을 합니다.",
                  "장면이 바뀔 때마다 요약합니다.",
                  "The arrow shows traffic direction and the button starts a deploy.",
                  "Press releases are not covered; the pressure is on latency.",
                  "Scroll down to see the table."):
            with self.subTest(s=s):
                self.assertEqual(rules(s), [])

    def test_mark_in_summary_line(self):
        for line, kind in (("[요약] 요점↓", "[요약]"), ("[출처] a↓", "[출처]"),
                           ("[약어] b↓", "[약어]"), ("{timing: 2}↓", "{")):
            with self.subTest(line=line):
                got = check_deck.lint_note_text("{timing: 1}\n" + line + "\n대본입니다.")
                meta = [m for r, m in got if r == META]
                self.assertEqual(len(meta), 1)
                self.assertIn(kind, meta[0])

    def test_mark_inside_braces_span(self):
        self.assertIn(META, rules("{timing: 2 ↓ min}\n대본"))

    def test_mark_in_script_line_not_meta(self):
        self.assertEqual(rules("[요약]\n요점\n대본입니다.↓ 다음 문장입니다."), [])

    def test_deck_level_warning_has_slide_number(self):
        deck = (
            '<html><body><div class="slide"><h1>One</h1>'
            '<template class="notes">\n[요약]\n요점\n정상 대본입니다. ↓ 다음.\n</template></div>'
            '<div class="slide"><h1>Two</h1>'
            '<template class="notes">\n[요약] 요점↓\n아래 화살표로 넘깁니다.\n</template></div>'
            '</body></html>')
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text(deck, encoding="utf-8")
            findings = []
            check_deck.check_file(Path(d), "index.html", set(), findings)
        got = {(f["rule"], f["slide"], f["severity"]) for f in findings
               if f["rule"] in (OP, META)}
        self.assertEqual(got, {(OP, 2, "WARN"), (META, 2, "WARN")})

    def test_presenter_notes_object_keeps_line_structure(self):
        deck = (
            '<html><body><div class="slide"><h1>One</h1></div>'
            '<script>const presenterNotes = {\n'
            '  1: "[요약] 요점↓\\n대본입니다.",\n};</script></body></html>')
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text(deck, encoding="utf-8")
            findings = []
            check_deck.check_file(Path(d), "index.html", set(), findings)
        self.assertIn((META, 1), {(f["rule"], f["slide"]) for f in findings})

    def _deck_findings(self, note_line):
        deck = ('<html><body><div class="slide"><h1>One</h1></div>'
                '<script>const presenterNotes = {\n' + note_line + '\n};</script></body></html>')
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text(deck, encoding="utf-8")
            findings = []
            check_deck.check_file(Path(d), "index.html", set(), findings)
        return {f["rule"] for f in findings if f["rule"] in (OP, META)}

    def test_object_form_clean_arrow(self):
        self.assertEqual(self._deck_findings(
            '  1: {text: "구조를 봅니다. ↓ 다음입니다.", timing: 2},'), set())

    def test_object_form_meta_via_escape(self):
        self.assertEqual(self._deck_findings(
            '  1: {text: "[요약] 요점↓\\n대본입니다.", timing: 2},'), {META})
        self.assertEqual(self._deck_findings(
            "  1: {notes: '[요약] 요점↓\\n대본입니다.'},"), {META})

    def test_object_form_operating_phrase(self):
        self.assertEqual(self._deck_findings(
            '  1: {text: "아래 화살표로 넘깁니다.", timing: 2},'), {OP})

    def test_brace_marker_in_plain_string_note(self):
        self.assertEqual(self._deck_findings(
            '  1: "{timing: 2}↓\\n대본입니다.",'), {META})

    def test_compiled_deck_is_linted(self):
        # remarp_to_slides.py writes notes with json.dumps (ensure_ascii): the built HTML
        # holds \u2193 and \uXXXX Korean, which the lint must decode before matching.
        src = ("---\nremarp: true\nlang: ko\n---\n"
               "## 하나\n\n본문입니다.\n\n:::notes\n{timing: 1min}\n[요약] 요점입니다↓\n"
               "대본입니다. 아래 화살표로 넘기겠습니다.\n:::\n\n---\n\n"
               "## 둘\n\n본문입니다.\n\n:::notes\n{timing: 1min}\n대본입니다.\n:::\n")
        with tempfile.TemporaryDirectory(prefix="rp-lint-built-") as d:
            source = Path(d) / "talk.md"
            source.write_text(src, encoding="utf-8")
            result = subprocess.run([sys.executable, str(COMPILER), "build", str(source)],
                                    capture_output=True, text=True, cwd=d,
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            built = list(Path(d).rglob("*.html"))
            self.assertEqual(1, len(built), built)
            html = built[0].read_text(encoding="utf-8")
            self.assertIn("\\u2193", html)  # the escaped form this test is about
            findings = []
            check_deck.check_file(built[0].parent, built[0].name, set(), findings)
        got = {(f["rule"], f["slide"]) for f in findings if f["rule"] in (OP, META)}
        self.assertEqual(got, {(OP, 1), (META, 1)})

    def test_js_string_decoding(self):
        dec = check_deck._decode_js_string
        self.assertEqual(dec('"\\uc694\\uc57d\\u2193\\n\\"q\\" \\\\ x"'), '요약↓\n"q" \\ x')
        self.assertEqual(dec('"\\ud83d\\ude00"'), '\U0001F600')  # surrogate pair
        self.assertEqual(dec("'it\\'s \\u2193'"), "it's ↓")
        self.assertEqual(dec("`a\\nb`"), "a\nb")
        self.assertEqual(dec('"\\x41\\t"'), "A\t")

    def test_escaped_length_counts_unchanged(self):
        # SHORT_NOTES keeps measuring the escaped source text (pre-existing behavior).
        note = "\\uac00" * 30  # 30 Korean chars, 180 escaped chars
        deck = ('<html><body><div class="slide"><h1>One</h1></div>'
                '<script>const presenterNotes = {\n  1: "' + note + '",\n};</script></body></html>')
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text(deck, encoding="utf-8")
            findings = []
            check_deck.check_file(Path(d), "index.html", set(), findings)
        self.assertNotIn("SHORT_NOTES", {f["rule"] for f in findings})

    def test_rule_ids_registered(self):
        self.assertIn(OP, check_deck.RULE_IDS)
        self.assertIn(META, check_deck.RULE_IDS)


if __name__ == "__main__":
    unittest.main()
