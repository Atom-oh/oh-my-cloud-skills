// Render the actual Preview implementation without an Extension Development Host.
const path = require('node:path');
const Module = require('node:module');

let resourceBase = '';
const disposable = () => ({ dispose() {} });
const uri = file => ({ fsPath: file, toString: () => `file://${file}` });
const vscode = {
    Uri: { file: uri, joinPath: (base, ...parts) => uri(path.join(base.fsPath, ...parts)) },
    ViewColumn: { Beside: 2 },
    workspace: { isTrusted: true, getWorkspaceFolder: () => undefined },
    window: {
        createWebviewPanel: () => ({
            onDidDispose: disposable,
            webview: {
                html: '', onDidReceiveMessage: disposable,
                asWebviewUri: file => ({ toString: () => resourceBase + '/files' + encodeURI(file.fsPath) })
            }
        })
    }
};
const originalLoad = Module._load;
let RemarpPreviewPanel;
try {
    Module._load = function(name, ...args) {
        return name === 'vscode' ? vscode : originalLoad.call(this, name, ...args);
    };
    ({ RemarpPreviewPanel } = require('../out/preview'));
} finally { Module._load = originalLoad; }

function renderPreview(source, base = '') {
    resourceBase = base;
    RemarpPreviewPanel.currentPanel = undefined;
    RemarpPreviewPanel.createOrShow(uri(path.resolve(__dirname, '..')), {
        uri: uri('/preview-fixture/deck.remarp.md'), getText: () => source
    });
    return RemarpPreviewPanel.currentPanel._panel.webview.html;
}
module.exports = { renderPreview };

if (require.main === module) {
    const input = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
    process.stdout.write(JSON.stringify(input.sources.map(source => renderPreview(source, input.base))));
}
