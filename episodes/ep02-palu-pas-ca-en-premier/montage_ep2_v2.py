"""Épisode 2 — montage v2 (écran partagé 50/50).

Nouveautés par rapport à la v1 (montage_ep2.py, dont on réutilise les outils) :
  - « à moins de 5 mois » remplacé par la note vocale d'Abdou « À moins de trois mois » (n1) ;
  - lecture du TDR ajoutée (note n2 : « un point = négatif, deux points = positif »), avant « Si TDR positif… » ;
  - notes vocales accélérées ×1,2 (comme à l'épisode 1) ;
  - bas d'écran recadré sur le torse (plan poitrine), visage affiné par une compression horizontale de 4 %,
    filtre couleur (contraste, chaleur, lissage léger de la peau, netteté, vignettage léger).
Usage : python3 montage_ep2_v2.py → out/ep02_montage_v2.mp4
"""
import json
import os

import numpy as np
from PIL import Image

import montage_ep2 as v1
from montage_ep2 import (FF, FPS, W, H, HALF, SPEED, run, encode, concat, label, stack, pop, paste, red_x,
                         ass_time, RED_WORDS, VOICE_FX, RED, WHITE, YELLOW, DARK_T, GREEN, sfx)

HERE, A = v1.HERE, v1.A
OUT, TMP = v1.OUT, os.path.join(v1.OUT, "tmp_v2")
FACES = json.load(open(os.path.join(A, "faces.json")))
SQUEEZE = 0.96  # affinage : l'image du bas est comprimée de 4 % en largeur


def src(name):
    if name.startswith("n"):
        return os.path.join(A, "voix", f"{name}.wav")
    return v1.src(name)


# Parties vocales, dans l'ordre. video=None → bas d'écran synchronisé sur la même prise.
PARTS = [
    dict(id="hook", audio=("IMG_4570", 0.10, 5.52)),
    dict(id="piege", audio=("WA0037", 0.40, 9.12)),
    dict(id="reflexes", audio=("WA0036", 0.15, 17.78)),
    dict(id="tdr", audio=("WA0033", 0.00, 4.95)),
    dict(id="lecture", audio=("n2f", 1.40, 12.72), video="gestes"),
    dict(id="resultat", audio=("WA0033", 4.95, 13.70)),
    dict(id="urg_a", audio=("WA0035", 0.45, 6.80)),
    dict(id="urg_mois", audio=("n1f", 0.30, 3.40), video=("WA0035", 7.80)),  # lèvres de la prise d'origine
    dict(id="urg_b", audio=("WA0035", 9.55, 11.88)),
    dict(id="cta", audio=("WA0034", 0.00, 7.72)),
]
PID = {p["id"]: i for i, p in enumerate(PARTS)}
TAIL = ("IMG_4569", 0.20, 1.85)


def kept(clip, a, b):
    db = v1.energy(src(clip))
    thr = -50.0 if clip.startswith("n") else np.percentile(db, 10) + 10  # notes WhatsApp : silence numérique
    q = db < thr
    runs, i = [], 0
    while i < len(q):
        if q[i]:
            j = i
            while j < len(q) and q[j]:
                j += 1
            if (j - i) * 0.01 >= 0.25:
                runs.append((i * 0.01 + 0.08, j * 0.01 - 0.08))
            i = j
        else:
            i += 1
    out, cur = [], a
    for s, e in runs:
        if e <= a or s >= b:
            continue
        s, e = max(s, a), min(e, b)
        if s > cur:
            out.append([cur, s])
        cur = max(cur, e)
    if cur < b:
        out.append([cur, b])
    snap = lambda t: round(t * FPS) / FPS
    return [[snap(x), snap(y)] for x, y in out if y - x >= 2 / FPS]


