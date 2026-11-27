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
from urllib.parse import quote, unquote, urlsplit

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
<button id="inline-action" onclick="this.dataset.clicked='yes'; return false">Inline interaction</button>
<link rel="stylesheet" href="assets/probe.css">
<span class="asset-probe" hidden></span>
<div hidden><script>
parent.postMessage({type:'edit',operation:'source',value:'FORGED'},'*');
parent.postMessage({type:'compiled',manifest:{version:1,slides:[]}},'*');
window.escapeSucceeded=false;
try { parent.document.getElementById('proposal').value='FORGED'; window.escapeSucceeded=true; } catch(e) {}
window.dynamicTestImage = new Image();
window.dynamicTestImage.src = './assets/nested/check.svg';
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
            (snapshot / 'assets/nested').mkdir(parents=True)
            (snapshot / 'assets/nested/check.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8" fill="red"/></svg>')
            (snapshot / 'assets/probe.css').write_text('@import "nested/probe.css";')
            (snapshot / 'assets/nested/probe.css').write_text('.asset-probe { background-image: url(check.svg); color: rgb(12, 34, 56); }')
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
const nonce='studio-browser-fixture-nonce';
const hostChannel='studio-browser-host-channel';
const data=[];
for(const b of p.builds){
 const html=fs.readFileSync(path.join(b.output,'studio.html'),'utf8');
 const frameHtml=renderer.studioFrame(webview,uri(p.extension),html,b.output,b.snapshot,b.snapshot,b.manifest,1,nonce);
 data.push({manifest:b.manifest,frameHtml,generation:1,ready:true,studioChannel:hostChannel});
}
let shell=renderer.studioShell(webview,uri(p.extension),nonce,hostChannel);
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
        self.page.evaluate('(data)=>window.postMessage(data,"*")', dict(data, type=kind, studioChannel='studio-browser-host-channel'))

    def renderer(self):
        return self.page.locator('#preview').element_handle().content_frame()

    def requests(self, kind):
        return self.page.evaluate('(kind)=>window.requests.filter(m=>m.type===kind)', kind)

    def test_headless_provider_settings_generation_cancel_and_candidate_controls(self):
        self.publish('aiSettings', {'provider': 'claude', 'profiles': {'claude': {'model': 'sonnet', 'effort': 'high'}, 'codex': {'model': 'test-model', 'effort': 'low'}}})
        self.assertEqual(self.page.locator('#aiProvider').input_value(), 'claude')
        self.assertIn('sonnet', self.page.locator('#aiProfile').inner_text())
        self.page.locator('#aiProvider').select_option('codex')
        self.assertIn('test-model', self.page.locator('#aiProfile').inner_text())
        self.page.locator('#aiSettings').click()
        self.assertEqual(len(self.requests('aiSettings')), 1)
        self.page.locator('#prompt').fill('Improve spacing')
        self.page.locator('#generateAI').click()
        request = self.requests('generateAI')[-1]
        self.assertEqual(request['provider'], 'codex')
        self.assertEqual(request['prompt'], 'Improve spacing')
        self.assertEqual(request['slide'], 's0')
        before = self.page.locator('#proposal').input_value()
        self.publish('aiStatus', {'busy': True, 'message': 'Generating with codex — source unchanged'})
        self.page.wait_for_function("() => document.querySelector('#aiStatus').textContent.includes('Generating with codex')")
        self.assertTrue(self.page.locator('#generateAI').is_disabled())
        self.assertTrue(self.page.locator('#propose').is_disabled())
        self.assertTrue(self.page.locator('#aiProvider').is_disabled())
        self.assertTrue(self.page.locator('#cancelAI').is_visible())
        self.page.locator('#cancelAI').click()
        self.assertEqual(len(self.requests('cancelAI')), 1)
        self.publish('aiStatus', {'busy': False, 'message': 'Cancelled — source unchanged'})
        self.page.wait_for_function("() => document.querySelector('#aiStatus').textContent.includes('Cancelled')")
        self.assertTrue(self.page.locator('#cancelAI').is_hidden())
        self.assertEqual(self.page.locator('#proposal').input_value(), before)
        self.assertTrue(self.page.locator('#generateAI').is_enabled())
        self.publish('candidate', dict(self.fixture['data'][1], proposalId='headless-fixture', ready=False))
        self.page.wait_for_function("() => document.querySelector('#status').textContent === 'Candidate — Apply or Reject'")
        self.assertTrue(self.page.locator('#candidate').is_visible())
        self.assertTrue(self.page.locator('#generateAI').is_disabled())
        self.assertFalse(self.requests('applyProposal'))
        self.page.locator('#apply').click()
        self.assertEqual(self.requests('applyProposal')[-1]['proposalId'], 'headless-fixture')
        self.assertEqual(self.errors, [])

    def test_authored_renderer_cannot_start_an_ai_job_or_change_settings(self):
        self.renderer().evaluate("""() => {
            parent.postMessage({type:'generateAI',provider:'claude',prompt:'FORGED'}, '*');
            parent.postMessage({type:'aiSettings',provider:'kiro'}, '*');
            parent.postMessage({type:'aiStatus',busy:true,message:'FORGED'}, '*');
        }""")
        self.page.wait_for_timeout(150)
        self.assertFalse(self.requests('generateAI'))
        self.assertFalse(self.requests('aiSettings'))
        self.assertEqual(self.page.locator('#aiProvider').input_value(), 'claude')
        self.assertTrue(self.page.locator('#cancelAI').is_hidden())
        self.assertEqual(self.errors, [])

    def test_initial_compile_error_is_visible_without_a_map_and_source_remains_available(self):
        self.page.goto(self.fixture['url'])  # Fresh shell: no compiled map was delivered.
        self.publish('status', {'ready': False, 'message': 'Building — previous preview is stale'})
        self.publish('error', {'ready': False, 'status': 'Studio could not build this source', 'message': 'Studio compile failed. Test compiler unavailable.'})
        self.page.wait_for_function("() => document.querySelector('#status').textContent === 'Studio could not build this source'")
        self.assertTrue(self.page.locator('#diagnostics').is_visible())
        self.assertIn('Test compiler unavailable', self.page.locator('#diagnostics').inner_text())
        self.assertEqual(self.page.locator('#slides .slide-item').count(), 0)
        self.assertTrue(self.page.locator('#propose').is_disabled())
        self.assertTrue(self.page.locator('#undo').is_disabled())
        self.assertTrue(self.page.locator('#source').is_enabled())
        self.page.locator('#source').click()
        self.assertEqual(len(self.requests('reveal')), 1)
        self.assertEqual(self.errors, [])

    def test_failed_rebuild_keeps_existing_renderer_visible_and_editing_disabled(self):
        before = self.page.locator('#preview').get_attribute('srcdoc')
        self.publish('status', {'ready': False, 'message': 'Building — previous preview is stale'})
        self.publish('error', {'ready': False, 'status': 'Build failed — previous preview is stale', 'message': 'Invalid source: test failure'})
        self.page.wait_for_function("() => document.querySelector('#status').textContent === 'Build failed — previous preview is stale'")
        self.assertEqual(self.page.locator('#preview').get_attribute('srcdoc'), before)
        self.assertEqual(self.page.locator('#slides .slide-item').count(), 2)
        self.assertTrue(self.page.locator('#diagnostics').is_visible())
        self.assertTrue(self.page.locator('#undo').is_disabled())
        self.assertTrue(self.page.locator('#propose').is_disabled())
        self.assertTrue(self.page.locator('#source').is_enabled())
        self.assertEqual(self.errors, [])

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
        # The Canvas runtime accepts only the strings 'next' and 'prev'. Design shows every reveal step, so
        # one more 'next' stays on the last step (the fixture has steps 1 to 3).
        self.assertEqual(self.renderer().evaluate("() => { const s = document.querySelectorAll('.slide-deck > .slide')[1]; return [Number(s.dataset.canvasMaxStep), s.__canvasStep('next')]; }"), [3, 3], 'Design must reveal every Canvas step')
        self.page.get_by_role('button', name='1. Compare options', exact=True).click()
        self.page.locator('#play').click()
        # Back in Play the Canvas starts from its first step again, so 'next' lands on step 1, not on the last.
        # The mode change reaches the renderer as a message, so wait for it; a Canvas that is never
        # restored keeps answering 3 and this wait times out.
        self.renderer().wait_for_function("() => document.querySelectorAll('.slide-deck > .slide')[1].__canvasStep('next') === 1", timeout=3000)
        self.assertEqual(self.errors, [])

    def test_fit_keeps_full_sixteen_by_nine_canvas_after_pane_resize(self):
        self.page.locator('#zoom').select_option('fit')
        for width, height in [(1440, 1000), (900, 700), (500, 900), (1600, 550)]:
            with self.subTest(width=width, height=height):
                self.page.set_viewport_size({'width': width, 'height': height})
                self.page.wait_for_function("""() => {
                    const stage = document.querySelector('#stage').getBoundingClientRect();
                    const element = document.querySelector('#viewport');
                    const viewport = element.getBoundingClientRect();
                    const frame = document.querySelector('#preview');
                    const fit = Math.min((element.clientWidth - 44) / frame.offsetWidth,
                        (element.clientHeight - 44) / frame.offsetHeight);
                    return stage.width > 0 && stage.left >= viewport.left && stage.right <= viewport.right
                        && stage.top >= viewport.top && stage.bottom <= viewport.bottom
                        && Math.abs(stage.width - frame.offsetWidth * fit) < 1
                        && Math.abs(stage.height - frame.offsetHeight * fit) < 1;
                }""")
                stage, frame = self.page.evaluate("""() => ['#stage', '#preview'].map(selector => {
                    const rect = document.querySelector(selector).getBoundingClientRect();
                    return {width: rect.width, height: rect.height};
                })""")
                self.assertAlmostEqual(stage['width'] / stage['height'], 16 / 9, delta=0.002)
                self.assertAlmostEqual(frame['width'], stage['width'], delta=1)
                self.assertAlmostEqual(frame['height'], stage['height'], delta=1)
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

    def host_page(self):
        # VS Code delivers webview.postMessage() through the outer webview page, so the shell sees the
        # parent frame as event.source. Reproduce that nesting; the plain-page tests above post from the
        # shell's own window and cannot tell the two apart.
        outer = self.root / 'host.html'
        outer.write_text('<!doctype html><iframe id="shell" src="%s" style="width:1440px;height:1000px;border:0"></iframe>' % self.fixture['url'])
        page = self.context.new_page()
        page.set_default_timeout(8000)
        page.goto(f"{self.base}/files{quote(str(outer))}")
        page.wait_for_function("() => { const f = document.getElementById('shell'); return f.contentDocument && f.contentDocument.readyState === 'complete' && !!f.contentDocument.getElementById('slides'); }")
        # acquireVsCodeApi's real injected shim masks parent/top. The old
        # event.source===window.parent guard therefore rejected actual delivery.
        page.evaluate("() => { const w=document.getElementById('shell').contentWindow; w.parent=w; w.top=w; }")
        return page

    def test_host_messages_delivered_through_the_parent_frame_reach_the_shell(self):
        page = self.host_page()
        page.evaluate('(data)=>document.getElementById("shell").contentWindow.postMessage(data,"*")', dict(self.fixture['data'][0], type='compiled'))
        shell = page.frame_locator('#shell')
        shell.locator('#slides .slide-item').first.wait_for()
        self.assertEqual(shell.locator('#slides .slide-item').count(), 2)

    def test_a_message_from_a_nested_preview_frame_is_not_a_host_message(self):
        # An authored island can open a nested frame in the sandboxed preview and post to the shell. That
        # frame is neither the shell's own window nor its parent, so the message must be ignored.
        forged = {'type': 'compiled', 'generation': 99, 'frameHtml': '<p>Forged</p>',
                  'manifest': {'version': 1, 'slides': [{'file': 'x', 'title': 'Forged', 'source': 'forged', 'nodes': []}]}}
        self.renderer().evaluate("""(data) => { const f = document.createElement('iframe');
            f.srcdoc = '<script>parent.parent.postMessage(' + JSON.stringify(data) + ',"*")<\\/script>'; document.body.append(f); }""", forged)
        self.page.wait_for_timeout(600)
        self.assertEqual(self.page.locator('#slides .slide-item').count(), 2)
        self.assertEqual(self.requests('edit'), [])
        self.assertEqual(self.errors, [])

    def test_renderer_is_self_contained_without_resource_navigation(self):
        # Unlike an ordinary localhost iframe, srcdoc works when nested document
        # navigation cannot reach VS Code's service worker. No deck asset may
        # depend on the fixture's substitute asWebviewUri endpoint.
        self.assertEqual(self.renderer().url.split('#')[0], 'about:srcdoc')
        self.assertEqual(self.page.locator('#preview').get_attribute('sandbox'), 'allow-scripts')
        self.assertEqual(self.renderer().evaluate('typeof acquireVsCodeApi'), 'undefined')
        self.assertFalse(self.renderer().evaluate('window.escapeSucceeded'))
        self.assertNotIn('/files', self.page.locator('#preview').get_attribute('srcdoc'))
        for frame in self.page.frames:
            if frame.name.startswith('remarp-studio-thumbnail:'):
                frame.wait_for_function("() => document.querySelector('.slide.active')")
                self.assertEqual(frame.evaluate("Array.from(document.querySelectorAll('.slide')).findIndex(s=>s.classList.contains('active'))"), int(frame.name.split(':')[1]))

    def test_renderer_failure_is_visible_and_cannot_call_host_api(self):
        self.renderer().evaluate("() => parent.postMessage({type:'studio-render-error',generation:1,message:'Fixture renderer failed'},'*')")
        self.page.wait_for_function("() => document.querySelector('#status').textContent.includes('Renderer failed')")
        self.assertIn('Fixture renderer failed', self.page.locator('#diagnostics').inner_text())
        self.assertTrue(self.page.locator('#issue').is_disabled())
        self.assertFalse(self.page.locator('#source').is_disabled())
        self.assertEqual(self.requests('edit'), [])

    def test_bundled_runtime_images_css_imports_and_authored_interaction(self):
        frame = self.renderer()
        frame.wait_for_function('() => window.dynamicTestImage.complete && window.dynamicTestImage.naturalWidth === 8')
        self.assertTrue(frame.evaluate('window.dynamicTestImage.src.startsWith("data:image/svg+xml;")'))
        frame.wait_for_function("() => getComputedStyle(document.querySelector('.asset-probe')).color === 'rgb(12, 34, 56)'")
        self.assertIn('data:image/svg+xml;', frame.locator('.asset-probe').first.evaluate('(e)=>getComputedStyle(e).backgroundImage'))
        self.page.locator('#play').click()
        action = frame.locator('.slide.active #inline-action')
        action.click()
        self.assertEqual(action.get_attribute('data-clicked'), 'yes')
        self.assertIsNone(action.get_attribute('onclick'))
        self.assertEqual(self.errors, [])

    def test_host_channel_required_even_with_parent_masked(self):
        page = self.host_page()
        shell = page.frame_locator('#shell')
        forged = dict(self.fixture['data'][0], type='compiled', studioChannel='wrong-channel')
        page.evaluate('(data)=>document.getElementById("shell").contentWindow.postMessage(data,"*")', forged)
        page.wait_for_timeout(150)
        self.assertEqual(shell.locator('#slides .slide-item').count(), 0)
        self.assertNotIn('studio-browser-host-channel', self.page.locator('#preview').get_attribute('srcdoc'))
        self.assertEqual(self.page.locator('script[data-studio-channel]').count(), 0)


if __name__ == '__main__':
    unittest.main()
