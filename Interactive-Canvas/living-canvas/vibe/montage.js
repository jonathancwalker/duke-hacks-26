// /montage: tonight's visits replayed fast (montage_play.js), then a hold on the night's final canvas. ?loop replays
// forever, picking up new visits each time (for the projector).
import { $, sleep } from './state.js';
import { fit } from './render.js';
import { playMontage } from './montage_play.js';
import { FINAL_MS } from './montage_plan.js';

const LOOP = new URLSearchParams(location.search).has('loop');

addEventListener('resize', fit);

async function play() {
  $('#again').disabled = true;
  const { visits } = await playMontage();
  if (visits) await sleep(FINAL_MS);
  return finish();
}

// Loop mode tries again (picking up new visits; after an empty or failed load, a few seconds later); otherwise the
// operator can press Play again.
async function finish() {
  $('#again').disabled = false;
  if (LOOP) { await sleep(FINAL_MS); if (!$('#again').disabled) return play(); }   // disabled: Play again already started one
}

$('#again').onclick = () => play();
addEventListener('keydown', e => { if (e.code === 'Space' && !$('#again').disabled) { e.preventDefault(); play(); } });
play();
