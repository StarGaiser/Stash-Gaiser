# -*- coding: utf-8 -*-
"""
Scrapers manquants : repérer ce que la médiathèque réclame.

Stash sait installer des scrapers depuis un catalogue, mais c'est à
l'utilisateur de deviner lesquels lui serviraient. Or l'information est
dans sa collection : les studios présents et les sites cités par les
fiches disent exactement de quoi il a besoin.

DEUX CHOSES SÉPARÉES, et la distinction est le cœur de ce module.

La **détection** est automatique et sans risque : elle lit, compare,
et rapporte. Elle se lance au bout de l'enrichissement des scènes et
des studios — le seul moment où la liste des studios est complète,
puisque ce sont ces tâches qui créent ceux qui manquaient.

L'**installation** ne l'est pas. Un scraper est du code tiers qui
s'exécutera sur la machine de l'utilisateur et interrogera des sites en
son nom. Rien ne s'installe sans une demande explicite, ou sans un
réglage qu'il aura activé en connaissance de cause.

Le rapprochement est EXACT sur forme normalisée, jamais approximatif.
Installer « BrazzersAPI » parce qu'un studio s'appelle « Brazil » serait
pire que ne rien installer : le scraper répondrait, avec des données
qui ne concernent personne.
"""

from __future__ import annotations

import re
from datetime import date as _date_auj
from urllib.parse import urlparse

from stashapi import log

import noyau
from noyau import etat_ecrire, etat_lire

SOURCE_DEFAUT = ("https://stashapp.github.io/CommunityScrapers/"
                 "stable/index.yml")


def _cle(texte) -> str:
    """Forme normalisée : « Say Uncle », « SayUncle » et « say-uncle »
    désignent la même chose."""
    return re.sub(r"[^a-z0-9]", "", str(texte or "").lower())


def _rapprocher(nom, catalogue):
    """Paquet correspondant à un nom, ou None.

    Aucune approximation : seule l'égalité des formes normalisées
    compte. Un rapprochement partiel installerait un scraper qui
    répondrait à côté."""
    cle = _cle(nom)
    if not cle or len(cle) < 3:
        return None
    for p in catalogue or []:
        if _cle(p.get("package_id")) == cle or _cle(p.get("name")) == cle:
            return p
    return None


def _rapprocher_url(url, catalogue):
    """Paquet correspondant au domaine d'une URL.

    Les sources propres aux interprètes — OnlyFans, JustFor.Fans — ne
    portent pas de nom de studio : elles se déduisent des adresses
    citées sur les fiches."""
    try:
        hote = urlparse(str(url or "")).hostname or ""
    except (ValueError, AttributeError):
        return None
    if not hote:
        return None
    hote = re.sub(r"^www\.", "", hote.lower())
    # « onlyfans.com » → « onlyfans » ; le domaine de tête ne dit rien.
    parties = hote.split(".")
    for candidat in (hote, ".".join(parties[:-1]) if len(parties) > 1
                     else hote):
        trouve = _rapprocher(candidat, catalogue)
        if trouve:
            return trouve
    return None


def source_sure(url) -> bool:
    """La source d'où du CODE sera installé mérite un contrôle propre.

    Deux exigences au-delà de celles du contrôle d'URL général. Le
    chiffrement est obligatoire : un catalogue servi en clair peut être
    remplacé en chemin, et le code installé ne serait pas celui
    annoncé. Et l'adresse doit être publique : installer depuis le
    réseau local reviendrait à exécuter ce que quiconque s'y trouve y
    aurait déposé."""
    texte = str(url or "").strip()
    if not texte.lower().startswith("https://"):
        return False
    return noyau.url_sure(texte)


def _source(ctx) -> str:
    """Source configurée, ou celle par défaut si elle ne convient pas.

    Retomber sur une source connue vaut mieux qu'échouer : une
    installation refusée laisserait l'utilisateur sans explication,
    tandis qu'un réglage douteux doit être écarté sans bruit — mais
    signalé."""
    voulue = str(ctx.settings.get("scraperSource") or "").strip()
    if not voulue:
        return SOURCE_DEFAUT
    if not source_sure(voulue):
        log.warning(f"catalogue « {voulue[:60]} » écarté : une source "
                    f"de code doit être en https et publique. "
                    f"Catalogue officiel employé à la place.")
        return SOURCE_DEFAUT
    return voulue


def _catalogue(ctx) -> list:
    """Paquets disponibles à la source configurée."""
    source = _source(ctx)
    d = ctx.stash.call_GQL(
        """query($src: String!) {
             availablePackages(type: Scraper, source: $src) {
               package_id name } }""",
        {"src": source})
    return d["availablePackages"] or []


