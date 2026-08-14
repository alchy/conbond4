"""AST jádra — Core Semantics 0.1, § 1 (sorty a typování) a § 2 (syntaxe).

Konvence (rozhodnutí J., § 3.7 zadání): identifikátory a klíčová slova
anglicky, lexikální materiál z dialogu jako data ("auto", "spisovatel"),
komentáře česky.

Pozn. k názvu modulu: `core_semantics.ast` stíní stdlib `ast` jen uvnitř
balíčku při relativním importu. Python 3 nemá implicitní relativní
importy, takže `import ast` kdekoli jinde stále dává stdlib.

Všechny termy jsou imutabilní a hashovatelné — `Atom.roles` je frozenset,
což vyžaduje hashovatelné `RoleTerm`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Sequence, Union, cast

# --------------------------------------------------------------------------
# Chybové stavy `attach` (§ 9)
# --------------------------------------------------------------------------


class AttachError(Exception):
    """Základ chybových stavů zápisu. Selhání `attach` je tah dialogu,
    ne výjimka v obvyklém smyslu — proto samostatná hierarchie."""


class SortError(AttachError):
    """§ 9 `TypeError` — role dostala jiný sort, porovnání napříč osami.
    Pojmenováno `SortError`, aby nestínilo builtin `TypeError`."""


class UnquantifiedRole(AttachError):
    """§ 9 `Unquantified` — group ve filleru bez kvantifikátoru.
    Vede na doptání, nikdy na default (§ 2.6 podkladu)."""


class DepthExceeded(AttachError):
    """§ 9 `DepthExceeded` — hloubka vnoření vztahů nad parametr gramatiky.
    Vyhazuje se až ve fázi 3, kdy `RoleTerm.target` unese instanci vztahu."""


class UnsafeRule(AttachError):
    """§ 9 `UnsafeRule` — porušení § 5.4/1–7 (bezpečnost proměnných,
    funkční symboly, přepsání jádrového predikátu)."""


class CycleDetected(AttachError):
    """§ 9 `CycleDetected` — cyklus v dependency grafu naučených pravidel.
    Jádrové uzávěry jsou listy grafu, ne uzly (§ 5.1)."""


# --------------------------------------------------------------------------
# Sorty (§ 1)
# --------------------------------------------------------------------------


class Sort(Enum):
    ENTITY = "E"
    GROUP = "G"
    RELATION = "R"
    PLACE = "P"
    TIME = "T"
    VALUE = "V"
    LABEL = "L"
    VARIABLE = "X"


@dataclass(frozen=True, slots=True)
class Entity:
    """Anonymní uzel identity (I‑9). `id` je neprůhledné; čitelná přípona
    (`e_filip`) je pohodlí bez významu."""

    id: str
    SORT: ClassVar[Sort] = Sort.ENTITY


@dataclass(frozen=True, slots=True)
class Group:
    """Množina termů. Typ vztahu je `Group` svých instancí, takže na něj
    platí táž algebra (§ 1: `RelationType` není samostatný sort)."""

    id: str
    SORT: ClassVar[Sort] = Sort.GROUP


@dataclass(frozen=True, slots=True)
class RelationInstance:
    """Reifikovaná instance vztahu — uzel s rolemi (§ 3.4 zadání)."""

    id: str
    SORT: ClassVar[Sort] = Sort.RELATION


@dataclass(frozen=True, slots=True)
class Place:
    """Vlastní sort, NE podtyp Group. „Praha ⊆ Česko" není podmnožina, ale
    `contains*` — § 1 to odděluje záměrně (hranice, překryvy, části území
    nejsou množinové operace)."""

    id: str
    SORT: ClassVar[Sort] = Sort.PLACE


@dataclass(frozen=True, slots=True)
class Interval:
    """Bod/interval na časové ose. Vnitřek specialisty „Chronos" je mimo F0."""

    id: str
    SORT: ClassVar[Sort] = Sort.TIME


@dataclass(frozen=True, slots=True)
class Value:
    """Hodnota veličiny. Jednotka je jméno osy — porovnávat lze jen na téže
    ose (§ 1), aritmetika je mimo v1 a je to podmínka evaluovatelnosti
    `bound` (§ 6)."""

    id: str
    quantity: str
    magnitude: Decimal
    unit: str
    SORT: ClassVar[Sort] = Sort.VALUE

    def __post_init__(self) -> None:
        # `bound` je minimum nad KONEČNOU množinou literálů v bázi (§ 6) a
        # determinismus (I‑4) stojí na přesném porovnání — float sem nepatří.
        # Převod je bezpodmínečný a idempotentní: volající smí předat int
        # nebo str, anotace přesto popisuje uložený typ.
        object.__setattr__(self, "magnitude", Decimal(str(self.magnitude)))


