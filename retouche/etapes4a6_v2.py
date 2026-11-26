"""Étapes 4 à 6 : retouche commune, agrandissement x2, version B (fond studio), exports.
Entrées : output/etapes/03_inpaint_modele.png (version A nettoyée), output/etapes/02_masque_final.png
Ordre réel : la retouche (étape 5) est faite une seule fois sur l'image nettoyée ; les pixels du sujet
sont donc strictement identiques entre A et B. B = sujet retouché + fond dégradé généré."""
import cv2, numpy as np, os, sys
E = 'output/etapes'; O = 'output/v2'
SCR = sys.argv[1] if len(sys.argv) > 1 else None   # dossier contenant weights/RealESRGAN_x2plus.pth
base = cv2.imread(f'{E}/03_inpaint_modele_v2.png')
alpha = cv2.imread(f'{E}/02_masque_final.png', 0).astype(np.float32) / 255
H, W = alpha.shape

def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

# ---------- ÉTAPE 5a : balance des blancs ciblée sur les blancs/gris (t-shirt) ----------
def balance(img):
    hsv = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    S, V = hsv[..., 1], hsv[..., 2]
    t = (alpha > 0.8) & (S < 70) & (V > 140); t[:300] = False; t[620:] = False
    # courbe par canal : pour chaque tranche de luminosité, ramener la moyenne B,G,R au gris commun
    pts = {c: [(0, 0)] for c in range(3)}
    for lo, hi in ((140, 200), (200, 225), (225, 245), (245, 254)):
        m = t & (V >= lo) & (V < hi)
        if m.sum() < 500: continue
        mu = img[m].astype(np.float32).mean(0); g = mu.mean()
        for c in range(3): pts[c].append((mu[c], g))
    lut = np.zeros((3, 256), np.float32); x = np.arange(256)
    for c in range(3):
        p = sorted(pts[c] + [(255, 255)]); lut[c] = np.interp(x, [a for a, _ in p], [b for _, b in p])
    corr = np.stack([lut[c][img[..., c].astype(np.uint8)] for c in range(3)], -1)
    # poids : seulement les pixels peu saturés et clairs (t-shirt, plis) ; peau et masque bleu épargnés
    w = (smooth(-S, -45, -25) * smooth(V, 120, 170) * alpha)[..., None]
    return np.clip(img * (1 - w) + corr * w, 0, 255), pts

# ---------- ÉTAPE 5b : courbe douce + épaule des hautes lumières ----------
def courbe(img):
    x = np.arange(256) / 255.0
    s = x + 0.06 * np.sin(2 * np.pi * x) * (x < 0.5) * 0.5 - 0.0      # léger relèvement des ombres
    s = 0.5 + (s - 0.5) * 1.06                                          # contraste doux
    epaule = np.where(s > 0.85, 0.85 + (s - 0.85) * 0.82, s)           # récupère les blancs non écrêtés
    lut = np.clip(epaule * 255, 0, 255).astype(np.float32)
    return lut[np.clip(img, 0, 255).astype(np.uint8)]

