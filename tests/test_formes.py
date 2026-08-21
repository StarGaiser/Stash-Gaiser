# -*- coding: utf-8 -*-
"""
Les formes d'interface, et ce qu'elles disent.

Écrit AVANT le remaniement.

Trois défauts se répondent.

**Un champ de saisie pour un choix fermé.** « Que faire des valeurs
trouvées » accepte trois valeurs — manual, seuil, auto — et se
présente en champ texte. L'utilisateur doit savoir quoi taper, une
faute de frappe passe inaperçue, et rien ne dit ce que chaque valeur
change. Un choix fermé se présente en choix fermé.

**Des onglets qui ne se lisent pas comme des onglets.** Sans
séparation visuelle ni indication d'état, ils passent pour une ligne
de liens. On ne comprend pas qu'on peut cliquer, ni où l'on est.

**« Simple » ne dit rien.** Un onglet se nomme par ce qu'on y trouve,
non par le niveau supposé de qui le lit.
"""

import re
from pathlib import Path

import pytest
import yaml

RACINE = Path(__file__).resolve().parent.parent
CODE = RACINE / "gaizer"


@pytest.fixture(scope="module")
def page():
    return (CODE / "gaizer_page.js").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def manifeste():
    return yaml.safe_load(
        (CODE / "gaizer.yml").read_text(encoding="utf-8"))


# ── La forme suit le contenu ─────────────────────────────────────────
class TestFormeDesChamps:
    """Un choix fermé se présente en choix fermé. Le taper de mémoire
    est une charge inutile, et une faute de frappe passe inaperçue —
    la valeur est simplement ignorée, sans message."""

    FERMES = {
        "applyMode": ("manual", "seuil", "auto"),
        "language": ("", "fr", "en", "de", "es", "it", "pt", "nl"),
        "tagProfile": ("gay", "hetero", "lesbien", "bi", "pan",
                       "trans", "mixte"),
    }

    def test_les_choix_fermes_sont_declares(self, page):
        assert "CHOIX" in page

    def test_chaque_choix_ferme_liste_ses_valeurs(self, page):
        i = page.find("const CHOIX = {")
        fin = page.find("\n  };", i)
        bloc = page[i:fin] if fin > i else page[i:i + 2000]
        for cle in self.FERMES:
            assert cle in bloc, cle

    def test_chaque_valeur_porte_un_libelle(self, page):
        """« seuil » ne dit rien ; « Appliquer au-delà d'une note »
        dit ce qui va se passer."""
        i = page.find("const CHOIX = {")
        fin = page.find("\n  };", i)
        bloc = page[i:fin] if fin > i else page[i:i + 2000]
        # Chaque entrée : une valeur ET un libellé lisible.
        paires = re.findall(r'\["([^"]*)",\s*"([^"]+)"\]', bloc)
        assert len(paires) >= 10, paires
        for valeur, libelle in paires:
            # Le libellé doit être LISIBLE, non plus long : « Gay »
            # se comprend tel quel, « seuil » non. Ce qui compte est
            # qu'il ne soit pas un identifiant technique.
            assert libelle[0].isupper() or libelle[0].isdigit(), \
                (valeur, libelle)
            assert libelle != valeur or valeur[0].isupper(), \
                (valeur, libelle)

    def test_un_booleen_se_presente_en_interrupteur(self, page):
        """Une case à cocher pour « simulation » est correcte, mais
        elle doit dire l'état dans lequel elle met — pas seulement
        être cochée ou non."""
        assert "custom-switch" in page or "form-check" in page \
            or 'type: "checkbox"' in page

    def test_un_nombre_ne_se_saisit_pas_en_texte(self, page):
        """La taille de lot est un nombre : un champ texte accepte
        « vingt-cinq », qui sera silencieusement ignoré."""
        i = page.find("REGLAGES_RAPIDES")
        fin = page.find("\n  ];", i)
        bloc = page[i:fin] if fin > i else page[i:i + 900]
        assert "number" in bloc or "nombre" in bloc


