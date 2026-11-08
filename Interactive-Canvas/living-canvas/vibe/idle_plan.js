// The idle loop's schedule and timer (#37). Pure (no DOM), so node can test it: node vibe/test_idle.mjs.
// When nobody is visiting, the station replays the last few visits (the montage's plan, slower), holds the current
// canvas, and loops. Nothing holds still for more than HOLD_MS, so the screen is never static for 10 s.
import { plan } from './montage_plan.js';

export const IDLE_MS = 8000, SLOT_MS = 1500, HOLD_MS = 5000, LAST = 5;

// visits: /api/visits records, oldest first. The last LAST of them, each revealing over the canvas as it was before
// it (the last saved canvas before the replayed ones, or the night's own `before` when the replay starts at visit 1).
// -> { steps: [{ visit, before, after, caption, name, at, ms }], final, finalAt, total }, like the montage's plan.
export function idlePlan(visits) {
  const all = Array.isArray(visits) ? visits : [];
  const tail = all.slice(-LAST);
  if (!tail.length) return { steps: [], final: null, finalAt: 0, total: 0 };
  const earlier = all.slice(0, all.length - tail.length).reverse();
  const before = earlier.length ? (earlier.find(v => v.canvas)?.canvas ?? all[0].before ?? null) : tail[0].before;
  const p = plan([{ ...tail[0], before: before || null }, ...tail.slice(1)]);
  const steps = p.steps.map((s, i) => ({ ...s, at: i * SLOT_MS, ms: SLOT_MS }));
  const finalAt = steps.length * SLOT_MS;
  return { steps, final: p.final, finalAt, total: finalAt + HOLD_MS };
}

// Calls onIdle once IDLE_MS pass with no poke(). poke() on every interaction (and whenever the station goes busy or
// free) restarts the wait; cancel() stops it until the next poke. timers: injectable for tests.
export function idleTimer(onIdle, timers = globalThis) {
  let h = null;
  const cancel = () => { if (h !== null) timers.clearTimeout(h); h = null; };
  return {
    poke() { cancel(); h = timers.setTimeout(() => { h = null; onIdle(); }, IDLE_MS); },
    cancel,
  };
}
