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
exports.SlideOutlineProvider = void 0;
const vscode = __importStar(require("vscode"));
class SlideOutlineProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (element) {
            return Promise.resolve([]);
        }
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'remarp') {
            return Promise.resolve([]);
        }
        const slides = this._parseSlides(editor.document);
        return Promise.resolve(slides.map(slide => new SlideItem(slide, editor.document.uri)));
    }
    _parseSlides(document) {
        const text = document.getText();
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
    _extractTitle(content) {
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
    _extractType(content) {
        const typeMatch = content.match(/^@type\s+(\S+)/m);
        return typeMatch ? typeMatch[1] : 'content';
    }
}
exports.SlideOutlineProvider = SlideOutlineProvider;
class SlideItem extends vscode.TreeItem {
    constructor(slide, documentUri) {
        super(`${slide.index + 1}. ${slide.title}`, vscode.TreeItemCollapsibleState.None);
        this.slide = slide;
        this.documentUri = documentUri;
        this.contextValue = 'slide';
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
}
//# sourceMappingURL=outline.js.map