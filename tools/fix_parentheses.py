from pathlib import Path

p = Path("gaizer/chemins.py")
s = p.read_text()

# ── Les parentheses portent souvent la distribution ──────────────────
a = '''# Separateurs employes a l'interieur d'un nom de dossier.
_COUPES = re.compile(r"\\s+-\\s+|\\s+_\\s+|\\s*\\|\\s*")'''
b = '''# Separateurs employes a l'interieur d'un nom de dossier.
_COUPES = re.compile(r"\\s+-\\s+|\\s+_\\s+|\\s*\\|\\s*")

# Un rangement courant place la distribution entre parentheses ou
# crochets : « Worship (Abraham Montenegro, Dylan Ayrton) ». Ces noms
# doivent etre lus, et RETIRES du titre — ils n'y ont pas leur place.
_ENTRE = re.compile(r"[\\(\\[]([^\\)\\]]{4,120})[\\)\\]]")'''
assert a in s
s = s.replace(a, b, 1)

# ── Les segments incluent le contenu des parentheses ─────────────────
a2 = '''    out = []
    for morceau in [fichier, *reversed(parties)]:
        for bout in _COUPES.split(morceau):
            texte = _propre(bout)
            if len(texte) >= 3 and not _INUTILES.match(texte):
                out.append(texte)
    return out'''
b2 = '''    out = []
    for morceau in [fichier, *reversed(parties)]:
        # Le contenu des parentheses est traite a part : il porte
        # souvent la distribution, separee par des virgules.
        for interieur in _ENTRE.findall(morceau):
            for bout in re.split(r"\\s*,\\s*|\\s+(?:and|et|&|\\+)\\s+",
                                 interieur):
                texte = _propre(bout)
                if len(texte) >= 3 and not _INUTILES.match(texte):
                    out.append(texte)
        for bout in _COUPES.split(_ENTRE.sub(" ", morceau)):
            texte = _propre(bout)
            if len(texte) >= 3 and not _INUTILES.match(texte):
                out.append(texte)
    return out'''
assert a2 in s
s = s.replace(a2, b2, 1)

# ── Le titre se debarrasse de ce qui a ete reconnu ───────────────────
a3 = '''    candidats = []
    for seg in segments(chemin):
        cle = _reduit(seg)
        if cle in (studios_vus or set()) or cle in (
                interpretes_vus or set()):
            continue
        if len(seg) < 6 or _INUTILES.match(seg):
            continue
        candidats.append(seg)
    if not candidats:
        return None
    return max(candidats, key=len)'''
b3 = '''    connus = (studios_vus or set()) | (interpretes_vus or set())
    candidats = []
    for seg in segments(chemin):
        if _reduit(seg) in connus:
            continue
        # Un segment peut contenir un titre ET une distribution :
        # « Worship (Abraham Montenegro) ». Le titre est ce qui reste
        # une fois les noms reconnus retires — les laisser produirait
        # un titre de scene illisible.
        nu = seg
        for interieur in _ENTRE.findall(seg):
            noms = re.split(r"\\s*,\\s*|\\s+(?:and|et|&|\\+)\\s+",
                            interieur)
            if noms and all(_reduit(_propre(n)) in connus
                            for n in noms if _propre(n)):
                nu = _ENTRE.sub(" ", nu)
        nu = re.sub(r"\\s+", " ", nu).strip(" -,")
        if len(nu) < 6 or _INUTILES.match(nu) or _reduit(nu) in connus:
            continue
        candidats.append(nu)
    if not candidats:
        return None
    return max(candidats, key=len)'''
assert a3 in s
s = s.replace(a3, b3, 1)
p.write_text(s)
print("  parentheses exploitees")
