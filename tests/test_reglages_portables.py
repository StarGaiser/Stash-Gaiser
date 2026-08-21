# -*- coding: utf-8 -*-
"""
Emporter ses réglages.

Écrit AVANT le code.

Stash n'offre rien pour cela : `exportObjects` traite les scènes, les
interprètes et les studios ; `backupDatabase` copie la base entière.
Aucun des deux ne touche aux réglages d'un plugin, qui vivent dans une
table à part.

Or ils sont nombreux — quarante-six — et plusieurs demandent du
tâtonnement : le prompt, la température, les seuils, le choix du
modèle. Les reperdre en changeant de machine, ou après qu'un outil
tiers a écrasé la table, coûte des heures.

**La copie automatique existait déjà**, mais elle est invisible : elle
vit dans un fichier que l'utilisateur ne voit pas et ne peut pas
emporter.

**Les secrets ne sortent jamais.** Une clé d'API dans un fichier qu'on
transporte, qu'on colle dans un ticket ou qu'on met sur un dépôt est
un incident. Seule leur PRÉSENCE est notée, pour que l'import puisse
dire ce qu'il reste à ressaisir.

**L'import ne détruit pas.** Il complète, et dit ce qu'il a changé :
écraser un réglage courant par un ancien sans le dire ferait perdre
un ajustement qu'on croyait fait.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "gaizer"))

import reglages  # noqa: E402
from faux import FauxStash, faux_contexte  # noqa: E402


class TestExport:
    """Ce qui sort doit pouvoir être relu, et ne rien contenir de
    secret."""

    def test_les_reglages_sortent(self):
        ctx = faux_contexte({"applyMode": "seuil", "batchSize": "25"},
                            FauxStash())
        texte = reglages.exporter(ctx)
        d = json.loads(texte)
        assert d["reglages"]["applyMode"] == "seuil"

    def test_le_format_se_relit(self):
        """Un export qu'on ne peut pas réimporter n'est qu'un
        journal."""
        ctx = faux_contexte({"applyMode": "auto"}, FauxStash())
        d = json.loads(reglages.exporter(ctx))
        assert "version" in d and "reglages" in d

    def test_aucune_cle_d_api_ne_sort(self):
        """Une clé dans un fichier qu'on transporte, qu'on colle dans
        un ticket ou qu'on pousse sur un dépôt est un incident."""
        ctx = faux_contexte({
            "llmApiKey": "sk-secret", "stashboxApiKey": "abc",
            "applyMode": "auto"}, FauxStash())
        texte = reglages.exporter(ctx)
        assert "sk-secret" not in texte
        assert "abc" not in texte
        assert "auto" in texte

    def test_la_presence_des_secrets_est_notee(self):
        """Sans cela, l'import ne pourrait pas dire ce qu'il reste à
        ressaisir — et l'utilisateur découvrirait le manque au
        premier appel qui échoue."""
        ctx = faux_contexte({"llmApiKey": "sk-secret"}, FauxStash())
        d = json.loads(reglages.exporter(ctx))
        assert "llmApiKey" in (d.get("secrets_a_ressaisir") or [])

    def test_les_valeurs_vides_ne_sortent_pas(self):
        """Elles alourdissent le fichier sans rien dire : un réglage
        absent et un réglage vide se valent."""
        ctx = faux_contexte({"applyMode": "auto", "batchSize": "",
                             "tagProfile": None}, FauxStash())
        d = json.loads(reglages.exporter(ctx))
        assert "batchSize" not in d["reglages"]
        assert "tagProfile" not in d["reglages"]

    def test_une_configuration_vide_ne_leve_pas(self):
        d = json.loads(reglages.exporter(faux_contexte({},
                                                       FauxStash())))
        assert d["reglages"] == {}


