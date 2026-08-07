# -*- coding: utf-8 -*-
"""
Lecture des vignettes : ce qu'un modèle de vision peut dire, et ce
qu'il ne dira pas.

Écrit AVANT le code.

**Le point de départ est une limite, pas une possibilité.** Les
fournisseurs commerciaux refusent d'identifier une personne réelle sur
une image — c'est une politique, non une lacune technique. Demander
« qui est-ce ? » obtient un refus ; demander « est-ce bien X ? » aussi,
car c'est la même question déguisée.

Ce module ne cherche donc pas à identifier des personnes. Il lit ce qui
est ÉCRIT sur l'image : filigranes de studio, adresses, titres
incrustés. C'est de la lecture de texte, sans restriction, et le studio
est le meilleur réducteur de candidats disponible — une fois connu, le
casting récurrent et les scrapers dédiés font le reste.

Trois exigences guident ces tests :

  **Ne jamais demander l'identification d'une personne.** Un test
  vérifie que le prompt ne le demande pas, quelle que soit la langue.

  **Une lecture n'est pas une source.** Ce qui sort d'un modèle de
  vision est une hypothèse à vérifier, notée comme telle et jamais
  écrite d'autorité.

  **Le refus est une réponse valide.** Un modèle qui décline doit être
  compris comme tel, non traité comme une panne à réessayer.
"""

import json
from types import MappingProxyType

import pytest

import i18n
import vision
from faux import FauxStash, faux_contexte, scene, studio


LANGUES = ("en", "fr", "de", "es", "it", "pt", "nl")


def _ctx(**reglages):
    """Contexte muni d'un modèle de vision ET de la clé qui
    l'accompagne : sans elle, `ai_for` rend None et toutes les
    réponses deviennent « aucun modèle configuré »."""
    base = {"language": "fr", "aiVision": "mistral:pixtral",
            "llmApiKey": "essai", "visionEnvoiImages": True}
    base.update(reglages)
    ctx = faux_contexte(base, FauxStash())
    ctx.args = {}
    return ctx


def _repond(monkeypatch, reponse):
    monkeypatch.setattr(vision, "_appel_vision", lambda *a, **k: reponse)


# ── Ce que le prompt demande, et ce qu'il ne demande pas ─────────────
class TestPrompt:
    """La limite est dans la question posée, pas dans le traitement de
    la réponse. Un prompt qui demande une identification obtient un
    refus dans le meilleur des cas — et une invention dans le pire."""

    @pytest.mark.parametrize("langue", LANGUES)
    def test_le_prompt_existe_dans_chaque_langue(self, langue):
        texte = i18n.t("prompt_vision", langue)
        assert texte and texte != "prompt_vision"

    @pytest.mark.parametrize("langue", LANGUES)
    def test_aucune_demande_d_identification(self, langue):
        """Le contrôle porte sur les VERBES d'identification appliqués
        à une personne. Sa formulation varie ; l'intention non."""
        texte = i18n.t("prompt_vision", langue).lower()
        # Le contrôle vise le verbe appliqué à une PERSONNE. « ce qui
        # est écrit » contient « qui est » sans rien demander de tel :
        # un motif trop large crierait au loup et finirait ignoré.
        import re as _re
        interdits = (
            r"qui est (cette|la) personne", r"who is (this|the) person",
            r"wer ist diese person", r"quién es esta persona",
            r"chi è questa persona", r"quem é esta pessoa",
            r"wie is deze persoon",
            r"identifi\w* (la |the |die |el |il |o |de )?person",
            r"reconna\w+ (la |cette )?personne",
            r"recogni[sz]e the person",
            r"nomme\w* (la |the )?person",
        )
        for motif in interdits:
            assert not _re.search(motif, texte), \
                f"{langue} : « {motif} »"

    @pytest.mark.parametrize("langue", LANGUES)
    def test_le_prompt_demande_du_texte_lu(self, langue):
        """Filigrane, logo, adresse : ce qui est écrit sur l'image."""
        texte = i18n.t("prompt_vision", langue).lower()
        assert any(mot in texte for mot in (
            "filigrane", "watermark", "wasserzeichen", "marca",
            "filigrana", "watermerk", "logo"))

    @pytest.mark.parametrize("langue", LANGUES)
    def test_le_prompt_interdit_d_inventer(self, langue):
        texte = i18n.t("prompt_vision", langue).lower()
        assert any(mot in texte for mot in (
            "invent", "erfind", "verzin", "supposi", "guess",
            "adivin", "null", "rien", "nothing", "nichts", "nada",
            "niets", "nulla"))

    def test_le_prompt_suit_la_langue(self):
        textes = {vision.prompt_vision(_ctx(language=lg))
                  for lg in LANGUES}
        assert len(textes) >= 5