# ── Les onglets se lisent comme des onglets ──────────────────────────
class TestApparenceDesOnglets:
    """Sans séparation ni indication d'état, une barre d'onglets passe
    pour une ligne de liens : on ne comprend ni qu'on peut cliquer, ni
    où l'on est."""

    def test_l_onglet_actif_est_marque(self, page):
        assert "active" in page

    def test_les_onglets_sont_separes_visuellement(self, page):
        """Coller les libellés les rend illisibles — mais c'est
        Bootstrap qui espace, via `nav-tabs` et `nav-item`. Ajouter un
        écart en style le figerait par-dessus le thème, alors que les
        thèmes communautaires ajustent précisément cela."""
        i = page.find("const lien =")
        fin = page.find("\n    };", i)
        bloc = page[i:fin if fin > i else i + 1400]
        assert "nav-item" in bloc and "nav-link" in bloc

    def test_le_role_est_annonce_aux_lecteurs_d_ecran(self, page):
        """Une barre d'onglets sans rôle déclaré est parcourue comme
        une liste de boutons sans lien entre eux."""
        assert 'role: "tab"' in page

    def test_l_etat_actif_est_annonce(self, page):
        assert "aria-selected" in page or "ariaSelected" in page


# ── Les noms disent ce qu'on trouve ──────────────────────────────────
class TestNomsDOnglets:
    """Un onglet se nomme par ce qu'on y trouve, non par le niveau
    supposé de qui le lit. « Simple » ne dit rien : ni ce qu'il
    contient, ni pourquoi commencer là."""

    def test_l_onglet_d_accueil_dit_ce_qu_on_y_fait(self, page):
        i = page.find("o_simple:")
        bloc = page[i:i + 400]
        m = re.search(r'fr:\s*"([^"]+)"', bloc)
        assert m, "libellé français introuvable"
        assert m.group(1).lower() not in ("simple", "basique",
                                          "facile"), m.group(1)

    def test_aucun_onglet_ne_juge_l_utilisateur(self, page):
        for mot in ("Débutant", "Expert", "Novice", "Avancé :"):
            assert mot not in page, mot

    def test_l_interrupteur_dit_ce_qu_il_revele(self, page):
        """« Mode avancé » suppose que l'utilisateur sait ce que ça
        recouvre. « Tout afficher » dit ce qui va se passer."""
        i = page.find("vers_avance:")
        bloc = page[i:i + 300]
        m = re.search(r'fr:\s*"([^"]+)"', bloc)
        assert m and "avancé" not in m.group(1).lower(), \
            m.group(1) if m else "absent"


class TestOngletsSansDoublon:
    """« Enrichir » ne contenait qu'une tâche, et cette tâche figurait
    aussi dans « Première mise en route ». Deux onglets pour le même
    bouton : l'utilisateur cherche la différence et n'en trouve pas.

    La distinction utile n'est pas entre deux façons d'enrichir, mais
    entre CE QU'ON FAIT et CE QU'ON RÈGLE."""

    def test_aucune_tache_dans_deux_onglets(self, page):
        i = page.find("const GROUPES")
        fin = page.find("\n  ];", i)
        bloc = page[i:fin if fin > i else i + 6000]
        modes = re.findall(r'\n\s*\["(\w+)",\s*\n?\s*"', bloc)
        doubles = {m for m in modes if modes.count(m) > 1}
        assert doubles == set(), doubles

    def test_l_onglet_d_accueil_n_est_pas_vide_de_sens(self, page):
        """Un onglet qui ne porte qu'un bouton déjà présent ailleurs
        n'a pas de raison d'être."""
        i = page.find('onglet !== "accueil"')
        if i < 0:
            i = page.find('onglet !== "simple"')
        fin = page.find("GROUPES.map", i)
        bloc = page[i:fin if fin > i else i + 2500]
        modes = set(re.findall(r'mode: "(\w+)"', bloc))
        assert len(modes) >= 2, modes


