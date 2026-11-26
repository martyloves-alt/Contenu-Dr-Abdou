"""Contrôle v4 : avant | après (même cadre), et zooms à 200 % sur les zones sensibles."""
import cv2, numpy as np
o = cv2.imread('input/photo.jpg'); f = cv2.imread('output/v4/DrAbdou_portrait_A_v4.png')
H2 = f.shape[0]
av = cv2.resize(o, (round(o.shape[1] * H2 / o.shape[0]), H2), interpolation=cv2.INTER_LANCZOS4)
def lab(i, t):
    i = i.copy(); cv2.rectangle(i, (0, 0), (i.shape[1], 80), (0, 0, 0), -1)
    cv2.putText(i, t, (28, 56), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 3, cv2.LINE_AA); return i
cv2.imwrite('output/v4/comparaison_avant_apres.jpg', np.hstack([lab(av, 'AVANT'), np.full((H2, 16, 3), 255, np.uint8), lab(f, 'APRES (v4)')]), [cv2.IMWRITE_JPEG_QUALITY, 90])
o1 = cv2.imread('output/etapes/02_sans_bandeau.png')
Z = {'oreille': (440, 140, 540, 270), 'cheveux_lunettes': (265, 50, 495, 215), 'bras_droit': (520, 470, 700, 660),
     'bas_bras_table': (130, 620, 520, 764), 'main_droite': (600, 600, 761, 764), 'coude_gauche': (100, 440, 260, 700)}
for n, (x0, y0, x1, y1) in Z.items():
    a = cv2.resize(o1[y0:y1, x0:x1], None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    b = f[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
    cv2.imwrite(f'output/v4/zoom200_{n}.jpg', np.hstack([a, np.full((a.shape[0], 8, 3), 255, np.uint8), b]), [cv2.IMWRITE_JPEG_QUALITY, 92])
print('ok')
