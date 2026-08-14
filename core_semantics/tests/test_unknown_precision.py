"""Proč padlo `U` — A‑27.

Všechny dosavadní metriky (§ 10) měří, co systém UDĚLAL. Žádná neměří,
co udělat MOHL a neudělal — a systém, který je přehnaně opatrný, má
přitom skvělou přesnost a je prakticky k ničemu.

**MĚŘÍ SE DŮVOD, NE POČET.** `U` je legitimní verdikt; otevřený svět bez
UNA znamená, že o většině věcí opravdu nic nevíme. Snižovat počet `U`
hádáním by bylo horší než neměřit nic, takže tenhle modul žádné skóre
k minimalizaci nemá a mít nesmí: číslo, které jde vylepšit, se dřív nebo
později vylepšovat začne.

Jedna kategorie je VADA, ne nález: `RECALL_FAILURE` znamená, že tvrzení
v bázi JE a systém ho přesto nenašel. Přesně to byla G‑3.
"""

from __future__ import annotations

import inspect

from core_semantics.ast import (
    Atom,
    Entity,
    Group,
    Interval,
    Place,
    Quantifier,
    QueryStatus,
    atom,
    before_of,
    complete_of,
    contains_of,
    group_and,
    group_or,
    member_of,
    role,
    same_as_of,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.storage import KnowledgeBase
from core_semantics.tests.dialogues import DIALOGUES
from core_semantics.tests._console import echo
from core_semantics import unknown_precision
from core_semantics.unknown_precision import (
    Diagnosis,
    UnknownReason,
    defects,
    diagnose,
    render,
    survey,
)

SELF = Quantifier.SELF


# --------------------------------------------------------------------------
# Rozklad podle důvodu
# --------------------------------------------------------------------------


def test_a_decided_query_is_not_part_of_the_breakdown() -> None:
    """Dotaz s verdiktem `A`, `N` nebo `CONFLICT` do rozkladu `U` nepatří
    vůbec — míchat ho tam by ředilo právě to, co se měří."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Filip"), Group("člověk")))
    assert diagnose(Engine(kb), member_of(Entity("Filip"), Group("člověk"))) is None


def test_nothing_stated_is_the_cleanest_unknown() -> None:
    """Nejčistší `U`, jaké v otevřeném světě existuje."""
    found = diagnose(Engine(KnowledgeBase()), member_of(Entity("x"), Group("g")))
    assert found is not None
    assert found.reason is UnknownReason.NOT_STATED
    assert not found.is_defect


def test_a_named_missing_link_is_a_learning_candidate() -> None:
    """Hledání mělo cestu a chyběl na ní článek — `GapFinder` ho jmenuje,
    takže je to zároveň legitimní `U` a nejlepší kandidát na učení."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Mourek"), Group("kočka")))
    found = diagnose(Engine(kb), member_of(Entity("Mourek"), Group("savec")))
    assert found is not None
    assert found.reason is UnknownReason.MISSING_LINK
    assert found.detail, "článek se musí JMENOVAT, jinak se na něj nedá odpovědět"


def test_a_disputed_identity_is_its_own_reason() -> None:
    """`U` je tu správně, ale příčina NENÍ nedostatek důkazu — je to spor,
    který má rozhodnout člověk. Slít to s ostatními by znamenalo poslat
    ho shánět fakta, která už má."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("a"), Group("g")))
    kb.attach(same_as_of(Entity("a"), Entity("b")))
    kb.attach(same_as_of(Entity("a"), Entity("b")).complement())
    found = diagnose(Engine(kb), member_of(Entity("b"), Group("g")))
    assert found is not None
    assert found.reason is UnknownReason.DISPUTED_IDENTITY


# --------------------------------------------------------------------------
# VADA: v bázi to je, ale nenašlo se
# --------------------------------------------------------------------------


class _AmnesiacEngine:
    """Engine, který na všechno odpoví `U`, ať má v bázi cokoli.

    Vada `RECALL_FAILURE` dnes v systému NENÍ — a právě proto se detektor
    nedá pinnout na skutečném enginu. Kdyby se testoval jen tím, že nic
    nenajde, prošel by i tehdy, kdyby přestal hledat úplně. Tenhle stub
    je proto součást měření, ne obcházení: říká, že detektor takový stav
    POZNÁ, až nastane.
    """

    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def ask(self, query: Atom) -> object:
        class _Result:
            status = QueryStatus.UNKNOWN

        return _Result()


def test_a_stated_fact_answered_unknown_is_a_defect() -> None:
    """G‑3 v podobě metriky. Neúplná sada zákonů je přiznaná mez a dá `U`
    právem; tohle je selhání PAMĚTI — odpověď „nevím" na tvrzení, které
    někdo řekl a které leží zapsané."""
    kb = KnowledgeBase()
    sid = kb.attach(subset_of(Group("auto"), group_and(Group("a"), Group("b"))))
    found = diagnose(
        _AmnesiacEngine(kb),  # type: ignore[arg-type]
        subset_of(Group("auto"), group_and(Group("a"), Group("b"))),
    )
    assert found is not None
    assert found.reason is UnknownReason.RECALL_FAILURE
    assert found.is_defect
    assert sid in found.detail, "vada musí ukázat NA TEN výrok, ne jen říct, že je"


def test_the_defect_check_compares_formulas_not_derivability() -> None:
    """Cokoli volnějšího by z metriky udělalo DRUHÝ EVALUÁTOR — a ten by
    měl vlastní chyby, o kterých by nikdo nevěděl. Doslovná shoda stačí:
    přesně na ní padla G‑3."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Mourek"), Group("kočka")))
    found = diagnose(Engine(kb), member_of(Entity("Mourek"), Group("savec")))
    assert found is not None
    assert found.reason is not UnknownReason.RECALL_FAILURE, (
        "odvoditelnost NENÍ přítomnost: to, co z báze plyne, v ní ležet "
        "nemusí — a metrika, která by to slila, by měřila vlastní domněnku"
    )


