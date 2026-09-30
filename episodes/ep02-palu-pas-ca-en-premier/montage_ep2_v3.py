"""Épisode 2 — montage v3, style « After » de la vidéo modèle (plein écran, rythme short-form).

Modèle (cadran After uniquement) : visage plein écran avec recadrages alternés à chaque coupe (punch-in),
sous-titres mot par mot sur la poitrine, un mot-clé géant en haut (rouge / jaune, apparition lettre par
lettre), inserts plein écran, stickers qui surgissent en bas à gauche, flashs lumineux aux transitions.

Contenu identique à la v2 (voix, ordre, texte validé) : seules l'image et l'habillage changent.
  - Inserts plein écran = uniquement des images réellement filmées (boîte floutée, kit, sang, migration,
    résultat) ou du graphisme (texte, pictogrammes emoji Noto, licence libre) : aucune image générée.
  - « À moins de 3 mois » (note vocale) est couvert par un carton graphique : plus de décalage lèvres / son.
  - Image d'Abdou plus naturelle : pas de lissage de peau ni de vignettage ; affinage 4 % conservé.
Usage : python3 montage_ep2_v3.py → out/ep02_montage_v3.mp4
"""
import difflib
import json
import math
import os
import re
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import montage_ep2 as v1
import montage_ep2_v2 as v2
from montage_ep2 import FF, FPS, W, H, SPEED, run, encode, concat, pop, paste, RED_WORDS, sfx
from montage_ep2_v2 import TL, PARTS, PID, SUBS, TAIL, FACES, SQUEEZE, src, arrow

HERE, A = v1.HERE, v1.A
OUT, TMP = v1.OUT, os.path.join(v1.OUT, "tmp_v3")
FONTS = os.path.join(HERE, "fonts")
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

RED, YEL, WHT, GRN = (255, 45, 45, 255), (255, 225, 60, 255), (255, 255, 255, 255), (60, 220, 100, 255)
GRADE = ("eq=contrast=1.05:brightness=0.01:saturation=1.08,"
         "colorbalance=rs=0.03:gs=0.01:bs=-0.02:rm=0.02:bm=-0.02,unsharp=5:5:0.5")


# ---------------------------------------------------------------------------------------
# Minutage mot par mot (transcription de la piste voix v2, même montage audio)
# ---------------------------------------------------------------------------------------
def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]", "", s)
    return {"un": "1", "deux": "2", "trois": "3"}.get(s, s)


def whisper_words():
    raw = json.load(open(os.path.join(A, "words_v2.json")))
    out = []
    for x in raw:
        if out and x["w"][:1] in "'-":
            out[-1] = dict(w=out[-1]["w"] + x["w"], s=out[-1]["s"], e=x["e"])
        elif x["w"] in "?!.,":
            continue
        else:
            out.append(dict(x))
    return out


WW = whisper_words()


def w(token, n=1):
    """Début (s, montage avant accélération) du n-ième mot prononcé `token`."""
    hits = [x["s"] for x in WW if norm(x["w"]) == norm(token)]
    return hits[n - 1]


def wr(raw):
    """Début du mot transcrit exactement `raw` (ex. « 1. » pour le chiffre annoncé, distinct de « un »)."""
    return next(x["s"] for x in WW if x["w"].rstrip(".,") == raw)


