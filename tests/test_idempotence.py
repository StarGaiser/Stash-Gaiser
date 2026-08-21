# -*- coding: utf-8 -*-
"""
Promesses tenues : relancer ne double rien, restaurer annule un passage,
une tâche ne dépasse pas son lot ni son budget de requêtes.

La spécification fonctionnelle affirme « une exécution annule un
passage » et « rien n'est écrasé ». Ces phrases n'étaient vérifiées par
rien. Elles le sont ici, sur un faux serveur qui applique les écritures
comme le vrai et compte chaque appel.

Le comptage plutôt que le chronométrage : une durée dépend de la
machine et rend le test instable, un nombre d'appels est déterministe.
Et c'est bien le nombre d'allers-retours qui a coûté cher ici — 400
poses de tag valaient 400 requêtes avant la mise en cache.
"""

import json

import pytest

import entites
import groupes
import noyau
from faux import FauxStash, faux_contexte, performer, scene


# ── Relancer ne double rien ──────────────────────────────────────────
class TestIdempotence:

    def test_lien_de_groupe_non_duplique(self):
        """Une scène déjà rattachée voyait son lien empilé à chaque
        passage. Le cas se produit dès qu'une partie isolée vient
        compléter un groupe existant."""
        st = FauxStash(
            scenes=[scene(1, "Serie Part 1", groups=[
                {"group": {"id": "50", "name": "Serie"},
                 "scene_index": 1}])],
            groups=[{"id": "50", "name": "Serie", "aliases": "",
                     "scene_count": 1}])
        ctx = faux_contexte({"applyMode": "auto"}, st)
        for _ in range(3):
            serie = {"nom": "Serie", "parties": [(1, st.scenes["1"])],
                     "studios": set(), "dates": [], "genre": "partie",
                     "bonus": 0.5, "depuis_titre": True}
            groupes._appliquer_serie(ctx, serie, 9.0, "essai")
        assert len(st.scenes["1"]["groups"]) == 1

    def test_rattachement_a_un_autre_groupe_conserve(self):
        """Dédupliquer ne doit pas effacer les autres rattachements."""
        st = FauxStash(
            scenes=[scene(1, "Serie Part 1", groups=[
                {"group": {"id": "99", "name": "Autre"},
                 "scene_index": 3}])],
            groups=[{"id": "50", "name": "Serie", "aliases": "",
                     "scene_count": 0},
                    {"id": "99", "name": "Autre", "aliases": "",
                     "scene_count": 1}])
        ctx = faux_contexte({"applyMode": "auto"}, st)
        serie = {"nom": "Serie", "parties": [(1, st.scenes["1"])],
                 "studios": set(), "dates": [], "genre": "partie",
                 "bonus": 0.5, "depuis_titre": True}
        groupes._appliquer_serie(ctx, serie, 9.0, "essai")
        ids = {g["group"]["id"] for g in st.scenes["1"]["groups"]}
        assert ids == {"50", "99"}

    def test_tag_pose_deux_fois_reste_unique(self):
        st = FauxStash(tags=[{"id": "7", "name": "Gaizer:créé"}])
        ctx = faux_contexte({}, st)
        assert noyau.tag_id(ctx, "Gaizer:créé") \
            == noyau.tag_id(ctx, "Gaizer:créé") == "7"

    def test_historique_ne_grossit_pas_sans_fin(self):
        fiche = {}
        for i in range(30):
            h = noyau._historique_maj(fiche, {"details": ["", f"v{i}"]})
            fiche = {"custom_fields": {"enrich_historique": h}}
        assert len(json.loads(h)) == 10


# ── Restaurer annule un passage ──────────────────────────────────────
class TestRestauration:
    """« Une exécution annule un passage ; relancer remonte d'un
    cran. » — spécification fonctionnelle, §5.2."""

    def _fiche_enrichie(self):
        """Un interprète vide, puis enrichi une fois."""
        p = performer(1, "Dato Foland")
        hist = noyau._historique_maj(
            p, {"country": ["", "RU"],
                "birthdate": ["", "1984-10-21"]},
            tags_aj=["7"])
        p["country"] = "RU"
        p["birthdate"] = "1984-10-21"
        p["tags"] = [{"id": "7", "name": "Gaizer:créé"}]
        p["custom_fields"] = {"enrich_historique": hist}
        return p

    def test_champs_remis_a_leur_valeur_d_avant(self):
        p = self._fiche_enrichie()
        st = FauxStash(performers=[p],
                       tags=[{"id": "7", "name": "Gaizer:créé"}])
        ctx = faux_contexte({}, st)
        assert entites._restaurer_entite(ctx, p, est_scene=False)
        remis = st.performers["1"]
        assert not (remis.get("country") or "")
        assert not (remis.get("birthdate") or "")

    def test_tags_ajoutes_retires(self):
        p = self._fiche_enrichie()
        st = FauxStash(performers=[p],
                       tags=[{"id": "7", "name": "Gaizer:créé"}])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, p, est_scene=False)
        restants = {t["id"] for t in st.performers["1"].get("tags", [])}
        assert "7" not in restants

    def test_deux_passages_deux_restaurations(self):
        """Chaque exécution remonte d'un cran, pas davantage."""
        p = performer(1, "X")
        h1 = noyau._historique_maj(p, {"country": ["", "FR"]})
        p["custom_fields"] = {"enrich_historique": h1}
        p["country"] = "FR"
        h2 = noyau._historique_maj(p, {"country": ["FR", "BE"]})
        p["custom_fields"] = {"enrich_historique": h2}
        p["country"] = "BE"

        st = FauxStash(performers=[p])
        ctx = faux_contexte({}, st)
        entites._restaurer_entite(ctx, p, est_scene=False)
        assert st.performers["1"]["country"] == "FR", \
            "le premier retour rend la valeur précédente"

        courant = st.performers["1"]
        entites._restaurer_entite(ctx, courant, est_scene=False)
        assert not (st.performers["1"].get("country") or "")

    def test_sans_historique_rien_ne_se_passe(self):
        p = performer(1, "X", country="FR")
        st = FauxStash(performers=[p])
        ctx = faux_contexte({}, st)
        assert entites._restaurer_entite(ctx, p, est_scene=False) \
            is False
        assert st.performers["1"]["country"] == "FR"

    def test_historique_corrompu_ne_leve_pas(self):
        p = performer(1, "X",
                      custom_fields={"enrich_historique": "pas du json"})
        st = FauxStash(performers=[p])
        ctx = faux_contexte({}, st)
        assert entites._restaurer_entite(ctx, p, est_scene=False) \
            is False

    def test_restauration_d_une_scene(self):
        s = scene(1, "Titre")
        hist = noyau._historique_maj(s, {"date": ["", "2020-01-01"]})
        s["date"] = "2020-01-01"
        s["custom_fields"] = {"enrich_historique": hist}
        st = FauxStash(scenes=[s])
        ctx = faux_contexte({}, st)
        assert entites._restaurer_entite(ctx, s, est_scene=True)
        assert not (st.scenes["1"].get("date") or "")


