"""Akceptační dialog — „Petrovice".

Zdroj: „Pes Roník bydlí ve vesničce Petrovice. Kočka Micka bydlí též ve
vesničce Petrovice. Radek bydlí ve stejném místě jako kočka Micka."

Co se tu láme: **unifikace proměnné přes dva nezávislé fakty** a
**pruning důkazu** — Roník bydlí v témž místě, ale do vysvětlení o
Radkovi se dostat nesmí.

## Volba u pravidla R4 a proč

Zadání navrhuje `bydlí_v(A,L) <- stejné_místo(A,B) ∧ bydlí_v(B,L)`. To je
**přímá rekurze** (predikát `bydlí_v` v hlavě i v těle) a § 5.4/5 ji
v naučeném programu zakazuje — `attach` pravidlo odmítne `CycleDetected`.
Nabízely se tři cesty; volím **přejmenování hlavy** na
`bydlí_v_odvozeně`, a to ze tří důvodů:

1. Funguje okamžitě a nesahá na verzované jádro (I‑13).
2. Modelování přes `same_as` by tvrdilo identitu *osob*, ne *míst* —
   muselo by se nejdřív zavést uzel pro bydliště, což je větší zásah do
   domény než do kódu.
3. **Odvozený predikát je věcně poctivější.** „Radek bydlí v Petrovicích"
   nikdo neřekl; je to závěr. Oddělený predikát ten rozdíl drží viditelný
   v odpovědi, místo aby ho slil s tím, co bylo tvrzeno.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    CycleDetected,
    Entity,
    Place,
    QueryStatus,
    Variable,
    atom,
    role,
)
from core_semantics.engine import Engine
from core_semantics.storage import KnowledgeBase

PETROVICE = Place("Petrovice")


def _base() -> tuple[KnowledgeBase, dict[str, str]]:
    kb = KnowledgeBase()
    ids = {
        "roník": kb.attach(
            atom("bydlí_v", role("who", Entity("Roník")), role("kde", PETROVICE))
        ),
        "micka": kb.attach(
            atom("bydlí_v", role("who", Entity("Micka")), role("kde", PETROVICE))
        ),
        "radek": kb.attach(
            atom(
                "stejné_místo",
                role("a", Entity("Radek")),
                role("b", Entity("Micka")),
            )
        ),
    }
    first, second, place = Variable("A"), Variable("B"), Variable("L")
    kb.attach_rule(
        rule_id="R3",
        head=atom("stejná_vesnice", role("a", first), role("b", second)),
        body=(
            atom("bydlí_v", role("who", first), role("kde", place)),
            atom("bydlí_v", role("who", second), role("kde", place)),
        ),
    )
    return kb, ids


def test_variable_unifies_across_two_independent_facts() -> None:
    """`L` se naváže na Petrovice prvním literálem a druhý ho musí potvrdit."""
    kb, ids = _base()
    result = Engine(kb).ask(
        atom(
            "stejná_vesnice",
            role("a", Entity("Roník")),
            role("b", Entity("Micka")),
        )
    )
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None
    assert result.proof.leaves() == {"R3", ids["roník"], ids["micka"]}


def test_recursive_rule_is_rejected() -> None:
    """R4 tak, jak je v zadání — hlava i tělo mají `bydlí_v`."""
    kb, _ = _base()
    first, second, place = Variable("A"), Variable("B"), Variable("L")
    with pytest.raises(CycleDetected):
        kb.attach_rule(
            rule_id="R4",
            head=atom("bydlí_v", role("who", first), role("kde", place)),
            body=(
                atom("stejné_místo", role("a", first), role("b", second)),
                atom("bydlí_v", role("who", second), role("kde", place)),
            ),
        )


def _with_derived_rule() -> tuple[KnowledgeBase, dict[str, str]]:
    kb, ids = _base()
    first, second, place = Variable("A"), Variable("B"), Variable("L")
    kb.attach_rule(
        rule_id="R4b",
        head=atom("bydlí_v_odvozeně", role("who", first), role("kde", place)),
        body=(
            atom("stejné_místo", role("a", first), role("b", second)),
            atom("bydlí_v", role("who", second), role("kde", place)),
        ),
    )
    return kb, ids


def test_derived_predicate_locates_radek() -> None:
    kb, ids = _with_derived_rule()
    result = Engine(kb).ask(
        atom(
            "bydlí_v_odvozeně",
            role("who", Entity("Radek")),
            role("kde", PETROVICE),
        )
    )
    assert result.status is QueryStatus.PROVEN_TRUE
    assert result.proof is not None
    assert result.proof.leaves() == {"R4b", ids["radek"], ids["micka"]}


def test_unrelated_component_stays_out_of_the_proof() -> None:
    """Pruning se neprogramuje — plyne z § 7.

    Roník bydlí v témž místě, ale `B` je navázané na Micku už prvním
    literálem těla, takže jeho fakt do vysvětlení nevede.
    """
    kb, ids = _with_derived_rule()
    result = Engine(kb).ask(
        atom(
            "bydlí_v_odvozeně",
            role("who", Entity("Radek")),
            role("kde", PETROVICE),
        )
    )
    assert result.proof is not None
    assert ids["roník"] not in result.proof.leaves()


def test_open_world_for_an_unmentioned_person() -> None:
    kb, _ = _with_derived_rule()
    for predicate in ("bydlí_v", "bydlí_v_odvozeně"):
        result = Engine(kb).ask(
            atom(predicate, role("who", Entity("Alena")), role("kde", PETROVICE))
        )
        assert result.status is QueryStatus.UNKNOWN
