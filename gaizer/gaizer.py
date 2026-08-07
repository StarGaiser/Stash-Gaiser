#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gaizer — plugin Stash d'enrichissement multi-sources à validation
humaine.

PRINCIPE (v0.2) — réutiliser l'existant de Stash, pas le dupliquer :

1. Les SOURCES sont celles de Stash lui-même :
   - les stash-boxes configurées (Settings → Metadata Providers) :
     PornDB, StashDB… — leurs clés API sont lues côté serveur Stash,
     RIEN n'est ressaisi dans le plugin ;
   - les scrapers installés (IAFD, GEVI…), appelés un par un via
     l'API — ce que l'UI ne permet que manuellement, un à la fois ;
   - en appoint : Wikipedia et AdultDVDEmpire (aucun scraper Stash
     équivalent, aucune clé requise).
2. La VALEUR AJOUTÉE du plugin est l'agrégation : consensus entre
   sources → confiance renforcée ; divergence → chaque valeur devient
   une proposition distincte annotée (source, fiabilité).
3. La VALIDATION s'appuie sur les mécanismes natifs (tags + UI Stash) :
       Gaizer:proposal                           (marqueur)
       Gaizer:birthdate=1984-10-21 [stashdb 85%] (proposition)
       Gaizer:accept                             (ta décision)
   La tâche « Appliquer » écrit alors les valeurs et retire les tags.

Stash appelle ce script avec un JSON sur stdin :
    { "server_connection": {...}, "args": { "mode": "..." } }

ORGANISATION DU CODE — chaque module ne dépend que des précédents :

    noyau        contexte, réglages, état, sécurité
    similarite   comparaison de noms (logique pure)
    collecte     interrogation des sources
    ia           modèles de langage
    entites      écritures communes aux entités
    performers   scenes   studios   doublons   groupes
    taches_diagnostic   regarder sans rien changer
    taches_menage       retirer ce qui encombre
    taches_heritage     champs venus d'un autre outil
    taches_arbitrage    la seule famille qui écrase
    taches_maintenance  réparer l'installation

Ce fichier ne contient que le registre des tâches et le point
d'entrée appelé par Stash.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log

from noyau import Context, _reprise_opportuniste, _sauver_reglages
from performers import (
    apply_accepted,
    enrich_one_performer,
    enrich_performers,
    regenerate_biohot)
from scenes import (
    apply_accepted_scenes,
    apply_covers,
    enrich_one_scene,
    enrich_scenes)
from studios import (
    apply_accepted_studios,
    enrich_one_studio,
    enrich_studios)
from doublons import (
    dedoublonnage_complet,
    detect_duplicates,
    detect_duplicates_studios,
    merge_marked,
    merge_marked_studios)
from groupes import detect_groupes
from scrapers import proposer_scrapers
from vision import lire_vignettes
from taches_arbitrage import (
    apply_recommended,
    arbitrer_conflits,
    restore_marked,
)
from taches_diagnostic import (
    controler_heritage,
    etat_agent,
    inspecter_collecte,
    position_tags,
    rapport_run,
    rapport_tags,
    sante_sources,
)
from taches_heritage import (
    deduire_roles,
    marquer_roles_importes,
    normaliser_roles,
    ranger_champs_herites,
    retirer_champ_herite,
    retirer_non_confirme,
)
from taches_maintenance import (
    migrer_langue,
    noop,
    reprendre_ia,
    restaurer_reglages,
)
from taches_menage import (
    clear_proposals,
    purger_tags_exclus,
    retirer_pied_bio,
    suggerer_tags_exclus,
)


TASKS = {
    "enrich_performers": enrich_performers,
    "enrich_one_performer": enrich_one_performer,
    "enrich_scenes": enrich_scenes,
    "enrich_studios": enrich_studios,
    "apply_accepted": apply_accepted,
    "apply_accepted_scenes": apply_accepted_scenes,
    "apply_recommended": apply_recommended,
    "restore_marked": restore_marked,
    "detect_duplicates": detect_duplicates,
    "rapport_run": rapport_run,
    "arbitrer_conflits": arbitrer_conflits,
    "controler_heritage": controler_heritage,
    "ranger_champs_herites": ranger_champs_herites,
    "retirer_champ_herite": retirer_champ_herite,
    "retirer_non_confirme": retirer_non_confirme,
    "deduire_roles": deduire_roles,
    "inspecter_collecte": inspecter_collecte,
    "marquer_roles_importes": marquer_roles_importes,
    "normaliser_roles": normaliser_roles,
    "retirer_pied_bio": retirer_pied_bio,
    "proposer_scrapers": proposer_scrapers,
    "lire_vignettes": lire_vignettes,
    "rapport_tags": rapport_tags,
    "sante_sources": sante_sources,
    "suggerer_tags_exclus": suggerer_tags_exclus,
    "detect_groupes": detect_groupes,
    "purger_tags_exclus": purger_tags_exclus,
    "etat_agent": etat_agent,
    "restaurer_reglages": restaurer_reglages,
    "migrer_langue": migrer_langue,
    "noop": noop,
    "apply_covers": apply_covers,
    "dedoublonnage_complet": dedoublonnage_complet,
    "reprendre_ia": reprendre_ia,
    "regenerate_biohot": regenerate_biohot,
    "apply_accepted_studios": apply_accepted_studios,
    "enrich_one_studio": enrich_one_studio,
    "detect_duplicates_studios": detect_duplicates_studios,
    "merge_marked_studios": merge_marked_studios,
    "merge_marked": merge_marked,
    "enrich_one_scene": enrich_one_scene,
    "position_tags": position_tags,
    "clear_proposals": clear_proposals,
}


def main():
    ctx = Context()
    try:
        _sauver_reglages(ctx)
    except Exception as exc:
        log.debug(f"sauvegarde des réglages : {exc}")
    try:
        _reprise_opportuniste(ctx)
    except Exception as exc:
        log.debug(f"reprise opportuniste : {exc}")
    fn = TASKS.get(ctx.mode())
    if not fn:
        log.error(f"mode inconnu : {ctx.mode()!r}")
        print(json.dumps({"error": f"mode inconnu : {ctx.mode()}"}))
        return
    try:
        fn(ctx)
        print(json.dumps({"output": "ok"}))
    except Exception as exc:
        log.error(f"échec {ctx.mode()} : {exc}")
        print(json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    main()
