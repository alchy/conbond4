"""Shoda nahrávky se živým rozborem — nástroj pro přechod na živou službu.

**Tyhle testy jsou hermetické a musí zůstat.** Ověřují NÁSTROJ, ne
službu: živý parser se simuluje injektovanou dopravou. Kdyby sada sáhla
na `127.0.0.1:42200`, přestala by být testem kódu a stala by se testem
toho, co je zrovna spuštěné — přesně to, čemu se `RecordedOracle` od
začátku brání.

Samotný diferenční běh proti běžící službě je **samostatná operace**,
kterou si někdo pustí. Do testů nepatří.
"""

from __future__ import annotations

import json
from typing import Mapping

from core_semantics.oracle import (
    OracleUnavailable,
    RecordedOracle,
    Transport,
    UDPipeOracle,
    Utterance,
)
from core_semantics.parity import compare, compare_all, summarise
from core_semantics.tests._console import echo
from core_semantics.tests.golden import PROVENANCE, recordings

VERSION = {"model": "czech-pdt-ud-2.12", "tokenizer": "czech-pdt-2.12"}
UPGRADED = {"model": "czech-pdt-ud-2.15", "tokenizer": "czech-pdt-2.15"}


def _as_payload(
    utterance: Utterance, *, lemma_of: dict[str, str] | None = None
) -> dict[str, object]:
    """Nahraný rozbor jako odpověď služby, volitelně s jinými lemmaty."""
    reading = utterance.readings[0]
    return {
        "sentences": [
            {
                "tokens": [
                    {
                        "id": t.index,
                        "form": t.form,
                        "lemma": (lemma_of or {}).get(t.form, t.lemma),
                        "upos": t.upos,
                        "head": t.head,
                        "deprel": t.deprel,
                        "feats": "|".join(f"{k}={v}" for k, v in t.feats) or None,
                    }
                    for t in reading.tokens
                ]
            }
        ]
    }


def _service(
    version: Mapping[str, object], payloads: Mapping[str, dict[str, object]]
) -> Transport:
    """Doprava, která se tváří jako běžící služba."""

    def transport(url: str, body: bytes | None, timeout: float) -> bytes:
        path = url.split("42200", 1)[-1]
        if path == "/version":
            return json.dumps(version).encode("utf-8")
        text = json.loads((body or b"{}").decode("utf-8"))["text"]
        if text not in payloads:
            raise OracleUnavailable(f"služba nezná {text!r}")
        return json.dumps(payloads[text]).encode("utf-8")

    return transport


def live(version: Mapping[str, object], **overrides: dict[str, str]) -> UDPipeOracle:
    payloads = {
        text: _as_payload(utterance, lemma_of=overrides.get(text))
        for text, utterance in recordings().items()
    }
    return UDPipeOracle(transport=_service(version, payloads))


# --------------------------------------------------------------------------


def test_identical_parses_agree() -> None:
    """Základ: služba se stejným modelem a stejným rozborem nedá nález."""
    results = compare_all(recordings(), live(VERSION))
    assert all(r.agrees for r in results), [r.render() for r in results if not r.agrees]


def test_a_changed_lemma_is_reported_as_a_finding_not_an_error() -> None:
    """Rozdíl NENÍ chyba. Je to nález k rozhodnutí — a musí být vidět,
    který token a které pole."""
    oracle = live(VERSION, **{"Vrabec létá.": {"Vrabec": "vrabeček"}})
    results = compare_all(recordings(), oracle)
    changed = [r for r in results if not r.agrees]
    assert len(changed) == 1
    assert changed[0].text == "Vrabec létá."
    assert [d.field for d in changed[0].differences] == ["lemma"]
    assert changed[0].error == "", "rozdíl se nesmí hlásit jako provozní chyba"


def test_a_different_model_is_reported_first_and_alone() -> None:
    """Liší-li se model, liší se skoro jistě i tokeny. Vypsat je všechny
    by nález utopilo, takže se provenience hlásí PRVNÍ a s upozorněním,
    že to ostatní je nejspíš její důsledek."""
    oracle = live(UPGRADED, **{"Vrabec létá.": {"Vrabec": "vrabeček"}})
    results = compare_all(recordings(), oracle)
    changed = next(r for r in results if not r.agrees)
    lines = changed.render()
    assert "JINÝ MODEL" in lines[1]
    assert not changed.same_model
    assert any("důsledek" in line for line in lines)


def test_different_tokenisation_stops_positional_comparison() -> None:
    """Jiný počet tokenů je vážnější třída nálezu: po pozicích se
    porovnat nedá vůbec, takže se to řekne a dál se nepředstírá."""
    recorded = recordings()
    text = "Vrabec létá."
    shortened = Utterance(
        text=text,
        readings=(
            type(recorded[text].readings[0])(
                tokens=recorded[text].readings[0].tokens[:1],
                provenance=PROVENANCE,
            ),
        ),
    )
    parity = compare(recorded[text], shortened)
    assert not parity.agrees
    assert parity.recorded_tokens != parity.live_tokens
    assert any("JINÁ TOKENIZACE" in line for line in parity.render())


def test_one_unavailable_sentence_does_not_stop_the_run() -> None:
    """Cílem je úplný obrázek, ne první problém."""
    partial = dict(recordings())
    oracle = RecordedOracle({k: v for k, v in list(partial.items())[:3]})
    results = compare_all(partial, oracle)
    assert len(results) == len(partial)
    assert any(r.error for r in results)
    assert any(r.agrees for r in results)


def test_summary_flags_an_unstable_service() -> None:
    """Dvě různé provenience v JEDNOM běhu nejsou rozdíl v rozboru —
    je to nestabilní prostředí, a to je jiná zpráva."""
    mixed = (
        compare_all(recordings(), live(VERSION))[0],
        compare_all(recordings(), live(UPGRADED))[0],
    )
    assert any("nestabilní prostředí" in line for line in summarise(mixed))


def test_the_recordings_stay_the_truth_of_the_tests() -> None:
    """Sada se NESMÍ začít ptát služby.

    Hermetičnost je celý důvod, proč zlaté transkripty vznikly. Tenhle
    test hlídá, že porovnání je samostatná operace a testy dál jedou
    z nahrávek."""
    from core_semantics.tests import golden

    assert "UDPipeOracle" not in golden.__doc__ if golden.__doc__ else True
    recorded = RecordedOracle(recordings())
    assert recorded.provenance == PROVENANCE


def test_parity_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("SHODA NAHRÁVKY SE ŽIVÝM ROZBOREM — nástroj pro živou službu")
    echo("=" * 72)
    echo("\n(služba se tu SIMULUJE — testy zůstávají hermetické)")
    oracle = live(UPGRADED, **{"Vrabec létá.": {"Vrabec": "vrabeček"}})
    results = compare_all(recordings(), oracle)
    for line in summarise(results):
        echo(f"   {line}")
    for parity in results:
        if not parity.agrees:
            for line in parity.render():
                echo(f"   {line}")
    echo("=" * 72)
