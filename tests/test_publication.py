# -*- coding: utf-8 -*-
"""
Ce que CommunityScripts attend d'un plugin publié.

Écrit AVANT les corrections.

Le dépôt officiel pose des conditions explicites, dont une que le
plugin ne remplissait pas : **l'usage d'un modèle de langage doit être
divulgué ouvertement**. Elle figure noir sur blanc dans leur README,
et l'ignorer n'est pas un oubli de forme — c'est une condition
d'acceptation.

Les autres exigences tiennent à la structure : un manifeste valide, un
nom de dossier qui correspond, une licence compatible, et de quoi
qu'un utilisateur comprenne ce qu'il installe.

Ces contrôles ne garantissent pas l'acceptation — un humain relit —
mais ils écartent les motifs de refus mécaniques.
"""

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


@pytest.fixture(scope="module")
def manifeste():
    return yaml.safe_load(
        (CODE / "gaizer.yml").read_text(encoding="utf-8"))


def _lire(nom):
    f = RACINE / nom
    return f.read_text(encoding="utf-8") if f.exists() else ""


# ── Conditions explicites du dépôt ───────────────────────────────────
class TestConditionsExplicites:
    """CommunityScripts autorise les contributions assistées par un
    modèle de langage à quatre conditions, dont la première est la
    divulgation ouverte.

    Le taire serait un manquement, pas une omission : c'est une
    condition d'acceptation, et le lecteur a le droit de savoir
    comment le code a été écrit avant de l'installer."""

    def test_l_usage_d_un_modele_est_divulgue(self):
        for readme in ("README.md", "README.fr.md"):
            texte = _lire(readme).lower()
            assert any(m in texte for m in
                       ("llm", "language model", "modèle de langage",
                        "ai-assisted", "assisté par")), readme

    def test_la_relecture_humaine_est_affirmee(self):
        """Deuxième condition : le code est relu par un humain."""
        texte = _lire("README.md").lower()
        assert "review" in texte or "reviewed" in texte

    def test_la_validation_par_essai_est_affirmee(self):
        """Troisième condition : essais et validation humains."""
        texte = _lire("README.md").lower()
        assert "test" in texte

    def test_la_licence_est_compatible(self):
        """Stash est sous AGPL : une licence non commerciale ou
        propriétaire rendrait le plugin inéligible."""
        licence = _lire("LICENSE")
        assert "AGPL" in licence or "GNU AFFERO" in licence.upper()


# ── Structure du plugin ──────────────────────────────────────────────
class TestStructure:
    """Stash lit un manifeste YAML dans un dossier portant le nom du
    plugin. Une divergence empêche le chargement, sans message
    utile."""

    def test_le_manifeste_porte_le_nom_du_dossier(self):
        assert (CODE / f"{CODE.name}.yml").exists()

    def test_les_champs_obligatoires_sont_presents(self, manifeste):
        for champ in ("name", "description", "version", "exec",
                      "interface"):
            assert manifeste.get(champ), champ

    def test_la_version_suit_un_format_lisible(self, manifeste):
        assert re.match(r"^\d+\.\d+(\.\d+)?$",
                        str(manifeste["version"])), manifeste["version"]

    def test_l_url_du_projet_est_declaree(self, manifeste):
        """Sans elle, personne ne sait où signaler un défaut."""
        assert manifeste.get("url")

    def test_la_description_tient_en_une_phrase(self, manifeste):
        """Elle s'affiche dans la liste des plugins de Stash, sur une
        ligne."""
        assert 20 <= len(str(manifeste["description"])) <= 200

    def test_aucune_dependance_non_declaree(self):
        """Un plugin qui échoue à l'exécution faute d'une
        bibliothèque absente est pire qu'un plugin qui refuse de
        s'installer : l'utilisateur ne comprend pas."""
        obligatoires = set()
        for f in CODE.glob("*.py"):
            texte = f.read_text(encoding="utf-8")
            for m in re.finditer(r"^import (\w+)|^from (\w+) import",
                                 texte, re.M):
                nom = m.group(1) or m.group(2)
                obligatoires.add(nom)
        # Ce qui vient de la bibliothèque standard ou de Stash.
        connus = {
            "os", "re", "sys", "json", "time", "math", "html",
            "base64", "hashlib", "datetime", "pathlib", "typing",
            "collections", "itertools", "functools", "unicodedata",
            "urllib", "difflib", "random", "io", "csv", "textwrap",
            "contextlib", "dataclasses", "enum", "copy", "shutil",
            "stashapi", "__future__", "yaml",
        }
        # Les modules du plugin lui-même.
        connus |= {f.stem for f in CODE.glob("*.py")}
        externes = sorted(obligatoires - connus)
        assert externes == [], externes


