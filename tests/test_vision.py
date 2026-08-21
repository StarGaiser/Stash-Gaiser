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
            "llmApiKey": "essai", "visionEnvoiImages": True,
            "sourceVision": True}
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
                             "visionEnvoiImages": True,
            "sourceVision": True}, FauxStash())
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
                             "sourceVision": True,
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
                             "visionEnvoiImages": True,
            "sourceVision": True}, st)
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
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {"relire": "1"}
        # La vignette doit être récupérable, sinon la scène est
        # écartée avant même la question de la relecture.
        # L'image doit être EXPLOITABLE : quelques octets ne passent
        # plus le contrôle qui écarte les icônes de remplacement.
        monkeypatch.setattr(
            vision, "image_de",
            lambda *a, **k: b"\xff\xd8\xff\xe0" + b"x" * 40000)
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
                             "visionEnvoiImages": True,
            "sourceVision": True}, st)
        ctx.args = {}
        assert vision.image_de(ctx, st.scenes["10"]) is None

    def test_une_scene_sans_image_est_ignoree(self):
        st = FauxStash(scenes=[scene(10, "Sans image")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral",
                             "visionEnvoiImages": True,
            "sourceVision": True}, st)
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


# ── Capacité des fournisseurs ────────────────────────────────────────
class TestCapaciteVision:
    """Tous les fournisseurs ne lisent pas les images, et tous leurs
    modèles non plus. Régler « aiVision » sur un modèle de texte
    échoue de façon obscure : l'appel part, le fournisseur refuse, et
    rien n'explique pourquoi.

    Le remède n'est PAS de séparer les réglages : la clé et l'adresse
    sont celles du même compte, et les dupliquer garantit qu'une des
    deux copies deviendra périmée. C'est la CAPACITÉ qui manque à la
    table, pas un second jeu d'identifiants."""

    def test_la_capacite_est_declaree(self):
        import llm
        table = llm.charger("gaizer")
        avec = [n for n, c in table.items() if c.get("vision")]
        assert avec, "aucun fournisseur ne déclare savoir lire une image"

    def test_les_modeles_de_vision_sont_suggeres(self):
        """Un utilisateur qui a déjà renseigné sa clé doit pouvoir
        choisir sans aller chercher la documentation du fournisseur."""
        import llm
        table = llm.charger("gaizer")
        for nom, conf in table.items():
            if conf.get("vision"):
                assert conf.get("vision_model"), nom

    def test_un_fournisseur_sans_vision_est_signale(self):
        ctx = _ctx(aiVision="unfournisseursansvision:x")
        assert not vision.fournisseur_convient(ctx)

    def test_un_fournisseur_avec_vision_convient(self):
        ctx = _ctx(aiVision="mistral:pixtral-12b")
        assert vision.fournisseur_convient(ctx)

    def test_les_fournisseurs_disponibles_sont_listes(self):
        """La suggestion s'appuie sur les clés DÉJÀ renseignées : la
        proposer sans en tenir compte enverrait vers un fournisseur
        qu'on ne peut pas appeler."""
        ctx = _ctx(mistralApiKey="essai")
        proposes = vision.fournisseurs_possibles(ctx)
        assert any(p.startswith("mistral") for p in proposes)

    def test_aucune_suggestion_sans_cle(self):
        ctx = faux_contexte({"language": "fr"}, FauxStash())
        proposes = vision.fournisseurs_possibles(ctx)
        assert all(":" in p for p in proposes)

    def test_les_services_locaux_sont_proposes_sans_cle(self):
        """Ollama et LM Studio n'en réclament aucune : les exclure
        faute de clé priverait de la seule option qui ne transmet
        rien à un tiers."""
        ctx = faux_contexte({"language": "fr", "ollamaUrl":
                             "http://192.168.1.10:11434"}, FauxStash())
        proposes = vision.fournisseurs_possibles(ctx)
        assert any("ollama" in p for p in proposes)

    def test_la_tache_suggere_quand_le_reglage_manque(self, monkeypatch):
        messages = []
        monkeypatch.setattr(vision.log, "info",
                            lambda m, *a, **k: messages.append(str(m)))
        monkeypatch.setattr(vision.log, "warning",
                            lambda m, *a, **k: messages.append(str(m)))
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"language": "fr", "mistralApiKey": "x",
                             "visionEnvoiImages": True,
            "sourceVision": True}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)
        assert any("pixtral" in m.lower() for m in messages), \
            "la tâche doit proposer un modèle exploitable"


