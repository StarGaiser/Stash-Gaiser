import re
import sys
from pathlib import Path

sys.path.insert(0, "gaizer")
import i18n

texte = i18n.t("prompt_biohot", "fr")

# Le controle mecanique verifie desormais les noms propres apres
# generation : le prompt n'a plus a plaider aussi longuement sur ce
# point. Ce que le CODE garantit n'a pas besoin d'etre argumente au
# modele — et un prompt plus court laisse mieux voir ce qui reste.
texte = texte.replace(
    "Les chiffres et les NOMS PROPRES se recopient, ils ne "
    "s'estiment pas : un studio plausible mais faux est pire qu'un "
    "studio tu, car personne ne vérifie un nom qui sonne juste. Si "
    "les données ne nomment aucun studio, n'en nomme aucun. Matière "
    "maigre : deux phrases vraies valent mieux que quatre inventées.",
    "Les chiffres et les noms propres se recopient, ils ne "
    "s'estiment pas. Matière maigre : fais court, deux phrases vraies "
    "valent mieux que quatre inventées.", 1)

texte = texte.replace(
    "Un divorce, un ancien métier, une taille de bite : inventés pour "
    "faire joli, ce sont des mensonges sur une personne réelle, et "
    "rien ne les signalera comme tels.",
    "Un divorce, un ancien métier, une taille de bite inventés pour "
    "faire joli sont des mensonges sur une personne réelle, que rien "
    "ne signalera.", 1)

texte = texte.replace(
    "OBJECTIF. Le lecteur possède ces scènes et cherche laquelle "
    "regarder ce soir. Donne-lui ENVIE de revoir cet acteur : ce "
    "qu'il a de bandant, ce qui le distingue. Un inventaire — "
    "« physique de rugbyman, quatre scènes ici » — n'excite "
    "personne.",
    "OBJECTIF. Le lecteur possède ces scènes et cherche laquelle "
    "regarder ce soir. Donne-lui ENVIE de revoir cet acteur. Un "
    "inventaire — « physique de rugbyman, quatre scènes ici » — "
    "n'excite personne.", 1)

texte = re.sub(r" +", " ", texte)
assert "fais court" in texte, "la concision doit rester dite"
assert len(texte) <= 2200, len(texte)


def bloc_python(t: str, indent: str = "            ") -> str:
    morceaux = t.split("\n")
    out = []
    for k, para in enumerate(morceaux):
        courant = ""
        for mot in para.split(" "):
            if courant and len(courant) + 1 + len(mot) > 52:
                out.append(courant + " ")
                courant = mot
            else:
                courant = (courant + " " + mot) if courant else mot
        if courant:
            out.append(courant)
        if k < len(morceaux) - 1:
            out.append("\\n")
    fusion = []
    for frag in out:
        if frag == "\\n" and fusion:
            fusion[-1] = fusion[-1] + "\\n"
        else:
            fusion.append(frag)
    return "\n".join(f'{indent}"{f}"' for f in fusion)


p = Path("gaizer/i18n.py")
s = p.read_text()
i = s.find("\nFR = {")
f = s.find("\n# =====", i)
bloc = s[i:f]
m = re.search(r'        "prompt_biohot": \(\n(?:.*\n)*?.*\),\n', bloc)
assert m
bloc = (bloc[:m.start()]
        + f'        "prompt_biohot": (\n{bloc_python(texte)}),\n'
        + bloc[m.end():])
p.write_text(s[:i] + bloc + s[f:])
print(f"  prompt : {len(texte)} caracteres")
