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


def _determiner_reading(
    noun: str, lemma: str, *, det: str = "jejich", det_lemma: str = "jeho"
) -> Reading:
    """„Lékaři sledovali jejich <X>." — role s DETERMINÁTOREM, jehož
    signatura NESE LEMMA a číslo ani pád nemá."""
    return Reading(
        tokens=(
            tok(1, "Lékaři", "lékař", "NOUN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Plur"),
            tok(2, "sledovali", "sledovat", "VERB", 0, "root", Gender="Masc", Number="Plur", Polarity="Pos"),
            tok(3, det, det_lemma, "DET", 4, "det", PronType="Prs"),
            tok(4, noun, lemma, "NOUN", 2, "obj", Case="Acc", Gender="Masc", Number="Sing"),
            tok(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


def _teach_the_determiner() -> tuple[Session, StructuralSignature]:
    from core_semantics.oracle import RecordedOracle
    from core_semantics.tests import golden

    text = "Lékaři sledovali jejich stav."
    reading = _determiner_reading("stav", "stav")
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    first = session.utter(text, oracle)
    assert first.predication is not None
    role = next(
        r for r in first.predication.roles if r.pending is not None and r.quantifier is None
    )
    assert role.pending is not None
    session.play(
        answers_quantifier("Některého.", first.predication, role.pending, Operation.EXISTS)
    )
    return session, role.pending


def test_what_was_learned_is_found_again_in_the_same_session() -> None:
    """„✓ NAUČENO … PLATÍ PRO KAŽDÝ TVAR" A NEPLATILO ANI PRO TUTÉŽ VĚTU
    *(B‑27)*. Spouštěč se stavěl bez `lemma`, tedy jako STRUKTURNÍ, jenže
    `Trigger.matches` strukturní vzor se signaturou, která lemma NESE,
    z principu nepáruje. Naučené se pak nenašlo — ne špatně použilo,
    NENAŠLO SE VŮBEC."""
    from core_semantics.oracle import RecordedOracle
    from core_semantics.tests import golden

    session, signature = _teach_the_determiner()
    assert session.lexicon.quantifier_candidates(signature), "naučené musí jít najít"
    text = "Lékaři sledovali jejich stav."
    oracle = RecordedOracle(
        {text: Utterance(text=text, readings=(_determiner_reading("stav", "stav"),))}
    )
    again = session.utter(text, oracle)
    assert again.predication is not None
    assert not any(
        r.pending is not None and r.quantifier is None for r in again.predication.roles
    ), "táž věta se nesmí zeptat podruhé"


def test_the_promise_of_a_class_holds_on_a_second_sentence() -> None:
    """Tah slibuje „platí pro každý tvar X" — a musí to dokázat na JINÉ
    větě téhož tvaru, ne jen na té, ze které se učil *(B‑27)*."""
    from core_semantics.oracle import RecordedOracle
    from core_semantics.tests import golden

    session, _ = _teach_the_determiner()
    text = "Lékaři sledovali jejich případ."
    oracle = RecordedOracle(
        {text: Utterance(text=text, readings=(_determiner_reading("případ", "případ"),))}
    )
    other = session.utter(text, oracle)
    assert other.predication is not None
    assert not any(
        r.pending is not None and r.quantifier is None for r in other.predication.roles
    )


def test_the_report_says_what_it_actually_learned() -> None:
    """Slib musí sedět s klíčem *(B‑27)*: u signatury s lemmatem se
    naučilo „`DET/det` se slovem „jeho“", ne „každý `DET/det`" —
    „některé", „jejich" a „každý" nejsou totéž a naučit je najednou by
    byl tichý default s razítkem naučeného."""
    from core_semantics.oracle import RecordedOracle
    from core_semantics.tests import golden

    text = "Lékaři sledovali jejich stav."
    reading = _determiner_reading("stav", "stav")
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    first = session.utter(text, oracle)
    assert first.predication is not None
    role = next(
        r for r in first.predication.roles if r.pending is not None and r.quantifier is None
    )
    assert role.pending is not None
    result = session.play(
        answers_quantifier("Některého.", first.predication, role.pending, Operation.EXISTS)
    )
    assert "se slovem „jeho“" in result.lines[1]


def test_learning_one_determiner_does_not_answer_for_another() -> None:
    """ZÚŽENÍ JE CELÝ SMYSL TOHO ROZHODNUTÍ *(B‑27)*. Naučit `DET/det →
    ∃` pro VŠECHNY determinátory by byl tichý default s razítkem
    naučeného: „jejich" je `∃`, ale „veškerý" `∃` být nemusí.

    **Determinátor musí být takový, o kterém lexikon ještě neví.**
    „Každý" se na tuhle zkoušku NEHODÍ a stálo to reviewera jeden pokus:
    je v osivu (`determinátor „každý“ → ∀`), takže se neptá z úplně
    jiného důvodu a zúžení by se nedokázalo ani nevyvrátilo."""
    from core_semantics.oracle import RecordedOracle

    session, signature = _teach_the_determiner()
    assert signature.lemma == "jeho"
    text = "Lékaři sledovali veškerý případ."
    reading = _determiner_reading("případ", "případ", det="veškerý", det_lemma="veškerý")
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    other = session.utter(text, oracle)
    assert other.predication is not None
    ceka = [
        r for r in other.predication.roles if r.pending is not None and r.quantifier is None
    ]
    assert ceka, "jiný determinátor se musí zeptat znovu"
    assert ceka[0].pending is not None and ceka[0].pending.lemma == "veškerý"
    assert not session.lexicon.quantifier_candidates(ceka[0].pending)
