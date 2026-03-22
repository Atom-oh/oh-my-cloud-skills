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
exports.RemarpCssEditor = void 0;
const vscode = __importStar(require("vscode"));
class RemarpCssEditor {
    /**
     * Parse a :::css block from slide content
     */
    parseCssBlock(slideContent, slideIndex) {
        const lines = slideContent.split('\n');
        let inCssBlock = false;
        let startLine = -1;
        let endLine = -1;
        const overrides = [];
        let currentTarget = null;
        let currentProperties = new Map();
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            if (trimmed === ':::css') {
                inCssBlock = true;
                startLine = i;
                continue;
            }
            if (inCssBlock && trimmed === ':::') {
                // Save any pending target
                if (currentTarget) {
                    overrides.push({ target: currentTarget, properties: currentProperties });
                }
                endLine = i;
                break;
            }
            if (inCssBlock) {
                // Check for opening target tag: <target> (exclude closing tags starting with /)
                const openMatch = trimmed.match(/^<([^/>][^>]*)>$/);
                if (openMatch) {
                    // Save previous target if exists
                    if (currentTarget) {
                        overrides.push({ target: currentTarget, properties: currentProperties });
                    }
                    currentTarget = openMatch[1];
                    currentProperties = new Map();
                    continue;
                }
                // Check for closing target tag: </target>
                const closeMatch = trimmed.match(/^<\/([^>]+)>$/);
                if (closeMatch && currentTarget === closeMatch[1]) {
                    overrides.push({ target: currentTarget, properties: currentProperties });
                    currentTarget = null;
                    currentProperties = new Map();
                    continue;
                }
                // Skip orphan closing tags (close tags that don't match currentTarget)
                if (closeMatch) {
                    continue;
                }
                // Parse property: value
                if (currentTarget) {
                    const propMatch = trimmed.match(/^([^:]+):\s*(.+)$/);
                    if (propMatch) {
                        currentProperties.set(propMatch[1].trim(), propMatch[2].trim());
                    }
                }
            }
        }
        if (startLine === -1) {
            return null;
        }
        return { startLine, endLine, overrides };
    }
    /**
     * Generate a :::css block string from overrides
     */
    generateCssBlock(overrides) {
        if (overrides.length === 0) {
            return '';
        }
        const lines = [':::css'];
        for (const override of overrides) {
            lines.push(`<${override.target}>`);
            override.properties.forEach((value, prop) => {
                lines.push(`  ${prop}: ${value}`);
            });
            lines.push(`</${override.target}>`);
        }
        lines.push(':::');
        return lines.join('\n');
    }
    /**
     * Apply a single property change to the .md source
     */
    async applyChange(document, slideIndex, target, property, value) {
        const slides = this._parseSlides(document);
        if (slideIndex < 0 || slideIndex >= slides.length) {
            return false;
        }
        const slide = slides[slideIndex];
        const slideContent = document.getText(new vscode.Range(new vscode.Position(slide.startLine, 0), new vscode.Position(slide.endLine + 1, 0)));
        const cssBlock = this.parseCssBlock(slideContent, slideIndex);
        const edit = new vscode.WorkspaceEdit();
        if (cssBlock) {
            // Find or create the target section within existing :::css block
            const absoluteStart = slide.startLine + cssBlock.startLine;
            const absoluteEnd = slide.startLine + cssBlock.endLine;
            // Check if target already exists
            const existingOverride = cssBlock.overrides.find(o => o.target === target);
            if (existingOverride) {
                existingOverride.properties.set(property, value);
            }
            else {
                cssBlock.overrides.push({
                    target,
                    properties: new Map([[property, value]])
                });
            }
            // Replace the entire :::css block
            const newCssBlock = this.generateCssBlock(cssBlock.overrides);
            const range = new vscode.Range(new vscode.Position(absoluteStart, 0), new vscode.Position(absoluteEnd + 1, 0));
            edit.replace(document.uri, range, newCssBlock + '\n');
        }
        else {
            // Create a new :::css block at the end of the slide (before next ---)
            const newOverride = {
                target,
                properties: new Map([[property, value]])
            };
            const newCssBlock = this.generateCssBlock([newOverride]);
            // Insert before the end of the slide
            const insertPosition = new vscode.Position(slide.endLine + 1, 0);
            edit.insert(document.uri, insertPosition, '\n' + newCssBlock + '\n');
        }
        return vscode.workspace.applyEdit(edit);
    }
    /**
     * Find existing :::css block or determine where to create one
     */
    findOrCreateCssBlock(document, slideIndex) {
        const slides = this._parseSlides(document);
        if (slideIndex < 0 || slideIndex >= slides.length) {
            return { exists: false, line: 0 };
        }
        const slide = slides[slideIndex];
        const slideContent = document.getText(new vscode.Range(new vscode.Position(slide.startLine, 0), new vscode.Position(slide.endLine + 1, 0)));
        const lines = slideContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].trim() === ':::css') {
                return { exists: true, line: slide.startLine + i };
            }
        }
        // Return end of slide position for insertion
        return { exists: false, line: slide.endLine };
    }
    /**
     * Convert data-remarp-id back to :::css target syntax
     * "s2-header" -> "header"
     * "s2-left" -> "left"
     * "s2-card-1" -> "card:1"
     * "s2-canvas-lambda" -> "canvas:lambda"
     */
    elementIdToTarget(elementId) {
        // Strip the "sN-" prefix
        const withoutPrefix = elementId.replace(/^s\d+-/, '');
        // Convert hyphen-number patterns to colon syntax: "card-1" -> "card:1"
        // Also handle canvas element IDs: "canvas-lambda" -> "canvas:lambda"
        const converted = withoutPrefix.replace(/-(\d+)$/, ':$1').replace(/^(canvas|card|li|cell|col|tab|step|option)-(.+)$/, '$1:$2');
        return converted;
    }
    /**
     * Parse slides from document (same logic as preview.ts _parseSlides)
     */
    _parseSlides(document) {
        const text = document.getText();
        const lines = text.split('\n');
        const slides = [];
        let currentSlideStart = 0;
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
                        startLine: currentSlideStart,
                        endLine: i - 1
                    });
                }
                currentSlideStart = i + 1;
            }
        }
        // Add last slide
        const lastSlideContent = lines.slice(currentSlideStart).join('\n');
        if (lastSlideContent.trim()) {
            slides.push({
                startLine: currentSlideStart,
                endLine: lines.length - 1
            });
        }
        return slides;
    }
}
exports.RemarpCssEditor = RemarpCssEditor;
//# sourceMappingURL=cssEditor.js.map