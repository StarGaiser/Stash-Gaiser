# -*- coding: utf-8 -*-
"""
i18n.py — libellés, étiquettes et messages d'Gaizer.

Organisation : un bloc par langue. Ajouter une langue = copier le bloc
anglais, traduire, déclarer le code dans LANGUES. Toute chaîne absente
retombe sur l'anglais, puis sur la clé : une traduction partielle
n'empêche jamais le plugin de fonctionner.

Quatre familles de chaînes :
  TAGS      suffixes des tags posés dans Stash (visibles partout)
  BOUTONS   libellés des boutons injectés dans les pages
  TACHES    noms des tâches (Settings → Tasks)
  REGLAGES  libellés des réglages (Settings → Plugins)
  MSG       messages écrits sur les fiches et dans le journal

Les DESCRIPTIONS longues (tâches et réglages) sont fournies en anglais
et en français ; les autres langues affichent l'anglais. Ce choix est
délibéré : un libellé court mal traduit gêne, un paragraphe en anglais
reste compréhensible et évite une maintenance disproportionnée.
"""

from __future__ import annotations

DEFAUT = "en"

LANGUES = {
    "en": {"nom": "English", "llm": "English"},
    "fr": {"nom": "Français", "llm": "français"},
    "de": {"nom": "Deutsch", "llm": "Deutsch"},
    "es": {"nom": "Español", "llm": "español"},
    "it": {"nom": "Italiano", "llm": "italiano"},
    "pt": {"nom": "Português", "llm": "português"},
    "nl": {"nom": "Nederlands", "llm": "Nederlands"},
}

_ALIAS = {
    "french": "fr", "français": "fr", "francais": "fr",
    "english": "en", "anglais": "en",
    "german": "de", "deutsch": "de", "allemand": "de",
    "spanish": "es", "español": "es", "espanol": "es",
    "espagnol": "es",
    "italian": "it", "italiano": "it", "italien": "it",
    "portuguese": "pt", "português": "pt", "portugues": "pt",
    "portugais": "pt",
    "dutch": "nl", "nederlands": "nl", "néerlandais": "nl",
    "neerlandais": "nl",
}


def code_langue(valeur) -> str:
    """Accepte « fr », « FR », « français », « French »…"""
    v = str(valeur or "").strip().lower()
    if v in LANGUES:
        return v
    return _ALIAS.get(v, DEFAUT)


# =====================================================================
#  ANGLAIS — référence. Toute clé doit exister ici.
# =====================================================================
EN = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "created", "verify": "verify",
        "duplicate": "duplicate?", "not_duplicate": "not-duplicate",
        "merge": "merge", "restore": "restore",
        "unidentified": "unidentified",
    },
    "boutons": {
        "enrichir": "Enrich", "accepter": "Accept",
        "pas_doublon": "Not a duplicate", "fusionner": "Merge",
        "verifie": "Checked", "restaurer": "Restore",
        "titre": "Gaizer — actions on this page",
        "confirm": "Merge « {nom} » into its twin? "
                   "This entry will be deleted.",
    },
    "taches": {
        "enrich_performers": "Enrich incomplete performers",
        "enrich_scenes": "Enrich incomplete scenes",
        "enrich_studios": "Enrich incomplete studios",
        "apply_accepted": "Apply accepted proposals",
        "apply_accepted_scenes": "Apply accepted scenes",
        "apply_accepted_studios": "Apply accepted studios",
        "apply_recommended": "Apply recommendations (bulk)",
        "apply_covers": "Apply official covers",
        "detect_duplicates": "Detect probable duplicates",
        "detect_duplicates_studios": "Detect duplicate studios",
        "merge_marked": "Merge marked duplicates",
        "merge_marked_studios": "Merge marked studios",
        "dedoublonnage_complet": "Full deduplication "
                                 "(performers + studios)",
        "restore_marked": "Restore marked entities",
        "regenerate_biohot": "Regenerate hot bios",
        "position_tags": "Position → standard tags",
        "rapport_run": "Run report and hygiene",
        "rapport_tags": "Tag report",
        "etat_agent": "Agent status",
        "reprendre_ia": "Resume AI generation",
        "migrer_langue": "Switch plugin language",
        "clear_proposals": "Clear proposals",
        "enrich_one_performer": "Enrich one performer",
        "enrich_one_scene": "Enrich one scene",
        "enrich_one_studio": "Enrich one studio",
        "restaurer_reglages": "Restore settings",
        "purger_tags_exclus": "Remove excluded tags",
        "detect_groupes": "Rebuild multi-part movies",
        "suggerer_tags_exclus": "Suggest tags to exclude",
        "normaliser_roles": "Normalise positions and roles",
        "retirer_pied_bio": "Remove biography footer",
        "deduire_roles": "Suggest positions and roles (AI)",
        "controler_heritage": "Check fields inherited from an import",
        "ranger_champs_herites": "Tidy fields inherited from an import",
        "retirer_non_confirme": "Remove values with no source backing",
        "retirer_champ_herite": "Delete an inherited field",
        "marquer_roles_importes": "Mark imported roles as suggested",
        "inspecter_collecte": "Inspect what sources say about a performer",
        "arbitrer_conflits": "Align conflicts with the sources",
        "sante_sources": "Check the health of the sources",
        "proposer_scrapers": "Suggest missing scrapers",
        "lire_vignettes": "Read watermarks on thumbnails",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Apply mode (manual / seuil / auto)",
        "autoAcceptThreshold": "Bulk approval threshold (score /10)",
        "strongMergeThreshold": "Strong merge threshold "
                                "(full deduplication)",
        "annotateBio": "« Data reliability » bio footer",
        "language": "Plugin language (en, fr, de, es, it, pt, nl)",
        "dryRun": "Simulation mode (no writes)",
        "maxLlmCalls": "AI call cap per task (0 = unlimited)",
        "llmDelayMs": "Delay between AI calls (milliseconds)",
        "applySceneCovers": "Prefer official covers",
        "applyImages": "Apply images from sources",
        "positionAsTag": "Position as a standard tag",
        "createMissing": "Create unknown entities (scenes)",
        "groupMinScenes": "Minimum parts to create a group",
        "batchSize": "Task batch size",
        "autoInstallScrapers": "Install missing scrapers",
        "scraperSource": "Scraper catalogue",
        "visionEnvoiImages": "Send thumbnails to the vision model",
        "aiVision": "AI for reading images (provider:model)",
        "visionPrompt": "Vision — prompt instructions",
        "tagProfile": "Collection profile (optional)",
        "tagsExclude": "Tags never to apply (comma separated)",
        "refreshDays": "Data freshness (days, 0 = never)",
        "generateBioHot": "Generate the hot bio",
        "biohotPrompt": "Hot bio — prompt instructions",
        "biohotTemperature": "Hot bio — temperature (0.0-1.5)",
        "autoMergeDuplicates": "Auto-merge safe duplicates",
        "proposalTagPrefix": "Prefix of the plugin's tags",
        "useUrlPass": "URL pass (per-URL scrapers)",
        "useExtraSources": "Extra sources (Wikipedia, ADE)",
        "useStashBoxes": "Use the configured stash-boxes",
        "scrapersExclude": "Scrapers to exclude",
        "aiDefault": "Default AI (provider:model)",
        "aiBio": "AI for factual bios",
        "aiSynopsis": "AI for scene synopses",
        "aiBiohot": "AI for the hot bio",
        "mistralApiKey": "Mistral API key",
        "openaiApiKey": "OpenAI API key",
        "anthropicApiKey": "Anthropic API key",
        "llmApiKey": "Generic API key (any provider)",
        "openrouterApiKey": "OpenRouter API key",
        "groqApiKey": "Groq API key",
        "deepseekApiKey": "DeepSeek API key",
        "googleApiKey": "Google (Gemini) API key",
        "lmstudioUrl": "LM Studio address",
        "perplexityApiKey": "Perplexity API key",
        "togetherApiKey": "Together API key",
        "xaiApiKey": "xAI API key",
        "llamacppUrl": "llama.cpp address",
        "vllmUrl": "vLLM address",
        "scrapersList": "Performer scrapers to use",
        "ollamaUrl": "Ollama address",
    },
    "msg": {
        "prompt_vision": (
            "Read the TEXT visible on this image: studio watermark, "
            "logo, web address, on-screen title. Do NOT describe the "
            "people, do NOT guess who they are — only report what is "
            "WRITTEN. If no text is legible, answer null. Reply ONLY "
            "with JSON: {\"studio\": name read or null, \"texte_lu\": "
            "[exact strings read], \"confiance\": 0.0 to 1.0}"),
        "prompt_donnees": "DATA :",
        "prompt_biohot": (
            "Write in {langue} the explicit bio of gay porn performer "
            "'{nom}' for a private adult library. Direct, unabashedly "
            "crude tone, 3 to 4 sentences (450 characters max): "
            "fucking style, position, equipment, recurring partners "
            "and studios in the collection. ABSOLUTE RULE: rely ONLY "
            "on the data below; infer NEITHER practice (raw, fetish…) "
            "NOR position NOR any trait not explicitly present. If "
            "the material is thin, be brief rather than invent. Reply "
            "with the bio only."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTATION: write no title, no name at the start, "
            "no asterisks, no markup — the name already appears above "
            "the text, and markup shows up as is. Write sentences "
            "only."),
        "prompt_roles": (
            "Examine the documentation of a performer to find an "
            "EXPLICIT mention of their usual sexual role. ABSOLUTE "
            "RULE: answer only if the text states it clearly. Infer "
            "NOTHING from build, orientation, nationality, studio, "
            "scene type or general impression. This is a real person: "
            "a guess would be an error, not an approximation. When in "
            "doubt, answer null — saying nothing is the right answer "
            "most of the time. Reply ONLY with a JSON object, no "
            "surrounding text."),
        "prompt_synopsis": (
            "Write in {langue} a factual synopsis of scene '{nom}' (2 "
            "sentences max), inventing nothing. Reply with the "
            "synopsis only.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Write in {langue} a factual presentation of studio "
            "'{nom}' (3 sentences max), inventing nothing. Reply with "
            "the text only.\n\n{donnees}"),
        "prompt_bio": (
            "From this multi-source data about performer '{nom}', "
            "write ONE factual bio in {langue} (300 characters max), "
            "inventing nothing. Reply with the bio only.\n\n{donnees}"),
        "conflits": "CONFLICTS (nothing was overwritten): {details}",
        "conflit_ligne": "{champ}: current « {actuel} » vs sources: "
                         "{propose}",
        "doublon_probable": "PROBABLE DUPLICATE of: {jumeaux} — use "
                            "the « Merge » or « Not a duplicate » "
                            "buttons on this page",
        "doublon_perf": "probable duplicate of: {jumeaux} — if wrong, "
                        "add the tag {tag} and run the detection again",
        "par_nom_fichier": "identified from the FILE NAME (no "
                           "fingerprint, lower confidence)",
        "coherence_fichier": "file name match {score} ({detail})",
        "coherence_nulle": "⚠ the file name does not match the "
                           "identification — please check",
        "fusion_trace": "merged duplicate « {nom} » (id {id}) on {date}",
        "restaure_trace": "restored on {date} (pass of {passage})",
        "bio_hot_echec": "hot bio not generated — {motif} ({date})",
        "pied_bio": "― Data reliability (Gaizer) ―",
        "pied_bio_intro": "Filled in automatically on {date} — "
                          "score /10 = estimated source reliability.",
        "accepter_studio": " — « Accept » button on this page, then "
                           "run the « Apply accepted studios » task",
        "ia_quota": "AI account quota or credit exhausted",
        "ia_debit": "AI provider rate limit reached (too many "
                    "requests)",
        "ia_cle": "API key rejected by the AI provider",
        "ia_modele": "AI model unknown or retired by the provider",
        "ia_requete": "request too long for the model",
        "ia_indispo": "AI service saturated — temporarily unavailable",
        "ia_reseau": "no network access to the AI provider",
        "ia_timeout": "the AI provider did not answer in time",
        "ia_inattendu": "unexpected error from the AI provider",
        "ia_indisponible": "AI unavailable — {motif}",
        "ia_suspendue": "AI SUSPENDED: {motif}. Text generation is "
                        "rescheduled for {date}; factual enrichment "
                        "continues. Run the « Agent status » task for "
                        "details.",
        "ia_en_pause": "AI generation paused until {date} ({motif}) — "
                       "factual data is still being enriched",
        "ia_reprise": "AI generation resumed: the pause set on {pose} "
                      "({motif}) expired on {date}. Pending work will "
                      "be picked up by the enrichment tasks.",
        "plafond_ia": "limit of {max} AI call(s) reached (maxLlmCalls "
                      "setting) — further generations are skipped, "
                      "run the task again to continue",
        "simulation_active": "SIMULATION MODE on: nothing will be "
                             "written to Stash.",
        "simulation_evite": "  [SIMULATION] {op} skipped: {details}",
    },
}

