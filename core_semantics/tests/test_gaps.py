"""`GapFinder` — „Proč nevíš?" (§ 6.8).

Testuje se to, co dělá rozdíl mezi rozborem mezery a zopakovanou otázkou:
že report ukáže **chybějící článek** a **které pravidlo by to dalo**, a že
neslibuje minimalitu, kterou § 12 nesankcionuje.
"""

from __future__ import annotations

from decimal import Decimal

from core_semantics.ast import (
    Comparator,
    Entity,
    Group,
    Label,
    P_ROLE_EXISTS,
    Quantifier,
    Sort,
    Value,
    Variable,
    atom,
    measure_of,
    member_of,
    role,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.gaps import GapFinder
from core_semantics.storage import KnowledgeBase

FOR_ALL = Quantifier.FOR_ALL
EXISTS = Quantifier.EXISTS
SELF = Quantifier.SELF


def test_nothing_is_open_when_the_query_holds() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    report = GapFinder(Engine(kb)).explain(
        member_of(Entity("e17"), Group("spisovatel"))
    )
    assert report.open_goals == ()


def test_missing_chain_link_is_named() -> None:
    """Dřív se vrátil jen zopakovaný dotaz. Report teď ukáže, co by řetěz
    uzavřelo: „vím, že Hrabal je spisovatel; chybí vědět: spisovatel ⊆
    dramatik"."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Hrabal"), Group("spisovatel")))
    report = GapFinder(Engine(kb)).explain(
        member_of(Entity("Hrabal"), Group("dramatik"))
    )
    rendered = "\n".join(report.render())
    assert "Hrabal patří do spisovatel" in rendered
    assert any(
        goal.atom == subset_of(Group("spisovatel"), Group("dramatik"))
        for goal in report.open_goals
    )
    assert any("uzávěr member*" == goal.via for goal in report.open_goals)


def test_report_says_when_no_rule_produces_the_goal() -> None:
    """Užitečná informace sama pro sebe: tohle prostě nikdo nevyrábí."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e1"), Group("auto")))
    report = GapFinder(Engine(kb)).explain(
        atom("jezdit", role("who", Entity("e1")))
    )
    assert report.open_goals
    assert any("žádné pravidlo" in goal.via for goal in report.open_goals)


def test_blocking_body_literal_is_reported_with_its_rule() -> None:
    """„Pravidlo p3 by to dalo, ale chybí omezení" je použitelná informace;
    „chybí vědět: <dotaz>" není."""
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("auto"), Group("DP")))
    jezdit = kb.attach(
        atom(
            "jezdit",
            role("who", Group("DP"), FOR_ALL),
            role("via", Group("dálnice"), EXISTS),
        )
    )
    relation = Variable("R")
    road = Variable("P", expects=Sort.GROUP)
    limit = Variable("V")
    kb.attach_rule(
        rule_id="p3",
        head=measure_of(relation, Comparator.LE, limit),
        body=(
            member_of(relation, Group("jezdit")),
            atom(
                P_ROLE_EXISTS,
                role("of", relation),
                role("name", Label("via")),
                role("filler", road, SELF),
            ),
            atom(
                "omezení",
                role("of", road, FOR_ALL),
                role("quantity", Label("rychlost")),
                role("limit", limit),
            ),
        ),
    )
    # omezení v bázi CHYBÍ — pravidlo se na něm zasekne
    from core_semantics.ast import RelationInstance

    query = measure_of(
        RelationInstance(jezdit),
        Comparator.LE,
        Value("v130", "rychlost", Decimal(130), "km/h"),
    )
    report = GapFinder(Engine(kb)).explain(query)
    blocked = [goal for goal in report.open_goals if "p3" in goal.via]
    assert blocked, report.render()
    assert blocked[0].atom.predicate == "omezení"


def test_satisfied_rule_reports_nothing_for_that_rule() -> None:
    """Když tělo projde celé, pravidlo mezeru nezpůsobuje — a nesmí se
    v reportu objevit."""
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach(member_of(Entity("e1"), Group("pták")))
    kb.attach_rule(
        rule_id="p_fly",
        head=atom("létat", role("who", x)),
        body=(member_of(x, Group("pták")),),
    )
    engine = Engine(kb)
    # dotaz platí, takže report je prázdný
    assert GapFinder(engine).explain(atom("létat", role("who", Entity("e1")))).open_goals == ()
    # a na jiném prvku se ukáže, který literál blokuje
    report = GapFinder(engine).explain(atom("létat", role("who", Entity("e2"))))
    assert report.open_goals
    assert any(goal.atom.predicate == "member" for goal in report.open_goals)


