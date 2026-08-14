"""Akceptační dialog — doména dopravy a rychlostních limitů.

Podklad pro `docs/EXAMPLES.md`. Testy tu jsou proto, aby dokumentace
nemohla zestárnout: vysvětlení se renderuje výhradně ze skutečně použité
struktury (I‑14), takže důkazní strom v dokumentu musí být ten, který
engine opravdu vyprodukuje.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from core_semantics.ast import (
    Comparator,
    Entity,
    Group,
    Label,
    P_ROLE_EXISTS,
    Quantifier,
    QueryStatus,
    RelationInstance,
    Sort,
    SortError,
    Value,
    Variable,
    atom,
    measure_of,
    member_of,
    role,
    same_as_of,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.epistemics import query_bound
from core_semantics.storage import KnowledgeBase

FOR_ALL = Quantifier.FOR_ALL
EXISTS = Quantifier.EXISTS
SELF = Quantifier.SELF
V130 = Value("130_km/h", "rychlost", Decimal(130), "km/h")


def _base(*, via: str) -> tuple[KnowledgeBase, str]:
    """`via` je skupina v `∃`-roli vztahu „jezdí po" — právě na ní se láme
    otázka 1 (viz `test_limit_does_not_reach_across_a_superclass`)."""
    kb = KnowledgeBase()
    for sub, sup in (
        ("Ford", "Automobil"),
        ("Automobil", "Auto"),
        ("Auto", "Vozidlo"),
        ("Dálnice", "Silnice"),
        ("Cestující", "Člověk"),
    ):
        kb.attach(subset_of(Group(sub), Group(sup)))
    kb.attach(same_as_of(Group("Automobil"), Group("Auto")))
    kb.add_disjoint(Group("Vozidlo"), Group("Člověk"))

    jezdi = kb.attach(
        atom(
            "jezdí_po",
            role("who", Group("Vozidlo"), FOR_ALL),
            role("via", Group(via), EXISTS),
        )
    )
    kb.attach(
        atom(
            "max_rychlost",
            role("of", Group("Dálnice"), FOR_ALL),
            role("quantity", Label("rychlost")),
            role("limit", V130),
        )
    )
    kb.attach(
        atom(
            "přepravuje",
            role("who", Group("Auto"), FOR_ALL),
            role("what", Group("Cestující"), EXISTS),
        )
    )
    relation, group_var, limit = (
        Variable("R"),
        Variable("P", expects=Sort.GROUP),
        Variable("V"),
    )
    kb.attach_rule(
        rule_id="R1",
        head=measure_of(relation, Comparator.LE, limit),
        body=(
            member_of(relation, Group("jezdí_po")),
            atom(
                P_ROLE_EXISTS,
                role("of", relation),
                role("name", Label("via")),
                role("filler", group_var, SELF),
            ),
            atom(
                "max_rychlost",
                role("of", group_var, FOR_ALL),
                role("quantity", Label("rychlost")),
                role("limit", limit),
            ),
        ),
    )
    kb.attach(member_of(Entity("Mondeo"), Group("Ford")))
    kb.attach(member_of(Entity("Jan_Novák"), Group("Člověk")))
    return kb, jezdi


def test_limit_does_not_reach_across_a_superclass() -> None:
    """Otázka 1 tak, jak je zadaná: „Vozidlo jezdí po **Silnici**".

    Limit je vlastnost **Dálnice**, tedy PODtřídy. `∀`-fakta se distribuují
    dolů, ne nahoru, takže z „dálnice mají limit 130" neplyne „silnice mají
    limit 130" — a můstek chybí. Poctivá odpověď je `U`, ne 130. Je to
    přesně mezera z dialogu A: chybějící článek se nehádá, nabídne se
    k potvrzení.
    """
    kb, jezdi = _base(via="Silnice")
    result = query_bound(
        Engine(kb), RelationInstance(jezdi), "rychlost", Comparator.LE
    )
    assert result.status is QueryStatus.UNKNOWN
    assert result.value is None


def test_limit_is_derived_once_the_premise_matches() -> None:
    """Doplněná premisa „Vozidlo jezdí po **Dálnici**" — teprve teď 130."""
    kb, jezdi = _base(via="Dálnice")
    result = query_bound(
        Engine(kb), RelationInstance(jezdi), "rychlost", Comparator.LE
    )
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.value is not None and result.value.magnitude == Decimal(130)
    assert result.proof is not None and "R1" in result.proof.leaves()


