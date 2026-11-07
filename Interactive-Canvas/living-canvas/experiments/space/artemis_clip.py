"""CLIP ViT-H/14 (laion2B) on this Mac: both towers, unit-length 1024-d embeddings.

The image tower is the same OpenCLIP ViT-H the IP-Adapter uses (experiments/gcp/lab_service.py), so anything
picked from a library embedded here can be handed to the IP-Adapter as a style reference.
"""
import torch
from transformers import CLIPImageProcessor, CLIPTextModelWithProjection, CLIPTokenizer, CLIPVisionModelWithProjection

CLIP_ID = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
DEV = "mps" if torch.backends.mps.is_available() else "cpu"
DT = torch.float16 if DEV == "mps" else torch.float32
_T = _V = None


def load_text():
    global _T
    if _T is None:
        _T = (CLIPTokenizer.from_pretrained(CLIP_ID), CLIPTextModelWithProjection.from_pretrained(CLIP_ID, torch_dtype=DT).to(DEV).eval())
    return _T


def load_image():
    global _V
    if _V is None:
        _V = (CLIPImageProcessor.from_pretrained(CLIP_ID), CLIPVisionModelWithProjection.from_pretrained(CLIP_ID, torch_dtype=DT).to(DEV).eval())
    return _V


@torch.no_grad()
def text(texts, bs=256):
    tk, m = load_text()
    out = []
    for i in range(0, len(texts), bs):
        tok = tk(texts[i:i + bs], padding=True, truncation=True, max_length=77, return_tensors="pt").to(DEV)
        e = m(**tok).text_embeds.float()
        out.append((e / e.norm(dim=-1, keepdim=True)).cpu())
    return torch.cat(out)


@torch.no_grad()
def image(imgs, bs=64):
    p, m = load_image()
    out = []
    for i in range(0, len(imgs), bs):
        px = p(imgs[i:i + bs], return_tensors="pt")["pixel_values"].to(DEV, DT)
        e = m(pixel_values=px).image_embeds.float()
        out.append((e / e.norm(dim=-1, keepdim=True)).cpu())
    return torch.cat(out)
