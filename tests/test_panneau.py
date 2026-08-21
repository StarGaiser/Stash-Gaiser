# -*- coding: utf-8 -*-
"""
Le panneau vu par quelqu'un qui découvre.

Écrit AVANT le remaniement.

Quarante-neuf tâches réparties sur cinq groupes tiennent sur un seul
écran défilant. C'est trop : celui qui découvre ne sait pas par où
commencer, et celui qui connaît cherche.

**Un onglet par intention.** Chaque groupe devient un onglet — on ne
voit que ce qu'on est venu chercher, et le nombre de tâches cesse
d'être une charge.

**Un mode simple, ouvert par défaut.** Un utilisateur qui installe le
plugin veut que sa médiathèque soit complétée, pas choisir entre
quarante-neuf actions. Un bouton, et ce qui a été écrit reste
annulable.

**Rien n'est retiré.** Le mode détaillé donne accès à tout, pour qui
veut piloter.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
PANNEAU = RACINE / "gaizer" / "gaizer_page.js"


@pytest.fixture(scope="module")
def code():
    return PANNEAU.read_text(encoding="utf-8")


# ── Onglets ──────────────────────────────────────────────────────────
class TestOnglets:
    """Un groupe de tâches par onglet : on ne voit que ce qu'on est
    venu chercher."""

    GROUPES = ("g_demarrage", "g_courant", "g_menage",
               "g_diagnostic", "g_reparation")

    def test_chaque_groupe_a_son_onglet(self, code):
        # Les onglets se déclarent par leur clé de traduction.
        for groupe in self.GROUPES:
            assert f'"{groupe}"' in code, groupe

    def test_un_seul_groupe_est_affiche_a_la_fois(self, code):
        """Afficher tout revient à n'avoir pas d'onglets : chaque
        groupe est rendu SOUS CONDITION de l'onglet courant."""
        assert "onglet !== cle ? null" in code

    def test_le_mode_simple_est_le_premier_onglet(self, code):
        """C'est ce que voit celui qui ouvre le panneau sans savoir ce
        qu'il cherche. L'ordre à l'écran est celui des appels à
        `lien()`, non celui des déclarations dans le fichier."""
        liens = re.findall(r'lien\("(\w+)"', code)
        assert liens and liens[0] == "simple", liens[:4]

    def test_le_mode_simple_est_ouvert_par_defaut(self, code):
        assert 'useState("simple")' in code

    def test_le_nombre_d_onglets_reste_lisible(self, code):
        """Au-delà de sept, les onglets débordent et se replient."""
        onglets = set(re.findall(r'lien\("(\w+)"', code))
        assert len(onglets) <= 7, sorted(onglets)


# ── Mode simple ──────────────────────────────────────────────────────
class TestModeSimple:
    """Celui qui installe le plugin veut que sa médiathèque soit
    complétée, pas choisir entre quarante-neuf actions."""

    def test_un_bouton_unique_est_propose(self, code):
        assert "enrichir_tout" in code

    def test_le_mode_simple_explique_ce_qui_va_se_passer(self, code):
        """Un bouton qui écrit dans la collection doit dire quoi avant
        d'être pressé."""
        assert "s_explication" in code

    def test_l_annulation_est_offerte_a_cote(self, code):
        """Ce qui rassure n'est pas la promesse que rien ne casse,
        c'est de voir le bouton qui défait."""
        i = code.find('onglet !== "simple"')
        fin = code.find("GROUPES.map", i)
        bloc = code[i:fin if fin > i else i + 3000]
        assert "undo_last" in bloc, \
            "l'annulation doit figurer dans le mode simple"

    def test_le_mode_simple_ne_propose_rien_de_destructif(self, code):
        """Fusionner, supprimer, écraser : ces actions demandent un
        choix éclairé, donc le mode détaillé."""
        i = code.find('onglet !== "simple"')
        fin = code.find("GROUPES.map", i)
        bloc = code[i:fin if fin > i else i + 3000]
        for destructif in ("merge_marked", "clear_proposals",
                           "retirer_non_confirme", "purger_tags"):
            assert destructif not in bloc, destructif


