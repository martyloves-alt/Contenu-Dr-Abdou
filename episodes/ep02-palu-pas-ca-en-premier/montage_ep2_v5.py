"""Épisode 2 — style « process », V2 (montage v5, demandes du 06/10).

Corrections par rapport à la v4 :
  - BUG de synchronisation corrigé : le filtre de zoom (zoompan) produit une image par image d'entrée et
    annulait l'accélération (setpts) ; visages et inserts tournaient à ×1 pendant que la voix tournait à ×1,5,
    d'où un décalage croissant dans chaque plan. On force maintenant la cadence (fps) avant le zoom.
  - Nouvelles notes d'Abdou (06/10), au tutoiement : « Puis va au centre de santé… » (WA0020), « Là où tu vois
    un trait… deux traits… » (WA0021), « Cherche une autre cause. » (WA0022), nouvel appel au commentaire
    « Et toi, sois honnête… sirop… frigo… » (WA0023).
  - Plus de vignette : alternance franche visage plein écran / insert plein écran resserré sur les mains.
  - Accroche : mouvement d'approche (zoom avant) dès la 1re seconde + riser qui finit sur « Ne fais… ».
  - Réflexes : pastilles 1, 2, 3 avec un « pop » juste avant chaque chiffre.
  - Urgences : un mot-clé à la fois, synchronisé sur la voix ; battement de cœur sourd ; sous-titre
    « a moins de 3 mois » (verbe avoir, comme dans le script validé).
  - Pas de musique de fond : elle sera ajoutée depuis la bibliothèque TikTok/Instagram à la publication.
Usage : python3 montage_ep2_v5.py → out/ep02_montage_v5.mp4
"""
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile

import montage_ep2 as v1
import montage_ep2_v2 as v2
import montage_ep2_v3 as v3
import montage_ep2_v4 as v4
from montage_ep2 import FF, FPS, W, H, run, sfx
from montage_ep2_v2 import src, kept

OUT = v1.OUT
TMP = os.path.join(OUT, "tmp_v5")
GRADE = v4.GRADE
# inserts : un peu plus de lumière et un léger débruitage (on ne peut pas refaire l'éclairage du tournage)
GRADE_INS = "hqdn3d=2:1.5:3:3,eq=brightness=0.03:contrast=1.07:saturation=1.08,colorbalance=rs=0.02:bs=-0.02,unsharp=5:5:0.6"

# Parties vocales (clip, début, fin dans le fichier source). face=True : visage synchronisé disponible.
PARTS = [
    dict(id="hook", audio=("IMG_4570", 0.10, 5.52), face=True),
    dict(id="piege", audio=("WA0037", 0.40, 9.12), face=True),
    dict(id="reflexes", audio=("WA0036", 0.15, 17.78), face=True),
    dict(id="tdr", audio=("n3", 1.15, 5.15), face=False),        # WA0020 (06/10)
    dict(id="lecture", audio=("n4", 1.00, 9.60), face=False),    # WA0021 (06/10)
    dict(id="resultat", audio=("WA0033", 4.95, 12.08), face=True),
    dict(id="res_b", audio=("n5", 1.25, 2.75), face=False),      # WA0022 : « Cherche une autre cause. »
    dict(id="urg_a", audio=("WA0035", 0.45, 6.80), face=True),
    dict(id="urg_mois", audio=("n1r", 1.10, 3.30), face=False),  # « À moins de trois mois »
    dict(id="urg_b", audio=("WA0035", 9.55, 11.88), face=True),
    dict(id="cta", audio=("n6", 0.80, 7.85), face=False),        # WA0023 (06/10) « Et toi… au cas où ? »
    # pause de 1,4 s retirée (silence + un clic, aucun mot à la transcription), puis « Dis-le-moi… dangereux. »
    dict(id="cta2", audio=("n6", 9.15, 12.50), face=False),
]
PID = {p["id"]: i for i, p in enumerate(PARTS)}
TAIL = ("IMG_4569", 0.20, 1.85)
SPEED = {p["id"]: 1.5 for p in PARTS}
SPEED.update(urg_a=1.3, urg_mois=1.3, urg_b=1.3)


class TL5:
    """Montage brut : morceaux de voix (silences mesurés retirés), à vitesse 1."""

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
        """Instant du montage brut correspondant à l'instant `raw` du fichier source de la partie."""
        cands = [x for x in self.pieces if x[0] == PID[pid]]
        for _, _, a, b, t0 in cands:
            if raw <= b:
                return t0 + max(0.0, raw - a)
        _, _, a, b, t0 = cands[-1]
        return t0 + b - a


