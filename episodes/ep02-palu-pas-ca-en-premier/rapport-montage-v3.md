# Épisode 2 : montage v3 — style « After » + analyse de l'audit

**Export :** `out/ep02_montage_v3.mp4` (30 Mo), **49,2 s**, 1080x1920, 30 i/s, −14,4 LUFS (crête −4,5 dBFS). **Rien n'a été publié.**
Aperçu pour l'envoi : `out/ep02_montage_v3_apercu.mp4` (22 Mo). Script : `montage_ep2_v3.py`.

## 1. Analyse de l'audit (avant toute modification)

| # | Constat de l'audit | Verdict | Détail vérifié |
|---|---|---|---|
| 1 | « point » (voix) ≠ « trait » (écran / image) | **Juste** | La note vocale d'Abdou dit « point » ; le test montre des traits. Une petite erreur de citation : il dit « c'est que **le** test », pas « votre test ». |
| 2 | Tutoiement / vouvoiement mélangés | **Juste** | Les « vous » viennent de l'enregistrement, pas du script : le script validé est déjà au tutoiement ou neutre (« Puis centre de santé dans les 24 heures… », « Négatif : on cherche une autre cause », « urgences, tout de suite »). À l'enregistrement, c'est devenu « allez », « cherchez », « allez aux urgences », et la note ajoutée dit « vous voyez ». |
| 3 | Haut de l'écran partagé décalé du propos | **Partiellement juste** | Juste pour les 3 réflexes (le haut montre le sang et la migration) et pour les urgences (image du test assombrie et figée). Faux pour le piège : montrer le kit pendant « sans faire le test » est cohérent. De toute façon, la v3 abandonne l'écran partagé. |
| 4 | « 5 puces affichées d'un coup » | **Faux, mais la conclusion tient** | Les 5 lignes apparaissaient une par une, sur le mot prononcé (vérifié image par image). Mais à la fin, 5 lignes restaient empilées : trop chargé sur mobile. |
| 5a | « Ré-enregistrer 00:23–00:29 en disant trait » | **Juste** | Je ne peux pas changer ce qu'Abdou dit (aucune voix générée). Il faut qu'il réenregistre. |
| 5b | « Rends-toi au centre de santé » | **Correction du prompt** | Inutile d'inventer une nouvelle formulation : il suffit de reprendre **mot pour mot le script validé**, déjà au tutoiement (feuille ci-dessous). Toute autre formulation devrait être revalidée par Abdou. |

## 2. Ce que la v3 corrige déjà (sans réenregistrement)

Le montage suit le cadran **After** de la vidéo modèle :
- **Plein écran**, plus d'écran partagé. Le cadre change à chaque coupe (plan plus ou moins serré), avec un zoom lent.
- **Sous-titres mot par mot** sur la poitrine, en majuscules blanches. « Piège » et « paracétamol » restent en rouge.
- **Un seul mot-clé géant en haut**, qui s'écrit lettre par lettre (rouge = danger, jaune = à retenir, vert = négatif). Ce sont toujours des mots prononcés par Abdou.
- **Inserts plein écran** seulement quand l'image correspond au mot : la boîte (marque floutée) sur « antipaludéen », le kit sur « sans faire le test », le sang puis la migration sur « pour le TDR », le test filmé sur la lecture « négatif », la photo étiquetée EXEMPLE (AUTRE TEST) sur « positif ».
- **Stickers** en bas à gauche, comme les sacs et voitures du modèle : ⏳ ⏰ 🍼 🤱 💊 🏥 🚨 👇 🚫. Ce sont des emoji Noto (licence libre), pas des images générées.
- **Flashs lumineux** et whooshes courts aux transitions. Compteur « 0 → 24 H ».

Points de l'audit traités :
- **Audit 1** : l'écran ne dit plus « UN TRAIT / DEUX TRAITS ». Les flèches pointent les traits, avec NÉGATIF (vert) et POSITIF (rouge). Il n'y a plus de contradiction écrite ; la voix dit toujours « point » jusqu'au réenregistrement.
- **Audit 3** : chaque insert illustre le mot dit au même moment. Pour les réflexes et les urgences, le visage reste à l'écran avec un mot-clé et un pictogramme, à la place d'une image hors sujet.
- **Audit 4** : un seul signe de gravité à la fois (CONVULSIONS → NE TÈTE PLUS → VOMIT TOUT → DORT TROP), sur le mot prononcé.
- **Bonus** : « à moins de 3 mois » (note vocale) est couvert par un carton noir « MOINS DE 3 MOIS » 🚨. Le décalage des lèvres (qui disaient « 5 ») a disparu.
- **Ton image** : j'ai retiré le lissage de peau et le vignettage de la v2 (effet « cire », image grise). Les couleurs sont naturelles et légèrement plus chaudes. L'affinage de 4 % est conservé.

Contrôle du son : chaque passage a été retranscrit dans l'export final. En cours de route, deux problèmes sont apparus et ont été corrigés :
- les « pops » des mots-clés masquaient « Deux : fais-le boire » et « dort trop » : supprimés ;
- les whooshes ont été raccourcis pour tenir dans les coupures.

## 3. ⚠️ Ce qui reste (et qui ne dépend pas du montage)

1. **Tutoiement et « trait »** : à corriger au réenregistrement (feuille ci-dessous). Tant que ce n'est pas fait, la voix dit toujours « allez / vous voyez / cherchez » et « point ».
2. **Hésitation dans la note 2** (≈ 1,5 s entre « un point, c' » et « est que le test est négatif »). Elle est couverte par l'image du test, mais toujours audible. Le réenregistrement la supprime.
3. **Ton image** : en plein écran, la limite vient surtout des **vidéos WhatsApp (720p compressées)**, agrandies ×1,5 à ×1,9. Elles sont plus douces que le plan 4K de l'accroche. **Envoie les fichiers originaux du téléphone.** Et dis-moi précisément ce qui te déplaît (netteté ? angle ? affinage ? couleurs ?) : je corrigerai ce point-là.
4. **Durée 49,2 s** : le modèle fait 18 s, mais tout le contenu vient du script validé. Raccourcir voudrait dire retirer du texte validé, ce qui est la décision d'Abdou.
5. **Nuances médicales** non dites dans la vidéo, à la décision d'Abdou :
   - sans trait C, le test est invalide ;
   - le test de la photo (P.f/Pan) peut montrer 3 traits.

## 4. Feuille de réenregistrement pour Abdou (face caméra, même tenue, même lieu)

Les lignes A, B et C sont **mot pour mot le script validé le 30/09**, sans rien à revalider. La ligne D est une **proposition à valider** : la note d'origine est d'Abdou, je n'ai remplacé que « vous voyez un point » par « un trait ».

- **A.** « Puis centre de santé dans les 24 heures, pour le TDR. »
- **B.** « Négatif : on cherche une autre cause. »
- **C.** « Mais s'il convulse, ne tète plus, vomit tout, dort trop, ou a moins de 3 mois : urgences, tout de suite. »
- **D.** *(à valider)* « Un seul trait : le test est négatif. Deux traits : le test est positif. »

Une prise par ligne, 1 s de silence avant et après. Des notes vocales seules suffisent pour A, B et D : je les couvre avec les images du test. Pour C, une vidéo est préférable.