KERNEL_SHAPES: dict[str, Atom] = {
    "member": member_of(Entity("e"), Group("g")),
    "subset": subset_of(Group("a"), Group("b")),
    "subset nad algebrou": subset_of(Group("a"), group_and(Group("x"), Group("y"))),
    "member nad algebrou": member_of(Entity("e"), group_or(Group("x"), Group("y"))),
    "contains": contains_of(Place("p"), Place("q")),
    "before": before_of(Interval("i"), Interval("j")),
    "same_as": same_as_of(Entity("e"), Entity("f")),
    "complete": complete_of(Group("g")),
    "vztah": atom("mít", role("kdo", Entity("Jan")), role("co", Group("auto"), SELF)),
}


def test_no_stated_fact_is_forgotten_in_any_kernel_shape() -> None:
    """MĚŘENÍ, ne kontrola typů: každý jádrový tvar se zapíše a hned se
    na něj zeptá. Kdyby některý dal `U`, je to bloker — a tenhle test je
    to místo, kde se to pozná dřív než na živé větě."""
    for label, formula in KERNEL_SHAPES.items():
        kb = KnowledgeBase()
        kb.attach(formula)
        found = diagnose(Engine(kb), formula)
        assert found is None or not found.is_defect, f"{label}: {found}"


# --------------------------------------------------------------------------
# Co metrika NESMÍ
# --------------------------------------------------------------------------


def test_the_module_offers_no_score_to_minimise() -> None:
    """Číslo, které jde vylepšit, se dřív nebo později vylepšovat začne —
    a vylepšit počet `U` jde jen hádáním. Modul proto žádnou souhrnnou
    hodnotu nevrací a tenhle test to drží: měří se DŮVOD, ne POČET."""
    public = {
        name
        for name, value in vars(unknown_precision).items()
        if not name.startswith("_")
        and inspect.isfunction(value)
        and value.__module__ == unknown_precision.__name__
    }
    assert public == {"diagnose", "survey", "defects", "render"}
    for name in ("score", "rate", "ratio", "precision", "total"):
        assert not any(name in symbol.lower() for symbol in public)


def test_the_breakdown_does_not_sum_anything_up() -> None:
    """Ani ve výpisu: kategorie se nesčítají do jednoho čísla, protože by
    se to začalo srovnávat mezi běhy."""
    kb = KnowledgeBase()
    lines = render(survey(Engine(kb), (member_of(Entity("x"), Group("g")),)))
    assert not any("celkem" in line.lower() for line in lines)


def test_the_reason_is_derived_only_from_what_was_really_found() -> None:
    """Metrika, která by si sama odvozovala, co „mělo jít dokázat", by
    měřila vlastní domněnku. Rozklad proto stojí jen na `GapFinder`
    a na tom, co v bázi doopravdy leží."""
    source = inspect.getsource(unknown_precision.diagnose)
    assert "GapFinder" in source
    assert "kb.active()" in inspect.getsource(unknown_precision._stated)


# --------------------------------------------------------------------------
# Rozklad na zapsaných dialozích
# --------------------------------------------------------------------------


def _dialogue_unknowns() -> tuple[Diagnosis, ...]:
    from core_semantics.oracle import RecordedOracle
    from core_semantics.session import Session

    from core_semantics.session import TurnResult
    from core_semantics.tests.dialogues import Step
    from core_semantics.tests.test_golden_dialogues import _run

    found: list[Diagnosis] = []
    for dialogue in DIALOGUES:
        session = Session(lexicon=dialogue.lexicon())
        oracle = RecordedOracle(dialogue.recordings())
        done: list[tuple[Step, TurnResult]] = []
        for step in dialogue.steps:
            # Kroky, které jsou TAH a ne věta, se přehrávají stejným
            # runnerem jako v akceptační sadě — jinak by rozklad `U`
            # měřil jinou posloupnost než gate.
            result = _run(session, oracle, step, done)
            done.append((step, result))
            if result.status is not QueryStatus.UNKNOWN:
                continue
            if result.predication is None:
                continue  # nepřečtená věta není odpověď `U`
            from core_semantics.grounding import ground

            grounded = ground(result.predication, session.kb.view())
            if grounded.formula is None:
                continue
            item = diagnose(session.engine(), grounded.formula)
            if item is not None:
                found.append(item)
    return tuple(found)


def test_no_dialogue_answer_is_a_recall_failure() -> None:
    """BLOKER, kdyby padl: `U` na akceptačním dialogu smí znamenat cokoli
    kromě „v bázi to je, jen se to nenašlo"."""
    assert defects(_dialogue_unknowns()) == ()


def test_unknown_precision_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("PROČ PADLO `U` — A‑27")
    echo("=" * 72)
    echo("Měří se DŮVOD, ne POČET: `U` je legitimní verdikt a snižovat")
    echo("jejich počet hádáním by bylo horší než neměřit nic.")
    echo("")
    echo("» jádrové tvary: zapiš a hned se zeptej")
    for label, formula in KERNEL_SHAPES.items():
        kb = KnowledgeBase()
        kb.attach(formula)
        found = diagnose(Engine(kb), formula)
        verdict = "odpovězeno" if found is None else f"VADA {found.reason.value}"
        echo(f"   {label:22} {verdict}")
    echo("")
    echo("» akceptační dialogy")
    for line in render(_dialogue_unknowns()):
        echo(f"   {line}")
    echo("=" * 72)
