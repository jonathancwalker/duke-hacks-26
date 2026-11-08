// "What name should we credit?" after the reveal (#30). The visitor says a name, or skips: the Skip button, the space
// key, saying "skip", or about 5 s of silence. Resolves with the cleaned name, or '' for a skip (the server then credits
// "Visitor N"). It never rejects and gives up after LISTEN_MAX_S, so a visit always finishes; speech failing is a skip.
import { $, say, sleep } from './state.js';
import { cleanName, creditName } from './name_text.js';

const SILENCE_S = 5, LISTEN_MAX_S = 12, THANKS_MS = 1400;
const SIM_NAMES = ['Ada', 'Rachel Chen', 'Sam', '', ''];   // Simulate: a pretend name, or a skip

// n: this visit's number (for the "Visitor N" thanks); sim: a pretend visitor, so no mic.
export async function askName(n, sim) {
  let done, heard = '';
  const answer = new Promise(r => { done = r; });
  say('What name should we credit?', 'Say your first name, or skip.');
  const skip = Object.assign(document.createElement('button'), { id: 'skip', textContent: 'Skip' });
  skip.onclick = () => done('');
  $('#sub').append(' ', skip);
  const onKey = e => { if (e.code === 'Space') { e.preventDefault(); done(''); } };
  addEventListener('keydown', onKey);
  const show = t => { heard = t; $('#sub').firstChild.textContent = `“${t}” `; };

  let silence = setTimeout(() => done(''), SILENCE_S * 1000);
  const cap = setTimeout(() => done(cleanName(heard)), LISTEN_MAX_S * 1000);
  let rec = null;
  try {
    if (sim) {
      const pick = SIM_NAMES[Math.floor(Math.random() * SIM_NAMES.length)];
      sleep(1200).then(() => { if (pick) show(pick); done(pick); });
    } else {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) done('');
      else {
        rec = new SR(); rec.continuous = false; rec.interimResults = true; rec.lang = 'en-US';
        rec.onresult = e => {
          clearTimeout(silence); silence = null;                 // they're talking: wait for them to finish
          const r = e.results[e.results.length - 1];
          show(r[0].transcript.trim());
          if (r.isFinal) done(cleanName(heard));
        };
        rec.onerror = e => { console.warn('name not heard:', e.error); done(''); };
        rec.onend = () => done(cleanName(heard));                // silence ends it too; nothing heard is a skip
        rec.start();
      }
    }
  } catch (e) { console.warn('name step failed, skipping:', e); done(''); }

  const name = await answer;
  clearTimeout(silence); clearTimeout(cap); removeEventListener('keydown', onKey);
  if (rec) { rec.onresult = rec.onerror = rec.onend = null; try { rec.abort(); } catch {} }
  skip.remove();
  say(`Thanks, ${creditName(name, n)}.`, '');
  await sleep(THANKS_MS);
  return name;
}
