# -*- coding: utf-8 -*-
"""
Collecte : normalisation des réponses et rapprochement au référentiel.

Ce module est la frontière entre le dehors et le dedans. Ce qui entre
ici vient de sites tiers : des champs absents, des chaînes vides prises
pour des valeurs, des dates nulles, des noms écrits de six façons.

Deux responsabilités s'y jouent, et l'erreur n'a pas le même coût dans
chacune. NORMALISER mal donne une valeur fausse, qu'un arbitrage
ultérieur peut rattraper. RAPPROCHER mal attribue une scène au mauvais
interprète — et rien ne le rattrape.
"""

import collecte
from faux import FauxStash, faux_contexte, performer, scene, studio


# ── Normalisation des réponses ───────────────────────────────────────
class TestNormalisation:
    """Une source renvoie ce qu'elle veut. Le plugin doit en tirer une
    forme unique sans jamais tomber."""

    def test_chaine_vide_n_est_pas_une_valeur(self):
        """Une chaîne vide comptée comme réponse ferait croire qu'une
        source connaît un champ qu'elle ignore, et fausserait le
        nombre de familles d'accord."""
        sortie = collecte._normalise(
            {"name": "Archie", "country": "", "ethnicity": "   "})
        assert not sortie.get("country")
        assert not sortie.get("ethnicity")

    def test_date_nulle_ecartee(self):
        """« 0000-00-00 » interrompait autrefois le traitement de la
        fiche entière."""
        for nulle in ("0000-00-00", "", "0000", None):
            sortie = collecte._normalise({"birthdate": nulle})
            assert not sortie.get("birthdate"), nulle

    def test_valeurs_absentes(self):
        for entree in ({}, None):
            assert isinstance(collecte._normalise(entree), dict)

    def test_les_champs_connus_sont_conserves(self):
        sortie = collecte._normalise(
            {"name": "Archie Fox", "birthdate": "1990-05-01",
             "country": "FR"})
        assert sortie.get("birthdate") == "1990-05-01"

    def test_types_inattendus_rendus_exploitables(self):
        """Une source qui renvoie un nombre là où un texte est attendu
        ne doit pas faire tomber le lot : la normalisation rend une
        forme utilisable, ou rien."""
        for bizarre in ({"country": 42}, {"birthdate": ["x"]},
                        {"name": {"a": 1}}, {"height": True}):
            assert isinstance(collecte._normalise(bizarre), dict)


class TestUrlNormale:

    def test_formes_equivalentes(self):
        base = collecte._url_normale("https://www.exemple.test/page")
        for variante in ("https://exemple.test/page",
                         "http://www.exemple.test/page/",
                         "HTTPS://WWW.EXEMPLE.TEST/page"):
            assert collecte._url_normale(variante) == base, variante

    def test_urls_differentes_restent_distinctes(self):
        assert (collecte._url_normale("https://a.test/x")
                != collecte._url_normale("https://a.test/y"))

    def test_valeurs_absurdes(self):
        for url in ("", None, "pas une url"):
            assert isinstance(collecte._url_normale(url), str)


class TestNettoyageStudio:
    """Les sources suffixent leurs studios : « Men.com (Network) »,
    « Falcon Studios [US] ». Sans nettoyage, chaque suffixe crée un
    studio de plus."""

    def test_suffixes_retires(self):
        for brut in ("Men.com (Network)", "Men.com [Network]",
                     "Men.com  "):
            assert collecte._nettoie_studio(brut).startswith("Men.com")

    def test_nom_simple_intact(self):
        assert collecte._nettoie_studio("Masqulin") == "Masqulin"

    def test_valeurs_vides(self):
        for brut in ("", None):
            assert isinstance(collecte._nettoie_studio(brut), str)


# ── Rapprochement au référentiel ─────────────────────────────────────
class TestResolution:
    """Attribuer une scène au mauvais interprète ne se rattrape pas :
    aucun arbitrage ultérieur ne le détectera."""

    INDEX = {"archie fox": "1", "archiefox": "1",
             "dean young": "2", "deanyoung": "2"}

    def test_identifiant_connu_prime(self):
        """Quand la source fournit un identifiant, il fait foi : le nom
        peut être écrit autrement."""
        assert collecte._resoudre("Peu importe", "7", self.INDEX) == "7"

    def test_rapprochement_par_nom(self):
        assert collecte._resoudre("Archie Fox", None, self.INDEX) == "1"

    def test_casse_et_espaces_ignores(self):
        for nom in ("archie fox", "ARCHIE FOX", "  Archie Fox  "):
            assert collecte._resoudre(nom, None, self.INDEX) == "1", nom

    def test_nom_inconnu_ne_rapproche_rien(self):
        """Mieux vaut créer une fiche que d'attribuer à la mauvaise."""
        assert not collecte._resoudre("Quelqu'un d'Autre", None,
                                      self.INDEX)

    def test_rapprochement_partiel_refuse(self):
        for nom in ("Archie", "Fox", "Arch"):
            assert not collecte._resoudre(nom, None, self.INDEX), nom

    def test_valeurs_vides(self):
        assert not collecte._resoudre("", None, self.INDEX)
        assert not collecte._resoudre(None, None, {})


