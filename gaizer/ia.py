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
BUDGETS = {"bio": 220, "synopsis": 150, "studio": 170, "biohot": 260}


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
            texte = llm.lire_reponse(conf, r.read())[:480]
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

def prompt_biohot(ctx) -> str:
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
    return gabarit.replace("{langue}", ctx.langue())


PROMPT_BIOHOT_DEFAUT = (
    "Rédige en {langue} la bio « hot » de l'acteur porno gay '{nom}' "
    "pour une médiathèque adulte privée. Ton direct et cru assumé, "
    "3 à 4 phrases (450 caractères max) : son style de baise, sa "
    "position, son matos, ses partenaires et studios récurrents dans "
    "la collection. RÈGLE ABSOLUE : appuie-toi uniquement sur les "
    "données ci-dessous ; ne déduis NI pratique (raw, fetish…) NI "
    "position NI trait qui n'y figure pas explicitement. Si la "
    "matière est maigre, fais court plutôt que d'inventer. Réponds "
    "uniquement la bio.")


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
    gabarit = prompt_biohot(ctx)
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
    log.info(f"  bio hot générée pour {fiche['name']} "
             f"({stats.get('scenes', 0)} scène(s), "
             f"{len(stats.get('partenaires', []))} partenaire(s))")




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
