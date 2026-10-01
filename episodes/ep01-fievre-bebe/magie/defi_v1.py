"""Épisode 1 — exercice « magique » v1 : défi « arrête l'image » (modèle : Saved-8093.mp4).

Principe du modèle : 4 objets détourés, cerclés de rouge, en losange. Chaque objet est coupé en deux :
une moitié reste dans son contour, l'autre tourne d'un emplacement à l'autre en pivotant sur elle-même.
Le spectateur doit mettre en pause au moment où les 4 objets sont reconstitués.

Ici, les 4 « objets » sont 4 vraies poses d'Abdou tirées des rushes de l'épisode 1 (thermomètre, boîte de
paracétamol, TDR, doigts levés), détourées (rembg, modèle u2net_human_seg : on enlève le fond, on ne
génère rien). Voix : les 2 notes vocales d'Abdou du 01/10, accélérées ×1,2.

Le défi est réellement faisable : les 4 objets sont reconstitués sur une seule image par cycle de 2 s
(images listées dans out/defi_v1_alignements.json), jamais entre les deux.
Usage : python3 defi_v1.py → out/defi_v1.mp4
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
EP1 = os.path.dirname(HERE)
RUSHES = os.path.join(EP1, "assets", "rushes")
VOIX = os.path.join(EP1, "assets", "voix")
OUT = os.path.join(EP1, "out")
TMP = os.path.join(OUT, "tmp_defi_v1")
sys.path.insert(0, EP1)
import sfx  # noqa: E402  (habillage synthétisé de l'épisode 1)

import imageio_ffmpeg  # noqa: E402
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = os.path.join(EP1, "..", "ep02-palu-pas-ca-en-premier", "fonts", "Montserrat[wght].ttf")

W, H, FPS = 1080, 1920, 30
BG = (238, 247, 251)
OUTLINE = (225, 30, 35)
INTRO = 1.0           # objets entiers et immobiles au début
STEP = 0.5            # durée d'un déplacement d'un emplacement au suivant (15 images)
CYCLES = 6            # 4 pas = 1 cycle = 2 s ; fin exactement sur un alignement (boucle TikTok propre)
TOTAL_F = round((INTRO + CYCLES * 4 * STEP) * FPS) + 1
FIG_H = 480

# (fichier rush, instant, bas du buste dans l'image 480x852, découpe, moitié qui tourne)
OBJETS = [
    dict(nom="tdr", rush="lv_0_20260923210750.mp4", t=5.0, bas=600, coupe="h", mobile="haut"),
    dict(nom="paracetamol", rush="lv_0_20260923205559.mp4", t=1.9, bas=560, coupe="h", mobile="haut"),
    dict(nom="doigts", rush="lv_0_20260923210140.mp4", t=1.5, bas=640, coupe="h", mobile="bas"),
    dict(nom="thermometre", rush="lv_0_20260923210033.mp4", t=1.8, bas=600, coupe="v", mobile="gauche"),
]
SLOTS = [(540, 560), (835, 1020), (540, 1480), (245, 1020)]  # haut, droite, bas, gauche (sens horaire)

VOICE_FX = ",".join(["highpass=f=80", "afftdn=nf=-30", "equalizer=f=380:t=q:w=1.2:g=-2",
                     "equalizer=f=3000:t=o:w=1.5:g=5", "treble=g=3:f=6000", "deesser",
                     "acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=2"])
NOTES = [  # (fichier, début, fin dans la note) — mots exacts vérifiés par transcription
    ("defi_n1.opus", 1.00, 3.70, "L'un des défis les plus difficiles au monde."),
    ("defi_n2.opus", 0.00, 3.55, "Je vous mets au défi d'arrêter l'image."),
]
UPLOADS = os.path.join(EP1, "assets", "magie")  # notes du 01/10 (WA0021, WA0022) + vidéo modèle


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit(r.stderr[-3000:])


# ---------------------------------------------------------------------------------------
# Détourage
# ---------------------------------------------------------------------------------------
def cutout(o):
    path = os.path.join(TMP, f"cut_{o['nom']}.png")
    if os.path.exists(path):
        return Image.open(path)
    from rembg import new_session, remove
    png = os.path.join(TMP, f"src_{o['nom']}.png")
    run([FF, "-y", "-ss", str(o["t"]), "-i", os.path.join(RUSHES, o["rush"]), "-frames:v", "1",
         "-vf", "scale=960:1704:flags=lanczos", png])
    im = Image.open(png).convert("RGB").crop((0, 0, 960, o["bas"] * 2))  # bas du buste (logo CapCut exclu)
    cut = remove(im, session=new_session("u2net_human_seg"))
    a = np.array(cut.getchannel("A"))
    lab, n = ndimage.label(a > 128)  # on garde les morceaux significatifs (pas les îlots du fond)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
        keep = np.isin(lab, 1 + np.flatnonzero(sizes > 0.02 * sizes.max()))
        a = np.where(ndimage.binary_dilation(keep, iterations=3), a, 0)
    a = np.where(a < 90, 0, a)  # pas de « fantômes » semi-transparents (bras coupé par le bord du rush)
    cut.putalpha(Image.fromarray(a.astype(np.uint8)))
    cut = cut.crop(cut.getbbox())
    s = FIG_H / cut.height
    cut = cut.resize((round(cut.width * s), FIG_H), Image.LANCZOS)
    cut.save(path)
    return cut


def outline(fig, gap=5, width=6):
    m = np.array(fig.getchannel("A")) > 110
    pad = gap + width + 4
    m = np.pad(m, pad)
    outer = ndimage.binary_dilation(m, iterations=gap + width)
    inner = ndimage.binary_dilation(m, iterations=gap)
    ring = (outer & ~inner).astype(np.uint8) * 255
    im = Image.new("RGBA", ring.shape[::-1], OUTLINE + (0,))
    im.putalpha(Image.fromarray(ring).filter(ImageFilter.GaussianBlur(0.8)))
    return im, pad


def halves(fig, o):
    """(moitié fixe, moitié mobile) : images de la taille de la figure, l'autre moitié transparente."""
    a = np.array(fig.getchannel("A"))
    ys, xs = np.nonzero(a > 110)
    keep = np.zeros_like(a, dtype=bool)
    if o["coupe"] == "h":
        cut = int(np.median(ys))  # coupe à mi-hauteur de la silhouette
        keep[:cut] = True
    else:
        cut = int(np.median(xs))
        keep[:, :cut] = True
    first = o["mobile"] in ("haut", "gauche")
    mob_mask, fix_mask = (keep, ~keep) if first else (~keep, keep)
    out = []
    for m in (fix_mask, mob_mask):
        h = fig.copy()
        h.putalpha(Image.fromarray(np.where(m, a, 0).astype(np.uint8)))
        out.append(h)
    return out


