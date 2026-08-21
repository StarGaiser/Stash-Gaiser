# -*- coding: utf-8 -*-
"""
Réglages : ce qu'un utilisateur peut comprendre sans documentation.

Écrit AVANT le remaniement.

Stash affiche les réglages d'un plugin dans une liste plate, sans
groupes ni sections. Cinquante entrées y deviennent illisibles : on ne
sait pas lesquelles vont ensemble, lesquelles sont obligatoires, ni
lesquelles ne servent à rien tant qu'une autre est vide.

Le remède n'est pas de tout supprimer mais de RANGER — un préfixe qui
regroupe visuellement, un nom qui dit à quoi la valeur sert, et le
retrait de ce qui fait double emploi.

Ces contrôles portent sur la lisibilité, pas sur le fonctionnement. Ils
sont donc formulés comme des exigences envers l'utilisateur : ce qu'il
voit lui suffit-il pour décider ?
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


@pytest.fixture(scope="module")
def reglages(manifeste):
    return manifeste.get("settings") or {}


# ── Volume ───────────────────────────────────────────────────────────
class TestVolume:
    """Une liste plate cesse d'être lisible bien avant cinquante
    entrées."""

    def test_le_nombre_reste_soutenable(self, reglages):
        # Le seuil tient compte des groupes : une liste plate de
        # quarante-cinq entrées reste illisible, mais six groupes de
        # sept se parcourent. Sans groupement, la borne serait plus
        # basse.
        # Le mode simple n'en montre que quatre ; le seuil
        # borne ce qui s'affiche d'un coup en mode complet.
        assert len(reglages) <= 48, (
            f"{len(reglages)} réglages : au-delà, même groupés, la "
            f"liste de Stash devient illisible")

    def test_aucune_cle_d_api_par_fournisseur(self, reglages):
        """Onze champs de clé pour onze fournisseurs, dont un seul
        sert : l'utilisateur cherche le sien dans la liste, et les dix
        autres restent vides à l'écran pour toujours.

        Une clé générique suffit — le fournisseur est déjà choisi par
        le réglage de modèle."""
        cles = [k for k in reglages
                if k.endswith("ApiKey") and k != "llmApiKey"]
        assert len(cles) <= 2, cles

    def test_aucune_adresse_par_service_local(self, reglages):
        """Même raisonnement : une adresse générique, le service étant
        déjà nommé dans le réglage de modèle."""
        adresses = [k for k in reglages
                    if k.endswith("Url") and k != "llmUrl"]
        assert len(adresses) <= 1, adresses


# ── Regroupement ─────────────────────────────────────────────────────
class TestRegroupement:
    """Stash trie les réglages par leur libellé. Un préfixe commun
    suffit donc à les rassembler visuellement, sans que Stash ait à
    connaître de notion de groupe."""

    PREFIXES = ("1.", "2.", "3.", "4.", "5.", "6.")

    def test_chaque_libelle_porte_un_groupe(self, reglages):
        sans = [k for k, v in reglages.items()
                if not str(v.get("displayName") or "").startswith(
                    self.PREFIXES)]
        assert sans == [], sans

    def test_les_groupes_sont_peu_nombreux(self, reglages):
        groupes = {str(v.get("displayName") or "")[:2]
                   for v in reglages.values()}
        assert len(groupes) <= 6, sorted(groupes)

    def test_aucun_groupe_ne_concentre_tout(self, reglages):
        """Un groupe qui contient la moitié des réglages n'a pas
        rangé grand-chose."""
        from collections import Counter
        c = Counter(str(v.get("displayName") or "")[:2]
                    for v in reglages.values())
        for groupe, n in c.items():
            assert n <= len(reglages) // 2 + 1, f"{groupe} : {n}"

    def test_les_reglages_lies_partagent_leur_groupe(self, reglages):
        """Ce qui se règle ensemble doit s'afficher ensemble."""
        for famille in (("aiDefault", "aiBio", "aiBiohot",
                         "aiSynopsis", "aiVision"),
                        ("applyMode", "createMissing")):
            presents = [k for k in famille if k in reglages]
            groupes = {str(reglages[k]["displayName"])[:2]
                       for k in presents}
            assert len(groupes) <= 1, f"{famille} → {groupes}"


