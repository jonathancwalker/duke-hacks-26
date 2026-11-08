// How long each step of a visit lasts, and the time bar under the painting while the visitor says their name.
//     node vibe/test_timing.mjs
import assert from 'node:assert/strict';
import { TRACE_S } from './timing.js';
import { nameProgress, SILENCE_S, LISTEN_MAX_S } from './name_text.js';

let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test('a visitor gets 6 seconds to draw', () => {
  assert.equal(TRACE_S, 6);
});

test('before they speak, the name bar fills over the 5 s of silence that skips', () => {
  assert.equal(SILENCE_S, 5);
  near(nameProgress(0, null), 0);
  near(nameProgress(2.5, null), 0.5);
  near(nameProgress(5, null), 1);
  near(nameProgress(9, null), 1);        // never past full
});

test('once they start talking, the bar slows to finish at the 12 s cap, without jumping back', () => {
  assert.equal(LISTEN_MAX_S, 12);
  near(nameProgress(2, 2), 0.4);         // same as the silence bar at the moment they start
  near(nameProgress(7, 2), 0.4 + 0.6 * 5 / 10);
  near(nameProgress(12, 2), 1);
  near(nameProgress(15, 2), 1);
});

console.log(`timing: ${pass} ok`);
