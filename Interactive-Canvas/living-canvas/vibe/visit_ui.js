// The station's visitor screens (Momento look, ported from booth/booth.html), shown around flow.js's visit:
//   question card + round Start -> 3 · 2 · 1 -> camera with live Vol / Move meters (10 s) -> "use your hand as a brush"
//   countdown -> the painting with the gesture key.
// Look only: no server calls, no visit logic. flow.js stays in charge and calls these through window.momento when it
// reaches each step (every call is optional, so flow.js still runs on a page without them):
//   ask(delayMs)  question card     countdown()  3 · 2 · 1 in the card     capture(sec)  camera + meters
//   closeCard()   lift the card     ready()      get-ready countdown       level(kind, 0..1)  'Vol' | 'Move'
import { startSilk } from './silk.js';

const $ = s => document.querySelector(s);
const wait = ms => new Promise(r => setTimeout(r, ms));
startSilk($('#silk'));

// ---------------------------------------------------------------- the top line
// flow.js writes every status line into #say (hidden). The big top line always shows tonight's question (or the name
// prompt while it's up); everything else shows as a small line under it, except the quiet loading lines.
const say = $('#say'), topQ = $('#top-q'), topSay = $('#top-say'), askQ = $('#ask-q'), askNote = $('#ask-note');
const QUIET = /^(Preparing|Bringing back)/, NAME = /name should we credit/i;
let eventQ = topQ.textContent;
function mirror() {
  const t = (say.textContent || '').trim();
  if (/\?$/.test(t)) {
    topQ.textContent = t; topSay.textContent = '';
    if (!NAME.test(t)) { eventQ = t; askQ.textContent = t; }
  } else {
    topQ.textContent = eventQ;
    const shown = QUIET.test(t) ? '' : t;
    topSay.textContent = shown; askNote.textContent = shown;
  }
}
new MutationObserver(mirror).observe(say, { childList: true, characterData: true, subtree: true });
mirror();

// ---------------------------------------------------------------- the visitor card
const veil = $('#visit'), nextIn = $('#next-in'), confirmFinish = $('#finish-confirm');
let askTimer = 0;
function screen(name) { for (const s of veil.querySelectorAll('.m-screen')) s.classList.toggle('is-off', s.id !== `s-${name}`); }
function cancelAsk() { clearInterval(askTimer); askTimer = 0; nextIn.textContent = ''; }
function openCard(name) { cancelAsk(); screen(name); veil.classList.remove('is-off'); document.body.classList.add('carded'); }
function closeCard() { cancelAsk(); stopCapture(); veil.classList.add('is-off'); document.body.classList.remove('carded'); }
function showAsk() { openCard('ask'); const go = $('#go'); if (!go.disabled) go.focus({ preventScroll: true }); }
// ask(ms): the question card, after ms. While waiting, the station shows Finish with "Next visitor in N s"; the wait
// pauses while the Finish dialog is open, and Finish itself (the night's montage) cancels it via closeCard().
function ask(ms = 0) {
  cancelAsk();
  if (ms <= 0) return showAsk();
  let left = ms;
  const tick = () => {
    if (confirmFinish.open) return;                   // deciding whether to finish: hold the countdown
    if (left <= 0) return showAsk();
    nextIn.textContent = `Next visitor in ${Math.ceil(left / 1000)} s`;
    left -= 250;
  };
  askTimer = setInterval(tick, 250); tick();
}
async function countdown() {
  openCard('count');
  const n = $('#count-n');
  for (const k of ['3', '2', '1']) { n.textContent = k; n.classList.remove('m-pop'); void n.offsetWidth; n.classList.add('m-pop'); await wait(1000); }
}

