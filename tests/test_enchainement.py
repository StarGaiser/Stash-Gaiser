# -*- coding: utf-8 -*-
"""
Enchaînement des sources sur une même fiche.

Écrit AVANT le code.

Le plugin propose une tâche par source : lire les chemins, interroger
les sources, lire les vignettes. Chacune passe sur toute la
collection, et l'utilisateur doit connaître l'ordre — chemins d'abord,
car un titre et un studio donnent aux sources une prise qu'elles
n'avaient pas.

C'est une charge mentale que rien ne justifie. Une passe devrait
épuiser ce qu'elle peut sur une fiche AVANT de passer à la suivante :
lire le chemin, puis interroger les sources avec ce qu'on vient
d'apprendre, puis seulement les sources coûteuses si le manque persiste.

**Trois exigences guident l'enchaînement.**

L'ordre suit le COÛT et la FIABILITÉ. Le chemin est gratuit et exact ;
les sources coûtent des appels ; la vision coûte de l'argent et
transmet des images. Commencer par le moins cher n'est pas une
optimisation : c'est ce qui évite de payer pour une information déjà
disponible.

Une source ne s'exécute que si elle peut SERVIR. Interroger la vision
sur une scène dont le studio vient d'être trouvé serait payer pour
rien.

Chaque source reste DÉSACTIVABLE, et l'enchaînement lui-même aussi.
Quelqu'un qui veut piloter chaque étape doit pouvoir continuer.
"""


import enchainement
from faux import FauxStash, faux_contexte, performer, scene, studio


def _ctx(**reglages):
    base = {"applyMode": "auto", "sourceChemin": True}
    base.update(reglages)
    ctx = faux_contexte(base, FauxStash())
    ctx.args = {}
    return ctx


# ── L'ordre ──────────────────────────────────────────────────────────
class TestOrdre:
    """Du moins cher au plus cher, et du plus sûr au moins sûr."""

    def test_le_chemin_precede_les_sources(self):
        etapes = enchainement.sources_actives(_ctx())
        noms = [s.nom for s in etapes]
        assert noms.index("chemin") < noms.index("sources")

    def test_les_sources_precedent_la_vision(self):
        etapes = enchainement.sources_actives(_ctx(sourceVision=True))
        noms = [s.nom for s in etapes]
        assert noms.index("sources") < noms.index("vision")

    def test_une_voie_eteinte_ne_figure_pas(self):
        noms = [s.nom for s in enchainement.sources_actives(
            _ctx(sourceChemin=False))]
        assert "chemin" not in noms

    def test_les_voies_couteuses_sont_absentes_par_defaut(self):
        noms = [s.nom for s in enchainement.sources_actives(_ctx())]
        assert "vision" not in noms
        assert "generiques" not in noms


# ── Ce qui manque encore ─────────────────────────────────────────────
class TestManques:
    """Une source ne s'exécute que si elle peut servir."""

    def test_une_scene_complete_n_appelle_rien(self):
        sc = {"id": "1", "title": "Un titre",
              "studio": {"id": "9"},
              "performers": [{"id": "1"}], "date": "2020-01-01"}
        assert enchainement.manques(sc) == set()

    def test_un_studio_absent_est_signale(self):
        sc = {"id": "1", "title": "T", "performers": [{"id": "1"}],
              "date": "2020-01-01"}
        assert "studio" in enchainement.manques(sc)

    def test_un_titre_vide_compte_comme_absent(self):
        sc = {"id": "1", "title": "   ", "studio": {"id": "9"}}
        assert "title" in enchainement.manques(sc)

    def test_une_voie_sans_utilite_est_sautee(self):
        """La vision ne cherche que le studio : sur une scène qui en a
        un, l'appeler serait payer pour rien."""
        sc = {"id": "1", "studio": {"id": "9"}}
        assert not enchainement.utile("vision", enchainement.manques(sc))

    def test_une_voie_utile_est_gardee(self):
        sc = {"id": "1"}
        assert enchainement.utile("vision", enchainement.manques(sc))

    def test_les_sources_servent_a_tout(self):
        """Elles peuvent combler n'importe quel champ : dès qu'il
        manque quelque chose, elles ont leur place."""
        for manque in ("studio", "title", "performers", "date"):
            assert enchainement.utile("sources", {manque}), manque


