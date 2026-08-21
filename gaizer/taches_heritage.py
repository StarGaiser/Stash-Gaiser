# -*- coding: utf-8 -*-
"""
Champs venus d'ailleurs.

Une médiathèque reprise d'un autre outil traîne des champs
qui font double emploi avec ceux de Stash, ou ne renvoient
plus à rien. Le point délicat est la PROVENANCE : une valeur
importée s'affiche exactement comme une valeur établie par
plusieurs sources, et rien ne les distingue.
"""

from __future__ import annotations
import re
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stashapi import log
import roles


# Champs natifs qu'un import a pu remplir sans qu'aucune source ne
# l'appuie, et le mot à chercher dans enrich_sources pour savoir si
# une source l'a effectivement confirmé.
CHAMPS_A_APPUYER = {
    "penis_length": "penis",
    "weight": "weight",
    "height_cm": "height_cm",
}


def _cm(valeur):
    """Nombre de centimètres d'une écriture libre (« 185cm », « 20.0 »).

    Le signe est retenu dans la recherche : sans lui, « -5 » donnait 5,
    valeur absurde mais dans la plage acceptée, donc écrite sans que
    rien ne le signale."""
    m = re.search(r"(-?\d+(?:[.,]\d+)?)", str(valeur or ""))
    if not m:
        return None
    try:
        n = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    return round(n) if 1 <= n <= 260 else None


def _kg(valeur):
    m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*kg", str(valeur or ""), re.I)
    if not m:
        return None
    try:
        n = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    return round(n) if 20 <= n <= 300 else None


def ranger_champs_herites(ctx):
    """Verse dans les champs natifs de Stash ce qu'un import avait mis
    dans des champs personnalisés, puis retire ce qui ne sert plus.

    Un import laisse ses propres colonnes : elles font double emploi
    avec des champs que Stash possède déjà — « sexe_cm » double
    `penis_length`, « mensurations » double `height_cm` et `weight` —
    et d'autres ne renvoient plus à rien, comme la clé d'un outil
    abandonné. Elles encombrent la fiche et, plus gênant, elles
    peuvent contredire les valeurs établies sans que rien ne le
    signale.

    Rien n'est écrasé : un champ natif déjà renseigné est laissé tel
    quel, et le champ hérité n'est retiré qu'une fois sa valeur
    récupérée — ou s'il ne portait rien d'utile."""
    perfs = ctx.stash.find_performers()
    n_penis = n_taille = n_poids = 0
    retires = {}
    conserves = {}

    for p in perfs:
        cf = p.get("custom_fields") or {}
        if not cf:
            continue
        maj_natifs = {}
        a_retirer = []

        # sexe_cm → penis_length
        brut = cf.get("sexe_cm")
        if str(brut or "").strip():
            n = _cm(brut)
            if n and not p.get("penis_length"):
                maj_natifs["penis_length"] = n
                n_penis += 1
            if n or not str(brut).strip():
                a_retirer.append("sexe_cm")

        # mensurations « 185cm / 88kg » → height_cm + weight
        brut = cf.get("mensurations")
        if str(brut or "").strip():
            taille = _cm(brut)
            poids = _kg(brut)
            if taille and not p.get("height_cm"):
                maj_natifs["height_cm"] = taille
                n_taille += 1
            if poids and not p.get("weight"):
                maj_natifs["weight"] = poids
                n_poids += 1
            if taille or poids:
                a_retirer.append("mensurations")

        # Champs sans équivalent et sans usage.
        for mort in ("mediapr0n_key", "alt_image"):
            if mort in cf:
                a_retirer.append(mort)

        # Rôles déjà versés sur les deux axes.
        for ancien, neuf in (("position", "enrich_position"),
                             ("pouvoir", "enrich_pouvoir")):
            if cf.get(ancien) and cf.get(neuf):
                a_retirer.append(ancien)
            elif cf.get(ancien):
                conserves[ancien] = conserves.get(ancien, 0) + 1

        # « sexe_type » n'est PAS retiré ici : 50 fiches le voient
        # contredire les sources, et cet arbitrage revient à
        # l'utilisateur (tâche « Contrôler les champs hérités »).
        if cf.get("sexe_type"):
            conserves["sexe_type"] = conserves.get("sexe_type", 0) + 1

        if not maj_natifs and not a_retirer:
            continue
        entree = {"id": p["id"]}
        entree.update(maj_natifs)
        if a_retirer:
            # « partial » ne SAIT PAS supprimer : ni None ni la chaîne
            # vide n'effacent la clé. L'API expose « remove », qui
            # prend la liste des clés à retirer — encore fallait-il
            # regarder le schéma plutôt que supposer.
            entree["custom_fields"] = {"remove": sorted(set(a_retirer))}
            for c in a_retirer:
                retires[c] = retires.get(c, 0) + 1
        try:
            ctx.stash.update_performer(entree)
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")

    log.info(f"Récupéré dans les champs natifs de Stash : "
             f"{n_penis} longueur(s), {n_taille} taille(s), "
             f"{n_poids} poids.")
    if retires:
        log.info("Champs hérités retirés : "
                 + " · ".join(f"{c} ({n})"
                              for c, n in sorted(retires.items(),
                                                 key=lambda x: -x[1])))
    if conserves:
        log.info("Conservés faute d'arbitrage : "
                 + " · ".join(f"{c} ({n})"
                              for c, n in sorted(conserves.items())))
        log.info("  « sexe_type » peut contredire les sources : tâche "
                 "« Contrôler les champs hérités » pour la liste.")
    if ctx.simulation():
        log.info("SIMULATION : rien n'a été écrit.")


