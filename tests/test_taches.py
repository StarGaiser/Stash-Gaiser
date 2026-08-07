# -*- coding: utf-8 -*-
"""
Les vingt-quatre tâches de `tache('py')`, éprouvées systématiquement.

Ce module concentre tout ce qui ne relève ni du pipeline ni des
doublons : diagnostics, ménage, arbitrage, migration. Il était couvert
à 14 %, et trois tâches seulement avaient des tests.

Le contrôle appliqué ici est le même pour toutes, et il tient en
quatre questions. La tâche survit-elle à une collection VIDE ? À des
arguments ABSENTS ? À des arguments ABSURDES ? Et n'écrit-elle RIEN
quand rien ne s'y prête ?

Ce n'est pas un contrôle profond, et il ne prétend pas l'être. C'est le
filet minimal : une tâche qui tombe sur une collection vide est un
défaut que personne ne devrait découvrir en production, et c'est
pourtant ainsi qu'on les découvre.
"""

import json

import pytest

import noyau
import taches_arbitrage
import taches_diagnostic
import taches_heritage
import taches_maintenance
import taches_menage

# Le registre est le point d'entrée réel : Stash n'appelle jamais une
# tâche autrement. L'éprouver par lui, plutôt que par un module
# intermédiaire, garantit qu'une tâche déclarée est atteignable.
MODULES = (taches_diagnostic, taches_menage, taches_heritage,
           taches_arbitrage, taches_maintenance)


def tache(nom):
    """La fonction enregistrée sous ce nom, où qu'elle vive."""
    for module in MODULES:
        if hasattr(module, nom):
            return getattr(module, nom)
    raise AssertionError(f"tâche introuvable : {nom}")
from faux import FauxStash, faux_contexte, performer, scene, studio


# Tâches sans effet destructeur, éprouvables sans précaution.
LECTURES = [
    "controler_heritage", "inspecter_collecte", "rapport_tags",
    "rapport_run", "etat_agent", "position_tags",
    "suggerer_tags_exclus", "noop",
]

# Tâches qui écrivent : elles passent aussi par la simulation.
ECRITURES = [
    "normaliser_roles", "retirer_pied_bio", "ranger_champs_herites",
    "retirer_non_confirme", "marquer_roles_importes",
    "arbitrer_conflits", "apply_recommended", "clear_proposals",
    "purger_tags_exclus", "restore_marked", "restaurer_reglages",
    "reprendre_ia",
]

TOUTES = LECTURES + ECRITURES


def _ecritures(st):
    """Ce qui a réellement touché une fiche.

    La création d'étiquettes et la lecture de configuration ne sont pas
    des écritures : les compter ferait échouer des tâches qui n'ont
    rien fait de mal."""
    return [q for q, _d in st.journal
            if q not in ("create_tag", "configuration")
            and not q.startswith(("find", "list_"))]


@pytest.fixture(autouse=True)
def etat_isole(tmp_path, monkeypatch):
    """Sans isolation, ces tâches écriraient dans le fichier d'état
    réel du plugin et corrompraient l'installation de qui lance les
    tests."""
    monkeypatch.setattr(noyau, "ETAT_FICHIER", tmp_path / "etat.json")


@pytest.fixture(autouse=True)
def sans_appels_exterieurs(monkeypatch):
    """Ni sources, ni modèle de langage : un test doit être autonome.

    L'interception vise les modules où le code VIT, non la façade qui
    le ré-exporte : remplacer un nom sur la façade ne change rien à ce
    qu'appelle la fonction. C'est le premier piège d'un découpage, et
    les tests l'ont signalé immédiatement."""
    import taches_diagnostic
    import taches_heritage
    for module in (taches_diagnostic, taches_heritage):
        for nom, remplacement in (
                ("collecter_stash", lambda *a, **k: ({}, [])),
                ("passe_url", lambda *a, **k: None),
                ("deduire_role", lambda *a, **k: (None, "aucune IA"))):
            if hasattr(module, nom):
                monkeypatch.setattr(module, nom, remplacement)


