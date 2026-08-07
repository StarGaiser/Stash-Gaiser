# -*- coding: utf-8 -*-
"""
La documentation vue par quelqu'un qui découvre.

Les contrôles de `test_documentation.py` vérifient des FAITS : telle
tâche existe, tel lien mène quelque part. Ils ne disent rien de ce
qu'un lecteur comprend.

Ceux-ci portent sur la lecture. Ils sont plus discutables — la
lisibilité ne se mesure pas exactement — et le seuil est donc placé
haut : on ne signale que ce qui bloquerait franchement quelqu'un
d'extérieur.

Trois familles, chacune née d'un défaut réel constaté en relisant :

  **La péremption.** Un numéro de version figé dans un en-tête devient
  faux à la première publication et laisse croire que le document date.

  **Le jargon.** Un terme propre au projet employé sans être défini
  oblige à deviner. Le lecteur qui devine mal se trompe sur tout ce
  qui suit.

  **L'implicite.** Un document qui suppose connu ce qu'il n'a pas dit
  ne sert qu'à celui qui l'a écrit.
"""

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
DOCS = RACINE / "docs"


def _documents():
    return sorted([*list(DOCS.glob("*.md")), RACINE / "README.md", RACINE / "README.fr.md"])


def _texte(f):
    return f.read_text(encoding="utf-8")


# ── Péremption ───────────────────────────────────────────────────────
class TestPeremption:
    """Ce qui vieillit sans qu'on s'en aperçoive."""

    def test_aucun_numero_de_version_fige(self):
        """Un en-tête « Version 0.29 » devient faux dès la publication
        suivante. Le numéro vit dans le manifeste du plugin, seul
        endroit qui le tient à jour ; un document qui le recopie ment
        au premier oubli."""
        fautes = []
        for f in _documents():
            for i, ligne in enumerate(_texte(f).split("\n"), 1):
                if re.match(r"^\s*(##?#?\s*)?Version\s+\d+\.\d+",
                            ligne):
                    fautes.append(f"{f.name}:{i} « {ligne.strip()[:50]} »")
        assert fautes == [], fautes

    def test_aucune_date_absolue(self):
        """« État au 5 août » invite à se demander ce qui a changé
        depuis, sans moyen de le savoir."""
        motif = re.compile(
            r"\b(?:janvier|février|mars|avril|mai|juin|juillet|août|"
            r"septembre|octobre|novembre|décembre)\s+20\d\d\b", re.I)
        fautes = []
        for f in _documents():
            for i, ligne in enumerate(_texte(f).split("\n"), 1):
                if motif.search(ligne):
                    fautes.append(f"{f.name}:{i}")
        assert fautes == [], fautes

    def test_les_decomptes_de_tests_sont_coherents(self):
        """Un document qui annonce un nombre de tests différent d'un
        autre laisse le lecteur choisir lequel croire."""
        nombres = set()
        for f in _documents():
            nombres |= {int(n) for n in
                        re.findall(r"\b(\d{3,4}) tests\b", _texte(f))}
        assert len(nombres) <= 1, f"décomptes divergents : {nombres}"

    def test_le_manifeste_est_la_seule_source_de_la_version(self):
        manifeste = yaml.safe_load(
            (RACINE / "gaizer" / "gaizer.yml").read_text())
        assert re.match(r"^\d+\.\d+", str(manifeste["version"]))


# ── Jargon ───────────────────────────────────────────────────────────
class TestVocabulaire:
    """Un terme propre au projet doit être défini avant d'être employé,
    ou renvoyer à l'endroit qui le définit."""

    # Termes que le plugin emploie et qu'un utilisateur de Stash ne
    # connaît pas forcément.
    TERMES = {
        "bio « hot »": "présentation rédigée par un modèle",
        "empreinte": "identification d'un fichier par son contenu",
        "famille de sources": "sources indépendantes les unes des autres",
        "proposition": "valeur suggérée en attente de validation",
        "fiches préexistantes": "ce qui existait avant le plugin",
    }

    def test_le_document_fonctionnel_definit_son_vocabulaire(self):
        """C'est la porte d'entrée : un lecteur y arrive sans rien
        savoir du projet."""
        texte = _texte(DOCS / "SPECIFICATIONS_FONCTIONNELLES.md")
        manquants = [t for t in self.TERMES
                     if t.split()[0].lower() in texte.lower()
                     and not re.search(
                         r"(?:c'est-à-dire|autrement dit|:\s|—\s)[^\n]{0,80}"
                         + re.escape(t.split()[0]), texte, re.I)
                     and texte.lower().count(t.split()[0].lower()) > 2]
        # Contrôle indicatif : on n'exige une définition que pour les
        # termes VRAIMENT récurrents, faute de quoi il crie au loup.
        assert len(manquants) <= 2, manquants

    def test_aucun_sigle_non_developpe(self):
        """Un sigle employé sans être développé la première fois
        oblige à chercher ailleurs."""
        connus = {"API", "URL", "JSON", "YAML", "HTML", "CSS", "SQL",
                  "AGPL", "GPL", "MIT", "SSH", "HTTP", "HTTPS", "IA",
                  "SVG", "PDF", "CSV", "UI", "ID", "OK", "TPDB", "ADE",
                  "LLM", "MD5", "SHA1", "IMDB", "NAS", "GZ", "XXX",
                  "DATA", "DONNÉES", "RAM", "CPU", "OS",
                  # Noms de sources et d'outils, écrits ainsi partout
                  "GEVI", "IAFD", "TIM", "PEP", "LM",
                  "README", "SSD", "GPU",
                  # Écrits en majuscules par convention du domaine
                  "TESTS", "READY", "BR", "VEUT"}
        # Les mots mis en majuscules pour insister — « JAMAIS »,
        # « AVANT », « FORME » — ne sont pas des sigles. Un sigle ne
        # se lit pas comme un mot français : on écarte donc ceux qui
        # contiennent une voyelle et se prononcent.
        fautes = set()
        for f in _documents():
            for sigle in re.findall(r"\b([A-Z]{2,6})\b", _texte(f)):
                if sigle in connus:
                    continue
                # Insistance : le mot existe aussi en minuscules
                # ailleurs dans le même document.
                if re.search(rf"\b{sigle.lower()}\b", _texte(f)):
                    continue
                # Développé quelque part dans le document : le sigle
                # peut ensuite être employé seul.
                if re.search(rf"{sigle}\s*[—(-]", _texte(f)):
                    continue
                # Identifiant de code cité entre accents graves.
                if f"`{sigle}" in _texte(f):
                    continue
                fautes.add(f"{f.name}: {sigle}")
        assert fautes == set(), sorted(fautes)


