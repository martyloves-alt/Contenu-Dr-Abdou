"""Épisode 1 — exercice « magique » v5 : défi « arrête l'image », boucle continue (modèle : Saved-8093.mp4).

v5 = v4 + demande du 01/10 : la vidéo doit sembler tourner sans fin.
  - message « Écris gagné en commentaire » retiré ;
  - plus d'intro immobile ni de punch-in : le mouvement démarre dès la 1re image ;
  - vitesse en aller-retour 1,6× → 2,7× → 1,6× : en fin de fichier la vitesse rejoint celle du début ;
  - la dernière image précède directement l'alignement de l'image 0 : la boucle TikTok ne se voit pas
    à l'image (pas d'image en double, pas de saut de vitesse) ;
  - le doigt qui appuie sur la pause clignote du début à la fin.
Variante `--muet` : sans son choc ni voix ni sous-titres (seuls musique et bips), boucle totalement invisible.


v4 = v3 + plan d'optimisation du 01/10, points retenus après analyse :
  - sous-titres style TikTok (gros, blanc + jaune, contour et ombre noirs), toujours les mots d'Abdou ;
  - punch-in (zoom rapide 1,12 → 1) sur les 0,4 premières secondes ;
  - pictogramme « doigt qui appuie » clignotant sous l'icône pause (consigne visible sans le son) ;
  - contours façon sticker : bord blanc + trait rouge lissé et anti-crénelé + ombre douce ;
  - « Presque ! Recommence 😂 » sur l'image qui précède chaque alignement (piège pour qui met pause trop tôt) ;
  - bips de suspense à chaque déplacement (ils accélèrent avec le défi) à la place des tics ;
  - appel au commentaire écrit à partir de 11 s.
Non retenus : « 99 % des gens échouent » (statistique inventée) et le remplacement de la voix d'Abdou
par « fais un screenshot » (ce n'est pas ce qu'il dit).


v3 = v2 + son choc « Dark Horror » (~1 s) à l'ouverture, synthétisé (impact grave qui chute, frappe
métallique dissonante, réverbération). La voix démarre juste après le pic de l'impact (0,55 s) pour
qu'aucun mot ne soit masqué ; le reste (images, accélération, alignements) est identique à la v2.


Changements v2 (demande du 01/10) :
  - accélération progressive : le 1er cycle tourne à 1,6× (la v1 tournait à 1,8×), puis chaque cycle
    est plus rapide, jusqu'à 2,7× au dernier ; chaque cycle dure un nombre entier d'images, donc
    l'alignement des 4 objets tombe toujours exactement sur une image ;
  - la pose « TDR devant le visage » est remplacée par le TDR filmé seul, posé sur la table
    (rush 4K IMG_4558, tourné pour l'épisode 2), détouré.


Principe du modèle : 4 objets détourés, cerclés de rouge, en losange. Chaque objet est coupé en deux :
une moitié reste dans son contour, l'autre tourne d'un emplacement à l'autre en pivotant sur elle-même.
Le spectateur doit mettre en pause au moment où les 4 objets sont reconstitués.

Ici, les 4 « objets » sont 4 vraies poses d'Abdou tirées des rushes de l'épisode 1 (thermomètre, boîte de
paracétamol, TDR, doigts levés), détourées (rembg, modèle u2net_human_seg : on enlève le fond, on ne
génère rien). Voix : les 2 notes vocales d'Abdou du 01/10, accélérées ×1,2.

Le défi est réellement faisable : les 4 objets sont reconstitués sur une seule image par cycle de 2 s
(images listées dans out/defi_v4_alignements.json), jamais entre les deux.
Usage : python3 defi_v4.py → out/defi_v4.mp4
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
TMP = os.path.join(OUT, "tmp_defi_v5")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
YELLOW = (255, 214, 0)
EP2_DRIVE = os.path.join(EP1, "..", "ep02-palu-pas-ca-en-premier", "assets", "drive")
sys.path.insert(0, EP1)
import sfx  # noqa: E402  (habillage synthétisé de l'épisode 1)

import imageio_ffmpeg  # noqa: E402
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = os.path.join(EP1, "..", "ep02-palu-pas-ca-en-premier", "fonts", "Montserrat[wght].ttf")

W, H, FPS = 1080, 1920, 30
BG = (238, 247, 251)
OUTLINE = (225, 30, 35)
INTRO_F = 0           # pas d'intro immobile : le mouvement démarre tout de suite
MUET = "--muet" in sys.argv
# Durée de chaque cycle (4 déplacements) en images. Repère : la v1 = 60 images/cycle = « 1,8× ».
# Vitesse équivalente = 1,8 × 60 / N : 67 → 1,61× au début … 40 → 2,7× à la fin.
# aller-retour : 1,61× → 2,70× → 1,74×, puis la boucle repart à 1,61×
CYCLE_F = [67, 58, 50, 43, 40, 45, 53, 62]
TOTAL_F = INTRO_F + sum(CYCLE_F)  # la dernière image précède l'alignement de l'image 0 (boucle sans couture)
INTRO = INTRO_F / FPS
FIG_H = 480

# (fichier rush, instant, bas du buste dans l'image 480x852, découpe, moitié qui tourne)
OBJETS = [
    dict(nom="tdr_seul", src=os.path.join(EP2_DRIVE, "IMG_4558.mov"), t=0.7, coupe="h", mobile="haut", h=480),
    dict(nom="paracetamol", rush="lv_0_20260923205559.mp4", t=1.9, bas=560, coupe="h", mobile="haut"),
    dict(nom="doigts", rush="lv_0_20260923210140.mp4", t=1.5, bas=640, coupe="h", mobile="bas"),
    dict(nom="thermometre", rush="lv_0_20260923210033.mp4", t=1.8, bas=600, coupe="v", mobile="gauche"),
]
SLOTS = [(540, 610), (835, 1020), (540, 1480), (245, 1020)]  # haut, droite, bas, gauche (sens horaire)

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
    if "src" in o:  # objet filmé seul (4K) : détourage « objet »
        run([FF, "-y", "-ss", str(o["t"]), "-i", o["src"], "-frames:v", "1", "-vf", "scale=1620:-2:flags=lanczos", png])
        im = Image.open(png).convert("RGB")
        cut = remove(im, session=new_session("isnet-general-use"))
    else:  # pose d'Abdou (rush 480p) : détourage « personne »
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
    fh = o.get("h", FIG_H)
    s = fh / cut.height
    cut = cut.resize((round(cut.width * s), fh), Image.LANCZOS)
    cut.save(path)
    return cut


def outline(fig, gap=6, width=7):
    """Contour façon sticker, calculé en 2x puis réduit (anti-crénelé) : bord blanc, trait rouge, ombre douce."""
    pad = gap + width + 16
    a = np.array(fig.getchannel("A")).astype(np.float32) / 255
    a = np.pad(a, pad)
    big = np.array(Image.fromarray((a * 255).astype(np.uint8)).resize((a.shape[1] * 2, a.shape[0] * 2), Image.LANCZOS))
    m = ndimage.gaussian_filter((big > 110).astype(np.float32), 3) > 0.5  # silhouette lissée (pas d'escalier)
    d = ndimage.distance_transform_edt(~m)  # distance à la silhouette, en demi-pixels
    g, wd = 2 * gap, 2 * (gap + width)
    white = np.clip(g + 0.5 - d, 0, 1)
    red = np.clip(d - g + 0.5, 0, 1) * np.clip(wd + 0.5 - d, 0, 1)
    shadow = ndimage.gaussian_filter((d <= wd).astype(np.float32), 10)
    shadow = np.roll(np.roll(shadow, 10, 0), 6, 1) * 0.22
    rgba = np.zeros(m.shape + (4,), np.float32)
    for c in range(3):
        rgba[..., c] = (255 * white + OUTLINE[c] * red) / np.maximum(white + red, 1e-6)
    al = np.maximum(np.maximum(white, red), shadow * (1 - white - red))
    rgba[..., :3] = np.where((white + red)[..., None] > 0, rgba[..., :3], 0)
    rgba[..., 3] = al * 255
    im = Image.fromarray(rgba.astype(np.uint8), "RGBA").resize((a.shape[1], a.shape[0]), Image.LANCZOS)
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


def emoji_im(ch, h):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((round(h * im.width / im.height), h), Image.LANCZOS)


def tiktok_text(text, size=74, maxw=760, yellow=(), emoji=None, weight=900):
    """Texte en majuscules, blanc avec mots jaunes, contour noir épais et ombre portée ; emoji en fin."""
    f = font(size, weight)
    words = text.upper().split()
    sp = f.getbbox(" ")[2]
    lines, cur, cw = [], [], 0
    for wd in words:
        ww = f.getbbox(wd, stroke_width=8)[2]
        if cur and cw + sp + ww > maxw:
            lines.append(cur)
            cur, cw = [], 0
        cur.append(wd)
        cw += (sp if cw else 0) + ww
    lines.append(cur)
    lh = round(size * 1.18)
    em = emoji_im(emoji, round(size * 1.05)) if emoji else None
    im = Image.new("RGBA", (maxw + 120, lh * len(lines) + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d, ds = ImageDraw.Draw(im), ImageDraw.Draw(sh)
    for i, ln in enumerate(lines):
        widths = [f.getbbox(w_, stroke_width=8)[2] for w_ in ln]
        tot = sum(widths) + sp * (len(ln) - 1) + (em.width + sp if em is not None and i == len(lines) - 1 else 0)
        x, y = (im.width - tot) // 2, 16 + i * lh
        for w_, ww in zip(ln, widths):
            col = YELLOW if any(k in w_ for k in yellow) else (255, 255, 255)
            ds.text((x + 5, y + 7), w_, font=f, fill=(0, 0, 0, 200), stroke_width=8, stroke_fill=(0, 0, 0, 200))
            d.text((x, y), w_, font=f, fill=col, stroke_width=8, stroke_fill=(0, 0, 0))
            x += ww + sp
        if em is not None and i == len(lines) - 1:
            im.alpha_composite(em, (x, y + 4))
    out = sh.filter(ImageFilter.GaussianBlur(5))
    out.alpha_composite(im)
    return out.crop(out.getbbox())


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


def phase(f):
    """Nombre de déplacements effectués à l'image f (4 par cycle, cycles de plus en plus courts)."""
    if f < INTRO_F:
        return 0.0
    off = f - INTRO_F
    for c, n in enumerate(CYCLE_F):
        if off < n:
            return 4 * c + 4 * off / n
        off -= n
    return 4.0 * len(CYCLE_F)


