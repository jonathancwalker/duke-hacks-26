// The montage schedule: every saved visit in order, about a second each, then a hold on the night's final canvas.
// Pure (no DOM), so node can test it: node vibe/test_montage.mjs.
export const SLOT_MS = 1000, FINAL_MS = 4000, MAX_MS = 58000;

// The visit's reading; without one (the rule-based director gives none), its painters, as the station names them.
function caption(v) {
  if (v.reading) return v.reading;
  const names = (Array.isArray(v.painters) ? v.painters : []).map(a => String(a?.name || '').split(',')[0]).filter(Boolean);
  return names.length ? 'after ' + names.join(', ') : '';
}

// visits: /api/visits records, oldest first. Each step reveals its visit's canvas over `before` (the canvas as it was
// before that visit: the previous saved canvas, or the first visit's own `before`). A long night gets shorter slots so
// the whole montage stays under a minute.
// -> { steps: [{ visit, before, after, caption, name, at, ms }], final, finalAt, total } (times in ms).
export function plan(visits) {
  const n = visits.length;
  if (!n) return { steps: [], final: null, finalAt: 0, total: 0 };
  const ms = Math.min(SLOT_MS, Math.floor((MAX_MS - FINAL_MS) / n));
  let before = visits[0].before || null;
  const steps = visits.map((v, i) => {
    const s = { visit: v, before, after: v.canvas || null, caption: caption(v), name: v.name || null, at: i * ms, ms };
    before = v.canvas || before;
    return s;
  });
  const finalAt = n * ms;
  return { steps, final: before, finalAt, total: finalAt + FINAL_MS };
}
