# -*- coding: utf-8 -*-
"""
Trancher : la seule famille qui écrase.

Le plugin n'écrase jamais — un désaccord est signalé et
laissé tel quel. C'est la bonne règle par défaut : la fiche
peut être juste et les sources se tromper.

Ces tâches sont l'EXCEPTION explicite. Elles écrivent par-
dessus, sur demande, et l'ancienne valeur passe dans
l'historique pour que l'annulation reste possible.
"""

from __future__ import annotations
import re
import sys
from datetime import date as _date_auj
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stashapi import log
import noyau
import scoring
from noyau import (
    MAP,
    _historique_maj,
    PERFORMER_FIELDS,
    tag_id)
from entites import _restaurer_entite
from scenes import _enrichir_scene


_CONFLIT = re.compile(
    r"(\w+)\s*:\s*actuel « ([^»]*) » vs sources\s*:\s*"
    r"(.+?)\s*\[([^\]]*?)\s*([\d.]+)/10\]")


def _ecart_significatif(champ, actuel, propose) -> bool:
    """Un désaccord d'un centimètre n'en est pas un.

    Les sources arrondissent différemment une taille convertie depuis
    les pouces : 5'10\" donne 177 ou 178 selon qui calcule. Traiter cela
    comme un conflit noierait les vrais écarts — treize centimètres —
    sous des dizaines de faux."""
    if champ in ("height_cm", "weight", "penis_length"):
        try:
            a = float(re.sub(r"[^\d.]", "", str(actuel)))
            b = float(re.sub(r"[^\d.]", "", str(propose)))
        except (ValueError, TypeError):
            return True
        return abs(a - b) > 2
    if champ == "birthdate":
        da, db = scoring._date(actuel), scoring._date(propose)
        if da and db:
            return abs((da - db).days) > 1
    return str(actuel).strip().lower() != str(propose).strip().lower()


def arbitrer_conflits(ctx):
    """Remplace une valeur de fiche par celle des sources, quand
    celles-ci sont largement d'accord.

    Le plugin n'écrase jamais : un désaccord est signalé et laissé tel
    quel. C'est la bonne règle par défaut — la fiche peut être juste
    et les sources se tromper. Mais quand six familles indépendantes
    disent la même chose contre une valeur d'origine inconnue, laisser
    le désaccord dormir n'est plus de la prudence.

    Cette tâche est donc l'EXCEPTION explicite : elle écrase, sur
    demande, et seulement au-dessus d'un seuil. L'ancienne valeur passe
    dans l'historique, donc « Annuler le dernier passage » la rétablit.

    Arguments : `note` (défaut 9.0), `champs` pour restreindre.
    """
    try:
        seuil = float(str(ctx.args.get("note") or 9.0).replace(",", "."))
    except (TypeError, ValueError):
        seuil = 9.0
    voulus = {c.strip() for c in
              str(ctx.args.get("champs") or "").split(",") if c.strip()}

    perfs = ctx.stash.find_performers()
    appliques, ignores, minimes = 0, 0, 0
    par_champ = {}
    for p in perfs:
        cf = p.get("custom_fields") or {}
        rap = str(cf.get("enrich_rapport") or "")
        if "CONFLIT" not in rap:
            continue
        maj, changements = {}, {}
        for m in _CONFLIT.finditer(rap):
            champ, actuel, propose, _srcs, note = m.groups()
            if voulus and champ not in voulus:
                continue
            try:
                if float(note) < seuil:
                    ignores += 1
                    continue
            except ValueError as exc:
                log.debug(f"valeur non appliquée sur cette fiche : {str(exc)[:70]}")
                continue
            propose = propose.strip()
            if not _ecart_significatif(champ, actuel, propose):
                minimes += 1
                continue
            # La valeur affichée est tronquée dans le rapport : au-delà
            # d'une trentaine de caractères, on ne peut pas la
            # réécrire fidèlement.
            if len(propose) >= 30:
                ignores += 1
                continue
            maj[champ] = propose
            changements[champ] = [actuel, propose]
            par_champ[champ] = par_champ.get(champ, 0) + 1
        if not maj:
            continue
        appliques += 1
        log.info(f"  {p['name'][:28]:30s} "
                 + " · ".join(f"{c} : {v[0]} → {v[1]}"
                              for c, v in changements.items()))
        entree = dict(maj, id=p["id"])
        entree["custom_fields"] = {"partial": {
            "enrich_historique": _historique_maj(p, changements)}}
        try:
            ctx.stash.update_performer(entree)
        except Exception as exc:
            log.warning(f"    échec : {str(exc)[:70]}")

    log.info(f"{appliques} fiche(s) alignées sur les sources · "
             + " · ".join(f"{c} ({n})" for c, n in
                          sorted(par_champ.items(), key=lambda x: -x[1])))
    log.info(f"{minimes} écart(s) trop faibles pour compter "
             f"(arrondis de conversion) · {ignores} sous le seuil de "
             f"{seuil}/10 ou illisibles")
    if ctx.simulation():
        log.info("SIMULATION : rien n'a été écrit.")
    else:
        log.info("Les valeurs remplacées sont dans l'historique : "
                 "« Annuler le dernier passage » les rétablit fiche "
                 "par fiche.")


