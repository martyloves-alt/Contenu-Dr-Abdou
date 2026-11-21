# Contenu Dr Abdou — mémoire du projet

Ce fichier est lu automatiquement au début de chaque session Claude Code sur ce dépôt.
Il remplace le « copier-coller du contexte » : on peut parler directement.

## Qui
- Dr Abdou, pédiatre au Bénin (consultations au CNHU).
- Compte : @conseils_de_dr_abdou — TikTok, Facebook, Instagram.
- Langue de travail : français. Tutoiement dans les vidéos, vouvoiement possible à l'écrit.

## Règles non négociables
1. **Ne rien inventer.** Pas de donnée, de chiffre, de citation ni de source de mon cru.
2. **Textes validés = texte exact.** Quand le Dr Abdou fournit un texte validé, le recopier mot pour mot, sans reformuler ni corriger le fond.
3. **Chiffres médicaux** (âge, température, dose, durée) : uniquement s'ils figurent dans l'onglet « Banque de Messages Validés » avec le statut **Validé**. Statut par défaut d'un nouveau message : **À vérifier**.
4. **Visuels :** jamais de substitut généré par IA pour un plan à filmer (carton « ASSET MANQUANT » à la place), sauf accord explicite et mention visible.
5. **Rien n'est publié** sur les réseaux sans accord écrit du Dr Abdou.
6. Si une colonne, un nom de fichier ou une consigne ne correspond pas exactement : **demander avant de deviner**.

## Classeur éditorial
- Fichier de référence (Google Sheets) : « Classeur Éditorial Dr Abdou »
  https://docs.google.com/spreadsheets/d/1i_zDylRC2dDsHPHFJ4HLUNeYwbqwf2BZ3YykJb50MiQ/edit
- 6 onglets : Sujets candidats · Historique Engagement · Banque de Messages Validés · Erreurs CNHU · Questions DM · Épidémies Bénin.
- Méthode en maillons : le Maillon 2 note les sujets candidats (scoring sur 30), le Maillon 3 rédige en ne citant que des messages validés.
- Mise à jour hebdomadaire : utiliser le skill `maj-classeur-editorial`.
- Ne jamais mettre un fichier Drive à la corbeille sans demande explicite.

## Montage vidéo — travail en conversation
Le montage se fait **par petites étapes en discutant** : le Dr Abdou dit ce qu'il veut, Claude modifie, exporte un aperçu, et on recommence.
- Un dossier par épisode : `episodes/epNN-<sujet>/`.
- Chaque version : `montage_vN.py` (ou `montage_epNN_vN.py`) + `rapport-montage-vN.md` (ce qui a changé, points à vérifier).
- Exports dans `out/` (non versionné) : fichier final + `_apercu.mp4` léger pour l'envoi sur téléphone.
- Les rushes vont dans `episodes/*/assets/` (non versionné) : ils disparaissent à la fin de la session cloud. Les garder sur Google Drive et les redéposer au besoin.
- Une seule modification demandée = une nouvelle version. Ne jamais écraser une version déjà validée.
- Voix intacte : vérifier par transcription après chaque export ; viser −14 LUFS.
- Effets « talking-head » : skill `effects` (dans `.claude/skills/effects`).
- Fin de chaque étape : dire en 2–3 lignes ce qui a changé et quoi regarder dans l'aperçu.

## Fin de session
Commiter et pousser le travail (scripts et rapports) avant de quitter : le conteneur cloud est effacé ensuite.
