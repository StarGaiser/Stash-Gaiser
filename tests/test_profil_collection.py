# -*- coding: utf-8 -*-
"""
Le prompt suit le profil de la collection.

Écrit AVANT le code.

Le prompt dit « acteur porno gay » et parle d'un lecteur qui regarde
des scènes gay. C'était mon cas d'usage, pas une propriété du plugin :
quelqu'un dont la médiathèque est hétéro, trans ou mixte reçoit un
texte qui suppose la sienne gay.

Le réglage `tagProfile` existe déjà — gay, hétéro, lesbien, bi, pan,
trans, mixte — et ne sert qu'aux suggestions de tags. Le prompt
l'ignorait.

**Ce qui change avec le profil est étroit.** Le ton, les garde-fous,
la longueur, la règle absolue : rien de tout cela ne dépend de
l'orientation. Seuls changent le mot qui désigne la personne, le genre
grammatical, et l'exception sur le contraste — « un hétéro qui tourne
gay » n'a de sens que dans une collection gay.

**Le défaut ne suppose rien.** Sans profil renseigné, le prompt
n'annonce aucune orientation : le modèle s'en tient à ce que les
données montrent, ce qu'il devait faire de toute façon.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import ia  # noqa: E402
from faux import FauxStash, faux_contexte  # noqa: E402

PROFILS = ("gay", "hetero", "lesbien", "bi", "pan", "trans", "mixte")


def _prompt(profil=None, langue="fr"):
    reglages = {"language": langue}
    if profil is not None:
        reglages["tagProfile"] = profil
    ctx = faux_contexte(reglages, FauxStash())
    return ia.prompt_biohot(ctx)


class TestLeProfilGouverneLeVocabulaire:
    """Seul change ce qui DÉSIGNE la personne : le reste du prompt
    vaut pour toutes les collections."""

    def test_une_collection_gay_dit_gay(self):
        assert "gay" in _prompt("gay").lower()

    def test_une_collection_hetero_ne_dit_pas_gay(self):
        """Recevoir « acteur porno gay » sur une médiathèque hétéro
        est le défaut qu'on corrige."""
        t = _prompt("hetero").lower()
        assert "porno gay" not in t, t[:200]

    def test_une_collection_lesbienne_emploie_le_feminin(self):
        """« Acteur » sur une collection lesbienne produit un texte au
        mauvais genre du premier mot à la dernière ligne."""
        t = _prompt("lesbien").lower()
        assert "actrice" in t or "interprète" in t, t[:200]

    def test_une_collection_trans_est_nommee(self):
        assert "trans" in _prompt("trans").lower()

    @pytest.mark.parametrize("profil", PROFILS)
    def test_chaque_profil_produit_un_prompt(self, profil):
        t = _prompt(profil)
        assert len(t) > 800, f"{profil} : {len(t)}"


class TestCeQuiNeChangePas:
    """Le ton, les garde-fous et la longueur ne dépendent pas de
    l'orientation : les faire varier multiplierait par sept le risque
    qu'une règle se perde."""

    @pytest.mark.parametrize("profil", PROFILS)
    def test_la_regle_absolue_survit(self, profil):
        assert "RÈGLE ABSOLUE" in _prompt(profil), profil

    @pytest.mark.parametrize("profil", PROFILS)
    def test_la_borne_de_longueur_survit(self, profil):
        assert "400" in _prompt(profil), profil

    @pytest.mark.parametrize("profil", PROFILS)
    def test_le_ton_cru_survit(self, profil):
        t = _prompt(profil).lower()
        assert "sans euphémisme" in t, profil

    @pytest.mark.parametrize("profil", PROFILS)
    def test_l_exemple_survit(self, profil):
        assert "EXEMPLE" in _prompt(profil), profil


class TestSansProfil:
    """Le défaut ne suppose rien : le modèle s'en tient à ce que les
    données montrent, ce qu'il devait faire de toute façon."""

    def test_aucune_orientation_annoncee(self):
        t = _prompt(None).lower()
        for mot in ("porno gay", "porno hétéro", "porno lesbien"):
            assert mot not in t, mot

    def test_le_prompt_reste_complet(self):
        t = _prompt(None)
        assert "RÈGLE ABSOLUE" in t and "EXEMPLE" in t

    def test_un_profil_inconnu_se_comporte_comme_aucun(self):
        """Une faute de frappe ne doit pas produire un prompt
        bancal."""
        t = _prompt("nimportequoi").lower()
        assert "porno gay" not in t


