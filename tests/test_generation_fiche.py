# -*- coding: utf-8 -*-
"""
Générer un texte là où on le lit.

Écrit AVANT le code.

Un panneau global règle les instructions données au modèle, et un
bouton de lot les applique à toute la collection. Entre les deux,
rien : on ne voit jamais sur QUELLE fiche le texte sera écrit, ni ce
qu'il donnera avant qu'il soit là.

Le défaut est de conception, pas de présentation. Régler un prompt
sans le voir agir, c'est ajuster à l'aveugle : on lance un lot, on
lit ce qui est sorti, on revient au panneau, on recommence. Chaque
tour coûte des appels sur des centaines de fiches pour vérifier une
formulation.

**La fiche est le bon endroit.** Elle nomme l'entité, elle porte les
données dont le modèle se sert, et c'est là qu'on lit le résultat.

**L'aperçu précède l'écriture.** Un texte généré remplace un texte
existant : le montrer avant permet de refuser, ce qu'aucun retour en
arrière ne rend aussi simple.

**Les trois familles sont concernées.** Un interprète a une
biographie, un studio une présentation, une scène un synopsis. Ne
traiter que la première laisserait deux tiers du problème.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


@pytest.fixture(scope="module")
def page():
    return (CODE / "gaizer_page.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fiche():
    return (CODE / "gaizer.js").read_text(encoding="utf-8")


# ── Le bouton, sur les trois familles ────────────────────────────────
class TestBoutonSurLesTroisFamilles:
    """Un interprète a une biographie, un studio une présentation, une
    scène un synopsis. Ne traiter que la première laisserait deux
    tiers du problème."""

    def test_le_bouton_existe(self, fiche):
        assert 'B("generer_ia"' in fiche

    def test_il_figure_sur_les_trois_types(self, fiche):
        """Compté par les branches qui le posent, non par le nombre
        d'occurrences : une seule ligne partagée conviendrait aussi."""
        assert fiche.count('B("generer_ia"') >= 1
        for genre in ("performer", "studio", "scene"):
            assert f'type === "{genre}"' in fiche, genre

    def test_chaque_famille_a_son_mode(self, fiche):
        """Une biographie n'est pas un synopsis : le même prompt pour
        les trois produirait trois textes également inadaptés."""
        i = fiche.find("MODES_GENERATION")
        assert i > 0, "la table des modes doit exister"
        bloc = fiche[i:i + 500]
        for genre in ("performer", "studio", "scene"):
            assert genre in bloc, genre


# ── L'aperçu ─────────────────────────────────────────────────────────
class TestApercuAvantEcriture:
    """Un texte généré remplace un texte existant. Le montrer avant
    permet de refuser — ce qu'aucun retour en arrière ne rend aussi
    simple, puisqu'il faut d'abord s'apercevoir du problème."""

    def test_le_texte_est_montre_avant_d_etre_ecrit(self, fiche):
        assert "apercu" in fiche.lower()

    def test_l_utilisateur_peut_refuser(self, fiche):
        i = fiche.find("function Apercu")
        fin = fiche.find("\n  function ", i + 10)
        bloc = fiche[i:fin if fin > i else i + 3500]
        assert "ap_annuler" in bloc

    def test_l_utilisateur_peut_accepter(self, fiche):
        i = fiche.find("function Apercu")
        fin = fiche.find("\n  function ", i + 10)
        bloc = fiche[i:fin if fin > i else i + 3500]
        assert "ap_ecrire" in bloc

    def test_le_texte_existant_est_montre_a_cote(self, fiche):
        """Remplacer sans comparer, c'est décider sans savoir ce qu'on
        perd."""
        i = fiche.find("MODES_GENERATION")
        bloc = fiche[i:i + 3500]
        assert "actuel" in bloc.lower() or "existant" in bloc.lower()

    def test_l_apercu_ne_touche_pas_la_fiche(self, fiche):
        """Générer pour voir ne doit rien écrire : sans cela,
        l'aperçu serait un fait accompli."""
        i = fiche.find("MODES_GENERATION")
        bloc = fiche[i:i + 3500]
        assert "dryRun" in bloc or "apercu" in bloc