// ---------------------------------------------------------------- capture: camera + Vol / Move (booth meters)
const capVideo = $('#cap-video'), N = 48, level = { Vol: 0, Move: 0 }, hist = { Vol: Array(N).fill(0), Move: Array(N).fill(0) };
let capTimer = 0, capEnd = 0, capSec = 10;
function capture(sec = 10) {
  openCard('cap');
  capSec = sec; capEnd = performance.now() + sec * 1000;
  level.Vol = level.Move = 0; hist.Vol.fill(0); hist.Move.fill(0);
  const src = $('#cam').srcObject;                    // the station's camera stream; hand and pose tracking read #cam
  if (src && capVideo.srcObject !== src) capVideo.srcObject = src;
  capVideo.play?.().catch(() => {});
  clearInterval(capTimer); capTimer = setInterval(capTick, 50); capTick();   // a steady clock, like the booth's audio tick
}
function stopCapture() { clearInterval(capTimer); capTimer = 0; }
function fitCanvas(cv) {
  const d = Math.min(devicePixelRatio || 1, 2), w = Math.round(cv.clientWidth * d), h = Math.round(cv.clientHeight * d);
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  return cv.getContext('2d');
}
const FG = () => getComputedStyle(document.documentElement).getPropertyValue('--m-fg').trim() || '#F1EDE6';
function drawMeter(cv, k) {                           // bars, newest on the left, fading to the right (as in the booth)
  const g = fitCanvas(cv), W = cv.width, H = cv.height, gap = W / N, bw = Math.max(2, gap * .55);
  g.clearRect(0, 0, W, H); g.fillStyle = FG();
  for (let i = 0; i < N; i++) {
    const h = Math.max(H * .06, hist[k][i] * H * .95);
    g.globalAlpha = 1 - .75 * (i / N); g.fillRect(i * gap + (gap - bw) / 2, (H - h) / 2, bw, h);
  }
  g.globalAlpha = 1;
}
function capTick() {
  const left = Math.max(0, capEnd - performance.now());
  $('#cap-bar').style.width = (100 * (1 - left / (capSec * 1000))) + '%';
  $('#cap-secs').textContent = Math.ceil(left / 1000);
  for (const k of ['Vol', 'Move']) { hist[k].unshift(level[k]); hist[k].pop(); level[k] *= .85; }   // decay between readings
  drawMeter($('#cv-vol'), 'Vol'); drawMeter($('#cv-move'), 'Move');
}
function setLevel(k, v) { if (k in level && Number.isFinite(v)) level[k] = Math.max(level[k], Math.min(1, Math.max(0, v))); }

// ---------------------------------------------------------------- the gesture key on the painting
// Shows after each get-ready countdown, hides after 5 s, and fades sooner whenever the brush comes near it.
const key = $('#key'), frame = $('#frame'), cur = $('#cursor'), trail = $('#trail');
let hideAt = Date.now() + 60 * 60 * 1000, near = false;   // up until the first countdown ends
const syncKey = () => key.classList.toggle('gone', near || Date.now() > hideAt);
const showKey = (ms = 5000) => { hideAt = Date.now() + ms; syncKey(); };
function brushNear(cv) {                              // anything drawn on the cursor or trail canvas inside the key's box?
  if (!cv.width || !cv.height) return false;
  const f = frame.getBoundingClientRect(), k = key.getBoundingClientRect(), sx = cv.width / f.width, sy = cv.height / f.height, pad = 40;
  const x = Math.max(0, (k.left - f.left - pad) * sx), y = Math.max(0, (k.top - f.top - pad) * sy);
  const w = Math.min(cv.width - x, (k.width + pad * 2) * sx), h = Math.min(cv.height - y, (k.height + pad * 2) * sy);
  if (w < 1 || h < 1) return false;
  try { const d = cv.getContext('2d').getImageData(x | 0, y | 0, w | 0, h | 0).data; for (let i = 3; i < d.length; i += 64) if (d[i] > 20) return true; } catch {}
  return false;
}
setInterval(() => {
  if (key.classList.contains('gone') && !near && Date.now() > hideAt) return;   // already hidden for good
  near = brushNear(cur) || brushNear(trail); syncKey();
}, 120);
frame.addEventListener('pointermove', e => {          // a mouse near the key counts too (handy when testing)
  const k = key.getBoundingClientRect(), p = 40;
  if (e.clientX > k.left - p && e.clientX < k.right + p && e.clientY > k.top - p && e.clientY < k.bottom + p) { near = true; syncKey(); }
});

// ---------------------------------------------------------------- get ready: your hand is the brush
const box = $('#ready'), num = $('#ready-num');
let running = null;
async function runReady() {
  box.classList.remove('counting', 'out'); box.hidden = false; document.body.classList.add('counting');
  await wait(2200);                                   // read the line first
  box.classList.add('counting');
  for (const n of ['3', '2', '1']) { num.textContent = n; num.classList.remove('tick'); void num.offsetWidth; num.classList.add('tick'); await wait(900); }
  num.textContent = 'Paint!'; num.style.fontSize = 'clamp(90px,11vw,160px)';
  num.classList.remove('tick'); void num.offsetWidth; num.classList.add('tick');
  await wait(600);
  box.classList.add('out'); document.body.classList.remove('counting'); await wait(350);
  box.hidden = true; num.style.fontSize = '';
  showKey(5000);
}
const ready = () => running || (running = runReady().finally(() => { running = null; }));

window.momento = { ask, countdown, capture, closeCard, ready, level: setLevel };
