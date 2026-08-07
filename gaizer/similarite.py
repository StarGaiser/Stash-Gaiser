# -*- coding: utf-8 -*-
"""Comparaison de noms : rapprochement de fiches et
notation des doublons. Logique pure, sans accès au
serveur."""

from __future__ import annotations

import json
import re
import unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))



def _sans_accents(txt: str) -> str:
    """« Björn » devient « Bjorn », et non « Bjrn ».

    Les sources écrivent indifféremment un nom avec ou sans signes
    diacritiques. Les supprimer sans translittérer empêcherait les deux
    écritures de se rapprocher — « Björn Söder » et « Bjorn Soder »
    seraient restés deux fiches distinctes."""
    decompose = unicodedata.normalize("NFD", txt or "")
    return "".join(c for c in decompose if not unicodedata.combining(c))


def _sim_cles(nom: str):
    bas = re.sub(r"[^a-z0-9 ]", "",
                 _sans_accents(nom or "").lower()).strip()
    return bas.replace(" ", ""), bas.split()


def _doublon_probable(c1, c2) -> bool:
    """c1/c2 : (cle_plate, tokens). Vrai si noms quasi identiques :
    égalité normalisée, préfixe (Koldo G/Koldo Goran), ou même prénom
    avec nom réduit à l'initiale."""
    a, ta = c1
    b, tb = c2
    if not a or not b:
        return False
    if a == b:
        return True
    if (min(len(a), len(b)) >= 6
            and (a.startswith(b) or b.startswith(a))
            and abs(len(a) - len(b)) <= 10):
        return True
    return bool(len(ta) > 1 and len(tb) > 1 and ta[0] == tb[0] and ta[1][0] == tb[1][0] and (len(ta[1]) == 1 or len(tb[1]) == 1))


def _score_doublon(c1, c2) -> tuple:
    """Note /10 de la paire, alignée sur le workflow (seuil
    autoAcceptThreshold). (note, motif) ou (0, "")."""
    a, ta = c1
    b, tb = c2
    if not a or not b:
        return 0, ""
    if a == b:
        return 9.5, "noms identiques"
    court, long_ = sorted((a, b), key=len)
    if long_.startswith(court) and long_[len(court):].isdigit():
        return 9.2, "suffixe numérique (artefact de source)"
    if (min(len(a), len(b)) >= 6
            and (a.startswith(b) or b.startswith(a))
            and abs(len(a) - len(b)) <= 10):
        return 7.0, "préfixe commun"
    if (len(ta) > 1 and len(tb) > 1 and ta[0] == tb[0]
            and ta[1][0] == tb[1][0]
            and (len(ta[1]) == 1 or len(tb[1]) == 1)):
        return 6.0, "prénom + initiale"
    return 0, ""


def _richesse(p: dict) -> int:
    return sum(1 for c in ("details", "birthdate", "country",
                           "height_cm", "career_length")
               if p.get(c)) + len(p.get("alias_list") or [])


def _canonique_de(p: dict, q: dict, nom_cree: str) -> tuple:
    """(canonique, doublon). Une fiche du référentiel (non :créé)
    n'est JAMAIS le doublon face à une fiche créée ; entre deux
    créées, la plus riche gagne."""
    p_cree = any(t["name"] == nom_cree for t in p.get("tags", []))
    q_cree = any(t["name"] == nom_cree for t in q.get("tags", []))
    if p_cree != q_cree:
        return (q, p) if p_cree else (p, q)
    return (p, q) if _richesse(p) >= _richesse(q) else (q, p)


def paires_candidates(objets, cles, alias_plats, exempts,
                      note_mini=0.0, restreindre_a=None):
    """Paires d'entités aux noms proches, avec leur note et le motif.

    Mécanique commune aux trois détections (performers, studios,
    dédoublonnage complet) : comparaison des noms normalisés, prise en
    compte des alias, exclusion des paires déjà exemptées.

    objets        : liste de fiches Stash
    cles          : {id: (nom_plat, tokens)}
    alias_plats   : {id: {alias normalisés}}
    exempts       : fonction fiche → ids déjà exemptés
    note_mini     : seuil en dessous duquel la paire est ignorée
    restreindre_a : si fourni, au moins un des deux membres doit
                    appartenir à cet ensemble d'identifiants
    Retour        : {(id1, id2): (fiche1, fiche2, note, motif)}
    """
    paires = {}
    for i, x in enumerate(objets):
        xi = str(x["id"])
        for y in objets[i + 1:]:
            yi = str(y["id"])
            if restreindre_a is not None and not (
                    xi in restreindre_a or yi in restreindre_a):
                continue
            note, motif = _score_doublon(cles[xi], cles[yi])
            if (cles[xi][0] in alias_plats.get(yi, ())
                    or cles[yi][0] in alias_plats.get(xi, ())):
                note, motif = max((note, motif),
                                  (8.5, "nom = alias de l'autre"))
            if note <= 0 or note < note_mini:
                continue
            if yi in exempts(x) or xi in exempts(y):
                continue
            paires[(xi, yi)] = (x, y, note, motif)
    return paires


def exemptions_de(fiche: dict) -> set:
    """Identifiants que cette fiche a déclarés « pas un doublon »."""
    try:
        v = json.loads((fiche.get("custom_fields") or {})
                       .get("enrich_pas_doublon") or "[]")
        return {str(x) for x in v}
    except (ValueError, TypeError):
        return set()