def _installes(ctx) -> set:
    d = ctx.stash.call_GQL(
        "{ installedPackages(type: Scraper) { package_id } }")
    return {p["package_id"] for p in d["installedPackages"] or []}


def _installer(ctx, ids):
    source = _source(ctx)
    ctx.stash.call_GQL(
        """mutation($p: [PackageSpecInput!]!) {
             installPackages(type: Scraper, packages: $p) }""",
        {"p": [{"id": i, "sourceURL": source} for i in ids]})


def detecter(ctx) -> list:
    """[{package_id, name, motif}] — scrapers utiles et non installés.

    Une défaillance du catalogue, qui est distant, ne doit pas
    interrompre l'enrichissement au bout duquel cette détection se
    greffe : l'absence de proposition est un moindre mal."""
    try:
        catalogue = _catalogue(ctx)
        deja = _installes(ctx)
    except Exception as exc:
        log.debug(f"catalogue de scrapers indisponible : {exc}")
        return []
    if not catalogue:
        return []

    trouves = {}

    def retenir(paquet, motif):
        pid = paquet["package_id"]
        if pid in deja or pid in trouves:
            return
        trouves[pid] = {"package_id": pid,
                        "name": paquet.get("name") or pid,
                        "motif": motif}

    try:
        d = ctx.stash.call_GQL(
            """{ findStudios(filter: {per_page: -1}) {
                 studios { name aliases } } }""")
        for st in d["findStudios"]["studios"]:
            al = st.get("aliases") or []
            if isinstance(al, str):
                al = [x.strip() for x in al.split(",")]
            for nom in [st.get("name")] + [a for a in al if a]:
                p = _rapprocher(nom, catalogue)
                if p:
                    retenir(p, f"studio « {st.get('name')} »")
                    break
    except Exception as exc:
        log.debug(f"lecture des studios : {exc}")

    try:
        for perf in ctx.stash.find_performers():
            for url in perf.get("urls") or []:
                p = _rapprocher_url(url, catalogue)
                if p:
                    retenir(p, f"fiche de « {perf.get('name')} »")
    except Exception as exc:
        log.debug(f"lecture des interprètes : {exc}")

    return list(trouves.values())


# ── Cadence ──────────────────────────────────────────────────────────
def _aujourd_hui() -> str:
    return _date_auj.today().isoformat()


def doit_verifier(ctx) -> bool:
    """Une fois par jour au plus.

    La détection se greffe à la fin de tâches qu'on relance souvent :
    sans limite, enrichir une fiche unique interrogerait le catalogue
    distant à chaque clic."""
    if str((getattr(ctx, "args", None) or {}).get("force") or ""):
        return True
    return etat_lire().get("scrapers_verifies") != _aujourd_hui()


def marquer_verifie(ctx):
    etat_ecrire({"scrapers_verifies": _aujourd_hui()})


# ── Tâche ────────────────────────────────────────────────────────────
def proposer_scrapers(ctx):
    """Signale les scrapers que la collection réclame, et les installe
    si c'est demandé.

    Arguments : `installer=1` pour installer, `force=1` pour passer
    outre la limite quotidienne."""
    manquants = detecter(ctx)
    marquer_verifie(ctx)
    if not manquants:
        log.info("Aucun scraper manquant : les studios de la "
                 "collection sont couverts, ou n'ont pas d'équivalent "
                 "au catalogue.")
        return

    log.info(f"═══ {len(manquants)} scraper(s) utiles et non installés "
             f"═══")
    for m in sorted(manquants, key=lambda x: x["package_id"]):
        log.info(f"  {m['package_id']:26s} {m['motif']}")

    demande = str((getattr(ctx, "args", None) or {})
                  .get("installer") or "").strip()
    auto = bool(ctx.settings.get("autoInstallScrapers"))
    if not demande and not auto:
        log.info("Rien n'a été installé. Un scraper est du code tiers "
                 "qui s'exécutera sur votre machine et interrogera des "
                 "sites en votre nom : l'installation reste un geste.")
        log.info("  Relancer avec l'argument « installer=1 », ou "
                 "activer le réglage « Installer les scrapers "
                 "manquants ».")
        return

    if ctx.simulation():
        log.info(f"SIMULATION : {len(manquants)} scraper(s) auraient "
                 f"été installés.")
        return

    ids = [m["package_id"] for m in manquants]
    try:
        _installer(ctx, ids)
    except Exception as exc:
        log.error(f"installation refusée : {str(exc)[:110]}")
        return
    log.info(f"{len(ids)} scraper(s) installés. Relancer "
             f"l'enrichissement pour en profiter : les scènes déjà "
             f"traitées ne le seront pas d'elles-mêmes.")
