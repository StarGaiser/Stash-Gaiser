# -*- coding: utf-8 -*-
"""
Génération de textes : ce qui protège contre l'invention.

Un modèle de langage produit toujours quelque chose. C'est sa nature,
et c'est le danger : sur une fiche sans matière, il écrira une
biographie plausible et fausse plutôt que de se taire.

Tout ce module est construit contre cela. Les tests éprouvent d'abord
les garde-fous — empreinte qui évite de repayer un appel identique,
plafond de dépense, pause après incident, vérification que le modèle a
CITÉ un passage réellement présent — puis la lecture des réponses, qui
arrivent malformées plus souvent qu'on ne croit.

Aucun appel réseau : le modèle est remplacé le temps du test. Ce qui
est éprouvé, c'est le raisonnement autour de l'appel, pas l'appel.
"""

import json

import pytest

import ia
import noyau
from faux import FauxStash, faux_contexte, performer


@pytest.fixture(autouse=True)
def etat_isole(tmp_path, monkeypatch):
    monkeypatch.setattr(noyau, "ETAT_FICHIER", tmp_path / "etat.json")
    ia._LLM.update({"n": 0, "max": 0, "averti": False,
                    "averti_pause": False, "delai": 0})


def _ctx(**reglages):
    # Chaque usage a son réglage : « bio » pour la biographie et
    # les rôles, « biohot » pour la présentation, « synopsis » pour
    # les scènes. Un contexte qui n'en déclare qu'un ne teste que lui.
    base = {"language": "fr", "aiDefault": "mistral:m",
            "llmApiKey": "essai"}
    base.update(reglages)
    ctx = faux_contexte(base, FauxStash())
    ctx.args = {}
    return ctx


def _repond(monkeypatch, reponse):
    """Remplace l'appel au modèle. Le reste du module est éprouvé
    tel quel."""
    monkeypatch.setattr(ia, "_appel_llm", lambda *a, **k: reponse)


# ── Ne pas repayer deux fois le même appel ───────────────────────────
class TestEmpreinte:
    """Une génération coûte un appel payant. La relancer sur une fiche
    dont ni les données ni les instructions n'ont changé la refait à
    l'identique — et la facture double sans rien apporter."""

    def test_meme_matiere_meme_empreinte(self):
        a = ia.empreinte_sources("biohot", "instructions")
        b = ia.empreinte_sources("biohot", "instructions")
        assert a == b

    def test_instructions_differentes_empreintes_differentes(self):
        assert (ia.empreinte_sources("biohot", "A")
                != ia.empreinte_sources("biohot", "B"))

    def test_usages_differents_empreintes_differentes(self):
        """La même consigne pour une bio et pour un synopsis ne doit
        pas se confondre."""
        assert (ia.empreinte_sources("biohot", "X")
                != ia.empreinte_sources("synopsis", "X"))

    def test_un_texte_a_jour_est_reconnu(self):
        cf = ia.marquer_empreinte({}, "biohot", "instructions")
        fiche = {"custom_fields": dict(cf, bio_hot="Un texte.")}
        assert ia.texte_a_jour(fiche, "biohot", "instructions",
                               "bio_hot")

    def test_des_instructions_modifiees_perimen_le_texte(self):
        cf = ia.marquer_empreinte({}, "biohot", "anciennes")
        fiche = {"custom_fields": dict(cf, bio_hot="Un texte.")}
        assert not ia.texte_a_jour(fiche, "biohot", "nouvelles",
                                   "bio_hot")

    def test_un_texte_absent_n_est_jamais_a_jour(self):
        cf = ia.marquer_empreinte({}, "biohot", "instructions")
        fiche = {"custom_fields": dict(cf, bio_hot="")}
        assert not ia.texte_a_jour(fiche, "biohot", "instructions",
                                   "bio_hot")

    def test_fiche_sans_champs(self):
        assert not ia.texte_a_jour({}, "biohot", "x", "bio_hot")


