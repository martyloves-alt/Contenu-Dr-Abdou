"""Montage « trucages magiques » de l'épisode 1 à partir des rushes d'Abdou.

Usage : python3 montage.py            → out/ep01_montage_v1.mp4 (1080x1920, 30 i/s)
        python3 montage.py --voix-brute → même montage sans traitement de la voix

Rushes attendus dans assets/rushes/ (noms d'origine lv_0_*.mp4), photo dans assets/photos/.
Tous les timings ci-dessous ont été relevés image par image sur les rushes (voir rapport).
Le texte affiché (sous-titres, checklist, badges) est le script validé, mot pour mot.
"""
import argparse
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RUSHES = os.path.join(HERE, "assets", "rushes")
PHOTOS = os.path.join(HERE, "assets", "photos")
OUT = os.path.join(HERE, "out")
TMP = os.path.join(OUT, "tmp_montage")
W, H, FPS = 1080, 1920, 30
SPEED = 1.08  # accélération finale (voix à hauteur conservée) pour tenir ~45 s
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RED, WHITE, YELLOW = (229, 57, 53, 255), (255, 255, 255, 255), (255, 193, 7, 255)
DARK, DARK_T = (15, 27, 45, 255), (15, 27, 45, 225)


def ffmpeg_bin():
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


FF = ffmpeg_bin()


def rush(stamp):
    return os.path.join(RUSHES, f"lv_0_20260923{stamp}.mp4")


# Recadrage commun : retire le filigrane CapCut (bas droite, y ≥ 795 sur 852) en gardant le 9:16.
CROP = "crop=444:790:18:0,scale=1080:1920:flags=lanczos,setsar=1"
S_CROP = 1080 / 444  # facteur source → sortie


def src_xy(x, y):
    return (x - 18) * S_CROP, y * S_CROP


# Égalisation couleur de la prise 205741 (dominante bleue) sur le mur de 204549 : gains R,G,B mesurés.
COLORFIX = "colorchannelmixer=rr=1.5:gg=1.14:bb=1.0"

# ---------------------------------------------------------------------------------------
# Découpage. Chaque section : audio = morceaux de la prise parlée ; vidéo = plans dont la
# somme des durées = durée audio. (id, début, fin[, effet])
# ---------------------------------------------------------------------------------------
SECTIONS = [
    dict(nom="Accroche", audio=[("204549", 0.00, 4.85)], video=[
        ("204725", 0.50, 1.60, "whip_out"),      # main qui avance et couvre l'objectif
        ("205741", 0.30, 2.10, "colorfix"),      # main qui recule avec le thermomètre
        ("204549", 2.90, 4.85, None),            # visage : « …pensez plutôt palu »
    ]),
    dict(nom="Annonce piège 3", audio=[("210605", 0.00, 3.75)], video=[
        ("205853", 0.25, 1.45, None),            # main ouverte tendue : badge dans la paume
        ("210605", 1.20, 3.75, None),
    ]),
    dict(nom="Piège 1", audio=[("210310", 2.10, 7.00)], video=[
        ("210310", 2.10, 4.95, None),
        ("210033", 0.70, 1.90, None),            # thermomètre filmé
        ("photo_thermo", 0, 0.85, None),         # zoom rapide 38,3 °C (photo fournie)
    ]),
    dict(nom="Piège 2", audio=[("210713", 0.15, 4.20), ("210713", 5.60, 8.45), ("210713", 10.05, 11.00)], video=[
        ("210713", 0.15, 4.20, None),
        ("210713", 5.60, 8.45, "punch"),         # coupes de silence masquées par un zoom
        ("210713", 10.05, 11.00, None),
    ]),
    dict(nom="Piège 3", audio=[("210521", 0.00, 7.70)], video=[
        ("210521", 0.00, 1.00, None),
        ("205559", 0.90, 2.50, None),            # la boîte de paracétamol entre dans le cadre
        ("210521", 2.60, 5.30, None),
        ("205947", 0.00, 0.80, None),            # il pose la boîte
        ("204815", 0.15, 0.95, None),            # il attrape en l'air et plaque
        ("still_205947", 1.75, 0.80, "impact"),  # la boîte, barre rouge plaquée
    ]),
    dict(nom="TDR", audio=[("205654", 0.00, 5.15)], video=[
        ("205654", 0.00, 1.40, None),
        ("210213", 1.50, 2.10, "whip_out"),      # balayage de la main vers la droite…
        ("210750", 0.00, 1.30, "whip_in"),       # …le TDR arrive par la droite
        ("210750", 5.05, 6.90, None),            # gros plan TDR
    ]),
    dict(nom="Action", audio=[("210140", 0.00, 9.90)], video=[
        ("204909", 0.95, 1.85, None),            # balayage 1 → ligne 1
        ("210140", 0.90, 3.00, None),
        ("204909", 4.55, 5.35, None),            # balayage 2 → ligne 2
        ("210140", 3.80, 5.80, None),
        ("204909", 10.85, 11.55, None),          # balayage 3 → ligne 3
        ("210140", 6.50, 9.90, None),            # checklist complète tenue
    ]),
    dict(nom="Appel à l'action", audio=[("205005", 0.00, 3.10), ("205005", 4.60, 6.60)], video=[
        ("205005", 0.00, 3.10, None),
        ("205005", 4.60, 6.60, "punch"),
    ]),
]


