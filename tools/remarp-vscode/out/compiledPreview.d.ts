import * as vscode from 'vscode';
/** Display compiler HTML unchanged apart from its webview resource policy. */
export declare class CompiledPreviewRenderer {
    private panel;
    constructor(panel: vscode.WebviewPanel, _extensionUri: vscode.Uri);
    render(document: Pick<vscode.TextDocument, 'uri' | 'getText'>): string;
}
