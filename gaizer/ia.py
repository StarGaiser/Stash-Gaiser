# -*- coding: utf-8 -*-
"""Dialogue avec les modèles de langage : diagnostic des
erreurs, plafonnement, et rédaction des textes."""

from __future__ import annotations

import json
import time
import re
import sys
from datetime import date as _date_auj
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from stashapi import log
import noyau
import profil
import sources
import llm
from noyau import (
    POIDS_DEFAUT,
    _LLM,
    _pause_llm_active,
    _programmer_demain,
    _t,
    etat_ecrire,
    etat_lire)
from collecte import stats_collection


# Vocabulaire des fournisseurs → cause réelle. Les messages d'erreur
# des API sont illisibles pour un utilisateur ; on les traduit.
# (mots reconnus, catégorie, clé du message traduit)
_MOTIFS_LLM = [
    (("insufficient_quota", "quota exceeded", "exceeded your current",
      "credit balance", "billing", "payment required",
      "no credits", "plan limit", "monthly limit", "daily limit"),
     "quota", "ia_quota"),
    (("rate limit", "rate_limit", "too many requests",
      "requests per minute", "requests per second",
      "tokens per minute"),
     "debit", "ia_debit"),
    (("overloaded", "capacity", "temporarily unavailable",
      "server_error", "bad gateway"),
     "indispo", "ia_indispo"),
    (("invalid api key", "unauthorized", "authentication",
      "invalid_api_key", "no api key", "api key not"),
     "cle", "ia_cle"),
    (("model", "not found", "does not exist", "decommissioned"),
     "modele", "ia_modele"),
    (("context length", "too long", "maximum context",
      "string too long"),
     "requete", "ia_requete"),
]


def _diag_llm(exc, code=None, corps="") -> tuple:
    """(catégorie, message lisible en français) à partir d'une erreur
    brute du fournisseur. Catégories : quota, debit, cle, modele,
    requete, indispo, reseau."""
    txt = f"{corps} {exc}".lower()
    for mots, cat, cle in _MOTIFS_LLM:
        if any(m in txt for m in mots):
            return cat, _t(cle)
    if code == 429:
        return "debit", _t("ia_debit")
    if code in (401, 403):
        return "cle", _t("ia_cle")
    if code == 402:
        return "quota", _t("ia_quota")
    if code and 500 <= int(code) < 600:
        return "indispo", _t("ia_indispo")
    if "timed out" in txt or "timeout" in txt:
        return "reseau", _t("ia_timeout")
    if "urlopen error" in txt or "name or service" in txt:
        return "reseau", _t("ia_reseau")
    return "indispo", _t("ia_inattendu")


# Longueur de réponse attendue selon l'usage. Un synopsis factuel n'a
# pas besoin d'autant de place qu'une présentation libre, et les jetons
# de sortie sont facturés plus cher que ceux d'entrée.
# ── Budgets de sortie ────────────────────────────────────────────
# Le budget borne ce que le modèle a le droit d'ÉCRIRE, en jetons.
#
# POURQUOI. Trois raisons, dans cet ordre d'importance.
#
# Le modèle remplit toujours l'espace qu'on lui laisse : sans borne,
# une présentation de trois phrases en fait dix. Une consigne dans le
# prompt n'y suffit pas — elle relève de sa bonne volonté, le budget
# coupe.
#
# Les jetons de sortie sont facturés plus cher que ceux d'entrée,
# souvent le triple. Sur une collection de mille fiches, la
# différence entre 220 et 400 jetons est réelle.
#
# Un texte trop long ne tient pas dans une fiche : Stash affiche la
# biographie dans un encart, et ce qui déborde est simplement perdu
# pour le lecteur, après avoir été payé.
#
# COMMENT. Trois signes par jeton est la mesure du français — un peu
# moins que l'anglais, dont les modèles sont surtout nourris. Le
# budget est donc la longueur visée divisée par trois, sans marge :
# la marge inciterait le modèle à l'employer.
#
#   synopsis   150 → ~450 signes : deux ou trois phrases factuelles
#   studio     170 → ~510 signes : présentation d'un catalogue
#   bio        220 → ~660 signes : biographie factuelle complète
#   biohot     220 → ~660 signes : quatre phrases denses
#
# Ces valeurs viennent de textes réellement produits, non d'un
# calcul : 260 tronquait les présentations au milieu d'un mot, 400
# les laissait doubler de longueur. 220 est le point où le modèle
# finit naturellement avant la coupe.
BUDGETS = {"bio": 220, "synopsis": 150, "studio": 170, "biohot": 220}


