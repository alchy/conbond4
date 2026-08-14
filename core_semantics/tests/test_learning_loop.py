"""Smyčka doptání — N‑1.

Nález W‑12: `TurnKind` měl jedenáct druhů tahu a **ani jeden nebyl
odpověď na otázku systému**. Systém se uměl zeptat, otázka slepě
skončila, `turns_to_learn` (§ 10) nemělo co měřit a rozhodnutá reference
nebyla tah, takže ji `replay` nezopakoval.

Tenhle modul testuje smyčku celou: zeptat se → dostat odpověď → naučit
se → **přečíst čekající větu znovu**. Ten poslední krok je ten, který
odlišuje učení od sběru dat — bez něj by člověk musel větu zopakovat.
"""

from __future__ import annotations

from core_semantics.ast import Entity, Group, QueryStatus, member_of
from core_semantics.lexicon import (
    Operation,
    PatternStatus,
    StructuralSignature,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import (
    Session,
    TurnKind,
    answers_quantifier,
    decides_reference,
)
from core_semantics.tests._console import echo

STAMP = "test"


def tok(
    index: int,
    form: str,
    lemma: str,
    upos: str,
    head: int,
    deprel: str,
    **feats: str,
) -> Token:
    return Token(
        index=index,
        form=form,
        lemma=lemma,
        upos=upos,
        head=head,
        deprel=deprel,
        feats=tuple(sorted(feats.items())),
    )


class _Recorded:
    provenance = STAMP

    def __init__(self, mapping: dict[str, tuple[Token, ...]]) -> None:
        self._mapping = mapping

    def parse(self, text: str) -> Utterance:
        return Utterance(
            text=text,
            readings=(Reading(tokens=self._mapping[text], provenance=STAMP),),
        )


TEACHER = (
    tok(1, "Učitelka", "učitelka", "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
    tok(2, "učí", "učit", "VERB", 0, "root", Number="Sing"),
)
TEACHER_Q = (
    tok(1, "Učí", "učit", "VERB", 0, "root", Number="Sing"),
    tok(2, "učitelka", "učitelka", "NOUN", 1, "nsubj", Case="Nom", Number="Sing"),
)
SHAPE = StructuralSignature(
    lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"
)


def oracle() -> _Recorded:
    return _Recorded({"Učitelka učí.": TEACHER, "Učí učitelka?": TEACHER_Q})


# --------------------------------------------------------------------------
# Odpověď na otázku po kvantifikátoru
# --------------------------------------------------------------------------


def test_answer_closes_the_question_and_reads_the_sentence_again() -> None:
    """Jádro N‑1. Tah odpovědi NAUČÍ tvar a HNED zapíše čekající větu.

    Kdyby jen učil, člověk by musel větu zopakovat — a to je přesně ta
    práce navíc, kvůli které se lidem s takovými systémy nechce mluvit.
    """
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.question is not None
    assert asked.statement_id is None
    assert asked.predication is not None

    answer = session.play(
        answers_quantifier(
            "O každé.", asked.predication, SHAPE, Operation.FOR_ALL
        )
    )
    assert answer.statement_id is not None, answer.lines
    assert answer.question is None
    assert "∀učitelka" in str(answer.predication)
    assert any("naučeno" in line for line in answer.lines)


def test_the_answer_generalises_beyond_this_one_sentence() -> None:
    """Naučí se TVAR, ne věta. Jinak by se člověk musel doptávat pořád
    dokola na totéž a metrika § 10 by nikdy neklesla."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    again = session.utter("Učitelka učí.", oracle())
    assert again.question is None, "podruhé se už ptát nemá"
    assert again.statement_id is not None


def test_the_learned_shape_is_revocable_data_with_provenance() -> None:
    """I‑16: učení mění PROGRAM, ne jazyk. Co se naučí odpovědí, jde
    odvolat stejně jako cokoli jiného."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    learned = [p for p in session.lexicon.all() if p.trigger.structural]
    assert learned
    assert all(p.status is PatternStatus.CONFIRMED for p in learned)
    assert all("tah" in p.learned_from for p in learned)

    session.lexicon.revoke(learned[0].key())
    assert session.utter("Učitelka učí.", oracle()).question is not None


def test_an_answer_to_a_shape_nobody_asked_about_says_so() -> None:
    """Odpověď, která v téhle větě nic nezavřela, se NAUČÍ — ale řekne
    se to, jinak by tah vypadal, že něco vyřešil."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    other = StructuralSignature(
        lemma="", upos="NOUN", number="Plur", case="Acc", deprel="obj"
    )
    answer = session.play(
        answers_quantifier("O některých.", asked.predication, other, Operation.EXISTS)
    )
    assert any("nic nečekalo" in line for line in answer.lines)
    assert answer.question is not None, "otázka je pořád otevřená"


def test_turns_to_learn_finally_has_something_to_measure() -> None:
    """Hlavní metrika § 10: kolik tahů od prvního „nevím" po doloženou
    odpověď na TUTÉŽ otázku. Bez tahu odpovědi ji nešlo změřit vůbec."""
    session = Session()
    question = "Učí učitelka?"

    first = session.utter(question, oracle())
    assert first.status is QueryStatus.UNKNOWN

    statement = session.utter("Učitelka učí.", oracle())
    assert statement.predication is not None
    session.play(
        answers_quantifier(
            "O každé.", statement.predication, SHAPE, Operation.FOR_ALL
        )
    )

    again = session.utter(question, oracle())
    assert again.status is QueryStatus.PROVEN_TRUE
    assert session.turns_to_learn(question) == 3


def test_the_whole_loop_replays_from_the_journal() -> None:
    """Odpověď je TAH, takže leží v žurnálu — a přehrání se neptá."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    replayed = Session.replay(session.journal)
    assert replayed.program() == session.program()
    assert replayed.answers() == session.answers()


# --------------------------------------------------------------------------
# Rozhodnutí reference
# --------------------------------------------------------------------------

DEFINITE = (
    tok(1, "To", "ten", "DET", 2, "det", Case="Nom"),
    tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
    tok(3, "je", "být", "AUX", 4, "cop", Number="Sing"),
    tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
)


def blue_car() -> Session:
    lexicon = czech_seed()
    from core_semantics.lexicon import LearnedPattern, Trigger

    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="ADJ", number="Sing", case="Nom", deprel="root"
            ),
            operation=Operation.SELF,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    session.kb.attach(member_of(Entity("a1"), Group("auto")))
    session.kb.attach(member_of(Entity("a2"), Group("auto")))
    return session


def test_reference_decision_closes_an_ambiguous_definite() -> None:
    session = blue_car()
    asked = session.utter("To auto je modré.", _Recorded({"To auto je modré.": DEFINITE}))
    assert asked.statement_id is None
    assert asked.question is not None and "Znám jich víc" in asked.question
    assert asked.predication is not None

    decided = session.play(
        decides_reference("To druhé.", asked.predication, "kdo", "a2")
    )
    assert decided.turn.kind is TurnKind.DECIDE_REFERENCE
    assert decided.statement_id is not None
    statement, _, _ = session.kb.inspect(decided.statement_id)
    filler = statement.formula.get_role("kdo")  # type: ignore[union-attr]
    assert filler is not None and filler.target == Entity("a2")


def test_a_decided_reference_is_not_looked_up_again() -> None:
    """Rozhodnutí je tah, ne dotaz do báze. Kdyby se hledalo znovu,
    přehrání by mohlo dopadnout jinak, jakmile v bázi přibude kandidát."""
    session = blue_car()
    asked = session.utter("To auto je modré.", _Recorded({"To auto je modré.": DEFINITE}))
    assert asked.predication is not None
    session.play(decides_reference("To druhé.", asked.predication, "kdo", "a2"))
    session.kb.attach(member_of(Entity("a3"), Group("auto")))

    replayed = Session.replay(session.journal)
    assert any("a2" in line for line in replayed.program())


def test_deciding_a_role_that_waits_for_nothing_is_refused() -> None:
    session = blue_car()
    asked = session.utter("To auto je modré.", _Recorded({"To auto je modré.": DEFINITE}))
    assert asked.predication is not None
    result = session.play(
        decides_reference("Tohle.", asked.predication, "co", "a1")
    )
    assert result.error is not None
    assert result.statement_id is None


def test_learning_loop_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("SMYČKA DOPTÁNÍ — N‑1")
    echo("=" * 72)
    session = Session()
    steps: list[tuple[str, object]] = []
    first = session.utter("Učí učitelka?", oracle())
    steps.append(("Učí učitelka?", first))
    asked = session.utter("Učitelka učí.", oracle())
    steps.append(("Učitelka učí.", asked))
    assert asked.predication is not None
    steps.append(
        (
            "→∀ O každé.",
            session.play(
                answers_quantifier(
                    "O každé.", asked.predication, SHAPE, Operation.FOR_ALL
                )
            ),
        )
    )
    steps.append(("Učí učitelka?", session.utter("Učí učitelka?", oracle())))
    for label, result in steps:
        echo(f"\n» {label}")
        for line in result.lines:  # type: ignore[attr-defined]
            echo(f"   {line}")
    echo(
        f"\ntahů do naučení na „Učí učitelka?“: "
        f"{session.turns_to_learn('Učí učitelka?')}"
    )
    echo("=" * 72)
