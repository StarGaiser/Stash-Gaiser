# -*- coding: utf-8 -*-
"""
Amorçage des tests.

Les modules du plugin importent `stashapi`, qui n'est installé que là où
Stash tourne. Les tests doivent pourtant s'exécuter n'importe où —
poste de développement, intégration continue — sans Stash ni serveur.

Un substitut minimal est donc inséré dans `sys.modules` AVANT le premier
import : il fournit `log` (journal muet) et `StashInterface` (jamais
instancié dans les tests, qui ne portent que sur la logique pure).

Ce qui est testé ici ne touche donc ni le réseau, ni la base : les
fonctions qui décident, pas celles qui écrivent.
"""

import sys
import types
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))


def _journal_muet():
    """Substitut de `stashapi.log` : accepte tout, n'affiche rien."""
    mod = types.ModuleType("stashapi.log")
    for niveau in ("trace", "debug", "info", "warning", "error",
                   "progress", "result", "exit"):
        setattr(mod, niveau, lambda *a, **k: None)
    return mod


if "stashapi" not in sys.modules:
    paquet = types.ModuleType("stashapi")
    paquet.__path__ = []
    journal = _journal_muet()

    app = types.ModuleType("stashapi.stashapp")

    class StashInterface:
        """Jamais instanciée : les tests n'appellent pas le serveur."""

        def __init__(self, *a, **k):
            raise RuntimeError(
                "les tests ne doivent pas ouvrir de connexion à Stash")

    app.StashInterface = StashInterface
    paquet.log = journal
    paquet.stashapp = app
    sys.modules["stashapi"] = paquet
    sys.modules["stashapi.log"] = journal
    sys.modules["stashapi.stashapp"] = app
