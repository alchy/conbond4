"""Rozpor s bází čtení NEODSTRAŇUJE — A‑21 (dodatek O).

**Problém.** Patro konzistence vracelo jen ta čtení, která bázi
neodporovala; odporující mizela nenávratně. Syntakticky i typově platné
čtení bylo pryč, aniž se kdo zeptal.

**Proč je to vada, a ne opatrnost.** Jsou to dvě různá tvrzení:

> „tohle čtení neodpovídá tomu, co mám zapsané" ≠ „tohle čtení je špatně".

Rozdíl by nevadil, kdyby báze byla neomylná. Není — plní ji tytéž věty,
které se přes ni filtrují. Chybný fakt tedy umlčí správné čtení, to
chybu upevní, a **potichu**: z každého dalšího kroku bude vypadat, že
„sedí". Je to táž smyčka, kterou ruší K‑7, jen postavená na rozporu
místo na známosti.

**Změna.** Odporující čtení zůstává v sadě, klesne na konec a rozpor se
zapíše do stopy. Zbude‑li po zbytku kaskády víc kandidátů, systém se
**zeptá** — doptání je tah dialogu, ne prohra.

**Co se tím NEMĚNÍ.** Věta, jejíž VŠECHNA čtení bázi odporují, se dál
přečte, zapíše a rozpor se ohlásí (I‑3): klesnout na konec není proti
komu. A tvrdě odmítat smí dál typová chyba, protože ta je o TVARU čtení,
ne o obsahu báze.
"""

from __future__ import annotations

from core_semantics.ast import (
    Entity,
    Group,
    Quantifier,
    QueryStatus,
    atom,
    role,
)
from core_semantics.cascade import (
    Candidate,
    Predication,
    Rejection,
    RejectionKind,
    base_consistency_tier,
    generate,
    quantifier_tier,
    role_mapping_tier,
)
from core_semantics.engine import Engine
from core_semantics.grounding import semantic_rejection
from core_semantics.lexicon import Lexicon, Operation
from core_semantics.oracle import Utterance
from core_semantics.session import Session, says
from core_semantics.storage import KnowledgeBase
from core_semantics.tests.test_grounding import (
    NOUN_OBJECT,
    PROPN_SUBJECT,
    _Recorded,
    shaped,
    tok,
)
from core_semantics.tests.test_parser_boundary import AMBIGUOUS, tier_over

#: „Vidí Petr Pavla?" — obě jména Sing i Nom, morfologie nerozhodne, takže
#: k patru konzistence dojdou DVĚ čtení. To je celý smysl fixtury: kde
#: zbývá jedno, není co upřednostňovat.
PROPN_OBJECT = ("PROPN", "Sing", "Nom", "obj", Operation.SELF)


def _lexicon() -> Lexicon:
    return shaped(PROPN_SUBJECT, PROPN_OBJECT)


def _denied_direction() -> KnowledgeBase:
    """Báze s doloženým `¬vidět(Petr → Pavel)`. Jedno ze dvou čtení tedy
    odporuje, druhé ne."""
    kb = KnowledgeBase()
    kb.attach(
        atom(
            "vidět",
            role("kdo", Entity("Petr")),
            role("co", Entity("Pavel")),
            negated=True,
        )
    )
    return kb


def _ready() -> tuple[Candidate, ...]:
    """Kandidáti tak, jak dojdou k poslednímu patru — po přejmenování rolí
    a kvantifikátoru, protože bez nich se čtení nezakotví a patro nemá co
    posuzovat."""
    lexicon = _lexicon()
    candidates = generate(AMBIGUOUS)
    candidates, _ = role_mapping_tier(lexicon)(candidates, AMBIGUOUS)
    candidates, _ = quantifier_tier(lexicon)(candidates, AMBIGUOUS)
    return candidates


class _Ambiguous:
    """Orákulum, které vrací jediný rozbor se dvěma čteními."""

    provenance = "test"

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(AMBIGUOUS,))


# --------------------------------------------------------------------------
# Jádro A‑21
# --------------------------------------------------------------------------


