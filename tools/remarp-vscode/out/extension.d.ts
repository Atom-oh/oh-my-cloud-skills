import * as vscode from 'vscode';
/**
 * Check if a document is a remarp file by looking for `remarp: true` in frontmatter
 * or checking if it has .remarp.md extension
 */
export declare function isRemarpDocument(document: vscode.TextDocument): boolean;
export declare function activate(context: vscode.ExtensionContext): void;
export declare function deactivate(): void;
