# Tests — Gaizer

la suite complète, moins de dix secondes, **aucune dépendance à Stash**.

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```

---

## Ce qui est couvert, et pourquoi

Le plugin se divise en deux natures de code. Celui qui **décide** —
quelle valeur retenir, si deux fiches n'en font qu'une, si une adresse
est sûre — et celui qui **écrit** dans Stash. Les tests portent sur le
premier.

Ce choix n'est pas un renoncement. Les erreurs qui ont réellement coûté
cher pendant le développement venaient toutes de décisions, pas
d'écritures : un contrôle d'URL troué, des accents mal normalisés, une
catégorie d'erreur mal déduite. Les écritures, elles, sont éprouvées sur
la collection réelle, en mode simulation d'abord.

| Fichier | Tests | Objet |
|---|---|---|
| `test_similarite.py` | | comparaison de noms, notation des doublons, choix du canonique |
| `test_groupes.py` | | motifs de parties, notation des séries, rapprochement des écritures |
| `test_noyau.py` | | filtrage des tags, contrôle des URLs, secrets, historique |
| `test_llm.py` | | table des fournisseurs, authentification, formats de réponse |
| `test_ia.py` | | diagnostic des erreurs de fournisseur |
| `test_coherence.py` | | cohérence YAML / code / traductions, architecture, sécurité |
| `test_scoring.py` | | familles de sources, fiabilité par champ, détecteurs de biais |
| `test_idempotence.py` | | relances, restauration, budgets de requêtes, mode simulation |
| `test_robustesse.py` | | réglages mal saisis, données hostiles, paramètres des traductions |
| `test_scrapers.py` | | rapprochement exact, refus d'installer sans volonté |
| `test_sources.py` | | sources d'appoint, après nettoyage |
| `test_taches.py` | | les 24 tâches, systématiquement |
| `test_collecte.py` | | frontière avec le dehors : normaliser, rapprocher |
| `test_documentation.py` | | ce que la doc affirme doit être vrai |
| `test_qualite.py` | | outils tiers, homogénéité, nommage, anonymat |
| `test_securite.py` | | portes ouvertes par la nature du plugin |
| `test_scenes.py` | | identification, liens, greffe de détection |
| `test_pipeline.py` | | ce qui est écrit et ce qui ne l'est pas, par mode |
| `test_doublons.py` | | fusion : rien ne se perd, rien ne se détruit sans conditions |
| `test_entites.py` | | création, propositions, restauration |
| `test_donnees_reelles.py` | | jeu fabriqué localement, ignoré s'il est absent |
| `test_rapports.py` | | lecture des mesures, seuils d'écart, arbitrage des conflits |
| `test_roles.py` | | vocabulaire des rôles, refus de ranger de force |
| `test_tags.py` | | familles de tags, mesures d'exclusion, protections des profils |
| `test_complexite.py` | | forme de la croissance, budgets de requêtes sur volume |
| `faux.py` | — | faux serveur Stash en mémoire (outil, pas des tests) |
| `bench.py` | — | banc de mesure, à lancer à la demande |
| `verif_patch.js` | 29 | contrat avec le mécanisme de patch, libellés des boutons |
| `verif_page.js` | 8 | panneau de commande, entrée de navigation |

---

## Fonctionner sans Stash

Les modules importent `stashapi`, présent uniquement là où Stash tourne.
`tests/conftest.py` insère un substitut dans `sys.modules` **avant** le
premier import : un journal muet, et une `StashInterface` qui **lève une
exception si on tente de l'instancier**.

Ce dernier point est délibéré : un test qui ouvrirait une connexion
échouerait bruyamment au lieu de dépendre silencieusement d'un serveur
en marche.

---

## Le faux serveur

`tests/faux.py` garde les fiches en mémoire, applique les écritures avec
la sémantique de Stash — y compris la mise à jour **partielle** des
champs personnalisés — et **compte chaque appel**.

Ce comptage est le cœur de l'affaire. Chronométrer donnerait des tests
instables : les durées dépendent de la machine et de la charge. Or ce
qui a réellement coûté cher ici n'était pas la lenteur d'un calcul mais
le **nombre d'allers-retours** — 400 poses de tag valaient 400 requêtes
avant la mise en cache. Un nombre d'appels est déterministe.

Une requête que le faux serveur ne connaît pas **lève une exception**
plutôt que de renvoyer `None`, qui serait interprété comme « aucun
résultat » et masquerait l'erreur.

## Les défauts que ces tests ont trouvés

Écrire ces tests révèle des défauts dans du code qui
fonctionnait en apparence.

### Les accents étaient supprimés, non translittérés

`_sim_cles("Björn Söder")` donnait `bjrnsder` au lieu de `bjornsoder`.
Conséquence : deux fiches « Björn Söder » et « Bjorn Soder » ne se
rapprochaient pas — alors que les sources écrivent indifféremment avec
ou sans signes diacritiques. Corrigé par une translittération
(`unicodedata`).

### Le contrôle des URLs demande plus qu'il n'y paraît

Le premier test de sécurité en a révélé trois d'un coup :

| Adresse | Pourquoi elle passait |
|---|---|
| `http://[::1]/` | l'extraction de l'hôte s'arrêtait au premier `:`, qui appartient à l'adresse IPv6 et non au port |
| `http://[fe80::1]/` | les liens-locaux IPv6 n'étaient pas couverts |
| `http://2130706433/` | écriture décimale de 127.0.0.1 |
| `http://127.1/` | forme abrégée, admise par les navigateurs |