# ── Ce qu'un utilisateur doit comprendre ─────────────────────────────
class TestAccueil:
    """Quelqu'un qui découvre le plugin sur une liste doit savoir en
    trente secondes ce qu'il fait, ce qu'il exige, et ce qu'il envoie
    au dehors."""

    def test_le_readme_dit_ce_que_le_plugin_fait(self):
        texte = _lire("README.md")
        assert len(texte) > 800

    def test_les_prerequis_sont_annonces(self):
        texte = _lire("README.md").lower()
        assert "stash" in texte and ("requir" in texte
                                     or "prerequis" in texte
                                     or "need" in texte)

    def test_ce_qui_sort_de_la_machine_est_annonce(self):
        """Un plugin qui transmet des données à des tiers doit le dire
        avant l'installation, non dans un réglage qu'on découvre
        après."""
        texte = _lire("README.md").lower()
        assert any(m in texte for m in
                   ("sends", "sent to", "third-party", "external"))

    def test_le_caractere_destructif_est_annonce(self):
        """Fusionner supprime une fiche : le taire dans l'accueil
        serait une omission grave."""
        texte = _lire("README.md").lower()
        assert any(m in texte for m in ("merge", "delete", "destruct",
                                        "irreversible"))

    def test_l_installation_est_expliquee(self):
        texte = _lire("README.md").lower()
        assert "install" in texte

    def test_aucune_promesse_invérifiable(self):
        """« Le meilleur », « parfait », « automatique à 100 % » :
        un accueil qui promet trop se retourne contre le plugin."""
        texte = _lire("README.md").lower()
        for mot in ("best plugin", "perfect", "100%", "flawless",
                    "never fails"):
            assert mot not in texte, mot


class TestWorkflowDePublication:
    """Le workflow échouait en neuf secondes à chaque poussée : il
    employait PyYAML, que le runner GitHub n'embarque pas.

    Personne ne l'avait vu parce que rien ne l'éprouve — un workflow
    ne s'exécute que sur GitHub, et son échec arrive par courriel
    qu'on finit par ignorer.

    Il lit désormais le manifeste avec `sed`, ce qui supprime la
    dépendance mais introduit une hypothèse : les deux champs lus
    doivent tenir sur une seule ligne, sans guillemets. Ces tests
    protègent cette hypothèse, que rien d'autre ne garantit."""

    def _workflow(self):
        """Le gabarit vit dans `tools/` : il n'est posé dans
        `.github/` que sur le dépôt public, où Pages existe."""
        f = RACINE / "tools" / "index-source.yml"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def test_le_workflow_existe(self):
        assert self._workflow(), "aucun workflow de publication"

    def test_il_ne_depend_d_aucune_bibliotheque_absente(self):
        """`ubuntu-latest` n'embarque ni PyYAML ni la plupart des
        paquets Python : ce qui n'est pas installé doit être évité."""
        w = self._workflow()
        assert "import yaml" not in w, \
            "PyYAML n'est pas installé sur le runner"

    def test_la_version_tient_sur_une_ligne(self, manifeste):
        """Le workflow la lit avec `sed` : une version sur plusieurs
        lignes casserait la publication sans que rien ne le dise
        avant la poussée."""
        brut = (CODE / "gaizer.yml").read_text(encoding="utf-8")
        lignes = [x for x in brut.split("\n")
                  if x.startswith("version:")]
        assert len(lignes) == 1, lignes
        assert str(manifeste["version"]) in lignes[0]

    def test_la_description_tient_sur_une_ligne(self, manifeste):
        brut = (CODE / "gaizer.yml").read_text(encoding="utf-8")
        lignes = [x for x in brut.split("\n")
                  if x.startswith("description:")]
        assert len(lignes) == 1, lignes

    def test_la_description_n_a_pas_de_guillemets(self):
        """Ils casseraient le YAML produit par le workflow."""
        brut = (CODE / "gaizer.yml").read_text(encoding="utf-8")
        ligne = next(x for x in brut.split("\n")
                     if x.startswith("description:"))
        valeur = ligne.split(":", 1)[1]
        assert '"' not in valeur, valeur

    def test_l_archive_porte_le_nom_du_plugin(self):
        """Un nom divergent rend le plugin introuvable pour Stash."""
        assert "gaizer.zip" in self._workflow()


