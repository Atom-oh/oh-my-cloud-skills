"""Browser regressions for the presenter step cue (reactive-presentation).

Skips (exit 0) when Playwright for Python or its Chromium is unavailable; the TAP wrapper
reports that as a SKIP so a missing browser is never mistaken for a pass.
"""
import functools
import http.server
import shutil
import socketserver
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/assets"

DECK = """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="UTF-8">
<title>Step cue fixture</title>
<link rel="stylesheet" href="./common/theme.css">
<link rel="stylesheet" href="./common/deck-pen.css">
</head>
<body>
<div class="slide-deck">
  <div class="slide" data-remarp-id="s1"><div class="slide-header"><h2>Action</h2></div>
    <div class="slide-body"><p>action</p></div></div>
  <div class="slide" data-remarp-id="s2"><div class="slide-header"><h2>Plain</h2></div>
    <div class="slide-body"><p>plain</p></div></div>
  <div class="slide" data-remarp-id="s3"><div class="slide-header"><h2>Fragments</h2></div>
    <div class="slide-body"><p class="fragment" data-fragment-index="1">a</p><p class="fragment" data-fragment-index="2">b</p><p class="fragment" data-fragment-index="3">c</p></div></div>
  <div class="slide" data-remarp-id="s4"><div class="slide-header"><h2>Stateless</h2></div>
    <div class="slide-body"><p>stateless</p></div></div>
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/deck-pen.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>
const deck = new SlideFramework({ sidebar: false });
let n = 0;
deck.registerSlideAction(0, {
  down: () => (n < 2 ? (n++, true) : false),
  up: () => (n > 0 ? (n--, true) : false),
  state: () => ({ cur: n, total: 2 }),
});
deck.registerSlideAction(3, { down: () => true, up: () => true });
</script>
</body>
</html>
"""


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:  # pragma: no cover
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class _Base(unittest.TestCase):
    LANG = "ko"

    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-step-cue-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (root / "index.html").write_text(DECK % {"lang": cls.LANG}, encoding="utf-8")
        handler = functools.partial(_Quiet, directory=str(root))
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.httpd.server_address[1]}/index.html"
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as exc:  # pragma: no cover
            cls.pw.stop()
            cls.httpd.shutdown()
            raise unittest.SkipTest(f"chromium unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.httpd.shutdown()
        cls.tmp.cleanup()

    def setUp(self):
        self.ctx = self.browser.new_context(viewport={"width": 1600, "height": 900})
        self.addCleanup(self.ctx.close)
        self.errors = []
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(5000)
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.goto(self.url, wait_until="networkidle")
        self.page.wait_for_timeout(300)
        self.open_presenter()

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def open_presenter(self):
        with self.ctx.expect_page() as info:
            self.page.keyboard.press("n")
        self.pv = info.value
        self.pv.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.pv.set_viewport_size({"width": 1600, "height": 900})
        self.pv.wait_for_function(
            "() => document.getElementById('p-counter').textContent.startsWith('1 /')", timeout=5000)

    def goto(self, index):
        self.page.evaluate(f"() => deck.goTo({index})")
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        self.pv.wait_for_function(
            "i => document.getElementById('p-counter').textContent.startsWith(`${i + 1} /`)",
            arg=index, timeout=5000)

    def cue(self):
        return self.pv.evaluate("() => document.getElementById('p-step-cue').textContent")

    def wait_cue(self, text):
        self.pv.wait_for_function(
            "t => document.getElementById('p-step-cue') && document.getElementById('p-step-cue').textContent === t",
            arg=text, timeout=5000)


class StepCueKoTests(_Base):
    def test_cue_for_action_slide_updates_on_down(self):
        self.wait_cue("↓ 다음 단계 있음 (지금 0/2)")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "data-more"), "1")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "role"), "status")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("↓ 다음 단계 있음 (지금 1/2)")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("✓ 마지막 단계 (2/2), 누르면 다음 슬라이드")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "data-more"), "0")

    def test_cue_none(self):
        self.goto(1)
        self.wait_cue("✓ 단계 없음, 누르면 다음 슬라이드")
        self.assertEqual(self.pv.get_attribute("#p-step-cue", "data-more"), "0")

    def test_cue_fragment_variant(self):
        self.goto(2)
        self.wait_cue("→ 다음 항목 있음 (0/3)")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("→ 다음 항목 있음 (1/3)")
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("✓ 마지막 단계 (3/3), 누르면 다음 슬라이드")

    def test_cue_action_without_state(self):
        self.goto(3)
        self.wait_cue("↓ 이 장에 단계가 있음")

    def test_cue_updates_when_main_window_pressed(self):
        self.page.bring_to_front()
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("↓ 다음 단계 있음 (지금 1/2)")

    def test_cue_survives_state_throwing(self):
        self.page.evaluate("() => deck.registerSlideAction(0, {down: () => true, up: () => true, state: () => { throw new Error('x'); }})")
        self.page.evaluate("() => deck.presenterView.updatePresenterView()")
        self.wait_cue("↓ 이 장에 단계가 있음")

    def test_no_duplicate_box_after_reopen(self):
        self.pv.close()
        self.page.wait_for_timeout(200)
        self.open_presenter()
        self.assertEqual(self.pv.evaluate("() => document.querySelectorAll('#p-step-cue').length"), 1)
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("↓ 다음 단계 있음 (지금 1/2)")

    def test_no_errors_after_close(self):
        self.pv.close()
        self.page.wait_for_timeout(200)
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("ArrowDown")
        self.page.wait_for_timeout(500)
        self.assertEqual(self.errors, [])


class StepCueEnTests(_Base):
    LANG = "en"

    def test_cue_english_when_lang_en(self):
        self.wait_cue("↓ more steps (now 0/2)")
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("ArrowDown")
        self.wait_cue("✓ last step (2/2), the next press moves on")
        self.goto(1)
        self.wait_cue("✓ no steps, the next press moves on")
        self.goto(2)
        self.wait_cue("→ more items (0/3)")
        self.goto(3)
        self.wait_cue("↓ this slide has steps")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
