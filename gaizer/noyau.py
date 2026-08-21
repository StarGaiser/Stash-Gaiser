# -*- coding: utf-8 -*-
"""Socle : contexte, réglages, état, sécurité, utilitaires
transverses. Ne dépend d'aucun autre module du plugin."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
import scoring
import i18n
import llm
from stashapi.stashapp import StashInterface
import contextlib


TAG_DEFAULT_PREFIX = "Gaizer"


PERFORMER_FIELDS = {"details", "birthdate", "height_cm", "country",
                    "ethnicity", "career_length", "measurements",
                    "circumcised"}


MAP = {"bio": "details", "years_active": "career_length"}


POIDS = {
    "stashdb.org": 0.85, "porndb": 0.80,
    "iafd": 0.85, "gevi": 0.80, "builtin_freeones": 0.60,
}


POIDS_DEFAUT = 0.6


class Context:
    def __init__(self):
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        self.args = payload.get("args", {})
        conn = payload.get("server_connection", {})
        # La connexion est CONSERVÉE : c'est elle qui permet de
        # reconnaître une adresse servie par Stash lui-même — ses
        # vignettes, notamment — sans ouvrir le contrôle qui refuse
        # les adresses locales aux sources tierces.
        self.connexion = dict(conn or {})
        self.stash = StashInterface(conn) if conn else StashInterface(
            {"Host": "localhost", "Port": 9999, "Scheme": "http"})
        cfg = {}
        try:
            cfg = self.stash.get_configuration()
        except Exception as exc:
            log.warning(f"configuration illisible : {exc}")
        self.settings = (cfg.get("plugins") or {}).get("gaizer") or {}
        # Reprise des réglages retirés : sans elle, une mise à jour
        # ferait cesser le plugin de fonctionner sans rien dire.
        repris = migrer_reglages(self)
        if repris:
            self.settings.update(repris)
            log.info("Réglages repris depuis les anciens champs : "
                     + ", ".join(sorted(repris))
                     + ". Ils seront enregistrés au prochain passage.")
        self.stash_boxes = [
            {"name": b.get("name") or b.get("endpoint"),
             "endpoint": b.get("endpoint")}
            for b in ((cfg.get("general") or {}).get("stashBoxes") or [])
            if b.get("endpoint")
        ]
        # Connaissance métier (familles, fiabilités, détecteurs) :
        # défauts de scoring.py + surcharges d'enrich_config.yml
        self.cfg = scoring.charger_config(
            str(Path(__file__).resolve().parent))
        _LANGUE["code"] = self.lang()
        try:
            _LLM["max"] = max(0, int(float(str(
                self.settings.get("maxLlmCalls") or 0))))
        except (TypeError, ValueError):
            _LLM["max"] = 0
        try:
            _LLM["delai"] = max(0.0, float(str(
                self.settings.get("llmDelayMs") or 600)) / 1000.0)
        except (TypeError, ValueError):
            _LLM["delai"] = 0.6
        if self.simulation():
            _activer_simulation(self)

    def mode(self) -> str:
        return self.args.get("mode", "")

    def tag_prefix(self) -> str:
        return self.settings.get("proposalTagPrefix") or TAG_DEFAULT_PREFIX

    def scrapers(self) -> list:
        """Scrapers performer à interroger.

        Défaut : TOUS les scrapers installés qui supportent la recherche
        par NOM (les scrapers par-URL comme EricVideos ou BelAmi ne
        peuvent pas être interrogés par nom — limite du scraper, pas du
        plugin). `scrapersList` restreint à une sous-liste,
        `scrapersExclude` retire des entrées.
        """
        try:
            dispo = self.stash.list_performer_scrapers()
        except Exception:
            dispo = []
        par_nom = [s["id"] for s in dispo
                   if "NAME" in ((s.get("performer") or {})
                                 .get("supported_scrapes") or [])]
        brut = str(self.settings.get("scrapersList") or "").strip()
        if brut:
            voulu = [x.strip() for x in brut.split(",") if x.strip()]
            retenu = [s for s in voulu if s in par_nom]
        else:
            retenu = par_nom
        exclu = {x.strip().lower() for x in
                 str(self.settings.get("scrapersExclude") or "")
                 .split(",") if x.strip()}
        return [s for s in retenu if s.lower() not in exclu]

    def fournisseurs(self) -> dict:
        """Fournisseurs connus : table embarquée + llm_providers.yml."""
        if getattr(self, "_llm_table", None) is None:
            self._llm_table = llm.charger(
                str(Path(__file__).resolve().parent))
        return self._llm_table

    def ai_for(self, usage: str):
        """Configuration IA pour un usage ('bio', 'synopsis', 'biohot').

        Réglages `aiBio`, `aiSynopsis`, `aiBiohot` au format
        « fournisseur:modèle » (ex. « openrouter:anthropic/claude-3.5
        -sonnet »), repli sur `aiDefault`. Le fournisseur peut être
        n'importe quelle entrée de llm_providers.yml. La clé vient du
        réglage dédié, sinon du réglage générique `llmApiKey` ; les
        services locaux (Ollama, LM Studio…) n'en réclament aucune.

        Retourne (fournisseur, modèle|None, clé) ou None.
        """
        val = (self.settings.get("ai" + usage.capitalize())
               or self.settings.get("aiDefault") or "").strip()
        if not val:
            return None
        fournisseur, _, modele = val.partition(":")
        fournisseur = fournisseur.strip().lower()
        conf = self.fournisseurs().get(fournisseur)
        if not conf:
            log.warning(f"fournisseur IA inconnu : « {fournisseur} ». "
                        f"Connus — {llm.liste_lisible(self.fournisseurs())}. "
                        f"En ajouter un : fichier llm_providers.yml.")
            return None
        cle = llm.cle_pour(conf, self.settings)
        if llm.besoin_de_cle(conf) and not cle:
            log.warning(f"aucune clé d'API pour « {fournisseur} » : "
                        f"renseigner « Clé d'API du fournisseur » "
                        f"dans les réglages du plugin.")
            return None
        return fournisseur, (modele.strip() or None), cle

    def use_boxes(self) -> bool:
        return self.settings.get("useStashBoxes", True)

    def use_appoint(self) -> bool:
        return self.settings.get("useExtraSources", True)

    def apply_mode(self) -> str:
        """manual : propositions à valider (tags) ;
        seuil  : propositions + tâche de masse ≥ autoAcceptThreshold ;
        auto   : la valeur la mieux notée est TOUJOURS appliquée,
                 quel que soit son score (aucune décision utilisateur
                 n'existe ni n'est enregistrée dans ce mode)."""
        m = str(self.settings.get("applyMode") or "manual").strip().lower()
        return m if m in ("manual", "seuil", "auto") else "manual"

    def auto_threshold(self) -> float:
        """Seuil d'application, borné au barème.

        Hors de [0, 10] le réglage devient un piège : à zéro ou moins
        tout s'applique, y compris les valeurs douteuses ; au-delà de
        dix plus rien ne s'applique jamais, et le plugin paraît en
        panne sans qu'aucun message ne l'explique."""
        brut = str(self.settings.get("autoAcceptThreshold") or 7.5)
        try:
            valeur = float(brut.replace(",", ".").strip())
        except (TypeError, ValueError):
            valeur = 7.5
        return max(0.0, min(10.0, valeur))


    def annotate_bio(self) -> bool:
        """Pied de bio « Fiabilité des données » sur les fiches."""
        # Défaut passé à False en 0.38 : le panneau de la fiche montre
        # la provenance en tableau, le pied ferait double emploi.
        return bool(self.settings.get("annotateBio", False))

    def lang(self) -> str:
        """Code de langue du plugin. Pilote les étiquettes, les
        messages ET la rédaction des textes.

        À défaut de réglage propre, c'est la langue que l'utilisateur
        a choisie POUR STASH qui s'applique. Lui demander de la redire
        ici serait une redite, et laisserait une installation en
        français produire de l'anglais parce qu'un second réglage est
        resté vide."""
        voulue = str(self.settings.get("language") or "").strip()
        if voulue:
            return i18n.code_langue(voulue)
        if getattr(self, "_lang_stash", None) is None:
            self._lang_stash = self._langue_de_stash()
        return self._lang_stash

    def _langue_de_stash(self) -> str:
        """Langue de l'interface Stash, ramenée à un code connu.

        Stash la donne sous forme régionale — « fr-FR », « pt-BR » —
        dont seule la première partie nous intéresse."""
        try:
            d = self.stash.call_GQL(
                "{ configuration { interface { language } } }")
            brut = ((d.get("configuration") or {}).get("interface")
                    or {}).get("language") or ""
        except Exception:
            return i18n.DEFAUT
        return i18n.code_langue(str(brut).split("-")[0])

    def langue(self) -> str:
        """Nom de la langue à donner au modèle pour la rédaction."""
        return i18n.LANGUES[self.lang()]["llm"]

    def t_brut(self, cle: str):
        """Une entrée de traduction NON textuelle, dans la langue
        courante.

        La table des profils de collection porte des tuples, non des
        phrases : `t()` les convertirait en chaîne, ce qui perdrait
        leur structure.
        """
        import i18n
        for langue in (self.lang(), i18n.DEFAUT):
            bloc = (i18n.CATALOGUE.get(langue) or {}).get("msg") or {}
            if cle in bloc:
                return bloc[cle]
        return None

    def t(self, cle: str, **kw) -> str:
        return i18n.t(cle, self.lang(), **kw)

    def tag_nom(self, cle: str) -> str:
        """Nom complet d'un tag du plugin, traduit."""
        return f"{self.tag_prefix()}:{i18n.tag(cle, self.lang())}"

    def simulation(self) -> bool:
        """Mode simulation : rien n'est écrit, tout est journalisé.

        Deux sources. Le RÉGLAGE vaut pour toutes les tâches. L'ARGUMENT
        ne vaut que pour l'appel en cours — c'est ce que passe le
        bouton « Simuler » du panneau, car cocher un réglage global
        pour éprouver une seule action, puis penser à le décocher,
        serait une invitation à l'oubli.

        Ne lire que le réglage rendait ce bouton inopérant : l'action
        s'exécutait pour de bon alors qu'on croyait l'éprouver. C'est
        le pire défaut possible sur une protection — elle rassure sans
        protéger.
        """
        if bool(self.settings.get("dryRun", False)):
            return True
        brut = (getattr(self, "args", None) or {}).get("dryRun")
        if isinstance(brut, bool):
            return brut
        return str(brut or "").strip().lower() in ("1", "true", "oui",
                                                   "yes", "vrai")

    def tags_exclus(self) -> set:
        """Tags que le plugin n'appliquera jamais aux scènes (réglage
        tagsExclude, liste séparée par des virgules). Comparaison
        insensible à la casse et à la ponctuation ; un motif terminé
        par * exclut par préfixe."""
        brut = str(self.settings.get("tagsExclude") or "")
        return {x.strip().lower() for x in brut.split(",") if x.strip()}

    def refresh_days(self) -> int:
        """Ré-enrichir une entité dont les données datent de plus de N
        jours (réglage refreshDays, 0 = jamais)."""
        try:
            return max(0, int(float(str(
                self.settings.get("refreshDays") or 0))))
        except (TypeError, ValueError):
            return 0

    # Chaque source d'enrichissement a un cout et un risque propres.
    # Celles qui DEVINENT ou TRANSMETTENT sont eteintes par defaut :
    # elles ne doivent pas s'activer a l'insu de qui installe le
    # plugin. Le chemin ne fait ni l'un ni l'autre.
    _VOIES = {
        "chemin": ("sourceChemin", True),
        "nomfichier": ("sourceNomFichier", True),
        "vision": ("sourceVision", False),
        "generiques": ("sourceGeneriques", False),
        # Epuiser les sources sur une fiche avant de passer a la
        # suivante est le comportement attendu par qui
        # decouvre : lancer une tache et qu'elle fasse ce
        # qu'elle peut.
        "enchainement": ("sourceEnchainement", True),
        # Ce que le modele sait et que les sources ignorent — un
        # prix, un fait de carriere — donne envie de revoir une
        # scene. Mais on ne peut pas distinguer ce qu'il sait de
        # ce qu'il fabrique : l'apport est donc isole, marque, et
        # eteint par defaut.
        "savoirmodele": ("sourceSavoirModele", False),
    }

    def source_active(self, source: str) -> bool:
        """Cette source d'enrichissement est-elle autorisee ?

        Un nom inconnu rend False : une faute de frappe ne doit pas
        activer silencieusement ce qu'elle ne designe pas.
        """
        entree = self._VOIES.get(str(source or "").lower())
        if not entree:
            return False
        reglage, defaut = entree
        valeur = self.settings.get(reglage)
        if valeur is None or valeur == "":
            return defaut
        if isinstance(valeur, bool):
            return valeur
        return str(valeur).strip().lower() in ("1", "true", "oui",
                                               "yes", "vrai")

    def cache_jours(self) -> int:
        """Combien de jours garder une reponse de source.

        Zero desactive le cache : l'utilisateur doit pouvoir forcer
        des reponses fraiches quand il soupconne une source d'avoir
        change."""
        try:
            return max(0, int(float(str(
                self.settings.get("cacheJours") or 30))))
        except (TypeError, ValueError):
            return 30

    def batch(self) -> int:
        """Taille de lot des tâches d'enrichissement (réglage
        batchSize, défaut 25, plafonné à 5000)."""
        try:
            n = int(float(str(self.settings.get("batchSize") or 25)))
        except (TypeError, ValueError):
            n = 25
        return max(1, min(n, 5000))


