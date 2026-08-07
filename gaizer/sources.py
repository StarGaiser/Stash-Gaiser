#!/usr/bin/env python3
"""
Sources d'enrichissement multi-origines + agrégation.

Chaque source est un *fetcher* qui retourne des champs NORMALISÉS pour
une entité (acteur, studio, vidéo). L'agrégateur croise ensuite les
valeurs de toutes les sources et de la base :

- valeurs CONVERGENTES → un seul candidat, confiance renforcée ;
- valeurs DIVERGENTES (entre sources, ou avec la valeur déjà en base)
  → un candidat PAR valeur, chacun avec sa note de fiabilité et une
  justification lisible.

Sources implémentées :
    tpdb       ThePornDB (API REST, token TPDB_API_KEY)          0.80
    stashdb    StashDB (API GraphQL, clé STASHDB_API_KEY)        0.85
    wikipedia  API REST summary + infobox (sans clé)             0.70
    ade        Adult DVD Empire (scraping HTML, sans clé)        0.50
    ffprobe    lecture locale du fichier vidéo (qualité réelle)  1.00

GEVI a été évalué et écarté (2026-07-10) : le site n'offre plus de
recherche interne (déléguée à Google), aucune navigation exploitable.

Aucune clé n'est requise pour fonctionner : les sources sans clé sont
simplement ignorées. Les clés vivent dans config/.env
(TPDB_API_KEY, STASHDB_API_KEY) — voir l'interface web /config.
"""

from __future__ import annotations

import re

import noyau
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import os

TIMEOUT_S = 12
USER_AGENT = "Mediatheque-perso/1.0"

# Pondération de base par source (0..1) — la confiance d'un candidat
# part de là, puis est renforcée par le consensus.
SOURCE_WEIGHTS = {
    "ffprobe": 1.0,
    "stashdb": 0.85,
    "tpdb": 0.80,
    "wikipedia": 0.70,
    "ade": 0.50,
    "base": 0.60,       # valeur déjà présente en base / référentiel
    "llm": 0.75,
}

# Confiance maximale d'un candidat multi-sources (jamais 1.0 : l'humain
# reste le juge).


#
# ==============================================================================
# Outils communs
#
# ==============================================================================

def _get(url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None):
    """GET JSON ou texte, sans lever (None en cas d'échec)."""
    import requests
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT,
                                       **(headers or {})},
                         params=params, timeout=TIMEOUT_S)
        if r.status_code != 200:
            return None
        return r
    except Exception:
        return None


def _api_key(env_var: str) -> str:
    return os.environ.get(env_var, "").strip()


def normalize(field_name: str, value) -> Optional[str]:
    """Forme canonique d'une valeur pour COMPARER les sources entre
    elles. Retourne None si la valeur est vide/inutilisable."""
    # Une date nulle, une chaîne d'espaces : la même notion que
    # partout ailleurs dans le plugin, définie une seule fois.
    if noyau.valeur_vide(value):
        return None
    text = str(value).strip()
    if field_name == "year":
        m = re.search(r"(19|20)\d{2}", text)
        return m.group(0) if m else None
    if field_name == "website":
        text = text.lower().rstrip("/")
        text = re.sub(r"^https?://", "", text)
        text = re.sub(r"^www\.", "", text)
        return text
    if field_name in ("quality",):
        m = re.search(r"(\d{3,4})p", text.lower())
        return m.group(0) if m else text.lower()
    # Comparaison texte générale : casse/espaces neutralisés
    return re.sub(r"\s+", " ", text).casefold()


#
# ==============================================================================
# ThePornDB — API REST (https://api.theporndb.net)
#
# ==============================================================================

_TPDB_BASE = "https://api.theporndb.net"


def _tpdb_headers() -> Optional[Dict]:
    key = _api_key("TPDB_API_KEY")
    if not key:
        return None
    return {"Authorization": f"Bearer {key}", "Accept": "application/json"}


