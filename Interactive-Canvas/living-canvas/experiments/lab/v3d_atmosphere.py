# Vibe paint round 3d: the chapel prompt ("garden pond") pulls every mood green. Let the visitor's mood set the
# scene's light and weather too (Gemini would write this phrase).
ensure_library()
def pick(*ps):
    return {n: w for p, w in ps for n in [next((n for n in ART_NAMES if n.startswith(p)), None)] if n}
CASES = [
    ("grandmother passed", pick(("Tanner", .5), ("Turner", .3), ("Whistler", .2)), .2, -.3, -.8, "at night, one candle-lit window, cold mist over the water"),
    ("won the championship", pick(("Klimt", .5), ("Delacroix", .3), ("Renoir", .2)), .95, .8, .6, "at blazing golden sunset, fireworks bursting in the sky"),
    ("nervous presentation", pick(("Munch", .6), ("Seurat", .4)), .7, -.4, -.2, "under a strange swirling orange sky, wind bending the trees"),
    ("calm sunday", pick(("Seurat", .6), ("Monet", .4)), .1, .2, .5, "on a hazy pastel summer morning, soft pink light"),
    ("bored in line", pick(("Caillebotte", .6), ("Seurat", .4)), .15, -.2, 0, "on a flat grey overcast afternoon, wet pavement"),
    ("spring break", pick(("Renoir", .6), ("Matisse", .4)), .85, .7, .7, "in full spring bloom, pink blossoms, bright turquoise sky"),
    ("homesick", pick(("Tanner", .6), ("Caillebotte", .4)), .2, -.1, -.4, "in falling winter snow at dusk, warm lamplight far away"),
    ("anxious exams", pick(("Munch", .6), ("Van Gogh", .4)), .75, -.3, -.4, "under a violent stormy night sky, lightning, churning clouds"),
]
SC = "an oil painting of a gothic chapel tower above still water, reflections on the water, visible brushstrokes"
def point(w, e, wa, li, k=1.0):
    v = mix_vector(w) + k * ((e - .5) * 2 * ART_AXES["energy"] + wa * ART_AXES["temperature"] + li * ART_AXES["value"])
    return v / v.norm() * MEAN_NORM
rows, labels = [], []
for n, w, e, wa, li, atm in CASES:
    c = E(f"{SC}, {atm}")
    rows.append([render2(ip=point(w, e, wa, li), ip_scale=style_only(1.4), seed=7, **ART_CN),
                 render2(cond=c, ip=point(w, e, wa, li), ip_scale=style_only(1.4), seed=7, **ART_CN),
                 render2(cond=c, ip=point(w, e, wa, li, .5), ip_scale=style_only(1.0), seed=7, **ART_CN)])
    labels.append(f"{n}: {atm}")
show(board(rows, labels, ["now", "+ light & weather, style 1.4", "+ light & weather, style 1.0, axes ½"],
           cell=(448, 252), left=300, title="V3d · the mood sets the light and weather"), "V3d_atmosphere")
