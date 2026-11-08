"""Presence scorer (issue #7): a visitor's words, voice loudness and movement -> 3 painting weights.

This is "C5", the scorer that won the blind feeling-space eval. For words + loudness (0..1) + movement (0..1):

1. Emotion read over the 9 ArtEmis emotions: the ArtEmis text head on the CLIP text embedding, blended 50/50 with
   Gemini (temperature 0, same 9 emotions). The booth waits up to `gemini_timeout_s` for Gemini and uses the head
   alone when it is slow or fails. "something else" is dropped and the rest renormalised. Then the voice/movement steer: arousal = (loudness + movement) / 2 multiplies excitement, anger and
   fear by exp(steer * (arousal - 0.5) * clarity) and contentment and sadness by its inverse, where clarity is
   1 - normalised entropy of the read (a vague read is steered less than a clear one).
2. Emotion score = steered read . PMI of each painting's human vote distribution, smoothed toward the corpus prior
   with `prior_votes` pseudo-votes (so a painting 40 people felt as calm outranks one that 5 did).
3. Subject score = cosine in the trained contrastive feeling space (text tower vs image tower, library centred);
   the text tower also takes arousal.
4. score = z(emotion) + lambda * z(subject) over the whole library; top 3; weights = softmax of the z-scores.

Returns the weights plus each painting's precomputed CLIP ViT-H image vector, which /api/vibe/render accepts for
paintings outside the lab's 36-painting library.

Settings live in config.json (re-read when it changes). The library (presence/build.py) is ArtEmis-derived, so it
stays outside git: config `library_dir`, or PRESENCE_DIR.
"""
import concurrent.futures
import json
import os
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.environ.get("PRESENCE_CONFIG") or os.path.join(HERE, "config.json")
LIBRARY_FILE = "presence_library.npz"
EMO = ["amusement", "awe", "contentment", "excitement", "anger", "disgust", "fear", "sadness", "something else"]
SE = EMO.index("something else")
HIGH = [EMO.index(e) for e in ("excitement", "anger", "fear")]
LOW = [EMO.index(e) for e in ("contentment", "sadness")]
F32 = np.float32


# ---------------------------------------------------------------- config
def load_config(path=None):
    with open(path or CONFIG_PATH) as f:
        cfg = json.load(f)
    cfg.pop("note", None)
    cfg["votes"] = {"min": int(cfg.get("votes", {}).get("min", 0)), "soft_k": float(cfg.get("votes", {}).get("soft_k", 0))}
    cfg["library_dir"] = os.path.expanduser(os.environ.get("PRESENCE_DIR") or cfg.get("library_dir", ""))
    return cfg


# ---------------------------------------------------------------- the emotion read (pure)
def drop_something_else(p):
    p = np.array(p, dtype=F32)
    p[..., SE] = 0
    return p / p.sum(-1, keepdims=True)


def blend(head, gemini, w):
    """Head alone, or (1 - w) * head + w * Gemini when Gemini has answered."""
    head = np.asarray(head, dtype=F32)
    return head if gemini is None else (F32(1 - w) * head + F32(w) * np.asarray(gemini, dtype=F32)).astype(F32)


def clarity(p8):
    """1 - normalised entropy over the 8 emotions a visitor can feel: 1 = one emotion, 0 = all equal."""
    q = np.maximum(np.delete(np.asarray(p8, dtype=F32), SE, axis=-1), F32(1e-9))
    return F32(1) - (-(q * np.log(q)).sum(-1)) / F32(np.log(q.shape[-1]))


def steer(p8, arousal, strength, clear=None):
    """Loud / moving -> excitement, anger, fear; quiet / still -> contentment, sadness. Scaled by the read's clarity."""
    p8 = np.asarray(p8, dtype=F32)
    clear = clarity(p8) if clear is None else clear
    s = (F32(arousal) - F32(0.5)) * F32(strength) * F32(clear)
    g = np.ones(len(EMO), dtype=F32)
    g[HIGH], g[LOW] = np.exp(s), np.exp(-s)
    q = p8 * g
    return q / q.sum()


