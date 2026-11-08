// What a spoken answer to "What name should we credit?" becomes (#30). Pure (no DOM), so node can test it:
// node vibe/test_name.mjs. The booth server checks the result again (credit_name) before saving it.
export const NAME_MAX = 24;

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
