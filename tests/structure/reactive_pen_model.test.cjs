'use strict';
// Unit tests for the pure ink model and renderer in deck-pen.js.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SRC = path.join(__dirname, '..', '..', 'plugins', 'aws-content-plugin',
  'skills', 'reactive-presentation', 'assets', 'deck-pen.js');

function load() {
  const window = {};
  vm.runInNewContext(fs.readFileSync(SRC, 'utf8'), { window, console });
  return window.DeckPen;
}

function setup(fadeMs) {
  const DeckPen = load();
  const clock = { t: 0 };
  const model = DeckPen.createModel({ fadeMs: fadeMs || 3000, now: () => clock.t });
  return { DeckPen, clock, model };
}

function draw(model, slide, pts) {
  model.begin(slide, pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) model.extend(pts[i][0], pts[i][1]);
  model.end();
}

test('test_laser_points_fade_and_expire', () => {
  const { clock, model } = setup(3000);
  model.setMode('laser');
  draw(model, 0, [[0.1, 0.1], [0.2, 0.2]]);
  assert.equal(model.visible(0)[0].points[0].alpha, 1);
  clock.t = 1500;
  assert.equal(model.visible(0)[0].points[0].alpha, 0.5);
  clock.t = 3000;
  assert.equal(model.visible(0).length, 0);
});

test('test_persistent_strokes_never_expire', () => {
  const { clock, model } = setup(3000);
  model.setMode('pen');
  draw(model, 0, [[0.1, 0.1], [0.2, 0.2]]);
  clock.t = 10 * 60 * 1000;
  const v = model.visible(0);
  assert.equal(v.length, 1);
  assert.ok(v[0].points.every((p) => p.alpha === 1));
});

test('test_show_slide_drops_laser_keeps_pen_per_slide', () => {
  const { model } = setup(3000);
  model.setMode('pen');
  draw(model, 0, [[0.1, 0.1], [0.2, 0.2]]);
  model.setMode('laser');
  draw(model, 0, [[0.3, 0.3], [0.4, 0.4]]);
  model.showSlide(1);
  assert.equal(model.visible(1).length, 0);
  model.showSlide(0);
  const v = model.visible(0);
  assert.equal(v.length, 1);
  assert.equal(v[0].mode, 'pen');
});

test('test_erase_removes_whole_stroke_under_pointer_only', () => {
  const { model } = setup(3000);
  model.setMode('pen');
  draw(model, 0, [[0.1, 0.1], [0.5, 0.1]]);
  draw(model, 0, [[0.1, 0.8], [0.5, 0.8]]);
  assert.equal(model.eraseAt(0, 0.3, 0.105), 1);
  const v = model.visible(0);
  assert.equal(v.length, 1);
  assert.equal(v[0].points[0].y, 0.8);
  assert.equal(model.eraseAt(0, 0.9, 0.9), 0);
});

test('test_clear_only_affects_the_given_slide', () => {
  const { model } = setup(3000);
  model.setMode('pen');
  draw(model, 0, [[0.1, 0.1], [0.2, 0.2]]);
  draw(model, 1, [[0.1, 0.1], [0.2, 0.2]]);
  model.clear(0);
  assert.equal(model.visible(0).length, 0);
  assert.equal(model.visible(1).length, 1);
});

test('test_invalid_size_color_mode_are_ignored', () => {
  const { model } = setup(3000);
  model.setMode('pen');
  model.setSize(2);
  model.setColor(3);
  model.setMode('bogus');
  model.setSize(9);
  model.setSize('x');
  model.setColor(-1);
  model.setColor(6);
  model.setColor(1.5);
  assert.equal(model.mode, 'pen');
  assert.equal(model.size, 2);
  assert.equal(model.colorIndex, 3);
});

test('test_highlighter_defaults_to_yellow', () => {
  const { DeckPen, model } = setup(3000);
  model.setMode('highlighter');
  draw(model, 0, [[0.1, 0.1], [0.2, 0.2]]);
  assert.equal(DeckPen.PALETTE[model.visible(0)[0].colorIndex], '#fdd835');
  model.setColor(3);
  draw(model, 0, [[0.1, 0.5], [0.2, 0.5]]);
  assert.equal(model.visible(0)[1].colorIndex, 3);
});