Le contrôle a été réécrit avec `urllib.parse` et `ipaddress`, qui
connaissent ces formes. Les seize adresses dangereuses testées sont
désormais refusées, les six adresses légitimes acceptées.

C'est le genre de faille qui ne se remarque jamais à l'usage : elle ne
gêne personne, elle n'attend qu'une source compromise.

### Une date aberrante interrompait tout l'enrichissement

`_date("0000-00-00")` levait `ValueError: year 0 is out of range`. La
forme était bonne, la date n'existait pas — et l'exception remontait
jusqu'à interrompre le traitement de la fiche entière. Les sources
distantes envoient ce genre de valeur sans prévenir.

### Les non-réponses concouraient comme des valeurs

Une source renvoyant `""`, `None` ou `"unknown"` voyait sa non-réponse
traitée comme un candidat. Proposer une valeur vide revient à effacer un
champ au nom d'une source.

### Le lien de groupe se dupliquait à chaque passage

Une scène déjà rattachée voyait son lien empilé. Le cas se produit dès
qu'une partie isolée vient compléter un groupe existant — précisément le
scénario ajouté pour « Brazil Underground ».

### Le seuil d'application n'était pas borné

`autoAcceptThreshold` acceptait `-3` ou `11`. À zéro ou moins, tout
s'applique, y compris les valeurs douteuses ; au-delà de dix, plus rien
ne s'applique jamais et le plugin paraît en panne sans qu'aucun message
ne l'explique.

### Deux hypothèses fausses de ma part

Un test supposait que « Jean-Daniel » donnerait deux jetons. Le code en
fait un seul, ce qui est défendable — un prénom composé est un tout, et
la clé plate reste identique, donc le rapprochement fonctionne. **Le
test a été corrigé, pas le code**, et il documente maintenant ce choix.

---

## Les contrôles de cohérence

`test_coherence.py` mérite une mention à part : il automatise ce qui
était jusque-là une revue manuelle. Cette revue avait trouvé quatre
défauts, et rien ne garantissait qu'ils ne reviendraient pas.

**Réglages morts.** Un réglage déclaré mais jamais lu trompe
l'utilisateur : il le renseigne sans effet. Un renommage de
fournisseur laisse typiquement l'ancien nom derrière lui.

