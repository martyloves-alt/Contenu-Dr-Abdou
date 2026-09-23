"""Montage v3 : réorganisation manuelle demandée par Abdou/Marty (audit des 3 défauts de la v2).

Ordre : Accroche (mythe des dents) → Faux-ami (paracétamol, coupé avant la fin de la phrase)
→ Urgence (signes qui doivent alerter) → Délivrance (TDR + « PALUDISME ») → Engagement (CTA).

Ce qui change par rapport à v2, et pourquoi :
  - Le hook n'ouvre plus sur « piège n°3 » (interne, illisible pour qui arrive) : il ouvre
    directement sur le mythe qu'on va casser.
  - Suppression totale du bip / « ??? » : dans ce nouvel ordre, le mot « palu » n'est tout
    simplement jamais prononcé avant la révélation (on coupe le Piège 3 juste avant la phrase
    qui le contient). Le suspense vient de l'omission, pas d'un artifice visible.
  - L'appel à l'action passe APRÈS la révélation TDR/PALUDISME, plus avant.
Conséquence : la barre rouge sur la boîte et le chrono « 24 H » n'ont plus de phrase à
illustrer (elles étaient accrochées aux passages qu'on coupe/retire) — retirés eux aussi.

Réutilise le moteur générique de montage_v2.py (silences coupés automatiquement, rendu des
plans, audio) : on remplace juste sa liste BLOCKS et le calque graphique.
Usage : python3 montage_v3.py → out/ep01_montage_v3.mp4
"""
import os
import subprocess

from PIL import Image, ImageDraw

import montage as v1
import montage_v2 as v2

OUT, TMP = v1.OUT, os.path.join(v1.OUT, "tmp_v3")
W, H, FPS = v1.W, v1.H, v1.FPS
FF, rush = v1.FF, v1.rush
LENS_PUNCH = v2.LENS_PUNCH

BLOCKS = [
    dict(nom="Accroche", audio=[("204549", 0.00, 2.85), ("210310", 2.15, 6.75)], inserts=[
        dict(de=("210310", 2.95), a=None, plans=[
            LENS_PUNCH,                        # flash : la main couvre l'objectif
            ("photo_thermo", 0, None, dict()),  # cut direct sur le thermomètre : 38,3 °C
        ])],
        subs=[("204549", 0.00, 0.96, "Fièvre chez votre bébé ?"),
              ("204549", 0.96, 2.85, "Ce n'est pas la dentition."),
              ("210310", 2.15, 4.18, "Piège 1 : croire aux dents."),
              ("210310", 4.18, 6.75, "Les dents ne donnent pas de forte fièvre.")]),
    dict(nom="Faux-ami", audio=[("210521", 0.00, 5.30)], inserts=[
        dict(de=("210521", 0.00), a=("210521", 0.85), plans=[("205853", 0.45, None, dict(badge=True))]),
        dict(de=("210521", 0.85), a=("210521", 2.40), plans=[("205947", 0.00, None, dict())]),  # la boîte, posée
        # (le clip 205947 devient noir/logo CapCut après ~1,7 s : on ne le laisse jamais dépasser)
    ], subs=[("210521", 0.00, 3.40, "Piège 3 : le paracétamol."),
             ("210521", 3.40, 5.30, "Il fait baisser la fièvre…")]),  # coupé avant « il ne soigne pas le palu »
    dict(nom="Urgence", audio=[("210140", 3.00, 8.95)], inserts=[
        dict(de=("210140", 3.00), a=("210140", 3.90), plans=[("204909", 0.95, None, dict(swipe=0))]),
    ], subs=[("210140", 3.00, 5.55, "Mais ton enfant convulse, vomit tout,"),
             ("210140", 5.55, 8.95, "fait la diarrhée : va aux urgences.")]),
    dict(nom="Délivrance", audio=[("205654", 0.00, 4.95), ("204549", 2.90, 4.75)], reveal=("205654", 2.50), inserts=[
        dict(de=("205654", 1.45), a=("205654", 4.95), plans=[
            ("210213", 1.75, 2.10, dict(whip_out=True)),   # balayage…
            ("210750", 0.00, 0.70, dict(whip_in=True)),    # …le TDR arrive
            ("210750", 5.00, None, dict()),                # gros plan TDR
        ])],
        subs=[("205654", 0.00, 1.40, "Le test le dit :"),
              ("205654", 1.40, 2.50, "le TDR."),
              ("205654", 2.50, 4.95, "Palu ou la goutte épaisse."),
              ("204549", 2.90, 4.75, "Pensez plutôt PALU.")]),
    dict(nom="Engagement", audio=[("205005", 0.00, 3.00), ("205005", 4.60, 7.35)], inserts=[],
         subs=[("205005", 0.00, 3.00, "Chez toi, on dit quoi quand le bébé chauffe ?"),
               ("205005", 4.60, 7.35, "Dis ça en commentaire.")]),
]

