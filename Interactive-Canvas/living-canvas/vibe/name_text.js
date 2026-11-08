// What a spoken answer to "What name should we credit?" becomes (#30). Pure (no DOM), so node can test it:
// node vibe/test_name.mjs. The booth server checks the result again (credit_name) before saving it.
export const NAME_MAX = 24;

// How long the name prompt listens: SILENCE_S of silence is a skip; once they talk, it stops at LISTEN_MAX_S.
export const SILENCE_S = 5, LISTEN_MAX_S = 12;

// The time bar under the painting while the prompt listens, 0..1. elapsed: seconds since the prompt; talkStart: when
// they started talking (null until then). Before they talk it fills over SILENCE_S; once they talk it carries on from
// where it was to full at LISTEN_MAX_S, so it never jumps back.
export function nameProgress(elapsed, talkStart) {
  const clamp = f => Math.max(0, Math.min(1, f));
  if (talkStart == null) return clamp(elapsed / SILENCE_S);
  const from = clamp(talkStart / SILENCE_S);
  if (talkStart >= LISTEN_MAX_S) return 1;
  return clamp(from + (1 - from) * (elapsed - talkStart) / (LISTEN_MAX_S - talkStart));
}

// Filler said before a name ("um, hi, my name is …"), peeled off the front one phrase at a time.
const FILLER = /^(?:um+|uh+|er+|so|okay|ok|well|hi|hello|hey|yeah|yes|sure|my name is|my name's|name's|the name is|i am|i'm|im|it is|it's|its|this is|call me|you can call me|just)\b[\s,.!?]*/i;
// Saying one of these skips, like the button.
const SKIP = /^(?:skip|pass|no|nope|no thanks|no thank you|none|nothing|anonymous|no name|not telling)$/i;

// transcript -> a short name, or '' for none. Trim, drop filler and punctuation, capitalize each word, and cut at a
// word boundary to about NAME_MAX characters (a single long word is cut hard).
export function cleanName(text) {
  let s = String(text ?? '').replace(/[’‘]/g, "'").replace(/\s+/g, ' ').trim();
  for (let prev; prev !== s;) { prev = s; s = s.replace(FILLER, '').trim(); }
  s = s.replace(/[^\p{L}\p{M}\s'-]/gu, ' ').replace(/\s+/g, ' ').replace(/^['-]+|['-]+$/g, '').trim();
  if (!s || SKIP.test(s)) return '';
  s = s.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  if (s.length <= NAME_MAX) return s;
  const cut = s.slice(0, NAME_MAX + 1).lastIndexOf(' ');
  return (cut > 0 ? s.slice(0, cut) : s.slice(0, NAME_MAX)).trim();
}

// The credit shown for a visit: its name, or "Visitor N" when they skipped.
export const creditName = (name, n) => name || `Visitor ${n}`;
