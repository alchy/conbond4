"""Sporná identita se v uzávěru nepoužije — M‑1.

Nález z dodatku M: `¬same_as(A,B)` vedle `same_as(A,B)` dalo na přímou
otázku `CONFLICT`, ale uzávěr hranu **dál používal** — takže `bydli(B)`
odpovědělo `A` přes identitu, o které báze ví, že je sporná.

Je to I‑1 v nejhorší podobě: systém si mezi dvěma neslučitelnými tvrzeními
vybral, které platí, a nikomu to neřekl. A bez opravy by kanonizace jmen
z Q1 slibovala ochranu, kterou uzávěr nectí.

**Odebírá se POUŽITÍ hrany, ne výrok.** Přímá otázka musí dál vracet
`CONFLICT` — spor je skutečný a hlásí se (I‑3).
"""

from __future__ import annotations

from core_semantics.ast import (
    Entity,
    Group,
    QueryStatus,
    atom,
    member_of,
    role,
    same_as_of,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.gaps import GapFinder
from core_semantics.storage import KnowledgeBase
from core_semantics.tests._console import echo

P1, P2 = Entity("P1"), Entity("P2")
LIVES = atom("bydli", role("kdo", P1))
ASKED = atom("bydli", role("kdo", P2))


def disputed() -> KnowledgeBase:
    """Báze, která o téže identitě tvrdí obojí."""
    kb = KnowledgeBase()
    kb.attach(same_as_of(P1, P2).complement())
    kb.attach(LIVES)
    kb.attach(same_as_of(P1, P2))
    return kb


def agreed() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(LIVES)
    kb.attach(same_as_of(P1, P2))
    return kb


def test_facts_do_not_flow_through_a_disputed_identity() -> None:
    """Jádro nálezu M‑1. Dřív `A`, teď `U` — a `U` je pravda: dokud spor
    trvá, nevíme, jestli jsou to tíž."""
    assert Engine(disputed()).ask(ASKED).status is QueryStatus.UNKNOWN


def test_the_same_question_answers_yes_without_the_dispute() -> None:
    """Kontrola, že se neodebralo víc, než mělo — bez sporu identita
    funguje dál."""
    assert Engine(agreed()).ask(ASKED).status is QueryStatus.PROVEN_TRUE


def test_the_direct_question_still_reports_the_conflict() -> None:
    """Odebírá se POUŽITÍ hrany, ne výrok. Kdyby zmizel i z přímé
    odpovědi, systém by spor zametl místo aby ho ohlásil (I‑3)."""
    result = Engine(disputed()).ask(same_as_of(P1, P2))
    assert result.status is QueryStatus.CONFLICT


def test_order_of_writing_does_not_matter() -> None:
    """Determinismus (I‑4): `¬same_as` může v bázi ležet až ZA `same_as`
    a uzávěr musí dopadnout stejně."""
    kb = KnowledgeBase()
    kb.attach(LIVES)
    kb.attach(same_as_of(P1, P2))
    kb.attach(same_as_of(P1, P2).complement())
    assert Engine(kb).ask(ASKED).status is QueryStatus.UNKNOWN


def test_dispute_is_symmetric() -> None:
    """`¬same_as(A,B)` popírá i `same_as(B,A)` — identita je symetrická
    a závěr nesmí viset na tom, v jakém pořadí to člověk vyslovil."""
    kb = KnowledgeBase()
    kb.attach(same_as_of(P2, P1).complement())
    kb.attach(LIVES)
    kb.attach(same_as_of(P1, P2))
    assert Engine(kb).ask(ASKED).status is QueryStatus.UNKNOWN


def test_only_the_disputed_edge_is_withdrawn() -> None:
    """Spor o jednu dvojici nesmí zneplatnit identitu jinde v bázi."""
    kb = disputed()
    other, twin = Entity("Q1"), Entity("Q2")
    kb.attach(same_as_of(other, twin))
    kb.attach(atom("bydli", role("kdo", other)))
    assert Engine(kb).ask(atom("bydli", role("kdo", twin))).status is (
        QueryStatus.PROVEN_TRUE
    )


def test_dispute_also_stops_the_bridge_through_other_closures() -> None:
    """Hrana identity se vkládá i do `subset`/`contains`/`within`/`before`,
    aby uměla přemostit řetěz uprostřed. Sporná hrana se tam nesmí dostat
    taky — jinak by se zákaz obešel jinou cestou."""
    kb = KnowledgeBase()
    a, b, sup = Group("A"), Group("B"), Group("Nad")
    kb.attach(same_as_of(a, b).complement())
    kb.attach(subset_of(b, sup))
    kb.attach(same_as_of(a, b))
    kb.attach(member_of(Entity("x"), a))
    assert Engine(kb).ask(member_of(Entity("x"), sup)).status is (
        QueryStatus.UNKNOWN
    )


def test_the_gap_says_why_instead_of_just_shrugging() -> None:
    """Mezera, kterou nejde vysvětlit, je skoro tak špatná jako tichá
    odpověď (I‑14). Pád z `A` na `U` musí mít důvod k přečtení."""
    engine = Engine(disputed())
    report = GapFinder(engine).explain(ASKED)
    assert report.disputed == (("P1", "P2"),)
    assert any("protiřečí" in line for line in report.render())


def test_unrelated_disputes_are_not_dumped_into_the_answer() -> None:
    """U velké báze by výpis všech sporů utopil ten jediný, na kterém
    odpověď opravdu ztroskotala."""
    kb = disputed()
    kb.attach(same_as_of(Entity("R1"), Entity("R2")).complement())
    kb.attach(same_as_of(Entity("R1"), Entity("R2")))
    report = GapFinder(Engine(kb)).explain(ASKED)
    assert report.disputed == (("P1", "P2"),)


def test_revoking_one_side_restores_the_edge() -> None:
    """Spor je stav báze, ne trvalá známka. Odvolání jedné strany má
    identitu vrátit do hry — jinak by se rozhodnutí nedalo opravit."""
    kb = KnowledgeBase()
    denial = kb.attach(same_as_of(P1, P2).complement())
    kb.attach(LIVES)
    kb.attach(same_as_of(P1, P2))
    assert Engine(kb).ask(ASKED).status is QueryStatus.UNKNOWN
    kb.revoke(denial, "ukázalo se, že jsou to tíž")
    assert Engine(kb).ask(ASKED).status is QueryStatus.PROVEN_TRUE


def test_disputed_identity_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("SPORNÁ IDENTITA SE V UZÁVĚRU NEPOUŽIJE — M‑1")
    echo("=" * 72)
    engine = Engine(disputed())
    echo("\nbáze:  ¬same_as(P1,P2) · bydli(kdo:P1) · same_as(P1,P2)")
    echo(f"\n? same_as(P1,P2)   → {engine.ask(same_as_of(P1, P2)).status.value}")
    echo(f"? bydli(kdo:P2)    → {engine.ask(ASKED).status.value}")
    for line in GapFinder(engine).explain(ASKED).render():
        echo(f"   {line}")
    echo("\n" + "=" * 72)
