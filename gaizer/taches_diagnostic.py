# -*- coding: utf-8 -*-
"""
Diagnostics : regarder sans rien changer.

Ces tâches n'écrivent JAMAIS. C'est leur intérêt : on
les lance sans conséquence, pour comprendre avant d'agir.
Un rapport qui modifie la collection surprend — et le cas
s'est présenté.
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from stashapi import log
import scoring
from collecte import collecter_stash, passe_url
from noyau import (
    CHAMPS_HERITES,
    MAP,
    PERFORMER_FIELDS,
    _pause_llm_active,
    _tag_exclu,
    etat_lire,
    tag_id)
from scenes import _marquer_non_identifiee


def rapport_tags(ctx):
    """Photographie des tags de scènes : fréquences, quasi-doublons et
    tags rares — la matière pour décider d'une normalisation (aucune
    écriture)."""
    from collections import Counter
    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             tags { id name } } } }""")
    freq = Counter()
    for sc in d["findScenes"]["scenes"]:
        for t in sc.get("tags") or []:
            if not t["name"].startswith(f"{ctx.tag_prefix()}:"):
                freq[t["name"]] += 1
    log.info(f"═══ {len(freq)} tags distincts sur "
             f"{len(d['findScenes']['scenes'])} scènes ═══")
    log.info("Top 25 : " + ", ".join(f"{n} ({c})"
                                     for n, c in freq.most_common(25)))

    def plat(x):
        return re.sub(r"[^a-z0-9]", "", x.lower())

    # Quasi-doublons : forme identique, inclusion, singulier/pluriel
    noms = sorted(freq)
    suspects = []
    for i, a in enumerate(noms):
        pa = plat(a)
        for b in noms[i + 1:]:
            pb = plat(b)
            if not pa or not pb:
                continue
            if pa == pb:
                suspects.append((a, b, "identiques (casse/ponctuation)"))
            elif pa + "s" == pb or pb + "s" == pa:
                suspects.append((a, b, "singulier/pluriel"))
            elif (len(pa) >= 4 and len(pb) >= 4
                  and (pb.startswith(pa) or pa.startswith(pb))
                  and abs(len(pa) - len(pb)) <= 6):
                suspects.append((a, b, "l'un contient l'autre"))
    log.info(f"═══ {len(suspects)} quasi-doublon(s) ═══")
    for a, b, motif in suspects[:40]:
        log.info(f"  {a} ({freq[a]}) ~ {b} ({freq[b]}) — {motif}")

    rares = [(n, c) for n, c in freq.items() if c <= 2]
    log.info(f"═══ {len(rares)} tag(s) sur 1 ou 2 scènes seulement "
             f"(candidats à tagsExclude) ═══")
    log.info("  " + ", ".join(n for n, _c in sorted(rares)[:60]))
    exclus = ctx.tags_exclus()
    if exclus:
        touches = [n for n in freq if _tag_exclu(n, exclus)]
        log.info(f"Réglage tagsExclude actif : {len(touches)} tag(s) "
                 f"déjà présents seraient exclus des prochains "
                 f"passages ({', '.join(sorted(touches)[:12])})")
    log.info("Rapport des tags terminé (aucune modification).")


def _marquer_non_identifiees(ctx, a_marquer, prefix):
    """Étiquette les scènes qu'aucune source n'a reconnues.

    Le marquage rend ces scènes FILTRABLES dans Stash, ce qui est son
    seul intérêt. Mais une tâche nommée « rapport » qui étiquette
    surprend : on la lance pour REGARDER. Il faut donc le demander,
    comme partout ailleurs dans le plugin où constater et agir sont
    séparés.
    """
    # Le marquage rétroactif rend les scènes non identifiées
    # filtrables — mais une tâche nommée « rapport » qui étiquette
    # surprend : on la lance pour REGARDER. Il faut donc le demander,
    # comme partout ailleurs dans le plugin où constater et agir sont
    # séparés.
    if a_marquer and not str(ctx.args.get("marquer") or "").strip():
        log.info(f"  → {len(a_marquer)} scène(s) pourraient être "
                 f"marquées '{ctx.tag_nom('unidentified')}' pour être "
                 f"filtrables. Relancer avec « marquer=1 ».")
    elif a_marquer:
        marquees = 0
        for sc in a_marquer:
            avant = len(sc.get("tags") or [])
            _marquer_non_identifiee(ctx, sc, True)
            if len(sc.get("tags") or []) > avant:
                marquees += 1
        log.info(f"  → {marquees} scène(s) marquées "
                 f"'{ctx.tag_nom('unidentified')}' (filtrables dans "
                 f"l'UI)")


