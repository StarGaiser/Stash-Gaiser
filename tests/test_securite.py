# -*- coding: utf-8 -*-
"""
Sécurité : ce que le plugin ne doit jamais faire.

Un plugin d'enrichissement occupe une position inconfortable. Il lit
des données venues de sites tiers, les passe à un modèle de langage,
écrit dans une base locale, appelle des commandes système et — depuis
peu — installe du code. Chacun de ces points est une porte.

Ces tests ne cherchent pas des défauts hypothétiques : chacun
correspond à une porte réellement ouverte dans ce code, ou qui l'a été.
Trois trous du contrôle d'URL ont été trouvés ainsi ; les clés d'API
ont été écrites sur le disque pendant plusieurs versions.

Un test de sécurité doit être PLUS strict qu'un test fonctionnel :
échouer par excès de prudence coûte une correction, échouer par excès
de confiance coûte une compromission.
"""

import re
from pathlib import Path

import pytest

import noyau
import scrapers
from faux import FauxStash, faux_contexte, performer

RACINE = Path(__file__).resolve().parent.parent / "gaizer"


# ── Sortie réseau ────────────────────────────────────────────────────
class TestAdressesRefusees:
    """Le plugin suit des URLs venues de sources tierces. Sans
    contrôle, une source pourrait le faire interroger le réseau local
    de l'utilisateur — services d'administration, métadonnées de
    machine virtuelle, imprimantes. Trois trous ont été trouvés ici."""

    @pytest.mark.parametrize("url", [
        "http://127.0.0.1/admin",
        "http://localhost:9999/graphql",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://127.1/",                    # forme abrégée
        "http://2130706433/",               # forme décimale
        "http://0x7f000001/",               # forme hexadécimale
        "http://192.168.1.1/",
        "http://10.0.0.1/",
        "http://172.16.0.1/",
        "http://169.254.169.254/latest/",   # métadonnées de VM
        "file:///etc/passwd",
        "ftp://exemple.test/x",
        "gopher://exemple.test/",
    ])
    def test_adresse_refusee(self, url):
        assert not noyau.url_sure(url), url

    @pytest.mark.parametrize("url", [
        "https://stashdb.org/performers/x",
        "https://www.iafd.com/person.rme/id=x",
        "http://exemple-public.test/page",
    ])
    def test_adresse_publique_acceptee(self, url):
        assert noyau.url_sure(url), url

    def test_valeurs_absurdes_refusees_sans_lever(self):
        """Une entrée malformée doit être REFUSÉE, pas provoquer une
        exception : une source qui renvoie n'importe quoi ne doit pas
        interrompre le traitement."""
        for url in ("", None, "pas une url", "http://",
                    "https://" + "a" * 5000):
            assert noyau.url_sure(url) in (True, False)


# ── Installation de code ─────────────────────────────────────────────
class TestSourceDePaquets:
    """Depuis la version 0.59, le plugin peut installer des scrapers —
    du code qui s'exécutera sur la machine de l'utilisateur. La source
    est un RÉGLAGE, donc une valeur qu'un tiers pourrait modifier s'il
    obtenait un accès à la configuration.

    Une source non contrôlée transforme une commodité en porte
    d'entrée."""

    def test_la_source_par_defaut_est_officielle(self):
        assert scrapers.SOURCE_DEFAUT.startswith(
            "https://stashapp.github.io/")

    @pytest.mark.parametrize("source", [
        "http://127.0.0.1:8000/index.yml",
        "http://192.168.1.50/index.yml",
        "file:///tmp/index.yml",
        "http://169.254.169.254/index.yml",
    ])
    def test_source_locale_refusee(self, source):
        """Installer depuis le réseau local reviendrait à exécuter du
        code déposé par quiconque s'y trouve."""
        assert not scrapers.source_sure(source), source

    def test_source_en_clair_refusee(self):
        """Un catalogue servi en HTTP peut être remplacé en chemin :
        le code installé ne serait pas celui annoncé."""
        assert not scrapers.source_sure(
            "http://exemple-public.test/index.yml")

    def test_source_publique_en_https_acceptee(self):
        assert scrapers.source_sure(
            "https://exemple-public.test/scrapers/index.yml")

    def test_source_vide_retombe_sur_le_defaut(self):
        st = FauxStash()
        ctx = faux_contexte({"scraperSource": ""}, st)
        assert scrapers._source(ctx) == scrapers.SOURCE_DEFAUT

    def test_source_refusee_retombe_sur_le_defaut(self):
        """Ne PAS échouer silencieusement en installant depuis une
        source douteuse : revenir à celle qui est connue."""
        st = FauxStash()
        ctx = faux_contexte(
            {"scraperSource": "http://127.0.0.1/index.yml"}, st)
        assert scrapers._source(ctx) == scrapers.SOURCE_DEFAUT


