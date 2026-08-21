// Gaizer — page de commande, accessible depuis la barre de navigation.
//
// Les tâches vivaient dans Settings → Tasks, mêlées à celles des autres
// plugins, sans ordre ni regroupement : trente-huit entrées dans une
// liste plate, où l'on ne trouvait pas ce qu'on cherchait. Cette page
// les présente par INTENTION — ce qu'on veut obtenir — plutôt que par
// ordre d'écriture, et montre la file d'attente, qui explique pourquoi
// une tâche paraît ne rien faire.
(function () {
  "use strict";

  const API = window.PluginApi;
  if (!API || !API.React || !API.patch) return;
  const React = API.React;
  const e = React.createElement;
  const LANG_DEFAUT = "en";

  // Stash place une icone devant chaque libelle d'onglet. Sans elle,
  // la barre du plugin se distingue au premier coup d'oeil de toutes
  // les autres — c'est precisement ce qu'il fallait eviter.
  //
  // Elles viennent de l'API. Les supposer presentes casserait
  // silencieusement chez qui a une autre version de Stash : leur
  // absence degrade vers le texte seul, jamais vers une page blanche.
  const FA = (API.libraries || {}).FontAwesomeSolid;
  const RFA = (API.libraries || {}).ReactFontAwesome;

  const ICONES = {
    simple: "faWandMagicSparkles",
    g_demarrage: "faLayerGroup",
    g_courant: "faSliders",
    g_menage: "faBroom",
    g_diagnostic: "faMagnifyingGlass",
    g_reparation: "faScrewdriverWrench",
    redaction: "faPenNib",
  };

  function Icone(props) {
    if (!FA || !RFA || !RFA.FontAwesomeIcon) return null;
    const glyphe = FA[ICONES[props.cle]];
    if (!glyphe) return null;
    return e(RFA.FontAwesomeIcon, {
      icon: glyphe,
      // Le libelle la suit : la faire annoncer doublerait
      // l'information pour un lecteur d'ecran.
      "aria-hidden": true,
      className: "mr-2",
    });
  }


  const L = {
    titre: { en: "Gaizer", fr: "Gaizer" },
    sous_titre: {
      en: "Enrich, tidy and check your library",
      fr: "Enrichir, ranger et contrôler la médiathèque",
      de: "Mediathek anreichern, aufräumen und prüfen",
      es: "Enriquecer, ordenar y comprobar la colección",
      it: "Arricchire, riordinare e controllare la raccolta",
      pt: "Enriquecer, arrumar e verificar a coleção",
      nl: "Verrijken, opruimen en controleren" },
    g_demarrage: { en: "By family", fr: "Par famille",
                   de: "Erste Schritte", es: "Primera puesta en marcha",
                   it: "Prima messa in opera",
                   pt: "Primeira colocação em marcha",
                   nl: "Eerste opstart" },
    g_courant: { en: "Refine", fr: "Affiner",
                 de: "Laufende Pflege", es: "Mantenimiento corriente",
                 it: "Manutenzione corrente",
                 pt: "Manutenção corrente", nl: "Regulier onderhoud" },
    g_menage: { en: "Tidying", fr: "Ménage",
                de: "Aufräumen", es: "Limpieza", it: "Pulizia",
                pt: "Arrumação", nl: "Opruimen" },
    g_diagnostic: { en: "Diagnostics", fr: "Diagnostic",
                    de: "Diagnose", es: "Diagnóstico",
                    it: "Diagnostica", pt: "Diagnóstico",
                    nl: "Diagnose" },
    g_reparation: { en: "Repair", fr: "Réparation",
                    de: "Reparatur", es: "Reparación",
                    it: "Riparazione", pt: "Reparação",
                    nl: "Herstel" },
    file_vide: { en: "No task running", fr: "Aucune tâche en cours",
                 de: "Keine Aufgabe aktiv", es: "Ninguna tarea en curso",
                 it: "Nessuna attività in corso",
                 pt: "Nenhuma tarefa em curso",
                 nl: "Geen taak actief" },
    file: { en: "Queue", fr: "File d'attente", de: "Warteschlange",
            es: "Cola", it: "Coda", pt: "Fila", nl: "Wachtrij" },
    une_seule: {
      en: "Stash runs one plugin task at a time: the others wait.",
      fr: "Stash n'exécute qu'une tâche de plugin à la fois : les "
          + "autres attendent leur tour.",
      de: "Stash führt jeweils nur eine Plugin-Aufgabe aus.",
      es: "Stash ejecuta una tarea de plugin a la vez.",
      it: "Stash esegue una sola attività di plugin alla volta.",
      pt: "O Stash executa uma tarefa de plugin de cada vez.",
      nl: "Stash voert één plugintaak tegelijk uit." },
    lancer: { en: "Run", fr: "Lancer", de: "Starten", es: "Ejecutar",
              it: "Avvia", pt: "Executar", nl: "Uitvoeren" },
    simuler: { en: "Dry run", fr: "Simuler", de: "Probelauf",
               es: "Simular", it: "Simula", pt: "Simular",
               nl: "Proefdraaien" },
    destructif: { en: "destructive", fr: "destructif",
                  de: "destruktiv", es: "destructivo",
                  it: "distruttivo", pt: "destrutivo",
                  nl: "destructief" },
    confirmer: {
      en: "« {t} » modifies your library and cannot be undone. Continue?",
      fr: "« {t} » modifie la médiathèque sans retour possible. "
          + "Continuer ?",
      de: "« {t} » ändert die Mediathek unwiderruflich. Fortfahren?",
      es: "« {t} » modifica la colección sin vuelta atrás. ¿Continuar?",
      it: "« {t} » modifica la raccolta senza ritorno. Continuare?",
      pt: "« {t} » altera a coleção sem retorno. Continuar?",
      nl: "« {t} » wijzigt de collectie onomkeerbaar. Doorgaan?" },
    d_simple: {
      en: "Fill in what can be filled, from the sources you have "
          + "enabled. Start here.",
      fr: "Compléter ce qui peut l'être, depuis les sources que vous "
          + "avez activées. Commencez ici.",
      de: "Ergänzen, was möglich ist, aus den aktivierten Quellen. "
          + "Hier beginnen.",
      es: "Completar lo que se pueda, desde las fuentes activadas. "
          + "Empiece aquí.",
      it: "Completare ciò che si può, dalle fonti attivate. "
          + "Inizia qui.",
      pt: "Completar o que for possível, a partir das fontes "
          + "ativadas. Comece aqui.",
      nl: "Aanvullen wat mogelijk is, uit de ingeschakelde bronnen. "
          + "Begin hier." },
    d_g_demarrage: {
      en: "Enrich one family at a time — scenes, performers, studios "
          + "— when you want to control what is touched.",
      fr: "Enrichir une famille à la fois — scènes, interprètes, "
          + "studios — pour maîtriser ce qui est touché.",
      de: "Einmalig auszuführen, in dieser Reihenfolge.",
      es: "Para ejecutar una vez, en este orden.",
      it: "Da eseguire una volta, in questo ordine.",
      pt: "Para executar uma vez, nesta ordem.",
      nl: "Eenmalig uit te voeren, in deze volgorde." },
    d_g_courant: {
      en: "Covers, groups, presentations, and applying what was "
          + "proposed.",
      fr: "Jaquettes, films en plusieurs parties, présentations, et "
          + "application de ce qui a été proposé.",
      de: "Nach dem Hinzufügen von Dateien, oder gelegentlich.",
      es: "Tras añadir archivos, o de vez en cuando.",
      it: "Dopo l'aggiunta di file, o di tanto in tanto.",
      pt: "Após adicionar ficheiros, ou de vez em quando.",
      nl: "Na het toevoegen van bestanden, of af en toe." },
    d_g_menage: {
      en: "Remove what is no longer needed. These write.",
      fr: "Retirer ce qui n'a plus lieu d'être. Ces actions écrivent.",
      de: "Entfernen, was nicht mehr nötig ist. Diese schreiben.",
      es: "Retirar lo que ya no hace falta. Estas acciones escriben.",
      it: "Rimuovere ciò che non serve più. Queste scrivono.",
      pt: "Remover o que já não é preciso. Estas escrevem.",
      nl: "Verwijderen wat niet meer nodig is. Deze schrijven." },
    d_g_diagnostic: {
      en: "Look without changing anything. Safe to run anytime.",
      fr: "Regarder sans rien changer. Aucune de ces actions "
          + "n'écrit.",
      de: "Ansehen, ohne etwas zu ändern. Keine schreibt.",
      es: "Mirar sin cambiar nada. Ninguna escribe.",
      it: "Guardare senza cambiare nulla. Nessuna scrive.",
      pt: "Ver sem mudar nada. Nenhuma escreve.",
      nl: "Kijken zonder iets te wijzigen. Geen enkele schrijft." },
    d_g_reparation: {
      en: "When something went wrong. Undo, restore, resume.",
      fr: "Quand quelque chose s'est mal passé : défaire, restaurer, "
          + "reprendre.",
      de: "Wenn etwas schiefging: rückgängig, wiederherstellen.",
      es: "Cuando algo salió mal: deshacer, restaurar, reanudar.",
      it: "Quando qualcosa è andato storto: annullare, ripristinare.",
      pt: "Quando algo correu mal: desfazer, restaurar, retomar.",
      nl: "Als er iets misging: ongedaan maken, herstellen." },
    d_redaction: {
      en: "Shape the biographies and presentations generated by the "
          + "model: what it is told, and how freely it writes.",
      fr: "Gouverner les biographies et présentations générées par le "
          + "modèle : ce qui lui est demandé, et la liberté qu'il "
          + "prend.",
      de: "Was dem Modell gesagt wird, und wie frei es schreibt.",
      es: "Lo que se pide al modelo, y la libertad que toma.",
      it: "Cosa viene chiesto al modello, e quanta libertà prende.",
      pt: "O que é pedido ao modelo, e a liberdade que toma.",
      nl: "Wat het model gevraagd wordt, en hoe vrij het schrijft." },
    b_lancer: {
      en: "Runs now and writes to your library.",
      fr: "Lance maintenant et écrit dans votre médiathèque.",
      de: "Startet jetzt und schreibt in Ihre Mediathek.",
      es: "Se ejecuta ahora y escribe en su mediateca.",
      it: "Esegue ora e scrive nella tua mediateca.",
      pt: "Executa agora e escreve na sua mediateca.",
      nl: "Start nu en schrijft in uw mediatheek." },
    b_simuler: {
      en: "Shows exactly what would change, without changing it.",
      fr: "Montre exactement ce qui changerait, sans rien changer.",
      de: "Zeigt genau, was sich ändern würde, ohne es zu ändern.",
      es: "Muestra exactamente qué cambiaría, sin cambiar nada.",
      it: "Mostra esattamente cosa cambierebbe, senza cambiarlo.",
      pt: "Mostra exatamente o que mudaria, sem mudar nada.",
      nl: "Toont precies wat zou veranderen, zonder te wijzigen." },
    vers_avance: { en: "Show everything", fr: "Tout afficher",
                   de: "Alles anzeigen", es: "Mostrar todo",
                   it: "Mostra tutto", pt: "Mostrar tudo",
                   nl: "Alles tonen" },
    vers_simple: { en: "Simplify", fr: "Simplifier",
                   de: "Vereinfachen", es: "Simplificar",
                   it: "Semplifica", pt: "Simplificar",
                   nl: "Vereenvoudigen" },
    d_vers_avance: {
      en: "Reveals the cleanup, diagnostic and repair tabs, and the "
          + "writing settings. Nothing is hidden that you cannot get "
          + "back.",
      fr: "Révèle les onglets Ménage, Diagnostic et Réparation, ainsi "
          + "que les réglages de rédaction. Rien n'est masqué que "
          + "vous ne puissiez retrouver.",
      de: "Zeigt die Reiter Aufräumen, Diagnose und Reparatur sowie "
          + "die Schreibeinstellungen.",
      es: "Revela las pestañas Limpieza, Diagnóstico y Reparación, y "
          + "los ajustes de redacción.",
      it: "Rivela le schede Pulizia, Diagnostica e Riparazione, e le "
          + "impostazioni di scrittura.",
      pt: "Revela os separadores Limpeza, Diagnóstico e Reparação, e "
          + "as definições de redação.",
      nl: "Toont de tabbladen Opruimen, Diagnose en Herstel, en de "
          + "schrijfinstellingen." },
    d_vers_simple: {
      en: "Keeps only what is needed day to day. Your settings are "
          + "kept, just not shown.",
      fr: "Ne garde que ce qui sert au quotidien. Vos réglages sont "
          + "conservés, simplement plus affichés.",
      de: "Behält nur das Alltägliche. Ihre Einstellungen bleiben "
          + "erhalten, werden nur nicht angezeigt.",
      es: "Conserva solo lo cotidiano. Sus ajustes se mantienen, "
          + "simplemente no se muestran.",
      it: "Conserva solo il quotidiano. Le impostazioni restano, "
          + "semplicemente non sono mostrate.",
      pt: "Mantém apenas o quotidiano. As suas definições são "
          + "mantidas, apenas não mostradas.",
      nl: "Houdt alleen het dagelijkse. Uw instellingen blijven "
          + "behouden, ze worden alleen niet getoond." },
    enregistre: { en: "saved", fr: "enregistré", de: "gespeichert",
                  es: "guardado", it: "salvato", pt: "guardado",
                  nl: "opgeslagen" },
    o_simple: { en: "Enrich", fr: "Enrichir", de: "Anreichern",
                es: "Enriquecer", it: "Arricchisci",
                pt: "Enriquecer", nl: "Verrijken" },
    a_enrichir_tout: {
      en: "Runs every enabled source on each incomplete record, "
          + "cheapest first. Run it again for the next batch.",
      fr: "Passe chaque source active sur les fiches incomplètes, de "
          + "la moins coûteuse à la plus coûteuse. Relancer pour le "
          + "lot suivant.",
      de: "Führt jede aktive Quelle auf unvollständigen Einträgen "
          + "aus. Erneut ausführen für den nächsten Stapel.",
      es: "Pasa cada fuente activa por las fichas incompletas. "
          + "Reejecutar para el siguiente lote.",
      it: "Applica ogni fonte attiva alle schede incomplete. "
          + "Rilanciare per il lotto successivo.",
      pt: "Aplica cada fonte ativa às fichas incompletas. Relançar "
          + "para o lote seguinte.",
      nl: "Past elke actieve bron toe op onvolledige items. Opnieuw "
          + "uitvoeren voor de volgende batch." },
    a_rapport_run: {
      en: "What the last run wrote, and what is still missing.",
      fr: "Ce que le dernier passage a écrit, et ce qui manque "
          + "encore.",
      de: "Was der letzte Durchlauf geschrieben hat, und was fehlt.",
      es: "Lo que escribió la última ejecución, y lo que falta.",
      it: "Cosa ha scritto l'ultima esecuzione, e cosa manca.",
      pt: "O que a última execução escreveu, e o que falta.",
      nl: "Wat de laatste run schreef, en wat nog ontbreekt." },
    a_undo_last: {
      en: "Restores the values as they were before the last run.",
      fr: "Rend aux fiches les valeurs qu'elles avaient avant le "
          + "dernier passage.",
      de: "Stellt die Werte von vor dem letzten Durchlauf wieder her.",
      es: "Restaura los valores anteriores a la última ejecución.",
      it: "Ripristina i valori precedenti all'ultima esecuzione.",
      pt: "Restaura os valores anteriores à última execução.",
      nl: "Herstelt de waarden van vóór de laatste run." },
    s_explication: {
      en: "One button. Gaizer fills in what it can — studio, title, "
          + "cast, date — from the sources you have enabled, cheapest "
          + "and most reliable first. Nothing already filled in is "
          + "overwritten, and everything written can be undone.",
      fr: "Un bouton. Gaizer complète ce qu'il peut — studio, titre, "
          + "distribution, date — depuis les sources que vous avez "
          + "activées, de la moins chère à la plus coûteuse. Rien de "
          + "déjà rempli n'est écrasé, et tout ce qui est écrit peut "
          + "être défait.",
      de: "Ein Knopf. Gaizer ergänzt, was möglich ist — Studio, Titel, "
          + "Besetzung, Datum — aus den aktivierten Quellen. Bereits "
          + "Ausgefülltes wird nicht überschrieben, und alles "
          + "Geschriebene lässt sich rückgängig machen.",
      es: "Un botón. Gaizer completa lo que puede — estudio, título, "
          + "reparto, fecha — desde las fuentes activadas. Nada de lo "
          + "ya rellenado se sobrescribe, y todo lo escrito puede "
          + "deshacerse.",
      it: "Un pulsante. Gaizer completa ciò che può — studio, titolo, "
          + "cast, data — dalle fonti attivate. Nulla di già compilato "
          + "viene sovrascritto, e tutto ciò che è scritto può essere "
          + "annullato.",
      pt: "Um botão. Gaizer completa o que pode — estúdio, título, "
          + "elenco, data — a partir das fontes ativadas. Nada do que "
          + "já está preenchido é substituído, e tudo o que é escrito "
          + "pode ser desfeito.",
      nl: "Eén knop. Gaizer vult aan wat het kan — studio, titel, "
          + "cast, datum — uit de ingeschakelde bronnen. Niets wat al "
          + "is ingevuld wordt overschreven, en alles wat wordt "
          + "geschreven kan ongedaan worden gemaakt." },
    s_detail: {
      en: "Everything else lives in the other tabs — one per intent.",
      fr: "Tout le reste vit dans les autres onglets, un par intention.",
      de: "Alles Weitere liegt in den anderen Reitern, einer je Absicht.",
      es: "Todo lo demás está en las otras pestañas, una por intención.",
      it: "Tutto il resto è nelle altre schede, una per intento.",
      pt: "Tudo o resto está nos outros separadores, um por intenção.",
      nl: "De rest staat in de andere tabbladen, één per bedoeling." },
    o_taches: { en: "Tasks", fr: "Tâches", de: "Aufgaben",
                es: "Tareas", it: "Attività", pt: "Tarefas",
                nl: "Taken" },
    partir_du_defaut: {
      en: "Start from the default prompt",
      fr: "Partir du prompt par défaut",
      de: "Mit dem Standard-Prompt beginnen",
      es: "Partir del prompt por defecto",
      it: "Partire dal prompt predefinito",
      pt: "Partir do prompt por omissão",
      nl: "Beginnen met de standaardprompt" },
    mod_titre: { en: "Choosing a model", fr: "Choisir un modèle",
                 de: "Modellwahl", es: "Elegir un modelo",
                 it: "Scegliere un modello",
                 pt: "Escolher um modelo", nl: "Een model kiezen" },
    mod_texte: {
      en: "Models differ widely on explicit content. Some refuse "
          + "outright, others soften what they write without saying "
          + "so — a text that comes back tame or evasive points at "
          + "the model, not at your prompt. Open-weight models run "
          + "locally (Ollama, LM Studio) have no external filter; "
          + "Mistral and DeepSeek write explicit text readily. The "
          + "large US providers apply stricter policies and may "
          + "refuse. Try one record before running a batch.",
      fr: "Les modèles diffèrent beaucoup devant le contenu "
          + "explicite. Certains refusent net, d'autres adoucissent "
          + "sans le dire — un texte qui revient sage ou évasif "
          + "désigne le modèle, non votre prompt. Les modèles à "
          + "poids ouverts exécutés en local (Ollama, LM Studio) "
          + "n'ont aucun filtre externe ; Mistral et DeepSeek "
          + "écrivent sans réserve. Les grands fournisseurs "
          + "américains appliquent des politiques plus strictes et "
          + "peuvent refuser. Essayez sur une fiche avant de lancer "
          + "un lot.",
      de: "Modelle unterscheiden sich stark bei expliziten Inhalten. "
          + "Ein zahmer Text weist auf das Modell hin, nicht auf "
          + "Ihren Prompt. Lokale Modelle (Ollama, LM Studio) haben "
          + "keinen externen Filter; Mistral und DeepSeek schreiben "
          + "ohne Zurückhaltung.",
      es: "Los modelos difieren mucho ante el contenido explícito. "
          + "Un texto sobrio señala al modelo, no a su prompt. Los "
          + "modelos locales (Ollama, LM Studio) no tienen filtro "
          + "externo; Mistral y DeepSeek escriben sin reservas.",
      it: "I modelli differiscono molto sui contenuti espliciti. Un "
          + "testo sobrio indica il modello, non il tuo prompt. I "
          + "modelli locali (Ollama, LM Studio) non hanno filtri "
          + "esterni; Mistral e DeepSeek scrivono senza riserve.",
      pt: "Os modelos diferem muito perante conteúdo explícito. Um "
          + "texto contido aponta para o modelo, não para o seu "
          + "prompt. Os modelos locais (Ollama, LM Studio) não têm "
          + "filtro externo; Mistral e DeepSeek escrevem sem "
          + "reservas.",
      nl: "Modellen verschillen sterk bij expliciete inhoud. Een "
          + "brave tekst wijst op het model, niet op uw prompt. "
          + "Lokale modellen (Ollama, LM Studio) hebben geen extern "
          + "filter; Mistral en DeepSeek schrijven onbevangen." },
    lim_titre: { en: "Length and limits", fr: "Longueur et limites",
                 de: "Länge und Grenzen",
                 es: "Longitud y límites",
                 it: "Lunghezza e limiti",
                 pt: "Comprimento e limites",
                 nl: "Lengte en grenzen" },
    lim_texte: {
      en: "Presentations are capped at about 660 characters. The cap "
          + "exists because a model always fills the space it is "
          + "given, output tokens cost more than input ones, and text "
          + "that overflows the record is paid for but never read. "
          + "Asking for a longer text in the prompt will not lift "
          + "it.",
      fr: "Les présentations sont bornées à environ 660 signes. La "
          + "borne existe parce qu'un modèle remplit toujours "
          + "l'espace qu'on lui laisse, que les jetons de sortie "
          + "coûtent plus cher que ceux d'entrée, et qu'un texte qui "
          + "déborde de la fiche est payé sans être lu. Demander plus "
          + "long dans le prompt ne la lèvera pas.",
      de: "Präsentationen sind auf etwa 660 Zeichen begrenzt. Ein "
          + "Modell füllt stets den gegebenen Raum, Ausgabe-Token "
          + "kosten mehr als Eingabe-Token, und überlaufender Text "
          + "wird bezahlt, aber nie gelesen.",
      es: "Las presentaciones se limitan a unos 660 caracteres. Un "
          + "modelo siempre llena el espacio que se le da, los tokens "
          + "de salida cuestan más que los de entrada, y el texto que "
          + "desborda se paga sin leerse.",
      it: "Le presentazioni sono limitate a circa 660 caratteri. Un "
          + "modello riempie sempre lo spazio concesso, i token di "
          + "uscita costano più di quelli in entrata, e il testo che "
          + "eccede viene pagato senza essere letto.",
      pt: "As apresentações estão limitadas a cerca de 660 "
          + "caracteres. Um modelo preenche sempre o espaço dado, os "
          + "tokens de saída custam mais que os de entrada, e o texto "
          + "que transborda é pago sem ser lido.",
      nl: "Presentaties zijn begrensd op ongeveer 660 tekens. Een "
          + "model vult altijd de gegeven ruimte, uitvoertokens "
          + "kosten meer dan invoertokens, en tekst die overloopt "
          + "wordt betaald maar niet gelezen." },
    lim_noms: {
      en: "Texts that name a studio or a person absent from the "
          + "record's own data are rejected and regenerated. A model "
          + "produces plausible names better than anything else, and "
          + "nobody checks a name that sounds right — the prompt says "
          + "so, and it is not enough.",
      fr: "Un texte qui nomme un studio ou une personne absents des "
          + "données de la fiche est refusé et régénéré. Un modèle "
          + "produit des noms plausibles mieux que tout le reste, et "
          + "personne ne vérifie un nom qui sonne juste — le prompt "
          + "le dit, et cela ne suffit pas.",
      de: "Texte, die ein Studio oder eine Person nennen, die in den "
          + "Daten fehlen, werden abgelehnt. Ein Modell erzeugt "
          + "plausible Namen besser als alles andere.",
      es: "Un texto que nombra un estudio o una persona ausentes de "
          + "los datos es rechazado. Un modelo produce nombres "
          + "plausibles mejor que nada.",
      it: "Un testo che nomina uno studio o una persona assenti dai "
          + "dati viene rifiutato. Un modello produce nomi "
          + "plausibili meglio di ogni altra cosa.",
      pt: "Um texto que nomeia um estúdio ou uma pessoa ausentes dos "
          + "dados é recusado. Um modelo produz nomes plausíveis "
          + "melhor do que tudo.",
      nl: "Een tekst die een studio of persoon noemt die niet in de "
          + "gegevens staat, wordt geweigerd." },
    m_titre: { en: "Model used", fr: "Modèle employé",
               de: "Verwendetes Modell", es: "Modelo empleado",
               it: "Modello impiegato", pt: "Modelo utilizado",
               nl: "Gebruikt model" },
    m_source_dedie: {
      en: "set for presentations", fr: "réglé pour les présentations",
      de: "für Präsentationen eingestellt",
      es: "ajustado para las presentaciones",
      it: "impostato per le presentazioni",
      pt: "definido para as apresentações",
      nl: "ingesteld voor presentaties" },
    m_source_defaut: {
      en: "the default model", fr: "le modèle par défaut",
      de: "das Standardmodell", es: "el modelo por defecto",
      it: "il modello predefinito", pt: "o modelo por omissão",
      nl: "het standaardmodel" },
    m_aucun: {
      en: "No model configured — set one in the plugin settings.",
      fr: "Aucun modèle configuré — renseignez-en un dans les "
          + "réglages du plugin.",
      de: "Kein Modell konfiguriert.",
      es: "Ningún modelo configurado.",
      it: "Nessun modello configurato.",
      pt: "Nenhum modelo configurado.",
      nl: "Geen model geconfigureerd." },
    o_redaction: { en: "Generated texts", fr: "Textes générés",
                   de: "Generierte Texte", es: "Textos generados",
                   it: "Testi generati", pt: "Textos gerados",
                   nl: "Gegenereerde teksten" },
    prompt: { en: "Instructions given to the model",
              fr: "Instructions données au modèle",
              de: "Anweisungen an das Modell",
              es: "Instrucciones dadas al modelo",
              it: "Istruzioni date al modello",
              pt: "Instruções dadas ao modelo",
              nl: "Instructies aan het model" },
    prompt_aide: {
      en: "Placeholders {langue}, {nom} and {donnees} are replaced "
          + "before sending. Leave empty to use the default.",
      fr: "Les repères {langue}, {nom} et {donnees} sont remplacés "
          + "avant envoi. Vide = instructions par défaut.",
      de: "Die Platzhalter {langue}, {nom} und {donnees} werden vor "
          + "dem Senden ersetzt. Leer = Standard.",
      es: "Los marcadores {langue}, {nom} y {donnees} se sustituyen "
          + "antes del envío. Vacío = valores por defecto.",
      it: "I segnaposto {langue}, {nom} e {donnees} sono sostituiti "
          + "prima dell'invio. Vuoto = valori predefiniti.",
      pt: "Os marcadores {langue}, {nom} e {donnees} são substituídos "
          + "antes do envio. Vazio = predefinição.",
      nl: "De plaatshouders {langue}, {nom} en {donnees} worden voor "
          + "verzending vervangen. Leeg = standaard." },
    temperature: { en: "Temperature", fr: "Température",
                   de: "Temperatur", es: "Temperatura",
                   it: "Temperatura", pt: "Temperatura",
                   nl: "Temperatuur" },
    temperature_aide: {
      en: "Low: factual and repetitive. High: varied and less "
          + "faithful to the data. 0.7 is a reasonable middle.",
      fr: "Basse : factuel et répétitif. Haute : varié et moins "
          + "fidèle aux données. 0,7 est un milieu raisonnable.",
      de: "Niedrig: sachlich und wiederholend. Hoch: abwechslungs"
          + "reicher, weniger datentreu. 0,7 ist ein guter Mittelweg.",
      es: "Baja: factual y repetitivo. Alta: variado y menos fiel a "
          + "los datos. 0,7 es un término medio razonable.",
      it: "Bassa: fattuale e ripetitivo. Alta: vario e meno fedele "
          + "ai dati. 0,7 è una via di mezzo ragionevole.",
      pt: "Baixa: factual e repetitivo. Alta: variado e menos fiel "
          + "aos dados. 0,7 é um meio-termo razoável.",
      nl: "Laag: feitelijk en herhalend. Hoog: gevarieerd en minder "
          + "trouw aan de gegevens. 0,7 is een redelijk midden." },
    enregistrer: { en: "Save", fr: "Enregistrer", de: "Speichern",
                   es: "Guardar", it: "Salva", pt: "Guardar",
                   nl: "Opslaan" },
    defaut: { en: "Restore default", fr: "Revenir au défaut",
              de: "Standard wiederherstellen",
              es: "Volver al valor por defecto",
              it: "Ripristina predefinito",
              pt: "Repor predefinição", nl: "Standaard herstellen" },
    enregistre: { en: "Saved", fr: "Enregistré", de: "Gespeichert",
                  es: "Guardado", it: "Salvato", pt: "Guardado",
                  nl: "Opgeslagen" },
    essai: { en: "Try on one entry", fr: "Essayer sur une fiche",
             de: "An einem Eintrag testen",
             es: "Probar en una ficha", it: "Prova su una scheda",
             pt: "Experimentar numa ficha",
             nl: "Op één item proberen" },
    essai_aide: {
      en: "Regenerates the presentation of a single entry so you can "
          + "judge before applying to the whole library.",
      fr: "Régénère la présentation d'une seule fiche, pour juger "
          + "avant d'appliquer à toute la médiathèque.",
      de: "Erzeugt die Vorstellung eines einzelnen Eintrags neu.",
      es: "Regenera la presentación de una sola ficha.",
      it: "Rigenera la presentazione di una sola scheda.",
      pt: "Regenera a apresentação de uma única ficha.",
      nl: "Genereert de presentatie van één item opnieuw." },
    lance: { en: "Started", fr: "Lancée", de: "Gestartet",
             es: "Iniciada", it: "Avviata", pt: "Iniciada",
             nl: "Gestart" },
    en_cours: { en: "working…", fr: "en cours…", de: "läuft…",
                es: "en curso…", it: "in corso…", pt: "em curso…",
                nl: "bezig…" },
    en_attente_n: { en: "queued", fr: "en attente", de: "wartend",
                    es: "en cola", it: "in coda", pt: "em fila",
                    nl: "in wachtrij" },
    arreter_tout: { en: "Stop all", fr: "Tout arrêter",
                    de: "Alle stoppen", es: "Detener todo",
                    it: "Ferma tutto", pt: "Parar tudo",
                    nl: "Alles stoppen" },
    arreter_tout_q: {
      en: "Stop the running task and clear the queue?",
      fr: "Arrêter la tâche en cours et vider la file d'attente ?",
      de: "Laufende Aufgabe stoppen und Warteschlange leeren?",
      es: "¿Detener la tarea en curso y vaciar la cola?",
      it: "Fermare l'attività in corso e svuotare la coda?",
      pt: "Parar a tarefa em curso e esvaziar a fila?",
      nl: "Lopende taak stoppen en wachtrij legen?" },
  };

  const ALIAS = { french: "fr", français: "fr", francais: "fr",
                  english: "en", anglais: "en", german: "de",
                  deutsch: "de", allemand: "de", spanish: "es",
                  español: "es", espanol: "es", espagnol: "es",
                  italian: "it", italiano: "it", italien: "it",
                  portuguese: "pt", português: "pt", portugues: "pt",
                  portugais: "pt", dutch: "nl", nederlands: "nl",
                  néerlandais: "nl" };
  const reglages = { lang: LANG_DEFAUT };
  const tr = (cle) => (L[cle] || {})[reglages.lang]
    || (L[cle] || {})[LANG_DEFAUT] || cle;

  const GQL = (query, variables) =>
    fetch("/graphql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables }),
    }).then((r) => r.json()).then((d) => {
      if (d.errors) throw new Error(d.errors[0].message);
      return d.data;
    });

  GQL(`{ configuration { plugins } }`).then((d) => {
    const c = (d.configuration.plugins || {})["gaizer"] || {};
    const brut = String(c.language || "").trim().toLowerCase();
    reglages.lang = L.titre[brut] ? brut : (ALIAS[brut] || LANG_DEFAUT);
  }).catch(() => {});

  // Les tâches rangées par INTENTION, et dans l'ordre où on les
  // emploie. Le premier de chaque groupe est celui qu'on cherche le
  // plus souvent : il est mis en avant.
  // Douze taches attendent un argument que rien ne permettait de
  // saisir : il fallait passer par l'ecran des plugins de Stash. La
  // description le disait, mais dire n'est pas offrir.
  //
  // Le champ n'apparait que sur les taches concernees : un champ vide
  // sur chaque ligne serait du bruit.
  // Ce que chaque argument attend, et sous quelle FORME.
  //
  // Quatre formes, choisies selon ce qui aide le plus :
  //   « oui-non »  une case a cocher, pour ce qui valait « 1 »
  //   « choix »    une liste, pour un ensemble ferme
  //   « nombre »   un champ numerique borne, avec son defaut
  //   « texte »    une invite qui donne un EXEMPLE, non une
  //                paraphrase du nom du champ
  //
  // Une faute de frappe sur un texte libre passe inapercue : la
  // valeur est ignoree, sans message. Fermer ce qui peut l'etre
  // supprime ce risque plutot que de l'annoncer.
  const ARGUMENTS = {
    // Sur une fiche precise : l'identifiant vient du contexte, mais
    // ces taches restent lancables depuis l'ecran des plugins.
    enrich_one_performer: ["performer_id", "texte",
                           "ex. Archie Fox, ou 42"],
    enrich_one_scene: ["scene_id", "texte", "ex. 1287"],
    enrich_one_studio: ["studio_id", "texte",
                        "ex. Raging Stallion, ou 17"],
    generer_apercu: ["performer_id", "texte", "ex. Archie Fox, ou 42"],
    valider_fiche: ["performer_id", "texte",
                    "ex. Archie Fox, ou 42"],
    inspecter_collecte: ["nom", "texte", "ex. Dean Young"],

    // Ce qui valait « 1 » : une case dit la meme chose sans qu'on
    // ait a deviner quelle valeur compte pour vrai.
    proposer_scrapers: ["installer", "oui-non",
                        "Installer ceux qui manquent"],
    lire_vignettes: ["relire", "oui-non",
                     "Relire celles deja lues"],
    lire_generiques: ["relire", "oui-non",
                      "Relire ceux deja lus"],
    appliquer_vision: ["incertaines", "oui-non",
                       "Inclure les propositions incertaines"],
    regenerate_biohot: ["toutes", "oui-non",
                        "Refaire aussi celles qui existent"],

    // Ensembles fermes : les lister evite de les taper de memoire.
    migrer_langue: ["langue", "choix", "Langue des textes"],
    retirer_champ_herite: ["champ", "texte",
                           "ex. sexe_cm, mensurations"],
    controler_heritage: ["champ", "texte",
                         "vide = tous les champs"],
    retirer_non_confirme: ["champs", "texte",
                           "vide = tous ; ex. details, url"],
    marquer_roles_importes: ["motif", "texte",
                             "ex. import CSV de 2023"],
    sante_sources: ["noms", "texte",
                    "vide = un echantillon ; ex. Dean Young"],

    // Borne : la plage et le defaut valent mieux qu'une invite.
    arbitrer_conflits: ["note", "nombre", "9.0", 0, 10],

    importer_reglages: ["fichier", "texte",
                        "Collez ici le contenu de l'export"],
  };

  // Les valeurs d'un argument ferme. Chacune porte un libelle qui
  // dit ce qu'elle fait, non son code.
  const CHOIX_ARGUMENT = {
    langue: [
      ["", "Choisir une langue"],
      ["fr", "Francais"], ["en", "English"], ["de", "Deutsch"],
      ["es", "Espanol"], ["it", "Italiano"], ["pt", "Portugues"],
      ["nl", "Nederlands"],
    ],
  };

  // Trois onglets sur cinq ne servent qu'a qui sait ce qu'il cherche.
  // Menage, Diagnostic et Reparation n'ont aucun sens pour quelqu'un
  // qui vient d'installer.
  const ONGLETS_SIMPLES = ["g_demarrage", "g_courant"];

  // Les reglages qu'on change vraiment. Aller dans l'ecran de Stash
  // pour modifier une valeur qu'on vient de voir mentionnee est une
  // gymnastique ; en offrir quarante reproduirait l'ecran qu'on fuit.
  // « Que faire des valeurs trouvees » accepte trois valeurs et se
  // presentait en champ texte : il fallait savoir quoi taper, une
  // faute de frappe passait inapercue — la valeur etait simplement
  // ignoree, sans message — et rien ne disait ce que chaque valeur
  // change.
  //
  // Un choix ferme se presente en choix ferme, et chaque valeur porte
  // un libelle qui dit CE QUI VA SE PASSER : « seuil » ne dit rien,
  // « Appliquer au-dela d'une note » si.
  const CHOIX = {
    applyMode: [
      ["manual", "Proposer, ne rien écrire"],
      ["seuil", "Écrire au-delà d'une note de confiance"],
      ["auto", "Écrire dès qu'une source répond"],
    ],
    language: [
      ["", "Comme Stash"],
      ["fr", "Français"], ["en", "English"], ["de", "Deutsch"],
      ["es", "Español"], ["it", "Italiano"], ["pt", "Português"],
      ["nl", "Nederlands"],
    ],
    tagProfile: [
      ["", "Aucun profil"],
      ["gay", "Gay"], ["hetero", "Hétéro"], ["lesbien", "Lesbien"],
      ["bi", "Bi"], ["pan", "Pan"], ["trans", "Trans"],
      ["mixte", "Mixte"],
    ],
  };

  // Le TYPE dit la forme : un nombre ne se saisit pas en texte, sinon
  // « vingt-cinq » est accepte puis silencieusement ignore.
  const REGLAGES_RAPIDES = [
    ["applyMode", "Que faire des valeurs trouvées", "choix"],
    ["batchSize", "Fiches par passage", "nombre"],
    ["createMissing", "Créer les fiches manquantes", "oui-non"],
    ["dryRun", "Simulation : n'écrire nulle part", "oui-non"],
  ];

  const GROUPES = [
    // Une même tâche ne figure qu'UNE fois : la voir sous deux
    // libellés différents laissait croire à deux actions distinctes.
    // L'ordre d'exécution conseillé est porté par la numérotation.
    ["g_demarrage", [
      ["enrich_scenes",
       "1. Scènes", "Identifie les fichiers et complète studio, titre, distribution. À lancer en premier : les scènes créent ce qui manque.", true, false],
      ["enrich_performers",
       "2. Interprètes", "Complète les champs vides depuis les sources.", true, false],
      ["enrich_studios", "3. Studios", "Complète réseau parent, site et présentation.", true, false],
      ["suggerer_tags_exclus",
       "4. Proposer des tags à écarter", "Signale les tags que les sources posent souvent et que vous n'employez jamais. N'écrit rien.", false, false],
    ]],
    ["g_courant", [
      ["apply_covers", "Appliquer les covers officielles", "Remplace les jaquettes par celles des stash-boxes, quand elles en fournissent.",
       false, false],
      ["detect_groupes", "Reconstituer les films en plusieurs parties", "Regroupe en films les scènes qui partagent un titre et un studio, et se suivent par leur numéro de partie.",
       false, false],
      ["regenerate_biohot", "Régénérer les présentations manquantes", "Rédige la présentation « hot » des fiches qui n'en ont pas. Coûte un appel de modèle par fiche.",
       false, false],
      ["apply_accepted",
       "Appliquer les propositions d'interprètes", "Écrit les valeurs proposées sur toutes les fiches marquées. Sur une seule fiche, le bouton de la fiche est plus direct.", false, true],
      ["apply_recommended",
       "Appliquer les recommandations", "Écrase les valeurs existantes par celles que les sources établissent. L'ancienne valeur passe dans l'historique.", false, true],
    ]],
    ["g_menage", [
      ["detect_duplicates", "Détecter les doublons d'interprètes", "Marque les fiches qui semblent désigner la même personne. Ne fusionne rien : la fusion est une action distincte.",
       false, false],
      ["detect_duplicates_studios", "Détecter les doublons de studios", "Marque les studios qui semblent être le même. Ne fusionne rien.",
       false, false],
      ["dedoublonnage_complet", "Fusionner les doublons certains", "Ne fusionne que les paires dont la note dépasse le seuil de fusion. Les autres attendent votre arbitrage.",
       false, true],
      ["purger_tags_exclus", "Retirer les tags exclus", "Retire des fiches les tags que vous avez listés comme indésirables.", false, true],
      ["retirer_pied_bio", "Retirer le pied de biographie", "Retire la mention de fiabilité ajoutée en bas des biographies générées.",
       false, true],
      ["ranger_champs_herites", "Ranger les champs d'un import", "Déplace vers les champs standard de Stash ce qu'un import avait laissé dans des champs libres.",
       false, true],
      ["arbitrer_conflits",
       "Aligner les conflits", "Écrase les valeurs qui contredisent les sources, au-delà du seuil de confiance. L'ancienne valeur passe dans l'historique.", false, true],
      ["clear_proposals",
       "Retirer les tags de proposition", "Retire les tags posés par le plugin pour signaler ce qui attendait une décision. Les valeurs restent.", false, true],
      ["merge_marked",
       "Fusionner les interprètes marqués", "Reporte scènes et alias sur la fiche conservée, puis supprime l'autre. Sans retour.", false, true],
      ["merge_marked_studios",
       "Fusionner les studios marqués", "Reporte les scènes sur le studio conservé, puis supprime l'autre. Sans retour.", false, true],
      ["retirer_non_confirme",
       "Retirer les valeurs sans source", "Efface ce qu'aucune source ne confirme, typiquement venu d'un import.", false, true],
      ["retirer_champ_herite",
       "Retirer un champ d'import", "Argument champ=nom. Les champs du plugin sont refusés.", false, true],
      ["normaliser_roles", "Normaliser l'écriture des rôles", "Uniformise la casse et l'orthographe des rôles déjà renseignés.",
       false, true],
      ["marquer_roles_importes",
       "Marquer les rôles venus d'un import", "Signale comme « suggérés » les rôles qu'aucune source ne confirme, pour les distinguer des rôles établis.", false, true],
    ]],
    ["g_diagnostic", [
      ["prompt_defaut",
       "Relever le prompt par défaut", "Écrit dans le journal et dans l'état le prompt intégré au plugin, pour servir de point de départ. N'écrit rien sur les fiches.",
       false, false],
      ["rapport_profil",
       "Profil de collection", "Ce que la composition de vos scènes dit de votre collection, et le profil que le rédacteur emploiera. N'écrit rien.",
       false, false],
      ["etat_agent", "État de l'agent", "Ce que le plugin sait de votre installation : sources joignables, modèle configuré, dernier passage.", false, false],
      ["rapport_run", "Dernier passage", "Ce que le dernier enrichissement a écrit, et ce qui reste incomplet.", false, false],
      ["rapport_tags", "Rapport des tags", "Quels tags sont posés, par quelles sources, et lesquels n'apparaissent jamais. N'écrit rien.", false, false],
      ["controler_heritage", "Contrôler les champs d'un import", "Liste les champs libres présents sur vos fiches et ce qu'ils contiennent. N'écrit rien.",
       false, false],
      ["sante_sources", "Vérifier l'état des sources", "Interroge chaque source sur une fiche connue et signale celles qui ne répondent plus.", false, false],
      ["lire_chemins",
       "Lire les chemins de fichiers", "Un dossier nomme souvent le studio, un nom de fichier la distribution. Gratuit et instantané.",
       false, false],
      ["appliquer_generiques",
       "Appliquer les noms lus", "Relie les interprètes et studios reconnus au catalogue. Ne crée jamais de fiche.",
       false, true],
      ["lire_generiques",
       "Lire les génériques", "Découpe le début et la fin des planches pour y lire les noms. Demande Pillow.",
       false, false],
      ["appliquer_vision",
       "Appliquer les studios lus", "Pose les studios reconnus au catalogue. Les lectures approximatives attendent une confirmation.",
       false, true],
      ["lire_vignettes",
       "Lire les filigranes", "Envoie les vignettes à un modèle pour y lire le nom du studio. Coûte des appels payants.",
       false, false],
      ["proposer_scrapers",
       "Proposer des scrapers", "Compare vos studios au catalogue et signale ceux qui auraient un scraper. Argument installer=1 pour les poser.",
       false, false],
      ["inspecter_collecte",
       "Inspecter une collecte", "Argument nom ou performer_id. Montre ce que chaque source répond, sans rien écrire.",
       false, false],
      ["position_tags", "Rapport des rôles", "Répartition des rôles dans votre collection, et ce sur quoi chacun s'appuie. N'écrit rien.", false, false],
    ]],
    ["g_reparation", [
      ["exporter_reglages",
       "Exporter les réglages", "Écrit vos réglages dans le journal, sous une forme à copier et garder hors de Stash. Aucune clé d'API n'est exportée.",
       false, false],
      ["importer_reglages",
       "Importer des réglages", "Rétablit des réglages depuis un export. Complète plutôt que de remplacer, et dit ce qu'il a changé.",
       true, false],
      ["vider_cache",
       "Oublier les réponses mémorisées", "Force la réinterrogation des sources au prochain passage.", false, true],
      ["restaurer_reglages", "Restaurer les réglages", "Remet les réglages du plugin dans l'état de la dernière sauvegarde automatique.", false, false],
      ["reprendre_ia", "Reprendre les générations IA", "Relance les rédactions interrompues par une panne ou un plafond d'appels atteint.", false, false],
      ["migrer_langue", "Basculer la langue du plugin", "Change la langue de l'interface et des textes générés. Vide = la langue de Stash.", false, false],
      ["restore_marked", "Restaurer les fiches marquées", "Rend aux fiches portant le tag de restauration les valeurs qu'elles avaient avant le dernier passage.", false, true],
    ]],
  ];

  // Afficher la liste brute des états produisait un mur de « READY »
  // illisible dès qu'une poignée de tâches s'accumulaient. Ce qui
  // importe tient en trois informations : ce qui tourne, combien
  // attendent, et de quoi il s'agit.
  function FileAttente() {
    const [file, setFile] = React.useState(null);
    const [arret, setArret] = React.useState(false);
    React.useEffect(() => {
      let vivant = true;
      const lire = () => GQL(
        `{ jobQueue { id status description progress } }`)
        .then((d) => { if (vivant) setFile(d.jobQueue || []); })
        .catch(() => {});
      lire();
      const t = setInterval(lire, 3000);
      return () => { vivant = false; clearInterval(t); };
    }, []);
    if (file === null) return null;

    const enCours = file.find((j) => j.status === "RUNNING");
    const attente = file.filter((j) => j.status !== "RUNNING").length;
    const nom = (j) => (j.description || "")
      .replace(/^Running plugin task:\s*/i, "").trim() || "—";

    const toutArreter = async () => {
      if (!confirm(tr("arreter_tout_q"))) return;
      setArret(true);
      try { await GQL(`mutation { stopAllJobs }`); }
      catch (err) { console.error("Gaizer", err); }
      setTimeout(() => setArret(false), 2000);
    };

    return e("div", { className: "card bg-transparent border mb-4" },
      e("div", { className: "card-body py-2 px-3" },
        e("div", { className: "d-flex align-items-center flex-wrap" },
          e("strong", { className: "mr-3" }, tr("file")),
          enCours
            ? e("span", { className: "mr-3" },
                e("span", { className: "badge badge-primary mr-2" },
                  tr("en_cours")),
                nom(enCours))
            : e("span", { className: "text-muted mr-3" },
                tr("file_vide")),
          attente
            ? e("span", { className: "badge badge-secondary mr-3" },
                attente + " " + tr("en_attente_n"))
            : null,
          file.length
            ? e("button", {
                className: "btn btn-sm btn-outline-danger ml-auto",
                disabled: arret, onClick: toutArreter,
              }, tr("arreter_tout"))
            : null),
        // « progress » est alimenté par log.progress(), que les
        // tâches de masse appellent à chaque entité. Sans l'afficher,
        // la file reste muette pendant plusieurs minutes et rien ne
        // distingue une tâche qui avance d'une tâche figée.
        enCours && typeof enCours.progress === "number"
          ? e("div", { className: "progress mt-2",
                       style: { height: ".4rem" } },
              e("div", {
                className: "progress-bar",
                role: "progressbar",
                style: {
                  width: Math.max(2, Math.round(
                    enCours.progress * 100)) + "%" },
                "aria-valuenow": Math.round(enCours.progress * 100),
                "aria-valuemin": 0, "aria-valuemax": 100,
              }))
          : null,
        enCours && enCours.progress > 0
          ? e("div", { className: "text-muted small mt-1" },
              Math.round(enCours.progress * 100) + " %")
          : null,
        e("div", { className: "text-muted small mt-1" },
          tr("une_seule"))));
  }

  // Aller dans l'ecran des reglages de Stash pour modifier une
  // valeur qu'on vient de voir mentionnee est une gymnastique. Les
  // quatre qui se changent vraiment sont ici — en offrir quarante
  // reproduirait l'ecran qu'on fuit.
  function ReglagesRapides() {
    const [valeurs, setValeurs] = React.useState(null);
    const [etat, setEtat] = React.useState("");

    React.useEffect(() => {
      GQL(`{ configuration { plugins } }`)
        .then((d) => setValeurs(
          (d.configuration.plugins || {})["gaizer"] || {}))
        .catch(() => setValeurs({}));
    }, []);

    const ecrire = async (cle, valeur) => {
      setEtat("…");
      try {
        // configurePlugin REMPLACE la table entiere : relire avant
        // d'ecrire, sans quoi tous les autres reglages disparaissent.
        const d = await GQL(`{ configuration { plugins } }`);
        const table = (d.configuration.plugins || {})["gaizer"] || {};
        table[cle] = valeur;
        await GQL(`mutation($i: Map!) { configurePlugin(
            plugin_id: "gaizer", input: $i) }`, { i: table });
        setValeurs(Object.assign({}, table));
        setEtat(tr("enregistre"));
      } catch (err) {
        setEtat(String(err).slice(0, 60));
      }
    };

    if (!valeurs) return null;
    return e("div", { className: "mb-3" },
      e("div", { className: "d-flex flex-wrap align-items-center",
                 style: { gap: "1.2rem" } },
        REGLAGES_RAPIDES.map(([cle, libelle, forme]) => {
          const brut = valeurs[cle];
          let champ;
          if (forme === "oui-non") {
            champ = e("input", {
              type: "checkbox", checked: !!brut,
              onChange: (ev) => ecrire(cle, ev.target.checked) });
          } else if (forme === "choix") {
            // Trois valeurs connues : les lister evite de les taper
            // de memoire, et dit ce que chacune change.
            champ = e("select", {
              className: "custom-select custom-select-sm",
              style: { maxWidth: "17rem" },
              value: brut === undefined ? "" : String(brut),
              onChange: (ev) => ecrire(cle, ev.target.value),
            }, (CHOIX[cle] || []).map(([v, lib]) =>
              e("option", { key: v, value: v }, lib)));
          } else {
            champ = e("input", {
              type: forme === "nombre" ? "number" : "text",
              min: forme === "nombre" ? 1 : undefined,
              className: "form-control form-control-sm",
              style: { maxWidth: "6.5rem" },
              defaultValue: brut === undefined ? "" : String(brut),
              onBlur: (ev) => ecrire(cle, ev.target.value) });
          }
          // On lit ce qu'on demande, PUIS on répond : le libellé
          // placé après le champ donnait « [Écrire au-delà d'une
          // note] Que faire des valeurs trouvées » — la réponse avant
          // la question, ce qui oblige à revenir en arrière.
          //
          // La case à cocher fait exception : « [x] Simulation » se
          // lit dans cet ordre, parce que la case EST la réponse et
          // que le texte la qualifie.
          const avant = forme !== "oui-non";
          return e("label", {
            key: cle,
            className: "mb-0 d-flex align-items-center text-muted small",
            style: { gap: ".45rem" },
          }, avant ? libelle : champ, avant ? champ : libelle);
        }),
        etat ? e("span", { className: "text-muted small" }, etat)
             : null));
  }

  // La forme d'un champ doit dire ce qu'il attend. Un champ vide
  // n'apprend rien ; une invite grise donne la valeur par defaut, la
  // plage, ou un exemple — selon ce qui aide le plus.
  function _champArgument(arg, valeur, poser) {
    const [, forme, invite, mini, maxi] = arg;

    if (forme === "oui-non") {
      // Ce qui valait « 1 » : la case dit la meme chose sans qu'on
      // ait a deviner quelle valeur compte pour vrai.
      return e("label", {
        className: "mb-0 d-flex align-items-center text-muted small "
          + "flex-shrink-0",
        style: { gap: ".4rem" },
      },
        e("input", {
          type: "checkbox",
          checked: valeur === "1",
          onChange: (ev) => poser(ev.target.checked ? "1" : ""),
        }),
        invite);
    }

    if (forme === "choix") {
      const valeurs = CHOIX_ARGUMENT[arg[0]] || [];
      return e("select", {
        className: "custom-select custom-select-sm flex-shrink-0",
        style: { maxWidth: "12rem" },
        value: valeur,
        onChange: (ev) => poser(ev.target.value),
      }, valeurs.map(([v, libelle]) =>
        e("option", { key: v, value: v }, libelle)));
    }

    if (forme === "nombre") {
      // L'invite porte le DEFAUT, la plage borne la saisie : les
      // deux ensemble disent ce qu'on attend sans phrase.
      return e("input", {
        type: "number",
        step: "0.1",
        min: mini,
        max: maxi,
        className: "form-control form-control-sm flex-shrink-0",
        style: { maxWidth: "7rem" },
        placeholder: invite,
        title: (mini !== undefined && maxi !== undefined)
          ? `entre ${mini} et ${maxi} · défaut ${invite}` : invite,
        value: valeur,
        onChange: (ev) => poser(ev.target.value),
      });
    }

    return e("input", {
      className: "form-control form-control-sm flex-shrink-0",
      style: { maxWidth: "15rem" },
      placeholder: invite,
      title: invite,
      value: valeur,
      onChange: (ev) => poser(ev.target.value),
    });
  }

  function Tache(props) {
    const [etat, setEtat] = React.useState("");
    // Le champ n'apparait que sur les taches qui en attendent un :
    // un champ vide sur chaque ligne serait du bruit.
    const arg = ARGUMENTS[props.mode];
    const [valeurArg, setValeurArg] = React.useState("");
    const lancer = async (simulation) => {
      if (props.destructif && !simulation) {
        if (!confirm(tr("confirmer").replace("{t}", props.libelle)))
          return;
      }
      setEtat("…");
      try {
        const args = { mode: props.mode };
        if (simulation) args.dryRun = "1";
        if (arg && valeurArg.trim()) args[arg[0]] = valeurArg.trim();
        await GQL(`mutation($a: Map) { runPluginTask(
            plugin_id: "gaizer", task_name: "Gaizer", args_map: $a) }`,
          { a: args });
        setEtat(tr("lance"));
      } catch (err) {
        setEtat("✗");
        console.error("Gaizer", err);
      }
      setTimeout(() => setEtat(""), 4000);
    };
    // Le libellé occupe la place disponible et peut aller à la ligne ;
    // les boutons gardent la leur. Sans « minWidth: 0 », un texte long
    // pousse les boutons hors de la carte au lieu de se replier.
    return e("div", {
      className: "d-flex align-items-center py-2 border-bottom",
      style: { gap: ".5rem" } },
      e("div", { className: "flex-grow-1", style: { minWidth: 0 } },
        e("div", null,
          e("span", { className: props.principal
            ? "font-weight-bold" : "" }, props.libelle),
          props.destructif
            ? e("span", { className: "text-danger small ml-2" },
                tr("destructif"))
            : null),
        // Un libelle seul ne dit pas ce qui va etre ecrit. La
        // description tient dessous, en gris, et n'encombre pas.
        props.aide
          ? e("div", { className: "text-muted small",
                       style: { lineHeight: 1.35 } }, props.aide)
          : null),
      etat
        ? e("span", { className: "text-muted small flex-shrink-0" },
            etat)
        : null,
      arg ? _champArgument(arg, valeurArg, setValeurArg) : null,
      props.destructif
        ? e("button", {
            className: "btn btn-sm btn-outline-secondary flex-shrink-0",
            title: tr("b_simuler"),
            onClick: () => lancer(true) }, tr("simuler"))
        : null,
      e("button", {
        className: "btn btn-sm flex-shrink-0 "
          + (props.principal ? "btn-primary" : "btn-secondary"),
        title: tr("b_lancer"),
        onClick: () => lancer(false),
      }, tr("lancer")));
  }

  // Le prompt et la température vivaient dans Settings → Plugins, où
  // Stash n'offre qu'un champ d'UNE LIGNE : illisible pour un texte de
  // dix lignes, et personne n'y touchait. Ils passent ici, avec la
  // place qu'il faut et de quoi essayer avant d'appliquer.
  function Redaction() {
    const [prompt, setPrompt] = React.useState(null);
    const [temp, setTemp] = React.useState("");
    const [etat, setEtat] = React.useState("");
    // La configuration est deja lue ici : conserver ce qui nomme le
    // modele evite un second appel pour la meme information.
    const [cfg, setCfg] = React.useState({});
    const [promptDefaut, setPromptDefaut] = React.useState("");

    React.useEffect(() => {
      let vivant = true;
      GQL(`{ configuration { plugins } }`).then((d) => {
        if (!vivant) return;
        const c = (d.configuration.plugins || {})["gaizer"] || {};
        setCfg(c);
        setPrompt(String(c.biohotPrompt || ""));
        setTemp(String(c.biohotTemperature || ""));
        // Le défaut vient du SERVEUR : le recopier ici le ferait
        // diverger du prompt réellement employé.
        // Déposé par la tâche « Relever le prompt par défaut » :
        // le lire d'un fichier serait impossible depuis le
        // navigateur, et le recopier ici le ferait diverger.
        if (c.promptDefautReleve)
          setPromptDefaut(String(c.promptDefautReleve));
      }).catch(() => { if (vivant) setPrompt(""); });
      return () => { vivant = false; };
    }, []);

    if (prompt === null) return null;

    const enregistrer = async (nouveauPrompt, nouvelleTemp) => {
      setEtat("…");
      try {
        // configurePlugin REMPLACE la table entière : la relire avant
        // d'écrire, sans quoi tous les autres réglages disparaissent.
        const d = await GQL(`{ configuration { plugins } }`);
        const tout = Object.assign(
          {}, (d.configuration.plugins || {})["gaizer"] || {});
        tout.biohotPrompt = nouveauPrompt;
        tout.biohotTemperature = nouvelleTemp;
        await GQL(`mutation($i: Map!) {
            configurePlugin(plugin_id: "gaizer", input: $i) }`,
          { i: tout });
        setEtat(tr("enregistre"));
      } catch (err) {
        setEtat("✗");
        console.error("Gaizer", err);
      }
      setTimeout(() => setEtat(""), 2500);
    };

    const champ = (libelle, aide, contenu) =>
      e("div", { className: "mb-4" },
        e("label", { className: "text-muted text-uppercase mb-1 d-block",
                     style: { letterSpacing: ".06em",
                              fontSize: ".72rem" } }, libelle),
        contenu,
        e("div", { className: "text-muted small mt-1" }, aide));

    // La regle est celle du serveur : reglage dedie, sinon defaut.
    // Dire LEQUEL des deux s'applique evite de chercher ou changer.
    const dedie = String(cfg.aiBiohot || "").trim();
    const parDefaut = String(cfg.aiDefault || "").trim();
    const modele = dedie || parDefaut;

    return e("div", { className: "container-fluid px-0" },
      e("div", { className: "mb-4" },
        e("label", { className: "text-muted text-uppercase mb-1 d-block",
                     style: { letterSpacing: ".06em",
                              fontSize: ".72rem" } },
          tr("m_titre")),
        modele
          ? e("div", null,
              e("code", null, modele),
              e("span", { className: "text-muted small ml-2" },
                dedie ? tr("m_source_dedie") : tr("m_source_defaut")))
          // Sans modele, rien ne sera ecrit : le taire laisserait
          // croire a une panne.
          : e("div", { className: "text-warning small" },
              tr("m_aucun"))),
      // Ce qui gouverne le resultat sans figurer dans le prompt :
      // l'utilisateur constatait un texte court sans savoir
      // pourquoi, et pouvait allonger son prompt en pure perte.
      e("div", { className: "mb-4" },
        e("label", { className: "text-muted text-uppercase mb-1 d-block",
                     style: { letterSpacing: ".06em",
                              fontSize: ".72rem" } },
          tr("mod_titre")),
        e("div", { className: "text-muted small",
                   style: { maxWidth: "44rem" } }, tr("mod_texte"))),
      e("div", { className: "mb-4" },
        e("label", { className: "text-muted text-uppercase mb-1 d-block",
                     style: { letterSpacing: ".06em",
                              fontSize: ".72rem" } },
          tr("lim_titre")),
        e("div", { className: "text-muted small",
                   style: { maxWidth: "44rem" } }, tr("lim_texte")),
        e("div", { className: "text-muted small mt-2",
                   style: { maxWidth: "44rem" } }, tr("lim_noms"))),
      champ(tr("prompt"), tr("prompt_aide"),
        e(React.Fragment, null,
        e("textarea", {
          className: "form-control input-control",
          rows: 8, value: prompt,
          style: { fontFamily: "inherit", lineHeight: 1.5 },
          onChange: (ev) => setPrompt(ev.target.value),
          placeholder: promptDefaut || "",
        }),
        // Le prompt par défaut sert de MODÈLE : la zone vide
        // n'apprenait ni ce que le plugin demande au modèle, ni
        // comment formuler autre chose.
        promptDefaut
          ? e("button", {
              type: "button",
              className: "btn btn-sm btn-link px-0 mt-1",
              onClick: () => { setPrompt(promptDefaut);
                               enregistrer(promptDefaut, temp); },
            }, tr("partir_du_defaut"))
          : null)),
      champ(tr("temperature"), tr("temperature_aide"),
        e("input", {
          type: "number", min: 0, max: 1.5, step: 0.1,
          className: "form-control input-control",
          style: { maxWidth: "8rem" },
          value: temp, placeholder: "0.7",
          onChange: (ev) => setTemp(ev.target.value),
        })),
      e("div", { className: "d-flex align-items-center",
                 style: { gap: ".5rem" } },
        e("button", {
          className: "btn btn-sm btn-primary",
          onClick: () => enregistrer(prompt, temp),
        }, tr("enregistrer")),
        e("button", {
          className: "btn btn-sm btn-secondary",
          onClick: () => { setPrompt(""); setTemp("");
                           enregistrer("", ""); },
        }, tr("defaut")),
        etat
          ? e("span", { className: "text-muted small ml-2" }, etat)
          : null),
      e("hr", { className: "my-4" }),
      e("div", { className: "text-muted small mb-2" },
        tr("essai_aide")),
      e("div", { className: "card bg-transparent border" },
        e("div", { className: "card-body py-1 px-3" },
          e(Tache, { mode: "regenerate_biohot",
                     libelle: tr("essai"),
                     principal: false, destructif: false }))));
  }

  // Chaque onglet avait sa propre mise en page : l'un une carte,
  // l'autre des colonnes, un troisieme des champs bruts. Passer de
  // l'un a l'autre demandait de se reorienter a chaque fois.
  //
  // Une seule enveloppe : le contenu change, le cadre non. C'est ce
  // qui fait qu'on cesse de regarder l'interface pour regarder ce
  // qu'elle contient.
  function Onglet(props) {
    return e("div", null,
      props.description
        ? e("p", { className: "text-muted mb-3",
                   style: { maxWidth: "44rem" } }, props.description)
        : null,
      e("div", { className: "card bg-transparent border" },
        e("div", { className: "card-body py-1 px-3" },
          props.children)));
  }

  function PageGaizer(props) {
    // Le titre figure déjà dans l'en-tête du panneau : le répéter
    // n'apporte rien et pousse le contenu vers le bas.
    // Quarante tâches sur cinq groupes tenaient sur un seul écran :
    // il fallait faire défiler pour atteindre le cinquième, et les
    // réglages de rédaction n'auraient rien eu à y faire. Deux onglets
    // séparent ce qu'on LANCE de ce qu'on RÈGLE.
    // Quarante-neuf taches sur cinq groupes tenaient sur un seul
    // ecran defilant : celui qui decouvre ne savait pas par ou
    // commencer, celui qui connaissait cherchait. Un onglet par
    // INTENTION — on ne voit que ce qu'on est venu chercher.
    //
    // Le premier onglet ne montre qu'un bouton : quelqu'un qui
    // installe le plugin veut que sa mediatheque soit completee, pas
    // choisir entre quarante-neuf actions.
    const [onglet, setOnglet] = React.useState("simple");

    // Quarante-cinq reglages, quarante-deux taches, sept onglets : la
    // QUANTITE elle-meme est ce qui decourage. Grouper et decrire a
    // aide, mais n'a rien retire de l'ecran.
    //
    // Un seul interrupteur commande le tout — un qui commanderait le
    // panneau sans commander les reglages laisserait la moitie du
    // bruit. Simple par defaut : c'est ce que voit qui installe.
    const [avance, setAvance] = React.useState(false);

    // Rebasculer en avance a chaque visite serait une punition pour
    // qui a choisi une fois.
    React.useEffect(() => {
      try {
        if (window.localStorage.getItem("gaizerAvance") === "1")
          setAvance(true);
      } catch (err) { /* stockage indisponible : simple */ }
    }, []);

    const basculerAvance = () => {
      const neuf = !avance;
      setAvance(neuf);
      try {
        window.localStorage.setItem("gaizerAvance", neuf ? "1" : "0");
      } catch (err) { /* sans consequence */ }
      // Basculer en simple alors qu'on est dans Diagnostic
      // laisserait un ecran vide.
      if (!neuf && !["simple", "redaction"].concat(ONGLETS_SIMPLES)
          .includes(onglet)) setOnglet("simple");
    };
    // La bulle dit a quoi sert l'onglet AVANT de cliquer : c'est
    // ce qui evite de tous les ouvrir pour trouver le bon.
    const lien = (cle, libelle) => {
      const actif = onglet === cle;
      return e("li", {
        key: cle,
        className: "nav-item",
        role: "presentation",
      },
        e("button", {
          type: "button",
          role: "tab",
          "aria-selected": actif ? "true" : "false",
          // Les CLASSES de Bootstrap, que Stash habille deja : c'est
          // au theme de decider des couleurs et des bordures. Un
          // style en ligne l'emporterait sur tous les themes, et le
          // plugin detonnerait la ou il doit se fondre.
          className: "nav-link" + (actif ? " active" : ""),
          // Le retour a la ligne d'un libelle casse la barre : c'est
          // une contrainte de mise en page, non un choix d'apparence.
          style: { whiteSpace: "nowrap" },
          title: tr("d_" + cle) !== "d_" + cle ? tr("d_" + cle) : "",
          onClick: () => setOnglet(cle),
        }, e(Icone, { cle }), libelle));
    };

    return e("div", { className: "container-fluid px-0" },
      props && props.avecTitre
        ? e("h3", { className: "mb-3" }, tr("titre")) : null,
      e("p", { className: "text-muted" }, tr("sous_titre")),
      e("div", { className: "d-flex align-items-end" },
        e("ul", { className: "nav nav-tabs flex-wrap flex-grow-1",
                  role: "tablist" },
          lien("simple", tr("o_simple")),
          lien("redaction", tr("o_redaction")),
          GROUPES.filter(([cle]) => avance
                         || ONGLETS_SIMPLES.includes(cle))
            .map(([cle]) => lien(cle, tr(cle)))),
        e("button", {
          type: "button",
          className: "btn btn-sm btn-link text-muted flex-shrink-0",
          title: tr(avance ? "d_vers_simple" : "d_vers_avance"),
          onClick: basculerAvance,
        }, tr(avance ? "vers_simple" : "vers_avance"))),


      onglet === "redaction" ? e(Redaction) : null,

      onglet !== "simple" ? null : e(React.Fragment, null,
        e(FileAttente),
        e(Onglet, { description: tr("s_explication") },
          e(Tache, { mode: "enrichir_tout",
                     libelle: tr("enrichir_tout"),
                     aide: tr("a_enrichir_tout"),
                     principal: true, destructif: false }),
          // Lancer sans pouvoir constater ni defaire laisse dans
          // l'inconnu : le parcours complet tient sur cet onglet.
          e(Tache, { mode: "rapport_run",
                     libelle: tr("rapport_run"),
                     aide: tr("a_rapport_run"),
                     principal: false, destructif: false }),
          e(Tache, { mode: "undo_last",
                     libelle: tr("undo_last"),
                     aide: tr("a_undo_last"),
                     principal: false, destructif: false })),
        e("p", { className: "text-muted small mt-3 mb-2" },
          tr("s_detail")),
        e(ReglagesRapides)),

      GROUPES.map(([cle, taches]) =>
        onglet !== cle ? null : e(React.Fragment, { key: cle },
          e(FileAttente),
          e(Onglet, { description: tr("d_" + cle) },
            taches.map(([mode, libelle, aide, principal,
                           destructif], i) =>
              e(Tache, { key: mode + i, mode, libelle, aide,
                         principal, destructif }))))));
  }

  // Une route enregistrée par un plugin n'est pas garantie d'exister
  // pour le routeur : le JavaScript des plugins est chargé APRÈS que
  // Stash a monté ses routes, et la page se solde alors par un 404.
  // Plutôt que de lutter contre l'ordre de chargement, la page devient
  // un panneau qui s'ouvre sur place — aucune navigation, donc aucune
  // route à faire reconnaître.
  //
  // La route reste enregistrée quand c'est possible : elle rend
  // l'adresse /plugin/gaizer utilisable pour qui la met en favori.
  if (API.register && API.register.route) {
    try { API.register.route("/plugin/gaizer", PageGaizer); }
    catch (err) { /* sans conséquence : le panneau suffit */ }
  }

  function Panneau(props) {
    // Fermeture par la touche d'échappement : un panneau qu'on ne
    // peut fermer qu'en visant une croix est pénible.
    React.useEffect(() => {
      const touche = (ev) => { if (ev.key === "Escape") props.fermer(); };
      window.addEventListener("keydown", touche);
      return () => window.removeEventListener("keydown", touche);
    }, [props]);

    return e("div", {
      className: "modal show d-block",
      style: { background: "rgba(0,0,0,.6)", zIndex: 1080,
               overflowY: "auto" },
      onClick: (ev) => {
        if (ev.target === ev.currentTarget) props.fermer();
      },
    }, e("div", { className: "modal-dialog modal-xl",
                  role: "document" },
        e("div", { className: "modal-content" },
          e("div", { className: "modal-header py-2" },
            e("h5", { className: "modal-title" }, tr("titre")),
            e("button", { type: "button", className: "close",
                          onClick: props.fermer,
                          "aria-label": "Fermer" },
              e("span", { "aria-hidden": "true" }, "×"))),
          e("div", { className: "modal-body" }, e(PageGaizer)))));
  }

  // Une entrée dans la barre de navigation : sans elle, la page ne
  // serait accessible qu'en tapant son adresse.
  //
  // Le lien DOIT passer par le routeur de l'application. Un « href »
  // ordinaire déclenche une navigation complète du navigateur vers
  // /plugin/gaizer — une adresse que le serveur Go ne connaît pas,
  // puisque la page n'existe que côté client : il répond 404, et la
  // page enregistrée n'a jamais l'occasion de se rendre.
  const Router = (API.libraries || {}).ReactRouterDOM || {};

  function EntreeNav() {
    const [ouvert, setOuvert] = React.useState(false);
    return e(React.Fragment, null,
      e("button", {
        type: "button",
        className: "nav-utility btn btn-link minimal",
        title: tr("sous_titre"),
        onClick: () => setOuvert(true),
      }, e("span", { style: { fontWeight: 700, fontSize: ".78rem",
                              letterSpacing: ".04em" } }, "GZ")),
      ouvert ? e(Panneau, { fermer: () => setOuvert(false) }) : null);
  }

  API.patch.before("MainNavBar.UtilityItems", function () {
    const args = Array.prototype.slice.call(arguments);
    const props = args[0] || {};
    const enfants = React.Children.toArray(props.children || []);
    const neufs = args.slice();
    neufs[0] = Object.assign({}, props, {
      children: [e(EntreeNav, { key: "gaizer" })].concat(enfants) });
    return neufs;
  });
})();
