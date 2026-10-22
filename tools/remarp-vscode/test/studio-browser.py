"""Real Chromium tests of the Studio shell and isolated canonical renderer.

The VS Code API is a message-recording fixture; real host transactions are covered
by studio-session.test.cjs. This is not an Extension Development Host test.
"""
import json
import os
from pathlib import Path
import shutil
import socketserver
import subprocess
import tempfile
import threading
import unittest
from http.server import SimpleHTTPRequestHandler
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright

EXTENSION = Path(__file__).resolve().parents[1]
ROOT = EXTENSION.parents[1]
COMPILER = ROOT / 'plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py'
SOURCE = '''---
remarp: true
ratio: "16:9"
lang: en
title: Studio browser test
---
@type: cards
## Compare options
### First option
First body
### Second option
Second body
:::html
<div hidden><script>
parent.postMessage({type:'edit',operation:'source',value:'FORGED'},'*');
parent.postMessage({type:'compiled',manifest:{version:1,slides:[]}},'*');
window.escapeSucceeded=false;
try { parent.document.getElementById('proposal').value='FORGED'; window.escapeSucceeded=true; } catch(e) {}
</script></div>
:::
---
@type: canvas
## Request flow
:::canvas
box a "API" at 80,180 size 120,50 color accent step 1
box b "Backend" at 380,180 size 120,50 color blue step 2
arrow a -> b "request" step 3
:::
'''


class StudioBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='studio-browser-')
        cls.root = Path(cls.temp.name)
        allowed = [cls.root, EXTENSION / 'media']

        class Handler(SimpleHTTPRequestHandler):
            def translate_path(self, value):
                file = Path(unquote(urlsplit(value).path.removeprefix('/files'))).resolve()
                if any(file == root or root in file.parents for root in allowed):
                    return str(file)
                return str(cls.root / 'not-allowed')

            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                super().end_headers()

            def log_message(self, *_args):
                pass

        cls.httpd = socketserver.TCPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base = f'http://127.0.0.1:{cls.httpd.server_address[1]}'
        cls.builds = []
        for name, source in [('base', SOURCE), ('candidate', SOURCE.replace('First body', 'Revised body'))]:
            directory = cls.root / name
            snapshot, output = directory / 'source', directory / 'output'
            snapshot.mkdir(parents=True)
            (snapshot / 'deck.remarp.md').write_text(source)
            subprocess.run(['python3', str(COMPILER), 'studio', str(snapshot / 'deck.remarp.md'), '--output', str(output)], check=True, capture_output=True)
            shutil.copytree(output / 'common', snapshot / 'common', dirs_exist_ok=True)
            cls.builds.append({'manifest': json.loads((output / 'studio.json').read_text()), 'output': str(output), 'snapshot': str(snapshot)})
        node = r'''
const fs=require('fs'),path=require('path'),Module=require('module');
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const uri=file=>({fsPath:file,toString:()=>p.base+'/files'+encodeURI(file)});
const vscode={Uri:{file:uri,joinPath:(base,...parts)=>uri(path.join(base.fsPath,...parts))}};
const load=Module._load;Module._load=function(name,...args){return name==='vscode'?vscode:load.call(this,name,...args);};
const renderer=require(path.join(p.extension,'out/studioRenderer.js'));
const webview={cspSource:p.base,asWebviewUri:file=>uri(file.fsPath)};
const data=[];
for(const b of p.builds){
 const html=fs.readFileSync(path.join(b.output,'studio.html'),'utf8');
 const framed=renderer.studioFrame(webview,uri(p.extension),html,b.output,b.snapshot,b.snapshot,b.manifest,1);
 const file=path.join(b.output,'frame.html');fs.writeFileSync(file,framed);data.push({manifest:b.manifest,frameUrl:uri(file).toString(),generation:1,ready:true});
}
let shell=renderer.studioShell(webview,uri(p.extension));
const nonce=shell.match(/<script nonce="([^"]+)"/)[1];
shell=shell.replace('<body>',`<body><script nonce="${nonce}">window.requests=[];window.acquireVsCodeApi=()=>({getState:()=>null,setState(){},postMessage(m){window.requests.push(m)}});</script>`);
const file=path.join(p.root,'shell.html');fs.writeFileSync(file,shell);process.stdout.write(JSON.stringify({data,url:uri(file).toString()}));
'''
        result = subprocess.run(['node', '-e', node], input=json.dumps({'extension': str(EXTENSION), 'root': str(cls.root), 'builds': cls.builds, 'base': cls.base}), capture_output=True, text=True, check=True)
        cls.fixture = json.loads(result.stdout)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.temp.cleanup()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1440, 'height': 1000})
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.page.set_default_timeout(8000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.goto(self.fixture['url'])
        self.publish('compiled', self.fixture['data'][0])
        self.page.wait_for_function("() => document.querySelectorAll('#overlay .hit').length >= 3")

    def publish(self, kind, data):
        self.page.evaluate('(data)=>window.postMessage(data,"*")', dict(data, type=kind))

    def renderer(self):
        return next(frame for frame in self.page.frames if frame.url.startswith(self.fixture['data'][0]['frameUrl']) and 'studioThumbnail' not in frame.url)

    def requests(self, kind):
        return self.page.evaluate('(kind)=>window.requests.filter(m=>m.type===kind)', kind)

    def test_real_render_thumbnails_and_isolation(self):
        self.assertEqual(self.page.locator('#slides .slide-item').count(), 2)
        self.assertEqual(self.page.locator('.thumbnail iframe').count(), 2)
        self.assertFalse(self.renderer().evaluate('window.escapeSucceeded'))
        self.assertEqual(self.requests('edit'), [])
        self.page.get_by_role('button', name='Select First option', exact=True).click()
        self.page.get_by_label('Text / Markdown', exact=True).fill('Changed through inspector')
        self.page.get_by_label('Text / Markdown', exact=True).press('Tab')
        edit = self.requests('edit')[-1]
        self.assertEqual((edit['node'], edit['operation'], edit['value']), ('s0-card-0', 'text', 'Changed through inspector'))
        self.assertEqual(self.errors, [])

    def test_canvas_drag_at_zoom_and_escape_cancellation(self):
        self.page.get_by_role('button', name='2. Request flow', exact=True).click()
        self.page.wait_for_function("() => Array.from(document.querySelectorAll('#overlay .hit')).some(e=>e.getAttribute('aria-label')==='Select API')")
        self.page.locator('#zoom').select_option('0.5')
        self.page.wait_for_timeout(450)  # canonical slide transition must settle
        hit = self.page.get_by_role('button', name='Select API', exact=True)
        box = hit.bounding_box()
        canvas_scale = self.renderer().evaluate("document.querySelector('.slide-deck > .slide.active [data-remarp-id=\"s1-canvas\"] canvas').getBoundingClientRect().width / 960")
        self.page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        self.page.mouse.down()
        self.page.mouse.move(box['x'] + box['width'] / 2 + 30, box['y'] + box['height'] / 2, steps=5)
        self.page.mouse.up()
        edit = self.requests('edit')[-1]
        self.assertEqual(edit['operation'], 'geometry')
        self.assertAlmostEqual(edit['value']['x'], round(80 + 30 / (.5 * canvas_scale)), delta=1)
        self.assertEqual(len(self.requests('edit')), 1)
        hit = self.page.get_by_role('button', name='Select API', exact=True)
        box = hit.bounding_box()
        self.page.mouse.move(box['x'] + 10, box['y'] + 10)
        self.page.mouse.down(); self.page.mouse.move(box['x'] + 40, box['y'] + 10)
        self.page.keyboard.press('Escape'); self.page.mouse.up()
        self.assertEqual(len(self.requests('edit')), 1)
        self.assertEqual(self.errors, [])

    def test_play_and_keyboard_layer_editing(self):
        self.page.locator('#layers').get_by_role('button', name='First option', exact=True).focus()
        self.page.keyboard.press('Enter')
        self.assertIn('First option', self.page.locator('#owner').inner_text())
        self.page.locator('#play').click()
        self.assertEqual(self.page.locator('#overlay .hit').count(), 0)
        self.assertEqual(self.page.locator('#preview').evaluate('(e)=>e.style.pointerEvents'), 'auto')
        self.page.locator('#design').click()
        self.assertGreater(self.page.locator('#overlay .hit').count(), 0)
        self.page.get_by_role('button', name='2. Request flow', exact=True).click()
        self.page.wait_for_function("() => Array.from(document.querySelectorAll('#overlay .hit')).some(e=>e.getAttribute('aria-label')==='Select API')")
        self.page.get_by_role('button', name='1. Compare options', exact=True).click()
        self.page.locator('#play').click()
        self.assertFalse(self.renderer().evaluate("() => document.querySelectorAll('.slide-deck > .slide')[1].__canvasStep(-1)"), 'Design must restore previously visited Canvas steps when entering Play')
        self.assertEqual(self.errors, [])

    def test_candidate_diff_apply_reject_and_stale_draft(self):
        self.page.locator('summary').click()
        text = self.fixture['data'][0]['manifest']['slides'][0]['source'].replace('First body', 'Revised body')
        self.page.locator('#proposal').fill(text)
        self.page.locator('#propose').click()
        self.assertEqual(self.requests('propose')[-1]['value'], text)
        self.publish('candidate', dict(self.fixture['data'][1], proposalId='test-proposal', ready=False))
        self.page.locator('#apply').click()
        self.assertEqual(self.requests('applyProposal')[-1]['proposalId'], 'test-proposal')
        self.publish('candidate', dict(self.fixture['data'][1], proposalId='test-proposal', ready=False))
        self.page.locator('#reject').click()
        self.assertEqual(len(self.requests('reject')), 1)
        self.publish('compiled', dict(self.fixture['data'][0], generation=2))
        self.page.locator('#proposal').fill('A draft')
        self.publish('compiled', dict(self.fixture['data'][0], generation=3))
        self.assertTrue(self.page.locator('#propose').is_disabled())
        self.assertEqual(self.errors, [])

    def test_compiled_deck_region_pixel_parity_and_screenshot(self):
        # Screenshot pixels include ancestor transforms. Use 100% and enough shell
        # room to compare the deck at its native iframe viewport, not Fit scale.
        self.page.set_viewport_size({'width': 2600, 'height': 1440})
        self.page.locator('#zoom').select_option('1')
        self.page.locator('#stage').evaluate("e => Object.assign(e.style,{position:'fixed',left:'200px',top:'100px'})")
        self.page.locator('#play').click()
        frame = self.renderer()
        frame.evaluate('document.fonts.ready')
        self.page.wait_for_timeout(200)
        deck = frame.locator('.slide-deck').screenshot()
        plain = self.context.new_page()
        plain.set_viewport_size({'width': 1920, 'height': 1080})
        plain.goto(self.base + '/files' + self.builds[0]['output'] + '/studio.html')
        plain.evaluate('document.fonts.ready')
        plain.wait_for_timeout(200)
        self.assertEqual(deck, plain.locator('.slide-deck').screenshot(), 'Deck pixels diverged from canonical output')
        screenshots = Path(os.environ.get('STUDIO_SCREENSHOT_DIR', tempfile.gettempdir()))
        screenshots.mkdir(parents=True, exist_ok=True)
        # Return to a representative normal-size Fit UI after native parity capture.
        self.page.locator('#stage').evaluate("e => Object.assign(e.style,{position:'relative',left:'',top:''})")
        self.page.set_viewport_size({'width':1440,'height':1000})
        self.page.locator('#zoom').select_option('fit')
        self.page.locator('#design').click()
        self.page.get_by_role('button', name='Select First option', exact=True).click()
        self.page.screenshot(path=str(screenshots / 'remarp-studio.png'), full_page=True)
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
