# -*- coding: utf-8 -*-
"""
Ce qu'un prompt doit contenir.

Écrit AVANT la réécriture.

Un prompt qui n'énonce qu'une consigne obtient un texte quelconque. Le
prompt actuel dit quoi écrire et pose une règle absolue, mais tait le
reste : à quoi le texte sert, pourquoi la règle existe, ce qui compte
comme un bon résultat, et à quoi ressemble une réponse acceptable.

Chaque manque a un coût mesurable.

**Sans OBJECTIF**, le modèle invente le sien — un texte publicitaire
là où il faut une fiche de consultation.

**Sans RAISON**, une règle est une contrainte qu'on contourne : « ne
déduis rien » se plie facilement quand rien ne dit ce que la déduction
casse. Expliquer qu'il s'agit d'une personne réelle et qu'une
supposition devient une affirmation fausse tient mieux qu'un
impératif.

**Sans FORMAT**, on obtient des titres, des astérisques, des listes à
puces — que Stash affiche tels quels.

**Sans CRITÈRE DE RÉUSSITE**, le modèle ne sait pas arbitrer entre
deux textes possibles, et prend le plus long.

**Sans EXEMPLE**, l'attente reste abstraite : montrer vaut mieux que
décrire, surtout pour un ton.
"""

import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))


@pytest.fixture(scope="module")
def prompt():
    import i18n
    return i18n.t("prompt_biohot", "fr")


@pytest.fixture(scope="module")
def consignes():
    import i18n
    return i18n.t("prompt_biohot_consignes", "fr")


class TestStructureDuPrompt:
    """Objectif, raison, formalisme, résultat attendu : les quatre
    manquants."""

    def test_l_objectif_est_enonce(self, prompt):
        """À quoi le texte sert. Sans cela, le modèle invente sa
        propre finalité — souvent publicitaire."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("objectif", "sert à", "permet", "pour que",
                    "afin")), prompt[:200]

    def test_le_role_est_pose(self, prompt):
        """Dire au modèle ce qu'il est cadre tout le reste."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("tu es", "tu rédiges", "ton rôle")), prompt[:200]

    def test_les_regles_disent_leur_raison(self, prompt):
        """« Ne déduis rien » se plie facilement quand rien ne dit ce
        que la déduction casse."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("parce que", "car ", "sinon", "personne réelle",
                    "ferait")), prompt[:400]

    def test_le_resultat_attendu_est_decrit(self, prompt):
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("réussi", "bon texte", "attendu", "critère")), \
            prompt[:400]

    def test_un_exemple_est_donné(self, prompt):
        """Montrer vaut mieux que décrire, surtout pour un ton."""
        bas = prompt.lower()
        assert "exemple" in bas, prompt[:400]

    def test_le_format_est_precise(self, prompt, consignes):
        ensemble = (prompt + consignes).lower()
        assert "phrase" in ensemble
        assert any(m in ensemble for m in
                   ("ni titre", "sans titre", "aucun balisage",
                    "pas de balisage"))


class TestContraintesMesurables:
    """Une contrainte qu'on ne peut pas vérifier n'en est pas une."""

    def test_la_longueur_est_donnee_en_une_seule_unite(self, prompt):
        """« 3 à 4 phrases (450 caractères max) » donne deux mesures
        qui peuvent se contredire : le modèle choisit celle qui
        l'arrange."""
        a_phrases = bool(re.search(r"\d+\s*(à|-)\s*\d+\s*phrases",
                                   prompt))
        a_signes = bool(re.search(r"\d{3,}\s*(caractères|signes)",
                                  prompt))
        # Deux mesures se contredisent quand elles sont
        # INDÉPENDANTES : « 3 à 4 phrases (450 signes max) » laisse
        # choisir. Elles s'accordent quand l'une illustre l'autre :
        # « 400 signes, soit trois ou quatre phrases denses ».
        if a_phrases and a_signes:
            assert "soit" in prompt, \
                "deux unités indépendantes peuvent se contredire"

    def test_la_langue_est_un_parametre(self, prompt):
        assert "{langue}" in prompt

    def test_le_nom_est_un_parametre(self, prompt):
        assert "{nom}" in prompt

    def test_le_prompt_reste_lisible(self, prompt):
        """Un prompt de trois mille signes coûte à chaque appel et
        noie ce qui compte."""
        # Le plafond a été relevé une fois : le prompt porte
        # désormais un exemple, une exception documentée et une règle
        # de conduite, chacun ajouté pour corriger un défaut observé
        # sur des textes réels. Il coûte à chaque appel, mais un
        # prompt maigre coûtait des textes faux.
        assert 400 <= len(prompt) <= 2400, len(prompt)


