"""Epistemická vrstva — Core Semantics 0.1, § 1.3 podkladu a § 4, § 6.

**Hranice, kterou tenhle modul hlídá.** Objektová vrstva se ptá na
vyplývání; epistemická na *doložitelnost*. Kleeneho tabulky z § 4 platí
**jen pro kombinaci už spočtených verdiktů**, nikdy pro objektové spojky.
Proto tu není žádná funkce, která by brala formuli se spojkou a
vyhodnocovala ji — bere se seznam atomů, každý se zeptá zvlášť a teprve
verdikty se kombinují.

Odtud plyne i to, proč „Je citron zelenina, nebo není?" vrací `U`:
`K φ ∨ K ¬φ` není `φ ∨ ¬φ`. Tertium non datur je pravda o modelech, ne
o tom, co víme, a systém se na modely takhle nikdy neptá.

Otevřený svět (I‑11) se promítá do každé výčtové odpovědi: extenze je
dolní odhad, dokud nepadne `complete(g)`. Bez UNA (§ 1.2 podkladu) se
navíc počítají třídy ekvivalence, ne id.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Sequence

from .ast import (
    Atom,
    Comparator,
    Group,
    P_MEMBER,
    Proof,
    QueryResult,
    QueryStatus,
    Sort,
    Term,
    Value,
    group_diff,
    measure_of,
    member_of,
    node_key,
)
from .engine import Engine

#: Uspořádání pro silnou Kleeneho logiku: konjunkce je minimum, disjunkce
#: maximum. `CONFLICT` v něm NENÍ — není to pravdivostní hodnota (§ 4).
_ORDER: dict[QueryStatus, int] = {
    QueryStatus.PROVEN_FALSE: 0,
    QueryStatus.UNKNOWN: 1,
    QueryStatus.PROVEN_TRUE: 2,
}


class EpistemicError(RuntimeError):
    """Dotaz, na který se v tomhle fragmentu nedá poctivě odpovědět."""


# --------------------------------------------------------------------------
# Kombinace verdiktů (§ 4)
# --------------------------------------------------------------------------


def combine(statuses: Sequence[QueryStatus], *, conjunction: bool) -> QueryStatus:
    """Silná Kleeneho kombinace nad UŽ SPOČTENÝMI verdikty.

    `CONFLICT` se nekombinuje — propaguje se jako stav dotazu, protože
    operand, o kterém se odvodí `p` i `p̄`, nemá žádnou pravdivostní
    hodnotu, kterou by šlo do tabulky dosadit.
    """
    if not statuses:
        raise EpistemicError("kombinace prázdného seznamu verdiktů")
    if any(s is QueryStatus.CONFLICT for s in statuses):
        return QueryStatus.CONFLICT
    picker = min if conjunction else max
    return picker(statuses, key=lambda s: _ORDER[s])


# --------------------------------------------------------------------------
# K / U nad jedním atomem
# --------------------------------------------------------------------------


def known(engine: Engine, atom: Atom) -> bool:
    """`K φ` — je doloženo, že φ."""
    return engine.ask(atom).status is QueryStatus.PROVEN_TRUE


def known_false(engine: Engine, atom: Atom) -> bool:
    """`K φ̄` — je doloženo, že ne-φ."""
    return engine.ask(atom).status is QueryStatus.PROVEN_FALSE


def unknown(engine: Engine, atom: Atom) -> bool:
    """`U φ` — ani jedno."""
    return engine.ask(atom).status is QueryStatus.UNKNOWN


# --------------------------------------------------------------------------
# Složené otázky (§ 6.2 zadání)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CompositeResult:
    """Verdikt složené otázky + dílčí verdikty.

    Dílčí část je POVINNÁ: „Je citron ovoce a obsahuje vitamíny?" s `A` a
    `U` musí odpovědět „jistě vím: je ovoce; nevím: vitamíny" — holé
    `NEVÍM` by zahodilo známou půlku (§ 6.2 zadání).
    """

    status: QueryStatus
    parts: tuple[tuple[Atom, QueryResult], ...]

    def certain(self) -> tuple[Atom, ...]:
        return tuple(a for a, r in self.parts if r.status is QueryStatus.PROVEN_TRUE)

    def missing(self) -> tuple[Atom, ...]:
        return tuple(a for a, r in self.parts if r.status is QueryStatus.UNKNOWN)


def _evaluate(engine: Engine, atoms: Iterable[Atom]) -> tuple[tuple[Atom, QueryResult], ...]:
    return tuple((a, engine.ask(a)) for a in atoms)


def query_conjunction(engine: Engine, atoms: Sequence[Atom]) -> CompositeResult:
    parts = _evaluate(engine, atoms)
    return CompositeResult(
        combine([r.status for _, r in parts], conjunction=True), parts
    )


def query_disjunction(engine: Engine, atoms: Sequence[Atom]) -> CompositeResult:
    parts = _evaluate(engine, atoms)
    return CompositeResult(
        combine([r.status for _, r in parts], conjunction=False), parts
    )


@dataclass(frozen=True, slots=True)
class AltResult:
    """Alternativní otázka — odpověď NENÍ ano/ne, ale vybraný člen."""

    status: QueryStatus
    chosen: Atom | None
    parts: tuple[tuple[Atom, QueryResult], ...]


def query_alt(engine: Engine, atoms: Sequence[Atom]) -> AltResult:
    """`alt{φ1, …, φn}` — „Je citron ovoce, nebo zelenina?"

    Je to **explicitně epistemická** operace: ptá se, který člen je
    DOLOŽENÝ, ne který je pravdivý. Objektová disjunkce by na tutéž otázku
    odpověděla `A` bez svědka, protože `φ ∨ ¬φ` platí v každém modelu —
    a to je přesně ta odpověď, kterou člověk nechce.

    Právě jeden doložený ⇒ odpověz jím. Víc než jeden ⇒ hlásit nesoulad.
    Žádný ⇒ `U`, nebo `N`, jsou-li všechny členy vyvrácené.
    """
    parts = _evaluate(engine, atoms)
    if not parts:
        raise EpistemicError("alternativní otázka bez členů")
    if any(r.status is QueryStatus.CONFLICT for _, r in parts):
        return AltResult(QueryStatus.CONFLICT, None, parts)
    true_members = [a for a, r in parts if r.status is QueryStatus.PROVEN_TRUE]
    if len(true_members) == 1:
        return AltResult(QueryStatus.PROVEN_TRUE, true_members[0], parts)
    if len(true_members) > 1:
        # Dvě vzájemné alternativy doložené současně — báze si odporuje
        # v tom, na co se člověk ptal. Hlásit, ne vybrat (§ 6.2 zadání).
        return AltResult(QueryStatus.CONFLICT, None, parts)
    if all(r.status is QueryStatus.PROVEN_FALSE for _, r in parts):
        return AltResult(QueryStatus.PROVEN_FALSE, None, parts)
    return AltResult(QueryStatus.UNKNOWN, None, parts)


# --------------------------------------------------------------------------
# Extenze, výčet, rozdíl (§ 3.1–3.2, § 6.4 zadání)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Extension:
    """Trojice kategorií, ne dvojice.

    `certain` — členství je doložené.
    `conflicted` — báze si o členství ODPORUJE (odvodí se `p` i `p̄`).
    `uncertain` — zbytek `possible`: prostě se neví.

    Konflikt je vlastní kategorie proto, že „nevím" a „báze si o tom
    odporuje" jsou dva různé stavy a celý návrh stojí na tom, že se
    nezaměňují (§ 6.0, I‑1, I‑3). Kdyby konflikt tiše propadl do
    `uncertain`, žádný renderer už ho z těch dat nevytáhne.
    """

    group: Group
    certain: tuple[Term, ...]
    possible: tuple[Term, ...]
    conflicted: tuple[Term, ...]
    complete: str | None

    @property
    def uncertain(self) -> tuple[Term, ...]:
        decided = {t.id for t in self.certain} | {t.id for t in self.conflicted}
        return tuple(t for t in self.possible if t.id not in decided)

    def caveat(self) -> str:
        """Poctivostní doložka (§ 8). Bez `complete(g)` je výčet dolní odhad.

        Doložka **nesmí tvrdit úplnost, dokud jsou nerozhodnuté prvky** —
        jinak by si jedna odpověď odporovala sama se sebou: „to jsou
        všichni" nad výčtem, který uzavřený není.
        """
        parts: list[str] = []
        if self.conflicted:
            names = ", ".join(t.id for t in self.conflicted)
            parts.append(
                f"U {names} si báze odporuje — je doložené členství "
                f"i jeho popření."
            )
        if not self.certain and not self.possible and self.complete is None:
            parts.append(
                "Neznám ani jednoho člena, takže o dalších kandidátech "
                "netvrdím nic."
            )
        elif self.complete is not None and not self.uncertain and not self.conflicted:
            parts.append(f"To jsou všichni — doloženo výrokem {self.complete}.")
        elif self.complete is not None:
            names = ", ".join(t.id for t in self.uncertain) or "některých prvků"
            parts.append(
                f"Výrok {self.complete} sice tvrdí úplnost, ale u {names} "
                f"členství doložené není — úplnost proto netvrdím."
            )
        elif self.uncertain:
            names = ", ".join(t.id for t in self.uncertain)
            parts.append(f"Znám {len(self.certain)}; u {names} to nevím.")
        else:
            parts.append(
                f"Znám {len(self.certain)}; jestli jsou všichni, nevím."
            )
        return " ".join(parts)


def individuals(engine: Engine) -> tuple[Term, ...]:
    """Jednotliviny, o kterých báze ví. Otevřený svět znamená, že jich může
    být víc — proto každá odpověď postavená na této množině nese doložku."""
    terms = engine.derivation().terms
    return tuple(
        sorted(
            (t for t in terms.values() if t.SORT in (Sort.ENTITY, Sort.RELATION)),
            key=node_key,
        )
    )


def extension(engine: Engine, group: Group) -> Extension:
    """`certain` = doložení členové, `possible` = ti, u kterých členství
    není vyvrácené. Bez UNA se výsledek redukuje na kanonické zástupce
    tříd ekvivalence (§ 1.2 podkladu)."""
    view = engine.kb.view()
    # Kandidáti se zužují na sorty prvků, které ve skupině doloženě jsou.
    # Bez toho by se do výčtu pacientů dostaly reifikované instance vztahů
    # a doložka by lékaři tvrdila „u s0004 nevím, jestli je pacient" —
    # neprůhledné id výroku vydávané za jednotlivinu (§ 8).
    admissible = view.element_sorts(group.id)
    buckets: dict[str, list[Term]] = {"certain": [], "possible": [], "conflicted": []}
    seen: dict[str, set[str]] = {key: set() for key in buckets}

    def collect(key: str, term: Term, canonical: str) -> None:
        if canonical not in seen[key]:
            seen[key].add(canonical)
            buckets[key].append(term)

    # Rychlá cesta. Verdikt `N` ani `CONFLICT` u členství nemůže vzniknout,
    # dokud v odvození není jediný `member̄` a v bázi žádné `complete(g)` —
    # `_match_negative_member` nemá z čeho vyrábět. V takové bázi je každý
    # nečlen `U` a každý doložený člen `A`, takže se nemusí ptát vůbec.
    derivation = engine.derivation()
    assert derivation.index is not None
    has_negatives = bool(
        derivation.by_predicate.get((P_MEMBER, True))
    ) or bool(derivation.index.complete_groups())
    certain_ids = frozenset(view.known_members(group.id))

    for term in individuals(engine):
        if term.SORT not in admissible:
            continue
        canonical = view.canonical(term.id)
        if not has_negatives:
            status = (
                QueryStatus.PROVEN_TRUE
                if canonical in certain_ids
                else QueryStatus.UNKNOWN
            )
        else:
            status = engine.ask(member_of(term, group)).status
        if status is QueryStatus.PROVEN_FALSE:
            continue
        collect("possible", term, canonical)
        if status is QueryStatus.PROVEN_TRUE:
            collect("certain", term, canonical)
        elif status is QueryStatus.CONFLICT:
            collect("conflicted", term, canonical)
    return Extension(
        group=group,
        certain=tuple(buckets["certain"]),
        possible=tuple(buckets["possible"]),
        conflicted=tuple(buckets["conflicted"]),
        complete=view.is_complete(group.id),
    )


def query_enum(engine: Engine, group: Group) -> Extension:
    """„Jaké znáš spisovatele?" — výčet známého, ne tvrzení o existenci."""
    return extension(engine, group)


