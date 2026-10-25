import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { randomBytes } from 'crypto';
import { StudioManifest } from './studioModel';
import { inside } from './studioSnapshot';
const escape = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;');
const json = (v: unknown) => JSON.stringify(v).replace(/</g, '\\u003c');

export function studioShell(webview: vscode.Webview, extension: vscode.Uri): string {
    const nonce = randomBytes(24).toString('hex');
    const resource = (file: string) => escape(webview.asWebviewUri(vscode.Uri.joinPath(extension, 'media', file)).toString());
    return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src ${webview.cspSource} 'unsafe-inline'; frame-src ${webview.cspSource}; img-src ${webview.cspSource} data:;">
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
<pre id="diagnostics" aria-live="polite" hidden></pre></footer><script nonce="${nonce}" src="${resource('studio.js')}"></script></body></html>`;
}

/** The deck is a separate document, not srcdoc (which inherits the shell CSP). */
export function studioFrame(webview: vscode.Webview, extension: vscode.Uri, html: string,
    output: string, snapshot: string, original: string, manifest: StudioManifest, generation: number): string {
    const resource = (file: string) => webview.asWebviewUri(vscode.Uri.file(file)).toString();
    const base = resource(snapshot) + '/';
    // Prefer build output, then snapshot assets. Original project assets are bounded by
    // localResourceRoots; no workspace-wide root is exposed.
    const resolve = (url: string): string => {
        if (/^(?:[a-z][\w+.-]*:|\/\/|#)/i.test(url)) { return url; }
        let decoded: string;
        try { decoded = decodeURIComponent(url.split(/[?#]/)[0]); } catch { return url; }
        const suffix = url.slice(url.split(/[?#]/)[0].length);
        for (const root of [output, snapshot, original]) {
            const file = path.resolve(root, decoded);
            if (inside(root, file) && fs.existsSync(file) && inside(root, fs.realpathSync(file))) { return resource(file) + suffix; }
        }
        return url;
    };
    // Keep all authored/runtime scripts inside the sandbox. Never inject acquireVsCodeApi.
    html = html.replace(/<meta\b[^>]*http-equiv=["']Content-Security-Policy["'][^>]*>/gi, '').replace(/<base\b[^>]*>/gi, '');
    const attributes = (tag: string) => tag.replace(/\b(src|href)=("|')([^"']+)\2/g, (_m, attr, quote, url) => `${attr}=${quote}${escape(resolve(url.replace(/&amp;/g, '&')))}${quote}`);
    html = html.replace(/(<script\b[^>]*>)([\s\S]*?)(<\/script>)|<[A-Za-z][^>]*>/gi,
        (tag, opening, body, closing) => opening ? attributes(opening) + body + closing : attributes(tag));
    const policy = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri ${webview.cspSource}; style-src ${webview.cspSource} 'unsafe-inline' https:; script-src ${webview.cspSource} 'unsafe-inline' https:; img-src ${webview.cspSource} https: data:; font-src ${webview.cspSource} https: data:; media-src ${webview.cspSource} https:; connect-src ${webview.cspSource} https:; frame-src https:;">`;
    html = html.replace(/<head\b[^>]*>/i, m => m + policy + `<base href="${escape(base)}">`);
    const nodes = manifest.slides.flatMap((slide, index) => slide.nodes.map(node => ({ id: node.id, renderId: node.renderId, geometry: node.geometry, slide: index })));
    const bridge = resource(path.join(extension.fsPath, 'media', 'studio-frame.js'));
    return html.replace(/<\/body>/i, `<script>window.__remarpStudio=${json({ generation, nodes })};</script><script src="${escape(bridge)}"></script></body>`);
}
