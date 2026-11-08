// Shared state, DOM handles and small helpers used by every vibe module.
export const $ = s => document.querySelector(s);
export const paint = $('#paint'), trail = $('#trail'), cursor = $('#cursor'), video = $('#cam');
export const pctx = paint.getContext('2d'), tctx = trail.getContext('2d'), cctx = cursor.getContext('2d');

// W/H: canvas size. base: the night's painting so far. start: 'chapel' (pale underpainting; your path repaints it),
// 'blank' (linen; your path reveals the chapel in your mood), 'abstract' (linen; your path lays down pure mood paint,
// no scene: the most varied).
export const S = { W: 768, H: 432, base: null, busy: false, visitors: 0, start: 'chapel' };
try { S.start = localStorage.getItem('vibe-start') || 'chapel'; } catch {}
export const blankStart = () => S.start !== 'chapel';

export const sleep = ms => new Promise(r => setTimeout(r, ms));
export const lin = (x, a, b) => Math.max(0, Math.min(1, (x - a) / (b - a)));
export const ease = t => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
export const mk = () => Object.assign(document.createElement('canvas'), { width: S.W, height: S.H });
export const say = (a, b = '') => { $('#say').textContent = a; $('#sub').textContent = b; };
export const bar = f => { $('#bar').style.width = (100 * Math.max(0, Math.min(1, f))) + '%'; };
export const meter = f => { $('#meter').style.width = (100 * f) + '%'; window.momento?.level?.('Vol', f); };   // + the station's Vol meter
export const frame = () => new Promise(r => requestAnimationFrame(r));
export const loadImg = src => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
