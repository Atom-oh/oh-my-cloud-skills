#!/usr/bin/env node
'use strict';

const {createHash} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {isDeepStrictEqual} = require('node:util');
// Docusaurus 3.9.2 exports this from markdownUtils, not its top-level index.
const {parseFileContentFrontMatter} = require('@docusaurus/utils/lib/markdownUtils');
const ts = require('typescript');
const {getTranslationFiles: themeTranslationFiles} = require('@docusaurus/theme-classic/lib/translations.js');
const {getLoadedContentTranslationFiles: docsTranslationFiles} = require('@docusaurus/plugin-content-docs/lib/translations.js');
const {normalizeSidebars} = require('@docusaurus/plugin-content-docs/lib/sidebars/normalization.js');

const normalize = (text) => text.replace(/\r\n?/g, '\n');
const read = (file) => normalize(fs.readFileSync(file, 'utf8'));
const hash = (text) => createHash('sha256').update(text).digest('hex');
const koDocs = 'i18n/ko/docusaurus-plugin-content-docs/current';
const catalogNames = [
  'code.json',
  'docusaurus-plugin-content-docs/current.json',
  'docusaurus-theme-classic/navbar.json',
  'docusaurus-theme-classic/footer.json',
];
const translatedFields = new Set(['title', 'description', 'sidebar_label']);
const translatedAttributes = new Set(['title', 'alt', 'aria-label']);
const multiset = (values) => [...values].sort();

function filesUnder(root, extension) {
  const files = [];
  function visit(directory) {
    for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
      const file = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) {
        throw new Error(`[coverage] Symlinked source entries cannot be verified: ${file}`);
      }
      if (entry.isDirectory()) visit(file);
      else if (entry.isFile() && extension.test(entry.name)) {
        files.push(path.relative(root, file).split(path.sep).join('/'));
      }
    }
  }
  visit(root);
  return files.sort();
}

function frontMatter(text) {
  const firstLine = text.replace(/^\uFEFF/, '').split('\n')[0];
  // gray-matter also has executable JavaScript engines. Guides use YAML only.
  if (firstLine.startsWith('---') && firstLine.trim() !== '---') {
    throw new Error('Only YAML front matter is supported');
  }
  const {frontMatter: metadata} = parseFileContentFrontMatter(text);
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata)) {
    throw new Error('Front matter must be an object');
  }
  const header = text.match(/^\uFEFF?---[ \t]*\n[\s\S]*?\n---[ \t]*(?:\n|$)/);
  if (firstLine.trim() === '---' && !header) throw new Error('Unclosed front matter');
  return {
    routing: Object.fromEntries(Object.entries(metadata).filter(([key]) => !translatedFields.has(key))),
    // The library trims content; retain raw fence whitespace for byte comparisons.
    body: header ? text.slice(header[0].length) : text,
  };
}

