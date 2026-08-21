# -*- coding: utf-8 -*-
"""Détection et fusion des doublons, interprètes et
studios."""

from __future__ import annotations

import json
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
from noyau import _historique_maj, tag_id
from similarite import (
    _canonique_de,
    _score_doublon,
    _sim_cles,
    exemptions_de,
    paires_candidates)


# Ce qui distingue une famille de l'autre, et RIEN de plus. Le reste
# de la fusion est commun : le paramétrer plutôt que le recopier
# garantit qu'un correctif profite aux deux.
FAMILLES = {
    "performer": {
        "alias": "alias_list",
        "detruire": "mutation($id: ID!) { performerDestroy(input: {id: $id}) }",
        "ecrire": ("methode", "update_performer"),
        "champs": ("details", "birthdate", "country", "ethnicity",
                   "height_cm", "career_length", "measurements",
                   "circumcised"),
        "requete": """query($ids: [ID!]!) {
                 findScenes(scene_filter: {performers:
                     {value: $ids, modifier: INCLUDES}},
                     filter: {per_page: -1}) {
                   scenes { id performers { id } } } }""",
        "liste_scene": "performers",
        "champ_scene": "performer_ids",
    },
    "studio": {
        "alias": "aliases",
        "detruire": "mutation($id: ID!) { studioDestroy(input: {id: $id}) }",
        "ecrire": ("mutation",
                   "mutation($input: StudioUpdateInput!) "
                   "{ studioUpdate(input: $input) { id } }"),
        "champs": ("details", "url", "parent_id", "image_path"),
        "requete": """query($ids: [ID!]!) {
                 findScenes(scene_filter: {studios:
                     {value: $ids, modifier: INCLUDES}},
                     filter: {per_page: -1}) {
                   scenes { id } } }""",
        "liste_scene": None,
        "champ_scene": "studio_id",
    },
}


def _reassigner_scenes(ctx, genre: str, canonique: dict,
                       doublon: dict) -> int:
    """Fait pointer vers le canonique les scènes du doublon.

    Un interprète est une LISTE sur la scène, un studio un champ
    unique : c'est la seule différence, et elle est déclarée.
    """
    conf = FAMILLES[genre]
    # Les deux requêtes emploient la même variable : le filtre de
    # Stash attend une LISTE d'identifiants dans les deux cas, même
    # quand une scène n'a qu'un studio.
    variables = {"ids": [doublon["id"]]}
    d = ctx.stash.call_GQL(conf["requete"], variables)
    scenes = d["findScenes"]["scenes"]
    for sc in scenes:
        if conf["liste_scene"]:
            ids = {str(q["id"]) for q in sc[conf["liste_scene"]]}
            ids.discard(str(doublon["id"]))
            ids.add(str(canonique["id"]))
            valeur = list(ids)
        else:
            valeur = canonique["id"]
        ctx.stash.update_scene({"id": sc["id"],
                                conf["champ_scene"]: valeur})
    return len(scenes)


