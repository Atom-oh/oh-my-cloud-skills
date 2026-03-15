import * as vscode from 'vscode';
import { RemarpCssEditor } from './cssEditor';
import { RemarpCanvasEditor } from './canvasEditor';
import { isRemarpHtml, findRemarpSource } from './extension';

export class VisualEditorController {
    private _isEditMode: boolean = false;
    private _cssEditor: RemarpCssEditor;
    private _canvasEditor: RemarpCanvasEditor;
    private _pendingChanges: Map<number, Map<string, Map<string, string>>> = new Map();

    constructor(private _context: vscode.ExtensionContext) {
        this._cssEditor = new RemarpCssEditor();
        this._canvasEditor = new RemarpCanvasEditor();
    }

    /**
     * Buffer a CSS change instead of writing immediately
     */
    private _bufferChange(slideIndex: number, target: string, property: string, value: string): void {
        if (!this._pendingChanges.has(slideIndex)) {
            this._pendingChanges.set(slideIndex, new Map());
        }
        const slideChanges = this._pendingChanges.get(slideIndex)!;
        if (!slideChanges.has(target)) {
            slideChanges.set(target, new Map());
        }
        slideChanges.get(target)!.set(property, value);
    }

    /**
     * Flush all pending CSS changes to the document, then auto-rebuild HTML
     */
    async flushChanges(document: vscode.TextDocument): Promise<void> {
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
    discardChanges(): void {
        this._pendingChanges.clear();
    }

    get isEditMode(): boolean {
        return this._isEditMode;
    }

    get cssEditor(): RemarpCssEditor {
        return this._cssEditor;
    }

    get canvasEditor(): RemarpCanvasEditor {
        return this._canvasEditor;
    }

    toggle(): void {
        this._isEditMode = !this._isEditMode;
        vscode.commands.executeCommand('setContext', 'remarp.editMode', this._isEditMode);

        // Import dynamically to avoid circular dependency
        const { RemarpPreviewPanel } = require('./preview');
        RemarpPreviewPanel.setEditMode(this._isEditMode);

        // Show status message
        if (this._isEditMode) {
            vscode.window.showInformationMessage('Remarp: Visual Edit Mode enabled');
        } else {
            vscode.window.showInformationMessage('Remarp: Visual Edit Mode disabled');
        }
    }

    /**
     * Handle messages from webview.
     * For Remarp HTML files, find the source .remarp.md and apply edits there.
     */
    handleMessage(message: any, document: vscode.TextDocument): void {
        if (isRemarpHtml(document)) {
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
    private async _handleHtmlMessage(message: any, htmlDocument: vscode.TextDocument): Promise<void> {
        const sourcePath = findRemarpSource(htmlDocument);
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
    private _handleElementMoved(doc: vscode.TextDocument, msg: any): void {
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
    private _handleElementResized(doc: vscode.TextDocument, msg: any): void {
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
    private _handlePropertyChanged(doc: vscode.TextDocument, msg: any): void {
        const target = this._cssEditor.elementIdToTarget(msg.elementId);
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._bufferChange(slideIndex, target, msg.property, msg.value);
    }

    /**
     * Route to canvasEditor for canvas element moves
     */
    private _handleCanvasElementMoved(doc: vscode.TextDocument, msg: any): void {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.updateElementPosition(doc, slideIndex, msg.canvasElementId, msg.x, msg.y);
    }

    /**
     * Route to canvasEditor for canvas element resizes
     */
    private _handleCanvasElementResized(doc: vscode.TextDocument, msg: any): void {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.updateElementSize(doc, slideIndex, msg.canvasElementId, msg.width, msg.height);
    }

    /**
     * Route to canvasEditor for step changes
     */
    private _handleCanvasStepChanged(doc: vscode.TextDocument, msg: any): void {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.updateElementStep(doc, slideIndex, msg.canvasElementId, msg.step);
    }

    /**
     * Route to canvasEditor for waypoint/animate-path changes
     */
    private _handleWaypointChanged(doc: vscode.TextDocument, msg: any): void {
        const slideIndex = this._extractSlideIndex(msg.elementId);
        this._canvasEditor.addAnimatePath(doc, slideIndex, msg.canvasElementId, msg.waypoints);
    }

    /**
     * Extract slide index from element ID
     * Format: "s{index}-{target}" e.g., "s2-header" -> 2
     */
    private _extractSlideIndex(elementId: string): number {
        const match = elementId.match(/^s(\d+)/);
        return match ? parseInt(match[1], 10) : 0;
    }
}
