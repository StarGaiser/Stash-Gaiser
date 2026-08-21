# -*- coding: utf-8 -*-
"""
Qualité du code, vérifiée par des outils tiers.

Les tests écrits à la main éprouvent ce que le code FAIT. Ceux-ci
éprouvent ce qu'il EST : sa lisibilité, son homogénéité, l'absence de
motifs dangereux, et le fait qu'aucune information personnelle n'y
figure.

Le choix d'outils tiers est délibéré. Un contrôle que j'écris moi-même
reflète ce à quoi je pense ; ruff, bandit et vulture repèrent ce à quoi
je ne pense pas. Sur ce projet, ils ont trouvé une adresse de
fournisseur non contrôlée qui aurait permis de lire un fichier local,
et une empreinte SHA1 dont l'usage n'était pas déclaré.

Ces tests s'ignorent si l'outil n'est pas installé : ils renforcent la
suite sans la rendre dépendante d'un environnement.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


def _outil(nom):
    return pytest.mark.skipif(
        shutil.which(nom) is None,
        reason=f"{nom} non installé")


def _lancer(args, cwd=RACINE):
    return subprocess.run(args, capture_output=True, text=True,
                          cwd=cwd, timeout=180, check=False)


# ── Style et pièges (ruff) ───────────────────────────────────────────
@_outil("ruff")
class TestRuff:

    def _erreurs(self, regles=None):
        args = ["ruff", "check", ".", "--output-format", "json"]
        if regles:
            args += ["--select", regles]
        r = _lancer(args)
        try:
            return json.loads(r.stdout or "[]")
        except json.JSONDecodeError:
            return []

    def test_aucune_erreur_reelle(self):
        """F : variables inexistantes, imports manquants, code
        inatteignable. Rien de discutable là-dedans."""
        erreurs = self._erreurs("F")
        assert erreurs == [], [
            f"{e['filename'].split('/')[-1]}:{e['location']['row']} "
            f"{e['code']}" for e in erreurs]

    def test_aucun_piege_classique(self):
        """B : mutable par défaut, comparaison à un littéral,
        exception trop large sans capture."""
        erreurs = self._erreurs("B")
        graves = [e for e in erreurs if e["code"] not in ("B007",)]
        assert graves == [], [
            f"{e['filename'].split('/')[-1]}:{e['location']['row']} "
            f"{e['code']}" for e in graves]

    def test_le_total_ne_remonte_pas(self):
        """Un plafond plutôt qu'un zéro : chaque exclusion doit être
        justifiée dans pyproject.toml, et le nombre restant ne doit pas
        croître sans qu'on s'en aperçoive."""
        assert len(self._erreurs()) <= 114


# ── Sécurité (bandit) ────────────────────────────────────────────────
@_outil("bandit")
class TestBandit:

    def _issues(self, severite=None):
        r = _lancer(["bandit", "-r", "gaizer/", "-q", "-f", "json",
                     "-c", "pyproject.toml"])
        try:
            resultats = json.loads(r.stdout or "{}").get("results", [])
        except json.JSONDecodeError:
            return []
        if severite:
            resultats = [x for x in resultats
                         if x["issue_severity"] == severite]
        return resultats

    def test_aucun_risque_eleve(self):
        graves = self._issues("HIGH")
        assert graves == [], [
            f"{x['filename'].split('/')[-1]}:{x['line_number']} "
            f"{x['test_id']} {x['issue_text'][:60]}" for x in graves]

    def test_les_risques_moyens_sont_connus(self):
        """B310 subsiste : l'ouverture d'URL est contrôlée en amont par
        `url_sure`, ce que bandit ne peut pas voir. Tout AUTRE risque
        moyen est un défaut."""
        moyens = {x["test_id"] for x in self._issues("MEDIUM")}
        assert moyens <= {"B310"}, moyens


# ── Code mort (vulture) ──────────────────────────────────────────────
@_outil("vulture")
class TestCodeMort:

    def test_peu_de_code_inatteignable(self):
        """Du code mort n'est pas seulement inutile : il donne
        l'illusion d'une fonctionnalité qui n'existe plus. Cinq
        réglages morts ont été trouvés ainsi sur ce projet."""
        r = _lancer(["vulture", "gaizer/", "--min-confidence", "90"])
        lignes = [x for x in r.stdout.split("\n") if x.strip()]
        assert len(lignes) <= 3, lignes


# ── Homogénéité ──────────────────────────────────────────────────────
class TestHomogeneite:
    """Deux solutions pour un même problème, c'est une de trop : la
    seconde ne sera pas corrigée quand la première le sera."""

    def _sources(self):
        return {f.name: f.read_text(encoding="utf-8")
                for f in CODE.glob("*.py")}

    def test_une_seule_facon_de_lire_l_etat(self):
        for nom, code in self._sources().items():
            if nom == "noyau.py":
                continue
            assert "ETAT_FICHIER" not in code, \
                f"{nom} touche au fichier d'état directement"

    def test_une_seule_facon_de_poser_un_tag(self):
        """`tag_id` gère le cache et la création : y échapper
        multiplierait les requêtes et les tags en double."""
        for nom, code in self._sources().items():
            if nom == "noyau.py":
                continue
            assert "create_tag(" not in code, \
                f"{nom} crée un tag sans passer par tag_id"

    def test_une_seule_facon_de_verifier_une_url(self):
        for nom, code in self._sources().items():
            if nom == "noyau.py":
                continue
            assert "urlparse" not in code or "url_sure" in code, \
                f"{nom} analyse une URL sans le contrôle commun"

    def test_la_comparaison_de_noms_est_centralisee(self):
        """Chaque module normalise pour SON domaine — un tag, une URL,
        un identifiant de paquet — et c'est légitime. Ce qui ne doit
        pas se répéter, c'est la comparaison de noms d'ENTITÉS : elle
        décide des doublons, et deux implémentations divergentes
        fusionneraient des fiches différemment selon le chemin."""
        for nom, code in self._sources().items():
            if nom in ("similarite.py",):
                continue
            assert "_sans_accents" not in code, \
                f"{nom} translittère sans passer par similarite"
            assert "SequenceMatcher" not in code, \
                f"{nom} compare des noms sans passer par similarite"

    def test_un_seul_format_d_horodatage(self):
        for nom, code in self._sources().items():
            assert "strftime" not in code or "isoformat" not in code, \
                f"{nom} mélange deux formats de date"


# ── Nommage ──────────────────────────────────────────────────────────
class TestNommage:
    """Le code est en français, y compris les identifiants : mélanger
    les langues oblige à traduire mentalement à chaque lecture."""

    ANGLICISMES = ("get_", "set_", "_list", "_dict", "check_",
                   "handle_", "process_", "compute_", "fetch_")

    def test_les_fonctions_publiques_sont_en_francais(self):
        fautes = []
        for f in CODE.glob("*.py"):
            # `sources.py` nomme ses fonctions d'après les services
            # qu'elles interrogent : « fetch_stashdb_actor » se lit
            # mieux que sa traduction, et correspond à la
            # documentation de la source.
            if f.name == "sources.py":
                continue
            for m in re.finditer(r"^def ([a-z_]\w*)",
                                 f.read_text(encoding="utf-8"),
                                 re.M):
                nom = m.group(1)
                if nom.startswith("_"):
                    continue
                if any(a in nom for a in self.ANGLICISMES):
                    fautes.append(f"{f.name}:{nom}")
        assert fautes == [], fautes

    def test_pas_de_parametre_muet_dans_une_fonction_publique(self):
        """Un paramètre d'une lettre est acceptable dans un utilitaire
        de trois lignes, où sa portée tient sous les yeux. Il ne l'est
        pas dans une fonction publique, qu'on lit sans voir son
        corps."""
        fautes = []
        for f in CODE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            for m in re.finditer(r"^def ([a-z]\w+)\(([^)]*)\)",
                                 code, re.M):
                if m.group(1).startswith("_"):
                    continue
                for arg in m.group(2).split(","):
                    arg = arg.split(":")[0].split("=")[0].strip()
                    if len(arg) == 1:
                        fautes.append(f"{f.name}:{m.group(1)}({arg})")
        assert fautes == [], fautes


# ── Anonymat ─────────────────────────────────────────────────────────
class TestAnonymat:
    """Ce dépôt est destiné à être publié. Rien n'y doit décrire son
    auteur ni sa collection.

    Ce n'est pas théorique : vingt-neuf scripts portaient un nom
    d'utilisateur dans des chemins absolus, et des messages de commit
    citaient des interprètes réels."""

    FICHIERS = ["*.py", "*.js", "*.yml", "*.md", "*.toml"]

    def _tous(self):
        """Les fichiers que git SUIT, non ceux du disque.

        Un rapport d'audit posé dans le dossier de travail cite le nom
        réel du mainteneur : c'est normal, il ne partira jamais. Le
        signaler ferait passer un contrôle utile pour un contrôle
        bruyant, et on cesserait de le lire.
        """
        import subprocess
        try:
            r = subprocess.run(["git", "ls-files"], cwd=RACINE,
                               capture_output=True, text=True,
                               check=True)
            suivis = {RACINE / ligne for ligne in r.stdout.split("\n")
                      if ligne.strip()}
        except (OSError, subprocess.CalledProcessError):
            suivis = None      # hors dépôt : tout examiner
        for motif in self.FICHIERS:
            for f in RACINE.rglob(motif):
                if any(x in f.parts for x in
                       (".git", "fixtures_locales", "__pycache__",
                        "node_modules")):
                    continue
                if suivis is not None and f not in suivis:
                    continue
                yield f

    def test_aucun_chemin_absolu_personnel(self):
        motif = re.compile(r"/(home|Users)/(?!<)[a-z][\w.-]+/")
        fautes = [f.name for f in self._tous()
                  if motif.search(f.read_text(encoding="utf-8",
                                              errors="ignore"))]
        assert fautes == [], fautes

    def test_aucune_forme_de_l_identite_reelle(self):
        """Nom, patronyme, identifiants de comptes, initiales,
        pseudonymes abandonnés.

        La liste vit HORS du dépôt, dans `tests/identite_locale.py`
        ignoré par git : l'écrire ici la divulguerait exactement autant
        que la fuite qu'on cherche à empêcher. Le contrôle s'abstient
        quand le fichier est absent — un contributeur extérieur lance
        le reste de la suite sans rien voir."""
        try:
            from identite_locale import FORMES
        except ImportError:
            pytest.skip("tests/identite_locale.py absent — le créer "
                        "depuis identite_locale.exemple.py")
        motifs = [(f, re.compile(re.escape(f), re.I)) for f in FORMES
                  if len(f) >= 4]
        fautes = []
        for fichier in self._tous():
            if fichier.name in ("identite_locale.py",
                                "identite_locale.exemple.py"):
                continue
            texte = fichier.read_text(encoding="utf-8", errors="ignore")
            for forme, motif in motifs:
                m = motif.search(texte)
                if m:
                    ligne = texte[:m.start()].count("\n") + 1
                    fautes.append(f"{fichier.name}:{ligne} « {forme} »")
        assert fautes == [], fautes

    def test_aucun_nom_d_interprete_cite(self):
        """Un dépôt public expose ce que la collection contient. Citer
        un interprète en exemple, même dans un commentaire, décrit les
        goûts de celui qui publie — et ces gens sont réels.

        La règle de codage correspondante est ancienne : un défaut se
        décrit par sa FORME — « une date nulle », « un nom réduit à un
        mot » — jamais par la fiche qui l'a révélé. Cinq messages de
        commit y avaient contrevenu."""
        try:
            from identite_locale import INTERPRETES
        except ImportError:
            pytest.skip("tests/identite_locale.py absent")
        motifs = [re.compile(r"(?<![\w/])" + re.escape(n) + r"(?![\w/])")
                  for n in INTERPRETES if len(n) >= 4]
        fautes = []
        for f in self._tous():
            if f.name in ("test_qualite.py",):
                continue
            if f.name in ("identite_locale.py",
                          "identite_locale.exemple.py"):
                continue
            texte = f.read_text(encoding="utf-8", errors="ignore")
            for motif in motifs:
                m = motif.search(texte)
                if m:
                    ligne = texte[:m.start()].count("\n") + 1
                    fautes.append(f"{f.name}:{ligne} « {m.group(0)} »")
        assert fautes == [], fautes

    def test_aucun_nom_d_auteur(self):
        """Le fichier LICENSE portait le nom complet de l'auteur.
        Aucun des contrôles précédents ne le voyait : ils cherchaient
        des chemins, des courriels et des secrets — pas un nom, qui ne
        ressemble à rien de particulier.

        La parade est de nommer explicitement ce qui doit apparaître à
        la place, plutôt que d'essayer de reconnaître un nom propre."""
        # Le texte de l'AGPL ne nomme personne : le titulaire figure
        # dans les en-têtes de fichiers et le README, pas ici.
        licence = (RACINE / "LICENSE").read_text(encoding="utf-8")
        assert "GNU AFFERO GENERAL PUBLIC LICENSE" in licence.upper()
        # Un « Copyright (c) ANNÉE Prénom Nom » est la forme à bannir.
        motif = re.compile(
            r"Copyright\s*\(c\)\s*\d{4}\s+([A-Z][a-zà-ÿ]+"
            r"(?:[- ][A-Z][a-zà-ÿ]+){1,3})")
        for f in self._tous():
            m = motif.search(f.read_text(encoding="utf-8",
                                         errors="ignore"))
            assert not m, f"{f.name} : « {m.group(1)} »"

    def test_aucune_adresse_de_courriel(self):
        # Le motif démarre au DÉBUT du mot et écarte l'hôte SSH d'une
        # adresse de dépôt : « git@github.com » n'est pas un courriel,
        # et le confondre ferait rejeter toute publication.
        motif = re.compile(r"(?<![\w.+-])(?!git@)[\w.+-]+@"
                           r"[\w-]+\.[\w.]+")
        fautes = []
        for f in self._tous():
            for m in motif.findall(f.read_text(encoding="utf-8",
                                               errors="ignore")):
                if m.endswith((".example", ".test", ".invalid")):
                    continue
                fautes.append(f"{f.name}:{m}")
        assert fautes == [], fautes

    def test_aucune_adresse_de_machine_locale(self):
        motif = re.compile(r"\b(?:192\.168|10\.\d+|172\.(?:1[6-9]|2\d|3[01]))"
                           r"\.\d+\.\d+\b")
        fautes = []
        for f in self._tous():
            # Les fichiers de sécurité citent ces formes pour les
            # refuser ; llm.py et sa table décrivent l'adresse d'un
            # modèle installé chez soi, ce qui est un usage et non une
            # fuite.
            if f.name in ("test_securite.py", "test_qualite.py",
                          "llm.py", "llm_providers.yml",
                          "test_llm.py", "test_noyau.py",
                          "test_reglages.py",
                          # Éprouve précisément l'exception qui admet
                          # l'adresse de Stash et refuse ses voisines.
                          "test_vision.py"):
                continue
            if motif.search(f.read_text(encoding="utf-8",
                                        errors="ignore")):
                fautes.append(f.name)
        assert fautes == [], fautes

    def test_aucun_secret_en_dur(self):
        """Une clé oubliée dans le code est publiée avec lui."""
        motifs = [re.compile(p) for p in (
            r"sk-[A-Za-z0-9]{16,}",
            r"ghp_[A-Za-z0-9]{20,}",
            r"AIza[A-Za-z0-9_-]{20,}",
            r"(?i)(api[_-]?key|token|password)\s*=\s*[\"'][^\"'{}\s]{16,}")]
        fautes = []
        for f in self._tous():
            if f.name in ("test_securite.py", "test_qualite.py"):
                continue
            texte = f.read_text(encoding="utf-8", errors="ignore")
            for m in motifs:
                if m.search(texte):
                    fautes.append(f.name)
                    break
        assert fautes == [], fautes


