# Épisode 1 — exercice « magique » v3 : défi « Arrête l'image » + son choc

**Export :** `out/defi_v3.mp4`, **14,9 s**, 1080x1920, 30 i/s, −14,0 LUFS (crête −2,2 dBFS). **Rien n'a été publié.**
Script : `magie/defi_v3.py`. Base : la v2 (même image, même accélération 1,6× → 2,7×, même TDR filmé seul).

## Ce qui change
- **Son choc « Dark Horror » à l'ouverture (0 → 1,1 s)**, synthétisé, donc sans banque de sons ni droits. Il se compose de :
  - un impact grave qui chute (110 → 32 Hz) ;
  - un claquement sec ;
  - une frappe métallique dissonante ;
  - un accord grave dissonant ;
  - une courte réverbération.
- **La voix démarre à 0,55 s**, juste après le pic de l'impact (0,15 s en v2). Aucun mot n'est masqué : la transcription de l'export donne « L'un des défis les plus difficiles au monde. » puis « Je vous mets au défi d'arrêter l'image. ». Les sous-titres suivent la voix.
- **La marimba ne joue plus pendant le choc.** Elle démarre avec le mouvement (1 s), pour ne pas casser l'effet.

## Inchangé
Les 4 objets sont entiers sur une seule image à 3,23 s, 5,30 s, 7,20 s, 8,97 s, 10,60 s, 12,10 s, 13,50 s et 14,83 s (`out/defi_v3_alignements.json`). Les limites de la v2 restent valables : TDR filmé sur bois et issu du tournage de l'épisode 2, poses en 480p.
