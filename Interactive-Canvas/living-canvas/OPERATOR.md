# Operator checklist

How to run the Living Canvas booth for a night. Allow 5 minutes; the GPU needs 2–3 of them to load.

## Once per laptop

- [ ] Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install) and Google Chrome.
- [ ] Sign in with the account that has access to project `hackathon-514014`:
  ```bash
  gcloud auth login
  ```
  ```bash
  gcloud auth application-default login
  ```
  The second one is what Gemini uses. Without it the booth still runs, on simple rules.
- [ ] Get `experiments/.lab.json` from the team (it holds the lab token; it is not in git, never commit it).
- [ ] macOS: **System Settings → Privacy & Security → Camera** and **Microphone**: turn on Google Chrome.

## At the venue

- [ ] Laptop on power, sleep off for the night (macOS: **System Settings → Displays / Lock Screen**).
- [ ] Wi-Fi works. The page needs the internet for hand tracking, speech, Gemini and the GPU.
- [ ] Webcam at chest-to-head height, facing the visitor, with light on their face and hands, not behind them.
- [ ] Mic close to where the visitor stands; keep it away from the speakers.
- [ ] Projector or second screen mirrored or extended, set as you like before starting.

## Start

From `Interactive-Canvas/living-canvas/`:

```bash
./start.sh
```

It starts the GPU VM, opens the tunnel to it, waits until the lab answers, then runs the booth in that terminal. Leave the terminal open. The first run on a laptop also sets up the booth's Python (`booth/.venv`, from `booth/requirements.txt`; torch is a large download) and downloads the presence scorer's CLIP text model (~4 GB). Run `./start.sh --dry-run` to see each command without starting anything.

The vibe painters come from the presence scorer. It loads about 10 s after the booth starts: the booth's log says `presence scorer ready`, and http://localhost:8790/api/health shows `"presence": "ready"`. If it says `unavailable`, the presence library is missing on this laptop (start.sh warns about that too; build it once, see `presence/README.md`). Visits still work then, with the Gemini director picking the painters.

Then in Chrome:

- [ ] Open http://localhost:8790/vibe (or `/` for the booth, `/brush` for the brush experiment).
- [ ] When Chrome asks, **Allow** camera and microphone. If you missed it: click the icon left of the address bar → turn on Camera and Microphone → reload.
- [ ] Wrong camera or mic? Same icon → **Site settings**, or `chrome://settings/content/camera` and `.../microphone`.
- [ ] Press **Simulate** once to check a full visit end to end, then go full screen (`Ctrl+Cmd+F` on macOS).

## If something breaks

- **Painting never changes / lab errors:** check the lab: `cd experiments && python3 lab.py --health`. Its log:
  ```bash
  gcloud compute ssh living-canvas-gpu --zone us-central1-b --project hackathon-514014 --command "sudo journalctl -u living-canvas-lab -f"
  ```
- **"port … is busy":** a previous booth or tunnel is still running. `./stop.sh --keep-vm`, then `./start.sh` again.
- **Tunnel dropped mid-night:** Ctrl-C the terminal and run `./start.sh` again. The VM keeps running, so it is quick.

## Stop (do this every night: the GPU costs about $0.85/hr while on)

- [ ] Ctrl-C in the `start.sh` terminal (stops the booth and the tunnel).
- [ ] Stop the VM:
  ```bash
  ./stop.sh
  ```
  It prints the VM status at the end; it should say `TERMINATED`. The disk keeps the models, so the next start is fast.
- [ ] Not sure it stopped? Check from any laptop:
  ```bash
  gcloud compute instances list --project hackathon-514014
  ```
