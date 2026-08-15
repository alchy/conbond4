"""Zlaté transkripty — dodatek G, bod 6.

Sada jede přes **skutečný vstupní bod** `Session.utter`, ne přes `cascade`
volanou napřímo. To je poučení z kola #19: vrstva, kterou jde zavolat
cestou, kde nefunguje, má vadu v návrhu, ne jen v postupu. Kdyby test
sestavoval patra sám, prošel by i tehdy, kdyby si je `Session` nezapojila
— a přesně to se dělo do dneška.

Rozbor drží `RecordedOracle` pod jednou proveniencí a `CachingOracle` nad
ním ukazuje, že se fixace opravdu využívá.
"""

from __future__ import annotations

import pytest

from core_semantics.lexicon import Mood, czech_seed
from core_semantics.oracle import (
    CachingOracle,
    OracleError,
    Reading,
    RecordedOracle,
    Utterance,
)
from core_semantics.session import Session, TurnKind
from core_semantics.tests._console import echo
from core_semantics.tests.golden import (
    CORPUS,
    PROVENANCE,
    Golden,
    golden_lexicon,
    recordings,
)


def oracle() -> CachingOracle:
    return CachingOracle(RecordedOracle(recordings()))


@pytest.mark.parametrize("item", CORPUS, ids=lambda g: f"{g.dialogue}:{g.text}")
def test_golden_sentence_reads_as_recorded(item: Golden) -> None:
    session = Session(lexicon=golden_lexicon())
    result = session.utter(item.text, oracle())

    if item.refuses:
        assert result.predication is None, (
            f"{item.text!r} se dnes číst NEMÁ, a přesto vzniklo "
            f"{result.predication} — tichá volba měnící význam (I‑1)"
        )
        assert result.turn.kind is TurnKind.READING
        assert any("?" in line for line in result.lines), (
            "odmítnutí bez otázky je jen mlčení; doptání je plnohodnotná "
            "odpověď (I‑7)"
        )
    else:
        assert result.predication is not None, (
            f"{item.text!r} nebyla přečtena: {result.lines}"
        )
        assert str(result.predication) == item.predication
        # Otázka a její absence jsou obojí tvrzení o systému. Věta bez
        # `asks` se ptát NESMÍ — jinak by se doptání rozlezlo po sadě
        # a nikdo by si toho nevšiml.
        if item.asks:
            assert result.question is not None, (
                f"{item.text!r} se má ptát ({item.asks}), a neptá se"
            )
        else:
            assert result.question is None, (
                f"{item.text!r} se ptá, ačkoli sada tvrdí, že nemá: "
                f"{result.question}"
            )
            # L‑5: věta, na kterou se systém neptá, má DOJÍT AŽ NA KONEC.
            # Bez tohohle by šlo zakotvení vypnout a sada by zůstala
            # zelená — četla by se dál, jen by se nic nedělo.
            #
            # „Konec" je ale u každé nálady jiný: tvrzení se ZAPÍŠE,
            # otázka dostane VERDIKT a bázi nechá být (I‑12). Žádat zápis
            # i po otázce by znamenalo žádat, aby se ptaním měnila báze.
            if result.predication.mood is Mood.QUESTION:
                assert result.status is not None, (
                    f"{item.text!r} je otázka a nedostala verdikt: "
                    f"{result.lines}"
                )
                assert result.statement_id is None, (
                    f"{item.text!r} je otázka a přesto zapsala "
                    f"{result.statement_id}"
                )
            else:
                assert result.statement_id is not None, (
                    f"{item.text!r} se přečetla, nikdo se neptá, a přesto do "
                    f"báze nešlo nic: {result.lines}"
                )

    haystack = " ".join((*result.lines, *result.trace))
    for note in item.notes:
        assert note in haystack, (
            f"{item.text!r} má ve stopě chybět {note!r} — vysvětlení musí "
            f"vzniknout z toho, co se opravdu použilo (I‑14)"
        )


def test_whole_corpus_shares_one_provenance() -> None:
    """Zlatý transkript fixuje JEDEN rozbor.

    Dvě provenience v jedné sadě znamenají, že se část vět čte jedním
    modelem a část jiným — a pak není čím poznat, kdy se model změnil.
    """
    assert RecordedOracle(recordings()).provenance == PROVENANCE
    assert len({r.provenance for u in recordings().values() for r in u.readings}) == 1