# =====================================================================
#  FRANÇAIS
# =====================================================================
FR = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "créé", "verify": "verifier",
        "duplicate": "doublon?", "not_duplicate": "pas-doublon",
        "merge": "fusionner", "restore": "restaurer",
        "unidentified": "non-identifiée",
    },
    "boutons": {
        "enrichir": "Enrichir", "accepter": "Accepter",
        "pas_doublon": "Pas un doublon", "fusionner": "Fusionner",
        "verifie": "Vérifié", "restaurer": "Restaurer",
        "titre": "Gaizer — actions sur cette fiche",
        "confirm": "Fusionner « {nom} » dans son jumeau ? "
                   "Cette fiche sera supprimée.",
    },
    "taches": {
        "enrich_performers": "Enrichir les performers incomplets",
        "enrich_scenes": "Enrichir les scènes incomplètes",
        "enrich_studios": "Enrichir les studios incomplets",
        "apply_accepted": "Appliquer les propositions acceptées",
        "apply_accepted_scenes": "Appliquer les scènes acceptées",
        "apply_accepted_studios": "Appliquer les studios acceptés",
        "apply_recommended": "Appliquer les recommandations (masse)",
        "apply_covers": "Appliquer les covers officielles",
        "detect_duplicates": "Détecter les doublons probables",
        "detect_duplicates_studios": "Détecter les doublons de studios",
        "merge_marked": "Fusionner les doublons marqués",
        "merge_marked_studios": "Fusionner les studios marqués",
        "dedoublonnage_complet": "Dédoublonnage complet "
                                 "(performers + studios)",
        "restore_marked": "Restaurer les entités marquées",
        "regenerate_biohot": "Régénérer les bios hot",
        "position_tags": "Position → tags standards",
        "rapport_run": "Rapport de run et hygiène",
        "rapport_tags": "Rapport des tags",
        "etat_agent": "État de l'agent",
        "reprendre_ia": "Reprendre les générations IA",
        "migrer_langue": "Basculer la langue du plugin",
        "clear_proposals": "Nettoyer les propositions",
        "enrich_one_performer": "Enrichir un performer",
        "enrich_one_scene": "Enrichir une scène",
        "enrich_one_studio": "Enrichir un studio",
        "restaurer_reglages": "Restaurer les réglages",
        "purger_tags_exclus": "Retirer les tags exclus",
        "detect_groupes": "Reconstituer les films en plusieurs parties",
        "suggerer_tags_exclus": "Suggérer des tags à exclure",
        "normaliser_roles": "Normaliser les positions et rôles",
        "retirer_pied_bio": "Retirer le pied de biographie",
        "deduire_roles": "Suggérer les positions et rôles (IA)",
        "controler_heritage": "Contrôler les champs hérités d'un import",
        "ranger_champs_herites": "Ranger les champs hérités d'un import",
        "retirer_non_confirme": "Retirer les valeurs qu'aucune source n'appuie",
        "retirer_champ_herite": "Supprimer un champ hérité",
        "marquer_roles_importes": "Marquer les rôles importés comme suggérés",
        "inspecter_collecte": "Inspecter la collecte d'une fiche",
        "arbitrer_conflits": "Aligner les conflits sur les sources",
        "sante_sources": "Vérifier l'état des sources",
        "proposer_scrapers": "Proposer les scrapers manquants",
        "lire_vignettes": "Lire les filigranes des vignettes",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Mode d'application (manual / seuil / auto)",
        "autoAcceptThreshold": "Seuil de validation de masse "
                               "(note /10)",
        "strongMergeThreshold": "Seuil fort de fusion "
                                "(dédoublonnage complet)",
        "annotateBio": "Pied de bio « Fiabilité des données »",
        "language": "Langue du plugin (fr, en, de, es, it, pt, nl)",
        "dryRun": "Mode simulation (aucune écriture)",
        "maxLlmCalls": "Plafond d'appels à l'IA par tâche "
                       "(0 = illimité)",
        "llmDelayMs": "Espacement des appels à l'IA (millisecondes)",
        "applySceneCovers": "Privilégier les covers officielles",
        "applyImages": "Appliquer les photos des sources",
        "positionAsTag": "Position en tag standard",
        "createMissing": "Créer les entités inconnues (scènes)",
        "groupMinScenes": "Parties minimales pour constituer un groupe",
        "batchSize": "Taille de lot des tâches",
        "autoInstallScrapers": "Installer les scrapers manquants",
        "scraperSource": "Catalogue de scrapers",
        "visionEnvoiImages": "Envoyer les vignettes au modèle de vision",
        "aiVision": "IA pour la lecture d'images (fournisseur:modèle)",
        "visionPrompt": "Vision — instructions du prompt",
        "tagProfile": "Profil de collection (facultatif)",
        "tagsExclude": "Tags à ne jamais appliquer "
                       "(séparés par des virgules)",
        "refreshDays": "Fraîcheur des données (jours, 0 = jamais)",
        "generateBioHot": "Générer la bio « hot »",
        "biohotPrompt": "Bio hot — instructions du prompt",
        "biohotTemperature": "Bio hot — température (0.0-1.5)",
        "autoMergeDuplicates": "Fusion automatique des doublons sûrs",
        "proposalTagPrefix": "Préfixe des tags du plugin",
        "useUrlPass": "Passe URL (scrapers par URL)",
        "useExtraSources": "Sources d'appoint (Wikipedia, ADE)",
        "useStashBoxes": "Utiliser les stash-boxes configurées",
        "scrapersExclude": "Scrapers à exclure",
        "aiDefault": "IA par défaut (provider:modèle)",
        "aiBio": "IA pour les bios factuelles",
        "aiSynopsis": "IA pour les synopsis de scènes",
        "aiBiohot": "IA pour la bio « hot »",
        "mistralApiKey": "Clé d'API Mistral",
        "openaiApiKey": "Clé d'API OpenAI",
        "anthropicApiKey": "Clé d'API Anthropic",
        "llmApiKey": "Clé d'API générique (tout fournisseur)",
        "openrouterApiKey": "Clé d'API OpenRouter",
        "groqApiKey": "Clé d'API Groq",
        "deepseekApiKey": "Clé d'API DeepSeek",
        "googleApiKey": "Clé d'API Google (Gemini)",
        "lmstudioUrl": "Adresse de LM Studio",
        "perplexityApiKey": "Clé d'API Perplexity",
        "togetherApiKey": "Clé d'API Together",
        "xaiApiKey": "Clé d'API xAI",
        "llamacppUrl": "Adresse de llama.cpp",
        "vllmUrl": "Adresse de vLLM",
        "scrapersList": "Scrapers performer à utiliser",
        "ollamaUrl": "Adresse d'Ollama",
    },
    "msg": {
        "prompt_vision": (
            "Lis le TEXTE visible sur cette image : filigrane de "
            "studio, logo, adresse web, titre incrusté. Ne décris PAS "
            "les personnes, ne devine PAS qui elles sont — rapporte "
            "uniquement ce qui est ÉCRIT. Si aucun texte n'est "
            "lisible, réponds null. Réponds UNIQUEMENT en JSON : "
            "{\"studio\": nom lu ou null, \"texte_lu\": [chaînes "
            "exactes lues], \"confiance\": 0.0 à 1.0}"),
        "prompt_donnees": "DONNÉES :",
        "prompt_biohot": (
            "Rédige en {langue} la bio « hot » de l'acteur porno gay "
            "'{nom}' pour une médiathèque adulte privée. Ton direct "
            "et cru assumé, 3 à 4 phrases (450 caractères max) : son "
            "style de baise, sa position, son matos, ses partenaires "
            "et studios récurrents dans la collection. RÈGLE ABSOLUE "
            ": appuie-toi uniquement sur les données ci-dessous ; ne "
            "déduis NI pratique (raw, fetish…) NI position NI trait "
            "qui n'y figure pas explicitement. Si la matière est "
            "maigre, fais court plutôt que d'inventer. Réponds "
            "uniquement la bio."),
        "prompt_biohot_consignes": (
            "\n\nPRÉSENTATION : n'écris ni titre, ni nom en tête, ni "
            "astérisques, ni aucun balisage — le nom figure déjà "
            "au-dessus du texte, et le balisage s'affiche tel quel. "
            "Rédige uniquement des phrases."),
        "prompt_roles": (
            "Tu examines la documentation d'un interprète pour y "
            "repérer une mention EXPLICITE de son rôle sexuel "
            "habituel. RÈGLE ABSOLUE : ne réponds que si le texte "
            "l'indique clairement. N'infère RIEN d'une morphologie, "
            "d'une orientation, d'une nationalité, d'un studio, d'un "
            "type de scène ni d'une impression générale. Il s'agit "
            "d'une personne réelle : une supposition serait une "
            "erreur, pas une approximation. Dans le doute, réponds "
            "null — ne rien conclure est la bonne réponse la plupart "
            "du temps. Réponds UNIQUEMENT par un objet JSON, sans "
            "texte autour."),
        "prompt_synopsis": (
            "Rédige en {langue} un synopsis factuel de la scène "
            "'{nom}' (2 phrases max), sans rien inventer. Réponds "
            "uniquement le synopsis.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Rédige en {langue} une présentation factuelle du studio "
            "'{nom}' (3 phrases max), sans rien inventer. Réponds "
            "uniquement le texte.\n\n{donnees}"),
        "prompt_bio": (
            "À partir de ces données multi-sources sur l'acteur "
            "'{nom}', rédige UNE bio factuelle en {langue} (max 300 "
            "caractères), sans rien inventer. Réponds uniquement la "
            "bio.\n\n{donnees}"),
        "conflits": "CONFLITS (rien n'a été écrasé) : {details}",
        "conflit_ligne": "{champ} : actuel « {actuel} » vs "
                         "sources : {propose}",
        "doublon_probable": "DOUBLON PROBABLE de : {jumeaux} — "
                            "boutons « Fusionner » ou « Pas un "
                            "doublon » sur la fiche",
        "doublon_perf": "doublon probable de : {jumeaux} — si faux, "
                        "poser le tag {tag} et relancer la détection",
        "par_nom_fichier": "identifié par NOM DE FICHIER "
                           "(pas d'empreinte, fiabilité moindre)",
        "coherence_fichier": "cohérence fichier {score} ({detail})",
        "coherence_nulle": "⚠ le nom de fichier ne recoupe pas "
                           "l'identification — à contrôler",
        "fusion_trace": "fusion du doublon « {nom} » (id {id}) "
                        "le {date}",
        "restaure_trace": "restauré le {date} (passage du {passage})",
        "bio_hot_echec": "bio hot non générée — {motif} ({date})",
        "pied_bio": "― Fiabilité des données (Gaizer) ―",
        "pied_bio_intro": "Remplissage automatique du {date} — "
                          "note /10 = fiabilité estimée des sources.",
        "accepter_studio": " — bouton « Accepter » sur la fiche, puis "
                           "tâche « Appliquer les studios acceptés »",
        "ia_quota": "quota ou crédit du compte IA épuisé",
        "ia_debit": "limite de débit du fournisseur IA atteinte "
                    "(trop de requêtes)",
        "ia_cle": "clé d'API refusée par le fournisseur IA",
        "ia_modele": "modèle IA inconnu ou retiré chez le fournisseur",
        "ia_requete": "requête trop longue pour le modèle",
        "ia_indispo": "service IA saturé — indisponible pour le moment",
        "ia_reseau": "pas d'accès réseau au fournisseur IA",
        "ia_timeout": "le fournisseur IA n'a pas répondu à temps",
        "ia_inattendu": "erreur inattendue du fournisseur IA",
        "ia_indisponible": "IA indisponible — {motif}",
        "ia_suspendue": "IA SUSPENDUE : {motif}. Les générations de "
                        "textes sont reprogrammées au {date} ; "
                        "l'enrichissement des données factuelles "
                        "continue. Tâche « État de l'agent » pour le "
                        "détail.",
        "ia_en_pause": "générations IA en pause jusqu'au {date} "
                       "({motif}) — les données factuelles continuent "
                       "d'être enrichies",
        "ia_reprise": "Générations IA réactivées : la pause posée le "
                      "{pose} ({motif}) arrivait à échéance le {date}. "
                      "Le travail en attente sera repris par les "
                      "tâches d'enrichissement.",
        "plafond_ia": "plafond de {max} appel(s) IA atteint (réglage "
                      "maxLlmCalls) — les générations suivantes sont "
                      "sautées, relancer la tâche pour continuer",
        "simulation_active": "MODE SIMULATION actif : aucune écriture "
                             "dans Stash.",
        "simulation_evite": "  [SIMULATION] {op} évité : {details}",
    },
}

