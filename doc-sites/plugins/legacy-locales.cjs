const {mkdir, writeFile} = require('node:fs/promises');
const path = require('node:path');

// English now lives at the original root routes. Keep previously published
// /en/ links (and explicit /ko/ links) working without a second content tree.
module.exports = function legacyLocales() {
  return {
    name: 'legacy-locales',
    async postBuild({outDir, baseUrl, routesPaths}) {
      for (const route of routesPaths) {
        if (!route.startsWith(baseUrl) || route.includes('*')) continue;
        const relative = route.slice(baseUrl.length);
        if (relative === '404.html') continue;
        const target = JSON.stringify(route).replace(/</g, '\\u003c');
        const href = route.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
        const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>Page moved</title><link rel="canonical" href="${href}"><script>location.replace(${target}+location.search+location.hash)</script></head><body><a href="${href}">Continue to the English documentation</a></body></html>`;
        for (const locale of ['en', 'ko']) {
          const file = path.join(outDir, locale, relative, 'index.html');
          await mkdir(path.dirname(file), {recursive: true});
          await writeFile(file, html);
        }
      }
    },
  };
};