def test_subclass_instance_inherits_the_relation() -> None:
    """Mondeo ∈ Ford ⊆ Automobil ⊆ Auto ⊆ Vozidlo — D1 dolů přes celý řetěz."""
    kb, _ = _base(via="Dálnice")
    query = atom(
        "jezdí_po",
        role("who", Entity("Mondeo")),
        role("via", Group("Dálnice"), EXISTS),
    )
    result = Engine(kb).ask(query)
    assert result.status is QueryStatus.PROVEN_TRUE
    assert any("subset*" in line for line in result.proof_tree)


def test_identity_edge_appears_only_when_it_is_load_bearing() -> None:
    """Přeformulovaný bod checklistu „Proof Tree Inspection".

    V plné bázi je vedle `same_as(Automobil, Auto)` i `subset(Automobil,
    Auto)`, takže existují dvě cesty a třístupňový `canonical_key` vybere
    tu s méně listy — identitní hrana se v důkazu NEobjeví, a je to
    správně (I‑14 žádá skutečně použitou strukturu). Jakmile je ale
    rovnost jedinou cestou, objevit se MUSÍ.
    """
    kb, _ = _base(via="Dálnice")
    full = Engine(kb).ask(
        atom(
            "jezdí_po",
            role("who", Entity("Mondeo")),
            role("via", Group("Dálnice"), EXISTS),
        )
    )
    assert full.proof is not None
    assert not any("same_as*" in line for line in full.proof.render())

    # Táž znalost, ale podmnožinový článek chybí — rovnost je jediná cesta.
    lean = KnowledgeBase()
    lean.attach(subset_of(Group("Ford"), Group("Automobil")))
    link = lean.attach(same_as_of(Group("Automobil"), Group("Auto")))
    lean.attach(subset_of(Group("Auto"), Group("Vozidlo")))
    lean.attach(member_of(Entity("Mondeo"), Group("Ford")))
    proof = lean.view().member_proof("Mondeo", "Vozidlo")
    assert proof is not None
    assert link in proof.leaves()
    assert any("same_as*" in line for line in proof.render())


def test_existential_role_does_not_name_a_witness() -> None:
    """Otázka 2 — zákaz skolemizace. „Přepravuje nějakého cestujícího?" ANO,
    „přepravuje konkrétně Jana Nováka?" NEVÍM."""
    kb, _ = _base(via="Dálnice")
    engine = Engine(kb)
    concrete = atom(
        "přepravuje",
        role("who", Entity("Mondeo")),
        role("what", Entity("Jan_Novák")),
    )
    existential = atom(
        "přepravuje",
        role("who", Entity("Mondeo")),
        role("what", Group("Cestující"), EXISTS),
    )
    assert engine.ask(concrete).status is QueryStatus.UNKNOWN
    assert engine.ask(existential).status is QueryStatus.PROVEN_TRUE


def test_strong_negation_reaches_the_subclass() -> None:
    """Otázka 3 — Jan Novák je člověk, člověk není vozidlo, a kontrapozice
    to donese až na automobil."""
    kb, _ = _base(via="Dálnice")
    result = Engine(kb).ask(member_of(Entity("Jan_Novák"), Group("Automobil")))
    assert result.status is QueryStatus.PROVEN_FALSE
    assert any("member̄*" in line for line in result.proof_tree)


def test_identity_with_a_vehicle_creates_a_conflict() -> None:
    """Otázka 4 — „Jan Novák je Mondeo".

    Pozor na typování: `Mondeo` je jednotlivina (`member(Mondeo, Ford)`),
    ne skupina, takže `member(Jan_Novák, Mondeo)` je sortová chyba.
    Dobře utvořené čtení je `same_as` — a to skutečně vyrobí spor.
    """
    kb, _ = _base(via="Dálnice")
    kb.attach(same_as_of(Entity("Jan_Novák"), Entity("Mondeo")))
    result = Engine(kb).ask(member_of(Entity("Jan_Novák"), Group("Člověk")))
    assert result.status is QueryStatus.CONFLICT
    assert result.conflict is not None
    positive, negative = result.conflict
    assert any("same_as*" in line for line in negative.render())
    assert positive.leaves() != negative.leaves()


def test_membership_in_an_individual_is_a_sort_error() -> None:
    with pytest.raises(SortError):
        member_of(Entity("Jan_Novák"), Entity("Mondeo"))  # type: ignore[arg-type]
