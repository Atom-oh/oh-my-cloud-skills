"""Browser regression tests for measure_deck SENTENCE_RUNON (reactive-nav-detail Task 4).

Skips (exit 0, prints SKIPPED-ALL) without Playwright/Chromium.
"""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RP = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation"
SCRIPT = RP / "scripts/measure_deck.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("measure_deck_runon", SCRIPT)
measure_deck = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = measure_deck
SPEC.loader.exec_module(measure_deck)

RUNON_1 = ('Public-only 또는 Private-only 권장. "Public and Private"는 VPC 밖 노드에서 '
           'endpoint가 public IP로 해석되어 join이 실패할 수 있음')
RUNON_2 = ('SNAT_EXCLUDE_CIDRS는 기존 제외 범위와 모든 hybrid Pod CIDR의 합집합입니다. '
           'Auto Mode는 aws-node DaemonSet이 없고, serviceAccount.annotations는 1.0.2에서 무시됩니다.')
SPLIT = ('<div class="card-desc" style="width:560px"><div>Public-only 또는 Private-only 권장.</div>'
         '<div>"Public and Private"는 VPC 밖 노드에서 endpoint가 public IP로 해석되어 join이 실패할 수 있음</div></div>')
ONE_SENTENCE = ('<div class="card-desc" style="width:560px">한 문장으로만 길게 이어지는 설명이 여러 줄로 감싸지는 경우에는 '
                '문장 경계가 없으므로 경고가 나오면 안 되는데 이 문장은 일부러 세 줄 이상이 되도록 아주 길게 이어서 작성했습니다</div>')


def slide(title, body):
    return (f'<div class="slide"><div class="slide-header"><h2>{title}</h2></div>'
            f'<div class="slide-body"><div class="card">{body}</div></div></div>')


DECK = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>Runon</title>
<link rel="stylesheet" href="./common/theme.css"></head><body>
<div class="slide-deck">%s</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/quiz-component.js"></script>
<script src="./common/presenter-view.js"></script>
<script>const deck = new SlideFramework({ sidebar: false });</script>
</body></html>
"""


def _have_playwright():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:  # pragma: no cover
        return False


class SentenceRunonTests(unittest.TestCase):
    def test_prepare_hides_overlay(self):
        self.assertIn(".rp-overlay-ui", measure_deck._PREPARE_JS)
        self.assertIn(".rp-detail::after", measure_deck._PREPARE_JS)

    def test_runon_is_a_density_rule(self):
        self.assertIn("SENTENCE_RUNON", measure_deck.__doc__)

    def build(self, slides):
        tmp = Path(tempfile.mkdtemp(prefix="rp-runon-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        common = tmp / "common"
        common.mkdir()
        for f in (RP / "assets").iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (tmp / "index.html").write_text(DECK % "".join(slides), encoding="utf-8")
        return tmp

    def runon(self, slides, viewports=((1920, 1080),)):
        if not _have_playwright():
            self.skipTest("playwright/chromium unavailable")
        deck = self.build(slides)
        findings = measure_deck.measure(deck, ["index.html"], list(viewports), ["light"], 5, None)
        return [f for f in findings if f["rule"] == "SENTENCE_RUNON"]

    def test_runon_flags_two_sentences_in_one_block(self):
        hits = self.runon([
            slide("A", f'<div class="card-desc" style="width:560px">{RUNON_1}</div>'),
            slide("B", f'<div class="card-desc" style="width:560px">{RUNON_2}</div>'),
        ])
        self.assertEqual({1, 2}, {h["slide"] for h in hits}, hits)
        self.assertTrue(all(h["severity"] == "WARN" for h in hits))

    def test_runon_ignores_split_lines_and_single_sentence(self):
        self.assertEqual([], self.runon([slide("A", SPLIT), slide("B", ONE_SENTENCE)]))

    def test_runon_reported_once_across_viewports(self):
        hits = self.runon([slide("A", f'<div class="card-desc" style="width:560px">{RUNON_1}</div>')],
                          viewports=((1920, 1080), (1280, 720)))
        self.assertEqual(1, len(hits), hits)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and len(result.skipped) >= 3:
        print("SKIPPED-BROWSER")
    sys.exit(0 if result.wasSuccessful() else 1)
