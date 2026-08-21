# -*- coding: utf-8 -*-
"""
Les prompts traduits : ce qu'une traduction doit préserver.

Écrit AVANT la traduction.

Un prompt n'est pas une phrase d'interface. Traduire mot à mot en
perdrait ce qui le fait marcher : chaque règle a été ajoutée parce
qu'un texte réel était faux sans elle, et chaque garde-fou a un coût
mesuré. Une traduction qui adoucit « n'invente rien » ou qui perd
l'exemple produira des textes que le français ne produit plus.

**Le sens prime sur la lettre.** « Bite » ne se traduit pas par le
terme clinique de chaque langue : le mot doit avoir le même registre
— celui qu'un adulte emploie, ni médical ni puéril.

**Les garde-fous sont mécaniques.** Les paramètres, la marque
d'apport, la borne de longueur ne se traduisent pas du tout : ce sont
des repères que le code cherche.

**Rien ne se perd en route.** Une section absente est une règle
absente, et les défauts qu'elle corrigeait reviennent.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import i18n  # noqa: E402

LANGUES = ("en", "fr", "de", "es", "it", "pt", "nl")


def _prompt(lg):
    return i18n.t("prompt_biohot", lg)


class TestPresenceDansToutesLesLangues:

    @pytest.mark.parametrize("lg", LANGUES)
    def test_le_prompt_existe(self, lg):
        t = _prompt(lg)
        assert len(t) > 800, f"{lg} : {len(t)}"

    @pytest.mark.parametrize("lg", LANGUES)
    def test_les_consignes_de_forme_existent(self, lg):
        assert len(i18n.t("prompt_biohot_consignes", lg)) > 100, lg

    @pytest.mark.parametrize("lg", LANGUES)
    def test_le_fragment_d_apport_existe(self, lg):
        assert len(i18n.t("prompt_biohot_apport", lg)) > 200, lg


class TestReperesMecaniques:
    """Ce que le CODE cherche ne se traduit jamais."""

    @pytest.mark.parametrize("lg", LANGUES)
    def test_les_parametres_survivent(self, lg):
        t = _prompt(lg)
        assert "{nom}" in t, lg
        assert "{langue}" in t, lg

    @pytest.mark.parametrize("lg", LANGUES)
    def test_la_marque_d_apport_est_identique(self, lg):
        """Le code cherche cette chaîne exacte pour séparer l'apport
        du texte : traduite, la séparation échoue en silence et
        l'apport se fond dans la biographie."""
        assert "[non vérifié]" in i18n.t("prompt_biohot_apport", lg), \
            lg

    @pytest.mark.parametrize("lg", LANGUES)
    def test_la_borne_de_longueur_est_chiffree(self, lg):
        """Un modèle respecte mieux « 400 » que « quatre cents »."""
        t = _prompt(lg)
        assert "400" in t or "quatre cents" in t.lower(), lg


class TestRienNeSePerd:
    """Une section absente est une règle absente, et les défauts
    qu'elle corrigeait reviennent."""

    SECTIONS = {
        "en": ("OBJECTIVE", "TONE", "MATERIAL", "RESULT", "EXAMPLE",
               "ABSOLUTE RULE"),
        "fr": ("OBJECTIF", "TON", "MATIÈRE", "RÉSULTAT", "EXEMPLE",
               "RÈGLE ABSOLUE"),
        "de": ("ZIEL", "TON", "MATERIAL", "ERGEBNIS", "BEISPIEL",
               "ABSOLUTE REGEL"),
        "es": ("OBJETIVO", "TONO", "MATERIA", "RESULTADO", "EJEMPLO",
               "REGLA ABSOLUTA"),
        "it": ("OBIETTIVO", "TONO", "MATERIA", "RISULTATO", "ESEMPIO",
               "REGOLA ASSOLUTA"),
        "pt": ("OBJETIVO", "TOM", "MATÉRIA", "RESULTADO", "EXEMPLO",
               "REGRA ABSOLUTA"),
        "nl": ("DOEL", "TOON", "MATERIAAL", "RESULTAAT", "VOORBEELD",
               "ABSOLUTE REGEL"),
    }

    @pytest.mark.parametrize("lg", LANGUES)
    def test_toutes_les_sections_sont_la(self, lg):
        t = _prompt(lg)
        manquantes = [s for s in self.SECTIONS[lg] if s not in t]
        assert manquantes == [], f"{lg} : {manquantes}"

    @pytest.mark.parametrize("lg", LANGUES)
    def test_l_exemple_est_traduit(self, lg):
        """Un exemple resté en français tirerait le modèle vers cette
        langue, quel que soit le reste du prompt."""
        t = _prompt(lg)
        # Chaque langue emploie SES guillemets : « » en français,
        # “ ” en anglais, „ “ en allemand et néerlandais.
        i = max(t.find("«"), t.find("\u201c"), t.find("\u201e"))
        assert i > 0, f"{lg} : aucun guillemet d'exemple"
        if lg != "fr":
            extrait = t[i:i + 300].lower()
            assert "toujours le même appétit" not in extrait, lg

    @pytest.mark.parametrize("lg", LANGUES)
    def test_l_exception_sur_l_orientation_survit(self, lg):
        """C'est la seule permission du prompt : la perdre écarterait
        une information qui compte."""
        # Le contraste vient du PROFIL de collection, non du
        # gabarit : « un hétéro qui tourne gay » n'a de sens que
        # dans une collection gay, et s'inverse ailleurs.
        profils = i18n.t_msg("profils_biohot", lg) or {}
        gay = profils.get("gay") or ("", "", "")
        assert any(m in gay[2].lower() for m in
                   ("hétéro", "hétero", "hetero", "etero",
                    "straight", "heterosexual")), (lg, gay[2][:80])


class TestRegistreDeLangue:
    """« Bite » ne se traduit pas par le terme clinique : le mot doit
    avoir le même registre — celui qu'un adulte emploie, ni médical
    ni puéril. Un prompt en registre médical produit un texte
    médical."""

    CRUS = {
        "en": ("cock", "ass", "fuck"),
        "fr": ("bite", "cul", "baise"),
        "de": ("schwanz", "arsch", "ficken"),
        "es": ("polla", "culo", "follar"),
        "it": ("cazzo", "culo", "scopare"),
        "pt": ("caralho", "cu", "foder"),
        "nl": ("pik", "kont", "neuken"),
    }

    @pytest.mark.parametrize("lg", LANGUES)
    def test_le_registre_cru_est_tenu(self, lg):
        t = _prompt(lg).lower()
        presents = [m for m in self.CRUS[lg] if m in t]
        assert len(presents) >= 2, f"{lg} : {presents}"

    @pytest.mark.parametrize("lg", LANGUES)
    def test_aucun_terme_clinique(self, lg):
        """« Pénis », « rapport sexuel » : le registre médical est
        exactement ce que le prompt cherche à éviter."""
        t = _prompt(lg).lower()
        for mot in ("pénis", "penis", "rapport sexuel",
                    "sexual intercourse", "geschlechtsverkehr"):
            assert mot not in t, f"{lg} : {mot}"


class TestLongueurRaisonnable:

    @pytest.mark.parametrize("lg", LANGUES)
    def test_le_prompt_reste_lisible(self, lg):
        """Il coûte à chaque appel, et un prompt bavard noie ses
        propres règles."""
        assert 800 <= len(_prompt(lg)) <= 2600, f"{lg} : {len(_prompt(lg))}"
