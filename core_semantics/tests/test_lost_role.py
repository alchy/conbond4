"""Doptání na ztracený člen — N‑5.

Zadání člověka: *„věta se zahozeným významovým tokenem MUSÍ ZÍSKAT
významový token, pokud existuje."* Řeší to PŘÍČINU, ne následek —
chybí role, tak si o ni řekni.

Do N‑5 se ztráta jen ohlásila do stopy a věta se zapsala oseknutá.
Ohlásit je lepší než mlčet, ale pořád je to konstatování; systém, který
ví, že mu něco chybí, se má **zeptat**.

Smyčka je táž jako u kvantifikátoru: **zeptat se → odpověď jako TAH →
naučit TVAR → přečíst větu ZNOVU.**
"""

from __future__ import annotations

from core_semantics.cascade import cascade, lost_members, lost_shape
from core_semantics.lexicon import Mood, czech_seed
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session, names_role

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


def sentence(owner: str) -> Reading:
    """«<Čí> auto je modré.» — PŘIVLASTNĚNÍ nemá roli.

    Původně tu stálo „Jan nesmí dostat penicilin.", jenže tam předmět
    ztracený BÝT PŘESTAL: složený přísudek (G‑1a) ho vtáhl do predikace,
    a to je správně. Příklad se proto vyměnil za ten, který ztracený
    člen má doopravdy — přivlastňovací přívlastek roli nemá a je to
    skutečná mez, ne vada, kterou lze opravit jinde.
    """
    return Reading(
        tokens=(
            tok(1, f"{owner}ovo", f"{owner}ův", "ADJ", 2, "amod", Case="Nom", Poss="Yes"),
            tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
            tok(3, "je", "být", "AUX", 4, "cop", Number="Sing"),
            tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
            tok(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )


class _Recorded:
    provenance = STAMP

    def __init__(self, mapping: dict[str, Reading]) -> None:
        self._mapping = mapping

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._mapping[text],))


DENIED = "Filipovo auto je modré."
OTHER = "Petrovo auto je modré."
SHAPE = "nsubj>amod+Nom"


def oracle() -> _Recorded:
    return _Recorded({DENIED: sentence("Filip"), OTHER: sentence("Petr")})


# --------------------------------------------------------------------------
# Tvar
# --------------------------------------------------------------------------


def test_the_shape_is_a_path_not_a_word() -> None:
    """Učí se TVAR, ne slovo — jedna odpověď má zavřít celou třídu vět.

    Cesta od přísudku je podstatná: `penicilin` nevisí na slovese, ale
    pod infinitivem, a `xcomp>obj+Acc` platí stejně pro „smí dostat",
    „chce koupit" i „musí vrátit"."""
    reading = sentence("Filip")
    assert lost_shape(reading.tokens[0], reading) == SHAPE


def test_only_what_is_really_in_the_parse_is_asked_about() -> None:
    """„Pokud existuje" je podstatná půlka zadání: interpunkce, spona ani
    pomocné sloveso nejsou ztracený člen a otázka bez odběratele je horší
    než ticho."""
    reading = sentence("Filip")
    verdict = cascade(reading)
    assert verdict.decided is not None
    lost = {t.form for t, _ in lost_members(reading, verdict.decided.predication)}
    assert lost == {"Filipovo"}


# --------------------------------------------------------------------------
# Smyčka
# --------------------------------------------------------------------------


def test_a_lost_member_is_asked_about_not_just_noted() -> None:
    session = Session()
    result = session.utter(DENIED, oracle())
    assert result.question is not None
    assert "Filipovo" in result.question
    assert SHAPE in result.question


def test_an_incomplete_sentence_is_not_written() -> None:
    """Zapsat ji teď a po odpovědi znovu by uložilo DVA výroky — nejdřív
    oseknutý, pak celý — a ten první by nikdo neodvolal."""
    session = Session()
    result = session.utter(DENIED, oracle())
    assert result.statement_id is None
    assert session.program() == ()


def test_the_answer_completes_the_very_sentence_that_asked() -> None:
    """Kdyby tah jen učil, člověk by musel větu zopakovat — a to je ta
    práce navíc, kvůli které se lidem s takovými systémy nechce mluvit."""
    session = Session()
    session.utter(DENIED, oracle())
    answer = session.play(
        names_role("Je to vlastník.", sentence("Filip"), SHAPE, "čí")
    )
    assert answer.predication is not None
    assert answer.predication.role("čí") is not None
    assert "Filipův" in str(answer.predication)
    assert any("naučeno" in line for line in answer.lines)


def test_one_answer_closes_the_whole_class() -> None:
    """JINÁ věta téhož tvaru se doplní sama — to je rozdíl mezi naučeným
    vzorem a zapamatovanou odpovědí."""
    session = Session()
    session.utter(DENIED, oracle())
    session.play(names_role("Je to vlastník.", sentence("Filip"), SHAPE, "čí"))

    again = session.utter(OTHER, oracle())
    assert again.predication is not None
    assert again.predication.role("čí") is not None
    assert again.question is None or "Petrovo" not in again.question
    assert any("DOPLNĚNO" in step for step in again.trace)


def test_the_learned_shape_is_revocable_data() -> None:
    """I‑16: co se naučí odpovědí, jde odvolat stejně jako cokoli jiného."""
    session = Session()
    session.utter(DENIED, oracle())
    session.play(names_role("Je to vlastník.", sentence("Filip"), SHAPE, "čí"))
    learned = [m for m in session.lexicon.all_roles() if m.surface == SHAPE]
    assert learned and "tah" in learned[0].learned_from

    session.lexicon.revoke_role(learned[0].key())
    assert session.utter(OTHER, oracle()).question is not None


def test_the_whole_loop_replays_from_the_journal() -> None:
    """Odpověď je TAH, takže leží v žurnálu a přehrání se neptá podruhé."""
    session = Session()
    session.utter(DENIED, oracle())
    session.play(names_role("Je to vlastník.", sentence("Filip"), SHAPE, "čí"))
    replayed = Session.replay(session.journal)
    assert replayed.answers() == session.answers()
    assert replayed.program() == session.program()


def test_lost_role_transcript_prints() -> None:
    from core_semantics.tests._console import echo

    echo("\n" + "=" * 72)
    echo("DOPTÁNÍ NA ZTRACENÝ ČLEN — N‑5")
    echo("=" * 72)
    session = Session()
    steps = [
        (DENIED, session.utter(DENIED, oracle())),
        (
            "→@ Je to vlastník.",
            session.play(
                names_role("Je to vlastník.", sentence("Filip"), SHAPE, "čí")
            ),
        ),
        (OTHER + "   (JINÁ věta téhož tvaru)", session.utter(OTHER, oracle())),
    ]
    for label, result in steps:
        echo(f"\n» {label}")
        for line in result.lines:
            echo(f"   {line}")
    echo("=" * 72)
