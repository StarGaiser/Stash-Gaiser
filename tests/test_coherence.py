# -*- coding: utf-8 -*-
"""
Cohérence de l'ensemble : ce que le YAML déclare, ce que le code
implémente, ce que les traductions couvrent.

Ces contrôles étaient menés à la main lors des revues. Ils y ont trouvé
quatre défauts réels — un réglage mort, sept réglages invisibles dans
l'interface, et cinq messages restés en français malgré leur traduction.
Automatisés, ils empêchent la rechute.
"""

import ast
import re
from pathlib import Path

import pytest
import yaml

import i18n
import llm

RACINE = Path(__file__).resolve().parent.parent / "gaizer"
SOURCES = sorted(RACINE.glob("*.py"))
CODE = "\n".join(f.read_text(encoding="utf-8") for f in SOURCES)
YAML_PLUGIN = yaml.safe_load(
    (RACINE / "gaizer.yml").read_text(encoding="utf-8"))

MODES_YAML = {(t.get("defaultArgs") or {}).get("mode")
              for t in YAML_PLUGIN.get("tasks") or []}
REGLAGES_YAML = set(YAML_PLUGIN.get("settings") or {})


def _modes_du_code() -> set:
    """Clés du registre TASKS, lues par analyse syntaxique."""
    arbre = ast.parse((RACINE / "gaizer.py").read_text(encoding="utf-8"))
    for n in ast.walk(arbre):
        if (isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "TASKS"
                        for t in n.targets)
                and isinstance(n.value, ast.Dict)):
            return {c.value for c in n.value.keys
                    if isinstance(c, ast.Constant)}
    raise AssertionError("registre TASKS introuvable")


MODES_CODE = _modes_du_code()



def _sans_tables(code: str) -> str:
    """Le panneau sans ses tables de configuration.

    ARGUMENTS, REGLAGES_RAPIDES et ONGLETS_SIMPLES ont la FORME d'une
    entrée de tâche — une clé, puis un ou deux textes — sans en être
    une : la première nomme des champs de saisie, la deuxième des
    réglages, la troisième des groupes. Les lire comme des tâches
    ferait réclamer un libellé scannable pour « 1 pour relire ».
    """
    for marque, fin_marque in (("const LOCAUX", ";"),
                               ("const CHOIX_ARGUMENT", "\n  };"),
                               ("const CHOIX", "\n  };"),
                               ("const ARGUMENTS", "\n  };"),
                               ("const REGLAGES_RAPIDES", "\n  ];"),
                               ("const ONGLETS_SIMPLES", ";")):
        i = code.find(marque)
        if i < 0:
            continue
        fin = code.find(fin_marque, i)
        if fin > i:
            code = code[:i] + code[fin + len(fin_marque):]
    return code


class TestTaches:

    def test_toute_tache_offerte_est_implementee(self):
        assert set() == MODES_YAML - MODES_CODE

    def test_toute_tache_implementee_est_offerte(self):
        assert set() == MODES_CODE - MODES_YAML

    def test_chaque_tache_a_un_nom_traduit(self):
        assert {m for m in MODES_YAML if m not in i18n.EN["taches"]} \
            == set()

    def test_chaque_tache_a_une_description(self):
        sans = [t.get("name") for t in YAML_PLUGIN["tasks"]
                if not (t.get("description") or "").strip()]
        assert sans == []


