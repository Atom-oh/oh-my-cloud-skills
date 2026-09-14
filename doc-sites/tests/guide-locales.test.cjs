'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');

const checker = path.resolve(__dirname, '../scripts/check-guide-locales.cjs');
const koRoot = 'i18n/ko/docusaurus-plugin-content-docs/current';
const manifestPath = 'i18n/ko/source-hashes.json';
const catalogs = [
  'i18n/ko/code.json',
  'i18n/ko/docusaurus-plugin-content-docs/current.json',
  'i18n/ko/docusaurus-theme-classic/navbar.json',
  'i18n/ko/docusaurus-theme-classic/footer.json',
];
const english = [
  '---',
  'title: Guide',
  'description: An English guide',
  'sidebar_label: Guide',
  'id: guide',
  'slug: /guide',
  'sidebar_position: 1',
  '---',
  "import Demo from '@site/src/components/Demo';",
  '<span id="예전-제목" />',
  '# Guide',
  'Read the guide before making changes.',
  '## First step {#first-step}',
  'Use `--safe` twice: `--safe`. [Reference](/docs/reference#details).',
  '<Demo src="/demos/one.html" title="English demo" command="tool --safe" style={{width: "100%"}} />',
  '````md',
  '```bash',
  'tool --safe',
  '```',
  '````',
  '## Second step {#second-step}',
  'Record the result.',
  '',
].join('\n');
const korean = english
  .replace('title: Guide', 'title: 가이드')
  .replace('description: An English guide', 'description: 한국어 가이드')
  .replace('sidebar_label: Guide', 'sidebar_label: 가이드')
  .replace('# Guide', '# 가이드')
  .replace('Read the guide before making changes.', '변경하기 전에 가이드를 읽습니다.')
  .replace('## First step', '## 첫 단계')
  .replace('Use `--safe` twice: `--safe`. [Reference]', '`--safe`를 두 번 사용합니다: `--safe`. [참조]')
  .replace('title="English demo"', 'title="한국어 데모"')
  .replace('## Second step', '## 두 번째 단계')
  .replace('Record the result.', '결과를 기록합니다.');

function write(site, relative, content) {
  const destination = path.join(site, relative);
  fs.mkdirSync(path.dirname(destination), {recursive: true});
  fs.writeFileSync(destination, content);
}

function fixture(t) {
  const site = fs.mkdtempSync(path.join(os.tmpdir(), 'guide-locales-'));
  t.after(() => fs.rmSync(site, {recursive: true, force: true}));
  write(site, 'docs/guide.mdx', english);
  write(site, `${koRoot}/guide.mdx`, korean);
  write(site, 'docs/nested/page.md', '# More\n\nMore English instructions.\n');
  write(site, `${koRoot}/nested/page.md`, '# 추가 안내\n\n추가 한국어 안내입니다.\n');
  write(site, 'src/App.tsx', [
    "import Translate, {translate} from '@docusaurus/Translate';",
    "const count = translate({id: 'ui.count', message: 'Count: {count}'});",
    'const greeting = <Translate id="ui.greeting">{\'Hello {name}\'}</Translate>;',
    '',
  ].join('\n'));
  write(site, catalogs[0], JSON.stringify({
    'ui.count': {message: '개수: {count}'},
    'ui.greeting': {message: '안녕하세요 {name}'},
  }));
  write(site, 'docusaurus.config.ts', [
    "const releaseLabel = 'Release notes';",
    'const config = {',
    "  presets: [['classic', {docs: {versions: {current: {label: 'Next'}}}}]],",
    '  themeConfig: {',
    "    navbar: {title: 'Guide site', logo: {alt: 'Site logo', src: 'logo.svg'}, items: [",
    "      {label: 'Guides', items: [{label: releaseLabel, to: '/docs/release'}]},",
    '    ]},',
    "    footer: {links: [{title: 'Links', items: [{label: releaseLabel, to: '/docs/release'}]}],",
    "      copyright: 'Copyright {year}'},",
    '  },',
    '} satisfies SiteConfig;',
    'export default config;',
    '',
  ].join('\n'));
  write(site, 'sidebars.ts', [
    'const sidebars = {',
    "  remarpGuide: ['guide', {type: 'category', label: 'Syntax Reference', items: ['nested/page']}],",
    '} satisfies SidebarsConfig;',
    'export default sidebars;',
    '',
  ].join('\n'));
  write(site, catalogs[1], JSON.stringify({
    'version.label': {message: '다음'},
    'sidebar.remarpGuide.category.Syntax Reference': {message: '문법 참고'},
  }));
  write(site, catalogs[2], JSON.stringify({
    title: {message: '가이드 사이트'},
    'logo.alt': {message: '사이트 로고'},
    'item.label.Guides': {message: '안내'},
    'item.label.Release notes': {message: '릴리스 노트'},
  }));
  write(site, catalogs[3], JSON.stringify({
    'link.title.Links': {message: '링크'},
    'link.item.label.Release notes': {message: '릴리스 노트'},
    copyright: {message: '저작권 {year}'},
  }));
  return site;
}

