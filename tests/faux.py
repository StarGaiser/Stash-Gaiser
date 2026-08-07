# -*- coding: utf-8 -*-
"""
Faux serveur Stash, en mémoire.

Les tests précédents ne portaient que sur des fonctions sans état. Pour
vérifier ce que la spécification PROMET — « une exécution annule un
passage », « relancer ne double rien », « une tâche respecte le lot » —
il faut observer les écritures. D'où cet objet : il garde les fiches en
mémoire, applique les mises à jour comme le ferait Stash, et surtout
**compte chaque appel**.

Le compte des appels est le cœur de l'affaire. Ce qui a réellement coûté
cher dans ce plugin n'était pas la lenteur d'un calcul mais le nombre
d'allers-retours : 400 poses de tag valaient 400 requêtes avant la mise
en cache. Une durée mesurée dépend de la machine et rend le test
instable ; un nombre d'appels est déterministe.
"""

from __future__ import annotations

import copy
import json
from collections import Counter


class FauxStash:
    """Imite la part de `StashInterface` que le plugin utilise."""

    def __init__(self, performers=None, scenes=None, studios=None,
                 tags=None, groups=None):
        self.performers = {str(p["id"]): dict(p)
                           for p in (performers or [])}
        self.scenes = {str(s["id"]): dict(s) for s in (scenes or [])}
        self.studios = {str(s["id"]): dict(s) for s in (studios or [])}
        self.tags = {str(t["id"]): dict(t) for t in (tags or [])}
        self.groups = {str(g["id"]): dict(g) for g in (groups or [])}
        self.appels = Counter()          # méthode ou mutation → nombre
        self.journal = []                # trace ordonnée, pour analyse
        self._suivant = 1000

    # ── comptage ─────────────────────────────────────────────────────
    def _note(self, quoi, detail=None):
        self.appels[quoi] += 1
        self.journal.append((quoi, detail))

    @property
    def total_appels(self) -> int:
        return sum(self.appels.values())

    def mutations(self) -> int:
        """Appels qui modifient quelque chose."""
        return sum(n for k, n in self.appels.items()
                   if any(m in k for m in ("update", "create", "destroy",
                                           "Update", "Create", "Destroy",
                                           "Merge")))

    def _id(self) -> str:
        self._suivant += 1
        return str(self._suivant)

    # ── lectures ─────────────────────────────────────────────────────
    def find_performers(self, f=None, filter=None, fragment=None):
        self._note("find_performers")
        return [copy.deepcopy(p) for p in self.performers.values()]

    def find_performer(self, ident, create=False, fragment=None):
        self._note("find_performer")
        cle = str(ident.get("id") if isinstance(ident, dict) else ident)
        p = self.performers.get(cle)
        return copy.deepcopy(p) if p else None

    def find_scenes(self, f=None, filter=None, fragment=None,
                    get_count=False):
        self._note("find_scenes")
        scenes = [copy.deepcopy(s) for s in self.scenes.values()]
        return (len(scenes), scenes) if get_count else scenes

    def find_tags(self, f=None, filter=None, fragment=None):
        self._note("find_tags")
        voulu = None
        if f and isinstance(f, dict):
            voulu = ((f.get("name") or {}).get("value"))
        return [copy.deepcopy(t) for t in self.tags.values()
                if voulu is None or t["name"] == voulu]

    def get_configuration(self, fragment=None):
        self._note("get_configuration")
        return {"general": {"stashBoxes": []},
                "plugins": {"gaizer": {}}}

    def list_performer_scrapers(self, *a, **k):
        self._note("list_performer_scrapers")
        return []

    # ── écritures ────────────────────────────────────────────────────
    def create_tag(self, entree, fragment=None):
        self._note("create_tag", entree.get("name"))
        for t in self.tags.values():
            if t["name"] == entree["name"]:
                return copy.deepcopy(t)
        tid = self._id()
        self.tags[tid] = {"id": tid, "name": entree["name"]}
        return copy.deepcopy(self.tags[tid])

    def destroy_tag(self, tid, fragment=None):
        self._note("destroy_tag", str(tid))
        self.tags.pop(str(tid), None)
        return True

    def update_performer(self, maj, fragment=None):
        self._note("update_performer", str(maj.get("id")))
        return self._appliquer(self.performers, maj)

    def update_scene(self, maj, fragment=None):
        self._note("update_scene", str(maj.get("id")))
        return self._appliquer(self.scenes, maj)

    def _appliquer(self, table, maj):
        """Reproduit la sémantique de Stash, y compris la mise à jour
        PARTIELLE des champs personnalisés — subtilité qui a déjà causé
        des pertes de données."""
        cle = str(maj.get("id"))
        fiche = table.setdefault(cle, {"id": cle})
        for champ, valeur in maj.items():
            if champ == "id":
                continue
            if champ == "custom_fields" and isinstance(valeur, dict):
                cf = fiche.setdefault("custom_fields", {})
                if "partial" in valeur:
                    cf.update(valeur["partial"])
                else:
                    fiche["custom_fields"] = dict(valeur)
            elif champ == "performer_ids":
                fiche["performers"] = [{"id": str(i)} for i in valeur]
            elif champ == "studio_id":
                fiche["studio"] = {"id": str(valeur)}
            elif champ == "tag_ids":
                fiche["tags"] = [{"id": str(i),
                                  "name": (self.tags.get(str(i)) or {})
                                  .get("name", f"tag{i}")}
                                 for i in valeur]
            elif champ == "groups":
                fiche["groups"] = [
                    {"group": {"id": str(g["group_id"]),
                               "name": (self.groups.get(
                                   str(g["group_id"])) or {})
                               .get("name", "")},
                     "scene_index": g.get("scene_index")}
                    for g in valeur]
            else:
                fiche[champ] = valeur
        return copy.deepcopy(fiche)

    # ── GraphQL ──────────────────────────────────────────────────────
    def call_GQL(self, requete, variables=None, callback=None):
        """Reconnaît les requêtes que le plugin émet réellement.

        Une requête non prévue lève : mieux vaut un test qui échoue
        franchement qu'un `None` silencieux interprété comme « aucun
        résultat »."""
        variables = variables or {}
        # Mutations
        for nom, action in (
            ("studioUpdate", self._studio_update),
            ("performerCreate", self._performer_create),
            ("studioCreate", self._studio_create),
            ("studioDestroy", self._studio_destroy),
            ("groupCreate", self._group_create),
            ("groupUpdate", self._group_update),
            ("groupDestroy", self._group_destroy),
            ("performerDestroy", self._performer_destroy),
            ("tagUpdate", self._tag_update),
            ("tagsMerge", self._tags_merge),
            ("configurePlugin", self._configure),
            ("sceneUpdate", self._scene_update),
            ("performerUpdate", self._performer_update),
        ):
            if nom in requete:
                self._note(nom, json.dumps(variables)[:80])
                return action(variables)
        # Lectures
        if "findStudios" in requete:
            self._note("findStudios")
            return {"findStudios": {
                "studios": [copy.deepcopy(s)
                            for s in self.studios.values()]}}
        if "findGroups" in requete:
            self._note("findGroups")
            return {"findGroups": {
                "count": len(self.groups),
                "groups": [copy.deepcopy(g)
                           for g in self.groups.values()]}}
        # Stash expose la langue de son interface : le plugin s'en
        # sert comme défaut, plutôt que d'exiger un second réglage.
        if "interface" in requete and "language" in requete:
            self._note("configuration")
            return {"configuration": {"interface": {
                "language": getattr(self, "interface_language",
                                    "en-GB")}}}
        if "findScenes" in requete:
            self._note("findScenes")
            # Stash renvoie le NOM des interprètes et studios liés, pas
            # seulement leur identifiant. Sans lui, tout calcul de
            # statistiques tombait — et le test aurait accusé le code.
            scenes = []
            for sc in self.scenes.values():
                sc = copy.deepcopy(sc)
                sc["performers"] = [
                    {"id": str(q["id"]),
                     "name": q.get("name")
                     or (self.performers.get(str(q["id"])) or {})
                     .get("name", "")}
                    for q in (sc.get("performers") or [])]
                if sc.get("studio") and not sc["studio"].get("name"):
                    sid = str(sc["studio"].get("id"))
                    sc["studio"]["name"] = (
                        self.studios.get(sid) or {}).get("name", "")
                scenes.append(sc)
            # Le filtre par interprète est HONORÉ : sans cela, une
            # fusion réécrirait les interprètes de toutes les scènes,
            # et le test ne prouverait rien sur celles qui ne sont pas
            # concernées.
            ids = variables.get("ids")
            if ids and "performers" in requete:
                voulus = {str(x) for x in ids}
                scenes = [s for s in scenes
                          if voulus & {str(q["id"])
                                       for q in (s.get("performers")
                                                 or [])}]
            tid = variables.get("tid")
            if tid and "tags" in requete:
                voulus = {str(x) for x in tid}
                scenes = [s for s in scenes
                          if voulus & {str(t["id"])
                                       for t in (s.get("tags") or [])}]
            # Le filtre par studio emploie le MÊME nom de variable
            # que celui par interprète : c'est le mot présent dans la
            # requête qui les distingue.
            if ids and "studios" in requete:
                voulus = {str(x) for x in ids}
                scenes = [s for s in scenes
                          if str((s.get("studio") or {}).get("id"))
                          in voulus]
            return {"findScenes": {"count": len(scenes),
                                   "scenes": scenes}}
        if "findStudio" in requete:
            self._note("findStudio")
            sid = str(variables.get("id"))
            return {"findStudio": copy.deepcopy(self.studios.get(sid))}
        if "findScene" in requete:
            self._note("findScene")
            sid = str(variables.get("id"))
            return {"findScene": copy.deepcopy(self.scenes.get(sid))}
        if "findTags" in requete:
            self._note("findTags")
            return {"findTags": {"tags": [copy.deepcopy(t)
                                          for t in self.tags.values()]}}
        raise AssertionError(
            f"requête non prévue par le faux serveur : "
            f"{requete.strip()[:90]}")

    # ── implémentations des mutations ────────────────────────────────
    def _studio_update(self, v):
        e = v.get("input", {})
        sid = str(e.get("id"))
        st = self.studios.setdefault(sid, {"id": sid})
        for champ, valeur in e.items():
            if champ == "custom_fields" and isinstance(valeur, dict):
                cf = st.setdefault("custom_fields", {})
                if "partial" in valeur:
                    cf.update(valeur["partial"])
                else:
                    st["custom_fields"] = dict(valeur)
            elif champ != "id":
                st[champ] = valeur
        return {"studioUpdate": {"id": sid}}

    def _studio_create(self, v):
        e = v.get("input", {})
        sid = self._id()
        self.studios[sid] = dict(e, id=sid)
        return {"studioCreate": {"id": sid, "name": e.get("name")}}

    def _performer_create(self, variables):
        e = (variables or {}).get("input") or {}
        pid = self._id()
        fiche = {"id": pid, "name": e.get("name"), "tags": [],
                 "alias_list": list(e.get("alias_list") or []),
                 "custom_fields": dict(e.get("custom_fields") or {})}
        self.performers[pid] = fiche
        return {"performerCreate": {"id": pid, "name": e.get("name")}}

    def _studio_destroy(self, v):
        self.studios.pop(str(v.get("id")), None)
        return {"studioDestroy": True}

    def _group_create(self, v):
        e = v.get("input", {})
        gid = self._id()
        self.groups[gid] = dict(e, id=gid, scene_count=0, aliases="")
        return {"groupCreate": {"id": gid}}

    def _group_update(self, v):
        e = v.get("input", {})
        gid = str(e.get("id"))
        g = self.groups.setdefault(gid, {"id": gid})
        g.update({k: val for k, val in e.items() if k != "id"})
        return {"groupUpdate": {"id": gid}}

    def _group_destroy(self, v):
        self.groups.pop(str(v.get("id")), None)
        return {"groupDestroy": True}

    def _performer_destroy(self, v):
        self.performers.pop(str(v.get("id")), None)
        return {"performerDestroy": True}

    def _performer_update(self, v):
        e = v.get("input", v)
        return {"performerUpdate": self._appliquer(self.performers, e)}

    def _scene_update(self, v):
        e = v.get("input", v)
        return {"sceneUpdate": self._appliquer(self.scenes, e)}

    def _tag_update(self, v):
        e = v.get("input", v)
        tid = str(e.get("id"))
        if tid in self.tags and e.get("name"):
            self.tags[tid]["name"] = e["name"]
        return {"tagUpdate": {"id": tid}}

    def _tags_merge(self, v):
        e = v.get("input", v)
        for src in e.get("source", []):
            self.tags.pop(str(src), None)
        return {"tagsMerge": {"id": str(e.get("destination"))}}

    def _configure(self, v):
        return {"configurePlugin": v.get("input", {})}


