import * as vscode from 'vscode';
import * as path from 'path';

/**
 * Check if a document is a remarp file by looking for `remarp: true` in frontmatter
 * or checking if it has .remarp.md extension
 */
export function isRemarpDocument(document: vscode.TextDocument): boolean {
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
export function isStudioSource(document: vscode.TextDocument): boolean {
    return document.uri.scheme === 'file' && (document.languageId === 'remarp' || isRemarpDocument(document));
}

/** Prefer an explicit source, then the current editor; ask rather than guess between decks. */
export async function selectStudioSource(uri?: vscode.Uri): Promise<vscode.TextDocument | undefined> {
    if (uri) { return openSource(uri); }
    const active = vscode.window.activeTextEditor?.document;
    if (active && isStudioSource(active)) { return active; }
    const open = vscode.workspace.textDocuments.filter(isStudioSource);
    if (open.length === 1) { return open[0]; }
    const selected = await vscode.window.showOpenDialog({
        title: 'Open Remarp source in Design Studio', openLabel: 'Open Design Studio',
        canSelectFiles: true, canSelectFolders: false, canSelectMany: false,
        filters: { 'Remarp Markdown': ['md'] },
        defaultUri: active?.uri.scheme === 'file' ? active.uri : vscode.workspace.workspaceFolders?.[0]?.uri
    });
    return selected?.[0] ? openSource(selected[0]) : undefined;
}

async function openSource(uri: vscode.Uri): Promise<vscode.TextDocument> {
    if (uri.scheme !== 'file') { throw new Error('Select a local .md or .remarp.md source file.'); }
    const document = await vscode.workspace.openTextDocument(uri);
    if (!isStudioSource(document)) {
        throw new Error('This is not Remarp source. Add remarp: true to the Markdown frontmatter, or select a .remarp.md file.');
    }
    return document;
}
