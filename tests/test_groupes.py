# -*- coding: utf-8 -*-
"""
Films en plusieurs parties : lecture des motifs, notation, rapprochement.

L'information ne venant d'aucune source, tout repose sur ces fonctions.
Un faux positif crée un groupe absurde ; un faux négatif laisse un film
en morceaux.
"""

import groupes as g


# ── Lecture d'un motif de partie ─────────────────────────────────────
class TestLirePartie:

    def test_part_classique(self):
        serie, num, genre, _bonus = g._lire_partie("The Business Of Sex Part 3")
        assert serie == "The Business Of Sex"
        assert num == 3
        assert genre == "partie"

    def test_variantes_du_mot_cle(self):
        for texte, attendu in [
            ("Stepfather's Secret Part 8", 8),
            ("Bullfight Edition vol 2", 2),
            ("Gay of Thrones Episode 4", 4),
            ("Brazil Underground - Scene 6", 6),
            ("The Cult Chapter 2", 2),
            ("Trade Show 3 of 5", 3),
        ]:
            lu = g._lire_partie(texte)
            assert lu is not None, texte
            assert lu[1] == attendu, texte

    def test_separateurs_de_nom_de_fichier(self):
        lu = g._lire_partie("GAY_Falcon_Cheat_Day_part.2.mp4")
        assert lu is not None and lu[1] == 2

    def test_extension_retiree(self):
        lu = g._lire_partie("Howl Part 1.mkv")
        assert lu is not None and "mkv" not in lu[0].lower()

    def test_nombre_seul_refuse(self):
        """« Men 2 » est un titre, pas une suite : sans mot-clé, rien."""
        for texte in ["Men 2", "Falcon 4K", "Sean Cody 1080p", "Big 12"]:
            assert g._lire_partie(texte) is None, texte

    def test_nom_trop_court_refuse(self):
        assert g._lire_partie("AB Part 2") is None

    def test_texte_vide(self):
        assert g._lire_partie("") is None
        assert g._lire_partie(None) is None

    def test_numero_a_deux_chiffres(self):
        lu = g._lire_partie("Long Series Part 12")
        assert lu is not None and lu[1] == 12


# ── Présentation du nom ──────────────────────────────────────────────
class TestNomPropre:

    def test_titre_officiel_intact(self):
        assert g._nom_serie_propre("Stepfather's Secret", True) \
            == "Stepfather's Secret"

    def test_prefixe_de_classement_retire(self):
        assert g._nom_serie_propre("GAY Irmaosdotados tesao", False) \
            == "Irmaosdotados Tesao"

    def test_capitales_retablies(self):
        assert g._nom_serie_propre("the power of persuasion", False) \
            == "The Power of Persuasion"

    def test_petits_mots_en_minuscules_sauf_en_tete(self):
        assert g._nom_serie_propre("the cult of hedonism", False) \
            == "The Cult of Hedonism"

    def test_sigles_preserves(self):
        assert "TIM" in g._nom_serie_propre("treasure island TIM fuck", False)

    def test_apostrophe_non_abimee(self):
        """`str.title()` produirait « Stepfather'S » : c'est pourquoi la
        mise en capitales est faite mot à mot."""
        assert g._nom_serie_propre("stepfather's secret", False) \
            == "Stepfather's Secret"


# ── Rapprochement de deux écritures ──────────────────────────────────
class TestMemeSerie:
    """Le titre est en FIN de nom, le bruit le précède : seul un
    rapprochement par suffixe est accepté."""

    def _proche(self, court, long_):
        return g._meme_serie(g._cle_serie(court), g._cle_serie(long_))

    def test_prefixe_de_nommage_reconnu(self):
        assert self._proche(
            "Brazil Underground",
            "Gay - Treasure Island - TIM Fuck - Brazil Underground")

    def test_suite_numerotee_non_confondue(self):
        assert not self._proche("Howl", "Howl 2 Reloaded")

    def test_titre_prolonge_non_confondu(self):
        assert not self._proche("The Cult", "The Cult of Hedonism")

    def test_nom_trop_court_refuse(self):
        """Sous huit caractères, la coïncidence est trop probable."""
        assert not self._proche("Call", "Last Call")

    def test_noms_identiques_non_rapproches(self):
        assert not self._proche("Brazil Underground", "Brazil Underground")

    def test_studio_en_prefixe(self):
        assert self._proche("Sex Traveler", "Drill My Hole Sex Traveler")