class TestWorkflowSurLeBonDepot:
    """L'index de source n'a de sens que sur le dépôt PUBLIC : c'est
    lui que Stash interroge pour installer le plugin.

    Sur le dépôt privé, GitHub Pages n'est même pas disponible sans
    abonnement payant — le workflow y échouait donc à chaque poussée,
    envoyant un courriel d'échec pour une publication que personne
    n'attend.

    Le fichier vit dans le dossier de publication, non dans le dépôt
    de travail, et le script de publication l'y dépose."""

    def test_le_workflow_n_est_pas_dans_le_depot_de_travail(self):
        f = RACINE / ".github" / "workflows" / "index-source.yml"
        assert not f.exists(), \
            "le workflow échoue sur un dépôt privé sans Pages"

    def test_le_script_de_publication_le_depose(self):
        """Sans cela, le dépôt public perdrait sa publication à la
        prochaine régénération."""
        script = (RACINE / "tools" /
                  "preparer_publication.sh").read_text(
                      encoding="utf-8")
        assert "index-source" in script

    def test_le_gabarit_du_workflow_est_conserve(self):
        """Le retirer sans le garder quelque part le ferait
        disparaître à la première régénération."""
        gabarit = RACINE / "tools" / "index-source.yml"
        assert gabarit.exists(), gabarit


class TestHistoriquePublic:
    """Le dépôt public était régénéré à chaque publication : « git
    init » puis un commit unique, écrasant tout. Chaque publication
    effaçait la précédente.

    C'est ce qui protégeait l'anonymat au début — l'historique privé
    porte des dates, des rythmes de travail, des tâtonnements qui
    disent des choses sur qui écrit. Mais une fois le dépôt public
    ouvert, repartir de zéro à chaque fois a un coût : personne ne
    peut voir ce qui a changé, ni suivre le projet.

    L'historique commence donc AU PROCHAIN PUBLICATION, sans reprendre
    le passé : ce qui a précédé reste privé, ce qui suit est visible.

    Trois conditions, chacune vérifiable :
    — le message de publication ne doit porter aucune trace
      personnelle, puisqu'il sera public ;
    — l'identité des commits reste pseudonyme ;
    — l'historique existant n'est jamais écrasé par une poussée
      forcée, sans quoi le problème reviendrait.
    """

    def _script(self):
        return (RACINE / "tools" /
                "preparer_publication.sh").read_text(encoding="utf-8")

    def test_l_historique_distant_est_repris(self):
        """Sans cela, chaque publication repart de zéro."""
        s = self._script()
        assert "git fetch" in s or "git clone" in s, \
            "le script doit reprendre l'historique distant"

    def test_l_identite_reste_pseudonyme(self):
        s = self._script()
        assert 'user.name "gaizer"' in s
        assert "noreply.github.com" in s

    def test_l_identite_reste_locale_au_depot(self):
        """Toucher la configuration globale changerait l'identité de
        tous les autres dépôts de la machine."""
        s = self._script()
        assert "--global" not in s

    def test_le_message_de_publication_est_controle(self):
        """Il sera public : une trace personnelle y serait aussi
        visible que dans un fichier."""
        # Le contrôle vit dans un outil à part : écrire les motifs
        # dans le script les aurait PUBLIÉS, ce qui révélerait
        # précisément ce qu'ils protègent.
        assert "auditer_message.py" in self._script()
        outil = RACINE / "tools" / "auditer_message.py"
        assert outil.exists()
        assert "message_sans_trace" in outil.read_text(
            encoding="utf-8")

    def test_aucune_poussee_forcee_dans_le_script(self):
        """Une poussée forcée écraserait l'historique qu'on vient de
        se donner la peine de conserver."""
        s = self._script()
        assert "push --force" not in s and "push -f" not in s

    def test_le_fichier_de_passation_n_est_pas_publie(self):
        """AGENTS.md porte les chemins réels de la machine et
        l'adresse des deux dépôts. C'est un document de TRAVAIL :
        utile à qui reprend le projet, sans objet pour qui installe
        le plugin, et sa publication trahirait l'anonymat que tout le
        reste protège."""
        s = self._script()
        assert "rm -f AGENTS.md" in s
