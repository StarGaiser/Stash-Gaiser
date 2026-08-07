# -*- coding: utf-8 -*-
"""Films en plusieurs parties : détection des séries,
rapprochement des écritures, constitution des groupes."""

from __future__ import annotations

import re
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
from noyau import _historique_maj


# Motifs de découpage en parties, du plus explicite au plus ambigu.
# Le mot-clé est OBLIGATOIRE : un simple nombre en fin de titre n'est
# pas un numéro de partie (« Men 2 » est un titre, pas une suite).
MOTIFS_PARTIE = [
    (r"^(.*?)[\s._\-]+(?:part|partie|pt)[\s._\-]*(\d{1,2})\b",
     "partie", 0.5),
    (r"^(.*?)[\s._\-]+(?:chapter|chapitre|ch)[\s._\-]*(\d{1,2})\b",
     "chapitre", 0.5),
    (r"^(.*?)[\s._\-]+(?:volume|vol)[\s._\-]*(\d{1,2})\b",
     "volume", 0.3),
    (r"^(.*?)[\s._\-]+(?:episode|ep)[\s._\-]*(\d{1,2})\b",
     "épisode", 0.3),
    (r"^(.*?)[\s._\-]+(\d{1,2})[\s._\-]*(?:of|sur)[\s._\-]*\d{1,2}\b",
     "n sur m", 0.4),
    (r"^(.*?)[\s._\-]+(?:scene|sc)[\s._\-]*(\d{1,2})\b",
     "scène", -0.5),
]


_PETITS_MOTS = {"a", "an", "and", "at", "by", "de", "du", "for",
                "in", "la", "le", "les", "of", "on", "or", "the",
                "to", "with"}


def _nom_serie_propre(nom: str, depuis_titre: bool) -> str:
    """Présente correctement un nom de série.

    Un titre officiel est repris tel quel. Un nom tiré d'un fichier
    subit le traitement d'usage : préfixe de classement retiré,
    séparateurs remplacés, capitales rétablies — sans toucher aux
    sigles déjà en majuscules (TIM, XXX)."""
    nom = (nom or "").strip()
    if depuis_titre:
        return nom
    nom = re.sub(r"^(gay|xxx)[\s._\-]+", "", nom, flags=re.I)
    mots = []
    for i, mot in enumerate(re.split(r"\s+", nom)):
        if not mot:
            continue
        if mot.isupper() and len(mot) > 1:
            mots.append(mot)                    # sigle : intact
        elif i and mot.lower() in _PETITS_MOTS:
            mots.append(mot.lower())
        else:
            mots.append(mot[:1].upper() + mot[1:])
    return " ".join(mots).strip() or nom


def _lire_partie(texte: str):
    """(nom de série, numéro, genre, bonus) ou None."""
    t = re.sub(r"\.(mp4|mkv|avi|wmv|mov|m4v)$", "", texte or "",
               flags=re.I)
    for motif, genre, bonus in MOTIFS_PARTIE:
        m = re.match(motif, t, re.I)
        if not m:
            continue
        serie = re.sub(r"[\s._\-]+", " ", m.group(1)).strip(" .,-_")
        if len(serie) < 3:
            continue
        return serie, int(m.group(2)), genre, bonus
    return None


def _note_serie(parties, meme_studio: bool, bonus: float) -> tuple:
    """Confiance /10 d'une série reconstituée et son motif.

    L'information ne vient d'aucune source : elle est déduite des
    titres. La note dit à quel point le faisceau d'indices tient."""
    nums = sorted(n for n, _sc in parties)
    note, motifs = 6.0 + bonus, []
    if len(parties) >= 3:
        note += 1.5
        motifs.append(f"{len(parties)} parties")
    elif len(parties) == 1:
        note -= 1.5
        motifs.append("une seule partie trouvée")
    if nums == list(range(1, len(nums) + 1)):
        note += 1.0
        motifs.append("numérotation continue depuis 1")
    elif len(nums) != len(set(nums)):
        note -= 1.0
        motifs.append("numéros en double")
    else:
        motifs.append(f"parties {nums}")
    if meme_studio:
        note += 1.0
        motifs.append("même studio")
    else:
        note -= 1.5
        motifs.append("studios différents")
    return round(max(0.0, min(10.0, note)), 1), ", ".join(motifs)


def _collecter_series(ctx, scenes):
    """{clé normalisée: {nom, parties, studios, dates}} — les scènes
    déjà rattachées à un groupe sont ignorées (rien n'est écrasé)."""
    series = {}
    for sc in scenes:
        if sc.get("groups"):
            continue
        titre = (sc.get("title") or "").strip()
        fichier = ((sc.get("files") or [{}])[0] or {}).get("basename")
        lu = _lire_partie(titre) or _lire_partie(fichier or "")
        if not lu:
            continue
        nom, num, genre, bonus = lu
        cle = re.sub(r"[^a-z0-9]", "", nom.lower())
        if not cle:
            continue
        depuis_titre = bool(titre and _lire_partie(titre))
        e = series.setdefault(cle, {"nom": _nom_serie_propre(
                                        nom, depuis_titre),
                                    "parties": [],
                                    "studios": set(), "dates": [],
                                    "genre": genre, "bonus": bonus,
                                    "depuis_titre": depuis_titre})
        e["parties"].append((num, sc))
        if sc.get("studio"):
            e["studios"].add(sc["studio"]["id"])
        if sc.get("date"):
            e["dates"].append(sc["date"])
    return series