@dataclass(frozen=True, slots=True)
class Label:
    """Neprůhledný název — jméno role, jméno veličiny. Implikován § 2, kde
    `role(r, name, t)` má jméno v argumentové pozici, takže pro něj musí
    existovat term."""

    id: str
    SORT: ClassVar[Sort] = Sort.LABEL


@dataclass(frozen=True, slots=True)
class Variable:
    """Proměnná v pravidle. V AST master promptu chyběla, ale bez ní nejde
    zapsat expanze `disjoint` na dvě pravidla se silnou negací (§ 5.3)."""

    id: str
    expects: Sort | None = None
    SORT: ClassVar[Sort] = Sort.VARIABLE


@dataclass(frozen=True, slots=True)
class GroupAnd:
    """Průnik. Operandy jsou **kanonizované**: setříděné a bez duplicit,
    a vnořený `AND` se zploští.

    Bez kanonizace by `A AND B` a `B AND A` byly dva různé termy téhož
    významu — uložily by se dvakrát, rozbila by se deduplikace faktů
    i kanonický důkaz (§ 7). `Atom.roles` je navíc `frozenset`, takže term
    musí být hashovatelný.
    """

    operands: tuple["GroupTerm", ...]
    SORT: ClassVar[Sort] = Sort.GROUP

    @property
    def id(self) -> str:
        return "(" + " AND ".join(operand.id for operand in self.operands) + ")"


@dataclass(frozen=True, slots=True)
class GroupOr:
    """Sjednocení. Kanonizované stejně jako `GroupAnd`."""

    operands: tuple["GroupTerm", ...]
    SORT: ClassVar[Sort] = Sort.GROUP

    @property
    def id(self) -> str:
        return "(" + " OR ".join(operand.id for operand in self.operands) + ")"


@dataclass(frozen=True, slots=True)
class GroupDiff:
    """Rozdíl. **Nekanonizuje se** — `A DIFF B` a `B DIFF A` jsou různé
    významy, protože rozdíl není komutativní."""

    left: "GroupTerm"
    right: "GroupTerm"
    SORT: ClassVar[Sort] = Sort.GROUP

    @property
    def id(self) -> str:
        return f"({self.left.id} DIFF {self.right.id})"


Term = Union[
    Entity,
    Group,
    GroupAnd,
    GroupOr,
    GroupDiff,
    RelationInstance,
    Place,
    Interval,
    Value,
    Label,
    Variable,
]

# Konstruktory strukturních predikátů berou i proměnnou — pravidla se bez ní
# nedají napsat a `_require_sort` ji za běhu propouští záměrně.
GroupTerm = Union[Group, GroupAnd, GroupOr, GroupDiff, Variable]
PlaceTerm = Union[Place, Variable]
IntervalTerm = Union[Interval, Variable]

#: Algebraické konstruktory — uzavřená sada (§ 2).
ALGEBRAIC = (GroupAnd, GroupOr, GroupDiff)


def _canonical_operands(
    operands: Sequence[GroupTerm], kind: type
) -> tuple[GroupTerm, ...]:
    """Zploští vnořený týž operátor, odstraní duplicity, setřídí."""
    flat: list[GroupTerm] = []
    for operand in operands:
        if isinstance(operand, (GroupAnd, GroupOr)) and type(operand) is kind:
            flat.extend(operand.operands)
        else:
            flat.append(operand)
    unique = {operand.id: operand for operand in flat}
    return tuple(sorted(unique.values(), key=node_key))


def group_and(*operands: GroupTerm) -> GroupTerm:
    canonical = _canonical_operands(operands, GroupAnd)
    if not canonical:
        raise SortError("prázdný průnik")
    return canonical[0] if len(canonical) == 1 else GroupAnd(canonical)


def group_or(*operands: GroupTerm) -> GroupTerm:
    canonical = _canonical_operands(operands, GroupOr)
    if not canonical:
        raise SortError("prázdné sjednocení")
    return canonical[0] if len(canonical) == 1 else GroupOr(canonical)


def group_diff(left: GroupTerm, right: GroupTerm) -> GroupDiff:
    return GroupDiff(left=left, right=right)