# ── Ce qui est à valider ─────────────────────────────────────────────
class TestChampsAValider:
    """Un enrichissement automatique écrit des valeurs dont certaines
    méritent un regard. Les signaler DANS la fiche, là où l'utilisateur
    regarde déjà, évite de lui demander d'aller chercher un rapport."""

    @pytest.fixture(scope="class")
    def panneau_fiche(self):
        return (RACINE / "gaizer" / "gaizer.js").read_text(
            encoding="utf-8")

    def test_les_valeurs_incertaines_sont_signalees(self,
                                                    panneau_fiche):
        assert "a_valider" in panneau_fiche or \
            "aValider" in panneau_fiche

    def test_la_provenance_reste_visible(self, panneau_fiche):
        """Signaler qu'une valeur est douteuse sans dire d'où elle
        vient n'aide pas à trancher."""
        assert "enrich_sources" in panneau_fiche

    def test_un_bouton_valide_depuis_la_fiche(self, panneau_fiche):
        """Aller dans le panneau de commande pour accepter une valeur
        qu'on regarde est une gymnastique inutile."""
        assert "accepter" in panneau_fiche.lower()


class TestValidationEnUnClic:
    """Un signalement qui ne peut pas être levé devient du bruit :
    l'utilisateur voit la pastille, ne sait qu'en faire, et cesse de
    la regarder.

    La validation est TOUT OU RIEN. Cocher champ par champ
    reproduirait l'éditeur de Stash en moins bien ; pour corriger une
    valeur précise, l'édition normale de la fiche est le bon outil, et
    corriger une valeur la valide de fait."""

    @pytest.fixture(scope="class")
    def fiche(self):
        return (RACINE / "gaizer" / "gaizer.js").read_text(
            encoding="utf-8")

    def test_un_bouton_valide_toute_la_fiche(self, fiche):
        assert "valider_tout" in fiche

    def test_le_bouton_n_apparait_que_s_il_y_a_a_valider(self, fiche):
        """Un bouton toujours visible sur une fiche sans rien à
        vérifier est du bruit permanent. C'est l'APPEL à `B(...)` qui
        doit être conditionné, non sa déclaration de libellé."""
        i = fiche.find('B("valider_tout"')
        assert i > 0, "le bouton doit être posé par B()"
        avant = fiche[max(0, i - 600):i]
        assert "aVerifier" in avant and "if (" in avant

    def test_aucune_case_a_cocher_par_champ(self, fiche):
        """Cocher champ par champ reproduirait l'éditeur de Stash en
        moins bien."""
        assert 'type: "checkbox"' not in fiche

    def test_le_bouton_appelle_la_tache_serveur(self, fiche):
        """La logique vit côté serveur : dans le JavaScript, elle
        échapperait aux tests et à la simulation."""
        i = fiche.find('B("valider_tout"')
        bloc = fiche[i:i + 400]
        assert "valider_fiche" in bloc


class TestTacheDeValidation:
    """Le bouton appelle une tâche : la logique vit côté serveur, non
    dans le JavaScript, sans quoi elle échapperait aux tests et à la
    simulation."""

    @pytest.fixture(scope="class")
    def manifeste(self):
        import yaml
        return yaml.safe_load(
            (RACINE / "gaizer" / "gaizer.yml").read_text(
                encoding="utf-8"))

    def test_la_tache_existe(self, manifeste):
        modes = {(t.get("defaultArgs") or {}).get("mode")
                 for t in manifeste["tasks"]}
        assert "valider_fiche" in modes

    def test_elle_prend_un_identifiant(self):
        import taches_arbitrage
        from faux import FauxStash, faux_contexte, performer
        st = FauxStash(performers=[performer(1, "Archie", custom_fields={
            "enrich_sources": "country: FR (5.0/10 · iafd)"})])
        ctx = faux_contexte({}, st)
        ctx.args = {"performer_id": "1"}
        taches_arbitrage.valider_fiche(ctx)
        cf = st.performers["1"].get("custom_fields") or {}
        assert "5.0/10" not in str(cf.get("enrich_sources") or "")

    def test_la_valeur_n_est_pas_touchee(self):
        """Valider dit « j'ai regardé », pas « réécris »."""
        import taches_arbitrage
        from faux import FauxStash, faux_contexte, performer
        st = FauxStash(performers=[performer(
            1, "Archie", country="FR",
            custom_fields={"enrich_sources": "country: FR (5.0/10 · x)"})])
        ctx = faux_contexte({}, st)
        ctx.args = {"performer_id": "1"}
        taches_arbitrage.valider_fiche(ctx)
        assert st.performers["1"]["country"] == "FR"

    def test_sans_identifiant_ne_leve_pas(self):
        import taches_arbitrage
        from faux import FauxStash, faux_contexte, performer
        st = FauxStash(performers=[performer(1, "Archie")])
        ctx = faux_contexte({}, st)
        ctx.args = {}
        taches_arbitrage.valider_fiche(ctx)

    def test_simulation(self):
        import noyau
        import taches_arbitrage
        from faux import FauxStash, faux_contexte, performer
        st = FauxStash(performers=[performer(1, "Archie", custom_fields={
            "enrich_sources": "country: FR (5.0/10 · iafd)"})])
        ctx = faux_contexte({"dryRun": True}, st)
        noyau._activer_simulation(ctx)
        ctx.args = {"performer_id": "1"}
        taches_arbitrage.valider_fiche(ctx)
        cf = st.performers["1"].get("custom_fields") or {}
        assert "5.0/10" in str(cf.get("enrich_sources") or "")

    def test_la_validation_est_reversible(self):
        """Comme toute écriture du plugin : l'historique la défait."""
        import taches_arbitrage
        from faux import FauxStash, faux_contexte, performer
        st = FauxStash(performers=[performer(1, "Archie", custom_fields={
            "enrich_sources": "country: FR (5.0/10 · iafd)"})])
        ctx = faux_contexte({}, st)
        ctx.args = {"performer_id": "1"}
        taches_arbitrage.valider_fiche(ctx)
        cf = st.performers["1"].get("custom_fields") or {}
        assert cf.get("enrich_historique")


