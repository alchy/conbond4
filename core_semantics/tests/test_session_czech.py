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
from core_semantics.session import Session, TurnKind, TurnResult

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
    """„Petr viděl psa běžícího parkem." — `běžícího` i `parkem` visí
    pod PŘÍVLASTKOVOU VĚTOU, tedy hlouběji než na přísudku, a do čtení
    se nedostanou. Souřadný člen se sem NEHODÍ: od W‑73 ztracený není,
    čeká na rozhodnutí o sdílení role. ZÁZNAM, ne živý rozbor."""
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "viděl", "vidět", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "psa", "pes", "NOUN", 2, "obj", Case="Acc", Gender="Masc", Number="Sing"),
            _token(4, "běžícího", "běžet", "ADJ", 3, "acl", Case="Acc", Gender="Masc", Number="Sing"),
            _token(5, "parkem", "park", "NOUN", 4, "obl", Case="Ins", Gender="Masc", Number="Sing"),
            _token(6, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


def _coordinate_session() -> tuple[Session, Reading, TurnResult]:
    """Sezení, ve kterém věta se ztraceným členem čeká na `→@`."""
    from core_semantics.tests import golden

    text = "Petr viděl psa běžícího parkem."
    reading = _coordinate_subject()
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    first = session.utter(text, oracle)
    assert first.turn.lost, "věta se musí na něco ptát"
    return session, reading, first


def test_an_answer_that_changes_nothing_says_so() -> None:
    """ŽÁDNÝ TAH NEPOTVRDÍ UČENÍ, ANIŽ ŘEKNE, CO SE VE VĚTĚ ZMĚNILO
    *(N‑1)*. Tah ohlásil „✓ naučeno" a čtení zůstalo beze změny — člověk
    si myslel, že postoupil. Je to horší než otázka bez tahu: u té ví,
    že stojí."""
    from core_semantics.session import names_role

    session, reading, first = _coordinate_session()
    result = session.play(
        names_role("Je to taky podmět.", reading, first.turn.lost[0][1], ROLE_SUBJECT)
    )
    hlaseni = chr(10).join(result.lines)
    assert "ČTENÍ SE NEZMĚNILO" in hlaseni
    assert "„Petr“" in hlaseni, "musí říct, KDO tu roli drží"
    assert "„běžícího“" in hlaseni, "musí říct, KTERÝ člen zůstal mimo"
    assert "Mapování platí dál" in hlaseni, "naučené se nezahazuje"


def test_an_answer_that_works_stays_silent_about_it() -> None:
    """PROTIPŘÍKLAD: když role volná JE, člen do čtení vstoupí a žádná
    věta o nezměněném čtení se nepíše. Tah se NEODMÍTÁ ani tady, ani
    tam — mapování je naučené správně pro celou třídu tvarů."""
    from core_semantics.session import names_role

    session, reading, first = _coordinate_session()
    result = session.play(
        names_role("Je to okolnost.", reading, first.turn.lost[0][1], "jak")
    )
    hlaseni = chr(10).join(result.lines)
    assert "ČTENÍ SE NEZMĚNILO" not in hlaseni
    # PÁROVÁNÍ, NE VÝSKYT *(W‑74)*. Že se „jak“ i „běžet“ někde objeví,
    # by prošlo i tehdy, kdyby ten člen skončil v jiné roli — kontroluje
    # se proto role S FILLEREM v jednom řetězci, jako v původní zkoušce.
    assert "jak:běžet" in hlaseni


def _three_lost_members() -> Reading:
    """„Petr viděl psa běžícího parkem." — mimo čtení zůstanou DVA
    členy přívlastkové věty, takže se věta ptá na oba najednou."""
    return _coordinate_subject()


def _asked_about_many() -> tuple[Session, Reading, TurnResult]:
    from core_semantics.tests import golden

    text = "Petr viděl psa běžícího parkem."
    reading = _three_lost_members()
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    first = session.utter(text, oracle)
    assert len(first.turn.lost) >= 2, "věta se musí ptát na víc členů"
    return session, reading, first


def test_answering_one_question_does_not_cancel_the_others() -> None:
    """ODPOVĚĎ NA JEDNU OTÁZKU NESMÍ ZRUŠIT OSTATNÍ *(B‑25)*. Ztracené
    členy se braly z `turn`, jenže tah ODPOVĚDI je vlastní tah a má je
    prázdné — takže se systém po jedné odpovědi přestal ptát na zbytek."""
    from core_semantics.session import names_role

    session, reading, first = _asked_about_many()
    result = session.play(
        names_role("Je to okolnost.", reading, first.turn.lost[0][1], "jak")
    )
    assert result.turn.lost or "ZAHOZENO" in chr(10).join(result.lines)
    assert "jakou roli hraje" in (result.question or ""), "ptá se na zbylé členy"


def test_a_sentence_with_a_member_left_out_is_not_marked_read() -> None:
    """ZNAČKA NESMÍ VZNIKNOUT Z PRÁZDNÉ STOPY *(B‑25)*. `has_dropped` se
    ptala stopy tahu, která na tahové cestě nebyla, takže `✓ přečteno`
    vznikalo Z NEPŘÍTOMNOSTI DŮKAZU — u věty, ze které zůstalo venku
    čtrnáct členů."""
    from core_semantics.session import names_role

    session, reading, first = _asked_about_many()
    result = session.play(
        names_role("Je to okolnost.", reading, first.turn.lost[0][1], "jak")
    )
    assert not any(line.startswith("✓ přečteno") for line in result.lines)
    assert any(line.startswith("◐ přečteno, neúplné") for line in result.lines)


def test_the_dropped_note_survives_the_turn() -> None:
    """`[ZAHOZENO: …]` PŘEŽIJE TAH *(B‑25)*. Stopa je jediný nosič
    záznamu o ztrátě; když se po tahu vyprázdní, není z čeho poznat, že
    věta není celá."""
    from core_semantics.session import names_role

    session, reading, first = _asked_about_many()
    result = session.play(
        names_role("Je to okolnost.", reading, first.turn.lost[0][1], "jak")
    )
    assert any("ZAHOZENO" in line for line in result.lines)


def test_a_finished_sentence_still_gets_the_read_mark() -> None:
    """PROTIPŘÍKLAD: věta, ze které venku nezůstal NIKDO, značku `✓`
    dostane dál — oprava nesmí značku jen utlumit."""
    from core_semantics.tests import golden

    text = "Petr přišel."
    reading = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "přišel", "přijít", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    result = session.utter(text, oracle)
    assert any(line.startswith("✓ přečteno") for line in result.lines)


def _coordinate_with_attribute() -> Reading:
    """„Petr viděl psa běžícího parkem souseda." — ztracený člen
    `parkem`, který má SVŮJ genitivní přívlastek. Ten se smí ohlásit
    teprve tehdy, až ta role z odpovědi vznikne."""
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "viděl", "vidět", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "psa", "pes", "NOUN", 2, "obj", Case="Acc", Gender="Masc", Number="Sing"),
            _token(4, "běžícího", "běžet", "ADJ", 3, "acl", Case="Acc", Gender="Masc", Number="Sing"),
            _token(5, "parkem", "park", "NOUN", 4, "obl", Case="Ins", Gender="Masc", Number="Sing"),
            _token(6, "souseda", "soused", "NOUN", 5, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(7, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


def test_a_member_named_by_an_answer_gets_its_own_attribute() -> None:
    """PO ODPOVĚDI NESMÍ ZMLKNOUT ZÁVISLÝ ČLEN TOHO, CO BYLO PRÁVĚ
    POJMENOVÁNO *(W‑71)*. Patro přívlastku běželo PŘED patrem ztracené
    role, takže role, která teprve vznikla z odpovědi člověka, svůj
    přívlastek nikdy nedostala: hlásilo se „zánět ledvina" a o „plic"
    ani slovo. Mlčet o členu, který ve větě stojí, je táž vada jako
    ohlásit ho špatně."""
    from core_semantics.session import names_role
    from core_semantics.tests import golden

    text = "Petr viděl psa běžícího parkem souseda."
    reading = _coordinate_with_attribute()
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    first = session.utter(text, oracle)
    shape = next(sh for form, sh in first.turn.lost if form == "parkem")
    result = session.play(names_role("Je to okolnost.", reading, shape, "kudy"))
    privlastky = [line for line in result.lines if "PŘÍVLASTEK" in line]
    assert privlastky, "přívlastek nově pojmenovaného členu musí být vidět"
    assert "soused" in privlastky[0]


def test_an_attribute_of_a_member_outside_the_reading_is_not_claimed() -> None:
    """PROTIPŘÍKLAD: dokud ten člen ve čtení NENÍ, jeho přívlastek se
    nehlásí — visel by na něčem, o čem věta (zatím) nemluví."""
    from core_semantics.tests import golden

    text = "Petr viděl psa běžícího parkem souseda."
    reading = _coordinate_with_attribute()
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    privlastky = [
        line for line in session.utter(text, oracle).lines if "PŘÍVLASTEK" in line
    ]
    assert not privlastky, "dokud ten člen ve čtení není, přívlastek se nehlásí"


def _two_in_one_role(predicate: str, lemma: str) -> Reading:
    """„Petr a Jana <přišli/zvedli>." — dvě jména v roli `kdo`.
    ROZBOR JE U OBOU TÝŽ; liší se jedině sloveso."""
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "a", "a", "CCONJ", 3, "cc"),
            _token(3, "Jana", "Jana", "PROPN", 1, "conj", Case="Nom", Gender="Fem", Number="Sing"),
            _token(4, predicate, lemma, "VERB", 0, "root", Gender="Masc", Number="Plur", Polarity="Pos"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )


def _shared_session(predicate: str, lemma: str) -> tuple[Session, Reading, TurnResult]:
    from core_semantics.tests import golden

    text = f"Petr a Jana {predicate}."
    reading = _two_in_one_role(predicate, lemma)
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    session = Session(lexicon=golden.golden_lexicon())
    return session, reading, session.utter(text, oracle)


def test_two_names_in_one_role_are_not_split_silently() -> None:
    """SPORNÝ PŘÍPAD — TEN, KTERÝ ROZHODUJE O CELÉM MECHANISMU *(W‑73)*.

    „Petr a Jana přišli." platí o každém zvlášť, „Petr a Jana zvedli
    klavír." o nich dohromady — a ROZBOR MÁ OBĚ VĚTY IDENTICKÉ (`nsubj`
    + `cc` + `conj`, přísudek v plurálu). Rozdělit to mlčky znamená
    vyrobit tvrzení, které ve větě není; nerozdělit mlčky taky. Systém
    se proto PTÁ a do báze zatím nejde nic."""
    _, _, result = _shared_session("přišli", "přijít")
    assert "o každém zvlášť, nebo o nich dohromady" in (result.question or "")
    assert result.statement_id is None, "dokud se nerozhodne, nezapisuje se"


def test_the_distributive_answer_writes_two_statements() -> None:
    """KLADNÝ PŘÍPAD: „o každém zvlášť" → DVĚ tvrzení, ne dvě role.
    Jádro drží jeden term na roli a to se nemění — druhý uzel dostane
    vlastní výrok se sdíleným přísudkem."""
    from core_semantics.session import decides_sharing

    session, reading, first = _shared_session("přišli", "přijít")
    assert first.predication is not None
    result = session.play(
        decides_sharing("Každý zvlášť.", first.predication, reading, distributive=True)
    )
    zapsano = [line for line in result.lines if "zapsáno" in line]
    assert len(zapsano) == 2, "dvě tvrzení o dvou uzlech"
    assert any("Petr" in line for line in zapsano)
    assert any("Jana" in line for line in zapsano)


def test_the_collective_answer_writes_one_node() -> None:
    """ZÁPORNÝ PŘÍPAD: „dohromady" → JEDEN uzel a JEDNO tvrzení.
    Klavír zvedli spolu; dvě tvrzení by byla nepravda."""
    from core_semantics.session import decides_sharing

    session, reading, first = _shared_session("zvedli", "zvednout")
    assert first.predication is not None
    result = session.play(
        decides_sharing("Dohromady.", first.predication, reading, distributive=False)
    )
    zapsano = [line for line in result.lines if "zapsáno" in line]
    assert len(zapsano) == 1, "jedno tvrzení o jednom uzlu"
    assert "Petr_a_Jana" in zapsano[0]


def test_a_single_filler_asks_nothing_about_sharing() -> None:
    """PROTIPŘÍKLAD: věta s JEDNÍM členem v roli se na sdílení neptá —
    otázka nesmí vzniknout tam, kde není co rozdělovat."""
    from core_semantics.tests import golden

    text = "Petr přišel."
    reading = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "přišel", "přijít", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    result = Session(lexicon=golden.golden_lexicon()).utter(text, oracle)
    assert "dohromady" not in (result.question or "")
    assert result.statement_id is not None


def test_an_incomplete_name_keeps_the_partial_mark() -> None:
    """ZNAČKA MLUVÍ O ČTENÍ, NE O BÁZI *(W‑76)*. „Rožnov pod Radhoštěm
    je město." nesla `✓ přečteno` a o dva řádky níž `[JMÉNO NEÚPLNÉ]` —
    jenže `✓` slibuje, že CELÁ VĚTA je ve čtení, a „Radhoštěm" v něm
    není. Že se to nezapíše, je jiná otázka než co ta značka tvrdí."""
    from core_semantics.tests import golden

    text = "Rožnov pod Radhoštěm je město."
    reading = Reading(
        tokens=(
            _token(1, "Rožnov", "Rožnov", "PROPN", 5, "nsubj", Case="Nom", Gender="Masc", NameType="Geo", Number="Sing"),
            _token(2, "pod", "pod", "ADP", 3, "case", AdpType="Prep", Case="Ins"),
            _token(3, "Radhoštěm", "Radhošť", "PROPN", 1, "nmod", Case="Ins", Gender="Masc", NameType="Geo", Number="Sing"),
            _token(4, "je", "být", "AUX", 5, "cop", Number="Sing", Polarity="Pos"),
            _token(5, "město", "město", "NOUN", 0, "root", Case="Nom", Gender="Neut", Number="Sing"),
            _token(6, ".", ".", "PUNCT", 5, "punct"),
        ),
        provenance=STAMP,
    )
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    result = Session(lexicon=golden.golden_lexicon()).utter(text, oracle)
    assert result.lines[0].startswith("◐"), "chybějící kus věty patří do značky"
    assert any("JMÉNO NEÚPLNÉ" in line for line in result.lines)
    assert result.statement_id is None
