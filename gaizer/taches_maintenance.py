# -*- coding: utf-8 -*-
"""
Réparer l'installation elle-même.

Ces tâches ne touchent pas à la collection mais au plugin :
ses réglages, sa langue, ses générations interrompues.
"""

from __future__ import annotations
import sys
from datetime import date as _date_auj
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stashapi import log
import i18n
from noyau import (
    _LLM,
    _pause_llm_active,
    etat_ecrire,
    etat_lire)
from performers import regenerate_biohot


def _traduire_yaml(cible: str) -> tuple:
    """Réécrit gaizer.yml dans la langue voulue : noms et
    descriptions des tâches, libellés et descriptions des réglages.

    Le fichier est relu et réécrit par PyYAML : la STRUCTURE (modes,
    types, clés techniques) n'est jamais touchée, seuls les textes
    affichés changent. Un réglage ou une tâche absent des tables de
    traduction conserve son libellé actuel."""
    chemin = Path(__file__).resolve().parent / "gaizer.yml"
    try:
        import yaml as _yaml
        doc = _yaml.safe_load(chemin.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning(f"YAML illisible : {exc}")
        return 0, 0
    if not isinstance(doc, dict):
        return 0, 0

    n_t = 0
    for tache_def in doc.get("tasks") or []:
        mode = ((tache_def.get("defaultArgs") or {}).get("mode") or "")
        libelle = i18n.tache(mode, cible)
        if mode and libelle != mode:
            if tache_def.get("name") != libelle:
                tache_def["name"] = libelle
                n_t += 1
            desc = i18n.description(mode, cible)
            if desc:
                tache_def["description"] = desc

    n_r = 0
    for nom, champ in (doc.get("settings") or {}).items():
        if not isinstance(champ, dict):
            continue
        libelle = i18n.reglage(nom, cible)
        if libelle != nom and champ.get("displayName") != libelle:
            champ["displayName"] = libelle
            n_r += 1

    try:
        chemin.write_text(
            _yaml.safe_dump(doc, allow_unicode=True, sort_keys=False,
                            default_flow_style=False, width=78),
            encoding="utf-8")
    except Exception as exc:
        log.warning(f"YAML non réécrit : {exc}")
        return 0, 0
    return n_t, n_r


def restaurer_reglages(ctx):
    """Réécrit dans Stash les réglages sauvegardés, complétés par ceux
    actuellement en place (les valeurs présentes gagnent)."""
    e = etat_lire()
    sauve = e.get("reglages") or {}
    if not sauve:
        log.warning("aucune sauvegarde de réglages disponible.")
        return
    fusion = dict(sauve)
    # Les identifiants en place sont conservés ; ils ne figurent pas
    # dans la sauvegarde et ne peuvent donc pas être rétablis d'ici.
    fusion.update({k: v for k, v in (ctx.settings or {}).items()
                   if v not in (None, "")})
    manquants = [k for k in (e.get("reglages_secrets") or [])
                 if not (ctx.settings or {}).get(k)]
    try:
        ctx.stash.call_GQL(
            """mutation($id: ID!, $input: Map!) {
                 configurePlugin(plugin_id: $id, input: $input) }""",
            {"id": "gaizer", "input": fusion})
    except Exception as exc:
        log.error(f"restauration impossible : {str(exc)[:120]}")
        return
    ajoutes = sorted(set(fusion) - set(ctx.settings or {}))
    log.info(f"{len(fusion)} réglage(s) en place"
             + (f" — {len(ajoutes)} remis : {', '.join(ajoutes[:12])}"
                if ajoutes else " — rien ne manquait")
             + f" (sauvegarde du {e.get('reglages_le')})")
    if manquants:
        log.warning(f"à ressaisir à la main (jamais stockés) : "
                    f"{', '.join(manquants)}")


def reprendre_ia(ctx):
    """Reprise des générations : lève la pause si sa date est passée
    (ou de force avec l'argument forcer=1), puis relance les bios hot
    manquantes. Destinée à être appelée une fois par jour."""
    forcer = str(ctx.args.get("forcer") or "").strip() in ("1", "true",
                                                           "oui")
    e = etat_lire()
    jusqu = _pause_llm_active()
    if jusqu and not forcer:
        log.info(f"pause IA encore active jusqu'au {jusqu} "
                 f"({e.get('pause_motif')}) — rien à faire "
                 f"aujourd'hui.")
        return
    if e.get("pause_llm_jusqu"):
        etat_ecrire({"pause_llm_jusqu": "", "pause_motif": "",
                     "derniere_reprise": _date_auj.today().isoformat()})
        log.info("pause IA levée — reprise des générations.")
    else:
        etat_ecrire({"derniere_reprise": _date_auj.today().isoformat()})
    _LLM["averti_pause"] = False
    regenerate_biohot(ctx)


def migrer_langue(ctx):
    """Aligne l'installation sur la langue choisie (réglage language) :

    1. renomme les TAGS posés dans une autre langue vers la langue
       courante (fusion si le tag cible existe déjà) ;
    2. réécrit les noms de tâches d'gaizer.yml.

    Rien n'est perdu : un tag renommé conserve ses entités."""
    cible = ctx.lang()
    prefix = ctx.tag_prefix()
    ctx._tags_cache = {}      # les noms vont changer
    log.info(f"Bascule vers « {i18n.LANGUES[cible]['nom']} » ({cible})")

    # ---- 1. Tags ----
    tags = ctx.stash.find_tags(f={"name": {
        "value": f"^{prefix}:", "modifier": "MATCHES_REGEX"}})
    par_nom = {t["name"]: t for t in tags
               if t["name"].startswith(f"{prefix}:")}
    renommes = fusionnes = 0
    for cle in i18n.EN["tags"]:
        voulu = f"{prefix}:{i18n.tag(cle, cible)}"
        for variante in i18n.tous_les_tags(cle):
            actuel = f"{prefix}:{variante}"
            if actuel == voulu or actuel not in par_nom:
                continue
            src = par_nom[actuel]
            dst = par_nom.get(voulu)
            try:
                if dst:
                    ctx.stash.call_GQL(
                        """mutation($s: [ID!]!, $d: ID!) {
                             tagsMerge(input: {source: $s,
                                               destination: $d})
                             { id } }""",
                        {"s": [src["id"]], "d": dst["id"]})
                    fusionnes += 1
                    log.info(f"  {actuel} fusionné dans {voulu}")
                else:
                    ctx.stash.call_GQL(
                        """mutation($id: ID!, $n: String!) {
                             tagUpdate(input: {id: $id, name: $n})
                             { id } }""",
                        {"id": src["id"], "n": voulu})
                    par_nom[voulu] = src
                    renommes += 1
                    log.info(f"  {actuel} → {voulu}")
            except Exception as exc:
                log.warning(f"  {actuel} : {str(exc)[:80]}")
            par_nom.pop(actuel, None)
    log.info(f"  tags : {renommes} renommé(s), {fusionnes} fusionné(s)")

    # ---- 2. Libellés du YAML (tâches ET réglages) ----
    n_t, n_r = _traduire_yaml(cible)
    if n_t or n_r:
        log.info(f"  interface : {n_t} tâche(s) et {n_r} réglage(s) "
                 f"traduits — recharger les plugins "
                 f"(Settings → Plugins → Reload) pour les voir")
    else:
        log.info("  interface : déjà dans la bonne langue")
    log.info("Bascule terminée. Les boutons des fiches suivent "
             "automatiquement.")


def noop(ctx):
    """Point d'entrée technique au nom stable : les boutons injectés
    dans les pages appellent toujours cette tâche en précisant le mode
    voulu, ce qui rend l'interface indépendante de la langue."""
    log.info("aucun mode fourni")