# ── Lecture de la réponse ────────────────────────────────────────────
class TestLectureDeLaReponse:
    """Un modèle répond ce qu'il veut, dans la forme qu'il veut."""

    def _reponse(self, **champs):
        base = {"studio": None, "texte_lu": [], "confiance": 0.0}
        base.update(champs)
        return json.dumps(base)

    def test_un_studio_lu_est_rendu(self, monkeypatch):
        _repond(monkeypatch, self._reponse(
            studio="Masqulin", texte_lu=["MASQULIN.COM"],
            confiance=0.9))
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu and lu.get("studio") == "Masqulin"

    def test_sans_texte_lu_rien_n_est_retenu(self, monkeypatch):
        """Un studio annoncé sans qu'aucun texte n'ait été lu est une
        déduction visuelle — donc une supposition."""
        _repond(monkeypatch, self._reponse(
            studio="Masqulin", confiance=0.95))
        lu, motif = vision.lire_vignette(_ctx(), b"image")
        assert lu is None
        assert "texte" in motif.lower()

    def test_une_confiance_faible_est_refusee(self, monkeypatch):
        _repond(monkeypatch, self._reponse(
            studio="Masqulin", texte_lu=["MASQ..."], confiance=0.3))
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu is None

    def test_le_texte_lu_doit_soutenir_le_studio(self, monkeypatch):
        """Le nom annoncé doit se retrouver dans ce qui a été lu :
        c'est le seul contrôle possible contre une invention."""
        _repond(monkeypatch, self._reponse(
            studio="Masqulin", texte_lu=["FALCON STUDIOS"],
            confiance=0.9))
        lu, motif = vision.lire_vignette(_ctx(), b"image")
        assert lu is None
        assert "correspond" in motif.lower() or "soutien" in motif.lower()

    def test_un_refus_du_modele_est_compris(self, monkeypatch):
        """Un fournisseur qui décline n'est pas une panne : le
        signaler comme telle ferait réessayer indéfiniment."""
        for refus in (
                "I'm sorry, I can't identify people in images.",
                "Je ne peux pas identifier de personnes.",
                "I cannot help with identifying individuals."):
            _repond(monkeypatch, refus)
            lu, motif = vision.lire_vignette(_ctx(), b"image")
            assert lu is None
            assert "refus" in motif.lower(), refus

    def test_reponse_illisible(self, monkeypatch):
        for brut in ("", None, "pas du json", "{cassé", "[]"):
            _repond(monkeypatch, brut)
            lu, _motif = vision.lire_vignette(_ctx(), b"image")
            assert lu is None, brut

    def test_json_noye_dans_du_texte(self, monkeypatch):
        _repond(monkeypatch, "Voici :\n" + self._reponse(
            studio="Masqulin", texte_lu=["MASQULIN"], confiance=0.9)
            + "\nJ'espère que cela aide.")
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu and lu.get("studio") == "Masqulin"

    def test_sans_modele_configure(self, monkeypatch):
        ctx = faux_contexte({"language": "fr"}, FauxStash())
        ctx.args = {}
        lu, motif = vision.lire_vignette(ctx, b"image")
        assert lu is None and motif


# ── Rapprochement au catalogue ───────────────────────────────────────
class TestRapprochement:
    """Un nom lu sur une image est approximatif : caractères mal
    reconnus, casse, suffixes. Le rapprocher d'un studio existant vaut
    mieux que d'en créer un de plus."""

    STUDIOS = MappingProxyType({"masqulin": "1", "falcon studios": "2",
               "men com": "3"})

    def test_correspondance_exacte(self):
        assert vision.rapprocher_studio("Masqulin",
                                        self.STUDIOS) == "1"

    def test_casse_et_ponctuation_ignorees(self):
        for lu in ("MASQULIN", "masqulin.com", "Masqulin ",
                   "MASQULIN.COM"):
            assert vision.rapprocher_studio(lu, self.STUDIOS) == "1", lu

    def test_aucun_rapprochement_approximatif(self):
        """« Falcon » ne doit pas ramener « Falcon Studios » : un
        studio attribué à tort vaut moins que pas de studio."""
        for lu in ("Falcon", "Masq", "Men", "Studios"):
            assert vision.rapprocher_studio(lu, self.STUDIOS) is None, lu

    def test_nom_inconnu(self):
        assert vision.rapprocher_studio("Inconnu", self.STUDIOS) is None

    def test_valeurs_vides(self):
        for lu in ("", None, "  "):
            assert vision.rapprocher_studio(lu, self.STUDIOS) is None


