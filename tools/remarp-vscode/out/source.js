"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.slideStarts = slideStarts;
/** Source line starts shared by text preview, outline and editor navigation. */
function slideStarts(text) {
    const lines = text.split('\n');
    let start = 0;
    if (lines[0]?.trim() === '---') {
        const end = lines.findIndex((line, i) => i > 0 && line.trim() === '---');
        if (end > 0) {
            start = end + 1;
        }
    }
    const starts = [start];
    let fence = '';
    for (let i = start; i < lines.length; i++) {
        const line = lines[i].replace(/\r$/, '');
        if (fence) {
            const close = line.match(/^ {0,3}(`+|~+)\s*$/);
            if (close && close[1][0] === fence[0] && close[1].length >= fence.length) {
                fence = '';
            }
            continue;
        }
        const open = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
        if (open && !(open[1][0] === '`' && open[2].includes('`'))) {
            fence = open[1];
        }
        else if (line.trim() === '---') {
            starts.push(i + 1);
        }
    }
    return starts;
}
//# sourceMappingURL=source.js.map