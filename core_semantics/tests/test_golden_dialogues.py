"""Zlaté dialogy pěti domén — L‑7, poslední položka dodatku L.

Rozdíl proti `test_golden_transcripts.py` je celý v tom, co se fixuje:
tam **rozbor jedné věty**, tady **celý tah** — čtení, vazby zmínek na
uzly, zápis do báze i doložená odpověď, a to napříč dialogem, kde na
sobě tahy stojí.
"""

from __future__ import annotations

import pytest

from core_semantics.oracle import RecordedOracle
from core_semantics.session import Session, TurnResult
from core_semantics.tests._console import echo
from core_semantics.tests.dialogues import DIALOGUES, Dialogue, Step


Played = tuple[list[tuple[Step, TurnResult]], Session]


def play(dialogue: Dialogue) -> Played:
    """Přehraje celý dialog v JEDNOM sezení.

    Jedno sezení je podstata téhle sady: kanonizace jmen, doložení
    určitého popisu i odpověď z dřív zapsaného faktu dávají smysl jen
    tehdy, když na sobě tahy stojí. Sada vět po jedné by tuhle vrstvu
    minula celou."""
    session = Session(lexicon=dialogue.lexicon())
    oracle = RecordedOracle(dialogue.recordings())
    turns = [(step, session.utter(step.text, oracle)) for step in dialogue.steps]
    return turns, session


@pytest.mark.parametrize("dialogue", DIALOGUES, ids=lambda d: d.name)
def test_dialogue_reads_writes_and_answers_as_recorded(dialogue: Dialogue) -> None:
    # Sezení se staví TADY, ne v pomocné funkci: doložka S‑13 žádá průchod
    # veřejným vstupním bodem a test, který se k němu dostane přes helper,
    # by ten průchod jen předstíral.
    session = Session(lexicon=dialogue.lexicon())
    oracle = RecordedOracle(dialogue.recordings())
    for step in dialogue.steps:
        result = session.utter(step.text, oracle)
        where = f"{dialogue.name} / {step.text!r}"

        if step.reads:
            assert result.predication is not None, f"{where}: nepřečteno {result.lines}"
            assert str(result.predication) == step.reads, where

        for anchor in step.anchors:
            assert any(anchor in line for line in result.lines), (
                f"{where}: chybí vazba {anchor!r} — predikace řekne, o KOM "
                f"se mluví, teprve vazba řekne, na který uzel to přistálo\n"
                f"{result.lines}"
            )

        if step.writes:
            assert result.statement_id is not None, f"{where}: nezapsáno"
            statement, _, _ = session.kb.inspect(result.statement_id)
            assert str(statement.formula) == step.writes, where
        elif step.answers or step.asks or step.refuses:
            assert result.statement_id is None, (
                f"{where}: tah neměl zapisovat, a zapsal {result.statement_id}"
            )

        if step.answers:
            assert result.status is not None, f"{where}: bez verdiktu"
            assert result.status.value == step.answers, where

        if step.asks:
            assert result.question is not None, f"{where}: mělo se ptát"


@pytest.mark.parametrize("dialogue", DIALOGUES, ids=lambda d: d.name)
def test_dialogue_is_replayable(dialogue: Dialogue) -> None:
    """Celý dialog přehraný ze žurnálu dá tutéž bázi i tytéž odpovědi.

    Bez orákula — parser se přehrávání ani nedotkne, protože žurnál nese
    rozhodnuté tahy, ne věty (§ 10). Vazby zmínek na uzly tím přežívají
    taky: kdyby se dosazovaly znovu, dialog by po přehrání mohl mluvit
    o jiných uzlech než při prvním běhu."""
    _, session = play(dialogue)
    replayed = Session.replay(session.journal)
    assert replayed.program() == session.program()
    assert replayed.answers() == session.answers()


@pytest.mark.parametrize("dialogue", DIALOGUES, ids=lambda d: d.name)
def test_questions_never_change_the_base(dialogue: Dialogue) -> None:
    """I‑12 přes celý dialog: po otázce musí být program beze změny."""
    session = Session(lexicon=dialogue.lexicon())
    oracle = RecordedOracle(dialogue.recordings())
    for step in dialogue.steps:
        before = session.program()
        result = session.utter(step.text, oracle)
        if step.answers:
            assert session.program() == before, (
                f"{dialogue.name} / {step.text!r}: otázka změnila bázi"
            )
            assert result.statement_id is None


def test_shapes_stay_out_of_the_shipped_seed() -> None:
    """Tvary potvrzené pro dialog jsou ROZHODNUTÍ té domény.

    V `czech_seed()` by z nich byl tichý default pro každého, kdo
    knihovnu použije — a tichý default kvantifikátoru je přesně to,
    co L‑3 zakazuje."""
    from core_semantics.lexicon import StructuralSignature, czech_seed

    seed = czech_seed()
    for dialogue in DIALOGUES:
        for upos, number, case, deprel, _ in dialogue.shapes:
            signature = StructuralSignature(
                lemma="", upos=upos, number=number, case=case, deprel=deprel
            )
            assert seed.quantifier_candidates(signature) == (), (
                f"{dialogue.name}: tvar {signature.shape()} je v dodávaném "
                f"seedu, takže by se nikdo nikdy nezeptal"
            )
            assert dialogue.lexicon().quantifier_candidates(signature), (
                f"{dialogue.name}: tvar {signature.shape()} chybí i v lexikonu "
                f"dialogu"
            )


def test_golden_dialogues_print() -> None:
    """Transkripty se vypisují BEZ PODMÍNKY — pět domén jako dokument."""
    echo("\n" + "=" * 72)
    echo("ZLATÉ DIALOGY PĚTI DOMÉN — L‑7")
    echo("=" * 72)
    written = 0
    answered = 0
    for dialogue in DIALOGUES:
        echo(f"\n### {dialogue.name}")
        echo(f"    zdroj: {dialogue.source}")
        if dialogue.note:
            echo(f"    {dialogue.note}")
        played, _ = play(dialogue)
        for step, result in played:
            echo(f"\n» {step.text}")
            if step.point:
                echo(f"   ({step.point})")
            for line in result.lines:
                echo(f"   {line}")
            if step.asks:
                echo(f"   [PRÁVEM SE PTÁ] {step.asks}")
            written += 1 if result.statement_id else 0
            answered += 1 if result.status is not None else 0
    echo("\n" + "=" * 72)
    echo(f"domén {len(DIALOGUES)} · zapsaných tahů {written} · s verdiktem {answered}")
    echo("=" * 72)
    assert written and answered
