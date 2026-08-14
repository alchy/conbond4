"""Identitní operace — M‑2, A‑15.

Kanonizace jmen ztotožňuje „Petr" ve dvou větách. Je to **odvolatelný**
default, a právě proto smí být default — ale odvolat ho musí být čím.
Tenhle modul je ta druhá půlka: `!≠` („ti dva nejsou tíž") a `!÷`
(„tohle byli dva různí lidé").
"""

from __future__ import annotations

from core_semantics.ast import (
    Entity,
    Group,
    QueryStatus,
    atom,
    member_of,
    role,
    same_as_of,
)
from core_semantics.engine import Engine
from core_semantics.session import Session, TurnKind, declares_distinct, says, splits
from core_semantics.tests._console import echo

PETR = Entity("Petr")
OTHER = Entity("Petr_z_Brna")


def with_two_petrs() -> Session:
    """Sezení, kde kanonizace slila dva různé lidi do jednoho uzlu."""
    session = Session()
    session.play(says("Petr bydlí v Praze.", atom("bydli", role("kdo", PETR))))
    session.play(says("Petr je učitel.", member_of(PETR, Group("učitel"))))
    return session


# --------------------------------------------------------------------------
# `!≠` — ti dva nejsou tíž
# --------------------------------------------------------------------------


def test_distinct_is_written_as_a_denial_of_identity() -> None:
    session = Session()
    result = session.play(declares_distinct("Ten Petr není ten Petr.", PETR, OTHER))
    assert result.statement_id is not None
    assert result.turn.kind is TurnKind.DISTINCT
    assert Engine(session.kb).ask(same_as_of(PETR, OTHER)).status is (
        QueryStatus.PROVEN_FALSE
    )


def test_distinct_keeps_facts_apart() -> None:
    """K čemu to je: bez popření by kanonizace jmen mohla fakty přelít
    z jednoho člověka na druhého a nikdo by neměl čím to zastavit."""
    session = Session()
    session.play(says("Petr bydlí v Praze.", atom("bydli", role("kdo", PETR))))
    session.play(declares_distinct("Nejsou tíž.", PETR, OTHER))
    asked = atom("bydli", role("kdo", OTHER))
    assert Engine(session.kb).ask(asked).status is QueryStatus.UNKNOWN


def test_distinct_after_identity_reports_the_dispute_out_loud() -> None:
    """M‑1 zblízka: když už `same_as` v bázi je, popření vyrobí SPOR —
    a tah to musí říct, protože od té chvíle přes tu identitu nic nevede."""
    session = Session()
    session.play(says("Jsou tíž.", same_as_of(PETR, OTHER)))
    result = session.play(declares_distinct("Nejsou tíž.", PETR, OTHER))
    assert result.statement_id is not None
    assert any("SPOR" in line for line in result.lines)
    assert Engine(session.kb).ask(same_as_of(PETR, OTHER)).status is (
        QueryStatus.CONFLICT
    )


# --------------------------------------------------------------------------
# `!÷` — rozdělení uzlu
# --------------------------------------------------------------------------


def test_split_moves_the_statements_and_keeps_the_originals_in_history() -> None:
    """Deaktivace, ne mazání (§ 8). Historie je to jediné, co dovoluje
    rozhodnutí vzít zpátky."""
    session = with_two_petrs()
    before = len(list(session.kb.active()))
    result = session.play(
        splits("Byli to dva.", PETR, ("Petr_1", "Petr_2"), "dva různí lidé")
    )
    assert result.derived, result.lines
    program = session.program()
    assert any("Petr_1" in line for line in program)
    assert not any(
        line.startswith("bydli(kdo:Petr)") for line in program
    ), "původní výrok nesmí zůstat aktivní"
    # Nic se nesmazalo — jen se to deaktivovalo.
    assert len(list(session.kb.active())) >= before


def test_split_provenance_points_at_the_split_turn_not_at_the_person() -> None:
    """Přesměrovaný výrok NEŘEKL člověk. Kdyby nesl původní „řekls",
    transkript by mu do úst vložil něco, co za něj odvodil systém."""
    session = with_two_petrs()
    result = session.play(
        splits("Byli to dva.", PETR, ("Petr_1", "Petr_2"), "dva různí lidé")
    )
    for sid in result.derived:
        statement, _, _ = session.kb.inspect(sid)
        assert "rozdělení" in statement.provenance


def test_split_does_not_guess_which_statements_belong_to_the_second_node() -> None:
    """Systém neví, co o kom platilo, a nehádá to. Druhý uzel začíná
    prázdný a řekne se to nahlas."""
    session = with_two_petrs()
    result = session.play(
        splits("Byli to dva.", PETR, ("Petr_1", "Petr_2"), "dva různí lidé")
    )
    # O druhém uzlu neplatí NIC — až na jeho jméno, které mu dal SPLIT,
    # aby se kanonizace příště nedomýšlela (N‑2).
    about_second = [
        line for line in session.program() if "Petr_2" in line and "name" not in line
    ]
    assert about_second == []
    assert any("Petr_2 zatím nic neříká" in line for line in result.lines)


def test_split_of_an_unknown_node_refuses_instead_of_pretending() -> None:
    session = Session()
    result = session.play(
        splits("Byli to dva.", PETR, ("Petr_1", "Petr_2"), "dva různí lidé")
    )
    assert result.error is not None
    assert session.program() == ()


def test_split_is_replayable() -> None:
    """Rozdělení je tah, takže `replay` musí dát tutéž bázi (§ 10)."""
    session = with_two_petrs()
    session.play(splits("Byli to dva.", PETR, ("Petr_1", "Petr_2"), "dva různí"))
    assert Session.replay(session.journal).program() == session.program()


def test_identity_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("IDENTITNÍ OPERACE — M‑2")
    echo("=" * 72)
    session = with_two_petrs()
    for turn in (
        splits("Byli to dva různí Petrové.", PETR, ("Petr_1", "Petr_2"), "dva lidé"),
        declares_distinct("A nejsou to tíž.", Entity("Petr_1"), Entity("Petr_2")),
    ):
        result = session.play(turn)
        echo(f"\n» {turn.kind.value} {turn.text}")
        for line in result.lines:
            echo(f"   {line}")
    echo("\n" + "=" * 72)