function run(site, ...args) {
  return spawnSync(process.execPath, [checker, '--site', site, ...args], {
    encoding: 'utf8',
    timeout: 20_000,
    env: {...process.env, NO_COLOR: '1'},
  });
}

function pass(result) {
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
}

function reject(result, reason) {
  assert.notEqual(result.status, 0, 'Invalid locale input was accepted');
  assert.equal(result.signal, null, 'The checker must reject, not hang or crash');
  assert.match(`${result.stdout}\n${result.stderr}`, reason);
}

function edit(site, relative, change) {
  write(site, relative, change(fs.readFileSync(path.join(site, relative), 'utf8')));
}

function editCatalog(site, relative, change) {
  const catalog = JSON.parse(fs.readFileSync(path.join(site, relative), 'utf8'));
  change(catalog);
  write(site, relative, JSON.stringify(catalog));
}

test('record accepts a translated pair and default checking leaves the manifest unchanged', (t) => {
  const site = fixture(t);
  pass(run(site, '--record'));
  const recorded = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  const manifest = JSON.parse(recorded);
  assert.equal(manifest.schemaVersion, 1);
  assert.deepEqual(Object.keys(manifest.files).sort(), ['guide.mdx', 'nested/page.md']);
  assert.equal(manifest.files['guide.mdx'], createHash('sha256').update(english).digest('hex'));
  pass(run(site));
  assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), recorded);
  assert.equal(fs.readFileSync(path.join(site, 'docs/guide.mdx'), 'utf8'), english);
  assert.equal(fs.readFileSync(path.join(site, `${koRoot}/guide.mdx`), 'utf8'), korean);
});

test('CRLF sources and translations produce LF-normalized hashes and comparisons', (t) => {
  const site = fixture(t);
  write(site, 'docs/guide.mdx', english.replaceAll('\n', '\r\n'));
  write(site, `${koRoot}/guide.mdx`, korean.replaceAll('\n', '\r\n'));
  pass(run(site, '--record'));
  const manifest = JSON.parse(fs.readFileSync(path.join(site, manifestPath), 'utf8'));
  assert.equal(manifest.files['guide.mdx'], createHash('sha256').update(english).digest('hex'));
  write(site, 'docs/guide.mdx', english);
  pass(run(site));
});

test('default checking rejects changed English prose until translations are reviewed and recorded', (t) => {
  const site = fixture(t);
  pass(run(site, '--record'));
  edit(site, 'docs/guide.mdx', (text) => text.replace('making changes', 'deployment'));
  reject(run(site), /source|stale/i);
  edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('변경하기 전에', '배포하기 전에'));
  pass(run(site, '--record'));
  pass(run(site));
});

test('default checking requires a recorded source manifest', (t) => {
  reject(run(fixture(t)), /source-hashes|manifest/i);
});

