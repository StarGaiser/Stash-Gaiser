# -*- coding: utf-8 -*-
"""
Tests sur données réelles, fabriquées localement.

Le jeu d'essai n'est pas dans le dépôt : il est produit sur place par
`tools/capturer_fixtures.py` depuis la médiathèque de celui qui lance
les tests. Chacun éprouve le plugin sur son propre réel, personne ne
publie les données de personnes réelles.

Ces tests s'ignorent proprement quand le jeu est absent : un
contributeur sans Stash lance quand même le reste de la suite.

Ce qu'ils cherchent est particulier. Les autres tests vérifient que le
plugin fait ce qu'il dit sur des cas choisis par moi. Ceux-ci le
confrontent à ce que la réalité contient vraiment — des noms d'une
seule partie, des biographies vides, des scènes sans studio, des
valeurs que personne n'aurait imaginées. Tous les défauts sérieux
trouvés jusqu'ici venaient de là, aucun d'un cas inventé.
"""

import json
from pathlib import Path

import pytest

import collecte
import doublons
import groupes
import roles
import scoring
import similarite
import tags as mod_tags
from faux import FauxStash, faux_contexte


JEU = Path(__file__).parent / "fixtures_locales" / "collection.json"

pytestmark = pytest.mark.skipif(
    not JEU.exists(),
    reason="jeu d'essai absent — le produire avec "
           "tools/capturer_fixtures.py")


@pytest.fixture(scope="module")
def collection():
    return json.loads(JEU.read_text(encoding="utf-8"))


@pytest.fixture
def monde(collection):
    st = FauxStash(performers=collection["performers"],
                   studios=collection["studios"],
                   scenes=collection["scenes"],
                   tags=collection["tags"])
    return st, faux_contexte({}, st)


# ── Ce qui ne doit jamais lever ──────────────────────────────────────
class TestAucuneValeurNeFaitTomber:
    """Un défaut trouvé en production interrompait TOUTE une fiche sur
    une date « 0000-00-00 ». Les fonctions qui lisent des valeurs
    doivent encaisser n'importe quoi."""

    def test_normalisation_des_noms(self, collection):
        for p in collection["performers"]:
            assert isinstance(similarite._sim_cles(p["name"]), (set, list,
                                                                tuple))

    def test_lecture_des_dates(self, collection):
        for s in collection["scenes"]:
            scoring._date(s.get("date"))

    def test_lecture_des_entiers(self, collection):
        for p in collection["performers"]:
            for champ in ("height_cm", "weight", "penis_length"):
                scoring._entier(p.get(champ))

    def test_lecture_des_roles(self, collection):
        for p in collection["performers"]:
            cf = p.get("custom_fields") or {}
            for champ in ("position", "enrich_position", "pouvoir"):
                position, pouvoir = roles.lire(cf.get(champ))
                assert position is None or position in roles.POSITIONS
                assert pouvoir is None or pouvoir in roles.POUVOIRS

    def test_familles_de_tags(self, collection):
        table = mod_tags.charger()
        for t in collection["tags"]:
            fam = mod_tags.famille_de(t["name"], table)
            assert fam == "" or fam in table["familles"]

    def test_motifs_de_parties(self, collection):
        for s in collection["scenes"]:
            groupes._lire_partie(s.get("title") or "")

    def test_nettoyage_des_studios(self, collection):
        for st in collection["studios"]:
            assert isinstance(collecte._nettoie_studio(st["name"]), str)


