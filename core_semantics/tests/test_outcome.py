"""Pět stavů tahu — W‑105.

Dva různé stavy říkaly totéž slovo: „→ NEVÍM [HYPOTÉZA — nikdo to
neřekl]" a „→ NEVÍM, jak to čtu … Tuhle větu přečíst neumím". A protože
to byly ŘETĚZCE v `lines`, nešly SPOČÍTAT — metrika získané znalosti se
proto nedala ani začít měřit.

**Systém dnes umí přečíst větu a pojmenovat, co na ní nezná; neumí
z textu získat znalost.** Tahle pětice je ten rozdíl rozepsaný do stavů,
které jdou sečíst.
"""

from __future__ import annotations

from core_semantics.ast import QueryStatus
from core_semantics.lexicon import (
    LearnedPattern,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Outcome, Session, answers_here

STAMP = "test"


def tok(
    index: int, form: str, lemma: str, upos: str, head: int, deprel: str,
    **feats: str,
) -> Token:
    return Token(
        index=index, form=form, lemma=lemma, upos=upos, head=head,
        deprel=deprel, feats=tuple(sorted(feats.items())),
    )


def _sentence(*, determiner: bool) -> Reading:
    """«(Každý) pes štěká.»"""
    tokens = [
        tok(2, "pes", "pes", "NOUN", 3, "nsubj",
            Case="Nom", Gender="Masc", Number="Sing"),
        tok(3, "štěká", "štěkat", "VERB", 0, "root",
            Number="Sing", Polarity="Pos"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ]
    if determiner:
        tokens.append(
            tok(1, "Každý", "každý", "DET", 2, "det",
                Case="Nom", Gender="Masc", Number="Sing", PronType="Tot")
        )
    return Reading(
        tokens=tuple(sorted(tokens, key=lambda t: t.index)), provenance=STAMP
    )


class _Oracle:
    provenance = STAMP

    def __init__(self, reading: Reading) -> None:
        self._reading = reading

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._reading,))


def _session() -> Session:
    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(lemma="", upos="NOUN", number="Sing", case="Nom",
                            deprel="nsubj"),
            operation=Operation.FOR_ALL,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    return Session(lexicon=lexicon)


def test_a_written_sentence_says_written() -> None:
    """ZAPSÁNO je jediný stav, po kterém systém něco VÍ."""
    session = _session()
    result = session.utter("Každý pes štěká.", _Oracle(_sentence(determiner=True)))
    assert result.outcome is Outcome.WRITTEN
    assert result.statement_id is not None


def test_a_read_but_unwritten_sentence_says_partial() -> None:
    """ČÁSTEČNĚ ROZUMÍM: věta se přečetla celá, ale zápis zastavil
    pojmenovaný zákaz — tady `∀` z osiva (W‑103)."""
    session = _session()
    result = session.utter("Pes štěká.", _Oracle(_sentence(determiner=False)))
    assert result.outcome is Outcome.PARTIAL
    assert result.predication is not None, "čtení JE, chybí licence zápisu"


def test_an_unreadable_sentence_does_not_say_unknown() -> None:
    """NEČTU není NEVÍM *(W‑105)*. „Nevím" znamená, že v bázi na to není
    dost; „nečtu" znamená, že se ta věta nedá přečíst — a dokud obojí
    říkalo totéž slovo, nešlo je od sebe odlišit ani spočítat."""
    prazdna = Reading(
        tokens=(tok(1, ".", ".", "PUNCT", 0, "root"),), provenance=STAMP
    )
    session = _session()
    result = session.utter(".", _Oracle(prazdna))
    assert result.predication is None
    assert result.outcome is Outcome.UNREADABLE
    # A DŘÍV BY VYŠLO NEVÍM: nečitelná věta dostane 
    # z téže cesty jako dotaz bez důkazu, takže se ty dva stavy dají
    # rozlišit jen tím, že NEČTU má přednost.
    assert result.status is QueryStatus.UNKNOWN


def test_a_refused_turn_says_refused() -> None:
    """ODMÍTÁM: tah, který nemá o co se opřít, není „nevím"."""
    session = _session()
    precteno = session.utter(
        "Každý pes štěká.", _Oracle(_sentence(determiner=True))
    )
    assert precteno.predication is not None
    znovu = session.play(
        answers_here("O každém.", precteno.predication, "kdo", Operation.FOR_ALL)
    )
    assert znovu.error is not None
    assert znovu.outcome is Outcome.REFUSED


def test_a_query_without_evidence_says_unknown() -> None:
    """NEVÍM patří DOTAZU: v bázi na to není dost."""
    otazka = Reading(
        tokens=(
            tok(1, "Štěká", "štěkat", "VERB", 0, "root",
                Number="Sing", Polarity="Pos"),
            tok(2, "pes", "pes", "NOUN", 1, "nsubj",
                Case="Nom", Gender="Masc", Number="Sing"),
            tok(3, "?", "?", "PUNCT", 1, "punct"),
        ),
        provenance=STAMP,
    )
    session = _session()
    result = session.utter("Štěká pes?", _Oracle(otazka))
    assert result.status is QueryStatus.UNKNOWN
    assert result.outcome is Outcome.UNKNOWN
