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
exports.RemarpPreviewPanel = void 0;
const vscode = __importStar(require("vscode"));
class RemarpPreviewPanel {
    static createOrShow(extensionUri, document) {
        const column = vscode.ViewColumn.Beside;
        if (RemarpPreviewPanel.currentPanel) {
            RemarpPreviewPanel.currentPanel._panel.reveal(column);
            RemarpPreviewPanel.currentPanel._document = document;
            RemarpPreviewPanel.currentPanel._updateContent();
            return;
        }
        const panel = vscode.window.createWebviewPanel(RemarpPreviewPanel.viewType, 'Remarp Preview', column, {
            enableScripts: true,
            localResourceRoots: [extensionUri],
            retainContextWhenHidden: true
        });
        RemarpPreviewPanel.currentPanel = new RemarpPreviewPanel(panel, extensionUri, document);
    }
    static update(document) {
        if (RemarpPreviewPanel.currentPanel && RemarpPreviewPanel.currentPanel._document.uri.toString() === document.uri.toString()) {
            RemarpPreviewPanel.currentPanel._debouncedUpdate();
        }
    }
    static syncCursor(editor) {
        if (RemarpPreviewPanel.currentPanel && RemarpPreviewPanel.currentPanel._document.uri.toString() === editor.document.uri.toString()) {
            const slides = RemarpPreviewPanel.currentPanel._parseSlides();
            const cursorLine = editor.selection.active.line;
            for (let i = slides.length - 1; i >= 0; i--) {
                if (cursorLine >= slides[i].startLine) {
                    if (i !== RemarpPreviewPanel.currentPanel._currentSlideIndex) {
                        RemarpPreviewPanel.currentPanel._currentSlideIndex = i;
                        RemarpPreviewPanel.currentPanel._updateContent();
                    }
                    break;
                }
            }
        }
    }
    constructor(panel, extensionUri, document) {
        this._currentSlideIndex = 0;
        this._disposables = [];
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._document = document;
        this._updateContent();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage((message) => {
            switch (message.command) {
                case 'navigateSlide':
                    this._navigateToSlide(message.index);
                    break;
                case 'nextSlide':
                    this._nextSlide();
                    break;
                case 'prevSlide':
                    this._prevSlide();
                    break;
            }
        }, null, this._disposables);
    }
    _debouncedUpdate() {
        if (this._updateTimeout) {
            clearTimeout(this._updateTimeout);
        }
        this._updateTimeout = setTimeout(() => {
            this._updateContent();
        }, 300);
    }
    _parseSlides() {
        const text = this._document.getText();
        const lines = text.split('\n');
        const slides = [];
        let currentSlideStart = 0;
        let slideIndex = 0;
        let inFrontmatter = false;
        let frontmatterEnd = 0;
        // Handle frontmatter at the beginning
        if (lines[0]?.trim() === '---') {
            inFrontmatter = true;
            for (let i = 1; i < lines.length; i++) {
                if (lines[i].trim() === '---') {
                    frontmatterEnd = i + 1;
                    break;
                }
            }
            currentSlideStart = frontmatterEnd;
        }
        for (let i = currentSlideStart; i < lines.length; i++) {
            if (lines[i].trim() === '---') {
                // End current slide
                const slideContent = lines.slice(currentSlideStart, i).join('\n');
                if (slideContent.trim()) {
                    slides.push({
                        index: slideIndex,
                        startLine: currentSlideStart,
                        endLine: i - 1,
                        content: slideContent,
                        title: this._extractTitle(slideContent),
                        type: this._extractType(slideContent)
                    });
                    slideIndex++;
                }
                currentSlideStart = i + 1;
            }
        }
        // Add last slide
        const lastSlideContent = lines.slice(currentSlideStart).join('\n');
        if (lastSlideContent.trim()) {
            slides.push({
                index: slideIndex,
                startLine: currentSlideStart,
                endLine: lines.length - 1,
                content: lastSlideContent,
                title: this._extractTitle(lastSlideContent),
                type: this._extractType(lastSlideContent)
            });
        }
        return slides;
    }
    _extractTitle(content) {
        const headingMatch = content.match(/^#\s+(.+)$/m);
        if (headingMatch) {
            return headingMatch[1].trim();
        }
        // Use first non-empty, non-directive line
        const lines = content.split('\n');
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed && !trimmed.startsWith('@') && !trimmed.startsWith(':::')) {
                return trimmed.substring(0, 50);
            }
        }
        return 'Untitled Slide';
    }
    _extractType(content) {
        const typeMatch = content.match(/^@type\s+(\S+)/m);
        return typeMatch ? typeMatch[1] : 'content';
    }
    _updateContent() {
        const slides = this._parseSlides();
        if (slides.length === 0) {
            this._panel.webview.html = this._getEmptyHtml();
            return;
        }
        // Clamp current slide index
        if (this._currentSlideIndex >= slides.length) {
            this._currentSlideIndex = slides.length - 1;
        }
        if (this._currentSlideIndex < 0) {
            this._currentSlideIndex = 0;
        }
        const currentSlide = slides[this._currentSlideIndex];
        this._panel.webview.html = this._getHtmlForSlide(currentSlide, slides.length);
    }
    _navigateToSlide(index) {
        const slides = this._parseSlides();
        if (index >= 0 && index < slides.length) {
            this._currentSlideIndex = index;
            this._updateContent();
            // Also move cursor in editor
            const editor = vscode.window.activeTextEditor;
            if (editor && editor.document.uri.toString() === this._document.uri.toString()) {
                const slide = slides[index];
                const position = new vscode.Position(slide.startLine, 0);
                editor.selection = new vscode.Selection(position, position);
                editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
            }
        }
    }
    _nextSlide() {
        const slides = this._parseSlides();
        if (this._currentSlideIndex < slides.length - 1) {
            this._navigateToSlide(this._currentSlideIndex + 1);
        }
    }
    _prevSlide() {
        if (this._currentSlideIndex > 0) {
            this._navigateToSlide(this._currentSlideIndex - 1);
        }
    }
    _getEmptyHtml() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remarp Preview</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1e1e1e;
            color: #cccccc;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .empty-state {
            text-align: center;
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="empty-state">
        <h2>No slides found</h2>
        <p>Add content separated by --- to create slides</p>
    </div>
