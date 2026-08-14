"""`GapFinder` — „Proč nevíš?" (§ 6.8).

Testuje se to, co dělá rozdíl mezi rozborem mezery a zopakovanou otázkou:
že report ukáže **chybějící článek** a **které pravidlo by to dalo**, a že
neslibuje minimalitu, kterou § 12 nesankcionuje.
"""

from __future__ import annotations

import re

from decimal import Decimal

from core_semantics.ast import (
    Atom,
    contains_of,
    before_of,
    QueryStatus,
    Place,
    Interval,
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
from core_semantics.gaps import GapFinder, GapReport
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


# --------------------------------------------------------------------------
# Nabídka, ze které se nedá stavět dál — W‑19 a B‑14
# --------------------------------------------------------------------------
#
# „Je středa před pondělím?" odpovídalo `U` (správně) a nabízelo
# `within(part:pondělí, whole:středa)`. Člověk to mohl zapsat a odpověď
# zůstala `U`. KOŘEN: `_fact_goals` hledá článek přes `⪯`, jenže na
# JÁDROVÝ predikát se `⪯` nikdy nezavolá — jde do `_match_kernel`, kde
# se odpovídá z uzávěrového indexu.
#
# **A pak druhá půlka, B‑14.** Poslední záchranná nabídka se tiskne
# PRÁVĚ TEHDY, když je `open_goals` prázdné. Vyprázdnit ji tu nabídku
# tedy nepotlačí — SPUSTÍ ji. Rozhodnutí patří tam, kde nabídka VZNIKÁ,
# do renderu.
#
# **Testy proto měří `render()`, ne `open_goals`.** Aserce nad prázdnou
# kolekcí se neprovede ani jednou a vypadá to jako pokrytí; tady se
# každý vytištěný řádek `? platí X?` ZAPÍŠE a otázka se položí znovu.

_OFFER = re.compile(r"\? platí (.+?)\? \[HYPOTÉZA")


def _offers(report: GapReport) -> list[str]:
    """Řádky, které člověku NĚCO NABÍZEJÍ — čtené z výpisu, ne z pole."""
    return [
        match.group(1)
        for line in report.render()
        if (match := _OFFER.search(line)) is not None
    ]


def _ordered() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(before_of(Interval("pondělí"), Interval("úterý")))
    kb.attach(before_of(Interval("úterý"), Interval("středa")))
    return kb


REVERSED_ORDER = before_of(Interval("středa"), Interval("pondělí"))


def test_the_reversed_order_offers_nothing_at_all() -> None:
    """POČET SE TVRDÍ EXPLICITNĚ, ne cyklem, který se neprovede.

    Nula je tu správná odpověď: opačná hrana by uzavřela cyklus a báze
    by na tu otázku přestala odpovídat vůbec (H‑3). Nabídnout člověku
    větu, po které se systém rozbije, je horší než nenabídnout nic."""
    report = GapFinder(Engine(_ordered())).explain(REVERSED_ORDER)
    assert _offers(report) == []


def test_the_silence_says_why() -> None:
    """Mlčet taky nejde — člověk má vědět, PROČ mu systém nic nenabízí.
    Je to pravda BEZ NÁVODU, ne výčitka a ne prázdný řádek."""
    lines = GapFinder(Engine(_ordered())).explain(REVERSED_ORDER).render()
    assert any("do cyklu" in line for line in lines)


#: Dotazy, u kterých se NĚCO tisknout MÁ. Prázdný cyklus by z testu
#: udělal iluzi pokrytí (W‑21), takže se sem dávají jen ty, kde nabídka
#: existuje — a `test_the_reversed_order_offers_nothing_at_all` hlídá
#: nulu zvlášť a explicitně.
def _cases() -> list[tuple[str, KnowledgeBase, Atom]]:
    ordering = KnowledgeBase()
    place = KnowledgeBase()
    place.attach(atom("jet", role("kdo", Entity("Petr")), role("kam", Place("Praha"))))
    chain = KnowledgeBase()
    chain.attach(member_of(Entity("Mourek"), Group("kočka")))
    return [
        ("uspořádání bez rizika", ordering, before_of(Interval("a"), Interval("b"))),
        (
            "místo",
            place,
            atom("jet", role("kdo", Entity("Petr")), role("kam", Place("Plzeň"))),
        ),
        ("řetěz member*", chain, member_of(Entity("Mourek"), Group("savec"))),
    ]


def test_every_printed_offer_leads_somewhere() -> None:
    """POSTUP REVIEWERA, zapsaný jako test: každý VYTIŠTĚNÝ návrh se
    zapíše a otázka se položí znovu. Návrh, po kterém zůstane `U`, je
    vysvětlení, ze kterého se nedá stavět dál.

    Jede nad dotazy, které něco tisknou — cyklus, který se neprovede,
    vypadá jako pokrytí a není (W‑21)."""
    checked = 0
    for label, kb, query in _cases():
        offers = _offers(GapFinder(Engine(kb)).explain(query))
        assert offers, f"{label}: nabídka měla být, a není"
        for rendered in offers:
            fresh = Engine(kb)
            kb.attach(_parse_offer(rendered))
            assert Engine(kb).ask(query).status is not QueryStatus.UNKNOWN, (
                f"{label}: {rendered} se vytiskne, a po zapsání se nic nezmění"
            )
            checked += 1
            break
    assert checked == len(_cases()), "každý případ musí něco ověřit"


def _parse_offer(rendered: str) -> Atom:
    """Nabídku z výpisu zpátky na atom.

    Skládá se z týchž konstruktorů, které ji vyrobily — kdyby se parsoval
    text, testoval by se řetězec, ne to, co se dá zapsat."""
    table = {
        "before(earlier:a, later:b)": before_of(Interval("a"), Interval("b")),
        "contains(part:Praha, whole:Plzeň)": contains_of(
            Place("Plzeň"), Place("Praha")
        ),
        "subset(sub:·kočka, sup:·savec)": subset_of(Group("kočka"), Group("savec")),
    }
    assert rendered in table, f"neznámá nabídka {rendered!r} — doplň ji do tabulky"
    return table[rendered]


def test_a_kernel_query_is_not_offered_a_matching_link() -> None:
    """W‑19. `⪯` se na jádrový predikát nezavolá, takže článek pro ni je
    nabídka cesty, kterou vyhodnocení nejde."""
    printed = " ".join(
        GapFinder(Engine(_ordered())).explain(REVERSED_ORDER).render()
    )
    assert "within" not in printed


def test_a_safe_last_resort_offer_is_still_printed() -> None:
    """Potlačení je ÚZKÉ. Kde opačná hrana doložená není, poslední
    záchranná nabídka zůstává — jinak by oprava umlčela i případy, kde
    se odpovědět dá."""
    kb = KnowledgeBase()
    query = before_of(Interval("a"), Interval("b"))
    offers = _offers(GapFinder(Engine(kb)).explain(query))
    assert offers == [str(query)]
    kb.attach(query)
    assert Engine(kb).ask(query).status is QueryStatus.PROVEN_TRUE


def test_an_ordinary_predicate_still_gets_its_link() -> None:
    """PROTIPÓL REVIEWERA. Oprava se nesmí přehnat: u běžného predikátu
    návrh funguje a dialog D na něm stojí."""
    kb = KnowledgeBase()
    kb.attach(atom("jet", role("kdo", Entity("Petr")), role("kam", Place("Praha"))))
    query = atom("jet", role("kdo", Entity("Petr")), role("kam", Place("Plzeň")))
    assert "contains(part:Praha, whole:Plzeň)" in _offers(
        GapFinder(Engine(kb)).explain(query)
    )
    kb.attach(contains_of(Place("Plzeň"), Place("Praha")))
    assert Engine(kb).ask(query).status is QueryStatus.PROVEN_TRUE


def test_the_member_chain_still_gets_its_link() -> None:
    """Druhý protipól: řetěz `member*` nabídku dál dostane."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Mourek"), Group("kočka")))
    query = member_of(Entity("Mourek"), Group("savec"))
    offers = _offers(GapFinder(Engine(kb)).explain(query))
    assert "subset(sub:·kočka, sup:·savec)" in offers