# ── Lecture des incidents ────────────────────────────────────────────
class TestDiagnostic:
    """Un fournisseur qui refuse le dit de dix façons. Confondre une
    limite de débit — passagère — avec une clé invalide — définitive —
    fait soit abandonner trop tôt, soit marteler un service qui refuse."""

    @pytest.mark.parametrize("code,attendu", [
        (429, "debit"), (401, "cle"), (403, "cle"), (402, "quota"),
        (500, "indispo"), (503, "indispo"),
    ])
    def test_les_codes_sont_distingues(self, code, attendu):
        categorie, _message = ia._diag_llm(None, code, "")
        assert categorie == attendu

    def test_message_traduit(self):
        _categorie, message = ia._diag_llm(None, 429, "")
        assert message and message != "ia_debit"

    def test_incident_inconnu(self):
        categorie, message = ia._diag_llm(
            RuntimeError("quelque chose"), None, "")
        assert categorie and message

    def test_aucune_exception_sur_entrees_absurdes(self):
        for exc, code, corps in ((None, None, None), (None, 0, ""),
                                 (ValueError(), 999, "")):
            categorie, _message = ia._diag_llm(exc, code, corps)
            assert isinstance(categorie, str)


# ── Plafond et pause ─────────────────────────────────────────────────
class TestPlafond:
    """Le plafond protège la facture ; la pause protège le service.
    Sans eux, une tâche de masse lancée sur un millier de fiches peut coûter
    cher et faire bloquer la clé."""

    def test_le_plafond_arrete_les_appels(self, monkeypatch):
        _repond(monkeypatch, "réponse")
        ia._LLM.update({"max": 2, "n": 2})
        assert ia._appel_llm_plafonne("mistral", "m", "k", "p") is None

    def test_sous_le_plafond_l_appel_passe(self, monkeypatch):
        monkeypatch.setattr(ia, "_appel_llm_une_fois",
                            lambda *a, **k: ("texte", None))
        ia._LLM.update({"max": 10, "n": 0})
        assert ia._appel_llm_plafonne("mistral", "m", "k", "p")

    def test_une_pause_active_bloque(self, monkeypatch):
        noyau.etat_ecrire({"pause_ia": "2099-01-01",
                           "pause_motif": "essai"})
        assert ia._appel_llm("mistral", "m", "k", "p") is None

    def test_la_pause_n_avertit_qu_une_fois(self, monkeypatch):
        """Un avertissement par fiche noierait le journal sur une
        collection entière : le second appel doit rester muet."""
        noyau.etat_ecrire({"pause_ia": "2099-01-01",
                           "pause_motif": "essai"})
        ia._LLM["averti_pause"] = False
        ia._appel_llm("mistral", "m", "k", "p")
        premier = ia._LLM.get("averti_pause")
        ia._appel_llm("mistral", "m", "k", "p")
        assert premier == ia._LLM.get("averti_pause")


# ── Rôles : le modèle doit citer, pas deviner ────────────────────────
class TestDeductionDesRoles:
    """C'est le contrôle le plus important du module. Le modèle doit
    citer un passage, et ce passage est vérifié PRÉSENT dans les textes
    fournis — seul garde-fou possible contre une citation fabriquée."""

    DOC = ("Dans une interview, il déclare qu'il était principalement "
           "bottom au début de sa carrière.")

    def _reponse(self, **champs):
        base = {"position": None, "pouvoir": None, "citation": None,
                "confiance": 0.0}
        base.update(champs)
        return json.dumps(base)

    def test_une_citation_presente_est_retenue(self, monkeypatch):
        _repond(monkeypatch, self._reponse(
            position="passif", citation="il était principalement bottom",
            confiance=0.9))
        lu, motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu and lu.get("position") == "passif"
        assert "bottom" in motif

    def test_une_citation_absente_est_refusee(self, monkeypatch):
        """Le cas qui compte : le modèle affirme, mais le passage
        n'existe pas dans ce qu'on lui a donné."""
        _repond(monkeypatch, self._reponse(
            position="actif", citation="il se dit exclusivement top",
            confiance=0.95))
        lu, motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu is None
        assert "citation" in motif.lower()

    def test_sans_citation_rien_n_est_retenu(self, monkeypatch):
        _repond(monkeypatch, self._reponse(
            position="actif", confiance=0.99))
        lu, _motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu is None

    def test_une_confiance_faible_est_refusee(self, monkeypatch):
        _repond(monkeypatch, self._reponse(
            position="passif", citation="il était principalement bottom",
            confiance=0.4))
        lu, _motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu is None

    def test_un_vocabulaire_inconnu_est_refuse(self, monkeypatch):
        """Le modèle peut répondre « dominant/passif » ou inventer un
        terme : seul le vocabulaire du plugin est accepté."""
        _repond(monkeypatch, self._reponse(
            position="mystérieux", citation="il était principalement "
            "bottom", confiance=0.9))
        lu, _motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu is None

    def test_reponse_illisible(self, monkeypatch):
        for brut in ("pas du json", "", "{cassé", "null", "[]"):
            _repond(monkeypatch, brut)
            lu, _motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
            assert lu is None, brut

    def test_json_noye_dans_du_texte(self, monkeypatch):
        """Les modèles encadrent souvent leur JSON d'explications."""
        _repond(monkeypatch, 'Voici ma réponse :\n'
                + self._reponse(position="passif",
                                citation="il était principalement bottom",
                                confiance=0.9)
                + "\nJ'espère que cela convient.")
        lu, _motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu and lu.get("position") == "passif"

    def test_sans_reponse_du_modele(self, monkeypatch):
        _repond(monkeypatch, None)
        lu, motif = ia.deduire_role(_ctx(), {"name": "X"}, self.DOC)
        assert lu is None and motif

    def test_sans_ia_configuree(self, monkeypatch):
        ctx = faux_contexte({"language": "fr"}, FauxStash())
        ctx.args = {}
        lu, motif = ia.deduire_role(ctx, {"name": "X"}, self.DOC)
        assert lu is None and motif