class TestReglages:

    def _lus_par_le_code(self) -> set:
        lus = set(re.findall(
            r'settings(?:\))?\.get\(\s*["\']([A-Za-z_]+)["\']', CODE))
        # « ai » est le fragment capturé dans settings.get("ai" +
        # usage.capitalize()) : les vraies clés sont construites à
        # l'exécution.
        lus.discard("ai")
        lus |= {"aiBio", "aiSynopsis", "aiBiohot"}
        # Clés désignées par la table des fournisseurs.
        for conf in llm.FOURNISSEURS_DEFAUT.values():
            for champ in ("key_setting", "url_setting"):
                if conf.get(champ):
                    lus.add(conf[champ])
        lus.add("llmApiKey")
        return lus

    def test_aucun_reglage_mort(self):
        """Un réglage déclaré que le code ne lit jamais est pire
        qu'absent : il apparaît dans l'interface, l'utilisateur le
        renseigne, et rien ne change. Deux l'étaient — les
        instructions et la température de la présentation « hot »."""
        lus = set()
        for f in RACINE.glob("*.py"):
            code = f.read_text(encoding="utf-8")
            lus |= set(re.findall(r'settings\.get\(\s*"(\w+)"', code))
            lus |= set(re.findall(r'reglages\.get\(\s*"(\w+)"', code))
            lus |= set(re.findall(r'_reglage\(\s*"(\w+)"', code))
        for f in RACINE.glob("*.js"):
            code = f.read_text(encoding="utf-8")
            lus |= set(re.findall(r'c\.(\w+)', code))
        declares = set(YAML_PLUGIN.get("settings") or {})
        # Certains réglages sont lus par un chemin GÉNÉRIQUE qui
        # construit leur nom : les clés d'API depuis le fournisseur,
        # et « aiBio »/« aiBiohot »/« aiSynopsis » depuis l'usage
        # demandé à `ai_for`. Les chercher littéralement les
        # déclarerait morts à tort.
        construits = {r for r in declares
                      if r.endswith(("ApiKey", "Url"))
                      or (r.startswith("ai")
                          and "ai_for" in "".join(
                              f.read_text(encoding="utf-8")
                              for f in RACINE.glob("noyau.py")))}
        # Les sources d'enrichissement sont lues par une TABLE, non
        # par un appel direct : les compter comme mortes ferait
        # retirer des réglages qui fonctionnent.
        import noyau
        indirects = {r for r, _d in noyau.Context._VOIES.values()}
        morts = declares - lus - construits - indirects
        assert morts == set(), f"réglages sans effet : {sorted(morts)}"

    def test_aucun_reglage_invisible(self):
        """Un réglage lu mais non déclaré n'apparaît pas dans
        l'interface : impossible à renseigner."""
        invisibles = self._lus_par_le_code() - REGLAGES_YAML
        assert invisibles == set(), \
            f"lus sans être déclarés : {sorted(invisibles)}"

    def test_chaque_reglage_a_un_libelle_traduit(self):
        sans = REGLAGES_YAML - set(i18n.EN["reglages"])
        assert sans == set(), f"sans libellé : {sorted(sans)}"

    def test_chaque_reglage_a_un_type_valide(self):
        for nom, champ in YAML_PLUGIN["settings"].items():
            assert champ.get("type") in ("STRING", "BOOLEAN", "NUMBER"), \
                nom

    def test_toute_cle_d_api_est_reconnue_comme_secret(self):
        import noyau
        for nom in REGLAGES_YAML:
            if "ApiKey" in nom:
                assert noyau.est_secret(nom), nom


class TestTraductions:

    def test_toutes_les_langues_couvrent_les_chaines_courtes(self):
        for langue, (presents, total) in i18n.couverture().items():
            assert presents == total, \
                f"{langue} : {presents}/{total} chaînes"

    def test_tout_message_appele_existe(self):
        appeles = set(re.findall(r'\bctx\.t(?:_brut)?\(\s*["\']([a-z_]+)["\']',
                              CODE))
        appeles |= set(re.findall(r'\b_t\(\s*["\']([a-z_]+)["\']', CODE))
        manquants = appeles - set(i18n.EN["msg"]) - set(i18n.EN["boutons"])
        assert manquants == set(), f"absents du catalogue : {manquants}"

    def test_tout_message_du_catalogue_est_utilise(self):
        """Un message traduit mais jamais appelé signale du texte resté
        en dur ailleurs. Ce contrôle a révélé cinq messages affichés en
        français quelle que soit la langue choisie."""
        appeles = set(re.findall(r'\bctx\.t(?:_brut)?\(\s*["\']([a-z_]+)["\']',
                              CODE))
        appeles |= set(re.findall(r'\b_t\(\s*["\']([a-z_]+)["\']', CODE))
        # Ceux-ci sont désignés indirectement, par la table de diagnostic
        # ou lors de l'écriture du pied de biographie.
        indirects = {"pied_bio", "pied_bio_intro", "simulation_evite"}
        indirects |= {c for c in i18n.EN["msg"] if c.startswith("ia_")}
        orphelins = set(i18n.EN["msg"]) - appeles - indirects
        assert orphelins == set(), \
            f"traduits mais jamais appelés : {sorted(orphelins)}"

    def test_les_cles_de_diagnostic_existent(self):
        import ia
        for _mots, _cat, cle in ia._MOTIFS_LLM:
            assert cle in i18n.EN["msg"], cle

    @pytest.mark.parametrize("valeur,attendu", [
        ("fr", "fr"), ("FR", "fr"), ("français", "fr"),
        ("French", "fr"), ("Deutsch", "de"), ("german", "de"),
        ("", "en"), ("klingon", "en"), (None, "en"),
    ])
    def test_langue_reconnue_souplement(self, valeur, attendu):
        assert i18n.code_langue(valeur) == attendu

    def test_repli_sur_l_anglais(self):
        """Une traduction incomplète ne doit jamais empêcher le
        fonctionnement."""
        assert i18n.t("ia_quota", "klingon") == i18n.t("ia_quota", "en")
        assert i18n.tache("rapport_run", "klingon") \
            == i18n.tache("rapport_run", "en")

    def test_cle_inconnue_renvoyee_telle_quelle(self):
        assert i18n.t("cle_qui_n_existe_pas", "fr") \
            == "cle_qui_n_existe_pas"

    def test_parametres_manquants_ne_levent_pas(self):
        assert isinstance(i18n.t("ia_suspendue", "fr"), str)

    def test_les_tags_ont_une_variante_par_langue(self):
        for cle in i18n.EN["tags"]:
            variantes = i18n.tous_les_tags(cle)
            assert variantes, cle
            assert i18n.tag(cle, "fr") in variantes


