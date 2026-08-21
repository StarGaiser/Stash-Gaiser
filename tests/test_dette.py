# -*- coding: utf-8 -*-
"""
Dette technique : mesurer pour qu'elle ne croisse pas.

Deux sortes de limites cohabitent ici, et les confondre rend le
contrôle inutile.

**Celles qui reposent sur la lecture humaine** sont défendables dans
l'absolu. Une fonction de cent cinquante lignes ne tient pas sur un
écran : on ne la voit jamais entière, donc on la modifie sans la
comprendre. Une complexité au-delà de vingt-cinq dépasse ce qu'on garde
en tête. Un module qui dépend de huit autres n'a plus de frontière.

**Les autres sont inventées.** « Vingt fonctions par module » ne repose
sur rien. Pour celles-là, un CLIQUET : on mesure ce qui existe et on
interdit que ça empire. Le chiffre n'a pas besoin d'être juste — il
doit seulement ne pas monter.

Ce fichier ne cherche pas la beauté du code. Il cherche à ce que la
prochaine version ne soit pas pire que celle-ci.
"""

import ast
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


def _modules():
    return {f.stem: f for f in CODE.glob("*.py")}


def _arbre(fichier):
    return ast.parse(fichier.read_text(encoding="utf-8"))


# ── Limites de lecture ───────────────────────────────────────────────
class TestLisibilite:
    """Ces bornes ne sont pas négociables : elles décrivent ce qu'un
    humain peut tenir sous les yeux, pas une préférence de style."""

    def test_aucune_fonction_ne_depasse_un_ecran_et_demi(self):
        """Au-delà, on ne la voit jamais entière — donc on la modifie
        sans la comprendre. La borne est large à dessein : plusieurs
        tâches longues sont des suites d'étapes lisibles, et les
        découper pour la métrique nuirait à la lecture."""
        fautes = []
        for nom, f in _modules().items():
            for n in _arbre(f).body:
                if isinstance(n, ast.FunctionDef):
                    lignes = n.end_lineno - n.lineno
                    if lignes > 150:
                        fautes.append(f"{nom}.{n.name} ({lignes} l.)")
        assert fautes == [], fautes

    def test_aucun_module_ne_depasse_mille_lignes(self):
        """`rapports.py` en comptait 1519 avant découpage : on n'y
        trouvait plus rien, et chaque ajout aggravait le cas."""
        # `i18n.py` est excepté : ce sont des TABLES de traduction,
        # pas de la logique. Sa longueur croît avec les langues, et la
        # découper disperserait ce qui doit se lire ensemble. Le
        # contrôle porte sur le code qu'on relit pour le comprendre.
        fautes = [f"{nom} ({len(f.read_text().splitlines())} l.)"
                  for nom, f in _modules().items()
                  if nom != "i18n"
                  and len(f.read_text().splitlines()) > 1000]
        assert fautes == [], fautes

    def test_l_imbrication_reste_suivable(self):
        """Cinq niveaux de « si » dans un « pour » dans un « essayer » :
        on perd le fil de ce qui est vrai à chaque ligne."""
        fautes = []
        for nom, f in _modules().items():
            for n in ast.walk(_arbre(f)):
                if not isinstance(n, ast.FunctionDef):
                    continue
                profondeur = self._profondeur(n)
                if profondeur > 5:
                    fautes.append(f"{nom}.{n.name} ({profondeur})")
        assert fautes == [], fautes

    @staticmethod
    def _profondeur(noeud, niveau=0):
        maxi = niveau
        for enfant in ast.iter_child_nodes(noeud):
            suivant = niveau + 1 if isinstance(
                enfant, (ast.If, ast.For, ast.While, ast.Try,
                         ast.With)) else niveau
            maxi = max(maxi, TestLisibilite._profondeur(enfant, suivant))
        return maxi


# ── Frontières entre modules ─────────────────────────────────────────
class TestFrontieres:
    """Un module qui dépend de tout n'a plus de responsabilité propre :
    on ne peut ni le comprendre seul, ni le remplacer, ni le tester
    sans monter la moitié du plugin."""

    def _dependances(self):
        mods = set(_modules())
        sortant = {}
        for nom, f in _modules().items():
            dep = set()
            for n in ast.walk(_arbre(f)):
                if isinstance(n, ast.Import):
                    dep |= {x.name.split(".")[0] for x in n.names}
                elif isinstance(n, ast.ImportFrom) and n.module:
                    dep.add(n.module.split(".")[0])
            sortant[nom] = (dep & mods) - {nom}
        return sortant

    def test_aucun_module_ne_depend_de_tout(self):
        """Le point d'entrée est excepté : son rôle EST de tout
        connaître pour bâtir le registre."""
        fautes = [f"{nom} → {len(dep)}"
                  for nom, dep in self._dependances().items()
                  if nom != "gaizer" and len(dep) > 8]
        assert fautes == [], fautes

    def test_aucun_cycle(self):
        """Deux modules qui s'importent l'un l'autre ne peuvent plus
        être compris ni chargés séparément."""
        dep = self._dependances()
        cycles = sorted({tuple(sorted((a, b)))
                         for a, voisins in dep.items()
                         for b in voisins if a in dep.get(b, ())})
        assert cycles == [], cycles

    def test_le_noyau_ne_depend_que_de_couches_sans_etat(self):
        """Un noyau ne doit dépendre que de modules qui ne
        connaissent rien du plugin : traductions, table de notation,
        catalogue de fournisseurs. Ce sont des DONNÉES qu'il consulte,
        non des services qui le rappelleraient."""
        assert self._dependances()["noyau"] <= {"i18n", "llm",
                                                "scoring"}

    def test_les_modules_de_taches_ne_se_parlent_pas(self):
        """Une table partagée entre deux intentions n'appartient à
        aucune des deux : sa place est dans la couche que toutes
        connaissent. Le cas s'est présenté et a été corrigé ainsi."""
        dep = self._dependances()
        fautes = [f"{a} → {b}"
                  for a, voisins in dep.items()
                  if a.startswith("taches_")
                  for b in voisins if b.startswith("taches_")]
        assert fautes == [], fautes


