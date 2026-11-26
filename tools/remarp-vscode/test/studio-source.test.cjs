const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const Module = require('node:module');
let documents, opened, dialogs, picked, warnings, errors, diagnostics, commands;
const disposable = () => ({ dispose() {} });
const uri = (file, scheme = 'file') => ({ fsPath: file, scheme, toString: () => `${scheme}://${file}` });
const vscode = {
    workspace: {
        get textDocuments() { return documents; },
        workspaceFolders: [{ uri: uri('/project') }], isTrusted: true,
        registerTextDocumentContentProvider: disposable,
        openTextDocument: async file => {
            opened.push(file);
            const doc = documents.find(d => d.uri.toString() === file.toString());
            if (!doc) throw new Error('File not found');
            return doc;
        }
    },
    window: {
        activeTextEditor: undefined,
        showOpenDialog: async options => { dialogs.push(options); return picked; },
        showWarningMessage: message => warnings.push(message),
        showErrorMessage: message => errors.push(message),
        createOutputChannel: () => ({ appendLine: line => diagnostics.push(line), ...disposable() })
    },
    commands: { registerCommand: (name, callback) => { commands.set(name, callback); return disposable(); } }
};
const load = Module._load;
Module._load = function (name, ...args) { return name === 'vscode' ? vscode : load.call(this, name, ...args); };
const { isRemarpDocument, isStudioSource, selectStudioSource } = require('../out/studioSource');
const { registerStudio } = require('../out/studio');
Module._load = load;
function document(name, text = '---\nremarp: true\n---\n# Deck', languageId = 'markdown', scheme = 'file') {
    const doc = { fileName: `/project/${name}`, uri: uri(`/project/${name}`, scheme), languageId, isDirty: true, getText: () => text };
    documents.push(doc);
    return doc;
}
beforeEach(() => {
    documents = []; opened = []; dialogs = []; picked = undefined; warnings = []; errors = []; diagnostics = []; commands = new Map();
    vscode.window.activeTextEditor = undefined; vscode.workspace.isTrusted = true;
});
for (const [name, text] of [
    ['01-overview.md', '---\nremarp: true\nratio: "16:9"\n---\n# Overview'],
    ['quoted.md', '---\r\nremarp: "true" # presentation\r\n---\r\n# Deck'],
    ['deck.remarp.md', '# Deck'], ['_presentation.md', '---\ntitle: Deck\n---'], ['_presentation.remarp.md', '# Deck']
]) {
    test(`Studio and Preview share recognition for ${name} before language conversion`, () => {
        const doc = document(name, text);
        assert.equal(isRemarpDocument(doc), true);
        assert.equal(isStudioSource(doc), true);
    });
}
test('active unsaved Markdown with Remarp frontmatter is used without opening or saving', async () => {
    const doc = document('01-overview.md'); vscode.window.activeTextEditor = { document: doc };
    assert.equal(await selectStudioSource(), doc);
    assert.deepEqual(opened, []); assert.deepEqual(dialogs, []);
});
test('explicit URI wins over the active source', async () => {
    const active = document('active.remarp.md'), selected = document('selected.md');
    vscode.window.activeTextEditor = { document: active };
    assert.equal(await selectStudioSource(selected.uri), selected);
    assert.deepEqual(opened, [selected.uri]); assert.deepEqual(dialogs, []);
});
test('one unambiguous open source is found when the webview owns focus', async () => {
    const doc = document('deck.md'); document('README.md', '# General docs');
    assert.equal(await selectStudioSource(), doc); assert.deepEqual(dialogs, []);
});
test('multiple sources use a labelled file picker rather than an arbitrary open deck', async () => {
    document('one.md'); const chosen = document('two.md'); picked = [chosen.uri];
    assert.equal(await selectStudioSource(), chosen);
    assert.equal(dialogs.length, 1); assert.equal(dialogs[0].canSelectMany, false);
    assert.equal(dialogs[0].openLabel, 'Open Design Studio'); assert.deepEqual(dialogs[0].filters, { 'Remarp Markdown': ['md'] });
});
test('no active source offers a picker and cancellation is quiet', async () => {
    assert.equal(await selectStudioSource(), undefined); assert.equal(dialogs.length, 1); assert.deepEqual(opened, []);
});
test('explicit unsupported or remote documents are rejected without fallback', async () => {
    const plain = document('README.md', '# Nothing to compile'), remote = document('remote.remarp.md', '# Deck', 'remarp', 'https');
    assert.equal(isStudioSource(plain), false); assert.equal(isStudioSource(remote), false);
    await assert.rejects(selectStudioSource(plain.uri), /not Remarp source/);
    await assert.rejects(selectStudioSource(remote.uri), /local/);
    assert.deepEqual(opened, [plain.uri]); assert.deepEqual(dialogs, []);
});
test('frontmatter-like body text does not mark a normal Markdown file as Remarp', () => {
    assert.equal(isRemarpDocument(document('README.md', '# Guide\nremarp: true')), false);
    assert.equal(isRemarpDocument(document('off.md', '---\nremarp: false\n---')), false);
});
test('command forwards the explicit URI and reports missing compiler without creating a session', async () => {
    const active = document('active.md'), selected = document('selected.md'), observed = [];
    vscode.window.activeTextEditor = { document: active };
    registerStudio({ subscriptions: [] }, doc => { observed.push(doc); return null; });
    await commands.get('remarp.studio')(selected.uri);
    assert.deepEqual(observed, [selected]); assert.match(errors[0], /buildScriptPath/);
});
test('command respects trust before opening files or prompting', async () => {
    vscode.workspace.isTrusted = false;
    registerStudio({ subscriptions: [] }, () => { throw new Error('Should not reach compiler'); });
    await commands.get('remarp.studio')(uri('/project/deck.md'));
    assert.equal(warnings.length, 1); assert.deepEqual(opened, []); assert.deepEqual(dialogs, []);
});
test('command logs and displays an invalid source or file-open failure', async () => {
    registerStudio({ subscriptions: [] }, () => null);
    await commands.get('remarp.studio')(uri('/project/missing.md'));
    assert.match(errors[0], /File not found/); assert.match(diagnostics[0], /File not found/);
});