class TestNomsSansCondescendance:
    """« Première mise en route » se lit comme une consigne pour
    débutant, et reste affiché des mois après la première fois.

    Un onglet se nomme par ce qu'on y trouve, indépendamment du moment
    où l'on est."""

    def test_aucun_nom_ne_suppose_un_moment(self, page):
        for cle in ("g_demarrage", "g_courant"):
            i = page.find(cle + ": { en:")
            bloc = page[i:i + 300]
            m = re.search(r'fr:\s*"([^"]+)"', bloc)
            assert m, cle
            libelle = m.group(1).lower()
            for mot in ("première", "premier", "démarrage", "début"):
                assert mot not in libelle, (cle, m.group(1))

    def test_les_noms_disent_ce_qu_on_y_trouve(self, page):
        """Un nom d'onglet doit permettre de choisir sans ouvrir."""
        for cle in ("g_demarrage", "g_courant"):
            i = page.find(cle + ": { en:")
            m = re.search(r'fr:\s*"([^"]+)"', page[i:i + 300])
            assert m and 2 <= len(m.group(1)) <= 22, \
                m.group(1) if m else cle

    def test_l_ordre_place_l_accueil_en_premier(self, page):
        liens = re.findall(r'lien\("(\w+)"', page)
        assert liens and liens[0] in ("accueil", "simple"), liens[:3]


class TestOrdreLibelleChamp:
    """Le libellé était placé APRÈS le champ : on lisait « [Écrire
    au-delà d'une note] Que faire des valeurs trouvées » — la réponse
    avant la question.

    La convention est constante depuis les premiers formulaires : on
    lit ce qu'on demande, puis on répond. L'inverser oblige à revenir
    en arrière pour comprendre ce qu'on vient de voir.

    Une case à cocher fait exception : « [x] Simulation » se lit dans
    cet ordre, parce que la case EST la réponse et que le texte la
    qualifie."""

    def test_le_libelle_precede_le_champ(self, page):
        i = page.find("REGLAGES_RAPIDES.map(")
        fin = page.find("\n        }),", i)
        bloc = page[i:fin if fin > i else i + 2200]
        # L'ordre dépend de la forme : le contrôle porte sur le
        # fait qu'il soit DÉCIDÉ, non recopié en dur.
        rendu = bloc.split("return e(")[-1]
        assert "avant ? libelle : champ" in rendu, rendu[-160:]

    def test_la_case_a_cocher_garde_son_ordre(self, page):
        """« [x] Simulation » se lit dans cet ordre : la case est la
        réponse, le texte la qualifie."""
        i = page.find("REGLAGES_RAPIDES.map(")
        fin = page.find("\n        }),", i)
        bloc = page[i:fin if fin > i else i + 2200]
        assert "oui-non" in bloc

    def test_le_champ_est_associe_a_son_libelle(self, page):
        """Sans association, un lecteur d'écran annonce un champ sans
        nom, et cliquer le texte ne place pas le curseur."""
        i = page.find("REGLAGES_RAPIDES.map(")
        fin = page.find("\n        }),", i)
        bloc = page[i:fin if fin > i else i + 2200]
        assert 'e("label"' in bloc

    def test_les_champs_d_argument_precedent_leur_bouton(self, page):
        """Sur une ligne de tâche, le champ doit venir avant le
        bouton qui le consomme."""
        i = page.find("_champArgument(arg,")
        j = page.find('tr("lancer")', i)
        assert 0 < i < j, "le champ doit précéder le bouton"


class TestApparenceHeriteeDeStash:
    """Stash habille déjà ses onglets : bordure basse de deux pixels
    et couleur d'accent sur l'actif, définies dans sa feuille de
    style.

    Forcer ces valeurs en styles ne rend pas l'apparence plus juste —
    elle la fige. Un thème sombre, un thème clair, un thème
    communautaire : chacun redéfinit ces règles, et un style en ligne
    l'emporte sur tous. Le plugin détonnerait précisément là où il
    devrait se fondre.

    Ce qui appartient au plugin, ce sont les CLASSES ; ce qui
    appartient au thème, ce sont les couleurs et les bordures."""

    def test_aucune_couleur_forcee_sur_les_onglets(self, page):
        i = page.find("const lien =")
        fin = page.find("\n    };", i)
        bloc = page[i:fin if fin > i else i + 1400]
        for propriete in ("color:", "borderBottom", "background"):
            assert propriete not in bloc, propriete

    def test_aucune_opacite_forcee(self, page):
        """L'opacité était mon remède à un contraste que je jugeais
        faible : c'est au thème d'en décider."""
        i = page.find("const lien =")
        fin = page.find("\n    };", i)
        bloc = page[i:fin if fin > i else i + 1400]
        assert "opacity" not in bloc

    def test_les_classes_de_bootstrap_sont_employees(self, page):
        i = page.find("const lien =")
        fin = page.find("\n    };", i)
        bloc = page[i:fin if fin > i else i + 1400]
        assert "nav-link" in bloc and "active" in bloc

    def test_la_barre_garde_sa_bordure(self, page):
        """La supprimer détachait les onglets de leur contenu."""
        i = page.find("nav nav-tabs")
        bloc = page[max(0, i - 200):i + 400]
        assert "borderBottom: 0" not in bloc

    def test_le_bouton_n_est_pas_un_lien_deguise(self, page):
        """`btn btn-link` ajoute un soulignement au survol et une
        couleur de lien qui se battent avec l'état actif."""
        i = page.find("const lien =")
        fin = page.find("\n    };", i)
        bloc = page[i:fin if fin > i else i + 1400]
        assert "btn btn-link" not in bloc


