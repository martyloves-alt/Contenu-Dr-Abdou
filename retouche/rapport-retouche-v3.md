# Retouche photo portrait — v3 (version A uniquement)

Demande : version A (même décor, nettoyé) seule, aucun bout de chaise ni de papier, 4:5 et 1:1, plus d'espace au-dessus de la tête en 1:1.

Script : `python3 retouche/v3_version_A.py` (part de la retouche v2 : `output/etapes/05_retouche_2x_v2.png`). Sorties : `output/v3/`.

| Fichier | Cadre (photo d'origine) | Marge au-dessus de la tête | Yeux |
|---|---|---|---|
| DrAbdou_portrait_A_v3_4x5 (1080×1350) | x 185–625, y 0–550 | 10 % | 32 % de la hauteur |
| DrAbdou_portrait_A_v3_1x1 (1080×1080) | x 185–625, y 0–440 | 13 % (v2 : 6 %) | 40 % |

- Chaises (gauche x < 180 dès y 460 ; droite x ≥ 630 dès y 355), papiers (y ≥ 680) et bras voisin (x ≥ 722) hors cadre ; vérifié visuellement et par recherche de pixels dorés au bord gauche (0).
- Le trait clair au bord gauche du 4:5 est la couture d'épaule du t-shirt (réelle).
- 1:1 : le cadre touche déjà le haut de la photo (y = 0). Davantage de marge demanderait d'ajouter du mur au-dessus de la tête (non fait sans accord).
- Comparaisons : `output/v3/comparaison_4x5.jpg`, `output/v3/comparaison_1x1.jpg`, cadres tracés sur l'original : `output/v3/cadres_sur_original.jpg`.
