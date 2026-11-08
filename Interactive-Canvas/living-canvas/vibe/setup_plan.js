// Event setup (#66): the decision after "Save and go live", before the station opens. Pure (no DOM), so node can
// test it: node vibe/test_setup.mjs.

// Tonight's painting was built on the old event's scene. When the live event changes and there are visits, ask
// whether to start a fresh night (visits are moved aside, not deleted) so the station opens on the new base scene.
// Returns the question, or null when there is nothing to ask.
export function freshNightAsk({ wasLive, nowLive, name, visits }) {
  if (!visits || wasLive === nowLive) return null;
  return `${name} is live. Tonight’s painting has ${visits} visit${visits === 1 ? '' : 's'} on the old scene.\n\n`
    + 'Start a fresh night on the new scene? (OK: those visits are moved aside, not deleted. Cancel: keep painting on top.)';
}
