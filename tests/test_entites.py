# -*- coding: utf-8 -*-
"""
Création et restauration de fiches.

Deux opérations symétriques, toutes deux irréversibles à leur manière :
créer une entité laisse une trace dans la collection de l'utilisateur,
restaurer défait un travail. Le module n'avait aucun test.

Le point sensible est le MARQUEUR. Une fiche créée par le plugin porte
une étiquette qui l'autorise à être fusionnée ou supprimée
automatiquement ; le référentiel de l'utilisateur, lui, ne la porte
jamais. Perdre ce marqueur reviendrait à donner au plugin le droit de
détruire ce qu'il n'a pas créé.
"""

import json


import entites
import noyau
from faux import FauxStash, faux_contexte, performer, scene, studio


CREE = "Gaizer:créé"
PROPOSAL = "Gaizer:proposal"


# ── Création d'entités manquantes ────────────────────────────────────
class TestCreationInterprete:

    def test_la_fiche_est_creee(self):
        st = FauxStash(tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)
        idx = {}
        pid = entites._creer_performer_minimal(ctx, "Nouveau Venu", idx)
        assert pid
        assert any(p["name"] == "Nouveau Venu"
                   for p in st.performers.values())

    def test_le_marqueur_est_pose(self):
        """C'est lui qui autorise une fusion automatique plus tard :
        sans marqueur, la fiche serait traitée comme du référentiel.
        Le nom du tag dépend de la langue : le demander au contexte
        plutôt que de l'écrire en dur."""
        st = FauxStash()
        ctx = faux_contexte({}, st)
        attendu = ctx.tag_nom("created")
        pid = entites._creer_performer_minimal(ctx, "Nouveau Venu", {})
        fiche = st.performers[str(pid)]
        assert any(t["name"] == attendu
                   for t in fiche.get("tags") or [])

    def test_l_index_est_renseigne(self):
        """La fonction ne consulte PAS l'index avant de créer — c'est
        l'appelant qui dédoublonne les noms. Elle l'alimente en
        revanche, sous forme brute et normalisée, pour que la suite du
        passage retrouve la fiche."""
        st = FauxStash()
        ctx = faux_contexte({}, st)
        idx = {}
        pid = entites._creer_performer_minimal(ctx, "Nouveau Venu", idx)
        assert idx.get("nouveau venu") == pid
        assert idx.get("nouveauvenu") == pid

    def test_nom_vide_refuse(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        for nom in ("", "   ", None):
            assert not entites._creer_performer_minimal(ctx, nom, {})
        assert len(st.performers) == 0

    def test_simulation_ne_cree_rien(self):
        st = FauxStash(tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        entites._creer_performer_minimal(ctx, "Nouveau Venu", {})
        assert len(st.performers) == 0


class TestCreationStudio:

    def test_le_studio_est_cree_avec_son_marqueur(self):
        st = FauxStash(tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)
        sid = entites._creer_studio(ctx, {"name": "Studio Neuf"}, {})
        assert sid
        assert st.studios[str(sid)]["name"] == "Studio Neuf"

    def test_index_partage(self):
        st = FauxStash(tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)
        idx = {}
        a = entites._creer_studio(ctx, {"name": "Studio Neuf"}, idx)
        b = entites._creer_studio(ctx, {"name": "Studio Neuf"}, idx)
        assert a == b
        assert len(st.studios) == 1

    def test_studio_sans_nom(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        assert not entites._creer_studio(ctx, {}, {})
        assert len(st.studios) == 0

    def test_simulation(self):
        st = FauxStash(tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        entites._creer_studio(ctx, {"name": "Studio Neuf"}, {})
        assert len(st.studios) == 0


# ── Propositions ─────────────────────────────────────────────────────
class TestPropositions:
    """Une proposition n'écrit pas la valeur : elle la range dans un
    champ à part, en attendant un arbitrage."""

    def test_la_valeur_n_est_pas_appliquee(self):
        st = FauxStash(performers=[performer(1, "Archie")],
                       tags=[{"id": "8", "name": PROPOSAL}])
        ctx = faux_contexte({}, st)
        entites.poser_proposition(ctx, st.performers["1"], "country",
                                  "FR", "iafd", 9.0, True)
        assert not st.performers["1"].get("country")

    def test_la_proposition_est_conservee(self):
        """La valeur proposée vit dans un TAG, pas dans un champ : elle
        reste ainsi visible et filtrable dans Stash sans occuper le
        champ qu'elle prétend remplir."""
        st = FauxStash(performers=[performer(1, "Archie")],
                       tags=[{"id": "8", "name": PROPOSAL}])
        ctx = faux_contexte({}, st)
        entites.poser_proposition(ctx, st.performers["1"], "country",
                                  "FR", "iafd", 9.0, True)
        crees = [str(d) for q, d in st.journal if q == "create_tag"]
        assert any("country=FR" in n for n in crees)
        assert any("★" in n for n in crees), \
            "la recommandation doit être distinguée"

    def test_le_tag_de_proposition_est_pose(self):
        st = FauxStash(performers=[performer(1, "Archie")],
                       tags=[{"id": "8", "name": PROPOSAL}])
        ctx = faux_contexte({}, st)
        entites.poser_proposition(ctx, st.performers["1"], "country",
                                  "FR", "iafd", 9.0, True)
        noms = {t["name"] for t in st.performers["1"].get("tags") or []}
        assert PROPOSAL in noms

    def test_simulation(self):
        st = FauxStash(performers=[performer(1, "Archie")],
                       tags=[{"id": "8", "name": PROPOSAL}])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        entites.poser_proposition(ctx, st.performers["1"], "country",
                                  "FR", "iafd", 9.0, True)
        assert not (st.performers["1"].get("custom_fields") or {})


# ── Restauration ─────────────────────────────────────────────────────
class TestRestauration:
    """« Annuler le dernier passage » doit rendre la fiche telle
    qu'elle était. C'est la contrepartie du droit d'écrire sans
    demander : sans restauration fiable, le mode automatique serait
    imprudent."""

    def _fiche_enrichie(self):
        hist = [{"d": "2026-08-01",
                 "champs": {"country": ["", "FR"],
                            "height_cm": ["", "180"]}}]
        return performer(
            1, "Archie", country="FR", height_cm=180,
            custom_fields={"enrich_historique": json.dumps(hist),
                           "enrich_sources": "country: FR (9/10)"})

    def test_les_champs_reviennent_a_leur_etat_anterieur(self):
        st = FauxStash(performers=[self._fiche_enrichie()])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.performers["1"], False, False)
        assert not st.performers["1"].get("country")
        assert not st.performers["1"].get("height_cm")

    def test_un_champ_absent_de_l_historique_est_conserve(self):
        """La restauration défait ce que le plugin a fait, pas ce que
        l'utilisateur a saisi entre-temps."""
        f = self._fiche_enrichie()
        f["ethnicity"] = "Latin"
        st = FauxStash(performers=[f])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.performers["1"], False, False)
        assert st.performers["1"].get("ethnicity") == "Latin"

    def test_le_passage_est_retire_de_l_historique(self):
        """Relancer doit remonter d'un cran, pas répéter le même."""
        st = FauxStash(performers=[self._fiche_enrichie()])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.performers["1"], False, False)
        cf = st.performers["1"].get("custom_fields") or {}
        hist = json.loads(cf.get("enrich_historique") or "[]")
        assert hist == []

    def test_sans_historique_rien_ne_se_passe(self):
        st = FauxStash(performers=[performer(1, "Archie",
                                             country="FR")])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.performers["1"], False, False)
        assert st.performers["1"]["country"] == "FR"

    def test_historique_illisible_ne_leve_pas(self):
        st = FauxStash(performers=[performer(
            1, "Archie",
            custom_fields={"enrich_historique": "{ceci n'est pas"})])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.performers["1"], False, False)

    def test_simulation_ne_restaure_pas(self):
        st = FauxStash(performers=[self._fiche_enrichie()])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        entites._restaurer_entite(ctx, st.performers["1"], False, False)
        assert st.performers["1"]["country"] == "FR"

    def test_restauration_de_scene(self):
        hist = [{"d": "2026-08-01", "champs": {"date": ["", "2023-01-01"]}}]
        st = FauxStash(scenes=[scene(
            10, "Une scène", date="2023-01-01",
            custom_fields={"enrich_historique": json.dumps(hist)})])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.scenes["10"], True, False)
        assert not st.scenes["10"].get("date")

    def test_restauration_de_studio(self):
        hist = [{"d": "2026-08-01", "champs": {"url": ["", "https://x"]}}]
        st = FauxStash(studios=[studio(
            1, "Un studio", url="https://x",
            custom_fields={"enrich_historique": json.dumps(hist)})])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, st.studios["1"], False, True)
        assert not st.studios["1"].get("url")
