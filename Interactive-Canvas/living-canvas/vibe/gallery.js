// The projector gallery: tonight's shared canvas, fullscreen. It polls the booth server for the latest saved canvas
// and crossfades when a visit lands, so it can run in another tab or on another machine that reaches the booth.
// No camera, no controls.
import { fetchEvent } from './api.js';

const POLL_MS = 1000;                        // a visit shows up within ~1 s of being saved, well under the 3 s target
const $ = s => document.querySelector(s);
const layers = [...document.querySelectorAll('.layer')];
let front = 0, shown = null;                 // which <img> is visible, and the canvas URL it shows

// Load the new canvas off-screen, then fade it in over the old one. A failed load leaves the old canvas up and is
// retried on the next poll, since `shown` only changes once the image is on screen.
async function show(url) {
  if (!url) {
    layers.forEach(l => l.classList.remove('on')); $('#wait').classList.remove('off'); shown = null;
    return;
  }
  const next = layers[1 - front];
  // The load event, not img.decode(): decode() can stay pending while the page isn't painting (a projector tab in
  // the background), which would stall the poll loop.
  await new Promise((ok, fail) => {
    next.onload = ok; next.onerror = () => fail(new Error(`canvas did not load: ${url}`));
    next.src = url;
  });
  next.classList.add('on'); layers[front].classList.remove('on'); $('#wait').classList.add('off');
  front = 1 - front; shown = url;
}

async function poll() {
  try {
    const r = await fetch('/api/gallery', { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const g = await r.json();
    $('#count').textContent = g.visits ? `${g.visits} visitor${g.visits > 1 ? 's' : ''} tonight` : '';
    if (g.canvas !== shown) await show(g.canvas);
  } catch (e) { console.warn('gallery poll failed', e); }
  setTimeout(poll, POLL_MS);
}

fetchEvent().then(ev => { $('#event').textContent = ev.name; }).catch(e => console.warn('no event config', e));
poll();
