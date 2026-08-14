"""Akceptační sada — fáze 3 (evaluátor).

Pokrývá T16–T18 (per-roli kvantifikace na dialozích A a B), T27 (derivace
`N` z `disjoint`), T28/T29 (můstkové pravidlo `p3` a `role_q` v těle) a
`CONFLICT` jako stav dotazu.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from core_semantics.ast import (
    Comparator,
    DepthExceeded,
    Entity,
    Group,
    Label,
    P_ROLE_EXISTS,
    Quantifier,
    QueryStatus,
    RelationInstance,
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
from core_semantics.storage import KnowledgeBase

DP = Group("dopravní_prostředek")
AUTO = Group("auto")
DALNICE = Group("dálnice")


def _dialog_a_base() -> tuple[KnowledgeBase, str]:
    kb = KnowledgeBase()
    kb.attach(subset_of(AUTO, DP))
    jezdit = kb.attach(
        atom(
            "jezdit",
            role("who", DP, Quantifier.FOR_ALL),
            role("via", DALNICE, Quantifier.EXISTS),
        )
    )
    return kb, jezdit


# --------------------------------------------------------------------------
# Dialog A — ∀ se distribuuje dolů (T16)
# --------------------------------------------------------------------------


def test_forall_distributes_down_to_subgroup() -> None:  # T16
    kb, _ = _dialog_a_base()
    query = atom(
        "jezdit",
        role("who", AUTO, Quantifier.FOR_ALL),
        role("via", DALNICE, Quantifier.EXISTS),
    )
    result = Engine(kb).ask(query)
    assert result.status is QueryStatus.PROVEN_TRUE
    # Krok distribuce musí být v důkazu vidět (§ 3.3).
    assert any("subset*" in line for line in result.proof_tree)


def test_forall_does_not_distribute_upwards() -> None:
    """Opačný směr neplatí: z „auta jezdí" neplyne „dopravní prostředky jezdí"."""
    kb = KnowledgeBase()
    kb.attach(subset_of(AUTO, DP))
    kb.attach(
        atom(
            "jezdit",
            role("who", AUTO, Quantifier.FOR_ALL),
            role("via", DALNICE, Quantifier.EXISTS),
        )
    )
    query = atom(
        "jezdit",
        role("who", DP, Quantifier.FOR_ALL),
        role("via", DALNICE, Quantifier.EXISTS),
    )
    assert Engine(kb).ask(query).status is QueryStatus.UNKNOWN


def test_forall_distributes_to_a_member() -> None:
    kb, _ = _dialog_a_base()
    kb.attach(member_of(Entity("a1"), AUTO))
    query = atom(
        "jezdit",
        role("who", Entity("a1")),
        role("via", DALNICE, Quantifier.EXISTS),
    )
    assert Engine(kb).ask(query).status is QueryStatus.PROVEN_TRUE


# --------------------------------------------------------------------------
# Dialog B — ∃ se nedistribuuje na svědka (T17), ale ∃-dotaz sedí (T18)
# --------------------------------------------------------------------------


def _dialog_b_base() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(
        atom(
            "obsahovat",
            role("who", Group("ovoce"), Quantifier.FOR_ALL),
            role("what", Group("vitamín"), Quantifier.EXISTS),
        )
    )
    kb.attach(member_of(Entity("e_citron"), Group("ovoce")))
    kb.attach(member_of(Entity("e_vitamin_c"), Group("vitamín")))
    return kb


def test_exists_does_not_distribute_to_a_witness() -> None:  # T17
    """«Obsahuje citron vitamín C?» — vztah ke group NENÍ vztah ke členu."""
    query = atom(
        "obsahovat",
        role("who", Entity("e_citron")),
        role("what", Entity("e_vitamin_c")),
    )
    result = Engine(_dialog_b_base()).ask(query)
    assert result.status is QueryStatus.UNKNOWN
    assert result.gap is not None


def test_exists_query_matches_an_exists_role() -> None:  # T18
    """«Obsahuje citron nějaký vitamín?» — táž báze, opačná odpověď."""
    query = atom(
        "obsahovat",
        role("who", Entity("e_citron")),
        role("what", Group("vitamín"), Quantifier.EXISTS),
    )
    assert Engine(_dialog_b_base()).ask(query).status is QueryStatus.PROVEN_TRUE


def test_exists_query_may_widen_but_not_narrow() -> None:
    kb = _dialog_b_base()
    kb.attach(subset_of(Group("vitamín"), Group("živina")))
    engine = Engine(kb)
    wider = atom(
        "obsahovat",
        role("who", Entity("e_citron")),
        role("what", Group("živina"), Quantifier.EXISTS),
    )
    assert engine.ask(wider).status is QueryStatus.PROVEN_TRUE  # D2 nahoru

    kb2 = _dialog_b_base()
    kb2.attach(subset_of(Group("vitamín_b"), Group("vitamín")))
    narrower = atom(
        "obsahovat",
        role("who", Entity("e_citron")),
        role("what", Group("vitamín_b"), Quantifier.EXISTS),
    )
    assert Engine(kb2).ask(narrower).status is QueryStatus.UNKNOWN


def test_extra_role_in_the_fact_does_not_block_the_match() -> None:
    """«jede rychle po dálnici» odpovídá i na «jede po dálnici?» (§ 3.4)."""
    kb = KnowledgeBase()
    kb.attach(
        atom(
            "jet",
            role("who", Entity("e_petr")),
            role("via", Group("dálnice"), Quantifier.EXISTS),
            role("manner", Label("rychle")),
        )
    )
    query = atom(
        "jet",
        role("who", Entity("e_petr")),
        role("via", Group("dálnice"), Quantifier.EXISTS),
    )
    assert Engine(kb).ask(query).status is QueryStatus.PROVEN_TRUE


# --------------------------------------------------------------------------
# Dialog C — derivační constraint dává verdikt N (T27)
# --------------------------------------------------------------------------


def test_disjoint_derives_proven_false() -> None:  # T27
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("spisovatel"), Group("člověk")))
    kb.add_disjoint(Group("stroj"), Group("člověk"))
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    result = Engine(kb).ask(member_of(Entity("e17"), Group("stroj")))
    assert result.status is QueryStatus.PROVEN_FALSE
    assert result.proof is not None


def _dialog_c_with_subclass() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("spisovatel"), Group("člověk")))
    kb.add_disjoint(Group("stroj"), Group("člověk"))
    kb.attach(subset_of(Group("parní_stroj"), Group("stroj")))
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    return kb


def test_strong_negation_propagates_to_subclasses() -> None:
    """§ 5.1: `member̄(x,B) ∧ subset*(A,B) ⇒ member̄(x,A)`.

    Premisa `member̄(e17,"stroj")` v bázi NENÍ — vzniká až expanzí
    `disjoint`, tedy pravidlem. Uzávěr proto musí saturovat uvnitř pevného
    bodu, ne v indexu nad základními fakty."""
    engine = Engine(_dialog_c_with_subclass())
    assert (
        engine.ask(member_of(Entity("e17"), Group("stroj"))).status
        is QueryStatus.PROVEN_FALSE
    )
    result = engine.ask(member_of(Entity("e17"), Group("parní_stroj")))
    assert result.status is QueryStatus.PROVEN_FALSE
    assert result.proof is not None
    assert any("member̄*" in line for line in result.proof_tree)


def test_strong_negation_does_not_propagate_to_superclasses() -> None:
    """Opačný směr je nekorektní: „není parní stroj" NEZNAMENÁ „není stroj"."""
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("parní_stroj"), Group("stroj")))
    kb.attach(member_of(Entity("e_r"), Group("parní_stroj"), negated=True))
    result = Engine(kb).ask(member_of(Entity("e_r"), Group("stroj")))
    assert result.status is QueryStatus.UNKNOWN


def test_contraposition_widens_reachable_conflicts() -> None:
    """Nárůst dosažitelných `CONFLICT` je SPRÁVNÝ důsledek úplnějšího
    uzávěru, ne regrese. Báze, která tvrdí členství v podtřídě vyloučené
    třídy, je nekonzistentní — dřív to procházelo tiše jako `A`."""
    kb = _dialog_c_with_subclass()
    kb.attach(member_of(Entity("e17"), Group("parní_stroj")))
    result = Engine(kb).ask(member_of(Entity("e17"), Group("parní_stroj")))
    assert result.status is QueryStatus.CONFLICT
    assert result.conflict is not None
    positive, negative = result.conflict
    assert positive.leaves() and negative.leaves()
    assert positive.leaves() != negative.leaves()


def test_absence_alone_never_yields_false() -> None:
    """I‑21: absence tvrzení nikdy sama nevytvoří záporné tvrzení."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    result = Engine(kb).ask(member_of(Entity("e17"), Group("stroj")))
    assert result.status is QueryStatus.UNKNOWN


