# -*- coding: utf-8 -*-
"""
Socle : filtrage des tags, contrôle des URLs distantes, secrets,
historique de restauration.

Les fonctions de sécurité sont testées d'abord par ce qu'elles doivent
REFUSER : un contrôle trop permissif ne se remarque pas à l'usage.
"""

import json

import noyau as n


# ── Exclusion de tags ────────────────────────────────────────────────
class TestTagExclu:
    """Motifs de la collection : « Gay » seul est du bruit dans une
    médiathèque entièrement gay, mais « Foursome (Gay) » informe."""

    EXCLUS = {"gay", "*pussy*", "*videos", "bonus*", "series", "4k"}

    def _exclu(self, nom):
        return n._tag_exclu(nom, self.EXCLUS)

    def test_correspondance_exacte(self):
        assert self._exclu("Gay")
        assert self._exclu("gay")

    def test_exact_ne_touche_pas_les_composes(self):
        for tag in ["Foursome (Gay)", "Gay Massage", "Gay Encouragement",
                    "Orgy (Gay)", "Threesome (Gay)"]:
            assert not self._exclu(tag), tag

    def test_motif_englobant(self):
        for tag in ["Hairy Pussy", "Pussy Licking", "Ass to Other's Pussy"]:
            assert self._exclu(tag), tag

    def test_motif_en_suffixe(self):
        assert self._exclu("Facial Videos")
        assert self._exclu("Cum Eating Videos")
        assert not self._exclu("Videos Extra")

    def test_motif_en_prefixe(self):
        assert self._exclu("Bonus Scene")
        assert not self._exclu("Extra Bonus")

    def test_ponctuation_et_casse_ignorees(self):
        assert n._tag_exclu("4K", {"4k"})
        assert n._tag_exclu("Series", {"series"})

    def test_liste_vide_ne_filtre_rien(self):
        assert not n._tag_exclu("Gay", set())

    def test_nom_vide(self):
        assert not n._tag_exclu("", self.EXCLUS)
        assert not n._tag_exclu(None, self.EXCLUS)


# ── Contrôle des URLs distantes ──────────────────────────────────────
class TestUrlSure:
    """Stash télécharge l'image qu'on lui donne : une source compromise
    ne doit pas pouvoir faire interroger le réseau local."""

    def test_adresses_publiques_acceptees(self):
        for u in ["https://stashdb.org/images/abc.jpg",
                  "http://cdn.exemple.com/a.png",
                  "https://exemple.com:8443/img.webp"]:
            assert n.url_sure(u), u

    def test_boucle_locale_refusee(self):
        for u in ["http://localhost/x.jpg", "http://127.0.0.1:9999/x.jpg",
                  "http://[::1]/x.jpg", "http://0.0.0.0/x.jpg"]:
            assert not n.url_sure(u), u

    def test_reseaux_prives_refuses(self):
        for u in ["http://10.0.0.5/x.jpg", "http://192.168.1.40/x.jpg",
                  "http://172.16.0.1/x.jpg", "http://172.31.255.1/x.jpg",
                  "http://169.254.169.254/latest/meta-data"]:
            assert not n.url_sure(u), u

    def test_reseau_public_ressemblant_accepte(self):
        """172.32 n'est pas dans la plage privée 172.16-31."""
        assert n.url_sure("http://172.32.0.1/x.jpg")

    def test_ipv6_locale_refusee(self):
        """« [::1] » est la boucle locale en IPv6, « fe80:: » un
        lien-local. Extraire l'hôte à la main achoppait ici : le
        premier deux-points appartient à l'adresse, pas au port."""
        assert not n.url_sure("http://[::1]/x.jpg")
        assert not n.url_sure("http://[fe80::1]/x.jpg")
        assert not n.url_sure("http://[::ffff:127.0.0.1]/x.jpg")

    def test_ecritures_detournees_refusees(self):
        """127.0.0.1 s'écrit aussi « 127.1 », « 2130706433 » ou
        « 0x7f000001 » — formes admises par les navigateurs."""
        for u in ["http://2130706433/x.jpg", "http://127.1/x.jpg",
                  "http://0x7f000001/x.jpg"]:
            assert not n.url_sure(u), u

    def test_domaines_internes_refuses(self):
        for u in ["http://nas.local/x.jpg", "http://srv.lan/x.jpg",
                  "http://box.internal/x.jpg"]:
            assert not n.url_sure(u), u

    def test_adresse_publique_ip_acceptee(self):
        assert n.url_sure("https://8.8.8.8/x.jpg")

    def test_schemas_non_http_refuses(self):
        for u in ["file:///etc/passwd", "ftp://exemple.com/x.jpg",
                  "gopher://exemple.com", "javascript:alert(1)",
                  "/chemin/relatif.jpg", "exemple.com/x.jpg"]:
            assert not n.url_sure(u), u

    def test_image_en_ligne_acceptee(self):
        """Une image incorporée ne déclenche aucune requête."""
        assert n.url_sure("data:image/jpeg;base64,/9j/4AAQ")

    def test_valeurs_vides(self):
        for u in ["", None, "   "]:
            assert not n.url_sure(u)


