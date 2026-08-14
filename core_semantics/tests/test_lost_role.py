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

from core_semantics.cascade import (
    cascade,
    lost_members,
    lost_shape,
    role_question,
    surface_roles,
)
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


# --------------------------------------------------------------------------
# Povrchová role, kterou nikdo nepojmenoval — N‑3
# --------------------------------------------------------------------------
#
# `v`+Loc je „v Praze" (místo) i „v pondělí" (čas). Do N‑3 byly v seedu
# OBĚ hypotézy, takže patro hlásilo dvojznačnost — a to nešlo vyřešit
# nikdy: i po odpovědi člověka by kandidáti zůstali dva. Věta se
# nezakotvila, protože povrchová role neurčuje sort, a dialog Petrovice
# neprošel.
#
# Oprava je stejná jako u ztraceného členu, jen o tvar výš: v seedu není
# nic, systém se ZEPTÁ a odpověď tvar rozhodne. Doptání je tah dialogu,
# ne prohra — a stejný tah `→@`, protože obojí je `RoleMapping`.

LOC = "v+Loc"


def locative(who: str, upos: str = "PROPN") -> Reading:
    """«<X> bydlí v Petrovicích.»"""
    return Reading(
        tokens=(
            tok(1, who, who, upos, 2, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "bydlí", "bydlet", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
            tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            tok(4, "Petrovicích", "Petrovice", "PROPN", 2, "obl", Case="Loc", NameType="Geo", Number="Plur"),
            tok(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


RONIK = "Roník bydlí v Petrovicích."
MICKA = "Micka bydlí v Petrovicích."


def locative_oracle() -> _Recorded:
    return _Recorded({RONIK: locative("Roník"), MICKA: locative("Micka")})


def test_a_surface_role_without_a_meaning_is_asked_about() -> None:
    """Tvar bez významu je OTÁZKA, ne poznámka do stopy. Věta se stejně
    nezakotví — povrchová role neurčuje sort — takže mlčet by znamenalo
    nechat člověka hádat, co má doplnit."""
    session = Session()
    result = session.utter(RONIK, locative_oracle())
    assert result.question is not None
    assert LOC in result.question


def test_the_seed_does_not_decide_it_for_anyone() -> None:
    """Dvě hypotézy v seedu situaci NEŘEŠILY — mapování by zůstalo
    dvojznačné navždy. A jedna by byla horší: tichý default pro každého,
    kdo tu knihovnu použije."""
    assert not czech_seed().role_candidates(LOC)


def test_the_answer_completes_the_very_sentence_that_asked_about_the_role() -> None:
    session = Session()
    session.utter(RONIK, locative_oracle())
    answer = session.play(names_role("Je to místo.", locative("Roník"), LOC, "kde"))
    assert answer.predication is not None
    assert answer.predication.role("kde") is not None
    assert answer.predication.role(LOC) is None


def test_the_place_gets_its_sort_from_the_role_not_from_the_word() -> None:
    """§ 3.6: „Petrovice" je `Place`, protože `kde` je prostorová role —
    ne proto, že by si o Petrovicích někdo něco myslel."""
    session = Session()
    session.utter(RONIK, locative_oracle())
    answer = session.play(names_role("Je to místo.", locative("Roník"), LOC, "kde"))
    assert any("místo" in line for line in answer.lines)


def test_one_answer_closes_the_whole_class_of_shapes() -> None:
    session = Session()
    session.utter(RONIK, locative_oracle())
    session.play(names_role("Je to místo.", locative("Roník"), LOC, "kde"))

    again = session.utter(MICKA, locative_oracle())
    assert again.predication is not None
    assert again.predication.role("kde") is not None
    # Ptát se dál MŮŽE — na kvantifikátor podmětu, což je jiná otázka.
    # Test se proto ptá na TU SVOU: tvar `v+Loc` už význam má.
    assert role_question(again.predication) is None


def test_the_learned_meaning_of_a_shape_is_revocable() -> None:
    session = Session()
    session.utter(RONIK, locative_oracle())
    session.play(names_role("Je to místo.", locative("Roník"), LOC, "kde"))
    learned = [m for m in session.lexicon.all_roles() if m.surface == LOC]
    assert learned and "tah" in learned[0].learned_from

    session.lexicon.revoke_role(learned[0].key())
    revoked = session.utter(MICKA, locative_oracle())
    assert revoked.predication is not None
    assert role_question(revoked.predication) is not None


def test_a_canonical_role_is_not_asked_about() -> None:
    """Kontrola, že se neptá na všechno: `kdo` a `co` jméno mají a ptát se
    na ně by byl výslech, ve kterém by skutečná otázka zanikla. Jádrová
    jména relací (`elem`, `sub`, …) jsou kanonická ze stejného důvodu,
    jen ve slovníku jádra."""
    verdict = cascade(locative("Micka"))
    assert verdict.decided is not None
    assert surface_roles(verdict.decided.predication) == (LOC,)
    assert "kdo" not in (role_question(verdict.decided.predication) or "")