def faux_contexte(reglages=None, stash=None, args=None):
    """Contexte utilisable sans Stash ni entrée standard.

    `Context.__init__` lit `sys.stdin` et ouvre une connexion : on
    construit donc l'objet sans passer par son initialisation, puis on
    renseigne ce dont les tâches ont besoin."""
    import noyau
    ctx = noyau.Context.__new__(noyau.Context)
    ctx.stash = stash or FauxStash()
    ctx.settings = dict(reglages or {})
    ctx.args = dict(args or {})
    ctx.connexion = {}
    ctx._tags_cache = {}
    ctx._idx = None
    ctx._groupes = None
    ctx._llm_table = None
    # La table de notation est CELLE DU PLUGIN, pas une imitation :
    # tester le pipeline avec des poids inventés ne dirait rien de ce
    # qui se passe en service.
    import scoring
    ctx.cfg = scoring.DEFAUTS
    # Aucune stash-box : un test ne doit rien appeler dehors.
    ctx.stash_boxes = []
    noyau._LANGUE["code"] = ctx.lang()
    return ctx


def performer(pid, nom, **champs):
    """Fiche minimale, telle que Stash la renvoie."""
    base = {"id": str(pid), "name": nom, "tags": [], "alias_list": [],
            "custom_fields": {}, "urls": []}
    base.update(champs)
    return base


def scene(sid, titre=None, **champs):
    base = {"id": str(sid), "title": titre, "tags": [], "performers": [],
            "custom_fields": {}, "urls": [], "groups": [],
            "files": [{"basename": champs.pop("basename", "")}]}
    base.update(champs)
    return base


def studio(sid, nom, **champs):
    base = {"id": str(sid), "name": nom, "aliases": "",
            "custom_fields": {}, "scene_count": 0, "image_path": ""}
    base.update(champs)
    return base
