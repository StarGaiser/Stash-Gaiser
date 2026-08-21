#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit avant publication : rien de personnel ne doit sortir.

Ce contrôle ne fait pas confiance aux tests. Il examine ce qui sera
RÉELLEMENT publié — le contenu de `git archive`, c'est-à-dire les
fichiers suivis à l'état courant — et non le dossier de travail, qui
contient des caches, des états déployés et des fichiers non versionnés.

La distinction n'est pas théorique : les caches de ruff et de coverage
portent des chemins absolus avec un nom d'utilisateur, et ils vivent
dans le dossier sans jamais être publiés.

Trois familles de fuites, par ordre de gravité :

  - l'IDENTITÉ : nom, pseudonyme, courriel, compte, nom de machine ;
  - la MACHINE : chemins absolus, adresses du réseau local, matériel ;
  - les SECRETS : clés d'API, jetons, mots de passe.

Le contrôle est volontairement plus large que nécessaire. Un faux
positif coûte une exception écrite ; un faux négatif coûte une
publication à reprendre — et ce qui est publié ne se reprend pas.

    python3 tools/auditer_avant_publication.py [motif supplémentaire…]
"""

import ast
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Ce qui doit apparaître à la place d'une identité.
PSEUDONYME = "gaizer"

MOTIFS = [
    # ── Identité ─────────────────────────────────────────────────────
    # Les formes de l'identité RÉELLE ne sont pas écrites ici : ce
    # fichier est publié, et les y inscrire divulguerait exactement ce
    # qu'on cherche à protéger. Elles sont lues plus bas depuis
    # `tests/identite_locale.py`, ignoré par git.
    ("identité", "nom propre en en-tête de licence",
     re.compile(r"Copyright\s*\(c\)\s*\d{4}\s+[A-Z][a-zà-ÿ]+"
                r"(?:[- ][A-Z][a-zà-ÿ]+)+")),
    ("identité", "adresse de courriel",
     # « git@github.com » est l'hôte SSH d'une adresse de dépôt, non
     # un courriel : le confondre ferait rejeter toute publication.
     # Le motif doit démarrer au DÉBUT du mot, sinon il se cale au
     # milieu et l'exclusion ne s'applique jamais : « git@github.com »
     # était retenu parce que la recherche commençait à « t@ ».
     re.compile(r"(?<![\w.+-])(?!git@)[\w.+-]+@"
                r"(?!users\.noreply|example|test|invalid)"
                r"[\w-]+\.[\w.]+")),
    ("identité", "nom d'utilisateur dans un chemin",
     re.compile(r"/(?:home|Users)/(?!<)[a-z][\w.-]+/")),
    # ── Machine ──────────────────────────────────────────────────────
    ("machine", "adresse du réseau local",
     re.compile(r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))"
                r"\.\d{1,3}\.\d{1,3}\b")),
    ("machine", "nom d'hôte local",
     re.compile(r"\b[\w-]+\.(?:local|lan|home)\b")),
    # ── Collection ───────────────────────────────────────────────────
    # Un dépôt PUBLIC expose aussi ce que la collection contient. Les
    # noms d'interprètes réels sont des personnes : les citer en
    # exemple, même dans un commentaire de code, décrit les goûts de
    # celui qui publie.
    # Les noms d'interprètes ne sont pas écrits ici non plus : mêmes
    # raisons que l'identité de l'auteur. Ils sont lus depuis le
    # fichier local.
    ("collection", "décompte précis d'une collection réelle",
     re.compile(r"\b\d{3,} (?:interprètes|scènes|studios|fiches)\b")),
    ("collection", "chemin de média",
     re.compile(r"/(?:mnt|media|Volumes)/[\w./-]*"
                r"(?:Vid[ée]os?|Movies|Films)[\w./-]*", re.I)),
    # ── Secrets ──────────────────────────────────────────────────────
    ("secret", "clé d'API",
     re.compile(r"\b(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}"
                r"|AIza[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})")),
    ("secret", "affectation de secret",
     re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*"
                r"[\"'][^\"'{}\s$]{16,}")),
]

# Ce qui est toléré, avec sa raison. Une exception sans raison finit
# par masquer une vraie fuite.
EXCEPTIONS = {
    ("tests/test_qualite.py", "identité"):
        "cite ces formes pour les interdire",
    ("tests/test_securite.py", "machine"):
        "énumère les adresses privées pour les refuser",
    ("tests/test_securite.py", "secret"):
        "clés factices employées comme cas d'essai",
    ("tools/auditer_avant_publication.py", "identité"):
        "ce fichier définit les motifs recherchés",
    ("tests/identite_locale.exemple.py", "identité"):
        "modèle à recopier : les noms y sont fictifs",
    ("tools/auditer_avant_publication.py", "machine"):
        "idem",
    ("tools/auditer_avant_publication.py", "secret"):
        "idem",
    ("tools/auditer_avant_publication.py", "collection"):
        "idem",
    ("gaizer/llm_providers.yml", "machine"):
        "adresse d'un modèle installé chez soi — un usage, non une fuite",
    ("gaizer/llm.py", "machine"):
        "idem",
    ("tests/test_chemins.py", "collection"):
        "chemins FICTIFS servant de cas d'essai au découpage",
    ("tests/test_llm.py", "machine"):
        "idem",
    ("tests/test_noyau.py", "machine"):
        "éprouve le refus des adresses privées",
    ("tests/test_vision.py", "machine"):
        "adresse d'un service local, donnée d'essai",
    ("tests/test_reglages.py", "machine"):
        "adresse d'un service local, donnée d'essai",
    ("docs/SPECIFICATIONS_TECHNIQUES.md", "machine"):
        "mentionne le matériel de mesure, sans identifiant",
}


def _liste(fichier, nom):
    """Lecture d'une liste de chaînes par l'ARBRE.

    Ce fichier est édité à la main : l'exécuter reviendrait à lancer
    ce qu'il contient, et le contrôle de sécurité du projet interdit
    « exec » — à juste titre ici aussi."""
    try:
        arbre = ast.parse(fichier.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == nom
                        for t in n.targets)
                and isinstance(n.value, ast.List)):
            return [e.value for e in n.value.elts
                    if isinstance(e, ast.Constant)
                    and isinstance(e.value, str)
                    and len(e.value) >= 4]
    return []


def _contenu_publie():
    """Ce que `git archive` produirait — donc ce qui sera publié.

    Examiner le dossier de travail donnerait de faux positifs à la
    pelle : les caches d'outils portent des chemins absolus et ne
    sortent jamais."""
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "a.tar"
        r = subprocess.run(["git", "archive", "-o", str(archive), "HEAD"],
                           cwd=RACINE, capture_output=True, check=False)
        if r.returncode:
            print("✗ git archive a échoué :",
                  r.stderr.decode()[:120], file=sys.stderr)
            return None
        with tarfile.open(archive) as tar:
            for membre in tar.getmembers():
                if not membre.isfile():
                    continue
                flux = tar.extractfile(membre)
                if flux is None:
                    continue
                brut = flux.read()
                try:
                    yield membre.name, brut.decode("utf-8")
                except UnicodeDecodeError:
                    # Un fichier binaire dans un dépôt de code mérite
                    # d'être signalé plutôt qu'ignoré.
                    yield membre.name, None


def main(motifs_sup):
    motifs = list(MOTIFS)
    # Formes de l'identité réelle, lues hors du dépôt. Sans ce
    # fichier, l'audit reste utile mais ne peut pas vérifier un nom
    # qu'il ne connaît pas : il le dit.
    locales = RACINE / "tests" / "identite_locale.py"
    if locales.exists():
        # Lecture par l'ARBRE plutôt que par exécution : ce fichier
        # est édité à la main, et l'exécuter reviendrait à lancer ce
        # qu'il contient. Le contrôle de sécurité du projet interdit
        # « exec », et il a raison de le faire ici aussi.
        formes = _liste(locales, "FORMES")
        for f in formes:
            motifs.append(("identité", "forme de l'identité réelle",
                           re.compile(re.escape(f), re.I)))
        for f in _liste(locales, "INTERPRETES"):
            motifs.append(("collection", "nom d'interprète cité",
                           re.compile(r"(?<![\w/])" + re.escape(f)
                                      + r"(?![\w/])")))
        print(f"  {len(formes)} forme(s) d'identité et "
              f"{len(_liste(locales, 'INTERPRETES'))} nom(s) de la "
              f"collection chargés\n    (fichier local, non publié)")
    else:
        print("  ⚠ tests/identite_locale.py absent : l'audit ne peut "
              "pas\n    vérifier un nom réel. Le créer depuis "
              "identite_locale.exemple.py")
    for m in motifs_sup:
        motifs.append(("demandé", f"motif « {m} »",
                       re.compile(re.escape(m), re.I)))

    fuites, binaires, examines = [], [], 0
    contenu = _contenu_publie()
    if contenu is None:
        return 2
    for nom, texte in contenu:
        if texte is None:
            binaires.append(nom)
            continue
        examines += 1
        for famille, quoi, motif in motifs:
            if EXCEPTIONS.get((nom, famille)):
                continue
            for i, ligne in enumerate(texte.split("\n"), 1):
                trouve = motif.search(ligne)
                if trouve:
                    fuites.append((famille, nom, i, quoi,
                                   trouve.group(0)[:48]))

    print(f"  {examines} fichier(s) examinés dans l'archive publiable")
    if binaires:
        print(f"  ⚠ {len(binaires)} fichier(s) binaire(s) : "
              f"{', '.join(binaires[:4])}")

    if not fuites:
        print("\n  ✓ aucune trace personnelle dans ce qui serait publié")
        print("    (le dossier de travail contient des caches et un "
              "état déployé\n     qui ne sortent pas — c'est normal)")
        return 0

    print(f"\n  ✗ {len(fuites)} trace(s) à retirer AVANT publication :\n")
    for famille in ("secret", "identité", "collection",
                    "machine", "demandé"):
        lot = [f for f in fuites if f[0] == famille]
        if not lot:
            continue
        print(f"  ── {famille.upper()} ──")
        for _f, nom, ligne, quoi, extrait in lot[:20]:
            print(f"    {nom}:{ligne}  {quoi}")
            print(f"        « {extrait} »")
        if len(lot) > 20:
            print(f"    … et {len(lot) - 20} autre(s)")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
