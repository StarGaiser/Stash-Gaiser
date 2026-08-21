#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique un jeu d'essai à partir de la médiathèque locale.

Le principe : les fixtures ne sont PAS dans le dépôt, elles sont
fabriquées sur place par celui qui lance les tests, depuis sa propre
collection. Chacun teste sur son réel, personne ne publie les données
de personnes réelles.

Ce que ça apporte face à un jeu synthétique : les bizarreries qu'on
n'invente pas. Les défauts trouvés jusqu'ici — une date « 0000-00-00 »
qui interrompait toute une fiche, des chaînes vides prises pour des
valeurs, « Réalisatrice / Icone » rangé de force parmi les positions,
des biographies réduites au seul pied — venaient tous de données
réelles, jamais d'un cas imaginé.

    python3 tools/capturer_fixtures.py [nombre]

Écrit dans `tests/fixtures_locales/`, ignoré par git. Les tests qui en
dépendent s'ignorent proprement quand le dossier est absent : un
contributeur sans Stash lance quand même le reste de la suite.
"""

import json
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "tests" / "fixtures_locales"
URL = "http://127.0.0.1:9999/graphql"


def gql(requete, variables=None):
    corps = json.dumps({"query": requete,
                        "variables": variables or {}}).encode()
    r = urllib.request.Request(
        URL, data=corps, headers={"Content-Type": "application/json"})
    reponse = json.loads(urllib.request.urlopen(r, timeout=180).read())
    if reponse.get("errors"):
        raise RuntimeError(reponse["errors"][0]["message"][:120])
    return reponse["data"]


def _varie(entites, combien, cle):
    """Échantillon VARIÉ plutôt que les N premiers.

    Prendre le début de l'alphabet donnerait un jeu homogène, où les
    cas limites — champs vides, valeurs aberrantes, noms d'une seule
    partie — auraient toutes les chances de manquer. On retient donc
    les extrêmes de chaque critère intéressant, puis on complète par
    un échantillonnage régulier."""
    retenus, vus = [], set()

    def ajouter(e):
        if e and str(e["id"]) not in vus:
            vus.add(str(e["id"]))
            retenus.append(e)

    # Les extrêmes : le plus et le moins renseigné.
    par_richesse = sorted(entites, key=lambda e: len(json.dumps(e)))
    ajouter(par_richesse[0])
    ajouter(par_richesse[-1])
    # Ce qui sort de l'ordinaire.
    for critere in (
            lambda e: len(str(e.get(cle) or "").split()) == 1,
            lambda e: not (e.get("custom_fields") or {}),
            lambda e: "CONFLIT" in str((e.get("custom_fields") or {})
                                       .get("enrich_rapport") or ""),
            lambda e: len(e.get("alias_list") or []) > 3,
            lambda e: not str(e.get(cle) or "").isascii()):
        ajouter(next((e for e in entites if critere(e)), None))
    # Puis un échantillonnage régulier pour compléter.
    pas = max(1, len(entites) // max(1, combien - len(retenus)))
    for e in entites[::pas]:
        if len(retenus) >= combien:
            break
        ajouter(e)
    return retenus[:combien]


def main():
    combien = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    try:
        d = gql("""{ findPerformers(filter: {per_page: -1}) {
            performers { id name alias_list birthdate height_cm weight
              penis_length country ethnicity circumcised details
              career_length custom_fields tags { id name } } }
          findStudios(filter: {per_page: -1}) {
            studios { id name aliases url details custom_fields
              parent_studio { id } } }
          findScenes(filter: {per_page: -1}) {
            scenes { id title date details custom_fields
              studio { id name } performers { id name }
              tags { id name } groups { group { id name } } } } }""")
    except Exception as exc:
        print(f"Stash injoignable sur {URL} : {str(exc)[:90]}")
        return 1

    perfs = d["findPerformers"]["performers"]
    studios = d["findStudios"]["studios"]
    scenes = d["findScenes"]["scenes"]
    print(f"  collection : {len(perfs)} interprètes, {len(studios)} "
          f"studios, {len(scenes)} scènes")

    jeu = {
        "performers": _varie(perfs, combien, "name"),
        "studios": _varie(studios, max(5, combien // 3), "name"),
        "scenes": _varie(scenes, combien, "title"),
    }
    # Les tags cités doivent exister, sinon le faux serveur ne les
    # retrouve pas et les tests échouent pour une mauvaise raison.
    tags = {}
    for groupe in ("performers", "scenes"):
        for e in jeu[groupe]:
            for t in e.get("tags") or []:
                tags[str(t["id"])] = {"id": str(t["id"]),
                                      "name": t["name"]}
    jeu["tags"] = list(tags.values())

    DOSSIER.mkdir(parents=True, exist_ok=True)
    (DOSSIER / "collection.json").write_text(
        json.dumps(jeu, ensure_ascii=False, indent=1), encoding="utf-8")
    (DOSSIER / "LISEZ-MOI.txt").write_text(
        "Jeu d'essai fabriqué depuis la médiathèque locale.\n"
        "Ce dossier n'est PAS versionné : il contient des données\n"
        "réelles. Le regénérer avec tools/capturer_fixtures.py.\n",
        encoding="utf-8")

    print(f"  jeu écrit : {len(jeu['performers'])} interprètes, "
          f"{len(jeu['studios'])} studios, {len(jeu['scenes'])} scènes, "
          f"{len(jeu['tags'])} tags")
    print(f"  → {DOSSIER}")

    # Ce que l'échantillon couvre : sans cela on ne sait pas ce qu'on
    # teste, et un jeu qui ne contient aucun cas limite rassure à tort.
    print("\n  cas limites présents :")
    controles = {
        "nom d'une seule partie":
            any(len(p["name"].split()) == 1 for p in jeu["performers"]),
        "sans champs personnalisés":
            any(not (p.get("custom_fields") or {})
                for p in jeu["performers"]),
        "conflit signalé":
            any("CONFLIT" in str((p.get("custom_fields") or {})
                                 .get("enrich_rapport") or "")
                for p in jeu["performers"]),
        "biographie vide":
            any(not (p.get("details") or "").strip()
                for p in jeu["performers"]),
        "caractères non ASCII":
            any(not p["name"].isascii() for p in jeu["performers"]),
        "scène sans studio":
            any(not s.get("studio") for s in jeu["scenes"]),
        "scène sans interprète":
            any(not s.get("performers") for s in jeu["scenes"]),
        "scène sans date":
            any(not s.get("date") for s in jeu["scenes"]),
        "scène dans un groupe":
            any(s.get("groups") for s in jeu["scenes"]),
    }
    for quoi, present in controles.items():
        print(f"    {'✓' if present else '—'} {quoi}")
    absents = [q for q, v in controles.items() if not v]
    if absents:
        print(f"\n  {len(absents)} cas limite(s) absent(s) : relancer "
              f"avec un nombre plus élevé pour les capter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
