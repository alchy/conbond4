"""Vnější orákulum (§ 5.1) — klient, nahrané rozbory, keš.

Testy jsou **hermetické**: doprava se injektuje, takže žádný z nich
nepotřebuje běžící službu ani síť. To je záměr, ne pohodlí — test, který
si nepozorovaně sáhne na `127.0.0.1:42200`, přestane být testem kódu
a stane se testem toho, co je zrovna spuštěné.
"""

from __future__ import annotations

import json
from typing import Mapping

import pytest

from core_semantics.oracle import (
    CachingOracle,
    OracleError,
    OracleUnavailable,
    Reading,
    SegmentationError,
    Token,
    Transport,
    UDPipeOracle,
    Utterance,
    parse_feats,
    recorded,
    RecordedOracle,
)

VERSION: dict[str, object] = {
    "model": "czech-pdt-ud-2.12",
    "tokenizer": "2.12.1",
}
UPGRADED: dict[str, object] = {
    "model": "czech-pdt-ud-2.15",
    "tokenizer": "2.15.0",
}
STAMP = "udpipe2 model=czech-pdt-ud-2.12 tokenizer=2.12.1"

SENTENCE: dict[str, object] = {
    "sentences": [
        {
            "source": "Citron je ovoce.",
            "tokens": [
                {
                    "id": 1,
                    "form": "Citron",
                    "lemma": "citron",
                    "upos": "NOUN",
                    "feats": "Gender=Masc|Number=Sing|Case=Nom",
                    "head": 3,
                    "deprel": "nsubj",
                },
                {
                    "id": 2,
                    "form": "je",
                    "lemma": "být",
                    "upos": "AUX",
                    "feats": "Number=Sing|Person=3",
                    "head": 3,
                    "deprel": "cop",
                },
                {
                    "id": 3,
                    "form": "ovoce",
                    "lemma": "ovoce",
                    "upos": "NOUN",
                    "feats": "Case=Nom|Number=Sing",
                    "head": 0,
                    "deprel": "root",
                },
            ],
        }
    ]
}


def _sentence(word: str, punct: str = ".") -> dict[str, object]:
    return {
        "tokens": [
            {
                "id": 1,
                "form": word,
                "lemma": word.lower(),
                "upos": "NOUN",
                "head": 0,
                "deprel": "root",
            },
            {
                "id": 2,
                "form": punct,
                "lemma": punct,
                "upos": "PUNCT",
                "head": 1,
                "deprel": "punct",
            },
        ]
    }


TWO_SENTENCES: dict[str, object] = {
    "sentences": [_sentence("Praha"), _sentence("Brno", "?")]
}


def _transport(script: Mapping[str, Mapping[str, object]]) -> Transport:
    calls: list[str] = []

    def transport(url: str, body: bytes | None, timeout: float) -> bytes:
        path = url.split("42200", 1)[-1] if "42200" in url else url
        calls.append(path)
        if path not in script:
            raise OracleUnavailable(f"neočekávaná cesta {path}")
        return json.dumps(script[path]).encode("utf-8")

    transport.calls = calls  # type: ignore[attr-defined]
    return transport


# --------------------------------------------------------------------------
# Tvar rozboru
# --------------------------------------------------------------------------


def test_feats_are_sorted_for_determinism() -> None:
    """Pořadí rysů ve výstupu modelu není smluvně dané; zlatý transkript
    na něm nesmí viset (I‑4)."""
    assert parse_feats("Number=Sing|Case=Nom") == (
        ("Case", "Nom"),
        ("Number", "Sing"),
    )
    assert parse_feats("_") == ()
    assert parse_feats(None) == ()


def test_reading_exposes_the_dependency_tree() -> None:
    oracle = UDPipeOracle(transport=_transport({"/version": VERSION, "/v1/parse": SENTENCE}))
    utterance = oracle.parse("Citron je ovoce.")
    reading = utterance.unambiguous
    assert reading is not None
    root = reading.root()
    assert root is not None and root.lemma == "ovoce"
    assert [t.lemma for t in reading.children(3)] == ["citron", "být"]
    assert reading.by_deprel("nsubj")[0].feat("Case") == "Nom"


# --------------------------------------------------------------------------
# Kandidátní čtení, ne jeden strom
# --------------------------------------------------------------------------


def test_readings_are_plural_from_the_start() -> None:
    """§ 5.1: výstupem NENÍ jeden strom. Dnešní orákulum vrací jedno čtení,
    ale typ o tom nesmí lhát — kaskáda § 5.2 bude potřebovat víc."""
    utterance = Utterance(text="x", readings=())
    assert utterance.unambiguous is None
    two = Utterance(
        text="x",
        readings=(
            Reading(tokens=(), provenance=STAMP),
            Reading(tokens=(), provenance=STAMP),
        ),
    )
    assert two.unambiguous is None  # nejednoznačné se nevydává za jisté


