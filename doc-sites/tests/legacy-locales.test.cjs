const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');
const legacyLocales = require('../plugins/legacy-locales.cjs');

async function fixture(t) {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'guide-locales-'));
  t.after(() => fs.rm(dir, {recursive: true, force: true}));
  return dir;
}

for (const [defaultLocale, other] of [['ko', 'en'], ['en', 'ko']]) {
  test(`default ${defaultLocale} alias preserves the real ${other} page`, async (t) => {
    const outDir = await fixture(t);
    const realPage = path.join(outDir, other, 'docs/guide/index.html');
    await fs.mkdir(path.dirname(realPage), {recursive: true});
    await fs.writeFile(realPage, '<h1>real localized guide</h1>');
    const plugin = legacyLocales({i18n: {defaultLocale, currentLocale: defaultLocale}});
    await plugin.postBuild({outDir, baseUrl: '/site/', routesPaths: ['/site/docs/guide', '/site/404.html', '/site/*']});
    assert.equal(await fs.readFile(realPage, 'utf8'), '<h1>real localized guide</h1>');
    const html = await fs.readFile(path.join(outDir, defaultLocale, 'docs/guide/index.html'), 'utf8');
    assert.match(html, new RegExp(`<html lang="${defaultLocale}">`));
    const script = html.match(/<script>(.*?)<\/script>/s)[1];
    let destination;
    vm.runInNewContext(script, {location: {search: '?source=old', hash: '#stable-id', replace: (url) => {destination = url;}}});
    assert.equal(destination, '/site/docs/guide?source=old#stable-id');
  });
}

test('a non-default locale build creates no nested locale aliases', async (t) => {
  const outDir = await fixture(t);
  const plugin = legacyLocales({i18n: {defaultLocale: 'ko', currentLocale: 'en'}});
  await plugin.postBuild({outDir, baseUrl: '/site/en/', routesPaths: ['/site/en/docs/guide']});
  assert.deepEqual(await fs.readdir(outDir), []);
});
