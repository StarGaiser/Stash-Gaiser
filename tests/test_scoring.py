# -*- coding: utf-8 -*-
"""
Moteur de notation : familles, fiabilité, détecteurs de biais.

C'est la raison d'être du plugin — ce qui le distingue d'un simple
recopiage de la première source venue. Un défaut ici dégrade
silencieusement TOUS les enrichissements, sans jamais lever d'erreur :
les fiches se remplissent, mais avec les mauvaises valeurs.

Trois convictions sont vérifiées ici :
  1. trois copies d'une même fiche ne valent pas trois confirmations ;
  2. un site commercial est juge et partie sur ce qui le vend ;
  3. les erreurs des sources ont une DIRECTION — on rajeunit, on
     agrandit, jamais l'inverse.
"""

import scoring


CFG = scoring.DEFAUTS


def _note_de(candidats, valeur):
    for c in candidats:
        if str(c["valeur"]) == str(valeur):
            return c["note"]
    raise AssertionError(f"valeur « {valeur} » absente des candidats")


def _gagnant(candidats):
    return candidats[0]["valeur"]


# ── Familles de sources ──────────────────────────────────────────────
class TestFamilles:
    """Men, Bromo et SeanCody appartiennent au même groupe éditorial :
    ils republient la même fiche."""

    def test_sources_du_meme_groupe_reunies(self):
        for source in ("men", "bromo", "seancody", "gaywire"):
            assert scoring.famille_de(source, CFG) == "aylo", source

    def test_second_groupe_distinct(self):
        for source in ("falconstudios", "hothouse", "ragingstallion"):
            assert scoring.famille_de(source, CFG) == "gamma", source
        assert scoring.famille_de("men", CFG) \
            != scoring.famille_de("falconstudios", CFG)

    def test_source_isolee_est_sa_propre_famille(self):
        assert scoring.famille_de("iafd", CFG) == "iafd"

    def test_trois_copies_ne_valent_pas_trois_voix(self):
        """Le cœur du dispositif : sans regroupement, une même donnée
        republiée trois fois écraserait une source indépendante."""
        meme_groupe = scoring.evaluer(
            "birthdate",
            {"men": "1990-01-01", "bromo": "1990-01-01",
             "seancody": "1990-01-01"}, CFG)
        groupes_differents = scoring.evaluer(
            "birthdate",
            {"men": "1990-01-01", "falconstudios": "1990-01-01",
             "iafd": "1990-01-01"}, CFG)
        assert _note_de(groupes_differents, "1990-01-01") \
            > _note_de(meme_groupe, "1990-01-01")

    def test_accord_entre_familles_commente(self):
        cands = scoring.evaluer(
            "country", {"iafd": "FR", "stashdb.org": "FR"}, CFG)
        commentaires = " ".join(cands[0]["commentaires"])
        assert "famille" in commentaires.lower()

    def test_bonus_plafonne(self):
        """Cinq familles d'accord ne doivent pas faire exploser la
        note au-delà du barème."""
        cands = scoring.evaluer("country", {
            "iafd": "FR", "gevi": "FR", "stashdb.org": "FR",
            "wikipedia": "FR", "men": "FR", "falconstudios": "FR"}, CFG)
        assert cands[0]["note"] <= 10.0


# ── Types de sources ─────────────────────────────────────────────────
class TestTypes:

    def test_annuaires_editoriaux(self):
        for s in ("iafd", "gevi"):
            assert scoring.type_de(s, CFG) == "editorial", s

    def test_bases_communautaires(self):
        for s in ("stashdb.org", "porndb", "wikipedia"):
            assert scoring.type_de(s, CFG) == "communautaire", s

    def test_site_commercial_par_defaut(self):
        """Une source inconnue est traitée comme un studio : c'est le
        cas le plus fréquent et le moins fiable."""
        assert scoring.type_de("un_studio_quelconque", CFG) == "studio"


