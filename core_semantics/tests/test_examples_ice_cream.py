"""Akceptační dialog — „Jana, děti a zmrzlina".

Zdroj: „Jana je učitelka. Učitelka učí děti. Děti mají rády zmrzlinu.
Za odměnu Jana koupí dětem, co mají rády."

Co se tu láme: **skládání dvou `∃`-relací za sebou**. Řetěz vede
`Učitelka →učí→ Děti →mají_rády→ Zmrzlina`, a v obou článcích je cíl
existenční. Závěr proto smí být jen `∃Zmrzlina` — vybrat z řetězu
konkrétní zmrzlinu by byla skolemizace v inferenci (§ 0/2).

Naivní pravidlo `učí(o,s) ∧ mají_rády(s,v) ⇒ koupí(o,v)` s konkrétními
fillery se na fakta **nechytí vůbec**: `konkrétní × ∀` s proměnnou vrací
`None` (enumeraci členů dělá `member` v těle) a `konkrétní × ∃` nesedí
nikdy. Pravidlo proto musí sáhnout na reifikované role — týž tvar jako
`p3` v § 10 dokumentu.
"""

from __future__ import annotations

from core_semantics.ast import (
    Atom,
    Entity,
    Group,
    Label,
    P_ROLE_EXISTS,
    P_ROLE_FORALL,
    Quantifier,
    QueryStatus,
    Sort,
    Term,
    Variable,
    atom,
    member_of,
    role,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.storage import KnowledgeBase

FOR_ALL = Quantifier.FOR_ALL
EXISTS = Quantifier.EXISTS
SELF = Quantifier.SELF


def _role_access(predicate: str, instance: Term, name: str, filler: Term) -> Atom:
    """Dekomponovaný přístup k roli reifikovaného vztahu (§ 2).

    Kvantifikátor je v NÁZVU predikátu, takže samotný filler vystupuje
    jako objekt — proto `SELF`."""
    return atom(
        predicate,
        role("of", instance),
        role("name", Label(name)),
        role("filler", filler, SELF),
    )


def _base(*, with_rule: bool) -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Jana"), Group("Učitelka")))
    kb.attach(
        atom(
            "učí",
            role("who", Group("Učitelka"), FOR_ALL),
            role("what", Group("Děti"), EXISTS),
        )
    )
    kb.attach(
        atom(
            "mají_rády",
            role("who", Group("Děti"), FOR_ALL),
            role("what", Group("Zmrzlina"), EXISTS),
        )
    )
    if not with_rule:
        return kb

    teaching = Variable("R")
    liking = Variable("S")
    person = Variable("O")
    teacher_group = Variable("G1", expects=Sort.GROUP)
    pupil_group = Variable("G2", expects=Sort.GROUP)
    treat_group = Variable("VG", expects=Sort.GROUP)
    kb.attach_rule(
        rule_id="R2",
        head=atom(
            "koupí_za_odměnu",
            role("who", person),
            role("what", treat_group, EXISTS),
        ),
        body=(
            member_of(teaching, Group("učí")),
            _role_access(P_ROLE_FORALL, teaching, "who", teacher_group),
            _role_access(P_ROLE_EXISTS, teaching, "what", pupil_group),
            member_of(person, teacher_group),
            member_of(liking, Group("mají_rády")),
            # táž skupina dětí v obou článcích řetězu — unifikace přes G2
            _role_access(P_ROLE_FORALL, liking, "who", pupil_group),
            _role_access(P_ROLE_EXISTS, liking, "what", treat_group),
        ),
    )
    return kb


def _asks_for_some_ice_cream() -> Atom:
    return atom(
        "koupí_za_odměnu",
        role("who", Entity("Jana")),
        role("what", Group("Zmrzlina"), EXISTS),
    )


def test_without_the_rule_the_chain_is_not_composed() -> None:
    """Fáze A — engine si chybějící můstek nedomýšlí."""
    result = Engine(_base(with_rule=False)).ask(_asks_for_some_ice_cream())
    assert result.status is QueryStatus.UNKNOWN


def test_rule_over_reified_roles_composes_two_relations() -> None:
    """Fáze B — `R2` skládá `učí` a `mají_rády` přes `role_forall`/`role_exists`."""
    result = Engine(_base(with_rule=True)).ask(_asks_for_some_ice_cream())
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None and "R2" in result.proof.leaves()
    rendered = result.proof_tree
    assert any("role_forall" in line or "role_exists" in line for line in rendered) or (
        "R2" in "".join(rendered)
    )


def test_no_witness_is_picked_out_of_the_chain() -> None:
    """Závěr smí být jen `∃Zmrzlina`. Konkrétní nanuk z řetězu neplyne —
    a to i když je doloženo, že do skupiny patří."""
    kb = _base(with_rule=True)
    kb.attach(member_of(Entity("e_nanuk"), Group("Zmrzlina")))
    concrete = atom(
        "koupí_za_odměnu",
        role("who", Entity("Jana")),
        role("what", Entity("e_nanuk")),
    )
    assert Engine(kb).ask(concrete).status is QueryStatus.UNKNOWN


def test_widening_the_existential_target_still_holds() -> None:
    """D2: `∃` se šíří nahoru, takže „koupí něco sladkého" plyne."""
    kb = _base(with_rule=True)
    kb.attach(subset_of(Group("Zmrzlina"), Group("Sladkost")))
    wider = atom(
        "koupí_za_odměnu",
        role("who", Entity("Jana")),
        role("what", Group("Sladkost"), EXISTS),
    )
    assert Engine(kb).ask(wider).status is QueryStatus.PROVEN_TRUE


def test_disjoint_treats_reach_the_subclass() -> None:
    """Zmrzlina a zelenina se vylučují, brokolice je zelenina — takže
    Míša (zmrzlina) prokazatelně brokolice není."""
    kb = _base(with_rule=False)
    kb.add_disjoint(Group("Zmrzlina"), Group("Zelenina"))
    kb.attach(subset_of(Group("Brokolice"), Group("Zelenina")))
    kb.attach(member_of(Entity("Míša"), Group("Zmrzlina")))
    result = Engine(kb).ask(member_of(Entity("Míša"), Group("Brokolice")))
    assert result.status is QueryStatus.PROVEN_FALSE
    assert any("member̄*" in line for line in result.proof_tree)
