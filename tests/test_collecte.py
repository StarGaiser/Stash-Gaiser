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

import pytest

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


class TestCollecteAvecCache:
    """Le cache s'est glissé entre la collecte et les sources. C'est
    le chemin le plus emprunté du plugin — une passe complète le
    traverse une fois par source et par fiche — et il n'était pas
    éprouvé.

    Deux garanties comptent. Une réponse mémorisée doit être
    indiscernable d'une réponse fraîche du point de vue de
    l'arbitrage. Et un cache qui tombe doit dégrader vers une collecte
    normale, jamais interrompre."""

    @pytest.fixture(autouse=True)
    def cache_isole(self, tmp_path, monkeypatch):
        import cache
        monkeypatch.setattr(cache, "DOSSIER", tmp_path / "c")

    def _monde(self, reponse=None, **reglages):
        base = {"useStashBoxes": False}
        base.update(reglages)
        st = FauxStash()
        st.scrape_reponse = reponse
        ctx = faux_contexte(base, st)
        ctx.args = {}
        return st, ctx

    def test_une_source_n_est_interrogee_qu_une_fois(self, monkeypatch):
        """Sur une collection d'un millier de fiches, réinterroger ce
        qu'on sait déjà coûte des heures et sollicite des services
        tiers pour rien."""
        appels = []
        st, ctx = self._monde()

        def compter(requete, variables=None):
            if "scrapeSinglePerformer" in str(requete):
                appels.append(1)
                return {"scrapeSinglePerformer": [
                    {"name": "Archie Fox", "country": "FR"}]}
            return st.call_GQL(requete, variables)
        monkeypatch.setattr(ctx.stash, "call_GQL", compter)
        monkeypatch.setattr(ctx, "scrapers", lambda: ["iafd"])
        collecte.collecter_stash(ctx, "Archie Fox")
        collecte.collecter_stash(ctx, "Archie Fox")
        assert len(appels) == 1

    def test_une_reponse_memorisee_est_identique(self, monkeypatch):
        st, ctx = self._monde()
        monkeypatch.setattr(ctx, "scrapers", lambda: ["iafd"])
        monkeypatch.setattr(
            ctx.stash, "call_GQL",
            lambda q, v=None: {"scrapeSinglePerformer": [
                {"name": "Archie Fox", "country": "FR",
                 "birthdate": "1990-05-01"}]}
            if "scrapeSingle" in str(q) else {})
        premier, _ = collecte.collecter_stash(ctx, "Archie Fox")
        second, _ = collecte.collecter_stash(ctx, "Archie Fox")
        assert premier == second

    def test_un_cache_desactive_reinterroge(self, monkeypatch):
        """Zéro jour force des réponses fraîches : l'utilisateur doit
        pouvoir passer outre quand il soupçonne une source d'avoir
        changé."""
        appels = []
        st, ctx = self._monde(cacheJours="0")
        monkeypatch.setattr(ctx, "scrapers", lambda: ["iafd"])

        def compter(q, v=None):
            if "scrapeSingle" in str(q):
                appels.append(1)
                return {"scrapeSinglePerformer": [
                    {"name": "Archie Fox", "country": "FR"}]}
            return {}
        monkeypatch.setattr(ctx.stash, "call_GQL", compter)
        collecte.collecter_stash(ctx, "Archie Fox")
        collecte.collecter_stash(ctx, "Archie Fox")
        assert len(appels) == 2

    def test_un_cache_illisible_ne_bloque_pas(self, monkeypatch,
                                              tmp_path):
        """Une défaillance du cache doit dégrader vers une collecte
        normale : elle ne peut pas empêcher d'enrichir."""
        st, ctx = self._monde()
        monkeypatch.setattr(ctx, "scrapers", lambda: ["iafd"])
        monkeypatch.setattr(
            ctx.stash, "call_GQL",
            lambda q, v=None: {"scrapeSinglePerformer": [
                {"name": "Archie Fox", "country": "FR"}]}
            if "scrapeSingle" in str(q) else {})
        collecte.collecter_stash(ctx, "Archie Fox")
        # Corrompre TOUT le cache, y compris la trace d'échec : c'est
        # le cas réel — un disque plein, une écriture interrompue —
        # et il ne doit pas empêcher d'enrichir.
        for f in (tmp_path / "c").rglob("*.json"):
            f.write_text("{cassé", encoding="utf-8")
        raw, _urls = collecte.collecter_stash(ctx, "Archie Fox")
        assert raw, "la collecte doit aboutir malgré le cache"

    def test_une_source_en_panne_n_est_pas_reessayee(self, monkeypatch):
        """Un scraper qui échoue coûte son délai d'attente sur chaque
        fiche du lot. Dix sources dans ce cas expliquent l'essentiel
        du temps perdu."""
        appels = []
        st, ctx = self._monde()
        monkeypatch.setattr(ctx, "scrapers", lambda: ["kink"])

        def casser(q, v=None):
            if "scrapeSingle" in str(q):
                appels.append(1)
                raise RuntimeError("chrome absent")
            return {}
        monkeypatch.setattr(ctx.stash, "call_GQL", casser)
        collecte.collecter_stash(ctx, "Archie Fox")
        collecte.collecter_stash(ctx, "Archie Fox")
        assert len(appels) == 1

    def test_une_source_muette_n_est_pas_reinterrogee(self,
                                                      monkeypatch):
        """« Cette source ne connaît pas cette fiche » EST une
        réponse : ne pas la garder ferait réinterroger indéfiniment
        les sources muettes, soit la majorité des cas."""
        appels = []
        st, ctx = self._monde()
        monkeypatch.setattr(ctx, "scrapers", lambda: ["iafd"])

        def vide(q, v=None):
            if "scrapeSingle" in str(q):
                appels.append(1)
                return {"scrapeSinglePerformer": []}
            return {}
        monkeypatch.setattr(ctx.stash, "call_GQL", vide)
        collecte.collecter_stash(ctx, "Archie Fox")
        collecte.collecter_stash(ctx, "Archie Fox")
        assert len(appels) == 1
