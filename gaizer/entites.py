# -*- coding: utf-8 -*-
"""Écritures communes aux entités : propositions,
créations minimales, restauration d'un passage."""

from __future__ import annotations

import json
import re
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
from noyau import tag_id
from collecte import _nettoie_studio, _resoudre


def poser_proposition(ctx, perf: dict, champ: str, valeur, source: str,
                      note: float, recommande: bool = False):
    """Tag de proposition : `Prefix:champ=valeur [sources n/10]` ;
    la recommandation de l'agent (meilleure note) porte une ★ — c'est
    elle que la validation de masse ou le mode auto retiennent."""
    prefix = ctx.tag_prefix()
    # Les URLs ne doivent JAMAIS être tronquées (une URL coupée est
    # invalide) ; les autres valeurs le sont pour garder des tags lisibles.
    limite = 200 if champ == "url" else 60
    marqueur = tag_id(ctx, ctx.tag_nom("proposal"))
    detail = tag_id(ctx, f"{prefix}:{champ}={str(valeur)[:limite]} "
                         f"[{source} {note:.1f}/10]"
                         f"{'★' if recommande else ''}")
    tags = {t["id"] for t in perf.get("tags", [])} | {marqueur, detail}
    ctx.stash.update_performer({"id": perf["id"], "tag_ids": list(tags)})
    perf.setdefault("tags", []).extend(
        [{"id": marqueur, "name": ctx.tag_nom("proposal")},
         {"id": detail, "name": f"{prefix}:x=y"}])
    log.info(f"  proposition {perf['name']}.{champ} = {str(valeur)[:44]} "
             f"[{source} {note:.1f}/10]{'★' if recommande else ''}")


def poser_proposition_scene(ctx, scene: dict, champ: str, valeur,
                            source: str, note: float,
                            recommande: bool = False):
    prefix = ctx.tag_prefix()
    limite = 200 if champ == "url" else 60
    marqueur = tag_id(ctx, ctx.tag_nom("proposal"))
    detail = tag_id(ctx, f"{prefix}:{champ}={str(valeur)[:limite]} "
                         f"[{source} {note:.1f}/10]"
                         f"{'★' if recommande else ''}")
    tags = {t["id"] for t in scene.get("tags", [])} | {marqueur, detail}
    ctx.stash.update_scene({"id": scene["id"], "tag_ids": list(tags)})
    scene.setdefault("tags", []).extend(
        [{"id": marqueur, "name": ctx.tag_nom("proposal")},
         {"id": detail, "name": f"{prefix}:x"}])
    log.info(f"  proposition scène {scene['id']}.{champ} = "
             f"{str(valeur)[:40]} [{source} {note:.1f}/10]"
             f"{'★' if recommande else ''}")


def _creer_studio(ctx, st: dict, idx_studios: dict):
    """Crée un studio inconnu, rattaché à son PARENT quand la
    stash-box le fournit (The Gay Office → Men.com). Marqué
    enrich_cree. Décision : les studios sont une taxonomie objective,
    on les crée ; réglage createMissing pour désactiver."""
    nom = _nettoie_studio(st.get("name") or "")
    if not nom:
        return None
    existant = _resoudre(nom, None, idx_studios)
    if existant:
        return existant
    parent_id = None
    par = st.get("parent")
    if par:
        pnom = _nettoie_studio(par.get("name") or "")
        parent_id = (_resoudre(pnom, par.get("stored_id"), idx_studios)
                     or _creer_studio(ctx, {"name": pnom}, idx_studios))
    try:
        inp = {"name": nom}
        if parent_id:
            inp["parent_id"] = parent_id
        d = ctx.stash.call_GQL(
            "mutation($input: StudioCreateInput!) "
            "{ studioCreate(input: $input) { id } }", {"input": inp})
        sid = str(d["studioCreate"]["id"])
    except Exception as exc:
        log.debug(f"création studio {nom} : {exc}")
        return None
    try:
        ctx.stash.call_GQL(
            "mutation($input: StudioUpdateInput!) "
            "{ studioUpdate(input: $input) { id } }",
            {"input": {"id": sid, "custom_fields": {"partial": {
                "enrich_cree": _date_auj.today().isoformat()}}}})
    except Exception as exc:
        log.debug(f"call_GQL : {exc}")
    for k in (nom.lower(), re.sub(r"[^a-z0-9]", "", nom.lower())):
        idx_studios.setdefault(k, sid)
    log.info(f"    studio créé : {nom}"
             + (f" (parent id {parent_id})" if parent_id else ""))
    return sid


# Un nom d'interprete qui n'en est pas un. Les sources renvoient des
# identifiants internes, des fragments de nom de fichier, des codes
# d'encodage — et le plugin CREE des fiches a partir de ce qu'elles
# disent.
#
# Une fiche creee a tort est pire qu'une scene incomplete : elle pollue
# le catalogue, fausse les rapprochements ulterieurs, et prive la scene
# de son vrai interprete. Personne ne la remarque avant longtemps.
_IDENTIFIANT = re.compile(r"\b\d{4,}\b")
_TECHNIQUE_NOM = re.compile(
    r"^(h\.?26[45]|x26[45]|hevc|avc|aac|ac3|dts|notag|web|dl|"
    r"\d{3,4}p|4k|uhd|hd|sd|vo|vf|multi|xvid|divx|remux|"
    r"gay|porn|scene|part|cd\d|id|user|perf)\b", re.I)


