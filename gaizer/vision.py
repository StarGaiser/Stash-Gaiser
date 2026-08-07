# -*- coding: utf-8 -*-
"""
Lecture des vignettes : ce qui est ÉCRIT sur l'image.

Une scène sans studio est difficile à enrichir : le studio est le
meilleur réducteur de candidats dont dispose le plugin, et sans lui les
scrapers dédiés ne peuvent rien. Or les vignettes portent presque
toujours un filigrane, parfois une adresse, parfois un titre incrusté.

**Ce module ne cherche jamais à identifier une personne.** Ce n'est pas
une précaution de façade : les fournisseurs commerciaux refusent de le
faire, et un modèle sommé de reconnaître quelqu'un répond soit par un
refus, soit par une invention. Poser la question serait donc au mieux
inutile, au pire dangereux. Il lit du texte — une tâche sans
restriction et bien plus fiable.

**Ce qu'il produit est une hypothèse, pas une source.** Un nom lu sur
une image se rapproche du catalogue existant, se note faiblement, et se
propose. Rien n'est écrit d'autorité.

**Et l'envoi d'images est éteint par défaut.** Le reste du plugin
transmet du texte ; une image est d'une autre nature — identifiante,
possiblement conservée par le fournisseur, et exposant des gens qui
n'ont rien demandé. L'activer est un geste conscient, quel que soit le
destinataire, y compris un modèle installé chez soi.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import date as _date_auj

from stashapi import log

import llm
import noyau

# Nom sous lequel une lecture apparaît dans la trace de provenance.
# Distinct de tout nom de source documentaire : l'utilisateur doit
# pouvoir reconnaître d'où vient la valeur.
NOM_SOURCE = "vision"

# Ce que le modèle doit rendre, et rien d'autre.
_CHAMPS = ("studio", "texte_lu", "confiance")

# Formules par lesquelles un fournisseur décline. Un refus n'est pas
# une panne : le traiter comme telle ferait réessayer indéfiniment et
# paierait des appels pour rien.
_REFUS = (
    "can't identify", "cannot identify", "can't help with identif",
    "unable to identify", "not able to identify",
    "ne peux pas identifier", "ne peux pas reconnaître",
    "i'm sorry", "je ne peux pas", "as an ai",
    # Les fournisseurs varient la formule ; le sens ne varie pas.
    "identifying individuals", "identifying people",
    "identifying real people", "identifier des personnes",
    "kann ich nicht", "no puedo identificar",
    "non posso identificare", "não posso identificar",
    "kan ik niet",
)


def autorisee(ctx) -> bool:
    """L'utilisateur a-t-il consenti à l'envoi d'images ?

    Renseigner un modèle de vision n'est PAS consentir : les deux
    réglages sont distincts, et le second doit être coché sciemment.
    Un modèle local n'y échappe pas — quelqu'un peut vouloir qu'aucune
    image ne quitte Stash, quel qu'en soit le destinataire.
    """
    return bool(ctx.settings.get("visionEnvoiImages"))


def prompt_vision(ctx) -> str:
    """Instructions de lecture, dans la langue voulue."""
    perso = str(ctx.settings.get("visionPrompt") or "").strip()
    return perso or ctx.t("prompt_vision")


# ── Appel ────────────────────────────────────────────────────────────
def _poster(url, corps, cle=None):
    """Envoi brut, isolé pour être remplaçable dans les tests."""
    import urllib.request
    if not noyau.url_sure(url):
        raise ValueError(f"adresse refusée : {str(url)[:60]}")
    entetes = {"Content-Type": "application/json"}
    if cle:
        entetes["Authorization"] = f"Bearer {cle}"
    requete = urllib.request.Request(
        url, data=json.dumps(corps).encode("utf-8"), headers=entetes)
    # noqa au point d'ouverture : `url_sure` a filtré le schéma
    # et l'adresse juste au-dessus.
    with urllib.request.urlopen(  # noqa: S310
            requete, timeout=60) as reponse:
        return reponse.read().decode("utf-8", "replace")


def _appel_vision(ctx, image: bytes, instructions: str):
    """Réponse brute du modèle, ou None.

    L'image part encodée en base64 dans une adresse de données : c'est
    la forme qu'attendent les API compatibles OpenAI, et des octets
    bruts seraient refusés sans explication utile.
    """
    ai = ctx.ai_for("vision")
    if not ai:
        return None
    fournisseur, modele, cle = ai
    # L'adresse se construit comme pour les appels de texte : même
    # table de fournisseurs, même possibilité de la surcharger pour un
    # modèle local déplacé sur le réseau.
    try:
        conf = ctx.fournisseurs().get(fournisseur)
        if not conf:
            log.warning(f"fournisseur de vision inconnu : "
                        f"{fournisseur}")
            return None
        url = llm.url_pour(conf, ctx.settings)
    except Exception as exc:
        log.debug(f"fournisseur de vision illisible : {str(exc)[:80]}")
        return None

    encodee = base64.b64encode(image).decode("ascii")
    corps = {
        "model": modele,
        "max_tokens": 300,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": instructions},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{encodee}"}},
        ]}],
    }
    try:
        brut = _poster(url, corps, cle)
        d = json.loads(brut)
        return d["choices"][0]["message"]["content"]
    except Exception as exc:
        log.debug(f"appel de vision : {str(exc)[:90]}")
        return None


# ── Image de la scène ────────────────────────────────────────────────
def image_de(ctx, sc: dict):
    """Vignette d'une scène, ou None.

    L'adresse vient de Stash, mais passe par le contrôle commun : une
    base compromise ne doit pas faire sortir le plugin vers une
    adresse locale ou un fichier.
    """
    chemins = sc.get("paths") or {}
    url = chemins.get("screenshot") or chemins.get("preview")
    if not url or not noyau.url_sure(url):
        return None
    try:
        import urllib.request
        # `url_sure` a validé l'adresse au-dessus.
        with urllib.request.urlopen(  # noqa: S310
                url, timeout=30) as reponse:
            return reponse.read()
    except Exception as exc:
        log.debug(f"vignette illisible : {str(exc)[:80]}")
        return None


# ── Lecture ──────────────────────────────────────────────────────────
def lire_vignette(ctx, image: bytes):
    """(dict, motif) ou (None, motif) — ce qui a été LU sur l'image.

    Trois refus, dans cet ordre, et chacun compte. Un studio annoncé
    sans texte lu est une déduction visuelle, donc une supposition sur
    un décor ou des personnes. Un nom qui ne se retrouve pas dans le
    texte lu est une invention. Et une confiance faible ne vaut pas
    qu'on écrive quoi que ce soit.
    """
    if not ctx.ai_for("vision"):
        return None, "aucun modèle de vision configuré"

    brut = _appel_vision(ctx, image, prompt_vision(ctx))
    if not brut:
        return None, "pas de réponse"

    # Un refus se reconnaît AVANT toute tentative de lecture : le
    # traiter comme une réponse illisible ferait réessayer, et
    # paierait des appels pour un service qui a dit non.
    bas = re.sub(r"[\u2018\u2019]", "'", str(brut)).lower()
    if any(m in bas for m in _REFUS):
        return None, "refus du fournisseur"

    try:
        texte = str(brut)
        texte = texte[texte.find("{"):texte.rfind("}") + 1]
        d = json.loads(texte)
        if not isinstance(d, dict):
            raise ValueError
    except (ValueError, IndexError):
        return None, "réponse illisible"

    studio = (d.get("studio") or "").strip() or None
    lu = [str(x) for x in (d.get("texte_lu") or []) if str(x).strip()]
    try:
        confiance = float(d.get("confiance") or 0)
    except (TypeError, ValueError):
        confiance = 0.0

    if not studio:
        return None, "aucun studio lisible"
    if not lu:
        return None, ("aucun texte lu à l'appui — un studio annoncé "
                      "sans lecture est une déduction")
    if confiance < 0.6:
        return None, f"confiance insuffisante ({confiance:.1f})"

    # Le nom annoncé doit se retrouver dans ce qui a été lu : seul
    # contrôle possible contre une invention.
    reduit = re.sub(r"[^a-z0-9]", "", studio.lower())
    source = re.sub(r"[^a-z0-9]", "", " ".join(lu).lower())
    if reduit and reduit not in source:
        return None, ("le nom annoncé ne correspond à aucun texte lu")

    return {"studio": studio, "texte_lu": lu, "confiance": confiance}, \
        f"filigrane lu ({confiance:.1f})"


def rapprocher_studio(lu, index: dict):
    """Identifiant du studio correspondant, ou None.

    Rapprochement EXACT sur forme normalisée. Un nom lu sur une image
    est déjà approximatif ; y ajouter une correspondance partielle
    attribuerait des scènes au mauvais studio, ce qu'aucun arbitrage
    ultérieur ne rattrape.
    """
    cle = re.sub(r"[^a-z0-9]", "", str(lu or "").lower())
    # « masqulin.com » et « masqulin » désignent la même chose ; le
    # suffixe de domaine n'apporte rien.
    cle = re.sub(r"(com|net|org|tv)$", "", cle)
    if len(cle) < 4:
        return None
    for nom, ident in (index or {}).items():
        nu = re.sub(r"[^a-z0-9]", "", str(nom).lower())
        nu = re.sub(r"(com|net|org|tv)$", "", nu)
        if nu == cle:
            return ident
    return None


# ── Tâche ────────────────────────────────────────────────────────────
def lire_vignettes(ctx):
    """Lit les vignettes des scènes sans studio et propose ce qu'elle
    y trouve.

    Argument `relire=1` pour reprendre des scènes déjà lues."""
    if not autorisee(ctx):
        log.info("Lecture des vignettes désactivée. Cette tâche "
                 "envoie des IMAGES de votre médiathèque à un modèle "
                 "— y compris installé chez vous. Le réglage "
                 "« Envoyer les vignettes au modèle de vision » "
                 "l'autorise.")
        return

    ai = ctx.ai_for("vision")
    if not ai:
        log.warning("aucun modèle de vision configuré (réglage "
                    "« aiVision »).")
        return
    log.info(f"Les vignettes seront envoyées à « {ai[0]} ». "
             f"Interrompre maintenant si ce n'est pas voulu.")

    relire = str((getattr(ctx, "args", None) or {})
                 .get("relire") or "").strip()
    scenes = ctx.stash.find_scenes()
    cibles = [s for s in scenes
              if not (s.get("studio") or {}).get("id")
              and (relire or not (s.get("custom_fields") or {})
                   .get("enrich_vision"))]
    limite = ctx.batch()
    log.info(f"{len(cibles)} scène(s) sans studio — lot de {limite}")

    index = {}
    try:
        d = ctx.stash.call_GQL(
            "{ findStudios(filter: {per_page: -1}) { studios "
            "{ id name } } }")
        index = {s["name"]: s["id"]
                 for s in d["findStudios"]["studios"]}
    except Exception as exc:
        log.debug(f"catalogue de studios illisible : {exc}")

    lues = proposees = 0
    motifs = {}
    for i, sc in enumerate(cibles[:limite], 1):
        image = image_de(ctx, sc)
        if not image:
            motifs["sans vignette"] = motifs.get("sans vignette", 0) + 1
            continue
        lu, motif = lire_vignette(ctx, image)
        lues += 1
        if not lu:
            motifs[motif] = motifs.get(motif, 0) + 1
            _marquer_lue(ctx, sc)
            continue

        ident = rapprocher_studio(lu["studio"], index)
        # Le texte lu n'est PAS journalisé en entier : il peut
        # contenir un nom, une adresse, et le journal du serveur est
        # lisible par d'autres.
        log.info(f"  scène {sc['id']} : « {lu['studio'][:30]} » "
                 f"{'→ studio connu' if ident else '(hors catalogue)'}")
        _proposer(ctx, sc, lu, ident)
        proposees += 1
        log.progress(i / max(1, min(len(cibles), limite)))

    log.info(f"{lues} vignette(s) lues, {proposees} proposition(s).")
    if motifs:
        log.info("  sans résultat : "
                 + " · ".join(f"{k} ({n})" for k, n in
                              sorted(motifs.items(),
                                     key=lambda x: -x[1])))
    if proposees:
        log.info("  Rien n'a été écrit sur les scènes : une lecture de "
                 "filigrane est une hypothèse. Les propositions "
                 "figurent dans le champ « enrich_vision ».")


def _marquer_lue(ctx, sc):
    """Trace de lecture : relire la même vignette produirait la même
    réponse et la même facture."""
    try:
        ctx.stash.update_scene({
            "id": sc["id"],
            "custom_fields": {"partial": {
                "enrich_vision": _date_auj.today().isoformat()}}})
    except Exception as exc:
        log.debug(f"marquage : {str(exc)[:70]}")


def _proposer(ctx, sc, lu, ident):
    """Enregistre la lecture SANS toucher au studio de la scène.

    Une lecture de filigrane n'est pas une source documentaire : elle
    propose, l'utilisateur tranche.
    """
    proposition = {
        "studio_lu": lu["studio"],
        "studio_id": ident,
        "confiance": lu["confiance"],
        "d": _date_auj.today().isoformat(),
    }
    try:
        ctx.stash.update_scene({
            "id": sc["id"],
            "custom_fields": {"partial": {
                "enrich_vision": _date_auj.today().isoformat(),
                "enrich_vision_studio": json.dumps(
                    proposition, ensure_ascii=False)}}})
    except Exception as exc:
        log.debug(f"proposition : {str(exc)[:70]}")