def rapport_run(ctx):
    """Bilan chiffré du dernier run + hygiène de la collection, écrit
    dans le log de la tâche. LECTURE SEULE, sauf le marquage
    rétroactif des scènes non identifiées (filtrables ensuite)."""
    prefix = ctx.tag_prefix()
    from collections import Counter

    d = ctx.stash.call_GQL(
        """{ findScenes(filter: {per_page: -1}) { scenes {
             id title date details custom_fields
             studio { id } performers { id } tags { id name } } } }""")
    scenes = d["findScenes"]["scenes"]
    n = max(1, len(scenes))
    emp = repli = rien = verif = 0
    sans_studio = sans_perf = sans_syn = 0
    tags_c = Counter()
    a_marquer = []
    for sc in scenes:
        src = str((sc.get("custom_fields") or {}).get("enrich_sources")
                  or "")
        if "NOM DE FICHIER" in src:
            repli += 1
        elif src:
            emp += 1
        else:
            rien += 1
            a_marquer.append(sc)
        noms = [t["name"] for t in sc.get("tags") or []]
        if ctx.tag_nom("verify") in noms:
            verif += 1
        for x in noms:
            if not x.startswith(f"{prefix}:"):
                tags_c[x] += 1
        if not sc.get("studio"):
            sans_studio += 1
        if not sc.get("performers"):
            sans_perf += 1
        if not (sc.get("details") or "").strip():
            sans_syn += 1

    log.info(f"═══ SCÈNES : {len(scenes)} ═══")
    log.info(f"  empreinte {emp} ({emp/n:.0%}) · repli nom de fichier "
             f"{repli} ({repli/n:.0%}) · aucune identification {rien} "
             f"({rien/n:.0%})")
    log.info(f"  sans studio {sans_studio} · sans acteurs {sans_perf} "
             f"· sans synopsis {sans_syn} · cohérence douteuse {verif}")
    log.info(f"  {len(tags_c)} tags distincts · top : "
             + ", ".join(f"{x} ({c})" for x, c in tags_c.most_common(8)))

    _marquer_non_identifiees(ctx, a_marquer, prefix)

    perfs = ctx.stash.find_performers()
    p_cree = p_enr = p_hot = p_photo = p_doub = p_conf = 0
    hot_pauvres = []
    cree_vides = []
    sans_scene = []

    for pf in perfs:
        noms = [t["name"] for t in pf.get("tags") or []]
        cf = pf.get("custom_fields") or {}
        est_cree = ctx.tag_nom("created") in noms
        p_cree += est_cree
        if cf.get("enrich_sources"):
            p_enr += 1
        elif est_cree:
            cree_vides.append(pf["name"])
        if cf.get("bio_hot"):
            p_hot += 1
            try:
                if not json.loads(cf.get("reco_data")
                                  or "{}").get("partenaires"):
                    hot_pauvres.append(pf["name"])
            except Exception as exc:
                log.debug(f"opération : {exc}")
        if "default=true" not in (pf.get("image_path") or ""):
            p_photo += 1
        if ctx.tag_nom("duplicate") in noms:
            p_doub += 1
        if str(cf.get("enrich_rapport") or "").startswith("CONFLITS"):
            p_conf += 1
        try:
            if not json.loads(cf.get("reco_data") or "{}").get("scenes"):
                sans_scene.append(pf["name"])
        except Exception as exc:
            log.debug(f"opération : {exc}")

    log.info(f"═══ PERFORMERS : {len(perfs)} ═══")
    log.info(f"  créés {p_cree} · enrichis {p_enr} · avec photo "
             f"{p_photo} · bios hot {p_hot}")
    log.info(f"  conflits signalés {p_conf} · doublons en attente "
             f"{p_doub}")
    if hot_pauvres:
        log.info(f"  ⚠ {len(hot_pauvres)} bio(s) hot sans partenaire "
                 f"(générées avant liaison des scènes) — tâche "
                 f"« Régénérer les bios hot »")
    if cree_vides:
        log.info(f"  ⚠ {len(cree_vides)} fiche(s) créées jamais "
                 f"enrichies : " + ", ".join(cree_vides[:8]))

    d = ctx.stash.call_GQL(
        """{ findStudios(filter: {per_page: -1}) { studios {
             id name details url parent_studio { id }
             custom_fields } } }""")
    studios = d["findStudios"]["studios"]
    st_cree = sum(1 for x in studios
                  if (x.get("custom_fields") or {}).get("enrich_cree"))
    st_enr = sum(1 for x in studios
                 if (x.get("custom_fields") or {}).get("enrich_sources"))
    st_par = sum(1 for x in studios if x.get("parent_studio"))
    st_url = sum(1 for x in studios if (x.get("url") or "").strip())
    log.info(f"═══ STUDIOS : {len(studios)} ═══")
    log.info(f"  créés {st_cree} · enrichis {st_enr} · avec parent "
             f"{st_par} · avec url {st_url}")
    log.info("Rapport terminé.")


