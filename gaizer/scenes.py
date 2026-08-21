# -*- coding: utf-8 -*-
"""Enrichissement des scènes : identification par
empreinte, repli sur le nom de fichier, application."""

from __future__ import annotations

import re
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
import scrapers
import sources
import scoring
from noyau import (
    _historique_maj,
    _ligne_fiche,
    _perime,
    _tag_exclu,
    tag_id,
    url_sure)
from collecte import (
    _index_referentiel,
    _nettoie_studio,
    _resoudre,
    collecter_scene)
from ia import synth_synopsis
from entites import (
    _creer_performer_minimal,
    _creer_studio,
    poser_proposition_scene)


def _coherence_fichier(basename: str, titre: str, studio: str,
                       perfs: list) -> tuple:
    """
    if not ctx.source_active("nomfichier"):
        returnLe NOM DE FICHIER corrobore-t-il l'identification par EMPREINTE ?
    (score 0-1, détail). Une divergence n'invalide pas le phash — les
    fichiers renommés sont un cas légitime — mais mérite un œil."""
    base = re.sub(r"[^a-z0-9]", "", (basename or "").lower())
    if not base:
        return None, ""
    trouves, rates = [], []
    mots = [m for m in re.findall(r"[a-z0-9]{3,}", (titre or "").lower())
            if m not in ("the", "and", "for", "part", "scene", "gay")]
    if mots:
        hit = sum(1 for m in mots if m in base)
        (trouves if hit / len(mots) >= 0.5 else rates).append(
            f"titre {hit}/{len(mots)}" if hit else "titre")
    if studio:
        ok = (re.sub(r"[^a-z0-9]", "", studio.lower()) in base
              or any(m in base for m in
                     re.findall(r"[a-z0-9]{4,}", studio.lower())))
        (trouves if ok else rates).append("studio")
    if perfs:
        hits = [n for n in perfs
                if re.sub(r"[^a-z0-9]", "", (n or "").lower()) in base]
        (trouves if hits else rates).append(
            f"{len(hits)}/{len(perfs)} acteurs" if hits else "acteurs")
    total = len(trouves) + len(rates)
    if not total:
        return None, ""
    return (len(trouves) / total,
            "+".join(trouves) if trouves else "aucun recoupement")


def _marquer_non_identifiee(ctx, s: dict, manquante: bool):
    """Pose ou retire `Gaizer:non-identifiée` — idempotent, pour
    qu'un filtre de l'UI liste les scènes qu'aucune source ne
    reconnaît (ni empreinte, ni nom de fichier)."""
    try:
        tid = tag_id(ctx, ctx.tag_nom("unidentified"))
        actuels = {t["id"] for t in s.get("tags") or []}
        if manquante and tid not in actuels:
            ctx.stash.update_scene({"id": s["id"],
                                    "tag_ids": list(actuels | {tid})})
            s.setdefault("tags", []).append(
                {"id": tid, "name": ctx.tag_nom("unidentified")})
        elif not manquante and tid in actuels:
            ctx.stash.update_scene({"id": s["id"],
                                    "tag_ids": list(actuels - {tid})})
            s["tags"] = [t for t in s.get("tags") or [] if t["id"] != tid]
    except Exception as exc:
        log.debug(f"marquage non-identifiée {s.get('id')} : {exc}")


