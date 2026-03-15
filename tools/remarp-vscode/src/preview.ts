import * as vscode from 'vscode';
import * as path from 'path';
import { VisualEditorController } from './visualEditor';
import { isRemarpHtml } from './extension';
import { HtmlPreviewRenderer } from './htmlPreview';

interface Slide {
    index: number;
    startLine: number;
    endLine: number;
    content: string;
    title: string;
    type: string;
}

export class RemarpPreviewPanel {
    public static currentPanel: RemarpPreviewPanel | undefined;
    private static readonly viewType = 'remarpPreview';
    private static _editMode: boolean = false;
    private static _visualEditor: VisualEditorController | undefined;

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _document: vscode.TextDocument;
    private _currentSlideIndex: number = 0;
    private _disposables: vscode.Disposable[] = [];
    private _updateTimeout: NodeJS.Timeout | undefined;
    private _isHtmlMode: boolean = false;

    public static createOrShow(extensionUri: vscode.Uri, document: vscode.TextDocument): void {
        const column = vscode.ViewColumn.Beside;

        if (RemarpPreviewPanel.currentPanel) {
            RemarpPreviewPanel.currentPanel._panel.reveal(column);
            RemarpPreviewPanel.currentPanel._document = document;
            RemarpPreviewPanel.currentPanel._panel.title = `Remarp Preview - ${path.basename(document.uri.fsPath)}`;
            RemarpPreviewPanel.currentPanel._isHtmlMode = isRemarpHtml(document);
            RemarpPreviewPanel.currentPanel._updateContent();
            return;
        }

        // Allow webview to load resources from the document's directory and ancestors
        // Walk up to 3 parent levels for ../common/, ../../common/ references
        const docDir = vscode.Uri.file(path.dirname(document.uri.fsPath));
        const roots: vscode.Uri[] = [extensionUri, docDir];
        let parentPath = docDir.fsPath;
        for (let i = 0; i < 3; i++) {
            parentPath = path.dirname(parentPath);
            roots.push(vscode.Uri.file(parentPath));
        }
        // Include workspace root if available
        const wsFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (wsFolder) { roots.push(wsFolder.uri); }

        const fileName = path.basename(document.uri.fsPath);
        const panel = vscode.window.createWebviewPanel(
            RemarpPreviewPanel.viewType,
            `Remarp Preview - ${fileName}`,
            column,
            {
                enableScripts: true,
                localResourceRoots: roots,
                retainContextWhenHidden: true
            }
        );

        RemarpPreviewPanel.currentPanel = new RemarpPreviewPanel(panel, extensionUri, document);
        RemarpPreviewPanel.currentPanel._isHtmlMode = isRemarpHtml(document);
    }

    public static update(document: vscode.TextDocument): void {
        if (RemarpPreviewPanel.currentPanel && RemarpPreviewPanel.currentPanel._document.uri.toString() === document.uri.toString()) {
            RemarpPreviewPanel.currentPanel._debouncedUpdate();
        }
    }

    public static setEditMode(enabled: boolean): void {
        RemarpPreviewPanel._editMode = enabled;
        if (RemarpPreviewPanel.currentPanel) {
            RemarpPreviewPanel.currentPanel._updateContent();
        }
    }

    public static setVisualEditor(editor: VisualEditorController): void {
        RemarpPreviewPanel._visualEditor = editor;
    }

    public static syncCursor(editor: vscode.TextEditor): void {
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

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, document: vscode.TextDocument) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._document = document;