class TestArchitecture:

    COUCHES = ["noyau", "similarite", "tags", "roles", "scrapers",
               "collecte", "ia",
               "entites", "performers", "scenes", "studios",
               "doublons", "groupes", "taches_diagnostic",
               "taches_menage", "taches_heritage",
               "taches_arbitrage", "taches_maintenance",
               "gaizer"]

    def test_aucune_dependance_ascendante(self):
        """Un module ne dépend que de ceux qui le précèdent. Une
        remontée est un défaut de conception, pas une contrainte à
        contourner par un import différé."""
        rang = {m: i for i, m in enumerate(self.COUCHES)}
        fautes = []
        for module, position in rang.items():
            f = RACINE / f"{module}.py"
            if not f.exists():
                continue
            for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(n, ast.ImportFrom) and n.module in rang:
                    if rang[n.module] >= position:
                        fautes.append(f"{module} → {n.module}")
                elif isinstance(n, ast.Import):
                    for a in n.names:
                        if a.name in rang and rang[a.name] >= position:
                            fautes.append(f"{module} → {a.name}")
        assert fautes == [], f"dépendances ascendantes : {fautes}"

    def test_le_point_d_entree_reste_mince(self):
        lignes = len((RACINE / "gaizer.py").read_text().splitlines())
        assert lignes < 250, \
            f"gaizer.py fait {lignes} lignes : la logique doit vivre " \
            f"dans les modules"

    def test_le_point_d_entree_appelle_main(self):
        """L'oubli de ce bloc laisse le plugin se charger sans rien
        exécuter — panne silencieuse difficile à diagnostiquer."""
        code = (RACINE / "gaizer.py").read_text()
        assert '__main__' in code and "main()" in code

    def test_aucun_appel_reseau_dans_les_modules_purs(self):
        """Les modules de logique pure doivent rester testables sans
        serveur. On examine les IMPORTS, pas le texte : « requests »
        figure dans une traduction (« too many requests ») sans que le
        module y touche."""
        interdits = {"urllib", "requests", "socket", "http",
                     "stashapi"}
        for module in ("similarite", "i18n", "tags", "roles"):
            arbre = ast.parse(
                (RACINE / f"{module}.py").read_text(encoding="utf-8"))
            importes = set()
            for n in ast.walk(arbre):
                if isinstance(n, ast.Import):
                    importes |= {a.name.split(".")[0] for a in n.names}
                elif isinstance(n, ast.ImportFrom) and n.module:
                    importes.add(n.module.split(".")[0])
            fautes = importes & interdits
            assert fautes == set(), f"{module} importe {fautes}"
            code = (RACINE / f"{module}.py").read_text()
            assert "call_GQL" not in code, f"{module} appelle le serveur"


