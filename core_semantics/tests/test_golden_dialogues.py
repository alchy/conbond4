"""Zlaté dialogy pěti domén — L‑7, poslední položka dodatku L.

Rozdíl proti `test_golden_transcripts.py` je celý v tom, co se fixuje:
tam **rozbor jedné věty**, tady **celý tah** — čtení, vazby zmínek na
uzly, zápis do báze i doložená odpověď, a to napříč dialogem, kde na
sobě tahy stojí.
"""

from __future__ import annotations

import pytest

from core_semantics.oracle import RecordedOracle
from typing import Sequence

from core_semantics.cascade import relation_shape
from core_semantics.session import (
    Session,
    TurnResult,
    answers_here,
    answers_quantifier,
    names_relation,
    names_relation_here,
)
from core_semantics.ast import Group
from core_semantics.session import (
    declares_complete,
    decides_reference,
    names_attribute,
    names_role,
    revokes,
)
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
    turns: list[tuple[Step, TurnResult]] = []
    for step in dialogue.steps:
        turns.append((step, _run(session, oracle, step, turns)))
    return turns, session


def _run(
    session: Session,
    oracle: RecordedOracle,
    step: Step,
    done: Sequence[tuple[Step, TurnResult]],
) -> TurnResult:
    """Krok je buď VĚTA, nebo TAH."""
    if not _is_turn(step):
        return session.utter(step.text, oracle)
    return _answer(session, step, done)


def _is_turn(step: Step) -> bool:
    """Krok je TAH, ne věta."""
    return (
        step.answers_quantifier is not None
        or step.answers_here is not None
        or step.answers_relation is not None
        or step.answers_relation_here is not None
        or step.decides_reference is not None
        or step.names_role is not None
        or step.names_attribute is not None
        or step.declares_complete != ""
        or step.revokes_complete != ""
    )


def _answer(
    session: Session, step: Step, done: Sequence[tuple[Step, TurnResult]]
) -> TurnResult:
    """Tah `→∀` složený z toho, na co se systém DOOPRAVDY ptal.

    Tvar se dopočítá z čekající role předchozího kroku, neopisuje se:
    opsaný tvar by se mohl rozejít s tím, na co se systém ptal, a sada by
    hlídala shodu dvou zápisů místo chování."""
    assert done, "tah bez předchozí věty nemá na co odpovídat"
    previous, result = done[-1]
    if step.names_role is not None:
        # POJMENOVÁNÍ ZTRACENÉ ROLE. Čte se z předchozího kroku, protože
        # rozbor té věty nese tvar, na který se systém ptal.
        shape, role_name = step.names_role
        assert previous.reading is not None
        return session.play(
            names_role(step.text, previous.reading, shape, role_name)
        )
    if step.names_attribute is not None:
        # PŘÍVLASTEK. Skládá se z hlavy a genitivu, ne z toho, na co se
        # systém ptal — otázka nabízí jména rolí, ale kterou dvojici
        # pojmenováváme, je dané větou.
        head, filler, role_name = step.names_attribute
        return session.play(names_attribute(step.text, head, filler, role_name))
    if step.decides_reference is not None:
        # ODKAZ. Rozhoduje se na PREDIKACI předchozího kroku — ta nese
        # roli, která na antecedent čeká.
        role_name, node_id = step.decides_reference
        assert result.predication is not None
        return session.play(
            decides_reference(step.text, result.predication, role_name, node_id)
        )
    if step.declares_complete:
        # UZAVŘENÍ SVĚTA. Není to odpověď na otázku po tvaru — je to
        # prohlášení mluvčího, takže se skládá ze skupiny, ne z toho, na
        # co se systém ptal.
        return session.play(declares_complete(step.text, Group(step.declares_complete)))
    if step.revokes_complete:
        # ODVOLÁNÍ. Hledá se KROK, který uzavření zapsal — ne poslední
        # výrok v bázi: odvolat „ten poslední" by fungovalo jen náhodou
        # a při přidání kroku by sada tiše odvolávala něco jiného.
        target = next(
            result.statement_id
            for previous, result in done
            if previous.declares_complete and result.statement_id
        )
        assert target is not None
        return session.play(revokes(step.text, target, step.revokes_complete))
    if step.answers_relation_here is not None:
        # ODPOVĚĎ NA VĚTU (`→⊆1`), ne na tvar — týž tvar znamená v jedné
        # větě `contains` a v druhé `within`.
        assert previous.reading is not None and result.predication is not None
        return session.play(
            names_relation_here(
                step.text,
                result.predication,
                previous.reading,
                step.answers_relation_here,
            )
        )
    if step.answers_relation is not None:
        # ODPOVĚĎ NA STAVBU (`→⊆`). Tvar konstrukce se DOPOČÍTÁ z toho, co
        # předchozí krok přečetl — opsaný tvar by se mohl rozejít s tím,
        # na co se systém doopravdy ptal.
        assert previous.reading is not None and result.predication is not None
        found = relation_shape(result.predication, previous.reading)
        assert found is not None, f"{step.text!r}: předchozí věta konstrukci nemá"
        return session.play(
            names_relation(
                step.text, previous.reading, found.shape, step.answers_relation
            )
        )
    answer = step.answers_quantifier or step.answers_here
    assert answer is not None
    name, operation = answer
    pending = result.predication
    assert pending is not None, f"{step.text!r}: předchozí krok nic nepřečetl"
    role = pending.reading(name)
    assert role is not None and role.pending is not None, (
        f"{step.text!r}: role {name!r} na kvantifikátor nečeká, "
        f"takže není na co odpovídat"
    )
    if step.answers_here is not None:
        # ODPOVĚĎ NA VĚTU, ne na tvar (N‑8). Sada tím měří i to, že se
        # tvar NENAUČIL: kdyby ano, další věta téhož tvaru by se nezeptala
        # a krok, který na ni odpovídá, by spadl na „role nečeká".
        return session.play(answers_here(step.text, pending, name, operation))
    return session.play(
        answers_quantifier(step.text, pending, role.pending, operation)
    )


