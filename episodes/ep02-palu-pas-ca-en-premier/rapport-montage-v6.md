# Épisode 2 — montage v6 = la v4 + les changements du 06/10

**Export :** `out/ep02_montage_v6.mp4` (31 Mo), **41,6 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −3,8 dBFS). Aperçu pour l'envoi : `out/ep02_montage_v6_apercu.mp4`. **Rien n'a été publié.**
Script : `montage_ep2_v6.py` (construit à partir de `montage_ep2_v4.py` ; tout ce qui n'est pas listé ici est identique à la v4).

## Changements demandés
1. **Cadence avant le zoom** : l'image accélère exactement comme la voix.
   - **Vérification** : à 8 instants (accroche, réflexes ×3, résultats ×2, urgences ×2), l'image exportée correspond à l'image source attendue avec un écart de 0 (comparé à ±0,1, ±0,2 et ±0,3 s).
   - **Sous-titres** : ils démarrent au plus à 0,16 s du mot entendu.
   - Les manipulations tournent maintenant vraiment à ×1,7. En v4, elles tournaient à ×1 à cause du même bug.
2. **Pastilles 1, 2, 3 de la v5**, avec un « pop » 0,12 s avant chaque chiffre.
3. **Appel au commentaire** : la note WA0023 sur la vidéo de la v4 (WA0034, Abdou assis).
   - Sur « sirop », **éclair de 0,4 s** sur la boîte de Bimalaril (marque floutée). « Quelques millisecondes » serait plus court qu'une image (1 image = 33 ms) : 0,4 s est le minimum pour que l'œil reconnaisse la boîte.
   - Sur « je te dirai si c'est dangereux », **la caméra suit la main d'Abdou vers le bas** (IMG_4569) : zoom progressif du visage vers la main.
4. **Piqûre ajoutée** (vidéo WA0026 reçue le 06/10). Elle est placée dans l'ordre réel : test posé → **lancette au bout du doigt** → sang sur le coton → goutte de tampon au ralenti. Le créneau total ne change pas.
5. Sous-titre « **a** moins de 3 mois » (verbe avoir, comme dans le script validé).

## Pourquoi la piqûre n'apparaissait pas avant
**Elle n'existait dans aucun rush reçu.** Les clips montrent la lancette tenue en main (IMG_4546), la compresse (4547), puis directement le coton avec la goutte de sang (4553). Il n'y avait ni patient, ni doigt, ni piqûre. La fiche de tournage (`script-final.md`) disait d'ailleurs « Pas de gros plan sur la piqûre ».

La vidéo WA0026 contient tout le geste : patient, désinfection du doigt, lancette décapuchonnée et piqûre. Seule la seconde de la piqûre est utilisée (29,1 → 30,4 s). La désinfection (10 → 17 s) reste disponible si tu veux un plan de plus.

## ⚠️ À savoir
1. **Lèvres pendant l'appel au commentaire** : la vidéo WA0034 date de l'ancienne phrase (« tu lui as déjà donné un antipaludéen… »), alors que la voix dit la nouvelle (« c'est quoi le sirop… »). Les deux commencent par « sois honnête », mais la suite ne correspond pas. C'est ce que tu as demandé (« on garde la vidéo de la v4 »). Si ça se voit trop, je peux mettre le plan d'Abdou assis bouche fermée (IMG_4568), qui se lira comme une voix off.
2. **Comme en v4, la voix dit encore « vous », « allez », « cherchez » et « point »** (tes notes au tutoiement WA0020 à WA0022 ne sont pas utilisées, puisque la v4 est gardée telle quelle). Dis-moi si tu veux les intégrer.
3. **WA0026 est une vidéo WhatsApp en 720p**, comme les visages. Elle est un peu moins nette que les autres manipulations, filmées en 4K.
4. **Piqûre à l'écran** : le geste est bref, mais certaines personnes y sont sensibles. TikTok l'accepte en contexte médical.
