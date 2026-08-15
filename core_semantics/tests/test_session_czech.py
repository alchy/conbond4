"""Napojení `Session` na orákulum a kaskádu — česká věta na vstupu.

Testuje se hlavně to, co se **nesmí slít** (past F‑3): neběžící orákulum,
nerozebraná věta a nerozhodnutá kaskáda jsou tři různé výsledky. A že
do žurnálu jde **struktura, ne text** — na tom stojí přehratelnost § 10.
"""

from __future__ import annotations

from core_semantics.cascade import ROLE_SUBJECT
from core_semantics.lexicon import Mood
from core_semantics.oracle import (
    OracleUnavailable,
    Reading,
    RecordedOracle,
    Token,
    Utterance,
)
from core_semantics.session import Session, TurnKind

STAMP = "test-model"


def _token(
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


LEMON_TEXT = "Obsahuje citron vitamíny?"
LEMON = Utterance(
    text=LEMON_TEXT,
    readings=(
        Reading(
            tokens=(
                _token(1, "Obsahuje", "obsahovat", "VERB", 0, "root", Number="Sing"),
                _token(2, "citron", "citron", "NOUN", 1, "obj", Number="Sing", Case="Nom"),
                _token(3, "vitamíny", "vitamín", "NOUN", 1, "obj", Number="Plur", Case="Acc"),
            ),
            provenance=STAMP,
        ),
    ),
)

AMBIGUOUS_TEXT = "Vidí Petr Pavel?"
AMBIGUOUS = Utterance(
    text=AMBIGUOUS_TEXT,
    readings=(
        Reading(
            tokens=(
                _token(1, "Vidí", "vidět", "VERB", 0, "root", Number="Sing"),
                _token(2, "Petr", "Petr", "PROPN", 1, "obj", Number="Sing", Case="Nom"),
                _token(3, "Pavel", "Pavel", "PROPN", 1, "obj", Number="Sing", Case="Nom"),
            ),
            provenance=STAMP,
        ),
    ),
)

SILENT_TEXT = "Ňuňu ňuňu."
SILENT = Utterance(text=SILENT_TEXT, readings=())


def _oracle() -> RecordedOracle:
    return RecordedOracle(
        {LEMON_TEXT: LEMON, AMBIGUOUS_TEXT: AMBIGUOUS, SILENT_TEXT: SILENT}
    )


class _DeadOracle:
    provenance = ""

    def parse(self, text: str) -> Utterance:
        raise OracleUnavailable("služba cb-udpipe neodpovídá na 127.0.0.1:42200")


# --------------------------------------------------------------------------
# Tři výsledky, které se nesmí slít (F‑3)
# --------------------------------------------------------------------------


def test_dead_oracle_is_an_operational_error_not_a_misunderstanding() -> None:
    session = Session()
    result = session.utter(LEMON_TEXT, _DeadOracle())
    assert result.error is not None
    assert "provozní chyba" in "\n".join(result.lines)
    # Do žurnálu nejde nic: přehrávat „parser byl mimo" by znamenalo
    # přehrávat stav prostředí, ne dialog.
    assert session.journal == []


def test_unreadable_sentence_is_an_honest_refusal() -> None:
    session = Session()
    result = session.utter(SILENT_TEXT, _oracle())
    assert result.error is None
    assert "neumím přečíst" in "\n".join(result.lines)
    assert session.journal == []


def test_undecided_cascade_asks_instead_of_choosing() -> None:
    """Obě jména jsou Sing i Nom, takže morfologie nerozhodne."""
    session = Session()
    result = session.utter(AMBIGUOUS_TEXT, _oracle())
    assert result.predication is None
    rendered = "\n".join(result.lines)
    assert "NEVÍM, jak to čtu" in rendered
    assert "které z toho" in rendered
    assert session.journal == []


# --------------------------------------------------------------------------
# Rozhodnuté čtení
# --------------------------------------------------------------------------


def test_decided_reading_becomes_a_structured_turn() -> None:
    """Motivační případ § 5.2 projde od české věty až k vybranému čtení."""
    session = Session()
    result = session.utter(LEMON_TEXT, _oracle())
    assert result.predication is not None
    subject = result.predication.role(ROLE_SUBJECT)
    assert subject is not None and subject.lemma == "citron"
    assert any("shoda čísla" in step for step in result.trace)


def test_journal_holds_structure_not_text() -> None:
    """§ 10: kdyby v žurnálu ležely věty, `replay` by závisel na verzi
    parseru a přehratelnost by padla — a na té stojí měření učitelnosti."""
    session = Session()
    session.utter(LEMON_TEXT, _oracle())
    assert len(session.journal) == 1
    turn = session.journal[0]
    assert turn.kind is TurnKind.READING
    assert turn.predication is not None  # struktura
    # Replay běží BEZ orákula — parser se ho ani nedotkne.
    replayed = Session.replay(session.journal)
    assert replayed.answers() == session.answers()
    assert replayed.program() == session.program()


def test_mood_comes_from_punctuation_but_can_be_overridden() -> None:
    """Otazník není rozbor věty, je to interpunkce. Strukturovaný vstup
    tah zná přesně, takže ho smí přebít (past F‑2)."""
    session = Session()
    result = session.utter(LEMON_TEXT, _oracle(), mood=Mood.ASSERTION)
    assert result.predication is not None
    assert result.predication.mood is Mood.ASSERTION

    other = Session()
    assert other.utter(LEMON_TEXT, _oracle()).predication is not None
    assert other.results[0].predication.mood is Mood.QUESTION  # type: ignore[union-attr]


def test_unfinished_reading_writes_nothing_to_the_base() -> None:
    """Od L‑5 se věta do báze DOSTANE — ale jen celá.

    Zapsat půlku čtení by znamenalo zapsat něco jiného, než člověk řekl.
    Tahle věta má role bez kvantifikátoru (parser nedal pád), takže se
    nezakotví, a do programu proto nesmí přibýt nic.
    """
    session = Session()
    session.utter(LEMON_TEXT, _oracle())
    assert session.program() == ()
    joined = "\n".join(session.results[0].lines)
    assert "NEZAKOTVENO" in joined
    assert session.results[0].statement_id is None


def _coordinate_subject() -> Reading:
    """„Petr a Jana přišli." — souřadný druhý podmět visí jako
    `nsubj>conj+Nom`, tedy týž tvar jako „zápal plic" v korpusu.
    ZÁZNAM, ne živý rozbor: sada je hermetická."""
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "a", "a", "CCONJ", 3, "cc"),
            _token(3, "Jana", "Jana", "PROPN", 1, "conj", Case="Nom", Gender="Fem", Number="Sing"),
            _token(4, "přišli", "přijít", "VERB", 0, "root", Gender="Masc", Number="Plur", Polarity="Pos"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )


