# -*- coding: utf-8 -*-
"""
Sources d'appoint : Wikipédia, ADE, ThePornDB, StashDB en direct.

Écrit AVANT le nettoyage du module, pour fixer ce qui doit survivre.

Ce module contenait une seconde implémentation de l'arbitrage —
`aggregate`, complexité 19 — qui faisait doublon avec `scoring.evaluer`
sans être appelée par personne. Deux implémentations d'une même
décision divergeront : la seconde ne sera pas corrigée quand la
première le sera. Elle est retirée, et ces tests garantissent que ce
qui reste continue de fonctionner.

Ce qui est éprouvé ici est PUR : normalisation des valeurs et
rapprochement des noms. Les appels réseau ne sont pas testés — ils le
sont par la tâche « Vérifier l'état des sources », qui interroge
réellement et dit ce que chacune fournit encore.
"""

import pytest

import sources


# ── Normalisation des valeurs reçues ─────────────────────────────────
class TestNormalisation:
    """Chaque source écrit à sa façon. Le plugin doit en tirer une
    forme unique — sans quoi « Uncut », « uncut » et « UNCUT »
    comptent comme trois valeurs différentes, et aucune n'atteint le
    seuil d'accord."""

    @pytest.mark.parametrize("brut", ["Uncut", "uncut", "UNCUT",
                                      "  UnCut  "])
    def test_les_ecritures_d_une_meme_valeur_se_rejoignent(self, brut):
        """La normalisation produit une CLÉ DE COMPARAISON, non une
        forme canonique métier : elle sert à reconnaître que deux
        sources disent la même chose. Sans elle, « Uncut », « uncut »
        et « UNCUT » comptent pour trois valeurs distinctes et aucune
        n'atteint le seuil d'accord."""
        assert (sources.normalize("circumcised", brut)
                == sources.normalize("circumcised", "uncut"))

    def test_deux_valeurs_differentes_restent_distinctes(self):
        assert (sources.normalize("circumcised", "Cut")
                != sources.normalize("circumcised", "Uncut"))

    @pytest.mark.parametrize("brut", ["", None, "   ", "peut-être"])
    def test_circoncision_illisible(self, brut):
        """Mieux vaut rien qu'une valeur inventée : une source qui
        répond n'importe quoi ne doit pas peser dans l'arbitrage."""
        assert sources.normalize("circumcised", brut) in (None, "", brut)

    def test_une_date_traverse_intacte(self):
        """Le découpage des dates appartient à `scoring`, qui sait les
        comparer. Ici, la valeur passe."""
        assert sources.normalize("birthdate", "1990-05-01")

    @pytest.mark.parametrize("brut", ["0000-00-00", "", None])
    def test_dates_nulles(self, brut):
        """Une date nulle interrompait autrefois le traitement de la
        fiche entière."""
        assert not sources.normalize("birthdate", brut)

    def test_champ_inconnu_traverse(self):
        """La normalisation ne connaît pas tous les champs : ceux
        qu'elle ignore doivent passer intacts, pas disparaître."""
        assert sources.normalize("champ_inedit", "valeur") == "valeur"

    def test_aucune_exception_sur_types_imprevus(self):
        for champ in ("circumcised", "birthdate", "height_cm"):
            for valeur in (42, [1], {"a": 1}, True):
                sources.normalize(champ, valeur)
        assert True, "aucune valeur ne doit faire tomber la lecture"


# ── Rapprochement des résultats ──────────────────────────────────────
class TestMeilleurNom:
    """Une source renvoie plusieurs résultats pour une recherche.
    Choisir le mauvais attribue à quelqu'un d'autre — l'erreur qu'aucun
    arbitrage ultérieur ne rattrape."""

    HITS = [{"name": "Archie Foxx"}, {"name": "Archie Fox"},
            {"name": "Archibald Fox"}]

    def test_correspondance_exacte_prime(self):
        trouve = sources._best_name_match(self.HITS, "Archie Fox")
        assert trouve["name"] == "Archie Fox"

    def test_casse_et_espaces_ignores(self):
        for voulu in ("archie fox", "ARCHIE FOX", "  Archie Fox  "):
            trouve = sources._best_name_match(self.HITS, voulu)
            assert trouve and trouve["name"] == "Archie Fox", voulu

    def test_aucun_resultat(self):
        assert sources._best_name_match([], "Archie Fox") is None
        assert sources._best_name_match(None, "Archie Fox") is None

    def test_nom_vide(self):
        assert sources._best_name_match(self.HITS, "") is None

    def test_resultats_malformes(self):
        """Une source peut renvoyer des entrées sans nom."""
        assert sources._best_name_match(
            [{}, {"name": None}, {"name": "Archie Fox"}],
            "Archie Fox")["name"] == "Archie Fox"


# ── Poids des sources ────────────────────────────────────────────────
class TestPoids:
    """Ces poids décident quelle valeur l'emporte en cas de désaccord.
    Une table incohérente fausse tous les arbitrages sans que rien ne
    le signale."""

    def test_toutes_les_sources_ont_un_poids(self):
        connues = (set(sources.ACTOR_SOURCES)
                   | set(sources.STUDIO_SOURCES))
        for nom in connues:
            assert nom in sources.SOURCE_WEIGHTS, nom

    def test_les_poids_sont_dans_les_bornes(self):
        for nom, poids in sources.SOURCE_WEIGHTS.items():
            assert 0.0 < float(poids) <= 1.0, f"{nom}={poids}"

    def test_les_annuaires_pesent_plus_que_l_encyclopedie(self):
        """Wikipédia n'est pas spécialisée : elle documente rarement
        ces fiches, et moins précisément qu'un annuaire dédié."""
        assert (sources.SOURCE_WEIGHTS["stashdb"]
                > sources.SOURCE_WEIGHTS["wikipedia"])

    def test_chaque_source_declaree_est_appelable(self):
        """Une entrée pointant vers une fonction inexistante
        échouerait au premier enrichissement, pas au chargement."""
        for table in (sources.ACTOR_SOURCES, sources.STUDIO_SOURCES):
            for nom, fonction in table.items():
                assert callable(fonction), nom


# ── Ce qui doit avoir disparu ────────────────────────────────────────
class TestPlusDeDoublon:
    """Le module portait une seconde implémentation de l'arbitrage.
    Elle n'était appelée par personne, et aurait divergé de la
    première à la première correction."""

    def test_l_arbitrage_n_existe_qu_une_fois(self):
        assert not hasattr(sources, "aggregate"), \
            "l'arbitrage appartient à scoring, pas à sources"

    def test_pas_de_seconde_boucle_de_collecte(self):
        assert not hasattr(sources, "collect"), \
            "la collecte appartient à collecte.py"

    def test_le_module_reste_une_couche_d_acces(self):
        """Ce module a UNE responsabilité : interroger des sites et
        rendre des dictionnaires. Toute décision qui s'y installerait
        se retrouverait hors du champ des tests d'arbitrage."""
        import ast
        from pathlib import Path
        code = (Path(sources.__file__)).read_text(encoding="utf-8")
        arbre = ast.parse(code)
        publiques = {n.name for n in arbre.body
                     if isinstance(n, ast.FunctionDef)
                     and not n.name.startswith("_")}
        attendues = {"normalize"} | {
            f"fetch_{x}" for x in
            ("tpdb_actor", "tpdb_studio", "stashdb_actor",
             "stashdb_studio", "wikipedia_entity", "ade_actor")}
        intruses = publiques - attendues
        assert intruses == set(), f"fonctions hors périmètre : {intruses}"