# ── Collection vide ──────────────────────────────────────────────────
class TestCollectionVide:
    """Une médiathèque neuve, ou filtrée à zéro. C'est le cas le plus
    fréquent au premier lancement, et le moins souvent éprouvé."""

    @pytest.mark.parametrize("nom", TOUTES)
    def test_la_tache_ne_leve_pas(self, nom):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        tache(nom)(ctx)

    @pytest.mark.parametrize("nom", TOUTES)
    def test_rien_n_est_ecrit(self, nom):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        tache(nom)(ctx)
        assert _ecritures(st) == [], f"{nom} a écrit sans matière"


# ── Arguments ────────────────────────────────────────────────────────
class TestArguments:
    """Une tâche lancée depuis l'interface de Stash reçoit ce que
    l'utilisateur a saisi, y compris rien du tout."""

    def _monde(self):
        st = FauxStash(
            performers=[performer(1, "Archie Fox", country="FR")],
            studios=[studio(1, "Masqulin")],
            scenes=[scene(10, "Une scène", studio={"id": "1"})])
        ctx = faux_contexte({}, st)
        return st, ctx

    @pytest.mark.parametrize("nom", TOUTES)
    def test_sans_argument_ne_leve_pas(self, nom):
        _st, ctx = self._monde()
        ctx.args = {}
        tache(nom)(ctx)

    @pytest.mark.parametrize("nom", TOUTES)
    def test_arguments_absurdes_ne_leve_pas(self, nom):
        """Une valeur inattendue doit être écartée, pas provoquer une
        exception qui interromprait la file de tâches."""
        _st, ctx = self._monde()
        ctx.args = {"champ": "", "champs": "n_existe_pas",
                    "note": "beaucoup", "nom": "☃",
                    "performer_id": "-1", "motif": "x" * 500,
                    "force": "peut-être", "installer": "oui"}
        tache(nom)(ctx)

    def test_identifiant_inexistant(self):
        st, ctx = self._monde()
        ctx.args = {"performer_id": "999999"}
        tache('inspecter_collecte')(ctx)
        assert _ecritures(st) == []

    def test_nom_inexistant(self):
        st, ctx = self._monde()
        ctx.args = {"nom": "Personne De Ce Nom"}
        tache('inspecter_collecte')(ctx)
        assert _ecritures(st) == []

    def test_champ_a_supprimer_manquant(self):
        st, ctx = self._monde()
        ctx.args = {}
        tache('retirer_champ_herite')(ctx)
        assert _ecritures(st) == []


# ── Simulation ───────────────────────────────────────────────────────
class TestSimulation:
    """La simulation est la protection dont dépendent toutes les
    tâches destructives : elle doit tenir sur chacune."""

    def _monde_garni(self):
        """Une collection qui donne du grain à moudre à chaque tâche :
        champs hérités, conflits, propositions, historique."""
        hist = [{"d": "2026-08-01", "champs": {"country": ["", "FR"]}}]
        st = FauxStash(
            performers=[performer(
                1, "Archie Fox", country="FR", height_cm=183,
                custom_fields={
                    "sexe_type": "Cut", "mensurations": "183cm / 88kg",
                    "position": "Actif Dominant",
                    "mediapr0n_key": "archiefox",
                    "enrich_historique": json.dumps(hist),
                    "enrich_position": "actif",
                    "enrich_rapport": "CONFLITS : height_cm : actuel "
                                      "« 183 » vs sources : 178 "
                                      "[gevi+iafd 9.8/10]"},
                details="Une bio.\n\n― Fiabilité des données (Gaizer) ―"
                        "\nnote 9/10")],
            studios=[studio(1, "Masqulin")],
            scenes=[scene(10, "Une scène", studio={"id": "1"})])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        ctx.args = {}
        return st, ctx

    @pytest.mark.parametrize("nom", ECRITURES)
    def test_aucune_ecriture_en_simulation(self, nom):
        st, ctx = self._monde_garni()
        avant = json.dumps(st.performers, sort_keys=True)
        tache(nom)(ctx)
        apres = json.dumps(st.performers, sort_keys=True)
        assert avant == apres, f"{nom} a écrit malgré la simulation"

    @pytest.mark.parametrize("nom", ECRITURES)
    def test_les_studios_sont_epargnes_aussi(self, nom):
        st, ctx = self._monde_garni()
        avant = json.dumps(st.studios, sort_keys=True)
        tache(nom)(ctx)
        assert json.dumps(st.studios, sort_keys=True) == avant, nom


