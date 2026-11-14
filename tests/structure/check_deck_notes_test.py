"""check_deck.py note lint: NOTE_OPERATING_INSTRUCTION and NOTE_MARK_IN_META (no browser)."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/scripts/check_deck.py"
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
        with tempfile.TemporaryDirectory(dir=str(Path.home() / ".tmp")) as d:
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
        with tempfile.TemporaryDirectory(dir=str(Path.home() / ".tmp")) as d:
            (Path(d) / "index.html").write_text(deck, encoding="utf-8")
            findings = []
            check_deck.check_file(Path(d), "index.html", set(), findings)
        self.assertIn((META, 1), {(f["rule"], f["slide"]) for f in findings})

    def test_rule_ids_registered(self):
        self.assertIn(OP, check_deck.RULE_IDS)
        self.assertIn(META, check_deck.RULE_IDS)


if __name__ == "__main__":
    unittest.main()
