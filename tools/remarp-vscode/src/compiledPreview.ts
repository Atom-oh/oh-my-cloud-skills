import * as vscode from 'vscode';
import * as path from 'path';

/** Display compiler HTML unchanged apart from its webview resource policy. */
export class CompiledPreviewRenderer {
    constructor(private panel: vscode.WebviewPanel, _extensionUri: vscode.Uri) {}

    render(document: Pick<vscode.TextDocument, 'uri' | 'getText'>): string {
        if (!vscode.workspace.isTrusted) { throw new Error('Compiled preview requires workspace trust.'); }
        const webview = this.panel.webview;
        const base = webview.asWebviewUri(vscode.Uri.file(path.dirname(document.uri.fsPath))).toString() + '/';
        // Set the policy before any resources. A base also resolves runtime-created
        // URLs and CSS references, preserving encoded paths, queries and fragments.
        const policy = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri ${webview.cspSource}; style-src ${webview.cspSource} 'unsafe-inline' https:; script-src ${webview.cspSource} 'unsafe-inline' https:; img-src ${webview.cspSource} https: data:; font-src ${webview.cspSource} https: data:; media-src ${webview.cspSource} https:; connect-src ${webview.cspSource} https:; frame-src ${webview.cspSource} https:;">`;
        const head = policy + `<base href="${base.replace(/&/g, '&amp;').replace(/"/g, '&quot;')}">`;
        const html = document.getText().replace(/<meta\b[^>]*http-equiv=["']Content-Security-Policy["'][^>]*>/gi, '')
            .replace(/<base\b[^>]*>/gi, '');
        return html.replace(/<head\b[^>]*>/i, match => match + head);
    }
}
