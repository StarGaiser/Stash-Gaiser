# -*- coding: utf-8 -*-
"""
Lecture du chemin complet, pas seulement du nom de fichier.

Écrit AVANT le code.

Une médiathèque est rangée, et son rangement porte de l'information :
« /nas/GAY - ManUpFilms - The.Power.Of.Persuasion/scene.mp4 » nomme le
studio dans le dossier et le titre dans le même segment.

Le plugin ne lisait que le nom de fichier. Sur une collection réelle,
cent vingt-six scènes sans studio se trouvaient dans des dossiers qui
portaient ce studio en toutes lettres — information gratuite, exacte,
et ignorée.

**C'est plus fiable que la vision et infiniment moins cher.** Aucun
appel réseau, aucun modèle, aucune hallucination possible : le texte
est là, il suffit de le lire.

**Mais un chemin n'est pas une preuve.** Un dossier peut être mal
nommé, ou nommer autre chose que ce qu'il contient. Le rapprochement
reste exact, et rien n'est écrasé.
"""

import pytest

import chemins
from faux import FauxStash, faux_contexte, performer, scene, studio


def _ctx(**reglages):
    reglages.setdefault("sourceChemin", True)
    ctx = faux_contexte(reglages, FauxStash())
    ctx.args = {}
    return ctx


# ── Découpage du chemin ──────────────────────────────────────────────
class TestSegments:
    """Chaque dossier du chemin est un indice possible, et les
    séparateurs internes en découpent d'autres : « GAY - ManUpFilms -
    Titre » porte trois segments dans un seul dossier."""

    def test_les_dossiers_sont_rendus(self):
        segs = chemins.segments("/nas/Videos/ManUpFilms/scene.mp4")
        assert "ManUpFilms" in segs
        # « Videos » est un dossier de RANGEMENT : le retenir
        # produirait un studio de ce nom.
        assert "Videos" not in segs

    def test_les_separateurs_internes_decoupent(self):
        segs = chemins.segments(
            "/nas/GAY - ManUpFilms - The Power/scene.mp4")
        assert "ManUpFilms" in segs
        assert "The Power" in segs

    def test_le_nom_de_fichier_est_inclus(self):
        segs = chemins.segments("/nas/x/Masqulin - Scene 4.mp4")
        assert any("Masqulin" in s for s in segs)

    def test_l_extension_est_retiree(self):
        segs = chemins.segments("/nas/x/Titre.mp4")
        assert "Titre" in segs
        assert not any(".mp4" in s for s in segs)

    def test_les_points_font_office_d_espaces(self):
        """« The.Power.Of.Persuasion » est un titre, pas un mot."""
        segs = chemins.segments("/nas/The.Power.Of.Persuasion/x.mp4")
        assert "The Power Of Persuasion" in segs

    def test_les_segments_inutiles_sont_ecartes(self):
        """« nas », « videos », « 1080p » ne nomment rien."""
        segs = chemins.segments("/mnt/nas/Videos/1080p/HD/x.mp4")
        for inutile in ("nas", "Videos", "1080p", "HD", "mnt"):
            assert inutile not in segs, inutile

    def test_valeurs_absurdes(self):
        for brut in ("", None, "/", "///", "x"):
            assert isinstance(chemins.segments(brut), list)


