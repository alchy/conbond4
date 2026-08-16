"""Rozsah letopočtů je jeden úsek — W‑95.

„V letech **1910 – 1911** byl Karel Čapek na studijním pobytu." dávalo
zmínku `léta_1910` a druhý letopočet hlásilo jako ztracený člen. Ta
zmínka je UŽŠÍ, než co ta věta říká; do báze se to nedostalo jen proto,
že ztracený člen zápis blokoval — tedy chránilo nás před tím CIZÍ
PRAVIDLO, ne kontrola téhle věci.
"""

from __future__ import annotations

from core_semantics.cascade import _reported_lost, date_parts_under
from core_semantics.lexicon import (
    LearnedPattern,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session

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


def sentence(druhy_form: str, druhy_lemma: str, **druhy_feats: str) -> Reading:
    """«V letech 1910 – <druhý> byl Petr na pobytu.»"""
    return Reading(
        tokens=(
            tok(1, "V", "v", "ADP", 2, "case", AdpType="Prep", Case="Loc"),
            tok(2, "letech", "léta", "NOUN", 6, "obl",
                Case="Loc", Gender="Neut", Number="Plur"),
            tok(3, "1910", "1910", "NUM", 2, "nummod",
                NumForm="Digit", NumType="Card"),
            tok(4, "–", "–", "PUNCT", 5, "punct"),
            tok(5, druhy_form, druhy_lemma, "NUM", 3, "conj", **druhy_feats),
            tok(6, "byl", "být", "VERB", 0, "root",
                Gender="Masc", Number="Sing", Polarity="Pos"),
            tok(7, "Petr", "Petr", "PROPN", 6, "nsubj",
                Case="Nom", Gender="Masc", Number="Sing"),
            tok(8, ".", ".", "PUNCT", 6, "punct"),
        ),
        provenance=STAMP,
    )


TEXT = "V letech 1910 – 1911 byl Petr na pobytu."


class _Oracle:
    provenance = STAMP

    def __init__(self, reading: Reading) -> None:
        self._reading = reading

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._reading,))


def _session(reading: Reading) -> tuple[Session, _Oracle]:
    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(lemma="", upos="NOUN", number="Plur", case="Loc",
                            deprel="obl"),
            operation=Operation.EXISTS,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    return Session(lexicon=lexicon), _Oracle(reading)


def test_a_year_range_is_one_mention() -> None:
    """Oba letopočty patří do TÉŽE zmínky — je to jeden časový úsek."""
    reading = sentence("1911", "1911", NumForm="Digit", NumType="Card")
    dily = date_parts_under(reading.tokens[1], reading)
    assert [t.form for t in dily] == ["1910", "1911"]

    session, oracle = _session(reading)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    assert "léta_1910_1911" in str(result.predication)


def test_an_ordinal_pair_is_not_a_range_and_stays_lost() -> None:
    """PROTIPŘÍKLAD: „ve **30. a 40.** letech" jsou DVĚ desetiletí, ne
    jeden úsek. Složit je do jedné zmínky by tvrdilo něco, co ta věta
    neříká — zůstávají ztrátou a hlásí se."""
    reading = sentence("40.", "40", NumForm="Digit", NumType="Card")
    dily = date_parts_under(reading.tokens[1], reading)
    assert [t.form for t in dily] == ["1910"], "řadová číslovka se nepřipojí"

    session, oracle = _session(reading)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    assert any(
        "40." in line and "ZAHOZENO" in line for line in result.lines
    ), "a mlčet se o ní nesmí"


def test_the_range_is_never_narrowed_to_its_first_year() -> None:
    """POJISTKA *(W‑95)*: BUĎ JE ÚSEK V UZLU CELÝ, NEBO TAM ZTRÁTA
    ZŮSTANE — nikdy uzel s prvním rokem a k tomu ticho.

    Do W‑95 platila ta podmínka jen náhodou: zápis blokoval ztracený
    člen, tedy CIZÍ pravidlo. Ochrana cizím pravidlem vydrží přesně do
    chvíle, kdy se to pravidlo z jiného důvodu uvolní, takže se to od
    teď kontroluje samo."""
    for druhy_form, druhy_lemma in (("1911", "1911"), ("40.", "40")):
        reading = sentence(
            druhy_form, druhy_lemma, NumForm="Digit", NumType="Card"
        )
        session, oracle = _session(reading)
        result = session.utter(TEXT, oracle)
        assert result.predication is not None
        cely = druhy_lemma in str(result.predication)
        ztracen = any(
            token.form == druhy_form
            for token in _reported_lost(reading, result.predication)
        )
        assert cely or ztracen, (
            f"„{druhy_form}“ se ani nesložilo, ani neohlásilo — to je "
            "zmínka užší, než co věta říká, a nikdo o tom neví"
        )
