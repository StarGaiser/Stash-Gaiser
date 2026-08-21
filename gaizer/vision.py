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
from rapprochement import (
    _reduit,
    _studio_dans,
    malgre_erreur_de_lecture,
    par_adresse,
    par_alias,
    rapprocher_studio,
    voisin_probable,
)

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


def fournisseur_convient(ctx) -> bool:
    """Le fournisseur réglé sait-il lire une image ?

    Sans ce contrôle, l'appel part, le service refuse, et rien
    n'explique pourquoi. Le message d'erreur d'un fournisseur qui
    reçoit une image sur un modèle de texte est rarement clair."""
    ai = ctx.ai_for("vision")
    if not ai:
        return False
    conf = (ctx.fournisseurs() or {}).get(ai[0]) or {}
    return bool(conf.get("vision"))


def fournisseurs_possibles(ctx) -> list:
    """Réglages exploitables au vu de ce qui est DÉJÀ configuré.

    Suggérer un fournisseur dont la clé n'est pas renseignée
    enverrait l'utilisateur en configurer un second alors qu'il en a
    déjà un qui convient. Les services locaux échappent à la règle :
    ils ne réclament aucune clé, et ce sont les seuls qui ne
    transmettent rien à un tiers."""
    proposes = []
    for nom, conf in sorted((ctx.fournisseurs() or {}).items()):
        if not conf.get("vision"):
            continue
        reglage = conf.get("key_setting")
        local = not reglage
        renseigne = reglage and str(
            ctx.settings.get(reglage) or "").strip()
        if local or renseigne:
            proposes.append(f"{nom}:{conf.get('vision_model')}")
    return proposes


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
    # `url_sure`, appelé en tête de fonction, a filtré le schéma et
    # l'adresse : c'est le contrôle que S310 réclame, fait une seule
    # fois pour tout le plugin.
    requete = urllib.request.Request(  # noqa: S310
        url, data=json.dumps(corps).encode("utf-8"), headers=entetes)
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
def adresse_de_stash(ctx, url) -> bool:
    """L'adresse est-elle celle du Stash auquel on est connecté ?

    Le contrôle général refuse les adresses locales, et il a raison :
    une source distante ne doit pas faire interroger le réseau de
    l'utilisateur. Mais Stash se sert lui-même sur 127.0.0.1, et le
    plugin y est déjà connecté — refuser cette adresse-là reviendrait
    à ne jamais pouvoir lire une vignette.

    L'exception est ÉTROITE : seule l'adresse de la connexion établie
    au démarrage est admise. Un port voisin ne l'est pas — ce serait un
    moyen d'atteindre un autre service de la machine.
    """
    texte = str(url or "")
    if not texte.lower().startswith(("http://", "https://")):
        return False
    if noyau.url_sure(texte):
        return True
    conn = getattr(ctx, "connexion", None) or {}
    hote = str(conn.get("Host") or "").strip()
    port = str(conn.get("Port") or "").strip()
    if not hote:
        return False
    from urllib.parse import urlparse
    try:
        vue = urlparse(texte)
    except ValueError:
        return False
    if (vue.hostname or "") != hote:
        return False
    return not port or str(vue.port or "") == port


def image_exploitable(donnees) -> bool:
    """Ces octets portent-ils une image susceptible d'être lue ?

    Stash sert une ICÔNE DE REMPLACEMENT — un SVG de quelques
    centaines d'octets — quand une scène n'a pas de vignette générée.
    L'envoyer coûte un appel, produit une erreur du fournisseur, et
    n'apprend rien. Le cas n'est pas marginal : il concerne la plupart
    des scènes non identifiées, précisément celles qu'on vise.
    """
    if not donnees or len(donnees) < 2000:
        return False
    debut = donnees[:200].lstrip()
    if debut.startswith((b"<svg", b"<?xml", b"<!DOCTYPE", b"<html")):
        return False
    if b"<svg" in debut:
        return False
    # Signatures des formats que les modèles acceptent.
    return donnees[:3] == b"\xff\xd8\xff" or donnees[:8] == (
        b"\x89PNG\r\n\x1a\n") or donnees[:4] == b"RIFF" or (
        donnees[:6] in (b"GIF87a", b"GIF89a"))


def _telecharger(url, timeout=30):
    """Récupération isolée, pour être remplaçable dans les tests."""
    import urllib.request
    with urllib.request.urlopen(  # noqa: S310
            url, timeout=timeout) as reponse:
        return reponse.read()


