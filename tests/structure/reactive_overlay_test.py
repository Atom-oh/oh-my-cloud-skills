"""Browser regression tests for the deck overlay: hover agenda, cmd-k search and detail layer.

Fixtures are hand-written HTML following the compiler DOM contract
(docs/superpowers/plans/2026-10-18-reactive-nav-detail.md, Task 2). Slide indices in
assertions are 0-based. Skips (exit 0, prints SKIPPED-ALL) without Playwright/Chromium.
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

XSS = '&lt;img src=x onerror=&quot;window.__xss=1&quot;&gt;'
LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" width="160" height="64">'
        '<rect width="160" height="64" fill="#888"/></svg>')

HEAD = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>Overlay fixture</title>
<link rel="stylesheet" href="./common/theme.css">
<link rel="stylesheet" href="./common/deck-overlay.css">
</head>
<body>
"""
SCRIPTS = """<script src="./common/animation-utils.js"></script>
<script src="./common/deck-overlay.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/presenter-view.js"></script>
<script>const deck = new SlideFramework({ %s });</script>
</body>
</html>
"""

SLIDES_A = f"""<div class="slide-deck">
  <div class="slide" data-block="01-a" data-block-title="개요">
    <div class="slide-header"><h2>Gateway 포트</h2></div>
    <div class="slide-body">
      <p>열어야 할 포트: <span class="rp-detail" tabindex="0" data-detail="vxlan" data-tip="hybrid 노드 간 VXLAN">UDP 8472</span>
      그리고 <span class="rp-detail" tabindex="0" data-tip="짧은 설명">tip term</span>
      그리고 <span class="rp-detail" data-detail="xss" data-tip="{XSS}">raw term</span></p>
    </div>
    <div class="rp-detail-store" hidden>
      <section data-detail-id="vxlan" data-title="UDP 8472가 필요한 이유" data-text="- direct routing, Gateway 모두 필요"><ul><li>direct routing, Gateway 모두 필요</li></ul></section>
      <section data-detail-id="xss" data-title="{XSS}" data-text="raw body"><p>raw body</p></section>
    </div>
  </div>
  <div class="slide" data-block="01-a" data-block-title="개요"><div class="slide-header"><h2>Second</h2></div><div class="slide-body"><p>two</p></div></div>
  <div class="slide" data-block="01-a" data-block-title="개요"><div class="slide-header"><h2>Third</h2></div><div class="slide-body"><p>three</p></div></div>
  <div class="slide" data-block="02-b" data-block-title="네트워킹"><div class="slide-header"><h2>Overlay</h2></div><div class="slide-body"><p>Cilium uses VXLAN encapsulation</p></div></div>
  <div class="slide" data-block="02-b" data-block-title="네트워킹"><div class="slide-header"><h2>Input slide</h2></div><div class="slide-body"><input id="fixture-input" type="text"></div></div>
  <div class="slide" data-block="02-b" data-block-title="네트워킹"><div class="slide-header"><h2>Notes slide</h2></div><div class="slide-body"><p>last</p></div>
    <template class="notes">notesonlyword</template></div>
</div>
"""

SLIDES_B = """<div class="slide-deck">
  <div class="slide"><div class="slide-header"><h2>One</h2></div><div class="slide-body"><p>a</p></div></div>
  <div class="slide"><div class="slide-header"><h2>Two</h2></div><div class="slide-body"><p>b</p></div></div>
  <div class="slide"><div class="slide-header"><h2>Three</h2></div><div class="slide-body"><p>c</p></div></div>
</div>
"""

OPTS_A = "sidebar: true, footer: 'Footer text', logoSrc: './logo.svg'"