class TestAdresseDeStash:
    """L'image vient de Stash, qui se sert lui-même sur une adresse
    locale. Le contrôle qui protège des sources EXTERNES la refuse — à
    juste titre pour une source tierce, à tort pour l'hôte auquel le
    plugin est déjà connecté.

    La distinction n'est pas une exception de confort : une adresse
    fournie par une source distante reste refusée. Seule celle de la
    connexion établie au démarrage est admise, et elle seule."""

    def _ctx_stash(self, hote="127.0.0.1", port=9999):
        ctx = _ctx()
        ctx.connexion = {"Scheme": "http", "Host": hote, "Port": port}
        return ctx

    def test_l_adresse_de_stash_est_admise(self):
        ctx = self._ctx_stash()
        assert vision.adresse_de_stash(
            ctx, "http://127.0.0.1:9999/scene/1/screenshot")

    def test_une_autre_adresse_locale_est_refusee(self):
        """Un port voisin n'est pas Stash : ce serait un moyen
        d'atteindre un autre service de la machine."""
        ctx = self._ctx_stash()
        for url in ("http://127.0.0.1:8080/x",
                    "http://192.168.1.10:9999/x",
                    "http://localhost:22/x"):
            assert not vision.adresse_de_stash(ctx, url), url

    def test_une_adresse_publique_reste_admise(self):
        """Les vignettes peuvent être servies par un domaine si Stash
        est derrière un proxy."""
        ctx = self._ctx_stash()
        assert vision.adresse_de_stash(
            ctx, "https://exemple-public.test/scene/1/screenshot")

    def test_un_fichier_local_reste_refuse(self):
        ctx = self._ctx_stash()
        for url in ("file:///etc/passwd", "ftp://x.test/y", ""):
            assert not vision.adresse_de_stash(ctx, url), url

    def test_la_vignette_de_stash_est_recuperee(self, monkeypatch):
        st = FauxStash(scenes=[scene(
            10, "Une scène",
            paths={"screenshot":
                   "http://127.0.0.1:9999/scene/10/screenshot"})])
        ctx = _ctx()
        ctx.stash = st
        ctx.connexion = {"Scheme": "http", "Host": "127.0.0.1",
                         "Port": 9999}
        monkeypatch.setattr(vision, "_telecharger",
                            lambda url, **k: b"image")
        assert vision.image_de(ctx, st.scenes["10"]) == b"image"


class TestImageExploitable:
    """Stash sert une ICÔNE DE REMPLACEMENT — un SVG de quelques
    centaines d'octets — quand une scène n'a pas de vignette générée.
    L'envoyer au modèle coûte un appel, produit une erreur du
    fournisseur, et n'apprend rien.

    Le cas n'est pas marginal : sur une collection dont les vignettes
    n'ont pas toutes été produites, il concerne la grande majorité des
    scènes non identifiées — précisément celles que cette tâche vise."""

    def test_un_svg_est_ecarte(self):
        for faux in (b'<svg xmlns="http://www.w3.org/2000/svg">',
                     b'<?xml version="1.0"?><svg>',
                     b'   <svg viewBox="0 0 1 1"/>'):
            assert not vision.image_exploitable(faux), faux[:20]

    def test_une_image_trop_petite_est_ecartee(self):
        """Quelques centaines d'octets ne portent aucun filigrane
        lisible."""
        assert not vision.image_exploitable(b"\xff\xd8\xff" + b"x" * 400)

    def test_une_vraie_image_est_acceptee(self):
        assert vision.image_exploitable(b"\xff\xd8\xff\xe0" + b"x" * 40000)
        assert vision.image_exploitable(b"\x89PNG\r\n\x1a\n" + b"x" * 40000)

    def test_valeurs_vides(self):
        for brut in (None, b"", b"x"):
            assert not vision.image_exploitable(brut)

    def test_la_tache_ne_paie_pas_pour_une_icone(self, monkeypatch):
        """Le contrôle doit intervenir AVANT l'appel : après, la
        facture est déjà due."""
        appels = []
        monkeypatch.setattr(vision, "_appel_vision",
                            lambda *a, **k: appels.append(1) or None)
        monkeypatch.setattr(vision, "image_de",
                            lambda *a, **k: b'<svg xmlns="x"/>')
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)
        assert appels == []

    def test_le_motif_dit_qu_il_manque_une_vignette(self, monkeypatch):
        """L'utilisateur doit comprendre qu'il lui faut GÉNÉRER ses
        vignettes, non que le plugin ou le modèle a échoué."""
        messages = []
        monkeypatch.setattr(vision.log, "info",
                            lambda m, *a, **k: messages.append(str(m)))
        monkeypatch.setattr(vision, "image_de",
                            lambda *a, **k: b'<svg xmlns="x"/>')
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        vision.lire_vignettes(ctx)
        joint = " ".join(messages).lower()
        assert "vignette" in joint and ("générer" in joint
                                        or "generate" in joint)


