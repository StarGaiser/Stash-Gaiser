# -*- coding: utf-8 -*-
"""
Ce que le modèle sait, et que les sources ignorent.

Écrit AVANT le code.

J'ai tenu une position trop ferme : tout ce qui ne figure pas dans les
données était refusé. L'argument contraire est solide — un Grabby pour
une scène de la collection donne envie de la revoir, et aucun scraper
ne le fournit. C'est même une raison d'employer un modèle plutôt qu'un
simple assembleur de champs.

Le problème n'est pas que le modèle sache : c'est qu'on ne peut pas
DISTINGUER ce qu'il sait de ce qu'il fabrique. « Grabby 2019 » et
« Titan Men » sortent de la même phrase, avec la même assurance.

**La solution n'est ni d'interdire ni de tout croire, mais de
SÉPARER.** Le texte de base ne tient que sur les données. Ce que le
modèle ajoute de son propre savoir va dans une phrase distincte,
signalée comme telle, que l'utilisateur peut lire, vérifier et
supprimer d'un geste.

Trois exigences en découlent.

**L'apport est isolé**, pas fondu dans le texte : fondu, il devient
invérifiable.

**Il est marqué comme non vérifié** — le lecteur doit savoir que
personne ne l'a confirmé.

**Il reste facultatif** : quelqu'un qui ne veut que du vérifiable
l'éteint.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import ia  # noqa: E402
from faux import FauxStash, faux_contexte, performer  # noqa: E402


@pytest.fixture(scope="module")
def prompt():
    import i18n
    return i18n.t("prompt_biohot", "fr")


class TestApportDuModele:
    """Ce que le modèle sait n'est pas à jeter, mais pas à mêler."""

    def test_le_prompt_demande_l_apport_a_part(self, prompt):
        """Fondu dans le texte, l'apport devient invérifiable : c'est
        toute la difficulté."""
        import i18n
        apport = i18n.t("prompt_biohot_apport", "fr").lower()
        assert any(m in apport for m in
                   ("à part", "séparé", "après le texte")), apport

    def test_le_prompt_nomme_ce_qui_est_recevable(self, prompt):
        """« Ce que tu sais » est trop large. Une récompense, un fait
        de carrière : des choses vérifiables par le lecteur."""
        import i18n
        apport = i18n.t("prompt_biohot_apport", "fr").lower()
        assert any(m in apport for m in
                   ("récompense", "grabby", "prix", "carrière")), \
            apport

    def test_le_prompt_exige_le_doute(self, prompt):
        """Le modèle doit se taire s'il n'est pas sûr : une récompense
        inventée est pire qu'une récompense tue."""
        import i18n
        apport = i18n.t("prompt_biohot_apport", "fr").lower()
        assert any(m in apport for m in
                   ("certitude", "certain", "doute", "sûr")), apport


class TestSeparationMecanique:
    """La séparation ne peut pas reposer sur la seule bonne volonté du
    modèle : elle doit être vérifiable dans le texte produit."""

    def test_l_apport_est_reconnaissable(self):
        texte = ("Corps épais, 20 cm.\n[non vérifié] Grabby 2019 du "
                 "meilleur second rôle.")
        base, apport = ia.separer_apport(texte)
        assert base.strip() == "Corps épais, 20 cm."
        assert "Grabby" in apport

    def test_un_texte_sans_apport_reste_entier(self):
        base, apport = ia.separer_apport("Corps épais, 20 cm.")
        assert base == "Corps épais, 20 cm."
        assert apport == ""

    def test_le_controle_des_noms_ne_porte_que_sur_la_base(self):
        """Un studio cité dans l'apport n'est pas une invention à
        refuser : il est signalé comme non vérifié, et c'est
        justement ce que le marquage permet."""
        texte = ("Quatre scènes chez Drill My Hole.\n"
                 "[non vérifié] Grabby 2019 chez Titan Men.")
        base, _apport = ia.separer_apport(texte)
        assert ia.noms_verifies(base, {"Drill My Hole"})

    def test_valeurs_absurdes(self):
        for brut in ("", None, "[non vérifié] seul"):
            base, apport = ia.separer_apport(brut)
            assert isinstance(base, str) and isinstance(apport, str)


class TestReglage:
    """Quelqu'un qui ne veut que du vérifiable doit pouvoir
    l'éteindre — et c'est le défaut, car c'est le choix prudent."""

    def test_l_apport_est_eteint_par_defaut(self):
        ctx = faux_contexte({}, FauxStash())
        assert not ctx.source_active("savoirmodele")

    def test_il_peut_etre_allume(self):
        ctx = faux_contexte({"sourceSavoirModele": True}, FauxStash())
        assert ctx.source_active("savoirmodele")

    def test_eteint_le_prompt_ne_le_demande_pas(self):
        """Demander un apport puis le jeter coûterait des jetons pour
        rien."""
        ctx = faux_contexte({}, FauxStash())
        assert "[non vérifié]" not in ia.prompt_biohot(ctx)

    def test_allume_le_prompt_le_demande(self):
        ctx = faux_contexte({"sourceSavoirModele": True,
                             "language": "fr"},
                            FauxStash())
        assert "[non vérifié]" in ia.prompt_biohot(ctx)