v2.BLOCKS = BLOCKS  # les fonctions génériques de montage_v2 (Timeline, plan_inserts, write_ass) lisent ce global


def build_overlay(path, tl, ev, reveal_t, reveal_end):
    badge = v1.label("PIÈGE N°3", 92, v1.WHITE, v1.RED, pad=38, radius=34)
    palu = v1.stack(v1.label("PALUDISME", 130, v1.WHITE, v1.RED, pad=42))
    alert = v1.stack(
        v1.label("Convulse, vomit tout,", 52, v1.WHITE, v1.DARK_T),
        v1.label("fait la diarrhée ?", 52, v1.WHITE, v1.DARK_T),
        v1.label("URGENCES.", 92, v1.WHITE, v1.RED, pad=36),
        gap=8,
    )
    swipe0 = sorted(ev["swipes"])[0] if ev["swipes"] else None

    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(round(tl.total * FPS)):
        t = i / FPS
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if ev["badge"] and ev["badge"][0] + 0.08 <= t < ev["badge"][1]:
            cx, cy = v1.src_xy(130, 520)
            v1.paste_center(L, badge, cx + 60, cy, scale=0.9 * v1.pop(t, ev["badge"][0] + 0.08, 0.2), angle=6)
        if swipe0:
            _, s0, s1 = swipe0
            a0 = s0 + 0.2
            block_end = tl.block_rng[2][1]  # fin du bloc « Urgence »
            if a0 <= t < block_end:
                v1.paste_center(L, alert, W / 2, 1080, scale=v1.pop(t, a0, 0.2))
        if reveal_t is not None and reveal_t <= t < reveal_end:
            v1.paste_center(L, palu, W / 2, 1060, scale=v1.pop(t, reveal_t, 0.15))
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


def main():
    os.makedirs(TMP, exist_ok=True)
    tl = v2.Timeline()
    ins, ev = v2.plan_inserts(tl)
    edl = v2.build_edl(tl, ins)
    print(f"Durée : {tl.total:.2f} s — {len(tl.spans)} morceaux de parole, {len(edl)} plans")
    ri = [i for i, b in enumerate(BLOCKS) if b.get("reveal")][0]
    reveal_t = tl.map(ri, *BLOCKS[ri]["reveal"])
    reveal_end = tl.block_rng[ri][1] + 0.5  # le bandeau ne doit pas suivre dans le bloc suivant (CTA)
    tdr_first = min((e[0] for e in edl if e[2] == "210750"), default=None)
    print(f"Révélation « PALU » à {reveal_t:.2f} s ; fin {tl.total:.2f} s → "
          f"{tl.total - reveal_t:.2f} s avant la fin")
    print(f"Ordre des blocs : {[b['nom'] for b in BLOCKS]}")
    for i, (s, e) in enumerate(tl.block_rng):
        print(f"  {BLOCKS[i]['nom']:12s} {s:6.2f}-{e:6.2f}")

    files = [v2.render(k, e) for k, e in enumerate(edl)]
    lst = os.path.join(TMP, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in files)
    base = os.path.join(TMP, "base.mp4")
    v1.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    overlay = os.path.join(TMP, "overlay.mov")
    build_overlay(overlay, tl, ev, reveal_t, reveal_end)
    ass = os.path.join(TMP, "subs.ass")
    v2.write_ass(ass, tl, (0, 0))  # pas de bandeau « checklist » à éviter : sous-titres en bas partout
    audio = os.path.join(TMP, "voix.wav")
    v2.build_audio(audio, tl, [], [], None)  # pas de bip, pas de whoosh, pas de choc

    dst = os.path.join(OUT, "ep01_montage_v3.mp4")
    fc = f"[0:v][1:v]overlay=0:0:format=auto,ass='{ass}',format=yuv420p[v]"
    v1.run([FF, "-y", "-i", base, "-i", overlay, "-i", audio, "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-shortest", dst])
    print("Export :", dst)


if __name__ == "__main__":
    main()