# =====================================================================
#  DEUTSCH
# =====================================================================
DE = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "erstellt", "verify": "pruefen",
        "duplicate": "duplikat?", "not_duplicate": "kein-duplikat",
        "merge": "zusammenfuehren", "restore": "wiederherstellen",
        "unidentified": "nicht-identifiziert",
    },
    "boutons": {
        "enrichir": "Anreichern", "accepter": "Übernehmen",
        "pas_doublon": "Kein Duplikat", "fusionner": "Zusammenführen",
        "verifie": "Geprüft", "restaurer": "Wiederherstellen",
        "titre": "Gaizer — Aktionen auf dieser Seite",
        "confirm": "« {nom} » mit dem Zwilling zusammenführen? "
                   "Dieser Eintrag wird gelöscht.",
    },
    "taches": {
        "enrich_performers": "Unvollständige Darsteller anreichern",
        "enrich_scenes": "Unvollständige Szenen anreichern",
        "enrich_studios": "Unvollständige Studios anreichern",
        "apply_accepted": "Angenommene Vorschläge übernehmen",
        "apply_accepted_scenes": "Angenommene Szenen übernehmen",
        "apply_accepted_studios": "Angenommene Studios übernehmen",
        "apply_recommended": "Empfehlungen übernehmen (Massenlauf)",
        "apply_covers": "Offizielle Cover übernehmen",
        "detect_duplicates": "Mögliche Duplikate erkennen",
        "detect_duplicates_studios": "Studio-Duplikate erkennen",
        "merge_marked": "Markierte Duplikate zusammenführen",
        "merge_marked_studios": "Markierte Studios zusammenführen",
        "dedoublonnage_complet": "Vollständige Bereinigung "
                                 "(Darsteller + Studios)",
        "restore_marked": "Markierte Einträge wiederherstellen",
        "regenerate_biohot": "Hot-Biografien neu erzeugen",
        "position_tags": "Position → Standard-Tags",
        "rapport_run": "Laufbericht und Hygiene",
        "rapport_tags": "Tag-Bericht",
        "etat_agent": "Agent-Status",
        "reprendre_ia": "KI-Erzeugung fortsetzen",
        "migrer_langue": "Sprache des Plugins wechseln",
        "clear_proposals": "Vorschläge aufräumen",
        "enrich_one_performer": "Einen Darsteller anreichern",
        "enrich_one_scene": "Eine Szene anreichern",
        "enrich_one_studio": "Ein Studio anreichern",
        "restaurer_reglages": "Einstellungen wiederherstellen",
        "purger_tags_exclus": "Ausgeschlossene Tags entfernen",
        "detect_groupes": "Mehrteilige Filme zusammenführen",
        "suggerer_tags_exclus": "Tags zum Ausschließen vorschlagen",
        "normaliser_roles": "Positionen und Rollen vereinheitlichen",
        "retirer_pied_bio": "Biografie-Fußzeile entfernen",
        "deduire_roles": "Positionen und Rollen vorschlagen (KI)",
        "controler_heritage": "Aus Import übernommene Felder prüfen",
        "ranger_champs_herites": "Aus Import übernommene Felder aufräumen",
        "retirer_non_confirme": "Nicht belegte Werte entfernen",
        "retirer_champ_herite": "Übernommenes Feld löschen",
        "marquer_roles_importes": "Importierte Rollen als Vorschlag markieren",
        "inspecter_collecte": "Erfassung eines Eintrags prüfen",
        "arbitrer_conflits": "Konflikte an die Quellen angleichen",
        "sante_sources": "Zustand der Quellen prüfen",
        "proposer_scrapers": "Fehlende Scraper vorschlagen",
        "lire_vignettes": "Wasserzeichen der Vorschaubilder lesen",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Anwendungsmodus (manual / seuil / auto)",
        "autoAcceptThreshold": "Schwelle für Massenübernahme (/10)",
        "strongMergeThreshold": "Starke Zusammenführungsschwelle",
        "annotateBio": "Bio-Fußzeile « Datenzuverlässigkeit »",
        "language": "Sprache des Plugins (en, fr, de, es, it, pt, nl)",
        "dryRun": "Simulationsmodus (keine Schreibvorgänge)",
        "maxLlmCalls": "Obergrenze KI-Aufrufe pro Aufgabe (0 = frei)",
        "llmDelayMs": "Abstand zwischen KI-Aufrufen (Millisekunden)",
        "applySceneCovers": "Offizielle Cover bevorzugen",
        "applyImages": "Bilder aus den Quellen übernehmen",
        "positionAsTag": "Position als Standard-Tag",
        "createMissing": "Unbekannte Einträge anlegen (Szenen)",
        "groupMinScenes": "Mindestanzahl Teile für eine Gruppe",
        "batchSize": "Stapelgröße der Aufgaben",
        "autoInstallScrapers": "Fehlende Scraper installieren",
        "scraperSource": "Scraper-Katalog",
        "visionEnvoiImages": "Vorschaubilder an das Bildmodell senden",
        "aiVision": "KI für Bildlesung (Anbieter:Modell)",
        "visionPrompt": "Vision — Anweisungen",
        "tagProfile": "Sammlungsprofil (optional)",
        "tagsExclude": "Nie zu vergebende Tags (kommagetrennt)",
        "refreshDays": "Datenaktualität (Tage, 0 = nie)",
        "generateBioHot": "Hot-Biografie erzeugen",
        "biohotPrompt": "Hot-Biografie — Prompt-Anweisungen",
        "biohotTemperature": "Hot-Biografie — Temperatur (0.0-1.5)",
        "autoMergeDuplicates": "Sichere Duplikate automatisch "
                               "zusammenführen",
        "proposalTagPrefix": "Präfix der Plugin-Tags",
        "useUrlPass": "URL-Durchlauf (URL-Scraper)",
        "useExtraSources": "Zusatzquellen (Wikipedia, ADE)",
        "useStashBoxes": "Konfigurierte Stash-Boxen verwenden",
        "scrapersExclude": "Auszuschließende Scraper",
        "aiDefault": "Standard-KI (Anbieter:Modell)",
        "aiBio": "KI für sachliche Biografien",
        "aiSynopsis": "KI für Szenen-Inhaltsangaben",
        "aiBiohot": "KI für die Hot-Biografie",
        "mistralApiKey": "Mistral API-Schlüssel",
        "openaiApiKey": "OpenAI API-Schlüssel",
        "anthropicApiKey": "Anthropic API-Schlüssel",
        "llmApiKey": "Allgemeiner API-Schlüssel",
        "openrouterApiKey": "OpenRouter API-Schlüssel",
        "groqApiKey": "Groq API-Schlüssel",
        "deepseekApiKey": "DeepSeek API-Schlüssel",
        "googleApiKey": "Google (Gemini) API-Schlüssel",
        "lmstudioUrl": "LM-Studio-Adresse",
        "perplexityApiKey": "Perplexity API-Schlüssel",
        "togetherApiKey": "Together API-Schlüssel",
        "xaiApiKey": "xAI API-Schlüssel",
        "llamacppUrl": "llama.cpp-Adresse",
        "vllmUrl": "vLLM-Adresse",
        "scrapersList": "Zu verwendende Darsteller-Scraper",
        "ollamaUrl": "Ollama-Adresse",
    },
    "msg": {
        "prompt_vision": (
            "Lies den auf diesem Bild sichtbaren TEXT: "
            "Studio-Wasserzeichen, Logo, Webadresse, eingeblendeter "
            "Titel. Beschreibe die Personen NICHT, errate NICHT, wer "
            "sie sind — gib nur wieder, was GESCHRIEBEN steht. Ist "
            "kein Text lesbar, antworte null. Antworte NUR als JSON: "
            "{\"studio\": gelesener Name oder null, \"texte_lu\": "
            "[gelesene Zeichenfolgen], \"confiance\": 0.0 bis 1.0}"),
        "prompt_donnees": "DATEN :",
        "prompt_biohot": (
            "Schreibe auf {langue} die explizite Biografie des "
            "schwulen Pornodarstellers '{nom}' für eine private "
            "Erwachsenen-Mediathek. Direkter, bewusst derber Ton, 3 "
            "bis 4 Sätze (max. 450 Zeichen): Fickstil, Position, "
            "Ausstattung, wiederkehrende Partner und Studios der "
            "Sammlung. ABSOLUTE REGEL: Stütze dich AUSSCHLIESSLICH "
            "auf die untenstehenden Daten; erfinde WEDER Praktiken "
            "(raw, Fetisch…) NOCH Position NOCH Merkmale, die dort "
            "nicht ausdrücklich stehen. Ist die Grundlage dünn, fasse "
            "dich kurz, statt zu erfinden. Antworte nur mit der "
            "Biografie."),
        "prompt_biohot_consignes": (
            "\n\nDARSTELLUNG: kein Titel, kein Name am Anfang, keine "
            "Sternchen, keine Auszeichnung — der Name steht bereits "
            "über dem Text, und Auszeichnung wird wörtlich angezeigt. "
            "Schreibe nur Sätze."),
        "prompt_roles": (
            "Prüfe die Dokumentation eines Darstellers auf eine "
            "AUSDRÜCKLICHE Nennung seiner üblichen sexuellen Rolle. "
            "ABSOLUTE REGEL: antworte nur, wenn der Text es klar "
            "sagt. Leite NICHTS aus Statur, Orientierung, "
            "Nationalität, Studio, Szenentyp oder einem "
            "Gesamteindruck ab. Es geht um eine reale Person: eine "
            "Vermutung wäre ein Fehler, keine Näherung. Im Zweifel "
            "antworte null — nichts zu schließen ist meist die "
            "richtige Antwort. Antworte NUR mit einem JSON-Objekt."),
        "prompt_synopsis": (
            "Schreibe auf {langue} eine sachliche Inhaltsangabe der "
            "Szene '{nom}' (max. 2 Sätze), ohne etwas zu erfinden. "
            "Antworte nur mit der Inhaltsangabe.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Schreibe auf {langue} eine sachliche Vorstellung des "
            "Studios '{nom}' (max. 3 Sätze), ohne etwas zu erfinden. "
            "Antworte nur mit dem Text.\n\n{donnees}"),
        "prompt_bio": (
            "Schreibe aus diesen Mehrquellen-Daten zum Darsteller "
            "'{nom}' EINE sachliche Biografie auf {langue} (max. 300 "
            "Zeichen), ohne etwas zu erfinden. Antworte nur mit der "
            "Biografie.\n\n{donnees}"),
        "conflits": "KONFLIKTE (nichts wurde überschrieben): "
                    "{details}",
        "conflit_ligne": "{champ}: aktuell « {actuel} » vs Quellen: "
                         "{propose}",
        "doublon_probable": "MÖGLICHES DUPLIKAT von: {jumeaux} — "
                            "Schaltflächen « Zusammenführen » oder "
                            "« Kein Duplikat » auf dieser Seite",
        "doublon_perf": "mögliches Duplikat von: {jumeaux} — falls "
                        "falsch, Tag {tag} setzen und die Erkennung "
                        "erneut starten",
        "par_nom_fichier": "über den DATEINAMEN erkannt (kein "
                           "Fingerabdruck, geringere Sicherheit)",
        "coherence_fichier": "Übereinstimmung mit dem Dateinamen "
                             "{score} ({detail})",
        "coherence_nulle": "⚠ der Dateiname passt nicht zur "
                           "Zuordnung — bitte prüfen",
        "fusion_trace": "Duplikat « {nom} » (id {id}) am {date} "
                        "zusammengeführt",
        "restaure_trace": "am {date} wiederhergestellt "
                          "(Durchlauf vom {passage})",
        "bio_hot_echec": "Hot-Biografie nicht erzeugt — {motif} "
                         "({date})",
        "pied_bio": "― Datenzuverlässigkeit (Gaizer) ―",
        "pied_bio_intro": "Automatisch ausgefüllt am {date} — "
                          "Note /10 = geschätzte Zuverlässigkeit der "
                          "Quellen.",
        "accepter_studio": " — Schaltfläche « Übernehmen » auf dieser "
                           "Seite, dann die Aufgabe « Angenommene "
                           "Studios übernehmen » ausführen",
        "ia_quota": "Kontingent oder Guthaben des KI-Kontos "
                    "aufgebraucht",
        "ia_debit": "Ratenbegrenzung des KI-Anbieters erreicht "
                    "(zu viele Anfragen)",
        "ia_cle": "API-Schlüssel vom KI-Anbieter abgelehnt",
        "ia_modele": "KI-Modell unbekannt oder vom Anbieter "
                     "abgeschaltet",
        "ia_requete": "Anfrage zu lang für das Modell",
        "ia_indispo": "KI-Dienst überlastet — derzeit nicht verfügbar",
        "ia_reseau": "kein Netzwerkzugang zum KI-Anbieter",
        "ia_timeout": "der KI-Anbieter hat nicht rechtzeitig "
                      "geantwortet",
        "ia_inattendu": "unerwarteter Fehler des KI-Anbieters",
        "ia_indisponible": "KI nicht verfügbar — {motif}",
        "ia_suspendue": "KI AUSGESETZT: {motif}. Die Texterzeugung "
                        "wird auf {date} verschoben; die sachliche "
                        "Anreicherung läuft weiter. Aufgabe "
                        "« Agent-Status » für Einzelheiten.",
        "ia_en_pause": "KI-Erzeugung pausiert bis {date} ({motif}) — "
                       "sachliche Daten werden weiter angereichert",
        "ia_reprise": "KI-Erzeugung wieder aktiv: die am {pose} "
                      "gesetzte Pause ({motif}) endete am {date}. "
                      "Ausstehende Arbeit wird von den "
                      "Anreicherungsaufgaben übernommen.",
        "plafond_ia": "Obergrenze von {max} KI-Aufruf(en) erreicht "
                      "(Einstellung maxLlmCalls) — weitere "
                      "Erzeugungen werden übersprungen, Aufgabe "
                      "erneut starten",
        "simulation_active": "SIMULATIONSMODUS aktiv: es wird nichts "
                             "in Stash geschrieben.",
        "simulation_evite": "  [SIMULATION] {op} übersprungen: "
                            "{details}",
    },
}

