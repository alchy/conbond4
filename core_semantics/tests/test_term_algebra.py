"""Termová algebra § 3.0 a § 2 — fáze F0.7, akceptační sada T40–T44.

`t AND t | t OR t | t DIFF t` jsou plnohodnotné termy použitelné v rolích.
Vyhodnocení je v § 5.2.1: `D1` a `D2` se nemění, rozšiřuje se jen doména
uzávěrů `member*` a `subset*`.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    CycleDetected,
    Entity,
    Group,
    GroupAnd,
    GroupDiff,
    GroupOr,
    Quantifier,
    QueryStatus,
    SortError,
    Variable,
    atom,
    group_and,
    group_diff,
    group_or,
    member_of,
    role,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.storage import KnowledgeBase

A = Group("a")
B = Group("b")
C = Group("c")
SELF = Quantifier.SELF
FOR_ALL = Quantifier.FOR_ALL


# --------------------------------------------------------------------------
# T40 — kanonizace
# --------------------------------------------------------------------------


def test_and_and_or_are_canonical_but_diff_is_not() -> None:
    """Bez kanonizace by `A AND B` a `B AND A` byly dva termy téhož
    významu — rozbila by se deduplikace i kanonický důkaz. `DIFF` naopak
    komutativní není a kanonizovat se NESMÍ."""
    assert group_and(A, B) == group_and(B, A)
    assert group_or(A, B) == group_or(B, A)
    assert group_diff(A, B) != group_diff(B, A)


def test_nested_same_operator_is_flattened_and_deduplicated() -> None:
    assert group_and(group_and(A, B), C) == group_and(A, B, C)
    assert group_and(A, A) is A  # jednoprvkový průnik je ten prvek sám
    assert isinstance(group_and(A, B), GroupAnd)
    assert isinstance(group_or(A, B), GroupOr)
    assert isinstance(group_diff(A, B), GroupDiff)


def test_identifier_is_stable_and_derived_from_operands() -> None:
    """`dependency_key` i `_unifies` klíčují na `.id`, takže algebraický
    term musí mít id deterministicky odvozené z operandů."""
    assert group_and(B, A).id == "(a AND b)"
    assert group_diff(A, B).id == "(a DIFF b)"
    assert group_or(A, B).id == group_or(B, A).id


def test_algebraic_operands_must_be_groups() -> None:
    with pytest.raises(SortError):
        from core_semantics.ast import as_group_terms

        as_group_terms((Entity("e1"),), "test")


# --------------------------------------------------------------------------
# T41 — algebraický term v roli
# --------------------------------------------------------------------------


def test_algebraic_term_is_a_well_formed_role_filler() -> None:
    """§ 5.2.1 / C‑3: term má `SORT = GROUP`, takže na roli potřebuje
    kvantifikátor stejně jako atomická skupina."""
    filler = group_diff(Group("pták"), Group("tučňák"))
    quantified = role("who", filler, FOR_ALL)
    assert quantified.target is filler

    from core_semantics.ast import UnquantifiedRole

    with pytest.raises(UnquantifiedRole):
        role("who", filler)


# --------------------------------------------------------------------------
# T42 — neeliminace OR
# --------------------------------------------------------------------------


def test_disjunctive_membership_is_attachable() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e1"), group_or(Group("pes"), Group("kočka"))))
    result = Engine(kb).ask(
        member_of(Entity("e1"), group_or(Group("pes"), Group("kočka")))
    )
    assert result.status is QueryStatus.PROVEN_TRUE


def test_or_membership_does_not_select_a_member() -> None:
    """Zákaz z dialogu A: z disjunkce se nesmí tiše vybrat člen.

    Kdyby bylo pravidlo pro `OR` ekvivalencí místo implikace zprava
    doleva, plynulo by z členství ve sjednocení členství v některém členu.
    """
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e1"), group_or(Group("pes"), Group("kočka"))))
    engine = Engine(kb)
    for member in (Group("pes"), Group("kočka")):
        assert (
            engine.ask(member_of(Entity("e1"), member)).status
            is QueryStatus.UNKNOWN
        )


def test_intersection_membership_does_distribute_downwards() -> None:
    """U `AND` se opačný směr neztrácí — bere se přes zákon `A AND B ⊆ A`."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e1"), group_and(Group("pes"), Group("černý"))))
    engine = Engine(kb)
    for member in (Group("pes"), Group("černý")):
        assert (
            engine.ask(member_of(Entity("e1"), member)).status
            is QueryStatus.PROVEN_TRUE
        )


