"""Kvantifikátor na roli — L‑3.

Bez tohohle patra se z české věty se skupinou v roli nedá postavit ani
jeden platný atom: jádro kvantifikátor **vyžaduje** a `Predication`
žádný nenesla. Testy proto končí u jádra, ne u řetězce — akceptační
otázka zní „jde z toho udělat `Atom`?", ne „vypadá to hezky?".
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    Group,
    Quantifier,
    Sort,
    UnquantifiedRole,
    atom,
    role,
)
from core_semantics.cascade import (
    AWAITING_QUANTIFIER,
    AWAITING_REFERENCE,
    HARD_TIERS,
    ROLE_SUBJECT,
    cascade,
    quantifier_tier,
    role_mapping_tier,
)
from core_semantics.lexicon import (
    LearnedPattern,
    Lexicon,
    Operation,
    PatternStatus,
    StructuralSignature,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token
from core_semantics.session import Session, answers_quantifier
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


def sentence(determiner: str | None, noun: str = "učitelka") -> Reading:
    """«[determinátor] učitelka učí» — jedna věta, měnitelný determinátor."""
    tokens = [
        tok(1, noun, noun, "NOUN", 3, "nsubj", Case="Nom", Number="Sing"),
        tok(3, "učí", "učit", "VERB", 0, "root", Number="Sing"),
    ]
    if determiner is not None:
        tokens.insert(
            0, tok(2, determiner, determiner, "DET", 1, "det", Case="Nom")
        )
    return Reading(tokens=tuple(sorted(tokens, key=lambda t: t.index)), provenance=STAMP)


def tiers(lexicon: Lexicon) -> tuple[object, ...]:
    return (*HARD_TIERS, role_mapping_tier(lexicon), quantifier_tier(lexicon))


def read(reading: Reading, lexicon: Lexicon):  # type: ignore[no-untyped-def]
    return cascade(reading, tiers=tiers(lexicon))  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Explicitní determinátor
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "word,expected",
    [
        ("každý", Quantifier.FOR_ALL),
        ("všechen", Quantifier.FOR_ALL),
        ("všichni", Quantifier.FOR_ALL),
        ("nějaký", Quantifier.EXISTS),
        ("některý", Quantifier.EXISTS),
    ],
)
def test_explicit_determiner_decides_the_quantifier(
    word: str, expected: Quantifier
) -> None:
    verdict = read(sentence(word), czech_seed())
    assert verdict.decided is not None
    subject = verdict.decided.predication.reading(ROLE_SUBJECT)
    assert subject is not None
    assert subject.quantifier is expected
    assert subject.determiner is not None and subject.determiner.lemma == word
    assert word in subject.source, "vysvětlení musí říct, ze kterého slova to je"


def test_definiteness_is_not_quantification() -> None:
    """„ta učitelka" NEOTVÍRÁ skupinu — odkazuje na už existující uzel.

    Kdyby se určitost přeložila na `∃`, věta by přestala mluvit o jednom
    konkrétním člověku a začala mluvit o komkoli z učitelek. Rozřešit ten
    odkaz je práce V3, takže role zůstává otevřená a řekne se to nahlas.
    """
    verdict = read(sentence("ten"), czech_seed())
    assert verdict.decided is not None
    subject = verdict.decided.predication.reading(ROLE_SUBJECT)
    assert subject is not None
    assert subject.quantifier is None
    assert subject.awaiting == AWAITING_REFERENCE, (
        "určitost čeká na ROZŘEŠENÍ ODKAZU, ne na kvantifikátor; slít to "
        "do jedné otázky by znamenalo ptát se na špatnou věc"
    )
    assert subject.pending is None
    assert not verdict.complete
    assert any("URČITOST" in step for step in verdict.trace)
    assert verdict.question is not None
    assert "odkazuje" in verdict.question
    assert "∀" not in verdict.question


# --------------------------------------------------------------------------
# Holé jméno — většinový případ češtiny
# --------------------------------------------------------------------------


def test_bare_noun_gets_no_implicit_quantifier() -> None:
    """Čeština nemá členy, takže tohle je většina vět — a právě proto se
    tu nesmí nic dosadit. „Kočka je savec" je o každé kočce, „Kočka spí
    na gauči" o jedné konkrétní."""
    verdict = read(sentence(None), czech_seed())
    assert verdict.decided is not None
    subject = verdict.decided.predication.reading(ROLE_SUBJECT)
    assert subject is not None
    assert subject.quantifier is None
    assert subject.pending is not None
    assert subject.awaiting == AWAITING_QUANTIFIER
    assert not verdict.complete, "nehotové čtení se nesmí tvářit jako hotové"
    assert verdict.question is not None
    assert "∀" in verdict.question and "∃" in verdict.question


