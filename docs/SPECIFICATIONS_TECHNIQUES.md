# Spécifications techniques — Gaizer

Cible : Stash ≥ 0.28 (API Groupes) · Python ≥ 3.9

---

## 1. Vue d'ensemble

Gaizer est un plugin Stash de type `exec` : Stash lance un processus
Python à chaque tâche, lui transmet la connexion au serveur et les
arguments par l'entrée standard, et lit le journal sur la sortie
standard. **Aucun démon, aucun état résident.**

```
Stash ──stdin(JSON)──▶ gaizer.py ──GraphQL──▶ Stash
  │                        │
  │                        ├──HTTPS──▶ stash-boxes, scrapers, sources
  │                        └──HTTPS──▶ fournisseur d'IA (facultatif)
  │
  └──ui.javascript──▶ gaizer.js (barre d'actions dans les pages)
```

### 1.1 Modules

Le code est organisé **en couches** : un module ne dépend que de ceux
qui le précèdent. Aucune dépendance ascendante, aucun cycle.

| Couche | Module | Lignes | Rôle |
|---|---|---|---|
| — | `i18n.py` | 2447 411 | libellés, étiquettes, messages (7 langues) |
| — | `sources.py` | 397 | définition et poids des sources |
| — | `scoring.py` | 375 | familles, fiabilités, détecteurs de biais |
| — | `llm.py` | 256 | table des fournisseurs de modèles |
| 0 | `noyau.py` | 850 | contexte, réglages, état, sécurité, utilitaires |
| 1 | `similarite.py` | 138 | comparaison de noms (logique pure) |
| 1 | `collecte.py` | 446 | interrogation des sources, statistiques |
| 2 | `ia.py` | 834 | appels aux modèles, diagnostic, rédaction |
| 2 | `entites.py` | 248 | propositions, créations, restauration |
| 3 | `performers.py` | 408 | enrichissement des interprètes |
| 3 | `scenes.py` | 568 | enrichissement des scènes |
| 3 | `studios.py` | 203 | enrichissement des studios |
| 3 | `doublons.py` | 495 | détection et fusion |
| 3 | `groupes.py` | 361 | films en plusieurs parties |
| 5 | `gaizer.py` | 1265 | registre des tâches et point d'entrée |
| — | `roles.py` | 135 | position et rapport de pouvoir (logique pure) |
| — | `tags.py` | 349 | familles de tags et mesures d'exclusion |
| — | `gaizer_page.js` | 1362 | panneau de commande, tâches par intention |
| — | `scrapers.py` | 264 | scrapers manquants : détection et pose |
| — | `chemins.py` | 389 | ce que le rangement dit du contenu |
| — | `vision.py` | 553 | lecture des filigranes |
| — | `sprites.py` | 408 | génériques de début et de fin |
| — | `rapprochement.py` | 201 | retrouver un studio depuis un texte lu |
| — | `cache.py` | 168 | mémoire des réponses de sources |
| — | `taches_diagnostic.py` | 568 | regarder sans rien changer |
| — | `taches_heritage.py` | 374 | champs venus d'un autre outil |
| — | `taches_arbitrage.py` | 370 | la seule famille qui écrase |
| — | `taches_menage.py` | 236 | retirer ce qui encombre |
| — | `taches_maintenance.py` | 217 | réparer l'installation |
| — | `gaizer.js` | 1265 | actions injectées dans l'interface |

**Ce que la stratification impose.** `entites` a besoin de comparer des
noms pour signaler un doublon dès la création : la comparaison a donc
été isolée dans `similarite`, module sans accès au serveur, plutôt que
laissée dans `doublons` — ce qui aurait créé un cycle. De même,
`rapports` orchestre des tâches des trois familles d'entités : il est
seul en couche 4, et rien ne remonte vers lui.

### 1.2 Fichiers de configuration

| Fichier | Versionné | Contenu |
|---|---|---|
| `gaizer.yml` | oui | réglages et tâches déclarés à Stash |
| `gaizer_config.yml` | oui | surcharges du moteur de notation |
| `llm_providers.yml` | oui | fournisseurs d'IA supplémentaires |
| `etat.json` | **non** | pause IA, incidents, sauvegarde des réglages |

---

## 2. Cycle d'exécution