# ── La tâche ─────────────────────────────────────────────────────────
class TestTache:
    """Elle ne traite QUE les scènes sans studio : lire une vignette
    coûte un appel payant, et une scène déjà renseignée n'a rien à y
    gagner."""

    def _monde(self, **champs):
        st = FauxStash(
            scenes=[scene(10, "Sans studio", **champs),
                    scene(11, "Avec studio", studio={"id": "1"})],
            studios=[studio(1, "Masqulin")])
        ctx = faux_contexte({"language": "fr"}, st)
        ctx.args = {}
        return st, ctx

    def test_une_scene_avec_studio_est_ignoree(self, monkeypatch):
        _st, ctx = self._monde()
        vues = []
        monkeypatch.setattr(vision, "lire_vignette",
                            lambda *a, **k: vues.append(1) or (None, ""))
        vision.lire_vignettes(ctx)
        assert len(vues) <= 1, "seule la scène sans studio est lue"

    def test_collection_vide_ne_leve_pas(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)

    def test_sans_modele_ne_leve_pas(self):
        _st, ctx = self._monde()
        vision.lire_vignettes(ctx)

    def test_le_resultat_est_une_proposition(self, monkeypatch):
        """Une lecture n'écrit jamais directement : elle propose, et
        sa provenance dit d'où elle vient."""
        st, ctx = self._monde()
        monkeypatch.setattr(
            vision, "lire_vignette",
            lambda *a, **k: ({"studio": "Masqulin",
                              "texte_lu": ["MASQULIN"]},
                             "filigrane lu"))
        vision.lire_vignettes(ctx)
        assert not st.scenes["10"].get("studio"), \
            "la scène ne doit pas être modifiée d'autorité"

    def test_simulation(self, monkeypatch):
        import noyau
        st, ctx = self._monde()
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        monkeypatch.setattr(
            vision, "lire_vignette",
            lambda *a, **k: ({"studio": "Masqulin",
                              "texte_lu": ["MASQULIN"]}, "lu"))
        vision.lire_vignettes(ctx)
        assert not st.scenes["10"].get("studio")


# ── Fiabilité déclarée ───────────────────────────────────────────────
class TestFiabilite:
    """Une lecture de filigrane n'est pas un annuaire. Sa note doit le
    dire, sans quoi elle pèserait autant qu'une source documentaire
    dans l'arbitrage."""

    def test_la_source_est_declaree_faible(self):
        import scoring
        poids = scoring.DEFAUTS.get("fiabilites", {})
        vision_poids = poids.get("vision")
        if vision_poids is None:
            pytest.skip("fiabilité de la vision non déclarée")
        for annuaire in ("iafd", "stashdb.org"):
            if annuaire in poids:
                assert vision_poids < poids[annuaire]

    def test_la_source_est_nommee_distinctement(self):
        """Dans la trace de provenance, une lecture doit se distinguer
        d'une réponse de source."""
        assert vision.NOM_SOURCE.startswith("vision")


# ── Consentement ─────────────────────────────────────────────────────
class TestConsentement:
    """Lire une vignette, c'est envoyer l'image d'une personne réelle à
    un tiers. Ce n'est pas une question technique.

    Le reste du plugin transmet du TEXTE — des noms, des dates. Une
    image est d'une autre nature : elle est identifiante, elle peut
    être conservée par le fournisseur, et elle expose des gens qui
    n'ont rien demandé. La fonctionnalité est donc éteinte par défaut,
    et son activation doit être un geste conscient."""

    def test_eteinte_par_defaut(self):
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral"}, st)
        ctx.args = {}
        assert not vision.autorisee(ctx)

    def test_un_modele_configure_ne_suffit_pas(self):
        """Renseigner un modèle de vision n'est pas consentir à
        envoyer des images : les deux réglages sont distincts."""
        ctx = faux_contexte({"aiVision": "mistral:pixtral"},
                            FauxStash())
        assert not vision.autorisee(ctx)

    def test_le_reglage_dedie_l_autorise(self):
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "visionEnvoiImages": True}, FauxStash())
        assert vision.autorisee(ctx)

    def test_sans_autorisation_aucun_appel(self, monkeypatch):
        appels = []
        monkeypatch.setattr(vision, "_appel_vision",
                            lambda *a, **k: appels.append(1) or None)
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral"}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)
        assert appels == []

    def test_un_modele_local_reste_soumis_au_reglage(self):
        """Même vers un modèle installé chez soi, l'envoi doit être
        voulu : l'utilisateur peut vouloir qu'aucune image ne quitte
        Stash, quel qu'en soit le destinataire."""
        ctx = faux_contexte({"aiVision": "ollama:llava"}, FauxStash())
        assert not vision.autorisee(ctx)

    def test_la_destination_est_annoncee(self, monkeypatch):
        """L'utilisateur doit savoir OÙ partent ses images avant que
        la première ne parte."""
        messages = []
        monkeypatch.setattr(vision.log, "info",
                            lambda m, *a, **k: messages.append(str(m)))
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "llmApiKey": "essai",
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)
        assert any("mistral" in m.lower() for m in messages)