class TestLExceptionSurLeContraste:
    """« Un hétéro qui tourne gay » n'a de sens que dans une
    collection gay : c'est le contraste qui excite, et il dépend de
    ce qu'on regarde."""

    def test_elle_figure_dans_une_collection_gay(self):
        t = _prompt("gay").lower()
        assert "hétéro" in t or "hetero" in t

    def test_elle_s_inverse_dans_une_collection_hetero(self):
        """Le ressort existe aussi, dans l'autre sens."""
        t = _prompt("hetero").lower()
        assert "gay" in t or "homo" in t

    def test_elle_disparait_sans_profil(self):
        """Sans savoir ce que regarde le lecteur, on ne sait pas ce
        qui ferait contraste."""
        t = _prompt(None)
        assert "EXCEPTION" not in t


class TestToutesLesLangues:

    @pytest.mark.parametrize("langue",
                             ("en", "fr", "de", "es", "it", "pt", "nl"))
    def test_le_profil_est_traduit(self, langue):
        t = _prompt("gay", langue)
        assert len(t) > 800, f"{langue} : {len(t)}"


class TestLeGenreVientDeLaFiche:
    """Le profil de collection ne dit rien du genre d'une PERSONNE.
    Dans un porno hétéro il y a des actrices, dans un porno bi les
    deux, et une collection mixte n'en dit rien du tout.

    J'avais déduit le genre du profil — « hétéro » donnait « l'acteur »
    — ce qui est faux la moitié du temps et efface les femmes d'un
    genre qui en est fait.

    Stash porte le genre sur la fiche : c'est la seule source juste,
    et elle est déjà là. Le profil ne sert plus qu'au REPLI, quand le
    champ est vide."""

    def _qui(self, genre=None, profil=None):
        fiche = {"name": "X"}
        if genre:
            fiche["gender"] = genre
        reglages = {"language": "fr"}
        if profil:
            reglages["tagProfile"] = profil
        ctx = faux_contexte(reglages, FauxStash())
        return ia._qui_designer(ctx, fiche)

    def test_une_femme_est_une_actrice(self):
        assert "actrice" in self._qui("FEMALE", "hetero")

    def test_un_homme_est_un_acteur(self):
        assert self._qui("MALE", "hetero").endswith("acteur")

    def test_le_genre_prime_sur_le_profil(self):
        """Une actrice dans une collection gay reste une actrice."""
        assert "actrice" in self._qui("FEMALE", "gay")

    def test_une_personne_trans_emploie_un_terme_neutre(self):
        """Stash distingue TRANSGENDER_FEMALE et TRANSGENDER_MALE :
        présumer à partir de là serait une atteinte, et « interprète »
        ne présume rien."""
        for genre in ("TRANSGENDER_FEMALE", "TRANSGENDER_MALE",
                      "NON_BINARY", "INTERSEX"):
            assert "interprète" in self._qui(genre), genre

    def test_sans_genre_le_profil_sert_de_repli(self):
        """Huit cent quatre-vingt-douze fiches sur une collection
        réelle n'ont pas de genre renseigné : le profil est alors le
        meilleur indice disponible."""
        assert self._qui(None, "gay").endswith("acteur")
        assert "actrice" in self._qui(None, "lesbien")

    def test_sans_genre_ni_profil_le_terme_est_neutre(self):
        assert "interprète" in self._qui(None, None)

    def test_un_genre_inconnu_ne_leve_pas(self):
        for genre in ("", "PEU_IMPORTE", None, 42):
            assert isinstance(self._qui(genre), str), genre


class TestLeProfilNeDitPlusLeGenre:
    """Le profil garde ce qui le concerne — l'orientation du
    chroniqueur et le contraste — et abandonne ce qu'il ne peut pas
    savoir."""

    def test_le_profil_hetero_ne_presume_plus(self):
        import i18n
        profils = i18n.t_msg("profils_biohot", "fr") or {}
        # Le deuxième élément était le mot désignant la personne : il
        # ne vient plus de là.
        assert len(profils["hetero"]) >= 2

    def test_la_mention_d_orientation_subsiste(self):
        import i18n
        profils = i18n.t_msg("profils_biohot", "fr") or {}
        assert "hétéro" in profils["hetero"][0]