class TestIconesDOnglets:
    """Stash place une icône devant chaque libellé d'onglet. Sans
    elle, la barre du plugin se distingue au premier coup d'œil de
    toutes les autres — c'est précisément ce qu'il fallait éviter.

    Les icônes viennent de l'API : `libraries.FontAwesomeSolid` pour
    les glyphes, `libraries.ReactFontAwesome` pour le composant. Les
    supposer présentes casserait silencieusement chez qui a une autre
    version, donc leur absence doit dégrader vers le texte seul."""

    def test_les_icones_viennent_de_l_api(self, page):
        assert "FontAwesomeSolid" in page
        assert "ReactFontAwesome" in page

    def test_chaque_onglet_a_son_icone(self, page):
        i = page.find("const ICONES")
        assert i > 0, "la table des icônes doit exister"
        fin = page.find("\n  };", i)
        bloc = page[i:fin if fin > i else i + 900]
        for cle in ("simple", "g_demarrage", "g_courant", "g_menage",
                    "g_diagnostic", "g_reparation", "redaction"):
            assert cle in bloc, cle

    def test_l_absence_d_icone_ne_casse_rien(self, page):
        """Une version de Stash sans ces bibliothèques doit afficher
        le texte, non une page blanche."""
        i = page.find("function Icone")
        assert i > 0
        bloc = page[i:i + 700]
        assert "return null" in bloc or "!" in bloc

    def test_l_icone_precede_le_libelle(self, page):
        i = page.find("const lien =")
        fin = page.find("\n    };", i)
        bloc = page[i:fin if fin > i else i + 1400]
        assert bloc.find("Icone") < bloc.rfind("libelle")

    def test_l_icone_est_ignoree_par_les_lecteurs_d_ecran(self, page):
        """Le libellé la suit : la faire annoncer doublerait
        l'information."""
        i = page.find("function Icone")
        bloc = page[i:i + 700]
        assert "aria-hidden" in bloc or "ariaHidden" in bloc


