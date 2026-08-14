"""Metriky dialogu — N‑5 (K‑8).

`turns_to_learn` samo o sobě může lhát oběma směry, a K‑8 to říká
přesně: *jeden tah do naučení a deset chybných použití je horší než tři
tahy a stabilní správnost.* Testuje se proto hlavně to, že čísla nejdou
zlepšit špatným chováním.
"""

from __future__ import annotations

from core_semantics.ast import Entity, Group, atom, member_of, role
from core_semantics.lexicon import Operation, StructuralSignature
from core_semantics.metrics import measure
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session, answers_quantifier, revokes, says
from core_semantics.tests._console import echo

STAMP = "test"
SHAPE = StructuralSignature(
    lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"
)


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


def verb(subject: str, lemma: str, predicate: str) -> tuple[Token, ...]:
    return (
        tok(1, subject.title(), subject, "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, lemma, predicate, "VERB", 0, "root", Number="Sing"),
    )


def oracle() -> _Recorded:
    return _Recorded(
        {
            "Učitelka učí.": verb("učitelka", "učí", "učit"),
            "Kominík čistí.": verb("kominík", "čistí", "čistit"),
        }
    )


# --------------------------------------------------------------------------
# Informace na tah
# --------------------------------------------------------------------------


def test_a_turn_that_only_asks_is_not_informative() -> None:
    """Tah, který skončil otázkou, informaci nepřinesl — a je správně,
    že se to pozná. Bez toho by systém vypadal produktivně tím, že se ptá."""
    session = Session()
    session.utter("Učitelka učí.", oracle())
    stats = measure(session)
    assert stats.turns == 1
    assert stats.informative == 0
    assert stats.open_questions == 1
    assert stats.information_per_turn == 0.0


def test_derived_statements_do_not_inflate_the_information() -> None:
    """Odvozené a reifikované výroky se nepočítají.

    Jsou to DŮSLEDKY, ne nová znalost, a jejich počet se řídí tvarem
    vztahu — víc rolí by znamenalo „víc informace", což je nesmysl."""
    session = Session()
    session.play(
        says(
            "Petr má auto.",
            atom("mít", role("kdo", Entity("Petr")), role("co", Entity("a1"))),
        )
    )
    stats = measure(session)
    assert stats.stated == 1, "jeden tah, jeden výrok — zbytek je reifikace"
    assert len(list(session.kb.active())) > 1


# --------------------------------------------------------------------------
# Znovupoužití
# --------------------------------------------------------------------------


def test_a_pattern_used_only_where_it_was_born_does_not_count_as_reuse() -> None:
    """Vzor použitý jen tam, kde vznikl, je zapamatovaná odpověď na jednu
    větu — ne naučené pravidlo."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    stats = measure(session)
    assert stats.learned_patterns == 1
    assert stats.reused_patterns == 0
    assert stats.reuse_rate == 0.0


def test_reuse_counts_only_across_turns() -> None:
    """Táž věta podruhé se nepočítá; JINÁ věta téhož tvaru ano — na tom
    stojí rozdíl mezi naučeným pravidlem a zapamatovanou odpovědí."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    session.utter("Kominík čistí.", oracle())
    stats = measure(session)
    assert stats.learned_patterns == 1
    assert stats.reused_patterns == 1
    assert stats.reuse_rate == 1.0


# --------------------------------------------------------------------------
# Míra oprav — číslo, které drží `turns_to_learn` u země
# --------------------------------------------------------------------------


def test_answering_a_question_is_not_a_correction() -> None:
    """Systém se zeptal, protože NEVĚDĚL, ne protože se spletl. Počítat
    odpověď jako opravu by trestalo právě to chování, které se má
    odměňovat."""
    session = Session()
    asked = session.utter("Učitelka učí.", oracle())
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    assert measure(session).corrections == 0


def test_revoking_counts_as_a_correction() -> None:
    session = Session()
    written = session.play(
        says("Petr má auto.", member_of(Entity("Petr"), Group("řidič")))
    )
    assert written.statement_id is not None
    session.play(revokes("Spletl jsem se.", written.statement_id, "omyl"))
    stats = measure(session)
    assert stats.corrections == 1
    assert stats.correction_rate == 0.5


def test_metrics_fall_after_a_revoke_because_they_are_a_function_of_state() -> None:
    """Nic se nemasuje průběžně, takže odvolání se v číslech PROJEVÍ.

    Kdyby si vrstvy vedly čítače, měřily by samy sebe a informace by po
    `revoke` zůstala započítaná — metrika by chválila práci, která už
    neplatí."""
    session = Session()
    written = session.play(
        says("Petr má auto.", member_of(Entity("Petr"), Group("řidič")))
    )
    assert written.statement_id is not None
    before = measure(session).stated
    session.play(revokes("Spletl jsem se.", written.statement_id, "omyl"))
    assert measure(session).stated < before


def test_fast_learning_with_many_corrections_does_not_look_good() -> None:
    """K‑8 v jednom testu: jeden tah do naučení a hromada oprav musí být
    v číslech vidět jako horší než pomalejší, ale stabilní postup."""
    quick = Session()
    written = quick.play(
        says("Petr je řidič.", member_of(Entity("Petr"), Group("řidič")))
    )
    assert written.statement_id is not None
    for reason in ("první omyl", "druhý omyl"):
        quick.play(revokes("Ne tak.", written.statement_id, reason))

    steady = Session()
    for name in ("Petr", "Pavel"):
        steady.play(
            says(f"{name} je řidič.", member_of(Entity(name), Group("řidič")))
        )

    assert measure(quick).correction_rate > measure(steady).correction_rate
    assert measure(steady).information_per_turn > measure(quick).information_per_turn


def test_metrics_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("METRIKY DIALOGU — N‑5 (K‑8)")
    echo("=" * 72)
    session = Session()
    session.utter("Učitelka učí.", oracle())
    asked = session.results[-1]
    assert asked.predication is not None
    session.play(
        answers_quantifier("O každé.", asked.predication, SHAPE, Operation.FOR_ALL)
    )
    session.utter("Kominík čistí.", oracle())
    for line in measure(session).render():
        if line:
            echo(f"   {line}")
    echo("=" * 72)
