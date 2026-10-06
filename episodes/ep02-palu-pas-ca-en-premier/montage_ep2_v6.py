"""Épisode 2 — montage v6 = la v4 (validée telle quelle le 06/10) + 3 changements demandés :
  1. cadence forcée AVANT le zoom : l'image accélère exactement comme la voix (bug de la v4 : le filtre de
     zoom rendait une image par image source, visages et manipulations tournaient à ×1 sous une voix à ×1,5) ;
  2. pastilles 1, 2, 3 de la v5 (avec un « pop » 0,12 s avant chaque chiffre) ;
  3. appel au commentaire : nouvelle note d'Abdou (WA0023, « …le sirop que tu caches toujours au frigo… je te
     dirai si c'est dangereux ») sur la vidéo de la v4 (WA0034), avec un éclair de la boîte de Bimalaril sur
     « sirop » et, sur « je te dirai si c'est dangereux », la caméra qui suit la main d'Abdou vers le bas (IMG_4569).
Tout le reste est identique à la v4. Ancienne description de la v4 :

Épisode 2 — nouveau style « process » (V1 du 06/10, modèle : Video_1859758211849536.mp4).

Modèle : une manipulation filmée étape par étape, accélérée, enchaînée en fondus, avec un plan final
« récompense » en léger zoom. Ici : le vrai TDR fait par Abdou (rushes 4K IMG_45xx, mains gantées),
pendant qu'il parle.
  - Voix : les mêmes prises que les montages précédents (texte validé), accélérées ×1,5 ; le bloc des
    signes d'urgence seulement ×1,3 (à ×1,5 « dort trop » devient inintelligible à la transcription).
  - Image : visage plein écran quand Abdou s'adresse au parent (accroche, réflexes, résultats, urgences,
    appel au commentaire) ; manipulations plein écran avec son visage en vignette pendant qu'il parle
    (piège, TDR) ; manipulations seules pendant la lecture du test (note vocale, pas d'image de lui).
  - Manipulations accélérées ×1,7, fondus enchaînés de 0,2 s, zoom lent sur chaque plan, ralenti ×0,5
    (images interpolées) sur la goutte de tampon.
  - Sous-titres français + anglais (traduction fidèle, à valider par Abdou).
  - Piano doux synthétisé (aucune musique sous droits).
Usage : python3 montage_ep2_v6.py → out/ep02_montage_v6.mp4
"""
import json
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile

import montage_ep2 as v1
import montage_ep2_v2 as v2
import montage_ep2_v3 as v3
from montage_ep2 import FF, FPS, W, H, run, sfx
from montage_ep2_v2 import TAIL, src, kept
import montage_ep2_v5 as v5

OUT = v1.OUT
TMP = os.path.join(OUT, "tmp_v6")
GRADE = ("eq=contrast=1.06:brightness=0.01:saturation=1.08,"
         "colorbalance=rs=0.03:gs=0.01:bs=-0.02:rm=0.02:bm=-0.02,unsharp=5:5:0.4")
# parties de la v4, sauf l'appel au commentaire remplacé par la note WA0023 (même découpage qu'en v5 :
# la pause de 1,4 s avant « Dis-le-moi », sans aucun mot, est retirée)
PARTS = v2.PARTS[:-1] + [dict(id="cta", audio=("n6", 0.80, 7.85)), dict(id="cta2", audio=("n6", 9.15, 12.50))]
PID = {p["id"]: i for i, p in enumerate(PARTS)}


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
        cands = [x for x in self.pieces if x[0] == PID[pid]]
        for _, _, a, b, t0 in cands:
            if raw <= b:
                return t0 + max(0.0, raw - a)
        _, _, a, b, t0 = cands[-1]
        return t0 + b - a


SPEED = {p["id"]: 1.5 for p in PARTS}
SPEED.update(urg_a=1.3, urg_mois=1.3, urg_b=1.3)
PROC = 1.7          # accélération des manipulations
XF = 6              # fondu enchaîné entre deux manipulations (images)

# ---------------------------------------------------------------------------------------
# Temps : montage brut (TL) → vidéo finale (vitesse par partie)
# ---------------------------------------------------------------------------------------
TLINE = TL()
_BOUNDS = [(a, b, SPEED[p["id"]]) for p, (a, b) in zip(PARTS, TLINE.rng)] + [(TLINE.voice_end, TLINE.total, 1.5)]


