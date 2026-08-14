"""Akceptační dialog D — prostor a čas složené na fakta (§ 6.12).

Zdroj: „Petr jel v pondělí do Prahy. V úterý jel Petr do Brna. Praha je
v Česku. Brno je v Česku."

Co se tu láme: **uspořádání na časové ose** (`before*`) a **obsažení míst**
(`contains*`) složené s rolemi dějů. Alternativní otázka „Kam jel Petr
dřív?" nevrací ano/ne, ale vybraný člen — a rozhoduje ji osa času.

Kalendář je **data**, ne kód (§ 12/6): „pondělí je před úterým" se do báze
zapíše jako fakt, ne zadrátuje do interpretu.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    Entity,
    Interval,
    Place,
    QueryStatus,
    atom,
    before_of,
    contains_of,
    role,
    within_of,
)
from core_semantics.closures import InconsistentOrder
from core_semantics.engine import Engine
from core_semantics.epistemics import query_alt
from core_semantics.storage import KnowledgeBase

MONDAY = Interval("pondělí")
TUESDAY = Interval("úterý")
WEDNESDAY = Interval("středa")
PRAGUE = Place("Praha")
BRNO = Place("Brno")
CZECHIA = Place("Česko")


def _base() -> tuple[KnowledgeBase, str, str]:
    kb = KnowledgeBase()
    # kalendář jako DATA (§ 12/6)
    kb.attach(before_of(MONDAY, TUESDAY))
    kb.attach(before_of(TUESDAY, WEDNESDAY))
    kb.attach(contains_of(CZECHIA, PRAGUE))
    kb.attach(contains_of(CZECHIA, BRNO))
    to_prague = kb.attach(
        atom(
            "jet",
            role("kdo", Entity("Petr")),
            role("kam", PRAGUE),
            role("kdy", MONDAY),
        )
    )
    to_brno = kb.attach(
        atom(
            "jet",
            role("kdo", Entity("Petr")),
            role("kam", BRNO),
            role("kdy", TUESDAY),
        )
    )
    return kb, to_prague, to_brno


# --------------------------------------------------------------------------
# Uspořádání na ose
# --------------------------------------------------------------------------


def test_ordering_is_transitive() -> None:
    kb, _, _ = _base()
    result = Engine(kb).ask(before_of(MONDAY, WEDNESDAY))
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None
    assert any("before*" in line for line in result.proof_tree)


def test_ordering_has_no_reverse_direction() -> None:
    """„Dřív" není symetrické — a absence není negace (I‑21), takže
    obrácený dotaz je `U`, ne `N`."""
    kb, _, _ = _base()
    assert (
        Engine(kb).ask(before_of(WEDNESDAY, MONDAY)).status
        is QueryStatus.UNKNOWN
    )


def test_ordering_is_not_reflexive() -> None:
    """Kdyby uzávěr reflexivitu přidal, splynulo by „dřív" s „nejpozději"."""
    kb, _, _ = _base()
    assert (
        Engine(kb).ask(before_of(MONDAY, MONDAY)).status is QueryStatus.UNKNOWN
    )


def test_time_and_space_do_not_mix() -> None:
    """§ 1: `Place` a `Time` jsou oddělené sorty, každý s vlastním grafem."""
    kb, _, _ = _base()
    view = kb.view()
    assert view.before_proof("Praha", "Brno") is None
    assert view.contains_proof("pondělí", "úterý") is None


# --------------------------------------------------------------------------
# Alternativní otázka nad osou času — jádro dialogu D
# --------------------------------------------------------------------------


def test_which_trip_was_earlier_is_answered_by_a_member() -> None:
    """„Kam jel Petr dřív — do Prahy, nebo do Brna?"

    Odpověď není ano/ne, ale **vybraný člen** (§ 6.2). Rozhoduje osa času:
    pondělí je před úterým."""
    kb, _, _ = _base()
    prague_first = before_of(MONDAY, TUESDAY)
    brno_first = before_of(TUESDAY, MONDAY)
    result = query_alt(Engine(kb), [prague_first, brno_first])
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.chosen == prague_first


def test_without_the_calendar_the_answer_is_unknown() -> None:
    """Bez zapsaného kalendáře osa neexistuje — a systém to přizná."""
    kb = KnowledgeBase()
    kb.attach(contains_of(CZECHIA, PRAGUE))
    result = query_alt(
        Engine(kb),
        [before_of(MONDAY, TUESDAY), before_of(TUESDAY, MONDAY)],
    )
    assert result.status is QueryStatus.UNKNOWN
    assert result.chosen is None


def test_place_containment_still_works_alongside_time() -> None:
    """„Byl Petr v pondělí v Česku?" — role `kam` se čte přes obsažení míst."""
    kb, _, _ = _base()
    query = atom(
        "jet",
        role("kdo", Entity("Petr")),
        role("kam", CZECHIA),
        role("kdy", MONDAY),
    )
    result = Engine(kb).ask(query)
    assert result.status is QueryStatus.PROVEN_TRUE
    assert any("contains*" in line for line in result.proof_tree)