def as_group_terms(parts: Sequence[Term], where: str) -> tuple[GroupTerm, ...]:
    """Ověří, že termy smějí stát jako operandy algebraického výrazu.

    Kontrola je za běhu, ne jen v anotaci: proměnná uvnitř `A DIFF V` se
    může navázat na cokoli, a průnik entity se skupinou není typová chyba
    jen podle anotace — je to nesmysl, který musí spadnout hlasitě."""
    checked: list[GroupTerm] = []
    for part in parts:
        if part.SORT is not Sort.GROUP and part.SORT is not Sort.VARIABLE:
            raise SortError(
                f"{where}: operand {part.id!r} je {part.SORT.name}, "
                f"algebraický výraz snese jen skupiny"
            )
        checked.append(cast(GroupTerm, part))
    return tuple(checked)

#: Sorty, které smí (a musí) nést kvantifikátor na roli.
_QUANTIFIABLE: frozenset[Sort] = frozenset({Sort.GROUP, Sort.VARIABLE})


def node_key(t: Term) -> tuple[str, str]:
    """Kanonické pořadí termů — determinismus (I‑4, I‑22)."""
    return (t.SORT.value, t.id)


def subterms(t: Term) -> tuple[Term, ...]:
    """Přímé podtermy algebraického termu; u atomického prázdná n-tice."""
    if isinstance(t, (GroupAnd, GroupOr)):
        return t.operands
    if isinstance(t, GroupDiff):
        return (t.left, t.right)
    return ()


def term_variables(t: Term) -> frozenset[Variable]:
    """Proměnné včetně těch uvnitř algebraických termů.

    Bez rekurze by `is_ground()` prohlásilo `group("a") DIFF V` za
    uzemněný fakt a proměnná by se tiše dostala do báze."""
    if isinstance(t, Variable):
        return frozenset({t})
    found: frozenset[Variable] = frozenset()
    for part in subterms(t):
        found |= term_variables(part)
    return found


# --------------------------------------------------------------------------
# Kvantifikátor na roli (§ 2, rozhodnutí 2 podkladu)
# --------------------------------------------------------------------------


class Quantifier(Enum):
    FOR_ALL = "∀"
    EXISTS = "∃"
    SELF = "·"  # o group-uzlu samotném


@dataclass(frozen=True, slots=True)
class RoleTerm:
    name: str
    target: Term
    quantifier: Quantifier | None = None

    def __post_init__(self) -> None:
        quantifiable = self.target.SORT in _QUANTIFIABLE
        # Proměnná, která se má navázat na group, potřebuje kvantifikátor
        # stejně jako group sama — jinak by `role_q(r, via, ∃, P)` prošlo bez něj.
        expects_group = getattr(self.target, "expects", None) is Sort.GROUP
        if (self.target.SORT is Sort.GROUP or expects_group) and self.quantifier is None:
            raise UnquantifiedRole(
                f"role {self.name!r} nese group {self.target.id!r} bez "
                f"kvantifikátoru; jádro nemá default — patří sem doptání"
            )
        if not quantifiable and self.quantifier is not None:
            raise SortError(
                f"role {self.name!r} nese {self.target.SORT.name} "
                f"{self.target.id!r}; kvantifikátor smí nést jen Group/Variable"
            )

    def __str__(self) -> str:
        q = self.quantifier.value if self.quantifier else ""
        return f"{self.name}:{q}{self.target.id}"


def role(name: str, target: Term, quantifier: Quantifier | None = None) -> RoleTerm:
    return RoleTerm(name=name, target=target, quantifier=quantifier)