def _repli_nom_fichier(ctx, s: dict, force_auto: bool):
    """Sans identification par empreinte (collections absentes des
    stash-boxes), le NOM DE FICHIER reste exploitable : studios et
    performers du RÉFÉRENTIEL (alias compris) recherchés dedans, titre
    nettoyé. Fiabilité moindre — signalée comme telle."""
    basename = ((s.get("files") or [{}])[0].get("basename") or "")
    if not basename:
        return
    idx_perfs, idx_studios = _index_referentiel(ctx)
    base = re.sub(r"[^a-z0-9]", "", basename.lower())
    studio_id = None
    for cle, sid in sorted(idx_studios.items(),
                           key=lambda kv: -len(kv[0])):
        if len(cle) >= 5 and cle in base:
            studio_id = sid
            break
    perf_ids = {pid for cle, pid in idx_perfs.items()
                if len(cle) >= 6 and cle in base}
    titre = re.sub(r"\.[a-z0-9]{2,4}$", "", basename, flags=re.I)
    titre = re.sub(r"[_.]+", " ", titre)
    titre = re.sub(r"\s{2,}", " ", titre).strip()
    if not perf_ids and not studio_id:
        # Rien du tout : la scène devient FILTRABLE dans l'UI plutôt
        # que perdue dans un log.
        _marquer_non_identifiee(ctx, s, True)
        log.info(f"  scène {s['id']} : ni empreinte, ni entité Stash "
                 f"reconnue dans le nom de fichier")
        return
    _marquer_non_identifiee(ctx, s, False)
    if force_auto or ctx.apply_mode() == "auto":
        maj = {"id": s["id"]}
        rapport = [ctx.t("par_nom_fichier")]
        if not (s.get("title") or "").strip():
            maj["title"] = titre[:120]
        if studio_id and not s.get("studio"):
            maj["studio_id"] = studio_id
            rapport.append("studio: retrouvé dans le nom (données Stash)")
        existants = {str(q["id"]) for q in s.get("performers") or []}
        if perf_ids - existants:
            maj["performer_ids"] = list(existants | perf_ids)
            rapport.append(f"performers: +{len(perf_ids - existants)}")
        if len(maj) <= 1:
            return
        maj["custom_fields"] = {"partial": {"enrich_sources":
            (" | ".join(rapport)
             + f" · auto {_date_auj.today().isoformat()}")[:900]}}
        ctx.stash.update_scene(maj)
        log.info(f"  AUTO scène {s['id']} (nom de fichier) : "
                 + "; ".join(rapport[1:])[:100])
    else:
        marqueur = tag_id(ctx, ctx.tag_nom("proposal"))
        tids = {t["id"] for t in s.get("tags") or []} | {marqueur}
        ctx.stash.update_scene({
            "id": s["id"], "tag_ids": list(tids),
            "custom_fields": {"partial": {"enrich_rapport":
                ("identifiable par nom de fichier : "
                 + ("studio " if studio_id else "")
                 + f"{len(perf_ids)} acteur(s) — accepter la scène "
                   "ou passer en mode auto")[:400]}}})


class EntitesScene:
    """Studio, interprètes et tags qu'une scène tire de ses sources,
    rapprochés des données de Stash.

    - `studio_id` / `perf_ids` : identifiants Stash retrouvés
    - `studio_src` / `perf_inconnus` : ce que les sources nomment sans
      qu'on sache le relier — à créer ou à signaler
    - `noms_tags` : tags des sources, hors ceux exclus par réglage
    """

    __slots__ = (
        "idx_perfs",
        "idx_studios",
        "noms_tags",
        "perf_ids",
        "perf_inconnus",
        "studio_id",
        "studio_inconnu",
        "studio_nom_src",
        "studio_src",
    )

    def __init__(self, ctx, raw):
        self.idx_perfs, self.idx_studios = _index_referentiel(ctx)
        self.studio_id = self.studio_inconnu = None
        self.studio_src = self.studio_nom_src = None
        self.perf_ids, self.perf_inconnus = set(), []
        self.noms_tags = {}
        exclus = ctx.tags_exclus()
        for d in raw.values():
            self._lire_studio(d.get("studio"))
            self._lire_performers(d.get("performers") or [])
            self._lire_tags(d.get("tags") or [], exclus)

    def _lire_studio(self, st):
        if not st:
            return
        if not self.studio_nom_src:
            self.studio_nom_src = st.get("name")
        sid = _resoudre(_nettoie_studio(st.get("name")),
                        st.get("stored_id"), self.idx_studios)
        if sid and not self.studio_id:
            self.studio_id = sid
        elif not sid and not self.studio_src:
            self.studio_src = st
            self.studio_inconnu = st.get("name")

    def _lire_performers(self, liste):
        for q in liste:
            pid = _resoudre(q.get("name"), q.get("stored_id"),
                            self.idx_perfs)
            if pid:
                self.perf_ids.add(pid)
            elif q.get("name"):
                self.perf_inconnus.append(q["name"])

    def _lire_tags(self, liste, exclus):
        for t in liste:
            if not _tag_exclu(t["name"], exclus):
                self.noms_tags[t["name"]] = t.get("stored_id")

    def noms_performers_sources(self, raw):
        return list({q.get("name") for d in raw.values()
                     for q in d.get("performers") or []
                     if q.get("name")})


def _poser_urls(s: dict, raw: dict, maj: dict, rapport: list) -> None:
    """Ajoute les adresses des fiches sources.

    ADDITIVES, jamais écrasantes : une adresse saisie à la main vaut
    autant que celle d'une source, et rien ne permet de trancher.
    """
    trouvees = []
    for donnees in raw.values():
        for url in donnees.get("urls") or []:
            if url and url not in (s.get("urls") or []):
                trouvees.append(url)
    trouvees = list(dict.fromkeys(trouvees))
    if not trouvees:
        return
    maj["urls"] = list(dict.fromkeys((s.get("urls") or []) + trouvees))
    rapport.append(f"urls: +{len(trouvees)}")


