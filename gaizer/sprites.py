# -*- coding: utf-8 -*-
"""
Lecture des génériques : le début et la fin de la vidéo.

La vignette d'une scène est prise au milieu : elle porte le filigrane
du studio, jamais le générique. Or Stash produit aussi un SPRITE — une
planche de cases réparties sur toute la durée — accompagné d'un fichier
VTT qui donne les coordonnées et l'horodatage de chacune.

Les premières et dernières cases contiennent ce que le milieu n'a pas :
titre d'ouverture, et surtout générique de fin où figurent les noms des
interprètes.

**Le rendement est faible, et c'est assumé.** Environ une scène sur
huit porte un générique lisible. Mais ces scènes-là ne sont atteintes
par aucun autre moyen — ni empreinte, ni nom de fichier, ni filigrane.

**Le risque est l'invention.** Une case fait 160×90 pixels ; agrandie,
elle invite le modèle à halluciner — un essai a produit un paragraphe
sur l'environnement à partir d'une image sans texte. Ce qui est retenu
doit donc RESSEMBLER à un nom, et un nom lu n'est jamais appliqué :
attribuer une scène au mauvais interprète est l'erreur qu'aucun
arbitrage ne rattrape.
"""

from __future__ import annotations

import io
import json
import re
from datetime import date as _date_auj

from stashapi import log

import vision

# Mentions qui encadrent les noms dans un générique sans en être.
_MENTIONS = (
    "starring", "featuring", "directed", "produced", "written",
    "cast", "with", "presents", "production", "camera", "editing",
    "music", "avec", "réalisation", "production", "montage",
)

# Textes lisibles qui ne sont jamais des noms.
_JAMAIS = re.compile(
    r"^(hd|4k|8k|uhd|\d{3,4}p|\d{4}|com|net|www\..*|.*\.(com|net|org|tv)"
    r"|scene\s*\d*|part\s*\d*|the end|fin|end)$", re.I)


def _pillow():
    """La bibliothèque d'images, ou None.

    Le plugin ne la réclame pas : découper une planche est la seule
    chose qui en ait besoin, et l'imposer à qui ne s'en sert pas
    serait un coût sans contrepartie.
    """
    try:
        from PIL import Image
        return Image
    except ImportError:
        return None


def disponible() -> bool:
    return _pillow() is not None


def _telecharger(url, timeout=30):
    """Isolé pour être remplaçable dans les tests."""
    return vision._telecharger(url, timeout)


# ── Découpage ────────────────────────────────────────────────────────
def cases_du_vtt(brut) -> list:
    """Coordonnées de chaque case, dans l'ordre du temps.

    Le VTT les donne explicitement. Les calculer à partir des
    dimensions de la planche supposerait une grille régulière que rien
    ne garantit.
    """
    out = []
    for m in re.finditer(r"#xywh=(\d+),(\d+),(\d+),(\d+)",
                         str(brut or "")):
        out.append(tuple(int(g) for g in m.groups()))
    return out


def cases_utiles(cases: list) -> list:
    """Les seules cases qui valent un appel.

    Lire les cent cases d'une planche coûterait cent appels pour une
    information qui tient dans deux : le générique est au début ou à
    la fin, jamais au milieu.
    """
    if not cases:
        return []
    if len(cases) <= 3:
        return list(cases)
    # La toute dernière case est souvent noire ; l'avant-dernière
    # porte plus souvent le générique.
    return [cases[0], cases[-2], cases[-1]]


def _lire_case(ctx, planche, boite):
    """Textes lus sur une case, ou liste vide."""
    Image = _pillow()
    if Image is None:
        return {"noms": [], "studio": None}
    x, y, w, h = boite
    try:
        im = Image.open(io.BytesIO(planche))
        vue = im.crop((x, y, x + w, y + h))
        # Agrandir aide la reconnaissance : 160×90 est en dessous de
        # ce que les modèles lisent confortablement.
        vue = vue.resize((w * 4, h * 4), Image.LANCZOS)
        tampon = io.BytesIO()
        vue.convert("RGB").save(tampon, "JPEG", quality=92)
    except Exception as exc:
        log.debug(f"case illisible : {str(exc)[:70]}")
        return {"noms": [], "studio": None}

    brut = vision._appel_vision(ctx, tampon.getvalue(),
                                ctx.t("prompt_generique"))
    if not brut:
        return {"noms": [], "studio": None}
    try:
        texte = str(brut)
        texte = texte[texte.find("{"):texte.rfind("}") + 1]
        d = json.loads(texte)
        # Le generique porte le studio autant que les interpretes :
        # ne lire que les noms de personnes jetterait la moitie de ce
        # que le modele a lu.
        return {"noms": [str(x) for x in (d.get("noms") or [])],
                "studio": (str(d.get("studio")).strip()
                           if d.get("studio") else None)}
    except (ValueError, IndexError, AttributeError):
        return {"noms": [], "studio": None}