class TestSecurite:

    def test_aucune_requete_construite_par_concatenation(self):
        assert re.search(r'call_GQL\(\s*f["\']', CODE) is None

    def test_aucune_execution_dynamique(self):
        for motif in (r'\beval\s*\(', r'\bexec\s*\(',
                      r'shell\s*=\s*True', r'\bpickle\b'):
            assert re.search(motif, CODE) is None, motif

    def test_yaml_charge_sans_danger(self):
        assert "yaml.load(" not in CODE.replace("yaml.load_all(", "")

    def test_simulation_couvre_toutes_les_mutations(self):
        """Une mutation absente de ce filtre écrit pour de vrai en mode
        « à blanc ». C'est arrivé : groupCreate manquait, et un essai a
        créé vingt groupes."""
        code = (RACINE / "noyau.py").read_text()
        depart = code.find("ecrit = re.compile(")
        filtre = code[depart:code.find(")", depart) + 1]
        for mutation in ("performerUpdate", "performerCreate",
                         "performerDestroy", "sceneUpdate",
                         "studioUpdate", "studioCreate", "studioDestroy",
                         "groupUpdate", "groupCreate", "groupDestroy",
                         "tagUpdate", "tagsMerge", "configurePlugin"):
            assert mutation in filtre, mutation

    def test_le_javascript_n_injecte_pas_de_html(self):
        js = (RACINE / "gaizer.js").read_text()
        for interdit in ("innerHTML", "outerHTML", "insertAdjacentHTML",
                         "eval("):
            assert interdit not in js, interdit

    def test_le_javascript_confirme_avant_destruction(self):
        js = (RACINE / "gaizer.js").read_text()
        assert "confirm(" in js


class TestEconomieDesAppels:
    """Le coût d'IA ne se maîtrise pas par un dispositif unique mais par
    des gardes disséminés. Ils sont discrets — une seule ligne — et
    disparaîtraient sans bruit au premier remaniement."""

    def test_les_textes_ne_sont_produits_que_sur_un_champ_vide(self):
        """Bio factuelle, synopsis et présentation de studio ne sont
        demandés que si le champ est vide. C'est ce garde, et non
        l'empreinte, qui évite l'essentiel des appels — l'empreinte ne
        sert que là où une régénération est délibérée."""
        for fichier, appel in (("performers.py", "synth_bio("),
                               ("scenes.py", "synth_synopsis("),
                               ("studios.py", "_bio_studio(")):
            code = (RACINE / fichier).read_text(encoding="utf-8")
            position = code.find(appel)
            assert position > 0, f"{appel} absent de {fichier}"
            avant = code[max(0, position - 220):position]
            assert 'details' in avant and 'strip()' in avant, \
                f"{fichier} : {appel} n'est plus protégé par un garde " \
                f"sur champ vide — chaque passage repaiera le texte"

    def test_la_bio_hot_verifie_l_empreinte(self):
        code = (RACINE / "ia.py").read_text(encoding="utf-8")
        assert "texte_a_jour(" in code
        position = code.find("texte_a_jour(")
        assert code.find("_appel_llm(", position) > position, \
            "le contrôle doit précéder l'appel, sinon il ne sert à rien"

    def test_chaque_usage_a_son_budget_de_sortie(self):
        import ia
        for usage in ("bio", "synopsis", "studio", "biohot"):
            assert usage in ia.BUDGETS, usage
        code = (RACINE / "ia.py").read_text(encoding="utf-8")
        # Ce qui importe est qu'AUCUN appel ne retombe sur le
        # budget par défaut, non qu'il y en ait un nombre fixe : en
        # ajouter un est légitime, en oublier le budget non.
        assert code.count("budget=BUDGETS[") >= 4, \
            "un appel sans budget explicite retombe sur le défaut"


