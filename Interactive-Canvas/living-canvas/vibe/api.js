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
// { artists, energy, warmth, light, atmosphere, mode } -> { image } : the event's scene repainted in the mood.
export const fetchRender = args => api('/api/vibe/render', { ...args, event: EVENT });
