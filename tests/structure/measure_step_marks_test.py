"""Browser tests for measure_deck STEP_MARKS (reactive-step-guidance Task 7).

Browser cases skip (exit 0, prints SKIPPED-BROWSER) without Playwright/Chromium.
"""
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RP = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation"
SCRIPT = RP / "scripts/measure_deck.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("measure_deck_step_marks", SCRIPT)
measure_deck = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = measure_deck
SPEC.loader.exec_module(measure_deck)

DECK = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Marks</title>
<link rel="stylesheet" href="./common/theme.css"></head><body>
<div class="slide-deck">%s</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/quiz-component.js"></script>
<script src="./common/presenter-view.js"></script>
<script>const deck = new SlideFramework({ sidebar: false, presenterNotes: %s });
%s</script>
</body></html>
"""


def slide(title, fragments=0):
    frags = "".join(f'<div class="fragment" data-fragment-index="{n}">item {n}</div>' for n in range(fragments))
    return (f'<div class="slide"><div class="slide-header"><h2>{title}</h2></div>'
            f'<div class="slide-body"><div class="card">{title}{frags}</div></div></div>')


def _have_playwright():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:  # pragma: no cover
        return False


class StepMarksTests(unittest.TestCase):
    def test_rule_is_documented(self):
        self.assertIn("STEP_MARKS", measure_deck.__doc__)

    def run_deck(self, slides, notes, script=""):
        if not _have_playwright():
            self.skipTest("playwright/chromium unavailable")
        tmp = Path(tempfile.mkdtemp(prefix="rp-marks-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        common = tmp / "common"
        common.mkdir()
        for f in (RP / "assets").iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (tmp / "index.html").write_text(
            DECK % ("".join(slides), json.dumps(notes, ensure_ascii=False), script), encoding="utf-8")
        findings = measure_deck.measure(tmp, ["index.html"], [(1920, 1080)], ["light"], 5, None)
        return [f for f in findings if f["rule"] == "STEP_MARKS"]

    def test_matching_marks_pass(self):
        hits = self.run_deck([slide("A", 2), slide("B")], {1: "말하기 ↓ 둘째 ↓ 끝"})
        self.assertEqual([], hits)

    def test_mismatch_warns(self):
        hits = self.run_deck([slide("A", 3), slide("B")], {1: "하나 ↓ 끝"})
        self.assertEqual(1, len(hits), hits)
        self.assertEqual(("WARN", 1), (hits[0]["severity"], hits[0]["slide"]))
        self.assertEqual('notes carry 1 "↓" but the slide takes 3 presses', hits[0]["message"])

    def test_marks_without_presses_warn(self):
        hits = self.run_deck([slide("A"), slide("B")], {1: "↓ ↓"})
        self.assertEqual(['notes carry 2 "↓" but the slide takes 0 presses'], [h["message"] for h in hits])

    def test_presses_without_marks_warn(self):
        hits = self.run_deck([slide("A", 2), slide("B")], {})
        self.assertEqual(['notes carry 0 "↓" but the slide takes 2 presses'], [h["message"] for h in hits])

    def test_object_note_uses_text(self):
        hits = self.run_deck([slide("A", 2), slide("B")], {1: {"text": "a ↓ b ↓ c", "timing": "1 min"}})
        self.assertEqual([], hits)

    def test_last_slide_skipped(self):
        hits = self.run_deck([slide("A"), slide("B", 2)], {2: "↓ ↓ ↓"})
        self.assertEqual([], hits)

    def test_action_without_state_counted(self):
        script = ("let n = 0; deck.registerSlideAction(0, { down: () => (++n <= 3) });")
        hits = self.run_deck([slide("A"), slide("B")], {1: "↓ ↓ ↓"}, script)
        self.assertEqual([], hits)
        hits = self.run_deck([slide("A"), slide("B")], {1: "↓"}, script)
        self.assertEqual(['notes carry 1 "↓" but the slide takes 3 presses'], [h["message"] for h in hits])

    def test_cap_reported(self):
        script = "deck.registerSlideAction(0, { down: () => true });"
        hits = self.run_deck([slide("A"), slide("B")], {}, script)
        self.assertEqual(1, len(hits), hits)
        self.assertIn("(stopped at the 40-press cap)", hits[0]["message"])
        self.assertIn("takes 40 presses", hits[0]["message"])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if any(reason == "playwright/chromium unavailable" for _, reason in result.skipped):
        print("SKIPPED-BROWSER")
    sys.exit(0 if result.wasSuccessful() else 1)
