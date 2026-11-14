const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

test('workflow exercises cover registered plugins and resolve both language references and example assets', () => {
  const root = path.resolve(__dirname, '..');
  const source = fs.readFileSync(path.join(root, 'src/components/GuideWorkspace/workflows.ts'), 'utf8');
  const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS}}).outputText;
  const context = {exports: {}, require(name) {
    assert.equal(name, '@docusaurus/Translate');
    return {translate: ({message}) => message};
  }};
  vm.runInNewContext(compiled, context);
  const {workflows} = context.exports;
  const plugins = Object.keys(JSON.parse(fs.readFileSync(path.join(root, '../hosts/catalog.json'))).plugins);
  assert.deepEqual([...new Set(Array.from(workflows, (w) => w.plugin))].sort(), plugins.sort());
  assert.equal(new Set(workflows.map((w) => w.id)).size, workflows.length);
  for (const workflow of workflows) {
    for (const field of ['title', 'summary', 'prompt', 'result', 'check', 'output']) {
      assert.ok(workflow[field]?.trim(), `${workflow.id}: missing ${field}`);
    }
    assert.ok(workflow.guide.startsWith('/docs/'));
    const [route, fragment] = workflow.guide.slice('/docs/'.length).split('#');
    const relative = route.replace(/\/$/, '');
    for (const locale of ['docs', 'i18n/ko/docusaurus-plugin-content-docs/current']) {
      // Docusaurus removes the duplicate terminal segment for commands/commands.
      const candidates = [relative + '.md', relative + '.mdx', `${relative}/${path.basename(relative)}.md`];
      const file = candidates.map((f) => path.join(root, locale, f)).find((f) => fs.existsSync(f));
      assert.ok(file, `${workflow.id}: ${locale}/${relative}`);
      if (fragment) assert.ok(fs.readFileSync(file, 'utf8').includes(`{#${fragment}}`), workflow.guide);
    }
    for (const asset of [workflow.image, workflow.demo].filter(Boolean)) {
      assert.ok(asset.startsWith('/img/') || asset.startsWith('/demos/'));
      assert.ok(fs.existsSync(path.join(root, 'static', asset)), asset);
    }
    if (workflow.demo) assert.ok(workflow.image, `${workflow.id}: preview needs a visible entry point`);
  }
});