class TestImport:
    """Il complète, il ne détruit pas."""

    def test_un_reglage_absent_est_pose(self):
        st = FauxStash()
        ctx = faux_contexte({}, st)
        texte = json.dumps({"version": 1,
                            "reglages": {"applyMode": "seuil"}})
        poses, ecrases, _ = reglages.importer(ctx, texte)
        assert "applyMode" in poses

    def test_un_reglage_identique_n_est_pas_compte(self):
        """Le rapport doit dire ce qui a CHANGÉ : compter l'identique
        noierait le vrai."""
        ctx = faux_contexte({"applyMode": "seuil"}, FauxStash())
        texte = json.dumps({"version": 1,
                            "reglages": {"applyMode": "seuil"}})
        poses, ecrases, _ = reglages.importer(ctx, texte)
        assert not poses and not ecrases

    def test_un_reglage_different_est_signale(self):
        """Écraser un réglage courant par un ancien sans le dire
        ferait perdre un ajustement qu'on croyait fait."""
        ctx = faux_contexte({"applyMode": "auto"}, FauxStash())
        texte = json.dumps({"version": 1,
                            "reglages": {"applyMode": "manual"}})
        _, ecrases, _ = reglages.importer(ctx, texte)
        assert any("applyMode" in str(x) for x in ecrases)

    def test_les_secrets_manquants_sont_dits(self):
        ctx = faux_contexte({}, FauxStash())
        texte = json.dumps({"version": 1, "reglages": {},
                            "secrets_a_ressaisir": ["llmApiKey"]})
        _, _, secrets = reglages.importer(ctx, texte)
        assert "llmApiKey" in secrets

    def test_un_secret_deja_present_n_est_pas_reclame(self):
        ctx = faux_contexte({"llmApiKey": "déjà là"}, FauxStash())
        texte = json.dumps({"version": 1, "reglages": {},
                            "secrets_a_ressaisir": ["llmApiKey"]})
        _, _, secrets = reglages.importer(ctx, texte)
        assert "llmApiKey" not in secrets

    def test_la_table_est_relue_avant_d_ecrire(self):
        """`configurePlugin` REMPLACE la table : écrire sans relire
        effacerait tout le reste, y compris les clés d'API."""
        # Vérifié par le COMPORTEMENT, non par la lecture du code :
        # ce qui compte est qu'un réglage absent du fichier survive.
        st = FauxStash(reglages_plugin={"llmApiKey": "sk-precieuse",
                                        "batchSize": "50"})
        ctx = faux_contexte({"batchSize": "50"}, st)
        texte = json.dumps({"version": 1,
                            "reglages": {"applyMode": "seuil"}})
        reglages.importer(ctx, texte)
        assert st.reglages_plugin.get("llmApiKey") == "sk-precieuse"
        assert st.reglages_plugin.get("applyMode") == "seuil"


class TestEntreesAbsurdes:
    """Un fichier collé à la main peut être n'importe quoi."""

    @pytest.mark.parametrize("brut", [
        "", "   ", "pas du json", "{}", "[]", "null",
        '{"version": 1}', '{"reglages": "pas un objet"}',
        '{"version": 99, "reglages": {}}'])
    def test_rien_ne_leve(self, brut):
        ctx = faux_contexte({}, FauxStash())
        r = reglages.importer(ctx, brut)
        assert isinstance(r, tuple) and len(r) == 3

    def test_une_valeur_absurde_est_ignoree(self):
        """Un réglage inconnu vient d'une version future ou d'une
        faute de frappe : le poser polluerait la table."""
        ctx = faux_contexte({}, FauxStash())
        texte = json.dumps({"version": 1, "reglages": {
            "reglageQuiNexistePas": "x", "applyMode": "auto"}})
        poses, _, _ = reglages.importer(ctx, texte)
        assert "reglageQuiNexistePas" not in poses

    def test_un_secret_dans_le_fichier_est_refuse(self):
        """Un fichier d'une version antérieure, ou trafiqué, pourrait
        en porter un : l'accepter le ferait entrer sans contrôle."""
        ctx = faux_contexte({}, FauxStash())
        texte = json.dumps({"version": 1, "reglages": {
            "llmApiKey": "sk-volée", "applyMode": "auto"}})
        poses, _, _ = reglages.importer(ctx, texte)
        assert "llmApiKey" not in poses


