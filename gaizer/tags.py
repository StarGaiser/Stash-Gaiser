# -*- coding: utf-8 -*-
"""
Familles de tags et suggestions d'exclusion.

Le problème que ce module résout : une liste de tags « à ne pas
appliquer » écrite pour une collection est absurde pour une autre.
« Gay » n'apprend rien dans une médiathèque entièrement gay ; c'est
l'information la plus discriminante dans une médiathèque mixte.

La bonne notion n'est donc pas « ce tag est mauvais » mais **« ce tag
ne discrimine rien ICI »**. D'où deux mécanismes complémentaires :

1. **Statistique** — un tag présent sur la quasi-totalité des scènes
   n'apporte aucune information, quel que soit son sens. Ce calcul ne
   suppose rien du contenu et vaut pour toute collection.

2. **Familles déclaratives** — `tag_profiles.yml` range les tags
   courants par nature (format, édition, anatomie, pratiques,
   orientation, identité). Ces familles sont DESCRIPTIVES, pas
   normatives : elles disent ce qu'un tag est, jamais s'il faut
   l'écarter.

Les profils (gay, hétéro, bi, pan, trans, mixte) ne sont jamais actifs
par défaut et ne PROPOSENT que des exclusions, laissées à l'arbitrage.
Par prudence, un profil ne touche d'office qu'aux familles techniques
(format, édition) : écarter mécaniquement les tags d'identité de genre
parce qu'une collection est étiquetée « gay » serait une régression,
pas une amélioration — les catégories ne sont pas étanches, et une
collection gay contient des interprètes trans.
"""

from __future__ import annotations

import re
from pathlib import Path

FICHIER = Path(__file__).resolve().parent / "tag_profiles.yml"

# Familles techniques : sans rapport avec le contenu, elles décrivent
# le fichier ou l'édition. Leur exclusion ne perd aucune information
# sur ce qui est filmé — c'est pourquoi les profils peuvent les
# proposer sans risque.
FAMILLES_TECHNIQUES = ("format", "edition")

DEFAUTS = {
    "familles": {
        # Qualité, encodage, provenance du fichier.
        "format": [
            "4k", "1080p", "720p", "480p", "2160p", "uhd", "hd", "sd",
            "web-dl", "webrip", "bluray", "dvd", "vr", "180", "360",
            "*fps", "hevc", "h264", "x265", "remux",
            # « *rip » attrapait « Cum Drip » : les formats sont
            # nommés explicitement plutôt que par un suffixe.
            "bdrip", "dvdrip", "brrip", "hdrip", "camrip",
        ],
        # Découpage éditorial, mentions commerciales.
        "edition": [
            "bonus*", "feature", "series", "trailer", "preview",
            "compilation", "behind the scenes", "bts", "photoshoot",
            "interview", "*videos", "full movie",
        ],
        # Anatomie. Aucun jugement : une famille sert à repérer, pas à
        # trier.
        "anatomie": [
            "*pussy*", "*penis*", "*cock*", "*breast*", "*boobs*",
            "*tits*", "*ass*", "*nipple*", "circumcised",
            "uncircumcised", "*balls*", "*clit*", "*vulva*",
        ],
        "pratiques": [
            "anal", "anal sex", "oral", "*blowjob*", "*handjob*",
            "*rimming*", "*fisting*", "*bondage*", "*massage*",
            "*creampie*", "*facial*", "threesome", "group sex", "solo",
            "*masturbation*", "kissing", "*fingering*",
        ],
        # Orientation du contenu.
        "orientation": [
            "gay", "straight", "hetero", "heterosexual", "lesbian",
            "bisexual", "bi", "pansexual", "queer", "lgbt", "lgbtq",
            "lgbtq+",
        ],
        # Identité de genre et présentation. Famille SENSIBLE : jamais
        # proposée à l'exclusion par un profil, seulement identifiable.
        # Identité de genre. Famille SENSIBLE : jamais proposée à
        # l'exclusion par un profil, seulement identifiable.
        # « *trans* » classait « Transparent Clothing » ici : les
        # termes sont donc exacts ou préfixés, jamais englobants.
        "identite": [
            "trans", "transgender", "transsexual", "transman",
            "transwoman", "trans man", "trans woman", "ftm", "mtf",
            "non-binary", "nonbinary", "enby", "intersex",
            "genderqueer", "crossdresser", "crossdressing", "drag",
            "drag queen", "drag king",
        ],
        # Caractéristiques physiques des interprètes.
        "physique": [
            "*hairy*", "*shaved*", "*smooth*", "*muscular*", "*bbw*",
            "*tattoo*", "*pierced*", "bald", "*beard*", "*blonde*",
            "*brunette*", "*redhead*", "*chubby*", "*twink*",
            # Morphotypes de la culture gay : ils décrivent une
            # silhouette, pas une identité de genre — les ranger dans
            # « identite » les aurait protégés pour une mauvaise
            # raison, et brouillait les deux notions.
            "bear", "otter", "cub", "wolf", "jock", "daddy",
            "silver fox", "femboy", "butch", "femme",
        ],
    },

    # Un profil décrit ce qu'une collection contient, afin de repérer
    # ce qui n'y discrimine rien. « suggere » liste les familles dont
    # l'exclusion sera PROPOSÉE ; « jamais » protège explicitement des
    # familles de toute suggestion, même statistique.
    "profils": {
        "gay": {
            "description": "Collection masculine gay",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "pratiques"],
        },
        "hetero": {
            "description": "Collection hétérosexuelle",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "pratiques"],
        },
        "lesbien": {
            "description": "Collection féminine lesbienne",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "pratiques"],
        },
        "bi": {
            "description": "Collection bisexuelle",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "orientation", "pratiques"],
        },
        "pan": {
            "description": "Collection pansexuelle",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "orientation", "pratiques"],
        },
        "trans": {
            "description": "Collection trans",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "orientation", "pratiques"],
        },
        "mixte": {
            "description": "Collection variée — rien n'est supposé",
            "suggere": list(FAMILLES_TECHNIQUES),
            "jamais": ["identite", "orientation", "pratiques",
                       "anatomie"],
        },
    },

    "seuils": {
        # Au-delà de cette part des scènes, un tag ne sépare plus rien.
        "couverture_inutile": 0.90,
        # Part des occurrences de sa famille qu'un tag doit absorber
        # pour être tenu pour une constante. Mesure RELATIVE, seule
        # utile quand l'étiquetage est clairsemé.
        "dominance_famille": 0.90,
        # En deçà, un tag ne sert pas non plus à regrouper.
        "occurrences_rares": 2,
    },
}