# --------------------------------------------------------------------------
# Atom (§ 2)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Atom:
    """Atomická formule. `is_negated=True` je SILNÁ negace: `p̄` je
    samostatný predikát, ne klasické ¬ (§ 4). Báze tím zůstane definitní.

    Role jsou `frozenset`, tedy NEUSPOŘÁDANÉ. Je to bezpečné jen proto, že
    čtení `∃∀` je zakázané (§ 5.2) — rozsah je určen druhem kvantifikátoru,
    ne pozicí role. Kdyby se ta mez někdy uvolnila, MUSÍ se z toho stát
    `tuple`, jinak se ztratí rozlišení `∀x∃y` × `∃y∀x`.
    """

    predicate: str
    roles: frozenset[RoleTerm]
    is_negated: bool = False

    def __post_init__(self) -> None:
        names = [r.name for r in self.roles]
        if len(names) != len(set(names)):
            raise SortError(
                f"atom {self.predicate!r} má roli vícekrát: "
                f"{sorted(n for n in names if names.count(n) > 1)}"
            )

    # -- přístup -----------------------------------------------------------

    def get_role(self, name: str) -> RoleTerm | None:
        for r in self.roles:
            if r.name == name:
                return r
        return None

    def canonical_roles(self) -> tuple[RoleTerm, ...]:
        return tuple(sorted(self.roles, key=lambda r: r.name))

    def complement(self) -> "Atom":
        """`p` ↔ `p̄`. Koherenční constraint `p ∧ p̄ → ⊥` (§ 4) se kontroluje
        proti tomuto tvaru."""
        return Atom(self.predicate, self.roles, not self.is_negated)

    def variables(self) -> frozenset[Variable]:
        found: frozenset[Variable] = frozenset()
        for r in self.roles:
            found |= term_variables(r.target)
        return found

    def is_ground(self) -> bool:
        return not self.variables()

    @property
    def signature(self) -> tuple[str, bool]:
        """Predikát se znaménkem. Silná negace tvoří SAMOSTATNÝ predikát,
        takže `member` a `member̄` jsou různé predikáty — jinak by expanze
        `disjoint` vypadala jako smyčka."""
        return (self.predicate, self.is_negated)

    def dependency_key(self) -> tuple[str, bool, tuple[tuple[str, str], ...]]:
        """Uzel dependency grafu (§ 5.4/5, § 5.4/6).

        Jemnější než `signature`: konstantní fillery rolí jsou součástí uzlu,
        proměnné se zobrazí na `*`. Bez toho splývají VŠECHNY expanze
        `disjoint` do jediného uzlu `member̄` a řetěz neslučitelností
        („co není stroj, není ani robot") vypadá jako smyčka, i když
        rekurzivní není.

        **`*` NENÍ divoká karta — je to jen značka.** Klíč sám o sobě žádnou
        bezpečnostní vlastnost nemá: `p(out:*)` a `p(out:a)` jsou dva různé
        klíče, takže rovnost klíčů by mezi nimi hranu nenašla a rekurze by
        prošla validací. Bezpečná strana vzniká až tím, že se hrany staví
        UNIFIKACÍ klíčů (`storage._unifies`), kde se `*` snoubí s libovolnou
        konstantou. Kdo použije tenhle klíč jinak než přes unifikaci, dostane
        under-aproximaci.
        """
        fillers = tuple(
            (
                r.name,
                "*" if isinstance(r.target, Variable) else r.target.id,
            )
            for r in self.canonical_roles()
        )
        return (self.predicate, self.is_negated, fillers)

    def __str__(self) -> str:
        bar = "¬" if self.is_negated else ""
        body = ", ".join(str(r) for r in self.canonical_roles())
        return f"{bar}{self.predicate}({body})"


def atom(predicate: str, *roles: RoleTerm, negated: bool = False) -> Atom:
    return Atom(predicate=predicate, roles=frozenset(roles), is_negated=negated)


# --------------------------------------------------------------------------
# Strukturní predikáty — jeden termový jazyk, žádný zvláštní případ (§ 3.0
# zadání). Group v nich vystupuje jako objekt, tedy `SELF`.
# --------------------------------------------------------------------------

P_MEMBER = "member"
P_SUBSET = "subset"
P_CONTAINS = "contains"
P_WITHIN = "within"
P_BEFORE = "before"
P_SAME_AS = "same_as"
P_COMPLETE = "complete"
P_NAME = "name"
P_DISJOINT = "disjoint"

# Dekompozice reifikovaného vztahu (§ 2). Kvantifikátor je zakódovaný
# v NÁZVU predikátu, ne v argumentu: menu je uzavřené (I‑15), takže čtyři
# predikáty jsou přesnější než jeden s proměnným kvantifikátorem.
P_ROLE = "role"  # konkrétní filler
P_ROLE_FORALL = "role_forall"
P_ROLE_EXISTS = "role_exists"
P_ROLE_SELF = "role_self"

ROLE_PREDICATES: frozenset[str] = frozenset(
    {P_ROLE, P_ROLE_FORALL, P_ROLE_EXISTS, P_ROLE_SELF}
)


class Comparator(Enum):
    """Uzavřené menu (§ 2, I‑15). Dialog učí, KTERÉ slovo spouští KTERÝ
    komparátor — nikdy nevyrábí nový."""

    LT = "<"
    LE = "<="
    EQ = "="
    GE = ">="
    GT = ">"
    NE = "!="


MEASURE_PREDICATES: frozenset[str] = frozenset(
    f"measure_{c.name.lower()}" for c in Comparator
)

