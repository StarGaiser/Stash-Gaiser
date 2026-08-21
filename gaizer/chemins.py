# -*- coding: utf-8 -*-
"""
Ce que le rangement dit du contenu.

Une médiathèque est rangée, et son rangement porte de l'information :
« /nas/GAY - ManUpFilms - The.Power.Of.Persuasion/scene.mp4 » nomme le
studio dans le dossier et le titre dans le même segment.

Le plugin ne lisait que le nom de fichier. Sur une collection réelle,
cent vingt-six scènes sans studio se trouvaient dans des dossiers
portant ce studio en toutes lettres — information gratuite, exacte, et
ignorée.

**C'est plus fiable que la lecture d'image et sans commune mesure en
coût.** Aucun appel réseau, aucun modèle, aucune hallucination
possible : le texte est là.

**Mais un chemin n'est pas une preuve.** Un dossier peut être mal
nommé, ou contenir autre chose que ce qu'il annonce. Le rapprochement
reste donc EXACT — jamais partiel, jamais créateur — et rien n'est
écrasé.
"""

from __future__ import annotations

import os
import re

from stashapi import log

# Segments qui ne nomment jamais une entité : rangement, qualité,
# encodage. Les retenir produirait un studio « 1080p ».
_INUTILES = re.compile(
    r"^(nas|mnt|data|media|videos?|films?|movies?|scenes?|gay|porn|"
    r"divers|autres?|new|nouveaux?|temp|tmp|downloads?|"
    r"\d{3,4}p|4k|8k|uhd|hd|sd|x26[45]|hevc|web-?dl|bluray|dvdrip|"
    r"part\s*\d*|cd\d|disc\d|vol\.?\s*\d*|\d{4})$", re.I)

# Dossiers de TRAVAIL : ils décrivent une manipulation de fichiers, non
# leur contenu. Les prendre pour des titres écrirait « rapatrie USB »
# sur des dizaines de scènes. La liste ne peut pas être exhaustive —
# chacun range à sa façon — mais le vocabulaire de manipulation se
# généralise.
_TRAVAIL = re.compile(
    r"^[_\s]*(?:[àa]\s+|to\s+)?(rapatri\w*|trier?|class\w*|sort\w*|backup|"
    r"sauvegardes?|en\s+cours|old|anciens?|r[ée]cup\w*|copies?|"
    r"imports?|exports?|misc|divers|inbox|corbeille|trash|todo|"
    r"[àa]\s+voir|[àa]\s+faire)"
    r"(\s+\w{1,6})?$", re.I)

# Séparateurs employés à l'intérieur d'un nom de dossier.
# Le rangement reel est moins regulier que les exemples :
# « GAY -TreasureIslandMedia - Titre » n'a pas d'espace avant le
# tiret, et « _rapatrie_USB » emploie des tirets bas. Un decoupage
# trop strict laisse le studio DANS le titre.
_COUPES = re.compile(r"\s*-\s+|\s+-\s*|\s*_\s*|\s*\|\s*")

# Un rangement courant place la distribution entre parentheses ou
# crochets : « Worship (Abraham Montenegro, Dylan Ayrton) ». Ces
# noms doivent etre lus, et RETIRES du titre.
_ENTRE = re.compile(r"[\(\[]([^\)\]]{4,120})[\)\]]")


# Sigles d'encodage et de source. Un segment qui n'est fait que de
# ceux-la decrit le FICHIER, non son contenu — meme quand aucun pris
# isolement ne suffit a l'ecarter : « OTB WEB-DL 1080p AVC ».
_TECHNIQUE = re.compile(
    r"^(web|dl|web-?dl|bluray|blu-?ray|remux|hdtv|dvdrip|brrip|"
    r"x26[45]|h\.?26[45]|hevc|avc|aac|ac3|dts|flac|mp3|5\.?1|"
    r"\d{3,4}p|4k|8k|uhd|hd|sd|otb|xvid|divx|10bit|hdr|"
    # Mentions de langue et de piste, aussi frequentes que le format.
    r"vo|vf|vost\w*|multi|truefrench|subfrench|dual|"
    r"h26[45]-\w+|x26[45]-\w+)$", re.I)


def _que_du_technique(texte: str) -> bool:
    """Le segment n'est-il fait que de mentions de format ?"""
    mots = [m for m in re.split(r"[\s.-]+", texte) if m]
    if not mots:
        return False
    return all(_TECHNIQUE.match(m) or m.isdigit() for m in mots)


