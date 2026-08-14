"""Akceptační sada — fáze F0.4 (epistemická vrstva).

Pokrývá § 4 (kombinace verdiktů), § 6.2 zadání (složené a alternativní
otázky), § 3.1–3.2 (dvojí extenze, `DIFF`), § 6.4 zadání (výčet a počet
s otevřeně-světovou doložkou) a § 6 (mez veličiny).
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
    Value,
    Variable,
    atom,
    complete_of,
    measure_of,
    member_of,
    role,
    same_as_of,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.epistemics import (
    EpistemicError,
    Extension,
    combine,
    query_alt,
    query_bound,
    query_conjunction,
    query_count,
    query_diff,
    query_enum,
)
from core_semantics.storage import KnowledgeBase

A = QueryStatus.PROVEN_TRUE
N = QueryStatus.PROVEN_FALSE
U = QueryStatus.UNKNOWN
CONFLICT = QueryStatus.CONFLICT


# --------------------------------------------------------------------------
# Kombinace verdiktů (§ 4)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (A, A, A), (A, U, U), (A, N, N),
        (U, A, U), (U, U, U), (U, N, N),
        (N, A, N), (N, U, N), (N, N, N),
    ],
)
def test_kleene_conjunction(left: QueryStatus, right: QueryStatus, expected: QueryStatus) -> None:
    assert combine([left, right], conjunction=True) is expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (A, A, A), (A, U, A), (A, N, A),
        (U, A, A), (U, U, U), (U, N, U),
        (N, A, A), (N, U, U), (N, N, N),
    ],
)
def test_kleene_disjunction(left: QueryStatus, right: QueryStatus, expected: QueryStatus) -> None:
    assert combine([left, right], conjunction=False) is expected


def test_conflict_is_not_a_truth_value_in_the_tables() -> None:
    """§ 4: `CONFLICT` se nekombinuje, propaguje se jako stav dotazu."""
    assert combine([A, CONFLICT], conjunction=True) is CONFLICT
    assert combine([N, CONFLICT], conjunction=False) is CONFLICT


# --------------------------------------------------------------------------
# Složené a alternativní otázky (§ 6.2 zadání)
# --------------------------------------------------------------------------


def _fruit_base() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    kb.attach(member_of(Entity("e_c"), Group("citron")))
    kb.add_disjoint(Group("ovoce"), Group("zelenina"))
    return kb


def test_partial_answer_is_mandatory() -> None:
    """`A ∧ U ⇒ U`, ale známá půlka se nesmí zahodit (§ 6.2 zadání)."""
    engine = Engine(_fruit_base())
    known_part = member_of(Entity("e_c"), Group("ovoce"))
    unknown_part = member_of(Entity("e_c"), Group("šťavnaté"))
    result = query_conjunction(engine, [known_part, unknown_part])
    assert result.status is U
    assert result.certain() == (known_part,)
    assert result.missing() == (unknown_part,)


def test_alternative_question_answers_with_a_member() -> None:
    engine = Engine(_fruit_base())
    result = query_alt(
        engine,
        [
            member_of(Entity("e_c"), Group("ovoce")),
            member_of(Entity("e_c"), Group("zelenina")),
        ],
    )
    assert result.status is A
    assert result.chosen == member_of(Entity("e_c"), Group("ovoce"))


def test_alternative_question_is_epistemic_not_object_level() -> None:
    """„Je citron zelenina, nebo není?" → `U`.

    Objektově je `φ ∨ ¬φ` tautologie a odpověď by byla `A` bez svědka.
    Epistemicky je to `K φ ∨ K φ̄`, a to doložené není ani jedno.
    """
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_c"), Group("citron")))
    engine = Engine(kb)
    positive = member_of(Entity("e_c"), Group("zelenina"))
    result = query_alt(engine, [positive, positive.complement()])
    assert result.status is U
    assert result.chosen is None


def test_alternative_question_reports_two_true_members() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_c"), Group("ovoce")))
    kb.attach(member_of(Entity("e_c"), Group("zelenina")))
    result = query_alt(
        Engine(kb),
        [
            member_of(Entity("e_c"), Group("ovoce")),
            member_of(Entity("e_c"), Group("zelenina")),
        ],
    )
    assert result.status is CONFLICT
    assert result.chosen is None


# --------------------------------------------------------------------------
# Výčet, počet, rozdíl (§ 6.4 zadání)
# --------------------------------------------------------------------------


def test_enumeration_is_a_lower_bound_without_complete() -> None:
    kb = KnowledgeBase()
    for name in ("citron", "pomeranč", "jablko"):
        kb.attach(member_of(Entity(f"e_{name}"), Group("ovoce")))
    count, caveat = query_count(Engine(kb), Group("ovoce"))
    assert count == 3
    assert "nevím" in caveat


def test_complete_turns_the_lower_bound_into_an_equality() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_citron"), Group("ovoce")))
    sid = kb.attach(complete_of(Group("ovoce")))
    extension = query_enum(Engine(kb), Group("ovoce"))
    assert extension.complete == sid
    assert "všichni" in extension.caveat()


def test_counting_collapses_equivalence_classes() -> None:
    """Bez UNA se počítají třídy, ne id — ale jen ty doložené (§ 1.2)."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("a1"), Group("auto")))
    kb.attach(member_of(Entity("a2"), Group("auto")))
    assert query_count(Engine(kb), Group("auto"))[0] == 2
    kb.attach(same_as_of(Entity("a1"), Entity("a2")))
    assert query_count(Engine(kb), Group("auto"))[0] == 1


