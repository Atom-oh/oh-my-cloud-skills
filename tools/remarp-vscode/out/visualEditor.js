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
exports.VisualEditorController = void 0;
const vscode = __importStar(require("vscode"));
const cssEditor_1 = require("./cssEditor");
const canvasEditor_1 = require("./canvasEditor");
const extension_1 = require("./extension");
class VisualEditorController {
    constructor(_context) {
        this._context = _context;
        this._isEditMode = false;
        this._pendingChanges = new Map();
        this._cssEditor = new cssEditor_1.RemarpCssEditor();
        this._canvasEditor = new canvasEditor_1.RemarpCanvasEditor();
    }
    /**
     * Buffer a CSS change instead of writing immediately
     */
    _bufferChange(slideIndex, target, property, value) {
        if (!this._pendingChanges.has(slideIndex)) {
            this._pendingChanges.set(slideIndex, new Map());
        }
        const slideChanges = this._pendingChanges.get(slideIndex);
        if (!slideChanges.has(target)) {
            slideChanges.set(target, new Map());
        }
        slideChanges.get(target).set(property, value);
    }
    /**
     * Flush all pending CSS changes to the document, then auto-rebuild HTML
     */
    async flushChanges(document) {
        for (const [slideIndex, targets] of this._pendingChanges) {
            for (const [target, properties] of targets) {
                for (const [property, value] of properties) {
                    await this._cssEditor.applyChange(document, slideIndex, target, property, value);
                }
            }
        }
        this._pendingChanges.clear();
        // Auto-rebuild HTML after saving
        vscode.commands.executeCommand('remarp.build');
    }
    /**
     * Discard all pending CSS changes
     */
    discardChanges() {
        this._pendingChanges.clear();
    }
    get isEditMode() {
        return this._isEditMode;
    }
    get cssEditor() {
        return this._cssEditor;
    }
    get canvasEditor() {
        return this._canvasEditor;
    }
    toggle() {
        this._isEditMode = !this._isEditMode;
        vscode.commands.executeCommand('setContext', 'remarp.editMode', this._isEditMode);
        // Import dynamically to avoid circular dependency
        const { RemarpPreviewPanel } = require('./preview');
        RemarpPreviewPanel.setEditMode(this._isEditMode);
        // Show status message
        if (this._isEditMode) {
            vscode.window.showInformationMessage('Remarp: Visual Edit Mode enabled');
        }
        else {
            vscode.window.showInformationMessage('Remarp: Visual Edit Mode disabled');
        }
    }
    /**
     * Handle messages from webview.
     * For Remarp HTML files, find the source .remarp.md and apply edits there.
     */
    handleMessage(message, document) {
        if ((0, extension_1.isRemarpHtml)(document)) {
            this._handleHtmlMessage(message, document);
            return;
        }
        switch (message.command) {
            case 'elementMoved':
                this._handleElementMoved(document, message);
                break;
            case 'elementResized':
                this._handleElementResized(document, message);
                break;
            case 'propertyChanged':
                this._handlePropertyChanged(document, message);
                break;
            case 'canvasElementMoved':
                this._handleCanvasElementMoved(document, message);
                break;
            case 'canvasElementResized':
                this._handleCanvasElementResized(document, message);
                break;
            case 'canvasStepChanged':
                this._handleCanvasStepChanged(document, message);
                break;
            case 'waypointChanged':
                this._handleWaypointChanged(document, message);
                break;
            case 'editDone':
                this.flushChanges(document);
                break;
        }
    }
    /**
     * Handle edit messages from a Remarp HTML file by reverse-syncing to source .remarp.md
     */
    async _handleHtmlMessage(message, htmlDocument) {
        const sourcePath = (0, extension_1.findRemarpSource)(htmlDocument);
        if (!sourcePath) {
            vscode.window.showWarningMessage('Could not find source .remarp.md for this HTML file');
            return;
        }
        const sourceDoc = await vscode.workspace.openTextDocument(sourcePath);
        // Route CSS-related messages to the source document
        switch (message.command) {
            case 'elementMoved': {
                const target = this._cssEditor.elementIdToTarget(message.elementId);
                const slideIndex = this._extractSlideIndex(message.elementId);
                const mdx = message.delta?.x ?? message.deltaX ?? 0;
                const mdy = message.delta?.y ?? message.deltaY ?? 0;
                const transformValue = `translate(${mdx}px, ${mdy}px)`;
                this._bufferChange(slideIndex, target, 'transform', transformValue);
                break;
            }
            case 'elementResized': {
                const target = this._cssEditor.elementIdToTarget(message.elementId);
                const slideIndex = this._extractSlideIndex(message.elementId);
                const mw = message.size?.width ?? message.width;
                const mh = message.size?.height ?? message.height;
                if (mw) {
                    this._bufferChange(slideIndex, target, 'width', `${mw}px`);
                }
                if (mh) {
                    this._bufferChange(slideIndex, target, 'height', `${mh}px`);
                }
                break;
            }
            case 'propertyChanged': {
                const target = this._cssEditor.elementIdToTarget(message.elementId);
                const slideIndex = this._extractSlideIndex(message.elementId);
                this._bufferChange(slideIndex, target, message.property, message.value);
                break;
            }
            case 'editDone':
                this.flushChanges(sourceDoc);
                break;
            case 'canvasElementMoved':
            case 'canvasElementResized':
            case 'canvasStepChanged':
            case 'waypointChanged':
                // Canvas edits route to source as well
                this.handleMessage(message, sourceDoc);
                break;
        }
    }
    /**
     * Route to cssEditor for HTML elements - handle element move
     */
    _handleElementMoved(doc, msg) {
        const target = this._cssEditor.elementIdToTarget(msg.elementId);
        const slideIndex = this._extractSlideIndex(msg.elementId);
        // Buffer transform change (written on Done click)
        // Support both nested {delta: {x, y}} and flat {deltaX, deltaY} shapes
        const dx = msg.delta?.x ?? msg.deltaX ?? 0;
        const dy = msg.delta?.y ?? msg.deltaY ?? 0;
        const transformValue = `translate(${dx}px, ${dy}px)`;
        this._bufferChange(slideIndex, target, 'transform', transformValue);
    }
    /**
     * Route to cssEditor for HTML elements - handle element resize
     */
    _handleElementResized(doc, msg) {
        const target = this._cssEditor.elementIdToTarget(msg.elementId);
        const slideIndex = this._extractSlideIndex(msg.elementId);
        // Support both nested {size: {width, height}} and flat {width, height} shapes
        const width = msg.size?.width ?? msg.width;
        const height = msg.size?.height ?? msg.height;
        if (width) {
            this._bufferChange(slideIndex, target, 'width', `${width}px`);
        }
        if (height) {
            this._bufferChange(slideIndex, target, 'height', `${height}px`);
        }
    }
    /**
     * Route to cssEditor for property changes from property panel
     */
    _handlePropertyChanged(doc, msg) {
        const target = this._cssEditor.elementIdToTarget(msg.elementId);
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._bufferChange(slideIndex, target, msg.property, msg.value);
    }
    /**
     * Route to canvasEditor for canvas element moves
     */
    _handleCanvasElementMoved(doc, msg) {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.updateElementPosition(doc, slideIndex, msg.canvasElementId, msg.x, msg.y);
    }
    /**
     * Route to canvasEditor for canvas element resizes
     */
    _handleCanvasElementResized(doc, msg) {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.updateElementSize(doc, slideIndex, msg.canvasElementId, msg.width, msg.height);
    }
    /**
     * Route to canvasEditor for step changes
     */
    _handleCanvasStepChanged(doc, msg) {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.updateElementStep(doc, slideIndex, msg.canvasElementId, msg.step);
    }
    /**
     * Route to canvasEditor for waypoint/animate-path changes
     */
    _handleWaypointChanged(doc, msg) {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.addAnimatePath(doc, slideIndex, msg.canvasElementId, msg.waypoints);
    }
    /**
     * Extract slide index from element ID
     * Format: "s{index}-{target}" e.g., "s2-header" -> 2
     */
    _extractSlideIndex(elementId) {
        const match = elementId.match(/^s(\d+)/);
        return match ? parseInt(match[1], 10) : 0;
    }
}
exports.VisualEditorController = VisualEditorController;
//# sourceMappingURL=visualEditor.js.map