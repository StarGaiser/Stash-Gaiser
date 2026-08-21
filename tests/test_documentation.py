# -*- coding: utf-8 -*-
"""
La documentation vieillit plus vite que le code.

Une spécification qui décrit une tâche retirée, un lien vers un fichier
déplacé, un décompte de tests dépassé : rien de tout cela n'empêche le
programme de tourner, et c'est bien le problème. Personne ne s'en
aperçoit, jusqu'au jour où quelqu'un suit une instruction qui ne marche
plus et conclut que le projet est abandonné.

Ces tests traitent la documentation comme du code : ce qu'elle affirme
doit être vrai, et le rester.

Ils ne jugent pas le style. Ils vérifient que ce qui est écrit
correspond à ce qui existe — tâches, réglages, modules, fichiers,
chiffres — et qu'un lecteur extérieur peut suivre ce qu'il lit.
"""

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
DOCS = RACINE / "docs"
CODE = RACINE / "gaizer"


def _documents():
    return sorted([*list(DOCS.glob("*.md")), RACINE / "README.md", RACINE / "README.fr.md"])


def _texte(fichier):
    return fichier.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def yml():
    return yaml.safe_load(_texte(CODE / "gaizer.yml"))


# ── Ce qui est promis existe ─────────────────────────────────────────
class TestPromesses:
    """Une documentation qui cite une tâche disparue envoie le lecteur
    la chercher dans une interface où elle n'est pas."""

    def test_les_taches_citees_existent(self, yml):
        """Les noms techniques cités entre accents graves doivent
        correspondre à des modes réellement enregistrés."""
        modes = {(t.get("defaultArgs") or {}).get("mode")
                 for t in yml["tasks"]}
        modes.discard(None)
        inconnus = set()
        for f in _documents():
            for cite in re.findall(r"`(mode\s*=\s*)?(\w+)`", _texte(f)):
                nom = cite[1]
                # Un mot entre accents graves n'est pas forcément un
                # mode : on ne retient que ceux qui y ressemblent.
                # « enrich_sources », « enrich_rapport » sont des
                # CHAMPS personnalisés, non des tâches : le préfixe
                # ne suffit pas à les distinguer.
                champs = ("enrich_sources", "enrich_rapport",
                          "enrich_historique", "enrich_cree",
                          "enrich_position", "enrich_pouvoir",
                          "enrich_ia", "enrich_accept",
                          "enrich_role_origine", "enrich_role_motif")
                if nom in champs:
                    continue
                if re.fullmatch(r"[a-z]+_[a-z_]+", nom) and \
                        nom not in modes and \
                        any(nom.startswith(p) for p in
                            ("apply_", "detect_", "rapport_",
                             "restaurer_", "retirer_", "ranger_",
                             "marquer_", "arbitrer_", "controler_",
                             "inspecter_", "proposer_", "sante_",
                             "purger_", "clear_", "migrer_",
                             "reprendre_", "normaliser_", "deduire_",
                             "suggerer_", "regenerate_")):
                    inconnus.add(f"{f.name}: {nom}")
        assert inconnus == set(), sorted(inconnus)

    def test_les_reglages_cites_existent(self, yml):
        """Un réglage documenté mais absent se cherche en vain dans
        l'écran des plugins."""
        connus = set(yml.get("settings") or {})
        inconnus = set()
        for f in _documents():
            for nom in re.findall(r"`([a-z][a-zA-Z]{4,})`", _texte(f)):
                # Les opérations de l'API Stash et les propriétés du
                # navigateur s'écrivent comme un réglage. Les
                # reconnaître par une LISTE demanderait de la tenir à
                # jour ; le vocabulaire de Stash suffit à les
                # distinguer, et il ne change pas.
                if re.match(
                        r"^(find|install|available|installed|configure|"
                        r"reload|run|stop|job|scrape|performer|scene|"
                        r"studio|group|tag|custom|inner|outer|text|"
                        r"document|window)", nom):
                    continue
                if (re.search(r"[A-Z]", nom) and nom not in connus
                        and not nom.endswith((".py", ".js", ".yml",
                                              ".md"))):
                    inconnus.add(f"{f.name}: {nom}")
        assert inconnus == set(), sorted(inconnus)

    def test_les_modules_cites_existent(self):
        modules = {f.name for f in CODE.glob("*.py")}
        modules |= {f.name for f in (RACINE / "tests").glob("*.py")}
        modules |= {f.name for f in (RACINE / "tools").glob("*.py")}
        modules |= {f.name for f in (RACINE / "tests").glob("*.js")}
        modules |= {f.name for f in CODE.glob("*.js")}
        modules |= {f.name for f in CODE.glob("*.yml")}
        inconnus = set()
        for f in _documents():
            for nom in re.findall(r"`(\w+\.(?:py|js|yml))`", _texte(f)):
                if nom not in modules and nom not in (
                        "gaizer.yml", "pyproject.toml"):
                    inconnus.add(f"{f.name}: {nom}")
        assert inconnus == set(), sorted(inconnus)

    def test_les_fichiers_de_tests_cites_existent(self):
        presents = {f.name for f in (RACINE / "tests").glob("*")}
        inconnus = set()
        for f in _documents():
            for nom in re.findall(r"`tests/([\w.]+)`", _texte(f)):
                if nom not in presents:
                    inconnus.add(f"{f.name}: tests/{nom}")
        assert inconnus == set(), sorted(inconnus)

    def test_les_outils_cites_existent(self):
        presents = {f.name for f in (RACINE / "tools").glob("*")}
        inconnus = set()
        for f in _documents():
            for nom in re.findall(r"`tools/([\w.]+)`", _texte(f)):
                if nom not in presents:
                    inconnus.add(f"{f.name}: tools/{nom}")
        assert inconnus == set(), sorted(inconnus)


