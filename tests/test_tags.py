# -*- coding: utf-8 -*-
"""
Familles de tags et suggestions d'exclusion.

Ce module porte le risque le plus délicat du plugin : il touche à des
catégories — orientation, identité de genre — où une erreur de
classement n'est pas seulement un bogue. Les tests portent donc autant
sur ce qui NE doit PAS être proposé que sur ce qui l'est.
"""

import tags


TABLE = tags.charger()


# ── Classement en familles ───────────────────────────────────────────
class TestFamilles:

    def test_formats_reconnus(self):
        for nom in ("4K", "1080p", "WEBRip", "BluRay", "HEVC"):
            assert tags.famille_de(nom, TABLE) == "format", nom

    def test_mentions_editoriales_reconnues(self):
        for nom in ("Bonus Scene", "Feature", "Series", "Trailer"):
            assert tags.famille_de(nom, TABLE) == "edition", nom

    def test_identite_de_genre_reconnue(self):
        for nom in ("Trans", "Transgender", "FTM", "Non-Binary",
                    "Intersex"):
            assert tags.famille_de(nom, TABLE) == "identite", nom

    def test_transparent_n_est_pas_une_identite(self):
        """« *trans* » classait « Transparent Clothing » parmi les
        identités de genre. Un motif englobant ne convient pas à une
        famille sensible."""
        assert tags.famille_de("Transparent Clothing", TABLE) \
            != "identite"

    def test_cum_drip_n_est_pas_un_format(self):
        """« *rip » attrapait « Cum Drip » en croyant lire « WEBRip »."""
        assert tags.famille_de("Cum Drip", TABLE) != "format"

    def test_morphotypes_ranges_en_physique(self):
        """« Bear », « Otter », « Twink » décrivent une silhouette, pas
        une identité de genre : les confondre brouille les deux
        notions et protégerait ces tags pour une mauvaise raison."""
        for nom in ("Bear", "Otter", "Twink", "Jock", "Daddy"):
            assert tags.famille_de(nom, TABLE) == "physique", nom

    def test_tag_inconnu_reste_non_classe(self):
        assert tags.famille_de("Un Tag Tout À Fait Inédit", TABLE) == ""

    def test_familles_techniques_prioritaires(self):
        """Un tag lisible de deux façons relève d'abord du format ou de
        l'édition."""
        assert tags.famille_de("Bonus Scene", TABLE) == "edition"

    def test_casse_et_ponctuation_ignorees(self):
        assert tags.famille_de("web-dl", TABLE) \
            == tags.famille_de("WEB-DL", TABLE) == "format"

    def test_valeurs_vides(self):
        for nom in ("", None, "   "):
            assert tags.famille_de(nom, TABLE) == ""


# ── Suggestions ──────────────────────────────────────────────────────
class TestSuggestions:

    def test_dominance_intra_famille(self):
        """Le cas réel : « Gay » ne couvre que 14 % des scènes — trop
        peu pour une mesure absolue — mais détient 96 % de sa famille.
        C'est une constante de la collection, pas une distinction."""
        freq = {"Gay": 118, "Lesbian": 2, "Straight": 1,
                "Bisexual": 1}
        sug = tags.suggestions(freq, 816, TABLE)
        dominants = [n for n, _c, _f in sug["dominant"]]
        assert dominants == ["Gay"]

    def test_famille_partagee_ne_donne_aucun_dominant(self):
        """Dans une collection mixte, aucune orientation n'écrase les
        autres : rien ne doit être proposé."""
        freq = {"Gay": 100, "Straight": 120, "Lesbian": 90,
                "Bisexual": 80}
        sug = tags.suggestions(freq, 500, TABLE)
        assert sug["dominant"] == []

    def test_famille_trop_maigre_ignoree(self):
        """Deux occurrences ne suffisent pas à conclure à une
        constante."""
        freq = {"Gay": 2}
        sug = tags.suggestions(freq, 100, TABLE)
        assert sug["dominant"] == []

    def test_tag_omnipresent_detecte(self):
        freq = {"Amateur": 95, "Autre": 3}
        sug = tags.suggestions(freq, 100, TABLE)
        assert "Amateur" in [n for n, _c, _f in sug["omnipresent"]]

    def test_tags_rares_signales(self):
        freq = {"Unique": 1, "Presque": 2, "Courant": 50}
        sug = tags.suggestions(freq, 200, TABLE)
        rares = [n for n, _c, _f in sug["rare"]]
        assert "Unique" in rares and "Presque" in rares
        assert "Courant" not in rares

    def test_familles_techniques_proposees_avec_profil(self):
        freq = {"4K": 30, "Series": 20}
        sug = tags.suggestions(freq, 800, TABLE, profil="gay")
        proposes = [n for n, _c, _f in sug["famille"]]
        assert "4K" in proposes and "Series" in proposes

    def test_aucune_proposition_de_famille_sans_profil(self):
        freq = {"4K": 30, "Series": 20}
        sug = tags.suggestions(freq, 800, TABLE)
        assert sug["famille"] == []


