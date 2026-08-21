# -*- coding: utf-8 -*-
"""
Lecture des sprites : le début et la fin de la vidéo.

Écrit AVANT le code.

La vignette d'une scène est une image prise au milieu : elle porte le
filigrane du studio, jamais le générique. Or Stash produit aussi un
SPRITE — une planche de cases réparties sur toute la durée, avec un
fichier VTT qui donne les coordonnées et l'horodatage de chacune.

Les premières et dernières cases contiennent ce que le milieu n'a pas :
titre d'ouverture, et surtout générique de fin où figurent les noms des
interprètes.

**Le rendement est faible et il faut l'assumer.** Sur un échantillon,
une scène sur huit porte un générique lisible. C'est peu, mais ces
scènes-là ne sont atteintes par aucun autre moyen — ni empreinte, ni
nom de fichier, ni filigrane.

**Le risque est l'invention.** Une case fait 160×90 pixels ; agrandie,
elle invite le modèle à halluciner. Un essai a produit un paragraphe
sur l'environnement à partir d'une image sans texte. Les garde-fous
comptent donc plus ici qu'ailleurs.

**Un nom lu n'est jamais appliqué.** Attribuer une scène au mauvais
interprète est l'erreur qu'aucun arbitrage ne rattrape.
"""

import json

import pytest


import sprites
from faux import FauxStash, faux_contexte, performer, scene


VTT = """WEBVTT

00:00:00.000 --> 00:00:10.000
s_sprite.jpg#xywh=0,0,160,90

00:00:10.000 --> 00:00:20.000
s_sprite.jpg#xywh=160,0,160,90

00:13:54.666 --> 00:14:05.100
s_sprite.jpg#xywh=1280,720,160,90
"""


def _ctx(**reglages):
    base = {"language": "fr", "aiVision": "mistral:pixtral-12b",
            "llmApiKey": "essai", "visionEnvoiImages": True,
            "sourceGeneriques": True}
    base.update(reglages)
    ctx = faux_contexte(base, FauxStash())
    ctx.args = {}
    return ctx


# ── Découpage de la planche ──────────────────────────────────────────
class TestDecoupage:
    """Le VTT dit où se trouve chaque case. S'en remettre à un calcul
    supposerait une grille régulière que rien ne garantit."""

    def test_les_cases_sont_lues_dans_l_ordre(self):
        cases = sprites.cases_du_vtt(VTT)
        assert len(cases) == 3
        assert cases[0] == (0, 0, 160, 90)
        assert cases[-1] == (1280, 720, 160, 90)

    def test_un_vtt_vide_ne_leve_pas(self):
        for brut in ("", None, "WEBVTT", "n'importe quoi"):
            assert sprites.cases_du_vtt(brut) == []

    def test_un_vtt_malforme_ne_leve_pas(self):
        assert sprites.cases_du_vtt("#xywh=a,b,c,d") == []

    def test_seules_les_cases_utiles_sont_retenues(self):
        """Lire les cent cases d'une planche coûterait cent appels
        pour une information qui tient dans deux."""
        choisies = sprites.cases_utiles(sprites.cases_du_vtt(VTT))
        assert len(choisies) <= 3

    def test_le_debut_et_la_fin_sont_pris(self):
        cases = [(i * 160, 0, 160, 90) for i in range(20)]
        choisies = sprites.cases_utiles(cases)
        assert cases[0] in choisies
        assert cases[-1] in choisies

    def test_une_planche_a_une_seule_case(self):
        cases = [(0, 0, 160, 90)]
        assert sprites.cases_utiles(cases) == cases

    def test_aucune_case(self):
        assert sprites.cases_utiles([]) == []


