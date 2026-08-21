#!/usr/bin/env bash
# Prépare la publication sous un compte distinct.
#
# Le dépôt actuel est associé à un compte nominatif. Trois choses en
# découlent, et une seule se corrige dans les fichiers.
#
#   - Les chemins absolus portaient un nom d'utilisateur : retirés.
#   - L'auteur des commits est déjà pseudonyme : rien à faire.
#   - Les messages de commit citent des interprètes de la collection :
#     cela ne se corrige PAS en modifiant le dépôt. L'historique doit
#     être abandonné, pas réécrit — une réécriture laisse des traces
#     dans les forks, les caches et les copies locales.
#
# Ce script crée donc un dépôt NEUF, sans historique, à partir de
# l'état courant. On perd la trace du développement ; les documents de
# docs/ en tiennent lieu.
#
# Usage :
#   ./tools/preparer_publication.sh <compte-github> [nom-du-depot]
#
# Le nom du projet reste « Stash-GAIzer ».

set -euo pipefail

COMPTE="${1:-}"
DEPOT="${2:-Stash-Gaiser}"
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CIBLE="${SOURCE}/../${DEPOT}-public"

if [[ -z "$COMPTE" ]]; then
  echo "Usage : $0 <compte-github> [nom-du-depot]" >&2
  echo >&2
  echo "Le compte doit être DISTINCT du compte professionnel." >&2
  exit 1
fi

if [[ -e "$CIBLE" ]]; then
  echo "« $CIBLE » existe déjà. Le retirer ou choisir un autre nom." >&2
  exit 1
fi

echo "── Contrôles avant copie ──"

# Ces contrôles doublent ceux de tests/test_qualite.py. La redondance
# est voulue : une publication ne doit pas dépendre du fait que
# quelqu'un a lancé les tests.
cd "$SOURCE"
# L'audit examine ce que « git archive » produirait — donc ce qui sera
# RÉELLEMENT publié — et non le dossier de travail, qui contient des
# caches d'outils et un état déployé portant des chemins personnels
# sans jamais sortir.
python3 tools/auditer_avant_publication.py \
  || { echo "✗ publication interrompue" >&2; exit 1; }

if [[ -d "tests/fixtures_locales" ]]; then
  echo "  ✓ jeu d'essai local présent (il ne sera PAS copié)"
fi

python3 -m pytest -q >/dev/null 2>&1 \
  && echo "  ✓ suite de tests au vert" \
  || { echo "✗ tests en échec — publication interrompue" >&2; exit 1; }

echo
echo "── Copie sans historique ──"
mkdir -p "$CIBLE"
git archive HEAD | tar -x -C "$CIBLE"

# L'index de source n'a de sens que sur le dépôt PUBLIC : c'est lui
# que Stash interroge pour installer le plugin. Sur le dépôt privé,
# GitHub Pages n'est pas disponible sans abonnement, et le workflow y
# échouait à chaque poussée — un courriel d'échec pour une
# publication que personne n'attend.
#
# Le gabarit vit donc dans « tools/ », et n'est posé qu'ici.
mkdir -p "$CIBLE/.github/workflows"
cp tools/index-source.yml "$CIBLE/.github/workflows/index-source.yml"
rm -f "$CIBLE/tools/index-source.yml"
cd "$CIBLE"

# Le jeu d'essai contient des données réelles : il est produit sur
# place par celui qui lance les tests, jamais transporté.
rm -rf tests/fixtures_locales

# AGENTS.md est déjà exclu par .gitattributes (export-ignore), ce
# que l'audit d'anonymat examine. Cette suppression est une seconde
# barrière : si l'exclusion d'archive échouait, le fichier partirait
# quand même.
rm -f AGENTS.md

# L'adresse du projet suit le nouveau compte.
if [[ -f gaizer/gaizer.yml ]]; then
  python3 - "$COMPTE" "$DEPOT" <<'PY'
import sys, yaml, pathlib
compte, depot = sys.argv[1], sys.argv[2]
p = pathlib.Path("gaizer/gaizer.yml")
d = yaml.safe_load(p.read_text())
d["url"] = f"https://github.com/{compte}/{depot}"
p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False,
                            width=78))
print(f"  ✓ url du plugin : {d['url']}")
PY
fi

git init -q
git branch -M main

# L'identité des commits reste pseudonyme et LOCALE à ce dépôt :
# la configuration globale de la machine n'est pas touchée.
git config user.name "gaizer"
git config user.email "gaizer@users.noreply.github.com"

# Le « :- » de bash collerait un tiret devant l'adresse, que
# l'audit prendrait pour un courriel : deux lignes lèvent
# l'ambiguïté.
DEFAUT_REMOTE="git@github.com:${COMPTE}/${DEPOT}.git"
git remote add origin "${REMOTE:=$DEFAUT_REMOTE}"

# ── Reprendre l'historique déjà publié ───────────────────────────────
# Sans cela, chaque publication repart de zéro et efface la
# précédente : personne ne peut voir ce qui a changé.
#
# Le passé PRIVÉ n'est pas repris — il porte des dates, des rythmes
# de travail et des tâtonnements qui disent des choses sur qui écrit.
# L'historique public commence à la première publication qui suit.
if git fetch -q origin main 2>/dev/null; then
  git reset -q --soft FETCH_HEAD
  echo "  ✓ historique public repris ($(git rev-list --count \
        FETCH_HEAD) commit(s))"
else
  echo "  ✓ premier dépôt public : l'historique commence ici"
fi

git add -A

# ── Le message, contrôlé avant d'être public ─────────────────────────
MESSAGE="${MESSAGE_PUBLICATION:-}"
if [ -z "$MESSAGE" ]; then
  MESSAGE="Publication du $(date -u +%Y-%m-%d)"
fi

# Chemin absolu : à ce point, le dossier courant est la CIBLE,
# où cet outil n'existe pas — il vit dans la source.
python3 "$SOURCE/tools/auditer_message.py" "$MESSAGE" \
  || { echo "✗ publication interrompue" >&2; exit 1; }

if git diff --cached --quiet; then
  echo "  ✓ rien de neuf à publier"
else
  git commit -q -m "$MESSAGE"
  echo "  ✓ commit : $MESSAGE"
fi

echo
echo "── Prêt ──"
echo "  dépôt : $CIBLE"
echo "  auteur : $(git config user.name) <$(git config user.email)>"
echo "  distant : $(git remote get-url origin)"
echo
echo "Créer le dépôt « $DEPOT » sous « $COMPTE » sur GitHub, puis :"
echo "  cd $CIBLE && git push -u origin main"
echo
echo "Vérifier avant de pousser :"
echo "  - le dépôt GitHub est-il créé sous le BON compte ?"
echo "  - la clé SSH employée appartient-elle à ce compte ?"
echo "    (git config core.sshCommand, ou une entrée dédiée dans"
echo "     ~/.ssh/config — une clé partagée relie les deux comptes)"
