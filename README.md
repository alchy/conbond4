# conBond4 — Core Semantics 0.1 Engine

Implementace formálního jádra podle [docs/CORE-SEMANTICS-0.1.md](docs/CORE-SEMANTICS-0.1.md).

## Stav

| Fáze | Modul | Stav |
|---|---|---|
| F0.1 | `core_semantics/ast.py` | hotovo — sorty, termy, kvantifikátor na roli, pravidla, důkaz |
| F0.2 | `core_semantics/closures.py` | hotovo — `subset*`, `contains*`, `within*`, `same_as*`, `member*` |
| F0.2 | `core_semantics/storage.py` | hotovo — `attach`/`revoke`/`inspect`, `ResolvedGraphView`, expanze `disjoint` |
| F0.3 | `core_semantics/engine.py` | hotovo — shoda `⪯` s D1–D4, least fixed point, `member̄*`, verdikty A/N/U/CONFLICT |
| F0.4 | `core_semantics/epistemics.py` | hotovo — `K`/`U`, Kleeneho kombinace, `alt`, `DIFF`, `enum`/`count`, `bound` |
| F0.4 | `core_semantics/presenter.py` | hotovo — `XAIPresenter`, šablony v profilu, export JSON/Markdown |
| F0.6 | `core_semantics/session.py` | hotovo — strukturované tahy, žurnál, deterministický replay, `awaiting_rule_confirmation` |
| F0.5 | `closed_context` (§ 12) | čeká — **potřebuje vlastní specifikaci dřív než kód**: lokální doména, UNA uvnitř kontextu, kardinality, enumerace modelů |
| — | `GapFinder` | čeká — top-down SLD pro „Proč nevíš?" |
| — | doména AML | čeká — omezená podoba (prahy nad literály v bázi, řetězce pevné hloubky) |

## Akceptační domény

`core_semantics/tests/test_examples_*.py` — celé úlohy od vstupu k odpovědi
(§ 10 zadání). Každá má fázi A (neúplný vstup → `UNKNOWN`) a fázi B
(doplněný můstek → verdikt s důkazem).

| Doména | Co ověřuje |
|---|---|
| 🚗 doprava | `bound` query, distribuce `∀` dolů, `∃`-role nejmenuje svědka |
| 🍦 zmrzlina | skládání dvou `∃`-relací; zákaz výběru svědka z řetězu |
| 🏡 Petrovice | unifikace přes dva fakty; pruning důkazu; zákaz naučené rekurze |
| 🩺 léky | kaskáda `subset*` do silné negace; OWA u pacienta bez anamnézy |

## Spuštění testů

```bash
python -m pytest -q
```

Dialogy se vypisují na konzoli — transkript každého akceptačního dialogu
se ukáže vždy, i když test projde:

```bash
python -m pytest core_semantics/tests/test_dialogue_console.py -s
```

## Tři věty, na kterých jádro stojí

1. **Doména je otevřená, UNA neplatí.** Extenze group je dolní odhad;
   `complete(g)` je jediný způsob, jak z něj udělat rovnost.
2. **Individua vytváří jen `attach` z lidského vstupu.** Inference nikdy —
   `∃` na roli nezakládá uzel. Odtud konečnost pevného bodu.
3. **Objektová vrstva se ptá na vyplývání, epistemická na doložitelnost.**
   Přirozeně-jazyková spojka v otázce jde vždy do epistemické vrstvy.