const corruptions = [
  {
    name: 'missing translated page',
    mutate: (site) => fs.unlinkSync(path.join(site, `${koRoot}/nested/page.md`)),
    reason: /missing.*nested\/page\.md/i,
  },
  {
    name: 'extra translated page',
    mutate: (site) => write(site, `${koRoot}/orphan.md`, '# 고립된 페이지\n\n안내입니다.\n'),
    reason: /extra.*orphan\.md/i,
  },
  {
    name: 'English copy containing legacy Korean IDs',
    mutate: (site) => write(site, `${koRoot}/guide.mdx`, english),
    reason: /translation|English/i,
  },
  {
    name: 'English body disguised by translated titles',
    mutate: (site) => write(site, `${koRoot}/guide.mdx`,
      english.replace('title: Guide', 'title: 안내').replace('# Guide', '# 안내')),
    reason: /translation|English/i,
  },
  {
    name: 'changed routing front matter',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('slug: /guide', 'slug: /different')),
    reason: /front.?matter|routing/i,
  },
  {
    name: 'changed numeric sidebar position',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('sidebar_position: 1', 'sidebar_position: 2')),
    reason: /front.?matter|routing/i,
  },
  {
    name: 'changed fenced command',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('\ntool --safe\n', '\ntool --unsafe\n')),
    reason: /fence|code/i,
  },
  {
    name: 'changed fence language',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('````md', '````text')),
    reason: /fence|code/i,
  },
  {
    name: 'lost repeated inline-code literal',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('`--safe`를 두 번 사용합니다: `--safe`.', '`--safe`를 사용합니다.')),
    reason: /inline/i,
  },
  {
    name: 'changed stable heading ID',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('{#first-step}', '{#other-step}')),
    reason: /heading/i,
  },
  {
    name: 'changed heading level',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('## 첫 단계', '### 첫 단계')),
    reason: /heading/i,
  },
  {
    name: 'reordered heading IDs',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text
      .replace('{#first-step}', '{#temporary}')
      .replace('{#second-step}', '{#first-step}')
      .replace('{#temporary}', '{#second-step}')),
    reason: /heading/i,
  },
  {
    name: 'changed legacy HTML ID',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('id="예전-제목"', 'id="다른-제목"')),
    reason: /legacy|attribute/i,
  },
  {
    name: 'changed relative URL or fragment',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('/docs/reference#details', '/docs/reference#other')),
    reason: /URL|link/i,
  },
  {
    name: 'changed import target',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('@site/src/components/Demo', '@site/src/components/Other')),
    reason: /import/i,
  },
  {
    name: 'changed functional JSX command',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('command="tool --safe"', 'command="tool --other"')),
    reason: /attribute|JSX/i,
  },
  {
    name: 'changed functional JSX expression',
    mutate: (site) => edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('width: "100%"', 'width: "50%"')),
    reason: /attribute|JSX/i,
  },
  {
    name: 'missing function-style UI message',
    mutate: (site) => editCatalog(site, catalogs[0], (data) => { delete data['ui.count']; }),
    reason: /ui\.count/,
  },
  {
    name: 'missing JSX-style UI message',
    mutate: (site) => editCatalog(site, catalogs[0], (data) => { delete data['ui.greeting']; }),
    reason: /ui\.greeting/,
  },
  {
    name: 'null UI message',
    mutate: (site) => editCatalog(site, catalogs[0], (data) => { data['ui.count'].message = null; }),
    reason: /message/i,
  },
  {
    name: 'blank UI message',
    mutate: (site) => editCatalog(site, catalogs[0], (data) => { data['ui.count'].message = '  '; }),
    reason: /message/i,
  },
  {
    name: 'lost function-message placeholder',
    mutate: (site) => editCatalog(site, catalogs[0], (data) => { data['ui.count'].message = '개수'; }),
    reason: /placeholder/i,
  },
  {
    name: 'renamed JSX-message placeholder',
    mutate: (site) => editCatalog(site, catalogs[0], (data) => { data['ui.greeting'].message = '안녕하세요 {other}'; }),
    reason: /placeholder/i,
  },
];

for (const {name, mutate, reason} of corruptions) {
  test(`rejects ${name} in normal and record modes`, (t) => {
    const site = fixture(t);
    pass(run(site, '--record'));
    const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
    mutate(site);
    reject(run(site), reason);
    reject(run(site, '--record'), reason);
    assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
  });
}

for (const catalog of catalogs) {
  test(`requires current Korean catalog ${catalog}`, (t) => {
    const site = fixture(t);
    fs.unlinkSync(path.join(site, catalog));
    reject(run(site, '--record'), /catalog/i);
    assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
  });
}