# ── Reconnaissance ───────────────────────────────────────────────────
class TestReconnaissance:
    """Un segment ne vaut que s'il désigne une entité connue. Créer
    depuis un chemin serait aventureux : un dossier mal nommé
    produirait un studio fantôme."""

    STUDIOS = {"hardkinks": "9", "manupfilms": "1",
               "next door studios": "2"}

    def test_un_studio_du_chemin_est_reconnu(self):
        assert chemins.studio_du_chemin(
            "/nas/Hardkinks 3/scene.mp4", self.STUDIOS) == "9"

    def test_le_numero_de_volume_est_ignore(self):
        """« Hardkinks 3 » et « HardKinks 1 » désignent le même
        studio : le numéro est une commodité de rangement."""
        for d in ("Hardkinks 3", "HardKinks 1", "Hardkinks 4"):
            assert chemins.studio_du_chemin(
                f"/nas/{d}/scene.mp4", self.STUDIOS) == "9", d

    def test_un_studio_au_milieu_d_un_dossier(self):
        assert chemins.studio_du_chemin(
            "/nas/GAY - ManUpFilms - Titre/x.mp4",
            self.STUDIOS) == "1"

    def test_un_studio_inconnu_ne_rapproche_rien(self):
        assert chemins.studio_du_chemin(
            "/nas/StudioInconnu/x.mp4", self.STUDIOS) is None

    def test_aucun_rapprochement_partiel(self):
        """« Next Door » ne doit pas ramener « Next Door Studios » :
        deux studios peuvent partager un préfixe."""
        assert chemins.studio_du_chemin(
            "/nas/Next Door/x.mp4", self.STUDIOS) is None

    def test_le_dossier_le_plus_proche_prime(self):
        """« /Hardkinks/ManUpFilms/x.mp4 » : le dossier immédiat
        décrit mieux le fichier que la racine."""
        assert chemins.studio_du_chemin(
            "/nas/Hardkinks/ManUpFilms/x.mp4", self.STUDIOS) == "1"


class TestInterpretes:
    INDEX = {"archie fox": "1", "dean young": "2"}

    def test_un_interprete_du_chemin_est_reconnu(self):
        ids = chemins.interpretes_du_chemin(
            "/nas/x/Archie Fox - scene.mp4", self.INDEX)
        assert "1" in ids

    def test_plusieurs_interpretes(self):
        ids = chemins.interpretes_du_chemin(
            "/nas/Archie Fox and Dean Young/x.mp4", self.INDEX)
        assert set(ids) == {"1", "2"}

    def test_un_nom_inconnu_ne_rapproche_rien(self):
        assert chemins.interpretes_du_chemin(
            "/nas/Quelqu'un Dautre/x.mp4", self.INDEX) == []

    def test_aucun_rapprochement_partiel(self):
        for chemin in ("/nas/Archie/x.mp4", "/nas/Fox/x.mp4"):
            assert chemins.interpretes_du_chemin(
                chemin, self.INDEX) == [], chemin


class TestTitre:
    """Le segment le plus long qui ne nomme ni studio ni interprète
    est le meilleur candidat au titre."""

    def test_un_titre_est_extrait(self):
        titre = chemins.titre_du_chemin(
            "/nas/GAY - ManUpFilms - The Power Of Persuasion/x.mp4",
            {"manupfilms"}, set())
        assert titre == "The Power Of Persuasion"

    def test_le_studio_n_est_pas_pris_pour_un_titre(self):
        titre = chemins.titre_du_chemin(
            "/nas/ManUpFilms/x.mp4", {"manupfilms"}, set())
        assert titre != "ManUpFilms"

    def test_un_titre_trop_court_est_refuse(self):
        assert chemins.titre_du_chemin("/nas/x/ab.mp4", set(),
                                       set()) is None

    def test_les_mentions_techniques_sont_ecartees(self):
        for brut in ("1080p", "x264", "WEB-DL", "part 1"):
            assert chemins.titre_du_chemin(
                f"/nas/x/{brut}.mp4", set(), set()) is None, brut