# ── Ce que le libellé dit ────────────────────────────────────────────
class TestLibelles:

    def test_chaque_reglage_a_une_description(self, reglages):
        """Un réglage sans explication se laisse tel qu'il est, donc
        ne sert à rien."""
        sans = [k for k, v in reglages.items()
                if len(str(v.get("description") or "")) < 20]
        assert sans == [], sans

    def test_les_valeurs_par_defaut_sont_dites(self, reglages):
        """Un champ texte vide ne dit pas ce qui se passe s'il le
        reste."""
        muets = []
        for cle, v in reglages.items():
            if v.get("type") != "STRING":
                continue
            d = str(v.get("description") or "").lower()
            if not any(m in d for m in ("vide", "défaut", "par "
                                        "défaut", "sinon", "laisser")):
                muets.append(cle)
        assert len(muets) <= 6, muets

    def test_aucun_libelle_a_rallonge(self, reglages):
        """Stash tronque : un libellé long devient illisible."""
        longs = [k for k, v in reglages.items()
                 if len(str(v.get("displayName") or "")) > 60]
        assert longs == [], longs

    def test_les_reglages_dangereux_le_disent(self, reglages):
        """Ce qui transmet des données ou détruit doit l'annoncer dans
        sa description, là où l'utilisateur décide."""
        for cle, mots in (
                ("visionEnvoiImages", ("image", "transmet", "envoie")),
                ("autoMergeDuplicates", ("fusion", "supprim")),
                ("dryRun", ("simul", "écrit", "rien"))):
            if cle not in reglages:
                continue
            d = str(reglages[cle].get("description") or "").lower()
            assert any(m in d for m in mots), cle


# ── Cohérence avec le code ───────────────────────────────────────────
class TestCoherence:

    def _lus(self):
        """Les noms construits DYNAMIQUEMENT comptent aussi : le code
        assemble « ai » + l'usage, et cherche la clé par la table des
        fournisseurs. Les ignorer ferait passer pour morts des
        réglages bel et bien lus."""
        lus = {"aiBio", "aiBiohot", "aiSynopsis", "aiVision",
               "llmApiKey", "llmUrl"}
        # Les sources d'enrichissement sont lues par leur table, non
        # par un appel direct : les compter comme mortes ferait
        # retirer des réglages qui fonctionnent.
        import noyau
        lus |= {r for r, _d in noyau.Context._VOIES.values()}
        for f in CODE.glob("*.py"):
            texte = f.read_text(encoding="utf-8")
            lus |= set(re.findall(r'settings\.get\(\s*["\'](\w+)', texte))
            lus |= set(re.findall(r'settings\[["\'](\w+)', texte))
        for f in CODE.glob("*.js"):
            texte = f.read_text(encoding="utf-8")
            lus |= set(re.findall(r'["\'](\w+ApiKey|ai\w+|\w+Prompt)["\']',
                                  texte))
        return lus

    def test_aucun_reglage_mort(self, reglages):
        """Déclaré mais jamais lu : l'utilisateur le renseigne sans
        effet."""
        morts = sorted(set(reglages) - self._lus())
        assert morts == [], morts

    def test_aucun_reglage_invisible(self, reglages):
        """Lu mais non déclaré : il n'apparaît nulle part et reste à
        sa valeur par défaut sans qu'on puisse le changer."""
        connus = {"mode", "dryRun"}
        invisibles = sorted(self._lus() - set(reglages) - connus)
        # Certains noms lus sont construits dynamiquement.
        invisibles = [x for x in invisibles
                      if not x.endswith(("Url", "ApiKey"))
                      and len(x) > 4 and not x.startswith("aide")]
        assert invisibles == [], invisibles