def sec_starts():
    t, out = 0.0, []
    for s in SECTIONS:
        out.append(t)
        t += sum(b - a for _, a, b in s["audio"])
    return out, t


STARTS, TOTAL = sec_starts()


def at(section_idx, t):
    return STARTS[section_idx] + t


# Sous-titres : script validé, calés sur la parole (temps dans la section).
SUBS = [
    (0, 0.00, 2.90, "Fièvre chez bébé ? Ce n'est pas les dents."),
    (0, 2.90, 4.85, "Pense palu."),
    (1, 0.00, 1.35, "Et le piège n°3,"),
    (1, 1.35, 3.75, "beaucoup de parents le font chaque soir."),
    (2, 0.00, 2.05, "Piège 1 : croire aux dents."),
    (2, 2.05, 4.90, "Les dents ne donnent pas de forte fièvre."),
    (3, 0.00, 0.90, "Piège 2 : attendre."),
    (3, 0.90, 4.05, "Au Bénin, un enfant fiévreux, on cherche d'abord le palu."),
    (3, 4.05, 7.85, "Sans traitement, en 24 heures, il peut devenir grave."),
    (4, 0.00, 2.50, "Piège 3 : le paracétamol."),
    (4, 2.50, 5.30, "Il fait baisser la fièvre."),
    (4, 5.30, 7.70, "Il ne soigne pas le palu."),
    (5, 0.00, 2.50, "Seul un test le dit : le TDR."),
    (5, 2.50, 3.80, "Une goutte de sang."),
    (5, 3.80, 5.15, "15 à 20 minutes."),
    (6, 0.00, 3.00, "Fièvre ? Test au centre de santé dans les 24 heures."),
    (6, 3.00, 4.90, "Convulsions, ne tète plus, vomit tout, dort trop ?"),
    (6, 4.90, 6.40, "Urgences. Tout de suite."),
    (6, 6.40, 9.90, "Moins de 3 mois ? Urgences."),
    (7, 0.00, 3.10, "Chez toi, on dit quoi quand bébé est chaud ?"),
    (7, 3.10, 5.10, "Écris un seul mot en commentaire."),
]

CHECKLIST = [
    ("Fièvre ?", "Test au centre de santé dans les 24 heures.", False),
    ("Convulsions, ne tète plus, vomit tout, dort trop ?", "Urgences. Tout de suite.", True),
    ("Moins de 3 mois ?", "Urgences.", True),
]
CHECK_T = [(0.25, 0.85), (3.05, 3.75), (5.85, 6.45)]  # révélation de chaque ligne (section 6)


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit(r.stderr[-3000:])