# ── La tâche ─────────────────────────────────────────────────────────
class TestTache:

    def _monde(self, chemin, **champs):
        st = FauxStash(
            scenes=[scene(10, "", files=[{"path": chemin}], **champs)],
            studios=[studio(9, "Hardkinks")],
            performers=[performer(1, "Archie Fox")])
        ctx = _ctx(applyMode="auto", sourceChemin=True)
        ctx.stash = st
        return st, ctx

    def test_un_studio_est_applique(self):
        st, ctx = self._monde("/nas/Hardkinks 3/scene.mp4")
        chemins.lire_chemins(ctx)
        assert (st.scenes["10"].get("studio") or {}).get("id") == "9"

    def test_un_studio_existant_n_est_pas_ecrase(self):
        st, ctx = self._monde("/nas/Hardkinks 3/scene.mp4",
                              studio={"id": "99"})
        chemins.lire_chemins(ctx)
        assert st.scenes["10"]["studio"]["id"] == "99"

    def test_un_interprete_est_relie(self):
        st, ctx = self._monde("/nas/x/Archie Fox - scene.mp4")
        chemins.lire_chemins(ctx)
        ids = {q["id"] for q in st.scenes["10"].get("performers") or []}
        assert "1" in ids

    def test_les_interpretes_existants_ne_sont_pas_remplaces(self):
        st, ctx = self._monde("/nas/x/Archie Fox - scene.mp4",
                              performers=[{"id": "2", "name": "Dean"}])
        chemins.lire_chemins(ctx)
        ids = {q["id"] for q in st.scenes["10"].get("performers") or []}
        assert "2" in ids

    def test_en_mode_manuel_rien_n_est_ecrit(self):
        st, ctx = self._monde("/nas/Hardkinks 3/scene.mp4")
        ctx.settings["applyMode"] = "manual"
        chemins.lire_chemins(ctx)
        assert not st.scenes["10"].get("studio")

    def test_simulation(self):
        import noyau
        st, ctx = self._monde("/nas/Hardkinks 3/scene.mp4")
        ctx.settings["dryRun"] = True
        noyau._activer_simulation(ctx)
        chemins.lire_chemins(ctx)
        assert not st.scenes["10"].get("studio")

    def test_la_provenance_dit_que_c_est_le_chemin(self):
        """Une valeur tirée du rangement n'a pas le statut d'une
        source documentaire : l'utilisateur doit pouvoir la
        distinguer."""
        st, ctx = self._monde("/nas/Hardkinks 3/scene.mp4")
        chemins.lire_chemins(ctx)
        cf = st.scenes["10"].get("custom_fields") or {}
        trace = str(cf.get("enrich_sources") or "").lower()
        assert "chemin" in trace or "dossier" in trace

    def test_collection_vide_ne_leve_pas(self):
        ctx = _ctx()
        ctx.stash = FauxStash()
        chemins.lire_chemins(ctx)

    def test_une_scene_sans_fichier_ne_leve_pas(self):
        st = FauxStash(scenes=[scene(10, "Sans fichier")])
        ctx = _ctx()
        ctx.stash = st
        chemins.lire_chemins(ctx)


class TestNomsEntreParentheses:
    """Un rangement courant place la distribution entre parenthèses :
    « Worship (Abraham Montenegro, Dylan Ayrton) ». Ne pas les lire
    perdrait des liens que le titre annonce lui-même, et laisserait
    les noms DANS le titre — où ils n'ont rien à faire."""

    INDEX = {"abraham montenegro": "1", "dylan ayrton": "2",
             "archie fox": "3"}

    def test_les_noms_entre_parentheses_sont_lus(self):
        ids = chemins.interpretes_du_chemin(
            "/nas/x/Worship (Abraham Montenegro, Dylan Ayrton).mp4",
            self.INDEX)
        assert set(ids) == {"1", "2"}

    def test_le_titre_est_debarrasse_des_noms(self):
        """« Worship (Abraham Montenegro, Dylan Ayrton) » comme titre
        de scène est illisible : le titre est « Worship »."""
        titre = chemins.titre_du_chemin(
            "/nas/x/Worship (Abraham Montenegro, Dylan Ayrton).mp4",
            set(), {"abrahammontenegro", "dylanayrton"})
        assert titre == "Worship"

    def test_une_parenthese_qui_n_est_pas_une_distribution(self):
        """« Scene 4 (Director's Cut) » : la parenthèse fait partie du
        titre si elle ne nomme personne de connu."""
        titre = chemins.titre_du_chemin(
            "/nas/x/Le Grand Voyage (Director's Cut).mp4",
            set(), set())
        assert titre and "Voyage" in titre

    def test_les_crochets_aussi(self):
        ids = chemins.interpretes_du_chemin(
            "/nas/x/Titre [Archie Fox].mp4", self.INDEX)
        assert "3" in ids

    def test_un_titre_reduit_a_des_noms_est_refuse(self):
        """« (Abraham Montenegro, Dylan Ayrton) » n'est pas un
        titre."""
        titre = chemins.titre_du_chemin(
            "/nas/x/(Abraham Montenegro, Dylan Ayrton).mp4",
            set(), {"abrahammontenegro", "dylanayrton"})
        assert titre is None