# Mots qui ouvrent une phrase sans etre des noms propres : les
# retenir ferait refuser tous les textes.
_COURANTS = {
    "il", "elle", "un", "une", "le", "la", "les", "des", "ce", "cet",
    "son", "sa", "ses", "corps", "bite", "cul", "quatre", "trois",
    "deux", "cinq", "six", "sept", "huit", "neuf", "dix", "dans",
    "chez", "pas", "mais", "et", "ou", "avec", "sans", "sur", "au",
    "aux", "du", "de", "pour", "par", "en", "chaque", "tout", "toute",
    "actif", "passif", "physique", "barbe", "torse", "peau", "matiere",
    "matière", "on", "ni", "puis", "quand", "comme", "meme", "même",
}


# Marque qui isole ce que le modele apporte de son propre savoir.
# Fondu dans le texte, cet apport devient invérifiable ; a part, il se
# lit, se verifie et se supprime d'un geste.
MARQUE_APPORT = "[non vérifié]"


def separer_apport(texte):
    """Sépare le texte fondé sur les données de l'apport du modèle.

    Rend (base, apport). L'apport peut être vide — c'est le cas
    ordinaire, et le cas souhaitable quand le modèle n'est pas sûr.
    """
    brut = str(texte or "")
    i = brut.find(MARQUE_APPORT)
    if i < 0:
        return brut, ""
    base = brut[:i].strip()
    apport = brut[i + len(MARQUE_APPORT):].strip()
    return base, apport


def _ranger_apport(ctx, genre: str, ident: str, apport: str) -> None:
    """Range l'apport dans un champ à part, jamais dans la
    biographie.

    Un apport non signalé serait pire que pas d'apport du tout : le
    lecteur croirait à un fait établi, et rien ne le détromperait.
    """
    if not str(apport or "").strip():
        return
    ecrire = {"performer": "update_performer",
              "studio": "update_studio",
              "scene": "update_scene"}.get(genre)
    if not ecrire:
        return
    try:
        getattr(ctx.stash, ecrire)({
            "id": ident,
            "custom_fields": {"partial": {
                "enrich_apport_modele": str(apport)[:400]}}})
    except Exception as exc:
        log.debug(f"apport non rangé : {str(exc)[:70]}")


def _noms_fournis(matiere) -> set:
    """Tous les noms propres présents dans la matière transmise.

    Ce qui figure dans les données peut être cité ; le reste est
    inventé, quelle que soit sa vraisemblance.
    """
    brut = json.dumps(matiere or {}, ensure_ascii=False)
    return set(re.findall(
        r"[A-ZÉÈÀÂÎÔÛÇ][\wéèàâîôûç'-]+"
        r"(?:\s+[A-ZÉÈÀÂÎÔÛÇ][\wéèàâîôûç'-]+)*", brut))


def noms_verifies(texte, connus) -> bool:
    """Le texte ne cite-t-il que des noms propres FOURNIS ?

    Un nom de studio plausible mais faux est pire qu'un studio tu : il
    a l'air d'un fait, personne ne le verifie, et il decrit une
    collection reelle.

    La detection reste grossiere — deux mots capitalises consecutifs —
    parce qu'une detection fine refuserait des textes justes. Mieux
    vaut manquer une invention que rejeter dix bons textes.
    """
    if not texte:
        return True
    reduits = {re.sub(r"[^a-z0-9]", "", str(n).lower())
               for n in (connus or set())}
    # Suites d'au moins deux mots capitalises : la forme d'un nom de
    # studio ou de personne.
    for suite in re.findall(
            r"\b([A-ZÉÈÀÂÎÔÛÇ][\wéèàâîôûç'-]+"
            r"(?:\s+[A-ZÉÈÀÂÎÔÛÇ][\wéèàâîôûç'-]+)+)", str(texte)):
        mots = suite.split()
        # Un debut de phrase capitalise suivi d'un nom propre n'est
        # pas un nom propre entier.
        while mots and mots[0].lower() in _COURANTS:
            mots.pop(0)
        if len(mots) < 2:
            continue
        cle = re.sub(r"[^a-z0-9]", "", " ".join(mots).lower())
        if cle and not any(cle in c or c in cle for c in reduits):
            log.debug(f"nom propre non fourni : {' '.join(mots)[:40]}")
            return False
    return True


def empreinte_sources(usage: str, prompt: str) -> str:
    """Signature courte de ce qui a servi à produire un texte.

    Régénérer un texte dont les sources n'ont pas bougé coûte autant
    que la première fois pour un résultat équivalent. L'empreinte est
    rangée sur la fiche : au passage suivant, si elle n'a pas changé,
    l'appel est évité. Sur une collection déjà enrichie, l'économie
    porte sur la quasi-totalité des appels."""
    import hashlib
    graine = f"{usage}|{prompt}".encode("utf-8", "replace")
    return hashlib.sha1(graine, usedforsecurity=False).hexdigest()[:16]


