# -*- coding: utf-8 -*-
"""
Un seul interrupteur, qui commande tout.

Écrit AVANT le code.

Quarante-cinq réglages, quarante-deux tâches, sept onglets : la
quantité elle-même est ce qui décourage. Grouper et décrire a aidé,
mais n'a rien retiré de l'écran.

**Le vrai remède est de ne pas montrer.** Quelqu'un qui installe le
plugin n'a besoin ni de la température du modèle, ni du seuil de
fusion, ni du plafond d'appels : il veut que sa médiathèque soit
complétée. Ces réglages doivent exister — quelqu'un d'autre en a
besoin — mais pas s'imposer à tous.

**Un seul interrupteur, pas un par endroit.** Un état « simple ou
avancé » qui commanderait le panneau sans commander les réglages
laisserait la moitié du bruit. Il commande les deux.

**Ce qui est masqué reste actif.** Masquer n'est pas désactiver : un
réglage qu'on a mis en avancé, puis repassé en simple, garde sa
valeur. L'inverse serait un piège.
"""

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


@pytest.fixture(scope="module")
def page():
    return (CODE / "gaizer_page.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def manifeste():
    return yaml.safe_load(
        (CODE / "gaizer.yml").read_text(encoding="utf-8"))


# ── L'interrupteur ───────────────────────────────────────────────────
class TestInterrupteur:

    def test_il_existe_un_etat_d_affichage(self, page):
        assert "avance" in page or "modeAvance" in page

    def test_il_est_visible_sans_le_chercher(self, page):
        """Un interrupteur enfoui dans les réglages de Stash
        obligerait à quitter le panneau pour le trouver."""
        i = page.find("nav-tabs")
        bloc = page[max(0, i - 1200):i + 1200]
        assert "avance" in bloc

    def test_le_simple_est_l_etat_par_defaut(self, page):
        """C'est ce que voit quelqu'un qui installe : montrer
        quarante-deux actions d'emblée est ce qui décourage."""
        m = re.search(r'useState\(\s*(false|true)\s*\)[^;]*avance',
                      page) or re.search(
            r'avance[^=]*=\s*React\.useState\(\s*(false|true)', page)
        assert m, "l'état doit être déclaré explicitement"
        assert m.group(1) == "false"

    def test_le_choix_survit_a_un_rechargement(self, page):
        """Rebasculer en avancé à chaque visite serait une punition
        pour qui a choisi une fois."""
        assert "localStorage" in page or "gaizerAvance" in page


# ── Ce que masque le mode simple ─────────────────────────────────────
class TestOngletsMasques:
    """Trois onglets sur cinq ne servent qu'à qui sait ce qu'il
    cherche. Ménage, Diagnostic et Réparation n'ont aucun sens pour
    quelqu'un qui vient d'installer."""

    VISIBLES = ("simple", "g_demarrage", "g_courant")

    def test_les_onglets_experts_sont_masques(self, page):
        i = page.find("GROUPES.filter(")
        assert i > 0, "la liste d'onglets doit filtrer"
        bloc = page[i:i + 300]
        assert "avance" in bloc and "ONGLETS_SIMPLES" in bloc

    def test_les_onglets_utiles_restent(self, page):
        """Masquer « Première mise en route » priverait du seul
        chemin balisé."""
        assert "g_demarrage" in page and "g_courant" in page

    def test_l_onglet_courant_revient_si_il_disparait(self, page):
        """Basculer en simple alors qu'on est dans Diagnostic
        laisserait un écran vide."""
        assert "setOnglet" in page
        i = page.find("basculerAvance")
        assert i > 0
        assert "setOnglet" in page[i:i + 500]


class TestReglagesMasques:
    """Un réglage que personne ne change n'a pas sa place devant tout
    le monde."""

    AVANCES = ("6.", "3.")

    def test_les_reglages_fins_sont_marques(self, manifeste):
        """Le manifeste ne peut pas masquer — Stash affiche tout —
        mais il peut DIRE lesquels sont fins, pour que le panneau et
        la documentation s'accordent."""
        fins = [k for k, v in manifeste["settings"].items()
                if str(v.get("displayName", "")).startswith("6.")]
        assert fins, "le groupe des réglages fins doit exister"

    def test_le_panneau_offre_les_reglages_courants(self, page):
        """Aller dans les réglages de Stash pour changer une valeur
        qu'on vient de voir mentionnée est une gymnastique."""
        assert "ReglagesRapides" in page or "reglages_rapides" in page

    def test_les_reglages_offerts_restent_peu_nombreux(self, page):
        """En offrir quarante reproduirait l'écran qu'on fuit."""
        i = page.find("REGLAGES_RAPIDES")
        assert i > 0
        fin = page.find("]", i)
        assert page[i:fin].count('"') // 2 <= 8


# ── Les arguments ────────────────────────────────────────────────────
class TestArguments:
    """Douze tâches attendent un argument que rien ne permet de
    saisir : il faut passer par l'écran des plugins de Stash. La
    description le dit, mais dire n'est pas offrir."""

    def test_une_tache_a_argument_offre_un_champ(self, page):
        assert "argument" in page.lower()

    def test_le_champ_n_apparait_que_si_besoin(self, page):
        """Un champ vide sur chaque ligne serait du bruit."""
        i = page.lower().find("argument")
        bloc = page[max(0, i - 600):i + 600]
        assert "?" in bloc or "&&" in bloc

    def test_les_taches_a_argument_sont_declarees(self, page):
        """Le panneau doit savoir lesquelles en prennent un, et sous
        quel nom."""
        assert "ARGUMENTS" in page

    def test_l_argument_est_transmis_a_la_tache(self, page):
        i = page.find("ARGUMENTS")
        assert i > 0
        assert "runModeEtAttendre" in page or "lancer" in page