def step_times():
    """Instants (s) où les moitiés passent sur un emplacement."""
    out, f0 = [], INTRO_F
    for n in CYCLE_F:
        out += [(f0 + n * j / 4) / FPS for j in range(4)]
        f0 += n
    return out + [f0 / FPS]


def mobile_state(i, f):
    """Position et angle de la moitié mobile de l'objet i à l'image f."""
    p = phase(f)
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
    hl = [("DÉFIS", "DIFFICILES"), ("ARRÊTER", "L'IMAGE")]  # (aucun sous-titre en variante muette)
    caps = [(s, e, tiktok_text(txt, size=68, maxw=960, yellow=y)) for (s, e, txt), y in zip(voice_spans, hl)]
    icon = stop_icon()
    finger = emoji_im("👆", 92)
    tap_from = 0.0
    almost = tiktok_text("Presque ! Recommence", size=70, maxw=820, yellow=("PRESQUE",), emoji="😂")
    almost_bg = Image.new("RGBA", (almost.width + 70, almost.height + 50), (0, 0, 0, 0))
    ImageDraw.Draw(almost_bg).rounded_rectangle((0, 0, almost_bg.width - 1, almost_bg.height - 1), 36,
                                                fill=(15, 27, 45, 215))
    almost_bg.alpha_composite(almost, (35, 25))
    al = set(aligned_frames())
    traps = {(f - 1) % TOTAL_F for f in al}  # image juste avant chaque alignement (y compris celui de la boucle)
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
        _safe(L, icon, 850, 400)  # pause : dans le vide à droite du TDR
        if t >= tap_from and (t - tap_from) % 0.5 < 0.32:  # doigt qui appuie sur la pause, clignotant
            dy = 10 * math.sin(2 * math.pi * (t - tap_from) / 0.5)
            _safe(L, finger, 905 - finger.width / 2, 525 + dy)
        for s, e, im in caps:
            if s <= t < e:
                _safe(L, im, 540 - im.width / 2, 225 - im.height / 2)
        if f in traps:
            _safe(L, almost_bg, (W - almost_bg.width) / 2, SLOTS[1][1] - almost_bg.height / 2)
        p.stdin.write(L.convert("RGB").tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------------------------------
# Son
# ---------------------------------------------------------------------------------------
def horror_hit(d=1.1):
    """Son choc « Dark Horror » : impact grave en chute + frappe métallique dissonante + réverbération."""
    SR = sfx.SR
    t = np.arange(int(d * SR)) / SR
    rng = np.random.default_rng(13)
    f = 32 + 78 * np.exp(-t / 0.12)  # boum : 110 Hz → 32 Hz
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    crack = sfx._lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.025)
    metal = sum(a * np.sin(2 * np.pi * fr * t + ph) * np.exp(-t / tau)  # partiels inharmoniques
                for fr, a, tau, ph in [(233, .5, .55, 0), (247, .45, .5, 1), (349, .35, .4, 2),
                                       (523, .25, .3, .5), (741, .2, .25, 1.5), (1109, .12, .18, 2.5)])
    stab = sum(np.sign(np.sin(2 * np.pi * fr * t)) for fr in (55, 58.3, 77.8))  # cluster grave dissonant
    stab = sfx._lp(stab, 600) * np.exp(-t / 0.4) * 0.25
    dry = 1.0 * boom + 0.6 * crack + 0.35 * metal + stab
    ir_t = np.arange(int(0.9 * SR)) / SR
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.25)
    wet = np.convolve(dry, ir)[: len(t)]
    out = dry + 0.35 * wet / (np.abs(wet).max() + 1e-9) * np.abs(dry).max()
    out *= np.minimum(1, (d - t) / 0.25)  # fondu de fin
    return out / np.abs(out).max()


