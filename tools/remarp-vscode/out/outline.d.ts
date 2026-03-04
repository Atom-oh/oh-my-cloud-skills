import * as vscode from 'vscode';
interface SlideInfo {
    index: number;
    title: string;
    type: string;
    startLine: number;
    endLine: number;
}
export declare class SlideOutlineProvider implements vscode.TreeDataProvider<SlideItem> {
    private _onDidChangeTreeData;
    readonly onDidChangeTreeData: vscode.Event<SlideItem | undefined | null | void>;
    refresh(): void;
    getTreeItem(element: SlideItem): vscode.TreeItem;
    getChildren(element?: SlideItem): Thenable<SlideItem[]>;
    private _parseSlides;
    private _extractTitle;
    private _extractType;
}
declare class SlideItem extends vscode.TreeItem {
    readonly slide: SlideInfo;
    readonly documentUri: vscode.Uri;
    constructor(slide: SlideInfo, documentUri: vscode.Uri);
    contextValue: string;
}
export {};