#: Predikáty, které obsluhují jádrové uzávěry (§ 5.1). Naučené pravidlo je
#: nesmí mít v hlavě v nenegovaném tvaru — jinak by učení přepsalo jádro (I‑16).
#:
#: **Kritérium členství, ne seznam.** Do množiny patří právě ten predikát,
#: jehož pravdivost MĚNÍ UZÁVĚR nebo UZAVÍRÁ SVĚT — tedy každý, který
#: `ClosureIndex` čte ze základních faktů při stavbě indexu. Důvod je
#: mechanický a platí na obě strany:
#:
#: * index se staví jen nad základními fakty, takže atom odvozený pravidlem
#:   se do uzávěru nikdy nedostane. Pravidlo by se přijalo, atom odvodil,
#:   dotaz vrátil `A` — a účinek by se zahodil. Táž báze by pak odpovídala
#:   dvěma způsoby podle toho, kterými dveřmi se do ní psalo.
#: * uzavření světa je **řečový akt člověka** („a to je všechno"), ne závěr
#:   učení. Odvodit úplnost z neúplných dat je přesně ten předpoklad
#:   uzavřeného světa, který § 0 zakazuje.
#:
#: Zároveň to drží stratifikaci: jsou to predikáty stratu 0, takže se
#: z těla pravidla nestává hrana závislosti. Cyklus se tím zakrýt nemůže —
#: žádný z nich se neodvozuje, takže žádný není hlavou.
KERNEL_PREDICATES: frozenset[str] = frozenset(
    {
        P_MEMBER,
        P_SUBSET,
        P_CONTAINS,
        P_WITHIN,
        P_BEFORE,
        P_SAME_AS,
        P_DISJOINT,
        P_COMPLETE,
        # `name` sem přibylo, až když ho začala číst kanonizace jmen
        # (N‑2): jméno určuje, KTERÝ uzel zmínka trefí, takže mění uzávěr
        # stejně jako `same_as`. Odvodit si jméno pravidlem by znamenalo
        # vyrobit si kotvu identity — a přesně to má I‑16 zakázané.
        # Nepřidával jsem to dopředu; vynutilo si to kritérium samo.
        P_NAME,
    }
)

#: Role, jejichž fillér je MÍSTO, a role, jejichž fillér je ČAS (§ 3.6).
#: Je to slovník JÁDRA, ne domněnka o slově: `kam` je prostorová role, ať
#: za ní stojí cokoli. Bydlí to tady, protože z toho žije kaskáda i V3 —
#: dvě kopie téhož seznamu by se rozešly a poznalo by se to až sortovou
#: chybou o vrstvu níž.
#:
#: **Fillér těchhle rolí NENESE kvantifikátor.** `RoleTerm` ho připouští
#: jen u `Group`/`Variable`; místo ani čas se nekvantifikují, mluví se
#: o nich samotných.
PLACE_ROLES: tuple[str, ...] = ("kam", "kde", "odkud", "kudy")
TIME_ROLES: tuple[str, ...] = ("kdy",)
UNQUANTIFIED_ROLES: frozenset[str] = frozenset(PLACE_ROLES + TIME_ROLES)

#: Predikáty, které naučené pravidlo NESMÍ mít v nenegované hlavě (I‑16).
#:
#: **Je to širší množina než `KERNEL_PREDICATES`, a ten rozdíl je celý
#: smysl téhle konstanty.** `KERNEL_PREDICATES` odpovídá na otázku „na co
#: se ptá uzávěrový index" a nese proto ještě dvě další věci: směrování
#: v evaluátoru a stratum 0. Zákaz v hlavě je ale otázka TŘETÍ a širší:
#:
#: > Co se nesmí odvozovat? To, co MĚNÍ UZÁVĚR, **a k tomu jazyk, kterým
#: > se fakty zapisují.**
#:
#: Role jsou ten jazyk. `role(R, kdo, W)` vzniká reifikací při `attach`,
#: tedy z toho, co člověk řekl; pravidlo s `role` v hlavě by NAROUBOVALO
#: roli na cizí, člověkem zapsanou instanci — uložený fakt by se nezměnil,
#: změnilo by se, jak se čte. To není učení nového tvrzení, to je tichý
#: přepis staršího.
#:
#: **Jen na hlavu.** Reifikace v TĚLECH pravidel zůstává povolená a stojí
#: na ní domény dálnice i zmrzliny — pravidlo smí roli ČÍST, nesmí ji
#: vyrábět.
PROTECTED_HEADS: frozenset[str] = KERNEL_PREDICATES | ROLE_PREDICATES

#: Predikáty s pevným významem. Fakt s jiným predikátem je VZTAH a engine
#: ho reifikuje na uzel s rolemi.
RESERVED_PREDICATES: frozenset[str] = (
    KERNEL_PREDICATES
    | ROLE_PREDICATES
    | MEASURE_PREDICATES
    | {P_COMPLETE, P_NAME, P_DISJOINT}
)


