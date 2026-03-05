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
exports.RemarpCompletionProvider = void 0;
const vscode = __importStar(require("vscode"));
class RemarpCompletionProvider {
    constructor() {
        this.directives = [
            { name: '@type', description: 'Slide type', values: ['content', 'compare', 'canvas', 'quiz', 'tabs', 'timeline', 'checklist', 'slider', 'code', 'title', 'section', 'image', 'video', 'embed', 'quote', 'list', 'table', 'columns', 'grid', 'split', 'diagram'] },
            { name: '@layout', description: 'Slide layout', values: ['default', 'two-column', 'three-column', 'grid-2x2', 'grid-3x3', 'split-40-60', 'split-60-40', 'split-30-70', 'split-70-30', 'centered', 'fullscreen'] },
            { name: '@transition', description: 'Slide transition', values: ['fade', 'slide', 'slide-left', 'slide-right', 'slide-up', 'slide-down', 'zoom', 'zoom-in', 'zoom-out', 'flip', 'flip-x', 'flip-y', 'rotate', 'cube', 'none'] },
            { name: '@background', description: 'Slide background (color, image URL, or gradient)' },
            { name: '@class', description: 'Custom CSS class for the slide' },
            { name: '@timing', description: 'Auto-advance timing (e.g., 5000ms, 10s)' },
            { name: '@canvas-id', description: 'Canvas identifier for animations' },
            { name: '@animation', description: 'Default animation for slide elements', values: ['fade-in', 'fade-up', 'fade-down', 'fade-left', 'fade-right', 'zoom-in', 'zoom-out', 'slide-up', 'slide-down', 'slide-left', 'slide-right', 'bounce', 'pulse', 'shake', 'flip', 'rotate', 'scale-up', 'scale-down', 'typewriter', 'draw', 'morph', 'blur-in', 'blur-out', 'none'] },
            { name: '@fragment', description: 'Enable fragment animations (true/false)' },
            { name: '@auto-animate', description: 'Enable auto-animation between slides (true/false)' },
            { name: '@notes', description: 'Speaker notes for this slide' },
            { name: '@data-id', description: 'Data ID for auto-animate matching' },
            { name: '@visibility', description: 'Slide visibility (visible/hidden)' }
        ];
        this.blockTypes = [
            { name: 'notes', description: 'Speaker notes (hidden during presentation)' },
            { name: 'canvas', description: 'Canvas DSL for programmatic graphics' },
            { name: 'click', description: 'Click-to-reveal content block' },
            { name: 'left', description: 'Left column in two-column layout' },
            { name: 'right', description: 'Right column in two-column layout' },
            { name: 'col', description: 'Column in multi-column layout' },
            { name: 'cell', description: 'Cell in grid layout' },
            { name: 'option', description: 'Quiz option' },
            { name: 'tab', description: 'Tab content' },
            { name: 'item', description: 'Timeline or checklist item' },
            { name: 'step', description: 'Timeline step with year' },
            { name: 'fragment', description: 'Fragment for sequential reveal' },
            { name: 'speaker', description: 'Speaker notes (alternative syntax)' }
        ];
        this.animations = [
            'fade-in', 'fade-up', 'fade-down', 'fade-left', 'fade-right',
            'zoom-in', 'zoom-out',
            'slide-up', 'slide-down', 'slide-left', 'slide-right',
            'bounce', 'pulse', 'shake',
            'flip', 'rotate',
            'scale-up', 'scale-down',
            'typewriter', 'draw', 'morph',
            'blur-in', 'blur-out',
            'none'
        ];
        this.frontmatterDirectives = [
            { name: 'footer', description: 'Global footer text (Marp-compatible)', snippet: 'footer: "${1:© 2025 Company}"' },
            { name: 'paginate', description: 'Show slide numbers (Marp-compatible)', snippet: 'paginate: ${1|true,false|}' },
            { name: 'backgroundColor', description: 'Global slide background color', snippet: 'backgroundColor: "${1:#1a1d2e}"' },
            { name: 'backgroundImage', description: 'Global slide background image', snippet: 'backgroundImage: "url(${1:path/to/image.png})"' },
            { name: 'header', description: 'Global header text', snippet: 'header: "${1:Header Text}"' },
            { name: 'color', description: 'Global text color', snippet: 'color: "${1:#ffffff}"' },
        ];
        this.canvasKeywords = [
            'box', 'circle', 'ellipse', 'rect', 'diamond', 'hexagon', 'triangle',
            'line', 'arrow', 'polyline', 'polygon', 'path',
            'text', 'icon', 'image', 'group', 'container',
            'at', 'to', 'from', 'x', 'y', 'size', 'width', 'height',
            'color', 'fill', 'stroke', 'opacity',
            'animate', 'delay', 'duration', 'easing'
        ];
    }
    provideCompletionItems(document, position, _token, _context) {
        const linePrefix = document.lineAt(position).text.substring(0, position.character);
        // Frontmatter directive completions (between --- markers)
        if (this._isInFrontmatter(document, position)) {
            return this._getFrontmatterCompletions(linePrefix);
        }
        // Check if we're in a canvas block
        if (this._isInCanvasBlock(document, position)) {
            return this._getCanvasCompletions(linePrefix);
        }
        // @ directive completions
        if (linePrefix.endsWith('@') || linePrefix.match(/^@\w*$/)) {
            return this._getDirectiveCompletions();
        }
        // Directive value completions
        for (const directive of this.directives) {
            if (directive.values) {
                const pattern = new RegExp(`^${directive.name}\\s+\\S*$`);
                if (pattern.test(linePrefix)) {
                    return this._getDirectiveValueCompletions(directive.values, directive.name);
                }
            }
        }
        // animation= completions
        if (linePrefix.match(/animation=\S*$/)) {
            return this._getAnimationCompletions();
        }
        // ::: block completions
        if (linePrefix.match(/^:::\s*\w*$/) || linePrefix.endsWith(':::')) {
            return this._getBlockCompletions();
        }
        // {.click} attribute completions
        if (linePrefix.match(/\{\.\w*$/)) {
            return this._getClickAttributeCompletions();
        }
        return undefined;
    }
    _isInFrontmatter(document, position) {
        // Frontmatter must start at line 0 with ---
        if (document.lineAt(0).text.trim() !== '---') {
            return false;
        }
        // Find closing --- (skip line 0)
        for (let i = 1; i <= position.line; i++) {
            if (document.lineAt(i).text.trim() === '---') {
                // If closing --- is at or before cursor line, we're past frontmatter
                return i > position.line;
            }
        }
        // No closing --- found yet — still in frontmatter
        return true;
    }
    _getFrontmatterCompletions(linePrefix) {
        return this.frontmatterDirectives
            .filter(d => !linePrefix.includes(':')) // Only suggest keys, not after colon
            .map(directive => {
            const item = new vscode.CompletionItem(directive.name, vscode.CompletionItemKind.Property);
            item.detail = directive.description;
            if (directive.snippet) {
                item.insertText = new vscode.SnippetString(directive.snippet);
            }
            item.documentation = new vscode.MarkdownString(`Marp-compatible frontmatter directive.\n\nAlso available as nested Remarp syntax.`);
            return item;
        });
    }
    _isInCanvasBlock(document, position) {
        // Look backwards for :::canvas
        for (let i = position.line - 1; i >= 0; i--) {
            const line = document.lineAt(i).text.trim();
            if (line === ':::canvas') {
                return true;
            }
            if (line === ':::' || line.startsWith('---')) {
                return false;
            }
        }
        return false;
    }
    _getDirectiveCompletions() {
        return this.directives.map(directive => {
            const item = new vscode.CompletionItem(directive.name, vscode.CompletionItemKind.Keyword);
            item.detail = directive.description;
            item.insertText = directive.name.substring(1); // Remove @ since user already typed it
            if (directive.values) {
                item.documentation = new vscode.MarkdownString(`Values: ${directive.values.join(', ')}`);
            }
            return item;
        });
    }
    _getDirectiveValueCompletions(values, directiveName) {
        return values.map(value => {
            const item = new vscode.CompletionItem(value, vscode.CompletionItemKind.EnumMember);
            item.detail = `${directiveName} value`;
            return item;
        });
    }
    _getAnimationCompletions() {
        return this.animations.map(anim => {
            const item = new vscode.CompletionItem(anim, vscode.CompletionItemKind.EnumMember);
            item.detail = 'Animation type';
            return item;
        });
    }
    _getBlockCompletions() {
        return this.blockTypes.map(block => {
            const item = new vscode.CompletionItem(block.name, vscode.CompletionItemKind.Snippet);
            item.detail = block.description;
            item.insertText = new vscode.SnippetString(`${block.name}\n$0\n:::`);
            item.documentation = new vscode.MarkdownString(`Creates a \`:::${block.name}\` block`);
            return item;
        });
    }
    _getClickAttributeCompletions() {
        const items = [];
        // Basic .click
        const clickItem = new vscode.CompletionItem('.click', vscode.CompletionItemKind.Property);
        clickItem.detail = 'Click-to-reveal element';
        clickItem.insertText = new vscode.SnippetString('click}');
        items.push(clickItem);
        // .click with animation
        const clickAnimItem = new vscode.CompletionItem('.click animation=', vscode.CompletionItemKind.Property);
        clickAnimItem.detail = 'Click-to-reveal with animation';
        clickAnimItem.insertText = new vscode.SnippetString('click animation=${1|fade-in,fade-up,fade-down,zoom-in,slide-up|}');
        items.push(clickAnimItem);
        // .click with order
        const clickOrderItem = new vscode.CompletionItem('.click order=', vscode.CompletionItemKind.Property);
        clickOrderItem.detail = 'Click-to-reveal with order';
        clickOrderItem.insertText = new vscode.SnippetString('click order=${1:1}}');
        items.push(clickOrderItem);
        // Full .click
        const clickFullItem = new vscode.CompletionItem('.click animation= order=', vscode.CompletionItemKind.Property);
        clickFullItem.detail = 'Click-to-reveal with animation and order';
        clickFullItem.insertText = new vscode.SnippetString('click animation=${1|fade-in,fade-up,fade-down,zoom-in|} order=${2:1}}');
        items.push(clickFullItem);
        return items;
    }
    _getCanvasCompletions(linePrefix) {
        const items = [];
        // Shape completions
        const shapes = ['box', 'circle', 'ellipse', 'rect', 'diamond', 'hexagon', 'triangle', 'line', 'arrow', 'text', 'icon', 'image', 'group'];
        for (const shape of shapes) {
            const item = new vscode.CompletionItem(shape, vscode.CompletionItemKind.Class);
            item.detail = `Canvas ${shape} element`;
            // Add snippet for common shapes
            if (shape === 'box') {
                item.insertText = new vscode.SnippetString('box "${1:label}" at ${2:x} ${3:y} size ${4:width} ${5:height}');
            }
            else if (shape === 'circle') {
                item.insertText = new vscode.SnippetString('circle at ${1:cx} ${2:cy} r ${3:radius}');
            }
            else if (shape === 'arrow') {
                item.insertText = new vscode.SnippetString('arrow from ${1:x1} ${2:y1} to ${3:x2} ${4:y2}');
            }
            else if (shape === 'text') {
                item.insertText = new vscode.SnippetString('text "${1:content}" at ${2:x} ${3:y}');
            }
            else if (shape === 'icon') {
                item.insertText = new vscode.SnippetString('icon "${1:icon-name}" at ${2:x} ${3:y}');
            }
            items.push(item);
        }
        // Position/dimension keywords
        const positionKeywords = ['at', 'to', 'from', 'x', 'y', 'size', 'width', 'height', 'r', 'radius'];
        for (const kw of positionKeywords) {
            const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword);
            item.detail = `Position/dimension keyword`;
            items.push(item);
        }
        // Style keywords
        const styleKeywords = ['color', 'fill', 'stroke', 'stroke-width', 'opacity', 'font-size'];
        for (const kw of styleKeywords) {
            const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Property);
            item.detail = `Style property`;
            item.insertText = new vscode.SnippetString(`${kw}=${kw === 'color' || kw === 'fill' || kw === 'stroke' ? '"${1:#ffffff}"' : '${1:value}'}`);
            items.push(item);
        }
        // Animation keywords
        const animKeywords = ['animate', 'delay', 'duration', 'easing'];
        for (const kw of animKeywords) {
            const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Event);
            item.detail = `Animation property`;
            if (kw === 'animate') {
                item.insertText = new vscode.SnippetString('animate="${1|fade-in,draw,morph,pulse|}"');
            }
            else if (kw === 'delay' || kw === 'duration') {
                item.insertText = new vscode.SnippetString(`${kw}=${kw === 'delay' ? '${1:0}' : '${1:1000}'}ms`);
            }
            items.push(item);
        }
        return items;
    }
}
exports.RemarpCompletionProvider = RemarpCompletionProvider;
//# sourceMappingURL=completions.js.map