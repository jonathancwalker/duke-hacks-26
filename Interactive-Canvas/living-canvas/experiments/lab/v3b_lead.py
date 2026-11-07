# Vibe paint round 3b: blends of 2-3 painters average toward the middle. Does letting the lead painter dominate help?
ensure_library()
def pick(*ps):
    return {n: w for p, w in ps for n in [next((n for n in ART_NAMES if n.startswith(p)), None)] if n}
CASES = [  # Gemini's real picks for these feelings, lead first
    ("grandmother passed", pick(("Tanner", .5), ("Turner", .3), ("Whistler", .2)), .2, -.3, -.8),
    ("won the championship", pick(("Klimt", .5), ("Delacroix", .3), ("Renoir", .2)), .95, .8, .6),
    ("nervous presentation", pick(("Munch", .6), ("Seurat", .4)), .7, -.4, -.2),
    ("calm sunday", pick(("Seurat", .6), ("Monet", .4)), .1, .2, .5),
    ("bored in line", pick(("Caillebotte", .6), ("Seurat", .4)), .15, -.2, 0),
    ("spring break", pick(("Renoir", .6), ("Matisse", .4)), .85, .7, .7),
    ("homesick", pick(("Tanner", .6), ("Caillebotte", .4)), .2, -.1, -.4),
    ("anxious exams", pick(("Munch", .6), ("Van Gogh", .4)), .75, -.3, -.4),
]
def point(w, e, wa, li, sharpen):
    if sharpen: w = {n: x ** 3 for n, x in w.items()}
    v = mix_vector(w) + (e - .5) * 2 * ART_AXES["energy"] + wa * ART_AXES["temperature"] + li * ART_AXES["value"]
    return v / v.norm() * MEAN_NORM
ABS = E("an abstract expressive painting, gestural brushstrokes and loose color fields, no objects")
rows, labels = [], []
for n, w, *ax in CASES:
    rows.append([render2(ip=point(w, *ax, False), ip_scale=style_only(1.4), seed=7, **ART_CN),
                 render2(ip=point(w, *ax, True), ip_scale=style_only(1.4), seed=7, **ART_CN),
                 render2(cond=ABS, ip=point(w, *ax, True), ip_scale=style_only(1.4), seed=7, cn_scale=0.0, cn_end=1.0)])
    labels.append(f"{n}: " + ", ".join(k.split(",")[0] for k in w))
show(board(rows, labels, ["chapel, blend (now)", "chapel, lead painter dominates", "abstract, lead dominates"],
           cell=(384, 216), left=230, title="V3b · lead painter vs blend"), "V3b_lead")