def texte_a_jour(entite: dict, usage: str, prompt: str,
                 champ_texte: str) -> bool:
    """Vrai si le texte existant provient déjà de ces sources-là."""
    cf = (entite or {}).get("custom_fields") or {}
    if not str(cf.get(champ_texte) or "").strip():
        return False
    connues = str(cf.get("enrich_ia_empreintes") or "")
    return f"{usage}:{empreinte_sources(usage, prompt)}" in connues


def marquer_empreinte(cf: dict, usage: str, prompt: str) -> dict:
    """Ajoute (ou remplace) l'empreinte de cet usage."""
    connues = [x for x in str(cf.get("enrich_ia_empreintes") or "")
               .split(" ") if x and not x.startswith(f"{usage}:")]
    connues.append(f"{usage}:{empreinte_sources(usage, prompt)}")
    cf["enrich_ia_empreintes"] = " ".join(connues)[:300]
    return cf


def _appel_llm(provider, model, key, prompt, temperature=0.2,
               essais=3, conf=None, reglages=None, budget=260):
    jusqu = _pause_llm_active()
    if jusqu:
        if not _LLM.get("averti_pause"):
            log.warning(_t("ia_en_pause", date=jusqu,
                           motif=etat_lire().get("pause_motif")))
            _LLM["averti_pause"] = True
        return None
    # Espacement des appels : les fournisseurs limitent le débit et
    # une rafale fait échouer des générations en silence.
    if _LLM["n"] and _LLM.get("delai"):
        # « _t » est déjà la fonction de traduction dans ce module :
        # l'employer aussi pour « time » la masquait dans toute la
        # portée, et le message de pause IA plus haut levait une
        # UnboundLocalError — invisible tant qu'aucune limite de débit
        # n'était atteinte.
        time.sleep(_LLM["delai"])
    if _LLM["max"] and _LLM["n"] >= _LLM["max"]:
        if not _LLM["averti"]:
            log.warning(_t("plafond_ia", max=_LLM["max"]))
            _LLM["averti"] = True
        return None
    _LLM["n"] += 1
    return _appel_llm_plafonne(provider, model, key, prompt,
                               temperature, essais, conf, reglages,
                               budget)


def _appel_llm_plafonne(provider, model, key, prompt, temperature=0.2,
                        essais=3, conf=None, reglages=None,
                        budget=260):
    """Réessaie avec attente croissante sur 429/5xx (limites de débit
    des fournisseurs) : sans cela, un traitement de masse perd des
    générations en silence."""
    import time
    for tentative in range(essais):
        r = _appel_llm_une_fois(provider, model, key, prompt,
                                temperature, conf, reglages, budget)
        if r is not None:
            return r
        cat = _LLM.get("derniere_cat")
        # Inutile d'insister : clé refusée, modèle inconnu, quota mort.
        if cat in ("cle", "modele", "quota"):
            break
        if tentative < essais - 1:
            time.sleep(3 * (tentative + 1))
    cat = _LLM.get("derniere_cat")
    msg = _LLM.get("dernier_msg") or "erreur du fournisseur IA"
    # Quota épuisé → report au lendemain. Saturation qui persiste après
    # tous les réessais → même traitement (le service ne rendra rien de
    # plus aujourd'hui).
    if cat == "quota":
        _programmer_demain(cat, msg)
    elif cat == "debit":
        _LLM["debit_consecutifs"] = _LLM.get("debit_consecutifs", 0) + 1
        if _LLM["debit_consecutifs"] >= 8:
            _programmer_demain(
                cat, msg + " de façon répétée (8 échecs consécutifs)")
    if cat != "debit":
        _LLM["debit_consecutifs"] = 0
    return None


