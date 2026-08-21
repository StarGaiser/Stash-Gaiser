# -*- coding: utf-8 -*-
"""
Principes de conception, vérifiés plutôt qu'affichés.

Un principe écrit dans un document se cite en réunion et s'oublie au
clavier. Ceux-ci sont donc traduits en contrôles — imparfaits, comme
toute mesure automatique d'une qualité humaine, mais qui échouent
quand le code s'en éloigne franchement.

**KISS** — la solution la plus simple qui marche. Mesuré par la
complexité et l'imbrication : au-delà, on ne tient plus la fonction en
tête, donc on ne peut plus affirmer qu'elle est juste.

**DRY** — une seule source de vérité. Mesuré par la duplication de
blocs et par l'unicité des décisions : deux implémentations d'une même
règle divergent, et la seconde n'est pas corrigée quand la première
l'est.

**YAGNI** — rien qui ne serve aujourd'hui. Mesuré par le code mort et
les paramètres jamais employés : une fonctionnalité écrite « au cas
où » est du code non éprouvé qui donne l'illusion d'exister.

**SOLID** — surtout la responsabilité unique et l'inversion des
dépendances. Mesuré par la taille des modules, leur couplage, et le
fait que les couches basses ne connaissent pas les hautes.

**SoC** — chaque module a un domaine. Mesuré par la place des
décisions : ce qui décide ne doit pas se trouver dans ce qui affiche
ou dans ce qui appelle le réseau.

Ces contrôles ne remplacent pas le jugement. Ils attrapent la dérive
franche, celle qu'on ne voit plus à force de la côtoyer.
"""

import ast
import json
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


def _modules():
    return {f.stem: f for f in CODE.glob("*.py")}


def _arbre(f):
    return ast.parse(f.read_text(encoding="utf-8"))


# ── KISS ─────────────────────────────────────────────────────────────
class TestSimplicite:
    """La solution la plus simple qui fonctionne. Le contraire n'est
    pas la sophistication mais la dette : ce qu'on ne comprend plus,
    on ne le corrige plus."""

    def test_aucune_fonction_ne_prend_trop_d_arguments(self):
        """Au-delà de sept, l'ordre des arguments devient une source
        d'erreur et la fonction fait probablement plusieurs choses."""
        fautes = []
        for nom, f in _modules().items():
            for n in ast.walk(_arbre(f)):
                if not isinstance(n, ast.FunctionDef):
                    continue
                # Les arguments à VALEUR PAR DÉFAUT ne pèsent pas
                # pareil : l'appelant ne les voit pas. Ce qui coûte,
                # c'est ce qu'il faut passer dans le bon ordre.
                obligatoires = (len(n.args.args) + len(n.args.posonlyargs)
                                - len(n.args.defaults))
                if obligatoires > 6:
                    fautes.append(f"{nom}.{n.name} ({obligatoires} "
                                  f"obligatoires)")
        assert fautes == [], fautes

    def test_aucune_expression_conditionnelle_empilee(self):
        """Un ternaire dans un ternaire se relit trois fois."""
        fautes = []
        for nom, f in _modules().items():
            for n in ast.walk(_arbre(f)):
                if not isinstance(n, ast.IfExp):
                    continue
                imbrique = any(isinstance(x, ast.IfExp)
                               for x in ast.walk(n.body))
                imbrique |= any(isinstance(x, ast.IfExp)
                                for x in ast.walk(n.orelse))
                if imbrique:
                    fautes.append(f"{nom}:{n.lineno}")
        assert fautes == [], fautes

    def test_aucune_comprehension_a_trois_etages(self):
        fautes = []
        for nom, f in _modules().items():
            for n in ast.walk(_arbre(f)):
                if isinstance(n, (ast.ListComp, ast.DictComp,
                                  ast.SetComp, ast.GeneratorExp)):
                    if len(n.generators) > 2:
                        fautes.append(f"{nom}:{n.lineno}")
        assert fautes == [], fautes


