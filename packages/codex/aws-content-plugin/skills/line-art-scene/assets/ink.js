/*
 * Ink helpers: draw everything with one thin pen on paper, built live as SVG.
 * No dependencies. Ink is `currentColor`, paper is the deck's `--surface-1`, so a theme
 * switch retints the whole drawing. Written for this plugin.
 */

export const NS = 'http://www.w3.org/2000/svg';
export const PEN = 1.5;
export const PAPER = 'var(--surface-1)';

/** Create an SVG element, set attributes, optionally append it to `parent`. */
export function el(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}

/**
 * Add the shared hand-drawn wobble filter to an svg and return its `url(#...)` reference.
 * Apply it to groups of strokes, never to text.
 */
export function inkDefs(svg, id = 'lac') {
  let defs = svg.querySelector('defs');
  if (!defs) defs = el('defs', {}, svg);
  const f = el('filter', { id: id + '-ink', x: '-3%', y: '-3%', width: '106%', height: '106%' }, defs);
  el('feTurbulence', { type: 'fractalNoise', baseFrequency: 0.03, numOctaves: 2, seed: 4, result: 'n' }, f);
  el('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale: 1.8, xChannelSelector: 'R', yChannelSelector: 'G' }, f);
  return { filter: `url(#${id}-ink)` };
}

/** An empty pen stroke; set its `d` attribute yourself. */
export function pen(parent, width = PEN) {
  return el('path', { fill: 'none', stroke: 'currentColor', 'stroke-width': width, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, parent);
}

/** A small solid ink blob (shoes, dots). */
export function blot(parent) {
  return el('path', { fill: 'currentColor', stroke: 'none' }, parent);
}

/** A closed shape filled with a flat colour and outlined with the pen. */
export function paint(parent, fill = PAPER, width = PEN) {
  return el('path', { fill, stroke: 'currentColor', 'stroke-width': width, 'stroke-linejoin': 'round' }, parent);
}

/** Smooth quadratic path through three points, sampled to `n + 1` points. */
function sample(a, b, c, n) {
  const out = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, m = 1 - t;
    out.push([m * m * a[0] + 2 * m * t * b[0] + t * t * c[0], m * m * a[1] + 2 * m * t * b[1] + t * t * c[1]]);
  }
  return out;
}

/**
 * A limb: a paper coloured band between two open pen lines. The lines stop short of each
 * other at the far end, which is the signature of the style. `draw([a, b, c], [startFrac, endFrac])`
 * sets the three joints (shoulder, elbow, hand or hip, knee, ankle).
 */
export function limb(parent, width = 4) {
  const g = el('g', {}, parent);
  const band = el('path', { fill: PAPER, stroke: 'none' }, g);
  const l1 = pen(g), l2 = pen(g);
  return {
    g,
    draw(pts, ends = [0.2, 0.8]) {
      const P = sample(pts[0], pts[1], pts[2], 10), h = width / 2;
      const left = [], right = [];
      P.forEach((p, i) => {
        const q = P[Math.min(i + 1, P.length - 1)], r = P[Math.max(i - 1, 0)];
        let dx = q[0] - r[0], dy = q[1] - r[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
        left.push([p[0] - dy * h, p[1] + dx * h]); right.push([p[0] + dy * h, p[1] - dx * h]);
      });
      const f = p => p[0].toFixed(1) + ' ' + p[1].toFixed(1);
      band.setAttribute('d', 'M' + left.map(f).join(' L') + ' L' + right.slice().reverse().map(f).join(' L') + 'Z');
      const cut = (A, a, b) => A.slice(Math.floor(a * (A.length - 1)), Math.ceil(b * (A.length - 1)) + 1);
      l1.setAttribute('d', 'M' + cut(left, 0, ends[1]).map(f).join(' L'));
      l2.setAttribute('d', 'M' + cut(right, ends[0], 1).map(f).join(' L'));
    }
  };
}

/** Draw a shoe blot at an ankle with a pitch in degrees. */
export function shoe(node, ankle, pitch = 0) {
  const [x, y] = ankle;
  node.setAttribute('d', `M${x - 3} ${y} Q${x - 3} ${y + 3.4} ${x + 1} ${y + 3.4} L${x + 6.5} ${y + 3.4} Q${x + 8} ${y + 3.4} ${x + 6.2} ${y + 1.4} Q${x + 3} ${y - 1.2} ${x + 1} ${y - 2.4}Z`);
  node.setAttribute('transform', `rotate(${pitch} ${x} ${y})`);
}

/**
 * Place a figure drawn in its own space (about 95 units tall, feet on y = 120, standing at
 * x = 40, facing +x) at a scene point. `dir` is 1 or -1, `scale` a number.
 */
export function place(g, x, y, dir = 1, scale = 1) {
  g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${(dir * scale).toFixed(3)} ${scale}) translate(-40 -120)`);
}

export const DEFAULT_ACCENT = 'var(--accent)';