# ── L'enchaînement ───────────────────────────────────────────────────
class TestEnchainement:

    def _monde(self, **reglages):
        st = FauxStash(
            scenes=[scene(10, "", files=[
                {"path": "/nas/Hardkinks/Archie Fox.mp4"}])],
            studios=[studio(9, "Hardkinks")],
            performers=[performer(1, "Archie Fox")])
        ctx = _ctx(**reglages)
        ctx.stash = st
        return st, ctx

    def test_une_passe_comble_ce_qu_elle_peut(self, monkeypatch):
        st, ctx = self._monde()
        monkeypatch.setattr(enchainement, "_appeler_sources",
                            lambda *a, **k: None)
        enchainement.enrichir_tout(ctx)
        assert (st.scenes["10"].get("studio") or {}).get("id") == "9"

    def test_les_sources_voient_ce_que_le_chemin_a_trouve(
            self, monkeypatch):
        """C'est la raison d'être de l'enchaînement : un titre et un
        studio donnent aux sources une prise qu'elles n'avaient pas."""
        vues = {}

        def capter(ctx, sc):
            vues["studio"] = (sc.get("studio") or {}).get("id")
        monkeypatch.setattr(enchainement, "_appeler_sources", capter)
        st, ctx = self._monde()
        enchainement.enrichir_tout(ctx)
        assert vues.get("studio") == "9"

    def test_une_voie_couteuse_n_est_pas_appelee_si_inutile(
            self, monkeypatch):
        """Le chemin ayant trouvé le studio, la vision n'a plus rien à
        chercher."""
        appels = []
        monkeypatch.setattr(enchainement, "_appeler_sources",
                            lambda *a, **k: None)
        monkeypatch.setattr(enchainement, "_appeler_vision",
                            lambda *a, **k: appels.append(1))
        st, ctx = self._monde(sourceVision=True)
        enchainement.enrichir_tout(ctx)
        assert appels == []

    def test_une_voie_couteuse_est_appelee_si_utile(self, monkeypatch):
        appels = []
        monkeypatch.setattr(enchainement, "_appeler_sources",
                            lambda *a, **k: None)
        monkeypatch.setattr(enchainement, "_appeler_vision",
                            lambda *a, **k: appels.append(1))
        st = FauxStash(scenes=[scene(10, "", files=[
            {"path": "/nas/inconnu/x.mp4"}])])
        ctx = _ctx(sourceVision=True)
        ctx.stash = st
        enchainement.enrichir_tout(ctx)
        assert appels == [1]

    def test_le_lot_est_respecte(self, monkeypatch):
        monkeypatch.setattr(enchainement, "_appeler_sources",
                            lambda *a, **k: None)
        st = FauxStash(scenes=[scene(10 + i, f"S{i}") for i in range(10)])
        ctx = _ctx(batchSize="3")
        ctx.stash = st
        vues = []
        monkeypatch.setattr(enchainement, "_traiter",
                            lambda ctx, sc, v: vues.append(sc["id"]))
        enchainement.enrichir_tout(ctx)
        assert len(vues) <= 3

    def test_simulation(self, monkeypatch):
        import noyau
        st, ctx = self._monde(dryRun=True)
        noyau._activer_simulation(ctx)
        monkeypatch.setattr(enchainement, "_appeler_sources",
                            lambda *a, **k: None)
        enchainement.enrichir_tout(ctx)
        assert not st.scenes["10"].get("studio")

    def test_collection_vide_ne_leve_pas(self):
        ctx = _ctx()
        ctx.stash = FauxStash()
        enchainement.enrichir_tout(ctx)

    def test_une_voie_qui_echoue_n_interrompt_pas(self, monkeypatch):
        """Une passe de lot ne doit pas s'arrêter sur une fiche."""
        def casser(*a, **k):
            raise RuntimeError("panne")
        monkeypatch.setattr(enchainement, "_appeler_sources", casser)
        st, ctx = self._monde()
        enchainement.enrichir_tout(ctx)
        assert (st.scenes["10"].get("studio") or {}).get("id") == "9"


# ── Le réglage ───────────────────────────────────────────────────────
class TestReglage:

    def test_l_enchainement_est_actif_par_defaut(self):
        """C'est le comportement attendu par quelqu'un qui découvre :
        lancer une tâche et qu'elle fasse ce qu'elle peut."""
        assert _ctx().source_active("enchainement")

    def test_il_peut_etre_desactive(self):
        """Qui veut piloter chaque étape doit pouvoir continuer."""
        ctx = _ctx(sourceEnchainement=False)
        assert not ctx.source_active("enchainement")