def _sans_queue(texte: str) -> str:
    """Retire la queue technique d'un nom de fichier de partage.

    « Sacred Band Of Thebes 2018 VO 1080p WEB AAC 2 0 H264-NTb » suit
    une convention : le titre, puis l'annee, puis les mentions de
    format. Ecarter le segment entier perdrait un vrai titre ; le
    garder tel quel ecrit une ligne illisible sur la fiche.

    La coupe se fait au premier mot technique — une annee seule ne
    suffit pas, « Bareback Auditions 12 » finit legitimement par un
    nombre.
    """
    mots = [m for m in re.split(r"\s+", texte) if m]
    # L'annee est la frontiere la plus sure : ce qui la suit dans un
    # nom de fichier de partage est toujours technique.
    for i, mot in enumerate(mots):
        if i >= 2 and re.fullmatch(r"(19|20)\d\d", mot) and \
                i + 1 < len(mots) and _TECHNIQUE.match(mots[i + 1]):
            return " ".join(mots[:i]).strip(" -,_")
    for i, mot in enumerate(mots):
        if not _TECHNIQUE.match(mot):
            continue
        # Une mention technique isolee en fin de titre suffit a
        # couper ; au milieu, elle pourrait appartenir au titre.
        if i >= 2:
            return " ".join(mots[:i]).strip(" -,_")
    # Une annee suivie d'autre chose est aussi une frontiere.
    for i, mot in enumerate(mots):
        if i >= 2 and re.fullmatch(r"(19|20)\d\d", mot) and \
                i + 1 < len(mots):
            return " ".join(mots[:i]).strip(" -,_")
    return texte


def _propre(brut: str) -> str:
    """Segment lisible : les points et tirets tiennent lieu d'espaces
    dans « The.Power.Of.Persuasion »."""
    texte = re.sub(r"[._]+", " ", str(brut or ""))
    return re.sub(r"\s+", " ", texte).strip(" -")


def segments(chemin) -> list:
    """Tous les fragments du chemin susceptibles de nommer quelque
    chose, du plus proche du fichier au plus lointain.

    L'ordre compte : le dossier immédiat décrit mieux le fichier que
    la racine de la médiathèque.
    """
    brut = str(chemin or "")
    if not brut:
        return []
    dossier, fichier = os.path.split(brut)
    fichier = os.path.splitext(fichier)[0]
    parties = [p for p in dossier.split(os.sep) if p]
    out = []
    for morceau in [fichier, *reversed(parties)]:
        # « [MEN][Gay]Titre » : les crochets de tete nomment le studio
        # ou une categorie. Ils sont lus comme segments a part, et le
        # titre est ce qui suit.
        for etiquette in re.findall(r"^\s*(?:\[([^\]]{2,30})\]\s*)+",
                                    morceau):
            pass
        for etiquette in re.findall(r"\[([^\]]{2,30})\]", morceau):
            texte = _propre(etiquette)
            if len(texte) >= 3 and not _INUTILES.match(texte):
                out.append(texte)
        # Le contenu des parentheses est traite a part : il porte
        # souvent la distribution, separee par des virgules.
        for interieur in _ENTRE.findall(morceau):
            for bout in re.split(r"\s*,\s*|\s+(?:and|et|&|\+)\s+",
                                 interieur):
                texte = _propre(bout)
                if len(texte) >= 3 and not _INUTILES.match(texte):
                    out.append(texte)
        for bout in _COUPES.split(_ENTRE.sub(" ", morceau)):
            texte = _propre(bout)
            if (len(texte) >= 3 and not _INUTILES.match(texte)
                    and not _TRAVAIL.match(texte)):
                out.append(texte)
    return out


def _reduit(texte) -> str:
    """Forme comparable. Le numéro final est retiré : « Hardkinks 3 »
    et « HardKinks 1 » désignent le même studio, le chiffre étant une
    commodité de rangement."""
    nu = re.sub(r"\s+\d{1,3}$", "", str(texte or "").strip())
    return re.sub(r"[^a-z0-9]", "", nu.lower())


