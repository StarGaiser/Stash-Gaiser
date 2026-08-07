# Gaizer

*[English version](README.md)*

> **Enrichissement de médiathèque pour [Stash](https://github.com/stashapp/stash).**
> Complète interprètes, scènes et studios depuis plusieurs sources à la
> fois, arbitre les désaccords en gardant la trace de chaque valeur,
> détecte les doublons et reconstitue les films en plusieurs parties.
> Tout ce qu'il écrit peut être défait ; rien n'est écrasé sans
> décision explicite.

**Sujets** : `stash` · `stash-plugin` · `metadata` · `enrichment` ·
`python` · `graphql` · `self-hosted`

---

## En quoi il diffère

La plupart des outils d'enrichissement choisissent une source et
écrivent ce qu'elle dit. Gaizer interroge toutes celles que votre Stash
connaît — stash-boxes et scrapers d'interprètes installés — puis doit
décider quoi faire quand elles se contredisent, ce qui arrive la
plupart du temps.

**Chaque valeur porte son origine.** Un panneau s'insère dans les
fiches d'interprètes et de studios : il montre ce qui a été collecté,
depuis combien de familles de sources indépendantes, avec une note de
confiance et un commentaire qui l'explique. Une valeur dont on ne peut
pas remonter l'origine vaut moins que pas de valeur du tout.

**Rien n'est écrasé.** Les champs vides sont complétés ; ceux qui
contiennent déjà quelque chose sont laissés tels quels, et le désaccord
est enregistré. Une tâche séparée et explicite peut passer outre —
c'est la seule — et elle conserve l'ancienne valeur pour que le
changement se défasse.

**Tout est réversible.** Dix passages d'historique par fiche.
*Annuler le dernier passage* remet les champs, retire les étiquettes
et les liens ajoutés, et remonte d'un cran à chaque relance.

**Il dit quand il ne sait pas.** Un interprète peu documenté reçoit un
texte court, ou rien. Le modèle de langage doit citer le passage sur
lequel il s'appuie, et cette citation est vérifiée présente dans le
texte source avant que la valeur soit retenue — seul garde-fou possible
contre une citation fabriquée.

## Ce qu'il couvre

| | |
|---|---|
| **Interprètes** | biographie, date de naissance, nationalité, ethnicité, mensurations, carrière, photos, rôles |
| **Scènes** | identification par empreinte, titre, date, studio, distribution, tags, synopsis, jaquettes officielles |
| **Studios** | réseau parent, site, présentation, logo |
| **Groupes** | reconstitue les films répartis sur plusieurs fichiers |
| **Doublons** | détecte et fusionne interprètes et studios, jamais automatiquement pour les fiches que vous aviez déjà |
| **Tags** | mesure lesquels distinguent réellement quelque chose dans votre collection |

Sept langues d'interface — anglais, français, allemand, espagnol,
italien, portugais, néerlandais — et les textes rédigés suivent le même
réglage. Laissé vide, il suit la langue que vous avez choisie dans
Stash.

## Installation

Gaizer ne figure pas encore au catalogue CommunityScripts. En
attendant :

```bash
cd <votre configuration Stash>/plugins
git clone https://github.com/StarGaiser/Stash-Gaiser.git gaizer
pip install stashapp-tools pyyaml
```

Puis **Settings → Plugins → Reload**. Un bouton **GZ** apparaît dans la
barre de navigation ; il ouvre le panneau de commande.

Requiert Stash ≥ 0.25 pour les panneaux d'interface. Les tâches
d'enrichissement fonctionnent sur les versions antérieures.

## Premier lancement

L'ordre compte, et le panneau le numérote :

1. **Scènes** — elles créent les interprètes et studios manquants
2. **Interprètes** — complète ce que les scènes ont laissé vide
3. **Studios**
4. **Proposer des tags à écarter** — rapport seulement

Chaque tâche destructive propose **Simuler** à côté de **Lancer**.
Servez-vous-en : elle dit exactement ce qui changerait, sans rien
changer.

## Modèles de langage

Facultatif. Gaizer fonctionne sans — il n'écrira simplement ni
présentations ni synopsis.

N'importe quel fournisseur compatible OpenAI convient, y compris local
(Ollama, LM Studio, llama.cpp, vLLM). Les instructions envoyées au
modèle sont **traduites** dans votre langue plutôt que de simplement
demander une réponse dans celle-ci : un modèle qui reçoit des consignes
en français et doit répondre en néerlandais glisse vers le français.

## Ce que ce n'est pas

**Pas un scraper.** Il emploie ceux que vous avez déjà, et sait dire
lesquels du catalogue correspondraient aux studios de votre collection.

**Pas un outil de reconnaissance faciale.** [Star
Identifier](https://github.com/stashapp/CommunityScripts) fait cela, et
Gaizer est bâti pour travailler à côté plutôt que de le remplacer.

**Pas une solution miracle.** Sur les champs où les annuaires de
référence se contredisent entre eux, aucun arbitrage ne peut faire
mieux que les sources. Ce que Gaizer apporte là, c'est la traçabilité :
vous voyez le désaccord et vous décidez.

## Prudence

Certaines actions sont **irréversibles** et le disent dans leur nom.
Une fusion **supprime** la fiche absorbée ; un alignement sur les
sources **écrase** une valeur existante — l'ancienne passe dans
l'historique, mais la fusion, elle, est **sans retour**.

Une fiche que vous aviez déjà n'est **jamais détruite
automatiquement** : seule une fiche créée par le plugin peut être
absorbée sans votre accord.

## Documentation

- [Spécifications fonctionnelles](docs/SPECIFICATIONS_FONCTIONNELLES.md)
  — ce que le plugin fait et pourquoi, en détail
- [Spécifications techniques](docs/SPECIFICATIONS_TECHNIQUES.md) —
  architecture, pièges de l'API Stash, mesures
- [Normes de codage](docs/NORMES_DE_CODAGE.md) — les règles suivies
- [Tests](docs/TESTS.md) — ce qui est couvert, et ce qui ne l'est
  délibérément pas

## Licence

AGPL-3.0-or-later, comme Stash lui-même.

Quiconque s'en sert dans un service accessible par le réseau doit en
publier le code modifié. Utilisez-le, modifiez-le, partagez-le — mais
pas derrière une porte fermée.