def M(t):
    """Instant final (s) d'un instant t du montage brut."""
    acc = 0.0
    for a, b, s in _BOUNDS:
        if t <= b + 1e-9:
            return acc + max(0.0, t - a) / s
        acc += (b - a) / s
    return acc


def Fr(t):
    return round(M(t) * FPS)


TOTAL_F = Fr(TLINE.total)
CTA0 = TLINE.rng[PID["cta"]][0]                 # début de l'appel au commentaire (montage brut)
SIROP = TLINE.at("cta", 3.95)                   # « sirop »
DIRAI = TLINE.at("cta2", 10.38)                 # « je te dirai si c'est dangereux »

# Plans (instants du montage brut). FULL = visage plein écran ; PIP = manipulations + vignette visage.
PIP = [(4.33, 9.80), (22.27, 26.77)]
PROCESS = [  # (début, fin, réglages) — manipulations plein écran, dans l'ordre réel du test
    (4.33, 6.10, dict(clip="IMG_4541", a=0.0)),                      # boîte de TDR
    (6.10, 7.10, dict(clip="IMG_4559", a=0.2, blur=True)),           # « antipaludéen » (marque floutée)
    (7.10, 8.40, dict(clip="IMG_4543", a=0.0)),                      # « sans faire le test » : le plateau
    (8.40, 9.80, dict(clip="IMG_4550", a=10.5)),                     # ouverture du sachet
    (22.27, 22.85, dict(clip="IMG_4551", a=0.0)),                    # test posé
    (22.85, 24.00, dict(clip="WA0026", a=29.10)),                    # piqûre au bout du doigt (vidéo du 06/10)
    (24.00, 24.60, dict(clip="IMG_4553", a=0.0)),                    # sang
    (24.60, 26.77, dict(clip="IMG_4555", a=3.55, slow=0.5)),         # goutte de tampon, ralenti
    (26.77, 27.90, dict(clip="IMG_4556", a=1.0)),                    # migration
    (27.90, 31.70, dict(clip="IMG_4558", a=0.0, hold=True)),         # résultat filmé : 1 trait
    (31.70, 35.53, dict(photo=True)),                                # photo : 2 traits (autre test)
    (46.70, 48.73, dict(card=True)),                                 # « à moins de 3 mois » (note vocale)
]
FULL_FACE_PARTS = {"hook", "piege", "reflexes", "tdr", "resultat", "urg_a", "urg_b", "cta"}

# Sous-titres : (début dans le montage brut, français = mots d'Abdou, anglais = traduction fidèle)
SUBS = [
    (0.00, "Tu soupçonnes le palu chez ton enfant ?", "Do you suspect malaria in your child?"),
    (2.12, "Ne fais SURTOUT PAS ça en premier !", "Whatever you do, DON'T do this first!"),
    (4.40, "L'erreur classique :", "The classic mistake:"),
    (5.42, "lui donner un antipaludéen sans faire le test.", "giving an antimalarial without testing."),
    (8.40, "Si c'est une autre maladie,", "If it's another illness,"),
    (9.80, "tu perds un temps précieux.", "you're losing precious time."),
    (11.70, "Trois bons réflexes.", "Three good reflexes."),
    (12.86, "Un : note l'heure du début de la fièvre.", "One: note when the fever started."),
    (15.38, "Deux : fais-le boire, ou allaite-le.", "Two: give fluids, or breastfeed."),
    (18.18, "Trois : paracétamol pour son confort,", "Three: paracetamol for comfort,"),
    (20.80, "et à la bonne dose.", "at the right dose."),
    (22.30, "Puis, allez au centre de santé le plus proche", "Then go to the nearest health centre"),
    (24.50, "dans les 24 heures pour le TDR.", "within 24 hours for a rapid test (RDT)."),
    (26.76, "Là où vous voyez un point,", "Where you see one dot,"),
    (30.00, "c'est que le test est négatif.", "the test is negative."),
    (31.70, "Et là où vous voyez deux points,", "And where you see two dots,"),
    (33.42, "c'est que le test est positif.", "the test is positive."),
    (35.50, "Si TDR positif : traitement complet, jusqu'au bout.", "Positive test: full treatment, right to the end."),
    (38.94, "Si TDR négatif : cherchez une autre cause.", "Negative test: look for another cause."),
    (42.36, "Mais s'il convulse, ne tète plus,", "But if the child has seizures, won't breastfeed,"),
    (44.86, "vomit tout, dort trop,", "vomits everything, sleeps too much,"),
    (46.75, "a moins de 3 mois,", "or is under 3 months old,"),  # « s'il … a moins de 3 mois » (verbe avoir)
    (48.64, "allez aux urgences tout de suite.", "go to the emergency room right away."),
]