def caption_groups(tl):
    """Mots du texte validé (SUBS) calés sur les mots prononcés ; mots courts groupés avec le suivant."""
    toks = []
    for pa, a, pb, b, txt in SUBS:
        s, e = tl.at(pa, a), tl.at(pb, b)
        disp = [t for t in re.sub(r"\s+([?:!,])", r"\1", txt).split() if norm(t)]
        spoken = [x for x in WW if s - 0.8 <= x["s"] < e]
        sm = difflib.SequenceMatcher(a=[norm(t) for t in disp], b=[norm(x["w"]) for x in spoken], autojunk=False)
        st = [None] * len(disp)
        for blk in sm.get_matching_blocks():
            for j in range(blk.size):
                st[blk.a + j] = spoken[blk.b + j]["s"]
        # mots non reconnus : interpolation entre voisins
        known = [(i, v) for i, v in enumerate(st) if v is not None] or [(0, s)]
        for i in range(len(st)):
            if st[i] is None:
                prev = max([k for k in known if k[0] < i], default=(-1, s), key=lambda k: k[0])
                nxt = min([k for k in known if k[0] > i], default=(len(st), e), key=lambda k: k[0])
                st[i] = prev[1] + (nxt[1] - prev[1]) * (i - prev[0]) / (nxt[0] - prev[0])
        for t, x in zip(disp, st):
            toks.append([x, t.strip(".,"), e])
    groups, i = [], 0
    while i < len(toks):
        g = [toks[i]]
        while len(norm(g[-1][1])) <= 2 and i + 1 < len(toks) and toks[i + 1][0] - g[-1][0] < 0.6:
            i += 1
            g.append(toks[i])
        groups.append([g[0][0], " ".join(x[1] for x in g), g[-1][2]])
        i += 1
    for k in range(len(groups)):
        end = groups[k + 1][0] if k + 1 < len(groups) else groups[k][2]
        groups[k][2] = min(end, groups[k][0] + 1.2)
    return groups


# ---------------------------------------------------------------------------------------
# Plan image : visage plein écran + inserts
# ---------------------------------------------------------------------------------------
def inserts(tl):
    lec, tdr, um = tl.r("lecture"), tl.r("tdr"), tl.r("urg_mois")
    return [
        (w("antipaludéen") - 0.08, w("sans"), dict(clip="IMG_4559", a=0.0, b=2.0, blur=True)),
        (w("sans"), w("si") - 0.05, dict(clip="IMG_4550", a=1.0, b=17.0)),
        (w("pour", 2) - 0.1, w("pour", 2) + 0.45, dict(clip="IMG_4553", a=0.0, b=0.73)),
        (w("pour", 2) + 0.45, lec[0], dict(clip="IMG_4556", a=0.0, b=7.44)),
        (lec[0], w("et", 2) - 0.1, dict(clip="IMG_4558", a=0.0, b=1.43, hold=True)),
        (w("et", 2) - 0.1, lec[1], dict(photo=True)),
        (um[0], um[1], dict(carton=True)),
    ]


def plan(tl):
    """Liste (t0, t1, spec) couvrant tout le montage."""
    ins = inserts(tl)
    out, z, k = [], 1.24, 0
    for pi, clip, a, b, t0 in tl.pieces:
        if PARTS[pi].get("video") is not None:
            continue
        t1 = t0 + b - a
        if t1 - t0 >= 0.35:  # recadrage alterné à chaque coupe ; un morceau très court garde le cadre précédent
            z, k = (1.06 if k % 2 == 0 else 1.24), k + 1
        segs = [(t0, t1)]
        for i0, i1, _ in ins:
            segs = [x for s0, s1 in segs for x in ((s0, min(s1, i0)), (max(s0, i1), s1)) if x[1] - x[0] > 0.02]
        for s0, s1 in segs:
            out.append((s0, s1, dict(face=clip, a=a + s0 - t0, zoom=z)))
    out += ins
    out.append((tl.voice_end, tl.total, dict(face=TAIL[0], a=TAIL[1], zoom=1.06)))
    out.sort(key=lambda x: x[0])
    # raccords : chaque plan commence exactement où finit le précédent (arrondi à l'image)
    fixed, t = [], 0.0
    for s0, s1, spec in out:
        e = round(s1 * FPS) / FPS
        if e - t >= 1 / FPS:
            fixed.append((t, e, spec))
            t = e
    return fixed


def face_crop(clip, Z):
    f = FACES.get(clip, dict(fx=540, fy=520, fw=400, fh=560))
    h = H / Z
    wd = min(W, W / Z / SQUEEZE)
    x = min(max(0, f["fx"] - wd / 2), W - wd)
    y = min(max(0, f["fy"] - 0.36 * h), H - h)  # visage vers 36 % de la hauteur (0 si le cadre ne le permet pas)
    return round(wd), round(h), round(x), round(y)