def image_de(ctx, sc: dict):
    """Vignette d'une scène, ou None.

    L'adresse vient de Stash et n'est admise que si elle DÉSIGNE
    Stash : un fichier local ou un autre service de la machine reste
    refusé.
    """
    chemins = sc.get("paths") or {}
    url = chemins.get("screenshot") or chemins.get("preview")
    if not url or not adresse_de_stash(ctx, url):
        return None
    try:
        return _telecharger(url)
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

    if not lu:
        return None, ("aucun texte lu à l'appui — un studio annoncé "
                      "sans lecture est une déduction")
    if not studio:
        # Le modele lit « HAROKINKS.COM » mais laisse le champ studio
        # a null : il a fait son travail sans oser en tirer un nom.
        # Le texte lu EST la reponse, et la jeter revient a payer un
        # appel pour rien.
        studio = _studio_dans(lu)
        if not studio:
            return None, "aucun studio lisible"
    if confiance < 0.6:
        return None, f"confiance insuffisante ({confiance:.1f})"

    # Le nom annoncé doit se retrouver dans ce qui a été lu : seul
    # contrôle possible contre une invention.
    reduit = _reduit(studio)
    source = _reduit(" ".join(lu))
    if reduit and reduit not in source:
        return None, ("le nom annoncé ne correspond à aucun texte lu")

    return {"studio": studio, "texte_lu": lu, "confiance": confiance}, \
        f"filigrane lu ({confiance:.1f})"


# ── Tâche ────────────────────────────────────────────────────────────
def lire_vignettes(ctx, scenes=None):
    """Lit les vignettes des scènes sans studio et propose ce qu'elle
    y trouve.

    Argument `relire=1` pour reprendre des scènes déjà lues."""
    if not ctx.source_active("vision"):
        log.info("Reglage : la lecture des filigranes est desactive.")
        return
    if not autorisee(ctx):
        log.info("Lecture des vignettes désactivée. Cette tâche "
                 "envoie des IMAGES de votre médiathèque à un modèle "
                 "— y compris installé chez vous. Le réglage "
                 "« Envoyer les vignettes au modèle de vision » "
                 "l'autorise.")
        return

    ai = ctx.ai_for("vision")
    if not ai or not fournisseur_convient(ctx):
        raison = ("aucun modèle de vision configuré" if not ai
                  else f"« {ai[0]} » ne sait pas lire d'image")
        log.warning(f"{raison} (réglage « aiVision »).")
        proposes = fournisseurs_possibles(ctx)
        if proposes:
            log.info("  Exploitables avec vos réglages actuels : "
                     + " · ".join(proposes))
        else:
            log.info("  Renseigner d'abord la clé d'un fournisseur "
                     "qui lit les images, ou l'adresse d'un service "
                     "local (Ollama, LM Studio).")
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

    index, studios = {}, []
    try:
        # L'adresse et les alias sont demandes en meme temps que le
        # nom : ils offrent des rapprochements que le nom seul ne
        # permet pas, et les obtenir ne coute rien de plus.
        d = ctx.stash.call_GQL(
            "{ findStudios(filter: {per_page: -1}) { studios "
            "{ id name aliases url } } }")
        studios = d["findStudios"]["studios"]
        index = {s["name"]: s["id"] for s in studios}
    except Exception as exc:
        log.debug(f"catalogue de studios illisible : {exc}")

    lues = proposees = 0
    motifs = {}
    for i, sc in enumerate(cibles[:limite], 1):
        log.progress(i / max(1, min(len(cibles), limite)))
        image = image_de(ctx, sc)
        if not image_exploitable(image):
            # Le contrôle intervient AVANT l'appel : après, la facture
            # est due.
            cle = ("vignette non générée par Stash" if image
                   else "vignette inaccessible")
            motifs[cle] = motifs.get(cle, 0) + 1
            continue
        lu, motif = lire_vignette(ctx, image)
        lues += 1
        if not lu:
            motifs[motif] = motifs.get(motif, 0) + 1
            # Une PANNE n'est pas une absence de filigrane. Marquer la
            # scene la condamnerait : elle ne serait jamais reprise,
            # et une coupure d'une minute suffirait a perdre tout un
            # lot. Une vignette sans texte, elle, n'en aura jamais.
            if motif not in ("pas de réponse", "refus du fournisseur",
                             "réponse illisible"):
                _marquer_lue(ctx, sc)
            continue

        # Du plus sur au moins sur. L'ADRESSE d'abord : un filigrane
        # est souvent une URL, et une URL ne souffre pas d'orthographe.
        # Puis le nom exact, puis les alias — variantes d'ecriture que
        # le studio declare lui-meme. Ces trois-la sont « certaines ».
        # Ensuite seulement les approximations : nom contenu dans ce
        # qui a ete lu, puis erreur de lecture a un caractere pres.
        ident = (par_adresse(" ".join(lu["texte_lu"]), studios)
                 or rapprocher_studio(lu["studio"], index)
                 or par_alias(lu["studio"], studios))
        voisin = None
        if not ident:
            voisin = (voisin_probable(lu["studio"], index)
                      or malgre_erreur_de_lecture(lu["studio"], index))
        # Le texte lu n'est PAS journalisé en entier : il peut
        # contenir un nom, une adresse, et le journal du serveur est
        # lisible par d'autres.
        if ident:
            etat = "→ studio connu"
        elif voisin:
            nom_voisin = next((n for n, i in index.items()
                               if i == voisin), "")
            etat = f"→ proche de « {nom_voisin[:26]} » (à confirmer)"
        else:
            etat = "(hors catalogue)"
        log.info(f"  scène {sc['id']} : « {lu['studio'][:30]} » {etat}")
        _proposer(ctx, sc, lu, ident or voisin,
                  certain=bool(ident))
        proposees += 1

    log.info(f"{lues} vignette(s) lues, {proposees} proposition(s).")
    if motifs.get("vignette non générée par Stash"):
        log.info("  Ces scènes n'ont pas de vignette : Stash sert une "
                 "icône à la place. Les générer d'abord — Tasks → "
                 "Generate → Sprites/Previews — puis relancer.")
    if motifs:
        log.info("  sans résultat : "
                 + " · ".join(f"{k} ({n})" for k, n in
                              sorted(motifs.items(),
                                     key=lambda x: -x[1])))
    if proposees:
        log.info("  Rien n'a été écrit sur les scènes : une lecture de "
                 "filigrane est une hypothèse. Les propositions "
                 "figurent dans le champ « enrich_vision ».")


