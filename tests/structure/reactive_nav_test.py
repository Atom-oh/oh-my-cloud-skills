"""Browser regressions for deck nav; skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture


class DeckNavTests(DeckOverlayFixture):
    overlay_modules = ("detail", "nav")

    def _assert_hint_clear(self, page):
        rects = page.evaluate(
            "() => [document.querySelector('.nav-hint'), document.querySelector('.slide-logo')]"
            ".map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })")
        (hl, ht, hr, hb), (ll, lt, lr, lb) = rects
        overlap = hl < lr and ll < hr and ht < lb and lt < hb
        self.assertFalse(overlap, rects)

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

    def test_nav_hint_clear_of_logo(self):
        for name in ("a.html", "a-nofooter.html"):
            page = self.open(name)
            page.wait_for_function("() => { const l = document.querySelector('.slide-logo'); return l && l.complete; }")
            page.wait_for_timeout(200)
            self._assert_hint_clear(page)

    def test_search_ignores_ime_composition_keys(self):
        page = self.open()
        self.open_search(page, "vx")
        before = page.evaluate("() => document.querySelector('#rp-search-results .is-selected, #rp-search-results [aria-selected=true]')?.dataset.goto ?? null")
        for key in ("ArrowDown", "Enter"):
            page.evaluate("(k) => document.getElementById('rp-search-input').dispatchEvent("
                          "new KeyboardEvent('keydown', {key: k, isComposing: true, bubbles: true, cancelable: true}))", key)
        page.wait_for_timeout(150)
        self.assertTrue(self.has_body_class(page, "rp-search-open"))
        self.assertEqual(self.active(page), 0)
        after = page.evaluate("() => document.querySelector('#rp-search-results .is-selected, #rp-search-results [aria-selected=true]')?.dataset.goto ?? null")
        self.assertEqual(before, after)

    def test_search_skips_style_text_and_indexes_detail_titles(self):
        page = self.open()
        self.open_search(page, "styleonlytoken")
        self.assertEqual(page.locator("#rp-search-results .rp-search-row").count(), 0)
        page.fill("#rp-search-input", "필요한 이유")
        page.wait_for_timeout(150)
        self.assertEqual(page.locator("#rp-search-results .rp-search-row").first.get_attribute("data-goto"), "0")

    def test_search_snippet_separates_blocks(self):
        page = self.open()
        self.open_search(page, "encapsulation")
        text = page.inner_text("#rp-search-results .rp-search-row")
        self.assertNotIn("OverlayCilium", text.replace("\n", ""))

    def test_search_keeps_space_between_inline_words(self):
        page = self.open()
        self.open_search(page, "Amazon EKS")
        self.assertEqual(page.locator("#rp-search-results .rp-search-row").first.get_attribute("data-goto"), "3")

    def test_hotzone_hidden_from_assistive_tech(self):
        page = self.open()
        self.assertEqual(page.get_attribute("#rp-agenda-hotzone", "aria-hidden"), "true")

    def test_panel_close_button_not_covered_by_hotzone(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        hit = page.evaluate(
            "() => { const b = document.querySelector('#rp-detail-panel button'); const r = b.getBoundingClientRect();"
            " const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return b === e || b.contains(e); }")
        self.assertTrue(hit)

    def test_close_click_does_not_reopen_agenda(self):
        page = self.open()
        page.click('.slide-deck > .slide .rp-detail[data-detail="vxlan"]')
        page.wait_for_timeout(200)
        page.click("#rp-detail-panel button")
        page.wait_for_timeout(500)
        self.assertFalse(page.is_visible("#rp-agenda"))

    def test_search_combobox_semantics(self):
        page = self.open()
        self.open_search(page, "a")
        roles = page.evaluate("() => Array.from(document.querySelectorAll('#rp-search-results .rp-search-row')).map(r => r.getAttribute('role'))")
        self.assertTrue(roles)
        self.assertTrue(all(r == "option" for r in roles), roles)
        self.assertEqual(page.get_attribute("#rp-search-input", "aria-controls"), "rp-search-results")
        first = page.get_attribute("#rp-search-input", "aria-activedescendant")
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(100)
        second = page.get_attribute("#rp-search-input", "aria-activedescendant")
        self.assertTrue(second)
        self.assertNotEqual(first, second)
        self.assertIsNotNone(page.query_selector("#" + second))

    def test_search_from_panel_returns_focus_to_term(self):
        page = self.open()
        sel = '.slide-deck > .slide .rp-detail[data-detail="vxlan"]'
        page.focus(sel)
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        page.keyboard.press("Control+K")
        page.wait_for_timeout(150)
        page.keyboard.press("Escape")
        page.wait_for_timeout(150)
        self.assertTrue(page.evaluate("() => { const a = document.activeElement; return !!a && a.offsetParent !== null; }"))

    def test_search_rows_keep_focus_on_combobox(self):
        page = self.open()
        self.open_search(page, "e")
        idx = page.evaluate("() => Array.from(document.querySelectorAll('#rp-search-results .rp-search-row')).map(r => r.getAttribute('tabindex'))")
        self.assertTrue(idx)
        self.assertTrue(all(v == "-1" for v in idx), idx)

    def test_search_joins_inline_split_words(self):
        page = self.open()
        self.open_search(page, "PodDisruptionBudget")
        self.assertEqual(page.locator("#rp-search-results .rp-search-row").first.get_attribute("data-goto"), "2")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
