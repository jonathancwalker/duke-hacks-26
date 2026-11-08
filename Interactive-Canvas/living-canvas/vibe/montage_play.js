// Montage playback: a fast replay of tonight's saved visits, in order, about a second each. Each visit's path reveals
// the canvas as it was after that visit over the canvas as it was before it, captioned with the reading and who it's
// credited to, ending drawn on the night's final canvas. Revealing the saved canvases (not the mood frames) needs no
// GPU, and every step lands exactly on what the station showed, palette-wash fallbacks included. Used by /montage and
// by the station's Finish (part of #32); both pages have the same #frame canvases, #say and #meter.
import { S, $, pctx, say, meter, sleep, loadImg } from './state.js';
import { fetchVisits } from './api.js';
import { fit, startCanvas, reveal, settle, clearTrail } from './render.js';
import { plan } from './montage_plan.js';

const REVEAL_SHARE = .7;   // of each visit's slot; the rest settles onto the saved canvas

const load = src => src ? loadImg(src).catch(() => (console.warn('montage image missing', src), null)) : Promise.resolve(null);

// -> { visits: n, ok } once the final canvas is on screen (and in S.base). ok is false when the saved visits could not
// be loaded; visits is 0 then, or when there are none yet.
export async function playMontage() {
  meter(0);
  say('Loading tonight’s visits…');
  const visits = await fetchVisits().catch(e => { say('Saved visits are unavailable.', String(e.message || e)); return null; });
  const p = plan(visits || []), n = p.steps.length;
  $('#count').textContent = n ? `${n} visitor${n > 1 ? 's' : ''} tonight` : '';
  if (!n) {
    if (visits) say('No visits yet tonight.', 'The montage plays once someone has painted.');
    return { visits: 0, ok: !!visits };
  }

  const urls = [...new Set(p.steps.flatMap(s => [s.before, s.after]).filter(Boolean))];
  const imgs = new Map(await Promise.all(urls.map(async u => [u, await load(u)])));
  const first = [...imgs.values()].find(Boolean);
  if (first) { S.W = first.naturalWidth; S.H = first.naturalHeight; }
  startCanvas(imgs.get(p.steps[0].before) || null);       // older nights saved no starting canvas: start on linen
  clearTrail(); fit();

  const t0 = performance.now();
  for (const [i, s] of p.steps.entries()) {
    say(s.caption || '…', [s.name, `${i + 1} of ${n}`].filter(Boolean).join(' · '));
    meter(i / n);
    const end = t0 + s.at + s.ms, after = imgs.get(s.after), strokes = s.visit.strokes?.filter(st => st.length) || [];
    if (after && strokes.length) await reveal(strokes, after, S.W * .08, .35, null, s.ms * REVEAL_SHARE);
    if (after) await settle(after, end);
    else await sleep(Math.max(0, end - performance.now()));   // no saved canvas: hold on the canvas so far
  }
  meter(1);
  const last = imgs.get(p.final);
  if (last) { pctx.drawImage(last, 0, 0, S.W, S.H); S.base.getContext('2d').drawImage(last, 0, 0, S.W, S.H); }
  say('Tonight’s canvas', `${n} visitor${n > 1 ? 's' : ''}, one painting`);
  console.info('montage', { visits: n, playedMs: Math.round(performance.now() - t0), plannedMs: p.finalAt });
  return { visits: n, ok: true };
}