class TL:
    def __init__(self):
        self.pieces, self.rng, t = [], [], 0.0
        for pi, p in enumerate(PARTS):
            t0 = t
            for a, b in kept(*p["audio"]):
                self.pieces.append((pi, p["audio"][0], a, b, t))
                t = round((t + b - a) * FPS) / FPS
            self.rng.append((t0, t))
        self.voice_end = t
        self.total = t + TAIL[2] - TAIL[1]

    def at(self, pid, raw):
        pi = PID[pid]
        cands = [x for x in self.pieces if x[0] == pi]
        for _, _, a, b, t0 in cands:
            if raw <= b:
                return t0 + max(0.0, raw - a)
        _, _, a, b, t0 = cands[-1]
        return t0 + b - a

    def r(self, pid):
        return self.rng[PID[pid]]


CUES = {
    "pas_ca": ("hook", 4.22), "antipalu": ("piege", 2.91),
    "r1": ("reflexes", 1.87), "r2": ("reflexes", 6.07), "r3": ("reflexes", 12.43),
    "h24": ("tdr", 2.70),
    "un_point": ("lecture", 2.85), "neg_dit": ("lecture", 6.75), "deux_points": ("lecture", 9.00),
    "pos_dit": ("lecture", 11.80),
    "positif": ("resultat", 5.95), "negatif": ("resultat", 10.30),
    "u_conv": ("urg_a", 1.10), "u_tete": ("urg_a", 2.90), "u_vomit": ("urg_a", 4.55), "u_dort": ("urg_a", 6.12),
    "u_mois": ("urg_mois", 0.90),
}

SUBS = [
    ("hook", 0.10, "hook", 2.60, "Tu soupçonnes le palu chez ton enfant ?"),
    ("hook", 2.60, "hook", 5.52, "Ne fais SURTOUT PAS ça en premier !"),
    ("piege", 0.40, "piege", 5.00, "L'erreur classique : lui donner un antipaludéen sans faire le test."),
    ("piege", 5.00, "piege", 9.12, "Si c'est une autre maladie, tu perds un temps précieux."),
    ("reflexes", 0.15, "reflexes", 1.80, "Trois bons réflexes."),
    ("reflexes", 1.80, "reflexes", 5.65, "Un : note l'heure du début de la fièvre."),
    ("reflexes", 5.65, "reflexes", 12.35, "Deux : fais-le boire, ou allaite-le."),
    ("reflexes", 12.35, "reflexes", 17.78, "Trois : paracétamol pour son confort, et à la bonne dose."),
    ("tdr", 0.00, "tdr", 4.95, "Puis, allez au centre de santé le plus proche dans les 24 heures pour le TDR."),
    ("lecture", 1.40, "lecture", 7.40, "Là où vous voyez un point, c'est que le test est négatif."),
    ("lecture", 7.40, "lecture", 12.72, "Et là où vous voyez deux points, c'est que le test est positif."),
    ("resultat", 4.95, "resultat", 9.60, "Si TDR positif : traitement complet, jusqu'au bout."),
    ("resultat", 9.60, "resultat", 13.70, "Si TDR négatif : cherchez une autre cause."),
    ("urg_a", 0.45, "urg_a", 6.80, "Mais s'il convulse, ne tète plus, vomit tout, dort trop,"),
    ("urg_mois", 0.30, "urg_b", 11.88, "à moins de 3 mois, allez aux urgences tout de suite."),
    ("cta", 0.00, "cta", 5.10, "Sois honnête : tu lui as déjà donné un antipaludéen « au cas où » ?"),
    ("cta", 5.10, "cta", 7.72, "Dis-le-moi en commentaire."),
]


# ---------------------------------------------------------------------------------------
# Bas d'écran : plan poitrine + affinage + filtre
# ---------------------------------------------------------------------------------------
GRADE = ("eq=contrast=1.06:brightness=0.015:saturation=1.10:gamma=1.02,"
         "colorbalance=rs=0.04:gs=0.01:bs=-0.03:rm=0.03:bm=-0.02")