GABARIT = """# tag_profiles.yml — familles de tags et profils de collection.
#
# Ce fichier est FACULTATIF : les familles courantes sont déjà connues
# du plugin. N'écrire ici que pour en ajouter, en corriger, ou définir
# un profil propre à votre collection.
#
# Les familles sont DESCRIPTIVES : elles disent ce qu'un tag est, pas
# s'il faut l'écarter. Rien n'est exclu sans votre validation.
#
# Motifs acceptés, comme pour le réglage « Tags à ne jamais appliquer » :
#   gay        correspondance exacte (n'atteint pas « Gay Massage »)
#   *pussy*    le tag contient le mot
#   bonus*     le tag commence par
#   *videos    le tag se termine par
#
# Exemple — ajouter une famille et un profil :
#
# familles:
#   studio_maison:
#     - "mon studio*"
#
# profils:
#   ma_collection:
#     description: Ce que contient ma médiathèque
#     suggere: [format, edition, studio_maison]
#     jamais: [identite, orientation]
#
# seuils:
#   couverture_inutile: 0.90   # un tag sur 90 % des scènes ne trie rien
#   occurrences_rares: 2
"""


def charger(dossier=None) -> dict:
    """Familles et profils : table embarquée, complétée par le fichier.

    La fusion se fait famille par famille : déclarer « format » dans le
    fichier remplace cette seule famille, les autres subsistent."""
    table = {
        "familles": {k: list(v)
                     for k, v in DEFAUTS["familles"].items()},
        "profils": {k: dict(v) for k, v in DEFAUTS["profils"].items()},
        "seuils": dict(DEFAUTS["seuils"]),
    }
    chemin = Path(dossier) / "tag_profiles.yml" if dossier else FICHIER
    if not chemin.exists():
        return table
    try:
        import yaml
        perso = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    except Exception:
        return table
    if not isinstance(perso, dict):
        return table
    for section in ("familles", "profils", "seuils"):
        ajouts = perso.get(section)
        if isinstance(ajouts, dict):
            table[section].update(ajouts)
    return table


def creer_gabarit(dossier=None) -> bool:
    """Dépose le fichier commenté s'il n'existe pas encore."""
    chemin = Path(dossier) / "tag_profiles.yml" if dossier else FICHIER
    if chemin.exists():
        return False
    try:
        chemin.write_text(GABARIT, encoding="utf-8")
        return True
    except OSError:
        return False


