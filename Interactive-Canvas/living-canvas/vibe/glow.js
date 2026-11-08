// See your change land (#25): right after the reveal, the visitor's own strokes get a soft warm-white haze over the new
// painting. It breathes while the name prompt is up, then fades when they answer or skip. No line and no bright core:
// the strokes at brush width, feathered. It draws on its own canvas over the painting (screen-blended), so the shared
// canvas and the saved image never contain it. Any failure just means no glow; it never blocks a visit.
import { S, mk, cursor } from './state.js';
import { glowLevel, FADE_MS } from './glow_time.js';

const WARM = 'rgb(255,244,214)', STRENGTH = .42;
let layer = null, run = null;      // run: the glow now showing, { stoppedAt }; null when none

function overlay() {               // made on first use, between the painting and the cursor
  if (!layer) {
    layer = Object.assign(document.createElement('canvas'), { id: 'glow' });
    Object.assign(layer.style, { mixBlendMode: 'screen', pointerEvents: 'none' });
    cursor.before(layer);
  }
  if (layer.width !== S.W || layer.height !== S.H) { layer.width = S.W; layer.height = S.H; }
  return layer;
}

// The strokes ([{x, y}] lists in canvas space) at 90% of the widest reveal brush, round, blurred: white where they drew.
export function strokeMask(strokes) {
  const { W } = S, m = mk(), c = m.getContext('2d');
  c.lineCap = c.lineJoin = 'round'; c.lineWidth = W * .08 * .9; c.strokeStyle = '#fff';
  c.filter = `blur(${Math.round(W / 48)}px)`;                     // 16 px on the 768-wide canvas
  for (const s of strokes) {
    if (!s.length) continue;
    c.beginPath(); c.moveTo(s[0].x, s[0].y);
    for (const p of s.length > 1 ? s.slice(1) : [{ x: s[0].x + .1, y: s[0].y }]) c.lineTo(p.x, p.y);   // a dot still shows
    c.stroke();
  }
  c.filter = 'none';
  return m;
}

function clear() {
  run = null;
  layer?.getContext('2d').clearRect(0, 0, layer.width, layer.height);
}

export function startGlow(strokes) {
  clear();
  try {
    const tint = strokeMask(strokes), tc = tint.getContext('2d');
    tc.globalCompositeOperation = 'source-in'; tc.fillStyle = WARM; tc.fillRect(0, 0, tint.width, tint.height);
    const g = overlay(), gc = g.getContext('2d'), me = { stoppedAt: null }, t0 = performance.now();
    run = me;
    const tick = () => {
      if (run !== me) return;
      const now = performance.now(), a = glowLevel(now - t0, me.stoppedAt == null ? null : me.stoppedAt - t0);
      gc.clearRect(0, 0, g.width, g.height);
      if (me.stoppedAt != null && a <= 0) { run = null; return; }
      gc.globalAlpha = STRENGTH * a; gc.drawImage(tint, 0, 0, g.width, g.height);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  } catch (e) { console.warn('no glow this visit:', e); clear(); }
}

// fade: ease out over FADE_MS (they answered or skipped); false: clear now (a new visit or a new night is starting).
export function stopGlow(fade = true) {
  if (!run) return;
  if (!fade) return clear();
  if (run.stoppedAt != null) return;                              // already fading
  const me = run; me.stoppedAt = performance.now();
  setTimeout(() => run === me && clear(), FADE_MS + 250);          // clears even if frames stop (hidden tab)
}
