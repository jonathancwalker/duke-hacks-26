// Finishing the night (part of #32): which station buttons show before and after Finish, and what the final piece is
// saved as. Pure (no DOM), so node can test it: node vibe/test_finish.mjs.

// busy: a visit, reset or the finishing montage is running. ready: the canvas is up. finished: the night was closed
// out; the station holds on the final piece until Reset starts a new night. asking: the question card is up.
// After a visit the station rests on the painting until someone presses Next visitor, which brings the card back.
// -> { go, sim, next, reset, finish, download: { hidden, disabled } }
export function stationButtons({ busy, ready, visitors, finished, asking }) {
  const off = busy || !ready;
  const hide = { hidden: true, disabled: true };
  if (finished) {
    return { go: hide, sim: hide, next: hide, finish: hide, reset: { hidden: false, disabled: busy },
             download: { hidden: busy, disabled: busy } };
  }
  return { go: { hidden: false, disabled: off }, sim: { hidden: false, disabled: off },
           next: off || asking ? hide : { hidden: false, disabled: false },
           reset: { hidden: false, disabled: busy },     // Reset also recovers a canvas that failed to load
           finish: { hidden: false, disabled: off || !visitors },
           download: { hidden: true, disabled: true } };
}

const slug = s => String(s || '').normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
  .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const pad = n => String(n).padStart(2, '0');

// event: /api/event ({ id, name, date? }); now: the station's clock, used when the event has no date.
// { name: 'Duke Chapel Night' } on 7 Nov 2026 -> 'duke-chapel-night-2026-11-07.jpg'.
export function downloadName(event, now = new Date()) {
  const base = slug(event?.name) || slug(event?.id) || 'living-canvas';
  const date = /^\d{4}-\d{2}-\d{2}$/.test(event?.date || '') ? event.date
    : `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  return `${base}-${date}.jpg`;
}
