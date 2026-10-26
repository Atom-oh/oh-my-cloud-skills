"""Shared HTML and browser fixture for optional deck overlay modules."""
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
<link rel="stylesheet" href="./common/deck-detail.css">
<link rel="stylesheet" href="./common/deck-nav.css">
<link rel="stylesheet" href="./common/deck-pen.css">
</head>
<body>
"""
SCRIPTS = """<script src="./common/animation-utils.js"></script>
<script src="./common/deck-overlay.js"></script>
<script src="./common/deck-detail.js"></script>
<script src="./common/deck-nav.js"></script>
<script src="./common/deck-pen.js"></script>
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
      <section data-detail-id="vxlan" data-title="UDP 8472가 필요한 이유" data-text="- direct routing, Gateway 모두 필요"><ul><li>direct routing, Gateway 모두 필요</li></ul><table><tr><th>모드</th><th>필요</th></tr><tr><td>Gateway</td><td>예</td></tr></table></section>
      <section data-detail-id="xss" data-title="{XSS}" data-text="raw body"><p>raw body</p></section>
    </div>
  </div>
  <div class="slide" data-block="01-a" data-block-title="개요"><div class="slide-header"><h2>Second</h2></div><div class="slide-body"><p>two</p><p class="fragment" data-fragment-index="1">hidden <span class="rp-detail" tabindex="0" data-detail="hid" data-tip="숨은 팁">secret term</span></p><p class="fragment" data-fragment-index="2">later</p></div><div class="rp-detail-store" hidden><section data-detail-id="hid" data-title="숨은 상세" data-text="hidden body"><p>hidden body</p></section></div></div>
  <div class="slide" data-block="01-a" data-block-title="개요"><style>.styleonlytoken {{ color: red; }}</style><div class="slide-header"><h2>Third</h2></div><div class="slide-body"><p>three</p><p>PDB: Pod<wbr>Disruption<wbr>Budget</p><p class="fragment fade-out" data-fragment-index="1"><span class="rp-detail" tabindex="0" data-detail="fo" data-tip="fo tip">fade term</span></p></div><div class="rp-detail-store" hidden><section data-detail-id="fo" data-title="Fade" data-text="fade body"><p>fade body</p></section></div></div>
  <div class="slide" data-block="02-b" data-block-title="네트워킹"><div class="slide-header"><h2>Overlay</h2></div><div class="slide-body"><p>Cilium uses VXLAN encapsulation</p><p><b>Amazon</b> <b>EKS</b> hybrid</p><p>Karpenter<br>NodePool</p></div></div>
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

SLIDES_DETAIL_CONTEXTS = """<div class="slide-deck">
  <div class="slide"><div class="slide-header"><h2>Explain the evidence</h2></div>
    <div class="slide-body">
      <figure>
        <svg role="img" aria-label="Synthetic response times of 80 and 40 milliseconds" width="240" height="100" viewBox="0 0 240 100">
          <rect x="30" y="20" width="60" height="80" fill="currentColor"/>
          <rect x="150" y="60" width="60" height="40" fill="currentColor"/>
        </svg>
        <figcaption>Illustrative response time (synthetic data): <span class="rp-detail" data-tip="These illustrative bars compare synthetic median response times before and after caching. The lower value represents a faster typical response in this example; it does not describe tail latency or a real benchmark.">50% lower median</span></figcaption>
      </figure>
      <blockquote><p>“<span class="rp-detail" data-tip="This illustrative quotation asks readers to verify a change with evidence. The chart uses synthetic medians to demonstrate the interaction; it is not evidence of a production improvement.">Measure before you conclude.</span>”</p><footer>Illustrative quotation written for this fixture</footer></blockquote>
    </div>
  </div>
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


class DeckOverlayFixture(unittest.TestCase):
    overlay_modules = ("detail",)

    @classmethod
    def setUpClass(cls):
        sync_playwright = _load_playwright()
        if sync_playwright is None:
            raise unittest.SkipTest("playwright for Python is not installed")
        cls.tmp = tempfile.TemporaryDirectory(prefix="rp-overlay-")
        root = Path(cls.tmp.name)
        common = root / "common"
        common.mkdir()
        head, scripts = HEAD, SCRIPTS
        for module in ("detail", "nav", "pen"):
            if module not in cls.overlay_modules:
                head = head.replace(f'<link rel="stylesheet" href="./common/deck-{module}.css">\n', "")
                scripts = scripts.replace(f'<script src="./common/deck-{module}.js"></script>\n', "")
        for f in ASSETS.iterdir():
            if f.stem in ("deck-detail", "deck-nav", "deck-pen") and f.stem[5:] not in cls.overlay_modules:
                continue
            if f.suffix in (".js", ".css"):
                shutil.copy(f, common / f.name)
        # Subclasses write extra pages with the same module selection.
        cls.root, cls.page_head, cls.page_scripts = root, head, scripts
        (root / "logo.svg").write_text(LOGO, encoding="utf-8")
        (root / "a.html").write_text(head + SLIDES_A + scripts % OPTS_A, encoding="utf-8")
        (root / "a-nofooter.html").write_text(
            head + SLIDES_A + scripts % "sidebar: true, logoSrc: './logo.svg'", encoding="utf-8")
        (root / "b.html").write_text(head + SLIDES_B + scripts % "sidebar: false", encoding="utf-8")
        (root / "detail-contexts.html").write_text(
            head + SLIDES_DETAIL_CONTEXTS + scripts % "sidebar: false", encoding="utf-8")
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
