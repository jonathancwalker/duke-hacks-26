// Event setup (#66): what happens after "Save and go live" before the station opens.
//     node vibe/test_setup.mjs
import assert from 'node:assert/strict';
import { freshNightAsk } from './setup_plan.js';

let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };

test('switching from Duke Chapel Night to Duke Jazz Night with 12 visits asks to start fresh', () => {
  const ask = freshNightAsk({ wasLive: 'museum', nowLive: 'duke-jazz-night', name: 'Duke Jazz Night', visits: 12 });
  assert.match(ask, /Duke Jazz Night/);
  assert.match(ask, /12 visits/);
});

test('one visit is singular', () => {
  assert.match(freshNightAsk({ wasLive: 'museum', nowLive: 'concert', name: 'Concert Night', visits: 1 }), /1 visit\b/);
});

test('re-saving the live event keeps tonight’s painting without asking', () => {
  assert.equal(freshNightAsk({ wasLive: 'concert', nowLive: 'concert', name: 'Concert Night', visits: 12 }), null);
});

test('a new event on an empty night needs no question', () => {
  assert.equal(freshNightAsk({ wasLive: 'museum', nowLive: 'concert', name: 'Concert Night', visits: 0 }), null);
});

console.log(`${pass} passed`);
