// Drawing: canvas layout, linen ground, glowing trails while tracing, and the bristle-masked reveal.
import { S, $, paint, trail, cursor, pctx, tctx, cctx, mk, bar, ease, frame, blankStart } from './state.js';

const REVEAL_MS = 3200;

export function fit() {
  const { W, H } = S, aw = innerWidth - 56, ah = innerHeight - 64 - 112, s = Math.min(aw / W, ah / H);
  Object.assign($('#frame').style, { width: W * s + 'px', height: H * s + 'px', left: (innerWidth - W * s) / 2 + 'px', top: 64 + (ah - H * s) / 2 + 'px' });
}

// Brighter, more saturated versions of a painting's colors, so trails glow on the dark-ish canvas.
export function glow(hex, onLight = blankStart()) {
  let [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, d = mx - mn;
  let h = 0, s = d ? d / (1 - Math.abs(2 * l - 1)) : 0;
  if (d) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return `hsl(${Math.round(h * 60)}, ${Math.round(Math.min(1, s * 1.3 + .15) * 100)}%, ${Math.round((onLight ? Math.max(.35, Math.min(.55, l)) : Math.max(.55, Math.min(.75, l + .25))) * 100)}%)`;
}

// Primed linen: warm off-white with a faint woven grain.
export function linen(c) {
  const { W, H } = S;
  c.fillStyle = '#e9e2d3'; c.fillRect(0, 0, W, H);
  for (let i = 0; i < 2600; i++) {
    const x = Math.random() * W, y = Math.random() * H, horiz = Math.random() < .5, len = 4 + Math.random() * 14;
    c.strokeStyle = Math.random() < .5 ? 'rgba(90,70,40,.05)' : 'rgba(255,255,255,.12)'; c.lineWidth = .8;
    c.beginPath(); c.moveTo(x, y); c.lineTo(horiz ? x + len : x, horiz ? y : y + len); c.stroke();
  }
}

// Size the canvases and lay down the night's starting painting (img, or linen when img is null).
export function startCanvas(img) {
  for (const c of [paint, trail, cursor]) { c.width = S.W; c.height = S.H; }
  S.base = mk();
  if (img) S.base.getContext('2d').drawImage(img, 0, 0); else linen(S.base.getContext('2d'));
  pctx.drawImage(S.base, 0, 0);
}

export const setTrailBlend = () => { trail.style.mixBlendMode = blankStart() ? 'multiply' : 'screen'; };

export const clearTrail = () => tctx.clearRect(0, 0, S.W, S.H);

// Trace for sec seconds. tipsAt(f) -> [{ key, x, y }] or null (no new frame), f in 0..1. Returns strokes of points.
export async function trace(sec, look, tipsAt) {
  const { W, H } = S;
  const strokes = [], live = {}, width = look.width, colors = look.palette.map(c => glow(c));
  tctx.clearRect(0, 0, W, H); trail.style.opacity = 1;
  let n = 0;
  const t0 = performance.now();
  for (let t = 0; t < sec; t = (performance.now() - t0) / 1000) {
    bar(t / sec);
    const tips = tipsAt(t / sec);                         // null: no new camera frame this tick (keep strokes open)
    cctx.clearRect(0, 0, W, H);
    if (tips) {
      for (const k of Object.keys(live)) if (!tips.some(p => p.key === k)) delete live[k];   // hand left: stroke ends
      for (const p of tips) {
        let h = live[p.key];
        if (!h) { h = live[p.key] = { x: p.x, y: p.y, s: [] }; strokes.push(h.s); }
        const x = h.x + (p.x - h.x) * .5, y = h.y + (p.y - h.y) * .5;           // light smoothing
        const prev = h.s[h.s.length - 1];
        if (!prev || Math.hypot(x - prev.x, y - prev.y) > W / 400) {
          h.s.push({ x, y, t });
          const c = colors[Math.floor(n++ / 14) % colors.length];
          const a = prev || { x, y };
          tctx.lineCap = tctx.lineJoin = 'round'; tctx.strokeStyle = c;
          tctx.globalAlpha = .16; tctx.lineWidth = width; tctx.shadowBlur = 0;
          tctx.beginPath(); tctx.moveTo(a.x, a.y); tctx.lineTo(x, y); tctx.stroke();
          tctx.globalAlpha = .95; tctx.lineWidth = W / 300; tctx.shadowBlur = W / 60; tctx.shadowColor = c;
          tctx.beginPath(); tctx.moveTo(a.x, a.y); tctx.lineTo(x, y); tctx.stroke();
        }
        h.x = x; h.y = y;
      }
    }
    for (const h of Object.values(live)) dot(h.x, h.y, width / 2);
    await frame();
  }
  cctx.clearRect(0, 0, W, H);
  return strokes.filter(s => s.length);
}

function dot(x, y, r) {
  cctx.globalAlpha = .9; cctx.strokeStyle = '#fff'; cctx.lineWidth = S.W / 500;
  cctx.beginPath(); cctx.arc(x, y, r, 0, Math.PI * 2); cctx.stroke();
}

// Voice loudness (envelope, 0..1 over the talking moment) stretched across the drawing: f = 0 at the first drawn point,
// 1 at the last. Quiet talk gives a faint reveal, loud talk a strong one. No envelope: full strength. Squared because a
// piece's core and bristles stack and saturate fast; this keeps the visible opacity roughly following the voice.
const FAINT = .05;
function loudness(envelope, f) {
  if (!envelope?.length) return 1;
  const x = Math.max(0, Math.min(1, f)) * (envelope.length - 1), i = Math.floor(x), j = Math.min(envelope.length - 1, i + 1);
  const v = envelope[i] + (envelope[j] - envelope[i]) * (x - i);
  return FAINT + (1 - FAINT) * v * v;
}

// The mood frame shows through a soft mask built along the path in the order it was drawn. Each short piece of path
// adds about two-thirds opacity (scaled by the voice's loudness at that moment) with ragged bristle edges, so
// crossings come through fully.
export async function reveal(strokes, vibe, width, envelope) {
  const { W, H, base } = S;
  const mask = mk(), soft = mk(), layer = mk(), m = mask.getContext('2d'), sc = soft.getContext('2d'), lc = layer.getContext('2d');
  m.lineCap = m.lineJoin = 'round'; m.strokeStyle = '#fff';
  const ts = strokes.flat().map(p => p.t), tFirst = Math.min(...ts), span = Math.max(...ts) - tFirst || 1;
  const pieces = [];
  for (const s of strokes) {
    const bristles = Array.from({ length: 9 }, () => ({ dx: (Math.random() - .5) * width * .9, dy: (Math.random() - .5) * width * .9,
                                                       w: width * (.08 + Math.random() * .14), a: .35 + Math.random() * .4 }));
    for (let i = 0; i < Math.max(1, s.length - 1); i += 10) {
      const pts = s.slice(i, i + 11);
      pieces.push({ pts, bristles, k: loudness(envelope, (pts[pts.length >> 1].t - tFirst) / span) });
    }
  }
  const line = (pts, dx, dy) => { m.beginPath(); m.moveTo(pts[0].x + dx, pts[0].y + dy);
    for (const q of pts.length > 1 ? pts.slice(1) : pts) m.lineTo(q.x + dx, q.y + dy); m.stroke(); };
  let drawn = 0; const t0 = performance.now();
  for (let f = 0; f < 1;) {
    f = Math.min(1, (performance.now() - t0) / REVEAL_MS);
    bar(f);
    const want = Math.round(ease(f) * pieces.length);
    let tip = null;
    while (drawn < want) {
      const { pts, bristles, k } = pieces[drawn++];
      m.globalAlpha = .65 * k; m.lineWidth = width * .75; line(pts, 0, 0);
      for (const b of bristles) { m.globalAlpha = b.a * k; m.lineWidth = b.w; line(pts, b.dx, b.dy); }
      tip = pts[pts.length - 1];
    }
    sc.clearRect(0, 0, W, H); sc.filter = `blur(${Math.max(1, Math.round(W / 350))}px)`; sc.drawImage(mask, 0, 0); sc.filter = 'none';
    lc.globalCompositeOperation = 'source-over'; lc.clearRect(0, 0, W, H); lc.drawImage(vibe, 0, 0, W, H);
    lc.globalCompositeOperation = 'destination-in'; lc.drawImage(soft, 0, 0); lc.globalCompositeOperation = 'source-over';
    pctx.drawImage(base, 0, 0); pctx.drawImage(layer, 0, 0);
    trail.style.opacity = 1 - f;
    cctx.clearRect(0, 0, W, H);
    if (tip && f < 1) { cctx.globalAlpha = .8; cctx.fillStyle = '#fff'; cctx.shadowBlur = W / 40; cctx.shadowColor = '#fff';
      cctx.beginPath(); cctx.arc(tip.x, tip.y, W / 160, 0, Math.PI * 2); cctx.fill(); cctx.shadowBlur = 0; }
    await frame();
  }
  cctx.clearRect(0, 0, W, H); tctx.clearRect(0, 0, W, H);
  base.getContext('2d').drawImage(paint, 0, 0);                  // the change stays: next visitor paints over it
}
