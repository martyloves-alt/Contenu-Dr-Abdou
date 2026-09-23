"""Montage v2 de l'épisode 1 : mécanique « Zach King » (choc physique, mystère, match cuts, jump cuts).

Usage : python3 montage_v2.py → out/ep01_montage_v2.mp4 (1080x1920, 30 i/s)

Règles appliquées (retour d'Abdou sur la v1) :
  - « palu »/« paludisme » ni dit ni affiché avant les 5 dernières secondes : le mot est masqué
    par un bip (« le ??? ») jusqu'à la révélation ; le TDR n'apparaît qu'à la fin ;
  - accroche physique : la main s'arrache de l'objectif, la boîte de paracétamol est lancée hors cadre ;
  - transitions sur le mouvement (main → écran noir → thermomètre, balayage → TDR) ;
  - chaque respiration / hésitation coupée (détection automatique des silences) ;
  - voix naturelle (pas d'effet de voix grave), sous-titres = mots réellement prononcés.
Réutilise les rushes d'origine uniquement (aucun nouveau tournage, aucune génération IA).
"""
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import montage as v1  # rendu des plans, calque, polices, recadrage anti-filigrane

HERE = v1.HERE
OUT, TMP = v1.OUT, os.path.join(v1.OUT, "tmp_v2")
W, H, FPS = v1.W, v1.H, v1.FPS
FF, rush, CROP = v1.FF, v1.rush, v1.CROP


def snap(t):
    return round(t * FPS) / FPS


