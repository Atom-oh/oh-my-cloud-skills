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
exports.RemarpCanvasEditor = void 0;
const vscode = __importStar(require("vscode"));
class RemarpCanvasEditor {
    /**
     * Find :::canvas block range within a slide
     */
    findCanvasBlock(document, slideIndex) {
        const slides = this._parseSlides(document);
        if (slideIndex < 0 || slideIndex >= slides.length) {
            return null;
        }
        const slide = slides[slideIndex];
        const slideLines = [];
        for (let i = slide.startLine; i <= slide.endLine; i++) {
            slideLines.push(document.lineAt(i).text);
        }
        let inCanvasBlock = false;
        let startLine = -1;
        for (let i = 0; i < slideLines.length; i++) {
            const trimmed = slideLines[i].trim();
            if (trimmed === ':::canvas') {
                inCanvasBlock = true;
                startLine = slide.startLine + i;
                continue;
            }
            if (inCanvasBlock && trimmed === ':::') {
                return { startLine, endLine: slide.startLine + i };
            }
        }
        return null;
    }
    /**
     * Update element position in :::canvas DSL
     * Finds the line with the element (by id) and replaces "at X,Y" with new coordinates
     */
    async updateElementPosition(document, slideIndex, elementId, x, y) {
        const canvasBlock = this.findCanvasBlock(document, slideIndex);
        if (!canvasBlock) {
            return false;
        }
        const edit = new vscode.WorkspaceEdit();
        for (let i = canvasBlock.startLine + 1; i < canvasBlock.endLine; i++) {
            const line = document.lineAt(i).text;
            // Check if this line contains the element ID
            // Canvas DSL format: type id "label" at X,Y ...
            // e.g., icon lambda "Lambda" at 100,50 size 48
            if (this._lineContainsElement(line, elementId)) {
                // Replace "at X,Y" or "at X Y" with new coordinates
                const newLine = line.replace(/\bat\s+\d+\s*[,\s]\s*\d+/, `at ${Math.round(x)},${Math.round(y)}`);
                if (newLine !== line) {
                    const range = new vscode.Range(new vscode.Position(i, 0), new vscode.Position(i, line.length));
                    edit.replace(document.uri, range, newLine);
                    return vscode.workspace.applyEdit(edit);
                }
            }
        }
        return false;
    }
    /**
     * Update element size
     * Finds and replaces "size W,H" or "size W H" or "size W"
     */
    async updateElementSize(document, slideIndex, elementId, w, h) {
        const canvasBlock = this.findCanvasBlock(document, slideIndex);
        if (!canvasBlock) {
            return false;
        }
        const edit = new vscode.WorkspaceEdit();
        for (let i = canvasBlock.startLine + 1; i < canvasBlock.endLine; i++) {
            const line = document.lineAt(i).text;
            if (this._lineContainsElement(line, elementId)) {
                let newLine;
                // Try to replace "size W,H" or "size W H" first
                if (/\bsize\s+\d+\s*[,\s]\s*\d+/.test(line)) {
                    newLine = line.replace(/\bsize\s+\d+\s*[,\s]\s*\d+/, `size ${Math.round(w)},${Math.round(h)}`);
                }
                else if (/\bsize\s+\d+/.test(line)) {
                    // Single value size (square or circle)
                    newLine = line.replace(/\bsize\s+\d+/, `size ${Math.round(w)},${Math.round(h)}`);
                }
                else {
                    // No size attribute, append it
                    newLine = line + ` size ${Math.round(w)},${Math.round(h)}`;
                }
                if (newLine !== line) {
                    const range = new vscode.Range(new vscode.Position(i, 0), new vscode.Position(i, line.length));
                    edit.replace(document.uri, range, newLine);
                    return vscode.workspace.applyEdit(edit);
                }
            }
        }
        return false;
    }
    /**
     * Update element step
     * Finds and replaces "step N"
     */
    async updateElementStep(document, slideIndex, elementId, step) {
        const canvasBlock = this.findCanvasBlock(document, slideIndex);
        if (!canvasBlock) {
            return false;
        }
        const edit = new vscode.WorkspaceEdit();
        for (let i = canvasBlock.startLine + 1; i < canvasBlock.endLine; i++) {
            const line = document.lineAt(i).text;
            if (this._lineContainsElement(line, elementId)) {
                let newLine;
                if (/\bstep\s+\d+/.test(line)) {
                    newLine = line.replace(/\bstep\s+\d+/, `step ${step}`);
                }
                else {
                    // No step attribute, append it
                    newLine = line + ` step ${step}`;
                }
                if (newLine !== line) {
                    const range = new vscode.Range(new vscode.Position(i, 0), new vscode.Position(i, line.length));
                    edit.replace(document.uri, range, newLine);
                    return vscode.workspace.applyEdit(edit);
                }
            }
        }
        return false;
    }
    /**
     * Add or update animate-path
     * Format: animate-path: (x,y) -> (x,y) -> ...
     */
    async addAnimatePath(document, slideIndex, elementId, waypoints) {
        if (waypoints.length === 0) {
            return false;
        }
        const canvasBlock = this.findCanvasBlock(document, slideIndex);
        if (!canvasBlock) {
            return false;
        }
        const edit = new vscode.WorkspaceEdit();
        const pathStr = waypoints.map(([x, y]) => `(${Math.round(x)},${Math.round(y)})`).join(' -> ');
        for (let i = canvasBlock.startLine + 1; i < canvasBlock.endLine; i++) {
            const line = document.lineAt(i).text;
            if (this._lineContainsElement(line, elementId)) {
                let newLine;
                // Check if animate-path already exists
                if (/\banimate-path:\s*\([^)]+\)/.test(line)) {
                    newLine = line.replace(/\banimate-path:\s*(?:\([^)]+\)\s*->\s*)*\([^)]+\)/, `animate-path: ${pathStr}`);
                }
                else {
                    // Add animate-path attribute
                    newLine = line + ` animate-path: ${pathStr}`;
                }
                if (newLine !== line) {
                    const range = new vscode.Range(new vscode.Position(i, 0), new vscode.Position(i, line.length));
                    edit.replace(document.uri, range, newLine);
                    return vscode.workspace.applyEdit(edit);
                }
            }
        }
        return false;
    }
    /**
     * Check if a canvas DSL line contains the specified element ID
     * Canvas DSL format examples:
     * - icon lambda "Lambda" at 100,50 size 48
     * - box api "API Gateway" at 75,210 size 100,30 color #FF9900
     * - arrow api -> compute "invoke" step 4
     */
    _lineContainsElement(line, elementId) {
        const trimmed = line.trim();
        // Skip empty lines and closing tags
        if (!trimmed || trimmed === ':::canvas' || trimmed === ':::') {
            return false;
        }
        // Match element declarations: type id "label" ...
        // The id is the second token after the type keyword
        const tokens = trimmed.split(/\s+/);
        if (tokens.length >= 2) {
            // For standard elements: icon lambda "Lambda" ...
            // tokens[0] = type (icon, box, text, etc.)
            // tokens[1] = id
            if (tokens[1] === elementId) {
                return true;
            }
            // For arrow connections: arrow id1 -> id2 "label" ...
            // Check if elementId appears in the connection definition
            if (tokens[0] === 'arrow') {
                // Arrow format: arrow source -> target "label" step N
                const arrowMatch = trimmed.match(/^arrow\s+(\w+)\s*->\s*(\w+)/);
                if (arrowMatch && (arrowMatch[1] === elementId || arrowMatch[2] === elementId)) {
                    return true;
                }
            }
        }
        return false;
    }
    /**
     * Parse slides from document (same logic as preview.ts _parseSlides)
     */
    _parseSlides(document) {
        const text = document.getText();
        const lines = text.split('\n');
        const slides = [];
        let currentSlideStart = 0;
        let frontmatterEnd = 0;
        // Handle frontmatter at the beginning
        if (lines[0]?.trim() === '---') {
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
exports.RemarpCanvasEditor = RemarpCanvasEditor;
//# sourceMappingURL=canvasEditor.js.map