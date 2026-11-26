# Retouche photo portrait — v1

Source : `input/photo.jpg` (761 × 814, JPEG). Images non versionnées (`input/`, `output/`) : à garder sur Drive.

## Refaire tout le traitement
```
python3 retouche/etape2_nettoyage.py          # coupe bandeau (y ≥ 764) + masques rembg
python3 retouche/etape2b_masque_final.py      # masque isnet moins chaise gauche
python3 retouche/etape3_version_A.py          # effacement cœurs / fils / ombres
python3 retouche/etapes4a6.py <dossier_poids> # retouche, x2, version B, exports
python3 retouche/etape7_controle.py           # comparaison + zooms 200 %
```
Dépendances : opencv, rembg[cpu], torch + torchvision (CPU), spandrel, poids RealESRGAN_x2plus.pth.

## Choix et écarts par rapport à la consigne
- Masque : isnet-general-use retenu (u2net_human_seg englobait un cœur derrière l'oreille). Les deux incluaient le cadre doré de la chaise gauche : retiré par couleur.
- Cœurs : TELEA et NS testés, tous deux laissent des traînées roses (écart moyen au mur ≈ 7). Retenu : remplissage par un modèle lisse du mur (polynôme) + grain mesuré (écart ≈ 1,7). Les trois sorties sont dans `output/etapes/03_inpaint_*.png`.
- Balance des blancs : les blancs du t-shirt tiraient au bleu, ses plis au magenta. Correction appliquée seulement aux pixels peu saturés (peau et masque bleu épargnés).
- 70 % du t-shirt était déjà écrêté à 255 dans le JPEG : ces hautes lumières sont irrécupérables.
- Agrandissement : Real-ESRGAN x2plus, mélangé 70/30 avec Lanczos (Real-ESRGAN seul lissait la peau).
- A large 4:5 : 24 px de mur uni ajoutés au-dessus de la tête (même modèle de mur) faute de hauteur.
- Ombre portée B : décalage (10, 14) px, flou 22, opacité 30 %.

## Points imparfaits connus
- A large : chaises, bras du voisin et papiers restent (option « mains et coudes entiers »).
- A : léger liseré rosé au bord haut de l'oreille (ancien cœur derrière).
- B : fin liseré clair sur le haut des cheveux ; bas des bras coupé net à la ligne de table (table supprimée) ; bande sombre fine contre le coude gauche (ancienne chaise).
