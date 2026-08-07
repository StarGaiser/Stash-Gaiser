# -*- coding: utf-8 -*-
"""
Rapprochement des studios de la médiathèque avec les scrapers
disponibles au catalogue.

Écrit AVANT le code, pour fixer le contrat.

Ce que la fonctionnalité doit faire : repérer qu'un studio présent dans
la collection a un scraper au catalogue qui n'est pas installé, et le
dire. Éventuellement l'installer.

Ce qu'elle ne doit PAS faire, et c'est le plus important : installer du
code tiers sans que l'utilisateur l'ait voulu. Un scraper s'exécute sur
sa machine et interroge des sites en son nom. La détection est
automatique et sans risque ; l'installation est un geste, ou un réglage
explicitement activé.

Le rapprochement est EXACT sur forme normalisée, jamais approximatif :
installer « BrazzersAPI » parce qu'un studio s'appelle « Brazil » serait
pire que ne rien installer.
"""


import pytest

import scrapers
from faux import FauxStash, faux_contexte, performer, studio


CATALOGUE = [
    {"package_id": "Masqulin", "name": "Masqulin"},
    {"package_id": "SayUncle", "name": "Say Uncle"},
    {"package_id": "GuysInSweatpants", "name": "Guys In Sweatpants"},
    {"package_id": "AyloAPI", "name": "Aylo API"},
    {"package_id": "OnlyFans", "name": "OnlyFans"},
    {"package_id": "BrazzersAPI", "name": "Brazzers"},
]


# ── Rapprochement ────────────────────────────────────────────────────
class TestRapprochement:

    def test_nom_identique(self):
        assert scrapers._rapprocher("Masqulin", CATALOGUE) \
            ["package_id"] == "Masqulin"

    def test_espaces_et_casse_ignores(self):
        """« Say Uncle » dans la collection, « SayUncle » au catalogue :
        la même chose écrite autrement."""
        for nom in ("Say Uncle", "sayuncle", "SAY  UNCLE",
                    "Say-Uncle"):
            trouve = scrapers._rapprocher(nom, CATALOGUE)
            assert trouve and trouve["package_id"] == "SayUncle", nom

    def test_le_nom_affiche_compte_aussi(self):
        """Le catalogue expose un identifiant ET un nom : les deux
        doivent servir au rapprochement."""
        assert scrapers._rapprocher("Guys In Sweatpants", CATALOGUE)

    def test_aucun_rapprochement_approximatif(self):
        """« Brazil » ne doit PAS ramener « Brazzers ». Installer le
        mauvais scraper est pire que n'en installer aucun : il
        répondrait, avec des données fausses."""
        for nom in ("Brazil", "Masqu", "Uncle", "Sweatpants",
                    "OnlyFansPlus"):
            assert scrapers._rapprocher(nom, CATALOGUE) is None, nom

    def test_nom_vide(self):
        for nom in ("", None, "   "):
            assert scrapers._rapprocher(nom, CATALOGUE) is None

    def test_catalogue_vide(self):
        assert scrapers._rapprocher("Masqulin", []) is None


class TestRapprochementParDomaine:
    """Les sources propres aux interprètes — OnlyFans, JustFor.Fans —
    ne portent pas de nom de studio : elles se déduisent des URLs
    présentes sur les fiches."""

    def test_domaine_reconnu(self):
        trouve = scrapers._rapprocher_url(
            "https://onlyfans.com/quelquun", CATALOGUE)
        assert trouve and trouve["package_id"] == "OnlyFans"

    def test_sous_domaine_et_chemin_ignores(self):
        for url in ("https://www.onlyfans.com/x",
                    "http://onlyfans.com/",
                    "https://onlyfans.com/a/b?c=d"):
            assert scrapers._rapprocher_url(url, CATALOGUE), url

    def test_domaine_inconnu(self):
        assert scrapers._rapprocher_url(
            "https://exemple-inconnu.test/x", CATALOGUE) is None

    def test_url_malformee(self):
        for url in ("", None, "pas une url", "ftp://x"):
            assert scrapers._rapprocher_url(url, CATALOGUE) is None


