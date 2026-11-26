# Retouche photo portrait — v2

Demande : corriger le liseré de l'oreille et le liseré des cheveux. v1 conservée telle quelle (`output/`), v2 dans `output/v2/`.

## Refaire la v2
```
python3 retouche/etape3_version_A_v2.py
python3 retouche/etapes4a6_v2.py <dossier_poids>
python3 retouche/etape7_controle_v2.py
```
(étapes 2 et 2b inchangées ; `retouche/propagation.py` = outil partagé)

## Ce qui a changé
- **Oreille (version A)** : seul l'excès de rouge (canal a* en LAB) est retiré autour de l'oreille, plafonné à la teinte de la peau de l'oreille côté sujet et à celle du mur côté fond. La luminosité de chaque pixel est conservée : forme de l'oreille et du lobe identiques à l'original. Zone touchée : x 462–505, y 151–259 (coordonnées de la photo d'origine).
- **Cheveux et contours (version B)** : les pixels du bord prennent la couleur du sujet juste à l'intérieur (cheveux, peau), propagée pixel par pixel vers l'extérieur ; plus de mur clair dans le liseré.
- Cheveux de la version A : inchangés par rapport à la v1 (pas de liseré à corriger : le fond reste le mur clair).

## Essais écartés pendant la v2 (pour mémoire)
- Recoloration complète du bord de l'oreille : bordure grise (couleur des cheveux tirée dans l'oreille) puis lobe partiellement coupé (le masque l'avait manqué). Abandonné : modifiait la forme de l'oreille.

## Reste imparfait
- Oreille A : très fin contour clair neutre (non rose) visible à 200 %.
- Points v1 non traités : chaises/bras voisin/papiers dans A large ; bas des bras coupé net dans B large ; bande sombre fine au coude gauche dans B.

## Contrôle
- `output/v2/comparaison.jpg`, `output/v2/zoom200_*.jpg`
- `output/v2/avant-apres_v1-v2_oreille_coeurs.jpg`, `output/v2/avant-apres_v1-v2_cheveux.jpg` (en haut v1, en bas v2 ; à gauche A, à droite B)