```
main()
 ├─ Context()                 lit stdin, réglages, connexion Stash
 │   ├─ _LANGUE ← lang()      fixe la langue des messages de module
 │   ├─ plafond et espacement des appels d'IA
 │   └─ si dryRun : _activer_simulation()
 ├─ _sauver_reglages(ctx)     copie hors secrets, alerte si disparition
 ├─ _reprise_opportuniste()   lève la pause IA arrivée à échéance
 └─ TASKS[ctx.mode()](ctx)    exécute la tâche demandée
```

Le mode provient de `args.mode` ; le registre `TASKS` associe chaque
mode à sa fonction. **54 tâches, 45 réglages.**

---

## 3. Contexte

`Context` encapsule la connexion, les réglages et les caches. Les
accesseurs normalisent les valeurs (virgule décimale française,
bornes, valeurs par défaut) pour qu'aucune tâche n'ait à s'en soucier.

| Méthode | Rôle |
|---|---|
| `apply_mode()` | `manual` \| `seuil` \| `auto` |
| `auto_threshold()` | seuil d'application (défaut 7,5) |
| `batch()` | taille de lot (défaut 25, plafond 5 000) |
| `lang()` / `langue()` / `t()` / `tag_nom()` | langue, traduction, étiquettes |
| `tags_exclus()` / `refresh_days()` | filtrage et fraîcheur |
| `simulation()` | mode sans écriture |
| `ai_for(usage)` | `(fournisseur, modèle, clé)` ou `None` |
| `fournisseurs()` | table des services d'IA, mise en cache |

### 3.1 Caches par exécution

| Cache | Sans lui |
|---|---|
| `_tags_cache` | une requête HTTP **par pose de tag** — mesuré : 400 appels = 400 requêtes, ramenés à 2 |
| `_idx` (fiches préexistantes) | un rechargement complet par scène |
| `_groupes` | un rechargement complet par série |
| `_llm_table` | une relecture du fichier par appel |

---

## 4. Accès à Stash

### 4.1 GraphQL

Toutes les requêtes sont **paramétrées** : aucune concaténation de
valeur dans une chaîne de requête.

```python
ctx.stash.call_GQL(
    "mutation($input: StudioUpdateInput!) "
    "{ studioUpdate(input: $input) { id } }",
    {"input": maj})
```

### 4.2 Pièges de l'API rencontrés et contournés

| Piège | Conséquence | Parade |
|---|---|---|
| `configurePlugin` **remplace** toute la table des réglages | écrire une clé efface les autres | sauvegarde dans `etat.json`, alerte, tâche de restauration ; relire et renvoyer la table complète |
| `find_performers()` sans filtre | 25 résultats seulement | `filter={"per_page": -1}` |
| alias en collision avec un nom existant | mutation refusée | détruire le doublon **avant** de mettre à jour le canonique |
| `scrape_performer()` de stashapi | 422 sur les stash-boxes | `call_GQL` direct sur `scrapeSingleSource` |
| hooks `*.Create.Post` | mutation bloquée pendant tout l'enrichissement | aucun hook ; tâches et boutons uniquement |
| lien scène↔groupe | `SceneGroupInput{group_id, scene_index}`, pas de description | — |
| `custom_fields: {partial: {clé: None}}` | ne supprime RIEN : la clé subsiste avec sa valeur | `CustomFieldsInput` expose `full`, `partial` et **`remove`** ; ce dernier prend la liste des clés à retirer |
| tâche de masse sur toute la collection | une écriture par entité, plusieurs minutes | ne pas la tuer par un délai d'attente trop court — ce n'est pas un blocage |
| `runPluginTask` | rend un numéro de travail, pas un résultat | suivre `findJob` jusqu'à un état terminal ; sans quoi l'interface annonce un succès avant toute écriture |
| file d'exécution des plugins | **une seule** tâche à la fois, toutes extensions confondues | un travail au statut `READY` attend son tour : ce n'est pas une panne. `stopAllJobs` vide la file |
| `register.route` | la route n'est pas garantie d'exister : le JavaScript des plugins est chargé après le montage des routes | ne pas en dépendre pour l'accès — un panneau ouvert sur place évite le problème |
| patch `after` d'un composant | reçoit `(props, contexte, résultat)` | lire le **dernier** argument ; le second est le contexte React, qu'afficher fait échouer le rendu |
| `.form-control` seul | style Bootstrap d'origine, fond blanc | ajouter `.input-control`, la classe dont Stash habille ses champs |
| `installPackages` | installe du code tiers qui s'exécutera sur la machine | jamais sans demande explicite ; `availablePackages` et `installedPackages` pour comparer sans rien poser |
| `career_length` | « 2013-présent » rejeté | format « 2013 - » |