def test_question_names_the_shape_it_asks_about() -> None:
    verdict = read(sentence(None), czech_seed())
    assert verdict.question is not None
    assert "NOUN/Sing/Nom/nsubj" in verdict.question


def test_confirmed_shape_pattern_decides_without_asking_again() -> None:
    """Člověk potvrdí JEDNOU a pak to platí — data s proveniencí, ne
    zadrátovaný dohad (I‑16)."""
    lexicon = czech_seed()
    lexicon.teach(
        Trigger(lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"),
        Operation.FOR_ALL,
        learned_from="tah 4",
    )
    verdict = read(sentence(None), lexicon)
    assert verdict.decided is not None
    subject = verdict.decided.predication.reading(ROLE_SUBJECT)
    assert subject is not None
    assert subject.quantifier is Quantifier.FOR_ALL
    assert subject.determiner is None, "vzor plyne z tvaru, ne ze slova"
    assert verdict.complete
    assert verdict.question is None


def test_shape_pattern_survives_renaming() -> None:
    """Renaming test § 10: vzor sedí na tvar, ne na konkrétní slovo."""
    lexicon = czech_seed()
    lexicon.teach(
        Trigger(lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"),
        Operation.FOR_ALL,
        learned_from="tah 4",
    )
    first = read(sentence(None, "učitelka"), lexicon)
    second = read(sentence(None, "kominík"), lexicon)
    for verdict in (first, second):
        assert verdict.decided is not None
        subject = verdict.decided.predication.reading(ROLE_SUBJECT)
        assert subject is not None and subject.quantifier is Quantifier.FOR_ALL


def test_revoking_the_pattern_reopens_the_question() -> None:
    """Odvolatelnost není ozdoba: naučený kvantifikátor se může ukázat
    jako špatný a pak se musí věta zase ptát."""
    lexicon = czech_seed()
    pattern = lexicon.teach(
        Trigger(lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"),
        Operation.FOR_ALL,
        learned_from="tah 4",
    )
    assert read(sentence(None), lexicon).complete
    lexicon.revoke(pattern.key())
    reopened = read(sentence(None), lexicon)
    assert not reopened.complete
    assert reopened.question is not None


def test_two_candidate_shapes_ask_instead_of_picking() -> None:
    """Dvojznačnost se hlásí, nerozhoduje se za člověka (I‑1)."""
    lexicon = czech_seed()
    shape = Trigger(
        lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"
    )
    lexicon.teach(shape, Operation.FOR_ALL, learned_from="tah 4")
    lexicon.teach(shape, Operation.EXISTS, learned_from="tah 9")
    verdict = read(sentence(None), lexicon)
    assert verdict.decided is not None
    subject = verdict.decided.predication.reading(ROLE_SUBJECT)
    assert subject is not None and subject.quantifier is None
    assert any("POZOR" in step for step in verdict.trace)


def test_hypothesis_and_confirmation_are_different_states() -> None:
    lexicon = Lexicon()
    pattern = lexicon.teach(
        Trigger(lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"),
        Operation.FOR_ALL,
        learned_from="tah 4",
    )
    assert pattern.status is PatternStatus.HYPOTHESIS
    confirmed = lexicon.confirm(pattern.key())
    assert confirmed is not None and confirmed.status is PatternStatus.CONFIRMED
    assert lexicon.quantifier_candidates(
        StructuralSignature(
            lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"
        )
    )


# --------------------------------------------------------------------------
# To, kvůli čemu L‑3 vzniklo: z čtení jde postavit platný atom
# --------------------------------------------------------------------------


def test_without_a_quantifier_the_kernel_refuses_the_role() -> None:
    """Výchozí stav před L‑3, zapíchnutý, aby bylo proti čemu měřit."""
    with pytest.raises(UnquantifiedRole):
        role(ROLE_SUBJECT, Group("učitelka"))


def test_a_quantified_reading_builds_a_valid_atom() -> None:
    """Akceptační otázka L‑3: jde z čtení udělat `Atom`?"""
    lexicon = czech_seed()
    verdict = read(sentence("každý"), lexicon)
    assert verdict.decided is not None
    assert verdict.complete, "hotové čtení nesmí mít otevřenou roli"
    subject = verdict.decided.predication.reading(ROLE_SUBJECT)
    assert subject is not None and subject.quantifier is not None

    built = atom(
        verdict.decided.predication.predicate,
        role(subject.name, Group(subject.mention.lemma), subject.quantifier),
    )
    assert built.predicate == "učit"
    filler = built.get_role(ROLE_SUBJECT)
    assert filler is not None
    assert filler.quantifier is Quantifier.FOR_ALL
    assert filler.target.SORT is Sort.GROUP


# --------------------------------------------------------------------------
# Sezení
# --------------------------------------------------------------------------


class _Recorded:
    provenance = STAMP

    def __init__(self, reading: Reading, text: str) -> None:
        self._reading = reading
        self._text = text

    def parse(self, text: str):  # type: ignore[no-untyped-def]
        from core_semantics.oracle import Utterance

        return Utterance(text=self._text, readings=(self._reading,))


def test_session_asks_about_the_quantifier_and_replay_repeats_it() -> None:
    """Otázka se z čtení ODVOZUJE, neukládá — proto ji `replay` zopakuje.

    Kdyby se ukládala jako text, žurnál by přestal držet strukturu
    a začal držet odpověď (§ 10).
    """
    text = "Učitelka učí."
    session = Session()
    result = session.utter(text, _Recorded(sentence(None), text))
    assert result.question is not None
    assert any("?" in line for line in result.lines)

    replayed = Session.replay(session.journal)
    assert replayed.answers() == session.answers()
    assert replayed.results[-1].question == result.question


def test_session_stops_asking_once_the_pattern_is_confirmed() -> None:
    text = "Učitelka učí."
    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="NOUN", number="Sing", case="Nom", deprel="nsubj"
            ),
            operation=Operation.FOR_ALL,
            learned_from="tah 4",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    result = session.utter(text, _Recorded(sentence(None), text))
    assert result.question is None
    assert result.predication is not None
    assert "∀" in str(result.predication)


def test_dropped_token_is_reported_not_swallowed() -> None:
    """B‑12, přepsané po N‑6.

    Původní znění: „Filipovo auto je modré." vyjde jako tvrzení o VŠECH
    autech, protože přivlastnění se do čtení nedostane; že se nepřečte, je
    poctivá mez, ale mlčet o tom je vada.

    POŽADAVEK ZŮSTÁVÁ, JEN JE SPLNĚNÝ SILNĚJI. Přivlastnění se do čtení
    dostane — udělá ze jména URČITÝ POPIS — takže věta o všech autech
    NENÍ a hlásit ztrátu není co. Systém místo toho říká, že neví, KTERÝ
    uzel se míní, a to je otázka, na kterou existuje odpověď (`→=`).
    Původní znění bylo zapsané u té špatné příčiny: nešlo o to, že token
    vypadl, ale o to, že se z určitého popisu stalo obecné tvrzení."""
    text = "Filipovo auto je modré."
    reading = Reading(
        tokens=(
            # `Poss="Yes"` tu dřív chybělo a nahrávka se tím rozešla s živou
            # službou. Od N‑2c na tom poli záleží: přivlastnění se NESKLÁDÁ
            # do jména třídy, protože „Filipovo auto" není druh auta. Bez
            # příznaku by se složilo a otázka, kterou tenhle test hlídá,
            # by tiše zmizela.
            tok(1, "Filipovo", "Filipův", "ADJ", 2, "amod", Case="Nom", Poss="Yes"),
            tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
            tok(3, "je", "být", "AUX", 4, "cop", Number="Sing"),
            tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
        ),
        provenance=STAMP,
    )
    session = Session()
    result = session.utter(text, _Recorded(reading, text))
    assert result.predication is not None
    assert "Filipův" not in str(result.predication)
    assert "∀auto" not in str(result.predication), (
        "věta NENÍ tvrzení o všech autech — právě to byla ta vada"
    )
    subject = result.predication.reading("kdo")
    assert subject is not None and subject.quantifier is None
    assert result.question is not None and "auto" in result.question
    assert result.lines[0].startswith("◐"), (
        "nedořečený tah není celá věta — `✓` by slibovalo víc, než "
        "tah odevzdal"
    )
    assert result.statement_id is None, "nerozhodnutý odkaz se nezapisuje"
    # Ohlášení musí přežít replay — jinak by druhý průchod týmž žurnálem
    # tvrdil, že se nic neztratilo.
    assert Session.replay(session.journal).answers() == session.answers()


def test_preposition_is_not_reported_as_a_loss() -> None:
    """Hlásit každou předložku by z upozornění udělalo šum, ve kterém by
    skutečná ztráta zanikla."""
    text = "Učitelka učí."
    session = Session()
    result = session.utter(text, _Recorded(sentence(None), text))
    assert not any("ZAHOZENO" in step for step in result.trace)


def test_open_reading_does_not_get_the_finished_mark() -> None:
    """A‑9. `✓` slibuje hotový tah, jenže čtení s otevřenou rolí by na
    `role()` spadlo na `UnquantifiedRole`."""
    text = "Učitelka učí."
    open_result = Session().utter(text, _Recorded(sentence(None), text))
    assert open_result.question is not None
    assert open_result.lines[0].startswith("◐")

    closed = Session().utter("x", _Recorded(sentence("každý"), "x"))
    assert closed.question is None
    assert closed.lines[0].startswith("✓")


def test_quantifier_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("KVANTIFIKÁTOR NA ROLI — L‑3")
    echo("=" * 72)
    for word in ("každý", "nějaký", "ten", None):
        label = f"„{word} učitelka učí“" if word else "„Učitelka učí“ (holé jméno)"
        verdict = read(sentence(word), czech_seed())
        echo(f"\n» {label}")
        for line in verdict.render():
            echo(f"   {line}")
    echo("\n" + "=" * 72)


# --------------------------------------------------------------------------
# Odpověď na JEDNU VĚTU, ne na tvar — N‑8
# --------------------------------------------------------------------------
#
# `→∀` váže odpověď na TVAR, takže jedna odpověď zavře celou třídu vět.
# Většinou přesně to chceme. Jenže čeština má tvary, které v jedné větě
# znamenají `∀` a v druhé `∃`: „Vegetarián nejí maso" mluví o KAŽDÉM
# masu, „Petr jedl steak" o JEDNOM steaku — a `NOUN/Sing/Acc/obj` je to
# v obou. Po první odpovědi se druhá věta už nezeptá a přečte se špatně.
#
# `→∀1` je proto DRUHÁ otázka, ne náhrada té první: „jak se čte tahle
# věta" vedle „jak se čte tenhle tvar".


def _pending(reading: Reading) -> object:
    verdict = read(reading, czech_seed())
    assert verdict.decided is not None
    return verdict.decided.predication


def test_the_sentence_level_answer_closes_the_role() -> None:
    from core_semantics.session import answers_here

    session = Session()
    predication = _pending(sentence(None))
    result = session.play(
        answers_here("Jde o každou.", predication, ROLE_SUBJECT, Operation.FOR_ALL)  # type: ignore[arg-type]
    )
    assert result.predication is not None
    subject = result.predication.reading(ROLE_SUBJECT)
    assert subject is not None
    assert subject.quantifier is Quantifier.FOR_ALL
    assert subject.pending is None


def test_the_sentence_level_answer_teaches_nothing() -> None:
    """JÁDRO N‑8. Kdyby se tvar naučil, další věta téhož tvaru by se
    nezeptala — a právě o to, že se zeptá, tady jde."""
    from core_semantics.session import answers_here

    session = Session()
    before = session.lexicon.all()
    session.play(
        answers_here("Jde o každou.", _pending(sentence(None)), ROLE_SUBJECT, Operation.FOR_ALL)  # type: ignore[arg-type]
    )
    assert session.lexicon.all() == before


def test_the_shape_level_answer_still_teaches() -> None:
    """PROTIPŘÍKLAD REVIEWERA (2). `→∀1` NENÍ náhrada `→∀`: tvarová
    odpověď dál zavírá celou třídu, jinak by se každá věta musela
    rozhodovat zvlášť a učení by zmizelo."""
    session = Session()
    predication = _pending(sentence(None))
    subject = predication.reading(ROLE_SUBJECT)  # type: ignore[attr-defined]
    assert subject is not None and subject.pending is not None
    session.play(
        answers_quantifier(
            "Platí to o každé.", predication, subject.pending, Operation.FOR_ALL  # type: ignore[arg-type]
        )
    )
    assert any(p.operation is Operation.FOR_ALL for p in session.lexicon.all())


def test_answering_a_role_that_does_not_wait_is_refused() -> None:
    """Tah, který nemá co zavřít, se nesmí tvářit, že něco udělal."""
    from core_semantics.session import answers_here

    session = Session()
    result = session.play(
        answers_here("Jde o každou.", _pending(sentence("každý")), ROLE_SUBJECT, Operation.FOR_ALL)  # type: ignore[arg-type]
    )
    assert result.error is not None
    assert any("nečeká" in line for line in result.lines)
