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

import ast
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


class TestFiltrageDesSecretsSansDegat:
    """Le filtrage reconnaît les secrets par leur FORME — un nom
    contenant « key », « token », « secret ». C'est ce qui le rend
    robuste à l'ajout d'un fournisseur.

    Mais une clé d'état qui parle DES secrets porte les mêmes mots
    sans en être un. La filtrer détruit une donnée de travail et
    produit des diagnostics absurdes : la liste des noms remplacée par
    une chaîne, puis relue caractère par caractère."""

    def test_la_liste_des_secrets_survit(self, tmp_path, monkeypatch):
        monkeypatch.setattr(noyau, "ETAT_FICHIER",
                            tmp_path / "etat.json")
        noyau.etat_ecrire({"reglages_secrets": ["mistralApiKey",
                                                "openaiApiKey"]})
        relu = noyau.etat_lire().get("reglages_secrets")
        assert isinstance(relu, list), \
            "une liste de NOMS n'est pas un secret"
        assert "mistralApiKey" in relu

    def test_la_valeur_du_secret_est_toujours_filtree(
            self, tmp_path, monkeypatch):
        """La correction ne doit pas rouvrir le trou qu'elle vient
        fermer."""
        monkeypatch.setattr(noyau, "ETAT_FICHIER",
                            tmp_path / "etat.json")
        noyau.etat_ecrire({"reglages": {
            "mistralApiKey": "sk-tres-secret-12345"}})
        contenu = (tmp_path / "etat.json").read_text(encoding="utf-8")
        assert "sk-tres-secret-12345" not in contenu

    def test_aucune_chaine_ne_remplace_une_liste(
            self, tmp_path, monkeypatch):
        """Règle générale : le filtrage change la VALEUR d'un secret,
        jamais le TYPE d'une donnée de travail. Un type qui change
        casse le code qui la relit, loin de l'endroit fautif."""
        monkeypatch.setattr(noyau, "ETAT_FICHIER",
                            tmp_path / "etat.json")
        entree = {"reglages_secrets": ["a", "b"],
                  "tokens_vus": ["x"], "cles_connues": ["y"],
                  "compte": 3, "actif": True}
        noyau.etat_ecrire(entree)
        relu = noyau.etat_lire()
        for cle, valeur in entree.items():
            assert type(relu.get(cle)) is type(valeur), \
                f"{cle} : {type(valeur)} → {type(relu.get(cle))}"

    def test_le_diagnostic_ne_signale_pas_de_faux_disparus(
            self, tmp_path, monkeypatch):
        """Le symptôme qui a révélé le défaut : des « identifiants
        disparus » qui étaient les lettres d'un mot."""
        monkeypatch.setattr(noyau, "ETAT_FICHIER",
                            tmp_path / "etat.json")
        erreurs = []
        monkeypatch.setattr(noyau.log, "error",
                            lambda m, *a, **k: erreurs.append(str(m)))
        st = FauxStash()
        ctx = faux_contexte({"mistralApiKey": "sk-x", "language": "fr",
                             "applyMode": "auto", "batchSize": "25",
                             "createMissing": True}, st)
        noyau._sauver_reglages(ctx)
        noyau._sauver_reglages(ctx)
        assert not any("DISPARU" in m for m in erreurs), erreurs


class TestSimulationParArgument:
    """Le bouton « Simuler » du panneau passe la simulation en
    ARGUMENT de tâche, non en réglage : cocher un réglage global pour
    essayer une seule action, puis penser à le décocher, serait une
    invitation à l'oubli.

    Ne lire que le réglage rendait donc ce bouton inopérant — l'action
    s'exécutait pour de bon alors que l'utilisateur croyait l'éprouver.
    C'est le pire défaut possible sur une protection : elle rassure
    sans protéger."""

    def _ctx(self, reglages=None, args=None):
        ctx = faux_contexte(reglages or {}, FauxStash())
        ctx.args = args or {}
        return ctx

    def test_l_argument_active_la_simulation(self):
        for valeur in ("1", "true", "True", 1, True):
            assert self._ctx(args={"dryRun": valeur}).simulation(), \
                valeur

    def test_le_reglage_active_la_simulation(self):
        assert self._ctx({"dryRun": True}).simulation()

    def test_sans_rien_la_simulation_est_inactive(self):
        assert not self._ctx().simulation()

    def test_une_valeur_fausse_n_active_pas(self):
        for valeur in ("0", "false", "", None):
            assert not self._ctx(args={"dryRun": valeur}).simulation(), \
                valeur

    def test_l_argument_prime_sur_un_reglage_inactif(self):
        """Le cas d'usage : le réglage global est décoché, et
        l'utilisateur veut éprouver UNE action."""
        ctx = self._ctx({"dryRun": False}, {"dryRun": "1"})
        assert ctx.simulation()


