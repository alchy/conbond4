"""Kontrola matice smluv — K‑6 zúžené.

Matice, kterou nikdo nekontroluje, je komentář. Tenhle modul je ta část,
kvůli které má smysl ji psát: **doložku nelze označit za drženou, dokud
není řetěz uzavřený.**

Čtyři sloupce, čtyři kontroly, všechny strojové:

* `typ` — symbol, na kterém doložka visí, jde najít (chytá přejmenování)
* `smysl` — u toho symbolu je napsané, co doložka znamená
* `použití` — vynucující test jde **veřejným vstupním bodem**; tenhle
  sloupec by chytil nepředanou `tiers`, protože test nad `cascade()`
  volanou napřímo obchází právě to místo, kde byla vada
* `test` — vynucující test existuje a je v sadě
"""

from __future__ import annotations

import inspect
import pkgutil
from types import ModuleType
from typing import Callable

import pytest

from core_semantics import contracts as contract_module
from core_semantics import tests as tests_package
from core_semantics.contracts import (
    BOUNDARIES,
    CONTRACTS,
    Clause,
    Column,
    Status,
)
from core_semantics.lexicon import czech_seed
from core_semantics.session import Session
from core_semantics.tests._console import echo


def _test_modules() -> tuple[ModuleType, ...]:
    import importlib

    found = []
    for info in pkgutil.iter_modules(tests_package.__path__):
        if info.name.startswith("test_"):
            found.append(importlib.import_module(f"{tests_package.__name__}.{info.name}"))
    return tuple(found)


def _test_functions() -> dict[str, Callable[..., object]]:
    table: dict[str, Callable[..., object]] = {}
    for module in _test_modules():
        for name, value in vars(module).items():
            if name.startswith("test_") and callable(value):
                table.setdefault(name, value)
    return table


TESTS = _test_functions()


def _columns(clause: Clause) -> dict[Column, bool]:
    """Sloupce se **odvozují**, nedeklarují. Deklarovaný sloupec by měřil,
    co si o kódu myslí ten, kdo matici psal."""
    try:
        clause.resolve()
        has_type = True
    except (AttributeError, ImportError, ModuleNotFoundError):
        has_type = False
    named = [TESTS[name] for name in clause.enforced_by if name in TESTS]
    reached = bool(named) and any(
        clause.entry in inspect.getsource(function) for function in named
    )
    return {
        Column.TYPE: has_type,
        Column.MEANING: has_type and clause.documented(),
        Column.REACHED: reached,
        Column.TEST: bool(clause.enforced_by)
        and all(name in TESTS for name in clause.enforced_by),
    }


@pytest.mark.parametrize("clause", CONTRACTS, ids=lambda c: c.id)
def test_anchor_still_exists(clause: Clause) -> None:
    """Přejmenovaný symbol nesmí matici nechat vypadat platně."""
    assert _columns(clause)[Column.TYPE], (
        f"{clause.id}: kotva {clause.anchor!r} se nedá rozřešit — buď se "
        f"něco přejmenovalo, nebo matice zestárla"
    )


@pytest.mark.parametrize("clause", CONTRACTS, ids=lambda c: c.id)
def test_held_clause_has_a_closed_chain(clause: Clause) -> None:
    """Držená doložka musí mít VŠECHNY čtyři sloupce.

    Tohle je věta z K‑6 přeložená do kódu: *CI nesmí dovolit označit
    konstruktor za hotový, dokud není řetěz uzavřený.*
    """
    if clause.status is not Status.HELD:
        pytest.skip("otevřená doložka se kontroluje jinde")
    missing = [column.value for column, ok in _columns(clause).items() if not ok]
    assert not missing, (
        f"{clause.id} ({clause.promise}) je označená jako držená, ale chybí "
        f"sloupce {missing}; vynucují ji {clause.enforced_by}"
    )


@pytest.mark.parametrize("clause", CONTRACTS, ids=lambda c: c.id)
def test_open_clause_says_what_closes_it(clause: Clause) -> None:
    """`OPEN` bez důvodu je tichá díra s razítkem."""
    if clause.status is not Status.OPEN:
        assert clause.closes_with == "", (
            f"{clause.id} drží, a přesto nese `closes_with` — to je zbytek "
            f"po opravě, který bude mást"
        )
        return
    assert clause.closes_with, f"{clause.id} je otevřená a neříká, co ji zavře"
    assert not clause.enforced_by, (
        f"{clause.id} je otevřená, ale tvrdí, že ji něco vynucuje — jedno "
        f"z toho je lež"
    )


def test_every_boundary_has_at_least_one_clause() -> None:
    """Hranice bez doložky je hranice, o které nikdo nepřemýšlel."""
    for boundary in BOUNDARIES:
        assert contract_module.by_boundary(boundary), f"{boundary} nemá doložku"


def test_clause_ids_are_unique() -> None:
    ids = [clause.id for clause in CONTRACTS]
    assert len(ids) == len(set(ids))


def test_enforcing_tests_are_never_invented() -> None:
    """Jméno testu, který neexistuje, by matici udělalo zeleně vypadající
    a prázdnou."""
    for clause in CONTRACTS:
        for name in clause.enforced_by:
            assert name in TESTS, f"{clause.id} se odvolává na neexistující {name}"


def test_matrix_prints() -> None:
    """Matice se vypisuje bez podmínky — je to dokument stejně jako test."""
    echo("\n" + "=" * 72)
    echo("MATICE SMLUV NA HRANICÍCH VRSTEV — K‑6 zúžené")
    echo("=" * 72)
    header = "  ".join(column.value for column in Column)
    for boundary in BOUNDARIES:
        echo(f"\n{boundary}")
        echo(f"{'':<6}{header}")
        for clause in contract_module.by_boundary(boundary):
            columns = _columns(clause)
            marks = "    ".join("✓" if columns[c] else "·" for c in Column)
            echo(f"  {clause.id:<4}{marks}    {clause.status.value}")
            echo(f"        {clause.promise}")
            if clause.closes_with:
                echo(f"        → zavře: {clause.closes_with}")
    held = sum(1 for c in CONTRACTS if c.status is Status.HELD)
    echo(f"\ndrží {held} / otevřeno {len(CONTRACTS) - held}")
    echo("=" * 72)


def test_tiers_follow_the_base_between_turns() -> None:
    """Doložka S‑2: patra se staví per tah.

    Kdyby se `base_consistency_tier` postavilo v konstruktoru, ptalo by se
    prázdné báze i po deseti tazích — a vypadalo by to jako patro, které
    „nikdy nic nerozhodne", ne jako zamrzlý pohled.
    """
    session = Session(lexicon=czech_seed())
    first = session.tiers()
    second = session.tiers()
    assert [type(t) for t in first] == [type(t) for t in second]
    # Uzávěry nad bází nejsou tytéž objekty — kdyby byly, nesly by starý
    # pohled. Identita je tu jediné, co ten rozdíl umí ukázat.
    assert any(a is not b for a, b in zip(first, second))
    assert len(first) == 14