# =====================================================================
#  ESPAÑOL
# =====================================================================
ES = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "creado", "verify": "verificar",
        "duplicate": "duplicado?", "not_duplicate": "no-duplicado",
        "merge": "fusionar", "restore": "restaurar",
        "unidentified": "no-identificada",
    },
    "boutons": {
        "enrichir": "Enriquecer", "accepter": "Aceptar",
        "pas_doublon": "No es duplicado", "fusionner": "Fusionar",
        "verifie": "Verificado", "restaurer": "Restaurar",
        "titre": "Gaizer — acciones en esta ficha",
        "confirm": "¿Fusionar « {nom} » con su gemelo? "
                   "Esta ficha se eliminará.",
    },
    "taches": {
        "enrich_performers": "Enriquecer intérpretes incompletos",
        "enrich_scenes": "Enriquecer escenas incompletas",
        "enrich_studios": "Enriquecer estudios incompletos",
        "apply_accepted": "Aplicar propuestas aceptadas",
        "apply_accepted_scenes": "Aplicar escenas aceptadas",
        "apply_accepted_studios": "Aplicar estudios aceptados",
        "apply_recommended": "Aplicar recomendaciones (en masa)",
        "apply_covers": "Aplicar carátulas oficiales",
        "detect_duplicates": "Detectar duplicados probables",
        "detect_duplicates_studios": "Detectar estudios duplicados",
        "merge_marked": "Fusionar duplicados marcados",
        "merge_marked_studios": "Fusionar estudios marcados",
        "dedoublonnage_complet": "Desduplicación completa "
                                 "(intérpretes + estudios)",
        "restore_marked": "Restaurar fichas marcadas",
        "regenerate_biohot": "Regenerar las biografías hot",
        "position_tags": "Posición → etiquetas estándar",
        "rapport_run": "Informe de ejecución e higiene",
        "rapport_tags": "Informe de etiquetas",
        "etat_agent": "Estado del agente",
        "reprendre_ia": "Reanudar la generación con IA",
        "migrer_langue": "Cambiar el idioma del plugin",
        "clear_proposals": "Limpiar las propuestas",
        "enrich_one_performer": "Enriquecer un intérprete",
        "enrich_one_scene": "Enriquecer una escena",
        "enrich_one_studio": "Enriquecer un estudio",
        "restaurer_reglages": "Restaurar los ajustes",
        "purger_tags_exclus": "Quitar las etiquetas excluidas",
        "detect_groupes": "Reconstruir las películas por partes",
        "suggerer_tags_exclus": "Sugerir etiquetas a excluir",
        "normaliser_roles": "Normalizar posiciones y roles",
        "retirer_pied_bio": "Quitar el pie de biografía",
        "deduire_roles": "Sugerir posiciones y roles (IA)",
        "controler_heritage": "Comprobar los campos heredados de una importación",
        "ranger_champs_herites": "Ordenar los campos heredados de una importación",
        "retirer_non_confirme": "Quitar los valores sin respaldo",
        "retirer_champ_herite": "Eliminar un campo heredado",
        "marquer_roles_importes": "Marcar los roles importados como sugeridos",
        "inspecter_collecte": "Inspeccionar la recogida de una ficha",
        "arbitrer_conflits": "Alinear los conflictos con las fuentes",
        "sante_sources": "Comprobar el estado de las fuentes",
        "proposer_scrapers": "Sugerir los scrapers que faltan",
        "lire_vignettes": "Leer las marcas de agua de las miniaturas",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Modo de aplicación (manual / seuil / auto)",
        "autoAcceptThreshold": "Umbral de aprobación en masa (/10)",
        "strongMergeThreshold": "Umbral fuerte de fusión",
        "annotateBio": "Pie de biografía « Fiabilidad de los datos »",
        "language": "Idioma del plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "Modo simulación (sin escrituras)",
        "maxLlmCalls": "Límite de llamadas a la IA por tarea "
                       "(0 = sin límite)",
        "llmDelayMs": "Espaciado entre llamadas a la IA "
                      "(milisegundos)",
        "applySceneCovers": "Preferir las carátulas oficiales",
        "applyImages": "Aplicar las imágenes de las fuentes",
        "positionAsTag": "Posición como etiqueta estándar",
        "createMissing": "Crear fichas desconocidas (escenas)",
        "groupMinScenes": "Partes mínimas para crear un grupo",
        "batchSize": "Tamaño de lote de las tareas",
        "autoInstallScrapers": "Instalar los scrapers que faltan",
        "scraperSource": "Catálogo de scrapers",
        "visionEnvoiImages": "Enviar las miniaturas al modelo de visión",
        "aiVision": "IA para lectura de imágenes (proveedor:modelo)",
        "visionPrompt": "Visión — instrucciones",
        "tagProfile": "Perfil de colección (opcional)",
        "tagsExclude": "Etiquetas que nunca se aplican "
                       "(separadas por comas)",
        "refreshDays": "Frescura de los datos (días, 0 = nunca)",
        "generateBioHot": "Generar la biografía « hot »",
        "biohotPrompt": "Biografía hot — instrucciones del prompt",
        "biohotTemperature": "Biografía hot — temperatura (0.0-1.5)",
        "autoMergeDuplicates": "Fusión automática de duplicados "
                               "seguros",
        "proposalTagPrefix": "Prefijo de las etiquetas del plugin",
        "useUrlPass": "Pasada de URL (scrapers por URL)",
        "useExtraSources": "Fuentes complementarias (Wikipedia, ADE)",
        "useStashBoxes": "Usar las stash-boxes configuradas",
        "scrapersExclude": "Scrapers a excluir",
        "aiDefault": "IA por defecto (proveedor:modelo)",
        "aiBio": "IA para las biografías factuales",
        "aiSynopsis": "IA para las sinopsis de escenas",
        "aiBiohot": "IA para la biografía « hot »",
        "mistralApiKey": "Clave de API de Mistral",
        "openaiApiKey": "Clave de API de OpenAI",
        "anthropicApiKey": "Clave de API de Anthropic",
        "llmApiKey": "Clave de API genérica",
        "openrouterApiKey": "Clave de API OpenRouter",
        "groqApiKey": "Clave de API Groq",
        "deepseekApiKey": "Clave de API DeepSeek",
        "googleApiKey": "Clave de API Google (Gemini)",
        "lmstudioUrl": "Dirección de LM Studio",
        "perplexityApiKey": "Clave de API Perplexity",
        "togetherApiKey": "Clave de API Together",
        "xaiApiKey": "Clave de API xAI",
        "llamacppUrl": "Dirección de llama.cpp",
        "vllmUrl": "Dirección de vLLM",
        "scrapersList": "Scrapers de intérpretes a usar",
        "ollamaUrl": "Dirección de Ollama",
    },
    "msg": {
        "prompt_vision": (
            "Lee el TEXTO visible en esta imagen: marca de agua del "
            "estudio, logotipo, dirección web, título incrustado. NO "
            "describas a las personas, NO adivines quiénes son — "
            "informa solo de lo que está ESCRITO. Si no hay texto "
            "legible, responde null. Responde ÚNICAMENTE en JSON: "
            "{\"studio\": nombre leído o null, \"texte_lu\": [cadenas "
            "leídas], \"confiance\": 0.0 a 1.0}"),
        "prompt_donnees": "DATOS :",
        "prompt_biohot": (
            "Redacta en {langue} la biografía explícita del actor "
            "porno gay '{nom}' para una mediateca adulta privada. "
            "Tono directo y crudo asumido, 3 o 4 frases (450 "
            "caracteres máx.): su estilo de follar, su posición, su "
            "equipo, sus compañeros y estudios recurrentes en la "
            "colección. REGLA ABSOLUTA: apóyate ÚNICAMENTE en los "
            "datos siguientes; no deduzcas NI práctica (raw, "
            "fetiche…) NI posición NI rasgo que no figure "
            "explícitamente. Si el material es escaso, sé breve en "
            "lugar de inventar. Responde solo la biografía."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTACIÓN: no escribas título, ni nombre al "
            "principio, ni asteriscos, ni marcado alguno — el nombre "
            "ya figura encima del texto, y el marcado se muestra tal "
            "cual. Redacta solo frases."),
        "prompt_roles": (
            "Examina la documentación de un intérprete para detectar "
            "una mención EXPLÍCITA de su rol sexual habitual. REGLA "
            "ABSOLUTA: responde solo si el texto lo indica "
            "claramente. No infieras NADA de la morfología, la "
            "orientación, la nacionalidad, el estudio, el tipo de "
            "escena ni una impresión general. Se trata de una persona "
            "real: una suposición sería un error, no una "
            "aproximación. En la duda, responde null — no concluir "
            "nada es la respuesta correcta la mayoría de las veces. "
            "Responde ÚNICAMENTE con un objeto JSON."),
        "prompt_synopsis": (
            "Redacta en {langue} una sinopsis factual de la escena "
            "'{nom}' (2 frases máx.), sin inventar nada. Responde "
            "solo la sinopsis.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Redacta en {langue} una presentación factual del estudio "
            "'{nom}' (3 frases máx.), sin inventar nada. Responde "
            "solo el texto.\n\n{donnees}"),
        "prompt_bio": (
            "A partir de estos datos multifuente sobre el actor "
            "'{nom}', redacta UNA biografía factual en {langue} (máx. "
            "300 caracteres), sin inventar nada. Responde solo la "
            "biografía.\n\n{donnees}"),
        "conflits": "CONFLICTOS (no se sobrescribió nada): {details}",
        "conflit_ligne": "{champ}: actual « {actuel} » vs fuentes: "
                         "{propose}",
        "doublon_probable": "DUPLICADO PROBABLE de: {jumeaux} — "
                            "botones « Fusionar » o « No es "
                            "duplicado » en esta ficha",
        "doublon_perf": "duplicado probable de: {jumeaux} — si es "
                        "falso, añadir la etiqueta {tag} y relanzar "
                        "la detección",
        "par_nom_fichier": "identificado por el NOMBRE DEL ARCHIVO "
                           "(sin huella, menor fiabilidad)",
        "coherence_fichier": "coincidencia con el nombre del archivo "
                             "{score} ({detail})",
        "coherence_nulle": "⚠ el nombre del archivo no coincide con "
                           "la identificación — conviene revisarlo",
        "fusion_trace": "duplicado « {nom} » (id {id}) fusionado "
                        "el {date}",
        "restaure_trace": "restaurado el {date} (pasada del {passage})",
        "bio_hot_echec": "biografía hot no generada — {motif} "
                         "({date})",
        "pied_bio": "― Fiabilidad de los datos (Gaizer) ―",
        "pied_bio_intro": "Relleno automático del {date} — "
                          "nota /10 = fiabilidad estimada de las "
                          "fuentes.",
        "accepter_studio": " — botón « Aceptar » en esta ficha, luego "
                           "la tarea « Aplicar estudios aceptados »",
        "ia_quota": "cuota o crédito de la cuenta de IA agotado",
        "ia_debit": "límite de peticiones del proveedor de IA "
                    "alcanzado",
        "ia_cle": "clave de API rechazada por el proveedor de IA",
        "ia_modele": "modelo de IA desconocido o retirado por el "
                     "proveedor",
        "ia_requete": "petición demasiado larga para el modelo",
        "ia_indispo": "servicio de IA saturado — no disponible por "
                      "ahora",
        "ia_reseau": "sin acceso de red al proveedor de IA",
        "ia_timeout": "el proveedor de IA no respondió a tiempo",
        "ia_inattendu": "error inesperado del proveedor de IA",
        "ia_indisponible": "IA no disponible — {motif}",
        "ia_suspendue": "IA SUSPENDIDA: {motif}. La generación de "
                        "textos se reprograma para el {date}; el "
                        "enriquecimiento factual continúa. Tarea "
                        "« Estado del agente » para más detalles.",
        "ia_en_pause": "generación con IA en pausa hasta el {date} "
                       "({motif}) — los datos factuales se siguen "
                       "enriqueciendo",
        "ia_reprise": "Generación con IA reactivada: la pausa puesta "
                      "el {pose} ({motif}) venció el {date}. Las "
                      "tareas de enriquecimiento retomarán el trabajo "
                      "pendiente.",
        "plafond_ia": "límite de {max} llamada(s) a la IA alcanzado "
                      "(ajuste maxLlmCalls) — las siguientes "
                      "generaciones se omiten, relanzar la tarea para "
                      "continuar",
        "simulation_active": "MODO SIMULACIÓN activo: no se escribirá "
                             "nada en Stash.",
        "simulation_evite": "  [SIMULACIÓN] {op} omitido: {details}",
    },
}

