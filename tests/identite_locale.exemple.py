# -*- coding: utf-8 -*-
"""
Identité à ne jamais publier — fichier LOCAL, jamais versionné.

Le piège est là : écrire son nom dans un test qui sera publié le
divulgue exactement autant que la fuite qu'on cherche à empêcher. La
liste vit donc hors du dépôt, dans un fichier ignoré par git, et le
contrôle s'abstient quand il est absent.

Chacun le remplit pour lui-même. Un contributeur extérieur n'y verra
rien, et son propre nom sera vérifié s'il prend la peine de l'écrire.

    cp tests/identite_locale.exemple.py tests/identite_locale.py

Les formes à couvrir : le nom complet, chaque partie prise seule si
elle est distinctive, les initiales, les identifiants de comptes, les
pseudonymes anciens. Une initiale trop courte — deux lettres — produit
trop de faux positifs : la laisser de côté.
"""

# Exemples de ce qu'il faut y mettre. À REMPLACER par les siens.
FORMES = [
    "Jean-Dupont",          # nom complet
    "Dupont",               # patronyme seul, s'il est distinctif
    "jdupont",              # identifiant de compte
    "JDUP",                 # initiales, si elles font au moins 3 lettres
    "ancien-pseudo",        # pseudonymes abandonnés
]

# Noms propres de la collection qui ne doivent pas figurer dans un
# dépôt public : un défaut se décrit par sa FORME — « une date nulle »,
# « un nom réduit à un mot » — jamais par la fiche qui l'a révélé.
INTERPRETES = [
    "Prénom Nom",           # à remplacer par les siens
]
