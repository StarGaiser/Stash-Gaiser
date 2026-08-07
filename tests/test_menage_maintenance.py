# -*- coding: utf-8 -*-
"""
Ménage et maintenance : ce qu'on retire, et ce qu'on répare.

Deux familles peu couvertes, et pour de mauvaises raisons — elles
paraissent anodines. Elles ne le sont pas : le ménage DÉTACHE des
étiquettes et RETIRE du texte, la maintenance réécrit des réglages et
peut basculer toute une installation d'une langue à l'autre.

Ce qui est éprouvé ici tient en deux exigences. Une tâche de ménage ne
doit retirer que ce qu'elle vise — retirer plus est irréversible. Une
tâche de maintenance ne doit jamais laisser l'installation dans un état
intermédiaire : soit elle aboutit, soit elle ne touche à rien.
"""

import json

import pytest

import noyau
import taches_maintenance
import taches_menage
from faux import FauxStash, faux_contexte, performer, scene


@pytest.fixture(autouse=True)
def etat_isole(tmp_path, monkeypatch):
    """Ces tâches écrivent dans le fichier d'état : sans isolation,
    elles corrompraient l'installation de qui lance les tests."""
    monkeypatch.setattr(noyau, "ETAT_FICHIER", tmp_path / "etat.json")


def _ecritures(st):
    return [q for q, _d in st.journal
            if q not in ("create_tag", "configuration")
            and not q.startswith(("find", "list_"))]


# ── Retrait de tags ──────────────────────────────────────────────────
class TestPurgeDesTagsExclus:
    """Détacher un tag d'une scène ne se défait pas : le tag exclu
    disparaît de la scène et rien ne dit qu'il y était."""

    def _monde(self, exclus=""):
        st = FauxStash(
            scenes=[scene(10, "Une scène",
                          tags=[{"id": "1", "name": "Anal Sex"},
                                {"id": "2", "name": "1080p"},
                                {"id": "3", "name": "Bareback"}])],
            tags=[{"id": "1", "name": "Anal Sex"},
                  {"id": "2", "name": "1080p"},
                  {"id": "3", "name": "Bareback"}])
        ctx = faux_contexte({"tagsExclude": exclus}, st)
        ctx.args = {}
        return st, ctx

    def test_sans_liste_rien_n_est_retire(self):
        """Un réglage vide ne doit pas être lu comme « tout retirer »."""
        st, ctx = self._monde()
        taches_menage.purger_tags_exclus(ctx)
        assert len(st.scenes["10"]["tags"]) == 3

    def test_seul_le_tag_vise_part(self):
        st, ctx = self._monde("1080p")
        taches_menage.purger_tags_exclus(ctx)
        restants = {t["name"] for t in st.scenes["10"]["tags"]}
        assert restants == {"Anal Sex", "Bareback"}

    def test_plusieurs_tags_vises(self):
        st, ctx = self._monde("1080p, Bareback")
        taches_menage.purger_tags_exclus(ctx)
        restants = {t["name"] for t in st.scenes["10"]["tags"]}
        assert restants == {"Anal Sex"}

    def test_un_tag_absent_ne_provoque_rien(self):
        st, ctx = self._monde("N'existe Pas")
        taches_menage.purger_tags_exclus(ctx)
        assert len(st.scenes["10"]["tags"]) == 3
        assert _ecritures(st) == []

    def test_simulation(self):
        st, ctx = self._monde("1080p")
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        taches_menage.purger_tags_exclus(ctx)
        assert len(st.scenes["10"]["tags"]) == 3


