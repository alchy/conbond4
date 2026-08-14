"""Diferenční běh proti ŽIVÉ službě `cb-udpipe`.

```
python -m core_semantics.live_check
```

**Není to test.** Testy jsou hermetické a musí zůstat; tohle je operace,
kterou si někdo pustí, když služba běží, aby zjistil, jestli to, co
držíme na nahrávkách, drží i na skutečném parseru.

Výstup má tři možné podoby a každá znamená něco jiného:

* **shoda** — nahrávky odpovídají živému rozboru; zlatá sada měří to, co
  si myslí, že měří;
* **rozdíl** — NÁLEZ k rozhodnutí, ne chyba. Buď se změnil model (pak to
  řekne provenience a keš starý záznam správně odmítne), nebo čte parser
  jinak, než jsme si mysleli, když jsme rozbor psali rukou;
* **služba neběží** — provozní stav, ne verdikt o kódu. Vypíše se to
  jako takový a skončí nenulovým kódem, aby se to nedalo přehlédnout
  v pipeline.

Rozdíl se **nezanáší do sady automaticky**. Co s ním, je rozhodnutí
člověka: buď se přepíše nahrávka (vědomě, s viditelným diffem CoNLL‑U),
nebo se zapíše jako mez. Automatická aktualizace by ze zlaté sady
udělala zrcadlo služby a přestala by cokoli hlídat.
"""

from __future__ import annotations

import sys

from .oracle import OracleUnavailable, UDPipeOracle
from .parity import compare_all, summarise
from .tests.golden import recordings


def main() -> int:
    try:
        oracle = UDPipeOracle()
    except OracleUnavailable as exc:
        print(f"✗ služba neběží: {exc}")
        print("  (provozní stav, ne verdikt o kódu — testy na ní nezávisí)")
        return 2

    print(f"živá služba: {oracle.provenance}")
    results = compare_all(recordings(), oracle)
    for line in summarise(results):
        print(line)
    for parity in results:
        for line in parity.render():
            print(line)
    differing = [r for r in results if not r.agrees]
    if differing:
        print()
        print(
            "Rozdíl NENÍ chyba. Rozhodni, jestli se přepíše nahrávka "
            "(vědomě, s viditelným diffem), nebo se zapíše jako mez."
        )
    return 1 if differing else 0


if __name__ == "__main__":  # pragma: no cover — vstupní bod, ne knihovna
    sys.exit(main())
