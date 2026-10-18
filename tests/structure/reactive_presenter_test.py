"""Browser regression tests for presenter-view preview fidelity (reactive-presentation).

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

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "plugins/aws-content-plugin/skills/reactive-presentation/assets"

LONG = "온프렘 라우터에 node별 prefix를 수동 등록하고 drift를 추적해야 합니다"
DECK = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Presenter fixture</title>
<link rel="stylesheet" href="./common/theme.css">
<link rel="stylesheet" href="./common/deck-overlay.css">
</head>
<body>
<div class="slide-deck preset-paper" data-fit="auto">
  <div class="slide"><div class="slide-header"><h2>First slide</h2></div>
    <div class="slide-body"><p>Intro text for the first slide.</p></div></div>
  <div class="slide theme-dark"><div class="slide-header"><h2>Routing choices</h2></div>
    <div class="slide-body"><table>
      <tr><th>Item</th><th>Static</th><th>BGP</th><th>Gateway</th></tr>
      <tr><td>Pod CIDR 도달 방법</td><td>{LONG}</td><td>{LONG}</td><td>{LONG}</td></tr>
      <tr><td>온프렘 라우터 변경</td><td>{LONG}</td><td>필요</td><td>{LONG}</td></tr>
      <tr><td>HA</td><td>{LONG}</td><td>{LONG}</td><td>짧음</td></tr>
    </table></div></div>
  <div class="slide"><div class="slide-header"><h2>Fragments</h2></div>
    <div class="slide-body"><p class="fragment" data-fragment-index="1">One</p>
      <p class="fragment" data-fragment-index="2">Two</p></div></div>
  <div class="slide"><div class="slide-header"><h2>Detail</h2></div>
    <div class="slide-body"><p>port <span class="rp-detail" tabindex="0" data-detail="d" data-tip="t">UDP 8472</span></p></div>
    <div class="rp-detail-store" hidden><section data-detail-id="d" data-title="T" data-text="x"><p>x</p></section></div></div>
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/deck-overlay.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>const deck = new SlideFramework({{ sidebar: false }});</script>
</body>
</html>
"""


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return sync_playwright
    except Exception:  # pragma: no cover - environment dependent
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class PresenterPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-presenter-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (root / "index.html").write_text(DECK, encoding="utf-8")
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
        self.page = self.ctx.new_page()
        self.page.set_default_timeout(5000)
        self.page.goto(self.url, wait_until="networkidle")
        self.page.wait_for_timeout(300)
        with self.ctx.expect_page() as info:
            self.page.keyboard.press("p")
        self.pv = info.value
        self.pv.set_viewport_size({"width": 1600, "height": 900})
        self.settle()

    def tearDown(self):
        self.ctx.close()

    def settle(self):
        self.pv.wait_for_timeout(500)
        self.page.evaluate("() => window.__pvScaleUpdate && window.__pvScaleUpdate()")
        self.pv.wait_for_timeout(150)

    def goto(self, index):
        self.page.evaluate(f"() => deck.goTo({index})")
        self.settle()

    def test_preview_uses_deck_canvas(self):
        size = self.pv.evaluate(
            "() => { const s = document.querySelector('#p-current .slide-scaler');"
            " return [s.offsetWidth, s.offsetHeight]; }")
        self.assertEqual(size, [1920, 1080])

    def test_preview_root_font_matches_deck(self):
        deck_root = self.page.evaluate("() => getComputedStyle(document.documentElement).fontSize")
        pv_root = self.pv.evaluate("() => getComputedStyle(document.documentElement).fontSize")
        self.assertEqual(deck_root, "24px")
        self.assertEqual(pv_root, deck_root)
        deck_h2 = self.page.evaluate("() => getComputedStyle(document.querySelector('.slide.active h2')).fontSize")
        pv_h2 = self.pv.evaluate("() => getComputedStyle(document.querySelector('#p-current .slide h2')).fontSize")
        self.assertEqual(pv_h2, deck_h2)

    def test_preview_font_family_matches_deck(self):
        deck_ff = self.page.evaluate("() => getComputedStyle(document.querySelector('.slide.active h2')).fontFamily")
        pv_ff = self.pv.evaluate("() => getComputedStyle(document.querySelector('#p-current .slide h2')).fontFamily")
        self.assertEqual(pv_ff, deck_ff)

    def test_preview_keeps_slide_and_deck_classes(self):
        self.goto(1)
        cls = self.pv.evaluate("() => document.querySelector('#p-current .slide').className")
        self.assertIn("theme-dark", cls)
        deck_cls = self.pv.evaluate("() => document.querySelector('#p-current .slide-deck').className")
        self.assertIn("preset-paper", deck_cls)
        fit = self.pv.evaluate("() => document.querySelector('#p-current .slide-deck').getAttribute('data-fit')")
        self.assertEqual(fit, "auto")
        self.assertEqual(self.pv.evaluate("() => document.documentElement.lang"), "en")

    def test_preview_table_layout_matches_deck(self):
        self.goto(1)
        js = ("(sel) => { const t = document.querySelector(sel); const h = t.getBoundingClientRect().height;"
              " return Array.from(t.querySelectorAll('tr')).map(r => r.getBoundingClientRect().height / h); }")
        deck_r = self.page.evaluate(js, ".slide.active table")
        pv_r = self.pv.evaluate(js, "#p-current .slide table")
        self.assertEqual(len(deck_r), len(pv_r))
        for d, p in zip(deck_r, pv_r):
            self.assertAlmostEqual(d, p, delta=0.02)

    def test_next_preview_reveals_fragments(self):
        self.goto(1)
        counts = self.pv.evaluate(
            "() => { const f = document.querySelectorAll('#p-next .fragment');"
            " return [f.length, Array.from(f).filter(e => e.classList.contains('visible')).length]; }")
        self.assertEqual(counts[0], 2)
        self.assertEqual(counts[1], 2)

    def test_current_preview_keeps_reveal_state(self):
        self.goto(2)
        self.page.keyboard.press("ArrowRight")
        self.pv.wait_for_timeout(500)
        shown = self.pv.evaluate("() => document.querySelectorAll('#p-current .fragment.visible').length")
        self.assertEqual(shown, 1)

    def test_presenter_chrome_size_unchanged(self):
        fs = self.pv.evaluate("() => getComputedStyle(document.querySelector('.presenter-timer')).fontSize")
        self.assertEqual(fs, "24px")

    def test_next_preview_after_going_back_is_visible(self):
        self.goto(1)
        self.page.keyboard.press("ArrowLeft")
        self.settle()
        cls = self.pv.evaluate("() => document.querySelector('#p-next .slide').className")
        for bad in ("leaving", "entering", "transition-"):
            self.assertNotIn(bad, cls)
        self.assertEqual(self.pv.evaluate("() => getComputedStyle(document.querySelector('#p-next .slide')).opacity"), "1")

    def test_preview_hides_detail_affordances(self):
        self.goto(3)
        res = self.pv.evaluate(
            "() => { const t = document.querySelector('#p-current .rp-detail'); const a = getComputedStyle(t, '::after');"
            " return [getComputedStyle(t).textDecorationLine, a.visibility, a.content]; }")
        self.assertEqual(res[0], "none")
        self.assertTrue(res[1] == "hidden" or res[2] in ("none", "normal"), res)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and not result.testsRun - len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