# ── Fiabilité par champ ──────────────────────────────────────────────
class TestFiabilite:
    """Une source n'est pas fiable « en général » : elle l'est sur
    certains champs et pas sur d'autres."""

    def test_editorial_meilleur_que_studio_sur_l_etat_civil(self):
        assert scoring.fiabilite("iafd", "birthdate", CFG) \
            > scoring.fiabilite("men", "birthdate", CFG)

    def test_studio_faible_sur_la_biographie(self):
        """Un site commercial rédige sa bio pour vendre."""
        assert scoring.fiabilite("men", "bio", CFG) <= 0.4

    def test_ecart_modere_sur_les_donnees_factuelles(self):
        """Ce test affirmait un écart d'au moins 0,3 sur la taille.
        La mesure l'a démenti : les sites commerciaux concordent avec
        les annuaires dans 71 à 78 % des cas sur les données
        vérifiables. L'écart subsiste, mais modeste."""
        ecart = (scoring.fiabilite("iafd", "height_cm", CFG)
                 - scoring.fiabilite("men", "height_cm", CFG))
        assert 0 < ecart <= 0.25

    def test_ecart_marque_sur_les_textes(self):
        """La méfiance envers le commercial reste entière là où elle
        n'est pas mesurable : une biographie promotionnelle n'a pas de
        valeur de référence."""
        assert scoring.fiabilite("iafd", "bio", CFG) \
            - scoring.fiabilite("men", "bio", CFG) >= 0.4

    def test_champ_inconnu_retombe_sur_un_defaut(self):
        v = scoring.fiabilite("iafd", "champ_inexistant", CFG)
        assert 0 < v <= 1

    def test_fiabilite_toujours_bornee(self):
        for source in ("iafd", "stashdb.org", "men", "ade", "inconnu"):
            for champ in ("birthdate", "height_cm", "bio", "inconnu"):
                v = scoring.fiabilite(source, champ, CFG)
                assert 0 <= v <= 1, (source, champ)

    def test_l_editorial_l_emporte_sur_le_commercial(self):
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1984-10-21", "men": "1990-01-01"},
            CFG)
        assert _gagnant(cands) == "1984-10-21"


# ── Détecteurs de biais ──────────────────────────────────────────────
class TestRajeunissement:
    """Les sites commerciaux rajeunissent leurs interprètes. L'erreur a
    une direction : personne ne se vieillit."""

    def test_date_plus_recente_penalisee(self):
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1984-10-21", "men": "1992-10-21"},
            CFG)
        assert _gagnant(cands) == "1984-10-21"
        rajeuni = _note_de(cands, "1992-10-21")
        assert rajeuni < _note_de(cands, "1984-10-21")

    def test_penalite_commentee(self):
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1984-10-21", "men": "1992-10-21"},
            CFG)
        for c in cands:
            if c["valeur"] == "1992-10-21":
                assert any("rajeuniss" in x.lower()
                           for x in c["commentaires"])

    def test_ecart_dans_la_tolerance_regroupe(self):
        """Un jour d'écart vient d'un fuseau horaire, pas d'un
        mensonge : les deux dates ne forment qu'un seul candidat, et la
        source la plus fiable fournit la valeur retenue."""
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1984-10-21", "men": "1984-10-22"},
            CFG)
        assert len(cands) == 1
        assert cands[0]["valeur"] == "1984-10-21"
        assert set(cands[0]["sources"]) == {"iafd", "men"}
        assert not any("rajeuniss" in x.lower()
                       for x in cands[0]["commentaires"])

    def test_vieillissement_non_penalise(self):
        """La pénalité est directionnelle : une date plus ANCIENNE que
        l'éditorial n'est pas suspecte du même biais."""
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1984-10-21", "men": "1978-01-01"},
            CFG)
        for c in cands:
            if c["valeur"] == "1978-01-01":
                assert not any("rajeuniss" in x.lower()
                               for x in c["commentaires"])


class TestExageration:

    def test_taille_gonflee_penalisee(self):
        cands = scoring.evaluer(
            "height_cm", {"iafd": 178, "men": 188}, CFG)
        assert _note_de(cands, 188) < _note_de(cands, 178)

    def test_petit_ecart_regroupe(self):
        """Deux centimètres d'écart relèvent de la mesure, pas de la
        vantardise : un seul candidat, sans pénalité."""
        cands = scoring.evaluer(
            "height_cm", {"iafd": 178, "men": 180}, CFG)
        assert len(cands) == 1
        assert not any("exagér" in x.lower()
                       for x in cands[0]["commentaires"])

    def test_valeur_plus_basse_non_penalisee(self):
        cands = scoring.evaluer(
            "height_cm", {"iafd": 178, "men": 170}, CFG)
        for c in cands:
            if c["valeur"] == 170:
                assert not any("exagér" in x.lower()
                               for x in c["commentaires"])


class TestIncoherence:
    """Une carrière commencée avant 18 ans signale une donnée fausse,
    et pose un problème qui dépasse la qualité des métadonnées."""

    def test_carriere_avant_dix_huit_ans_penalisee(self):
        contexte = {"years_active": "1998 - 2010"}
        avec = scoring.evaluer("birthdate", {"men": "1985-01-01"},
                               CFG, contexte)
        sans = scoring.evaluer("birthdate", {"men": "1985-01-01"}, CFG)
        assert avec[0]["note"] < sans[0]["note"]
        assert any("incohér" in x.lower() or "18" in x
                   for x in avec[0]["commentaires"])

    def test_carriere_normale_non_penalisee(self):
        contexte = {"years_active": "2010 - 2020"}
        avec = scoring.evaluer("birthdate", {"men": "1985-01-01"},
                               CFG, contexte)
        sans = scoring.evaluer("birthdate", {"men": "1985-01-01"}, CFG)
        assert avec[0]["note"] == sans[0]["note"]


