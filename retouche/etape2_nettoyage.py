"""Étape 2 : coupe du bandeau noir + segmentation de la personne (rembg)."""
import cv2, numpy as np, sys
from rembg import remove, new_session
im = cv2.imread('input/photo.jpg')
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).mean(1)
# première ligne très sombre (<80) dans le dernier quart, en remontant d'un bloc continu
y = im.shape[0]
while y > 0 and g[y-1] < 80: y -= 1
print('bandeau détecté : lignes', y, '→', im.shape[0]-1)
crop = im[:y]
cv2.imwrite('output/etapes/02_sans_bandeau.png', crop)
for model in sys.argv[1:] or ['u2net_human_seg', 'isnet-general-use']:
    s = new_session(model)
    m = remove(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB), session=s, only_mask=True)
    m = np.array(m)
    cv2.imwrite(f'output/etapes/02_masque_{model}.png', m)
    ov = crop.copy(); ov[m < 128] = (ov[m < 128] * 0.25).astype(np.uint8)
    cv2.imwrite(f'output/etapes/02_controle_{model}.jpg', ov)
    print(model, 'ok, couverture', round((m > 128).mean() * 100, 1), '%')