</body>
</html>`;
    }
    _getHtmlForSlide(slide, totalSlides) {
        const renderedContent = this._renderMarkdown(slide.content);
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remarp Preview</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1e1e1e;
            color: #e0e0e0;
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .toolbar {
            background: #252526;
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #3c3c3c;
        }
        .toolbar-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .slide-counter {
            color: #888;
            font-size: 14px;
        }
        .slide-type {
            background: #0e639c;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }
        .nav-buttons {
            display: flex;
            gap: 8px;
        }
        .nav-button {
            background: #3c3c3c;
            color: #e0e0e0;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .nav-button:hover {
            background: #4c4c4c;
        }
        .nav-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .slide-container {
            flex: 1;
            overflow: auto;
            padding: 40px;
        }
        .slide {
            background: #252526;
            border-radius: 8px;
            padding: 40px;
            max-width: 960px;
            margin: 0 auto;
            min-height: 400px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        h1 { font-size: 2.5em; margin-top: 0; color: #fff; }
        h2 { font-size: 2em; color: #fff; }
        h3 { font-size: 1.5em; color: #ddd; }
        p { line-height: 1.6; }
        code {
            background: #1e1e1e;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }
        pre {
            background: #1e1e1e;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
        }
        pre code {
            background: none;
            padding: 0;
        }
        ul, ol {
            padding-left: 24px;
            line-height: 1.8;
        }
        .directive {
            color: #569cd6;
            font-weight: 500;
        }
        .block-tag {
            color: #4ec9b0;
        }
        .notes-block {
            background: #2d2d2d;
            border-left: 4px solid #888;
            padding: 12px;
            margin: 16px 0;
            font-style: italic;
            color: #999;
        }
        blockquote {
            border-left: 4px solid #0e639c;
            margin: 16px 0;
            padding-left: 16px;
            color: #aaa;
        }
        a {
            color: #3794ff;
        }
        img {
            max-width: 100%;
            border-radius: 8px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }
        th, td {
            border: 1px solid #3c3c3c;
            padding: 12px;
            text-align: left;
        }
        th {
            background: #2d2d2d;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <div class="toolbar-left">
            <span class="slide-counter">Slide ${slide.index + 1} of ${totalSlides}</span>
            <span class="slide-type">@${slide.type}</span>
        </div>
        <div class="nav-buttons">
            <button class="nav-button" onclick="prevSlide()" ${slide.index === 0 ? 'disabled' : ''}>Previous</button>
            <button class="nav-button" onclick="nextSlide()" ${slide.index === totalSlides - 1 ? 'disabled' : ''}>Next</button>
        </div>
    </div>
    <div class="slide-container">
        <div class="slide">
            ${renderedContent}
        </div>
    </div>
    <script>
        const vscode = acquireVsCodeApi();

        function nextSlide() {
            vscode.postMessage({ command: 'nextSlide' });
        }

        function prevSlide() {
            vscode.postMessage({ command: 'prevSlide' });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                nextSlide();
            } else if (e.key === 'ArrowLeft') {
                prevSlide();
            }
        });
    </script>
</body>
</html>`;
    }
    _renderMarkdown(content) {
        // Remove directives for display (but show them styled)
        let html = content;
        // Convert directives to styled spans
        html = html.replace(/^(@\w+(?:-\w+)*)\s+(.*)$/gm, '<div class="directive">$1 <span style="color: #ce9178;">$2</span></div>');
        // Convert ::: blocks
        html = html.replace(/^:::\s*(\w+)(?:\s+(.*))?$/gm, '<div class="block-tag">::: $1 <span style="color: #ce9178;">$2</span></div>');
        html = html.replace(/^:::$/gm, '<div class="block-tag">:::</div>');
        // Handle notes blocks specially
        html = html.replace(/:::notes([\s\S]*?):::/g, '<div class="notes-block">$1</div>');
        // Convert headers
        html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');
        // Convert bold and italic
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
        html = html.replace(/_(.+?)_/g, '<em>$1</em>');
        // Convert inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Convert code blocks
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
        // Convert links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
        // Convert images
        html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');
        // Convert unordered lists
        html = html.replace(/^[-*] (.*)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
        // Convert ordered lists
        html = html.replace(/^\d+\. (.*)$/gm, '<li>$1</li>');
        // Convert blockquotes
        html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>');
        // Convert line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';
        // Clean up empty paragraphs
        html = html.replace(/<p>\s*<\/p>/g, '');
        html = html.replace(/<p>(<h[1-6]>)/g, '$1');
        html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1');
        html = html.replace(/<p>(<div)/g, '$1');
        html = html.replace(/(<\/div>)<\/p>/g, '$1');
        html = html.replace(/<p>(<ul>)/g, '$1');
        html = html.replace(/(<\/ul>)<\/p>/g, '$1');
        html = html.replace(/<p>(<pre>)/g, '$1');
        html = html.replace(/(<\/pre>)<\/p>/g, '$1');
        html = html.replace(/<p>(<blockquote>)/g, '$1');
        html = html.replace(/(<\/blockquote>)<\/p>/g, '$1');
        return html;
    }
    dispose() {
        RemarpPreviewPanel.currentPanel = undefined;
        if (this._updateTimeout) {
            clearTimeout(this._updateTimeout);
        }
        this._panel.dispose();
        while (this._disposables.length) {
            const disposable = this._disposables.pop();
            if (disposable) {
                disposable.dispose();
            }
        }
    }
}
exports.RemarpPreviewPanel = RemarpPreviewPanel;
RemarpPreviewPanel.viewType = 'remarpPreview';
//# sourceMappingURL=preview.js.map