def test_a_contradicting_reading_is_kept_not_dropped() -> None:
    """JÁDRO. Dřív zbylo jedno čtení a druhé bylo nenávratně pryč."""
    survivors, why = tier_over(_denied_direction())(_ready(), AMBIGUOUS)
    assert len(survivors) == 2, "odporující čtení se NEODSTRAŇUJE"
    assert why is not None and "rozpor s bází" in why


def test_the_contradicting_reading_drops_to_the_back() -> None:
    """Priorita je skutečná, ne jen slovo ve stopě: čisté čtení jde
    dopředu, odporující dozadu."""
    survivors, _ = tier_over(_denied_direction())(_ready(), AMBIGUOUS)
    rendered = [str(c.predication) for c in survivors]
    assert rendered[0] == "vidět(co:·Petr, kdo:·Pavel)"
    assert rendered[1] == "vidět(co:·Pavel, kdo:·Petr)"


def test_the_trace_says_it_was_demoted_and_not_removed() -> None:
    """Stopa je jediný zdroj vysvětlení (I‑14). Kdyby psala „PROČ", četlo
    by se to jako rozhodnutí patra — jenže patro nerozhodlo, jen seřadilo."""
    _, why = tier_over(_denied_direction())(_ready(), AMBIGUOUS)
    assert why is not None
    assert "NEODSTRAŇUJE" in why
    assert "doložené" in why, "důvod musí zůstat POJMENOVANÝ (K‑7)"


def test_the_reason_stays_named_even_though_nothing_is_dropped() -> None:
    """Eliminace bez důvodu byla vada; snížení priority bez důvodu by byla
    táž vada tišeji."""
    _, why = tier_over(_denied_direction())(_ready(), AMBIGUOUS)
    assert why is not None and "vidět(co:Pavel, kdo:Petr)" in why


# --------------------------------------------------------------------------
# Konec kaskády: ptát se, ne vybrat
# --------------------------------------------------------------------------


def test_the_sentence_asks_instead_of_choosing_silently() -> None:
    """OČEKÁVANÝ VÝSLEDEK A‑21. Dřív systém tiše vybral druhé čtení a
    tvářil se rozhodnutě."""
    session = Session(lexicon=_lexicon())
    session.kb.attach(
        atom(
            "vidět",
            role("kdo", Entity("Petr")),
            role("co", Entity("Pavel")),
            negated=True,
        )
    )
    result = session.utter("Vidí Petr Pavla?", _Ambiguous())
    assert result.question is not None, "systém se MÁ zeptat"
    assert "vidět(co:·Pavel, kdo:·Petr)" in result.question, (
        "v nabídce musí být i to čtení, které bázi odporuje — jinak by "
        "se otázka jen ptala na to, co už systém vybral"
    )


def test_nothing_is_written_while_the_reading_is_undecided() -> None:
    """Zeptat se a přitom zapsat by byla ta tichá volba znovu, jen
    s otazníkem navrch."""
    session = Session(lexicon=_lexicon())
    session.kb.attach(
        atom(
            "vidět",
            role("kdo", Entity("Petr")),
            role("co", Entity("Pavel")),
            negated=True,
        )
    )
    before = session.program()
    result = session.utter("Vidí Petr Pavla?", _Ambiguous())
    assert result.statement_id is None
    assert session.program() == before, "báze se nerozhodnutým čtením nemění"


def test_without_the_denial_the_sentence_is_equally_undecided() -> None:
    """Kontrola, že se neměří něco jiného: dvojznačnost tu byla i BEZ
    báze. A‑21 nepřidala otázku — zabránila tomu, aby ji báze umlčela."""
    session = Session(lexicon=_lexicon())
    result = session.utter("Vidí Petr Pavla?", _Ambiguous())
    assert result.question is not None
    assert result.statement_id is None


# --------------------------------------------------------------------------
# COUNTEREXAMPLE: co se změnit NESMÍ
# --------------------------------------------------------------------------