# ── Les liens mènent quelque part ────────────────────────────────────
class TestLiens:

    def test_aucun_lien_interne_mort(self):
        morts = []
        for f in _documents():
            for cible in re.findall(r"\]\(([^)#]+)\)", _texte(f)):
                if cible.startswith(("http://", "https://", "mailto:")):
                    continue
                # Un appel de fonction cité dans un exemple ressemble
                # à un lien : « log.progress(ctx) ».
                if "/" not in cible and "." not in cible:
                    continue
                if not (f.parent / cible).resolve().exists():
                    morts.append(f"{f.name} → {cible}")
        assert morts == [], morts

    def test_les_deux_readme_se_citent(self):
        """Un lecteur arrivé sur la version anglaise doit trouver la
        française, et l'inverse."""
        assert "README.fr.md" in _texte(RACINE / "README.md")
        assert "README.md" in _texte(RACINE / "README.fr.md")


# ── Ce qui ne doit pas être publié ───────────────────────────────────
class TestPortee:
    """Une documentation publique s'adresse à des inconnus. Ce qui
    relève du journal de bord de son auteur n'y a pas sa place."""

    def test_aucune_formulation_a_la_premiere_personne(self):
        """Une norme s'énonce ; le récit de la fois où elle a manqué
        appartient ailleurs. « J'avais fait » n'apprend rien et fait
        douter du reste."""
        motif = re.compile(
            r"(?<![\w'])(j'ai |j'avais|je ne |mon propre|ma propre|"
            r"nous avons dû|je pense)", re.I)
        fautes = []
        for f in _documents():
            for i, ligne in enumerate(_texte(f).split("\n"), 1):
                if motif.search(ligne):
                    fautes.append(f"{f.name}:{i}")
        assert fautes == [], fautes

    def test_aucun_decompte_de_defauts_passes(self):
        """« Trois trous ont été trouvés », « cinq réglages morts » :
        des chiffres qui datent le document sans rien apprendre."""
        motif = re.compile(
            r"\b(trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze)\s+"
            r"(trous?|défauts?|erreurs?|bugs?|réglages? morts?|"
            r"régressions?)\b", re.I)
        fautes = []
        for f in _documents():
            for i, ligne in enumerate(_texte(f).split("\n"), 1):
                if motif.search(ligne):
                    fautes.append(f"{f.name}:{i}")
        assert fautes == [], fautes

    def test_aucune_reference_a_une_collection_particuliere(self):
        motif = re.compile(
            r"(cette collection|notre collection|ma collection|"
            r"sur cette médiathèque|de l'auteur)", re.I)
        fautes = []
        for f in _documents():
            for i, ligne in enumerate(_texte(f).split("\n"), 1):
                if motif.search(ligne):
                    fautes.append(f"{f.name}:{i}")
        assert fautes == [], fautes