**Réglages invisibles.** Un réglage lu mais non déclaré n'apparaît pas
dans l'interface : sept clés d'API étaient dans ce cas, donc impossibles
à renseigner.

**Textes restés en dur.** Un message présent au catalogue de traduction
mais jamais appelé signale du français figé ailleurs. Cinq messages ont
été pris ainsi — ils s'affichaient en français quelle que soit la langue
choisie.

**Mutations hors du mode simulation.** Le test vérifie nommément que
treize mutations figurent dans le filtre. `groupCreate` y manquait, et
un essai « à blanc » avait réellement créé vingt groupes. Un filet troué
est plus dangereux qu'une absence de filet : il inspire confiance.

**Dépendances ascendantes.** Le test reconstruit le graphe des imports
et vérifie qu'aucun module ne dépend d'une couche supérieure.

**Bloc `__main__`.** Son absence laisse le plugin se charger — 29 tâches
enregistrées, code retour 0 — sans rien exécuter. Panne silencieuse,
survenue lors du découpage en modules.

---

## Deux catégories, deux rôles

**Les tests** sont synthétiques, rapides, déterministes et autonomes.
Ils vérifient que le plugin fait ce qu'il dit. Un appel réseau les
rendrait lents et dépendants de l'état du monde ; un test qui échoue
pour une raison extérieure finit ignoré, et un test ignoré ne protège
rien.

**La vérification des sources** procède par appels réels, hors de la
suite, à la demande. Elle comble le seul angle mort que les tests ne
peuvent pas couvrir : qu'une source ait changé de format ou cessé de
répondre. Les tests resteraient verts pendant que la collecte ramène
du vide.

## Un jeu d'essai fabriqué, jamais publié

Les défauts sérieux trouvés jusqu'ici venaient tous de données réelles,
aucun d'un cas imaginé : une date « 0000-00-00 » qui interrompait une
fiche entière, des biographies réduites au seul pied, « Réalisatrice /
Icone » rangé de force parmi les positions.

`tools/capturer_fixtures.py` produit un jeu depuis la médiathèque
locale, dans `tests/fixtures_locales/`, **non versionné**. Chacun
éprouve le plugin sur son propre réel ; les données de personnes
réelles ne quittent pas la machine. Les tests concernés s'ignorent
proprement quand le dossier est absent.

L'échantillon est choisi pour sa VARIÉTÉ, pas pour sa taille : les
extrêmes de chaque critère, les fiches sans champs personnalisés, les
noms d'une seule partie, les scènes sans studio ni date. Le script dit
quels cas limites il a captés — un jeu qui n'en contient aucun
rassurerait à tort.

## Un test ne doit rien appeler dehors

Le pipeline d'enrichissement interroge les stash-boxes, les sources
d'appoint et un modèle de langage. Sans coupure explicite de ces trois
voies, la suite passait de cinq secondes à **cinquante-quatre**, et son
résultat dépendait de l'état du réseau.

La coupure est faite dans le test lui-même, pas dans le code : les
fonctions de collecte et de génération sont remplacées le temps du
test. Le code testé reste celui qui tourne en service.

## Écrire les tests avant le code

Les scrapers manquants ont été traités ainsi : vingt-six tests d'abord,
tous en échec faute de module, puis le code écrit contre ce contrat.

Ce que cela a changé : les questions difficiles se sont posées avant
d'être noyées dans l'implémentation. Faut-il rapprocher
approximativement ? Non — « Brazil » ne doit pas ramener « Brazzers »,
un scraper installé à tort répondrait avec des données qui ne
concernent personne. Que se passe-t-il si le catalogue est
injoignable ? La détection se greffant à la fin d'un enrichissement,
elle doit se taire plutôt que l'interrompre. À quel rythme ? Une fois
par jour, sinon chaque clic interroge un serveur distant.

Aucune de ces trois décisions n'aurait été prise en écrivant le code
d'abord : elles seraient apparues comme des correctifs, après coup.

## Le faux serveur doit refuser autant qu'il accepte

