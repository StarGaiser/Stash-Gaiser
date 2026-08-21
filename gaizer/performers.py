# -*- coding: utf-8 -*-
"""Enrichissement des interprètes."""

from __future__ import annotations

import json
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
import sources
import scoring
from noyau import (
    MAP,
    PERFORMER_FIELDS,
    _historique_maj,
    _ligne_fiche,
    _sans_footer,
    footer_mark,
    tag_id,
    url_sure)
from collecte import _url_normale, collecter_stash, passe_url, table_motifs
from ia import deduire_role, generer_bio_hot, synth_bio
from entites import poser_proposition


def _enrichir_un(ctx, p: dict):
    nom = p["name"]
    deja = set(p.get("urls") or [])
    raw, urls = collecter_stash(ctx, nom)
    urls.extend(deja)                    # fiches déjà sur le performer
    passe_url(ctx, raw, urls)            # débloque les scrapers par-URL
    if ctx.use_appoint():
        for src in ("wikipedia", "ade"):
            fetcher = sources.ACTOR_SOURCES.get(src)
            if not fetcher:
                continue
            try:
                d = fetcher(nom)
            except Exception:
                d = None
            if d:
                raw[src] = d
    if not raw:
        log.info(f"  aucune source pour {nom}")
        return
    # URLs de fiches découvertes, couvertes par un scraper installé et
    # absentes du performer.
    motifs = table_motifs(ctx)
    urls_valides = [u for u in dict.fromkeys(urls) if u not in deja
                    and any(m in _url_normale(u)
                            for ms in motifs.values() for m in ms)]
    actuel = {
        "bio": p.get("details"),
        "birthdate": p.get("birthdate"),
        "height_cm": str(p["height_cm"]) if p.get("height_cm") else None,
        "country": p.get("country"),
        "ethnicity": p.get("ethnicity"),
        "years_active": p.get("career_length"),
        "measurements": p.get("measurements"),
        "circumcised": p.get("circumcised"),
    }
    champs = {"birthdate", "height_cm", "country", "ethnicity",
              "years_active", "measurements", "circumcised"}
    cands = scoring.evaluer_tous(raw, actuel, champs, ctx.cfg)

    if ctx.apply_mode() == "auto":
        appliquer_auto(ctx, p, cands, urls_valides, raw, actuel)
        generer_bio_hot(ctx, p, raw)
        return

    for url in urls_valides:
        poser_proposition(ctx, p, "url", url, "stash-box", 8.5, True)
    fiche = []
    for champ, liste in cands.items():
        for c in liste:
            poser_proposition(ctx, p, champ, c["valeur"],
                              "+".join(c["sources"]), c["note"],
                              c["recommande"])
        fiche.append(_ligne_fiche(champ, liste))
    if not (p.get("details") or "").strip():
        srcs_bio = sorted(s2 for s2, d2 in raw.items()
                          if d2.get("bio"))
        if srcs_bio:
            # Tag INFORMATIF (une bio tronquée à 60 car. serait
            # inutilisable) : la bio est régénérée à l'application.
            poser_proposition(ctx, p, "bio",
                              f"disponible ({len(srcs_bio)} source(s))",
                              "+".join(srcs_bio), 7.5, True)
    if fiche:
        # Fiche de décision complète, visible dans les Custom Fields
        ctx.stash.update_performer({
            "id": p["id"],
            "custom_fields": {"partial": {
                "enrich_rapport": " | ".join(fiche)[:900]}}})
    if ctx.apply_mode() == "seuil":
        # En mode manual, RIEN ne s'écrit sans validation — bio hot
        # comprise. Elle est réservée aux modes seuil et auto.
        generer_bio_hot(ctx, p, raw)

    # Le role ne figure dans aucun champ de source : la seule piste
    # est qu'un texte le DISE. La deduction lit donc la documentation
    # qu'on VIENT de collecter, quand elle est encore en memoire.
    #
    # La proposer en tache separee n'avait pas de sens : elle
    # obligeait a enrichir, puis a comprendre qu'il fallait relancer
    # autre chose sur les memes fiches.
    if ctx.settings.get("deduireRoles"):
        try:
            _deduire_role_ici(ctx, p, raw)
        except Exception as exc:
            log.debug(f"rôle {p.get('name')} : {str(exc)[:70]}")


