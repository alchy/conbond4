"""Akceptační sada — fáze 1–2.

Pokryto je jen to, na co AST, uzávěry a báze dosáhnou. T16–T19, T23–T26
a T27–T31 potřebují evaluátor z fáze 3; T20 (uzávěr `⊆`) a T21 (`same_as`
jako pohled) jsou zde v té části, která na engine nečeká.

Konvence: názvy testů anglicky, komentáře a hlášky česky.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    CycleDetected,
    Entity,
    Group,
    Place,
    Proof,
    ProofKind,
    Quantifier,
    Rule,
    Sort,
    SortError,
    UnquantifiedRole,
    UnsafeRule,
    Variable,
    atom,
    complete_of,
    contains_of,
    member_of,
    role,
    same_as_of,
    select_canonical,
    subset_of,
)
from core_semantics.storage import KnowledgeBase

# --------------------------------------------------------------------------
# Typování AST (§ 1)
# --------------------------------------------------------------------------


def test_group_role_requires_quantifier() -> None:
    """Group ve filleru bez kvantifikátoru je chyba zápisu, ne default —
    jádro nemá co hádat, patří sem doptání (§ 2.6 podkladu)."""
    with pytest.raises(UnquantifiedRole):
        role("who", Group("dopravní_prostředek"))


def test_quantifier_on_entity_is_rejected() -> None:
    with pytest.raises(SortError):
        role("who", Entity("e_petr"), Quantifier.FOR_ALL)


def test_quantifier_is_allowed_on_variable() -> None:
    # `role_q(r, via, ∃, P)` z můstkového pravidla dialogu A potřebuje
    # kvantifikátor nad proměnnou.
    r = role("via", Variable("P"), Quantifier.EXISTS)
    assert r.quantifier is Quantifier.EXISTS


def test_duplicate_role_is_rejected() -> None:
    with pytest.raises(SortError):
        atom(
            "jezdit",
            role("who", Entity("e_petr")),
            role("who", Entity("e_pavel")),
        )


def test_strong_negation_is_a_separate_predicate() -> None:
    """`p̄` není klasické ¬ — je to jiný uzel dependency grafu (§ 4)."""
    positive = member_of(Entity("e17"), Group("stroj"))
    negative = positive.complement()
    assert negative.is_negated is True
    assert positive.signature != negative.signature
    assert negative.complement() == positive


# --------------------------------------------------------------------------
# Pravidla (§ 5.4)
# --------------------------------------------------------------------------


def test_rule_with_unbound_head_variable_is_rejected() -> None:
    x, y = Variable("x"), Variable("y")
    with pytest.raises(UnsafeRule):
        Rule(
            id="p_bad",
            head=member_of(y, Group("savec"), negated=True),
            body=(member_of(x, Group("pták")),),
        )


def test_rule_cannot_redefine_kernel_predicate() -> None:
    """Učení mění program, nikdy jazyk (I‑16): `member` dodává jádrový
    uzávěr, naučené pravidlo ho nesmí mít v nenegované hlavě."""
    x = Variable("x")
    with pytest.raises(UnsafeRule):
        Rule(
            id="p_bad",
            head=member_of(x, Group("člověk")),
            body=(member_of(x, Group("spisovatel")),),
        )


def test_cycle_in_learned_rules_is_rejected() -> None:
    kb = KnowledgeBase()
    x = Variable("x")
    a = atom("a", role("x", x))
    b = atom("b", role("x", x))
    kb.attach_rule(head=b, body=(a,), rule_id="p_ab")
    with pytest.raises(CycleDetected):
        kb.attach_rule(head=a, body=(b,), rule_id="p_ba")


def test_rule_variable_cannot_be_bound_by_negated_body_only() -> None:
    """§ 5.4/1 — vazba jen z pozitivního těla. „Létá všechno, co není tučňák"
    má rozsah přes celou otevřenou doménu, včetně nepojmenovaných individuí."""
    x = Variable("x")
    with pytest.raises(UnsafeRule):
        Rule(
            id="p_flounder",
            head=atom("létat", role("who", x)),
            body=(member_of(x, Group("tučňák"), negated=True),),
        )


def test_free_variable_under_negation_is_rejected() -> None:
    """§ 5.4/7 — proměnná v negovaném literálu musí být vázaná pozitivně."""
    x, y = Variable("x"), Variable("y")
    with pytest.raises(UnsafeRule):
        Rule(
            id="p_flounder2",
            head=atom("létat", role("who", x)),
            body=(
                member_of(x, Group("pták")),
                member_of(y, Group("tučňák"), negated=True),
            ),
        )


def test_revoke_cascade_is_transitive() -> None:
    kb = KnowledgeBase()
    a = kb.attach(member_of(Entity("e1"), Group("a")))
    b = kb.attach(member_of(Entity("e2"), Group("b")), derived_from=a)
    c = kb.attach(member_of(Entity("e3"), Group("c")), derived_from=b)
    assert set(kb.revoke(a, "test")) == {a, b, c}
    assert list(kb.active()) == []


def test_quantifier_is_required_on_group_typed_variable() -> None:
    with pytest.raises(UnquantifiedRole):
        role("via", Variable("P", expects=Sort.GROUP))


def test_fact_with_variable_is_rejected() -> None:
    kb = KnowledgeBase()
    with pytest.raises(UnsafeRule):
        kb.attach(member_of(Variable("x"), Group("auto")))


# --------------------------------------------------------------------------
# Uzávěry (§ 5.1) — část T20
# --------------------------------------------------------------------------


def test_subset_star_is_transitive_and_cites_every_step() -> None:
    kb = KnowledgeBase()
    s1 = kb.attach(subset_of(Group("citron"), Group("ovoce")))
    s2 = kb.attach(subset_of(Group("ovoce"), Group("potravina")))
    proof = kb.view().subset_proof("citron", "potravina")
    assert proof is not None
    # Každý krok uzávěru je hrana v důkazu, ne skrytá normalizace (§ 3.3).
    assert proof.leaves() == {s1, s2}


def test_subset_star_is_reflexive() -> None:
    kb = KnowledgeBase()
    proof = kb.view().subset_proof("ovoce", "ovoce")
    assert proof is not None
    assert proof.leaves() == frozenset()


def test_subset_star_has_no_reverse_direction() -> None:
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    assert kb.view().subset_proof("ovoce", "citron") is None


def test_contains_star_over_places(  # T20
) -> None:
    kb = KnowledgeBase()
    s1 = kb.attach(contains_of(Place("evropa"), Place("cesko")))
    s2 = kb.attach(contains_of(Place("cesko"), Place("praha")))
    proof = kb.view().contains_proof("evropa", "praha")
    assert proof is not None
    assert proof.leaves() == {s1, s2}


def test_places_are_not_groups() -> None:
    """„Praha ⊆ Česko" není podmnožina (§ 1) — grafy jsou oddělené, takže
    `contains` nesmí prosáknout do `subset*` ani naopak."""
    kb = KnowledgeBase()
    kb.attach(contains_of(Place("cesko"), Place("praha")))
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    view = kb.view()
    assert view.subset_proof("praha", "cesko") is None
    assert view.contains_proof("ovoce", "citron") is None


def test_member_star_through_subset_chain() -> None:
    kb = KnowledgeBase()
    s1 = kb.attach(member_of(Entity("e_c"), Group("citron")))
    s2 = kb.attach(subset_of(Group("citron"), Group("ovoce")))
    proof = kb.view().member_proof("e_c", "ovoce")
    assert proof is not None
    assert proof.leaves() == {s1, s2}


def test_known_extension_is_a_lower_bound() -> None:
    """Extenze je dolní odhad, dokud nepadne `complete(g)` (§ 3.1, I‑11)."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_citron"), Group("ovoce")))
    kb.attach(member_of(Entity("e_pomeranc"), Group("ovoce")))
    view = kb.view()
    assert view.known_members("ovoce") == ["e_citron", "e_pomeranc"]
    assert view.is_complete("ovoce") is None

    sid = kb.attach(complete_of(Group("ovoce")))
    assert kb.view().is_complete("ovoce") == sid


