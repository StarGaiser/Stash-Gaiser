# Spécifications fonctionnelles — Gaizer

Plugin d'enrichissement pour [Stash](https://github.com/stashapp/stash)

---

## 1. Raison d'être

Une médiathèque personnelle est presque toujours incomplète : titres
tronqués, dates absentes, interprètes non reliés, studios en double,
films découpés en parties dispersées. Les sources qui pourraient
combler ces trous se contredisent, se recopient, et défendent parfois
leurs propres intérêts.

Gaizer ne se contente donc pas de **recopier la première source
trouvée**. Il interroge plusieurs sources, **note chaque valeur
candidate**, et laisse voir sur chaque fiche d'où vient ce qui a été
écrit et ce que cela vaut.

**Principe cardinal : rien n'est jamais écrasé.** Seuls les champs
vides sont complétés. Un désaccord entre une valeur existante et les
sources est signalé, jamais résolu d'autorité.

---

## 2. Périmètre

### 2.1 Ce que le plugin traite

| Entité | Informations complétées |
|---|---|
| **Interprètes** | état civil, nationalité, mensurations, circoncision, photo, carrière, alias, URLs, bio factuelle, bio « hot » |
| **Scènes** | titre, date, studio, interprètes, tags, synopsis, cover officielle, URL de la fiche source |
| **Studios** | description, URL, logo, alias, réseau parent, statistiques de collection |
| **Groupes** | films en plusieurs parties, reconstitués et ordonnés |

### 2.2 Ce que le plugin ne fait pas

- Il ne **télécharge** aucun média.
- Il ne **renomme** ni ne déplace aucun fichier.
- Il ne **supprime** jamais une scène.
- Il n'introduit **aucune source de données propre** : stash-boxes,
  scrapers et clés déjà configurés dans Stash lui suffisent.
- Il ne **recommande** rien : le choix de quoi regarder relève d'un
  autre outil, alimenté par les données que Gaizer produit.

---

## 3. Sources et arbitrage

### 3.1 Ordre d'interrogation

1. **Stash-boxes** configurées dans Stash (StashDB, ThePornDB…) —
   pour les scènes, l'identification passe par l'**empreinte
   perceptuelle** du fichier, ce qui est le mode le plus fiable.
2. **Scrapers d'interprètes** installés, par nom.
3. **Passe par URL** : les scrapers dédiés aux URLs déjà présentes sur
   la fiche.
4. **Sources d'appoint** (Wikipedia, annuaires), facultatives.

### 3.2 Comment une valeur est retenue

Trois mécanismes, réglables dans `gaizer_config.yml` :

**Familles de sources.** Des sites appartenant au même groupe
éditorial publient la même fiche. Trois copies ne valent pas trois
confirmations : une famille ne compte que pour une voix.

**Fiabilité par type et par champ.** Un annuaire éditorial fait
autorité sur l'état civil ; un site commercial est juge et partie sur
les bios et les mensurations, mais fiable sur sa propre filmographie.

**Détecteurs de biais.** Sont pénalisés et commentés : le
rajeunissement par rapport aux sources éditoriales, les mensurations
gonflées, une carrière commençant avant 18 ans, les valeurs hors
plage.

La valeur la mieux notée reçoit une **★** et une note sur 10.

### 3.4 Ce que ce dispositif vaut réellement

Le moteur a été confronté aux faits sur un échantillon de 70 fiches, en
masquant une source éditoriale et en lui demandant de la retrouver
parmi les autres. Trois résultats, qui n'étaient pas ceux attendus.

**Il n'existe pas de vérité terrain.** Les deux annuaires de référence,
IAFD et GEVI, ne s'accordent qu'à **56 % sur la nationalité**, 66 % sur
la date de naissance, 74 % sur l'ethnicité, 86 % sur la taille. La
tâche est donc intrinsèquement bruitée : aucun dispositif ne peut
dépasser nettement ces proportions, et un désaccord résiduel n'est pas
forcément une erreur.

**La pondération n'améliore pas la sélection.** Sur 135 cas mesurés, le
moteur retrouve la référence dans 77 % des cas — exactement comme un
vote majoritaire sans aucune pondération. Sur les 31 cas de désaccord
réel entre sources, aucune variante testée (fiabilité seule, somme des
fiabilités, bonus proportionnel à la qualité) n'a fait mieux que la
majorité simple.

**Les sources commerciales sont plus fiables que supposé.** Un site de
studio était crédité de 0,35 sur la taille ; il concorde en réalité
avec les annuaires dans 71 à 78 % des cas. La méfiance de principe
envers le commercial ne se vérifie pas sur ce qui est vérifiable. Les
poids ont été corrigés en conséquence.

**Conséquence sur ce qu'il faut attendre du plugin.** La valeur du
dispositif n'est pas de choisir mieux qu'un vote majoritaire — il ne le
fait pas — mais de **rendre visible sur quoi repose chaque valeur** :
combien de sources, lesquelles, dans quel désaccord. C'est cette
traçabilité qui permet d'arbitrer soi-même, là où un simple recopiage
laisserait sans recours.

Les fiabilités livrées valent pour une collection donnée.
`tools/mesurer_fiabilites.py` permet de les recalculer sur la sienne,
et `gaizer_config.yml` de les remplacer.

### 3.3 Quand aucune source ne répond