def _appel_llm_une_fois(provider, model, key, prompt, temperature=0.2,
                        conf=None, reglages=None, budget=260):
    """Un appel, un résultat ou None. Le dialogue avec le service est
    entièrement décrit par llm.py : ajouter un fournisseur ne demande
    aucune modification ici.

    temperature : 0.2 pour le factuel (bios, synopsis) ; la bio hot
    utilise la sienne (réglage biohotTemperature, défaut 0.7)."""
    import urllib.request
    conf = conf or llm.charger(
        str(Path(__file__).resolve().parent)).get(provider)
    if not conf:
        log.warning(f"fournisseur IA inconnu : {provider}")
        return None
    url = llm.url_pour(conf, reglages or {})
    req = llm.construire_requete(conf, url, key,
                                 model or conf.get("model"),
                                 prompt, temperature,
                                 max_tokens=budget)
    # L'adresse vient de llm_providers.yml, que l'utilisateur peut
    # modifier : sans contrôle, un « file:// » y ferait lire un fichier
    # local et l'envoyer dans la réponse.
    if not noyau.url_sure(url):
        raise ValueError(f"adresse de fournisseur refusée : {url[:60]}")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            # Le plafond protège d'un fournisseur qui déverserait
            # des kilo-octets, mais il ne doit pas annuler le budget
            # demandé : 480 signes était la taille d'UNE biographie
            # courte, et une présentation de quatre phrases denses
            # s'y terminait au milieu d'un mot.
            #
            # Trois signes par jeton est la mesure du français ; la
            # marge évite de couper ce qu'on vient de payer.
            plafond = max(600, int(budget) * 4)
            texte = llm.lire_reponse(conf, r.read())[:plafond]
        if not texte:
            raise ValueError("réponse vide du fournisseur")
        _LLM["derniere_cat"] = None
        _LLM["dernier_msg"] = None
        _LLM["debit_consecutifs"] = 0
        return texte
    except Exception as exc:
        code = getattr(exc, "code", None)
        corps = ""
        try:
            corps = exc.read().decode("utf-8", "replace")[:400]
        except Exception as exc:
            log.debug(f"opération : {exc}")
        cat, msg = _diag_llm(exc, code, corps)
        _LLM["derniere_cat"] = cat
        _LLM["dernier_msg"] = msg
        _LLM["incidents"] = _LLM.get("incidents", 0) + 1
        # Message LISIBLE dans le log de la tâche (visible dans l'UI),
        # le détail technique restant en debug.
        log.warning(_t("ia_indisponible", motif=msg)
                    + (f" [HTTP {code}]" if code else ""))
        log.debug(f"détail brut : {corps or exc}")
        etat_ecrire({"dernier_incident": {
            "date": _date_auj.today().isoformat(),
            "categorie": cat, "message": msg,
            "http": code, "fournisseur": provider,
            "detail": (corps or str(exc))[:300]}})
        return None


# Prompt PAR DÉFAUT de la bio hot. Personnalisable via le réglage
# `biohotPrompt` (placeholder {nom} disponible ; les données calculées
# sont toujours ajoutées à la suite). VIDER le réglage = revenir à ce
# défaut — c'est la réinitialisation. Reproduit aussi dans le README.
PROMPT_BIOHOT_CONSIGNES = (
    "\n\nPRÉSENTATION : n'écris ni titre, ni nom en tête, ni "
    "astérisques, ni aucun balisage — le nom figure déjà au-dessus du "
    "texte, et le balisage s'affiche tel quel. Rédige uniquement des "
    "phrases."
)

def prompt_biohot(ctx, fiche=None) -> str:
    """Instructions de rédaction de la présentation, dans la langue
    voulue et avec la langue de sortie déjà substituée.

    Les instructions étaient en français quelle que soit la langue
    demandée. Un modèle sommé de répondre en néerlandais avec des
    consignes françaises obéit mal : il glisse vers la langue des
    consignes, et sa compréhension des nuances se dégrade.

    Un prompt saisi par l'utilisateur prime : c'est le sien."""
    perso = str(ctx.settings.get("biohotPrompt") or "").strip()
    gabarit = perso or ctx.t("prompt_biohot")
    if not perso:
        gabarit += ctx.t("prompt_biohot_consignes")

    # Demander un apport puis le jeter couterait des jetons pour
    # rien : le prompt ne le reclame que si le reglage l'autorise.
    if ctx.source_active("savoirmodele"):
        gabarit += ctx.t("prompt_biohot_apport")
    return _selon_profil(ctx, gabarit, fiche).replace("{langue}",
                                               ctx.langue())


def _selon_profil(ctx, gabarit: str, fiche=None) -> str:
    """Adapte le prompt au profil de la collection.

    Le prompt disait « acteur porno gay » : c'était un cas d'usage,
    pas une propriété du plugin. Quelqu'un dont la médiathèque est
    hétéro, trans ou mixte recevait un texte qui supposait la sienne
    gay.

    Ce qui change est ÉTROIT : le mot qui désigne la personne, la
    mention d'orientation, et le contraste qui a du sens — « un hétéro
    qui tourne gay » n'excite que dans une collection gay. Le ton, les
    garde-fous et la longueur n'en dépendent pas, et les faire varier
    multiplierait par sept le risque qu'une règle se perde.

    Sans profil, rien n'est supposé : le modèle s'en tient aux
    données, ce qu'il devait faire de toute façon.
    """
    profils = ctx.t_brut("profils_biohot") or {}
    # Le réglage prime ; à défaut, la composition des scènes le
    # suggère. Stash ne porte aucune orientation sur les fiches, mais
    # une scène jouée par deux hommes est une scène gay quelle que
    # soit celle de qui la joue.
    cle = profil.profil_courant(ctx) or ""
    mention, _ancien, contraste = profils.get(cle, ("", "", ""))
    # Le mot qui désigne la personne vient de SA fiche, non du profil
    # de la collection : celui-ci ne peut pas le savoir.
    return (gabarit.replace("{profil}", mention)
            .replace("{qui}", _qui_designer(ctx, fiche))
            .replace("{contraste}", contraste))