# ---------------------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------------------
def font(size, weight=800):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight])
    return f


def caption(text, size=56, maxw=700):
    f = font(size)
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if f.getbbox(t)[2] > maxw and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    lh = round(size * 1.2)
    im = Image.new("RGBA", (maxw + 40, lh * len(lines) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = f.getbbox(l)[2]
        d.text(((im.width - lw) // 2, 10 + i * lh), l, font=f, fill=(15, 27, 45), stroke_width=5,
               stroke_fill=(255, 255, 255))
    return im


def stop_icon(size=110):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, size - 4, size - 4), fill=OUTLINE)
    bw, bh = size * 0.13, size * 0.42
    for cx in (size * 0.38, size * 0.62):
        d.rounded_rectangle((cx - bw / 2, (size - bh) / 2, cx + bw / 2, (size + bh) / 2), 4, fill=(255, 255, 255))
    return im


def center_paste(L, im, cx, cy, angle=0.0, pivot=None):
    """Colle `im` centré en (cx, cy) ; rotation autour de `pivot` (coordonnées dans im), par défaut son centre."""
    if angle:
        pv = pivot or (im.width / 2, im.height / 2)
        big = max(im.size) * 2
        canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        ox, oy = round(big / 2 - pv[0]), round(big / 2 - pv[1])
        canvas.alpha_composite(im, (ox, oy))
        rot = canvas.rotate(-angle, resample=Image.BICUBIC, center=(big / 2, big / 2))
        # le pivot reste au centre du canvas
        tx = cx - (im.width / 2 - pv[0]) - big / 2
        ty = cy - (im.height / 2 - pv[1]) - big / 2
        _safe(L, rot, tx, ty)
    else:
        _safe(L, im, cx - im.width / 2, cy - im.height / 2)


def _safe(L, im, x, y):
    x, y = round(x), round(y)
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, W - x), min(im.height, H - y)
    if r > l and b > t:
        L.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))