# ---------------------------------------------------------------------------------------
# Blocs de parole. audio = (prise, début, fin) ; bleeps = zones où « palu » est masqué ;
# inserts = plans de coupe posés sur la parole, ancrés sur un instant de la prise parlée.
# pièce d'insert : (prise, début, fin|None, options) — fin None = durée ajustée (flex).
# ---------------------------------------------------------------------------------------
BLOCKS = [
    dict(nom="Accroche", audio=[("210605", 0.20, 3.70)], inserts=[
        dict(de=("210605", 0.20), a=("210605", 2.70), plans=[
            ("204725", 2.30, 3.07, dict(speed=1.6)),            # la main s'arrache de l'objectif
            ("205559", 0.70, None, dict()),                      # il saisit la boîte
            ("205117", 0.05, 1.30, dict(speed=1.6, whoosh=True)),  # et la lance hors du cadre
        ])],
        subs=[("210605", 0.24, 1.25, "Le piège numéro 3,"),
              ("210605", 1.30, 3.70, "beaucoup de parents font ça chaque soir.")]),
    dict(nom="Dents", audio=[("204549", 0.00, 2.85)], inserts=[],
         subs=[("204549", 0.00, 0.96, "Fièvre chez votre bébé ?"),
               ("204549", 0.96, 2.85, "Ce n'est pas la dentition.")]),
    dict(nom="Piège 1", audio=[("210310", 2.15, 6.75)], inserts=[
        dict(de=("210310", 2.95), a=None, plans=[
            ("204725", 0.90, 1.60, dict()),                      # la main couvre l'objectif → noir
            ("205741", 0.30, None, dict(speed=1.6, colorfix=True)),  # recul depuis le noir : thermomètre
            ("photo_thermo", 0, 0.60, dict()),                   # zoom 38,3 °C
        ])],
        subs=[("210310", 2.15, 4.18, "Piège 1 : croire aux dents."),
              ("210310", 4.18, 6.75, "Les dents ne donnent pas de forte fièvre.")]),
    dict(nom="Piège 2", audio=[("210713", 0.15, 10.90)], bleeps=[("210713", 3.84, 4.25), ("210713", 6.40, 6.74)],
         inserts=[], chrono=("210713", 7.30),
         subs=[("210713", 0.15, 2.64, "Au Bénin, quand un enfant fait la fièvre,"),
               ("210713", 2.64, 4.60, "on cherche d'abord le ???"),
               ("210713", 5.60, 8.10, "Et si le ??? n'est pas traité dans les 24 heures,"),
               ("210713", 8.10, 10.90, "ça peut s'aggraver.")]),
    dict(nom="Piège 3", audio=[("210521", 0.00, 7.55)], bleeps=[("210521", 6.78, 7.55)], inserts=[
        dict(de=("210521", 0.00), a=("210521", 0.85), plans=[("205853", 0.45, None, dict(badge=True))]),
        dict(de=("210521", 0.85), a=("210521", 3.40), plans=[("205947", 0.00, None, dict())]),
        dict(de=("210521", 6.60), a=None, plans=[
            ("204815", 0.40, 0.95, dict()),                      # il attrape en l'air et plaque
            ("still_205947", 1.75, None, dict(bar=True)),        # barre rouge plaquée + choc
        ])],
        subs=[("210521", 0.00, 3.40, "Piège 3 : le paracétamol."),
              ("210521", 3.40, 5.32, "Il fait baisser la fièvre,"),
              ("210521", 5.32, 7.55, "il ne soigne pas le ???")]),
    dict(nom="Action", audio=[("210140", 0.00, 8.95)], checklist=True, inserts=[
        dict(de=("210140", 0.00), a=None, plans=[("204909", 0.95, 1.80, dict(swipe=0))]),
        dict(de=("210140", 3.50), a=None, plans=[("204909", 4.55, 5.30, dict(swipe=1))]),
        dict(de=("210140", 6.10), a=None, plans=[("204909", 10.85, 11.55, dict(swipe=2))]),
    ], subs=[("210140", 0.00, 2.60, "Ton enfant fait la fièvre ? Test au centre de santé."),
             ("210140", 2.60, 5.55, "Mais ton enfant convulse, vomit tout,"),
             ("210140", 5.55, 8.95, "fait la diarrhée, va aux urgences.")]),
    dict(nom="Appel à l'action", audio=[("205005", 0.00, 7.35)], inserts=[],
         subs=[("205005", 0.00, 3.00, "Chez toi, on dit quoi quand le bébé chauffe ?"),
               ("205005", 3.00, 7.35, "Dis ça en commentaire.")]),
    dict(nom="Révélation", audio=[("205654", 0.00, 4.95), ("204549", 2.90, 4.75)], reveal=("205654", 2.50), inserts=[
        dict(de=("205654", 1.45), a=("205654", 4.95), plans=[
            ("210213", 1.75, 2.10, dict(whip_out=True)),         # balayage…
            ("210750", 0.00, 0.70, dict(whip_in=True)),          # …le TDR arrive par la droite
            ("210750", 5.00, None, dict()),                      # gros plan TDR
        ]),
    ], subs=[("205654", 0.00, 1.40, "Le test le dit :"),
             ("205654", 1.40, 2.50, "le TDR."),
             ("205654", 2.50, 4.95, "Palu ou la goutte épaisse."),
             ("204549", 2.90, 4.75, "Pensez plutôt PALU.")]),
]