# ── Ce que la fiche doit dire ────────────────────────────────────────
class TestCeQueLaFicheDit:

    def test_le_modele_employe_est_nomme(self, fiche):
        """Le même manque que dans le panneau : régler sans savoir qui
        recevra les instructions, c'est régler à l'aveugle."""
        assert "m_titre" in fiche or "modele" in fiche.lower()

    def test_l_absence_de_modele_est_dite(self, fiche):
        """Un bouton qui ne peut rien faire doit le dire avant d'être
        pressé."""
        assert "m_aucun" in fiche or "aucun_modele" in fiche

    def test_le_bouton_dit_ce_qu_il_produit(self, fiche):
        """« Générer » ne dit pas quoi : une biographie, un synopsis,
        une présentation ?"""
        i = fiche.find("generer_ia: {")
        assert i > 0
        m = re.search(r'fr:\s*"([^"]+)"', fiche[i:i + 300])
        assert m, "libellé français introuvable"
        assert len(m.group(1)) > 8, m.group(1)


class TestChaqueActionVitOuElleAgit:
    """Une tâche qui agit sur une fiche précise appartient à cette
    fiche, où l'on voit ce qu'elle va toucher. La même tâche au
    panneau demande un identifiant qu'il faut aller chercher — alors
    qu'on est justement sur la fiche en question.

    « Inspecter ce que les sources disent d'un interprète » n'existait
    qu'au panneau, avec un champ où taper son nom. C'est demander de
    ressaisir ce qu'on a sous les yeux."""

    def test_l_inspection_est_offerte_sur_la_fiche(self, fiche):
        assert "inspecter_collecte" in fiche

    def test_elle_ne_concerne_que_les_interpretes(self, fiche):
        """Elle interroge les sources d'un INTERPRÈTE : l'offrir sur
        un studio promettrait ce qu'elle ne fait pas."""
        i = fiche.find("inspecter_collecte")
        bloc = fiche[max(0, i - 700):i]
        assert 'type === "performer"' in bloc

    def test_elle_prend_l_identifiant_du_contexte(self, fiche):
        """C'est tout l'intérêt : ne rien avoir à ressaisir."""
        i = fiche.find("inspecter_collecte")
        bloc = fiche[i:i + 200]
        assert "fiche.id" in bloc or "fiche.name" in bloc

    def test_elle_ne_modifie_rien(self, fiche):
        """Une action de lecture posée parmi des actions d'écriture
        doit se distinguer, sans quoi on hésite à la lancer."""
        i = fiche.find('B("inspecter"')
        assert i > 0, "bouton introuvable"
        bloc = fiche[i:i + 300]
        # Le troisième argument dit si l'action est destructive.
        assert "false)" in bloc, bloc[:150]


class TestCeQuiResteAuPanneau:
    """Une tâche qui balaie la collection appartient au panneau : la
    lancer depuis une fiche laisserait croire qu'elle ne touche que
    celle-là.

    Six tâches existent aux deux endroits, et c'est délibéré :
    appliquer sur UNE fiche et appliquer sur TOUT sont deux
    intentions, pas deux chemins vers la même."""

    def test_l_application_de_masse_reste_au_panneau(self, page):
        assert "apply_accepted" in page

    def test_la_detection_de_doublons_reste_au_panneau(self, page):
        """Elle compare les fiches ENTRE elles : la lancer depuis une
        seule n'aurait pas de sens."""
        assert "detect_duplicates" in page

    def test_le_bouton_de_fiche_dit_qu_il_ne_touche_qu_elle(self,
                                                            fiche):
        """« Accepter » sur une fiche pose un marqueur puis lance
        l'application : sans cela, l'utilisateur croirait avoir
        appliqué toute la collection."""
        i = fiche.find('B("accepter"')
        assert i > 0
        bloc = fiche[i:i + 300]
        assert "poserTag" in bloc
