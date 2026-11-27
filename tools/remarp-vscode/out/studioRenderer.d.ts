import * as vscode from 'vscode';
import { StudioManifest } from './studioModel';
export declare function studioShell(webview: vscode.Webview, extension: vscode.Uri, nonce?: string, hostChannel?: string): string;
/** No renderer request depends on the code-server webview service worker. */
export declare function studioFrame(_webview: vscode.Webview, extension: vscode.Uri, html: string, output: string, snapshot: string, _original: string, manifest: StudioManifest, generation: number, nonce?: string): string;
