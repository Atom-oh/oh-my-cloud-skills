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
exports.HtmlPreviewRenderer = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
class HtmlPreviewRenderer {
    constructor(panel, extensionUri) {
        this.panel = panel;
        this.extensionUri = extensionUri;
    }
    render(document) {
        let html = document.getText();
        const docDir = path.dirname(document.uri.fsPath);
        const webview = this.panel.webview;
        // Helper: convert a relative path to a webview-safe URI
        const toWebviewUri = (relativePath) => {
            const absPath = path.resolve(docDir, relativePath);
            return webview.asWebviewUri(vscode.Uri.file(absPath)).toString();
        };
        // Convert relative paths in <link href="...">, <script src="...">, <img src="...">
        html = html.replace(/(<link[^>]+href=["'])([^"']+)(["'])/g, (match, pre, href, post) => {
            if (href.startsWith('http') || href.startsWith('data:') || href.startsWith('#')) {
                return match;
            }
            return pre + toWebviewUri(href) + post;
        });
        html = html.replace(/(<script[^>]+src=["'])([^"']+)(["'])/g, (match, pre, src, post) => {
            if (src.startsWith('http') || src.startsWith('data:')) {
                return match;
            }
            return pre + toWebviewUri(src) + post;
        });
        html = html.replace(/(<img[^>]+src=["'])([^"']+)(["'])/g, (match, pre, src, post) => {
            if (src.startsWith('http') || src.startsWith('data:')) {
                return match;
            }
            return pre + toWebviewUri(src) + post;
        });
        // Convert CSS url(...) references (background-image, @font-face, etc.)
        html = html.replace(/url\(["']?(?!data:|http|#|'data:|"data:|'http|"http)([^"')]+)["']?\)/g, (_match, urlPath) => {
            return `url('${toWebviewUri(urlPath)}')`;
        });
        // Strip any existing CSP meta tags to avoid conflicting policies
        html = html.replace(/<meta[^>]+Content-Security-Policy[^>]*>/gi, '');
        // Inject our CSP before </head>
        const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline' https:; script-src ${webview.cspSource} 'unsafe-inline'; img-src ${webview.cspSource} https: data:; font-src ${webview.cspSource} https: data:; connect-src https:;">`;
        html = html.replace('</head>', csp + '\n</head>');
        // Inject vscode API bridge and edit mode flag before </head>
        const bridgeScript = `
<script>
    const vscode = acquireVsCodeApi();
    window._remarpEditMode = false;
    window._remarpPostMessage = function(msg) { vscode.postMessage(msg); };
</script>`;
        // Inject edit mode scripts if enabled
        const editModeCssUri = this.panel.webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'edit-mode.css'));
        const editModeJsUri = this.panel.webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'edit-mode.js'));
        const canvasEditorJsUri = this.panel.webview.asWebviewUri(vscode.Uri.joinPath(this.extensionUri, 'media', 'canvas-editor.js'));
        // Always load edit scripts so per-slide Edit buttons work
        const editScripts = `
<link rel="stylesheet" href="${editModeCssUri}">
<script src="${editModeJsUri}"></script>
<script src="${canvasEditorJsUri}"></script>`;
        // Per-slide Edit button overlay (always injected)
        const slideEditButtonStyles = `
<style>
    .remarp-slide-edit-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        background: rgba(55, 148, 255, 0.8);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 12px;
        font-size: 12px;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.2s;
        z-index: 100;
    }
    .slide:hover .remarp-slide-edit-btn {
        opacity: 1;
    }
    .remarp-slide-edit-btn:hover {
        background: rgba(55, 148, 255, 1);
    }
</style>`;
        const slideEditButtonScript = `
<script>
(function() {
    document.querySelectorAll('.slide').forEach((slide, i) => {
        var btn = document.createElement('button');
        btn.className = 'remarp-slide-edit-btn';
        btn.textContent = 'Edit';
        btn.onclick = function(e) {
            e.stopPropagation();
            slide.classList.toggle('edit-mode');
            if (slide.classList.contains('edit-mode')) {
                btn.textContent = 'Done';
                btn.style.background = 'rgba(39, 174, 96, 0.8)';
                window._remarpEditMode = true;
                if (!window._remarpVisualEditor && window._RemarpVisualEditorClass) {
                    window._remarpVisualEditor = new window._RemarpVisualEditorClass();
                }
                if (!window._remarpCanvasEditor && window._RemarpCanvasEditorClass) {
                    window._remarpCanvasEditor = new window._RemarpCanvasEditorClass();
                }
                slide.querySelectorAll('[data-remarp-id]').forEach(function(el) {
                    el.style.outline = '1px dashed rgba(100, 150, 255, 0.3)';
                    el.style.cursor = 'move';
                });
            } else {
                btn.textContent = 'Edit';
                btn.style.background = 'rgba(55, 148, 255, 0.8)';
                window._remarpEditMode = false;
                slide.querySelectorAll('[data-remarp-id]').forEach(function(el) {
                    el.style.outline = '';
                    el.style.cursor = '';
                    el.classList.remove('selected');
                });
                if (window._remarpVisualEditor) {
                    window._remarpVisualEditor.deselectAll();
                }
                vscode.postMessage({ command: 'editDone' });
            }
        };
        slide.style.position = 'relative';
        slide.appendChild(btn);
    });
})();
</script>`;
        // SlideFramework timing fix + navigation bridge
        const slideFrameworkFix = `
<script>
(function() {
    // Fix DOMContentLoaded timing: if SlideFramework exists but hasn't initialized,
    // manually trigger initialization
    if (window.deck && window.deck.slides && window.deck.slides.length === 0) {
        window.deck.slides = Array.from(document.querySelectorAll('.slide'));
        window.deck.totalSlides = window.deck.slides.length;
        if (window.deck.totalSlides > 0) {
            if (window.deck.createProgressBar) { window.deck.createProgressBar(); }
            if (window.deck.createSlideCounter) { window.deck.createSlideCounter(); }
            if (window.deck.bindKeys) { window.deck.bindKeys(); }
            if (window.deck.bindTouch) { window.deck.bindTouch(); }
            if (window.deck.handleHash) { window.deck.handleHash(); }
            if (window.deck.showSlide) { window.deck.showSlide(0, false); }
        }
    }

    // Report slide count to extension
    var slideCount = document.querySelectorAll('.slide').length;
    if (slideCount === 0) {
        vscode.postMessage({ command: 'htmlSlideCountError', count: 0 });
    } else {
        vscode.postMessage({ command: 'htmlSlideCount', count: slideCount });
    }

    // Bridge: intercept slide changes to sync with extension
    if (window.deck && window.deck.showSlide) {
        var origShowSlide = window.deck.showSlide.bind(window.deck);
        window.deck.showSlide = function(index, animate) {
            origShowSlide(index, animate);
            vscode.postMessage({ command: 'htmlSlideChanged', index: index });
        };
    }

    // Listen for navigation commands from extension
    window.addEventListener('message', function(event) {
        var msg = event.data;
        if (msg.command === 'goToSlide' && window.deck && window.deck.showSlide) {
            window.deck.showSlide(msg.index, true);
        }
    });
})();
</script>`;
        // Inject bridge before </head>, edit scripts + slide fix before </body>
        html = html.replace('</head>', bridgeScript + '\n' + slideEditButtonStyles + '\n</head>');
        html = html.replace('</body>', editScripts + '\n' + slideEditButtonScript + '\n' + slideFrameworkFix + '\n</body>');
        return html;
    }
}
exports.HtmlPreviewRenderer = HtmlPreviewRenderer;
//# sourceMappingURL=htmlPreview.js.map