Pour les scènes, le **nom du fichier** est exploité en repli : les
studios et interprètes déjà connus de la collection y sont recherchés.
Cette identification est explicitement annoncée comme moins fiable, et
un contrôle croisé signale les cas où le nom de fichier ne corrobore
pas l'identification retenue.

Une scène qu'**aucun mécanisme** ne parvient à identifier reçoit le tag
`Gaizer:non-identifiée`, ce qui la rend filtrable dans l'interface au
lieu de disparaître dans un journal.

---

## 4. Modes d'application

| Mode | Comportement | Vos arbitrages sont-ils mémorisés ? |
|---|---|---|
| `manual` | tout passe par des propositions à valider, portées par des tags | oui |
| `seuil` | les recommandations ★ atteignant le seuil s'appliquent en masse | non, pour ce qui est appliqué en masse |
| `auto` | la valeur la plus probable est appliquée directement | sans objet : il n'y a pas d'arbitrage |

Le **seuil** (défaut 7,5/10) sépare ce qui est appliqué de ce qui est
soumis.

### 4.1 Cycle en mode manuel

1. Une tâche d'enrichissement pose des **tags de proposition** portant
   la valeur, la source et la note.
2. Vous filtrez sur `Gaizer:proposal`, examinez, et **acceptez** —
   par le bouton de la fiche ou en posant `Gaizer:accept`.
3. La tâche d'application écrit les valeurs et retire les tags.

---

## 5. Traçabilité et réversibilité

### 5.1 Ce que chaque fiche conserve

| Champ | Contenu |
|---|---|
| `enrich_sources` | valeurs retenues, notes, sources, date du passage |
| `enrich_rapport` | conflits détectés, doublons signalés, décisions en attente |
| `enrich_historique` | les dix derniers passages, valeur avant et après |
| `enrich_ia` | raison pour laquelle un texte n'a pas pu être produit |
| `reco_data` | partenaires, studios et tags récurrents, tirés de la collection |
| `bio_hot` | présentation libre, séparée de la bio factuelle |

Un **pied de bio** facultatif résume la fiabilité des données
directement dans la biographie visible.

### 5.2 Revenir en arrière

Chaque passage automatique est journalisé. Poser `Gaizer:restaurer`
(ou cliquer **Restaurer**) puis lancer la tâche de restauration
rétablit l'état antérieur : champs remis, tags, interprètes et URLs
ajoutés retirés. Une exécution annule un passage ; relancer remonte
d'un cran.

**Exceptions, non réversibles :** les fusions de doublons (la fiche
absorbée est supprimée, son nom conservé en alias) et le remplacement
d'une cover.

### 5.3 Essayer sans conséquence

Le **mode simulation** fait calculer toutes les tâches et journaliser
ce qu'elles auraient écrit, sans rien modifier. Toutes les mutations
d'entités sont interceptées — interprètes, scènes, studios, groupes,
tags, et jusqu'à la configuration du plugin.

---

## 5.9 Ce qui peut être créé

Le plugin crée des fiches d'interprètes et de studios quand une source
en nomme un qui n'existe pas encore. C'est utile — sans quoi une scène
resterait sans distribution — mais c'est l'écriture la plus lourde de
conséquences.

**Une fiche créée à tort est pire qu'une scène incomplète.** Elle
pollue durablement le catalogue, fausse les rapprochements ultérieurs,
et prive la scène de son vrai interprète. Surtout, personne ne la
remarque : elle se fond dans la liste.

Les sources renvoient parfois des identifiants internes, des fragments
de nom de fichier, des codes d'encodage. Un contrôle de FORME les
écarte : il ne peut pas savoir si un nom existe, mais il sait qu'un
patronyme ne porte pas de nombre à quatre chiffres, qu'un mot isolé
désigne trop de monde, et qu'une phrase entière vient d'un champ mal
lu.

Ce contrôle vit DANS la création, non chez l'appelant : une source
ajoutée demain en bénéficie sans qu'on ait à y penser, et un test
d'architecture vérifie qu'il n'existe qu'un seul chemin de création.

## 6. Doublons

> **Une fusion est irréversible.** Elle reporte scènes et alias sur la
> fiche conservée, puis **supprime** l'autre. L'historique ne la défait
> pas — contrairement à toutes les autres écritures du plugin. C'est la
> seule opération sans retour, et c'est pourquoi elle n'est jamais
> automatique sur une fiche que vous aviez déjà.


### 6.1 Détection

Les fiches aux noms proches sont rapprochées et **notées** :