# ── Secrets ──────────────────────────────────────────────────────────
class TestEstSecret:

    def test_identifiants_reconnus(self):
        for nom in ["mistralApiKey", "openaiApiKey", "llmApiKey",
                    "apiToken", "clientSecret", "dbPassword",
                    "userCredential", "PASSWD"]:
            assert n.est_secret(nom), nom

    def test_reglages_ordinaires_non_secrets(self):
        for nom in ["applyMode", "batchSize", "language", "ollamaUrl",
                    "tagsExclude", "aiDefault"]:
            assert not n.est_secret(nom), nom

    def test_valeurs_limites(self):
        assert not n.est_secret("")
        assert not n.est_secret(None)


# ── Historique de restauration ───────────────────────────────────────
class TestHistorique:

    def test_passage_enregistre(self):
        h = n._historique_maj({}, {"country": ["", "FR"]})
        passages = json.loads(h)
        assert len(passages) == 1
        assert passages[0]["champs"]["country"] == ["", "FR"]
        assert "d" in passages[0], "la date du passage doit être notée"

    def test_passages_empiles(self):
        fiche = {}
        for i in range(3):
            h = n._historique_maj(fiche, {"details": ["", f"v{i}"]})
            fiche = {"custom_fields": {"enrich_historique": h}}
        assert len(json.loads(h)) == 3

    def test_dix_passages_au_plus(self):
        fiche = {}
        for i in range(15):
            h = n._historique_maj(fiche, {"details": ["", f"v{i}"]})
            fiche = {"custom_fields": {"enrich_historique": h}}
        passages = json.loads(h)
        assert len(passages) == 10
        assert passages[-1]["champs"]["details"][1] == "v14", \
            "le plus récent est conservé"

    def test_historique_corrompu_repart_a_zero(self):
        fiche = {"custom_fields": {"enrich_historique": "pas du json"}}
        passages = json.loads(n._historique_maj(fiche, {"a": ["", "b"]}))
        assert len(passages) == 1

    def test_ajouts_traces(self):
        h = n._historique_maj({}, {}, tags_aj=["5"], perfs_aj=["7"],
                              urls_aj=["https://x"])
        p = json.loads(h)[0]
        assert p.get("tags_aj") == ["5"]
        assert p.get("perfs_aj") == ["7"]
        assert p.get("urls_aj") == ["https://x"]


# ── Fraîcheur des données ────────────────────────────────────────────
class TestDateEnrich:

    def test_derniere_date_extraite(self):
        e = {"custom_fields": {"enrich_sources":
                               "bio: x · auto 2026-07-27"}}
        assert n._date_enrich(e).isoformat() == "2026-07-27"

    def test_plusieurs_dates_la_derniere_gagne(self):
        e = {"custom_fields": {"enrich_sources":
                               "restauré le 2026-01-02 · auto 2026-07-27"}}
        assert n._date_enrich(e).isoformat() == "2026-07-27"

    def test_aucune_date(self):
        assert n._date_enrich({}) is None
        assert n._date_enrich({"custom_fields": {"enrich_sources": "x"}}) \
            is None


# ── Pied de biographie ───────────────────────────────────────────────
class TestPiedDeBio:

    def test_pied_retire(self):
        base = "Une biographie factuelle."
        for marque in n.FOOTER_MARKS:
            texte = base + marque + "\nnote 9/10"
            assert n._sans_footer(texte) == base

    def test_ancien_nom_du_plugin_encore_reconnu(self):
        """Les fiches enrichies avant le renommage portent l'ancien
        marqueur : il doit rester purgeable."""
        texte = ("Bio." + "\n\n"
                 + "― Fiabilité des données (EnrichAgent) ―" + "\nnote")
        assert n._sans_footer(texte) == "Bio."

    def test_texte_sans_pied_intact(self):
        assert n._sans_footer("Bio simple.") == "Bio simple."

    def test_valeurs_vides(self):
        assert n._sans_footer("") == ""
        assert n._sans_footer(None) == ""


class TestPiedSeul:
    """Une biographie peut ne contenir QUE le pied, quand aucune source
    n'a fourni de texte. Le marqueur était cherché précédé de deux
    sauts de ligne — ceux qui le séparent du texte — si bien que ces
    fiches-là échappaient à la purge. 235 d'entre elles ont résisté à
    trois passages avant que la cause soit trouvée."""

    def test_pied_sans_texte_devant(self):
        for marque in n.FOOTER_MARKS:
            nu = marque.lstrip("\n")
            assert n._sans_footer(nu + "\nnote 9/10") == ""

    def test_pied_avec_texte_devant(self):
        for marque in n.FOOTER_MARKS:
            texte = "Une biographie."
            assert n._sans_footer(texte + marque + "\nnote") == texte

    def test_texte_sans_pied_intact(self):
        assert n._sans_footer("Rien à retirer.") == "Rien à retirer."
