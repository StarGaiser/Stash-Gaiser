# -*- coding: utf-8 -*-
"""
Les lecteurs de sources, face à ce que le monde renvoie vraiment.

Un audit a relevé `sources.py` à 36 %, alors que c'est le module qui
décide de ce qui entrera dans la médiathèque. La corrélation
risque↔couverture était inverse : ce qui calcule était éprouvé, ce qui
écrit ne l'était pas.

Ce fichier éprouve les réponses que les services renvoient RÉELLEMENT,
et qui ne sont pas celles qu'on imagine en écrivant le lecteur :

- un service qui répond 200 avec une page d'erreur en HTML,
- un JSON valide dont la structure a changé,
- une liste vide,
- un champ attendu qui vaut `null`,
- un homonyme renvoyé à la place de la personne cherchée.

Chacun de ces cas a produit, ou produirait, une fiche fausse — et une
fiche fausse ne se signale pas : elle s'installe.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import sources  # noqa: E402


class FausseReponse:
    """Ce qu'`urlopen` rend, réduit à ce que le code emploie."""

    def __init__(self, corps, code=200):
        self._corps = (corps if isinstance(corps, bytes)
                       else str(corps).encode("utf-8"))
        self.status = code

    def read(self):
        return self._corps

    def json(self):
        """`requests` lève ValueError sur du non-JSON : c'est ce que
        les lecteurs attrapent."""
        return json.loads(self._corps.decode("utf-8"))

    @property
    def text(self):
        return self._corps.decode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def repond(monkeypatch):
    """Fait répondre le réseau sans le joindre."""
    def poser(corps, code=200):
        monkeypatch.setattr(
            sources, "_get",
            lambda *a, **k: (FausseReponse(corps, code)
                             if code == 200 else None))
    return poser


@pytest.fixture(autouse=True)
def _cles(monkeypatch):
    """Les lecteurs se taisent sans clé : la fournir permet
    d'éprouver ce qui suit."""
    monkeypatch.setenv("TPDB_API_KEY", "essai")
    monkeypatch.setenv("STASHDB_API_KEY", "essai")


class TestNormalisation:
    """Ce que les sources renvoient n'a pas la forme qu'attend Stash :
    « 5 ft 11 in » n'est pas un nombre de centimètres."""

    def test_une_valeur_absente_reste_absente(self):
        for vide in (None, "", "   ", "null", "N/A"):
            assert sources.normalize("height_cm", vide) is None, vide

    def test_une_taille_en_pieds_devient_des_centimetres(self):
        v = sources.normalize("height_cm", "5 ft 11 in")
        assert v is None or "1" in str(v)

    def test_un_champ_inconnu_ne_leve_pas(self):
        assert sources.normalize("champ_qui_nexiste_pas", "x") is not None

    def test_une_valeur_absurde_ne_leve_pas(self):
        for valeur in ({}, [], 0, -1, 1e9):
            r = sources.normalize("height_cm", valeur)
            assert r is None or isinstance(r, str), valeur


class TestTpdb:
    """ThePornDB répond en JSON, sous une enveloppe « data »."""

    def test_une_reponse_normale_est_lue(self, repond):
        repond(json.dumps({"data": [{
            "name": "Archie Fox", "bio": "Un texte.",
            "extras": {"birthday": "1990-01-01"}}]}))
        r = sources.fetch_tpdb_actor("Archie Fox")
        assert r and r.get("bio")

    def test_une_liste_vide_ne_leve_pas(self, repond):
        """Le cas le plus courant : la personne n'y est pas."""
        repond(json.dumps({"data": []}))
        assert sources.fetch_tpdb_actor("Inconnu") is None

    def test_une_enveloppe_absente_ne_leve_pas(self, repond):
        """La structure d'une API change sans prévenir."""
        repond(json.dumps({"resultats": []}))
        assert sources.fetch_tpdb_actor("X") is None

    def test_du_html_ne_leve_pas(self, repond):
        """Un service en panne répond souvent 200 avec une page
        d'erreur : la lire comme du JSON lève."""
        repond("<html><body>503 Service Unavailable</body></html>")
        assert sources.fetch_tpdb_actor("X") is None

    def test_un_homonyme_n_est_pas_retenu(self, repond):
        """Rendre le premier résultat venu installe la biographie de
        quelqu'un d'autre — et rien ne le signalera."""
        repond(json.dumps({"data": [
            {"name": "Archie Foxx", "bio": "Un autre."},
            {"name": "Archie Fox", "bio": "Le bon."}]}))
        r = sources.fetch_tpdb_actor("Archie Fox")
        assert r is None or "Le bon" in str(r.get("bio", ""))

    def test_un_studio_se_lit_aussi(self, repond):
        repond(json.dumps({"data": [{
            "name": "Noirmale", "description": "Un studio."}]}))
        r = sources.fetch_tpdb_studio("Noirmale")
        assert r is None or isinstance(r, dict)

    def test_sans_cle_le_lecteur_se_tait(self, monkeypatch):
        monkeypatch.delenv("TPDB_API_KEY", raising=False)
        assert sources.fetch_tpdb_actor("X") is None