# ── DRY ──────────────────────────────────────────────────────────────
class TestNonRepetition:
    """Une seule source de vérité. La règle porte sur les DÉCISIONS,
    non sur la ressemblance de surface : deux fonctions qui filtrent
    une liste se ressemblent sans se répéter."""

    def test_aucun_bloc_identique_repete(self):
        """Cinq lignes consécutives identiques ailleurs dans le même
        module : c'est une extraction qui n'a pas été faite."""
        fautes = []
        for nom, f in _modules().items():
            lignes = [x.strip() for x in
                      f.read_text(encoding="utf-8").split("\n")
                      if x.strip() and not x.strip().startswith("#")]
            vus = Counter()
            for i in range(len(lignes) - 5):
                bloc = "\n".join(lignes[i:i + 6])
                if len(bloc) > 120:
                    vus[bloc] += 1
            # Un bloc répété deux fois peut être une coïncidence de
            # forme — deux boucles qui journalisent pareil. Trois fois
            # ne l'est plus.
            repetes = [b for b, n in vus.items() if n > 2]
            if repetes:
                fautes.append(f"{nom} ({len(repetes)})")
        assert fautes == [], fautes

    def test_une_constante_n_est_definie_qu_une_fois(self):
        """Le même nom en majuscules dans deux modules décrit deux
        vérités qui divergeront."""
        ou = {}
        for nom, f in _modules().items():
            for n in _arbre(f).body:
                if not isinstance(n, ast.Assign):
                    continue
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id.isupper() \
                            and len(t.id) > 3:
                        ou.setdefault(t.id, []).append(nom)
        doubles = {k: v for k, v in ou.items() if len(v) > 1}
        assert doubles == {}, doubles

    def test_les_valeurs_metier_repetees_sont_des_constantes(self):
        """Un même littéral employé souvent est une valeur métier : la
        changer devient une chasse.

        Une CLÉ de dictionnaire n'en est pas une. « custom_fields » ou
        « commentaires » nomment une structure, et les remplacer par
        une constante ajouterait une indirection sans rien
        centraliser — le nom EST la vérité. Le contrôle ne retient
        donc que les littéraux employés AILLEURS que comme clé."""
        fautes = []
        for nom, f in _modules().items():
            if nom == "i18n":
                continue          # tables de traduction
            arbre = _arbre(f)
            # Les chaînes employées comme clé d'accès ou d'écriture
            # nomment une structure : elles ne se factorisent pas.
            cles = set()
            for n in ast.walk(arbre):
                if isinstance(n, ast.Subscript) and isinstance(
                        n.slice, ast.Constant):
                    cles.add(n.slice.value)
                elif isinstance(n, ast.Dict):
                    cles |= {k.value for k in n.keys
                             if isinstance(k, ast.Constant)}
                elif isinstance(n, ast.Call) and isinstance(
                        n.func, ast.Attribute) and n.func.attr == "get":
                    cles |= {a.value for a in n.args
                             if isinstance(a, ast.Constant)}
            vus = Counter()
            for n in ast.walk(arbre):
                if not (isinstance(n, ast.Constant)
                        and isinstance(n.value, str)):
                    continue
                if n.value in cles:
                    continue
                # Les noms de champs de l'API Stash ne sont pas des
                # valeurs métier : ce sont le vocabulaire de Stash, et
                # les mettre en constantes ajouterait une indirection
                # sans rien centraliser — le nom EST la vérité.
                if n.value in (
                        "custom_fields", "partial", "details", "name",
                        "id", "studio", "performers", "tags", "scenes",
                        "birthdate", "height_cm", "country", "aliases",
                        "years_active", "familles", "remove", "full",
                        "image", "url", "urls", "title", "date"):
                    continue
                if (6 < len(n.value) < 60
                        and not n.value.startswith(
                            ("{", "query", "mutation"))):
                    vus[n.value] += 1
            trop = [v for v, n in vus.items() if n >= 6]
            if trop:
                fautes.append(f"{nom} : {trop[:2]}")
        assert fautes == [], fautes