| Situation | Note |
|---|---|
| noms identiques une fois normalisés | 9,5 |
| suffixe numérique (artefact d'import) | 9,2 |
| nom égal à un alias de l'autre | 8,5 |
| préfixe commun long | 7,0 |
| prénom + initiale | 6,0 |

### 6.2 Règles de prudence

- Une fiche **créée par le plugin** peut être absorbée ; une fiche de
  une fiche que vous aviez déjà n'est **jamais détruite
  automatiquement**.
- Entre deux fiches créées, la plus renseignée l'emporte.
- Pour les studios, le canonique est celui qui porte le plus de
  scènes ; à égalité, le nom le plus lisible.
- Une **fausse alerte** se signale par un bouton : la paire est alors
  exemptée définitivement.

### 6.3 Dédoublonnage complet

Une tâche distincte fusionne, **y compris entre fiches du
fiches préexistantes**, les paires atteignant un seuil fort
(défaut 9,0). Elle
est destructive : le mode simulation en donne la liste avant toute
action.

---

## 7. Films en plusieurs parties

Les stash-boxes ne renseignant pas le groupe des scènes, l'information
est **déduite des titres**, à défaut des noms de fichiers.

**Motifs reconnus :** `part`/`partie`/`pt`, `chapter`/`chapitre`,
`volume`/`vol`, `episode`/`ep`, `n of m`, `scene`/`sc`. Le mot-clé est
obligatoire : un nombre isolé en fin de titre n'est pas un numéro de
partie.

**Note de confiance** combinant le nombre de parties, la continuité de
la numérotation depuis 1, l'unité de studio et la fiabilité du motif.
Un nom tiré d'un fichier perd un demi-point.

**Rapprochement des écritures.** Une même série peut figurer sous deux
noms selon la convention de nommage. Le titre se trouvant toujours en
fin de nom — le bruit le précède — le rapprochement n'accepte qu'un
**suffixe d'au moins huit caractères**, et refuse la fusion si un même
numéro de partie apparaît des deux côtés ou si les studios divergent.
Le nom retenu est le plus court.

Une série dont une seule partie figure dans la collection est signalée
mais pas créée, **sauf** si un groupe existant la réclame : c'est alors
le morceau manquant d'une série déjà formée.

---

## 8. Tags

Les tags des sources sont repris tels quels, puis filtrables.

### 8.1 Le problème

Une liste de tags « à ne pas appliquer » écrite pour une collection est
absurde pour une autre. `Gay` n'apprend rien dans une médiathèque
entièrement gay ; c'est l'information la plus discriminante dans une
médiathèque mixte. La question posée n'est donc pas *ce tag est-il
mauvais* mais **ce tag distingue-t-il quelque chose ici**.

Le plugin est livré **sans aucune exclusion** : la liste est celle de
l'utilisateur, jamais celle du plugin.

### 8.2 Trois mesures, sans hypothèse sur le contenu

| Mesure | Ce qu'elle repère |
|---|---|
| **Omniprésence** | un tag posé sur la quasi-totalité des scènes ne les sépare plus |
| **Dominance de famille** | un tag qui absorbe presque toutes les occurrences de sa famille décrit une constante, pas une distinction |
| **Rareté** | une ou deux occurrences ne regroupent rien |

La deuxième est la plus utile en pratique. Sur une collection réelle,
`Gay` ne couvrait que 14 % des scènes — trop peu pour l'omniprésence,
l'étiquetage étant clairsemé — mais détenait **96 % de sa famille**.
Cette mesure relative le repère là où la mesure absolue échoue, et elle
vaut pour n'importe quelle collection : dans une médiathèque mixte,
aucune orientation n'écrase les autres, donc rien n'est proposé.

### 8.3 Familles et profils

`tag_profiles.yml` range les tags courants par nature — format,
édition, anatomie, pratiques, orientation, identité, physique. Ces
familles sont **descriptives** : elles disent ce qu'un tag est, jamais
s'il faut l'écarter.

Un **profil de collection** (`gay`, `hetero`, `lesbien`, `bi`, `pan`,
`trans`, `mixte`) est facultatif et n'est jamais actif par défaut. Il
ne fait que deux choses :

- proposer d'écarter les familles **techniques** (format, édition), qui
  ne disent rien de ce qui est filmé ;
- **protéger** certaines familles de toute suggestion, y compris
  statistique.

Cette seconde fonction est la plus importante. Aucun profil ne propose
jamais d'écarter un tag d'**identité de genre** : une collection
étiquetée « gay » contient des interprètes trans, et évincer ces tags
parce qu'ils sont minoritaires serait une régression, pas un nettoyage.
Les catégories ne sont pas étanches, et le plugin ne prétend pas
trancher à la place de qui que ce soit.

Ce que les statistiques ne peuvent pas décider reste à l'utilisateur.
Écarter les tags anatomiques d'un genre absent d'une collection est un
jugement légitime — mais c'en est un, et il n'est pas automatisable
sans se tromper sur quelqu'un.

### 8.4 Les outils

- **Suggérer des tags à exclure** : applique les trois mesures et
  propose une liste, sans rien écrire.
- **Rapport des tags** : fréquences, quasi-doublons (forme normalisée,
  singulier/pluriel, inclusion), tags rares. Lecture seule.
- **Retirer les tags exclus** : détache des scènes les tags visés par
  le réglage, sans les supprimer de Stash.

---

## 9. Textes rédigés

Facultatifs. Sans modèle de langage configuré, le plugin applique les
données factuelles et reprend la meilleure description source.

| Texte | Nature |
|---|---|
| bio factuelle | synthèse sobre des sources, sans extrapolation |
| bio « hot » | présentation libre, champ séparé, ton et température réglables |
| synopsis de scène | factuel, ce qui est visible |
| présentation de studio | factuelle, appuyée sur les statistiques de collection |

### 9.1 Quand le service flanche

L'erreur est **traduite en langage clair** — quota épuisé, limite de
débit, clé refusée, modèle inconnu, service saturé, réseau injoignable
— journalisée et **portée sur la fiche concernée**, pour qu'un champ
vide ne reste jamais inexpliqué.

Un **quota épuisé** suspend les générations et les **reprogramme au
lendemain** ; l'enrichissement factuel, lui, continue. La reprise est
interne : la première tâche lancée après l'échéance repart. Aucun
ordonnanceur externe n'est nécessaire.

Deux garde-fous de consommation : un **plafond d'appels par tâche** et
un **espacement** entre appels, les rafales déclenchant des limites de
débit qui font échouer des générations en silence.

---

## 10. L'interface

### 10.1 Le panneau de fiche

Un panneau s'insère dans les pages interprète et studio, entre la
biographie et les champs personnalisés. Il porte ce que le plugin a
produit, présenté pour être lu plutôt que déchiffré :

- la **présentation** en évidence, taille de lecture ;
- les **rôles** — position et rapport de pouvoir — modifiables d'un
  menu, avec une pastille quand la valeur vient d'un import ou d'une
  lecture par l'IA plutôt que d'une confirmation ;
- les **partenaires et studios fréquents**, cliquables ;
- la **provenance repliée** : un tableau trié par note, code couleur,
  commentaires en infobulle.

Les champs du plugin sont retirés du bloc « Champs personnalisés » de
Stash, qui affichait le même contenu en vrac juste en dessous.

### 10.2 Les actions

| Bouton | Apparaît quand | Effet |
|---|---|---|
| **Compléter depuis les sources** | toujours | interroge les sources et remplit les champs vides |
| **Appliquer les propositions** | une proposition existe | écrit les valeurs et retire les tags |
| **Pas un doublon (définitif)** | un doublon est signalé | exempte la paire pour de bon |
| **Fusionner dans le jumeau (supprime celle-ci)** | un doublon est signalé | absorbe cette fiche |
| **Lever l'alerte** | l'identification est douteuse | retire l'avertissement |
| **Annuler le dernier passage** | toujours | défait le dernier enrichissement |

Chaque libellé annonce son **effet**, pas le moyen employé, et porte
une explication au survol. Les actions destructives le disent dans leur
nom et demandent confirmation.

Une tâche de plugin est asynchrone : le bouton suit son travail
jusqu'au bout, affiche « en attente » tant qu'il patiente en file puis
« en cours » quand il s'exécute, et rafraîchit le panneau à la fin.

### 10.3 Le panneau de commande

**Un onglet par intention.** Cinquante tâches sur un seul écran
défilant : celui qui découvrait ne savait pas par où commencer, celui
qui connaissait cherchait. Chaque groupe a désormais son onglet — on ne
voit que ce qu'on est venu chercher, et le nombre de tâches cesse
d'être une charge.

**Le premier onglet ne montre qu'un bouton.** Quelqu'un qui installe le
plugin veut que sa médiathèque soit complétée, pas choisir entre
cinquante actions. Une seule tâche y figure, celle qui enchaîne les
sources actives, et l'annulation juste à côté : ce qui rassure n'est
pas la promesse que rien ne casse, c'est de voir le bouton qui défait.

Rien n'y est destructif. Fusionner, supprimer, écraser demandent un
choix éclairé, donc les onglets détaillés.

### 10.4 Générer un texte là où on le lit

Un panneau global réglait les instructions données au modèle, un
bouton de lot les appliquait à toute la collection, et entre les deux,
rien : on ne voyait jamais sur QUELLE fiche le texte serait écrit, ni
ce qu'il donnerait avant qu'il soit là.

Le défaut était de conception. Régler un prompt sans le voir agir,
c'est ajuster à l'aveugle : on lance un lot, on lit ce qui est sorti,
on revient au panneau, on recommence — chaque tour coûtant des appels
sur des centaines de fiches pour vérifier une formulation.

**La fiche est le bon endroit.** Elle nomme l'entité, elle porte les
données dont le modèle se sert, et c'est là qu'on lit le résultat.

**L'aperçu précède l'écriture.** Le texte généré s'affiche à côté de
l'existant : remplacer sans comparer, c'est décider sans savoir ce
qu'on perd. Rien n'est appliqué tant qu'on n'accepte pas — un retour
en arrière suppose de s'être d'abord aperçu du problème.

**Les trois familles sont traitées.** Un interprète a une biographie,
un studio une présentation, une scène un synopsis. Chacune emploie sa
propre génération, celle-là même qui sert en lot : en écrire une
autre pour l'aperçu le rendrait menteur.

Le modèle employé est nommé à côté du texte : juger un résultat sans
savoir d'où il vient rend le changement de modèle tâtonnant.

### 10.5 La forme suit le contenu

**Un choix fermé se présente en choix fermé.** « Que faire des valeurs
trouvées » accepte trois valeurs et se saisissait en texte : il fallait
savoir quoi taper, une faute de frappe passait inaperçue — la valeur
était simplement ignorée, sans message — et rien ne disait ce que
chaque valeur change.

Chaque valeur porte désormais un libellé qui dit ce qui va se passer :
« seuil » ne dit rien, « Écrire au-delà d'une note de confiance » si.

**Le type dit la forme.** Un nombre se saisit dans un champ nombre, un
oui-non dans une case, un choix dans une liste. Un champ texte pour une
taille de lot accepte « vingt-cinq », qui sera silencieusement ignoré.

**Un onglet se lit comme un onglet.** Sans séparation ni indication
d'état, une barre passe pour une ligne de liens : on ne comprend ni
qu'on peut cliquer, ni où l'on est. L'onglet actif porte une bordure
et un texte plus dense, les rôles sont déclarés pour les lecteurs
d'écran, et les libellés sont espacés.

**Un onglet se nomme par ce qu'on y trouve.** « Simple » ne disait
rien : ni ce qu'il contient, ni pourquoi commencer là. Il s'appelle
« Enrichir ». Nommer un onglet par le niveau supposé de qui le lit est
un jugement, pas une information.

### 10.5 Simple ou avancé : un seul interrupteur

Quarante-cinq réglages, quarante-deux tâches, sept onglets : la
quantité elle-même est ce qui décourage. Grouper et décrire a aidé,
mais n'avait rien retiré de l'écran.

**Le remède est de ne pas montrer.** Quelqu'un qui installe le plugin
n'a besoin ni de la température du modèle, ni du seuil de fusion, ni
du plafond d'appels. Ces réglages doivent exister — quelqu'un d'autre
en a besoin — mais pas s'imposer à tous.

**Un seul interrupteur commande le tout.** Un état qui commanderait le
panneau sans commander les réglages laisserait la moitié du bruit. En
mode simple, deux onglets sur cinq restent — Première mise en route et
Entretien courant — et quatre réglages sont offerts sur place, ceux
qu'on change vraiment.

**Masquer n'est pas désactiver.** Un réglage mis en avancé, puis
repassé en simple, garde sa valeur. L'inverse serait un piège. Et le
choix survit au rechargement : rebasculer à chaque visite serait une
punition pour qui a choisi une fois.

**Les arguments sont saisissables.** Douze tâches en attendent un, et
rien ne permettait de le donner : il fallait passer par l'écran des
plugins de Stash. La description le disait, mais dire n'est pas
offrir. Un champ apparaît sur ces tâches, et sur elles seules.

### 10.5 Où vit chaque action

**Ce qui porte sur une fiche appartient à la fiche.** Une action qui a
besoin d'un identifiant obligerait, depuis le panneau, à le saisir à
la main — alors que sur la fiche il est implicite.

Cela vaut aussi contre la duplication : « Appliquer les propositions »
existe sur chaque fiche, où il porte sur ce qu'on regarde. Le répéter
au panneau en un bouton par famille créait trois entrées que rien ne
distinguait à l'œil, sans rien apporter.

**Ce qui balaie la collection appartient au panneau**, et un seul
bouton suffit par intention.

**Ce qui n'a pas de sens seul n'est pas une tâche.** Déduire un rôle
lit la documentation déjà collectée sur un interprète : en faire une
action séparée obligeait à enrichir, puis à comprendre qu'il fallait
relancer autre chose sur les mêmes fiches. C'est une étape de
l'enrichissement, et un réglage l'active.

### 10.5 Ce que l'interface doit dire

**Un cadre unique.** Chaque onglet avait sa mise en page — une carte,
des colonnes, des champs bruts. Passer de l'un à l'autre demandait de
se réorienter. Le contenu change, le cadre non : c'est ce qui fait
qu'on cesse de regarder l'interface pour regarder ce qu'elle contient.

**Un libellé se scanne, une description explique.** Les mélanger
produit des lignes qu'on ne peut ni parcourir ni comprendre. Le
libellé commence par un verbe — on cherche une action — ou nomme une
famille en trois mots. Ce qui tenait entre parenthèses passe dessous,
en gris.

**Une bulle partout où l'on hésite.** Sur l'onglet, pour savoir s'il
faut l'ouvrir. Sur « Lancer » et « Simuler », qui ne disent pas ce
qu'ils font de différent. Sur la tâche, pour ce que la description
n'a pas la place de dire.

### 10.5 Ce qui mérite un regard

Un enrichissement automatique écrit des valeurs dont certaines
méritent vérification : une seule source, une note basse, ou une
lecture d'image qui peut se tromper.

Elles sont signalées DANS la fiche, là où l'utilisateur regarde déjà —
lui demander d'aller chercher un rapport reviendrait à ce qu'il ne le
lise jamais.

**La validation est tout ou rien.** Un bouton lève les marques de la
fiche entière. Cocher champ par champ reproduirait l'éditeur de Stash
en moins bien ; pour corriger une valeur précise, l'édition normale est
le bon outil — et corriger une valeur la valide de fait.

Valider ne réécrit rien : la valeur est déjà là. Cela dit « j'ai
regardé », et l'historique le défait comme toute autre écriture.

Deux onglets séparent ce qu'on **lance** de ce qu'on **règle**.

**Tâches** : les quarante tâches regroupées par intention — première
mise en route, entretien courant, ménage, diagnostic, réparation — avec
la file d'attente en tête et un bouton *Simuler* à côté de chaque
action destructive.

**Rédaction** : les instructions données au modèle et la température,
sur un champ de la taille qu'il faut. Ces deux réglages existaient dans
la page des plugins de Stash, qui n'offre qu'un champ d'une seule
ligne : illisible pour un texte de dix lignes, et personne n'y touchait.
Un essai sur une fiche unique permet de juger avant d'appliquer à toute
la médiathèque.

Le panneau de FICHE, lui, n'a pas d'onglets : il tient en un écran, et
les y mettre cacherait de l'information derrière un clic.

Le bouton **GZ** de la barre de navigation ouvre un panneau qui
regroupe les tâches par **intention** : première mise en route,
entretien courant, ménage, diagnostic, réparation. Chaque tâche ne
figure qu'une fois, et l'ordre conseillé au premier usage est numéroté
— les scènes d'abord, puisqu'elles créent les interprètes et studios
manquants.

La **file d'attente** y est visible, avec ce qui tourne, combien
attend, et de quoi remettre tout à zéro. Stash n'exécutant qu'une tâche
de plugin à la fois, une attente de plusieurs minutes est normale et
n'est pas une panne.

Chaque action destructive propose **Simuler** à côté de Lancer.

## 11. Arbitrer, réparer, ranger

Ces tâches traitent des situations que l'enrichissement seul ne résout
pas.

### 11.1 Ce que les sources contredisent

Le plugin n'écrase jamais : un désaccord entre la fiche et les sources
est signalé et laissé tel quel. C'est la bonne règle par défaut — la
fiche peut être juste.

Mais un désaccord signalé ne se résout pas tout seul. **Aligner les
conflits sur les sources** est l'exception explicite : elle écrase, au-
dessus d'un seuil réglable, et l'ancienne valeur passe dans
l'historique. Les écarts d'un ou deux centimètres sont ignorés — les
sources arrondissent différemment une taille convertie depuis les
pouces, et traiter cela comme un conflit noierait les vrais.

### 11.2 Ce qui vient d'ailleurs

Une médiathèque reprise d'un autre outil traîne des champs
personnalisés qui font double emploi avec ceux de Stash, ou ne
renvoient plus à rien.

- **Contrôler les champs hérités** compare sans rien écrire.
- **Ranger les champs hérités** verse les valeurs dans les champs
  natifs — longueur, taille, poids — puis retire ce qui ne sert plus.
- **Retirer les valeurs qu'aucune source n'appuie** vide les champs
  natifs dont la provenance ne peut être établie.

Ce dernier point mérite une explication. Une valeur importée s'affiche
exactement comme une valeur établie par plusieurs sources : rien ne les
distingue. Quand l'import provient d'une recherche automatisée non
vérifiée, cela revient à présenter une supposition comme un fait. Ce
qui est retiré n'est pas forcément faux, seulement invérifiable — et le
prochain enrichissement le rétablira s'il est vrai, avec sa provenance.

**Limite connue** : la trace ne remonte qu'au dernier passage. Une
valeur saisie à la main hors du plugin est indiscernable d'une valeur
importée, et sera retirée avec elle.

### 11.3 Les rôles

Aucune source ne fournit la position ni le rapport de pouvoir. Trois
origines coexistent, distinguées sur la fiche :

| Marque | Origine |
|---|---|
| *(aucune)* | saisie ou confirmée |
| **suggéré** | l'IA l'a lu dans un texte, en citant le passage |
| **importé** | repris d'un import, non confirmé |

**Suggérer les positions et rôles** relit la documentation déjà
présente pour y trouver une mention explicite. Le modèle doit citer le
passage, et cette citation est vérifiée présente avant d'être retenue :
rien n'est déduit d'une morphologie, d'une nationalité ou d'un type de
scène. Une fiche sans mention reste vide — c'est le résultat attendu
dans la plupart des cas.

### 11.4 Comprendre ce qui a été collecté

Le plugin n'écrit que dans les champs vides. Une fiche déjà remplie ne
reçoit donc qu'une ou deux valeurs, ce qui peut laisser croire que la
collecte n'a rien trouvé.

**Inspecter la collecte d'une fiche** lève l'ambiguïté : pour chaque
champ, elle indique le nombre de sources, la valeur retenue avec sa
note et ses familles, les valeurs écartées, et l'état — vide et donc
écrit, déjà rempli à l'identique, en conflit non écrasé, ou fourni par
aucune source.

## 12. Scrapers manquants

Stash sait installer des scrapers depuis un catalogue, mais c'est à
l'utilisateur de deviner lesquels lui serviraient. Or l'information est
dans sa collection : les studios présents et les sites cités sur les
fiches disent exactement de quoi il a besoin.

**Deux choses séparées, et la distinction est le cœur du dispositif.**

La **détection** est automatique et sans risque : elle lit, compare,
rapporte. Elle se lance au bout de l'enrichissement des scènes et des
studios — le seul moment où la liste des studios est complète, puisque
ce sont ces tâches qui créent ceux qui manquaient — et au plus une fois
par jour, sans quoi enrichir une fiche unique interrogerait le
catalogue distant à chaque clic.

L'**installation** ne l'est pas. Un scraper est du code tiers qui
s'exécutera sur la machine de l'utilisateur et interrogera des sites en
son nom. Rien ne s'installe sans une demande explicite — argument
`installer=1` — ou sans le réglage *Installer les scrapers manquants*,
désactivé par défaut.

**Le rapprochement est exact**, jamais approximatif. « Say Uncle » et
« SayUncle » désignent la même chose ; « Brazil » ne doit pas ramener
« Brazzers ». Installer le mauvais scraper serait pire que n'en
installer aucun : il répondrait, avec des données qui ne concernent
personne.

Les sources propres aux interprètes — OnlyFans, ChaosMen, IMDB — ne
portent pas de nom de studio : elles se déduisent des adresses citées
sur les fiches.

Sur une collection d'une centaine de studios, un cinquième environ
s'est révélé couvert par un scraper installé, un autre cinquième par
un scraper disponible mais absent, et le reste sans équivalent au
catalogue. Les proportions varient beaucoup selon la collection.

## 12. Les sources d'enrichissement, et comment les choisir

Le plugin dispose de plusieurs façons d'apprendre quelque chose sur une
scène, et elles n'ont ni le même coût, ni le même risque, ni le même
rendement. Les imposer ensemble — ou les refuser ensemble — forcerait à
choisir entre trop et rien.

Chacune s'active donc séparément, et le choix par défaut suit une
règle simple : **ce qui devine ou transmet est éteint**.

| Source | Coût | Risque | Par défaut |
|---|---|---|---|
| Empreinte et sources | appels aux services tiers | aucun : le fichier est reconnu | actif |
| Chemin des fichiers | nul | suppose un rangement fiable | **actif** |
| Nom de fichier | nul | devine ; la valeur avoue sa moindre confiance | **actif** |
| Filigranes des vignettes | appels payants, images transmises | lecture, mais approximative | inactif |
| Génériques | appels payants, images transmises, dépendance | invention possible sur image agrandie | inactif |

### 12.1 Pourquoi le chemin d'abord

Une médiathèque rangée porte de l'information dans son rangement, et
cette information est gratuite, instantanée et exacte : ni réseau, ni
modèle, ni hallucination possible.

Sur une collection d'essai, cette seule source a comblé la grande
majorité des scènes sans studio et la totalité des scènes sans titre —
davantage que toutes les autres réunies, et sans un seul appel.

**Elle suppose un rangement fiable.** Quelqu'un dont les dossiers ne
décrivent pas ce qu'ils contiennent doit l'éteindre : le réglage existe
pour cela.

### 12.2 L'ordre compte

Ces sources se nourrissent l'une l'autre. Un titre et un studio tirés du
chemin donnent aux scrapers une prise qu'ils n'avaient pas : sur la
collection d'essai, l'enrichissement relancé APRÈS la lecture des
chemins a récupéré des dizaines de dates qu'il ne trouvait pas avant.

L'ordre recommandé, que le panneau numérote :

1. **Chemins** — gratuit, et prépare le terrain
2. **Scènes** — les sources exploitent ce que le chemin a établi
3. **Interprètes** et **studios**
4. **Vision** et **génériques**, s'ils sont activés, pour le reliquat

## 13. Ce que le rangement dit du contenu

Une médiathèque est rangée, et son rangement porte de l'information :
un dossier nomme souvent le studio, un nom de fichier la distribution.
Le plugin ne lisait que le nom de fichier — sur une collection réelle,
la grande majorité des scènes sans studio se trouvaient dans des
dossiers qui le portaient en toutes lettres.

**C'est plus fiable que la lecture d'image et sans commune mesure en
coût.** Aucun appel réseau, aucun modèle, aucune hallucination
possible : le texte est là.

**Mais un chemin n'est pas une preuve.** Le rapprochement reste exact,
rien n'est créé, rien n'est écrasé, et la provenance dit que la valeur
vient du rangement — non d'une source documentaire.

### 13.1 Ce qu'il faut savoir écarter

Le rangement réel est moins régulier que les exemples, et trois
familles de pièges se présentent.

**Les dossiers de travail** — « à trier », « rapatrié », « backup » —
décrivent une manipulation de fichiers, non leur contenu. Les prendre
pour des titres écrirait la même ligne sur des dizaines de scènes.

**Les mentions de format.** Un segment fait de sigles d'encodage
décrit le fichier ; aucun pris isolément ne suffit à l'écarter, mais
leur accumulation est un signal sûr.

**Les conventions de partage.** Un nom tel que
`[STUDIO][Gay]Titre 2018 VO 1080p WEB AAC H264` place les étiquettes avant le titre et la queue technique
après. Écarter le segment entier perdrait un vrai titre ; le garder
tel quel écrit une ligne illisible. L'année suivie d'une mention de
format est la frontière la plus sûre — un titre peut légitimement
finir par un nombre.

**Les parenthèses portent souvent la distribution** : les noms y sont
lus, puis retirés du titre où ils n'ont pas leur place.

## 13.2 Lire ce qui est écrit sur les vignettes

Une scène sans studio est difficile à enrichir : le studio est le
meilleur réducteur de candidats disponible, et sans lui les scrapers
dédiés ne peuvent rien. Or les vignettes portent presque toujours un
filigrane, parfois une adresse, parfois un titre incrusté.

**Le plugin ne cherche jamais à identifier une personne.** Ce n'est pas
une précaution de façade : les fournisseurs commerciaux refusent de le
faire, et un modèle sommé de reconnaître quelqu'un répond soit par un
refus, soit par une invention. Poser la question serait au mieux
inutile. Les instructions envoyées le disent explicitement, dans les
sept langues, et un contrôle automatique vérifie qu'aucune formulation
ne le demande.

**Trois refus protègent la lecture.** Un studio annoncé sans qu'aucun
texte n'ait été lu est une déduction visuelle, donc une supposition sur
un décor ou des personnes. Un nom qui ne se retrouve pas dans le texte
lu est une invention. Une confiance faible ne vaut pas qu'on écrive
quoi que ce soit.

**Rien n'est écrit sur la scène.** Une lecture de filigrane est une
hypothèse : elle se range dans un champ dédié, se rapproche du
catalogue de studios existant, et attend un arbitrage.

### 13.1 Les génériques, dans les sprites

La vignette d'une scène est prise au milieu : elle porte le filigrane,
jamais le générique. Stash produit aussi un SPRITE — une planche de
cases réparties sur toute la durée — avec un fichier qui donne les
coordonnées et l'horodatage de chacune. Les premières et dernières
cases contiennent ce que le milieu n'a pas, dont les noms des
interprètes au générique de fin.

**Le rendement est faible et assumé** : une scène sur cinq porte un
générique lisible. Mais ces scènes-là ne sont atteintes par aucun
autre moyen.

**Le risque est l'invention.** Une case fait 160×90 pixels ; agrandie,
elle invite le modèle à halluciner. Trois garde-fous : ce qui est
retenu doit ressembler à un nom — deux parties, ni chiffre, ni mention
de générique —, une case qui mêle des alphabets est entièrement
écartée, et plus de huit noms sur une case signalent une invention
plutôt qu'une distribution nombreuse.

**Un nom lu n'est jamais appliqué**, et ne crée jamais de fiche.
Attribuer une scène au mauvais interprète est l'erreur qu'aucun
arbitrage ne rattrape.

Cette lecture demande Pillow, que le plugin ne réclame pas : découper
une planche est la seule chose qui en ait besoin, et l'imposer à qui
ne s'en sert pas serait un coût sans contrepartie. Son absence est
annoncée, elle n'interrompt rien.

### 13.2 Envoi d'images : éteint par défaut

Le reste du plugin transmet du TEXTE — des noms, des dates. Une image
est d'une autre nature : elle est identifiante, peut être conservée par
le fournisseur, et expose des personnes qui n'ont rien demandé.

L'activation est donc un geste distinct de la configuration du modèle,
et vaut même pour un modèle installé chez soi : quelqu'un peut vouloir
qu'aucune image ne quitte Stash, quel qu'en soit le destinataire. La
tâche annonce la destination avant le premier envoi.

Une scène déjà lue n'est pas relue : la même vignette produirait la
même réponse et la même facture.

## 14. Langues

Un seul réglage pilote tout : les étiquettes, les messages, ET les
textes rédigés par le modèle. Sept langues sont couvertes — anglais,
français, allemand, espagnol, italien, portugais, néerlandais.

**Laissé vide, il suit la langue réglée dans Stash.** Demander à
l'utilisateur de la redire serait une redite, et laisserait une
installation en français produire de l'anglais parce qu'un second
réglage est resté vide. Les formes régionales — « fr-FR », « pt-BR » —
sont ramenées au code correspondant.

**Les instructions données au modèle sont traduites elles aussi.**
C'est moins évident que la langue de sortie, et tout aussi important :
un modèle sommé de répondre en néerlandais avec des consignes en
français obéit mal — il glisse vers la langue des consignes, et sa
compréhension des nuances se dégrade. Les six prompts du plugin —
présentation, biographie, synopsis, studio, rôles, mise en forme — sont
donc rédigés dans chacune des sept langues, y compris l'intitulé qui
introduit les données.

La consigne qui interdit d'inventer est la protection la plus
importante de ces prompts : un test vérifie qu'elle survit à chaque
traduction, faute de quoi une langue produirait des textes inventés là
où les autres s'en tiennent aux données.

Un prompt saisi par l'utilisateur prime sur tout : c'est le sien, et il
est employé tel quel.

Sept langues : anglais, français, allemand, espagnol, italien,
portugais, néerlandais. Le réglage pilote **les étiquettes** (tags
posés dans Stash), **les messages** (fiches et journal), **les
boutons**, **les noms de tâches** et **la langue de rédaction** des
textes produits.

Après un changement, une tâche dédiée renomme les tags déjà posés —
aucune donnée n'est perdue — et traduit l'interface. Les tags de toutes
les langues restent protégés du nettoyage.

---

## 15. Diagnostic

| Tâche | Répond à la question |
|---|---|
| **Rapport de run et hygiène** | qu'a produit le dernier passage ? que manque-t-il ? |
| **Rapport des tags** | ma taxonomie est-elle saine ? |
| **État de l'agent** | le service d'IA fonctionne-t-il ? que reste-t-il à faire ? |

---

## 16. Protections

- **Rien n'est écrasé** : seuls les champs vides sont complétés.
- **Les conflits sont visibles** sans être résolus d'autorité.
- **Une fiche que vous aviez déjà n'est jamais détruite**
  automatiquement.
- **Les identifiants ne sont jamais écrits sur disque** ; leur
  disparition est signalée, ils sont à ressaisir.
- **Les réglages sont sauvegardés** : la mutation `configurePlugin` de
  Stash remplace toute la table quand un outil n'écrit qu'une clé, ce
  qui vide la configuration sans prévenir. Une disparition massive est
  signalée et réparable.
- **Les images distantes sont contrôlées** : seules les adresses
  publiques en http(s) sont acceptées, une source compromise ne peut
  pas faire interroger le réseau local.
