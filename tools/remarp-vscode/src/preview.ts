import * as vscode from 'vscode';

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

    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _document: vscode.TextDocument;
    private _currentSlideIndex: number = 0;
    private _disposables: vscode.Disposable[] = [];
    private _updateTimeout: NodeJS.Timeout | undefined;

    public static createOrShow(extensionUri: vscode.Uri, document: vscode.TextDocument): void {
        const column = vscode.ViewColumn.Beside;

        if (RemarpPreviewPanel.currentPanel) {
            RemarpPreviewPanel.currentPanel._panel.reveal(column);
            RemarpPreviewPanel.currentPanel._document = document;
            RemarpPreviewPanel.currentPanel._updateContent();
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            RemarpPreviewPanel.viewType,
            'Remarp Preview',
            column,
            {
                enableScripts: true,
                localResourceRoots: [extensionUri],
                retainContextWhenHidden: true
            }
        );

        RemarpPreviewPanel.currentPanel = new RemarpPreviewPanel(panel, extensionUri, document);
    }

    public static update(document: vscode.TextDocument): void {
        if (RemarpPreviewPanel.currentPanel && RemarpPreviewPanel.currentPanel._document.uri.toString() === document.uri.toString()) {
            RemarpPreviewPanel.currentPanel._debouncedUpdate();
        }
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

    private _getHtmlForSlide(slide: Slide, totalSlides: number): string {
        const { html: renderedContent, notes: rawNotes, notesArg } = this._renderMarkdown(slide.content);
        const hasNotes = !!rawNotes;
        const fm = this._parseFrontmatter();

        // Extract @type and @layout for slide-level CSS classes
        const slideType = slide.type || 'content';
        const layoutMatch = slide.content.match(/^@layout\s+(\S+)/m);
        const slideLayout = layoutMatch ? layoutMatch[1] : '';
        const slideClasses = ['slide', `slide-type-${slideType}`, slideLayout ? `slide-layout-${slideLayout}` : ''].filter(Boolean).join(' ');

        // Global styles from frontmatter directives
        const bgColor = fm['backgroundColor'] || '';
        const bgImage = fm['backgroundImage'] || '';
        const textColor = fm['color'] || '';
        const headerText = fm['header'] || '';
        const footerText = fm['footer'] || fm['theme'] || ''; // top-level footer only
        const showPagination = fm['pagination'] !== 'false';

        const bodyBg = bgColor || '#1e1e1e';
        const slideBg = bgColor || '#252526';
        const slideBgImage = bgImage ? `background-image: ${bgImage.startsWith('url(') ? bgImage : `url(${bgImage})`};` : '';
        const slideColor = textColor || '#e0e0e0';
        const headingColor = textColor || '#fff';

        const headerHtml = headerText
            ? `<div class="slide-header">${this._escapeHtml(headerText)}</div>`
            : '';
        const footerHtml = footerText
            ? `<div class="slide-footer">${this._escapeHtml(footerText)}</div>`
            : '';
        const paginationHtml = showPagination
            ? `<div class="slide-pagination">${slide.index + 1} / ${totalSlides}</div>`
            : '';

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
            background: ${bodyBg};
            color: ${slideColor};
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
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }
        .slide-wrapper {
            width: 960px;
            transform-origin: center center;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }
        .slide {
            background: ${slideBg};
            ${slideBgImage}
            background-size: cover;
            padding: 40px;
            width: 960px;
            height: 540px;
            position: relative;
            overflow: auto;
        }
        .slide-header {
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
            right: 40px;
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
        /* Column layouts */
        .columns-2, .columns-3 { display: flex; gap: 24px; margin: 16px 0; align-items: flex-start; }
        .columns-2 .col { flex: 1; min-width: 0; }
        .columns-3 .col { flex: 1; min-width: 0; }

        /* Grid cells */
        .grid-cells { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 16px 0; }
        .cell { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 16px; }

        /* Click blocks */
        .click-block { border-left: 3px solid var(--accent, #6c5ce7); padding: 12px 16px; margin: 12px 0; background: rgba(108,92,231,0.08); border-radius: 0 8px 8px 0; }

        /* Canvas placeholder */
        .canvas-placeholder { background: rgba(255,255,255,0.03); border: 2px dashed rgba(255,255,255,0.15); border-radius: 8px; padding: 24px; text-align: center; color: rgba(255,255,255,0.4); font-style: italic; margin: 16px 0; }

        /* Tab blocks */
        .tab-block { border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; margin: 8px 0; overflow: hidden; }
        .tab-title { background: rgba(255,255,255,0.08); padding: 8px 16px; font-weight: 600; font-size: 0.85em; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .tab-content { padding: 12px 16px; }

        /* Timeline steps */
        .timeline-step { display: flex; gap: 16px; margin: 12px 0; align-items: flex-start; }
        .step-label { background: var(--accent, #6c5ce7); color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: 700; white-space: nowrap; flex-shrink: 0; }

        /* List items */
        .list-item { padding: 8px 16px; margin: 4px 0; border-left: 2px solid rgba(255,255,255,0.15); }

        /* Quiz options */
        .quiz-option { padding: 10px 16px; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; cursor: default; }
        .quiz-option:hover { border-color: var(--accent, #6c5ce7); }
        .quiz-option.correct { border-color: #27ae60; background: rgba(39,174,96,0.08); }

        /* Fragment blocks */
        .fragment-block { padding: 8px 0; }

        /* Inline click indicator */
        .click-indicator { opacity: 0.5; font-size: 0.75em; color: var(--accent, #6c5ce7); margin-left: 4px; }

        /* Notes panel (inside slide-wrapper, below slide) */
        .notes-panel { background: #1a1a2e; border-top: 1px solid #3c3c3c; padding: 12px 20px; max-height: 150px; overflow-y: auto; }
        /* notes-marker removed — no longer used */
        .notes-keyword { color: #4ec9b0; }
        .notes-arg { color: #ce9178; }
        .notes-panel-content { font-size: 0.85em; color: #ccc; line-height: 1.5; padding: 2px 0; }
        .notes-timing { color: #ce9178; font-weight: 600; margin: 0 2px; }
        .notes-cue { color: #3498db; font-weight: 600; margin: 0 2px; }
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
        <div class="slide-wrapper">
            <div class="${slideClasses}">
                ${headerHtml}
                ${renderedContent}
                ${footerHtml}
                ${paginationHtml}
            </div>${hasNotes ? `
            <div class="notes-panel">
                <div class="notes-panel-content">${this._styleNotes(rawNotes)}</div>
            </div>` : ''}
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

        function scaleSlide() {
            const container = document.querySelector('.slide-container');
            const wrapper = document.querySelector('.slide-wrapper');
            if (!container || !wrapper) return;
            const cw = container.clientWidth - 32;
            const ch = container.clientHeight - 32;
            const wrapperHeight = wrapper.scrollHeight;
            const scale = Math.min(cw / 960, ch / wrapperHeight, 1);
            wrapper.style.transform = 'scale(' + scale + ')';
        }
        scaleSlide();
        window.addEventListener('resize', scaleSlide);
        new ResizeObserver(scaleSlide).observe(document.querySelector('.slide-container'));
    </script>
</body>
</html>`;
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

    private _parseBlocks(content: string): { text: string; rendered: string[]; notes: string; notesArg: string } {
        // Parse :::block ... ::: structures into HTML layout elements.
        // Returns text with placeholders (\x00BLK0\x00), an array of rendered HTML,
        // and collected notes content (extracted from :::notes blocks).

        const lines = content.split('\n');
        const result: string[] = [];
        const rendered: string[] = [];
        const notesCollector: string[] = [];
        let notesArg = '';
        let i = 0;

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
                    case 'canvas':
                        emit(`<div class="canvas-placeholder">&#9881; Canvas DSL (preview unavailable)</div>`);
                        break;
                    case 'left': {
                        const leftHtml = this._renderInlineMarkdown(inner);
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
                            rightHtml = this._renderInlineMarkdown(rightInner.join('\n'));
                        }
                        emit(`<div class="columns-2"><div class="col">${leftHtml}</div><div class="col">${rightHtml}</div></div>`);
                        break;
                    }
                    case 'right':
                        emit(`<div class="columns-2"><div class="col"></div><div class="col">${this._renderInlineMarkdown(inner)}</div></div>`);
                        break;
                    case 'col': {
                        const cols: string[] = [this._renderInlineMarkdown(inner)];
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
                            cols.push(this._renderInlineMarkdown(colInner.join('\n')));
                        }
                        const colClass = cols.length <= 2 ? 'columns-2' : 'columns-3';
                        emit(`<div class="${colClass}">${cols.map(c => `<div class="col">${c}</div>`).join('')}</div>`);
                        break;
                    }
                    case 'cell': {
                        const cells: string[] = [this._renderInlineMarkdown(inner)];
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
                            cells.push(this._renderInlineMarkdown(cellInner.join('\n')));
                        }
                        emit(`<div class="grid-cells">${cells.map(c => `<div class="cell">${c}</div>`).join('')}</div>`);
                        break;
                    }
                    case 'click':
                        emit(`<div class="click-block">${this._renderInlineMarkdown(inner)}</div>`);
                        break;
                    case 'tab':
                        emit(`<div class="tab-block"><div class="tab-title">${this._escapeHtml(blockArg)}</div><div class="tab-content">${this._renderInlineMarkdown(inner)}</div></div>`);
                        break;
                    case 'item':
                        emit(`<div class="list-item">${this._renderInlineMarkdown(inner)}</div>`);
                        break;
                    case 'step':
                        emit(`<div class="timeline-step"><span class="step-label">${this._escapeHtml(blockArg)}</span><div>${this._renderInlineMarkdown(inner)}</div></div>`);
                        break;
                    case 'option':
                        emit(`<div class="quiz-option">${this._renderInlineMarkdown(inner)}</div>`);
                        break;
                    case 'fragment':
                        emit(`<div class="fragment-block">${this._renderInlineMarkdown(inner)}</div>`);
                        break;
                    case 'notes':
                        // Collect notes for the panel below the slide
                        notesArg = blockArg; // e.g. {timing: 3min}
                        if (inner.trim()) { notesCollector.push(inner); }
                        break;
                    default:
                        emit(`<div class="block-tag">::: ${blockType} ${blockArg}</div>${this._renderInlineMarkdown(inner)}`);
                        break;
                }
            } else {
                result.push(lines[i]);
                i++;
            }
        }

        return { text: result.join('\n'), rendered, notes: notesCollector.join('\n'), notesArg };
    }

    private _renderInlineMarkdown(content: string): string {
        let html = content;

        // Preserve code blocks with placeholders
        const codeBlocks: string[] = [];
        html = html.replace(/```(\w*)[^\n]*\n([\s\S]*?)```/g, (_match, lang, code) => {
            const idx = codeBlocks.length;
            codeBlocks.push(`<pre><code class="language-${lang}">${this._escapeHtml(code)}</code></pre>`);
            return `\x00CODEBLOCK${idx}\x00`;
        });

        // Convert directives to styled spans
        html = html.replace(/^(@\w+(?:-\w+)*)\s+(.*)$/gm, '<div class="directive">$1 <span style="color: #ce9178;">$2</span></div>');

        // Quiz checkboxes: - [ ] and - [x]
        html = html.replace(/^- \[x\]\s+(.*)$/gm, '<div class="quiz-option correct">&#9679; $1</div>');
        html = html.replace(/^- \[ \]\s+(.*)$/gm, '<div class="quiz-option">&#9675; $1</div>');

        // Convert headers
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

        // Convert inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // {.click} inline syntax
        html = html.replace(/\{\.click\s+animation=([^}\s]+)\}/g, '<span class="click-indicator">[click: $1]</span>');
        html = html.replace(/\{\.click\s+order=(\d+)\}/g, '<span class="click-indicator">[click: #$1]</span>');
        html = html.replace(/\{\.click\}/g, '<span class="click-indicator">[click]</span>');

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

        // Restore code blocks
        html = html.replace(/\x00CODEBLOCK(\d+)\x00/g, (_match, idx) => codeBlocks[parseInt(idx)]);

        return html;
    }

    private _renderMarkdown(content: string): { html: string; notes: string; notesArg: string } {
        // 1. Parse ::: blocks — extracts notes, returns placeholders for rendered blocks
        const { text, rendered, notes, notesArg } = this._parseBlocks(content);

        // 2. Apply inline markdown only to non-block text segments
        let html = this._renderInlineMarkdown(text);

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