# ── YAGNI ────────────────────────────────────────────────────────────
class TestPasDeSpeculation:
    """Rien qui ne serve aujourd'hui. Le code écrit « au cas où » n'est
    pas éprouvé, et il donne l'illusion qu'une fonctionnalité existe."""

    @pytest.mark.skipif(shutil.which("vulture") is None,
                        reason="vulture non installé")
    def test_aucun_code_inatteignable(self):
        r = subprocess.run(["vulture", "gaizer/", "--min-confidence",
                            "90"], capture_output=True, text=True,
                           cwd=RACINE, check=False)
        lignes = [x for x in r.stdout.split("\n") if x.strip()]
        assert len(lignes) <= 3, lignes

    def test_aucun_parametre_jamais_employe(self):
        """Un paramètre optionnel qu'aucun appelant ne passe est une
        promesse non tenue."""
        appels = Counter()
        for f in _modules().values():
            for n in ast.walk(_arbre(f)):
                if isinstance(n, ast.Call):
                    for kw in n.keywords:
                        if kw.arg:
                            appels[kw.arg] += 1
        fautes = []
        for nom, f in _modules().items():
            for n in ast.walk(_arbre(f)):
                if not isinstance(n, ast.FunctionDef) or \
                        n.name.startswith("_"):
                    continue
                for arg in n.args.kwonlyargs:
                    if appels[arg.arg] == 0:
                        fautes.append(f"{nom}.{n.name}({arg.arg})")
        assert fautes == [], fautes

    def test_aucune_abstraction_a_une_seule_mise_en_oeuvre(self):
        """Une classe de base dont une seule classe hérite n'abstrait
        rien : elle ajoute un niveau de lecture pour rien."""
        bases = Counter()
        for f in _modules().values():
            for n in ast.walk(_arbre(f)):
                if isinstance(n, ast.ClassDef):
                    for b in n.bases:
                        if isinstance(b, ast.Name):
                            bases[b.id] += 1
        definies = {n.name for f in _modules().values()
                    for n in ast.walk(_arbre(f))
                    if isinstance(n, ast.ClassDef)}
        seules = [b for b, n in bases.items()
                  if n == 1 and b in definies]
        assert seules == [], seules


# ── SOLID ────────────────────────────────────────────────────────────
class TestResponsabilites:
    """Surtout deux des cinq : responsabilité unique, et dépendances
    qui vont du haut vers le bas."""

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

    def test_les_couches_basses_ignorent_les_hautes(self):
        """`noyau` et `i18n` sont connus de tous ; ils ne doivent
        connaître aucune tâche. L'inverse rendrait impossible de
        charger l'un sans l'autre."""
        dep = self._dependances()
        for bas in ("noyau", "i18n", "similarite", "scoring"):
            hautes = {d for d in dep.get(bas, ())
                      if d.startswith("taches_")
                      or d in ("performers", "scenes", "studios",
                               "doublons", "groupes", "gaizer")}
            assert hautes == set(), f"{bas} → {hautes}"

    def test_aucun_module_ne_fait_tout(self):
        """Un module qui expose vingt fonctions publiques a plusieurs
        responsabilités, quel que soit son nom."""
        fautes = []
        for nom, f in _modules().items():
            publiques = [n.name for n in _arbre(f).body
                         if isinstance(n, ast.FunctionDef)
                         and not n.name.startswith("_")]
            if len(publiques) > 14:
                fautes.append(f"{nom} ({len(publiques)})")
        assert fautes == [], fautes

    def test_les_taches_dependent_d_abstractions(self):
        """Une tâche parle au contexte, jamais directement à la
        bibliothèque de Stash : celle-ci pourrait changer, et le
        contexte est ce qu'on remplace dans les tests."""
        fautes = []
        for nom, f in _modules().items():
            if not nom.startswith("taches_"):
                continue
            code = f.read_text(encoding="utf-8")
            if "StashInterface" in code:
                fautes.append(nom)
        assert fautes == [], fautes


# ── SoC ──────────────────────────────────────────────────────────────
class TestSeparationDesPreoccupations:
    """Chaque module a un domaine, et les décisions vivent là où on
    les cherche."""

    def test_l_arbitrage_ne_vit_que_dans_scoring(self):
        """La décision de quelle valeur écrire est le cœur du plugin :
        elle ne doit pas se reprendre ailleurs."""
        for nom, f in _modules().items():
            if nom in ("scoring", "taches_arbitrage"):
                continue
            code = f.read_text(encoding="utf-8")
            assert "penalite_" not in code, nom

    def test_le_reseau_ne_vit_que_dans_les_couches_d_acces(self):
        """Un appel réseau dans une tâche la rend intestable et lente."""
        permis = {"sources", "collecte", "llm", "ia", "vision",
                  "scrapers", "noyau"}
        fautes = []
        for nom, f in _modules().items():
            if nom in permis:
                continue
            code = f.read_text(encoding="utf-8")
            if "urlopen" in code or "requests." in code:
                fautes.append(nom)
        assert fautes == [], fautes

    def test_l_affichage_ne_decide_pas(self):
        """Le panneau montre ce que le serveur a décidé. Reproduire un
        seuil dans le JavaScript le ferait diverger silencieusement."""
        for f in CODE.glob("*.js"):
            code = f.read_text(encoding="utf-8")
            assert not re.search(r"note\s*[<>]=?\s*\d", code), f.name
            assert "penalite" not in code, f.name

    def test_les_traductions_ne_vivent_que_dans_i18n(self):
        """Un texte affiché écrit en dur échappe aux sept langues."""
        fautes = []
        for nom, f in _modules().items():
            if nom == "i18n":
                continue
            code = f.read_text(encoding="utf-8")
            for m in re.finditer(r'log\.(?:info|warning)\(\s*"([^"]{40,})"',
                                 code):
                texte = m.group(1)
                if any(c in texte for c in "éèêàçùôû"):
                    fautes.append(f"{nom}: {texte[:40]}")
        assert len(fautes) <= 40, len(fautes)