# --------------------------------------------------------------------------
# Identita jako pohled (§ 8) — část T21, T22
# --------------------------------------------------------------------------


def test_same_as_is_a_view_and_revoke_restores_unknown() -> None:  # T21
    kb = KnowledgeBase()
    fact = kb.attach(member_of(Entity("e_b"), Group("spisovatel")))
    assert kb.view().member_proof("e_a", "spisovatel") is None

    link = kb.attach(same_as_of(Entity("e_a"), Entity("e_b")))
    proof = kb.view().member_proof("e_a", "spisovatel")
    assert proof is not None
    # Identitní hrana MUSÍ být v důkazu — jinak by pohled lhal o tom,
    # proč se fakt o `e_b` použil na `e_a`.
    assert proof.leaves() == {fact, link}

    kb.revoke(link, "ukázalo se, že jde o jiného Hrabala")
    assert kb.view().member_proof("e_a", "spisovatel") is None
    # Nic se nepřepsalo: původní fakt je pořád aktivní a beze změny.
    stmt, active, _ = kb.inspect(fact)
    assert active is True
    assert stmt.formula == member_of(Entity("e_b"), Group("spisovatel"))


def test_same_as_does_not_leak_between_sorts() -> None:
    """Rovnost dvou míst nesmí vyrobit podmnožinovou hranu (§ 1) a identitní
    krok se nesmí renderovat jako `subset*` (§ 3.3, I‑14)."""
    kb = KnowledgeBase()
    kb.attach(same_as_of(Place("leningrad"), Place("petrohrad")))
    view = kb.view()
    assert view.subset_proof("leningrad", "petrohrad") is None
    # Nad Place naopak obsažení přes identitu platit MÁ.
    proof = view.contains_proof("leningrad", "petrohrad")
    assert proof is not None
    assert any("same_as*" in line for line in proof.render())