def render_video(k, t0, t1, spec):
    out = os.path.join(TMP, f"v{k:03d}.mp4")
    dur = t1 - t0
    n = max(1, round(dur * FPS))
    clip, a = spec.get("face") or spec["clip"], spec["a"]
    if "face" in spec:
        b, speed = a + dur, 1.0
        cw, ch, cx, cy = face_crop(clip, spec["zoom"])
        z0 = 1.0
    else:
        b = spec["b"]
        speed = 1.0 if spec.get("hold") else max(0.5, (b - a) / dur)
        cw, ch, cx, cy = W, H, 0, 0
        z0 = None if spec.get("hold") else 1.0
    vf = [f"setpts=PTS/{speed:.4f}", f"scale={W}:{H}:flags=lanczos,setsar=1"]
    if spec.get("blur"):  # nom commercial flouté (on dénonce un usage, pas une marque)
        vf.append("split[m][bb];[bb]crop=380:360:280:500,boxblur=18:3[b2];[m][b2]overlay=280:500")
    vf.append(f"crop={cw}:{ch}:{cx}:{cy},{GRADE}")
    if z0 is not None:  # zoom lent (+3 %)
        vf.append(f"scale={W * 3 // 2}:{H * 3 // 2}:flags=lanczos,"
                  f"zoompan=z='{z0}+0.03*on/{max(1, n - 1)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
    else:
        vf.append(f"scale={W}:{H}:flags=lanczos,fps={FPS},tpad=stop_mode=clone:stop_duration={dur:.3f}")
    vf.append("format=yuv420p")
    run([FF, "-y", "-ss", f"{a:.3f}", "-t", f"{(b - a) + 0.3:.3f}", "-i", src(clip), "-filter_complex", ",".join(vf),
         "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


# Photo du test positif (autre test, P.f/Pan, photographiée à l'envers) : fond flou + photo agrandie
PH_S, PH_Y = 1.3, None
MARK_NEG = [(505, 695)]  # IMG_4558 plein cadre : ligne C


def photo_frames(n):
    im = Image.open(os.path.join(A, "tdr_resultat.jpg")).convert("RGB").rotate(180)
    s = H / im.height
    bg = im.resize((round(im.width * s), H), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, 0, (bg.width + W) // 2, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.55)
    fg = im.resize((round(im.width * PH_S), round(im.height * PH_S)), Image.LANCZOS)
    ox = 540 - round(471.5 * PH_S)
    oy = (H - fg.height) // 2
    bg.paste(fg, (ox, oy))
    marks = [(ox + round(x * PH_S), oy + round((y - 179) * PH_S)) for x, y in v2.MARK_POS]
    return [bg] * n, marks, oy + fg.height


def carton_frames(n):
    """Carton plein écran « MOINS DE 3 MOIS » sur fond noir quadrillé (façon inserts graphiques du modèle)."""
    frames = []
    base = Image.new("RGB", (W, H), (8, 8, 12))
    d = ImageDraw.Draw(base)
    for x in range(0, W, 90):
        d.line((x, 0, x, H), fill=(22, 26, 30), width=2)
    for y in range(0, H, 90):
        d.line((0, y, W, y), fill=(22, 26, 30), width=2)
    for i in range(n):
        frames.append(base)
    return frames


def render_still(k, t0, t1, spec):
    out = os.path.join(TMP, f"v{k:03d}.mp4")
    n = max(1, round((t1 - t0) * FPS))
    frames = photo_frames(n)[0] if spec.get("photo") else carton_frames(n)
    return encode(frames, out, H)


# ---------------------------------------------------------------------------------------
# Calque graphique
# ---------------------------------------------------------------------------------------
_cache = {}


def mfont(size, weight=900):
    key = ("m", size, weight)
    if key not in _cache:
        f = ImageFont.truetype(os.path.join(FONTS, "Montserrat[wght].ttf"), size)
        f.set_variation_by_axes([weight])
        _cache[key] = f
    return _cache[key]


def text_im(text, size, color, stroke=8, weight=900, maxw=1000):
    key = ("t", text, size, color, stroke, weight)
    if key in _cache:
        return _cache[key]
    lines = [text]
    while True:
        f = mfont(size, weight)
        widths = [f.getbbox(l, stroke_width=stroke)[2] for l in lines]
        if max(widths) <= maxw:
            break
        if len(lines) == 1 and size <= 96 and " " in text:
            words = text.split()
            cut = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(text) / 2))
            lines = [" ".join(words[:cut]), " ".join(words[cut:])]
            continue
        size -= 4
    lh = round(size * 1.12)
    im = Image.new("RGBA", (maxw + 80, lh * len(lines) + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds, d = ImageDraw.Draw(sh), ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        lw = f.getbbox(l, stroke_width=stroke)[2]
        x, y = (im.width - lw) // 2, 20 + i * lh
        ds.text((x + 6, y + 8), l, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        d.text((x, y), l, font=f, fill=color, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    out = sh.filter(ImageFilter.GaussianBlur(6))
    out.alpha_composite(im)
    _cache[key] = out
    return out


def emoji_im(ch, size=250):
    key = ("e", ch, size)
    if key not in _cache:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox())
        _cache[key] = im.resize((size, round(size * im.height / im.width)), Image.LANCZOS)
    return _cache[key]


def glow():
    if "glow" not in _cache:
        yy, xx = np.mgrid[0:H // 4, 0:W // 4]
        r = np.hypot((xx - W / 8) / (W / 4), (yy - H / 5) / (H / 4))
        a = np.clip(1.1 - r, 0, 1) ** 1.5
        rgba = np.dstack([np.full_like(a, 255), 190 + 50 * a, 90 + 120 * a, 255 * a]).astype(np.uint8)
        _cache["glow"] = Image.fromarray(rgba, "RGBA").resize((W, H), Image.BILINEAR)
    return _cache["glow"]


def keywords(tl):
    """(début, texte, couleur, sticker) — un seul mot-clé à la fois, toujours des mots prononcés."""
    return [
        (0.0, "LE PALU ?", YEL, None),
        (w("ne"), "NE FAIS PAS ÇA", RED, "🚫"),
        (w("l'erreur"), "L'ERREUR CLASSIQUE", YEL, None),
        (w("antipaludéen"), "ANTIPALUDÉEN", RED, None),
        (w("sans"), "SANS TEST", RED, None),
        (w("autre"), "UNE AUTRE MALADIE ?", YEL, None),
        (w("temps"), "TEMPS PRÉCIEUX", RED, "⏳"),
        (w("trois"), "3 BONS RÉFLEXES", YEL, None),
        (wr("1"), "1 · L'HEURE", WHT, "⏰"),
        (wr("2"), "2 · BOIRE", WHT, "🍼"),
        (w("allaite-le"), "2 · ALLAITER", WHT, "🤱"),
        (wr("3"), "3 · PARACÉTAMOL", RED, "💊"),
        (w("bonne"), "À LA BONNE DOSE", YEL, None),
        (w("puis"), "CENTRE DE SANTÉ", WHT, "🏥"),
        (w("24"), "#24", YEL, None),
        (w("pour", 2), "TDR", YEL, None),
        (w("point") - 0.55, None, None, None),
        (w("négatif"), "NÉGATIF", GRN, None),
        (w("et", 2) - 0.1, None, None, None),
        (w("positif"), "POSITIF", RED, None),
        (tl.r("resultat")[0], None, None, None),
        (w("positif", 2), "POSITIF", RED, None),
        (w("traitement"), "TRAITEMENT COMPLET", WHT, None),
        (w("jusqu'au"), "JUSQU'AU BOUT", YEL, None),
        (w("négatif", 2), "NÉGATIF", GRN, None),
        (w("cherchez"), "UNE AUTRE CAUSE", YEL, None),
        (w("convulsif") - 0.1, "CONVULSIONS", RED, "🚨"),
        (w("tête"), "NE TÈTE PLUS", RED, "🚨"),
        (w("vomis"), "VOMIT TOUT", RED, "🚨"),
        (w("dors"), "DORT TROP", RED, "🚨"),
        (tl.r("urg_mois")[0], None, None, None),
        (w("urgences"), "URGENCES", RED, "🚨"),
        (w("tout", 2), "TOUT DE SUITE", RED, "🚨"),
        (w("sois"), "SOIS HONNÊTE", YEL, None),
        (w("au", 2), "« AU CAS OÙ » ?", YEL, None),
        (w("dis-le"), "DIS-LE EN COMMENTAIRE", RED, "👇"),
    ]


def flashes(tl, pl):
    t = [s0 for s0, _, spec in pl if "face" not in spec or s0 in [r[0] for r in tl.rng]]
    return sorted({round(x, 3) for x in t if x > 0.2})


def build_overlay(path, tl, pl):
    import subprocess
    KW = keywords(tl)
    caps = caption_groups(tl)
    fl = flashes(tl, pl)
    lec0, um = tl.r("lecture")[0], tl.r("urg_mois")
    ph_marks, ph_bottom = photo_frames(1)[1:]
    AR = arrow().resize((180, 135), Image.LANCZOS)
    tag = text_im("EXEMPLE (AUTRE TEST)", 58, (15, 27, 45, 255), stroke=0, weight=800)
    tag_bg = Image.new("RGBA", (tag.width - 60, tag.height - 30), YEL)
    json.dump(dict(keywords=[(round(a, 2), b) for a, b, *_ in KW], captions=caps, flashes=fl),
              open(os.path.join(TMP, "overlay_plan.json"), "w"), ensure_ascii=False, indent=0)
    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", path], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    for i in range(round(tl.total * FPS)):
        t = i / FPS
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # carton « moins de 3 mois »
        if um[0] <= t < um[1]:
            paste(L, text_im("MOINS DE", 120, WHT), W / 2, 520, scale=pop(t, um[0]))
            paste(L, text_im("3 MOIS", 260, RED, stroke=12), W / 2, 750, scale=pop(t, um[0] + 0.12))
            paste(L, emoji_im("🚨", 230), W / 2, 1020, scale=pop(t, um[0] + 0.25))
        # flèches sur les traits
        if lec0 <= t < w("et", 2) - 0.1 and t >= w("point") - 0.55:
            for mx, my in MARK_NEG:
                paste(L, AR, mx, my - 110, scale=pop(t, w("point") - 0.55))
        if w("et", 2) - 0.1 <= t < tl.r("lecture")[1]:
            if t >= w("deux", 2) - 0.1:
                for mx, my in ph_marks:
                    paste(L, AR, mx, my - 110, scale=pop(t, w("deux", 2) - 0.1))
            L.alpha_composite(tag_bg, (60, ph_bottom + 40))
            L.alpha_composite(tag, (30, ph_bottom + 25))
        # mot-clé du moment (un seul), apparition lettre par lettre
        cur = None
        for k, (t0, txt, col, st) in enumerate(KW):
            t1 = KW[k + 1][0] if k + 1 < len(KW) else tl.total + 1
            if t0 <= t < t1:
                cur = (t0, txt, col, st, t1)
        if cur and cur[1]:
            t0, txt, col, st, t1 = cur
            if txt == "#24":
                txt = f"{min(24, int(24 * (t - t0) / 0.45))} H" if t - t0 < 0.45 else "24 H"
                paste(L, text_im(txt, 170, col), W / 2, 300)
            else:
                nch = max(1, math.ceil(len(txt) * min(1.0, (t - t0) / 0.22)))
                paste(L, text_im(txt[:nch], 120, col), W / 2, 300)
            if st:
                paste(L, emoji_im(st), 230, 1530, scale=pop(t, t0 + 0.05, 0.25))
        # sous-titre mot par mot
        for s0, txt, s1 in caps:
            if s0 <= t < s1:
                red = bool(RED_WORDS.search(txt))
                paste(L, text_im(txt.upper(), 76, RED if red else WHT, stroke=7, weight=800), W / 2, 1290,
                      scale=0.9 + 0.1 * pop(t, s0, 0.1))
                break
        # flash lumineux aux transitions
        for f0 in fl:
            if f0 - 0.06 <= t < f0 + 0.3:
                a = max(0.0, 1 - abs(t - f0 - 0.04) / 0.26) * 0.8
                g = glow().copy()
                g.putalpha(g.getchannel("A").point(lambda v: int(v * a)))
                L.alpha_composite(g)
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


# ---------------------------------------------------------------------------------------
# Son : même voix que la v2, habillage recalé sur les nouveaux plans
# ---------------------------------------------------------------------------------------
def build_sfx(tl, pl, music_p, fx_p):
    from scipy.io import wavfile
    S = SPEED
    r = {p["id"]: (a / S, b / S) for p, (a, b) in zip(PARTS, tl.rng)}
    total = tl.total / S + 0.5
    mus, fx = np.zeros(int(total * sfx.SR)), np.zeros(int(total * sfx.SR))
    sfx._place(fx, sfx.heartbeat(r["hook"][1]), 0.0, 0.4)
    for f0 in flashes(tl, pl):
        # whoosh court, calé dans la coupure : ne déborde ni sur la fin de la phrase, ni sur le mot suivant
        sfx._place(fx, sfx.whoosh(0.3), max(0.0, f0 / S - 0.22), 0.18)
    # pas de « pop » sur les mots-clés : ils tombent sur l'attaque des mots et les masquent (vérifié)
    sfx._place(mus, sfx.dark_bed(r["lecture"][0] - r["piege"][0]), r["piege"][0], 0.26)
    sfx._place(fx, sfx.ticktock(r["tdr"][0] - r["reflexes"][0]), r["reflexes"][0], 0.14)
    sfx._place(fx, sfx.sub_drop(), r["urg_a"][0], 0.7)
    sfx._place(mus, sfx.driving_bed(r["urg_b"][1] - r["urg_a"][0]), r["urg_a"][0], 0.24)
    sfx._place(mus, sfx.neutral_bed(total - r["cta"][0]), r["cta"][0], 0.18)
    for x, pth in ((mus, music_p), (fx, fx_p)):
        wavfile.write(pth, sfx.SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


def main():
    os.makedirs(TMP, exist_ok=True)
    v1.TMP = TMP
    tl = TL()
    pl = plan(tl)
    print(f"Durée : {tl.total:.2f} s → après ×{SPEED} : {tl.total / SPEED:.2f} s ; {len(pl)} plans")
    vids = []
    for k, (t0, t1, spec) in enumerate(pl):
        print(f"  {t0:6.2f}-{t1:6.2f} {spec.get('face') or spec.get('clip') or ('photo' if spec.get('photo') else 'carton')}")
        vids.append(render_video(k, t0, t1, spec) if ("face" in spec or "clip" in spec) else render_still(k, t0, t1, spec))
    base = concat(vids, os.path.join(TMP, "base.mp4"))
    ov = os.path.join(TMP, "overlay.mov")
    build_overlay(ov, tl, pl)
    voice = os.path.join(TMP, "voix.wav")
    v2.build_voice(voice, tl)
    mus, fxp = os.path.join(TMP, "music.wav"), os.path.join(TMP, "fx.wav")
    build_sfx(tl, pl, mus, fxp)
    dst = os.path.join(OUT, "ep02_montage_v3.mp4")
    n = round(tl.total * FPS)
    fc = (f"[0:v]trim=end_frame={n}[b];[b][1:v]overlay=0:0:format=auto,setpts=PTS/{SPEED},fps={FPS},format=yuv420p[v];"
          # musique passée sous 250 Hz (sinon elle masque des mots) ; musique + effets baissés sous la voix
          f"[2:a]atempo={SPEED},asplit=2[vo][key];[3:a]lowpass=f=250[mu];"
          f"[mu][4:a]amix=inputs=2:duration=longest:normalize=0[bed];"
          f"[bed][key]sidechaincompress=threshold=0.02:ratio=8:attack=5:release=300[m];"
          f"[vo][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
          f"aformat=channel_layouts=stereo[a]")
    run([FF, "-y", "-i", base, "-i", ov, "-i", voice, "-i", mus, "-i", fxp, "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", dst])
    print("Export :", dst)


if __name__ == "__main__":
    main()
