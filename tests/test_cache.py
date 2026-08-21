# -*- coding: utf-8 -*-
"""
Cache des réponses de sources.

Écrit AVANT le code.

Une collecte complète sur une fiche interroge une vingtaine de sources
et prend deux minutes. Relancer la même tâche recommence tout, alors
que ces réponses ne changent pas d'un jour à l'autre : un annuaire ne
révise pas une date de naissance entre deux passages.

Le coût n'est pas seulement le temps. Chaque interrogation sollicite un
service tiers gratuit, et marteler ces services pour obtenir la réponse
qu'on a déjà est un abus, pas une optimisation manquée.

**Ce que le cache doit garantir.** Une réponse mémorisée doit être
indiscernable d'une réponse fraîche du point de vue de l'arbitrage —
mêmes valeurs, même provenance. Un cache qui simplifie ce qu'il garde
fausserait les notes sans que rien ne le signale.

**Ce qu'il ne doit pas faire.** Masquer une source qui recommence à
répondre, garder une réponse indéfiniment, ou grossir sans limite.
"""

import time
from pathlib import Path

import pytest

import cache


@pytest.fixture(autouse=True)
def cache_isole(tmp_path, monkeypatch):
    """Sans isolation, les tests écriraient dans le cache réel."""
    monkeypatch.setattr(cache, "DOSSIER", tmp_path / "cache")


# ── Ce qui est mémorisé ──────────────────────────────────────────────
class TestMemorisation:

    def test_une_reponse_est_relue_a_l_identique(self):
        reponse = {"name": "Archie", "birthdate": "1990-05-01",
                   "urls": ["https://exemple.test/a"]}
        cache.poser("iafd", "performer", "Archie Fox", reponse)
        assert cache.lire("iafd", "performer", "Archie Fox") == reponse

    def test_une_cle_absente_rend_rien(self):
        assert cache.lire("iafd", "performer", "Inconnu") is None

    def test_les_sources_ne_se_melangent_pas(self):
        cache.poser("iafd", "performer", "X", {"a": 1})
        cache.poser("gevi", "performer", "X", {"a": 2})
        assert cache.lire("gevi", "performer", "X") == {"a": 2}

    def test_les_types_d_entite_ne_se_melangent_pas(self):
        cache.poser("iafd", "performer", "Men", {"a": 1})
        cache.poser("iafd", "studio", "Men", {"a": 2})
        assert cache.lire("iafd", "studio", "Men") == {"a": 2}

    def test_le_nom_est_normalise(self):
        """« Archie Fox » et « archie  fox » désignent la même
        recherche : sans normalisation, le cache manquerait la moitié
        des reprises."""
        cache.poser("iafd", "performer", "Archie Fox", {"a": 1})
        for variante in ("archie fox", "  Archie  Fox ", "ARCHIE FOX"):
            assert cache.lire("iafd", "performer", variante), variante

    def test_une_reponse_vide_est_memorisee(self):
        """« Cette source ne connaît pas cette fiche » est une réponse.
        Ne pas la garder ferait réinterroger indéfiniment les sources
        qui n'ont rien — soit la majorité des cas."""
        cache.poser("iafd", "performer", "Inconnu", {})
        assert cache.lire("iafd", "performer", "Inconnu") == {}

    def test_une_reponse_nulle_n_est_pas_confondue_avec_absente(self):
        cache.poser("iafd", "performer", "Vide", None)
        assert cache.lire("iafd", "performer", "Vide") is None


# ── Péremption ───────────────────────────────────────────────────────
class TestPeremption:
    """Une réponse mémorisée trop longtemps devient un mensonge : une
    fiche corrigée en amont ne parviendrait jamais."""

    def test_une_reponse_recente_est_servie(self):
        cache.poser("iafd", "performer", "X", {"a": 1})
        assert cache.lire("iafd", "performer", "X", jours=30)

    def test_une_reponse_ancienne_est_ignoree(self, monkeypatch):
        cache.poser("iafd", "performer", "X", {"a": 1})
        # Trente et un jours plus tard.
        monkeypatch.setattr(cache, "_maintenant",
                            lambda: time.time() + 31 * 86400)
        assert cache.lire("iafd", "performer", "X", jours=30) is None

    def test_une_duree_nulle_desactive_le_cache(self):
        """L'utilisateur doit pouvoir forcer des réponses fraîches."""
        cache.poser("iafd", "performer", "X", {"a": 1})
        assert cache.lire("iafd", "performer", "X", jours=0) is None

    def test_les_echecs_perimen_plus_vite(self):
        """Une source qui a échoué peut avoir été réparée. Garder son
        silence un mois la condamnerait pour rien."""
        assert cache.duree_pour(None) < cache.duree_pour({"a": 1})