def test_membership_in_an_intersection_needs_both_sides() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e1"), Group("pes")))
    engine = Engine(kb)
    assert (
        engine.ask(
            member_of(Entity("e1"), group_and(Group("pes"), Group("černý")))
        ).status
        is QueryStatus.UNKNOWN
    )
    kb.attach(member_of(Entity("e1"), Group("černý")))
    assert (
        Engine(kb)
        .ask(member_of(Entity("e1"), group_and(Group("pes"), Group("černý"))))
        .status
        is QueryStatus.PROVEN_TRUE
    )


# --------------------------------------------------------------------------
# T43 — DIFF přes `possible`, ne přes `certain`
# --------------------------------------------------------------------------


def test_difference_requires_proven_absence_not_ignorance() -> None:
    """`certain(A DIFF B) = certain(A) \\ possible(B)`.

    Dokud není doloženo, že prvek do `B` nepatří, je členství v rozdílu
    `U`. Slabší varianta `certain(A) \\ certain(B)` by z nevědomosti
    udělala tvrzení — táž chyba, která se opravovala u `query_diff`
    (I‑21).
    """
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("vrabec"), Group("pták")))
    kb.attach(member_of(Entity("v1"), Group("vrabec")))
    difference = group_diff(Group("pták"), Group("tučňák"))

    assert (
        Engine(kb).ask(member_of(Entity("v1"), difference)).status
        is QueryStatus.UNKNOWN
    )

    kb.add_disjoint(Group("vrabec"), Group("tučňák"))
    result = Engine(kb).ask(member_of(Entity("v1"), difference))
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None and "member*/alg" in "\n".join(
        result.proof_tree
    )


def test_species_level_difference_needs_documented_separateness() -> None:
    """Dodatek E: `X ⊆ A ∧ disjoint(X,B) ⇒ X ⊆ A DIFF B`.

    Bez toho by druhová reprezentace neměla protějšek k pravidlu, které
    `member*` pro `DIFF` má — „vrabec je pták kromě tučňáka" by nešlo
    doložit na úrovni tříd.
    """
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("vrabec"), Group("pták")))
    difference = group_diff(Group("pták"), Group("tučňák"))
    query = atom("létat", role("who", Group("vrabec"), FOR_ALL))
    kb.attach(atom("létat", role("who", difference, FOR_ALL)))

    assert Engine(kb).ask(query).status is QueryStatus.UNKNOWN
    kb.add_disjoint(Group("vrabec"), Group("tučňák"))
    assert Engine(kb).ask(query).status is QueryStatus.PROVEN_TRUE


def test_disjoint_is_found_in_both_directions() -> None:
    """Marker je v bázi jednosměrný, relace symetrická. Kdyby se hledal
    jen jeden směr, závisel by závěr na pořadí, ve kterém člověk
    oddělenost vyslovil."""
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("vrabec"), Group("pták")))
    kb.attach(
        atom(
            "létat",
            role("who", group_diff(Group("pták"), Group("tučňák")), FOR_ALL),
        )
    )
    # opačné pořadí, než se ptáme
    kb.add_disjoint(Group("tučňák"), Group("vrabec"))
    result = Engine(kb).ask(atom("létat", role("who", Group("vrabec"), FOR_ALL)))
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None
    assert any("disjoint" in line for line in result.proof_tree)


