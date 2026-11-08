// Optional name per visit (#30): what a spoken answer to "What name should we credit?" becomes.
//     node vibe/test_name.mjs
import assert from 'node:assert/strict';
import { cleanName, creditName, NAME_MAX } from './name_text.js';

let pass = 0;
const test = (what, fn) => { fn(); pass++; console.log('ok -', what); };

test('filler before the name is dropped', () => {
  assert.equal(cleanName('my name is Rachel Chen'), 'Rachel Chen');
  assert.equal(cleanName("I'm Rachel"), 'Rachel');
  assert.equal(cleanName('I’m Rachel'), 'Rachel');
  assert.equal(cleanName('um, hi, it’s Sam.'), 'Sam');
  assert.equal(cleanName('you can call me Jo'), 'Jo');
  assert.equal(cleanName('this is Dev Patel'), 'Dev Patel');
});

test('a plain spoken name is kept and capitalized', () => {
  assert.equal(cleanName('  rachel chen  '), 'Rachel Chen');
  assert.equal(cleanName('Mary-Kate'), 'Mary-Kate');
  assert.equal(cleanName("o'brien"), "O'brien");
});

test('long names are cut at a word to about 24 characters', () => {
  const n = cleanName('Alexandria Ocasio Cortez Montgomery the Third');
  assert.ok(n.length <= NAME_MAX, n);
  assert.equal(n, 'Alexandria Ocasio Cortez');
  assert.equal(cleanName('Supercalifragilisticexpialidocious').length, NAME_MAX);
});

test('nothing said, or a skip word, is no name', () => {
  for (const s of ['', '   ', null, undefined, 'skip', 'no thanks', 'pass', 'my name is', 'um', 'nope', '...'])
    assert.equal(cleanName(s), '', JSON.stringify(s));
});

test('a skipped visit 23 is credited "Visitor 23"', () => {
  assert.equal(creditName('', 23), 'Visitor 23');
  assert.equal(creditName(null, 23), 'Visitor 23');
  assert.equal(creditName('Rachel Chen', 23), 'Rachel Chen');
});

console.log(`${pass} passed`);
