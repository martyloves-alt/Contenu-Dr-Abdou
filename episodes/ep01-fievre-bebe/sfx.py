"""Habillage sonore de l'épisode 1, synthétisé (aucune banque de sons tierce, donc aucun droit à gérer).

build(cues, total, path_music, path_fx) écrit deux pistes WAV 48 kHz mono :
  - music : lits musicaux (tension, retour accéléré, ambiance neutre) — à « ducker » sous la voix ;
  - fx    : ponctuations (cœur, whoosh, tic-tac, sub drop, ding) — non duckées.
cues : dict de temps en secondes dans la vidéo FINALE (après accélération) :
  A = fin du cœur / whoosh / début musique de tension
  B = début du tic-tac
  D = sub drop : tension et tic-tac coupés net
  E = retour de la musique, rythme accéléré
  F = ding (révélation / validation)
  G = fin de tension, ambiance neutre jusqu'à la fin
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000


def _t(d):
    return np.arange(int(d * SR)) / SR


def _place(buf, sig, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += gain * sig


def _bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def _lp(x, f):
    return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)


def _fade(x, fi=0.02, fo=0.05):
    n = len(x)
    a, b = min(n, int(fi * SR)), min(n, int(fo * SR))
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[n - b:] *= np.linspace(1, 0, b)
    return x


def thump(f=52, d=0.28):
    t = _t(d)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.07) + 0.5 * np.sin(2 * np.pi * 2.1 * f * t) * np.exp(-t / 0.03))


def heartbeat(dur, bpm=138):
    out = np.zeros(int(dur * SR))
    period = 60 / bpm
    t = 0.0
    while t < dur:
        _place(out, thump(), t, 1.0)
        _place(out, thump(46), t + 0.17, 0.7)
        t += period
    return out


def whoosh(d=0.75):
    rng = np.random.default_rng(1)
    n = rng.standard_normal(int(d * SR))
    # balayage de bande 250 Hz → 5 kHz, enveloppe en cloche
    seg = 32
    out = np.zeros_like(n)
    L = len(n) // seg
    for k in range(seg):
        p = k / (seg - 1)
        fc = 250 * (20 ** p)
        sl = slice(k * L, (k + 1) * L if k < seg - 1 else len(n))
        out[sl] = _bp(n, max(60, fc * 0.6), min(SR / 2 - 100, fc * 1.6))[sl]
    env = np.sin(np.pi * np.linspace(0, 1, len(n))) ** 1.5
    return _lp(out * env, 9000)


def tick(f, d=0.035):
    t = _t(d)
    rng = np.random.default_rng(int(f))
    return (np.sin(2 * np.pi * f * t) + 0.4 * rng.standard_normal(len(t))) * np.exp(-t / 0.006)


def ticktock(dur, step=0.25):
    out = np.zeros(int(dur * SR))
    t, k = 0.0, 0
    while t < dur:
        _place(out, tick(2600 if k % 2 == 0 else 1900), t, 0.9 if k % 2 == 0 else 0.7)
        t += step
        k += 1
    return out


def sub_drop(d=1.6):
    t = _t(d)
    f = 28 + 72 * np.exp(-t / 0.35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    hit = np.random.default_rng(3).standard_normal(len(t)) * np.exp(-t / 0.02) * 0.25
    return (np.sin(ph) * np.exp(-t / 0.7) + _lp(hit, 900))


def ding(d=1.6):
    t = _t(d)
    parts = [(1568, 1.0, 0.55), (3136, 0.35, 0.25), (4704, 0.15, 0.12), (2093, 0.3, 0.4)]
    return sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau) for f, a, tau in parts) * (1 - np.exp(-t / 0.002))


def dark_bed(dur):
    """Tension sombre : drone grave dissonant + souffle filtré + montée (riser) sur 4 s."""
    t = _t(dur)
    drone = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 58.3 * t)
             + 0.35 * np.sin(2 * np.pi * 82.4 * t) + 0.2 * np.sin(2 * np.pi * 110 * t + np.sin(2 * np.pi * 0.3 * t)))
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * 1.1 * t)  # pulsation lente
    air = _bp(np.random.default_rng(5).standard_normal(len(t)), 300, 2200) * 0.25
    rise_d = min(4.0, dur)
    rt = _t(rise_d)
    f = 180 * (4 ** (rt / rise_d))
    riser = np.sin(2 * np.pi * np.cumsum(f) / SR) * (rt / rise_d) ** 2 * 0.5
    out = drone * 0.5 + air
    out[: len(riser)] += riser
    env = np.minimum(1, t / 1.2)
    return _fade(out * env, 0.05, 0.01)


def driving_bed(dur, bpm=150):
    """Retour de la musique, rythme accéléré : drone + basse pulsée en croches + charley."""
    t = _t(dur)
    out = 0.35 * (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t))
    step = 60 / bpm / 2
    notes = [55, 55, 65.4, 55, 73.4, 55, 65.4, 49]
    k, s = 0, 0.0
    while s < dur:
        d = step * 0.9
        tt = _t(d)
        f = notes[k % len(notes)]
        _place(out, np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.12) * 0.9, s)
        _place(out, _bp(np.random.default_rng(k).standard_normal(len(tt)), 6000, 12000) * np.exp(-tt / 0.02) * 0.25, s)
        s += step
        k += 1
    return _fade(out * np.minimum(1, t / 0.3), 0.05, 0.4)


def neutral_bed(dur):
    """Fin de tension : nappe douce en accord majeur."""
    t = _t(dur)
    chord = [130.8, 164.8, 196.0, 261.6]
    out = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)) for f in chord) / len(chord)
    return _fade(out * np.minimum(1, t / 0.8), 0.05, min(1.0, dur / 3))


def build(cues, total, path_music, path_fx):
    A, B, D, E, F, G = (cues[k] for k in "ABDEFG")
    music = np.zeros(int(total * SR))
    fx = np.zeros(int(total * SR))
    _place(fx, heartbeat(A), 0.0, 0.55)
    _place(fx, whoosh(), A - 0.35, 0.45)
    _place(music, dark_bed(D - A), A, 0.30)
    _place(fx, ticktock(D - B), B, 0.22)
    _place(fx, sub_drop(), D, 0.75)
    _place(music, driving_bed(G - E), E, 0.28)
    _place(fx, ding(), F, 0.30)
    _place(music, neutral_bed(total - G), G, 0.20)
    for x, p in ((music, path_music), (fx, path_fx)):
        x = np.clip(x, -1, 1)
        wavfile.write(p, SR, (x * 32767).astype(np.int16))
