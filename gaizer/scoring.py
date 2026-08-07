# -*- coding: utf-8 -*-
"""
scoring.py — évaluation critique des sources pour Gaizer.

Trois idées :
1. FAMILLES : des sources apparentées (Men/Bromo = Aylo ; Falcon/HotHouse
   = Gamma…) ne comptent que pour UN vote — trois copies d'une même
   fiche ne sont pas trois confirmations.
2. MATRICE type de source × champ : un studio est partie prenante (bios
   marketing, rajeunissement, mensurations gonflées) mais fiable sur la
   carrière chez lui ; un annuaire éditorial (IAFD) est solide sur
   l'état civil.
3. DÉTECTEURS de biais directionnels : rajeunissement, exagération
   anatomique, incohérence carrière/naissance — annotés et pénalisés.

Chaque candidat reçoit une NOTE /10 et des commentaires ; le mieux noté
est marqué `recommande` (valeur par défaut pour la validation de masse
ou le mode automatique).

Configuration : DEFAUTS ci-dessous, surchargeable par gaizer_config.yml
posé à côté du plugin (fusion clé à clé).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────
# FIABILITÉS : ce qui est mesuré, ce qui est supposé.
#
# Les valeurs ci-dessous ont été confrontées aux faits sur un
# échantillon de 70 fiches (tools/mesurer_fiabilites.py). Deux
# enseignements ont conduit à les revoir :
#
# 1. LES SOURCES COMMERCIALES SONT BIEN PLUS FIABLES QUE SUPPOSÉ sur
#    les données factuelles. Un site de studio était crédité de 0,35
#    sur la taille ; il concorde en réalité avec les annuaires dans
#    71 à 78 % des cas. La méfiance de principe envers le commercial
#    ne se vérifie pas sur ce qui est vérifiable — elle reste fondée
#    sur les textes promotionnels, qui eux ne sont pas mesurables.
#
# 2. IL N'EXISTE PAS DE VÉRITÉ TERRAIN. Les deux annuaires de
#    référence, IAFD et GEVI, ne s'accordent qu'à 56 % sur la
#    nationalité, 66 % sur la date de naissance, 86 % sur la taille.
#    Aucun moteur ne peut donc dépasser nettement ces proportions :
#    l'écart résiduel n'est pas une erreur de sélection, c'est du
#    désaccord irréductible entre sources.
#
# Ces chiffres valent pour UNE collection. La commande
# `tools/mesurer_fiabilites.py` permet de les recalculer sur la
# sienne, et `gaizer_config.yml` de les remplacer.
# ─────────────────────────────────────────────────────────────────────

DEFAUTS = {
    # Sources apparentées : un seul vote par famille.
    "familles": {
        "aylo": ["men", "bromo", "milehighmedia_gay", "seancody",
                 "gaywire"],
        "gamma": ["falconstudios", "hothouse", "ragingstallion",
                  "nextdoorstudios"],
    },
    # Type de chaque source (non listée = "studio", défaut prudent).
    "types": {
        "editorial": ["iafd", "gevi"],
        "communautaire": ["stashdb.org", "porndb", "builtin_freeones",
                          "wikipedia"],
        "appoint": ["ade"],
    },
    # Fiabilité type × champ (0-1). "defaut" si champ absent.
    "fiabilite": {
        "editorial": {"birthdate": 0.90, "height_cm": 0.75,
                      "country": 0.85, "ethnicity": 0.80,
                      "years_active": 0.85, "bio": 0.75, "defaut": 0.75},
        # Mesuré : 89 % sur la date, 82 % sur la nationalité et la
        # taille, 81 % sur l'ethnicité (StashDB, 27 à 54 relevés).
        "communautaire": {"birthdate": 0.85, "height_cm": 0.80,
                          "country": 0.80, "ethnicity": 0.78,
                          "years_active": 0.85, "bio": 0.60,
                          "defaut": 0.70},
        # Revu à la HAUSSE d'après la mesure : 71 à 78 % de concordance
        # sur la taille (men, Falcon, HotHouse, Raging Stallion, 14 à
        # 23 relevés chacun) contre 0,35 supposé, 83 % sur la date.
        # La méfiance envers le commercial reste justifiée pour les
        # textes promotionnels — invérifiables — mais pas pour les
        # données factuelles, que ces sites reprennent correctement.
        "studio": {"birthdate": 0.70, "height_cm": 0.70,
                   "country": 0.60, "ethnicity": 0.55,
                   "years_active": 0.70, "bio": 0.30, "defaut": 0.50},
        "appoint": {"defaut": 0.50},
    },
    "detecteurs": {
        "date_tolerance_jours": 1,     # dates fusionnées si écart ≤ N j
        "taille_tolerance_cm": 2,      # tailles fusionnées si écart ≤ N cm
        "penalite_rajeunissement": 2.5,
        "penalite_exageration": 1.5,
        "penalite_incoherence": 3.0,
        "bonus_famille": 1.0,          # par famille indépendante en plus
        "bonus_max": 2.0,
    },
}


def charger_config(dossier_plugin: str) -> dict:
    """DEFAUTS fusionnés avec gaizer_config.yml s'il existe."""
    cfg = {k: (dict(v) if isinstance(v, dict) else v)
           for k, v in DEFAUTS.items()}
    for k in ("familles", "types", "fiabilite"):
        cfg[k] = {kk: (dict(vv) if isinstance(vv, dict) else list(vv))
                  for kk, vv in DEFAUTS[k].items()}
    chemin = Path(dossier_plugin) / "gaizer_config.yml"
    if not chemin.exists():
        return cfg
    try:
        import yaml
        perso = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    except Exception:
        return cfg
    for cle, val in perso.items():
        if isinstance(val, dict) and isinstance(cfg.get(cle), dict):
            cfg[cle].update(val)
        else:
            cfg[cle] = val
    return cfg


