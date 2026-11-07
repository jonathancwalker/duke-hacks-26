# Living Canvas GPU on Google Cloud

- **VM:** `living-canvas-gpu` in project `hackathon-514014`, zone in `.zone` (currently `us-central1-b`)
- **Machine:** `g2-standard-8`, 1× NVIDIA L4, Deep Learning VM (PyTorch 2.9, CUDA 12.9)
- **Cost:** about $0.85/hr while running, plus the 150 GB disk while stopped. Billed to the Education credits.
- **Service:** `living-canvas-lab` (systemd) runs `lab_service.py` and starts on boot. Models load in about 2–3 min; the first boot also downloads them.
- **Access:** localhost only on the VM. The booth reaches it through an SSH tunnel; nothing is public.

## Daily use

Start the VM (the lab service starts itself):

```bash
gcloud compute instances start living-canvas-gpu --zone us-central1-b --project hackathon-514014
```

Open the tunnel from the booth laptop and leave it running:

```bash
gcloud compute ssh living-canvas-gpu --zone us-central1-b --project hackathon-514014 -- -N -o ServerAliveInterval=30 -L 8765:localhost:8765
```

Check it (from `experiments/`):

```bash
python3 lab.py --health
```

Stop the VM when you're done (stops GPU billing; the disk keeps the models):

```bash
gcloud compute instances stop living-canvas-gpu --zone us-central1-b --project hackathon-514014
```

Watch the service log:

```bash
gcloud compute ssh living-canvas-gpu --zone us-central1-b --project hackathon-514014 --command "sudo journalctl -u living-canvas-lab -f"
```

## Connection files (in `experiments/`, gitignored)

- `.lab.json`: what the booth and `lab.py` use. Currently the GCP lab (`http://localhost:8765` + token).
- `.lab.gcp.json` / `.lab.colab.json`: copy one over `.lab.json` to switch.

## Updating the lab code

`lab_service.py` is generated from `../lab_server.ipynb`. Edit the notebook, regenerate, then copy it to the VM and restart:

```bash
gcloud compute scp lab_service.py living-canvas-gpu:~ --zone us-central1-b --project hackathon-514014
```

```bash
gcloud compute ssh living-canvas-gpu --zone us-central1-b --project hackathon-514014 --command "sudo systemctl restart living-canvas-lab"
```