# ── Solidité des tests eux-mêmes ─────────────────────────────────────
class TestQualiteDesTests:
    """Un test sans assertion passe toujours. Un test qui appelle le
    réseau est lent et instable. Un test qui touche au vrai état du
    plugin le corrompt.

    Ces trois défauts se sont présentés sur ce projet."""

    TESTS = Path(__file__).resolve().parent

    def _fichiers(self):
        return [f for f in self.TESTS.glob("test_*.py")]

    def test_chaque_test_affirme_quelque_chose(self):
        muets = []
        for f in self._fichiers():
            code = f.read_text(encoding="utf-8")
            for m in re.finditer(r"    def (test_\w+)\(([^)]*)\):"
                                 r"((?:\n(?:        .*)?)*)", code):
                corps = m.group(3)
                # Un test qui vérifie l'ABSENCE d'exception n'a rien
                # à affirmer : l'appel qui ne lève pas EST
                # l'affirmation. Son nom doit le dire.
                sans_assert = ("assert" not in corps
                               and "pytest.raises" not in corps
                               and "pytest.skip" not in corps)
                dit_ce_qu_il_fait = re.search(
                    r"ne_leve_pas|_ne_leve|absent|_intact|"
                    r"n_interrompt|lecture_des|motifs_de", m.group(1))
                if sans_assert and not dit_ce_qu_il_fait:
                    muets.append(f"{f.name}:{m.group(1)}")
        assert muets == [], muets

    def test_aucun_appel_reseau(self):
        """Un test doit être autonome : ni stash-box, ni modèle de
        langage, ni catalogue distant. Faute de quoi la suite passe de
        cinq secondes à cinquante-quatre et dépend de l'état du
        réseau."""
        fautes = []
        for f in self._fichiers():
            # Ce fichier-ci et celui de sécurité CITENT ces motifs pour
            # les interdire : les compter serait se mordre la queue.
            if f.name in ("test_qualite.py", "test_securite.py",
                          "test_noyau.py", "test_vision.py"):
                continue
            code = f.read_text(encoding="utf-8")
            for interdit in ("urllib.request.urlopen", "requests.get",
                             "http://127.0.0.1:9999",
                             "socket.socket"):
                if interdit in code:
                    fautes.append(f"{f.name}:{interdit}")
        assert fautes == [], fautes

    def test_aucune_ecriture_hors_du_bac_a_sable(self):
        """Un test qui écrit dans le vrai fichier d'état corromprait
        l'installation de celui qui le lance."""
        fautes = []
        for f in self._fichiers():
            code = f.read_text(encoding="utf-8")
            if "etat_ecrire" in code and "ETAT_FICHIER" not in code:
                fautes.append(f"{f.name} écrit l'état sans l'isoler")
        assert fautes == [], fautes

    def test_les_faux_serveurs_ne_sont_pas_permissifs(self):
        """Un faux serveur qui accepte tout rend les tests inutiles
        sans qu'on s'en aperçoive : ils passent et ne prouvent rien.
        Trois filtres ont dû y être ajoutés après coup."""
        faux = (self.TESTS / "faux.py").read_text(encoding="utf-8")
        for filtre in ("performers", "studios", "tags"):
            assert f'"{filtre}" in requete' in faux, \
                f"le filtre par {filtre} n'est pas honoré"
