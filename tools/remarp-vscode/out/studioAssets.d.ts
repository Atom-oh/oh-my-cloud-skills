export declare function assertStudioDocumentSize(bytes: number): void;
/** Bound expanded output before joining replacements (imports can amplify tiny inputs). */
export declare function boundedReplace(input: string, pattern: RegExp, replace: (...match: any[]) => string): string;
export declare const decodeAttribute: (s: string) => string;
export declare const htmlTokens: RegExp;
export declare function mapAttributes(tag: string, map: (name: string, value: string) => string | undefined): string;
export interface StudioAssets {
    html: string;
    images: Record<string, string>;
    warnings: string[];
}
/** Build a finite self-contained renderer from isolated output and staged assets only. */
export declare function bundleStudioAssets(html: string, output: string, snapshot: string): StudioAssets;
