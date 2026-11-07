#!/usr/bin/env bash
# Runs ON the GPU VM (copied there by deploy). Installs the lab's Python deps and runs lab_service.py as a
# systemd service, so it survives disconnects and restarts after a VM reboot.
#   usage: LAB_TOKEN=<token> bash setup_vm.sh
set -euo pipefail
: "${LAB_TOKEN:?set LAB_TOKEN}"
PY=$(command -v python3)
echo "== python: $PY"
$PY -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
DEPS='diffusers==0.31.0 transformers==4.46.3 accelerate==1.1.1 fastapi uvicorn opencv-python-headless'
$PY -m pip install -q $DEPS 2>/dev/null || $PY -m pip install -q --break-system-packages $DEPS
sudo tee /etc/systemd/system/living-canvas-lab.service >/dev/null <<UNIT
[Unit]
Description=Living Canvas lab server
After=network-online.target

[Service]
User=$USER
WorkingDirectory=$HOME
Environment=LAB_TOKEN=$LAB_TOKEN
Environment=PYTHONUNBUFFERED=1
ExecStart=$PY $HOME/lab_service.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now living-canvas-lab.service
echo "== service started; first start downloads ~12 GB of models (5-10 min). Follow with:"
echo "   sudo journalctl -u living-canvas-lab -f"