        this._updateContent();

        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        this._panel.webview.onDidReceiveMessage(
            (message) => {
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
                    // HTML preview slide navigation messages
                    case 'htmlSlideChanged':
                        this._currentSlideIndex = message.index;
                        break;
                    case 'htmlSlideCount':
                        // Slide framework loaded successfully
                        break;
                    case 'htmlSlideCountError':
                        vscode.window.showWarningMessage(
                            'Remarp HTML preview: No slides detected. Check if slide-framework.js loaded correctly.'
                        );
                        break;
                    // Edit mode messages - route to visual editor controller
                    case 'elementMoved':
                    case 'elementResized':
                    case 'propertyChanged':
                    case 'canvasElementMoved':
                    case 'canvasElementResized':
                    case 'canvasStepChanged':
                    case 'waypointChanged':
                    case 'editDone':
                        if (RemarpPreviewPanel._visualEditor) {
                            RemarpPreviewPanel._visualEditor.handleMessage(message, this._document);
                        }
                        break;
                }
            },
            null,
            this._disposables
        );
    }

    private _debouncedUpdate(): void {
        if (this._updateTimeout) {
            clearTimeout(this._updateTimeout);
        }
        this._updateTimeout = setTimeout(() => {
            this._updateContent();
        }, 300);
    }

    private _parseFrontmatter(): Record<string, string> {
        const text = this._document.getText();
        const match = text.match(/^---\s*\n([\s\S]*?)\n---/);
        if (!match) { return {}; }
        const result: Record<string, string> = {};
        for (const line of match[1].split('\n')) {
            const kv = line.match(/^\s*(\w+):\s*"?([^"#]*?)"?\s*(?:#.*)?$/);
            if (kv) { result[kv[1].trim()] = kv[2].trim(); }
        }
        // Normalize Marp aliases: paginate → pagination
        if (result['paginate'] && !result['pagination']) {
            result['pagination'] = result['paginate'];
        }
        return result;
    }

    private _parseSlides(): Slide[] {
        const text = this._document.getText();
        const lines = text.split('\n');
        const slides: Slide[] = [];

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

    private _extractTitle(content: string): string {
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

    private _extractType(content: string): string {
        const typeMatch = content.match(/^@type\s+(\S+)/m);
        return typeMatch ? typeMatch[1] : 'content';
    }

    private _updateContent(): void {
        if (this._isHtmlMode) {
            const renderer = new HtmlPreviewRenderer(this._panel, this._extensionUri);
            this._panel.webview.html = renderer.render(this._document);
            return;
        }

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

    private _navigateToSlide(index: number): void {
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

    private _nextSlide(): void {
        const slides = this._parseSlides();
        if (this._currentSlideIndex < slides.length - 1) {
            this._navigateToSlide(this._currentSlideIndex + 1);
        }
    }

    private _prevSlide(): void {
        if (this._currentSlideIndex > 0) {
            this._navigateToSlide(this._currentSlideIndex - 1);
        }
    }

    private _getEmptyHtml(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remarp Preview - ${path.basename(this._document.uri.fsPath)}</title>
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

    private _getHtmlForSlide(slide: Slide, totalSlides: number): string {
        const { html: rawRenderedHtml, notes: rawNotes, notesArg } = this._renderMarkdown(slide.content, slide.index);

        // Convert relative image paths to webview URIs (mirrors htmlPreview.ts behavior)
        const docDir = path.dirname(this._document.uri.fsPath);
        const rawRenderedContent = rawRenderedHtml.replace(
            /(<img[^>]+src=["'])([^"']+)(["'])/g,
            (match, pre, src, post) => {
                if (src.startsWith('http') || src.startsWith('data:') || src.startsWith('vscode-')) {
                    return match;
                }
                const absPath = path.resolve(docDir, src);
                return pre + this._panel.webview.asWebviewUri(vscode.Uri.file(absPath)).toString() + post;
            }
        );
        const hasNotes = !!rawNotes;
        const fm = this._parseFrontmatter();
        const isEditMode = RemarpPreviewPanel._editMode;
        const sid = `s${slide.index}`;

        // Extract @type and @layout for slide-level CSS classes
        const slideType = slide.type || 'content';
        const layoutMatch = slide.content.match(/^@layout\s+(\S+)/m);
        const slideLayout = layoutMatch ? layoutMatch[1] : '';
        const slideClasses = ['slide', `slide-type-${slideType}`, slideLayout ? `slide-layout-${slideLayout}` : '', isEditMode ? 'edit-mode' : ''].filter(Boolean).join(' ');

        // Type-specific content transformation
        const renderedContent = this._transformByType(slideType, rawRenderedContent, slide, fm);

        // Edit mode media URIs
        const editModeCssUri = this._panel.webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'edit-mode.css'));
        const editModeJsUri = this._panel.webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'edit-mode.js'));

        // Global styles from frontmatter directives
        const bgColor = fm['backgroundColor'] || '';
        const bgImage = fm['backgroundImage'] || '';
        const textColor = fm['color'] || '';
        const headerText = fm['header'] || '';
        const footerText = fm['footer'] || fm['theme'] || ''; // top-level footer only
        const showPagination = fm['pagination'] !== 'false';

        const bodyBg = bgColor || '#0f1117';
        const slideBg = bgColor || '#1a1d2e';
        const slideBgImage = bgImage ? `background-image: ${bgImage.startsWith('url(') ? bgImage : `url(${bgImage})`};` : '';
        const slideColor = textColor || '#e8eaf0';
        const headingColor = textColor || '#e8eaf0';

        const headerHtml = headerText
            ? `<div class="fm-header" data-remarp-id="${sid}-header">${this._escapeHtml(headerText)}</div>`
            : '';
        const footerHtml = footerText
            ? `<div class="slide-footer" data-remarp-id="${sid}-footer">${this._escapeHtml(footerText)}</div>`
            : '';
        const paginationHtml = showPagination
            ? `<div class="slide-pagination">${slide.index + 1} / ${totalSlides}</div>`
            : '';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remarp Preview - ${path.basename(this._document.uri.fsPath)}</title>
    <link rel="stylesheet" href="${editModeCssUri}">
    <style>
        * {
            box-sizing: border-box;
        }
        :root {
          --bg-primary: #0f1117;
          --bg-secondary: #1a1d2e;
          --bg-card: #1e2235;
          --surface: #282d45;
          --border: #2d3250;
          --text-primary: #e8eaf0;
          --text-secondary: #9ba1b8;
          --text-muted: #6b7194;
          --text-accent: #7b8cff;
          --accent: #6c5ce7;
          --accent-light: #a29bfe;
          --accent-glow: rgba(108, 92, 231, 0.3);
          --green: #00b894;
          --red: #e17055;
          --yellow: #fdcb6e;
          --blue: #74b9ff;
          --font-main: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: ${bodyBg};
            color: ${slideColor};
            margin: 0;
            padding: 0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .toolbar {
            background: var(--bg-secondary);
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
        }
        .toolbar-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .slide-counter {
            color: var(--text-muted);
            font-size: 14px;
        }
        .slide-type {
            background: var(--accent);
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
            background: var(--surface);
            color: #e0e0e0;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .nav-button:hover {
            background: rgba(108,92,231,0.3);
        }
        .nav-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .slide-container {
            flex: 1;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 8px;
        }
        .slide-wrapper {
            width: 1280px;
            transform-origin: center center;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .slide {
            background: ${slideBg};
            ${slideBgImage}
            background-size: cover;
            padding: 48px 60px;
            width: 1280px;
            height: 720px;
            position: relative;
            overflow: auto;
            display: flex;
            flex-direction: column;
        }
        .fm-header {
            position: absolute;
            top: 12px;
            left: 40px;
            right: 40px;
            font-size: 0.75em;
            color: ${headingColor};
            opacity: 0.7;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 6px;
        }
        .slide-footer {
            position: absolute;
            bottom: 12px;
            left: 40px;
            right: 120px; /* leave room for pagination */
            font-size: 0.7em;
            color: ${slideColor};
            opacity: 0.6;
        }
        .slide-pagination {
            position: absolute;
            bottom: 12px;
            right: 40px;
            font-size: 0.7em;
            color: ${slideColor};
            opacity: 0.5;
        }
        h1 { font-size: 2.5em; margin-top: 0; color: ${headingColor}; }
        h2 { font-size: 2em; color: ${headingColor}; }
        h3 { font-size: 1.5em; color: ${headingColor}; }
        p { line-height: 1.6; }
        code {
            background: #0d1117;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }
        pre {
            background: #0d1117;
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
        /* Column layouts */
        .columns-2, .columns-3 { display: flex; gap: 24px; margin: 16px 0; align-items: flex-start; }
        .columns-2 .col { flex: 1; min-width: 0; }
        .columns-3 .col { flex: 1; min-width: 0; }

        /* Grid cells */
        .grid-cells { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 16px 0; }
        .cell { background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }

        /* Click blocks */
        .click-block { border-left: 3px solid var(--accent); padding: 12px 16px; margin: 12px 0; background: rgba(108,92,231,0.08); border-radius: 0 8px 8px 0; }

        /* Canvas placeholder */
        .canvas-placeholder { background: rgba(255,255,255,0.03); border: 2px dashed rgba(255,255,255,0.15); border-radius: 8px; padding: 16px 20px; color: rgba(255,255,255,0.5); margin: 16px 0; text-align: left; }
        .canvas-header { font-weight: 600; font-size: 0.85em; color: rgba(255,255,255,0.4); margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; }
        .canvas-source { margin: 0; padding: 0; font-size: 0.8em; line-height: 1.5; white-space: pre-wrap; word-break: break-word; color: rgba(255,255,255,0.55); background: none; border: none; }

        /* Prompt placeholder */
        .prompt-placeholder { background: rgba(255,153,0,0.06); border: 2px dashed rgba(255,153,0,0.4); border-radius: 8px; padding: 16px 20px; color: rgba(255,255,255,0.7); margin: 16px 0; text-align: left; }
        .prompt-header { font-weight: 600; font-size: 0.85em; color: #FF9900; margin-bottom: 8px; border-bottom: 1px solid rgba(255,153,0,0.2); padding-bottom: 8px; }
        .prompt-source { margin: 0; padding: 0; font-size: 0.85em; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: rgba(255,255,255,0.75); background: none; border: none; }
        .prompt-footer { font-size: 0.75em; color: rgba(255,153,0,0.5); margin-top: 8px; font-style: italic; }

        /* Tab blocks */
        .tab-block { border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; margin: 8px 0; overflow: hidden; }
        .tab-title { background: rgba(255,255,255,0.08); padding: 8px 16px; font-weight: 600; font-size: 0.85em; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .tab-content { padding: 12px 16px; }

        /* Timeline steps */
        .timeline-step { display: flex; gap: 16px; margin: 12px 0; align-items: flex-start; }
        .step-label { background: var(--accent); color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: 700; white-space: nowrap; flex-shrink: 0; }

        /* List items */
        .list-item { padding: 8px 16px; margin: 4px 0; border-left: 2px solid rgba(255,255,255,0.15); }

        /* Quiz options */
        .quiz-option { padding: 10px 16px; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; cursor: default; }
        .quiz-option:hover { border-color: var(--accent); }
        .quiz-option.correct { border-color: #27ae60; background: rgba(39,174,96,0.08); }

        /* Per-slide Edit button */
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
        .slide:hover .remarp-slide-edit-btn,
        .slide-wrapper:hover .remarp-slide-edit-btn {
            opacity: 1;
        }
        .remarp-slide-edit-btn:hover {
            background: rgba(55, 148, 255, 1);
        }
        .remarp-slide-edit-btn.active {
            background: rgba(39, 174, 96, 0.8);
        }

        /* Fragment blocks */
        .fragment-block { padding: 8px 0; }

        /* Inline click indicator */
        .click-indicator { opacity: 0.5; font-size: 0.75em; color: var(--accent); margin-left: 4px; }

        /* Notes panel (inside slide-wrapper, below slide) */
        .notes-panel { background: var(--bg-secondary); border-top: 1px solid var(--border); padding: 12px 20px; max-height: 150px; overflow-y: auto; }
        /* notes-marker removed — no longer used */
        .notes-keyword { color: #4ec9b0; }
        .notes-arg { color: #ce9178; }
        .notes-panel-content { font-size: 0.85em; color: #ccc; line-height: 1.5; padding: 2px 0; }
        .notes-timing { color: #ce9178; font-weight: 600; margin: 0 2px; }
        .notes-cue { color: #3498db; font-weight: 600; margin: 0 2px; }
        blockquote {
            border-left: 4px solid var(--accent);
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
            border: 1px solid var(--border);
            padding: 12px;
            text-align: left;
        }
        th {
            background: var(--surface);
        }

        /* Slide structure: heading area + body */
        .slide-header { margin-bottom: 16px; flex-shrink: 0; }
        .slide-body { flex: 1; overflow: auto; }

        /* ─── Cover type ─── */
        .slide-type-cover {
            position: relative;
            background: linear-gradient(135deg, #1a1f35, #0d1117, #161b2e) !important;
            padding: 0 !important;
            overflow: hidden;
        }

        /* ─── Section type ─── */
        .slide-type-section {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            text-align: center;
        }
        .slide-type-section h2 { font-size: 2.5em; margin-bottom: 0; }
        .slide-type-section h2::after {
            content: ''; display: block; width: 60px; height: 3px;
            background: var(--accent, #6c5ce7); margin: 16px auto 0;
            border-radius: 2px;
        }
        .slide-type-section h3 { font-weight: 400; opacity: 0.7; margin-top: 12px; }

        /* ─── Thankyou type ─── */
        .slide-type-thankyou {
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            text-align: center;
        }
        .slide-type-thankyou h1, .slide-type-thankyou h2 {
            background: linear-gradient(135deg, var(--accent-light), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3em;
        }
        .slide-type-thankyou p { opacity: 0.7; font-size: 1.1em; }

        /* Timeline: horizontal layout */
        .timeline { display: flex; align-items: flex-start; gap: 0; padding: 1rem 0; }
        .timeline .timeline-step { display: flex; flex-direction: column; align-items: center; text-align: center; flex: 1; position: relative; }
        .timeline .timeline-dot { width: 2.2rem; height: 2.2rem; border-radius: 50%; background: var(--surface); border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; color: var(--text-muted); z-index: 1; transition: all 0.3s ease; }
        .timeline .timeline-step.active .timeline-dot { background: var(--accent); border-color: var(--accent); color: #fff; box-shadow: 0 0 12px var(--accent-glow); }
        .timeline .timeline-label { margin-top: 0.5rem; font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
        .timeline .timeline-desc { margin-top: 0.25rem; font-size: 0.78rem; color: var(--text-secondary); max-width: 120px; }
        .timeline .timeline-connector { flex: 1; height: 2px; background: var(--border); align-self: center; margin: 0 -4px; position: relative; top: 1.1rem; }

        /* ─── Compare type: styled cards ─── */
        .slide-type-compare .columns-2 { gap: 32px; }
        .slide-type-compare .col {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 24px;
        }
        .slide-type-compare .col h3 {
            margin-top: 0; padding-bottom: 8px;
            border-bottom: 2px solid var(--accent, #6c5ce7);
            margin-bottom: 12px;
        }

        /* ─── Checklist type: styled checkboxes ─── */
        .slide-type-checklist li {
            list-style: none;
            padding: 6px 0;
        }
        .slide-type-checklist input[type="checkbox"] {
            width: 18px; height: 18px;
            margin-right: 8px;
            accent-color: var(--accent, #6c5ce7);
        }

        /* ─── Tabs type: tab bar + panels ─── */
        .slide-type-tabs .tab-bar {
            display: flex; gap: 0;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            margin-bottom: 16px;
        }
        .slide-type-tabs .tab-bar .tab-btn {
            padding: 10px 20px;
            cursor: pointer;
            border: none;
            background: transparent;
            color: inherit;
            opacity: 0.5;
            font-size: 0.9em; font-weight: 600;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: opacity 0.2s, border-color 0.2s;
        }
        .slide-type-tabs .tab-bar .tab-btn:hover { opacity: 0.8; }
        .slide-type-tabs .tab-bar .tab-btn.active {
            opacity: 1;
            border-bottom-color: var(--accent, #6c5ce7);
        }
        .slide-type-tabs .tab-content { display: none; }
        .slide-type-tabs .tab-content.active { display: block; }

        /* Code blocks */
        .code-block { background: #0d1117; border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; font-family: var(--font-mono); font-size: 0.85rem; line-height: 1.65; color: #c9d1d9; overflow-x: auto; position: relative; }
        .code-block .keyword { color: #ff7b72; }
        .code-block .string { color: #a5d6ff; }
        .code-block .comment { color: #8b949e; font-style: italic; }
        .code-block .number { color: #79c0ff; }
        .code-label { position: absolute; top: 8px; right: 12px; font-size: 0.7rem; color: var(--text-muted); background: var(--bg-secondary); padding: 2px 8px; border-radius: 4px; }

        /* Checklist */
        .checklist { list-style: none; padding-left: 0; }
        .checklist li { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.6rem; border-radius: 0.33rem; cursor: pointer; transition: background 0.15s ease; }
        .checklist li:hover { background: var(--surface); }
        .checklist li .check { width: 1rem; height: 1rem; border: 2px solid var(--border); border-radius: 0.25rem; display: flex; align-items: center; justify-content: center; transition: all 0.15s ease; flex-shrink: 0; }
        .checklist li.checked .check { background: var(--green); border-color: var(--green); }
        .checklist li.checked .check::after { content: '\\2713'; color: #fff; font-size: 0.7rem; }
        .checklist li.checked .checklist-text { text-decoration: line-through; opacity: 0.6; }

        /* Quiz */
        .quiz { display: flex; flex-direction: column; gap: 1rem; }
        .quiz-question { font-size: 1.2rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem; }
        .quiz-options { display: flex; flex-direction: column; gap: 0.5rem; }
        .quiz-options .quiz-option { padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: 0.5rem; background: var(--bg-card); color: var(--text-primary); font-size: 1rem; text-align: left; cursor: pointer; transition: all 0.15s ease; font-family: inherit; }
        .quiz-options .quiz-option:hover { border-color: var(--accent); background: var(--surface); }
        .quiz-options .quiz-option.selected-correct { border-color: var(--green); background: rgba(0,184,148,0.15); }
        .quiz-options .quiz-option.selected-wrong { border-color: var(--red); background: rgba(225,112,85,0.15); }
        .quiz-feedback { font-size: 0.9rem; padding: 0.5rem; min-height: 1.5rem; }

        /* Cards grid */
        .col-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .col-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.83rem; }
        .card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; transition: border-color 0.15s ease; }
        .card:hover { border-color: var(--accent); }
        .card-title { font-size: 1.05rem; font-weight: 600; color: var(--text-accent); margin-bottom: 0.4rem; }

        /* Compare toggle */
        .compare-toggle { display: flex; gap: 0; border-radius: 0.42rem; overflow: hidden; border: 1px solid var(--border); margin-bottom: 1rem; width: fit-content; }
        .compare-btn { padding: 0.5rem 1.2rem; border: none; background: var(--surface); color: var(--text-muted); font-family: inherit; font-size: 0.9rem; cursor: pointer; transition: all 0.15s ease; }
        .compare-btn.active { background: var(--accent); color: #fff; }
        .compare-highlight { border-color: var(--accent) !important; box-shadow: 0 0 12px var(--accent-glow); }
    </style>
</head>
<body>
    <div class="toolbar">
        <div class="toolbar-left">
            <span class="slide-counter">Slide ${slide.index + 1} of ${totalSlides}</span>
            ${slide.type !== 'content' ? `<span class="slide-type">@${slide.type}</span>` : ''}
        </div>
        <div class="nav-buttons">
            <button class="nav-button" onclick="prevSlide()" ${slide.index === 0 ? 'disabled' : ''}>Previous</button>
            <button class="nav-button" onclick="nextSlide()" ${slide.index === totalSlides - 1 ? 'disabled' : ''}>Next</button>
        </div>
    </div>
    <div class="slide-container">
        <div class="slide-wrapper">
            <div class="${slideClasses}" data-remarp-id="${sid}">
                ${headerHtml}
                ${renderedContent}
                ${footerHtml}
                ${paginationHtml}
                <button class="remarp-slide-edit-btn" id="slideEditBtn">Edit</button>
            </div>${hasNotes ? `
            <div class="notes-panel">
                <div class="notes-panel-content">${this._styleNotes(rawNotes)}</div>
            </div>` : ''}
        </div>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        window._remarpEditMode = false;
        window._remarpPostMessage = function(msg) { vscode.postMessage(msg); };

        function nextSlide() {
            vscode.postMessage({ command: 'nextSlide' });
        }

        function prevSlide() {
            vscode.postMessage({ command: 'prevSlide' });
        }

        document.addEventListener('keydown', (e) => {
            // Disable arrow key navigation in edit mode
            if (window._remarpEditMode) return;
            if (e.key === 'ArrowRight' || e.key === ' ') {
                nextSlide();
            } else if (e.key === 'ArrowLeft') {
                prevSlide();
            }
        });

        function scaleSlide() {
            const container = document.querySelector('.slide-container');
            const wrapper = document.querySelector('.slide-wrapper');
            if (!container || !wrapper) return;
            const cw = container.clientWidth - 16;
            const ch = container.clientHeight - 16;
            const wrapperHeight = wrapper.scrollHeight;
            const scale = Math.min(cw / 1280, ch / wrapperHeight);
            wrapper.style.transform = 'scale(' + scale + ')';
        }
        scaleSlide();
        window.addEventListener('resize', scaleSlide);
        new ResizeObserver(scaleSlide).observe(document.querySelector('.slide-container'));

        // Per-slide Edit button
        (function() {
            const editBtn = document.getElementById('slideEditBtn');
            const slide = document.querySelector('.slide');
            if (!editBtn || !slide) return;
            editBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                slide.classList.toggle('edit-mode');
                window._remarpEditMode = slide.classList.contains('edit-mode');
                if (window._remarpEditMode) {
                    editBtn.textContent = 'Done';
                    editBtn.classList.add('active');
                    // Lazy-init the full visual editor (resize handles, property panel)
                    if (!window._remarpVisualEditor && window._RemarpVisualEditorClass) {
                        window._remarpVisualEditor = new window._RemarpVisualEditorClass();
                    }
                    // Lazy-init the canvas editor
                    if (!window._remarpCanvasEditor && window._RemarpCanvasEditorClass) {
                        window._remarpCanvasEditor = new window._RemarpCanvasEditorClass();
                    }
                } else {
                    editBtn.textContent = 'Edit';
                    editBtn.classList.remove('active');
                    if (window._remarpVisualEditor) {
                        window._remarpVisualEditor.deselectAll();
                    }
                    // Flush buffered CSS changes to .md file
                    vscode.postMessage({ command: 'editDone' });
                }
            });
        })();
    </script>
    <script src="${editModeJsUri}"></script>
    <script src="${this._panel.webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'media', 'canvas-editor.js'))}"></script>
    <script>
        // Tab switching
        (function() {
            const slide = document.querySelector('.slide-type-tabs');
            if (!slide) return;
            const btns = Array.from(slide.querySelectorAll('.tab-bar .tab-btn'));
            const panels = Array.from(slide.querySelectorAll('.tab-content'));
            btns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const tabId = btn.getAttribute('data-tab');
                    btns.forEach(b => b.classList.remove('active'));
                    panels.forEach(p => p.classList.remove('active'));
                    btn.classList.add('active');
                    const target = slide.querySelector('.tab-content[data-tab="' + tabId + '"]');
                    if (target) target.classList.add('active');
                });
            });
        })();

        // Compare toggle
        (function() {
            const slide = document.querySelector('.slide-type-compare');
            if (!slide) return;
            const btns = Array.from(slide.querySelectorAll('.compare-btn'));
            const cards = Array.from(slide.querySelectorAll('.compare-content'));
            btns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const idx = btn.getAttribute('data-compare');
                    btns.forEach(b => b.classList.remove('active'));
                    cards.forEach(c => c.classList.remove('compare-highlight'));
                    btn.classList.add('active');
                    const target = slide.querySelector('.compare-content[data-compare="' + idx + '"]');
                    if (target) target.classList.add('compare-highlight');
                });
            });
        })();

        // Checklist toggle
        (function() {
            const slide = document.querySelector('.slide-type-checklist');
            if (!slide) return;
            slide.querySelectorAll('.checklist li').forEach(li => {
                li.addEventListener('click', () => {
                    li.classList.toggle('checked');
                });
            });
        })();

        // Quiz answer check
        (function() {
            const slide = document.querySelector('.slide-type-quiz');
            if (!slide) return;
            const options = Array.from(slide.querySelectorAll('.quiz-option'));
            const feedback = slide.querySelector('.quiz-feedback');
            let answered = false;
            options.forEach(opt => {
                opt.addEventListener('click', () => {
                    if (answered) return;
                    answered = true;
                    const isCorrect = opt.getAttribute('data-correct') === 'true';
                    opt.classList.add(isCorrect ? 'selected-correct' : 'selected-wrong');
                    // Show correct answer
                    options.forEach(o => {
                        if (o.getAttribute('data-correct') === 'true') o.classList.add('selected-correct');
                        o.style.pointerEvents = 'none';
                    });
                    if (feedback) {
                        feedback.textContent = isCorrect ? 'Correct!' : 'Incorrect - see the highlighted answer above.';
                        feedback.style.color = isCorrect ? 'var(--green)' : 'var(--red)';
                    }
                });
            });
        })();

        // Timeline step animation
        (function() {
            const timeline = document.querySelector('.timeline');
            if (!timeline) return;
            const steps = Array.from(timeline.querySelectorAll('.timeline-step'));
            let currentStep = 0;
            function activateStep(idx) {
                steps.forEach((s, i) => {
                    s.classList.toggle('active', i === idx);
                });
            }
            if (steps.length > 0) activateStep(0);
            // Auto-advance every 2s
            if (steps.length > 1) {
                setInterval(() => {
                    currentStep = (currentStep + 1) % steps.length;
                    activateStep(currentStep);
                }, 2000);
            }
        })();
    </script>
</body>
</html>`;
    }

    private _transformByType(slideType: string, content: string, slide: Slide, fm: Record<string, string>): string {
        switch (slideType) {
            case 'cover':
                return this._renderCoverContent(content, fm);
            case 'section':
                return this._renderSectionContent(content);
            case 'thankyou':
                return this._renderThankyouContent(content);
            case 'tabs':
                return this._renderTabsContent(content);
            case 'code':
                return this._renderCodeContent(content);
            case 'compare':
                return this._renderCompareContent(content);
            case 'steps':
                return this._renderStepsContent(content, slide);
            case 'timeline':
                return this._renderTimelineContent(content);
            case 'checklist':
                return this._renderChecklistContent(content);
            case 'quiz':
                return this._renderQuizContent(content);
            case 'cards':
                return this._renderCardsContent(content, slide);
            default:
                return this._wrapHeadingBody(content);
        }
    }

    private _renderCoverContent(content: string, fm: Record<string, string>): string {
        const speaker = fm['speaker'] || fm['author'] || '';
        const role = fm['role'] || fm['title'] || '';

        // Extract h1 (title), h2 (subtitle), remaining (speaker info)
        const h1Match = content.match(/<h1[^>]*>([\s\S]*?)<\/h1>/);
        const h2Match = content.match(/<h2[^>]*>([\s\S]*?)<\/h2>/);
        const title = h1Match ? h1Match[1] : '';
        const subtitle = h2Match ? h2Match[1] : '';

        // Remove h1/h2 from remaining
        let remaining = content;
        if (h1Match) remaining = remaining.replace(h1Match[0], '');
        if (h2Match) remaining = remaining.replace(h2Match[0], '');
        remaining = remaining.replace(/<p>\s*<\/p>/g, '').trim();

        let speakerHtml = '';
        if (speaker || role || remaining) {
            const speakerName = speaker || '';
            const speakerRole = role || '';
            const extraInfo = remaining.replace(/<\/?p>/g, '').trim();
            const parts = [speakerName, speakerRole, extraInfo].filter(Boolean);
            speakerHtml = `<div style="position:absolute;left:5%;top:76%;font-size:0.95rem;color:var(--text-secondary);max-width:50%;">${parts.join('<br>')}</div>`;
        }

        return `<div style="position:absolute;top:0;right:0;width:60%;height:60%;background:radial-gradient(ellipse at 80% 20%, var(--accent-glow) 0%, transparent 70%);pointer-events:none;"></div>
<div style="position:absolute;left:5%;top:42%;width:80px;height:3px;background:var(--accent);border-radius:2px;"></div>
<h1 style="position:absolute;left:5%;top:45%;font-size:2.8rem;font-weight:700;color:var(--text-primary);max-width:70%;line-height:1.2;margin:0;">${title}</h1>
${subtitle ? `<div style="position:absolute;left:5%;top:60%;font-size:1.3rem;color:var(--text-secondary);max-width:60%;">${subtitle}</div>` : ''}
${speakerHtml}`;
    }

    private _renderSectionContent(content: string): string {
        // Section slides: just centered heading, handled by CSS
        return content;
    }

    private _renderThankyouContent(content: string): string {
        return `${content}<p style="margin-top:1.5rem;font-size:1.1rem;color:var(--text-secondary);opacity:0.8;">수고하셨습니다!</p>`;
    }

    private _renderTabsContent(content: string): string {
        // Convert .tab-block elements into a tab-bar + tab-content structure
        const tabBlockRegex = /<div class="tab-block"[^>]*><div class="tab-title">([^<]*)<\/div><div class="tab-content">([\s\S]*?)<\/div><\/div>/g;
        const tabs: { title: string; content: string; id: string }[] = [];
        let match;
        let contentWithoutTabs = content;

        while ((match = tabBlockRegex.exec(content)) !== null) {
            tabs.push({ title: match[1], content: match[2], id: `tab-${tabs.length}` });
        }

        if (tabs.length === 0) { return this._wrapHeadingBody(content); }

        // Remove original tab-block elements from content
        contentWithoutTabs = content.replace(tabBlockRegex, '');

        // Build tab bar
        const tabBar = `<div class="tab-bar">${tabs.map((t, i) =>
            `<div class="tab-btn${i === 0 ? ' active' : ''}" data-tab="${t.id}">${this._escapeHtml(t.title)}</div>`
        ).join('')}</div>`;

        // Build tab panels
        const tabPanels = tabs.map((t, i) =>
            `<div class="tab-content${i === 0 ? ' active' : ''}" data-tab="${t.id}">${t.content}</div>`
        ).join('');

        // Extract heading from remaining content
        const headingMatch = contentWithoutTabs.match(/(<h[12][^>]*>[\s\S]*?<\/h[12]>)/);
        const heading = headingMatch ? headingMatch[1] : '';
        const body = headingMatch ? contentWithoutTabs.replace(headingMatch[0], '') : contentWithoutTabs;
        const cleanBody = body.replace(/<p>\s*<\/p>/g, '').trim();

        return `${heading ? `<div class="slide-header">${heading}</div>` : ''}${cleanBody}${tabBar}${tabPanels}`;
    }

    private _renderCodeContent(content: string): string {
        const highlighted = content.replace(
            /(<pre><code[^>]*(?:class="language-(\w+)")?[^>]*>)([\s\S]*?)(<\/code><\/pre>)/g,
            (_match, _pre, lang, code, _post) => {
                let hl = code;
                // Keywords
                hl = hl.replace(/\b(import|from|export|default|const|let|var|function|class|return|if|else|for|while|try|catch|async|await|new|this|def|self|print|lambda|with|as|raise|yield)\b/g,
                    '<span class="keyword">$1</span>');
                // Strings
                hl = hl.replace(/(&quot;[^&]*?&quot;|&#39;[^&]*?&#39;|"[^"]*?"|'[^']*?')/g,
                    '<span class="string">$1</span>');
                // Comments
                hl = hl.replace(/(\/\/.*$|#.*$)/gm,
                    '<span class="comment">$1</span>');
                // Numbers
                hl = hl.replace(/\b(\d+\.?\d*)\b/g,
                    '<span class="number">$1</span>');

                const langLabel = lang ? `<span class="code-label">${lang}</span>` : '';
                return `<div class="code-block">${langLabel}<pre style="margin:0;background:none;border:none;padding:0;"><code>${hl}</code></pre></div>`;
            }
        );
        return this._wrapHeadingBody(highlighted);
    }

    private _renderCompareContent(content: string): string {
        // Extract column headings and content from .columns-2 structure
        const colRegex = /<div class="col"[^>]*>([\s\S]*?)<\/div>/g;
        const cols: { heading: string; body: string }[] = [];
        let match;
        while ((match = colRegex.exec(content)) !== null) {
            const colHtml = match[1];
            const h3Match = colHtml.match(/<h3>([\s\S]*?)<\/h3>/);
            const heading = h3Match ? h3Match[1] : `Option ${cols.length + 1}`;
            const body = h3Match ? colHtml.replace(h3Match[0], '') : colHtml;
            cols.push({ heading, body });
        }
        if (cols.length < 2) return this._wrapHeadingBody(content);

        // Extract slide heading (h1/h2) from content before columns
        const headingMatch = content.match(/^([\s\S]*?)(<div class="columns-2)/);
        const slideHeading = headingMatch ? headingMatch[1].replace(/<p>\s*<\/p>/g, '').trim() : '';

        const toggleBar = `<div class="compare-toggle">${cols.map((c, i) =>
            `<button class="compare-btn${i === 0 ? ' active' : ''}" data-compare="${i}">${this._escapeHtml(c.heading)}</button>`
        ).join('')}</div>`;

        const cards = `<div class="col-2">${cols.map((c, i) =>
            `<div class="card compare-content${i === 0 ? ' compare-highlight' : ''}" data-compare="${i}">${c.body}</div>`
        ).join('')}</div>`;

        return `${slideHeading ? `<div class="slide-header">${slideHeading}</div>` : ''}
<div class="slide-body">${toggleBar}${cards}</div>`;
    }

    private _renderStepsContent(content: string, slide: Slide): string {
        // Extract heading
        let slideHeading = '';
        let bodyContent = content;
        const hMatch = content.match(/(<h[12][^>]*>[\s\S]*?<\/h[12]>)/);
        if (hMatch) {
            slideHeading = hMatch[1];
            bodyContent = content.replace(hMatch[0], '');
        }

        // Read directives
        const shape = slide.content.match(/@steps-shape:\s*(\w+)/)?.[1] || 'circle';
        const layout = slide.content.match(/@steps-layout:\s*(\w+)/)?.[1] || 'horizontal';
        const iconPath = slide.content.match(/@steps-icon:\s*(\S+)/)?.[1] || '';

        // Parse steps from ### headings or numbered list
        const steps: { title: string; desc: string }[] = [];
        const h3Regex = /<h3[^>]*>([\s\S]*?)<\/h3>([\s\S]*?)(?=<h3|$)/g;
        let match;
        while ((match = h3Regex.exec(bodyContent)) !== null) {
            const desc = match[2].replace(/<\/?p>/g, '').trim();
            steps.push({ title: match[1], desc });
        }

        // Fallback: parse numbered list items
        if (steps.length === 0) {
            const liRegex = /<li>([\s\S]*?)<\/li>/g;
            while ((match = liRegex.exec(bodyContent)) !== null) {
                const text = match[1];
                const boldMatch = text.match(/<strong>(.*?)<\/strong>\s*[-—]\s*(.*)/);
                if (boldMatch) {
                    steps.push({ title: boldMatch[1], desc: boldMatch[2].trim() });
                } else {
                    steps.push({ title: text, desc: '' });
                }
            }
        }

        if (steps.length === 0) return this._wrapHeadingBody(content);

        const stepsHtml = steps.map((step, i) => {
            const markerContent = (shape === 'icon' && iconPath)
                ? `<img src="${this._escapeHtml(iconPath)}" alt="">`
                : `${i + 1}`;
            const connector = i < steps.length - 1 ? '<div class="step-connector"></div>' : '';
            const descHtml = step.desc ? `<div class="step-desc">${step.desc}</div>` : '';
            return `<div class="step-item">
    <div class="step-marker">${markerContent}</div>
    <div class="step-label">${step.title}</div>
    ${descHtml}
</div>${connector}`;
        }).join('\n');

        return `${slideHeading ? `<div class="slide-header">${slideHeading}</div>` : ''}
<div class="slide-body"><div class="steps-container steps--${this._escapeHtml(layout)} steps--${this._escapeHtml(shape)}">${stepsHtml}</div></div>`;
    }

    private _renderTimelineContent(content: string): string {
        // Extract timeline steps from .timeline-step elements
        const stepRegex = /<div class="timeline-step"[^>]*><span class="step-label"[^>]*>([^<]*)<\/span><div>([\s\S]*?)<\/div><\/div>/g;
        const steps: { label: string; content: string }[] = [];
        let match;
        while ((match = stepRegex.exec(content)) !== null) {
            steps.push({ label: match[1], content: match[2] });
        }
        if (steps.length === 0) return this._wrapHeadingBody(content);

        // Extract heading before timeline steps
        const headingMatch = content.match(/^([\s\S]*?)(<div class="timeline-step)/);
        const slideHeading = headingMatch ? headingMatch[1].replace(/<p>\s*<\/p>/g, '').trim() : '';

        // Build horizontal timeline
        const timelineHtml = steps.map((step, i) => {
            const connector = i < steps.length - 1 ? '<div class="timeline-connector"></div>' : '';
            // Extract h3 as label, rest as description
            const h3Match = step.content.match(/<h3>([\s\S]*?)<\/h3>/);
            const label = h3Match ? h3Match[1] : '';
            const desc = h3Match ? step.content.replace(h3Match[0], '').trim() : step.content;
            return `<div class="timeline-step">
    <div class="timeline-dot">${step.label}</div>
    <div class="timeline-label">${label || step.label}</div>
    <div class="timeline-desc">${desc}</div>
</div>${connector}`;
        }).join('\n');

        return `${slideHeading ? `<div class="slide-header">${slideHeading}</div>` : ''}
<div class="slide-body"><div class="timeline">${timelineHtml}</div></div>`;
    }

    private _renderChecklistContent(content: string): string {
        // Extract heading
        let slideHeading = '';
        let bodyContent = content;

        const hMatch = content.match(/(<h[12][^>]*>[\s\S]*?<\/h[12]>)/);
        if (hMatch) {
            slideHeading = hMatch[1];
            bodyContent = content.replace(hMatch[0], '');
        }

        // Convert list items to checklist structure
        bodyContent = bodyContent.replace(/<ul>([\s\S]*?)<\/ul>/g, (_match, items) => {
            const converted = items.replace(/<li>([\s\S]*?)<\/li>/g, (_m: string, text: string) => {
                const isChecked = text.match(/^<input type="checkbox" checked>/);
                let cleanText = text.replace(/^<input type="checkbox"[^>]*>\s*/, '');
                // Also handle raw [ ] / [x] markers
                if (cleanText.match(/^\[x\]\s*/)) {
                    cleanText = cleanText.replace(/^\[x\]\s*/, '');
                    return `<li class="checked"><span class="check"></span><span class="checklist-text">${cleanText}</span></li>`;
                }
                if (cleanText.match(/^\[ \]\s*/)) {
                    cleanText = cleanText.replace(/^\[ \]\s*/, '');
                    return `<li><span class="check"></span><span class="checklist-text">${cleanText}</span></li>`;
                }
                const checkedClass = isChecked ? ' class="checked"' : '';
                return `<li${checkedClass}><span class="check"></span><span class="checklist-text">${cleanText}</span></li>`;
            });
            return `<ul class="checklist">${converted}</ul>`;
        });

        return `${slideHeading ? `<div class="slide-header">${slideHeading}</div>` : ''}
<div class="slide-body">${bodyContent}</div>`;
    }

    private _renderQuizContent(content: string): string {
        // Extract heading
        const hMatch = content.match(/(<h[12][^>]*>[\s\S]*?<\/h[12]>)/);
        const slideHeading = hMatch ? hMatch[1] : '';
        let bodyContent = hMatch ? content.replace(hMatch[0], '') : content;

        // Extract question text (first h3 or first paragraph)
        const questionMatch = bodyContent.match(/(<h3>[\s\S]*?<\/h3>|<p>[\s\S]*?<\/p>)/);
        let questionHtml = '';
        if (questionMatch) {
            // Only use as question if it's before the first quiz-option
            const questionIdx = bodyContent.indexOf(questionMatch[0]);
            const optionIdx = bodyContent.indexOf('class="quiz-option');
            if (optionIdx === -1 || questionIdx < optionIdx) {
                questionHtml = `<div class="quiz-question">${questionMatch[1] || questionMatch[0]}</div>`;
                bodyContent = bodyContent.replace(questionMatch[0], '');
            }
        }

        // Convert quiz-option divs to buttons
        bodyContent = bodyContent.replace(
            /<div class="quiz-option( correct)?"[^>]*>([\s\S]*?)<\/div>/g,
            (_match, correct, text) => {
                const dataCorrect = correct ? ' data-correct="true"' : '';
                return `<button class="quiz-option"${dataCorrect}>${text}</button>`;
            }
        );

        return `${slideHeading ? `<div class="slide-header">${slideHeading}</div>` : ''}
<div class="slide-body">
    <div class="quiz">${questionHtml}<div class="quiz-options">${bodyContent}</div><div class="quiz-feedback"></div></div>
</div>`;
    }

    private _renderCardsContent(content: string, slide: Slide): string {
        // Extract heading
        const hMatch = content.match(/(<h[12][^>]*>[\s\S]*?<\/h[12]>)/);
        const slideHeading = hMatch ? hMatch[1] : '';
        let bodyContent = hMatch ? content.replace(hMatch[0], '') : content;

        // Try to extract cards from .cell elements
        const cellRegex = /<div class="cell"[^>]*>([\s\S]*?)<\/div>/g;
        const cards: string[] = [];
        let match;
        while ((match = cellRegex.exec(bodyContent)) !== null) {
            cards.push(match[1]);
        }

        // If no cells, try to split by h3 headings
        if (cards.length === 0) {
            const h3Parts = bodyContent.split(/(?=<h3>)/);
            for (const part of h3Parts) {
                if (part.trim() && part.includes('<h3>')) {
                    cards.push(part);
                }
            }
        }

        if (cards.length === 0) return this._wrapHeadingBody(content);

        // Determine column count from @columns directive
        const colMatch = slide.content.match(/@columns\s+(\d+)/);
        const colCount = colMatch ? parseInt(colMatch[1]) : Math.min(cards.length, 3);

        const cardsHtml = cards.map(c => {
            const titleMatch = c.match(/<h3>([\s\S]*?)<\/h3>/);
            const title = titleMatch ? `<div class="card-title">${titleMatch[1]}</div>` : '';
            const body = titleMatch ? c.replace(titleMatch[0], '') : c;
            return `<div class="card">${title}${body}</div>`;
        }).join('');

        return `${slideHeading ? `<div class="slide-header">${slideHeading}</div>` : ''}
<div class="slide-body"><div class="col-${colCount}">${cardsHtml}</div></div>`;
    }

    private _wrapHeadingBody(content: string): string {
        // Split at first h1/h2 heading into heading area + body area
        const headingMatch = content.match(/^([\s\S]*?)(<h[12][^>]*>[\s\S]*?<\/h[12]>)([\s\S]*)$/);
        if (headingMatch) {
            const before = headingMatch[1].replace(/<p>\s*<\/p>/g, '').trim();
            const heading = headingMatch[2];
            const after = headingMatch[3];
            return `${before}<div class="slide-header">${heading}</div><div class="slide-body">${after}</div>`;
        }
        return `<div class="slide-body">${content}</div>`;
    }

    private _escapeHtml(text: string): string {
        return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    private _styleNotes(raw: string): string {
        let notes = raw;
        notes = notes.replace(/\{timing:\s*([^}]+)\}/g, '<span class="notes-timing">&#128339; $1</span>');
        notes = notes.replace(/\{cue:\s*([^}]+)\}/g, '<span class="notes-cue">&#10148; $1</span>');
        return notes;
    }

    private _parseBlocks(content: string, slideIndex: number = 0): { text: string; rendered: string[]; notes: string; notesArg: string } {
        // Parse :::block ... ::: structures into HTML layout elements.
        // Returns text with placeholders (\x00BLK0\x00), an array of rendered HTML,
        // and collected notes content (extracted from :::notes blocks).

        const lines = content.split('\n');
        const result: string[] = [];
        const rendered: string[] = [];
        const notesCollector: string[] = [];
        let notesArg = '';
        let i = 0;

        // Counters for data-remarp-id generation
        let colCounter = 0;
        let cellCounter = 0;
        let tabCounter = 0;
        let stepCounter = 0;
        let optionCounter = 0;

        const sid = `s${slideIndex}`;

        while (i < lines.length) {
            const blockMatch = lines[i].match(/^:::\s*(\w+)(?:\s+(.*))?$/);

            if (blockMatch) {
                const blockType = blockMatch[1];
                const blockArg = blockMatch[2]?.trim() || '';
                // Collect inner content until closing :::
                const innerLines: string[] = [];
                i++;
                while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
                    innerLines.push(lines[i]);
                    i++;
                }
                i++; // skip closing :::

                const inner = innerLines.join('\n');

                const emit = (html: string) => {
                    const idx = rendered.length;
                    rendered.push(html);
                    result.push(`\x00BLK${idx}\x00`);
                };

                switch (blockType) {
                    case 'canvas': {
                        const elementCount = (inner.match(/^(box|circle|arrow|icon|text|group)\s/gm) || []).length;
                        const stepCount = (inner.match(/^step\s/gm) || []).length;
                        const summary = [
                            elementCount > 0 ? `${elementCount} elements` : '',
                            stepCount > 0 ? `${stepCount} steps` : ''
                        ].filter(Boolean).join(', ');
                        const escaped = inner.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        emit(`<div class="canvas-placeholder" data-remarp-id="${sid}-canvas">`
                            + `<div class="canvas-header">&#9881; Canvas DSL${summary ? ` (${summary})` : ''}</div>`
                            + `<pre class="canvas-source">${escaped}</pre>`
                            + `</div>`);
                        break;
                    }
                    case 'left': {
                        const leftHtml = this._renderInlineMarkdown(inner, slideIndex);
                        let rightHtml = '';
                        while (i < lines.length && lines[i].trim() === '') { i++; }
                        const rightMatch = i < lines.length && lines[i].match(/^:::\s*right(?:\s+.*)?$/);
                        if (rightMatch) {
                            const rightInner: string[] = [];
                            i++;
                            while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
                                rightInner.push(lines[i]);
                                i++;
                            }
                            i++;
                            rightHtml = this._renderInlineMarkdown(rightInner.join('\n'), slideIndex);
                        }
                        emit(`<div class="columns-2" data-remarp-id="${sid}-columns"><div class="col" data-remarp-id="${sid}-left">${leftHtml}</div><div class="col" data-remarp-id="${sid}-right">${rightHtml}</div></div>`);
                        break;
                    }
                    case 'right':
                        emit(`<div class="columns-2" data-remarp-id="${sid}-columns"><div class="col"></div><div class="col" data-remarp-id="${sid}-right">${this._renderInlineMarkdown(inner, slideIndex)}</div></div>`);
                        break;
                    case 'col': {
                        const cols: { html: string; id: string }[] = [{ html: this._renderInlineMarkdown(inner, slideIndex), id: `${sid}-col-${colCounter++}` }];
                        while (i < lines.length) {
                            let peek = i;
                            while (peek < lines.length && lines[peek].trim() === '') { peek++; }
                            const nextCol = peek < lines.length && lines[peek].match(/^:::\s*col(?:\s+.*)?$/);
                            if (!nextCol) { break; }
                            i = peek + 1;
                            const colInner: string[] = [];
                            while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
                                colInner.push(lines[i]);
                                i++;
                            }
                            i++;
                            cols.push({ html: this._renderInlineMarkdown(colInner.join('\n'), slideIndex), id: `${sid}-col-${colCounter++}` });
                        }
                        const colClass = cols.length <= 2 ? 'columns-2' : 'columns-3';
                        emit(`<div class="${colClass}" data-remarp-id="${sid}-cols">${cols.map(c => `<div class="col" data-remarp-id="${c.id}">${c.html}</div>`).join('')}</div>`);
                        break;
                    }
                    case 'cell': {
                        const cells: { html: string; id: string }[] = [{ html: this._renderInlineMarkdown(inner, slideIndex), id: `${sid}-cell-${cellCounter++}` }];
                        while (i < lines.length) {
                            let peek = i;
                            while (peek < lines.length && lines[peek].trim() === '') { peek++; }
                            const nextCell = peek < lines.length && lines[peek].match(/^:::\s*cell(?:\s+.*)?$/);
                            if (!nextCell) { break; }
                            i = peek + 1;
                            const cellInner: string[] = [];
                            while (i < lines.length && !/^:::\s*$/.test(lines[i])) {
                                cellInner.push(lines[i]);
                                i++;
                            }
                            i++;
                            cells.push({ html: this._renderInlineMarkdown(cellInner.join('\n'), slideIndex), id: `${sid}-cell-${cellCounter++}` });
                        }
                        emit(`<div class="grid-cells" data-remarp-id="${sid}-grid">${cells.map(c => `<div class="cell" data-remarp-id="${c.id}">${c.html}</div>`).join('')}</div>`);
                        break;
                    }
                    case 'click':
                        emit(`<div class="click-block" data-remarp-id="${sid}-click">${this._renderInlineMarkdown(inner, slideIndex)}</div>`);
                        break;
                    case 'tab':
                        emit(`<div class="tab-block" data-remarp-id="${sid}-tab-${tabCounter++}"><div class="tab-title">${this._escapeHtml(blockArg)}</div><div class="tab-content">${this._renderInlineMarkdown(inner, slideIndex)}</div></div>`);
                        break;
                    case 'steps':
                        emit(`<div class="steps-container" data-remarp-id="${sid}-steps">${this._renderInlineMarkdown(inner, slideIndex)}</div>`);
                        break;
                    case 'item':
                        emit(`<div class="list-item" data-remarp-id="${sid}-item">${this._renderInlineMarkdown(inner, slideIndex)}</div>`);
                        break;
                    case 'step':
                        emit(`<div class="timeline-step" data-remarp-id="${sid}-step-${stepCounter++}"><span class="step-label">${this._escapeHtml(blockArg)}</span><div>${this._renderInlineMarkdown(inner, slideIndex)}</div></div>`);
                        break;
                    case 'option':
                        emit(`<div class="quiz-option" data-remarp-id="${sid}-option-${optionCounter++}">${this._renderInlineMarkdown(inner, slideIndex)}</div>`);
                        break;
                    case 'fragment':
                        emit(`<div class="fragment-block" data-remarp-id="${sid}-fragment">${this._renderInlineMarkdown(inner, slideIndex)}</div>`);
                        break;
                    case 'notes':
                        // Collect notes for the panel below the slide
                        notesArg = blockArg; // e.g. {timing: 3min}
                        if (inner.trim()) { notesCollector.push(inner); }
                        break;
                    case 'prompt': {
                        const escaped = inner.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        emit(`<div class="prompt-placeholder" data-remarp-id="${sid}-prompt">`
                            + `<div class="prompt-header">\u{1F4AC} Diagram Prompt</div>`
                            + `<pre class="prompt-source">${escaped}</pre>`
                            + `<div class="prompt-footer">Agent will resolve this prompt into :::canvas DSL</div>`
                            + `</div>`);
                        break;
                    }
                    default:
                        emit(`<div class="block-tag" data-remarp-id="${sid}-${blockType}">::: ${blockType} ${blockArg}</div>${this._renderInlineMarkdown(inner, slideIndex)}`);
                        break;
                }
            } else {
                result.push(lines[i]);
                i++;
            }
        }

        return { text: result.join('\n'), rendered, notes: notesCollector.join('\n'), notesArg };
    }

    private _renderInlineMarkdown(content: string, slideIndex: number = 0): string {
        let html = content;
        const sid = `s${slideIndex}`;
        let quizCounter = 0;
        let liCounter = 0;

        // Preserve code blocks with placeholders
        const codeBlocks: string[] = [];
        html = html.replace(/```(\w*)[^\n]*\n([\s\S]*?)```/g, (_match, lang, code) => {
            const idx = codeBlocks.length;
            codeBlocks.push(`<pre><code class="language-${lang}">${this._escapeHtml(code)}</code></pre>`);
            return `\x00CODEBLOCK${idx}\x00`;
        });

        // Convert directives to styled spans
        html = html.replace(/^(@\w+(?:-\w+)*)\s+(.*)$/gm, '<div class="directive">$1 <span style="color: #ce9178;">$2</span></div>');

        // Quiz checkboxes: - [ ] and - [x] with data-remarp-id
        html = html.replace(/^- \[x\]\s+(.*)$/gm, (_match, text) => {
            return `<div class="quiz-option correct" data-remarp-id="${sid}-quiz-${quizCounter++}">&#9679; ${text}</div>`;
        });
        html = html.replace(/^- \[ \]\s+(.*)$/gm, (_match, text) => {
            return `<div class="quiz-option" data-remarp-id="${sid}-quiz-${quizCounter++}">&#9675; ${text}</div>`;
        });

        // Table rendering: detect lines starting with | (trailing | optional)
        html = html.replace(
            /((?:^\|.+$\n?)+)/gm,
            (tableBlock) => {
                const rows = tableBlock.trim().split('\n');
                if (rows.length < 2) { return tableBlock; }
                // Verify this looks like a table (at least 2 cells in first row)
                const firstRowCells = rows[0].split('|').filter(c => c.trim() !== '');
                if (firstRowCells.length < 2) { return tableBlock; }

                let tableHtml = '<table style="border-collapse:collapse;width:100%;margin:0.5em 0;">';
                let isHeader = true;

                rows.forEach((row) => {
                    // Skip separator row (|---|---|)
                    if (/^\|[\s\-:|]+\|?\s*$/.test(row.trim())) { return; }

                    const rawCells = row.split('|');
                    // Remove empty first element (before leading |)
                    if (rawCells[0].trim() === '') { rawCells.shift(); }
                    // Remove empty last element (after trailing |, if present)
                    if (rawCells.length > 0 && rawCells[rawCells.length - 1].trim() === '') { rawCells.pop(); }

                    const tag = isHeader ? 'th' : 'td';
                    const style = isHeader
                        ? 'style="border:1px solid rgba(255,255,255,0.2);padding:8px;background:rgba(255,255,255,0.05);text-align:left;font-weight:bold;"'
                        : 'style="border:1px solid rgba(255,255,255,0.2);padding:8px;text-align:left;"';

                    tableHtml += '<tr>';
                    rawCells.forEach(cell => {
                        tableHtml += `<${tag} ${style}>${cell.trim()}</${tag}>`;
                    });
                    tableHtml += '</tr>';
                    isHeader = false;
                });

                tableHtml += '</table>';
                return tableHtml;
            }
        );

        // Convert headers (h6 to h1, longest prefix first)
        html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>');
        html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>');
        html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');

        // Convert images (before links to avoid conflict)
        html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');

        // Convert links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

        // Convert bold and italic
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
        html = html.replace(/_(.+?)_/g, '<em>$1</em>');

        // Strikethrough
        html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');

        // Convert inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // {.click} inline syntax — hide markers, just render content directly
        html = html.replace(/\{\.click\s+animation=[^}\s]+\}/g, '');
        html = html.replace(/\{\.click\s+order=\d+\}/g, '');
        html = html.replace(/\{\.click\}/g, '');

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
        html = html.replace(/<p>(<table)/g, '$1');
        html = html.replace(/(<\/table>)<\/p>/g, '$1');

        // Restore code blocks
        html = html.replace(/\x00CODEBLOCK(\d+)\x00/g, (_match, idx) => codeBlocks[parseInt(idx)]);

        return html;
    }

    private _renderMarkdown(content: string, slideIndex: number = 0): { html: string; notes: string; notesArg: string } {
        // 1. Parse ::: blocks — extracts notes, returns placeholders for rendered blocks
        const { text, rendered, notes, notesArg } = this._parseBlocks(content, slideIndex);

        // 2. Apply inline markdown only to non-block text segments
        let html = this._renderInlineMarkdown(text, slideIndex);

        // 3. Restore rendered block HTML
        html = html.replace(/\x00BLK(\d+)\x00/g, (_match, idx) => rendered[parseInt(idx)]);

        return { html, notes, notesArg };
    }

    public dispose(): void {
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
