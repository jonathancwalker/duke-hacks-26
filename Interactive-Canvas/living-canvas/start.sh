#!/usr/bin/env bash
# Living Canvas: start everything for a booth night with one command.
#   1. starts the GPU VM   2. opens the SSH tunnel to the lab (localhost:8765)
#   3. waits until the lab answers   4. runs the booth server (localhost:8790) in this terminal
# Ctrl-C stops the booth and the tunnel. The VM keeps running (and billing) until ./stop.sh.
#
#   usage: ./start.sh [--dry-run]
#     --dry-run   print each command instead of running it; starts nothing
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
PROJECT=hackathon-514014
VM=living-canvas-gpu
ZONE=$(cat "$HERE/experiments/gcp/.zone" 2>/dev/null || echo us-central1-b)
LAB_PORT=8765
BOOTH_PORT=${BOOTH_PORT:-8790}
LAB_WAIT_S=${LAB_WAIT_S:-900}   # first boot downloads the models; later boots take 2-3 min
GC=(--zone "$ZONE" --project "$PROJECT")

DRY=0
case "${1:-}" in
  --dry-run) DRY=1 ;;
  "") ;;
  -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
  *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
esac

say()  { printf '\n== %s\n' "$*"; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
need() { if [ "$DRY" = 1 ]; then printf 'check failed (dry run continues): %s\n' "$*"; else die "$@"; fi; }
show() { printf '+'; printf ' %q' "$@"; printf '\n'; }
run()  { show "$@"; [ "$DRY" = 1 ] || "$@"; }
listening() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
lab_ok()    { curl -fsS --max-time 3 "http://localhost:$LAB_PORT/health" >/dev/null 2>&1; }

# ---------------------------------------------------------------- preflight
say "Checking this laptop"
command -v gcloud >/dev/null || die "gcloud is not installed (https://cloud.google.com/sdk/docs/install)"
for t in curl lsof python3; do command -v "$t" >/dev/null || die "$t is not installed"; done
[ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)" ] \
  || need "gcloud is not signed in: run  gcloud auth login"
gcloud auth application-default print-access-token >/dev/null 2>&1 \
  || echo "warning: no Gemini credentials; the booth falls back to rules. Fix: gcloud auth application-default login"
[ -f "$HERE/experiments/.lab.json" ] \
  || need "experiments/.lab.json is missing (it holds the lab token and is not in git; ask the team)"
if listening "$BOOTH_PORT"; then need "port $BOOTH_PORT is busy (a booth already running?). Run ./stop.sh --keep-vm first"; fi
PY="$HERE/booth/.venv/bin/python"
if [ ! -x "$PY" ]; then
  say "First run: setting up the booth's Python environment (torch is a large download)"
  run python3 -m venv "$HERE/booth/.venv"
  run "$PY" -m pip install -q -r "$HERE/booth/requirements.txt"
elif ! "$PY" -c "import google.genai, torch, transformers, numpy" 2>/dev/null; then
  say "Adding the booth's new Python packages (booth/requirements.txt; torch is a large download)"
  run "$PY" -m pip install -q -r "$HERE/booth/requirements.txt"
fi

# Presence scorer (picks the vibe painters): its library is built from ArtEmis data, which is not in git.
PRESENCE_LIB=${PRESENCE_DIR:-$HOME/.cache/living-canvas/presence}/presence_library.npz
[ -f "$PRESENCE_LIB" ] \
  || echo "warning: no presence library at $PRESENCE_LIB; the Gemini director picks the painters. Build it once: see presence/README.md"
# Its CLIP text model (~4 GB) is fetched once, here, so the first visitor does not wait for the download.
CLIP_ID=laion/CLIP-ViT-H-14-laion2B-s32B-b79K
if [ ! -d "${HF_HOME:-$HOME/.cache/huggingface}/hub/models--${CLIP_ID//\//--}" ]; then
  say "First run: downloading the CLIP text model for the presence scorer (~4 GB)"
  run "$PY" -c "from transformers import CLIPTextModelWithProjection, CLIPTokenizer as T; T.from_pretrained('$CLIP_ID'); CLIPTextModelWithProjection.from_pretrained('$CLIP_ID')"
fi

# ---------------------------------------------------------------- 1. GPU VM
say "Starting the GPU VM ($VM, about \$0.85/hr while running)"
run gcloud compute instances start "$VM" "${GC[@]}"   # no-op if already running; returns once it is RUNNING

# ---------------------------------------------------------------- 2-3. tunnel + wait for the lab
TUNNEL_PID=""
BOOTH_PID=""
cleanup() {
  [ -n "$BOOTH_PID" ] && kill "$BOOTH_PID" 2>/dev/null
  # gcloud runs ssh as a child: stop both so the tunnel port is freed
  [ -n "$TUNNEL_PID" ] && { pkill -P "$TUNNEL_PID" 2>/dev/null; kill "$TUNNEL_PID" 2>/dev/null; }
  printf '\nBooth and tunnel stopped. The GPU VM is still running: ./stop.sh to stop billing.\n'
}
trap cleanup EXIT
trap 'exit 130' INT TERM

open_tunnel() {
  gcloud compute ssh "$VM" "${GC[@]}" --quiet -- -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -L "$LAB_PORT:localhost:$LAB_PORT" &
  TUNNEL_PID=$!
}

say "Opening the tunnel to the lab (localhost:$LAB_PORT)"
if [ "$DRY" = 1 ]; then
  show gcloud compute ssh "$VM" "${GC[@]}" --quiet -- -N -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -L "$LAB_PORT:localhost:$LAB_PORT" '&'
  show curl -fsS "http://localhost:$LAB_PORT/health"
  echo "  (repeated every 5s, reopening the tunnel if it drops, until the lab answers; up to ${LAB_WAIT_S}s)"
elif lab_ok; then
  echo "a tunnel is already open and the lab answers; reusing it"
else
  listening "$LAB_PORT" && die "port $LAB_PORT is busy but the lab does not answer. Run ./stop.sh --keep-vm, then retry"
  echo "waiting for the lab (models take 2-3 min to load after boot)..."
  deadline=$((SECONDS + LAB_WAIT_S))
  until lab_ok; do
    # sshd may not be up right after boot: reopen the tunnel whenever it has exited
    if [ -z "$TUNNEL_PID" ] || ! kill -0 "$TUNNEL_PID" 2>/dev/null; then open_tunnel; fi
    [ "$SECONDS" -lt "$deadline" ] || die "the lab did not answer within ${LAB_WAIT_S}s. Check its log (see OPERATOR.md)"
    sleep 5
  done
  echo "lab is up: $(curl -fsS --max-time 3 "http://localhost:$LAB_PORT/health")"
fi

# ---------------------------------------------------------------- 4. booth server
say "Starting the booth: open http://localhost:$BOOTH_PORT/vibe in Chrome"
if [ "$DRY" = 1 ]; then
  show env BOOTH_GCP_PROJECT="$PROJECT" BOOTH_PORT="$BOOTH_PORT" "$HERE/booth/.venv/bin/python" "$HERE/booth/booth_server.py"
  trap - EXIT
  exit 0
fi
BOOTH_GCP_PROJECT=$PROJECT BOOTH_PORT=$BOOTH_PORT "$HERE/booth/.venv/bin/python" "$HERE/booth/booth_server.py" &
BOOTH_PID=$!
wait "$BOOTH_PID"
