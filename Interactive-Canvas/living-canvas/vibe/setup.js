// Operator screen (/setup, issue #66): describe tonight, let Gemini draft what visitors see, edit it, preview the
// base scene on the GPU, then save. Saving makes it the active event at once; the station picks it up on its next
// Reset or reload; this page then opens the station itself.
import { freshNightAsk } from './setup_plan.js';

const $ = s => document.querySelector(s);
const TONIGHT = ['name', 'kind', 'date', 'context'];
const DRAFTED = ['question', 'scene', 'voice', 'closing'];
let edited = false;                                   // drafted fields changed by hand since the last fill
let loaded = null;                                    // { id, name } of the saved event the form was filled from

async function call(path, body) {
  const r = await fetch(path, body === undefined ? {} :
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}

function note(id, text, kind = '') { const el = $(id); el.textContent = text; el.className = `note ${kind}`; }
const values = keys => Object.fromEntries(keys.map(k => [k, $(`#${k}`).value.trim()]));
function busy(btn, on, label) {
  btn.disabled = on;
  if (label) btn.textContent = label;
}

function fill(ev) {
  for (const k of [...TONIGHT, ...DRAFTED]) if (ev[k] !== undefined) $(`#${k}`).value = ev[k];
  if (ev.id) loaded = { id: ev.id, name: ev.name };
  edited = false;
}

function clearPreview() { $('#preview').textContent = 'No preview yet'; note('#preview-note', ''); }

async function loadPicker() {
  const events = await call('/api/events');
  const active = events.find(e => e.active);
  $('#pick').innerHTML = '';
  for (const e of events) {
    const o = new Option(e.active ? `${e.name} (live)` : e.name, e.id);
    o.selected = e.active;
    $('#pick').append(o);
  }
  $('#live-name').textContent = active ? active.name : 'none';
}

async function start() {
  try {
    await loadPicker();
    fill(await call('/api/event'));
    if (!$('#date').value) $('#date').value = new Date().toLocaleDateString('en-CA');   // YYYY-MM-DD, local
  } catch (e) { note('#save-note', `Could not load the active event: ${e.message}`, 'warn'); }
}

$('#pick').addEventListener('change', async () => {
  if (edited && !confirm('Replace your edits with this saved event?')) return;
  try { fill(await call(`/api/event?event=${encodeURIComponent($('#pick').value)}`)); clearPreview(); note('#draft-note', ''); }
  catch (e) { note('#draft-note', e.message, 'warn'); }
});

for (const k of DRAFTED) $(`#${k}`).addEventListener('input', () => { edited = true; });
$('#scene').addEventListener('input', clearPreview);

$('#draft').addEventListener('click', async () => {
  if (edited && !confirm('Replace your edits with a new draft?')) return;
  const btn = $('#draft');
  busy(btn, true, 'Drafting…'); note('#draft-note', '');
  try {
    const d = await call('/api/event/draft', values(TONIGHT));
    fill(d); clearPreview();
    const fallback = d.source.startsWith('rules');
    note('#draft-note', fallback ? (d.note || 'This is a simple starting draft. Edit anything.')
      : `Drafted by ${d.source}. Edit anything, then preview the scene.`, fallback ? 'warn' : 'ok');
  } catch (e) { note('#draft-note', `Draft failed: ${e.message}`, 'warn'); }
  busy(btn, false, 'Draft with Gemini');
});

$('#preview-btn').addEventListener('click', async () => {
  const btn = $('#preview-btn'), box = $('#preview');
  busy(btn, true, 'Painting…'); box.textContent = 'Painting the base scene on the GPU (up to a minute)…'; note('#preview-note', '');
  try {
    const r = await call('/api/event/preview', values(['name', 'scene']));
    const img = new Image(); img.alt = 'Base scene preview'; img.src = r.image;
    box.replaceChildren(img);
    if (r.fallback) note('#preview-note', 'The GPU lab didn’t answer; this is the last preview of this exact scene.', 'warn');
  } catch (e) { box.textContent = 'No preview'; note('#preview-note', e.message, 'warn'); }
  busy(btn, false, 'Preview scene');
});

$('#save').addEventListener('click', async () => {
  const btn = $('#save');
  busy(btn, true, 'Saving…');
  try {
    const form = values([...TONIGHT, ...DRAFTED]);
    // Same name as the saved event it was loaded from: update that file. A new name saves a new event.
    if (loaded && form.name === loaded.name) form.id = loaded.id;
    const wasLive = (await call('/api/events')).find(e => e.active)?.id;
    const ev = await call('/api/event/save', form);
    loaded = { id: ev.id, name: ev.name }; edited = false;
    const { visits } = await call('/api/gallery').catch(() => ({ visits: 0 }));
    const ask = freshNightAsk({ wasLive, nowLive: ev.id, name: ev.name, visits });
    if (ask && confirm(ask)) await call('/api/visits/clear', {});
    note('#save-note', `${ev.name} is live. Opening the station…`, 'ok');
    location.href = '/vibe';                          // the station loads the new event fresh
    return;
  } catch (e) { note('#save-note', `Not saved: ${e.message}`, 'warn'); }
  busy(btn, false, 'Save and go live');
});

$('#fresh').addEventListener('click', async () => {
  if (!confirm('Start a fresh night? Tonight’s visits are moved aside (not deleted) and the shared painting starts over.')) return;
  try {
    await call('/api/visits/clear', {});
    note('#save-note', 'Fresh night started. Reload the station to begin from the base scene.', 'ok');
  } catch (e) { note('#save-note', `Could not start a fresh night: ${e.message}`, 'warn'); }
});

start();