# --------------------------------------------------------------------------
# Klient
# --------------------------------------------------------------------------


def test_client_fails_at_construction_not_at_first_call() -> None:
    """Klient nad neběžící službou je tikající chyba — ukázala by se
    uprostřed dialogu, s polovinou tahů už zapsaných."""
    with pytest.raises(OracleUnavailable):
        UDPipeOracle(transport=_transport({}))


def test_provenance_carries_model_and_tokenizer() -> None:
    oracle = UDPipeOracle(transport=_transport({"/version": VERSION, "/v1/parse": SENTENCE}))
    assert oracle.provenance == STAMP
    reading = oracle.parse("Citron je ovoce.").readings[0]
    assert reading.provenance == STAMP


def test_unreadable_response_is_an_error_not_a_guess() -> None:
    def broken(url: str, body: bytes | None, timeout: float) -> bytes:
        return b"{ tohle neni json"

    with pytest.raises(OracleError):
        UDPipeOracle(transport=broken)


# --------------------------------------------------------------------------
# Nahrané rozbory a keš
# --------------------------------------------------------------------------


def test_feats_survive_both_shapes_the_service_speaks() -> None:
    """N‑6, nález z prvního běhu proti ŽIVÉ službě.

    CoNLL‑U posílá rysy jako řetězec, JSON API jako objekt. Klient uměl
    jen ten první a druhý si přetypoval přes `str(dict)` — takže
    `"{'Case': 'Nom'}"` neobsahovalo ani jeden pár a **všechny rysy se
    tiše zahodily**. Bez `Number` nefunguje shoda čísla, bez `Case`
    pádová mřížka, bez `Polarity` zápor: celá morfologická vrstva byla
    mrtvá a nic to neohlásilo.
    """
    from_string = parse_feats("Case=Nom|Number=Sing")
    from_object = parse_feats({"Number": "Sing", "Case": "Nom"})
    assert from_string == from_object == (("Case", "Nom"), ("Number", "Sing"))


def test_unreadable_feats_are_loud_because_empty_ones_are_legitimate() -> None:
    """Prázdné rysy jsou platná hodnota — interpunkce opravdu žádné nemá.

    Právě proto se neznámý tvar NESMÍ tiše zredukovat na prázdno: vypadal
    by jako slovo bez morfologie a tvrdá patra by mlčky přestala platit.
    """
    assert parse_feats(None) == ()
    assert parse_feats("_") == ()
    assert parse_feats({}) == ()
    with pytest.raises(OracleError):
        parse_feats("{'Case': 'Nom'}")  # přetypovaný slovník, ne CoNLL-U
    with pytest.raises(OracleError):
        parse_feats(["Case=Nom"])


def test_two_sentences_are_a_segmentation_error_not_two_readings() -> None:
    """Rozhodnutí L‑1. Dřív se druhá věta vydávala za druhé kandidátní
    čtení téže promluvy, takže se systém ptal „které z toho?" na dvě různé
    věty. Nerozdělený text není dvojznačnost."""
    client = UDPipeOracle(
        transport=_transport({"/version": VERSION, "/v1/parse": TWO_SENTENCES})
    )
    with pytest.raises(SegmentationError) as caught:
        client.parse("Praha. Brno?")
    assert "2 vět" in str(caught.value)
    assert "segment()" in str(caught.value)


def test_segmentation_error_is_told_apart_from_the_other_two_failures() -> None:
    """Tři různé situace, tři různé typy: služba mimo, větu neumím
    přečíst, tohle nebyla věta. Poslední umí volající opravit sám."""
    assert issubclass(SegmentationError, OracleError)
    assert not issubclass(SegmentationError, OracleUnavailable)
    assert not issubclass(OracleUnavailable, SegmentationError)


def test_segment_is_a_separate_operation() -> None:
    """Rozdělení textu je vlastní operace, ne vedlejší účinek rozboru."""
    client = UDPipeOracle(
        transport=_transport({"/version": VERSION, "/v1/parse": TWO_SENTENCES})
    )
    parts = client.segment("Praha. Brno?")
    assert [u.text for u in parts] == ["Praha.", "Brno?"]
    assert all(len(u.readings) == 1 for u in parts), (
        "každá věta si nese vlastní rozbor; skládat text zpátky z tvarů "
        "a posílat ho modelu podruhé by mohlo dát jiný strom"
    )
    assert all(u.readings[0].provenance == client.provenance for u in parts)


def test_single_sentence_still_parses_normally() -> None:
    client = UDPipeOracle(
        transport=_transport({"/version": VERSION, "/v1/parse": SENTENCE})
    )
    assert len(client.parse("Citron je ovoce.").readings) == 1