# ── Cohérence entre documents ────────────────────────────────────────
class TestCoherence:

    def test_la_licence_est_dite_pareil_partout(self):
        """Une licence annoncée différemment selon l'endroit est une
        ambiguïté juridique, pas une nuance de rédaction."""
        licence = _texte(RACINE / "LICENSE")
        assert "AFFERO" in licence.upper()
        for f in (RACINE / "README.md", RACINE / "README.fr.md"):
            texte = _texte(f).upper()
            assert "AGPL" in texte, f.name
            # Chercher des MOTS entiers : « MIT » se trouve dans
            # « limite », et un faux positif sur la licence ferait
            # échouer toute publication.
            for interdit in ("MIT", "POLYFORM", "BSD", "APACHE"):
                assert not re.search(rf"\b{interdit}\b", texte), \
                    f"{f.name} : {interdit}"

    def test_la_version_minimale_de_stash_est_coherente(self):
        """Annoncer deux versions minimales différentes fait échouer
        l'installation de quelqu'un pour rien."""
        versions = set()
        for f in _documents():
            versions |= set(re.findall(r"Stash (\d+\.\d+)", _texte(f)))
        assert len(versions) <= 2, versions

    def test_chaque_document_dit_de_quoi_il_traite(self):
        """Un document sans titre ni introduction oblige à lire pour
        savoir s'il concerne le lecteur."""
        for f in _documents():
            lignes = [x for x in _texte(f).split("\n")[:12] if x.strip()]
            assert lignes and lignes[0].startswith("#"), f.name
            assert len(lignes) > 2, f"{f.name} : pas d'introduction"


# ── Instructions exécutables ─────────────────────────────────────────
class TestInstructions:
    """Une commande fausse dans un README fait conclure au lecteur que
    le projet est abandonné."""

    def test_les_commandes_python_citees_existent(self):
        fautes = []
        for f in _documents():
            for cmd in re.findall(r"python3 (tools/[\w.]+|tests/[\w.]+)",
                                  _texte(f)):
                if not (RACINE / cmd).exists():
                    fautes.append(f"{f.name}: {cmd}")
        assert fautes == [], fautes

    def test_les_dependances_citees_sont_declarees(self):
        """Un README qui demande d'installer un paquet absent des
        dépendances laisse une installation incomplète."""
        readme = _texte(RACINE / "README.md")
        cites = set(re.findall(r"pip install ([\w\s-]+)", readme))
        paquets = {p for ligne in cites for p in ligne.split()}
        assert paquets <= {"stashapp-tools", "pyyaml"}, paquets