def query_count(engine: Engine, group: Group) -> tuple[int, str]:
    """„Kolik druhů ovoce znáš?" — mohutnost ZNÁMÉ extenze + doložka.

    Počítají se třídy ekvivalence, ne id: bez UNA se dvě jména můžou
    ukázat jako týž uzel, a dokud to není doloženo, zůstávají dvě.
    """
    ext = extension(engine, group)
    return len(ext.certain), ext.caveat()


@dataclass(frozen=True, slots=True)
class DiffResult:
    """`A DIFF B` v otevřeném světě.

    Pole odpovídají § 3.2 a **dvěma různým účelům**:

    * `certain` = `certain(A) \\ possible(B)` — o prvku je doloženo, že
      v `B` není. Formule ze specifikace.
    * `possible` = `possible(A) \\ certain(B)` — druhá formule ze
      specifikace. Bez ní není `DIFF` skladatelný podle § 3.0: zanoří‑li
      se do jiného termu, chybí mu druhá polovina dvojice.
    * `uncertain` = `certain(A) ∩ possible(B) \\ certain(B) \\ conflicted(B)`
      — **užší** než `possible` a nese jiné sdělení: „o tomhle prvku vím,
      že je v `A`, a jen nevím, jestli je i v `B`". To je to, co se
      renderuje v § 6.4 („Z těch, které znám: Hrabal — nevím o něm, že je
      básník").
    * `conflicted` — báze si o členství odporuje; není to nevědomost.
    """

    left: Group
    right: Group
    certain: tuple[Term, ...]
    possible: tuple[Term, ...]
    uncertain: tuple[Term, ...]
    conflicted: tuple[Term, ...]

    def caveat(self) -> str:
        parts: list[str] = []
        if self.conflicted:
            names = ", ".join(t.id for t in self.conflicted)
            parts.append(
                f"U {names} si báze o členství ve skupině "
                f"{self.right.id!r} odporuje."
            )
        if self.uncertain:
            names = ", ".join(t.id for t in self.uncertain)
            parts.append(
                f"U {names} nevím, jestli do skupiny {self.right.id!r} patří — "
                f"tvrdím jen, že to nevím, ne že nepatří."
            )
        return " ".join(parts)