def _require_sort(name: str, term: Term, expected: Sort) -> None:
    """Sorty se kontrolují ZA BĚHU, ne jen v anotacích. Bez toho by typová
    bezpečnost § 1 stála a padala s tím, jestli někdo spustil type checker."""
    if term.SORT is Sort.VARIABLE:
        return
    if term.SORT is not expected:
        raise SortError(
            f"{name}: očekává se {expected.name}, dostal "
            f"{term.SORT.name} {term.id!r}"
        )


def _object_quantifier(term: Term) -> Quantifier | None:
    """Ve strukturních predikátech vystupuje group jako OBJEKT — tedy `·`."""
    return Quantifier.SELF if term.SORT in _QUANTIFIABLE else None


def member_of(elem: Term, group: GroupTerm, *, negated: bool = False) -> Atom:
    _require_sort("member/group", group, Sort.GROUP)
    return atom(
        P_MEMBER,
        role("elem", elem, _object_quantifier(elem) if elem.SORT is Sort.GROUP else None),
        role("group", group, Quantifier.SELF),
        negated=negated,
    )


def subset_of(sub: GroupTerm, sup: GroupTerm, *, negated: bool = False) -> Atom:
    _require_sort("subset/sub", sub, Sort.GROUP)
    _require_sort("subset/sup", sup, Sort.GROUP)
    return atom(
        P_SUBSET,
        role("sub", sub, Quantifier.SELF),
        role("sup", sup, Quantifier.SELF),
        negated=negated,
    )


def contains_of(whole: PlaceTerm, part: PlaceTerm) -> Atom:
    _require_sort("contains/whole", whole, Sort.PLACE)
    _require_sort("contains/part", part, Sort.PLACE)
    return atom(P_CONTAINS, role("whole", whole), role("part", part))


def within_of(whole: IntervalTerm, part: IntervalTerm) -> Atom:
    """Obsažení intervalů. Týž tvar jako `contains`, ale jiný sort a jiný
    graf — čas a prostor se nesmí mísit (§ 1)."""
    _require_sort("within/whole", whole, Sort.TIME)
    _require_sort("within/part", part, Sort.TIME)
    return atom(P_WITHIN, role("whole", whole), role("part", part))


def before_of(earlier: IntervalTerm, later: IntervalTerm) -> Atom:
    """Uspořádání na časové ose (§ 3.6). Striktně nad sortem `Time`.

    „Po" je `before` obráceně, „během" je `within`; „překrývá" by
    vyžadoval intervaly s koncovými body, a to je jiná, větší věc."""
    _require_sort("before/earlier", earlier, Sort.TIME)
    _require_sort("before/later", later, Sort.TIME)
    return atom(P_BEFORE, role("earlier", earlier), role("later", later))


def measure_of(
    subject: Term,
    comparator: Comparator,
    value: Term,
    *,
    negated: bool = False,
) -> Atom:
    """Mez veličiny na ději. Komparátor je v názvu predikátu, protože menu
    je uzavřené — žádné pravidlo nemůže vyrobit sedmý."""
    return atom(
        f"measure_{comparator.name.lower()}",
        role("of", subject),
        role("limit", value),
        negated=negated,
    )


def role_atom(instance: Term, name: str, filler: RoleTerm) -> Atom:
    """Dekompozice jedné role reifikovaného vztahu do datalogového atomu."""
    predicate = {
        None: P_ROLE,
        Quantifier.FOR_ALL: P_ROLE_FORALL,
        Quantifier.EXISTS: P_ROLE_EXISTS,
        Quantifier.SELF: P_ROLE_SELF,
    }[filler.quantifier]
    # Ve dekomponovaném tvaru je kvantifikátor v predikátu, takže samotný
    # filler vystupuje jako objekt — tedy `SELF`, je-li to group.
    inner = Quantifier.SELF if filler.target.SORT in _QUANTIFIABLE else None
    return atom(
        predicate,
        role("of", instance),
        role("name", Label(name)),
        role("filler", filler.target, inner),
    )


def same_as_of(left: Term, right: Term) -> Atom:
    """Scelení dvou uzlů TÉHOŽ sortu.

    Musí jít i nad `Group`: „Hrabal"/„Bohumil Hrabal" a „člověk"/„lidé" jsou
    týž problém a jedna jmenná vrstva ho řeší pro entity i třídy (§ 3.5
    zadání). Proto se pro group operandy doplní `·`, jinak by konstruktor
    spadl na chybějícím kvantifikátoru.
    """
    if left.SORT is not right.SORT:
        raise SortError(
            f"same_as: {left.SORT.name} {left.id!r} a {right.SORT.name} "
            f"{right.id!r} nejsou téhož sortu; identita napříč sorty by "
            f"slila třídy ekvivalence"
        )
    return atom(
        P_SAME_AS,
        role("left", left, _object_quantifier(left)),
        role("right", right, _object_quantifier(right)),
    )


