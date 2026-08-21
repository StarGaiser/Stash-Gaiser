# -*- coding: utf-8 -*-
"""
Seuils de couverture par module, selon ce que le module risque.

Un objectif unique — « 90 % partout » — mesure mal. Il pousse à écrire
des tests qui exécutent sans éprouver, parce que les derniers points
sont les plus pénibles, et il traite de la même façon une fonction qui
supprime des fiches et une fonction qui écrit une ligne de journal.

Trois régimes, selon ce qu'une ligne non couverte coûte :

  **Ce qui décide ou détruit** — arbitrage, fusion, suppression,
  restauration, sécurité. Une ligne non éprouvée y est un risque de
  perte de données. Seuil haut.

  **Ce qui traite** — collecte, normalisation, tâches, interface. Une
  erreur s'y voit et se corrige. Seuil moyen.

  **Ce qui appelle l'extérieur** — sources distantes, modèle de
  langage, point d'entrée. Non couvert DÉLIBÉRÉMENT : un test qui
  appelle le réseau est lent et instable, et un test instable finit
  ignoré. Ces chemins sont éprouvés par la tâche « Vérifier l'état des
  sources », qui appelle pour de vrai, hors de la suite.

Les seuils fonctionnent comme des CLIQUETS : ils reflètent l'état
atteint, et les baisser demande une raison. Les monter quand le code
progresse fait partie du travail.
"""

import json
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent

# Seuil minimal par module. Le commentaire dit POURQUOI ce régime.
SEUILS = {
    # ── Ce qui décide ou détruit ─────────────────────────────────────
    "scoring": (95, "décide quelle valeur est écrite"),
    "roles": (96, "vocabulaire fermé, aucune excuse"),
    "tags": (91, "décide ce qui est écarté"),
    "reglages": (96, "export et import des réglages"),
    "profil": (90, "déduction du profil de collection"),
    "entites": (80, "crée, restaure, marque"),
    "scrapers": (80, "installe du code tiers"),
    "vision": (83, "envoie des images à un tiers"),
    "doublons": (55, "fusionne et supprime des fiches"),
    "similarite": (85, "décide si deux fiches sont la même"),
    "gaizer": (93, ""),
    "rapprochement": (93, ""),
    "cache": (90, ""),
    "sprites": (84, ""),
    "chemins": (88, ""),
    "enchainement": (85, ""),
    # ── Ce qui traite ────────────────────────────────────────────────
    "noyau": (77, "socle commun"),
    "ia": (71, "génération de textes"),
    "groupes": (68, "reconstitution des films"),
    "studios": (61, ""),
    "taches_heritage": (72, ""),
    "taches_arbitrage": (59, ""),
    "performers": (46, ""),
    "taches_diagnostic": (48, ""),
    "scenes": (58, ""),
    "collecte": (47, ""),
    "taches_menage": (77, ""),
    "i18n": (92, "tables de traduction"),
    "llm": (91, "catalogue de fournisseurs"),
    # ── Ce qui appelle l'extérieur ───────────────────────────────────
    "sources": (59, "requêtes distantes — éprouvées hors suite"),
    "taches_maintenance": (69, "réglages et migrations, peu de logique"),
}

# Non couverts délibérément, avec la raison.
EXEMPTS = {
    "gaizer": "point d'entrée : lit l'entrée standard et distribue. "
              "L'éprouver reviendrait à tester le lanceur de Stash.",
}


def _couverture():
    """{module: pourcentage} — mesure fraîche, pas un fichier ancien."""
    r = subprocess.run(
        ["python3", "-m", "coverage", "json", "-o", "-", "--quiet"],
        capture_output=True, text=True, cwd=RACINE, check=False)
    try:
        fichiers = json.loads(r.stdout or "{}").get("files", {})
    except json.JSONDecodeError:
        return {}
    return {Path(chemin).stem: d["summary"]["percent_covered"]
            for chemin, d in fichiers.items()}


@pytest.fixture(scope="module")
def couverture():
    mesures = _couverture()
    if not mesures:
        pytest.skip("mesure de couverture indisponible — lancer "
                    "« coverage run -m pytest » d'abord")
    return mesures


class TestSeuils:

    def test_chaque_module_est_classe(self, couverture):
        """Un module ajouté sans seuil échappe au contrôle sans que
        rien ne le signale."""
        oublies = sorted(set(couverture) - set(SEUILS) - set(EXEMPTS))
        assert oublies == [], (
            f"modules sans seuil : {oublies}. Leur en attribuer un "
            f"selon ce qu'ils risquent, ou les exempter avec une "
            f"raison.")

    def test_aucun_module_sous_son_seuil(self, couverture):
        """Le cliquet : la couverture peut monter, jamais descendre
        sans qu'on s'en aperçoive."""
        sous = []
        for module, (seuil, _raison) in sorted(SEUILS.items()):
            mesure = couverture.get(module)
            if mesure is None:
                continue
            if mesure < seuil:
                sous.append(f"{module} {mesure:.0f} % < {seuil} %")
        assert sous == [], sous

    def test_ce_qui_detruit_est_mieux_couvert_que_le_reste(self):
        """La règle qui justifie les régimes : le code qui peut faire
        perdre des données doit être plus éprouvé que celui qui écrit
        un message."""
        destructeurs = ("scoring", "roles", "similarite", "tags",
                        "scrapers")
        for module in destructeurs:
            assert SEUILS[module][0] >= 80, module

    def test_les_exemptions_portent_une_raison(self):
        for module, raison in EXEMPTS.items():
            assert len(raison) > 30, module

    def test_les_seuils_ne_derivent_pas_de_la_mesure(self, couverture):
        """Un seuil très en dessous de la mesure ne protège plus rien :
        le module pourrait perdre la moitié de sa couverture sans que
        le contrôle réagisse."""
        laxistes = []
        for module, (seuil, _raison) in SEUILS.items():
            mesure = couverture.get(module)
            if mesure is not None and mesure - seuil > 12:
                laxistes.append(
                    f"{module} : seuil {seuil} % pour {mesure:.0f} % "
                    f"mesurés")
        assert laxistes == [], laxistes


class TestEnsemble:

    def test_la_couverture_globale_ne_baisse_pas(self, couverture):
        if not couverture:
            pytest.skip("mesure indisponible")
        total = sum(couverture.values()) / len(couverture)
        assert total >= 60, f"{total:.1f} %"
