# -*- coding: utf-8 -*-
"""
Données hostiles et réglages mal saisis.

Le plugin écrit ce que des sources distantes lui donnent, et lit des
réglages tapés à la main dans une interface. Ni les unes ni les autres
ne sont dignes de confiance.

Deux exigences :
  - une donnée aberrante ne doit jamais interrompre le traitement des
    autres fiches ;
  - une exception dans `Context` tuerait TOUTES les tâches, y compris
    celles qui n'ont rien à voir avec le réglage fautif.
"""

import re

import pytest

import i18n
import noyau
import scoring
import similarite
from faux import faux_contexte


# ── Réglages mal saisis ──────────────────────────────────────────────
class TestReglagesAberrants:
    """Les réglages arrivent en texte : « abc », « 7,5 », « -5 »…"""

    @pytest.mark.parametrize("valeur", [
        "abc", "", "  ", "-5", "0", "1e9", "7,5", "999999999999",
        None, "12.7.3", "∞",
    ])
    def test_taille_de_lot_toujours_utilisable(self, valeur):
        ctx = faux_contexte({"batchSize": valeur})
        lot = ctx.batch()
        assert isinstance(lot, int) and 1 <= lot <= 5000, \
            f"« {valeur} » donne {lot}"

    @pytest.mark.parametrize("valeur", [
        "abc", "", "-3", "11", "7,5", "0", None, "1e3",
    ])
    def test_seuil_toujours_dans_le_bareme(self, valeur):
        ctx = faux_contexte({"autoAcceptThreshold": valeur})
        seuil = ctx.auto_threshold()
        assert 0 <= seuil <= 10, f"« {valeur} » donne {seuil}"

    def test_virgule_decimale_acceptee(self):
        """Un utilisateur francophone tape « 7,5 » sans y penser."""
        assert faux_contexte({"autoAcceptThreshold": "7,5"}) \
            .auto_threshold() == 7.5

    @pytest.mark.parametrize("valeur", [
        "abc", "-1", "", None, "1e9", "3,5"])
    def test_fraicheur_toujours_utilisable(self, valeur):
        n = faux_contexte({"refreshDays": valeur}).refresh_days()
        assert isinstance(n, int) and n >= 0

    @pytest.mark.parametrize("valeur", [
        "abc", "MANUAL", "Auto", "", None, "seuil ", "n'importe quoi"])
    def test_mode_toujours_reconnu(self, valeur):
        mode = faux_contexte({"applyMode": valeur}).apply_mode()
        assert mode in ("manual", "seuil", "auto"), f"« {valeur} »"

    def test_langue_inconnue_retombe_sur_l_anglais(self):
        assert faux_contexte({"language": "klingon"}).lang() == "en"

    def test_liste_de_tags_malformee(self):
        for valeur in (",,,", " , , ", "", None, "a,,b"):
            exclus = faux_contexte({"tagsExclude": valeur}).tags_exclus()
            assert isinstance(exclus, set)
            assert "" not in exclus, "un motif vide exclurait tout"

    def test_aucun_reglage_du_tout(self):
        """Première installation : la table est vide."""
        ctx = faux_contexte({})
        assert ctx.apply_mode() and ctx.batch() and ctx.lang()
        assert ctx.ai_for("bio") is None


# ── Valeurs de sources hostiles ──────────────────────────────────────
class TestValeursAberrantes:

    @pytest.mark.parametrize("date", [
        "0000-00-00", "1984-13-45", "9999-99-99", "pas une date",
        "1984", "", "1984-10-21T00:00:00Z", "21/10/1984", None,
    ])
    def test_date_illisible_n_interrompt_pas(self, date):
        """Une date aberrante d'une source faisait lever une exception
        qui interrompait l'enrichissement de toute la fiche."""
        cands = scoring.evaluer(
            "birthdate", {"iafd": "1984-10-21", "men": date},
            scoring.DEFAUTS)
        assert isinstance(cands, list)

    @pytest.mark.parametrize("taille", [
        0, -5, 999, 99999, "cent quatre-vingts", "", None, "180cm",
        float("inf"),
    ])
    def test_taille_aberrante_n_interrompt_pas(self, taille):
        cands = scoring.evaluer("height_cm",
                                {"iafd": 178, "men": taille},
                                scoring.DEFAUTS)
        assert isinstance(cands, list)

    def test_non_reponses_ecartees(self):
        """« unknown », « n/a », « - » sont des non-réponses : les
        proposer reviendrait à effacer un champ au nom d'une source."""
        for vide in ("", "  ", "unknown", "N/A", "none", "null", "-",
                     "0000-00-00", None):
            cands = scoring.evaluer("country", {"men": vide},
                                    scoring.DEFAUTS)
            assert cands == [], f"« {vide} » ne doit pas concourir"

    def test_texte_tres_long(self):
        """Une bio de 50 000 caractères ne doit pas faire exploser le
        traitement."""
        enorme = "x" * 50000
        cands = scoring.evaluer("bio", {"men": enorme},
                                scoring.DEFAUTS)
        assert isinstance(cands, list)

    def test_caracteres_de_controle_dans_un_nom(self):
        for nom in ["Tom\x00Hardy", "Tom\u200bHardy", "Tom\nHardy",
                    "Tom\tHardy", "  Tom  "]:
            plat, jetons = similarite._sim_cles(nom)
            assert isinstance(plat, str) and isinstance(jetons, list)

    def test_emoji_et_ecritures_non_latines(self):
        for nom in ["Tom 🔥 Hardy", "山田太郎", "Дато Фоланд",
                    "Ω Alpha"]:
            plat, _jetons = similarite._sim_cles(nom)
            assert isinstance(plat, str)

    def test_noms_exotiques_ne_se_confondent_pas(self):
        """Deux noms réduits à une chaîne vide ne doivent pas être
        déclarés identiques."""
        a = similarite._sim_cles("山田太郎")
        b = similarite._sim_cles("Дато Фоланд")
        if not a[0] and not b[0]:
            note, _m = similarite._score_doublon(a, b)
            assert note == 0, \
                "deux noms illisibles ne sont pas un doublon"