# ---------------------------------------------------------------------------------------
# Vidéo
# ---------------------------------------------------------------------------------------
def render_piece(k, piece):
    sid, a, b, fx = piece
    out = os.path.join(TMP, f"p{k:02d}.mp4")
    if sid == "photo_thermo":
        return photo_zoom(out, b - a)
    if sid.startswith("still_"):
        return still_impact(out, sid[6:], a, b)
    dur = b - a
    n = round(dur * FPS)
    vf = []
    if fx == "colorfix":
        vf.append(COLORFIX)
    vf.append(CROP)
    if fx == "punch":
        vf.append("scale=1188:2112,crop=1080:1920")
    if fx == "whip_out":
        vf.append(f"gblur=sigma=45:sigmaV=0.01:enable='gte(t,{dur - 0.10:.3f})'")
    if fx == "whip_in":
        vf.append("gblur=sigma=45:sigmaV=0.01:enable='lt(t,0.10)'")
    vf.append(f"fps={FPS},format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-i", rush(sid), "-frames:v", str(n), "-vf", ",".join(vf),
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", out])
    return out


def encode_frames(frames, out):
    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p", out],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in frames:
        p.stdin.write(f.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()
    return out


def photo_zoom(out, dur):
    """Zoom rapide sur l'écran du thermomètre (38,3 °C) : 1 → 2,2 en 0,3 s puis tenu."""
    im = Image.open(os.path.join(PHOTOS, "thermometre-38-3.jpg")).convert("RGB")
    lcd = (355, 392)  # centre de l'écran LCD sur la photo (735x817)
    s = H / im.height
    base = im.resize((round(im.width * s), H), Image.LANCZOS)
    cx, cy = lcd[0] * s, lcd[1] * s
    frames = []
    n = round(dur * FPS)
    for i in range(n):
        p = min(1.0, i / (0.3 * FPS))
        z = 1 + 1.2 * (1 - (1 - p) ** 3)
        cw, ch = W / z, H / z
        x0 = min(max(cx - cw / 2, 0), base.width - cw)
        y0 = min(max(cy - ch / 2, 0), base.height - ch)
        frames.append(base.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)))
    return encode_frames(frames, out)


def still_impact(out, sid, t, dur):
    """Image fixe de la boîte ; petit « choc » de zoom au moment où la barre est plaquée."""
    png = os.path.join(TMP, f"still_{sid}.png")
    run([FF, "-y", "-ss", f"{t:.3f}", "-i", rush(sid), "-frames:v", "1", "-vf", CROP, png])
    base = Image.open(png).convert("RGB")
    frames = []
    for i in range(round(dur * FPS)):
        z = 1.07 - 0.07 * min(1, i / 5)
        cw, ch = W / z, H / z
        frames.append(base.resize((W, H), Image.LANCZOS, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)))
    return encode_frames(frames, out)


# ---------------------------------------------------------------------------------------
# Calque graphique animé (RGBA, image par image)
# ---------------------------------------------------------------------------------------
def font(sz):
    return ImageFont.truetype(FONT, sz)


def label(text, size, fg, bg, pad=34, radius=26):
    f = font(size)
    l, t, r, b = f.getbbox(text)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius, fill=bg)
    d.text((pad - l, pad - t), text, font=f, fill=fg)
    return im