def retirer_non_confirme(ctx):
    """Vide les champs natifs qu'aucune source n'appuie.

    Une valeur venue d'un import s'affiche dans Stash exactement comme
    une valeur établie par plusieurs sources concordantes : rien ne les
    distingue. Quand l'import provient d'une recherche automatisée non
    vérifiée, cela revient à présenter une supposition comme un fait —
    et à la rendre indétectable.

    Le critère est la trace : un champ est conservé si `enrich_sources`
    OU l'historique montre qu'une source l'a fourni, retiré sinon.

    LIMITE CONNUE, mesurée à l'usage : `enrich_sources` ne décrit que
    le DERNIER passage. Un champ rempli lors d'un passage antérieur, ou
    saisi à la main hors du plugin, n'y laisse aucune trace et sera
    retiré à tort. L'historique rattrape le premier cas mais pas le
    second — une valeur saisie manuellement est indiscernable d'une
    valeur importée. Sur cette collection, 227 tailles ont été retirées
    dont 6 seulement figuraient dans l'historique. Ce qui est retiré
    n'est pas forcément faux ; il est seulement invérifiable, et le
    prochain enrichissement le rétablira s'il est vrai — cette fois
    avec sa provenance.

    Argument `champs` pour restreindre (ex. « penis_length,weight »).
    """
    voulus = [c.strip() for c in
              str(ctx.args.get("champs") or "").split(",") if c.strip()]
    cibles = {c: m for c, m in CHAMPS_A_APPUYER.items()
              if not voulus or c in voulus}
    if not cibles:
        log.warning("aucun champ reconnu dans l'argument « champs ».")
        return

    perfs = ctx.stash.find_performers()
    retires = dict.fromkeys(cibles, 0)
    gardes = dict.fromkeys(cibles, 0)
    for p in perfs:
        cf = p.get("custom_fields") or {}
        src = str(cf.get("enrich_sources") or "")
        maj = {}
        for champ, mot in cibles.items():
            if not p.get(champ):
                continue
            # L'historique conserve dix passages : il rattrape les
            # champs remplis avant le dernier, invisibles dans
            # enrich_sources.
            dans_hist = False
            try:
                for passage in json.loads(
                        cf.get("enrich_historique") or "[]"):
                    if champ in (passage.get("champs") or {}):
                        dans_hist = True
                        break
            except (ValueError, TypeError) as exc:
                log.debug(f"champ hérité illisible : {str(exc)[:70]}")
            if mot in src or dans_hist:
                gardes[champ] += 1
            else:
                maj[champ] = None
                retires[champ] += 1
        if not maj:
            continue
        try:
            ctx.stash.update_performer(dict(maj, id=p["id"]))
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")

    for champ in cibles:
        log.info(f"  {champ:14s} {gardes[champ]:4d} appuyé(s) par une "
                 f"source · {retires[champ]:4d} retiré(s)")
    if ctx.simulation():
        log.info("SIMULATION : rien n'a été écrit.")
    else:
        log.info("Relancer « Enrichir les performers incomplets » "
                 "rétablira ce que les sources savent, avec sa "
                 "provenance cette fois.")


