# -*- coding: utf-8 -*-
"""
Enrichissement des scènes.

Le plus gros morceau du pipeline, et le plus délicat : une scène porte
des liens — studio, interprètes, groupe — et non de simples valeurs.
Se tromper y coûte plus qu'un champ mal rempli.

Deux mécanismes cohabitent. L'identification par EMPREINTE est sûre :
le fichier est reconnu, les données lui appartiennent. Le repli par
NOM DE FICHIER ne l'est pas : il devine, et doit dire qu'il devine.

C'est cette distinction que ces tests protègent avant tout.
"""

import json

import noyau
import scenes
from faux import FauxStash, faux_contexte, performer, scene, studio


# ── Le nom de fichier corrobore-t-il l'identification ? ──────────────
class TestCoherenceFichier:
    """Le repli par nom de fichier propose une identification qu'aucune
    empreinte ne confirme. Avant de l'accepter, on vérifie que le nom
    du fichier contient bien ce que la source prétend y trouver."""

    def test_studio_et_interprete_presents(self):
        note, _motif = scenes._coherence_fichier(
            "Masqulin - Archie Fox and Dean Young.mp4",
            "Some Title", "Masqulin", ["Archie Fox", "Dean Young"])
        assert note > 0

    def test_rien_ne_correspond(self):
        note, _motif = scenes._coherence_fichier(
            "video_2023_final.mp4", "Some Title", "Masqulin",
            ["Archie Fox"])
        assert note == 0

    def test_un_seul_indice_vaut_moins_que_deux(self):
        seul, _a = scenes._coherence_fichier(
            "Masqulin 12.mp4", "T", "Masqulin", ["Archie Fox"])
        deux, _b = scenes._coherence_fichier(
            "Masqulin - Archie Fox.mp4", "T", "Masqulin",
            ["Archie Fox"])
        assert deux > seul

    def test_casse_et_separateurs_ignores(self):
        for nom in ("MASQULIN_archie-fox.mp4",
                    "masqulin.archie.fox.1080p.mp4",
                    "Masqulin - Archie Fox [1080p].mkv"):
            note, _m = scenes._coherence_fichier(
                nom, "T", "Masqulin", ["Archie Fox"])
            assert note > 0, nom

    def test_valeurs_vides(self):
        """La fonction rend (note, explication) : sans rien à
        comparer, la note est nulle ou absente."""
        for args in (("", "", None, []), (None, None, None, None)):
            note, _motif = scenes._coherence_fichier(*args)
            assert not note


# ── Marquage des scènes non identifiées ──────────────────────────────
class TestMarquageNonIdentifiee:
    """Une scène qu'aucune source ne reconnaît doit le dire, et cesser
    de le dire quand elle finit par l'être. Sans idempotence, le tag
    s'accumulerait ou resterait à tort."""

    def test_le_tag_est_pose(self):
        st = FauxStash(scenes=[scene(10, "Inconnue")])
        ctx = faux_contexte({}, st)
        scenes._marquer_non_identifiee(ctx, st.scenes["10"], True)
        noms = {t["name"] for t in st.scenes["10"].get("tags") or []}
        assert any("identif" in n for n in noms)

    def test_le_tag_est_retire_quand_identifiee(self):
        st = FauxStash(scenes=[scene(10, "Connue")])
        ctx = faux_contexte({}, st)
        scenes._marquer_non_identifiee(ctx, st.scenes["10"], True)
        scenes._marquer_non_identifiee(ctx, st.scenes["10"], False)
        noms = {t["name"] for t in st.scenes["10"].get("tags") or []}
        assert not any("identif" in n for n in noms)

    def test_pose_repetee_sans_effet(self):
        st = FauxStash(scenes=[scene(10, "Inconnue")])
        ctx = faux_contexte({}, st)
        scenes._marquer_non_identifiee(ctx, st.scenes["10"], True)
        avant = len(st.journal)
        scenes._marquer_non_identifiee(ctx, st.scenes["10"], True)
        assert len([q for q, _d in st.journal[avant:]
                    if q == "update_scene"]) == 0

    def test_retrait_sur_scene_non_marquee(self):
        st = FauxStash(scenes=[scene(10, "Connue")])
        ctx = faux_contexte({}, st)
        scenes._marquer_non_identifiee(ctx, st.scenes["10"], False)
        assert not [q for q, _d in st.journal if q == "update_scene"]


