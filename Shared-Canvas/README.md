# Shared Canvas

One painting, made by everyone in the room. People say how they feel, an LLM mixes their paint,
and they paint for 10 seconds with their hands, face and voice in the style of Van Gogh, Monet or Seurat.

## Run it (about 15 minutes the first time)

1. **Install Node 18 or newer.** Check with `node -v`. Nothing else to install.
2. **Create the database.** Make a free project at supabase.com. Open SQL Editor, paste all of
   `supabase.sql`, and click Run.
3. **Add your keys.** Copy `.env.example` to `.env`. From Supabase > Project Settings > API, paste the
   Project URL and the anon public key. Add your LLM API key.
4. **Start it.** In this folder run `node server.js`.
5. **Open it in Chrome.**
   - Station: `http://localhost:3000` (allow camera and mic)
   - Gallery screen: `http://localhost:3000/?gallery`

The terminal tells you whether Supabase and the LLM are connected. Both are optional: without
Supabase it runs as a single station, and without an LLM key it uses the built-in paint mixer.

## Every laptop runs its own copy

Camera and mic only work on `localhost` in a browser on the same machine. So copy this folder
(with your `.env`) to each station laptop and to the gallery laptop, and run `node server.js` on each.
They share one painting through Supabase.

## Gallery keys

- **F** fullscreen
- **S** group snapshot (3-second countdown), which becomes the hidden picture
- **R** reveal: shows every connection and replays the whole painting with its song

## Station shortcuts

- **`** (backquote) shows or hides which models have loaded
- "Add 12 test people" adds local test strokes only. They are not saved to the shared painting.
- "Clear canvas" clears this screen only. To wipe the shared painting, run
  `delete from contributions;` in Supabase.

## Test checklist

- [ ] Terminal says Supabase connected and LLM connected
- [ ] Paint once at a station; the terminal logs the paint the LLM chose
- [ ] The stroke appears on the gallery screen a moment later
- [ ] Refresh the gallery; the painting rebuilds itself
- [ ] Paint at a second station; both screens show both strokes
- [ ] Press S then R on the gallery for the full reveal
