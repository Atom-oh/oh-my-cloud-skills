import * as vscode from 'vscode';
export declare class RemarpCanvasEditor {
    /**
     * Find :::canvas block range within a slide
     */
    findCanvasBlock(document: vscode.TextDocument, slideIndex: number): {
        startLine: number;
        endLine: number;
    } | null;
    /**
     * Update element position in :::canvas DSL
     * Finds the line with the element (by id) and replaces "at X,Y" with new coordinates
     */
    updateElementPosition(document: vscode.TextDocument, slideIndex: number, elementId: string, x: number, y: number): Promise<boolean>;
    /**
     * Update element size
     * Finds and replaces "size W,H" or "size W H" or "size W"
     */
    updateElementSize(document: vscode.TextDocument, slideIndex: number, elementId: string, w: number, h: number): Promise<boolean>;
    /**
     * Update element step
     * Finds and replaces "step N"
     */
    updateElementStep(document: vscode.TextDocument, slideIndex: number, elementId: string, step: number): Promise<boolean>;
    /**
     * Add or update animate-path
     * Format: animate-path: (x,y) -> (x,y) -> ...
     */
    addAnimatePath(document: vscode.TextDocument, slideIndex: number, elementId: string, waypoints: [number, number][]): Promise<boolean>;
    /**
     * Check if a canvas DSL line contains the specified element ID
     * Canvas DSL format examples:
     * - icon lambda "Lambda" at 100,50 size 48
     * - box api "API Gateway" at 75,210 size 100,30 color #FF9900
     * - arrow api -> compute "invoke" step 4
     */
    private _lineContainsElement;
    /**
     * Parse slides from document (same logic as preview.ts _parseSlides)
     */
    private _parseSlides;
}
