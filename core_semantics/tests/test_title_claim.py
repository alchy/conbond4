"""Co tvrdí TITUL — druhý výrok, který se nabídne a nezapíše sám *(W‑55)*.

„básník Josef Hora" tvrdí DVĚ věci: že promluvil a že je básník. Zapsala
se jedna a o druhé systém na přímou otázku odpověděl **„nikdo to neřekl"**
— což byla nepravda o jeho vlastním vstupu. **Mezera, která o sobě lže,
je horší než mezera**: první se dá doplnit, druhá se dá jen objevit.

**Proč se to NEZAPISUJE ze tvaru.** Ne z opatrnosti — z měření. Ze 71
zmínek téhle stavby v korpusu je 29 POVOLÁNÍ („básník", „astronom"), 24
ÚŘAD DRŽENÝ V ČASE („prezident Masaryk", který zemřel v roce 1937) a 18
PŘÍBUZENSTVÍ („bratr Josef Čapek" — bratr KOHO?). Tvar je u všech tří
týž a rozbor je nerozlišuje. Zapsat `member` ze tvaru by znamenalo, že
dvě třetiny zápisů jsou buď bezčasé o něčem časovém, nebo neúplné
o vztahu — a ležely by v bázi jako doložený fakt.

**Odvození z konstrukce se tedy odmítá podruhé** (poprvé u `same_as`
z apozice, B‑22). Rozdíl proti tehdejšku je, že tentokrát se to dá
DOLOŽIT ČÍSLEM, a ne jen obhájit úvahou.
"""

from __future__ import annotations

