"""Étape 2b : masque final = isnet-general-use, moins le cadre doré/rouge de la chaise gauche."""
import cv2, numpy as np
im = cv2.imread('output/etapes/02_sans_bandeau.png')
m = cv2.imread('output/etapes/02_masque_isnet-general-use.png', 0)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s = hsv[..., 0].astype(int), hsv[..., 1].astype(int)
zone = np.zeros(m.shape, bool); zone[470:, :175] = True
dore = (h >= 11) & (h <= 28) & (s > 105)
rouge = ((h >= 165) | (h <= 4)) & (s > 150)
rose = (h >= 160) & (s > 30)                      # tissu rouge du siège en lisière du bras
reflet = (h >= 11) & (h <= 30) & (s > 45) & np.pad(np.ones((90, 150), bool), ((470, m.shape[0]-560), (0, m.shape[1]-150)))
chaise = zone & (dore | rouge | rose | reflet)
chaise = cv2.dilate(chaise.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & zone
m2 = m.copy(); m2[chaise] = 0
m2 = cv2.morphologyEx(m2, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
# garder la plus grande composante
b = (m2 > 128).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(b)
k = 1 + np.argmax(st[1:, 4]); keep = (lab == k)
m2[~keep & (m2 > 0)] = 0
# combler les trous fermés (verres des lunettes, entre bras et buste s'ils sont fermés)
pleine = (m2 > 128).astype(np.uint8) * 255
ff = pleine.copy(); cv2.floodFill(ff, np.zeros((ff.shape[0] + 2, ff.shape[1] + 2), np.uint8), (0, 0), 255)
trous = cv2.bitwise_not(ff) > 0
# seuls les petits trous (< 3000 px) sont comblés : un vrai jour entre bras et buste resterait ouvert
n, labt, st, _ = cv2.connectedComponentsWithStats(trous.astype(np.uint8))
for i in range(1, n):
    if st[i, 4] < 3000 and st[i, 1] + st[i, 3] < 240: m2[labt == i] = 255   # zone lunettes uniquement
print('trous comblés :', sum(1 for i in range(1, n) if st[i, 4] < 3000 and st[i, 1] + st[i, 3] < 240), '/', n - 1)
# tête : combler les creux d'alpha dans les verres (fermeture 5 px, zone tête seulement)
tete = m2[40:340, 250:520]
m2[40:340, 250:520] = np.maximum(tete, cv2.morphologyEx(tete, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))))
print('alpha min dans le verre gauche :', int(m2[150:200, 295:330].min()))
# lisser le bord découpé contre la chaise gauche (marches d'escalier)
z = m2[460:, :230].astype(np.float32)
z = cv2.GaussianBlur(cv2.morphologyEx(z, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)), (0, 0), 1.6)
m2[460:, :230] = np.clip((z - 128) * 1.6 + 128, 0, 255).astype(np.uint8)
cv2.imwrite('output/etapes/02_masque_final.png', m2)
ov = im.copy(); ov[m2 < 128] = (ov[m2 < 128] * 0.25).astype(np.uint8)
cv2.imwrite('output/etapes/02_controle_final.jpg', ov)
z = cv2.resize(ov[450:764, 60:330], None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
cv2.imwrite('output/etapes/02_zoom_coude_gauche.jpg', z)
print('pixels retirés', int(chaise.sum()))
