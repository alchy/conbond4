"""Kritéria chráněných predikátů — A‑6 a A‑7.

Jsou to DVĚ různé otázky a mají dvě různé množiny.

`KERNEL_PREDICATES` odpovídá na „na co se ptá uzávěrový index" a nese
k tomu směrování v evaluátoru a stratum 0. Mění se **ručně**, a dvakrát
po sobě se ukázalo, že v ní něco chybí — `disjoint` (B‑10) a `complete`
(B‑11), potřetí `name` (N‑2), a to už si vynutilo kritérium samo.
Obojí se projevilo stejně: pravidlo se přijalo, atom odvodil, **a účinek
se zahodil**, protože uzávěrový index se staví jen nad základními fakty.

Proto se členství **neověřuje proti seznamu**. Ověřuje se proti kritériu:

> Predikát, jehož pravdivost mění uzávěr nebo uzavírá svět, se nesmí
> odvozovat pravidlem.

„Mění uzávěr" je strojově zjistitelné — je to přesně ten predikát, na
který se `ClosureIndex` ptá při stavbě indexu. Test proto čte **zdrojový
kód** té stavby a porovná, co se v ní testuje, s obsahem množiny. Kdyby
kdokoli přidal do indexu další predikát a zapomněl na množinu, spadne to
tady, a ne až na tom, že báze odpovídá dvěma způsoby podle vstupního bodu.

`PROTECTED_HEADS` odpovídá na otázku širší — **co se nesmí odvozovat**:

> Predikát, který mění uzávěr, **nebo je to jazyk, kterým se fakty
> zapisují**, nesmí stát v nenegované hlavě naučeného pravidla.

Role jsou ten jazyk (A‑7). Vznikají reifikací z toho, co člověk řekl,
takže pravidlo s `role` v hlavě nepřidává tvrzení — přepisuje, jak se
čte cizí, už zapsaný fakt.
"""

from __future__ import annotations

import ast as pyast
import inspect
import textwrap

import pytest

from core_semantics import ast as core_ast
from core_semantics.ast import (
    KERNEL_PREDICATES,
    PROTECTED_HEADS,
    ROLE_PREDICATES,
    Group,
    Rule,
    UnsafeRule,
    member_of,
)
from core_semantics.closures import ClosureIndex
from core_semantics.tests._console import echo


def _predicates_read_by_the_index() -> set[str]:
    """Predikáty, na které se ptá stavba indexu.

    Bere se `Name` uzel porovnání (`P_MEMBER`), ne řetězec — jméno se
    rozřeší přes modul, takže přejmenování konstanty test nezmate.
    """
    # `getsource` metody vrací odsazený blok, který sám o sobě není platný
    # modul.
    tree = pyast.parse(textwrap.dedent(inspect.getsource(ClosureIndex.__init__)))
    names: set[str] = set()
    for node in pyast.walk(tree):
        if isinstance(node, pyast.Compare):
            operands = [node.left, *node.comparators]
            for operand in operands:
                if isinstance(operand, pyast.Name) and operand.id.startswith("P_"):
                    names.add(operand.id)
                if isinstance(operand, (pyast.Tuple, pyast.List)):
                    for item in operand.elts:
                        if isinstance(item, pyast.Name) and item.id.startswith("P_"):
                            names.add(item.id)
    assert names, "ve stavbě indexu se nenašlo žádné porovnání predikátu"
    return {getattr(core_ast, name) for name in names}


def test_every_predicate_the_index_reads_is_a_kernel_predicate() -> None:
    """Kritérium, ne výčet. Tohle by chytilo B‑10 i B‑11."""
    read = _predicates_read_by_the_index()
    missing = sorted(read - KERNEL_PREDICATES)
    assert not missing, (
        f"{missing} mění uzávěr, ale nejsou v KERNEL_PREDICATES; pravidlo "
        f"by je smělo mít v hlavě, atom by se odvodil a účinek na uzávěr by "
        f"se ZAHODIL — báze by pak odpovídala dvěma způsoby podle toho, "
        f"kterými dveřmi se do ní psalo"
    )