def z(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / (x.std() + 1e-9)


def mix_from_scores(row, k=3):
    """Top k by score; weights = softmax of the row's z-scores over those k (the eval board's mix_from_scores)."""
    zz = z(row)
    top = np.argsort(-zz)[:k]
    w = np.exp(zz[top] - zz[top].max())
    return top, w / w.sum()


# ---------------------------------------------------------------- CLIP text tower (same model and settings as the build)
CLIP_ID = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"


class ClipText:
    """CLIP ViT-H/14 text tower on this machine (Apple GPU in fp16 when there is one), unit-length 1024-d."""

    def __init__(self):
        import torch
        from transformers import CLIPTextModelWithProjection, CLIPTokenizer
        from transformers.utils import logging as hf_logging
        hf_logging.set_verbosity_error()                  # the checkpoint's unused image tower is expected
        self.torch = torch
        self.dev = "mps" if torch.backends.mps.is_available() else "cpu"
        dt = torch.float16 if self.dev == "mps" else torch.float32
        self.tok = CLIPTokenizer.from_pretrained(CLIP_ID)
        self.model = CLIPTextModelWithProjection.from_pretrained(CLIP_ID, torch_dtype=dt).to(self.dev).eval()
        self.lock = threading.Lock()

    def __call__(self, text):
        with self.lock, self.torch.no_grad():
            t = self.tok([text], padding=True, truncation=True, max_length=77, return_tensors="pt").to(self.dev)
            e = self.model(**t).text_embeds.float()
            return (e / e.norm(dim=-1, keepdim=True)).cpu().numpy()[0].astype(F32)


# ---------------------------------------------------------------- the library
class Library:
    def __init__(self, arrays, cfg, encode):
        self.a, self.encode = arrays, encode
        self._views, self.cfg = {}, None
        self.configure(cfg)

    @classmethod
    def load(cls, cfg, encode=None):
        path = os.path.join(cfg["library_dir"], LIBRARY_FILE)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} (build it with presence/build.py)")
        with np.load(path, allow_pickle=False) as f:
            arrays = {k: f[k] for k in f.files}
        return cls(arrays, cfg, encode or ClipText())

    def configure(self, cfg):
        self.cfg = cfg
        key = (cfg["votes"]["min"], cfg["votes"]["soft_k"], float(cfg["prior_votes"]))
        if key not in self._views:
            self._views[key] = self._view(*key)
        self.view = self._views[key]

    def _view(self, min_votes, soft_k, prior_votes):
        """Everything that depends on which paintings are in play: computed once per vote setting."""
        a = self.a
        keep = np.where(a["n"] >= min_votes)[0]
        if len(keep) < 3:
            raise ValueError(f"only {len(keep)} paintings have >= {min_votes} votes")
        n = a["n"][keep].astype(F32)[:, None]
        H = (a["D"][keep] * n + F32(prior_votes) * a["prior"][None]) / (n + F32(prior_votes))
        pmi = (np.log(H) - np.log(H.mean(0, keepdims=True))).T.astype(F32)            # (9, N)
        if soft_k > 0:                                    # soft count weighting: thin-vote paintings lean to neutral
            pmi = pmi * (n[:, 0] / (n[:, 0] + F32(soft_k)))[None]
        L = a["img_proj"][keep]
        L = L - L.mean(0, keepdims=True)
        L = (L / np.linalg.norm(L, axis=1, keepdims=True)).astype(F32)
        return {"keep": keep, "pmi": pmi, "L": L}

    def head(self, t):
        x = (t * F32(20)) @ self.a["head_W"].T + self.a["head_b"]
        e = np.exp(x - x.max())
        return (e / e.sum()).astype(F32)

    def subject(self, t, arousal):
        a = self.a
        u = (t @ a["c4_t_W"].T + a["c4_t_b"]) + (F32(arousal) - F32(0.5)) * (t @ a["c4_g_W"].T + a["c4_g_b"])
        u = u / np.linalg.norm(u)
        return self.view["L"] @ u.astype(F32)

    def score(self, text, loudness, movement, gemini=None):
        t0 = time.perf_counter()
        cfg, v = self.cfg, self.view
        arousal = (float(loudness) + float(movement)) / 2
        t = self.encode(text)
        head = self.head(t)
        p8 = drop_something_else(blend(head, gemini, cfg["gemini_weight"]))
        clear = clarity(p8)
        p8s = steer(p8, arousal, cfg["steer"], clear)
        emo, subj = z(p8s @ v["pmi"]), z(self.subject(t, arousal))
        S = emo + cfg["lambda"] * subj
        top, w = mix_from_scores(S, cfg["top_k"])
        a, artists, vectors = self.a, [], {}
        for j, wj in zip(top, w):
            g = int(v["keep"][j]); name = str(a["names"][g])
            artists.append({"name": name, "weight": round(float(wj), 3), "label": f"{a['artist'][g]}, {a['title'][g]}",
                            "artist": str(a["artist"][g]), "title": str(a["title"][g]), "votes": int(a["n"][g]),
                            "emotion_z": round(float(emo[j]), 2), "subject_z": round(float(subj[j]), 2)})
            vectors[name] = a["img_emb"][g].tolist()
        emotions = lambda q: {e: round(float(q[k]), 2) for k, e in enumerate(EMO) if q[k] >= 0.05}
        return {"artists": artists, "vectors": vectors,
                "read": {"source": "head" if gemini is None else "head+gemini", "emotions": emotions(p8s),
                         "head": emotions(head), "gemini": None if gemini is None else emotions(np.asarray(gemini)),
                         "clarity": round(float(clear), 2), "arousal": round(arousal, 2)},
                "library": int(len(v["keep"])), "ms": round(1000 * (time.perf_counter() - t0), 1)}


