/*
 * Flow scene: a sketched cutaway (cabinet projection) with a camera that moves between steps,
 * a glowing packet that follows real paths, numbered callouts on leader lines, small
 * line-art figures, and a side panel with the step title, code lines and checks.
 *
 * One scene is one plain data object (see references/scene-spec.md). The scene opens on the
 * full picture (step 0, so reduced motion and every slide entry show everything), then each Down
 * press or click on the stage plays the next step once and holds its end state; Up goes back.
 * PDF export runs no scripts, so a PDF shows the host's static fallback markup; mount() replaces it.
 *
 *   import('./common/line-art-scene/flowscene.js').then(m => m.mount('#scene', SPEC));
 *
 * Colours are deck role tokens only, so light and dark decks both work. Written for this
 * plugin; the idea of a stepped, hand-drawn cutaway was inspired by public line-art work.
 */
import { el, pen, blot, paint, limb, shoe, place, inkDefs, PEN, PAPER } from './ink.js';
import { gait } from './gait.js';
import { ease, clamp, spring, curve } from './motion.js';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const DEFAULT_HINT = 'Click the scene or press Down for the next step, Up for the previous step';

// The scene styles ship next to this module, so any deck that imports it gets them.
(function loadStyles() {
  const href = new URL('./flowscene.css', import.meta.url).href;
  const has = [].some.call(document.querySelectorAll('link[rel=stylesheet]'), l => l.href === href);
  if (has) return;
  const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = href; document.head.appendChild(l);
})();

// The framework object is a top-level const of the deck page, so find it lazily.
function findDeck() {
  try { if (typeof deck !== 'undefined' && deck && deck.registerSlideAction) return deck; } catch (e) { /* not defined yet */ }
  return window.deck && window.deck.registerSlideAction ? window.deck : null;
}

