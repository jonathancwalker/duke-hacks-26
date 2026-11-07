// Vibe paint: a visitor says how they feel, then traces a path in the air with a fingertip. Nothing is painted yet,
// only a glowing trail. The GPU repaints the whole scene in their mood (Gemini picks the painters, plus energy,
// warmth and light), and that repainting is revealed only along their path. Crossings show the mood more strongly.
// This module is the visit state machine: speak -> brush -> trace -> reveal -> commit, plus start modes and Simulate.
import { S, $, video, sleep, say, bar, loadImg } from './state.js';
import { fetchBase, fetchBrush, fetchRender } from './api.js';
import { listen } from './audio.js';
import { startCamera, readTips, resetTips } from './hand.js';
import { fit, startCanvas, setTrailBlend, trace, reveal, clearTrail, paletteWash } from './render.js';

const SPEAK_S = 6, TRACE_S = 12, SIM_TRACE_S = 5;

addEventListener('resize', fit);

// ---------------------------------------------------------------- the night's painting
async function reset() {
  S.busy = true; setButtons();
  document.querySelectorAll('.modes button').forEach(b => b.classList.toggle('on', b.dataset.mode === S.start));
  setTrailBlend();
  try {
    let img = null;
    if (S.start === 'chapel') {
      say('Preparing the underpainting…', 'a calm, pale chapel for tonight’s visitors to paint into');
      // GPU lab down and no cached frame: start on bare linen so visits can still run.
      img = await fetchBase().then(r => loadImg(r.image)).catch(e => { console.warn('no base frame:', e); return null; });
      if (img) { S.W = img.naturalWidth; S.H = img.naturalHeight; }
    }
    startCanvas(img);
    S.visitors = 0; $('#count').textContent = ''; fit();
    say('Step up, say how you feel, then trace a path in the air.', 'Your mood repaints the canvas only where your hand went.');
  } catch (e) { say('The GPU lab is not answering.', String(e.message || e)); }
  S.busy = false; setButtons();
}

// ---------------------------------------------------------------- one visit
async function visit(sim) {
  if (S.busy || !S.base) return;
  S.busy = true; setButtons();
  try {
    let heard;
    if (sim) { heard = sim.heard; say(`“${heard.feeling}”`, 'a pretend visitor'); await sleep(900); }
    else {
      await startCamera(); video.classList.add('on');
      say('How are you feeling right now?', 'Say it out loud, any way you like.');
      heard = await listen(SPEAK_S);
    }
    say('Choosing your painters…', ''); bar(0);
    const d = await fetchBrush(heard);
    const look = { palette: d.palette?.length ? d.palette : ['#e6bd6a'], width: S.W * (.035 + .045 * (d.size ?? .5)) };
    const painting = fetchRender({ artists: d.artists, energy: d.energy, warmth: d.warmth, light: d.light,
                                   atmosphere: d.atmosphere, mode: S.start === 'abstract' ? 'abstract' : 'scene' })
      .then(r => loadImg(r.image))
      .catch(e => { console.warn('no mood frame, revealing a palette wash:', e); return paletteWash(look.palette); });
    const names = d.artists.map(a => a.name.split(',')[0]).join(', ');
    say(sim ? 'Tracing…' : 'Now trace a path in the air with your finger.', `${d.reason}`);
    $('#sub').prepend(Object.assign(document.createElement('span'), { id: 'swatches',
      innerHTML: look.palette.slice(0, 8).map(c => `<i style="background:${c}"></i>`).join('') }));
    resetTips();
    const strokes = await trace(sim ? SIM_TRACE_S : TRACE_S, look, sim ? sim.path : readTips);
    video.classList.remove('on');
    if (!strokes.length) { say('No path this time.', 'Hold a hand up where the camera can see it, then trace.'); clearTrail(); return; }
    say('Mixing your paint…', `after ${names}`); bar(0);
    const vibe = await painting;
    say('Your vibe, painted.', `${d.reason}`);
    await reveal(strokes, vibe, look.width);
    S.visitors++; $('#count').textContent = `${S.visitors} visitor${S.visitors > 1 ? 's' : ''} tonight`;
    await sleep(2500);
    say('Next visitor: step up.', 'Each visit repaints only the path its hands drew.');
  } catch (e) {
    console.error(e); say('Something went wrong.', String(e.message || e));
  } finally { S.busy = false; setButtons(); bar(0); video.classList.remove('on'); }
}

// A pretend visitor: a scripted feeling and a looping path, so the room can be tested without a camera.
const FEELINGS = [
  ['I just found out my grandmother passed away', .2], ['We won the championship, I can’t believe it!', .95],
  ['so nervous about my presentation tomorrow', .7], ['honestly just calm, slow Sunday morning', .15],
  ['I’m furious, my landlord kept the whole deposit', .9], ['in love, first date went really well', .6],
];
function simVisitor() {
  const [feeling, arousal] = FEELINGS[Math.floor(Math.random() * FEELINGS.length)];
  const a = 1 + Math.random() * 2, b = 1 + Math.random() * 2, ph = Math.random() * 6, cx = .3 + Math.random() * .4, cy = .35 + Math.random() * .3;
  const path = f => [{ key: 'sim', x: S.W * (cx + .28 * Math.sin(a * 6.28 * f + ph)), y: S.H * (cy + .3 * Math.sin(b * 6.28 * f)) }];
  return { heard: { feeling, arousal }, path };
}

function setButtons() { $('#go').disabled = $('#sim').disabled = $('#reset').disabled = S.busy || !S.base; if (!S.base) $('#reset').disabled = S.busy; }
$('#go').onclick = () => visit();
$('#sim').onclick = () => visit(simVisitor());
$('#reset').onclick = () => !S.busy && reset();
document.querySelectorAll('.modes button').forEach(b => b.onclick = () => {
  if (S.busy || b.dataset.mode === S.start) return;
  if (S.visitors && !confirm('Start a new canvas? Tonight’s painting will be cleared.')) return;
  S.start = b.dataset.mode; try { localStorage.setItem('vibe-start', S.start); } catch {}
  reset();
});
addEventListener('keydown', e => { if (e.code === 'Space' && !S.busy) { e.preventDefault(); visit(); } });
reset();
