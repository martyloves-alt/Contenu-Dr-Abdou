"""Étape 3 : version A — effacement des cœurs, fils et ombres de cœurs sur le mur (hors personne).
Masque = rouges HSV (0° et 180°) + écarts au modèle lisse du mur ; puis cv2.inpaint TELEA / NS
et, en 3e variante, remplissage par le modèle de mur + grain (le mur est uni)."""
import cv2, numpy as np
im = cv2.imread('output/etapes/02_sans_bandeau.png')
alpha_p = cv2.imread('output/etapes/02_masque_final.png', 0).astype(np.float32) / 255
pers = alpha_p > 0.5
H, W = pers.shape
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s = hsv[..., 0].astype(int), hsv[..., 1].astype(int)
lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
rouge = ((h <= 12) | (h >= 160)) & (s > 35)
# zone mur : hors dossiers de chaises et hors table
mur = np.ones((H, W), bool)
mur[430:, 625:] = False; mur[355:430, 690:] = False; mur[460:, :185] = False; mur[640:, :] = False
siege = (s > 120) & ((h <= 8) | (h >= 165)) & (np.arange(H)[:, None] >= 355) & (np.arange(W)[None] >= 640)
# ne garder que le siège lui-même (plus grande composante) : un cœur isolé au-dessus du dossier reste à effacer
_n, _l, _st, _ = cv2.connectedComponentsWithStats(siege.astype(np.uint8))
siege = (_l == 1 + np.argmax(_st[1:, 4])) if _n > 1 else siege
protege = cv2.dilate(pers.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
zone = mur & ~protege & ~siege
# modèle lisse du mur : polynôme 2D de degré 3 ajusté sur les pixels propres (2 passes robustes)
yy, xx = np.mgrid[0:H, 0:W]; X = xx / W; Y = yy / H
A = np.stack([X**i * Y**j for i in range(4) for j in range(4 - i)], -1)
propre = zone & ~cv2.dilate(rouge.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
for _ in range(2):
    idx = np.flatnonzero(propre.ravel())[::7]
    coef = [np.linalg.lstsq(A.reshape(-1, A.shape[-1])[idx], lab[..., c].ravel()[idx], rcond=None)[0] for c in range(3)]
    model = np.stack([A @ c for c in coef], -1)
    dE = np.linalg.norm(lab - model, axis=-1)
    propre = zone & (dE < 4)
defaut = zone & (rouge | (dE > 3))
mr = cv2.morphologyEx(defaut.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
mr = cv2.dilate(mr, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))   # ≈ 4 px pour les fils
mr[~zone] = 0
cv2.imwrite('output/etapes/03_masque_rouges.png', mr * 255)
telea = cv2.inpaint(im, mr, 7, cv2.INPAINT_TELEA)
ns = cv2.inpaint(im, mr, 7, cv2.INPAINT_NS)
# variante modèle : couleur du mur reconstruite + grain mesuré sur le mur propre
rng = np.random.default_rng(0)
sig = float(np.std((lab - model)[propre], axis=0).mean())
fill = model + rng.normal(0, sig, model.shape).astype(np.float32)
fill = cv2.cvtColor(np.clip(fill, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
a = cv2.GaussianBlur(mr.astype(np.float32), (7, 7), 0)[..., None]
modele = im * (1 - a) + fill * a
# lisière du sujet : recomposer avec l'alpha doux de la personne là où le fond était un cœur
lis = cv2.dilate(mr, np.ones((15, 15), np.uint8)).astype(bool) & (alpha_p < 0.98) & (alpha_p > 0) & (np.arange(H)[:, None] < 640)
ap = alpha_p[..., None]
modele[lis] = (ap * im + (1 - ap) * fill)[lis]
modele = np.clip(modele, 0, 255).astype(np.uint8)
for nom, r in (('telea', telea), ('ns', ns), ('modele', modele)):
    cv2.imwrite(f'output/etapes/03_inpaint_{nom}.png', r)
    d = np.linalg.norm(cv2.cvtColor(r, cv2.COLOR_BGR2LAB).astype(np.float32) - model, axis=-1)
    print(f'{nom:7s} écart moyen au mur dans la zone effacée : {d[mr > 0].mean():.2f}  (pixels > 5 : {int((d[mr > 0] > 5).sum())})')
print('pixels effacés :', int(mr.sum()), ' grain mur σ =', round(sig, 2))
