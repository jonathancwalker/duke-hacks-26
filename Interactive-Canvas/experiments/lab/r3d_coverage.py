# Ran on the GPU lab bundled after r3_director.py (for DIRECTOR) with LIB_ART_SPACE_SRC = source of 01_art_space.py.
# Its effect is now permanent: lab_server.ipynb and 01_art_space.py include the four Romantic paintings.
# Coverage fix: add hot / dark / violent Romantic paintings, then rerender the art-director cases.
# Note: 01_art_space.py already ran above with the OLD library; after adding, rebuild axes by re-running its body.
import io, time, urllib.parse, urllib.request
NEW_ART = {
    "Goya, The Third of May 1808 (1814)": "El_Tres_de_Mayo,_by_Francisco_de_Goya,_from_Prado_thin_black_margin.jpg",
    "Delacroix, Liberty Leading the People (1830)": "Eugène_Delacroix_-_Le_28_Juillet._La_Liberté_guidant_le_peuple.jpg",
    "Delacroix, The Death of Sardanapalus (1827)": "Eugène_Delacroix_-_La_Mort_de_Sardanapale.jpg",
    "Gericault, The Raft of the Medusa (1819)": "JEAN_LOUIS_THÉODORE_GÉRICAULT_-_La_Balsa_de_la_Medusa_(Museo_del_Louvre,_1818-19).jpg",
}
for name, f in NEW_ART.items():
    if name in ART_V: continue
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(f) + "?width=1024"
    data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    img = Image.open(io.BytesIO(data)).convert("RGB"); img.thumbnail((1024, 1024))
    ART[name], ART_V[name] = img, clip_image(img); time.sleep(2.5)
ART_NAMES = list(ART_V)
ART_M = torch.cat([ART_V[n] for n in ART_NAMES]); ART_MN = ART_M / ART_M.norm(dim=-1, keepdim=True)
print(f"library: {len(ART_NAMES)} paintings")
exec(LIB_ART_SPACE_SRC, globals())   # rebuild axes / center from the expanded library

rows, labels = [], []
for words, d in DIRECTOR.items():
    c = {k: d[k] for k in AX3}
    rows.append([paint_art(c)])
    labels.append(f"\"{words}\" | e{c['energy']:+.1f} t{c['temperature']:+.1f} v{c['value']:+.1f} ({d['why']}) | nearest: {', '.join(nearest_art(art_point(c), 3))}")
    print(labels[-1])
show(board(rows, labels, ["Claude as art director, 18-painting library"], cell=(512, 288), left=300,
           title="R3d · coverage fix: hot + dark + violent now has paintings to land on"), "R3d_coverage")
