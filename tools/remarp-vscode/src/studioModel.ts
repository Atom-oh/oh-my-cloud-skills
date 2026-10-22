/** Host-owned edit planning. No VS Code or browser dependencies. */
export interface Span { start: number; end: number; }
export interface Field extends Span { value: string | number; line?: Span; }
export interface Geometry { x: number; y: number; width: number; height: number; canvasWidth: number; canvasHeight: number; centered: boolean; }
export interface StudioNode {
    id: string; kind: string; label: string; renderId?: string | null; cssTarget?: string;
    text?: Field; body?: Field; geometry?: Geometry; position?: Span; size?: Span; step?: Field; lineEnd?: Span;
}
export interface StudioSlide {
    id: string; file: string; title: string; type: string; block: string; source: string; range: Span; eol: string;
    nodes: StudioNode[]; directives: Record<string, Field | null>; cssEditable: boolean;
    css: null | { insert: Span; targets: Record<string, { insert: Span | null; properties: Record<string, Field> }> };
}
export interface StudioManifest { version: number; html: string; files: Record<string, string>; slides: StudioSlide[]; }
export interface Patch extends Span { text: string; }
export interface Intent { slide: string; node?: string; operation: string; value?: unknown; property?: string; }
const has = (o: object, k: string) => Object.prototype.hasOwnProperty.call(o, k);
const properties = new Set(['color', 'background-color', 'font-size', 'font-weight', 'text-align', 'padding', 'margin-top', 'margin-bottom', 'gap', 'border-radius']);
const directives: Record<string, RegExp> = {
    fit: /^(auto|shrink|off)$/, columns: /^[1-4]$/, layout: /^(two-column|three-column|grid-2x2|grid-2x3|grid-3x2|grid-3x3)$/, transition: /^(none|fade|slide|zoom)$/
};
function string(value: unknown, max = 100000): string {
    if (typeof value !== 'string' || value.length > max || value.includes('\0')) { throw new Error('Invalid text value.'); }
    return value;
}
function integer(value: unknown, min = 0, max = 10000): number {
    if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < min || value > max) { throw new Error('Invalid geometry or step value.'); }
    return value;
}
export function findSlide(manifest: StudioManifest, id: unknown): StudioSlide {
    const slide = manifest.slides.find(s => s.id === id);
    if (!slide) { throw new Error('Selection no longer exists. Select again.'); }
    return slide;
}
export function planEdit(manifest: StudioManifest, intent: Intent): { file: string; patches: Patch[] } {
    if (!intent || typeof intent !== 'object') { throw new Error('Invalid edit request.'); }
    const slide = findSlide(manifest, intent.slide);
    const node = slide.nodes.find(n => n.id === intent.node);
    const patch = (span: Span, text: string): Patch => ({ start: span.start, end: span.end, text });
    let patches: Patch[];
    switch (intent.operation) {
        case 'source': patches = [patch(slide.range, string(intent.value).replace(/\r\n|\r|\n/g, slide.eol))]; break;
        case 'text': case 'body': {
            const field = intent.operation === 'text' ? node?.text : node?.body;
            if (!field) { throw new Error('This field is source-only.'); }
            let value = string(intent.value);
            if (intent.operation === 'text' && /[\r\n]/.test(value)) { throw new Error('Labels must be a single line.'); }
            if (node?.geometry && /"/.test(value)) { throw new Error('Canvas labels cannot contain double quotes.'); }
            value = value.replace(/\r\n|\r|\n/g, slide.eol);
            patches = [patch(field, value)]; break;
        }
        case 'directive': {
            const name = string(intent.property, 32), value = string(intent.value, 80);
            if (!has(directives, name) || !directives[name].test(value)) { throw new Error('Unsupported directive value.'); }
            if (has(slide.directives, name) && slide.directives[name] === null) { throw new Error('Duplicate directives: edit source instead.'); }
            const field = slide.directives[name];
            patches = [field ? patch(field, value) : patch({ start: slide.range.start, end: slide.range.start }, `@${name}: ${value}${slide.eol}`)]; break;
        }
        case 'geometry': {
            if (!node?.geometry || !node.position || !node.size || !intent.value || typeof intent.value !== 'object') { throw new Error('This element cannot move or resize.'); }
            const v = intent.value as Record<string, unknown>;
            const x = integer(v.x), y = integer(v.y), width = integer(v.width, 1), height = integer(v.height, 1);
            if (node.kind === 'icon' && width !== height) { throw new Error('Icons require a square size.'); }
            const g = node.geometry, left = g.centered ? x - width / 2 : x, top = g.centered ? y - height / 2 : y;
            if (left < 0 || top < 0 || left + width > g.canvasWidth || top + height > g.canvasHeight) { throw new Error('Keep the element inside its Canvas.'); }
            patches = [patch(node.position, `${x},${y}`), patch(node.size, node.kind === 'icon' ? `${width}` : `${width},${height}`)]; break;
        }
        case 'step': {
            if (!node?.geometry) { throw new Error('This element has no editable reveal step.'); }
            const value = integer(intent.value, 0, 100);
            if (node.step) { patches = [patch(node.step, String(value))]; }
            else if (node.lineEnd) { patches = [patch(node.lineEnd, ` step ${value}`)]; }
            else { throw new Error('Edit the step in source.'); }
            break;
        }
        case 'style': {
            const property = string(intent.property, 32);
            if (!properties.has(property) || !node?.cssTarget || !slide.cssEditable) { throw new Error('This style is source-only.'); }
            const value = intent.value === null ? null : string(intent.value, 80);
            // No URLs, declarations, functions, selectors or script-bearing CSS.
            if (value !== null && (!value.trim() || !/^[#\w.%, \-]+$/.test(value))) { throw new Error('Use a plain color, number, unit or keyword (no URLs/functions).'); }
            const target = slide.css?.targets[node.cssTarget], current = target?.properties[property];
            if (value === null) { patches = current?.line ? [patch(current.line, '')] : []; }
            else if (current) { patches = [patch(current, value)]; }
            else if (target?.insert) { patches = [patch(target.insert, `  ${property}: ${value}${slide.eol}`)]; }
            else {
                const content = `<${node.cssTarget}>${slide.eol}  ${property}: ${value}${slide.eol}</${node.cssTarget}>${slide.eol}`;
                patches = slide.css ? [patch(slide.css.insert, content)] :
                    [patch({ start: slide.range.end, end: slide.range.end }, `${slide.eol}${slide.eol}:::css${slide.eol}${content}:::${slide.eol}`)];
            }
            break;
        }
        case 'issue': {
            const value = string(intent.value, 4000).trim().replace(/--/g, '—').replace(/>/g, '&gt;');
            if (!value) { throw new Error('Enter an improvement request.'); }
            patches = [patch({ start: slide.range.end, end: slide.range.end }, `${slide.eol}<!-- issue: ${value} -->${slide.eol}`)]; break;
        }
        default: throw new Error('Unsupported edit operation.');
    }
    return { file: slide.file, patches };
}
export function applyPatches(source: string, patches: Patch[]): string {
    const ordered = [...patches].sort((a, b) => b.start - a.start);
    let last = source.length;
    for (const p of ordered) {
        if (!Number.isSafeInteger(p.start) || !Number.isSafeInteger(p.end) || p.start < 0 || p.start > p.end || p.end > last) { throw new Error('Invalid or overlapping source ranges.'); }
        source = source.slice(0, p.start) + p.text + source.slice(p.end);
        last = p.start;
    }
    return source;
}