def _poser_cover(ctx, raw: dict, maj: dict, rapport: list):
    """Retient la jaquette officielle, et rend sa provenance.

    Elle REMPLACE la vignette existante : l'image du studio est plus
    représentative qu'une image extraite de la vidéo. Le remplacement
    n'est pas restaurable — `applySceneCovers=false` pour s'en
    abstenir.
    """
    if not ctx.settings.get("applySceneCovers", True):
        return None
    for source in sorted(raw, key=lambda x:
                         -sources.SOURCE_WEIGHTS.get(x, 0.4)):
        img = raw[source].get("image")
        if img and url_sure(img):
            maj["cover_image"] = img
            rapport.append(f"cover officielle: {source}")
            return f"{source} ({_date_auj.today().isoformat()})"
    return None


def _appliquer_scene(ctx, s, raw, cands, ent, actuel):
    """Écrit dans Stash tout ce que les sources ont apporté sur
    une scène : titre et date retenus, studio et interprètes
    rapprochés ou créés, tags, synopsis, URLs, cover officielle.

    Sépare l'ÉCRITURE de la collecte : `_enrichir_scene` décide
    quoi faire, cette fonction le fait. Rien n'écrase une valeur
    existante — seuls les champs vides sont complétés."""
    idx_perfs, idx_studios = ent.idx_perfs, ent.idx_studios
    studio_id, studio_inconnu = ent.studio_id, ent.studio_inconnu
    studio_src, studio_nom_src = ent.studio_src, ent.studio_nom_src
    perf_ids, perf_inconnus = set(ent.perf_ids), list(ent.perf_inconnus)
    noms_tags = ent.noms_tags
    maj = {"id": s["id"]}
    rapport = []
    for champ, liste in cands.items():
        if liste and not actuel.get(champ):
            best = liste[0]
            maj[champ] = best["valeur"]
            rapport.append(f"{champ}: {str(best['valeur'])[:40]} "
                           f"({best['note']}/10 · "
                           f"{'+'.join(best['sources'])})")
    if (not studio_id and studio_src
            and ctx.settings.get("createMissing", True)):
        studio_id = _creer_studio(ctx, studio_src, idx_studios)
        if studio_id:
            studio_inconnu = None
            rapport.append("studio: créé + rattaché à son parent")
    if studio_id and not s.get("studio"):
        maj["studio_id"] = studio_id
        if not any(r.startswith("studio:") for r in rapport):
            rapport.append("studio: assigné (données Stash)")
    if perf_inconnus and ctx.settings.get("createMissing", True):
        crees = 0
        for nom_p in sorted(set(perf_inconnus)):
            pid = _creer_performer_minimal(ctx, nom_p, idx_perfs)
            if pid:
                perf_ids.add(pid)
                crees += 1
        if crees:
            rapport.append(f"performers créés: {crees} "
                           f"(fiches minimales à enrichir)")
            perf_inconnus = []
    nouveaux_perfs = perf_ids - {str(q["id"])
                                 for q in s.get("performers") or []}
    if nouveaux_perfs:
        maj["performer_ids"] = list(
            {str(q["id"]) for q in s.get("performers") or []}
            | perf_ids)
        rapport.append(f"performers: +{len(nouveaux_perfs)}")
    _poser_urls(s, raw, maj, rapport)
    cf_cover = _poser_cover(ctx, raw, maj, rapport)
    if noms_tags:
        tids = {t["id"] for t in s.get("tags") or []
                if not t["name"].startswith(ctx.tag_prefix())}
        for nom_t, sid in noms_tags.items():
            tids.add(sid or tag_id(ctx, nom_t))
        maj["tag_ids"] = list(tids)
        rapport.append(f"tags: {len(noms_tags)} (sources, bruts)")
    if not (s.get("details") or "").strip():
        r = synth_synopsis(ctx, str(maj.get("title")
                                    or s.get("title") or ""), raw)
        if r:
            maj["details"], src_syn = r
            rapport.append(f"synopsis: {src_syn}")
    # Contrôle croisé : le nom de fichier corrobore-t-il le phash ?
    basename = ((s.get("files") or [{}])[0].get("basename") or "")
    noms_src = list({q.get("name") for d in raw.values()
                     for q in d.get("performers") or []
                     if q.get("name")})
    score, detail = _coherence_fichier(
        basename, str(maj.get("title") or s.get("title") or ""),
        _nettoie_studio(studio_nom_src or "") or None, noms_src)
    if score is not None:
        if score > 0:
            rapport.append(ctx.t("coherence_fichier",
                                 score=f"{score:.0%}",
                                 detail=detail))
        else:
            rapport.append(ctx.t("coherence_nulle"))
            tids = set(maj.get("tag_ids")
                       or [t["id"] for t in s.get("tags") or []])
            tids.add(tag_id(ctx, ctx.tag_nom("verify")))
            maj["tag_ids"] = list(tids)
    if perf_inconnus:
        rapport.append("inconnus de Stash: "
                       + ", ".join(sorted(set(perf_inconnus))[:4]))
    if studio_inconnu:
        rapport.append(f"studio inconnu de Stash: {studio_inconnu}")
    if len(maj) <= 1:
        return
    stamp = _date_auj.today().isoformat()
    changements = {c: [str(actuel.get(c) or "")[:60],
                       str(maj[c])[:60]]
                   for c in ("title", "date", "details")
                   if c in maj}
    if "studio_id" in maj:
        changements["studio_id"] = [
            str(((s.get("studio") or {}).get("id")) or ""),
            str(maj["studio_id"])]
    tags_aj = None
    if "tag_ids" in maj:
        avant_t = {t["id"] for t in s.get("tags") or []}
        tags_aj = [t for t in maj["tag_ids"] if t not in avant_t]
    perfs_aj = list(nouveaux_perfs) if nouveaux_perfs else None
    cf_sc = {"enrich_sources": (" | ".join(rapport)
                                + f" · auto {stamp}")[:900],
             "enrich_historique": _historique_maj(
                 s, changements, tags_aj=tags_aj,
                 perfs_aj=perfs_aj)}
    if cf_cover:
        cf_sc["enrich_cover"] = cf_cover
    maj["custom_fields"] = {"partial": cf_sc}
    ctx.stash.update_scene(maj)
    log.info(f"  AUTO scène {s['id']} : "
             + "; ".join(rapport)[:110])
    return