def test_identity_bridges_a_subset_chain_and_is_named_in_the_proof() -> None:
    """`Ford ⊆ Automobil ≡ Auto ⊆ Vozidlo`.

    Rovnost musí přemostit řetěz UPROSTŘED, ne jen na jeho koncích — kolaps
    tříd jen u krajních uzlů by tenhle případ minul. Krok se přitom
    v důkazu jmenuje `closure(same_as*)`, ne `subset*`: cesta smí vést
    přes rovnost, ale nesmí se tvářit jako podmnožinový krok (I‑14).
    """
    kb = KnowledgeBase()
    first = kb.attach(subset_of(Group("Ford"), Group("Automobil")))
    link = kb.attach(same_as_of(Group("Automobil"), Group("Auto")))
    second = kb.attach(subset_of(Group("Auto"), Group("Vozidlo")))

    proof = kb.view().subset_proof("Ford", "Vozidlo")
    assert proof is not None
    assert proof.leaves() == {first, link, second}
    assert any("same_as*" in line for line in proof.render())


def test_same_as_over_groups_is_writable() -> None:
    """§ 3.5: „člověk"/„lidé" je týž problém jako „Hrabal"/„Bohumil Hrabal" —
    jedna jmenná vrstva pro entity i třídy."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e17"), Group("lidé")))
    link = kb.attach(same_as_of(Group("člověk"), Group("lidé")))
    proof = kb.view().member_proof("e17", "člověk")
    assert proof is not None
    assert link in proof.leaves()


def test_identity_that_would_close_a_cycle_is_rejected() -> None:
    """Rozhodnutí B‑IV: scelení identity je odmítnutelná operace.

    `ga` a `gb` drží dvě pravidla od sebe; jakmile je `same_as` ztotožní,
    vznikne cyklus `q → p → q`. Samotné zopakování validace by nestačilo —
    `dependency_key` skládá klíče ze surových id, takže se musí porovnávat
    přes třídy ekvivalence (`_unifies`).
    """
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        rule_id="r1",
        head=atom("p", role("who", x), role("out", Group("ga"), Quantifier.SELF)),
        body=(atom("q", role("who", x)),),
    )
    kb.attach_rule(
        rule_id="r2",
        head=atom("q", role("who", x)),
        body=(atom("p", role("who", x), role("out", Group("gb"), Quantifier.SELF)),),
    )
    before = len(kb.history())
    with pytest.raises(CycleDetected):
        kb.attach(same_as_of(Group("ga"), Group("gb")))
    # Odmítnutá hrana v bázi nezůstane.
    assert len(kb.history()) == before
    assert kb.view().subset_proof("ga", "gb") is None


def test_harmless_identity_still_attaches() -> None:
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        rule_id="r1",
        head=atom("p", role("who", x), role("out", Group("ga"), Quantifier.SELF)),
        body=(atom("q", role("who", x)),),
    )
    kb.attach(same_as_of(Group("ga"), Group("gc")))
    assert kb.view().canonical("gc") == "ga"


def test_same_as_across_sorts_is_rejected() -> None:
    with pytest.raises(SortError):
        same_as_of(Entity("e_petr"), Place("praha"))


def test_structural_builders_enforce_sorts_at_runtime() -> None:
    with pytest.raises(SortError):
        subset_of(Group("ovoce"), Place("praha"))  # type: ignore[arg-type]
    with pytest.raises(SortError):
        contains_of(Place("praha"), Group("ovoce"))  # type: ignore[arg-type]


def test_canonical_representative_is_the_lowest_id() -> None:
    kb = KnowledgeBase()
    kb.attach(same_as_of(Entity("e_z"), Entity("e_a")))
    kb.attach(same_as_of(Entity("e_a"), Entity("e_m")))
    view = kb.view()
    assert view.canonical("e_z") == "e_a"
    assert view.class_of("e_m") == ["e_a", "e_m", "e_z"]


def test_counting_without_una_collapses_only_proven_identities() -> None:  # T22
    """Bez UNA je poctivé to, co lze doložit: dvě auta zůstanou dvě, dokud
    někdo netvrdí, že jsou totéž (§ 1.2 podkladu)."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("a1"), Group("auto")))
    kb.attach(member_of(Entity("a2"), Group("auto")))
    assert kb.view().known_members("auto") == ["a1", "a2"]

    kb.attach(same_as_of(Entity("a1"), Entity("a2")))
    assert kb.view().known_members("auto") == ["a1"]


