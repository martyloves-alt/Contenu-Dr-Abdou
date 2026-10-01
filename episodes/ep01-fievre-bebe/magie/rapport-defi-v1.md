# Épisode 1 — exercice « magique » v1 : défi « Arrête l'image »

**Export :** `out/defi_v1.mp4`, **13,0 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −2,6 dBFS), 9,5 Mo. **Rien n'a été publié.**
Script : `magie/defi_v1.py`. Modèle : la vidéo « Saved-8093 » (poule / pomme / Fanta / lézard).

## Ce que fait le modèle, et ce que j'ai reproduit
| Modèle | v1 |
|---|---|
| 4 objets détourés, cerclés de rouge, en losange, fond bleu très pâle | 4 **vraies poses d'Abdou** tirées des rushes de l'épisode 1 : **TDR** devant le visage, **thermomètre** au poing, **boîte de paracétamol**, **doigts levés** |
| Chaque objet coupé en deux : une moitié reste dans son contour, l'autre voyage d'un emplacement à l'autre en tournant sur elle-même | Pareil : les têtes, mains et objets passent d'une silhouette à l'autre (tête du TDR sur le corps du paracétamol, etc.) |
| Icône « pause » rouge en haut à droite | Pareil (pastille rouge « pause ») |
| Voix : « One of the hardest challenges in the world. I challenge you to stop the picture. » | Les 2 notes d'Abdou du 01/10, mot pour mot : « L'un des défis les plus difficiles au monde. » / « Je vous mets au défi d'arrêter l'image. » (accélérées ×1,2, comme les notes de l'épisode 1). Vérifié par transcription de l'export. |
| Musique | Marimba synthétisée (aucun droit à gérer), calée sur les déplacements, plus un tic à chaque emplacement |

## Le défi est réellement faisable (vérifié image par image)
- 0 à 1 s : les 4 poses sont entières et immobiles, pour que le spectateur voie la cible.
- Ensuite, les 4 poses sont entières sur **une seule image toutes les 2 s** : à **3,0 s, 5,0 s, 7,0 s, 9,0 s, 11,0 s et 13,0 s** (images 90, 150, 210, 270, 330, 390, listées dans `out/defi_v1_alignements.json`). Une image avant ou après, au moins une moitié est décalée ou penchée.
- Aucun son particulier au moment de l'alignement, pour ne pas donner la réponse.
- La vidéo finit sur un alignement et recommence sur les poses entières : la boucle TikTok est propre.

## Fait honnête sur la technique
- Les détourages sont faits par un modèle qui **enlève le fond** (rembg, `u2net_human_seg`). Il ne génère aucune image : tout ce qu'on voit a été filmé.
- Le découpage des moitiés, les rotations et les contours sont du montage.

## ⚠️ Limites (à connaître avant validation)
1. **Netteté** : les rushes de l'épisode 1 sont des exports CapCut en 480p. Les bustes restent corrects à cette taille, mais moins nets que les objets « studio » du modèle. Les originaux du téléphone donneraient un rendu bien meilleur.
2. **Bustes coupés à plat en bas** : les rushes coupent Abdou à mi-corps, donc le contour rouge a un bord droit en bas, comme un sticker.
3. **Pose TDR** : l'avant-bras qui tient le test entre par le bord de l'image, il apparaît coupé et pâle.
4. **Pose thermomètre** : le poing cache une partie du visage (c'est la vraie prise).
5. **Phrase 3 du modèle absente** : « If you can stop it, take a screenshot and send it to us » n'a pas de version française enregistrée. Je ne l'ai donc **ni ajoutée en texte, ni inventée**. Si Abdou veut l'appel à l'action, une note suffit, par exemple : « Si tu y arrives, fais une capture d'écran et envoie-la-nous. »
6. **« Je vous mets au défi »** : vouvoiement, alors que l'épisode 1 tutoie. C'est cohérent dans cette vidéo seule, à harmoniser si tu veux le même ton partout.
7. **Pas de lien santé** : l'exercice montre le thermomètre, le paracétamol et le TDR, mais ne dit rien de médical. C'est volontaire : aucune information médicale ajoutée. L'algorithme n'est pas garanti : ce format pousse aux pauses, aux revisionnages et aux commentaires, mais je ne peux pas promettre qu'il « explose ».

## Pistes pour une v2 (à décider)
- Accélération progressive : un premier cycle lent, puis de plus en plus vite.
- Remplacer une pose par un objet filmé seul en gros plan (thermomètre, boîte), si Abdou en filme un sur fond uni.
- Ajouter la phrase 3 enregistrée par Abdou.
