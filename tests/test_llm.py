# -*- coding: utf-8 -*-
"""
Fournisseurs de modèles de langage : table, authentification, formats.

Aucun appel réseau : on vérifie ce qui est CONSTRUIT, pas ce qui est
envoyé.
"""

import json

import llm


class TestTableDesFournisseurs:

    def test_fournisseurs_courants_presents(self):
        table = llm.charger()
        for nom in ("openai", "mistral", "anthropic", "openrouter",
                    "groq", "deepseek", "ollama", "lmstudio"):
            assert nom in table, nom

    def test_chaque_entree_est_complete(self):
        for nom, conf in llm.charger().items():
            assert conf.get("url", "").startswith("http"), nom
            assert conf.get("model"), nom
            assert conf.get("auth") in ("bearer", "x-api-key", "query",
                                        "none"), nom
            assert conf.get("format") in ("openai", "anthropic"), nom

    def test_services_locaux_sans_cle(self):
        table = llm.charger()
        for nom in ("ollama", "lmstudio", "llamacpp", "vllm"):
            assert not llm.besoin_de_cle(table[nom]), nom

    def test_services_distants_exigent_une_cle(self):
        table = llm.charger()
        for nom in ("openai", "mistral", "openrouter", "groq"):
            assert llm.besoin_de_cle(table[nom]), nom

    def test_aucune_cle_dans_la_table(self):
        """Les identifiants vivent dans les réglages de Stash, jamais
        dans le code ni dans un fichier."""
        brut = json.dumps(llm.charger())
        for suspect in ("sk-", "Bearer ", "api_key"):
            assert suspect not in brut, suspect

    def test_fichier_perso_fusionne_entree_par_entree(self, tmp_path):
        (tmp_path / "llm_providers.yml").write_text(
            "mistral:\n  model: mistral-small-latest\n"
            "maison:\n  url: https://api.maison.test/v1/chat/completions\n"
            "  model: local\n  auth: none\n", encoding="utf-8")
        table = llm.charger(tmp_path)
        assert table["mistral"]["model"] == "mistral-small-latest"
        assert table["mistral"]["url"].startswith("https://api.mistral")
        assert "maison" in table

    def test_fichier_illisible_ne_casse_rien(self, tmp_path):
        (tmp_path / "llm_providers.yml").write_text(
            "ceci: [n'est pas: du yaml", encoding="utf-8")
        assert "mistral" in llm.charger(tmp_path)

    def test_fichier_absent(self, tmp_path):
        assert len(llm.charger(tmp_path)) == len(llm.FOURNISSEURS_DEFAUT)

    def test_gabarit_cree_une_seule_fois(self, tmp_path):
        assert llm.creer_gabarit(tmp_path) is True
        assert llm.creer_gabarit(tmp_path) is False
        contenu = (tmp_path / "llm_providers.yml").read_text()
        assert "JAMAIS de clé" in contenu


class TestChoixDeLaCle:

    def test_reglage_dedie_prioritaire(self):
        conf = {"key_setting": "mistralApiKey"}
        cle = llm.cle_pour(conf, {"mistralApiKey": "dediee",
                                  "llmApiKey": "generique"})
        assert cle == "dediee"

    def test_repli_sur_la_cle_generique(self):
        conf = {"key_setting": "openrouterApiKey"}
        assert llm.cle_pour(conf, {"llmApiKey": "generique"}) \
            == "generique"

    def test_reglage_dedie_vide_bascule_sur_generique(self):
        conf = {"key_setting": "openrouterApiKey"}
        assert llm.cle_pour(conf, {"openrouterApiKey": "  ",
                                   "llmApiKey": "generique"}) \
            == "generique"

    def test_aucune_cle(self):
        assert llm.cle_pour({"key_setting": "x"}, {}) == ""


