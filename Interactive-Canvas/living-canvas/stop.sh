#!/usr/bin/env bash
# Living Canvas: stop the booth server, the lab tunnel, and the GPU VM (stops GPU billing; the disk keeps the models).
#   usage: ./stop.sh [--keep-vm] [--dry-run]
#     --keep-vm   free the booth and tunnel ports but leave the VM running
#     --dry-run   print each command instead of running it
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
PROJECT=hackathon-514014
VM=living-canvas-gpu
ZONE=$(cat "$HERE/experiments/gcp/.zone" 2>/dev/null || echo us-central1-b)
LAB_PORT=8765
BOOTH_PORT=${BOOTH_PORT:-8790}

DRY=0
KEEP_VM=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --keep-vm) KEEP_VM=1 ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) echo "unknown option: $a (try --help)" >&2; exit 2 ;;
  esac
done

show() { printf '+'; printf ' %q' "$@"; printf '\n'; }
run()  { show "$@"; [ "$DRY" = 1 ] || "$@"; }

for port in "$BOOTH_PORT" "$LAB_PORT"; do
  pids=$(lsof -nP -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "== stopping what listens on localhost:$port"
    # shellcheck disable=SC2086  # one or more pids
    run kill $pids
  else
    echo "== nothing listening on localhost:$port"
  fi
done

if [ "$KEEP_VM" = 1 ]; then
  echo "== leaving the GPU VM running (still billing): ./stop.sh to stop it"
  exit 0
fi
echo "== stopping the GPU VM ($VM)"
run gcloud compute instances stop "$VM" --zone "$ZONE" --project "$PROJECT"
[ "$DRY" = 1 ] || echo "VM status: $(gcloud compute instances describe "$VM" --zone "$ZONE" --project "$PROJECT" --format='value(status)')"