def _correspond(nom: str, motif: str) -> bool:
    """Même logique de motifs que le réglage d'exclusion, pour qu'un
    utilisateur n'ait qu'une syntaxe à connaître."""
    bas = re.sub(r"[^a-z0-9 ]", "", (nom or "").strip().lower()).strip()
    m = re.sub(r"[^a-z0-9 *]", "", (motif or "").strip().lower()).strip()
    if not bas or not m:
        return False
    if m.startswith("*") and m.endswith("*") and len(m) > 2:
        return m[1:-1] in bas
    if m.startswith("*"):
        return bas.endswith(m[1:])
    if m.endswith("*"):
        return bas.startswith(m[:-1])
    return bas == m


def famille_de(nom: str, table: dict) -> str:
    """Famille d'un tag, ou « » s'il n'en a aucune de connue.

    L'ordre compte : les familles techniques sont examinées d'abord,
    car « Bonus Scene » relève de l'édition avant tout autre sens."""
    familles = table.get("familles") or {}
    ordre = list(FAMILLES_TECHNIQUES) + [
        f for f in familles if f not in FAMILLES_TECHNIQUES]
    for fam in ordre:
        for motif in familles.get(fam) or []:
            if _correspond(nom, motif):
                return fam
    return ""


def repartition(noms, table: dict) -> dict:
    """{famille: [tags]} — « » regroupe les tags non classés."""
    out = {}
    for nom in noms:
        out.setdefault(famille_de(nom, table), []).append(nom)
    return out


def suggestions(frequences: dict, total_scenes: int, table: dict,
                profil: str = "") -> dict:
    """Tags dont l'exclusion mérite d'être PROPOSÉE, par motif.

    Rien n'est décidé ici : la fonction produit un avis, l'utilisateur
    tranche. Trois motifs, du plus objectif au plus discutable :

    - `omnipresent` : le tag couvre presque toute la collection, il ne
      sépare donc plus rien. Aucune hypothèse sur son sens.
    - `rare` : une ou deux occurrences, il ne regroupe rien non plus.
    - `famille` : le profil déclaré considère cette famille comme sans
      valeur de tri — uniquement les familles techniques par défaut.

    Les familles listées dans « jamais » du profil sont écartées de
    toute suggestion, y compris statistique : leur omniprésence peut
    être une caractéristique de la collection, pas du bruit.
    """
    seuils = table.get("seuils") or {}
    try:
        part = float(seuils.get("couverture_inutile", 0.90))
    except (TypeError, ValueError):
        part = 0.90
    try:
        rare = int(seuils.get("occurrences_rares", 2))
    except (TypeError, ValueError):
        rare = 2
    try:
        dom = float(seuils.get("dominance_famille", 0.90))
    except (TypeError, ValueError):
        dom = 0.90

    conf = (table.get("profils") or {}).get(profil) or {}
    proposees = set(conf.get("suggere") or [])
    protegees = set(conf.get("jamais") or [])

    # Poids de chaque famille, pour mesurer les dominances.
    totaux, familles = {}, {}
    for nom, n in frequences.items():
        fam = famille_de(nom, table)
        familles[nom] = fam
        if fam:
            totaux[fam] = totaux.get(fam, 0) + n

    out = {"omnipresent": [], "dominant": [], "rare": [], "famille": []}
    seuil_abs = max(1, int(total_scenes * part)) if total_scenes else 0
    for nom, n in frequences.items():
        fam = familles[nom]
        if fam and fam in protegees:
            continue
        if seuil_abs and n >= seuil_abs:
            out["omnipresent"].append((nom, n, fam))
        elif fam and fam in proposees:
            out["famille"].append((nom, n, fam))
        elif (fam and totaux.get(fam, 0) >= 10
                and n / totaux[fam] >= dom):
            # Ce tag absorbe presque toute sa famille : il décrit une
            # constante de la collection, pas une distinction. Cette
            # mesure RELATIVE rattrape ce que la couverture absolue
            # laisse passer quand l'étiquetage est clairsemé — un tag
            # posé sur 14 % des scènes seulement peut détenir 96 % de
            # sa famille.
            out["dominant"].append((nom, n, fam))
        elif n <= rare:
            out["rare"].append((nom, n, fam))
    for cle in out:
        out[cle].sort(key=lambda x: -x[1])
    return out


def profils_connus(table: dict) -> list:
    """[(nom, description)] pour affichage."""
    return sorted(((nom, (conf or {}).get("description") or "")
                   for nom, conf in (table.get("profils") or {}).items()),
                  key=lambda x: x[0])
