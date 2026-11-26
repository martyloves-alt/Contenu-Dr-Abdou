"""v3 : version A seule (même décor, nettoyé), cadrage sans aucun bout de chaise ni de papier.
Base : output/etapes/05_retouche_2x_v2.png (retouche v2 agrandie x2). Sorties : output/v3/."""
import cv2, numpy as np, os
up = cv2.imread('output/etapes/05_retouche_2x_v2.png'); orig = cv2.imread('input/photo.jpg')
O = 'output/v3'; os.makedirs(O, exist_ok=True)
# boîtes en coordonnées de la photo d'origine (x0, y0, x1, y1)
# chaises : gauche x < 180 dès y 460, droite x ≥ 630 dès y 355 ; papiers y ≥ 680 ; bras voisin x ≥ 722
CADRES = {'4x5': ((185, 0, 625, 550), (1080, 1350)),
          '1x1': ((185, 0, 625, 440), (1080, 1080))}   # v2 commençait à y=30 : +30 px au-dessus de la tête
for n, ((x0, y0, x1, y1), wh) in CADRES.items():
    out = cv2.resize(up[y0 * 2:y1 * 2, x0 * 2:x1 * 2], wh, interpolation=cv2.INTER_LANCZOS4)
    nom = f'DrAbdou_portrait_A_v3_{n}'
    cv2.imwrite(f'{O}/{nom}.jpg', out, [cv2.IMWRITE_JPEG_QUALITY, 95]); cv2.imwrite(f'{O}/{nom}.png', out)
    av = cv2.resize(orig[y0:y1, x0:x1], wh, interpolation=cv2.INTER_LANCZOS4)
    def lab(i, t):
        i = i.copy(); cv2.rectangle(i, (0, 0), (i.shape[1], 64), (0, 0, 0), -1)
        cv2.putText(i, t, (24, 46), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3, cv2.LINE_AA); return i
    cv2.imwrite(f'{O}/comparaison_{n}.jpg', np.hstack([lab(av, 'AVANT'), np.full((wh[1], 14, 3), 255, np.uint8), lab(out, 'APRES (v3)')]), [cv2.IMWRITE_JPEG_QUALITY, 92])
    tete = 57 - y0; yeux = 175 - y0
    print(nom, wh, f'marge au-dessus de la tête {tete / (y1 - y0) * 100:.0f} %, yeux à {yeux / (y1 - y0) * 100:.0f} % de la hauteur')
# vue d'ensemble : photo d'origine entière, cadres v3 tracés
ov = orig.copy()
for n, ((x0, y0, x1, y1), _) in CADRES.items():
    c = (0, 200, 0) if n == '4x5' else (255, 120, 0)
    cv2.rectangle(ov, (x0, y0), (x1 - 1, y1 - 1), c, 3); cv2.putText(ov, n, (x0 + 6, y1 - 10), 0, .8, c, 2)
cv2.imwrite(f'{O}/cadres_sur_original.jpg', ov)