def test_conflict_is_a_query_state() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_tucnak"), Group("létající")))
    kb.attach(member_of(Entity("e_tucnak"), Group("létající"), negated=True))
    result = Engine(kb).ask(member_of(Entity("e_tucnak"), Group("létající")))
    assert result.status is QueryStatus.CONFLICT
    assert result.conflict is not None and len(result.conflict) == 2


# --------------------------------------------------------------------------
# Dialog A — můstkové pravidlo p3 nad ∃-rolí (T28, T29)
# --------------------------------------------------------------------------


def test_bridge_rule_reaches_into_an_exists_role() -> None:  # T28 / T29
    """`p3` musí sáhnout na `∃`-roli, která NEMÁ konkrétního svědka —
    proto `role_q`, a proto je přístup k roli predikát, ne funkce."""
    kb, jezdit = _dialog_a_base()
    v130 = Value("v130", "rychlost", Decimal(130), "km/h")
    kb.attach(
        atom(
            "omezení",
            role("of", DALNICE, Quantifier.FOR_ALL),
            role("quantity", Label("rychlost")),
            role("limit", v130),
        )
    )
    R = Variable("R")
    P = Variable("P", expects=Sort.GROUP)
    V = Variable("V")
    kb.attach_rule(
        rule_id="p3",
        head=measure_of(R, Comparator.LE, V),
        body=(
            member_of(R, Group("jezdit")),
            atom(
                P_ROLE_EXISTS,
                role("of", R),
                role("name", Label("via")),
                role("filler", P, Quantifier.SELF),
            ),
            atom(
                "omezení",
                role("of", P, Quantifier.FOR_ALL),
                role("quantity", Label("rychlost")),
                role("limit", V),
            ),
        ),
    )
    result = Engine(kb).ask(
        measure_of(RelationInstance(jezdit), Comparator.LE, v130)
    )
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None and "p3" in result.proof.leaves()