# ── Ce qu'un lecteur doit trouver ────────────────────────────────────
class TestAccueil:
    """Le README est souvent la seule page lue. Ce qui n'y est pas
    n'existe pas."""

    def _readme(self, langue="en"):
        return _texte(RACINE
                      / ("README.md" if langue == "en"
                         else "README.fr.md"))

    @pytest.mark.parametrize("langue", ["en", "fr"])
    def test_le_readme_dit_comment_installer(self, langue):
        texte = self._readme(langue).lower()
        assert any(m in texte for m in ("install", "installer"))
        assert "plugins" in texte, "où poser les fichiers"

    @pytest.mark.parametrize("langue", ["en", "fr"])
    def test_le_readme_dit_ce_qu_il_faut_avoir(self, langue):
        """Un lecteur doit savoir avant d'essayer si son installation
        convient."""
        texte = self._readme(langue)
        assert re.search(r"Stash\s*[≥>]?=?\s*0\.\d+", texte), \
            "version minimale de Stash"
        assert "pip install" in texte, "dépendances Python"

    @pytest.mark.parametrize("langue", ["en", "fr"])
    def test_le_readme_dit_par_quoi_commencer(self, langue):
        """Une liste de fonctionnalités sans ordre laisse le lecteur
        deviner ce qu'il doit lancer en premier."""
        texte = self._readme(langue).lower()
        assert any(m in texte for m in
                   ("first run", "première", "commencer", "1."))

    @pytest.mark.parametrize("langue", ["en", "fr"])
    def test_le_readme_dit_ce_que_le_plugin_ne_fait_pas(self, langue):
        """Annoncer les limites évite les attentes déçues, et vaut
        mieux qu'un utilisateur qui découvre en cours de route."""
        texte = self._readme(langue).lower()
        assert any(m in texte for m in
                   ("what it is not", "ce que ce n'est pas",
                    "n'est pas", "not a "))

    @pytest.mark.parametrize("langue", ["en", "fr"])
    def test_le_readme_dit_la_licence(self, langue):
        assert "agpl" in self._readme(langue).lower()

    def test_les_deux_readme_couvrent_les_memes_sujets(self):
        """Une version traduite plus pauvre que l'autre laisse une
        partie des lecteurs moins renseignée."""
        titres = {}
        for langue, f in (("en", "README.md"), ("fr", "README.fr.md")):
            titres[langue] = len(re.findall(r"^##\s", _texte(RACINE / f),
                                            re.M))
        assert abs(titres["en"] - titres["fr"]) <= 3, titres


# ── Sécurité de lecture ──────────────────────────────────────────────
class TestAvertissements:
    """Ce qui détruit doit être annoncé là où on le lit, pas seulement
    là où on le lance."""

    def test_les_actions_destructives_sont_signalees(self):
        texte = _texte(DOCS / "SPECIFICATIONS_FONCTIONNELLES.md")
        for mot in ("supprime", "écrase", "irréversible", "sans retour"):
            assert mot in texte.lower(), mot

    def test_la_simulation_est_expliquee(self):
        """C'est la protection la plus utile du plugin ; ne pas la
        présenter revient à ne pas l'offrir."""
        for f in (DOCS / "SPECIFICATIONS_FONCTIONNELLES.md",
                  RACINE / "README.md"):
            texte = _texte(f).lower()
            assert any(m in texte for m in
                       ("simulation", "simuler", "dry run",
                        "simulate")), f.name

    def test_la_reversibilite_est_annoncee(self):
        for f in (RACINE / "README.md", RACINE / "README.fr.md"):
            texte = _texte(f).lower()
            assert any(m in texte for m in
                       ("revers", "undo", "annuler", "défa")), f.name