test('record cannot create a manifest for structurally invalid translations', (t) => {
  const site = fixture(t);
  write(site, `${koRoot}/guide.mdx`, korean.replace('{#first-step}', '{#changed}'));
  reject(run(site, '--record'), /heading/i);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

test('record cannot replace a previous manifest when the changed source code no longer matches', (t) => {
  const site = fixture(t);
  pass(run(site, '--record'));
  const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  edit(site, 'docs/guide.mdx', (text) => text.replace('\ntool --safe\n', '\ntool --new\n'));
  reject(run(site, '--record'), /fence|code/i);
  assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
});

test('removing explicit IDs from both languages cannot waive stable heading coverage', (t) => {
  const site = fixture(t);
  for (const file of ['docs/guide.mdx', `${koRoot}/guide.mdx`]) {
    edit(site, file, (text) => text.replace(' {#first-step}', ''));
  }
  reject(run(site, '--record'), /heading/i);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

test('an empty guide set cannot be recorded as complete coverage', (t) => {
  const site = fixture(t);
  fs.rmSync(path.join(site, 'docs'), {recursive: true});
  fs.mkdirSync(path.join(site, 'docs'));
  fs.rmSync(path.join(site, koRoot), {recursive: true});
  fs.mkdirSync(path.join(site, koRoot));
  reject(run(site, '--record'), /empty|no.*guide/i);
});

test('static UI IDs in nested source files are required but comments and strings are not calls', (t) => {
  const site = fixture(t);
  write(site, 'src/nested/More.tsx', [
    '// translate({id: "not.a.call", message: "Ignored"})',
    'const example = \'<Translate id="not.jsx">Ignored</Translate>\';',
    "const label = translate({id: 'ui.' + 'more', message: 'More'});",
    'const jsx = <Translate id={\'ui.more\'}>More</Translate>;',
  ].join('\n'));
  reject(run(site, '--record'), /ui\.more/);
  editCatalog(site, catalogs[0], (data) => { data['ui.more'] = {message: '더 보기'}; });
  pass(run(site, '--record'));
});

const unsupportedUi = [
  ['aliased named translation import', "import {translate as t} from '@docusaurus/Translate';\nconst label = t({id: 'untracked', message: 'Hidden'});", /canonical.*import/i],
  ['aliased default translation import', "import T from '@docusaurus/Translate';\nconst label = <T id=\"untracked\">Hidden</T>;", /canonical.*import/i],
  ['namespace translation import', "import * as messages from '@docusaurus/Translate';\nconst label = messages.translate({id: 'untracked', message: 'Hidden'});", /canonical.*import/i],
  ['function without an ID', "const label = translate({message: 'Hidden'});", /static.*id/i],
  ['function with a dynamic ID', "const label = translate({id: messageId, message: 'Hidden'});", /static.*id/i],
  ['function with a descriptor variable', 'const label = translate(descriptor);', /static.*id/i],
  ['function without a descriptor', 'const label = translate();', /static.*id/i],
  ['JSX without an ID', 'const label = <Translate>Hidden</Translate>;', /static.*id/i],
  ['self-closing JSX with a dynamic ID', 'const label = <Translate id={messageId} />;', /static.*id/i],
  ['spread overriding a function ID', "const label = translate({id: 'ui.count', message: 'Count: {count}', ...descriptor});", /static.*id/i],
  ['spread overriding a JSX ID', 'const label = <Translate id="ui.greeting" {...props}>{\'Hello {name}\'}</Translate>;', /static.*id/i],
];

for (const [name, source, reason] of unsupportedUi) {
  for (const args of [[], ['--record']]) {
    test(`static grammar rejects ${name} in ${args.length ? 'record' : 'normal'} mode without replacing the manifest`, (t) => {
      const site = fixture(t);
      pass(run(site, '--record'));
      const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
      write(site, 'src/Unsupported.tsx', source);
      reject(run(site, ...args), reason);
      assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    });
  }
}

for (const [name, suffix, both] of [
  ['reference link definitions', '\n[Reference][one]\n\n[one]: /docs/one\n[two]: /docs/two\n', true],
  ['quoted reference definitions', '\n> [Reference][one]\n>\n> [one]: /docs/one\n> [two]: /docs/two\n', true],
  ['list reference definitions', '\n- [one]: /docs/one\n- [two]: /docs/two\n\n[Reference][one]\n', true],
  ['Setext H1', '\n새 제목\n===\n', false],
  ['Setext H2', '\n새 제목\n---\n', false],
  ['blockquote heading', '\n> ## 인용 제목\n', false],
  ['nested blockquote heading', '\n > > ### 중첩 제목\n', false],
  ['quoted list heading', '\n> - ## 목록 안의 인용 제목\n', false],
  ['bullet list heading', '\n- ## 목록 제목\n', false],
  ['ordered list heading', '\n1. ## 순서 목록 제목\n', false],
  ['empty blockquote heading', '\n> ##\n', false],
  ['blockquote Setext heading', '\n> 인용 제목\n> ---\n', false],
]) {
  for (const args of [[], ['--record']]) {
    test(`static grammar rejects ${name} in ${args.length ? 'record' : 'normal'} mode without replacing the manifest`, (t) => {
      const site = fixture(t);
      pass(run(site, '--record'));
      edit(site, `${koRoot}/guide.mdx`, (text) => text + suffix);
      if (both) {
        // A prior permissive record can contain matching definitions even when
        // the Korean reference usage points to a different defined target.
        const source = english + suffix;
        write(site, 'docs/guide.mdx', source);
        edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('[Reference][one]', '[참조][two]'));
        editCatalog(site, manifestPath, (data) => {
          data.files['guide.mdx'] = createHash('sha256').update(source).digest('hex');
        });
      }
      const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
      reject(run(site, ...args), /reference.*definition|Setext|(?:blockquote|list).*heading/i);
      assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    });
  }
}

test('static grammar keeps fenced examples, inline literals, comments and separated horizontal rules', (t) => {
  const site = fixture(t);
  const examples = [
    '',
    '---',
    '',
    '```mdx',
    "import {translate as t} from '@docusaurus/Translate';",
    'translate({message: "Example"});',
    '<Translate>Example</Translate>',
    '[label]: /example',
    'Heading',
    '---',
    '> ## Quoted heading',
    '```',
    '',
    '`[label]: /example`',
    '`> ## Quoted heading`',
    '`Heading\n---`',
    '<!--',
    '[label]: /ignored',
    'Heading',
    '---',
    '> ## Quoted heading',
    '-->',
    '',
  ].join('\n');
  for (const file of ['docs/guide.mdx', `${koRoot}/guide.mdx`]) {
    edit(site, file, (text) => text + examples);
  }
  write(site, 'src/Literals.tsx', [
    '// translate({message: "Example"});',
    'const text = \'<Translate>Example</Translate>\';',
    '// import {translate as t} from "@docusaurus/Translate";',
    'import {value as named} from "./unrelated";',
  ].join('\n'));
  pass(run(site, '--record'));
  const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  pass(run(site));
  assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
});

test('static grammar preserves plain indentation before an ATX heading', (t) => {
  const site = fixture(t);
  for (const file of ['docs/guide.mdx', `${koRoot}/guide.mdx`]) {
    edit(site, file, (text) => text.replace('\n## ', '\n  ## '));
  }
  pass(run(site, '--record'));
  const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  pass(run(site));
  assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
});

test('translated human-facing JSX attributes and reordered inline literals remain valid', (t) => {
  const site = fixture(t);
  edit(site, 'docs/guide.mdx', (text) => `${text}\nUse \`--one\` and \`--two\`.\n<img src="/img/a.svg" alt="Picture" aria-label="Preview" />\n`);
  edit(site, `${koRoot}/guide.mdx`, (text) => `${text}\n\`--two\`와 \`--one\`을 사용합니다.\n<img src="/img/a.svg" alt="그림" aria-label="미리 보기" />\n`);
  pass(run(site, '--record'));
});

test('front-matter formatting changes preserve parsed routing values', (t) => {
  const site = fixture(t);
  edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('slug: /guide', 'slug: "/guide"'));
  pass(run(site, '--record'));
});

test('non-YAML front matter is rejected before any executable engine can run', (t) => {
  const site = fixture(t);
  const marker = path.join(site, 'executed');
  write(site, `${koRoot}/guide.mdx`, [
    '---js',
    `({title: 'Guide', touched: require('node:fs').writeFileSync(${JSON.stringify(marker)}, 'ran')})`,
    '---',
    '# 가이드',
    '한국어 설명입니다.',
  ].join('\n'));
  reject(run(site, '--record'), /front.?matter/i);
  assert.equal(fs.existsSync(marker), false);
});

test('comment-looking text inside inline code is still protected code', (t) => {
  const site = fixture(t);
  edit(site, 'docs/guide.mdx', (text) => `${text}\nKeep \`/* original */\` unchanged.\n`);
  edit(site, `${koRoot}/guide.mdx`, (text) => `${text}\n\`/* original */\`을 보존합니다.\n`);
  pass(run(site, '--record'));
  edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('/* original */', '/* changed */'));
  reject(run(site, '--record'), /inline/i);
});

test('comment-looking command attributes cannot conceal a functional change', (t) => {
  const site = fixture(t);
  for (const file of ['docs/guide.mdx', `${koRoot}/guide.mdx`]) {
    edit(site, file, (text) => text.replace('command="tool --safe"', 'command="tool {/* original */}"'));
  }
  pass(run(site, '--record'));
  edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('{/* original */}', '{/* changed */}'));
  reject(run(site, '--record'), /attribute|JSX/i);
});