def stack(*ims, gap=18):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in ims:
        out.alpha_composite(i, ((w - i.width) // 2, y))
        y += i.height + gap
    return out


def paste_center(layer, im, cx, cy, scale=1.0, alpha=1.0, angle=0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    if angle:
        im = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: round(v * alpha))
        im = im.copy()
        im.putalpha(a)
    layer.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def pop(t, t0, dur=0.18):
    """Courbe d'apparition 0 → 1,12 → 1."""
    p = (t - t0) / dur
    if p <= 0:
        return 0
    if p >= 1:
        return 1
    return 1.12 * math.sin(p * math.pi / 2) if p < 0.7 else 1.12 - 0.12 * (p - 0.7) / 0.3


def wrap(text, f, maxw):
    words, lines, cur = text.replace(" ?", " ?").split(" "), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def checklist_rows():
    rows = []
    fq, fa = font(40), font(46)
    x0, x1 = 50, W - 130  # marge droite pour les boutons TikTok
    for q, a, urgent in CHECKLIST:
        ql, al = wrap(q, fq, x1 - x0 - 150), wrap(a, fa, x1 - x0 - 150)
        h = 28 + len(ql) * 52 + 8 + len(al) * 58 + 28
        im = Image.new("RGBA", (x1 - x0, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, h - 1), 30, fill=DARK_T)
        col = RED if urgent else YELLOW
        d.ellipse((26, 28, 106, 108), fill=col)
        d.text((66, 68), "!" if urgent else "✓", font=font(56), fill=WHITE if urgent else DARK, anchor="mm")
        y = 28
        for line in ql:
            d.text((130, y), line, font=fq, fill=WHITE)
            y += 52
        y += 8
        for line in al:
            d.text((130, y), line, font=fa, fill=col)
            y += 58
        rows.append(im)
    return rows, x0


def chrono_frame(p):
    size = 440
    im = Image.new("RGBA", (size + 20, size + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = (10, 10, size + 10, size + 10)
    d.ellipse(box, fill=DARK_T)
    d.arc(box, 0, 360, fill=(255, 255, 255, 60), width=30)
    d.arc(box, -90 + 360 * p, 270, fill=RED, width=30)
    s = 1 + 0.06 * math.sin(p * math.pi * 8)
    f = font(round(130 * s))
    d.text((im.width / 2, im.height / 2), "24 H", font=f, fill=RED, anchor="mm")
    return im


def red_bar(progress):
    """Barre diagonale sur la boîte (image fixe 205947 @1,75 s : boîte x 158–245, y 504–677 source)."""
    (xa, ya), (xb, yb) = src_xy(140, 700), src_xy(262, 482)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    xe, ye = xa + (xb - xa) * progress, ya + (yb - ya) * progress
    d.line((xa, ya, xe, ye), fill=RED, width=56)
    return im


def build_overlay(path):
    hook1 = stack(label("FIÈVRE = LES DENTS ?", 58, WHITE, DARK_T), label("FAUX", 124, WHITE, RED, pad=40))
    hook2 = stack(label("PENSE", 76, DARK, YELLOW), label("PALUDISME", 116, WHITE, RED, pad=40))
    badge = label("PIÈGE N°3", 92, WHITE, RED, pad=38, radius=34)
    rows, rx = checklist_rows()
    chk_y = [1000]
    for r in rows[:-1]:
        chk_y.append(chk_y[-1] + r.height + 16)
    # la checklist remonte si elle dépasse la zone utile (au-dessus de 1440 px)
    over = chk_y[-1] + rows[-1].height - 1400
    chk_y = [y - max(0, over) for y in chk_y]

    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    n = round(TOTAL * FPS)
    for i in range(n):
        t = i / FPS
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # Accroche : « FAUX » qui éclate à 2,2 s, puis « PENSE PALUDISME » dès 2,25 s (< 3 s)
        s0 = at(0, 0)
        if t < s0 + 2.20:
            paste_center(L, hook1, W / 2, 1020, scale=pop(t, s0 + 0.05))
        elif t < s0 + 2.45:
            q = (t - s0 - 2.20) / 0.25
            paste_center(L, hook1, W / 2, 1020, scale=1 + 0.6 * q, alpha=1 - q)
        if at(0, 2.25) <= t < at(0, 4.85):
            paste_center(L, hook2, W / 2, 1020, scale=pop(t, at(0, 2.25)))
        # Badge PIÈGE N°3 : apparaît dans la paume, puis reste sous le visage
        if at(1, 0.35) <= t < at(1, 1.20):
            cx, cy = src_xy(130, 520)
            paste_center(L, badge, cx + 60, cy, scale=0.9 * pop(t, at(1, 0.35), 0.22), angle=6)
        elif at(1, 1.20) <= t < at(1, 3.75):
            paste_center(L, badge, W / 2, 1080)
        # Chrono 24 H (Piège 2), sur « en 24 heures, il peut devenir grave »
        c0, c1 = at(3, 5.40), at(3, 7.85)
        if c0 <= t < c1:
            paste_center(L, chrono_frame((t - c0) / (c1 - c0)), W / 2, 1000, scale=pop(t, c0))
        # Barre rouge plaquée sur la boîte au moment de l'impact
        b0 = at(4, 6.90)
        if b0 <= t < at(4, 7.70):
            L.alpha_composite(red_bar(min(1, (t - b0) / 0.10)))
        # Checklist : chaque ligne se révèle de gauche à droite sous la main
        for k, (r0, r1) in enumerate(CHECK_T):
            a0, a1 = at(6, r0), at(6, r1)
            if a0 <= t < at(6, 9.90):
                q = min(1, (t - a0) / (a1 - a0))
                row = rows[k]
                cut = row.crop((0, 0, max(1, round(row.width * q)), row.height))
                L.alpha_composite(cut, (rx, chk_y[k]))
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------------------------------
# Sous-titres (ASS) — en haut pendant la checklist pour ne pas la masquer
# ---------------------------------------------------------------------------------------
def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_ass(path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,2,80,140,420,1
Style: SubTop,DejaVu Sans,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,80,140,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for sec, a, b, txt in SUBS:
            style = "SubTop" if sec == 6 or (sec, a) == (4, 5.30) else "Sub"  # checklist / boîte en bas du cadre
            txt = txt.replace(" ?", "\\h?").replace(" :", "\\h:")
            f.write(f"Dialogue: 0,{ass_time(at(sec, a))},{ass_time(at(sec, b))},{style},,0,0,0,,{txt}\n")


# ---------------------------------------------------------------------------------------
# Audio : voix d'Abdou, morceaux mis bout à bout puis traitement « voix de narrateur »
# ---------------------------------------------------------------------------------------
# Réglages déduits de la comparaison avec la vidéo de référence (voix plus grave, plus de
# graves et d'aigus de présence, plus compressée) : EQ + excitateur + compression + hauteur
# abaissée de 2 demi-tons. Pas de clonage : c'est la voix d'Abdou, seulement traitée.
VOICE_FX = ",".join([
    "highpass=f=70",
    "afftdn=nf=-30",
    "rubberband=pitch=0.8909:formant=shifted",
    "bass=g=8:f=120:w=0.7",
    "equalizer=f=380:t=q:w=1.2:g=-3",
    "equalizer=f=3000:t=o:w=1.5:g=9",
    "treble=g=6:f=6000",
    "aexciter=amount=3:drive=8:freq=2500",
    "deesser",
    "acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=2",
])


def build_audio(path, voice_fx):
    parts = []
    for sec in SECTIONS:
        for sid, a, b in sec["audio"]:
            parts.append((sid, a, b))
    inputs, chains = [], []
    for k, (sid, a, b) in enumerate(parts):
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", rush(sid)]
        d = b - a
        chains.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=mono,afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{k}]")
    cat = "".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1"
    post = (voice_fx + "," if voice_fx else "") + "loudnorm=I=-14:TP=-1.5:LRA=9"
    fc = ";".join(chains) + ";" + cat + "," + post + "[out]"
    run([FF, "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2", path])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voix-brute", action="store_true", help="sans traitement de la voix")
    ap.add_argument("--sortie", default=None)
    a = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)

    pieces = [p for s in SECTIONS for p in s["video"]]
    for s in SECTIONS:
        va = sum(b - a for _, a, b in s["audio"])
        vv = sum((p[2] - p[1]) if not p[0].startswith("still_") else p[2] for p in s["video"])
        assert abs(va - vv) < 0.02, (s["nom"], va, vv)

    print(f"Durée avant accélération : {TOTAL:.2f} s → après ×{SPEED} : {TOTAL / SPEED:.2f} s")
    files = []
    for k, p in enumerate(pieces):
        if p[0].startswith("still_"):  # (id, instant, durée)
            files.append(render_piece(k, (p[0], p[1], p[2], p[3])))
        else:
            files.append(render_piece(k, p))
    lst = os.path.join(TMP, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in files)
    base = os.path.join(TMP, "base.mp4")
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    overlay = os.path.join(TMP, "overlay.mov")
    if not os.path.exists(overlay) or os.path.getmtime(overlay) < os.path.getmtime(__file__):
        print("Calque graphique…")
        build_overlay(overlay)
    ass = os.path.join(TMP, "subs.ass")
    write_ass(ass)
    audio = os.path.join(TMP, "voix_brute.wav" if a.voix_brute else "voix.wav")
    build_audio(audio, None if a.voix_brute else VOICE_FX)

    dst = a.sortie or os.path.join(OUT, "ep01_montage_v1_voix-brute.mp4" if a.voix_brute else "ep01_montage_v1.mp4")
    fc = (f"[0:v][1:v]overlay=0:0:format=auto,ass='{ass}',setpts=PTS/{SPEED},fps={FPS},format=yuv420p[v];"
          f"[2:a]atempo={SPEED}[a]")
    run([FF, "-y", "-i", base, "-i", overlay, "-i", audio, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", "-shortest", dst])
    print("Export :", dst)


if __name__ == "__main__":
    main()
