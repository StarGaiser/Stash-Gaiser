// Reproduit le mécanisme d'application des patches de Stash 0.31.1
// pour vérifier que le plugin respecte le contrat, sans navigateur ni
// serveur.
//
//   before  : a = fn.apply(this, a)         → retourne de NOUVEAUX args
//   after   : i = fn.apply(this, a.concat(i)) → le résultat est en DERNIER
//   instead : fn reçoit les args plus la fonction suivante
const avant = {}, apres = {}, place = {};
const React = {
  Fragment: "FRAGMENT",
  createElement: (type, props, ...enfants) =>
    ({ __react: true, type, props: props || {}, enfants }),
  useState: (v) => [v, () => {}],
  useEffect: () => {},
};
global.window = {
  PluginApi: {
    React, ReactDOM: { render: () => {} },
    patch: {
      before: (nom, fn) => { (avant[nom] ||= []).push(fn); },
      after: (nom, fn) => { (apres[nom] ||= []).push(fn); },
      instead: (nom, fn) => { (place[nom] ||= []).push(fn); },
    },
    Event: { addEventListener: () => {} },
  },
  location: { pathname: "/performers/608" },
};
global.document = { querySelector: () => null, getElementById: () => null,
                    createElement: () => ({}) };
global.fetch = () => Promise.resolve({
  json: () => Promise.resolve({ data: { configuration: { plugins: {} } } }) });
global.setTimeout = () => {};
global.location = window.location;

require(require("path").resolve(__dirname, "../gaizer/gaizer.js"));

let erreurs = 0;
const verifier = (libelle, condition) => {
  console.log(`  ${condition ? "✓" : "✗"} ${libelle}`);
  if (!condition) erreurs += 1;
};

// ── Insertion du panneau parmi les enfants du bloc de détails ────────
const fnAvant = (avant["PerformerDetailsPanel.DetailGroup"] || [])[0];
verifier("greffe enregistrée sur DetailGroup", !!fnAvant);

if (fnAvant) {
  const enfants = [
    { props: { id: "age" } }, { props: { id: "country" } },
    { props: { id: "details" } }, { props: { id: "tags" } },
    { props: { values: { perso: "x" } } },   // champs personnalisés
  ];
  const props = { performer: { id: 608, name: "Test" }, children: enfants };
  const sortie = fnAvant.apply(null, [props, {}]);

  verifier("« before » retourne bien un tableau d'arguments",
           Array.isArray(sortie));
  const neufs = (sortie[0] || {}).children || [];
  verifier("aucun enfant d'origine perdu",
           enfants.every((c) => neufs.includes(c)));
  const iPanneau = neufs.findIndex((c) => c && c.props &&
                                          c.props.key === "gaizer");
  const iDetails = neufs.findIndex((c) => c && c.props &&
                                          c.props.id === "details");
  verifier("panneau inséré", iPanneau >= 0);
  verifier("panneau APRÈS les données de Stash", iPanneau > 1);
  const iPerso = neufs.findIndex((c) => c && c.props &&
                                        c.props.values !== undefined);
  verifier("panneau APRÈS la biographie",
           iPanneau >= 0 && iDetails >= 0 && iPanneau > iDetails);
  verifier("panneau AVANT les champs personnalisés",
           iPanneau >= 0 && iPerso >= 0 && iPanneau < iPerso);

  // Une fiche sans identifiant ne doit pas être touchée.
  const intact = fnAvant.apply(null, [{ children: enfants }, {}]);
  verifier("fiche sans identifiant laissée intacte",
           (intact[0] || {}).children === enfants);
}

// ── Masquage des champs du plugin ───────────────────────────────────
const fnPlace = (place["CustomFields"] || [])[0];
verifier("greffe enregistrée sur CustomFields", !!fnPlace);

if (fnPlace) {
  let recu = null;
  const suivant = function (p) { recu = p; return "RENDU"; };
  fnPlace.apply(null, [{ values: { enrich_sources: "x", bio_hot: "y",
                                   perso: "z" } }, {}, suivant]);
  verifier("champs du plugin retirés de l'affichage",
           recu && !("enrich_sources" in recu.values) &&
           !("bio_hot" in recu.values));
  verifier("champ de l'utilisateur conservé",
           recu && recu.values.perso === "z");

  const vide = fnPlace.apply(null,
    [{ values: { enrich_sources: "x" } }, {}, suivant]);
  verifier("bloc masqué s'il ne reste rien", vide === null);

  recu = null;
  fnPlace.apply(null, [{ values: { perso: "z" } }, {}, suivant]);
  verifier("aucune modification si rien n'est du plugin",
           recu && recu.values.perso === "z");
}



