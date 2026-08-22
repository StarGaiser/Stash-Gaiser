"""Engendre l'inventaire des taches depuis le CODE.

Une liste ecrite a la main perime au premier ajout, et personne ne
s'en apercoit : c'est ce qu'un audit a montre sur les compteurs de
lignes et le nombre de taches. Celle-ci est reconstruite, et un test
verifie qu'elle correspond au registre.
"""
import ast
import re
from pathlib import Path

RACINE = Path(".")
CODE = RACINE / "gaizer"

# ── Les taches, depuis le registre ───────────────────────────────────
arbre = ast.parse((CODE / "gaizer.py").read_text(encoding="utf-8"))
modes = []
for n in ast.walk(arbre):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TASKS":
                modes = [k.value for k in n.value.keys]

# ── Ce que le panneau en dit ─────────────────────────────────────────
page = (CODE / "gaizer_page.js").read_text(encoding="utf-8")
descriptions = {}
for m in re.finditer(
        r'\["(\w+)",\s*\n?\s*"([^"]+)",\s*"([^"]+)"', page):
    descriptions[m.group(1)] = (m.group(2), m.group(3))

# ── Le groupe auquel chacune appartient ──────────────────────────────
GROUPES = {
    "g_demarrage": "Par famille",
    "g_courant": "Affiner",
    "g_menage": "Ménage",
    "g_diagnostic": "Diagnostic",
    "g_reparation": "Réparation",
}
appartenance = {}
for cle, titre in GROUPES.items():
    i = page.find(f'["{cle}", [')
    if i < 0:
        continue
    fin = page.find("    ]],", i)
    for m in re.finditer(r'\n\s*\["(\w+)",', page[i:fin]):
        if m.group(1) != cle:
            appartenance[m.group(1)] = titre

# ── Ce qui ECRIT, et ce qui regarde ──────────────────────────────────
# La distinction la plus utile a l'usage : une tache de lecture se
# lance sans risque, une tache d'ecriture demande d'y penser.
# Ce qui ne touche AUCUNE fiche. La distinction se juge sur l'effet,
# non sur le nom : « detect_duplicates » commence par « detect » mais
# POSE un tag sur chaque fiche suspecte. Le classer en lecture était
# une contradiction avec sa propre description, dans le même tableau
# — et l'inventaire sert précisément à décider si on peut lancer sans
# y penser.
LECTURE = {"rapport_run", "rapport_profil", "rapport_tags",
           "rapport_roles", "etat_agent", "controler_champs",
           "verifier_sources", "prompt_defaut", "suggerer_tags_exclus",
           "exporter_reglages", "noop"}

lignes = ["# Inventaire des tâches", "",
          "Engendré depuis le registre du plugin : une liste écrite à",
          "la main périme au premier ajout, sans que personne s'en",
          "aperçoive.", "",
          f"**{len(modes)} tâches.**", ""]

par_groupe = {}
for mode in modes:
    par_groupe.setdefault(appartenance.get(mode, "Hors panneau"),
                          []).append(mode)

for titre in ("Par famille", "Affiner", "Ménage", "Diagnostic",
              "Réparation", "Hors panneau"):
    dedans = par_groupe.get(titre)
    if not dedans:
        continue
    lignes += [f"## {titre}", ""]
    if titre == "Hors panneau":
        lignes += ["Ces tâches vivent sur les fiches, où elles",
                   "s'appliquent à un enregistrement précis, ou ne",
                   "sont appelées que par une autre.", ""]
    lignes += ["| Tâche | Écrit | Ce qu'elle fait |",
               "|---|---|---|"]
    for mode in sorted(dedans):
        libelle, desc = descriptions.get(mode, (mode, "—"))
        ecrit = "non" if mode in LECTURE else "**oui**"
        lignes.append(f"| {libelle} | {ecrit} | {desc} |")
    lignes.append("")

(RACINE / "docs" / "INVENTAIRE_TACHES.md").write_text(
    "\n".join(lignes) + "\n", encoding="utf-8")
print(f"  {len(modes)} tâches · {len(par_groupe)} groupes")