### 4.3 Champs personnalisés

Mise à jour partielle : `{"partial": {"champ": "valeur"}}`.
Création : dictionnaire simple. Les clés restent préfixées `enrich_`
malgré le renommage du plugin : elles décrivent leur contenu, et les
migrer aurait mis en péril les données existantes.

---

## 5. Notation des sources

`scoring.py` expose une matrice **famille × type de source × champ**.
Le calcul :

1. les sources d'une même famille sont **fusionnées en une voix** ;
2. chaque valeur candidate reçoit une note de base selon la fiabilité
   du type de source pour ce champ précis ;
3. les **détecteurs de biais** appliquent des pénalités commentées ;
4. la meilleure note l'emporte, la valeur est marquée **★**.

`gaizer_config.yml` ne contient que les écarts aux valeurs du code.

### 5.2 Couverture des tests

Mesurée avec `coverage`, et instructive au-delà du chiffre : elle était
**inversement corrélée au risque**. Les modules bien couverts étaient
les modules purs, ceux qui ne peuvent rien casser ; `doublons.py`, qui
fusionne et supprime des fiches, était à zéro sur 247 instructions.

| Module | Avant | Après | Ce qu'il fait |
|---|---|---|---|
| `doublons.py` | 495 % | 59 % | fusionne et **supprime** |
| `studios.py` | 203 % | 73 % | écrit sur les studios |
| `performers.py` | 408 % | 54 % | écrit sur les interprètes |
| `scenes.py` | 568 % | 40 % | écrit et relie |
| `entites.py` | 248 % | 80 % | crée et restaure |
| **Ensemble** | **30 %** | **47 %** | |

L'ordre suivi a été celui du risque, pas celui de la facilité.

### 5.1 Validation empirique

Trois outils, dans `tools/`, mesurent ce que le moteur vaut :

| Outil | Question posée |
|---|---|
| `collecte_echantillon.py` | rejoue la collecte et conserve le détail par source, que le plugin ne garde pas |
| `valider_scoring.py` | méthode de la source retirée : masquer un annuaire, demander au moteur de le retrouver |
| `mesurer_fiabilites.py` | quelle part des valeurs de chaque source concorde avec la référence ? |
| `essai_ponderations.py` | une autre formule ferait-elle mieux ? |

**Protocole de la source retirée.** Pour chaque fiche où IAFD ou GEVI
fournit une valeur : la mettre de côté comme référence, retirer cette
source des données, faire choisir le moteur parmi le reste, comparer.
La référence est extérieure aux données soumises — le protocole n'est
pas circulaire. Deux témoins servent d'étalon : « première source » et
« vote majoritaire non pondéré ».

**Résultats (70 fiches, 135 cas).** Moteur 77 %, vote majoritaire 77 %,
première source 77 %. Sur les 31 cas de désaccord réel, toutes les
variantes tombent à 51 %. Le plafond est fixé par le désaccord entre
les références elles-mêmes : 56 % sur la nationalité, 86 % sur la
taille.

**Ce qui a été corrigé.** Les fiabilités du type `studio` ont été
relevées (0,35 → 0,70 sur la taille) d'après la mesure. Un test qui
affirmait un écart d'au moins 0,3 entre éditorial et commercial a été
réécrit : il encodait une intuition démentie par les faits.

**Ce qui n'a pas été corrigé, faute de preuve.** Le bonus d'accord
reste forfaitaire. Le rendre proportionnel à la qualité des sources qui
confirment paraissait mieux fondé, mais n'a rien amélioré à la mesure —
l'ajouter aurait été de la complexité sans contrepartie.

---

## 6. Modèles de langage

### 6.1 Table des fournisseurs

`llm.DEFAUTS` décrit 14 services. Chaque entrée :

```yaml
url:          point d'entrée « chat completions »
model:        modèle par défaut
auth:         bearer | x-api-key | query | none
format:       openai | anthropic
key_setting:  réglage Stash portant la clé (facultatif)
url_setting:  réglage Stash portant l'adresse (services locaux)
headers:      en-têtes additionnels
```