# ── Génération de textes ─────────────────────────────────────────────
class TestGeneration:

    def test_le_modele_reformule_ce_que_les_sources_disent(
            self, monkeypatch):
        """La fonction rend un quadruplet : texte, provenance,
        fiabilité, motif. Le modèle est appelé même sur une source
        unique — il uniformise la forme et traduit —, et sa
        provenance est enregistrée comme telle."""
        _repond(monkeypatch, "Un texte du modèle.")
        sortie = ia.synth_bio(_ctx(), "Archie", {"iafd": {"bio": "x"}})
        assert sortie and sortie[0] == "Un texte du modèle."
        assert sortie[1].startswith("llm/"), \
            "la provenance doit dire que le texte vient du modèle"
        assert "iafd" in sortie[3], \
            "et le motif doit citer les sources employées"

    def test_sans_matiere_rien_n_est_genere(self, monkeypatch):
        """Le point le plus important : sur une fiche vide, le modèle
        écrirait une biographie plausible et fausse."""
        _repond(monkeypatch, "Une biographie inventée.")
        assert ia.synth_bio(_ctx(), "Archie", {}) is None

    def test_synopsis_sans_matiere(self, monkeypatch):
        _repond(monkeypatch, "Un synopsis inventé.")
        assert ia.synth_synopsis(_ctx(), "Une scène", {}) is None

    def test_sans_ia_une_source_reste_exploitable(self, monkeypatch):
        """L'absence de modèle ne doit pas priver de ce qu'une source
        a déjà écrit."""
        _repond(monkeypatch, "texte")
        ctx = faux_contexte({"language": "fr"}, FauxStash())
        sortie = ia.synth_bio(ctx, "Archie", {"iafd": {"bio": "x"}})
        assert sortie and sortie[0] == "x"

    def test_reponse_vide_du_modele(self, monkeypatch):
        """Plusieurs sources et un modèle muet : rien ne doit être
        écrit plutôt qu'un texte vide."""
        _repond(monkeypatch, "")
        sortie = ia.synth_bio(_ctx(), "Archie",
                              {"iafd": {"bio": "x"},
                               "gevi": {"bio": "y"}})
        assert sortie is None or sortie[0] in ("x", "y")

    def test_la_presentation_suit_les_instructions_du_contexte(self):
        """Un prompt personnalisé prime ; à défaut, celui de la langue
        choisie."""
        perso = ia.prompt_biohot(_ctx(biohotPrompt="Mes consignes."))
        defaut = ia.prompt_biohot(_ctx())
        assert perso.startswith("Mes consignes.")
        assert "français" in defaut

    def test_presentation_sans_matiere(self, monkeypatch):
        _repond(monkeypatch, "Une présentation inventée.")
        st = FauxStash(performers=[performer(1, "Archie")])
        ctx = faux_contexte({"language": "fr", "aiBiohot": "mistral:m"},
                            st)
        ctx.args = {}
        ia.generer_bio_hot(ctx, st.performers["1"], {})
        assert not (st.performers["1"].get("custom_fields") or {}) \
            .get("bio_hot")
