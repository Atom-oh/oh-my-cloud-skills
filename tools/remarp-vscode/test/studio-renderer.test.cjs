const {test, beforeEach, afterEach} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const Module = require('node:module');
const {bundleStudioAssets} = require('../out/studioAssets');
const oldLoad = Module._load;
const uri = file => ({fsPath: file});
Module._load = function(name, ...args) {
    return name === 'vscode' ? {Uri: {file: uri, joinPath: (base, ...pieces) => uri(path.join(base.fsPath, ...pieces))}} : oldLoad.call(this, name, ...args);
};
const {studioShell, studioFrame} = require('../out/studioRenderer');
Module._load = oldLoad;
let root, output, snapshot, original;
const nonce = '1234567890abcdef1234567890abcdef';
const extension = uri(path.resolve(__dirname, '..'));
const webview = {cspSource: 'https://resources.example', asWebviewUri: file => ({toString: () => `https://resources.example${file.fsPath}`})};
const document = body => `<!doctype html><html><head></head><body>${body}</body></html>`;
function write(relative, value, base = output) {const file = path.join(base, relative); fs.mkdirSync(path.dirname(file), {recursive: true}); fs.writeFileSync(file, value); return file;}
function bundle(html) {return bundleStudioAssets(document(html), output, snapshot);}
function frame(html) {return studioFrame(webview, extension, document(html), output, snapshot, original, {slides: []}, 7, nonce);}
function data(url) {return Buffer.from(url.replace(/#.*$/, '').split(',')[1], 'base64').toString();}
function resource(html, attr = 'src') {return new RegExp(`\\b${attr}="([^"]+)"`).exec(html)[1];}
beforeEach(() => {root = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-assets-')); output = path.join(root, 'output'); snapshot = path.join(root, 'snapshot'); original = path.join(root, 'original'); [output, snapshot, original].forEach(p => fs.mkdirSync(p));});
afterEach(() => fs.rmSync(root, {recursive: true, force: true}));

test('local scripts are data URLs and never depend on a VS Code resource URL', () => {
    write('common/runtime.js', 'window.runtimeLoaded=true;');
    const html = frame('<script src="./common/runtime.js"></script>');
    assert.match(html, /src="data:text\/javascript;base64,/);
    assert.doesNotMatch(html, /vscode-resource|resources\.example|acquireVsCodeApi/);
    assert.ok([...html.matchAll(/<script\b[^>]*>/g)].every(match => match[0].includes(`nonce="${nonce}"`)));
});
test('frame and shell share nonce-only CSP without unsafe-inline script or same-origin sandbox', () => {
    const shell = studioShell(webview, extension, nonce), html = frame('<script nonce=wrong>window.inline=true;</script>');
    for (const text of [shell, html]) {
        assert.match(text, new RegExp(`script-src 'nonce-${nonce}';`));
        assert.doesNotMatch(text, /script-src[^;]*(?:unsafe-inline|https:|data:)/);
        assert.match(text, /base-uri 'none'/);
    }
    assert.match(shell, /sandbox="allow-scripts"/); assert.doesNotMatch(shell, /allow-same-origin/);
    assert.doesNotMatch(html, /nonce="?wrong/);
});
test('a malicious nonce cannot alter HTML or the CSP', () => {
    assert.throws(() => studioShell(webview, extension, '" unsafe-inline'), /nonce/);
    assert.throws(() => studioFrame(webview, extension, '', output, snapshot, original, {slides: []}, 1, '<script>'), /nonce/);
});
test('authored base and CSP cannot replace renderer policy; inline scripts get the nonce', () => {
    const html = frame('<base href="https://example.invalid/"><META HTTP-EQUIV=Content-Security-Policy content="script-src *"><script>window.x="<base>";</script>');
    assert.doesNotMatch(html, /<base href|script-src \*/);
    assert.match(html, /window.x="<base>"/);
    assert.equal((html.match(/http-equiv="Content-Security-Policy"/g) || []).length, 1);
});
test('CSS imports and font/image URLs resolve relative to their own stylesheet', () => {
    write('css/main.css', '@import "parts/colors.css"; .logo {background:url("../images/logo.png")}');
    write('css/parts/colors.css', '@font-face {font-family:Local; src:url(../../fonts/local.woff2)}');
    write('images/logo.png', 'PNG'); write('fonts/local.woff2', 'FONT');
    const css = data(resource(bundle('<link rel="stylesheet" href="css/main.css">').html, 'href'));
    assert.match(css, /background:url\("data:image\/png;base64,UE5H"\)/);
    const nested = data(/@import url\("([^"]+)"\)/.exec(css)[1]);
    assert.match(nested, /src:url\("data:font\/woff2;base64,Rk9OVA=="\)/);
});
test('CSS comments are not asset requests and cyclic imports fail clearly', () => {
    write('a.css', '/* url(private.txt) */ @import url(b.css);'); write('b.css', '@import url(a.css);');
    assert.throws(() => bundle('<link rel=stylesheet href=a.css>'), /Cyclic/);
    write('a.css', '/* url(private.txt) */ body {color:red}');
    assert.equal(bundle('<link rel=stylesheet href=a.css>').warnings.length, 0);
});
test('inline styles, style blocks and HTML entity URLs are bundled', () => {
    write('img/a&b.png', 'A');
    const result = bundle('<img src="img/a&amp;b.png"><div style="background:url(img/a&amp;b.png)"></div><style>.x{background:url("img/a&b.png")}</style>');
    assert.equal((result.html.match(/data:image\/png;base64,QQ==/g) || []).length, 3);
    assert.equal(result.warnings.length, 0);
});
test('quoted > attributes, unquoted URLs and script-body markup are handled without rewriting JS', () => {
    write('a.png', 'A'); write('r.js', '// loaded');
    const result = bundle('<img title="greater > less" src=a.png><script src=r.js>const x = \'<img src="private.png">\';</script>');
    assert.match(result.html, /title="greater > less"/); assert.match(result.html, /src="data:image\/png/);
    assert.match(result.html, /const x = '<img src="private.png">'/); assert.equal(result.warnings.length, 0);
});
test('finite runtime image map includes staged icons but not sources, JSON, maps or unrelated scripts', () => {
    write('icons/local.svg', '<svg></svg>', snapshot); write('private.md', 'SECRET SOURCE', snapshot);
    write('credentials.json', 'SECRET JSON', snapshot); write('private.js', 'SECRET SCRIPT', snapshot);
    write('studio.json', 'SECRET MAP'); write('bundle.js.map', 'SECRET SOURCEMAP');
    const result = bundle('<p>deck</p>');
    assert.deepEqual(Object.keys(result.images), ['icons/local.svg']);
    assert.doesNotMatch(JSON.stringify(result), /SECRET/);
});
test('original project files are never a fallback for missing staged resources', () => {
    write('secret.png', 'ORIGINAL SECRET', original); write('secret.js', 'ORIGINAL SCRIPT', original);
    const html = frame('<img src="secret.png">');
    assert.doesNotMatch(html, /T1JJR0lOQUwgU0VDUkVU/);
    assert.throws(() => frame('<script src="secret.js"></script>'), /not staged/);
});
test('optional missing/outside media never blanks the whole deck, and warnings are bounded', () => {
    const result = bundle('<video src="../outside/private.mp4" poster="missing.jpg"></video>' + Array.from({length: 30}, (_, i) => `<img src="missing${i}.png">`).join(''));
    assert.equal(result.warnings.length, 12); assert.ok(result.warnings.every(w => w.length < 250));
    assert.match(result.html, /src="data:application\/octet-stream;base64,"/);
    assert.doesNotMatch(result.html, /src="\.\.\//);
});
test('required script/style traversal, absolute paths and unsupported files fail closed', () => {
    write('private.md', 'PRIVATE');
    for (const url of ['../secret.js', '%2e%2e/secret.js', '/etc/secret.js', 'private.md', 'a%00.js', 'a%5cb.js']) {
        assert.throws(() => bundle(`<script src="${url}"></script>`), /Cannot bundle Studio asset/);
    }
    assert.throws(() => bundle('<link rel=stylesheet href=missing.css>'), /not staged/);
});
test('symlink files and symlink directory components cannot expose files', () => {
    write('secret.js', 'SECRET', original); write('secret.png', 'SECRET', original);
    fs.symlinkSync(path.join(original, 'secret.js'), path.join(output, 'linked.js'));
    fs.symlinkSync(original, path.join(output, 'linked'));
    assert.throws(() => bundle('<script src="linked.js"></script>'), /symlinks/);
    assert.throws(() => bundle('<script src="linked/secret.js"></script>'), /symlinks/);
    assert.deepEqual(Object.keys(bundle('<p>deck</p>').images), []);
});
test('oversized optional resources fail clearly instead of silently exhausting memory', () => {
    const file = write('huge.png', ''); fs.truncateSync(file, 32 * 1024 * 1024 + 1);
    assert.throws(() => bundle('<img src="huge.png">'), /32 MiB/);
});
test('too many renderer resources fail with an explicit bound', () => {
    for (let i = 0; i < 2001; i++) write(`images/${i}.png`, '');
    assert.throws(() => bundle('<p>deck</p>'), /2,000 file limit/);
});
test('external HTTPS/data resources remain external without host fetching or recursive HTML bundling', () => {
    write('linked.html', 'PRIVATE HTML');
    const result = bundle('<img src="https://example.invalid/a.png"><img src="data:image/png;base64,QQ=="><a href="linked.html">link</a>');
    assert.match(result.html, /https:\/\/example.invalid\/a.png/); assert.match(result.html, /href="linked.html"/);
    assert.doesNotMatch(JSON.stringify(result), /PRIVATE HTML/);
});
test('SVG fragments, srcset candidates and output-over-snapshot precedence are preserved', () => {
    write('symbol.svg', '<svg>OUTPUT</svg>'); write('symbol.svg', '<svg>SNAPSHOT</svg>', snapshot); write('second.png', 'TWO');
    const result = bundle('<svg><use href="symbol.svg#icon"></use></svg><img srcset="second.png 1x, symbol.svg 2x">');
    assert.match(result.html, /base64,[^"]+#icon/); assert.match(result.html, /base64,VFdP 1x/);
    assert.match(data(result.images['symbol.svg']), /OUTPUT/);
});
test('nested documents are stripped rather than given access to local resources', () => {
    const result = bundle('<iframe src="linked.html" srcdoc="hello"></iframe><object data="linked.html"></object><embed src="linked.html">');
    assert.doesNotMatch(result.html, /src=|srcdoc=|data=/);
    assert.ok(result.warnings.some(message => message.includes('iframe document is not supported')));
});
test('runtime image assignments resolve only finite bundle entries, without a host bridge', () => {
    class Element {setAttribute(name, value) {this[name + 'Attribute'] = value;}}
    class HTMLImageElement extends Element {get src() {return this.value;} set src(value) {this.value = value;}}
    const window = {__remarpStudioAssets: {'icons/a.png': 'data:image/png;base64,QQ=='}};
    const context = {window, Element, HTMLImageElement, URL, console: {warn() {}}};
    vm.runInNewContext(fs.readFileSync(path.join(extension.fsPath, 'media/studio-assets.js'), 'utf8'), context);
    const img = new HTMLImageElement(); img.src = './icons/a.png'; assert.equal(img.src, 'data:image/png;base64,QQ==');
    img.setAttribute('src', 'icons/a.png'); assert.equal(img.srcAttribute, 'data:image/png;base64,QQ==');
    img.src = 'private.png'; assert.equal(img.src, 'data:application/octet-stream;base64,');
    img.src = 'https://example.invalid/a.png'; assert.equal(img.src, 'https://example.invalid/a.png');
    assert.equal(window.__remarpStudioAssets, undefined);
});
test('host-channel capability appears on the shell script only, never in the authored renderer', () => {
    const channel = 'HostChannelSecret1234567890';
    const shell = studioShell(webview, extension, nonce, channel);
    assert.match(shell, new RegExp(`<script nonce="${nonce}" data-studio-channel="${channel}"`));
    assert.equal((shell.match(new RegExp(channel, 'g')) || []).length, 1);
    assert.doesNotMatch(frame('<p>slide</p>'), new RegExp(channel));
    assert.throws(() => studioShell(webview, extension, nonce, '"><script>'), /nonce/);
});
test('authored onclick becomes a nonce script listener preserving this/event and return false', () => {
    const html = frame('<button onclick="this.label = &quot;Clicked&quot;; this.received = event; return false">Click</button>');
    assert.doesNotMatch(html, /onclick=/); assert.match(html, /data-remarp-studio-event="0"/);
    const scripts = [...html.matchAll(/<script[^>]*src="([^"]+)"[^>]*>/g)].map(match => data(match[1]));
    const listener = scripts.find(source => source.includes('[data-remarp-studio-event="0"]'));
    assert.ok(listener); assert.doesNotMatch(listener, /eval\(|new Function/);
    const element = {}, event = {type: 'click'};
    vm.runInNewContext(listener, {document: {querySelector: () => element}});
    assert.equal(element.onclick(event), false); assert.equal(element.label, 'Clicked'); assert.equal(element.received, event);
});
test('event-handler closing-script text cannot escape the nonce data script', () => {
    const html = frame('<button onclick="this.label = \'&lt;/script>&lt;script>alert(1)&lt;/script>\'">Click</button>');
    assert.doesNotMatch(html, /<script>alert\(1\)/);
    const scripts = [...html.matchAll(/<script[^>]*src="([^"]+)"[^>]*>/g)].map(match => data(match[1]));
    const element = {};
    vm.runInNewContext(scripts.find(source => source.includes('[data-remarp-studio-event="0"]')), {document: {querySelector: () => element}});
    element.onclick({}); assert.equal(element.label, '</script><script>alert(1)</script>');
});
test('deep asset trees and CSS chains fail within explicit nesting limits', () => {
    const nested = Array.from({length: 66}, () => 'd').join('/'); write(`${nested}/a.png`, 'A');
    assert.throws(() => bundle('<p>deck</p>'), /64-level limit/);
    fs.rmSync(path.join(output, 'd'), {recursive: true});
    for (let i = 0; i < 34; i++) write(`a${i}.css`, `@import "a${i + 1}.css";`);
    assert.throws(() => bundle('<link rel=stylesheet href=a0.css>'), /32-level limit/);
});
test('small recursive CSS fan-out is bounded before expanded cache allocation', () => {
    write('expand0.css', 'body{color:red}');
    for (let i = 1; i < 19; i++) write(`expand${i}.css`, `@import "expand${i - 1}.css";@import "expand${i - 1}.css";`);
    assert.throws(() => bundle('<link rel=stylesheet href=expand18.css>'), /64 MiB transfer limit/);
});
test('repeated HTML asset references have an incremental expanded document budget', () => {
    write('large.svg', '<svg>' + ' '.repeat(1024 * 1024) + '</svg>');
    assert.throws(() => bundle('<img src="large.svg">'.repeat(80)), /64 MiB transfer limit/);
});