# ── Application sur une scène ────────────────────────────────────────
class TestApplicationScene:

    def _monde(self, reglages=None, **champs):
        st = FauxStash(scenes=[scene(10, "Une scène", **champs)],
                       studios=[studio(1, "Masqulin")],
                       performers=[performer(1, "Archie Fox")])
        base = {"applyMode": "auto", "generateBioHot": False}
        base.update(reglages or {})
        ctx = faux_contexte(base, st)
        ctx.args = {}
        return st, ctx

    def _sans_ia(self, monkeypatch):
        monkeypatch.setattr(scenes, "synth_synopsis",
                            lambda *a, **k: None)

    def _appliquer(self, ctx, s, raw, cands):
        """`ent` n'est pas un dictionnaire mais un objet construit
        depuis les données brutes : il rapproche studio, interprètes
        et tags du référentiel de Stash."""
        ent = scenes.EntitesScene(ctx, raw)
        # `actuel` porte l'état de la scène AVANT écriture : c'est lui
        # qui protège les valeurs existantes. Le passer vide reviendrait
        # à dire que la scène n'a rien, et tout serait écrasé.
        actuel = {"title": s.get("title"), "date": s.get("date")}
        scenes._appliquer_scene(ctx, s, raw, cands, ent, actuel)

    def test_une_date_vide_est_remplie(self, monkeypatch):
        self._sans_ia(monkeypatch)
        st, ctx = self._monde()
        self._appliquer(
            ctx, st.scenes["10"],
            {"stashdb.org": {"date": "2023-05-01"}},
            {"date": [{"valeur": "2023-05-01", "note": 9.0,
                       "sources": ["stashdb.org"],
                       "commentaires": []}]})
        assert st.scenes["10"].get("date") == "2023-05-01"

    def test_une_date_existante_n_est_pas_ecrasee(self, monkeypatch):
        self._sans_ia(monkeypatch)
        st, ctx = self._monde(date="2020-01-01")
        self._appliquer(
            ctx, st.scenes["10"],
            {"stashdb.org": {"date": "2023-05-01"}},
            {"date": [{"valeur": "2023-05-01", "note": 9.0,
                       "sources": ["stashdb.org"],
                       "commentaires": []}]})
        assert st.scenes["10"]["date"] == "2020-01-01"

    def test_l_historique_est_alimente(self, monkeypatch):
        self._sans_ia(monkeypatch)
        st, ctx = self._monde()
        self._appliquer(
            ctx, st.scenes["10"],
            {"stashdb.org": {"date": "2023-05-01"}},
            {"date": [{"valeur": "2023-05-01", "note": 9.0,
                       "sources": ["stashdb.org"],
                       "commentaires": []}]})
        cf = st.scenes["10"].get("custom_fields") or {}
        hist = json.loads(cf.get("enrich_historique") or "[]")
        assert hist, "sans historique, l'annulation ne peut rien défaire"

    def test_simulation_n_ecrit_pas(self, monkeypatch):
        self._sans_ia(monkeypatch)
        st, ctx = self._monde({"dryRun": True})
        noyau._activer_simulation(ctx)
        self._appliquer(
            ctx, st.scenes["10"],
            {"stashdb.org": {"date": "2023-05-01"}},
            {"date": [{"valeur": "2023-05-01", "note": 9.0,
                       "sources": ["stashdb.org"],
                       "commentaires": []}]})
        assert not st.scenes["10"].get("date")

    def test_aucun_candidat_ne_leve_pas(self, monkeypatch):
        self._sans_ia(monkeypatch)
        st, ctx = self._monde()
        self._appliquer(ctx, st.scenes["10"], {}, {})


# ── Tâches ───────────────────────────────────────────────────────────
class TestTachesScenes:

    def _vierge(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        return st, ctx

    def _ecritures(self, st):
        return [q for q, _d in st.journal
                if q not in ("create_tag", "configuration")
                and not q.startswith(("find", "list_"))]

    def test_collection_vide(self, monkeypatch):
        monkeypatch.setattr(scenes.scrapers, "doit_verifier",
                            lambda ctx: False)
        st, ctx = self._vierge()
        scenes.enrich_scenes(ctx)
        scenes.apply_accepted_scenes(ctx)
        scenes.apply_covers(ctx)
        assert self._ecritures(st) == []

    def test_identifiant_inexistant(self):
        st = FauxStash(scenes=[scene(10, "Une scène")])
        ctx = faux_contexte({}, st)
        ctx.args = {"scene_id": "999999"}
        scenes.enrich_one_scene(ctx)
        assert self._ecritures(st) == []

    def test_identifiant_absent(self):
        st = FauxStash(scenes=[scene(10, "Une scène")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        scenes.enrich_one_scene(ctx)

    def test_application_sans_marqueur(self):
        st = FauxStash(scenes=[scene(10, "Une scène")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        scenes.apply_accepted_scenes(ctx)
        assert self._ecritures(st) == []

    def test_covers_sans_scene_identifiee(self):
        st = FauxStash(scenes=[scene(10, "Une scène")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        scenes.apply_covers(ctx)
        assert self._ecritures(st) == []


# ── Détection des scrapers greffée en fin de tâche ───────────────────
class TestGreffeScrapers:
    """La détection se lance au bout de l'enrichissement des scènes.
    Elle ne doit ni installer, ni faire échouer la tâche."""

    def test_la_detection_est_appelee(self, monkeypatch):
        vus = []
        monkeypatch.setattr(scenes.scrapers, "doit_verifier",
                            lambda ctx: True)
        monkeypatch.setattr(scenes.scrapers, "detecter",
                            lambda ctx: vus.append(1) or [])
        monkeypatch.setattr(scenes.scrapers, "marquer_verifie",
                            lambda ctx: None)
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        scenes.enrich_scenes(ctx)
        assert vus == [1]

    def test_une_detection_qui_echoue_n_interrompt_pas(self,
                                                      monkeypatch):
        """Le catalogue est distant : son indisponibilité ne doit pas
        faire échouer un enrichissement qui, lui, a réussi."""
        monkeypatch.setattr(scenes.scrapers, "doit_verifier",
                            lambda ctx: True)

        def casse(ctx):
            raise RuntimeError("catalogue injoignable")
        monkeypatch.setattr(scenes.scrapers, "detecter", casse)
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        scenes.enrich_scenes(ctx)

    def test_la_cadence_est_respectee(self, monkeypatch):
        vus = []
        monkeypatch.setattr(scenes.scrapers, "doit_verifier",
                            lambda ctx: False)
        monkeypatch.setattr(scenes.scrapers, "detecter",
                            lambda ctx: vus.append(1) or [])
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        scenes.enrich_scenes(ctx)
        assert vus == []