# ── Ce qui ressemble à un nom ────────────────────────────────────────
def _alphabet_latin(texte: str) -> bool:
    """Le texte s'ecrit-il en alphabet latin ?

    Une case de 160x90 agrandie invite le modele a inventer, et
    l'invention se trahit souvent par un alphabet qui n'a rien a faire
    la : le generique d'un studio occidental ne s'ecrit pas en
    cyrillique. Les accents latins restent acceptes — les noms
    espagnols et portugais en portent, et les ecarter perdrait de
    vraies lectures.
    """
    for c in texte:
        if not c.isalpha():
            continue
        # Latin de base et supplements accentues.
        if not (ord(c) < 0x250 or 0x1E00 <= ord(c) <= 0x1EFF):
            return False
    return True


def noms_plausibles(textes) -> list:
    """Parmi les textes lus, ceux qui peuvent être des noms.

    Une hallucination produit des phrases ; un décor produit des mots
    isolés — une marque sur un vêtement, un panneau. Exiger deux
    parties et une longueur raisonnable écarte l'essentiel du bruit
    sans perdre les vrais noms.
    """
    # Une case de generique porte quelques noms. Une liste de quinze
    # est un signe d'invention, non une distribution nombreuse.
    if len(textes or []) > 8:
        return []
    out = []
    for brut in textes or []:
        if not isinstance(brut, str):
            continue
        texte = re.sub(r"\s+", " ", brut).strip(" .,-—:")
        if not (4 <= len(texte) <= 40):
            continue
        if _JAMAIS.match(texte):
            continue
        bas = texte.lower()
        if any(bas.startswith(m) for m in _MENTIONS):
            continue
        mots = [m for m in texte.split(" ") if len(m) > 1]
        # Un mot seul est trop ambigu : « BOXER » peut être un nom,
        # une marque ou un vêtement. Deux réduisent le hasard.
        if not (2 <= len(mots) <= 4):
            continue
        if any(any(c.isdigit() for c in m) for m in mots):
            continue
        out.append(texte)

    # Si une case mele des alphabets, elle n'est pas lue : elle est
    # inventee. Garder la moitie latine reviendrait a retenir la
    # moitie d'une hallucination.
    if any(not _alphabet_latin(x) for x in out):
        return []
    return out


def rapprocher_studio(lu, index: dict):
    """Identifiant du studio lu au generique, ou None.

    Rapprochement EXACT, comme partout : un nom lu sur une image
    agrandie ne justifie pas d'attribuer une scene a un studio voisin.
    """
    cle = re.sub(r"[^a-z0-9]", "", str(lu or "").lower())
    if len(cle) < 4:
        return None
    for nom, ident in (index or {}).items():
        if re.sub(r"[^a-z0-9]", "", str(nom).lower()) == cle:
            return ident
    return None


def rapprocher_interprete(lu, index: dict):
    """Identifiant de l'interprète, ou None.

    Rapprochement EXACT, et aucune création : un nom lu sur une image
    agrandie n'a pas la fiabilité qu'exige la création d'une fiche, et
    l'attribuer au mauvais interprète ne se rattrape pas.
    """
    cle = re.sub(r"[^a-z0-9]", "", str(lu or "").lower())
    if len(cle) < 5:
        return None
    for nom, ident in (index or {}).items():
        if re.sub(r"[^a-z0-9]", "", str(nom).lower()) == cle:
            return ident
    return None