# ── Complexité ───────────────────────────────────────────────────────
@pytest.mark.skipif(shutil.which("radon") is None,
                    reason="radon non installé")
class TestComplexite:

    def _mesures(self):
        r = subprocess.run(["radon", "cc", "gaizer/", "-j"],
                           capture_output=True, text=True,
                           cwd=RACINE, check=False)
        try:
            brut = json.loads(r.stdout or "{}")
        except json.JSONDecodeError:
            return []
        return [(f"{Path(f).stem}.{b['name']}", b["complexity"])
                for f, blocs in brut.items()
                if isinstance(blocs, list) for b in blocs]

    def test_aucune_fonction_illisible(self):
        """Au-delà de 25 chemins d'exécution, personne ne tient la
        fonction en tête — donc personne ne peut affirmer qu'elle est
        juste.

        `scoring.evaluer` était à 42 : c'est le cœur de l'arbitrage,
        celui dont dépend chaque valeur écrite. Il a été découpé."""
        fautes = [f"{nom} ({c})" for nom, c in self._mesures() if c > 25]
        assert fautes == [], fautes

    def test_la_moyenne_ne_derive_pas(self):
        """Un cliquet, non une vérité : le chiffre n'a pas à être
        juste, il doit ne pas monter."""
        mesures = self._mesures()
        if not mesures:
            pytest.skip("radon muet")
        moyenne = sum(c for _n, c in mesures) / len(mesures)
        assert moyenne <= 10.5, f"moyenne {moyenne:.1f}"


# ── Cliquets ─────────────────────────────────────────────────────────
class TestCliquets:
    """Ces bornes ne prétendent à aucune vérité. Elles figent l'état
    atteint pour qu'il ne se dégrade pas sans qu'on le remarque.

    Les baisser quand le code s'améliore fait partie du travail ; les
    monter demande une raison écrite."""

    def test_le_nombre_de_modules_reste_maitrise(self):
        """Trop de modules disperse autant que trop peu concentre."""
        # Le seuil borne l'ÉPARPILLEMENT, non la croissance :
        # « profil.py » regroupe une responsabilité qui vivait
        # nulle part — deviner l'orientation d'une collection.
        assert len(_modules()) <= 31

    def test_aucun_module_n_accumule_les_taches(self):
        """Le seuil vient de l'expérience : au-delà d'une dizaine de
        tâches, un module cesse d'avoir une intention et redevient un
        fourre-tout — c'est exactement ce qui est arrivé."""
        fautes = []
        for nom, f in _modules().items():
            publiques = [n.name for n in _arbre(f).body
                         if isinstance(n, ast.FunctionDef)
                         and not n.name.startswith("_")]
            if len(publiques) > 12:
                fautes.append(f"{nom} ({len(publiques)})")
        assert fautes == [], fautes

    def test_la_dette_signalee_ne_croit_pas(self):
        """Le nombre de remarques d'outils tolérées. Chacune est
        justifiée dans `pyproject.toml` ; leur nombre ne doit pas
        augmenter à la faveur d'un ajout."""
        if shutil.which("ruff") is None:
            pytest.skip("ruff non installé")
        r = subprocess.run(
            ["ruff", "check", ".", "--output-format", "json"],
            capture_output=True, text=True, cwd=RACINE, check=False)
        try:
            erreurs = json.loads(r.stdout or "[]")
        except json.JSONDecodeError:
            erreurs = []
        assert len(erreurs) <= 115, Counter(
            e["code"] for e in erreurs).most_common(5)

    def test_aucun_marqueur_de_travail_inacheve(self):
        """Un « TODO » dans le code est une dette qu'on a choisi de ne
        pas écrire ailleurs. Sa place est dans `docs/CHANTIERS.md`, où
        on la relit ; dans le code, on cesse de la voir."""
        # Le marqueur doit être une ANNOTATION, non un mot qui passe
        # par là : « XXX » est un sigle de studio dans ce domaine, et
        # le chercher n'importe où produisait un faux positif dans une
        # phrase d'explication.
        import re as _re
        motif = _re.compile(r"#\s*(TODO|FIXME|HACK)\b")
        fautes = []
        for nom, f in _modules().items():
            for i, ligne in enumerate(
                    f.read_text(encoding="utf-8").split("\n"), 1):
                if motif.search(ligne):
                    fautes.append(f"{nom}:{i}")
        assert fautes == [], fautes

    def test_aucun_code_commente(self):
        """Du code mis en commentaire ment sur ce que fait le
        programme, et l'historique le conserve de toute façon."""
        fautes = []
        for nom, f in _modules().items():
            for i, ligne in enumerate(
                    f.read_text(encoding="utf-8").split("\n"), 1):
                nu = ligne.strip().lstrip("#").strip()
                if not ligne.strip().startswith("#"):
                    continue
                if (nu.startswith(("def ", "class ", "return ",
                                   "import ", "for ", "if "))
                        and nu.endswith((":", ")"))):
                    fautes.append(f"{nom}:{i}")
        assert fautes == [], fautes