export function mount(sel, S) {
  const host = typeof sel === 'string' ? (document.querySelector('.slide-deck ' + sel) || document.querySelector(sel)) : sel;
  if (!host || host.dataset.fsMounted) return;
  host.dataset.fsMounted = '1';
  host.classList.add('fs');
  const uid = 'fs' + Math.random().toString(36).slice(2, 7);
  const slide = host.closest('.slide');

  // Build the markup unless the author supplied a .fs-stage; this replaces any static fallback.
  if (!host.querySelector('.fs-stage')) {
    host.innerHTML = '<div class="fs-stage"></div><div class="fs-side"><div class="fs-step"></div><div class="fs-title"></div>' +
      '<pre class="fs-code"></pre><div class="fs-checks"></div><div class="fs-say"></div><div class="fs-prog"><i></i></div>' +
      '<div class="fs-hint"></div></div>';
  }
  const stage = host.querySelector('.fs-stage');
  const hintEl = host.querySelector('.fs-hint'); if (hintEl && !hintEl.textContent) hintEl.textContent = S.hint || DEFAULT_HINT;

  const W = S.W || 900, H = S.H || 520, K = S.K || 30, OX = S.OX || 34, OY = S.OY || 380;
  // cabinet projection: x to the right, y into the screen (half depth), z up
  const pj = (x, y, z = 0) => [OX + x * K + y * K * 0.5, OY - y * K * 0.3 - z * K];
  const P = (...a) => a.map(p => pj(...p).map(v => v.toFixed(1)).join(',')).join(' ');

  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': S.aria || '' });
  stage.appendChild(svg);
  const { filter } = inkDefs(svg, uid);
  svg.style.color = 'var(--on-surface)';
  const defs = svg.querySelector('defs');
  const glowId = uid + '-glow';
  const glow = el('filter', { id: glowId, x: '-200%', y: '-200%', width: '500%', height: '500%' }, defs);
  el('feGaussianBlur', { stdDeviation: 3.2, result: 'b' }, glow);
  const merge = el('feMerge', {}, glow); el('feMergeNode', { in: 'b' }, merge); el('feMergeNode', { in: 'SourceGraphic' }, merge);
  const L0 = el('g', { filter }, svg), L1 = el('g', { filter }, svg), L2 = el('g', {}, svg), L3 = el('g', {}, svg);

  function box(parent, [x, y, z, w, d, h], cls = '') {
    const g = el('g', { class: 'fs-box ' + cls }, parent);
    el('polygon', { class: 'fs-face fs-front', points: P([x, y, z], [x + w, y, z], [x + w, y, z + h], [x, y, z + h]) }, g);
    el('polygon', { class: 'fs-face fs-side', points: P([x + w, y, z], [x + w, y + d, z], [x + w, y + d, z + h], [x + w, y, z + h]) }, g);
    el('polygon', { class: 'fs-face fs-top', points: P([x, y, z + h], [x + w, y, z + h], [x + w, y + d, z + h], [x, y + d, z + h]) }, g);
    return g;
  }
  const text = (parent, [x, y], s, cls = 'fs-lbl', anchor = 'middle') => {
    const t = el('text', { x: x.toFixed(1), y: y.toFixed(1), class: cls, 'text-anchor': anchor }, parent); t.textContent = s; return t;
  };
  const image = (parent, src, x, y, size) => {
    const im = el('image', { x: x.toFixed(1), y: y.toFixed(1), width: size, height: size, class: 'fs-awsicon' }, parent);
    im.setAttribute('href', src); return im;
  };

  // zones: ground slabs with a label and an optional icon (icon is a full URL, see scene-spec.md)
  (S.zones || []).forEach(z => {
    box(L0, z.box, 'fs-zone');
    if (!z.label) return;
    let [lx, ly] = pj(...z.labelAt);
    if (z.icon) { const sz = z.sub ? 16 : 20; image(L3, z.icon, lx, ly - sz + 4, sz); lx += sz + 5; }
    text(L3, [lx, ly], z.label, z.sub ? 'fs-sub' : 'fs-lbl', 'start');
  });

  // parts: boxes, clouds (ellipses), pipes and rings
  const parts = {};
  for (const id in (S.parts || {})) {
    const def = S.parts[id], g = el('g', { class: 'fs-part' }, L1);
    (def.boxes || []).forEach((b, i) => box(g, b, 'b' + i));
    (def.pipes || []).forEach(([a, b]) => {
      const A = pj(...a), B = pj(...b);
      el('path', { d: `M${A} L${B}`, class: 'fs-pipe-outer', 'stroke-width': 14, fill: 'none' }, g);
      el('path', { d: `M${A} L${B}`, class: 'fs-pipe-inner', 'stroke-width': 11, fill: 'none' }, g);
    });
    (def.clouds || []).forEach(([c, rx, ry, label]) => {
      const p = pj(...c); el('ellipse', { cx: p[0], cy: p[1], rx, ry, class: 'fs-face fs-top' }, g);
      if (label) text(g, [p[0], p[1] + 4], label);
    });
    (def.rings || []).forEach(([c, rx, ry]) => { const p = pj(...c); el('ellipse', { cx: p[0], cy: p[1], rx, ry, class: 'fs-ring' }, g); });
    parts[id] = g;
  }

  // icons standing on parts; they dim together with their part
  const partIcons = {};
  (S.icons || []).forEach(ic => {
    const g = el('g', { class: 'fs-icon' }, L3), sz = ic.size || 30, [x, y] = pj(...ic.at);
    image(g, ic.src, x - sz / 2, y - sz, sz);
    (partIcons[ic.part] = partIcons[ic.part] || []).push(g);
  });

  // marks (an X on a blocked path) and text tags (shown in chosen steps)
  const marks = {};
  (S.marks || []).forEach(m => {
    const g = el('g', { class: 'fs-mark', opacity: 0 }, L3), [x, y] = pj(...m.at);
    pen(g, 3).setAttribute('d', `M${x - 11} ${y - 11} L${x + 11} ${y + 11} M${x + 11} ${y - 11} L${x - 11} ${y + 11}`);
    marks[m.id] = g;
  });
  const tags = {};
  (S.tags || []).forEach(t => { tags[t.id] = text(L3, pj(...t.at), t.text, t.cls || 'fs-mono', t.anchor || 'middle'); });

  // wires: polylines through named waypoints; `at(i, j, u)` walks from waypoint i to j
  const wires = {};
  for (const id in (S.wires || {})) {
    const w = S.wires[id], pts = w.pts.map(p => pj(...p));
    const node = el('path', { d: 'M' + pts.map(p => p.map(v => v.toFixed(1)).join(' ')).join(' L'), class: 'fs-wire ' + (w.cls || '') }, L2);
    const cum = [0];
    for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const at = (i, j, u) => {
      const s = cum[i] + (cum[j] - cum[i]) * u; let k = 1;
      while (k < pts.length - 1 && cum[k] < s) k++;
      const r = (s - cum[k - 1]) / ((cum[k] - cum[k - 1]) || 1);
      return [pts[k - 1][0] + (pts[k][0] - pts[k - 1][0]) * r, pts[k - 1][1] + (pts[k][1] - pts[k - 1][1]) * r];
    };
    wires[id] = { node, at, n: pts.length, pts };
  }
  const dot = el('circle', { r: 6.5, class: 'fs-dot', filter: `url(#${glowId})` }, L3);

  // callouts: numbered boxes joined to a part by a leader line
  const calls = {};
  (S.callouts || []).forEach(c => {
    const g = el('g', { class: 'fs-call' }, L3), [ax, ay] = pj(...c.anchor), [bx, by] = c.at;
    el('path', { d: `M${ax.toFixed(1)} ${ay.toFixed(1)} L${bx} ${by}`, class: 'fs-leader' }, g);
    el('circle', { cx: ax.toFixed(1), cy: ay.toFixed(1), r: 2.6, class: 'fs-pin' }, g);
    const w = Math.max(c.title.length * (c.charW || 12.5), (c.sub || '').length * (c.subW || 6.4)) + 34;
    el('rect', { x: bx - 4, y: by - 15, width: w, height: c.sub ? 36 : 22, rx: 6, class: 'fs-callbox' }, g);
    const badge = el('g', { class: 'fs-badge' }, g);
    el('circle', { cx: bx + 8, cy: by - 4, r: 8 }, badge); text(badge, [bx + 8, by], String(c.n), 'fs-badge-n');
    text(g, [bx + 22, by + 0.5], c.title, 'fs-lbl', 'start');
    if (c.sub) text(g, [bx + 22, by + 15], c.sub, 'fs-sub', 'start');
    calls[c.id] = g;
  });

  // ---------- figures: small line-art people (stand, type, walk between points, raise a hand) ----------
  const figs = (S.figures || []).map(f => makeFigure(L3, f));
  function makeFigure(parent, f) {
    const g = el('g', { filter }, parent);
    const farArm = limb(g, 3.4), legs = [limb(g, 4), limb(g, 4)], shoes = [blot(g), blot(g)];
    const body = paint(g, f.colour || 'var(--accent)');
    const head = el('ellipse', { rx: 3.8, ry: 4.6, fill: PAPER, stroke: 'currentColor', 'stroke-width': PEN }, g);
    const nearArm = limb(g, 3.4);
    const walk = gait({ kind: f.gait || 'walk' }), raise = spring(30, 7), typeBlend = spring(40, 9);
    const tap = curve([[0, 0], [0.2, -2], [0.4, 0], [0.6, -1.6], [0.8, 0]], 1);
    // busy: head nods, hands drum, a sweat drop falls, optional sound word and code glyphs float up
    const fx = f.busy ? el('g', {}, g) : null;
    const sweat = fx ? el('path', { fill: 'var(--info)', stroke: 'currentColor', 'stroke-width': 0.8 }, fx) : null;
    const word = fx && f.sound ? el('text', { 'font-size': 6.5, fill: 'currentColor', 'text-anchor': 'middle', 'font-weight': 700 }, fx) : null;
    if (word) word.textContent = f.sound;
    const glyphs = fx ? (f.glyphs || ['{ }', '</>']).map(s => {
      const n = el('text', { 'font-size': 7, fill: 'var(--accent)', 'text-anchor': 'middle', 'font-weight': 700, 'font-family': 'var(--font-mono, monospace)' }, fx);
      n.textContent = s; return n;
    }) : [];
    let x = f.at[0], phase = 0;
    return {
      f, draw(t, dt, ph, act, calm) {
        // calm is reduced motion: no walk, no spring travel, no busy loop; the end pose is drawn at once
        if (calm) t = 0;
        const want = (f.goto && ph && f.goto[ph.key] != null) ? f.goto[ph.key] : f.at[0];
        if (calm) x = want;
        const moving = Math.abs(want - x) > 0.02;
        if (moving) { phase += dt / walk.period; x += Math.sign(want - x) * Math.min(Math.abs(want - x), walk.speed * 0.028 * dt); }
        const [sx, sy] = pj(x, f.at[1], f.at[2]);
        place(g, sx, sy, moving ? (want > x ? 1 : -1) : (f.dir || 1), f.scale || 0.9);
        const p = walk.pose(phase, moving ? 1 : 0);
        p.feet.forEach((fo, i) => { legs[i].draw([p.hip, fo.knee, fo.ankle], [0.3, 0.8]); shoe(shoes[i], fo.ankle, fo.pitch); });
        g.insertBefore(legs[p.front].g, body); g.insertBefore(shoes[p.front], body);
        const b = p.bob, typing = (f.pose === 'type' || act === 'type') ? 1 : 0, k = f.busy && !calm ? (act === 'type' ? 1 : 0.5) : 0;
        if (calm) { typeBlend.x = typing; typeBlend.v = 0; raise.x = act === 'raise' ? 1 : 0; raise.v = 0; }
        const tb = calm ? typeBlend.x : typeBlend.step(typing, dt), lean = 2 * k * tb, nod = k ? Math.sin(t * 7.5) * 0.9 * k : 0;
        body.setAttribute('d', `M35 ${42 + b} Q41 ${38.4 + b} 47 ${42 + b} L47.5 ${73 + b} Q40 ${76 + b} 32.5 ${73 + b}Z`);
        head.setAttribute('cx', 43 + lean); head.setAttribute('cy', 31.4 + b + nod);
        const r = calm ? raise.x : raise.step(act === 'raise' ? 1 : 0, dt);
        const tp = (k ? tap(t * (2.4 + 2.6 * k)) * 1.4 : tb ? tap(t * 2.2) : 0) * tb, tq = (k ? tap(t * (2.4 + 2.6 * k) + 0.4) * 1.4 : tp) * tb;
        const rest = [42, 72], desk = [60 + lean, 66 + tp + b];
        const handFar = [rest[0] + (desk[0] - rest[0]) * tb, rest[1] + b + (desk[1] - b - rest[1]) * tb];
        farArm.draw([[40 + lean * 0.5, 43 + b], [50 + lean * tb, 58 + b], handFar], [0.2, 0.5]);
        const handNear = [52 - 2 * r + (63 + lean - 52) * tb, 70 - 40 * r + b + ((65 - tq + b) - (70 + b)) * tb];
        nearArm.draw([[43 + lean * 0.5, 44 + b], [53 + lean - 4 * r, 61 - 16 * r + b], handNear], [0.2, 0.4]);
        if (fx) {
          const s = (t * 0.85) % 1, sx2 = 50 + lean, sy2 = 21 + s * 9 + b;
          sweat.setAttribute('d', `M${sx2} ${sy2 - 2.6} Q${sx2 + 1.9} ${sy2 + 0.4} ${sx2} ${sy2 + 1.4} Q${sx2 - 1.9} ${sy2 + 0.4} ${sx2} ${sy2 - 2.6}Z`);
          sweat.setAttribute('opacity', (k * (1 - s)).toFixed(2));
          if (word) { word.setAttribute('x', 70 + lean); word.setAttribute('y', 47 + b + Math.sin(t * 14) * 0.8); word.setAttribute('opacity', (k * (0.35 + 0.65 * Math.max(0, Math.sin(t * 5)))).toFixed(2)); }
          glyphs.forEach((n, i) => {
            const u = (t * 0.55 + i / glyphs.length) % 1;
            n.setAttribute('x', (86 + lean + i * 5 + Math.sin(t * 2 + i) * 1.5).toFixed(1)); n.setAttribute('y', (44 + b - u * 26).toFixed(1));
            n.setAttribute('opacity', (k * Math.sin(Math.PI * u)).toFixed(2));
          });
        }
      }
    };
  }

  // ---------- side panel ----------
  const $ = c => host.querySelector(c);
  const stepEl = $('.fs-step'), titleEl = $('.fs-title'), sayEl = $('.fs-say'), pre = $('.fs-code'), checksEl = $('.fs-checks');
  if (pre) pre.innerHTML = (S.code || []).map(l => `<span class="ln">${esc(l) || ' '}</span>`).join('');
  if (pre && !(S.code || []).length) pre.style.display = 'none';
  const lns = pre ? [...pre.querySelectorAll('.ln')] : [];
  if (checksEl) checksEl.innerHTML = (S.checks || []).map(c => `<div><i></i>${esc(c)}</div>`).join('');
  const chk = checksEl ? [...checksEl.children] : [];
  const prog = $('.fs-prog i');

  // ---------- camera frames ----------
  function frameOf(ids, minW) {
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    const add = n => { const b = n.getBBox(); if (!b.width && !b.height) return; x0 = Math.min(x0, b.x); y0 = Math.min(y0, b.y); x1 = Math.max(x1, b.x + b.width); y1 = Math.max(y1, b.y + b.height); };
    if (!ids) { add(L0); add(L1); add(L2); add(L3); }
    else ids.forEach(id => { if (parts[id]) add(parts[id]); if (calls[id]) add(calls[id]); if (tags[id]) add(tags[id]); });
    if (x0 > x1) return [0, 0, W, H];
    const pad = ids ? 46 : 18; x0 -= pad; y0 -= pad; x1 += pad; y1 += pad;
    let w = x1 - x0, h = y1 - y0; const r = W / H;
    if (w / h < r) { const nw = h * r; x0 -= (nw - w) / 2; w = nw; } else { const nh = w / r; y0 -= (nh - h) / 2; h = nh; }
    if (ids) { const cx = x0 + w / 2, cy = y0 + h / 2; w = Math.max(w, W * (minW || 0.26)); h = w / r; x0 = cx - w / 2; y0 = cy - h / 2; }
    return [x0, y0, w, h];
  }
  let OVER = frameOf(null);
  const ov = S.overview || {};
  const PH = [{ key: 'all', d: S.hold || 2.6, label: ov.label, title: ov.title, say: ov.say, lines: ov.lines || [], all: true }]
    .concat((S.phases || []).map((p, i) => Object.assign({ key: p.key || ('p' + (i + 1)), d: 3 }, p)));
  function segmentPoints(ph) {
    const pk = ph.packet; if (!pk || !wires[pk.wire]) return null;
    const w = wires[pk.wire], [a, b] = pk.span || [0, w.n - 1];
    return w.pts.slice(Math.min(a, b), Math.max(a, b) + 1);
  }
  function computeFrames() {
    OVER = frameOf(null);
    PH.forEach(ph => {
      if (ph.all) { ph.frame = OVER; return; }
      const base = frameOf(ph.cam || ph.focus, ph.zoom), seg = segmentPoints(ph);
      if (!seg || ph.segment === false) { ph.frame = base; return; }
      let [x0, y0, w, h] = base, x1 = x0 + w, y1 = y0 + h; const pad = 40;   // grow so the whole packet path fits
      seg.forEach(([x, y]) => { x0 = Math.min(x0, x - pad); y0 = Math.min(y0, y - pad); x1 = Math.max(x1, x + pad); y1 = Math.max(y1, y + pad); });
      w = x1 - x0; h = y1 - y0; const r = W / H;
      if (w / h < r) { const nw = h * r; x0 -= (nw - w) / 2; w = nw; } else { const nh = w / r; y0 -= (nh - h) / 2; h = nh; }
      ph.frame = [x0, y0, w, h];
    });
  }
  computeFrames();
  let framesReady = svg.getBBox().width > 0;
  const CYCLE = PH.reduce((a, p) => a + p.d, 0);
  let cam = OVER.slice();
  let camStep = -1, camFrom = cam.slice();   // step the camera last eased toward, and where it started
  svg.setAttribute('viewBox', OVER.map(v => v.toFixed(1)).join(' '));

  let cur = -1;
  function enter(i) {
    if (i === cur) return; cur = i; const ph = PH[i];
    if (stepEl) stepEl.textContent = ph.label || '';
    if (titleEl) titleEl.textContent = ph.title || '';
    if (sayEl) sayEl.innerHTML = ph.say || '';
    lns.forEach((ln, k) => ln.classList.toggle('on', (ph.all ? (ov.lines || lns.map((_, j) => j + 1)) : (ph.lines || [])).includes(k + 1)));
    for (const id in parts) {
      const on = ph.all || (ph.focus || []).includes(id);
      parts[id].classList.toggle('dim', !on); parts[id].classList.toggle('on', !ph.all && !!ph.focus && ph.focus[0] === id);
      (partIcons[id] || []).forEach(g => g.classList.toggle('dim', !on));
    }
    for (const id in calls) { calls[id].classList.toggle('dim', !(ph.all || ph.badge === id)); calls[id].classList.toggle('on', ph.badge === id); }
    for (const id in wires) wires[id].node.classList.toggle('on', ph.all ? !wires[id].node.classList.contains('fs-alt') : !!(ph.packet && ph.packet.wire === id));
    if (checksEl) checksEl.classList.toggle('dim', !(ph.checks || ph.all));
  }

  // ---------- stepping ----------
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const STEP = S.mode !== 'auto';   // 'auto' plays the phases as one looping film instead
  let clock = 0, paused = false, last = 0, idx = 0, phaseStart = 0;
  let loop = null;
  // A step change draws at once: the presenter window mirrors this slide's DOM and a deck window
  // behind it may get no animation frames until focused.
  const go = n => {
    idx = Math.max(0, Math.min(PH.length - 1, n)); phaseStart = performance.now();
    if (loop && loop.drawNow) loop.drawNow(); else draw(performance.now());
  };
  const notify = () => { const d = findDeck(); if (d && d.notifyStepChange) d.notifyStepChange(); };
  stage.addEventListener('click', () => {
    if (!STEP) { paused = !paused; return; }
    go(idx < PH.length - 1 ? idx + 1 : 0); notify();
  });
  const handlers = {
    down: () => { if (idx < PH.length - 1) { go(idx + 1); return true; } return false; },
    up: () => { if (idx > 0) { go(idx - 1); return true; } return false; },
    state: () => ({ cur: idx, total: PH.length - 1 })       // step 0 is the overview, so cur matches the labels
  };
  const myIndex = () => Array.from(document.querySelectorAll('.slide-deck .slide')).indexOf(slide);
  if (STEP) {
    // standalone preview (no deck on the page): drive the scene with the arrow keys
    const bindKeys = () => document.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' && handlers.down()) e.preventDefault();
      if (e.key === 'ArrowUp' && handlers.up()) e.preventDefault();
    });
    let tries = 0;
    const attach = () => {
      const d = findDeck();
      if (d) { d.registerSlideAction(myIndex(), handlers); return; }
      if (++tries < 60) { setTimeout(attach, 50); return; }   // the deck object is created after the page body
      bindKeys();
    };
    if (document.querySelector('.slide-deck')) attach(); else bindKeys();
  }
  // `.active` is added about 350 ms after rp:slidechange, so match the event's slide index
  document.addEventListener('rp:slidechange', e => {
    if (e.detail && e.detail.index === myIndex()) { clock = 0; paused = false; go(0); }
  });
  const active = () => !slide || slide.classList.contains('active');

  function draw(now) {
    // real elapsed time, so a sparse frame rate never slows the scene; dt only feeds the smoothing
    const dt = Math.min(0.5, last ? Math.max(0, now - last) / 1000 : 0); last = now;
    if (!active()) return;
    // the slide may have been hidden when the scene mounted (getBBox is 0 then): measure now
    if (!framesReady && svg.getBBox().width > 0) { computeFrames(); framesReady = true; cam = OVER.slice(); camStep = -1; }
    let i, s;
    if (STEP) { i = idx; s = still ? PH[i].d : Math.min((now - phaseStart) / 1000, PH[i].d); }  // reduced motion: end state at once
    else {
      if (!paused && !still) clock += dt;
      s = still ? 0 : clock % CYCLE; i = 0;
      while (s >= PH[i].d) { s -= PH[i].d; i++; }
    }
    enter(i);
    const ph = PH[i], lead = (STEP && !ph.all) ? (ph.lead != null ? ph.lead : 0.9) : 0;
    const u = clamp((s - lead) / Math.max(0.1, ph.d - lead), 0, 1), t = now / 1000;
    if (prog) prog.style.width = (STEP ? (i / (PH.length - 1)) * 100 : ((clock % CYCLE) / CYCLE) * 100).toFixed(1) + '%';

    // the packet travels along a wire during the step
    let q = null, colour = 'var(--accent)';
    const pk = ph.packet;
    if (pk && wires[pk.wire]) {
      const w = wires[pk.wire], [a, b] = pk.span || [0, w.n - 1];
      const stopAt = pk.stopAt || 0.6, holdAt = pk.hold || 0.8, waitAt = pk.waitAt || 0.5;
      if (pk.mode === 'pingpong') q = u < 0.5 ? w.at(a, b, ease(u / 0.5)) : w.at(b, a, ease((u - 0.5) / 0.5));
      else if (pk.mode === 'wait') q = w.at(a, b, u < holdAt ? waitAt : waitAt + (1 - waitAt) * ease((u - holdAt) / (1 - holdAt)));
      else if (pk.mode === 'block') q = w.at(a, b, ease(clamp(u / stopAt, 0, 1)));
      else q = w.at(a, b, ease(u));
      colour = pk.mode === 'block' && u > stopAt ? 'var(--danger)' : (pk.colour || colour);
    }
    if (q) { dot.setAttribute('cx', q[0].toFixed(1)); dot.setAttribute('cy', q[1].toFixed(1)); dot.style.fill = colour; dot.style.opacity = 1; }
    else dot.style.opacity = 0;

    for (const id in marks) marks[id].setAttribute('opacity', ph.all || (pk && pk.mode === 'block' && pk.mark === id && u > (pk.stopAt || 0.6)) ? 1 : 0);
    (S.tags || []).forEach(td => { tags[td.id].style.opacity = (ph.all && td.overview !== false) || (td.show || []).includes(ph.key) ? 1 : 0; });

    // sequential checks (for example a policy evaluation) light up during the step
    const lit = ph.checks ? Math.floor(clamp(u / (pk && pk.hold || 0.8), 0, 1) * (chk.length + 0.0001))
      : (ph.all || (S.checksDoneAfter && PH.findIndex(p => p.key === S.checksDoneAfter) < i) ? chk.length : 0);
    chk.forEach((c, k) => c.classList.toggle('ok', k < lit));
    if (S.frame) S.frame({ parts, marks, tags, wires, svg, lit, ph, u, t, all: !!ph.all });

    figs.forEach(fg => fg.draw(t, Math.min(dt, 0.05), ph, (fg.f.act || {})[ph.key] || null, still));

    if (still) svg.setAttribute('viewBox', ((STEP && ph.frame) || OVER).map(v => v.toFixed(1)).join(' '));
    else if (STEP) {
      // the camera eases to the step's frame during the lead and is exactly there when the packet
      // starts, so it never moves while the packet travels (the overview eases for up to 0.9 s)
      if (camStep !== i) { camStep = i; camFrom = cam.slice(); }
      const camT = Math.min(ph.all ? 0.9 : lead, ph.d), c = camT > 0 ? ease(clamp(s / camT, 0, 1)) : 1;
      cam = camFrom.map((v, j) => v + (ph.frame[j] - v) * c);
      svg.setAttribute('viewBox', cam.map(v => v.toFixed(1)).join(' '));
    } else {
      // auto mode (a looping film) keeps the exponential follow
      const k = 1 - Math.exp(-dt * 4.2);
      cam = cam.map((v, j) => v + (ph.frame[j] - v) * k);
      svg.setAttribute('viewBox', cam.map(v => v.toFixed(1)).join(' '));
    }
  }

  // Prefer the framework's AnimationLoop (it redraws on demand and has a timer fallback);
  // draw on a plain rAF plus timer when the scene runs outside a deck.
  if (typeof AnimationLoop !== 'undefined') {
    loop = new AnimationLoop(() => draw(performance.now()));
    loop.start();
  } else {
    let lastDraw = 0;
    const tick = () => { requestAnimationFrame(tick); lastDraw = performance.now(); draw(lastDraw); };
    requestAnimationFrame(tick);
    setInterval(() => { if (performance.now() - lastDraw > 150) { lastDraw = performance.now(); draw(lastDraw); } }, 100);
  }
  return { go, handlers };
}