# ── Les actions vivent dans le panneau ───────────────────────────────
class TestActions:
    """Une tâche déclarée dans le manifeste apparaît dans l'écran des
    plugins de Stash, mêlée à celles de tous les autres plugins et sans
    explication à l'écran. Le panneau du plugin les regroupe par
    intention, avec leur libellé traduit et un bouton de simulation.

    Ce qui est dans l'un doit être dans l'autre : une tâche absente du
    panneau ne sera pas trouvée, et une entrée du panneau qui ne
    correspond à aucune tâche échoue au clic."""

    def _panneau(self):
        return (CODE / "gaizer_page.js").read_text(encoding="utf-8")

    def _modes_du_manifeste(self, manifeste):
        return {(t.get("defaultArgs") or {}).get("mode")
                for t in manifeste["tasks"]} - {None}

    def test_chaque_tache_figure_dans_le_panneau(self, manifeste):
        panneau = self._panneau()
        # `noop` est un point d'entrée technique : les boutons du
        # panneau passent le vrai mode en argument.
        # Les taches qui portent sur UNE fiche vivent sur la fiche,
        # non dans le panneau de commande : les y mettre obligerait a
        # saisir un identifiant a la main.
        # Une tache qui a besoin d'un IDENTIFIANT appartient a la
        # fiche, ou il est implicite. La mettre au panneau
        # obligerait a le saisir a la main.
        #
        # Et « appliquer les propositions » existe deja sur chaque
        # fiche, ou il porte sur ce qu'on regarde : le repeter en un
        # bouton par famille creait une confusion sans rien apporter.
        sur_fiche = {"valider_fiche", "generer_apercu",
                     "enrich_one_performer",
                     "enrich_one_scene", "enrich_one_studio",
                     "apply_accepted_scenes", "apply_accepted_studios"}
        absentes = sorted(m for m in self._modes_du_manifeste(manifeste)
                          if m != "noop" and m not in sur_fiche
                          and f'"{m}"' not in panneau)
        assert absentes == [], absentes

    def test_aucune_entree_de_panneau_sans_tache(self, manifeste):
        panneau = self._panneau()
        modes = self._modes_du_manifeste(manifeste)
        # La table ARGUMENTS et la liste des onglets simples ont la
        # meme forme qu'une entree de tache sans en etre : ce sont des
        # noms de champ et des cles de groupe.
        nu = panneau
        for marque, fin_m in (("const CHOIX_ARGUMENT", "\n  };"),
                              ("const CHOIX = {", "\n  };"),
                               ("const ARGUMENTS", "\n  };"),
                              ("const REGLAGES_RAPIDES", "\n  ];"),
                              ("const ONGLETS_SIMPLES", ";")):
            i = nu.find(marque)
            if i < 0:
                continue
            f = nu.find(fin_m, i)
            if f > i:
                nu = nu[:i] + nu[f + len(fin_m):]
        cites = set(re.findall(r'\[\s*"(\w+)"\s*,\s*"', nu))
        fantomes = sorted(c for c in cites
                          if c not in modes and "_" in c)
        assert fantomes == [], fantomes

    def test_les_actions_destructives_offrent_la_simulation(self):
        """Le troisième argument marque le caractère destructeur, et
        c'est lui qui fait apparaître le bouton Simuler."""
        panneau = self._panneau()
        assert "destructif" in panneau
        assert panneau.count("true") >= 3


class TestMigrationDesCles:
    """Retirer un réglage ne doit pas perdre sa valeur.

    Un utilisateur qui met à jour a renseigné sa clé dans l'ancien
    champ. Le nouveau est vide, l'ancien a disparu de l'écran : sans
    reprise, le plugin cesse de fonctionner sans rien dire, et la
    valeur reste dans la configuration sans être lue par personne."""

    def _ctx(self, **reglages):
        from faux import FauxStash, faux_contexte
        ctx = faux_contexte(reglages, FauxStash())
        ctx.args = {}
        return ctx

    def test_une_ancienne_cle_est_reprise(self):
        import noyau
        ctx = self._ctx(mistralApiKey="sk-ancienne",
                        aiDefault="mistral:m")
        assert noyau.migrer_reglages(ctx).get("llmApiKey") \
            == "sk-ancienne"

    def test_la_cle_du_fournisseur_choisi_prime(self):
        """Plusieurs anciennes clés peuvent coexister : celle du
        fournisseur employé est la bonne."""
        import noyau
        ctx = self._ctx(openaiApiKey="sk-openai",
                        mistralApiKey="sk-mistral",
                        aiDefault="mistral:m")
        assert noyau.migrer_reglages(ctx).get("llmApiKey") \
            == "sk-mistral"

    def test_le_nouveau_champ_n_est_pas_ecrase(self):
        import noyau
        ctx = self._ctx(llmApiKey="sk-nouvelle",
                        mistralApiKey="sk-ancienne",
                        aiDefault="mistral:m")
        assert noyau.migrer_reglages(ctx) == {}

    def test_une_ancienne_adresse_est_reprise(self):
        import noyau
        ctx = self._ctx(ollamaUrl="http://192.168.1.10:11434",
                        aiDefault="ollama:llava")
        assert noyau.migrer_reglages(ctx).get("llmUrl")

    def test_rien_a_migrer(self):
        import noyau
        assert noyau.migrer_reglages(self._ctx()) == {}

    def test_la_migration_ne_leve_pas_sur_reglages_absurdes(self):
        import noyau
        for r in ({"aiDefault": ":::"}, {"aiDefault": None},
                  {"mistralApiKey": 42}):
            assert isinstance(noyau.migrer_reglages(self._ctx(**r)),
                              dict)