def appliquer_vision(ctx):
    """Applique les studios lus sur les vignettes.

    Une proposition qui n'est jamais reprise est un cul-de-sac :
    l'utilisateur voit un studio reconnu et la scene reste vide. Une
    source qui propose doit avoir sa source qui applique.

    Seules les correspondances CERTAINES — adresse, nom exact, alias —
    sont appliquees d'office. Les rattrapages d'erreur de lecture
    demandent un regard : les appliquer effacerait la distinction
    entre certain et probable. Argument `incertaines=1` pour les
    inclure.
    """
    if not ctx.source_active("vision"):
        log.info("Reglage : la lecture des filigranes est desactivee.")
        return
    incertaines = str((getattr(ctx, "args", None) or {})
                      .get("incertaines") or "").strip()
    poses = attente = 0
    for sc in ctx.stash.find_scenes():
        if (sc.get("studio") or {}).get("id"):
            continue
        brut = (sc.get("custom_fields") or {}).get(
            "enrich_vision_studio")
        if not brut:
            continue
        try:
            d = json.loads(brut)
        except (ValueError, TypeError) as exc:
            log.debug(f"vignette non exploitable : {str(exc)[:70]}")
            continue
        ident = d.get("studio_id")
        if not ident:
            continue
        if not d.get("certain") and not incertaines:
            attente += 1
            continue
        try:
            ctx.stash.update_scene({
                "id": sc["id"],
                "studio_id": ident,
                "custom_fields": {"partial": {
                    "enrich_sources": f"studio: vision "
                                      f"({str(d.get('studio_lu'))[:30]})"}}})
            poses += 1
        except Exception as exc:
            log.debug(f"scene {sc['id']} : {str(exc)[:70]}")
    log.info(f"{poses} studio(s) appliques depuis les vignettes.")
    if attente:
        log.info(f"  {attente} proposition(s) a confirmer : relancer "
                 f"avec « incertaines=1 » pour les appliquer aussi.")


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


def _proposer(ctx, sc, lu, ident, certain=True):
    """Enregistre la lecture SANS toucher au studio de la scène.

    Une lecture de filigrane n'est pas une source documentaire : elle
    propose, l'utilisateur tranche.
    """
    proposition = {
        "studio_lu": lu["studio"],
        "studio_id": ident,
        # Un voisin probable n'est pas une correspondance : le dire,
        # sans quoi l'utilisateur croirait la valeur établie.
        "certain": certain,
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
