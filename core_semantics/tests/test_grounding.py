"""V3 — zmínka na uzel a směrování tahu, L‑5.

Do L‑5 česká věta skončila u `✓ přečteno` a **do báze nešlo nic**. Testuje
se proto hlavně to, co se tím otevřelo, a co se přitom nesmí porušit:
nový uzel zakládá jen `!`, otázka jen čte, a nezakotvená věta nezapíše
ani půlku.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import Entity, Group, Place, QueryStatus, Quantifier, Sort
from core_semantics.grounding import UNSUPPORTED_UPOS, ground, name_of
from core_semantics.lexicon import (
    LearnedPattern,
    Lexicon,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session
from core_semantics.storage import KnowledgeBase
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
    """Nahrané orákulum pro jednu větu."""

    provenance = STAMP

    def __init__(self, text: str, *tokens: Token) -> None:
        self._utterance = Utterance(
            text=text, readings=(Reading(tokens=tokens, provenance=STAMP),)
        )

    def parse(self, text: str) -> Utterance:
        return self._utterance


def shaped(*shapes: tuple[str, str, str, str, Operation]) -> Lexicon:
    """Lexikon s POTVRZENÝMI tvary — rozhodnutí člověka, zapsané."""
    lexicon = czech_seed()
    for upos, number, case, deprel, operation in shapes:
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number=number, case=case, deprel=deprel
                ),
                operation=operation,
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    return lexicon


PROPN_SUBJECT = ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF)
NOUN_OBJECT = ("NOUN", "Sing", "Acc", "obj", Operation.EXISTS)
NOUN_SUBJECT = ("NOUN", "Sing", "Nom", "nsubj", Operation.FOR_ALL)


def has_car(text: str = "Filip má auto.") -> _Recorded:
    return _Recorded(
        text,
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )


# --------------------------------------------------------------------------
# Zakotvení
# --------------------------------------------------------------------------


def test_proper_name_becomes_an_individual() -> None:
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    result = session.utter("Filip má auto.", has_car())
    assert result.statement_id is not None
    statement, _, _ = session.kb.inspect(result.statement_id)
    filler = statement.formula.get_role("kdo")  # type: ignore[union-attr]
    assert filler is not None
    assert filler.target == Entity("Filip")
    assert filler.quantifier is None, (
        "individuum kvantifikátor nenese — konkrétnost je vlastnost sortu, "
        "ne značka navíc"
    )


def test_common_noun_becomes_a_group_with_its_quantifier() -> None:
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    result = session.utter("Filip má auto.", has_car())
    assert result.statement_id is not None
    statement, _, _ = session.kb.inspect(result.statement_id)
    filler = statement.formula.get_role("co")  # type: ignore[union-attr]
    assert filler is not None
    assert filler.target == Group("auto")
    assert filler.quantifier is Quantifier.EXISTS


def test_place_role_decides_the_sort_not_the_word() -> None:
    """„Praha" je `Place` proto, že `kam` je prostorová role slovníku jádra
    (§ 3.6) — ne proto, že by si V3 o Praze něco myslela."""
    session = Session(lexicon=shaped(PROPN_SUBJECT))
    result = session.utter(
        "Petr jel do Prahy.",
        _Recorded(
            "Petr jel do Prahy.",
            tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "jel", "jet", "VERB", 0, "root", Number="Sing"),
            tok(3, "do", "do", "ADP", 4, "case"),
            tok(4, "Prahy", "Praha", "PROPN", 2, "obl", Case="Gen", Number="Sing"),
        ),
    )
    assert result.statement_id is not None
    statement, _, _ = session.kb.inspect(result.statement_id)
    filler = statement.formula.get_role("kam")  # type: ignore[union-attr]
    assert filler is not None
    assert filler.target == Place("Praha")
    assert filler.target.SORT is Sort.PLACE
    assert filler.quantifier is None, "místo se nekvantifikuje"


def test_surface_role_cannot_be_grounded_and_says_so() -> None:
    """Role, která zůstala povrchová (`v+Loc` je `kde` i `kdy`), neurčí
    sort — a je to táž nerozhodnutost o patro dřív, ne nová."""
    session = Session(lexicon=shaped(PROPN_SUBJECT))
    result = session.utter(
        "Petr jel v pondělí.",
        _Recorded(
            "Petr jel v pondělí.",
            tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "jel", "jet", "VERB", 0, "root", Number="Sing"),
            tok(3, "v", "v", "ADP", 4, "case"),
            tok(4, "pondělí", "pondělí", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
        ),
    )
    assert result.statement_id is None
    assert any("NEZAKOTVENO" in line for line in result.lines)
    assert session.program() == ()


def test_pronoun_is_refused_out_loud() -> None:
    """Zájmeno BEZ ANTECEDENTU se odmítne NAHLAS.

    Od 0.1.16 už zájmena nejsou celá za hranicí: kandidáta z předchozí
    věty systém NAVRHNE a zeptá se. Když ale předchozí věta žádného
    nenabízí — a v prázdném sezení nenabízí nikoho — nesmí se sáhnout
    jinam. Nabídnout uzel odjinud znamená tvrdit, že text odkazuje tam,
    kde nic nestojí, a to je horší než přiznat mez.

    Zápis je zakázaný pořád stejně: dokud o odkazu nepadne rozhodnutí,
    věta se nezapisuje.
    """
    assert "PRON" in UNSUPPORTED_UPOS
    session = Session(lexicon=shaped(NOUN_OBJECT))
    result = session.utter(
        "On má auto.",
        _Recorded(
            "On má auto.",
            tok(1, "On", "on", "PRON", 2, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
            tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
        ),
    )
    assert result.statement_id is None
    assert result.question is not None
    assert "V předchozí větě nikdo takový nestojí" in result.question
    assert session.program() == ()


# --------------------------------------------------------------------------
# Určitý popis
# --------------------------------------------------------------------------


def definite_car(text: str = "To auto je modré.") -> _Recorded:
    return _Recorded(
        text,
        tok(1, "To", "ten", "DET", 2, "det", Case="Nom"),
        tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
        tok(3, "je", "být", "AUX", 4, "cop", Number="Sing"),
        tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
    )


def test_definite_description_documents_an_existing_node() -> None:
    """Určitý popis se DOKLÁDÁ, nezakládá. Kdyby zakládal, systém by si na
    každé zopakování téže věci vyrobil dalšího dvojníka."""
    from core_semantics.ast import member_of

    session = Session(
        lexicon=shaped(("ADJ", "Sing", "Nom", "root", Operation.SELF))
    )
    session.kb.attach(member_of(Entity("a1"), Group("auto")))
    before = len(list(session.kb.active()))

    result = session.utter("To auto je modré.", definite_car())
    assert result.statement_id is not None
    statement, _, _ = session.kb.inspect(result.statement_id)
    filler = statement.formula.get_role("kdo")  # type: ignore[union-attr]
    assert filler is not None and filler.target == Entity("a1")
    # I jednoznačné doložení se VYPÍŠE (M‑4): odkaz, který vyšel na
    # jediného kandidáta, je pořád rozhodnutí systému, ne fakt z věty.
    assert any(
        "auto → a1 (určitý popis; jediný kandidát)" in line
        for line in result.lines
    ), result.lines
    assert len(list(session.kb.active())) > before  # přibyl vztah, ne uzel


def test_definite_description_with_two_candidates_asks() -> None:
    from core_semantics.ast import member_of

    session = Session(
        lexicon=shaped(("ADJ", "Sing", "Nom", "root", Operation.SELF))
    )
    session.kb.attach(member_of(Entity("a1"), Group("auto")))
    session.kb.attach(member_of(Entity("a2"), Group("auto")))
    result = session.utter("To auto je modré.", definite_car())
    assert result.statement_id is None
    assert result.question is not None
    assert "Znám jich víc" in result.question


def test_definite_description_without_a_referent_asks() -> None:
    session = Session(
        lexicon=shaped(("ADJ", "Sing", "Nom", "root", Operation.SELF))
    )
    result = session.utter("To auto je modré.", definite_car())
    assert result.statement_id is None
    assert result.question is not None
    assert "nezakládá" in result.question


# --------------------------------------------------------------------------
# Směrování tahu
# --------------------------------------------------------------------------


def test_assertion_becomes_a_fact_in_the_base() -> None:
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    result = session.utter("Filip má auto.", has_car())
    assert result.statement_id is not None
    assert session.program(), "tah `!` má bázi změnit"
    assert any("zapsáno" in line for line in result.lines)


def test_question_is_answered_not_written() -> None:
    """`?` → `ask`, ne `attach`. Otázka bázi nemění (I‑12)."""
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    session.utter("Filip má auto.", has_car())
    before = session.program()

    answer = session.utter("Má Filip auto?", has_car("Má Filip auto?"))
    assert answer.statement_id is None
    assert answer.status is QueryStatus.PROVEN_TRUE
    assert session.program() == before, "otázka bázi nesmí změnit"


def test_question_about_an_unknown_name_creates_nothing() -> None:
    """Nový uzel zakládá JEN `attach` (§ 0.2). Ptát se na neznámé jméno je
    legitimní `U` — ne důvod ho založit."""
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    answer = session.utter("Má Filip auto?", has_car("Má Filip auto?"))
    assert answer.status is QueryStatus.UNKNOWN
    assert session.program() == ()
    assert answer.statement_id is None


def test_unknown_mood_is_not_guessed() -> None:
    """Hádat mezi „zapiš to" a „odpověz na to" je nejhorší tichá volba,
    jakou tenhle systém může udělat — jedna z nich mění bázi.

    Z textu tenhle stav dnes nevznikne (`_mood_of` vrací `ASSERTION`, když
    otazník chybí), ale volající náladu smí přebít, a tudy se dovnitř
    dostane. Zapíchnuto proto, že ta větev je jediná zábrana.
    """
    from core_semantics.lexicon import Mood

    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    result = session.utter(
        "Filip má auto", has_car("Filip má auto"), mood=Mood.UNKNOWN
    )
    assert result.predication is not None
    assert result.statement_id is None
    assert session.program() == ()


def test_punctuation_decides_whether_the_base_changes() -> None:
    """Od L‑5 na náladě visí, jestli se báze změní — dřív vybírala mezi
    dvěma čteními. Výchozí `ASSERTION` je proto vědomá volba."""
    writes = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    writes.utter("Filip má auto.", has_car())
    assert writes.program()

    asks = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    asks.utter("Má Filip auto?", has_car("Má Filip auto?"))
    assert asks.program() == ()


# --------------------------------------------------------------------------
# Identita jmen
# --------------------------------------------------------------------------


def test_repeated_name_says_it_is_the_same_node() -> None:
    """Podmínka A z M‑2: kanonizace je DEFAULT, a default se říká nahlas.

    Smí být default jen proto, že je odvolatelný (`!≠`, `!÷`) — a to je
    přesně ten rozdíl proti kvantifikátoru, kde default být nesmí.
    """
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    first = session.utter("Filip má auto.", has_car())
    assert any("Filip → Filip (založen)" in line for line in first.lines)

    again = session.utter("Filip má auto.", has_car())
    assert any(
        "Filip → Filip (kanonicky; týž uzel, o kterém už řeč byla)" in line
        for line in again.lines
    ), again.lines


def test_canonisation_refuses_when_the_same_name_is_disputed() -> None:
    """Podmínka B z M‑2 — a od N‑10 ZÚŽENÁ na uzly TÉHOŽ JMÉNA.

    Tam ztotožnit mlčky opravdu nejde: neví se, KTERÝ z nich zmínka
    trefila, a rozhodnout to za člověka by znamenalo vzít zpátky
    rozdělení, které sám udělal."""
    from core_semantics.ast import Label, P_NAME, atom, role

    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    session.utter("Filip má auto.", has_car())
    session.kb.attach(
        atom(P_NAME, role("of", Entity("Filip_2")), role("value", Label("Filip")))
    )
    session.kb.attach(
        atom(P_NAME, role("of", Entity("Filip")), role("value", Label("Filip")))
    )

    result = session.utter("Filip má auto.", has_car())
    assert result.statement_id is None
    assert result.question is not None
    assert "Kterého" in result.question


def test_a_dispute_with_another_name_gets_a_verdict_not_a_question() -> None:
    """N‑10. Spor s uzlem JINÉHO jména nezpochybňuje, KTERÝ uzel se míní
    — zpochybňuje jejich TOTOŽNOST, a to je práce evaluátoru (M‑1).

    Odmítnout tu zakotvení znamenalo, že se člověk na spornou identitu
    nikdy nedozvěděl verdikt: přímá otázka nedala `CONFLICT` a otázka na
    fakt nedala `U`, obojí skončilo doptáním na to, kdo je kdo. Verdikt
    je víc než otázka — a M‑1 ho slibuje."""
    from core_semantics.ast import QueryStatus, same_as_of
    from core_semantics.engine import Engine

    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    session.utter("Filip má auto.", has_car())
    session.kb.attach(same_as_of(Entity("Filip"), Entity("Filip_z_Brna")))
    session.kb.attach(
        same_as_of(Entity("Filip"), Entity("Filip_z_Brna")).complement()
    )

    verdict = Engine(session.kb).ask(
        same_as_of(Entity("Filip"), Entity("Filip_z_Brna"))
    )
    assert verdict.status is QueryStatus.CONFLICT
    assert verdict.conflict is not None and len(verdict.conflict) == 2


def test_name_identity_lives_in_one_place() -> None:
    """Že „Praha" ve dvou větách je týž uzel, je v otevřeném světě bez UNA
    ROZHODNUTÍ, ne samozřejmost. Drží ho jediná funkce, takže se dá vzít
    zpátky, až o tom někdo rozhodne jinak."""
    from core_semantics.cascade import Mention

    first = Mention(lemma="Praha", form="Prahy", token_index=1, upos="PROPN")
    second = Mention(lemma="Praha", form="Praze", token_index=9, upos="PROPN")
    assert name_of(first) == name_of(second)


def test_grounding_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("V3 — ZMÍNKA NA UZEL A SMĚROVÁNÍ TAHU (L‑5)")
    echo("=" * 72)
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    for label, oracle in (
        ("Filip má auto.", has_car()),
        ("Má Filip auto?", has_car("Má Filip auto?")),
    ):
        echo(f"\n» {label}")
        for line in session.utter(label, oracle).lines:
            echo(f"   {line}")
    echo("\n" + "=" * 72)


# --------------------------------------------------------------------------
# ZVRATNÉ ZÁJMENO neodkazuje ven z věty *(W‑68)*
# --------------------------------------------------------------------------


def _reflexive_reading(*, reflex: bool):  # type: ignore[no-untyped-def]
    from core_semantics.cascade import AWAITING_QUANTIFIER, Mention, RoleReading

    feats: tuple[tuple[str, str], ...] = (("Case", "Dat"), ("PronType", "Prs"))
    if reflex:
        feats = feats + (("Reflex", "Yes"),)
    return RoleReading(
        "Dat",
        Mention(lemma="se", form="si", token_index=3, upos="PRON", feats=feats),
        awaiting=AWAITING_QUANTIFIER,
    )


def test_a_reflexive_is_not_asked_about_as_an_anaphor() -> None:
    """„V prosinci 1938 **si** Karel Čapek přivodil chřipku." — `si` míří
    na podmět TÉŽE věty. Systém se přesto ptal „Na koho odkazuje?" a pak
    tu odpověď NEMĚL KAM PŘIJMOUT: role čeká na KVANTIFIKÁTOR, takže
    `→=` vrátí „role na odkaz nečeká".

    **Otázka, na kterou neexistuje tah, je horší než mlčení** — táž
    úvaha jako u prezentačního „to" (W‑29), jen tady doložená tím, že
    tah tu odpověď odmítá."""
    from core_semantics.grounding import _reflexive

    assert _reflexive(_reflexive_reading(reflex=True))


def test_a_plain_pronoun_is_still_asked_about() -> None:
    """PROTIPŘÍKLAD: bez `Reflex=Yes` je to obyčejné zájmeno a doptat se
    na ně je správné. Rozhoduje RYS Z ROZBORU, ne výčet tvarů („se",
    „si", „sebe") — ten by byl druhý slovník vedle parserova."""
    from core_semantics.grounding import _reflexive

    assert not _reflexive(_reflexive_reading(reflex=False))


def test_the_reflexive_sentence_asks_only_what_it_can_answer() -> None:
    """CELOU CESTOU: po opravě zbude JEN otázka na kvantifikátor — a ta
    tah má."""
    from core_semantics.cascade import generate
    from core_semantics.grounding import ground
    from core_semantics.storage import KnowledgeBase

    reading = Reading(
        tokens=(
            tok(1, "Jan", "Jan", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "si", "se", "PRON", 3, "obl", Case="Dat", PronType="Prs", Reflex="Yes"),
            tok(3, "přivodil", "přivodit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            tok(4, "chřipku", "chřipka", "NOUN", 3, "obj", Case="Acc", Gender="Fem", Number="Sing"),
            tok(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )
    grounded = ground(generate(reading)[0].predication, KnowledgeBase().view())
    assert "odkazuje mimo text" not in (grounded.question or "")