# =====================================================================
#  ITALIANO
# =====================================================================
IT = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "creato", "verify": "verificare",
        "duplicate": "duplicato?", "not_duplicate": "non-duplicato",
        "merge": "unire", "restore": "ripristinare",
        "unidentified": "non-identificata",
    },
    "boutons": {
        "enrichir": "Arricchisci", "accepter": "Accetta",
        "pas_doublon": "Non è un doppione", "fusionner": "Unisci",
        "verifie": "Verificato", "restaurer": "Ripristina",
        "titre": "Gaizer — azioni su questa scheda",
        "confirm": "Unire « {nom} » al suo gemello? "
                   "Questa scheda sarà eliminata.",
    },
    "taches": {
        "enrich_performers": "Arricchisci gli interpreti incompleti",
        "enrich_scenes": "Arricchisci le scene incomplete",
        "enrich_studios": "Arricchisci gli studi incompleti",
        "apply_accepted": "Applica le proposte accettate",
        "apply_accepted_scenes": "Applica le scene accettate",
        "apply_accepted_studios": "Applica gli studi accettati",
        "apply_recommended": "Applica le raccomandazioni (in blocco)",
        "apply_covers": "Applica le copertine ufficiali",
        "detect_duplicates": "Rileva i probabili doppioni",
        "detect_duplicates_studios": "Rileva gli studi doppioni",
        "merge_marked": "Unisci i doppioni contrassegnati",
        "merge_marked_studios": "Unisci gli studi contrassegnati",
        "dedoublonnage_complet": "Deduplicazione completa "
                                 "(interpreti + studi)",
        "restore_marked": "Ripristina le schede contrassegnate",
        "regenerate_biohot": "Rigenera le biografie hot",
        "position_tags": "Posizione → tag standard",
        "rapport_run": "Rapporto di esecuzione e igiene",
        "rapport_tags": "Rapporto dei tag",
        "etat_agent": "Stato dell'agente",
        "reprendre_ia": "Riprendi la generazione IA",
        "migrer_langue": "Cambia la lingua del plugin",
        "clear_proposals": "Pulisci le proposte",
        "enrich_one_performer": "Arricchisci un interprete",
        "enrich_one_scene": "Arricchisci una scena",
        "enrich_one_studio": "Arricchisci uno studio",
        "restaurer_reglages": "Ripristina le impostazioni",
        "purger_tags_exclus": "Rimuovi i tag esclusi",
        "detect_groupes": "Ricostruisci i film in più parti",
        "suggerer_tags_exclus": "Suggerisci tag da escludere",
        "normaliser_roles": "Normalizza posizioni e ruoli",
        "retirer_pied_bio": "Rimuovi il piè di biografia",
        "deduire_roles": "Suggerisci posizioni e ruoli (IA)",
        "controler_heritage": "Controlla i campi ereditati da un'importazione",
        "ranger_champs_herites": "Riordina i campi ereditati da un'importazione",
        "retirer_non_confirme": "Rimuovi i valori senza fonte",
        "retirer_champ_herite": "Elimina un campo ereditato",
        "marquer_roles_importes": "Segna i ruoli importati come suggeriti",
        "inspecter_collecte": "Ispeziona la raccolta di una scheda",
        "arbitrer_conflits": "Allinea i conflitti alle fonti",
        "sante_sources": "Verifica lo stato delle fonti",
        "proposer_scrapers": "Suggerisci gli scraper mancanti",
        "lire_vignettes": "Leggi le filigrane delle miniature",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Modalità di applicazione "
                     "(manual / seuil / auto)",
        "autoAcceptThreshold": "Soglia di approvazione in blocco (/10)",
        "strongMergeThreshold": "Soglia forte di unione",
        "annotateBio": "Piè di biografia « Affidabilità dei dati »",
        "language": "Lingua del plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "Modalità simulazione (nessuna scrittura)",
        "maxLlmCalls": "Tetto di chiamate all'IA per attività "
                       "(0 = illimitato)",
        "llmDelayMs": "Intervallo tra le chiamate all'IA "
                      "(millisecondi)",
        "applySceneCovers": "Preferire le copertine ufficiali",
        "applyImages": "Applicare le immagini delle fonti",
        "positionAsTag": "Posizione come tag standard",
        "createMissing": "Creare le schede sconosciute (scene)",
        "groupMinScenes": "Parti minime per creare un gruppo",
        "batchSize": "Dimensione del lotto delle attività",
        "autoInstallScrapers": "Installa gli scraper mancanti",
        "scraperSource": "Catalogo di scraper",
        "visionEnvoiImages": "Invia le miniature al modello di visione",
        "aiVision": "IA per la lettura di immagini (fornitore:modello)",
        "visionPrompt": "Visione — istruzioni",
        "tagProfile": "Profilo della raccolta (facoltativo)",
        "tagsExclude": "Tag da non applicare mai "
                       "(separati da virgole)",
        "refreshDays": "Freschezza dei dati (giorni, 0 = mai)",
        "generateBioHot": "Generare la biografia « hot »",
        "biohotPrompt": "Biografia hot — istruzioni del prompt",
        "biohotTemperature": "Biografia hot — temperatura (0.0-1.5)",
        "autoMergeDuplicates": "Unione automatica dei doppioni sicuri",
        "proposalTagPrefix": "Prefisso dei tag del plugin",
        "useUrlPass": "Passaggio URL (scraper per URL)",
        "useExtraSources": "Fonti supplementari (Wikipedia, ADE)",
        "useStashBoxes": "Usare le stash-box configurate",
        "scrapersExclude": "Scraper da escludere",
        "aiDefault": "IA predefinita (fornitore:modello)",
        "aiBio": "IA per le biografie fattuali",
        "aiSynopsis": "IA per le sinossi delle scene",
        "aiBiohot": "IA per la biografia « hot »",
        "mistralApiKey": "Chiave API Mistral",
        "openaiApiKey": "Chiave API OpenAI",
        "anthropicApiKey": "Chiave API Anthropic",
        "llmApiKey": "Chiave API generica",
        "openrouterApiKey": "Chiave API OpenRouter",
        "groqApiKey": "Chiave API Groq",
        "deepseekApiKey": "Chiave API DeepSeek",
        "googleApiKey": "Chiave API Google (Gemini)",
        "lmstudioUrl": "Indirizzo di LM Studio",
        "perplexityApiKey": "Chiave API Perplexity",
        "togetherApiKey": "Chiave API Together",
        "xaiApiKey": "Chiave API xAI",
        "llamacppUrl": "Indirizzo di llama.cpp",
        "vllmUrl": "Indirizzo di vLLM",
        "scrapersList": "Scraper interpreti da usare",
        "ollamaUrl": "Indirizzo di Ollama",
    },
    "msg": {
        "prompt_vision": (
            "Leggi il TESTO visibile su questa immagine: filigrana "
            "dello studio, logo, indirizzo web, titolo sovrimpresso. "
            "NON descrivere le persone, NON indovinare chi sono — "
            "riporta solo ciò che è SCRITTO. Se nessun testo è "
            "leggibile, rispondi null. Rispondi SOLO in JSON: "
            "{\"studio\": nome letto o null, \"texte_lu\": [stringhe "
            "lette], \"confiance\": 0.0 a 1.0}"),
        "prompt_donnees": "DATI :",
        "prompt_biohot": (
            "Scrivi in {langue} la biografia esplicita dell'attore "
            "porno gay '{nom}' per una mediateca adulta privata. Tono "
            "diretto e volutamente crudo, 3 o 4 frasi (450 caratteri "
            "max): il suo stile di scopata, la sua posizione, la sua "
            "dotazione, i partner e gli studi ricorrenti nella "
            "collezione. REGOLA ASSOLUTA: basati SOLO sui dati qui "
            "sotto; non dedurre NÉ pratiche (raw, feticci…) NÉ "
            "posizione NÉ tratti che non vi figurino esplicitamente. "
            "Se il materiale è scarso, sii breve invece di inventare. "
            "Rispondi solo con la biografia."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTAZIONE: non scrivere titolo, né nome in "
            "testa, né asterischi, né alcun markup — il nome figura "
            "già sopra il testo, e il markup appare tale e quale. "
            "Scrivi solo frasi."),
        "prompt_roles": (
            "Esamina la documentazione di un interprete per "
            "individuare una menzione ESPLICITA del suo ruolo "
            "sessuale abituale. REGOLA ASSOLUTA: rispondi solo se il "
            "testo lo indica chiaramente. Non dedurre NULLA da "
            "morfologia, orientamento, nazionalità, studio, tipo di "
            "scena o impressione generale. Si tratta di una persona "
            "reale: una supposizione sarebbe un errore, non "
            "un'approssimazione. Nel dubbio rispondi null — non "
            "concludere nulla è la risposta giusta il più delle "
            "volte. Rispondi SOLO con un oggetto JSON."),
        "prompt_synopsis": (
            "Scrivi in {langue} una sinossi fattuale della scena "
            "'{nom}' (max 2 frasi), senza inventare nulla. Rispondi "
            "solo con la sinossi.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Scrivi in {langue} una presentazione fattuale dello "
            "studio '{nom}' (max 3 frasi), senza inventare nulla. "
            "Rispondi solo con il testo.\n\n{donnees}"),
        "prompt_bio": (
            "Da questi dati multi-fonte sull'attore '{nom}', scrivi "
            "UNA biografia fattuale in {langue} (max 300 caratteri), "
            "senza inventare nulla. Rispondi solo con la "
            "biografia.\n\n{donnees}"),
        "conflits": "CONFLITTI (nulla è stato sovrascritto): "
                    "{details}",
        "conflit_ligne": "{champ}: attuale « {actuel} » vs fonti: "
                         "{propose}",
        "doublon_probable": "PROBABILE DOPPIONE di: {jumeaux} — "
                            "pulsanti « Unisci » o « Non è un "
                            "doppione » su questa scheda",
        "doublon_perf": "probabile doppione di: {jumeaux} — se "
                        "errato, applicare il tag {tag} e rilanciare "
                        "il rilevamento",
        "par_nom_fichier": "identificato dal NOME DEL FILE (nessuna "
                           "impronta, affidabilità minore)",
        "coherence_fichier": "corrispondenza con il nome del file "
                             "{score} ({detail})",
        "coherence_nulle": "⚠ il nome del file non corrisponde "
                           "all'identificazione — da controllare",
        "fusion_trace": "doppione « {nom} » (id {id}) unito il {date}",
        "restaure_trace": "ripristinato il {date} "
                          "(passaggio del {passage})",
        "bio_hot_echec": "biografia hot non generata — {motif} "
                         "({date})",
        "pied_bio": "― Affidabilità dei dati (Gaizer) ―",
        "pied_bio_intro": "Compilazione automatica del {date} — "
                          "voto /10 = affidabilità stimata delle "
                          "fonti.",
        "accepter_studio": " — pulsante « Accetta » su questa scheda, "
                           "poi l'attività « Applica gli studi "
                           "accettati »",
        "ia_quota": "quota o credito dell'account IA esaurito",
        "ia_debit": "limite di richieste del fornitore IA raggiunto",
        "ia_cle": "chiave API rifiutata dal fornitore IA",
        "ia_modele": "modello IA sconosciuto o ritirato dal fornitore",
        "ia_requete": "richiesta troppo lunga per il modello",
        "ia_indispo": "servizio IA saturo — non disponibile al "
                      "momento",
        "ia_reseau": "nessun accesso di rete al fornitore IA",
        "ia_timeout": "il fornitore IA non ha risposto in tempo",
        "ia_inattendu": "errore inatteso del fornitore IA",
        "ia_indisponible": "IA non disponibile — {motif}",
        "ia_suspendue": "IA SOSPESA: {motif}. La generazione dei "
                        "testi è riprogrammata al {date}; "
                        "l'arricchimento fattuale continua. Attività "
                        "« Stato dell'agente » per i dettagli.",
        "ia_en_pause": "generazione IA in pausa fino al {date} "
                       "({motif}) — i dati fattuali continuano a "
                       "essere arricchiti",
        "ia_reprise": "Generazione IA riattivata: la pausa posta il "
                      "{pose} ({motif}) è scaduta il {date}. Il "
                      "lavoro in sospeso sarà ripreso dalle attività "
                      "di arricchimento.",
        "plafond_ia": "tetto di {max} chiamata/e IA raggiunto "
                      "(impostazione maxLlmCalls) — le generazioni "
                      "successive sono saltate, rilanciare "
                      "l'attività per continuare",
        "simulation_active": "MODALITÀ SIMULAZIONE attiva: nulla sarà "
                             "scritto in Stash.",
        "simulation_evite": "  [SIMULAZIONE] {op} evitato: {details}",
    },
}

