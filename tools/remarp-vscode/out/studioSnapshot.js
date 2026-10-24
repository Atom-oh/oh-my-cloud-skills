"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.digest = void 0;
exports.inside = inside;
exports.sourcePath = sourcePath;
exports.stageSnapshot = stageSnapshot;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const crypto = __importStar(require("crypto"));
const digest = (s) => crypto.createHash('sha256').update(s).digest('hex');
exports.digest = digest;
function inside(root, file) {
    const relative = path.relative(root, file);
    return relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative));
}
function sourcePath(root, relative) {
    if (typeof relative !== 'string' || path.isAbsolute(relative) || relative.includes('\\') || relative.includes('\0')) {
        throw new Error('Invalid source path.');
    }
    const file = path.resolve(root, relative);
    let ancestor = file;
    while (!fs.existsSync(ancestor) && ancestor !== root && inside(root, ancestor)) {
        ancestor = path.dirname(ancestor);
    }
    if (!inside(root, file) || !inside(root, fs.realpathSync(ancestor))) {
        throw new Error('Source is outside the project.');
    }
    return file;
}
/** Stage only source and explicitly referenced local assets, never an entire repo. */
function stageSnapshot(root, directory, sources) {
    fs.mkdirSync(directory, { recursive: true });
    const queue = [];
    for (const [relative, source] of sources) {
        fs.writeFileSync(sourcePath(directory, relative), source.text, 'utf8');
        queue.push(...assetReferences(source.text));
    }
    let total = 0, count = 0;
    const visited = new Set();
    function copy(relative) {
        relative = relative.replace(/^\.\//, '');
        if (visited.has(relative) || sources.has(relative) || !relative || /^[a-z][\w+.-]*:/i.test(relative) || relative.startsWith('#')) {
            return;
        }
        visited.add(relative);
        // Authored text names many paths the compiler never loads (a code sample's absolute script src, a
        // link to the site root), so a reference outside the project is skipped, not a staging failure.
        let from;
        try {
            from = sourcePath(root, relative);
        }
        catch {
            return;
        }
        if (!fs.existsSync(from)) {
            return;
        }
        // Reject symlink components, including in-root ancestor cycles. Staging is
        // deliberately conservative rather than recursively mirroring a workspace.
        let component = root;
        for (const name of path.relative(root, from).split(path.sep)) {
            component = path.join(component, name);
            if (fs.lstatSync(component).isSymbolicLink()) {
                throw new Error('Referenced asset symlinks are not supported; use a real project-local path.');
            }
        }
        if (visited.size > 4000) {
            throw new Error('Referenced assets exceed the Studio staging limit (4,000 entries).');
        }
        const stat = fs.statSync(from);
        if (stat.isDirectory()) {
            for (const name of fs.readdirSync(from)) {
                if (!name.startsWith('.') && !['node_modules', 'packages', 'out', 'slides'].includes(name)) {
                    copy(path.posix.join(relative, name));
                }
            }
        }
        else if (stat.isFile()) {
            total += stat.size;
            count++;
            if (total > 32 * 1024 * 1024 || count > 2000) {
                throw new Error('Referenced assets exceed the Studio staging limit (32 MiB / 2,000 files).');
            }
            const to = sourcePath(directory, relative);
            fs.mkdirSync(path.dirname(to), { recursive: true });
            fs.copyFileSync(from, to);
            if (/\.(css|json)$/i.test(relative)) {
                const text = fs.readFileSync(from, 'utf8');
                for (const ref of assetReferences(text)) {
                    copy(path.posix.join(path.posix.dirname(relative), ref));
                }
            }
        }
    }
    queue.forEach(copy);
}
function assetReferences(text) {
    const refs = [];
    const patterns = [/!\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)/g, /(?:src|href)\s*=\s*["']([^"']+)["']/g,
        /url\(\s*["']?([^"')\s]+)["']?\s*\)/g, /^\s*(?:source|logo|logoSrc|logoDark|logoDarkSrc|background|image|@background|@img):\s*["']?([^\s"']+)/gm,
        /"(?:spec|src|image|logo)"\s*:\s*"([^"]+)"/g,
        // A Canvas icon whose quoted name holds a slash or a dot is an author path the compiler loads at
        // runtime (drawIcon); a short name is an AWS service icon, not a project path.
        /^\s*icon\s+\w+\s+"([^"]*[/.][^"]*)"/gm,
        // A file-backed :::archify block holds the spec path as its whole body (the inline form starts with {).
        /^[ \t]*:::archify\b[^\n]*\r?\n\s*([^\s{:][^\r\n]*?)[ \t]*\r?$/gm];
    for (const pattern of patterns) {
        for (const m of text.matchAll(pattern)) {
            refs.push(m[1].split(/[?#]/)[0]);
        }
    }
    return refs.filter(ref => ref && !/^[a-z][\w+.-]*:/i.test(ref));
}
//# sourceMappingURL=studioSnapshot.js.map