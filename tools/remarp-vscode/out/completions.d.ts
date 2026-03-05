import * as vscode from 'vscode';
export declare class RemarpCompletionProvider implements vscode.CompletionItemProvider {
    private readonly directives;
    private readonly blockTypes;
    private readonly animations;
    private readonly frontmatterDirectives;
    private readonly canvasKeywords;
    provideCompletionItems(document: vscode.TextDocument, position: vscode.Position, _token: vscode.CancellationToken, _context: vscode.CompletionContext): vscode.ProviderResult<vscode.CompletionItem[] | vscode.CompletionList>;
    private _isInFrontmatter;
    private _getFrontmatterCompletions;
    private _isInCanvasBlock;
    private _getDirectiveCompletions;
    private _getDirectiveValueCompletions;
    private _getAnimationCompletions;
    private _getBlockCompletions;
    private _getClickAttributeCompletions;
    private _getCanvasCompletions;
}