def etat_agent(ctx):
    """État lisible de l'agent : santé du fournisseur d'IA, pause
    éventuelle et sa date de reprise, volume de travail en attente."""
    e = etat_lire()
    jusqu = _pause_llm_active()
    log.info("═══ Agent d'enrichissement — état ═══")
    log.info(f"  mode d'application : {ctx.apply_mode()} · seuil "
             f"{ctx.auto_threshold()}/10 · lot {ctx.batch()}")
    ai = ctx.ai_for("bio")
    log.info("  IA configurée : "
             + (f"{ai[0]} / {ai[1] or 'modèle par défaut'}" if ai
                else "aucune (les textes ne seront pas générés)"))
    if jusqu:
        log.error(f"  ⏸ GÉNÉRATIONS EN PAUSE jusqu'au {jusqu} — motif : "
                  f"{e.get('pause_motif')}")
        log.info(f"     Posée le {e.get('pause_posee_le')}. Reprise "
                 f"automatique au premier passage suivant cette date ; "
                 f"« Reprendre les générations IA » pour forcer.")
    else:
        log.info("  ✓ générations IA actives")
    inc = e.get("dernier_incident") or {}
    if inc:
        log.info(f"  dernier incident IA : {inc.get('message')} "
                 f"(le {inc.get('date')}, {inc.get('fournisseur')}"
                 + (f", HTTP {inc.get('http')}" if inc.get("http")
                    else "") + ")")
    # Travail en attente
    perfs = ctx.stash.find_performers()
    att_hot = sum(1 for x in perfs
                  if (x.get("custom_fields") or {}).get("reco_data")
                  and not str((x.get("custom_fields") or {})
                              .get("bio_hot") or "").strip())
    att_bio = sum(1 for x in perfs if not (x.get("details") or "").strip())
    en_echec = [x for x in perfs
                if (x.get("custom_fields") or {}).get("enrich_ia")]
    log.info(f"  en attente : {att_hot} bio(s) hot · {att_bio} bio(s) "
             f"factuelle(s) · {len(en_echec)} fiche(s) portant une "
             f"explication d'échec (champ enrich_ia)")
    if e.get("derniere_reprise"):
        log.info(f"  dernière reprise programmée exécutée : "
                 f"{e['derniere_reprise']}")
    log.info("═══════════════════════════════════")


def position_tags(ctx):
    """Convertit le champ custom `position` (hérité) en TAG STANDARD
    Stash sur chaque performer — idempotent, filtrable dans l'UI."""
    n = 0
    for p in ctx.stash.find_performers():
        pos = ((p.get("custom_fields") or {}).get("position")
               or "").strip()
        if not pos:
            continue
        tid = tag_id(ctx, pos)
        tids = {t["id"] for t in p.get("tags", [])}
        if tid in tids:
            continue
        ctx.stash.update_performer({"id": p["id"],
                                    "tag_ids": list(tids | {tid})})
        n += 1
    log.info(f"{n} performer(s) taggés avec leur position "
             f"(tags standards Stash).")