def _deduire_role_ici(ctx, p: dict, raw: dict):
    """Lit la documentation collectee pour y trouver une mention
    EXPLICITE du role.

    Le modele doit CITER le passage, et cette citation est verifiee
    presente dans le texte fourni : c'est le seul garde-fou possible
    contre une citation fabriquee. Sans citation verifiable, rien
    n'est ecrit — il s'agit d'une personne reelle, et une supposition
    serait une erreur, pas une approximation.
    """
    cf = p.get("custom_fields") or {}
    if cf.get("enrich_position") or cf.get("enrich_pouvoir"):
        return                       # deja renseigne
    textes = []
    for source in (raw or {}).values():
        for champ in ("details", "bio", "description"):
            valeur = (source or {}).get(champ)
            if valeur:
                textes.append(str(valeur))
    if p.get("details"):
        textes.append(str(p["details"]))
    documentation = "\n".join(textes)[:2500]
    if len(documentation) < 60:
        return                       # rien a lire

    lu, motif = deduire_role(ctx, p, documentation)
    if not lu:
        log.debug(f"rôle {p.get('name')} : {motif}")
        return
    partiel = {"enrich_role_origine": "suggéré",
               "enrich_role_motif": str(motif)[:300]}
    for champ, cle in (("position", "enrich_position"),
                       ("pouvoir", "enrich_pouvoir")):
        if lu.get(champ):
            partiel[cle] = str(lu[champ])
    if ctx.simulation():
        log.info(f"[simulation] rôle de {p.get('name')} : {partiel}")
        return
    try:
        ctx.stash.update_performer({
            "id": p["id"], "custom_fields": {"partial": partiel}})
    except Exception as exc:
        log.debug(f"rôle non écrit : {str(exc)[:70]}")


def appliquer_auto(ctx, fiche: dict, cands: dict, urls_valides: list,
                   raw: dict, actuel: dict):
    """Mode auto : la valeur la mieux notée est appliquée d'office,
    quel que soit son score — pour qui ne veut pas passer son temps à
    avaliser. Seuls les champs VIDES sont remplis (jamais d'écrasement
    silencieux). La fiabilité reste visible sur la fiche :
    custom_field `enrich_sources` + pied de bio optionnel. Aucune
    décision utilisateur n'est enregistrée : il n'y en a pas."""
    maj = {"id": fiche["id"]}
    rapport = []
    conflits = []
    changements = {}
    for champ, liste in cands.items():
        if not liste:
            continue
        best = liste[0]
        if actuel.get(champ):
            # JAMAIS d'écrasement — mais le conflit devient VISIBLE
            # (aide à la curation, enrich_rapport).
            if str(best["valeur"]).strip() != str(actuel[champ]).strip():
                conflits.append(ctx.t(
                    "conflit_ligne", champ=champ,
                    actuel=str(actuel[champ])[:30],
                    propose=(f"{str(best['valeur'])[:30]} "
                             f"[{'+'.join(best['sources'])} "
                             f"{best['note']}/10]")))
            continue
        champ_stash = MAP.get(champ, champ)
        if champ_stash not in PERFORMER_FIELDS:
            continue
        val = best["valeur"]
        if champ_stash == "height_cm":
            val = scoring._entier(val)
            if not val:
                continue
        if champ_stash == "circumcised":
            val = str(val).strip().upper()
            if val not in ("CUT", "UNCUT"):
                continue
        maj[champ_stash] = val
        changements[champ_stash] = ["", val]
        com = "; ".join(best["commentaires"])
        rapport.append(f"{champ}: {best['valeur']} ({best['note']}/10 · "
                       f"{'+'.join(best['sources'])}"
                       f"{' · ' + com if com else ''})")
    if urls_valides:
        maj["urls"] = list(dict.fromkeys((fiche.get("urls") or [])
                                         + urls_valides))
        rapport.append(f"urls: +{len(urls_valides)} fiche(s) (stash-box)")
    # Photo : champ STANDARD, uniquement si la fiche n'en a pas
    if (ctx.settings.get("applyImages", True)
            and "default=true" in (fiche.get("image_path") or "")):
        for src2 in sorted(raw, key=lambda x:
                           -sources.SOURCE_WEIGHTS.get(x, 0.4)):
            imgs = [u for u in (raw[src2].get("images") or [])
                    if url_sure(u)]
            if imgs:
                maj["image"] = imgs[0]
                changements["image"] = ["", f"(photo {src2})"]
                rapport.append(f"photo: {src2}")
                break
    # Position (champ custom hérité) → TAG STANDARD Stash
    pos = ((fiche.get("custom_fields") or {}).get("position") or "").strip()
    if pos and ctx.settings.get("positionAsTag", True):
        tid_pos = tag_id(ctx, pos)
        tids_p = {t["id"] for t in fiche.get("tags", [])}
        if tid_pos not in tids_p:
            maj["tag_ids"] = list(tids_p | {tid_pos})
            rapport.append(f"tag position: {pos}")
    if not (fiche.get("details") or "").strip():
        r = synth_bio(ctx, fiche["name"], raw)
        if r:
            val, src, conf, _n = r
            maj["details"] = val
            changements["details"] = ["", "(bio générée)"]
            rapport.append(f"bio: synthèse {src} "
                           f"({round(conf * 10, 1)}/10)")
    if len(maj) <= 1 and not conflits:
        log.info(f"  AUTO {fiche['name']} : rien à compléter")
        return
    stamp = _date_auj.today().isoformat()
    if ctx.annotate_bio():
        base = _sans_footer(maj.get("details") or fiche.get("details") or "")
        lignes = "\n".join("• " + r for r in rapport)
        maj["details"] = (base + footer_mark(ctx) + "\n"
                          + ctx.t("pied_bio_intro", date=stamp)
                          + "\n" + lignes)
    cf = {"enrich_sources": (" | ".join(rapport)
                             + f" · auto {stamp}")[:900]}
    if conflits:
        cf["enrich_rapport"] = ctx.t(
            "conflits", details=" | ".join(conflits))[:900]
    if changements or urls_valides:
        cf["enrich_historique"] = _historique_maj(
            fiche, changements,
            tags_aj=([tag_id(ctx, pos)] if "tag_ids" in maj else None),
            urls_aj=urls_valides or None)
    maj["custom_fields"] = {"partial": cf}
    ctx.stash.update_performer(maj)
    log.info(f"  AUTO {fiche['name']} : "
             f"{len([k for k in maj if k not in ('id', 'custom_fields')])}"
             f" champ(s) appliqués")