# ── Secrets ──────────────────────────────────────────────────────────
class TestSecrets:
    """Les clés d'API ont été écrites en clair dans un fichier d'état
    pendant plusieurs versions. Le défaut est corrigé ; ces tests
    empêchent son retour."""

    @pytest.mark.parametrize("cle", [
        "mistralApiKey", "openaiApiKey", "anthropicApiKey",
        "llmApiKey", "openrouterApiKey", "groqApiKey",
        "deepseekApiKey", "googleApiKey", "xaiApiKey",
        "togetherApiKey", "perplexityApiKey",
    ])
    def test_toute_cle_est_reconnue_comme_secrete(self, cle):
        assert noyau.est_secret(cle), cle

    @pytest.mark.parametrize("cle", [
        "apiKey", "api_key", "MonJetonSecret", "password",
        "monTOKENprive", "secretMachin",
    ])
    def test_les_formes_voisines_aussi(self, cle):
        """Un fournisseur ajouté demain nommera sa clé autrement : la
        reconnaissance doit porter sur la FORME, pas sur une liste."""
        assert noyau.est_secret(cle), cle

    @pytest.mark.parametrize("cle", [
        "language", "batchSize", "applyMode", "tagsExclude",
        "ollamaUrl", "scraperSource",
    ])
    def test_les_reglages_ordinaires_ne_le_sont_pas(self, cle):
        assert not noyau.est_secret(cle), cle

    def test_aucun_secret_dans_l_etat(self, tmp_path, monkeypatch):
        monkeypatch.setattr(noyau, "ETAT_FICHIER",
                            tmp_path / "etat.json")
        st = FauxStash()
        ctx = faux_contexte({"mistralApiKey": "sk-tres-secret-12345",
                             "language": "fr"}, st)
        noyau.etat_ecrire({"reglages": dict(ctx.settings)})
        contenu = (tmp_path / "etat.json").read_text(encoding="utf-8")
        assert "sk-tres-secret-12345" not in contenu

    def test_le_fichier_d_etat_n_est_pas_lisible_par_tous(
            self, tmp_path, monkeypatch):
        monkeypatch.setattr(noyau, "ETAT_FICHIER",
                            tmp_path / "etat.json")
        noyau.etat_ecrire({"x": 1})
        mode = (tmp_path / "etat.json").stat().st_mode & 0o777
        assert mode & 0o077 == 0, f"permissions trop larges : {mode:o}"


# ── Interrogation de la base ─────────────────────────────────────────
class TestRequetes:
    """Une valeur venue d'une source arrive dans des requêtes. Si elle
    y était concaténée, un nom d'interprète bien choisi suffirait à
    lire ou détruire la base."""

    def test_aucune_requete_construite_par_concatenation(self):
        suspects = []
        for f in RACINE.glob("*.py"):
            for i, ligne in enumerate(
                    f.read_text(encoding="utf-8").split("\n"), 1):
                if not re.search(r"(query|mutation)\s*[({]", ligne):
                    continue
                if re.search(r'f"""|f"|\.format\(|%\s*\(|"\s*\+',
                             ligne):
                    suspects.append(f"{f.name}:{i}")
        assert suspects == [], \
            f"requêtes construites par assemblage : {suspects}"

    def test_les_variables_passent_par_le_second_argument(self):
        """`call_GQL(requete, {variables})` : la forme qui protège."""
        st = FauxStash(performers=[performer(1, "Archie")])
        ctx = faux_contexte({}, st)
        noyau.tag_id(ctx, 'x"; mutation { performerDestroy(id: "1") }')
        assert "1" in st.performers


# ── Lecture de fichiers ──────────────────────────────────────────────
class TestLectureDeFichiers:

    def test_yaml_charge_sans_execution(self):
        """`yaml.load` sans chargeur sûr exécute du code contenu dans
        le fichier. Le plugin lit des YAML éditables par l'utilisateur
        et fournis avec le paquet."""
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            assert "yaml.load(" not in code or "SafeLoader" in code, \
                f.name
            assert "yaml.unsafe_load" not in code, f.name

    def test_aucune_deserialisation_dangereuse(self):
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            for interdit in ("pickle", "marshal", "shelve"):
                assert interdit not in code, f"{f.name} : {interdit}"

    def test_aucune_evaluation_de_chaine(self):
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            assert not re.search(r"\beval\s*\(", code), f.name
            assert not re.search(r"\bexec\s*\(", code), f.name