def famille_de(source: str, cfg: dict) -> str:
    s = source.lower()
    for fam, membres in cfg["familles"].items():
        if s in membres:
            return fam
    return s        # source indépendante = sa propre famille


def type_de(source: str, cfg: dict) -> str:
    s = source.lower()
    for typ, membres in cfg["types"].items():
        if s in membres:
            return typ
    return "studio"


def fiabilite(source: str, champ: str, cfg: dict) -> float:
    table = cfg["fiabilite"].get(type_de(source, cfg), {})
    return table.get(champ, table.get("defaut", 0.4))


def _date(v):
    """Date d'une source, ou None si elle n'a pas de sens.

    Les sources distantes envoient parfois « 0000-00-00 » ou
    « 1984-13-45 » : la forme est bonne, la date n'existe pas.
    Construire l'objet sans filet levait une exception qui
    interrompait l'enrichissement de toute la fiche."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(v).strip())
    if not m:
        return None
    try:
        return date(*map(int, m.groups()))
    except ValueError:
        return None


def _entier(v):
    """Entier d'une source, ou None. `float("inf")` levait une
    OverflowError à la conversion — une valeur qu'aucune mensuration
    ne justifie, mais qu'un flux JSON peut transporter."""
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError, OverflowError):
        return None


def _norme(champ: str, v) -> str:
    s = re.sub(r"\s+", " ", str(v).strip().lower())
    if champ == "years_active":
        s = re.sub(r"\s*-\s*(présent|present|now)?\s*$", " -", s)
    return s


def _proches(champ: str, a, b, cfg: dict) -> bool:
    d = cfg["detecteurs"]
    if champ == "birthdate":
        da, db = _date(a), _date(b)
        if da and db:
            return abs((da - db).days) <= d["date_tolerance_jours"]
    if champ == "height_cm":
        ia, ib = _entier(a), _entier(b)
        if ia and ib:
            return abs(ia - ib) <= d["taille_tolerance_cm"]
    return _norme(champ, a) == _norme(champ, b)


def _vide(v) -> bool:
    """Une source qui ne sait pas renvoie « », None, « unknown »… Ces
    non-réponses ne doivent pas concourir : proposer une valeur vide
    reviendrait à effacer un champ au nom d'une source."""
    if v is None:
        return True
    t = str(v).strip().lower()
    return t in ("", "none", "null", "n/a", "na", "unknown", "inconnu",
                 "-", "--", "0000-00-00")


def _clusters(champ: str, valeurs: dict, cfg: dict) -> list:
    """[{valeur, sources}] — valeurs proches fusionnées, représentant =
    valeur de la source la plus fiable du cluster."""
    out = []
    valeurs = {s: v for s, v in valeurs.items() if not _vide(v)}
    for src, val in valeurs.items():
        for c in out:
            if _proches(champ, val, c["brutes"][0][1], cfg):
                c["brutes"].append((src, val))
                break
        else:
            out.append({"brutes": [(src, val)]})
    for c in out:
        c["brutes"].sort(key=lambda sv: -fiabilite(sv[0], champ, cfg))
        c["valeur"] = c["brutes"][0][1]
        c["sources"] = sorted(s for s, _ in c["brutes"])
        del c["brutes"]
    return out

# ─────────────────────────────────────────────────────────────────────
# Détecteurs : ce qui corrige la note APRÈS le calcul général.
#
# Chacun connaît un travers PARTICULIER du métier, mesuré sur des
# données réelles, et n'agit que sur le champ concerné. Les tenir
# séparés permet d'en ajouter un sans relire les autres — et de lire
# celui qu'on soupçonne sans traverser les quatre.
#
# Tous suivent le même contrat : ils reçoivent les candidats, les
# réglages et le contexte, modifient les notes SUR PLACE, et
# expliquent chaque correction. Une note sans explication est
# inexploitable : l'utilisateur doit pouvoir juger l'arbitrage.
# ─────────────────────────────────────────────────────────────────────


