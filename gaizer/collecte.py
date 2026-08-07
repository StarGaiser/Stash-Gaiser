# -*- coding: utf-8 -*-
"""Interrogation des sources : stash-boxes, scrapers,
passe URL, sources d'appoint, et statistiques tirées
de la collection."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
import sources
import noyau
from noyau import Context, POIDS, POIDS_DEFAUT


GQL_SCRAPE_SINGLE = """
query($src: ScraperSourceInput!, $in: ScrapeSinglePerformerInput!) {
  scrapeSinglePerformer(source: $src, input: $in) {
    name birthdate height country ethnicity career_length details urls
    measurements circumcised images
  }
}"""


GQL_SCRAPE_URL = """
query($url: String!) {
  scrapePerformerURL(url: $url) {
    name birthdate height country ethnicity career_length details
    measurements circumcised images
  }
}"""


# =============================================================================
# Scènes — identification par empreinte + enrichissement
# =============================================================================

GQL_SCRAPE_SCENE = """
query($src: ScraperSourceInput!, $in: ScrapeSingleSceneInput!) {
  scrapeSingleScene(source: $src, input: $in) {
    title date details urls image
    studio { name stored_id parent { name stored_id } }
    performers { name stored_id }
    tags { name stored_id }
  }
}"""


def _normalise(hit: dict) -> dict:
    # Une source peut ne rien renvoyer du tout : `None` traversait
    # jusqu'ici et levait une AttributeError.
    hit = hit or {}
    out = {}
    if not noyau.valeur_vide(hit.get("details")):
        out["bio"] = str(hit["details"])[:480]
    if not noyau.valeur_vide(hit.get("birthdate")):
        out["birthdate"] = hit["birthdate"]
    if not noyau.valeur_vide(hit.get("height")):
        out["height_cm"] = str(hit["height"])
    if not noyau.valeur_vide(hit.get("country")):
        out["country"] = hit["country"]
    if not noyau.valeur_vide(hit.get("ethnicity")):
        out["ethnicity"] = hit["ethnicity"]
    if not noyau.valeur_vide(hit.get("career_length")):
        out["years_active"] = str(hit["career_length"]).strip()
    if not noyau.valeur_vide(hit.get("measurements")):
        out["measurements"] = str(hit["measurements"]).strip()
    if not noyau.valeur_vide(hit.get("circumcised")):
        out["circumcised"] = str(hit["circumcised"]).strip()
    if hit.get("images"):
        out["images"] = list(hit["images"])[:1]   # hors scoring
    return out


def _match(hits, nom: str):
    exact = [h for h in hits or []
             if (h.get("name") or "").strip().lower()
             == nom.strip().lower()]
    return exact[0] if exact else None


def collecter_stash(ctx: Context, nom: str) -> tuple:
    """({source: {champ: valeur}}, [urls récoltées]) depuis
    stash-boxes + scrapers par-nom de Stash."""
    raw = {}
    urls = []
    if ctx.use_boxes():
        for box in ctx.stash_boxes:
            cle = (box["name"] or "").lower()
            try:
                d = ctx.stash.call_GQL(GQL_SCRAPE_SINGLE, {
                    "src": {"stash_box_endpoint": box["endpoint"]},
                    "in": {"query": nom}})
                hit = _match(d.get("scrapeSinglePerformer"), nom)
            except Exception as exc:
                log.debug(f"stash-box {cle} : {exc}")
                continue
            if hit:
                urls.extend(hit.get("urls") or [])
                data = _normalise(hit)
                if data:
                    raw[cle] = data
                    sources.SOURCE_WEIGHTS.setdefault(
                        cle, POIDS.get(cle, POIDS_DEFAUT))

    for scraper_id in ctx.scrapers():
        cle = scraper_id.lower()
        try:
            d = ctx.stash.call_GQL(GQL_SCRAPE_SINGLE, {
                "src": {"scraper_id": scraper_id},
                "in": {"query": nom}})
            hit = _match(d.get("scrapeSinglePerformer"), nom)
        except Exception as exc:
            log.debug(f"scraper {cle} : {exc}")
            continue
        if not hit:
            continue
        urls.extend(hit.get("urls") or [])
        data = _normalise(hit)
        if not data and (hit.get("urls") or [None])[0]:
            try:
                d = ctx.stash.call_GQL(GQL_SCRAPE_URL,
                                       {"url": hit["urls"][0]})
                data = _normalise(d.get("scrapePerformerURL") or {})
            except Exception:
                data = {}
        if data:
            raw[cle] = data
            sources.SOURCE_WEIGHTS.setdefault(
                cle, POIDS.get(cle, POIDS_DEFAUT))
    return raw, urls


def _url_normale(u: str) -> str:
    """Forme comparable d'une adresse.

    La barre finale était conservée : « /page » et « /page/ »
    paraissaient différentes, et un motif de scraper pouvait ne pas
    reconnaître une URL qui lui appartenait."""
    # Le passage en minuscules vient EN PREMIER : placé à la fin, il
    # laissait « HTTPS:// » intact, et une adresse écrite en
    # majuscules ne correspondait à aucun motif de scraper.
    return (str(u or "").lower().replace("\\", "")
            .replace("https://", "").replace("http://", "")
            .replace("www.", "").rstrip("/"))


def table_motifs(ctx: Context) -> dict:
    """{scraper_id: [motifs d'URL]} pour TOUS les scrapers performer
    installés (y compris ceux par-URL uniquement, comme EricVideos),
    hors exclusions. C'est ce qui permet la seconde passe : les URLs
    récoltées en passe nom sont routées vers ces scrapers.

    NB : list_performer_scrapers() de stashapi ne remonte pas le champ
    `urls` de chaque scraper — on interroge le GraphQL directement."""
    exclu = {x.strip().lower() for x in
             str(ctx.settings.get("scrapersExclude") or "")
             .split(",") if x.strip()}
    out = {}
    try:
        d = ctx.stash.call_GQL(
            "{ listScrapers(types:[PERFORMER]) { id performer { urls } } }")
        dispo = d.get("listScrapers") or []
    except Exception:
        return out
    for s in dispo:
        if s["id"].lower() in exclu:
            continue
        motifs = [_url_normale(m) for m in
                  ((s.get("performer") or {}).get("urls") or [])]
        if motifs:
            out[s["id"]] = motifs
    return out


def passe_url(ctx: Context, raw: dict, urls: list) -> None:
    """Seconde passe : scrape par URL des fiches découvertes en passe
    nom. Débloque les scrapers par-URL uniquement (EricVideos, BelAmi,
    CockyBoys…). Une URL max par scraper ; les scrapers ayant déjà
    répondu en passe nom sont sautés."""
    if not ctx.settings.get("useUrlPass", True):
        return
    motifs = table_motifs(ctx)
    vus = set(raw)                       # sources déjà entendues
    for url in dict.fromkeys(urls):      # dédoublonné, ordre conservé
        nu = _url_normale(url)
        scraper = next((sid for sid, ms in motifs.items()
                        if any(m in nu for m in ms)), None)
        if not scraper or scraper.lower() in vus:
            continue
        try:
            d = ctx.stash.call_GQL(GQL_SCRAPE_URL, {"url": url})
            data = _normalise(d.get("scrapePerformerURL") or {})
        except Exception as exc:
            log.debug(f"passe URL {scraper} : {exc}")
            continue
        if data:
            cle = scraper.lower()
            raw[cle] = data
            vus.add(cle)
            sources.SOURCE_WEIGHTS.setdefault(
                cle, POIDS.get(cle, POIDS_DEFAUT))
            log.info(f"    ↳ passe URL : {scraper} a répondu "
                     f"({', '.join(data)})")


def collecter_scene(ctx: Context, scene: dict) -> dict:
    """{source: données} via les stash-boxes, par EMPREINTE (phash) :
    Stash envoie les fingerprints de la scène, la stash-box répond si
    elle connaît le contenu — pas de recherche par nom, donc quasi
    aucun faux positif."""
    raw = {}
    for box in ctx.stash_boxes:
        cle = (box["name"] or "").lower()
        try:
            d = ctx.stash.call_GQL(GQL_SCRAPE_SCENE, {
                "src": {"stash_box_endpoint": box["endpoint"]},
                "in": {"scene_id": scene["id"]}})
            hits = d.get("scrapeSingleScene") or []
        except Exception as exc:
            log.debug(f"stash-box {cle} (scène) : {exc}")
            continue
        if not hits:
            continue
        h = hits[0]                    # match d'empreinte = fiable
        data = {}
        for champ in ("title", "date", "urls"):
            if h.get(champ):
                data[champ] = h[champ]
        if h.get("details"):
            data["details"] = str(h["details"])[:2000]
        if h.get("image"):
            data["image"] = h["image"]
        for champ in ("studio", "performers", "tags"):
            if h.get(champ):
                data[champ] = h[champ]
        if data:
            raw[cle] = data
            sources.SOURCE_WEIGHTS.setdefault(
                cle, POIDS.get(cle, POIDS_DEFAUT))
    return raw


def collecter_studio(ctx, nom: str) -> dict:
    """{source: données} : stash-boxes (via Stash, clés serveur) +
    Wikipedia en appoint (sans clé, désactivable)."""
    raw = {}
    if ctx.use_boxes():
        for box in ctx.stash_boxes:
            cle = (box["name"] or "").lower()
            try:
                d = ctx.stash.call_GQL(
                    """query($src: ScraperSourceInput!,
                             $in: ScrapeSingleStudioInput!) {
                         scrapeSingleStudio(source: $src, input: $in) {
                           name url urls details aliases image
                           parent { name stored_id } } }""",
                    {"src": {"stash_box_endpoint": box["endpoint"]},
                     "in": {"query": nom}})
                hits = d.get("scrapeSingleStudio") or []
            except Exception as exc:
                log.debug(f"stash-box {cle} (studio) : {exc}")
                continue
            hit = next((h for h in hits
                        if _nettoie_studio(h.get("name") or "").lower()
                        == _nettoie_studio(nom).lower()), None)
            if not hit:
                continue
            data = {}
            if not noyau.valeur_vide(hit.get("url")):
                data["website"] = hit["url"]
            elif hit.get("urls"):
                data["website"] = hit["urls"][0]
            if not noyau.valeur_vide(hit.get("details")):
                data["bio"] = str(hit["details"])[:2000]
            if not noyau.valeur_vide(hit.get("aliases")):
                data["aliases"] = [a for a in hit["aliases"] if a]
            if not noyau.valeur_vide(hit.get("image")):
                data["image"] = hit["image"]
            if not noyau.valeur_vide(hit.get("parent")):
                data["parent"] = hit["parent"]
            if data:
                raw[cle] = data
                sources.SOURCE_WEIGHTS.setdefault(
                    cle, POIDS.get(cle, POIDS_DEFAUT))
    if ctx.use_appoint():
        fetcher = sources.STUDIO_SOURCES.get("wikipedia")
        if fetcher:
            try:
                d = fetcher(nom)
            except Exception:
                d = None
            if d:
                raw["wikipedia"] = d
    return raw


def stats_collection(ctx, fiche: dict) -> dict:
    """Partenaires, studios et tags les plus fréquents du performer
    dans LA collection (calculés depuis les scènes Stash — données
    réelles, pas des suppositions)."""
    try:
        d = ctx.stash.call_GQL(
            """query($ids: [ID!]!) {
                 findScenes(scene_filter: {performers:
                     {value: $ids, modifier: INCLUDES}},
                     filter: {per_page: -1}) {
                   scenes { studio { name }
                            tags { name }
                            performers { id name } } } }""",
            {"ids": [fiche["id"]]})
        scenes = d["findScenes"]["scenes"]
    except Exception:
        return {}
    from collections import Counter
    part, studios, tags = Counter(), Counter(), Counter()
    for s in scenes:
        for q in s.get("performers") or []:
            if str(q["id"]) != str(fiche["id"]):
                part[q["name"]] += 1
        if s.get("studio"):
            studios[s["studio"]["name"]] += 1
        for t in s.get("tags") or []:
            tags[t["name"]] += 1
    return {"scenes": len(scenes),
            "partenaires": part.most_common(5),
            "studios": studios.most_common(3),
            "tags": [t for t, _ in tags.most_common(6)]}


# =============================================================================
# Studios — bio multi-sources, hiérarchie, stats de collection
# =============================================================================

def stats_studio(ctx, studio_id) -> dict:
    """Ce que LA collection dit du studio : scènes, période couverte,
    acteurs récurrents, tags dominants (données Stash uniquement)."""
    try:
        d = ctx.stash.call_GQL(
            """query($ids: [ID!]!) {
                 findScenes(scene_filter: {studios:
                     {value: $ids, modifier: INCLUDES}},
                     filter: {per_page: -1}) {
                   scenes { date
                            performers { name }
                            tags { name } } } }""",
            {"ids": [studio_id]})
        scenes = d["findScenes"]["scenes"]
    except Exception:
        return {}
    if not scenes:
        return {"scenes": 0}
    from collections import Counter
    perfs, tags = Counter(), Counter()
    annees = []
    for s in scenes:
        if s.get("date"):
            annees.append(s["date"][:4])
        for q in s.get("performers") or []:
            perfs[q["name"]] += 1
        for t in s.get("tags") or []:
            if not t["name"].startswith("Gaizer"):
                tags[t["name"]] += 1
    return {"scenes": len(scenes),
            "periode": (f"{min(annees)}-{max(annees)}"
                        if annees else None),
            "acteurs": [n for n, _ in perfs.most_common(5)],
            "tags": [n for n, _ in tags.most_common(5)]}


def _index_referentiel(ctx) -> tuple:
    """Index {nom/alias → id} des performers et studios du référentiel,
    pour rapprocher ce que les stash-boxes renvoient sans stored_id
    (correspondance insensible à la casse + forme alphanumérique)."""
    if getattr(ctx, "_idx", None):
        return ctx._idx

    def cles(nom):
        bas = (nom or "").strip().lower()
        return {bas, re.sub(r"[^a-z0-9]", "", bas)} - {""}

    perfs, studios = {}, {}
    try:
        for p in ctx.stash.find_performers():
            for k in cles(p["name"]) | {c for a in
                                        (p.get("alias_list") or [])
                                        for c in cles(a)}:
                perfs.setdefault(k, str(p["id"]))
        d = ctx.stash.call_GQL(
            "{ findStudios(filter:{per_page:-1}) "
            "{ studios { id name aliases } } }")
        for st in d["findStudios"]["studios"]:
            for k in cles(st["name"]) | {c for a in
                                         (st.get("aliases") or [])
                                         for c in cles(a)}:
                studios.setdefault(k, str(st["id"]))
    except Exception as exc:
        log.debug(f"index référentiel : {exc}")
    ctx._idx = (perfs, studios)
    return ctx._idx


def _resoudre(nom: str, stored_id, index: dict):
    if stored_id:
        return str(stored_id)
    bas = (nom or "").strip().lower()
    return (index.get(bas)
            or index.get(re.sub(r"[^a-z0-9]", "", bas)))


def _nettoie_studio(nom: str) -> str:
    """'Men.com (Network)' → 'Men.com' — les suffixes de plateforme des
    stash-boxes empêchent le rapprochement avec le référentiel."""
    return re.sub(r"\s*\((network|gay|straight|channel)\)\s*$", "",
                  nom or "", flags=re.I).strip()