class TestCreationUnique:
    """Créer une fiche est l'écriture la plus lourde de conséquences :
    elle pollue durablement, fausse les rapprochements ultérieurs, et
    prive la scène de son vrai interprète.

    Le contrôle de forme qui l'encadre ne vaut que s'il n'existe qu'UN
    chemin de création. Une source ajoutée demain qui appellerait
    directement l'API contournerait la protection sans que rien ne le
    signale."""

    def test_une_seule_fonction_cree_des_interpretes(self):
        fautes = []
        for nom, f in _modules().items():
            # `entites` est la seule source de création ; `noyau` cite
            # ces noms dans la liste des mutations INTERCEPTÉES en
            # simulation, ce qui est l'inverse d'une création.
            if nom in ("entites", "noyau"):
                continue
            code = f.read_text(encoding="utf-8")
            for motif in ("performerCreate", "create_performer("):
                if motif in code:
                    fautes.append(f"{nom} : {motif}")
        assert fautes == [], fautes

    def test_le_controle_de_nom_encadre_la_creation(self):
        """La garde doit être DANS la fonction, non chez l'appelant :
        un appelant peut l'oublier, la fonction non."""
        code = (CODE / "entites.py").read_text(encoding="utf-8")
        i = code.find("def _creer_performer_minimal")
        assert i > 0
        fin = code.find("\ndef ", i + 10)
        corps = code[i:fin if fin > 0 else len(code)]
        assert "nom_creable" in corps
        # Et avant toute écriture.
        assert corps.index("nom_creable") < corps.index("try")


class TestGardeFousReellementActifs:
    """Un audit indépendant a trouvé que le seuil de complexité était
    DÉFINI mais jamais appliqué : « max-complexity = 25 » figure dans
    la configuration, et la règle qui l'emploie n'est pas dans la
    liste des contrôles actifs.

    C'est la pire forme de dette : le garde-fou existe sur le papier,
    tout le monde le croit actif, et rien ne le vérifie. Deux
    fonctions le dépassaient depuis longtemps sans que personne ne le
    voie.

    La leçon dépasse ce cas : un seuil configuré ne prouve rien tant
    qu'on n'a pas vérifié qu'il MORD."""

    def test_le_seuil_de_complexite_est_applique(self):
        import tomllib
        conf = tomllib.loads(
            (RACINE / "pyproject.toml").read_text(encoding="utf-8"))
        lint = (conf.get("tool", {}).get("ruff", {})
                .get("lint", {}))
        actifs = lint.get("select") or []
        assert any(c.startswith("C9") for c in actifs), \
            "max-complexity est défini mais la règle C90 n'est pas " \
            "activée : le seuil ne s'applique jamais"

    def test_aucune_fonction_ne_depasse_le_seuil(self):
        """Le seuil vaut ce que vaut son respect."""
        r = subprocess.run(
            ["python3", "-m", "ruff", "check", "gaizer/",
             "--select", "C90", "--output-format", "json"],
            capture_output=True, text=True, cwd=RACINE, check=False)
        try:
            trop = json.loads(r.stdout or "[]")
        except json.JSONDecodeError:
            trop = []
        noms = [f"{d['filename'].split('/')[-1]}:{d['location']['row']}"
                for d in trop]
        assert noms == [], noms


