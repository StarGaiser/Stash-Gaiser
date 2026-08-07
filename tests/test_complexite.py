# -*- coding: utf-8 -*-
"""
Budgets de complexité.

Ces tests ne mesurent PAS des durées absolues : elles dépendent de la
machine, de la charge et du cache, ce qui rend le test instable — on
finit par l'ignorer, et un test ignoré ne protège rien.

Ils vérifient la FORME de la croissance. Doubler le nombre d'entités
doit multiplier le travail par environ quatre pour une comparaison
deux à deux, jamais par huit. C'est ce qui attrape le jour où quelqu'un
glisse un `re.compile` dans une boucle ou une requête dans un parcours.

Les plafonds sont volontairement larges : ils signalent un changement
d'ordre de grandeur, pas une régression de dix pour cent.
"""

import time

import pytest

import groupes
import noyau
import similarite
from faux import FauxStash, faux_contexte


def _duree(fonction, repetitions=1) -> float:
    """Meilleur temps sur trois essais : la mesure la moins polluée par
    l'ordonnanceur du système."""
    meilleurs = []
    for _ in range(3):
        debut = time.perf_counter()
        for _ in range(repetitions):
            fonction()
        meilleurs.append(time.perf_counter() - debut)
    return min(meilleurs)


def _jeu(n):
    noms = [f"Interprete Numero {i}" for i in range(n)]
    objets = [{"id": str(i), "name": nom} for i, nom in enumerate(noms)]
    cles = {str(i): similarite._sim_cles(nom)
            for i, nom in enumerate(noms)}
    alias = {str(i): set() for i in range(n)}
    return objets, cles, alias


class TestCroissance:

    def test_recherche_de_paires_reste_quadratique(self):
        """Comparer deux à deux est quadratique par nature. Ce qui est
        vérifié, c'est qu'on n'y a pas ajouté un facteur — un tri, une
        compilation d'expression, une copie — dans la boucle interne."""
        petit = _duree(lambda: similarite.paires_candidates(
            *_jeu(300), lambda f: set()))
        grand = _duree(lambda: similarite.paires_candidates(
            *_jeu(600), lambda f: set()))
        if petit < 0.002:
            pytest.skip("mesure trop courte pour être significative")
        facteur = grand / petit
        assert facteur < 8, (
            f"doubler la collection multiplie le temps par "
            f"{facteur:.1f} : au-delà de ~4, un coût s'est glissé dans "
            f"la boucle")

    def test_normalisation_lineaire(self):
        court = _duree(lambda: similarite._sim_cles("Jean Daniel"), 2000)
        long = _duree(
            lambda: similarite._sim_cles("Jean Daniel " * 20), 2000)
        if court < 0.002:
            pytest.skip("mesure trop courte")
        assert long / court < 40, \
            "le coût doit suivre la longueur du nom, pas son carré"

    def test_filtrage_des_tags_insensible_au_nombre_de_motifs(self):
        peu = {"gay", "4k"}
        beaucoup = {f"motif{i}" for i in range(200)} | peu
        t_peu = _duree(lambda: noyau._tag_exclu("Hairy Pussy", peu),
                       3000)
        t_beaucoup = _duree(
            lambda: noyau._tag_exclu("Hairy Pussy", beaucoup), 3000)
        if t_peu < 0.002:
            pytest.skip("mesure trop courte")
        assert t_beaucoup / t_peu < 150, \
            "cent fois plus de motifs ne doit pas coûter cent fois plus"


class TestBudgetDeRequetesSurVolume:
    """Le vrai risque n'est pas la lenteur d'un calcul mais le nombre
    d'allers-retours : ils se paient en latence réseau, pas en cycles."""

    def test_les_poses_de_tag_ne_croissent_pas_avec_les_entites(self):
        st = FauxStash(tags=[{"id": "1", "name": "Gaizer:créé"}])
        ctx = faux_contexte({}, st)
        for _ in range(500):
            noyau.tag_id(ctx, "Gaizer:créé")
        assert st.appels["find_tags"] <= 1, \
            f"{st.appels['find_tags']} requêtes pour un seul nom"

    def test_l_index_des_groupes_ne_se_recharge_pas(self):
        st = FauxStash(groups=[{"id": str(i), "name": f"Film {i}",
                                "aliases": ""} for i in range(200)])
        ctx = faux_contexte({}, st)
        for i in range(200):
            groupes._groupe_existant(ctx, f"Film {i}")
        assert st.appels["findGroups"] == 1

    def test_le_rapprochement_de_series_ne_lit_pas_le_serveur(self):
        """`_fusionner_series` travaille sur un dictionnaire déjà
        constitué : une requête glissée là serait payée par série."""
        st = FauxStash()
        series = {
            groupes._cle_serie(f"Serie Numero {i}"): {
                "nom": f"Serie Numero {i}",
                "parties": [(1, {"id": str(i)})],
                "studios": {"1"}, "dates": [], "genre": "partie",
                "bonus": 0.5, "depuis_titre": True}
            for i in range(150)}
        groupes._fusionner_series(series)
        assert st.total_appels == 0


class TestVolumeRealiste:
    """Ordres de grandeur de la collection : un millier de interprètes, 800
    scènes, une centaine de studios."""

    def test_recherche_de_doublons_sur_neuf_cents_fiches(self):
        objets, cles, alias = _jeu(900)
        debut = time.perf_counter()
        paires = similarite.paires_candidates(objets, cles, alias,
                                              lambda f: set())
        duree = time.perf_counter() - debut
        assert duree < 10, (
            f"{duree:.1f}s pour un millier de fiches — mesuré autour de 1 s, "
            f"un dépassement franc signale un changement de nature")
        assert isinstance(paires, dict)

    def test_lecture_des_motifs_sur_huit_cents_titres(self):
        titres = [f"Une Serie Quelconque Part {i % 12}"
                  for i in range(800)]
        debut = time.perf_counter()
        for t in titres:
            groupes._lire_partie(t)
        assert time.perf_counter() - debut < 2

    def test_filtrage_de_six_cents_tags(self):
        exclus = {"gay", "*pussy*", "*videos", "bonus*", "series"}
        noms = [f"Un Tag Quelconque {i}" for i in range(600)]
        debut = time.perf_counter()
        for n in noms:
            noyau._tag_exclu(n, exclus)
        assert time.perf_counter() - debut < 1
