# -*- coding: utf-8 -*-
"""
Fusion de doublons : la seule opération du plugin qui DÉTRUIT.

Une fusion supprime une fiche. Elle n'est pas restaurable — la
spécification le dit — et elle déplace des scènes. C'était pourtant le
module le moins couvert du plugin : zéro test sur 247 instructions.

Ce qui est vérifié ici tient en une phrase : rien ne doit se perdre, et
rien ne doit être détruit sans que les conditions soient réunies.
"""



import doublons
import noyau
from faux import FauxStash, faux_contexte, performer, scene, studio


PREFIX = "Gaizer"
CREE = f"{PREFIX}:créé"


def _cree(pid, nom, **champs):
    """Fiche portant le marqueur « créé par le plugin » : la seule
    qu'une fusion automatique a le droit d'absorber."""
    f = performer(pid, nom, **champs)
    f["tags"] = [{"id": "9", "name": CREE}]
    return f


# ── Fusion d'interprètes ─────────────────────────────────────────────
class TestFusionInterpretes:

    def _monde(self):
        st = FauxStash(
            performers=[performer(1, "Archie"),
                        _cree(2, "Archie 18969",
                              alias_list=["Archie A"], country="FR")],
            scenes=[scene(10, "Scène du doublon",
                          performers=[{"id": "2"}, {"id": "7"}]),
                    scene(11, "Scène étrangère",
                          performers=[{"id": "7"}])],
            tags=[{"id": "9", "name": CREE}])
        return st, faux_contexte({}, st)

    def test_le_doublon_est_supprime(self):
        st, ctx = self._monde()
        assert doublons._fusionner(ctx, st.performers["1"],
                                   st.performers["2"])
        assert "2" not in st.performers
        assert "1" in st.performers

    def test_les_scenes_sont_reportees(self):
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        ids = {q["id"] for q in st.scenes["10"]["performers"]}
        assert "1" in ids, "le canonique reprend la scène"
        assert "2" not in ids, "le doublon n'y figure plus"

    def test_les_autres_interpretes_de_la_scene_restent(self):
        """Une fusion ne doit pas déloger les partenaires."""
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        ids = {q["id"] for q in st.scenes["10"]["performers"]}
        assert "7" in ids

    def test_les_scenes_etrangeres_ne_bougent_pas(self):
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        assert [q["id"] for q in st.scenes["11"]["performers"]] == ["7"]

    def test_le_nom_du_doublon_devient_un_alias(self):
        """Sans cela, une recherche sur l'ancien nom ne trouverait
        plus rien."""
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        alias = st.performers["1"].get("alias_list") or []
        assert "Archie 18969" in alias

    def test_les_alias_du_doublon_sont_repris(self):
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        assert "Archie A" in (st.performers["1"].get("alias_list") or [])

    def test_les_champs_vides_du_canonique_sont_completes(self):
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        assert st.performers["1"].get("country") == "FR"

    def test_les_champs_remplis_ne_sont_pas_ecrases(self):
        st = FauxStash(
            performers=[performer(1, "Archie", country="BE"),
                        _cree(2, "Archie 18969", country="FR")],
            tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        assert st.performers["1"]["country"] == "BE"

    def test_la_fusion_est_tracee(self):
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        trace = (st.performers["1"].get("custom_fields") or {}) \
            .get("enrich_sources") or ""
        assert "Archie 18969" in trace

    def test_le_nom_n_est_pas_duplique_en_alias(self):
        """Fusionner deux fois le même nom ne doit pas empiler."""
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        alias = st.performers["1"].get("alias_list") or []
        assert len(alias) == len(set(alias))

    def test_ordre_des_ecritures(self):
        """Stash refuse un alias qui collide avec un nom existant : la
        suppression doit précéder la mise à jour."""
        st, ctx = self._monde()
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        ordre = [q for q, _d in st.journal
                 if q in ("performerDestroy", "update_performer")]
        assert ordre.index("performerDestroy") < \
            ordre.index("update_performer")


# ── Fusion de studios ────────────────────────────────────────────────
class TestFusionStudios:

    def _monde(self):
        st = FauxStash(
            studios=[studio(1, "Drill My Hole", scene_count=86),
                     studio(2, "Drillmyhole", url="https://d.example",
                            scene_count=0)],
            scenes=[scene(10, "S1", studio={"id": "2"}),
                    scene(11, "S2", studio={"id": "5"})])
        return st, faux_contexte({}, st)

    def test_le_doublon_est_detruit(self):
        st, ctx = self._monde()
        assert doublons._fusionner_studio(ctx, st.studios["1"],
                                          st.studios["2"])
        assert "2" not in st.studios

    def test_les_scenes_sont_reassignees(self):
        st, ctx = self._monde()
        doublons._fusionner_studio(ctx, st.studios["1"],
                                   st.studios["2"])
        assert st.scenes["10"]["studio"]["id"] == "1"
        assert st.scenes["11"]["studio"]["id"] == "5", \
            "les scènes d'un autre studio ne bougent pas"

    def test_le_nom_devient_un_alias(self):
        st, ctx = self._monde()
        doublons._fusionner_studio(ctx, st.studios["1"],
                                   st.studios["2"])
        assert "Drillmyhole" in (st.studios["1"].get("aliases") or "")

    def test_les_champs_vides_sont_repris(self):
        st, ctx = self._monde()
        doublons._fusionner_studio(ctx, st.studios["1"],
                                   st.studios["2"])
        assert st.studios["1"].get("url") == "https://d.example"

    def test_destruction_avant_mise_a_jour(self):
        st, ctx = self._monde()
        doublons._fusionner_studio(ctx, st.studios["1"],
                                   st.studios["2"])
        ordre = [q for q, _d in st.journal
                 if q in ("studioDestroy", "studioUpdate")]
        assert ordre.index("studioDestroy") < ordre.index("studioUpdate")


# ── Protections ──────────────────────────────────────────────────────
class TestProtections:
    """Le référentiel de l'utilisateur ne doit jamais être détruit
    automatiquement. C'est la garantie qui rend la détection
    utilisable sans surveillance."""

    def test_le_referentiel_n_est_pas_fusionne_automatiquement(self):
        """Deux fiches sans marqueur « créé » : la détection signale,
        elle ne fusionne pas."""
        st = FauxStash(performers=[performer(1, "Archie"),
                                   performer(2, "Archie 18969")])
        ctx = faux_contexte({"autoMergeDuplicates": True}, st)
        doublons.detect_duplicates(ctx)
        assert "1" in st.performers and "2" in st.performers

    def test_la_paire_exemptee_n_est_pas_signalee(self):
        st = FauxStash(performers=[
            performer(1, "Archie",
                      custom_fields={"enrich_pas_doublon": '["2"]'}),
            _cree(2, "Archie 18969")],
            tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)
        doublons.detect_duplicates(ctx)
        rap = (st.performers["1"].get("custom_fields") or {}) \
            .get("enrich_rapport") or ""
        assert "doublon" not in rap.lower()

    def test_simulation_ne_detruit_rien(self):
        st = FauxStash(
            performers=[performer(1, "Archie"), _cree(2, "Archie 18969")],
            tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        doublons._fusionner(ctx, st.performers["1"], st.performers["2"])
        assert "2" in st.performers

    def test_dedoublonnage_complet_respecte_le_seuil(self):
        """Sous le seuil fort, rien n'est fusionné — même entre fiches
        du référentiel, où la tâche a pourtant le droit d'agir."""
        st = FauxStash(performers=[performer(1, "Rogan Richards"),
                                   performer(2, "Rogan R")])
        ctx = faux_contexte({"strongMergeThreshold": "9.0"}, st)
        ctx.args = {}
        doublons.dedoublonnage_complet(ctx)
        assert "1" in st.performers and "2" in st.performers

    def test_dedoublonnage_complet_en_simulation(self):
        st = FauxStash(performers=[performer(1, "Tony D'Angelo"),
                                   performer(2, "Tony DAngelo")])
        ctx = faux_contexte({"dryRun": True,
                             "strongMergeThreshold": "9.0"}, st)
        ctx.args = {}
        noyau._activer_simulation(ctx)
        doublons.dedoublonnage_complet(ctx)
        assert len(st.performers) == 2


# ── Cas limites ──────────────────────────────────────────────────────
class TestCasLimites:

    def test_collection_vide(self):
        """Aucune FICHE ne doit bouger. La création des étiquettes de
        travail est tolérée : le plugin les prépare d'avance, ce qui
        ne coûte que deux entrées dans la liste des tags."""
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        doublons.detect_duplicates(ctx)
        doublons.detect_duplicates_studios(ctx)
        doublons.merge_marked(ctx)
        doublons.dedoublonnage_complet(ctx)
        touchees = [q for q, _d in st.journal
                    if q not in ("create_tag", "configuration")
                    and not q.startswith("find")]
        assert touchees == [], f"écritures inattendues : {touchees}"

    def test_fiche_unique(self):
        st = FauxStash(performers=[performer(1, "Archie")])
        ctx = faux_contexte({}, st)
        doublons.detect_duplicates(ctx)
        assert "1" in st.performers

    def test_doublon_sans_scene(self):
        st = FauxStash(performers=[performer(1, "Archie"),
                                   _cree(2, "Archie 18969")],
                       tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)
        assert doublons._fusionner(ctx, st.performers["1"],
                                   st.performers["2"])

    def test_echec_d_ecriture_ne_leve_pas(self):
        """Une fiche qui résiste ne doit pas interrompre le lot."""
        st = FauxStash(performers=[performer(1, "Archie"),
                                   _cree(2, "Archie 18969")],
                       tags=[{"id": "9", "name": CREE}])
        ctx = faux_contexte({}, st)

        def refuse(*a, **k):
            raise RuntimeError("refusé par le serveur")
        st.update_performer = refuse
        assert doublons._fusionner(ctx, st.performers["1"],
                                   st.performers["2"]) in (True, False)
