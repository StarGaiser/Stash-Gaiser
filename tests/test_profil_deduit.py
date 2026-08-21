# -*- coding: utf-8 -*-
"""
Deviner le profil de collection plutôt que le demander.

Écrit AVANT le code.

Stash ne porte AUCUNE orientation sur les fiches d'interprète : le
champ n'existe pas. Mais l'orientation d'une collection ne se lit pas
sur une personne — elle se lit sur ce qui se passe dans les scènes.
Une scène jouée par deux hommes est une scène gay, quelle que soit
l'orientation déclarée de qui la joue.

**Ce qui rend la déduction praticable.** Le genre figure sur la fiche
d'interprète, et une scène nomme ses interprètes : la composition
suffit.

**Ce qui la rend fragile.** Sur une collection réelle, six cent trente
et une scènes sur sept cent cinquante-cinq ont des interprètes sans
genre renseigné. La déduction ne vaut donc que si elle refuse de
répondre quand la matière manque — un profil deviné à tort produit un
prompt faux sur toute la collection, ce qui est pire que pas de profil
du tout.

**Elle ne remplace pas le réglage, elle le propose.** Écrire un profil
que l'utilisateur n'a pas choisi serait décider à sa place sur un
sujet qui le regarde.
"""

import sys
from pathlib import Path


RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import profil  # noqa: E402
from faux import FauxStash, faux_contexte, scene  # noqa: E402


def _scene(ident, genres):
    return scene(ident, f"S{ident}", performers=[
        {"id": str(i), "gender": g} for i, g in enumerate(genres)])


class TestFormeDUneScene:
    """Une scène jouée par deux hommes est une scène gay, quelle que
    soit l'orientation déclarée de qui la joue."""

    def test_deux_hommes(self):
        assert profil.forme_scene(["MALE", "MALE"]) == "gay"

    def test_deux_femmes(self):
        assert profil.forme_scene(["FEMALE", "FEMALE"]) == "lesbien"

    def test_un_homme_une_femme(self):
        assert profil.forme_scene(["MALE", "FEMALE"]) == "hetero"

    def test_une_personne_seule_ne_dit_rien(self):
        """Une scène solo ne dit rien de l'orientation : elle est
        regardée par tout le monde."""
        assert profil.forme_scene(["MALE"]) is None
        assert profil.forme_scene(["FEMALE"]) is None

    def test_un_genre_manquant_annule(self):
        """Un seul genre inconnu suffit à rendre la scène muette :
        deviner sur une composition partielle serait pire que se
        taire."""
        assert profil.forme_scene(["MALE", None]) is None
        assert profil.forme_scene([None, None]) is None

    def test_une_identite_trans_est_signalee(self):
        for genre in ("TRANSGENDER_FEMALE", "TRANSGENDER_MALE"):
            assert profil.forme_scene(["MALE", genre]) == "trans"

    def test_aucun_interprete(self):
        assert profil.forme_scene([]) is None


class TestProfilDeviné:
    """Le profil se déduit de ce qui DOMINE, non de ce qui existe :
    une collection gay avec trois scènes hétéro reste gay."""

    def _ctx(self, scenes):
        st = FauxStash(scenes=scenes)
        return faux_contexte({}, st)

    def test_une_collection_franchement_gay(self):
        scenes = [_scene(i, ["MALE", "MALE"]) for i in range(10)]
        assert profil.deviner(self._ctx(scenes)) == "gay"

    def test_une_minorite_ne_change_rien(self):
        scenes = ([_scene(i, ["MALE", "MALE"]) for i in range(9)]
                  + [_scene(99, ["MALE", "FEMALE"])])
        assert profil.deviner(self._ctx(scenes)) == "gay"

    def test_une_collection_partagee_est_mixte(self):
        scenes = ([_scene(i, ["MALE", "MALE"]) for i in range(5)]
                  + [_scene(i + 50, ["MALE", "FEMALE"])
                     for i in range(5)])
        assert profil.deviner(self._ctx(scenes)) == "mixte"

    def test_trop_peu_de_matiere_ne_dit_rien(self):
        """Trois scènes ne caractérisent pas une collection : répondre
        sur si peu produirait un profil faux qu'on croirait établi."""
        scenes = [_scene(i, ["MALE", "MALE"]) for i in range(3)]
        assert profil.deviner(self._ctx(scenes)) is None

    def test_des_genres_absents_ne_disent_rien(self):
        """Le cas le plus courant : personne ne renseigne le genre."""
        scenes = [_scene(i, [None, None]) for i in range(50)]
        assert profil.deviner(self._ctx(scenes)) is None

    def test_collection_vide(self):
        assert profil.deviner(self._ctx([])) is None