def retirer_champ_herite(ctx):
    """Supprime un champ personnalisé hérité sur toute la collection.

    Argument `champ` obligatoire. Destiné aux champs d'import dont on
    a établi qu'ils ne valaient rien — non par principe, mais parce
    qu'on connaît leur provenance."""
    champ = str(ctx.args.get("champ") or "").strip()
    if not champ:
        log.error("argument « champ » manquant : rien à supprimer.")
        return
    if champ.startswith("enrich_") or champ in ("bio_hot", "reco_data"):
        log.error(f"« {champ} » est produit par le plugin : utiliser "
                  f"« Nettoyer les propositions » ou la restauration.")
        return
    perfs = ctx.stash.find_performers()
    n = 0
    for p in perfs:
        if champ not in (p.get("custom_fields") or {}):
            continue
        try:
            ctx.stash.update_performer({
                "id": p["id"],
                "custom_fields": {"remove": [champ]}})
            n += 1
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")
    if ctx.simulation():
        log.info(f"SIMULATION : « {champ} » aurait été retiré de {n} "
                 f"fiche(s).")
    else:
        log.info(f"« {champ} » retiré de {n} fiche(s).")


def marquer_roles_importes(ctx):
    """Signale comme non confirmés les rôles venus d'un import.

    Une position issue d'un import s'affiche exactement comme une
    position saisie ou lue dans une source : rien ne la distingue. Quand
    l'import provient d'une recherche automatisée, cela revient à
    présenter une supposition comme un fait — le même travers que les
    valeurs promues dans les champs natifs.

    La marque ne change ni la valeur ni son usage : elle rend visible
    ce qu'on ne sait pas. La modifier depuis le panneau vaut
    confirmation et fait disparaître la marque."""
    motif = str(ctx.args.get("motif") or "").strip() or (
        "valeur reprise d'un import, non confirmée par une source")
    perfs = ctx.stash.find_performers()
    n = deja = 0
    for p in perfs:
        cf = p.get("custom_fields") or {}
        if not (cf.get("enrich_position") or cf.get("enrich_pouvoir")):
            continue
        origine = str(cf.get("enrich_role_origine") or "").strip()
        if origine:
            deja += 1
            continue
        try:
            ctx.stash.update_performer({
                "id": p["id"],
                "custom_fields": {"partial": {
                    "enrich_role_origine": "import",
                    "enrich_role_motif": motif[:200]}}})
            n += 1
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")
    if ctx.simulation():
        log.info(f"SIMULATION : {n} rôle(s) auraient été marqués.")
    else:
        log.info(f"{n} rôle(s) marqués « suggéré » · {deja} portaient "
                 f"déjà une origine.")
    log.info("Le panneau les signale par une pastille ; les modifier "
             "vaut confirmation.")


def normaliser_roles(ctx):
    """Range les positions en texte libre sur deux axes distincts.

    Les valeurs héritées mélangeaient position et rapport de pouvoir
    — « Actif Dominant », « Versatile (Dominante Active) » — ce qui
    rendait tout filtrage impossible. Elles sont relues et réparties
    entre `enrich_position` (actif / passif / versatile) et
    `enrich_pouvoir` (dominant / soumis / permutant).

    Ce qui n'est pas compris est CONSERVÉ tel quel dans
    `enrich_role_libre` : « Réalisatrice / Icone » n'est pas une
    position, et la ranger de force serait pire que de la laisser."""
    perfs = ctx.stash.find_performers()
    n_pos = n_pouv = n_reste = 0
    inconnus = []
    for p in perfs:
        cf = p.get("custom_fields") or {}
        brut = (cf.get("position") or cf.get("enrich_position_libre")
                or "")
        if not str(brut).strip():
            continue
        if cf.get("enrich_position") or cf.get("enrich_pouvoir"):
            continue                      # déjà normalisé
        lu = roles.normaliser(brut)
        if not lu:
            continue
        maj = {}
        if lu.get("position"):
            maj["enrich_position"] = lu["position"]
            n_pos += 1
        if lu.get("pouvoir"):
            maj["enrich_pouvoir"] = lu["pouvoir"]
            n_pouv += 1
        if lu.get("reste"):
            maj["enrich_role_libre"] = lu["reste"]
            n_reste += 1
            inconnus.append(f"{p['name']} : « {lu['reste']} »")
        try:
            ctx.stash.update_performer({
                "id": p["id"], "custom_fields": {"partial": maj}})
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")
    log.info(f"{n_pos} position(s) et {n_pouv} rapport(s) de pouvoir "
             f"rangés sur les deux axes.")
    if inconnus:
        log.info(f"{n_reste} valeur(s) non reconnues, conservées telles "
                 f"quelles :")
        for x in inconnus[:15]:
            log.info(f"  {x}")
    sans = sum(1 for p in perfs
               if not (p.get("custom_fields") or {}).get(
                   "enrich_position"))
    log.info(f"{sans} fiche(s) sans position. Aucune source n'en "
             f"fournit : elle se renseigne à la main, depuis le "
             f"panneau de la fiche.")


