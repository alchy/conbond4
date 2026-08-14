"""Hranice parseru — N‑4 (K‑7).

Otázka, kterou tenhle modul hlídá, zní: **kdy smí báze zasáhnout do
čtení?**

Do N‑4 platilo „když už podobný vztah zná". To ale není konzistence, to
je POPULARITA — a je to self‑confirming loop: báze dává přednost tomu,
co už jednou přečetla, čímž si své dřívější čtení potvrzuje. Čím víc se
systém splete stejným směrem, tím jistěji se splete znovu, a nikdy se to
neprojeví jako chyba, protože každý další krok „sedí".

Od K‑7 smí báze čtení eliminovat **jen z důvodu, který jde pojmenovat**:
typová chyba, formální konflikt, nesplnitelný constraint. „Tahle
interpretace se mi nehodí" mezi ně nepatří.

Píše se to teď, **před** přechodem na živou službu, schválně: dokud jedou
nahrané rozbory, je vstup chudý a smyčka se neprojeví. S živým parserem
by se projevila, a to už by bylo pozdě ji hledat.
"""

from __future__ import annotations

from core_semantics.ast import (
    Entity,
    Group,
    Quantifier,
    QueryStatus,
    atom,
    member_of,
    role,
)
from core_semantics.cascade import base_consistency_tier, generate
from core_semantics.engine import Engine
from core_semantics.grounding import semantic_rejection
from core_semantics.oracle import Reading, Token
from core_semantics.session import Session, says
from core_semantics.storage import KnowledgeBase
from core_semantics.tests._console import echo
from core_semantics.tests.test_grounding import (
    NOUN_OBJECT,
    PROPN_SUBJECT,
    _Recorded,
    shaped,
    tok,
)

STAMP = "test"


def reading(*tokens: Token) -> Reading:
    return Reading(tokens=tokens, provenance=STAMP)


#: „Vidí Petr Pavla?" — obě jména Sing i Nom, morfologie nerozhodne.
AMBIGUOUS = reading(
    tok(1, "Vidí", "vidět", "VERB", 0, "root", Number="Sing"),
    tok(2, "Petr", "Petr", "PROPN", 1, "nsubj", Case="Nom", Number="Sing"),
    tok(3, "Pavel", "Pavel", "PROPN", 1, "obj", Case="Nom", Number="Sing"),
)


def tier_over(kb: KnowledgeBase):  # type: ignore[no-untyped-def]
    return base_consistency_tier(semantic_rejection(Engine(kb)))


# --------------------------------------------------------------------------
# Co báze NESMÍ
# --------------------------------------------------------------------------


def test_familiarity_is_not_a_reason_to_eliminate_a_reading() -> None:
    """JÁDRO K‑7. Báze zná vztah `vidět` — a to nesmí stačit.

    Dřív by patro obě čtení nechala jen proto, že predikát v bázi je,
    a čtení s neznámým predikátem by vyhodila. Tím si systém utahoval
    smyčku kolem vlastních dřívějších rozhodnutí.
    """
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("r1"), Group("vidět")))
    survivors, why = tier_over(kb)(generate(AMBIGUOUS), AMBIGUOUS)
    assert len(survivors) == 2, "známost vztahu není sémantický důvod"
    assert why is None


def test_an_unknown_relation_is_not_penalised() -> None:
    """Druhá strana téže mince: o vztahu, který báze nezná, nelze říct,
    že je špatně. Neznalost není důvod."""
    survivors, why = tier_over(KnowledgeBase())(generate(AMBIGUOUS), AMBIGUOUS)
    assert len(survivors) == 2
    assert why is None