def test_recorded_oracle_refuses_unknown_text() -> None:
    """Hermetický test se nesmí tiše propadnout na síť."""
    oracle = RecordedOracle(
        {"Citron je ovoce.": recorded("Citron je ovoce.", (), provenance=STAMP)}
    )
    assert oracle.parse("Citron je ovoce.").text == "Citron je ovoce."
    with pytest.raises(OracleError, match="nahraný rozbor"):
        oracle.parse("Pomeranč je ovoce.")


def test_cache_hits_on_the_recorded_path() -> None:
    """B‑7: právě tahle cesta je ta, kvůli které keš vznikla.

    Zlaté transkripty a hermetické testy jedou přes `RecordedOracle`.
    Dřív se klíč zápisu bral z provenience ČTENÍ a klíč čtení z objektu
    orákula; `RecordedOracle` atribut neměl, takže keš na téhle cestě
    NIKDY netrefila a jen rostla — a přitom mlčela.
    """
    utterance = recorded("Citron je ovoce.", (), provenance=STAMP)
    cache = CachingOracle(RecordedOracle({"Citron je ovoce.": utterance}))
    cache.parse("Citron je ovoce.")
    cache.parse("Citron je ovoce.")
    assert (cache.hits, cache.misses) == (1, 1)


def test_cache_is_keyed_by_provenance_too() -> None:
    """Kdyby klíč nesl jen text, upgrade modelu by se schoval za starý
    záznam a systém by odpovídal podle rozboru, který nikdo nezopakuje."""
    inner = UDPipeOracle(
        transport=_transport({"/version": VERSION, "/v1/parse": SENTENCE})
    )
    cache = CachingOracle(inner)
    cache.parse("Citron je ovoce.")
    cache.parse("Citron je ovoce.")
    assert (cache.hits, cache.misses) == (1, 1)

    upgraded = UDPipeOracle(
        transport=_transport({"/version": UPGRADED, "/v1/parse": SENTENCE})
    )
    cache._inner = upgraded  # simulace upgradu pod keší
    cache.parse("Citron je ovoce.")
    assert cache.misses == 2  # jiná provenience ⇒ nový rozbor, ne starý záznam


def test_cache_never_stores_a_failure() -> None:
    """Prázdný výsledek může být i důsledek přechodné poruchy; trvale
    zapamatované „neumím přečíst" by systém udrželo tvrdošíjně vedle."""
    silent: dict[str, object] = {"sentences": []}
    cache = CachingOracle(
        UDPipeOracle(transport=_transport({"/version": VERSION, "/v1/parse": silent}))
    )
    cache.parse("Ňuňu ňuňu.")
    cache.parse("Ňuňu ňuňu.")
    assert (cache.hits, cache.misses) == (0, 2)
    assert cache.stored() == 0


def test_cache_stays_out_of_the_way_without_provenance() -> None:
    """Pod „nevím" by se slily rozbory z různých modelů."""
    anonymous = RecordedOracle(
        {"x": Utterance(text="x", readings=(Reading(tokens=(), provenance=""),))}
    )
    cache = CachingOracle(anonymous)
    cache.parse("x")
    cache.parse("x")
    assert cache.provenance == ""
    assert (cache.hits, cache.misses) == (0, 2)
    assert cache.stored() == 0


def test_recorded_oracle_refuses_mixed_provenances() -> None:
    """Zlatý transkript musí fixovat JEDEN rozbor — jinak není čím poznat,
    že se model změnil."""
    with pytest.raises(OracleError, match="provenience"):
        RecordedOracle(
            {
                "a": recorded("a", (), provenance=STAMP),
                "b": recorded("b", (), provenance="udpipe2 model=jiny"),
            }
        )


def test_service_failure_and_unreadable_sentence_are_different_signals() -> None:
    """Neběžící parser NENÍ „nerozumím větě".

    První je provozní chyba a patří na ni jiná hláška; druhé je poctivé
    „tuhle větu neumím přečíst" a vede na doptání. Splynutí by bylo tiché
    selhání vrstvy (I‑1), proto to jsou dva různé signály: výjimka proti
    prázdné n-tici čtení.
    """
    # (a) provozní chyba — výjimka, ne prázdný výsledek
    with pytest.raises(OracleUnavailable):
        UDPipeOracle(transport=_transport({}))

    # (b) služba běží, ale větu nerozebrala — prázdná čtení, žádná výjimka
    silent: dict[str, object] = {"sentences": []}
    oracle = UDPipeOracle(
        transport=_transport({"/version": VERSION, "/v1/parse": silent})
    )
    utterance = oracle.parse("Ňuňu ňuňu.")
    assert utterance.readings == ()
    assert utterance.unambiguous is None


def test_token_renders_as_conllu_like_line() -> None:
    token = Token(
        index=1,
        form="Citron",
        lemma="citron",
        upos="NOUN",
        head=3,
        deprel="nsubj",
        feats=(("Case", "Nom"),),
    )
    assert str(token).split("\t")[:4] == ["1", "Citron", "citron", "NOUN"]
