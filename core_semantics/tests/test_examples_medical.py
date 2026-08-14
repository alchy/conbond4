"""Akceptační dialog — „Lékařská kontraindikace".

Zdroj: „Pacient Jan má alergii na Penicilin. Amoxicilin je druh Penicilinu.
Kdo je alergický na látku, nesmí dostat lék obsahující tuto látku ani její
podtřídu. Curam obsahuje Amoxicilin. Smí Jan dostat Curam?"

Co se tu láme: **kaskáda `subset*` do silné negace** a **otevřený svět
u pacienta bez anamnézy**. Druhá polovina je ta důležitější: o Petrovi,
o kterém nic nevíme, se NESMÍ říct, že lék dostat smí. `U` není slabší
odpověď — je to jediná bezpečná.

## Pozor na pořadí literálů v těle (W‑5)

Jádrový predikát v těle vyžaduje, aby **obě** jeho role byly vázané
v okamžiku, kdy na ně dojde řada. `subset(L2, L1)` se dvěma dosud
nevázanými proměnnými skončí `EvaluationError`. Tělo `R5` je proto
uspořádané tak, aby `subset` přišel až po `alergie_na` (naváže `L1`)
a `obsahuje` (naváže `L2`).

V deklarativním čtení Hornovy klauzule je pořadí konjunktů lhostejné, tady
lhostejné není — autor pravidla musí znát vyhodnocovací strategii.
Selhává to ale **hlasitě**, ne tiše, a to je záměr (I‑1).
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    Atom,
    Entity,
    Group,
    Quantifier,
    QueryStatus,
    Sort,
    Variable,
    atom,
    role,
    subset_of,
)
from core_semantics.engine import Engine, EvaluationError
from core_semantics.storage import KnowledgeBase

SELF = Quantifier.SELF


def _substance(name: str) -> Variable:
    return Variable(name, expects=Sort.GROUP)


def _base(*, ordered_body: bool = True) -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(
        atom(
            "alergie_na",
            role("who", Entity("Jan")),
            role("what", Group("Penicilin"), SELF),
        )
    )
    kb.attach(subset_of(Group("Amoxicilin"), Group("Penicilin")))
    kb.attach(
        atom(
            "obsahuje",
            role("what", Group("Curam"), SELF),
            role("látka", Group("Amoxicilin"), SELF),
        )
    )

    patient = Variable("P")
    medicine = _substance("M")
    allergen = _substance("L1")
    ingredient = _substance("L2")
    allergy = atom(
        "alergie_na", role("who", patient), role("what", allergen, SELF)
    )
    contains = atom(
        "obsahuje", role("what", medicine, SELF), role("látka", ingredient, SELF)
    )
    narrower = subset_of(ingredient, allergen)
    body = (
        (allergy, contains, narrower) if ordered_body else (allergy, narrower, contains)
    )
    kb.attach_rule(
        rule_id="R5",
        head=atom(
            "smí_dostat",
            role("who", patient),
            role("what", medicine, SELF),
            negated=True,
        ),
        body=body,
    )
    return kb


def _may_receive(patient: str, medicine: str) -> Atom:
    return atom(
        "smí_dostat",
        role("who", Entity(patient)),
        role("what", Group(medicine), SELF),
    )


def test_contraindication_is_proven_false() -> None:
    """Fáze B — Jan je alergický na penicilin, Curam obsahuje amoxicilin
    a ten je penicilin. Kaskáda `subset*` musí být v důkazu vidět."""
    result = Engine(_base()).ask(_may_receive("Jan", "Curam"))
    assert result.status is QueryStatus.PROVEN_FALSE
    assert result.proof is not None
    assert any("subset*" in line for line in result.proof_tree)


def test_patient_without_history_stays_unknown() -> None:
    """Fáze A — o Petrovi nevíme nic. `U`, nikdy „smí".

    Tohle je důvod, proč se v téhle doméně nesmí uzavírat svět volnými
    defaulty: default „pacient bez známé alergie → smí dostat" by proměnil
    nevědomost v povolení k podání léku.
    """
    result = Engine(_base()).ask(_may_receive("Petr", "Curam"))
    assert result.status is QueryStatus.UNKNOWN


def test_unrelated_allergy_is_not_invented() -> None:
    kb = _base()
    query = atom(
        "alergie_na",
        role("who", Entity("Jan")),
        role("what", Group("Paracetamol"), SELF),
    )
    assert Engine(kb).ask(query).status is QueryStatus.UNKNOWN


def test_medicine_without_the_allergen_is_not_refused() -> None:
    """Silná negace se nesmí rozlít na lék, který alergen neobsahuje."""
    kb = _base()
    kb.attach(
        atom(
            "obsahuje",
            role("what", Group("Ibalgin"), SELF),
            role("látka", Group("Ibuprofen"), SELF),
        )
    )
    assert Engine(kb).ask(_may_receive("Jan", "Ibalgin")).status is QueryStatus.UNKNOWN


def test_body_order_matters_and_fails_loudly() -> None:
    """W‑5 zafixované: `subset` před navázáním obou stran spadne s hláškou,
    ne tiše. Táž klauzule, jiné pořadí, jiný výsledek."""
    kb = _base(ordered_body=False)
    with pytest.raises(EvaluationError, match="vázané"):
        Engine(kb).ask(_may_receive("Jan", "Curam"))