# ── Note de confiance ────────────────────────────────────────────────
class TestNoteSerie:

    def _parties(self, nums):
        return [(n, {"id": str(n)}) for n in nums]

    def test_serie_complete_bien_notee(self):
        note, _motif = g._note_serie(self._parties([1, 2, 3, 4]),
                                     True, 0.5)
        assert note >= 8.5, "doit passer le seuil d'application"

    def test_partie_unique_penalisee(self):
        note, motif = g._note_serie(self._parties([6]), True, 0.5)
        assert note < 7.5
        assert "une seule partie" in motif

    def test_studios_differents_penalises(self):
        pleine = g._note_serie(self._parties([1, 2, 3]), True, 0.5)[0]
        eclatee = g._note_serie(self._parties([1, 2, 3]), False, 0.5)[0]
        assert eclatee < pleine

    def test_numerotation_trouee_moins_sure(self):
        continue_ = g._note_serie(self._parties([1, 2]), True, 0.5)[0]
        trouee = g._note_serie(self._parties([1, 4]), True, 0.5)[0]
        assert trouee < continue_

    def test_motif_ambigu_penalise(self):
        """« scene » vaut moins que « part » : bonus négatif."""
        sur = g._note_serie(self._parties([1, 2]), True, 0.5)[0]
        vague = g._note_serie(self._parties([1, 2]), True, -0.5)[0]
        assert vague < sur

    def test_note_bornee(self):
        for nums in ([1], [1, 2, 3, 4, 5, 6, 7, 8], [3, 3]):
            for studio in (True, False):
                note, _m = g._note_serie(self._parties(nums), studio, 0.5)
                assert 0 <= note <= 10

    def test_numeros_en_double_signales(self):
        _note, motif = g._note_serie(self._parties([1, 1, 2]), True, 0.5)
        assert "double" in motif


# ── Fusion des séries écrites de deux façons ─────────────────────────
class TestFusionnerSeries:

    def _serie(self, nom, nums, studios=("1",)):
        return {"nom": nom,
                "parties": [(n, {"id": f"{nom}{n}"}) for n in nums],
                "studios": set(studios), "dates": [], "genre": "partie",
                "bonus": 0.5, "depuis_titre": True}

    def test_deux_ecritures_reunies(self):
        series = {
            g._cle_serie("Brazil Underground"):
                self._serie("Brazil Underground", [6]),
            g._cle_serie("Gay Treasure Island TIM Fuck Brazil Underground"):
                self._serie("Gay Treasure Island TIM Fuck Brazil "
                            "Underground", [1, 2, 3]),
        }
        assert g._fusionner_series(series) == 1
        assert len(series) == 1
        restante = next(iter(series.values()))
        assert restante["nom"] == "Brazil Underground", \
            "le nom le plus court est retenu"
        assert len(restante["parties"]) == 4

    def test_numeros_en_conflit_bloquent(self):
        """Un même numéro des deux côtés : deux films distincts."""
        series = {
            g._cle_serie("Brazil Underground"):
                self._serie("Brazil Underground", [1]),
            g._cle_serie("Autre Chose Brazil Underground"):
                self._serie("Autre Chose Brazil Underground", [1, 2]),
        }
        assert g._fusionner_series(series) == 0
        assert len(series) == 2

    def test_studios_incompatibles_bloquent(self):
        series = {
            g._cle_serie("Brazil Underground"):
                self._serie("Brazil Underground", [6], studios=("1",)),
            g._cle_serie("Prefixe Long Brazil Underground"):
                self._serie("Prefixe Long Brazil Underground", [1],
                            studios=("2",)),
        }
        assert g._fusionner_series(series) == 0

    def test_series_sans_rapport_intactes(self):
        series = {
            g._cle_serie("Stepfather's Secret"):
                self._serie("Stepfather's Secret", [1, 2]),
            g._cle_serie("Bullfight Edition"):
                self._serie("Bullfight Edition", [1, 2]),
        }
        assert g._fusionner_series(series) == 0
        assert len(series) == 2

    def test_le_rapprochement_est_trace(self):
        series = {
            g._cle_serie("Brazil Underground"):
                self._serie("Brazil Underground", [6]),
            g._cle_serie("Gay TIM Fuck Brazil Underground"):
                self._serie("Gay TIM Fuck Brazil Underground", [1]),
        }
        g._fusionner_series(series)
        restante = next(iter(series.values()))
        assert restante.get("rapproche"), \
            "l'autre écriture doit rester mentionnée dans le motif"