# ── Coût ─────────────────────────────────────────────────────────────
class TestCout:
    """Un appel de vision coûte plusieurs fois un appel de texte. Une
    tâche lancée sans limite sur une collection entière produit une
    facture que personne n'a vue venir."""

    def _monde(self, combien):
        st = FauxStash(scenes=[scene(10 + i, f"Scène {i}")
                               for i in range(combien)])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "visionEnvoiImages": True,
                             "batchSize": "3"}, st)
        ctx.args = {}
        return st, ctx

    def test_le_lot_est_respecte(self, monkeypatch):
        appels = []
        monkeypatch.setattr(
            vision, "lire_vignette",
            lambda *a, **k: appels.append(1) or (None, "rien"))
        _st, ctx = self._monde(10)
        vision.lire_vignettes(ctx)
        assert len(appels) <= 3

    def test_une_scene_deja_lue_n_est_pas_relue(self, monkeypatch):
        """Relire la même vignette produit la même réponse et la même
        facture. La trace de lecture évite de repayer."""
        appels = []
        monkeypatch.setattr(
            vision, "lire_vignette",
            lambda *a, **k: appels.append(1) or (None, "rien"))
        st = FauxStash(scenes=[scene(
            10, "Déjà lue",
            custom_fields={"enrich_vision": "2026-08-07"})])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)
        assert appels == []

    def test_une_relecture_peut_etre_demandee(self, monkeypatch):
        appels = []
        monkeypatch.setattr(
            vision, "lire_vignette",
            lambda *a, **k: appels.append(1) or (None, "rien"))
        st = FauxStash(scenes=[scene(
            10, "Déjà lue",
            paths={"screenshot": "https://exemple.test/v.jpg"},
            custom_fields={"enrich_vision": "2026-08-07"})])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "llmApiKey": "essai",
                             "visionEnvoiImages": True}, st)
        ctx.args = {"relire": "1"}
        # La vignette doit être récupérable, sinon la scène est
        # écartée avant même la question de la relecture.
        monkeypatch.setattr(vision, "image_de",
                            lambda *a, **k: b"image")
        vision.lire_vignettes(ctx)
        assert appels == [1]


# ── Provenance de l'image ────────────────────────────────────────────
class TestImage:
    """L'image vient de Stash, par une adresse que Stash fournit. Une
    adresse non contrôlée ferait de cette tâche un moyen de faire
    interroger n'importe quoi au plugin."""

    def test_l_adresse_de_l_image_est_controlee(self, monkeypatch):
        """Même venue de Stash, elle passe par le contrôle commun :
        une base compromise ne doit pas faire sortir le plugin."""
        st = FauxStash(scenes=[scene(
            10, "Sans studio",
            paths={"screenshot": "file:///etc/passwd"})])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        assert vision.image_de(ctx, st.scenes["10"]) is None

    def test_une_scene_sans_image_est_ignoree(self):
        st = FauxStash(scenes=[scene(10, "Sans image")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        assert vision.image_de(ctx, st.scenes["10"]) is None

    def test_l_image_est_transmise_encodee(self, monkeypatch):
        """Les API de vision attendent du base64, non des octets
        bruts : une image mal encodée est refusée sans explication."""
        recu = {}

        def capter(url, corps, cle=None):
            recu.update(corps)
            return json.dumps({"choices": [{"message":
                                            {"content": "{}"}}]})
        monkeypatch.setattr(vision, "_poster", capter)
        ctx = _ctx()
        vision._appel_vision(ctx, b"\x89PNG\r\n", "instructions")
        texte = json.dumps(recu)
        assert "base64" in texte or "data:image" in texte


# ── Ce qui est journalisé ────────────────────────────────────────────
class TestJournal:
    """Le texte lu sur une vignette peut contenir n'importe quoi — un
    nom, une adresse. Le journal du serveur est lisible par d'autres."""

    def test_le_texte_lu_n_est_pas_journalise_en_entier(self, monkeypatch):
        messages = []
        monkeypatch.setattr(vision.log, "info",
                            lambda m, *a, **k: messages.append(str(m)))
        _repond(monkeypatch, json.dumps({
            "studio": "Masqulin",
            "texte_lu": ["MASQULIN.COM", "Un Nom Qui Traine"],
            "confiance": 0.9}))
        vision.lire_vignette(_ctx(), b"image")
        assert not any("Un Nom Qui Traine" in m for m in messages)