def test_a_wholly_contradictory_sentence_is_still_written() -> None:
    """PROTIPŘÍKLAD REVIEWERA. Když bázi odporují VŠECHNA čtení, věta se
    dál přečte, ZAPÍŠE a rozpor se ohlásí (I‑3).

    Klesnout na konec tu není proti komu, takže přeuspořádání nesmí tenhle
    případ proměnit v doptání. Odmítnout zápis by znamenalo vybrat stranu
    sporu mlčky, ve prospěch toho, kdo mluvil dřív."""
    session = Session(lexicon=shaped(PROPN_SUBJECT, NOUN_OBJECT))
    positive = atom(
        "mít",
        role("kdo", Entity("Filip")),
        role("co", Group("auto"), Quantifier.EXISTS),
    )
    session.play(says("Filip auto nemá.", positive.complement()))

    has_car = _Recorded(
        "Filip má auto.",
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )
    result = session.utter("Filip má auto.", has_car)

    assert result.predication is not None, "věta se má přečíst"
    assert result.statement_id is not None, "a zapsat"
    assert result.question is None, "a NEptat se — není mezi čím vybírat"
    assert any("v rozporu s bází" in step for step in result.trace)

    verdict = Engine(session.kb).ask(positive)
    assert verdict.status is QueryStatus.CONFLICT
    assert verdict.conflict is not None and len(verdict.conflict) == 2


# --------------------------------------------------------------------------
# Tvrdě odmítat smí jen typová chyba
# --------------------------------------------------------------------------


def test_only_a_sort_error_is_hard() -> None:
    """Hranice je v TYPU, ne v české větě. Kdyby si patro sílu důvodu
    četlo z textu hlášky, byla by to heuristika přesně tam, kde patří
    typ — a příští překlad hlášky by ji tiše otočil."""
    assert Rejection(RejectionKind.SORT, "…").hard
    assert not Rejection(RejectionKind.CONTRADICTED, "…").hard


def test_a_mistyped_reading_is_still_removed() -> None:
    """Z typově vadného čtení žádná formule nevznikne, takže není co
    upřednostňovat a nač se ptát. Ponechat ho „pro jistotu" by znamenalo
    ptát se člověka na možnost, která neexistuje."""
    ready = _ready()
    bad = str(ready[0].predication)

    def only_the_first_is_mistyped(predication: Predication) -> Rejection | None:
        if str(predication) == bad:
            return Rejection(RejectionKind.SORT, "typová chyba: sort role")
        return None

    survivors, why = base_consistency_tier(only_the_first_is_mistyped)(
        ready, AMBIGUOUS
    )
    assert len(survivors) == len(ready) - 1
    assert all(str(c.predication) != bad for c in survivors)
    assert why is not None and "typová chyba" in why


def test_the_base_classifies_its_own_two_reasons_as_soft() -> None:
    """Doklad, že se rozdělení netýká jen typu, ale i toho, CO do něj
    `semantic_rejection` doopravdy posílá: doložené popření je měkké."""
    reject = semantic_rejection(Engine(_denied_direction()))
    reasons = [reject(c.predication) for c in _ready()]
    named = [r for r in reasons if r is not None]
    assert named, "aspoň jedno čtení musí být odmítnuté, jinak test neměří nic"
    assert all(r.kind is RejectionKind.CONTRADICTED for r in named)
    assert not any(r.hard for r in named)


# --------------------------------------------------------------------------
# Přepis
# --------------------------------------------------------------------------


def test_hard_pruning_transcript_prints() -> None:
    from core_semantics.tests._console import echo

    echo("\n" + "=" * 72)
    echo("ROZPOR S BÁZÍ ČTENÍ NEODSTRAŇUJE — A‑21")
    echo("=" * 72)
    echo("báze:  ¬vidět(kdo:Petr, co:Pavel)   ← doložené popření")
    echo("věta:  „Vidí Petr Pavla?“   obě jména Nom, morfologie nerozhodne")
    echo("")
    session = Session(lexicon=_lexicon())
    session.kb.attach(
        atom(
            "vidět",
            role("kdo", Entity("Petr")),
            role("co", Entity("Pavel")),
            negated=True,
        )
    )
    for line in session.utter("Vidí Petr Pavla?", _Ambiguous()).lines:
        echo(f"   {line}")
    echo("")
    echo("Dřív: odporující čtení zmizelo a systém tiše odpověděl to druhé.")
    echo("Chybný fakt v bázi tak umlčel správnou větu — a potichu.")
    echo("=" * 72)