def test_gap_names_the_fact_and_the_role_that_did_not_match() -> None:
    """Bez tohohle patra hlásil report „žádné pravidlo tohle nevyrábí"
    i tam, kde fakt v bázi JE a chybí jediný článek."""
    from core_semantics.ast import group_diff

    kb = KnowledgeBase()
    kb.attach(subset_of(Group("vrabec"), Group("pták")))
    fact = kb.attach(
        atom(
            "létat",
            role("who", group_diff(Group("pták"), Group("tučňák")), FOR_ALL),
        )
    )
    report = GapFinder(Engine(kb)).explain(
        atom("létat", role("who", Group("vrabec"), FOR_ALL))
    )
    rendered = "\n".join(report.render())
    assert f"fakt {fact}, role who" in rendered


def test_gap_descends_to_what_a_person_can_actually_say() -> None:
    """Dialog E: „chybí subset(vrabec, pták DIFF tučňák)" je pravda, ale
    doplnit se dá až to, co z toho plyne — `disjoint(vrabec, tučňák)`.
    Report proto sestupuje o úroveň dál (zákon 9, dodatek E)."""
    from core_semantics.ast import group_diff

    kb = KnowledgeBase()
    kb.attach(subset_of(Group("vrabec"), Group("pták")))
    kb.attach(
        atom(
            "létat",
            role("who", group_diff(Group("pták"), Group("tučňák")), FOR_ALL),
        )
    )
    report = GapFinder(Engine(kb)).explain(
        atom("létat", role("who", Group("vrabec"), FOR_ALL))
    )
    rendered = "\n".join(report.render())
    assert "disjoint(a:·vrabec, b:·tučňák)" in rendered
    assert "zákon X ⊆ A ∧ disjoint(X,B)" in rendered


def test_gap_names_the_missing_containment_for_places() -> None:
    """W‑5: dialog D je právě o místech a časech. Bez tohohle patra by
    report spadl na obecné „žádné pravidlo tohle nevyrábí", místo aby
    ukázal na roli `kam` a na `contains*`."""
    from core_semantics.ast import Place

    kb = KnowledgeBase()
    kb.attach(
        atom("jel", role("kdo", Entity("Petr")), role("kam", Place("Praha")))
    )
    report = GapFinder(Engine(kb)).explain(
        atom("jel", role("kdo", Entity("Petr")), role("kam", Place("Brno")))
    )
    rendered = "\n".join(report.render())
    assert "contains" in rendered
    assert "role kam" in rendered


def test_gap_names_the_missing_containment_for_intervals() -> None:
    from core_semantics.ast import Interval

    kb = KnowledgeBase()
    kb.attach(
        atom("jel", role("kdo", Entity("Petr")), role("kdy", Interval("pondělí")))
    )
    report = GapFinder(Engine(kb)).explain(
        atom("jel", role("kdo", Entity("Petr")), role("kdy", Interval("týden")))
    )
    rendered = "\n".join(report.render())
    assert "within" in rendered


def test_duplicates_are_removed() -> None:
    """§ 6.8 žádá chybějící premisy **bez duplicit**."""
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach(member_of(Entity("e1"), Group("a")))
    for index in (1, 2):
        kb.attach_rule(
            rule_id=f"p{index}",
            head=atom("cíl", role("who", x)),
            body=(member_of(x, Group("chybí")),),
        )
    report = GapFinder(Engine(kb)).explain(atom("cíl", role("who", Entity("e1"))))
    rendered = report.render()
    assert len(set(rendered)) == len(rendered)


def test_report_admits_when_the_search_was_cut_short() -> None:
    """Mez se přiznává, nezamlčuje."""
    kb = KnowledgeBase()
    finder = GapFinder(Engine(kb), max_depth=0)
    x = Variable("x")
    kb.attach_rule(
        rule_id="p_deep",
        head=atom("cíl", role("who", x)),
        body=(member_of(x, Group("chybí")),),
    )
    report = GapFinder(Engine(kb), max_depth=0).explain(
        atom("cíl", role("who", Entity("e1")))
    )
    assert report.open_goals or report.exhausted
