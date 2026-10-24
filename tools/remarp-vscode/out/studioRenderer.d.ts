import * as vscode from 'vscode';
import { StudioManifest } from './studioModel';
export declare function studioShell(webview: vscode.Webview, extension: vscode.Uri): string;
/** The deck is a separate document, not srcdoc (which inherits the shell CSP). */
export declare function studioFrame(webview: vscode.Webview, extension: vscode.Uri, html: string, output: string, snapshot: string, original: string, manifest: StudioManifest, generation: number): string;