Un faux serveur trop permissif rend les tests inutiles sans qu'on s'en
aperçoive : ils passent, mais ne prouvent rien.

Trois fois le même piège s'est présenté. La fusion d'un interprète
interroge les scènes où il figure : le faux les renvoyait TOUTES, si
bien qu'une fusion réécrivait la collection entière et que le test
« les scènes étrangères ne bougent pas » n'avait aucun sens. Idem pour
le filtre par studio, puis par tag — l'application des scènes acceptées
touchait toutes les scènes.

Le faux honore désormais ces trois filtres. La règle qui s'en dégage :
quand un test échoue, se demander d'abord si c'est le CODE ou le FAUX
qui a tort. Sur onze échecs de la dernière séance, trois venaient du
faux, six de tests qui supposaient un mauvais contrat, deux seulement
d'un défaut réel.

## Un test de sécurité est plus strict qu'un test fonctionnel

Échouer par excès de prudence coûte une correction ; échouer par excès
de confiance coûte une compromission. Ces tests refusent donc des
choses que le code accepterait peut-être sans dommage.

Ils ne cherchent pas des menaces théoriques mais les portes qu'ouvre
la nature du plugin : contrôle d'URL incomplet, secrets écrits en
clair, opération destructrice absente du mécanisme de simulation.
Chacune de ces familles est vérifiable par un test, et invisible
autrement.

## Ce que des outils tiers voient

Un contrôle qu'on écrit soi-même reflète ce à quoi on pense ; `ruff`,
`bandit` et `vulture` repèrent ce à quoi on ne pense pas. Trois
familles de défauts échappent typiquement à une suite de tests, si
fournie soit-elle :