# =====================================================================
#  PORTUGUÊS
# =====================================================================
PT = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "criado", "verify": "verificar",
        "duplicate": "duplicado?", "not_duplicate": "nao-duplicado",
        "merge": "fundir", "restore": "restaurar",
        "unidentified": "nao-identificada",
    },
    "boutons": {
        "enrichir": "Enriquecer", "accepter": "Aceitar",
        "pas_doublon": "Não é duplicado", "fusionner": "Fundir",
        "verifie": "Verificado", "restaurer": "Restaurar",
        "titre": "Gaizer — ações nesta ficha",
        "confirm": "Fundir « {nom} » com o seu gémeo? "
                   "Esta ficha será eliminada.",
    },
    "taches": {
        "enrich_performers": "Enriquecer intérpretes incompletos",
        "enrich_scenes": "Enriquecer cenas incompletas",
        "enrich_studios": "Enriquecer estúdios incompletos",
        "apply_accepted": "Aplicar as propostas aceites",
        "apply_accepted_scenes": "Aplicar as cenas aceites",
        "apply_accepted_studios": "Aplicar os estúdios aceites",
        "apply_recommended": "Aplicar as recomendações (em massa)",
        "apply_covers": "Aplicar as capas oficiais",
        "detect_duplicates": "Detetar duplicados prováveis",
        "detect_duplicates_studios": "Detetar estúdios duplicados",
        "merge_marked": "Fundir os duplicados marcados",
        "merge_marked_studios": "Fundir os estúdios marcados",
        "dedoublonnage_complet": "Desduplicação completa "
                                 "(intérpretes + estúdios)",
        "restore_marked": "Restaurar as fichas marcadas",
        "regenerate_biohot": "Regenerar as biografias hot",
        "position_tags": "Posição → etiquetas padrão",
        "rapport_run": "Relatório de execução e higiene",
        "rapport_tags": "Relatório das etiquetas",
        "etat_agent": "Estado do agente",
        "reprendre_ia": "Retomar a geração com IA",
        "migrer_langue": "Mudar o idioma do plugin",
        "clear_proposals": "Limpar as propostas",
        "enrich_one_performer": "Enriquecer um intérprete",
        "enrich_one_scene": "Enriquecer uma cena",
        "enrich_one_studio": "Enriquecer um estúdio",
        "restaurer_reglages": "Restaurar as definições",
        "purger_tags_exclus": "Remover as etiquetas excluídas",
        "detect_groupes": "Reconstituir os filmes em várias partes",
        "suggerer_tags_exclus": "Sugerir etiquetas a excluir",
        "normaliser_roles": "Normalizar posições e papéis",
        "retirer_pied_bio": "Remover o rodapé da biografia",
        "deduire_roles": "Sugerir posições e papéis (IA)",
        "controler_heritage": "Verificar os campos herdados de uma importação",
        "ranger_champs_herites": "Arrumar os campos herdados de uma importação",
        "retirer_non_confirme": "Remover os valores sem fonte",
        "retirer_champ_herite": "Eliminar um campo herdado",
        "marquer_roles_importes": "Marcar os papéis importados como sugeridos",
        "inspecter_collecte": "Inspecionar a recolha de uma ficha",
        "arbitrer_conflits": "Alinhar os conflitos pelas fontes",
        "sante_sources": "Verificar o estado das fontes",
        "proposer_scrapers": "Sugerir os scrapers em falta",
        "lire_vignettes": "Ler as marcas de água das miniaturas",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Modo de aplicação (manual / seuil / auto)",
        "autoAcceptThreshold": "Limiar de aprovação em massa (/10)",
        "strongMergeThreshold": "Limiar forte de fusão",
        "annotateBio": "Rodapé da biografia "
                       "« Fiabilidade dos dados »",
        "language": "Idioma do plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "Modo simulação (sem escritas)",
        "maxLlmCalls": "Limite de chamadas à IA por tarefa "
                       "(0 = ilimitado)",
        "llmDelayMs": "Espaçamento entre chamadas à IA "
                      "(milissegundos)",
        "applySceneCovers": "Preferir as capas oficiais",
        "applyImages": "Aplicar as imagens das fontes",
        "positionAsTag": "Posição como etiqueta padrão",
        "createMissing": "Criar as fichas desconhecidas (cenas)",
        "groupMinScenes": "Partes mínimas para criar um grupo",
        "batchSize": "Tamanho do lote das tarefas",
        "autoInstallScrapers": "Instalar os scrapers em falta",
        "scraperSource": "Catálogo de scrapers",
        "visionEnvoiImages": "Enviar as miniaturas ao modelo de visão",
        "aiVision": "IA para leitura de imagens (fornecedor:modelo)",
        "visionPrompt": "Visão — instruções",
        "tagProfile": "Perfil da coleção (opcional)",
        "tagsExclude": "Etiquetas a nunca aplicar "
                       "(separadas por vírgulas)",
        "refreshDays": "Frescura dos dados (dias, 0 = nunca)",
        "generateBioHot": "Gerar a biografia « hot »",
        "biohotPrompt": "Biografia hot — instruções do prompt",
        "biohotTemperature": "Biografia hot — temperatura (0.0-1.5)",
        "autoMergeDuplicates": "Fusão automática dos duplicados "
                               "seguros",
        "proposalTagPrefix": "Prefixo das etiquetas do plugin",
        "useUrlPass": "Passagem de URL (scrapers por URL)",
        "useExtraSources": "Fontes complementares (Wikipedia, ADE)",
        "useStashBoxes": "Usar as stash-boxes configuradas",
        "scrapersExclude": "Scrapers a excluir",
        "aiDefault": "IA por defeito (fornecedor:modelo)",
        "aiBio": "IA para as biografias factuais",
        "aiSynopsis": "IA para as sinopses das cenas",
        "aiBiohot": "IA para a biografia « hot »",
        "mistralApiKey": "Chave de API Mistral",
        "openaiApiKey": "Chave de API OpenAI",
        "anthropicApiKey": "Chave de API Anthropic",
        "llmApiKey": "Chave de API genérica",
        "openrouterApiKey": "Chave de API OpenRouter",
        "groqApiKey": "Chave de API Groq",
        "deepseekApiKey": "Chave de API DeepSeek",
        "googleApiKey": "Chave de API Google (Gemini)",
        "lmstudioUrl": "Endereço do LM Studio",
        "perplexityApiKey": "Chave de API Perplexity",
        "togetherApiKey": "Chave de API Together",
        "xaiApiKey": "Chave de API xAI",
        "llamacppUrl": "Endereço do llama.cpp",
        "vllmUrl": "Endereço do vLLM",
        "scrapersList": "Scrapers de intérpretes a usar",
        "ollamaUrl": "Endereço do Ollama",
    },
    "msg": {
        "prompt_vision": (
            "Lê o TEXTO visível nesta imagem: marca de água do "
            "estúdio, logótipo, endereço web, título sobreposto. NÃO "
            "descrevas as pessoas, NÃO adivinhes quem são — indica "
            "apenas o que está ESCRITO. Se nenhum texto for legível, "
            "responde null. Responde APENAS em JSON: {\"studio\": "
            "nome lido ou null, \"texte_lu\": [cadeias lidas], "
            "\"confiance\": 0.0 a 1.0}"),
        "prompt_donnees": "DADOS :",
        "prompt_biohot": (
            "Escreve em {langue} a biografia explícita do ator porno "
            "gay '{nom}' para uma mediateca adulta privada. Tom "
            "direto e assumidamente cru, 3 a 4 frases (450 caracteres "
            "máx.): o seu estilo de foda, a sua posição, o seu "
            "equipamento, os parceiros e estúdios recorrentes na "
            "coleção. REGRA ABSOLUTA: baseia-te APENAS nos dados "
            "abaixo; não deduzas NEM prática (raw, fetiche…) NEM "
            "posição NEM traço que não figure explicitamente. Se o "
            "material for escasso, sê breve em vez de inventar. "
            "Responde apenas com a biografia."),
        "prompt_biohot_consignes": (
            "\n\nAPRESENTAÇÃO: não escrevas título, nem nome no "
            "início, nem asteriscos, nem qualquer marcação — o nome "
            "já figura acima do texto, e a marcação aparece tal e "
            "qual. Escreve apenas frases."),
        "prompt_roles": (
            "Examina a documentação de um intérprete para detetar uma "
            "menção EXPLÍCITA do seu papel sexual habitual. REGRA "
            "ABSOLUTA: responde apenas se o texto o indicar "
            "claramente. Não infiras NADA de morfologia, orientação, "
            "nacionalidade, estúdio, tipo de cena ou impressão geral. "
            "Trata-se de uma pessoa real: uma suposição seria um "
            "erro, não uma aproximação. Na dúvida responde null — "
            "nada concluir é a resposta certa na maioria dos casos. "
            "Responde APENAS com um objeto JSON."),
        "prompt_synopsis": (
            "Escreve em {langue} uma sinopse factual da cena '{nom}' "
            "(máx. 2 frases), sem inventar nada. Responde apenas com "
            "a sinopse.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Escreve em {langue} uma apresentação factual do estúdio "
            "'{nom}' (máx. 3 frases), sem inventar nada. Responde "
            "apenas com o texto.\n\n{donnees}"),
        "prompt_bio": (
            "A partir destes dados multifonte sobre o ator '{nom}', "
            "escreve UMA biografia factual em {langue} (máx. 300 "
            "caracteres), sem inventar nada. Responde apenas com a "
            "biografia.\n\n{donnees}"),
        "conflits": "CONFLITOS (nada foi substituído): {details}",
        "conflit_ligne": "{champ}: atual « {actuel} » vs fontes: "
                         "{propose}",
        "doublon_probable": "DUPLICADO PROVÁVEL de: {jumeaux} — "
                            "botões « Fundir » ou « Não é duplicado » "
                            "nesta ficha",
        "doublon_perf": "duplicado provável de: {jumeaux} — se "
                        "errado, aplicar a etiqueta {tag} e relançar "
                        "a deteção",
        "par_nom_fichier": "identificado pelo NOME DO FICHEIRO (sem "
                           "impressão digital, menor fiabilidade)",
        "coherence_fichier": "correspondência com o nome do ficheiro "
                             "{score} ({detail})",
        "coherence_nulle": "⚠ o nome do ficheiro não corresponde à "
                           "identificação — a verificar",
        "fusion_trace": "duplicado « {nom} » (id {id}) fundido "
                        "em {date}",
        "restaure_trace": "restaurado em {date} "
                          "(passagem de {passage})",
        "bio_hot_echec": "biografia hot não gerada — {motif} ({date})",
        "pied_bio": "― Fiabilidade dos dados (Gaizer) ―",
        "pied_bio_intro": "Preenchimento automático de {date} — "
                          "nota /10 = fiabilidade estimada das fontes.",
        "accepter_studio": " — botão « Aceitar » nesta ficha, depois "
                           "a tarefa « Aplicar os estúdios aceites »",
        "ia_quota": "quota ou crédito da conta de IA esgotado",
        "ia_debit": "limite de pedidos do fornecedor de IA atingido",
        "ia_cle": "chave de API recusada pelo fornecedor de IA",
        "ia_modele": "modelo de IA desconhecido ou retirado pelo "
                     "fornecedor",
        "ia_requete": "pedido demasiado longo para o modelo",
        "ia_indispo": "serviço de IA saturado — indisponível de "
                      "momento",
        "ia_reseau": "sem acesso de rede ao fornecedor de IA",
        "ia_timeout": "o fornecedor de IA não respondeu a tempo",
        "ia_inattendu": "erro inesperado do fornecedor de IA",
        "ia_indisponible": "IA indisponível — {motif}",
        "ia_suspendue": "IA SUSPENSA: {motif}. A geração de textos "
                        "está reprogramada para {date}; o "
                        "enriquecimento factual continua. Tarefa "
                        "« Estado do agente » para os detalhes.",
        "ia_en_pause": "geração com IA em pausa até {date} ({motif}) "
                       "— os dados factuais continuam a ser "
                       "enriquecidos",
        "ia_reprise": "Geração com IA reativada: a pausa colocada em "
                      "{pose} ({motif}) terminou em {date}. O "
                      "trabalho pendente será retomado pelas tarefas "
                      "de enriquecimento.",
        "plafond_ia": "limite de {max} chamada(s) à IA atingido "
                      "(definição maxLlmCalls) — as gerações "
                      "seguintes são saltadas, relançar a tarefa para "
                      "continuar",
        "simulation_active": "MODO SIMULAÇÃO ativo: nada será escrito "
                             "no Stash.",
        "simulation_evite": "  [SIMULAÇÃO] {op} evitado: {details}",
    },
}

