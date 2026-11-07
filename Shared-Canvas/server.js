// Shared Canvas local server. No packages needed: Node 18 or newer.
//   node server.js   ->   http://localhost:3000          (station)
//                         http://localhost:3000/?gallery (gallery screen)
const http = require('http');
const fs = require('fs');
const path = require('path');

// ---- Load .env (simple KEY=value lines) ----
const envFile = path.join(__dirname, '.env');
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
}
const PORT = Number(process.env.PORT || 3000);
const PUBLIC = path.join(__dirname, 'public');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
                '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.json': 'application/json' };

// ---- Feeling -> paint, via the LLM ----
const BRUSH_PROMPT = `You mix paint for a shared painting that strangers make together at an event.
Read how one person feels and choose their paint. Return JSON only, no other text:
{ "palette_index": 0-4 (0 coral, 1 golden, 2 sage, 3 sky blue, 4 lilac),
  "shape": "ribbon" | "bloom" | "wash" | "scatter",
  "energy": 0 to 1, "size": 0 to 1,
  "reason": "3 to 5 words naming the paint, like 'golden blossoms' or 'restless coral flecks'" }
ribbon = long flowing strokes, bloom = blossoms (warmth, joy), wash = soft glazes (calm, tired),
scatter = flecks (excited, nervous, chaotic). Energy follows how intense the feeling is.
Feeling: `;

// Pick the provider in .env with LLM_PROVIDER = gemini (default) | vertex | anthropic
const PROVIDER = (process.env.LLM_PROVIDER || 'gemini').toLowerCase();

function brushFromLLM(feeling) {
  const prompt = BRUSH_PROMPT + JSON.stringify(String(feeling).slice(0, 200));
  if (PROVIDER === 'anthropic') return brushFromClaude(prompt);
  return brushFromGemini(prompt);
}

function parseJSON(text) {
  return JSON.parse(text.slice(text.indexOf('{'), text.lastIndexOf('}') + 1));
}

// ---- Google: Gemini API (one API key) or Vertex AI (your Cloud project, via gcloud) ----
// Same request body for both; only the URL and the auth header differ.
const { execSync } = require('child_process');
let vertexToken = null, vertexTokenAt = 0;
function getVertexToken() {
  if (!vertexToken || Date.now() - vertexTokenAt > 45 * 60 * 1000) {   // tokens last about an hour
    vertexToken = execSync('gcloud auth print-access-token', { encoding: 'utf8' }).trim();
    vertexTokenAt = Date.now();
  }
  return vertexToken;
}

async function brushFromGemini(prompt) {
  const model = process.env.GEMINI_MODEL || 'gemini-3.5-flash-lite';
  let url, headers = { 'content-type': 'application/json' };
  if (PROVIDER === 'vertex') {
    const project = process.env.GOOGLE_CLOUD_PROJECT;
    const loc = process.env.GOOGLE_CLOUD_LOCATION || 'global';
    if (!project) throw new Error('No GOOGLE_CLOUD_PROJECT in .env');
    const host = loc === 'global' ? 'aiplatform.googleapis.com' : `${loc}-aiplatform.googleapis.com`;
    url = `https://${host}/v1/projects/${project}/locations/${loc}/publishers/google/models/${model}:generateContent`;
    headers.authorization = `Bearer ${getVertexToken()}`;
  } else {
    const key = process.env.GEMINI_API_KEY;
    if (!key) throw new Error('No GEMINI_API_KEY in .env');
    url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
    headers['x-goog-api-key'] = key;
  }
  const r = await fetch(url, {
    method: 'POST', headers,
    body: JSON.stringify({
      contents: [{ role: 'user', parts: [{ text: prompt }] }],
      generationConfig: { responseMimeType: 'application/json', temperature: 0.8, maxOutputTokens: 300 }
    })
  });
  if (!r.ok) {
    if (r.status === 401) vertexToken = null;   // refresh the gcloud token next time
    throw new Error(`Gemini ${r.status}: ${(await r.text()).slice(0, 300)}`);
  }
  const data = await r.json();
  const parts = (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts) || [];
  return parseJSON(parts.map(p => p.text || '').join(''));
}

// ---- Anthropic: Claude ----
async function brushFromClaude(prompt) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error('No ANTHROPIC_API_KEY in .env');
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({
      model: process.env.LLM_MODEL || 'claude-haiku-5-5',
      max_tokens: 200,
      messages: [{ role: 'user', content: prompt }]
    })
  });
  if (!r.ok) throw new Error(`Claude ${r.status}: ${(await r.text()).slice(0, 300)}`);
  const data = await r.json();
  return parseJSON((data.content || []).map(c => c.text || '').join(''));
}

function llmStatus() {
  if (PROVIDER === 'anthropic') return process.env.ANTHROPIC_API_KEY ? 'Claude (connected)' : 'not set (local paint mixer)';
  if (PROVIDER === 'vertex') return process.env.GOOGLE_CLOUD_PROJECT ? `Vertex AI, project ${process.env.GOOGLE_CLOUD_PROJECT}` : 'Vertex AI, but GOOGLE_CLOUD_PROJECT is missing';
  return process.env.GEMINI_API_KEY ? `Gemini API, ${process.env.GEMINI_MODEL || 'gemini-3.5-flash-lite'}` : 'not set (local paint mixer)';
}

function send(res, status, body, type = 'application/json') {
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store' });
  res.end(typeof body === 'string' ? body : JSON.stringify(body));
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  // Public config for the browser. The Supabase anon key is meant to be public;
  // row-level security decides what it can do. Never put the LLM key here.
  if (url.pathname === '/config.js') {
    const cfg = { supabaseUrl: process.env.SUPABASE_URL || '', supabaseKey: process.env.SUPABASE_ANON_KEY || '' };
    return send(res, 200, `window.CANVAS_CONFIG = ${JSON.stringify(cfg)};`, 'text/javascript');
  }

  if (url.pathname === '/api/brush' && req.method === 'POST') {
    let body = '';
    req.on('data', c => { body += c; if (body.length > 10000) req.destroy(); });
    req.on('end', async () => {
      try {
        const { feeling } = JSON.parse(body || '{}');
        const brush = await brushFromLLM(feeling || '');
        console.log(`brush  "${feeling}" -> ${brush.reason}`);
        send(res, 200, brush);
      } catch (e) {
        console.warn('brush fallback:', e.message);
        send(res, 503, { error: e.message });   // the page falls back to its local mixer
      }
    });
    return;
  }

  // Static files from public/
  let file = path.join(PUBLIC, decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname));
  if (!file.startsWith(PUBLIC)) return send(res, 403, 'Forbidden', 'text/plain');
  fs.readFile(file, (err, data) => {
    if (err) return send(res, 404, 'Not found', 'text/plain');
    send(res, 200, data, TYPES[path.extname(file)] || 'application/octet-stream');
  });
}).listen(PORT, () => {
  console.log(`\nShared Canvas running`);
  console.log(`  Station:  http://localhost:${PORT}`);
  console.log(`  Gallery:  http://localhost:${PORT}/?gallery`);
  console.log(`  Supabase: ${process.env.SUPABASE_URL ? 'connected' : 'not set (single-station mode)'}`);
  console.log(`  LLM:      ${llmStatus()}\n`);
});