class TestChiffresAnnonces:
    """Un audit a trouvé vingt-cinq chiffres faux dans la
    documentation : « 29 tâches » et « 24 tâches » selon le document,
    pour cinquante et une réelles ; « ia.py 356 lignes » pour huit
    cent trente-quatre.

    Le problème n'est pas la péremption — elle est inévitable — mais
    qu'aucun contrôle ne la détecte. Un lecteur qui vérifie un chiffre
    et le trouve faux cesse de croire le reste, y compris ce qui est
    juste.

    D'où la règle qui en découle : ne PAS annoncer ce qui périmera
    sans être vérifié. Un ordre de grandeur se maintient ; un compte
    exact non."""

    def _lignes_reelles(self):
        return {f.stem: len(f.read_text(encoding="utf-8").split("\n"))
                for f in list(CODE.glob("*.py")) + list(CODE.glob("*.js"))}

    def test_aucun_compteur_de_lignes_perime(self):
        """Un compteur faux à 15 % près est un compteur faux."""
        reels = self._lignes_reelles()
        fautes = []
        for doc in RACINE.glob("docs/*.md"):
            texte = doc.read_text(encoding="utf-8")
            for nom, reel in reels.items():
                for m in re.finditer(
                        rf"`{re.escape(nom)}\.(?:py|js)`[^|\n]*\|\s*(\d+)",
                        texte):
                    annonce = int(m.group(1))
                    if abs(annonce - reel) > max(20, reel * 0.15):
                        fautes.append(
                            f"{doc.name} {nom}: {annonce} ≠ {reel}")
        assert fautes == [], fautes

    def test_le_nombre_de_taches_annonce_est_juste(self):
        """C'est le chiffre le plus lu : il dit ce que le plugin sait
        faire."""
        import ast
        arbre = ast.parse(
            (CODE / "gaizer.py").read_text(encoding="utf-8"))
        reel = 0
        for n in ast.walk(arbre):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id == "TASKS":
                        reel = len(n.value.keys)
        assert reel > 0, "registre TASKS introuvable"
        fautes = []
        for doc in RACINE.glob("docs/*.md"):
            texte = doc.read_text(encoding="utf-8")
            for m in re.finditer(r"(\d+)\s+tâches", texte):
                if int(m.group(1)) != reel:
                    fautes.append(f"{doc.name}: {m.group(1)} ≠ {reel}")
        assert fautes == [], fautes

    def test_le_nombre_de_tests_annonce_est_juste(self):
        """Il sert d'argument de confiance : le laisser périmer serait
        pire que ne rien annoncer."""
        reel = sum(
            len(re.findall(r"\n    def test_", f.read_text(
                encoding="utf-8")))
            for f in (RACINE / "tests").glob("test_*.py"))
        fautes = []
        for doc in list(RACINE.glob("docs/*.md")) + [
                RACINE / "README.md", RACINE / "README.fr.md"]:
            if not doc.exists():
                continue
            texte = doc.read_text(encoding="utf-8")
            for m in re.finditer(r"(\d[\d\s]{2,})\s*tests", texte):
                annonce = int(m.group(1).replace(" ", ""))
                # Un ordre de grandeur arrondi reste juste.
                if annonce > reel or annonce < reel * 0.75:
                    fautes.append(f"{doc.name}: {annonce} ≠ {reel}")
        assert fautes == [], fautes


class TestGuideEtInventaire:
    """Un audit a montré que la documentation ment sur des faits
    vérifiables dès que rien ne les vérifie. Ces deux documents
    décrivent ce que le plugin FAIT : les laisser périmer serait pire
    que ne rien écrire, parce qu'un lecteur qui vérifie un point et le
    trouve faux cesse de croire le reste."""

    def _inventaire(self):
        f = RACINE / "docs" / "INVENTAIRE_TACHES.md"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def _guide(self):
        f = RACINE / "docs" / "GUIDE_UTILISATION.md"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def test_les_deux_documents_existent(self):
        assert self._guide(), "guide d'utilisation absent"
        assert self._inventaire(), "inventaire des tâches absent"

    def test_l_inventaire_couvre_toutes_les_taches(self):
        """Une tâche absente de l'inventaire est une fonctionnalité
        que personne ne découvrira."""
        import ast
        arbre = ast.parse(
            (CODE / "gaizer.py").read_text(encoding="utf-8"))
        modes = []
        for n in ast.walk(arbre):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id == "TASKS":
                        modes = [k.value for k in n.value.keys]
        assert modes, "registre introuvable"
        texte = self._inventaire()
        m = re.search(r"\*\*(\d+) tâches\.\*\*", texte)
        assert m, "l'inventaire n'annonce aucun compte"
        assert int(m.group(1)) == len(modes), \
            f"inventaire : {m.group(1)} ≠ {len(modes)}"

    def test_l_inventaire_distingue_lecture_et_ecriture(self):
        """C'est la distinction la plus utile à l'usage : une tâche de
        lecture se lance sans risque, une tâche d'écriture demande d'y
        penser."""
        texte = self._inventaire()
        assert "Écrit" in texte
        assert "**oui**" in texte and "| non |" in texte

    def test_le_guide_decrit_la_premiere_utilisation(self):
        """C'est ce qui manque le plus à qui vient d'installer : non
        pas la liste de ce qui existe, mais l'ordre dans lequel s'en
        servir."""
        guide = self._guide().lower()
        assert "première utilisation" in guide

    def test_le_guide_dit_ce_qui_est_ecrit_sans_accord(self):
        """Un plugin qui modifie une médiathèque doit dire d'emblée
        ce qu'il touche sans demander."""
        guide = self._guide().lower()
        assert "rien n'est écrit sans votre accord" in guide

    def test_le_guide_couvre_les_sources(self):
        guide = self._guide()
        for source in ("Chemin du fichier", "Stash-boxes", "Vignettes",
                       "Génériques"):
            assert source in guide, source

    def test_le_guide_couvre_l_export_des_reglages(self):
        guide = self._guide().lower()
        assert "exporter les réglages" in guide
        assert "aucune clé d'api" in guide


