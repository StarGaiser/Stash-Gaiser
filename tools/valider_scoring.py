#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validation empirique du moteur de notation.

Le moteur repose sur des poids — 0,90 pour un annuaire éditorial, 0,40
pour un site de studio — qui sont des jugements, jamais confrontés à
quoi que ce soit. Un système de notation invérifiable donne surtout une
impression de rigueur.

MÉTHODE, dite de la source retirée. Pour chaque fiche où une source
éditoriale (IAFD, GEVI) fournit une valeur :

  1. cette valeur est mise de côté et tenue pour référence ;
  2. la source éditoriale est RETIRÉE des données ;
  3. le moteur choisit parmi ce qui reste ;
  4. son choix est comparé à la référence.

La mesure obtenue répond à une question précise : **les poids
permettent-ils de retrouver ce que dirait un annuaire éditorial, quand
on ne l'a pas ?** C'est exactement le cas d'usage — la plupart des
fiches n'ont que des sources commerciales.

Le protocole n'est pas circulaire : la référence est extérieure aux
données soumises au moteur.

TÉMOINS. Le moteur est comparé à deux stratégies naïves :

  - « première source » : prendre ce que dit la première venue ;
  - « vote majoritaire » : la valeur la plus répandue, sans pondérer.

Si le moteur ne bat pas le vote majoritaire, les poids n'apportent
rien et la complexité n'est pas justifiée.

    python3 tools/valider_scoring.py [/tmp/echantillon_sources.json]
