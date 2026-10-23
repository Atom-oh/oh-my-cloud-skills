"""Browser regressions for deck detail; skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture


class DeckDetailTests(DeckOverlayFixture):
    def test_tooltip_hover_crosses_gap_and_leaves_content(self):
        page = self.open("detail-contexts.html")
        term = page.locator(".slide-deck figcaption .rp-detail")
        term.hover()
        tooltip = page.locator("#rp-tooltip")
        tooltip.wait_for(state="visible")
        anchor, box = term.bounding_box(), tooltip.bounding_box()
        x = (max(anchor["x"], box["x"]) + min(
            anchor["x"] + anchor["width"], box["x"] + box["width"])) / 2
        if box["y"] < anchor["y"]:
            y = (box["y"] + box["height"] + anchor["y"]) / 2
        else:
            y = (anchor["y"] + anchor["height"] + box["y"]) / 2
        page.mouse.move(x, y)
        page.wait_for_timeout(400)
        self.assertTrue(tooltip.is_visible(), "The pointer can pause in the trigger-to-tooltip gap")
        tooltip.hover()
        page.wait_for_timeout(400)
        self.assertTrue(tooltip.is_visible(), "Long explanations remain visible while hovered")
        page.mouse.move(1500, 800)
        tooltip.wait_for(state="hidden")
        self.assertEqual(tooltip.get_attribute("aria-hidden"), "true")
        self.assertIsNone(term.get_attribute("aria-describedby"))

    def test_reentering_trigger_cancels_pending_tooltip_close(self):
        page = self.open()
        term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        term.hover()
        page.mouse.move(800, 800)
        term.hover()
        page.wait_for_timeout(400)
        self.assertTrue(page.is_visible("#rp-tooltip"))

    def test_tooltip_focus_and_hover_hold_independently(self):
        page = self.open()
        term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        term.focus()
        term.hover()
        page.mouse.move(800, 800)
        page.wait_for_timeout(400)
        self.assertTrue(page.is_visible("#rp-tooltip"), "Focus retains the tooltip after pointer exit")
        page.locator("#rp-tooltip").hover()
        term.evaluate("el => el.blur()")
        page.wait_for_timeout(400)
        self.assertTrue(page.is_visible("#rp-tooltip"), "Hover retains the tooltip after focus exit")
        page.mouse.move(800, 800)
        page.wait_for_selector("#rp-tooltip", state="hidden")

    def test_new_focus_replaces_tooltip_with_pending_close(self):
        page = self.open()
        old = page.locator('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        new = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        old.hover()
        page.mouse.move(800, 800)
        new.focus()
        page.wait_for_timeout(400)
        self.assertTrue(page.is_visible("#rp-tooltip"))
        self.assertEqual(page.inner_text("#rp-tooltip"), new.get_attribute("data-tip"))
        self.assertIsNone(old.get_attribute("aria-describedby"))
        new.evaluate("el => el.blur()")
        page.wait_for_selector("#rp-tooltip", state="hidden")

    def test_escape_dismisses_tooltip_before_deck_shortcuts(self):
        for activation in ("hover", "focus"):
            with self.subTest(activation=activation):
                page = self.open()
                term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
                page.evaluate("""() => {
                    window.__escapeActions = 0;
                    const original = deck.getKeyAction.bind(deck);
                    deck.getKeyAction = key => {
                        if (key === 'Escape') window.__escapeActions++;
                        return original(key);
                    };
                }""")
                term.evaluate("el => el.setAttribute('aria-describedby', 'existing-description')")
                getattr(term, activation)()
                page.wait_for_selector("#rp-tooltip", state="visible")
                page.keyboard.press("Escape")
                page.wait_for_selector("#rp-tooltip", state="hidden")
                page.wait_for_timeout(300)
                self.assertFalse(page.is_visible("#rp-tooltip"))
                self.assertEqual(term.get_attribute("aria-describedby"), "existing-description")
                self.assertEqual(page.evaluate("() => window.__escapeActions"), 0)
                self.assertEqual(self.active(page), 0)
                if activation == "focus":
                    self.assertTrue(term.evaluate("el => el === document.activeElement"))
                page.keyboard.press("Escape")
                self.assertEqual(page.evaluate("() => window.__escapeActions"), 1)
                page.mouse.move(800, 800)
                term.hover()
                page.wait_for_selector("#rp-tooltip", state="visible")

    def test_tooltip_clears_after_slide_or_overview_change(self):
        for action in ("deck.goTo(1)", "deck.toggleOverview()"):
            with self.subTest(action=action):
                page = self.open()
                term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
                term.hover()
                page.mouse.move(800, 800)
                page.evaluate("() => " + action)
                page.wait_for_selector("#rp-tooltip", state="hidden")
                page.wait_for_timeout(400)
                self.assertIsNone(term.get_attribute("aria-describedby"))
                self.assertFalse(page.is_visible("#rp-tooltip"))

    def test_dismissed_tooltip_can_reopen_after_pointer_leaves_viewport(self):
        page = self.open()
        term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        term.hover()
        page.keyboard.press("Escape")
        page.wait_for_selector("#rp-tooltip", state="hidden")
        page.mouse.move(-10, -10)
        term.hover()
        page.wait_for_selector("#rp-tooltip", state="visible")

    def test_chart_caption_and_quotation_use_authored_explanations(self):
        page = self.open("detail-contexts.html")
        for context in ("figcaption", "blockquote"):
            with self.subTest(context=context):
                term = page.locator(f".slide-deck {context} .rp-detail")
                self.assertEqual(term.get_attribute("tabindex"), "0")
                for activation in ("hover", "focus"):
                    getattr(term, activation)()
                    page.wait_for_selector("#rp-tooltip", state="visible")
                    self.assertEqual(page.inner_text("#rp-tooltip"), term.get_attribute("data-tip"))
                    self.assertFalse(self.has_body_class(page, "rp-detail-open"))
                    page.keyboard.press("Escape")
                    page.wait_for_selector("#rp-tooltip", state="hidden")
                term.evaluate("el => el.blur()")

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
        page.hover(sel)
        page.wait_for_selector("#rp-tooltip", state="visible")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(300)
        self.assertEqual(page.get_attribute(sel, "tabindex"), "-1")
        self.assertFalse(page.is_visible("#rp-tooltip"))


class DeckDetailNavigationTests(DeckOverlayFixture):
    overlay_modules = ("detail", "nav")

    def test_search_dismisses_tooltip_with_focus_and_hover_on_different_terms(self):
        page = self.open()
        hovered = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        focused = page.locator('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        box = hovered.bounding_box()
        # PointerEvent retains subpixels that compatibility MouseEvent discards.
        page.mouse.move(int(box["x"] + box["width"] / 2) + .25,
                        int(box["y"] + box["height"] / 2) + .75)
        focused.focus()
        page.wait_for_selector("#rp-tooltip", state="visible")
        self.assertEqual(page.inner_text("#rp-tooltip"), focused.get_attribute("data-tip"))
        self.open_search(page)
        page.wait_for_selector("#rp-tooltip", state="hidden")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        self.assertTrue(focused.evaluate("el => el === document.activeElement"))
        self.assertFalse(page.is_visible("#rp-tooltip"))
        page.mouse.move(800, 800)
        hovered.hover()
        page.wait_for_selector("#rp-tooltip", state="visible")
        self.assertEqual(page.inner_text("#rp-tooltip"), hovered.get_attribute("data-tip"))

    def test_search_dismisses_hovered_tooltip(self):
        page = self.open()
        term = page.locator('.slide-deck > .slide .rp-detail:not([data-detail])')
        term.hover()
        page.wait_for_selector("#rp-tooltip", state="visible")
        self.open_search(page)
        page.wait_for_selector("#rp-tooltip", state="hidden")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        self.assertFalse(page.is_visible("#rp-tooltip"))
        self.assertFalse(self.has_body_class(page, "rp-search-open"))
        self.assertIsNone(term.get_attribute("aria-describedby"))
        page.mouse.move(800, 800)
        term.hover()
        page.wait_for_selector("#rp-tooltip", state="visible")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
