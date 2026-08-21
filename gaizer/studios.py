# -*- coding: utf-8 -*-
"""Enrichissement des studios."""

from __future__ import annotations

import re
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
import scrapers
import sources
from noyau import _historique_maj, _perime, url_sure
from collecte import (
    _index_referentiel,
    _nettoie_studio,
    _resoudre,
    collecter_studio,
    stats_studio)
from ia import _bio_studio
from entites import _creer_studio


def _enrichir_studio(ctx, st: dict, force_auto: bool = False):
    nom = st["name"]
    raw = collecter_studio(ctx, nom)
    stats = stats_studio(ctx, st["id"])
    _, idx_studios = _index_referentiel(ctx)
    rapport = []
    maj = {"id": st["id"]}

    if not (st.get("url") or "").strip():
        urls = {s: d["website"] for s, d in raw.items()
                if d.get("website")}
        if urls:
            best = max(urls, key=lambda s:
                       sources.SOURCE_WEIGHTS.get(s, 0.4))
            maj["url"] = urls[best]
            rapport.append(f"url: {best}")

    if not st.get("parent_studio"):
        parent = next((d["parent"] for d in raw.values()
                       if d.get("parent")), None)
        if parent:
            pnom = _nettoie_studio(parent.get("name") or "")
            pid = _resoudre(pnom, parent.get("stored_id"), idx_studios)
            if not pid:
                for segment in re.split(r"\s*[|/]\s*", pnom):
                    pid = _resoudre(segment, None, idx_studios)
                    if pid:
                        break
            if not pid and ctx.settings.get("createMissing", True):
                pid = _creer_studio(ctx, {"name": pnom}, idx_studios)
            if pid and pid != str(st["id"]):
                maj["parent_id"] = pid
                rapport.append(f"parent: {pnom}")

    # Alias : essentiels au rapprochement des scènes (« Men.com » vs
    # « Men »), additifs et non destructifs.
    alias_src = []
    for d2 in raw.values():
        for a in d2.get("aliases") or []:
            if (a and a.lower() != nom.lower()
                    and a not in (st.get("aliases") or [])):
                alias_src.append(a)
    alias_src = list(dict.fromkeys(alias_src))
    if alias_src:
        maj["aliases"] = list(dict.fromkeys((st.get("aliases") or [])
                                            + alias_src))
        rapport.append(f"alias: +{len(alias_src)}")
    # Logo, si la fiche n'en a pas (champ standard image)
    if (ctx.settings.get("applyImages", True)
            and "default=true" in (st.get("image_path") or "")):
        for src2 in sorted(raw, key=lambda x:
                           -sources.SOURCE_WEIGHTS.get(x, 0.4)):
            img = raw[src2].get("image")
            if img and url_sure(img):
                maj["image"] = img
                rapport.append(f"logo: {src2}")
                break
    if not (st.get("details") or "").strip():
        r = _bio_studio(ctx, nom, raw, stats)
        if r:
            maj["details"], src_bio = r
            rapport.append(f"bio: {src_bio}")

    if stats.get("scenes"):
        resume = (f"{stats['scenes']} scène(s)"
                  + (f" {stats['periode']}" if stats.get("periode")
                     else "")
                  + (" · acteurs: " + ", ".join(stats["acteurs"][:3])
                     if stats.get("acteurs") else ""))
        rapport.append(f"collection: {resume}")

    if len(maj) <= 1 and not rapport:
        # Rien à appliquer — mais le marqueur d'acceptation doit tout
        # de même être consommé, sinon la fiche est reprise à CHAQUE
        # passage : les sources sont réinterrogées, le modèle est
        # rappelé, et rien ne change jamais. L'utilisateur voit une
        # tâche qui « applique un studio » sans effet visible, et ne
        # peut pas deviner qu'elle recommencera indéfiniment.
        if force_auto and (st.get("custom_fields") or {}).get(
                "enrich_accept"):
            ctx.stash.call_GQL(
                "mutation($input: StudioUpdateInput!) "
                "{ studioUpdate(input: $input) { id } }",
                {"input": {"id": st["id"], "custom_fields": {
                    "partial": {"enrich_accept": ""}}}})
            log.info(f"  studio {nom} : rien à appliquer, marqueur "
                     f"retiré")
        return
    stamp = _date_auj.today().isoformat()
    if force_auto or ctx.apply_mode() == "auto":
        changements = {c: ["", str(maj[c])[:60]]
                       for c in ("url", "details", "parent_id")
                       if c in maj}
        cf_maj = {"enrich_sources": (" | ".join(rapport)
                                     + f" · auto {stamp}")[:900],
                  "enrich_accept": ""}
        if changements:
            cf_maj["enrich_historique"] = _historique_maj(st,
                                                          changements)
        maj["custom_fields"] = {"partial": cf_maj}
        ctx.stash.call_GQL(
            "mutation($input: StudioUpdateInput!) "
            "{ studioUpdate(input: $input) { id } }", {"input": maj})
        log.info(f"  AUTO studio {nom} : " + "; ".join(rapport)[:100])
    else:
        # Les studios Stash n'ont pas de tags : la fiche de décision
        # porte tout, et le bouton « Accepter » de l'interface pose le
        # custom_field enrich_accept que la tâche dédiée consomme.
        ctx.stash.call_GQL(
            "mutation($input: StudioUpdateInput!) "
            "{ studioUpdate(input: $input) { id } }",
            {"input": {"id": st["id"], "custom_fields": {"partial": {
                "enrich_rapport": ((" | ".join(rapport)
                                    or "—")
                                   + ctx.t("accepter_studio"))[:900]}}}})
        log.info(f"  studio {nom} : fiche posée "
                 f"({len(rapport)} élément(s))")


