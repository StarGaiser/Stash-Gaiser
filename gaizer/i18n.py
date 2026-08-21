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
        "vider_cache": "Forget cached source replies",
        "lire_generiques": "Read opening and closing credits",
        "lire_chemins": "Read studio and cast from the file path",
        "appliquer_vision": "Apply studios read from thumbnails",
        "enrichir_tout": "Enrich everything (chains the active paths)",
        "appliquer_generiques": "Apply what was read from the credits",
        "valider_fiche": "Mark this record as checked",
        "prompt_defaut": "Show the default prompt",
        "generer_apercu": "Preview a generated text",
        "rapport_profil": "Collection profile report",
        "exporter_reglages": "Export settings",
        "importer_reglages": "Import settings",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Apply mode (manual / seuil / auto)",
        "autoAcceptThreshold": "6. Bulk approval threshold (score /10)",
        "strongMergeThreshold": "6. Strong merge threshold "
                                "(full deduplication)",
        "annotateBio": "2. « Data reliability » bio footer",
        "language": "1. Plugin language (en, fr, de, es, it, pt, nl)",
        "dryRun": "1. Simulation mode (no writes)",
        "maxLlmCalls": "3. AI call cap per task (0 = unlimited)",
        "llmDelayMs": "3. Delay between AI calls (milliseconds)",
        "applySceneCovers": "2. Prefer official covers",
        "applyImages": "2. Apply images from sources",
        "positionAsTag": "5. Position as a standard tag",
        "createMissing": "2. Create unknown entities (scenes)",
        "groupMinScenes": "6. Minimum parts to create a group",
        "batchSize": "1. Task batch size",
        "autoInstallScrapers": "4. Install missing scrapers",
        "scraperSource": "4. Scraper catalogue",
        "visionEnvoiImages": "3. Send thumbnails to the vision model",
        "aiVision": "3. AI for reading images (provider:model)",
        "deduireRoles": "3. Deduce sexual role from documentation",
        "sourceSavoirModele": "3. Let the model add what it knows",
        "visionPrompt": "3. Vision — prompt instructions",
        "tagProfile": "5. Collection profile (optional)",
        "tagsExclude": "5. Tags never to apply (comma separated)",
        "refreshDays": "4. Data freshness (days, 0 = never)",
        "sourceChemin": "4. Enrich from the file path",
        "sourceEnchainement": "4. Chain the paths on each scene",
        "sourceNomFichier": "4. Guess from the file name",
        "sourceVision": "4. Read thumbnail watermarks",
        "sourceGeneriques": "4. Read opening and closing credits",
        "cacheJours": "4. Source reply memory (days)",
        "generateBioHot": "2. Generate the hot bio",
        "biohotPrompt": "3. Hot bio — prompt instructions",
        "biohotTemperature": "3. Hot bio — temperature (0.0-1.5)",
        "autoMergeDuplicates": "2. Auto-merge safe duplicates",
        "proposalTagPrefix": "5. Prefix of the plugin's tags",
        "useUrlPass": "2. URL pass (per-URL scrapers)",
        "useExtraSources": "4. Extra sources (Wikipedia, ADE)",
        "useStashBoxes": "4. Use the configured stash-boxes",
        "scrapersExclude": "4. Scrapers to exclude",
        "aiDefault": "3. Default AI (provider:model)",
        "aiBio": "3. AI for factual bios",
        "aiSynopsis": "3. AI for scene synopses",
        "aiBiohot": "3. AI for the hot bio",
        "mistralApiKey": "Mistral API key",
        "openaiApiKey": "OpenAI API key",
        "anthropicApiKey": "Anthropic API key",
        "llmApiKey": "3. Generic API key (any provider)",
        "llmUrl": "3. Local service address",
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
        "scrapersList": "4. Performer scrapers to use",
        "ollamaUrl": "Ollama address",
    },
    "msg": {
        "prompt_generique": (
            "This image is a frame from the opening or closing "
            "credits of a video. Read ONLY the performer names "
            "written on it. Do NOT describe the people, do NOT guess "
            "who they are — report only what is WRITTEN. Ignore "
            "titles, dates, resolutions and watermarks. If no name is "
            "legible, answer an empty list. Invent nothing. Reply "
            "ONLY as JSON: {\"noms\": [names read], \"studio\": studio name or null}"),
        "prompt_vision": (
            "Read the TEXT visible on this image: studio watermark, "
            "logo, web address, on-screen title. Do NOT describe the "
            "people, do NOT guess who they are — only report what is "
            "WRITTEN. If no text is legible, answer null. Reply ONLY "
            "with JSON: {\"studio\": name read or null, \"texte_lu\": "
            "[exact strings read], \"confiance\": 0.0 to 1.0}"),
        "prompt_donnees": "DATA :",
        "profils_biohot": {
            "gay": (' of gay porn', 'the performer',
                "\n\nEXCEPTION: a performer who DECLARES himself straight and shoots gay is a genre hook worth naming. Only if he says so himself or the studio makes it a selling point: assuming anyone's orientation is forbidden."),
            "hetero": (' of straight porn', 'the performer',
                "\n\nEXCEPTION: a performer who DECLARES himself gay and shoots straight is a genre hook worth naming. Only if he says so himself or the studio makes it a selling point: assuming anyone's orientation is forbidden."),
            "lesbien": (' of lesbian porn', 'the performer',
                '\n\nEXCEPTION: a performer who DECLARES herself straight and shoots lesbian is a genre hook worth naming. Only if she says so herself or the studio makes it a selling point.'),
            "bi": (' of bi porn', 'the performer',
                ''),
            "pan": (' of pan porn', 'the performer',
                ''),
            "trans": (' of trans porn', 'the performer',
                '\n\nAnything touching gender identity is said only if the person states it themselves or the studio makes it a selling point: assuming it would be an intrusion, not information.'),
            "mixte": ('', 'the performer',
                ''),
        },
        "termes_personne": {
            "MALE": 'the performer',
            "FEMALE": 'the performer',
            "NEUTRE": 'the performer',
        },
        "prompt_biohot": (
            "You are a porn columnist{profil} of twenty years' "
            "standing: you know the studios, the careers, and you "
            "talk about them with relish. Introduce {qui} '{nom}' "
            "in {langue}, for a private library.\n\n"
            "OBJECTIVE. The reader owns these scenes and is "
            "deciding what to watch tonight. Make him WANT to go "
            "back to this performer: what makes him hot, what "
            "sets him apart. An inventory — “rugby build, four "
            "scenes here” — turns nobody on.\n\n"
            "TONE. Crude, precise, sensual. Call things what they "
            "are — cock, ass, fuck — without euphemism. Look for "
            "the image that shows rather than the adjective that "
            "comments. But crude is not lurid: no exclamations, "
            "no piled-up superlatives, no trailer copy.\n\n"
            "MATERIAL. Nothing but the data supplied below. Keep "
            "only what sheds light on his work: studios, how he "
            "fucks, physique, presence in the collection. Leave "
            "out private life and any career outside "
            "porn.{contraste}\n\n"
            "RESULT. 400 CHARACTERS MAXIMUM, ending included. "
            "That is short: three dense sentences, not four "
            "rambling ones. Count them. Every claim traceable in "
            "the data, something learned that a scene title would "
            "not tell, no filler. Do not repeat the name: it "
            "appears above the text.\n\n"
            "EXAMPLE of the tone expected, about another "
            "performer:\n"
            "“Ten years at Raging Stallion, and the same appetite "
            "throughout. Thick beard, heavy build, 19 uncut "
            "centimetres he does not spare. He takes charge with "
            "the patience of a man certain he will win, and the "
            "younger ones bear the brunt. Seven scenes here, "
            "three with the same partner.”\n\n"
            "ABSOLUTE RULE, overriding everything above. A good "
            "image needs a concrete detail: if you cannot find "
            "one in the data, WRITE WITHOUT THE IMAGE rather than "
            "invent one. A divorce, a former job, a cock size "
            "made up to sound good are lies about a real person, "
            "and nothing will flag them. Figures and proper nouns "
            "are copied, never estimated. Thin material: keep it "
            "short — two true sentences beat four invented ones.\n\n"
            "Answer with the text only, no preamble, no comment — "
            "and under 400 characters."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTATION: write no title, no name at the start, "
            "no asterisks, no markup — the name already appears above "
            "the text, and markup shows up as is. Write sentences "
            "only."),
        "prompt_biohot_apport": (
            "\n\n"
            "PERSONAL ADDITION, kept separate. If you know for "
            "CERTAIN something the data does not carry — an award "
            "received, a notable career fact — add it after the "
            "text, on a line beginning with [non vérifié]. One "
            "line at most, one sentence.\n\n"
            "Worth having: a Grabby, a GayVN, a role that made a "
            "mark, a studio exclusivity. Worth nothing: a guess, "
            "an \"it seems that\", anything you are unsure of. When "
            "in doubt, do not write that line at all — it is "
            "optional, and an invented award is worse than an "
            "award left unsaid.\n\n"
            "The main text itself contains ONLY what the data "
            "shows."),
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
        "vider_cache": "Oublier les réponses mémorisées",
        "lire_generiques": "Lire les génériques de début et de fin",
        "lire_chemins": "Lire le studio et la distribution dans le chemin",
        "appliquer_vision": "Appliquer les studios lus sur les vignettes",
        "enrichir_tout": "Tout enrichir (enchaîne les sources actives)",
        "appliquer_generiques": "Appliquer ce qui a été lu aux génériques",
        "valider_fiche": "Marquer cette fiche comme vérifiée",
        "prompt_defaut": "Relever le prompt par défaut",
        "generer_apercu": "Prévisualiser un texte généré",
        "rapport_profil": "Rapport du profil de collection",
        "exporter_reglages": "Exporter les réglages",
        "importer_reglages": "Importer des réglages",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Mode d'application (manual / seuil / auto)",
        "autoAcceptThreshold": "6. Seuil de validation de masse "
                               "(note /10)",
        "strongMergeThreshold": "6. Seuil fort de fusion "
                                "(dédoublonnage complet)",
        "annotateBio": "2. Pied de bio « Fiabilité des données »",
        "language": "1. Langue du plugin (fr, en, de, es, it, pt, nl)",
        "dryRun": "1. Mode simulation (aucune écriture)",
        "maxLlmCalls": "3. Plafond d'appels à l'IA par tâche "
                       "(0 = illimité)",
        "llmDelayMs": "3. Espacement des appels à l'IA (millisecondes)",
        "applySceneCovers": "2. Privilégier les covers officielles",
        "applyImages": "2. Appliquer les photos des sources",
        "positionAsTag": "5. Position en tag standard",
        "createMissing": "2. Créer les entités inconnues (scènes)",
        "groupMinScenes": "6. Parties minimales pour constituer un groupe",
        "batchSize": "1. Taille de lot des tâches",
        "autoInstallScrapers": "4. Installer les scrapers manquants",
        "scraperSource": "4. Catalogue de scrapers",
        "visionEnvoiImages": "3. Envoyer les vignettes au modèle de vision",
        "aiVision": "3. IA pour la lecture d'images (fournisseur:modèle)",
        "deduireRoles": "3. Déduire le rôle depuis la documentation",
        "sourceSavoirModele": "3. Laisser le modèle ajouter ce qu'il sait",
        "visionPrompt": "3. Vision — instructions du prompt",
        "tagProfile": "5. Profil de collection (facultatif)",
        "tagsExclude": "5. Tags à ne jamais appliquer "
                       "(séparés par des virgules)",
        "refreshDays": "4. Fraîcheur des données (jours, 0 = jamais)",
        "sourceChemin": "4. Enrichir depuis le chemin des fichiers",
        "sourceEnchainement": "4. Enchaîner les sources sur chaque scène",
        "sourceNomFichier": "4. Deviner depuis le nom de fichier",
        "sourceVision": "4. Lire les filigranes des vignettes",
        "sourceGeneriques": "4. Lire les generiques de debut et de fin",
        "cacheJours": "4. Mémoire des réponses de sources (jours)",
        "generateBioHot": "2. Générer la bio « hot »",
        "biohotPrompt": "3. Bio hot — instructions du prompt",
        "biohotTemperature": "3. Bio hot — température (0.0-1.5)",
        "autoMergeDuplicates": "2. Fusion automatique des doublons sûrs",
        "proposalTagPrefix": "5. Préfixe des tags du plugin",
        "useUrlPass": "2. Passe URL (scrapers par URL)",
        "useExtraSources": "4. Sources d'appoint (Wikipedia, ADE)",
        "useStashBoxes": "4. Utiliser les stash-boxes configurées",
        "scrapersExclude": "4. Scrapers à exclure",
        "aiDefault": "3. IA par défaut (provider:modèle)",
        "aiBio": "3. IA pour les bios factuelles",
        "aiSynopsis": "3. IA pour les synopsis de scènes",
        "aiBiohot": "3. IA pour la bio « hot »",
        "mistralApiKey": "Clé d'API Mistral",
        "openaiApiKey": "Clé d'API OpenAI",
        "anthropicApiKey": "Clé d'API Anthropic",
        "llmApiKey": "3. Clé d'API générique (tout fournisseur)",
        "llmUrl": "3. Adresse d'un service local",
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
        "scrapersList": "4. Scrapers performer à utiliser",
        "ollamaUrl": "Adresse d'Ollama",
    },
    "msg": {
        "prompt_generique": (
            "Cette image est extraite du générique d'ouverture ou de "
            "fin d'une vidéo. Lis UNIQUEMENT les noms d'interprètes "
            "qui y sont écrits. Ne décris PAS les personnes, ne "
            "devine PAS qui elles sont — rapporte seulement ce qui "
            "est ÉCRIT. Ignore les titres, dates, résolutions et "
            "filigranes. Si aucun nom n'est lisible, réponds une "
            "liste vide. N'invente rien. Réponds UNIQUEMENT en JSON : "
            "{\"noms\": [noms lus], \"studio\": nom du studio ou null}"),
        "prompt_vision": (
            "Lis le TEXTE visible sur cette image : filigrane de "
            "studio, logo, adresse web, titre incrusté. Ne décris PAS "
            "les personnes, ne devine PAS qui elles sont — rapporte "
            "uniquement ce qui est ÉCRIT. Si aucun texte n'est "
            "lisible, réponds null. Réponds UNIQUEMENT en JSON : "
            "{\"studio\": nom lu ou null, \"texte_lu\": [chaînes "
            "exactes lues], \"confiance\": 0.0 à 1.0}"),
        "prompt_donnees": "DONNÉES :",
        "profils_biohot": {
            "gay": (' du porno gay', "l'acteur",
                "\n\nEXCEPTION : un acteur qui se DÉCLARE hétéro et tourne gay est un ressort du genre, à dire. Uniquement s'il l'affiche ou si le studio en fait un argument : supposer l'orientation de quelqu'un est interdit."),
            "hetero": (' du porno hétéro', "l'acteur",
                "\n\nEXCEPTION : un acteur qui se DÉCLARE gay et tourne hétéro est un ressort du genre, à dire. Uniquement s'il l'affiche ou si le studio en fait un argument : supposer l'orientation de quelqu'un est interdit."),
            "lesbien": (' du porno lesbien', "l'actrice",
                "\n\nEXCEPTION : une actrice qui se DÉCLARE hétéro et tourne lesbien est un ressort du genre, à dire. Uniquement si elle l'affiche ou si le studio en fait un argument : supposer l'orientation de quelqu'un est interdit."),
            "bi": (' du porno bi', "l'interprète",
                ''),
            "pan": (' du porno pan', "l'interprète",
                ''),
            "trans": (' du porno trans', "l'interprète",
                "\n\nCe qui touche à la transidentité ne se dit que si la personne l'affiche elle-même ou si le studio en fait un argument : le supposer serait une atteinte, non une information."),
            "mixte": ('', "l'interprète",
                ''),
        },
        "termes_personne": {
            "MALE": "l'acteur",
            "FEMALE": "l'actrice",
            "NEUTRE": "l'interprète",
        },
        "prompt_biohot": (
            "Tu es chroniqueur{profil} depuis vingt ans : tu "
            "connais les studios, les carrières, et tu en parles "
            "avec gourmandise. Présente {qui} '{nom}' en "
            "{langue}, pour une médiathèque privée.\n\n"
            "OBJECTIF. Le lecteur possède ces scènes et cherche "
            "laquelle regarder ce soir. Donne-lui ENVIE de revoir "
            "cet acteur : ce qu'il a de bandant, ce qui le "
            "distingue. Un inventaire — « physique de rugbyman, "
            "quatre scènes ici » — n'excite personne.\n\n"
            "TON. Cru, précis, sensuel. Nomme les choses — bite, "
            "cul, baise — sans euphémisme. Cherche l'image qui "
            "fait voir plutôt que l'adjectif qui commente. Mais "
            "cru n'est pas outré : ni exclamations, ni "
            "superlatifs empilés, ni formules de bande-annonce.\n\n"
            "MATIÈRE. Rien que les données fournies plus bas. Ne "
            "retiens que ce qui éclaire son travail : studios, "
            "façon de baiser, physique, présence dans la "
            "collection. Écarte la vie privée et le parcours hors "
            "porno.{contraste}\n\n"
            "RÉSULTAT. 400 SIGNES MAXIMUM, fin comprise. C'est "
            "court : trois phrases denses, pas quatre "
            "phrases-fleuves. Compte-les. Chaque affirmation "
            "traçable dans les données, on y apprend ce qu'un "
            "titre de scène ne dirait pas, aucune phrase de "
            "remplissage. Ne répète pas le nom : il s'affiche "
            "au-dessus du texte.\n\n"
            "EXEMPLE du ton attendu, sur un autre acteur :\n"
            "« Dix ans chez Raging Stallion, et toujours le même "
            "appétit. Barbe drue, corps épais, 19 cm non "
            "circoncis qu'il ne ménage pas. Il prend le dessus "
            "avec la patience d'un mec sûr de gagner, et les plus "
            "jeunes en font les frais. Sept scènes ici, dont "
            "trois avec le même partenaire. »\n\n"
            "RÈGLE ABSOLUE, qui prime sur tout ce qui précède. "
            "Une belle image réclame un détail concret : si tu ne "
            "le trouves pas dans les données, ÉCRIS SANS IMAGE "
            "plutôt que d'en inventer un. Un divorce, un ancien "
            "métier, une taille de bite inventés pour faire joli "
            "sont des mensonges sur une personne réelle, que rien "
            "ne signalera. Les chiffres et les noms propres se "
            "recopient, ils ne s'estiment pas. Matière maigre : "
            "fais court, deux phrases vraies valent mieux que "
            "quatre inventées.\n\n"
            "Réponds uniquement le texte, sans préambule ni "
            "commentaire — et sous 400 signes."),
        "prompt_biohot_consignes": (
            "\n\n"
            "FORME. N'écris ni titre, ni nom en tête, ni "
            "astérisques, ni tirets de liste, ni aucun balisage : "
            "le nom figure déjà au-dessus du texte, et le "
            "balisage s'affiche tel quel dans Stash. Rédige des "
            "phrases suivies, rien d'autre."),
        "prompt_biohot_apport": (
            "\n\n"
            "APPORT PERSONNEL, à part. Si tu sais avec CERTITUDE "
            "une chose que les données ne portent pas — une "
            "récompense reçue, un fait de carrière marquant — "
            "ajoute-la après le texte, sur une ligne commençant "
            "par [non vérifié]. Une ligne au plus, une phrase.\n\n"
            "Ce qui vaut la peine : un Grabby, un GayVN, un rôle "
            "qui a marqué, une exclusivité de studio. Ce qui ne "
            "vaut rien : une supposition, un « il semble que », "
            "un fait dont tu n'es pas sûr. Dans le doute, n'écris "
            "pas cette ligne du tout — elle est facultative, et "
            "une récompense inventée est pire qu'une récompense "
            "tue.\n\n"
            "Le texte principal, lui, ne contient QUE ce que les "
            "données montrent."),
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
        "vider_cache": "Gespeicherte Antworten verwerfen",
        "lire_generiques": "Vor- und Abspann lesen",
        "lire_chemins": "Studio und Besetzung aus dem Dateipfad lesen",
        "appliquer_vision": "Aus Vorschaubildern gelesene Studios anwenden",
        "enrichir_tout": "Alles anreichern (verkettet die aktiven Wege)",
        "appliquer_generiques": "Aus dem Abspann Gelesenes anwenden",
        "valider_fiche": "Diesen Eintrag als geprüft markieren",
        "prompt_defaut": "Standard-Prompt anzeigen",
        "generer_apercu": "Generierten Text vorschauen",
        "rapport_profil": "Bericht zum Sammlungsprofil",
        "exporter_reglages": "Einstellungen exportieren",
        "importer_reglages": "Einstellungen importieren",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Anwendungsmodus (manual / seuil / auto)",
        "autoAcceptThreshold": "6. Schwelle für Massenübernahme (/10)",
        "strongMergeThreshold": "6. Starke Zusammenführungsschwelle",
        "annotateBio": "2. Bio-Fußzeile « Datenzuverlässigkeit »",
        "language": "1. Sprache des Plugins (en, fr, de, es, it, pt, nl)",
        "dryRun": "1. Simulationsmodus (keine Schreibvorgänge)",
        "maxLlmCalls": "3. Obergrenze KI-Aufrufe pro Aufgabe (0 = frei)",
        "llmDelayMs": "3. Abstand zwischen KI-Aufrufen (Millisekunden)",
        "applySceneCovers": "2. Offizielle Cover bevorzugen",
        "applyImages": "2. Bilder aus den Quellen übernehmen",
        "positionAsTag": "5. Position als Standard-Tag",
        "createMissing": "2. Unbekannte Einträge anlegen (Szenen)",
        "groupMinScenes": "6. Mindestanzahl Teile für eine Gruppe",
        "batchSize": "1. Stapelgröße der Aufgaben",
        "autoInstallScrapers": "4. Fehlende Scraper installieren",
        "scraperSource": "4. Scraper-Katalog",
        "visionEnvoiImages": "3. Vorschaubilder an das Bildmodell senden",
        "aiVision": "3. KI für Bildlesung (Anbieter:Modell)",
        "deduireRoles": "3. Sexuelle Rolle aus der Dokumentation ableiten",
        "sourceSavoirModele": "3. Modell darf Eigenwissen ergänzen",
        "visionPrompt": "3. Vision — Anweisungen",
        "tagProfile": "5. Sammlungsprofil (optional)",
        "tagsExclude": "5. Nie zu vergebende Tags (kommagetrennt)",
        "refreshDays": "4. Datenaktualität (Tage, 0 = nie)",
        "sourceChemin": "4. Aus dem Dateipfad anreichern",
        "sourceEnchainement": "4. Wege pro Szene verketten",
        "sourceNomFichier": "4. Aus dem Dateinamen erraten",
        "sourceVision": "4. Wasserzeichen der Vorschaubilder lesen",
        "sourceGeneriques": "4. Vor- und Abspann lesen",
        "cacheJours": "4. Speicherdauer für Quellantworten (Tage)",
        "generateBioHot": "2. Hot-Biografie erzeugen",
        "biohotPrompt": "3. Hot-Biografie — Prompt-Anweisungen",
        "biohotTemperature": "3. Hot-Biografie — Temperatur (0.0-1.5)",
        "autoMergeDuplicates": "2. Sichere Duplikate automatisch "
                               "zusammenführen",
        "proposalTagPrefix": "5. Präfix der Plugin-Tags",
        "useUrlPass": "2. URL-Durchlauf (URL-Scraper)",
        "useExtraSources": "4. Zusatzquellen (Wikipedia, ADE)",
        "useStashBoxes": "4. Konfigurierte Stash-Boxen verwenden",
        "scrapersExclude": "4. Auszuschließende Scraper",
        "aiDefault": "3. Standard-KI (Anbieter:Modell)",
        "aiBio": "3. KI für sachliche Biografien",
        "aiSynopsis": "3. KI für Szenen-Inhaltsangaben",
        "aiBiohot": "3. KI für die Hot-Biografie",
        "mistralApiKey": "Mistral API-Schlüssel",
        "openaiApiKey": "OpenAI API-Schlüssel",
        "anthropicApiKey": "Anthropic API-Schlüssel",
        "llmApiKey": "3. Allgemeiner API-Schlüssel",
        "llmUrl": "3. Adresse eines lokalen Dienstes",
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
        "scrapersList": "4. Zu verwendende Darsteller-Scraper",
        "ollamaUrl": "Ollama-Adresse",
    },
    "msg": {
        "prompt_generique": (
            "Dieses Bild stammt aus dem Vor- oder Abspann eines "
            "Videos. Lies NUR die dort geschriebenen Darstellernamen. "
            "Beschreibe die Personen NICHT, errate NICHT, wer sie "
            "sind — gib nur wieder, was GESCHRIEBEN steht. Ignoriere "
            "Titel, Daten, Auflösungen und Wasserzeichen. Ist kein "
            "Name lesbar, antworte mit einer leeren Liste. Erfinde "
            "nichts. Antworte NUR als JSON: {\"noms\": [gelesene Namen], \"studio\": Studioname oder null}"),
        "prompt_vision": (
            "Lies den auf diesem Bild sichtbaren TEXT: "
            "Studio-Wasserzeichen, Logo, Webadresse, eingeblendeter "
            "Titel. Beschreibe die Personen NICHT, errate NICHT, wer "
            "sie sind — gib nur wieder, was GESCHRIEBEN steht. Ist "
            "kein Text lesbar, antworte null. Antworte NUR als JSON: "
            "{\"studio\": gelesener Name oder null, \"texte_lu\": "
            "[gelesene Zeichenfolgen], \"confiance\": 0.0 bis 1.0}"),
        "prompt_donnees": "DATEN :",
        "profils_biohot": {
            "gay": (' für Gay-Pornos', 'den Darsteller',
                '\n\nAUSNAHME: ein Darsteller, der sich als hetero BEZEICHNET und schwul dreht, ist ein Reiz des Genres. Nur wenn er es selbst sagt oder das Studio damit wirbt: die Orientierung zu unterstellen ist verboten.'),
            "hetero": (' für Hetero-Pornos', 'den Darsteller',
                '\n\nAUSNAHME: ein Darsteller, der sich als schwul BEZEICHNET und hetero dreht, ist ein Reiz des Genres. Nur wenn er es selbst sagt oder das Studio damit wirbt.'),
            "lesbien": (' für Lesben-Pornos', 'die Darstellerin',
                '\n\nAUSNAHME: eine Darstellerin, die sich als hetero BEZEICHNET und lesbisch dreht, ist ein Reiz des Genres. Nur wenn sie es selbst sagt.'),
            "bi": (' für Bi-Pornos', 'die Person',
                ''),
            "pan": (' für Pan-Pornos', 'die Person',
                ''),
            "trans": (' für Trans-Pornos', 'die Person',
                '\n\nWas die Geschlechtsidentität betrifft, wird nur gesagt, wenn die Person es selbst angibt oder das Studio damit wirbt.'),
            "mixte": ('', 'die Person',
                ''),
        },
        "termes_personne": {
            "MALE": 'den Darsteller',
            "FEMALE": 'die Darstellerin',
            "NEUTRE": 'die Person',
        },
        "prompt_biohot": (
            "Du bist seit zwanzig Jahren Porno-Kolumnist{profil}: "
            "du kennst die Studios, die Karrieren, und sprichst "
            "mit Genuss darüber. Stelle {qui} '{nom}' auf "
            "{langue} vor, für eine private Mediathek.\n\n"
            "ZIEL. Der Leser besitzt diese Szenen und sucht, was "
            "er heute Abend schaut. Mach ihm LUST, diesen "
            "Darsteller wiederzusehen: was ihn geil macht, was "
            "ihn auszeichnet. Eine Aufzählung — „Rugby-Statur, "
            "vier Szenen hier“ — erregt niemanden.\n\n"
            "TON. Derb, präzise, sinnlich. Nenne die Dinge beim "
            "Namen — Schwanz, Arsch, ficken — ohne Beschönigung. "
            "Suche das Bild, das zeigt, statt des Adjektivs, das "
            "kommentiert. Aber derb ist nicht reißerisch: keine "
            "Ausrufe, keine gehäuften Superlative, keine "
            "Trailer-Floskeln.\n\n"
            "MATERIAL. Nur die unten gelieferten Daten. Behalte "
            "nur, was seine Arbeit erhellt: Studios, wie er "
            "fickt, Körper, Präsenz in der Sammlung. Lass "
            "Privatleben und Werdegang außerhalb des Pornos "
            "weg.{contraste}\n\n"
            "ERGEBNIS. HÖCHSTENS 400 ZEICHEN, Schluss "
            "inbegriffen. Das ist kurz: drei dichte Sätze, keine "
            "vier ausufernden. Zähle sie. Jede Aussage in den "
            "Daten belegbar, etwas erfahren, was ein Szenentitel "
            "nicht sagt, keine Füllsätze. Wiederhole den Namen "
            "nicht: er steht über dem Text.\n\n"
            "BEISPIEL für den erwarteten Ton, über einen anderen "
            "Darsteller:\n"
            "„Zehn Jahre bei Raging Stallion, und immer derselbe "
            "Appetit. Dichter Bart, schwerer Körper, 19 "
            "unbeschnittene Zentimeter, die er nicht schont. Er "
            "übernimmt mit der Geduld eines Mannes, der weiß, "
            "dass er gewinnt, und die Jüngeren tragen die Folgen. "
            "Sieben Szenen hier, drei mit demselben Partner.“\n\n"
            "ABSOLUTE REGEL, die alles Vorherige überwiegt. Ein "
            "gutes Bild braucht ein konkretes Detail: findest du "
            "keines in den Daten, SCHREIBE OHNE BILD, statt eines "
            "zu erfinden. Eine Scheidung, ein früherer Beruf, "
            "eine Schwanzlänge, erfunden um gut zu klingen, sind "
            "Lügen über eine reale Person, die nichts kenntlich "
            "macht. Zahlen und Eigennamen werden abgeschrieben, "
            "nie geschätzt. Dünnes Material: fasse dich kurz — "
            "zwei wahre Sätze schlagen vier erfundene.\n\n"
            "Antworte nur mit dem Text, ohne Vorrede, ohne "
            "Kommentar — und unter 400 Zeichen."),
        "prompt_biohot_consignes": (
            "\n\nDARSTELLUNG: kein Titel, kein Name am Anfang, keine "
            "Sternchen, keine Auszeichnung — der Name steht bereits "
            "über dem Text, und Auszeichnung wird wörtlich angezeigt. "
            "Schreibe nur Sätze."),
        "prompt_biohot_apport": (
            "\n\n"
            "PERSÖNLICHE ERGÄNZUNG, gesondert. Weißt du mit "
            "SICHERHEIT etwas, das die Daten nicht enthalten — "
            "eine erhaltene Auszeichnung, ein markanter "
            "Karrierepunkt —, füge es nach dem Text an, in einer "
            "Zeile, die mit [non vérifié] beginnt. Höchstens eine "
            "Zeile, ein Satz.\n\n"
            "Lohnt sich: ein Grabby, ein GayVN, eine prägende "
            "Rolle, eine Studio-Exklusivität. Lohnt sich nicht: "
            "eine Vermutung, ein „es scheint, dass“, etwas, "
            "dessen du nicht sicher bist. Im Zweifel schreibe "
            "diese Zeile gar nicht — sie ist freiwillig, und eine "
            "erfundene Auszeichnung ist schlimmer als eine "
            "verschwiegene.\n\n"
            "Der Haupttext enthält NUR, was die Daten zeigen."),
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
        "vider_cache": "Olvidar las respuestas memorizadas",
        "lire_generiques": "Leer los créditos iniciales y finales",
        "lire_chemins": "Leer el estudio y el reparto en la ruta del archivo",
        "appliquer_vision": "Aplicar los estudios leidos en las miniaturas",
        "enrichir_tout": "Enriquecer todo (encadena las vías activas)",
        "appliquer_generiques": "Aplicar lo leído en los créditos",
        "valider_fiche": "Marcar esta ficha como verificada",
        "prompt_defaut": "Mostrar el prompt por defecto",
        "generer_apercu": "Previsualizar un texto generado",
        "rapport_profil": "Informe del perfil de colección",
        "exporter_reglages": "Exportar los ajustes",
        "importer_reglages": "Importar ajustes",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Modo de aplicación (manual / seuil / auto)",
        "autoAcceptThreshold": "6. Umbral de aprobación en masa (/10)",
        "strongMergeThreshold": "6. Umbral fuerte de fusión",
        "annotateBio": "2. Pie de biografía « Fiabilidad de los datos »",
        "language": "1. Idioma del plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "1. Modo simulación (sin escrituras)",
        "maxLlmCalls": "3. Límite de llamadas a la IA por tarea "
                       "(0 = sin límite)",
        "llmDelayMs": "3. Espaciado entre llamadas a la IA "
                      "(milisegundos)",
        "applySceneCovers": "2. Preferir las carátulas oficiales",
        "applyImages": "2. Aplicar las imágenes de las fuentes",
        "positionAsTag": "5. Posición como etiqueta estándar",
        "createMissing": "2. Crear fichas desconocidas (escenas)",
        "groupMinScenes": "6. Partes mínimas para crear un grupo",
        "batchSize": "1. Tamaño de lote de las tareas",
        "autoInstallScrapers": "4. Instalar los scrapers que faltan",
        "scraperSource": "4. Catálogo de scrapers",
        "visionEnvoiImages": "3. Enviar las miniaturas al modelo de visión",
        "aiVision": "3. IA para lectura de imágenes (proveedor:modelo)",
        "deduireRoles": "3. Deducir el rol sexual de la documentación",
        "sourceSavoirModele": "3. Permitir que el modelo añada lo que sabe",
        "visionPrompt": "3. Visión — instrucciones",
        "tagProfile": "5. Perfil de colección (opcional)",
        "tagsExclude": "5. Etiquetas que nunca se aplican "
                       "(separadas por comas)",
        "refreshDays": "4. Frescura de los datos (días, 0 = nunca)",
        "sourceChemin": "4. Enriquecer desde la ruta del archivo",
        "sourceEnchainement": "4. Encadenar las vías en cada escena",
        "sourceNomFichier": "4. Deducir del nombre del archivo",
        "sourceVision": "4. Leer las marcas de agua de las miniaturas",
        "sourceGeneriques": "4. Leer los creditos iniciales y finales",
        "cacheJours": "4. Memoria de respuestas de fuentes (días)",
        "generateBioHot": "2. Generar la biografía « hot »",
        "biohotPrompt": "3. Biografía hot — instrucciones del prompt",
        "biohotTemperature": "3. Biografía hot — temperatura (0.0-1.5)",
        "autoMergeDuplicates": "2. Fusión automática de duplicados "
                               "seguros",
        "proposalTagPrefix": "5. Prefijo de las etiquetas del plugin",
        "useUrlPass": "2. Pasada de URL (scrapers por URL)",
        "useExtraSources": "4. Fuentes complementarias (Wikipedia, ADE)",
        "useStashBoxes": "4. Usar las stash-boxes configuradas",
        "scrapersExclude": "4. Scrapers a excluir",
        "aiDefault": "3. IA por defecto (proveedor:modelo)",
        "aiBio": "3. IA para las biografías factuales",
        "aiSynopsis": "3. IA para las sinopsis de escenas",
        "aiBiohot": "3. IA para la biografía « hot »",
        "mistralApiKey": "Clave de API de Mistral",
        "openaiApiKey": "Clave de API de OpenAI",
        "anthropicApiKey": "Clave de API de Anthropic",
        "llmApiKey": "3. Clave de API genérica",
        "llmUrl": "3. Dirección de un servicio local",
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
        "scrapersList": "4. Scrapers de intérpretes a usar",
        "ollamaUrl": "Dirección de Ollama",
    },
    "msg": {
        "prompt_generique": (
            "Esta imagen procede de los créditos iniciales o finales "
            "de un vídeo. Lee ÚNICAMENTE los nombres de intérpretes "
            "escritos en ella. NO describas a las personas, NO "
            "adivines quiénes son — informa solo de lo que está "
            "ESCRITO. Ignora títulos, fechas, resoluciones y marcas "
            "de agua. Si ningún nombre es legible, responde una lista "
            "vacía. No inventes nada. Responde ÚNICAMENTE en JSON: "
            "{\"noms\": [nombres leídos], \"studio\": nombre del estudio o null}"),
        "prompt_vision": (
            "Lee el TEXTO visible en esta imagen: marca de agua del "
            "estudio, logotipo, dirección web, título incrustado. NO "
            "describas a las personas, NO adivines quiénes son — "
            "informa solo de lo que está ESCRITO. Si no hay texto "
            "legible, responde null. Responde ÚNICAMENTE en JSON: "
            "{\"studio\": nombre leído o null, \"texte_lu\": [cadenas "
            "leídas], \"confiance\": 0.0 a 1.0}"),
        "prompt_donnees": "DATOS :",
        "profils_biohot": {
            "gay": (' del porno gay', 'al actor',
                '\n\nEXCEPCIÓN: un actor que se DECLARA hétero y rueda gay es un resorte del género, digno de mención. Solo si él mismo lo dice o el estudio lo usa como argumento: suponer la orientación de alguien está prohibido.'),
            "hetero": (' del porno hétero', 'al actor',
                '\n\nEXCEPCIÓN: un actor que se DECLARA gay y rueda hétero es un resorte del género. Solo si él mismo lo dice o el estudio lo usa como argumento.'),
            "lesbien": (' del porno lésbico', 'a la actriz',
                '\n\nEXCEPCIÓN: una actriz que se DECLARA hétero y rueda lésbico es un resorte del género. Solo si ella misma lo dice.'),
            "bi": (' del porno bi', 'a la intérprete',
                ''),
            "pan": (' del porno pan', 'a la intérprete',
                ''),
            "trans": (' del porno trans', 'a la intérprete',
                '\n\nLo relativo a la identidad de género solo se dice si la persona lo declara o el estudio lo usa como argumento.'),
            "mixte": ('', 'a la intérprete',
                ''),
        },
        "termes_personne": {
            "MALE": 'al actor',
            "FEMALE": 'a la actriz',
            "NEUTRE": 'a la intérprete',
        },
        "prompt_biohot": (
            "Eres cronista{profil} desde hace veinte años: "
            "conoces los estudios, las carreras, y hablas de ello "
            "con gusto. Presenta {qui} '{nom}' en {langue}, para "
            "una mediateca privada.\n\n"
            "OBJETIVO. El lector posee estas escenas y busca cuál "
            "ver esta noche. Dale GANAS de volver a ver a este "
            "actor: lo que tiene de excitante, lo que lo "
            "distingue. Un inventario — «físico de rugbier, "
            "cuatro escenas aquí» — no excita a nadie.\n\n"
            "TONO. Crudo, preciso, sensual. Llama a las cosas por "
            "su nombre — polla, culo, follar — sin eufemismos. "
            "Busca la imagen que hace ver más que el adjetivo que "
            "comenta. Pero crudo no es chabacano: ni "
            "exclamaciones, ni superlativos amontonados, ni "
            "fórmulas de tráiler.\n\n"
            "MATERIA. Nada más que los datos facilitados abajo. "
            "Retén solo lo que ilumina su trabajo: estudios, cómo "
            "folla, físico, presencia en la colección. Descarta "
            "la vida privada y la trayectoria fuera del "
            "porno.{contraste}\n\n"
            "RESULTADO. 400 CARACTERES COMO MÁXIMO, final "
            "incluido. Es corto: tres frases densas, no cuatro "
            "interminables. Cuéntalas. Cada afirmación rastreable "
            "en los datos, se aprende algo que un título de "
            "escena no diría, ninguna frase de relleno. No "
            "repitas el nombre: aparece encima del texto.\n\n"
            "EJEMPLO del tono esperado, sobre otro actor:\n"
            "«Diez años en Raging Stallion, y siempre el mismo "
            "apetito. Barba espesa, cuerpo macizo, 19 centímetros "
            "sin circuncidar que no escatima. Toma el mando con "
            "la paciencia de quien sabe que va a ganar, y los más "
            "jóvenes lo pagan. Siete escenas aquí, tres con la "
            "misma pareja.»\n\n"
            "REGLA ABSOLUTA, que prima sobre todo lo anterior. "
            "Una buena imagen exige un detalle concreto: si no lo "
            "encuentras en los datos, ESCRIBE SIN IMAGEN en vez "
            "de inventarlo. Un divorcio, un antiguo oficio, un "
            "tamaño de polla inventados para quedar bien son "
            "mentiras sobre una persona real, que nada señalará. "
            "Las cifras y los nombres propios se copian, no se "
            "estiman. Materia escasa: sé breve — dos frases "
            "ciertas valen más que cuatro inventadas.\n\n"
            "Responde solo el texto, sin preámbulo ni comentario "
            "— y por debajo de 400 caracteres."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTACIÓN: no escribas título, ni nombre al "
            "principio, ni asteriscos, ni marcado alguno — el nombre "
            "ya figura encima del texto, y el marcado se muestra tal "
            "cual. Redacta solo frases."),
        "prompt_biohot_apport": (
            "\n\n"
            "APORTE PERSONAL, aparte. Si sabes con CERTEZA algo "
            "que los datos no contienen — un premio recibido, un "
            "hecho de carrera destacado — añádelo tras el texto, "
            "en una línea que empiece por [non vérifié]. Una "
            "línea como máximo, una frase.\n\n"
            "Vale la pena: un Grabby, un GayVN, un papel que "
            "marcó, una exclusividad de estudio. No vale nada: "
            "una suposición, un «parece que», un dato del que no "
            "estés seguro. En la duda, no escribas esa línea — es "
            "facultativa, y un premio inventado es peor que un "
            "premio callado.\n\n"
            "El texto principal contiene SOLO lo que los datos "
            "muestran."),
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
        "vider_cache": "Dimentica le risposte memorizzate",
        "lire_generiques": "Leggi i titoli di testa e di coda",
        "lire_chemins": "Leggi studio e cast dal percorso del file",
        "appliquer_vision": "Applica gli studi letti dalle miniature",
        "enrichir_tout": "Arricchisci tutto (concatena le vie attive)",
        "appliquer_generiques": "Applica quanto letto dai titoli",
        "valider_fiche": "Segna questa scheda come verificata",
        "prompt_defaut": "Mostra il prompt predefinito",
        "generer_apercu": "Anteprima di un testo generato",
        "rapport_profil": "Rapporto del profilo di collezione",
        "exporter_reglages": "Esportare le impostazioni",
        "importer_reglages": "Importare impostazioni",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Modalità di applicazione "
                     "(manual / seuil / auto)",
        "autoAcceptThreshold": "6. Soglia di approvazione in blocco (/10)",
        "strongMergeThreshold": "6. Soglia forte di unione",
        "annotateBio": "2. Piè di biografia « Affidabilità dei dati »",
        "language": "1. Lingua del plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "1. Modalità simulazione (nessuna scrittura)",
        "maxLlmCalls": "3. Tetto di chiamate all'IA per attività "
                       "(0 = illimitato)",
        "llmDelayMs": "3. Intervallo tra le chiamate all'IA "
                      "(millisecondi)",
        "applySceneCovers": "2. Preferire le copertine ufficiali",
        "applyImages": "2. Applicare le immagini delle fonti",
        "positionAsTag": "5. Posizione come tag standard",
        "createMissing": "2. Creare le schede sconosciute (scene)",
        "groupMinScenes": "6. Parti minime per creare un gruppo",
        "batchSize": "1. Dimensione del lotto delle attività",
        "autoInstallScrapers": "4. Installa gli scraper mancanti",
        "scraperSource": "4. Catalogo di scraper",
        "visionEnvoiImages": "3. Invia le miniature al modello di visione",
        "aiVision": "3. IA per la lettura di immagini (fornitore:modello)",
        "deduireRoles": "3. Dedurre il ruolo sessuale dalla documentazione",
        "sourceSavoirModele": "3. Lasciare che il modello aggiunga ciò che sa",
        "visionPrompt": "3. Visione — istruzioni",
        "tagProfile": "5. Profilo della raccolta (facoltativo)",
        "tagsExclude": "5. Tag da non applicare mai "
                       "(separati da virgole)",
        "refreshDays": "4. Freschezza dei dati (giorni, 0 = mai)",
        "sourceChemin": "4. Arricchire dal percorso del file",
        "sourceEnchainement": "4. Concatenare le vie su ogni scena",
        "sourceNomFichier": "4. Dedurre dal nome del file",
        "sourceVision": "4. Leggere le filigrane delle miniature",
        "sourceGeneriques": "4. Leggere i titoli di testa e di coda",
        "cacheJours": "4. Memoria delle risposte delle fonti (giorni)",
        "generateBioHot": "2. Generare la biografia « hot »",
        "biohotPrompt": "3. Biografia hot — istruzioni del prompt",
        "biohotTemperature": "3. Biografia hot — temperatura (0.0-1.5)",
        "autoMergeDuplicates": "2. Unione automatica dei doppioni sicuri",
        "proposalTagPrefix": "5. Prefisso dei tag del plugin",
        "useUrlPass": "2. Passaggio URL (scraper per URL)",
        "useExtraSources": "4. Fonti supplementari (Wikipedia, ADE)",
        "useStashBoxes": "4. Usare le stash-box configurate",
        "scrapersExclude": "4. Scraper da escludere",
        "aiDefault": "3. IA predefinita (fornitore:modello)",
        "aiBio": "3. IA per le biografie fattuali",
        "aiSynopsis": "3. IA per le sinossi delle scene",
        "aiBiohot": "3. IA per la biografia « hot »",
        "mistralApiKey": "Chiave API Mistral",
        "openaiApiKey": "Chiave API OpenAI",
        "anthropicApiKey": "Chiave API Anthropic",
        "llmApiKey": "3. Chiave API generica",
        "llmUrl": "3. Indirizzo di un servizio locale",
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
        "scrapersList": "4. Scraper interpreti da usare",
        "ollamaUrl": "Indirizzo di Ollama",
    },
    "msg": {
        "prompt_generique": (
            "Questa immagine proviene dai titoli di testa o di coda "
            "di un video. Leggi SOLO i nomi degli interpreti scritti "
            "su di essa. NON descrivere le persone, NON indovinare "
            "chi sono — riporta solo ciò che è SCRITTO. Ignora "
            "titoli, date, risoluzioni e filigrane. Se nessun nome è "
            "leggibile, rispondi con una lista vuota. Non inventare "
            "nulla. Rispondi SOLO in JSON: {\"noms\": [nomi letti], \"studio\": nome dello studio o null}"),
        "prompt_vision": (
            "Leggi il TESTO visibile su questa immagine: filigrana "
            "dello studio, logo, indirizzo web, titolo sovrimpresso. "
            "NON descrivere le persone, NON indovinare chi sono — "
            "riporta solo ciò che è SCRITTO. Se nessun testo è "
            "leggibile, rispondi null. Rispondi SOLO in JSON: "
            "{\"studio\": nome letto o null, \"texte_lu\": [stringhe "
            "lette], \"confiance\": 0.0 a 1.0}"),
        "prompt_donnees": "DATI :",
        "profils_biohot": {
            "gay": (' del porno gay', "l'attore",
                "\n\nECCEZIONE: un attore che si DICHIARA etero e gira gay è una molla del genere, da dire. Solo se lo dichiara lui stesso o se lo studio ne fa un argomento: supporre l'orientamento di qualcuno è vietato."),
            "hetero": (' del porno etero', "l'attore",
                '\n\nECCEZIONE: un attore che si DICHIARA gay e gira etero è una molla del genere. Solo se lo dichiara lui stesso o se lo studio ne fa un argomento.'),
            "lesbien": (' del porno lesbo', "l'attrice",
                "\n\nECCEZIONE: un'attrice che si DICHIARA etero e gira lesbo è una molla del genere. Solo se lo dichiara lei stessa."),
            "bi": (' del porno bi', "l'interprete",
                ''),
            "pan": (' del porno pan', "l'interprete",
                ''),
            "trans": (' del porno trans', "l'interprete",
                "\n\nCiò che tocca l'identità di genere si dice solo se la persona lo dichiara o se lo studio ne fa un argomento."),
            "mixte": ('', "l'interprete",
                ''),
        },
        "termes_personne": {
            "MALE": "l'attore",
            "FEMALE": "l'attrice",
            "NEUTRE": "l'interprete",
        },
        "prompt_biohot": (
            "Sei cronista{profil} da vent'anni: conosci gli "
            "studi, le carriere, e ne parli con gusto. Presenta "
            "{qui} '{nom}' in {langue}, per una mediateca "
            "privata.\n\n"
            "OBIETTIVO. Il lettore possiede queste scene e cerca "
            "quale guardare stasera. Fagli VENIRE VOGLIA di "
            "rivedere questo attore: cosa ha di eccitante, cosa "
            "lo distingue. Un inventario — «fisico da rugbista, "
            "quattro scene qui» — non eccita nessuno.\n\n"
            "TONO. Crudo, preciso, sensuale. Chiama le cose col "
            "loro nome — cazzo, culo, scopare — senza eufemismi. "
            "Cerca l'immagine che fa vedere più dell'aggettivo "
            "che commenta. Ma crudo non è sguaiato: né "
            "esclamazioni, né superlativi ammucchiati, né formule "
            "da trailer.\n\n"
            "MATERIA. Nient'altro che i dati forniti sotto. Tieni "
            "solo ciò che illumina il suo lavoro: studi, come "
            "scopa, fisico, presenza nella collezione. Scarta la "
            "vita privata e il percorso fuori dal "
            "porno.{contraste}\n\n"
            "RISULTATO. 400 CARATTERI AL MASSIMO, finale "
            "compreso. È poco: tre frasi dense, non quattro "
            "fiumi. Contale. Ogni affermazione rintracciabile nei "
            "dati, si impara qualcosa che un titolo di scena non "
            "direbbe, nessuna frase di riempimento. Non ripetere "
            "il nome: compare sopra il testo.\n\n"
            "ESEMPIO del tono atteso, su un altro attore:\n"
            "«Dieci anni a Raging Stallion, e sempre lo stesso "
            "appetito. Barba folta, corpo massiccio, 19 "
            "centimetri non circoncisi che non risparmia. Prende "
            "il comando con la pazienza di chi sa che vincerà, e "
            "i più giovani ne pagano il prezzo. Sette scene qui, "
            "tre con lo stesso partner.»\n\n"
            "REGOLA ASSOLUTA, che prevale su tutto quanto "
            "precede. Una bella immagine esige un dettaglio "
            "concreto: se non lo trovi nei dati, SCRIVI SENZA "
            "IMMAGINE invece di inventarlo. Un divorzio, un "
            "vecchio mestiere, una misura di cazzo inventati per "
            "far bella figura sono menzogne su una persona reale, "
            "che nulla segnalerà. Le cifre e i nomi propri si "
            "ricopiano, non si stimano. Materia scarsa: sii breve "
            "— due frasi vere valgono più di quattro inventate.\n\n"
            "Rispondi solo con il testo, senza preambolo né "
            "commento — e sotto i 400 caratteri."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTAZIONE: non scrivere titolo, né nome in "
            "testa, né asterischi, né alcun markup — il nome figura "
            "già sopra il testo, e il markup appare tale e quale. "
            "Scrivi solo frasi."),
        "prompt_biohot_apport": (
            "\n\n"
            "APPORTO PERSONALE, a parte. Se sai con CERTEZZA "
            "qualcosa che i dati non riportano — un premio "
            "ricevuto, un fatto di carriera notevole — aggiungilo "
            "dopo il testo, su una riga che inizia con [non "
            "vérifié]. Una riga al massimo, una frase.\n\n"
            "Vale la pena: un Grabby, un GayVN, un ruolo che ha "
            "segnato, un'esclusiva di studio. Non vale nulla: una "
            "supposizione, un «pare che», un fatto di cui non sei "
            "sicuro. Nel dubbio, non scrivere quella riga — è "
            "facoltativa, e un premio inventato è peggio di un "
            "premio taciuto.\n\n"
            "Il testo principale contiene SOLO ciò che i dati "
            "mostrano."),
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
        "vider_cache": "Esquecer as respostas memorizadas",
        "lire_generiques": "Ler os créditos iniciais e finais",
        "lire_chemins": "Ler o estúdio e o elenco no caminho do ficheiro",
        "appliquer_vision": "Aplicar os estudios lidos nas miniaturas",
        "enrichir_tout": "Enriquecer tudo (encadeia as vias ativas)",
        "appliquer_generiques": "Aplicar o que foi lido nos créditos",
        "valider_fiche": "Marcar esta ficha como verificada",
        "prompt_defaut": "Mostrar o prompt por omissão",
        "generer_apercu": "Pré-visualizar um texto gerado",
        "rapport_profil": "Relatório do perfil da coleção",
        "exporter_reglages": "Exportar as definições",
        "importer_reglages": "Importar definições",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Modo de aplicação (manual / seuil / auto)",
        "autoAcceptThreshold": "6. Limiar de aprovação em massa (/10)",
        "strongMergeThreshold": "6. Limiar forte de fusão",
        "annotateBio": "2. Rodapé da biografia "
                       "« Fiabilidade dos dados »",
        "language": "1. Idioma do plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "1. Modo simulação (sem escritas)",
        "maxLlmCalls": "3. Limite de chamadas à IA por tarefa "
                       "(0 = ilimitado)",
        "llmDelayMs": "3. Espaçamento entre chamadas à IA "
                      "(milissegundos)",
        "applySceneCovers": "2. Preferir as capas oficiais",
        "applyImages": "2. Aplicar as imagens das fontes",
        "positionAsTag": "5. Posição como etiqueta padrão",
        "createMissing": "2. Criar as fichas desconhecidas (cenas)",
        "groupMinScenes": "6. Partes mínimas para criar um grupo",
        "batchSize": "1. Tamanho do lote das tarefas",
        "autoInstallScrapers": "4. Instalar os scrapers em falta",
        "scraperSource": "4. Catálogo de scrapers",
        "visionEnvoiImages": "3. Enviar as miniaturas ao modelo de visão",
        "aiVision": "3. IA para leitura de imagens (fornecedor:modelo)",
        "deduireRoles": "3. Deduzir o papel sexual a partir da documentação",
        "sourceSavoirModele": "3. Permitir que o modelo acrescente o que sabe",
        "visionPrompt": "3. Visão — instruções",
        "tagProfile": "5. Perfil da coleção (opcional)",
        "tagsExclude": "5. Etiquetas a nunca aplicar "
                       "(separadas por vírgulas)",
        "refreshDays": "4. Frescura dos dados (dias, 0 = nunca)",
        "sourceChemin": "4. Enriquecer a partir do caminho do ficheiro",
        "sourceEnchainement": "4. Encadear as vias em cada cena",
        "sourceNomFichier": "4. Deduzir do nome do ficheiro",
        "sourceVision": "4. Ler as marcas de agua das miniaturas",
        "sourceGeneriques": "4. Ler os creditos iniciais e finais",
        "cacheJours": "4. Memória das respostas das fontes (dias)",
        "generateBioHot": "2. Gerar a biografia « hot »",
        "biohotPrompt": "3. Biografia hot — instruções do prompt",
        "biohotTemperature": "3. Biografia hot — temperatura (0.0-1.5)",
        "autoMergeDuplicates": "2. Fusão automática dos duplicados "
                               "seguros",
        "proposalTagPrefix": "5. Prefixo das etiquetas do plugin",
        "useUrlPass": "2. Passagem de URL (scrapers por URL)",
        "useExtraSources": "4. Fontes complementares (Wikipedia, ADE)",
        "useStashBoxes": "4. Usar as stash-boxes configuradas",
        "scrapersExclude": "4. Scrapers a excluir",
        "aiDefault": "3. IA por defeito (fornecedor:modelo)",
        "aiBio": "3. IA para as biografias factuais",
        "aiSynopsis": "3. IA para as sinopses das cenas",
        "aiBiohot": "3. IA para a biografia « hot »",
        "mistralApiKey": "Chave de API Mistral",
        "openaiApiKey": "Chave de API OpenAI",
        "anthropicApiKey": "Chave de API Anthropic",
        "llmApiKey": "3. Chave de API genérica",
        "llmUrl": "3. Endereço de um serviço local",
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
        "scrapersList": "4. Scrapers de intérpretes a usar",
        "ollamaUrl": "Endereço do Ollama",
    },
    "msg": {
        "prompt_generique": (
            "Esta imagem provém dos créditos iniciais ou finais de um "
            "vídeo. Lê APENAS os nomes de intérpretes nela escritos. "
            "NÃO descrevas as pessoas, NÃO adivinhes quem são — "
            "indica apenas o que está ESCRITO. Ignora títulos, datas, "
            "resoluções e marcas de água. Se nenhum nome for legível, "
            "responde uma lista vazia. Não inventes nada. Responde "
            "APENAS em JSON: {\"noms\": [nomes lidos], \"studio\": nome do estúdio ou null}"),
        "prompt_vision": (
            "Lê o TEXTO visível nesta imagem: marca de água do "
            "estúdio, logótipo, endereço web, título sobreposto. NÃO "
            "descrevas as pessoas, NÃO adivinhes quem são — indica "
            "apenas o que está ESCRITO. Se nenhum texto for legível, "
            "responde null. Responde APENAS em JSON: {\"studio\": "
            "nome lido ou null, \"texte_lu\": [cadeias lidas], "
            "\"confiance\": 0.0 a 1.0}"),
        "prompt_donnees": "DADOS :",
        "profils_biohot": {
            "gay": (' do porno gay', 'o ator',
                '\n\nEXCEÇÃO: um ator que se DECLARA hétero e filma gay é uma mola do género, digna de menção. Apenas se ele próprio o declarar ou se o estúdio disso fizer argumento: supor a orientação de alguém é proibido.'),
            "hetero": (' do porno hétero', 'o ator',
                '\n\nEXCEÇÃO: um ator que se DECLARA gay e filma hétero é uma mola do género. Apenas se ele próprio o declarar ou se o estúdio disso fizer argumento.'),
            "lesbien": (' do porno lésbico', 'a atriz',
                '\n\nEXCEÇÃO: uma atriz que se DECLARA hétero e filma lésbico é uma mola do género. Apenas se ela própria o declarar.'),
            "bi": (' do porno bi', 'o intérprete',
                ''),
            "pan": (' do porno pan', 'o intérprete',
                ''),
            "trans": (' do porno trans', 'o intérprete',
                '\n\nO que toca a identidade de género só se diz se a pessoa o declarar ou se o estúdio disso fizer argumento.'),
            "mixte": ('', 'o intérprete',
                ''),
        },
        "termes_personne": {
            "MALE": 'o ator',
            "FEMALE": 'a atriz',
            "NEUTRE": 'o intérprete',
        },
        "prompt_biohot": (
            "És cronista{profil} há vinte anos: conheces os "
            "estúdios, as carreiras, e falas disso com gosto. "
            "Apresenta {qui} '{nom}' em {langue}, para uma "
            "mediateca privada.\n\n"
            "OBJETIVO. O leitor possui estas cenas e procura qual "
            "ver esta noite. Dá-lhe VONTADE de rever este ator: o "
            "que tem de excitante, o que o distingue. Um "
            "inventário — «físico de râguebi, quatro cenas aqui» "
            "— não excita ninguém.\n\n"
            "TOM. Cru, preciso, sensual. Chama as coisas pelo "
            "nome — caralho, cu, foder — sem eufemismos. Procura "
            "a imagem que faz ver em vez do adjetivo que comenta. "
            "Mas cru não é berrante: nem exclamações, nem "
            "superlativos empilhados, nem fórmulas de trailer.\n\n"
            "MATÉRIA. Nada além dos dados fornecidos abaixo. "
            "Retém apenas o que ilumina o seu trabalho: estúdios, "
            "como fode, físico, presença na coleção. Descarta a "
            "vida privada e o percurso fora do porno.{contraste}\n\n"
            "RESULTADO. 400 CARACTERES NO MÁXIMO, fim incluído. É "
            "curto: três frases densas, não quatro intermináveis. "
            "Conta-as. Cada afirmação rastreável nos dados, "
            "aprende-se algo que um título de cena não diria, "
            "nenhuma frase de enchimento. Não repitas o nome: "
            "aparece acima do texto.\n\n"
            "EXEMPLO do tom esperado, sobre outro ator:\n"
            "«Dez anos na Raging Stallion, e sempre o mesmo "
            "apetite. Barba densa, corpo pesado, 19 centímetros "
            "não circuncidados que não poupa. Assume o comando "
            "com a paciência de quem sabe que vai ganhar, e os "
            "mais novos pagam-no. Sete cenas aqui, três com o "
            "mesmo parceiro.»\n\n"
            "REGRA ABSOLUTA, que prevalece sobre tudo o que "
            "precede. Uma boa imagem exige um pormenor concreto: "
            "se não o encontrares nos dados, ESCREVE SEM IMAGEM "
            "em vez de o inventares. Um divórcio, um antigo "
            "ofício, um tamanho de caralho inventados para soar "
            "bem são mentiras sobre uma pessoa real, que nada "
            "assinalará. Os números e os nomes próprios "
            "copiam-se, não se estimam. Matéria escassa: sê breve "
            "— duas frases verdadeiras valem mais que quatro "
            "inventadas.\n\n"
            "Responde apenas o texto, sem preâmbulo nem "
            "comentário — e abaixo dos 400 caracteres."),
        "prompt_biohot_consignes": (
            "\n\nAPRESENTAÇÃO: não escrevas título, nem nome no "
            "início, nem asteriscos, nem qualquer marcação — o nome "
            "já figura acima do texto, e a marcação aparece tal e "
            "qual. Escreve apenas frases."),
        "prompt_biohot_apport": (
            "\n\n"
            "CONTRIBUTO PESSOAL, à parte. Se sabes com CERTEZA "
            "algo que os dados não contêm — um prémio recebido, "
            "um facto de carreira marcante — acrescenta-o depois "
            "do texto, numa linha que comece por [non vérifié]. "
            "Uma linha no máximo, uma frase.\n\n"
            "Vale a pena: um Grabby, um GayVN, um papel que "
            "marcou, uma exclusividade de estúdio. Não vale nada: "
            "uma suposição, um «parece que», um facto de que não "
            "tens a certeza. Na dúvida, não escrevas essa linha — "
            "é facultativa, e um prémio inventado é pior que um "
            "prémio calado.\n\n"
            "O texto principal contém APENAS o que os dados "
            "mostram."),
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
        "vider_cache": "Onthouden antwoorden vergeten",
        "lire_generiques": "Begin- en aftiteling lezen",
        "lire_chemins": "Studio en cast uit het bestandspad lezen",
        "appliquer_vision": "Uit miniaturen gelezen studio's toepassen",
        "enrichir_tout": "Alles verrijken (koppelt de actieve wegen)",
        "appliquer_generiques": "Toepassen wat uit de aftiteling is gelezen",
        "valider_fiche": "Dit item als gecontroleerd markeren",
        "prompt_defaut": "Standaardprompt tonen",
        "generer_apercu": "Gegenereerde tekst voorvertonen",
        "rapport_profil": "Rapport van het collectieprofiel",
        "exporter_reglages": "Instellingen exporteren",
        "importer_reglages": "Instellingen importeren",
        "noop": "Gaizer",
    },
    "reglages": {
        "applyMode": "2. Toepassingsmodus (manual / seuil / auto)",
        "autoAcceptThreshold": "6. Drempel voor bulkgoedkeuring (/10)",
        "strongMergeThreshold": "6. Sterke samenvoegdrempel",
        "annotateBio": "2. Bio-voettekst « Betrouwbaarheid gegevens »",
        "language": "1. Taal van de plugin (en, fr, de, es, it, pt, nl)",
        "dryRun": "1. Simulatiemodus (niets wordt weggeschreven)",
        "maxLlmCalls": "3. Maximum AI-aanroepen per taak "
                       "(0 = onbeperkt)",
        "llmDelayMs": "3. Pauze tussen AI-aanroepen (milliseconden)",
        "applySceneCovers": "2. Officiële covers verkiezen",
        "applyImages": "2. Afbeeldingen uit de bronnen toepassen",
        "positionAsTag": "5. Positie als standaardtag",
        "createMissing": "2. Onbekende items aanmaken (scènes)",
        "groupMinScenes": "6. Minimum aantal delen voor een groep",
        "batchSize": "1. Batchgrootte van de taken",
        "autoInstallScrapers": "4. Ontbrekende scrapers installeren",
        "scraperSource": "4. Scrapercatalogus",
        "visionEnvoiImages": "3. Miniaturen naar het beeldmodel sturen",
        "aiVision": "3. AI voor het lezen van afbeeldingen (aanbieder:model)",
        "deduireRoles": "3. Seksuele rol afleiden uit de documentatie",
        "sourceSavoirModele": "3. Model mag toevoegen wat het weet",
        "visionPrompt": "3. Visie — instructies",
        "tagProfile": "5. Collectieprofiel (optioneel)",
        "tagsExclude": "5. Tags die nooit worden toegepast "
                       "(komma-gescheiden)",
        "refreshDays": "4. Versheid van de gegevens (dagen, 0 = nooit)",
        "sourceChemin": "4. Verrijken vanuit het bestandspad",
        "sourceEnchainement": "4. Wegen per scène koppelen",
        "sourceNomFichier": "4. Raden uit de bestandsnaam",
        "sourceVision": "4. Watermerken van miniaturen lezen",
        "sourceGeneriques": "4. Begin- en aftiteling lezen",
        "cacheJours": "4. Geheugen voor bronantwoorden (dagen)",
        "generateBioHot": "2. Hot-bio genereren",
        "biohotPrompt": "3. Hot-bio — prompt-instructies",
        "biohotTemperature": "3. Hot-bio — temperatuur (0.0-1.5)",
        "autoMergeDuplicates": "2. Veilige duplicaten automatisch "
                               "samenvoegen",
        "proposalTagPrefix": "5. Voorvoegsel van de plugin-tags",
        "useUrlPass": "2. URL-ronde (scrapers per URL)",
        "useExtraSources": "4. Aanvullende bronnen (Wikipedia, ADE)",
        "useStashBoxes": "4. De ingestelde stash-boxes gebruiken",
        "scrapersExclude": "4. Uit te sluiten scrapers",
        "aiDefault": "3. Standaard-AI (aanbieder:model)",
        "aiBio": "3. AI voor feitelijke bio's",
        "aiSynopsis": "3. AI voor scène-samenvattingen",
        "aiBiohot": "3. AI voor de hot-bio",
        "mistralApiKey": "Mistral API-sleutel",
        "openaiApiKey": "OpenAI API-sleutel",
        "anthropicApiKey": "Anthropic API-sleutel",
        "llmApiKey": "3. Algemene API-sleutel",
        "llmUrl": "3. Adres van een lokale dienst",
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
        "scrapersList": "4. Te gebruiken performer-scrapers",
        "ollamaUrl": "Adres van Ollama",
    },
    "msg": {
        "prompt_generique": (
            "Deze afbeelding komt uit de begin- of aftiteling van een "
            "video. Lees ALLEEN de daarop geschreven namen van "
            "acteurs. Beschrijf de personen NIET, raad NIET wie ze "
            "zijn — geef alleen weer wat er GESCHREVEN staat. Negeer "
            "titels, data, resoluties en watermerken. Is geen naam "
            "leesbaar, antwoord een lege lijst. Verzin niets. "
            "Antwoord ALLEEN in JSON: {\"noms\": [gelezen namen], \"studio\": studionaam of null}"),
        "prompt_vision": (
            "Lees de op deze afbeelding zichtbare TEKST: watermerk "
            "van de studio, logo, webadres, ingebrande titel. "
            "Beschrijf de personen NIET, raad NIET wie ze zijn — geef "
            "alleen weer wat er GESCHREVEN staat. Is geen tekst "
            "leesbaar, antwoord null. Antwoord ALLEEN in JSON: "
            "{\"studio\": gelezen naam of null, \"texte_lu\": "
            "[gelezen tekenreeksen], \"confiance\": 0.0 tot 1.0}"),
        "prompt_donnees": "GEGEVENS :",
        "profils_biohot": {
            "gay": (' van gayporno', 'de acteur',
                '\n\nUITZONDERING: een acteur die zichzelf hetero NOEMT en gay draait is een prikkel van het genre. Alleen als hij het zelf zegt of de studio er een argument van maakt: iemands geaardheid veronderstellen is verboden.'),
            "hetero": (' van heteroporno', 'de acteur',
                '\n\nUITZONDERING: een acteur die zichzelf gay NOEMT en hetero draait is een prikkel van het genre. Alleen als hij het zelf zegt.'),
            "lesbien": (' van lesbische porno', 'de actrice',
                '\n\nUITZONDERING: een actrice die zichzelf hetero NOEMT en lesbisch draait is een prikkel van het genre. Alleen als zij het zelf zegt.'),
            "bi": (' van biporno', 'de vertolker',
                ''),
            "pan": (' van panporno', 'de vertolker',
                ''),
            "trans": (' van transporno', 'de vertolker',
                '\n\nWat de genderidentiteit betreft wordt alleen gezegd als de persoon het zelf aangeeft of de studio er een argument van maakt.'),
            "mixte": ('', 'de vertolker',
                ''),
        },
        "termes_personne": {
            "MALE": 'de acteur',
            "FEMALE": 'de actrice',
            "NEUTRE": 'de vertolker',
        },
        "prompt_biohot": (
            "Je bent al twintig jaar pornocolumnist{profil}: je "
            "kent de studio's, de carrières, en je praat er met "
            "smaak over. Stel {qui} '{nom}' voor in het {langue}, "
            "voor een privémediatheek.\n\n"
            "DOEL. De lezer bezit deze scènes en zoekt wat hij "
            "vanavond kijkt. Geef hem ZIN om deze acteur terug te "
            "zien: wat hem geil maakt, wat hem onderscheidt. Een "
            "opsomming — „rugbylijf, vier scènes hier“ — windt "
            "niemand op.\n\n"
            "TOON. Rauw, precies, sensueel. Noem de dingen bij "
            "naam — pik, kont, neuken — zonder eufemisme. Zoek "
            "het beeld dat laat zien in plaats van het "
            "bijvoeglijk naamwoord dat becommentarieert. Maar "
            "rauw is niet schreeuwerig: geen uitroepen, geen "
            "opgestapelde superlatieven, geen trailerpraat.\n\n"
            "MATERIAAL. Niets dan de hieronder geleverde "
            "gegevens. Houd alleen wat zijn werk verheldert: "
            "studio's, hoe hij neukt, lichaam, aanwezigheid in de "
            "collectie. Laat privéleven en loopbaan buiten de "
            "porno weg.{contraste}\n\n"
            "RESULTAAT. MAXIMAAL 400 TEKENS, slot inbegrepen. Dat "
            "is kort: drie dichte zinnen, geen vier eindeloze. "
            "Tel ze. Elke bewering terugvindbaar in de gegevens, "
            "je leert iets wat een scènetitel niet zou zeggen, "
            "geen vulzinnen. Herhaal de naam niet: hij staat "
            "boven de tekst.\n\n"
            "VOORBEELD van de verwachte toon, over een andere "
            "acteur:\n"
            "„Tien jaar bij Raging Stallion, en steeds dezelfde "
            "honger. Dichte baard, zwaar lijf, 19 onbesneden "
            "centimeter die hij niet spaart. Hij neemt de leiding "
            "met het geduld van een man die weet dat hij wint, en "
            "de jongeren betalen de prijs. Zeven scènes hier, "
            "drie met dezelfde partner.“\n\n"
            "ABSOLUTE REGEL, die alles hierboven overtreft. Een "
            "goed beeld vraagt een concreet detail: vind je er "
            "geen in de gegevens, SCHRIJF DAN ZONDER BEELD in "
            "plaats van er een te verzinnen. Een scheiding, een "
            "vroeger beroep, een piklengte verzonnen om mooi te "
            "klinken zijn leugens over een echt mens, die niets "
            "zal signaleren. Cijfers en eigennamen worden "
            "overgeschreven, nooit geschat. Karig materiaal: hou "
            "het kort — twee ware zinnen zijn beter dan vier "
            "verzonnen.\n\n"
            "Antwoord alleen met de tekst, zonder inleiding of "
            "commentaar — en onder de 400 tekens."),
        "prompt_biohot_consignes": (
            "\n\nPRESENTATIE: schrijf geen titel, geen naam vooraan, "
            "geen sterretjes, geen opmaak — de naam staat al boven de "
            "tekst, en opmaak wordt letterlijk getoond. Schrijf "
            "alleen zinnen."),
        "prompt_biohot_apport": (
            "\n\n"
            "PERSOONLIJKE AANVULLING, apart. Weet je met "
            "ZEKERHEID iets wat de gegevens niet bevatten — een "
            "gewonnen prijs, een opvallend carrièrefeit — voeg "
            "het dan na de tekst toe, op een regel die begint met "
            "[non vérifié]. Hoogstens één regel, één zin.\n\n"
            "De moeite waard: een Grabby, een GayVN, een rol die "
            "indruk maakte, een studio-exclusiviteit. Niets "
            "waard: een gissing, een „het lijkt erop dat“, iets "
            "waarvan je niet zeker bent. Bij twijfel: schrijf die "
            "regel helemaal niet — hij is optioneel, en een "
            "verzonnen prijs is erger dan een verzwegen prijs.\n\n"
            "De hoofdtekst bevat ALLEEN wat de gegevens tonen."),
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


def t_msg(cle: str, langue: str = DEFAUT):
    """Une entrée de message NON textuelle, telle quelle.

    La table des profils de collection porte des tuples : `t()` les
    convertirait en chaîne et perdrait leur structure.
    """
    for lg in (langue, DEFAUT):
        bloc = (CATALOGUE.get(lg) or {}).get("msg") or {}
        if cle in bloc:
            return bloc[cle]
    return None


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
