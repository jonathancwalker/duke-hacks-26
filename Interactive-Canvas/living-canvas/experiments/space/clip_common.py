"""Candidate A (repaired CLIP): shared loading, library download and embedding. Runs locally (MPS or CPU).

CLIP is laion/CLIP-ViT-H-14-laion2B-s32B-b79K, both towers: the image tower is the same ViT-H the IP-Adapter
uses as its image encoder, and `image_features` here matches the lab's `clip_image` (projected, not normalized).
Everything heavy is cached under cache/ (gitignored).
"""
import io, json, os, time, urllib.parse, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
OUT = os.path.join(HERE, "out")
CLIP_ID = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"
UA = {"User-Agent": "LivingCanvasHackathon/0.1 (student research prototype; Duke hackathon)"}

# The lab's 36-painting library: ARTWORKS in experiments/gcp/lab_service.py + EXTRA_ART in experiments/lab/03_brush.py
LIBRARY = {
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
    "Goya, The Third of May 1808 (1814)": "El_Tres_de_Mayo,_by_Francisco_de_Goya,_from_Prado_thin_black_margin.jpg",
    "Delacroix, Liberty Leading the People (1830)": "Eugène_Delacroix_-_Le_28_Juillet._La_Liberté_guidant_le_peuple.jpg",
    "Delacroix, The Death of Sardanapalus (1827)": "Eugène_Delacroix_-_La_Mort_de_Sardanapale.jpg",
    "Gericault, The Raft of the Medusa (1819)": "JEAN_LOUIS_THÉODORE_GÉRICAULT_-_La_Balsa_de_la_Medusa_(Museo_del_Louvre,_1818-19).jpg",
    "Bruegel, The Hunters in the Snow (1565)": "Pieter Bruegel the Elder - Hunters in the Snow (Winter) - Google Art Project.jpg",
    "Caravaggio, The Calling of Saint Matthew (1600)": "Caravaggio — The Calling of Saint Matthew.jpg",
    "Vermeer, The Milkmaid (1658)": "Johannes Vermeer - Het melkmeisje - Google Art Project.jpg",
    "Renoir, Dance at Le Moulin de la Galette (1876)": "Auguste Renoir - Dance at Le Moulin de la Galette - Google Art Project.jpg",
    "Sargent, Carnation, Lily, Lily, Rose (1886)": "John Singer Sargent - Carnation, Lily, Lily, Rose - Google Art Project.jpg",
    "Tanner, The Banjo Lesson (1893)": "Henry Ossawa Tanner - The Banjo Lesson.jpg",
    "Cassatt, The Child's Bath (1893)": "Mary Cassatt - The Child's Bath - Google Art Project.jpg",
    "Gauguin, Vision after the Sermon (1888)": "Paul Gauguin - Vision of the Sermon (Jacob Wrestling with the Angel) - NG 1643 - National Galleries of Scotland.jpg",
    "Matisse, Woman with a Hat (1905)": "Matisse-Woman-with-a-Hat.jpg",
    "Marc, The Large Blue Horses (1911)": "Franz Marc - Die großen blauen Pferde 1911.jpg",
    "Klee, Senecio (1922)": "Paul Klee, 1922, Senecio, oil on gauze, 40.3 × 37.4 cm, Kunstmuseum Basel.jpg",
    "Homer, The Gulf Stream (1899)": "Winslow Homer - The Gulf Stream - Metropolitan Museum of Art.jpg",
    "Caillebotte, Paris Street; Rainy Day (1877)": "Gustave Caillebotte - Paris Street; Rainy Day - Google Art Project.jpg",
    "Hiroshige, Sudden Shower over Shin-Ohashi (1857)": "Hiroshige, Sudden shower over Shin-Ōhashi bridge and Atake, 1857.jpg",
    "Fan Kuan, Travelers Among Mountains and Streams (c.1000)": "Fan Kuan - Travelers Among Mountains and Streams - Google Art Project.jpg",
    "Monet, Rouen Cathedral in Sunlight (1894)": "Claude Monet - Rouen Cathedral, West Façade, Sunlight - Google Art Project.jpg",
    "Turner, Snow Storm (1842)": "Joseph Mallord William Turner - Snow Storm - Steam-Boat off a Harbour's Mouth - WGA23178.jpg",
    "Mondrian, Composition II in Red, Blue and Yellow (1930)": "Piet Mondriaan, 1930 - Mondrian Composition II in Red, Blue, and Yellow.jpg",
}

# Reference text bank for centering / gap / hub correction. Deliberately NOT the test statements in feelings.json:
# a generic emotion vocabulary, so the fixes are fit on something a deployed system would also have.
REF_WORDS = [
    "happy", "sad", "angry", "afraid", "calm", "anxious", "joyful", "lonely", "hopeful", "hopeless", "grateful",
    "bitter", "tender", "proud", "ashamed", "guilty", "jealous", "bored", "curious", "amazed", "awestruck",
    "disgusted", "relieved", "tense", "restless", "serene", "melancholy", "nostalgic", "homesick", "heartbroken",
    "in love", "playful", "silly", "confident", "insecure", "overwhelmed", "exhausted", "energetic", "excited",
    "numb", "empty", "content", "peaceful", "frustrated", "irritated", "furious", "terrified", "nervous",
    "triumphant", "defeated", "determined", "confused", "betrayed", "safe", "vulnerable", "free", "trapped",
    "dreamy", "wistful", "mournful", "ecstatic", "cheerful", "gloomy", "worried", "brave", "shy", "warm",
    "cold", "alive", "tired", "inspired", "lost", "at home", "rejected", "accepted", "embarrassed", "sentimental",
]

