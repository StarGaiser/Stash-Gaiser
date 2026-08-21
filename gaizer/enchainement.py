# -*- coding: utf-8 -*-
"""
Épuiser ce qu'on peut sur une fiche avant de passer à la suivante.

Le plugin propose une tâche par source : lire les chemins, interroger
les sources, lire les vignettes. Chacune parcourt toute la collection,
et l'utilisateur doit connaître l'ordre — les chemins d'abord, car un
titre et un studio donnent aux sources une prise qu'elles n'avaient
pas.

C'est une charge mentale que rien ne justifie. Une passe épuise ici ce
qu'elle peut sur une fiche : le chemin, puis les sources avec ce qu'on
vient d'apprendre, puis les sources coûteuses seulement si le manque
persiste.

**L'ordre suit le coût et la fiabilité.** Le chemin est gratuit et
exact ; les sources coûtent des appels ; la vision coûte de l'argent
et transmet des images. Commencer par le moins cher n'est pas une
optimisation, c'est ce qui évite de payer pour une information déjà
disponible.

**Une source ne s'exécute que si elle peut servir.** Interroger la
vision sur une scène dont le studio vient d'être trouvé serait payer
pour rien.

**Tout reste désactivable**, y compris l'enchaînement : qui veut
piloter chaque étape le peut encore.
"""

from __future__ import annotations

from collections import namedtuple

from stashapi import log

# Une source : son nom, ce qu'elle peut combler, ce qu'elle coûte.
Source = namedtuple("Source", "nom comble appel")

# Ce que chaque source sait chercher. Les sources peuvent tout combler ;
# les autres visent un manque précis, et les appeler pour autre chose
# serait payer sans espoir.
_COMBLE = {
    "chemin": {"studio", "title", "performers"},
    "sources": {"studio", "title", "performers", "date", "details"},
    "vision": {"studio"},
    "generiques": {"performers"},
}

# Champs dont l'absence justifie une tentative.
_ATTENDUS = ("studio", "title", "performers", "date")


def manques(sc: dict) -> set:
    """Ce qui manque encore à cette scène."""
    absents = set()
    if not (sc.get("studio") or {}).get("id"):
        absents.add("studio")
    if not str(sc.get("title") or "").strip():
        absents.add("title")
    if not sc.get("performers"):
        absents.add("performers")
    if not sc.get("date"):
        absents.add("date")
    return absents


def utile(source: str, absents: set) -> bool:
    """Cette source peut-elle combler l'un des manques ?"""
    return bool(_COMBLE.get(source, set()) & (absents or set()))


def sources_actives(ctx) -> list:
    """Les sources actives, dans l'ordre du moins cher au plus cher."""
    out = []
    if ctx.source_active("chemin"):
        out.append(Source("chemin", _COMBLE["chemin"], _appeler_chemin))
    out.append(Source("sources", _COMBLE["sources"], _appeler_sources))
    if ctx.source_active("vision"):
        out.append(Source("vision", _COMBLE["vision"], _appeler_vision))
    if ctx.source_active("generiques"):
        out.append(Source("generiques", _COMBLE["generiques"],
                        _appeler_generiques))
    return out


# ── Ce que chaque source fait sur UNE scène ────────────────────────────
def _appeler_chemin(ctx, sc):
    import chemins
    chemins.lire_chemins(ctx, scenes=[sc])


def _appeler_sources(ctx, sc):
    import scenes as mod_scenes
    mod_scenes._enrichir_scene(ctx, sc)


def _appeler_vision(ctx, sc):
    import vision
    vision.lire_vignettes(ctx, scenes=[sc])


def _appeler_generiques(ctx, sc):
    import sprites
    sprites.lire_generiques(ctx, scenes=[sc])


def _relire(ctx, sc):
    """Relit la scène après une source : la suivante doit voir ce que la
    précédente a écrit, sans quoi l'enchaînement ne sert à rien."""
    try:
        frais = ctx.stash.find_scene(sc["id"])
        return frais or sc
    except Exception:
        return sc


def _traiter(ctx, sc, etapes) -> int:
    """Passe les sources sur une scène. Rend le nombre de sources qui ont
    servi."""
    servi = 0
    for source in etapes:
        absents = manques(sc)
        if not absents:
            break
        if not utile(source.nom, absents):
            continue
        try:
            source.appel(ctx, sc)
        except Exception as exc:
            # Une passe de lot ne s'arrête pas sur une fiche.
            log.debug(f"scène {sc.get('id')} / {source.nom} : "
                      f"{str(exc)[:70]}")
            continue
        sc = _relire(ctx, sc)
        servi += 1
    return servi


# ── Tâche ────────────────────────────────────────────────────────────
def enrichir_tout(ctx):
    """Épuise les sources actives sur chaque scène incomplète."""
    etapes = sources_actives(ctx)
    log.info("Sources actives, du moins cher au plus cher : "
             + " → ".join(s.nom for s in etapes))

    cibles = [s for s in ctx.stash.find_scenes() if manques(s)]
    limite = ctx.batch()
    log.info(f"{len(cibles)} scène(s) incomplètes — lot de {limite}")

    traitees = 0
    for i, sc in enumerate(cibles[:limite], 1):
        log.progress(i / max(1, min(len(cibles), limite)))
        if _traiter(ctx, sc, etapes):
            traitees += 1

    log.info(f"{traitees} scène(s) enrichies.")
    reste = [s for s in ctx.stash.find_scenes() if manques(s)]
    if reste:
        log.info(f"  {len(reste)} scène(s) encore incomplètes : "
                 f"relancer pour le lot suivant.")
