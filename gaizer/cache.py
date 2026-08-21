# -*- coding: utf-8 -*-
"""
Mémoire des réponses de sources.

Une collecte complète sur une fiche interroge une vingtaine de sources
et prend deux minutes. Relancer la même tâche recommence tout, alors
que ces réponses ne changent pas d'un jour à l'autre : un annuaire ne
révise pas une date de naissance entre deux passages.

Le coût n'est pas seulement le temps. Chaque interrogation sollicite un
service tiers gratuit, et le marteler pour obtenir la réponse qu'on a
déjà est un abus, pas une optimisation manquée.

**Une réponse mémorisée est indiscernable d'une réponse fraîche.** Le
cache garde la réponse telle quelle, sans la simplifier : la moindre
transformation fausserait l'arbitrage sans que rien ne le signale.

**Il ne masque rien durablement.** Les réponses périment, et les
échecs plus vite que les succès — une source réparée doit pouvoir
répondre à nouveau.

**Il ne peut pas interrompre une tâche.** Toute défaillance — dossier
inaccessible, fichier corrompu — dégrade vers une collecte normale.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from stashapi import log

DOSSIER = Path(__file__).resolve().parent / ".cache"

# Une réponse utile vaut plus longtemps qu'un silence : un annuaire ne
# révise pas une date de naissance, mais une source en panne peut être
# réparée demain.
JOURS_SUCCES = 30
JOURS_ECHEC = 2


def _maintenant() -> float:
    """Isolé pour que les tests puissent avancer l'horloge."""
    return time.time()


def duree_pour(reponse) -> int:
    """Combien de jours garder cette réponse."""
    return JOURS_ECHEC if not reponse else JOURS_SUCCES


def _chemin(source: str, genre: str, nom: str) -> Path | None:
    """Fichier où vit cette réponse.

    Le nom vient de sources tierces : il est réduit à une empreinte,
    jamais employé comme chemin. Un nom contenant « ../ » écrirait
    hors du cache — et un nom d'interprète peut contenir n'importe
    quoi.
    """
    cle = re.sub(r"\s+", " ", str(nom or "").strip().lower())
    if not cle:
        return None
    propre = re.sub(r"[^a-z0-9_-]", "", str(source or "")[:40]) or "x"
    empreinte = hashlib.sha256(
        f"{genre}\n{cle}".encode(), usedforsecurity=False).hexdigest()
    return DOSSIER / propre / f"{empreinte[:2]}" / f"{empreinte}.json"


def lire(source: str, genre: str, nom: str, jours: int | None = None):
    """Réponse mémorisée, ou None si absente ou périmée."""
    chemin = _chemin(source, genre, nom)
    if chemin is None:
        return None
    try:
        brut = json.loads(chemin.read_text(encoding="utf-8"))
        pose = float(brut["t"])
        reponse = brut["r"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    limite = duree_pour(reponse) if jours is None else jours
    if limite <= 0:
        return None
    if _maintenant() - pose > limite * 86400:
        return None
    return reponse


def poser(source: str, genre: str, nom: str, reponse) -> None:
    """Mémorise une réponse. Un échec d'écriture est sans conséquence
    — la prochaine collecte interrogera la source."""
    chemin = _chemin(source, genre, nom)
    if chemin is None:
        return
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(
            json.dumps({"t": _maintenant(), "r": reponse},
                       ensure_ascii=False),
            encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        log.debug(f"cache non écrit : {str(exc)[:70]}")


def poser_echec(source: str, genre: str, nom: str, motif: str) -> None:
    """Mémorise qu'une source a échoué, et pourquoi.

    Une source en panne coûte son délai d'attente à chaque fiche. Dix
    scrapers défaillants — navigateur absent, site fermé — font perdre
    une minute par interprète.

    La mémoire est brève : une panne est passagère par nature, et
    condamner une source pour un mois sur une coupure d'une minute
    serait pire que le mal.
    """
    poser(f"{source}#echec", genre, nom,
          {"motif": str(motif)[:120]})


def echec_recent(source: str, genre: str, nom: str):
    """Motif de l'échec récent, ou None."""
    d = lire(f"{source}#echec", genre, nom, JOURS_ECHEC)
    return (d or {}).get("motif") if d else None


def vider() -> int:
    """Retire tout. Rend le nombre d'entrées supprimées."""
    n = 0
    try:
        for f in DOSSIER.rglob("*.json"):
            f.unlink()
            n += 1
    except OSError as exc:
        log.debug(f"cache non vidé : {str(exc)[:70]}")
    return n


def nettoyer(jours: int = 90) -> int:
    """Retire les entrées trop anciennes pour servir encore."""
    n = 0
    try:
        for f in DOSSIER.rglob("*.json"):
            try:
                brut = json.loads(f.read_text(encoding="utf-8"))
                vieux = _maintenant() - float(brut["t"]) > jours * 86400
            except (OSError, ValueError, KeyError, TypeError):
                vieux = True      # illisible : sans valeur
            if vieux:
                f.unlink()
                n += 1
    except OSError as exc:
        log.debug(f"cache non nettoyé : {str(exc)[:70]}")
    return n


def statistiques() -> dict:
    """De quoi juger si le cache mérite sa place sur le disque."""
    entrees = octets = 0
    try:
        for f in DOSSIER.rglob("*.json"):
            entrees += 1
            octets += f.stat().st_size
    except OSError as exc:
        log.debug(f"cache illisible pour les statistiques : {str(exc)[:70]}")
    return {"entrees": entrees, "octets": octets}