test('Korean comments do not turn copied English into translated prose', (t) => {
  const site = fixture(t);
  write(site, `${koRoot}/guide.mdx`, `${english}\nAn English line. {/* 번역이 아닌 주석 */}\n`);
  reject(run(site, '--record'), /translation|English/i);
});

test('static Translate IDs in JavaScript JSX files are also required', (t) => {
  const site = fixture(t);
  write(site, 'src/Extra.js', 'export const extra = <Translate id="ui.js">Extra</Translate>;');
  reject(run(site, '--record'), /ui\.js/);
  editCatalog(site, catalogs[0], (data) => { data['ui.js'] = {message: '추가'}; });
  pass(run(site, '--record'));
});

test('inline code containing non-JSX angle syntax remains literal data', (t) => {
  const site = fixture(t);
  edit(site, 'docs/guide.mdx', (text) => `${text}\nKeep \`<path/to/file>\` literal.\n`);
  edit(site, `${koRoot}/guide.mdx`, (text) => `${text}\n\`<path/to/file>\`을 그대로 사용합니다.\n`);
  pass(run(site, '--record'));
});

test('translated template-literal JSX titles do not count as Markdown code', (t) => {
  const site = fixture(t);
  edit(site, 'docs/guide.mdx', (text) => text.replace('title="English demo"', 'title={`English demo`}'));
  edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('title="한국어 데모"', 'title={`한국어 데모`}'));
  pass(run(site, '--record'));
});

