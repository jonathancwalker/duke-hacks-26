// Booth server calls. Each returns parsed JSON or throws with the server's error message.
async function api(path, body) {
  const r = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}
// { image } : the night's calm chapel underpainting.
export const fetchBase = () => api('/api/vibe/base');
// heard { feeling, arousal } -> { artists, palette, size, energy, warmth, light, atmosphere, reason }.
export const fetchBrush = heard => api('/api/brush', heard);
// { artists, energy, warmth, light, atmosphere, mode } -> { image } : the whole scene repainted in the mood.
export const fetchRender = args => api('/api/vibe/render', args);
// Tonight's saved visits, oldest first: [{ id, t, name, reading, painters, presence, start, strokes, mood, canvas }].
export const fetchVisits = async () => { const r = await fetch('/api/visits'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); };
// Store one finished visit (images as data URLs) -> { id }.
export const saveVisit = v => api('/api/visits', v);
// Start a new night: the server moves tonight's visits aside.
export const clearVisits = () => api('/api/visits/clear');