def disjoint_of(a: GroupTerm, b: GroupTerm) -> Atom:
    """Oddělenost dvou skupin — **osmý sourozenec, ne výjimka**.

    Do dneška byl `disjoint` jediná jádrová relace bez konstruktoru, a ta
    chybějící zábrana dělala špatnou cestu dosažitelnou: `P_DISJOINT` je
    ve veřejném rozhraní, `attach` je veřejný zapisovač, takže se dal
    ručně sestavený marker zapsat — a báze pak tvrdila oddělenost, ze
    které se nic neodvodilo.

    **Konstruktor sám o sobě nestačí a nemá to předstírat.** Zapsat
    oddělenost do báze znamená vygenerovat i dvojici pravidel se silnou
    negací (§ 5.3), a to jsou tři výroky, ne jeden — proto to dělá
    `KnowledgeBase.add_disjoint` a `attach` holý marker odmítne. Tenhle
    konstruktor je pro **otázku** („jsou kočky a psi oddělení?") a pro
    tělo pravidla.
    """
    _require_sort("disjoint/a", a, Sort.GROUP)
    _require_sort("disjoint/b", b, Sort.GROUP)
    return atom(
        P_DISJOINT,
        role("a", a, Quantifier.SELF),
        role("b", b, Quantifier.SELF),
    )


def complete_of(group: GroupTerm) -> Atom:
    """`complete(g)` — jediný způsob, jak z dolního odhadu udělat rovnost
    `K(g) = M(g)` (§ 3.1). Bez něj je výčet vždy jen „znám tyto"."""
    return atom(P_COMPLETE, role("group", group, Quantifier.SELF))


# --------------------------------------------------------------------------
# Pravidla (§ 5.4)
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    head: Atom
    body: tuple[Atom, ...]

    def __post_init__(self) -> None:
        if not self.body:
            raise UnsafeRule(f"pravidlo {self.id!r} má prázdné tělo")
        # § 5.4/1 — vazba se počítá jen z POZITIVNÍHO těla. Vázat proměnnou
        # negovaným literálem znamená rozsah přes celou otevřenou doménu `D`
        # (§ 0/1), tedy i přes individua, která báze nepojmenovává.
        positive = [a for a in self.body if not a.is_negated]
        bound: frozenset[Variable] = frozenset()
        for a in positive:
            bound |= a.variables()
        unbound = self.head.variables() - bound
        if unbound:
            raise UnsafeRule(
                f"pravidlo {self.id!r}: proměnné {sorted(v.id for v in unbound)} "
                f"v hlavě nejsou vázané v pozitivním těle (§ 5.4/1)"
            )
        # § 5.4/7 — žádná volná proměnná pod negací (floundering).
        floundering: frozenset[Variable] = frozenset()
        for a in self.body:
            if a.is_negated:
                floundering |= a.variables()
        floundering -= bound
        if floundering:
            raise UnsafeRule(
                f"pravidlo {self.id!r}: proměnné "
                f"{sorted(v.id for v in floundering)} jsou volné pod negací "
                f"(§ 5.4/7)"
            )
        if self.head.predicate in PROTECTED_HEADS and not self.head.is_negated:
            raise UnsafeRule(
                f"pravidlo {self.id!r} by přepsalo chráněný predikát "
                f"{self.head.predicate!r}; učení mění program, nikdy jazyk (I‑16)"
            )

    def variables(self) -> frozenset[Variable]:
        return self.head.variables().union(*(a.variables() for a in self.body))

    def __str__(self) -> str:
        return f"{self.id}: {self.head} <- " + " AND ".join(str(a) for a in self.body)


Formula = Union[Atom, Rule]


# --------------------------------------------------------------------------
# Důkaz a mezera (§ 7)
# --------------------------------------------------------------------------


class ProofKind(Enum):
    FACT = "fact"
    RULE = "rule"
    CLOSURE = "closure"
    DISTRIBUTE = "distribute"
    WITNESS = "witness"
    CONSTRAINT = "constraint"
    COUNTERMODEL = "countermodel"


