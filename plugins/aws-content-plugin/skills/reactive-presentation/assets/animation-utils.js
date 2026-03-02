/**
 * Reactive Presentation - Canvas/SVG Animation Utilities
 */

/* ── Color Helpers ── */
const Colors = {
  bg:        '#0f1117',
  bgSecond:  '#1a1d2e',
  surface:   '#282d45',
  border:    '#2d3250',
  accent:    '#6c5ce7',
  accentLt:  '#a29bfe',
  green:     '#00b894',
  yellow:    '#fdcb6e',
  red:       '#e17055',
  blue:      '#74b9ff',
  cyan:      '#00cec9',
  pink:      '#fd79a8',
  orange:    '#f39c12',
  textPri:   '#e8eaf0',
  textSec:   '#9ba1b8',
  textMuted: '#6b7194',
};

/* ── Canvas Setup ── */
function setupCanvas(canvasId, width, height) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  const dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = '100%';
  canvas.style.maxWidth = width + 'px';
  canvas.style.height = 'auto';
  canvas.style.aspectRatio = width + '/' + height;
  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  return { canvas, ctx, width, height };
}

/* ── Drawing Primitives ── */
function drawRoundRect(ctx, x, y, w, h, r, fill, stroke) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.stroke(); }
}

function drawBox(ctx, x, y, w, h, label, color, textColor) {
  drawRoundRect(ctx, x, y, w, h, 8, color + '22', color);
  ctx.fillStyle = textColor || Colors.textPri;
  ctx.font = '600 13px Pretendard, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // Word wrap for long labels
  const words = label.split(' ');
  const maxWidth = w - 12;
  let lines = [];
  let currentLine = words[0];

  for (let i = 1; i < words.length; i++) {
    const test = currentLine + ' ' + words[i];
    if (ctx.measureText(test).width < maxWidth) {
      currentLine = test;
    } else {
      lines.push(currentLine);
      currentLine = words[i];
    }
  }
  lines.push(currentLine);

  const lineHeight = 16;
  const startY = y + h / 2 - (lines.length - 1) * lineHeight / 2;
  lines.forEach((line, i) => {
    ctx.fillText(line, x + w / 2, startY + i * lineHeight);
  });
}

function drawArrow(ctx, x1, y1, x2, y2, color, dashed) {
  ctx.beginPath();
  if (dashed) ctx.setLineDash([6, 4]);
  else ctx.setLineDash([]);
  ctx.strokeStyle = color || Colors.accent;
  ctx.lineWidth = 2;
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.setLineDash([]);

  // Arrowhead
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const headLen = 10;
  ctx.beginPath();
  ctx.fillStyle = color || Colors.accent;
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - headLen * Math.cos(angle - Math.PI / 6), y2 - headLen * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(x2 - headLen * Math.cos(angle + Math.PI / 6), y2 - headLen * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

function drawCircle(ctx, x, y, r, fill, stroke) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 2; ctx.stroke(); }
}

function drawText(ctx, text, x, y, opts = {}) {
  ctx.fillStyle = opts.color || Colors.textPri;
  ctx.font = (opts.weight || '400') + ' ' + (opts.size || 13) + 'px ' + (opts.font || 'Pretendard, sans-serif');
  ctx.textAlign = opts.align || 'center';
  ctx.textBaseline = opts.baseline || 'middle';
  ctx.fillText(text, x, y);
}

/* ── Animation Loop Manager ── */
class AnimationLoop {
  constructor(drawFn) {
    this.drawFn = drawFn;
    this.running = false;
    this.rafId = null;
    this.startTime = 0;
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.startTime = performance.now();
    const loop = (now) => {
      if (!this.running) return;
      const elapsed = (now - this.startTime) / 1000;
      this.drawFn(elapsed);
      this.rafId = requestAnimationFrame(loop);
    };
    this.rafId = requestAnimationFrame(loop);
  }

  stop() {
    this.running = false;
    if (this.rafId) cancelAnimationFrame(this.rafId);
  }

  restart() {
    this.stop();
    this.start();
  }
}

/* ── Timeline Animation ── */
class TimelineAnimation {
  constructor(steps, duration) {
    this.steps = steps; // [{at: 0.1, action: fn}, ...]
    this.duration = duration;
    this.progress = 0;
    this.speed = 1;
    this.playing = false;
    this.executedSteps = new Set();
    this.currentStep = -1;
  }

  play()  { this.playing = true; }
  pause() { this.playing = false; }
  reset() {
    this.progress = 0;
    this.playing = false;
    this.executedSteps.clear();
  }
  setSpeed(s) { this.speed = s; }

  // Manual step control — for ↑↓ keyboard navigation
  goToStep(stepIndex) {
    if (stepIndex < 0 || stepIndex >= this.steps.length) return;
    this.currentStep = stepIndex;
    this.progress = this.steps[stepIndex].at;
    this.executedSteps.clear();
    for (let i = 0; i <= stepIndex; i++) this.executedSteps.add(i);
    this.steps[stepIndex].action();
  }

  nextStep() {
    const next = (this.currentStep ?? -1) + 1;
    if (next < this.steps.length) this.goToStep(next);
  }

  prevStep() {
    const prev = (this.currentStep ?? 0) - 1;
    if (prev >= 0) this.goToStep(prev);
  }

  update(dt) {
    if (!this.playing) return;
    this.progress = Math.min(1, this.progress + (dt * this.speed) / this.duration);
    this.steps.forEach((step, i) => {
      if (this.progress >= step.at && !this.executedSteps.has(i)) {
        this.executedSteps.add(i);
        step.action();
      }
    });
    if (this.progress >= 1) this.playing = false;
  }
}

/* ── Particle System (for decorative effects) ── */
class ParticleSystem {
  constructor(count, bounds) {
    this.particles = [];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: Math.random() * bounds.w,
        y: Math.random() * bounds.h,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        r: Math.random() * 2 + 1,
        alpha: Math.random() * 0.3 + 0.1,
      });
    }
    this.bounds = bounds;
  }

  update() {
    this.particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = this.bounds.w;
      if (p.x > this.bounds.w) p.x = 0;
      if (p.y < 0) p.y = this.bounds.h;
      if (p.y > this.bounds.h) p.y = 0;
    });
  }

  draw(ctx) {
    this.particles.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(108, 92, 231, ${p.alpha})`;
      ctx.fill();
    });
  }
}

/* ── Easing Functions ── */
const Ease = {
  linear: t => t,
  inOut: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
  out: t => t * (2 - t),
  in: t => t * t,
  elastic: t => {
    if (t === 0 || t === 1) return t;
    return Math.pow(2, -10 * t) * Math.sin((t - 0.075) * (2 * Math.PI) / 0.3) + 1;
  },
  bounce: t => {
    if (t < 1 / 2.75) return 7.5625 * t * t;
    if (t < 2 / 2.75) return 7.5625 * (t -= 1.5 / 2.75) * t + 0.75;
    if (t < 2.5 / 2.75) return 7.5625 * (t -= 2.25 / 2.75) * t + 0.9375;
    return 7.5625 * (t -= 2.625 / 2.75) * t + 0.984375;
  }
};

/* ── Value Interpolation ── */
function lerp(a, b, t) { return a + (b - a) * t; }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