**Une collision de noms qui plantait à l'exécution.** `import time as
_t` masquait la fonction de traduction `_t` dans la même portée : le
message d'avertissement de pause IA levait une `UnboundLocalError`.
Invisible tant qu'aucune limite de débit n'était atteinte.

**Des guillemets imbriqués**, valides depuis Python 3.12 seulement. Le
plugin aurait échoué au chargement sur une installation plus ancienne.

**Une adresse de fournisseur non contrôlée.** Elle vient d'un fichier
éditable : un « file:// » y aurait fait lire un fichier local et
l'envoyer dans la réponse.

Les exclusions figurent dans `pyproject.toml`, chacune avec sa raison.
Une règle désactivée sans justification finit par masquer un défaut
réel.

## Quatre familles de contrôles génériques

**Homogénéité** — deux solutions pour un même problème, c'est une de
trop : la seconde ne sera pas corrigée quand la première le sera. Une
seule façon de lire l'état, de poser une étiquette, de contrôler une
URL, de comparer des noms d'entités.

**Nommage** — le code est en français, identifiants compris. Un
paramètre d'une lettre est acceptable dans un utilitaire de trois
lignes, pas dans une fonction publique qu'on lit sans voir son corps.

**Anonymat** — aucun chemin personnel, aucune adresse de courriel,
aucun secret en dur. Le contrôle est doublé dans le script de
publication : celle-ci ne doit pas dépendre du fait que quelqu'un a
lancé les tests.

**Solidité des tests eux-mêmes** — un test sans assertion passe
toujours ; un test qui appelle le réseau est lent et instable ; un
test qui écrit le vrai état corrompt l'installation. Les trois se sont
présentés ici.

## La frontière avec le dehors mérite ses propres tests

Ce qui entre dans le plugin vient de sites tiers : des champs absents,
des chaînes d'espaces prises pour des valeurs, des dates nulles, des
adresses en majuscules. Deux responsabilités s'y jouent, et l'erreur
n'a pas le même coût dans chacune.

**Normaliser mal** donne une valeur fausse, qu'un arbitrage ultérieur
peut rattraper. **Rapprocher mal** attribue une scène au mauvais
interprète — et rien ne le rattrape. Les tests de rapprochement sont
donc plus nombreux et plus stricts : le rapprochement partiel est
explicitement refusé, mieux vaut créer une fiche que se tromper de
personne.

Quatre faiblesses réelles y ont été trouvées : une réponse nulle qui
levait une exception, une chaîne d'espaces comptée comme réponse — ce
qui faussait le nombre de familles d'accord, donc la note —, une barre
finale qui distinguait deux adresses identiques, et un passage en
minuscules placé APRÈS le retrait du préfixe, si bien qu'une adresse en
majuscules ne correspondait à aucun motif de scraper.

## Deux tests ne peuvent pas porter le même nom

`ruff` a trouvé deux méthodes homonymes dans une même classe : la
seconde remplaçait la première en silence, et l'une des deux n'avait
jamais tourné. La suite paraissait plus grosse qu'elle n'était.

C'est le genre de défaut qu'aucun test ne peut trouver — un test qui ne
s'exécute pas ne signale rien — et que seul un outil lisant le code
peut voir.

## Un filet minimal vaut mieux qu'un contrôle profond sur trois tâches

Vingt-quatre tâches, trois éprouvées. Plutôt que d'en couvrir quelques-
unes en profondeur, chacune passe le même contrôle en quatre questions :
survit-elle à une collection VIDE ? à des arguments ABSENTS ? à des
arguments ABSURDES ? n'écrit-elle RIEN quand rien ne s'y prête ?

Ce n'est pas profond, et ça ne prétend pas l'être. Mais une tâche qui
tombe sur une collection vide est un défaut que personne ne devrait
découvrir en production — et c'est pourtant ainsi qu'on les découvre.
la suite complète pour cela, écrits une fois et appliqués à toutes.

Le contrôle a immédiatement trouvé une incohérence de conception : une
tâche nommée « rapport » qui ÉTIQUETAIT des scènes. Le comportement
était documenté — ce qui est un aveu : on la lance pour regarder. Elle
annonce désormais ce qu'elle ferait, et ne le fait que si on le
demande, comme partout ailleurs dans le plugin où constater et agir
sont séparés.

## Des seuils par module, non un objectif unique

« 90 % partout » mesure mal. L'objectif pousse à écrire des tests qui
exécutent sans éprouver — les derniers points sont les plus pénibles —
et traite de la même façon une fonction qui supprime des fiches et une
fonction qui écrit une ligne de journal.

Trois régimes, selon ce qu'une ligne non couverte coûte :

**Ce qui décide ou détruit** — arbitrage, comparaison de noms,
installation de code tiers. Une ligne non éprouvée y est un risque de
perte de données. Seuil haut.

**Ce qui traite** — collecte, tâches, interface. Une erreur s'y voit
et se corrige. Seuil moyen.

**Ce qui appelle l'extérieur** — sources distantes, point d'entrée.
Non couvert délibérément : un test qui appelle le réseau est lent et
instable, et un test instable finit ignoré. Ces chemins sont éprouvés
par la vérification de l'état des sources, hors de la suite.

Les seuils sont des CLIQUETS : ils reflètent l'état atteint et les
baisser demande une raison. Un contrôle refuse également qu'un seuil
s'éloigne trop de la mesure — au-delà d'une dizaine de points, il ne
protège plus rien, le module pouvant perdre la moitié de sa couverture
sans réaction.

## La documentation vieillit plus vite que le code

Une spécification qui décrit une tâche retirée, un lien vers un fichier
déplacé, un réglage cité qui n'existe plus : rien de cela n'empêche le
programme de tourner, et c'est le problème. Personne ne s'en aperçoit,
jusqu'au jour où quelqu'un suit une instruction qui ne marche pas et
conclut que le projet est abandonné.

Les documents sont donc éprouvés comme du code. Ce qu'ils affirment
doit exister : tâches, réglages, modules, fichiers, outils, commandes.
Les liens internes doivent mener quelque part. La licence doit être
annoncée pareil partout — une divergence est une ambiguïté juridique,
pas une nuance de rédaction.

Trois contrôles portent sur la PORTÉE plutôt que sur l'exactitude. Un
document public s'adresse à des inconnus : pas de formulation à la
première personne, pas de décompte de défauts passés qui date le
texte sans rien apprendre, aucune référence à une collection
particulière.

## Ce que les tests de documentation ne voient pas

Vérifier qu'une tâche citée existe ne dit rien de ce qu'un lecteur
comprend. Un document peut être exact et illisible.

Une seconde famille de contrôles porte donc sur la LECTURE, avec un
seuil placé haut : on ne signale que ce qui bloquerait franchement
quelqu'un d'extérieur.

**La péremption.** Un numéro de version dans un en-tête devient faux à
la publication suivante ; le manifeste du plugin est le seul endroit
qui le tient à jour. Une date absolue invite à se demander ce qui a
changé depuis, sans moyen de le savoir. Un décompte de tests diverge
d'un document à l'autre et laisse choisir lequel croire.

**Le jargon.** Un terme propre au projet employé sans être défini
oblige à deviner ; qui devine mal se trompe sur tout ce qui suit. Un
sigle doit être développé à sa première occurrence.

**L'accueil.** Le README est souvent la seule page lue : ce qui n'y est
pas n'existe pas. Prérequis, premier lancement, limites annoncées,
licence — et les deux versions linguistiques doivent couvrir les mêmes
sujets, faute de quoi une partie des lecteurs est moins renseignée.

## Mesurer plutôt que chronométrer

Aucun test ne pose de plafond en secondes. Une durée dépend de la
machine, de la charge et du cache : le test devient instable, on finit
par l'ignorer, et un test ignoré ne protège rien.

Deux approches le remplacent.

**La forme de la croissance.** Doubler le volume doit multiplier le
travail par environ quatre pour une comparaison deux à deux — jamais par
huit. C'est ce qui attrape le jour où quelqu'un glisse une compilation
d'expression régulière ou une requête dans la boucle interne. Mesuré :
×3,8, ×4,2, ×4,3.

**Le nombre d'appels.** Déterministe, lui. Mille poses de tag doivent
coûter une requête, pas mille. C'est ce compte, et non un chronomètre,
qui a rendu visible le gain du cache.

Le banc `tests/bench.py` se lance à la demande et donne les chiffres
réels. Il alimente la section « Performance » des spécifications
techniques ; c'est à lui qu'on demande si une optimisation a servi.

## Écrire un nouveau test

Trois principes tirés de l'expérience ci-dessus.

**Nommer le comportement, pas la fonction.** `test_prefixe_de_nommage_reconnu` dit ce qui est attendu ; `test_meme_serie_1` n'apprend rien à celui qui lit un échec.

**Partir des cas réels.** Les jeux d'essai viennent de la collection :
« Archie 18969 », « Tony DAngelo », « Brazil Underground ». Un test sur
des données inventées passe à côté de ce que produisent vraiment les
sources.

**Tester d'abord ce qui doit être REFUSÉ.** Pour la sécurité comme pour
les doublons, le faux positif coûte plus cher que le faux négatif :
fusionner deux fiches distinctes est irréversible, accepter une adresse
interne ouvre une porte. La moitié des tests de `url_sure` et de
`_meme_serie` porte sur des refus.

---

## Ce qui n'est pas couvert

Les fonctions qui **écrivent** dans Stash — enrichissement, application,
fusion, constitution des groupes. Les simuler demanderait un faux
serveur GraphQL dont la fidélité serait elle-même à démontrer, pour un
bénéfice inférieur à l'essai réel en mode simulation.

Ces chemins sont donc validés autrement : mode simulation sur la
collection, puis exécution réelle sur une entité, puis vérification du
résultat par requête. C'est ce protocole qui a rattrapé le bloc
`__main__` manquant.

Le JavaScript n'est pas testé non plus ; il est vérifié par
`node --check` et à l'usage.