# --------------------------------------------------------------------------
# Derivační constrainty (§ 5.3)
# --------------------------------------------------------------------------


def test_disjoint_expands_to_two_strongly_negated_rules() -> None:
    kb = KnowledgeBase()
    marker, left, right = kb.add_disjoint(Group("stroj"), Group("člověk"))
    rules = [st.formula for st in kb.active() if isinstance(st.formula, Rule)]
    assert len(rules) == 2
    for rule in rules:
        assert rule.head.is_negated is True
        assert len(rule.body) == 1
        assert rule.body[0].is_negated is False
    group_roles = [rule.head.get_role("group") for rule in rules]
    assert all(r is not None for r in group_roles)
    heads = {r.target.id for r in group_roles if r is not None}
    assert heads == {"stroj", "člověk"}
    assert {left, right} == {st.id for st in kb.active() if isinstance(st.formula, Rule)}
    assert all(
        st.derived_from == marker
        for st in kb.active()
        if isinstance(st.formula, Rule)
    )


def test_disjoint_expansion_is_not_a_cycle() -> None:
    """`member` → `member̄` vypadá jako smyčka jen tomu, kdo silnou negaci
    nepovažuje za samostatný predikát (§ 5.4/5)."""
    kb = KnowledgeBase()
    kb.add_disjoint(Group("stroj"), Group("člověk"))  # nesmí vyhodit CycleDetected
    kb.add_disjoint(Group("ovoce"), Group("zelenina"))