def _coordinate_session() -> tuple[Session, Reading]:
    """Sezení, ve kterém věta o dvou podmětech čeká na `→@`."""
    from core_semantics.tests import golden

    text = "Petr a Jana přišli."
    reading = _coordinate_subject()
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    session.utter(text, oracle)
    return session, reading


def test_an_answer_that_changes_nothing_says_so() -> None:
    """ŽÁDNÝ TAH NEPOTVRDÍ UČENÍ, ANIŽ ŘEKNE, CO SE VE VĚTĚ ZMĚNILO
    *(N‑1)*. Tah ohlásil „✓ naučeno" a čtení zůstalo beze změny — člověk
    si myslel, že postoupil. Je to horší než otázka bez tahu: u té ví,
    že stojí."""
    from core_semantics.session import names_role

    session, reading = _coordinate_session()
    result = session.play(
        names_role("Je to taky podmět.", reading, "nsubj>conj+Nom", ROLE_SUBJECT)
    )
    hlaseni = chr(10).join(result.lines)
    assert "ČTENÍ SE NEZMĚNILO" in hlaseni
    assert "„Petr“" in hlaseni, "musí říct, KDO tu roli drží"
    assert "„Jana“" in hlaseni, "musí říct, KTERÝ člen zůstal mimo"
    assert "Mapování platí dál" in hlaseni, "naučené se nezahazuje"


def test_an_answer_that_works_stays_silent_about_it() -> None:
    """PROTIPŘÍKLAD: když role volná JE, člen do čtení vstoupí a žádná
    věta o nezměněném čtení se nepíše. Tah se NEODMÍTÁ ani tady, ani
    tam — mapování je naučené správně pro celou třídu tvarů."""
    from core_semantics.session import names_role

    session, reading = _coordinate_session()
    result = session.play(
        names_role("Je to okolnost.", reading, "nsubj>conj+Nom", "jak")
    )
    hlaseni = chr(10).join(result.lines)
    assert "ČTENÍ SE NEZMĚNILO" not in hlaseni
    assert "jak:Jana" in hlaseni
