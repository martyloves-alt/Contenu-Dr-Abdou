"""Assemble l'épisode 1 (45 s, 9:16) à partir des assets d'Abdou + graphiques de make_graphics.py.

Usage :
  python3 build.py                 # brouillon 1080x1920 30 fps (out/ep01_brouillon.mp4)
  python3 build.py --final --lufs <cible>   # 2160x3840 60 fps, loudnorm à la cible donnée

Un asset absent est remplacé par un carton « ASSET MANQUANT » : rien n'est inventé ni généré.
Les timings des sous-titres sont provisoires tant que la voix d'Abdou n'est pas là :
ils devront être recalés sur l'audio réel.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
GFX = os.path.join(HERE, "graphics")
OUT = os.path.join(HERE, "out")
DURATION = 45.0


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


FFMPEG = ffmpeg_bin()

# --- Sous-titres : texte mot pour mot du script validé ---------------------------------
SUBS = [
    (0.0, 1.6, "Fièvre chez bébé ? Ce n'est pas les dents."),
    (1.6, 3.0, "Pense palu."),
    (3.0, 3.8, "Et le piège n°3,"),
    (3.8, 5.0, "beaucoup de parents le font chaque soir."),
    (5.0, 7.0, "Piège 1 : croire aux dents."),
    (7.0, 9.8, "Les dents ne donnent pas de forte fièvre."),
    (9.8, 11.5, "Piège 2 : attendre."),
    (11.5, 14.4, "Au Bénin, un enfant fiévreux, on cherche d'abord le palu."),
    (14.4, 18.2, "Sans traitement, en 24 heures, il peut devenir grave."),
    (18.2, 20.0, "Piège 3 : le paracétamol."),
    (20.0, 22.4, "Il fait baisser la fièvre."),
    (22.4, 24.8, "Il ne soigne pas le palu."),
    (24.8, 27.6, "Seul un test le dit : le TDR."),
    (27.6, 29.8, "Une goutte de sang."),
    (29.8, 32.0, "15 à 20 minutes."),
    (32.0, 34.6, "Fièvre ? Test au centre de santé dans les 24 heures."),
    (34.6, 35.8, "Convulsions, ne tète plus, vomit tout, dort trop ?"),
    (35.8, 37.0, "Urgences. Tout de suite."),
    (37.0, 40.0, "Moins de 3 mois ? Urgences."),
    (40.0, 42.5, "Chez toi, on dit quoi quand bébé est chaud ?"),
    (42.5, 45.0, "Écris un seul mot en commentaire."),
]

# --- Plans de fond (vidéo) ---------------------------------------------------------------
# (début, fin, asset, zoom rapide ?)
SHOTS = [
    (0.0, 5.0, "talking-head-hook", False),
    (5.0, 9.8, "thermometre", True),
    (9.8, 18.2, None, False),  # Piège 2 : aucun asset prévu au script → fond uni + chrono
    (18.2, 24.8, "paracetamol-boite", False),
    (24.8, 32.0, "tdr", False),
    (32.0, 40.0, None, False),  # checklist sur fond uni
    (40.0, 45.0, "talking-head-hook", False),
]

# --- Overlays graphiques (PNG plein cadre, transparents) --------------------------------
OVERLAYS = [
    (0.0, 1.6, "hook_1_faux.png"),
    (1.6, 3.0, "hook_2_paludisme.png"),  # PALUDISME visible dès 1,6 s (< 3 s)
    (3.0, 5.0, "badge_piege3.png"),
    (22.4, 24.8, "barre_paracetamol.png"),
    (32.0, 34.6, "checklist_1.png"),
    (34.6, 37.0, "checklist_2.png"),
    (37.0, 40.0, "checklist_3.png"),  # checklist complète maintenue 3 s
]
CHRONO = (14.4, 18.2)


def find_asset(stem):
    for ext in ("mp4", "mov", "jpg", "jpeg", "png"):
        p = os.path.join(ASSETS, f"{stem}.{ext}")
        if os.path.exists(p):
            return p
    return None


def run(cmd):
    print("+", " ".join(cmd[:3]), "…", cmd[-1])
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def probe_duration(path):
    r = subprocess.run([FFMPEG, "-i", path], stderr=subprocess.PIPE, text=True)
    for line in r.stderr.splitlines():
        if "Duration:" in line:
            h, m, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return None


def fill(w, h):
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"


def render_shot(i, start, end, stem, zoom, w, h, fps, cta_start, missing):
    dur = end - start
    out = os.path.join(OUT, "tmp", f"shot{i:02d}.mp4")
    src = find_asset(stem) if stem else os.path.join(GFX, "fond.png")
    if stem and not src:
        missing.add(stem)
        src = os.path.join(GFX, f"manquant_{stem}.png")
    is_still = src.lower().endswith((".jpg", ".jpeg", ".png"))
    vf = fill(w, h)
    if zoom:  # « zoom rapide » : 1 → 1,25 en 0,6 s puis tenu
        n = int(0.6 * fps)
        vf += f",zoompan=z='min(1+0.25*on/{n},1.25)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={w}x{h}:fps={fps}"
    vf += f",fps={fps},format=yuv420p"
    inp = ["-loop", "1", "-t", f"{dur}", "-i", src] if is_still else []
    if not is_still:
        ss = 0.0
        if stem == "talking-head-hook" and start >= 40.0:
            ss = cta_start if cta_start is not None else max(0.0, (probe_duration(src) or dur) - dur)
        inp = ["-ss", f"{ss}", "-t", f"{dur}", "-i", src]
    run([FFMPEG, "-y", *inp, "-vf", vf, "-an", "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])
    return out


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
Style: Sub,DejaVu Sans,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,150,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head)
        for s, e, txt in SUBS:
            txt = txt.replace(" ?", "\\h?").replace(" :", "\\h:")  # typo française : pas de « ? » seul en début de ligne
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Sub,,0,0,0,,{txt}\n")


def build_audio(path, lufs, cta_start):
    """Voix : talking-head (0–5 s, 40–45 s) + voix-corps (5–40 s). Silence si absent."""
    th = find_asset("talking-head-hook")
    body = next((p for p in glob.glob(os.path.join(ASSETS, "voix-corps.*"))), None)
    inputs, parts = ["-f", "lavfi", "-t", f"{DURATION}", "-i", "anullsrc=r=48000:cl=stereo"], ["[0:a]"]
    k = 1
    if th and th.lower().endswith((".mp4", ".mov")):
        cta = cta_start if cta_start is not None else max(0.0, (probe_duration(th) or 5) - 5)
        inputs += ["-t", "5", "-i", th, "-ss", f"{cta}", "-t", "5", "-i", th]
        parts += [f"[{k}:a]adelay=0|0[a{k}]", f"[{k+1}:a]adelay=40000|40000[a{k+1}]"]
        k += 2
    if body:
        inputs += ["-t", "35", "-i", body]
        parts += [f"[{k}:a]aresample=48000,adelay=5000|5000[a{k}]"]
        k += 1
    labels = "[0:a]" + "".join(f"[a{j}]" for j in range(1, k))
    chains = ";".join(parts[1:])
    mix = f"{labels}amix=inputs={k}:duration=first:normalize=0"
    if lufs is not None:
        mix += f",loudnorm=I={lufs}:TP=-1.5:LRA=11"
    fc = (chains + ";" if chains else "") + mix + "[out]"
    run([FFMPEG, "-y", *inputs, "-filter_complex", fc, "-map", "[out]", "-t", f"{DURATION}", "-c:a", "aac", "-b:a", "256k", path])
    return bool(th) or bool(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="4K 60 fps")
    ap.add_argument("--lufs", type=float, help="cible loudnorm (paramètre du pipeline Creatomate/Make — à fournir par Abdou)")
    ap.add_argument("--cta-start", type=float, help="seconde du talking-head où commence l'appel à l'action (40–45 s)")
    a = ap.parse_args()
    if a.final and a.lufs is None:
        sys.exit("--final exige --lufs (valeur du pipeline existant, à demander à Abdou).")

    w, h, fps = (2160, 3840, 60) if a.final else (1080, 1920, 30)
    os.makedirs(os.path.join(OUT, "tmp"), exist_ok=True)
    missing = set()

    shots = [render_shot(i, *s, w, h, fps, a.cta_start, missing) for i, s in enumerate(SHOTS)]
    lst = os.path.join(OUT, "tmp", "concat.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in shots)
    base = os.path.join(OUT, "tmp", "base.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    ass = os.path.join(OUT, "tmp", "subs.ass")
    write_ass(ass)

    # overlays + chrono + sous-titres
    inputs = ["-i", base]
    fc, last = [], "[0:v]"
    for j, (s, e, png) in enumerate(OVERLAYS, start=1):
        inputs += ["-i", os.path.join(GFX, png)]
        fc.append(f"[{j}:v]scale={w}:{h}[g{j}]")
        fc.append(f"{last}[g{j}]overlay=0:0:enable='between(t,{s},{e})'[v{j}]")
        last = f"[v{j}]"
    j = len(OVERLAYS) + 1
    cs, ce = CHRONO
    n_frames = len(glob.glob(os.path.join(GFX, "chrono", "f*.png")))
    inputs += ["-framerate", f"{n_frames / (ce - cs):.4f}", "-i", os.path.join(GFX, "chrono", "f%04d.png")]
    fc.append(f"[{j}:v]scale={w}:{h},fps={fps},setpts=PTS+{cs}/TB[ch]")
    fc.append(f"{last}[ch]overlay=0:0:eof_action=pass:enable='between(t,{cs},{ce})'[vc]")
    fc.append(f"[vc]ass='{ass}'[vout]")

    audio = os.path.join(OUT, "tmp", "audio.m4a")
    has_voice = build_audio(audio, a.lufs, a.cta_start)
    inputs += ["-i", audio]

    name = "ep01_final_4k60.mp4" if a.final else "ep01_brouillon.mp4"
    dst = os.path.join(OUT, name)
    run([FFMPEG, "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", f"{j + 1}:a",
         "-t", f"{DURATION}", "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", dst])

    print("\nExport :", dst)
    if missing:
        print("Assets manquants (cartons à la place) :", ", ".join(sorted(missing)))
    if not has_voice:
        print("Aucune voix fournie : piste audio silencieuse.")


if __name__ == "__main__":
    main()
