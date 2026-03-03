import * as vscode from 'vscode';
import { RemarpPreviewPanel } from './preview';
import { SlideOutlineProvider } from './outline';
import { RemarpCompletionProvider } from './completions';

/**
 * Check if a document is a remarp file by looking for `remarp: true` in frontmatter
 * or checking if it has .remarp.md extension
 */
export function isRemarpDocument(document: vscode.TextDocument): boolean {
    // Check file extension first
    if (document.fileName.endsWith('.remarp.md')) {
        return true;
    }

    // Check for remarp: true in frontmatter
    const text = document.getText();
    const frontmatterMatch = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (frontmatterMatch) {
        const frontmatter = frontmatterMatch[1];
        // Check for remarp: true (with optional quotes)
        if (/^remarp:\s*(?:true|"true"|'true')\s*$/m.test(frontmatter)) {
            return true;
        }
    }

    return false;
}

/**
 * Set the language mode to remarp for markdown files with remarp: true
 */
async function setRemarpLanguageIfNeeded(document: vscode.TextDocument): Promise<void> {
    if (document.languageId === 'markdown' && isRemarpDocument(document)) {
        await vscode.languages.setTextDocumentLanguage(document, 'remarp');
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('Remarp extension is now active');

    // Check all open markdown files for remarp: true
    vscode.workspace.textDocuments.forEach(doc => {
        setRemarpLanguageIfNeeded(doc);
    });

    // Watch for newly opened documents
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument((document) => {
            setRemarpLanguageIfNeeded(document);
        })
    );

    // Watch for document saves (in case remarp: true is added)
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((document) => {
            setRemarpLanguageIfNeeded(document);
        })
    );

    // Register the preview panel command
    context.subscriptions.push(
        vscode.commands.registerCommand('remarp.preview', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor && (editor.document.languageId === 'remarp' || isRemarpDocument(editor.document))) {
                RemarpPreviewPanel.createOrShow(context.extensionUri, editor.document);
            } else {
                vscode.window.showWarningMessage('Open a .remarp.md file or a markdown file with remarp: true to preview');
            }
        })
    );

    // Register the outline provider
    const outlineProvider = new SlideOutlineProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('remarpOutline', outlineProvider)
    );

    // Register completion provider
    const completionProvider = new RemarpCompletionProvider();
    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider(
            { language: 'remarp' },
            completionProvider,
            '@', ':', '='
        )
    );

    // Register slide navigation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('remarp.nextSlide', () => {
            navigateSlide('next');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('remarp.prevSlide', () => {
            navigateSlide('prev');
        })
    );

    // Watch for document changes to update outline and preview
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
            if (event.document.languageId === 'remarp') {
                outlineProvider.refresh();
                RemarpPreviewPanel.update(event.document);
            }
        })
    );

    // Watch for active editor changes
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor && editor.document.languageId === 'remarp') {
                outlineProvider.refresh();
            }
        })
    );

    // Watch for cursor position changes to sync with outline
    context.subscriptions.push(
        vscode.window.onDidChangeTextEditorSelection((event) => {
            if (event.textEditor.document.languageId === 'remarp') {
                RemarpPreviewPanel.syncCursor(event.textEditor);
            }
        })
    );
}

function navigateSlide(direction: 'next' | 'prev'): void {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'remarp') {
        return;
    }

    const document = editor.document;
    const text = document.getText();
    const currentPosition = editor.selection.active;
    const currentOffset = document.offsetAt(currentPosition);

    // Find all slide separators (---)
    const separatorRegex = /^---$/gm;
    const separators: number[] = [];
    let match;

    while ((match = separatorRegex.exec(text)) !== null) {
        separators.push(match.index);
    }

    if (separators.length === 0) {
        return;
    }

    let targetOffset: number | null = null;

    if (direction === 'next') {
        // Find the next separator after current position
        for (const sep of separators) {
            if (sep > currentOffset) {
                targetOffset = sep;
                break;
            }
        }
    } else {
        // Find the previous separator before current position
        for (let i = separators.length - 1; i >= 0; i--) {
            if (separators[i] < currentOffset - 1) {
                targetOffset = separators[i];
                break;
            }
        }
    }

    if (targetOffset !== null) {
        const targetPosition = document.positionAt(targetOffset);
        const newSelection = new vscode.Selection(targetPosition, targetPosition);
        editor.selection = newSelection;
        editor.revealRange(new vscode.Range(targetPosition, targetPosition), vscode.TextEditorRevealType.InCenter);
    }
}

export function deactivate() {
    // Cleanup
}
