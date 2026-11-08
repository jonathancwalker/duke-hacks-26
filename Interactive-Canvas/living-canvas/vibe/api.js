// Booth server calls. Each returns parsed JSON or throws with the server's error message.
async function api(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}
// The event this page is for: ?event=<name> on the page URL, else the server's BOOTH_EVENT.
const EVENT = new URLSearchParams(location.search).get('event') || undefined;
// { id, name, kind, question, scene, closing } : the active event's config.
export async function fetchEvent() {
  const r = await fetch('/api/event' + (EVENT ? `?event=${encodeURIComponent(EVENT)}` : ''));
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}
// { image } : the night's calm underpainting of the event's scene.
export const fetchBase = () => api('/api/vibe/base', { event: EVENT });
// heard { feeling, arousal } -> { artists, palette, size, energy, warmth, light, atmosphere, reason }.
export const fetchBrush = heard => api('/api/brush', heard);
// { feeling, loudness, movement } -> { artists: [{ name, weight, label }], vectors, read } : the presence scorer's
// 3 paintings (issue #7), from the text head blended with Gemini's read (up to 8 s). Fails (503) when the scorer is
// not loaded; the director's painters are used then.
export const fetchPresence = args => api('/api/presence', args);
// { artists, vectors?, energy, warmth, light, atmosphere, mode } -> { image } : the event's scene repainted in the mood.
// vectors: CLIP vectors for paintings outside the lab library, as fetchPresence returns them.
export const fetchRender = args => api('/api/vibe/render', { ...args, event: EVENT });
// Tonight's saved visits, oldest first: [{ id, t, name ('Visitor N' if skipped), reading, painters, presence, start, strokes, mood, canvas }].
export const fetchVisits = async () => { const r = await fetch('/api/visits'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); };
// Store one finished visit (images as data URLs) -> { id }.
export const saveVisit = v => api('/api/visits', v);
// { reading, before } -> { line, source } : one sentence for after the visit (#67), written from the event, the reading
// and how many people painted before; the event's fixed closing line when Gemini is off, slow (4 s) or off-voice.
export const fetchLine = args => api('/api/line', { ...args, event: EVENT });
// -> { reflection, visitors, source } : the montage's closing words over the final canvas (#34), from every reading of
// the night; "N visitors. One painting." when Gemini is off or slow.
export const fetchReflection = () => api('/api/reflection', { event: EVENT });
// Start a new night: the server moves tonight's visits aside.
export const clearVisits = () => api('/api/visits/clear');
