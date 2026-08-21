import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, "gaizer")

# ═══ 1. Retirer du panneau ce qui appartient a la fiche ═════════════
# Une action qui a besoin d'un identifiant demande de le saisir a la
# main : sa place est sur la fiche, ou l'identifiant est implicite.
#
# « Appliquer les propositions » existe deja sur chaque fiche, ou il
# porte sur ce qu'on regarde. Le repeter en trois boutons de balayage
# — un par famille — cree une confusion sans rien apporter.
p = Path("gaizer/gaizer_page.js")
s = p.read_text()

A_RETIRER = (
    "apply_accepted_scenes", "apply_accepted_studios",
    "enrich_one_performer", "enrich_one_scene", "enrich_one_studio",
    "deduire_roles",
)
n = 0
for mode in A_RETIRER:
    # Une entree tient sur une a trois lignes : du crochet ouvrant au
    # crochet fermant de son tuple.
    motif = re.compile(
        r'\n\s*\["' + mode + r'",[\s\S]{0,400}?\],(?=\n)')
    s, k = motif.subn("", s)
    n += k
p.write_text(s)
print(f"  {n} entree(s) retiree(s) du panneau")

# ═══ 2. La deduction des roles suit l'enrichissement ════════════════
# Elle lit la documentation DEJA collectee : la proposer en solo
# oblige a comprendre qu'il faut d'abord enrichir, puis relancer autre
# chose. Sa place est dans l'enrichissement, dont elle est une etape.
p2 = Path("gaizer/performers.py")
s2 = p2.read_text()
if "deduire_role" not in s2:
    a = "def enrich_performers(ctx):"
    i = s2.find(a)
    assert i > 0, "enrich_performers introuvable"
    j = s2.find('"""', i + len(a))
    j = s2.find('"""', j + 3) + 3
    # Apres la boucle d'enrichissement, sur les fiches traitees.
    s2 = s2[:j] + s2[j:]
    # On ajoute l'appel dans _enrichir_performer, la ou la
    # documentation vient d'etre collectee.
    a2 = "def _enrichir_performer(ctx"
    k = s2.find(a2)
    if k > 0:
        fin = s2.find("\ndef ", k + 10)
        corps = s2[k:fin if fin > 0 else len(s2)]
        if "deduire_role" not in corps:
            # Juste avant le return final de la fonction.
            lignes = corps.rstrip().split("\n")
            insertion = '''
    # Le role ne figure dans aucun champ de source : la seule piste
    # est qu'un texte le DISE. La deduction lit donc la documentation
    # qu'on vient de collecter — la proposer en tache separee
    # obligerait a enrichir, puis a relancer autre chose.
    if ctx.settings.get("deduireRoles"):
        try:
            roles.deduire_depuis_documentation(ctx, fiche, raw)
        except Exception as exc:
            log.debug(f"roles : {str(exc)[:70]}")
'''
            corps = "\n".join(lignes) + insertion
            s2 = s2[:k] + corps + (s2[fin:] if fin > 0 else "")
    p2.write_text(s2)
    print("  deduction integree a l'enrichissement")

# ═══ 3. Le reglage ══════════════════════════════════════════════════
p3 = Path("gaizer/gaizer.yml")
d = yaml.safe_load(p3.read_text())
d["version"] = "0.74.0"
d["settings"]["deduireRoles"] = {
    "displayName": "3. Deduce sexual role from documentation",
    "description": (
        "While enriching a performer, reads the documentation just "
        "collected for an EXPLICIT mention of their usual role. The "
        "model must quote the passage, and the quote is checked "
        "against the source text. Costs one model call per performer. "
        "Off by default."),
    "type": "BOOLEAN"}
p3.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False,
                             width=78))
print("  reglage deduireRoles")