@dataclass(frozen=True, slots=True)
class Proof:
    """Strukturovaný důkaz. Master prompt měl `proof_tree: list[str]`, ale
    nad seznamem stringů nejde spočítat minimalitu ani kanonický výběr
    (§ 7, T31) — proto struktura a `render()` jako výstup pro člověka."""

    kind: ProofKind
    ref: str
    premises: tuple["Proof", ...] = ()

    def leaves(self) -> frozenset[str]:
        """Id výroků, na kterých důkaz stojí — fakta I pravidla.

        `rule` NENÍ list ve smyslu konce rekurze: pravidlo se do množiny
        započítá a zároveň se sestoupí do jeho premis. Jinak by vysvětlení
        („seznam id výroků, které se použily", § 3.7/1) zamlčelo fakta pod
        pravidlem a minimalita by se počítala nad neúplnou množinou.
        """
        out = (
            frozenset({self.ref})
            if self.kind in (ProofKind.FACT, ProofKind.RULE)
            else frozenset()
        )
        for p in self.premises:
            out |= p.leaves()
        return out

    def canonical_key(self) -> tuple[int, tuple[str, ...], int]:
        """§ 7, třístupňový klíč — schváleno 14. 8. 2026.

        1. **počet listů** — princip minimálního vysvětlení. Bez něj vyhrával
           důkaz s lexikograficky nižšími id bez ohledu na délku, takže
           „citron je citron a citron je ovoce" porazilo „citron je ovoce",
           pokud se přímý fakt připojil později. Právnicky platné, lidsky
           absurdní.
        2. **uspořádaná n-tice id listů** — rozsekne shodu v počtu.
        3. **velikost stromu** — poslední pojistka.

        Determinismus (I‑13) zůstává: je to zjemnění metrické funkce, ne
        zavedení nondeterminismu — žádný stupeň nezávisí na pořadí průchodu.
        """
        return (len(self.leaves()), tuple(sorted(self.leaves())), self.size())

    def size(self) -> int:
        return 1 + sum(p.size() for p in self.premises)

    def render(self, indent: int = 0) -> list[str]:
        pad = "  " * indent
        head = f"{pad}{self.kind.value}({self.ref})"
        out = [head]
        for p in self.premises:
            out.extend(p.render(indent + 1))
        return out

    def __str__(self) -> str:
        return "\n".join(self.render())


def select_canonical(proofs: list[Proof]) -> Proof | None:
    """Deterministická volba mezi několika důkazy téhož verdiktu.

    Dvě fáze podle § 7: nejdřív se zahodí NEMINIMÁLNÍ důkazy (ty, jejichž
    množina listů je vlastní nadmnožinou jiné — taková obsahuje krok, bez
    kterého by se verdikt odvodil taky), teprve pak rozhoduje lexikografické
    pořadí listů. Na tom stojí `normalize_proof(ref) == normalize_proof(prod)`.
    """
    if not proofs:
        return None
    leaves = [p.leaves() for p in proofs]
    minimal = [
        p
        for i, p in enumerate(proofs)
        if not any(leaves[j] < leaves[i] for j in range(len(proofs)) if j != i)
    ]
    return min(minimal or proofs, key=Proof.canonical_key)


@dataclass(frozen=True, slots=True)
class Gap:
    """Otevřené podcíle pro verdikt `UNKNOWN`. `Proof` a `Gap` jsou
    oddělené typy — „důkaz s chybějící premisou" by rozbil minimalitu
    (§ 7)."""

    open_goals: tuple[Atom, ...] = ()

    def render(self) -> list[str]:
        return [f"chybí vědět: {a}" for a in self.open_goals]


# --------------------------------------------------------------------------
# Výsledek dotazu (§ 4)
# --------------------------------------------------------------------------


class QueryStatus(Enum):
    PROVEN_TRUE = "A"  # K φ
    PROVEN_FALSE = "N"  # K φ̄
    UNKNOWN = "U"
    CONFLICT = "CONFLICT"  # stav dotazu, NE čtvrtá pravdivostní hodnota (§ 4)


@dataclass(frozen=True, slots=True)
class QueryResult:
    status: QueryStatus
    proof: Proof | None = None
    conflict: tuple[Proof, Proof] | None = None
    gap: Gap | None = None
    payload: Any = None

    @property
    def proof_tree(self) -> list[str]:
        """Kompatibilita s API master promptu."""
        if self.proof is not None:
            return self.proof.render()
        if self.conflict is not None:
            pos, neg = self.conflict
            return ["p:", *pos.render(1), "p̄:", *neg.render(1)]
        if self.gap is not None:
            return self.gap.render()
        return []

    def __str__(self) -> str:
        return f"{self.status.value}" + (
            f" [{', '.join(sorted(self.proof.leaves()))}]" if self.proof else ""
        )
