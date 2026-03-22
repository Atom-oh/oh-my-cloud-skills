import * as vscode from 'vscode';
import { RemarpCssEditor } from './cssEditor';
import { RemarpCanvasEditor } from './canvasEditor';
export declare class VisualEditorController {
    private _context;
    private _isEditMode;
    private _cssEditor;
    private _canvasEditor;
    private _pendingChanges;
    constructor(_context: vscode.ExtensionContext);
    /**
     * Buffer a CSS change instead of writing immediately
     */
    private _bufferChange;
    /**
     * Flush all pending CSS changes to the document, then auto-rebuild HTML
     */
    flushChanges(document: vscode.TextDocument): Promise<void>;
    /**
     * Discard all pending CSS changes
     */
    discardChanges(): void;
    get isEditMode(): boolean;
    get cssEditor(): RemarpCssEditor;
    get canvasEditor(): RemarpCanvasEditor;
    toggle(): void;
    /**
     * Handle messages from webview.
     * For Remarp HTML files, find the source .remarp.md and apply edits there.
     */
    handleMessage(message: any, document: vscode.TextDocument): void;
    /**
     * Handle edit messages from a Remarp HTML file by reverse-syncing to source .remarp.md
     */
    private _handleHtmlMessage;
    /**
     * Route to cssEditor for HTML elements - handle element move
     */
    private _handleElementMoved;
    /**
     * Route to cssEditor for HTML elements - handle element resize
     */
    private _handleElementResized;
    /**
     * Route to cssEditor for property changes from property panel
     */
    private _handlePropertyChanged;
    /**
     * Route to canvasEditor for canvas element moves
     */
    private _handleCanvasElementMoved;
    /**
     * Route to canvasEditor for canvas element resizes
     */
    private _handleCanvasElementResized;
    /**
     * Route to canvasEditor for step changes
     */
    private _handleCanvasStepChanged;
    /**
     * Route to canvasEditor for waypoint/animate-path changes
     */
    private _handleWaypointChanged;
    /**
     * Extract slide index from element ID
     * Format: "s{index}-{target}" e.g., "s2-header" -> 2
     */
    private _extractSlideIndex;
}