def controler_heritage(ctx):
    """Confronte les champs hérités d'un import aux valeurs arbitrées.

    Un import laisse des champs personnalisés que le plugin ne relit
    jamais : ils survivent à côté des valeurs qu'il a établies, et rien
    ne signale qu'ils disent le contraire. Le risque n'est pas
    théorique — la présentation d'une fiche affirmait « coupé » quand
    les sources disaient l'inverse, parce que le modèle avait repris le
    champ hérité.

    Aucune écriture : le rapport dit ce qui diverge, la décision
    revient à l'utilisateur — un import peut très bien être plus juste
    que les sources."""
    perfs = ctx.stash.find_performers()
    divergences = []
    total_herites = 0
    for p in perfs:
        cf = p.get("custom_fields") or {}
        for herite, (officiel, table) in CHAMPS_HERITES.items():
            brut = str(cf.get(herite) or "").strip().lower()
            if not brut:
                continue
            total_herites += 1
            attendu = table.get(brut)
            actuel = str(p.get(officiel) or "").strip().lower()
            if not attendu or not actuel:
                continue
            if attendu != actuel:
                divergences.append((p["name"], herite, brut, officiel,
                                    actuel, cf.get("enrich_sources")))
    log.info(f"{total_herites} fiche(s) portent un champ hérité d'un "
             f"import.")
    if not divergences:
        log.info("Aucune divergence avec les valeurs arbitrées.")
        return
    log.error(f"{len(divergences)} divergence(s) — le champ hérité dit "
              f"le contraire des sources :")
    for nom, herite, brut, officiel, actuel, src in divergences[:30]:
        appui = ""
        for morceau in str(src or "").split(" | "):
            if officiel in morceau:
                appui = morceau.strip()[:80]
                break
        log.info(f"  {nom[:28]:30s} {herite}={brut:8s} vs "
                 f"{officiel}={actuel}")
        if appui:
            log.info(f"      sources : {appui}")
    if len(divergences) > 30:
        log.info(f"  … et {len(divergences) - 30} autre(s).")
    log.info("Rien n'a été modifié. Un import peut être plus juste que "
             "les sources : à vous de trancher. Les présentations "
             "rédigées avant la 0.40 ont pu reprendre le champ hérité "
             "— les régénérer après correction.")