`llm_providers.yml` est fusionné **entrée par entrée** : on peut
ajouter un service ou n'en modifier qu'un champ.

**Aucune clé ne figure dans ce fichier** : elle vient du réglage dédié,
sinon du réglage générique `llmApiKey`.

### 6.2 Robustesse des appels

```
_appel_llm            pause si suspendu, espacement, plafond, compteur
  └─ _appel_llm_plafonne   réessais avec attente croissante
       └─ _appel_llm_une_fois   requête, diagnostic, état
```

- **Inutile d'insister** sur une clé refusée, un modèle inconnu ou un
  quota mort : la boucle s'arrête.
- **Quota épuisé** ou saturation persistante (8 échecs consécutifs) →
  pause jusqu'au lendemain, écrite dans `etat.json`.
- Le diagnostic traduit l'erreur brute en sept catégories : `quota`,
  `debit`, `cle`, `modele`, `requete`, `indispo`, `reseau`.

### 6.4 Coût des appels

Une passe complète sur une collection d'environ un millier
d'interprètes et autant de scènes
représente **2 752 appels** — deux par interprète (bio factuelle et bio
« hot »), un par scène, un par studio.

Trois dispositifs le réduisent :

**Empreinte des sources.** `empreinte_sources()` signe ce qui a servi à
produire un texte ; la signature est rangée sur la fiche. Au passage
suivant, si elle n'a pas changé et que le texte est toujours là, l'appel
est évité. Sur une collection déjà enrichie, cela porte sur la
quasi-totalité des appels — c'est de loin le gain principal.

**Budget de sortie par usage.** `BUDGETS` donne 150 jetons à un
synopsis factuel contre 260 à une présentation libre. Les jetons de
sortie sont facturés plus cher que ceux d'entrée.

**Modèle choisi par usage.** Les réglages `aiBio`, `aiSynopsis` et
`aiBiohot` acceptent chacun un fournisseur et un modèle distincts : un
synopsis factuel n'a pas besoin du modèle le plus cher.

### 6.3 Reprise sans ordonnanceur

`_reprise_opportuniste()` s'exécute au début de **chaque** tâche et
lève la pause dès son échéance passée. Les cibles étant recalculées à
chaque passage, le travail en attente repart de lui-même. **Aucune
dépendance à cron, systemd ou tout autre service propre à un système
d'exploitation.**

---

## 7. Internationalisation

`i18n.py` est organisé **par langue** : ajouter une langue revient à
copier le bloc anglais et à le traduire.

| Famille | Contenu | Couverture |
|---|---|---|
| `tags` | suffixes des étiquettes | 7/7 |
| `boutons` | libellés de l'interface | 7/7 |
| `taches` | noms des tâches | 7/7 |
| `reglages` | libellés des réglages | 7/7 |
| `msg` | messages fiches et journal | 7/7 |
| `DESCRIPTIONS` | textes longs | en, fr (repli anglais) |

Repli : langue demandée → anglais → clé. **Une traduction partielle
n'empêche jamais le fonctionnement.**

