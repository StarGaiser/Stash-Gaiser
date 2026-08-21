# Normes de codage — Gaizer

Ces règles sont celles qui ont émergé du développement du plugin.
Chacune vient d'un problème rencontré, pas d'un principe abstrait.

---

## 1. Forme

**Python** — PEP 8, lignes de **79 caractères**, indentation de 4
espaces, `snake_case`. `pyflakes` doit être **silencieux** avant tout
commit.

**JavaScript** — 2 espaces, `const`/`let`, jamais `var`, point-virgule
terminal.

**YAML** — 2 espaces, jamais de tabulation. Le fichier du plugin est
**généré** par la bascule de langue : ne pas le mettre en forme à la
main, les modifications seraient perdues.

**Encodage** — UTF-8 partout, `# -*- coding: utf-8 -*-` en tête des
fichiers Python.

---

## 2. Langue du code

| Élément | Langue | Raison |
|---|---|---|
| noms de fonctions et variables | français | le domaine est décrit en français, mélanger nuit à la lecture |
| commentaires et docstrings | français | idem |
| clés techniques (`custom_fields`, réglages, modes) | anglais | elles voyagent dans l'API et la configuration |
| textes affichés | **aucune** | ils passent par `i18n.py` |

```python
def _canonique_de(p, q, nom_cree):        # ✔
def _get_canonical(p, q, created_tag):    # ✘ mélange de langues
```

---

## 3. Commentaires

**Le commentaire dit pourquoi, jamais quoi.** Le code dit déjà ce
qu'il fait.

```python
# ✘ inutile
# Boucle sur les performers
for p in perfs:

# ✔ justifie une décision non évidente
# Le doublon est détruit AVANT la mise à jour du canonique : Stash
# refuse un alias qui collide avec un nom existant.
```

Les contournements de l'API Stash sont **toujours** commentés : sans
explication, le prochain lecteur les prendra pour de la maladresse et
les « simplifiera ».

Les docstrings expliquent l'intention et les garde-fous, pas la
signature :

```python
def _meme_serie(court, long_):
    """« Brazil Underground » et « Gay - Treasure Island - TIM Fuck -
    Brazil Underground » désignent le même film.

    Le titre se trouve en FIN de nom, jamais au début : on n'accepte
    donc qu'un rapprochement par suffixe. « Howl » et « Howl 2 » —
    où le court est un préfixe — restent deux films distincts."""
```

---

## 4. Règles de fond

### 4.1 Ne jamais écraser

Seuls les champs vides sont complétés. Un désaccord se **signale**
dans `enrich_rapport` ; il ne se tranche pas.

```python
if not (fiche.get(champ) or "").strip():
    maj[champ] = valeur
else:
    conflits.append(ctx.t("conflit_ligne", ...))
```

### 4.2 Tout passage automatique est réversible

Toute écriture en mode auto alimente `enrich_historique` via
`_historique_maj()`. Les exceptions — fusion, cover — sont
**documentées comme telles** dans les spécifications fonctionnelles.

### 4.3 Toute mutation nouvelle entre dans le mode simulation

L'expression de `_activer_simulation()` doit couvrir la mutation, sans
quoi le mode « à blanc » écrit pour de vrai. **Cela s'est produit** :
`groupCreate` manquait, vingt groupes ont été créés lors d'un essai.

### 4.4 Aucun secret sur disque ni dans le journal

`est_secret()` fait foi. Une clé qui disparaît est **signalée**, jamais
restaurée depuis une copie.

### 4.5 Aucune dépendance propre à un système

Ni cron, ni systemd, ni chemin absolu. Ce qui doit se répéter dans le
temps s'appuie sur la relance des tâches, pas sur un ordonnanceur : le
plugin s'installe par copie d'un dossier et doit fonctionner sur toute
machine où Stash tourne, y compris dans un conteneur.

### 4.6 Les sources priment sur la déduction