class TestGreffeInterface:
    """Contrat avec le mécanisme de patch de Stash.

    Stash applique un patch « after » ainsi :

        i = fn.apply(this, args.concat(resultat))

    où `args` sont ceux passés au composant React, soit
    `(props, contexte)`. Le résultat du rendu est donc le DERNIER
    argument. L'avoir lu en deuxième position revenait à récupérer le
    contexte — un objet vide — et à le rendre comme enfant, ce que
    React refuse : la fiche interprète entière disparaissait derrière
    l'erreur minifiée #31.

    Une vérification exécutable du même contrat vit dans
    `tests/verif_patch.js` (nécessite Node)."""

    JS = (RACINE / "gaizer.js").read_text(encoding="utf-8")

    def test_le_resultat_est_lu_en_dernier(self):
        assert "args[args.length - 1]" in self.JS, (
            "le résultat du rendu doit être lu comme dernier argument, "
            "sinon c'est le contexte React qui est rendu")

    def test_pas_de_signature_a_deux_parametres(self):
        """`function (props, result)` est précisément la signature
        fautive."""
        assert not re.search(r"patch\.after\([^,]+,\s*function\s*\("
                             r"\s*\w+\s*,\s*\w+\s*\)", self.JS)

    def test_greffes_sur_composants_verifies_patchables(self):
        """Vérifiés dans les fragments servis par Stash 0.31.1."""
        for nom in ("PerformerDetailsPanel.DetailGroup",
                    "StudioDetailsPanel", "CustomFields"):
            assert nom in self.JS, nom

    def test_chaque_bouton_a_une_explication(self):
        """Un libellé de deux mots ne dit pas ce que fait une action
        destructive : chacune porte une aide au survol."""
        import re as _re
        cles = set(_re.findall(r'B\("(\w+)"', self.JS))
        cles |= set(_re.findall(r'cle: "(\w+)", *\n? *danger', self.JS))
        for cle in cles:
            assert f'aide_{cle}:' in self.JS, \
                f"le bouton « {cle} » n'a pas d'explication"

    def test_page_scene_traitee_a_part(self):
        """La page scène n'est pas patchable sur 0.31.x : le repli DOM
        doit subsister tant que ce n'est pas le cas."""
        assert "querySelector" in self.JS

    def test_horodatage_isole_avant_analyse(self):
        """Le plugin appose « · auto AAAA-MM-JJ » en fin de ligne.
        Cet horodatage tombant après la parenthèse fermante, la
        dernière entrée — et elle seule — échappait à l'analyse et
        s'affichait en vrac dans la colonne du champ."""
        assert "horodatage" in self.JS
        avant = self.JS.find("horodatage = fin[2]")
        boucle = self.JS.find("for (const l of texte.split")
        assert 0 < avant < boucle, \
            "l'horodatage doit être retiré AVANT la boucle d'analyse"

    def test_absence_de_couleurs_en_dur(self):
        """Des hexadécimaux figés rendent le panneau illisible sur un
        thème clair."""
        couleurs = re.findall(r"#[0-9a-fA-F]{6}\b", self.JS)
        assert couleurs == [], f"couleurs en dur : {set(couleurs)}"

    def test_degradation_si_api_absente(self):
        """Sur un Stash antérieur à 0.25, le panneau doit s'abstenir,
        pas casser la page."""
        assert "if (!API || !API.React)" in self.JS


