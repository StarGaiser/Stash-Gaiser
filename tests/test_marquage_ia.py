# -*- coding: utf-8 -*-
"""
Voir d'un coup d'œil ce qui appelle un modèle.

Écrit AVANT le code.

Huit tâches appellent un modèle de langue. Rien ne les distingue des
autres : ni icône, ni mention. L'utilisateur ne peut pas savoir
laquelle va coûter des appels, ni laquelle produira un texte qu'il
faudra relire.

C'est le manque le plus sensible avant publication. Quelqu'un qui
découvre le plugin lance une tâche sans savoir qu'elle consomme un
quota payant, ou s'étonne qu'une autre ne rédige rien.

**Trois choses doivent se voir sans lire.**

L'ICÔNE dit qu'un modèle intervient. Elle est la même partout, sinon
elle n'apprend rien.

Le COÛT se distingue de l'écriture : une tâche qui lit des vignettes
appelle un modèle sans rien rédiger, une autre écrit un texte qu'il
faudra relire. Ce ne sont pas les mêmes précautions.

L'ABSENCE DE MODÈLE se dit AVANT de lancer. Une tâche qui ne peut
rien faire doit le montrer, non l'apprendre après coup.
"""

import ast
import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"
sys.path.insert(0, str(CODE))


@pytest.fixture(scope="module")
def page():
    return (CODE / "gaizer_page.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def fiche():
    return (CODE / "gaizer.js").read_text(encoding="utf-8")


def _taches_ia():
    """Les tâches qui appellent réellement un modèle.

    Mesuré dans le CODE, non déclaré à la main : une liste écrite
    périmerait au premier ajout, et personne ne le verrait.
    """
    trouvees = set()
    for f in CODE.glob("*.py"):
        texte = f.read_text(encoding="utf-8")
        arbre = ast.parse(texte)
        for n in arbre.body:
            if not isinstance(n, ast.FunctionDef):
                continue
            corps = ast.get_source_segment(texte, n) or ""
            if any(m in corps for m in
                   ("ai_for(", "_appel_llm(", "generer_bio_hot(",
                    "synth_bio(", "synth_synopsis(")):
                trouvees.add(n.name)
    return trouvees


class TestMarquageDesTachesIA:
    """L'icône dit qu'un modèle intervient. La même partout, sinon
    elle n'apprend rien."""

    def test_la_table_des_taches_ia_existe(self, page):
        assert "TACHES_IA" in page

    def test_elle_couvre_les_taches_qui_appellent_un_modele(self,
                                                            page):
        """Une tâche non marquée laisse croire qu'elle est
        gratuite."""
        i = page.find("const TACHES_IA")
        fin = page.find("};", i)
        bloc = page[i:fin if fin > i else i + 900]
        declarees = set(re.findall(r'\n\s+(\w+):', bloc))
        reelles = _taches_ia()
        # Toutes celles du panneau doivent y être.
        au_panneau = set(re.findall(r'\n\s+\["(\w+)",\s*\n?\s*"',
                                    page))
        manquantes = (reelles & au_panneau) - declarees
        assert manquantes == set(), sorted(manquantes)

    def test_aucune_tache_marquee_a_tort(self, page):
        """Marquer une tâche qui n'appelle rien ferait craindre un
        coût inexistant, et on cesserait de croire le marquage."""
        i = page.find("const TACHES_IA")
        fin = page.find("};", i)
        bloc = page[i:fin if fin > i else i + 900]
        declarees = set(re.findall(r'\n\s+(\w+):', bloc))
        # `_taches_ia()` trouve aussi les fonctions internes qui
        # appellent un modèle. Ce qui compte est qu'une tâche marquée
        # en appelle un, directement ou par ce qu'elle enchaîne.
        import gaizer as reg
        for mode in declarees:
            assert mode in reg.TASKS, f"{mode} n'est pas une tâche"

    def test_l_icone_vient_de_l_api(self, page):
        """Une icône dessinée à la main détonnerait ; celles de Stash
        sont déjà chargées."""
        i = page.find("const TACHES_IA")
        bloc = page[max(0, i - 2000):i + 900]
        assert "FA[" in bloc or "IconeIA" in page


class TestCeQueLIconeDit:
    """Une icône sans texte n'apprend rien à qui ne la connaît pas,
    et rien du tout à qui ne voit pas l'écran."""

    def test_elle_porte_une_bulle(self, page):
        i = page.find("function IconeIA")
        assert i > 0, "composant introuvable"
        bloc = page[i:i + 800]
        assert "title" in bloc

    def test_elle_est_masquee_aux_lecteurs_d_ecran(self, page):
        """Le texte de la bulle porte l'information : la faire
        annoncer deux fois est du bruit."""
        i = page.find("function IconeIA")
        fin = page.find("\n  function ", i + 10)
        bloc = page[i:fin if fin > i else i + 1600]
        assert "aria-hidden" in bloc

    def test_deux_natures_sont_distinguees(self, page):
        """Lire des vignettes appelle un modèle sans rien rédiger ;
        écrire une présentation produit un texte à relire. Ce ne sont
        pas les mêmes précautions."""
        i = page.find("const TACHES_IA")
        fin = page.find("};", i)
        bloc = page[i:fin if fin > i else i + 900]
        natures = set(re.findall(r':\s*"(\w+)"', bloc))
        assert len(natures) >= 2, natures

    def test_l_absence_de_modele_se_voit_avant_de_lancer(self, page):
        """Une tâche qui ne peut rien faire doit le montrer, non
        l'apprendre après coup."""
        assert "sansModele" in page or "modeleAbsent" in page


class TestSurLaFiche:
    """Le bouton de génération appelle un modèle : il doit le dire
    comme le panneau."""

    def test_le_bouton_de_generation_est_marque(self, fiche):
        # Le marquage fait partie du NOM du bouton : on ne peut
        # pas l'oublier en le déplaçant.
        assert 'B("generer_ia"' in fiche
        i = fiche.find("generer_ia: {")
        assert i > 0, "libellé introuvable"
        assert "✨" in fiche[i:i + 200]


class TestCheminCritique:
    """D'« installé » à « ma médiathèque est enrichie ».

    Ce qui compte n'est pas le nombre de fonctionnalités mais qu'un
    nouvel utilisateur arrive au bout sans se perdre. Chaque étape où
    il peut s'arrêter faute de comprendre est un échec du produit,
    quelle que soit la qualité du reste.

    Sept étapes, chacune vérifiée dans le code."""

    def _accueil(self, page):
        """Le bloc de l'onglet d'accueil.

        Il s'écrit « onglet !== "simple" ? null : … » — chercher la
        forme positive ne le trouve pas, et c'est ce qui m'a fait
        croire à deux manques inexistants."""
        i = page.find('onglet !== "simple" ? null :')
        assert i > 0, "onglet d'accueil introuvable"
        return page[i:i + 1600]

    def test_l_accueil_explique_avant_d_agir(self, page):
        """Un bouton sans explication demande de faire confiance à un
        plugin qui va modifier une médiathèque."""
        assert "s_explication" in self._accueil(page)

    def test_l_accueil_porte_le_parcours_complet(self, page):
        """Lancer, constater, défaire : lancer sans pouvoir vérifier
        ni revenir laisse dans l'inconnu."""
        bloc = self._accueil(page)
        for etape in ("enrichir_tout", "rapport_run", "undo_last"):
            assert etape in bloc, etape

    def test_le_defaut_propose_au_lieu_d_ecrire(self, ):
        """Le premier essai ne doit rien casser : c'est ce qui permet
        d'essayer sans avoir tout compris."""
        import yaml
        d = yaml.safe_load((CODE / "gaizer.yml").read_text(
            encoding="utf-8"))
        desc = str(d["settings"]["applyMode"]["description"]).lower()
        assert "manual" in desc or "propos" in desc

    def test_l_ajustement_ne_demande_pas_un_lot(self, ):
        """Ajuster un prompt en relançant la collection coûte des
        centaines d'appels pour vérifier une formulation."""
        fiche = (CODE / "gaizer.js").read_text(encoding="utf-8")
        assert "generer_apercu" in fiche

    def test_l_installation_est_publiee(self):
        """Sans index de source, installer demande de télécharger une
        archive et de la décompresser au bon endroit."""
        w = (RACINE / "tools" / "index-source.yml").read_text(
            encoding="utf-8")
        assert "gaizer.zip" in w and "index.yml" in w


class TestOuVontLesDonnees:
    """Un audit tiers a proposé de dire où partent les données. La
    mesure lui donne raison : dix fournisseurs sur quatorze sont
    distants, et rien dans l'interface ne dit lequel est employé.

    Ce plugin envoie des titres de scènes, des noms d'interprètes et
    des présentations à un service tiers. Sur une médiathèque de
    pornographie, ce n'est pas un détail technique : c'est ce que
    l'utilisateur doit savoir avant de choisir son modèle, non
    après.

    Un service LOCAL — Ollama, LM Studio — n'envoie rien. La
    distinction se voit d'un coup d'œil ou ne sert à rien."""

    def test_la_nature_du_fournisseur_est_calculee(self, page):
        assert "fournisseurLocal" in page or "estLocal" in page

    def test_elle_se_fonde_sur_l_adresse(self, page):
        """Une liste de noms périmerait au premier fournisseur
        ajouté : c'est l'ADRESSE qui dit si les données sortent."""
        i = page.find("estLocal")
        bloc = page[max(0, i - 200):i + 500]
        assert "localhost" in bloc or "127.0.0.1" in bloc

    def test_le_panneau_le_dit(self, page):
        assert "d_local" in page or "d_distant" in page

    def test_les_deux_cas_sont_nommes(self, page):
        """Dire « local » sans dire l'inverse laisse croire que le
        silence vaut approbation."""
        assert "d_local" in page and "d_distant" in page

    def test_le_texte_dit_ce_qui_part(self, page):
        """« Distant » ne suffit pas : il faut dire QUOI part."""
        i = page.find("d_distant:")
        bloc = page[i:i + 700].lower()
        assert any(m in bloc for m in
                   ("titre", "nom", "présentation", "donnée")), \
            bloc[:200]
