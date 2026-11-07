#!/usr/bin/env python3
"""Living Canvas lab server for a GCP GPU VM. GENERATED from lab_server.ipynb by the experiments/gcp build step:
edit the notebook, then regenerate, so Colab and GCP never drift apart.

Listens on 127.0.0.1:8765 only. Reach it from the booth laptop through an SSH tunnel:
    gcloud compute ssh living-canvas-gpu --zone <zone> -- -N -L 8765:localhost:8765
"""
display = lambda *a, **k: None   # notebook display() calls become no-ops

# ---- models (notebook cell) ----
import torch, time, os, io, gc, re, json, base64, secrets, threading, subprocess, traceback, contextlib, textwrap, colorsys
import urllib.parse, urllib.request
import numpy as np, cv2
from PIL import Image, ImageDraw
from diffusers import (StableDiffusionXLControlNetPipeline, StableDiffusionXLControlNetImg2ImgPipeline,
                       StableDiffusionXLPipeline, ControlNetModel, AutoencoderKL)
from transformers import CLIPTextModelWithProjection, CLIPTokenizer
assert torch.cuda.is_available(), "No GPU. Runtime > Change runtime type > T4 GPU"
DEV, W, H = "cuda", 768, 432
t0 = time.time()
try:
    cn = ControlNetModel.from_pretrained("diffusers/controlnet-canny-sdxl-1.0", torch_dtype=torch.float16, variant="fp16")
except Exception:
    cn = ControlNetModel.from_pretrained("diffusers/controlnet-canny-sdxl-1.0", torch_dtype=torch.float16)
vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)
xl = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/sdxl-turbo", controlnet=cn, vae=vae, torch_dtype=torch.float16, variant="fp16")
# IP-Adapter with the OpenCLIP ViT-H image encoder
xl.load_ip_adapter("h94/IP-Adapter", subfolder="sdxl_models", weight_name="ip-adapter_sdxl_vit-h.safetensors",
                   image_encoder_folder="models/image_encoder")
xl.to(DEV)
xl_i2i = StableDiffusionXLControlNetImg2ImgPipeline.from_pipe(xl)
plain = StableDiffusionXLPipeline.from_pipe(xl)
for p in (xl, xl_i2i, plain):
    p.set_progress_bar_config(disable=True)
# The text side of the same CLIP model, so visitor text and artworks share one embedding space
CLIP_ID = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
clip_tok = CLIPTokenizer.from_pretrained(CLIP_ID)
clip_txt = CLIPTextModelWithProjection.from_pretrained(CLIP_ID, torch_dtype=torch.float16).to(DEV)
print(f"models loaded in {time.time() - t0:.0f}s, GPU memory {torch.cuda.memory_allocated() / 1e9:.1f} GB")

# ---- helpers + opening painting (notebook cell) ----
def gen(seed=7):
    return torch.Generator(DEV).manual_seed(seed)

@torch.no_grad()
def E(text):
    """SDXL text conditioning: (token embeds (1,77,2048), pooled (1,1280))."""
    pe, _, pp, _ = xl.encode_prompt(prompt=text, device=DEV, num_images_per_prompt=1, do_classifier_free_guidance=False)
    return pe, pp

@torch.no_grad()
def clip_text(texts):
    """Unit-length CLIP ViT-H text embeddings, shape (n, 1024). Same space as clip_image."""
    tok = clip_tok(texts, padding=True, truncation=True, max_length=77, return_tensors="pt").to(DEV)
    e = clip_txt(**tok).text_embeds.float()
    return e / e.norm(dim=-1, keepdim=True)

@torch.no_grad()
def clip_image(img):
    """The IP-Adapter's own CLIP ViT-H image embedding, shape (1, 1024)."""
    v, _ = xl.encode_image(img, DEV, 1, False)
    return v.float()

ZERO_IP = torch.zeros(1, 1024, device=DEV)
def ip_embeds(v, cfg):
    pos = v.to(torch.float16)[None]                       # (1, 1, 1024)
    return [torch.cat([torch.zeros_like(pos), pos]) if cfg else pos]

def style_only(s):
    """InstantStyle: inject the IP-Adapter only into SDXL's style block, so it transfers style but not content."""
    return {"up": {"block_0": [0.0, s, 0.0]}}

