import * as vscode from 'vscode';

interface SlideInfo {
    index: number;
    title: string;
    type: string;
    startLine: number;
    endLine: number;
}

export class SlideOutlineProvider implements vscode.TreeDataProvider<SlideItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<SlideItem | undefined | null | void> = new vscode.EventEmitter<SlideItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<SlideItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: SlideItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: SlideItem): Thenable<SlideItem[]> {
        if (element) {
            return Promise.resolve([]);
        }

        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'remarp') {
            return Promise.resolve([]);
        }

        const slides = this._parseSlides(editor.document);
        return Promise.resolve(
            slides.map(slide => new SlideItem(slide, editor.document.uri))
        );
    }

    private _parseSlides(document: vscode.TextDocument): SlideInfo[] {
        const text = document.getText();
        const lines = text.split('\n');
        const slides: SlideInfo[] = [];

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
                title: this._extractTitle(lastSlideContent),
                type: this._extractType(lastSlideContent)
            });
        }

        return slides;
    }

    private _extractTitle(content: string): string {
        // Look for # heading
        const headingMatch = content.match(/^#\s+(.+)$/m);
        if (headingMatch) {
            return headingMatch[1].trim();
        }

        // Look for ## heading
        const h2Match = content.match(/^##\s+(.+)$/m);
        if (h2Match) {
            return h2Match[1].trim();
        }

        // Use first non-empty, non-directive, non-block line
        const lines = content.split('\n');
        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed && !trimmed.startsWith('@') && !trimmed.startsWith(':::') && !trimmed.startsWith('```')) {
                return trimmed.substring(0, 40) + (trimmed.length > 40 ? '...' : '');
            }
        }

        return 'Untitled Slide';
    }

    private _extractType(content: string): string {
        const typeMatch = content.match(/^@type\s+(\S+)/m);
        return typeMatch ? typeMatch[1] : 'content';
    }
}

class SlideItem extends vscode.TreeItem {
    constructor(
        public readonly slide: SlideInfo,
        public readonly documentUri: vscode.Uri
    ) {
        super(`${slide.index + 1}. ${slide.title}`, vscode.TreeItemCollapsibleState.None);

        this.description = `@${slide.type}`;
        this.tooltip = `Slide ${slide.index + 1}: ${slide.title}\nType: ${slide.type}\nLines: ${slide.startLine + 1}-${slide.endLine + 1}`;
        this.iconPath = new vscode.ThemeIcon('window');

        // Command to jump to slide
        this.command = {
            command: 'revealLine',
            title: 'Go to Slide',
            arguments: [{ lineNumber: slide.startLine, at: 'center' }]
        };
    }

    contextValue = 'slide';
}