def _cle_serie(nom: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (nom or "").lower())


def _meme_serie(court: str, long_: str) -> bool:
    """« Brazil Underground » et « Gay Treasure Island TIM Fuck Brazil
    Underground » désignent le même film : le second n'est que le
    premier précédé d'un préfixe de classement (langue, studio, label).

    Le titre se trouve en FIN de nom, jamais au début : on n'accepte
    donc qu'un rapprochement par suffixe. « Howl » et « Howl 2 » — où
    le court est un préfixe — restent deux films distincts."""
    if len(court) < 8 or court == long_:
        return False
    return long_.endswith(court)


def _fusionner_series(series: dict) -> int:
    """Réunit les séries qui n'en sont qu'une, écrite autrement.

    Le nom retenu est le PLUS COURT : le bruit se trouve en tête
    (« GAY - Treasure Island - TIM Fuck - »), le titre en queue."""
    cles = sorted(series, key=len)
    fusions = 0
    for i, court in enumerate(cles):
        if court not in series:
            continue
        for long_ in cles[i + 1:]:
            if long_ not in series or not _meme_serie(court, long_):
                continue
            a, b = series[court], series[long_]
            # Un même numéro des deux côtés = deux films distincts.
            nums_a = {n for n, _sc in a["parties"]}
            nums_b = {n for n, _sc in b["parties"]}
            if nums_a & nums_b:
                continue
            # Studios incompatibles = prudence.
            if a["studios"] and b["studios"] and not (a["studios"]
                                                      & b["studios"]):
                continue
            a["parties"].extend(b["parties"])
            a["studios"] |= b["studios"]
            a["dates"].extend(b["dates"])
            a["depuis_titre"] = a["depuis_titre"] or b["depuis_titre"]
            a["rapproche"] = a.get("rapproche", []) + [b["nom"]]
            del series[long_]
            fusions += 1
    return fusions


def _index_groupes(ctx) -> list:
    """Groupes existants, chargés une fois par exécution."""
    if getattr(ctx, "_groupes", None) is None:
        d = ctx.stash.call_GQL(
            """{ findGroups(filter: {per_page: -1}) { groups {
                 id name aliases } } }""")
        ctx._groupes = d["findGroups"]["groups"]
    return ctx._groupes


def _groupe_existant(ctx, nom: str):
    """Groupe déjà présent portant ce nom ou cet alias."""
    plat = _cle_serie(nom)
    proche = None
    for g in _index_groupes(ctx):
        noms = [g["name"]] + [a.strip() for a
                              in (g.get("aliases") or "").split(",")
                              if a.strip()]
        cles = [_cle_serie(n) for n in noms]
        if plat in cles:
            return g
        # Un groupe créé avant le rapprochement peut porter l'écriture
        # longue : on le retrouve quand même.
        if proche is None and any(_meme_serie(plat, c) or
                                  _meme_serie(c, plat) for c in cles):
            proche = g
    return proche


def _appliquer_serie(ctx, e: dict, note: float, motif: str) -> bool:
    """Crée ou retrouve le groupe et y rattache les parties."""
    nom = e["nom"]
    g = _groupe_existant(ctx, nom)
    if g:
        gid, cree = g["id"], False
        # Le groupe porte peut-être l'écriture longue d'avant le
        # rapprochement : on lui rend son titre, l'ancien nom restant
        # en alias pour ne rien perdre.
        if _cle_serie(g["name"]) != _cle_serie(nom) and \
                len(nom) < len(g["name"]):
            alias = [a.strip() for a in (g.get("aliases") or "")
                     .split(",") if a.strip()]
            if g["name"] not in alias:
                alias.append(g["name"])
            ctx.stash.call_GQL(
                """mutation($input: GroupUpdateInput!) {
                     groupUpdate(input: $input) { id } }""",
                {"input": {"id": gid, "name": nom,
                           "aliases": ", ".join(alias)}})
            log.info(f"  groupe renommé : « {g['name']} » → « {nom} » "
                     f"(ancien nom conservé en alias)")
    else:
        entree = {"name": nom}
        if len(e["studios"]) == 1:
            entree["studio_id"] = next(iter(e["studios"]))
        if e["dates"]:
            entree["date"] = min(e["dates"])
        entree["custom_fields"] = {
            "enrich_sources": (f"série reconstituée depuis les titres "
                               f"({e['genre']}) — {note}/10 : {motif} "
                               f"· {_date_auj.today().isoformat()}")}
        d = ctx.stash.call_GQL(
            """mutation($input: GroupCreateInput!) {
                 groupCreate(input: $input) { id } }""",
            {"input": entree})
        gid = (d.get("groupCreate") or {}).get("id")
        cree = True
    if not gid:
        return False
    for num, sc in sorted(e["parties"]):
        # Les rattachements existants sont conservés, mais celui-ci
        # REMPLACE un lien déjà posé vers le même groupe : sans cette
        # précaution, relancer la tâche empilait des doublons.
        liens = [{"group_id": g2["group"]["id"],
                  "scene_index": g2.get("scene_index")}
                 for g2 in (sc.get("groups") or [])
                 if str(g2["group"]["id"]) != str(gid)]
        liens.append({"group_id": gid, "scene_index": num})
        maj = {"id": sc["id"], "groups": liens,
               "custom_fields": {"partial": {
                   "enrich_historique": _historique_maj(
                       sc, {"groupe": ["", f"{nom} — {e['genre']} "
                                           f"{num}"]})}}}
        ctx.stash.update_scene(maj)
    log.info(f"  {'créé' if cree else 'complété'} : « {nom} » "
             f"({len(e['parties'])} partie(s), {note}/10 — {motif})")
    return True


