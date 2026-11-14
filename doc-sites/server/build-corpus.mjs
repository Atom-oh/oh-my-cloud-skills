import {access, readdir, readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {PLUGINS} from './chat.mjs';
import {guideUrl} from './guide-paths.mjs';
import {guideText} from './guide-text.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
async function walk(dir) {
  const entries = await readdir(dir, {withFileTypes: true});
  const groups = await Promise.all(entries.map((e) => e.isDirectory()
    ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]));
  return groups.flat();
}

const corpus = [];
for (const [locale, directory] of [
  ['en', 'docs'], ['ko', 'i18n/ko/docusaurus-plugin-content-docs/current'],
]) {
  const base = path.join(root, directory);
  for (const file of (await walk(base)).filter((f) => /\.mdx?$/.test(f))) {
    const relative = path.relative(base, file).replace(/\\/g, '/').replace(/\.mdx?$/, '');
    const section = relative.split('/')[0];
    const plugin = PLUGINS.includes(section) ? section : section === 'remarp-guide' ? 'aws-content-plugin' : null;
    if (!plugin) continue;
    const raw = await readFile(file, 'utf8');
    const title = raw.match(/^title:\s*["']?(.+?)["']?\s*$/m)?.[1]
      || raw.match(/^#\s+(.+)$/m)?.[1] || relative;
    const body = guideText(raw);
    const url = guideUrl(relative, locale);
    // Fail packaging if a citation would lead to an unpublished route.
    await access(path.join(root, 'build', url, 'index.html'));
    for (let offset = 0; offset < body.length; offset += 3500) {
      const text = body.slice(offset, offset + 4500).trim();
      if (text) corpus.push({locale, plugin, title, url, text});
    }
  }
}
await writeFile(path.join(root, 'server/content.generated.json'), JSON.stringify(corpus));
console.log(`Indexed ${corpus.length} public guide excerpts in two languages.`);