for (const directory of [false, true]) {
  test(`symlinked guide ${directory ? 'directories' : 'files'} cannot disappear from coverage`, (t) => {
    const site = fixture(t);
    fs.symlinkSync(
      path.join(site, 'docs', directory ? 'nested' : 'guide.mdx'),
      path.join(site, koRoot, directory ? 'linked' : 'extra.mdx'),
      directory ? 'dir' : 'file',
    );
    reject(run(site, '--record'), /symlink/i);
    assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
  });
}

for (const [catalog, id] of [
  [catalogs[2], 'title'],
  [catalogs[2], 'logo.alt'],
  [catalogs[2], 'item.label.Release notes'],
  [catalogs[3], 'link.title.Links'],
  [catalogs[3], 'link.item.label.Release notes'],
  [catalogs[3], 'copyright'],
  [catalogs[1], 'version.label'],
  [catalogs[1], 'sidebar.remarpGuide.category.Syntax Reference'],
]) {
  test(`individual catalog key ${id} cannot fall back to English in either mode`, (t) => {
    const site = fixture(t);
    pass(run(site, '--record'));
    const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
    editCatalog(site, catalog, (data) => { delete data[id]; });
    for (const args of [[], ['--record']]) {
      reject(run(site, ...args), /catalog/i);
      assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    }
  });
}