def _enrichir_scene(ctx, s: dict, force_auto: bool = False):
    raw = collecter_scene(ctx, s)
    if not raw:
        _repli_nom_fichier(ctx, s, force_auto)
        return
    _marquer_non_identifiee(ctx, s, False)   # empreinte trouvée
    actuel = {"title": s.get("title"), "date": s.get("date")}
    plat = {src: {k: v for k, v in d.items() if k in ("title", "date")}
            for src, d in raw.items()}
    cands = scoring.evaluer_tous(plat, actuel, {"title", "date"},
                                 ctx.cfg)

    # Studio / performers / tags : union des sources, rapprochés du
    # référentiel (stored_id de Stash, sinon nom/alias nettoyé). Les
    # inconnus sont créés si createMissing (studios avec parent,
    # performers en fiche minimale), sinon signalés.
    ent = EntitesScene(ctx, raw)
    studio_id, studio_inconnu = ent.studio_id, ent.studio_inconnu
    perf_ids, perf_inconnus = ent.perf_ids, ent.perf_inconnus
    noms_tags = ent.noms_tags

    if force_auto or ctx.apply_mode() == "auto":
        _appliquer_scene(ctx, s, raw, cands, ent, actuel)
        return

    # Mode manuel : propositions (tags) + fiche de décision.
    fiche = []
    for champ, liste in cands.items():
        for c in liste:
            poser_proposition_scene(ctx, s, champ, c["valeur"],
                                    "+".join(c["sources"]), c["note"],
                                    c["recommande"])
        fiche.append(_ligne_fiche(champ, liste))
    if not (s.get("details") or "").strip() and any(
            d.get("details") for d in raw.values()):
        poser_proposition_scene(
            ctx, s, "synopsis",
            f"disponible ({sum(1 for d in raw.values() if d.get('details'))} source(s))",
            "+".join(sorted(raw)), 7.5, True)
    if noms_tags:
        fiche.append("tags sources: "
                     + ", ".join(sorted(noms_tags))[:220])
    if perf_ids or perf_inconnus:
        fiche.append(f"performers: {len(perf_ids)} connus de Stash"
                     + (" ; inconnus: "
                        + ", ".join(sorted(set(perf_inconnus))[:4])
                        if perf_inconnus else ""))
    if studio_id or studio_inconnu:
        fiche.append("studio: "
                     + ("connu de Stash" if studio_id
                        else f"inconnu ({studio_inconnu})"))
    if fiche:
        ctx.stash.update_scene({
            "id": s["id"],
            "custom_fields": {"partial": {
                "enrich_rapport": " | ".join(fiche)[:900]}}})


