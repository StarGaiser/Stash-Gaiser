#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Banc de mesure — à lancer à la demande, jamais dans la suite de tests.

    python3 tests/bench.py

Les tests posent des plafonds larges pour rester stables d'une machine à
l'autre. Ce banc, lui, donne les chiffres réels : c'est lui qui alimente
la section « Performance » des spécifications techniques, et c'est à lui
qu'on demande si une optimisation a servi à quelque chose.

Aucune connexion à Stash : les mesures portent sur le calcul et sur le
NOMBRE d'appels qu'une tâche émettrait, pas sur la latence du réseau —
laquelle dépend de l'installation et n'apprend rien sur le code.
"""

import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RACINE / "gaizer"))

import conftest  # noqa: E402  — installe le substitut de stashapi
_ = conftest

import groupes  # noqa: E402
import noyau  # noqa: E402
import scoring  # noqa: E402
import similarite  # noqa: E402
from faux import FauxStash, faux_contexte  # noqa: E402

# Volumes observés sur la collection de référence.
REEL = {"performers": 901, "scenes": 816, "studios": 134, "tags": 603}


def chrono(fonction, repetitions=1):
    meilleurs = []
    for _ in range(3):
        debut = time.perf_counter()
        for _ in range(repetitions):
            resultat = fonction()
        meilleurs.append(time.perf_counter() - debut)
    return min(meilleurs), resultat


def titre(texte):
    print(f"\n\033[1m{texte}\033[0m")
    print("─" * 66)


def ligne(quoi, valeur, note=""):
    print(f"  {quoi:<40s} {valeur:>12s}  {note}")


def jeu_de_noms(n):
    noms = [f"Interprete Numero {i}" for i in range(n)]
    objets = [{"id": str(i), "name": nom} for i, nom in enumerate(noms)]
    cles = {str(i): similarite._sim_cles(nom)
            for i, nom in enumerate(noms)}
    alias = {str(i): set() for i in range(n)}
    return objets, cles, alias


def mesurer_doublons():
    titre("Recherche de doublons — croissance")
    precedent = None
    for n in (100, 200, 400, 800, REEL["performers"]):
        duree, _paires = chrono(
            lambda n=n: similarite.paires_candidates(
                *jeu_de_noms(n), lambda f: set()))
        comparaisons = n * (n - 1) // 2
        rapport = f"×{duree / precedent:.1f}" if precedent else ""
        ligne(f"{n} fiches ({comparaisons} comparaisons)",
              f"{duree * 1000:.0f} ms", rapport)
        precedent = duree
    print("\n  Doubler la collection quadruple le travail : c'est la "
          "nature\n  d'une comparaison deux à deux. Un facteur nettement "
          "supérieur\n  signalerait un coût ajouté dans la boucle.")


def mesurer_notation():
    titre("Moteur de notation")
    valeurs = {"iafd": "1984-10-21", "gevi": "1984-10-21",
               "stashdb.org": "1984-10-22", "men": "1992-01-01",
               "falconstudios": "1990-05-05"}
    duree, _ = chrono(
        lambda: scoring.evaluer("birthdate", valeurs, scoring.DEFAUTS),
        1000)
    ligne("une évaluation (5 sources)", f"{duree:.1f} µs".replace(
        f"{duree:.1f}", f"{duree * 1000:.1f}"))
    total = REEL["performers"] * 8
    ligne(f"{total} évaluations (collection × 8 champs)",
          f"{duree * total / 1000:.2f} s")


def mesurer_tags():
    titre("Filtrage des tags")
    exclus = {"gay", "*pussy*", "*videos", "bonus*", "series", "4k"}
    duree, _ = chrono(
        lambda: noyau._tag_exclu("Hairy Pussy Licking", exclus), 10000)
    ligne("un tag contre 6 motifs", f"{duree * 100:.2f} µs")
    ligne(f"{REEL['tags']} tags", f"{duree * REEL['tags'] / 10:.1f} ms")


def mesurer_series():
    titre("Films en plusieurs parties")
    titres = [f"Une Serie Quelconque Part {i % 12}" for i in range(800)]
    duree, _ = chrono(lambda: [groupes._lire_partie(t) for t in titres])
    ligne(f"{len(titres)} titres analysés", f"{duree * 1000:.0f} ms")
    series = {
        groupes._cle_serie(f"Serie {i}"): {
            "nom": f"Serie {i}", "parties": [(1, {"id": str(i)})],
            "studios": {"1"}, "dates": [], "genre": "partie",
            "bonus": 0.5, "depuis_titre": True}
        for i in range(200)}
    duree, _ = chrono(lambda: groupes._fusionner_series(dict(series)))
    ligne("rapprochement de 200 séries", f"{duree * 1000:.0f} ms")


def mesurer_requetes():
    titre("Allers-retours évités par les caches")
    st = FauxStash(tags=[{"id": "1", "name": "Gaizer:créé"}])
    ctx = faux_contexte({}, st)
    for _ in range(1000):
        noyau.tag_id(ctx, "Gaizer:créé")
    ligne("1000 poses de tag", f"{st.appels['find_tags']} requête(s)",
          "sans cache : 1000")
    st2 = FauxStash(groups=[{"id": str(i), "name": f"F{i}",
                             "aliases": ""} for i in range(300)])
    ctx2 = faux_contexte({}, st2)
    for i in range(300):
        groupes._groupe_existant(ctx2, f"F{i}")
    ligne("300 recherches de groupe",
          f"{st2.appels['findGroups']} requête(s)", "sans cache : 300")


def mesurer_cout_ia():
    titre("Appels au modèle de langage")
    par_passe = (REEL["performers"] * 2 + REEL["scenes"]
                 + REEL["studios"])
    ligne("passe complète, collection vierge", f"{par_passe} appels")
    ligne("dont bio « hot »", f"{REEL['performers']} appels",
          "seul poste régénéré")
    ligne("passe suivante, sources inchangées", "~0 appel",
          "gardes + empreinte")
    print("\n  Bio factuelle, synopsis et présentation de studio ne "
          "sont produits\n  que sur un champ VIDE : ils ne se paient "
          "qu'une fois. La bio « hot »\n  est délibérément "
          "régénérable, d'où son empreinte de sources.")


if __name__ == "__main__":
    print("\n\033[1mGaizer — banc de mesure\033[0m")
    print(f"volumes de référence : "
          f"{REEL['performers']} interprètes, {REEL['scenes']} scènes, "
          f"{REEL['studios']} studios")
    mesurer_doublons()
    mesurer_notation()
    mesurer_tags()
    mesurer_series()
    mesurer_requetes()
    mesurer_cout_ia()
    print()