for (const [name, suffix] of [
  ['inserted export', '\nexport const amount = 999;\n'],
  ['inserted body expression', '\n{amount + 1}\n'],
  ['inline body expression', '\n한국어 문장 안의 {amount}입니다.\n'],
]) {
  test(`unsupported live MDX ${name} fails normal and record modes`, (t) => {
    const site = fixture(t);
    pass(run(site, '--record'));
    const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
    edit(site, `${koRoot}/guide.mdx`, (text) => text + suffix);
    for (const args of [[], ['--record']]) {
      reject(run(site, ...args), /MDX|export|expression/i);
      assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    }
  });
}

test('matching recorded English cannot bless changed live MDX exports or expressions', (t) => {
  const site = fixture(t);
  pass(run(site, '--record'));
  const source = `${english}\nexport const amount = 2;\n\n{amount}\n`;
  write(site, 'docs/guide.mdx', source);
  write(site, `${koRoot}/guide.mdx`, `${korean}\nexport const amount = 999;\n\n{amount + 1}\n`);
  // Model a pre-existing record made by the earlier permissive checker.
  editCatalog(site, manifestPath, (data) => {
    data.files['guide.mdx'] = createHash('sha256').update(source).digest('hex');
  });
  const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  for (const args of [[], ['--record']]) {
    reject(run(site, ...args), /MDX|export|expression/i);
    assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
  }
});

