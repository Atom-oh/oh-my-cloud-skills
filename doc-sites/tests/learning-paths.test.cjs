const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

test('every registered plugin has learning links that resolve in both locales', () => {
  const root = path.resolve(__dirname, '..');
  const source = fs.readFileSync(path.join(root, 'src/components/GuideWorkspace/guides.ts'), 'utf8');
  const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS}}).outputText;
  const sandbox = {exports: {}, require: (name) => {
    assert.equal(name, '@docusaurus/Translate');
    return {translate: ({message}) => message};
  }};
  vm.runInNewContext(compiled, sandbox);
  const {guides} = sandbox.exports;
  const catalog = JSON.parse(fs.readFileSync(path.join(root, '../hosts/catalog.json'), 'utf8'));
  assert.deepEqual(Array.from(guides, (g) => g.id).sort(), Object.keys(catalog.plugins).sort());
  for (const guide of guides) {
    for (const link of [guide.setup, guide.next]) {
      assert.ok(link.startsWith('/docs/'), link);
      const [relative, fragment] = link.slice('/docs/'.length).split('#');
      for (const locale of ['docs', 'i18n/ko/docusaurus-plugin-content-docs/current']) {
        const file = path.join(root, locale, relative + '.md');
        assert.ok(fs.existsSync(file), `${guide.id}: ${locale}/${relative}`);
        if (fragment) assert.ok(fs.readFileSync(file, 'utf8').includes(`{#${fragment}}`), link);
      }
    }
  }
});