# ---------- ÉTAPE 5c : peau — débruitage léger, texture conservée ----------
def peau(img):
    u8 = np.clip(img, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(u8, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, S = hsv[..., 0], hsv[..., 1]
    zone = ((h <= 25) | (h >= 170)) & (S > 50) & (alpha > 0.5)
    w = cv2.GaussianBlur(zone.astype(np.float32), (0, 0), 2)[..., None] * 0.5   # 50 % seulement
    dn = cv2.fastNlMeansDenoisingColored(u8, None, 3, 3, 5, 15).astype(np.float32)
    return img * (1 - w) + dn * w

# ---------- ÉTAPE 5d : netteté ciblée yeux + monture ----------
def nettete_yeux(img):
    m = np.zeros((H, W), np.float32); cv2.ellipse(m, (380, 172), (115, 42), 0, 0, 360, 1, -1)
    m = cv2.GaussianBlur(m, (0, 0), 8)[..., None]
    bl = cv2.GaussianBlur(img, (0, 0), 1.0)
    return img + 0.7 * (img - bl) * m

wb, pts = balance(base.astype(np.float32))
r = nettete_yeux(peau(courbe(wb)))
retouche = np.clip(r, 0, 255).astype(np.uint8)
cv2.imwrite(f'{E}/05_retouche_1x_v2.png', retouche)

# ---------- ÉTAPE 5e : agrandissement x2 ----------
methode = 'Lanczos + netteté légère (Real-ESRGAN indisponible)'
up = None
try:
    import torch, spandrel
    model = spandrel.ModelLoader().load_from_file(os.path.join(SCR, 'weights/RealESRGAN_x2plus.pth')).eval()
    with torch.no_grad():
        t = torch.from_numpy(cv2.cvtColor(retouche, cv2.COLOR_BGR2RGB)).permute(2, 0, 1)[None].float() / 255
        o = model(t)[0].permute(1, 2, 0).clamp(0, 1).numpy()
    up = cv2.cvtColor((o * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)
    # 30 % de Lanczos réinjecté : Real-ESRGAN lisse légèrement la peau, on garde le grain d'origine
    lz = cv2.resize(retouche, (W * 2, H * 2), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    up = np.clip(0.7 * up + 0.3 * lz, 0, 255).astype(np.uint8)
    methode = 'Real-ESRGAN x2plus (mélangé 70/30 avec Lanczos pour garder la texture de peau)'
except Exception as e:
    print('Real-ESRGAN ÉCHEC :', repr(e))
    up = cv2.resize(retouche, (W * 2, H * 2), interpolation=cv2.INTER_LANCZOS4)
    up = np.clip(up * 1.4 - cv2.GaussianBlur(up, (0, 0), 1.2) * 0.4, 0, 255).astype(np.uint8)
print('agrandissement :', methode)
cv2.imwrite(f'{E}/05_retouche_2x_v2.png', up)
a2 = np.clip(cv2.resize(alpha, (W * 2, H * 2), interpolation=cv2.INTER_LANCZOS4), 0, 1)

# ---------- ÉTAPE 4 : version B (sujet détouré + fond studio) ----------
# fond d'origine estimé autour du sujet → décontamination des halos clairs
k = (a2 > 0.02).astype(np.uint8)
bg_est = cv2.inpaint(up, cv2.dilate(k, np.ones((5, 5), np.uint8)), 9, cv2.INPAINT_TELEA).astype(np.float32)
a_c = cv2.erode(a2, np.ones((3, 3), np.uint8))             # « choke » d'1 px (à 2x) contre le liseré
a_c = cv2.GaussianBlur(a_c, (0, 0), 1.5)                   # feather ≈ 1,5 px
a_c[a2 < 0.02] = 0
den = np.maximum(a2, 0.15)[..., None]
fg = np.clip((up.astype(np.float32) - (1 - a2[..., None]) * bg_est) / den, 0, 255)
lis = ((a2 > 0.02) & (a2 < 0.98))[..., None]
fg = np.where(lis, fg, up.astype(np.float32))
# v2 — liseré clair des cheveux : le bord prend la couleur du sujet juste à l'intérieur (cheveux, peau),
# propagée vers l'extérieur ; plus aucune trace du mur clair dans les pixels de bord.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from propagation import propager
k9 = np.ones((9, 9), np.uint8)
inter = cv2.erode((a2 > 0.98).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
prop = propager(up, inter, 60)
bord = (a2 > 0.02) & cv2.dilate((a2 < 0.5).astype(np.uint8), k9).astype(bool)
fg[bord] = prop[bord]

def hexbgr(hx): return np.array([int(hx[i:i + 2], 16) for i in (5, 3, 1)], np.float32)
FONDS = {'anthracite': ('#5a6270', '#2b2f36'), 'bleunuit': ('#2d4468', '#0e1626')}

def composer_B(box, out_wh, fond):
    """box = (x0, y0, x1, y1) en coordonnées de l'image 1x ; peut déborder (le fond est généré)."""
    x0, y0, x1, y1 = [v * 2 for v in box]
    cw, ch = x1 - x0, y1 - y0
    centre, bord = [hexbgr(c) for c in FONDS[fond]]
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    cx, cy = 395 * 2 - x0, 150 * 2 - y0                       # derrière la tête
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (0.75 * max(cw, ch))
    t = smooth(d, 0, 1)[..., None]
    canvas = centre * (1 - t) + bord * t
    canvas += np.random.default_rng(1).normal(0, 1.2, canvas.shape)   # anti-bandes
    # placer sujet et alpha dans le canevas
    A = np.zeros((ch, cw), np.float32); F = np.zeros((ch, cw, 3), np.float32)
    sx0, sy0 = max(x0, 0), max(y0, 0); sx1, sy1 = min(x1, W * 2), min(y1, H * 2)
    A[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a_c[sy0:sy1, sx0:sx1]
    F[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = fg[sy0:sy1, sx0:sx1]
    # ombre portée très légère (décalée en bas à droite, très floue)
    M = np.float32([[1, 0, 10], [0, 1, 14]])
    sh = cv2.GaussianBlur(cv2.warpAffine(A, M, (cw, ch)), (0, 0), 22) * 0.30
    canvas *= (1 - sh[..., None])
    out = F * A[..., None] + canvas * (1 - A[..., None])
    return cv2.resize(np.clip(out, 0, 255).astype(np.uint8), out_wh, interpolation=cv2.INTER_LANCZOS4)

# ---------- version A : cadrages ----------
def composer_A(box, out_wh, ext_haut=0):
    x0, y0, x1, y1 = [v * 2 for v in box]
    img = up
    if ext_haut:   # prolongement du mur uni au-dessus de la tête (signalé dans le rapport)
        e = ext_haut * 2
        haut = up[:e * 2].astype(np.float32)
        top = cv2.resize(cv2.GaussianBlur(up[:60], (0, 0), 25), (W * 2, e)).astype(np.float32)
        top += np.random.default_rng(2).normal(0, 0.9, top.shape)
        img = np.vstack([np.clip(top, 0, 255).astype(np.uint8), up]); y0 += e; y1 += e
    c = img[y0:y1, x0:x1]
    return cv2.resize(c, out_wh, interpolation=cv2.INTER_LANCZOS4)

S45, S11 = (1080, 1350), (1080, 1080)
exports = {
    'A_large_4x5':  composer_A((127, -24, 757, 764), S45, ext_haut=24),
    'A_buste_4x5':  composer_A((185, 0, 625, 550), S45),
    'A_buste_1x1':  composer_A((185, 30, 625, 470), S11),
}
for f in FONDS:
    exports[f'B_{f}_large_4x5'] = composer_B((117, -50, 767, 762), S45, f)
    exports[f'B_{f}_buste_4x5'] = composer_B((175, 0, 615, 550), S45, f)
    exports[f'B_{f}_1x1'] = composer_B((95, 0, 695, 600), S11, f)
os.makedirs(O, exist_ok=True)
for n, im in exports.items():
    cv2.imwrite(f'{O}/{n}.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 95])
    cv2.imwrite(f'{O}/{n}.png', im)
    print(n, im.shape[1], 'x', im.shape[0])
print('points de balance (canal: entrée→sortie) :', {c: [(round(a), round(b)) for a, b in p] for c, p in pts.items()})
