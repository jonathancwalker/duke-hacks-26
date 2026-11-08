// Lock onto one visitor (#22). Pure, no camera or DOM, so it runs under node (vibe/test_pick.mjs).
// Candidates are { area, x, y, ... }: the landmark bounding-box area (bigger = nearer the camera) and a reference
// point (a hand's wrist, a body's nose), all in normalized image coords. Extra fields ride along untouched.

export const LOST_S = .5;   // gone this long: stop following frame to frame and re-acquire near the last position
export const STEP = .2;     // while following, the locked point moves at most this far between frames
export const NEAR = .35;    // re-acquiring: how far from the last position a hand may reappear

// Bounding box of a landmark list; (x, y) is landmark `at`.
export function boxOf(lm, at) {
  let x0 = 1, x1 = 0, y0 = 1, y1 = 0;
  for (const p of lm) { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); }
  return { area: Math.max(0, x1 - x0) * Math.max(0, y1 - y0), x: lm[at].x, y: lm[at].y };
}

const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const largest = cs => cs.reduce((a, b) => (!a || b.area > a.area ? b : a), null);

// One frame: which candidate is the visitor, and the lock to pass in next frame. t in seconds.
// No lock: take the largest (the 3, 2, 1 moment). Locked: follow the nearest within STEP of the last position; others are
// ignored. Lost longer than LOST_S: take the largest within NEAR of where it was last seen. Never jump to a far stranger.
export function pickHand(cands, lock, t) {
  let hand;
  if (!lock) hand = largest(cands);
  else if (t - lock.t <= LOST_S) {
    hand = cands.filter(c => dist(c, lock) <= STEP).sort((a, b) => dist(a, lock) - dist(b, lock))[0] || null;
  } else hand = largest(cands.filter(c => dist(c, lock) <= NEAR));
  return hand ? { hand, lock: { x: hand.x, y: hand.y, t } } : { hand: null, lock };
}
