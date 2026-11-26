"""Étape 7 : contrôle qualité — comparaison avant | A | B, et zooms à 200 % (par rapport à l'original)."""
import cv2, numpy as np
orig = cv2.imread('input/photo.jpg')
A = cv2.imread('output/A_large_4x5.png'); Ba = cv2.imread('output/B_anthracite_large_4x5.png'); Bb = cv2.imread('output/B_bleunuit_large_4x5.png')
def h(img, H=1350): return cv2.resize(img, (round(img.shape[1] * H / img.shape[0]), H), interpolation=cv2.INTER_AREA)
sep = np.full((1350, 12, 3), 255, np.uint8)
def lab(img, t):
    img = img.copy(); cv2.rectangle(img, (0, 0), (img.shape[1], 60), (0, 0, 0), -1)
    cv2.putText(img, t, (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 2, cv2.LINE_AA); return img
comp = np.hstack([lab(h(orig), 'AVANT'), sep, lab(A, 'VERSION A'), sep, lab(Ba, 'VERSION B (anthracite)'), sep, lab(Bb, 'B (bleu nuit)')])
cv2.imwrite('output/comparaison.jpg', comp, [cv2.IMWRITE_JPEG_QUALITY, 92])
# zooms 200 % : boîte en coordonnées de l'original ; mapping vers chaque export
BOX = {'A': ((127, -24, 757, 764), A), 'B': ((117, -50, 767, 762), Ba)}
ZONES = {'cheveux': (320, 45, 490, 125), 'lunettes': (265, 130, 490, 215), 'oreille_coeurs': (440, 100, 600, 300),
         'epaule_D': (540, 380, 700, 520), 'coude_G': (127, 470, 267, 640), 'coeurs_G': (130, 20, 290, 300)}
for z, (x0, y0, x1, y1) in ZONES.items():
    row = [cv2.resize(orig[y0:y1, x0:x1], None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)]
    for k in 'AB':
        (bx0, by0, bx1, _), img = BOX[k]; s = img.shape[1] / (bx1 - bx0)
        c = img[round((y0 - by0) * s):round((y1 - by0) * s), round((x0 - bx0) * s):round((x1 - bx0) * s)]
        row.append(cv2.resize(c, (row[0].shape[1], row[0].shape[0]), interpolation=cv2.INTER_CUBIC))
    s2 = np.full((row[0].shape[0], 8, 3), 255, np.uint8)
    cv2.imwrite(f'output/zoom200_{z}.jpg', np.hstack([row[0], s2, row[1], s2, row[2]]), [cv2.IMWRITE_JPEG_QUALITY, 92])
print('ok')