def _fusionner_entite(ctx, genre: str, canonique: dict,
                      doublon: dict) -> bool:
    """Fusionne le doublon DANS le canonique.

    Scènes réassignées, nom du doublon conservé en alias, champs
    vides repris, champs libres complétés, puis suppression.

    Une fusion N'EST PAS restaurable : la fiche est détruite, et
    l'historique du canonique en garde la seule trace.
    """
    conf = FAMILLES[genre]
    try:
        n_scenes = _reassigner_scenes(ctx, genre, canonique, doublon)

        maj = {"id": canonique["id"]}
        alias = list(dict.fromkeys(
            (canonique.get(conf["alias"]) or [])
            + [doublon["name"]] + (doublon.get(conf["alias"]) or [])))
        maj[conf["alias"]] = [
            a for a in alias
            if a and a.strip()
            and a.lower() != canonique["name"].lower()]

        for champ in conf["champs"]:
            if not canonique.get(champ) and doublon.get(champ):
                maj[champ] = doublon[champ]

        urls = list(dict.fromkeys((canonique.get("urls") or [])
                                  + (doublon.get("urls") or [])))
        if urls:
            maj["urls"] = urls

        cf_c = canonique.get("custom_fields") or {}
        cf_d = doublon.get("custom_fields") or {}
        cf = {k: v for k, v in cf_d.items()
              if v and not cf_c.get(k)
              and not k.startswith("enrich_")}
        cf["enrich_sources"] = ctx.t(
            "fusion_trace", nom=doublon["name"], id=doublon["id"],
            date=_date_auj.today().isoformat())
        cf["enrich_historique"] = _historique_maj(
            canonique, {"fusion": [doublon["name"],
                                   canonique["name"]]})
        maj["custom_fields"] = {"partial": cf}

        ctx.stash.call_GQL(conf["detruire"], {"id": doublon["id"]})
        # La bibliothèque expose « update_performer » comme
        # méthode, mais pas d'équivalent pour les studios : ceux-ci
        # passent par une mutation. C'est une donnée de l'outil, non
        # un choix.
        forme, appel = conf["ecrire"]
        if forme == "methode":
            getattr(ctx.stash, appel)(maj)
        else:
            ctx.stash.call_GQL(appel, {"input": maj})
        log.info(f"  ⨝ fusionné : {doublon['name']} → "
                 f"{canonique['name']} "
                 f"({n_scenes} scène(s) réassignée(s))")
        return True
    except Exception as exc:
        log.warning(f"fusion {doublon.get('name')} : {exc}")
        return False


def _fusionner(ctx, canonique: dict, doublon: dict) -> bool:
    """Fusionne deux interprètes."""
    return _fusionner_entite(ctx, "performer", canonique, doublon)


def _fusionner_studio(ctx, canonique: dict, doublon: dict) -> bool:
    """Fusionne deux studios."""
    return _fusionner_entite(ctx, "studio", canonique, doublon)


