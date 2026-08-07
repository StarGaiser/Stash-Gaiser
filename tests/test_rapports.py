# -*- coding: utf-8 -*-
"""
Tâches transverses : lecture des valeurs, seuils, arbitrage.

Ces fonctions décident de ce qui sera ÉCRASÉ — la seule famille
d'opérations du plugin qui déroge au principe « rien n'est écrasé ».
Une erreur de seuil ou de lecture y coûte des données, pas seulement
un affichage.
"""

import json

import pytest

import noyau
import taches_arbitrage
import taches_heritage
from faux import FauxStash, faux_contexte, performer


# ── Lecture de mesures écrites librement ─────────────────────────────
class TestLectureMesures:
    """Les valeurs viennent d'imports au format libre : « 185cm »,
    « 185 cm / 88 kg », « 1,85 m »."""

    @pytest.mark.parametrize("brut,attendu", [
        ("185cm", 185), ("185 cm", 185), ("185", 185),
        ("185cm / 88kg", 185), ("19.0", 19), ("19,5", 20),
        ("  178  ", 178),
    ])
    def test_centimetres_lus(self, brut, attendu):
        assert taches_heritage._cm(brut) == attendu

    @pytest.mark.parametrize("brut", [
        "", None, "abc", "0", "999", "-5", "1000cm",
    ])
    def test_valeurs_hors_plage_refusees(self, brut):
        """Une taille de 999 cm ou de 0 n'est pas une taille : mieux
        vaut ne rien écrire que d'écrire une absurdité."""
        assert taches_heritage._cm(brut) is None

    @pytest.mark.parametrize("brut,attendu", [
        ("185cm / 88kg", 88), ("88 kg", 88), ("88kg", 88),
        ("93.4 kg", 93),
    ])
    def test_kilogrammes_lus(self, brut, attendu):
        assert taches_heritage._kg(brut) == attendu

    def test_poids_absent_de_la_chaine(self):
        """Sans unité, un nombre n'est pas un poids : « 185cm » ne doit
        pas donner 185 kg."""
        assert taches_heritage._kg("185cm") is None
        assert taches_heritage._kg("185") is None

    @pytest.mark.parametrize("brut", ["", None, "10 kg", "500 kg"])
    def test_poids_hors_plage(self, brut):
        assert taches_heritage._kg(brut) is None


# ── Ce qui compte comme un désaccord ─────────────────────────────────
class TestEcartSignificatif:
    """Les sources arrondissent différemment une taille convertie
    depuis les pouces : 5'10″ donne 177 ou 178 selon qui calcule.
    Traiter cela comme un conflit noyait les vrais écarts — treize
    centimètres — sous des dizaines de faux."""

    def test_arrondi_de_conversion_ignore(self):
        for a, b in [("178", "177"), ("183", "184"), ("175", "173")]:
            assert not taches_arbitrage._ecart_significatif("height_cm", a, b)

    def test_ecart_reel_retenu(self):
        for a, b in [("183", "170"), ("180", "173"), ("178", "188")]:
            assert taches_arbitrage._ecart_significatif("height_cm", a, b)

    def test_seuil_a_deux_centimetres(self):
        assert not taches_arbitrage._ecart_significatif("height_cm", "180", "178")
        assert taches_arbitrage._ecart_significatif("height_cm", "180", "177")

    def test_meme_regle_pour_le_poids_et_la_longueur(self):
        for champ in ("weight", "penis_length"):
            assert not taches_arbitrage._ecart_significatif(champ, "90", "91")
            assert taches_arbitrage._ecart_significatif(champ, "90", "95")

    def test_un_jour_d_ecart_sur_une_date(self):
        """Un jour vient d'un fuseau horaire, pas d'un désaccord."""
        assert not taches_arbitrage._ecart_significatif(
            "birthdate", "1984-10-21", "1984-10-22")
        assert taches_arbitrage._ecart_significatif(
            "birthdate", "1984-10-21", "1978-06-14")

    def test_champ_textuel_compare_a_l_identique(self):
        assert not taches_arbitrage._ecart_significatif(
            "country", "FR", "fr")
        assert taches_arbitrage._ecart_significatif("country", "FR", "BE")

    def test_valeurs_illisibles_traitees_comme_un_ecart(self):
        """Dans le doute, signaler : ne pas écraser silencieusement."""
        assert taches_arbitrage._ecart_significatif("height_cm", "abc", "178")


# ── Lecture des conflits enregistrés ─────────────────────────────────
class TestLectureConflits:
    """Le rapport de conflit est du texte : sa relecture doit rendre
    exactement ce qui y a été écrit, sinon on écraserait une valeur par
    une autre mal découpée."""

    LIGNE = ("height_cm : actuel « 183 » vs sources : 178 "
             "[gevi+iafd+stashdb.org 9.8/10]")

    def test_les_quatre_parties_sont_lues(self):
        m = taches_arbitrage._CONFLIT.search(self.LIGNE)
        assert m is not None
        champ, actuel, propose, _srcs, note = m.groups()
        assert champ == "height_cm"
        assert actuel == "183"
        assert propose.strip() == "178"
        assert note == "9.8"

    def test_plusieurs_conflits_sur_une_ligne(self):
        texte = (self.LIGNE + " | country : actuel « BE » vs "
                 "sources : FR [iafd 9.0/10]")
        trouves = list(taches_arbitrage._CONFLIT.finditer(texte))
        assert len(trouves) == 2
        assert trouves[1].group(1) == "country"

    def test_valeur_actuelle_vide(self):
        m = taches_arbitrage._CONFLIT.search(
            "country : actuel «  » vs sources : FR [iafd 9.0/10]")
        assert m is not None
        assert m.group(2).strip() == ""

    def test_texte_sans_conflit(self):
        assert taches_arbitrage._CONFLIT.search("aucun conflit ici") is None


