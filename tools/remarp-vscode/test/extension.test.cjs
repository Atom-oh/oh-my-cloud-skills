const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const Module = require('node:module');
const childProcess = require('node:child_process');

let root, commands, errors, panels, calls, saves, onSave, output;
const disposable = () => ({ dispose() {} });
class Position { constructor(line, character) { Object.assign(this, { line, character }); } }
class Range { constructor(start, end) { Object.assign(this, { start, end }); } }
class Selection extends Range { get active() { return this.end; } }
const uri = file => ({ fsPath: file, scheme: 'file', toString: () => `file://${file}` });
const vscode = {
    Position, Range, Selection,
    Uri: { file: uri, joinPath: (base, ...parts) => uri(path.join(base.fsPath, ...parts)) },
    EventEmitter: class { event = disposable; fire() {} },
    TreeItem: class { constructor(label) { this.label = label; } },
    ThemeIcon: class {}, TreeItemCollapsibleState: { None: 0 },
    ViewColumn: { Beside: 2 }, TextEditorRevealType: { InCenter: 1 },
    WorkspaceEdit: class { edits = []; delete(_uri, range) { this.edits.push(range); } },
    commands: { registerCommand: (name, fn) => { commands.set(name, fn); return disposable(); } },
    languages: { setTextDocumentLanguage: disposable, registerCompletionItemProvider: disposable },
    workspace: {
        isTrusted: true, textDocuments: [], workspaceFolders: [],
        getWorkspaceFolder: () => undefined,
        getConfiguration: () => ({ get: (key, fallback) => key === 'buildScriptPath' ? path.join(root, 'compiler.py') : fallback }),
        onDidOpenTextDocument: disposable, onDidChangeTextDocument: disposable,
        onDidSaveTextDocument: fn => { onSave.push(fn); return disposable(); },
        openTextDocument: async file => document(typeof file === 'string' ? file : file.fsPath, fs.readFileSync(typeof file === 'string' ? file : file.fsPath, 'utf8')),
        applyEdit: async edit => {
            const doc = vscode.window.activeTextEditor.document;
            for (const range of edit.edits.reverse()) {
                doc.text = doc.text.slice(0, doc.offsetAt(range.start)) + doc.text.slice(doc.offsetAt(range.end));
            }
            return true;
        }
    },
    window: {
        showWarningMessage: msg => errors.push(msg), showErrorMessage: msg => errors.push(msg),
        showInformationMessage: disposable, createOutputChannel: () => output,
        registerTreeDataProvider: disposable, onDidChangeActiveTextEditor: disposable,
        onDidChangeTextEditorSelection: disposable,
        createWebviewPanel: (_type, title, _column, options) => {
            const panel = { title, options, reveal() {}, onDidDispose: disposable, dispose() {},
                webview: { html: '', cspSource: 'https://resources.example',
                    asWebviewUri: file => ({ toString: () => `https://resources.example${encodeURI(file.fsPath)}` }),
                    onDidReceiveMessage: disposable, postMessage: disposable } };
            panels.push(panel);
            return panel;
        }
    }
};
function document(fileName, text = '# First', dirty = false) {
    const doc = { fileName, uri: uri(fileName), text, isDirty: dirty, languageId: 'remarp',
        getText() { return this.text; },
        offsetAt(p) { return this.text.split('\n').slice(0, p.line).reduce((n, line) => n + line.length + 1, 0) + p.character; },
        positionAt(offset) { const lines = this.text.slice(0, offset).split('\n'); return new Position(lines.length - 1, lines.at(-1).length); },
        async save() { saves.push(fileName); fs.writeFileSync(fileName, this.text); this.isDirty = false; onSave.forEach(fn => fn(this)); return true; } };
    return doc;
}
function active(doc) {
    vscode.workspace.textDocuments.push(doc);
    vscode.window.activeTextEditor = { document: doc, selection: new Selection(new Position(0, 0), new Position(0, 0)), revealRange() {} };
}
const originalLoad = Module._load;
Module._load = function(name, ...args) { return name === 'vscode' ? vscode : originalLoad.call(this, name, ...args); };
const extension = require('../out/extension');
const { RemarpPreviewPanel } = require('../out/preview');
const { SlideOutlineProvider } = require('../out/outline');
const { CompiledPreviewRenderer } = require('../out/compiledPreview');
Module._load = originalLoad;
const originalExec = childProcess.execFile;
beforeEach(() => {
    root = fs.mkdtempSync(path.join(os.tmpdir(), 'remarp-extension-'));
    fs.writeFileSync(path.join(root, 'compiler.py'), '');
    commands = new Map(); errors = []; panels = []; calls = []; saves = []; onSave = [];
    output = { lines: [], shown: false, appendLine(line) { this.lines.push(line); }, show() { this.shown = true; }, dispose() {} };
    vscode.workspace.isTrusted = true; vscode.workspace.textDocuments = [];
    RemarpPreviewPanel.currentPanel = undefined;
    childProcess.execFile = (_program, args, options, done) => {
        calls.push({ args, options, saves: [...saves] });
        const target = args[2];
        const generated = path.extname(target) === '.md' ? path.join(path.dirname(target), 'slides/default.html') : path.join(target, 'index.html');
        queueMicrotask(() => done(null, `Generated: ${generated}`, ''));
    };
    extension.activate({ subscriptions: [], extensionUri: uri(path.resolve(__dirname, '..')) });
});
afterEach(() => { childProcess.execFile = originalExec; fs.rmSync(root, { recursive: true, force: true }); });

