"""Browser regressions for hidden slides (@hidden / H toggle); skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture


def _slides(hidden):
    parts = []
    for i in range(5):
        attr = ' data-hidden="true"' if i in hidden else ""
        parts.append(
            f'<div class="slide" data-remarp-id="s{i + 1}"{attr}>'
            f'<div class="slide-header"><h2>S{i + 1}</h2></div>'
            f'<div class="slide-body"><p>body {i + 1}</p></div></div>')
    return '<div class="slide-deck">\n' + "\n".join(parts) + "\n</div>\n"


class HiddenSlideTests(DeckOverlayFixture):
    overlay_modules = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = "sidebar: true"
        (cls.root / "h.html").write_text(
            cls.page_head + _slides({1, 2}) + cls.page_scripts % opts, encoding="utf-8")
        (cls.root / "h-first.html").write_text(
            cls.page_head + _slides({0}) + cls.page_scripts % opts, encoding="utf-8")
        (cls.root / "h-last.html").write_text(
            cls.page_head + _slides({4}) + cls.page_scripts % opts, encoding="utf-8")

    def press(self, page, key):
        page.keyboard.press(key)
        page.wait_for_timeout(450)  # slide transition lock is 350ms

    def test_next_and_prev_skip_hidden(self):
        page = self.open("h.html")
        self.assertEqual(self.active(page), 0)
        self.press(page, "ArrowRight")
        self.assertEqual(self.active(page), 3)
        self.press(page, "ArrowLeft")
        self.assertEqual(self.active(page), 0)

    def test_goto_reaches_hidden_and_next_leaves_it(self):
        page = self.open("h.html")
        page.evaluate("() => deck.goTo(1)")
        page.wait_for_timeout(450)
        self.assertEqual(self.active(page), 1)
        self.press(page, "ArrowRight")
        self.assertEqual(self.active(page), 3)

    def test_hash_can_open_hidden_slide(self):
        page = self.open("h.html#2")
        self.assertEqual(self.active(page), 1)

    def test_first_slide_hidden_opens_on_first_visible(self):
        page = self.open("h-first.html")
        self.assertEqual(self.active(page), 1)
        self.press(page, "Home")
        self.assertEqual(self.active(page), 1)

    def test_end_goes_to_last_visible(self):
        page = self.open("h-last.html")
        self.press(page, "End")
        self.assertEqual(self.active(page), 3)
        self.press(page, "ArrowRight")  # nothing visible ahead: stay
        self.assertEqual(self.active(page), 3)

    def test_h_toggles_and_persists_across_reload(self):
        page = self.open("h.html")
        self.press(page, "h")  # hide slide 0
        self.assertTrue(page.evaluate("() => deck.isHidden(0)"))
        self.assertTrue(page.evaluate(
            "() => document.querySelector('.sidebar-thumb[data-index=\"0\"]').classList.contains('is-skipped')"))
        page.evaluate("() => deck.goTo(3)")
        page.wait_for_timeout(450)
        self.press(page, "ArrowLeft")
        self.assertEqual(self.active(page), 3)  # slide 0 is hidden too: nothing visible earlier, stay
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        self.assertTrue(page.evaluate("() => deck.isHidden(0)"))

    def test_h_unhides_authored_hidden_slide(self):
        page = self.open("h.html")
        page.evaluate("() => deck.goTo(1)")
        page.wait_for_timeout(450)
        self.press(page, "H")
        self.assertFalse(page.evaluate("() => deck.isHidden(1)"))
        self.assertEqual(page.evaluate("() => JSON.stringify(deck.hiddenOverrides)"), '{"s2":false}')
        self.press(page, "ArrowLeft")
        self.assertEqual(self.active(page), 0)
        self.press(page, "ArrowRight")
        self.assertEqual(self.active(page), 1)

    def test_sidebar_eye_toggles_without_navigating(self):
        page = self.open("h.html")
        eye = page.locator('.sidebar-thumb[data-index="0"] .sidebar-thumb-hide')
        self.assertEqual(eye.get_attribute("aria-pressed"), "false")
        page.hover('.sidebar-thumb[data-index="0"]')
        eye.click()
        page.wait_for_timeout(450)
        self.assertTrue(page.evaluate("() => deck.isHidden(0)"))
        self.assertEqual(eye.get_attribute("aria-pressed"), "true")
        self.assertEqual(self.active(page), 0)  # click did not jump to another slide
        # authored-hidden slide shows the "show" state and can be unhidden
        eye1 = page.locator('.sidebar-thumb[data-index="1"] .sidebar-thumb-hide')
        self.assertEqual(eye1.get_attribute("aria-pressed"), "true")
        eye1.click()
        self.assertFalse(page.evaluate("() => deck.isHidden(1)"))
        self.assertEqual(eye1.get_attribute("aria-pressed"), "false")

    def test_h_ignored_while_typing(self):
        page = self.open("h.html")
        page.evaluate("() => { const i = document.createElement('input'); i.id = 'x'; document.body.appendChild(i); i.focus(); }")
        page.keyboard.type("h")
        self.assertFalse(page.evaluate("() => deck.isHidden(0)"))


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
