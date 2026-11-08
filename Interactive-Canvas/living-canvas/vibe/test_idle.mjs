// The idle loop (#37): what the station replays when nobody is visiting, and when it starts.
//     node vibe/test_idle.mjs
import assert from 'node:assert/strict';
import { idlePlan, idleTimer, IDLE_MS, SLOT_MS, HOLD_MS } from './idle_plan.js';

let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };

const id = n => String(n).padStart(4, '0');
const visit = (n, extra = {}) => ({ id: id(n), reading: `reading ${n}`, name: null,
  strokes: [[{ x: 10, y: 10, t: 0 }, { x: 50, y: 40, t: 1 }]], canvas: `/visits/${id(n)}-canvas.jpg`, ...extra });
const night = n => Array.from({ length: n }, (_, i) => visit(i + 1, i ? {} : { before: '/visits/0001-before.jpg' }));

test('with 7 saved visits, the loop replays visits 3 to 7 in order', () => {
  const p = idlePlan(night(7));
  assert.deepEqual(p.steps.map(s => s.visit.id), ['0003', '0004', '0005', '0006', '0007']);
});

test('visit 3 reveals over visit 2’s canvas, and the loop ends holding visit 7’s canvas', () => {
  const p = idlePlan(night(7));
  assert.equal(p.steps[0].before, '/visits/0002-canvas.jpg');
  assert.equal(p.steps[1].before, '/visits/0003-canvas.jpg');
  assert.equal(p.final, '/visits/0007-canvas.jpg');
});

test('each visit gets about 1.5 s, then the canvas holds about 5 s', () => {
  const p = idlePlan(night(7));
  assert.ok(p.steps.every(s => s.ms === SLOT_MS), 'every slot is SLOT_MS');
  assert.ok(SLOT_MS >= 1200 && SLOT_MS <= 1800, `slot ${SLOT_MS} ms`);
  assert.deepEqual(p.steps.map(s => s.at), [0, 1, 2, 3, 4].map(i => i * SLOT_MS));
  assert.equal(p.finalAt, 5 * SLOT_MS);
  assert.equal(p.total, 5 * SLOT_MS + HOLD_MS);
});

test('nothing on screen holds still for 10 s: the hold and every slot are under 10 s', () => {
  assert.ok(HOLD_MS < 10000 && SLOT_MS < 10000);
  assert.ok(IDLE_MS < 10000, 'the loop starts within 10 s of the last interaction');
});

test('with 1 visit, it replays that visit over the night’s starting canvas', () => {
  const p = idlePlan(night(1));
  assert.equal(p.steps.length, 1);
  assert.equal(p.steps[0].before, '/visits/0001-before.jpg');
  assert.equal(p.steps[0].caption, 'reading 1');
  assert.equal(p.steps[0].name, 'Visitor 1');
});

test('captions carry the saved name and reading', () => {
  const p = idlePlan([...night(2), visit(3, { name: 'Ada' })]);
  assert.equal(p.steps[2].name, 'Ada');
  assert.equal(p.steps[2].caption, 'reading 3');
});

test('a missing canvas before the replayed visits falls back to the last one that was saved', () => {
  const v = night(7); v[1].canvas = null;   // visit 2's canvas failed to save
  assert.equal(idlePlan(v).steps[0].before, '/visits/0001-canvas.jpg');
});

test('with 0 visits (or no list at all), the plan is empty', () => {
  for (const v of [[], null, undefined]) {
    const p = idlePlan(v);
    assert.equal(p.steps.length, 0);
    assert.equal(p.final, null);
  }
});

// A fake clock for the timer.
function clock() {
  let now = 0, next = 1; const due = new Map();
  return {
    setTimeout: (fn, ms) => { due.set(next, { fn, at: now + ms }); return next++; },
    clearTimeout: h => due.delete(h),
    advance(ms) {
      const end = now + ms;
      for (;;) {
        const [h, t] = [...due].filter(([, t]) => t.at <= end).sort((a, b) => a[1].at - b[1].at)[0] || [];
        if (!t) break;
        due.delete(h); now = t.at; t.fn();
      }
      now = end;
    },
  };
}

test('the idle timer fires at 8 s', () => {
  const c = clock(); let fired = 0;
  const t = idleTimer(() => fired++, c); t.poke();
  c.advance(IDLE_MS - 1); assert.equal(fired, 0, 'not before 8 s');
  c.advance(1); assert.equal(fired, 1, 'at 8 s');
  assert.equal(IDLE_MS, 8000);
});

test('an interaction restarts the 8 s wait', () => {
  const c = clock(); let fired = 0;
  const t = idleTimer(() => fired++, c); t.poke();
  c.advance(7000); t.poke();
  c.advance(7000); assert.equal(fired, 0, 'the click at 7 s pushed it back');
  c.advance(1000); assert.equal(fired, 1);
});

test('cancel stops it for good, until the next poke', () => {
  const c = clock(); let fired = 0;
  const t = idleTimer(() => fired++, c); t.poke(); t.cancel();
  c.advance(60000); assert.equal(fired, 0);
  t.poke(); c.advance(IDLE_MS); assert.equal(fired, 1);
});

console.log(`${pass} passed`);