def apply_recommended(ctx):
    """Validation de MASSE : applique les recommandations (★) dont la
    note ≥ autoAcceptThreshold ; les autres restent en proposition.
    Aucune décision utilisateur n'est enregistrée — il n'y en a pas."""
    prefix = ctx.tag_prefix()
    seuil = ctx.auto_threshold()
    marqueur = tag_id(ctx, ctx.tag_nom("proposal"))
    perfs = ctx.stash.find_performers(f={
        "tags": {"value": [marqueur], "modifier": "INCLUDES"}})
    stamp = _date_auj.today().isoformat()
    n_perf = n_champs = 0
    for p in perfs:
        maj = {"id": p["id"]}
        urls_add = []
        for t in p.get("tags", []):
            nomt = t["name"]
            if (not nomt.startswith(f"{prefix}:") or "=" not in nomt
                    or not nomt.endswith("★")):
                continue
            m = re.search(r"\s(\d+(?:\.\d+)?)/10\]★$", nomt)
            if not m or float(m.group(1)) < seuil:
                continue
            corps = nomt.split(":", 1)[1]
            champ, reste = corps.split("=", 1)
            valeur = reste.split(" [")[0].strip()
            champ = MAP.get(champ.strip(), champ.strip())
            if champ == "url":
                if valeur.startswith("http"):
                    urls_add.append(valeur)
                continue
            if champ not in PERFORMER_FIELDS:
                continue
            if champ == "height_cm":
                valeur = scoring._entier(valeur)
                if not valeur:
                    continue
            maj[champ] = valeur
        if urls_add:
            maj["urls"] = list(dict.fromkeys(
                (p.get("urls") or []) + urls_add))
        champs_ok = [k for k in maj if k not in ("id", "urls")]
        if len(maj) <= 1:
            continue
        resume = ", ".join(f"{k}={str(maj[k])[:40]}" for k in champs_ok)
        maj["custom_fields"] = {"partial": {
            "enrich_sources": (f"masse auto {stamp} (seuil {seuil}): "
                               f"{resume}")[:900]}}
        ctx.stash.update_performer(maj)
        # Retire les tags des champs appliqués (recommandé + concurrents)
        traites = set(champs_ok) | ({"url", "urls"} if urls_add else set())
        garder, reste_detail = [], False
        for t in p.get("tags", []):
            nomt = t["name"]
            if nomt == ctx.tag_nom("proposal"):
                continue
            if nomt.startswith(f"{prefix}:") and "=" in nomt:
                brut = nomt.split(":", 1)[1].split("=", 1)[0].strip()
                if MAP.get(brut, brut) in traites:
                    continue
                reste_detail = True
            garder.append(t["id"])
        if reste_detail:
            garder.append(marqueur)
        ctx.stash.update_performer({"id": p["id"], "tag_ids": garder})
        n_perf += 1
        n_champs += len(champs_ok) + (1 if urls_add else 0)
        log.info(f"  MASSE {p['name']} : {resume[:80]}")
    # Scènes en proposition : appliquées intégralement (mêmes règles
    # que le mode auto) si leur recommandation ★ atteint le seuil. Les
    # replis nom-de-fichier (sans ★) restent à l'accept explicite.
    d = ctx.stash.call_GQL(
        """query($tid: [ID!]!) { findScenes(scene_filter: {tags:
             {value: $tid, modifier: INCLUDES}},
             filter: {per_page: -1}) { scenes {
               id title date details
               files { basename }
               studio { id name }
               performers { id name }
               tags { id name } } } }""", {"tid": [marqueur]})
    n_sc = 0
    for sc in d["findScenes"]["scenes"]:
        if not any((m := re.search(r"\s(\d+(?:\.\d+)?)/10\]★$",
                                   t["name"]))
                   and float(m.group(1)) >= seuil
                   for t in sc.get("tags", [])):
            continue
        _enrichir_scene(ctx, sc, force_auto=True)
        restes = [t["id"] for t in sc.get("tags", [])
                  if not t["name"].startswith(f"{prefix}:")]
        ctx.stash.update_scene({"id": sc["id"], "tag_ids": restes})
        n_sc += 1
    log.info(f"Masse (seuil {seuil}) : {n_perf} performer(s) "
             f"({n_champs} champ(s)) + {n_sc} scène(s) appliqués. "
             f"Les propositions sous le seuil restent à arbitrer.")