def mobile_state(i, f):
    """Position et angle de la moitié mobile de l'objet i à l'image f."""
    t = f / FPS
    if t < INTRO:
        return SLOTS[i], 0.0
    p = (t - INTRO) / STEP
    k = math.floor(p + 1e-9)
    fr = p - k
    a, b = SLOTS[(i + k) % 4], SLOTS[(i + k + 1) % 4]
    pos = (a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr)
    return pos, 360.0 * fr  # un tour complet par déplacement : droite à chaque emplacement


def aligned_frames():
    out = []
    for f in range(TOTAL_F):
        if all(mobile_state(i, f)[0] == SLOTS[i] and mobile_state(i, f)[1] % 360 == 0 for i in range(4)):
            out.append(f)
    return out


def render_video(path, figs, voice_spans):
    rings = [outline(fg) for fg in figs]
    hv = [halves(fg, o) for fg, o in zip(figs, OBJETS)]
    caps = [(s, e, caption(txt)) for s, e, txt in voice_spans]
    icon = stop_icon()
    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(TOTAL_F):
        t = f / FPS
        L = Image.new("RGBA", (W, H), BG + (255,))
        for i, (ring, pad) in enumerate(rings):  # contours fixes
            center_paste(L, ring, *SLOTS[i])
        for i in range(4):  # moitiés fixes
            center_paste(L, hv[i][0], *SLOTS[i])
        for i in range(4):  # moitiés mobiles (pivotent sur leur propre centre de masse)
            (cx, cy), ang = mobile_state(i, f)
            mob = hv[i][1]
            ys, xs = np.nonzero(np.array(mob.getchannel("A")) > 110)
            center_paste(L, mob, cx, cy, angle=ang, pivot=(xs.mean(), ys.mean()))
        _safe(L, icon, 905, 175)
        for s, e, im in caps:
            if s <= t < e:
                _safe(L, im, 450 - im.width / 2, 175)
        p.stdin.write(L.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------------------------------
# Son
# ---------------------------------------------------------------------------------------
def marimba(freq, d=0.45):
    t = np.arange(int(d * sfx.SR)) / sfx.SR
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 4 * freq * t) * np.exp(-t / 0.03)
    return x * np.exp(-t / 0.18) * (1 - np.exp(-t / 0.003))