class TestVoisinage:
    """Un filigrane dit « MASQULIN.COM » là où le catalogue dit
    « Masqulin », ou « TREASURE ISLAND MEDIA » pour « Treasure
    Island ». Rapprocher automatiquement serait dangereux — « Falcon »
    et « Falcon Studios » peuvent être deux entités.

    Mais taire la proximité fait passer pour inconnu ce que
    l'utilisateur reconnaîtrait d'un coup d'œil. Le voisin est donc
    SIGNALÉ, jamais appliqué."""

    STUDIOS = MappingProxyType({"treasure island": "72",
                                "masqulin": "1",
                                "falcon studios": "2"})

    def test_un_voisin_est_signale(self):
        voisin = vision.voisin_probable("TREASURE ISLAND MEDIA",
                                        self.STUDIOS)
        assert voisin == "72"

    def test_le_voisin_n_est_pas_un_rapprochement(self):
        """Les deux fonctions ne doivent pas se confondre : l'une
        décide, l'autre suggère."""
        assert vision.rapprocher_studio("TREASURE ISLAND MEDIA",
                                        self.STUDIOS) is None

    def test_un_prefixe_seul_ne_suffit_pas(self):
        """« Falcon » ne doit pas suggérer « Falcon Studios » : le
        fragment est trop court pour distinguer."""
        assert vision.voisin_probable("Falcon", self.STUDIOS) is None

    def test_un_nom_sans_rapport(self):
        assert vision.voisin_probable("Autre Chose", self.STUDIOS) is None

    def test_valeurs_vides(self):
        for lu in ("", None, "ab"):
            assert vision.voisin_probable(lu, self.STUDIOS) is None


class TestAppelReel:
    """Le chemin d'appel lui-même : construction de la requête,
    lecture de la réponse, gestion des pannes. Non couvert tant qu'on
    ne remplace que `_appel_vision`, alors que c'est là que se trouve
    ce qui part réellement sur le réseau."""

    def _conf(self, monkeypatch, reponse=None, erreur=None):
        def poster(url, corps, cle=None):
            if erreur:
                raise erreur
            return reponse or json.dumps(
                {"choices": [{"message": {"content": "{}"}}]})
        monkeypatch.setattr(vision, "_poster", poster)

    def test_la_reponse_est_extraite(self, monkeypatch):
        self._conf(monkeypatch, json.dumps(
            {"choices": [{"message": {"content": "du texte"}}]}))
        assert vision._appel_vision(_ctx(), b"img", "x") == "du texte"

    def test_une_panne_reseau_ne_leve_pas(self, monkeypatch):
        """Une tâche de lot ne doit pas s'interrompre sur une scène."""
        self._conf(monkeypatch, erreur=OSError("réseau coupé"))
        assert vision._appel_vision(_ctx(), b"img", "x") is None

    def test_une_reponse_malformee_ne_leve_pas(self, monkeypatch):
        for brut in ("{}", "pas du json", '{"choices": []}'):
            self._conf(monkeypatch, brut)
            assert vision._appel_vision(_ctx(), b"img", "x") is None

    def test_sans_fournisseur_connu(self, monkeypatch):
        ctx = _ctx(aiVision="inconnu:x")
        assert vision._appel_vision(ctx, b"img", "x") is None

    def test_l_adresse_du_service_est_controlee(self, monkeypatch):
        """Elle vient d'un fichier éditable : un « file:// » y ferait
        lire un fichier local."""
        with pytest.raises(ValueError):
            vision._poster("file:///etc/passwd", {})

    def test_la_cle_est_transmise_en_entete(self, monkeypatch):
        """Une clé placée dans le corps ou l'adresse fuirait dans les
        journaux du fournisseur."""
        vu = {}

        class FausseReponse:
            def read(self):
                return b"{}"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def faux_urlopen(requete, timeout=None):
            vu["entetes"] = dict(requete.headers)
            vu["url"] = requete.full_url
            return FausseReponse()
        import urllib.request
        monkeypatch.setattr(urllib.request, "urlopen", faux_urlopen)
        vision._poster("https://exemple-public.test/v1", {"a": 1},
                       cle="secret-123")
        assert "secret-123" not in vu["url"]
        assert any("secret-123" in str(v)
                   for v in vu["entetes"].values())