def query_diff(engine: Engine, left: Group, right: Group) -> DiffResult:
    """Zařazení se **neodvozuje z `possible(B)`**, ale ptá se na každý prvek
    `certain(A)` zvlášť.

    Důvod: kandidáti se ve výčtu zužují na sorty doložených členů, takže
    prázdné `possible(B)` znamená „nikdo nekandidoval", ne „nikdo tam
    není". Číst z toho `certain = certain(A) \\ possible(B)` by u skupiny
    bez známých členů vyrobilo tvrzení „prokazatelně nepatří" z pouhé
    nevědomosti — přesně to, co I‑21 zakazuje.
    """
    a = extension(engine, left)
    b = extension(engine, right)
    difference = group_diff(left, right)
    certain: list[Term] = []
    uncertain: list[Term] = []
    conflicted: list[Term] = []
    for term in a.certain:
        # Zařazení do rozdílu má JEDNU definici — termovou algebru § 5.2.1.
        # Kdyby si `query_diff` držel vlastní kritérium, rozešly by se dvě
        # cesty k témuž a jedna by časem začala odpovídat jinak.
        if engine.ask(member_of(term, difference)).status is (
            QueryStatus.PROVEN_TRUE
        ):
            certain.append(term)
            continue
        status = engine.ask(member_of(term, right)).status
        if status is QueryStatus.CONFLICT:
            conflicted.append(term)
        elif status is QueryStatus.UNKNOWN:
            uncertain.append(term)
    seen = {t.id for t in conflicted}
    conflicted.extend(t for t in a.conflicted if t.id not in seen)
    certain_b = {t.id for t in b.certain}
    return DiffResult(
        left=left,
        right=right,
        certain=tuple(certain),
        possible=tuple(t for t in a.possible if t.id not in certain_b),
        uncertain=tuple(uncertain),
        conflicted=tuple(conflicted),
    )