Les fonctions de module (appel d'IA, gestion de la pause) n'ont pas de
contexte : la langue est retenue dans `_LANGUE` à l'initialisation, et
`_t()` y donne accès.

### 7.1 Bascule de langue

1. Les tags posés sont **renommés** vers la langue cible ; en cas de
   collision, ils sont **fusionnés** (`tagsMerge`).
2. Le YAML est **régénéré** par PyYAML : seuls les textes affichés
   changent, jamais les modes, types ou clés techniques.

Le JavaScript n'appelle jamais une tâche par son nom traduit : il passe
par un point d'entrée technique au nom stable, en précisant le mode.

---

## 8. Sécurité

| Risque | Traitement |
|---|---|
| **Secrets sur disque** | `est_secret()` exclut toute clé de la sauvegarde ; seule leur présence est mémorisée ; fichier en 0600 ; `etat.json` non versionné |
| **SSRF — falsification de requête côté serveur, c'est-à-dire
amener le plugin à interroger une adresse qu'il ne devrait pas — par images distantes** | `url_sure()` n'accepte que http(s) vers un hôte public — localhost, 10/172.16-31/192.168, 169.254, `.local` et `file://` refusés |
| **Injection GraphQL** | requêtes exclusivement paramétrées |
| **Injection HTML** | le JavaScript n'utilise que `textContent` ; ni `innerHTML` ni `eval` |
| **Désérialisation** | `yaml.safe_load` uniquement ; pas de `pickle` |
| **Exécution** | aucun `eval`, `exec` ni `shell=True` |
| **Destruction accidentelle** | confirmation exigée avant toute fusion ; fiches préexistantes jamais détruit automatiquement |
| **Fuite par le journal** | aucun secret journalisé ; les erreurs brutes du fournisseur restent en `debug` |

### 8.1 Mode simulation

`_activer_simulation()` intercepte **toutes** les mutations d'entités —
interprètes, scènes, studios, groupes, tags, `configurePlugin`. Les
lectures passent.

> Cette liste a dû être élargie : `groupCreate` n'y figurait pas et un
> essai « à blanc » a réellement créé vingt groupes. Un filet troué est
> plus dangereux qu'une absence de filet, puisqu'il inspire confiance.
> **Toute nouvelle mutation doit être ajoutée à cette expression.**

---

## 9. Performance

Mesures sur une collection de l'ordre du millier d'entités, sur un
ordinateur monocarte :

Chiffres du banc (`python3 tests/bench.py`), sur un millier d'interprètes,
autant de scènes :

| Opération | Coût |
|---|---|
| ~400 000 comparaisons de noms | 526 ms |
| 7 208 évaluations du moteur de notation | 480 ms |
| lecture des motifs de partie sur 800 titres | 4 ms |
| rapprochement de 200 séries | 3 ms |
| filtrage de 603 tags | 4 ms |
| 1 000 poses de tag **avec** cache | 1 requête (1 000 sans) |
| 300 recherches de groupe **avec** cache | 1 requête (300 sans) |
| chargement des interprètes depuis Stash | 3,4 s |

La croissance de la recherche de doublons est mesurée à ×3,8, ×4,2 puis
×4,3 pour un doublement du volume : conforme à une comparaison deux à
deux, sans coût parasite dans la boucle. Un test verrouille cette forme
de croissance sans jamais poser de plafond en secondes — une durée
absolue dépendrait de la machine et rendrait le test instable.

La complexité quadratique de la détection de doublons est **assumée** :
mesurée à moins d'une seconde, elle ne justifie pas d'indexation.

Le **lot** (`batchSize`) borne chaque tâche ; les traitements longs
sont conçus pour être relancés, les cibles étant recalculées.

---

## 10. Dette technique connue

| Point | Ampleur | Position |
|---|---|---|
| `_appliquer_scene` (140 lignes, 30 branchements) | modéré | séquence d'écritures cohérente ; la découper disperserait la logique |
| `rapport_run` (122 lignes) | faible | énumération linéaire, lisible telle quelle |
| Champs `enrich_*` après renommage | faible | assumé : migrer les clés mettrait en péril les données |
| Descriptions longues en deux langues | faible | assumé : repli anglais suffisant |

Le découpage du fichier unique de 4 000 lignes a été mené d'un bloc,
par un script s'appuyant sur l'analyse syntaxique : répartition des
définitions, calcul des dépendances, génération des imports. Le point
d'entrée est passé à 142 lignes. Deux défauts ont été rattrapés au
passage — des imports devenus superflus, et le bloc `if __name__ ==
"__main__"` que l'extraction des seules définitions avait laissé de
côté, si bien que le plugin se chargeait sans rien exécuter.

**Règle d'engagement :** ne pas commencer un refactoring qu'on ne
termine pas. Extraire une fonction sans câbler ses appelants laisse
deux implémentations concurrentes — cela s'est produit avec
`paires_candidates()` et a été corrigé.

---

## 11. Vérifications avant publication

```bash
python3 -m pyflakes gaizer/*.py     # doit être silencieux
python3 -m py_compile gaizer/*.py
node --check gaizer/gaizer.js
```

Contrôles de cohérence à rejouer après toute évolution :

1. réglages déclarés ↔ réglages lus (attention aux clés construites à
   l'exécution, `"ai" + usage`) ;
2. modes du YAML ↔ registre `TASKS` ;
3. clés de traduction appelées ↔ catalogue ;
4. messages du catalogue effectivement utilisés — un message traduit
   mais jamais appelé signale du texte resté en dur.

Toute tâche nouvelle est éprouvée **en simulation d'abord**, sur la
collection réelle.