# ── Ce qui manque ────────────────────────────────────────────────────
class TestDetection:

    def _monde(self, studios=(), perfs=()):
        st = FauxStash(studios=list(studios), performers=list(perfs))
        ctx = faux_contexte({}, st)
        ctx.args = {}
        return st, ctx

    def test_un_studio_sans_scraper_est_signale(self, monkeypatch):
        _st, ctx = self._monde([studio(1, "Masqulin")])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        manquants = scrapers.detecter(ctx)
        assert any(m["package_id"] == "Masqulin" for m in manquants)

    def test_un_scraper_deja_installe_n_est_pas_propose(self,
                                                       monkeypatch):
        _st, ctx = self._monde([studio(1, "Masqulin")])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes",
                            lambda ctx: {"Masqulin"})
        assert scrapers.detecter(ctx) == []

    def test_un_studio_sans_equivalent_est_ignore(self, monkeypatch):
        _st, ctx = self._monde([studio(1, "Un Studio Inconnu")])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        assert scrapers.detecter(ctx) == []

    def test_les_alias_comptent(self, monkeypatch):
        """Un studio renommé garde son ancien nom en alias : c'est
        souvent celui du scraper."""
        _st, ctx = self._monde([studio(1, "Masq", aliases=["Masqulin"])])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        assert scrapers.detecter(ctx)

    def test_les_urls_des_interpretes_comptent(self, monkeypatch):
        _st, ctx = self._monde(
            perfs=[performer(1, "Quelqu'un",
                             urls=["https://onlyfans.com/quelquun"])])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        assert any(m["package_id"] == "OnlyFans"
                   for m in scrapers.detecter(ctx))

    def test_chaque_paquet_n_est_propose_qu_une_fois(self,
                                                     monkeypatch):
        _st, ctx = self._monde(
            [studio(1, "Masqulin"), studio(2, "masqulin")])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        assert len(scrapers.detecter(ctx)) == 1

    def test_le_motif_est_conserve(self, monkeypatch):
        """Savoir POURQUOI un scraper est proposé : sans le studio qui
        l'a déclenché, la proposition est incompréhensible."""
        _st, ctx = self._monde([studio(1, "Masqulin")])
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        m = scrapers.detecter(ctx)[0]
        assert "Masqulin" in str(m.get("motif") or "")

    def test_catalogue_injoignable_ne_leve_pas(self, monkeypatch):
        """Le catalogue est distant : son indisponibilité ne doit pas
        interrompre un enrichissement en cours."""
        _st, ctx = self._monde([studio(1, "Masqulin")])

        def casse(ctx):
            raise RuntimeError("catalogue injoignable")
        monkeypatch.setattr(scrapers, "_catalogue", casse)
        assert scrapers.detecter(ctx) == []


# ── Installation ─────────────────────────────────────────────────────
class TestInstallation:
    """Un scraper est du code tiers qui s'exécutera sur la machine de
    l'utilisateur et interrogera des sites en son nom. Rien ne
    s'installe sans une volonté explicite."""

    def _prepare(self, monkeypatch, reglages=None):
        st = FauxStash(studios=[studio(1, "Masqulin")])
        ctx = faux_contexte(reglages or {}, st)
        ctx.args = {}
        monkeypatch.setattr(scrapers, "_catalogue",
                            lambda ctx: CATALOGUE)
        monkeypatch.setattr(scrapers, "_installes", lambda ctx: set())
        poses = []
        monkeypatch.setattr(scrapers, "_installer",
                            lambda ctx, ids: poses.extend(ids))
        return st, ctx, poses

    def test_rien_n_est_installe_par_defaut(self, monkeypatch):
        _st, ctx, poses = self._prepare(monkeypatch)
        scrapers.proposer_scrapers(ctx)
        assert poses == []

    def test_installation_sur_demande_explicite(self, monkeypatch):
        _st, ctx, poses = self._prepare(monkeypatch)
        ctx.args = {"installer": "1"}
        scrapers.proposer_scrapers(ctx)
        assert poses == ["Masqulin"]

    def test_installation_par_reglage_active(self, monkeypatch):
        _st, ctx, poses = self._prepare(
            monkeypatch, {"autoInstallScrapers": True})
        scrapers.proposer_scrapers(ctx)
        assert poses == ["Masqulin"]

    def test_simulation_n_installe_pas(self, monkeypatch):
        import noyau
        _st, ctx, poses = self._prepare(
            monkeypatch, {"autoInstallScrapers": True, "dryRun": True})
        noyau._activer_simulation(ctx)
        scrapers.proposer_scrapers(ctx)
        assert poses == []


# ── Déclenchement automatique ────────────────────────────────────────
@pytest.fixture(autouse=True)
def etat_isole(tmp_path, monkeypatch):
    """L'état vit dans un fichier : sans isolation, un test marque la
    vérification faite et le suivant la croit déjà passée. Les tests se
    contamineraient, et pire, ils écriraient dans l'état réel du
    plugin."""
    import noyau
    monkeypatch.setattr(noyau, "ETAT_FICHIER", tmp_path / "etat.json")


class TestDeclenchement:
    """La détection se lance au bout de l'enrichissement des scènes et
    des studios — le seul moment où la liste des studios est complète,
    puisque ce sont ces tâches qui créent ceux qui manquent.

    Elle est limitée à un passage par jour : sans quoi enrichir une
    fiche unique interrogerait le catalogue distant à chaque clic."""

    def test_premier_passage_autorise(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        assert scrapers.doit_verifier(ctx)

    def test_deuxieme_passage_du_jour_refuse(self, monkeypatch):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        scrapers.marquer_verifie(ctx)
        assert not scrapers.doit_verifier(ctx)

    def test_lendemain_autorise(self, monkeypatch):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        scrapers.marquer_verifie(ctx)
        monkeypatch.setattr(scrapers, "_aujourd_hui",
                            lambda: "2099-01-01")
        assert scrapers.doit_verifier(ctx)

    def test_demande_explicite_passe_outre(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        scrapers.marquer_verifie(ctx)
        ctx.args = {"force": "1"}
        assert scrapers.doit_verifier(ctx)