# ── Robustesse ───────────────────────────────────────────────────────
class TestRobustesse:
    """Les valeurs viennent de sources distantes : elles peuvent être
    de n'importe quelle forme."""

    def test_aucune_valeur(self):
        assert scoring.evaluer("birthdate", {}, CFG) == []

    def test_valeurs_vides_ignorees(self):
        cands = scoring.evaluer(
            "country", {"iafd": "", "men": None, "gevi": "FR"}, CFG)
        assert [c["valeur"] for c in cands] == ["FR"]

    def test_date_malformee_ne_leve_pas(self):
        for mauvaise in ("0000-00-00", "pas une date", "1984",
                         "1984-13-45", ""):
            cands = scoring.evaluer(
                "birthdate", {"iafd": "1984-10-21", "men": mauvaise},
                CFG)
            assert isinstance(cands, list)

    def test_taille_aberrante_ne_leve_pas(self):
        for mauvaise in (0, -5, 999, "cent quatre-vingts", None):
            cands = scoring.evaluer(
                "height_cm", {"iafd": 178, "men": mauvaise}, CFG)
            assert isinstance(cands, list)

    def test_carriere_illisible_ne_leve_pas(self):
        for mauvaise in ("depuis toujours", "20xx", "", None):
            cands = scoring.evaluer("birthdate", {"men": "1985-01-01"},
                                    CFG, {"years_active": mauvaise})
            assert isinstance(cands, list)

    def test_notes_toujours_dans_le_bareme(self):
        jeux = [
            {"iafd": "1984-10-21", "men": "1992-01-01"},
            {"men": "1992-01-01"},
            {"iafd": "1984-10-21", "gevi": "1984-10-21",
             "stashdb.org": "1984-10-21", "porndb": "1984-10-21"},
        ]
        for valeurs in jeux:
            for c in scoring.evaluer("birthdate", valeurs, CFG):
                assert 0 <= c["note"] <= 10, (valeurs, c)

    def test_candidats_tries_par_note(self):
        cands = scoring.evaluer(
            "birthdate",
            {"iafd": "1984-10-21", "men": "1992-01-01",
             "gevi": "1984-10-21"}, CFG)
        notes = [c["note"] for c in cands]
        assert notes == sorted(notes, reverse=True)


# ── Sélection d'ensemble ─────────────────────────────────────────────
class TestEvaluerTous:

    def test_champ_deja_rempli_non_propose(self):
        """Rien n'est écrasé : un champ déjà renseigné à la même valeur
        n'a pas à être proposé."""
        raw = {"iafd": {"country": "FR"}}
        res = scoring.evaluer_tous(raw, {"country": "FR"},
                                   {"country"}, CFG)
        assert "country" not in res or res["country"] == []

    def test_champ_vide_complete(self):
        raw = {"iafd": {"country": "FR"}}
        res = scoring.evaluer_tous(raw, {"country": ""},
                                   {"country"}, CFG)
        assert res.get("country")

    def test_desaccord_signale(self):
        raw = {"iafd": {"country": "FR"}}
        res = scoring.evaluer_tous(raw, {"country": "BE"},
                                   {"country"}, CFG)
        assert res.get("country"), \
            "un désaccord doit remonter, pour être signalé"

    def test_champs_hors_perimetre_ignores(self):
        raw = {"iafd": {"country": "FR", "autre": "x"}}
        res = scoring.evaluer_tous(raw, {}, {"country"}, CFG)
        assert "autre" not in res

    def test_sources_vides(self):
        assert scoring.evaluer_tous({}, {}, {"country"}, CFG) == {}


# ── Configuration ────────────────────────────────────────────────────
class TestConfiguration:

    def test_defauts_complets(self):
        for cle in ("familles", "types", "fiabilite", "detecteurs"):
            assert cle in scoring.DEFAUTS

    def test_fichier_absent_donne_les_defauts(self, tmp_path):
        cfg = scoring.charger_config(str(tmp_path))
        assert cfg["familles"] == scoring.DEFAUTS["familles"]

    def test_surcharge_partielle(self, tmp_path):
        """Le fichier ne contient que les écarts : le reste doit
        subsister."""
        (tmp_path / "gaizer_config.yml").write_text(
            "detecteurs:\n  penalite_rajeunissement: 5.0\n",
            encoding="utf-8")
        cfg = scoring.charger_config(str(tmp_path))
        assert cfg["detecteurs"]["penalite_rajeunissement"] == 5.0
        assert cfg["detecteurs"]["penalite_exageration"] == \
            scoring.DEFAUTS["detecteurs"]["penalite_exageration"]
        assert cfg["familles"] == scoring.DEFAUTS["familles"]

    def test_fichier_illisible_donne_les_defauts(self, tmp_path):
        (tmp_path / "gaizer_config.yml").write_text(
            "ceci: [n'est pas: du yaml", encoding="utf-8")
        assert scoring.charger_config(str(tmp_path))["familles"] \
            == scoring.DEFAUTS["familles"]


