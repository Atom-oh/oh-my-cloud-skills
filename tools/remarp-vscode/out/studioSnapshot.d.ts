export interface SnapshotFile {
    text: string;
    version?: number;
}
export type Snapshot = Map<string, SnapshotFile>;
export declare const digest: (s: string) => string;
export declare function inside(root: string, file: string): boolean;
export declare function sourcePath(root: string, relative: string): string;
/** Stage only source and explicitly referenced local assets, never an entire repo. */
export declare function stageSnapshot(root: string, directory: string, sources: Snapshot): void;
