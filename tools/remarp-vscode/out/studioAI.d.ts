export declare const providers: readonly ["claude", "kiro", "codex"];
export type AIProvider = typeof providers[number];
export interface AIConfig {
    provider: AIProvider;
    executable: string;
    model: string;
    effort: string;
    timeoutSeconds: number;
}
export interface AIJob {
    result: Promise<string>;
    cancel(): void;
}
export declare function aiProvider(value: unknown): AIProvider;
export declare function validateAIConfig(config: AIConfig): AIConfig;
export declare function aiRequest(source: string, request: unknown): string;
/** Files written here are private and temporary, never in the presentation project. */
export declare function prepareAI(config: AIConfig, prompt: string, directory: string): {
    args: string[];
    stdin: string;
};
export declare function aiResponse(provider: AIProvider, stdout: string, directory: string): string;
export declare function startAI(config: AIConfig, prompt: string): AIJob;
