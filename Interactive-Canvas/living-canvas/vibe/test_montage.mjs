// The montage schedule (issue #31): every saved visit in order, about a second each, ending on the final canvas.
//     node vibe/test_montage.mjs
import assert from 'node:assert/strict';
import { plan } from './montage_plan.js';

const visit = (n, extra = {}) => ({ id: String(n).padStart(4, '0'), reading: `reading ${n}`, name: null,
  strokes: [[{ x: 10, y: 10, t: 0 }, { x: 50, y: 40, t: 1 }]], canvas: `/visits/${String(n).padStart(4, '0')}-canvas.jpg`, ...extra });

// 50 visits play in under a minute and end on visit 50's canvas.
{
  const visits = Array.from({ length: 50 }, (_, i) => visit(i + 1));
  visits[0].before = '/visits/0001-before.jpg';
  const p = plan(visits);
  assert.equal(p.steps.length, 50, 'one step per visit');
  assert.ok(p.total < 60000, `50 visits take ${p.total} ms, want under 60 s`);
  assert.ok(p.steps.every(s => s.ms >= 800 && s.ms <= 1000), 'about a second each');
  assert.deepEqual(p.steps.map(s => s.visit.id), visits.map(v => v.id), 'in saved order');
  assert.equal(p.final, '/visits/0050-canvas.jpg', 'ends on visit 50’s canvas');
  assert.equal(p.steps[0].before, '/visits/0001-before.jpg', 'visit 1 reveals over the canvas as it was before it');
  assert.equal(p.steps[1].before, '/visits/0001-canvas.jpg', 'visit 2 reveals over visit 1’s canvas');
  assert.equal(p.steps.at(-1).at + p.steps.at(-1).ms, p.finalAt, 'the final canvas follows the last visit');
  assert.ok(p.finalAt < p.total, 'the final canvas holds before the end');
}

// A long night still fits in a minute: 200 visits get shorter slots.
{
  const p = plan(Array.from({ length: 200 }, (_, i) => visit(i + 1)));
  assert.ok(p.total <= 60000, `200 visits take ${p.total} ms`);
  assert.equal(p.final, '/visits/0200-canvas.jpg');
}

// The caption is the reading, plus the name when one is stored.
{
  const p = plan([visit(1, { name: 'Ada' }), visit(2)]);
  assert.equal(p.steps[0].caption, 'reading 1');
  assert.equal(p.steps[0].name, 'Ada');
  assert.equal(p.steps[1].name, 'Visitor 2', 'a visit saved without a name is credited by its number');
}

// No reading (the rule-based director gives none): the caption names the painters instead.
{
  const p = plan([visit(1, { reading: '', painters: [{ name: 'Claude Monet, Water Lilies' }, { name: 'J. M. W. Turner' }] })]);
  assert.equal(p.steps[0].caption, 'after Claude Monet, J. M. W. Turner');
}

// A visit whose canvas image failed to save keeps the previous canvas as the next one's starting point.
{
  const p = plan([visit(1), visit(2, { canvas: null }), visit(3)]);
  assert.equal(p.steps[2].before, '/visits/0001-canvas.jpg');
  assert.equal(p.final, '/visits/0003-canvas.jpg');
}

// No visits: nothing to play.
{
  const p = plan([]);
  assert.equal(p.steps.length, 0);
  assert.equal(p.final, null);
  assert.equal(p.total, 0);
}

console.log('montage plan: ok');