class TestTacheDeBout:
    """La tâche complète, avec un modèle qui répond vraiment."""

    def _monde(self, monkeypatch, reponse):
        st = FauxStash(
            scenes=[scene(10, "Sans studio",
                          paths={"screenshot":
                                 "https://exemple.test/v.jpg"})],
            studios=[studio(1, "Masqulin")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True,
                             "batchSize": "5"}, st)
        ctx.args = {}
        monkeypatch.setattr(
            vision, "image_de",
            lambda *a, **k: b"\xff\xd8\xff\xe0" + b"x" * 40000)
        monkeypatch.setattr(vision, "_appel_vision",
                            lambda *a, **k: reponse)
        return st, ctx

    def test_un_studio_connu_est_propose(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, json.dumps(
            {"studio": "Masqulin", "texte_lu": ["MASQULIN.COM"],
             "confiance": 0.9}))
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        d = json.loads(cf.get("enrich_vision_studio") or "{}")
        assert d.get("studio_id") == "1" and d.get("certain")

    def test_un_studio_inconnu_est_consigne_sans_lien(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, json.dumps(
            {"studio": "Studio Inconnu", "texte_lu": ["STUDIO INCONNU"],
             "confiance": 0.9}))
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        d = json.loads(cf.get("enrich_vision_studio") or "{}")
        assert d.get("studio_lu") == "Studio Inconnu"
        assert not d.get("studio_id")

    def test_une_vignette_sans_texte_marque_la_scene(self, monkeypatch):
        """Sans marque, la scène serait relue au passage suivant et
        repaierait le même appel pour le même résultat.

        Le modèle doit avoir RÉPONDU : une réponse illisible est un
        incident, pas un constat d'absence."""
        st, ctx = self._monde(monkeypatch, json.dumps(
            {"studio": None, "texte_lu": [], "confiance": 0.0}))
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        assert cf.get("enrich_vision")

    def test_le_studio_de_la_scene_reste_vide(self, monkeypatch):
        st, ctx = self._monde(monkeypatch, json.dumps(
            {"studio": "Masqulin", "texte_lu": ["MASQULIN"],
             "confiance": 0.95}))
        vision.lire_vignettes(ctx)
        assert not (st.scenes["10"].get("studio") or {}).get("id")


class TestReponseEncadree:
    """Les modèles encadrent presque toujours leur JSON d'un bloc de
    code Markdown. C'est le comportement NORMAL, pas une déviance :
    ne pas le prévoir fait échouer la lecture sur des réponses
    parfaitement valides."""

    def test_un_bloc_de_code_est_traverse(self, monkeypatch):
        _repond(monkeypatch, '```json\n'
                '{"studio": "Masqulin", "texte_lu": ["MASQULIN.COM"], '
                '"confiance": 1.0}\n```')
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu and lu.get("studio") == "Masqulin"

    def test_un_bloc_sans_langue(self, monkeypatch):
        _repond(monkeypatch, '```\n{"studio": "Masqulin", '
                '"texte_lu": ["MASQULIN"], "confiance": 0.9}\n```')
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu

    def test_du_texte_avant_et_apres(self, monkeypatch):
        _repond(monkeypatch, 'Voici ce que je lis :\n```json\n'
                '{"studio": "Masqulin", "texte_lu": ["MASQULIN"], '
                '"confiance": 0.9}\n```\nJ\'espère que cela aide.')
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu


