"""Browser regressions for deck detail; skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture


class DeckDetailTests(DeckOverlayFixture):
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

    def test_space_on_term_and_close_button_keeps_slide(self):
        page = self.open()
        active = "() => Array.from(document.querySelectorAll('.slide-deck > .slide')).findIndex(s => s.classList.contains('active'))"
        start = page.evaluate(active)
        page.focus('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.keyboard.press(" ")
        page.wait_for_timeout(200)
        self.assertTrue(self.has_body_class(page, "rp-detail-open"))
        self.assertEqual(start, page.evaluate(active))
        page.focus("#rp-detail-panel button")
        page.keyboard.press(" ")
        page.wait_for_timeout(200)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))
        self.assertEqual(start, page.evaluate(active))

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

    def test_hidden_fragment_term_inert(self):
        page = self.open()
        page.evaluate("() => deck.goTo(1)")
        page.wait_for_timeout(300)
        sel = '.slide-deck > .slide .rp-detail[data-detail="hid"]'
        self.assertEqual(page.get_attribute(sel, "tabindex"), "-1")
        page.evaluate("(s) => document.querySelector(s).focus()", sel)
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        self.assertEqual(page.get_attribute(sel, "tabindex"), "0")

    def test_panel_closes_on_fragment_reveal(self):
        page = self.open()
        page.evaluate("() => deck.goTo(1)")
        page.wait_for_timeout(300)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        page.click('.slide-deck > .slide .rp-detail[data-detail="hid"]')
        page.wait_for_timeout(200)
        self.assertTrue(self.has_body_class(page, "rp-detail-open"))
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))

    def test_detail_term_aria_and_focus(self):
        page = self.open()
        sel = '.slide-deck > .slide .rp-detail[data-detail="vxlan"]'
        self.assertEqual(page.get_attribute(sel, "role"), "button")
        self.assertEqual(page.get_attribute(sel, "aria-haspopup"), "dialog")
        page.focus(sel)
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        self.assertEqual(page.get_attribute(sel, "aria-expanded"), "true")
        self.assertTrue(page.evaluate("() => document.getElementById('rp-detail-panel').contains(document.activeElement)"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        self.assertTrue(page.evaluate("(s) => document.activeElement === document.querySelector(s)", sel))

    def test_overlay_korean_keep_all(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        self.assertEqual(page.evaluate("() => getComputedStyle(document.querySelector('#rp-detail-panel li')).wordBreak"), "keep-all")

    def test_panel_table_is_styled(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        pad = page.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#rp-detail-panel td')).paddingLeft)")
        self.assertGreater(pad, 0)

    def test_overview_clears_open_panel(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        page.keyboard.press("o")
        page.wait_for_timeout(300)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))

    def test_overlay_scales_with_deck(self):
        sizes = []
        for vp in ({"width": 1920, "height": 1080}, {"width": 3840, "height": 2160}):
            page = self.open()
            page.set_viewport_size(vp)
            page.wait_for_timeout(400)
            page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
            page.wait_for_timeout(200)
            sizes.append(page.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#rp-detail-panel li')).fontSize)"))
        self.assertGreater(sizes[1], sizes[0] * 1.5, sizes)

    def test_no_stray_tooltip_after_panel_close(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        page.mouse.move(800, 800)
        page.click("#rp-detail-panel button")
        page.wait_for_timeout(300)
        self.assertFalse(page.is_visible("#rp-tooltip"))
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        page.mouse.move(800, 800)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        self.assertFalse(page.is_visible("#rp-tooltip"))

    def test_tooltip_scales_with_deck(self):
        sizes = []
        for vp in ({"width": 1920, "height": 1080}, {"width": 3840, "height": 2160}):
            page = self.open()
            page.set_viewport_size(vp)
            page.wait_for_timeout(400)
            page.hover('.slide-deck > .slide .rp-detail:not([data-detail])')
            page.wait_for_timeout(200)
            sizes.append(page.evaluate("() => parseFloat(getComputedStyle(document.getElementById('rp-tooltip')).fontSize)"))
        self.assertGreater(sizes[1], sizes[0] * 1.5, sizes)

    def test_overview_term_enter_does_not_open_panel(self):
        page = self.open()
        page.keyboard.press("o")
        page.wait_for_timeout(300)
        page.evaluate("() => document.querySelector('.slide-deck > .slide .rp-detail[data-detail=vxlan]').focus()")
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        self.assertFalse(self.has_body_class(page, "rp-detail-open"))

    def test_fade_out_fragment_term_is_reversed(self):
        page = self.open()
        page.evaluate("() => deck.goTo(2)")
        page.wait_for_timeout(300)
        sel = '.slide-deck > .slide .rp-detail[data-detail="fo"]'
        self.assertEqual(page.get_attribute(sel, "tabindex"), "0")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        self.assertEqual(page.get_attribute(sel, "tabindex"), "-1")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