Avant d'écrire une heuristique, **vérifier qu'aucune source ne fournit
l'information**. Les groupes ont fait l'objet de cette vérification :
`ScrapedScene.groups` existe mais revient vide, ce qui a justifié la
déduction — et cette déduction est annoncée comme telle, avec une note
de confiance.

---

## 5. Erreurs

**Jamais de `except: pass`.** Une erreur avalée en silence coûte des
heures de diagnostic.

```python
except Exception as exc:
    log.debug(f"marquage {sc.get('id')} : {exc}")   # ✔ tracé
```

**Sévérité** : `error` pour ce qui exige une action de l'utilisateur ;
`warning` pour une dégradation ; `info` pour le déroulement normal ;
`debug` pour la trace technique — notamment les réponses brutes des
fournisseurs, qui peuvent contenir des données sensibles.

**Un incident sur une fiche ne doit pas tuer le lot** : chaque entité
est traitée dans son propre `try`.

**Une erreur affichée doit être compréhensible.** « HTTP 429 » ne dit
rien à personne : le diagnostic traduit en « quota du compte IA
épuisé », et la raison est portée sur la fiche concernée.

---

## 6. Requêtes et performance

**Requêtes GraphQL toujours paramétrées** — aucune concaténation.

**Rien qui interroge Stash dans une boucle** sans nécessité. Les
tables stables (tags, fiches préexistantes, groupes) sont chargées une fois par
exécution.

```python
cache = getattr(ctx, "_tags_cache", None)
if cache is None:
    cache = ctx._tags_cache = {}
```

**Mesurer avant d'optimiser.** La détection de doublons est
quadratique : 405 000 comparaisons en 0,96 s. Elle reste telle quelle.
Le vrai gain était ailleurs — le cache de tags, 200 fois plus rapide.

**Toute tâche de masse respecte `batchSize`** et se conçoit comme
relançable.

---

## 7. Traduction

**Aucun texte affiché en dur.** Tout passe par `ctx.t()`, ou par `_t()`
dans les fonctions de module.

```python
log.error(_t("ia_suspendue", motif=msg, date=demain))   # ✔
log.error(f"IA SUSPENDUE : {msg}...")                   # ✘
```

Ajouter une chaîne, c'est l'ajouter **dans les sept langues** —
l'anglais fait référence, toute clé absente y retombe.

**Test de cohérence** : un message présent au catalogue mais jamais
appelé signale du texte resté en dur quelque part. Cinq messages ont
été pris ainsi.

---

## 8. Refactoring

**Ne pas commencer ce qu'on ne termine pas.** Extraire une fonction
sans câbler ses appelants laisse deux implémentations concurrentes,
dont l'une reste définie et inutilisée sans que rien ne le signale.

**Vérifier après nettoyage.** Une variable « jamais utilisée » peut
l'être trois fonctions plus bas — `pyflakes` a rattrapé exactement
cette régression.

**Éprouver sur les données réelles** avant de conclure, en simulation
d'abord.

---

## 10. Organisation en couches

Un module ne dépend que de ceux qui le précèdent :

```
noyau ─▶ similarite, collecte ─▶ ia, entites
      ─▶ performers, scenes, studios, doublons, groupes
      ─▶ rapports ─▶ gaizer (registre et point d'entrée)
```

**Toute dépendance ascendante est un défaut de conception**, pas une
contrainte à contourner par un import différé. Quand `entites` a eu
besoin de comparer des noms, la comparaison a été isolée dans un module
sans accès au serveur plutôt que rattachée à `doublons`.

Une fonction se place au niveau de sa **dépendance la plus haute**. Une
tâche qui orchestre plusieurs familles d'entités appartient à
`rapports`, jamais à l'une d'elles.

## 11. Tests

**Ce qui décide se teste ; ce qui écrit s'éprouve.** Les fonctions de
décision — comparaison, notation, filtrage, contrôle d'adresse — ont des
tests. Les fonctions d'écriture sont validées en mode simulation puis
sur une entité réelle.

