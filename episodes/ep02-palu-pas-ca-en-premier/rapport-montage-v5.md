# Épisode 2 — style « process », V2 (montage v5)

**Export :** `out/ep02_montage_v5.mp4`, **39,7 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −3,9 dBFS), 28,7 Mo. **Rien n'a été publié.**
Script : `montage_ep2_v5.py`.

## 1. Le décalage voix / image : cause et correction
- **Cause (bug de ma part dans la v4)** : le filtre de zoom lent produit une image pour chaque image source et ignorait l'accélération. Les plans (visage et inserts) défilaient à vitesse normale alors que la voix était à ×1,5, donc le décalage grandissait dans chaque plan, du début à la fin.
- **Correction** : la cadence est fixée avant le zoom, donc l'image accélère exactement comme la voix.
- **Vérification objective** :
  - **Image** : à 6 instants (accroche, réflexes ×2, résultats, urgences ×2), j'ai comparé l'image exportée à l'image source attendue et aux images voisines (±0,1 à ±0,4 s). La meilleure correspondance est à l'écart 0 dans 5 cas, et à 0,1 s près dans le 6e (urgences).
  - **Voix** : d'après la transcription de l'export, chaque sous-titre démarre à ±0,13 s du mot prononcé.

## 2. Tes 4 nouvelles notes (06/10), intégrées mot pour mot
| Note | Texte (transcription vérifiée) | Où |
|---|---|---|
| WA0020 | « Puis va au centre de santé le plus proche dans les 24 heures pour le TDR. » | remplace « Puis, allez… » |
| WA0021 | « Là où tu vois un trait, c'est que le test est négatif et là où tu vois deux traits, c'est que le test est positif. » | remplace « vous voyez un point… » |
| WA0022 | « Cherche une autre cause. » | remplace « cherchez une autre cause » |
| WA0022 (suite) | « Va au centre de santé le plus proche. » | **non utilisée**, voir § 4 |
| WA0023 | « Et toi, sois honnête, c'est quoi le sirop que tu caches toujours au frigo au cas où ? Dis-le-moi en commentaire, je te dirai si c'est dangereux. » | nouvel appel au commentaire |

- Les notes sont accélérées ×1,5 comme le reste (la v4 les accélérait en réalité ×1,8).
- Une pause de 1,4 s avant « Dis-le-moi » a été retirée : elle ne contient que du silence et un clic, aucun mot à la transcription.

## 3. Le plan de corrections, point par point
| Point | Verdict | Ce qui a été fait |
|---|---|---|
| 1. Approche caméra dès la 1re seconde, **refilmer en 4K 60 i/s (Galaxy S25)** | ✅ partiel | Je ne peux pas refilmer. J'ai simulé un **mouvement d'approche** (zoom avant 1,30 → 1 en 0,8 s) sur la prise 4K. Un vrai travelling filmé serait plus fluide et plus naturel |
| 1. Whoosh / riser sur « Ne fais SURTOUT PAS ça » | ✅ | Riser synthétisé (pas la bibliothèque CapCut) **qui se termine juste avant** « Ne fais », pour ne pas couvrir le mot |
| 2. Supprimer le split-screen | ✅ | Plus de vignette : alternance franche visage plein écran / insert plein écran |
| 2. Inserts très resserrés sur les mains | ✅ | Recadrage ×1,2 + zoom lent |
| 2. Lumière naturelle intense ou anneau lumineux | ⚠️ Au tournage | Juste, et ça ne se rattrape pas au montage : j'ai seulement ajouté un peu de lumière et un léger débruitage. Pour les prochains tournages, une lumière forte et douce sur les mains |
| 2. « Pop » sur 1, 2, 3 | ✅ | Pastilles jaunes 1, 2, 3 à côté du visage. Le pop tombe **0,12 s avant** le chiffre (un pop pile sur le mot masquait « Deux » dans un montage précédent) |
| 3. Tutoiement + « trait » | ✅ | Grâce à tes notes WA0020, WA0021 et WA0022 |
| 4. « à moins de 3 mois » → « a moins de 3 mois » | ✅ L'audit a raison | Dans la phrase « s'il convulse, ne tète plus, vomit tout, dort trop, **a** moins de 3 mois », c'est le verbe avoir, comme dans le script validé. Sous-titre et carton corrigés |
| 4. Mots-clés d'urgence un par un, synchronisés | ✅ | CONVULSE → NE TÈTE PLUS → VOMIT TOUT → DORT TROP → (carton 3 mois) → URGENCES, en français et en anglais, au-dessus de la tête |
| 4. Couper la musique + battement de cœur | ✅ | Battement de cœur sourd sur tout le bloc urgences (il n'y a plus de musique, voir point 5) |
| 5. Musique « Trending » à 5–10 % à la publication | ✅ | **L'export ne contient plus de musique**, pour ne pas qu'elle se superpose à celle que tu ajouteras dans TikTok ou Instagram. Il reste la voix, le riser, les pops et le battement de cœur |
| 6. Appel au commentaire plus polarisant | ✅ | Ta note WA0023 |

## 4. ⚠️ À décider / à savoir
1. **« allez aux urgences tout de suite » est encore au vouvoiement** (prise vidéo WA0035). Ta note WA0022 contient aussi « **Va au centre de santé le plus proche** », mais je ne l'ai **pas** mise à la place : « urgences » et « centre de santé » ne sont pas le même message médical pour des signes de gravité. Si tu veux le tutoiement ici, il faut une note « **Va aux urgences tout de suite.** », ou bien que Abdou confirme que le centre de santé convient.
2. **Image pendant les nouvelles notes** : aucune vidéo d'Abdou ne dit ces phrases. Je les ai couvertes avec de vraies images du test :
   - « tdr » : le test en train d'être fait ;
   - « trait / traits » : le résultat filmé, puis la photo ;
   - « Cherche une autre cause » : le résultat négatif ;
   - appel au commentaire : la boîte Bimalaril (c'est un sirop, marque floutée), puis Abdou assis, bouche fermée, ce qui se lit comme une voix off.
3. **« Je te dirai si c'est dangereux »** engage Abdou à répondre au cas par cas dans les commentaires. C'est son choix, mais ça demande du temps et des réponses prudentes (sans diagnostic à distance).
4. Le **visage reste en 720p** (WhatsApp). Les fichiers originaux du téléphone seraient plus nets.
5. Traduction anglaise : les nouvelles phrases sont ajoutées. À valider comme les autres (voir `rapport-montage-v4.md`).
