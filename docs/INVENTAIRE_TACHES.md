# Inventaire des tâches

Engendré depuis le registre du plugin : une liste écrite à
la main périme au premier ajout, sans que personne s'en
aperçoive.

**54 tâches.**

## Par famille

| Tâche | Écrit | Ce qu'elle fait |
|---|---|---|
| 2. Interprètes | **oui** | Complète les champs vides depuis les sources. |
| 1. Scènes | **oui** | Identifie les fichiers et complète studio, titre, distribution. À lancer en premier : les scènes créent ce qui manque. |
| 3. Studios | **oui** | Complète réseau parent, site et présentation. |
| 4. Proposer des tags à écarter | non | Signale les tags que les sources posent souvent et que vous n'employez jamais. N'écrit rien. |

## Affiner

| Tâche | Écrit | Ce qu'elle fait |
|---|---|---|
| Appliquer les propositions d'interprètes | **oui** | Écrit les valeurs proposées sur toutes les fiches marquées. Sur une seule fiche, le bouton de la fiche est plus direct. |
| Appliquer les covers officielles | **oui** | Remplace les jaquettes par celles des stash-boxes, quand elles en fournissent. |
| Appliquer les recommandations | **oui** | Écrase les valeurs existantes par celles que les sources établissent. L'ancienne valeur passe dans l'historique. |
| Reconstituer les films en plusieurs parties | **oui** | Regroupe en films les scènes qui partagent un titre et un studio, et se suivent par leur numéro de partie. |
| Régénérer les présentations manquantes | **oui** | Rédige la présentation « hot » des fiches qui n'en ont pas. Coûte un appel de modèle par fiche. |

## Ménage

| Tâche | Écrit | Ce qu'elle fait |
|---|---|---|
| Aligner les conflits | **oui** | Écrase les valeurs qui contredisent les sources, au-delà du seuil de confiance. L'ancienne valeur passe dans l'historique. |
| Retirer les tags de proposition | **oui** | Retire les tags posés par le plugin pour signaler ce qui attendait une décision. Les valeurs restent. |
| Fusionner les doublons certains | **oui** | Ne fusionne que les paires dont la note dépasse le seuil de fusion. Les autres attendent votre arbitrage. |
| Détecter les doublons d'interprètes | **oui** | Marque les fiches qui semblent désigner la même personne. Ne fusionne rien : la fusion est une action distincte. |
| Détecter les doublons de studios | **oui** | Marque les studios qui semblent être le même. Ne fusionne rien. |
| Marquer les rôles venus d'un import | **oui** | Signale comme « suggérés » les rôles qu'aucune source ne confirme, pour les distinguer des rôles établis. |
| Fusionner les interprètes marqués | **oui** | Reporte scènes et alias sur la fiche conservée, puis supprime l'autre. Sans retour. |
| Fusionner les studios marqués | **oui** | Reporte les scènes sur le studio conservé, puis supprime l'autre. Sans retour. |
| Normaliser l'écriture des rôles | **oui** | Uniformise la casse et l'orthographe des rôles déjà renseignés. |
| Retirer les tags exclus | **oui** | Retire des fiches les tags que vous avez listés comme indésirables. |
| Ranger les champs d'un import | **oui** | Déplace vers les champs standard de Stash ce qu'un import avait laissé dans des champs libres. |
| Retirer un champ d'import | **oui** | Argument champ=nom. Les champs du plugin sont refusés. |
| Retirer les valeurs sans source | **oui** | Efface ce qu'aucune source ne confirme, typiquement venu d'un import. |
| Retirer le pied de biographie | **oui** | Retire la mention de fiabilité ajoutée en bas des biographies générées. |

## Diagnostic

| Tâche | Écrit | Ce qu'elle fait |
|---|---|---|
| Appliquer les noms lus | **oui** | Relie les interprètes et studios reconnus au catalogue. Ne crée jamais de fiche. |
| Appliquer les studios lus | **oui** | Pose les studios reconnus au catalogue. Les lectures approximatives attendent une confirmation. |
| Contrôler les champs d'un import | **oui** | Liste les champs libres présents sur vos fiches et ce qu'ils contiennent. N'écrit rien. |
| État de l'agent | non | Ce que le plugin sait de votre installation : sources joignables, modèle configuré, dernier passage. |
| Inspecter une collecte | **oui** | Argument nom ou performer_id. Montre ce que chaque source répond, sans rien écrire. |
| Lire les chemins de fichiers | **oui** | Un dossier nomme souvent le studio, un nom de fichier la distribution. Gratuit et instantané. |
| Lire les génériques | **oui** | Découpe le début et la fin des planches pour y lire les noms. Demande Pillow. |
| Lire les filigranes | **oui** | Envoie les vignettes à un modèle pour y lire le nom du studio. Coûte des appels payants. |
| Rapport des rôles | **oui** | Répartition des rôles dans votre collection, et ce sur quoi chacun s'appuie. N'écrit rien. |
| Relever le prompt par défaut | non | Écrit dans le journal et dans l'état le prompt intégré au plugin, pour servir de point de départ. N'écrit rien sur les fiches. |
| Proposer des scrapers | **oui** | Compare vos studios au catalogue et signale ceux qui auraient un scraper. Argument installer=1 pour les poser. |
| Profil de collection | non | Ce que la composition de vos scènes dit de votre collection, et le profil que le rédacteur emploiera. N'écrit rien. |
| Dernier passage | non | Ce que le dernier enrichissement a écrit, et ce qui reste incomplet. |
| Rapport des tags | non | Quels tags sont posés, par quelles sources, et lesquels n'apparaissent jamais. N'écrit rien. |
| Vérifier l'état des sources | **oui** | Interroge chaque source sur une fiche connue et signale celles qui ne répondent plus. |

## Réparation

| Tâche | Écrit | Ce qu'elle fait |
|---|---|---|
| Exporter les réglages | non | Écrit vos réglages dans le journal, sous une forme à copier et garder hors de Stash. Aucune clé d'API n'est exportée. |
| Importer des réglages | **oui** | Rétablit des réglages depuis un export. Complète plutôt que de remplacer, et dit ce qu'il a changé. |
| Basculer la langue du plugin | **oui** | Change la langue de l'interface et des textes générés. Vide = la langue de Stash. |
| Reprendre les générations IA | **oui** | Relance les rédactions interrompues par une panne ou un plafond d'appels atteint. |
| Restaurer les réglages | **oui** | Remet les réglages du plugin dans l'état de la dernière sauvegarde automatique. |
| Restaurer les fiches marquées | **oui** | Rend aux fiches portant le tag de restauration les valeurs qu'elles avaient avant le dernier passage. |
| Oublier les réponses mémorisées | **oui** | Force la réinterrogation des sources au prochain passage. |

## Hors panneau

Ces tâches vivent sur les fiches, où elles
s'appliquent à un enregistrement précis, ou ne
sont appelées que par une autre.

| Tâche | Écrit | Ce qu'elle fait |
|---|---|---|
| apply_accepted_scenes | **oui** | — |
| apply_accepted_studios | **oui** | — |
| enrich_one_performer | **oui** | — |
| enrich_one_scene | **oui** | — |
| enrich_one_studio | **oui** | — |
| enrichir_tout | **oui** | — |
| generer_apercu | **oui** | — |
| noop | non | — |
| valider_fiche | **oui** | — |

