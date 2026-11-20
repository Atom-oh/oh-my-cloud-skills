/*
 * Gait: a walking, shuffling or running figure with planted feet.
 *
 * Figure space: about 95 units tall, feet on y = 120, standing at x = 40, facing +x.
 * `gait(...).pose(phase, go)` returns hip, two feet (knee, ankle, pitch), which foot is in
 * front and a small body bob. Move the figure by `speed * scale` per second and the stance
 * foot stays still on the ground; do not speed a gait up to fit a clock.
 */
import { clamp, ease, lerp } from './motion.js';

export const GROUND = 120;
const THIGH = 22, SHANK = 23, HIP_Y = GROUND - (THIGH + SHANK) + 3, X0 = 40;

const PRESETS = {
  walk:    { stride: 22, period: 1.0,  lift: 6,  bob: 1.2, stance: 0.55 },
  shuffle: { stride: 11, period: 0.8,  lift: 2,  bob: 0.6, stance: 0.6 },
  run:     { stride: 38, period: 0.62, lift: 13, bob: 2.6, stance: 0.4 }
};

/** Two bone solver. Bends the knee toward +x (forward). */
function knee(hip, ankle) {
  const dx = ankle[0] - hip[0], dy = ankle[1] - hip[1];
  const d = clamp(Math.hypot(dx, dy), Math.abs(THIGH - SHANK) + 0.01, THIGH + SHANK - 0.01);
  const a = (THIGH * THIGH - SHANK * SHANK + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, THIGH * THIGH - a * a));
  const ux = dx / (Math.hypot(dx, dy) || 1), uy = dy / (Math.hypot(dx, dy) || 1);
  return [hip[0] + ux * a + uy * h, hip[1] + uy * a - ux * h];
}

export function gait(opts = {}) {
  const p = Object.assign({}, PRESETS[opts.kind || 'walk'] || PRESETS.walk, opts);
  // The stance foot travels back `stride` units in `stance * period` seconds.
  const speed = p.stride / (p.stance * p.period);

  function foot(ph, go) {
    const u = ((ph % 1) + 1) % 1, half = p.stride / 2;
    let x, y;
    if (u < p.stance) {                          // stance: foot planted, body moves over it
      x = X0 + half - p.stride * (u / p.stance); y = GROUND - 2;
    } else {                                     // swing: foot comes forward in an arc
      const s = (u - p.stance) / (1 - p.stance);
      x = X0 - half + p.stride * ease(s); y = GROUND - 2 - p.lift * Math.sin(Math.PI * s);
    }
    // blend toward a standing foot as `go` falls to 0
    return [lerp(X0 + (ph % 1 < 0.5 ? -3 : 3), x, go), lerp(GROUND - 2, y, go)];
  }

  return {
    speed, period: p.period, stride: p.stride,
    pose(phase, go = 1) {
      const bob = -p.bob * go * Math.abs(Math.sin(phase * Math.PI * 2));
      const hip = [X0, HIP_Y + bob];
      const feet = [0, 0.5].map(off => {
        const ankle = foot(phase + off, go);
        return { knee: knee(hip, ankle), ankle, pitch: go * (ankle[1] < GROUND - 3 ? -16 : 4) };
      });
      return { hip, feet, front: feet[0].ankle[0] >= feet[1].ankle[0] ? 0 : 1, bob };
    }
  };
}
