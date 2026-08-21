#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Généralise les normes : la règle, pas son anecdote.

Une norme s'énonce. Le récit de la fois où elle a manqué appartient au
journal de bord de celui qui l'a écrite, pas au document qu'un inconnu
lit pour savoir comment contribuer.

Deux choses se ressemblent et ne se valent pas. Expliquer POURQUOI une
règle existe est utile : « une seconde implémentation divergera de la
première » se retient mieux qu'un impératif nu. Raconter que l'auteur
s'est trompé n'apporte rien — c'est de l'autoflagellation, et cela
fait douter du reste.

Le critère retenu : garder ce qui décrit un MÉCANISME, retirer ce qui
raconte un ÉPISODE.
"""

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Le point 20 disait l'inverse de son titre, et racontait une
# hésitation. Réécrit en règle.
POINT_20 = '''## 20. Découper un module par intention

Quand un module absorbe ce qui ne trouve pas sa place ailleurs, il
cesse d'avoir une responsabilité et devient un fourre-tout : on n'y
trouve plus rien, et chaque ajout aggrave le cas.

Le découpage suit CE QU'ON VEUT OBTENIR — diagnostic, ménage,
arbitrage — et non l'ordre d'écriture. Quand l'interface propose déjà
un classement, c'est celui-là : un lecteur retrouve dans le code ce
qu'il voit à l'écran.

**Pas de façade de compatibilité.** Un module qui n'existe que pour
ré-exporter est un vestige, et il masque les défauts de la structure
qu'il enveloppe — notamment les dépendances latérales entre modules
frères, qui ne se voient qu'une fois la redirection retirée. Les
appelants sont mis à jour, y compris les tests : ceux-ci suivent la
conception, ils ne la dictent jamais.

**Une table partagée entre deux intentions n'appartient à aucune des
deux.** Sa place est dans la couche que toutes connaissent.

**Ne découper que du code couvert.** Sur du code non éprouvé, on
déplace sans savoir si l'on casse.
'''

# Ce qui est retiré : phrases qui racontent l'histoire du projet
# plutôt que d'énoncer une règle. Le remplacement conserve le
# mécanisme quand il y en a un.
REMPLACEMENTS = [
    # NORMES_DE_CODAGE
    ("""Les scrapers manquants ont été traités ainsi : vingt-six tests
d'abord, tous en échec faute de module, puis le code écrit contre ce
contrat.

