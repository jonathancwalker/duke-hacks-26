// Lock onto one visitor (#22): only the visitor's hand draws, even with other people in frame.
// Run: node vibe/test_pick.mjs   (no camera; hands are synthetic { area, x, y } in normalized image coords)
import assert from 'node:assert/strict';
import { pickHand, boxOf, LOST_S } from './pick.js';

const hand = (name, area, x, y) => ({ name, area, x, y });
const F = 1 / 30;                                  // one camera frame
let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };

test('a bigger bystander appearing far away does not steal a locked visitor', () => {
  const lock = { x: .5, y: .5, t: 0 };
  const visitor = hand('visitor', .04, .5, .5), bystander = hand('bystander', .06, .9, .2);
  assert.equal(pickHand([bystander, visitor], lock, F).hand, visitor);
  assert.equal(pickHand([visitor, bystander], lock, F).hand, visitor);
});

test('with no lock yet, the largest hand is locked (nearest person)', () => {
  const r = pickHand([hand('far', .01, .2, .2), hand('near', .05, .6, .7)], null, 0);
  assert.equal(r.hand.name, 'near');
  assert.deepEqual(r.lock, { x: .6, y: .7, t: 0 });
});

test('no hands and no lock: nothing drawn, still unlocked', () => {
  assert.deepEqual(pickHand([], null, 0), { hand: null, lock: null });
});

test('the locked hand is followed by nearest wrist as it moves', () => {
  let lock = null;
  for (let i = 0; i <= 20; i++) {
    const v = hand('visitor', .04, .3 + .02 * i, .5);          // sweeps right, toward a bigger bystander
    const r = pickHand([hand('bystander', .07, .85, .45), v], lock, i * F);
    assert.equal(r.hand.name, i === 0 ? 'bystander' : 'visitor', `frame ${i}`);
    lock = i === 0 ? { x: v.x, y: v.y, t: 0 } : r.lock;        // frame 0: pretend the countdown locked the visitor
  }
});

test('visitor briefly lost: nobody draws, lock keeps the last position', () => {
  const lock = { x: .5, y: .5, t: 1 };
  const r = pickHand([hand('bystander', .06, .9, .2)], lock, 1 + .2);
  assert.equal(r.hand, null);
  assert.deepEqual(r.lock, lock);
});

test('after ~0.5 s lost, re-acquire the largest hand near the last position, never a far stranger', () => {
  const lock = { x: .5, y: .5, t: 1 }, t = 1 + LOST_S + .1;
  const far = hand('far stranger', .09, .95, .15), near = hand('near small', .02, .6, .55), nearBig = hand('near big', .04, .4, .6);
  assert.equal(pickHand([far], lock, t).hand, null);
  assert.equal(pickHand([far, near, nearBig], lock, t).hand, nearBig);
});

test('someone walking behind the visitor never draws (whole window)', () => {
  let lock = null, drawn = 0;
  for (let i = 0; i < 12 * 30; i++) {
    const t = i * F, a = t * 2;
    const visitor = hand('visitor', .04, .5 + .1 * Math.cos(a), .62 + .08 * Math.sin(a));   // circles in front
    const walker = hand('walker', .06, -.2 + 1.4 * (i / 360), .3);                           // crosses behind, bigger box
    const lost = i % 50 > 44;                                                                // visitor drops out now and then
    const hands = (lost ? [walker] : i % 2 ? [walker, visitor] : [visitor, walker]).filter(h => h.x >= 0 && h.x <= 1);
    const r = pickHand(hands, i === 0 ? null : lock, t);
    if (i === 0) assert.equal(r.hand.name, 'visitor');   // walker not in frame yet at the countdown
    if (r.hand) { assert.equal(r.hand.name, 'visitor', `frame ${i}`); drawn++; }
    lock = r.lock;
  }
  assert.ok(drawn > 300, `visitor drew in ${drawn} frames`);
});

test('boxOf: landmark bounding-box area and the reference point', () => {
  const lm = [{ x: .5, y: .8 }, { x: .4, y: .6 }, { x: .6, y: .5 }];
  const b = boxOf(lm, 0);
  assert.ok(Math.abs(b.area - .2 * .3) < 1e-9);
  assert.equal(b.x, .5); assert.equal(b.y, .8);
});

console.log(`${pass} passed`);
