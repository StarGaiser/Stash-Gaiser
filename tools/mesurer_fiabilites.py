#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fiabilité MESURÉE de chaque source, par champ.

Les poids du moteur (0,90 pour un annuaire, 0,40 pour un studio) sont
des jugements. Ce script les confronte aux faits : pour chaque source
et chaque champ, quelle proportion de ses valeurs concorde avec la
référence éditoriale ?

Si les fiabilités mesurées ressemblent aux fiabilités déclarées, les
poids sont fondés. Sinon, ils décrivent une intuition, pas la réalité —
et il vaut mieux le savoir.

    python3 tools/mesurer_fiabilites.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "tests"))
sys.path.insert(0, str(RACINE / "gaizer"))

import conftest  # noqa: E402
_ = conftest

import scoring  # noqa: E402
from valider_scoring import _comparable  # noqa: E402

CFG = scoring.DEFAUTS
REFERENCES = ("iafd", "gevi")
CHAMPS = ("birthdate", "height_cm", "country", "ethnicity",
          "circumcised")
MINIMUM = 5          # en deçà, la proportion ne veut rien dire


def main():
    donnees = json.loads(
        Path("/tmp/echantillon_sources.json").read_text(
            encoding="utf-8"))

    # (source, champ) → [accords, total]
    scores = defaultdict(lambda: [0, 0])
    # Les deux références sont aussi comparées l'une à l'autre : c'est
    # la seule façon de savoir si la « vérité » en est une.
    entre_refs = defaultdict(lambda: [0, 0])

    for fiche in donnees.values():
        sources = fiche.get("sources") or {}
        for champ in CHAMPS:
            refs = {s: v[champ] for s, v in sources.items()
                    if s.lower() in REFERENCES
                    and v.get(champ) not in (None, "")}
            if not refs:
                continue
            if len(refs) == 2:
                a, b = list(refs.values())
                entre_refs[champ][1] += 1
                if _comparable(champ, a, b):
                    entre_refs[champ][0] += 1
            reference = next(iter(refs.values()))
            for src, vals in sources.items():
                if src.lower() in REFERENCES:
                    continue
                val = vals.get(champ)
                if val in (None, ""):
                    continue
                scores[(src, champ)][1] += 1
                if _comparable(champ, val, reference):
                    scores[(src, champ)][0] += 1

    print("\n\033[1mLes références sont-elles d'accord entre "
          "elles ?\033[0m")
    print("IAFD et GEVI comparés l'un à l'autre — plafond de ce qu'on "
          "peut espérer.\n")
    for champ in CHAMPS:
        bons, tot = entre_refs[champ]
        if tot:
            print(f"  {champ:<14s} {bons:>3d}/{tot:<3d} "
                  f"({100*bons//tot:>3d} %)")

    print("\n\033[1mFiabilité mesurée par source\033[0m")
    print("Part des valeurs concordant avec la référence "
          f"(minimum {MINIMUM} observations).\n")
    print(f"  {'source':<22s} {'champ':<13s} {'mesuré':>10s} "
          f"{'déclaré':>9s}  écart")
    print("  " + "─" * 66)

    ecarts = []
    for (src, champ), (bons, tot) in sorted(
            scores.items(), key=lambda x: (x[0][1], -x[1][1])):
        if tot < MINIMUM:
            continue
        mesure = bons / tot
        declare = scoring.fiabilite(src, champ, CFG)
        ecart = mesure - declare
        ecarts.append((abs(ecart), src, champ, mesure, declare))
        marque = "  " if abs(ecart) < 0.15 else ("↑" if ecart > 0
                                                 else "↓")
        print(f"  {src[:21]:<22s} {champ:<13s} "
              f"{mesure:>7.0%} ({tot:>2d}) {declare:>8.2f}  "
              f"{marque} {ecart:+.2f}")

    if ecarts:
        moyen = sum(e[0] for e in ecarts) / len(ecarts)
        print(f"\n  Écart absolu moyen entre mesuré et déclaré : "
              f"{moyen:.2f}")
        pires = sorted(ecarts, reverse=True)[:5]
        print("  Écarts les plus marqués :")
        for _e, src, champ, m, d in pires:
            print(f"    {src} / {champ} : mesuré {m:.0%}, "
                  f"déclaré {d:.0%}")

    print("\n\033[1mClassement mesuré, tous champs confondus\033[0m\n")
    par_source = defaultdict(lambda: [0, 0])
    for (src, champ), (bons, tot) in scores.items():
        par_source[src][0] += bons
        par_source[src][1] += tot
    classement = sorted(
        ((b / t, s, b, t) for s, (b, t) in par_source.items()
         if t >= MINIMUM * 2), reverse=True)
    for taux, src, bons, tot in classement:
        declare_moyen = sum(
            scoring.fiabilite(src, c, CFG) for c in CHAMPS) / len(CHAMPS)
        barre = "█" * int(taux * 30)
        print(f"  {src[:21]:<22s} {taux:>5.0%} ({bons:>3d}/{tot:<3d}) "
              f"· déclaré {declare_moyen:.2f}  {barre}")
    print()


if __name__ == "__main__":
    main()
