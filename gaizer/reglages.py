# -*- coding: utf-8 -*-
"""
Emporter ses réglages.

Stash n'offre rien pour cela : `exportObjects` traite les scènes, les
interprètes et les studios ; `backupDatabase` copie la base entière.
Aucun des deux ne touche aux réglages d'un plugin, qui vivent dans une
table à part.

Or ils sont nombreux, et plusieurs demandent du tâtonnement : le
prompt, la température, les seuils, le choix du modèle. Les reperdre
en changeant de machine, ou après qu'un outil tiers a écrasé la table,
coûte des heures.

Une copie automatique existait déjà dans l'état du plugin, mais elle
est invisible : elle vit dans un fichier que l'utilisateur ne voit pas
et ne peut pas emporter.
"""

from __future__ import annotations

import json

from stashapi import log

import noyau

# Ce que le format garantit. Un fichier d'une version inconnue est
# refusé plutôt que lu de travers.
VERSION = 1


def exporter(ctx) -> str:
    """Les réglages, en JSON, sans aucun secret.

    Une clé d'API dans un fichier qu'on transporte, qu'on colle dans
    un ticket ou qu'on pousse sur un dépôt est un incident. Seule leur
    PRÉSENCE est notée, pour que l'import puisse dire ce qu'il reste à
    ressaisir — sans quoi l'utilisateur découvrirait le manque au
    premier appel qui échoue.
    """
    courant = ctx.settings or {}
    gardes = {k: v for k, v in courant.items()
              if not noyau.valeur_vide(v) and not noyau.est_secret(k)}
    secrets = sorted(k for k, v in courant.items()
                     if not noyau.valeur_vide(v)
                     and noyau.est_secret(k))
    return json.dumps({
        "format": "gaizer-reglages",
        "version": VERSION,
        "reglages": gardes,
        "secrets_a_ressaisir": secrets,
    }, ensure_ascii=False, indent=1, sort_keys=True)


def importer(ctx, brut: str):
    """Pose les réglages d'un export. Rend (posés, écrasés, secrets).

    COMPLÈTE, ne détruit pas : `configurePlugin` remplace la table
    entière, donc elle est relue avant d'être écrite — sans quoi
    l'import effacerait tout ce que le fichier ne contient pas, à
    commencer par les clés d'API.

    Ce qui est écrasé est RAPPORTÉ : remplacer un réglage courant par
    un ancien sans le dire ferait perdre un ajustement qu'on croyait
    fait.
    """
    try:
        d = json.loads(str(brut or ""))
    except (ValueError, TypeError) as exc:
        log.warning(f"fichier illisible : {str(exc)[:70]}")
        return [], [], []
    if not isinstance(d, dict):
        log.warning("le fichier ne contient pas un objet.")
        return [], [], []
    if int(d.get("version") or 0) != VERSION:
        log.warning(f"version {d.get('version')!r} inconnue — attendu "
                    f"{VERSION}. Rien n'a été touché.")
        return [], [], []

    venus = d.get("reglages")
    if not isinstance(venus, dict):
        log.warning("aucun réglage dans ce fichier.")
        return [], [], []

    connus = _reglages_connus()
    courant = ctx.settings or {}
    poses, ecrases = [], []
    a_ecrire = {}

    for cle, valeur in venus.items():
        # Un réglage inconnu vient d'une version future ou d'une
        # faute de frappe : le poser polluerait la table.
        if connus and cle not in connus:
            log.debug(f"réglage inconnu ignoré : {cle}")
            continue
        # Un fichier d'une version antérieure, ou trafiqué, pourrait
        # porter un secret : l'accepter le ferait entrer sans
        # contrôle.
        if noyau.est_secret(cle):
            log.warning(f"secret refusé dans un import : {cle}")
            continue
        actuel = courant.get(cle)
        if str(actuel or "") == str(valeur or ""):
            continue
        if noyau.valeur_vide(actuel):
            poses.append(cle)
        else:
            ecrases.append(f"{cle} : {str(actuel)[:20]} → "
                           f"{str(valeur)[:20]}")
        a_ecrire[cle] = valeur

    manquants = [k for k in (d.get("secrets_a_ressaisir") or [])
                 if noyau.valeur_vide(courant.get(k))]

    if a_ecrire and not ctx.simulation():
        _ecrire(ctx, a_ecrire)
    return poses, ecrases, manquants


