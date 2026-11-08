// Montage: a fast replay of tonight's saved visits, in order, about a second each. Each visit's path reveals the canvas
// as it was after that visit over the canvas as it was before it, captioned with the reading and who it's credited to,
// ending on the night's final canvas. Revealing the saved canvases (not the mood frames) needs no GPU, and every step
// lands exactly on what the station showed, palette-wash fallbacks included. ?loop replays forever, picking up new
// visits each time (for the projector).
import { S, $, pctx, say, meter, sleep, loadImg } from './state.js';
import { fetchVisits, fetchReflection } from './api.js';
import { fit, startCanvas, reveal, settle, clearTrail } from './render.js';
import { plan, FINAL_MS } from './montage_plan.js';

const LOOP = new URLSearchParams(location.search).has('loop');
const REVEAL_SHARE = .7;   // of each visit's slot; the rest settles onto the saved canvas
const GRACE_MS = 2000, READ_MS_PER_WORD = 300;   // wait for a late reflection; hold long enough to read it

addEventListener('resize', fit);

const load = src => src ? loadImg(src).catch(() => (console.warn('montage image missing', src), null)) : Promise.resolve(null);

// The closing reflection (#34), asked for when the montage starts so it's ready at the end. Only this page asks (the
// station's idle loop has its own engine). Loop mode asks again only when the night has new visits.
// Keyed on the count and the last visit's id and time, so a new night after Reset never reuses the old reflection.
let asked = { key: null, words: null };
const reflectionFor = visits => {
  const last = visits[visits.length - 1], key = `${visits.length} ${last?.id} ${last?.t}`;
  if (asked.key !== key) asked = { key, words: fetchReflection().then(r => r.reflection || '').catch(e => (console.warn('no reflection:', e), '')) };
  return asked.words;
};

async function play() {
  $('#again').disabled = true; meter(0); $('#say').classList.remove('long');
  say('Loading tonight’s visits…');
  const visits = await fetchVisits().catch(e => { say('Saved visits are unavailable.', String(e.message || e)); return null; });
  const p = plan(visits || []), n = p.steps.length;
  $('#count').textContent = n ? `${n} visitor${n > 1 ? 's' : ''} tonight` : '';
  if (!n) {
    if (visits) say('No visits yet tonight.', 'The montage plays once someone has painted.');
    return finish();
  }
  const reflection = reflectionFor(visits);

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
  // The final canvas, captioned with the night's reflection; the count (the server's own fallback) until it arrives.
  say(`${n} visitor${n > 1 ? 's' : ''}. One painting.`, 'Tonight’s canvas');
  const words = await Promise.race([reflection, sleep(GRACE_MS).then(() => '')]);
  if (words) { $('#say').classList.toggle('long', words.length > 90); say(words); }   // in place of the caption
  const hold = Math.max(FINAL_MS, READ_MS_PER_WORD * (words ? words.split(' ').length : 0));
  console.info('montage', { visits: n, playedMs: Math.round(performance.now() - t0) + hold, plannedMs: p.total, reflection: words });
  await sleep(hold);
  return finish();
}

// Loop mode tries again (picking up new visits; after an empty or failed load, a few seconds later); otherwise the
// operator can press Play again.
async function finish() {
  $('#again').disabled = false;
  if (LOOP) { await sleep(FINAL_MS); if (!$('#again').disabled) return play(); }   // disabled: Play again already started one
}

$('#again').onclick = () => play();
addEventListener('keydown', e => { if (e.code === 'Space' && !$('#again').disabled) { e.preventDefault(); play(); } });
play();
