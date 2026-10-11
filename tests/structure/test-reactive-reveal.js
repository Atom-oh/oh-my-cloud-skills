// Dependency-free behavioral coverage of the browser export final-state preparation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '../..');
const source = fs.readFileSync(path.join(root,
  'plugins/aws-content-plugin/skills/reactive-presentation/assets/export-utils.js'), 'utf8');
const context = vm.createContext({});
vm.runInContext(source, context);
const complete = vm.runInContext('ExportUtils._completeAllAnimations', context);

const styles = new Map();
const operations = [];
const fragments = [0, 1].map(() => ({
  classList: {add(name) {
    assert.ok(styles.has('reactive-export-final-state'),
      'CSS motion must be frozen before delayed children are revealed');
    assert.equal(name, 'visible');
    operations.push('reveal');
  }},
}));
let canvasStep = 0;
const slides = [{
  dataset: {canvasMaxStep: '8'}, style: {},
  __canvasStep() { canvasStep += 1; return canvasStep < 3; },
}, {dataset: {}, style: {}}];
const document = {
  getElementById(id) { return styles.get(id); },
  createElement(name) { assert.equal(name, 'style'); return {}; },
  head: {appendChild(style) { styles.set(style.id, style); operations.push('freeze'); }},
  querySelectorAll(selector) {
    if (selector === '.fragment') return fragments;
    if (selector === '.slide') return slides;
    throw new Error(`Unexpected capture selector: ${selector}`);
  },
};

complete(document);
assert.deepEqual(operations.slice(0, 3), ['freeze', 'reveal', 'reveal']);
const css = styles.get('reactive-export-final-state').textContent;
assert.match(css, /animation:\s*none\s*!important/);
assert.match(css, /transition:\s*none\s*!important/);
assert.match(css, /\[data-reveal="stagger"\]\s*>\s*\*\s*\{[^}]*opacity:\s*1\s*!important/);
assert.match(css, /\[data-reveal="stagger"\]\s*>\s*\*\s*\{[^}]*transform:\s*none\s*!important/);
assert.equal(canvasStep, 3, 'capture still advances canvas to its final step');
for (const slide of slides) {
  assert.equal(slide.style.display, 'flex');
  assert.equal(slide.style.opacity, '1');
  assert.equal(slide.style.transform, 'none');
}
complete(document);
assert.equal(styles.size, 1, 'repeated capture preparation does not duplicate freeze styles');
console.log('Browser export freezes delayed reveal groups before capture and retains canvas completion');