# ── Budgets de requêtes ──────────────────────────────────────────────
class TestBudgetDeRequetes:
    """Ce qui a coûté cher n'était pas la lenteur d'un calcul mais le
    nombre d'allers-retours."""

    def test_un_seul_appel_par_nom_de_tag(self):
        st = FauxStash(tags=[{"id": "7", "name": "Gaizer:créé"},
                             {"id": "8", "name": "Gaizer:accept"}])
        ctx = faux_contexte({}, st)
        for _ in range(100):
            noyau.tag_id(ctx, "Gaizer:créé")
            noyau.tag_id(ctx, "Gaizer:accept")
        assert st.appels["find_tags"] <= 2, \
            f"{st.appels['find_tags']} requêtes pour 2 noms distincts"

    def test_creation_de_tag_une_seule_fois(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        for _ in range(50):
            noyau.tag_id(ctx, "Gaizer:nouveau")
        assert st.appels["create_tag"] == 1

    def test_groupes_charges_une_seule_fois(self):
        st = FauxStash(groups=[{"id": str(i), "name": f"Film {i}",
                                "aliases": ""} for i in range(30)])
        ctx = faux_contexte({}, st)
        for i in range(30):
            groupes._groupe_existant(ctx, f"Film {i}")
        assert st.appels["findGroups"] == 1, \
            "l'index doit être mis en cache pour la durée de la tâche"

    def test_le_cache_est_bien_par_execution(self):
        """Deux contextes distincts ne partagent rien : un cache global
        laisserait des données périmées d'une tâche à l'autre."""
        st = FauxStash(groups=[{"id": "1", "name": "Film", "aliases": ""}])
        groupes._groupe_existant(faux_contexte({}, st), "Film")
        groupes._groupe_existant(faux_contexte({}, st), "Film")
        assert st.appels["findGroups"] == 2


# ── Mode simulation ──────────────────────────────────────────────────
class TestSimulation:
    """Le filet de sécurité. Un trou dedans est pire qu'aucun filet :
    il inspire confiance. Vingt groupes ont été créés lors d'un essai
    « à blanc » parce que groupCreate manquait au filtre."""

    def _ctx_simule(self, **fiches):
        st = FauxStash(**fiches)
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        return ctx, st

    def test_aucune_creation_de_groupe(self):
        ctx, st = self._ctx_simule(
            scenes=[scene(1, "Serie Part 1")])
        serie = {"nom": "Serie", "parties": [(1, st.scenes["1"])],
                 "studios": set(), "dates": [], "genre": "partie",
                 "bonus": 0.5, "depuis_titre": True}
        groupes._appliquer_serie(ctx, serie, 9.0, "essai")
        assert st.groups == {}
        assert st.appels["groupCreate"] == 0

    def test_aucune_modification_de_fiche(self):
        ctx, st = self._ctx_simule(performers=[performer(1, "X")])
        ctx.stash.update_performer({"id": "1", "country": "FR"})
        assert "country" not in st.performers["1"]

    def test_les_lectures_passent(self):
        ctx, _st = self._ctx_simule(performers=[performer(1, "X")])
        assert len(ctx.stash.find_performers()) == 1

    @pytest.mark.parametrize("mutation", [
        "performerUpdate", "performerCreate", "performerDestroy",
        "sceneUpdate", "studioUpdate", "studioCreate", "studioDestroy",
        "groupCreate", "groupUpdate", "groupDestroy",
        "tagUpdate", "tagsMerge", "configurePlugin"])
    def test_chaque_mutation_est_interceptee(self, mutation):
        ctx, st = self._ctx_simule()
        avant = dict(st.appels)
        ctx.stash.call_GQL(
            f"mutation($input: X!) {{ {mutation}(input: $input) "
            f"{{ id }} }}", {"input": {"id": "1", "name": "x"}})
        assert st.appels.get(mutation, 0) == avant.get(mutation, 0), \
            f"{mutation} a atteint le serveur en mode simulation"

    def test_la_creation_de_tag_reste_permise(self):
        """Les tags sont inoffensifs et nécessaires au calcul des
        propositions : les bloquer fausserait la simulation."""
        ctx, st = self._ctx_simule()
        assert noyau.tag_id(ctx, "Gaizer:essai")
        assert st.appels["create_tag"] == 1
