import * as vscode from 'vscode';
/**
 * Check if a document is a remarp file by looking for `remarp: true` in frontmatter
 * or checking if it has .remarp.md extension
 */
export declare function isRemarpDocument(document: vscode.TextDocument): boolean;
/** Recognize the current buffer, even before VS Code's asynchronous language switch. */
export declare function isStudioSource(document: vscode.TextDocument): boolean;
/** Prefer an explicit source, then the current editor; ask rather than guess between decks. */
export declare function selectStudioSource(uri?: vscode.Uri): Promise<vscode.TextDocument | undefined>;
