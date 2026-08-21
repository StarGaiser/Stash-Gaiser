#!/usr/bin/env python3
"""Refuse un message de publication qui porterait une trace.

Le message sera PUBLIC, et une trace y serait aussi visible que dans
un fichier — sauf qu'un message ne se relit pas comme un fichier :
personne ne pense à l'auditer.

Les motifs viennent du même fichier local que l'audit des fichiers.
En tenir une seconde liste ici la ferait diverger, et surtout : cette
liste serait elle-même publiée, ce qui révélerait précisément ce
qu'elle protège.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _motifs():
    """Les formes de l'identité, depuis le fichier local."""
    try:
        import auditer_avant_publication as audit
    except ImportError:
        print("  ✗ audit introuvable : contrôle impossible",
              file=sys.stderr)
        return None
    # Le fichier local est lu par l'ARBRE, jamais exécuté : le
    # contrôle de sécurité du projet interdit « exec », à juste titre
    # ici aussi.
    local = audit.RACINE / "tests" / "identite_locale.py"
    if not local.exists():
        return None
    formes = []
    for nom in ("FORMES", "INTERPRETES"):
        formes += audit._liste(local, nom)
    return formes or None


def message_sans_trace(texte: str) -> bool:
    formes = _motifs()
    if formes is None:
        # Sans motifs, refuser plutôt que laisser passer : un
        # contrôle qu'on ne peut pas faire n'est pas un contrôle
        # réussi.
        return False
    for forme in formes:
        if re.search(re.escape(str(forme)), texte, re.IGNORECASE):
            print("  ✗ trace personnelle dans le message",
                  file=sys.stderr)
            return False
    # Une adresse de courriel qui n'est pas celle du pseudonyme.
    m = re.search(r"[\w.+-]+@(?!users\.noreply)[\w-]+\.[a-z]{2,}",
                  texte)
    if m and not m.group(0).startswith(("-git@", "git@")):
        print(f"  ✗ adresse de courriel dans le message : "
              f"« {m.group(0)} »", file=sys.stderr)
        return False
    # Un chemin qui nomme un compte d'utilisateur.
    m = re.search(r"/(?:home|Users)/[a-z][\w.-]+", texte)
    if m:
        print(f"  ✗ chemin personnel dans le message : "
              f"« {m.group(0)} »", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    texte = sys.argv[1] if len(sys.argv) > 1 else ""
    if not message_sans_trace(texte):
        sys.exit(1)
    print("  ✓ message sans trace personnelle")
