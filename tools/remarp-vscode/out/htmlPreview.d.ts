import * as vscode from 'vscode';
export declare class HtmlPreviewRenderer {
    private panel;
    private extensionUri;
    constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri);
    render(document: vscode.TextDocument): string;
}