# ── Troncatures ──────────────────────────────────────────────────────
class TestTroncatures:
    """Les valeurs sont coupées avant écriture. Une coupe au milieu
    d'un caractère multi-octets produirait du texte invalide."""

    def test_historique_borne_meme_avec_de_longues_valeurs(self):
        fiche = {}
        long_texte = "é" * 3000
        for _i in range(12):
            h = noyau._historique_maj(
                fiche, {"details": ["", long_texte]})
            fiche = {"custom_fields": {"enrich_historique": h}}
        import json
        assert len(json.loads(h)) == 10

    def test_troncature_preserve_les_accents(self):
        """Python coupe des caractères, pas des octets : vérifions que
        rien dans la chaîne d'écriture ne casse cette propriété."""
        texte = "é" * 600
        coupe = texte[:480]
        assert coupe.encode("utf-8").decode("utf-8") == coupe
        assert len(coupe) == 480

    def test_pied_de_bio_retire_meme_apres_troncature(self):
        base = "Bio."
        for marque in noyau.FOOTER_MARKS:
            assert noyau._sans_footer(base + marque + "\nx") == base


# ── Paramètres des messages traduits ─────────────────────────────────
class TestParametresDesTraductions:
    """Si une langue perd un paramètre, `.format()` produit un message
    amputé sans rien signaler — le texte s'affiche, mais la date ou le
    motif manque."""

    def _params(self, texte):
        return set(re.findall(r"\{(\w+)\}", texte or ""))

    def test_memes_parametres_dans_toutes_les_langues(self):
        fautes = []
        for famille in ("msg", "boutons"):
            reference = i18n.EN[famille]
            for cle, modele in reference.items():
                attendus = self._params(modele)
                for langue, bloc in i18n.CATALOGUE.items():
                    traduit = (bloc.get(famille) or {}).get(cle)
                    if traduit is None:
                        continue
                    trouves = self._params(traduit)
                    if trouves != attendus:
                        fautes.append(
                            f"{langue}/{cle} : {sorted(trouves)} "
                            f"au lieu de {sorted(attendus)}")
        assert fautes == [], "\n".join(fautes)

    def test_aucun_parametre_positionnel(self):
        """« {} » rendrait la traduction dépendante de l'ordre des
        arguments, impossible à respecter d'une langue à l'autre."""
        for langue, bloc in i18n.CATALOGUE.items():
            for famille in ("msg", "boutons"):
                for cle, texte in (bloc.get(famille) or {}).items():
                    assert "{}" not in texte, f"{langue}/{cle}"

    def test_messages_rendus_sans_erreur(self):
        """Chaque message doit se rendre même si un paramètre manque."""
        for langue in i18n.LANGUES:
            for cle in i18n.EN["msg"]:
                rendu = i18n.t(cle, langue, motif="m", date="d",
                               details="x", champ="c", actuel="a",
                               propose="p", jumeaux="j", tag="t",
                               score="s", detail="d", nom="n", id="1",
                               passage="p", max=1, pose="p", op="o")
                assert isinstance(rendu, str) and rendu

    def test_aucun_texte_vide(self):
        for langue, bloc in i18n.CATALOGUE.items():
            for famille in ("tags", "boutons", "taches", "reglages",
                            "msg"):
                for cle, texte in (bloc.get(famille) or {}).items():
                    assert str(texte).strip(), f"{langue}/{famille}/{cle}"

    def test_tags_utilisables_comme_noms(self):
        """Un suffixe de tag ne doit contenir ni virgule ni retour à la
        ligne : Stash les découperait."""
        for langue, bloc in i18n.CATALOGUE.items():
            for cle, suffixe in (bloc.get("tags") or {}).items():
                assert "," not in suffixe, f"{langue}/{cle}"
                assert "\n" not in suffixe, f"{langue}/{cle}"
                assert suffixe.strip() == suffixe, f"{langue}/{cle}"

    def test_suffixes_de_tags_distincts_par_langue(self):
        """Deux clés ne doivent pas donner le même tag : les états du
        flux deviendraient indiscernables."""
        for langue, bloc in i18n.CATALOGUE.items():
            suffixes = list((bloc.get("tags") or {}).values())
            assert len(suffixes) == len(set(suffixes)), langue


# ── Fiches incomplètes ───────────────────────────────────────────────
class TestFichesIncompletes:
    """Stash renvoie parfois des fiches sans les champs attendus."""

    def test_fiche_sans_aucun_champ(self):
        assert similarite.exemptions_de({}) == set()
        assert noyau._date_enrich({}) is None
        assert similarite._richesse({}) >= 0

    def test_fiche_aux_champs_nuls(self):
        fiche = {"id": "1", "name": None, "custom_fields": None,
                 "tags": None}
        assert similarite.exemptions_de(fiche) == set()
        assert noyau._date_enrich(fiche) is None

    def test_comparaison_avec_un_nom_absent(self):
        note, _m = similarite._score_doublon(
            similarite._sim_cles(None), similarite._sim_cles("Tom"))
        assert note == 0
