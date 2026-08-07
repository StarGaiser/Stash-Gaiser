# -*- coding: utf-8 -*-
"""
Comparaison de noms : rapprochement de fiches et notation des doublons.

Chaque cas vient d'une situation réelle rencontrée dans la collection.
Les faux positifs comptent autant que les vrais : fusionner deux fiches
distinctes est irréversible.
"""

import similarite as s


# ── Normalisation ────────────────────────────────────────────────────
class TestNormalisation:

    def test_ponctuation_et_casse_ignorees(self):
        assert s._sim_cles("J.D. Phoenix")[0] == s._sim_cles("JD Phoenix")[0]
        assert s._sim_cles("Tony D'Angelo")[0] == s._sim_cles("Tony DAngelo")[0]
        assert s._sim_cles("Johnny V.")[0] == s._sim_cles("Johnny V")[0]

    def test_accents_reduits(self):
        assert s._sim_cles("Björn Söder")[0] == s._sim_cles("Bjorn Soder")[0]

    def test_prenom_compose_reste_solidaire(self):
        """Le trait d'union soude : « Jean-Daniel » est un jeton, pas
        deux. La clé plate restant identique, « Jean-Daniel Cadinot »
        et « Jean Daniel Cadinot » se rapprochent malgré tout."""
        _plat, jetons = s._sim_cles("Jean-Daniel Cadinot")
        assert jetons == ["jeandaniel", "cadinot"]
        assert s._sim_cles("Jean-Daniel Cadinot")[0] \
            == s._sim_cles("Jean Daniel Cadinot")[0]

    def test_nom_vide_ne_casse_pas(self):
        assert s._sim_cles("")[0] == ""
        assert s._sim_cles(None)[0] == ""


# ── Notation des doublons ────────────────────────────────────────────
class TestNoteDoublon:
    """Les seuils comptent : 7,5 déclenche l'application automatique,
    9,0 autorise la fusion entre fiches du référentiel."""

    def _note(self, a, b):
        return s._score_doublon(s._sim_cles(a), s._sim_cles(b))[0]

    def test_identiques_apres_normalisation(self):
        assert self._note("Tony D'Angelo", "Tony DAngelo") >= 9.5

    def test_suffixe_numerique_artefact_import(self):
        # « Archie 18969 » vient d'un identifiant de source
        assert self._note("Archie", "Archie 18969") >= 9.0

    def test_prenom_et_initiale(self):
        note = self._note("Rogan Richards", "Rogan R")
        assert 5.0 <= note < 7.5, "à soumettre, pas à fusionner"

    def test_noms_distincts_non_signales(self):
        assert self._note("Dato Foland", "Cole Connor") == 0

    def test_prenom_commun_ne_suffit_pas(self):
        """Deux interprètes peuvent partager un prénom."""
        assert self._note("Jack Emhoff", "Jack Hunter") < 7.5

    def test_note_bornee(self):
        for a, b in [("X", "X"), ("Alexandre Dupont", "Alex Dupond"),
                     ("", "")]:
            note = self._note(a, b)
            assert 0 <= note <= 10


# ── Choix du canonique ───────────────────────────────────────────────
class TestCanonique:

    def _fiche(self, nom, tags=(), **champs):
        f = {"id": nom, "name": nom,
             "tags": [{"name": t} for t in tags]}
        f.update(champs)
        return f

    def test_le_referentiel_absorbe_la_fiche_creee(self):
        cree = self._fiche("Doublon", tags=["Gaizer:créé"])
        ref = self._fiche("Original")
        canon, doub = s._canonique_de(ref, cree, "Gaizer:créé")
        assert canon["name"] == "Original"
        assert doub["name"] == "Doublon"

    def test_ordre_des_arguments_indifferent(self):
        cree = self._fiche("Doublon", tags=["Gaizer:créé"])
        ref = self._fiche("Original")
        assert s._canonique_de(cree, ref, "Gaizer:créé")[0]["name"] \
            == "Original"

    def test_entre_deux_creees_la_plus_fournie_gagne(self):
        pauvre = self._fiche("A", tags=["Gaizer:créé"])
        riche = self._fiche("B", tags=["Gaizer:créé"],
                            details="une biographie", birthdate="1984-10-21",
                            country="FR")
        canon, _doub = s._canonique_de(pauvre, riche, "Gaizer:créé")
        assert canon["name"] == "B"

    def test_richesse_croissante(self):
        vide = self._fiche("V")
        rempli = self._fiche("R", details="bio", country="FR")
        assert s._richesse(rempli) > s._richesse(vide)