# ── Disponibilité ────────────────────────────────────────────────────
class TestDisponibilite:
    """Découper une image demande une bibliothèque que le plugin n'a
    pas par défaut. Son absence doit dégrader proprement, non
    interrompre."""

    def test_sans_bibliotheque_la_tache_le_dit(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: None)
        assert not sprites.disponible()

    def test_sans_bibliotheque_rien_n_est_lu(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: None)
        st = FauxStash(scenes=[scene(10, "Sans interprète")])
        ctx = _ctx()
        ctx.stash = st
        sprites.lire_generiques(ctx)
        assert not (st.scenes["10"].get("custom_fields") or {}).get(
            "enrich_generique")

    def test_le_message_dit_comment_installer(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: None)
        messages = []
        monkeypatch.setattr(sprites.log, "warning",
                            lambda m, *a, **k: messages.append(str(m)))
        ctx = _ctx()
        ctx.stash = FauxStash(scenes=[scene(10, "X")])
        sprites.lire_generiques(ctx)
        assert any("pillow" in m.lower() for m in messages)


# ── Lecture des noms ─────────────────────────────────────────────────
class TestLectureDesNoms:
    """Ce que le modèle rapporte doit ressembler à un nom, sinon
    c'est du décor lu au hasard."""

    def _repond(self, monkeypatch, reponse):
        monkeypatch.setattr(sprites, "_lire_case",
                            lambda *a, **k: reponse)

    def test_des_noms_sont_rendus(self, monkeypatch):
        self._repond(monkeypatch, ["EDU BOXER", "HUGO VERGARI"])
        noms = sprites.noms_plausibles(["EDU BOXER", "HUGO VERGARI"])
        assert "EDU BOXER" in noms

    def test_un_texte_qui_n_est_pas_un_nom_est_ecarte(self):
        """« LACOSTE » sur un vêtement, « HD », « 4K », une année :
        du texte lisible n'est pas un nom d'interprète."""
        for texte in ("HD", "4K", "2023", "1080P", "COM",
                      "WWW.EXEMPLE.COM", "SCENE 4", "0"):
            assert texte not in sprites.noms_plausibles([texte]), texte

    def test_un_nom_doit_avoir_deux_parties(self):
        """Un mot seul est trop ambigu : « BOXER » peut être un nom,
        une marque ou un vêtement. Deux mots réduisent le hasard."""
        assert sprites.noms_plausibles(["BOXER"]) == []
        assert sprites.noms_plausibles(["EDU BOXER"]) == ["EDU BOXER"]

    def test_une_phrase_est_ecartee(self):
        """Une hallucination produit des phrases, pas des noms."""
        long = ("L'objectif de cette étude est d'analyser les impacts "
                "environnementaux")
        assert sprites.noms_plausibles([long]) == []

    def test_les_mentions_de_generique_sont_retirees(self):
        """« STARRING », « DIRECTED BY » encadrent les noms sans en
        être."""
        noms = sprites.noms_plausibles(
            ["STARRING", "EDU BOXER", "DIRECTED BY JOHN SMITH"])
        assert "EDU BOXER" in noms
        assert "STARRING" not in noms

    def test_valeurs_absurdes(self):
        for entree in (None, [], [None], [""], [42], [["x"]]):
            assert isinstance(sprites.noms_plausibles(entree), list)


# ── Rapprochement au catalogue ───────────────────────────────────────
class TestRapprochement:
    """Un nom lu doit désigner un interprète EXISTANT, ou rester une
    simple mention."""

    INDEX = {"archie fox": "1", "dean young": "2"}

    def test_un_nom_connu_est_rapproche(self):
        assert sprites.rapprocher_interprete("ARCHIE FOX",
                                             self.INDEX) == "1"

    def test_la_casse_est_ignoree(self):
        assert sprites.rapprocher_interprete("archie  fox",
                                             self.INDEX) == "1"

    def test_un_nom_inconnu_ne_rapproche_rien(self):
        """Et surtout, ne crée rien : un nom lu sur une image
        agrandie n'a pas la fiabilité qu'exige la création d'une
        fiche."""
        assert sprites.rapprocher_interprete("EDU BOXER",
                                             self.INDEX) is None

    def test_aucun_rapprochement_partiel(self):
        for lu in ("ARCHIE", "FOX", "ARCHIE FOXX"):
            assert sprites.rapprocher_interprete(lu, self.INDEX) \
                is None, lu


