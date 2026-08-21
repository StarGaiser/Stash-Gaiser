# Guide d'utilisation

Ce document décrit ce que Gaizer fait, dans quel ordre s'en servir, et
ce que chaque tâche écrit. Il s'adresse à quelqu'un qui vient
d'installer le plugin.

Les chiffres qu'il contient sont vérifiés par des tests : s'ils
périment, la suite échoue.

---

## Ce que fait Gaizer

Votre médiathèque Stash contient des fichiers dont les fiches sont
incomplètes : pas de studio, pas d'interprète, pas de date, pas de
présentation. Gaizer va chercher ces informations à plusieurs endroits
et les propose — ou les écrit, selon ce que vous décidez.

**Il ne remplace rien sans le dire.** Chaque valeur écrite porte sa
provenance et une note de confiance, consultables sur la fiche. Ce qui
a été fait peut être défait.

---

## Première utilisation

L'onglet **Enrichir** suffit pour commencer. Il porte trois boutons,
dans l'ordre où on s'en sert.

### 1. Renseigner un modèle (facultatif)

Sans modèle de langue, Gaizer fonctionne : il complète les champs
depuis les sources, mais n'écrit ni biographie ni synopsis.

Pour en avoir un, renseignez **Modèle par défaut** dans les réglages
du plugin, au format `fournisseur:modèle` — par exemple
`mistral:mistral-large-latest` ou `ollama:llama3`. La clé d'API va
dans **Clé d'API du modèle**, sauf pour un service local qui n'en
réclame pas.

Les modèles diffèrent beaucoup devant le contenu explicite. Un texte
qui revient sage ou évasif désigne le modèle, non votre prompt.

### 2. Lancer « Tout enrichir »

Il passe chaque source active sur les fiches incomplètes, de la moins
coûteuse à la plus coûteuse. Il traite un lot puis s'arrête : le
relancer prend le lot suivant.

Par défaut, **rien n'est écrit sans votre accord** : les valeurs
trouvées sont proposées et marquées d'un tag. C'est le réglage
« Que faire des valeurs trouvées », qui a trois positions :

| Position | Effet |
|---|---|
| Proposer | rien n'est écrit, tout est proposé |
| Au-delà d'une note | écrit ce qui dépasse le seuil de confiance |
| Dès qu'une source répond | écrit sans arbitrage |

### 3. Regarder ce que ça a donné

« Dernier passage » dit ce qui a été écrit et ce qui manque encore.
« Annuler » rend aux fiches leurs valeurs précédentes.

---

## Les sources, et ce qu'elles coûtent

Gaizer interroge plusieurs sources, activables séparément. L'ordre
ci-dessous est celui de l'exécution : du gratuit vers le coûteux.

| Source | Ce qu'elle lit | Coût |
|---|---|---|
| Chemin du fichier | dossiers et nom de fichier | nul |
| Nom de fichier | titre, studio, interprètes | nul |
| Stash-boxes | vos stash-boxes configurées | réseau |
| Scrapers | ceux installés dans Stash | réseau |
| Sources d'appoint | ThePornDB, StashDB, Wikipédia | réseau |
| Vignettes | filigranes de studio sur l'image | modèle |
| Génériques | noms lus sur les planches de sprites | modèle |

**Rien de tout cela n'écrit un nom qui n'a pas de forme plausible.**
Un contrôle refuse les fiches nommées « Do 40092 » ou « Tony 40365 »,
qui venaient autrefois d'une lecture de travers.

---

## Les textes générés

L'onglet **Textes générés** gouverne ce que le modèle écrit :
biographies, présentations, synopsis.

**Le prompt par défaut y figure**, avec un bouton pour en partir. Le
relever d'abord évite d'inventer un prompt sans avoir vu celui qui
marche.

**Le modèle employé est nommé**, avec sa provenance — réglage propre
aux présentations, ou modèle par défaut. Sans cela, changer de modèle
devient un tâtonnement.

**Deux limites gouvernent le résultat** sans figurer dans le prompt :

- La longueur est bornée à environ 660 signes. Un modèle remplit
  toujours l'espace qu'on lui laisse, les jetons de sortie coûtent
  plus cher que ceux d'entrée, et un texte qui déborde de la fiche est
  payé sans être lu. Demander plus long dans le prompt ne la lèvera
  pas.
- Un texte qui nomme un studio ou une personne absents des données de
  la fiche est refusé et régénéré. Le prompt l'interdit déjà ; cela ne
  suffit pas, parce qu'un modèle produit des noms plausibles mieux que
  tout le reste, et que personne ne vérifie un nom qui sonne juste.

### Le profil de collection

Le prompt s'adapte à ce que vous regardez : un texte sur une actrice
dans une collection hétéro n'emploie pas les mêmes mots qu'un texte
sur un acteur gay.

Le genre vient de la **fiche** quand il est renseigné — c'est la seule
source juste. À défaut, le réglage « Profil de collection » sert de
repli. Sans l'un ni l'autre, rien n'est supposé.

La tâche **Profil de collection** dit ce que la composition de vos
scènes suggère, et si votre réglage s'en écarte.

---

## Générer un texte sur une fiche précise

Sur la fiche d'un interprète, d'un studio ou d'une scène, un bouton
**Générer un texte** produit un aperçu.

Le résultat s'affiche **à côté du texte actuel** : remplacer sans
comparer, c'est décider sans savoir ce qu'on perd. Rien n'est appliqué
tant que vous n'acceptez pas.

C'est aussi la façon la moins coûteuse d'ajuster un prompt : un essai
vaut un appel, contre des centaines pour un lot.

---

## Emporter ses réglages

Stash n'offre rien pour cela — ses exports traitent les données, pas
les réglages de plugin.

**Exporter les réglages** (onglet Réparation) les écrit dans le
journal, sous une forme à copier. **Aucune clé d'API n'en sort** :
seule leur présence est notée, pour que l'import puisse dire ce qu'il
reste à ressaisir.

**Importer des réglages** les rétablit. Il complète plutôt que de
remplacer, et dit ce qu'il a changé. Simulez d'abord : il annonce ce
qu'il ferait sans rien écrire.