def enrich_scenes(ctx, limit: int = 25):
    limit = int(ctx.args.get("limit", 0)) or ctx.batch()
    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             id title date details urls custom_fields
             files { basename }
             studio { id name }
             performers { id name }
             tags { id name } } } }""")
    tous = d["findScenes"]["scenes"]
    cibles = [s for s in tous
              if not s.get("date") or not s.get("studio")
              or not (s.get("details") or "").strip()
              or not s.get("performers") or _perime(ctx, s)]
    log.info(f"{len(cibles)} scène(s) incomplète(s) sur {len(tous)} — "
             f"identification par empreinte via "
             f"{[b['name'] for b in ctx.stash_boxes]}")
    for i, s in enumerate(cibles[:limit], 1):
        _enrichir_scene(ctx, s)
        log.progress(i / max(1, min(len(cibles), limit)))
    log.info("Terminé (scènes).")

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


def apply_accepted_scenes(ctx):
    """L'accept d'une scène (tag Gaizer:accept) déclenche son
    application complète — mêmes règles que le mode auto — puis les
    tags de proposition sont retirés. Décision mémorisée."""
    prefix = ctx.tag_prefix()
    accept = tag_id(ctx, ctx.tag_nom("accept"))
    d = ctx.stash.call_GQL(
        """query($tid: [ID!]!) { findScenes(scene_filter: {tags:
             {value: $tid, modifier: INCLUDES}},
             filter: {per_page: -1}) { scenes {
               id title date details
               files { basename }
               studio { id name }
               performers { id name }
               tags { id name } } } }""", {"tid": [accept]})
    n = 0
    stamp = _date_auj.today().isoformat()
    for s in d["findScenes"]["scenes"]:
        _enrichir_scene(ctx, s, force_auto=True)
        restes = [t["id"] for t in s.get("tags", [])
                  if not t["name"].startswith(f"{prefix}:")]
        ctx.stash.update_scene({
            "id": s["id"], "tag_ids": restes,
            "custom_fields": {"partial": {
                "enrich_decisions":
                    f"{stamp}: scène validée manuellement"}}})
        n += 1
    log.info(f"{n} scène(s) appliquée(s) et nettoyée(s).")


def enrich_one_scene(ctx):
    """Enrichit UNE scène (args scene_id) — utilisé par le bouton
    injecté dans la page scène."""
    sid = str(ctx.args.get("scene_id") or "")
    if not sid:
        return
    d = ctx.stash.call_GQL(
        """query($id: ID!) { findScene(id: $id) {
             id title date details files { basename }
             studio { id name } performers { id name }
             tags { id name } custom_fields } }""", {"id": sid})
    sc = d.get("findScene")
    if sc:
        _enrichir_scene(ctx, sc)


def apply_covers(ctx):
    """Applique les covers OFFICIELLES aux scènes déjà identifiées par
    empreinte : ré-interroge les stash-boxes pour récupérer l'image de
    la source la plus fiable. Les scènes qui en ont déjà une (champ
    enrich_cover) sont sautées. Respecte batchSize."""
    limite = ctx.batch()
    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             id title custom_fields } } }""")
    cibles = []
    for sc in d["findScenes"]["scenes"]:
        cf = sc.get("custom_fields") or {}
        src = str(cf.get("enrich_sources") or "")
        if not src or "NOM DE FICHIER" in src:
            continue          # jamais identifiée : pas de cover source
        if str(cf.get("enrich_cover") or "").strip():
            continue          # déjà posée
        cibles.append(sc)
    log.info(f"{len(cibles)} scène(s) sans cover officielle — lot de "
             f"{limite}")
    n = 0
    for i, sc in enumerate(cibles[:limite], 1):
        try:
            raw = collecter_scene(ctx, sc)
            img = src2 = None
            for cle in sorted(raw, key=lambda x:
                              -sources.SOURCE_WEIGHTS.get(x, 0.4)):
                if url_sure(raw[cle].get("image")):
                    img, src2 = raw[cle]["image"], cle
                    break
            if not img:
                continue
            ctx.stash.update_scene({
                "id": sc["id"], "cover_image": img,
                "custom_fields": {"partial": {
                    "enrich_cover": f"{src2} "
                                    f"({_date_auj.today().isoformat()})"}}})
            n += 1
            log.info(f"  cover officielle : scène {sc['id']} "
                     f"({(sc.get('title') or '')[:36]}) ← {src2}")
        except Exception as exc:
            log.warning(f"  scène {sc.get('id')} : {str(exc)[:70]}")
        log.progress(i / max(1, min(len(cibles), limite)))
    log.info(f"{n} cover(s) officielle(s) appliquée(s).")