class TestMatch:

    def test_correspondance_exacte_choisie(self):
        hits = [{"name": "Archie Foxx"}, {"name": "Archie Fox"}]
        assert collecte._match(hits, "Archie Fox")["name"] == "Archie Fox"

    def test_aucun_resultat(self):
        assert collecte._match([], "Archie Fox") is None
        assert collecte._match(None, "Archie Fox") is None


# ── Lecture de la collection ─────────────────────────────────────────
class TestIndexReferentiel:
    """L'index sert à décider si un nom cité par une source désigne une
    fiche existante. Une entrée manquante crée un doublon ; une entrée
    erronée attribue une scène à un tiers."""

    def test_les_noms_et_alias_sont_indexes(self):
        st = FauxStash(performers=[
            performer(1, "Archie Fox", alias_list=["A. Fox"])])
        ctx = faux_contexte({}, st)
        idx_perfs, _idx_studios = collecte._index_referentiel(ctx)
        assert idx_perfs.get("archie fox") == "1"
        assert idx_perfs.get("a. fox") == "1"

    def test_forme_compacte_indexee(self):
        """« ArchieFox » écrit sans espace doit retrouver la fiche."""
        st = FauxStash(performers=[performer(1, "Archie Fox")])
        ctx = faux_contexte({}, st)
        idx_perfs, _ = collecte._index_referentiel(ctx)
        assert idx_perfs.get("archiefox") == "1"

    def test_studios_indexes(self):
        st = FauxStash(studios=[studio(1, "Falcon Studios")])
        ctx = faux_contexte({}, st)
        _, idx_studios = collecte._index_referentiel(ctx)
        assert idx_studios.get("falcon studios") == "1"

    def test_collection_vide(self):
        ctx = faux_contexte({}, FauxStash())
        idx_perfs, idx_studios = collecte._index_referentiel(ctx)
        assert idx_perfs == {} and idx_studios == {}

    def test_fiche_sans_nom_ignoree(self):
        """Une fiche sans nom indexée sous la clé vide rapprocherait
        n'importe quoi."""
        st = FauxStash(performers=[performer(1, "")])
        ctx = faux_contexte({}, st)
        idx_perfs, _ = collecte._index_referentiel(ctx)
        assert "" not in idx_perfs


class TestStatistiques:
    """Les statistiques nourrissent la présentation et les
    recommandations : elles décrivent la collection, pas les sources."""

    def test_partenaires_et_studios_comptes(self):
        st = FauxStash(
            performers=[performer(1, "Archie"), performer(2, "Dean")],
            studios=[studio(5, "Masqulin")],
            scenes=[scene(10, "S1", studio={"id": "5"},
                          performers=[{"id": "1"}, {"id": "2"}])])
        ctx = faux_contexte({}, st)
        stats = collecte.stats_collection(ctx, st.performers["1"])
        assert isinstance(stats, dict)

    def test_fiche_sans_scene(self):
        st = FauxStash(performers=[performer(1, "Archie")])
        ctx = faux_contexte({}, st)
        assert isinstance(
            collecte.stats_collection(ctx, st.performers["1"]), dict)

    def test_studio_sans_scene(self):
        st = FauxStash(studios=[studio(1, "Masqulin")])
        ctx = faux_contexte({}, st)
        assert isinstance(collecte.stats_studio(ctx, "1"), dict)


class TestCollecteSansSource:
    """Sans stash-box ni scraper configuré, la collecte doit rendre un
    résultat vide — pas lever."""

    def test_interprete(self):
        ctx = faux_contexte({}, FauxStash())
        raw, urls = collecte.collecter_stash(ctx, "Archie Fox")
        assert raw == {} and urls == []

    def test_studio(self):
        ctx = faux_contexte({}, FauxStash())
        assert collecte.collecter_studio(ctx, "Masqulin") == {}

    def test_scene(self):
        st = FauxStash(scenes=[scene(10, "Une scène")])
        ctx = faux_contexte({}, st)
        assert isinstance(
            collecte.collecter_scene(ctx, st.scenes["10"]), dict)

    def test_passe_url_sans_url(self):
        ctx = faux_contexte({}, FauxStash())
        assert collecte.passe_url(ctx, {}, []) in ({}, None)
