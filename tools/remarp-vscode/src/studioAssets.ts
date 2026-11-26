import * as fs from 'fs';
import * as path from 'path';
import { inside } from './studioSnapshot';

const MAX_BYTES = 32 * 1024 * 1024;
const MAX_FILES = 2000;
const MAX_ENTRIES = 4000;
const MAX_HTML_BYTES = 64 * 1024 * 1024;
export function assertStudioDocumentSize(bytes: number): void {
    if (bytes > MAX_HTML_BYTES) { throw new Error('Studio renderer document exceeds the 64 MiB transfer limit.'); }
}
/** Bound expanded output before joining replacements (imports can amplify tiny inputs). */
export function boundedReplace(input: string, pattern: RegExp, replace: (...match: any[]) => string): string {
    assertStudioDocumentSize(Buffer.byteLength(input));
    const chunks: string[] = [];
    let end = 0, bytes = 0;
    const append = (value: string) => {
        bytes += Buffer.byteLength(value); assertStudioDocumentSize(bytes); chunks.push(value);
    };
    for (const match of input.matchAll(new RegExp(pattern.source, pattern.flags))) {
        append(input.slice(end, match.index)); append(replace(...match));
        end = match.index! + match[0].length;
    }
    append(input.slice(end));
    return chunks.join('');
}
const EMPTY_ASSET = 'data:application/octet-stream;base64,';
const imageTypes: Record<string, string> = {
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
    '.svg': 'image/svg+xml', '.webp': 'image/webp', '.avif': 'image/avif', '.ico': 'image/x-icon',
};
const types: Record<string, string> = { ...imageTypes, '.css': 'text/css', '.js': 'text/javascript', '.mjs': 'text/javascript',
    '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.otf': 'font/otf',
    '.mp4': 'video/mp4', '.webm': 'video/webm', '.ogg': 'audio/ogg', '.mp3': 'audio/mpeg', '.wav': 'audio/wav' };