class TestPortee:
    """La tâche ne traite que les scènes sans studio. Mais une scène
    LUE reste sans studio tant que sa proposition n'est pas arbitrée :
    sans distinction, les passages suivants butent indéfiniment sur
    les mêmes, et n'atteignent jamais les autres."""

    def _monde(self, combien=6, marquees=3):
        scenes = []
        for i in range(combien):
            cf = ({"enrich_vision": "2026-08-08"} if i < marquees
                  else {})
            scenes.append(scene(10 + i, f"Scène {i}", custom_fields=cf))
        st = FauxStash(scenes=scenes)
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True,
                             "batchSize": "10"}, st)
        ctx.args = {}
        return st, ctx

    def test_les_scenes_deja_lues_sont_ecartees(self, monkeypatch):
        vues = []
        monkeypatch.setattr(
            vision, "image_de",
            lambda ctx, sc: vues.append(sc["id"]) or (
                b"\xff\xd8\xff\xe0" + b"x" * 40000))
        monkeypatch.setattr(vision, "_appel_vision",
                            lambda *a, **k: None)
        _st, ctx = self._monde()
        vision.lire_vignettes(ctx)
        assert len(vues) == 3, "seules les non lues doivent être vues"

    def test_le_compte_annonce_ce_qui_reste_a_lire(self, monkeypatch):
        """Annoncer un total de scènes sans studio quand certaines sont déjà lues
        laisse croire qu'aucune n'a été traitée."""
        messages = []
        monkeypatch.setattr(vision.log, "info",
                            lambda m, *a, **k: messages.append(str(m)))
        monkeypatch.setattr(vision, "image_de", lambda *a, **k: None)
        _st, ctx = self._monde(combien=6, marquees=4)
        vision.lire_vignettes(ctx)
        joint = " ".join(messages)
        assert "2 " in joint or " 2\u00a0" in joint, joint[:200]