def _qui_designer(ctx, fiche: dict) -> str:
    """Le mot qui désigne cette personne dans le prompt.

    Le GENRE de la fiche prime : le profil de collection ne dit rien
    d'une personne — un porno hétéro est joué par des actrices autant
    que par des acteurs, et déduire l'un de l'autre efface les femmes
    d'un genre qui en est fait.

    Stash porte ce champ, mais il est vide sur la quasi-totalité des
    fiches d'une collection réelle : le profil sert alors de repli,
    car un porno gay est joué par des hommes. C'est une supposition,
    meilleure que rien.

    Sans l'un ni l'autre, le terme est neutre : présumer serait pire
    que rester vague.
    """
    termes = ctx.t_brut("termes_personne") or {}
    genre = str((fiche or {}).get("gender") or "").strip().upper()
    if genre in ("MALE", "FEMALE"):
        return termes.get(genre) or termes.get("NEUTRE") or ""
    # Les identités trans et non binaires emploient le terme neutre :
    # Stash les distingue, mais présumer à partir de là serait une
    # atteinte, et « interprète » ne présume rien.
    if genre:
        return termes.get("NEUTRE") or ""
    devine = profil.profil_courant(ctx) or ""
    suppose = {"gay": "MALE", "lesbien": "FEMALE"}.get(devine)
    if suppose:
        return termes.get(suppose) or termes.get("NEUTRE") or ""
    return termes.get("NEUTRE") or ""


def generer_bio_hot(ctx, fiche: dict, raw: dict, force: bool = False):
    """Bio « hot » : style sexuel de l'acteur, matos, partenaires et
    studios récurrents dans la collection. Champ SÉPARÉ de la bio
    officielle (`custom_field bio_hot`) : la fiche garde une bio
    factuelle, le futur moteur de recommandation a sa matière — texte
    pour l'humain, `reco_data` (JSON) pour l'algorithme. Le LLM rédige
    à partir des données calculées, il n'invente pas."""
    if not ctx.settings.get("generateBioHot", True):
        return
    cf = fiche.get("custom_fields") or {}
    if cf.get("bio_hot") and not force:
        return                                  # déjà générée
    ai = ctx.ai_for("biohot")
    if not ai:
        return                                  # aucune IA configurée
    stats = stats_collection(ctx, fiche)
    matiere = {
        "position": cf.get("position"),
        # La valeur ARBITRÉE prime sur le champ hérité d'un import :
        # sur cette collection, 50 fiches portaient un « sexe_type »
        # contredit par les sources, et c'est lui que le modèle
        # reprenait — la contradiction se retrouvait alors affirmée
        # dans un texte en apparence sûr de lui.
        "sexe": f"{cf.get('sexe_cm', '')} cm "
                f"{fiche.get('circumcised') or cf.get('sexe_type') or ''}"
                .strip(),
        "analyse_perso": cf.get("analyse"),
        "compatibilite": cf.get("compatibilite"),
        "mensurations": cf.get("mensurations"),
        "dans_la_collection": stats,
        "sources_externes": {s: {k: v for k, v in d.items()
                                 if k != "bio"}
                             for s, d in raw.items()},
    }
    provider, model, key = ai
    # Instructions : réglage biohotPrompt s'il est renseigné, sinon le
    # défaut embarqué. Température : biohotTemperature (défaut 0.7).
    gabarit = prompt_biohot(ctx, fiche)
    try:
        temp = float(str(ctx.settings.get("biohotTemperature")
                         or "0.7").replace(",", "."))
    except (TypeError, ValueError):
        temp = 0.7
    temp = min(max(temp, 0.0), 1.5)
    # L'intitulé des données suit la langue lui aussi : « DONNÉES »
    # au milieu d'un prompt néerlandais tire le modèle vers le
    # français.
    prompt = (gabarit.replace("{nom}", fiche["name"])
              + "\n\n" + ctx.t("prompt_donnees") + "\n"
              + json.dumps(matiere, ensure_ascii=False)[:2200])
    # Sources inchangées depuis la dernière génération : le texte
    # existant vaut celui qu'on paierait à nouveau. `force=True`
    # (régénération demandée) passe outre.
    if not force and texte_a_jour(fiche, "biohot", prompt, "bio_hot"):
        log.debug(f"bio hot déjà à jour pour {fiche.get('name')} — "
                  f"appel évité")
        _LLM["evites"] = _LLM.get("evites", 0) + 1
        return
    texte = _appel_llm(provider, model, key, prompt, temperature=temp,
                       reglages=ctx.settings,
                       budget=BUDGETS["biohot"])
    # Ce que le modèle apporte de son propre savoir est ISOLÉ avant
    # tout contrôle : le vérifier contre les données n'aurait pas de
    # sens, puisque son intérêt est précisément de les dépasser. Il
    # est rangé à part, marqué non vérifié, et le lecteur tranche.
    apport = ""
    if texte:
        texte, apport = separer_apport(texte)
    # Le prompt interdit d'inventer un nom propre dans le TEXTE DE
    # BASE ; le modèle le fait quand même — « Titan Men » sur une
    # fiche qui n'en porte aucun. Une consigne ne suffit pas : un nom
    # plausible est ce qu'un modèle produit le mieux.
    if texte and not noms_verifies(texte, _noms_fournis(matiere)):
        log.debug(f"bio hot refusée pour {fiche.get('name')} : "
                  f"nom propre non fourni")
        return
    if not texte:
        # La fiche porte la RAISON de l'absence de bio hot : l'agent ne
        # laisse pas l'utilisateur devant un champ vide inexpliqué.
        motif = (_LLM.get("dernier_msg")
                 or (f"générations en pause jusqu'au "
                     f"{_pause_llm_active()}"
                     if _pause_llm_active() else "IA indisponible"))
        try:
            ctx.stash.update_performer({
                "id": fiche["id"],
                "custom_fields": {"partial": {
                    "enrich_ia": ctx.t(
                        "bio_hot_echec", motif=motif,
                        date=_date_auj.today().isoformat())}}})
        except Exception as exc:
            log.debug(f"update_performer : {exc}")
        return
    reco = {"partenaires": [n for n, _ in stats.get("partenaires", [])],
            "studios": [n for n, _ in stats.get("studios", [])],
            "tags": stats.get("tags", []),
            "scenes": stats.get("scenes", 0)}
    ctx.stash.update_performer({
        "id": fiche["id"],
        "custom_fields": {"partial": marquer_empreinte({
            "bio_hot": texte[:600],
            "reco_data": json.dumps(reco, ensure_ascii=False)[:600],
            # L'explication d'échec éventuelle n'a plus lieu d'être
            "enrich_ia": ""}, "biohot", prompt)}})
    # Rangé APRÈS l'écriture de la bio : c'est un champ distinct, que
    # le lecteur peut lire, vérifier et supprimer d'un geste. Le
    # mêler à la biographie le rendrait invérifiable.
    _ranger_apport(ctx, "performer", fiche["id"], apport)
    log.info(f"  bio hot générée pour {fiche['name']} "
             f"({stats.get('scenes', 0)} scène(s), "
             f"{len(stats.get('partenaires', []))} partenaire(s))"
             + (" · un apport non vérifié" if apport else ""))