class TestRetraitDesPropositions:
    """Les propositions sont des tags de travail. Les retirer ne doit
    jamais emporter les tags de l'utilisateur, qui vivent dans le même
    espace de noms."""

    def _monde(self):
        st = FauxStash(
            performers=[performer(1, "Archie", tags=[
                {"id": "1", "name": "Gaizer:proposal"},
                {"id": "2", "name": "Gaizer:country=FR"},
                {"id": "3", "name": "Mon Tag À Moi"},
                {"id": "4", "name": "Gaizer:créé"}])],
            tags=[{"id": "1", "name": "Gaizer:proposal"},
                  {"id": "2", "name": "Gaizer:country=FR"},
                  {"id": "3", "name": "Mon Tag À Moi"},
                  {"id": "4", "name": "Gaizer:créé"}])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        return st, ctx

    def test_les_tags_de_l_utilisateur_survivent(self):
        st, ctx = self._monde()
        taches_menage.clear_proposals(ctx)
        noms = {t["name"] for t in st.performers["1"]["tags"]}
        assert "Mon Tag À Moi" in noms

    def test_le_marqueur_de_creation_survit(self):
        """C'est lui qui autorise une fusion automatique : le perdre
        ferait traiter la fiche comme préexistante."""
        st, ctx = self._monde()
        taches_menage.clear_proposals(ctx)
        noms = {t["name"] for t in st.performers["1"]["tags"]}
        assert "Gaizer:créé" in noms

    def test_simulation(self):
        st, ctx = self._monde()
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        avant = len(st.performers["1"]["tags"])
        taches_menage.clear_proposals(ctx)
        assert len(st.performers["1"]["tags"]) == avant


