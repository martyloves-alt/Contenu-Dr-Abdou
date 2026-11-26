"""Propagation de la couleur du sujet vers son bord, pixel par pixel (voisins connus uniquement)."""
import cv2, numpy as np
def propager(img, connu, n):
    """img float32 HxWx3, connu bool HxW. Étend la couleur des pixels connus de n pixels vers l'extérieur."""
    out = img.astype(np.float32).copy(); k = connu.astype(np.float32); K = np.ones((3, 3), np.float32)
    out *= k[..., None]
    for _ in range(n):
        s = cv2.filter2D(out, -1, K, borderType=cv2.BORDER_CONSTANT); c = cv2.filter2D(k, -1, K, borderType=cv2.BORDER_CONSTANT)
        neuf = (k == 0) & (c > 0)
        out[neuf] = s[neuf] / c[neuf][:, None]; k[neuf] = 1
    out[k == 0] = img[k == 0]          # sécurité : un pixel non atteint garde sa couleur d'origine (jamais de noir)
    return out