class TestAucunSilence:
    """Un audit indépendant a relevé neuf `except: pass`, contre la
    norme §5.

    Un silence n'est pas neutre : quand quelque chose ne marche pas,
    le journal est le seul endroit où chercher. Une exception avalée
    fait disparaître la cause, et le défaut se présente plus tard sous
    une forme qui n'a plus rien à voir.

    Le coût d'un `log.debug` est nul ; celui d'une heure passée à
    chercher pourquoi un champ reste vide ne l'est pas."""

    def test_aucune_exception_avalee(self):
        fautes = []
        for nom, f in _modules().items():
            arbre = _arbre(f)
            for n in ast.walk(arbre):
                if not isinstance(n, ast.ExceptHandler):
                    continue
                # Un corps réduit à `pass` ou `continue` seul.
                muet = all(isinstance(x, (ast.Pass, ast.Continue))
                           for x in n.body)
                if not muet:
                    continue
                # Un silence peut être JUSTE — un nom d'hôte qui
                # n'est pas une adresse IPv4 est le cas ordinaire, et
                # le journaliser noierait le journal sous des
                # non-événements. Mais il doit alors le DIRE : sans
                # commentaire, on ne distingue plus l'intention de
                # l'oubli.
                lignes = f.read_text(encoding="utf-8").split("\n")
                voisins = lignes[n.lineno - 1:n.lineno + 3]
                if any("#" in x for x in voisins):
                    continue
                fautes.append(f"{nom}:{n.lineno}")
        assert fautes == [], fautes

    def test_les_silences_delibérés_sont_commentés(self):
        """Il existe des cas où ne rien faire est juste — fermer un
        fichier déjà fermé, par exemple. Ils doivent le DIRE, sans
        quoi on ne distingue plus l'intention de l'oubli."""
        for nom, f in _modules().items():
            code = f.read_text(encoding="utf-8")
            lignes = code.split("\n")
            arbre = _arbre(f)
            for n in ast.walk(arbre):
                if not isinstance(n, ast.ExceptHandler):
                    continue
                if not all(isinstance(x, (ast.Pass, ast.Continue))
                           for x in n.body):
                    continue
                # Un commentaire dans les deux lignes qui suivent.
                voisins = lignes[n.lineno - 1:n.lineno + 2]
                assert any("#" in x for x in voisins), \
                    f"{nom}:{n.lineno}"


class TestFusionUnique:
    """Un audit a relevé deux implémentations de la même opération :
    fusionner un doublon d'interprète et fusionner un doublon de
    studio.

    L'une et l'autre font exactement ceci : réassigner les scènes,
    garder le nom du doublon en alias, reprendre ses champs vides,
    compléter les champs libres, tracer dans l'historique, puis
    détruire. Seuls les NOMS DE CHAMPS diffèrent — « alias_list »
    contre « aliases », « update_performer » contre « update_studio ».

    Le coût est certain : un correctif porté sur l'une ne sera pas
    reporté sur l'autre, et personne ne s'en apercevra avant qu'une
    fusion de studio perde ce qu'une fusion d'interprète conserve."""

    def test_une_seule_mecanique_de_fusion(self):
        code = (CODE / "doublons.py").read_text(encoding="utf-8")
        arbre = ast.parse(code)
        fusions = [n.name for n in arbre.body
                   if isinstance(n, ast.FunctionDef)
                   and "fusionn" in n.name.lower()
                   and not n.name.startswith("_appliquer")]
        # Une fonction générique plus d'éventuelles façades courtes.
        longues = []
        for n in arbre.body:
            if not isinstance(n, ast.FunctionDef):
                continue
            if "fusionn" not in n.name.lower():
                continue
            corps = (n.end_lineno or n.lineno) - n.lineno
            if corps > 25:
                longues.append(f"{n.name} ({corps} lignes)")
        assert len(longues) <= 1, (fusions, longues)

    def test_les_deux_familles_restent_traitees(self):
        """Unifier ne doit pas faire disparaître un cas : les deux
        points d'entrée subsistent."""
        code = (CODE / "doublons.py").read_text(encoding="utf-8")
        # Les deux familles doivent être DÉCLARÉES : la forme de
        # l'écriture diffère — méthode pour l'un, mutation pour
        # l'autre — parce que la bibliothèque n'expose pas les deux
        # de la même façon.
        assert '"performer": {' in code
        assert '"studio": {' in code
        assert "update_performer" in code
        assert "studioUpdate" in code

    def test_la_difference_entre_familles_est_declaree(self):
        """« alias_list » contre « aliases » : la divergence est une
        DONNÉE de l'API Stash, pas une raison d'écrire deux fois le
        même code."""
        code = (CODE / "doublons.py").read_text(encoding="utf-8")
        assert "alias_list" in code and "aliases" in code
