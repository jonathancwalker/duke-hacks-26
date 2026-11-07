// Listening: Web Speech transcript plus mic loudness -> { feeling, arousal }.
import { bar, meter, lin, frame, sleep } from './state.js';

export async function listen(sec) {
  let text = '', interim = '', rec = null, ended = Promise.resolve();
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR) {
    rec = new SR(); rec.continuous = true; rec.interimResults = true; rec.lang = 'en-US';
    rec.onresult = e => { interim = ''; for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i]; if (r.isFinal) text += r[0].transcript + ' '; else interim += r[0].transcript; } };
    ended = new Promise(r => { rec.onend = r; rec.onerror = r; });
    try { rec.start(); } catch {}
  }
  let stream, ac, an; const levels = [], buf = new Float32Array(2048);
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { autoGainControl: false, noiseSuppression: false, echoCancellation: false } });
    ac = new AudioContext(); an = ac.createAnalyser(); an.fftSize = 2048; ac.createMediaStreamSource(stream).connect(an);
  } catch {}
  const t0 = performance.now();
  for (let t = 0; t < sec; t = (performance.now() - t0) / 1000) {
    bar(t / sec);
    if (an) { an.getFloatTimeDomainData(buf); let s = 0; for (const v of buf) s += v * v;
      const db = 10 * Math.log10(s / buf.length + 1e-12); levels.push(db); meter(lin(db, -55, -20)); }
    await frame();
  }
  meter(0);
  if (rec) { try { rec.stop(); } catch {} await Promise.race([ended, sleep(1500)]); }
  stream?.getTracks().forEach(t => t.stop()); ac?.close();
  const voiced = levels.filter(d => d > -50).sort((a, b) => a - b);
  const p90 = voiced.length ? voiced[Math.floor(voiced.length * .9)] : -60;
  return { feeling: (text + interim).trim(), arousal: voiced.length > 10 ? lin(p90, -41, -25) : 0.3 };
}
