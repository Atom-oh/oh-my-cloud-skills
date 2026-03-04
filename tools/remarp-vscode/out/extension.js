"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.isRemarpDocument = isRemarpDocument;
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const preview_1 = require("./preview");
const outline_1 = require("./outline");
const completions_1 = require("./completions");
/**
 * Check if a document is a remarp file by looking for `remarp: true` in frontmatter
 * or checking if it has .remarp.md extension
 */
function isRemarpDocument(document) {
    // Check file extension first
    if (document.fileName.endsWith('.remarp.md')) {
        return true;
    }
    // Check for remarp: true in frontmatter
    const text = document.getText();
    const frontmatterMatch = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (frontmatterMatch) {
        const frontmatter = frontmatterMatch[1];
        // Check for remarp: true (with optional quotes)
        if (/^remarp:\s*(?:true|"true"|'true')\s*$/m.test(frontmatter)) {
            return true;
        }
    }
    return false;
}
/**
 * Set the language mode to remarp for markdown files with remarp: true
 */
async function setRemarpLanguageIfNeeded(document) {
    if (document.languageId === 'markdown' && isRemarpDocument(document)) {
        await vscode.languages.setTextDocumentLanguage(document, 'remarp');
    }
}
function activate(context) {
    console.log('Remarp extension is now active');
    // Check all open markdown files for remarp: true
    vscode.workspace.textDocuments.forEach(doc => {
        setRemarpLanguageIfNeeded(doc);
    });
    // Watch for newly opened documents
    context.subscriptions.push(vscode.workspace.onDidOpenTextDocument((document) => {
        setRemarpLanguageIfNeeded(document);
    }));
    // Watch for document saves (in case remarp: true is added)
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument((document) => {
        setRemarpLanguageIfNeeded(document);
    }));
    // Register the preview panel command
    context.subscriptions.push(vscode.commands.registerCommand('remarp.preview', () => {
        const editor = vscode.window.activeTextEditor;
        if (editor && (editor.document.languageId === 'remarp' || isRemarpDocument(editor.document))) {
            preview_1.RemarpPreviewPanel.createOrShow(context.extensionUri, editor.document);
        }
        else {
            vscode.window.showWarningMessage('Open a .remarp.md file or a markdown file with remarp: true to preview');
        }
    }));
    // Register the outline provider
    const outlineProvider = new outline_1.SlideOutlineProvider();
    context.subscriptions.push(vscode.window.registerTreeDataProvider('remarpOutline', outlineProvider));
    // Register completion provider
    const completionProvider = new completions_1.RemarpCompletionProvider();
    context.subscriptions.push(vscode.languages.registerCompletionItemProvider({ language: 'remarp' }, completionProvider, '@', ':', '='));
    // Register slide navigation commands
    context.subscriptions.push(vscode.commands.registerCommand('remarp.nextSlide', () => {
        navigateSlide('next');
    }));
    context.subscriptions.push(vscode.commands.registerCommand('remarp.prevSlide', () => {
        navigateSlide('prev');
    }));
    // Watch for document changes to update outline and preview
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((event) => {
        if (event.document.languageId === 'remarp') {
            outlineProvider.refresh();
            preview_1.RemarpPreviewPanel.update(event.document);
        }
    }));
    // Watch for active editor changes
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor && editor.document.languageId === 'remarp') {
            outlineProvider.refresh();
        }
    }));
    // Watch for cursor position changes to sync with outline
    context.subscriptions.push(vscode.window.onDidChangeTextEditorSelection((event) => {
        if (event.textEditor.document.languageId === 'remarp') {
            preview_1.RemarpPreviewPanel.syncCursor(event.textEditor);
        }
    }));
}
function navigateSlide(direction) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'remarp') {
        return;
    }
    const document = editor.document;
    const text = document.getText();
    const currentPosition = editor.selection.active;
    const currentOffset = document.offsetAt(currentPosition);
    // Find all slide separators (---)
    const separatorRegex = /^---$/gm;
    const separators = [];
    let match;
    while ((match = separatorRegex.exec(text)) !== null) {
        separators.push(match.index);
    }
    if (separators.length === 0) {
        return;
    }
    let targetOffset = null;
    if (direction === 'next') {
        // Find the next separator after current position
        for (const sep of separators) {
            if (sep > currentOffset) {
                targetOffset = sep;
                break;
            }
        }
    }
    else {
        // Find the previous separator before current position
        for (let i = separators.length - 1; i >= 0; i--) {
            if (separators[i] < currentOffset - 1) {
                targetOffset = separators[i];
                break;
            }
        }
    }
    if (targetOffset !== null) {
        const targetPosition = document.positionAt(targetOffset);
        const newSelection = new vscode.Selection(targetPosition, targetPosition);
        editor.selection = newSelection;
        editor.revealRange(new vscode.Range(targetPosition, targetPosition), vscode.TextEditorRevealType.InCenter);
    }
}
function deactivate() {
    // Cleanup
}
//# sourceMappingURL=extension.js.map