class TestMiseEnPage:
    """Chaque onglet avait sa propre mise en page : l'un une carte,
    l'autre des colonnes, un troisième des champs bruts. Passer de
    l'un à l'autre demandait de se réorienter à chaque fois.

    Une seule enveloppe pour tous : le contenu change, le cadre non.
    C'est ce qui fait qu'on cesse de regarder l'interface pour
    regarder ce qu'elle contient."""

    def test_une_seule_enveloppe_pour_tous_les_onglets(self, code):
        """Un composant partagé, plutôt que la même structure
        recopiée — qui divergerait à la première retouche."""
        assert "function Onglet(" in code

    def test_chaque_onglet_a_un_titre_et_une_explication(self, code):
        """Un onglet qui ne dit pas à quoi il sert oblige à lire les
        tâches pour le deviner."""
        assert "d_simple" in code
        for groupe in ("d_g_demarrage", "d_g_courant", "d_g_menage",
                       "d_g_diagnostic", "d_g_reparation"):
            assert groupe in code, groupe

    def test_les_taches_portent_une_description(self, code):
        """Un libellé seul ne dit pas ce qui va être écrit. La
        description tient sous le libellé, en gris."""
        assert "description" in code or "aide" in code

    def test_les_boutons_portent_une_bulle(self, code):
        """« Lancer » et « Simuler » ne disent pas ce qu'ils font de
        différent : la bulle l'explique sans encombrer."""
        assert "title:" in code

    def test_les_onglets_portent_une_bulle(self, code):
        """La bulle dit à quoi sert l'onglet AVANT de cliquer : c'est
        ce qui évite de tous les ouvrir pour trouver le bon."""
        i = code.find("const lien =")
        fin = code.find("\n    };", i)
        bloc = code[i:fin if fin > i else i + 1400]
        assert "title:" in bloc


