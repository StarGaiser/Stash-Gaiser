// Gaizer — panneau d'informations et actions dans l'interface de Stash.
//
// L'injection se fait par PluginApi.patch, le point d'extension React
// officiel : le panneau devient un composant enfant du composant Stash
// qu'il complète, au lieu d'être greffé sur un sélecteur CSS deviné.
// Il survit donc aux re-rendus et aux changements de structure entre
// versions.
//
// Vérifié sur Stash 0.31.1 : « PerformerDetailsPanel » et
// « StudioDetailsPanel » sont patchables ; la page scène ne l'est pas
// encore (seuls SceneCard et SceneFileInfoPanel le sont), d'où un
// repli DOM pour ce seul cas, déclenché par l'événement de navigation
// « stash:location » plutôt que par une observation permanente du
// document.
//
// Le style s'appuie sur les classes Bootstrap de Stash (card, text-
// muted, badge, btn) : un thème clair ou personnalisé reste lisible,
// ce qu'une couleur écrite en dur interdirait.
(function () {
  "use strict";

  const API = window.PluginApi;
  if (!API || !API.React) {
    console.warn("Gaizer : PluginApi indisponible, panneau désactivé.");
    return;
  }
  const React = API.React;
  const e = React.createElement;

  const PREFIX_DEFAUT = "Gaizer";
  const LANG_DEFAUT = "en";

  // ── Traductions (miroir de i18n.py) ──────────────────────────────
  const TAGS = {
    proposal: { en: "proposal", fr: "proposal" },
    accept: { en: "accept", fr: "accept" },
    created: { en: "created", fr: "créé", de: "erstellt", es: "creado",
               it: "creato", pt: "criado", nl: "aangemaakt" },
    verify: { en: "verify", fr: "verifier", de: "pruefen",
              es: "verificar", it: "verificare", pt: "verificar",
              nl: "controleren" },
    duplicate: { en: "duplicate?", fr: "doublon?", de: "duplikat?",
                 es: "duplicado?", it: "duplicato?", pt: "duplicado?",
                 nl: "duplicaat?" },
    not_duplicate: { en: "not-duplicate", fr: "pas-doublon",
                     de: "kein-duplikat", es: "no-duplicado",
                     it: "non-duplicato", pt: "nao-duplicado",
                     nl: "geen-duplicaat" },
    merge: { en: "merge", fr: "fusionner", de: "zusammenfuehren",
             es: "fusionar", it: "unire", pt: "fundir",
             nl: "samenvoegen" },
    restore: { en: "restore", fr: "restaurer", de: "wiederherstellen",
               es: "restaurar", it: "ripristinare", pt: "restaurar",
               nl: "herstellen" },
  };

  const L = {
    enrichir: { en: "Fill in from sources",
                fr: "Compléter depuis les sources",
                de: "Aus Quellen ergänzen",
                es: "Completar desde las fuentes",
                it: "Completa dalle fonti",
                pt: "Completar a partir das fontes",
                nl: "Aanvullen uit bronnen" },
    aide_enrichir: {
      en: "Query the configured sources for this entry and fill in the " +
          "empty fields. Nothing already filled is overwritten.",
      fr: "Interroge les sources configurées pour cette fiche et " +
          "complète les champs vides. Rien de déjà rempli n'est " +
          "écrasé.",
      de: "Fragt die eingerichteten Quellen ab und füllt leere Felder. " +
          "Bereits Ausgefülltes bleibt unangetastet.",
      es: "Consulta las fuentes configuradas y rellena los campos " +
          "vacíos. Nada de lo ya escrito se sobrescribe.",
      it: "Interroga le fonti configurate e riempie i campi vuoti. " +
          "Nulla di già presente viene sovrascritto.",
      pt: "Consulta as fontes configuradas e preenche os campos " +
          "vazios. Nada do que já existe é substituído.",
      nl: "Bevraagt de ingestelde bronnen en vult lege velden aan. " +
          "Bestaande gegevens blijven ongemoeid." },
    aide_accepter: {
      en: "Write the proposed values to the entry and clear the " +
          "proposal tags.",
      fr: "Écrit les valeurs proposées sur la fiche et retire les tags " +
          "de proposition.",
      de: "Schreibt die vorgeschlagenen Werte und entfernt die " +
          "Vorschlags-Tags.",
      es: "Escribe los valores propuestos y quita las etiquetas de " +
          "propuesta.",
      it: "Scrive i valori proposti e rimuove i tag di proposta.",
      pt: "Escreve os valores propostos e retira as etiquetas de " +
          "proposta.",
      nl: "Schrijft de voorgestelde waarden weg en verwijdert de " +
          "voorstel-tags." },
    aide_fusionner: {
      en: "Another entry looks like a duplicate of this one. Merging " +
          "moves its scenes and aliases onto the twin, then DELETES " +
          "this entry. Irreversible.",
      fr: "Une autre fiche paraît être un doublon de celle-ci. La " +
          "fusion reporte ses scènes et ses alias sur la jumelle, puis " +
          "SUPPRIME cette fiche. Sans retour possible.",
      de: "Ein anderer Eintrag scheint ein Duplikat zu sein. Das " +
          "Zusammenführen überträgt Szenen und Aliase und LÖSCHT " +
          "diesen Eintrag. Unwiderruflich.",
      es: "Otra ficha parece un duplicado. La fusión traslada sus " +
          "escenas y alias a la gemela y ELIMINA esta ficha. " +
          "Irreversible.",
      it: "Un'altra scheda sembra un doppione. L'unione sposta scene e " +
          "alias sulla gemella ed ELIMINA questa scheda. " +
          "Irreversibile.",
      pt: "Outra ficha parece um duplicado. A fusão transfere cenas e " +
          "aliases para a gémea e ELIMINA esta ficha. Irreversível.",
      nl: "Een ander item lijkt een duplicaat. Samenvoegen verplaatst " +
          "scènes en aliassen en VERWIJDERT dit item. " +
          "Onomkeerbaar." },
    aide_pas_doublon: {
      en: "Fausse alerte : the pair is exempted for good and will not " +
          "be flagged again.",
      fr: "Fausse alerte : la paire est exemptée définitivement et ne " +
          "sera plus signalée.",
      de: "Fehlalarm: das Paar wird dauerhaft ausgenommen.",
      es: "Falsa alarma: el par queda exceptuado definitivamente.",
      it: "Falso allarme: la coppia è esentata definitivamente.",
      pt: "Falso alerta: o par fica excluído definitivamente.",
      nl: "Vals alarm: het paar wordt definitief uitgesloten." },
    aide_restaurer: {
      en: "Undo the last automatic pass on this entry: fields restored, " +
          "added tags and links removed. Run again to go back further.",
      fr: "Annule le dernier passage automatique sur cette fiche : " +
          "champs remis, tags et liens ajoutés retirés. Relancer " +
          "remonte d'un cran.",
      de: "Macht den letzten automatischen Durchlauf rückgängig. " +
          "Erneut ausführen geht einen Schritt weiter zurück.",
      es: "Deshace la última pasada automática. Repetir retrocede un " +
          "paso más.",
      it: "Annulla l'ultimo passaggio automatico. Ripetere torna " +
          "indietro di un altro passo.",
      pt: "Anula a última passagem automática. Repetir recua mais um " +
          "passo.",
      nl: "Maakt de laatste automatische ronde ongedaan. Nogmaals " +
          "uitvoeren gaat een stap verder terug." },
    aide_verifie: {
      en: "The identification was checked by hand: clear the warning.",
      fr: "L'identification a été contrôlée à la main : retirer " +
          "l'alerte.",
      de: "Zuordnung von Hand geprüft: Hinweis entfernen.",
      es: "Identificación comprobada a mano: quitar el aviso.",
      it: "Identificazione verificata a mano: togliere l'avviso.",
      pt: "Identificação verificada à mão: retirar o aviso.",
      nl: "Identificatie handmatig gecontroleerd: melding weg." },
    inspecter: { en: "What the sources say",
                 fr: "Ce que disent les sources",
                 de: "Was die Quellen sagen",
                 es: "Lo que dicen las fuentes",
                 it: "Cosa dicono le fonti",
                 pt: "O que dizem as fontes",
                 nl: "Wat de bronnen zeggen" },
    aide_inspecter: {
      en: "Shows every value the sources return for this record, "
          + "field by field, and why each was kept or set aside. "
          + "Writes nothing.",
      fr: "Montre toutes les valeurs que les sources renvoient pour "
          + "cette fiche, champ par champ, et pourquoi chacune a été "
          + "retenue ou écartée. N'écrit rien.",
      de: "Zeigt alle Werte der Quellen für diesen Eintrag. Schreibt "
          + "nichts.",
      es: "Muestra todos los valores que devuelven las fuentes. No "
          + "escribe nada.",
      it: "Mostra tutti i valori restituiti dalle fonti. Non scrive "
          + "nulla.",
      pt: "Mostra todos os valores devolvidos pelas fontes. Não "
          + "escreve nada.",
      nl: "Toont alle waarden die de bronnen teruggeven. Schrijft "
          + "niets." },
    generer: { en: "Generate a text", fr: "Générer un texte",
               de: "Text generieren", es: "Generar un texto",
               it: "Genera un testo", pt: "Gerar um texto",
               nl: "Tekst genereren" },
    aide_generer: {
      en: "Writes a draft with the model and shows it before anything "
          + "is applied. Nothing is written until you accept.",
      fr: "Produit un texte avec le modèle et le montre avant toute "
          + "écriture. Rien n'est appliqué tant que vous n'acceptez "
          + "pas.",
      de: "Erzeugt einen Entwurf und zeigt ihn vor jeder Änderung.",
      es: "Produce un borrador y lo muestra antes de escribir nada.",
      it: "Produce una bozza e la mostra prima di scrivere.",
      pt: "Produz um rascunho e mostra-o antes de escrever.",
      nl: "Maakt een concept en toont het voor er iets wordt "
          + "geschreven." },
    ap_titre: { en: "Preview", fr: "Aperçu",
                de: "Vorschau", es: "Vista previa",
                it: "Anteprima", pt: "Pré-visualização",
                nl: "Voorbeeld" },
    ap_actuel: { en: "Current text", fr: "Texte actuel",
                 de: "Aktueller Text", es: "Texto actual",
                 it: "Testo attuale", pt: "Texto atual",
                 nl: "Huidige tekst" },
    ap_nouveau: { en: "Generated text", fr: "Texte généré",
                  de: "Generierter Text", es: "Texto generado",
                  it: "Testo generato", pt: "Texto gerado",
                  nl: "Gegenereerde tekst" },
    ap_ecrire: { en: "Apply", fr: "Appliquer",
                 de: "Übernehmen", es: "Aplicar",
                 it: "Applica", pt: "Aplicar", nl: "Toepassen" },
    ap_annuler: { en: "Discard", fr: "Annuler",
                  de: "Verwerfen", es: "Descartar",
                  it: "Scarta", pt: "Descartar", nl: "Verwerpen" },
    ap_vide: { en: "(nothing yet)", fr: "(rien pour l'instant)",
               de: "(noch nichts)", es: "(nada por ahora)",
               it: "(ancora nulla)", pt: "(nada ainda)",
               nl: "(nog niets)" },
    m_aucun: {
      en: "No model configured — set one in the plugin settings.",
      fr: "Aucun modèle configuré — renseignez-en un dans les "
          + "réglages du plugin.",
      de: "Kein Modell konfiguriert.",
      es: "Ningún modelo configurado.",
      it: "Nessun modello configurato.",
      pt: "Nenhum modelo configurado.",
      nl: "Geen model geconfigureerd." },
    valider_tout: { en: "Mark as checked",
                    fr: "Marquer comme vérifiée",
                    de: "Als geprüft markieren",
                    es: "Marcar como verificada",
                    it: "Segna come verificata",
                    pt: "Marcar como verificada",
                    nl: "Als gecontroleerd markeren" },
    aide_valider_tout: {
      en: "Clears the check marks on this record. Nothing is "
          + "rewritten — the values are already there. To fix one, "
          + "edit the record normally.",
      fr: "Lève les marques de vérification de cette fiche. Rien "
          + "n'est réécrit — les valeurs y sont déjà. Pour en "
          + "corriger une, modifiez la fiche normalement.",
      de: "Hebt die Prüfmarkierungen dieses Eintrags auf. Nichts wird "
          + "neu geschrieben. Zum Korrigieren den Eintrag normal "
          + "bearbeiten.",
      es: "Levanta las marcas de verificación de esta ficha. No se "
          + "reescribe nada. Para corregir una, edite la ficha "
          + "normalmente.",
      it: "Rimuove le marcature di verifica di questa scheda. Nulla "
          + "viene riscritto. Per correggerne una, modifica la scheda "
          + "normalmente.",
      pt: "Levanta as marcas de verificação desta ficha. Nada é "
          + "reescrito. Para corrigir uma, edite a ficha normalmente.",
      nl: "Verwijdert de controlemarkeringen van dit item. Er wordt "
          + "niets herschreven. Bewerk het item normaal om er een te "
          + "corrigeren." },
    a_valider: { en: "to check", fr: "à vérifier",
                 de: "zu prüfen", es: "por verificar",
                 it: "da verificare", pt: "a verificar",
                 nl: "te controleren" },
    aide_a_valider: {
      en: "Written automatically from a single source, or from a "
          + "reading that may be wrong. Worth a glance.",
      fr: "Écrit automatiquement depuis une seule source, ou depuis "
          + "une lecture qui peut se tromper. Mérite un coup d'œil.",
      de: "Automatisch aus einer einzigen Quelle geschrieben oder aus "
          + "einer Lesung, die falsch sein kann. Einen Blick wert.",
      es: "Escrito automáticamente desde una sola fuente, o desde una "
          + "lectura que puede equivocarse. Merece un vistazo.",
      it: "Scritto automaticamente da una sola fonte, o da una "
          + "lettura che può sbagliare. Merita uno sguardo.",
      pt: "Escrito automaticamente a partir de uma única fonte, ou de "
          + "uma leitura que pode enganar-se. Merece uma olhadela.",
      nl: "Automatisch geschreven uit één bron, of uit een lezing die "
          + "fout kan zijn. Een blik waard." },
    accepter: { en: "Apply proposals", fr: "Appliquer les propositions",
                de: "Vorschläge anwenden", es: "Aplicar las propuestas",
                it: "Applica le proposte", pt: "Aplicar as propostas",
                nl: "Voorstellen toepassen" },
    pas_doublon: { en: "Not a duplicate (permanent)",
                   fr: "Pas un doublon (définitif)",
                   de: "Kein Duplikat (dauerhaft)",
                   es: "No es duplicado (definitivo)",
                   it: "Non è un doppione (definitivo)",
                   pt: "Não é duplicado (definitivo)",
                   nl: "Geen duplicaat (definitief)" },
    fusionner: { en: "Merge into twin (deletes this one)",
                 fr: "Fusionner dans le jumeau (supprime celle-ci)",
                 de: "Mit Zwilling vereinen (löscht diesen)",
                 es: "Fusionar con el gemelo (elimina esta)",
                 it: "Unire al gemello (elimina questa)",
                 pt: "Fundir com o gémeo (elimina esta)",
                 nl: "Samenvoegen met dubbele (verwijdert deze)" },
    verifie: { en: "Dismiss warning", fr: "Lever l'alerte",
               de: "Hinweis entfernen", es: "Quitar el aviso",
               it: "Togli l'avviso", pt: "Retirar o aviso",
               nl: "Melding weghalen" },
    restaurer: { en: "Undo last pass", fr: "Annuler le dernier passage",
                 de: "Letzten Durchlauf rückgängig",
                 es: "Deshacer la última pasada",
                 it: "Annulla l'ultimo passaggio",
                 pt: "Anular a última passagem",
                 nl: "Laatste ronde ongedaan maken" },
    confirm_restaurer: {
      en: "Undo the last automatic pass on « {n} »? Collected values " +
          "will be rolled back to their previous state.",
      fr: "Annuler le dernier passage automatique sur « {n} » ? Les " +
          "valeurs collectées reviendront à leur état précédent.",
      de: "Letzten automatischen Durchlauf für « {n} » rückgängig " +
          "machen? Erfasste Werte kehren zum vorherigen Stand zurück.",
      es: "¿Deshacer la última pasada automática sobre « {n} »? Los " +
          "valores recogidos volverán a su estado anterior.",
      it: "Annullare l'ultimo passaggio automatico su « {n} »? I " +
          "valori raccolti torneranno allo stato precedente.",
      pt: "Anular a última passagem automática sobre « {n} »? Os " +
          "valores recolhidos voltarão ao estado anterior.",
      nl: "De laatste automatische ronde op « {n} » ongedaan maken? " +
          "Verzamelde waarden keren terug naar hun vorige staat." },
    confirm: {
      en: "Merge « {n} » into its twin? This entry will be deleted.",
      fr: "Fusionner « {n} » dans son jumeau ? Cette fiche sera supprimée.",
      de: "« {n} » mit dem Zwilling zusammenführen? Dieser Eintrag wird gelöscht.",
      es: "¿Fusionar « {n} » con su gemelo? Esta ficha se eliminará.",
      it: "Unire « {n} » al suo gemello? Questa scheda sarà eliminata.",
      pt: "Fundir « {n} » com o seu gémeo? Esta ficha será eliminada.",
      nl: "« {n} » samenvoegen met de dubbele? Dit item wordt verwijderd." },
    presentation: { en: "Presentation", fr: "Présentation",
                    de: "Vorstellung", es: "Presentación",
                    it: "Presentazione", pt: "Apresentação",
                    nl: "Presentatie" },
    position: { en: "Position", fr: "Position", de: "Position",
                es: "Posición", it: "Posizione", pt: "Posição",
                nl: "Positie" },
    pouvoir: { en: "Dynamic", fr: "Rapport", de: "Rollenspiel",
               es: "Dinámica", it: "Dinamica", pt: "Dinâmica",
               nl: "Dynamiek" },
    partenaires: { en: "Frequent partners", fr: "Partenaires fréquents",
                   de: "Häufige Partner", es: "Compañeros frecuentes",
                   it: "Partner frequenti", pt: "Parceiros frequentes",
                   nl: "Vaste partners" },
    studios_freq: { en: "Main studios", fr: "Studios principaux",
                    de: "Hauptstudios", es: "Estudios principales",
                    it: "Studi principali", pt: "Estúdios principais",
                    nl: "Voornaamste studio's" },
    provenance: { en: "Sources and scores", fr: "Provenance et notes",
                  de: "Herkunft und Bewertungen",
                  es: "Procedencia y notas", it: "Provenienza e voti",
                  pt: "Proveniência e notas",
                  nl: "Herkomst en scores" },
    a_verifier: { en: "Needs attention", fr: "À vérifier",
                  de: "Zu prüfen", es: "A revisar",
                  it: "Da verificare", pt: "A verificar",
                  nl: "Te controleren" },
    non_renseigne: { en: "not set", fr: "non renseigné",
                     de: "nicht angegeben", es: "sin indicar",
                     it: "non indicato", pt: "não indicado",
                     nl: "niet ingevuld" },
    champ: { en: "Field", fr: "Champ", de: "Feld", es: "Campo",
             it: "Campo", pt: "Campo", nl: "Veld" },
    valeur: { en: "Value", fr: "Valeur", de: "Wert", es: "Valor",
              it: "Valore", pt: "Valor", nl: "Waarde" },
    note: { en: "Score", fr: "Note", de: "Note", es: "Nota",
            it: "Voto", pt: "Nota", nl: "Score" },
    sources: { en: "Sources", fr: "Sources", de: "Quellen",
               es: "Fuentes", it: "Fonti", pt: "Fontes",
               nl: "Bronnen" },
    en_cours: { en: "working…", fr: "en cours…", de: "läuft…",
                es: "en curso…", it: "in corso…", pt: "em curso…",
                nl: "bezig…" },
    en_attente: { en: "queued…", fr: "en attente…", de: "wartet…",
                  es: "en cola…", it: "in coda…", pt: "em fila…",
                  nl: "in wachtrij…" },
    champs_completes: { en: "+{n} field(s)", fr: "+{n} champ(s)",
                        de: "+{n} Feld(er)", es: "+{n} campo(s)",
                        it: "+{n} campo/i", pt: "+{n} campo(s)",
                        nl: "+{n} veld(en)" },
    rien_de_neuf: { en: "nothing new", fr: "rien de neuf",
                    de: "nichts Neues", es: "nada nuevo",
                    it: "nulla di nuovo", pt: "nada de novo",
                    nl: "niets nieuws" },
    en_attente: { en: "queued…", fr: "en attente…", de: "wartet…",
                  es: "en cola…", it: "in coda…", pt: "em fila…",
                  nl: "in wachtrij…" },
    deduit: { en: "suggested", fr: "suggéré", de: "vorgeschlagen",
              es: "sugerido", it: "suggerito", pt: "sugerido",
              nl: "voorgesteld" },
    importe: { en: "imported", fr: "importé", de: "importiert",
               es: "importado", it: "importato", pt: "importado",
               nl: "geïmporteerd" },
    rien: { en: "Nothing collected yet — use Enrich.",
            fr: "Rien de collecté pour l'instant — bouton Enrichir.",
            de: "Noch nichts erfasst — Schaltfläche Anreichern.",
            es: "Nada recogido todavía — botón Enriquecer.",
            it: "Ancora nulla — pulsante Arricchisci.",
            pt: "Nada recolhido ainda — botão Enriquecer.",
            nl: "Nog niets verzameld — knop Verrijken." },
  };

  const POSITIONS = {
    "": {}, actif: { en: "Top", fr: "Actif", de: "Aktiv",
                     es: "Activo", it: "Attivo", pt: "Ativo",
                     nl: "Actief" },
    passif: { en: "Bottom", fr: "Passif", de: "Passiv", es: "Pasivo",
              it: "Passivo", pt: "Passivo", nl: "Passief" },
    versatile: { en: "Versatile", fr: "Versatile", de: "Versatil",
                 es: "Versátil", it: "Versatile", pt: "Versátil",
                 nl: "Veelzijdig" },
  };
  const POUVOIRS = {
    "": {}, dominant: { en: "Dominant", fr: "Dominant",
                        de: "Dominant", es: "Dominante",
                        it: "Dominante", pt: "Dominante",
                        nl: "Dominant" },
    soumis: { en: "Submissive", fr: "Soumis", de: "Devot",
              es: "Sumiso", it: "Sottomesso", pt: "Submisso",
              nl: "Onderdanig" },
    permutant: { en: "Switch", fr: "Permutant", de: "Switch",
                 es: "Switch", it: "Switch", pt: "Switch",
                 nl: "Switch" },
  };

  const ALIAS = { french: "fr", français: "fr", francais: "fr",
                  english: "en", anglais: "en", german: "de",
                  deutsch: "de", allemand: "de", spanish: "es",
                  español: "es", espanol: "es", espagnol: "es",
                  italian: "it", italiano: "it", italien: "it",
                  portuguese: "pt", português: "pt", portugues: "pt",
                  portugais: "pt", dutch: "nl", nederlands: "nl",
                  néerlandais: "nl" };

  // Les sources répondent en anglais ou en codes : « Uncut », « Latin »,
  // « PR ». Les afficher tels quels au milieu d'une interface traduite
  // donne un mélange de langues déroutant. Seules les valeurs à
  // vocabulaire fermé sont traduites ; le reste — un titre, un nom —
  // est laissé intact, le traduire serait une erreur.
  const VALEURS = {
    circumcised: {
      cut: { en: "Cut", fr: "Circoncis", de: "Beschnitten",
             es: "Circuncidado", it: "Circonciso", pt: "Circuncidado",
             nl: "Besneden" },
      uncut: { en: "Uncut", fr: "Non circoncis", de: "Unbeschnitten",
               es: "No circuncidado", it: "Non circonciso",
               pt: "Não circuncidado", nl: "Onbesneden" },
    },
    ethnicity: {
      white: { en: "White", fr: "Blanche", de: "Weiß", es: "Blanca",
               it: "Bianca", pt: "Branca", nl: "Blank" },
      black: { en: "Black", fr: "Noire", de: "Schwarz", es: "Negra",
               it: "Nera", pt: "Negra", nl: "Zwart" },
      asian: { en: "Asian", fr: "Asiatique", de: "Asiatisch",
               es: "Asiática", it: "Asiatica", pt: "Asiática",
               nl: "Aziatisch" },
      latin: { en: "Latin", fr: "Latino", de: "Latino", es: "Latina",
               it: "Latina", pt: "Latina", nl: "Latijns" },
      hispanic: { en: "Hispanic", fr: "Hispanique", de: "Hispanisch",
                  es: "Hispana", it: "Ispanica", pt: "Hispânica",
                  nl: "Hispanic" },
      indian: { en: "Indian", fr: "Indienne", de: "Indisch",
                es: "India", it: "Indiana", pt: "Indiana",
                nl: "Indiaas" },
      "middle eastern": { en: "Middle Eastern",
                          fr: "Moyen-orientale",
                          de: "Nahöstlich", es: "Oriente Medio",
                          it: "Mediorientale", pt: "Médio Oriente",
                          nl: "Midden-Oosters" },
    },
  };

  function valeurLisible(champ, valeur) {
    const table = VALEURS[champ];
    if (!table) return valeur;
    const entree = table[String(valeur || "").trim().toLowerCase()];
    if (!entree) return valeur;
    return entree[reglages.lang] || entree[LANG_DEFAUT] || valeur;
  }

  const reglages = { lang: LANG_DEFAUT, prefix: PREFIX_DEFAUT,
    seuilVerif: 7,
                     profil: "" };

  const tr = (table, cle) =>
    (table[cle] || {})[reglages.lang] ||
    (table[cle] || {})[LANG_DEFAUT] || cle;
  const tag = (cle) => reglages.prefix + ":" + tr(TAGS, cle);

  const GQL = (query, variables) =>
    fetch("/graphql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.errors) throw new Error(d.errors[0].message);
        return d.data;
      });

  const attendre = (ms) => new Promise((r) => setTimeout(r, ms));

  // Une tâche de plugin est asynchrone : la mutation rend un numéro de
  // travail, pas un résultat. Sans attendre sa fin, le bouton affichait
  // une coche alors que rien n'était encore écrit, et le panneau
  // continuait de montrer l'état d'avant — d'où l'impression que le
  // bouton ne servait à rien.
  // Stash n'exécute qu'UNE tâche de plugin à la fois : une tâche
  // lancée alors qu'une autre tourne reste en file (« READY ») sans
  // rien faire, parfois plusieurs minutes. Afficher « en cours » dans
  // cet état est faux et donne l'impression d'un blocage — c'est
  // exactement ce qui s'est produit. L'état est donc rapporté tel
  // qu'il est, position dans la file comprise.
  async function suivre(numero, signaler, maxSecondes) {
    const limite = Date.now() + (maxSecondes || 900) * 1000;
    let vuEnCours = false;
    while (Date.now() < limite) {
      await attendre(1500);
      let job = null, file = [];
      try {
        const d = await GQL(
          `query($id: ID!) { findJob(input: {id: $id}) { status error }
             jobQueue { id status } }`, { id: String(numero) });
        job = d.findJob;
        file = d.jobQueue || [];
      } catch (err) {
        return vuEnCours ? "fini" : "inconnu";
      }
      // Un travail terminé disparaît de la file : sans l'avoir vu
      // démarrer on ne peut rien conclure, après l'avoir vu tourner
      // c'est qu'il est allé au bout.
      if (!job) return vuEnCours ? "fini" : "inconnu";
      if (job.status === "FINISHED") return "fini";
      if (job.status === "FAILED") return job.error || "échec";
      if (job.status === "CANCELLED") return "annulé";
      if (job.status === "RUNNING") {
        vuEnCours = true;
        if (signaler) signaler("en_cours", 0);
      } else {
        // Combien de travaux le précèdent ?
        const rang = file.findIndex(
          (j) => String(j.id) === String(numero));
        if (signaler) signaler("en_attente", rang > 0 ? rang : 0);
      }
    }
    return "trop long";
  }

  const runMode = (mode, extra) =>
    GQL(`mutation($a: Map) { runPluginTask(plugin_id: "gaizer",
           task_name: "Gaizer", args_map: $a) }`,
        { a: Object.assign({ mode }, extra || {}) })
      .then((d) => d.runPluginTask);

  // Lance la tâche ET attend qu'elle soit terminée, pour que ce qui
  // suit — le rafraîchissement — source l'état réel.
  async function runModeEtAttendre(mode, extra, signaler) {
    const numero = await runMode(mode, extra);
    if (!numero) return "inconnu";
    return await suivre(numero, signaler);
  }

  // Une tâche annonce « fini » sans dire ce qu'elle a fait : sur une
  // fiche déjà complète, une seule valeur change et rien ne le montre.
  // Comparer la trace de provenance avant et après donne le compte
  // rendu sans rien ajouter côté serveur.
  function champsDe(source) {
    return new Set(
      String(source || "").split(" | ")
        .map((l) => (l.match(/^([\w_]+)\s*:/) || [])[1])
        .filter(Boolean));
  }

  async function traceDe(type, id) {
    const q = type === "performer"
      ? `query($id: ID!) { findPerformer(id: $id) { custom_fields } }`
      : type === "studio"
        ? `query($id: ID!) { findStudio(id: $id) { custom_fields } }`
        : `query($id: ID!) { findScene(id: $id) { custom_fields } }`;
    try {
      const d = await GQL(q, { id: String(id) });
      const f = d.findPerformer || d.findStudio || d.findScene || {};
      return (f.custom_fields || {}).enrich_sources || "";
    } catch (err) {
      return "";
    }
  }

  GQL(`{ configuration { plugins } }`)
    .then((d) => {
      const c = (d.configuration.plugins || {})["gaizer"] || {};
      const brut = String(c.language || "").trim().toLowerCase();
      reglages.lang = TAGS.created[brut] ? brut
        : (ALIAS[brut] || LANG_DEFAUT);
      reglages.prefix =
        String(c.proposalTagPrefix || "").trim() || PREFIX_DEFAUT;
      reglages.profil = String(c.tagProfile || "").trim().toLowerCase();
      // Réglage propre aux présentations, sinon modèle par défaut :
      // la même règle que le serveur applique.
      reglages.modele = String(c.aiBiohot || c.aiDefault || "").trim();
      const seuil = parseFloat(c.autoAcceptThreshold);
      reglages.seuilVerif = Number.isFinite(seuil) ? seuil : 7;
    })
    .catch((err) => console.warn("Gaizer : réglages illisibles", err));

  // ── Lecture de enrich_sources ────────────────────────────────────
  // « champ: valeur (9.0/10 · src1+src2 · commentaire) | … »
  function lireProvenance(brut) {
    const out = [];
    // Le plugin appose « · auto AAAA-MM-JJ » en fin de ligne. Cet
    // horodatage tombait APRÈS la parenthèse fermante, si bien que la
    // dernière entrée — et elle seule — échappait à l'analyse et
    // s'affichait en vrac dans la colonne du champ.
    let horodatage = "";
    let texte = String(brut || "");
    const fin = texte.match(/\s*·\s*(auto|manuel)\s+(\d{4}-\d{2}-\d{2})\s*$/);
    if (fin) {
      horodatage = fin[2];
      texte = texte.slice(0, fin.index);
    }
    for (const l of texte.split(" | ")) {
      const m = l.match(
        /^([\w_]+)\s*:\s*(.+?)\s*\(([\d.]+)\/10\s*·\s*([^)·]+?)(?:\s*·\s*([^)]+))?\)\s*$/
      );
      if (m) {
        out.push({ champ: m[1], valeur: m[2], note: parseFloat(m[3]),
                   sources: m[4].trim(),
                   commentaire: (m[5] || "").trim() });
      } else if (l.trim()) {
        out.push({ champ: "", valeur: l.trim(), note: null,
                   sources: "", commentaire: "" });
      }
    }
    if (horodatage) out.horodatage = horodatage;
    return out;
  }

  // La couleur passe par les classes contextuelles de Bootstrap :
  // elles suivent le thème actif au lieu de l'ignorer.
  const classeNote = (n) =>
    n === null ? "text-muted"
      : n >= 8.5 ? "text-success"
        : n >= 7 ? "text-warning" : "text-danger";

  // ── Composants ───────────────────────────────────────────────────
  // Les noms cités ne servent à rien s'il faut les recopier dans la
  // recherche : ils deviennent des liens. L'identifiant est résolu
  // quand c'est possible, sinon le lien pointe vers une recherche —
  // toujours utile, jamais cassé.
  function Liens(props) {
    const [ids, setIds] = React.useState({});
    const noms = props.noms;
    const type = props.type;             // performers | studios
    React.useEffect(() => {
      let vivant = true;
      const champ = type === "studios" ? "findStudios" : "findPerformers";
      const filtre = type === "studios" ? "studio_filter" : "performer_filter";
      Promise.all(noms.map((n) =>
        GQL(`query($n: String!) { ${champ}(${filtre}: {name: {value: $n,
               modifier: EQUALS}}, filter: {per_page: 1}) {
               ${type} { id name } } }`, { n })
          .then((d) => {
            const l = (d[champ] || {})[type] || [];
            return l.length ? [n, l[0].id] : null;
          })
          .catch(() => null)))
        .then((paires) => {
          if (!vivant) return;
          const table = {};
          for (const paire of paires) if (paire) table[paire[0]] = paire[1];
          setIds(table);
        });
      return () => { vivant = false; };
    }, [noms.join("|"), type]);

    const sortie = [];
    noms.forEach((n, i) => {
      if (i) sortie.push(e("span", { key: "s" + i,
                                     className: "text-muted" }, " · "));
      const cible = ids[n]
        ? "/" + type + "/" + ids[n]
        : "/" + type + "?q=" + encodeURIComponent(n);
      sortie.push(e("a", { key: n, href: cible }, n));
    });
    return e("div", null, sortie);
  }

  // Les présentations déjà enregistrées portent parfois un titre en
  // gras et le nom répété — le modèle ajoutait cela de lui-même. Les
  // régénérer toutes coûterait un appel par fiche : mieux vaut nettoyer
  // à l'affichage, ce qui vaut aussi pour l'existant.
  function nettoyerTexte(texte, nom) {
    let t = String(texte || "").trim();
    t = t.replace(/\*\*(.+?)\*\*/g, "$1").replace(/__(.+?)__/g, "$1");
    t = t.replace(/^#{1,6}\s*/gm, "");
    if (nom) {
      const echappe = nom.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      t = t.replace(new RegExp("^" + echappe + "\\s*[—–\\-:]\\s*"), "");
    }
    return t.trim();
  }

  function Etiquette(props) {
    return e("div", { className: "text-muted small text-uppercase mb-1",
                      style: { letterSpacing: ".06em",
                               fontSize: ".7rem" } },
             props.children);
  }

  function Provenance(props) {
    const lignes = props.lignes.filter((l) => l.note !== null);
    const notes = props.lignes.filter((l) => l.note === null);
    return e("details", { className: "mt-3" },
      e("summary", { className: "text-muted small",
                     style: { cursor: "pointer" } },
        tr(L, "provenance") + " (" + props.lignes.length + ")"
        + (props.lignes.horodatage
            ? " · " + props.lignes.horodatage : "")),
      e("div", { className: "table-responsive mt-2" },
        e("table", { className: "table table-sm table-borderless mb-0 small" },
          e("thead", null,
            e("tr", { className: "text-muted" },
              ["champ", "valeur", "note", "sources"].map((c) =>
                e("th", { key: c, className: "border-0 py-1",
                          style: { fontSize: ".68rem",
                                   textTransform: "uppercase" } },
                  tr(L, c))))),
          e("tbody", null,
            lignes.slice().sort((a, b) => (b.note || 0) - (a.note || 0))
              .map((l, i) =>
                e("tr", { key: i },
                  e("td", { className: "text-muted py-1",
                            style: { whiteSpace: "nowrap" } }, l.champ),
                  e("td", { className: "py-1", title: l.commentaire },
                    valeurLisible(l.champ, l.valeur)),
                  e("td", { className: classeNote(l.note) + " py-1",
                            style: { whiteSpace: "nowrap",
                                     fontVariantNumeric: "tabular-nums" } },
                    l.note === null ? "" : l.note.toFixed(1)),
                  e("td", { className: "text-muted py-1" },
                    l.sources))))),
        notes.length
          ? e("div", { className: "text-muted small mt-1" },
              notes.map((l, i) =>
                e("div", { key: i }, l.valeur)))
          : null));
  }

  function ChoixRole(props) {
    const [valeur, setValeur] = React.useState(props.valeur || "");
    const [etat, setEtat] = React.useState("");
    // Une valeur lue par l'IA ou reprise d'un import n'a pas le même
    // statut qu'une valeur saisie : elle est signalée, et la modifier
    // vaut confirmation. Seule « saisi » — ou l'absence d'origine sur
    // une fiche jamais marquée — ne porte pas de pastille.
    const origine = String(props.origine || "");
    const deduit = valeur && origine && origine !== "saisi";
    const changer = async (v) => {
      setValeur(v);
      try {
        await GQL(`mutation($i: PerformerUpdateInput!) {
                     performerUpdate(input: $i) { id } }`,
          { i: { id: props.id,
                 custom_fields: { partial: {
                   [props.champ]: v,
                   enrich_role_origine: "saisi" } } } });
        setEtat("is-valid");
      } catch (err) {
        setEtat("is-invalid");
        console.error("Gaizer", err);
      }
      setTimeout(() => setEtat(""), 1600);
    };
    return e("div", { className: "col-auto mb-3" },
      e(Etiquette, null, tr(L, props.cle),
        deduit
          ? e("span", { className: "badge badge-secondary ml-1",
                        title: props.justification || "",
                        style: { cursor: "help", fontWeight: 400 } },
              tr(L, origine === "import" ? "importe" : "deduit"))
          : null),
      e("select", {
        className: "form-control form-control-sm input-control " + etat,
        style: { maxWidth: "11rem", marginBottom: 0 },
        value: valeur,
        onChange: (ev) => changer(ev.target.value),
      }, Object.keys(props.table).map((v) =>
        e("option", { key: v, value: v },
          v === "" ? tr(L, "non_renseigne") : tr(props.table, v)))));
  }

  function Bouton(props) {
    const [libelle, setLibelle] = React.useState(null);
    const [occupe, setOccupe] = React.useState(false);
    const cliquer = async () => {
      setOccupe(true);
      setLibelle(tr(L, "en_attente"));
      const signaler = (etat, rang) =>
        setLibelle(etat === "en_cours"
          ? tr(L, "en_cours")
          : tr(L, "en_attente") + (rang ? " (" + rang + ")" : ""));
      // La trace d'avant sert de point de comparaison : sans elle, on
      // ne peut dire que « fini », ce qui n'apprend rien.
      const avant = props.suivi
        ? await traceDe(props.suivi.type, props.suivi.id) : null;
      try {
        const issue = await props.action(signaler);
        if (issue && issue !== "fini" && issue !== "inconnu") {
          setLibelle("⚠");
          console.warn("Gaizer :", issue);
        } else if (avant !== null) {
          const apres = await traceDe(props.suivi.type, props.suivi.id);
          const ancien = champsDe(avant);
          const nouveaux = [...champsDe(apres)]
            .filter((c) => !ancien.has(c));
          setLibelle(nouveaux.length
            ? tr(L, "champs_completes").replace("{n}", nouveaux.length)
            : tr(L, "rien_de_neuf"));
        } else {
          setLibelle("✓");
        }
        if (props.recharger) props.recharger();
      } catch (err) {
        setLibelle("✗");
        console.error("Gaizer", err);
      }
      setTimeout(() => { setLibelle(null); setOccupe(false); }, 3400);
    };
    return e("button", {
      className: "btn btn-sm mr-2 mb-1 " +
        (props.danger ? "btn-outline-danger"
          : props.principal ? "btn-primary" : "btn-secondary"),
      // Un libellé de deux mots ne peut pas dire ce que fait une
      // action destructive : l'explication est au survol.
      title: tr(L, "aide_" + props.cle),
      disabled: occupe, onClick: cliquer,
    }, libelle === null ? tr(L, props.cle) : libelle);
  }

  async function tagId(nom) {
    const q = await GQL(
      `query($n: String!) { findTags(tag_filter: {name: {value: $n,
         modifier: EQUALS}}) { tags { id name } } }`, { n: nom });
    const t = (q.findTags.tags || []).find((x) => x.name === nom);
    if (t) return t.id;
    return (await GQL(
      `mutation($n: String!) { tagCreate(input: {name: $n}) { id } }`,
      { n: nom })).tagCreate.id;
  }

  async function poserTag(type, fiche, cle) {
    const tid = await tagId(tag(cle));
    const ids = (fiche.tags || []).map((t) => t.id);
    if (!ids.includes(tid)) ids.push(tid);
    const mut = type === "performer"
      ? `mutation($i: PerformerUpdateInput!) { performerUpdate(input: $i) { id } }`
      : `mutation($i: SceneUpdateInput!) { sceneUpdate(input: $i) { id } }`;
    await GQL(mut, { i: { id: fiche.id, tag_ids: ids } });
  }

  const champStudio = (id, cle, valeur) =>
    GQL(`mutation($i: StudioUpdateInput!) { studioUpdate(input: $i) { id } }`,
        { i: { id, custom_fields: { partial: { [cle]: valeur } } } });

  // Une biographie n'est pas un synopsis : chaque famille a son
  // champ et son mode. Le meme prompt pour les trois produirait
  // trois textes egalement inadaptes.
  const MODES_GENERATION = {
    performer: ["performer_id", "details"],
    studio: ["studio_id", "details"],
    scene: ["scene_id", "details"],
  };

  // Un texte genere REMPLACE un texte existant. Le montrer a cote de
  // l'actuel permet de decider en sachant ce qu'on perd — ce qu'aucun
  // retour en arriere ne rend aussi simple, puisqu'il faut d'abord
  // s'apercevoir du probleme.
  function Apercu(props) {
    const { type, fiche, cf } = props;
    const nouveau = String(cf.enrich_apercu || "");
    if (!nouveau) return null;
    const champ = (MODES_GENERATION[type] || [])[1] || "details";
    const actuel = String(fiche[champ] || "");
    const [etat, setEtat] = React.useState("");

    const finir = async (appliquer) => {
      setEtat("…");
      try {
        const maj = { id: fiche.id,
                      custom_fields: { partial: { enrich_apercu: "" } } };
        if (appliquer) maj[champ] = nouveau;
        const mut = type === "performer" ? "performerUpdate"
          : (type === "studio" ? "studioUpdate" : "sceneUpdate");
        const t = type === "performer" ? "PerformerUpdateInput"
          : (type === "studio" ? "StudioUpdateInput"
                               : "SceneUpdateInput");
        await GQL(`mutation($i: ${t}!) { ${mut}(input: $i) { id } }`,
                  { i: maj });
        props.recharger && props.recharger();
      } catch (err) {
        setEtat(String(err).slice(0, 70));
      }
    };

    return e("div", { className: "border rounded p-3 mb-3" },
      e("div", { className: "d-flex align-items-baseline mb-2",
                 style: { gap: ".6rem" } },
        e("div", { className: "text-muted text-uppercase",
                   style: { letterSpacing: ".06em",
                            fontSize: ".72rem" } }, tr("ap_titre")),
        // Le modèle qui a produit ce texte : sans lui, on juge un
        // résultat sans savoir d'où il vient, et changer de modèle
        // devient un tâtonnement.
        reglages.modele
          ? e("code", { className: "small text-muted" },
              reglages.modele)
          : e("span", { className: "text-warning small" },
              tr("m_aucun"))),
      e("div", { className: "row" },
        e("div", { className: "col-md-6 mb-2" },
          e("div", { className: "text-muted small mb-1" },
            tr("ap_actuel")),
          e("div", { className: "small",
                     style: { whiteSpace: "pre-wrap", opacity: .7 } },
            actuel || tr("ap_vide"))),
        e("div", { className: "col-md-6 mb-2" },
          e("div", { className: "text-muted small mb-1" },
            tr("ap_nouveau")),
          e("div", { className: "small",
                     style: { whiteSpace: "pre-wrap" } }, nouveau))),
      e("div", { className: "d-flex align-items-center",
                 style: { gap: ".5rem" } },
        e("button", { className: "btn btn-sm btn-primary",
                      onClick: () => finir(true) }, tr("ap_ecrire")),
        e("button", { className: "btn btn-sm btn-secondary",
                      onClick: () => finir(false) }, tr("ap_annuler")),
        etat ? e("span", { className: "text-muted small" }, etat)
             : null));
  }

  function Actions(props) {
    const { type, fiche, cf } = props;
    const noms = (fiche.tags || []).map((t) => t.name);
    const a = (cle) => noms.includes(tag(cle));
    const boutons = [];
    const suivi = { type, id: fiche.id };
    const B = (cle, action, principal) =>
      boutons.push(e(Bouton, { key: cle, cle, action, principal,
                               recharger: props.recharger, suivi }));

    // Un signalement qui ne peut pas etre leve devient du bruit :
    // l'utilisateur voit la pastille, ne sait qu'en faire, et cesse
    // de la regarder.
    //
    // La validation est TOUT OU RIEN. Cocher champ par champ
    // reproduirait l'editeur de Stash en moins bien ; pour corriger
    // une valeur precise, l'edition normale de la fiche est le bon
    // outil — et corriger une valeur la valide de fait.
    const lignesFiche = lireProvenance(cf.enrich_sources);
    const aVerifier = lignesFiche.filter(aValider).length;
    if (aVerifier) {
      const cleId = type === "performer" ? "performer_id"
        : (type === "studio" ? "studio_id" : "scene_id");
      B("valider_tout",
        (signaler) => runModeEtAttendre(
          "valider_fiche", { [cleId]: fiche.id }, signaler),
        false);
    }

    // Regler un prompt sans le voir agir, c'est ajuster a l'aveugle :
    // on lance un lot, on lit ce qui est sorti, on revient au
    // panneau, on recommence. Ici, un essai coute un appel.
    const idGen = (MODES_GENERATION[type] || [])[0];
    if (idGen && !cf.enrich_apercu) {
      B("generer",
        (signaler) => runModeEtAttendre(
          "generer_apercu", { [idGen]: fiche.id }, signaler),
        false);
    }

    if (type === "performer") {
      // Elle interroge les sources de CETTE fiche : la reléguer au
      // panneau obligeait à y ressaisir un nom qu'on a sous les yeux.
      // Lecture seule — rien n'est écrit.
      B("inspecter",
        (signaler) => runModeEtAttendre(
          "inspecter_collecte", { nom: fiche.name || "" }, signaler),
        false);
      B("enrichir",
        (signaler) => runModeEtAttendre("enrich_one_performer", { performer_id: fiche.id }, signaler),
        true);
      if (a("proposal"))
        B("accepter", async (signaler) => {
          await poserTag(type, fiche, "accept");
          return await runModeEtAttendre("apply_accepted", signaler);
        }, true);
      if (a("duplicate")) {
        B("pas_doublon", async (signaler) => {
          await poserTag(type, fiche, "not_duplicate");
          return await runModeEtAttendre("detect_duplicates", signaler);
        });
        boutons.push(e(Bouton, { key: "fusionner", cle: "fusionner",
                                 danger: true, action: async (signaler) => {
          if (!confirm(tr(L, "confirm").replace("{n}", fiche.name)))
            return;
          await poserTag(type, fiche, "merge");
          return await runModeEtAttendre("merge_marked", signaler);
        } }));
      }
      B("restaurer", async () => {
        if (!confirm(tr(L, "confirm_restaurer")
            .replace("{n}", fiche.name || fiche.title || "")))
          return;
        await poserTag(type, fiche, "restore");
        return await runModeEtAttendre("restore_marked", signaler);
      });
    } else if (type === "scene") {
      B("enrichir",
        (signaler) => runModeEtAttendre("enrich_one_scene", { scene_id: fiche.id }, signaler), true);
      if (a("proposal"))
        B("accepter", async (signaler) => {
          await poserTag(type, fiche, "accept");
          return await runModeEtAttendre("apply_accepted_scenes", signaler);
        }, true);
      if (a("verify"))
        B("verifie", async (signaler) => {
          const garder = (fiche.tags || [])
            .filter((t) => t.name !== tag("verify")).map((t) => t.id);
          await GQL(
            `mutation($i: SceneUpdateInput!) { sceneUpdate(input: $i) { id } }`,
            { i: { id: fiche.id, tag_ids: garder } });
        });
      B("restaurer", async () => {
        if (!confirm(tr(L, "confirm_restaurer")
            .replace("{n}", fiche.name || fiche.title || "")))
          return;
        await poserTag(type, fiche, "restore");
        return await runModeEtAttendre("restore_marked", signaler);
      });
    } else {
      B("enrichir",
        (signaler) => runModeEtAttendre("enrich_one_studio", { studio_id: fiche.id }, signaler),
        true);
      if ((cf.enrich_rapport || "").trim() && !cf.enrich_doublon_id)
        B("accepter", async (signaler) => {
          await champStudio(fiche.id, "enrich_accept", "1");
          return await runModeEtAttendre("apply_accepted_studios", signaler);
        }, true);
      if (cf.enrich_doublon_id) {
        B("pas_doublon", async (signaler) => {
          await champStudio(fiche.id, "enrich_pas_doublon_demande",
                            cf.enrich_doublon_id);
          return await runModeEtAttendre("detect_duplicates_studios", signaler);
        });
        B("fusionner", async (signaler) => {
          if (!confirm(tr(L, "confirm").replace("{n}", fiche.name)))
            return;
          await champStudio(fiche.id, "enrich_fusionner",
                            cf.enrich_doublon_id);
          return await runModeEtAttendre("merge_marked_studios", signaler);
        });
      }
      B("restaurer", async () => {
        if (!confirm(tr(L, "confirm_restaurer")
            .replace("{n}", fiche.name || fiche.title || "")))
          return;
        await champStudio(fiche.id, "enrich_restaurer", "1");
        return await runModeEtAttendre("restore_marked", signaler);
      });
    }
    return e("div", { className: "mt-3 pt-2 border-top" }, boutons);
  }

  // Un enrichissement automatique ecrit des valeurs dont certaines
  // meritent un regard : une seule source, une note basse, ou une
  // lecture d'image qui peut se tromper.
  //
  // Les signaler DANS la fiche — la ou l'utilisateur regarde deja —
  // evite de lui demander d'aller chercher un rapport qu'il ne lira
  // pas. Une pastille discrete suffit : il s'agit d'attirer l'oeil,
  // non d'alarmer.
  function aValider(ligne) {
    if (!ligne || ligne.note === null) return false;
    // Une note basse dit que les sources se contredisaient ou qu'une
    // seule a repondu. Le SEUIL vient du serveur : le recopier ici le
    // ferait diverger de celui qui decide, sans que rien ne le
    // signale.
    if (ligne.note < reglages.seuilVerif) return true;
    // Une lecture d'image ou de chemin n'est pas une source
    // documentaire, quelle que soit sa note.
    const src = String(ligne.sources || "").toLowerCase();
    return src.includes("vision") || src.includes("chemin")
        || src.includes("generique") || src.includes("générique")
        || src.includes("fichier");
  }

  function Panneau(props) {
    const { type, fiche } = props;
    const cf = fiche.custom_fields || {};
    const hot = nettoyerTexte(cf.bio_hot, fiche.name || fiche.title);
    const alerte = String(cf.enrich_rapport || "").trim();
    const lignes = lireProvenance(cf.enrich_sources);
    let reco = {};
    try { reco = JSON.parse(cf.reco_data || "{}"); } catch (err) { reco = {}; }

    const listes = [];
    for (const [cle, valeurs] of [["partenaires", reco.partenaires],
                                  ["studios_freq", reco.studios]]) {
      if (Array.isArray(valeurs) && valeurs.length) {
        listes.push(e("div", { key: cle, className: "col-auto mb-3",
                               style: { minWidth: "12rem" } },
          e(Etiquette, null, tr(L, cle)),
          e(Liens, { noms: valeurs.slice(0, 5).map(String),
                     type: cle === "partenaires" ? "performers"
                                                 : "studios" })));
      }
    }

    const roles = [];
    if (type === "performer") {
      const montrer = !reglages.profil ||
        ["gay", "bi", "pan", "trans", "mixte"].includes(reglages.profil);
      const commun = { id: fiche.id, origine: cf.enrich_role_origine,
                       justification: cf.enrich_role_motif };
      if (montrer)
        roles.push(e(ChoixRole, Object.assign({}, commun,
          { key: "p", cle: "position", table: POSITIONS,
            champ: "enrich_position", valeur: cf.enrich_position })));
      roles.push(e(ChoixRole, Object.assign({}, commun,
        { key: "d", cle: "pouvoir", table: POUVOIRS,
          champ: "enrich_pouvoir", valeur: cf.enrich_pouvoir })));
    }

    const rien = !hot && !lignes.length && !listes.length;

    return e("div", { className: "card bg-transparent border mt-3 mb-3" },
      e("div", { className: "card-header py-1 px-3 d-flex align-items-center" },
        e("span", { className: "text-muted",
                    style: { fontSize: ".7rem", fontWeight: 600,
                             letterSpacing: ".08em" } }, "GAIZER"),
        alerte
          ? e("span", { className: "badge badge-warning ml-auto",
                        title: alerte,
                        style: { cursor: "help" } },
              "⚠ " + tr(L, "a_verifier"))
          : null),
      e("div", { className: "card-body py-3 px-3" },
        hot
          ? e("div", { className: "mb-3" },
              e(Etiquette, null, tr(L, "presentation")),
              e("div", { style: { whiteSpace: "pre-wrap",
                                  lineHeight: 1.55 } }, hot))
          : null,
        roles.length || listes.length
          ? e("div", { className: "row align-items-start" },
              roles.concat(listes))
          : null,
        rien ? e("div", { className: "text-muted small" },
                 tr(L, "rien")) : null,
        lignes.length ? e(Provenance, { lignes }) : null,
        e(Actions, { type, fiche, cf,
                     recharger: props.recharger })));
  }

  // Les données du panneau ne sont pas toutes dans les props du
  // composant patché : un petit chargement complète ce qui manque.
  function PanneauCharge(props) {
    const [fiche, setFiche] = React.useState(null);
    const [tour, setTour] = React.useState(0);
    const id = props.id;
    React.useEffect(() => {
      let vivant = true;
      const q = props.type === "performer"
        ? `query($id: ID!) { findPerformer(id: $id) {
             id name tags { id name } custom_fields } }`
        : props.type === "studio"
          ? `query($id: ID!) { findStudio(id: $id) {
               id name custom_fields } }`
          : `query($id: ID!) { findScene(id: $id) {
               id title tags { id name } custom_fields } }`;
      GQL(q, { id })
        .then((d) => {
          if (!vivant) return;
          setFiche(d.findPerformer || d.findStudio || d.findScene);
        })
        .catch((err) => console.error("Gaizer", err));
      return () => { vivant = false; };
    }, [id, props.type, tour]);
    if (!fiche) return null;
    return e(Panneau, { type: props.type, fiche,
                        recharger: () => setTour((t) => t + 1) });
  }

  // ── Greffes ──────────────────────────────────────────────────────
  // Le patch « after » est appelé ainsi par Stash :
  //     i = fn.apply(this, args.concat(resultat))
  // où `args` sont ceux du composant React, soit (props, contexte).
  // Le résultat du rendu est donc le DERNIER argument, pas le second :
  // le lire en deuxième position revient à récupérer le contexte, un
  // objet vide, que React refuse d'afficher comme enfant (erreur #31).
  // La valeur retournée devient directement le rendu du composant.
  function greffer(nom, type, extraireId) {
    API.patch.after(nom, function () {
      const args = Array.prototype.slice.call(arguments);
      const resultat = args[args.length - 1];
      const props = args[0];
      let id = null;
      try { id = extraireId(props); } catch (err) { id = null; }
      if (!id) return resultat;
      // Le panneau porte l'essentiel : il précède les détails bruts
      // plutôt que de les suivre, sans quoi il faut faire défiler
      // toute la liste des champs pour l'atteindre.
      return e(React.Fragment, null,
               e(PanneauCharge, { type, id: String(id) }),
               resultat);
    });
  }

  // Le bloc « Champs personnalisés » de Stash déballait tout : le JSON
  // de l'historique, la liste des sources, la présentation — soit
  // exactement ce que le panneau présente en clair juste au-dessus.
  // Ces champs sont masqués DE L'AFFICHAGE seulement : ils restent en
  // base, consultables par l'éditeur de fiche et par l'API.
  const CHAMPS_PLUGIN = /^(enrich_|bio_hot$|reco_data$)/;

  API.patch.instead("CustomFields", function () {
    const args = Array.prototype.slice.call(arguments);
    const suivant = args[args.length - 1];
    const props = args[0];
    const valeurs = (props && props.values) || null;
    if (!valeurs || typeof valeurs !== "object")
      return suivant.apply(this, args.slice(0, -1));
    const filtrees = {};
    let masques = 0;
    for (const cle of Object.keys(valeurs)) {
      if (CHAMPS_PLUGIN.test(cle)) { masques += 1; continue; }
      filtrees[cle] = valeurs[cle];
    }
    if (!masques) return suivant.apply(this, args.slice(0, -1));
    // Plus rien à montrer : ne pas laisser un intitulé vide.
    if (!Object.keys(filtrees).length) return null;
    const nouveaux = args.slice(0, -1);
    nouveaux[0] = Object.assign({}, props, { values: filtrees });
    return suivant.apply(this, nouveaux);
  });

  // « PerformerDetailsPanel.DetailGroup » enveloppe TOUTE la fiche :
  // genre, âge, pays… puis la biographie, les étiquettes et les champs
  // personnalisés. Se greffer avant ou après ce bloc place le panneau
  // aux extrémités ; l'insérer parmi ses enfants, juste avant la
  // biographie, le met là où il se lit — après les données de Stash,
  // avant le texte.
  API.patch.before("PerformerDetailsPanel.DetailGroup", function () {
    const args = Array.prototype.slice.call(arguments);
    const props = args[0] || {};
    const id = props.performer && props.performer.id;
    const enfants = props.children;
    if (!id || !Array.isArray(enfants)) return args;
    // Le bloc de détails contient, dans l'ordre : les données de
    // Stash, la biographie, les étiquettes, puis les champs
    // personnalisés — ces derniers reconnaissables à leur propriété
    // « values » plutôt qu'à un identifiant. Le panneau se glisse
    // juste avant eux : après le texte, avant la mécanique.
    let place = enfants.findIndex(
      (c) => c && c.props && c.props.values !== undefined);
    if (place < 0) {
      const iDetails = enfants.findIndex(
        (c) => c && c.props && c.props.id === "details");
      place = iDetails >= 0 ? iDetails + 1 : enfants.length;
    }
    const neufs = enfants.slice();
    neufs.splice(place, 0,
      e(PanneauCharge, { key: "gaizer", type: "performer",
                         id: String(id) }));
    const nouveauxArgs = args.slice();
    nouveauxArgs[0] = Object.assign({}, props, { children: neufs });
    return nouveauxArgs;
  });
  greffer("StudioDetailsPanel", "studio",
          (p) => p && p.studio && p.studio.id);

  // La page scène n'est pas patchable sur 0.31.x : repli DOM, mais
  // déclenché par l'événement de navigation plutôt que par une
  // observation continue du document — pas d'observateur qui traîne.
  function greffeScene() {
    const m = location.pathname.match(/^\/scenes\/(\d+)/);
    const ancien = document.getElementById("gaizer-scene");
    if (!m) { if (ancien) ancien.remove(); return; }
    if (ancien) return;
    const cible = document.querySelector(
      ".scene-details, .scene-tabs, .detail-body, #scene-tabs");
    if (!cible) { setTimeout(greffeScene, 400); return; }
    const hote = document.createElement("div");
    hote.id = "gaizer-scene";
    cible.insertBefore(hote, cible.firstChild);
    API.ReactDOM.render(
      e(PanneauCharge, { type: "scene", id: m[1] }), hote);
  }

  if (API.Event && API.Event.addEventListener) {
    API.Event.addEventListener("stash:location", () =>
      setTimeout(greffeScene, 120));
  }
  setTimeout(greffeScene, 600);
})();