const escape = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
export const decodeAttribute = (s: string): string => s.replace(/&(?:#(x[\da-f]+|\d+)|(amp|quot|apos|lt|gt));/gi, (all, code, name) => {
    if (code) {
        const value = code[0].toLowerCase() === 'x' ? parseInt(code.slice(1), 16) : parseInt(code, 10);
        return value > 0 && value <= 0x10ffff ? String.fromCodePoint(value) : all;
    }
    return ({ amp: '&', quot: '"', apos: "'", lt: '<', gt: '>' } as Record<string, string>)[name.toLowerCase()];
});
// Quoted > characters must not terminate tags; script/style contents and comments are separate tokens.
export const htmlTokens = /<!--[\s\S]*?-->|<(script|style)\b((?:[^>"']|"[^"]*"|'[^']*')*)>([\s\S]*?)<\/\1\s*>|<[a-z][\w:-]*\b(?:[^>"']|"[^"]*"|'[^']*')*>/gi;
export function mapAttributes(tag: string, map: (name: string, value: string) => string | undefined): string {
    return boundedReplace(tag, /(\s+)([^\s=/>]+)(?:\s*=\s*("[^"]*"|'[^']*'|[^\s>]+))?/g, (whole, space, name, raw) => {
        if (raw === undefined) { return whole; }
        const value = decodeAttribute(/^["']/.test(raw) ? raw.slice(1, -1) : raw);
        const mapped = map(name.toLowerCase(), value);
        return mapped === undefined ? '' : `${space}${name}="${escape(mapped)}"`;
    });
}
export interface StudioAssets { html: string; images: Record<string, string>; warnings: string[]; }
interface Asset { file: string; relative: string; extension: string; }

/** Build a finite self-contained renderer from isolated output and staged assets only. */
export function bundleStudioAssets(html: string, output: string, snapshot: string): StudioAssets {
    if (Buffer.byteLength(html) > MAX_HTML_BYTES) { throw new Error('Studio renderer document exceeds the 64 MiB transfer limit.'); }
    const roots = [...new Set([output, snapshot].map(root => fs.realpathSync(root)))];
    const loaded = new Map<string, Buffer>();
    const encoded = new Map<string, string>();
    const processing = new Set<string>();
    const warnings: string[] = [];
    let bytes = 0, encodedBytes = 0;
    const warn = (url: string) => {
        const message = `Studio could not bundle optional local asset: ${url.slice(0, 200)}`;
        if (warnings.length < 12 && !warnings.includes(message)) { warnings.push(message); }
    };
    function local(url: string): boolean { return !/^(?:[a-z][\w+.-]*:|\/\/|#)/i.test(url); }
    function locate(url: string, base: string): Asset {
        const raw = url.split(/[?#]/)[0];
        let decoded: string;
        try { decoded = decodeURIComponent(raw); } catch { throw new Error('Studio asset URL has invalid encoding.'); }
        if (!decoded || decoded.includes('\\') || decoded.includes('\0') || path.posix.isAbsolute(decoded)) { throw new Error('Studio asset path is not project-relative.'); }
        const relative = path.posix.normalize(path.posix.join(base, decoded));
        if (relative === '..' || relative.startsWith('../')) { throw new Error('Studio asset is outside the isolated snapshot.'); }
        const extension = path.posix.extname(relative).toLowerCase();
        if (!types[extension]) { throw new Error(`Unsupported Studio resource type: ${extension || '(none)'}.`); }
        for (const root of roots) {
            const file = path.resolve(root, relative);
            if (!inside(root, file)) { throw new Error('Studio asset is outside the isolated snapshot.'); }
            let component = root;
            for (const name of relative.split('/')) {
                component = path.join(component, name);
                if (!fs.existsSync(component)) { break; }
                if (fs.lstatSync(component).isSymbolicLink()) { throw new Error('Studio asset symlinks are not supported.'); }
            }
            if (fs.existsSync(file)) {
                if (!inside(root, fs.realpathSync(file)) || !fs.statSync(file).isFile()) { throw new Error('Studio resource is not an isolated regular file.'); }
                return { file, relative, extension };
            }
        }
        throw new Error('Studio resource was not staged.');
    }
    function read(asset: Asset): Buffer {
        const prior = loaded.get(asset.file);
        if (prior) { return prior; }
        const size = fs.statSync(asset.file).size;
        if (loaded.size >= MAX_FILES || bytes + size > MAX_BYTES) { throw new Error('Studio renderer assets exceed the 32 MiB / 2,000 file limit.'); }
        const value = fs.readFileSync(asset.file);
        bytes += value.length;
        if (bytes > MAX_BYTES) { throw new Error('Studio renderer assets exceed the 32 MiB limit.'); }
        loaded.set(asset.file, value);
        return value;
    }
    function resource(url: string, base: string, required = false): string {
        if (!local(url)) { return url; }
        try {
            const asset = locate(url, base);
            if (!encoded.has(asset.file)) {
                if (processing.has(asset.file)) { throw new Error('Cyclic Studio stylesheet import.'); }
                if (processing.size >= 32) { throw new Error('Studio stylesheet nesting exceeds the 32-level limit.'); }
                processing.add(asset.file);
                try {
                    let content = read(asset);
                    if (asset.extension === '.css') { content = Buffer.from(css(content.toString('utf8'), path.posix.dirname(asset.relative))); }
                    const prefix = `data:${types[asset.extension]};base64,`;
                    encodedBytes += prefix.length + 4 * Math.ceil(content.length / 3);
                    assertStudioDocumentSize(encodedBytes);
                    encoded.set(asset.file, prefix + content.toString('base64'));
                } finally { processing.delete(asset.file); }
            }
            const fragment = url.includes('#') ? url.slice(url.indexOf('#')) : '';
            return encoded.get(asset.file)! + fragment;
        } catch (error) {
            if (required || /limit|Cyclic/.test(String(error))) { throw new Error(`Cannot bundle Studio asset ${url.slice(0, 200)}: ${error instanceof Error ? error.message : 'invalid resource'}`); }
            warn(url);
            return EMPTY_ASSET;
        }
    }
    function css(text: string, base: string): string {
        return boundedReplace(text, /\/\*[\s\S]*?\*\/|@import\s+(?:"([^"]+)"|'([^']+)')|url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*?))\s*\)/gi,
            (token, importDouble, importSingle, double, single, bare) => {
                if (token.startsWith('/*')) { return token; }
                const imported = importDouble !== undefined || importSingle !== undefined;
                const url = imported ? (importDouble ?? importSingle) : (double ?? single ?? bare).trim();
                const isImport = imported || /\.css(?:[?#]|$)/i.test(url);
                const bundled = resource(url, base, isImport).replace(/"/g, '%22');
                return `${imported ? '@import ' : ''}url("${bundled}")`;
            });
    }
    const attributes = (tag: string): string => {
        const name = /^<([\w:-]+)/.exec(tag)![1].toLowerCase();
        const stylesheet = name === 'link' && /\brel\s*=\s*(?:["']stylesheet["']|stylesheet\b)/i.test(tag);
        return mapAttributes(tag, (attr, value) => {
            if (attr === 'style') { return css(value, '.'); }
            if (attr === 'src' && ['script', 'img', 'audio', 'video', 'source', 'track', 'input'].includes(name)) {
                return resource(value, '.', name === 'script');
            }
            if (attr === 'poster' && name === 'video') { return resource(value, '.'); }
            if ((attr === 'href' || attr === 'xlink:href') && ['link', 'image', 'use'].includes(name)) {
                return resource(value, '.', stylesheet);
            }
            if (attr === 'srcset' && ['img', 'source'].includes(name) && !/^data:/i.test(value)) {
                return boundedReplace(value, /[^,]+/g, candidate => {
                    const match = /^\s*(\S+)(\s+[\d.]+[wx])?\s*$/.exec(candidate);
                    return match ? resource(match[1], '.') + (match[2] || '') : EMPTY_ASSET;
                });
            }
            // No document nesting or base/navigation escapes are needed to render a slide.
            if (attr === 'srcdoc' || (attr === 'src' && ['iframe', 'embed'].includes(name)) || (attr === 'data' && name === 'object')) {
                warn(`${name} document is not supported; open the standalone compiled presentation`); return undefined;
            }
            return value;
        });
    };
    html = boundedReplace(html, htmlTokens, (token, block, attrs, body) => {
        if (token.startsWith('<!--')) { return token; }
        if (block) { return attributes(`<${block}${attrs}>`) + (block.toLowerCase() === 'style' ? css(body, '.') : body) + `</${block}>`; }
        return attributes(token);
    });
    // Canvas/runtime logos create images from strings after parsing. Expose only supported
    // images already present in the isolated compiler/snapshot trees, never original files.
    const images: Record<string, string> = Object.create(null);
    let entries = 0;
    function imagesIn(root: string, relative = '', depth = 0): void {
        if (depth > 64) { throw new Error('Studio renderer asset directory nesting exceeds the 64-level limit.'); }
        for (const entry of fs.readdirSync(path.join(root, relative), { withFileTypes: true })) {
            if (++entries > MAX_ENTRIES) { throw new Error('Studio renderer assets exceed the 4,000 entry limit.'); }
            if (entry.name.startsWith('.')) { continue; }
            const child = path.posix.join(relative, entry.name);
            if (entry.isDirectory()) { imagesIn(root, child, depth + 1); }
            else if (imageTypes[path.extname(entry.name).toLowerCase()] && !(child in images)) { images[child] = resource(child, '.'); }
        }
    }
    roots.forEach(root => imagesIn(root));
    if (Buffer.byteLength(html) + Buffer.byteLength(JSON.stringify(images)) > MAX_HTML_BYTES) { throw new Error('Studio renderer document exceeds the 64 MiB transfer limit.'); }
    return { html, images, warnings };
}