TLN = TL5()
BOUNDS = [(a, b, SPEED[p["id"]]) for p, (a, b) in zip(PARTS, TLN.rng)] + [(TLN.voice_end, TLN.total, 1.5)]


def M(t):
    acc = 0.0
    for a, b, s in BOUNDS:
        if t <= b + 1e-9:
            return acc + max(0.0, t - a) / s
        acc += (b - a) / s
    return acc


def Fr(t):
    return round(M(t) * FPS)


def at(pid, raw):
    """Instant final (s) d'un mot prononcé à `raw` dans le fichier source de la partie."""
    return M(TLN.at(pid, raw))


TOTAL_F = Fr(TLN.total)


_OLD = v2.TL().pieces


def old(t):
    """Instant (montage brut v2/v3) → partie + instant source, via le découpage v2 (mêmes prises)."""
    for pi, clip, a, b, t0 in _OLD:
        if t0 - 1e-6 <= t < t0 + (b - a) + 1e-6:
            return v2.PARTS[pi]["id"], a + t - t0
    raise ValueError(t)


def at_old(t):
    pid, raw = old(t)
    return at(pid, raw)


# ---------------------------------------------------------------------------------------
# Plan image : visage plein écran ou insert plein écran (pas de vignette)
# ---------------------------------------------------------------------------------------
def inserts():
    """(début final s, fin final s, réglages). Partout ailleurs : visage synchronisé."""
    tdr0, tdr1 = M(TLN.rng[PID["tdr"]][0]), M(TLN.rng[PID["tdr"]][1])
    lec0, lec1 = M(TLN.rng[PID["lecture"]][0]), M(TLN.rng[PID["lecture"]][1])
    rb0, rb1 = M(TLN.rng[PID["res_b"]][0]), M(TLN.rng[PID["res_b"]][1])
    um0, um1 = M(TLN.rng[PID["urg_mois"]][0]), M(TLN.rng[PID["urg_mois"]][1])
    cta0 = M(TLN.rng[PID["cta"]][0])
    deux = at("lecture", 6.45)
    d = (tdr1 - tdr0) / 5
    return [
        (at_old(6.10), at_old(7.10), dict(clip="IMG_4559", a=0.2, blur=True)),          # « antipaludéen »
        (at_old(7.10), at_old(8.40), dict(clip="IMG_4541", a=0.0)),                     # « sans faire le test »
        (tdr0, tdr0 + d, dict(clip="IMG_4543", a=0.0)),                                  # « Puis va au centre… »
        (tdr0 + d, tdr0 + 2 * d, dict(clip="IMG_4550", a=10.5)),
        (tdr0 + 2 * d, tdr0 + 3 * d, dict(clip="IMG_4551", a=0.0)),
        (tdr0 + 3 * d, tdr0 + 4 * d, dict(clip="IMG_4553", a=0.0)),
        (tdr0 + 4 * d, lec0, dict(clip="IMG_4555", a=3.55, slow=0.5)),                  # goutte, ralenti
        (lec0, deux - 0.15, dict(clip="IMG_4558", a=0.0, hold=True)),                   # « un trait » : négatif filmé
        (deux - 0.15, lec1, dict(photo=True)),                                            # « deux traits » : photo
        (rb0, rb1, dict(clip="IMG_4558", a=0.0, hold=True)),                             # « Cherche une autre cause »
        (um0, um1, dict(card=True)),                                                      # « à moins de 3 mois »
        (cta0, at("cta", 6.70), dict(clip="IMG_4559", a=0.0, blur=True)),               # « …le sirop… au frigo »
        (at("cta", 6.70), M(TLN.voice_end), dict(clip="IMG_4568", a=0.3)),             # « Dis-le-moi en commentaire… »
    ]