def test_difference_is_a_subset_of_its_left_operand() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("v1"), group_diff(Group("pták"), Group("tučňák"))))
    assert (
        Engine(kb).ask(member_of(Entity("v1"), Group("pták"))).status
        is QueryStatus.PROVEN_TRUE
    )


# --------------------------------------------------------------------------
# T44 — detekce rekurze nad algebraickým termem
# --------------------------------------------------------------------------


def test_laws_are_reachable_by_a_direct_question() -> None:
    """B‑6: zákony § 5.2.1 musí platit i na PŘÍMÝ dotaz, ne jen uvnitř
    distribuce.

    Dřív se `subset` v dotazu směroval na atomickou cestu, takže engine
    si `subset*` nad algebraickým termem vnitřně dokázal, ale člověku na
    tutéž otázku odpověděl `U`. Táž relace nesmí odpovídat různě podle
    toho, kudy se na ni jde.
    """
    kb = KnowledgeBase()
    engine = Engine(kb)
    assert (
        engine.ask(subset_of(group_and(A, B), A)).status
        is QueryStatus.PROVEN_TRUE
    )
    assert (
        engine.ask(subset_of(A, group_or(A, B))).status
        is QueryStatus.PROVEN_TRUE
    )
    assert (
        engine.ask(subset_of(group_diff(A, B), A)).status
        is QueryStatus.PROVEN_TRUE
    )
    # negativní kontroly — nic nesoundního neprojde
    assert engine.ask(subset_of(A, group_and(A, B))).status is QueryStatus.UNKNOWN
    assert engine.ask(subset_of(group_or(A, B), A)).status is QueryStatus.UNKNOWN


def test_algebraic_premise_in_a_rule_body_actually_fires() -> None:
    """B‑6, druhá polovina: pravidlo s algebraickou premisou se dřív
    TIŠE nespustilo — validace ho přijala a ono se nikdy nespárovalo.
    Bez chyby a bez varování, tedy přesně to, čemu brání I‑1."""

    def build(*, with_disjoint: bool) -> KnowledgeBase:
        kb = KnowledgeBase()
        kb.attach(subset_of(Group("vrabec"), Group("pták")))
        kb.attach(member_of(Entity("v1"), Group("vrabec")))
        if with_disjoint:
            kb.add_disjoint(Group("vrabec"), Group("tučňák"))
        x = Variable("x")
        kb.attach_rule(
            rule_id="p_safe",
            head=atom("bezpečný", role("who", x)),
            body=(
                member_of(x, Group("vrabec")),
                subset_of(
                    Group("vrabec"),
                    group_diff(Group("pták"), Group("tučňák")),
                ),
            ),
        )
        return kb

    query = atom("bezpečný", role("who", Entity("v1")))
    # bez doložené oddělenosti premisa neplatí a pravidlo nestřílí
    assert Engine(build(with_disjoint=False)).ask(query).status is QueryStatus.UNKNOWN

    result = Engine(build(with_disjoint=True)).ask(query)
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None and "p_safe" in result.proof.leaves()


def test_recursion_through_an_algebraic_term_is_detected() -> None:
    """C‑2: kdyby algebraický term neměl stabilní odvozené id, `_unifies`
    by ho neporovnal a detekce rekurze by se tiše rozpadla."""
    kb = KnowledgeBase()
    x, v = Variable("x"), Variable("V")
    kb.attach_rule(
        rule_id="r1",
        head=atom(
            "p",
            role("who", x),
            role("out", group_diff(Group("ga"), Group("gb")), SELF),
        ),
        body=(atom("q", role("who", x)),),
    )
    with pytest.raises(CycleDetected):
        kb.attach_rule(
            rule_id="r2",
            head=atom("q", role("who", x)),
            body=(atom("p", role("who", x), role("out", v)),),
        )
