# Épisode 1 — exercice « magique » v2 : défi « Arrête l'image »

**Export :** `out/defi_v2.mp4`, **14,9 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −3,0 dBFS). **Rien n'a été publié.**
Script : `magie/defi_v2.py` (la v1 reste disponible : `magie/defi_v1.py`).

## Changements demandés
### 1. Accélération progressive
Repère de vitesse : la v1 vaut 1,8×. La vitesse équivalente d'un cycle se calcule ainsi : 1,8 × 60 / (nombre d'images du cycle).

| Cycle | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Images | 67 | 62 | 57 | 53 | 49 | 45 | 42 | 40 |
| Vitesse | **1,61×** | 1,74× | 1,89× | 2,04× | 2,20× | 2,40× | 2,57× | **2,70×** |

- On démarre légèrement moins vite que la v1, comme demandé (1,6×), puis chaque cycle est environ 8 % plus rapide.
- La musique (une note par demi-déplacement) et les tics accélèrent avec le défi.
- **Toujours faisable, vérifié image par image :** les 4 objets sont entiers à 0–1 s, puis sur une seule image à **3,23 s, 5,30 s, 7,20 s, 8,97 s, 10,60 s, 12,10 s, 13,50 s et 14,83 s** (images 97, 159, 216, 269, 318, 363, 405, 445). La liste est dans `out/defi_v2_alignements.json`.
- Plus le défi accélère, plus ces moments sont rapprochés, mais plus ils sont durs à attraper.

### 2. Un objet filmé seul à la place d'une pose
La pose « TDR devant le visage » est remplacée par **le TDR filmé seul, posé sur la table** (rush 4K `IMG_4558`), détouré. C'était aussi la pose la plus faible de la v1 (avant-bras pâle et coupé).
- ⚠️ **Ce rush vient du tournage de l'épisode 2**, pas de l'épisode 1. Il n'existe **aucun objet filmé seul** dans les fichiers de l'épisode 1 : on y voit toujours les objets en main, en 480p.
- ⚠️ Il est filmé **sur une table en bois, pas sur fond uni**. Le détourage est propre, mais un vrai fond uni serait plus sûr.
- Le test affiché est celui du tournage (un seul trait). Aucun texte ne l'interprète, donc rien de médical n'est affirmé.

## Pour aller au bout de « l'objet filmé seul sur fond uni »
Si Abdou veut remplacer aussi d'autres poses, il faut **filmer chaque objet seul** :
- sur un fond uni et clair (drap, feuille A3 ou mur blanc), en lumière du jour, sans ombre forte ;
- téléphone stable, au-dessus ou en face, l'objet entier dans le cadre avec de la marge ;
- environ 3 s par objet, fichier original (pas d'export CapCut).

Objets utiles pour l'épisode 1 : **le thermomètre** et **la boîte de paracétamol**. Le fichier original du thermomètre `thermometre-38-3.jpg` coupe les deux bouts de l'objet.

## Inchangé depuis la v1
- Voix : les 2 notes d'Abdou, mot pour mot, accélérées ×1,2 (transcription de l'export conforme).
- Pas de son à l'alignement.
- Fin sur un alignement, donc la boucle est propre.
- Limites des 3 poses restantes (480p, bustes coupés à plat).
- La phrase 3 du modèle (capture d'écran) n'est toujours pas ajoutée, faute d'enregistrement.