class TestDossiersTechniques:
    """Une médiathèque contient des dossiers de travail — « rapatrie
    USB », « à trier », « backup » — qui ne nomment rien de ce qu'ils
    contiennent. Les prendre pour des titres écrirait n'importe quoi
    sur des dizaines de scènes.

    Les reconnaître exhaustivement est impossible : chacun range à sa
    façon. Mais deux signaux se généralisent — un vocabulaire de
    manipulation de fichiers, et l'absence de structure de titre."""

    @pytest.mark.parametrize("brut", [
        "rapatrie USB", "a trier", "à trier", "backup", "sauvegarde",
        "en cours", "old", "ancien", "recup", "récupéré", "copie",
        "import", "a classer", "to sort", "misc", "divers 2",
    ])
    def test_un_dossier_de_travail_n_est_pas_un_titre(self, brut):
        assert chemins.titre_du_chemin(
            f"/nas/{brut}/scene.mp4", set(), set()) is None, brut

    def test_un_vrai_titre_passe(self):
        for brut in ("The Power Of Persuasion", "Watching Sports",
                     "Le Grand Voyage", "Bareback Auditions"):
            assert chemins.titre_du_chemin(
                f"/nas/{brut}/scene.mp4", set(), set()) == brut, brut

    def test_un_dossier_de_travail_n_est_pas_un_studio(self):
        assert chemins.studio_du_chemin(
            "/nas/rapatrie USB/scene.mp4", {"usb": "1"}) is None


class TestSeparateursReels:
    """Les séparateurs varient d'une médiathèque à l'autre, et le
    rangement réel est moins régulier que les exemples : « GAY
    -TreasureIslandMedia - Titre » n'a pas d'espace avant le tiret,
    « _rapatrie_USB » emploie des tirets bas.

    Un découpage trop strict laisse le studio DANS le titre, et un
    filtre qui n'anticipe pas les variantes laisse passer les dossiers
    de travail."""

    def test_un_tiret_sans_espace_avant_decoupe(self):
        segs = chemins.segments(
            "/nas/GAY -TreasureIslandMedia - Brazil/x.mp4")
        assert "TreasureIslandMedia" in segs

    def test_les_tirets_bas_encadrent_aussi(self):
        assert chemins.titre_du_chemin(
            "/nas/_rapatrie_USB/x.mp4", set(), set()) is None

    def test_un_dossier_de_travail_prefixe(self):
        for brut in ("_rapatrie_USB", "__a_trier", "_backup_2024"):
            assert chemins.titre_du_chemin(
                f"/nas/{brut}/x.mp4", set(), set()) is None, brut

    @pytest.mark.parametrize("brut", [
        "OTB WEB-DL 1080p AVC", "1080p AVC AAC", "x264 AAC 5 1",
        "WEB DL 720p", "BluRay REMUX", "H264 AAC",
    ])
    def test_une_suite_de_mentions_techniques_n_est_pas_un_titre(
            self, brut):
        """Un segment fait de sigles d'encodage décrit le fichier, non
        son contenu — même quand aucun mot pris isolément ne suffit à
        l'écarter."""
        assert chemins.titre_du_chemin(
            f"/nas/x/{brut}.mp4", set(), set()) is None, brut

    def test_un_titre_avec_un_chiffre_reste_accepte(self):
        """« Bareback Auditions 12 » est un vrai titre : écarter tout
        ce qui contient un nombre perdrait des volumes numérotés."""
        assert chemins.titre_du_chemin(
            "/nas/Bareback Auditions 12/x.mp4", set(), set())

    def test_le_studio_est_retire_du_titre(self):
        """Quand le studio est reconnu dans le même segment, il ne
        doit pas rester dans le titre."""
        titre = chemins.titre_du_chemin(
            "/nas/GAY -TreasureIslandMedia - Brazil Fever/x.mp4",
            {"treasureislandmedia"}, set())
        assert titre == "Brazil Fever"