# ── Exemptions ───────────────────────────────────────────────────────
class TestExemptions:

    def test_liste_lue_depuis_le_champ(self):
        f = {"custom_fields": {"enrich_pas_doublon": '["12", "34"]'}}
        assert s.exemptions_de(f) == {"12", "34"}

    def test_champ_absent(self):
        assert s.exemptions_de({}) == set()

    def test_json_corrompu_ne_leve_pas(self):
        f = {"custom_fields": {"enrich_pas_doublon": "pas du json"}}
        assert s.exemptions_de(f) == set()

    def test_identifiants_numeriques_convertis(self):
        f = {"custom_fields": {"enrich_pas_doublon": "[12, 34]"}}
        assert s.exemptions_de(f) == {"12", "34"}


# ── Recherche de paires ──────────────────────────────────────────────
class TestPairesCandidates:
    """Mécanique commune aux trois détections. Une erreur ici se
    répercute partout."""

    def _jeu(self, noms):
        objets = [{"id": str(i), "name": n} for i, n in enumerate(noms)]
        cles = {str(i): s._sim_cles(n) for i, n in enumerate(noms)}
        alias = {str(i): set() for i in range(len(noms))}
        return objets, cles, alias

    def test_paire_evidente_trouvee(self):
        objets, cles, alias = self._jeu(["Archie", "Archie 18969"])
        paires = s.paires_candidates(objets, cles, alias,
                                     lambda f: set())
        assert len(paires) == 1

    def test_aucune_paire_entre_noms_distincts(self):
        objets, cles, alias = self._jeu(["Dato Foland", "Cole Connor"])
        assert s.paires_candidates(objets, cles, alias,
                                   lambda f: set()) == {}

    def test_seuil_minimal_respecte(self):
        objets, cles, alias = self._jeu(["Rogan Richards", "Rogan R"])
        assert s.paires_candidates(objets, cles, alias, lambda f: set(),
                                   note_mini=9.0) == {}
        assert s.paires_candidates(objets, cles, alias, lambda f: set(),
                                   note_mini=0.0) != {}

    def test_alias_rapproche_deux_fiches(self):
        objets, cles, alias = self._jeu(["Mister X", "Monsieur Y"])
        alias["1"] = {s._sim_cles("Mister X")[0]}
        paires = s.paires_candidates(objets, cles, alias,
                                     lambda f: set())
        assert len(paires) == 1
        assert paires[("0", "1")][2] >= 8.5

    def test_exemption_ecarte_la_paire(self):
        objets, cles, alias = self._jeu(["Archie", "Archie 18969"])
        assert s.paires_candidates(objets, cles, alias,
                                   lambda f: {"0", "1"}) == {}

    def test_restriction_a_un_sous_ensemble(self):
        """La détection ne soupçonne le référentiel que face à une
        fiche créée par le plugin."""
        objets, cles, alias = self._jeu(["Archie", "Archie 18969"])
        assert s.paires_candidates(objets, cles, alias, lambda f: set(),
                                   restreindre_a=set()) == {}
        assert s.paires_candidates(objets, cles, alias, lambda f: set(),
                                   restreindre_a={"1"}) != {}

    def test_chaque_paire_une_seule_fois(self):
        objets, cles, alias = self._jeu(["Tom", "Tom", "Tom"])
        paires = s.paires_candidates(objets, cles, alias,
                                     lambda f: set())
        assert len(paires) == 3          # 3 combinaisons, pas 6
        for (a, b) in paires:
            assert a < b, "les paires sont ordonnées, donc uniques"

    def test_collection_vide(self):
        assert s.paires_candidates([], {}, {}, lambda f: set()) == {}
