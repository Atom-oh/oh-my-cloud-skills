const {mkdir, writeFile} = require('node:fs/promises');
const path = require('node:path');

// The default locale lives at root; its explicit locale prefix remains an alias.
// Never overwrite a real non-default locale with a compatibility redirect.
module.exports = function legacyLocales({i18n}) {
  const {currentLocale, defaultLocale} = i18n;
  return {
    name: 'legacy-locales',
    async postBuild({outDir, baseUrl, routesPaths}) {
      if (currentLocale !== defaultLocale) return;
      const label = defaultLocale === 'ko'
        ? {title: '페이지 이동', link: '한국어 가이드로 이동'}
        : {title: 'Page moved', link: 'Continue to the English documentation'};
      for (const route of routesPaths) {
        if (!route.startsWith(baseUrl) || route.includes('*')) continue;
        const relative = route.slice(baseUrl.length);
        if (relative === '404.html') continue;
        const target = JSON.stringify(route).replace(/</g, '\\u003c');
        const href = route.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
        const html = `<!doctype html><html lang="${defaultLocale}"><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>${label.title}</title><link rel="canonical" href="${href}"><script>location.replace(${target}+location.search+location.hash)</script></head><body><a href="${href}">${label.link}</a></body></html>`;
        const file = path.join(outDir, defaultLocale, relative, 'index.html');
        await mkdir(path.dirname(file), {recursive: true});
        await writeFile(file, html);
      }
    },
  };
};