# ── Protections ──────────────────────────────────────────────────────
class TestProtections:
    """Le point le plus important. Un profil décrit ce qu'une
    collection contient ; il ne doit jamais servir à évincer ce qui
    n'entre pas dans une catégorie supposée."""

    def test_identite_jamais_proposee(self):
        """Une collection étiquetée « gay » contient des interprètes
        trans : écarter ces tags parce qu'ils sont minoritaires serait
        une régression, pas un nettoyage."""
        freq = {"Trans": 200, "Transgender": 1, "Gay": 5}
        for profil in ("gay", "hetero", "lesbien", "bi", "pan",
                       "trans", "mixte"):
            sug = tags.suggestions(freq, 210, TABLE, profil)
            tous = [n for cle in sug for n, _c, _f in sug[cle]]
            assert "Trans" not in tous, profil
            assert "Transgender" not in tous, profil

    def test_pratiques_jamais_proposees(self):
        freq = {"Anal": 400, "Blowjob": 2}
        for profil in ("gay", "hetero", "bi", "mixte"):
            sug = tags.suggestions(freq, 420, TABLE, profil)
            tous = [n for cle in sug for n, _c, _f in sug[cle]]
            assert "Anal" not in tous, profil

    def test_orientation_protegee_pour_les_profils_pluriels(self):
        """Dans une collection bi ou pan, l'orientation d'une scène est
        justement l'information utile."""
        freq = {"Gay": 300, "Straight": 2}
        for profil in ("bi", "pan", "mixte"):
            sug = tags.suggestions(freq, 310, TABLE, profil)
            tous = [n for cle in sug for n, _c, _f in sug[cle]]
            assert "Gay" not in tous, profil

    def test_aucun_profil_n_ecarte_une_famille_de_contenu(self):
        """Aucun profil livré ne doit proposer d'écarter autre chose
        que du technique : le contenu relève de l'utilisateur."""
        for nom, conf in TABLE["profils"].items():
            proposees = set(conf.get("suggere") or [])
            assert proposees <= set(tags.FAMILLES_TECHNIQUES), \
                f"le profil « {nom} » propose d'écarter {proposees}"

    def test_chaque_profil_protege_l_identite(self):
        for nom, conf in TABLE["profils"].items():
            assert "identite" in (conf.get("jamais") or []), nom


# ── Configuration ────────────────────────────────────────────────────
class TestConfiguration:

    def test_fichier_absent_donne_les_defauts(self, tmp_path):
        assert tags.charger(tmp_path)["familles"].keys() \
            == tags.DEFAUTS["familles"].keys()

    def test_surcharge_famille_par_famille(self, tmp_path):
        (tmp_path / "tag_profiles.yml").write_text(
            "familles:\n  maison:\n    - 'mon studio*'\n",
            encoding="utf-8")
        table = tags.charger(tmp_path)
        assert "maison" in table["familles"]
        assert "format" in table["familles"], \
            "ajouter une famille ne doit pas effacer les autres"

    def test_profil_personnalise(self, tmp_path):
        (tmp_path / "tag_profiles.yml").write_text(
            "profils:\n  perso:\n    description: Le mien\n"
            "    suggere: [format]\n    jamais: [identite]\n",
            encoding="utf-8")
        table = tags.charger(tmp_path)
        assert "perso" in table["profils"]
        assert "gay" in table["profils"]

    def test_fichier_illisible_donne_les_defauts(self, tmp_path):
        (tmp_path / "tag_profiles.yml").write_text(
            "ceci: [n'est pas: du yaml", encoding="utf-8")
        assert "format" in tags.charger(tmp_path)["familles"]

    def test_gabarit_cree_une_seule_fois(self, tmp_path):
        assert tags.creer_gabarit(tmp_path) is True
        assert tags.creer_gabarit(tmp_path) is False
        contenu = (tmp_path / "tag_profiles.yml").read_text()
        assert "DESCRIPTIVES" in contenu

    def test_seuils_surchargeables(self, tmp_path):
        (tmp_path / "tag_profiles.yml").write_text(
            "seuils:\n  dominance_famille: 0.5\n", encoding="utf-8")
        table = tags.charger(tmp_path)
        assert table["seuils"]["dominance_famille"] == 0.5
        assert "occurrences_rares" in table["seuils"]

    def test_seuils_aberrants_ne_levent_pas(self, tmp_path):
        (tmp_path / "tag_profiles.yml").write_text(
            "seuils:\n  dominance_famille: abc\n"
            "  couverture_inutile: null\n", encoding="utf-8")
        table = tags.charger(tmp_path)
        assert isinstance(tags.suggestions({"Gay": 50}, 100, table),
                          dict)

    def test_profils_listes_avec_description(self):
        connus = tags.profils_connus(TABLE)
        assert len(connus) >= 5
        for nom, desc in connus:
            assert nom and desc


# ── Robustesse ───────────────────────────────────────────────────────
class TestRobustesse:

    def test_collection_vide(self):
        sug = tags.suggestions({}, 0, TABLE)
        assert all(v == [] for v in sug.values())

    def test_profil_inconnu_traite_comme_absent(self):
        freq = {"4K": 30}
        sug = tags.suggestions(freq, 100, TABLE, profil="inexistant")
        assert sug["famille"] == []

    def test_repartition_complete(self):
        noms = ["4K", "Gay", "Trans", "Inconnu", "Anal"]
        rep = tags.repartition(noms, TABLE)
        assert sum(len(v) for v in rep.values()) == len(noms)