# Suffixes d'usage : « Treasure Island Media » et « Treasure Island »
# désignent le même studio. Ils ne sont retirés que du texte LU —
# les retirer du catalogue ferait confondre « Next Door » et « Next
# Door Studios », qui peuvent être deux entités.
_SUFFIXES = re.compile(
    r"(media|studios?|films?|productions?|entertainment|network|"
    r"com|tv|xxx)$", re.I)


def studio_du_chemin(chemin, index: dict):
    """Identifiant du studio nommé dans le chemin, ou None.

    Rapprochement EXACT : « Next Door » ne doit pas ramener « Next
    Door Studios », deux studios pouvant partager un préfixe.
    """
    reduits = {_reduit(nom): ident
               for nom, ident in (index or {}).items()}
    for seg in segments(chemin):
        cle = _reduit(seg)
        trouve = reduits.get(cle)
        if trouve:
            return trouve
        # « TreasureIslandMedia » désigne « Treasure Island » : le
        # suffixe d'usage est retiré du texte lu, jamais du catalogue.
        court = _SUFFIXES.sub("", cle)
        if len(court) >= 6 and court != cle:
            trouve = reduits.get(court)
            if trouve:
                return trouve
    return None


# Formules de compilation : un dossier nomme son interprete avant ou
# apres une tournure fixe — « The Best Of Untel », « Untel
# Collection ». Le rapprochement exact echoue sur le segment
# entier ; retirer la formule laisse le nom.
_COMPILATION = re.compile(
    r"^(?:the\s+|le\s+|la\s+|les\s+)?"
    r"(?:best\s+of|meilleur[es]?\s+d[eu]|collection|anthology|"
    r"anthologie|compilation|greatest\s+hits|selection)\s+"
    r"|"
    r"\s+(?:collection|anthology|anthologie|compilation|"
    r"greatest\s+hits)$", re.I)


def _sans_formule(texte: str) -> str:
    """Le nom, une fois la formule de compilation retiree.

    Rend une chaine vide si rien d'utile ne subsiste : « Best Of »
    seul ne designe personne.
    """
    nu = _COMPILATION.sub(" ", str(texte or ""))
    nu = re.sub(r"^(?:the|le|la|les)\s+", "", nu.strip(), flags=re.I)
    return re.sub(r"\s+", " ", nu).strip()


def interpretes_du_chemin(chemin, index: dict) -> list:
    """Identifiants des interprètes nommés dans le chemin.

    Le nom complet doit apparaître : « Archie » seul désigne trop de
    monde, et attribuer une scène au mauvais interprète ne se rattrape
    par aucun arbitrage.
    """
    reduits = {_reduit(nom): ident
               for nom, ident in (index or {}).items()}
    trouves = []
    for seg in segments(chemin):
        # Un segment peut porter plusieurs noms : « Archie Fox and
        # Dean Young ».
        for bout in re.split(r"\s+(?:and|et|&|,|\+)\s+", seg):
            # Le rapprochement reste EXACT : retirer la formule ne
            # doit pas ouvrir la porte au partiel. « The Best Of
            # Archie » ne ramene pas « Archie Fox ».
            for essai in (bout, _sans_formule(bout)):
                if not essai:
                    continue
                ident = reduits.get(_reduit(essai))
                if ident and ident not in trouves:
                    trouves.append(ident)
                    break
    return trouves


