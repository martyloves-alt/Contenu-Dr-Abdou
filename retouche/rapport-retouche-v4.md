# Retouche photo portrait — v4 (version A, cadre d'origine)

Choix du Dr Abdou (via l'utilisateur) : décor parasite EFFACÉ (mur et table reconstitués), agrandissement x2 classique, finition naturelle et chaude.
**Mention à faire en cas de diffusion : « décor retouché ».**

Scripts : `python3 retouche/v4_version_A.py` puis `python3 retouche/v4_controle.py`. Sorties : `output/v4/`.
Fichier final : `DrAbdou_portrait_A_v4.jpg` / `.png` — 1522 × 1528 (cadre d'origine sans bandeau, x2 Lanczos, sans IA).

## Erreur corrigée : oreille coupée (v1 à v3)
Le masque isnet s'arrêtait au milieu de l'oreille (lobe posé devant un cœur rouge) ; l'effacement des cœurs a donc
remplacé le bas de l'oreille par du mur. v4 : le lobe (x 462–489, y 200–242) est repris du masque u2net, sans le rouge
vif du cœur, silhouette arrondie, excès de rouge du bord retiré. 186 pixels de lobe rendus au sujet.

## Pourquoi v1–v3 n'étaient pas beaux (analyse revue)
1. Agrandissement ×2,5 avec Real-ESRGAN sur une petite photo compressée → texture « peinte ». v4 : Lanczos ×2 seulement.
2. Cadrage buste trop serré → posture perdue. v4 : cadre d'origine.
3. Couleurs : mur lavande froid, blancs grisés par l'épaule de courbe. v4 : mur gris clair neutre, blancs laissés blancs, peau légèrement réchauffée, relief doux du visage, vignettage léger.
4. Liseré autour de la tête, mur trop lisse → effet découpé. v4 : bord recoloré depuis le sujet, grain de la photo ajouté au fond.

## Décor reconstitué (inventé, avec accord)
- Mur : modèle lisse ajusté sur le mur propre, dominante lavande réduite de 75 %, grain mesuré.
- Table : couleur bois mesurée entre le bras et les papiers (LAB ≈ 231/131/150), bord arrière y≈700→672, veines très douces, ombre de contact sous les avant-bras.
- Supprimés : 2 chaises, bras de la personne voisine, papiers, tissu à motifs, cœurs.

## Masque du sujet
- Contour plus franc (moins de semi-transparence), bas des avant-bras lissé, bouts de papier blanc retirés (bracelets protégés).
- Creux entre bras droit et buste : le mur vu à travers rendu au fond (1943 px, par couleur et connexité).

## Reste imparfait
- Le contact bras/table est reconstitué : sous l'avant-bras gauche, la limite reste un peu nette.
- La table est unie (pas de vraie texture de bois).
- Le t-shirt reste blanc pur sur 70 % de sa surface (écrêté dans l'original, irrécupérable).
