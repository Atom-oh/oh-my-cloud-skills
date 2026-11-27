"""Optional authenticated real code-server/Extension Host Studio smoke test.

Requires code-server, Python Playwright/Chromium and localhost sockets. Unlike
studio-browser.py, this exercises VS Code's actual injected API and service
worker. The extension, user data and presentation are copied into a temporary
instance; no existing editor session, installation or presentation is modified.

Run after npm run compile:
  python3 test/studio-code-server.py --artifacts /tmp/studio-host-check
  python3 test/studio-code-server.py --project-source /tmp/staged-deck --entry 01-overview.md
"""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import tempfile
import time
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

EXTENSION = Path(__file__).resolve().parents[1]
COMPILER = EXTENSION.parents[1] / 'plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py'
SOURCE = '''---
remarp: true
ratio: "16:9"
lang: en
title: Real Extension Host test
---
@type: cards
## Compare options
### First option
First body
### Second option
Second body
---
## Second slide
The complete sixteen-by-nine slide should remain visible.
'''


def wait_until(page, callback, description, timeout=75):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = callback()
        if result:
            return result
        page.wait_for_timeout(200)
    raise AssertionError('Timed out waiting for ' + description)


def copy_project(source, target):
    """Copy a bounded data-only fixture, without symlinks or workspace settings."""
    ignored = {'.git', '.vscode', 'node_modules', '__pycache__'}
    total = count = 0
    target.mkdir()
    for base, directories, files in os.walk(source, followlinks=False):
        directories[:] = [name for name in directories if name not in ignored and not name.startswith('.')]
        for name in directories + files:
            if (Path(base) / name).is_symlink():
                raise ValueError('Project fixture must not contain symlinks')
        relative = Path(base).relative_to(source)
        (target / relative).mkdir(exist_ok=True)
        for name in files:
            if name.startswith('.'):
                continue
            file = Path(base) / name
            if not file.is_file():
                raise ValueError('Project fixture must contain regular files only')
            count += 1
            total += file.stat().st_size
            if count > 10000 or total > 200 * 1024 * 1024:
                raise ValueError('Project fixture exceeds 10,000 files / 200 MiB')
            shutil.copyfile(file, target / relative / name)


def command(page, text):
    page.keyboard.press('Control+Shift+p')
    box = page.locator('.quick-input-widget input').first
    box.wait_for(state='visible')
    box.fill('>' + text)
    page.wait_for_timeout(700)
    box.press('Enter')


def find_shell(page):
    for frame in page.frames:
        if frame.locator('#preview').count() and frame.locator('#status').count():
            return frame
    return None


def renderer(shell):
    return shell.locator('#preview').element_handle().content_frame()


def check_render(page, shell):
    shell.wait_for_function("() => document.querySelector('#status').textContent === 'Compiled snapshot'", timeout=75000)
    current = wait_until(page, lambda: renderer(shell), 'renderer document')
    current.wait_for_function("() => document.querySelector('.slide-deck > .slide.active') && document.querySelector('.slide-deck > .slide.active').getBoundingClientRect().width > 100", timeout=30000)
    assert shell.locator('#slides .slide-item').count() > 0, 'No slide navigation'
    assert shell.locator('#preview').get_attribute('sandbox') == 'allow-scripts'
    assert current.evaluate('typeof acquireVsCodeApi') == 'undefined', 'Renderer acquired host API'
    assert current.evaluate("() => { try { return !!parent.document; } catch (_) { return false; } }") is False, 'Renderer escaped opaque sandbox'
    assert shell.evaluate('window.parent === window') is True, 'Test did not exercise VS Code parent shadowing'
    before = shell.locator('#proposal').input_value()
    # A renderer can observe geometry, never pretend to be the Extension Host.
    current.evaluate("""() => {
        parent.postMessage({type:'compiled',studioChannel:'forged',manifest:{version:1,slides:[]}}, '*');
        parent.postMessage({type:'edit',operation:'source',value:'FORGED'}, '*');
        parent.postMessage({type:'error',message:'FORGED'}, '*');
    }""")
    page.wait_for_timeout(400)
    assert shell.locator('#proposal').input_value() == before, 'Untrusted frame changed source state'
    assert shell.locator('#status').inner_text() == 'Compiled snapshot', 'Untrusted frame changed status'
    dimensions = current.evaluate("""() => {
        const rect = document.querySelector('.slide-deck > .slide.active').getBoundingClientRect();
        return {width:rect.width,height:rect.height};
    }""")
    return dimensions