def beep(freq=1650, d=0.07):
    """Bip de compte à rebours (sinus + harmonique, attaque et relâche douces)."""
    t = np.arange(int(d * sfx.SR)) / sfx.SR
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t)
    env = np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.015)
    return x * env


def marimba(freq, d=0.45):
    t = np.arange(int(d * sfx.SR)) / sfx.SR
    x = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 4 * freq * t) * np.exp(-t / 0.03)
    return x * np.exp(-t / 0.18) * (1 - np.exp(-t / 0.003))


def build_audio(voice_path, music_path, fx_path, starts):
    total = TOTAL_F / FPS
    # voix : chaque note nettoyée, accélérée ×1,2, posée à son instant
    parts = []
    for (fn, a, b, _), s in zip(NOTES if not MUET else [], starts):
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
    st = step_times()
    beats = []  # pas de marimba pendant le son choc : la musique démarre avec le mouvement
    for a, b in zip(st, st[1:]):  # puis une note par demi-déplacement : la musique accélère avec le défi
        beats += [a, (a + b) / 2]
    for k, t in enumerate(beats):
        sfx._place(mus, marimba(notes[k % len(notes)]), t, 0.22 if k % 2 == 0 else 0.15)
        sfx._place(mus, marimba(notes[k % len(notes)] / 4, 0.4), t, 0.18 if k % 4 == 0 else 0.0)
    fx = np.zeros(int(total * sfx.SR))
    if not MUET:
        sfx._place(fx, horror_hit(), 0.0, 0.95)  # son choc d'ouverture
    for t in step_times()[:-1]:  # bip à chaque passage, y compris à 0 s (rythme régulier au raccord de boucle) ; tic à chaque passage d'emplacement (pas de son spécial à l'alignement : défi intact)
        sfx._place(fx, beep(), t, 0.20)
    for x, pth in ((mus, music_path), (fx, fx_path)):
        wavfile.write(pth, sfx.SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    figs = [cutout(o) for o in OBJETS]
    # minutage voix (après ×1,2)
    # sous-titre calé sur le premier mot réellement entendu (transcription de l'export : 0,0 s et 3,3 s)
    delays = [0.0, 0.80]
    starts, spans, t = [], [], 0.55  # après le pic du son choc
    for (fn, a, b, txt), dl in zip(NOTES, delays):
        d = (b - a) / 1.2
        starts.append(t)
        spans.append([t + dl, t + d + 0.25, txt])
        t += d + 0.10
    for k in range(len(spans) - 1):
        spans[k][1] = min(spans[k][1], spans[k + 1][0])
    al = aligned_frames()
    json.dump(dict(fps=FPS, images_alignees=al, secondes=[round(x / FPS, 3) for x in al]),
              open(os.path.join(OUT, "defi_v5_alignements.json"), "w"), indent=1)
    print("Images où les 4 objets sont entiers :", al)
    vid = os.path.join(TMP, "video.mp4")
    render_video(vid, figs, [] if MUET else spans)
    voice, mus, fxp = (os.path.join(TMP, n) for n in ("voix.wav", "music.wav", "fx.wav"))
    build_audio(voice, mus, fxp, starts)
    dst = os.path.join(OUT, "defi_v5_muet.mp4" if MUET else "defi_v5.mp4")
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