class TestPanneEtLectureSansNom:
    """Deux confusions coûteuses, constatées en service.

    Une PANNE RÉSEAU n'est pas une absence de filigrane. Les confondre
    marque la scène comme lue, et elle n'est jamais reprise — une
    coupure d'une minute condamne définitivement tout un lot.

    Et un modèle qui LIT un texte sans oser en tirer un nom de studio a
    quand même fait son travail : « texte_lu: [HAROKINKS.COM] » avec
    « studio: null » contient la réponse. La jeter revient à payer un
    appel pour rien."""

    def test_une_panne_ne_marque_pas_la_scene(self, monkeypatch):
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        monkeypatch.setattr(
            vision, "image_de",
            lambda *a, **k: b"\xff\xd8\xff\xe0" + b"x" * 40000)
        monkeypatch.setattr(vision, "_appel_vision",
                            lambda *a, **k: None)
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        assert not cf.get("enrich_vision"), \
            "une panne ne doit pas condamner la scène"

    def test_une_absence_de_texte_marque_la_scene(self, monkeypatch):
        """En revanche, une vignette sans filigrane n'en aura jamais :
        la relire coûterait un appel pour le même résultat."""
        st = FauxStash(scenes=[scene(10, "Sans studio")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        monkeypatch.setattr(
            vision, "image_de",
            lambda *a, **k: b"\xff\xd8\xff\xe0" + b"x" * 40000)
        monkeypatch.setattr(vision, "_appel_vision", lambda *a, **k:
                            '{"studio": null, "texte_lu": [], '
                            '"confiance": 0}')
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        assert cf.get("enrich_vision")

    def test_un_texte_lu_sans_nom_est_exploite(self, monkeypatch):
        """Le modèle lit « HAROKINKS.COM » mais laisse studio à null.
        Le texte lu EST la réponse."""
        _repond(monkeypatch, '{"studio": null, '
                '"texte_lu": ["HAROKINKS.COM"], "confiance": 1.0}')
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu and lu.get("studio")
        assert "harokinks" in lu["studio"].lower()

    def test_seule_une_adresse_ou_un_nom_est_retenu(self, monkeypatch):
        """Du texte quelconque lu sur l'image n'est pas un studio."""
        _repond(monkeypatch, '{"studio": null, '
                '"texte_lu": ["Scene 4", "HD", "2023"], '
                '"confiance": 1.0}')
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu is None

    def test_une_adresse_est_reconnue_comme_studio(self, monkeypatch):
        _repond(monkeypatch, '{"studio": null, '
                '"texte_lu": ["www.masqulin.com"], "confiance": 0.9}')
        lu, _motif = vision.lire_vignette(_ctx(), b"image")
        assert lu and "masqulin" in lu["studio"].lower()

    def test_le_motif_distingue_panne_et_absence(self, monkeypatch):
        _repond(monkeypatch, None)
        _lu, motif = vision.lire_vignette(_ctx(), b"image")
        assert "réponse" in motif.lower() or "panne" in motif.lower()


class TestErreurDeLecture:
    """Un filigrane se lit mal : « HARDKINKS » revient tantôt
    « HAROKINKS », tantôt « HARDINKS ». Un D pris pour un O, une
    lettre avalée — la reconnaissance de caractères se trompe, et
    refuser ces variantes fait perdre des scènes que l'utilisateur
    reconnaîtrait d'un coup d'œil.

    Le rapprochement EXACT reste la règle pour ce qui est appliqué.
    Ceci est une troisième source, entre l'exact et le voisinage : une
    correspondance à un caractère près, SIGNALÉE comme incertaine."""

    STUDIOS = MappingProxyType({"hardkinks": "9", "masqulin": "1",
                                "men com": "3", "falcon studios": "2"})

    def test_une_lettre_fausse_est_rattrapee(self):
        for lu in ("HAROKINKS", "HARDINKS", "HARDKINK5"):
            assert vision.malgre_erreur_de_lecture(
                lu, self.STUDIOS) == "9", lu

    def test_deux_lettres_fausses_ne_le_sont_pas(self):
        """Au-delà d'un caractère, ce n'est plus une erreur de lecture
        mais un autre nom."""
        assert vision.malgre_erreur_de_lecture(
            "HAROKINGS2", self.STUDIOS) is None

    def test_un_nom_court_n_est_jamais_rattrape(self):
        """Sur quatre lettres, un caractère de différence change
        complètement le mot : « MEN » et « MAN » ne sont pas la même
        erreur qu'un nom long."""
        assert vision.malgre_erreur_de_lecture("MAN", self.STUDIOS) \
            is None

    def test_deux_studios_egalement_proches_sont_refuses(self):
        """Si l'erreur peut désigner deux studios, on ne choisit
        pas."""
        index = MappingProxyType({"studio a": "1", "studio b": "2"})
        assert vision.malgre_erreur_de_lecture("studio c", index) \
            is None

    def test_un_nom_exact_n_est_pas_traite_ici(self):
        """Les fonctions ne se recouvrent pas : l'exacte décide,
        celle-ci suggère."""
        assert vision.rapprocher_studio("HARDKINKS", self.STUDIOS) \
            == "9"

    def test_valeurs_vides(self):
        for lu in ("", None, "ab"):
            assert vision.malgre_erreur_de_lecture(
                lu, self.STUDIOS) is None

    def test_le_rattrapage_est_marque_incertain(self, monkeypatch):
        """Une lecture rattrapée ne vaut pas une lecture exacte :
        l'utilisateur doit voir la différence avant d'appliquer."""
        st = FauxStash(
            scenes=[scene(10, "Sans studio")],
            studios=[studio(9, "HardKinks")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        monkeypatch.setattr(
            vision, "image_de",
            lambda *a, **k: b"\xff\xd8\xff\xe0" + b"x" * 40000)
        monkeypatch.setattr(vision, "_appel_vision", lambda *a, **k:
                            '{"studio": "HAROKINKS", '
                            '"texte_lu": ["HAROKINKS.COM"], '
                            '"confiance": 1.0}')
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        d = json.loads(cf.get("enrich_vision_studio") or "{}")
        assert d.get("studio_id") == "9"
        assert not d.get("certain"), \
            "un rattrapage n'est pas une correspondance"


class TestRapprochementParUrl:
    """Un filigrane EST souvent une adresse : « HARDKINKS.COM ». Or la
    plupart des studios en portent une dans leur fiche.

    C'est le rapprochement le plus fiable qui soit — plus qu'un nom,
    qui s'écrit de dix façons. Une adresse est unique et ne souffre
    pas d'orthographe : deux studios ne partagent pas un domaine.

    Il doit donc être tenté AVANT le rapprochement par nom, et compter
    comme certain."""

    STUDIOS = (
        {"id": "9", "name": "Hard Kinks",
         "url": "https://hardkinks.com/"},
        {"id": "1", "name": "Masqulin",
         "url": "https://www.masqulin.com"},
        {"id": "2", "name": "Falcon Studios", "url": None},
    )

    def test_une_adresse_lue_designe_son_studio(self):
        assert vision.par_adresse("HARDKINKS.COM", self.STUDIOS) == "9"

    def test_le_prefixe_www_est_ignore(self):
        for lu in ("MASQULIN.COM", "www.masqulin.com",
                   "https://masqulin.com/scene/4"):
            assert vision.par_adresse(lu, self.STUDIOS) == "1", lu

    def test_un_domaine_inconnu_ne_rapproche_rien(self):
        assert vision.par_adresse("AUTRECHOSE.COM",
                                  self.STUDIOS) is None

    def test_un_studio_sans_adresse_n_est_pas_atteint(self):
        assert vision.par_adresse("FALCONSTUDIOS.COM",
                                  self.STUDIOS) is None

    def test_un_texte_qui_n_est_pas_une_adresse(self):
        for lu in ("HARDKINKS", "Scene 4", "", None):
            assert vision.par_adresse(lu, self.STUDIOS) is None

    def test_l_adresse_prime_sur_le_nom(self, monkeypatch):
        """Une adresse lue vaut mieux qu'un nom mal orthographié :
        elle est exacte là où le nom est approximatif."""
        st = FauxStash(
            scenes=[scene(10, "Sans studio")],
            studios=[studio(9, "Hard Kinks",
                            url="https://hardkinks.com/")])
        ctx = faux_contexte({"aiVision": "mistral:pixtral-12b",
                             "llmApiKey": "essai",
                             "sourceVision": True,
                             "visionEnvoiImages": True}, st)
        ctx.args = {}
        monkeypatch.setattr(
            vision, "image_de",
            lambda *a, **k: b"\xff\xd8\xff\xe0" + b"x" * 40000)
        monkeypatch.setattr(vision, "_appel_vision", lambda *a, **k:
                            '{"studio": "HAROKINKS", '
                            '"texte_lu": ["HAROKINKS.COM"], '
                            '"confiance": 1.0}')
        vision.lire_vignettes(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        d = json.loads(cf.get("enrich_vision_studio") or "{}")
        assert d.get("studio_id") == "9"


class TestRapprochementParAlias:
    """Un studio porte souvent ses variantes d'écriture en alias :
    « bear films » pour « BearFilms ». Les ignorer fait rejeter une
    lecture correcte."""

    def test_un_alias_designe_le_studio(self):
        studios = ({"id": "5", "name": "BearFilms",
                    "aliases": ["bear films", "Bear Films Inc"]},)
        assert vision.par_alias("BEAR FILMS", studios) == "5"

    def test_la_casse_et_les_espaces_sont_ignores(self):
        studios = ({"id": "5", "name": "BearFilms",
                    "aliases": ["bear films"]},)
        for lu in ("bearfilms", "BEAR  FILMS", "Bear-Films"):
            assert vision.par_alias(lu, studios) == "5", lu

    def test_un_alias_corrompu_est_ignore(self):
        """Des alias réduits à une lettre viennent d'un import ou
        d'un défaut : les employer rapprocherait n'importe quoi."""
        studios = ({"id": "6", "name": "Bound In Public",
                    "aliases": [".", "b", "c", "d", "i"]},)
        for lu in ("BOUND", "D", "c"):
            assert vision.par_alias(lu, studios) is None, lu

    def test_aucun_alias(self):
        assert vision.par_alias("X", ({"id": "1", "name": "Y"},)) \
            is None


class TestApplicationDesPropositions:
    """Une proposition de vision se consigne dans un champ, et rien ne
    la reprend jamais : l'utilisateur voit « TREASURE ISLAND MEDIA »
    rapproché d'un studio de son catalogue, et la scène reste sans
    studio.

    C'est un cul-de-sac — le même défaut que les propositions
    d'enrichissement sans tâche pour les appliquer. Une source qui
    propose doit avoir sa source qui applique."""

    def _monde(self, proposition, **reglages):
        st = FauxStash(
            scenes=[scene(10, "Sans studio", custom_fields={
                "enrich_vision_studio": json.dumps(proposition)})],
            studios=[studio(9, "Treasure Island")])
        base = {"applyMode": "auto", "sourceVision": True}
        base.update(reglages)
        ctx = faux_contexte(base, st)
        ctx.args = {}
        return st, ctx

    def test_une_proposition_certaine_est_appliquee(self):
        st, ctx = self._monde({"studio_lu": "TREASURE ISLAND MEDIA",
                               "studio_id": "9", "certain": True,
                               "confiance": 1.0})
        vision.appliquer_vision(ctx)
        assert (st.scenes["10"].get("studio") or {}).get("id") == "9"

    def test_une_proposition_incertaine_est_laissee(self):
        """Un rattrapage d'erreur de lecture demande un regard :
        l'appliquer d'office reviendrait à effacer la distinction
        entre certain et probable."""
        st, ctx = self._monde({"studio_lu": "HAROKINKS",
                               "studio_id": "9", "certain": False,
                               "confiance": 1.0})
        vision.appliquer_vision(ctx)
        assert not st.scenes["10"].get("studio")

    def test_une_proposition_incertaine_peut_etre_forcee(self):
        st, ctx = self._monde({"studio_lu": "HAROKINKS",
                               "studio_id": "9", "certain": False,
                               "confiance": 1.0})
        ctx.args = {"incertaines": "1"}
        vision.appliquer_vision(ctx)
        assert (st.scenes["10"].get("studio") or {}).get("id") == "9"

    def test_une_proposition_sans_studio_connu_est_ignoree(self):
        st, ctx = self._monde({"studio_lu": "STUDIO INCONNU",
                               "studio_id": None, "certain": False})
        vision.appliquer_vision(ctx)
        assert not st.scenes["10"].get("studio")

    def test_un_studio_existant_n_est_pas_ecrase(self):
        st, ctx = self._monde({"studio_lu": "TREASURE ISLAND MEDIA",
                               "studio_id": "9", "certain": True})
        st.scenes["10"]["studio"] = {"id": "99"}
        vision.appliquer_vision(ctx)
        assert st.scenes["10"]["studio"]["id"] == "99"

    def test_la_provenance_dit_que_c_est_une_lecture(self):
        st, ctx = self._monde({"studio_lu": "TREASURE ISLAND MEDIA",
                               "studio_id": "9", "certain": True})
        vision.appliquer_vision(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        assert "vision" in str(cf.get("enrich_sources") or "").lower()

    def test_simulation(self):
        import noyau
        st, ctx = self._monde({"studio_lu": "X", "studio_id": "9",
                               "certain": True}, dryRun=True)
        noyau._activer_simulation(ctx)
        vision.appliquer_vision(ctx)
        assert not st.scenes["10"].get("studio")

    def test_sans_proposition_ne_leve_pas(self):
        st = FauxStash(scenes=[scene(10, "Rien")])
        ctx = faux_contexte({"sourceVision": True}, st)
        ctx.args = {}
        vision.appliquer_vision(ctx)

    def test_une_proposition_illisible_ne_leve_pas(self):
        st = FauxStash(scenes=[scene(10, "X", custom_fields={
            "enrich_vision_studio": "{cassé"})])
        ctx = faux_contexte({"sourceVision": True}, st)
        ctx.args = {}
        vision.appliquer_vision(ctx)
