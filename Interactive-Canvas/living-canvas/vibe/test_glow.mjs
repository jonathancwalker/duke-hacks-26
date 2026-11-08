// "See your change land" (#25): how bright the glow over a visitor's strokes is, t ms after the reveal.
//     node vibe/test_glow.mjs
import assert from 'node:assert/strict';
import { pulse, glowLevel, FADE_MS } from './glow_time.js';

let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };
const near = (a, b, tol, what) => assert.ok(Math.abs(a - b) <= tol, `${what}: ${a} not within ${tol} of ${b}`);

test('the glow starts dark: pulse(0) is 0', () => {
  assert.equal(pulse(0), 0);
});

test('the first breath peaks near full about 1.3 s in', () => {
  const ts = Array.from({ length: 3000 }, (_, i) => i);
  const peak = ts.reduce((best, t) => pulse(t) > pulse(best) ? t : best, 0);
  near(peak, 1320, 20, 'peak time');
  near(pulse(peak), 1, .01, 'peak level');
});

test('it keeps breathing about every 2.6 s, never going dark while the prompt is up', () => {
  near(pulse(1320 + 2639), pulse(1320), .01, 'one breath later');
  for (let t = 600; t < 20000; t += 50) assert.ok(pulse(t) >= .099 && pulse(t) <= 1, `t=${t}: ${pulse(t)}`);
});

test('a skip at 2 s fades from that level to nothing in about 0.5 s', () => {
  assert.equal(FADE_MS, 500);
  assert.equal(glowLevel(2000, 2000), pulse(2000));
  assert.ok(glowLevel(2250, 2000) < pulse(2000) && glowLevel(2250, 2000) > 0);
  assert.equal(glowLevel(2000 + FADE_MS, 2000), 0);
  assert.equal(glowLevel(9000, 2000), 0);
});

test('no answer yet: the level is just the breath', () => {
  assert.equal(glowLevel(1320, null), pulse(1320));
});

console.log(`${pass} passed`);
