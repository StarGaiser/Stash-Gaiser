# -*- coding: utf-8 -*-
"""
Ménage : retirer ce qui encombre.

Tags de proposition consommés, pieds de biographie devenus
redondants, étiquettes écartées. Rien d'irremplaçable, mais
toutes ces tâches ÉCRIVENT : elles passent par la simulation.
"""

from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stashapi import log
import i18n
import tags as mod_tags
from noyau import _sans_footer
from noyau import (
    _tag_exclu)


def purger_tags_exclus(ctx):
    """Détache des scènes les tags visés par le réglage `tagsExclude`.

    Le réglage empêche d'en poser de nouveaux ; cette tâche s'occupe de
    ceux déjà en place. Les tags eux-mêmes ne sont PAS supprimés de
    Stash : seul le lien avec les scènes est retiré, ce qui reste
    réparable à la main. Passer en mode simulation pour voir la liste
    sans rien changer."""
    exclus = ctx.tags_exclus()
    if not exclus:
        log.info("aucun motif dans tagsExclude — rien à faire.")
        return
    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             id tags { id name } } } }""")
    scenes = d["findScenes"]["scenes"]
    vises = {}
    for sc in scenes:
        for t in sc.get("tags") or []:
            if (not t["name"].startswith(f"{ctx.tag_prefix()}:")
                    and _tag_exclu(t["name"], exclus)):
                vises.setdefault(t["name"], []).append(sc["id"])
    if not vises:
        log.info("aucun tag posé ne correspond aux motifs.")
        return
    log.info(f"{len(vises)} tag(s) visé(s) par « "
             f"{ctx.settings.get('tagsExclude')} » :")
    for nom in sorted(vises, key=lambda n: -len(vises[n])):
        log.info(f"  {nom} — {len(vises[nom])} scène(s)")
    ids_vises = {t["id"] for sc in scenes for t in sc.get("tags") or []
                 if not t["name"].startswith(f"{ctx.tag_prefix()}:")
                 and _tag_exclu(t["name"], exclus)}
    n = 0
    for sc in scenes:
        actuels = {t["id"] for t in sc.get("tags") or []}
        restants = actuels - ids_vises
        if restants == actuels:
            continue
        ctx.stash.update_scene({"id": sc["id"],
                                "tag_ids": list(restants)})
        n += 1
    if ctx.simulation():
        log.info(f"SIMULATION : {n} scène(s) auraient été allégées.")
    else:
        log.info(f"{n} scène(s) allégées. Les tags subsistent dans "
                 f"Stash sans être rattachés — les supprimer "
                 f"définitivement se fait depuis la page des tags.")


def clear_proposals(ctx):
    """Retire les PROPOSITIONS (marqueur + tags-valeurs). Les tags de
    traçabilité (:créé, :verifier) et :accept sont CONSERVÉS."""
    prefix = ctx.tag_prefix()
    cles_protegees = ("created", "verify", "accept", "restore",
                      "unidentified", "duplicate", "not_duplicate",
                      "merge")
    proteges = {ctx.tag_nom(c) for c in cles_protegees}
    # Les variantes des AUTRES langues sont protégées elles aussi :
    # changer de langue ne doit pas rendre supprimables les tags posés
    # auparavant.
    for c in cles_protegees:
        proteges |= {f"{prefix}:{v}" for v in i18n.tous_les_tags(c)}
    n = 0
    for t in ctx.stash.find_tags(f={"name": {
            "value": f"^{prefix}:", "modifier": "MATCHES_REGEX"}}):
        nom = t["name"]
        if (not nom.startswith(f"{prefix}:") or nom in proteges):
            continue
        if nom == ctx.tag_nom("proposal") or "=" in nom:
            ctx.stash.destroy_tag(t["id"])
            n += 1
    log.info(f"{n} tag(s) de proposition retiré(s) "
             f"(:créé, :verifier et :accept conservés).")


def retirer_pied_bio(ctx):
    """Retire des biographies le pied « Fiabilité des données ».

    Ce pied recopiait dans la biographie la liste des valeurs, leurs
    notes et leurs sources. Il avait un sens quand cette information
    n'était visible nulle part ailleurs ; le panneau de la fiche la
    présente désormais en tableau trié et repliable, ce qui rend le
    pied redondant — et il occupe la biographie, qui devrait contenir
    la biographie.

    Les pieds portant l'ancien nom du plugin sont reconnus au même
    titre. Seul le pied est retiré : le texte qui le précède est
    conservé intact."""
    perfs = ctx.stash.find_performers()
    n = 0
    for p in perfs:
        details = p.get("details") or ""
        if not details.strip():
            continue
        propre = _sans_footer(details)
        if propre == details.rstrip():
            continue
        try:
            ctx.stash.update_performer({"id": p["id"],
                                        "details": propre})
            n += 1
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")
    if ctx.simulation():
        log.info(f"SIMULATION : {n} biographie(s) auraient été "
                 f"allégées.")
    else:
        log.info(f"{n} biographie(s) allégées. Décocher le réglage "
                 f"« Pied de bio » pour qu'il ne soit pas réécrit au "
                 f"prochain passage.")


def suggerer_tags_exclus(ctx):
    """Propose des tags à écarter, en s'appuyant d'abord sur les
    chiffres de VOTRE collection.

    Une liste d'exclusion écrite pour une médiathèque est absurde pour
    une autre : « Gay » n'apprend rien là où tout l'est, et constitue
    l'information la plus discriminante ailleurs. La question posée
    n'est donc pas « ce tag est-il mauvais » mais « ce tag sépare-t-il
    quelque chose ICI ».

    Aucune écriture : la liste proposée est à recopier — après examen —
    dans le réglage « Tags à ne jamais appliquer »."""
    from collections import Counter
    table = mod_tags.charger(str(Path(__file__).resolve().parent))
    profil = str(ctx.settings.get("tagProfile") or "").strip().lower()
    if profil and profil not in (table.get("profils") or {}):
        log.warning(f"profil « {profil} » inconnu — disponibles : "
                    + ", ".join(n for n, _d
                                in mod_tags.profils_connus(table)))
        profil = ""

    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             tags { id name } } } }""")
    scenes = d["findScenes"]["scenes"]
    freq = Counter()
    for sc in scenes:
        for t in sc.get("tags") or []:
            if not t["name"].startswith(f"{ctx.tag_prefix()}:"):
                freq[t["name"]] += 1
    if not freq:
        log.info("aucun tag à examiner.")
        return

    log.info(f"═══ {len(freq)} tags distincts sur {len(scenes)} "
             f"scènes ═══")
    if profil:
        conf = table["profils"][profil]
        log.info(f"  profil déclaré : {profil} — "
                 f"{conf.get('description')}")
    else:
        log.info("  aucun profil déclaré : seuls les chiffres de la "
                 "collection sont utilisés (réglage « Profil de "
                 "collection » pour en choisir un).")

    par_famille = mod_tags.repartition(freq, table)
    log.info("═══ Répartition par famille ═══")
    for fam in sorted(par_famille, key=lambda f: -len(par_famille[f])):
        noms = par_famille[fam]
        etiquette = fam or "(non classés)"
        exemples = ", ".join(sorted(noms, key=lambda n: -freq[n])[:5])
        log.info(f"  {etiquette:14s} {len(noms):4d} tag(s) — "
                 f"{exemples}")

    sug = mod_tags.suggestions(freq, len(scenes), table, profil)

    log.info("═══ Suggestions ═══")
    if sug["omnipresent"]:
        log.info(f"  ── {len(sug['omnipresent'])} tag(s) presents sur "
                 f"presque toutes les scènes : ils ne séparent plus "
                 f"rien ──")
        for nom, n, fam in sug["omnipresent"][:15]:
            part = 100 * n / max(1, len(scenes))
            log.info(f"     {nom} — {n} scènes ({part:.0f} %)"
                     + (f" · {fam}" if fam else ""))
    if sug["dominant"]:
        log.info(f"  ── {len(sug['dominant'])} tag(s) qui absorbent "
                 f"presque toute leur famille : ils décrivent une "
                 f"constante de la collection, pas une distinction ──")
        for nom, n, fam in sug["dominant"][:15]:
            log.info(f"     {nom} — {n} scènes, l'essentiel de la "
                     f"famille « {fam} »")
    if sug["famille"]:
        log.info(f"  ── {len(sug['famille'])} tag(s) techniques "
                 f"(format, édition) : sans rapport avec ce qui est "
                 f"filmé ──")
        for nom, n, fam in sug["famille"][:20]:
            log.info(f"     {nom} — {n} scènes · {fam}")
    if sug["rare"]:
        noms = ", ".join(f"{n} ({c})" for n, c, _f in sug["rare"][:30])
        log.info(f"  ── {len(sug['rare'])} tag(s) sur une ou deux "
                 f"scènes : ils ne regroupent rien ──")
        log.info(f"     {noms}")

    retenus = [n for cle in ("omnipresent", "dominant", "famille")
               for n, _c, _f in sug[cle]]
    if retenus:
        log.info("═══ À recopier dans « Tags à ne jamais appliquer » "
                 "après examen ═══")
        log.info("  " + ", ".join(sorted(retenus)))
        log.info("  Puis la tâche « Retirer les tags exclus » détache "
                 "ceux déjà posés (essayer en simulation d'abord).")
    else:
        log.info("  Rien à proposer : la taxonomie paraît saine.")

    protegees = set((table["profils"].get(profil) or {}).get("jamais")
                    or [])
    if protegees:
        log.info(f"  Familles écartées de toute suggestion pour ce "
                 f"profil : {', '.join(sorted(protegees))} — leur "
                 f"omniprésence peut caractériser la collection plutôt "
                 f"que la parasiter.")