Trois décisions en sont sorties qui seraient autrement apparues comme
des correctifs après coup — et un correctif après coup, c'est un défaut
qu'un utilisateur a rencontré avant nous.""",
     """Écrire les tests d'abord force à trancher les questions difficiles
avant qu'elles ne se noient dans l'implémentation. Un correctif après
coup, c'est un défaut qu'un utilisateur a rencontré avant nous."""),

    ("""Sur onze échecs d'une séance : trois venaient du faux serveur, trop
permissif ; six de tests qui supposaient un contrat que le code
n'avait jamais promis ; deux seulement d'un défaut réel.

Corriger le code à chaque échec aurait donc introduit neuf régressions.
L'ordre est : lire le contrat réel, vérifier le faux serveur, et
seulement alors mettre en cause le code.""",
     """Un test qui échoue met en cause trois choses, et le code arrive en
dernier. Le test peut supposer un contrat que le code n'a jamais
promis ; le faux serveur peut être trop permissif ou trop strict ;
le code peut avoir tort.

Corriger le code à chaque échec introduit des régressions. L'ordre
est : lire le contrat réel, vérifier le faux serveur, puis seulement
mettre en cause le code."""),

    ("""Un contrôle qu'on écrit soi-même reflète ce à quoi on pense. En une
passe, `ruff` et `bandit` ont trouvé une collision de noms qui levait
une exception à l'exécution, des guillemets imbriqués incompatibles
avec Python 3.11, et une adresse non contrôlée permettant de lire un
fichier local. Six cents tests écrits à la main les avaient laissés
passer.""",
     """Un contrôle qu'on écrit soi-même reflète ce à quoi on pense ; des
outils tiers repèrent ce à quoi on ne pense pas. Collisions de noms,
constructions valides seulement dans une version récente du langage,
entrées non contrôlées : autant de défauts qu'une suite de tests, si
fournie soit-elle, ne cherche pas."""),

    ("""**La protection va là où tout le monde passe.** Le filtrage des
secrets vivait chez l'appelant : la tâche de sauvegarde savait quoi ne
pas écrire. Suffisant tant qu'elle était seule, ouvert dès qu'un autre
chemin d'écriture est apparu. Il appartient désormais à l'écriture
elle-même, seule à être forcément traversée.""",
     """**La protection va là où tout le monde passe.** Filtrer les secrets
chez l'appelant suffit tant qu'il est seul, et le trou se rouvre au
premier chemin d'écriture ajouté. La protection appartient au passage
obligé — l'écriture elle-même."""),

    ("""**Une liste d'opérations interceptées se vérifie par le code, pas par
la mémoire.** La destruction d'étiquettes échappait à la simulation
depuis son introduction. Un test énumère désormais les mutations
employées et exige qu'elles y figurent toutes.""",
     """**Une liste d'opérations interceptées se vérifie par le code, pas par
la mémoire.** Un test énumère les mutations employées et exige
qu'elles figurent toutes dans le mécanisme de simulation. Une
omission n'y est pas visible autrement."""),

    ("""Les messages de commit documentent les défauts trouvés, et les défauts
viennent de données réelles. Cinq d'entre eux citaient des interprètes
de la collection : utile techniquement, mais publié sous un nom, cela
décrit les goûts de quelqu'un.

Les chemins absolus portent le nom d'utilisateur. Les scripts de
correction ponctuels n'ont aucune valeur une fois appliqués et n'en
portent que le risque.""",
     """Les défauts viennent de données réelles, et les messages de commit
les documentent. Citer une fiche décrit ce que contient une
collection — donc les goûts de celui qui publie, et des personnes
réelles.

Les chemins absolus portent un nom d'utilisateur. Les scripts de
correction ponctuels n'ont aucune valeur une fois appliqués et n'en
portent que le risque."""),

    ("""`sources.py` portait une SECONDE implémentation de l'arbitrage —
soixante-cinq lignes, complexité 19 — que personne n'appelait. Lue par
quelqu'un qui découvre le projet, elle laissait croire que la décision
se prend là. Corrigée un jour par mégarde, elle aurait divergé de la
vraie sans que rien ne le signale.

Deux cents lignes retirées au total : la table des sources vidéo
pointait vers des fonctions elles-mêmes mortes, et un appel à
`ffprobe` ne servait plus.

`vulture` trouve ces cas ; encore faut-il le lancer et agir sur ce
qu'il dit, plutôt que de laisser le doute protéger le code inutile.""",
     """Une fonction que personne n'appelle laisse croire, à qui découvre le
projet, que la décision se prend là. Corrigée un jour par mégarde,
elle diverge de la vraie sans que rien ne le signale.

Le code mort s'accumule par grappes : une table pointe vers des
fonctions elles-mêmes mortes, un appel à un outil externe ne sert
plus. `vulture` trouve ces cas ; encore faut-il agir sur ce qu'il dit,
plutôt que de laisser le doute protéger l'inutile."""),
]


def main():
    p = RACINE / "docs" / "NORMES_DE_CODAGE.md"
    s = p.read_text(encoding="utf-8")

    # Le point 20, réécrit en entier
    debut = s.find("## 20. Découper sans casser")
    if debut > 0:
        fin = s.find("\n## ", debut + 10)
        s = s[:debut] + POINT_20 + "\n" + s[fin + 1:]
        print("  point 20 réécrit")

    n = 0
    for avant, apres in REMPLACEMENTS:
        if avant in s:
            s = s.replace(avant, apres, 1)
            n += 1
    p.write_text(s, encoding="utf-8")
    print(f"  {n}/{len(REMPLACEMENTS)} passages généralisés")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