SUBS += [  # appel au commentaire : note WA0023 (mots d'Abdou) + traduction
    (TLINE.at("cta", 0.94), "Et toi, sois honnête : c'est quoi le sirop", "And you, be honest: what's the syrup"),
    (TLINE.at("cta", 4.52), "que tu caches toujours au frigo « au cas où » ?", "you always hide in the fridge \"just in case\"?"),
    (TLINE.at("cta2", 9.20), "Dis-le-moi en commentaire,", "Tell me in the comments,"),
    (DIRAI, "je te dirai si c'est dangereux.", "I'll tell you if it's dangerous."),
]
# éclair de la boîte de Bimalaril (un sirop, marque floutée) sur « sirop » : 0,4 s
PROCESS.append((SIROP, SIROP + 0.4 * SPEED["cta"], dict(clip="IMG_4559", a=0.3, blur=True)))
BADGES = [(12.86, "1"), (15.38, "2"), (18.18, "3")]  # instants du montage brut (identiques à la v4)
REFL_END = 22.20

BUBBLE = (50, 230, 380, 476)  # x, y, largeur, hauteur de la vignette visage


# ---------------------------------------------------------------------------------------
# Piste visage (plein écran, synchronisée sur la voix)
# ---------------------------------------------------------------------------------------
def render_face(k, clip, a, n, speed, zoom):
    out = os.path.join(TMP, f"f{k:03d}.mp4")
    cw, ch, cx, cy = v3.face_crop(clip, zoom)
    vf = (f"setpts=PTS/{speed:.4f},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,crop={cw}:{ch}:{cx}:{cy},{GRADE},"
          f"scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,"
          f"zoompan=z='1+0.03*on/{max(1, n - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
          f"format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-t", f"{n / FPS * speed + 0.4:.3f}", "-i", src(clip), "-vf", vf,
         "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


def black(k, n, tag="b"):
    out = os.path.join(TMP, f"{tag}{k:03d}.mp4")
    run([FF, "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}", "-frames:v", str(n),
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
    return out


def concat(files, out):
    lst = out + ".txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in files)
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    return out


def face_track():
    files, f, z = [], 0, 0
    for k, (pi, clip, a, b, t0) in enumerate(TLINE.pieces):
        p = PARTS[pi]
        if p["id"] in ("cta", "cta2"):
            continue  # traité après la boucle
        f0, f1 = Fr(t0), Fr(t0 + b - a)
        if f0 > f:
            files.append(black(len(files), f0 - f))
        if f1 - f0 < 1:
            continue
        if p["id"] in FULL_FACE_PARTS and p.get("video") is None:
            if f1 - f0 >= 10:
                z += 1
            files.append(render_face(len(files), clip, a, f1 - f0, SPEED[p["id"]], 1.06 if z % 2 else 1.18))
        else:
            files.append(black(len(files), f1 - f0))
        f = f1
    # appel au commentaire : la vidéo de la v4 (WA0034, depuis 0 s, ×1,5) jusqu'à « je te dirai… »
    c0, c1 = Fr(CTA0), Fr(DIRAI)
    if c0 > f:
        files.append(black(len(files), c0 - f))
    files.append(render_face(len(files), "WA0034", 0.0, c1 - c0, SPEED["cta"], 1.06))
    # « je te dirai si c'est dangereux » + fin : la caméra suit la main d'Abdou vers le bas
    files.append(render_follow(len(files), TOTAL_F - c1))
    return concat(files, os.path.join(TMP, "face.mp4"))


def render_follow(k, n):
    """IMG_4569 : Abdou pointe vers le bas ; zoom progressif qui suit la main (à gauche de l'image) vers le bas."""
    out = os.path.join(TMP, f"f{k:03d}.mp4")
    a0, src_len = TAIL[1], 1.62
    sp = src_len / (n / FPS)
    P = f"(on/{max(1, n - 1)})"
    E = f"({P}*{P}*(3-2*{P}))"                      # départ et arrivée en douceur
    z = f"1+0.65*{E}"
    cx = f"(540-300*{E})*1.5"                       # du visage (x 540) vers la main (x ≈ 240)
    cy = f"(760+420*{E})*1.5"                       # et vers le bas (y 760 → 1180)
    vf = (f"setpts=PTS/{sp:.4f},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,{GRADE},"
          f"tpad=stop_mode=clone:stop_duration={n / FPS:.3f},scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,"
          f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{cx}-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{cy}-ih/zoom/2))'"
          f":d=1:s={W}x{H}:fps={FPS},format=yuv420p")
    run([FF, "-y", "-ss", f"{a0:.3f}", "-t", f"{src_len + 0.2:.3f}", "-i", src(TAIL[0]), "-vf", vf,
         "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


# ---------------------------------------------------------------------------------------
# Piste manipulations (plein écran, fondus enchaînés)
# ---------------------------------------------------------------------------------------
def render_proc(k, n, ext, spec):
    """n images utiles + ext images de recouvrement pour le fondu suivant."""
    out = os.path.join(TMP, f"p{k:03d}.mp4")
    tot = n + ext
    if spec.get("photo"):
        return v1.encode(v3.photo_frames(tot)[0], out, H)
    if spec.get("card"):
        return v1.encode(v3.carton_frames(tot), out, H)
    clip, a = spec["clip"], spec["a"]
    info = subprocess.run([FF, "-i", src(clip)], stderr=subprocess.PIPE, text=True).stderr
    dur = float(info.split("Duration: ")[1].split(",")[0].split(":")[2])
    avail = max(0.1, dur - a - 0.05)
    vf = []
    if spec.get("slow"):  # ralenti : images intermédiaires calculées (interpolation de mouvement)
        sp = spec["slow"]
        vf += [f"scale={W}:{H}:flags=lanczos,setsar=1", f"minterpolate=fps={round(FPS / sp)}:mi_mode=mci:mc_mode=aobmc:vsbmc=1",
               f"setpts=PTS/{sp:.4f}", f"fps={FPS}"]
        need = tot / FPS * sp
    else:
        sp = 1.0 if spec.get("hold") else min(PROC, max(0.6, avail / (tot / FPS)))
        vf += [f"setpts=PTS/{sp:.4f}", f"fps={FPS}", f"scale={W}:{H}:flags=lanczos,setsar=1"]
        need = tot / FPS * sp
    if spec.get("blur"):
        vf.append("split[m][bb];[bb]crop=380:360:280:500,boxblur=18:3[b2];[m][b2]overlay=280:500")
    vf.append(GRADE)
    if spec.get("hold"):
        vf.append(f"fps={FPS},tpad=stop_mode=clone:stop_duration={tot / FPS:.3f}")
    else:  # zoom lent sur chaque plan
        vf.append(f"scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,"
                  f"zoompan=z='1+0.05*on/{max(1, tot - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
                  f"tpad=stop_mode=clone:stop_duration={tot / FPS:.3f}")
    vf.append("format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-t", f"{min(avail, need) + 0.3:.3f}", "-i", src(clip),
         "-filter_complex", ",".join(vf), "-frames:v", str(tot), "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "16", out])
    return out


def process_track():
    segs, f = [], 0  # (fichier, images utiles, est_manip)
    for k, (r0, r1, spec) in enumerate(PROCESS):
        f0, f1 = Fr(r0), Fr(r1)
        if f0 > f:
            segs.append([None, f0 - f, False])
        segs.append([spec, f1 - f0, True])
        f = f1
    if TOTAL_F > f:
        segs.append([None, TOTAL_F - f, False])
    files, ext = [], []
    for k, (spec, n, is_proc) in enumerate(segs):
        nxt = segs[k + 1] if k + 1 < len(segs) else None
        e = 0 if nxt is None else (XF if (is_proc and nxt[2]) else 1)
        files.append(render_proc(k, n, e, spec) if is_proc else black(k, n + e, "pb"))
        ext.append(e)
    # chaîne de fondus : décalage du fondu i = somme des durées utiles 0..i
    ins, fc, off, last = [], [], 0, "[s0]"
    for i, x in enumerate(files):
        ins += ["-i", x]
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[s{i}]")
    for i in range(1, len(files)):
        off += segs[i - 1][1]
        lab = f"[x{i}]"
        fc.append(f"{last}[s{i}]xfade=transition=fade:duration={ext[i - 1] / FPS:.4f}:offset={off / FPS:.4f}{lab}")
        last = lab
    out = os.path.join(TMP, "process.mp4")
    run([FF, "-y", *ins, "-filter_complex", ";".join(fc), "-map", last, "-frames:v", str(TOTAL_F),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", out])
    return out


# ---------------------------------------------------------------------------------------
# Calque : sous-titres FR + EN, cadre de la vignette, flèches et étiquettes, carton
# ---------------------------------------------------------------------------------------
def font(size, weight):
    f = ImageFont.truetype(os.path.join(v3.FONTS, "Montserrat[wght].ttf"), size)
    f.set_variation_by_axes([weight])
    return f


def wrap(text, f, maxw, stroke):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if cur and f.getbbox(t, stroke_width=stroke)[2] > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    return lines + [cur]


def subtitle(fr, en):
    ffr, fen = font(52, 800), font(40, 600)
    lf, le = wrap(fr, ffr, 940, 6), wrap(en, fen, 940, 5)
    h = 66 * len(lf) + 16 + 52 * len(le) + 30
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 10
    for ln in lf:
        lw = ffr.getbbox(ln, stroke_width=6)[2]
        d.text(((W - lw) // 2, y), ln, font=ffr, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
        y += 66
    y += 16
    for ln in le:
        lw = fen.getbbox(ln, stroke_width=5)[2]
        d.text(((W - lw) // 2, y), ln, font=fen, fill=(255, 226, 110), stroke_width=5, stroke_fill=(0, 0, 0))
        y += 52
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 140), mask=im.getchannel("A").point(lambda v: 255 if v > 0 else 0))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (3, 5))
    out.alpha_composite(im)
    return out


def chip(text, size, fg, bg, pad=22):
    f = font(size, 800)
    l, t, r, b = f.getbbox(text)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), 20, fill=bg)
    d.text((pad - l, pad - t), text, font=f, fill=fg)
    return im


def paste_c(L, im, cx, cy, a=1.0):
    if a < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    x, y = round(cx - im.width / 2), round(cy - im.height / 2)
    L.alpha_composite(im, (max(0, x), max(0, y)))


def build_overlay(path):
    subs = [(Fr(t0), subtitle(fr, en)) for t0, fr, en in SUBS]
    subs = [(f0, (subs[i + 1][0] if i + 1 < len(subs) else Fr(TLINE.voice_end) + 15), im) for i, (f0, im) in enumerate(subs)]
    bx, by, bw, bh = BUBBLE
    frame = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((14, 14, bw + 25, bh + 25), 34, outline=(255, 255, 255, 255), width=7)
    pip = [(Fr(a), Fr(b)) for a, b in PIP]
    AR = v2.arrow().resize((160, 120), Image.LANCZOS)
    _, marks, ph_bottom = v3.photo_frames(1)
    ph_top = H - ph_bottom  # la photo est centrée verticalement
    lab_neg = chip("NÉGATIF · NEGATIVE", 54, (255, 255, 255), (30, 170, 80, 235))
    lab_pos = chip("POSITIF · POSITIVE", 54, (255, 255, 255), (225, 40, 40, 235))
    ex = chip("EXEMPLE (AUTRE TEST) · EXAMPLE (OTHER TEST)", 34, (15, 27, 45), (255, 214, 0, 240), pad=16)
    card1 = chip("MOINS DE 3 MOIS", 92, (255, 255, 255), (225, 40, 40, 240), pad=30)
    card2 = chip("UNDER 3 MONTHS", 58, (255, 226, 110), (0, 0, 0, 0), pad=10)
    siren = v3.emoji_im("🚨", 200)
    r_res = (Fr(27.90), Fr(31.70))
    f_neg_arrow, f_neg_lab = Fr(28.05), Fr(31.02)
    r_ph = (Fr(31.70), Fr(35.53))
    f_pos_arrow, f_pos_lab = Fr(32.70), Fr(34.54)
    r_card = (Fr(46.70), Fr(48.73))
    badges = [(Fr(t), v5.badge(n)) for t, n in BADGES]
    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "qtrle", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(TOTAL_F):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i, (b0, im) in enumerate(badges):  # pastilles 1, 2, 3 (comme en v5)
            b1 = badges[i + 1][0] if i + 1 < len(badges) else Fr(REFL_END)
            if b0 <= f < b1:
                v5.paste_s(L, im, 890, 560, v5.pop_scale(f, b0))
        if any(a <= f < b for a, b in pip):
            L.alpha_composite(frame, (bx - 20, by - 20))
        if r_res[0] <= f < r_res[1]:
            if f >= f_neg_arrow:
                for mx, my in v3.MARK_NEG:
                    paste_c(L, AR, mx, my - 100, a=min(1, (f - f_neg_arrow) / 5))
            if f >= f_neg_lab:
                paste_c(L, lab_neg, W / 2, 380, a=min(1, (f - f_neg_lab) / 5))
        if r_ph[0] <= f < r_ph[1]:
            paste_c(L, ex, W / 2, ph_top - 50)  # au-dessus de la photo (le bas est pris par les sous-titres)
            if f >= f_pos_arrow:
                for mx, my in marks:
                    paste_c(L, AR, mx, my - 100, a=min(1, (f - f_pos_arrow) / 5))
            if f >= f_pos_lab:
                paste_c(L, lab_pos, W / 2, 380, a=min(1, (f - f_pos_lab) / 5))
        if r_card[0] <= f < r_card[1]:
            a = min(1, (f - r_card[0]) / 6)
            paste_c(L, siren, W / 2, 560, a)
            paste_c(L, card1, W / 2, 800, a)
            paste_c(L, card2, W / 2, 930, a)
        for f0, f1, im in subs:
            if f0 <= f < f1:
                L.alpha_composite(im, (0, 1330 - im.height // 2))
                break
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


def bubble_mask(path):
    bx, by, bw, bh = BUBBLE
    m = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, bw - 1, bh - 1), 28, fill=255)
    m.save(path)


# ---------------------------------------------------------------------------------------
# Son : voix (vitesse par partie) + piano doux synthétisé
# ---------------------------------------------------------------------------------------
def build_pops(path):
    fx = np.zeros(int((TOTAL_F / FPS + 1) * sfx.SR))
    for t, _ in BADGES:
        sfx._place(fx, v5.pop_snd(), max(0.0, M(t) - 0.12), 0.35)  # pop juste avant le chiffre
    wavfile.write(path, sfx.SR, (np.clip(fx[: int(TOTAL_F / FPS * sfx.SR)], -1, 1) * 32767).astype(np.int16))


def build_voice(path):
    raw = os.path.join(TMP, "voix_brute.wav")
    v2.build_voice(raw, TLINE)  # mêmes prises et même traitement que la v4 ; appel au commentaire = WA0023
    parts = []
    for k, (a, b, s) in enumerate(_BOUNDS):
        o = os.path.join(TMP, f"vx{k:02d}.wav")
        run([FF, "-y", "-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", raw, "-af", f"atempo={s}", "-ar", "48000", "-ac", "1", o])
        parts.append(o)
    lst = os.path.join(TMP, "vx.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in parts)
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-af", f"apad,atrim=0:{TOTAL_F / FPS:.4f}", path])


def piano_note(freq, d=2.4):
    t = np.arange(int(d * sfx.SR)) / sfx.SR
    x = sum((0.6 ** (h - 1)) * np.sin(2 * np.pi * freq * h * (1 + 0.0004 * h * h) * t) * np.exp(-t * (0.9 + 0.7 * h))
            for h in range(1, 7))
    return sfx._lp(x * np.minimum(1, t / 0.006), 3500)


def build_music(path):
    total = TOTAL_F / FPS
    out = np.zeros(int((total + 3) * sfx.SR))
    n = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # la m – fa – do – sol
    beat, t, k = 0.4, 0.0, 0
    while t < total:
        ch = chords[(k // 8) % 4]
        if k % 8 == 0:  # basse
            sfx._place(out, piano_note(n(ch[0] - 12), 3.2), t, 0.30)
        arp = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[2] + 12, ch[1]]
        gain = 0.16 + 0.06 * min(1, max(0, (t - (total - 12)) / 10))  # légère montée vers l'appel final
        sfx._place(out, piano_note(n(arp[k % 8])), t, gain)
        t += beat
        k += 1
    ir_t = np.arange(int(1.6 * sfx.SR)) / sfx.SR  # réverbération douce
    ir = np.random.default_rng(7).standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45)
    wet = np.convolve(out, ir)[: len(out)]
    out = out + 0.5 * wet / (np.abs(wet).max() + 1e-9) * np.abs(out).max()
    out = out[: int(total * sfx.SR)]
    fade = int(1.5 * sfx.SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    wavfile.write(path, sfx.SR, (np.clip(out / (np.abs(out).max() + 1e-9) * 0.5, -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    print(f"Durée finale : {TOTAL_F / FPS:.2f} s")
    face = face_track()
    proc = process_track()
    ov = os.path.join(TMP, "overlay.mov")
    build_overlay(ov)
    mask = os.path.join(TMP, "mask.png")
    bubble_mask(mask)
    voice, music = os.path.join(TMP, "voix.wav"), os.path.join(TMP, "piano.wav")
    build_voice(voice)
    build_music(music)
    pops = os.path.join(TMP, "pops.wav")
    build_pops(pops)
    # instants (s) des plans visage plein écran = hors manipulations
    proc_iv = [(Fr(a) / FPS, Fr(b) / FPS) for a, b, _ in PROCESS]
    cuts, t = [], 0.0
    for a, b in sorted(proc_iv):
        if a > t + 1e-6:
            cuts.append((t, a))
        t = max(t, b)
    cuts.append((t, TOTAL_F / FPS + 1))
    pip_iv = [(Fr(a) / FPS, Fr(b) / FPS) for a, b in PIP]
    en = lambda iv: "+".join(f"between(t,{a + 1e-3:.4f},{b - 1e-3:.4f})" for a, b in iv)
    bx, by, bw, bh = BUBBLE
    fc = (f"[1:v]split=2[af][ab];[0:v][af]overlay=0:0:enable='{en(cuts)}'[v1];"
          # vignette : un recadrage par séquence (dans WA0037, Abdou se penche vers la droite)
          f"[ab]split=2[ab1][ab2];[4:v]format=gray,scale={bw}:{bh},split=2[m1][m2];"
          f"[ab1]crop=780:982:300:240,scale={bw}:{bh},format=rgba[b1];[b1][m1]alphamerge[ba1];"
          f"[ab2]crop=780:982:150:240,scale={bw}:{bh},format=rgba[b2];[b2][m2]alphamerge[ba2];"
          f"[v1][ba1]overlay={bx}:{by}:enable='{en(pip_iv[:1])}'[v1b];"
          f"[v1b][ba2]overlay={bx}:{by}:enable='{en(pip_iv[1:])}'[v2];"
          f"[v2][2:v]overlay=0:0:format=auto,format=yuv420p[v];"
          # piano : creusé dans la zone de la voix (sinon il masque « fais-le boire », « dans les 24 heures »), plus bas,
          # et baissé davantage sous la voix
          f"[3:a]asplit=2[vo][key];[5:a]equalizer=f=1800:t=o:w=2:g=-10,lowpass=f=2500,volume=0.55[pn];"
          f"[pn][key]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=350[mu];"
          f"[vo][mu][6:a]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
          f"aformat=channel_layouts=stereo[a]")
    dst = os.path.join(OUT, "ep02_montage_v6.mp4")
    run([FF, "-y", "-i", proc, "-i", face, "-i", ov, "-i", voice, "-loop", "1", "-framerate", str(FPS),
         "-t", f"{TOTAL_F / FPS:.3f}", "-i", mask, "-i", music, "-i", pops, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-frames:v", str(TOTAL_F), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", dst])
    r = subprocess.run([FF, "-i", dst, "-af", "ebur128", "-f", "null", "-"], stderr=subprocess.PIPE, text=True).stderr
    lufs = float(r.rsplit("I:", 1)[1].split("LUFS")[0])
    fixed = dst.replace(".mp4", "_n.mp4")
    run([FF, "-y", "-i", dst, "-c:v", "copy", "-af", f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=0",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", fixed])
    os.replace(fixed, dst)
    json.dump(dict(face_full=cuts, pip=pip_iv, process=proc_iv), open(os.path.join(TMP, "plan.json"), "w"), indent=1)
    print("Export :", dst, f"({lufs:.1f} → −14 LUFS)")


if __name__ == "__main__":
    main()