class TestPlaceEtNomDeLaRedaction:
    """« Rédaction » nomme une activité, non un but : on ne sait ni ce
    qu'on y règle, ni sur quoi cela agit.

    Ce qui s'y trouve — les instructions données au modèle et la
    liberté qu'on lui laisse — gouverne les textes que le plugin
    écrit. C'est le PROLONGEMENT de l'enrichissement, pas une annexe,
    et sa place est à côté."""

    def test_le_nom_dit_ce_qui_est_gouverne(self, page):
        i = page.find("o_redaction: { en:")
        bloc = page[i:i + 320]
        m = re.search(r'fr:\s*"([^"]+)"', bloc)
        assert m, "libellé français introuvable"
        libelle = m.group(1).lower()
        assert libelle != "rédaction", m.group(1)
        # Il doit évoquer le texte produit ou le modèle.
        assert any(mot in libelle for mot in
                   ("texte", "modèle", "biograph", "présentation",
                    "généré", "écrit")), m.group(1)

    def test_le_nom_dit_que_c_est_une_machine(self, page):
        """« Rédigé » laisse croire qu'un humain a écrit. Le lecteur
        doit savoir qu'une machine a produit ces textes avant de les
        lire comme une source."""
        i = page.find("o_redaction: { en:")
        m = re.search(r'fr:\s*"([^"]+)"', page[i:i + 320])
        assert m and "rédigé" not in m.group(1).lower(), \
            m.group(1) if m else "absent"

    def test_il_suit_immediatement_l_enrichissement(self, page):
        """Séparé par quatre onglets, il passait pour un réglage sans
        rapport avec ce qu'on venait de lancer."""
        i = page.find("nav nav-tabs")
        fin = page.find("</ul", i)
        bloc = page[i:fin if fin > i else i + 900]
        liens = re.findall(r'lien\("(\w+)"', bloc)
        assert "redaction" in liens, liens
        assert liens.index("redaction") <= liens.index("simple") + 1, \
            liens

    def test_il_reste_visible_en_mode_simple(self, page):
        """Ce qui gouverne les textes écrits n'est pas une affaire
        d'expert : quelqu'un qui trouve les présentations trop sages
        doit pouvoir agir sans chercher un interrupteur."""
        i = page.find("nav nav-tabs")
        fin = page.find("</ul", i)
        bloc = page[i:fin if fin > i else i + 900]
        j = bloc.find('lien("redaction"')
        assert j > 0
        # Aucune condition d'affichage sur cette ligne.
        ligne = bloc[max(0, bloc.rfind("\n", 0, j)):j]
        assert "avance ?" not in ligne, ligne


class TestTexteGenere:
    """« Textes rédigés » suggère une rédaction humaine. Ces textes
    sont produits par un modèle de langage, et le dire n'est pas un
    détail de vocabulaire : c'est ce qui prévient qu'ils peuvent se
    tromper, et ce qui justifie qu'on les relise.

    Le plugin le dit partout ailleurs — la divulgation du README, le
    pied de fiabilité des biographies. L'onglet doit s'accorder."""

    def test_l_onglet_dit_que_les_textes_sont_generes(self, page):
        i = page.find("o_redaction: { en:")
        bloc = page[i:i + 340]
        m = re.search(r'fr:\s*"([^"]+)"', bloc)
        assert m, "libellé français introuvable"
        libelle = m.group(1).lower()
        assert "généré" in libelle or "genere" in libelle, m.group(1)
        assert "rédigé" not in libelle, m.group(1)

    def test_toutes_les_langues_suivent(self, page):
        """Un libellé traduit à moitié laisse la moitié des
        utilisateurs devant l'ancienne ambiguïté."""
        i = page.find("o_redaction: { en:")
        bloc = page[i:i + 340]
        for lg in ("en", "de", "es", "it", "pt", "nl"):
            assert re.search(rf'{lg}:\s*"[^"]+"', bloc), lg

    def test_le_vocabulaire_est_constant(self, page):
        """Employer « rédigé » ailleurs rouvrirait l'ambiguïté que le
        libellé vient de fermer."""
        i = page.find("d_redaction:")
        bloc = page[i:i + 500]
        texte = bloc[bloc.find("fr:"):bloc.find("de:")].lower()
        assert "rédige" not in texte and "rédigé" not in texte, texte[:120]