# Endpoints compatibles OpenAI chat/completions ; modèle par défaut si
# le réglage n'en précise pas (format 'provider:modèle').
ETAT_FICHIER = Path(__file__).resolve().parent / "etat.json"


def etat_lire() -> dict:
    try:
        return json.loads(ETAT_FICHIER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sans_secrets(valeur):
    """Écarte les secrets, à quelque profondeur qu'ils se trouvent.

    Un secret est une CHAÎNE portée par un nom qui en a la forme. Une
    liste ou un dictionnaire sous un tel nom est une donnée de travail
    — la liste des noms de secrets présents, par exemple — et la
    remplacer par une chaîne change son TYPE. Le code qui la relit
    échoue alors loin de l'endroit fautif : la liste devient un mot, et
    le mot se relit lettre par lettre.

    Le filtrage vivait chez l'APPELANT : la tâche de sauvegarde des
    réglages savait quoi ne pas écrire. C'était suffisant tant qu'elle
    était seule ; tout nouveau chemin d'écriture rouvrait le trou sans
    que rien ne le signale. Il appartient donc à l'écriture elle-même,
    seule à être forcément traversée."""
    if isinstance(valeur, dict):
        return {k: ("(présente)"
                    if est_secret(k) and isinstance(v, str)
                    else _sans_secrets(v))
                for k, v in valeur.items()}
    if isinstance(valeur, list):
        return [_sans_secrets(v) for v in valeur]
    return valeur


def etat_ecrire(maj: dict):
    e = etat_lire()
    e.update(maj)
    try:
        ETAT_FICHIER.write_text(
            json.dumps(_sans_secrets(e), ensure_ascii=False, indent=1),
            encoding="utf-8")
        # Le fichier voisine la configuration de Stash, lisible par
        # d'autres comptes selon l'installation : il ne contient plus
        # de secret, mais il décrit la collection.
        os.chmod(ETAT_FICHIER, 0o600)
    except Exception as exc:
        log.warning(f"état non enregistré : {exc}")


def _pause_llm_active() -> str:
    """Renvoie la date de reprise si les générations sont en pause."""
    d = str(etat_lire().get("pause_llm_jusqu") or "")
    if not d:
        return ""
    try:
        from datetime import date as _d
        jusqu = _d(*map(int, d.split("-")))
    except Exception:
        return ""
    return d if _date_auj.today() < jusqu else ""


def _programmer_demain(cat: str, msg: str):
    """Quota épuisé ou saturation persistante : les générations sont
    suspendues et REPROGRAMMÉES au lendemain. L'enrichissement factuel
    continue normalement."""
    from datetime import timedelta
    demain = (_date_auj.today() + timedelta(days=1)).isoformat()
    etat_ecrire({"pause_llm_jusqu": demain,
                 "pause_motif": msg,
                 "pause_categorie": cat,
                 "pause_posee_le": _date_auj.today().isoformat()})
    log.error(_t("ia_suspendue", motif=msg, date=demain))


# Compteur d'appels au fournisseur d'IA pour la durée de la tâche :
# un traitement de masse peut sinon consommer sans limite.
_LLM = {"n": 0, "max": 0, "averti": False, "delai": 0.6}


# Langue courante, retenue au démarrage. Les fonctions de module (appel
# au modèle de langage, gestion de la pause) n'ont pas de contexte à
# leur disposition : sans cela, leurs messages resteraient en français.
_LANGUE = {"code": i18n.DEFAUT}


def _t(cle: str, **kw) -> str:
    return i18n.t(cle, _LANGUE["code"], **kw)


def tag_id(ctx, nom: str) -> str:
    """Identifiant d'un tag, créé au besoin. Mémorisé pour la durée de
    la tâche : sans cela, chaque pose de tag coûtait une requête, soit
    des milliers d'allers-retours sur un traitement de masse."""
    cache = getattr(ctx, "_tags_cache", None)
    if cache is None:
        cache = ctx._tags_cache = {}
    if nom in cache:
        return cache[nom]
    for t in ctx.stash.find_tags(f={"name": {"value": nom,
                                             "modifier": "EQUALS"}}):
        if t["name"] == nom:
            cache[nom] = t["id"]
            return t["id"]
    tid = ctx.stash.create_tag({"name": nom})["id"]
    cache[nom] = tid
    return tid


def _historique_maj(entite: dict, changements: dict,
                    tags_aj=None, perfs_aj=None, urls_aj=None) -> str:
    """Ajoute un passage à l'historique de l'entité (custom_field
    `enrich_historique`, 10 passages max) : valeurs avant/après et ids
    ajoutés, pour revenir en arrière — poser le tag standard
    `Gaizer:restaurer` puis lancer la tâche « Restaurer »."""
    try:
        hist = json.loads((entite.get("custom_fields") or {})
                          .get("enrich_historique") or "[]")
        if not isinstance(hist, list):
            hist = []
    except Exception:
        hist = []
    entree = {"d": _date_auj.today().isoformat(),
              "champs": {k: [str(v[0] or "")[:60], str(v[1] or "")[:60]]
                         for k, v in changements.items()}}
    if tags_aj:
        entree["tags_aj"] = sorted(tags_aj)
    if perfs_aj:
        entree["perfs_aj"] = sorted(perfs_aj)
    if urls_aj:
        entree["urls_aj"] = list(urls_aj)[:12]
    hist.append(entree)
    return json.dumps(hist[-10:], ensure_ascii=False)[:1800]


def _activer_simulation(ctx):
    """Neutralise toutes les ÉCRITURES sur les entités (les créations
    de tags restent permises : elles sont inoffensives et nécessaires
    au calcul). Chaque écriture évitée est journalisée."""
    # Toute mutation qui touche une ENTITÉ. Seules les créations de
    # tags restent permises : elles sont inoffensives et nécessaires
    # au calcul des propositions.
    ecrit = re.compile(
        r"(performerUpdate|performerCreate|performerDestroy|"
        r"sceneUpdate|sceneDestroy|"
        r"studioUpdate|studioCreate|studioDestroy|"
        r"groupUpdate|groupCreate|groupDestroy|"
        r"tagUpdate|tagsMerge|tagDestroy|"
        r"configurePlugin)")
    vrai_gql = ctx.stash.call_GQL

    def gql_simule(query, variables=None, **kw):
        m = ecrit.search(query or "")
        if m:
            log.info(f"  [SIMULATION] {m.group(1)} évité : "
                     f"{json.dumps(variables, ensure_ascii=False)[:180]}")
            return {}
        return vrai_gql(query, variables, **kw)

    def maj_simulee(nom):
        def _f(maj, *a, **k):
            log.info(f"  [SIMULATION] {nom} évité : "
                     f"{json.dumps(maj, ensure_ascii=False)[:180]}")
            return {}
        return _f

    ctx.stash.call_GQL = gql_simule
    ctx.stash.update_performer = maj_simulee("update_performer")
    ctx.stash.update_scene = maj_simulee("update_scene")
    # La SUPPRESSION d'une étiquette échappait à la simulation : la
    # création de tags est délibérément permise, mais leur destruction
    # est irréversible et emporte tout ce qui y était attaché.
    ctx.stash.destroy_tag = maj_simulee("destroy_tag")
    log.info(ctx.t("simulation_active"))


def _tag_exclu(nom: str, exclus: set) -> bool:
    if not exclus:
        return False
    bas = (nom or "").strip().lower()
    plat = re.sub(r"[^a-z0-9]", "", bas)
    for motif in exclus:
        deb, fin = motif.startswith("*"), motif.endswith("*")
        noyau = re.sub(r"[^a-z0-9]", "", motif.strip("*"))
        if not noyau:
            continue
        if deb and fin:
            if noyau in plat:              # *motif* : n'importe où
                return True
        elif fin:
            if plat.startswith(noyau):     # motif* : préfixe
                return True
        elif deb:
            if plat.endswith(noyau):       # *motif : suffixe
                return True
        elif bas == motif or plat == noyau:
            return True
    return False


def _date_enrich(e: dict):
    """Dernière date figurant dans enrich_sources (aaaa-mm-jj)."""
    src = str((e.get("custom_fields") or {}).get("enrich_sources") or "")
    dates = re.findall(r"(\d{4})-(\d{2})-(\d{2})", src)
    if not dates:
        return None
    try:
        from datetime import date as _d
        return _d(*map(int, dates[-1]))
    except ValueError:
        return None


def _perime(ctx, e: dict) -> bool:
    n = ctx.refresh_days()
    if not n:
        return False
    d = _date_enrich(e)
    if not d:
        return False
    return (_date_auj.today() - d).days >= n


# Noms d'hôtes toujours refusés, indépendamment de la résolution DNS.
_NOMS_INTERNES = re.compile(
    r"^(localhost|.*\.local|.*\.localhost|.*\.internal|.*\.home"
    r"|.*\.lan)$", re.I)


def _hote_de(url: str):
    """Hôte d'une URL http(s), crochets IPv6 retirés.

    `urllib.parse` est préféré à une expression régulière : extraire
    l'hôte à la main achoppe sur « http://[::1]/ », où le premier
    deux-points appartient à l'adresse et non au port."""
    from urllib.parse import urlsplit
    try:
        parties = urlsplit(url)
    except ValueError:
        return None
    if parties.scheme.lower() not in ("http", "https"):
        return None
    hote = parties.hostname          # décrochète et met en minuscules
    return hote or None


# Champs hérités d'un import et leur équivalent arbitré par le plugin.
# Ils coexistent sans jamais se confronter : personne ne s'aperçoit
# qu'ils se contredisent, et un texte généré peut reprendre le mauvais.
CHAMPS_HERITES = {
    "sexe_type": ("circumcised", {"cut": "cut", "coupé": "cut",
                                  "coupe": "cut", "circoncis": "cut",
                                  "uncut": "uncut",
                                  "non coupé": "uncut",
                                  "non circoncis": "uncut"}),
}


# Réglages retirés, et le champ générique qui les remplace. Le
# fournisseur est désigné par le nom du modèle : la clé n'a pas à le
# redire.
_ANCIENS = {
    "openai": ("openaiApiKey", None),
    "mistral": ("mistralApiKey", None),
    "anthropic": ("anthropicApiKey", None),
    "openrouter": ("openrouterApiKey", None),
    "groq": ("groqApiKey", None),
    "deepseek": ("deepseekApiKey", None),
    "google": ("googleApiKey", None),
    "xai": ("xaiApiKey", None),
    "together": ("togetherApiKey", None),
    "perplexity": ("perplexityApiKey", None),
    "ollama": (None, "ollamaUrl"),
    "lmstudio": (None, "lmstudioUrl"),
    "llamacpp": (None, "llamacppUrl"),
    "vllm": (None, "vllmUrl"),
}


def migrer_reglages(ctx) -> dict:
    """Valeurs à reprendre depuis les réglages retirés.

    Retirer un champ ne doit pas perdre sa valeur : celui qui met à
    jour a renseigné l'ancien, le nouveau est vide, et l'ancien a
    disparu de l'écran. Sans reprise, le plugin cesse de fonctionner
    sans rien dire.

    Seule la valeur du fournisseur EMPLOYÉ est reprise : plusieurs
    anciennes clés peuvent coexister, et les recopier toutes n'aurait
    aucun sens dans un champ unique.
    """
    reglages = getattr(ctx, "settings", None) or {}
    repris = {}
    for usage in ("vision", "biohot", "bio", "synopsis", ""):
        val = str(reglages.get(f"ai{usage.capitalize()}" if usage
                               else "aiDefault") or "").strip()
        if not val:
            continue
        fournisseur = val.partition(":")[0].strip().lower()
        cle_ancienne, url_ancienne = _ANCIENS.get(fournisseur,
                                                  (None, None))
        if (cle_ancienne and not str(reglages.get("llmApiKey")
                                     or "").strip()):
            valeur = str(reglages.get(cle_ancienne) or "").strip()
            if valeur:
                repris["llmApiKey"] = valeur
        if (url_ancienne and not str(reglages.get("llmUrl")
                                     or "").strip()):
            valeur = str(reglages.get(url_ancienne) or "").strip()
            if valeur:
                repris["llmUrl"] = valeur
        if repris:
            break
    return repris


def valeur_vide(valeur) -> bool:
    """Une valeur qui n'en est pas une.

    Trois formes se présentent, et les trois viennent de sources
    réelles : l'absence, la chaîne d'espaces — comptée comme réponse,
    elle faisait croire qu'une source connaît un champ qu'elle ignore
    et faussait le nombre de familles d'accord — et la date nulle
    « 0000-00-00 », qui interrompait autrefois le traitement d'une
    fiche entière.

    Cette notion vivait en deux exemplaires, dans la collecte et dans
    les sources d'appoint. Deux implémentations d'une même décision
    divergent : la seconde n'est pas corrigée quand la première l'est.
    """
    if valeur is None:
        return True
    texte = str(valeur).strip()
    if texte == "" or texte.strip("0-") == "":
        return True
    # Une quatrième forme, venue des mêmes sources : le MOT qui dit
    # l'absence. Une API qui sérialise mal rend « null », « none » ou
    # « N/A » comme une chaîne ordinaire — et ces trois-là
    # s'écriraient tels quels dans une fiche, où personne ne les
    # distinguerait d'une vraie valeur.
    #
    # « na » et « - » sont ÉCARTÉS de cette liste : trop courts pour
    # être sûrs, ils peuvent être une vraie valeur — un tiret sert de
    # séparateur, et « na » ouvre des noms propres. Compter un
    # marqueur interne comme vide a fait échouer un test existant, ce
    # qui est précisément le genre de dégât qu'un mot trop court
    # provoque.
    return texte.lower() in ("null", "none", "nil", "n/a",
                             "undefined", "unknown")


def url_sure(url) -> bool:
    """Une image proposée par une source distante est téléchargée par
    Stash : on n'accepte que http(s) vers un hôte PUBLIC, pour qu'une
    source compromise ne puisse pas faire interroger le réseau local
    (SSRF) ni glisser un « file:// ».

    Les adresses IP sont jugées par `ipaddress`, qui connaît les
    boucles locales, les plages privées, les liens-locaux et les
    formes détournées — « 2130706433 » vaut 127.0.0.1, et « [::1] »
    est la boucle locale en IPv6."""
    url = str(url or "").strip()
    if not url:
        return False
    if url.startswith("data:image/"):
        return True                      # image incorporée, sans requête
    hote = _hote_de(url)
    if not hote or _NOMS_INTERNES.match(hote):
        return False
    for adr in _adresses_de(hote):
        if (adr.is_private or adr.is_loopback or adr.is_link_local
                or adr.is_reserved or adr.is_multicast
                or adr.is_unspecified):
            return False
        mappee = getattr(adr, "ipv4_mapped", None)
        if mappee and (mappee.is_private or mappee.is_loopback):
            return False
    return True


def _adresses_de(hote: str) -> list:
    """Adresses IP que cet hôte peut désigner.

    Une même adresse s'écrit de plusieurs façons : « 127.0.0.1 », mais
    aussi « 127.1 », « 2130706433 » ou « 0x7f000001 ». `inet_aton` les
    accepte toutes, comme le font les navigateurs et la plupart des
    bibliothèques réseau — un contrôle qui ne reconnaîtrait que la
    notation pointée serait contournable d'un caractère."""
    import ipaddress
    import socket
    trouvees = []
    with contextlib.suppress(ValueError):
        trouvees.append(ipaddress.ip_address(hote))
    if ":" not in hote:
        try:
            octets = socket.inet_aton(hote)
            trouvees.append(ipaddress.IPv4Address(octets))
        except OSError:
            # Un nom d'hôte qui n'est pas une adresse IPv4 : c'est le
            # cas ORDINAIRE — « exemple.test » n'en est pas une. Le
            # journaliser noierait le journal sous des non-événements.
            pass
    return trouvees


def est_secret(nom: str) -> bool:
    """Un réglage porteur d'identifiant ne doit jamais être écrit sur
    disque ni journalisé."""
    bas = (nom or "").lower()
    return any(m in bas for m in ("key", "token", "secret", "password",
                                  "passwd", "credential"))


def _sauver_reglages(ctx):
    """Copie les réglages dans etat.json à chaque exécution.

    La mutation `configurePlugin` de Stash REMPLACE la table des
    réglages au lieu de la compléter : un outil tiers (ou un appel
    d'API distrait) qui n'écrit qu'une clé efface toutes les autres,
    sans prévenir. Cette copie permet de s'en apercevoir et de tout
    remettre en place — tâche « Restaurer les réglages ».

    SÉCURITÉ : les clés d'API ne sont jamais copiées. Seule leur
    PRÉSENCE est mémorisée, afin de pouvoir signaler leur disparition
    sans jamais écrire un identifiant sur le disque."""
    courant = {k: v for k, v in (ctx.settings or {}).items()
               if v not in (None, "") and not est_secret(k)}
    secrets = sorted(k for k, v in (ctx.settings or {}).items()
                     if v not in (None, "") and est_secret(k))
    if not courant:
        return
    e = etat_lire()
    ancien = e.get("reglages") or {}
    secrets_avant = e.get("reglages_secrets") or []
    perdus_secrets = sorted(set(secrets_avant) - set(secrets))
    if perdus_secrets:
        log.error(f"IDENTIFIANT(S) DISPARU(S) : "
                  f"{', '.join(perdus_secrets)}. Ils ne sont jamais "
                  f"copiés sur disque pour des raisons de sécurité : "
                  f"il faut les ressaisir dans les réglages du "
                  f"plugin.")
    # Alerte si la configuration a fondu d'un coup
    if len(ancien) >= 5 and len(courant) <= max(2, len(ancien) // 3):
        perdus = sorted(set(ancien) - set(courant))
        log.error(f"RÉGLAGES PERDUS : {len(ancien)} enregistrés, "
                  f"{len(courant)} présents. Manquent : "
                  f"{', '.join(perdus[:10])}. La mutation "
                  f"configurePlugin de Stash remplace toute la table "
                  f"quand on n'écrit qu'une clé. Tâche « Restaurer "
                  f"les réglages » pour les remettre.")
        return          # ne pas écraser la sauvegarde avec le vide
    if courant != ancien or secrets != secrets_avant:
        etat_ecrire({"reglages": courant,
                     "reglages_secrets": secrets,
                     "reglages_le": _date_auj.today().isoformat()})


def _reprise_opportuniste(ctx):
    """Lève la pause des générations dès que son échéance est passée.

    Appelée au début de CHAQUE tâche : le plugin n'a donc besoin
    d'aucun ordonnanceur externe (cron, systemd, planificateur
    Windows…) pour repartir — la première tâche lancée après la date de
    reprise suffit, et le travail en attente est de toute façon
    recalculé à chaque passage. Un ordonnanceur reste possible mais
    facultatif : voir la tâche « Reprendre les générations IA »."""
    e = etat_lire()
    prevu = str(e.get("pause_llm_jusqu") or "")
    if not prevu or _pause_llm_active():
        return
    etat_ecrire({"pause_llm_jusqu": "", "pause_motif": "",
                 "pause_categorie": "",
                 "derniere_reprise": _date_auj.today().isoformat()})
    _LLM["averti_pause"] = False
    log.info(ctx.t("ia_reprise", pose=e.get("pause_posee_le"),
                   motif=e.get("pause_motif"), date=prevu))


def _ligne_fiche(champ: str, liste: list) -> str:
    parts = []
    for c in liste:
        com = "; ".join(c["commentaires"])
        parts.append(f"{'★' if c['recommande'] else ''}{c['valeur']} "
                     f"{c['note']}/10 ({'+'.join(c['sources'])}"
                     f"{' — ' + com if com else ''})")
    return f"{champ}: " + " · ".join(parts)


def footer_mark(ctx) -> str:
    return "\n\n" + ctx.t("pied_bio")


# Marqueurs de toutes les langues, pour retrouver et purger un pied de
# bio écrit avant un changement de langue.
# Le marqueur du pied de bio a changé de nom avec le plugin : les
# anciennes variantes restent reconnues pour que la purge et la
# réécriture fonctionnent sur les fiches enrichies auparavant.
_PIEDS_HERITES = ("― Fiabilité des données (EnrichAgent) ―",
                  "― Data reliability (EnrichAgent) ―")


FOOTER_MARKS = tuple(
    "\n\n" + v for v in
    (set(i18n.toutes_variantes("msg", "pied_bio")) | set(_PIEDS_HERITES)))


def _sans_footer(details: str) -> str:
    """Biographie débarrassée du pied « Fiabilité des données ».

    Le marqueur était cherché précédé de deux sauts de ligne, ceux qui
    le séparent du texte. Or une biographie peut ne contenir QUE le
    pied — c'est le cas quand aucune source n'a fourni de bio : il n'y
    a alors rien devant lui, et la purge le laissait intact. Le
    marqueur est donc cherché seul, ce qui couvre les deux cas."""
    d = details or ""
    for m in FOOTER_MARKS:
        nu = m.lstrip("\n")
        if nu and nu in d:
            d = d.split(nu)[0]
    return d.rstrip()