def enrich_performers(ctx, limit: int = 25):
    limit = int(ctx.args.get("limit", 0)) or ctx.batch()
    tous = ctx.stash.find_performers()
    cibles = [p for p in tous
              if not (p.get("details") or "").strip()
              or not p.get("birthdate")]
    log.info(f"{len(cibles)} performer(s) incomplet(s) sur {len(tous)} — "
             f"sources : {[b['name'] for b in ctx.stash_boxes]} + "
             f"{ctx.scrapers()}")
    for i, p in enumerate(cibles[:limit], 1):
        try:
            _enrichir_un(ctx, p)
        except Exception as exc:
            log.warning(f"  {p.get('name')} : {str(exc)[:80]}")
        log.progress(i / max(1, min(len(cibles), limit)))
    etiquette = ctx.tag_nom("proposal")
    log.info(f"Terminé. Filtre par le tag '{etiquette}' "
             f"pour valider.")


def enrich_one_performer(ctx):
    pid = (str(ctx.args.get("performer_id") or "")
           or (ctx.args.get("hookContext", {}) or {}).get("id"))
    if not pid:
        return
    p = ctx.stash.find_performer(pid)
    if p:
        _enrichir_un(ctx, p)


def apply_accepted(ctx):
    prefix = ctx.tag_prefix()
    accept = tag_id(ctx, ctx.tag_nom("accept"))
    perfs = ctx.stash.find_performers(f={
        "tags": {"value": [accept], "modifier": "INCLUDES"}})
    n = 0
    for p in perfs:
        maj = {"id": p["id"]}
        urls_add = []
        for t in p.get("tags", []):
            nom_tag = t["name"]
            if not nom_tag.startswith(f"{prefix}:") or "=" not in nom_tag:
                continue
            corps = nom_tag.split(":", 1)[1]
            champ, reste = corps.split("=", 1)
            valeur = reste.split(" [")[0].strip()
            champ = MAP.get(champ.strip(), champ.strip())
            if champ == "details" and valeur.startswith("disponible"):
                # Bio proposée en tag informatif → régénération complète
                raw2, _u2 = collecter_stash(ctx, p["name"])
                r2 = synth_bio(ctx, p["name"], raw2)
                if not r2:
                    continue
                valeur = r2[0]
            if champ == "url":
                # Le tag tronque à 60 car. : ne poser que les URLs
                # complètes (les tronquées seraient invalides).
                if valeur.startswith("http") and not valeur.endswith("…"):
                    urls_add.append(valeur)
                continue
            if champ not in PERFORMER_FIELDS:
                continue
            if champ == "height_cm":
                try:
                    valeur = int(float(valeur))
                except ValueError as exc:
                    log.debug(f"photo alternative non appliquée : {str(exc)[:70]}")
                    continue
            maj[champ] = valeur
        if urls_add:
            maj["urls"] = list(dict.fromkeys(
                (p.get("urls") or []) + urls_add))
        if len(maj) > 1:
            # Décision MANUELLE : mémorisée (contrairement au mode auto
            # et à la masse, où il n'y a pas de choix utilisateur).
            stamp = _date_auj.today().isoformat()
            resume = ", ".join(f"{k}={str(v)[:40]}"
                               for k, v in maj.items() if k != "id")
            maj["custom_fields"] = {"partial": {
                "enrich_decisions": f"{stamp}: {resume}"[:400],
                "enrich_sources": (f"validation manuelle {stamp}: "
                                   f"{resume}")[:400]}}
            ctx.stash.update_performer(maj)
            restes = [t["id"] for t in p.get("tags", [])
                      if not t["name"].startswith(f"{prefix}:")]
            ctx.stash.update_performer({"id": p["id"], "tag_ids": restes})
            n += 1
            log.info(f"  {p['name']} : {len(maj)-1} champ(s) appliqué(s)")
    log.info(f"{n} performer(s) mis à jour dans Stash.")