def fetch_tpdb_actor(name: str) -> Optional[Dict]:
    """Performer TPDB → bio, mensurations (si présentes), carrière."""
    headers = _tpdb_headers()
    if not headers:
        return None
    r = _get(f"{_TPDB_BASE}/performers", headers=headers,
             params={"q": name, "per_page": 3})
    if not r:
        return None
    try:
        hits = r.json().get("data") or []
    except ValueError:
        return None
    hit = _best_name_match(hits, name)
    if not hit:
        return None
    extras = hit.get("extras") or {}
    out = {}
    if hit.get("bio"):
        out["bio"] = str(hit["bio"])[:480]
    if extras.get("measurements"):
        out["mensurations"] = str(extras["measurements"])[:40]
    debut, fin = extras.get("career_start_year"), extras.get("career_end_year")
    if debut:
        out["years_active"] = (f"{debut}-{fin}" if fin
                               else f"{debut}-présent")
    return out or None


def fetch_tpdb_studio(name: str) -> Optional[Dict]:
    """Site/studio TPDB → description, url."""
    headers = _tpdb_headers()
    if not headers:
        return None
    r = _get(f"{_TPDB_BASE}/sites", headers=headers,
             params={"q": name, "per_page": 3})
    if not r:
        return None
    try:
        hits = r.json().get("data") or []
    except ValueError:
        return None
    hit = _best_name_match(hits, name)
    if not hit:
        return None
    out = {}
    if hit.get("description"):
        out["bio"] = str(hit["description"])[:480]
    if hit.get("url"):
        out["website"] = str(hit["url"])[:200]
    return out or None


#
# ==============================================================================
# StashDB — API GraphQL (https://stashdb.org/graphql)
#
# ==============================================================================

_STASHDB_URL = "https://stashdb.org/graphql"


def _stashdb_post(query: str, variables: Dict) -> Optional[Dict]:
    import requests
    key = _api_key("STASHDB_API_KEY")
    if not key:
        return None
    try:
        r = requests.post(_STASHDB_URL,
                          headers={"ApiKey": key,
                                   "User-Agent": USER_AGENT,
                                   "Content-Type": "application/json"},
                          json={"query": query, "variables": variables},
                          timeout=TIMEOUT_S)
        if r.status_code != 200:
            return None
        return r.json().get("data")
    except Exception:
        return None


def fetch_stashdb_actor(name: str) -> Optional[Dict]:
    """Performer StashDB → années de carrière uniquement.

    StashDB expose `height` (taille en cm), mais la base stocke des
    mensurations complètes ('185cm / 88kg') : proposer '183 cm' à la
    place ÉCRASERAIT le poids. La taille seule n'est donc pas remontée
    comme proposition — elle sert au contrôle de cohérence
    (tools/audit_base_vs_sources.py), pas à l'écriture.
    """
    data = _stashdb_post(
        """query($term: String!) {
             searchPerformer(term: $term, limit: 3) {
               name aliases career_start_year career_end_year height
             }
           }""", {"term": name})
    if not data:
        return None
    hits = data.get("searchPerformer") or []
    hit = _best_name_match(hits, name)
    if not hit:
        return None
    out = {}
    debut, fin = hit.get("career_start_year"), hit.get("career_end_year")
    if debut:
        out["years_active"] = (f"{debut}-{fin}" if fin
                               else f"{debut}-présent")
    return out or None


def fetch_stashdb_studio(name: str) -> Optional[Dict]:
    """Studio StashDB → url officielle."""
    data = _stashdb_post(
        """query($term: String!) {
             searchStudio(term: $term, limit: 3) {
               name urls { url type }
             }
           }""", {"term": name})
    if not data:
        return None
    hits = data.get("searchStudio") or []
    hit = _best_name_match(hits, name)
    if not hit:
        return None
    out = {}
    for u in hit.get("urls") or []:
        if (u.get("type") or "").upper() == "HOME" and u.get("url"):
            out["website"] = u["url"][:200]
            break
    return out or None