class TestOwaspLlm:
    """Audit selon OWASP Top 10 pour les applications à modèle de
    langue (2025), tel que Microsoft l'encode.

    Ce plugin envoie des données à un modèle et ÉCRIT ses réponses
    dans une médiathèque. C'est exactement le péril de LLM05 —
    « improper output handling » : une sortie de modèle traitée comme
    une donnée de confiance.

    L'audit initial a relevé vingt-trois points ; vingt-et-un étaient
    des faux positifs de mes propres motifs — « re.compile » pris
    pour « compile », « cle » de dictionnaire pris pour un secret. Un
    audit bruyant cesse d'être lu, ce qui est pire qu'aucun audit."""

    def _py(self):
        return {f.stem: f.read_text(encoding="utf-8")
                for f in RACINE.glob("*.py")}

    def test_aucune_sortie_n_atteint_un_interpreteur(self):
        """LLM05 : `eval` ou `exec` sur une sortie de modèle donne
        l'exécution de code à qui contrôle le prompt."""
        fautes = []
        for nom, code in self._py().items():
            for m in re.finditer(r"(?<![.\w])(eval|exec)\s*\(", code):
                fautes.append(f"{nom}:{code[:m.start()].count(chr(10)) + 1}")
        assert fautes == [], fautes

    def test_aucun_shell(self):
        for nom, code in self._py().items():
            assert "shell=True" not in code, nom

    def test_aucune_sortie_dans_le_html(self):
        """Une présentation générée s'affiche dans Stash : la poser
        en HTML brut donnerait du XSS à qui contrôle le modèle."""
        for f in RACINE.glob("*.js"):
            texte = f.read_text(encoding="utf-8")
            assert "dangerouslySetInnerHTML" not in texte, f.name
            assert "innerHTML =" not in texte, f.name

    def test_la_sortie_est_controlee_avant_ecriture(self):
        """Le contrôle des noms propres est la seule barrière entre
        ce que le modèle invente et ce qui entre dans la
        médiathèque."""
        ia = (RACINE / 'ia.py').read_text(encoding="utf-8")
        i = ia.find("def generer_bio_hot")
        assert i > 0
        assert "noms_verifies" in ia[i:i + 4000]

    def test_la_consommation_est_bornee(self):
        """LLM10 : sans plafond, une boucle sur une collection épuise
        un quota payant."""
        ia = (RACINE / 'ia.py').read_text(encoding="utf-8")
        assert "BUDGETS" in ia
        assert "maxLlmCalls" in (RACINE / 'gaizer.yml').read_text(
            encoding="utf-8")

    def test_chaque_appel_sortant_a_un_delai(self):
        """Un service qui ne répond jamais bloquerait la tâche
        indéfiniment."""
        fautes = []
        for nom, code in self._py().items():
            for m in re.finditer(r"urlopen\(|requests\.(get|post)\(",
                                 code):
                if "timeout" not in code[m.start():m.start() + 400]:
                    fautes.append(nom)
        assert fautes == [], fautes

    def test_aucun_secret_journalise(self):
        """LLM02 : une clé dans le journal est une clé publiée, le
        journal étant lisible depuis l'interface de Stash."""
        fautes = []
        for nom, code in self._py().items():
            for m in re.finditer(
                    r"log\.\w+\([^)]*\{[^}]*\b(\w*[Aa]pi[_]?[Kk]ey|"
                    r"\w*[Tt]oken|\w*[Ss]ecret|password)\b", code):
                fautes.append(f"{nom}:{code[:m.start()].count(chr(10)) + 1}")
        assert fautes == [], fautes

    def test_toute_adresse_distante_est_jugee(self):
        """Une image proposée par une source est téléchargée par le
        serveur : sans contrôle, une source compromise ferait
        interroger le réseau local."""
        vision = (RACINE / 'vision.py').read_text(encoding="utf-8")
        i = vision.find("return _telecharger(url)")
        assert i > 0
        # L'appelant juge l'adresse avant d'appeler.
        assert "adresse_de_stash" in vision[max(0, i - 400):i]