def test_chained_disjointness_is_not_a_cycle() -> None:
    """Řetěz neslučitelností: všechny expanze mají hlavu `member̄` a tělo
    `member` (jádrový, tedy list stratu 0) — mezi uzly nevzniká hrana."""
    kb = KnowledgeBase()
    for a, b in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]:
        kb.add_disjoint(Group(a), Group(b))
    assert len([st for st in kb.active() if isinstance(st.formula, Rule)]) == 8


def test_chain_of_incompatibilities_is_learnable() -> None:
    """«Co není stroj, není ani robot» — proměnná vázaná pozitivně, žádná
    rekurze. Uzel dependency grafu musí být jemnější než (predikát, znaménko),
    jinak všechny expanze `disjoint` splynou do `member̄` a řetěz vypadá
    jako smyčka."""
    kb = KnowledgeBase()
    kb.add_disjoint(Group("stroj"), Group("člověk"))
    y = Variable("y")
    kb.attach_rule(
        head=member_of(y, Group("robot"), negated=True),
        body=(
            member_of(y, Group("kov")),
            member_of(y, Group("stroj"), negated=True),
        ),
    )


def test_genuine_recursion_through_negation_is_still_rejected() -> None:
    """Zjemnění uzlu nesmí propustit skutečný cyklus: `p̄ <- q` a `q <- p̄`
    nemá stratifikaci (§ 5.4/6)."""
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        head=atom("p", role("x", x), negated=True),
        body=(atom("q", role("x", x)),),
        rule_id="p_first",
    )
    with pytest.raises(CycleDetected):
        kb.attach_rule(
            head=atom("q", role("x", x)),
            # `x` je vázané pozitivně, takže pravidlo projde kontrolou § 5.4/1;
            # zachytit ho musí až stratifikace.
            body=(atom("zaklad", role("x", x)), atom("p", role("x", x), negated=True)),
            rule_id="p_second",
        )


def test_recursion_hidden_behind_a_variable_filler_is_rejected() -> None:
    """Cyklus `q → p(a) → q`, kde jeden literál nese v roli PROMĚNNOU.

    `*` není divoká karta, jen značka — hrany se proto musí stavět unifikací.
    Při rovnosti klíčů by `p(out:*)` a `p(out:·a)` byly různé uzly, hrana by
    nevznikla a rekurze by prošla validací.
    """
    kb = KnowledgeBase()
    x, v = Variable("x"), Variable("V")
    kb.attach_rule(
        head=atom("p", role("who", x), role("out", Group("a"), Quantifier.SELF)),
        body=(atom("q", role("who", x)),),
        rule_id="r1",
    )
    with pytest.raises(CycleDetected):
        kb.attach_rule(
            head=atom("q", role("who", x)),
            body=(atom("p", role("who", x), role("out", v)),),
            rule_id="r2",
        )


def test_direct_self_recursion_with_variable_filler_is_rejected() -> None:
    kb = KnowledgeBase()
    x, v = Variable("x"), Variable("V")
    with pytest.raises(CycleDetected):
        kb.attach_rule(
            head=atom("p", role("who", x), role("out", Group("a"), Quantifier.SELF)),
            body=(atom("p", role("who", x), role("out", v)),),
            rule_id="r_self",
        )


