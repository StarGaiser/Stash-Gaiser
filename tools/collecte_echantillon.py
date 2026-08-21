#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collecte un échantillon de données brutes, source par source.

Le plugin ne conserve que la valeur RETENUE, jamais ce que chaque
source proposait. Impossible, donc, de mesurer après coup si le moteur
a bien choisi. Ce script rejoue la collecte sur un échantillon et
enregistre le détail, afin que l'analyse puisse être relancée autant de
fois que nécessaire sans réinterroger le réseau.

    docker exec stash python3 /root/.stash/plugins/gaizer/collecte_echantillon.py 60

Sortie : /tmp/echantillon_sources.json
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import noyau
from collecte import collecter_stash, passe_url

SORTIE = Path("/tmp/echantillon_sources.json")


def main():
    combien = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    ctx = noyau.Context()
    perfs = ctx.stash.find_performers()

    # On ne retient que les fiches susceptibles d'être documentées par
    # plusieurs sources : un nom d'une seule partie (« Archie ») ne
    # donnera rien d'exploitable.
    candidats = [p for p in perfs
                 if len((p.get("name") or "").split()) >= 2]
    candidats.sort(key=lambda p: p["name"])
    # Échantillonnage régulier plutôt que les N premiers : évite de ne
    # prendre que le début de l'alphabet.
    pas = max(1, len(candidats) // combien)
    echantillon = candidats[::pas][:combien]

    print(f"{len(perfs)} fiches, {len(candidats)} exploitables, "
          f"{len(echantillon)} échantillonnées", flush=True)

    resultats = {}
    for i, p in enumerate(echantillon, 1):
        nom = p["name"]
        try:
            raw, urls = collecter_stash(ctx, nom)
            # `passe_url` consulte lui-même le réglage useUrlPass.
            raw2 = passe_url(ctx, p, urls)
            for src, vals in (raw2 or {}).items():
                raw.setdefault(src, {}).update(vals)
            resultats[nom] = {
                "id": p["id"],
                "sources": {s: {k: v for k, v in vals.items()
                                if not isinstance(v, (list, dict))}
                            for s, vals in raw.items()},
            }
            n_src = len(raw)
        except Exception as exc:
            resultats[nom] = {"id": p["id"], "sources": {},
                              "erreur": str(exc)[:120]}
            n_src = 0
        print(f"  [{i}/{len(echantillon)}] {nom} — {n_src} source(s)",
              flush=True)
        # Écriture à chaque fiche : la collecte dure des dizaines de
        # minutes, l'analyse doit pouvoir démarrer sur un résultat
        # partiel plutôt que d'attendre la fin.
        SORTIE.write_text(json.dumps(resultats, ensure_ascii=False,
                                     indent=1), encoding="utf-8")
        time.sleep(0.3)

    SORTIE.write_text(json.dumps(resultats, ensure_ascii=False,
                                 indent=1), encoding="utf-8")
    utiles = sum(1 for v in resultats.values()
                 if len(v.get("sources") or {}) >= 2)
    print(f"\nÉcrit dans {SORTIE} — {utiles} fiche(s) avec au moins "
          f"deux sources.")


if __name__ == "__main__":
    main()
