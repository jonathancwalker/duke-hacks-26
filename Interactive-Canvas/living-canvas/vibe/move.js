// Movement while talking: MediaPipe pose tracks the wrists, Laban effort is computed exactly as the booth does
// (booth/booth.html labanFrom), and the whole talk becomes ONE movement score that sets the stroke's edge texture.
// Only talk-time movement counts; how the fingertip moves while drawing never changes the texture.
import { video } from './state.js';
import { pickHand, boxOf } from './pick.js';

let pose = null;

// Load the pose model on the already-running camera. Never throws: no pose just means a neutral texture.
export async function startPose() {
  if (pose) return;
  try {
    const { FilesetResolver, PoseLandmarker } = await import('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14');
    const vision = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm');
    pose = await PoseLandmarker.createFromOptions(vision, { runningMode: 'VIDEO', numPoses: 3,
      baseOptions: { modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task', delegate: 'GPU' } });
  } catch (e) { console.warn('pose unavailable', e); }
}

// Record wrists until stop() is called; stop() returns the Laban effort of the whole recording.
// Several bodies in frame: lock onto the largest (nearest) one and follow it by its nose, same rule as the drawing hand.
// onMove(0..1), optional: a live wrist-speed level each frame, for the station's Move meter. Display only.
export function trackMoves(onMove) {
  const track = []; let on = true, lastT = -1, lock = null, prev = null;
  const loop = now => {
    if (!on) return;
    if (pose && video.readyState >= 2 && video.currentTime !== lastT) {
      lastT = video.currentTime;
      const bodies = (pose.detectForVideo(video, now).landmarks || []).map(L => ({ ...boxOf(L, 0), L }));   // 0: nose
      const pick = pickHand(bodies, lock, now / 1000), L = pick.hand?.L;
      lock = pick.lock;
      if (L) track.push({ t: now / 1000, l: L[15].visibility > .5 ? [L[15].x, L[15].y] : null, r: L[16].visibility > .5 ? [L[16].x, L[16].y] : null });
      if (onMove) {
        const f = L ? track[track.length - 1] : null, p = f && (f.r || f.l), q = prev && (prev.r || prev.l);
        try { onMove(p && q ? Math.min(1, Math.hypot(p[0] - q[0], p[1] - q[1]) / Math.max(1 / 60, f.t - prev.t) / 1.5) : 0); } catch {}
        prev = f;
      }
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
  return () => { on = false; return labanFrom(track); };
}

// ---------------------------------------------------------------- ported from booth/booth.html (keep in sync)
const clamp = (v, a = -1, b = 1) => Math.max(a, Math.min(b, v));
const lin = (v, lo, hi) => clamp((v - lo) / (hi - lo) * 2 - 1);            // map [lo,hi] -> [-1,1]

// Centered moving average over ±k samples (landmark jitter is amplified twice by differentiating to acceleration).
function smoothPath(s, k = 2) {
  return s.map((f, i) => { let x = 0, y = 0, n = 0;
    for (let j = Math.max(0, i - k); j <= Math.min(s.length - 1, i + k); j++) { x += s[j].p[0]; y += s[j].p[1]; n++; }
    return { t: f.t, p: [x / n, y / n] }; });
}

/** Laban effort from wrist paths (normalized image coords, seconds), each in -1..1.
 *  weight: peak acceleration (light .. strong) · time: share of sudden accelerations (sustained .. sudden)
 *  space: path straightness over 1 s windows (indirect .. direct) · flow: range of motion (bound .. free) */
export function labanFrom(tr) {
  const out = { weight: 0, time: 0, space: 0, flow: 0, motion: 0, detected: false, still: false, raw: null };
  const accs = [], speeds = [], straight = [], pts = [];
  for (const side of ['l', 'r']) {
    const s = smoothPath(tr.filter(f => f[side]).map(f => ({ t: f.t, p: f[side] })));
    if (s.length < 8) continue;
    out.detected = true;
    let v = [];
    for (let i = 1; i < s.length; i++) { const dt = Math.max(1 / 60, s[i].t - s[i - 1].t); v.push({ t: s[i].t, v: [(s[i].p[0] - s[i - 1].p[0]) / dt, (s[i].p[1] - s[i - 1].p[1]) / dt] }); pts.push(s[i].p); }
    v = v.map((x, i) => { const a = v[Math.max(0, i - 1)], b = v[Math.min(v.length - 1, i + 1)]; return { t: x.t, v: [(a.v[0] + x.v[0] + b.v[0]) / 3, (a.v[1] + x.v[1] + b.v[1]) / 3] }; });
    for (let i = 1; i < v.length; i++) { const dt = Math.max(1 / 60, v[i].t - v[i - 1].t); accs.push(Math.hypot(v[i].v[0] - v[i - 1].v[0], v[i].v[1] - v[i - 1].v[1]) / dt); }
    for (const x of v) speeds.push(Math.hypot(...x.v));
    for (let i = 0; i + 30 < s.length; i += 15) {
      let path = 0; for (let k = i + 1; k <= i + 30; k++) path += Math.hypot(s[k].p[0] - s[k - 1].p[0], s[k].p[1] - s[k - 1].p[1]);
      const disp = Math.hypot(s[i + 30].p[0] - s[i].p[0], s[i + 30].p[1] - s[i].p[1]);
      if (path > 0.05) straight.push(disp / path);
    }
  }
  if (!out.detected) {
    // Body visible but hands out of frame or down at the sides: that's stillness, not absence.
    if (tr.length >= 30) Object.assign(out, { detected: true, still: true, weight: -0.6, time: -0.7, space: 0, flow: -0.3, motion: 0 });
    return out;
  }
  const sorted = accs.slice().sort((a, b) => a - b), p95 = sorted[Math.floor(sorted.length * .95)] || 0;
  const meanSpeed = speeds.reduce((a, b) => a + b, 0) / Math.max(1, speeds.length);
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  const extent = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
  const sudden = accs.filter(a => a > 10).length / Math.max(1, accs.length);
  const straightness = straight.length ? straight.reduce((a, b) => a + b, 0) / straight.length : null;
  out.weight = lin(p95, 12, 50);
  out.time = lin(sudden, 0.05, 0.75);
  out.space = straightness == null ? 0 : lin(straightness, 0.15, 0.75);
  out.flow = lin(extent, 0.9, 1.8);
  out.motion = clamp(meanSpeed / 2.5, 0, 1);
  out.raw = { p95: +p95.toFixed(2), sudden: +sudden.toFixed(3), straightness: straightness == null ? null : +straightness.toFixed(2),
              extent: +extent.toFixed(2), speed: +meanSpeed.toFixed(2), samples: pts.length };
  return out;
}

// ---------------------------------------------------------------- one score for the whole talk
// 0 = soft edges (still, light, sustained, free) .. 1 = ragged bristles (strong, sudden, bound).
// Still hands score 0; no pose at all (no camera, model failed) gets a neutral, fairly soft 0.35.
export function moveScore(l) {
  if (!l?.detected) return .35;
  if (l.still) return 0;
  const u = v => (v + 1) / 2;
  return Math.max(0, Math.min(1, .4 * u(l.weight) + .4 * u(l.time) + .2 * u(-l.flow)));
}
