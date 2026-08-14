"""Konzole, která unese češtinu.

Dialogové testy vypisují transkript na `stdout` a ten je plný `ě`, `ů`,
`ř`. Na Windows je konzole ve výchozím stavu `cp1252`, takže `pytest -s`
končil `UnicodeEncodeError` — a to **přesně v tom režimu, kvůli kterému
výpis vznikl**. Pod `pytest -q` se to neprojevilo, protože pytest stdout
zachytává; testy tedy byly zelené, zatímco funkce nefungovala.

Oprava patří sem, ne do proměnných prostředí: nikdo nemá mít povinnost
nastavit `PYTHONIOENCODING`, aby mu prošly testy.
"""

from __future__ import annotations

import sys
from typing import IO, Any


def force_utf8(stream: IO[Any] | None) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):  # pragma: no cover — proud to nedovolí
        pass


def echo(text: str) -> None:
    """Vypíše text i na konzoli, která ho neumí celý zakódovat.

    Druhá pojistka k fixture `utf8_console`: proud může být objekt, který
    `reconfigure` nemá (starší zachytávač, přesměrování). Výpis transkriptu
    nesmí být to, co shodí testovací sadu.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        print(text.encode(encoding, errors="replace").decode(encoding))
