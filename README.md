# Gaizer

> **Metadata enrichment for [Stash](https://github.com/stashapp/stash).**
> Fills in performers, scenes and studios from several sources at once,
> arbitrates disagreements while keeping track of where every value
> came from, detects duplicates and reassembles multi-part films.
> Everything it writes can be undone; nothing is overwritten without an
> explicit decision.

**Topics**: `stash` · `stash-plugin` · `metadata` · `enrichment` ·
`python` · `graphql` · `self-hosted`

*[Version française](README.fr.md)*

---

## What it does differently

Most enrichment tools pick a source and write what it says. Gaizer
queries every source available to your Stash — stash-boxes and every
installed performer scraper — and then has to decide what to do when
they disagree, which is most of the time.

**Every value carries its origin.** A field panel on each performer and
studio page shows what was collected, from how many independent source
families, with a confidence score and a comment explaining it. A value
without a traceable origin is worth less than no value at all.

**Nothing is overwritten.** Empty fields get filled; existing ones are
left alone and the disagreement is recorded. A separate, explicit task
can overrule that — it is the only one that does, and it keeps the old
value so the change can be undone.

**Everything is reversible.** Ten passes of history per entity. *Undo
last pass* restores fields, removes tags and links that were added, and
steps back one pass at a time.

**It says when it doesn't know.** A performer with thin documentation
gets a short entry or none. The language model is instructed to cite
the passage it relied on, and that citation is checked against the
source text before the value is accepted — the only workable guard
against a fabricated quote.

## What it covers

| | |
|---|---|
| **Performers** | biography, birth date, nationality, ethnicity, measurements, career span, images, roles |
| **Scenes** | identification by fingerprint, title, date, studio, cast, tags, synopsis, official covers |
| **Studios** | parent network, website, presentation, logo |
| **Groups** | reassembles films split across several files |
| **Duplicates** | detects and merges performers and studios, never automatically for entries you created |
| **Tags** | measures which ones actually distinguish anything in your collection |

Seven interface languages — English, French, German, Spanish, Italian,
Portuguese, Dutch — and generated text follows the same setting. Left
blank, it follows the language you set in Stash itself.

## Enrichment paths

Gaizer has several ways to learn something about a scene. They differ
in cost, risk and yield, so each is switched on separately — and the
default follows one rule: **whatever guesses or transmits is off**.

| Path | Cost | Default |
|---|---|---|
| Fingerprints and sources | calls to third-party services | on |
| **File path** | none | **on** |
| File name | none, but guesses | **on** |
| Thumbnail watermarks | paid calls, images sent out | off |
| Opening/closing credits | paid calls, images sent out, needs Pillow | off |

The file path is the surprise: a tidy library carries its own
metadata, and reading it costs nothing. On a real collection it filled
more gaps than every other path combined, without a single network
call. It does assume your folders describe what they contain — switch
it off if they don't.

**Order matters.** A title and studio taken from the path give the
scrapers a handle they didn't have; running the scene enrichment
*after* the path pass recovers dates it could not find before.

## Installing

Gaizer is not in the CommunityScripts catalogue yet. Until then:

```bash
cd <your Stash config>/plugins
git clone https://github.com/StarGaiser/Stash-Gaiser.git gaizer
pip install stashapp-tools pyyaml
```

Then **Settings → Plugins → Reload**. A **GZ** button appears in the
navigation bar; it opens the command panel.

Requires Stash 0.25 or later for the interface panels. The enrichment
tasks themselves work on older versions.

## First run

The order matters, and the panel numbers it:

1. **Scenes** — they create the performers and studios that are missing
2. **Performers** — fills what the scenes left empty
3. **Studios**
4. **Suggest tags to exclude** — reports only

Every destructive task offers **Simulate** next to **Run**. Use it. It
tells you exactly what would change without changing anything.

## Language models

Optional. Gaizer works without one — it just won't write presentations
or synopses.

Any OpenAI-compatible provider works, including local ones (Ollama, LM
Studio, llama.cpp, vLLM), and the instructions sent to the model are
translated into your language rather than merely asking for output in
it. A model given French instructions and told to answer in Dutch
drifts back towards French.

## What it is not

**Not a scraper.** It uses the ones you already have, and can tell you
which ones from the catalogue would fit the studios in your collection.

**Not a facial recognition tool.** [Star
Identifier](https://github.com/stashapp/CommunityScripts) does that,
and Gaizer is built to work alongside it rather than replace it.

**Not a magic fix.** On the fields where reference directories disagree
with each other, no arbitration can be better than the sources. What
Gaizer offers there is traceability: you can see the disagreement and
decide.

## How this plugin was written

This plugin was written with the assistance of a large language model,
disclosed here as required by the CommunityScripts guidelines.

- **Human review.** Every change was read and accepted by the
  maintainer before being committed. Nothing was merged unreviewed.
- **Human testing.** Each feature was exercised against a real Stash
  instance and a real library — not only against the test suite.
  Several defects fixed here were found that way, not by the tests.
- **Automated checks.** The suite holds over 1300+tests, written
  before the code they cover. Coverage thresholds, third-party
  linting and documentation checks run on every change.
- **Responsibility.** The maintainer takes full responsibility for
  this code, including licence compliance.

The tests are the honest part of that claim: they are readable, they
state what they expect and why, and several exist because a
plausible-looking piece of code turned out to be wrong.

## Documentation

- [Functional specification](docs/SPECIFICATIONS_FONCTIONNELLES.md) —
  what it does and why, in detail *(French)*
- [Technical specification](docs/SPECIFICATIONS_TECHNIQUES.md) —
  architecture, Stash API pitfalls, measurements *(French)*
- [Coding standards](docs/NORMES_DE_CODAGE.md) — rules that each came
  out of a real problem *(French)*
- [Testing](docs/TESTS.md) — what is covered and what deliberately
  isn't *(French)*

## Licence

AGPL-3.0-or-later, like Stash itself.

Anyone running it as part of a network service must publish their
modifications. Use it, change it, share it — but not behind a closed
door.