# =====================================================================
#  NEDERLANDS
# =====================================================================
NL = {
    "tags": {
        "proposal": "proposal", "accept": "accept",
        "created": "aangemaakt", "verify": "controleren",
        "duplicate": "duplicaat?", "not_duplicate": "geen-duplicaat",
        "merge": "samenvoegen", "restore": "herstellen",
        "unidentified": "niet-geidentificeerd",
    },
    "boutons": {
        "enrichir": "Verrijken", "accepter": "Accepteren",
        "pas_doublon": "Geen duplicaat", "fusionner": "Samenvoegen",
        "verifie": "Gecontroleerd", "restaurer": "Herstellen",
        "titre": "Gaizer — acties op deze pagina",
        "confirm": "« {nom} » samenvoegen met de dubbele? "
                   "Dit item wordt verwijderd.",
    },
    "taches": {
        "enrich_performers": "Onvolledige performers verrijken",
        "enrich_scenes": "Onvolledige scènes verrijken",
        "enrich_studios": "Onvolledige studio's verrijken",
        "apply_accepted": "Geaccepteerde voorstellen toepassen",
        "apply_accepted_scenes": "Geaccepteerde scènes toepassen",
        "apply_accepted_studios": "Geaccepteerde studio's toepassen",
        "apply_recommended": "Aanbevelingen toepassen (bulk)",
        "apply_covers": "Officiële covers toepassen",
        "detect_duplicates": "Waarschijnlijke duplicaten opsporen",
        "detect_duplicates_studios": "Dubbele studio's opsporen",
        "merge_marked": "Gemarkeerde duplicaten samenvoegen",
        "merge_marked_studios": "Gemarkeerde studio's samenvoegen",
        "dedoublonnage_complet": "Volledige ontdubbeling "
                                 "(performers + studio's)",
        "restore_marked": "Gemarkeerde items herstellen",
        "regenerate_biohot": "Hot-bio's opnieuw genereren",
        "position_tags": "Positie → standaardtags",
        "rapport_run": "Uitvoeringsrapport en hygiëne",
        "rapport_tags": "Tagrapport",
        "etat_agent": "Status van de agent",
        "reprendre_ia": "AI-generatie hervatten",
        "migrer_langue": "Taal van de plugin wisselen",
        "clear_proposals": "Voorstellen opruimen",
        "enrich_one_performer": "Eén performer verrijken",
        "enrich_one_scene": "Eén scène verrijken",
        "enrich_one_studio": "Eén studio verrijken",
        "restaurer_reglages": "Instellingen herstellen",
        "purger_tags_exclus": "Uitgesloten tags verwijderen",
        "detect_groupes": "Meerdelige films samenvoegen",
        "suggerer_tags_exclus": "Tags voorstellen om uit te sluiten",
        "normaliser_roles": "Posities en rollen normaliseren",
        "retirer_pied_bio": "Biografie-voettekst verwijderen",
        "deduire_roles": "Posities en rollen voorstellen (AI)",
        "controler_heritage": "Uit een import overgenomen velden controleren",
        "ranger_champs_herites": "Uit een import overgenomen velden opruimen",
        "retirer_non_confirme": "Waarden zonder bron verwijderen",
        "retirer_champ_herite": "Overgenomen veld verwijderen",
        "marquer_roles_importes": "Geïmporteerde rollen als voorstel markeren",
        "inspecter_collecte": "Verzameling van een item inspecteren",
        "arbitrer_conflits": "Conflicten afstemmen op de bronnen",
        "sante_sources": "Status van de bronnen controleren",
        "proposer_scrapers": "Ontbrekende scrapers voorstellen",
        "lire_vignettes": "Watermerken van miniaturen lezen",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "Toepassingsmodus (manual / seuil / auto)",
        "autoAcceptThreshold": "Drempel voor bulkgoedkeuring (/10)",
        "strongMergeThreshold": "Sterke samenvoegdrempel",
        "annotateBio": "Bio-voettekst « Betrouwbaarheid gegevens »",
        "language": "Taal van de plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "Simulatiemodus (niets wordt weggeschreven)",
        "maxLlmCalls": "Maximum AI-aanroepen per taak "
                       "(0 = onbeperkt)",
        "llmDelayMs": "Pauze tussen AI-aanroepen (milliseconden)",
        "applySceneCovers": "Officiële covers verkiezen",
        "applyImages": "Afbeeldingen uit de bronnen toepassen",
        "positionAsTag": "Positie als standaardtag",
        "createMissing": "Onbekende items aanmaken (scènes)",
        "groupMinScenes": "Minimum aantal delen voor een groep",
        "batchSize": "Batchgrootte van de taken",
        "autoInstallScrapers": "Ontbrekende scrapers installeren",
        "scraperSource": "Scrapercatalogus",
        "visionEnvoiImages": "Miniaturen naar het beeldmodel sturen",
        "aiVision": "AI voor het lezen van afbeeldingen (aanbieder:model)",
        "visionPrompt": "Visie — instructies",
        "tagProfile": "Collectieprofiel (optioneel)",
        "tagsExclude": "Tags die nooit worden toegepast "
                       "(komma-gescheiden)",
        "refreshDays": "Versheid van de gegevens (dagen, 0 = nooit)",
        "generateBioHot": "Hot-bio genereren",
        "biohotPrompt": "Hot-bio — prompt-instructies",
        "biohotTemperature": "Hot-bio — temperatuur (0.0-1.5)",
        "autoMergeDuplicates": "Veilige duplicaten automatisch "
                               "samenvoegen",
        "proposalTagPrefix": "Voorvoegsel van de plugin-tags",
        "useUrlPass": "URL-ronde (scrapers per URL)",
        "useExtraSources": "Aanvullende bronnen (Wikipedia, ADE)",
        "useStashBoxes": "De ingestelde stash-boxes gebruiken",
        "scrapersExclude": "Uit te sluiten scrapers",
        "aiDefault": "Standaard-AI (aanbieder:model)",
        "aiBio": "AI voor feitelijke bio's",
        "aiSynopsis": "AI voor scène-samenvattingen",
        "aiBiohot": "AI voor de hot-bio",
        "mistralApiKey": "Mistral API-sleutel",
        "openaiApiKey": "OpenAI API-sleutel",
        "anthropicApiKey": "Anthropic API-sleutel",
        "llmApiKey": "Algemene API-sleutel",
        "openrouterApiKey": "OpenRouter API-sleutel",
        "groqApiKey": "Groq API-sleutel",
        "deepseekApiKey": "DeepSeek API-sleutel",
        "googleApiKey": "Google (Gemini) API-sleutel",
        "lmstudioUrl": "Adres van LM Studio",
        "perplexityApiKey": "Perplexity API-sleutel",
        "togetherApiKey": "Together API-sleutel",
        "xaiApiKey": "xAI API-sleutel",
        "llamacppUrl": "llama.cpp-adres",
        "vllmUrl": "vLLM-adres",
        "scrapersList": "Te gebruiken performer-scrapers",
        "ollamaUrl": "Adres van Ollama",
    },
    "msg": {
        "prompt_vision": (
            "Lees de op deze afbeelding zichtbare TEKST: watermerk "
            "van de studio, logo, webadres, ingebrande titel. "
            "Beschrijf de personen NIET, raad NIET wie ze zijn — geef "
            "alleen weer wat er GESCHREVEN staat. Is geen tekst "
            "leesbaar, antwoord null. Antwoord ALLEEN in JSON: "
            "{\"studio\": gelezen naam of null, \"texte_lu\": "
            "[gelezen tekenreeksen], \"confiance\": 0.0 tot 1.0}"),
        "prompt_donnees": "GEGEVENS :",
        "prompt_biohot": (
            "Schrijf in het {langue} de expliciete biografie van de "
            "homoporno-acteur '{nom}' voor een privé mediatheek. "
            "Directe, bewust rauwe toon, 3 tot 4 zinnen (max. 450 "
            "tekens): zijn neukstijl, zijn positie, zijn uitrusting, "
            "zijn vaste partners en studio's in de collectie. "
            "ABSOLUTE REGEL: baseer je ALLEEN op de gegevens "
            "hieronder; verzin GEEN praktijk (raw, fetisj…), GEEN "
            "positie en GEEN kenmerk dat er niet uitdrukkelijk staat. "
            "Is er weinig materiaal, hou het kort in plaats van te "
            "verzinnen. Antwoord alleen met de biografie."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTATIE: schrijf geen titel, geen naam vooraan, "
            "geen sterretjes, geen opmaak — de naam staat al boven de "
            "tekst, en opmaak wordt letterlijk getoond. Schrijf "
            "alleen zinnen."),
        "prompt_roles": (
            "Onderzoek de documentatie van een acteur op een "
            "UITDRUKKELIJKE vermelding van zijn gebruikelijke "
            "seksuele rol. ABSOLUTE REGEL: antwoord alleen als de "
            "tekst het duidelijk zegt. Leid NIETS af uit "
            "lichaamsbouw, geaardheid, nationaliteit, studio, "
            "scènetype of algemene indruk. Het gaat om een echt "
            "persoon: een gok zou een fout zijn, geen benadering. Bij "
            "twijfel antwoord null — niets concluderen is meestal het "
            "juiste antwoord. Antwoord ALLEEN met een JSON-object."),
        "prompt_synopsis": (
            "Schrijf in het {langue} een feitelijke synopsis van "
            "scène '{nom}' (max. 2 zinnen), zonder iets te verzinnen. "
            "Antwoord alleen met de synopsis.\n\n{donnees}"),
        "prompt_bio_studio": (
            "Schrijf in het {langue} een feitelijke voorstelling van "
            "studio '{nom}' (max. 3 zinnen), zonder iets te "
            "verzinnen. Antwoord alleen met de tekst.\n\n{donnees}"),
        "prompt_bio": (
            "Schrijf op basis van deze gegevens uit meerdere bronnen "
            "over acteur '{nom}' ÉÉN feitelijke biografie in het "
            "{langue} (max. 300 tekens), zonder iets te verzinnen. "
            "Antwoord alleen met de biografie.\n\n{donnees}"),
        "conflits": "CONFLICTEN (er is niets overschreven): "
                    "{details}",
        "conflit_ligne": "{champ}: huidig « {actuel} » vs bronnen: "
                         "{propose}",
        "doublon_probable": "WAARSCHIJNLIJK DUPLICAAT van: {jumeaux} "
                            "— knoppen « Samenvoegen » of « Geen "
                            "duplicaat » op deze pagina",
        "doublon_perf": "waarschijnlijk duplicaat van: {jumeaux} — "
                        "indien onjuist, tag {tag} plaatsen en de "
                        "detectie opnieuw uitvoeren",
        "par_nom_fichier": "herkend via de BESTANDSNAAM (geen "
                           "vingerafdruk, lagere betrouwbaarheid)",
        "coherence_fichier": "overeenkomst met de bestandsnaam "
                             "{score} ({detail})",
        "coherence_nulle": "⚠ de bestandsnaam komt niet overeen met "
                           "de identificatie — controleren",
        "fusion_trace": "duplicaat « {nom} » (id {id}) samengevoegd "
                        "op {date}",
        "restaure_trace": "hersteld op {date} (ronde van {passage})",
        "bio_hot_echec": "hot-bio niet gegenereerd — {motif} ({date})",
        "pied_bio": "― Betrouwbaarheid van de gegevens "
                    "(Gaizer) ―",
        "pied_bio_intro": "Automatisch ingevuld op {date} — "
                          "score /10 = geschatte betrouwbaarheid van "
                          "de bronnen.",
        "accepter_studio": " — knop « Accepteren » op deze pagina, "
                           "daarna de taak « Geaccepteerde studio's "
                           "toepassen »",
        "ia_quota": "quota of tegoed van het AI-account op",
        "ia_debit": "verzoekslimiet van de AI-aanbieder bereikt",
        "ia_cle": "API-sleutel geweigerd door de AI-aanbieder",
        "ia_modele": "AI-model onbekend of teruggetrokken door de "
                     "aanbieder",
        "ia_requete": "verzoek te lang voor het model",
        "ia_indispo": "AI-dienst overbelast — tijdelijk niet "
                      "beschikbaar",
        "ia_reseau": "geen netwerktoegang tot de AI-aanbieder",
        "ia_timeout": "de AI-aanbieder antwoordde niet op tijd",
        "ia_inattendu": "onverwachte fout van de AI-aanbieder",
        "ia_indisponible": "AI niet beschikbaar — {motif}",
        "ia_suspendue": "AI OPGESCHORT: {motif}. Het genereren van "
                        "teksten is verplaatst naar {date}; de "
                        "feitelijke verrijking gaat door. Taak "
                        "« Status van de agent » voor details.",
        "ia_en_pause": "AI-generatie gepauzeerd tot {date} ({motif}) "
                       "— feitelijke gegevens worden nog wel verrijkt",
        "ia_reprise": "AI-generatie hervat: de pauze van {pose} "
                      "({motif}) liep af op {date}. Openstaand werk "
                      "wordt opgepakt door de verrijkingstaken.",
        "plafond_ia": "limiet van {max} AI-aanroep(en) bereikt "
                      "(instelling maxLlmCalls) — volgende generaties "
                      "worden overgeslagen, voer de taak opnieuw uit",
        "simulation_active": "SIMULATIEMODUS actief: er wordt niets "
                             "naar Stash geschreven.",
        "simulation_evite": "  [SIMULATIE] {op} overgeslagen: "
                            "{details}",
    },
}

