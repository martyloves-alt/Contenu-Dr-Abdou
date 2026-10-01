# Épisode 1 — exercice « magique » v4 : défi « Arrête l'image » optimisé

**Export :** `out/defi_v4.mp4`, **14,9 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −3,4 dBFS), 10 Mo. **Rien n'a été publié.**
Script : `magie/defi_v4.py`. Base : la v3 (son choc, accélération 1,6× → 2,7×, TDR filmé seul).

## Analyse du plan d'optimisation reçu le 01/10

| Point du plan | Verdict | Ce que j'ai fait |
|---|---|---|
| Gros texte jaune / blanc, ombre noire | ✅ Retenu | Sous-titres style TikTok (majuscules, mots clés en jaune, contour et ombre noirs), **avec les mots exacts d'Abdou** |
| « 99 % DES GENS ÉCHOUENT 😱 » | ❌ Rejeté | Statistique inventée, sans aucune donnée. C'est le genre d'affirmation qui décrédibilise un compte médical |
| « TEST DE RAPIDITÉ ULTIME ⏱️ » | ❌ Non ajouté | Pas faux, mais ce serait un 3e texte dans les 2 premières secondes, en plus de la voix |
| Punch-in au démarrage | ✅ Retenu | Zoom 1,12 → 1 sur les 0,4 premières secondes |
| Impact / whoosh au départ | ✅ Déjà fait | Le son choc de la v3 remplit ce rôle (le plan dit « à la place ou en complément ») |
| Remplacer le texte par « FAIS UN SCREENSHOT AU BON MOMENT 📸 » | ❌ Rejeté tel quel | Ce n'est pas ce que dit Abdou (« arrêter l'image »), et le sous-titre doit suivre sa voix. Une capture d'écran demande aussi beaucoup plus de réflexes qu'une pause |
| Pictogramme clignotant pour les spectateurs sans le son | ✅ Retenu, adapté | Un doigt 👆 qui appuie, en clignotant, sous l'icône pause, à partir de la phrase 2 et jusqu'à la fin |
| Contours plus nets et plus beaux | ✅ Retenu | Style sticker : silhouette lissée, bord blanc, trait rouge anti-crénelé, ombre douce. Les emplacements vides apparaissent en blanc, ce qui rend la forme à compléter plus lisible |
| Une seule image gagnante exacte | ✅ Déjà vrai | 1 image par cycle (0,033 s), sans chevauchement : images 97, 159, 216, 269, 318, 363, 405, 445 (`out/defi_v4_alignements.json`) |
| « Presque ! Recommence 😂 » juste avant l'image gagnante | ✅ Retenu | Sur l'image qui précède **chaque** alignement (96, 158, 215…). Ça ne gêne pas le jeu : l'image gagnante reste intacte juste après |
| Bips de suspense qui accélèrent | ✅ Retenu | Un bip à chaque déplacement, à la place des tics. Ils accélèrent avec le défi |
| Appel au commentaire 11 → 14 s | ✅ Retenu, déplacé | « Écris « gagné » en commentaire si tu as réussi ! 👇 » apparaît à 11 s, **en haut** et non en bas : le bas de l'écran TikTok est couvert par la légende et les boutons |
| Boucle parfaite | ⚠️ En partie | Visuellement, c'est déjà le cas : la dernière image est un alignement, identique au début. Mais à chaque boucle, le son choc et la voix repartent, donc le spectateur voit que ça recommence. On ne peut pas avoir à la fois une accroche sonore forte et une boucle invisible : j'ai gardé l'accroche |

## Points à vérifier par toi
- L'appel au commentaire est un **texte écrit, pas dit** par Abdou, et il tutoie (« Écris »), alors que la voix vouvoie (« Je vous mets au défi »).
- « Presque ! Recommence » n'est visible que si on met pause à cet instant. En lecture normale, 1 image passe inaperçue, et c'est voulu.