def detect_duplicates(ctx):
    """Signale les DOUBLONS PROBABLES parmi les performers — paires
    impliquant au moins une fiche créée par le plugin (:créé) : le
    référentiel curé n'est pas soupçonné entre lui-même.

    Tag posé des deux côtés : `Gaizer:doublon?` + jumeau nommé
    dans enrich_rapport. FAUSSE ALERTE : poser `Gaizer:pas-doublon`
    sur UNE des deux fiches puis relancer cette tâche — la paire est
    exemptée définitivement (enrich_pas_doublon des deux côtés) et les
    tags nettoyés. La tâche est idempotente : chaque exécution
    recalcule tout."""
    prefix = ctx.tag_prefix()
    t_doub = tag_id(ctx, ctx.tag_nom("duplicate"))
    t_faux = tag_id(ctx, ctx.tag_nom("not_duplicate"))
    nom_cree = ctx.tag_nom("created")
    perfs = ctx.stash.find_performers()
    par_id = {str(p["id"]): p for p in perfs}

    # Précalculs
    cles = {str(p["id"]): _sim_cles(p["name"]) for p in perfs}
    alias_plats = {str(p["id"]):
                   {_sim_cles(a)[0] for a in (p.get("alias_list") or [])}
                   for p in perfs}

    # 1. Paires candidates : au moins un des deux membres doit être
    #    une fiche créée par le plugin — le référentiel curé n'est pas
    #    soupçonné contre lui-même.
    crees = {str(p["id"]) for p in perfs
             if any(t["name"] == nom_cree for t in p.get("tags", []))}
    paires = paires_candidates(perfs, cles, alias_plats, exemptions_de,
                               restreindre_a=crees)

    # 2. Fausses alertes : consommer :pas-doublon → exemptions
    for p in perfs:
        if not any(t["name"] == ctx.tag_nom("not_duplicate")
                   for t in p.get("tags", [])):
            continue
        for cle in [c for c in list(paires) if str(p["id"]) in c]:
            a, b = paires.pop(cle)[:2]
            for x, autre in ((a, str(b["id"])), (b, str(a["id"]))):
                ex = exemptions_de(x) | {autre}
                val = json.dumps(sorted(ex))
                ctx.stash.update_performer({
                    "id": x["id"],
                    "custom_fields": {"partial": {
                        "enrich_pas_doublon": val}}})
                x.setdefault("custom_fields", {})[
                    "enrich_pas_doublon"] = val
            log.info(f"  fausse alerte exemptée : "
                     f"{a['name']} ≠ {b['name']}")

    # 3. Écarter les paires déjà exemptées
    actives = {cle: pq for cle, pq in paires.items()
               if cle[1] not in exemptions_de(pq[0])
               and cle[0] not in exemptions_de(pq[1])}

    # Fusion AUTOMATIQUE : alignée sur le workflow existant — modes
    # auto/seuil uniquement, note ≥ autoAcceptThreshold, et la fiche
    # supprimée est TOUJOURS une fiche :créé (le référentiel curé
    # n'est jamais détruit automatiquement).
    fusionnees = 0
    if (ctx.apply_mode() in ("auto", "seuil")
            and ctx.settings.get("autoMergeDuplicates", True)):
        seuil = ctx.auto_threshold()
        for cle in list(actives):
            p1, p2, note, motif = actives[cle]
            if note < seuil:
                continue
            canon, doub = _canonique_de(p1, p2, nom_cree)
            if not any(t["name"] == nom_cree
                       for t in doub.get("tags", [])):
                continue        # jamais détruire le référentiel
            if _fusionner(ctx, canon, doub):
                fusionnees += 1
                del actives[cle]
                par_id.pop(str(doub["id"]), None)
    if fusionnees:
        log.info(f"{fusionnees} doublon(s) fusionné(s) "
                 f"automatiquement (≥ {ctx.auto_threshold()}/10).")

    # 4. Pose/retrait idempotent des tags
    signales = {}
    for _cle, (p, q, note, motif) in actives.items():
        signales.setdefault(str(p["id"]), []).append((q, note, motif))
        signales.setdefault(str(q["id"]), []).append((p, note, motif))
    n_maj = 0
    for p in perfs:
        tids = {t["id"] for t in p.get("tags", [])}
        doit = str(p["id"]) in signales
        nouveaux = (tids - {t_doub, t_faux}) | ({t_doub} if doit
                                                else set())
        maj = {"id": p["id"]}
        if nouveaux != tids:
            maj["tag_ids"] = list(nouveaux)
        if doit:
            jum = "; ".join(
                f"{x['name']} (id {x['id']}, {nt}/10 — {mo})"
                for x, nt, mo in signales[str(p["id"])][:4])
            maj["custom_fields"] = {"partial": {"enrich_rapport":
                ctx.t("doublon_perf", jumeaux=jum,
                      tag=ctx.tag_nom("not_duplicate"))[:400]}}
        if len(maj) > 1:
            ctx.stash.update_performer(maj)
            n_maj += 1
    log.info(f"{len(actives)} paire(s) de doublons probables — "
             f"{n_maj} fiche(s) mise(s) à jour. Filtre par le tag "
             f"'{prefix}:doublon?'.")


def merge_marked(ctx):
    """Fusion MANUELLE : poser le tag `Gaizer:fusionner` sur la
    fiche à faire disparaître (son jumeau signalé devient canonique)
    puis lancer cette tâche. Ignore le seuil — c'est ta décision."""
    perfs = ctx.stash.find_performers()
    cles = {str(p["id"]): _sim_cles(p["name"]) for p in perfs}
    marques = [p for p in perfs
               if any(t["name"] == ctx.tag_nom("merge")
                      for t in p.get("tags", []))]
    n = 0
    for doub in marques:
        di = str(doub["id"])
        jumeau = None
        meilleur = 0
        for q in perfs:
            qi = str(q["id"])
            if qi == di:
                continue
            note, _m = _score_doublon(cles[di], cles[qi])
            if note > meilleur:
                meilleur, jumeau = note, q
        if not jumeau:
            log.warning(f"  {doub['name']} : aucun jumeau détecté — "
                        f"fusion refusée")
            continue
        if _fusionner(ctx, jumeau, doub):
            n += 1
    log.info(f"{n} fusion(s) manuelle(s) effectuée(s).")


