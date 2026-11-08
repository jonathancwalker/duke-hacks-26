// Finishing the night: the station's buttons before and after Finish, and the downloaded file's name.
//     node vibe/test_finish.mjs
import assert from 'node:assert/strict';
import { stationButtons, downloadName } from './finish_plan.js';

let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };

const live = { busy: false, ready: true, visitors: 12, finished: false };

test('during the night, with 12 visitors, Finish is shown and Download is hidden', () => {
  const b = stationButtons(live);
  assert.equal(b.finish.hidden, false); assert.equal(b.finish.disabled, false);
  assert.equal(b.download.hidden, true);
  assert.equal(b.go.disabled, false); assert.equal(b.sim.disabled, false); assert.equal(b.reset.disabled, false);
});

test('with no visitors yet, there is nothing to finish', () => {
  assert.equal(stationButtons({ ...live, visitors: 0 }).finish.disabled, true);
});

test('mid-visit, Finish waits like every other button', () => {
  const b = stationButtons({ ...live, busy: true });
  assert.ok(['go', 'sim', 'reset', 'finish'].every(k => b[k].disabled));
});

test('while the montage plays, nothing can be pressed', () => {
  const b = stationButtons({ ...live, busy: true, finished: true });
  assert.ok(Object.values(b).every(x => x.hidden || x.disabled));
});

test('holding on the final piece of 12 visits: only Download and Reset (a new night) are offered', () => {
  const b = stationButtons({ ...live, finished: true });
  assert.equal(b.download.hidden, false); assert.equal(b.download.disabled, false);
  assert.equal(b.reset.disabled, false);
  assert.ok(b.go.hidden && b.sim.hidden && b.finish.hidden, 'no more visits after finishing');
});

test('Duke Chapel Night on 7 Nov 2026 downloads as duke-chapel-night-2026-11-07.jpg', () => {
  assert.equal(downloadName({ id: 'museum', name: 'Duke Chapel Night' }, new Date(2026, 10, 7, 23, 30)),
               'duke-chapel-night-2026-11-07.jpg');
});

test('an event date wins over today (a night that runs past midnight keeps its date)', () => {
  assert.equal(downloadName({ id: 'museum', name: 'Duke Chapel Night', date: '2026-11-07' }, new Date(2026, 10, 8, 0, 40)),
               'duke-chapel-night-2026-11-07.jpg');
});

test('punctuation and accents fold into a plain slug', () => {
  assert.equal(downloadName({ id: 'concert', name: 'Concert Night: Encore! Café' }, new Date(2026, 10, 7)),
               'concert-night-encore-cafe-2026-11-07.jpg');
});

test('no usable name falls back to the event id, then to living-canvas', () => {
  assert.equal(downloadName({ id: 'museum', name: '★★' }, new Date(2026, 10, 7)), 'museum-2026-11-07.jpg');
  assert.equal(downloadName(null, new Date(2026, 10, 7)), 'living-canvas-2026-11-07.jpg');
});

test('a malformed event date is ignored', () => {
  assert.equal(downloadName({ name: 'Duke Chapel Night', date: 'next Friday' }, new Date(2026, 10, 7)),
               'duke-chapel-night-2026-11-07.jpg');
});

console.log(`finish: ${pass} ok`);
