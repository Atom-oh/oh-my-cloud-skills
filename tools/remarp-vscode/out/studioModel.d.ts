/** Host-owned edit planning. No VS Code or browser dependencies. */
export interface Span {
    start: number;
    end: number;
}
export interface Field extends Span {
    value: string | number;
    line?: Span;
}
export interface Geometry {
    x: number;
    y: number;
    width: number;
    height: number;
    canvasWidth: number;
    canvasHeight: number;
    centered: boolean;
}
export interface StudioNode {
    id: string;
    kind: string;
    label: string;
    renderId?: string | null;
    cssTarget?: string;
    text?: Field;
    body?: Field;
    geometry?: Geometry;
    position?: Span;
    size?: Span;
    step?: Field;
    lineEnd?: Span;
}
export interface StudioSlide {
    id: string;
    file: string;
    title: string;
    type: string;
    block: string;
    source: string;
    range: Span;
    eol: string;
    nodes: StudioNode[];
    directives: Record<string, Field | null>;
    cssEditable: boolean;
    css: null | {
        insert: Span;
        targets: Record<string, {
            insert: Span | null;
            properties: Record<string, Field>;
        }>;
    };
}
export interface StudioManifest {
    version: number;
    html: string;
    files: Record<string, string>;
    slides: StudioSlide[];
}
export interface Patch extends Span {
    text: string;
}
export interface Intent {
    slide: string;
    node?: string;
    operation: string;
    value?: unknown;
    property?: string;
}
export declare function findSlide(manifest: StudioManifest, id: unknown): StudioSlide;
export declare function planEdit(manifest: StudioManifest, intent: Intent): {
    file: string;
    patches: Patch[];
};
export declare function applyPatches(source: string, patches: Patch[]): string;