class TestCeQueLaDeductionNeFaitPas:
    """Elle propose, elle n'impose pas."""

    def test_elle_n_ecrit_pas_le_reglage(self):
        """Écrire un profil que l'utilisateur n'a pas choisi serait
        décider à sa place sur un sujet qui le regarde."""
        code = (RACINE / "gaizer" / "profil.py").read_text(
            encoding="utf-8")
        assert "configurePlugin" not in code

    def test_un_reglage_explicite_prime(self):
        """Ce que l'utilisateur a choisi ne se discute pas."""
        st = FauxStash(scenes=[_scene(i, ["MALE", "FEMALE"])
                               for i in range(20)])
        ctx = faux_contexte({"tagProfile": "gay"}, st)
        assert profil.profil_courant(ctx) == "gay"

    def test_sans_reglage_la_deduction_sert(self):
        st = FauxStash(scenes=[_scene(i, ["MALE", "MALE"])
                               for i in range(20)])
        ctx = faux_contexte({}, st)
        assert profil.profil_courant(ctx) == "gay"

    def test_sans_reglage_ni_matiere_rien_n_est_suppose(self):
        ctx = faux_contexte({}, FauxStash())
        assert profil.profil_courant(ctx) is None


class TestRapportDeProfil:
    """La déduction agit sans se montrer : sans ce rapport,
    l'utilisateur ne sait ni qu'elle existe, ni ce qu'elle a conclu,
    ni pourquoi elle se tait sur sa collection.

    Il sert aussi à décider s'il faut fixer le réglage : un profil
    deviné change avec la collection, un profil réglé non."""

    def _lignes(self, ctx, monkeypatch):
        vues = []
        monkeypatch.setattr(profil.log, "info",
                            lambda m, *a, **k: vues.append(str(m)))
        monkeypatch.setattr(profil.log, "warning",
                            lambda m, *a, **k: vues.append(str(m)))
        profil.rapport_profil(ctx)
        return "\n".join(vues)

    def test_il_compte_les_formes(self, monkeypatch):
        scenes = [_scene(i, ["MALE", "MALE"]) for i in range(10)]
        ctx = faux_contexte({}, FauxStash(scenes=scenes))
        rendu = self._lignes(ctx, monkeypatch)
        assert "gay" in rendu and "10" in rendu

    def test_il_dit_pourquoi_il_se_tait(self, monkeypatch):
        """Le cas le plus courant : les genres ne sont pas
        renseignés. Le taire laisserait croire à une panne."""
        scenes = [_scene(i, [None, None]) for i in range(20)]
        ctx = faux_contexte({}, FauxStash(scenes=scenes))
        rendu = self._lignes(ctx, monkeypatch).lower()
        assert "genre" in rendu

    def test_il_signale_les_solos(self, monkeypatch):
        scenes = [_scene(i, ["MALE"]) for i in range(10)]
        ctx = faux_contexte({}, FauxStash(scenes=scenes))
        rendu = self._lignes(ctx, monkeypatch).lower()
        assert "caractérisent" in rendu or "interprète" in rendu

    def test_un_reglage_explicite_est_dit_prioritaire(self,
                                                      monkeypatch):
        scenes = [_scene(i, ["MALE", "MALE"]) for i in range(10)]
        ctx = faux_contexte({"tagProfile": "hetero"},
                            FauxStash(scenes=scenes))
        rendu = self._lignes(ctx, monkeypatch).lower()
        assert "hetero" in rendu and "prime" in rendu

    def test_un_desaccord_est_signale(self, monkeypatch):
        """Régler « hétéro » sur une collection manifestement gay est
        peut-être voulu, peut-être une erreur : le dire laisse
        trancher."""
        scenes = [_scene(i, ["MALE", "MALE"]) for i in range(10)]
        ctx = faux_contexte({"tagProfile": "hetero"},
                            FauxStash(scenes=scenes))
        rendu = self._lignes(ctx, monkeypatch).lower()
        assert "suggérerait" in rendu

    def test_il_conseille_de_fixer_le_reglage(self, monkeypatch):
        """Un profil deviné change avec la collection : celui qui
        ajoute des scènes verrait son rédacteur changer de ton sans
        comprendre."""
        scenes = [_scene(i, ["MALE", "MALE"]) for i in range(10)]
        ctx = faux_contexte({}, FauxStash(scenes=scenes))
        rendu = self._lignes(ctx, monkeypatch).lower()
        assert "fixer" in rendu

    def test_une_collection_illisible_ne_leve_pas(self, monkeypatch):
        class Cassé:
            def find_scenes(self, *a, **k):
                raise RuntimeError("serveur absent")
        ctx = faux_contexte({}, Cassé())
        rendu = self._lignes(ctx, monkeypatch).lower()
        assert "illisible" in rendu

    def test_une_collection_vide_ne_leve_pas(self, monkeypatch):
        ctx = faux_contexte({}, FauxStash())
        assert self._lignes(ctx, monkeypatch)