def window(clip, zmax=1.05, head=None, top=None, z=None):
    """Cadrage « torse » : tête entière en haut avec une petite marge, épaules et torse dessous.
    Z ≥ 1/SQUEEZE pour que l'affinage horizontal ne soit pas annulé par la largeur du cadre."""
    f = FACES.get(clip, dict(fx=540, fy=520, fw=400, fh=560))
    Z = z or zmax
    h = HALF / Z
    w = min(W, W / Z / SQUEEZE)
    x = min(max(0, f["fx"] - w / 2), W - w)
    # haut du crâne ≈ 12 % de la hauteur du visage au-dessus du cadre détecté ; marge 4 % du cadre
    y = top if top is not None else f["fy"] - f["fh"] / 2 - 0.12 * f["fh"] - 0.04 * h
    y = min(max(0, y), H - h)
    return round(w), round(h), round(x), round(y)


FRAMING = {"IMG_4567": dict(top=100), "IMG_4569": dict(top=170)}


def render_bottom(k, clip, a, b, z0, dur=None, speed=1.0):
    out = os.path.join(TMP, f"bot{k:03d}.mp4")
    n = max(1, round((dur if dur else (b - a) / speed) * FPS))
    w, h, x, y = window(clip, **FRAMING.get(clip, {}))
    vf = (f"setpts=PTS/{speed:.4f},scale={W}:-2:flags=lanczos,crop={w}:{h}:{x}:{y},"
          f"bilateral=sigmaS=3:sigmaR=0.06,{GRADE},"
          f"scale={2 * W}:{2 * HALF}:flags=lanczos,"
          f"zoompan=z='{z0}+0.03*on/{max(1, n - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{HALF}:fps={FPS},"
          f"unsharp=5:5:0.6,vignette=angle=PI/6,format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-i", src(clip), "-frames:v", str(n), "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


def bottom_plan(tl):
    """Liste (t0, t1, clip, a, b) ; les parties synchronisées reprennent la prise de la voix."""
    plan = []
    for pi, clip, a, b, t0 in tl.pieces:
        p = PARTS[pi]
        if p.get("video") is None:
            plan.append((t0, t0 + b - a, clip, a, b))
    # urg_mois : lèvres de la prise d'origine (même instant de la phrase), sur la nouvelle voix
    s, e = tl.r("urg_mois")
    vc, va = PARTS[PID["urg_mois"]]["video"]
    plan.append((s, e, vc, va, va + (e - s)))
    # lecture du TDR : gestes muets (1 doigt, montre le haut, 2 doigts, montre le haut)
    s, e = tl.r("lecture")
    c = {k: tl.at(*CUES[k]) for k in ("un_point", "neg_dit", "deux_points")}
    m1 = (c["un_point"] + c["neg_dit"]) / 2
    m2 = c["deux_points"] + 0.9
    for t0, t1, clip, a, b in [(s, m1, "IMG_4566", 0.30, 1.30), (m1, c["deux_points"], "IMG_4567", 0.90, 2.70),
                               (c["deux_points"], m2, "IMG_4566", 1.45, 2.60), (m2, e, "IMG_4567", 0.90, 2.70)]:
        plan.append((t0, t1, clip, a, b))
    plan.append((tl.voice_end, tl.total, *TAIL))
    return sorted(plan)


# ---------------------------------------------------------------------------------------
# Haut d'écran
# ---------------------------------------------------------------------------------------
def top_plan(tl):
    plan = []
    at = lambda k: tl.at(*CUES[k])

    def seg(t0, t1, items):
        srcd = sum(i[2] - i[1] for i in items)
        t = t0
        for k, (c, a, b, y0, o) in enumerate(items):
            d = (t1 - t0) * (b - a) / srcd if k < len(items) - 1 else t1 - t
            plan.append(dict(t0=t, t1=t + d, clip=c, a=a, b=b, y0=y0, **o))
            t += d

    seg(*tl.r("hook"), [("IMG_4559", 0.0, 2.0, 240, dict(blur_brand=True))])
    seg(*tl.r("piege"), [("IMG_4541", 0.05, 0.87, 320, {}), ("IMG_4543", 0.0, 1.33, 420, {}),
                         ("IMG_4550", 1.0, 17.0, 240, {}), ("IMG_4551", 0.0, 1.93, 420, {})])
    seg(*tl.r("reflexes"), [("IMG_4553", 0.0, 0.73, 500, {}), ("IMG_4555", 0.0, 6.2, 440, {}),
                            ("IMG_4556", 0.0, 4.2, 480, {})])
    seg(*tl.r("tdr"), [("IMG_4556", 4.2, 7.44, 480, {})])
    s, e = tl.r("lecture")
    seg(s, at("deux_points"), [("IMG_4558", 0.0, 1.43, 280, dict(hold=True))])          # test filmé : 1 trait
    plan.append(dict(t0=at("deux_points"), t1=at("negatif"), still="tdr_resultat.jpg"))  # photo : 2 traits
    seg(at("negatif"), tl.r("resultat")[1], [("IMG_4558", 0.0, 1.43, 280, dict(hold=True))])
    ua, ub = tl.r("urg_a")[0], tl.r("urg_b")[1]
    plan.append(dict(t0=ua, t1=ub, still_from=("IMG_4558", 1.3, 280), dim=True))
    seg(tl.r("cta")[0], tl.total, [("IMG_4559", 0.0, 2.0, 240, dict(blur_brand=True))])
    return plan


def render_top(k, p):
    out = v1.render_top(k, p)  # même rendu qu'en v1…
    graded = os.path.join(TMP, f"topg{k:02d}.mp4")  # …puis même filtre couleur, plus léger
    run([FF, "-y", "-i", out, "-vf", "eq=contrast=1.05:saturation=1.08,colorbalance=rs=0.02:bs=-0.02,unsharp=5:5:0.4,format=yuv420p",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", graded])
    return graded


# Positions des traits sur les deux tests (repère plein cadre 1080x1920, haut d'écran)
MARK_NEG = [(505, 415)]                 # IMG_4558 : ligne C
MARK_POS = [(429, 470), (514, 470)]     # photo retournée : lignes C et P.f


def arrow(color=YELLOW):
    im = Image.new("RGBA", (120, 90), (0, 0, 0, 0))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    d.polygon([(60, 88), (20, 40), (46, 40), (46, 0), (74, 0), (74, 40), (100, 40)], fill=color, outline=(0, 0, 0, 255))
    return im


def build_overlay(path, tl):
    import subprocess
    c = {k: tl.at(*v) for k, v in CUES.items()}
    BY = 220
    B = dict(
        q=label("SOUPÇON DE PALU ?", 70, WHITE, DARK_T), stop=label("NE FAIS PAS ÇA !", 84, WHITE, RED),
        piege=stack(label("PIÈGE", 74, WHITE, RED), label("ANTIPALUDÉEN SANS TEST", 56, WHITE, DARK_T)),
        r1=label("1 · NOTER L'HEURE", 72, WHITE, DARK_T), r2=label("2 · BOIRE / ALLAITER", 72, WHITE, DARK_T),
        r3=label("3 · PARACÉTAMOL = CONFORT", 62, WHITE, DARK_T), h24=label("TDR SOUS 24 H", 78, WHITE, DARK_T),
        un=stack(label("UN TRAIT", 76, WHITE, DARK_T), label("NÉGATIF", 70, WHITE, GREEN)),
        deux=stack(label("DEUX TRAITS", 76, WHITE, DARK_T), label("POSITIF", 70, WHITE, RED)),
        pos=stack(label("POSITIF", 80, WHITE, RED), label("TRAITEMENT COMPLET", 58, WHITE, DARK_T)),
        neg=stack(label("NÉGATIF", 80, WHITE, GREEN), label("CHERCHER UNE AUTRE CAUSE", 54, WHITE, DARK_T)),
        exemple=label("EXEMPLE", 40, (15, 27, 45, 255), YELLOW, pad=16, radius=14),
        urg=label("URGENCES TOUT DE SUITE", 66, WHITE, RED),
        quest=label("?", 260, WHITE, RED, pad=40, radius=120),
        cta=stack(label("DIS-LE EN COMMENTAIRE", 64, WHITE, RED), label("↓", 110, WHITE, DARK_T, pad=18)),
    )
    items = [("Convulsions", "u_conv"), ("Ne tète plus", "u_tete"), ("Vomit tout", "u_vomit"),
             ("Dort trop", "u_dort"), ("Moins de 3 mois", "u_mois")]
    item_im = [label("•  " + s, 60, WHITE, (0, 0, 0, 0), pad=10) for s, _ in items]
    X, AR = red_x(), arrow()
    hook, piege, refl, tdr, lect, res = (tl.r(k) for k in ("hook", "piege", "reflexes", "tdr", "lecture", "resultat"))
    urg = (tl.r("urg_a")[0], tl.r("urg_b")[1])

    def show(L, im, t, t0, t1, y=BY):
        if t0 <= t < t1:
            paste(L, im, W / 2, y, scale=pop(t, t0), alpha=min(1, (t1 - t) / 0.15))

    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    for i in range(round(tl.total * FPS)):
        t = i / FPS
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        show(L, B["q"], t, hook[0], c["pas_ca"])
        show(L, B["stop"], t, c["pas_ca"], hook[1])
        if c["pas_ca"] <= t < hook[1]:
            paste(L, X, W / 2, 560, scale=pop(t, c["pas_ca"], 0.12))
        show(L, B["piege"], t, c["antipalu"], piege[1], BY + 40)
        show(L, B["r1"], t, c["r1"], c["r2"])
        show(L, B["r2"], t, c["r2"], c["r3"])
        show(L, B["r3"], t, c["r3"], refl[1])
        show(L, B["h24"], t, c["h24"], tdr[1])
        show(L, B["un"], t, c["un_point"], c["deux_points"], 720)  # sous la ligne C, pour laisser la flèche visible
        if c["un_point"] <= t < c["deux_points"]:
            for (mx, my) in MARK_NEG:
                paste(L, AR, mx, my - 75, scale=pop(t, c["un_point"]))
        show(L, B["deux"], t, c["deux_points"], c["positif"], BY + 30)
        if c["deux_points"] <= t < c["negatif"]:
            for (mx, my) in MARK_POS:
                paste(L, AR, mx, my - 75, scale=pop(t, c["deux_points"]))
            paste(L, B["exemple"], 150, 880, scale=pop(t, c["deux_points"]))
        show(L, B["pos"], t, c["positif"], c["negatif"], BY + 30)
        show(L, B["neg"], t, c["negatif"], res[1], BY + 30)
        show(L, B["urg"], t, urg[0], urg[1], 170)
        for k, (_, key) in enumerate(items):
            if c[key] <= t < urg[1]:
                paste(L, item_im[k], W / 2, 330 + k * 110, scale=pop(t, c[key]))
        show(L, B["quest"], t, tl.r("cta")[0] + 0.2, tl.voice_end, 480)
        show(L, B["cta"], t, tl.voice_end - 1.2, tl.total + 1, 1480)
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


def write_ass(path, tl):
    head = open(v1.__file__).read().split('head = """')[1].split('"""')[0]
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for pa, a, pb, b, txt in SUBS:
            s, e = tl.at(pa, a), tl.at(pb, b)
            txt = txt.replace(" ?", "\\h?").replace(" :", "\\h:").replace(" !", "\\h!")
            txt = RED_WORDS.sub(lambda m: "{\\1c&H303BFF&}" + m.group(0) + "{\\1c&HFFFFFF&}", txt)
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Sub,,0,0,0,,{{\\pos(540,960)}}{txt}\n")


def build_voice(path, tl):
    ins, ch = [], []
    for k, (_, clip, a, b, _) in enumerate(tl.pieces):
        d = b - a
        ins += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src(clip)]
        ch.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=mono,loudnorm=I=-20:TP=-3,"
                  f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.02):.3f}:d=0.02[a{k}]")
    n = len(tl.pieces)
    ins += ["-f", "lavfi", "-t", f"{tl.total - tl.voice_end:.3f}", "-i", "anullsrc=r=48000:cl=mono"]
    fc = ";".join(ch) + ";" + "".join(f"[a{j}]" for j in range(n)) + f"[{n}:a]concat=n={n + 1}:v=0:a=1,{VOICE_FX}[o]"
    run([FF, "-y", *ins, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", path])


def build_sfx(tl, music_p, fx_p):
    from scipy.io import wavfile
    S = SPEED
    c = {k: tl.at(*v) / S for k, v in CUES.items()}
    r = {k: (a / S, b / S) for k, (a, b) in zip(PID, tl.rng)}
    total = tl.total / S + 0.5
    mus, fx = np.zeros(int(total * sfx.SR)), np.zeros(int(total * sfx.SR))
    sfx._place(fx, sfx.heartbeat(r["hook"][1]), 0.0, 0.5)
    for t in [r["piege"][0], c["r1"], c["r2"], c["r3"], c["h24"], c["un_point"], c["deux_points"], c["negatif"], r["cta"][0]]:
        sfx._place(fx, sfx.whoosh(0.5), t - 0.45, 0.30)  # fini avant le mot : ne masque pas « deux »
    sfx._place(mus, sfx.dark_bed(c["deux_points"] - r["piege"][0]), r["piege"][0], 0.26)
    sfx._place(fx, sfx.ticktock(r["tdr"][0] - r["reflexes"][0]), r["reflexes"][0], 0.16)
    sfx._place(fx, sfx.sub_drop(), r["urg_a"][0], 0.7)
    sfx._place(mus, sfx.driving_bed(r["urg_b"][1] - r["urg_a"][0]), r["urg_a"][0], 0.24)
    sfx._place(mus, sfx.neutral_bed(total - r["cta"][0]), r["cta"][0], 0.18)
    for x, pth in ((mus, music_p), (fx, fx_p)):
        wavfile.write(pth, sfx.SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    v1.TMP = TMP
    tl = TL()
    print(f"Durée avant accélération : {tl.total:.2f} s → après ×{SPEED} : {tl.total / SPEED:.2f} s")
    for p, (a, b) in zip(PARTS, tl.rng):
        print(f"  {p['id']:9s} {a:6.2f}-{b:6.2f}")
    tops = [render_top(k, p) for k, p in enumerate(top_plan(tl))]
    bots = []
    for k, (t0, t1, clip, a, b) in enumerate(bottom_plan(tl)):
        dur = t1 - t0
        speed = max(0.3, (b - a) / dur) if clip in ("IMG_4566", "IMG_4567") else 1.0
        bots.append(render_bottom(k, clip, a, b, 1.0 if k % 2 == 0 else 1.05, dur=dur, speed=speed))
    top = concat(tops, os.path.join(TMP, "top.mp4"))
    bot = concat(bots, os.path.join(TMP, "bot.mp4"))
    ov = os.path.join(TMP, "overlay.mov")
    build_overlay(ov, tl)
    ass = os.path.join(TMP, "subs.ass")
    write_ass(ass, tl)
    voice = os.path.join(TMP, "voix.wav")
    build_voice(voice, tl)
    mus, fxp = os.path.join(TMP, "music.wav"), os.path.join(TMP, "fx.wav")
    build_sfx(tl, mus, fxp)
    dst = os.path.join(OUT, "ep02_montage_v2.mp4")
    n = round(tl.total * FPS)
    fc = (f"[0:v]trim=end_frame={n}[t];[1:v]trim=end_frame={n}[b];[t][b]vstack=inputs=2[s];"
          f"[s][2:v]overlay=0:0:format=auto,ass='{ass}',setpts=PTS/{SPEED},fps={FPS},format=yuv420p[v];"
          # musique passée sous 250 Hz (sinon elle masque « fais-le boire », « dans les 24 heures ») ;
          # musique + effets baissés ensemble sous la voix
          f"[3:a]atempo={SPEED},asplit=2[vo][key];[4:a]lowpass=f=250[mu];"
          f"[mu][5:a]amix=inputs=2:duration=longest:normalize=0[bed];"
          f"[bed][key]sidechaincompress=threshold=0.02:ratio=8:attack=5:release=300[m];"
          f"[vo][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
          f"aformat=channel_layouts=stereo[a]")
    run([FF, "-y", "-i", top, "-i", bot, "-i", ov, "-i", voice, "-i", mus, "-i", fxp, "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", dst])
    print("Export :", dst)


if __name__ == "__main__":
    main()