def inspecter_collecte(ctx):
    """Montre TOUT ce que les sources disent d'une fiche, et pourquoi
    chaque valeur a été retenue ou non.

    Le plugin n'écrit que dans les champs vides. Vu de l'extérieur, une
    fiche déjà remplie ne reçoit qu'une ou deux valeurs et l'on peut
    croire que la collecte n'a rien trouvé — alors qu'elle a interrogé
    sept sources et récolté huit champs. Cette tâche lève l'ambiguïté :
    elle distingue ce qui n'a pas été collecté de ce qui l'a été sans
    être écrit.

    Argument `performer_id`, ou `nom` pour désigner la fiche.
    Aucune écriture."""
    ident = str(ctx.args.get("performer_id") or "").strip()
    nom = str(ctx.args.get("nom") or "").strip()
    if not ident and not nom:
        log.error("préciser « performer_id » ou « nom ».")
        return
    perfs = ctx.stash.find_performers()
    if ident:
        fiche = next((x for x in perfs if str(x["id"]) == ident), None)
    else:
        bas = nom.lower()
        fiche = next((x for x in perfs
                      if (x.get("name") or "").lower() == bas), None)
        if not fiche:
            fiche = next((x for x in perfs
                          if bas in (x.get("name") or "").lower()), None)
    if not fiche:
        log.error("fiche introuvable.")
        return

    log.info(f"═══ {fiche['name']} (id {fiche['id']}) ═══")
    raw, urls = collecter_stash(ctx, fiche["name"])
    depuis_url = passe_url(ctx, fiche, urls) or {}
    for src, vals in depuis_url.items():
        raw.setdefault(src, {}).update(vals)

    if not raw:
        log.warning("aucune source n'a répondu — vérifier les "
                    "stash-boxes et les scrapers configurés.")
        return
    log.info(f"{len(raw)} source(s) ont répondu : "
             f"{', '.join(sorted(raw))}")

    # Ce que le plugin sait chercher, indépendamment des réponses.
    attendus = sorted(PERFORMER_FIELDS)
    inverse = {v: k for k, v in MAP.items()}
    log.info(f"═══ Les {len(attendus)} champs recherchés ═══")

    cfg = ctx.cfg or scoring.charger_config(
        str(Path(__file__).resolve().parent))
    for champ_stash in attendus:
        # Les sources nomment certains champs autrement que Stash.
        champ_src = inverse.get(champ_stash, champ_stash)
        valeurs = {s2: v.get(champ_src) for s2, v in raw.items()
                   if v.get(champ_src) not in (None, "", [], {})}
        actuel = fiche.get(champ_stash)
        rempli = actuel not in (None, "", [], {})

        if not valeurs:
            log.info(f"  {champ_stash:16s} — aucune source ne le "
                     f"fournit" + (f" · fiche : « {actuel} »"
                                   if rempli else ""))
            continue

        cands = scoring.evaluer(champ_src, valeurs, cfg)
        meilleur = cands[0] if cands else None
        detail = (f"{meilleur['valeur']} ({meilleur['note']}/10 · "
                  f"{'+'.join(meilleur['sources'])})"
                  if meilleur else "aucun candidat retenu")
        if not rempli:
            etat = "VIDE → serait écrit"
        elif meilleur and str(meilleur["valeur"]).strip().lower() == \
                str(actuel).strip().lower():
            etat = "déjà rempli, identique"
        else:
            etat = f"déjà rempli « {actuel} » → CONFLIT, non écrasé"
        log.info(f"  {champ_stash:16s} {len(valeurs)} source(s) · "
                 f"{etat}")
        log.info(f"      retenu : {detail}")
        if meilleur and meilleur.get("commentaires"):
            for c in meilleur["commentaires"][:2]:
                log.info(f"      {c}")
        if len(cands) > 1:
            autres = " · ".join(
                f"{c['valeur']} ({c['note']}/10, "
                f"{'+'.join(c['sources'])})" for c in cands[1:4])
            log.info(f"      écartés : {autres}")

    log.info("═══ Lecture ═══")
    log.info("  « VIDE → serait écrit » : la valeur manque et serait "
             "ajoutée.")
    log.info("  « déjà rempli, identique » : la collecte confirme ce "
             "qui est là.")
    log.info("  « CONFLIT » : les sources disent autre chose ; rien "
             "n'est écrasé, le désaccord est reporté sur la fiche.")
    log.info("  « aucune source ne le fournit » : la collecte a bien "
             "eu lieu, ce champ n'existe simplement nulle part.")