# ── La tâche ─────────────────────────────────────────────────────────
class TestTache:

    def _monde(self, monkeypatch, textes):
        st = FauxStash(
            scenes=[scene(10, "Sans interprète",
                          paths={"sprite": "https://x.test/s.jpg",
                                 "vtt": "https://x.test/s.vtt"})],
            performers=[performer(1, "Archie Fox")])
        ctx = _ctx()
        ctx.stash = st
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        monkeypatch.setattr(sprites, "cases_utiles",
                            lambda c: [(0, 0, 160, 90)])
        monkeypatch.setattr(sprites, "cases_du_vtt",
                            lambda v: [(0, 0, 160, 90)])
        monkeypatch.setattr(sprites, "_telecharger",
                            lambda *a, **k: b"planche")
        monkeypatch.setattr(sprites, "_lire_case",
                            lambda *a, **k: {"noms": textes,
                                            "studio": None})
        return st, ctx

    def test_un_nom_connu_est_propose(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, ["ARCHIE FOX"])
        sprites.lire_generiques(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        d = json.loads(cf.get("enrich_generique") or "{}")
        assert "1" in (d.get("performer_ids") or [])

    def test_la_scene_n_est_pas_modifiee(self, monkeypatch):
        """Une lecture de générique propose ; elle n'attribue pas."""
        st, ctx = self._monde(monkeypatch, ["ARCHIE FOX"])
        sprites.lire_generiques(ctx)
        assert not st.scenes["10"].get("performers")

    def test_un_nom_inconnu_est_consigne_sans_lien(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, ["EDU BOXER"])
        sprites.lire_generiques(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        d = json.loads(cf.get("enrich_generique") or "{}")
        assert "EDU BOXER" in (d.get("noms_lus") or [])
        assert not (d.get("performer_ids") or [])

    def test_une_scene_avec_interpretes_est_ignoree(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, ["ARCHIE FOX"])
        st.scenes["10"]["performers"] = [{"id": "1", "name": "Archie"}]
        vues = []
        monkeypatch.setattr(sprites, "_lire_case",
                            lambda *a, **k: vues.append(1)
                            or {"noms": [], "studio": None})
        sprites.lire_generiques(ctx)
        assert vues == []

    def test_une_scene_deja_lue_n_est_pas_relue(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, ["ARCHIE FOX"])
        st.scenes["10"]["custom_fields"] = {
            "enrich_generique_le": "2026-08-08"}
        vues = []
        monkeypatch.setattr(sprites, "_lire_case",
                            lambda *a, **k: vues.append(1)
                            or {"noms": [], "studio": None})
        sprites.lire_generiques(ctx)
        assert vues == []

    def test_sans_consentement_rien_n_est_envoye(self, monkeypatch):
        """Un sprite est une image : le même consentement que pour les
        vignettes s'applique."""
        st, ctx = self._monde(monkeypatch, ["ARCHIE FOX"])
        ctx.settings["visionEnvoiImages"] = False
        vues = []
        monkeypatch.setattr(sprites, "_lire_case",
                            lambda *a, **k: vues.append(1)
                            or {"noms": [], "studio": None})
        sprites.lire_generiques(ctx)
        assert vues == []

    def test_simulation(self, monkeypatch):
        import noyau
        st, ctx = self._monde(monkeypatch, ["ARCHIE FOX"])
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        sprites.lire_generiques(ctx)
        assert not (st.scenes["10"].get("custom_fields") or {}).get(
            "enrich_generique")

    def test_collection_vide_ne_leve_pas(self, monkeypatch):
        ctx = _ctx()
        ctx.stash = FauxStash()
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        sprites.lire_generiques(ctx)


class TestDecoupageReel:
    """Le découpage d'image lui-même, avec une vraie planche. C'est là
    que vit le risque : une case mal découpée produit une image
    illisible, et le modèle invente plutôt que de se taire."""

    def _planche(self, largeur=640, hauteur=180):
        Image = sprites._pillow()
        if Image is None:
            pytest.skip("Pillow absent")
        import io as _io
        im = Image.new("RGB", (largeur, hauteur), (30, 30, 30))
        tampon = _io.BytesIO()
        im.save(tampon, "JPEG")
        return tampon.getvalue()

    def test_une_case_est_extraite_et_agrandie(self, monkeypatch):
        vues = {}

        def capter(ctx, image, prompt):
            vues["octets"] = len(image)
            return '{"noms": ["EDU BOXER"]}'
        monkeypatch.setattr(sprites.vision, "_appel_vision", capter)
        lu = sprites._lire_case(_ctx(), self._planche(),
                                (0, 0, 160, 90))
        assert lu["noms"] == ["EDU BOXER"]
        assert vues["octets"] > 1000, "l'image doit être agrandie"

    def test_une_case_hors_planche_ne_leve_pas(self, monkeypatch):
        monkeypatch.setattr(sprites.vision, "_appel_vision",
                            lambda *a, **k: '{"noms": []}')
        assert sprites._lire_case(_ctx(), self._planche(),
                                  (9999, 9999, 160, 90))["noms"] == []

    def test_une_planche_illisible_ne_leve_pas(self):
        assert sprites._lire_case(_ctx(), b"pas une image",
                                  (0, 0, 160, 90))["noms"] == []

    def test_une_reponse_malformee_ne_leve_pas(self, monkeypatch):
        for brut in ("", None, "pas du json", "{cassé", "[]"):
            # La valeur est liée par DÉFAUT, non capturée : une lambda
            # dans une boucle voit la variable, pas sa valeur au
            # moment de la définition — les cinq appels emploieraient
            # la dernière.
            monkeypatch.setattr(sprites.vision, "_appel_vision",
                                lambda *a, _r=brut, **k: _r)
            assert sprites._lire_case(_ctx(), self._planche(),
                                      (0, 0, 160, 90))["noms"] == []

    def test_un_bloc_de_code_est_traverse(self, monkeypatch):
        monkeypatch.setattr(
            sprites.vision, "_appel_vision",
            lambda *a, **k: '```json\n{"noms": ["EDU BOXER"]}\n```')
        assert sprites._lire_case(_ctx(), self._planche(),
                                  (0, 0, 160, 90))["noms"] == ["EDU BOXER"]

    def test_sans_pillow_aucune_lecture(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: None)
        assert sprites._lire_case(_ctx(), b"x",
                                  (0, 0, 160, 90))["noms"] == []


class TestTacheCompletion:
    """Les chemins de sortie de la tâche, qui décident si un appel
    part ou non."""

    def _ctx_stash(self, scenes, **reglages):
        st = FauxStash(scenes=scenes,
                       performers=[performer(1, "Archie Fox")])
        ctx = _ctx(**reglages)
        ctx.stash = st
        return st, ctx

    def test_sans_modele_configure(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        st, ctx = self._ctx_stash([scene(10, "X")])
        ctx.settings["aiVision"] = ""
        ctx.settings["aiDefault"] = ""
        sprites.lire_generiques(ctx)
        assert not (st.scenes["10"].get("custom_fields") or {})

    def test_une_scene_sans_sprite_est_ignoree(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        vues = []
        monkeypatch.setattr(sprites, "_telecharger",
                            lambda *a, **k: vues.append(1) or b"x")
        st, ctx = self._ctx_stash([scene(10, "Sans sprite")])
        sprites.lire_generiques(ctx)
        assert vues == []

    def test_une_adresse_etrangere_est_refusee(self, monkeypatch):
        """La planche vient de Stash : une adresse quelconque serait
        un moyen de faire télécharger n'importe quoi au plugin."""
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        vues = []
        monkeypatch.setattr(sprites, "_telecharger",
                            lambda *a, **k: vues.append(1) or b"x")
        st, ctx = self._ctx_stash([scene(
            10, "X", paths={"sprite": "file:///etc/passwd",
                            "vtt": "file:///etc/passwd"})])
        sprites.lire_generiques(ctx)
        assert vues == []

    def test_une_planche_inaccessible_ne_leve_pas(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        monkeypatch.setattr(
            sprites, "_telecharger",
            lambda *a, **k: (_ for _ in ()).throw(OSError("coupé")))
        st, ctx = self._ctx_stash([scene(
            10, "X", paths={"sprite": "https://exemple.test/s.jpg",
                            "vtt": "https://exemple.test/s.vtt"})])
        sprites.lire_generiques(ctx)

    def test_un_vtt_sans_case_est_ignore(self, monkeypatch):
        monkeypatch.setattr(sprites, "_pillow", lambda: object())
        monkeypatch.setattr(sprites, "_telecharger",
                            lambda *a, **k: b"WEBVTT")
        vues = []
        monkeypatch.setattr(sprites, "_lire_case",
                            lambda *a, **k: vues.append(1)
                            or {"noms": [], "studio": None})
        st, ctx = self._ctx_stash([scene(
            10, "X", paths={"sprite": "https://exemple.test/s.jpg",
                            "vtt": "https://exemple.test/s.vtt"})])
        sprites.lire_generiques(ctx)
        assert vues == []


class TestHallucination:
    """Une case de 160×90 agrandie invite le modèle à inventer. Un
    essai réel a produit « ВАСЯ ВЕТРОВ » en cyrillique et « Bill
    Pertwee » — un acteur de sitcom britannique — sur la même image.

    Deux signaux distinguent l'invention de la lecture. Un alphabet
    qui n'a rien à faire là : le générique d'un studio occidental ne
    s'écrit pas en cyrillique. Et l'absence de cohérence entre les
    noms d'une même case — un générique liste des interprètes du même
    film, pas un mélange d'origines."""

    def test_un_alphabet_etranger_est_ecarte(self):
        for texte in ("ВАСЯ ВЕТРОВ", "山田 太郎", "김철수 이영희"):
            assert sprites.noms_plausibles([texte]) == [], texte

    def test_les_accents_latins_restent_acceptes(self):
        """Les noms espagnols et portugais en portent : les écarter
        perdrait de vraies lectures."""
        for texte in ("José Domínguez", "Germán Álvarez",
                      "François Léger"):
            assert sprites.noms_plausibles([texte]) == [texte], texte

    def test_un_melange_d_alphabets_annule_la_case(self):
        """Si une case mêle cyrillique et latin, elle n'est pas lue :
        elle est inventée. Garder la moitié latine reviendrait à
        retenir la moitié d'une hallucination."""
        lus = sprites.noms_plausibles(["ВАСЯ ВЕТРОВ", "Bill Pertwee"])
        assert lus == []

    def test_une_case_coherente_est_gardee(self):
        lus = sprites.noms_plausibles(["MIKEL BOSCO", "CESAR FERRER"])
        assert len(lus) == 2

    def test_trop_de_noms_sur_une_case(self):
        """Une case de générique porte quelques noms. Une liste de
        quinze est un signe d'invention."""
        beaucoup = [f"Prenom{i} Nom{i}" for i in range(15)]
        assert sprites.noms_plausibles(beaucoup) == []


class TestApplicationDesGeneriques:
    """Les noms lus au générique se consignaient dans un champ que
    rien ne reprenait — le même cul-de-sac que les propositions de
    vision, corrigé pour l'une et oublié pour l'autre.

    Un interprète reconnu au catalogue doit pouvoir être relié ; un
    nom inconnu reste une mention, car créer une fiche depuis une
    image agrandie serait aventureux."""

    def _monde(self, proposition, **reglages):
        st = FauxStash(
            scenes=[scene(10, "Sans interprète", custom_fields={
                "enrich_generique": json.dumps(proposition)})],
            performers=[performer(1, "Archie Fox"),
                        performer(2, "Dean Young")])
        base = {"applyMode": "auto", "sourceGeneriques": True}
        base.update(reglages)
        ctx = faux_contexte(base, st)
        ctx.args = {}
        return st, ctx

    def test_les_interpretes_reconnus_sont_relies(self):
        st, ctx = self._monde({"noms_lus": ["ARCHIE FOX", "DEAN YOUNG"],
                               "performer_ids": ["1", "2"]})
        sprites.appliquer_generiques(ctx)
        ids = {q["id"] for q in st.scenes["10"].get("performers") or []}
        assert ids == {"1", "2"}

    def test_une_scene_avec_interpretes_n_est_pas_touchee(self):
        """Le générique complète, il ne remplace pas."""
        st, ctx = self._monde({"noms_lus": ["ARCHIE FOX"],
                               "performer_ids": ["1"]})
        st.scenes["10"]["performers"] = [{"id": "2", "name": "Dean"}]
        sprites.appliquer_generiques(ctx)
        ids = {q["id"] for q in st.scenes["10"].get("performers") or []}
        assert "2" in ids

    def test_un_nom_inconnu_ne_cree_rien(self):
        """Créer une fiche depuis un nom lu sur une image agrandie
        serait aventureux : une erreur de lecture peuplerait le
        catalogue de fantômes."""
        st, ctx = self._monde({"noms_lus": ["EDU BOXER"],
                               "performer_ids": []})
        sprites.appliquer_generiques(ctx)
        assert not st.scenes["10"].get("performers")
        assert len(st.performers) == 2

    def test_la_provenance_dit_que_c_est_le_generique(self):
        st, ctx = self._monde({"noms_lus": ["ARCHIE FOX"],
                               "performer_ids": ["1"]})
        sprites.appliquer_generiques(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        trace = str(cf.get("enrich_sources") or "").lower()
        assert "generique" in trace or "générique" in trace

    def test_simulation(self):
        import noyau
        st, ctx = self._monde({"noms_lus": ["ARCHIE FOX"],
                               "performer_ids": ["1"]}, dryRun=True)
        noyau._activer_simulation(ctx)
        sprites.appliquer_generiques(ctx)
        assert not st.scenes["10"].get("performers")

    def test_sans_proposition_ne_leve_pas(self):
        st = FauxStash(scenes=[scene(10, "Rien")])
        ctx = faux_contexte({"sourceGeneriques": True}, st)
        ctx.args = {}
        sprites.appliquer_generiques(ctx)

    def test_une_proposition_illisible_ne_leve_pas(self):
        st = FauxStash(scenes=[scene(10, "X", custom_fields={
            "enrich_generique": "{cassé"})])
        ctx = faux_contexte({"sourceGeneriques": True}, st)
        ctx.args = {}
        sprites.appliquer_generiques(ctx)


class TestStudioAuGenerique:
    """Un générique porte le nom du studio autant que ceux des
    interprètes — c'est même souvent la seule chose lisible sur un
    carton de fin. Ne chercher que les noms de personnes jette la
    moitié de ce que le modèle a lu."""

    def test_le_studio_est_demande_dans_le_prompt(self):
        import i18n
        for lg in ("en", "fr", "de", "es", "it", "pt", "nl"):
            texte = i18n.t("prompt_generique", lg).lower()
            assert any(m in texte for m in
                       ("studio", "estudio", "estúdio")), lg

    def test_un_studio_lu_est_rendu(self, monkeypatch):
        monkeypatch.setattr(
            sprites.vision, "_appel_vision",
            lambda *a, **k: '{"noms": ["ARCHIE FOX"], '
                            '"studio": "MASQULIN"}')
        Image = sprites._pillow()
        if Image is None:
            pytest.skip("Pillow absent")
        import io as _io
        im = Image.new("RGB", (640, 180), (30, 30, 30))
        t = _io.BytesIO()
        im.save(t, "JPEG")
        lu = sprites._lire_case(_ctx(), t.getvalue(), (0, 0, 160, 90))
        assert lu.get("studio") == "MASQULIN"
        assert "ARCHIE FOX" in lu.get("noms")

    def test_le_studio_est_rapproche_du_catalogue(self):
        assert sprites.rapprocher_studio(
            "MASQULIN", {"masqulin": "1"}) == "1"

    def test_un_studio_inconnu_ne_rapproche_rien(self):
        assert sprites.rapprocher_studio(
            "INCONNU", {"masqulin": "1"}) is None