def _reglages_connus():
    """Les clés que le manifeste déclare, ou rien si illisible.

    Lues SANS PyYAML : le conteneur de Stash ne l'embarque pas, et le
    garde-fou contre les réglages inconnus ne s'appliquerait donc pas
    là où il compte — c'est-à-dire en production.

    Le manifeste est un YAML simple : les clés de réglages sont les
    lignes indentées de quatre espaces sous « settings: », suivies de
    deux-points.
    """
    from pathlib import Path
    try:
        f = Path(__file__).resolve().parent / "gaizer.yml"
        lignes = f.read_text(encoding="utf-8").split("\n")
    except OSError as exc:
        log.debug(f"manifeste illisible : {str(exc)[:70]}")
        return set()

    cles, dedans = set(), False
    for ligne in lignes:
        if ligne.startswith("settings:"):
            dedans = True
            continue
        if dedans:
            # Une ligne non indentée termine la section.
            if ligne.strip() and not ligne.startswith(" "):
                break
            if (ligne.startswith("  ") and not ligne.startswith("   ")
                    and ":" in ligne):
                cles.add(ligne.split(":", 1)[0].strip())
    return cles


def _ecrire(ctx, valeurs: dict) -> None:
    """Écrit en préservant ce qui n'est pas dans le fichier."""
    d = ctx.stash.call_GQL("{ configuration { plugins } }")
    table = dict((d["configuration"]["plugins"] or {}).get("gaizer")
                 or {})
    table.update(valeurs)
    ctx.stash.call_GQL(
        "mutation($i: Map!) { configurePlugin("
        'plugin_id: "gaizer", input: $i) }', {"i": table})


def exporter_reglages(ctx):
    """Écrit les réglages dans le journal, à copier.

    Le journal est le seul canal par lequel un plugin Stash rend du
    texte : écrire un fichier sur le serveur ne servirait à rien, il
    est souvent dans un conteneur auquel l'utilisateur n'a pas accès.
    """
    texte = exporter(ctx)
    n = len(json.loads(texte)["reglages"])
    secrets = json.loads(texte)["secrets_a_ressaisir"]
    log.info(f"{n} réglage(s) — copiez le bloc ci-dessous et gardez-le "
             f"hors de Stash.")
    if secrets:
        log.info(f"Aucune clé d'API n'est exportée. À ressaisir après "
                 f"import : {', '.join(secrets)}")
    for ligne in texte.split("\n"):
        log.info(ligne)


def importer_reglages(ctx):
    """Pose les réglages d'un export collé dans l'argument `fichier`.

    Simuler d'abord est le comportement prudent : l'import dit ce
    qu'il changerait sans rien écrire.
    """
    args = getattr(ctx, "args", None) or {}
    brut = str(args.get("fichier") or "").strip()
    if not brut:
        log.warning("Rien à importer : collez le contenu de l'export "
                    "dans l'argument « fichier ».")
        return

    poses, ecrases, secrets = importer(ctx, brut)
    if ctx.simulation():
        log.info("SIMULATION — rien n'a été écrit.")
    if not poses and not ecrases:
        log.info("Aucun changement : vos réglages correspondent déjà "
                 "à ce fichier.")
    if poses:
        log.info(f"{len(poses)} réglage(s) posé(s) : "
                 f"{', '.join(poses)}")
    for ligne in ecrases:
        # Remplacer un réglage courant par un ancien sans le dire
        # ferait perdre un ajustement qu'on croyait fait.
        log.info(f"  remplacé — {ligne}")
    if secrets:
        log.warning(f"Clés d'API à ressaisir dans les réglages du "
                    f"plugin : {', '.join(secrets)}")