**Aucun test n'ouvre de connexion.** `stashapi` est simulé dans
`conftest.py`, et sa `StashInterface` lève une exception si on
l'instancie : un test qui dépendrait d'un serveur échoue bruyamment au
lieu de passer par hasard.

**Tester d'abord ce qui doit être refusé.** Le faux positif coûte plus
cher que le faux négatif : une fusion est irréversible, une adresse
interne acceptée ouvre une porte.

**Partir des données réelles.** Un nom suffixé d'un numéro, une
apostrophe avalée, un studio dont le nom contient celui d'un autre :
les cas limites viennent des collections, pas de l'imagination. Ils se
décrivent par leur FORME — jamais par la fiche qui les a révélés.

**Quand un test échoue, déterminer d'abord qui a tort.** Le test peut
supposer un contrat que le code n'a jamais promis ; le faux serveur
peut être trop permissif ; le code peut avoir tort. Corriger le code
sans vérifier est aussi fautif que l'inverse.

Avant chaque commit : `python3 -m pytest` doit être vert.

## 12. Mesurer avant de croire

Un poids, un seuil, une heuristique sont des **hypothèses**. Tant
qu'elles ne sont pas confrontées à des données, elles donnent une
impression de rigueur sans en avoir la substance.

**Toute pondération doit avoir un témoin.** Comparer le dispositif à
une stratégie naïve — vote majoritaire, première valeur venue. S'il ne
la bat pas, la complexité n'est pas justifiée et il faut le dire.

**Chercher d'abord le plafond.** Avant de mesurer une exactitude,
mesurer le désaccord entre les références elles-mêmes. Ici, IAFD et
GEVI divergent sur 44 % des nationalités : viser mieux que 56 % n'avait
aucun sens.

**Un test qui échoue après un recalibrage peut avoir tort.** Un test
affirmait un écart d'au moins 0,3 entre sources éditoriales et
commerciales. La mesure l'a démenti ; c'est le test qui a été réécrit,
et il documente désormais le fait plutôt que l'intuition.

**Ne pas appliquer une correction non démontrée.** Rendre le bonus
d'accord proportionnel à la qualité des sources semblait mieux fondé.
Mesuré : aucun gain. La correction n'a pas été retenue.

## 13. Écrire les tests avant le code, pour les fonctions à risque

Les scrapers manquants ont été traités ainsi : vingt-six tests d'abord,
tous en échec faute de module, puis le code écrit contre ce contrat.

Trois décisions en sont sorties qui seraient autrement apparues comme
des correctifs après coup — et un correctif après coup, c'est un défaut
qu'un utilisateur a rencontré avant nous.

**Le rapprochement doit être exact.** « Brazil » ne doit pas ramener
« Brazzers » : un scraper installé à tort répondrait, avec des données
qui ne concernent personne. Écrit après, ce test n'aurait servi qu'à
constater le dégât.

**Une dépendance distante doit se taire, pas interrompre.** La
détection se greffe à la fin d'un enrichissement : son échec ne doit
pas faire tomber un travail qui a réussi.

**Une opération répétée doit avoir une cadence.** Sans limite, enrichir
une fiche unique interrogerait un serveur distant à chaque clic.

## 14. Quand un test échoue, chercher qui a tort

Un test qui échoue met en cause trois choses, et le code arrive en
dernier. Le test peut supposer un contrat que le code n'a jamais
promis ; le faux serveur peut être trop permissif ou trop strict ;
le code peut avoir tort.

Corriger le code à chaque échec introduit des régressions. L'ordre
est : lire le contrat réel, vérifier le faux serveur, puis seulement
mettre en cause le code.

## 15. Sécurité : la protection appartient au passage obligé

Un plugin d'enrichissement lit des données venues de sites tiers, les
passe à un modèle de langage, écrit dans une base locale, appelle des
commandes système et installe du code. Chacun de ces points est une
porte.

