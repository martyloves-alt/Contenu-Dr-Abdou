---
name: maj-classeur-editorial
description: Mise à jour hebdomadaire du classeur éditorial du Dr Abdou (sujets candidats, messages validés, erreurs CNHU, questions DM, épidémies) avec des contenus déjà décidés. Utiliser quand l'utilisateur dit « mets à jour le classeur », « ajoute au classeur » ou fournit des lignes à saisir.
---

# Mise à jour du classeur éditorial

But : saisir des contenus **déjà validés** par le Dr Abdou, au mot près, sans rien ajouter.

## Étapes
1. **Ouvrir le fichier de référence** : Google Sheets « Classeur Éditorial Dr Abdou » (lien dans `CLAUDE.md`). Si plusieurs fichiers portent un nom proche, demander lequel.
2. **Lire les 6 onglets** (en-têtes + lignes existantes + légendes) avant d'écrire.
3. **Comparer les colonnes** fournies avec les en-têtes réels. Le moindre écart de nom → une seule question regroupée à l'utilisateur, **avant** d'écrire.
4. **Lignes d'exemple** (jaunes, « Exemple fictif ») : demander s'il faut les supprimer ou les garder sous les vraies lignes, si ce n'est pas déjà dit.
5. **Écrire** :
   - texte exact, dates en texte `AAAA-MM-JJ` (empêcher la conversion automatique en date) ;
   - nouvelles lignes au-dessus de la légende, sans écraser la légende ni les formules ;
   - style normal (pas le jaune ni l'italique des exemples) ;
   - onglets pour lesquels l'utilisateur dit « ne rien ajouter » : ne pas y toucher.
6. **Règle chiffres** : dans « Message validé », aucun chiffre médical en dehors du texte fourni. Statut par défaut : « À vérifier ».
7. **Vérifier** : relire le fichier enregistré et comparer **cellule par cellule** au texte fourni ; vérifier que les onglets non concernés sont identiques à avant.
8. **Rendre compte** : dire ce qui a été ajouté par onglet, les écarts signalés, et donner le lien.

## Écriture selon les outils disponibles
- Connecteur Google Sheets actif → modifier le Google Sheets **en place** (même lien).
- Sinon → ne pas créer de copie sans le dire : demander à l'utilisateur d'activer le connecteur Google Sheets, ou proposer une copie `.xlsx` en expliquant qu'elle crée un deuxième fichier.
- Ne jamais mettre un fichier à la corbeille sans demande explicite.