class TestAdresseDuService:

    def test_adresse_par_defaut(self):
        conf = {"url": "http://localhost:11434/v1/chat/completions"}
        assert llm.url_pour(conf, {}) == conf["url"]

    def test_reglage_deplace_le_service(self):
        conf = {"url": "http://localhost:11434/v1/chat/completions",
                "url_setting": "ollamaUrl"}
        u = llm.url_pour(conf, {"ollamaUrl": "http://192.168.1.40:11434"})
        assert u == "http://192.168.1.40:11434/v1/chat/completions", \
            "le chemin doit être complété"

    def test_adresse_complete_respectee(self):
        conf = {"url": "http://x/v1/chat/completions",
                "url_setting": "ollamaUrl"}
        voulue = "http://y:8080/v1/chat/completions"
        assert llm.url_pour(conf, {"ollamaUrl": voulue}) == voulue


class TestConstructionDeLaRequete:

    def _corps(self, req):
        return json.loads(req.data.decode())

    def test_authentification_bearer(self):
        req = llm.construire_requete(
            {"auth": "bearer", "format": "openai"},
            "https://x/v1", "secret", "m", "prompt", 0.2)
        entetes = {k.lower(): v for k, v in req.headers.items()}
        assert entetes["authorization"] == "Bearer secret"

    def test_authentification_par_entete(self):
        req = llm.construire_requete(
            {"auth": "x-api-key", "format": "anthropic"},
            "https://x/v1", "secret", "m", "prompt", 0.2)
        entetes = {k.lower(): v for k, v in req.headers.items()}
        assert entetes["x-api-key"] == "secret"
        assert "authorization" not in entetes

    def test_service_local_sans_authentification(self):
        req = llm.construire_requete(
            {"auth": "none", "format": "openai"},
            "http://localhost:11434/v1", "", "m", "prompt", 0.2)
        entetes = {k.lower(): v for k, v in req.headers.items()}
        assert "authorization" not in entetes

    def test_entetes_additionnels_transmis(self):
        req = llm.construire_requete(
            {"auth": "bearer", "headers": {"X-Title": "Gaizer"}},
            "https://x/v1", "k", "m", "prompt", 0.2)
        entetes = {k.lower(): v for k, v in req.headers.items()}
        assert entetes["x-title"] == "Gaizer"

    def test_parametres_du_corps(self):
        corps = self._corps(llm.construire_requete(
            {"auth": "bearer"}, "https://x", "k", "mon-modele",
            "ma question", 0.7, max_tokens=120))
        assert corps["model"] == "mon-modele"
        assert corps["temperature"] == 0.7
        assert corps["max_tokens"] == 120
        assert corps["messages"][0]["content"] == "ma question"

    def test_cle_en_parametre_d_url(self):
        req = llm.construire_requete(
            {"auth": "query"}, "https://x/v1?alt=json", "secret", "m",
            "p", 0.2)
        assert "key=secret" in req.full_url


class TestLectureDeLaReponse:

    def test_format_openai(self):
        brut = json.dumps({"choices": [
            {"message": {"content": "  une réponse  "}}]}).encode()
        assert llm.lire_reponse({"format": "openai"}, brut) \
            == "une réponse"

    def test_format_anthropic(self):
        brut = json.dumps({"content": [
            {"type": "text", "text": "une réponse"}]}).encode()
        assert llm.lire_reponse({"format": "anthropic"}, brut) \
            == "une réponse"

    def test_anthropic_plusieurs_blocs(self):
        brut = json.dumps({"content": [
            {"type": "text", "text": "début "},
            {"type": "text", "text": "et suite"}]}).encode()
        assert llm.lire_reponse({"format": "anthropic"}, brut) \
            == "début et suite"

    def test_reponse_vide(self):
        for brut, fmt in [(b'{"choices": []}', "openai"),
                          (b'{"content": []}', "anthropic"),
                          (b'{}', "openai")]:
            assert llm.lire_reponse({"format": fmt}, brut) == ""

    def test_format_absent_traite_comme_openai(self):
        brut = json.dumps({"choices": [
            {"message": {"content": "x"}}]}).encode()
        assert llm.lire_reponse({}, brut) == "x"


class TestListeLisible:

    def test_distants_et_locaux_distingues(self):
        texte = llm.liste_lisible(llm.charger())
        assert "openrouter" in texte and "ollama" in texte
        assert "en ligne" in texte and "local" in texte