class TestCeQueVoitLeLecteur:
    """Un apport non signalé serait pire que pas d'apport du tout :
    le lecteur croirait à un fait établi."""

    def test_l_apport_est_range_a_part_sur_la_fiche(self):
        st = FauxStash(performers=[performer(1, "Archie Fox")])
        ctx = faux_contexte({"sourceSavoirModele": True}, st)
        ia._ranger_apport(ctx, "performer", "1",
                          "Grabby 2019 du meilleur second rôle.")
        cf = st.performers["1"].get("custom_fields") or {}
        assert "Grabby" in str(cf.get("enrich_apport_modele") or "")

    def test_un_apport_vide_n_ecrit_rien(self):
        st = FauxStash(performers=[performer(1, "Archie Fox")])
        ctx = faux_contexte({"sourceSavoirModele": True}, st)
        ia._ranger_apport(ctx, "performer", "1", "")
        cf = st.performers["1"].get("custom_fields") or {}
        assert not cf.get("enrich_apport_modele")


class TestControlePartoutOuLOnGenere:
    """Le contrôle des noms propres ne s'exécutait que dans la
    génération en lot. L'aperçu sur fiche — celui qu'on regarde de
    près, justement — n'en bénéficiait pas.

    Un garde-fou qui ne couvre qu'un chemin sur deux ne protège de
    rien : il donne l'illusion d'une protection là où l'utilisateur
    lit le plus attentivement."""

    def _monde(self, reponse):
        st = FauxStash(performers=[performer(
            1, "Archie Fox", details="Un texte.")])
        ctx = faux_contexte({"aiBiohot": "mistral:m",
                             "llmApiKey": "essai",
                             "language": "fr"}, st)
        ctx.args = {"performer_id": "1"}
        return st, ctx

    def test_l_apercu_refuse_un_nom_invente(self, monkeypatch):
        monkeypatch.setattr(
            ia, "_appel_llm",
            lambda *a, **k: "Quatre scènes chez Titan Men.")
        st, ctx = self._monde(None)
        ia.generer_apercu(ctx)
        cf = st.performers["1"].get("custom_fields") or {}
        assert not cf.get("enrich_apercu"), cf.get("enrich_apercu")

    def test_l_apercu_accepte_un_texte_sans_nom(self, monkeypatch):
        monkeypatch.setattr(
            ia, "_appel_llm",
            lambda *a, **k: "Corps épais, il baise sans hâte.")
        st, ctx = self._monde(None)
        ia.generer_apercu(ctx)
        cf = st.performers["1"].get("custom_fields") or {}
        assert cf.get("enrich_apercu")

    def test_l_apport_est_separe_dans_l_apercu(self, monkeypatch):
        """L'apport ne doit pas être soumis au contrôle des noms :
        son intérêt est précisément de dépasser les données."""
        monkeypatch.setattr(
            ia, "_appel_llm",
            lambda *a, **k: ("Corps épais.\n[non vérifié] Grabby 2019 "
                             "chez Titan Men."))
        st, ctx = self._monde(None)
        ia.generer_apercu(ctx)
        cf = st.performers["1"].get("custom_fields") or {}
        assert cf.get("enrich_apercu")
        assert "Grabby" in str(cf.get("enrich_apport_modele") or "")


class TestApercuRecoitLaMemeMatiere:
    """L'aperçu n'envoyait au modèle que la biographie de la fiche. La
    génération en lot, elle, transmet les statistiques de collection :
    studios, partenaires, nombre de scènes.

    Le modèle inventait donc des studios — Falcon, CockyBoys, Bel Ami
    — non par penchant, mais parce qu'on ne lui donnait rien. Et le
    texte visé par l'aperçu est précisément celui qui doit parler de
    LA COLLECTION.

    Deux conséquences. L'aperçu doit recevoir la même matière, sans
    quoi il ne montre pas ce que la génération produira — un aperçu
    menteur. Et le contrôle des noms doit comparer à cette même
    matière, sans quoi il refuse des studios pourtant réels."""

    def test_l_apercu_transmet_les_studios_de_la_collection(self):
        st = FauxStash(performers=[performer(1, "Archie Fox")])
        ctx = faux_contexte({}, st)
        matiere = ia._matiere_fiche(ctx, "performer",
                                    st.performers["1"])
        assert "dans_la_collection" in matiere

    def test_la_matiere_est_celle_du_lot(self):
        """Deux matières différentes produiraient deux textes
        différents, et l'aperçu serait menteur."""
        code = (Path(ia.__file__)).read_text(encoding="utf-8")
        i = code.find("def _matiere_fiche")
        bloc = code[i:i + 900]
        assert "stats_collection" in bloc

    def test_le_controle_compare_a_cette_matiere(self):
        """Comparer aux seules données de la fiche ferait refuser un
        studio pourtant présent dans la collection."""
        code = (Path(ia.__file__)).read_text(encoding="utf-8")
        i = code.find("def generer_apercu")
        fin = code.find("\ndef ", i + 10)
        bloc = code[i:fin if fin > i else i + 2500]
        assert "_noms_fournis(fiche)" not in bloc, \
            "le contrôle doit porter sur la matière transmise"

    def test_un_studio_de_la_collection_passe(self):
        assert ia.noms_verifies("Quatre scènes chez Drill My Hole.",
                                {"Drill My Hole"})
