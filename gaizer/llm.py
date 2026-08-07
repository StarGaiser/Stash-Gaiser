# -*- coding: utf-8 -*-
"""
llm.py — accès aux modèles de langage, quels qu'ils soient.

Tout fournisseur exposant une API de type « chat completions » est
utilisable sans toucher au code : les fournisseurs courants sont
prédéfinis, et le fichier `llm_providers.yml` posé à côté du plugin
permet d'en ajouter ou d'en modifier.

Format d'une entrée :

    monfournisseur:
      url: https://api.exemple.com/v1/chat/completions
      model: nom-du-modele-par-defaut
      auth: bearer          # bearer | x-api-key | query | none
      format: openai        # openai | anthropic | ollama
      key_setting: monfournisseurApiKey   # réglage Stash porteur de
                                          # la clé (facultatif)
      headers:              # en-têtes additionnels (facultatif)
        HTTP-Referer: https://exemple

La clé d'API n'est JAMAIS écrite dans ce fichier : elle vit dans les
réglages du plugin (`key_setting`, sinon `llmApiKey` par défaut), donc
dans la base de Stash et non sur le disque en clair.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

# Fournisseurs prédéfinis. « format » décrit la forme de la réponse :
# la grande majorité des services suivent le schéma OpenAI.
DEFAUTS = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini", "auth": "bearer", "format": "openai",
        "key_setting": "openaiApiKey"},
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-large-latest", "auth": "bearer",
        "format": "openai", "key_setting": "mistralApiKey"},
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "model": "claude-sonnet-4-20250514", "auth": "x-api-key",
        "format": "anthropic", "key_setting": "anthropicApiKey",
        "headers": {"anthropic-version": "2023-06-01"}},
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "model": "meta-llama/llama-3.3-70b-instruct",
        "auth": "bearer", "format": "openai",
        "key_setting": "openrouterApiKey",
        "headers": {"X-Title": "Stash Gaizer"}},
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile", "auth": "bearer",
        "format": "openai", "key_setting": "groqApiKey"},
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat", "auth": "bearer",
        "format": "openai", "key_setting": "deepseekApiKey"},
    "together": {
        "url": "https://api.together.xyz/v1/chat/completions",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "auth": "bearer", "format": "openai",
        "key_setting": "togetherApiKey"},
    "perplexity": {
        "url": "https://api.perplexity.ai/chat/completions",
        "model": "sonar", "auth": "bearer", "format": "openai",
        "key_setting": "perplexityApiKey"},
    "google": {
        "url": "https://generativelanguage.googleapis.com/v1beta/"
               "openai/chat/completions",
        "model": "gemini-2.0-flash", "auth": "bearer",
        "format": "openai", "key_setting": "googleApiKey"},
    "xai": {
        "url": "https://api.x.ai/v1/chat/completions",
        "model": "grok-2-latest", "auth": "bearer",
        "format": "openai", "key_setting": "xaiApiKey"},
    # --- exécution locale, sans clé ---
    "ollama": {
        "url": "http://localhost:11434/v1/chat/completions",
        "model": "llama3.2", "auth": "none", "format": "openai",
        "url_setting": "ollamaUrl"},
    "lmstudio": {
        "url": "http://localhost:1234/v1/chat/completions",
        "model": "local-model", "auth": "none", "format": "openai",
        "url_setting": "lmstudioUrl"},
    "llamacpp": {
        "url": "http://localhost:8080/v1/chat/completions",
        "model": "local-model", "auth": "none", "format": "openai",
        "url_setting": "llamacppUrl"},
    "vllm": {
        "url": "http://localhost:8000/v1/chat/completions",
        "model": "local-model", "auth": "none", "format": "openai",
        "url_setting": "vllmUrl"},
}

FICHIER = Path(__file__).resolve().parent / "llm_providers.yml"

GABARIT = """# llm_providers.yml — fournisseurs de modèles de langage.
#
# Ce fichier est FACULTATIF : les fournisseurs courants sont déjà
# connus du plugin (openai, mistral, anthropic, openrouter, groq,
# deepseek, together, perplexity, google, xai, ollama, lmstudio,
# llamacpp, vllm). N'écrire ici que pour en AJOUTER un ou en modifier
# un existant — la fusion se fait entrée par entrée.
#
# N'y mettez JAMAIS de clé d'API : elle se saisit dans les réglages du
# plugin (champ indiqué par key_setting, sinon « llmApiKey »).
#
# Exemple — un service compatible OpenAI :
#
# monservice:
#   url: https://api.monservice.com/v1/chat/completions
#   model: mon-modele
#   auth: bearer          # bearer | x-api-key | query | none
#   format: openai        # openai | anthropic
#   key_setting: monserviceApiKey
#   headers:
#     X-Extra: valeur
#
# Exemple — un modèle local déjà lancé sur le réseau :
#
# atelier:
#   url: http://192.168.1.40:11434/v1/chat/completions
#   model: mixtral
#   auth: none
"""


def charger(dossier=None) -> dict:
    """Fournisseurs prédéfinis, complétés par llm_providers.yml."""
    table = {k: dict(v) for k, v in DEFAUTS.items()}
    chemin = Path(dossier) / "llm_providers.yml" if dossier else FICHIER
    if not chemin.exists():
        return table
    try:
        import yaml
        perso = yaml.safe_load(chemin.read_text(encoding="utf-8")) or {}
    except Exception:
        return table
    if not isinstance(perso, dict):
        return table
    for nom, conf in perso.items():
        if not isinstance(conf, dict):
            continue
        base = table.get(str(nom).lower(), {})
        base.update({k: v for k, v in conf.items() if v is not None})
        table[str(nom).lower()] = base
    return table


def creer_gabarit(dossier=None) -> bool:
    """Dépose le fichier commenté s'il n'existe pas encore."""
    chemin = Path(dossier) / "llm_providers.yml" if dossier else FICHIER
    if chemin.exists():
        return False
    try:
        chemin.write_text(GABARIT, encoding="utf-8")
        return True
    except Exception:
        return False


def cle_pour(conf: dict, reglages: dict) -> str:
    """Clé d'API du fournisseur : réglage dédié s'il est renseigné,
    sinon le réglage générique `llmApiKey`."""
    nom = conf.get("key_setting")
    if nom:
        valeur = str((reglages or {}).get(nom) or "").strip()
        if valeur:
            return valeur
    return str((reglages or {}).get("llmApiKey") or "").strip()


def url_pour(conf: dict, reglages: dict) -> str:
    """Adresse du service : réglage dédié (utile pour les modèles
    locaux déplacés sur le réseau), sinon celle du fournisseur."""
    nom = conf.get("url_setting")
    if nom:
        valeur = str((reglages or {}).get(nom) or "").strip()
        if valeur:
            if "/chat/completions" not in valeur:
                valeur = valeur.rstrip("/") + "/v1/chat/completions"
            return valeur
    return conf.get("url") or ""


def construire_requete(conf: dict, url: str, cle: str, modele: str,
                       prompt: str, temperature: float,
                       max_tokens: int = 260):
    """(urllib.Request) prête à être envoyée, selon le format."""
    entetes = {"Content-Type": "application/json"}
    entetes.update({str(k): str(v)
                    for k, v in (conf.get("headers") or {}).items()})
    auth = (conf.get("auth") or "bearer").lower()
    if cle and auth == "bearer":
        entetes["Authorization"] = f"Bearer {cle}"
    elif cle and auth == "x-api-key":
        entetes["x-api-key"] = cle
    elif cle and auth == "query":
        url = f"{url}{'&' if '?' in url else '?'}key={cle}"

    if (conf.get("format") or "openai").lower() == "anthropic":
        corps = {"model": modele, "max_tokens": max_tokens,
                 "temperature": temperature,
                 "messages": [{"role": "user", "content": prompt}]}
    else:
        corps = {"model": modele, "max_tokens": max_tokens,
                 "temperature": temperature,
                 "messages": [{"role": "user", "content": prompt}]}
    return urllib.request.Request(
        url, data=json.dumps(corps).encode("utf-8"), headers=entetes)


def lire_reponse(conf: dict, brut: bytes) -> str:
    """Texte produit, quel que soit le format de la réponse."""
    d = json.loads(brut)
    fmt = (conf.get("format") or "openai").lower()
    if fmt == "anthropic":
        blocs = d.get("content") or []
        return "".join(b.get("text", "") for b in blocs
                       if isinstance(b, dict)).strip()
    choix = (d.get("choices") or [{}])[0]
    msg = choix.get("message") or {}
    return str(msg.get("content") or choix.get("text") or "").strip()


def besoin_de_cle(conf: dict) -> bool:
    return (conf.get("auth") or "bearer").lower() != "none"


def liste_lisible(table: dict) -> str:
    distants = sorted(k for k, v in table.items() if besoin_de_cle(v))
    locaux = sorted(k for k, v in table.items() if not besoin_de_cle(v))
    return (f"en ligne : {', '.join(distants)} · "
            f"local (sans clé) : {', '.join(locaux)}")