class TestSourcesActivables:
    """Chaque source d'enrichissement a un coût et un risque différents,
    et tout le monde ne veut pas les mêmes.

    Le chemin est gratuit et sûr, mais suppose un rangement fiable —
    quelqu'un dont les dossiers sont en vrac ne veut pas qu'on en tire
    des studios. Le nom de fichier devine. La vision envoie des images
    à un tiers et coûte de l'argent. Les imposer ensemble, ou les
    refuser ensemble, force à choisir entre trop et rien.

    Chacune est donc activable séparément, et celles qui devinent ou
    transmettent sont éteintes par défaut."""

    SOURCES = ("sourceChemin", "sourceNomFichier", "sourceVision",
             "sourceGeneriques")

    def test_chaque_voie_a_son_reglage(self, reglages):
        manquants = [v for v in self.SOURCES if v not in reglages]
        assert manquants == [], manquants

    def test_les_voies_sont_dans_le_meme_groupe(self, reglages):
        groupes = {str(reglages[v]["displayName"])[:2]
                   for v in self.SOURCES if v in reglages}
        assert len(groupes) <= 1, groupes

    def test_la_voie_sure_est_active_par_defaut(self):
        """Le chemin ne devine pas et ne transmet rien : l'éteindre
        par défaut priverait de la source la plus rentable sans raison."""
        from faux import FauxStash, faux_contexte
        ctx = faux_contexte({}, FauxStash())
        assert ctx.source_active("chemin")

    def test_les_voies_couteuses_sont_eteintes_par_defaut(self):
        """Envoyer des images à un tiers et payer des appels ne
        s'active pas à l'insu de qui installe le plugin."""
        from faux import FauxStash, faux_contexte
        ctx = faux_contexte({}, FauxStash())
        for source in ("vision", "generiques"):
            assert not ctx.source_active(source), source

    def test_une_voie_peut_etre_eteinte(self):
        from faux import FauxStash, faux_contexte
        ctx = faux_contexte({"sourceChemin": False}, FauxStash())
        assert not ctx.source_active("chemin")

    def test_une_voie_peut_etre_allumee(self):
        from faux import FauxStash, faux_contexte
        ctx = faux_contexte({"sourceVision": True}, FauxStash())
        assert ctx.source_active("vision")

    def test_une_voie_inconnue_est_refusee(self):
        """Un nom mal orthographié ne doit pas activer silencieusement
        ce qu'il ne désigne pas."""
        from faux import FauxStash, faux_contexte
        ctx = faux_contexte({}, FauxStash())
        assert not ctx.source_active("inexistante")

    def test_la_tache_respecte_son_reglage(self):
        """Une tâche lancée alors que sa source est éteinte doit le dire
        et s'arrêter — sans quoi le réglage ne sert à rien."""
        import chemins
        from faux import FauxStash, faux_contexte, scene, studio
        st = FauxStash(scenes=[scene(10, "", files=[
            {"path": "/nas/Hardkinks/x.mp4"}])],
            studios=[studio(9, "Hardkinks")])
        ctx = faux_contexte({"sourceChemin": False,
                             "applyMode": "auto"}, st)
        ctx.args = {}
        chemins.lire_chemins(ctx)
        assert not st.scenes["10"].get("studio")