# ── Commandes système ────────────────────────────────────────────────
class TestCommandes:
    """`sources.py` appelle des commandes externes. Une valeur venue
    d'une source qui arriverait dans un shell serait une exécution
    arbitraire."""

    def test_aucun_shell(self):
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            assert "shell=True" not in code, f.name
            assert "os.system(" not in code, f.name
            assert "os.popen(" not in code, f.name

    def test_les_commandes_sont_des_listes(self):
        """`subprocess.run(["ffprobe", chemin])` sépare la commande de
        ses arguments ; une chaîne unique les confondrait."""
        code = (RACINE / "sources.py").read_text(encoding="utf-8")
        for m in re.finditer(r"subprocess\.run\(\s*([^\n]{0,40})", code):
            debut = m.group(1).lstrip()
            assert debut.startswith("["), \
                f"commande non séparée : {debut[:40]}"


# ── Interface ────────────────────────────────────────────────────────
class TestInterface:
    """Le panneau affiche des textes venus de sources tierces. Les
    insérer comme du HTML permettrait à une biographie de contenir un
    script."""

    def test_aucun_html_injecte(self):
        for f in RACINE.glob("*.js"):
            code = f.read_text(encoding="utf-8")
            for interdit in ("innerHTML", "outerHTML",
                             "insertAdjacentHTML", "document.write"):
                assert interdit not in code, f"{f.name} : {interdit}"

    def test_aucune_evaluation_en_javascript(self):
        for f in RACINE.glob("*.js"):
            code = f.read_text(encoding="utf-8")
            assert not re.search(r"\beval\s*\(", code), f.name
            assert "new Function(" not in code, f.name

    def test_les_liens_sont_construits_avec_encodage(self):
        """Un nom contenant « ?q= » ou « # » fausserait une adresse
        assemblée sans précaution."""
        code = (RACINE / "gaizer.js").read_text(encoding="utf-8")
        assert "encodeURIComponent" in code


# ── Simulation ───────────────────────────────────────────────────────
class TestSimulation:
    """Le mode simulation est la protection dont dépendent toutes les
    tâches destructives. Une mutation oubliée dans sa liste écrirait
    pour de bon alors que l'utilisateur croit essayer."""

    def test_toute_mutation_du_code_est_interceptee(self):
        """Les mutations employées par le plugin doivent TOUTES figurer
        dans la liste des opérations interceptées."""
        employees = set()
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            employees |= set(re.findall(
                r"mutation[^{]*\{\s*(\w+)", code))
            employees |= {m for m in re.findall(
                r"stash\.(\w+)\(", code)
                if m.startswith(("update_", "create_", "destroy_"))}
        # Le bloc à examiner est la FONCTION d'activation, prise en
        # entier : la borner à une longueur arbitraire ferait passer
        # une omission pour une couverture.
        code_noyau = (RACINE / "noyau.py").read_text(encoding="utf-8")
        i = code_noyau.find("def _activer_simulation")
        fin = code_noyau.find("\ndef ", i + 10)
        bloc = code_noyau[i:fin if fin > 0 else len(code_noyau)]
        # `create_tag` est délibérément permise : une étiquette créée
        # est inoffensive et nécessaire au calcul des propositions.
        # `installPackages` se garde elle-même, faute d'être une
        # écriture sur une entité.
        tolerees = {"create_tag", "installPackages", "k"}
        oubliees = [m for m in employees
                    if m not in bloc and m not in tolerees]
        assert oubliees == [], \
            f"mutations non interceptées en simulation : {oubliees}"

    def test_l_installation_ne_passe_pas_en_simulation(self):
        """`installPackages` n'est pas interceptée par le mécanisme
        général : la tâche doit s'en garder elle-même."""
        code = (RACINE / "scrapers.py").read_text(encoding="utf-8")
        # La DÉFINITION porte le même nom que l'appel : c'est le
        # second qui importe.
        i = code.rfind("_installer(ctx, ids)")
        j = code.find("ctx.simulation()")
        assert 0 < j < i, \
            "le contrôle de simulation doit précéder l'installation"