class TestGardeFous:
    """Ce qui protégeait déjà doit survivre à la réécriture : ces
    règles viennent de textes réellement produits."""

    def test_l_invention_reste_interdite(self, prompt):
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("n'invente", "ne déduis", "sans inventer",
                    "uniquement")), prompt[:400]

    def test_le_silence_est_prefere_a_l_invention(self, prompt):
        """« Si la matière est maigre, fais court » : c'est la règle
        qui a le plus évité de textes faux."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("plutôt que d'inventer", "fais court", "moins",
                    "abrège", "tais")), prompt[:600]

    def test_le_texte_seul_est_demande(self, prompt):
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("uniquement le texte", "réponds uniquement",
                    "rien d'autre", "sans préambule")), prompt[-400:]


class TestCeQueLesEssaisOntMontre:
    """Deux défauts constatés sur des textes réellement produits.

    **Le nom ne figure pas dans le texte du second essai** alors qu'il
    ouvre le premier. Un texte de fiche n'a pas à répéter le nom — il
    est affiché juste au-dessus — mais l'inconstance montre que la
    règle n'est pas dite.

    **La biographie hors porno déborde.** « Un mariage avec Gia
    Darling » est dans les données, donc autorisé par la règle
    absolue, mais n'apprend rien sur ce que l'acteur apporte à la
    collection. La règle disait quoi ne PAS inventer ; elle ne disait
    pas quoi ÉCARTER parmi ce qui est vrai."""

    def test_le_nom_n_est_pas_a_repeter(self, prompt, consignes):
        ensemble = (prompt + consignes).lower()
        assert "ne répète pas" in ensemble or "n'écris pas le nom" \
            in ensemble or "déjà affiché" in ensemble, prompt[-500:]

    def test_le_tri_de_la_matiere_est_dit(self, prompt):
        """Tout ce qui est vrai n'a pas sa place : le prompt doit
        dire ce qui sert le lecteur."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("écarte", "laisse de côté", "n'a pas sa place",
                    "ne retiens que")), prompt[:900]

    def test_la_vie_privee_est_ecartee(self, prompt):
        """Mariage, orientation déclarée, parcours hors porno :
        exacts, mais hors sujet — et sur une personne réelle, les
        étaler dans une fiche de consultation n'a aucune utilité."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("vie privée", "hors porno", "hors du travail",
                    "vie personnelle")), prompt[:1200]


class TestTonEtEnvie:
    """Le prompt obtenait des textes JUSTES et plats : « Physique de
    rugbyman, torse large. Quatre scènes ici. » C'est un inventaire,
    pas une présentation — et ça ne donne envie de rien.

    Le manque était dans le ton. Dire « direct et cru » ne suffit
    pas : cru décrit un vocabulaire, pas une intention. Il faut dire
    QUI écrit et POUR QUOI FAIRE — un chroniqueur du milieu, qui
    connaît les acteurs et sait ce qui rend une scène désirable.

    La justesse reste la contrainte : sulfureux ne veut pas dire
    inventé."""

    def test_le_role_est_celui_d_un_connaisseur(self, prompt):
        """« Tu rédiges une fiche » n'appelle rien. « Tu es
        chroniqueur du milieu » appelle un ton."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("chroniqueur", "connaisseur", "critique",
                    "journaliste")), prompt[:300]

    def test_l_effet_recherche_est_dit(self, prompt):
        """Un texte de présentation doit donner envie de voir la
        scène : c'est son usage, et le taire produit un inventaire."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("envie", "désir", "attise", "excite")), \
            prompt[:900]

    def test_l_inventaire_est_proscrit(self, prompt):
        """Nommer le défaut vaut mieux que décrire l'idéal : le
        modèle reconnaît « liste de caractéristiques »."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("inventaire", "liste", "énumération",
                    "catalogue")), prompt[:1400]

    def test_la_justesse_reste_la_contrainte(self, prompt):
        """Sulfureux ne veut pas dire inventé : sans ce rappel, le ton
        emporte la règle."""
        bas = prompt.lower()
        # La limite peut se dire de plusieurs façons : ce qui
        # compte est qu'elle borne le TON, pas qu'elle emploie une
        # formule précise.
        assert any(m in bas for m in
                   ("sans inventer", "inventé", "inventés",
                    "mensonge", "sans image")), prompt[:1600]


