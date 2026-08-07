# -*- coding: utf-8 -*-
"""
Rôles : position et rapport de pouvoir.

Aucune source ne fournit cette information — le plugin ne la devine
jamais. Ce qui est testé, c'est la lecture d'écritures libres et le
refus de ranger de force ce qui n'entre dans aucune case.
"""

import roles


class TestLecture:

    def test_position_seule(self):
        for brut, attendu in [("Versatile", "versatile"),
                              ("Top", "actif"), ("Bottom", "passif"),
                              ("Actif", "actif"), ("passive", "passif")]:
            assert roles.lire(brut)[0] == attendu, brut

    def test_valeur_composee_repartie_sur_deux_axes(self):
        """« Actif Dominant » mélangeait deux notions distinctes, ce
        qui rendait tout filtrage impossible."""
        position, pouvoir = roles.lire("Actif Dominant")
        assert position == "actif"
        assert pouvoir == "dominant"

    def test_expression_longue_prioritaire(self):
        """« Power Bottom » doit être lu en entier, pas réduit au seul
        mot « bottom » rencontré en premier."""
        assert roles.lire("Power Bottom")[0] == "passif"
        assert roles.lire("Versatile Top")[0] == "versatile"

    def test_parentheses_et_ponctuation(self):
        position, pouvoir = roles.lire("Versatile (Dominante Active)")
        assert position == "versatile"
        assert pouvoir == "dominant"

    def test_pouvoir_seul(self):
        for brut in ("sub", "Soumise", "submissive", "esclave"):
            assert roles.lire(brut)[1] == "soumis", brut
        for brut in ("Dominatrice", "Mistress", "dom"):
            assert roles.lire(brut)[1] == "dominant", brut

    def test_valeur_hors_sujet_non_rangee(self):
        """« Réalisatrice / Icone » n'est pas une position : l'inventer
        serait pire que de laisser vide."""
        assert roles.lire("Réalisatrice / Icone") == (None, None)

    def test_valeurs_vides(self):
        for brut in ("", None, "   ", "???"):
            assert roles.lire(brut) == (None, None)


class TestNormalisation:

    def test_ce_qui_n_est_pas_compris_est_conserve(self):
        out = roles.normaliser("Réalisatrice / Icone")
        assert out.get("reste") == "Réalisatrice / Icone"
        assert "position" not in out

    def test_valeur_vide_ne_produit_rien(self):
        assert roles.normaliser("") == {}
        assert roles.normaliser(None) == {}

    def test_sortie_limitee_aux_axes_trouves(self):
        assert set(roles.normaliser("Top")) == {"position"}
        assert set(roles.normaliser("sub")) == {"pouvoir"}


class TestVocabulaire:

    def test_valeurs_canoniques_courtes(self):
        """Une taxonomie fine serait plus juste mais resterait vide :
        mieux vaut trois valeurs renseignées que douze abandonnées."""
        assert len(roles.POSITIONS) == 3
        assert len(roles.POUVOIRS) == 3

    def test_toute_lecture_donne_une_valeur_canonique(self):
        exemples = ["Top", "vers", "Power Bottom", "Actif Dominant",
                    "switch", "Mistress", "total top"]
        for brut in exemples:
            position, pouvoir = roles.lire(brut)
            assert position is None or position in roles.POSITIONS
            assert pouvoir is None or pouvoir in roles.POUVOIRS

    def test_validation(self):
        assert roles.valide("position", "actif")
        assert not roles.valide("position", "dominant")
        assert roles.valide("pouvoir", "soumis")
        assert not roles.valide("pouvoir", "n'importe quoi")


class TestPertinence:
    """La position structure le contenu gay masculin ; le rapport de
    pouvoir vaut partout. L'interface s'en sert pour ne pas afficher un
    champ hors sujet — sans jamais empêcher de le renseigner."""

    def test_pouvoir_pertinent_pour_tous(self):
        for profil in ("", "gay", "hetero", "lesbien", "bi", "trans"):
            assert roles.pertinent("pouvoir", profil), profil

    def test_position_sans_objet_pour_certains_profils(self):
        assert roles.pertinent("position", "gay")
        assert not roles.pertinent("position", "hetero")
        assert not roles.pertinent("position", "lesbien")

    def test_position_affichee_par_defaut(self):
        assert roles.pertinent("position", "")
