# Motion

## Gait

`gait({ kind: 'walk' | 'shuffle' | 'run' })` returns `{ speed, period, pose(phase, go) }`. Advance
`phase += dt / period` and move the figure by exactly `speed * scale` units per second: the stance
foot then stays still on the ground. Never speed a gait up to fit a compressed clock; shorten the
journey or the arrival schedule instead. `pose(phase, go)` blends to a standing pose as `go`
falls to 0, so stopping looks natural.

## Springs and keyed poses

- `spring(stiffness, damping)` for anything attached: sleeves, scarves, a raised hand. Call
  `step(target, dt)` each frame.
- `curve(keys, period)` for gestures with a real shape (typing taps, a nod). Keys are
  `[time 0..1, value]` and the sampler loops smoothly.
- No bare sines on a figure's limbs. Sines are for swaying objects only (`sway`).

## Packet and camera

- One step is one packet journey along one wire span. The packet runs after a short `lead`
  so the camera settles first.
- The camera eases to the step's frame when the step changes (exponential smoothing, about 4 per
  second) and holds still while the packet travels.
- A step change draws immediately (`go()` redraws at once), so the presenter window and a
  background deck window stay in sync even when no animation frames arrive.
- Reduced motion jumps the camera to each step's frame and shows the packet's end state.

## Timing

Durations default to 3 s per step and 2.6 s for the overview hold. Keep a step under about 5 s;
longer reads as stalling. The presenter can always press Down again.