class TestContrasteHeteroGay:
    """Un hétéro dans une scène gay — ou l'inverse — est un ressort du
    genre, pas un détail de vie privée. Le taire par excès de pudeur
    jetait une information qui compte pour le lecteur.

    La limite tient à la SOURCE : ce qui est déclaré publiquement par
    l'acteur ou porté par le studio comme argument est du travail ;
    une orientation supposée, non."""

    def test_le_contraste_est_mentionnable(self):
        """Il vient du PROFIL de collection : « un hétéro qui tourne
        gay » n'excite que dans une collection gay, et s'inverse
        ailleurs."""
        import i18n
        profils = i18n.t_msg("profils_biohot", "fr") or {}
        gay = profils.get("gay") or ("", "", "")
        assert "hétéro" in gay[2].lower(), gay[2][:120]

    def test_seul_ce_qui_est_declare_compte(self, prompt):
        import i18n
        profils = i18n.t_msg("profils_biohot", "fr") or {}
        prompt = (profils.get("gay") or ("", "", ""))[2]
        """Supposer l'orientation de quelqu'un est exactement ce que
        la règle absolue interdit."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("déclare", "déclaré", "revendiqu", "annonce",
                    "affiche")), prompt[:1600]


class TestLaRegleTientMalgreLeTon:
    """Le ton a emporté la règle. Trois inventions constatées sur deux
    textes : « toutes tournées après son divorce », « un mec qui a
    porté des charges lourdes », et une taille de sexe fausse.

    Le mécanisme est identifiable : une image demande un détail
    concret, le modèle en produit un s'il n'en trouve pas. Interdire
    l'invention ne suffit donc pas — il faut dire QUOI FAIRE quand
    l'image manque de matière, et placer cette consigne À CÔTÉ de
    celle qui réclame des images.

    La règle doit aussi être la DERNIÈRE chose lue : ce qui ferme le
    prompt pèse plus que ce qui l'ouvre."""

    def test_la_conduite_a_tenir_est_dite(self, prompt):
        """« N'invente pas » ne dit pas quoi faire à la place."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("écris sans image", "renonce à l'image",
                    "reste factuel", "sans image")), prompt[:1600]

    def test_la_regle_ferme_le_prompt(self, prompt):
        """Ce qui est lu en dernier pèse plus. La règle absolue ne
        peut pas se trouver au milieu, entre le ton et l'exemple."""
        queue = prompt[-500:].lower()
        assert any(m in queue for m in
                   ("inventé", "n'invente", "vérifiable",
                    "dans les données")), prompt[-500:]

    def test_les_chiffres_sont_proteges(self, prompt):
        """Une taille de sexe fausse est le pire cas : elle a l'air
        d'un fait, personne ne la vérifie, et elle décrit une
        personne réelle."""
        bas = prompt.lower()
        assert any(m in bas for m in
                   ("chiffre", "taille", "mesure", "nombre")), \
            prompt[:1800]


class TestLongueurTenue:
    """Le prompt demande quatre cents signes ; le modèle en produit
    mille. Une borne qu'aucun mécanisme ne fait respecter n'en est
    pas une : elle relève de la bonne volonté du modèle, qui préfère
    toujours en dire plus.

    Le budget de sortie est le seul levier réel — il coupe. Mais
    couper au milieu d'une phrase est pire que produire un texte
    plat : il faut viser une longueur telle que le modèle finisse
    naturellement avant."""

    def test_le_budget_correspond_a_la_borne_annoncee(self):
        """Un budget de quatre cents jetons autorise mille deux cents
        signes, soit trois fois ce qui est demandé : le prompt dit une
        chose et le mécanisme en permet une autre."""
        import ia
        # Trois signes par jeton en français, avec marge.
        signes_permis = ia.BUDGETS["biohot"] * 3
        assert signes_permis <= 700, (
            f"{signes_permis} signes permis pour une borne annoncée "
            f"à 400 : le modèle remplira l'espace offert")

    def test_la_borne_est_repetee_a_la_fin(self, prompt):
        """Ce qui ferme le prompt pèse le plus. Une borne énoncée au
        milieu se dilue."""
        queue = prompt[-400:]
        assert any(m in queue for m in
                   ("400", "quatre cents", "court", "bref")), queue