test('test_colour_is_remembered_per_mode', () => {
  const { model } = setup(3000);
  model.setMode('pen');
  model.setColor(3);
  model.setMode('highlighter');
  assert.equal(model.effectiveColor(), 1);
  model.setColor(2);
  model.setMode('pen');
  assert.equal(model.effectiveColor(), 3);
  model.setMode('laser');
  assert.equal(model.effectiveColor(), 0);
  model.setColor(5);
  model.setMode('highlighter');
  assert.equal(model.effectiveColor(), 2);
  model.setMode('pen');
  assert.equal(model.effectiveColor(), 3);
  // Eraser: setColor is a no-op and leaves every mode's colour alone.
  model.setMode('eraser');
  model.setColor(4);
  model.setMode('pen');
  assert.equal(model.effectiveColor(), 3);
  model.setMode('laser');
  assert.equal(model.effectiveColor(), 5);
});

test('test_render_loop_stops_when_idle', () => {
  const { clock, model } = setup(3000);
  assert.equal(model.animating(0), false);
  model.setMode('laser');
  model.begin(0, 0.1, 0.1);
  assert.equal(model.animating(0), true);
  model.extend(0.2, 0.2);
  model.end();
  assert.equal(model.animating(0), true);
  clock.t = 3000;
  assert.equal(model.animating(0), false);
});

test('test_render_scales_width_with_canvas', () => {
  const { DeckPen, model } = setup(3000);
  model.setMode('pen');
  model.setSize(2);
  draw(model, 0, [[0.1, 0.1], [0.2, 0.2]]);
  const widths = [];
  const ctx = {
    clearRect() {}, beginPath() {}, moveTo() {}, lineTo() {}, stroke() {},
    save() {}, restore() {},
    set lineWidth(v) { widths.push(v); },
  };
  DeckPen.render(ctx, 1920, 1080, model.visible(0));
  DeckPen.render(ctx, 960, 540, model.visible(0));
  assert.equal(widths[0], 8);
  assert.equal(widths[widths.length - 1], 4);
});

test('test_begin_in_eraser_mode_creates_no_stroke', () => {
  const { model } = setup(3000);
  model.setMode('eraser');
  assert.equal(model.begin(0, 0.1, 0.1), null);
  assert.doesNotThrow(() => { model.extend(0.2, 0.2); model.end(); });
  assert.equal(model.visible(0).length, 0);
  assert.equal(model.animating(0), false);
});

test('test_erase_aspect_makes_the_hit_area_round_in_pixels', () => {
  const { model } = setup(3000);
  model.setMode('pen');
  // A vertical stroke at x = 0.5. On a 16:9 slide 0.02 of the height is
  // 0.01125 of the width, so a point 0.015 to the side is outside the circle.
  draw(model, 0, [[0.5, 0.1], [0.5, 0.9]]);
  assert.equal(model.eraseAt(0, 0.515, 0.5, 0.02, 16 / 9), 0);
  assert.equal(model.eraseAt(0, 0.51, 0.5, 0.02, 16 / 9), 1);
  // Without an aspect the radius stays per-axis, as before.
  draw(model, 0, [[0.5, 0.1], [0.5, 0.9]]);
  assert.equal(model.eraseAt(0, 0.515, 0.5, 0.02), 1);
});

test('test_effective_color_follows_the_current_mode', () => {
  const { model } = setup(3000);
  assert.equal(model.effectiveColor(), 0);
  model.setMode('highlighter');
  assert.equal(model.effectiveColor(), 1);
  model.setColor(3);
  assert.equal(model.effectiveColor(), 3);
  model.setMode('pen');
  assert.equal(model.effectiveColor(), 0);
});

test('test_controller_is_not_created_without_the_overlay_core', () => {
  const DeckPen = load();
  assert.equal(DeckPen.controller, null);
  assert.equal(typeof DeckPen.attachSurface, 'function');
});
