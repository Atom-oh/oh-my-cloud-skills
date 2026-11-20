/*
 * Small motion helpers for line-art scenes. No dependencies.
 * Written for this plugin; the ideas (springs for anything attached, keyed poses for
 * gestures, never free sines for a figure) are the documented house rules.
 */

export const clamp = (v, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, v));
export const lerp = (a, b, u) => a + (b - a) * u;

/** Smooth ease in and out, 0..1 to 0..1. */
export const ease = u => { const x = clamp(u); return x * x * (3 - 2 * x); };

/** Deterministic pseudo random numbers, so a scene looks the same on every run. */
export function seeded(seed = 1) {
  let s = seed >>> 0 || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
}

/**
 * Damped spring for anything attached to a moving body (sleeves, scarves, a raised arm).
 * `step(target, dt)` advances one frame and returns the new value.
 */
export function spring(stiffness = 30, damping = 7, start = 0) {
  const s = { x: start, v: 0 };
  s.step = (target, dt) => {
    const h = Math.min(dt, 0.05);          // keep the integrator stable on slow frames
    s.v += (stiffness * (target - s.x) - damping * s.v) * h;
    s.x += s.v * h;
    return s.x;
  };
  return s;
}

/**
 * Keyed pose sampler for gestures: `curve([[0, a], [0.5, b], [1, a]], period)` returns
 * f(t) that loops every `period` seconds with smooth interpolation between keys.
 */
export function curve(keys, period = 1) {
  const n = keys.length;
  return t => {
    const u = ((t / period) % 1 + 1) % 1;
    let i = 0;
    while (i < n - 1 && keys[i + 1][0] <= u) i++;
    const [t0, v0] = keys[i], [t1, v1] = keys[Math.min(i + 1, n - 1)];
    if (t1 === t0) return v0;
    return lerp(v0, v1, ease((u - t0) / (t1 - t0)));
  };
}

/** Gentle slow drift for things that sway (flags, lanterns). Amplitude in output units. */
export const sway = (t, amp = 1, rate = 0.8, phase = 0) =>
  amp * (Math.sin(t * rate * 2 * Math.PI + phase) * 0.7 + Math.sin(t * rate * 4.3 * Math.PI + phase * 1.7) * 0.3);