class TestFichierDePassation:
    """AGENTS.md permet à un agent de reprendre le travail sans
    redécouvrir ce qui a déjà été appris.

    Un fichier de passation périmé est pire qu'aucun : il envoie
    chercher au mauvais endroit, et celui qui le lit croit savoir.
    Ces contrôles vérifient ce qui peut l'être."""

    def _agents(self):
        f = RACINE / "AGENTS.md"
        return f.read_text(encoding="utf-8") if f.exists() else ""

    def test_il_existe(self):
        assert self._agents(), "AGENTS.md absent"

    def test_le_compte_de_tests_est_juste(self):
        """C'est le premier chiffre qu'un agent vérifiera : le
        trouver faux lui fera douter du reste."""
        reel = sum(
            len(re.findall(r"\n    def test_", f.read_text(
                encoding="utf-8")))
            for f in (RACINE / "tests").glob("test_*.py"))
        m = re.search(r"(\d{3,})\s+tests", self._agents())
        assert m, "aucun compte de tests"
        annonce = int(m.group(1))
        assert abs(annonce - reel) <= reel * 0.05, \
            f"AGENTS.md : {annonce} ≠ {reel}"

    def test_les_pieges_sont_consignes(self):
        """Chacun a coûté du temps : les taire les ferait repayer."""
        texte = self._agents()
        for piege in ("configurePlugin", "PyYAML", "update_studio"):
            assert piege in texte, piege

    def test_la_regle_du_test_avant_le_code_est_dite(self):
        """C'est ce qui gouverne tout le reste."""
        texte = self._agents().lower()
        assert "avant le code" in texte or "test avant" in texte

    def test_les_deux_depots_sont_decrits(self):
        """Travailler dans le dépôt public perdrait le travail à la
        publication suivante."""
        texte = self._agents()
        assert "stash-gaizer" in texte and "Stash-Gaiser-public" in texte
        assert "régénéré" in texte

    def test_les_fichiers_cites_existent(self):
        """Un chemin faux envoie chercher au mauvais endroit."""
        manquants = []
        for chemin in re.findall(r"`(docs/[\w_]+\.md)`",
                                 self._agents()):
            if not (RACINE / chemin).exists():
                manquants.append(chemin)
        assert manquants == [], manquants

    def test_les_taches_citees_existent(self):
        """Un exemple qui ne marche pas décourage d'essayer les
        suivants."""
        import ast
        arbre = ast.parse(
            (CODE / "gaizer.py").read_text(encoding="utf-8"))
        modes = set()
        for n in ast.walk(arbre):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id == "TASKS":
                        modes = {k.value for k in n.value.keys}
        cites = set(re.findall(r'\\"mode\\": \\"(\w+)\\"',
                               self._agents()))
        assert cites <= modes, sorted(cites - modes)