test('identical unsupported live MDX cannot be newly recorded', (t) => {
  const site = fixture(t);
  for (const file of ['docs/guide.mdx', `${koRoot}/guide.mdx`]) {
    edit(site, file, (text) => `${text}\nexport const amount = 2;\n\n{amount}\n`);
  }
  reject(run(site, '--record'), /MDX|export|expression/i);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

test('static imports, escaped braces and frozen MDX examples remain supported', (t) => {
  const site = fixture(t);
  for (const file of ['docs/guide.mdx', `${koRoot}/guide.mdx`]) {
    edit(site, file, (text) => `${text}\nimport {value as named} from '@site/static';\n\n\\{literal\\}\n\n\`\`\`mdx\nexport const amount = 2;\n{amount}\n\`\`\`\n`);
  }
  pass(run(site, '--record'));
});

for (const [name, file, beforeText, afterText] of [
  ['function message', 'src/App.tsx', 'Count: {count}', 'Total: {count}'],
  ['JSX message', 'src/App.tsx', 'Hello {name}', 'Welcome {name}'],
  ['navbar title', 'docusaurus.config.ts', "title: 'Guide site'", "title: 'Changed guide site'"],
  ['logo alt', 'docusaurus.config.ts', "alt: 'Site logo'", "alt: 'Changed site logo'"],
  ['footer text', 'docusaurus.config.ts', 'Copyright {year}', 'Copyright notice {year}'],
  ['version label', 'docusaurus.config.ts', "label: 'Next'", "label: 'Current'"],
]) {
  test(`same-ID English ${name} edits invalidate freshness until explicit record`, (t) => {
    const site = fixture(t);
    pass(run(site, '--record'));
    const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
    edit(site, file, (text) => text.replace(beforeText, afterText));
    reject(run(site), /source|stale|fresh/i);
    assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    pass(run(site, '--record'));
    assert.notEqual(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    pass(run(site));
  });
}

test('a stable sidebar key still tracks English category label changes', (t) => {
  const site = fixture(t);
  edit(site, 'sidebars.ts', (text) => text.replace("label: 'Syntax Reference'", "key: 'syntax', label: 'Syntax Reference'"));
  editCatalog(site, catalogs[1], (data) => {
    delete data['sidebar.remarpGuide.category.Syntax Reference'];
    data['sidebar.remarpGuide.category.syntax'] = {message: '문법 참고'};
  });
  pass(run(site, '--record'));
  edit(site, 'sidebars.ts', (text) => text.replace('Syntax Reference', 'Syntax Handbook'));
  reject(run(site), /source|stale|fresh/i);
  pass(run(site, '--record'));
  editCatalog(site, catalogs[1], (data) => { delete data['sidebar.remarpGuide.category.syntax']; });
  reject(run(site, '--record'), /catalog/i);
});

test('UI source changes never allow record to waive a broken guide', (t) => {
  const site = fixture(t);
  pass(run(site, '--record'));
  const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  edit(site, 'src/App.tsx', (text) => text.replace('Count: {count}', 'Total: {count}'));
  edit(site, `${koRoot}/guide.mdx`, (text) => text.replace('{#first-step}', '{#changed}'));
  reject(run(site, '--record'), /heading/i);
  assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
});

test('config statements are rejected without executing project configuration', (t) => {
  const site = fixture(t);
  const marker = path.join(site, 'config-executed');
  edit(site, 'docusaurus.config.ts', (text) =>
    `${text}\nrequire('node:fs').writeFileSync(${JSON.stringify(marker)}, 'ran');\n`);
  reject(run(site, '--record'), /static|config/i);
  assert.equal(fs.existsSync(marker), false);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

test('computed catalog labels fail closed rather than inventing a required ID', (t) => {
  const site = fixture(t);
  edit(site, 'docusaurus.config.ts', (text) => text.replace("'Release notes'", 'getReleaseLabel()'));
  reject(run(site, '--record'), /static|config|label/i);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

test('computed sidebars fail closed rather than omitting category coverage', (t) => {
  const site = fixture(t);
  write(site, 'sidebars.ts', 'export default createSidebars();');
  reject(run(site, '--record'), /static|sidebar/i);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

test('the current copyright year template is captured as source data, not evaluated', (t) => {
  const site = fixture(t);
  edit(site, 'docusaurus.config.ts', (text) =>
    text.replace("'Copyright {year}'", '`Copyright © ${new Date().getFullYear()} Example`'));
  editCatalog(site, catalogs[3], (data) => { data.copyright.message = 'Copyright © 2026 Example'; });
  pass(run(site, '--record'));
  edit(site, 'docusaurus.config.ts', (text) => text.replace('Copyright ©', 'Copyright notice ©'));
  reject(run(site), /source|stale|fresh/i);
  pass(run(site, '--record'));
});

test('unused const initializers cannot mutate the statically inventoried labels', (t) => {
  const site = fixture(t);
  pass(run(site, '--record'));
  const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
  edit(site, 'docusaurus.config.ts', (text) =>
    `${text}\nconst changed = (config.themeConfig.navbar.items[0].items[0].label = 'Hidden English');\n`);
  for (const args of [[], ['--record']]) {
    reject(run(site, ...args), /static|config/i);
    assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
  }
});

test('unused config initializer calls are rejected without executing them', (t) => {
  const site = fixture(t);
  const marker = path.join(site, 'initializer-executed');
  edit(site, 'docusaurus.config.ts', (text) =>
    `${text}\nconst ignored = require('node:fs').writeFileSync(${JSON.stringify(marker)}, 'ran');\n`);
  reject(run(site, '--record'), /static|config/i);
  assert.equal(fs.existsSync(marker), false);
  assert.equal(fs.existsSync(path.join(site, manifestPath)), false);
});

for (const [tag, original, changed] of [
  ['script', 'globalThis.amount = 2;', 'globalThis.amount = 999;'],
  ['style', '@import "/original.css";', '@import "/changed.css";'],
]) {
  test(`live ${tag} bodies cannot hide code changes behind matching JSX tags`, (t) => {
    const site = fixture(t);
    pass(run(site, '--record'));
    const source = `${english}\n<${tag}>${original}</${tag}>\n`;
    write(site, 'docs/guide.mdx', source);
    write(site, `${koRoot}/guide.mdx`, `${korean}\n<${tag}>${changed}</${tag}>\n`);
    editCatalog(site, manifestPath, (data) => {
      data.files['guide.mdx'] = createHash('sha256').update(source).digest('hex');
    });
    const before = fs.readFileSync(path.join(site, manifestPath), 'utf8');
    for (const args of [[], ['--record']]) {
      reject(run(site, ...args), /MDX|script|style/i);
      assert.equal(fs.readFileSync(path.join(site, manifestPath), 'utf8'), before);
    }
  });
}

test('fully qualified classic preset names retain version-label freshness', (t) => {
  const site = fixture(t);
  edit(site, 'docusaurus.config.ts', (text) => text.replace("['classic',", "['@docusaurus/preset-classic',"));
  pass(run(site, '--record'));
  edit(site, 'docusaurus.config.ts', (text) => text.replace("label: 'Next'", "label: 'Current'"));
  reject(run(site), /source|stale|fresh/i);
  pass(run(site, '--record'));
});
