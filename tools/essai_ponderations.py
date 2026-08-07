#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Banc d'essai des variantes de pondération.

La validation a montré que le moteur fait jeu égal avec un vote
majoritaire : les poids n'apportent rien. Le diagnostic pointe le
bonus d'accord, qui est FORFAITAIRE — un site de studio qui confirme
rapporte autant qu'un annuaire éditorial, si bien que deux sources
médiocres l'emportent toujours sur une bonne.

Ce script mesure plusieurs variantes sur les mêmes données, afin de
n'appliquer au plugin que ce qui est démontré. Une variante qui ne bat
pas le vote majoritaire ne mérite pas d'exister : elle ajouterait de la
complexité pour rien.

    python3 tools/essai_ponderations.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "tests"))
sys.path.insert(0, str(RACINE / "gaizer"))

import conftest  # noqa: E402
_ = conftest

import scoring  # noqa: E402
from valider_scoring import _comparable, _majoritaire  # noqa: E402

CFG = scoring.DEFAUTS
REFERENCES = ("iafd", "gevi")
CHAMPS = ("birthdate", "height_cm", "country", "ethnicity")


def _groupes(champ, valeurs):
    """[(valeur, [sources])] — valeurs proches regroupées."""
    groupes = []
    for src, val in valeurs.items():
        if val in (None, ""):
            continue
        for g in groupes:
            if _comparable(champ, g[0], val):
                g[1].append(src)
                break
        else:
            groupes.append([val, [src]])
    return groupes


def _familles(sources):
    return {scoring.famille_de(s, CFG) for s in sources}


# ── Variantes ────────────────────────────────────────────────────────
def actuelle(champ, valeurs):
    """Ce que fait le plugin : meilleure fiabilité + 1 point par
    famille supplémentaire, plafonné à 2."""
    meilleur, note_max = None, -1
    for val, srcs in _groupes(champ, valeurs):
        base = 10 * max(scoring.fiabilite(s, champ, CFG) for s in srcs)
        bonus = min(2.0, 1.0 * (len(_familles(srcs)) - 1))
        note = base + bonus
        if note > note_max:
            meilleur, note_max = val, note
    return meilleur


def bonus_pondere(champ, valeurs, facteur=1.5):
    """Le bonus dépend de la QUALITÉ des sources qui confirment.

    Une source à 0,9 qui appuie apporte plus qu'une source à 0,4 :
    c'est ce que le bonus forfaitaire ignorait."""
    meilleur, note_max = None, -1
    for val, srcs in _groupes(champ, valeurs):
        fiab = sorted((scoring.fiabilite(s, champ, CFG) for s in srcs),
                      reverse=True)
        base = 10 * fiab[0]
        vues = set()
        bonus = 0.0
        for s, f in zip(sorted(srcs, key=lambda x: -scoring.fiabilite(
                x, champ, CFG)), fiab, strict=True):
            fam = scoring.famille_de(s, CFG)
            if fam in vues:
                continue
            vues.add(fam)
            if len(vues) > 1:
                bonus += facteur * f
        note = base + min(3.0, bonus)
        if note > note_max:
            meilleur, note_max = val, note
    return meilleur


def somme_fiabilites(champ, valeurs):
    """Chaque famille apporte sa fiabilité, sans notion de « base »."""
    meilleur, note_max = None, -1
    for val, srcs in _groupes(champ, valeurs):
        par_famille = {}
        for s in srcs:
            fam = scoring.famille_de(s, CFG)
            f = scoring.fiabilite(s, champ, CFG)
            par_famille[fam] = max(par_famille.get(fam, 0), f)
        note = sum(par_famille.values())
        if note > note_max:
            meilleur, note_max = val, note
    return meilleur


def fiabilite_seule(champ, valeurs):
    """Aucun bonus : la meilleure source l'emporte, point."""
    meilleur, note_max = None, -1
    for val, srcs in _groupes(champ, valeurs):
        note = max(scoring.fiabilite(s, champ, CFG) for s in srcs)
        if note > note_max:
            meilleur, note_max = val, note
    return meilleur


VARIANTES = {
    "majoritaire (témoin)": lambda c, v: _majoritaire(c, v),
    "actuelle (plugin)": actuelle,
    "fiabilité seule": fiabilite_seule,
    "somme des fiabilités": somme_fiabilites,
    "bonus pondéré ×1.0": lambda c, v: bonus_pondere(c, v, 1.0),
    "bonus pondéré ×1.5": lambda c, v: bonus_pondere(c, v, 1.5),
    "bonus pondéré ×2.5": lambda c, v: bonus_pondere(c, v, 2.5),
}


def cas_de_test(donnees):
    cas = []
    for champ in CHAMPS:
        for nom, fiche in donnees.items():
            sources = fiche.get("sources") or {}
            refs = [v.get(champ) for s, v in sources.items()
                    if s.lower() in REFERENCES
                    and v.get(champ) not in (None, "")]
            if not refs:
                continue
            restantes = {s: v[champ] for s, v in sources.items()
                         if s.lower() not in REFERENCES
                         and v.get(champ) not in (None, "")}
            if len(restantes) < 2:
                continue
            # Un désaccord entre les sources restantes est nécessaire :
            # là où toutes disent la même chose, aucune stratégie ne
            # peut se distinguer.
            if len(_groupes(champ, restantes)) < 2:
                continue
            cas.append((champ, nom, refs[0], restantes))
    return cas


def main():
    chemin = Path("/tmp/echantillon_sources.json")
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    cas = cas_de_test(donnees)
    print(f"\n\033[1mVariantes de pondération — {len(cas)} cas de "
          f"DÉSACCORD réel\033[0m")
    print("Seuls les cas où les sources se contredisent sont retenus :")
    print("ailleurs, toutes les stratégies donnent le même résultat.\n")
    par_champ = Counter(c[0] for c in cas)
    print("  répartition :", dict(par_champ), "\n")

    resultats = {}
    for nom, fonction in VARIANTES.items():
        bons = 0
        for champ, _p, reference, restantes in cas:
            try:
                choix = fonction(champ, restantes)
            except Exception:
                choix = None
            if _comparable(champ, choix, reference):
                bons += 1
        resultats[nom] = bons
        part = 100 * bons // max(1, len(cas))
        barre = "█" * (bons * 40 // max(1, len(cas)))
        print(f"  {nom:<24s} {bons:>3d}/{len(cas)} ({part:>3d} %) "
              f"{barre}")

    temoin = resultats["majoritaire (témoin)"]
    print()
    meilleure = max(resultats.items(), key=lambda x: x[1])
    if meilleure[1] > temoin:
        print(f"  Meilleure variante : « {meilleure[0]} », "
              f"{meilleure[1] - temoin} cas de plus que le vote "
              f"majoritaire.")
    else:
        print("  Aucune variante ne bat le vote majoritaire sur ces "
              "données.")
    print()


if __name__ == "__main__":
    main()