# ---------------------------------------------------------------------------------------
# Détection de la parole (coupe des respirations / hésitations)
# ---------------------------------------------------------------------------------------
def load_audio(clip, a, b, sr=16000):
    r = subprocess.run([FF, "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", rush(clip),
                        "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], stdout=subprocess.PIPE)
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768, sr


def speech_spans(clip, a, b, min_gap=0.12, pad=0.05):
    y, sr = load_audio(clip, a, b)
    hop = int(sr * 0.01)
    n = len(y) // hop
    db = 20 * np.log10(np.sqrt(np.mean(y[: n * hop].reshape(n, hop) ** 2, 1)) + 1e-6)
    thr = max(np.percentile(db, 10) + 9, db.max() - 36)
    on = db > thr
    spans, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            spans.append([i * 0.01, j * 0.01])
            i = j
        else:
            i += 1
    spans = [s for s in spans if s[1] - s[0] >= 0.05]
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] < min_gap:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    out = []
    for s0, s1 in merged:
        s0, s1 = snap(max(0, s0 - pad) + a), snap(min(b - a, s1 + pad) + a)
        if out and s0 <= out[-1][1]:
            out[-1][1] = s1
        elif s1 - s0 >= 2 / FPS:
            out.append([s0, s1])
    return out


# ---------------------------------------------------------------------------------------
# Construction de la ligne de temps
# ---------------------------------------------------------------------------------------
class Timeline:
    def __init__(self):
        self.spans = []  # (bloc, prise, s0, s1, t0)
        self.block_rng = []
        t = 0.0
        for bi, blk in enumerate(BLOCKS):
            t_start = t
            for clip, a, b in blk["audio"]:
                for s0, s1 in speech_spans(clip, a, b):
                    self.spans.append((bi, clip, s0, s1, t))
                    t = snap(t + s1 - s0)
            self.block_rng.append((t_start, t))
        self.total = t

    def map(self, bi, clip, ts):
        """Instant de la prise parlée → instant de sortie (si dans une coupe : début du morceau suivant)."""
        cands = [s for s in self.spans if s[0] == bi and s[1] == clip]
        for _, _, s0, s1, t0 in cands:
            if ts <= s1:
                return snap(t0 + max(0, ts - s0))
        _, _, s0, s1, t0 = cands[-1]
        return snap(t0 + s1 - s0)

    def ranges(self, bi, clip, a, b):
        """Parties conservées d'un intervalle de la prise → intervalles de sortie."""
        out = []
        for sb, c, s0, s1, t0 in self.spans:
            if sb == bi and c == clip:
                x0, x1 = max(a, s0), min(b, s1)
                if x1 > x0:
                    out.append((snap(t0 + x0 - s0), snap(t0 + x1 - s0)))
        return out


def plan_inserts(tl):
    """Retourne les inserts à la seconde près : (t0, t1, prise, src0, options)."""
    ins, events = [], dict(swipes=[], bar=None, badge=None, whoosh=[])
    for bi, blk in enumerate(BLOCKS):
        b_end = tl.block_rng[bi][1]
        for it in blk["inserts"]:
            t0 = tl.map(bi, *it["de"])
            t1 = tl.map(bi, *it["a"]) if it["a"] else b_end
            dur_of = lambda p: 0.0 if p[2] is None else (p[2] - p[1]) / p[3].get("speed", 1)
            fixed = sum(dur_of(p) for p in it["plans"])
            flex = [p for p in it["plans"] if p[2] is None]
            avail = t1 - t0
            if not flex:
                avail = min(avail, fixed) if it["a"] is None else avail
            spare = max(0.0, avail - fixed)
            t = t0
            for p in it["plans"]:
                clip, a, b, o = p
                d = spare / len(flex) if b is None else dur_of(p)
                d = snap(min(d, t0 + avail - t))
                if d < 1 / FPS:
                    continue
                ins.append((t, t + d, clip, a, o))
                if o.get("swipe") is not None:
                    events["swipes"].append((o["swipe"], t, t + d))
                if o.get("bar"):
                    events["bar"] = (t, t + d)
                if o.get("badge"):
                    events["badge"] = (t, t + d)
                if o.get("whoosh"):
                    events["whoosh"].append(t)
                t = snap(t + d)
    return ins, events


def build_edl(tl, ins):
    """Plans face caméra (synchro labiale, zoom alterné à chaque jump cut) remplacés par les inserts."""
    base, k_prev = [], None
    for k, (bi, clip, s0, s1, t0) in enumerate(tl.spans):
        k = 0 if k_prev != bi else k + 0
        zoom = 1.0 if len([b for b in base if b[5] == bi]) % 2 == 0 else 1.1
        base.append((t0, snap(t0 + s1 - s0), clip, s0, dict(zoom=zoom), bi))
        k_prev = bi
    cuts = sorted({0.0, tl.total, *[x for b in base for x in b[:2]], *[x for i in ins for x in i[:2]]})
    edl = []
    for c0, c1 in zip(cuts, cuts[1:]):
        if c1 - c0 < 0.5 / FPS:
            continue
        mid = (c0 + c1) / 2
        hit = [i for i in ins if i[0] <= mid < i[1]]
        if hit:
            t0, t1, clip, a, o = hit[0]
            sp = o.get("speed", 1)
            edl.append((c0, c1, clip, a + (c0 - t0) * sp, o, (t0, t1)))
        else:
            b = [x for x in base if x[0] <= mid < x[1]][0]
            edl.append((c0, c1, b[2], b[3] + (c0 - b[0]), b[4], (b[0], b[1])))
    # fusionne les morceaux contigus d'un même plan
    merged = []
    for e in edl:
        if merged and merged[-1][2] == e[2] and merged[-1][5] == e[5] and abs(merged[-1][1] - e[0]) < 1e-6:
            m = merged[-1]
            merged[-1] = (m[0], e[1], m[2], m[3], m[4], m[5])
        else:
            merged.append(e)
    return merged


def render(k, e):
    t0, t1, clip, a, o, rng = e
    dur = t1 - t0
    n = round(dur * FPS)
    out = os.path.join(TMP, f"e{k:03d}.mp4")
    if clip == "photo_thermo":
        return v1.photo_zoom(out, dur)
    if clip.startswith("still_"):
        return v1.still_impact(out, clip[6:], a, dur)
    sp = o.get("speed", 1)
    vf = []
    if o.get("colorfix"):
        vf.append(v1.COLORFIX)
    vf.append(CROP)
    if sp != 1:
        vf.insert(0, f"setpts=PTS/{sp}")
    z = o.get("zoom", 1.0)
    if z != 1.0:
        vf.append(f"scale={round(W * z / 2) * 2}:{round(H * z / 2) * 2},crop={W}:{H}")
    # flou de balayage sur les 3 dernières / premières images du plan d'insert
    if o.get("whip_out") and abs(t1 - rng[1]) < 1e-6:
        vf.append(f"gblur=sigma=45:sigmaV=0.01:enable='gte(t,{dur - 0.1:.3f})'")
    if o.get("whip_in") and abs(t0 - rng[0]) < 1e-6:
        vf.append("gblur=sigma=45:sigmaV=0.01:enable='lt(t,0.1)'")
    if o.get("whoosh"):  # tremblement pendant le lancer
        vf.append(f"scale={W + 40}:{H + 72},crop={W}:{H}:x='20+14*sin(t*55)':y='36+10*cos(t*47)'")
    vf.append(f"fps={FPS},format=yuv420p")
    v1.run([FF, "-y", "-ss", f"{a:.3f}", "-i", rush(clip), "-frames:v", str(n), "-vf", ",".join(vf),
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", out])
    return out


# ---------------------------------------------------------------------------------------
# Calque graphique
# ---------------------------------------------------------------------------------------
def build_overlay(path, tl, ev, bleeps_out, chrono_rng, reveal_t, chk_end):
    badge = v1.label("PIÈGE N°3", 92, v1.WHITE, v1.RED, pad=38, radius=34)
    qmark = v1.label("?", 150, v1.WHITE, v1.RED, pad=30, radius=90)
    palu = v1.stack(v1.label("PALUDISME", 130, v1.WHITE, v1.RED, pad=42))
    rows, rx = v1.checklist_rows()
    chk_y = [1000]
    for r in rows[:-1]:
        chk_y.append(chk_y[-1] + r.height + 16)
    over = chk_y[-1] + rows[-1].height - 1400
    chk_y = [y - max(0, over) for y in chk_y]
    swipes = sorted(ev["swipes"])

    p = subprocess.Popen([FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", path],
                         stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(round(tl.total * FPS)):
        t = i / FPS
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if ev["badge"] and ev["badge"][0] + 0.08 <= t < ev["badge"][1]:
            cx, cy = v1.src_xy(130, 520)
            L_s = v1.pop(t, ev["badge"][0] + 0.08, 0.2)
            v1.paste_center(L, badge, cx + 60, cy, scale=0.9 * L_s, angle=6)
        for b0, b1 in bleeps_out:  # b1 inclut déjà la traîne, bornée à la fin du bloc
            if b0 <= t < b1:
                v1.paste_center(L, qmark, W / 2, 1020, scale=v1.pop(t, b0, 0.15))
        if chrono_rng and chrono_rng[0] <= t < chrono_rng[1]:
            c0, c1 = chrono_rng
            v1.paste_center(L, v1.chrono_frame((t - c0) / (c1 - c0)), W / 2, 1000, scale=v1.pop(t, c0))
        if ev["bar"] and ev["bar"][0] <= t < ev["bar"][1]:
            L.alpha_composite(v1.red_bar(min(1, (t - ev["bar"][0]) / 0.1)))
        for k, s0, s1 in swipes:
            a0 = s0 + 0.2
            if a0 <= t < chk_end:
                q = min(1, (t - a0) / max(0.2, (s1 - a0)))
                row = rows[k]
                L.alpha_composite(row.crop((0, 0, max(1, round(row.width * q)), row.height)), (rx, chk_y[k]))
        if reveal_t is not None and t >= reveal_t:
            sh = 10 * math.exp(-(t - reveal_t) * 9) * math.sin((t - reveal_t) * 70)
            v1.paste_center(L, palu, W / 2 + sh, 1060, scale=v1.pop(t, reveal_t, 0.15))
        p.stdin.write(L.tobytes())
    p.stdin.close()
    p.wait()


def write_ass(path, tl, chk_rng):
    head = open_head()
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for bi, blk in enumerate(BLOCKS):
            for clip, a, b, txt in blk["subs"]:
                rr = tl.ranges(bi, clip, a, b)
                if not rr:
                    continue
                s, e = rr[0][0], rr[-1][1]
                top = chk_rng[0] - 0.01 <= s < chk_rng[1]
                txt = txt.replace(" ?", "\\h?").replace(" :", "\\h:")
                f.write(f"Dialogue: 0,{v1.ass_time(s)},{v1.ass_time(e)},{'SubTop' if top else 'Sub'},,0,0,0,,{txt}\n")


def open_head():
    return """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,DejaVu Sans,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,2,80,140,420,1
Style: SubTop,DejaVu Sans,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,2,8,80,140,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


# ---------------------------------------------------------------------------------------
# Audio : voix naturelle nettoyée (pas d'effet grave) + bips + bruitages
# ---------------------------------------------------------------------------------------
VOICE_FX = ",".join([
    "highpass=f=80",
    "afftdn=nf=-30",
    "equalizer=f=380:t=q:w=1.2:g=-2",
    "equalizer=f=3000:t=o:w=1.5:g=5",
    "treble=g=3:f=6000",
    "deesser",
    "acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=2",
    "loudnorm=I=-14:TP=-1.5:LRA=9",
])


def build_audio(path, tl, bleeps_out, whooshes, thud_t):
    inputs, chains = [], []
    for k, (bi, clip, s0, s1, t0) in enumerate(tl.spans):
        d = s1 - s0
        inputs += ["-ss", f"{s0:.3f}", "-t", f"{d:.3f}", "-i", rush(clip)]
        chains.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=mono,afade=t=in:d=0.012,"
                      f"afade=t=out:st={max(0, d - 0.015):.3f}:d=0.015[a{k}]")
    n = len(tl.spans)
    cat = "".join(f"[a{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1,{VOICE_FX}"
    mute = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in bleeps_out) or "0"
    fc = ";".join(chains) + f";{cat},volume=0:enable='{mute}'[voice]"
    bleep = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in bleeps_out) or "0"
    fc += f";aevalsrc='0.18*sin(2*PI*1000*t)*({bleep})':s=48000:d={tl.total:.3f}[bip]"
    mix = ["[voice]", "[bip]"]
    for j, t in enumerate(whooshes):
        fc += (f";anoisesrc=d=0.4:c=pink:a=0.6:r=48000,highpass=f=700,lowpass=f=6000,"
               f"afade=t=in:d=0.18,afade=t=out:st=0.18:d=0.22,adelay={int(t * 1000)}[w{j}]")
        mix.append(f"[w{j}]")
    if thud_t is not None:
        fc += f";aevalsrc='0.9*sin(2*PI*58*t)*exp(-14*t)':s=48000:d=0.4,adelay={int(thud_t * 1000)}[thud]"
        mix.append("[thud]")
    fc += f";{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.89[out]"
    v1.run([FF, "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2", path])


def main():
    os.makedirs(TMP, exist_ok=True)
    tl = Timeline()
    ins, ev = plan_inserts(tl)
    edl = build_edl(tl, ins)
    print(f"Durée : {tl.total:.2f} s — {len(tl.spans)} morceaux de parole, {len(edl)} plans")

    bleeps_out = []
    for bi, blk in enumerate(BLOCKS):
        for clip, a, b in blk.get("bleeps", []):
            bleeps_out += tl.ranges(bi, clip, a, b)
    chrono = None
    for bi, blk in enumerate(BLOCKS):
        if blk.get("chrono"):
            chrono = (tl.map(bi, *blk["chrono"]), tl.block_rng[bi][1])
    ri = [i for i, b in enumerate(BLOCKS) if b.get("reveal")][0]
    reveal_t = tl.map(ri, *BLOCKS[ri]["reveal"])
    ci = [i for i, b in enumerate(BLOCKS) if b.get("checklist")][0]
    last_line = max(s0 for k, s0, s1 in ev["swipes"]) + 0.2 + 0.5
    chk_rng = (tl.block_rng[ci][0], max(tl.block_rng[ci][1], last_line + 3.0))
    tdr_first = min(e[0] for e in edl if e[2] == "210750")
    print(f"Révélation « PALU » à {reveal_t:.2f} s ; TDR à l'écran dès {tdr_first:.2f} s ; "
          f"fin {tl.total:.2f} s → {tl.total - min(reveal_t, tdr_first):.2f} s avant la fin")
    print(f"Checklist complète tenue {chk_rng[1] - last_line:.2f} s")

    files = [render(k, e) for k, e in enumerate(edl)]
    lst = os.path.join(TMP, "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{x}'\n" for x in files)
    base = os.path.join(TMP, "base.mp4")
    v1.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    overlay = os.path.join(TMP, "overlay.mov")
    marks = [(a, min(b + 0.25, next(e for s, e in tl.block_rng if s <= a < e))) for a, b in bleeps_out]
    build_overlay(overlay, tl, ev, marks, chrono, reveal_t, chk_rng[1])
    ass = os.path.join(TMP, "subs.ass")
    write_ass(ass, tl, chk_rng)
    audio = os.path.join(TMP, "voix.wav")
    build_audio(audio, tl, bleeps_out, ev["whoosh"], ev["bar"][0] if ev["bar"] else None)

    dst = os.path.join(OUT, "ep01_montage_v2.mp4")
    fc = f"[0:v][1:v]overlay=0:0:format=auto,ass='{ass}',format=yuv420p[v]"
    v1.run([FF, "-y", "-i", base, "-i", overlay, "-i", audio, "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "-shortest", dst])
    print("Export :", dst)


if __name__ == "__main__":
    main()