class TestSuggestionDeTagsExclus:
    """Cette tâche ne fait que proposer. Elle ne doit rien écrire —
    c'est ce qui permet de la lancer sans y penser."""

    def test_aucune_ecriture(self):
        st = FauxStash(
            scenes=[scene(10, "S1", tags=[{"id": "1", "name": "Anal"}]),
                    scene(11, "S2", tags=[{"id": "1", "name": "Anal"}])],
            tags=[{"id": "1", "name": "Anal"}])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_menage.suggerer_tags_exclus(ctx)
        assert _ecritures(st) == []

    def test_collection_sans_tag_ne_leve_pas(self):
        st = FauxStash(scenes=[scene(10, "S1")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_menage.suggerer_tags_exclus(ctx)


class TestRetraitDuPiedDeBio:

    def _fiche(self, details):
        st = FauxStash(performers=[performer(1, "Archie",
                                             details=details)])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        return st, ctx

    def test_le_texte_qui_precede_est_conserve(self):
        """Le pied est retiré, la biographie reste."""
        st, ctx = self._fiche(
            "Une biographie factuelle.\n\n"
            "― Fiabilité des données (Gaizer) ―\nnote 9/10")
        taches_menage.retirer_pied_bio(ctx)
        assert st.performers["1"]["details"] == \
            "Une biographie factuelle."

    def test_une_biographie_reduite_au_pied_devient_vide(self):
        """Sans texte devant, il ne reste rien — et c'est exact : le
        pied n'était pas une biographie."""
        st, ctx = self._fiche(
            "― Fiabilité des données (Gaizer) ―\nnote 9/10")
        taches_menage.retirer_pied_bio(ctx)
        assert not (st.performers["1"]["details"] or "").strip()

    def test_une_biographie_sans_pied_est_intacte(self):
        st, ctx = self._fiche("Une biographie simple.")
        taches_menage.retirer_pied_bio(ctx)
        assert st.performers["1"]["details"] == "Une biographie simple."
        assert _ecritures(st) == []

    def test_fiche_sans_biographie(self):
        st, ctx = self._fiche("")
        taches_menage.retirer_pied_bio(ctx)
        assert _ecritures(st) == []

    def test_simulation(self):
        st, ctx = self._fiche("Bio.\n\n― Fiabilité des données "
                              "(Gaizer) ―\nnote")
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        taches_menage.retirer_pied_bio(ctx)
        assert "Fiabilité" in st.performers["1"]["details"]


# ── Maintenance ──────────────────────────────────────────────────────
class TestRestaurationDesReglages:
    """Un réglage perdu se reconfigure ; un réglage ÉCRASÉ par une
    restauration hâtive se perd deux fois."""

    def test_sans_sauvegarde_rien_n_est_ecrit(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_maintenance.restaurer_reglages(ctx)
        assert _ecritures(st) == []

    def test_les_secrets_ne_sont_pas_restaures(self):
        """L'état ne les contient pas — ils y sont filtrés à
        l'écriture. Une restauration ne doit donc pas écrire une
        valeur factice par-dessus une clé valide."""
        noyau.etat_ecrire({"reglages": {"language": "fr"},
                           "reglages_secrets": ["mistralApiKey"]})
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_maintenance.restaurer_reglages(ctx)
        ecrits = [d for q, d in st.journal if q == "configurePlugin"]
        for d in ecrits:
            assert "mistralApiKey" not in json.dumps(d or {})

    def test_simulation_n_ecrit_pas(self):
        noyau.etat_ecrire({"reglages": {"language": "fr"}})
        st = FauxStash()
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        ctx.args = {}
        taches_maintenance.restaurer_reglages(ctx)
        assert not [q for q, _d in st.journal
                    if q == "configurePlugin"]


class TestReprisIA:
    """La pause protège d'un fournisseur qui refuse. La lever trop tôt
    fait repartir une rafale qui sera refusée de nouveau."""

    def test_sans_pause_ne_leve_pas(self):
        st = FauxStash()
        ctx = faux_contexte({"generateBioHot": False}, st)
        ctx.args = {}
        taches_maintenance.reprendre_ia(ctx)

    def test_une_pause_echue_est_levee(self):
        """La clé d'état s'appelle `pause_llm_jusqu` : la pause porte
        sur le modèle de langage, pas sur une notion vague d'« IA »."""
        noyau.etat_ecrire({"pause_llm_jusqu": "2020-01-01",
                           "pause_motif": "essai"})
        st = FauxStash()
        ctx = faux_contexte({"generateBioHot": False}, st)
        ctx.args = {}
        taches_maintenance.reprendre_ia(ctx)
        assert not noyau.etat_lire().get("pause_llm_jusqu")

    def test_une_pause_en_cours_est_maintenue(self):
        noyau.etat_ecrire({"pause_llm_jusqu": "2099-01-01",
                           "pause_motif": "essai"})
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_maintenance.reprendre_ia(ctx)
        assert noyau.etat_lire().get("pause_llm_jusqu") \
            == "2099-01-01"

    def test_une_pause_peut_etre_forcee(self):
        """L'argument s'appelle `forcer`, à l'impératif comme les
        autres arguments du plugin."""
        noyau.etat_ecrire({"pause_llm_jusqu": "2099-01-01",
                           "pause_motif": "essai"})
        st = FauxStash()
        ctx = faux_contexte({"generateBioHot": False}, st)
        ctx.args = {"forcer": "1"}
        taches_maintenance.reprendre_ia(ctx)
        assert not noyau.etat_lire().get("pause_llm_jusqu")


class TestBasculeDeLangue:
    """Basculer une installation d'une langue à l'autre renomme des
    étiquettes employées par des fiches. Un renommage partiel laisse
    la collection dans deux langues."""

    def test_sans_changement_ne_leve_pas(self):
        st = FauxStash()
        ctx = faux_contexte({"language": "fr"}, st)
        ctx.args = {}
        taches_maintenance.migrer_langue(ctx)

    def test_simulation(self):
        st = FauxStash(
            performers=[performer(1, "Archie", tags=[
                {"id": "1", "name": "Gaizer:créé"}])],
            tags=[{"id": "1", "name": "Gaizer:créé"}])
        ctx = faux_contexte({"language": "en", "dryRun": True}, st)
        noyau._activer_simulation(ctx)
        ctx.args = {}
        taches_maintenance.migrer_langue(ctx)
        assert st.tags["1"]["name"] == "Gaizer:créé"

    def test_langue_inconnue_ne_leve_pas(self):
        st = FauxStash()
        ctx = faux_contexte({"language": "klingon"}, st)
        ctx.args = {}
        taches_maintenance.migrer_langue(ctx)


class TestPointDEntreeTechnique:

    def test_noop_ne_fait_rien(self):
        """Son nom stable sert aux boutons de l'interface, qui passent
        le vrai mode en argument."""
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_maintenance.noop(ctx)
        assert _ecritures(st) == []
