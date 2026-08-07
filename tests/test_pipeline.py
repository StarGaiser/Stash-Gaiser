# -*- coding: utf-8 -*-
"""
Pipeline d'enrichissement : ce qui est écrit, et ce qui ne l'est pas.

Le contrat du plugin tient en une phrase : il remplit ce qui manque et
ne touche pas à ce qui existe. Tout le reste — modes, seuils,
propositions, arbitrage — n'est que la déclinaison de cette règle.

Ces modules écrivent sur la collection de l'utilisateur et étaient
couverts à 0 et 8 %.
"""

import json

import noyau
import performers
import studios
from faux import FauxStash, faux_contexte, performer, scene, studio


# ── Studios ──────────────────────────────────────────────────────────
class TestEnrichissementStudio:

    def _monde(self, **champs):
        st = FauxStash(studios=[studio(1, "Falcon Studios", **champs)],
                       scenes=[scene(10, "S1", studio={"id": "1"})])
        return st, faux_contexte({}, st)

    def test_ne_leve_pas_sur_studio_sans_source(self, monkeypatch):
        st, ctx = self._monde()
        monkeypatch.setattr(studios, "collecter_studio",
                            lambda *a, **k: {})
        studios._enrichir_studio(ctx, st.studios["1"])

    def test_un_champ_vide_est_propose(self, monkeypatch):
        st, ctx = self._monde()
        monkeypatch.setattr(
            studios, "collecter_studio",
            lambda *a, **k: {"stashdb.org": {"website": "https://f.example"}})
        studios._enrichir_studio(ctx, st.studios["1"])
        touchees = [q for q, _d in st.journal if q == "studioUpdate"]
        assert touchees, "le studio aurait dû être mis à jour"

    def test_un_champ_rempli_n_est_pas_ecrase(self, monkeypatch):
        """La règle cardinale : ce que l'utilisateur a saisi prime."""
        st, ctx = self._monde(url="https://a-moi.example")
        monkeypatch.setattr(
            studios, "collecter_studio",
            lambda *a, **k: {"stashdb.org": {"website": "https://f.example"}})
        studios._enrichir_studio(ctx, st.studios["1"])
        assert st.studios["1"]["url"] == "https://a-moi.example"

    def test_simulation_n_ecrit_pas(self, monkeypatch):
        st, ctx = self._monde()
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        monkeypatch.setattr(
            studios, "collecter_studio",
            lambda *a, **k: {"stashdb.org": {"website": "https://f.example"}})
        studios._enrichir_studio(ctx, st.studios["1"])
        assert not st.studios["1"].get("url")

    def test_collection_vide(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        studios.enrich_studios(ctx)
        studios.apply_accepted_studios(ctx)
        assert st.mutations() == 0

    def test_identifiant_inexistant(self):
        st = FauxStash(studios=[studio(1, "Falcon Studios")])
        ctx = faux_contexte({}, st)
        ctx.args = {"studio_id": "999999"}
        studios.enrich_one_studio(ctx)
        assert st.mutations() == 0

    def test_identifiant_absent(self):
        st = FauxStash(studios=[studio(1, "Falcon Studios")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        studios.enrich_one_studio(ctx)


class TestApplicationStudio:

    def test_sans_marqueur_rien_n_est_applique(self):
        """La validation est explicite : une fiche non marquée ne doit
        pas être touchée par une application de masse."""
        st = FauxStash(studios=[studio(1, "Falcon Studios")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        studios.apply_accepted_studios(ctx)
        assert st.mutations() == 0

    def test_le_marqueur_est_consomme(self):
        """Sans cela, la fiche serait réappliquée à chaque passage."""
        st = FauxStash(studios=[studio(
            1, "Falcon Studios",
            custom_fields={"enrich_accept": "1"})])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        studios.apply_accepted_studios(ctx)
        cf = st.studios["1"].get("custom_fields") or {}
        assert not cf.get("enrich_accept")


# ── Interprètes ──────────────────────────────────────────────────────
class TestEnrichissementInterprete:

    def _monde(self, reglages=None, **champs):
        st = FauxStash(performers=[performer(1, "Archie Fox", **champs)])
        base = {"useAppoint": False, "generateBioHot": False}
        base.update(reglages or {})
        ctx = faux_contexte(base, st)
        ctx.args = {}
        return st, ctx

    def _sources(self, monkeypatch, donnees):
        """Un test ne doit RIEN appeler dehors : ni les stash-boxes,
        ni les sources d'appoint, ni le modèle de langage. Sans cette
        coupure, la suite passait de cinq secondes à une minute et son
        résultat dépendait de l'état du réseau."""
        monkeypatch.setattr(performers, "collecter_stash",
                            lambda *a, **k: (donnees, []))
        monkeypatch.setattr(performers, "passe_url",
                            lambda *a, **k: None)
        monkeypatch.setattr(performers, "synth_bio",
                            lambda *a, **k: None)
        monkeypatch.setattr(performers, "generer_bio_hot",
                            lambda *a, **k: None)
        monkeypatch.setattr(performers.sources, "ACTOR_SOURCES", {})

    def test_aucune_source_ne_leve_pas(self, monkeypatch):
        st, ctx = self._monde()
        self._sources(monkeypatch, {})
        performers._enrichir_un(ctx, st.performers["1"])

    def test_mode_auto_applique_la_meilleure_valeur(self, monkeypatch):
        st, ctx = self._monde({"applyMode": "auto"})
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert st.performers["1"].get("country") == "FR"

    def test_mode_auto_n_ecrase_pas(self, monkeypatch):
        st, ctx = self._monde({"applyMode": "auto"}, country="BE")
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert st.performers["1"]["country"] == "BE"

    def test_le_desaccord_est_reporte(self, monkeypatch):
        """Un champ rempli que les sources contredisent doit laisser
        une trace : c'est ce qui rend l'arbitrage possible plus tard."""
        st, ctx = self._monde({"applyMode": "auto"}, height_cm=183)
        self._sources(monkeypatch, {
            "iafd": {"height_cm": "178"}, "gevi": {"height_cm": "178"},
            "stashdb.org": {"height_cm": "178"}})
        performers._enrichir_un(ctx, st.performers["1"])
        rap = (st.performers["1"].get("custom_fields") or {}) \
            .get("enrich_rapport") or ""
        # Le libellé dépend de la langue : c'est le CONTENU qui compte.
        assert "height_cm" in rap
        assert "183" in rap and "178" in rap

    def test_mode_manuel_ne_touche_pas_les_champs(self, monkeypatch):
        """En mode manuel, tout passe par des propositions."""
        st, ctx = self._monde({"applyMode": "manual"})
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert not st.performers["1"].get("country")

    def test_mode_seuil_refuse_sous_la_barre(self, monkeypatch):
        """Une source unique et faible ne suffit pas à écrire."""
        st, ctx = self._monde({"applyMode": "seuil",
                               "autoAcceptThreshold": "9.5"})
        self._sources(monkeypatch, {"men": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert not st.performers["1"].get("country")

    def test_mode_seuil_propose_sans_appliquer(self, monkeypatch):
        """En mode seuil, l'enrichissement PROPOSE ; c'est une tâche de
        masse séparée qui applique ce qui dépasse la barre. Le mode
        laisse ainsi la main entre la collecte et l'écriture."""
        st, ctx = self._monde({"applyMode": "seuil",
                               "autoAcceptThreshold": "7.0"})
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"},
            "stashdb.org": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert not st.performers["1"].get("country")
        noms = {t["name"] for t in st.performers["1"].get("tags") or []}
        assert any("proposal" in n for n in noms)

    def test_l_historique_est_alimente(self, monkeypatch):
        """Sans historique, « Annuler le dernier passage » ne pourrait
        rien défaire."""
        st, ctx = self._monde({"applyMode": "auto"})
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        cf = st.performers["1"].get("custom_fields") or {}
        hist = json.loads(cf.get("enrich_historique") or "[]")
        assert hist and "country" in (hist[-1].get("champs") or {})

    def test_la_provenance_est_tracee(self, monkeypatch):
        st, ctx = self._monde({"applyMode": "auto"})
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        src = (st.performers["1"].get("custom_fields") or {}) \
            .get("enrich_sources") or ""
        assert "country" in src and "iafd" in src

    def test_simulation_n_ecrit_pas(self, monkeypatch):
        st, ctx = self._monde({"applyMode": "auto", "dryRun": True})
        noyau._activer_simulation(ctx)
        self._sources(monkeypatch, {
            "iafd": {"country": "FR"}, "gevi": {"country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert not st.performers["1"].get("country")

    def test_valeurs_aberrantes_ignorees(self, monkeypatch):
        """Une date nulle interrompait autrefois toute la fiche."""
        st, ctx = self._monde({"applyMode": "auto"})
        self._sources(monkeypatch, {
            "iafd": {"birthdate": "0000-00-00", "country": "FR"},
            "gevi": {"birthdate": "", "country": "FR"}})
        performers._enrichir_un(ctx, st.performers["1"])
        assert st.performers["1"].get("country") == "FR", \
            "le reste de la fiche doit être traité malgré une valeur " \
            "illisible"


class TestTachesInterpretes:

    def test_collection_vide(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        performers.enrich_performers(ctx)
        performers.apply_accepted(ctx)
        performers.regenerate_biohot(ctx)
        touchees = [q for q, _d in st.journal
                    if q not in ("create_tag", "configuration")
                    and not q.startswith(("find", "list_"))]
        assert touchees == [], f"écritures inattendues : {touchees}"

    def test_identifiant_inexistant(self):
        st = FauxStash(performers=[performer(1, "Archie Fox")])
        ctx = faux_contexte({}, st)
        ctx.args = {"performer_id": "999999"}
        performers.enrich_one_performer(ctx)
        assert st.mutations() == 0

    def test_application_sans_proposition(self):
        st = FauxStash(performers=[performer(1, "Archie Fox")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        performers.apply_accepted(ctx)
        touchees = [q for q, _d in st.journal
                    if q not in ("create_tag", "configuration")
                    and not q.startswith(("find", "list_"))]
        assert touchees == []