def detect_duplicates_studios(ctx):
    """Doublons de STUDIOS : mêmes notes et même workflow que les
    performers. Fusion automatique en modes auto/seuil au-delà du
    seuil (le studio détruit est toujours une fiche créée par le
    plugin) ; sinon signalement dans enrich_rapport. Fausse alerte :
    bouton « Pas un doublon » de l'interface (custom_field
    enrich_pas_doublon), exemption définitive."""
    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name details url aliases custom_fields
             parent_studio { id } } } }""")
    studios = d["findStudios"]["studios"]
    cles = {str(x["id"]): _sim_cles(x["name"]) for x in studios}
    alias_plats = {str(x["id"]):
                   {_sim_cles(a)[0] for a in (x.get("aliases") or [])}
                   for x in studios}

    def cfd(x, k, defaut=""):
        return str((x.get("custom_fields") or {}).get(k) or defaut)

    # Fausses alertes signalées par l'interface → exemptions durables
    for x in studios:
        if not cfd(x, "enrich_pas_doublon_demande").strip():
            continue
        cible = cfd(x, "enrich_pas_doublon_demande").strip()
        for a, b in ((x, cible),
                     (next((y for y in studios
                            if str(y["id"]) == cible), None),
                      str(x["id"]))):
            if not a:
                continue
            ex = exemptions_de(a) | {b}
            ctx.stash.call_GQL(
                "mutation($input: StudioUpdateInput!) "
                "{ studioUpdate(input: $input) { id } }",
                {"input": {"id": a["id"], "custom_fields": {"partial": {
                    "enrich_pas_doublon": json.dumps(sorted(ex)),
                    "enrich_pas_doublon_demande": "",
                    "enrich_rapport": ""}}}})
            a.setdefault("custom_fields", {})["enrich_pas_doublon"] = \
                json.dumps(sorted(ex))
        log.info(f"  fausse alerte exemptée : {x['name']} ≠ id {cible}")

    paires = paires_candidates(studios, cles, alias_plats,
                               exemptions_de)

    fusionnes = 0
    if (ctx.apply_mode() in ("auto", "seuil")
            and ctx.settings.get("autoMergeDuplicates", True)):
        seuil = ctx.auto_threshold()
        for cle in list(paires):
            x, y, note, motif = paires[cle]
            if note < seuil:
                continue
            # Le studio détruit est celui CRÉÉ par le plugin ; à défaut
            # le moins renseigné. Jamais un studio du référentiel face
            # à un autre du référentiel.
            x_cree = bool(cfd(x, "enrich_cree"))
            y_cree = bool(cfd(y, "enrich_cree"))
            if x_cree == y_cree:
                continue
            canon, doub = (x, y) if y_cree else (y, x)
            if _fusionner_studio(ctx, canon, doub):
                fusionnes += 1
                del paires[cle]
    if fusionnes:
        log.info(f"{fusionnes} studio(s) doublon(s) fusionné(s) "
                 f"automatiquement (≥ {ctx.auto_threshold()}/10).")
    proteges = sum(1 for x, y, nt, _m in paires.values()
                   if nt >= ctx.auto_threshold())
    if proteges:
        log.info(f"{proteges} paire(s) au-dessus du seuil NON "
                 f"fusionnées : aucune des deux fiches n'a été créée "
                 f"par le plugin (le référentiel n'est jamais détruit "
                 f"automatiquement) — arbitrage manuel sur la fiche.")

    signales = {}
    for (xi, yi), (x, y, note, motif) in paires.items():
        signales.setdefault(xi, []).append((y, note, motif))
        signales.setdefault(yi, []).append((x, note, motif))
    for x in studios:
        xi = str(x["id"])
        if xi not in signales:
            continue
        jum = "; ".join(f"{z['name']} (id {z['id']}, {nt}/10 — {mo})"
                        for z, nt, mo in signales[xi][:4])
        ctx.stash.call_GQL(
            "mutation($input: StudioUpdateInput!) "
            "{ studioUpdate(input: $input) { id } }",
            {"input": {"id": x["id"], "custom_fields": {"partial": {
                "enrich_doublon_id": str(signales[xi][0][0]["id"]),
                "enrich_rapport": ctx.t("doublon_probable",
                                        jumeaux=jum)[:900]}}}})
    log.info(f"{len(paires)} paire(s) de studios en attente d'arbitrage.")


def merge_marked_studios(ctx):
    """Fusion MANUELLE de studios : le bouton « Fusionner » de
    l'interface pose le custom_field enrich_fusionner (id du jumeau
    canonique) sur le studio à faire disparaître."""
    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name details url aliases custom_fields
             parent_studio { id } } } }""")
    studios = d["findStudios"]["studios"]
    par_id = {str(x["id"]): x for x in studios}
    n = 0
    for x in studios:
        cible = str((x.get("custom_fields") or {}).get("enrich_fusionner")
                    or "").strip()
        canon = par_id.get(cible)
        if not canon:
            continue
        if _fusionner_studio(ctx, canon, x):
            n += 1
    log.info(f"{n} fusion(s) manuelle(s) de studios.")