def restore_marked(ctx):
    """Restaure les entités portant le tag standard
    `Gaizer:restaurer` (dernier passage annulé), puis retire le
    tag. Relancer la tâche = remonter d'un passage de plus."""
    trest = tag_id(ctx, ctx.tag_nom("restore"))
    n = 0
    for p in ctx.stash.find_performers(f={"tags": {
            "value": [trest], "modifier": "INCLUDES"}}):
        if _restaurer_entite(ctx, p, est_scene=False):
            n += 1
            restes = [t["id"] for t in p.get("tags", [])
                      if t["id"] != trest]
            ctx.stash.update_performer({"id": p["id"],
                                        "tag_ids": restes})
            log.info(f"  restauré : {p['name']}")
    d = ctx.stash.call_GQL(
        """query($tid: [ID!]!) { findScenes(scene_filter: {tags:
             {value: $tid, modifier: INCLUDES}},
             filter: {per_page: -1}) { scenes {
               id title performers { id } urls: files { basename }
               tags { id name } custom_fields } } }""",
        {"tid": [trest]})
    for sc in d["findScenes"]["scenes"]:
        if _restaurer_entite(ctx, sc, est_scene=True):
            n += 1
            restes = [t["id"] for t in sc.get("tags", [])
                      if t["id"] != trest]
            ctx.stash.update_scene({"id": sc["id"], "tag_ids": restes})
            log.info(f"  restauré : scène {sc['id']}")
    # Studios : pas de tags dans Stash — le bouton « Restaurer » de
    # l'interface pose le custom_field enrich_restaurer.
    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name url details parent_studio { id }
             custom_fields } } }""")
    for st in d["findStudios"]["studios"]:
        if not (st.get("custom_fields") or {}).get("enrich_restaurer"):
            continue
        if _restaurer_entite(ctx, st, est_scene=False, est_studio=True):
            n += 1
            log.info(f"  restauré : studio {st['name']}")
        ctx.stash.call_GQL(
            "mutation($input: StudioUpdateInput!) "
            "{ studioUpdate(input: $input) { id } }",
            {"input": {"id": st["id"], "custom_fields": {"partial": {
                "enrich_restaurer": ""}}}})
    log.info(f"{n} entité(s) restaurée(s).")

def valider_fiche(ctx):
    """Retire les marques de vérification d'une fiche entière.

    Un signalement qui ne peut pas être levé devient du bruit :
    l'utilisateur voit la pastille, ne sait qu'en faire, et cesse de
    la regarder.

    La validation est TOUT OU RIEN. Cocher champ par champ
    reproduirait l'éditeur de Stash en moins bien ; pour corriger une
    valeur précise, l'édition normale de la fiche est le bon outil —
    et corriger une valeur la valide de fait.

    Elle ne réécrit RIEN : la valeur est déjà dans la fiche. Elle dit
    « j'ai regardé », et l'historique la défait comme toute autre
    écriture du plugin.

    Arguments : performer_id, studio_id ou scene_id.
    """
    args = getattr(ctx, "args", None) or {}
    for cle, genre in (("performer_id", "performer"),
                       ("studio_id", "studio"),
                       ("scene_id", "scene")):
        ident = str(args.get(cle) or "").strip()
        if ident:
            break
    else:
        log.warning("valider_fiche : aucun identifiant "
                    "(performer_id, studio_id ou scene_id).")
        return

    lire = {"performer": ctx.stash.find_performer,
            "studio": ctx.stash.find_studio,
            "scene": ctx.stash.find_scene}[genre]
    try:
        fiche = lire(ident)
    except Exception as exc:
        log.warning(f"fiche {ident} illisible : {str(exc)[:70]}")
        return
    if not fiche:
        log.warning(f"fiche {ident} introuvable.")
        return

    cf = fiche.get("custom_fields") or {}
    brut = str(cf.get("enrich_sources") or "")
    if not brut.strip():
        log.info("Rien à vérifier sur cette fiche.")
        return

    # La note et les sources disparaissent, la valeur reste : c'est
    # elle qui compte, et la relire ne servirait à rien.
    propre = re.sub(r"\s*\([\d.]+/10[^)]*\)", "", brut)
    propre = re.sub(r"\s+", " ", propre).strip()
    if propre == brut.strip():
        log.info("Rien à vérifier sur cette fiche.")
        return

    if ctx.simulation():
        log.info(f"[simulation] marques de vérification de la fiche "
                 f"{ident} — rien n'est écrit.")
        return

    ecrire = {"performer": "update_performer",
              "studio": "update_studio",
              "scene": "update_scene"}[genre]
    # L'historique rend la validation réversible, comme toute autre
    # écriture du plugin : « Annuler le dernier passage » la défait.
    try:
        hist = noyau._historique_maj(
            fiche, {"enrich_sources": [brut, propre]})
    except Exception as exc:
        log.debug(f"historique : {str(exc)[:70]}")
        hist = None
    partiel = {"enrich_sources": propre,
               "enrich_verifie": _date_auj.today().isoformat()}
    if hist:
        partiel["enrich_historique"] = hist
    try:
        getattr(ctx.stash, ecrire)({
            "id": ident,
            "custom_fields": {"partial": partiel}})
        log.info(f"Fiche {ident} vérifiée : les valeurs restent, les "
                 f"marques sont levées.")
    except Exception as exc:
        log.warning(f"fiche {ident} : {str(exc)[:70]}")