def render_face(k, clip, a, n, speed, zoom, approach=False):
    out = os.path.join(TMP, f"f{k:03d}.mp4")
    cw, ch, cx, cy = v3.face_crop(clip, zoom)
    z = "1.30-0.30*min(1,on/24)" if approach else f"1+0.03*on/{max(1, n - 1)}"  # approche : 1,30 → 1 en 0,8 s
    vf = (f"setpts=PTS/{speed:.4f},fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,crop={cw}:{ch}:{cx}:{cy},{GRADE},"
          f"scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,"
          f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-t", f"{n / FPS * speed + 0.4:.3f}", "-i", src(clip), "-vf", vf,
         "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


def render_insert(k, n, spec):
    out = os.path.join(TMP, f"i{k:03d}.mp4")
    if spec.get("photo"):
        return v1.encode(v3.photo_frames(n)[0], out, H)
    if spec.get("card"):
        return v1.encode(v3.carton_frames(n), out, H)
    clip, a = spec["clip"], spec["a"]
    info = subprocess.run([FF, "-i", src(clip)], stderr=subprocess.PIPE, text=True).stderr
    dur = float(info.split("Duration: ")[1].split(",")[0].split(":")[2])
    avail = max(0.1, dur - a - 0.05)
    if spec.get("slow"):
        sp = spec["slow"]
        vf = [f"scale={W}:{H}:flags=lanczos,setsar=1",
              f"minterpolate=fps={round(FPS / sp)}:mi_mode=mci:mc_mode=aobmc:vsbmc=1", f"setpts=PTS/{sp:.4f}", f"fps={FPS}"]
    elif spec.get("hold"):
        sp = 1.0
        vf = [f"fps={FPS}", f"scale={W}:{H}:flags=lanczos,setsar=1"]
    else:
        sp = min(v4.PROC, max(0.6, avail / (n / FPS)))
        vf = [f"setpts=PTS/{sp:.4f}", f"fps={FPS}", f"scale={W}:{H}:flags=lanczos,setsar=1"]
    if spec.get("blur"):
        vf.append("split[m][bb];[bb]crop=380:360:280:500,boxblur=18:3[b2];[m][b2]overlay=280:500")
    vf.append(GRADE_INS)
    if spec.get("hold"):  # plan fixe : pas de zoom (les flèches pointent les traits au pixel près)
        vf.append(f"tpad=stop_mode=clone:stop_duration={n / FPS:.3f}")
    else:  # insert resserré sur les mains (×1,2) + zoom lent
        vf.append(f"tpad=stop_mode=clone:stop_duration={n / FPS:.3f},scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,"
                  f"zoompan=z='1.2+0.06*on/{max(1, n - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    vf.append("format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-t", f"{min(avail, n / FPS * sp) + 0.3:.3f}", "-i", src(clip),
         "-filter_complex", ",".join(vf), "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "16", out])
    return out


def video_track(ins):
    """Une seule piste : pour chaque image, insert s'il y en a un, sinon visage synchronisé."""
    iv = sorted((round(a * FPS), round(b * FPS), s) for a, b, s in ins)
    files, f, z, k = [], 0, 0, 0

    def face_span(f0, f1):
        nonlocal z, k
        # morceaux de voix qui recouvrent [f0, f1)
        for pi, clip, a, b, t0 in TLN.pieces:
            p = PARTS[pi]
            p0, p1 = Fr(t0), Fr(t0 + b - a)
            s0, s1 = max(p0, f0), min(p1, f1)
            if s1 <= s0:
                continue
            if not p["face"]:  # ne doit pas arriver (couvert par un insert) : sécurité
                files.append(v4.black(len(files), s1 - s0))
                continue
            src_a = a + (s0 - p0) / FPS * SPEED[p["id"]]
            if p1 - p0 >= 10 and s0 == p0:
                z += 1
            files.append(render_face(len(files), clip, src_a, s1 - s0, SPEED[p["id"]], 1.06 if z % 2 else 1.18,
                                     approach=(s0 == 0)))
        tf0 = Fr(TLN.voice_end)
        if f1 > tf0:
            s0 = max(f0, tf0)
            files.append(render_face(len(files), TAIL[0], TAIL[1] + (s0 - tf0) / FPS * 1.5, f1 - s0, 1.5, 1.06))

    for a, b, spec in iv:
        if a > f:
            face_span(f, a)
        files.append(render_insert(len(files), b - a, spec))
        f = b
    if TOTAL_F > f:
        face_span(f, TOTAL_F)
    return v4.concat(files, os.path.join(TMP, "video.mp4"))


# ---------------------------------------------------------------------------------------
# Calque : sous-titres FR + EN, pastilles, flèches, mots-clés d'urgence
# ---------------------------------------------------------------------------------------
def subs():
    O, A = at_old, at
    return [
        (O(0.00), "Tu soupçonnes le palu chez ton enfant ?", "Do you suspect malaria in your child?"),
        (O(2.12), "Ne fais SURTOUT PAS ça en premier !", "Whatever you do, DON'T do this first!"),
        (O(4.40), "L'erreur classique :", "The classic mistake:"),
        (O(5.42), "lui donner un antipaludéen sans faire le test.", "giving an antimalarial without testing."),
        (O(8.40), "Si c'est une autre maladie,", "If it's another illness,"),
        (O(9.80), "tu perds un temps précieux.", "you're losing precious time."),
        (O(11.70), "Trois bons réflexes.", "Three good reflexes."),
        (O(12.86), "Un : note l'heure du début de la fièvre.", "One: note when the fever started."),
        (O(15.38), "Deux : fais-le boire, ou allaite-le.", "Two: give fluids, or breastfeed."),
        (O(18.18), "Trois : paracétamol pour son confort,", "Three: paracetamol for comfort,"),
        (O(20.80), "et à la bonne dose.", "at the right dose."),
        (A("tdr", 1.32), "Puis va au centre de santé le plus proche", "Then go to the nearest health centre"),
        (A("tdr", 3.46), "dans les 24 heures pour le TDR.", "within 24 hours for a rapid test (RDT)."),
        (A("lecture", 1.14), "Là où tu vois un trait,", "Where you see one line,"),
        (A("lecture", 2.74), "c'est que le test est négatif.", "the test is negative."),
        (A("lecture", 5.24), "Et là où tu vois deux traits,", "And where you see two lines,"),
        (A("lecture", 7.28), "c'est que le test est positif.", "the test is positive."),
        (A("resultat", 5.32), "Si TDR positif : traitement complet, jusqu'au bout.", "Positive test: full treatment, right to the end."),
        (A("resultat", 10.00), "Si TDR négatif :", "Negative test:"),
        (A("res_b", 1.40), "cherche une autre cause.", "look for another cause."),
        (O(42.36), "Mais s'il convulse, ne tète plus,", "But if the child has seizures, won't breastfeed,"),
        (O(44.86), "vomit tout, dort trop,", "vomits everything, sleeps too much,"),
        (A("urg_mois", 1.26), "a moins de 3 mois,", "or is under 3 months old,"),
        (A("urg_b", 9.60), "allez aux urgences tout de suite.", "go to the emergency room right away."),
        (A("cta", 0.94), "Et toi, sois honnête : c'est quoi le sirop", "And you, be honest: what's the syrup"),
        (A("cta", 4.52), "que tu caches toujours au frigo « au cas où » ?", "you always hide in the fridge \"just in case\"?"),
        (A("cta2", 9.20), "Dis-le-moi en commentaire,", "Tell me in the comments,"),
        (A("cta2", 10.38), "je te dirai si c'est dangereux.", "I'll tell you if it's dangerous."),
    ]


def badge(num):
    im = Image.new("RGBA", (190, 190), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 10, 184, 188), fill=(0, 0, 0, 90))
    d.ellipse((0, 0, 178, 178), fill=(255, 214, 0, 255), outline=(255, 255, 255, 255), width=8)
    f = v4.font(110, 900)
    l, t, r, b = f.getbbox(num)
    d.text((89 - (r - l) / 2 - l, 89 - (b - t) / 2 - t), num, font=f, fill=(15, 27, 45))
    return im


def pop_scale(f, f0):
    p = (f - f0) / 6
    return 0 if p < 0 else (1.15 * np.sin(p * np.pi / 2) if p < 0.7 else max(1.0, 1.15 - 0.15 * (p - 0.7) / 0.3))


def paste_s(L, im, cx, cy, sc):
    if sc <= 0.02:
        return
    if abs(sc - 1) > 1e-3:
        im = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.LANCZOS)
    L.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def cues():
    """Instants finaux (s) des événements visuels et sonores."""
    O, A = at_old, at
    lec1 = M(TLN.rng[PID["lecture"]][1])
    rb = (M(TLN.rng[PID["res_b"]][0]), M(TLN.rng[PID["res_b"]][1]))
    return dict(
        ne_fais=O(2.12), n1=O(12.86), n2=O(15.38), n3=O(18.18), refl_end=O(22.20),
        trait=A("lecture", 2.00), neg=A("lecture", 4.50), deux=A("lecture", 6.45), pos=A("lecture", 8.80), lec_end=lec1,
        res_b=rb,
        u_conv=O(42.94), u_tete=O(44.08), u_vomit=O(44.86), u_dort=O(45.70),
        u_mois=(M(TLN.rng[PID["urg_mois"]][0]), M(TLN.rng[PID["urg_mois"]][1])),
        u_urg=O(49.20), u_end=M(TLN.rng[PID["urg_b"]][1]), urg0=M(TLN.rng[PID["urg_a"]][0]),
    )