# ── Ce que le moteur produit sur du réel ─────────────────────────────
class TestMoteurSurDonneesReelles:

    def test_toute_note_est_bornee(self, collection):
        """Un seuil non borné acceptait -3 et 11 : le défaut avait été
        trouvé par les tests, il ne doit pas revenir par des données."""
        cfg = scoring.DEFAUTS
        for p in collection["performers"]:
            valeurs = {"iafd": p.get("height_cm"),
                       "gevi": p.get("height_cm"),
                       "men": p.get("weight")}
            valeurs = {k: v for k, v in valeurs.items() if v}
            if len(valeurs) < 2:
                continue
            for c in scoring.evaluer("height_cm", valeurs, cfg):
                assert 0.0 <= c["note"] <= 10.0

    def test_les_conflits_enregistres_sont_relisibles(self, collection):
        """Le rapport de conflit est du texte : s'il ne se relit pas,
        l'arbitrage écraserait une valeur par une autre mal
        découpée."""
        import taches_arbitrage
        vus = 0
        for p in collection["performers"]:
            rap = str((p.get("custom_fields") or {})
                      .get("enrich_rapport") or "")
            if "CONFLIT" not in rap:
                continue
            for m in taches_arbitrage._CONFLIT.finditer(rap):
                vus += 1
                champ, _actuel, propose, _srcs, note = m.groups()
                assert champ and propose.strip()
                assert 0.0 <= float(note) <= 10.0
        if vus == 0:
            pytest.skip("aucun conflit dans ce jeu")

    def test_la_provenance_enregistree_se_relit(self, collection):
        """Même exigence côté interface : une ligne mal découpée
        s'affiche en vrac dans la colonne du champ."""
        import re
        motif = re.compile(
            r"^([\w_]+)\s*:\s*(.+?)\s*\(([\d.]+)/10")
        lus = total = 0
        for p in collection["performers"]:
            src = str((p.get("custom_fields") or {})
                      .get("enrich_sources") or "")
            src = re.sub(r"\s*·\s*(auto|manuel)\s+[\d-]+\s*$", "", src)
            for ligne in src.split(" | "):
                if not ligne.strip():
                    continue
                total += 1
                if motif.match(ligne):
                    lus += 1
        if total == 0:
            pytest.skip("aucune trace dans ce jeu")
        # Certaines lignes ne portent pas de note (urls, photo) : le
        # gros doit néanmoins se relire.
        assert lus / total > 0.5, \
            f"seules {lus}/{total} lignes de provenance se relisent"


# ── Ce que les tâches font sur du réel ───────────────────────────────
class TestTachesSurDonneesReelles:

    def test_detection_de_doublons_ne_leve_pas(self, monde):
        _st, ctx = monde
        ctx.args = {}
        doublons.detect_duplicates(ctx)
        doublons.detect_duplicates_studios(ctx)

    def test_la_detection_ne_detruit_rien(self, monde):
        """Sur des fiches réelles, dont beaucoup se ressemblent : la
        détection signale, elle ne fusionne jamais d'elle-même."""
        st, ctx = monde
        avant = set(st.performers), set(st.studios)
        ctx.args = {}
        doublons.detect_duplicates(ctx)
        doublons.detect_duplicates_studios(ctx)
        assert set(st.performers) == avant[0]
        assert set(st.studios) == avant[1]

    def test_groupes_ne_leve_pas(self, monde):
        _st, ctx = monde
        ctx.args = {}
        groupes.detect_groupes(ctx)

    def test_les_groupes_proposes_ont_plusieurs_parties(self, monde):
        """Un « groupe » d'une seule scène n'est pas un film en
        plusieurs parties."""
        st, ctx = monde
        ctx.args = {}
        groupes.detect_groupes(ctx)
        for g in st.groups.values():
            liees = [s for s in st.scenes.values()
                     if any(str((x.get("group") or {}).get("id"))
                            == str(g["id"])
                            for x in (s.get("groups") or []))]
            if liees:
                assert len(liees) >= 2, g.get("name")


# ── Représentativité du jeu ──────────────────────────────────────────
class TestJeuDEssai:
    """Un jeu qui ne contient aucun cas limite rassure à tort."""

    def test_taille_suffisante(self, collection):
        assert len(collection["performers"]) >= 10
        assert len(collection["scenes"]) >= 10

    def test_diversite_des_fiches(self, collection):
        """Sans variété, ces tests ne valent pas mieux qu'un cas
        choisi par moi."""
        perfs = collection["performers"]
        constats = [
            any(not (p.get("details") or "").strip() for p in perfs),
            any((p.get("custom_fields") or {}) for p in perfs),
            any(not (p.get("custom_fields") or {}) for p in perfs),
            any(p.get("alias_list") for p in perfs),
        ]
        assert sum(constats) >= 3, \
            "jeu trop homogène — le regénérer plus large"
