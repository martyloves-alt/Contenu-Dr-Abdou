"""Génère les éléments graphiques de l'épisode 1 (PNG transparents, 2160x3840 = 4K 9:16).

Aucun contenu médical ajouté : tous les textes viennent mot pour mot du script validé.
Usage : python3 make_graphics.py
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 2160, 3840
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphics")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

RED = (229, 57, 53, 255)
WHITE = (255, 255, 255, 255)
DARK = (15, 27, 45, 255)
DARK_T = (15, 27, 45, 215)
YELLOW = (255, 193, 7, 255)

# Zones sûres TikTok/Reels : rien d'important dans les 12 % du haut ni les 22 % du bas.
SAFE_TOP = int(H * 0.12)


def font(size):
    return ImageFont.truetype(FONT, size)


def canvas(bg=(0, 0, 0, 0)):
    return Image.new("RGBA", (W, H), bg)


def text_box(draw, cx, y, text, size, fg, bg, pad=60, radius=40):
    f = font(size)
    l, t, r, b = draw.textbbox((0, 0), text, font=f)
    w, h = r - l, b - t
    x0 = cx - w // 2 - pad
    draw.rounded_rectangle((x0, y, x0 + w + 2 * pad, y + h + 2 * pad), radius, fill=bg)
    draw.text((x0 + pad - l, y + pad - t), text, font=f, fill=fg)
    return y + h + 2 * pad


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    print("écrit", path)


def hook():
    # 0–1,5 s : « FIÈVRE = LES DENTS ? FAUX »
    img = canvas()
    d = ImageDraw.Draw(img)
    y = text_box(d, W // 2, SAFE_TOP + 80, "FIÈVRE = LES DENTS\u00a0?", 120, WHITE, DARK_T)
    text_box(d, W // 2, y + 50, "FAUX", 260, WHITE, RED, pad=70)
    save(img, "hook_1_faux.png")

    # 1,5–3 s : « PENSE PALUDISME » (mot-clé PALUDISME visible avant 3 s)
    img = canvas()
    d = ImageDraw.Draw(img)
    y = text_box(d, W // 2, SAFE_TOP + 80, "PENSE", 170, DARK, YELLOW)
    text_box(d, W // 2, y + 40, "PALUDISME", 250, WHITE, RED, pad=70)
    save(img, "hook_2_paludisme.png")


def badge_piege3():
    img = canvas()
    d = ImageDraw.Draw(img)
    text_box(d, W // 2, SAFE_TOP + 120, "PIÈGE N°3", 230, WHITE, RED, pad=80, radius=60)
    save(img, "badge_piege3.png")


def chrono_frames(fps=60, seconds=4.0):
    """Chrono « 24 H » rouge : un anneau qui se vide sur la durée du Piège 2."""
    d_ = os.path.join(OUT, "chrono")
    os.makedirs(d_, exist_ok=True)
    n = int(fps * seconds)
    size = 1300
    cx, cy = W // 2, int(H * 0.36)
    for i in range(n):
        p = i / (n - 1)
        img = canvas()
        d = ImageDraw.Draw(img)
        box = (cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2)
        d.ellipse(box, fill=DARK_T)
        d.arc(box, 0, 360, fill=(255, 255, 255, 60), width=70)
        # l'anneau rouge se vide dans le sens horaire
        d.arc(box, -90 + 360 * p, 270, fill=RED, width=70)
        # pulsation légère du texte
        s = 1 + 0.06 * math.sin(p * math.pi * 8)
        f = font(int(360 * s))
        l, t, r, b = d.textbbox((0, 0), "24 H", font=f)
        d.text((cx - (r - l) // 2 - l, cy - (b - t) // 2 - t), "24 H", font=f, fill=RED)
        img.save(os.path.join(d_, f"f{i:04d}.png"))
    print(f"écrit {n} images dans", d_)


def strike():
    """Barre rouge diagonale posée sur la boîte de paracétamol."""
    img = canvas()
    d = ImageDraw.Draw(img)
    cy = int(H * 0.40)
    d.line((240, cy + 900, W - 240, cy - 900), fill=RED, width=150)
    save(img, "barre_paracetamol.png")


CHECKLIST = [
    ("Fièvre ?", "Test au centre de santé dans les 24 heures."),
    ("Convulsions, ne tète plus, vomit tout, dort trop ?", "Urgences. Tout de suite."),
    ("Moins de 3 mois ?", "Urgences."),
]


def wrap(draw, text, f, maxw):
    # espaces insécables (avant « ? ») : ne pas couper dessus
    words, lines, cur = text.replace(" ?", "\u00a0?").split(" "), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=f) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def checklist():
    """3 images cumulatives : 1 ligne, 2 lignes, 3 lignes."""
    fq, fa = font(96), font(110)
    for k in range(1, 4):
        img = canvas()
        d = ImageDraw.Draw(img)
        y = SAFE_TOP + 40
        x0, x1 = 170, W - 330  # marge droite plus large (boutons TikTok)
        for q, a in CHECKLIST[:k]:
            ql = wrap(d, q, fq, x1 - x0 - 260)
            al = wrap(d, a, fa, x1 - x0 - 260)
            h = 60 + len(ql) * 125 + 20 + len(al) * 140 + 60
            emergency = a.startswith("Urgences")
            d.rounded_rectangle((x0, y, x1, y + h), 50, fill=DARK_T)
            # pastille
            col = RED if emergency else YELLOW
            d.ellipse((x0 + 50, y + 60, x0 + 200, y + 210), fill=col)
            d.text((x0 + 125, y + 135), "!" if emergency else "✓", font=font(110), fill=WHITE if emergency else DARK, anchor="mm")
            ty = y + 60
            for line in ql:
                d.text((x0 + 250, ty), line, font=fq, fill=WHITE)
                ty += 125
            ty += 20
            for line in al:
                d.text((x0 + 250, ty), line, font=fa, fill=RED if emergency else YELLOW)
                ty += 140
            y += h + 50
        save(img, f"checklist_{k}.png")


def background():
    save(canvas(DARK), "fond.png")


def placeholder(name, label):
    img = canvas((40, 40, 40, 255))
    d = ImageDraw.Draw(img)
    d.rectangle((60, 60, W - 60, H - 60), outline=YELLOW, width=24)
    d.text((W // 2, H // 2 - 200), "ASSET MANQUANT", font=font(170), fill=YELLOW, anchor="mm")
    d.text((W // 2, H // 2 + 50), name, font=font(110), fill=WHITE, anchor="mm")
    d.text((W // 2, H // 2 + 220), label, font=font(80), fill=(200, 200, 200, 255), anchor="mm")
    save(img, f"manquant_{name.split('.')[0]}.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    hook()
    badge_piege3()
    chrono_frames()
    strike()
    checklist()
    background()
    placeholder("talking-head-hook.mp4", "à fournir par Abdou")
    placeholder("thermometre", "à fournir par Abdou")
    placeholder("paracetamol-boite", "à fournir par Abdou")
    placeholder("tdr", "à fournir par Abdou")