def test_fixed_parse_is_actually_reused() -> None:
    """Keš klíčovaná proveniencí — jinak by fixace byla jen slib."""
    shared = oracle()
    for _ in range(2):
        for item in CORPUS:
            Session(lexicon=golden_lexicon()).utter(item.text, shared)
    assert shared.stored() == len(CORPUS)
    assert shared.misses == len(CORPUS)
    assert shared.hits == len(CORPUS)


def test_model_upgrade_does_not_hide_behind_the_cache() -> None:
    """Táž věta z jiného modelu se NESMÍ obsloužit starým záznamem.

    Tohle je celý důvod, proč je provenience součástí klíče: potichu
    povýšený model by jinak odpovídal rozborem, který už nikdo nedokáže
    zopakovat.
    """
    upgraded = {
        text: Utterance(
            text=text,
            readings=tuple(
                Reading(tokens=r.tokens, provenance="udpipe2 model=NOVÝ tokenizer=NOVÝ")
                for r in utterance.readings
            ),
        )
        for text, utterance in recordings().items()
    }
    cache = CachingOracle(RecordedOracle(recordings()))
    Session(lexicon=golden_lexicon()).utter(CORPUS[0].text, cache)
    assert cache.hits == 0 and cache.stored() == 1

    cache._inner = RecordedOracle(upgraded)  # simulace povýšení modelu
    Session(lexicon=golden_lexicon()).utter(CORPUS[0].text, cache)
    assert cache.hits == 0, "povýšený model se schoval za starý záznam"
    assert cache.stored() == 2


def test_recorded_oracle_refuses_unknown_sentence() -> None:
    """Zlatá sada nesmí tiše propadnout na síť — jinak přestane být zlatá."""
    with pytest.raises(OracleError):
        RecordedOracle(recordings()).parse("Tuhle větu nikdo nenahrál.")


def test_session_wires_the_learned_role_mappings() -> None:
    """`Session` si patra zapojuje sama.

    Bez tohohle testu by šlo `role_mapping_tier` smazat z `Session.tiers()`
    a zlatá sada by spadla až na jménu role — což vypadá jako chyba
    lexikonu, ne jako chybějící zapojení.
    """
    session = Session(lexicon=golden_lexicon())
    assert len(session.tiers()) == 10
    reading = session.utter("Auta jezdí po dálnici.", oracle())
    assert reading.predication is not None
    assert reading.predication.role("kudy") is not None
    assert reading.predication.role("po+Loc") is None


def test_golden_transcript_prints() -> None:
    """Transkript se vypisuje BEZ PODMÍNKY.

    Zlatá sada je dokument stejně jako test — text vět, rozbor a vybrané
    čtení mají být vidět, ne jen zeleně odškrtnuté.
    """
    session = Session(lexicon=golden_lexicon())
    shared = oracle()
    echo("\n" + "=" * 72)
    echo(f"ZLATÉ TRANSKRIPTY — dialogy A–F   [{PROVENANCE}]")
    echo("=" * 72)
    current = ""
    for item in CORPUS:
        if item.dialogue != current:
            current = item.dialogue
            echo(f"\n--- Dialog {current} " + "-" * 52)
        result = session.utter(item.text, shared)
        echo(f"\n» {item.text}")
        if item.point:
            echo(f"   ({item.point})")
        for line in result.lines:
            echo(f"   {line}")
        if item.asks:
            echo(f"   [PRÁVEM SE PTÁ] {item.asks}")
        if item.limit:
            echo(f"   [MEZ] {item.limit}")
    echo("\n" + "=" * 72)
    # Do žurnálu jde jen to, co se přečetlo. Věta, na kterou se systém
    # zeptal, není tah dialogu k přehrání — přehrávat „nevěděl jsem, jak
    # to číst" by znamenalo přehrávat mlčení.
    assert len(session.journal) == sum(1 for item in CORPUS if not item.refuses)
    assert all(turn.kind is TurnKind.READING for turn in session.journal)