def deduire_role(ctx, fiche: dict, evidences: str):
    """(dict, citation) ou (None, motif) — rôle mentionné dans la
    documentation d'un interprète.

    Aucune source ne fournit ce champ ; il ne peut venir que d'une
    mention en toutes lettres dans un texte déjà collecté. Le modèle
    n'est pas là pour deviner mais pour LIRE : c'est pourquoi il doit
    citer le passage, et qu'une réponse sans citation est écartée."""
    ai = ctx.ai_for("bio")
    if not ai:
        return None, "aucune IA configurée"
    provider, modele, cle = ai
    prompt = (ctx.t("prompt_roles") + "\n\n"
              + ctx.t("prompt_donnees") + "\n"
              + evidences[:2500])
    brut = _appel_llm(provider, modele, cle, prompt, temperature=0.0,
                      reglages=ctx.settings, budget=200)
    if not brut:
        return None, "pas de réponse"
    try:
        texte = brut.strip()
        texte = texte[texte.find("{"):texte.rfind("}") + 1]
        d = json.loads(texte)
    except (ValueError, IndexError):
        log.debug(f"réponse illisible pour {fiche.get('name')} : "
                  f"{brut[:80]}")
        return None, "réponse illisible"

    position = d.get("position") or None
    pouvoir = d.get("pouvoir") or None
    citation = (d.get("citation") or "").strip()
    try:
        confiance = float(d.get("confiance") or 0)
    except (TypeError, ValueError):
        confiance = 0.0

    if not position and not pouvoir:
        return None, "rien d'explicite"
    # Sans passage cité, rien ne distingue une lecture d'une invention.
    if not citation or citation.lower() in ("null", "none", "aucun"):
        return None, "aucune citation à l'appui"
    if confiance < 0.7:
        return None, f"confiance insuffisante ({confiance:.1f})"
    # Le modèle doit citer un passage RÉELLEMENT présent : c'est le
    # seul garde-fou vérifiable contre une citation fabriquée.
    reduit = re.sub(r"[^a-zà-ÿ0-9]", "", citation.lower())[:40]
    source = re.sub(r"[^a-zà-ÿ0-9]", "", evidences.lower())
    if reduit and reduit not in source:
        return None, "citation absente de la documentation"

    out = {}
    if position in ("actif", "passif", "versatile"):
        out["position"] = position
    if pouvoir in ("dominant", "soumis", "permutant"):
        out["pouvoir"] = pouvoir
    if not out:
        return None, "valeurs hors vocabulaire"
    return out, citation