def test_diff_separates_proven_absence_from_ignorance() -> None:
    """„Kteří spisovatelé nejsou básníci?" — „vím, že není" × „nevím, že je"."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_hrabal"), Group("spisovatel")))
    kb.attach(member_of(Entity("e_seifert"), Group("spisovatel")))
    kb.attach(member_of(Entity("e_seifert"), Group("básník")))
    kb.add_disjoint(Group("básník"), Group("prozaik"))
    kb.attach(member_of(Entity("e_hrabal"), Group("prozaik")))

    result = query_diff(Engine(kb), Group("spisovatel"), Group("básník"))
    # Hrabal je prozaik a prozaik je neslučitelný s básníkem → doloženo.
    assert [t.id for t in result.certain] == ["e_hrabal"]
    assert result.uncertain == ()


def test_complete_denies_membership_of_a_non_member() -> None:
    """§ 5.1, schváleno 14. 8. 2026: `complete(g)` zesiluje `U → N`.

    Je to jediné místo v jádře, kde závěr plyne z absence — proto se
    vyhodnocuje až při dotazu a nikdy se nematerializuje do pevného bodu.
    """
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_citron"), Group("ovoce")))
    kb.attach(member_of(Entity("e_kladivo"), Group("nářadí")))
    sid = kb.attach(complete_of(Group("ovoce")))

    result = Engine(kb).ask(member_of(Entity("e_kladivo"), Group("ovoce")))
    assert result.status is N
    assert result.proof is not None and sid in result.proof.leaves()
    assert any("complete*" in line for line in result.proof_tree)


def test_completing_a_supergroup_closes_its_subgroups() -> None:
    """Skládá se s kontrapozicí: `x ∉ g` a `A ⊆ g` dává `x ∉ A`."""
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("citron"), Group("ovoce")))
    kb.attach(member_of(Entity("e_kladivo"), Group("nářadí")))
    kb.attach(complete_of(Group("ovoce")))

    result = Engine(kb).ask(member_of(Entity("e_kladivo"), Group("citron")))
    assert result.status is N
    assert any("subset*" in line for line in result.proof_tree)


def test_complete_does_not_deny_an_actual_member() -> None:
    """Uzavření skupiny nesmí popřít prvek, který v ní doloženě je —
    jinak by `complete(g)` vyrobilo falešný `CONFLICT`."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_citron"), Group("ovoce")))
    kb.attach(complete_of(Group("ovoce")))
    result = Engine(kb).ask(member_of(Entity("e_citron"), Group("ovoce")))
    assert result.status is A


def test_caveat_never_claims_completeness_while_something_is_open() -> None:
    """B‑1 část 2 — doložka a data si nesmí odporovat v jedné odpovědi.

    Po zavedení B‑I je tenhle stav v enginu nedosažitelný (`complete(g)`
    každý nečlen rovnou vyvrátí), takže se testuje přímo na struktuře.
    Kontrola v `caveat()` zůstává jako pojistka: kdyby se `possible`
    někdy plnilo jinou cestou, odpověď nesmí začít lhát.
    """
    leaky = Extension(
        group=Group("ovoce"),
        certain=(Entity("e_citron"),),
        possible=(Entity("e_citron"), Entity("e_kladivo")),
        conflicted=(),
        complete="s0003",
    )
    caveat = leaky.caveat()
    assert [t.id for t in leaky.uncertain] == ["e_kladivo"]
    assert "s0003" in caveat
    assert "To jsou všichni" not in caveat