# ── Robustesse ───────────────────────────────────────────────────────
class TestRobustesse:
    """Un cache qui tombe doit dégrader vers une collecte normale,
    jamais interrompre la tâche."""

    def test_un_fichier_illisible_ne_leve_pas(self, tmp_path):
        cache.poser("iafd", "performer", "X", {"a": 1})
        for f in (tmp_path / "cache").rglob("*.json"):
            f.write_text("{cassé", encoding="utf-8")
        assert cache.lire("iafd", "performer", "X") is None

    def test_un_dossier_inaccessible_ne_leve_pas(self, monkeypatch):
        monkeypatch.setattr(cache, "DOSSIER",
                            Path("/inexistant/interdit"))
        cache.poser("iafd", "performer", "X", {"a": 1})
        assert cache.lire("iafd", "performer", "X") is None

    def test_des_valeurs_absurdes_ne_levent_pas(self):
        for nom in ("", None, "x" * 500, "../../etc/passwd"):
            cache.poser("iafd", "performer", nom, {"a": 1})
            cache.lire("iafd", "performer", nom)
        assert True, "aucune entrée ne doit faire tomber la collecte"

    def test_un_nom_ne_peut_pas_sortir_du_dossier(self, tmp_path):
        """Un nom d'interprète vient de sources tierces : s'il servait
        de chemin, « ../../ » écrirait hors du cache."""
        cache.poser("iafd", "performer", "../../evade", {"a": 1})
        dehors = list(tmp_path.parent.glob("evade*"))
        assert dehors == [], dehors


# ── Contenu conservé ─────────────────────────────────────────────────
class TestFidelite:
    """Une réponse mémorisée doit être indiscernable d'une réponse
    fraîche du point de vue de l'arbitrage."""

    def test_les_valeurs_sont_conservees_telles_quelles(self):
        reponse = {"name": "Archie", "height": "178",
                   "measurements": None, "images": ["a", "b"],
                   "birthdate": "1990-05-01", "vide": ""}
        cache.poser("iafd", "performer", "X", reponse)
        assert cache.lire("iafd", "performer", "X") == reponse

    def test_les_accents_survivent(self):
        cache.poser("iafd", "performer", "X",
                    {"country": "Brésil", "details": "à côté"})
        relu = cache.lire("iafd", "performer", "X")
        assert relu["country"] == "Brésil"

    def test_une_structure_imbriquee_survit(self):
        reponse = {"a": {"b": [1, {"c": "d"}]}}
        cache.poser("iafd", "performer", "X", reponse)
        assert cache.lire("iafd", "performer", "X") == reponse


# ── Entretien ────────────────────────────────────────────────────────
class TestEntretien:

    def test_le_cache_se_vide_sur_demande(self):
        cache.poser("iafd", "performer", "X", {"a": 1})
        cache.vider()
        assert cache.lire("iafd", "performer", "X") is None

    def test_le_vidage_sur_un_cache_absent_ne_leve_pas(self):
        cache.vider()
        assert True, "vider deux fois ne doit pas échouer"

    def test_les_entrees_perimees_sont_retirees(self, monkeypatch):
        cache.poser("iafd", "performer", "X", {"a": 1})
        monkeypatch.setattr(cache, "_maintenant",
                            lambda: time.time() + 400 * 86400)
        retirees = cache.nettoyer(jours=30)
        assert retirees >= 1

    def test_les_statistiques_sont_lisibles(self):
        cache.poser("iafd", "performer", "X", {"a": 1})
        cache.poser("gevi", "studio", "Y", {"b": 2})
        stats = cache.statistiques()
        assert stats.get("entrees") == 2
        assert stats.get("octets", 0) > 0


class TestEchecsMemorises:
    """Une source en panne coûte le temps d'attente à chaque fiche.
    Dix scrapers défaillants — navigateur absent, site fermé — font
    perdre une minute par interprète, soit quinze heures sur une
    collection d'un millier de fiches.

    Mémoriser l'échec évite cela. Mais brièvement : une panne est
    passagère par nature, et condamner une source pour un mois sur une
    coupure d'une minute serait pire que le mal."""

    def test_un_echec_est_memorise(self):
        cache.poser_echec("kink", "performer", "X", "chrome absent")
        assert cache.echec_recent("kink", "performer", "X")

    def test_un_echec_perime_vite(self, monkeypatch):
        cache.poser_echec("kink", "performer", "X", "panne")
        monkeypatch.setattr(cache, "_maintenant",
                            lambda: time.time() + 3 * 86400)
        assert not cache.echec_recent("kink", "performer", "X")

    def test_un_echec_ne_masque_pas_une_reponse(self):
        """Si la source a répondu depuis, la réponse prime."""
        cache.poser_echec("kink", "performer", "X", "panne")
        cache.poser("kink", "performer", "X", {"a": 1})
        assert cache.lire("kink", "performer", "X") == {"a": 1}

    def test_le_motif_est_conserve(self):
        """L'utilisateur doit pouvoir savoir POURQUOI une source est
        écartée, sans quoi il la croit interrogée."""
        cache.poser_echec("kink", "performer", "X", "chrome absent")
        assert "chrome" in str(
            cache.echec_recent("kink", "performer", "X")).lower()

    def test_un_echec_sur_une_fiche_ne_condamne_pas_les_autres(self):
        """Une source peut ignorer un interprète et en connaître un
        autre : l'échec porte sur le couple, pas sur la source."""
        cache.poser_echec("kink", "performer", "X", "panne")
        assert not cache.echec_recent("kink", "performer", "Y")
