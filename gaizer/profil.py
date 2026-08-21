# -*- coding: utf-8 -*-
"""
Deviner le profil d'une collection plutôt que le demander.

Stash ne porte AUCUNE orientation sur les fiches d'interprète : le
champ n'existe pas. Mais l'orientation d'une collection ne se lit pas
sur une personne — elle se lit sur ce qui se passe dans les scènes.
Une scène jouée par deux hommes est une scène gay, quelle que soit
l'orientation déclarée de qui la joue.

**Ce qui rend la déduction praticable.** Le genre figure sur la fiche
d'interprète, et une scène nomme les siens : la composition suffit.

**Ce qui la rend fragile.** Sur une collection réelle, six cent trente
et une scènes sur sept cent cinquante-cinq ont des interprètes sans
genre renseigné — parce que personne ne remplit ce champ à la main.
La déduction refuse donc de répondre quand la matière manque : un
profil deviné à tort produit un prompt faux sur TOUTE la collection,
ce qui est pire que pas de profil du tout.

**Elle propose, elle n'impose pas.** Le réglage explicite prime
toujours, et rien n'est écrit à la place de l'utilisateur : le sujet
le regarde.
"""

from __future__ import annotations

from collections import Counter

from stashapi import log

# En deçà, une collection n'est pas caractérisée : trois scènes ne
# disent rien, et répondre sur si peu produirait un profil faux qu'on
# croirait établi.
MINIMUM = 8

# Part qu'une forme doit atteindre pour donner son nom à l'ensemble.
# Une collection gay contient presque toujours quelques scènes
# hétéro ; l'inverse est vrai aussi.
DOMINANCE = 0.7

_MASCULIN = {"MALE"}
_FEMININ = {"FEMALE"}
_TRANS = {"TRANSGENDER_MALE", "TRANSGENDER_FEMALE", "NON_BINARY",
          "INTERSEX"}


def forme_scene(genres):
    """Ce que la composition d'une scène dit de son orientation.

    Rend « gay », « lesbien », « hetero », « trans », ou None quand
    la scène ne dit rien — ce qui est le cas d'un solo, et de toute
    scène dont un interprète n'a pas de genre renseigné. Deviner sur
    une composition partielle serait pire que se taire.
    """
    valeurs = [str(g).strip().upper() if g else "" for g in genres or []]
    if len(valeurs) < 2:
        return None                  # solo : ne caractérise rien
    if any(not v for v in valeurs):
        return None                  # un genre manque
    if any(v in _TRANS for v in valeurs):
        return "trans"
    if all(v in _MASCULIN for v in valeurs):
        return "gay"
    if all(v in _FEMININ for v in valeurs):
        return "lesbien"
    if (any(v in _MASCULIN for v in valeurs)
            and any(v in _FEMININ for v in valeurs)):
        return "hetero"
    return None


def deviner(ctx):
    """Le profil que la collection suggère, ou None.

    Fondé sur ce qui DOMINE, non sur ce qui existe : une collection
    gay contenant trois scènes hétéro reste gay.
    """
    try:
        scenes = ctx.stash.find_scenes()
    except Exception as exc:
        log.debug(f"collection illisible : {str(exc)[:70]}")
        return None

    formes = Counter()
    for sc in scenes:
        f = forme_scene([(p or {}).get("gender")
                         for p in sc.get("performers") or []])
        if f:
            formes[f] += 1

    total = sum(formes.values())
    if total < MINIMUM:
        return None

    dominante, compte = formes.most_common(1)[0]
    if compte / total >= DOMINANCE:
        return dominante
    # Aucune forme ne domine : la collection est bel et bien mixte,
    # et le dire vaut mieux que de choisir la moins minoritaire.
    return "mixte"


def profil_courant(ctx):
    """Le profil à employer : celui qui est réglé, sinon celui que la
    collection suggère.

    Ce que l'utilisateur a choisi ne se discute pas — la déduction
    n'intervient que sur son silence.
    """
    regle = str(ctx.settings.get("tagProfile") or "").strip().lower()
    if regle:
        return regle
    return deviner(ctx)


def rapport_profil(ctx):
    """Ce que la composition des scènes dit de la collection.

    N'écrit rien. Sert à voir ce que le rédacteur emploiera, et à
    décider s'il faut fixer le réglage plutôt que de laisser deviner.
    """
    try:
        scenes = ctx.stash.find_scenes()
    except Exception as exc:
        log.warning(f"collection illisible : {str(exc)[:70]}")
        return

    formes = Counter()
    muettes = solos = 0
    for sc in scenes:
        genres = [(p or {}).get("gender")
                  for p in sc.get("performers") or []]
        f = forme_scene(genres)
        if f:
            formes[f] += 1
        elif len(genres) < 2:
            solos += 1
        else:
            muettes += 1

    total = sum(formes.values())
    log.info(f"{len(scenes)} scène(s) — {total} caractérisée(s)")
    for forme, n in formes.most_common():
        log.info(f"  {forme} : {n} ({100 * n / max(1, total):.0f} %)")
    if muettes:
        log.info(f"  {muettes} scène(s) muettes : un interprète au "
                 f"moins n'a pas de genre renseigné")
    if solos:
        log.info(f"  {solos} scène(s) à un interprète ou moins : "
                 f"elles ne caractérisent rien")

    regle = str(ctx.settings.get("tagProfile") or "").strip().lower()
    devine = deviner(ctx)
    if regle:
        log.info(f"Profil RÉGLÉ : « {regle} » — il prime sur la "
                 f"déduction.")
        if devine and devine != regle:
            log.info(f"  (la collection suggérerait « {devine} »)")
    elif devine:
        log.info(f"Profil DEVINÉ : « {devine} ». Le fixer dans les "
                 f"réglages évite qu'il change avec la collection.")
    else:
        log.info("Aucun profil : trop peu de scènes caractérisées. "
                 "Le rédacteur ne supposera aucune orientation, ce "
                 "qui est le comportement prudent.")