def build_audio(voice_path, music_path, fx_path, starts):
    total = TOTAL_F / FPS
    # voix : chaque note nettoyée, accélérée ×1,2, posée à son instant
    parts = []
    for (fn, a, b, _), s in zip(NOTES, starts):
        o = os.path.join(TMP, f"note_{s:.2f}.wav")
        run([FF, "-y", "-ss", str(a), "-to", str(b), "-i", os.path.join(UPLOADS, fn), "-af",
             f"aresample=48000,{VOICE_FX},atempo=1.2,loudnorm=I=-18:TP=-2", "-ac", "1", "-ar", "48000", o])
        parts.append((o, s))
    vo = np.zeros(int(total * sfx.SR))
    for o, s in parts:
        sr, x = wavfile.read(o)
        sfx._place(vo, x.astype(np.float64) / 32768, s)
    wavfile.write(voice_path, sfx.SR, (np.clip(vo, -1, 1) * 32767).astype(np.int16))
    # musique : marimba à 120 bpm, une note par demi-temps, calée sur les déplacements (pentatonique majeure)
    mus = np.zeros(int(total * sfx.SR))
    notes = [523.3, 659.3, 784.0, 659.3, 587.3, 784.0, 880.0, 784.0]
    k, t = 0, 0.0
    while t < total:
        sfx._place(mus, marimba(notes[k % len(notes)]), t, 0.22 if k % 2 == 0 else 0.15)
        sfx._place(mus, marimba(notes[k % len(notes)] / 4, 0.4), t, 0.18 if k % 4 == 0 else 0.0)
        t += STEP / 2
        k += 1
    fx = np.zeros(int(total * sfx.SR))
    sfx._place(fx, sfx.whoosh(0.5), INTRO - 0.35, 0.35)
    t = INTRO + STEP
    while t < total:  # tic à chaque passage d'emplacement (pas de son spécial à l'alignement : défi intact)
        sfx._place(fx, sfx.tick(2400), t, 0.25)
        t += STEP
    for x, pth in ((mus, music_path), (fx, fx_path)):
        wavfile.write(pth, sfx.SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    figs = [cutout(o) for o in OBJETS]
    # minutage voix (après ×1,2)
    # sous-titre calé sur le premier mot réellement entendu (transcription de l'export : 0,0 s et 3,3 s)
    delays = [0.0, 0.80]
    starts, spans, t = [], [], 0.15
    for (fn, a, b, txt), dl in zip(NOTES, delays):
        d = (b - a) / 1.2
        starts.append(t)
        spans.append([t + dl, t + d + 0.25, txt])
        t += d + 0.10
    for k in range(len(spans) - 1):
        spans[k][1] = min(spans[k][1], spans[k + 1][0])
    al = aligned_frames()
    json.dump(dict(fps=FPS, images_alignees=al, secondes=[round(x / FPS, 3) for x in al]),
              open(os.path.join(OUT, "defi_v1_alignements.json"), "w"), indent=1)
    print("Images où les 4 objets sont entiers :", al)
    vid = os.path.join(TMP, "video.mp4")
    render_video(vid, figs, spans)
    voice, mus, fxp = (os.path.join(TMP, n) for n in ("voix.wav", "music.wav", "fx.wav"))
    build_audio(voice, mus, fxp, starts)
    dst = os.path.join(OUT, "defi_v1.mp4")
    fc = ("[1:a]asplit=2[vo][key];[2:a][3:a]amix=inputs=2:normalize=0[bed];"
          "[bed][key]sidechaincompress=threshold=0.02:ratio=6:attack=5:release=250[m];"
          "[vo][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
          "aformat=channel_layouts=stereo[a]")
    run([FF, "-y", "-i", vid, "-i", voice, "-i", mus, "-i", fxp, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", dst])
    # 2e passe : niveau intégré ramené exactement à −14 LUFS (le loudnorm en une passe tombe à ~−15)
    r = subprocess.run([FF, "-i", dst, "-af", "ebur128", "-f", "null", "-"], stderr=subprocess.PIPE, text=True).stderr
    lufs = float(r.rsplit("I:", 1)[1].split("LUFS")[0])
    fixed = dst.replace(".mp4", "_n.mp4")
    run([FF, "-y", "-i", dst, "-c:v", "copy", "-af", f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=0", "-c:a", "aac",
         "-b:a", "192k", "-movflags", "+faststart", fixed])
    os.replace(fixed, dst)
    print("Export :", dst, f"({TOTAL_F / FPS:.2f} s, {lufs:.1f} → −14 LUFS)")


if __name__ == "__main__":
    main()