def _load_playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except Exception:  # pragma: no cover
        return None


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class DeckOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-overlay-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        for f in ASSETS.iterdir():
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        (root / "logo.svg").write_text(LOGO, encoding="utf-8")
        (root / "a.html").write_text(HEAD + SLIDES_A + SCRIPTS % OPTS_A, encoding="utf-8")
        (root / "a-nofooter.html").write_text(
            HEAD + SLIDES_A + SCRIPTS % "sidebar: true, logoSrc: './logo.svg'", encoding="utf-8")
        (root / "b.html").write_text(HEAD + SLIDES_B + SCRIPTS % "sidebar: false", encoding="utf-8")
        handler = functools.partial(_Quiet, directory=str(root))
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}/"
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

    def open(self, name="a.html", **ctx_kwargs):
        self.ctx = self.browser.new_context(viewport={"width": 1600, "height": 900}, **ctx_kwargs)
        self.addCleanup(self.ctx.close)
        page = self.ctx.new_page()
        page.set_default_timeout(5000)
        page.goto(self.base + name, wait_until="networkidle")
        page.wait_for_timeout(300)
        return page

    # --- helpers ---------------------------------------------------------
    @staticmethod
    def active(page):
        return page.evaluate("() => deck.currentSlide")

    @staticmethod
    def has_body_class(page, cls):
        return page.evaluate(f"() => document.body.classList.contains('{cls}')")

    def open_search(self, page, query=None):
        page.keyboard.press("Meta+K")
        page.wait_for_timeout(100)
        if query is not None:
            page.keyboard.type(query)
            page.wait_for_timeout(150)

    # --- agenda ------------------------------------------------------------
    def test_agenda_opens_on_hover_and_jumps(self):
        page = self.open()
        page.hover("#rp-agenda-hotzone")
        page.wait_for_selector("#rp-agenda", state="visible")
        self.assertEqual(page.locator("#rp-agenda .rp-agenda-block").count(), 2)
        page.click('#rp-agenda .rp-agenda-row[data-goto="3"]')
        page.wait_for_timeout(300)
        self.assertEqual(self.active(page), 3)
        page.mouse.move(10, 450)
        page.wait_for_timeout(500)
        page.hover("#rp-agenda-hotzone")
        page.wait_for_selector("#rp-agenda", state="visible")
        row = page.locator('#rp-agenda .rp-agenda-row[data-goto="3"]')
        self.assertIn("is-current", row.get_attribute("class"))
        block = page.locator("#rp-agenda .rp-agenda-block").nth(1)
        self.assertIn("is-current-block", block.get_attribute("class"))

    def test_agenda_block_header_jumps_to_first_slide(self):
        page = self.open()
        page.hover("#rp-agenda-hotzone")
        page.wait_for_selector("#rp-agenda", state="visible")
        page.locator("#rp-agenda .rp-agenda-block-title").nth(1).click()
        page.wait_for_timeout(300)
        self.assertEqual(self.active(page), 3)

    def test_agenda_single_block_lists_slides(self):
        page = self.open("b.html")
        page.hover("#rp-agenda-hotzone")
        page.wait_for_selector("#rp-agenda", state="visible")
        self.assertEqual(page.locator("#rp-agenda .rp-agenda-row").count(), 3)

    # --- search ------------------------------------------------------------
    def test_search_cmd_k_finds_body_text(self):
        page = self.open()
        self.open_search(page, "vxlan")
        self.assertTrue(self.has_body_class(page, "rp-search-open"))
        first = page.locator("#rp-search-results .rp-search-row").first
        self.assertEqual(first.get_attribute("data-goto"), "3")
        page.keyboard.press("Enter")
        page.wait_for_timeout(300)
        self.assertEqual(self.active(page), 3)
        self.assertFalse(self.has_body_class(page, "rp-search-open"))

    def test_search_ctrl_k_and_slash_open(self):
        page = self.open()
        page.keyboard.press("Control+K")
        page.wait_for_timeout(100)
        self.assertTrue(self.has_body_class(page, "rp-search-open"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(100)
        self.assertFalse(self.has_body_class(page, "rp-search-open"))
        page.keyboard.press("/")
        page.wait_for_timeout(100)
        self.assertTrue(self.has_body_class(page, "rp-search-open"))

    def test_search_indexes_tips(self):
        page = self.open()
        self.open_search(page, "짧은 설명")
        rows = page.locator("#rp-search-results .rp-search-row")
        self.assertGreaterEqual(rows.count(), 1)
        self.assertEqual(rows.first.get_attribute("data-goto"), "0")

    def test_search_excludes_notes_and_clones(self):
        page = self.open()
        self.assertEqual(page.locator(".slide-sidebar").count(), 1)
        self.open_search(page, "notesonlyword")
        self.assertEqual(page.locator("#rp-search-results .rp-search-row").count(), 0)
        page.fill("#rp-search-input", "VXLAN encapsulation")
        page.wait_for_timeout(150)
        self.assertEqual(page.locator("#rp-search-results .rp-search-row").count(), 1)

    def test_search_ignores_typing_in_inputs(self):
        page = self.open()
        page.evaluate("() => deck.goTo(4)")
        page.wait_for_timeout(300)
        page.focus("#fixture-input")
        page.keyboard.type("/k")
        page.wait_for_timeout(150)
        self.assertFalse(self.has_body_class(page, "rp-search-open"))
        self.assertEqual(self.active(page), 4)
        page.keyboard.press("Escape")
        page.evaluate("() => document.activeElement && document.activeElement.blur()")
        self.open_search(page, "abc")
        page.keyboard.press("ArrowRight")
        page.keyboard.press(" ")
        page.wait_for_timeout(300)
        self.assertEqual(self.active(page), 4)
        self.assertTrue(self.has_body_class(page, "rp-search-open"))

    # --- tooltip / detail -----------------------------------------------------
    def test_tooltip_on_hover_tip_only(self):
        page = self.open()
        term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        term.hover()
        page.wait_for_selector("#rp-tooltip", state="visible")
        self.assertIn("짧은 설명", page.inner_text("#rp-tooltip"))
        term.click()
        page.wait_for_timeout(200)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))

    def test_icon_only_on_detail_terms(self):
        page = self.open()
        js = ("(sel) => getComputedStyle(document.querySelector(sel), '::after').content")
        self.assertNotIn(page.evaluate(js, '.slide-deck > .slide .rp-detail[data-detail="vxlan"]'), ("none", "normal", ""))
        self.assertIn(page.evaluate(js, '.slide-deck > .slide .rp-detail:not([data-detail])'), ("none", "normal", ""))

    def test_icon_static_from_first_paint(self):
        page = self.open()
        sel = '.slide-deck > .slide .rp-detail[data-detail="vxlan"]'
        before = page.evaluate(
            "(sel) => [document.querySelector('.slide.active').dataset.fitScale || '',"
            " JSON.stringify(document.querySelector(sel).getBoundingClientRect())]", sel)
        page.hover(sel)
        page.click(sel)
        page.wait_for_timeout(200)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        after = page.evaluate(
            "(sel) => [document.querySelector('.slide.active').dataset.fitScale || '',"
            " JSON.stringify(document.querySelector(sel).getBoundingClientRect())]", sel)
        self.assertEqual(before, after)

    def test_thumbnail_terms_inert(self):
        page = self.open()
        idx = page.evaluate(
            "() => Array.from(document.querySelectorAll('.slide-sidebar .rp-detail')).map(e => e.getAttribute('tabindex'))")
        self.assertTrue(idx)
        self.assertTrue(all(v == "-1" for v in idx), idx)

    def test_click_term_with_detail_opens_panel(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_selector("#rp-detail-panel", state="visible")
        self.assertTrue(self.has_body_class(page, "rp-detail-open"))
        text = page.inner_text("#rp-detail-panel")
        self.assertIn("UDP 8472가 필요한 이유", text)
        self.assertIn("direct routing, Gateway 모두 필요", text)

    def test_enter_on_focused_term_opens_panel(self):
        page = self.open()
        page.focus('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        self.assertTrue(self.has_body_class(page, "rp-detail-open"))

    def test_raw_html_term_becomes_focusable(self):
        page = self.open()
        self.assertEqual(
            page.get_attribute('.slide-deck > .slide .rp-detail[data-detail="xss"]', "tabindex"), "0")

    def test_panel_closes_on_slide_change(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(400)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))
        self.assertEqual(self.active(page), 1)

    def test_esc_closes_panel_and_search(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))
        self.open_search(page)
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        self.assertFalse(self.has_body_class(page, "rp-search-open"))

    def test_tooltip_and_panel_title_are_text(self):
        page = self.open()
        sel = '.slide-deck > .slide .rp-detail[data-detail="xss"]'
        page.hover(sel)
        page.wait_for_timeout(200)
        self.assertEqual(page.locator("#rp-tooltip img").count(), 0)
        page.click(sel)
        page.wait_for_timeout(300)
        self.assertEqual(page.locator("#rp-detail-panel img").count(), 0)
        self.assertIn("<img", page.inner_text("#rp-detail-panel"))
        self.assertIsNone(page.evaluate("() => window.__xss"))

    def test_touch_tap_toggles_tip(self):
        page = self.open(has_touch=True)
        sel = '.slide-deck > .slide .rp-detail:not([data-detail])'
        page.tap(sel)
        page.wait_for_timeout(200)
        self.assertTrue(page.is_visible("#rp-tooltip"))
        page.tap(sel)
        page.wait_for_timeout(200)
        self.assertFalse(page.is_visible("#rp-tooltip"))

    # --- overview / placement -------------------------------------------------
    def test_overlay_hidden_in_overview(self):
        page = self.open()
        page.keyboard.press("o")
        page.wait_for_timeout(400)
        self.assertFalse(page.is_visible("#rp-agenda-hotzone"))
        page.keyboard.press("Meta+K")
        page.wait_for_timeout(150)
        self.assertFalse(self.has_body_class(page, "rp-search-open"))

    def test_overlay_outside_slides(self):
        page = self.open()
        self.open_search(page, "x")
        self.assertEqual(page.locator(".slide .rp-overlay-ui").count(), 0)
        self.assertGreaterEqual(page.locator("body > .rp-overlay-ui").count(), 1)

    def _assert_hint_clear(self, page):
        rects = page.evaluate(
            "() => [document.querySelector('.nav-hint'), document.querySelector('.slide-logo')]"
            ".map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })")
        (hl, ht, hr, hb), (ll, lt, lr, lb) = rects
        overlap = hl < lr and ll < hr and ht < lb and lt < hb
        self.assertFalse(overlap, rects)

    def test_nav_hint_clear_of_logo(self):
        for name in ("a.html", "a-nofooter.html"):
            page = self.open(name)
            page.wait_for_function("() => { const l = document.querySelector('.slide-logo'); return l && l.complete; }")
            page.wait_for_timeout(200)
            self._assert_hint_clear(page)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and not result.testsRun - len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
