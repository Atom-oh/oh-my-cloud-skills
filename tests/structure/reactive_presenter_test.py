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
<link rel="stylesheet" href="./common/deck-detail.css">
<link rel="stylesheet" href="./common/deck-nav.css">
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
<script src="./common/deck-detail.js"></script>
<script src="./common/deck-nav.js"></script>
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

    def assert_slide_sync(self, index):
        self.assertEqual(self.page.evaluate("() => deck.currentSlide"), index)
        self.page.wait_for_function("() => !deck.transitioning", timeout=5000)
        self.pv.wait_for_function(
            "index => document.getElementById('p-counter').textContent === `${index + 1} / 4`",
            arg=index, timeout=5000)

    def assert_fragment_sync(self, count):
        self.assert_slide_sync(2)
        self.assertEqual(self.page.locator(".slide.active .fragment.visible").count(), count)
        self.pv.wait_for_function(
            "count => document.querySelectorAll('#p-current .fragment.visible').length === count",
            arg=count, timeout=5000)

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

    def test_presenter_vertical_keys_reveal_reverse_and_leave_at_start(self):
        self.goto(2)
        self.assert_fragment_sync(0)
        for key, count in (("ArrowDown", 1), ("ArrowDown", 2),
                           ("ArrowUp", 1), ("ArrowUp", 0)):
            self.pv.keyboard.press(key)
            self.assert_fragment_sync(count)
        self.pv.keyboard.press("ArrowUp")
        self.assert_slide_sync(1)

    def test_presenter_vertical_keys_leave_only_after_last_fragment(self):
        self.goto(2)
        for count in (1, 2):
            self.pv.keyboard.press("ArrowDown")
            self.assert_fragment_sync(count)
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(3)

    def test_presenter_vertical_keys_dispatch_canvas_steps(self):
        self.goto(1)
        self.page.evaluate("""() => {
            window.canvasCalls = [];
            window.canvasConsumes = true;
            deck.slides[1].__canvasStep = direction => {
                window.canvasCalls.push(direction);
                return window.canvasConsumes;
            };
        }""")
        for key in ("ArrowDown", "ArrowUp"):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
        self.assertEqual(self.page.evaluate("() => window.canvasCalls"), ["next", "prev"])
        self.page.evaluate("() => { window.canvasConsumes = false; }")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(2)
        self.assertEqual(self.page.evaluate("() => window.canvasCalls"), ["next", "prev", "next"])

    def test_presenter_slide_actions_take_precedence_and_allow_fallback(self):
        self.goto(1)
        self.page.evaluate("""() => {
            window.actionCalls = [];
            window.actionConsumes = true;
            deck.slides[1].__canvasStep = () => {
                window.actionCalls.push('canvas');
                return true;
            };
            deck.registerSlideAction(1, {
                down: () => {
                    window.actionCalls.push('down');
                    return window.actionConsumes ? undefined : false;
                },
                up: () => {
                    window.actionCalls.push('up');
                    return window.actionConsumes;
                }
            });
        }""")
        for key in ("ArrowDown", "ArrowUp"):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
        self.assertEqual(self.page.evaluate("() => window.actionCalls"), ["down", "up"])
        self.page.evaluate("() => { window.actionConsumes = false; }")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(2)
        self.goto(1)
        self.pv.keyboard.press("ArrowUp")
        self.assert_slide_sync(0)
        self.assertEqual(self.page.evaluate("() => window.actionCalls"), ["down", "up", "down", "up"])

    def test_presenter_vertical_keys_refresh_inline_style_tabs(self):
        self.goto(1)
        self.page.evaluate("""() => {
            const body = deck.slides[1].querySelector('.slide-body');
            body.innerHTML = '<div class="tab-bar"><button class="tab-btn">First</button>'
                + '<button class="tab-btn">Second</button></div>'
                + '<p data-tab-panel="0">First tab content</p>'
                + '<p data-tab-panel="1">Second tab content</p>';
            const buttons = body.querySelectorAll('.tab-btn');
            const panels = body.querySelectorAll('[data-tab-panel]');
            const select = index => {
                buttons.forEach((button, i) => button.style.background = i === index ? 'var(--accent)' : 'transparent');
                panels.forEach((panel, i) => panel.style.display = i === index ? 'block' : 'none');
            };
            buttons.forEach((button, index) => button.onclick = () => select(index));
            select(0);
            deck.presenterView.updatePresenterView();
        }""")
        for key, selected in (("ArrowDown", 1), ("ArrowUp", 0)):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
            for page, root in ((self.page, ".slide.active"), (self.pv, "#p-current")):
                page.wait_for_function("""([root, selected]) => {
                    const panels = document.querySelectorAll(root + ' [data-tab-panel]');
                    return panels.length === 2 && Array.from(panels).every(
                        (panel, i) => panel.style.display === (i === selected ? 'block' : 'none'));
                }""", arg=[root, selected], timeout=5000)

    def test_presenter_vertical_keys_cycle_compare_and_refresh_preview(self):
        self.goto(1)
        self.page.evaluate("""() => {
            const body = deck.slides[1].querySelector('.slide-body');
            body.innerHTML = '<div class="compare-toggle"><button class="compare-btn active">Before</button>'
                + '<button class="compare-btn">After</button></div><p data-compare-content>Before details</p>';
            const buttons = body.querySelectorAll('.compare-btn');
            buttons.forEach(button => button.onclick = () => {
                buttons.forEach(other => other.classList.toggle('active', other === button));
                body.querySelector('[data-compare-content]').textContent = button.textContent + ' details';
            });
            deck.presenterView.updatePresenterView();
        }""")
        for key, label in (("ArrowDown", "After"), ("ArrowUp", "Before")):
            self.pv.keyboard.press(key)
            self.assert_slide_sync(1)
            for page, root in ((self.page, ".slide.active"), (self.pv, "#p-current")):
                page.wait_for_function("""([root, label]) => {
                    const active = document.querySelector(root + ' .compare-btn.active');
                    const details = document.querySelector(root + ' [data-compare-content]');
                    return active.textContent === label && details.textContent === label + ' details';
                }""", arg=[root, label], timeout=5000)

    def test_presenter_respects_remapped_navigation_keys(self):
        self.goto(2)
        self.page.evaluate("() => { deck.keyMappings.j = 'down'; deck.keyMappings.k = 'up'; }")
        self.pv.keyboard.press("j")
        self.assert_fragment_sync(1)
        self.pv.keyboard.press("k")
        self.assert_fragment_sync(0)
        self.page.evaluate("() => { deck.keyMappings.ArrowDown = 'prev'; }")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(1)

    def test_presenter_step_closes_main_search_and_reveals_fragment(self):
        self.goto(2)
        self.page.keyboard.press("Control+K")
        self.page.wait_for_function("() => document.body.classList.contains('rp-search-open')")
        self.pv.keyboard.press("ArrowDown")
        self.assert_fragment_sync(1)
        self.assertFalse(self.page.evaluate("() => document.body.classList.contains('rp-search-open')"))

    def test_presenter_step_closes_main_detail_and_runs_slide_action(self):
        self.goto(3)
        self.page.evaluate("""() => {
            deck.registerSlideAction(3, {
                down: () => { deck.slides[3].querySelector('h2').textContent = 'Detail advanced'; }
            });
        }""")
        self.page.click('.slide.active .rp-detail')
        self.page.wait_for_function("() => document.body.classList.contains('rp-detail-open')")
        self.pv.keyboard.press("ArrowDown")
        self.assert_slide_sync(3)
        self.assertFalse(self.page.evaluate("() => document.body.classList.contains('rp-detail-open')"))
        self.assertEqual(self.page.locator('.slide.active h2').text_content(), 'Detail advanced')
        self.pv.wait_for_function(
            "() => document.querySelector('#p-current h2').textContent === 'Detail advanced'", timeout=5000)

    def test_presenter_right_space_and_left_preserve_fragments(self):
        self.goto(2)
        for key, count in (("ArrowRight", 1), ("Space", 2),
                           ("ArrowLeft", 1), ("ArrowLeft", 0)):
            self.pv.keyboard.press(key)
            self.assert_fragment_sync(count)

    def test_presenter_editable_controls_do_not_navigate(self):
        self.goto(2)
        self.pv.evaluate("""() => {
            const controls = document.createElement('div');
            controls.innerHTML = '<input id="keyboard-input">'
                + '<textarea id="keyboard-textarea"></textarea>'
                + '<select id="keyboard-select"><option>One</option><option>Two</option></select>'
                + '<div id="keyboard-editable" contenteditable="true">Editable notes</div>';
            document.body.appendChild(controls);
        }""")
        for selector in ("#keyboard-input", "#keyboard-textarea", "#keyboard-select", "#keyboard-editable"):
            with self.subTest(control=selector):
                self.pv.focus(selector)
                for key in ("ArrowDown", "ArrowUp", "ArrowRight", "ArrowLeft", "Space"):
                    self.pv.keyboard.press(key)
                    self.assert_fragment_sync(0)

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
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