# ── Tâche ────────────────────────────────────────────────────────────
def lire_generiques(ctx, scenes=None):
    """Lit le début et la fin des sprites des scènes sans interprète.

    Argument `relire=1` pour reprendre des scènes déjà traitées."""
    if not ctx.source_active("generiques"):
        log.info("Reglage : la lecture des generiques est desactive.")
        return
    if not vision.autorisee(ctx):
        log.info("Lecture des génériques désactivée. Cette tâche "
                 "envoie des IMAGES à un modèle. Le réglage "
                 "« Envoyer les vignettes au modèle de vision » "
                 "l'autorise.")
        return
    if not disponible():
        log.warning("Découper une planche demande Pillow, absent de "
                    "cette installation. « pip install pillow » dans "
                    "le conteneur Stash, puis relancer.")
        return
    if not ctx.ai_for("vision") or not vision.fournisseur_convient(ctx):
        log.warning("aucun modèle capable de lire une image "
                    "(réglage « aiVision »).")
        return

    relire = str((getattr(ctx, "args", None) or {})
                 .get("relire") or "").strip()
    cibles = [s for s in (scenes if scenes is not None
                          else ctx.stash.find_scenes())
              if not s.get("performers")
              and (relire or not (s.get("custom_fields") or {})
                   .get("enrich_generique_le"))]
    limite = ctx.batch()
    log.info(f"{len(cibles)} scène(s) sans interprète — lot de "
             f"{limite}")

    index, idx_studios = {}, {}
    try:
        index = {p["name"]: p["id"]
                 for p in ctx.stash.find_performers()}
    except Exception as exc:
        log.debug(f"catalogue d'interprètes illisible : {exc}")
    try:
        idx_studios = {s["name"]: s["id"]
                       for s in ctx.stash.find_studios()}
    except Exception as exc:
        log.debug(f"catalogue de studios illisible : {exc}")

    lues = trouvees = 0
    for i, sc in enumerate(cibles[:limite], 1):
        log.progress(i / max(1, min(len(cibles), limite)))
        chemins = sc.get("paths") or {}
        url_planche = chemins.get("sprite")
        url_vtt = chemins.get("vtt")
        if not url_planche or not url_vtt:
            continue
        if not (vision.adresse_de_stash(ctx, url_planche)
                and vision.adresse_de_stash(ctx, url_vtt)):
            continue
        try:
            vtt = _telecharger(url_vtt).decode("utf-8", "replace")
            planche = _telecharger(url_planche)
        except Exception as exc:
            log.debug(f"planche inaccessible : {str(exc)[:70]}")
            continue

        cases = cases_utiles(cases_du_vtt(vtt))
        if not cases:
            continue
        lus, studio_lu = [], None
        for boite in cases:
            vu = _lire_case(ctx, planche, boite)
            lus.extend(vu.get("noms") or [])
            studio_lu = studio_lu or vu.get("studio")
        lues += 1

        noms = noms_plausibles(lus)
        _marquer(ctx, sc)
        if not noms and not studio_lu:
            continue
        ids = [x for x in (rapprocher_interprete(n, index)
                           for n in noms) if x]
        studio_id = (rapprocher_studio(studio_lu, idx_studios)
                     if studio_lu else None)
        log.info(f"  scène {sc['id']} : {len(noms)} nom(s) lu(s), "
                 f"{len(ids)} reconnu(s)"
                 + (f", studio « {str(studio_lu)[:22]} »"
                    if studio_lu else ""))
        _proposer(ctx, sc, noms, ids, studio_lu, studio_id)
        trouvees += 1

    log.info(f"{lues} générique(s) examinés, {trouvees} avec des noms.")
    if trouvees:
        log.info("  Rien n'a été attribué : un nom lu sur une image "
                 "est une hypothèse. Les propositions figurent dans "
                 "le champ « enrich_generique ».")


def appliquer_generiques(ctx):
    """Applique les interpretes et studios lus aux generiques.

    Une proposition qui n'est jamais reprise est un cul-de-sac :
    l'utilisateur voit des noms reconnus au catalogue, et la scene
    reste vide. Le defaut avait ete corrige pour les filigranes et
    oublie ici.

    Un nom INCONNU ne cree rien : une erreur de lecture sur une image
    agrandie peuplerait le catalogue de fantomes, et une fiche creee a
    tort se remarque bien plus tard que la scene qu'elle prive de son
    vrai interprete.
    """
    if not ctx.source_active("generiques"):
        log.info("Reglage : la lecture des generiques est desactivee.")
        return
    perfs = studios = 0
    for sc in ctx.stash.find_scenes():
        brut = (sc.get("custom_fields") or {}).get("enrich_generique")
        if not brut:
            continue
        try:
            d = json.loads(brut)
        except (ValueError, TypeError) as exc:
            log.debug(f"case de planche illisible : {str(exc)[:70]}")
            continue

        maj, notes = {}, []
        ids = [str(x) for x in (d.get("performer_ids") or []) if x]
        if ids and not sc.get("performers"):
            maj["performer_ids"] = ids
            notes.append(f"performers: +{len(ids)} depuis le generique")
            perfs += 1
        studio_id = d.get("studio_id")
        if studio_id and not (sc.get("studio") or {}).get("id"):
            maj["studio_id"] = str(studio_id)
            notes.append("studio: lu au generique")
            studios += 1
        if not maj:
            continue
        try:
            maj["id"] = sc["id"]
            maj["custom_fields"] = {"partial": {
                "enrich_sources": " | ".join(notes)}}
            ctx.stash.update_scene(maj)
        except Exception as exc:
            log.debug(f"scene {sc['id']} : {str(exc)[:70]}")

    log.info(f"{perfs} scene(s) reliees a des interpretes, "
             f"{studios} studio(s) poses depuis les generiques.")


def _marquer(ctx, sc):
    """Trace de lecture : relire la même planche coûterait les mêmes
    appels pour le même résultat."""
    try:
        ctx.stash.update_scene({
            "id": sc["id"],
            "custom_fields": {"partial": {
                "enrich_generique_le":
                    _date_auj.today().isoformat()}}})
    except Exception as exc:
        log.debug(f"marquage : {str(exc)[:70]}")


def _proposer(ctx, sc, noms, ids, studio_lu=None, studio_id=None):
    """Consigne les noms lus SANS toucher aux interprètes de la
    scène."""
    try:
        ctx.stash.update_scene({
            "id": sc["id"],
            "custom_fields": {"partial": {
                "enrich_generique": json.dumps(
                    {"noms_lus": noms, "performer_ids": ids,
                     "studio_lu": studio_lu, "studio_id": studio_id,
                     "d": _date_auj.today().isoformat()},
                    ensure_ascii=False)}}})
    except Exception as exc:
        log.debug(f"proposition : {str(exc)[:70]}")
