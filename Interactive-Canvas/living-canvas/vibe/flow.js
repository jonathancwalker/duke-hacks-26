// Vibe paint: a visitor says how they feel, then traces a path in the air with a fingertip. Nothing is painted yet,
// only a glowing trail. The GPU repaints the whole scene in their mood (the presence scorer picks 3 paintings from
// their words, voice and movement; Gemini sets energy, warmth, light and the reading), and that repainting is revealed
// only along their path. Crossings show the mood more strongly.
// This module is the visit state machine: speak -> brush -> trace -> reveal -> name -> commit, plus start modes and Simulate.
import { S, $, video, sleep, say, bar, loadImg } from './state.js';
import { fetchEvent, fetchBase, fetchBrush, fetchPresence, fetchRender, fetchLine, fetchVisits, fetchGallery, saveVisit, clearVisits } from './api.js';
import { listen } from './audio.js';
import { askName } from './name.js';
import { startGlow, stopGlow } from './glow.js';
import { startCamera, readTips, resetTips } from './hand.js';
import { startPose, trackMoves, moveScore } from './move.js';
import { fit, startCanvas, setTrailBlend, trace, reveal, clearTrail, paletteWash } from './render.js';
import { watchIdle } from './idle.js';
import { playMontage } from './montage_play.js';
import { stationButtons, downloadName } from './finish_plan.js';

const SPEAK_S = 10, TRACE_S = 12, SIM_TRACE_S = 5;
// The station's screens (visit_ui.js): question card, 3 · 2 · 1, camera with meters, get-ready countdown. Look only;
// every call is optional, so this module runs the same on a page without them.
const ui = () => window.momento || {};

addEventListener('resize', fit);

// ---------------------------------------------------------------- the night's painting
const showCount = () => { $('#count').textContent = S.visitors ? `${S.visitors} visitor${S.visitors > 1 ? 's' : ''} tonight` : ''; };

// On load, rebuild tonight's painting from the saved visits; with clear (Reset, new start mode), start a new night.
async function reset(clear) {
  S.busy = true; setButtons(); stopGlow(false);
  try {
    // The event's question, scene and closing (events/*.json). Reset re-reads it, so an event saved on /setup goes live.
    if (clear || !S.event) S.event = await fetchEvent();
    if (clear) { await clearVisits(); S.finished = false; $('#say').classList.remove('long'); }
    const saved = clear ? [] : await fetchVisits().catch(e => (console.warn('saved visits unavailable', e), []));
    const last = saved[saved.length - 1];
    if (last?.start) S.start = last.start;
    document.querySelectorAll('.modes button').forEach(b => b.classList.toggle('on', b.dataset.mode === S.start));
    setTrailBlend();
    let img = null;
    if (last?.canvas) {
      say('Bringing back tonight’s painting…', `${saved.length} visitor${saved.length > 1 ? 's' : ''} so far`);
      img = await loadImg(last.canvas).catch(() => (console.warn('saved canvas missing', last.canvas), null));
      if (img) { S.W = img.naturalWidth; S.H = img.naturalHeight; }
    }
    if (!img && S.start === 'chapel') {
      say('Preparing the underpainting…', 'a calm, pale underpainting for tonight’s visitors to paint into');
      // GPU lab down and no cached frame: start on bare linen so visits can still run.
      img = await fetchBase().then(r => loadImg(r.image)).catch(e => { console.warn('no base frame:', e); return null; });
      if (img) { S.W = img.naturalWidth; S.H = img.naturalHeight; }
    }
    startCanvas(img);
    S.visitors = saved.length; showCount(); fit();
    say(S.event.question, 'Step up and answer out loud, then trace a path in the air. Your mood repaints the canvas only where your hand went.');
  } catch (e) { say('The GPU lab is not answering.', String(e.message || e)); }
  if (!S.finished) showQuestion();                      // the question card for the first visitor
  S.busy = false; setButtons();
}

// The question card (visit_ui.js). After a visit it waits for Next visitor instead of coming back on a timer.
function showQuestion() { S.asking = !!ui().ask; ui().ask?.(); }

