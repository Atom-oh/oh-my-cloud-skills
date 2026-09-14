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
exports.CompiledPreviewRenderer = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
/** Display compiler HTML unchanged apart from its webview resource policy. */
class CompiledPreviewRenderer {
    constructor(panel, _extensionUri) {
        this.panel = panel;
    }
    render(document) {
        if (!vscode.workspace.isTrusted) {
            throw new Error('Compiled preview requires workspace trust.');
        }
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
exports.CompiledPreviewRenderer = CompiledPreviewRenderer;
//# sourceMappingURL=compiledPreview.js.map