def test_conflicted_membership_is_reported_not_flattened_to_unknown() -> None:
    """§ 6.0, I‑1, I‑3: „nevím" a „báze si o tom odporuje" jsou dva různé
    stavy. Kdyby konflikt propadl do `uncertain`, žádný renderer už ho
    z těch dat nevytáhne."""
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("spisovatel"), Group("člověk")))
    kb.add_disjoint(Group("stroj"), Group("člověk"))
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    kb.attach(member_of(Entity("e17"), Group("stroj")))

    engine = Engine(kb)
    assert engine.ask(member_of(Entity("e17"), Group("stroj"))).status is CONFLICT

    extension = query_enum(engine, Group("stroj"))
    assert [t.id for t in extension.conflicted] == ["e17"]
    assert extension.uncertain == ()
    assert "odporuje" in extension.caveat()


def test_reified_relations_do_not_pollute_an_enumeration() -> None:
    """Doložka nesmí vypisovat neprůhledná id výroků jako jednotliviny.

    Reifikovaná instance vztahu je uzel s id `sNNNN`; tvrdit lékaři
    „u s0002 nevím, jestli je pacient" je nepoužitelné (§ 8). Kandidáti
    se proto zužují na sorty, které ve skupině doloženě jsou.
    """
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Jan"), Group("pacient")))
    kb.attach(
        atom(
            "alergie_na",
            role("kdo", Entity("Jan")),
            role("na", Group("penicilin"), Quantifier.SELF),
        )
    )
    extension = query_enum(Engine(kb), Group("pacient"))
    assert [t.id for t in extension.certain] == ["Jan"]
    assert [t.id for t in extension.possible] == ["Jan"]
    assert "s0" not in extension.caveat()


def test_relation_type_still_enumerates_its_instances() -> None:
    """§ 3.4: typ vztahu JE group svých instancí — zúžení kandidátů tuhle
    schopnost nesmí zabít."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Jan"), Group("pacient")))
    sid = kb.attach(
        atom(
            "alergie_na",
            role("kdo", Entity("Jan")),
            role("na", Group("penicilin"), Quantifier.SELF),
        )
    )
    extension = query_enum(Engine(kb), Group("alergie_na"))
    assert [t.id for t in extension.certain] == [sid]


def test_enumeration_fast_path_agrees_with_the_general_path() -> None:
    """W‑2: bez jediného `member̄` a bez `complete(g)` nemůže u členství
    vzniknout `N` ani `CONFLICT`, takže se výčet nemusí ptát vůbec.

    Zkratka je bezpečná jen potud, pokud dává tytéž odpovědi jako obecná
    cesta — proto se táž báze staví dvakrát, jednou s nesouvisejícím
    záporným faktem, který obecnou cestu vynutí.
    """

    def build(*, with_negative: bool) -> KnowledgeBase:
        kb = KnowledgeBase()
        kb.attach(member_of(Entity("e_citron"), Group("ovoce")))
        kb.attach(member_of(Entity("e_kladivo"), Group("nářadí")))
        if with_negative:
            kb.attach(
                member_of(Entity("e_kladivo"), Group("zelenina"), negated=True)
            )
        return kb

    fast = query_enum(Engine(build(with_negative=False)), Group("ovoce"))
    general = query_enum(Engine(build(with_negative=True)), Group("ovoce"))
    assert [t.id for t in fast.certain] == [t.id for t in general.certain]
    assert [t.id for t in fast.possible] == [t.id for t in general.possible]
    assert fast.conflicted == general.conflicted == ()
    assert fast.caveat() == general.caveat()


def test_empty_group_offers_no_candidates() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Jan"), Group("pacient")))
    extension = query_enum(Engine(kb), Group("lékař"))
    assert extension.certain == ()
    assert extension.possible == ()
    assert "netvrdím nic" in extension.caveat()


def test_diff_exposes_both_specification_branches() -> None:
    """§ 3.2 má dvě formule a `DIFF` musí nést obě, jinak není skladatelný
    podle § 3.0. `uncertain` je proti nim UŽŠÍ množina pro renderování."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_hrabal"), Group("spisovatel")))
    kb.attach(member_of(Entity("e_seifert"), Group("spisovatel")))
    kb.attach(member_of(Entity("e_seifert"), Group("básník")))
    kb.attach(member_of(Entity("e_kladivo"), Group("nářadí")))

    result = query_diff(Engine(kb), Group("spisovatel"), Group("básník"))
    # certain(A) \ possible(B): o nikom není doloženo, že básník NENÍ
    assert result.certain == ()
    # possible(A) \ certain(B): spec formule — nese i prvek mimo `certain(A)`
    assert [t.id for t in result.possible] == ["e_hrabal", "e_kladivo"]
    # užší množina pro § 6.4: „o Hrabalovi vím, že je spisovatel, a jen
    # nevím, jestli je i básník"
    assert [t.id for t in result.uncertain] == ["e_hrabal"]


