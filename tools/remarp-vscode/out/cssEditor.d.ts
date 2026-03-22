import * as vscode from 'vscode';
export interface CssOverride {
    target: string;
    properties: Map<string, string>;
}
export interface ParsedCssBlock {
    startLine: number;
    endLine: number;
    overrides: CssOverride[];
}
export declare class RemarpCssEditor {
    /**
     * Parse a :::css block from slide content
     */
    parseCssBlock(slideContent: string, slideIndex: number): ParsedCssBlock | null;
    /**
     * Generate a :::css block string from overrides
     */
    generateCssBlock(overrides: CssOverride[]): string;
    /**
     * Apply a single property change to the .md source
     */
    applyChange(document: vscode.TextDocument, slideIndex: number, target: string, property: string, value: string): Promise<boolean>;
    /**
     * Find existing :::css block or determine where to create one
     */
    findOrCreateCssBlock(document: vscode.TextDocument, slideIndex: number): {
        exists: boolean;
        line: number;
    };
    /**
     * Convert data-remarp-id back to :::css target syntax
     * "s2-header" -> "header"
     * "s2-left" -> "left"
     * "s2-card-1" -> "card:1"
     * "s2-canvas-lambda" -> "canvas:lambda"
     */
    elementIdToTarget(elementId: string): string;
    /**
     * Parse slides from document (same logic as preview.ts _parseSlides)
     */
    private _parseSlides;
}
