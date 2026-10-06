# Épisode 2 — V1 du nouveau style « process » (montage v4)

**Export :** `out/ep02_montage_v4.mp4`, **39,5 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −4,0 dBFS). **Rien n'a été publié.**
Script : `montage_ep2_v4.py`. Modèle : `Video_1859758211849536.mp4`.

## 1. Ce que fait la vidéo modèle (vérifié image par image)
- Une fabrication filmée étape par étape (barbecue en béton) : caméra presque fixe, plans accélérés, fondus enchaînés, plan final « récompense » avec un zoom lent.
- **Aucune parole** : la transcription ne détecte aucune langue. C'est de la musique seule.

## 2. Analyse du scénario proposé

| Point du scénario | Verdict |
|---|---|
| Accroche d'une phrase, puis manipulations du TDR pendant qu'Abdou parle | ✅ Faisable avec les rushes : 15 plans 4K du vrai test (mains gantées), dans l'ordre |
| Manipulations accélérées ×1,6 / ×1,8 | ✅ ×1,7 |
| Parole accélérée ×1,5 ou ×1,8 | ⚠️ **×1,5 retenu, ×1,8 rejeté** : à ×1,8, la transcription perd des informations médicales (« dans les 24 heures » disparaît, « fais-le boire » devient « taille le bois »). Le bloc des signes d'urgence passe à **×1,3** : à ×1,5, « dort trop » devient inintelligible |
| Ralenti « immersion » | ✅ Sur la goutte de tampon (×0,5). Les rushes sont en 30 i/s : les images intermédiaires sont **calculées** (interpolation), sans aucun ajout de contenu |
| Zooms sur les plans statiques | ✅ Zoom lent sur chaque plan, et un recadrage alterné à chaque coupe sur le visage |
| « Cabinet pédiatrique moderne, fenêtre, dossiers flous » | ❌ **Ce décor n'existe pas dans les rushes** (pièce carrelée blanche, table en bois). Le créer serait de la génération par IA, ce qui n'est ni validé ni honnête |
| « 16K HDR, 244 fps, objectif 50 mm f/1.8, faible profondeur de champ » | ❌ **Impossible** : c'est un prompt de génération d'images, pas un réglage de montage. Les rushes sont en 4K 30 i/s (manipulations) et en 720p (visage). On ne peut pas créer de détail ni d'images qui n'ont pas été filmées |
| « Parle rapidement » + « regard très doux, pauses émotionnelles » | ⚠️ Contradictoire : accélérer la voix enlève justement les pauses. Et on ne peut que monter les prises existantes, pas changer le jeu d'Abdou |
| Piano type *Interstellar* | ❌ Musique protégée. J'ai **synthétisé** un piano doux (la m – fa – do – sol, réverbération, légère montée vers la fin). Pour un vrai piano, choisis un son de la bibliothèque TikTok au moment de publier |
| Ambiance sonore de cabinet | ❌ Non enregistrée, je ne l'invente pas |
| Sous-titres français + anglais | ✅ Le français reprend les mots exacts d'Abdou. **L'anglais est ma traduction : à faire valider** (tableau ci-dessous) |

## 3. Structure de la V1

| Temps | Image | Voix |
|---|---|---|
| 0–2,9 s | Visage plein écran (4K) | Accroche |
| 2,9–6,6 s | Manipulations plein écran + **vignette visage** : boîte de TDR → boîte d'antipaludéen (marque floutée) → plateau → ouverture du sachet | « L'erreur classique… » |
| 6,6–14,9 s | Visage plein écran | « …tu perds un temps précieux. Trois bons réflexes… » |
| 14,9–17,8 s | Manipulations + vignette : test posé → sang → **goutte de tampon au ralenti** | « Puis… dans les 24 heures pour le TDR » |
| 17,8–23,7 s | Migration → résultat filmé (flèche + **NÉGATIF · NEGATIVE**) → photo d'un autre test (2 flèches + **POSITIF · POSITIVE**, étiquette EXEMPLE) | Note vocale « un point / deux points » |
| 23,7–35,8 s | Visage plein écran, sauf « à moins de 3 mois » : carton **MOINS DE 3 MOIS · UNDER 3 MONTHS** (note vocale, aucune image d'Abdou ne dit « 3 ») | Résultats, urgences |
| 35,8–39,5 s | Visage plein écran, doigt vers le bas | Appel au commentaire |

## 4. Traduction anglaise à valider
| Français (mots d'Abdou) | Anglais |
|---|---|
| Tu soupçonnes le palu chez ton enfant ? | Do you suspect malaria in your child? |
| Ne fais SURTOUT PAS ça en premier ! | Whatever you do, DON'T do this first! |
| L'erreur classique : lui donner un antipaludéen sans faire le test. | The classic mistake: giving an antimalarial without testing. |
| Si c'est une autre maladie, tu perds un temps précieux. | If it's another illness, you're losing precious time. |
| Trois bons réflexes. | Three good reflexes. |
| Un : note l'heure du début de la fièvre. | One: note when the fever started. |
| Deux : fais-le boire, ou allaite-le. | Two: give fluids, or breastfeed. |
| Trois : paracétamol pour son confort, et à la bonne dose. | Three: paracetamol for comfort, at the right dose. |
| Puis, allez au centre de santé le plus proche dans les 24 heures pour le TDR. | Then go to the nearest health centre within 24 hours for a rapid test (RDT). |
| Là où vous voyez un point, c'est que le test est négatif. | Where you see one dot, the test is negative. |
| Et là où vous voyez deux points, c'est que le test est positif. | And where you see two dots, the test is positive. |
| Si TDR positif : traitement complet, jusqu'au bout. | Positive test: full treatment, right to the end. |
| Si TDR négatif : cherchez une autre cause. | Negative test: look for another cause. |
| Mais s'il convulse, ne tète plus, vomit tout, dort trop, à moins de 3 mois, allez aux urgences tout de suite. | But if the child has seizures, won't breastfeed, vomits everything, sleeps too much, or is under 3 months old, go to the emergency room right away. |
| Sois honnête : tu lui as déjà donné un antipaludéen « au cas où » ? Dis-le-moi en commentaire. | Be honest: have you ever given an antimalarial "just in case"? Tell me in the comments. |

## 5. ⚠️ Limites et points ouverts
1. **Toujours pas corrigé (audit du 30/09)** : la voix dit « vous » / « allez » / « cherchez » et « point » au lieu de « trait ». La feuille de réenregistrement est dans `rapport-montage-v3.md`. Dès réception des notes, je les intègre.
2. **Intelligibilité à ×1,5** : « le plus proche dans les 24 heures » et « Deux : fais-le boire » sont limites à la transcription automatique, alors qu'ils passaient à ×1,18. Les sous-titres affichent le texte exact. **Écoute ces deux passages** ; si besoin, je les passe à ×1,3.
3. **Visage en 720p (WhatsApp)** : en plein écran, il est moins net que les manipulations en 4K. Les fichiers originaux du téléphone régleraient ça.
4. **Vignette « en même temps »** : Abdou n'a pas été filmé en train de parler pendant les manipulations. La vignette montre ses prises face caméra en même temps que ses mains : c'est un montage, pas une prise unique.
5. **Le ralenti est interpolé** : il est propre sur ce plan, mais des déformations peuvent apparaître sur les mouvements rapides. Un tournage en 60 ou 120 i/s donnerait un vrai ralenti.
6. **Photo du test positif** : c'est un autre test (P.f/Pan), donc étiqueté EXEMPLE. Rappel des nuances médicales, à la décision d'Abdou : sans trait C, le test est invalide ; un test P.f/Pan peut afficher 3 traits.