def check_project_interaction(page, shell):
    current = renderer(shell)
    # Some authored decks use raw HTML onclick tab sets; preserving those is a
    # separate requirement from merely rendering static title text.
    index = current.evaluate("""() => Array.from(document.querySelectorAll('.slide-deck > .slide')).findIndex(
        slide => slide.querySelectorAll('.tab-set .tab-btn').length > 1)""")
    if index < 0:
        return False
    shell.locator('#slides .slide-item').nth(index).click()
    shell.locator('#play').click()
    current.wait_for_function("""index => document.querySelectorAll('.slide-deck > .slide')[index].classList.contains('active')""", arg=index)
    button = current.locator('.slide-deck > .slide.active .tab-set').first.locator('.tab-btn').nth(1)
    button.click()
    current.wait_for_function("""() => {
        const tabs = document.querySelector('.slide-deck > .slide.active .tab-set');
        return tabs.querySelectorAll('.tab-btn')[1].classList.contains('active')
            && !tabs.parentElement.querySelectorAll('.tc')[1].hidden;
    }""")
    if not shell.locator('#diagnostics').is_hidden():
        assert 'FORGED' not in shell.locator('#diagnostics').inner_text()
    shell.locator('#design').click()
    return True


def smoke(page, workspace, entry, synthetic, artifacts):
    page.keyboard.press('Control+p')
    box = page.locator('.quick-input-widget input').first
    box.wait_for(state='visible')
    box.fill(str(workspace / entry))
    page.wait_for_timeout(600)
    box.press('Enter')
    page.wait_for_timeout(1500)
    command(page, 'Remarp: Open Design Studio')
    shell = wait_until(page, lambda: find_shell(page), 'Studio shell')
    dimensions = check_render(page, shell)
    displayed = shell.evaluate("""() => {
        const stage = document.querySelector('#stage').getBoundingClientRect();
        const viewport = document.querySelector('#viewport').getBoundingClientRect();
        return {width:stage.width,height:stage.height,contained:stage.left >= viewport.left
            && stage.right <= viewport.right && stage.top >= viewport.top && stage.bottom <= viewport.bottom};
    }""")
    assert displayed['contained'], 'Fit clipped the Studio canvas'
    assert abs(displayed['width'] / displayed['height'] - dimensions['width'] / dimensions['height']) < .002
    if artifacts:
        page.screenshot(path=str(artifacts / 'studio-initial.png'))
    if synthetic:
        assert abs(dimensions['width'] / dimensions['height'] - 16 / 9) < .002
        shell.locator('#layers').get_by_role('button', name='First option', exact=True).click()
        field = shell.get_by_label('Text / Markdown', exact=True)
        field.fill('Changed through the real host')
        field.press('Tab')
        shell.wait_for_function("() => document.querySelector('#proposal').value.includes('Changed through the real host')", timeout=75000)
        check_render(page, shell)
        renderer(shell).locator('.slide-deck > .slide.active').get_by_text('Changed through the real host', exact=True).wait_for(state='visible')
        assert (workspace / entry).read_text() == SOURCE, 'Studio unexpectedly saved the source file'
        shell.locator('#undo').click()
        shell.wait_for_function("() => document.querySelector('#proposal').value.includes('First option') && !document.querySelector('#proposal').value.includes('Changed through the real host')", timeout=75000)
        check_render(page, shell)
        assert (workspace / entry).read_text() == SOURCE
        if artifacts:
            page.screenshot(path=str(artifacts / 'source-undo.png'))
        page.get_by_role('tab', name=re.compile('Remarp Design Studio')).click()
        shell.locator('#viewport').wait_for(state='visible')
    candidate_flow = False
    if synthetic:
        # Manual-handoff flow: the user pastes replacement slide source, previews a
        # compiled candidate, and only Apply mutates the (unsaved) document.
        for outcome in ['reject', 'apply']:
            page.get_by_role('tab', name=re.compile('Remarp Design Studio')).click()
            proposal = shell.locator('#proposal')
            proposal.evaluate("(element) => element.closest('details').open = true")
            proposal.fill(proposal.input_value().replace('First body', 'Pasted host candidate'))
            shell.locator('#propose').click()
            shell.wait_for_function("() => !document.querySelector('#candidate').hidden", timeout=75000)
            page.get_by_role('tab', name=re.compile('Remarp Design Studio')).click()
            shell.wait_for_function("() => document.querySelector('#status').textContent === 'Candidate — Apply or Reject'", timeout=30000)
            assert (workspace / entry).read_text() == SOURCE, 'Candidate saved source without Apply'
            if outcome == 'apply':
                shell.locator('#apply').click()
                shell.wait_for_function("() => document.querySelector('#proposal').value.includes('Pasted host candidate')", timeout=75000)
                check_render(page, shell)
                shell.locator('#undo').click()
                shell.wait_for_function("() => document.querySelector('#proposal').value.includes('First body') && !document.querySelector('#proposal').value.includes('Pasted host candidate')", timeout=75000)
                check_render(page, shell)
            else:
                shell.locator('#reject').click()
                check_render(page, shell)
            assert (workspace / entry).read_text() == SOURCE
        candidate_flow = True
    interaction = False if synthetic else check_project_interaction(page, shell)
    renderer(shell).wait_for_function("""() => Array.from(document.images).filter(
        image => image.src.startsWith('data:')).every(image => image.complete && image.naturalWidth > 0)""")
    embedded_images = renderer(shell).evaluate("() => Array.from(document.images).filter(image => image.src.startsWith('data:')).length")
    if artifacts:
        page.screenshot(path=str(artifacts / 'studio.png'))
    return {'slides': shell.locator('#slides .slide-item').count(), 'dimensions': dimensions,
            'displayed_canvas': displayed,
            'rendered': True, 'opaque_sandbox': True, 'forgery_rejected': True,
            'real_host_edit_and_undo': synthetic, 'manual_candidate_reject_apply_undo': candidate_flow, 'authored_tabs': interaction,
            'loaded_embedded_images': embedded_images}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code-server', default='/usr/local/bin/code-server')
    parser.add_argument('--compiler', type=Path, default=COMPILER)
    parser.add_argument('--project-source', type=Path)
    parser.add_argument('--entry', default='deck.md', help='Relative Markdown path inside the copied project')
    parser.add_argument('--require-tabs', action='store_true', help='Fail unless an authored HTML tab interaction is verified')
    parser.add_argument('--expect-ratio', help='Assert a specific renderer aspect ratio, for example 16:9')
    parser.add_argument('--artifacts', type=Path, help='Optional screenshots and redacted diagnostic logs')
    args = parser.parse_args()
    if Path(args.entry).is_absolute() or '..' in Path(args.entry).parts or not args.entry.endswith('.md'):
        parser.error('--entry must be a relative Markdown path without traversal')
    if args.expect_ratio and not re.fullmatch(r'[1-9][0-9]{0,5}:[1-9][0-9]{0,5}', args.expect_ratio):
        parser.error('--expect-ratio must contain two positive integers, for example 16:9')
    if not args.compiler.is_file() or not (EXTENSION / 'out/studio.js').is_file():
        parser.error('Compiler/build unavailable; run npm run compile first')
    executable = shutil.which(args.code_server)
    if not executable:
        parser.error('code-server unavailable; pass the server launcher, not its remote CLI')
    artifacts = args.artifacts.resolve() if args.artifacts else None
    if artifacts:
        artifacts.mkdir(parents=True, exist_ok=True)
    report = {'authenticated': False, 'passed': False}
    with tempfile.TemporaryDirectory(prefix='remarp-real-host-') as temporary:
        root = Path(temporary)
        workspace = root / 'workspace'
        if args.project_source:
            source = args.project_source.resolve(strict=True)
            if not source.is_dir():
                parser.error('--project-source must be a fixture directory')
            copy_project(source, workspace)
        else:
            workspace.mkdir()
            (workspace / args.entry).parent.mkdir(parents=True, exist_ok=True)
            (workspace / args.entry).write_text(SOURCE)
        if not (workspace / args.entry).is_file():
            parser.error('--entry does not exist in the copied fixture')
        manifest = json.loads((EXTENSION / 'package.json').read_text())
        installed = root / 'extensions' / f"{manifest['publisher']}.{manifest['name']}-{manifest['version']}"
        installed.mkdir(parents=True)
        for name in ['out', 'media', 'syntaxes']:
            shutil.copytree(EXTENSION / name, installed / name)
        for name in ['package.json', 'language-configuration.json']:
            shutil.copyfile(EXTENSION / name, installed / name)
        user = root / 'user/User'
        user.mkdir(parents=True)
        (user / 'settings.json').write_text(json.dumps({
            'remarp.buildScriptPath': str(args.compiler.resolve()),
            'workbench.startupEditor': 'none', 'extensions.autoCheckUpdates': False,
            'extensions.autoUpdate': False, 'telemetry.telemetryLevel': 'off',
            'chat.disableAIFeatures': True, 'files.autoSave': 'off',
        }))
        # Keep authentication on even on loopback. The generated password never
        # enters command arguments, environment variables or persistent artifacts.
        password = secrets.token_urlsafe(32)
        config = root / 'config.yaml'
        config.write_text('auth: password\nbind-addr: 127.0.0.1:0\npassword: ' + json.dumps(password) + '\n')
        config.chmod(0o600)
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('VSCODE_', 'CODE_SERVER_', 'CS_'))
               and key not in {'PASSWORD', 'HASHED_PASSWORD', 'PORT', 'HOST'}}
        env['CODE_SERVER_SESSION_SOCKET'] = str(root / 'session.sock')
        (root / 'temporary').mkdir()
        env['TMPDIR'] = str(root / 'temporary')  # Clean Studio snapshots with this instance too.
        console, errors = [], []
        log_path = root / 'server.log'
        process = None
        try:
            with log_path.open('w') as log:
                process = subprocess.Popen([
                    executable, '--config', str(config), '--bind-addr', '127.0.0.1:0',
                    '--user-data-dir', str(root / 'user'), '--extensions-dir', str(root / 'extensions'),
                    '--disable-telemetry', '--disable-update-check', str(workspace),
                ], env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                deadline = time.monotonic() + 30
                url = None
                while time.monotonic() < deadline:
                    match = re.search(r'HTTP server listening on (http://127\.0\.0\.1:\d+/)', log_path.read_text())
                    if match:
                        url = match[1]
                        break
                    if process.poll() is not None:
                        raise AssertionError('Isolated code-server exited before listening')
                    time.sleep(.1)
                if not url:
                    raise AssertionError('Isolated code-server did not bind to loopback')
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    try:
                        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
                        page.set_default_timeout(20000)
                        page.on('console', lambda message: console.append({'type': message.type, 'text': message.text.replace(password, '[redacted]')}))
                        page.on('pageerror', lambda error: errors.append(str(error).replace(password, '[redacted]')))
                        page.goto(url + '?' + urlencode({'folder': str(workspace)}))
                        page.locator('input[type=password]').wait_for(state='visible')
                        page.locator('input[type=password]').fill(password)
                        page.locator('button[type=submit], input[type=submit]').first.click()
                        page.wait_for_selector('.monaco-workbench', timeout=60000)
                        report['authenticated'] = True
                        page.wait_for_timeout(3000)
                        trust = page.get_by_role('button', name=re.compile('Yes, I trust'))
                        if trust.count():
                            trust.click()
                        report.update(smoke(page, workspace, args.entry, args.project_source is None, artifacts))
                        if args.require_tabs:
                            assert report['authored_tabs'], 'Required authored tab interaction was not tested'
                        if args.expect_ratio:
                            width, height = map(int, args.expect_ratio.split(':'))
                            assert abs(report['dimensions']['width'] / report['dimensions']['height'] - width / height) < .002
                        assert not errors, 'Browser JavaScript errors; see diagnostics'
                        report['passed'] = True
                    except Exception:
                        if artifacts:
                            page.screenshot(path=str(artifacts / 'failure.png'))
                            report['frames'] = [{'name': frame.name, 'url': frame.url.split('?')[0][:250]} for frame in page.frames]
                        raise
                    finally:
                        browser.close()
        except Exception as error:
            # Playwright call logs can include fill() arguments on failures.
            raise RuntimeError(str(error).replace(password, '[redacted]')) from None
        finally:
            if process:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            config.unlink(missing_ok=True)
            if artifacts:
                (artifacts / 'server.log').write_text(log_path.read_text().replace(password, '[redacted]') if log_path.exists() else '')
                (artifacts / 'diagnostics.json').write_text(json.dumps({'report': report, 'errors': errors, 'console': console}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