def test_an_ungroundable_reading_is_not_eliminated_either() -> None:
    """Čtení, které se nedá zakotvit, se neposuzuje.

    Chybějící kvantifikátor NENÍ rozpor — je to otevřená otázka. Vyhodit
    čtení za to, že se na ně systém ještě nezeptal, by byla táž tichá
    volba v jiném kabátě.
    """
    bare = reading(
        tok(1, "Učitelka", "učitelka", "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "učí", "učit", "VERB", 0, "root", Number="Sing"),
    )
    survivors, why = tier_over(KnowledgeBase())(generate(bare), bare)
    assert len(survivors) == len(generate(bare))
    assert why is None


# --------------------------------------------------------------------------
# Co báze SMÍ — a musí u toho říct proč
# --------------------------------------------------------------------------


def test_a_documented_denial_is_a_reason_and_it_is_named() -> None:
    """Doložené `p̄` je formální konflikt, tedy legitimní důvod — a patro
    ho musí POJMENOVAT, jinak by eliminace byla bez odůvodnění."""
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    denied = atom(
        "mít",
        role("kdo", Entity("Filip")),
        role("co", Group("auto"), Quantifier.EXISTS),
        negated=True,
    )
    session.kb.attach(denied)

    has_car = _Recorded(
        "Filip má auto.",
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )
    result = session.utter("Filip má auto.", has_car)
    assert any("v rozporu s bází" in step for step in result.trace), result.trace
    # Důvod je POJMENOVANÝ, ne jen ohlášený.
    assert any("doložené" in step for step in result.trace), result.trace


def test_a_contradictory_sentence_is_recorded_warned_about_and_not_arbitrated() -> None:
    """Rozporná věta se PŘEČTE, ZAPÍŠE a rozpor se OHLÁSÍ — v tomhle pořadí.

    Je to protějšek dialogu E a stojí to na jedné úvaze: člověk tu větu
    **řekl**. Odmítnout zápis by znamenalo odmítnout zaznamenat, co řekl,
    a systém by si tím vybral stranu sporu — mlčky a ve prospěch toho, kdo
    mluvil dřív. Správné chování je opačné: zaznamenat obojí s proveniencí,
    rozpor pojmenovat a rozhodnutí nechat na člověku (I‑3).

    Zapíchnuto celé, protože do N‑4 to nedržel žádný test a šlo by to
    změnit bez povšimnutí — a moje vlastní předávka o téhle větvi tvrdila
    opak toho, co kód dělá.
    """
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    positive = atom(
        "mít",
        role("kdo", Entity("Filip")),
        role("co", Group("auto"), Quantifier.EXISTS),
    )
    denial = session.play(says("Filip auto nemá.", positive.complement()))
    assert denial.statement_id is not None

    has_car = _Recorded(
        "Filip má auto.",
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )
    result = session.utter("Filip má auto.", has_car)

    assert result.predication is not None, "věta se má přečíst"
    assert any("v rozporu s bází" in step for step in result.trace), result.trace
    assert result.statement_id is not None, (
        "co člověk řekl, se zaznamenává; nezapsat by znamenalo vybrat "
        "stranu sporu mlčky"
    )

    verdict = Engine(session.kb).ask(positive)
    assert verdict.status is QueryStatus.CONFLICT
    assert verdict.conflict is not None and len(verdict.conflict) == 2, (
        "spor musí nést OBA důkazy — jinak by odpověď zamlčela jednu stranu"
    )
    leaves = {leaf for proof in verdict.conflict for leaf in proof.leaves()}
    assert {denial.statement_id, result.statement_id} <= leaves


def test_the_reason_travels_with_the_turn_so_replay_repeats_it() -> None:
    """Důvod eliminace je ve stopě, takže ho zopakuje i přehrání —
    stav, který replay z holého žurnálu nespočítá, není reprodukovatelný."""
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    # Premisa jde do báze TAHEM, ne obchvatem — jinak by ji replay neměl
    # odkud vzít a rozdíl by nebyl o důvodu, ale o mé přípravě testu.
    session.play(
        says(
            "Filip auto nemá.",
            atom(
                "mít",
                role("kdo", Entity("Filip")),
                role("co", Group("auto"), Quantifier.EXISTS),
                negated=True,
            ),
        )
    )
    has_car = _Recorded(
        "Filip má auto.",
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )
    session.utter("Filip má auto.", has_car)
    replayed = Session.replay(session.journal)
    assert replayed.answers() == session.answers()


def test_parser_boundary_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("HRANICE PARSERU — N‑4 (K‑7)")
    echo("=" * 72)
    echo("\nbáze smí čtení eliminovat JEN z pojmenovaného důvodu:")
    echo("  · typová chyba")
    echo("  · formální konflikt (doložené p̄)")
    echo("  · nesplnitelný constraint")
    echo("\na NESMÍ z toho, že vztah už zná — to je popularita, ne konzistence")

    kb = KnowledgeBase()
    kb.attach(member_of(Entity("r1"), Group("vidět")))
    survivors, why = tier_over(kb)(generate(AMBIGUOUS), AMBIGUOUS)
    echo("\n» „Vidí Petr Pavla?“ nad bází, která `vidět` zná")
    echo(f"   kandidátů po patru: {len(survivors)}   důvod: {why}")
    echo("=" * 72)
