# agent-tasks — plán pro agentické sezení nad conBondem4

**K čemu to je.** Na conBondu4 pracuje víc agentů najednou. Tenhle
adresář je jejich zadání: **agent si přečte svůj soubor a hned ví, co
řeší, komu to předává, kdo ho kontroluje a co musí být v předávce**.
Nic z toho se nedomýšlí za běhu.

## Kdo je kdo

| agent | soubor | vlastní | nesmí sáhnout na |
|---|---|---|---|
| **Řídicí** („gazda") | [AGENT-0-RIDICI.md](AGENT-0-RIDICI.md) | zadání, pořadí, rozhodnutí o rozsahu | kód, testy, verdikty |
| **Builder jádra** | [AGENT-1-BUILDER-JADRO.md](AGENT-1-BUILDER-JADRO.md) | `core_semantics/`, `docs/`, testy jádra | `REVIEW.md`, cizí repo |
| **Reviewer** | [AGENT-2-REVIEWER.md](AGENT-2-REVIEWER.md) | `REVIEW.md`, `REVIEW-UTILS.md`, statefile | `core_semantics/`, `tests/`, `cb_utils/` |
| **Builder měřicí vrstvy** | [AGENT-3-BUILDER-UTILS.md](AGENT-3-BUILDER-UTILS.md) | `conbond4-utils/` | `core_semantics/` |

**Repozitáře:** `conbond4` (jádro), `conbond4-utils` (měření),
`conbond4-deps` (služba UDPipe). Každý má vlastní `main` a vlastní
statefile.

## Jak to běží

```
        ┌──────────────────────────────────────────────┐
        │  Řídicí agent — zadá rozsah a pořadí         │
        └───────────────┬──────────────────────────────┘
                        │
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
┌──────────────┐   tah/verdikt     ┌──────────────┐
│  Builder 1   │ ◄───────────────► │  Reviewer    │
│  jádro       │                   │  (poslední   │
└──────────────┘                   │   pojistka)  │
┌──────────────┐   tah/verdikt     │              │
│  Builder 3   │ ◄───────────────► │              │
│  měření      │                   └──────────────┘
└──────────────┘
```

**Tah má v jednu chvíli právě jeden agent.** Kdo tah nemá, **nedělá
nic** — ani „drobnou opravu". Předávka se děje výhradně statefilem
(viz [PROTOKOL.md](PROTOKOL.md)).

## Než cokoli uděláš

1. Přečti si **svůj** soubor výše.
2. Přečti si [PROTOKOL.md](PROTOKOL.md) — formát statefile a předávky.
3. Přečti si [PRAVIDLA.md](PRAVIDLA.md) — pravidla vydobytá ~130 koly
   auditu. **Nejsou to zásady, jsou to popisy pastí, do kterých už
   někdo spadl.**
4. Podívej se do [PODLAHA.md](PODLAHA.md) — čísla, která **nesmí
   klesnout**. Každá předávka je proti nim měřená.

## Co tenhle adresář NENÍ

**Není to specifikace jádra.** Ta je v [`docs/CORE-SEMANTICS-0.1.md`](../docs/CORE-SEMANTICS-0.1.md).
**Není to historie auditu.** Ta je v [`REVIEW.md`](../REVIEW.md).
Tohle je jen **provozní řád**: kdo, s kým, jak a čím to doloží.