# --------------------------------------------------------------------------
# Mez veličiny (§ 6)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BoundResult:
    status: QueryStatus
    comparator: Comparator
    value: Value | None
    proof: Proof | None


#: Komparátory, které mez zdola/shora vůbec definují.
_UPPER = (Comparator.LE, Comparator.LT)
_LOWER = (Comparator.GE, Comparator.GT)


def query_bound(
    engine: Engine,
    subject: Term,
    quantity: str,
    comparator: Comparator = Comparator.LE,
) -> BoundResult:
    """„Jak rychle může jezdit auto po dálnici?" — odpovědí je MEZ, ne verdikt.

    Dobrá definovanost stojí na tom, že **v1 nemá aritmetiku** (§ 6): žádné
    pravidlo neumí vyrobit hodnotu, která v bázi není, takže odvoditelné
    meze jsou podmnožinou konečné množiny literálů a infimum se degraduje
    na minimum nad konečnou množinou.

    Ze stejného důvodu se neporovnává napříč jednotkami — převod by byl
    aritmetika. Dvě jednotky téže veličiny jsou proto hlášená chyba, ne
    tichý výběr jedné z nich.
    """
    if comparator not in (*_UPPER, *_LOWER):
        raise EpistemicError(
            f"komparátor {comparator.value!r} nedefinuje mez; mez dávají "
            f"jen {[c.value for c in (*_UPPER, *_LOWER)]}"
        )
    literals = [
        t
        for t in engine.derivation().terms.values()
        if isinstance(t, Value) and t.quantity == quantity
    ]
    units = {t.unit for t in literals}
    if len(units) > 1:
        raise EpistemicError(
            f"veličina {quantity!r} má v bázi jednotky {sorted(units)}; "
            f"převod jednotek je aritmetika, tedy mimo v1"
        )

    supported: list[tuple[Decimal, Value, Proof]] = []
    for literal in sorted(literals, key=node_key):
        result = engine.ask(measure_of(subject, comparator, literal))
        if result.status is QueryStatus.PROVEN_TRUE and result.proof is not None:
            supported.append((literal.magnitude, literal, result.proof))
    if not supported:
        return BoundResult(QueryStatus.UNKNOWN, comparator, None, None)
    picker = min if comparator in _UPPER else max
    _, value, proof = picker(supported, key=lambda item: item[0])
    return BoundResult(QueryStatus.PROVEN_TRUE, comparator, value, proof)
