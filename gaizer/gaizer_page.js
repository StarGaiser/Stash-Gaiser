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
    g_demarrage: { en: "Getting started", fr: "Première mise en route",
                   de: "Erste Schritte", es: "Primera puesta en marcha",
                   it: "Prima messa in opera",
                   pt: "Primeira colocação em marcha",
                   nl: "Eerste opstart" },
    g_courant: { en: "Routine", fr: "Entretien courant",
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
    o_taches: { en: "Tasks", fr: "Tâches", de: "Aufgaben",
                es: "Tareas", it: "Attività", pt: "Tarefas",
                nl: "Taken" },
    o_redaction: { en: "Writing", fr: "Rédaction", de: "Textgestaltung",
                   es: "Redacción", it: "Redazione", pt: "Redação",
                   nl: "Tekstopmaak" },
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
    en_cours: { en: "running", fr: "en cours", de: "läuft",
                es: "en curso", it: "in corso", pt: "em curso",
                nl: "bezig" },
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
  const GROUPES = [
    // Une même tâche ne figure qu'UNE fois : la voir sous deux
    // libellés différents laissait croire à deux actions distinctes.
    // L'ordre d'exécution conseillé est porté par la numérotation.
    ["g_demarrage", [
      ["enrich_scenes",
       "1. Scènes : identifier et compléter", true, false],
      ["enrich_performers",
       "2. Interprètes : compléter les champs vides", true, false],
      ["enrich_studios", "3. Studios : compléter", true, false],
      ["suggerer_tags_exclus",
       "4. Proposer des tags à écarter", false, false],
    ]],
    ["g_courant", [
      ["apply_covers", "Appliquer les covers officielles",
       false, false],
      ["detect_groupes", "Reconstituer les films en plusieurs parties",
       false, false],
      ["regenerate_biohot", "Régénérer les présentations manquantes",
       false, false],
    ]],
    ["g_menage", [
      ["detect_duplicates", "Détecter les doublons d'interprètes",
       false, false],
      ["detect_duplicates_studios", "Détecter les doublons de studios",
       false, false],
      ["dedoublonnage_complet", "Fusionner les doublons certains",
       false, true],
      ["purger_tags_exclus", "Retirer les tags exclus", false, true],
      ["retirer_pied_bio", "Retirer le pied de biographie",
       false, true],
      ["ranger_champs_herites", "Ranger les champs d'un import",
       false, true],
      ["arbitrer_conflits",
       "Aligner les conflits sur les sources (écrase)", false, true],
    ]],
    ["g_diagnostic", [
      ["etat_agent", "État de l'agent", false, false],
      ["rapport_run", "Rapport du dernier passage", false, false],
      ["rapport_tags", "Rapport des tags", false, false],
      ["controler_heritage", "Contrôler les champs d'un import",
       false, false],
      ["sante_sources", "Vérifier l'état des sources", false, false],
      ["lire_vignettes",
       "Lire les filigranes des vignettes (envoie des images)",
       false, false],
      ["proposer_scrapers",
       "Proposer les scrapers manquants (installer=1 pour poser)",
       false, false],
      ["inspecter_collecte",
       "Inspecter la collecte d'une fiche (nom ou performer_id)",
       false, false],
    ]],
    ["g_reparation", [
      ["restaurer_reglages", "Restaurer les réglages", false, false],
      ["reprendre_ia", "Reprendre les générations IA", false, false],
      ["migrer_langue", "Basculer la langue du plugin", false, false],
      ["restore_marked", "Restaurer les fiches marquées", false, true],
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

  function Tache(props) {
    const [etat, setEtat] = React.useState("");
    const lancer = async (simulation) => {
      if (props.destructif && !simulation) {
        if (!confirm(tr("confirmer").replace("{t}", props.libelle)))
          return;
      }
      setEtat("…");
      try {
        const args = { mode: props.mode };
        if (simulation) args.dryRun = "1";
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
        e("span", { className: props.principal
          ? "font-weight-bold" : "" }, props.libelle),
        props.destructif
          ? e("span", { className: "text-danger small ml-2" },
              tr("destructif"))
          : null),
      etat
        ? e("span", { className: "text-muted small flex-shrink-0" },
            etat)
        : null,
      props.destructif
        ? e("button", {
            className: "btn btn-sm btn-outline-secondary flex-shrink-0",
            onClick: () => lancer(true) }, tr("simuler"))
        : null,
      e("button", {
        className: "btn btn-sm flex-shrink-0 "
          + (props.principal ? "btn-primary" : "btn-secondary"),
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

    React.useEffect(() => {
      let vivant = true;
      GQL(`{ configuration { plugins } }`).then((d) => {
        if (!vivant) return;
        const c = (d.configuration.plugins || {})["gaizer"] || {};
        setPrompt(String(c.biohotPrompt || ""));
        setTemp(String(c.biohotTemperature || ""));
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

    return e("div", { className: "container-fluid px-0" },
      champ(tr("prompt"), tr("prompt_aide"),
        e("textarea", {
          className: "form-control input-control",
          rows: 8, value: prompt,
          style: { fontFamily: "inherit", lineHeight: 1.5 },
          onChange: (ev) => setPrompt(ev.target.value),
        })),
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

  function PageGaizer(props) {
    // Le titre figure déjà dans l'en-tête du panneau : le répéter
    // n'apporte rien et pousse le contenu vers le bas.
    // Quarante tâches sur cinq groupes tenaient sur un seul écran :
    // il fallait faire défiler pour atteindre le cinquième, et les
    // réglages de rédaction n'auraient rien eu à y faire. Deux onglets
    // séparent ce qu'on LANCE de ce qu'on RÈGLE.
    const [onglet, setOnglet] = React.useState("taches");
    const lien = (cle, libelle) =>
      e("li", { key: cle, className: "nav-item" },
        e("button", {
          type: "button",
          className: "nav-link btn btn-link"
            + (onglet === cle ? " active" : ""),
          onClick: () => setOnglet(cle),
        }, libelle));

    return e("div", { className: "container-fluid px-0" },
      props && props.avecTitre
        ? e("h3", { className: "mb-3" }, tr("titre")) : null,
      e("p", { className: "text-muted" }, tr("sous_titre")),
      e("ul", { className: "nav nav-tabs mb-3" },
        lien("taches", tr("o_taches")),
        lien("redaction", tr("o_redaction"))),
      onglet === "redaction" ? e(Redaction) : null,
      onglet !== "taches" ? null : e(React.Fragment, null,
      e(FileAttente),
      e("div", { className: "row" },
        GROUPES.map(([cle, taches]) =>
          e("div", { key: cle, className: "col-12 col-lg-6 mb-4" },
            e("h6", { className: "text-muted text-uppercase mb-2",
                      style: { letterSpacing: ".06em",
                               fontSize: ".72rem" } }, tr(cle)),
            e("div", { className: "card bg-transparent border h-100" },
              e("div", { className: "card-body py-1 px-3" },
                taches.map(([mode, libelle, principal, destructif], i) =>
                  e(Tache, { key: mode + i, mode, libelle, principal,
                             destructif })))))))));
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
