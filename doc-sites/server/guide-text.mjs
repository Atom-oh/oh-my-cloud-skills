// Keep syntax examples verbatim: JSX stripping must only touch prose, never code.
export function guideText(raw) {
  const source = raw.replace(/^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/, '');
  const output = [];
  let prose = [], fence;
  function flush() {
    output.push(prose.join('\n').replace(
      /(`+)[\s\S]*?\1|^import [^\n]*|\{\/\*[\s\S]*?\*\/\}|<[^>]+>/gm,
      (match, ticks) => ticks ? match : '',
    ));
    prose = [];
  }
  for (const line of source.split(/\r?\n/)) {
    if (fence) {
      output.push(line);
      const end = line.match(/^ {0,3}(`{3,}|~{3,})\s*$/);
      if (end && end[1][0] === fence[0] && end[1].length >= fence.length) fence = undefined;
    } else {
      const start = line.match(/^ {0,3}(`{3,}|~{3,})/);
      if (start) {flush(); fence = start[1]; output.push(line);}
      else prose.push(line);
    }
  }
  flush();
  return output.join('\n');
}