def test_the_criterion_covers_the_whole_set() -> None:
    """Druhý směr: v množině nemá být nic, co uzávěr nemění.

    Kdyby tam takový predikát byl, zakazoval by se učit něco, co se učit
    smí — a zákaz bez důvodu se dřív nebo později obejde.
    """
    extra = sorted(KERNEL_PREDICATES - _predicates_read_by_the_index())
    assert not extra, (
        f"{extra} jsou v KERNEL_PREDICATES, ale index se na ně neptá; buď "
        f"kritérium neplatí, nebo do množiny nepatří"
    )


def test_the_head_guard_is_wider_than_the_closure_criterion() -> None:
    """Dvě různé otázky, dvě různé množiny.

    „Na co se ptá uzávěr" (`KERNEL_PREDICATES`) nese i směrování
    v evaluátoru a stratum 0. „Co se nesmí odvozovat" je otázka širší:
    mění‑li to uzávěr, NEBO je to jazyk, kterým se fakty zapisují.
    Role jsou ten jazyk — vznikají reifikací z toho, co člověk řekl.
    """
    assert PROTECTED_HEADS == KERNEL_PREDICATES | ROLE_PREDICATES
    assert ROLE_PREDICATES - KERNEL_PREDICATES, (
        "role NEMAJÍ být v jádrové množině — uzávěr se na ně neptá a "
        "směrovat je do `_match_kernel` by rozbilo reifikovaná fakta"
    )


def test_a_rule_may_read_a_role_but_not_produce_one() -> None:
    """Jen na hlavu. Na reifikaci v TĚLECH stojí domény dálnice
    i zmrzliny — pravidlo smí roli číst, nesmí ji vyrábět.

    Rozdíl je v tom, co se tím děje: pravidlo s `role` v hlavě naroubuje
    roli na cizí, člověkem zapsanou instanci. Uložený fakt se nezmění,
    změní se, JAK SE ČTE — a to není naučené tvrzení, to je tichý přepis
    staršího.
    """
    relation = core_ast.Variable("R", expects=core_ast.Sort.ENTITY)
    who = core_ast.Variable("w", expects=core_ast.Sort.ENTITY)
    reads_a_role = Rule(
        id="r_reads",
        head=core_ast.atom(
            "odvozeno", core_ast.role("kdo", who, core_ast.Quantifier.SELF)
        ),
        body=(core_ast.role_atom(relation, "kdo", core_ast.role("kdo", who)),),
    )
    assert reads_a_role.body  # tělo s rolí projde

    with pytest.raises(UnsafeRule):
        Rule(
            id="r_writes",
            head=core_ast.role_atom(relation, "kdo", core_ast.role("kdo", who)),
            body=(member_of(who, Group("g")),),
        )


@pytest.mark.parametrize("predicate", sorted(PROTECTED_HEADS))
def test_no_learned_rule_may_write_a_protected_predicate(predicate: str) -> None:
    """I‑16 pro každý prvek množiny, ne jen pro ten, na který kdo myslel."""
    head = core_ast.atom(
        predicate, core_ast.role("group", Group("g"), core_ast.Quantifier.SELF)
    )
    with pytest.raises(UnsafeRule):
        Rule(
            id=f"r_{predicate}",
            head=head,
            body=(
                member_of(
                    core_ast.Variable("x", expects=core_ast.Sort.ENTITY), Group("g")
                ),
            ),
        )


def test_criterion_prints() -> None:
    echo("\n" + "=" * 72)
    echo("KRITÉRIUM JÁDROVÝCH PREDIKÁTŮ — A‑6")
    echo("=" * 72)
    echo("mění uzávěr nebo uzavírá svět ⇒ nesmí se odvozovat pravidlem")
    for predicate in sorted(KERNEL_PREDICATES):
        echo(f"  {predicate}")
    echo("=" * 72)