def _detect_rajeunissement(cands, reglages, _contexte):
    """Une fiche promotionnelle rajeunit son interprète.

    Le travers est constant et documenté : à fiabilité comparable, une
    date plus récente qu'une source éditoriale est suspecte."""
    if len(cands) < 2:
        return
    edito = [c for c in cands if c["types"] & {"editorial"}]
    for c in cands:
        if c["types"] != {"studio"} and (c["types"] & {"editorial"}):
            continue
        dc = _date(c["valeur"])
        for e in edito:
            de = _date(e["valeur"])
            if dc and de and dc > de:
                ans = round((dc - de).days / 365.25, 1)
                c["note"] -= reglages["penalite_rajeunissement"]
                c["commentaires"].append(
                    f"rajeunissement de {ans} an(s) vs sources "
                    f"éditoriales — motif marketing connu")
                break


def _detect_exageration(cands, reglages, _contexte):
    """Le même travers sur la taille, dans l'autre sens."""
    if len(cands) < 2:
        return
    indep = [c for c in cands
             if c["types"] & {"editorial", "communautaire"}]
    for c in cands:
        if c["types"] != {"studio"}:
            continue
        ic = _entier(c["valeur"])
        for i in indep:
            ii = _entier(i["valeur"])
            if ic and ii and ic > ii:
                c["note"] -= reglages["penalite_exageration"]
                c["commentaires"].append(
                    f"+{ic - ii} cm vs sources indépendantes — "
                    f"exagération possible")
                break


def _detect_age_de_debut(cands, reglages, contexte):
    """Une date qui ferait débuter la carrière avant la majorité.

    Ce n'est pas une question de goût : une telle valeur est
    nécessairement fausse, et la signaler vaut mieux que l'écrire."""
    m = re.match(r"(\d{4})",
                 str((contexte or {}).get("years_active") or ""))
    if not m:
        return
    debut = int(m.group(1))
    for c in cands:
        dc = _date(c["valeur"])
        if dc and debut - dc.year < 18:
            c["note"] -= reglages["penalite_incoherence"]
            c["commentaires"].append(
                f"incohérence : débuterait à {debut - dc.year} ans")


def _detect_taille_implausible(cands, _reglages, _contexte):
    """Hors de cette plage, c'est une erreur de saisie ou d'unité."""
    for c in cands:
        ic = _entier(c["valeur"])
        if ic and not (150 <= ic <= 210):
            c["note"] -= 1.0
            c["commentaires"].append("valeur hors plage plausible")


# Quel champ subit quels détecteurs. Ajouter un travers du métier se
# fait ici, sans toucher au calcul général.
DETECTEURS = {
    "birthdate": (_detect_rajeunissement, _detect_age_de_debut),
    "height_cm": (_detect_exageration, _detect_taille_implausible),
}


def evaluer(champ: str, valeurs: dict, cfg: dict,
            contexte: dict = None) -> list:
    """Candidats triés par note décroissante.

    valeurs  : {source: valeur} pour ce champ
    contexte : autres infos utiles aux détecteurs (ex. carrière)
    Retour   : [{valeur, sources, familles, note, commentaires,
                 recommande}]
    """
    d = cfg["detecteurs"]
    contexte = contexte or {}
    cands = _clusters(champ, valeurs, cfg)
    for c in cands:
        c["familles"] = sorted({famille_de(s, cfg) for s in c["sources"]})
        c["types"] = {type_de(s, cfg) for s in c["sources"]}
        base = 10 * max(fiabilite(s, champ, cfg) for s in c["sources"])
        bonus = min(d["bonus_max"],
                    d["bonus_famille"] * (len(c["familles"]) - 1))
        c["note"] = base + bonus
        c["commentaires"] = []
        if len(c["familles"]) > 1:
            c["commentaires"].append(
                f"{len(c['familles'])} familles indépendantes d'accord")
        elif c["types"] == {"studio"}:
            c["commentaires"].append("sources studio uniquement "
                                     "(partie prenante)")

    for detecteur in DETECTEURS.get(champ, ()):
        detecteur(cands, d, contexte)

    for c in cands:
        c["note"] = round(max(0.5, min(9.8, c["note"])), 1)
        c.pop("types", None)
    cands.sort(key=lambda c: -c["note"])
    for i, c in enumerate(cands):
        c["recommande"] = (i == 0)
    return cands


def evaluer_tous(raw: dict, actuel: dict, champs: set,
                 cfg: dict) -> dict:
    """{champ: [candidats]} — un champ n'est évalué que si au moins une
    source apporte une valeur différente de l'existant."""
    contexte = {"years_active":
                next((d.get("years_active") for d in raw.values()
                      if d.get("years_active")), None)}
    out = {}
    for champ in champs:
        valeurs = {s: d[champ] for s, d in raw.items() if d.get(champ)}
        if not valeurs:
            continue
        act = actuel.get(champ)
        if act and all(_proches(champ, v, act, cfg)
                       for v in valeurs.values()):
            continue
        out[champ] = evaluer(champ, valeurs, cfg, contexte)
    return out
