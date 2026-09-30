"""Montage de l'épisode 2 — « Soupçon de palu : l'erreur réflexe » (écran partagé 50/50).

Haut : étapes réelles du TDR (rushes 4K du Drive) · Bas : Abdou face caméra (notes WhatsApp + IMG_4570).
Usage : python3 montage_ep2.py → out/ep02_montage_v1.mp4 (1080x1920, 30 i/s)

Les blancs coupés sont uniquement des silences mesurés (énergie < plancher + 10 dB pendant ≥ 0,25 s),
situés entre deux mots de la transcription, et on garde 0,08 s de marge de chaque côté.
Les sous-titres reprennent ce qu'Abdou dit réellement (règle fixée à l'épisode 1).
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
OUT = os.path.join(HERE, "out")
TMP = os.path.join(OUT, "tmp")
sys.path.insert(0, os.path.join(HERE, "..", "ep01-fievre-bebe"))
import sfx  # noqa: E402  (habillage sonore synthétisé de l'épisode 1)

W, H, HALF, FPS = 1080, 1920, 960, 30
SPEED = 1.18  # même accélération globale que l'épisode 1
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RED, WHITE, YELLOW = (229, 57, 53, 255), (255, 255, 255, 255), (255, 193, 7, 255)
DARK_T, GREEN = (15, 27, 45, 225), (46, 160, 67, 255)


def ffbin():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FF = ffbin()


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit(r.stderr[-3000:])


def src(name):
    if name.startswith("WA"):
        return os.path.join(A, "whatsapp", f"{name}.mp4")
    return os.path.join(A, "drive", f"{name}.mov")


# ---------------------------------------------------------------------------------------
# Voix : 6 phrases du script validé (prise, début, fin, cadrage du visage y0 dans 1080x1920)
# ---------------------------------------------------------------------------------------
LINES = [
    dict(nom="Accroche", clip="IMG_4570", a=0.10, b=5.52, y0=280),
    dict(nom="Piège", clip="WA0037", a=0.40, b=9.12, y0=220),
    dict(nom="Réflexes", clip="WA0036", a=0.15, b=17.78, y0=280),
    dict(nom="TDR", clip="WA0033", a=0.00, b=13.70, y0=260),
    dict(nom="Urgences", clip="WA0035", a=0.45, b=11.88, y0=300),
    dict(nom="CTA", clip="WA0034", a=0.00, b=7.72, y0=150),
]
TAIL = dict(clip="IMG_4569", a=0.20, b=1.85, y0=160)  # doigt vers le bas, bouche fermée (après la voix)


def energy(path, sr=16000):
    r = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                       stdout=subprocess.PIPE)
    y = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
    hop = sr // 100
    n = len(y) // hop
    return 20 * np.log10(np.sqrt(np.mean(y[: n * hop].reshape(n, hop) ** 2, 1)) + 1e-6)


def kept_ranges(line):
    """Morceaux gardés : on retire les silences mesurés ≥ 0,25 s (réduits de 0,08 s de chaque côté)."""
    db = energy(src(line["clip"]))
    thr = np.percentile(db, 10) + 10
    quiet = db < thr
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= 0.25:
                runs.append((i * 0.01 + 0.08, j * 0.01 - 0.08))
            i = j
        else:
            i += 1
    a, b = line["a"], line["b"]
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
        self.pieces = []  # (ligne, clip, a, b, t0)
        self.line_rng = []
        t = 0.0
        for li, line in enumerate(LINES):
            t0 = t
            for a, b in kept_ranges(line):
                self.pieces.append((li, line["clip"], a, b, t))
                t = round((t + b - a) * FPS) / FPS
            self.line_rng.append((t0, t))
        self.voice_end = t
        self.total = t + (TAIL["b"] - TAIL["a"])

    def at(self, li, raw):
        """Instant brut dans la prise de la ligne li → instant de sortie."""
        cands = [p for p in self.pieces if p[0] == li]
        for _, _, a, b, t0 in cands:
            if raw <= b:
                return t0 + max(0.0, raw - a)
        _, _, a, b, t0 = cands[-1]
        return t0 + b - a


# Mots-repères (instants bruts dans chaque prise, relevés sur la transcription + l'énergie)
CUES = {
    "pas_ca": (0, 4.22), "antipalu": (1, 2.91),
    "r1": (2, 1.87), "r2": (2, 6.07), "r3": (2, 12.43),
    "h24": (3, 2.70), "positif": (3, 5.95), "negatif": (3, 10.30),
    "u_conv": (4, 1.10), "u_tete": (4, 2.90), "u_vomit": (4, 4.55), "u_dort": (4, 6.12), "u_mois": (4, 7.85),
    "u_urg": (4, 9.70),
}

SUBS = [
    (0, 0.10, 2.60, "Tu soupçonnes le palu chez ton enfant ?"),
    (0, 2.60, 5.52, "Ne fais SURTOUT PAS ça en premier !"),
    (1, 0.40, 5.00, "L'erreur classique : lui donner un antipaludéen sans faire le test."),
    (1, 5.00, 9.12, "Si c'est une autre maladie, tu perds un temps précieux."),
    (2, 0.15, 1.80, "Trois bons réflexes."),
    (2, 1.80, 5.65, "Un : note l'heure du début de la fièvre."),
    (2, 5.65, 12.35, "Deux : fais-le boire, ou allaite-le."),
    (2, 12.35, 17.78, "Trois : paracétamol pour son confort, et à la bonne dose."),
    (3, 0.00, 4.95, "Puis, allez au centre de santé le plus proche dans les 24 heures pour le TDR."),
    (3, 4.95, 9.60, "Si TDR positif : traitement complet, jusqu'au bout."),
    (3, 9.60, 13.70, "Si TDR négatif : cherchez une autre cause."),
    (4, 0.45, 6.75, "Mais s'il convulse, ne tète plus, vomit tout, dort trop,"),
    (4, 6.75, 11.88, "à moins de 3 mois, allez aux urgences tout de suite."),
    (5, 0.00, 5.10, "Sois honnête : tu lui as déjà donné un antipaludéen « au cas où » ?"),
    (5, 5.10, 7.72, "Dis-le-moi en commentaire."),
]


# ---------------------------------------------------------------------------------------
# Haut d'écran : étapes du TDR (clip, début, fin, y0 du cadrage) — durées ajustées à la voix
# ---------------------------------------------------------------------------------------
def top_plan(tl):
    L = tl.line_rng
    pos, neg = tl.at(*CUES["positif"]), tl.at(*CUES["negatif"])
    plan = []

    def seg(t0, t1, items):
        """Répartit [t0, t1] entre des plans (clip, a, b, y0, opts) au prorata de leur durée source."""
        srcd = sum(i[2] - i[1] for i in items)
        t = t0
        for k, (c, a, b, y0, o) in enumerate(items):
            d = (t1 - t0) * (b - a) / srcd if k < len(items) - 1 else t1 - t
            plan.append(dict(t0=t, t1=t + d, clip=c, a=a, b=b, y0=y0, **o))
            t += d

    seg(L[0][0], L[0][1], [("IMG_4559", 0.0, 2.0, 240, dict(blur_brand=True))])            # l'antipaludéen
    seg(L[1][0], L[1][1], [("IMG_4541", 0.05, 0.87, 320, {}), ("IMG_4543", 0.0, 1.33, 420, {}),
                           ("IMG_4550", 1.0, 17.0, 240, {}), ("IMG_4551", 0.0, 1.93, 420, {})])  # le kit, sorti du sachet
    seg(L[2][0], L[2][1], [("IMG_4553", 0.0, 0.73, 500, {}), ("IMG_4555", 0.0, 6.2, 440, {}),
                           ("IMG_4556", 0.0, 4.2, 480, {})])                                     # sang, tampon, migration
    seg(L[3][0], pos, [("IMG_4556", 4.2, 7.44, 480, {})])
    plan.append(dict(t0=pos, t1=neg, still="tdr_resultat.jpg"))                                  # exemple positif (photo)
    seg(neg, L[3][1], [("IMG_4558", 0.0, 1.43, 280, dict(hold=True))])                          # le test filmé : négatif
    plan.append(dict(t0=L[4][0], t1=L[4][1], still_from=("IMG_4558", 1.3, 280), dim=True))      # urgences : fond sombre
    seg(L[5][0], tl.total, [("IMG_4559", 0.0, 2.0, 240, dict(blur_brand=True))])                # retour à l'antipaludéen
    return plan


def fit(scale_y0):
    return f"scale={W}:-2:flags=lanczos,crop={W}:{HALF}:0:{scale_y0},setsar=1"


def render_top(k, p):
    out = os.path.join(TMP, f"top{k:02d}.mp4")
    dur = p["t1"] - p["t0"]
    n = max(1, round(dur * FPS))
    if "still" in p or "still_from" in p:
        if "still" in p:
            im = Image.open(os.path.join(A, p["still"])).convert("RGB").rotate(180)  # photo prise à l'envers
            s = W / im.width
            im = im.resize((W, round(im.height * s)), Image.LANCZOS)
            bg = Image.new("RGB", (W, HALF), (30, 30, 30))
            bg.paste(im, (0, (HALF - im.height) // 2))
        else:
            c, t, y0 = p["still_from"]
            png = os.path.join(TMP, f"still{k}.png")
            run([FF, "-y", "-ss", str(t), "-i", src(c), "-frames:v", "1", "-vf", fit(y0), png])
            bg = Image.open(png).convert("RGB")
            if p.get("dim"):
                bg = Image.blend(bg, Image.new("RGB", bg.size, (10, 10, 15)), 0.72)
        frames = []
        for i in range(n):
            z = 1 + 0.06 * i / max(1, n - 1)
            cw, ch = W / z, HALF / z
            frames.append(bg.resize((W, HALF), Image.LANCZOS, box=((W - cw) / 2, (HALF - ch) / 2, (W + cw) / 2, (HALF + ch) / 2)))
        return encode(frames, out, HALF)
    speed = (p["b"] - p["a"]) / dur
    vf = [f"setpts=PTS/{speed:.4f}", fit(p["y0"])]
    if p.get("blur_brand"):  # nom commercial flouté (on dénonce un usage, pas une marque)
        vf.append("split[m][b];[b]crop=380:360:280:260,boxblur=18:3[bb];[m][bb]overlay=280:260")
    vf.append(f"fps={FPS},format=yuv420p")
    if p.get("hold"):
        vf.append(f"tpad=stop_mode=clone:stop_duration={dur:.3f}")
    run([FF, "-y", "-ss", f"{p['a']:.3f}", "-t", f"{p['b'] - p['a'] + 0.2:.3f}", "-i", src(p["clip"]),
         "-filter_complex", ",".join(vf), "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


def encode(frames, out, h):
    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{h}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in frames:
        p.stdin.write(f.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()
    return out


def render_bottom(k, clip, a, b, y0, z0):
    out = os.path.join(TMP, f"bot{k:02d}.mp4")
    n = max(1, round((b - a) * FPS))
    vf = (f"scale={W}:-2:flags=lanczos,crop={W}:{HALF}:0:{y0},scale={2 * W}:{2 * HALF},"
          f"zoompan=z='{z0}+0.03*on/{max(1, n - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{HALF}:fps={FPS},"
          f"format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-i", src(clip), "-frames:v", str(n), "-vf", vf, "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


def concat(files, out):
    lst = out + ".txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in files)
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    return out


# ---------------------------------------------------------------------------------------
# Calque graphique (plein cadre 1080x1920)
# ---------------------------------------------------------------------------------------
def font(s):
    return ImageFont.truetype(FONT, s)


def label(text, size, fg, bg, pad=30, radius=24):
    f = font(size)
    l, t, r, bb = f.getbbox(text)
    im = Image.new("RGBA", (r - l + 2 * pad, bb - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius, fill=bg)
    d.text((pad - l, pad - t), text, font=f, fill=fg)
    return im


def stack(*ims, gap=14):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in ims:
        out.alpha_composite(i, ((w - i.width) // 2, y))
        y += i.height + gap
    return out


def pop(t, t0, d=0.18):
    p = (t - t0) / d
    if p <= 0:
        return 0
    if p >= 1:
        return 1
    return 1.12 * math.sin(p * math.pi / 2) if p < 0.7 else 1.12 - 0.12 * (p - 0.7) / 0.3


def paste(L, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: round(v * alpha)))
    L.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def red_x(size=520, width=46):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.line((30, 30, size - 30, size - 30), fill=RED, width=width)
    d.line((size - 30, 30, 30, size - 30), fill=RED, width=width)
    return im


def build_overlay(path, tl):
    L = tl.line_rng
    c = {k: tl.at(*v) for k, v in CUES.items()}
    BY = 220  # bannières en haut de la moitié supérieure (sous l'interface TikTok)
    B = dict(
        q=label("SOUPÇON DE PALU ?", 70, WHITE, DARK_T),
        stop=label("NE FAIS PAS ÇA !", 84, WHITE, RED),
        piege=stack(label("PIÈGE", 74, WHITE, RED), label("ANTIPALUDÉEN SANS TEST", 56, WHITE, DARK_T)),
        r1=label("1 · NOTER L'HEURE", 72, WHITE, DARK_T), r2=label("2 · BOIRE / ALLAITER", 72, WHITE, DARK_T),
        r3=label("3 · PARACÉTAMOL = CONFORT", 62, WHITE, DARK_T),
        h24=label("TDR SOUS 24 H", 78, WHITE, DARK_T),
        pos=stack(label("POSITIF", 80, WHITE, RED), label("TRAITEMENT COMPLET", 58, WHITE, DARK_T)),
        neg=stack(label("NÉGATIF", 80, WHITE, GREEN), label("CHERCHER UNE AUTRE CAUSE", 54, WHITE, DARK_T)),
        exemple=label("EXEMPLE", 40, DARK_T[:3] + (255,), YELLOW, pad=16, radius=14),
        urg=label("URGENCES TOUT DE SUITE", 66, WHITE, RED),
        quest=label("?", 260, WHITE, RED, pad=40, radius=120),
        cta=stack(label("DIS-LE EN COMMENTAIRE", 64, WHITE, RED), label("↓", 110, WHITE, DARK_T, pad=18)),
    )
    items = [("Convulsions", "u_conv"), ("Ne tète plus", "u_tete"), ("Vomit tout", "u_vomit"),
             ("Dort trop", "u_dort"), ("Moins de 3 mois", "u_mois")]
    item_im = [label("•  " + s, 60, WHITE, (0, 0, 0, 0), pad=10) for s, _ in items]
    X = red_x()

    def show(Lr, im, t, t0, t1, y=BY):
        if t0 <= t < t1:
            fade = min(1, (t1 - t) / 0.15)
            paste(Lr, im, W / 2, y, scale=pop(t, t0), alpha=fade)

    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    for i in range(round(tl.total * FPS)):
        t = i / FPS
        Lr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        show(Lr, B["q"], t, L[0][0], c["pas_ca"])
        show(Lr, B["stop"], t, c["pas_ca"], L[0][1])
        if c["pas_ca"] <= t < L[0][1]:
            paste(Lr, X, W / 2, 560, scale=pop(t, c["pas_ca"], 0.12))
        show(Lr, B["piege"], t, c["antipalu"], L[1][1], BY + 40)
        show(Lr, B["r1"], t, c["r1"], c["r2"])
        show(Lr, B["r2"], t, c["r2"], c["r3"])
        show(Lr, B["r3"], t, c["r3"], L[2][1])
        show(Lr, B["h24"], t, c["h24"], c["positif"])
        show(Lr, B["pos"], t, c["positif"], c["negatif"], BY + 30)
        if c["positif"] <= t < c["negatif"]:
            paste(Lr, B["exemple"], 150, 880, scale=pop(t, c["positif"]))
        show(Lr, B["neg"], t, c["negatif"], L[3][1], BY + 30)
        show(Lr, B["urg"], t, L[4][0], L[4][1], 170)
        for k, (_, key) in enumerate(items):
            if c[key] <= t < L[4][1]:
                paste(Lr, item_im[k], W / 2, 330 + k * 110, scale=pop(t, c[key]))
        show(Lr, B["quest"], t, L[5][0] + 0.2, tl.voice_end, 480)
        show(Lr, B["cta"], t, tl.voice_end - 1.2, tl.total + 1, 1480)
        p.stdin.write(Lr.tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------------------------------
# Sous-titres (au niveau de la séparation, comme le mot « Physics » de la vidéo de référence)
# ---------------------------------------------------------------------------------------
import re  # noqa: E402

RED_WORDS = re.compile(r"\b(pièges?|paracétamol)\b", re.IGNORECASE)


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_ass(path, tl):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for li, a, b, txt in SUBS:
            s, e = tl.at(li, a), tl.at(li, b)
            txt = txt.replace(" ?", "\\h?").replace(" :", "\\h:").replace(" !", "\\h!")
            txt = RED_WORDS.sub(lambda m: "{\\1c&H303BFF&}" + m.group(0) + "{\\1c&HFFFFFF&}", txt)
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Sub,,0,0,0,,{{\\pos(540,960)}}{txt}\n")


# ---------------------------------------------------------------------------------------
# Audio : voix naturelle (réglages v6 de l'épisode 1) + habillage sonore
# ---------------------------------------------------------------------------------------
VOICE_FX = ",".join(["highpass=f=80", "afftdn=nf=-30", "equalizer=f=380:t=q:w=1.2:g=-2",
                     "equalizer=f=3000:t=o:w=1.5:g=5", "treble=g=3:f=6000", "deesser",
                     "acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=2"])


def build_voice(path, tl):
    ins, ch = [], []
    for k, (_, clip, a, b, _) in enumerate(tl.pieces):
        d = b - a
        ins += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", src(clip)]
        ch.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=mono,loudnorm=I=-20:TP=-3,"
                  f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.02):.3f}:d=0.02[a{k}]")
    n = len(tl.pieces)
    k = n
    ins += ["-f", "lavfi", "-t", f"{tl.total - tl.voice_end:.3f}", "-i", "anullsrc=r=48000:cl=mono"]
    fc = ";".join(ch) + ";" + "".join(f"[a{j}]" for j in range(n)) + f"[{k}:a]concat=n={n + 1}:v=0:a=1,{VOICE_FX}[o]"
    run([FF, "-y", *ins, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", path])


def build_sfx(tl, music_p, fx_p):
    S, L = SPEED, tl.line_rng
    c = {k: tl.at(*v) / S for k, v in CUES.items()}
    total = tl.total / S + 0.5
    mus, fx = np.zeros(int(total * sfx.SR)), np.zeros(int(total * sfx.SR))
    l = [(a / S, b / S) for a, b in L]
    sfx._place(fx, sfx.heartbeat(l[0][1]), 0.0, 0.5)
    for t in [l[1][0], c["r1"], c["r2"], c["r3"], c["h24"], c["negatif"], l[5][0]]:
        sfx._place(fx, sfx.whoosh(0.5), t - 0.2, 0.30)
    sfx._place(mus, sfx.dark_bed(c["positif"] - l[1][0]), l[1][0], 0.26)
    sfx._place(fx, sfx.ticktock(l[3][0] - l[2][0]), l[2][0], 0.16)
    sfx._place(fx, sfx.ding(), c["positif"], 0.30)
    sfx._place(fx, sfx.sub_drop(), l[4][0], 0.7)
    sfx._place(mus, sfx.driving_bed(l[4][1] - l[4][0]), l[4][0], 0.24)
    sfx._place(mus, sfx.neutral_bed(total - l[5][0]), l[5][0], 0.18)
    from scipy.io import wavfile
    for x, pth in ((mus, music_p), (fx, fx_p)):
        wavfile.write(pth, sfx.SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    tl = TL()
    print(f"Durée avant accélération : {tl.total:.2f} s → après ×{SPEED} : {tl.total / SPEED:.2f} s")
    for i, (a, b) in enumerate(tl.line_rng):
        print(f"  {LINES[i]['nom']:9s} {a:6.2f}-{b:6.2f}  ({len([p for p in tl.pieces if p[0] == i])} morceaux)")
    tops = [render_top(k, p) for k, p in enumerate(top_plan(tl))]
    bots, z = [], 0
    for k, (li, clip, a, b, t0) in enumerate(tl.pieces):
        bots.append(render_bottom(k, clip, a, b, LINES[li]["y0"], 1.0 if z % 2 == 0 else 1.05))
        z += 1
    bots.append(render_bottom(len(bots), TAIL["clip"], TAIL["a"], TAIL["b"], TAIL["y0"], 1.0))
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
    dst = os.path.join(OUT, "ep02_montage_v1.mp4")
    n = round(tl.total * FPS)
    fc = (f"[0:v]trim=end_frame={n}[t];[1:v]trim=end_frame={n}[b];[t][b]vstack=inputs=2[s];"
          f"[s][2:v]overlay=0:0:format=auto,ass='{ass}',setpts=PTS/{SPEED},fps={FPS},format=yuv420p[v];"
          f"[3:a]atempo={SPEED},asplit=2[vo][key];[4:a][key]sidechaincompress=threshold=0.03:ratio=5:attack=15:release=350[m];"
          f"[vo][m][5:a]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[a]")
    run([FF, "-y", "-i", top, "-i", bot, "-i", ov, "-i", voice, "-i", mus, "-i", fxp, "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", dst])
    print("Export :", dst)


if __name__ == "__main__":
    main()