def regenerate_biohot(ctx):
    """Régénère les bios « hot » : par défaut celles qui sont PAUVRES
    (aucun partenaire dans reco_data — typiquement générées avant que
    les scènes ne soient liées) ; args {"toutes": 1} pour tout refaire.
    Respecte batchSize."""
    toutes = str(ctx.args.get("toutes") or "").strip() in ("1", "true",
                                                           "oui")
    limite = ctx.batch()
    perfs = ctx.stash.find_performers()
    cibles = []
    for p in perfs:
        cf = p.get("custom_fields") or {}
        a_hot = bool(str(cf.get("bio_hot") or "").strip())
        a_reco = bool(cf.get("reco_data"))
        if toutes and a_hot:
            cibles.append(p)
            continue
        # Cibles par défaut : bio pauvre (aucun partenaire) OU bio vide
        # alors qu'un passage a déjà eu lieu (génération ratée).
        try:
            reco = json.loads(cf.get("reco_data") or "{}")
        except Exception:
            reco = {}
        if (a_hot and not reco.get("partenaires")) or (not a_hot and a_reco):
            cibles.append(p)
    log.info(f"{len(cibles)} bio(s) hot à régénérer"
             + ("" if toutes else " (sans partenaire)")
             + f" — lot de {limite}")
    n = echecs = 0
    for i, p in enumerate(cibles[:limite], 1):
        try:
            # La bio existante n'est JAMAIS effacée d'avance : elle
            # n'est remplacée qu'en cas de génération réussie.
            avant = str((p.get("custom_fields") or {}).get("bio_hot")
                        or "")
            generer_bio_hot(ctx, p, {}, force=True)
            frais = ctx.stash.find_performer(p["id"]) or {}
            apres = str((frais.get("custom_fields") or {}).get("bio_hot")
                        or "")
            if apres and apres != avant:
                n += 1
            elif not apres:
                echecs += 1
        except Exception as exc:
            echecs += 1
            log.warning(f"  {p.get('name')} : {str(exc)[:70]}")
        log.progress(i / max(1, min(len(cibles), limite)))
    log.info(f"{n} bio(s) hot régénérée(s)"
             + (f", {echecs} échec(s) (limite de débit du LLM ? "
                f"relancer la tâche)" if echecs else "") + ".")