class TestQueueTechnique:
    """Un nom de fichier de partage suit une convention :
    « [MEN][Gay]Sacred Band Of Thebes 2018 VO 1080p WEB AAC H264-N ».
    Le titre est au milieu — les crochets le précèdent, la queue
    technique le suit.

    Écarter le segment entier perdrait un vrai titre ; le garder tel
    quel écrit une ligne illisible sur la fiche."""

    def test_les_crochets_de_tete_sont_retires(self):
        titre = chemins.titre_du_chemin(
            "/nas/x/[MEN][Gay]Sacred Band Of Thebes.mp4",
            set(), set())
        assert titre == "Sacred Band Of Thebes"

    def test_la_queue_technique_est_coupee(self):
        titre = chemins.titre_du_chemin(
            "/nas/x/Sacred Band Of Thebes 2018 VO 1080p WEB AAC 2 0 "
            "H264-NTb.mp4", set(), set())
        assert titre == "Sacred Band Of Thebes"

    def test_les_deux_ensemble(self):
        titre = chemins.titre_du_chemin(
            "/nas/x/[Gay]Harder They Come 2025 VO 1080p WEB AAC 2 0 "
            "H264.mp4", set(), set())
        assert titre == "Harder They Come"

    def test_un_titre_qui_finit_par_un_nombre_survit(self):
        """« Bareback Auditions 12 » : le nombre fait partie du titre,
        seule une ANNÉE suivie de mentions techniques est une queue."""
        assert chemins.titre_du_chemin(
            "/nas/x/Bareback Auditions 12.mp4", set(), set()) \
            == "Bareback Auditions 12"

    def test_un_titre_sans_queue_est_intact(self):
        assert chemins.titre_du_chemin(
            "/nas/x/The Power Of Persuasion.mp4", set(), set()) \
            == "The Power Of Persuasion"

    def test_le_studio_entre_crochets_est_reconnu(self):
        """« [MEN] » nomme le studio : le lire vaut mieux que le
        jeter."""
        assert chemins.studio_du_chemin(
            "/nas/x/[MEN][Gay]Titre.mp4", {"men": "3"}) == "3"


