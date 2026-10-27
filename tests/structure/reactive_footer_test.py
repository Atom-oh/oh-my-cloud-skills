"""Browser regression: the footer text follows the logo width; deck overrides still win."""
import sys
import unittest

sys.dont_write_bytecode = True

from reactive_overlay_fixture import DeckOverlayFixture, SLIDES_B

LOGO_WIDE = ('<svg xmlns="http://www.w3.org/2000/svg" width="240" height="64">'
             '<rect width="240" height="64" fill="#888"/></svg>')
LOGO_NARROW = ('<svg xmlns="http://www.w3.org/2000/svg" width="106" height="64">'
               '<rect width="106" height="64" fill="#888"/></svg>')

SLIDES_SWAP = """<div class="slide-deck">
  <div class="slide theme-light"><div class="slide-header"><h2>Light</h2></div><div class="slide-body"><p>a</p></div></div>
  <div class="slide theme-dark"><div class="slide-header"><h2>Dark</h2></div><div class="slide-body"><p>b</p></div></div>
</div>
"""

METRICS = """() => {
  const f = document.querySelector('.slide-footer');
  const l = document.querySelector('.slide-logo');
  return { footerLeft: f.offsetLeft, logoLeft: l ? l.offsetLeft : null,
           logoRight: l ? l.offsetLeft + l.offsetWidth : null,
           prop: f.style.getPropertyValue('--rp-footer-left') };
}"""


class DeckFooterTests(DeckOverlayFixture):
    overlay_modules = ()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        r = cls.root
        (r / "logo-narrow.svg").write_text(LOGO_NARROW, encoding="utf-8")
        (r / "logo-wide.svg").write_text(LOGO_WIDE, encoding="utf-8")
        (r / "override.css").write_text(".slide-footer { left: 200px; }\n", encoding="utf-8")

        def page(name, opts, slides=SLIDES_B, extra_css=False):
            head = cls.page_head
            if extra_css:
                head = head.replace("</head>", '<link rel="stylesheet" href="./override.css">\n</head>')
            (r / name).write_text(head + slides + cls.page_scripts % opts, encoding="utf-8")

        page("f-narrow.html", "footer: 'Footer text', logoSrc: './logo-narrow.svg'")
        page("f-wide.html", "footer: 'Footer text', logoSrc: './logo-wide.svg'")
        page("f-nologo.html", "footer: 'Footer text'")
        page("f-override.html", "footer: 'Footer text', logoSrc: './logo-wide.svg'", extra_css=True)
        page("f-swap.html", "footer: 'Footer text', logoSrc: './logo-narrow.svg', "
             "logoDarkSrc: './logo-wide.svg'", slides=SLIDES_SWAP)

    def metrics(self, page):
        return page.evaluate(METRICS)

    def test_footer_follows_logo_width_and_override_still_wins(self):
        for name, width in (("f-narrow.html", 53), ("f-wide.html", 120)):
            m = self.metrics(self.open(name))
            self.assertGreaterEqual(m["footerLeft"] - m["logoRight"], 12, (name, m))
            self.assertEqual(m["logoRight"] - m["logoLeft"], width, (name, m))
        m = self.metrics(self.open("f-nologo.html"))
        self.assertEqual(m["footerLeft"], 96, m)
        self.assertEqual(m["prop"], "", m)
        m = self.metrics(self.open("f-override.html"))
        self.assertEqual(m["footerLeft"], 200, m)

    def test_footer_recomputed_after_logo_swap(self):
        page = self.open("f-swap.html")
        before = self.metrics(page)
        self.assertGreaterEqual(before["footerLeft"] - before["logoRight"], 12, before)
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        after = self.metrics(page)
        self.assertGreater(after["logoRight"], before["logoRight"], (before, after))
        self.assertGreaterEqual(after["footerLeft"] - after["logoRight"], 12, (before, after))


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    if result.skipped and result.testsRun <= len(result.skipped):
        print("SKIPPED-ALL")
    sys.exit(0 if result.wasSuccessful() else 1)