class TestReconnaissanceDesSecrets:
    """`est_secret` décide de ce qui ne sort jamais : ni dans un
    export, ni dans le journal, ni dans le fichier d'état.

    Elle ne reconnaissait que des formes ANGLAISES. Un réglage nommé
    « cleApi » ou « motDePasse » — plausible dans un plugin dont
    l'interface est française — serait sorti dans un fichier qu'on
    transporte ou qu'on colle dans un ticket.

    Aucun réglage actuel n'est dans ce cas : le défaut est latent,
    non effectif. Mais il se réaliserait au premier réglage nommé en
    français, et rien ne l'aurait signalé."""

    def test_les_formes_anglaises_sont_reconnues(self):
        for nom in ("llmApiKey", "apiToken", "mySecret",
                    "userPassword", "credentialX", "authBearer"):
            assert noyau.est_secret(nom), nom

    def test_les_formes_francaises_aussi(self):
        """L'interface de ce plugin est française : un réglage y
        sera nommé en français tôt ou tard."""
        for nom in ("cleApi", "motDePasse", "jetonAcces",
                    "identifiantSecret"):
            assert noyau.est_secret(nom), nom

    def test_un_reglage_ordinaire_n_est_pas_un_secret(self):
        """Tout classer en secret viderait l'export de sa
        substance."""
        for nom in ("applyMode", "batchSize", "llmUrl", "aiDefault",
                    "tagProfile", "language", "cacheJours"):
            assert not noyau.est_secret(nom), nom

    def test_la_casse_ne_compte_pas(self):
        for nom in ("LLMAPIKEY", "Api_Key", "MOT_DE_PASSE"):
            assert noyau.est_secret(nom), nom

    def test_valeurs_absurdes(self):
        for nom in ("", None, 42):
            assert isinstance(noyau.est_secret(nom), bool), nom

    def test_aucun_reglage_du_manifeste_n_echappe(self):
        """Le contrôle qui compte : ce qui porte un identifiant dans
        le manifeste réel doit être reconnu."""
        import yaml
        d = yaml.safe_load((RACINE / "gaizer.yml").read_text(
            encoding="utf-8"))
        for cle in d["settings"]:
            porteur = any(m in cle.lower() for m in
                          ("key", "token", "secret", "password",
                           "cle", "jeton", "motdepasse"))
            if porteur:
                assert noyau.est_secret(cle), cle


class TestRequetesNonConstruites:
    """Revue menée selon la méthode de « security-review » : tracer
    la donnée avant de signaler, ne rapporter que ce dont on est sûr.

    Un motif seul ne suffit pas — cherché à la main, il donnait
    quinze requêtes « construites dynamiquement », toutes fausses :
    le motif attrapait le journal voisin, pas la requête.

    La question juste porte sur le PREMIER argument de `call_GQL` :
    un littéral ou une constante nommée est sûr, une concaténation
    ne l'est pas."""

    def test_aucune_requete_construite(self):
        """Une requête assemblée depuis une valeur extérieure — nom
        d'interprète, argument de tâche — accepte l'injection."""
        douteuses = []
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            arbre = ast.parse(code)
            for n in ast.walk(arbre):
                if not isinstance(n, ast.Call):
                    continue
                if getattr(n.func, "attr", "") != "call_GQL":
                    continue
                if not n.args:
                    continue
                req = n.args[0]
                # Littéral, constante nommée, ou entrée de table :
                # dans les trois cas la requête est écrite au clair
                # dans le code, non assemblée à l'exécution.
                if isinstance(req, (ast.Constant, ast.Name,
                                    ast.Subscript)):
                    continue
                douteuses.append(f"{f.stem}:{n.lineno}")
        assert douteuses == [], douteuses

    def test_les_valeurs_passent_en_variables(self):
        """C'est ce qui rend l'injection impossible : le serveur
        distingue la requête de ses paramètres."""
        exemples = 0
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            arbre = ast.parse(code)
            for n in ast.walk(arbre):
                if not isinstance(n, ast.Call):
                    continue
                if getattr(n.func, "attr", "") != "call_GQL":
                    continue
                if len(n.args) >= 2:
                    exemples += 1
        assert exemples >= 20, exemples

    def test_aucun_puits_grave(self):
        """Exécution de code, commande système, désérialisation : les
        trois puits où une donnée extérieure devient une action."""
        motifs = {
            "exécution": r"(?<![.\w])(eval|exec)\s*\(",
            "commande": r"subprocess\.|os\.system|shell\s*=\s*True",
            "désérialisation": r"pickle\.|marshal\.",
        }
        fautes = []
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            for quoi, motif in motifs.items():
                for m in re.finditer(motif, code):
                    ligne = code[:m.start()].count("\n") + 1
                    fautes.append(f"{quoi} {f.stem}:{ligne}")
        assert fautes == [], fautes