class TestNomsColles:
    """Un studio s'écrit de plusieurs façons dans un chemin :
    « Treasure Island », « TreasureIslandMedia »,
    « [Treasure.Island.Media] ». Les points font office d'espaces, les
    majuscules internes marquent les mots, et un suffixe comme
    « Media » ou « Studios » peut manquer.

    Le rapprochement EXACT reste la règle — mais sur une forme
    comparable qui ignore ces variations d'écriture, non sur les
    caractères bruts."""

    STUDIOS = {"treasure island": "72", "hard kinks": "9",
               "next door studios": "2"}

    def test_les_points_tiennent_lieu_d_espaces(self):
        assert chemins.studio_du_chemin(
            "/nas/[Treasure.Island.Media][Gay]Titre/x.mp4",
            self.STUDIOS) == "72"

    def test_un_nom_colle_est_reconnu(self):
        assert chemins.studio_du_chemin(
            "/nas/GAY -TreasureIslandMedia - Brazil/x.mp4",
            self.STUDIOS) == "72"

    def test_un_suffixe_de_studio_est_tolere(self):
        """« Treasure Island Media » et « Treasure Island » désignent
        le même studio : « Media », « Studios », « Films » sont des
        suffixes d'usage."""
        for variante in ("Treasure Island Media",
                         "Treasure Island Studios",
                         "Treasure Island Films"):
            assert chemins.studio_du_chemin(
                f"/nas/{variante}/x.mp4", self.STUDIOS) == "72", variante

    def test_un_suffixe_ne_cree_pas_de_confusion(self):
        """« Next Door » sans son suffixe ne doit PAS ramener « Next
        Door Studios » : retirer un suffixe du CATALOGUE serait
        dangereux, seul celui du texte lu l'est."""
        assert chemins.studio_du_chemin(
            "/nas/Next Door/x.mp4", self.STUDIOS) is None

    def test_un_autre_studio_n_est_pas_confondu(self):
        assert chemins.studio_du_chemin(
            "/nas/Treasure Hunt/x.mp4", self.STUDIOS) is None


class TestFormulesDeCompilation:
    """Un dossier de compilation nomme son interprète après une
    formule : « The Best Of Marcel Dupont », « Collection Julien Martin »,
    « Dirk Caber Anthology ».

    Le rapprochement exact échoue sur le segment entier — « The Best
    Of Marcel Dupont » n'est pas un nom. Retirer la formule laisse le
    nom, qui se rapproche alors normalement.

    Le contrôle reste EXACT sur ce qui reste : « The Best Of Archie »
    ne doit pas ramener « Archie Fox »."""

    INDEX = {"marcel dupont": "1", "dante colle": "2",
             "archie fox": "3"}

    @pytest.mark.parametrize("dossier", [
        "The Best Of Marcel Dupont", "Best Of Marcel Dupont",
        "BEST OF MARCEL DUPONT", "Le Meilleur De Marcel Dupont",
        "Collection Marcel Dupont", "Marcel Dupont Collection",
        "Marcel Dupont Anthology", "The Marcel Dupont Collection",
    ])
    def test_l_interprete_est_reconnu(self, dossier):
        ids = chemins.interpretes_du_chemin(
            f"/nas/{dossier}/x.mp4", self.INDEX)
        assert "1" in ids, dossier

    def test_le_rapprochement_reste_exact(self):
        """Retirer la formule ne doit pas ouvrir la porte au
        rapprochement partiel."""
        assert chemins.interpretes_du_chemin(
            "/nas/The Best Of Archie/x.mp4", self.INDEX) == []

    def test_un_inconnu_ne_rapproche_rien(self):
        assert chemins.interpretes_du_chemin(
            "/nas/Best Of Quelqu Un/x.mp4", self.INDEX) == []

    def test_le_titre_ne_garde_pas_la_formule(self):
        """« The Best Of Marcel Dupont » n'est pas un titre de scène :
        c'est le nom du recueil, et l'interprète en a été extrait."""
        titre = chemins.titre_du_chemin(
            "/nas/The Best Of Marcel Dupont/x.mp4", set(),
            {"marceldupont"})
        assert titre is None or "Marcel" not in titre

    def test_une_formule_seule_ne_designe_personne(self):
        assert chemins.interpretes_du_chemin(
            "/nas/Best Of/x.mp4", self.INDEX) == []

    def test_un_vrai_titre_contenant_best_survit(self):
        """« Best Friends » n'est pas une formule de compilation."""
        assert chemins.titre_du_chemin(
            "/nas/Best Friends Forever/x.mp4", set(), set()) \
            == "Best Friends Forever"