// ---------------------------------------------------------------- one visit
async function visit(sim) {
  if (S.busy || S.finished || !S.base) return;
  S.busy = true; S.asking = false; setButtons(); stopGlow(false);
  try {
    let heard, laban;
    if (sim) { ui().closeCard?.(); heard = sim.heard; laban = sim.laban; say(`“${heard.feeling}”`, `a pretend visitor, ${sim.voice}`); await sleep(900); }
    else {
      await startCamera(); await startPose(); video.classList.add('on');
      say(S.event.question, 'Say it out loud, any way you like.');
      await ui().countdown?.();                           // 3 · 2 · 1 in the card
      ui().capture?.(SPEAK_S);                            // camera with live Vol / Move meters
      const moves = trackMoves(v => ui().level?.('Move', v));
      try { heard = await listen(SPEAK_S); } finally { laban = moves(); ui().closeCard?.(); }
    }
    const ready = ui().ready?.();                         // "use your hand as a brush" while the painters are chosen
    const texture = moveScore(laban);                     // one edge texture for the whole stroke; drawing can't change it
    console.info('movement while talking', { texture: +texture.toFixed(2), ...laban });
    say('Choosing your painters…', ''); bar(0);
    // Painters: the presence scorer (words + voice loudness + movement), asked alongside the director; both wait on
    // Gemini. Scorer down: the director's own painters.
    const [d, pres] = await Promise.all([
      fetchBrush(heard),
      fetchPresence({ feeling: heard.feeling, loudness: heard.arousal, movement: texture })
        .catch(e => (console.warn('presence scorer unavailable:', e), null)),
    ]);
    // The line after the visit (#67), written while the canvas renders. Never awaited: if it isn't back by the time
    // it shows, the event's fixed closing line shows instead.
    let line = null;
    fetchLine({ reading: d.reading, before: S.visitors }).then(r => { line = r.line; }).catch(e => console.warn('no visit line:', e));
    const artists = pres?.artists?.length ? pres.artists : d.artists;
    if (pres) console.info('presence', pres.read, artists.map(a => `${a.label} ${a.weight}`));
    const look = { palette: d.palette?.length ? d.palette : ['#e6bd6a'], width: S.W * (.035 + .045 * (d.size ?? .5)) };
    const painting = fetchRender({ artists, vectors: pres?.vectors, energy: d.energy, warmth: d.warmth, light: d.light,
                                   atmosphere: d.atmosphere, mode: S.start === 'abstract' ? 'abstract' : 'scene' })
      .then(r => loadImg(r.image))
      .catch(e => { console.warn('no mood frame, revealing a palette wash:', e); return paletteWash(look.palette); });
    const names = artists.map(a => (a.label || a.name).split(',')[0]).join(', ');
    const reason = pres ? (d.reading ? `${d.reading} · after ${names}` : `after ${names}`).slice(0, 90) : d.reason;
    say(sim ? 'Tracing…' : 'Now trace a path in the air with your finger.', reason);
    $('#sub').prepend(Object.assign(document.createElement('span'), { id: 'swatches',
      innerHTML: look.palette.slice(0, 8).map(c => `<i style="background:${c}"></i>`).join('') }));
    await ready;                                          // the get-ready countdown ends...
    resetTips();                                          // ...and locks onto the largest hand: the 3, 2, 1 should end here
    const strokes = await trace(sim ? SIM_TRACE_S : TRACE_S, look, sim ? sim.path : readTips);
    video.classList.remove('on');
    if (!strokes.length) { say('No path this time.', 'Hold a hand up where the camera can see it, then trace.'); clearTrail(); return; }
    say('Mixing your paint…', `after ${names}`); bar(0);
    const vibe = await painting;
    say('Your vibe, painted.', reason);
    const before = S.visitors ? undefined : S.base.toDataURL('image/jpeg', .92);   // night's first visit: where the montage starts
    await reveal(strokes, vibe, look.width, texture, heard.envelope);
    S.visitors++; showCount();
    startGlow(strokes);                                   // their strokes breathe behind the name prompt, then fade
    const name = await askName(S.visitors, !!sim, stopGlow);   // '' = skipped; never throws, so the visit always finishes
    say(line || S.event.closing, reason);
    const painters = artists.map(a => ({ name: a.label || a.name, id: a.name, weight: a.weight }));
    await saveVisit({ name, reading: d.reading, painters, presence: heard.presence, start: S.start,
                      strokes, mood: vibe.src, canvas: S.base.toDataURL('image/jpeg', .92), before })
      .catch(e => console.warn('visit not saved', e));
    await sleep(2500);
    say('Next visitor: step up.', 'Each visit repaints only the path its hands drew.');
  } catch (e) {
    console.error(e); say('Something went wrong.', String(e.message || e));
  } finally {
    stopGlow(); S.busy = false; setButtons(); bar(0); video.classList.remove('on');   // rests here until Next visitor
  }
}

// A pretend visitor: a scripted feeling, how they moved while saying it, a voice loudness shape and a looping path, so
// the room can be tested without a camera or mic. Laban effort per feeling: [weight, time, space, flow], each -1..1 as
// labanFrom gives. Loudness shapes are 0..1 over the talking moment; each of 24 steps gets a little syllable jitter.
const VOICES = { 'quiet then loud': f => .15 + .85 * f, 'loud then quiet': f => 1 - .85 * f,
                 'swelling': f => .2 + .8 * Math.sin(Math.PI * f), 'steady': () => .9 };