def detect_groupes(ctx):
    """Reconstitue les films en plusieurs parties.

    Ni StashDB ni PornDB ne renseignent le groupe des scènes de cette
    collection : l'information est DÉDUITE des titres, à défaut des
    noms de fichiers. Chaque série reçoit donc une note de confiance,
    et les scènes déjà rattachées à un groupe ne sont pas touchées.

    Mode auto : les séries au-dessus du seuil sont créées. Mode manuel
    ou séries douteuses : rapport détaillé, rien n'est écrit."""
    seuil = ctx.auto_threshold()
    mini = 2
    try:
        mini = max(1, int(float(str(
            ctx.settings.get("groupMinScenes") or 2))))
    except (TypeError, ValueError):
        mini = 2
    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             id title date files { basename }
             studio { id name }
             groups { group { id name } scene_index } } } }""")
    scenes = d["findScenes"]["scenes"]
    series = _collecter_series(ctx, scenes)
    if not series:
        log.info("aucune série multi-parties repérée.")
        return
    n_rapp = _fusionner_series(series)
    if n_rapp:
        log.info(f"{n_rapp} série(s) écrite(s) de deux façons "
                 f"rapprochée(s).")

    retenues, ecartees = [], []
    for e in series.values():
        note, motif = _note_serie(e["parties"], len(e["studios"]) <= 1,
                                  e["bonus"])
        if not e["depuis_titre"]:
            note = round(max(0.0, note - 0.5), 1)
            motif += ", d'après le nom de fichier"
        if e.get("rapproche"):
            motif += (f", rapprochée de « "
                      f"{'; '.join(e['rapproche'])[:60]} »")
        # Une partie isolée n'est écartée que si aucun groupe
        # existant ne la réclame : sinon c'est le morceau manquant
        # d'une série déjà constituée.
        assez = len(e["parties"]) >= mini
        if not assez and _groupe_existant(ctx, e["nom"]):
            assez = True
            motif += ", complète un groupe existant"
            # Le rapprochement de nom est déjà exigeant (suffixe d'au
            # moins huit caractères, studio concordant) : qu'un groupe
            # réclame cette partie compense largement le fait qu'elle
            # soit seule de son écriture.
            note = round(min(10.0, note + 3.5), 1)
        (retenues if assez else ecartees).append((note, motif, e))

    retenues.sort(key=lambda x: -x[0])
    log.info(f"{len(retenues)} série(s) de {mini} parties ou plus, "
             f"{len(ecartees)} écartée(s) faute de parties.")
    auto = ctx.apply_mode() in ("auto", "seuil")
    faits = 0
    for note, motif, e in retenues:
        parties = ", ".join(str(n) for n, _sc in sorted(e["parties"]))
        if auto and note >= seuil:
            if _appliquer_serie(ctx, e, note, motif):
                faits += 1
        else:
            log.info(f"  ⏸ « {e['nom']} » — parties {parties} — "
                     f"{note}/10 : {motif}")
    if auto:
        log.info(f"{faits} groupe(s) constitué(s) au-dessus de "
                 f"{seuil}/10. Les autres sont listés ci-dessus.")
    else:
        log.info("Mode manuel : rien n'a été écrit. Passer en mode "
                 "auto, ou constituer les groupes à la main.")
    if ecartees:
        noms = ", ".join(f"{e['nom']} ({e['parties'][0][0]})"
                         for _n, _m, e in ecartees[:12])
        log.info(f"Écartées (une seule partie dans la collection — "
                 f"suite manquante ou faux positif) : {noms}")