// ── Le bouton attend la fin de la tâche ─────────────────────────────
// Une tâche de plugin est asynchrone : la mutation rend un numéro de
// travail, pas un résultat. Sans attendre, la coche s'affichait avant
// toute écriture et le panneau montrait l'état d'avant — d'où
// l'impression que le bouton ne servait à rien.
const src = require("fs").readFileSync(
  require("path").resolve(__dirname, "../gaizer/gaizer.js"), "utf8");

verifier("le statut du travail est interrogé", src.includes("findJob"));
verifier("les états terminaux sont reconnus",
         ["FINISHED", "FAILED", "CANCELLED"].every((e) => src.includes(e)));
verifier("l'attente est bornée dans le temps",
         /maxSecondes|limite\s*=\s*Date\.now/.test(src));
verifier("le panneau est rechargé après l'action",
         src.includes("props.recharger") && src.includes("setTour"));
verifier("aucune action ne lance sans attendre",
         !/[^t]\brunMode\(/.test(src.replace(/const runMode =[\s\S]*?d\.runPluginTask\);/, "")
                                   .replace("await runMode(mode, extra)", "")));


// ── Chaque bouton est complet et honnête ────────────────────────────
{
  const m = src.match(/const L = (\{[\s\S]*?\n  \});/);
  const L = eval("(" + m[1] + ")");
  const cles = ["enrichir", "accepter", "pas_doublon", "fusionner",
                "verifie", "restaurer"];
  const langues = ["en", "fr", "de", "es", "it", "pt", "nl"];

  verifier("chaque bouton est traduit dans les sept langues",
           cles.every((c) => L[c] && langues.every((lg) => L[c][lg])));
  verifier("chaque bouton porte une explication au survol",
           cles.every((c) => L["aide_" + c]));

  // Un libellé doit annoncer l'EFFET, pas le moyen : « Chercher les
  // sources » décrivait la consultation, pas le fait que la fiche est
  // complétée — d'où l'impression que le bouton ne produisait rien.
  verifier("les actions destructives annoncent leur effet",
           /supprime|deletes|löscht|elimina|verwijdert/i.test(L.fusionner.fr
             + L.fusionner.en + L.fusionner.de));
  verifier("l'action d'annulation dit qu'elle défait",
           /annuler|undo|rückgängig|deshacer/i.test(L.restaurer.fr
             + L.restaurer.en));

  // Les modes appelés par les boutons doivent exister dans le registre.
  const modes = [...src.matchAll(/runModeEtAttendre\("(\w+)"/g)]
    .map((x) => x[1]);
  verifier("onze actions branchées sur un mode",
           new Set(modes).size >= 11);
}

// ── L'attente en file est distinguée de l'exécution ─────────────────
// Stash n'exécute qu'UNE tâche de plugin à la fois. Une tâche lancée
// pendant qu'une autre tourne reste en file, parfois plusieurs
// minutes, sans rien faire. Afficher « en cours » dans cet état est
// faux et donne l'impression d'un blocage — c'est ce qui s'est
// produit, et ce que ces contrôles empêchent de revenir.
verifier("l'état READY est distingué de RUNNING",
         src.includes("en_attente") && src.includes("RUNNING"));
verifier("la position dans la file est calculée",
         src.includes("file.findIndex"));
verifier("le bouton annonce l'attente avant l'exécution",
         /setLibelle\(tr\(L, "en_attente"\)\)/.test(src));
verifier("l'attente laisse le temps à la file de se vider",
         src.includes("|| 900"));
verifier("un travail vu tourner puis disparu compte comme fini",
         src.includes('vuEnCours ? "fini"'));
verifier("chaque action transmet son rapporteur d'état",
         [...src.matchAll(/action: async \(\) =>/g)].length === 0);

// ── Compte rendu de ce qui a changé ─────────────────────────────────
// Une tâche annonce « fini » sans dire ce qu'elle a fait : sur une
// fiche déjà complète, une seule valeur change et rien ne le montre.
verifier("la trace de provenance est relue après l'action",
         src.includes("traceDe("));
verifier("les champs sont extraits de la trace",
         src.includes("champsDe("));
verifier("le bouton annonce le nombre de champs complétés",
         /champs_completes|nouveaux\.size/.test(src));
verifier("aucun champ nouveau est distingué d'un échec",
         src.includes("rien_de_neuf"));

console.log(erreurs ? `\n  ${erreurs} vérification(s) en échec`
                    : "\n  toutes les vérifications passent");
process.exit(erreurs ? 1 : 0);
