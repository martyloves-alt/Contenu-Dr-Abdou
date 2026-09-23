# Épisode 1 : montage v3 — réorganisation demandée (ton ordre exact)

**Export :** `out/ep01_montage_v3.mp4`, **20,3 s**, 1080x1920, 30 i/s. **Rien n'a été publié.**
Script : `montage_v3.py`. Réutilise le moteur de `montage_v2.py` (silences coupés, rendu, audio), seule la liste des blocs et le calque changent.

## L'ordre appliqué, exactement comme demandé

| Bloc | Ce que tu dis | Image |
|---|---|---|
| **Accroche** (0,0–4,7 s) | « Fièvre chez votre bébé ? Ce n'est pas la dentition. Piège 1 : croire aux dents. Les dents ne donnent pas de forte fièvre. » | Visage → flash (main sur l'objectif) → thermomètre **38,3°C** net et immédiat |
| **Faux-ami** (4,7–8,0 s) | « Piège 3 : le paracétamol. Il fait baisser la fièvre… » *(coupé avant « il ne soigne pas le palu »)* | Badge « PIÈGE N°3 » dans la paume → boîte posée → retour au visage |
| **Urgence** (8,0–12,1 s) | « Mais ton enfant convulse, vomit tout, fait la diarrhée : va aux urgences. » | Geste de balayage + carte rouge « URGENCES » |
| **Délivrance** (12,1–16,2 s) | « Le test le dit : le TDR. Palu ou la goutte épaisse. Pensez plutôt PALU. » | Balayage → TDR → bandeau « PALUDISME » |
| **Engagement** (16,2–20,3 s) | « Chez toi, on dit quoi quand le bébé chauffe ? Dis ça en commentaire. » | Visage, aucune bannière |

## Les 3 points de ton audit, un par un

1. **Hook qui ouvrait sur « piège n°3 » :** supprimé. La vidéo démarre directement sur « Fièvre chez votre bébé ? Ce n'est pas la dentition. »
2. **Bip / « ??? » qui ressemblait à un bug :** supprimé entièrement. Avec ce nouvel ordre, le mot « palu » n'est **tout simplement jamais prononcé** avant la révélation à 13,5 s (je l'ai vérifié : transcription automatique de l'audio final, aucun « palu » avant ce point). Le suspense vient de la coupe en plein milieu de ta phrase sur le paracétamol, pas d'un artifice visuel.
3. **CTA avant la révélation :** inversé. Le TDR et « PALUDISME » arrivent maintenant à 13,5 s, l'appel au commentaire seulement après, à 16,3 s.

## Deux bugs trouvés et corrigés avant de te l'envoyer

En vérifiant image par image (comme la dernière fois) :
- Le plan de la boîte de paracétamol s'étirait trop longtemps et tombait sur l'**écran de fin CapCut** (logo visible, image noire) parce que ce bout de rush ne dure réellement que ~1,7 s. Corrigé : le plan est maintenant coupé avant, et on revient à ton visage pour la fin de la phrase.
- Le bandeau « PALUDISME » restait affiché jusqu'à la toute fin de la vidéo, y compris pendant l'appel au commentaire. Corrigé : il disparaît maintenant peu après la révélation, avant que la partie suivante ne commence.

## Ce qui a disparu de cette version (à valider, c'est un choix éditorial, pas un bug)

Pour tenir ton ordre en 5 blocs courts, deux passages du script validé ne sont plus dans la vidéo :
- **Le Piège 2** (« Au Bénin, un enfant fiévreux, on cherche d'abord le palu… en 24 heures, il peut devenir grave. ») — le rush correspondant (avec le chrono 24 H) n'apparaît plus du tout.
- **Le début de la partie action** (« Ton enfant fait la fièvre ? Test au centre de santé. ») — je n'ai gardé que la suite (« Mais ton enfant convulse… va aux urgences »).

Comme ce sont des informations médicales validées par toi, je ne les ai pas retirées de mon propre chef sans te le signaler : dis-moi si c'est voulu (vidéo plus courte et plus percutante) ou s'il faut les remettre quelque part.

## Toujours en attente pour l'export final

- Vidéos originales du téléphone (les rushes actuels sont des exports CapCut 480p avec logo, recadré).
- Paramètres Make.com / Creatomate et cible LUFS (actuellement −13,1 LUFS, provisoire).
