# -*- coding: utf-8 -*-
"""
Retrouver un studio a partir d'un texte lu.

Un filigrane, une adresse incrustee, un nom mal reconnu : ce qui
sort d'une lecture d'image est approximatif, et le rapprocher du
catalogue demande plusieurs sources de sureté decroissante.

**L'adresse d'abord.** Un filigrane EST souvent une URL, et une
URL ne souffre pas d'orthographe : deux studios ne partagent pas
un domaine. C'est le rapprochement le plus fiable qui soit.

**Puis le nom exact, puis les alias** que le studio declare
lui-meme. Ces trois sources sont sures.

**Ensuite les approximations**, qui ne le sont pas : un nom
contenu dans ce qui a ete lu, une erreur de reconnaissance a un
caractere pres. Elles sont proposees, jamais appliquees — un
studio attribue a tort ne se rattrape par aucun arbitrage.
"""

import re


def _studio_dans(textes) -> str:
    """Nom de studio reconnaissable parmi les textes lus.

    Une adresse en est un : « MASQULIN.COM » designe le studio.
    « Scene 4 », « HD » ou une annee n'en sont pas — du texte lu sur
    une image n'est pas un studio parce qu'il est lisible.
    """
    for texte in textes or []:
        nu = str(texte).strip()
        if re.search(r"\.(com|net|org|tv|xxx)\b", nu, re.I):
            # L'adresse porte le nom : retirer schema et suffixe.
            nom = re.sub(r"^https?://", "", nu, flags=re.I)
            nom = re.sub(r"^www\.", "", nom, flags=re.I)
            nom = re.split(r"[/?]", nom)[0]
            nom = re.sub(r"\.(com|net|org|tv|xxx)$", "", nom,
                         flags=re.I)
            if len(nom) >= 4:
                return nom
    return ""


def _reduit(texte) -> str:
    """Forme comparable d'un nom lu ou catalogue.

    Un filigrane s'ecrit « MASQULIN.COM », le catalogue « Masqulin » :
    la comparaison porte sur ce qui reste une fois retires casse,
    ponctuation et suffixe de domaine. La regle etait repetee a six
    endroits, ce qui garantissait qu'un ajustement en oublierait un.
    """
    nu = re.sub(r"[^a-z0-9]", "", str(texte or "").lower())
    return re.sub(r"(com|net|org|tv)$", "", nu)


def _domaine(texte) -> str:
    """Domaine nu d'une adresse, ou chaine vide.

    « https://www.hardkinks.com/scene/4 » et « HARDKINKS.COM »
    designent le meme studio : ce qui compte est ce qui reste une fois
    retires schema, prefixe et chemin.
    """
    nu = str(texte or "").strip().lower()
    nu = re.sub(r"^https?://", "", nu)
    nu = re.sub(r"^www\.", "", nu)
    nu = re.split(r"[/?#]", nu)[0]
    return nu if re.match(r"^[\w.-]+\.[a-z]{2,6}$", nu) else ""


def par_adresse(lu, studios):
    """Studio dont l'adresse correspond au texte lu.

    C'est le rapprochement le plus fiable qui soit. Un nom s'ecrit de
    dix facons et se lit mal ; une adresse est unique et ne souffre
    pas d'orthographe — deux studios ne partagent pas un domaine. Un
    filigrane EST souvent une adresse, ce qui rend ce chemin plus sur
    que tous les autres.
    """
    cible = _domaine(lu)
    if not cible:
        return None
    for st in studios or []:
        connu = _domaine((st or {}).get("url"))
        if connu and connu == cible:
            return str(st.get("id"))
    return None


def par_alias(lu, studios):
    """Studio dont un alias correspond au texte lu.

    Un studio porte souvent ses variantes d'ecriture en alias ;
    les ignorer fait rejeter une lecture correcte.

    Les alias reduits a un ou deux caracteres sont ecartes : ils
    viennent d'un import defectueux, et les employer rapprocherait
    n'importe quoi.
    """
    cle = _reduit(lu)
    if len(cle) < 4:
        return None
    for st in studios or []:
        for alias in (st or {}).get("aliases") or []:
            nu = _reduit(alias)
            if len(nu) >= 4 and nu == cle:
                return str(st.get("id"))
    return None


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


def malgre_erreur_de_lecture(lu, index: dict):
    """Studio correspondant a un caractere pres.

    Un filigrane se lit mal : un D pris pour un O, une lettre avalee.
    Refuser ces variantes fait perdre des scenes que l'utilisateur
    reconnaitrait d'un coup d'oeil.

    Trois garde-fous, car cette tolerance est dangereuse. Le nom doit
    etre assez long — sur quatre lettres, un caractere de difference
    change le mot. La distance est d'exactement un. Et si deux studios
    sont egalement proches, on ne choisit pas : une erreur qui peut
    designer deux entites n'en designe aucune.
    """
    cle = _reduit(lu)
    if len(cle) < 7:
        return None
    proches = []
    for nom, ident in (index or {}).items():
        nu = _reduit(nom)
        if len(nu) < 7 or abs(len(nu) - len(cle)) > 1:
            continue
        if _distance_un(cle, nu):
            proches.append(ident)
    return proches[0] if len(proches) == 1 else None


def _distance_un(a: str, b: str) -> bool:
    """Les deux chaines different-elles d'exactement un caractere ?

    Substitution, insertion ou suppression. Une comparaison complete
    de distance d'edition serait plus generale, mais ici seul le cas
    « un caractere » nous interesse : au-dela, ce n'est plus une
    erreur de lecture mais un autre nom.
    """
    if a == b:
        return False
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b, strict=True)
                   if x != y) == 1
    if abs(len(a) - len(b)) != 1:
        return False
    long, court = (a, b) if len(a) > len(b) else (b, a)
    return any(long[:i] + long[i + 1:] == court
               for i in range(len(long)))


def voisin_probable(lu, index: dict):
    """Studio dont le nom est CONTENU dans ce qui a été lu.

    Un filigrane dit « TREASURE ISLAND MEDIA » là où le catalogue dit
    « Treasure Island ». Rapprocher automatiquement serait dangereux —
    deux studios peuvent partager un préfixe. Mais taire la proximité
    fait passer pour inconnu ce que l'utilisateur reconnaîtrait d'un
    coup d'œil.

    Le voisin est donc SIGNALÉ, jamais appliqué. Le nom du catalogue
    doit être assez long pour distinguer.
    """
    cle = _reduit(lu)
    if len(cle) < 6:
        return None
    meilleur, longueur = None, 0
    for nom, ident in (index or {}).items():
        nu = _reduit(nom)
        if len(nu) >= 8 and nu in cle and len(nu) > longueur:
            meilleur, longueur = ident, len(nu)
    return meilleur