def nom_creable(nom) -> bool:
    """Ce texte peut-il etre le nom d'une personne ?

    Le controle porte sur la FORME. Il ne peut pas savoir si « Archie
    Fox » existe, mais il sait que « Do 40092 » n'est pas un nom :
    aucun patronyme ne porte un nombre a quatre chiffres.

    Il vit DANS la creation, non chez l'appelant : toute source qui cree
    doit en beneficier, et une nouvelle source ajoutee demain aussi.
    """
    texte = re.sub(r"\s+", " ", str(nom or "")).strip()
    if not (4 <= len(texte) <= 60):
        return False
    if _IDENTIFIANT.search(texte):
        return False
    if _TECHNIQUE_NOM.match(texte):
        return False
    mots = [m for m in texte.split(" ") if m]
    # Un mot isole designe trop de monde, et vient souvent d'un
    # decoupage rate. Un suffixe court est tolere : « Rocco 2 »
    # distingue deux homonymes.
    utiles = [m for m in mots if not m.isdigit()]
    if len(utiles) < 2:
        return False
    if len(mots) > 6:
        return False
    # Au moins une lettre par mot utile : « X 9 Y » n'est pas un nom.
    return all(any(c.isalpha() for c in m) for m in utiles)


def _creer_performer_minimal(ctx, nom: str, idx_perfs: dict):
    """Fiche minimale marquée `Gaizer:créé` + enrich_cree — sera
    complétée par la tâche d'enrichissement des performers."""
    if not nom_creable(nom):
        log.debug(f"nom refuse a la creation : {str(nom)[:40]!r}")
        return None
    # Un nom vide produisait une fiche sans nom, impossible à
    # retrouver autrement qu'en parcourant la collection, et que rien
    # ne viendrait jamais compléter.
    if not str(nom or "").strip():
        return None
    nom = str(nom).strip()
    try:
        d = ctx.stash.call_GQL(
            "mutation($input: PerformerCreateInput!) "
            "{ performerCreate(input: $input) { id } }",
            {"input": {"name": nom, "custom_fields": {
                "enrich_cree": _date_auj.today().isoformat()}}})
        pid = str(d["performerCreate"]["id"])
    except Exception as exc:
        log.debug(f"création performer {nom} : {exc}")
        return None
    try:
        tags_neuf = [tag_id(ctx, ctx.tag_nom("created"))]
        # Le plugin signale DE LUI-MÊME un doublon probable dès la
        # création : nom quasi identique à une fiche existante.
        cle_n = re.sub(r"[^a-z0-9]", "", nom.lower())
        jumeau = next(
            (v for k, v in idx_perfs.items()
             if v != pid and k.isalnum() and len(k) >= 6
             and (k.startswith(cle_n) or cle_n.startswith(k))
             and abs(len(k) - len(cle_n)) <= 10), None)
        maj_n = {"id": pid, "tag_ids": tags_neuf}
        if jumeau:
            tags_neuf.append(tag_id(ctx, ctx.tag_nom("duplicate")))
            maj_n["custom_fields"] = {"partial": {"enrich_rapport":
                f"doublon probable de l'id {jumeau} — vérifier, ou "
                f"poser {ctx.tag_nom('not_duplicate')} et relancer la "
                f"détection"}}
            log.info(f"    ⚠ doublon probable : {nom} ~ id {jumeau}")
        ctx.stash.update_performer(maj_n)
    except Exception as exc:
        log.debug(f"update_performer : {exc}")
    for k in (nom.strip().lower(),
              re.sub(r"[^a-z0-9]", "", nom.strip().lower())):
        idx_perfs.setdefault(k, pid)
    log.info(f"    performer créé : {nom} (fiche minimale, à enrichir)")
    return pid


def _restaurer_entite(ctx, e: dict, est_scene: bool,
                      est_studio: bool = False) -> bool:
    """Rétablit le DERNIER passage d'enrichissement : champs remis à
    leur valeur d'avant, tags / performers / urls ajoutés retirés."""
    cf = e.get("custom_fields") or {}
    try:
        hist = json.loads(cf.get("enrich_historique") or "[]")
    except Exception:
        hist = []
    if not hist:
        return False
    passage = hist.pop()
    maj = {"id": e["id"]}
    for champ, av_ap in (passage.get("champs") or {}).items():
        maj[champ] = (av_ap[0] or None)
    retirer = set(passage.get("tags_aj") or [])
    if retirer:
        maj["tag_ids"] = [t["id"] for t in e.get("tags") or []
                          if t["id"] not in retirer]
    p_ret = set(str(x) for x in passage.get("perfs_aj") or [])
    if p_ret and est_scene:
        maj["performer_ids"] = [str(q["id"]) for q in
                                e.get("performers") or []
                                if str(q["id"]) not in p_ret]
    u_ret = set(passage.get("urls_aj") or [])
    if u_ret and not est_scene:
        maj["urls"] = [u for u in e.get("urls") or [] if u not in u_ret]
    maj["custom_fields"] = {"partial": {
        "enrich_historique": json.dumps(hist, ensure_ascii=False)[:1800],
        "enrich_sources": ctx.t(
            "restaure_trace", date=_date_auj.today().isoformat(),
            passage=passage.get("d"))}}
    try:
        if est_studio:
            maj.pop("tag_ids", None)
            maj.pop("performer_ids", None)
            if "parent_id" in maj and not maj["parent_id"]:
                maj["parent_id"] = None
            ctx.stash.call_GQL(
                "mutation($input: StudioUpdateInput!) "
                "{ studioUpdate(input: $input) { id } }", {"input": maj})
        elif est_scene:
            ctx.stash.update_scene(maj)
        else:
            ctx.stash.update_performer(maj)
        return True
    except Exception as exc:
        log.warning(f"restauration {e['id']} : {exc}")
        return False