# A second reference bank shaped like what visitors actually say (sentences, mixed and neutral topics), standing in
# for a log of past visitors. Written to be disjoint from the feelings.json statements.
REF_SENTENCES = [
    "I just got off a long shift at the hospital.", "My sister is getting married next weekend.",
    "I came here with my roommate.", "I don't really know what to say.", "The coffee here is actually good.",
    "I failed my driving test this morning.", "I just adopted a puppy!", "My knees hurt from all the stairs.",
    "I got the internship I applied for.", "My best friend moved to another country.", "It's my birthday today.",
    "I'm not sure I picked the right major.", "My dad is in the hospital.", "I finally finished my thesis.",
    "Traffic was terrible on the way here.", "I'm a little bored, honestly.", "The music in here is so loud.",
    "I broke up with my boyfriend last week.", "I ran my first marathon on Sunday.", "I feel kind of numb lately.",
    "We're celebrating our anniversary.", "I keep thinking about a mistake I made at work.",
    "Someone was rude to me on the bus.", "I'm proud of how far I've come.", "I can't decide what to eat.",
    "My grandfather taught me to paint.", "I just moved here and don't know anyone.", "Spring is finally here.",
    "I'm curious what this thing does.", "Rain all week, I'm sick of it.", "I just got some really good news.",
    "My cat has been sick and I'm worried.", "I feel like I'm on top of the world.", "Work has been really boring.",
    "I've been laughing all night with my friends.", "My flight got cancelled again.",
    "I'm jealous of how easy things are for other people.", "I just want to lie on the beach.",
    "I'm embarrassed about what I said earlier.", "I volunteered at the shelter today.",
    "It's been a weird, confusing week.", "My little brother made me a card.", "I feel trapped in my job.",
    "We got lost hiking but found an amazing view.", "I'm ready for whatever comes next.",
    "My phone died and I feel weirdly free.", "I miss the ocean.", "The city lights look beautiful tonight.",
    "I don't trust the people I work with.", "Today was just an ordinary day.",
]

TEMPLATES = {
    "baseline": "a painting that feels {}",                         # current art_weights in lab/00_lib.py
    "raw": "{}",
    "evokes": "a painting that evokes the feeling of someone who says: {}",
    "mood": "the mood of this artwork is like: {}",
    "emotion": "an artwork expressing this emotion: {}",
    "atmosphere": "a painting whose colors and atmosphere feel like {}",
}


def device():
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"


_MODEL = None
def model():
    global _MODEL
    if _MODEL is None:
        import torch
        from transformers import CLIPModel, CLIPProcessor
        m = CLIPModel.from_pretrained(CLIP_ID, torch_dtype=torch.float32).to(device()).eval()
        _MODEL = (m, CLIPProcessor.from_pretrained(CLIP_ID))
    return _MODEL


def _unit(x):
    return x / np.linalg.norm(x, axis=-1, keepdims=True)


def embed_texts(texts, bs=32):
    """Unit-length CLIP ViT-H text embeddings (n, 1024), same as the lab's clip_text."""
    import torch
    m, proc = model()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), bs):
            tok = proc.tokenizer(texts[i:i + bs], padding=True, truncation=True, max_length=77, return_tensors="pt").to(device())
            pooled = m.text_model(input_ids=tok["input_ids"], attention_mask=tok["attention_mask"]).pooler_output
            out.append(m.text_projection(pooled).float().cpu().numpy())
    return _unit(np.concatenate(out))


def embed_images(imgs, bs=8):
    """Raw projected CLIP ViT-H image embeddings (n, 1024), like the lab's clip_image (IP-Adapter's encoder)."""
    import torch
    m, proc = model()
    out = []
    with torch.no_grad():
        for i in range(0, len(imgs), bs):
            px = proc.image_processor(imgs[i:i + bs], return_tensors="pt")["pixel_values"].to(device())
            pooled = m.vision_model(pixel_values=px).pooler_output       # = CLIPVisionModelWithProjection.image_embeds
            out.append(m.visual_projection(pooled).float().cpu().numpy())
    return np.concatenate(out)


def fetch(url, path, tries=4, pause=2.0):
    """Polite cached download. Returns bytes or None."""
    if os.path.exists(path):
        return open(path, "rb").read()
    for a in range(tries):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(data)
            time.sleep(pause)
            return data
        except Exception as e:
            print(f"  retry {os.path.basename(path)}: {e}")
            time.sleep(6 * (a + 1))
    return None


def load_small_library():
    """The lab's 36 paintings from Wikimedia Commons (1024 px), cached in cache/commons/."""
    from PIL import Image
    names, imgs = [], []
    for name, f in LIBRARY.items():
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f) + "?width=1024"
        safe = "".join(c if c.isalnum() else "_" for c in name)[:80] + ".jpg"
        data = fetch(url, os.path.join(CACHE, "commons", safe))
        if data is None:
            print("SKIPPED", name); continue
        img = Image.open(io.BytesIO(data)).convert("RGB"); img.thumbnail((1024, 1024))
        names.append(name); imgs.append(img)
    return names, imgs


def cached_image_embeds(tag, names, imgs):
    p = os.path.join(CACHE, f"img_{tag}.npz")
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True)
        if list(z["names"]) == list(names):
            return z["emb"]
    emb = embed_images(imgs)
    np.savez(p, names=np.array(names, dtype=object), emb=emb)
    return emb
