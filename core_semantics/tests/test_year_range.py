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


def sentence(
    druhy_form: str,
    druhy_lemma: str,
    *,
    spojka: str = "",
    predlozka: str = "v",
    pomlcka_jako_cc: bool = False,
    **druhy_feats: str,
) -> Reading:
    """«<Předložka> letech 1910 <spojka|–> <druhý> byl Petr na pobytu.»

    `spojka` prázdná znamená POMLČKU, tedy spojení bez spojovacího slova.
    """
    spojovaci = (
        tok(4, spojka, spojka, "CCONJ", 5, "cc")
        if spojka
        else tok(4, "–", "–", "PUNCT", 5, "punct")
    )
    if pomlcka_jako_cc:
        # TÁŽ POMLČKA, JINÁ ZNAČKA. Parser ji v korpusu otagoval jednou
        # `PUNCT/punct` a jednou `ADP/cc` — a na `ADP/cc` se první verze
        # B‑30 rozbila, protože se ptala jen na `cc`.
        spojovaci = tok(4, "–", "–", "ADP", 5, "cc")
    return Reading(
        tokens=(
            tok(1, predlozka, predlozka, "ADP", 2, "case",
                AdpType="Prep", Case="Loc"),
            tok(2, "letech", "léta", "NOUN", 6, "obl",
                Case="Loc", Gender="Neut", Number="Plur"),
            tok(3, "1910", "1910", "NUM", 2, "nummod",
                NumForm="Digit", NumType="Card"),
            spojovaci,
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
    neříká — zůstávají ztrátou a hlásí se.

    **A PROCHÁZÍ Z JINÉHO DŮVODU, NEŽ HLÍDÁ B‑30**: řadová číslovka není
    holý letopočet, takže vypadne dřív, než se na spojku vůbec někdo
    zeptá. O tom, že rozhoduje SPOJKA, tenhle test neříká nic — to
    dokládají až testy pod hlavičkou B‑30. Test, který prochází z jiného
    důvodu, než si myslí, je pořád zelený a nic nechrání."""
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


# --------------------------------------------------------------------------
# Úsek pozná SPOJKA, ne to, že jsou obojí letopočty — B‑30
# --------------------------------------------------------------------------
#
# První verze W‑95 skládala každý konjunkt letopočtu, takže „v letech
# 1910 NEBO 1920" dalo TÝŽ UZEL jako „1910 – 1911": věta říká, že se neví
# který, a báze by tvrdila jeden čas. A bylo to TICHÉ — žádné
# `[ZAHOZENO]`, žádná otázka. Pojistka „buď je úsek v uzlu celý, nebo tam
# ztráta zůstane" hlídala jen jeden směr; ten, který vyrábí nepravdu, je
# opačný: něco, co úsek NENÍ, se zapsalo jako úsek.


def _one_year(
    druhy: str,
    *,
    spojka: str = "",
    predlozka: str = "v",
    pomlcka_jako_cc: bool = False,
) -> tuple[str, bool]:
    """Vrátí zmínku a to, jestli druhý letopočet zůstal ztrátou."""
    reading = sentence(
        druhy,
        druhy,
        spojka=spojka,
        predlozka=predlozka,
        pomlcka_jako_cc=pomlcka_jako_cc,
        NumForm="Digit",
        NumType="Card",
    )
    session, oracle = _session(reading)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    ztracen = any(
        token.form == druhy
        for token in _reported_lost(reading, result.predication)
    )
    return str(result.predication), ztracen


def test_a_dash_makes_a_span() -> None:
    """Bez spojovacího slova je to ÚSEK a skládá se."""
    zmineno, ztracen = _one_year("1911")
    assert "léta_1910_1911" in zmineno and not ztracen


def test_a_dash_tagged_as_a_conjunction_is_still_a_dash() -> None:
    """TÁŽ POMLČKA DOSTANE OD PARSERU DVĚ RŮZNÉ ZNAČKY *(B‑30)*.

    „v letech 1910 – 1911" má `PUNCT/punct`, „v letech 1925 – 1933" má
    `ADP/cc` — ověřeno na živé službě. První verze opravy se ptala jen na
    `cc` a rozbila tím jeden skutečný úsek z korpusu; rozhoduje proto
    SPOJOVACÍ SLOVO (má písmena), ne značka."""
    zmineno, ztracen = _one_year("1911", pomlcka_jako_cc=True)
    assert "léta_1910_1911" in zmineno and not ztracen


def test_a_conjunction_means_two_times_not_a_span() -> None:
    """„v letech 1910 A 1920" jsou DVA ROKY. Uzel, který tvrdí úsek, by
    říkal něco, co ta věta neříká — takže se neskládá a ztráta se
    hlásí."""
    zmineno, ztracen = _one_year("1920", spojka="a")
    assert "léta_1910_1920" not in zmineno
    assert ztracen, "a mlčet se o tom nesmí"


def test_a_disjunction_means_it_is_not_known_which() -> None:
    """„v letech 1910 NEBO 1920" NEVÍ KTERÝ. Do B‑30 dalo TÝŽ uzel jako
    pomlčka, tedy jistý čas z věty, která žádný jistý čas netvrdí."""
    zmineno, ztracen = _one_year("1920", spojka="nebo")
    assert "léta_1910_1920" not in zmineno
    assert ztracen


def test_the_preposition_between_makes_a_span_even_with_a_conjunction() -> None:
    """„MEZI lety 2009 a 2013" je úsek SE SPOJKOU — ta předložka interval
    vymezuje sama. Pravidlo „`a` = nikdy úsek" by rozbilo jednu ze sedmi
    vět, které v korpusu fungují."""
    zmineno, ztracen = _one_year("1920", spojka="a", predlozka="mezi")
    assert "léta_1910_1920" in zmineno and not ztracen


def test_a_comma_list_asks_the_whole_coordination_not_one_edge() -> None:
    """„v letech 1910, 1911 A 1912" nese `cc` až u POSLEDNÍHO členu.
    Kdyby se ptalo jedné hrany, výčet by prošel jako úsek."""
    from core_semantics.cascade import date_parts_under

    reading = Reading(
        tokens=(
            tok(1, "V", "v", "ADP", 2, "case", AdpType="Prep", Case="Loc"),
            tok(2, "letech", "léta", "NOUN", 8, "obl",
                Case="Loc", Gender="Neut", Number="Plur"),
            tok(3, "1910", "1910", "NUM", 2, "nummod",
                NumForm="Digit", NumType="Card"),
            tok(4, ",", ",", "PUNCT", 5, "punct"),
            tok(5, "1911", "1911", "NUM", 3, "conj",
                NumForm="Digit", NumType="Card"),
            tok(6, "a", "a", "CCONJ", 7, "cc"),
            tok(7, "1912", "1912", "NUM", 3, "conj",
                NumForm="Digit", NumType="Card"),
            tok(8, "byl", "být", "VERB", 0, "root",
                Gender="Masc", Number="Sing", Polarity="Pos"),
            tok(9, ".", ".", "PUNCT", 8, "punct"),
        ),
        provenance=STAMP,
    )
    assert [t.form for t in date_parts_under(reading.tokens[1], reading)] == [
        "1910"
    ], "výčet se neskládá ani zčásti"