const FEELINGS = [
  ['I just found out my grandmother passed away', .2, [-.7, -.8, -.6, .6]], ['We won the championship, I can’t believe it!', .95, [.8, .9, .3, .8]],
  ['so nervous about my presentation tomorrow', .7, [-.2, .7, -.6, -.8]], ['honestly just calm, slow Sunday morning', .15, [-.8, -.9, -.4, .5]],
  ['I’m furious, my landlord kept the whole deposit', .9, [.9, .9, .9, -.9]], ['in love, first date went really well', .6, [-.6, -.3, -.5, .8]],
];
function simVisitor() {
  const [feeling, arousal, [weight, time, space, flow]] = FEELINGS[Math.floor(Math.random() * FEELINGS.length)];
  const a = 1 + Math.random() * 2, b = 1 + Math.random() * 2, ph = Math.random() * 6, cx = .3 + Math.random() * .4, cy = .35 + Math.random() * .3;
  const path = f => [{ key: 'sim', x: S.W * (cx + .28 * Math.sin(a * 6.28 * f + ph)), y: S.H * (cy + .3 * Math.sin(b * 6.28 * f)),
    fist: f > .4 && f < .55 }];   // a fist mid-trace lifts the pen, so the path is two separate shapes
  const voices = Object.keys(VOICES), voice = voices[Math.floor(Math.random() * voices.length)];
  const envelope = Array.from({ length: 24 }, (_, i) => VOICES[voice](i / 23) * (.85 + .15 * Math.random()));
  return { heard: { feeling, arousal, envelope }, laban: { weight, time, space, flow, detected: true }, path, voice };
}

// ---------------------------------------------------------------- finishing the night (part of #32)
// Finish -> "are you sure?" -> tonight's montage -> hold on the final piece with Download. Tonight's visits stay in
// place (the final piece and /montage stay reachable) until Reset starts a new night, which moves them aside.
async function finishNight() {
  if (S.busy || S.finished || !S.visitors) return;
  S.busy = S.finished = true; S.asking = false; setButtons(); stopGlow(false); clearTrail(); ui().closeCard?.();
  try {
    const { visits, ok } = await playMontage();
    if (!ok) S.finished = false;                          // visits unavailable: back to the night, nothing was closed
    else if (!visits) { S.finished = false; S.visitors = 0; showCount(); }
  } catch (e) { console.error(e); say('The montage did not play.', String(e.message || e)); }
  S.busy = false; setButtons();
}

// Saves the latest saved canvas (what the montage ended on) as <event>-<date>.jpg.
async function download() {
  try {
    const { canvas } = await fetchGallery();
    if (!canvas) throw new Error('no saved canvas yet');
    let blob = await fetch(canvas).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.blob(); });
    if (blob.type !== 'image/jpeg') {                     // the station saves JPEGs; re-encode anything else
      const img = await loadImg(URL.createObjectURL(blob)), c = document.createElement('canvas');
      URL.revokeObjectURL(img.src);
      c.width = img.naturalWidth; c.height = img.naturalHeight; c.getContext('2d').drawImage(img, 0, 0);
      blob = await new Promise(r => c.toBlob(r, 'image/jpeg', .92));
    }
    const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: downloadName(S.event) });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
  } catch (e) { console.warn('download failed', e); say('Tonight’s canvas', `Download failed: ${e.message || e}`); }
}

const confirmFinish = $('#finish-confirm');
confirmFinish.addEventListener('close', () => { if (confirmFinish.returnValue === 'finish') finishNight(); });

// Idle loop (#37): after 8 s with no visit and no interaction, replay recent visits; going busy or free restarts the wait.
const nudgeIdle = watchIdle(() => S.busy || S.finished || confirmFinish.open || !S.base);
function setButtons() {
  nudgeIdle();
  const b = stationButtons({ busy: S.busy, ready: !!S.base, visitors: S.visitors, finished: !!S.finished, asking: !!S.asking });
  for (const [id, { hidden, disabled }] of Object.entries(b)) Object.assign($('#' + id), { hidden, disabled });
}
$('#go').onclick = () => visit();
$('#sim').onclick = () => visit(simVisitor());
$('#next').onclick = () => { if (S.busy || S.finished) return; showQuestion(); setButtons(); };
$('#reset').onclick = () => !S.busy && reset(true);
$('#finish').onclick = () => { if (!S.busy && S.visitors) { confirmFinish.returnValue = ''; confirmFinish.showModal(); } };
$('#download').onclick = download;
document.querySelectorAll('.modes button').forEach(b => b.onclick = () => {
  if (S.busy || b.dataset.mode === S.start) return;
  if (S.visitors && !confirm('Start a new canvas? Tonight’s painting will be cleared.')) return;
  S.start = b.dataset.mode; try { localStorage.setItem('vibe-start', S.start); } catch {}
  reset(true);
});
addEventListener('keydown', e => { if (e.code === 'Space' && !S.busy && !confirmFinish.open) { e.preventDefault(); visit(); } });
reset();
