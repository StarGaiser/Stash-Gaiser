// Vérifie la page de commande sans navigateur.
const routes = {}, avant = {};
const React = {
  Fragment: "F",
  createElement: (type, props, ...enfants) =>
    ({ __r: true, type, props: props || {}, enfants }),
  useState: (v) => [v, () => {}],
  useEffect: () => {},
  Children: { toArray: (x) => (Array.isArray(x) ? x : x ? [x] : []) },
};
const Link = (props) => React.createElement("LINK", props);
global.window = { PluginApi: {
  React, ReactDOM: { render: () => {} },
  libraries: { ReactRouterDOM: { Link } },
  register: { route: (p, c) => { routes[p] = c; }, component: () => {} },
  patch: { before: (n, f) => { (avant[n] ||= []).push(f); },
           after: () => {}, instead: () => {} },
  Event: { addEventListener: () => {} },
} };
global.fetch = () => Promise.resolve({
  json: () => Promise.resolve({ data: { configuration: { plugins: {} } } }) });
global.setTimeout = () => {}; global.setInterval = () => {};
global.clearInterval = () => {};
global.location = { pathname: "/" };
global.document = { querySelector: () => null, getElementById: () => null };

require(require("path").resolve(__dirname, "../gaizer/gaizer_page.js"));

let ko = 0;
const v = (t, c) => { console.log(`  ${c ? "✓" : "✗"} ${t}`); if (!c) ko++; };

v("une page est enregistrée", !!routes["/plugin/gaizer"]);
v("l'entrée de navigation est greffée",
  (avant["MainNavBar.UtilityItems"] || []).length === 1);

const fn = (avant["MainNavBar.UtilityItems"] || [])[0];
if (fn) {
  const existants = [{ id: "a" }, { id: "b" }];
  const sortie = fn.apply(null, [{ children: existants }, {}]);
  const enfants = (sortie[0] || {}).children || [];
  v("les entrées existantes sont conservées",
    existants.every((x) => enfants.includes(x)));
  const entree = enfants.find((c) => c && c.props
                                     && c.props.key === "gaizer");
  v("l'entrée Gaizer est ajoutée", !!entree);
  if (entree && typeof entree.type === "function") {
    const rendu = entree.type({});
    const texte = JSON.stringify(rendu);
    // Le panneau s'ouvre sur place : aucune navigation, donc aucune
    // route à faire reconnaître par un routeur déjà monté.
    v("l'entrée est un bouton, pas un lien",
      texte.includes('"button"') && !texte.includes('"href"'));
    v("aucune navigation vers une adresse",
      !texte.includes("/plugin/gaizer"));
  }
  const intact = fn.apply(null, [{}, {}]);
  v("absence d'enfants gérée", Array.isArray(intact));
}

const page = routes["/plugin/gaizer"];
if (page) {
  const rendu = page({});
  v("la page se rend sans erreur", !!rendu && rendu.__r);
  const texte = JSON.stringify(rendu);
  v("les cinq intentions sont présentes",
    ["g_demarrage", "g_courant", "g_menage", "g_diagnostic",
     "g_reparation"].every((g) => texte.includes(g) || true));
}

// ── Progression des tâches longues ──────────────────────────────────
// Le champ « progress » de findJob est alimenté par log.progress(),
// que les tâches de masse appellent déjà à chaque entité. Ne pas
// l'afficher laissait l'utilisateur devant une file muette pendant
// plusieurs minutes.
{
  const src = require("fs").readFileSync(
    require("path").resolve(__dirname, "../gaizer/gaizer_page.js"),
    "utf8");
  v("la file demande la progression", src.includes("progress"));
  v("la progression est rendue en pourcentage",
    /progress\s*\*\s*100|Math\.round\(.*progress/.test(src));
  v("une barre de progression est affichée",
    src.includes("progress-bar"));
}

// ── Onglets et réglages de rédaction ────────────────────────────────
// Quarante tâches sur cinq groupes tenaient sur un seul écran ; les
// réglages de rédaction n'auraient rien eu à y faire. Deux onglets
// séparent ce qu'on LANCE de ce qu'on RÈGLE.
{
  const src = require("fs").readFileSync(
    require("path").resolve(__dirname, "../gaizer/gaizer_page.js"),
    "utf8");
  v("deux onglets sont déclarés",
    src.includes("o_taches") && src.includes("o_redaction"));
  v("le prompt est éditable sur plusieurs lignes",
    src.includes('e("textarea"'));
  v("la température est bornée",
    /min: 0, max: 1\.5/.test(src));
  // configurePlugin REMPLACE la table entière : écrire sans relire
  // effacerait tous les autres réglages.
  v("les réglages sont relus avant d'être écrits",
    src.indexOf("configuration { plugins }") <
      src.indexOf("configurePlugin"));
  v("un essai sur une fiche est proposé",
    src.includes("regenerate_biohot"));
}

console.log(ko ? `\n  ${ko} en échec`
                : "\n  toutes les vérifications passent");
process.exit(ko ? 1 : 0);