def test_relation_is_reified_into_role_atoms() -> None:
    kb, jezdit = _dialog_a_base()
    derivation = Engine(kb).derivation()
    instance = RelationInstance(jezdit)
    assert member_of(instance, Group("jezdit")) in derivation.facts
    decomposed = atom(
        P_ROLE_EXISTS,
        role("of", instance),
        role("name", Label("via")),
        role("filler", DALNICE, Quantifier.SELF),
    )
    assert decomposed in derivation.facts


def test_evaluation_creates_no_individuals() -> None:  # T30
    """§ 0/2: individua zakládá jen `attach`. Evaluace nesmí přidat uzel —
    a od kola #2 to platí i pro reifikované uzly vztahů."""
    kb, _ = _dialog_a_base()
    kb.attach(member_of(Entity("a1"), AUTO))
    kb.add_disjoint(Group("auto"), Group("chodec"))
    engine = Engine(kb)
    declared = kb.node_ids()
    derivation = engine.derivation()
    engine.ask(
        atom(
            "jezdit",
            role("who", Entity("a1")),
            role("via", DALNICE, Quantifier.EXISTS),
        )
    )
    assert set(derivation.terms) <= declared
    assert kb.node_ids() == declared


def test_reified_relation_is_inspectable_and_revocable() -> None:
    """Reifikovaný uzel je výrok v bázi: má provenienci, `inspect` ho vidí
    a kaskádové `revoke` na něj dosáhne (§ 3.7/1)."""
    kb, jezdit = _dialog_a_base()
    derived = kb.derived_from(jezdit)
    assert derived, "reifikace musí být v bázi, ne jen v evaluaci"
    assert any(
        st.formula == member_of(RelationInstance(jezdit), Group("jezdit"))
        for st in derived
    )
    for st in derived:
        statement, active, _ = kb.inspect(st.id)
        assert active and statement.provenance.startswith("reifikace")

    query = atom(
        "jezdit",
        role("who", AUTO, Quantifier.FOR_ALL),
        role("via", DALNICE, Quantifier.EXISTS),
    )
    assert Engine(kb).ask(query).status is QueryStatus.PROVEN_TRUE

    revoked = kb.revoke(jezdit, "oprava zadání")
    assert set(st.id for st in derived) <= set(revoked)
    assert Engine(kb).ask(query).status is QueryStatus.UNKNOWN