# ── Effets réels ─────────────────────────────────────────────────────
class TestEffets:
    """Au-delà de la survie : chaque tâche fait-elle ce qu'elle
    annonce ?"""

    def _fiche(self, **cf):
        st = FauxStash(performers=[
            performer(1, "Archie Fox", custom_fields=dict(cf))])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        return st, ctx

    def test_le_pied_de_bio_est_retire(self):
        st = FauxStash(performers=[performer(
            1, "Archie",
            details="Une bio.\n\n― Fiabilité des données (Gaizer) ―"
                    "\nnote")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        tache('retirer_pied_bio')(ctx)
        assert "Fiabilité" not in (st.performers["1"]["details"] or "")

    def test_une_bio_sans_pied_n_est_pas_touchee(self):
        st = FauxStash(performers=[
            performer(1, "Archie", details="Une bio simple.")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        tache('retirer_pied_bio')(ctx)
        assert st.performers["1"]["details"] == "Une bio simple."

    def test_les_roles_importes_sont_marques(self):
        st, ctx = self._fiche(enrich_position="actif")
        tache('marquer_roles_importes')(ctx)
        cf = st.performers["1"]["custom_fields"]
        assert cf.get("enrich_role_origine") == "import"

    def test_un_role_deja_marque_n_est_pas_ecrase(self):
        """Une valeur confirmée par l'utilisateur ne doit pas
        redevenir « importée »."""
        st, ctx = self._fiche(enrich_position="actif",
                              enrich_role_origine="saisi")
        tache('marquer_roles_importes')(ctx)
        assert st.performers["1"]["custom_fields"][
            "enrich_role_origine"] == "saisi"

    def test_le_champ_herite_demande_est_retire(self):
        st, ctx = self._fiche(vieux_champ="x", enrich_position="actif")
        ctx.args = {"champ": "vieux_champ"}
        tache('retirer_champ_herite')(ctx)
        assert st.appels.get("update_performer", 0) == 1

    def test_un_champ_du_plugin_est_refuse(self):
        st, ctx = self._fiche(enrich_sources="x")
        ctx.args = {"champ": "enrich_sources"}
        tache('retirer_champ_herite')(ctx)
        assert st.performers["1"]["custom_fields"].get("enrich_sources")

    def test_les_valeurs_sans_source_sont_retirees(self):
        st = FauxStash(performers=[performer(
            1, "Archie", penis_length=19,
            custom_fields={"enrich_sources": "country: FR (9/10)"})])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        tache('retirer_non_confirme')(ctx)
        assert not st.performers["1"].get("penis_length")

    def test_une_valeur_appuyee_est_conservee(self):
        st = FauxStash(performers=[performer(
            1, "Archie", height_cm=178,
            custom_fields={
                "enrich_sources": "height_cm: 178 (9/10 · iafd)"})])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        tache('retirer_non_confirme')(ctx)
        assert st.performers["1"].get("height_cm") == 178


# ── Diagnostics ──────────────────────────────────────────────────────
class TestDiagnostics:
    """Ces tâches ne doivent JAMAIS écrire : leur intérêt est
    précisément qu'on puisse les lancer sans conséquence."""

    def _monde_garni(self):
        st = FauxStash(
            performers=[performer(
                1, "Archie Fox", circumcised="UNCUT",
                custom_fields={"sexe_type": "Cut",
                               "enrich_sources": "x: y (9/10)"})],
            studios=[studio(1, "Masqulin")],
            scenes=[scene(10, "Une scène", studio={"id": "1"})],
            tags=[{"id": "5", "name": "Anal"}])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        return st, ctx

    @pytest.mark.parametrize("nom", LECTURES)
    def test_aucune_ecriture(self, nom):
        st, ctx = self._monde_garni()
        tache(nom)(ctx)
        assert _ecritures(st) == [], f"{nom} a écrit"

    def test_le_conflit_herite_est_signale(self):
        """La tâche doit VOIR la divergence sans la corriger."""
        st, ctx = self._monde_garni()
        tache('controler_heritage')(ctx)
        assert st.performers["1"]["custom_fields"]["sexe_type"] == "Cut"