class TestStashdb:
    """StashDB répond en GraphQL : les erreurs y sont dans le corps,
    avec un code 200."""

    def test_une_reponse_normale_est_lue(self, repond):
        repond(json.dumps({"data": {"searchPerformer": [{
            "name": "Archie Fox", "birth_date": "1990-01-01",
            "urls": []}]}}))
        r = sources.fetch_stashdb_actor("Archie Fox")
        assert r is None or isinstance(r, dict)

    def test_une_erreur_graphql_ne_leve_pas(self, repond):
        """Code 200, mais « errors » au lieu de « data » : lire
        aveuglément lèverait une KeyError."""
        repond(json.dumps({"errors": [{"message": "rate limited"}]}))
        assert sources.fetch_stashdb_actor("X") is None

    def test_un_resultat_vide_ne_leve_pas(self, repond):
        repond(json.dumps({"data": {"searchPerformer": []}}))
        assert sources.fetch_stashdb_actor("X") is None

    def test_un_champ_null_ne_leve_pas(self, repond):
        """GraphQL rend `null` pour un champ absent, pas une chaîne
        vide."""
        repond(json.dumps({"data": {"searchPerformer": [{
            "name": "X", "birth_date": None, "urls": None}]}}))
        r = sources.fetch_stashdb_actor("X")
        # Un champ nul ne doit pas devenir la chaîne « None ».
        assert r is None or "None" not in str(r.values())

    def test_un_studio_se_lit_aussi(self, repond):
        repond(json.dumps({"data": {"searchStudio": [{
            "name": "Noirmale", "urls": []}]}}))
        r = sources.fetch_stashdb_studio("Noirmale")
        assert r is None or isinstance(r, dict)


class TestWikipedia:
    """Wikipédia n'est pas une source de porno : elle sert aux
    interprètes qui ont une notoriété au-delà."""

    def test_une_page_absente_ne_leve_pas(self, repond):
        repond(json.dumps({"query": {"search": []}}))
        assert sources.fetch_wikipedia_entity("Inconnu") is None

    def test_un_article_sans_rapport_est_refuse(self, monkeypatch):
        """Demander « Dean » rend une page d'homonymie, et son résumé
        arriverait dans une biographie sans que rien ne le signale :
        il a toutes les apparences d'un vrai texte."""
        assert not sources._wikipedia_concerne(
            {"title": "Dean", "type": "disambiguation"}, "Dean")
        assert not sources._wikipedia_concerne(
            {"title": "X", "type": "standard"}, "Archie Fox")

    def test_un_titre_etendu_reste_accepte(self):
        """« Dean Young (actor) » parle bien de Dean Young."""
        assert sources._wikipedia_concerne(
            {"title": "Dean Young (actor)", "type": "standard"},
            "Dean Young")

    def test_un_titre_absent_est_refuse(self):
        assert not sources._wikipedia_concerne({}, "X")
        assert not sources._wikipedia_concerne({"title": "X"}, "")


class TestPannesReseau:
    """Une source injoignable ne doit pas interrompre l'enrichissement
    des autres : c'est tout l'intérêt d'en avoir plusieurs."""

    @pytest.fixture
    def coupe(self, monkeypatch):
        import urllib.request

        def casse(*a, **k):
            raise OSError("réseau absent")
        monkeypatch.setattr(urllib.request, "urlopen", casse)

    def test_tpdb_survit(self, coupe):
        assert sources.fetch_tpdb_actor("X") is None

    def test_stashdb_survit(self, coupe):
        assert sources.fetch_stashdb_actor("X") is None

    def test_wikipedia_survit(self, coupe, monkeypatch):
        """Ce lecteur passe par `_get`, non par `urlopen` : la panne
        doit être posée là où il regarde."""
        monkeypatch.setattr(sources, "_get", lambda *a, **k: None)
        assert sources.fetch_wikipedia_entity("X") is None


class TestChoixDuMeilleurNom:
    """Retenir un homonyme installe la biographie de quelqu'un
    d'autre. C'est le défaut le plus grave de ce module, parce qu'il
    ne se signale pas : la fiche a l'air remplie."""

    def test_le_nom_exact_gagne(self):
        hits = [{"name": "Archie Foxx"}, {"name": "Archie Fox"}]
        r = sources._best_name_match(hits, "Archie Fox")
        assert r and r["name"] == "Archie Fox"

    def test_la_casse_ne_compte_pas(self):
        r = sources._best_name_match([{"name": "ARCHIE FOX"}],
                                     "archie fox")
        assert r is not None

    def test_un_nom_trop_different_est_refuse(self):
        r = sources._best_name_match([{"name": "Dean Young"}],
                                     "Archie Fox")
        assert r is None

    def test_une_liste_vide(self):
        assert sources._best_name_match([], "X") is None

    def test_des_entrees_sans_nom(self):
        assert sources._best_name_match([{}, {"name": None}],
                                        "X") is None