def test_distinct_constant_fillers_still_do_not_collide() -> None:
    """Protikontrola k unifikaci: dvě různé konstanty v téže roli kolidují,
    takže se hrana nepostaví a legitimní program projde."""
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        head=atom("p", role("who", x), role("out", Group("a"), Quantifier.SELF)),
        body=(atom("q", role("who", x)),),
        rule_id="r1",
    )
    kb.attach_rule(
        head=atom("q", role("who", x)),
        body=(atom("p", role("who", x), role("out", Group("b"), Quantifier.SELF)),),
        rule_id="r2",
    )


def test_positive_recursion_is_rejected() -> None:
    """§ 5.4/5 — pozitivní cyklus je rekurze v naučeném programu."""
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        head=atom("b", role("x", x)),
        body=(atom("a", role("x", x)),),
        rule_id="p_ab",
    )
    with pytest.raises(CycleDetected):
        kb.attach_rule(
            head=atom("a", role("x", x)),
            body=(atom("b", role("x", x)),),
            rule_id="p_ba",
        )


def test_stratified_negation_is_ordered_after_lower_stratum() -> None:
    """Negovaný literál se musí číst až po dokončení nižšího strata —
    pořadí dodává pohled, ne engine."""
    kb = KnowledgeBase()
    x = Variable("x")
    # vyšší stratum se připojí PRVNÍ, aby pořadí nemohlo vzniknout náhodou
    kb.attach_rule(
        head=atom("vysoke", role("x", x)),
        body=(atom("zaklad", role("x", x)), atom("nizke", role("x", x), negated=True)),
        rule_id="p_high",
    )
    kb.attach_rule(
        head=atom("nizke", role("x", x), negated=True),
        body=(atom("zaklad", role("x", x)),),
        rule_id="p_low",
    )
    order = [rule.id for rule in kb.view().rules]
    assert order.index("p_low") < order.index("p_high")


def test_revoking_disjoint_cascades_to_derived_rules() -> None:
    kb = KnowledgeBase()
    marker, left, right = kb.add_disjoint(Group("stroj"), Group("člověk"))
    revoked = kb.revoke(marker, "oprava zadání")
    assert set(revoked) == {marker, left, right}
    assert list(kb.active()) == []
    # Historie zůstává — nic se nemaže, jen neplatí (§ 3.7 zadání).
    assert len(kb.history()) == 3


# --------------------------------------------------------------------------
# Důkaz (§ 7)
# --------------------------------------------------------------------------


def test_canonical_proof_selection_is_deterministic() -> None:
    a = Proof(ProofKind.CLOSURE, "subset*", (Proof(ProofKind.FACT, "s0009"),))
    b = Proof(ProofKind.CLOSURE, "subset*", (Proof(ProofKind.FACT, "s0002"),))
    assert select_canonical([a, b]) is b
    assert select_canonical([b, a]) is b
    assert select_canonical([]) is None


def test_non_minimal_proof_is_discarded() -> None:
    """§ 7: důkaz, jehož listy jsou vlastní nadmnožinou jiného, není
    minimální — obsahuje krok, bez kterého by se verdikt odvodil taky."""
    lean = Proof(ProofKind.CLOSURE, "x", (Proof(ProofKind.FACT, "s0001"),))
    fat = Proof(
        ProofKind.CLOSURE,
        "x",
        (Proof(ProofKind.FACT, "s0001"), Proof(ProofKind.FACT, "s0002")),
    )
    assert select_canonical([fat, lean]) is lean
    assert select_canonical([lean, fat]) is lean


def test_canonical_proof_prefers_the_smaller_leaf_set() -> None:
    """§ 7, první stupeň klíče: mezi dvěma NEPOROVNATELNÝMI minimálními
    důkazy vyhrává ten s méně listy — i když má lexikograficky vyšší id.

    Přímý fakt se tu připojuje POSLEDNÍ, takže pod čistě lexikografickým
    pravidlem by prohrál s dvoukrokovým řetězem.
    """
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_c"), Group("citron")))  # s0001
    kb.attach(subset_of(Group("citron"), Group("ovoce")))  # s0002
    direct = kb.attach(member_of(Entity("e_c"), Group("ovoce")))  # s0003
    proof = kb.view().member_proof("e_c", "ovoce")
    assert proof is not None
    assert proof.leaves() == {direct}


