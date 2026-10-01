# Épisode 1 — exercice « magique » v5 : boucle continue

**Exports** (13,9 s, 1080x1920, 30 i/s, −14,0 LUFS). **Rien n'a été publié.**
- `out/defi_v5.mp4` : avec le son choc, la voix d'Abdou et les sous-titres.
- `out/defi_v5_muet.mp4` : sans son choc, sans voix, sans sous-titres. Il reste la musique et les bips.

Script : `magie/defi_v5.py` (variante : `python3 defi_v5.py --muet`).

## Changements par rapport à la v4
- Message « Écris gagné en commentaire » **retiré**.
- **Plus d'intro immobile ni de zoom d'ouverture** : le mouvement démarre dès la 1re image, qui est un alignement (c'est aussi la miniature).
- **Vitesse en aller-retour** :

| Cycle | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Vitesse | 1,61× | 1,86× | 2,16× | 2,51× | 2,70× | 2,40× | 2,04× | 1,74× |

  Puis la boucle repart à 1,61× : environ 8 % d'écart au raccord, contre un saut de 2,7× à 1,6× en v4.
- **Raccord sans couture** : la dernière image (417, « Presque ! ») précède directement l'image 0 (alignement). Il n'y a ni image en double, ni saut de position, ni saut de rotation. Vérifié image par image : 415 → 416 → 417 → 0 → 1 → 2.
- Le doigt qui appuie sur la pause clignote du début à la fin. Un bip tombe à chaque passage d'emplacement, y compris au raccord.
- Alignements : images 0, 67, 125, 175, 218, 258, 303, 356 (`out/defi_v5_alignements.json`). « Presque ! » s'affiche sur l'image qui précède chacun d'eux.

## Ce qui trahit encore le recommencement
- **Version complète** : le son choc et la voix repartent à chaque boucle, donc la reprise s'entend, même si l'image raccorde parfaitement.
- **Version muette** : rien ne marque la reprise. En contrepartie, il n'y a plus d'accroche sonore ni de consigne dite par Abdou ; seul le doigt sur la pause indique quoi faire.