def sante_sources(ctx):
    """Interroge chaque source configurée et dit laquelle répond.

    Aucun test unitaire ne détectera qu'une source a CHANGÉ DE FORMAT
    ou cessé de répondre : les tests vérifient que le plugin fait ce
    qu'il dit, pas que le monde extérieur est resté le même. Si StashDB
    renomme un champ ou qu'un scraper meurt, la suite reste verte
    pendant que la collecte ramène du vide.

    Cette tâche comble cet angle mort par des appels RÉELS. Elle ne
    juge pas la justesse des données — elle dit si le tuyau est ouvert,
    et quels champs en sortent encore.

    Argument `noms` : fiches à interroger, séparées par des virgules.
    À défaut, trois interprètes bien documentés de la collection.
    """
    demandes = [n.strip() for n in
                str(ctx.args.get("noms") or "").split(",") if n.strip()]
    if not demandes:
        # Des fiches déjà bien renseignées : si une source ne répond
        # rien sur celles-là, c'est qu'elle ne répond plus du tout.
        perfs = ctx.stash.find_performers()
        classees = sorted(
            (p for p in perfs if len((p.get("name") or "").split()) >= 2),
            key=lambda p: -len(str((p.get("custom_fields") or {})
                                   .get("enrich_sources") or "")))
        demandes = [p["name"] for p in classees[:3]]
    if not demandes:
        log.warning("aucune fiche à interroger.")
        return

    log.info(f"═══ Interrogation réelle sur {len(demandes)} fiche(s) "
             f"═══")
    par_source = {}
    for nom in demandes:
        try:
            raw, _urls = collecter_stash(ctx, nom)
        except Exception as exc:
            log.error(f"  {nom} : {str(exc)[:90]}")
            continue
        log.info(f"  {nom} — {len(raw)} source(s)")
        for src, vals in raw.items():
            utiles = {k for k, v in vals.items()
                      if v not in (None, "", [], {})}
            e = par_source.setdefault(src, {"fiches": 0, "champs": set()})
            e["fiches"] += 1
            e["champs"] |= utiles

    if not par_source:
        log.error("AUCUNE source n'a répondu. Vérifier les stash-boxes "
                  "et les scrapers dans les réglages de Stash.")
        return

    log.info("═══ Ce que chaque source fournit encore ═══")
    for src in sorted(par_source, key=lambda s2: -par_source[s2]["fiches"]):
        e = par_source[src]
        log.info(f"  {src:26s} {e['fiches']}/{len(demandes)} fiche(s) · "
                 f"{', '.join(sorted(e['champs'])) or 'AUCUN CHAMP'}")

    # Ce que le plugin sait exploiter, et qui ne vient plus de nulle part.
    couverts = set()
    for e in par_source.values():
        couverts |= e["champs"]
    inverse = {v: k for k, v in MAP.items()}
    manquants = sorted(
        c for c in PERFORMER_FIELDS
        if inverse.get(c, c) not in couverts and c not in couverts)
    if manquants:
        log.warning(f"Champs qu'AUCUNE source ne fournit plus : "
                    f"{', '.join(manquants)}")
        log.info("  Soit ces fiches ne les documentent pas, soit une "
                 "source a changé de format. Relancer sur d'autres "
                 "noms pour trancher.")
    else:
        log.info("Tous les champs recherchés sont couverts par au "
                 "moins une source.")

    muettes = [s2 for s2, e in par_source.items() if not e["champs"]]
    if muettes:
        log.warning(f"Source(s) qui répondent sans rien fournir : "
                    f"{', '.join(muettes)}")

def prompt_defaut(ctx):
    """Écrit le prompt par défaut dans l'état, pour que le panneau
    puisse l'afficher.

    La zone de saisie vide n'apprenait rien : on ne savait ni ce que
    le plugin demande au modèle, ni comment formuler autre chose. Le
    montrer donne un point de départ — on part de ce qui marche.

    Le recopier dans le JavaScript le ferait diverger du prompt
    réellement employé, sans que rien ne le signale.
    """
    textes = {
        "biohot": ctx.t("prompt_biohot"),
        "biohot_consignes": ctx.t("prompt_biohot_consignes"),
    }
    log.info("Prompt par défaut (langue : " + ctx.lang() + ")")
    for cle, texte in textes.items():
        log.info(f"  --- {cle} ---")
        log.info(str(texte))
    # L'état vit dans un FICHIER, que le panneau ne peut pas lire :
    # il passe par GraphQL. Le prompt est donc déposé dans un réglage,
    # seul canal commun aux deux.
    try:
        cfg = ctx.stash.call_GQL("{ configuration { plugins } }")
        table = dict((cfg["configuration"]["plugins"] or {})
                     .get("gaizer") or {})
        table["promptDefautReleve"] = textes["biohot"]
        ctx.stash.call_GQL(
            "mutation($i: Map!) { configurePlugin("
            "plugin_id: \"gaizer\", input: $i) }", {"i": table})
        log.info("  Le panneau « Textes générés » peut désormais "
                 "l'afficher.")
    except Exception as exc:
        log.debug(f"prompt non déposé : {str(exc)[:70]}")