def render(cond=None, ip=None, ip_scale=0.0, push=0.0, neg=None, control=None, cn_scale=0.45,
           init=None, strength=0.5, seed=7):
    """One frame.
    cond: (pe, pp) text conditioning (default: the base STYLE prompt)
    ip: (1,1024) CLIP image-space vector for the IP-Adapter; ip_scale: float or style_only(s)
    push: classifier-free guidance scale (>1 turns it on); neg: negative (pe, pp), default STYLE
    init: PIL image for image-to-image (with strength); otherwise generated from noise
    control: Canny edge image (default: EDGES of the opening painting)"""
    pe, pp = cond if cond is not None else (S_PE, S_PP)
    cfg = push > 1
    xl.set_ip_adapter_scale(ip_scale if ip is not None else 0.0)
    kw = dict(prompt_embeds=pe, pooled_prompt_embeds=pp,
              ip_adapter_image_embeds=ip_embeds(ip if ip is not None else ZERO_IP, cfg),
              controlnet_conditioning_scale=cn_scale, num_inference_steps=4, generator=gen(seed))
    if cfg:
        npe, npp = neg if neg is not None else (S_PE, S_PP)
        kw.update(guidance_scale=push, negative_prompt_embeds=npe, negative_pooled_prompt_embeds=npp)
    else:
        kw.update(guidance_scale=0.0)
    ctrl = control if control is not None else EDGES
    if init is None:
        return xl(image=ctrl, width=W, height=H, **kw).images[0]
    return xl_i2i(image=init, control_image=ctrl, strength=strength, **kw).images[0]

def edges_of(img, lo=80, hi=160):
    e = cv2.Canny(np.array(img.convert("RGB").resize((W, H))), lo, hi)
    return Image.fromarray(np.stack([e] * 3, -1))

