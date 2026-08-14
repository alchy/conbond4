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
    same_as_of,
    AttachError,
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


def test_the_cycle_is_refused_at_the_door() -> None:
    """B‑16. Hrana, která by uzavřela pořadí do kruhu, se NEZAPÍŠE.

    Do téhle změny se zapsala bez námitky a rozbila se až PŘÍŠTÍ otázka —
    výjimkou, která utekla ze `Session.utter` ven. To je nejhorší možná
    chvíle: báze už je v rozbitém stavu a program nemá jak říct, co se
    stalo (I‑1). Selhání zápisu je přitom TAH DIALOGU (§ 9).
    """
    kb = KnowledgeBase()
    kb.attach(before_of(MONDAY, TUESDAY))
    with pytest.raises(AttachError, match="do kruhu"):
        kb.attach(before_of(TUESDAY, MONDAY))


def test_the_refusal_names_the_statements_that_form_the_circle() -> None:
    """„Tohle nejde" bez nich by po člověku chtělo, aby si bázi prošel
    sám — a tah, na který se nedá odpovědět, je k ničemu."""
    kb = KnowledgeBase()
    first = kb.attach(before_of(MONDAY, TUESDAY))
    with pytest.raises(AttachError) as exc:
        kb.attach(before_of(TUESDAY, MONDAY))
    assert first in str(exc.value)


def test_the_base_stays_answerable_after_a_refusal() -> None:
    """Odmítnutí není poškození: báze musí dál odpovídat, jinak by se
    zákaz choval stejně špatně jako ta vada."""
    kb = KnowledgeBase()
    kb.attach(before_of(MONDAY, TUESDAY))
    with pytest.raises(AttachError):
        kb.attach(before_of(TUESDAY, MONDAY))
    assert Engine(kb).ask(before_of(MONDAY, TUESDAY)).status is (
        QueryStatus.PROVEN_TRUE
    )


def test_contradictory_ordering_refuses_to_answer() -> None:
    """`before(a,b)` i `before(b,a)` dají uzávěrem „všechno je před vším".

    Konzervativní default (H‑3): uzávěr cyklus detekuje a **netiše
    neodpoví**. Zapojení na `CONFLICT` s oběma důkazy je nový druh inference
    v jádře a čeká na rozhodnutí člověka.

    **Od B‑16 je to DRUHÁ obrana, ne první.** Veřejné dveře cyklus
    odmítnou; sem se dá dojít jen vnitřním zápisem, který používá
    `add_disjoint` pro svou expanzi. Test proto jde `_attach`em — kdyby
    šel `attach`em, netestoval by uzávěr, ale ten nový zákaz, a H‑3 by
    přestalo být hlídané, aniž by si toho kdo všiml.
    """
    kb = KnowledgeBase()
    kb._attach(before_of(MONDAY, TUESDAY))  # noqa: SLF001
    kb._attach(before_of(TUESDAY, MONDAY))  # noqa: SLF001
    with pytest.raises(InconsistentOrder, match="odporuje"):
        Engine(kb).ask(before_of(MONDAY, TUESDAY))


def test_a_cycle_elsewhere_does_not_block_unrelated_questions() -> None:
    """Cyklus jinde na ose nemá blokovat nesouvisející otázku — jinak by
    jedna chyba v kalendáři znepoužitelnila celou osu."""
    kb = KnowledgeBase()
    kb._attach(before_of(MONDAY, TUESDAY))  # noqa: SLF001
    kb._attach(before_of(TUESDAY, MONDAY))  # noqa: SLF001
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


def test_a_self_loop_is_a_circle_of_one_node() -> None:
    """B‑16, druhá půlka. Hledání „vede už cesta opačným směrem?" smyčku
    na sebe MINULO — u hrany na sebe opačná cesta neexistuje, takže se
    jednouzlový cyklus zapsal a shodil příští otázku, i tu, která s ním
    nesouvisela.

    Není to nová politika: `before` je STRIKTNÍ uspořádání a celé H‑3 na
    tom stojí („z cyklu by uzávěr odvodil, že je všechno před vším").
    Ireflexivita je táž věta, jen o jednom uzlu."""
    kb = KnowledgeBase()
    with pytest.raises(AttachError, match="dřív než ono samo"):
        kb.attach(before_of(MONDAY, MONDAY))


def test_a_self_loop_is_refused_on_an_empty_base_too() -> None:
    """Odmítá se BEZ OHLEDU na to, co v bázi je — proto nemá co jmenovat:
    kruh netvoří žádný dřívější výrok, tvoří ho ta hrana sama se sebou."""
    kb = KnowledgeBase()
    kb.attach(before_of(MONDAY, TUESDAY))
    with pytest.raises(AttachError, match="dřív než ono samo"):
        kb.attach(before_of(TUESDAY, TUESDAY))


def test_the_base_survives_a_refused_self_loop() -> None:
    """Odmítnutí nesmí bázi poškodit: hned po něm musí jít zapsat i
    odpovědět. Dřív se po `before(X, X)` rozbily i dotazy, které s tou
    větou nesouvisely."""
    kb = KnowledgeBase()
    with pytest.raises(AttachError):
        kb.attach(before_of(MONDAY, MONDAY))
    kb.attach(before_of(MONDAY, TUESDAY))
    assert Engine(kb).ask(before_of(MONDAY, TUESDAY)).status is (
        QueryStatus.PROVEN_TRUE
    )


def test_the_identity_side_is_a_known_limit() -> None:
    """W‑22, ZAPSANÁ MEZ, ne hotová věc.

    Kruh jde uzavřít i ZE STRANY IDENTITY: `same_as`, které dva uzly
    sceluje, zábranu na hraně obejde. Z ČEŠTINY se tam dnes dojít nedá —
    „Středa je pondělí." se čte jako spona a systém se ptá, jestli jde
    o `member`, `subset`, nebo `disjoint`.

    Test to FIXUJE JAKO MEZ, aby se nezapomnělo: až se na to sáhne,
    ukáže se, jestli zábrana patří NA HRANU, nebo NA STAV GRAFU. Kdyby
    se to jednou spravilo, tenhle test spadne — a to je jeho účel."""
    kb = KnowledgeBase()
    kb.attach(before_of(MONDAY, TUESDAY))
    kb.attach(same_as_of(TUESDAY, MONDAY))  # zábrana na hraně to nevidí
    with pytest.raises(InconsistentOrder):
        Engine(kb).ask(before_of(MONDAY, TUESDAY))
