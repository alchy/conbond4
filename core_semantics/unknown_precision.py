"""Proč padlo `U` — A‑27.

Systém umí říct `U` a `GapFinder` umí říct, co k důkazu chybělo. Co se
dosud nikde neměřilo, je **jestli to `U` bylo na místě**.

Je to jediná díra v měření, která má tenhle tvar: všechny ostatní
metriky (§ 10) měří, co systém UDĚLAL — kolik tahů, kolik oprav, kolik
znovupoužitých vzorů. Žádná neměří, co udělat MOHL a neudělal. Systém,
který je přehnaně opatrný, má přitom skvělou přesnost a je prakticky
k ničemu, a dnes by se to nepoznalo.

**MĚŘÍ SE DŮVOD, NE POČET.** Tenhle modul nikdy nedává pokyn odpovídat
víc. `U` je legitimní verdikt — otevřený svět bez UNA znamená, že
o většině věcí opravdu nic nevíme — a snižovat počet `U` hádáním by bylo
horší než neměřit nic. Proto tu není žádné skóre k minimalizaci a být
nemá: číslo, které jde vylepšit, se dřív nebo později vylepšovat začne.

**Nic se nedomýšlí.** Rozklad se skládá výhradně z toho, co `GapFinder`
skutečně vrátil, a z toho, co v bázi doopravdy leží. Metrika, která by
si sama odvozovala, co „mělo jít dokázat", by měřila vlastní domněnku.

Jedna z kategorií je **VADA, ne nález**: `RECALL_FAILURE` znamená, že
tvrzení v bázi JE a systém ho přesto nenašel. Přesně to byla G‑3 —
`attach(subset(auto, A AND B))` se uložil, index tu hranu měl a přímá
otázka vrátila `U`. Tahle metrika by ho odhalila sama, a to je důvod,
proč vznikla.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Sequence

from .ast import Atom, QueryStatus
from .gaps import GapFinder

if TYPE_CHECKING:  # pragma: no cover — jen pro typy
    from .engine import Engine


class UnknownReason(Enum):
    """Proč odpověď vyšla `U`. Pořadí je pořadím ZÁVAŽNOSTI, ne abecedy."""

    #: **VADA.** Výrok v bázi je a systém ho nenašel. Není to neúplnost
    #: odvozování — neúplná sada zákonů je přiznaná mez a dá `U` právem.
    #: Tohle je selhání PAMĚTI: odpověď „nevím" na tvrzení, které někdo
    #: řekl a které leží zapsané.
    RECALL_FAILURE = "v bázi to je, ale nenašlo se"
    #: Cesta k důkazu vedla přes identitu, o které si báze protiřečí
    #: (M‑1). `U` je tu správně, ale příčina NENÍ nedostatek důkazu —
    #: je to spor, který má rozhodnout člověk.
    DISPUTED_IDENTITY = "přes spornou identitu nic nevede"
    #: Hledání mělo cestu a chyběl na ní článek. Legitimní `U` a zároveň
    #: nejlepší kandidát na učení: `GapFinder` ty články jmenuje.
    MISSING_LINK = "chybí článek, který hledání pojmenovalo"
    #: Hledání se zastavilo na mezi hloubky. `U` tu může být opatrnost,
    #: ne nevědomost — a je poctivé to nemíchat s ostatními.
    DEPTH_LIMIT = "hledání se zastavilo na mezi hloubky"
    #: NĚKDO TO ŘEKL a nezapsalo se to *(W‑55)*. `U` je tu správně —
    #: nikdo to nepotvrdil, takže se to netvrdí — ale míchat to s `U`,
    #: o kterém nepadlo ani slovo, by zakrylo právě ten rozdíl, kvůli
    #: kterému tahle kategorie vznikla: na tohle `U` jde odpovědět
    #: JEDNÍM TAHEM, a systém i ví, kterým.
    STATED_UNDECIDED = "řeklo se to, ale čeká to na potvrzení"
    #: O věci nikdo nic neřekl a nic k ní nevede. Nejčistší `U`, jaké
    #: v otevřeném světě existuje.
    NOT_STATED = "nikdo to neřekl a neplyne to"


@dataclass(frozen=True, slots=True)
class Diagnosis:
    """Jedno `U` i s tím, proč padlo."""

    query: Atom
    reason: UnknownReason
    detail: tuple[str, ...] = ()

    @property
    def is_defect(self) -> bool:
        return self.reason is UnknownReason.RECALL_FAILURE

    def render(self) -> str:
        return f"U {self.query} — {self.reason.value}"


def _stated(engine: "Engine", query: Atom) -> tuple[str, ...]:
    """Id výroků, které v bázi LEŽÍ a odpovídají dotazu doslova.

    Porovnává se **rovnost formulí**, ne odvoditelnost. Cokoli volnějšího
    by z metriky udělalo druhý evaluátor — a ten by měl vlastní chyby,
    o kterých by nikdo nevěděl. Doslovná shoda stačí: přesně na ní padla
    G‑3.
    """
    return tuple(
        statement.id
        for statement in engine.kb.active()
        if isinstance(statement.formula, Atom) and statement.formula == query
    )


def diagnose(
    engine: "Engine", query: Atom, *, undecided: Sequence[Atom] = ()
) -> Diagnosis | None:
    """Proč tenhle dotaz vyšel `U` — nebo `None`, když nevyšel.

    Vrací se `None`, a ne nějaké „v pořádku": dotaz s verdiktem `A`, `N`
    nebo `CONFLICT` do rozkladu `U` nepatří vůbec a míchat ho tam by
    ředilo právě to, co se měří.
    """
    if engine.ask(query).status is not QueryStatus.UNKNOWN:
        return None

    stated = _stated(engine, query)
    if stated:
        return Diagnosis(query, UnknownReason.RECALL_FAILURE, stated)

    report = GapFinder(engine).explain(query, undecided=undecided)
    if report.disputed:
        return Diagnosis(
            query,
            UnknownReason.DISPUTED_IDENTITY,
            tuple(f"{a} × {b}" for a, b in report.disputed),
        )
    # Podcíl, který je JEN SÁM DOTAZ, žádný článek nejmenuje: hledání
    # nemělo kudy jít a vrátilo, na co se ptalo. Brát to jako „chybí
    # článek" by tu kategorii vyprázdnilo — spadlo by do ní každé `U`
    # a nešlo by z ní poznat, na co se dá odpovědět.
    named = tuple(
        str(goal.atom) for goal in report.open_goals if goal.atom != query
    )
    if named:
        return Diagnosis(query, UnknownReason.MISSING_LINK, named)
    if report.exhausted:
        return Diagnosis(query, UnknownReason.DEPTH_LIMIT)
    # AŽ TADY, a schválně za `MISSING_LINK`: „řeklo se to" je jmenovka
    # důvodu, ne cesty. Kdyby stálo výš, přebilo by nález, který hledání
    # opravdu udělalo, značkou, kterou mu někdo dal zvenčí.
    if query in list(undecided):
        return Diagnosis(query, UnknownReason.STATED_UNDECIDED)
    return Diagnosis(query, UnknownReason.NOT_STATED)


def survey(
    engine: "Engine",
    queries: Sequence[Atom],
    *,
    undecided: Sequence[Atom] = (),
) -> tuple[Diagnosis, ...]:
    """Rozklad `U` přes sadu dotazů. Dotazy s jiným verdiktem vypadnou."""
    found = (diagnose(engine, query, undecided=undecided) for query in queries)
    return tuple(item for item in found if item is not None)


def defects(diagnoses: Sequence[Diagnosis]) -> tuple[Diagnosis, ...]:
    """Jen ta `U`, která jsou VADA. Zbytek jsou nálezy, ne chyby."""
    return tuple(item for item in diagnoses if item.is_defect)


def render(diagnoses: Sequence[Diagnosis]) -> tuple[str, ...]:
    """Rozklad pro člověka. **Bez součtu ke srovnávání** — jsou to
    kategorie, ne body."""
    if not diagnoses:
        return ("žádné `U` k rozboru",)
    lines: list[str] = []
    for reason in UnknownReason:
        matching = [item for item in diagnoses if item.reason is reason]
        if not matching:
            continue
        mark = "VADA " if reason is UnknownReason.RECALL_FAILURE else ""
        lines.append(f"{mark}{reason.value}: {len(matching)}")
        lines.extend(f"    {item.query}" for item in matching)
    return tuple(lines)