def board(rows, row_labels, col_labels, title=None, cell=(384, 216), left=190):
    """Labeled grid of PIL images (None leaves a blank)."""
    cw, ch = cell; top = 26 + (22 if title else 0)
    C = max(len(r) for r in rows)
    B = Image.new("RGB", (left + C * cw, top + len(rows) * (ch + 6)), "white"); d = ImageDraw.Draw(B)
    if title: d.text((6, 6), title, fill="black")
    for j, cl in enumerate(col_labels): d.text((left + j * cw + 4, top - 16), cl[:60], fill="black")
    for i, r in enumerate(rows):
        y = top + i * (ch + 6)
        for k, line in enumerate(textwrap.wrap(row_labels[i], 30)[:14]): d.text((4, y + 2 + k * 13), line, fill="black")
        for j, im in enumerate(r):
            if im is None: continue
            t = im.copy(); t.thumbnail((cw - 4, ch)); B.paste(t, (left + j * cw + (cw - t.width) // 2, y + (ch - t.height) // 2))
    return B

STYLE = "an oil painting of a gothic chapel tower above a garden pond, reflections on the water, visible brushstrokes"
S_PE, S_PP = E(STYLE)
xl.set_ip_adapter_scale(0.0)
opening = plain(prompt_embeds=S_PE, pooled_prompt_embeds=S_PP, ip_adapter_image_embeds=ip_embeds(ZERO_IP, False),
                num_inference_steps=4, guidance_scale=0.0, width=W, height=H, generator=gen()).images[0]
EDGES = edges_of(opening)
display(opening)

# ---- art library (notebook cell) ----
ARTWORKS = {
    "Rembrandt, The Night Watch (1642)": "The_Night_Watch_-_HD.jpg",
    "Friedrich, Wanderer above the Sea of Fog (1818)": "Caspar_David_Friedrich_-_Wanderer_above_the_sea_of_fog.jpg",
    "Hokusai, The Great Wave (1831)": "Tsunami_by_hokusai_19th_century.jpg",
    "Turner, The Fighting Temeraire (1839)": "The_Fighting_Temeraire,_JMW_Turner,_National_Gallery.jpg",
    "Turner, Rain, Steam and Speed (1844)": "Turner_-_Rain,_Steam_and_Speed_-_National_Gallery_file.jpg",
    "Monet, Impression, Sunrise (1872)": "Monet_-_Impression,_Sunrise.jpg",
    "Whistler, Nocturne in Black and Gold (1875)": "Whistler-Nocturne_in_black_and_gold.jpg",
    "Seurat, A Sunday on La Grande Jatte (1884)": "Georges_Seurat_-_A_Sunday_on_La_Grande_Jatte_--_1884_-_Google_Art_Project.jpg",
    "Van Gogh, The Starry Night (1889)": "Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
    "Van Gogh, Wheatfield with Crows (1890)": "Vincent_van_Gogh_(1853-1890)_-_Wheat_Field_with_Crows_(1890).jpg",
    "Munch, The Scream (1893)": "Edvard_Munch,_1893,_The_Scream,_oil,_tempera_and_pastel_on_cardboard,_91_x_73_cm,_National_Gallery_of_Norway.jpg",
    "Monet, Water Lilies (1906)": "Claude_Monet_-_Water_Lilies_-_1906,_Ryerson.jpg",
    "Klimt, The Kiss (1908)": "The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg",
    "Kandinsky, Composition VII (1913)": "Vassily_Kandinsky,_1913_-_Composition_7.jpg",
    # Round 3: Romantic paintings so "hot, dark, violent" has somewhere to land
    "Goya, The Third of May 1808 (1814)": "El_Tres_de_Mayo,_by_Francisco_de_Goya,_from_Prado_thin_black_margin.jpg",
    "Delacroix, Liberty Leading the People (1830)": "Eugène_Delacroix_-_Le_28_Juillet._La_Liberté_guidant_le_peuple.jpg",
    "Delacroix, The Death of Sardanapalus (1827)": "Eugène_Delacroix_-_La_Mort_de_Sardanapale.jpg",
    "Gericault, The Raft of the Medusa (1819)": "JEAN_LOUIS_THÉODORE_GÉRICAULT_-_La_Balsa_de_la_Medusa_(Museo_del_Louvre,_1818-19).jpg",
}
UA = {"User-Agent": "LivingCanvasHackathon/0.1 (student research prototype)"}
ART, ART_V = {}, {}
for name, f in ARTWORKS.items():
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f) + "?width=1024"
    data = None
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read(); break
        except Exception as e:
            print(f"  retry {name}: {e}"); time.sleep(6 * (attempt + 1))
    if data is None:
        print("SKIPPED", name); continue
    img = Image.open(io.BytesIO(data)).convert("RGB"); img.thumbnail((1024, 1024))
    ART[name], ART_V[name] = img, clip_image(img)
    time.sleep(2.5)
ART_NAMES = list(ART_V)
ART_M = torch.cat([ART_V[n] for n in ART_NAMES])                 # (N, 1024) raw IP-Adapter image embeds
ART_MN = ART_M / ART_M.norm(dim=-1, keepdim=True)                # unit length, for similarity
print(f"{len(ART_NAMES)} artworks embedded")

# ---- server (notebook cell, tunnel removed) ----
from fastapi import FastAPI, HTTPException
import uvicorn

G = globals()
SHOW = []
def show(img, name=None):
    """Experiments call show(img, "name") to send an image back to Claude."""
    SHOW.append((name or f"img{len(SHOW)}", img))

TOKEN = os.environ.get("LAB_TOKEN") or secrets.token_urlsafe(24)
LOCK = threading.Lock()
app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True, "gpu": torch.cuda.get_device_name(0), "artworks": len(ART_NAMES)}

@app.post("/exec")
def run(req: dict):
    if req.get("token") != TOKEN:
        raise HTTPException(status_code=403, detail="bad token")
    with LOCK:
        SHOW.clear(); out = io.StringIO(); err = None; t0 = time.time()
        try:
            with contextlib.redirect_stdout(out):
                exec(req.get("code", ""), G)
        except Exception:
            err = traceback.format_exc()
        imgs = []
        for name, im in SHOW:
            b = io.BytesIO(); im.convert("RGB").save(b, "JPEG", quality=88)
            imgs.append({"name": name, "jpg": base64.b64encode(b.getvalue()).decode()})
        return {"stdout": out.getvalue()[-20000:], "error": err, "images": imgs, "seconds": round(time.time() - t0, 2)}

server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning"))


print(f"LAB READY  token={TOKEN}", flush=True)
server.run()
