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
| F0.7 | termová algebra v `ast.py` / `engine.py` | hotovo — `AND` / `OR` / `DIFF` jako termy, § 5.2.1 |
| F1.1 | `core_semantics/oracle.py` | hotovo — fasáda vnějšího orákula (§ 5.1), kandidátní čtení, keš s proveniencí |
| F1.1 | `core_semantics/lexicon.py` | hotovo — program `LEX` (§ 3.7), uzavřené menu operací, vzory s proveniencí a statusem |
| F1.2 | `core_semantics/cascade.py` | hotovo — V2 kaskáda čtení (§ 5.2): generátor, tvrdé filtry, konzistence s bází, naučené vzory, doptání |
| F1.2 | `Session.utter()` | hotovo — česká věta na vstupu: orákulum → kaskáda → strukturovaný tah; do žurnálu jde struktura, ne text |
| F1.2 | V3 rozřešení zmínek | čeká — § 5.3; aktivace grafu (§ 4) neexistuje, takže jedno patro kaskády bude chybět |
| F1.3 | zlaté transkripty | čeká — fixovaný rozbor, aby upgrade modelu nezpůsobil tichý drift |
| F0.5 | `closed_context` (§ 12) | čeká — **potřebuje vlastní specifikaci dřív než kód**: lokální doména, UNA uvnitř kontextu, kardinality, enumerace modelů |
| — | `core_semantics/gaps.py` | hotovo — `GapFinder` (§ 6.8): otevřené podcíle, chybějící článek řetězu, blokující literál pravidla |
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
| 🕐 Petr a čas | `before*` na ose, `contains*` u míst, alternativa nad osou |

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
