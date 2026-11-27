"""Real Chromium geometry tests of the Approximate Text Preview.

The HTML comes from Preview's createOrShow() path with a minimal VS Code fixture.
These are browser layout tests, not an Extension Development Host smoke test.
Run after npm run compile; requires Python Playwright and its Chromium browser.
"""
import json
import os
from pathlib import Path
import socketserver
import subprocess
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler
from urllib.parse import quote, unquote, urlsplit

from playwright.sync_api import sync_playwright

EXTENSION = Path(__file__).resolve().parents[1]
CASES = {
    'default': ('', (1280, 720)),
    'wide': ('ratio: "16:9"', (1280, 720)),
    'classic': ('ratio: "4:3"', (960, 720)),
    'ultrawide': ('ratio: "21:9"', (1280, 1280 * 9 / 21)),
    'portrait': ('ratio: "9:16"', (405, 720)),
    'size': ('size: 960x720\nratio: "16:9"', (960, 720)),
    'invalid': ('size: 0x720\nratio: "16:0"', (1280, 720)),
}


def source(frontmatter):
    return f'''---
remarp: true
{frontmatter}
---
# Preview geometry

The entire slide, including its right edge, must remain visible.

:::notes
Speaker notes remain accessible beside or below the slide.
{chr(10).join('- A long note line for testing sidebar scrolling.' for _ in range(100))}
:::
'''


class PreviewBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='preview-browser-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        allowed = [cls.root, EXTENSION / 'media']

        class Handler(SimpleHTTPRequestHandler):
            def translate_path(self, value):
                file = Path(unquote(urlsplit(value).path.removeprefix('/files'))).resolve()
                if any(file == root or root in file.parents for root in allowed):
                    return str(file)
                return str(cls.root / 'not-allowed')

            def log_message(self, *_args):
                pass

        cls.httpd = socketserver.TCPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.addClassCleanup(cls.httpd.server_close)
        cls.addClassCleanup(cls.httpd.shutdown)
        cls.base = f'http://127.0.0.1:{cls.httpd.server_address[1]}'
        rendered = subprocess.run(
            ['node', str(EXTENSION / 'test/preview-fixture.cjs')],
            input=json.dumps({'base': cls.base, 'sources': [source(fm) for fm, _ in CASES.values()]}),
            capture_output=True, text=True, check=True,
        )
        cls.urls = {}
        for name, html in zip(CASES, json.loads(rendered.stdout)):
            file = cls.root / f'{name}.html'
            file.write_text(html)
            cls.urls[name] = cls.base + '/files' + quote(str(file))
        cls.pw = sync_playwright().start()
        cls.addClassCleanup(cls.pw.stop)
        cls.browser = cls.pw.chromium.launch()
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 900})
        self.addCleanup(self.context.close)
        self.context.add_init_script('''
            window.requests = [];
            window.acquireVsCodeApi = () => ({ getState: () => null, setState() {},
                postMessage: m => window.requests.push(m) });
        ''')
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def load(self, name='default'):
        self.page.goto(self.urls[name])
        self.page.locator('.slide-wrapper').wait_for(state='attached')
        self.settle()
        if name == 'default':
            self.capture('default')

    def capture(self, name):
        if os.environ.get('PREVIEW_SCREENSHOT_DIR'):
            screenshots = Path(os.environ['PREVIEW_SCREENSHOT_DIR'])
            screenshots.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(screenshots / f'remarp-preview-{name}.png'))
            (screenshots / f'remarp-preview-{name}.json').write_text(json.dumps(self.geometry(), indent=2))

    def settle(self):
        # Allow both window resize and ResizeObserver callbacks to run.
        self.page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')

    def geometry(self):
        return self.page.evaluate('''() => {
            const rect = selector => {
                const e = document.querySelector(selector), r = e.getBoundingClientRect();
                return { x: r.x, y: r.y, width: r.width, height: r.height,
                    right: r.right, bottom: r.bottom, clientWidth: e.clientWidth,
                    clientHeight: e.clientHeight, scrollWidth: e.scrollWidth, scrollHeight: e.scrollHeight };
            };
            const slide = document.querySelector('.slide');
            return { wrapper: rect('.slide-wrapper'), slide: rect('.slide'),
                container: rect('.slide-container'), sidebar: rect('.sidebar'),
                notes: rect('.sidebar-content'), prompt: rect('#promptInput'),
                designWidth: parseFloat(getComputedStyle(slide).width),
                designHeight: parseFloat(getComputedStyle(slide).height),
                viewport: { width: innerWidth, height: innerHeight },
                document: { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight } };
        }''')

    def assert_fitted(self, name='default'):
        g = self.geometry()
        detail = json.dumps(g, indent=2)
        wrapper, slide, container, sidebar = (g[key] for key in ('wrapper', 'slide', 'container', 'sidebar'))
        width, height = CASES[name][1]
        self.assertAlmostEqual(g['designWidth'], width, delta=0.02, msg=detail)
        self.assertAlmostEqual(g['designHeight'], height, delta=0.02, msg=detail)
        self.assertGreater(wrapper['width'], 0, detail)
        self.assertGreater(wrapper['height'], 0, detail)
        self.assertAlmostEqual(wrapper['width'] / wrapper['height'], width / height, delta=0.001, msg=detail)
        expected_scale = min((container['clientWidth'] - 16) / width,
                             (container['clientHeight'] - 16) / height)
        self.assertAlmostEqual(wrapper['width'], width * expected_scale, delta=0.1, msg=detail)
        self.assertAlmostEqual(wrapper['height'], height * expected_scale, delta=0.1, msg=detail)
        for key in ('x', 'y', 'width', 'height'):
            self.assertAlmostEqual(wrapper[key], slide[key], delta=0.1, msg='Slide was clipped by its wrapper: ' + detail)
        self.assertGreaterEqual(wrapper['x'], container['x'] + 7.9, detail)
        self.assertGreaterEqual(wrapper['y'], container['y'] + 7.9, detail)
        self.assertLessEqual(wrapper['right'], container['right'] - 7.9, detail)
        self.assertLessEqual(wrapper['bottom'], container['bottom'] - 7.9, detail)
        for origin, length in (('x', 'width'), ('y', 'height')):
            self.assertAlmostEqual(wrapper[origin] + wrapper[length] / 2,
                                   container[origin] + container[length] / 2, delta=0.1, msg=detail)
        self.assertTrue(wrapper['right'] <= sidebar['x'] + 0.1 or wrapper['bottom'] <= sidebar['y'] + 0.1, detail)
        self.assertLessEqual(g['document']['width'], g['viewport']['width'], detail)
        self.assertLessEqual(g['document']['height'], g['viewport']['height'], detail)
        self.assertGreater(g['prompt']['width'], 100, detail)
        self.assertGreater(g['notes']['height'], 0, detail)
        self.assertGreater(g['notes']['scrollHeight'], g['notes']['clientHeight'], detail)
        self.assertEqual(self.errors, [])

    def test_ratio_size_and_default_fit_real_rendered_boxes(self):
        for name in CASES:
            with self.subTest(name=name):
                self.load(name)
                self.assert_fitted(name)

    def test_resizes_keep_slide_centered_and_notes_accessible(self):
        self.load()
        for width, height in [(1920, 600), (900, 480), (600, 1000), (480, 640), (320, 480), (320, 240), (1440, 900)]:
            with self.subTest(width=width, height=height):
                self.page.set_viewport_size({'width': width, 'height': height})
                self.settle()
                if width == 480:
                    self.capture('narrow')
                self.assert_fitted()
                self.page.locator('#promptInput').fill('Keep notes usable')
                self.assertTrue(self.page.locator('.prompt-submit').is_visible())
                self.page.locator('.sidebar-content').evaluate('e => e.scrollTop = e.scrollHeight')
                self.assertGreater(self.page.locator('.sidebar-content').evaluate('e => e.scrollTop'), 0)

    def test_sidebar_resize_without_window_resize_refits_slide(self):
        self.load('classic')
        self.page.locator('.sidebar').evaluate("e => Object.assign(e.style, {width: '420px', flexBasis: '420px'})")
        self.settle()
        self.assert_fitted('classic')


if __name__ == '__main__':
    unittest.main()
