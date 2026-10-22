import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
export interface SnapshotFile { text: string; version?: number; }
export type Snapshot = Map<string, SnapshotFile>;
export const digest = (s: string) => crypto.createHash('sha256').update(s).digest('hex');
export function inside(root: string, file: string): boolean {
    const relative = path.relative(root, file);
    return relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative));
}
export function sourcePath(root: string, relative: string): string {
    if (typeof relative !== 'string' || path.isAbsolute(relative) || relative.includes('\\') || relative.includes('\0')) { throw new Error('Invalid source path.'); }
    const file = path.resolve(root, relative);
    let ancestor = file;
    while (!fs.existsSync(ancestor) && ancestor !== root && inside(root, ancestor)) { ancestor = path.dirname(ancestor); }
    if (!inside(root, file) || !inside(root, fs.realpathSync(ancestor))) { throw new Error('Source is outside the project.'); }
    return file;
}
/** Stage only source and explicitly referenced local assets, never an entire repo. */
export function stageSnapshot(root: string, directory: string, sources: Snapshot): void {
    fs.mkdirSync(directory, { recursive: true });
    const queue: string[] = [];
    for (const [relative, source] of sources) {
        fs.writeFileSync(sourcePath(directory, relative), source.text, 'utf8');
        queue.push(...assetReferences(source.text));
    }
    let total = 0, count = 0;
    const visited = new Set<string>();
    function copy(relative: string): void {
        relative = relative.replace(/^\.\//, '');
        if (visited.has(relative) || sources.has(relative) || !relative || /^[a-z][\w+.-]*:/i.test(relative) || relative.startsWith('#')) { return; }
        visited.add(relative);
        const from = sourcePath(root, relative);
        if (!fs.existsSync(from)) { return; }
        // Reject symlink components, including in-root ancestor cycles. Staging is
        // deliberately conservative rather than recursively mirroring a workspace.
        let component = root;
        for (const name of path.relative(root, from).split(path.sep)) {
            component = path.join(component, name);
            if (fs.lstatSync(component).isSymbolicLink()) { throw new Error('Referenced asset symlinks are not supported; use a real project-local path.'); }
        }
        if (visited.size > 4000) { throw new Error('Referenced assets exceed the Studio staging limit (4,000 entries).'); }
        const stat = fs.statSync(from);
        if (stat.isDirectory()) {
            for (const name of fs.readdirSync(from)) {
                if (!name.startsWith('.') && !['node_modules', 'packages', 'out', 'slides'].includes(name)) { copy(path.posix.join(relative, name)); }
            }
        } else if (stat.isFile()) {
            total += stat.size; count++;
            if (total > 32 * 1024 * 1024 || count > 2000) { throw new Error('Referenced assets exceed the Studio staging limit (32 MiB / 2,000 files).'); }
            const to = sourcePath(directory, relative);
            fs.mkdirSync(path.dirname(to), { recursive: true }); fs.copyFileSync(from, to);
            if (/\.(css|json)$/i.test(relative)) {
                const text = fs.readFileSync(from, 'utf8');
                for (const ref of assetReferences(text)) { copy(path.posix.join(path.posix.dirname(relative), ref)); }
            }
        }
    }
    queue.forEach(copy);
}
function assetReferences(text: string): string[] {
    const refs: string[] = [];
    const patterns = [/!\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)/g, /(?:src|href)\s*=\s*["']([^"']+)["']/g,
        /url\(\s*["']?([^"')\s]+)["']?\s*\)/g, /^\s*(?:source|logo|background|image|@background|@img):\s*["']?([^\s"']+)/gm,
        /"(?:spec|src|image|logo)"\s*:\s*"([^"]+)"/g];
    for (const pattern of patterns) { for (const m of text.matchAll(pattern)) { refs.push(m[1].split(/[?#]/)[0]); } }
    return refs.filter(ref => ref && !/^[a-z][\w+.-]*:/i.test(ref));
}
