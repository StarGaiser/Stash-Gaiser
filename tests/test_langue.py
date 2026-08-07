# -*- coding: utf-8 -*-
"""
Langue : ce qui est écrit doit l'être dans la langue voulue.

Écrit AVANT le code.

Deux exigences distinctes, qu'il faut séparer pour les tenir.

**Le texte produit** doit être dans la langue choisie : une
présentation, une biographie, un synopsis. C'était déjà le cas — le nom
de la langue était passé au modèle.

**Les instructions données au modèle** doivent l'être aussi. Elles
étaient toutes en français, quelle que soit la langue demandée. Un
modèle recevant des consignes en français et sommé de répondre en
néerlandais obéit mal : il glisse vers la langue des consignes, et sa
compréhension des nuances se dégrade.

**La langue par défaut** est celle que l'utilisateur a réglée dans
Stash. Lui demander de la redire dans le plugin est une redite, et
laisse une installation en anglais produire du français.
"""

import pytest

import i18n
from faux import FauxStash, faux_contexte


LANGUES = ("en", "fr", "de", "es", "it", "pt", "nl")


# ── Langue par défaut ────────────────────────────────────────────────
class TestLangueParDefaut:

    def _ctx(self, reglage=None, langue_stash=None):
        st = FauxStash()
        if langue_stash is not None:
            st.interface_language = langue_stash
        return faux_contexte({"language": reglage} if reglage
                             else {}, st)

    def test_le_reglage_du_plugin_prime(self):
        ctx = self._ctx(reglage="de", langue_stash="fr-FR")
        assert ctx.lang() == "de"

    def test_a_defaut_la_langue_de_stash(self):
        """Une installation réglée en français ne doit pas produire de
        l'anglais parce qu'on a oublié un second réglage."""
        ctx = self._ctx(langue_stash="fr-FR")
        assert ctx.lang() == "fr"

    @pytest.mark.parametrize("brut,attendu", [
        ("fr-FR", "fr"), ("de-DE", "de"), ("es-ES", "es"),
        ("it-IT", "it"), ("pt-BR", "pt"), ("nl-NL", "nl"),
        ("en-US", "en"), ("en-GB", "en"),
    ])
    def test_les_formes_regionales_sont_reconnues(self, brut, attendu):
        assert ctx_lang(self._ctx(langue_stash=brut)) == attendu

    def test_langue_inconnue_retombe_sur_l_anglais(self):
        ctx = self._ctx(langue_stash="ja-JP")
        assert ctx.lang() == "en"

    def test_stash_muet_ne_leve_pas(self):
        ctx = self._ctx()
        assert ctx.lang() in LANGUES


def ctx_lang(ctx):
    return ctx.lang()


# ── Instructions données au modèle ───────────────────────────────────
class TestPromptsTraduits:
    """Un prompt est un texte : il se traduit comme les autres, et sa
    place est donc dans la table de traduction."""

    CLES = ("prompt_biohot", "prompt_biohot_consignes",
            "prompt_roles", "prompt_bio", "prompt_synopsis",
            "prompt_bio_studio")

    @pytest.mark.parametrize("cle", CLES)
    def test_chaque_prompt_existe_dans_les_sept_langues(self, cle):
        for lg in LANGUES:
            texte = i18n.t(cle, lg)
            assert texte and texte != cle, f"{cle} manque en {lg}"

    @pytest.mark.parametrize("cle", CLES)
    def test_les_traductions_different_vraiment(self, cle):
        """Une table où toutes les langues portent le même texte
        donnerait l'illusion d'une traduction."""
        textes = {i18n.t(cle, lg) for lg in LANGUES}
        assert len(textes) >= 5, f"{cle} : {len(textes)} versions"

    def test_les_reperes_sont_conserves(self):
        """« {nom} », « {langue} », « {donnees} » sont remplacés avant
        envoi : une traduction qui les perd casse le prompt."""
        for lg in LANGUES:
            texte = i18n.t("prompt_biohot", lg)
            for repere in ("{nom}", "{langue}"):
                assert repere in texte, f"prompt_biohot/{lg}: {repere}"

    def test_la_regle_de_non_invention_survit_a_la_traduction(self):
        """La consigne qui interdit d'inventer est la protection la
        plus importante du prompt : elle doit figurer dans chaque
        version, faute de quoi une langue produirait des textes
        inventés."""
        for lg in LANGUES:
            texte = i18n.t("prompt_biohot", lg).lower()
            assert any(mot in texte for mot in (
                "invent", "erfind", "inventa", "verzin", "déduis",
                "deduce", "solo", "uniquement", "only", "nur",
                "alleen", "apenas", "unicamente")), lg


class TestPromptEmploye:
    """Le prompt employé doit suivre la langue du contexte, et le
    réglage de l'utilisateur doit primer sur tout."""

    def _ctx(self, lang):
        return faux_contexte({"language": lang}, FauxStash())

    def test_le_prompt_suit_la_langue(self):
        import ia
        textes = {ia.prompt_biohot(self._ctx(lg)) for lg in LANGUES}
        assert len(textes) >= 5

    def test_le_prompt_personnalise_prime(self):
        import ia
        ctx = faux_contexte({"language": "fr",
                             "biohotPrompt": "Mes propres consignes."},
                            FauxStash())
        assert ia.prompt_biohot(ctx) .startswith("Mes propres")

    def test_prompt_personnalise_vide_ignore(self):
        import ia
        ctx = faux_contexte({"language": "fr", "biohotPrompt": "   "},
                            FauxStash())
        assert len(ia.prompt_biohot(ctx)) > 50

    def test_la_langue_de_sortie_est_dans_le_prompt(self):
        """Le nom de la langue est donné au modèle en toutes lettres :
        « Nederlands » est plus sûr que « nl »."""
        import ia
        for lg in LANGUES:
            ctx = self._ctx(lg)
            attendu = i18n.LANGUES[lg]["llm"]
            assert attendu in ia.prompt_biohot(ctx), lg