def synth_bio(ctx, nom: str, raw: dict):
    bios = {s: d["bio"] for s, d in raw.items() if d.get("bio")}
    if not bios:
        return None
    ai = ctx.ai_for("bio")
    if ai:
        provider, model, key = ai
        prompt = (ctx.t("prompt_bio")
                  .replace("{nom}", nom)
                  .replace("{langue}", ctx.langue())
                  .replace("{donnees}",
                           json.dumps(raw, ensure_ascii=False)[:2000]))
        bio = _appel_llm(provider, model, key, prompt,
                        reglages=ctx.settings,
                         budget=BUDGETS["bio"])
        if bio:
            return (bio, f"llm/{provider}",
                    sources.SOURCE_WEIGHTS.get("llm", 0.75),
                    "synthèse IA de : " + ", ".join(sorted(bios)))
    best = max(bios, key=lambda s: sources.SOURCE_WEIGHTS.get(s, 0.4))
    return (bios[best], best,
            sources.SOURCE_WEIGHTS.get(best, POIDS_DEFAUT),
            "source retenue : " + best)


def synth_synopsis(ctx, titre: str, raw: dict):
    """Synopsis FACTUEL en français, synthèse des descriptions des
    sources. Sans IA configurée : description de la meilleure source
    (souvent en anglais)."""
    descs = {s: d["details"] for s, d in raw.items() if d.get("details")}
    if not descs:
        return None
    ai = ctx.ai_for("synopsis")
    if ai:
        provider, model, key = ai
        prompt = (ctx.t("prompt_synopsis")
                  .replace("{nom}", titre)
                  .replace("{langue}", ctx.langue())
                  .replace("{donnees}",
                           json.dumps(descs,
                                      ensure_ascii=False)[:2500]))
        texte = _appel_llm(provider, model, key, prompt,
                        reglages=ctx.settings,
                         budget=BUDGETS["synopsis"])
        if texte:
            return texte[:800], "llm/" + provider
    best = max(descs, key=lambda s: sources.SOURCE_WEIGHTS.get(s, 0.4))
    return descs[best][:800], best


def _bio_studio(ctx, nom: str, raw: dict, stats: dict):
    """Bio factuelle française du studio : sources + ce que la
    collection en montre. Sans IA : meilleure bio source brute."""
    bios = {s: d["bio"] for s, d in raw.items() if d.get("bio")}
    ai = ctx.ai_for("bio")
    if ai and (bios or stats.get("scenes")):
        provider, model, key = ai
        matiere = {"sources": bios,
                   "dans_la_collection": stats}
        prompt = (ctx.t("prompt_bio_studio")
                  .replace("{nom}", nom)
                  .replace("{langue}", ctx.langue())
                  .replace("{donnees}",
                           json.dumps(matiere,
                                      ensure_ascii=False)[:2200]))
        texte = _appel_llm(provider, model, key, prompt,
                        reglages=ctx.settings,
                         budget=BUDGETS["studio"])
        if texte:
            return texte[:700], "llm/" + provider
    if bios:
        best = max(bios, key=lambda s: sources.SOURCE_WEIGHTS.get(s, 0.4))
        return bios[best][:700], best
    return None

