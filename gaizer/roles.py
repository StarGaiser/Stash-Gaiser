# -*- coding: utf-8 -*-
"""
Rôles et positions des interprètes.

Aucune source ne fournit cette information : `ScrapedPerformer` n'a
aucun champ de rôle, et les stash-boxes n'en exposent pas. Elle vient
donc de l'utilisateur, d'un import, ou éventuellement de ce qu'une
biographie dit explicitement. **Le plugin ne la devine jamais** :
attribuer un rôle sexuel à une personne réelle par déduction serait à
la fois faux et déplacé.

DEUX AXES INDÉPENDANTS, parce qu'ils ne recouvrent pas la même chose :

- la **position** (actif / passif / versatile) décrit un acte ; elle
  est structurante dans le contenu gay masculin, moins ailleurs, et
  n'a pas toujours de sens ;
- le **rapport de pouvoir** (dominant / soumis / permutant) est
  transversal : il vaut pour toutes les orientations et existe
  indépendamment de la position.

Les séparer évite le fourre-tout des valeurs héritées du type
« Actif Dominant », qui mélangeaient les deux et rendaient tout
filtrage impossible.

Le vocabulaire est volontairement court. Une taxonomie fine serait
plus juste mais impossible à renseigner : mieux vaut trois valeurs
utilisées qu'une douzaine laissées vides.
"""

from __future__ import annotations

import re

# Valeurs canoniques. La clé est stable et sert au stockage ; les
# libellés affichés passent par i18n.
POSITIONS = ("actif", "passif", "versatile")
POUVOIRS = ("dominant", "soumis", "permutant")

# Écritures rencontrées → valeur canonique. La liste couvre l'anglais
# et le français, le jargon courant, et les variantes du référentiel
# hérité. Ce qui n'est pas reconnu est laissé tel quel plutôt que
# rangé de force dans une case approximative.
_SYNONYMES_POSITION = {
    "actif": "actif", "active": "actif", "top": "actif",
    "tops": "actif", "dom top": "actif", "total top": "actif",
    "strictly top": "actif", "seulement actif": "actif",
    "passif": "passif", "passive": "passif", "bottom": "passif",
    "bottoms": "passif", "power bottom": "passif",
    "total bottom": "passif", "strictly bottom": "passif",
    "seulement passif": "passif",
    "versatile": "versatile", "vers": "versatile",
    "switch": "versatile", "polyvalent": "versatile",
    "versatile top": "versatile", "vers top": "versatile",
    "versatile bottom": "versatile", "vers bottom": "versatile",
    "les deux": "versatile", "both": "versatile",
}

_SYNONYMES_POUVOIR = {
    "dominant": "dominant", "dominante": "dominant", "dom": "dominant",
    "domina": "dominant", "dominatrice": "dominant",
    "dominateur": "dominant", "maitre": "dominant",
    "maitresse": "dominant", "master": "dominant", "mistress": "dominant",
    "soumis": "soumis", "soumise": "soumis", "sub": "soumis",
    "submissive": "soumis", "esclave": "soumis", "slave": "soumis",
    "permutant": "permutant", "switch": "permutant",
    "versatile pouvoir": "permutant",
}


def _plat(v) -> str:
    return re.sub(r"\s+", " ",
                  re.sub(r"[^a-zà-ÿ ]", " ", str(v or "").lower())).strip()


def lire(brut) -> tuple:
    """(position, pouvoir) déduits d'une écriture libre.

    « Actif Dominant » donne ('actif', 'dominant') ; « Power Bottom »
    donne ('passif', None) ; « Réalisatrice / Icone » ne donne rien —
    ce n'est pas une position, et l'inventer serait pire que le vide.

    Chaque axe est cherché indépendamment, ce qui permet de lire les
    valeurs composées sans énumérer toutes leurs combinaisons.
    """
    t = _plat(brut)
    if not t:
        return None, None

    position = pouvoir = None
    # Les expressions les plus longues d'abord : « power bottom » doit
    # primer sur « bottom », « versatile top » sur « top ».
    for table, cible in ((_SYNONYMES_POSITION, "position"),
                         (_SYNONYMES_POUVOIR, "pouvoir")):
        for mot in sorted(table, key=len, reverse=True):
            if re.search(rf"(^|\s){re.escape(mot)}($|\s)", t):
                if cible == "position" and position is None:
                    position = table[mot]
                elif cible == "pouvoir" and pouvoir is None:
                    pouvoir = table[mot]
                break
    return position, pouvoir


def normaliser(brut) -> dict:
    """{'position': …, 'pouvoir': …, 'reste': …} — « reste » conserve
    ce qui n'a pas été compris, pour ne rien perdre."""
    position, pouvoir = lire(brut)
    out = {}
    if position:
        out["position"] = position
    if pouvoir:
        out["pouvoir"] = pouvoir
    if not position and not pouvoir and str(brut or "").strip():
        out["reste"] = str(brut).strip()[:60]
    return out


def valide(axe: str, valeur) -> bool:
    reference = POSITIONS if axe == "position" else POUVOIRS
    return str(valeur or "").strip().lower() in reference


def pertinent(axe: str, profil: str = "") -> bool:
    """La position a-t-elle du sens pour ce profil de collection ?

    Elle structure le contenu gay masculin ; ailleurs elle est souvent
    sans objet, tandis que le rapport de pouvoir vaut partout. Ceci ne
    RESTREINT rien — l'utilisateur renseigne ce qu'il veut — mais
    permet à l'interface de ne pas encombrer avec un champ hors sujet.
    """
    if axe == "pouvoir":
        return True
    return (profil or "").strip().lower() in ("", "gay", "bi", "pan",
                                              "trans", "mixte")
