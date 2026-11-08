// Idle loop (#37): when nobody is visiting, replay the last few visits over the canvas, hold the current canvas, and
// loop, with an invite to step up. It draws only on its own overlay (never the shared canvas or S.base), so stopping
// restores the live canvas exactly. Self-contained: any screen can call startIdle() / stopIdle(); watchIdle() starts it
// after IDLE_MS with no interaction and stops it on any click, touch or key.
import { S, $, mk, sleep, loadImg } from './state.js';
import { fetchVisits } from './api.js';
import { reveal, settle, linen } from './render.js';
import { idlePlan, idleTimer, HOLD_MS } from './idle_plan.js';

const INVITE = 'Step up and add yours', REVEAL_SHARE = .7;   // of each visit's slot; the rest settles onto its canvas

let run = 0, playing = false, ui = null;   // run: bumped by every start and stop, so a stopped loop's awaits bail out
const imgs = new Map();                     // url -> image (or null if missing), for this idle stretch

function overlay() {
  if (ui) return ui;
  const canvas = Object.assign(document.createElement('canvas'), { id: 'idle', hidden: true });
  const cap = Object.assign(document.createElement('div'), { id: 'idle-cap', hidden: true });
  cap.append(Object.assign(document.createElement('div'), { className: 'reading' }),
             Object.assign(document.createElement('div'), { className: 'who' }));
  const invite = Object.assign(document.createElement('div'), { id: 'idle-invite', hidden: true, textContent: INVITE });
  $('#frame').append(canvas, cap, invite);
  return ui = { canvas, ctx: canvas.getContext('2d'), cap, invite };
}

const caption = (reading, who) => {
  ui.cap.hidden = !(reading || who);
  ui.cap.querySelector('.reading').textContent = reading || '';
  ui.cap.querySelector('.who').textContent = who || '';
};

const load = src => !src ? Promise.resolve(null) : imgs.has(src) ? Promise.resolve(imgs.get(src))
  : loadImg(src).catch(() => null).then(i => (imgs.set(src, i), i));

export const idleActive = () => playing;

export function startIdle() {
  if (playing) return;
  playing = true;
  const me = ++run;
  overlay().invite.hidden = false;
  loop(me).catch(e => console.warn('idle loop stopped:', e));
}

// Hides the overlay at once; the live canvas underneath was never touched.
export function stopIdle() {
  if (!playing) return;
  playing = false; run++;
  ui.canvas.hidden = ui.cap.hidden = ui.invite.hidden = true;
  ui.ctx.clearRect(0, 0, ui.canvas.width, ui.canvas.height);
  imgs.clear();
}

async function loop(me) {
  const live = () => me === run;
  const to = { ctx: ui.ctx, base: null, stop: () => !live() };
  while (live()) {
    const p = idlePlan(await fetchVisits().catch(e => (console.warn('idle: visits unavailable', e), [])));
    const urls = [...new Set(p.steps.flatMap(s => [s.before, s.after]).filter(Boolean))];
    await Promise.all(urls.map(load));
    if (!live()) return;
    if (p.steps.length) {
      ui.canvas.width = S.W; ui.canvas.height = S.H;
      to.base = mk();
      const first = imgs.get(p.steps[0].before);
      if (first) to.base.getContext('2d').drawImage(first, 0, 0, S.W, S.H); else linen(to.base.getContext('2d'));
      ui.ctx.drawImage(to.base, 0, 0);
      ui.canvas.hidden = false;
      const t0 = performance.now();
      for (const s of p.steps) {
        caption(s.caption, s.name);
        const end = t0 + s.at + s.ms, after = imgs.get(s.after), strokes = s.visit.strokes?.filter(st => st.length) || [];
        if (after && strokes.length) await reveal(strokes, after, S.W * .08, .35, null, s.ms * REVEAL_SHARE, to);
        if (after && live()) await settle(after, end, to);
        else await sleep(Math.max(0, end - performance.now()));
        if (!live()) return;
      }
    }
    // Hold on the live canvas itself: the night's painting as it is now.
    ui.canvas.hidden = true;
    caption(p.steps.length ? 'Tonight’s canvas' : '', '');
    await sleep(HOLD_MS);
    for (const u of imgs.keys()) if (!urls.includes(u)) imgs.delete(u);
  }
}

// Start the loop after IDLE_MS with no interaction, unless busy() (a visit in progress). Any click, touch or key stops
// it at once. Returns nudge(): call it when the station goes busy or free, to stop the loop and restart the wait.
export function watchIdle(busy) {
  const timer = idleTimer(() => (busy() ? timer.poke() : startIdle()));
  const nudge = () => { stopIdle(); timer.poke(); };
  for (const ev of ['pointerdown', 'keydown']) addEventListener(ev, nudge, { capture: true, passive: true });
  timer.poke();
  return nudge;
}