def test_canonical_proof_is_independent_of_attach_order() -> None:
    """Táž znalost vložená v opačném pořadí dává důkaz téhož TVARU."""

    def leaf_count(direct_first: bool) -> int:
        kb = KnowledgeBase()
        if direct_first:
            kb.attach(member_of(Entity("e_c"), Group("ovoce")))
        kb.attach(member_of(Entity("e_c"), Group("citron")))
        kb.attach(subset_of(Group("citron"), Group("ovoce")))
        if not direct_first:
            kb.attach(member_of(Entity("e_c"), Group("ovoce")))
        proof = kb.view().member_proof("e_c", "ovoce")
        assert proof is not None
        return len(proof.leaves())

    assert leaf_count(True) == leaf_count(False) == 1


def test_proof_is_stable_across_rebuilds() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_c"), Group("citron")))
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    kb.attach(subset_of(Group("ovoce"), Group("potravina")))
    first = kb.view().member_proof("e_c", "potravina")
    kb.attach(member_of(Entity("e_p"), Group("pomeranč")))  # nesouvisející zápis
    second = kb.view().member_proof("e_c", "potravina")
    assert first is not None and second is not None
    assert first.render() == second.render()


def test_proof_tree_renders_for_the_master_prompt_api() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_c"), Group("citron")))
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    proof = kb.view().member_proof("e_c", "ovoce")
    assert proof is not None
    lines = proof.render()
    assert lines[0] == "closure(member*)"
    assert any(line.strip().startswith("fact(") for line in lines)


# --------------------------------------------------------------------------
# Rozhraní (§ 9)
# --------------------------------------------------------------------------


def test_revoke_keeps_history_and_reason() -> None:
    kb = KnowledgeBase()
    sid = kb.attach(member_of(Entity("a1"), Group("modrý")), provenance="stated(t2)")
    kb.revoke(sid, "oprava: bylo červené")
    stmt, active, reason = kb.inspect(sid)
    assert active is False
    assert reason == "oprava: bylo červené"
    assert stmt.provenance == "stated(t2)"
    assert list(kb.active()) == []


def test_dependency_graphs_are_not_rebuilt_for_every_fact() -> None:
    """W‑1: grafy závisí jen na pravidlech a na třídách ekvivalence.

    Zápis faktu je nemění, a faktů je v dialogu řádově víc než pravidel —
    bez zapamatované stavby rostl náklad kvadraticky s délkou rozhovoru.
    Měří se POČET staveb, ne čas: „stavíme míň" je tvrzení o počtu (I‑4).
    """
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        rule_id="p1",
        head=atom("b", role("x", x)),
        body=(atom("a", role("x", x)),),
    )
    kb.view()
    builds = kb.graph_builds

    for index in range(50):
        kb.attach(member_of(Entity(f"e{index}"), Group("g")))
        kb.view()
    assert kb.graph_builds == builds


def test_identity_edge_does_rebuild_the_graphs() -> None:
    """Scelení naopak stavbu vyžaduje — mění třídy, přes které se
    v `_unifies` porovnávají konstanty."""
    kb = KnowledgeBase()
    x = Variable("x")
    kb.attach_rule(
        rule_id="p1",
        head=atom("b", role("x", x)),
        body=(atom("a", role("x", x)),),
    )
    kb.view()
    builds = kb.graph_builds
    kb.attach(same_as_of(Group("ga"), Group("gb")))
    assert kb.graph_builds > builds


def test_query_does_not_write_to_the_base() -> None:
    """Otázka nemění bázi (I‑12) — pohled je odvozený, ne uložený."""
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    before = len(kb.history())
    kb.view().subset_proof("citron", "ovoce")
    kb.view().member_proof("e_x", "ovoce")
    assert len(kb.history()) == before
