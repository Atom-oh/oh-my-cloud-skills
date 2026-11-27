const { test } = require('node:test');
const assert = require('node:assert/strict');
const { renderPreview } = require('./preview-fixture.cjs');

function dimensions(frontmatter) {
    const html = renderPreview(`---\nremarp: true\n${frontmatter}\n---\n# Geometry\n`);
    const wrapper = html.match(/\.slide-wrapper\s*\{([^}]+)\}/)?.[1];
    assert.ok(wrapper, 'Preview must render its design wrapper');
    return [Number(wrapper.match(/\bwidth:\s*([\d.]+)px/)[1]),
        Number(wrapper.match(/\bheight:\s*([\d.]+)px/)[1])];
}

for (const [name, source, expected] of [
    ['default', '', [1280, 720]],
    ['16:9', 'ratio: "16:9"', [1280, 720]],
    ['4:3', 'ratio: 4:3', [960, 720]],
    ['21:9', 'ratio: "21:9"', [1280, 1280 * 9 / 21]],
    ['portrait', 'ratio: "9:16"', [405, 720]],
    ['single quoted with whitespace', "ratio: ' 4 : 3 '", [960, 720]],
    ['equivalent ratio', 'ratio: 1920:1080', [1280, 720]],
    ['size precedence', 'size: 960x720\nratio: 16:9', [960, 720]],
    ['single quoted size', "size: '800x600'", [800, 600]],
    ['lower size bound', 'size: 1x1', [1, 1]],
    ['upper size bound', 'size: 16384x16384', [16384, 16384]],
    ['invalid size with valid ratio', 'size: 0x720\nratio: 4:3', [960, 720]],
    ['oversized size with valid ratio', 'size: 16385x720\nratio: 4:3', [960, 720]],
    ['CRLF', 'ratio: "4:3"\r', [960, 720]],
]) {
    test(`Preview dimensions: ${name}`, () => {
        const actual = dimensions(source);
        expected.forEach((value, index) => assert.ok(Math.abs(actual[index] - value) < 1e-8, `${actual} != ${expected}`));
    });
}

for (const source of [
    'size: 0x720', 'size: 1280x0', 'size: -1x720', 'size: 1280.5x720',
    'size: 1280x16385', `size: ${'9'.repeat(400)}x720`,
    'ratio: 0:9', 'ratio: 16:0', 'ratio: -4:3', 'ratio: 4:3junk',
    'ratio: 1.5:1', 'ratio: NaN:9', 'ratio: Infinity:9',
    'ratio: 9007199254740993:1', `ratio: ${'9'.repeat(400)}:9`,
    'ratio: 16384:1', 'ratio: 1:16384', 'size: 0x0\nratio: 0:0',
]) {
    test(`Preview invalid dimensions safely fall back: ${source.slice(0, 60)}`, () => {
        assert.deepEqual(dimensions(source), [1280, 720]);
    });
}