"""

import json
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "tests"))
sys.path.insert(0, str(RACINE / "gaizer"))

import conftest  # noqa: E402  — substitut de stashapi
_ = conftest

import scoring  # noqa: E402

CFG = scoring.DEFAUTS
REFERENCES = ("iafd", "gevi")
CHAMPS = ("birthdate", "height_cm", "country", "ethnicity",
          "circumcised", "measurements")


def _comparable(champ, a, b) -> bool:
    """Deux valeurs disent-elles la même chose ?

    La tolérance appliquée est celle du moteur lui-même : un jour
    d'écart sur une date, deux centimètres sur une taille. Exiger
    l'égalité stricte ferait compter comme erreur ce que le moteur
    traite délibérément comme un accord."""
    if a is None or b is None:
        return False
    sa, sb = str(a).strip().lower(), str(b).strip().lower()
    if not sa or not sb:
        return False
    if sa == sb:
        return True
    if champ == "birthdate":
        # Une référence peut se réduire à l'année (« 2000 ») quand
        # l'annuaire n'en sait pas plus : comparer à une date complète
        # sur l'année seule, sinon on compterait comme erreur une
        # réponse plus précise et concordante.
        if len(sa) == 4 or len(sb) == 4:
            return sa[:4] == sb[:4]
        da, db = scoring._date(a), scoring._date(b)
        return bool(da and db and abs((da - db).days) <= 1)
    if champ == "height_cm":
        ia, ib = scoring._entier(a), scoring._entier(b)
        return bool(ia and ib and abs(ia - ib) <= 2)
    return False


def _premier(valeurs):
    for v in valeurs.values():
        if v not in (None, ""):
            return v
    return None


def _majoritaire(champ, valeurs):
    """Valeur la plus répandue, chaque source comptant pour une voix —
    sans notion de famille ni de fiabilité."""
    compte = Counter()
    for v in valeurs.values():
        if v in (None, ""):
            continue
        cle = None
        for connue in compte:
            if _comparable(champ, connue, v):
                cle = connue
                break
        compte[cle if cle is not None else v] += 1
    return compte.most_common(1)[0][0] if compte else None


def _moteur(champ, valeurs):
    cands = scoring.evaluer(champ, valeurs, CFG)
    return cands[0]["valeur"] if cands else None


def analyser(donnees: dict) -> dict:
    resultats = {}
    for champ in CHAMPS:
        cas = []
        for nom, fiche in donnees.items():
            sources = fiche.get("sources") or {}
            refs = {s: v for s, v in sources.items()
                    if s.lower() in REFERENCES
                    and v.get(champ) not in (None, "")}
            if not refs:
                continue
            reference = next(iter(refs.values())).get(champ)
            restantes = {s: v[champ] for s, v in sources.items()
                         if s.lower() not in REFERENCES
                         and v.get(champ) not in (None, "")}
            if len(restantes) < 2:
                continue        # sans choix à faire, rien à mesurer
            cas.append({
                "nom": nom, "reference": reference,
                "restantes": restantes,
                "moteur": _moteur(champ, restantes),
                "majoritaire": _majoritaire(champ, restantes),
                "premier": _premier(restantes),
            })
        if not cas:
            continue
        note = {}
        for strategie in ("moteur", "majoritaire", "premier"):
            bons = sum(1 for c in cas
                       if _comparable(champ, c[strategie],
                                      c["reference"]))
            note[strategie] = (bons, len(cas))
        resultats[champ] = {"cas": cas, "scores": note}
    return resultats


def rapport(resultats: dict):
    print("\n\033[1mValidation du moteur de notation — source "
          "retirée\033[0m")
    print("La référence (IAFD/GEVI) est masquée ; le moteur choisit "
          "parmi le reste.\n")
    entete = (f"  {'champ':<14s} {'cas':>4s} {'moteur':>14s} "
              f"{'majoritaire':>14s} {'1re source':>14s}")
    print(entete)
    print("  " + "─" * (len(entete) - 2))
    totaux = Counter()
    for champ, res in resultats.items():
        s = res["scores"]
        n = s["moteur"][1]
        ligne = f"  {champ:<14s} {n:>4d}"
        for strategie in ("moteur", "majoritaire", "premier"):
            bons, tot = s[strategie]
            totaux[strategie] += bons
            totaux[strategie + "_tot"] += tot
            ligne += f" {bons:>4d} ({100*bons//max(1,tot):>3d} %)"
        print(ligne)
    print("  " + "─" * (len(entete) - 2))
    ligne = f"  {'ENSEMBLE':<14s} {totaux['moteur_tot']:>4d}"
    for strategie in ("moteur", "majoritaire", "premier"):
        bons = totaux[strategie]
        tot = totaux[strategie + "_tot"]
        ligne += f" {bons:>4d} ({100*bons//max(1,tot):>3d} %)"
    print(ligne)

    ecart = totaux["moteur"] - totaux["majoritaire"]
    print()
    if ecart > 0:
        print(f"  Le moteur retrouve la référence {ecart} fois de plus "
              f"que le vote majoritaire :\n  la pondération apporte "
              f"quelque chose.")
    elif ecart == 0:
        print("  Le moteur fait JEU ÉGAL avec un vote majoritaire non "
              "pondéré.\n  Les poids n'apportent rien de mesurable sur "
              "cet échantillon.")
    else:
        print(f"  Le moteur fait {-ecart} fois PIRE que le vote "
              f"majoritaire.\n  Les poids dégradent la sélection : ils "
              f"sont à revoir.")

    print("\n\033[1mDésaccords du moteur\033[0m")
    for champ, res in resultats.items():
        rates = [c for c in res["cas"]
                 if not _comparable(champ, c["moteur"], c["reference"])]
        if not rates:
            continue
        print(f"\n  {champ} — {len(rates)} cas")
        for c in rates[:6]:
            sources = ", ".join(f"{s}={v}"
                                for s, v in list(c["restantes"].items())[:4])
            print(f"    {c['nom'][:26]:28s} référence {c['reference']}"
                  f" · moteur {c['moteur']}")
            print(f"      {sources}")


def main():
    chemin = Path(sys.argv[1] if len(sys.argv) > 1
                  else "/tmp/echantillon_sources.json")
    if not chemin.exists():
        print(f"Échantillon absent : {chemin}\n"
              f"Le collecter d'abord avec collecte_echantillon.py")
        return 1
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    avec = sum(1 for v in donnees.values()
               if len(v.get("sources") or {}) >= 2)
    print(f"{len(donnees)} fiches, {avec} avec au moins deux sources.")
    resultats = analyser(donnees)
    if not resultats:
        print("Aucun cas exploitable : il faut des fiches où une "
              "source éditoriale ET deux autres renseignent le même "
              "champ.")
        return 1
    rapport(resultats)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