**La protection va là où tout le monde passe.** Filtrer les secrets
chez l'appelant suffit tant qu'il est seul, et le trou se rouvre au
premier chemin d'écriture ajouté. La protection appartient au passage
obligé — l'écriture elle-même.

**Une source de code se contrôle plus qu'une source de données.** Le
catalogue de scrapers doit être en https — servi en clair, il peut être
remplacé en chemin et le code installé ne serait pas celui annoncé — et
publique : installer depuis le réseau local reviendrait à exécuter ce
que quiconque s'y trouve y aurait déposé. Une source refusée retombe
sur celle par défaut plutôt que d'échouer : un refus muet laisserait
l'utilisateur sans explication.

**Une liste d'opérations interceptées se vérifie par le code, pas par
la mémoire.** Un test énumère les mutations employées et exige
qu'elles figurent toutes dans le mécanisme de simulation. Une
omission n'y est pas visible autrement.

**Un test de sécurité doit être plus strict qu'un test fonctionnel.**
Échouer par excès de prudence coûte une correction ; échouer par excès
de confiance coûte une compromission.

## 16. Ne pas écrire dans un dépôt ce qui décrit son auteur

Les défauts viennent de données réelles, et les messages de commit
les documentent. Citer une fiche décrit ce que contient une
collection — donc les goûts de celui qui publie, et des personnes
réelles.

Les chemins absolus portent un nom d'utilisateur. Les scripts de
correction ponctuels n'ont aucune valeur une fois appliqués et n'en
portent que le risque.

La règle : un exemple de défaut se décrit par sa FORME — « une date
nulle », « un nom réduit à un mot » — jamais par la fiche qui l'a
révélé.

## 17. Faire lire le code par des outils qu'on n'a pas écrits

Un contrôle qu'on écrit soi-même reflète ce à quoi on pense ; des
outils tiers repèrent ce à quoi on ne pense pas. Collisions de noms,
constructions valides seulement dans une version récente du langage,
entrées non contrôlées : autant de défauts qu'une suite de tests, si
fournie soit-elle, ne cherche pas.

Chaque exclusion porte sa raison dans `pyproject.toml`. Une règle
désactivée sans justification finit par masquer un défaut réel.

## 18. Une seule solution pour un même problème

Deux implémentations d'une même chose divergeront : la seconde ne sera
pas corrigée quand la première le sera. C'est vrai en particulier de
la comparaison de noms, qui décide des doublons — deux versions
fusionneraient des fiches différemment selon le chemin emprunté.

Une normalisation propre à un domaine — un tag, une URL, un
identifiant de paquet — n'est pas une répétition : c'est une règle
métier distincte. La distinction se fait sur ce que le code DÉCIDE,
pas sur sa forme.

## 19. Le code mort ment sur ce que fait le programme

Une fonction que personne n'appelle laisse croire, à qui découvre le
projet, que la décision se prend là. Corrigée un jour par mégarde,
elle diverge de la vraie sans que rien ne le signale.

Le code mort s'accumule par grappes : une table pointe vers des
fonctions elles-mêmes mortes, un appel à un outil externe ne sert
plus. `vulture` trouve ces cas ; encore faut-il agir sur ce qu'il dit,
plutôt que de laisser le doute protéger l'inutile.

## 20. Découper un module par intention

Quand un module absorbe ce qui ne trouve pas sa place ailleurs, il
cesse d'avoir une responsabilité et devient un fourre-tout : on n'y
trouve plus rien, et chaque ajout aggrave le cas.

Le découpage suit CE QU'ON VEUT OBTENIR — diagnostic, ménage,
arbitrage — et non l'ordre d'écriture. Quand l'interface propose déjà
un classement, c'est celui-là : un lecteur retrouve dans le code ce
qu'il voit à l'écran.

**Pas de façade de compatibilité.** Un module qui n'existe que pour
ré-exporter est un vestige, et il masque les défauts de la structure
qu'il enveloppe — notamment les dépendances latérales entre modules
frères, qui ne se voient qu'une fois la redirection retirée. Les
appelants sont mis à jour, y compris les tests : ceux-ci suivent la
conception, ils ne la dictent jamais.