from core_semantics.ast import Entity, Group, QueryStatus, member_of
from core_semantics.cascade import title_claims
from core_semantics.gaps import NO_PATH, STATED_UNDECIDED, GapFinder
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session, confirms_title
from core_semantics.lexicon import (
    LearnedPattern,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.unknown_precision import UnknownReason, diagnose

STAMP = "test"


def w(
    index: int, form: str, lemma: str, upos: str, head: int, deprel: str, **feats: str
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


#: „Nad hrobem promluvil básník Josef Hora." — bez předložkové vazby, aby
#: doména testu byla TITUL a ne role.
POET = Reading(
    tokens=(
        w(1, "básník", "básník", "NOUN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "Josef", "Josef", "PROPN", 1, "flat", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(3, "Hora", "Hora", "PROPN", 1, "flat", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, "promluvil", "promluvit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
        w(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)

#: „Je Josef Hora básník?"
ASK_POET = Reading(
    tokens=(
        w(1, "Je", "být", "AUX", 4, "cop", Number="Sing", Person="3", Polarity="Pos"),
        w(2, "Josef", "Josef", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(3, "Hora", "Hora", "PROPN", 2, "flat", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, "básník", "básník", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(5, "?", "?", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)

#: „Město Praha leží." — `nmod`, ne `flat`. ZÁPORNÝ PŘÍPAD.
CITY = Reading(
    tokens=(
        w(1, "Město", "město", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        w(2, "Praha", "Praha", "PROPN", 1, "nmod", Case="Nom", Gender="Fem", Number="Sing"),
        w(3, "leží", "ležet", "VERB", 0, "root", Number="Sing", Person="3", Polarity="Pos"),
        w(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

#: „bratří Čapků psali." — PLURÁL. Druhý ZÁPORNÝ PŘÍPAD.
BROTHERS = Reading(
    tokens=(
        w(1, "bratří", "bratr", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur"),
        w(2, "Čapků", "Čapka", "PROPN", 1, "flat", Animacy="Anim", Case="Gen", Gender="Masc", Number="Plur"),
        w(3, "psali", "psát", "VERB", 0, "root", Gender="Masc", Number="Plur", Polarity="Pos"),
        w(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

POET_TEXT = "Básník Josef Hora promluvil."
ASK_TEXT = "Je Josef Hora básník?"
CITY_TEXT = "Město Praha leží."
BROTHERS_TEXT = "Bratří Čapků psali."


class _Recorded:
    provenance = STAMP

    def parse(self, text: str) -> Utterance:
        mapping = {
            POET_TEXT: POET,
            ASK_TEXT: ASK_POET,
            CITY_TEXT: CITY,
            BROTHERS_TEXT: BROTHERS,
        }
        return Utterance(text=text, readings=(mapping[text],))


def _session() -> Session:
    """Tvary potvrzené člověkem. Bez nich by se systém právem ptal na
    kvantifikátor a měřilo by se to doptání, ne tvrzení titulu."""
    lexicon = czech_seed()
    for upos, case, deprel, operation in (
        ("PROPN", "Nom", "nsubj", Operation.SELF),
        ("NOUN", "Nom", "root", Operation.SELF),
    ):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number="Sing", case=case, deprel=deprel
                ),
                operation=operation,
                learned_from="test W‑55",
                status=PatternStatus.CONFIRMED,
            )
        )
    return Session(lexicon=lexicon)


# --------------------------------------------------------------------------
# Co se z věty PŘEČTE
# --------------------------------------------------------------------------


def test_the_title_is_read_as_a_claim() -> None:
    from core_semantics.cascade import generate

    predication = generate(POET)[0].predication
    assert title_claims(POET, predication) == (("Josef_Hora", "básník", 1),)


def test_a_modifier_is_not_a_claim() -> None:
    """ZÁPORNÝ PŘÍPAD. „Město Praha" má `nmod` — samostatný přívlastek,
    ne jedna zmínka. Tudy tvrzení nevzniká, a **stráž se neopisuje**:
    ptá se `titled_name_of`, takže platí totéž, co se změřilo u W‑53."""
    from core_semantics.cascade import generate

    predication = generate(CITY)[0].predication
    assert title_claims(CITY, predication) == ()


def test_a_plural_family_is_not_a_claim() -> None:
    """Druhý ZÁPORNÝ PŘÍPAD. „bratří Čapků" je SKUPINA dvou lidí (W‑54);
    `member(Čapka, bratr)` by tvrdil něco o člověku, který neexistuje."""
    from core_semantics.cascade import generate

    predication = generate(BROTHERS)[0].predication
    assert title_claims(BROTHERS, predication) == ()


def test_a_claim_about_someone_outside_the_reading_is_not_taken() -> None:
    """Jméno musí být VE ČTENÍ — jinak by tvrzení viselo na uzlu, o kterém
    věta nemluví. Táž stráž jako u genitivního přívlastku."""
    from core_semantics.cascade import Predication

    prazdna = Predication(predicate="promluvit", roles=())
    assert title_claims(POET, prazdna) == ()


# --------------------------------------------------------------------------
# Co se ZAPÍŠE — a co ne
# --------------------------------------------------------------------------


def test_the_sentence_is_written_and_the_claim_is_not() -> None:
    """Obojí v jednom testu ZÁMĚRNĚ: „nezapsalo se členství" by prošlo
    i tehdy, kdyby se nezapsalo vůbec nic."""
    session = _session()
    result = session.utter(POET_TEXT, _Recorded())
    assert result.statement_id is not None, "věta sama se zapsat musí"
    formule = [str(s.formula) for s in session.kb.active()]
    assert any(f.startswith("promluvit(") for f in formule)
    # `member(elem:s0001, group:·promluvit)` v bázi JE a být má — to je
    # reifikace samotné věty, ne tvrzení titulu. Hledá se ta konkrétní
    # dvojice; „žádný member“ by tady byl špatně položený dotaz.
    assert "member(elem:Josef_Hora, group:·básník)" not in formule, (
        "zapsat členství ze tvaru je ODVOZENÍ Z KONSTRUKCE — týž tichý "
        "default, jaký se odmítl u `same_as` z apozice (B‑22)"
    )


def test_the_claim_is_reported_not_swallowed() -> None:
    """Nezapsat je rozhodnutí; NEOHLÁSIT bylo opomenutí."""
    result = _session().utter(POET_TEXT, _Recorded())
    assert result.question is not None
    assert "básník Josef Hora" in result.question


def test_the_gap_stops_claiming_nobody_said_it() -> None:
    """JÁDRO CELÉHO W‑55. `U` zůstane `U` — nikdo to nepotvrdil — ale
    důvod „nikdo to neřekl" byl nepravdivý o vlastním vstupu."""
    session = _session()
    session.utter(POET_TEXT, _Recorded())
    result = session.utter(ASK_TEXT, _Recorded())
    assert result.status is QueryStatus.UNKNOWN
    hlaseni = "\n".join(result.lines)
    assert NO_PATH not in hlaseni
    assert STATED_UNDECIDED in hlaseni
    assert POET_TEXT in hlaseni, (
        "„řeklas to“ bez věty, ve které to stálo, je tvrzení bez důkazu"
    )


def test_a_question_nobody_touched_still_says_nobody_said_it() -> None:
    """Nová jmenovka se nesmí rozlít na každé `U`. Kdyby se rozlila,
    přestala by měřit cokoli — a ztratila by se přesně ta kategorie,
    kvůli které vznikla."""
    session = _session()
    session.utter(POET_TEXT, _Recorded())
    report = GapFinder(session.engine()).explain(
        member_of(Entity("Josef_Hora"), Group("astronom")),
        undecided=session.undecided(),
    )
    assert NO_PATH in "\n".join(report.render())


def test_confirming_writes_the_claim_and_closes_the_offer() -> None:
    session = _session()
    session.utter(POET_TEXT, _Recorded())
    written = session.play(confirms_title("Ano.", "Josef_Hora", "básník"))
    assert written.statement_id is not None
    result = session.utter(ASK_TEXT, _Recorded())
    assert result.status is QueryStatus.PROVEN_TRUE
    assert "čeká to na tvé potvrzení" not in "\n".join(result.lines), (
        "u zapsaného faktu by ta hláška člověku říkala, že se nic nestalo"
    )


# --------------------------------------------------------------------------
# Rozklad `U`
# --------------------------------------------------------------------------


def test_the_breakdown_has_its_own_reason_for_this() -> None:
    """Slít to s `NOT_STATED` by zakrylo právě ten rozdíl, kvůli kterému
    kategorie vznikla: na tohle `U` jde odpovědět JEDNÍM TAHEM — a systém
    ví, kterým."""
    session = _session()
    session.utter(POET_TEXT, _Recorded())
    found = diagnose(
        session.engine(),
        member_of(Entity("Josef_Hora"), Group("básník")),
        undecided=session.undecided(),
    )
    assert found is not None
    assert found.reason is UnknownReason.STATED_UNDECIDED
    assert not found.is_defect, (
        "není to vada: v bázi to NENÍ, takže paměť neselhala — čeká to na "
        "rozhodnutí, které nikdo neudělal"
    )
