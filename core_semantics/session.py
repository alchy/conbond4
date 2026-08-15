"""Dialogová vrstva — Core Semantics 0.1, § 2 (V0), § 3.7 (`DIA`), § 10.

Dialog není nadstavba nad hotovým jádrem: `DIA` je třetí program vedle
`ONTO` a `LEX` a hlavní metrika projektu — *„kolik tahů dialogu potřebuje,
aby se naučil odpovídat správně"* (§ 10) — je bez téhle vrstvy neměřitelná.

**Tah je STRUKTUROVANÝ, ne surový text.** Parser je vnější orákulum
(§ 5.1) a vrstvy V1–V3 ve F0 nejsou; `Session` proto dostává rovnou
formuli nebo dotaz, a `text` je jen lidský popis pro transkript. Testuje
se, co systém s posloupností tahů udělá a co odpoví — ne jak větu rozebral.

**Můstková pravidla se nevymýšlejí.** Vrátí‑li dotaz `U`, tah smí nabídnout
pravidlo, které s sebou nese jako návrh (`awaiting_rule_confirmation`,
§ 3.7). Generátor návrhů — tedy schopnost odvodit z mezery, JAKÉ pravidlo
chybí — je v F0 mimo rozsah a je to vědomá díra, ne opomenutí: nabídnout
smí jen to, co někdo navrhl.

**Determinismus** (I‑4): „teď" je pořadové číslo tahu, ne čas stroje.
Žádné hodiny, žádná neseedovaná náhoda — `replay(žurnál)` proto dá týž
program i tytéž odpovědi (§ 10).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Sequence

from .ast import (
    Atom,
    AttachError,
    Comparator,
    Entity,
    Formula,
    Group,
    GroupTerm,
    Interval,
    Label,
    Place,
    Sort,
    P_NAME,
    Proof,
    QueryResult,
    Quantifier,
    QueryStatus,
    RoleTerm,
    Rule,
    SortError,
    Term,
    Variable,
    atom,
    role,
    same_as_of,
)
from .cascade import (
    AWAITING_REFERENCE,
    HARD_TIERS,
    QUANTIFIER_OF,
    Candidate,
    Predication,
    Tier,
    Verdict,
    base_consistency_tier,
    cascade,
    has_dropped,
    lexicon_tier,
    lost_question,
    lost_role_tier,
    open_roles_question,
    quantifier_tier,
    as_relation,
    relation_question,
    relation_shape,
    relation_tier,
    role_question,
    role_mapping_tier,
)
from .engine import Engine
from .epistemics import BoundResult, query_bound
from .gaps import GapFinder
from .grounding import BindingType, Grounded, ground, semantic_rejection
from .lexicon import (
    Lexicon,
    Mood,
    Operation,
    StructuralSignature,
    Trigger,
    czech_seed,
)
from .oracle import OracleUnavailable, ParseOracle, Reading, Utterance
from .presenter import DEFAULT_PROFILE, AuditReport, TemplateProfile, XAIPresenter
from .storage import KnowledgeBase


#: Sorty, které jsou POJMENOVANÝ UZEL, a jde je tedy přejmenovat. Algebraický
#: term ani veličina uzel nejsou — jejich id se odvozuje z operandů, takže
#: přejmenovat je zvlášť by vyrobilo id, které neodpovídá vlastnímu obsahu.
_RENAMEABLE: dict[Sort, Callable[[str], Term]] = {
    Sort.ENTITY: Entity,
    Sort.GROUP: Group,
    Sort.PLACE: Place,
    Sort.TIME: Interval,
}


def _rename_node(formula: Atom, old: str, new: str) -> Atom:
    """Týž atom s jiným uzlem v rolích. Sort se zachovává — rozdělení mění
    identitu, ne druh věci."""

    def moved(target: Term) -> Term:
        factory = _RENAMEABLE.get(target.SORT)
        if target.id != old or factory is None:
            return target
        return factory(new)

    return Atom(
        predicate=formula.predicate,
        roles=frozenset(
            RoleTerm(name=r.name, target=moved(r.target), quantifier=r.quantifier)
            for r in formula.roles
        ),
        is_negated=formula.is_negated,
    )


def _apply_quantifier(
    predication: Predication,
    shape: StructuralSignature,
    quantifier: Quantifier | None,
) -> Predication:
    """Zavře role, které čekaly PRÁVĚ NA TENHLE tvar.

    Ne všechny otevřené role — kdyby se zavřely i ty, které čekaly na
    jiný tvar, odpověď na jednu otázku by tiše zodpověděla i druhou.
    """
    return replace(
        predication,
        roles=tuple(
            replace(
                role,
                quantifier=quantifier,
                pending=None,
                awaiting="",
                # ODKUD kvantifikátor je, se zaznamenává i tady. Role
                # zavřená odpovědí by jinak nesla verdikt bez původu —
                # vysvětlení by o naučeném tvaru mlčelo (I‑14) a metrika
                # znovupoužití by ten tah nezapočítala, takže učení by
                # vypadalo neužitečněji, než je.
                source=f"tvar {shape.shape()}",
            )
            if role.pending is not None and role.pending == shape
            else role
            for role in predication.roles
        ),
    )


def _mood_of(text: str) -> Mood:
    """Tah dialogu z povrchového signálu.

    Otazník na konci není rozbor věty, je to interpunkce — a rozlišení
    tvrzení/otázka je právě to, co odděluje objektové `OR` od epistemické
    alternativy (past F‑2). Volající to smí přebít, protože strukturovaný
    vstup tah zná přesně.

    **Od L‑5 na téhle jedné funkci visí, jestli se BÁZE ZMĚNÍ.** Dřív
    vybírala mezi dvěma čteními, teď mezi `attach` a `ask`. Výchozí
    `ASSERTION` je proto vědomá volba, ne pohodlí: oznamovací věta bez
    otazníku tvrzení JE, a jiný signál na téhle vrstvě není. Otázku bez
    otazníku („Máš auto") tím nepoznáme — to je přiznaná mez, ne přehlédnutí.
    """
    return Mood.QUESTION if text.rstrip().endswith("?") else Mood.ASSERTION


class TurnKind(Enum):
    ASSERT = "!"
    READING = "«"
    DISJOINT = "!∦"
    REVOKE = "✗"
    QUESTION = "?"
    BOUND = "?~"
    DESCRIBE = "?="
    ENUMERATE = "?∃"
    CONFIRM = "→"
    #: „Ti dva nejsou tíž." Vlastní druh tahu, protože je to tvrzení
    #: o identitě, ne obyčejný fakt — a jádro na něj reaguje jinak
    #: (sporná hrana se přestane používat, M‑1).
    DISTINCT = "!≠"
    #: „Tohle byli dva různí lidé." Rozdělení uzlu, který kanonizace
    #: jmen ztotožnila (M‑2).
    SPLIT = "!÷"
    #: ODPOVĚĎ na otázku systému po kvantifikátoru. Naučí tvar a hned
    #: přečte čekající větu znovu (N‑1).
    ANSWER_QUANTIFIER = "→∀"
    #: ODPOVĚĎ na otázku systému po tom, KTERÝ uzel se míní (M‑4).
    DECIDE_REFERENCE = "→="
    #: ODPOVĚĎ na otázku systému po JMÉNU ROLE ztraceného členu (N‑5).
    NAME_ROLE = "→@"
    #: ODPOVĚĎ na otázku systému po tom, KTEROU JÁDROVOU RELACI stavba
    #: věty tvrdí (N‑2). Vlastní druh tahu, protože se tím nenaučí, jak se
    #: věta ČTE, ale co se z ní zapíše do JÁDRA — a to je jiná váha.
    NAME_RELATION = "→⊆"
    #: ODPOVĚĎ na otázku po kvantifikátoru JEDNÉ VĚTY, ne tvaru (N‑8).
    #: Vlastní druh tahu, protože se tím NIC NEUČÍ — a to je celý rozdíl
    #: proti `→∀`. Jsou to dvě různé otázky: „jak se čte tenhle tvar"
    #: a „jak se čte tahle věta".
    ANSWER_HERE = "→∀1"
    #: ODPOVĚĎ na otázku po jádrové relaci JEDNÉ VĚTY, ne tvaru (N‑11).
    #: Táž úvaha jako u `→∀1`: „Praha je součástí Česka." a „Pondělí je
    #: součástí týdne." mají TÝŽ tvar a různé relace, protože jedno je
    #: místo a druhé čas — a to čeština neříká.
    NAME_RELATION_HERE = "→⊆1"
    #: ODPOVĚĎ na otázku, KOHO označuje přivlastňovací přívlastek (N‑7).
    #: Vlastní druh tahu, protože zapisuje DVA výroky: větu a k ní vztah
    #: vlastnictví. Ani `→=`, ani `→@` to nejsou — první rozhoduje odkaz
    #: uvnitř jedné formule, druhý učí tvar; tenhle přidává FAKT.
    NAME_OWNER = "→'"


@dataclass(frozen=True, slots=True)
class Turn:
    """Jeden tah dialogu. `text` je pro člověka, ostatní pole pro jádro."""

    kind: TurnKind
    text: str
    formula: Formula | None = None
    query: Atom | None = None
    bridge: Rule | None = None
    subject: Term | None = None
    quantity: str | None = None
    comparator: Comparator = Comparator.LE
    accepted: bool = True
    statement_id: str | None = None
    reason: str = ""
    variable: str = ""
    pair: tuple[GroupTerm, GroupTerm] | None = None
    #: Druhý operand identitních tahů (`!≠`).
    other: Term | None = None
    #: Nová jména při rozdělení uzlu (`!÷`).
    split_into: tuple[str, str] | None = None
    #: Tvar, na který odpovídá tah `→∀`, a zvolená operace.
    shape: StructuralSignature | None = None
    operation: Operation | None = None
    #: Role a uzel, které rozhodl tah `→=`.
    role_name: str = ""
    node_id: str = ""
    #: Tvar ztracené role a rozbor, ze kterého se čte znovu (`→@`).
    #: Rozbor se nese s tahem, protože ztracený člen v predikaci NENÍ —
    #: to je celý ten problém — takže znovu přečíst jde jen ze stromu.
    shape_name: str = ""
    reading: Reading | None = None
    #: Vybrané čtení. Do žurnálu jde STRUKTURA, ne text — kdyby v žurnálu
    #: ležely věty, `replay` by závisel na verzi parseru a přehratelnost
    #: z § 10 by padla (a na té stojí měření učitelnosti).
    predication: Predication | None = None
    trace: tuple[str, ...] = ()
    #: Ztracené významové členy tahu čtení. Nesou se s tahem, protože
    #: v predikaci NEJSOU — to je celý ten problém — a `replay` by se
    #: na ně jinak nezeptal podruhé, ačkoli pořád chybí.
    lost: tuple[tuple[str, str], ...] = ()


def says(text: str, formula: Formula) -> Turn:
    return Turn(TurnKind.ASSERT, text, formula=formula)


def asks(text: str, query: Atom, *, bridge: Rule | None = None) -> Turn:
    return Turn(TurnKind.QUESTION, text, query=query, bridge=bridge)


def asks_bound(
    text: str,
    subject: Term,
    quantity: str,
    *,
    comparator: Comparator = Comparator.LE,
    bridge: Rule | None = None,
) -> Turn:
    return Turn(
        TurnKind.BOUND,
        text,
        subject=subject,
        quantity=quantity,
        comparator=comparator,
        bridge=bridge,
    )


def asks_about(text: str, subject: Term) -> Turn:
    return Turn(TurnKind.DESCRIBE, text, subject=subject)


def asks_for(text: str, pattern: Atom, variable: str) -> Turn:
    """Výčtová otázka se syntézou — „Co má Filip?" nevrací echo jedné věty,
    ale složený popis nalezeného uzlu (§ 6.5, dialog F)."""
    return Turn(TurnKind.ENUMERATE, text, query=pattern, variable=variable)


def reads(
    text: str,
    predication: Predication,
    *,
    trace: Sequence[str] = (),
    lost: Sequence[tuple[str, str]] = (),
) -> Turn:
    """Tah, který vznikl z české věty. Nese VYBRANÉ ČTENÍ, ne text —
    `text` je jen popis pro transkript, přehrává se struktura."""
    return Turn(
        TurnKind.READING,
        text,
        predication=predication,
        trace=tuple(trace),
        lost=tuple(lost),
    )


def _disjoint_pair(formula: Atom) -> tuple[GroupTerm, GroupTerm]:
    """Operandy `disjoint` z atomu, který postavila V3.

    Sort se kontroluje, i když ho `disjoint_of` vyrobil právě před chvílí:
    kdyby se sem někdy dostal jiný atom, tichý `cast` by ho pustil dál
    a spadlo by to o vrstvu níž, kde už nebude vidět, odkud přišel.
    """
    sides = {r.name: r.target for r in formula.roles}
    first, second = sides.get("a"), sides.get("b")
    if not isinstance(first, (Group, Variable)) or not isinstance(
        second, (Group, Variable)
    ):
        raise SortError(
            f"{formula}: oddělenost se tvrdí o SKUPINÁCH; role `a`/`b` "
            f"nesou {first!r} a {second!r}"
        )
    return first, second


def declares_disjoint(text: str, first: GroupTerm, second: GroupTerm) -> Turn:
    """„Žádný stroj není člověk." Vlastní druh tahu, protože se neukládá
    jeden atom, ale marker plus derivační expanze na dvě pravidla se
    silnou negací (§ 5.3)."""
    return Turn(TurnKind.DISJOINT, text, pair=(first, second))


def names_relation(
    text: str, reading: Reading, shape: str, operation: Operation
) -> Turn:
    """ODPOVĚĎ na otázku „co ta stavba tvrdí?" (N‑2).

    Táž smyčka jako u kvantifikátoru a ztracené role: **zeptat se →
    odpověď jako TAH → naučit TVAR → přečíst větu ZNOVU.** Učí se
    konstrukce (`cop:NOUN=NOUN`), ne věta, takže jedna odpověď zavře
    celou třídu vět.

    Nabídka je uzavřená (`RELATIONAL`) — dialog nesmí vyrobit relaci,
    kterou jádro nezná (I‑15).
    """
    return Turn(
        TurnKind.NAME_RELATION,
        text,
        reading=reading,
        shape_name=shape,
        operation=operation,
    )


def answers_here(
    text: str, predication: Predication, role_name: str, operation: Operation
) -> Turn:
    """ODPOVĚĎ na kvantifikátor JEDNÉ VĚTY — N‑8.

    **Proč to nemůže dělat `→∀`.** Ten váže odpověď na `StructuralSignature`,
    tedy na TVAR, a jedna odpověď tím zavře celou třídu vět. Většinou je
    to přesně to, co chceme; jenže čeština má tvary, které v jedné větě
    znamenají `∀` a v druhé `∃`. „Vegetarián nejí maso" mluví o KAŽDÉM
    masu, „Petr jedl steak" o JEDNOM steaku — a `NOUN/Sing/Acc/obj` je to
    v obou. Po první odpovědi se ta druhá věta už nezeptá a přečte se
    špatně.

    **Tenhle tah se proto NIC NEUČÍ.** Odpověď platí pro tu jednu větu
    a v lexikonu po ní nezůstane nic. Není to náhrada `→∀`, je to jiná
    otázka — a obě se ptají právem: tvar má většinou jeden význam a je
    hloupé se na něj ptát pokaždé, ale výjimky existují a tichý default
    by je přejel (L‑3).
    """
    return Turn(
        TurnKind.ANSWER_HERE,
        text,
        predication=predication,
        role_name=role_name,
        operation=operation,
    )


def names_relation_here(
    text: str, predication: Predication, reading: Reading, operation: Operation
) -> Turn:
    """ODPOVĚĎ na jádrovou relaci JEDNÉ VĚTY — N‑11.

    **Proč to nemůže dělat `→⊆`.** Ten učí KONSTRUKCI, takže jedna
    odpověď zavře celou třídu vět. U zahrnutí to nejde: „Praha je
    součástí Česka." je `contains` (místo), „Pondělí je součástí týdne."
    je `within` (čas), a tvar je v obou `cop:součást+Gen`. Rozdíl je
    v SORTU filleru, a ten čeština neříká — jméno „týden" o sobě
    neprozradí, že je to čas.

    **Tenhle tah se proto nic neučí.** Není to náhrada `→⊆`, je to jiná
    otázka — a obě se ptají právem: konstrukce má většinou jeden význam
    a je hloupé se na něj ptát pokaždé, ale výjimky existují a tichý
    default by je přejel.
    """
    return Turn(
        TurnKind.NAME_RELATION_HERE,
        text,
        predication=predication,
        reading=reading,
        operation=operation,
    )


def names_owner(text: str, reading: Reading, owner_id: str) -> Turn:
    """ODPOVĚĎ na otázku „koho označuje to přivlastnění?" (N‑7).

    **Proč to musí říct člověk.** Rozbor dá `Filipovo` s lemmatem
    `Filipův`; cesta odtud k uzlu `Filip` je derivační morfologie, kterou
    tagger neřeší. Useknout „‑ův" by byl dohad o češtině zadrátovaný do
    interpretu — táž třída jako seznam významů předložek (INV‑11).

    **Co je na tvaru a co na slově.** Že přivlastnění vůbec označuje
    VLASTNÍKA, je vlastnost konstrukce a platí pro každé `amod` s
    `Poss=Yes`; to se neučí, protože to není rozhodnutí. KDO je ten
    vlastník, je naproti tomu vlastnost jedné zmínky — tady se
    rozhoduje, a proto to leží v žurnálu jako tah, ne v lexikonu jako
    vzor. Uložit dvojici `Filipův → Filip` jako vzor by znamenalo učit
    se každé jméno zvlášť a tvářit se u toho, že jde o naučenou
    zákonitost.
    """
    return Turn(TurnKind.NAME_OWNER, text, reading=reading, node_id=owner_id)


def answers_quantifier(
    text: str,
    predication: Predication,
    shape: StructuralSignature,
    operation: Operation,
) -> Turn:
    """ODPOVĚĎ na otázku „o kom to platí?" (N‑1).

    Systém, který se umí zeptat a neumí přijmout odpověď, se neumí učit
    dialogem — otázka slepě končí a `turns_to_learn` (§ 10) nemá co měřit.

    Tah dělá dvě věci najednou a obě jsou nutné: **naučí tvar** (jako
    potvrzený vzor, tedy odvolatelná data s proveniencí) a **znovu přečte
    čekající větu**. Kdyby jen učil, člověk by musel větu zopakovat — a to
    je přesně ta práce navíc, kvůli které se lidem s takovými systémy
    nechce mluvit.
    """
    return Turn(
        TurnKind.ANSWER_QUANTIFIER,
        text,
        predication=predication,
        shape=shape,
        operation=operation,
    )


def decides_reference(
    text: str, predication: Predication, role_name: str, node_id: str
) -> Turn:
    """ODPOVĚĎ na otázku „o kterém z nich mluvíš?" (M‑4).

    Rozhodnutí je TAH, takže leží v žurnálu a `replay` se neptá podruhé —
    a nevyjde ani jinak, kdyby mezitím v bázi přibyl další kandidát.
    """
    return Turn(
        TurnKind.DECIDE_REFERENCE,
        text,
        predication=predication,
        role_name=role_name,
        node_id=node_id,
    )


def names_role(
    text: str, reading: Reading, shape: str, role_name: str
) -> Turn:
    """ODPOVĚĎ na otázku „jakou roli hraje tenhle člen?" (N‑5).

    Systém ohlásil, že mu ze vstupu něco vypadlo, a **zeptal se**.
    Tenhle tah je odpověď: naučí mapování TVARU na roli a čekající větu
    přečte ZNOVU — teprve pak se zapisuje. Věta se tím dokončí, ne oseká.

    Učí se tvar (`xcomp>obj+Acc`), ne slovo (`penicilin`), takže jedna
    odpověď zavře celou třídu vět.
    """
    return Turn(
        TurnKind.NAME_ROLE,
        text,
        reading=reading,
        shape_name=shape,
        role_name=role_name,
    )


def declares_distinct(text: str, first: Term, second: Term) -> Turn:
    """„Ten Petr není ten Petr." Zapíše `¬same_as` — jádro to umí a od
    verze 0.1.6 tím zároveň **odebere spornou hranu z uzávěru** (M‑1),
    takže kanonizace jmen má o co se opřít."""
    return Turn(TurnKind.DISTINCT, text, subject=first, other=second)


def splits(text: str, node: Term, into: tuple[str, str], reason: str) -> Turn:
    """„Tohle byli dva různí lidé." Rozdělení kanonického uzlu (M‑2).

    Je to ATOMICKÝ tah, ne posloupnost: mezi odpojením výroků a jejich
    přesměrováním by báze tvrdila něco, co nikdo neřekl."""
    return Turn(
        TurnKind.SPLIT, text, subject=node, split_into=into, reason=reason
    )


def revokes(text: str, statement_id: str, reason: str) -> Turn:
    """Odvolání je plnohodnotný tah — učení má jen `attach` a `revoke`
    (§ 3.7). Výrok zůstává v historii s důvodem."""
    return Turn(TurnKind.REVOKE, text, statement_id=statement_id, reason=reason)


def confirms(text: str, *, accepted: bool = True) -> Turn:
    return Turn(TurnKind.CONFIRM, text, accepted=accepted)


@dataclass(frozen=True, slots=True)
class TurnResult:
    index: int
    turn: Turn
    lines: tuple[str, ...] = ()
    statement_id: str | None = None
    derived: tuple[str, ...] = ()
    status: QueryStatus | None = None
    report: AuditReport | None = None
    offered: Rule | None = None
    error: str | None = None
    #: Vybrané čtení u tahu, který vznikl z české věty.
    predication: Predication | None = None
    trace: tuple[str, ...] = ()
    #: Doptání, které tah nechává otevřené. Čtení může být vybrané a přesto
    #: nehotové — role bez kvantifikátoru je otázka, ne hodnota (L‑3).
    question: str | None = None

    def render(self) -> str:
        head = f"»  {self.turn.kind.value} {self.turn.text}"
        return "\n".join([head, *[f"    {line}" for line in self.lines]])


class Session:
    """Drží bázi, evaluátor a renderer a zpracovává tahy."""

    def __init__(
        self,
        *,
        profile: TemplateProfile = DEFAULT_PROFILE,
        max_depth: int = 1,
        lexicon: Lexicon | None = None,
    ) -> None:
        self.kb = KnowledgeBase(max_depth=max_depth)
        self.presenter = XAIPresenter(self.kb, profile)
        self.journal: list[Turn] = []
        self.results: list[TurnResult] = []
        self._pending: Rule | None = None
        #: `LEX` je program vedle `ONTO` a `DIA`, takže patří do sezení,
        #: ne do volání. Jinak by dvě věty téhož dialogu mohly být čteny
        #: podle jiných naučených vzorů a „diff naučeného" (§ 10) by nešel
        #: přečíst z žurnálu.
        self.lexicon = czech_seed() if lexicon is None else lexicon

    def tiers(self) -> tuple[Tier, ...]:
        """Patra kaskády v pořadí § 5.2: tvrdé filtry → konzistence s bází
        → naučené vzory → doptání.

        Sestavuje se při každém tahu znovu, protože **báze i lexikon se
        mezi tahy mění**. Zamrazit patra v konstruktoru by znamenalo, že
        se sezení ptá staré báze — a přesně to má § 5.2 zakázané.
        """
        return (
            *HARD_TIERS,
            lexicon_tier(self.lexicon),
            role_mapping_tier(self.lexicon),
            # Jádrová relace ze stavby (N‑2) PŘED kvantifikátorem: relace
            # své role přejmenuje na jádrové a označí je jako třídy, takže
            # kvantifikátor už na nich nemá co řešit. V opačném pořadí by
            # se člověk nejdřív doptal na kvantifikátor role `co`, a ta by
            # vzápětí přestala existovat.
            relation_tier(self.lexicon),
            # Doplnění ztracené role PŘED kvantifikátorem: role, která
            # teprve vznikne, se musí stihnout zkvantifikovat jako každá
            # jiná — jinak by odpověď zavřela jednu otázku a hned otevřela
            # druhou, na kterou by se systém zeptal až příště.
            lost_role_tier(self.lexicon),
            # Kvantifikátor až po přejmenování rolí: patro se ptá lexikonu
            # na TVAR role, a ten se do poslední chvíle může změnit.
            quantifier_tier(self.lexicon),
            # KONZISTENCE S BÁZÍ JE AŽ TADY, a je to VĚDOMÁ ODCHYLKA od
            # pořadí v § 5.2 („…→ konzistence s bází → naučené vzory…").
            #
            # Důvod: od K‑7 smí báze čtení eliminovat jen z pojmenovaného
            # sémantického důvodu, a ten se dá zjistit teprve nad ZAKOTVENOU
            # formulí. Zakotvení potřebuje kvantifikátor, a ten je naučený
            # vzor. Patro postavené před učením by tedy buď nemělo co
            # posoudit, nebo by posuzovalo podle něčeho jiného — a to
            # „něco jiného" byla přesně ta popularita, kterou K‑7 ruší.
            #
            # Pořadí § 5.2 vzniklo dřív, než kvantifikátor byl naučeným
            # vzorem. Držet ho doslova by znamenalo držet tvar proti účelu.
            base_consistency_tier(semantic_rejection(self.engine())),
        )

    # -- běh ---------------------------------------------------------------

    def engine(self) -> Engine:
        """Nový evaluátor nad aktuální bází. Otázka bázi nemění (I‑12),
        takže je zahoditelný."""
        return Engine(self.kb)

    def play(self, turn: Turn) -> TurnResult:
        index = len(self.journal) + 1
        self.journal.append(turn)
        handler = {
            TurnKind.ASSERT: self._assert,
            TurnKind.READING: self._reading,
            TurnKind.DISJOINT: self._declare_disjoint,
            TurnKind.DISTINCT: self._declare_distinct,
            TurnKind.SPLIT: self._split,
            TurnKind.ANSWER_QUANTIFIER: self._answer_quantifier,
            TurnKind.DECIDE_REFERENCE: self._decide_reference,
            TurnKind.NAME_ROLE: self._name_role,
            TurnKind.NAME_RELATION: self._name_relation,
            TurnKind.NAME_RELATION_HERE: self._name_relation_here,
            TurnKind.ANSWER_HERE: self._answer_here,
            TurnKind.NAME_OWNER: self._name_owner,
            TurnKind.REVOKE: self._revoke,
            TurnKind.QUESTION: self._question,
            TurnKind.BOUND: self._bound,
            TurnKind.DESCRIBE: self._describe,
            TurnKind.ENUMERATE: self._enumerate,
            TurnKind.CONFIRM: self._confirm,
        }[turn.kind]
        result = handler(index, turn)
        self.results.append(result)
        return result

    def run(self, turns: Sequence[Turn]) -> list[TurnResult]:
        return [self.play(turn) for turn in turns]

    @classmethod
    def replay(
        cls, journal: Sequence[Turn], *, profile: TemplateProfile = DEFAULT_PROFILE
    ) -> "Session":
        """Přehraje žurnál. **Lexikon není parametr, a je to smlouva.**

        Žurnál nese ROZHODNUTÉ tahy, ne věty (§ 10) — čtení je v něm už
        vybrané, takže není co číst znovu a naučené vzory nemají do čeho
        mluvit. Kdyby žurnál někdy začal nést text, přestane to platit
        a přehrání se rozejde s originálem podle toho, co se mezitím
        systém naučil. Psáno sem proto, aby to byla smlouva, ne náhoda.
        """
        session = cls(profile=profile)
        session.run(journal)
        return session

    # -- výstup ------------------------------------------------------------

    def transcript(self) -> str:
        return "\n\n".join(result.render() for result in self.results)

    def program(self) -> tuple[str, ...]:
        """Aktivní výroky jako text — „diff kódu je diff naučeného" (§ 10)."""
        return tuple(str(statement) for statement in self.kb.active())

    def answers(self) -> tuple[str, ...]:
        return tuple(result.render() for result in self.results)

    def turns_to_learn(self, text: str) -> int | None:
        """Hlavní metrika § 10 — kolik tahů uplynulo od prvního `NEVÍM` na
        danou otázku po první doloženou odpověď na tutéž otázku."""
        unknown_at: int | None = None
        for result in self.results:
            if result.turn.text != text or result.status is None:
                continue
            if result.status is QueryStatus.UNKNOWN:
                if unknown_at is None:
                    unknown_at = result.index
            elif unknown_at is not None:
                return result.index - unknown_at
        return None

    # -- jednotlivé druhy tahu ---------------------------------------------

    def _assert(self, index: int, turn: Turn) -> TurnResult:
        assert turn.formula is not None
        try:
            sid = self.kb.attach(turn.formula, provenance=f"tah {index}")
        except AttachError as exc:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(f"✗ nezapsáno: {exc}",),
                error=str(exc),
            )
        statement, _, _ = self.kb.inspect(sid)
        derived = tuple(item.id for item in self.kb.derived_from(sid))
        lines = [f"✓ zapsáno [{sid}]  {statement.formula}"]
        if derived:
            lines.append(f"[odvozeno: {', '.join(derived)}]")
        return TurnResult(
            index=index, turn=turn, lines=tuple(lines), statement_id=sid,
            derived=derived,
        )

    def _question(self, index: int, turn: Turn) -> TurnResult:
        assert turn.query is not None
        engine = self.engine()
        result = engine.ask(turn.query)
        report = self.presenter.render_audit_report(turn.query, result)
        # Na `U` se místo zopakované otázky vypíše ROZBOR mezery (§ 6.8).
        # „Chybí vědět: <dotaz>" člověku neřekne, co má doplnit.
        gap_lines = (
            GapFinder(engine).explain(turn.query).render()
            if result.status is QueryStatus.UNKNOWN
            else ()
        )
        lines = list(self._render_answer(report, gap_lines=gap_lines))
        offered = self._offer_bridge(turn, result, lines)
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=result.status,
            report=report,
            offered=offered,
        )

    def _bound(self, index: int, turn: Turn) -> TurnResult:
        assert turn.subject is not None and turn.quantity is not None
        bound: BoundResult = query_bound(
            self.engine(), turn.subject, turn.quantity, turn.comparator
        )
        lines: list[str] = []
        if bound.status is QueryStatus.PROVEN_TRUE and bound.value is not None:
            lines.append(
                f"→ {turn.comparator.value} {bound.value.magnitude} "
                f"{bound.value.unit}"
            )
            lines.extend(self._render_reason(bound.proof))
        else:
            lines.append("→ NEVÍM")
            lines.append(
                f"  chybí vědět: mez veličiny {turn.quantity!r} "
                f"pro {turn.subject.id}"
            )
        synthetic = QueryResult(status=bound.status, proof=bound.proof)
        offered = self._offer_bridge(turn, synthetic, lines)
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=bound.status,
            offered=offered,
        )

    # -- česká věta na vstupu ----------------------------------------------

    def utter(
        self,
        text: str,
        oracle: ParseOracle,
        *,
        mood: Mood | None = None,
    ) -> TurnResult:
        """Druhý vstup vedle strukturovaného tahu: **česká věta**.

        Věta se rozloží orákulem, kaskáda z kandidátních čtení vybere,
        a **do žurnálu jde vybrané čtení, ne text**. Replay tím nezávisí
        na verzi parseru (§ 10).

        Tři různé výsledky, které se nesmí slít (past F‑3):

        * **orákulum neodpovídá** — provozní chyba. Do žurnálu nejde nic:
          přehrávat „parser byl mimo" by znamenalo přehrávat stav prostředí,
          ne dialog.
        * **věta se nerozebrala** — poctivé „tuhle větu neumím přečíst".
          Taky nejde do žurnálu, protože není co přehrát.
        * **kaskáda nerozhodla** — doptání. Otázka je odpověď (I‑7).

        Zápis do báze se tu **nedělá**: převod zmínky na uzel je V3
        a ten čeká. `TurnResult.predication` nese, co kaskáda vybrala.
        """
        index = len(self.journal) + 1
        detected = mood if mood is not None else _mood_of(text)
        try:
            utterance = oracle.parse(text)
        except OracleUnavailable as exc:
            return TurnResult(
                index=index,
                turn=Turn(TurnKind.READING, text),
                lines=(
                    "✗ orákulum neodpovídá — provozní chyba, ne nepochopení",
                    f"  {exc}",
                ),
                error=str(exc),
            )
        if not utterance.readings:
            return TurnResult(
                index=index,
                turn=Turn(TurnKind.READING, text),
                lines=(
                    "→ tuhle větu neumím přečíst",
                    "  (rozbor se nepodařil — zkus to říct jinak,"
                    " nebo mi to zadej strukturovaně)",
                ),
            )

        if len(utterance.readings) > 1:
            # Orákulum vrátilo víc kandidátních čtení. Vzít `readings[0]`
            # by byla tichá volba měnící význam (I‑1) — a hlásit se sama
            # nemá jak, protože zbylá čtení se jen zahodí. Kaskáda běží
            # nad každým a rozhodnuto je, jen když PŘES VŠECHNA zbyde
            # jeden kandidát.
            return self._utter_many(index, text, utterance, detected)

        verdict = cascade(utterance.readings[0], mood=detected, tiers=self.tiers())
        if verdict.decided is None:
            lines = ["→ NEVÍM, jak to čtu", *(f"  {step}" for step in verdict.trace)]
            if verdict.question:
                lines.append(f"  ? {verdict.question}")
            return TurnResult(
                index=index,
                turn=Turn(TurnKind.READING, text),
                lines=tuple(lines),
                status=QueryStatus.UNKNOWN,
                trace=verdict.trace,
                # Otázka patří i do VÝSLEDKU, nejen do vypsaných řádků.
                # Odběratel, který se ptá `result.question`, by jinak
                # u nerozhodnutého čtení dostal `None` a četl to jako
                # „systém se neptá" — a přesně tady se ptá nejvíc.
                question=verdict.question,
            )
        return self.play(
            reads(
                text,
                verdict.decided.predication,
                trace=verdict.trace,
                lost=verdict.lost,
            )
        )

    def _utter_many(
        self, index: int, text: str, utterance: Utterance, mood: Mood
    ) -> TurnResult:
        """Víc kandidátních čtení jedné promluvy (§ 5.1).

        Kaskáda je psaná nad JEDNÍM stromem, protože její patra se ptají
        rozboru („jaké číslo má přísudek"). Sloučit stromy nejde; sloučit
        se dá až to, co z nich zbylo. Shodné predikace z různých stromů
        se přitom **slévají** — dvojznačnost, kterou nikdo neuvidí, není
        důvod k doptání.
        """
        pooled: list[Candidate] = []
        trace: list[str] = [f"orákulum: {len(utterance.readings)} kandidátních čtení"]
        for number, reading in enumerate(utterance.readings, start=1):
            verdict = cascade(reading, mood=mood, tiers=self.tiers())
            trace.extend(f"[čtení {number}] {step}" for step in verdict.trace)
            for candidate in verdict.survivors:
                if all(
                    candidate.predication != seen.predication for seen in pooled
                ):
                    pooled.append(candidate)
        if len(pooled) == 1:
            return self.play(
                reads(text, pooled[0].predication, trace=tuple(trace))
            )
        lines = ["→ NEVÍM, jak to čtu", *(f"  {step}" for step in trace)]
        if pooled:
            options = " / ".join(str(c.predication) for c in pooled)
            lines.append(f"  ? Čtu to jako: {options} — které z toho?")
        return TurnResult(
            index=index,
            turn=Turn(TurnKind.READING, text),
            lines=tuple(lines),
            status=QueryStatus.UNKNOWN,
            trace=tuple(trace),
        )

    def _reading(self, index: int, turn: Turn) -> TurnResult:
        """Vybrané čtení jako tah — **i s tím, co v něm ještě chybí**.

        Doptání na kvantifikátor se z čtení **odvozuje**, neukládá. Role
        si nese `pending`, takže otázka jde spočítat z žurnálu — a proto
        ji `replay` zopakuje doslova. Kdyby se ukládala jako text, žurnál
        by přestal držet strukturu a začal držet odpověď (§ 10).
        """
        assert turn.predication is not None
        return self._settle(index, turn, turn.predication, ())

    def _settle(
        self,
        index: int,
        turn: Turn,
        predication: Predication,
        prefix: Sequence[str],
    ) -> TurnResult:
        """Čtení → zakotvení → směrování, společné pro všechny tři cesty.

        Vede sem tah čtení i oba tahy ODPOVĚDI na doptání. Kdyby měl každý
        vlastní kopii, rozešly by se — a rozešly by se zrovna v tom, jestli
        se po odpovědi opravdu ZNOVU ZKUSÍ zapsat, což je celý smysl toho,
        že se člověk odpovídat obtěžoval.

        **Otázka se skládá AŽ Z VÝSLEDKU ZAKOTVENÍ** *(G‑4)*. Role, kterou
        zakotvení doložilo, otevřenou otázku nemá — a značka `◐` se řídí
        týmž stavem, protože je to tvrzení o tahu, ne ozdoba. Ptát se na
        to, co si systém právě sám zodpověděl, je horší než otázka bez
        odběratele: odpověď by přišla k rozhodnutí, které padlo, a mohla
        by správnou vazbu přepsat.
        """
        # ZAKOTVENÍ NEJDŘÍV, TEPRVE PAK OTÁZKA *(G‑4)*. Dřív se otázka
        # skládala z předzakotvené predikace a úspěšné doložení odkazu ji
        # už nesmazalo: systém vypsal „na koho odkazuje `auto`?", hned pod
        # tím „auto → a1 (jediný kandidát)", větu ZAPSAL — a v `question`
        # pořád nesl dotaz na roli, která je navázaná. Odběratel by se
        # člověka ptal na rozhodnutí, které padlo, a odpověď by v horším
        # případě správnou vazbu přepsala.
        #
        # Je to zrcadlo nálezu z N‑3: tam se otázka četla ze STOPY, tedy
        # z logu, tady se počítala PŘED krokem, který ji ruší. Obojí má
        # touž opravu — ptát se AŽ VÝSLEDKU.
        grounded = ground(predication, self.kb.view())
        anchored = {anchor.mention.token_index for anchor in grounded.anchors}
        still_open = tuple(
            role
            for role in predication.open_roles()
            if role.mention.token_index not in anchored
        )
        question = " ".join(
            part
            for part in (
                open_roles_question(still_open),
                lost_question(turn.lost),
                # Otázka na význam povrchové role (N‑3). Počítá se
                # z HOTOVÉ predikace, ne ze stopy — jinak by se ptala na
                # tvary, které pozdější patro spotřebovalo.
                role_question(predication),
                # Otázka na to, co stavba tvrdí (N‑2). Čte se ze STOPY,
                # protože v predikaci po sobě nerozhodnutá relace nic
                # nenechá — čtení zůstane obyčejným vztahem a nedalo by
                # se z něj poznat, že o něm systém pochybuje.
                relation_question(turn.trace),
                grounded.question,
            )
            if part
        ) or None
        # Tři znaménka, ne dvě. `✓` slibuje hotový tah, jenže čtení
        # s otevřenou rolí by na `role()` spadlo na `UnquantifiedRole`,
        # a čtení, ze kterého vypadl kus věty, není celá věta. V obou
        # případech je odevzdané míň, než ta značka říká.
        partial = question is not None or has_dropped(turn.trace)
        mark = "◐ přečteno, neúplné" if partial else "✓ přečteno"
        lines = [*prefix, f"{mark}  {predication}"]
        lines.extend(f"  {step}" for step in turn.trace)
        lines.extend(f"  {note}" for note in grounded.notes)
        lines.extend(f"  {anchor}" for anchor in grounded.anchors)
        if question:
            lines.append(f"  ? {question}")

        # Věta, ze které něco VYPADLO, se nezapisuje. Zapsat ji teď a po
        # odpovědi znovu by uložilo DVA výroky — nejdřív oseknutý, pak
        # celý — a ten první by nikdo neodvolal. Čeká se na doplnění;
        # věta se má dokončit, ne oseknout.
        #
        # TÝŽ DŮVOD U NEROZHODNUTÉ JÁDROVÉ RELACE (N‑2). Věta, u které se
        # systém ptá, co ta stavba tvrdí, by se zapsala jako obyčejný
        # vztah `být` — a kdyby člověk vzápětí odpověděl `subset`, ležely
        # by v bázi OBA výroky a ten první by nikdo neodvolal. Je to táž
        # vada jako u ztraceného členu, jen o jinou chybějící věc.
        pending_relation = relation_question(turn.trace) is not None
        routed = (
            None
            if turn.lost or pending_relation
            else self._route(index, turn, predication, grounded)
        )
        if routed is None:
            if grounded.formula is None and not question:
                lines.append("  (zakotvení neproběhlo — do báze nejde nic)")
            return TurnResult(
                index=index,
                turn=turn,
                lines=tuple(lines),
                predication=predication,
                trace=turn.trace,
                question=question,
                # Nezodpovězená OTÁZKA je `U`, i když ztroskotala už na
                # čtení. Z pohledu člověka se zeptal a odpověď nedostal,
                # a `turns_to_learn` (§ 10) měří přesně tuhle vzdálenost —
                # bez toho by metrika neviděla začátek intervalu.
                status=(
                    QueryStatus.UNKNOWN
                    if predication.mood is Mood.QUESTION
                    else None
                ),
            )
        return replace(
            routed,
            turn=turn,
            lines=(*lines, *routed.lines),
            predication=predication,
            trace=turn.trace,
            question=question,
        )

    def _route(
        self,
        index: int,
        turn: Turn,
        predication: Predication,
        grounded: Grounded,
    ) -> TurnResult | None:
        """`!` → `attach`, `?` → `ask`. Nálada rozhoduje, co se s formulí
        stane (L‑5).

        **Nezakotvená věta se nesměruje.** Zapsat půlku čtení by znamenalo
        zapsat něco jiného, než člověk řekl, a otázka na půlku atomu by
        se ptala na něco jiného, než se ptal on.

        Směruje se **uvnitř tahu čtení**, ne druhým tahem. Jedna věta je
        jeden tah — jinak by `turns_to_learn` (§ 10) počítalo dvakrát to,
        co člověk řekl jednou.
        """
        if grounded.formula is None:
            return None
        if predication.mood is Mood.QUESTION:
            return self._question(index, asks(turn.text, grounded.formula))
        if predication.mood is Mood.ASSERTION:
            if predication.relation is Operation.DISJOINT:
                # SPRÁVNÝMI DVEŘMI (N‑2). Oddělenost se nezapisuje přes
                # `attach`: s markerem musí vzniknout i dvojice pravidel
                # se silnou negací, jinak by se `disjoint` do indexu dostal
                # a NEODVODILO by se z něj nic. `attach` to odmítá — a to
                # odmítnutí je správně, takže se nemá obcházet, ale použít
                # ty dveře, na které ukazuje.
                return self._declare_disjoint(
                    index, declares_disjoint(turn.text, *_disjoint_pair(grounded.formula))
                )
            return self._assert(index, says(turn.text, grounded.formula))
        # `Mood.UNKNOWN` — nálada se nepoznala. Hádat mezi „zapiš to"
        # a „odpověz na to" je ta nejhorší tichá volba, jakou tenhle
        # systém může udělat: jedna z nich mění bázi.
        return None

    def _declare_disjoint(self, index: int, turn: Turn) -> TurnResult:
        assert turn.pair is not None
        first, second = turn.pair
        try:
            marker, left, right = self.kb.add_disjoint(
                first, second, provenance=f"tah {index}"
            )
        except AttachError as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ nezapsáno: {exc}",), error=str(exc)
            )
        return TurnResult(
            index=index,
            turn=turn,
            lines=(
                f"✓ zapsáno [{marker}]  disjoint({first.id}, {second.id})",
                f"[expanze na dvě pravidla se silnou negací: {left}, {right}]",
            ),
            statement_id=marker,
            derived=(left, right),
        )

    def _answer_here(self, index: int, turn: Turn) -> TurnResult:
        """`→∀1` — kvantifikátor pro TUHLE VĚTU. Nic se neučí.

        Zavírá se role podle JMÉNA, ne podle tvaru: tvar je zrovna to,
        co tu rozhodnout nejde, protože v jiné větě znamená něco jiného.
        """
        assert turn.predication is not None and turn.operation is not None
        target = turn.predication.reading(turn.role_name)
        if target is None or target.pending is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(
                    f"✗ nerozhodnuto: role {turn.role_name!r} na kvantifikátor "
                    f"nečeká, takže není co rozhodovat",
                ),
                error="role nečeká na kvantifikátor",
            )
        quantifier = QUANTIFIER_OF.get(turn.operation)
        resolved = replace(
            turn.predication,
            roles=tuple(
                replace(
                    role,
                    quantifier=quantifier,
                    pending=None,
                    awaiting="",
                    source=f"rozhodnuto pro tuhle větu (tah {index})",
                )
                if role.name == turn.role_name
                else role
                for role in turn.predication.roles
            ),
        )
        prefix = [
            f"✓ rozhodnuto pro TUHLE VĚTU  {turn.role_name} → "
            f"{turn.operation.value}",
            "  (tvar se tím NEUČÍ — jiná věta se zeptá znovu)",
        ]
        return self._settle(index, turn, resolved, prefix)

    def _answer_quantifier(self, index: int, turn: Turn) -> TurnResult:
        """`→∀` — naučí tvar a HNED přečte čekající větu znovu."""
        assert turn.predication is not None
        assert turn.shape is not None and turn.operation is not None
        pattern = self.lexicon.teach(
            Trigger(
                lemma="",
                upos=turn.shape.upos,
                number=turn.shape.number,
                case=turn.shape.case,
                deprel=turn.shape.deprel,
            ),
            turn.operation,
            learned_from=f"tah {index}",
        )
        confirmed = self.lexicon.confirm(pattern.key())
        quantifier = QUANTIFIER_OF.get(turn.operation)
        closed = tuple(
            role.name
            for role in turn.predication.roles
            if role.pending is not None and role.pending == turn.shape
        )
        resolved = _apply_quantifier(turn.predication, turn.shape, quantifier)
        prefix = [
            f"✓ naučeno  {confirmed or pattern}",
            f"  (platí pro každý tvar {turn.shape.shape()}, ne jen pro tuhle větu)",
        ]
        if not closed:
            prefix.append(
                f"  [POZOR: v téhle větě na tvar {turn.shape.shape()} nic "
                f"nečekalo — naučilo se to, ale nic to tu nezavřelo]"
            )
        return self._settle(index, turn, resolved, prefix)

    def _name_owner(self, index: int, turn: Turn) -> TurnResult:
        """`→'` — člověk pojmenoval vlastníka a vzniká vztah vlastnictví.

        **Věta se tímhle tahem NEZAPISUJE ZNOVU.** Zapsala ji ta věta
        sama, když se dočetla; tenhle tah přidává, co se z ní zapsat
        nedalo. Kdyby prošel `_settle`, ležel by v bázi týž výrok dvakrát
        a ten první by nikdo neodvolal — je to táž vada, kterou u
        ztraceného členu a u nerozhodnuté relace hlídá zábrana v `_settle`,
        jen by ji tudy šlo obejít zezadu.

        Čte se proto znovu jen proto, aby se zjistilo, KE KTERÉMU UZLU se
        přivlastnění vztahuje. Čtení nic nezapisuje.

        **Vlastnictví se připne jen k UZLU.** Dokud se odkaz nerozřešil,
        není ke komu: „nějaké auto patří Filipovi" je jiné tvrzení než
        „TOHLE auto patří Filipovi", a jen to druhé věta nese.
        """
        assert turn.reading is not None
        verdict = cascade(
            turn.reading, mood=_mood_of(turn.text), tiers=self.tiers()
        )
        lines = [f"✓ rozhodnuto  přivlastnění → {turn.node_id}"]
        if verdict.decided is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(*lines, "→ větu se ani tak přečíst nepodařilo"),
                trace=verdict.trace,
            )
        predication = verdict.decided.predication
        grounded = ground(predication, self.kb.view())
        lines.append(f"  čtení: {predication}")
        owned = self._possessed_node(grounded)
        if owned is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(
                    *lines,
                    "→ vlastnictví se nezapsalo: dokud se neví, KTERÝ uzel "
                    "se míní, není ke komu ho připnout",
                ),
                predication=predication,
                trace=verdict.trace,
            )
        fact = atom(
            "vlastnit", role("kdo", Entity(turn.node_id)), role("co", owned)
        )
        try:
            sid = self.kb.attach(fact, provenance=f"tah {index}")
        except AttachError as exc:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(*lines, f"✗ nezapsáno: {exc}"),
                error=str(exc),
            )
        return TurnResult(
            index=index,
            turn=turn,
            lines=(*lines, f"✓ zapsáno [{sid}]  {fact}"),
            predication=predication,
            trace=verdict.trace,
            statement_id=sid,
        )

    @staticmethod
    def _possessed_node(grounded: Grounded) -> Entity | None:
        """Uzel, ke kterému se přivlastnění vztahuje — nebo `None`.

        Poznává se podle DRUHU VAZBY (`RESOLVED_DEFINITE`), ne podle
        jména role: která role je ta přivlastněná, ví stavba věty, ne
        seznam jmen. A bere se ze ZAKOTVENÍ, protože teprve ono řekne,
        na který uzel zmínka přistála — v predikaci je vidět jen to, že
        na nějaký čeká.
        """
        for anchor in grounded.anchors:
            if anchor.binding is BindingType.RESOLVED_DEFINITE:
                return Entity(anchor.term.id)
        return None

    def _decide_reference(self, index: int, turn: Turn) -> TurnResult:
        """`→=` — člověk řekl, KTERÝ uzel se míní."""
        assert turn.predication is not None
        target = turn.predication.reading(turn.role_name)
        if target is None or target.awaiting != AWAITING_REFERENCE:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(
                    f"✗ nerozhodnuto: role {turn.role_name!r} na odkaz "
                    f"nečeká, takže není co rozhodovat",
                ),
                error="role nečeká na odkaz",
            )
        resolved = replace(
            turn.predication,
            roles=tuple(
                replace(role, resolved=turn.node_id, awaiting="")
                if role.name == turn.role_name
                else role
                for role in turn.predication.roles
            ),
        )
        prefix = [f"✓ rozhodnuto  {turn.role_name} → {turn.node_id}"]
        return self._settle(index, turn, resolved, prefix)

    def _name_role(self, index: int, turn: Turn) -> TurnResult:
        """`→@` — člověk pojmenoval roli ztraceného členu a věta se čte znovu."""
        assert turn.reading is not None
        mapping = self.lexicon.teach_role(
            turn.shape_name, turn.role_name, learned_from=f"tah {index}"
        )
        verdict = cascade(
            turn.reading, mood=_mood_of(turn.text), tiers=self.tiers()
        )
        prefix = [
            f"✓ naučeno  {mapping}",
            f"  (platí pro každý tvar {turn.shape_name}, ne jen pro tuhle větu)",
        ]
        if verdict.decided is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(*prefix, "→ větu se ani tak přečíst nepodařilo"),
                trace=verdict.trace,
            )
        return self._settle(index, turn, verdict.decided.predication, prefix)

    def _name_relation_here(self, index: int, turn: Turn) -> TurnResult:
        """`→⊆1` — jádrová relace pro TUHLE VĚTU. Nic se neučí."""
        assert turn.predication is not None and turn.operation is not None
        found = relation_shape(turn.predication, turn.reading) if turn.reading else None
        if found is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=("✗ nerozhodnuto: ta věta žádnou konstrukci nenese",),
                error="věta nenese konstrukci",
            )
        try:
            resolved = as_relation(turn.predication, turn.operation, found)
        except KeyError:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(f"✗ nenaučeno: {turn.operation.value} není jádrová relace",),
                error="operace mimo menu",
            )
        prefix = [
            f"✓ rozhodnuto pro TUHLE VĚTU  stavba → {turn.operation.value}",
            "  (tvar se tím NEUČÍ — jiná věta se zeptá znovu)",
        ]
        return self._settle(index, turn, resolved, prefix)

    def _name_relation(self, index: int, turn: Turn) -> TurnResult:
        """`→⊆` — člověk řekl, co ta stavba tvrdí, a věta se čte znovu."""
        assert turn.reading is not None and turn.operation is not None
        try:
            mapping = self.lexicon.teach_relation(
                turn.shape_name, turn.operation, learned_from=f"tah {index}"
            )
        except ValueError as exc:
            # Odpověď mimo uzavřené menu. Selhat má TAH, ne čtení: člověk
            # nabídl relaci, kterou jádro nezná, a má to slyšet hned.
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ nenaučeno: {exc}",), error=str(exc)
            )
        verdict = cascade(
            turn.reading, mood=_mood_of(turn.text), tiers=self.tiers()
        )
        prefix = [
            f"✓ naučeno  {mapping}",
            f"  (platí pro každou stavbu {turn.shape_name}, ne jen pro tuhle větu)",
        ]
        if verdict.decided is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(*prefix, "→ větu se ani tak přečíst nepodařilo"),
                trace=verdict.trace,
            )
        return self._settle(index, turn, verdict.decided.predication, prefix)

    def _declare_distinct(self, index: int, turn: Turn) -> TurnResult:
        """`!≠` — „ti dva nejsou tíž".

        Je to obyčejný `attach` negovaného `same_as`; jádro ho umělo už
        dřív. Vlastní druh tahu má proto, že **jeho účinek je jiný než
        u faktu**: od 0.1.6 tím sporná hrana vypadne z uzávěru (M‑1),
        a to je věc, kterou má transkript říct nahlas.
        """
        assert turn.subject is not None and turn.other is not None
        denial = same_as_of(turn.subject, turn.other).complement()
        try:
            sid = self.kb.attach(denial, provenance=f"tah {index}")
        except (AttachError, SortError) as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ nezapsáno: {exc}",), error=str(exc)
            )
        lines = [f"✓ zapsáno [{sid}]  {denial}"]
        if self.kb.view().index.identity_is_disputed(
            turn.subject.id, turn.other.id
        ):
            lines.append(
                f"  [SPOR: o totožnosti {turn.subject.id} a {turn.other.id} "
                f"teď báze tvrdí obojí — přes tuhle identitu nic nevede, "
                f"dokud jednu stranu neodvoláš]"
            )
        return TurnResult(index=index, turn=turn, lines=tuple(lines), statement_id=sid)

    def _split(self, index: int, turn: Turn) -> TurnResult:
        """`!÷` — „tohle byli dva různí lidé".

        **Atomický tah.** Odpojit výroky a teprve pak je přesměrovat by
        znamenalo, že mezi tím báze tvrdí něco, co nikdo neřekl.

        **Deaktivace, ne mazání** (§ 8). Původní výroky zůstávají
        v historii se svým `revoke` důvodem; nové nesou provenienci
        ukazující na TENHLE tah, ne na původní „řekls" — jinak by
        transkript tvrdil, že člověk řekl něco, co za něj odvodil systém.

        Kam který výrok patří, systém **neví** a nehádá: rozdělení mu dá
        dvě jména a všechny dosavadní výroky přepíše na to PRVNÍ, protože
        druhé teprve začíná existovat. Rozdělit je mezi ně je další
        rozhodnutí člověka, ne tenhle tah.
        """
        assert turn.subject is not None and turn.split_into is not None
        first, second = turn.split_into
        original = turn.subject
        touched = [
            statement
            for statement in self.kb.active()
            if isinstance(statement.formula, Atom)
            and any(r.target.id == original.id for r in statement.formula.roles)
        ]
        if not touched:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(
                    f"✗ nerozděleno: o uzlu {original.id} žádný aktivní "
                    f"výrok není, takže není co rozdělovat",
                ),
                error="nic k rozdělení",
            )
        # Obě půlky dostanou PŮVODNÍ JMÉNO jako doložený fakt. Bez toho by
        # se další zmínka téhož jména tiše ztotožnila s jednou z nich —
        # nebo, což je horší, založila TŘETÍ uzel a tvářila se, že se nic
        # nestalo. Jméno v bázi je to jediné, co kanonizaci umožní zjistit,
        # že už není jednoznačná.
        named: list[str] = []
        for fresh in (first, second):
            named.append(
                self.kb.attach(
                    atom(
                        P_NAME,
                        role("of", Entity(fresh)),
                        role("value", Label(original.id)),
                    ),
                    provenance=f"tah {index}: rozdělení {original.id}",
                )
            )
        moved: list[str] = []
        for statement in touched:
            formula = statement.formula
            assert isinstance(formula, Atom)
            self.kb.revoke(statement.id, f"rozdělení uzlu {original.id} (tah {index})")
            sid = self.kb.attach(
                _rename_node(formula, original.id, first),
                provenance=f"tah {index}: rozdělení {original.id} → {first}",
            )
            moved.append(sid)
        return TurnResult(
            index=index,
            turn=turn,
            lines=(
                f"✓ rozděleno  {original.id} → {first}, {second}",
                f"  [{len(touched)} výroků přepsáno na {first}: {', '.join(moved)}]",
                f"  [obě půlky nesou jméno {original.id!r}, takže se ho "
                f"kanonizace příště nebude domýšlet]",
                f"  (původní výroky zůstávají v historii, jen neplatí; "
                f"{second} zatím nic neříká — co o něm platí, musíš říct ty)",
            ),
            derived=(*named, *moved),
        )

    def _revoke(self, index: int, turn: Turn) -> TurnResult:
        assert turn.statement_id is not None
        try:
            revoked = self.kb.revoke(turn.statement_id, turn.reason)
        except KeyError as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ {exc}",), error=str(exc)
            )
        lines = [f"✓ odvoláno [{', '.join(revoked)}]  důvod: {turn.reason}"]
        lines.append("  (výroky zůstávají v historii, jen neplatí)")
        return TurnResult(index=index, turn=turn, lines=tuple(lines), derived=tuple(revoked))

    def _synthesis(self, subject: Term) -> tuple[list[str], list[str]]:
        """§ 6.5 — složený popis uzlu z doložených členství a jmen.

        Odpověď na „Co má Filip?" má být SYNTÉZA nashromážděného popisu
        (členství + vlastnost + jméno), ne echo jedné věty. Vše se bere
        z doložených struktur, takže každý údaj má citovatelný výrok.
        """
        view = self.kb.view()
        traits: list[str] = []
        cited: list[str] = []
        for group_id in view.known_groups_of(subject.id):
            proof = view.member_proof(subject.id, group_id)
            if proof is None:
                continue
            traits.append(group_id)
            cited.extend(proof.leaves())
        canonical = view.canonical(subject.id)
        for statement in self.kb.active():
            formula = statement.formula
            if isinstance(formula, Rule) or formula.predicate != P_NAME:
                continue
            target = formula.get_role("of")
            value = formula.get_role("value")
            if target is None or value is None:
                continue
            if view.canonical(target.target.id) == canonical:
                traits.append(f"jménem {value.target.id}")
                cited.append(statement.id)
        return traits, sorted(set(cited))

    def _describe(self, index: int, turn: Turn) -> TurnResult:
        assert turn.subject is not None
        traits, cited = self._synthesis(turn.subject)
        lines = (
            [f"→ {turn.subject.id}: " + ", ".join(traits)]
            if traits
            else ["→ NEVÍM", f"  chybí vědět: cokoli o {turn.subject.id}"]
        )
        if cited:
            lines.append(f"[doloženo: {', '.join(cited)}]")
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=QueryStatus.PROVEN_TRUE if traits else QueryStatus.UNKNOWN,
        )

    def _enumerate(self, index: int, turn: Turn) -> TurnResult:
        assert turn.query is not None
        solutions = self.engine().solutions(turn.query)
        lines: list[str] = []
        cited: set[str] = set()
        found: list[str] = []
        for binding, proof in solutions:
            term = binding.get(turn.variable)
            if term is None:
                continue
            traits, node_cited = self._synthesis(term)
            found.append(term.id)
            lines.append(
                f"→ {term.id}: " + (", ".join(traits) if traits else "(bez popisu)")
            )
            cited.update(node_cited)
            cited.update(proof.leaves())
        if not found:
            lines = ["→ NEVÍM", f"  chybí vědět: {turn.query}"]
        elif cited:
            lines.append(f"[doloženo: {', '.join(sorted(cited))}]")
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=QueryStatus.PROVEN_TRUE if found else QueryStatus.UNKNOWN,
        )

    def _confirm(self, index: int, turn: Turn) -> TurnResult:
        if self._pending is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=("(nebylo na co odpovědět)",),
                error="žádná nabídka nečeká na potvrzení",
            )
        rule = self._pending
        self._pending = None
        if not turn.accepted:
            return TurnResult(
                index=index, turn=turn, lines=(f"✓ nabídka {rule.id} odmítnuta",)
            )
        try:
            sid = self.kb.attach(rule, provenance=f"potvrzeno tahem {index}")
        except AttachError as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ nezapsáno: {exc}",), error=str(exc)
            )
        return TurnResult(
            index=index,
            turn=turn,
            lines=(f"✓ zapsáno [{sid}]  {rule}",),
            statement_id=sid,
        )

    # -- renderování -------------------------------------------------------

    def _offer_bridge(
        self, turn: Turn, result: QueryResult, lines: list[str]
    ) -> Rule | None:
        """`awaiting_rule_confirmation` — chybějící článek se nehádá,
        nabídne se k potvrzení (§ 6.6 zadání, I‑7)."""
        if turn.bridge is None or result.status is not QueryStatus.UNKNOWN:
            return None
        self._pending = turn.bridge
        lines.append(f"  mám z toho usoudit pravidlo {turn.bridge.id}?")
        lines.append(f"    {turn.bridge}")
        return turn.bridge

    def _render_answer(
        self, report: AuditReport, *, gap_lines: Sequence[str] = ()
    ) -> list[str]:
        lines = [f"→ {report.verdict}"]
        if report.reason:
            lines.append("  protože:")
            lines.extend(f"  {line.render()}" for line in report.reason)
        if report.conflict is not None:
            positive, negative = report.conflict
            lines.append("  důkaz pro:")
            lines.extend(f"  {line.render()}" for line in positive)
            lines.append("  důkaz proti:")
            lines.extend(f"  {line.render()}" for line in negative)
        for item in gap_lines or report.gap:
            lines.append(f"  {item}")
        if report.cited:
            lines.append(f"[doloženo: {', '.join(report.cited)}]")
        return lines

    def _render_reason(self, proof: Proof | None) -> list[str]:
        if proof is None:
            return []
        lines = ["  protože:"]
        lines.extend(
            f"  {line.render()}" for line in self.presenter.render_proof(proof)
        )
        lines.append(f"[doloženo: {', '.join(sorted(proof.leaves()))}]")
        return lines