function splitFences(text) {
  const fences = [];
  let outside = '';
  let block = '';
  let marker = '';
  for (const line of text.match(/[^\n]*\n|[^\n]+$/g) || []) {
    const unquoted = line.replace(/^[ \t]*(?:>[ \t]*)*/, '');
    const start = unquoted.match(/^(`{3,}|~{3,})/);
    if (!marker && start) marker = start[1];
    else if (!marker) {
      outside += line;
      continue;
    }
    block += line;
    outside += line.endsWith('\n') ? '\n' : '';
    if (block !== line && new RegExp(`^${marker[0]}{${marker.length},}[ \\t]*\\n?$`).test(unquoted)) {
      fences.push(block);
      block = '';
      marker = '';
    }
  }
  if (marker) throw new Error('Unclosed code fence');
  return {fences, outside};
}

function staticString(node) {
  if (!node) return undefined;
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  if (ts.isJsxExpression(node) || ts.isParenthesizedExpression(node) || ts.isAsExpression(node)) {
    return staticString(node.expression);
  }
  if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.PlusToken) {
    const left = staticString(node.left);
    const right = staticString(node.right);
    if (left !== undefined && right !== undefined) return left + right;
  }
  return undefined;
}

function importStatements(text) {
  return [...text.matchAll(/^[ \t]*import(?=\s|['"])/gm)].map((match) => {
    const source = ts.createSourceFile('import.ts', text.slice(match.index), ts.ScriptTarget.Latest);
    const statement = source.statements[0];
    return statement && ts.isImportDeclaration(statement) ? statement.getText(source) : '';
  }).filter(Boolean);
}

function inlineMarkup(text) {
  const tags = [];
  const ids = [];
  const spans = [];
  let prose = '';
  let consumed = 0;
  // Consume each tag/code span before looking for comments inside its literals.
  // TypeScript parses attribute expressions as data; nothing is evaluated.
  const starts = /`+|<!--|\{[ \t]*\/\*|<\/?[A-Za-z][\w.:-]*/g;
  let match;
  while ((match = starts.exec(text))) {
    if (match[0].startsWith('`')) {
      const ticks = /`+/g;
      ticks.lastIndex = starts.lastIndex;
      let closing;
      while ((closing = ticks.exec(text)) && closing[0] !== match[0]) { /* inner literal ticks */ }
      if (!closing) continue;
      spans.push(text.slice(match.index, ticks.lastIndex));
      prose += text.slice(consumed, match.index);
      consumed = ticks.lastIndex;
      starts.lastIndex = consumed;
      continue;
    }
    if (match[0] === '<!--' || match[0].startsWith('{')) {
      const suffix = text.slice(starts.lastIndex);
      const closing = match[0] === '<!--' ? /-->/.exec(suffix) : /\*\/[ \t]*\}/.exec(suffix);
      if (!closing) throw new Error('Unclosed markup comment');
      prose += text.slice(consumed, match.index);
      consumed = starts.lastIndex + closing.index + closing[0].length;
      starts.lastIndex = consumed;
      continue;
    }
    let quote = '';
    let braces = 0;
    let end = starts.lastIndex;
    for (; end < text.length; end += 1) {
      const char = text[end];
      if (quote) {
        if (char === '\\') end += 1;
        else if (char === quote) quote = '';
      } else if ('"\'`'.includes(char)) quote = char;
      else if (char === '{') braces += 1;
      else if (char === '}') braces -= 1;
      else if (char === '>' && braces === 0) break;
    }
    if (end === text.length) throw new Error('Unclosed JSX/HTML tag');
    const raw = text.slice(match.index, end + 1);
    const closing = raw.startsWith('</');
    if (closing) tags.push([raw.replace(/\s/g, ''), []]);
    else {
      const tag = raw.replace(/\/?>$/, '/>');
      const source = ts.createSourceFile('tag.tsx', `const item = (${tag});`,
        ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
      if (source.parseDiagnostics.length) throw new Error('Invalid JSX/HTML attributes');
      const node = source.statements[0].declarationList.declarations[0].initializer.expression;
      const attributes = [];
      for (const attribute of node.attributes.properties) {
        if (ts.isJsxSpreadAttribute(attribute)) {
          attributes.push(['...', attribute.expression.getText(source)]);
          continue;
        }
        const name = attribute.name.getText(source);
        const literal = staticString(attribute.initializer);
        if (name === 'id') ids.push(literal ?? attribute.initializer?.getText(source));
        if (translatedAttributes.has(name) && literal !== undefined) continue;
        attributes.push([name, literal ?? attribute.initializer?.getText(source) ?? true]);
      }
      tags.push([node.tagName.getText(source), attributes]);
    }
    prose += text.slice(consumed, match.index);
    consumed = end + 1;
    starts.lastIndex = consumed;
  }
  return {tags, ids, inline: multiset(spans), prose: prose + text.slice(consumed)};
}

function linkTargets(text) {
  const targets = [];
  for (const match of text.matchAll(/\]\([ \t]*/g)) {
    const start = match.index + match[0].length;
    if (text[start] === '<') {
      const end = text.indexOf('>', start + 1);
      targets.push(text.slice(start + 1, end));
      continue;
    }
    let depth = 0;
    let end = start;
    for (; end < text.length; end += 1) {
      const char = text[end];
      if (char === '\\') end += 1;
      else if (char === '(') depth += 1;
      else if (char === ')' && depth) depth -= 1;
      else if (/\s/.test(char) || char === ')') break;
    }
    targets.push(text.slice(start, end));
  }
  for (const match of text.matchAll(/^[ \t]*\[([^\]\n]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))/gm)) {
    if (!match[1].startsWith('^')) targets.push(`${match[1]}:${match[2] ?? match[3]}`);
  }
  return targets;
}

function documentShape(text) {
  const parsed = frontMatter(text);
  const {fences, outside} = splitFences(parsed.body);
  const jsx = inlineMarkup(outside);
  if (jsx.tags.some(([name]) => ['script', 'style'].includes(name.toLowerCase()))) {
    throw new Error('Unsupported live MDX script/style element; keep examples in fenced code');
  }
  const imports = importStatements(jsx.prose);
  let plain = jsx.prose;
  for (const statement of imports) plain = plain.replace(statement, '');
  // Current guides are static wrappers. Imports and JSX attributes are compared
  // separately; live ESM exports/body expressions require a different grammar.
  if (/^(?:[ \t]*>[ \t]*)*[ \t]*export\b/m.test(plain)) {
    throw new Error('Unsupported live MDX export; keep examples in fenced code');
  }
  const withoutHeadingIds = plain.replace(
    /^([ \t]*#{1,6}[ \t]+[^\n]*?)\{#[^\s}]+\}[ \t]*$/gm, '$1',
  );
  for (const match of withoutHeadingIds.matchAll(/\{/g)) {
    let backslashes = 0;
    for (let index = match.index - 1; index >= 0 && withoutHeadingIds[index] === '\\'; index -= 1) {
      backslashes += 1;
    }
    if (backslashes % 2 === 0) throw new Error('Unsupported live MDX body expression');
  }
  const headings = [...plain.matchAll(/^[ \t]*(#{1,6})[ \t]+(.+)$/gm)].map((match) => ({
    level: match[1].length,
    id: match[2].match(/\{#([^\s}]+)\}[ \t]*$/)?.[1] ?? null,
  }));
  if (headings.some(({level, id}) => level > 1 && id === null)) {
    throw new Error('Headings below H1 require explicit stable heading IDs');
  }
  const prose = (keepHeadings) => plain
    .replace(keepHeadings ? /$^/g : /^[ \t]*#{1,6}[ \t]+.*$/gm, '')
    .replace(/\{#[^}]+\}|\]\([^)]*\)|https?:\/\/\S+/g, '')
    .replace(/\s+/g, ' ').trim();
  return {
    routing: parsed.routing, fences, inline: jsx.inline, headings,
    legacyIds: jsx.ids, attributes: jsx.tags, imports,
    links: linkTargets(jsx.prose),
    urls: [...outside.matchAll(/https?:\/\/[^\s<>"'`\])}]+/g)].map((match) => match[0]),
    prose: prose(false),
    allProse: prose(true),
  };
}

function compareDocuments(file, english, korean, errors) {
  let source;
  let translated;
  try {
    source = documentShape(english);
    translated = documentShape(korean);
  } catch (error) {
    errors.push(`[structure] ${file}: ${error.message}`);
    return;
  }
  const checks = {
    routing: 'routing front matter', fences: 'code fences', inline: 'inline code multiset',
    headings: 'heading IDs/levels/order', legacyIds: 'legacy HTML IDs',
    attributes: 'functional JSX attributes', imports: 'imports', links: 'link targets', urls: 'URLs',
  };
  for (const [key, label] of Object.entries(checks)) {
    if (!isDeepStrictEqual(source[key], translated[key])) errors.push(`[parity] ${file}: ${label} differ`);
  }
  const originalProse = /[A-Za-z가-힣]/.test(source.prose) ? source.prose : source.allProse;
  const translatedProse = /[A-Za-z가-힣]/.test(source.prose) ? translated.prose : translated.allProse;
  if (!/[가-힣]/.test(translatedProse) || originalProse === translatedProse) {
    errors.push(`[translation] ${file}: Korean prose is missing or still a literal English copy`);
  }
}

function placeholders(message) {
  return [...new Set([...message.matchAll(/\{\s*([A-Za-z_0-9][\w.]*)\s*(?:\}|,)/g)]
    .map((match) => match[1]))].sort();
}

function uiMessages(site) {
  const messages = [];
  const root = path.join(site, 'src');
  if (!fs.existsSync(root)) return messages;
  for (const file of filesUnder(root, /\.(?:[cm]?js|jsx|ts|tsx)$/)) {
    const kind = file.endsWith('.tsx') ? ts.ScriptKind.TSX
      : file.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JSX;
    const source = ts.createSourceFile(file, read(path.join(root, file)),
      ts.ScriptTarget.Latest, true, kind);
    function visit(node) {
      if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)
          && node.expression.text === 'translate' && node.arguments[0]
          && ts.isObjectLiteralExpression(node.arguments[0])) {
        const properties = node.arguments[0].properties.filter(ts.isPropertyAssignment);
        const initializer = (name) => properties.find((property) =>
          property.name.getText(source).replace(/^['"]|['"]$/g, '') === name)?.initializer;
        const id = staticString(initializer('id'));
        const message = staticString(initializer('message'));
        if (id !== undefined) messages.push({
          id, message, file,
          input: message !== undefined ? {text: message}
            : {expression: initializer('message')?.getText(source) ?? null},
        });
      }
      if (ts.isJsxElement(node) || ts.isJsxSelfClosingElement(node)) {
        const opening = ts.isJsxElement(node) ? node.openingElement : node;
        if (opening.tagName.getText(source) === 'Translate') {
          const id = staticString(opening.attributes.properties.find((attribute) =>
            ts.isJsxAttribute(attribute) && attribute.name.getText(source) === 'id')?.initializer);
          const children = ts.isJsxElement(node) ? node.children : [];
          const pieces = children.map((child) => ts.isJsxText(child) ? child.text : staticString(child));
          const message = pieces.every((piece) => piece !== undefined) ? pieces.join('') : undefined;
          if (id !== undefined) messages.push({
            id, message, file,
            input: message !== undefined ? {text: message}
              : {expression: children.map((child) => child.getText(source)).join('')},
          });
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
  return messages;
}

function staticModule(file) {
  // Parse constant data only. Never require/import a project config or sidebar.
  const source = ts.createSourceFile(file, read(file), ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const fail = () => { throw new Error(`[ui-source] ${path.basename(file)} requires statically resolvable config data`); };
  if (source.parseDiagnostics.length) fail();
  const bindings = new Map();
  const importedNames = new Set();
  let exported;
  for (const statement of source.statements) {
    if (ts.isImportDeclaration(statement)) {
      if (statement.importClause?.name) importedNames.add(statement.importClause.name.text);
      const names = statement.importClause?.namedBindings;
      if (names && ts.isNamespaceImport(names)) importedNames.add(names.name.text);
      if (names && ts.isNamedImports(names)) {
        for (const name of names.elements) importedNames.add(name.name.text);
      }
    } else if (ts.isVariableStatement(statement)) {
      if (!(statement.declarationList.flags & ts.NodeFlags.Const)) fail();
      for (const declaration of statement.declarationList.declarations) {
        if (!ts.isIdentifier(declaration.name) || !declaration.initializer) fail();
        bindings.set(declaration.name.text, declaration.initializer);
      }
    } else if (ts.isExportAssignment(statement) && !statement.isExportEquals) exported = statement.expression;
    else if (!ts.isInterfaceDeclaration(statement) && !ts.isTypeAliasDeclaration(statement)
        && !ts.isEmptyStatement(statement)) fail();
  }
  if (!exported) fail();
  function resolve(node, seen = new Set()) {
    if (!node) return undefined;
    if (seen.has(node)) fail();
    seen.add(node);
    if (ts.isParenthesizedExpression(node) || ts.isAsExpression(node)
        || ts.isSatisfiesExpression(node) || ts.isNonNullExpression(node)) {
      return resolve(node.expression, seen);
    }
    if (ts.isIdentifier(node) && bindings.has(node.text)) return resolve(bindings.get(node.text), seen);
    return node;
  }
  function fields(input, ancestors = new Set()) {
    const node = resolve(input);
    if (!node || !ts.isObjectLiteralExpression(node) || ancestors.has(node)) fail();
    const seen = new Set(ancestors).add(node);
    const result = new Map();
    for (const member of node.properties) {
      if (ts.isSpreadAssignment(member)) {
        for (const [key, value] of fields(member.expression, seen)) result.set(key, value);
      } else if (ts.isShorthandPropertyAssignment(member)) {
        result.set(member.name.text, member.name);
      } else if (ts.isPropertyAssignment(member)) {
        const key = ts.isIdentifier(member.name) || ts.isStringLiteral(member.name)
          ? member.name.text : undefined;
        if (key === undefined || key === '__proto__') fail();
        result.set(key, member.initializer);
      } else fail();
    }
    return result;
  }
  function array(input) {
    const node = resolve(input);
    if (!node || !ts.isArrayLiteralExpression(node)) fail();
    return node.elements.flatMap((item) => ts.isSpreadElement(item) ? array(item.expression) : [item]);
  }
  function yearTemplate(input) {
    const node = resolve(input);
    return node && ts.isTemplateExpression(node) && !bindings.has('Date') && !importedNames.has('Date')
      && node.templateSpans.every(({expression}) => {
        const call = resolve(expression);
        return ts.isCallExpression(call) && call.arguments.length === 0
          && ts.isPropertyAccessExpression(call.expression) && call.expression.name.text === 'getFullYear'
          && ts.isNewExpression(call.expression.expression)
          && call.expression.expression.arguments?.length === 0
          && ts.isIdentifier(call.expression.expression.expression)
          && call.expression.expression.expression.text === 'Date';
      });
  }
  function passiveInitializer(node) {
    // Even an unused const can mutate the exported config at module evaluation.
    // The existing year template is the sole source-only call shape we accept.
    if (ts.isTemplateExpression(node) && yearTemplate(node)) return;
    const assignment = ts.isBinaryExpression(node)
      && node.operatorToken.kind >= ts.SyntaxKind.FirstAssignment
      && node.operatorToken.kind <= ts.SyntaxKind.LastAssignment;
    const increment = ts.isPrefixUnaryExpression(node)
      && [ts.SyntaxKind.PlusPlusToken, ts.SyntaxKind.MinusMinusToken].includes(node.operator);
    if (assignment || increment || ts.isPostfixUnaryExpression(node)
        || ts.isCallExpression(node) || ts.isNewExpression(node)
        || ts.isTaggedTemplateExpression(node) || ts.isDeleteExpression(node)
        || ts.isAwaitExpression(node) || ts.isYieldExpression(node)
        || ts.isArrowFunction(node) || ts.isFunctionExpression(node)
        || ts.isClassExpression(node) || node.kind === ts.SyntaxKind.GetAccessor
        || node.kind === ts.SyntaxKind.SetAccessor || ts.isMethodDeclaration(node)) fail();
    ts.forEachChild(node, passiveInitializer);
  }
  function literal(input, allowCopyright = false, ancestors = new Set()) {
    const node = resolve(input);
    if (!node) return undefined;
    if (ancestors.has(node)) fail();
    const seen = new Set(ancestors).add(node);
    const string = staticString(node);
    if (string !== undefined) return string;
    if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.PlusToken) {
      const left = literal(node.left, false, seen);
      const right = literal(node.right, false, seen);
      if (typeof left === 'string' && typeof right === 'string') return left + right;
      fail();
    }
    if (ts.isNumericLiteral(node)) return Number(node.text);
    if (node.kind === ts.SyntaxKind.TrueKeyword) return true;
    if (node.kind === ts.SyntaxKind.FalseKeyword) return false;
    if (node.kind === ts.SyntaxKind.NullKeyword) return null;
    if (ts.isArrayLiteralExpression(node)) return array(node).map((item) => literal(item, false, seen));
    if (ts.isObjectLiteralExpression(node)) {
      return Object.fromEntries([...fields(node)].map(([key, value]) => [
        key,
        // This existing fixed-key template is recorded as source, never run.
        allowCopyright && key === 'copyright' && yearTemplate(value)
          ? resolve(value).getText(source) : literal(value, false, seen),
      ]));
    }
    fail();
  }
  for (const initializer of bindings.values()) passiveInitializer(initializer);
  passiveInitializer(exported);
  return {source, root: resolve(exported), resolve, fields, array, literal, yearTemplate};
}

function configuredMessages(site) {
  const config = staticModule(path.join(site, 'docusaurus.config.ts'));
  const root = config.fields(config.root);
  const theme = config.fields(root.get('themeConfig'));
  const navbar = config.literal(theme.get('navbar'));
  const footer = config.literal(theme.get('footer'), true);
  if (!navbar || !Array.isArray(navbar.items)) throw new Error('[ui-source] Static navbar items are required');
  const required = Object.fromEntries(catalogNames.map((name) => [name, {}]));
  for (const file of themeTranslationFiles({themeConfig: {navbar, footer}})) {
    const catalog = required[`docusaurus-theme-classic/${file.path}.json`];
    for (const [id, value] of Object.entries(file.content)) {
      catalog[id] = {message: value.message, input: {text: value.message}};
    }
  }
  if (footer) {
    const copyright = config.fields(theme.get('footer')).get('copyright');
    if (config.yearTemplate(copyright)) {
      required['docusaurus-theme-classic/footer.json'].copyright = {
        input: {expression: config.resolve(copyright).getText(config.source)},
      };
    }
  }

  let docs;
  if (root.has('presets')) {
    for (const entry of config.array(root.get('presets'))) {
      const preset = config.resolve(entry);
      if (!ts.isArrayLiteralExpression(preset)) continue;
      const parts = config.array(preset);
      if (['classic', '@docusaurus/preset-classic'].includes(config.literal(parts[0])) && parts[1]) {
        docs = config.fields(parts[1]).get('docs');
      }
    }
  }
  const options = docs && config.resolve(docs).kind !== ts.SyntaxKind.TrueKeyword
    ? config.fields(docs) : new Map();
  let versionLabel = 'Next';
  if (options.has('versions')) {
    const current = config.fields(options.get('versions')).get('current');
    const label = current && config.fields(current).get('label');
    if (label) versionLabel = config.literal(label);
  }
  if (typeof versionLabel !== 'string') throw new Error('[ui-source] Current version label must be static text');
  const sidebarName = options.has('sidebarPath') ? config.literal(options.get('sidebarPath')) : './sidebars.ts';
  if (typeof sidebarName !== 'string') throw new Error('[ui-source] A static sidebarPath is required');
  const sidebarPath = path.resolve(site, sidebarName);
  const relative = path.relative(fs.realpathSync(site), fs.realpathSync(sidebarPath));
  if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('[ui-source] sidebarPath must stay within the site');
  const sidebar = staticModule(sidebarPath);
  const sidebars = normalizeSidebars(sidebar.literal(sidebar.root));
  function checkItems(items) {
    for (const item of items) {
      if (!['category', 'doc', 'ref', 'link'].includes(item.type)) {
        throw new Error('[ui-source] Only static sidebar categories, docs, refs and links are supported');
      }
      if (item.type === 'category') checkItems(item.items);
    }
  }
  for (const items of Object.values(sidebars)) checkItems(items);
  for (const file of docsTranslationFiles({
    loadedVersions: [{versionName: 'current', label: versionLabel, sidebars}],
  })) {
    for (const [id, value] of Object.entries(file.content)) {
      required[`docusaurus-plugin-content-docs/${file.path}.json`][id] = {
        message: value.message, input: {text: value.message},
      };
    }
  }
  return required;
}

function checkCatalogs(site, errors) {
  const catalogs = {};
  for (const name of catalogNames) {
    try {
      const value = JSON.parse(read(path.join(site, 'i18n/ko', name)));
      if (!value || Array.isArray(value) || typeof value !== 'object' || !Object.keys(value).length) {
        throw new Error('Expected a nonempty message object');
      }
      catalogs[name] = value;
      for (const [id, entry] of Object.entries(value)) {
        if (!entry || typeof entry.message !== 'string' || !entry.message.trim()) {
          errors.push(`[catalog] ${name}: ${id} needs a nonempty string message`);
        }
      }
    } catch {
      errors.push(`[catalog] Missing, invalid or empty Korean catalog: ${name}`);
    }
  }
  const required = configuredMessages(site);
  const inputs = Object.fromEntries(catalogNames.map((name) => [name, new Map()]));
  function check(name, id, entry) {
    const translated = catalogs[name]?.[id]?.message;
    if (typeof translated !== 'string' || !translated.trim()) {
      errors.push(`[catalog] ${name} is missing required message ${id}`);
    } else if (entry.message !== undefined
        && !isDeepStrictEqual(placeholders(entry.message), placeholders(translated))) {
      errors.push(`[placeholder] ${name}: ${id} must preserve the source message placeholders`);
    }
    if (!inputs[name].has(id)) inputs[name].set(id, new Set());
    inputs[name].get(id).add(JSON.stringify(entry.input));
  }
  for (const [name, entries] of Object.entries(required)) {
    for (const [id, entry] of Object.entries(entries)) check(name, id, entry);
  }
  for (const entry of uiMessages(site)) check('code.json', entry.id, entry);
  return Object.fromEntries(Object.entries(inputs).map(([name, messages]) => [
    name, Object.fromEntries([...messages].sort(([a], [b]) => a.localeCompare(b))
      .map(([id, values]) => [id, hash(JSON.stringify([...values].sort()))])),
  ]));
}

function checkSite(site, record) {
  const docs = path.join(site, 'docs');
  const sources = filesUnder(docs, /\.mdx?$/);
  const translations = filesUnder(path.join(site, koDocs), /\.mdx?$/);
  const errors = [];
  if (!sources.length) errors.push('[coverage] No canonical guide pages found');
  const englishSet = new Set(sources);
  const koreanSet = new Set(translations);
  for (const file of sources) {
    if (!koreanSet.has(file)) errors.push(`[coverage] Missing Korean page: ${file}`);
    else compareDocuments(file, read(path.join(docs, file)), read(path.join(site, koDocs, file)), errors);
  }
  for (const file of translations) {
    if (!englishSet.has(file)) errors.push(`[coverage] Extra Korean page: ${file}`);
  }
  const ui = checkCatalogs(site, errors);
  if (errors.length) throw new Error(errors.join('\n'));

  const manifest = {
    schemaVersion: 1,
    files: Object.fromEntries(sources.map((file) => [file, hash(read(path.join(docs, file)))])),
    ui,
  };
  const destination = path.join(site, 'i18n/ko/source-hashes.json');
  if (record) {
    // No write occurs until every document and UI check has passed.
    const temporary = `${destination}.tmp-${process.pid}`;
    try {
      fs.writeFileSync(temporary, `${JSON.stringify(manifest, null, 2)}\n`);
      fs.renameSync(temporary, destination);
    } finally {
      fs.rmSync(temporary, {force: true});
    }
  } else {
    let previous;
    try {
      previous = JSON.parse(read(destination));
    } catch {
      throw new Error('[source-hashes] Missing or invalid manifest; review translations before --record.');
    }
    if (!isDeepStrictEqual(previous, manifest)) {
      throw new Error('[source-hashes] English guide/UI sources changed; review translations before --record.');
    }
  }
  console.log(`Guide locales: ${sources.length} English/Korean pairs and four catalogs checked${record ? '; hashes recorded' : ''}.`);
}

function main(args) {
  let site = path.resolve(__dirname, '..');
  let record = false;
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === '--record') record = true;
    else if (args[index] === '--site' && args[index + 1] && !args[index + 1].startsWith('--')) {
      site = path.resolve(args[++index]);
    } else {
      throw new Error('Usage: check-guide-locales.cjs [--site <directory>] [--record]');
    }
  }
  checkSite(site, record);
}

if (require.main === module) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