class TestDetecteursSepares:
    """`evaluer` mêlait la notation générale et quatre détecteurs
    propres à un champ — complexité 42, la pire du projet, sur le code
    dont dépend CHAQUE valeur écrite.

    Ces tests fixent le comportement observable avant le découpage :
    ce qui compte n'est pas la forme du code, mais que les mêmes
    entrées donnent les mêmes notes après."""

    def _cfg(self):
        return scoring.DEFAUTS

    def test_une_date_ancienne_est_preferee(self):
        """Une source qui rajeunit un interprète est un travers connu
        du métier : à fiabilité égale, la date la plus ancienne gagne."""
        cands = scoring.evaluer(
            "birthdate",
            {"iafd": "1978-06-10", "gevi": "1984-06-10"}, self._cfg())
        assert cands[0]["valeur"] == "1978-06-10"

    def test_une_taille_plus_petite_est_preferee(self):
        """Même travers dans l'autre sens : les fiches promotionnelles
        grandissent leurs interprètes."""
        cands = scoring.evaluer(
            "height_cm", {"iafd": "178", "gevi": "183"}, self._cfg())
        assert cands[0]["valeur"] == "178"

    def test_l_accord_de_plusieurs_familles_prime(self):
        """Deux sources indépendantes qui disent la même chose valent
        mieux qu'une seule, même mieux notée."""
        cands = scoring.evaluer(
            "country",
            {"iafd": "FR", "gevi": "FR", "stashdb.org": "BE"},
            self._cfg())
        assert cands[0]["valeur"] == "FR"

    def test_les_notes_restent_bornees(self):
        for champ, valeurs in (
                ("birthdate", {"iafd": "1978-06-10",
                               "gevi": "1984-06-10"}),
                ("height_cm", {"iafd": "178", "gevi": "183"}),
                ("country", {"iafd": "FR"})):
            for c in scoring.evaluer(champ, valeurs, self._cfg()):
                assert 0.0 <= c["note"] <= 10.0, champ

    def test_les_candidats_sont_ordonnes(self):
        cands = scoring.evaluer(
            "height_cm",
            {"iafd": "178", "gevi": "183", "porndb": "178"},
            self._cfg())
        notes = [c["note"] for c in cands]
        assert notes == sorted(notes, reverse=True)

    def test_un_seul_candidat(self):
        cands = scoring.evaluer("country", {"iafd": "FR"}, self._cfg())
        assert len(cands) == 1 and cands[0]["valeur"] == "FR"

    def test_aucune_valeur(self):
        assert scoring.evaluer("country", {}, self._cfg()) == []

    def test_champ_sans_detecteur_dedie(self):
        """La notation générale doit fonctionner sans qu'un détecteur
        propre au champ existe."""
        cands = scoring.evaluer(
            "ethnicity", {"iafd": "Latin", "gevi": "Latin"},
            self._cfg())
        assert cands and cands[0]["valeur"] == "Latin"

    def test_le_detecteur_explique_sa_correction(self):
        """Une note corrigée sans explication est inexploitable :
        l'utilisateur doit pouvoir juger l'arbitrage.

        Le détecteur de rajeunissement ne vise que les sources de
        STUDIO contredisant une source éditoriale — c'est là qu'est le
        travers. Deux sources éditoriales en désaccord ne déclenchent
        rien, et c'est voulu : aucune des deux n'a de motif à mentir."""
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1978-06-10", "men": "1984-06-10"},
            self._cfg())
        suspect = next(c for c in cands if c["valeur"] == "1984-06-10")
        assert suspect["commentaires"], \
            "la pénalité doit dire pourquoi elle s'applique"
        assert "rajeunissement" in " ".join(suspect["commentaires"])

    def test_deux_sources_editoriales_ne_declenchent_rien(self):
        """Le détecteur suppose un MOTIF de mentir. Deux annuaires en
        désaccord n'en ont pas : l'écart est une erreur, pas un
        travers, et le pénaliser fausserait l'arbitrage."""
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1978-06-10", "gevi": "1984-06-10"},
            self._cfg())
        assert all(not c["commentaires"] for c in cands)