# ---------------------------------------------------------------- Gemini emotion read (the booth waits for it, up to a timeout)
EMO_KEYS = [e.replace(" ", "_") for e in EMO]
EMO_SCHEMA = {"type": "OBJECT", "properties": {k: {"type": "NUMBER"} for k in EMO_KEYS}, "required": EMO_KEYS}
EMO_PROMPT = ("Someone at an interactive art installation said: \"{text}\"\n"
              "How do they feel right now? Give a probability for each of these 9 emotions, summing to 1: "
              + ", ".join(EMO_KEYS) + ". Read the whole sentence, not single words.")


def gemini_reader(client, model):
    """text -> 9-way distribution from Gemini at temperature 0, or None."""
    from google.genai import types

    def read(text):
        cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=EMO_SCHEMA, temperature=0.0)
        r = client.models.generate_content(model=model, contents=EMO_PROMPT.format(text=text), config=cfg)
        a = json.loads(r.text) if r.text else {}
        v = np.clip([float(a.get(k, 0) or 0) for k in EMO_KEYS], 0, None)
        return (v / v.sum()).tolist() if v.sum() > 0 else None
    return read


class Presence:
    """The booth's scorer: the text head blended with Gemini's read, waiting up to timeout_s (config
    `gemini_timeout_s`) for Gemini. Gemini slow, failing or not configured: the head alone. config.json is re-read
    when it changes."""

    def __init__(self, lib, gemini=None, timeout_s=None, config_path=None):
        self.lib, self.gemini, self.config_path = lib, gemini, config_path or CONFIG_PATH
        self.timeout_s = timeout_s
        self._pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        self._mtime = self._stat()

    def _stat(self):
        try:
            return os.path.getmtime(self.config_path)
        except OSError:
            return None

    def _refresh_config(self):
        m = self._stat()
        if m != self._mtime:
            self._mtime = m
            try:
                self.lib.configure(load_config(self.config_path))
            except Exception as e:                       # a half-saved or bad config keeps the last good one
                print(f"[presence] config not applied: {e.__class__.__name__}: {e}", file=sys.stderr)

    def _gemini_read(self, text):
        timeout = self.timeout_s if self.timeout_s is not None else float(self.lib.cfg.get("gemini_timeout_s", 8.0))
        f = self._pool.submit(self.gemini, text)
        try:
            return f.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"[presence] Gemini emotion read over {timeout:.1f}s; using the text head alone", file=sys.stderr)
        except Exception as e:
            print(f"[presence] Gemini emotion read failed ({e.__class__.__name__}: {str(e)[:200]}); using the text head alone",
                  file=sys.stderr)
        return None

    def __call__(self, text, loudness, movement):
        self._refresh_config()
        gem = self._gemini_read(text) if self.gemini is not None and text else None
        return self.lib.score(text, loudness, movement, gemini=None if gem is None else np.asarray(gem, dtype=F32))