class TestLesDeuxTaches:
    """Le journal est le seul canal par lequel un plugin Stash rend du
    texte : écrire un fichier sur le serveur ne servirait à rien, il
    est souvent dans un conteneur auquel l'utilisateur n'a pas
    accès."""

    def _journal(self, ctx, quoi, monkeypatch):
        vues = []
        for niveau in ("info", "warning"):
            monkeypatch.setattr(reglages.log, niveau,
                                lambda m, *a, **k: vues.append(str(m)))
        quoi(ctx)
        return "\n".join(vues)

    def test_l_export_ecrit_dans_le_journal(self, monkeypatch):
        ctx = faux_contexte({"applyMode": "seuil"}, FauxStash())
        rendu = self._journal(ctx, reglages.exporter_reglages,
                              monkeypatch)
        assert "applyMode" in rendu and "seuil" in rendu

    def test_l_export_dit_ce_qui_reste_a_ressaisir(self,
                                                   monkeypatch):
        ctx = faux_contexte({"llmApiKey": "sk-x"}, FauxStash())
        rendu = self._journal(ctx, reglages.exporter_reglages,
                              monkeypatch)
        assert "sk-x" not in rendu
        assert "llmApiKey" in rendu

    def test_l_import_sans_fichier_le_dit(self, monkeypatch):
        """Une tâche qui ne fait rien sans le dire laisse croire à
        une panne."""
        ctx = faux_contexte({}, FauxStash())
        ctx.args = {}
        rendu = self._journal(ctx, reglages.importer_reglages,
                              monkeypatch)
        assert "fichier" in rendu.lower()

    def test_l_import_rapporte_ce_qu_il_pose(self, monkeypatch):
        ctx = faux_contexte({}, FauxStash())
        ctx.args = {"fichier": json.dumps({
            "version": 1, "reglages": {"applyMode": "seuil"}})}
        rendu = self._journal(ctx, reglages.importer_reglages,
                              monkeypatch)
        assert "applyMode" in rendu

    def test_l_import_rapporte_ce_qu_il_remplace(self, monkeypatch):
        """Remplacer un réglage courant sans le dire ferait perdre un
        ajustement qu'on croyait fait."""
        ctx = faux_contexte({"applyMode": "auto"}, FauxStash())
        ctx.args = {"fichier": json.dumps({
            "version": 1, "reglages": {"applyMode": "manual"}})}
        rendu = self._journal(ctx, reglages.importer_reglages,
                              monkeypatch)
        assert "remplacé" in rendu.lower()

    def test_l_import_sans_changement_le_dit(self, monkeypatch):
        ctx = faux_contexte({"applyMode": "auto"}, FauxStash())
        ctx.args = {"fichier": json.dumps({
            "version": 1, "reglages": {"applyMode": "auto"}})}
        rendu = self._journal(ctx, reglages.importer_reglages,
                              monkeypatch)
        assert "aucun changement" in rendu.lower()

    def test_la_simulation_n_ecrit_pas(self, monkeypatch):
        st = FauxStash()
        ctx = faux_contexte({"dryRun": True}, st)
        ctx.args = {"fichier": json.dumps({
            "version": 1, "reglages": {"applyMode": "seuil"}})}
        rendu = self._journal(ctx, reglages.importer_reglages,
                              monkeypatch)
        assert "simulation" in rendu.lower()
        assert not st.reglages_plugin.get("applyMode")

    def test_l_import_reclame_les_secrets(self, monkeypatch):
        ctx = faux_contexte({}, FauxStash())
        ctx.args = {"fichier": json.dumps({
            "version": 1, "reglages": {},
            "secrets_a_ressaisir": ["llmApiKey"]})}
        rendu = self._journal(ctx, reglages.importer_reglages,
                              monkeypatch)
        assert "llmApiKey" in rendu


class TestLectureDuManifeste:
    """Le garde-fou contre les réglages inconnus lit le manifeste. Il
    employait PyYAML, que le conteneur de Stash n'embarque pas : il ne
    s'appliquait donc pas là où il compte, en production.

    Un garde-fou qui ne fonctionne qu'en test ne protège personne."""

    def test_les_reglages_du_manifeste_sont_reconnus(self):
        connus = reglages._reglages_connus()
        assert len(connus) > 40, len(connus)

    def test_les_cles_sont_bien_celles_du_manifeste(self):
        connus = reglages._reglages_connus()
        for attendu in ("applyMode", "batchSize", "llmApiKey",
                        "tagProfile"):
            assert attendu in connus, attendu

    def test_aucune_valeur_n_est_prise_pour_une_cle(self):
        """Les lignes indentées plus profond décrivent un réglage :
        les compter comme des clés laisserait passer n'importe
        quoi."""
        connus = reglages._reglages_connus()
        for parasite in ("displayName", "description", "type"):
            assert parasite not in connus, parasite

    def test_la_section_suivante_arrete_la_lecture(self):
        """Une ligne non indentée termine « settings: » : continuer
        ferait entrer les tâches dans la liste des réglages."""
        connus = reglages._reglages_connus()
        assert "tasks" not in connus and "name" not in connus

    def test_un_manifeste_absent_ne_leve_pas(self, monkeypatch):
        """Sans manifeste, le garde-fou se tait plutôt que
        d'empêcher tout import."""
        monkeypatch.setattr(
            Path, "read_text",
            lambda self, **k: (_ for _ in ()).throw(OSError("absent")))
        assert reglages._reglages_connus() == set()

    def test_sans_manifeste_l_import_reste_possible(self,
                                                    monkeypatch):
        """Refuser tout réglage faute de manifeste serait pire que
        d'en accepter un inconnu."""
        monkeypatch.setattr(reglages, "_reglages_connus",
                            lambda: set())
        ctx = faux_contexte({}, FauxStash())
        poses, _, _ = reglages.importer(ctx, json.dumps({
            "version": 1, "reglages": {"applyMode": "seuil"}}))
        assert "applyMode" in poses
