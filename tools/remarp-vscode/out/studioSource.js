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
exports.isStudioSource = isStudioSource;
exports.selectStudioSource = selectStudioSource;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
/**
 * Check if a document is a remarp file by looking for `remarp: true` in frontmatter
 * or checking if it has .remarp.md extension
 */
function isRemarpDocument(document) {
    // Check file extension first
    if (document.fileName.endsWith('.remarp.md') || path.basename(document.fileName) === '_presentation.md') {
        return true;
    }
    // Check for remarp: true in frontmatter
    const text = document.getText();
    const frontmatterMatch = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (frontmatterMatch) {
        const frontmatter = frontmatterMatch[1];
        // Check for remarp: true (with optional quotes)
        if (/^remarp:\s*(?:true|"true"|'true')\s*(?:#.*)?$/m.test(frontmatter)) {
            return true;
        }
    }
    return false;
}
/** Recognize the current buffer, even before VS Code's asynchronous language switch. */
function isStudioSource(document) {
    return document.uri.scheme === 'file' && (document.languageId === 'remarp' || isRemarpDocument(document));
}
/** Prefer an explicit source, then the current editor; ask rather than guess between decks. */
async function selectStudioSource(uri) {
    if (uri) {
        return openSource(uri);
    }
    const active = vscode.window.activeTextEditor?.document;
    if (active && isStudioSource(active)) {
        return active;
    }
    const open = vscode.workspace.textDocuments.filter(isStudioSource);
    if (open.length === 1) {
        return open[0];
    }
    const selected = await vscode.window.showOpenDialog({
        title: 'Open Remarp source in Design Studio', openLabel: 'Open Design Studio',
        canSelectFiles: true, canSelectFolders: false, canSelectMany: false,
        filters: { 'Remarp Markdown': ['md'] },
        defaultUri: active?.uri.scheme === 'file' ? active.uri : vscode.workspace.workspaceFolders?.[0]?.uri
    });
    return selected?.[0] ? openSource(selected[0]) : undefined;
}
async function openSource(uri) {
    if (uri.scheme !== 'file') {
        throw new Error('Select a local .md or .remarp.md source file.');
    }
    const document = await vscode.workspace.openTextDocument(uri);
    if (!isStudioSource(document)) {
        throw new Error('This is not Remarp source. Add remarp: true to the Markdown frontmatter, or select a .remarp.md file.');
    }
    return document;
}
//# sourceMappingURL=studioSource.js.map