#
# ==============================================================================
# Wikipedia — API REST summary + infobox (sans clé)
#
# ==============================================================================

def fetch_wikipedia_entity(name: str) -> Optional[Dict]:
    """Résumé (bio) via l'API REST + infobox (website/founded/
    years_active) en complément. Fonctionne pour acteurs ET studios."""
    titre = name.strip().replace(" ", "_")
    out = {}
    r = _get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{titre}")
    if r:
        try:
            data = r.json()
            if data.get("type") == "standard" and data.get("extract"):
                out["bio"] = str(data["extract"])[:480]
        except ValueError:
            pass
    # Infobox pour les champs structurés
    r = _get(f"https://en.wikipedia.org/wiki/{titre}")
    if r:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            box = soup.find("table", {"class": "infobox"})
            if box:
                infos = {}
                for tr in box.find_all("tr"):
                    if tr.th and tr.td:
                        infos[tr.th.get_text().strip()] = \
                            tr.td.get_text().strip()
                if "Website" in infos:
                    out["website"] = infos["Website"][:200]
                if "Founded" in infos:
                    out["founded"] = infos["Founded"][:100]
                if "Years active" in infos:
                    out["years_active"] = infos["Years active"][:60]
        except Exception:
            pass
    return out or None


#
# ==============================================================================
# Adult DVD Empire — scraping HTML (repris de l'agent v2)
#
# ==============================================================================

def fetch_ade_actor(name: str) -> Optional[Dict]:
    r = _get("https://www.adultdvdempire.com/"
             + name.replace(" ", "-").lower(),
             headers={"User-Agent": "Mozilla/5.0"})
    if not r:
        return None
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        out = {}
        bio = soup.find("div", class_="bio")
        if bio:
            out["bio"] = bio.get_text().strip()[:480]
        m = soup.find("span", string="Measurements:")
        if m:
            nxt = m.find_next("span")
            if nxt:
                out["mensurations"] = nxt.get_text().strip()[:40]
        return out or None
    except Exception:
        return None


#
# ==============================================================================
# ffprobe — lecture locale (qualité réelle, fiabilité maximale)
#
# ==============================================================================


#
# ==============================================================================
# Correspondance de noms
#
# ==============================================================================

def _best_name_match(hits: List[Dict], wanted: str) -> Optional[Dict]:
    """Choisit le résultat dont le nom correspond le mieux (clé
    normalisée identique, sinon premier résultat si la recherche est
    déjà restrictive — jamais de correspondance farfelue)."""
    if not hits:
        return None
    cible = normalize("name", wanted)
    for hit in hits:
        if normalize("name", hit.get("name")) == cible:
            return hit
    # Tolérance : clé compacte identique (espaces/casse/accents)
    compact = re.sub(r"[^a-z0-9]", "", cible or "")
    for hit in hits:
        candidat = re.sub(r"[^a-z0-9]", "",
                          normalize("name", hit.get("name")) or "")
        if candidat and candidat == compact:
            return hit
    return None


#
# ==============================================================================
# Registres par entité
#
# ==============================================================================

ACTOR_SOURCES: Dict[str, Callable[[str], Optional[Dict]]] = {
    "tpdb": fetch_tpdb_actor,
    "stashdb": fetch_stashdb_actor,
    "wikipedia": fetch_wikipedia_entity,
    "ade": fetch_ade_actor,
}

STUDIO_SOURCES: Dict[str, Callable[[str], Optional[Dict]]] = {
    "tpdb": fetch_tpdb_studio,
    "stashdb": fetch_stashdb_studio,
    "wikipedia": fetch_wikipedia_entity,
}

# Les sources vidéo reçoivent un dict {"title","studio","filename","path"}

#
# ==============================================================================
# Agrégation : consensus / divergence → candidats annotés
#
# ==============================================================================

@dataclass
class Candidate:
    """Une valeur candidate pour un champ, avec sa provenance."""
    field: str
    value: str
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.5
    note: str = ""