def build_overlay(path, ins):
    S = [(round(t * FPS), v4.subtitle(fr, en)) for t, fr, en in subs()]
    S = [(f0, S[i + 1][0] if i + 1 < len(S) else round(M(TLN.voice_end) * FPS) + 15, im) for i, (f0, im) in enumerate(S)]
    c = {k: (round(v * FPS) if not isinstance(v, tuple) else tuple(round(x * FPS) for x in v)) for k, v in cues().items()}
    nums = [(c["n1"], badge("1")), (c["n2"], badge("2")), (c["n3"], badge("3"))]
    AR = v2.arrow().resize((160, 120), Image.LANCZOS)
    _, marks, ph_bottom = v3.photo_frames(1)
    ph_top = H - ph_bottom
    lab_neg = v4.chip("NÉGATIF · NEGATIVE", 54, (255, 255, 255), (30, 170, 80, 235))
    lab_pos = v4.chip("POSITIF · POSITIVE", 54, (255, 255, 255), (225, 40, 40, 235))
    lab_cause = v4.chip("AUTRE CAUSE · OTHER CAUSE", 50, (15, 27, 45), (255, 214, 0, 240))
    ex = v4.chip("EXEMPLE (AUTRE TEST) · EXAMPLE (OTHER TEST)", 34, (15, 27, 45), (255, 214, 0, 240), pad=16)
    urg_kw = [(c["u_conv"], "CONVULSE · SEIZURES"), (c["u_tete"], "NE TÈTE PLUS · WON'T FEED"),
              (c["u_vomit"], "VOMIT TOUT · VOMITS"), (c["u_dort"], "DORT TROP · TOO SLEEPY"),
              (c["u_mois"][0], None), (c["u_urg"], "URGENCES · EMERGENCY")]  # rien pendant le carton
    urg_im = {t: v4.chip(t, 58, (255, 255, 255), (225, 40, 40, 240)) for _, t in urg_kw if t}
    card1 = v4.chip("A MOINS DE 3 MOIS", 84, (255, 255, 255), (225, 40, 40, 240), pad=30)
    card2 = v4.chip("UNDER 3 MONTHS OLD", 54, (255, 226, 110), (0, 0, 0, 0), pad=10)
    siren = v3.emoji_im("🚨", 200)
    photo_iv = [(round(a * FPS), round(b * FPS)) for a, b, s in ins if s.get("photo")][0]
    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "qtrle", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for f in range(TOTAL_F):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # réflexes : la pastille du chiffre en cours
        for i, (f0, im) in enumerate(nums):
            f1 = nums[i + 1][0] if i + 1 < len(nums) else c["refl_end"]
            if f0 <= f < f1:
                paste_s(L, im, 890, 560, pop_scale(f, f0))  # à droite du visage, à hauteur des mains
        # lecture du test : négatif filmé, puis photo positive
        if c["trait"] <= f < photo_iv[0]:
            for mx, my in v3.MARK_NEG:
                paste_s(L, AR, mx, my - 100, pop_scale(f, c["trait"]))
            if f >= c["neg"]:
                paste_s(L, lab_neg, W / 2, 380, pop_scale(f, c["neg"]))
        if photo_iv[0] <= f < photo_iv[1]:
            paste_s(L, ex, W / 2, ph_top - 50, 1)
            if f >= c["deux"]:
                for mx, my in marks:
                    paste_s(L, AR, mx, my - 100, pop_scale(f, c["deux"]))
            if f >= c["pos"]:
                paste_s(L, lab_pos, W / 2, 380, pop_scale(f, c["pos"]))
        if c["res_b"][0] <= f < c["res_b"][1]:
            for mx, my in v3.MARK_NEG:
                paste_s(L, AR, mx, my - 100, 1)
            paste_s(L, lab_cause, W / 2, 380, pop_scale(f, c["res_b"][0]))
        # urgences : un mot-clé à la fois
        for i, (f0, t) in enumerate(urg_kw):
            f1 = urg_kw[i + 1][0] if i + 1 < len(urg_kw) else c["u_end"]
            if t and f0 <= f < f1:
                paste_s(L, urg_im[t], W / 2, 185, pop_scale(f, f0))  # au-dessus de la tête
        if c["u_mois"][0] <= f < c["u_mois"][1]:
            sc = pop_scale(f, c["u_mois"][0])
            paste_s(L, siren, W / 2, 560, sc)
            paste_s(L, card1, W / 2, 800, sc)
            paste_s(L, card2, W / 2, 930, sc)
        for f0, f1, im in S:
            if f0 <= f < f1:
                L.alpha_composite(im, (0, 1330 - im.height // 2))
                break
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------------------------------
# Son : voix (vitesse par partie) + habillage (riser, pops, battement de cœur) ; pas de musique
# ---------------------------------------------------------------------------------------
def build_voice(path):
    raw = os.path.join(TMP, "voix_brute.wav")
    v2.build_voice(raw, TLN)  # nettoyage et niveau par morceau (réglages des montages précédents)
    parts = []
    for k, (a, b, s) in enumerate(BOUNDS):
        o = os.path.join(TMP, f"vx{k:02d}.wav")
        run([FF, "-y", "-ss", f"{a:.4f}", "-to", f"{b:.4f}", "-i", raw, "-af", f"atempo={s}", "-ar", "48000", "-ac", "1", o])
        parts.append(o)
    lst = os.path.join(TMP, "vx.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in parts)
    run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-af", f"apad,atrim=0:{TOTAL_F / FPS:.4f}", path])


def riser(d=0.7):
    t = np.arange(int(d * sfx.SR)) / sfx.SR
    n = np.random.default_rng(4).standard_normal(len(t))
    sweep = np.sin(2 * np.pi * np.cumsum(300 * 6 ** (t / d)) / sfx.SR) * 0.3
    x = sfx._bp(n, 500, 6000) * 0.6 + sweep
    return x * (t / d) ** 2 * np.minimum(1, (d - t) / 0.03)


def pop_snd(d=0.05):
    t = np.arange(int(d * sfx.SR)) / sfx.SR
    return np.sin(2 * np.pi * np.cumsum(1200 * np.exp(-t / 0.012) + 300) / sfx.SR) * np.exp(-t / 0.015)


def build_fx(path):
    c = cues()
    total = TOTAL_F / FPS
    fx = np.zeros(int((total + 1) * sfx.SR))
    sfx._place(fx, riser(), max(0.0, c["ne_fais"] - 0.72), 0.5)        # finit juste avant « Ne fais… »
    for k in ("n1", "n2", "n3"):
        sfx._place(fx, pop_snd(), max(0.0, c[k] - 0.12), 0.35)           # pop juste avant le chiffre
    sfx._place(fx, sfx.heartbeat(c["u_end"] - c["urg0"], bpm=96), c["urg0"], 0.45)  # urgences : cœur sourd
    wavfile.write(path, sfx.SR, (np.clip(fx[: int(total * sfx.SR)], -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    print(f"Durée finale : {TOTAL_F / FPS:.2f} s")
    for p, (a, b) in zip(PARTS, TLN.rng):
        print(f"  {p['id']:9s} {M(a):6.2f}-{M(b):6.2f}")
    ins = inserts()
    vid = video_track(ins)
    ov = os.path.join(TMP, "overlay.mov")
    build_overlay(ov, ins)
    voice, fxp = os.path.join(TMP, "voix.wav"), os.path.join(TMP, "fx.wav")
    build_voice(voice)
    build_fx(fxp)
    fc = (f"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
          f"[2:a]asplit=2[vo][key];[3:a][key]sidechaincompress=threshold=0.03:ratio=4:attack=10:release=300[fx];"
          f"[vo][fx]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
          f"aformat=channel_layouts=stereo[a]")
    dst = os.path.join(OUT, "ep02_montage_v5.mp4")
    run([FF, "-y", "-i", vid, "-i", ov, "-i", voice, "-i", fxp, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-frames:v", str(TOTAL_F), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", dst])
    r = subprocess.run([FF, "-i", dst, "-af", "ebur128", "-f", "null", "-"], stderr=subprocess.PIPE, text=True).stderr
    lufs = float(r.rsplit("I:", 1)[1].split("LUFS")[0])
    fixed = dst.replace(".mp4", "_n.mp4")
    run([FF, "-y", "-i", dst, "-c:v", "copy", "-af", f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=0",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", fixed])
    os.replace(fixed, dst)
    json.dump(dict(inserts=[(round(a, 3), round(b, 3), s) for a, b, s in ins]), open(os.path.join(TMP, "plan.json"), "w"),
              indent=1, ensure_ascii=False)
    print("Export :", dst, f"({lufs:.1f} → −14 LUFS)")


if __name__ == "__main__":
    main()
