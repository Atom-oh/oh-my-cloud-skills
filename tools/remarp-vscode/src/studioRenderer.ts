import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { randomBytes } from 'crypto';
import { StudioManifest } from './studioModel';
import { assertStudioDocumentSize, boundedReplace, bundleStudioAssets, htmlTokens, mapAttributes } from './studioAssets';
const escape = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;');
const json = (v: unknown) => JSON.stringify(v).replace(/</g, '\\u003c');

export function studioShell(webview: vscode.Webview, extension: vscode.Uri, nonce = randomBytes(24).toString('hex'),
    hostChannel = randomBytes(24).toString('hex')): string {
    validateNonce(nonce);
    validateNonce(hostChannel);
    const resource = (file: string) => escape(webview.asWebviewUri(vscode.Uri.joinPath(extension, 'media', file)).toString());
    return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="${studioPolicy(nonce, webview.cspSource)}">
<meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="${resource('studio.css')}"></head>
<body><header><strong>Remarp Studio</strong><button id="design" aria-pressed="true">Design</button><button id="play" aria-pressed="false">Play</button>
<label>Zoom <select id="zoom"><option value="fit">Fit</option><option value="0.25">25%</option><option value="0.5">50%</option><option value="0.75">75%</option><option value="1">100%</option></select></label>
<button id="refresh">Refresh</button><button id="undo">Undo</button><button id="redo">Redo</button><span id="status" role="status">Building snapshot…</span></header>
<main><aside id="navigation"><h2>Slides</h2><div id="slides"></div><h2>Layers</h2><div id="layers"></div></aside>
<section id="viewport" aria-label="Slide design canvas"><div id="stage"><iframe id="preview" title="Compiler-rendered slide" sandbox="allow-scripts"></iframe><div id="overlay"></div></div></section>
<aside id="inspector"><h2>Selection</h2><p id="owner"></p><button id="source">Reveal in source</button><div id="fields"></div><h2>Slide settings</h2><div id="settings"></div><details><summary>Selected slide source / AI response</summary><label for="proposal">Remarp source</label><textarea id="proposal" spellcheck="false"></textarea><button id="propose">Preview candidate &amp; diff</button></details></aside></main>
<footer><div><label for="prompt">AI improvement request — selected slide only</label><input id="prompt" placeholder="Shorten the cards and improve spacing"><button id="copy">Copy AI request</button><button id="issue">Add /slide-fix issue</button></div>
<small>Copies the selected source to your clipboard. No AI is called automatically. Paste the returned slide source into the inspector to preview it.</small>
<div id="candidate" hidden><strong>Candidate — source unchanged</strong><button id="diff">Open diff</button><button id="apply">Apply proposal</button><button id="reject">Reject</button></div>
<pre id="diagnostics" aria-live="polite" hidden></pre></footer><script nonce="${nonce}" data-studio-channel="${hostChannel}" src="${resource('studio.js')}"></script></body></html>`;
}

/** srcdoc inherits this nonce-only script policy; sandboxing keeps the renderer opaque. */
function studioPolicy(nonce: string, shellResource?: string): string {
    const resource = shellResource ? shellResource + ' ' : '';
    return `default-src 'none'; base-uri 'none'; script-src 'nonce-${nonce}'; style-src ${resource}'unsafe-inline' data: https:; img-src ${resource}data: blob: https:; font-src data: https:; media-src data: blob: https:; connect-src data: https:; frame-src 'self';`;
}
function validateNonce(nonce: string): void {
    if (!/^[a-zA-Z0-9_-]{16,128}$/.test(nonce)) { throw new Error('Invalid Studio script nonce.'); }
}
const script = (nonce: string, source: string) => {
    assertStudioDocumentSize(4 * Math.ceil(Buffer.byteLength(source) / 3) + 256);
    return `<script nonce="${nonce}" src="data:text/javascript;base64,${Buffer.from(source).toString('base64')}"></script>`;
};

/** No renderer request depends on the code-server webview service worker. */
export function studioFrame(_webview: vscode.Webview, extension: vscode.Uri, html: string,
    output: string, snapshot: string, _original: string, manifest: StudioManifest, generation: number,
    nonce = randomBytes(24).toString('hex')): string {
    validateNonce(nonce);
    // Bundling never reads original workspace paths. The two inputs are bounded isolated
    // compiler output and source snapshots; source/map/JSON files are not renderer assets.
    const bundled = bundleStudioAssets(html, output, snapshot);
    const handlers: string[] = [];
    let handlerBytes = 0;
    const events = new Set(['onclick', 'ondblclick', 'onchange', 'oninput', 'onkeydown', 'onkeyup', 'onkeypress',
        'onmousedown', 'onmouseup', 'onmousemove', 'onmouseenter', 'onmouseleave', 'onmouseover', 'onmouseout',
        'onpointerdown', 'onpointerup', 'onpointermove', 'onpointerenter', 'onpointerleave', 'onpointercancel',
        'onfocus', 'onblur', 'onfocusin', 'onfocusout', 'onsubmit', 'onreset', 'ontouchstart', 'ontouchmove',
        'ontouchend', 'ontouchcancel', 'oncontextmenu', 'onwheel', 'onselect', 'oncut', 'oncopy', 'onpaste']);
    let elementId = 0;
    // Event attribute code stays authored renderer code. Compile it into nonce-bearing
    // listener functions, not eval/Function or a relaxation of the shell's script policy.
    const convertEvents = (tag: string): string => {
        const assignments: Array<{ event: string; code: string }> = [];
        tag = mapAttributes(tag, (name, value) => {
            if (name === 'data-remarp-studio-event') { return undefined; }
            if (/^on[a-z]+$/.test(name)) {
                if (events.has(name)) { assignments.push({ event: name, code: value }); }
                return undefined;
            }
            return value;
        });
        if (!assignments.length) { return tag; }
        const id = String(elementId++);
        for (const handler of assignments) {
            const listener = script(nonce, `(() => { const element = document.querySelector('[data-remarp-studio-event="${id}"]'); if (element) element.${handler.event} = function(event) {\n${handler.code}\n}; })();`);
            handlerBytes += Buffer.byteLength(listener);
            assertStudioDocumentSize(handlerBytes);
            handlers.push(listener);
        }
        return tag.replace(/\s*\/?>(?=$)/, ending => ` data-remarp-studio-event="${id}"${ending}`);
    };
    html = boundedReplace(bundled.html, htmlTokens, (token, block, attrs, body) => {
        if (token.startsWith('<!--')) { return token; }
        if (/^<base\b/i.test(token)) { return ''; }
        if (/^<meta\b/i.test(token)) {
            let policy = false;
            mapAttributes(token, (name, value) => { if (name === 'http-equiv' && value.toLowerCase() === 'content-security-policy') { policy = true; } return value; });
            if (policy) { return ''; }
        }
        if (block && block.toLowerCase() === 'script') {
            const opening = `<${block}${attrs}>`.replace(/\snonce(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?/gi, '');
            return opening.replace(/>$/, ` nonce="${nonce}">`) + body + `</${block}>`;
        }
        if (block) { return convertEvents(`<${block}${attrs}>`) + body + `</${block}>`; }
        return convertEvents(token);
    });
    if (!/<head\b/i.test(html)) { html = '<!doctype html><html><head></head><body>' + html + '</body></html>'; }
    const policy = `<meta http-equiv="Content-Security-Policy" content="${studioPolicy(nonce)}">`;
    const bootstrap = script(nonce, `window.__remarpStudioAssets=${json(bundled.images)};\n` + fs.readFileSync(path.join(extension.fsPath, 'media', 'studio-assets.js'), 'utf8'));
    assertStudioDocumentSize(Buffer.byteLength(html) + Buffer.byteLength(policy) + Buffer.byteLength(bootstrap));
    html = html.replace(/<head\b[^>]*>/i, head => head + policy + bootstrap);
    const nodes = manifest.slides.flatMap((slide, index) => slide.nodes.map(node => ({ id: node.id, renderId: node.renderId, geometry: node.geometry, slide: index })));
    const bridge = script(nonce, `window.__remarpStudio=${json({ generation, nodes, assetWarnings: bundled.warnings })};\n` + fs.readFileSync(path.join(extension.fsPath, 'media', 'studio-frame.js'), 'utf8'));
    assertStudioDocumentSize(Buffer.byteLength(html) + Buffer.byteLength(bridge) + handlerBytes);
    const result = html.replace(/<\/body>/i, handlers.join('') + bridge + '</body>');
    if (Buffer.byteLength(result) > 64 * 1024 * 1024) { throw new Error('Studio renderer document exceeds the 64 MiB transfer limit.'); }
    return result;
}
