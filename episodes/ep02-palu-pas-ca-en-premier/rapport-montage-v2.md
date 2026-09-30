# Épisode 2 : montage v2 — corrections d'Abdou intégrées

**Export :** `out/ep02_montage_v2.mp4` (31 Mo), **49,2 s**, 1080x1920, 30 i/s, −14,5 LUFS (crête −4,4 dBFS). **Rien n'a été publié.**
Aperçu < 30 Mo pour l'envoi : `out/ep02_montage_v2_apercu.mp4`. Script : `montage_ep2_v2.py`.

## Ce qui a changé par rapport à v1
1. **« À moins de 3 mois »** : la note vocale 1 (n1) remplace la phrase de WA0035 qui disait « 5 mois ». Vérifié par transcription de l'export final : « À moins de 3 mois, allez aux urgences tout de suite. »
2. **« Antipaludéen »** : conservé tel quel (confirmé par Abdou).
3. **Lecture du TDR** (note vocale 2, placée entre « …pour le TDR » et « Si TDR positif ») :
   - « Là où vous voyez un point, c'est que le test est négatif » → en haut, **le test filmé (1 seul trait, ligne C)**, flèche + bannière UN TRAIT / NÉGATIF ;
   - « Et là où vous voyez deux points, c'est que le test est positif » → en haut, **la photo (traits C + P.f)**, 2 flèches + bannière DEUX TRAITS / POSITIF + étiquette EXEMPLE.
   - Sous-titres = mots exacts de la note (« point », pas « trait »).
4. **Filtre** sur le visage (bas d'écran) : lissage léger de la peau, couleurs plus chaudes et plus contrastées, netteté, vignettage doux. Filtre plus léger sur le haut (mains, test).
5. **Visage affiné** : l'image du bas est comprimée de **4 % en largeur**.
6. **Cadrage « torse »** : tête entière en haut, épaules et torse dessous, pour une présence plus imposante. Le cadrage se base sur la position du visage détectée dans chaque plan.
7. **Réglages de l'épisode 1 repris** :
   - accélération ×1,18, avec ×1,2 en plus sur les notes vocales ;
   - une bannière à la fois ;
   - « piège » et « paracétamol » en rouge ;
   - zoom lent sur le visage ;
   - voix naturelle (pas de changement de hauteur) ;
   - silences coupés seulement s'ils sont mesurés entre deux mots ;
   - habillage sonore synthétisé comme dans l'épisode 1 ;
   - −14 LUFS visé.

## Corrigé pendant mon contrôle (avant envoi)
- **Mot « deux » masqué** : un whoosh et un « ding » tombaient pile sur « deux points », et un whoosh sur « Deux : fais-le boire ». Dans le mix, la transcription entendait « un point… positif », une erreur grave. Les whooshes se terminent maintenant avant le mot, et le ding a été retiré. J'ai aussi baissé les effets sous la voix et filtré la musique sous 250 Hz (elle masquait « fais-le boire » et « dans les 24 heures »). Vérifié : « Deux, fais-le boire ou allaite-le », « …le plus près dans les 24 heures pour le TDR », « …deux points, c'est que le test est positif ».
- **Premier cadrage trop serré** (front coupé) : refait, la tête est maintenant entière.
- **Flèche posée sur la bannière NÉGATIF** : la bannière est descendue sous le test, et la flèche pointe la ligne C.

## ⚠️ À vérifier à l'écoute / à décider
1. **Hésitation dans la note 2** : après « un point, c' », il y a environ 1,5 s avant « est que le test est négatif » (dans la note d'origine). Je ne l'ai pas coupée : la coupe risquait d'emporter le « c' ». Si ça s'entend comme une hésitation, dis-moi où couper à l'oreille, ou fais réenregistrer la note d'un trait.
2. **Synchronisation labiale sur « 3 mois »** : l'image vient de la prise d'origine, où Abdou disait « 5 mois ». Sur cette seconde, les lèvres ne correspondent pas exactement au son.
3. **Plans pendant la lecture du TDR** (bas d'écran) : pas de prise face caméra pour cette note, donc j'ai utilisé les gestes muets filmés (1 doigt, 2 doigts, doigt vers le haut). Sur IMG_4567, Abdou regarde vers le haut et est décentré. À remplacer si tu as mieux.
4. **Bannière « TRAIT » / voix « point »** : les bannières disent « UN TRAIT / DEUX TRAITS » (ce qu'on voit sur le test), la voix dit « point ». Dis-moi si tu préfères « UN POINT / DEUX POINTS » à l'écran.
5. **Nuances médicales non dites dans la vidéo** (je n'ajoute rien, à la décision d'Abdou) :
   - sans trait C, le test est **invalide** (à refaire) ;
   - la photo est un test P.f/Pan, qui peut montrer **3 traits**.
6. **Affinage** : c'est une compression globale de 4 % de l'image du bas (le décor aussi), pas une retouche du seul visage. Au-delà de 5 %, la déformation se voit.
7. **Netteté** : le recadrage « torse » agrandit les vidéos WhatsApp (720p compressées), ce qui les rend un peu moins nettes que le plan 4K de l'accroche. Les **fichiers originaux du téléphone** régleraient ça.
8. **Durée : 49,2 s** (41,5 s en v1), à cause de la lecture du TDR ajoutée.

## Toujours en attente
- Les originaux non compressés des 5 vidéos WhatsApp.
- Les paramètres Make.com / Creatomate et la cible LUFS définitive.
