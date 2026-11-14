import {test} from 'node:test';
import assert from 'node:assert/strict';
import {guideText} from '../guide-text.mjs';

test('retrieval preserves fenced and inline syntax while removing MDX presentation markup', () => {
  const source = [
    '---', 'title: Syntax', '---', "import Demo from './Demo';",
    '<Demo title="Example" />', 'Use `<id>` and ``<label> with `ticks` ``.',
    '{/* maintained wrapper note */}', '````md', '```canvas',
    'box <id> "<label>" at <x>,<y>', '<Demo />', '```', '````',
    '~~~js', 'import example from "<module>";', '~~~',
    '<strong>Visible explanation</strong>',
  ].join('\n');
  const text = guideText(source);
  assert.ok(text.includes('`<id>`'));
  assert.ok(text.includes('``<label> with `ticks` ``'));
  assert.ok(text.includes('box <id> "<label>" at <x>,<y>'));
  assert.ok(text.includes('<Demo />'));
  assert.ok(text.includes('import example from "<module>";'));
  assert.ok(text.includes('Visible explanation'));
  assert.doesNotMatch(text, /title: Syntax|import Demo|maintained wrapper note|<strong>|title="Example"/);
});
