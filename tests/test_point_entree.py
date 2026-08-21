# -*- coding: utf-8 -*-
"""
Le point d'entrée, que rien n'éprouvait.

Un audit a relevé une corrélation risque↔couverture INVERSE :
`scoring.py` est couvert à 99 % et ne fait que calculer, tandis que
`gaizer.py` est à 0 % et porte tout ce qui décide — le routage des
cinquante-deux tâches, la lecture des arguments, le rattrapage des
pannes.

C'est l'inverse de ce qu'il faudrait. Un défaut de calcul se voit dans
un résultat ; un défaut de routage fait qu'une tâche ne s'exécute
jamais, ou qu'une autre s'exécute à sa place — et personne ne
s'aperçoit qu'une tâche « a marché » alors qu'elle n'a rien fait.

Ce fichier éprouve ce qui décide, non ce qui calcule.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import gaizer  # noqa: E402


class TestRegistreDesTaches:
    """Le registre relie un nom de mode à une fonction. Une entrée
    manquante fait échouer une tâche que le manifeste annonce ; une
    entrée en trop annonce une tâche qui n'existe pas."""

    def test_le_registre_n_est_pas_vide(self):
        assert len(gaizer.TASKS) > 40

    def test_chaque_mode_pointe_vers_une_fonction(self):
        for nom, f in gaizer.TASKS.items():
            assert callable(f), nom

    def test_aucun_mode_en_double(self):
        """Un dictionnaire les écraserait silencieusement : le
        contrôle porte sur le CODE, où le doublon est visible."""
        code = (RACINE / "gaizer" / "gaizer.py").read_text(
            encoding="utf-8")
        i = code.find("TASKS = {")
        fin = code.find("\n}", i)
        bloc = code[i:fin]
        cles = [ligne.split('"')[1] for ligne in bloc.split("\n")
                if ligne.strip().startswith('"')]
        doubles = {c for c in cles if cles.count(c) > 1}
        assert doubles == set(), doubles

    def test_chaque_tache_du_manifeste_existe(self):
        """Une tâche annoncée sans mode correspondant échoue au clic,
        sans rien dire d'utile."""
        import yaml
        d = yaml.safe_load(
            (RACINE / "gaizer" / "gaizer.yml").read_text(
                encoding="utf-8"))
        manquants = []
        for t in d["tasks"]:
            mode = (t.get("defaultArgs") or {}).get("mode")
            if mode and mode not in gaizer.TASKS:
                manquants.append(f"{t['name']} → {mode}")
        assert manquants == [], manquants


class TestMain:
    """`main()` fait tout : sauvegarde des réglages, reprise d'un
    passage interrompu, routage, et rapport à Stash par la sortie
    standard.

    Chaque étape peut échouer sans que la suivante doive s'arrêter —
    une sauvegarde de réglages qui échoue ne justifie pas de refuser
    d'enrichir. C'est ce qui est éprouvé ici."""

    def _sortie(self, capsys):
        return capsys.readouterr().out.strip()

    def test_un_mode_connu_est_appele(self, monkeypatch, capsys):
        vus = []
        monkeypatch.setitem(gaizer.TASKS, "essai",
                            lambda ctx: vus.append("appelé"))
        monkeypatch.setattr(gaizer, "Context", lambda: _faux_ctx("essai"))
        gaizer.main()
        assert vus == ["appelé"]
        assert "ok" in self._sortie(capsys)

    def test_un_mode_inconnu_est_signale(self, monkeypatch, capsys):
        """Sans message, l'utilisateur voit une tâche « réussie » qui
        n'a rien fait."""
        messages = []
        monkeypatch.setattr(gaizer.log, "error",
                            lambda m, *a, **k: messages.append(str(m)))
        monkeypatch.setattr(gaizer, "Context",
                            lambda: _faux_ctx("nexistepas"))
        gaizer.main()
        assert messages
        assert "error" in self._sortie(capsys)

    def test_un_echec_de_tache_est_rapporte(self, monkeypatch,
                                            capsys):
        """Stash lit la sortie standard : une exception avalée
        laisserait croire à une réussite."""
        def casse(ctx):
            raise RuntimeError("panne d'essai")
        monkeypatch.setitem(gaizer.TASKS, "essai", casse)
        monkeypatch.setattr(gaizer.log, "error", lambda *a, **k: None)
        monkeypatch.setattr(gaizer, "Context",
                            lambda: _faux_ctx("essai"))
        gaizer.main()
        sortie = self._sortie(capsys)
        assert "error" in sortie and "panne d'essai" in sortie

    def test_une_sauvegarde_ratee_n_empeche_pas_la_tache(
            self, monkeypatch, capsys):
        """Une sauvegarde de réglages qui échoue ne justifie pas de
        refuser d'enrichir."""
        vus = []
        monkeypatch.setattr(
            gaizer, "_sauver_reglages",
            lambda ctx: (_ for _ in ()).throw(OSError("disque")))
        monkeypatch.setitem(gaizer.TASKS, "essai",
                            lambda ctx: vus.append("appelé"))
        monkeypatch.setattr(gaizer, "Context",
                            lambda: _faux_ctx("essai"))
        gaizer.main()
        assert vus == ["appelé"]

    def test_une_reprise_ratee_n_empeche_pas_la_tache(
            self, monkeypatch, capsys):
        vus = []
        monkeypatch.setattr(
            gaizer, "_reprise_opportuniste",
            lambda ctx: (_ for _ in ()).throw(RuntimeError("réseau")))
        monkeypatch.setitem(gaizer.TASKS, "essai",
                            lambda ctx: vus.append("appelé"))
        monkeypatch.setattr(gaizer, "Context",
                            lambda: _faux_ctx("essai"))
        gaizer.main()
        assert vus == ["appelé"]

    def test_la_sortie_est_toujours_du_json(self, monkeypatch,
                                            capsys):
        """Stash la parse : une sortie libre casserait son
        affichage."""
        monkeypatch.setitem(gaizer.TASKS, "essai", lambda ctx: None)
        monkeypatch.setattr(gaizer, "Context",
                            lambda: _faux_ctx("essai"))
        gaizer.main()
        rendu = json.loads(self._sortie(capsys))
        assert isinstance(rendu, dict) and rendu




def _faux_ctx(mode):
    """Le minimum que `main()` réclame, sans joindre de serveur.

    Éprouver le point d'entrée demandait de pouvoir l'appeler sans
    Stash : c'est précisément ce qui manquait, et ce qui explique ses
    zéro pour cent de couverture.
    """
    # `mode` est à la fois l'argument et le nom de la méthode : dans
    # le corps de la classe, le second masque le premier. Le capturer
    # d'abord lève l'ambiguïté.
    valeur = mode

    class Ctx:
        args = {"mode": valeur}
        settings = {}

        def mode(self):
            return valeur
    return Ctx()


@pytest.fixture(autouse=True)
def _sans_effet(monkeypatch):
    """Aucun test de ce fichier ne doit joindre un vrai serveur."""
    monkeypatch.setattr(gaizer.log, "info", lambda *a, **k: None)
    monkeypatch.setattr(gaizer.log, "debug", lambda *a, **k: None)
    monkeypatch.setattr(gaizer, "_sauver_reglages", lambda ctx: None)
    monkeypatch.setattr(gaizer, "_reprise_opportuniste",
                        lambda ctx: None)
