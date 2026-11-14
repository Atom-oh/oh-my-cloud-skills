"""Browser tests for deck.getStepInfo; skips without Playwright/Chromium."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture


def _slide(body):
    return ('<div class="slide"><div class="slide-header"><h2>S</h2></div>'
            f'<div class="slide-body">{body}</div></div>')


TAB_CLICK = ("this.parentNode.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));"
             "this.classList.add('active')")
TABS = ('<div class="tab-bar">' + "".join(
    f'<button class="tab-btn{" active" if i == 0 else ""}" onclick="{TAB_CLICK}">T{i}</button>'
    for i in range(3)) + "</div>")
CMP_CLICK = ("this.parentNode.querySelectorAll('.compare-btn').forEach(b=>b.classList.remove('active'));"
             "this.classList.add('active')")


def _compare(active):
    return '<div class="compare-toggle">' + "".join(
        f'<button class="compare-btn{" active" if i == active else ""}" onclick="{CMP_CLICK}">C{i}</button>'
        for i in range(3)) + "</div>"


FRAG = '<p class="fragment"{attr}>f</p>'

SLIDES = [
    _slide("<p>plain</p>"),                                                        # 0 none
    _slide("<p>action</p>"),                                                       # 1 action state 1/3
    _slide("<p>action</p>"),                                                       # 2 action state 3/3
    _slide("<p>action</p>"),                                                       # 3 action no state
    _slide("<p>action</p>"),                                                       # 4 state throws
    _slide("".join(FRAG.format(attr=f' data-fragment-index="{i}"') for i in (1, 1, 2))),  # 5
    _slide(FRAG.format(attr="") * 3),                                              # 6 no index
    _slide(TABS + FRAG.format(attr="") * 2),                                       # 7 tabs + frags
    _slide("<p>action</p>" + FRAG.format(attr="") * 2),                            # 8 action hides frags
    _slide(FRAG.format(attr="") * 2),                                              # 9 other slide
    _slide(TABS),                                                                  # 10 tabs only
    _slide(_compare(-1)),                                                          # 11 compare, none active
    _slide(_compare(1)),                                                           # 12 compare, middle active
]
HTML = '<div class="slide-deck">\n' + "\n".join(SLIDES) + "\n</div>\n"


class StepInfoTests(DeckOverlayFixture):
    overlay_modules = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.root / "s.html").write_text(
            cls.page_head + HTML + cls.page_scripts % "sidebar: false", encoding="utf-8")

    def info(self, page, i=None):
        arg = "" if i is None else str(i)
        return page.evaluate(f"() => deck.getStepInfo({arg})")

    def goto(self, page, i):
        page.evaluate(f"() => deck.goTo({i})")
        page.wait_for_timeout(450)

    def test_no_steps(self):
        page = self.open("s.html")
        self.assertEqual(self.info(page), {"kind": "none", "cur": None, "total": None, "more": False})

    def test_action_with_state(self):
        page = self.open("s.html")
        page.evaluate("() => deck.registerSlideAction(1, {down: () => true, up: () => true, state: () => ({cur: 1, total: 3})})")
        page.evaluate("() => deck.registerSlideAction(2, {down: () => true, up: () => true, state: () => ({cur: 3, total: 3})})")
        self.assertEqual(self.info(page, 1), {"kind": "action", "cur": 1, "total": 3, "more": True})
        self.assertEqual(self.info(page, 2), {"kind": "action", "cur": 3, "total": 3, "more": False})

    def test_action_without_state(self):
        page = self.open("s.html")
        page.evaluate("() => deck.registerSlideAction(3, {down: () => true, up: () => true})")
        self.assertEqual(self.info(page, 3), {"kind": "action", "cur": None, "total": None, "more": True})

    def test_action_state_throwing(self):
        page = self.open("s.html")
        page.evaluate("() => deck.registerSlideAction(4, {down: () => true, up: () => true, state: () => { throw new Error('x'); }})")
        self.assertEqual(self.info(page, 4), {"kind": "action", "cur": None, "total": None, "more": True})

    def test_action_state_invalid_values(self):
        page = self.open("s.html")
        page.evaluate("() => deck.registerSlideAction(4, {down: () => true, up: () => true, state: () => ({cur: NaN, total: 0})})")
        self.assertEqual(self.info(page, 4), {"kind": "action", "cur": None, "total": None, "more": True})

    def test_fragments_group_by_index(self):
        page = self.open("s.html")
        self.goto(page, 5)
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 0, "total": 2, "more": True})
        page.evaluate("() => deck.revealNextFragment()")
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 1, "total": 2, "more": True})
        page.evaluate("() => deck.revealNextFragment()")
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 2, "total": 2, "more": False})
        self.goto(page, 6)
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 0, "total": 1, "more": True})

    def test_tabs_then_fragments(self):
        page = self.open("s.html")
        self.goto(page, 7)
        self.assertEqual(self.info(page), {"kind": "interactive", "cur": 0, "total": 2, "more": True})
        page.evaluate("() => deck.handleNavigationAction('down')")
        self.assertEqual(self.info(page), {"kind": "interactive", "cur": 1, "total": 2, "more": True})
        page.evaluate("() => deck.handleNavigationAction('down')")
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 0, "total": 1, "more": True})

    def presses_until_exhausted(self, page):
        """Real Down presses while getStepInfo still reports the interactive phase."""
        return page.evaluate("""() => {
          let n = 0;
          while (deck.getStepInfo().kind === 'interactive' && n < 20) { deck.handleNavigationAction('down'); n++; }
          return n;
        }""")

    def test_compare_no_active_matches_real_presses(self):
        page = self.open("s.html")
        self.goto(page, 11)
        info = self.info(page)
        self.assertEqual(info, {"kind": "interactive", "cur": 0, "total": 3, "more": True})
        self.assertEqual(self.presses_until_exhausted(page), info["total"] - info["cur"])
        self.assertEqual(self.active(page), 11)
        self.assertEqual(self.info(page), {"kind": "none", "cur": None, "total": None, "more": False})

    def test_compare_middle_active_matches_real_presses(self):
        page = self.open("s.html")
        self.goto(page, 12)
        info = self.info(page)
        self.assertEqual(info, {"kind": "interactive", "cur": 1, "total": 2, "more": True})
        self.assertEqual(self.presses_until_exhausted(page), info["total"] - info["cur"])
        self.assertEqual(self.active(page), 12)

    def test_tabs_exhausted_then_fragments_hidden_then_revealed(self):
        page = self.open("s.html")
        self.goto(page, 7)
        vis = "() => document.querySelectorAll('.slide')[7].querySelectorAll('.fragment.visible').length"
        self.assertEqual(self.presses_until_exhausted(page), 2)
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 0, "total": 1, "more": True})
        self.assertEqual(page.evaluate(vis), 0)
        page.evaluate("() => deck.handleNavigationAction('down')")
        self.assertEqual(page.evaluate(vis), 2)
        self.assertEqual(self.info(page), {"kind": "fragment", "cur": 1, "total": 1, "more": False})

    def test_tabs_only_exhausted(self):
        page = self.open("s.html")
        self.goto(page, 10)
        page.evaluate("() => { deck.handleNavigationAction('down'); deck.handleNavigationAction('down'); }")
        self.assertEqual(self.info(page), {"kind": "none", "cur": None, "total": None, "more": False})

    def test_action_hides_fragments(self):
        page = self.open("s.html")
        page.evaluate("() => deck.registerSlideAction(8, {down: () => true, up: () => true})")
        self.goto(page, 8)
        self.assertEqual(self.info(page)["kind"], "action")

    def test_other_slide(self):
        page = self.open("s.html")
        self.assertEqual(self.info(page, 9), {"kind": "fragment", "cur": 0, "total": 1, "more": True})
        self.assertEqual(self.active(page), 0)
        self.assertEqual(page.evaluate("() => document.querySelectorAll('.fragment.visible').length"), 0)

    def test_canvas_step_legacy(self):
        page = self.open("s.html")
        page.evaluate("() => { deck.slides[0].__canvasStep = () => true; }")
        self.assertEqual(self.info(page), {"kind": "interactive", "cur": None, "total": None, "more": True})


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