def titre_du_chemin(chemin, studios_vus: set, interpretes_vus: set):
    """Meilleur candidat au titre, ou None.

    C'est le segment le plus long qui ne nomme ni studio ni
    interprète : ce qui reste après avoir retiré ce qu'on a reconnu
    est, en général, ce que le fichier raconte.
    """
    connus = (studios_vus or set()) | (interpretes_vus or set())
    candidats = []
    for seg in segments(chemin):
        if _reduit(seg) in connus:
            continue
        # Un segment peut porter un titre ET une distribution :
        # « Worship (Abraham Montenegro) ». Le titre est ce qui reste
        # une fois les noms reconnus retires — les laisser produirait
        # un titre de scene illisible.
        nu = seg
        for interieur in _ENTRE.findall(seg):
            noms = [n for n in re.split(
                r"\s*,\s*|\s+(?:and|et|&|\+)\s+", interieur)
                if _propre(n)]
            if noms and all(_reduit(_propre(n)) in connus
                            for n in noms):
                nu = _ENTRE.sub(" ", nu)
        nu = re.sub(r"\s+", " ", nu).strip(" -,")
        # Le studio reconnu peut subsister DANS le segment :
        # « GAY -TreasureIslandMedia - Brazil Fever » decoupe mal
        # laisserait le studio en tete du titre.
        for connu in connus:
            nu = re.sub(rf"(?i)\b{re.escape(connu)}\b", " ",
                        re.sub(r"[^\w\s]", " ", nu)) if _reduit(
                            nu).startswith(connu) else nu
        # Les etiquettes de tete precedent le titre, la queue
        # technique le suit : « [Gay]Harder They Come 2025 1080p ».
        nu = re.sub(r"^(\s*\[[^\]]{2,30}\]\s*)+", " ", nu)
        nu = re.sub(r"\s+", " ", nu).strip(" -,_")
        nu = _sans_queue(nu)
        # « The Best Of Untel » nomme un recueil, non une
        # scene : si le nom qu'il porte est reconnu, le segment n'est
        # pas un titre.
        if _COMPILATION.search(nu) and _reduit(_sans_formule(nu)) in connus:
            continue
        if (len(nu) < 6 or _INUTILES.match(nu) or _TRAVAIL.match(nu)
                or _que_du_technique(nu) or _reduit(nu) in connus):
            continue
        candidats.append(nu)
    if not candidats:
        return None
    return max(candidats, key=len)


# ── Tâche ────────────────────────────────────────────────────────────
def lire_chemins(ctx, scenes=None):
    """Complète les scènes à partir de leur emplacement sur le disque.

    Ne remplit que ce qui est vide : un chemin dit où le fichier est
    rangé, pas ce qu'une source a établi.
    """
    if not ctx.source_active("chemin"):
        log.info("Reglage : l'enrichissement depuis le chemin est desactive.")
        return
    # Une liste fournie limite la tache a ces scenes :
    # c'est ce qui permet a l'enchainement de l'appeler
    # fiche par fiche, sans reparcourir la collection.
    scenes = (scenes if scenes is not None
              else ctx.stash.find_scenes())
    idx_studios, idx_perfs = {}, {}
    try:
        idx_studios = {s["name"]: s["id"]
                       for s in ctx.stash.find_studios()}
    except Exception as exc:
        log.debug(f"studios illisibles : {exc}")
    try:
        idx_perfs = {p["name"]: p["id"]
                     for p in ctx.stash.find_performers()}
    except Exception as exc:
        log.debug(f"interprètes illisibles : {exc}")

    auto = ctx.settings.get("applyMode") in ("auto", "seuil")
    poses = liees = titres = 0
    for sc in scenes:
        fichiers = sc.get("files") or []
        if not fichiers:
            continue
        chemin = fichiers[0].get("path") or ""
        if not chemin:
            continue

        maj, notes = {}, []
        if not (sc.get("studio") or {}).get("id"):
            ident = studio_du_chemin(chemin, idx_studios)
            if ident:
                maj["studio_id"] = ident
                notes.append("studio: reconnu dans le chemin")
                poses += 1
        if not sc.get("performers"):
            ids = interpretes_du_chemin(chemin, idx_perfs)
            if ids:
                maj["performer_ids"] = ids
                notes.append(f"performers: +{len(ids)} depuis le "
                             f"chemin")
                liees += 1
        if not (sc.get("title") or "").strip():
            titre = titre_du_chemin(
                chemin,
                {_reduit(n) for n in idx_studios},
                {_reduit(n) for n in idx_perfs})
            if titre:
                maj["title"] = titre
                notes.append("title: tiré du chemin")
                titres += 1

        if not maj:
            continue
        if not auto:
            log.info(f"  scène {sc['id']} : {' | '.join(notes)} "
                     f"(mode manuel, non appliqué)")
            continue
        try:
            maj["id"] = sc["id"]
            # La provenance dit d'où vient la valeur : le rangement
            # n'a pas le statut d'une source documentaire.
            maj["custom_fields"] = {"partial": {
                "enrich_sources": " | ".join(notes)}}
            ctx.stash.update_scene(maj)
        except Exception as exc:
            log.debug(f"scène {sc['id']} : {str(exc)[:70]}")

    log.info(f"{poses} studio(s), {liees} lien(s) d'interprètes, "
             f"{titres} titre(s) depuis les chemins.")
    if not auto:
        log.info("  Mode manuel : rien n'a été écrit.")