CATALOGUE = {"en": EN, "fr": FR, "de": DE, "es": ES, "it": IT,
             "pt": PT, "nl": NL}

# =====================================================================
#  DESCRIPTIONS LONGUES — anglais et français ; les autres langues
#  affichent l'anglais (voir l'explication en tête de fichier).
# =====================================================================
DESCRIPTIONS = {
    "en": {
        "enrich_performers": "Multi-source enrichment of incomplete "
            "performers: stash-boxes, installed name scrapers, URL "
            "pass, optional extra sources. Sources are scored, the "
            "best value is marked ★.",
        "enrich_scenes": "Identification by FINGERPRINT (phash) via "
            "the stash-boxes: title, date, studio, performers, source "
            "tags, factual synopsis, official cover. Falls back to "
            "the file name when no fingerprint matches.",
        "enrich_studios": "Factual description, URL, logo, aliases "
            "and parent network from the stash-boxes, plus collection "
            "statistics.",
        "apply_accepted": "Writes the proposals of performers tagged "
            "« accept », then removes the proposal tags.",
        "apply_accepted_scenes": "Fully applies the scenes tagged "
            "« accept », then removes the proposal tags.",
        "apply_accepted_studios": "Applies the studios accepted from "
            "their page. Studios have no tags in Stash, hence this "
            "dedicated task.",
        "apply_recommended": "Applies every ★ recommendation scoring "
            "at or above the threshold, for performers and scenes. "
            "Proposals below the threshold are left for you.",
        "apply_covers": "Fetches the official image of scenes already "
            "identified by fingerprint and replaces the generated "
            "thumbnail. Scenes that already have one are skipped.",
        "detect_duplicates": "Flags performers with nearly identical "
            "names. False alert: use the « Not a duplicate » button, "
            "the pair is then exempt for good.",
        "detect_duplicates_studios": "Same for studios "
            "(Men.Com/Men.com, Falcon/Falcon Studios).",
        "merge_marked": "Manual merge of the performers marked from "
            "their page. Destructive.",
        "merge_marked_studios": "Manual merge of the studios marked "
            "from their page. Destructive.",
        "dedoublonnage_complet": "Merges duplicates scoring at or "
            "above the strong threshold, including between curated "
            "entries. Destructive — turn on simulation mode first to "
            "see the list without changing anything.",
        "restore_marked": "Cancels the LAST enrichment pass of the "
            "marked entries (fields restored, added tags, performers "
            "and URLs removed).",
        "regenerate_biohot": "Redoes the hot bios generated before "
            "the scenes were linked, hence without partners. "
            "Argument toutes=1 to redo them all.",
        "position_tags": "Turns the legacy « position » custom field "
            "into a standard Stash tag on every performer.",
        "rapport_run": "Figures for the last run: fingerprint vs file "
            "name vs no identification, missing links, tags, "
            "performers created and enriched, studios. Also marks "
            "never-identified scenes so they can be filtered.",
        "rapport_tags": "Tag frequencies, near-duplicates and rare "
            "tags — the material for deciding on a normalisation. "
            "Read-only.",
        "etat_agent": "Health of the AI provider in plain language, "
            "current pause and its resume date, pending work, last "
            "incident.",
        "reprendre_ia": "Lifts the pause once its date has passed "
            "(forcer=1 to override) and regenerates the missing "
            "texts.",
        "migrer_langue": "Aligns the installation with the "
            "« language » setting: renames the tags already in place "
            "and translates the task names. No data is lost.",
        "clear_proposals": "Removes the proposal marker and value "
            "tags. Traceability tags are kept.",
        "enrich_one_performer": "Enriches a single performer — "
            "called by the button on the page.",
        "enrich_one_scene": "Enriches a single scene — called by the "
            "button on the page.",
        "enrich_one_studio": "Enriches a single studio — called by "
            "the button on the page.",
        "noop": "Technical entry point used by the buttons shown on "
            "the pages. Nothing to run manually from here.",
    },
    "fr": {
        "enrich_performers": "Enrichissement multi-sources des "
            "performers incomplets : stash-boxes, scrapers par nom "
            "installés, passe URL, sources d'appoint. Les sources "
            "sont notées, la meilleure valeur porte une ★.",
        "enrich_scenes": "Identification par EMPREINTE (phash) via "
            "les stash-boxes : titre, date, studio, performers, tags "
            "des sources, synopsis factuel, cover officielle. Repli "
            "sur le nom de fichier si aucune empreinte ne répond.",
        "enrich_studios": "Description factuelle, URL, logo, alias et "
            "réseau parent depuis les stash-boxes, plus les "
            "statistiques de la collection.",
        "apply_accepted": "Écrit les propositions des performers "
            "portant le tag « accept », puis retire les tags de "
            "proposition.",
        "apply_accepted_scenes": "Applique intégralement les scènes "
            "portant le tag « accept », puis retire les tags de "
            "proposition.",
        "apply_accepted_studios": "Applique les studios acceptés "
            "depuis leur fiche. Les studios n'ont pas de tags dans "
            "Stash, d'où cette tâche dédiée.",
        "apply_recommended": "Applique toutes les recommandations ★ "
            "dont la note atteint le seuil, performers et scènes. Les "
            "propositions sous le seuil restent à arbitrer.",
        "apply_covers": "Récupère l'image officielle des scènes déjà "
            "identifiées par empreinte et remplace la vignette "
            "générée. Les scènes déjà pourvues sont sautées.",
        "detect_duplicates": "Signale les performers aux noms quasi "
            "identiques. Fausse alerte : bouton « Pas un doublon », "
            "la paire est alors exemptée définitivement.",
        "detect_duplicates_studios": "Idem pour les studios "
            "(Men.Com/Men.com, Falcon/Falcon Studios).",
        "merge_marked": "Fusion manuelle des performers marqués "
            "depuis leur fiche. Destructif.",
        "merge_marked_studios": "Fusion manuelle des studios marqués "
            "depuis leur fiche. Destructif.",
        "dedoublonnage_complet": "Fusionne les doublons dont la note "
            "atteint le seuil fort, y compris entre fiches du "
            "référentiel. Destructif — activer le mode simulation "
            "d'abord pour voir la liste sans rien modifier.",
        "restore_marked": "Annule le DERNIER passage d'enrichissement "
            "des entités marquées (champs remis, tags, performers et "
            "URLs ajoutés retirés).",
        "regenerate_biohot": "Refait les bios hot générées avant que "
            "les scènes ne soient liées, donc sans partenaire. "
            "Argument toutes=1 pour tout régénérer.",
        "position_tags": "Convertit le champ custom « position » "
            "hérité en tag standard Stash sur chaque performer.",
        "rapport_run": "Bilan chiffré du dernier run : empreinte vs "
            "nom de fichier vs aucune identification, rattachements "
            "manquants, tags, performers créés et enrichis, studios. "
            "Marque aussi les scènes jamais identifiées pour les "
            "filtrer.",
        "rapport_tags": "Fréquences des tags, quasi-doublons et tags "
            "rares — la matière pour décider d'une normalisation. "
            "Lecture seule.",
        "etat_agent": "Santé du fournisseur d'IA en langage clair, "
            "pause éventuelle et date de reprise, travail en attente, "
            "dernier incident.",
        "reprendre_ia": "Lève la pause si sa date est passée "
            "(forcer=1 pour outrepasser) et relance les textes "
            "manquants.",
        "migrer_langue": "Aligne l'installation sur le réglage "
            "« Langue » : renomme les tags déjà posés et traduit les "
            "noms de tâches. Aucune donnée n'est perdue.",
        "clear_proposals": "Retire le marqueur et les tags-valeurs "
            "des propositions. Les tags de traçabilité sont "
            "conservés.",
        "enrich_one_performer": "Enrichit une seule fiche — appelée "
            "par le bouton de la page.",
        "enrich_one_scene": "Enrichit une seule scène — appelée par "
            "le bouton de la page.",
        "enrich_one_studio": "Enrichit un seul studio — appelée par "
            "le bouton de la page.",
        "noop": "Point d'entrée technique utilisé par les boutons "
            "affichés sur les fiches. Ne rien lancer manuellement "
            "depuis ici.",
    },
}


# ─────────────────────────── ACCÈS ───────────────────────────────────
def _chercher(famille: str, cle: str, langue: str) -> str:
    for lg in (langue, DEFAUT):
        val = (CATALOGUE.get(lg, {}).get(famille, {}) or {}).get(cle)
        if val:
            return val
    return cle


def t(cle: str, langue: str = DEFAUT, **kw) -> str:
    """Message traduit. Repli anglais puis clé."""
    texte = _chercher("msg", cle, langue)
    if texte == cle:
        texte = _chercher("boutons", cle, langue)
    try:
        return texte.format(**kw) if kw else texte
    except (KeyError, IndexError):
        return texte


def tag(cle: str, langue: str = DEFAUT) -> str:
    """Suffixe de tag traduit (sans le préfixe du plugin)."""
    return _chercher("tags", cle, langue)


def tache(cle: str, langue: str = DEFAUT) -> str:
    return _chercher("taches", cle, langue)


def reglage(cle: str, langue: str = DEFAUT) -> str:
    return _chercher("reglages", cle, langue)


def description(cle: str, langue: str = DEFAUT) -> str:
    for lg in (langue, DEFAUT):
        val = (DESCRIPTIONS.get(lg) or {}).get(cle)
        if val:
            return val
    return ""


def bouton(cle: str, langue: str = DEFAUT) -> str:
    return _chercher("boutons", cle, langue)


def toutes_variantes(famille: str, cle: str) -> set:
    """Toutes les traductions connues d'une chaîne — sert à retrouver
    du texte écrit avant un changement de langue."""
    return {(bloc.get(famille) or {}).get(cle)
            for bloc in CATALOGUE.values()
            if (bloc.get(famille) or {}).get(cle)}


def tous_les_tags(cle: str) -> set:
    """Toutes les variantes connues d'un tag, pour la migration."""
    return {(bloc.get("tags") or {}).get(cle)
            for bloc in CATALOGUE.values()
            if (bloc.get("tags") or {}).get(cle)}


def couverture() -> dict:
    """Taux de traduction par langue — utile en diagnostic."""
    ref = {f: set(EN[f]) for f in ("tags", "boutons", "taches",
                                   "reglages", "msg")}
    out = {}
    for lg, bloc in CATALOGUE.items():
        total = sum(len(v) for v in ref.values())
        presents = sum(len(set(bloc.get(f, {})) & cles)
                       for f, cles in ref.items())
        out[lg] = (presents, total)
    return out