def test_diff_keeps_the_undecided_member_out_of_certain() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e_hrabal"), Group("spisovatel")))
    result = query_diff(Engine(kb), Group("spisovatel"), Group("básník"))
    assert result.certain == ()
    assert [t.id for t in result.uncertain] == ["e_hrabal"]
    assert "nevím" in result.caveat()


# --------------------------------------------------------------------------
# Mez veličiny (§ 6) — dialog A
# --------------------------------------------------------------------------


def _dialog_a_with_bridge() -> tuple[KnowledgeBase, str]:
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("auto"), Group("DP")))
    jezdit = kb.attach(
        atom(
            "jezdit",
            role("who", Group("DP"), Quantifier.FOR_ALL),
            role("via", Group("dálnice"), Quantifier.EXISTS),
        )
    )
    kb.attach(
        atom(
            "omezení",
            role("of", Group("dálnice"), Quantifier.FOR_ALL),
            role("quantity", Label("rychlost")),
            role("limit", Value("v130", "rychlost", Decimal(130), "km/h")),
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
    return kb, jezdit


def test_bound_query_returns_the_limit() -> None:
    kb, jezdit = _dialog_a_with_bridge()
    result = query_bound(
        Engine(kb), RelationInstance(jezdit), "rychlost", Comparator.LE
    )
    assert result.status is A
    assert result.value is not None
    assert result.value.magnitude == Decimal(130)
    assert result.proof is not None and "p3" in result.proof.leaves()


def test_bound_query_takes_the_tightest_limit() -> None:
    """Odvoditelné meze jsou podmnožinou literálů v bázi; horní mez je
    minimum nad nimi, ne libovolná z nich."""
    kb, jezdit = _dialog_a_with_bridge()
    kb.attach(
        atom(
            "omezení",
            role("of", Group("dálnice"), Quantifier.FOR_ALL),
            role("quantity", Label("rychlost")),
            role("limit", Value("v90", "rychlost", Decimal(90), "km/h")),
        )
    )
    result = query_bound(
        Engine(kb), RelationInstance(jezdit), "rychlost", Comparator.LE
    )
    assert result.value is not None
    assert result.value.magnitude == Decimal(90)


def test_bound_query_without_a_derivation_is_unknown() -> None:
    kb = KnowledgeBase()
    kb.attach(
        atom(
            "omezení",
            role("of", Group("dálnice"), Quantifier.FOR_ALL),
            role("quantity", Label("rychlost")),
            role("limit", Value("v130", "rychlost", Decimal(130), "km/h")),
        )
    )
    result = query_bound(Engine(kb), Entity("e_petr"), "rychlost", Comparator.LE)
    assert result.status is U
    assert result.value is None


def test_bound_query_refuses_to_mix_units() -> None:
    """Převod jednotek je aritmetika, tedy mimo v1 — hlášená chyba, ne
    tichý výběr jedné z nich."""
    kb, jezdit = _dialog_a_with_bridge()
    kb.attach(
        atom(
            "omezení",
            role("of", Group("dálnice"), Quantifier.FOR_ALL),
            role("quantity", Label("rychlost")),
            role("limit", Value("v50", "rychlost", Decimal(50), "mph")),
        )
    )
    with pytest.raises(EpistemicError):
        query_bound(Engine(kb), RelationInstance(jezdit), "rychlost", Comparator.LE)


def test_bound_query_rejects_a_non_bounding_comparator() -> None:
    kb, jezdit = _dialog_a_with_bridge()
    with pytest.raises(EpistemicError):
        query_bound(
            Engine(kb), RelationInstance(jezdit), "rychlost", Comparator.NE
        )