def test_nesting_beyond_max_depth_is_rejected() -> None:  # W-6
    """Mez z § 12/3 zadání musí být strojově hlídaná (I‑13), ne jen zapsaná."""
    kb = KnowledgeBase(max_depth=1)
    mit = kb.attach(
        atom("mít", role("kdo", Entity("e_petr")), role("co", Entity("a1")))
    )
    chtit = kb.attach(
        atom(
            "chtít",
            role("kdo", Entity("e_petr")),
            role("co", RelationInstance(mit)),
        )
    )
    with pytest.raises(DepthExceeded):
        kb.attach(
            atom(
                "říct",
                role("kdo", Entity("e_pavel")),
                role("co", RelationInstance(chtit)),
            )
        )


def test_open_query_returns_a_witness() -> None:  # W-5
    """Dotaz s proměnnou je existenční — `ANO` musí nést svědka (§ 6.3,
    dialog C), ne mlčky existenčně kvantifikovat."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    kb.attach(
        atom(
            "napsat",
            role("who", Entity("e17")),
            role("what", Entity("e_postriziny")),
        )
    )
    query = atom(
        "napsat",
        role("who", Variable("X")),
        role("what", Entity("e_postriziny")),
    )
    result = Engine(kb).ask(query)
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.payload["X"] == Entity("e17")
    assert result.proof_tree[0].startswith("witness(")


def test_open_query_without_a_witness_is_unknown() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    query = atom(
        "napsat",
        role("who", Variable("X")),
        role("what", Entity("e_postriziny")),
    )
    assert Engine(kb).ask(query).status is QueryStatus.UNKNOWN


def test_long_rule_chain_does_not_exhaust_max_rounds() -> None:  # W-2
    """Řetěz 25 pravidel připojený v OPAČNÉM pořadí, než v jakém se
    vyhodnocuje. Pořadí musí dodat topologické řazení, ne id výroků —
    jinak by pevný bod spotřeboval jedno kolo na článek a `max_rounds`
    by se stal nosným místo pojistky."""
    length = 25
    kb = KnowledgeBase()
    x = Variable("x")
    for i in reversed(range(length)):
        kb.attach_rule(
            head=atom(f"a{i + 1}", role("who", x)),
            body=(atom(f"a{i}", role("who", x)),),
            rule_id=f"p{i:04d}",
        )
    kb.attach(atom("a0", role("who", Entity("e1"))))

    engine = Engine(kb)
    result = engine.ask(atom(f"a{length}", role("who", Entity("e1"))))
    assert result.status is QueryStatus.PROVEN_TRUE
    # 1 produktivní kolo + 1 potvrzovací; nezávisle na pořadí zápisu.
    assert engine.derivation().rounds == 2


def test_enumeration_never_drops_an_element_silently() -> None:  # W-2
    """I‑1: žádná vrstva nesmí selhat tiše. Nevázaná role `group`
    v jádrovém atomu je hlášená chyba, ne prázdný výsledek."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e1"), Group("ovoce")))
    x = Variable("x")
    kb.attach_rule(
        head=atom("ovocny", role("x", x)),
        body=(member_of(x, Group("ovoce")),),
        rule_id="p_enum",
    )
    solutions = Engine(kb).solutions(atom("ovocny", role("x", Variable("y"))))
    assert [binding["y"] for binding, _ in solutions] == [Entity("e1")]