def test_unmentioned_day_stays_unknown() -> None:
    """§ 6.12 dialog D: „Byl Petr ve středu v Česku?" → NEVÍM. Trvání stavů
    systém neumí a nepředstírá to (hranice v1)."""
    kb, _, _ = _base()
    query = atom(
        "jet",
        role("kdo", Entity("Petr")),
        role("kam", CZECHIA),
        role("kdy", WEDNESDAY),
    )
    assert Engine(kb).ask(query).status is QueryStatus.UNKNOWN


# --------------------------------------------------------------------------
# Cyklus v uspořádání — konzervativní default H‑3
# --------------------------------------------------------------------------


def test_contradictory_ordering_refuses_to_answer() -> None:
    """`before(a,b)` i `before(b,a)` dají uzávěrem „všechno je před vším".

    Konzervativní default (H‑3): uzávěr cyklus detekuje a **netiše
    neodpoví**. Zapojení na `CONFLICT` s oběma důkazy je nový druh inference
    v jádře a čeká na rozhodnutí člověka.
    """
    kb = KnowledgeBase()
    kb.attach(before_of(MONDAY, TUESDAY))
    kb.attach(before_of(TUESDAY, MONDAY))
    with pytest.raises(InconsistentOrder, match="odporuje"):
        Engine(kb).ask(before_of(MONDAY, TUESDAY))


def test_a_cycle_elsewhere_does_not_block_unrelated_questions() -> None:
    """Cyklus jinde na ose nemá blokovat nesouvisející otázku — jinak by
    jedna chyba v kalendáři znepoužitelnila celou osu."""
    kb = KnowledgeBase()
    kb.attach(before_of(MONDAY, TUESDAY))
    kb.attach(before_of(TUESDAY, MONDAY))
    kb.attach(before_of(Interval("leden"), Interval("únor")))
    result = Engine(kb).ask(before_of(Interval("leden"), Interval("únor")))
    assert result.status is QueryStatus.PROVEN_TRUE
    assert kb.view().ordering_cycles() == frozenset({"pondělí", "úterý"})


def test_within_and_before_are_different_relations() -> None:
    """„Během" je `within`, „dřív" je `before` — dva grafy, dvě otázky."""
    kb = KnowledgeBase()
    kb.attach(within_of(Interval("týden"), MONDAY))
    kb.attach(before_of(MONDAY, TUESDAY))
    engine = Engine(kb)
    assert engine.ask(within_of(Interval("týden"), MONDAY)).status is (
        QueryStatus.PROVEN_TRUE
    )
    assert engine.ask(before_of(Interval("týden"), MONDAY)).status is (
        QueryStatus.UNKNOWN
    )