class TestPageCommande:
    """La page de commande présente les tâches par intention.

    Trente-huit tâches dans la liste plate de Stash, mêlées à celles
    des autres plugins : on n'y trouvait pas ce qu'on cherchait. La
    page les regroupe par ce qu'on veut obtenir, montre la file
    d'attente — qui explique pourquoi une tâche paraît ne rien faire —
    et propose une simulation avant chaque action destructive.

    Une vérification exécutable vit dans `tests/verif_page.js`."""

    PAGE = _sans_tables(
        (RACINE / "gaizer_page.js").read_text(encoding="utf-8"))

    def test_page_declaree_dans_le_yaml(self):
        js = ((YAML_PLUGIN.get("ui") or {}).get("javascript") or [])
        assert "gaizer_page.js" in js

    def test_tous_les_modes_cites_existent(self):
        """Un bouton pointant vers un mode inexistant échouerait au
        clic, sans rien dire."""
        cites = set(re.findall(r'\["(\w+)", "', self.PAGE))
        assert cites, "aucun mode trouvé dans la page"
        # « simple » nomme l'ONGLET d'accueil, non une tâche : il n'y
        # figure aucun mode, seulement le bouton d'enrichissement.
        cites -= {"simple"}
        assert cites <= MODES_CODE, \
            f"modes inconnus du registre : {sorted(cites - MODES_CODE)}"

    def test_les_actions_destructives_sont_signalees(self):
        """Toute tâche marquée destructive doit proposer une
        simulation et demander confirmation."""
        assert "destructif" in self.PAGE
        assert "tr(\"simuler\")" in self.PAGE
        assert "confirm(tr(\"confirmer\")" in self.PAGE

    def test_aucune_tache_en_double(self):
        """Une même tâche sous deux libellés différents laissait
        croire à deux actions distinctes."""
        modes = re.findall(r'\["(\w+)", "', self.PAGE)
        doublons = {m for m in modes if modes.count(m) > 1}
        assert doublons == set(), f"tâches en double : {doublons}"

    def test_cinq_groupes_declares(self):
        """Le groupe « Réparation » n'apparaissait pas à l'écran : sur
        deux colonnes, il tombait sous la ligne de flottaison."""
        for g in ("g_demarrage", "g_courant", "g_menage",
                  "g_diagnostic", "g_reparation"):
            assert f'["{g}"' in self.PAGE, g

    def test_la_file_reste_lisible(self):
        """Afficher la liste brute des états produisait un mur de
        « READY » dès qu'une poignée de tâches s'accumulaient."""
        assert "file.map((j) => j.status).join" not in self.PAGE
        assert "en_attente_n" in self.PAGE

    def test_la_file_peut_etre_videe(self):
        assert "stopAllJobs" in self.PAGE

    def test_la_file_est_affichee(self):
        assert "jobQueue" in self.PAGE

    def test_degradation_si_api_absente(self):
        assert "if (!API || !API.React || !API.patch) return;" in self.PAGE

    def test_aucune_navigation_requise(self):
        """Une route enregistrée par un plugin n'est pas garantie
        d'exister pour le routeur : le JavaScript des plugins est
        chargé APRÈS le montage des routes, et la page se soldait par
        un 404. Le panneau s'ouvre sur place, ce qui supprime la
        dépendance."""
        assert "modal-dialog" in self.PAGE
        # L'enregistrement de route subsiste, mais protégé et
        # facultatif : il ne doit pas conditionner l'accès.
        assert "if (API.register && API.register.route)" in self.PAGE

    def test_le_panneau_se_ferme(self):
        """Un panneau qu'on ne peut fermer qu'en visant une croix est
        pénible : touche d'échappement et clic à côté."""
        assert "Escape" in self.PAGE
        assert "ev.target === ev.currentTarget" in self.PAGE


class TestScrapersManquants:
    """La détection se greffe à la fin de l'enrichissement des scènes
    et des studios. C'est le seul moment où la liste des studios est
    complète : ce sont ces tâches qui créent ceux qui manquaient."""

    def test_declenchement_greffe_aux_deux_taches(self):
        for fichier in ("scenes.py", "studios.py"):
            code = (RACINE / fichier).read_text(encoding="utf-8")
            assert "scrapers.doit_verifier(ctx)" in code, fichier

    def test_la_cadence_est_respectee(self):
        """Sans limite, enrichir une fiche unique interrogerait le
        catalogue distant à chaque clic. La condition et l'appel
        tiennent désormais sur une même expression."""
        for fichier in ("scenes.py", "studios.py"):
            code = (RACINE / fichier).read_text(encoding="utf-8")
            assert "scrapers.doit_verifier(ctx) else []" in code, \
                f"{fichier} : la détection doit être conditionnée"

    def test_la_greffe_protege_l_enrichissement(self):
        """La détection est un SUPPLÉMENT : son échec ne doit pas faire
        tomber un enrichissement qui a réussi. Se reposer sur le fait
        que `detecter` capture ses erreurs serait une hypothèse, pas
        une garantie — et le test l'a démentie."""
        for fichier in ("scenes.py", "studios.py"):
            code = (RACINE / fichier).read_text(encoding="utf-8")
            i = code.find("scrapers.doit_verifier")
            avant = code[max(0, i - 400):i]
            assert "try:" in avant, \
                f"{fichier} : la greffe doit être protégée"

    def test_rien_ne_s_installe_au_declenchement(self):
        """Le déclenchement automatique DÉTECTE ; il n'installe pas.
        Un scraper est du code tiers qui s'exécutera sur la machine de
        l'utilisateur."""
        for fichier in ("scenes.py", "studios.py"):
            code = (RACINE / fichier).read_text(encoding="utf-8")
            assert "_installer" not in code, fichier
            assert "proposer_scrapers" not in code, fichier