for (const marker of ['_presentation.md', '_presentation.remarp.md']) {
    test(`recognizes ${marker} and builds its project after saving all dirty sources`, async () => {
        const main = document(path.join(root, marker), '---\ntitle: Training\n---', true);
        assert.equal(extension.isRemarpDocument(main), true);
        fs.writeFileSync(main.fileName, main.text);
        const block = document(path.join(root, '01.remarp.md'), '# Saved changes', true);
        active(block); vscode.workspace.textDocuments.push(main);
        await commands.get('remarp.build')();
        assert.equal(calls.length, 1, 'save events must not duplicate the build');
        assert.deepEqual(calls[0].args.slice(1), ['build', root]);
        assert.deepEqual(new Set(calls[0].saves), new Set([main.fileName, block.fileName]));
    });
}
test('standalone build waits for save and reports compiler exit failures', async () => {
    const doc = document(path.join(root, 'single.remarp.md'), '# Changed', true); active(doc);
    childProcess.execFile = (_program, args, _options, done) => {
        calls.push(args); assert.equal(fs.readFileSync(doc.fileName, 'utf8'), '# Changed');
        queueMicrotask(() => done(Object.assign(new Error('exit 1'), { code: 1 }), '', 'CRITICAL invalid slide'));
    };
    await commands.get('remarp.build')();
    assert.deepEqual(calls[0].slice(1), ['build', doc.fileName]);
    assert.ok(output.shown && errors.length);
    assert.match(output.lines.join('\n'), /CRITICAL/);
});
test('failed saving and untrusted workspaces cannot execute builds', async () => {
    const doc = document(path.join(root, 'one.remarp.md'), '# One', true); active(doc);
    doc.save = async () => false;
    await commands.get('remarp.build')();
    assert.equal(calls.length, 0); assert.ok(errors.length);
    vscode.workspace.isTrusted = false; doc.isDirty = false; errors = [];
    await commands.get('remarp.build')();
    assert.equal(calls.length, 0); assert.ok(errors.length);
});
test('compiled command displays actual project HTML and blocks untrusted builds', async () => {
    const run = commands.get('remarp.previewCompiled'); assert.equal(typeof run, 'function');
    fs.writeFileSync(path.join(root, '_presentation.md'), '---\ntitle: Deck\n---');
    fs.writeFileSync(path.join(root, 'index.html'), '<html><head></head><body>COMPILED CANVAS<script src="./common/slide-framework.js"></script></body></html>');
    active(document(path.join(root, '01.remarp.md')));
    await run();
    assert.match(panels.at(-1).webview.html, /COMPILED CANVAS/);
    assert.match(panels.at(-1).title, /Compiled/);
    assert.ok(panels.at(-1).options.enableScripts);
    assert.ok(panels.at(-1).options.localResourceRoots.some(u => u.fsPath === root));
    vscode.workspace.isTrusted = false; calls = []; panels = [];
    await run(); assert.equal(calls.length, 0); assert.equal(panels.length, 0);
});
test('standalone compiled preview opens slides/default.html and exposes missing output', async () => {
    const run = commands.get('remarp.previewCompiled'); assert.equal(typeof run, 'function');
    active(document(path.join(root, 'one.remarp.md')));
    await run(); assert.equal(panels.length, 0); assert.ok(errors.length);
    fs.mkdirSync(path.join(root, 'slides'));
    fs.writeFileSync(path.join(root, 'slides/default.html'), '<html><head></head><body>STANDALONE</body></html>');
    await run(); assert.match(panels.at(-1).webview.html, /STANDALONE/);
});
test('activated command uses the real compiler, saved global footer and encoded project URI', async () => {
    const project = path.join(root, 'deck & spaces'); fs.mkdirSync(project);
    const main = document(path.join(project, '_presentation.md'), '---\nremarp: true\ntitle: Deck\nratio: "16:9"\ntheme:\n  footer: SavedGlobalFooter\n---', true);
    fs.writeFileSync(main.fileName, main.text.replace('SavedGlobalFooter', 'OLD FOOTER'));
    active(document(path.join(project, '01.remarp.md'), '---\nremarp: true\n---\n## Saved source title', true));
    vscode.workspace.textDocuments.push(main);
    const config = vscode.workspace.getConfiguration;
    vscode.workspace.getConfiguration = () => ({ get: () => path.resolve(__dirname, '../../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py') });
    childProcess.execFile = originalExec;
    try {
        await commands.get('remarp.previewCompiled')();
        assert.deepEqual(errors, []);
        const html = panels.at(-1).webview.html;
        assert.match(html, /Saved source title/); assert.match(html, /SavedGlobalFooter/);
        assert.doesNotMatch(html, /OLD FOOTER/);
        assert.match(html, /<base href="https:\/\/resources\.example[^"]+\/deck%20&amp;%20spaces\/">/);
        for (const file of ['index.html', 'toc.html', '01.html', 'common/slide-framework.js']) {
            assert.ok(fs.existsSync(path.join(project, file)), file);
        }
        active(document(path.join(root, 'single.remarp.md'), '## Standalone source', true));
        await commands.get('remarp.previewCompiled')();
        assert.match(panels.at(-1).webview.html, /Standalone source/);
        assert.match(panels.at(-1).webview.html, /\/slides\/">/);
    } finally { vscode.workspace.getConfiguration = config; }
});
for (const code of [1, 2]) {
    test(`compiled preview never opens stale output after compiler exit ${code}`, async () => {
        active(document(path.join(root, 'one.remarp.md')));
        fs.mkdirSync(path.join(root, 'slides'));
        fs.writeFileSync(path.join(root, 'slides/default.html'), '<html><head></head><body>STALE</body></html>');
        childProcess.execFile = (_program, _args, _options, done) =>
            queueMicrotask(() => done(Object.assign(new Error(`exit ${code}`), { code }), '', 'Rejected source'));
        await commands.get('remarp.previewCompiled')();
        assert.equal(panels.length, 0); assert.ok(errors.length && output.shown);
    });
}
test('compiled preview reads newly generated bytes rather than an open HTML buffer', async () => {
    active(document(path.join(root, 'one.remarp.md')));
    fs.mkdirSync(path.join(root, 'slides'));
    fs.writeFileSync(path.join(root, 'slides/default.html'), '<html><head></head><body>NEW BYTES</body></html>');
    const open = vscode.workspace.openTextDocument;
    vscode.workspace.openTextDocument = async file => document(file.fsPath, '<html><head></head><body>STALE BUFFER</body></html>');
    try { await commands.get('remarp.previewCompiled')(); }
    finally { vscode.workspace.openTextDocument = open; }
    assert.match(panels.at(-1).webview.html, /NEW BYTES/);
});
test('compiled HTML resolves assets through a webview base, CSP first, without edit controls', () => {
    const panel = vscode.window.createWebviewPanel('', '', 2, {});
    const html = new CompiledPreviewRenderer(panel, uri(root)).render(document(path.join(root, 'slides', 'default.html'),
        '<html><head><base href="https://wrong.example/"><script src="./common/slide-framework.js"></script></head><body><img src="./common/a%20b.png"><style>.x{background:url(../images/a.png)}</style><script>window.canvasReady=true</script></body></html>'));
    assert.match(html, /<base href="https:\/\/resources\.example[^"]+\/slides\/"/);
    assert.ok(html.indexOf('Content-Security-Policy') < html.indexOf('<script'));
    assert.doesNotMatch(html, /wrong\.example|remarp-slide-edit-btn|edit-mode\.js|canvas-editor\.js|acquireVsCodeApi/);
    assert.match(html, /window.canvasReady=true/);
});
for (const [text, target, expected] of [
    ['# Revenue <!-- issue: shorten -->', 'shorten', '# Revenue '],
    ['# A <!-- issue: first --> B <!-- issue: second --> C\r\nTail', 'second', '# A <!-- issue: first --> B  C\r\nTail'],
    ['# A\r\n<!-- issue: remove -->', 'remove', '# A\r\n'],
]) {
    test(`annotation removal preserves exact surrounding bytes: ${target} / ${text.length}`, async () => {
        const doc = document(path.join(root, 'issues.remarp.md'), text); active(doc);
        RemarpPreviewPanel.createOrShow(uri(root), doc);
        await RemarpPreviewPanel.currentPanel._removeIssueFromSlide(target, 0);
        assert.equal(doc.getText(), expected);
    });
}
test('preview, outline and navigation share fence-aware CRLF boundaries', async () => {
    const text = ['---', 'remarp: true', '---', '# One', '````md', '---', '```', '````', '~~~', '---', '~~~', '---', '# Two'].join('\r\n');
    const doc = document(path.join(root, 'fences.remarp.md'), text); active(doc);
    RemarpPreviewPanel.createOrShow(uri(root), doc);
    assert.equal(RemarpPreviewPanel.currentPanel._parseSlides().length, 2);
    assert.equal((await new SlideOutlineProvider().getChildren()).length, 2);
    vscode.window.activeTextEditor.selection = new Selection(new Position(3, 0), new Position(3, 0));
    await commands.get('remarp.nextSlide')();
    assert.equal(vscode.window.activeTextEditor.selection.active.line, 12);
    await commands.get('remarp.prevSlide')();
    assert.equal(vscode.window.activeTextEditor.selection.active.line, 3);
});
test('text preview is labeled approximate and disables scripts without workspace trust', () => {
    vscode.workspace.isTrusted = false;
    RemarpPreviewPanel.createOrShow(uri(root), document(path.join(root, 'one.remarp.md')));
    assert.match(panels[0].title, /Approximate/); assert.equal(panels[0].options.enableScripts, false);
});

test('named standalone block must preview its newly generated output', async () => {
    const doc = document(path.join(root, 'named.remarp.md'), '---\nremarp: true\n---\n<!-- block: lesson -->\n## CURRENT LESSON\n', true);
    active(doc);
    fs.mkdirSync(path.join(root, 'slides'));
    fs.writeFileSync(path.join(root, 'slides/default.html'), '<html><head></head><body>STALE OTHER DECK</body></html>');
    vscode.workspace.getConfiguration = () => ({ get: () => path.resolve(__dirname, '../../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py') });
    childProcess.execFile = originalExec;
    await commands.get('remarp.previewCompiled')();
    assert.deepEqual(errors, []);
    assert.ok(fs.existsSync(path.join(root, 'slides/lesson.html')));
    assert.match(panels.at(-1).webview.html, /CURRENT LESSON/);
});
test('save compiler-recognized commented frontmatter sources', async () => {
    fs.writeFileSync(path.join(root, '_presentation.md'), '---\nremarp: true\nratio: "16:9"\n---\n');
    const first = document(path.join(root, '01.remarp.md'), '## First source\n', true);
    const other = document(path.join(root, '02.md'), '---\nremarp: true # valid YAML\n---\n## CURRENT SAVED SOURCE\n', true);
    fs.writeFileSync(other.fileName, other.text.replace('CURRENT SAVED SOURCE','OLD DISK SOURCE'));
    active(first);vscode.workspace.textDocuments.push(other);
    vscode.workspace.getConfiguration = () => ({ get: () => path.resolve(__dirname, '../../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py') });
    childProcess.execFile=originalExec;
    await commands.get('remarp.previewCompiled')();
    assert.deepEqual(errors, []);
    assert.equal(other.isDirty, false);
});