class TestZoneDeRedaction:
    """Deux manques rendent cet onglet inutilisable pour qui découvre.

    **La zone de saisie est vide** quand aucun prompt n'a été
    enregistré. L'utilisateur ne sait ni ce que le plugin demande au
    modèle par défaut, ni comment formuler le sien : il devrait
    inventer un prompt sans avoir vu celui qui marche.

    **Le modèle employé n'est nommé nulle part.** Régler la
    température et les instructions sans savoir qui les recevra, c'est
    régler à l'aveugle — et le résultat dépend au moins autant du
    modèle que du prompt."""

    def test_le_prompt_par_defaut_sert_de_modele(self, page):
        """Vide, la zone n'apprend rien. Le prompt par défaut y figure
        comme point de départ : on part de ce qui marche."""
        i = page.find("function Redaction")
        fin = page.find("\n  function ", i + 10)
        bloc = page[i:fin if fin > i else i + 3000]
        assert "prompt_defaut" in bloc or "promptDefaut" in bloc

    def test_le_defaut_est_lu_du_serveur(self, page):
        """Le recopier dans le JavaScript le ferait diverger du prompt
        réellement employé, sans que rien ne le signale."""
        i = page.find("function Redaction")
        fin = page.find("\n  function ", i + 10)
        bloc = page[i:fin if fin > i else i + 3000]
        assert "GQL" in bloc

    def test_le_modele_employe_est_nomme(self, page):
        i = page.find("function Redaction")
        fin = page.find("\n  function ", i + 10)
        bloc = page[i:fin if fin > i else i + 3000]
        assert "modele" in bloc.lower() or "aiBiohot" in bloc

    def test_le_modele_dit_d_ou_il_vient(self, page):
        """« mistral:pixtral » ne dit pas si c'est le réglage propre à
        cette tâche ou le modèle par défaut : l'utilisateur qui veut
        en changer ne saurait pas où."""
        assert "m_source" in page or "modele_source" in page

    def test_l_absence_de_modele_est_dite(self, page):
        """Sans modèle configuré, rien ne sera écrit : le taire
        laisserait croire à une panne."""
        assert "m_aucun" in page

    def test_un_bouton_revient_au_defaut(self, page):
        """Avoir gâché son prompt sans pouvoir revenir dissuade
        d'essayer."""
        i = page.find("function Redaction")
        fin = page.find("\n  function ", i + 10)
        bloc = page[i:fin if fin > i else i + 3000]
        assert "defaut" in bloc.lower()


class TestChaqueArgumentAnnonceEstSaisissable:
    """Cinq tâches du panneau annoncent un argument dans leur
    description sans offrir de champ pour le saisir.

    C'est le défaut déjà corrigé pour douze autres, revenu par
    l'ajout de nouvelles tâches : dire qu'un argument existe sans
    permettre de le donner oblige à passer par l'écran des plugins de
    Stash — l'utilisateur qui lit la description croit pouvoir agir,
    essaie, et la tâche s'exécute sans son argument.

    Le contrôle porte sur la COHÉRENCE entre ce qui est annoncé et ce
    qui est offert, non sur une liste figée : ajouter une tâche à
    argument sans son champ le fera échouer."""

    def _modes_du_panneau(self, page):
        return set(re.findall(r'\n\s+\["(\w+)",\s*\n?\s*"', page))

    def _champs_offerts(self, page):
        i = page.find("const ARGUMENTS")
        fin = page.find("\n  };", i)
        bloc = page[i:fin if fin > i else i + 2000]
        return set(re.findall(r'\n\s+(\w+): \["', bloc))

    def test_toute_tache_a_argument_offre_son_champ(self, page,
                                                    manifeste):
        au_panneau = self._modes_du_panneau(page)
        offerts = self._champs_offerts(page)
        manquants = []
        for t in manifeste["tasks"]:
            mode = (t.get("defaultArgs") or {}).get("mode")
            desc = str(t.get("description") or "")
            if not mode or "rgument" not in desc:
                continue
            # Une tâche de fiche prend son identifiant du contexte :
            # l'utilisateur n'a rien à saisir.
            if mode not in au_panneau:
                continue
            if mode not in offerts:
                manquants.append(f"{t['name']} ({mode})")
        assert manquants == [], manquants

    def test_aucun_champ_sans_tache(self, page):
        """Un champ offert pour une tâche absente du panneau est du
        code mort qui laisse croire à une fonctionnalité."""
        # Un champ peut servir une tâche de FICHE, absente du
        # panneau : le champ y apparaît quand même, sur la fiche.
        # L'orphelin véritable est celui qu'aucune tâche ne connaît.
        import ast
        arbre = ast.parse(
            (RACINE / "gaizer" / "gaizer.py").read_text(
                encoding="utf-8"))
        modes = set()
        for n in ast.walk(arbre):
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and t.id == "TASKS":
                        modes = {k.value for k in n.value.keys}
        assert modes, "registre introuvable"
        orphelins = [c for c in self._champs_offerts(page)
                     if c not in modes]
        assert orphelins == [], orphelins

    def test_chaque_champ_dit_ce_qu_il_attend(self, page):
        """« champs » ne dit pas quoi taper : l'invite doit le dire,
        sans quoi le champ ne vaut pas mieux que son absence."""
        i = page.find("const ARGUMENTS")
        fin = page.find("\n  };", i)
        bloc = page[i:fin if fin > i else i + 2000]
        # La structure porte : clé, forme, invite [, min, max].
        # L'invite est le TROISIÈME élément.
        muets = []
        for nom, forme, invite in re.findall(
                r'\n\s+\w+: \["(\w+)",\s*"(\w+)",\s*\n?\s*"([^"]*)"',
                bloc):
            # Sur un champ numérique, l'invite porte le DÉFAUT :
            # « 9.0 » dit plus qu'une phrase, et la plage est dans
            # la bulle.
            if forme == "nombre":
                assert invite.replace(".", "").isdigit(), \
                    f"{nom} : le défaut doit être un nombre"
                continue
            if len(invite) < 8:
                muets.append(f"{nom} : {invite!r}")
        assert muets == [], muets