# ── Champs hérités ───────────────────────────────────────────────────
class TestChampsHerites:

    def test_correspondance_avec_les_champs_natifs(self):
        """Chaque champ hérité doit désigner un champ que Stash
        possède vraiment, sinon la migration n'aboutit nulle part."""
        natifs = {"circumcised", "height_cm", "weight", "penis_length"}
        for herite, (officiel, _table) in \
                noyau.CHAMPS_HERITES.items():
            assert officiel in natifs, herite

    def test_vocabulaire_des_valeurs(self):
        _officiel, table = noyau.CHAMPS_HERITES["sexe_type"]
        assert table["cut"] == "cut"
        assert table["coupé"] == "cut"
        assert table["uncut"] == "uncut"

    def test_champs_a_appuyer_sont_natifs(self):
        for champ in taches_heritage.CHAMPS_A_APPUYER:
            assert champ in ("penis_length", "weight", "height_cm")


# ── Comportement des tâches d'écrasement ─────────────────────────────
class TestArbitrageSurFauxServeur:
    """La seule famille de tâches qui écrase : ce qu'elles font doit
    être vérifiable sans toucher à une vraie collection."""

    def _fiche_en_conflit(self, note="9.8", actuel="183",
                          propose="178"):
        return performer(
            1, "Test", height_cm=int(actuel),
            custom_fields={"enrich_rapport":
                           f"CONFLITS : height_cm : actuel « {actuel} » "
                           f"vs sources : {propose} [gevi+iafd {note}/10]"})

    def test_conflit_au_dessus_du_seuil_applique(self):
        st = FauxStash(performers=[self._fiche_en_conflit()])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_arbitrage.arbitrer_conflits(ctx)
        assert str(st.performers["1"]["height_cm"]) == "178"

    def test_conflit_sous_le_seuil_ignore(self):
        st = FauxStash(performers=[self._fiche_en_conflit(note="7.5")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_arbitrage.arbitrer_conflits(ctx)
        assert str(st.performers["1"]["height_cm"]) == "183"

    def test_arrondi_non_applique(self):
        st = FauxStash(performers=[
            self._fiche_en_conflit(actuel="178", propose="177")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_arbitrage.arbitrer_conflits(ctx)
        assert str(st.performers["1"]["height_cm"]) == "178"

    def test_ancienne_valeur_conservee_dans_l_historique(self):
        """Sans cela, « Annuler le dernier passage » ne pourrait rien
        rétablir — et l'écrasement serait sans retour."""
        st = FauxStash(performers=[self._fiche_en_conflit()])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_arbitrage.arbitrer_conflits(ctx)
        hist = json.loads(
            st.performers["1"]["custom_fields"]["enrich_historique"])
        assert hist[-1]["champs"]["height_cm"] == ["183", "178"]

    def test_seuil_reglable(self):
        st = FauxStash(performers=[self._fiche_en_conflit(note="8.0")])
        ctx = faux_contexte({}, st)
        ctx.args = {"note": "7.5"}
        taches_arbitrage.arbitrer_conflits(ctx)
        assert str(st.performers["1"]["height_cm"]) == "178"

    def test_restriction_par_champ(self):
        st = FauxStash(performers=[self._fiche_en_conflit()])
        ctx = faux_contexte({}, st)
        ctx.args = {"champs": "country"}
        taches_arbitrage.arbitrer_conflits(ctx)
        assert str(st.performers["1"]["height_cm"]) == "183"

    def test_rien_sans_conflit(self):
        st = FauxStash(performers=[performer(1, "Test", height_cm=183)])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_arbitrage.arbitrer_conflits(ctx)
        assert st.mutations() == 0

    def test_simulation_n_ecrit_pas(self):
        import noyau
        st = FauxStash(performers=[self._fiche_en_conflit()])
        ctx = faux_contexte({"dryRun": True}, st)
        ctx.args = {}
        noyau._activer_simulation(ctx)
        taches_arbitrage.arbitrer_conflits(ctx)
        assert str(st.performers["1"]["height_cm"]) == "183"


class TestSuppressionChampHerite:

    def test_champ_du_plugin_refuse(self):
        """Supprimer enrich_sources d'un coup effacerait toute la
        traçabilité : la tâche doit s'y opposer."""
        st = FauxStash(performers=[performer(
            1, "Test", custom_fields={"enrich_sources": "x"})])
        ctx = faux_contexte({}, st)
        ctx.args = {"champ": "enrich_sources"}
        taches_heritage.retirer_champ_herite(ctx)
        assert st.performers["1"]["custom_fields"].get("enrich_sources")

    def test_argument_manquant(self):
        st = FauxStash(performers=[performer(1, "Test")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_heritage.retirer_champ_herite(ctx)
        assert st.mutations() == 0

    def test_champ_herite_retire(self):
        st = FauxStash(performers=[performer(
            1, "Test", custom_fields={"vieux": "x", "enrich_a": "y"})])
        ctx = faux_contexte({}, st)
        ctx.args = {"champ": "vieux"}
        taches_heritage.retirer_champ_herite(ctx)
        assert st.appels.get("update_performer", 0) == 1
