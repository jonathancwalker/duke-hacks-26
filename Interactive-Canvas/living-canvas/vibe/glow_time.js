// How bright the glow over a visitor's own strokes is (#25), 0..1, t ms after it starts. Pure, so node can test it.
export const FADE_MS = 500;
const clamp = x => Math.max(0, Math.min(1, x));
const ease = x => x < .5 ? 2 * x * x : 1 - (-2 * x + 2) ** 2 / 2;

// A slow breath, about 2.6 s per cycle (peaks near 1.3 s), easing in over the first 0.6 s.
export const pulse = t => (.55 + .45 * Math.sin(t / 420 - Math.PI / 2)) * clamp(t / 600);

// stoppedAt: when they answered or skipped (ms on the same clock), or null while the name prompt is up.
// From there the glow fades from the level it had to nothing over FADE_MS.
export const glowLevel = (t, stoppedAt) => stoppedAt == null ? pulse(t)
  : pulse(stoppedAt) * (1 - ease(clamp((t - stoppedAt) / FADE_MS)));