class TestChaqueChampDitCeQuOnYMet:
    """Un champ vide n'apprend rien : l'utilisateur doit deviner ce
    qu'on attend, et une faute passe inaperçue — la valeur est
    simplement ignorée, sans message.

    Ce qui aide dépend du champ : la valeur par DÉFAUT quand il y en
    a une, une PLAGE quand la valeur est bornée, un EXEMPLE quand la
    forme est libre. Une paraphrase du nom du champ n'apprend rien —
    « Nom du champ » sur un champ nommé « champ » est du bruit."""

    def test_chaque_reglage_texte_porte_un_repere(self, manifeste):
        """Stash n'offre qu'un champ texte pour un réglage : ni liste
        déroulante, ni invite grise. Le seul endroit où dire ce qu'on
        attend est la description."""
        muets = []
        for cle, v in manifeste["settings"].items():
            if v.get("type") != "STRING":
                continue
            desc = str(v.get("description") or "")
            if not any(m in desc for m in
                       ("Ex.", "ex.", "Défaut", "défaut", "Vide",
                        "vide", "Valeurs", "Default")):
                muets.append(cle)
        assert muets == [], muets

    def test_les_arguments_fermes_ne_sont_pas_du_texte(self, page):
        """« 1 pour relire » demandait de taper « 1 » de mémoire.
        Une case dit la même chose sans qu'on ait à deviner quelle
        valeur compte pour vrai."""
        i = page.find("const ARGUMENTS")
        fin = page.find("\n  };", i)
        bloc = page[i:fin if fin > i else i + 3000]
        for nom, forme in re.findall(
                r'\n\s+\w+: \["(\w+)",\s*"(\w+)"', bloc):
            if nom in ("relire", "installer", "toutes",
                       "incertaines"):
                assert forme == "oui-non", f"{nom} : {forme}"

    def test_un_argument_borne_declare_sa_plage(self, page):
        """Une note entre 0 et 10 : la plage borne la saisie, et le
        défaut dit ce qu'on attend."""
        i = page.find("const ARGUMENTS")
        fin = page.find("\n  };", i)
        bloc = page[i:fin if fin > i else i + 3000]
        m = re.search(r'"nombre",\s*\n?\s*"([\d.]+)",\s*(\d+),\s*(\d+)',
                      bloc)
        assert m, "aucun argument numérique borné"
        defaut, mini, maxi = float(m.group(1)), int(m.group(2)), \
            int(m.group(3))
        assert mini <= defaut <= maxi, (mini, defaut, maxi)

    def test_le_rendu_emploie_la_forme_declaree(self, page):
        """Déclarer une forme sans la rendre ne servirait à rien."""
        i = page.find("function _champArgument")
        fin = page.find("\n  function ", i + 10)
        bloc = page[i:fin if fin > i else i + 2500]
        for forme in ("oui-non", "choix", "nombre"):
            assert f'"{forme}"' in bloc, forme

    def test_un_champ_numerique_montre_sa_plage(self, page):
        """Dans la bulle : l'afficher à l'écran encombrerait la
        ligne, la taire obligerait à essayer."""
        i = page.find("function _champArgument")
        bloc = page[i:i + 2500]
        assert "entre ${mini} et ${maxi}" in bloc