@pytest.mark.parametrize("dialogue", DIALOGUES, ids=lambda d: d.name)
def test_dialogue_reads_writes_and_answers_as_recorded(dialogue: Dialogue) -> None:
    # Sezení se staví TADY, ne v pomocné funkci: doložka S‑13 žádá průchod
    # veřejným vstupním bodem a test, který se k němu dostane přes helper,
    # by ten průchod jen předstíral.
    session = Session(lexicon=dialogue.lexicon())
    oracle = RecordedOracle(dialogue.recordings())
    done: list[tuple[Step, TurnResult]] = []
    for step in dialogue.steps:
        # `session.utter(...)` je tu ROZEPSANÉ, ne schované v pomocné
        # funkci: doložka S‑13 žádá průchod veřejným vstupním bodem a test,
        # který se k němu dostane přes helper, by ten průchod jen
        # předstíral. Tah je jediná výjimka — vstupní bod pro větu nemá,
        # protože to není věta.
        result = (
            session.utter(step.text, oracle)
            if not _is_turn(step)
            else _answer(session, step, done)
        )
        done.append((step, result))
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
    done: list[tuple[Step, TurnResult]] = []
    for step in dialogue.steps:
        before = session.program()
        result = _run(session, oracle, step, done)
        done.append((step, result))
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
            # ZÁVĚRY DOMÉN, ne „tahy, které mají nějaký status". Ten dřívější
            # čítač počítal i NEPŘEČTENOU větu, protože ta se vrací se
            # statusem `UNKNOWN` — takže když se „Děti mají rády zmrzlinu."
            # konečně přečetla a ZAPSALA, číslo KLESLO. Metrika, která
            # ohlásí pokrok jako propad, je horší než žádná: příště by se
            # stejně nerozeznalo, že doména o odpověď opravdu přišla.
            answered += 1 if step.answers else 0
    echo("\n" + "=" * 72)
    echo(
        f"domén {len(DIALOGUES)} · zapsaných tahů {written} · "
        f"závěrů domén {answered}"
    )
    echo("=" * 72)
    assert written and answered


def test_the_turn_branch_really_runs_in_the_acceptance_set() -> None:
    """W‑16: mašinerie ve stejném harnessu, který hlídá gate, a sama
    nehlídaná, je horší než žádná — vypadá jako pokrytí a není.

    Počítá se PRŮCHOD, ne existence pole: krok, který je tah, musí projít
    `_answer`, jinak by sada tvrdila, že smyčku učení měří, a přitom by
    ji obcházela."""
    ran = 0
    for dialogue in DIALOGUES:
        session = Session(lexicon=dialogue.lexicon())
        oracle = RecordedOracle(dialogue.recordings())
        done: list[tuple[Step, TurnResult]] = []
        for step in dialogue.steps:
            if _is_turn(step):
                ran += 1
                done.append((step, _answer(session, step, done)))
            else:
                done.append((step, session.utter(step.text, oracle)))
    assert ran >= 1, "větev tahu se v akceptačním běhu neprovedla ani jednou"


def test_a_sentence_level_answer_does_not_leak_into_the_next_sentence() -> None:
    """N‑8 měřené NA DOMÉNĚ, ne na jednotce: „Vegetarián nejí maso" se
    rozhodne jako `∀`, a „Petr jedl steak" se PŘESTO zeptá znovu. Kdyby
    se tvar naučil, druhá věta by se přečetla jako `∀steak` a závěr
    domény by stál na chybném čtení."""
    dialogue = next(d for d in DIALOGUES if d.name == "Vegetarián a steak")
    played, session = play(dialogue)
    written = " ".join(session.program())
    assert "jíst(co:∃steak" in written
    assert "jíst(co:∀steak" not in written
    asked = [step.text for step, result in played if result.question is not None]
    assert "Petr jedl steak." in asked