**Une table partagée entre deux intentions n'appartient à aucune des
deux.** Sa place est dans la couche que toutes connaissent.

**Ne découper que du code couvert.** Sur du code non éprouvé, on
déplace sans savoir si l'on casse.

## 21. Principes de conception, et comment ils sont verifies

Un principe ecrit dans un document se cite et s'oublie. Ceux-ci sont
traduits en controles automatiques — imparfaits, comme toute mesure
d'une qualite humaine, mais qui echouent quand le code s'en eloigne
franchement.

### KISS — la solution la plus simple qui marche

Le contraire n'est pas la sophistication, c'est la dette : ce qu'on ne
comprend plus, on ne le corrige plus.

Mesure : complexite sous 25, imbrication sous cinq niveaux, six
arguments obligatoires au plus, pas de ternaire dans un ternaire, pas
de comprehension a trois etages.

Les arguments a valeur par defaut ne comptent pas : l'appelant ne les
voit pas. Ce qui coute, c'est ce qu'il faut passer dans le bon ordre.

### DRY — une seule source de verite

Deux implementations d'une meme regle divergent : la seconde n'est pas
corrigee quand la premiere l'est.

Mesure : aucun bloc de six lignes repete trois fois, aucune constante
declaree dans deux modules, aucune valeur metier repetee six fois.

La regle porte sur les DECISIONS, non sur la ressemblance de surface.
Deux fonctions qui filtrent une liste se ressemblent sans se repeter.
Et une clé de dictionnaire n'est pas une valeur metier : la remplacer
par une constante ajouterait une indirection sans rien centraliser —
le nom EST la verite.

### YAGNI — rien qui ne serve aujourd'hui

Le code ecrit « au cas ou » n'est pas eprouve, et il donne l'illusion
qu'une fonctionnalite existe.

Mesure : pas de code inatteignable, pas de parametre nomme qu'aucun
appelant ne passe, pas de classe de base dont une seule classe herite.

Corollaire pratique : n'extraire une abstraction qu'au deuxieme usage
reel, jamais au premier.

### SOLID — surtout deux des cinq

**Responsabilite unique** : un module qui expose plus de quatorze
fonctions publiques en a plusieurs, quel que soit son nom.

**Inversion des dependances** : les couches basses — noyau,
traductions, notation, comparaison — ne connaissent aucune tache. Une
tache parle au contexte, jamais directement a la bibliotheque de
Stash : celle-ci peut changer, et le contexte est ce qu'on remplace
dans les tests.

Les trois autres principes se verifient mal automatiquement et
relevent de la relecture.

### SoC — chaque module a un domaine

Mesure : l'arbitrage ne vit que dans le module de notation ; le reseau
ne vit que dans les couches d'acces ; l'affichage ne decide de rien —
reproduire un seuil dans le JavaScript le ferait diverger
silencieusement ; les textes affiches vivent dans les tables de
traduction, faute de quoi ils echappent aux sept langues.

### Ce que ces controles ne font pas

Ils attrapent la derive franche, celle qu'on ne voit plus a force de la
cotoyer. Ils ne remplacent pas le jugement, et un code qui les passe
tous peut rester mauvais. Quand l'un d'eux echoue, la question reste
la meme que pour tout test : qui a tort, le code ou la mesure ?

## 9. Livraison

Avant chaque commit :

```bash
python3 -m pyflakes gaizer/*.py     # silencieux
python3 -m py_compile gaizer/*.py
node --check gaizer/gaizer.js
```

Puis, pour toute évolution touchant l'interface ou les réglages,
rejouer les quatre contrôles de cohérence des spécifications
techniques (§11).

**Le message de commit explique le pourquoi et ce qui a été mesuré**,
pas la liste des lignes changées — le diff s'en charge. Une erreur
introduite se dit franchement : elle en apprend plus que la
correction.
