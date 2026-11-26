"""v4 — version A, cadre d'origine (761×764 sans bandeau), agrandie x2 classique (Lanczos), finition naturelle et chaude.
Décor RETOUCHÉ (accord explicite) : chaises, bras voisin, papiers et tissu remplacés par un mur uni et une table bois
reconstitués. Le sujet n'est pas modifié (forme, traits, masque, lunettes, t-shirt, bracelets).
Entrées : output/etapes/02_sans_bandeau.png, 02_masque_final.png, 02_masque_u2net_human_seg.png
Sorties : output/v4/ (+ étapes intermédiaires output/v4/etapes/)."""
import cv2, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from propagation import propager
E, O = 'output/etapes', 'output/v4'; os.makedirs(f'{O}/etapes', exist_ok=True)
im = cv2.imread(f'{E}/02_sans_bandeau.png'); H, W = im.shape[:2]
f32 = lambda x: x.astype(np.float32)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int); h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
yy, xx = np.mgrid[0:H, 0:W]

# ---------- 1. Masque du sujet : oreille entière ----------
a = f32(cv2.imread(f'{E}/02_masque_final.png', 0)) / 255
u2 = f32(cv2.imread(f'{E}/02_masque_u2net_human_seg.png', 0)) / 255
boite = (yy >= 140) & (yy < 275) & (xx >= 440) & (xx < 540)
# lobe seul (isnet avait le haut de l'oreille juste) : peau rosée x 462–489, y 200–242, sans le rouge vif du cœur collé à droite
lobe = (yy >= 200) & (yy <= 242) & (xx >= 462) & (xx <= 489)
ajout = lobe & (u2 > 0.5) & (s <= 135) & (s >= 40) & ~(((h >= 168) | (h <= 3)) & (s > 120) & (xx > 484))
ajout = cv2.morphologyEx(ajout.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
ajout = cv2.morphologyEx(ajout, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
a = np.maximum(a, cv2.GaussianBlur(ajout.astype(np.float32), (0, 0), 0.8) * lobe)
# lobe arrondi : on lisse la silhouette de l'oreille basse (pas de coin carré)
zl = (yy >= 195) & (yy <= 250) & (xx >= 455) & (xx <= 500)
rond = cv2.GaussianBlur(a, (0, 0), 2.2); rond = np.clip((rond - 0.42) / 0.16, 0, 1)
a = np.where(zl, cv2.GaussianBlur(rond, (0, 0), 0.7), a)
# bord gauche (ancienne chaise) : contour lissé, sans points isolés
zg = (xx < 200) & (yy >= 460) & (yy < 640)
lg = cv2.GaussianBlur(a, (0, 0), 1.8); lg = np.clip((lg - 0.42) / 0.16, 0, 1)
a = np.where(zg, cv2.GaussianBlur(lg, (0, 0), 0.7), a)
# contour plus franc : moins de zones semi-transparentes (sauf cheveux, y < 140)
dur = np.clip((a - 0.3) / 0.4, 0, 1); dur = dur * dur * (3 - 2 * dur)
dur = cv2.GaussianBlur(dur, (0, 0), 0.7)
a = np.where(yy < 140, a, dur)
# creux entre bras droit et buste (x 540–610, y 500–610) : le mur bleuté vu à travers n'est pas le sujet
creux = (xx >= 548) & (xx <= 610) & (yy >= 500) & (yy <= 605)
# mur vu à travers : bleuté (teinte 100–130), assez saturé et clair ; grandit depuis les germes sûrs (s ≥ 28, v ≥ 205)
cand = creux & (h >= 100) & (h <= 130) & (s >= 16) & (v >= 200)
germe = cand & (s >= 28) & (v >= 205)
n_, lab_, _, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8))
ids = np.unique(lab_[germe]); ids = ids[ids > 0]
mur_vu = np.isin(lab_, ids)
mur_vu = cv2.morphologyEx(mur_vu.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
mur_vu = cv2.morphologyEx(mur_vu, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool) | (creux & (a < 0.5))
print('creux bras droit : pixels de mur rendus au fond =', int(mur_vu.sum()))
a[mur_vu] = 0
a = np.where(creux, cv2.GaussianBlur(a, (0, 0), 0.7), a)
# bas des avant-bras : retirer les bouts de papier blanc et lisser le contour irrégulier
papier = (yy > 650) & (s < 25) & (v > 215) & ~((xx >= 450) & (xx <= 505) & (yy <= 700))   # bracelets protégés
a[papier] = 0
bas = yy > 630
lisse = cv2.GaussianBlur(a, (0, 0), 2.2); lisse = np.clip((lisse - 0.42) / 0.16, 0, 1)
lisse = cv2.GaussianBlur(lisse, (0, 0), 0.7)
a = np.where(bas, lisse, a)
print('oreille : pixels de lobe rendus au sujet =', int((ajout & ~(cv2.imread(f'{E}/02_masque_final.png', 0) > 128)).sum()))
cv2.imwrite(f'{O}/etapes/1_masque_v4.png', (a * 255).astype(np.uint8))

# ---------- 2. Décor reconstitué : mur + table ----------
TABLE = lambda x: 700 - 28 * x / W                          # bord arrière de la table : y≈700 à gauche, ≈672 à droite
table = yy >= TABLE(xx)
lab_im = f32(cv2.cvtColor(im, cv2.COLOR_BGR2LAB))
loin = ~cv2.dilate((a > 0.02).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
rouge = ((h <= 12) | (h >= 160)) & (s > 35)
mur_propre = loin & ~table & ~cv2.dilate(rouge.astype(np.uint8), np.ones((21, 21), np.uint8)).astype(bool) \
             & (s < 45) & (v > 225) & ~((xx >= 620) & (yy >= 340)) & ~((xx < 190) & (yy >= 450))
X, Y = xx / W, yy / H
def poly(mask, deg):
    A = np.stack([X**i * Y**j for i in range(deg + 1) for j in range(deg + 1 - i)], -1)
    idx = np.flatnonzero(mask.ravel())[::3]
    return np.stack([A.reshape(-1, A.shape[-1]) @ np.linalg.lstsq(A.reshape(-1, A.shape[-1])[idx], lab_im[..., c].ravel()[idx], rcond=None)[0] for c in range(3)], -1).reshape(H, W, 3)
mur = poly(mur_propre, 2)
# finition : mur gris clair neutre légèrement chaud (on retire 75 % de la dominante lavande)
mur[..., 1] = 128 + (mur[..., 1] - 128) * 0.25 + 0.6
mur[..., 2] = 128 + (mur[..., 2] - 128) * 0.25 + 1.5
mur[..., 0] = np.clip(mur[..., 0] - 3, 0, 255)
sig_mur = float(np.std((lab_im - poly(mur_propre, 2))[mur_propre][:, 0]))
bois_px = loin & (h >= 12) & (h <= 26) & (s > 35) & (s < 100) & (v > 200) & (yy > 660) & (yy < 712) & (xx > 500)
bois = lab_im[bois_px].mean(0); print('bois : pixels de référence =', int(bois_px.sum()), ' LAB moyen =', bois.round(1))
rng = np.random.default_rng(4)
# table : couleur bois mesurée, plus claire vers l'avant, fines veines horizontales très douces
prof = np.clip((yy - TABLE(xx)) / 70.0, 0, 1)
tab = np.zeros_like(lab_im); tab[...] = bois
tab[..., 0] += 6 * prof - 3
veines = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), sigmaX=40, sigmaY=0.8)
tab[..., 0] += veines / (veines.std() + 1e-6) * 1.6
fond = np.where(table[..., None], tab, mur)
fond[..., 0] += rng.normal(0, max(sig_mur, 0.8), (H, W)).astype(np.float32)     # grain de la photo
# arête de table douce (ombre fine sur le bord arrière)
arete = np.exp(-((yy - TABLE(xx)) / 2.5) ** 2) * 9
fond[..., 0] -= arete
fond_bgr = f32(cv2.cvtColor(np.clip(fond, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR))
# ombre de contact des avant-bras sur la table + ombre très douce du buste sur le mur
contact = cv2.GaussianBlur(cv2.warpAffine(a, np.float32([[1, 0, 1], [0, 1, 4]]), (W, H)), (0, 0), 3)
ombre = np.where(table, contact * 0.55, cv2.GaussianBlur(cv2.warpAffine(a, np.float32([[1, 0, 10], [0, 1, 12]]), (W, H)), (0, 0), 25) * 0.10)
fond_bgr *= (1 - ombre[..., None])
cv2.imwrite(f'{O}/etapes/2_fond_reconstitue.png', np.clip(fond_bgr, 0, 255).astype(np.uint8))

# ---------- 3. Composition sans liseré ----------
inter = cv2.erode((a > 0.98).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
prop = propager(f32(im), inter, 30)
bord = (a > 0.02) & (a < 0.98)
fg = f32(im).copy(); fg[bord] = prop[bord]
# bord plein du sujet (α 0.9–0.98) : on garde la luminosité réelle, seule la teinte vient de l'intérieur
lab_fg = f32(cv2.cvtColor(np.clip(fg, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB))
plein = (a >= 0.9) & (a < 0.98)
lab_fg[plein, 0] = lab_im[plein, 0]
fg = f32(cv2.cvtColor(np.clip(lab_fg, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR))
ac = cv2.GaussianBlur(np.clip((a - 0.08) / 0.84, 0, 1), (0, 0), 0.7)[..., None]
comp = fg * ac + fond_bgr * (1 - ac)
lc = f32(cv2.cvtColor(np.clip(comp, 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB))
ref = boite & cv2.erode((a > 0.98).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & (xx > 465)
a_peau = float(np.percentile(lc[..., 1][ref], 90))
zr = boite & (xx > 470)
lc[..., 1] = np.where(zr, np.minimum(lc[..., 1], a_peau), lc[..., 1])
comp = f32(cv2.cvtColor(np.clip(lc, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR))
cv2.imwrite(f'{O}/etapes/3_composition.png', np.clip(comp, 0, 255).astype(np.uint8))

# ---------- 4. Finition naturelle et chaude ----------
sm = lambda x, lo, hi: np.clip((x - lo) / (hi - lo), 0, 1) ** 2 * (3 - 2 * np.clip((x - lo) / (hi - lo), 0, 1))
u8 = lambda x: np.clip(x, 0, 255).astype(np.uint8)
c = comp.copy()
cs = cv2.cvtColor(u8(c), cv2.COLOR_BGR2HSV).astype(np.float32)
# a) blancs du t-shirt neutres (pixels peu saturés du sujet uniquement)
gris = (sm(-cs[..., 1], -45, -25) * sm(cs[..., 2], 120, 170) * a)[..., None]
moy = c.mean(-1, keepdims=True); c = c * (1 - gris * 0.85) + moy * (gris * 0.85)
# b) peau chaude : léger réchauffement des tons chairs (sujet seulement), pas du masque bleu
peau = (((cs[..., 0] <= 25) | (cs[..., 0] >= 170)) & (cs[..., 1] > 45) & (a > 0.5)).astype(np.float32)
peau = cv2.GaussianBlur(peau, (0, 0), 2)[..., None]
c = c * (1 + peau * np.array([-0.035, 0.0, 0.04], np.float32))
# c) courbe douce : ombres légèrement ouvertes, contraste modéré, blancs laissés blancs
x = np.arange(256, dtype=np.float32) / 255
cur = x + 0.035 * np.sin(np.pi * x) - 0.02 * np.sin(2 * np.pi * x)
lut = np.clip(cur * 255, 0, 255)
c = lut[u8(c)]
# d) relief du visage : contraste local doux (grand rayon) sur le sujet
blur = cv2.GaussianBlur(c, (0, 0), 12)
c = c + (c - blur) * 0.18 * a[..., None]
# e) peau : débruitage léger (50 %), texture conservée
dn = f32(cv2.fastNlMeansDenoisingColored(u8(c), None, 3, 3, 5, 15))
c = c * (1 - peau * 0.45) + dn * (peau * 0.45)
# f) netteté ciblée yeux + monture
m = np.zeros((H, W), np.float32); cv2.ellipse(m, (380, 172), (115, 42), 0, 0, 360, 1, -1)
m = cv2.GaussianBlur(m, (0, 0), 8)[..., None]
c = c + 0.6 * (c - cv2.GaussianBlur(c, (0, 0), 1.0)) * m
# g) vignettage très léger pour guider l'œil
d = np.sqrt(((xx - 390) / W) ** 2 + ((yy - 300) / H) ** 2)
c *= (1 - 0.10 * sm(d, 0.35, 0.85))[..., None]
fin1x = u8(c)
cv2.imwrite(f'{O}/etapes/4_finition_1x.png', fin1x)

# ---------- 5. Agrandissement x2 classique + exports ----------
up = f32(cv2.resize(fin1x, (W * 2, H * 2), interpolation=cv2.INTER_LANCZOS4))
up = u8(up + 0.35 * (up - cv2.GaussianBlur(up, (0, 0), 1.2)))
nom = 'DrAbdou_portrait_A_v4'
cv2.imwrite(f'{O}/{nom}.jpg', up, [cv2.IMWRITE_JPEG_QUALITY, 95]); cv2.imwrite(f'{O}/{nom}.png', up)
print(nom, up.shape[1], 'x', up.shape[0])