def enrich_studios(ctx, limit: int = 25):
    limit = int(ctx.args.get("limit", 0)) or ctx.batch()
    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name details url aliases custom_fields image_path
             parent_studio { id name } } } }""")
    tous = d["findStudios"]["studios"]
    cibles = [s for s in tous
              if not (s.get("details") or "").strip()
              or not (s.get("url") or "").strip()
              or not s.get("parent_studio")
              or "default=true" in (s.get("image_path") or "")
              or _perime(ctx, s)]
    log.info(f"{len(cibles)} studio(s) incomplet(s) sur {len(tous)}")
    for i, s in enumerate(cibles[:limit], 1):
        _enrichir_studio(ctx, s)
        log.progress(i / max(1, min(len(cibles), limit)))
    log.info("Terminé (studios).")

    # La liste des studios n'est complète qu'ICI : cette tâche
    # vient de créer ceux qui manquaient. C'est donc le seul moment
    # où la détection a une chance d'être juste.
    # Cette détection est un SUPPLÉMENT : elle ne doit en aucun cas
    # faire échouer un enrichissement qui, lui, a réussi. Se reposer
    # sur le fait que `detecter` capture ses propres erreurs serait
    # une hypothèse, pas une garantie.
    try:
        manquants = (scrapers.detecter(ctx)
                     if scrapers.doit_verifier(ctx) else [])
        if manquants:
            scrapers.marquer_verifie(ctx)
            log.info(f"{len(manquants)} scraper(s) du catalogue "
                     f"correspondent à vos studios sans être "
                     f"installés — tâche « Proposer les scrapers "
                     f"manquants » pour la liste.")
        else:
            scrapers.marquer_verifie(ctx)
    except Exception as exc:
        log.debug(f"détection des scrapers : {exc}")


def enrich_one_studio(ctx):
    """Enrichit UN studio (args studio_id) — bouton de l'interface."""
    sid = str(ctx.args.get("studio_id") or "")
    if not sid:
        return
    d = ctx.stash.call_GQL(
        """query($id: ID!) { findStudio(id: $id) {
             id name details url aliases custom_fields image_path
             parent_studio { id name } } }""", {"id": sid})
    st = d.get("findStudio")
    if st:
        _enrichir_studio(ctx, st)


def apply_accepted_studios(ctx):
    """Applique les studios dont la fiche porte le custom_field
    `enrich_accept` (posé par le bouton « Accepter » de l'interface) —
    mêmes règles que le mode auto. Comble le cul-de-sac du mode manuel
    pour les studios, qui n'ont pas de tags dans Stash."""
    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name details url aliases custom_fields image_path
             parent_studio { id name } } } }""")
    n = 0
    for st in d["findStudios"]["studios"]:
        if not str((st.get("custom_fields") or {}).get("enrich_accept")
                   or "").strip():
            continue
        _enrichir_studio(ctx, st, force_auto=True)
        n += 1
    log.info(f"{n} studio(s) appliqué(s).")