class TestLibelles:
    """Un libellé de tâche est lu par quelqu'un qui cherche quoi
    lancer. Il doit tenir sur une ligne et commencer par le verbe."""

    def _hors_tables(self, code):
        """Le panneau sans ses tables de configuration : ARGUMENTS
        nomme des champs de saisie, REGLAGES_RAPIDES des réglages,
        ONGLETS_SIMPLES des groupes. Aucune n'est une tâche."""
        for marque, fin_m in (("const CHOIX_ARGUMENT", "\n  };"),
                              ("const CHOIX = {", "\n  };"),
                               ("const ARGUMENTS", "\n  };"),
                              ("const REGLAGES_RAPIDES", "\n  ];"),
                              ("const ONGLETS_SIMPLES", ";")):
            i = code.find(marque)
            if i < 0:
                continue
            f = code.find(fin_m, i)
            if f > i:
                code = code[:i] + code[f + len(fin_m):]
        return code

    def _libelles(self, code):
        """Le LIBELLÉ est le premier texte du tuple ; ce qui suit est
        la description, qui a le droit d'être longue et d'expliquer."""
        import re as _re
        return _re.findall(r'\[\s*"[\w_]+",\s*\n?\s*"([^"]+)"',
                           self._hors_tables(code))

    def test_aucun_libelle_a_rallonge(self, code):
        """Au-delà d'une cinquantaine de caractères, le libellé se
        replie et la ligne devient illisible."""
        longs = [x for x in self._libelles(code) if len(x) > 46]
        assert longs == [], longs

    def test_aucune_parenthese_explicative(self, code):
        """Ce qui tenait entre parenthèses appartient à la
        description, non au libellé."""
        avec = [x for x in self._libelles(code)
                if "(" in x and "GZ" not in x]
        assert avec == [], avec

    def test_les_libelles_sont_scannables(self, code):
        """Un libellé se scanne : soit un VERBE — on cherche une
        action — soit un NOM D'OBJET quand la tâche porte sur une
        famille entière. « 1. Scènes » dit par quoi commencer mieux
        que « Traiter les scènes », et « Rapport des tags » nomme ce
        qu'on obtient.

        Ce qui est proscrit, c'est le mélange : une phrase entière,
        une parenthèse explicative, un libellé qui se replie."""
        import re as _re
        fautes = []
        for x in self._libelles(code):
            # Un numéro d'ordre précède parfois le verbe :
            # « 1. Scènes : identifier » dit par quoi commencer.
            nu = re.sub(r"^\d+\.\s*", "", x)
            premier = nu.split(" ")[0].lower().strip("'")
            verbe = _re.match(r".*(er|ir|re|oir|yer)$", premier)
            # Un nom d'objet est acceptable s'il tient en trois mots :
            # au-delà, c'est une phrase.
            nom_court = len(nu.split(" ")) <= 3
            if not verbe and not nom_court:
                fautes.append(x)
        assert fautes == [], fautes


class TestRepartitionFichePanneau:
    """Une action qui porte sur UNE fiche appartient à la fiche ; une
    action qui balaie la collection appartient au panneau.

    Les mélanger produit deux défauts. Dans le panneau, trois boutons
    « Appliquer les propositions » — un par famille — que rien ne
    distingue à l'œil alors que la fiche en offre déjà un, précis et
    contextuel. Et sur la fiche, on cherche ce qu'on ne trouve pas.

    La règle : si l'action a besoin d'un identifiant, sa place est sur
    la fiche."""

    def test_le_panneau_ne_duplique_pas_les_actions_de_fiche(self,
                                                             code):
        """« Appliquer les propositions » existe sur chaque fiche,
        où il porte sur ce qu'on regarde. Le répéter en trois boutons
        de balayage crée une confusion sans rien apporter."""
        for tache in ("apply_accepted_scenes", "apply_accepted_studios"):
            assert tache not in code, tache

    def test_une_seule_application_de_masse_subsiste(self, code):
        """Balayer la collection reste utile après un gros
        enrichissement : un bouton, pas trois."""
        assert code.count('["apply_accepted"') <= 1

    def test_les_actions_sur_une_fiche_ne_sont_pas_dans_le_panneau(
            self, code):
        """Elles y demanderaient de saisir un identifiant à la main."""
        for tache in ("enrich_one_performer", "enrich_one_scene",
                      "enrich_one_studio", "valider_fiche"):
            assert f'["{tache}"' not in code, tache


class TestRolesIntegres:
    """Déduire un rôle n'a pas de sens en solo : c'est une lecture de
    la documentation DÉJÀ collectée sur un interprète. La proposer
    comme une tâche séparée oblige l'utilisateur à comprendre qu'il
    faut d'abord enrichir, puis relancer autre chose.

    Sa place est dans l'enrichissement des interprètes, dont elle est
    une étape."""

    def test_la_tache_solo_disparait_du_panneau(self, code):
        assert '["deduire_roles"' not in code

    def test_la_deduction_suit_l_enrichissement(self):
        """Elle s'exécute sur les fiches qui viennent d'être
        enrichies, quand la documentation est fraîche."""
        code = (RACINE / "gaizer" / "performers.py").read_text(
            encoding="utf-8")
        assert "deduire_role" in code

    def test_elle_reste_desactivable(self):
        """Elle appelle un modèle de langage : qui n'en veut pas doit
        pouvoir s'en passer."""
        import yaml
        d = yaml.safe_load(
            (RACINE / "gaizer" / "gaizer.yml").read_text(
                encoding="utf-8"))
        assert "deduireRoles" in d["settings"]