def dedoublonnage_complet(ctx):
    """DÉDOUBLONNAGE de la base, performers et studios : fusionne les
    paires dont la note atteint le seuil fort (défaut 9.0), y compris
    entre fiches du référentiel — ce que les tâches de détection
    refusent de faire seules. Chaque fusion est journalisée. Les paires
    en dessous du seuil fort restent signalées pour arbitrage manuel.
    En mode simulation, rien n'est détruit : tout est listé."""
    try:
        fort = float(str(ctx.settings.get("strongMergeThreshold")
                         or 9.0).replace(",", "."))
    except (TypeError, ValueError):
        fort = 9.0
    nom_cree = ctx.tag_nom("created")
    log.info(f"Dédoublonnage complet — seuil fort {fort}/10 "
             + ("(SIMULATION)" if ctx.simulation() else ""))

    # ---- Performers ----
    perfs = ctx.stash.find_performers()
    cles = {str(x["id"]): _sim_cles(x["name"]) for x in perfs}
    alias_plats = {str(x["id"]):
                   {_sim_cles(a)[0] for a in (x.get("alias_list") or [])}
                   for x in perfs}

    paires = paires_candidates(perfs, cles, alias_plats,
                               exemptions_de, note_mini=fort)
    n_p = 0
    for (xi, yi), (x, y, note, motif) in paires.items():
        canon, doub = _canonique_de(x, y, nom_cree)
        log.info(f"  performer {note}/10 ({motif}) : "
                 f"« {doub['name']} » → « {canon['name']} »")
        if ctx.simulation():
            continue
        if _fusionner(ctx, canon, doub):
            n_p += 1

    # ---- Studios ----
    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name details url aliases custom_fields image_path
             scene_count parent_studio { id } } } }""")
    studios = d["findStudios"]["studios"]
    clesS = {str(x["id"]): _sim_cles(x["name"]) for x in studios}
    aliasS = {str(x["id"]):
              {_sim_cles(a)[0] for a in (x.get("aliases") or [])}
              for x in studios}
    def rang(z):
        """Le canonique est le studio le plus fourni en scènes ; à
        égalité, celui dont le nom est le plus lisible (avec
        espaces)."""
        return (z.get("scene_count") or 0, " " in z["name"],
                len(z["name"]))

    n_s = 0
    vus = set()
    for (xi, yi), (x, y, note, motif) in paires_candidates(
            studios, clesS, aliasS, exemptions_de,
            note_mini=fort).items():
        if xi in vus or yi in vus:
            continue
        canon, doub = ((x, y) if rang(x) >= rang(y) else (y, x))
        log.info(f"  studio {note}/10 ({motif}) : "
                 f"« {doub['name']} » ({doub.get('scene_count')} sc.)"
                 f" → « {canon['name']} » "
                 f"({canon.get('scene_count')} sc.)")
        if ctx.simulation():
            continue
        if _fusionner_studio(ctx, canon, doub):
            n_s += 1
            vus.add(str(doub["id"]))
    if ctx.simulation():
        log.info(f"SIMULATION : {len(paires)} performer(s) et les "
                 f"studios listés ci-dessus seraient fusionnés.")
    else:
        log.info(f"{n_p} performer(s) et {n_s} studio(s) fusionnés. "
                 f"Les paires sous {fort}/10 restent signalées pour "
                 f"arbitrage sur les fiches.")