def generer_apercu(ctx):
    """Génère un texte pour UNE fiche et le dépose sans l'appliquer.

    Le texte va dans `enrich_apercu`, où le panneau de la fiche le
    lit. Rien n'est écrit sur le champ visible : un texte généré
    remplace un texte existant, et le montrer avant permet de
    refuser.

    Arguments : performer_id, studio_id ou scene_id.
    """
    args = getattr(ctx, "args", None) or {}
    for cle, genre in (("performer_id", "performer"),
                       ("studio_id", "studio"),
                       ("scene_id", "scene")):
        ident = str(args.get(cle) or "").strip()
        if ident:
            break
    else:
        log.warning("generer_apercu : aucun identifiant.")
        return

    lire = {"performer": ctx.stash.find_performer,
            "studio": ctx.stash.find_studio,
            "scene": ctx.stash.find_scene}[genre]
    try:
        fiche = lire(ident)
    except Exception as exc:
        log.warning(f"fiche {ident} illisible : {str(exc)[:70]}")
        return
    if not fiche:
        log.warning(f"fiche {ident} introuvable.")
        return

    # Chaque famille a son texte : une biographie n'est pas un
    # synopsis, et le même prompt pour les trois produirait trois
    # textes également inadaptés.
    usage = {"performer": "biohot", "studio": "bio",
             "scene": "synopsis"}[genre]
    if not ctx.ai_for(usage):
        log.warning("Aucun modèle configuré : renseignez « Modèle par "
                    "défaut » dans les réglages du plugin.")
        return

    texte = _texte_pour(ctx, genre, fiche, usage)
    if not texte:
        log.warning("Le modèle n'a rien produit.")
        return

    # Les mêmes garde-fous que la génération en lot : un contrôle qui
    # ne couvre qu'un chemin sur deux ne protège de rien, et l'aperçu
    # est justement celui qu'on lit de près.
    texte, apport = separer_apport(texte)
    # Comparer aux seules données de la fiche ferait refuser un studio
    # pourtant présent dans la collection : le contrôle porte sur ce
    # qui a été TRANSMIS.
    if not noms_verifies(texte,
                         _noms_fournis(_matiere_fiche(ctx, genre,
                                                      fiche))):
        log.warning("Texte refusé : il nomme un studio ou une "
                    "personne absents des données de la fiche.")
        return
    _ranger_apport(ctx, genre, ident, apport)

    log.info(f"Aperçu généré ({len(texte)} caractères) — rien n'a été "
             f"écrit sur la fiche.")
    log.info(texte)
    ecrire = {"performer": "update_performer",
              "studio": "update_studio",
              "scene": "update_scene"}[genre]
    try:
        getattr(ctx.stash, ecrire)({
            "id": ident,
            "custom_fields": {"partial": {"enrich_apercu": texte}}})
    except Exception as exc:
        log.warning(f"aperçu non déposé : {str(exc)[:70]}")


def _matiere_fiche(ctx, genre: str, fiche: dict) -> dict:
    """La matière transmise au modèle pour cette fiche.

    C'est la MÊME que celle de la génération en lot : deux matières
    différentes produiraient deux textes différents, et l'aperçu
    serait menteur — il montrerait autre chose que ce qui sera écrit.
    """
    details = str(fiche.get("details") or "").strip()
    matiere = {"sources_externes": {"fiche": {"bio": details,
                                              "details": details}}}
    if genre == "performer":
        # Sans les statistiques, le modèle n'a AUCUN studio à citer :
        # il en invente, et ce n'est pas un penchant mais un manque.
        try:
            matiere["dans_la_collection"] = stats_collection(ctx,
                                                             fiche)
        except Exception as exc:
            log.debug(f"stats indisponibles : {str(exc)[:70]}")
            matiere["dans_la_collection"] = {}
        cf = fiche.get("custom_fields") or {}
        for cle in ("position", "sexe_cm", "sexe_type", "analyse",
                    "mensurations"):
            if cf.get(cle):
                matiere[cle] = cf[cle]
    return matiere


def _texte_pour(ctx, genre: str, fiche: dict, usage: str):
    """Le texte qu'un modèle produit pour cette fiche, ou None.

    Les fonctions de génération existantes sont réemployées telles
    quelles : en écrire une quatrième ferait qu'un texte généré depuis
    la fiche diffère de celui généré en lot, et l'aperçu serait
    menteur.

    Elles attendent les données des sources ; ici, la fiche ELLE-MÊME
    fait office de source, puisque c'est ce dont l'utilisateur
    dispose.
    """
    nom = fiche.get("name") or fiche.get("title") or ""
    details = str(fiche.get("details") or "").strip()
    raw = {"fiche": {"bio": details, "details": details}}

    if genre == "performer":
        # generer_bio_hot écrit elle-même : la simulation l'en
        # empêche, et le texte revient par le journal.
        return _biohot_sans_ecrire(ctx, fiche, raw)
    if genre == "studio":
        return synth_bio(ctx, nom, raw)
    return synth_synopsis(ctx, nom, raw)


def _biohot_sans_ecrire(ctx, fiche: dict, raw: dict):
    """La présentation « hot », produite sans toucher à la fiche.

    `generer_bio_hot` applique son résultat : l'appeler pour un
    aperçu écrirait ce qu'on voulait montrer avant d'écrire.
    """
    ai = ctx.ai_for("biohot")
    if not ai:
        return None
    provider, model, key = ai
    prompt = prompt_biohot(ctx, fiche).format(
        nom=fiche.get("name") or "", langue=ctx.lang())
    # La MÊME matière que la génération en lot : sans les studios de
    # la collection, le modèle en invente faute d'en avoir.
    prompt += ("\n\n" + json.dumps(
        _matiere_fiche(ctx, "performer", fiche),
        ensure_ascii=False)[:2200])
    # La température vient du même réglage que la génération en lot :
    # un aperçu produit à une autre température serait menteur.
    try:
        temp = float(str(ctx.settings.get("biohotTemperature")
                         or 0.7))
    except (TypeError, ValueError):
        temp = 0.7
    return _appel_llm(provider, model, key, prompt, temperature=temp,
                      reglages=ctx.settings, budget=BUDGETS["biohot"])
