"""Společné zázemí testů. Pomocníky drží `_console`, aby je testy mohly
importovat běžným importem — conftest je pytestí soubor, ne knihovna."""

from __future__ import annotations

import sys
from typing import Iterator

import pytest

from core_semantics.tests._console import force_utf8


@pytest.fixture(scope="session", autouse=True)
def utf8_console() -> Iterator[None]:
    """Přenastaví proud, který má pytest k dispozici v okamžiku běhu.

    Fixture, ne kód při importu: pod `-s` pytest `sys.stdout` vyměňuje až
    po načtení conftestu, takže reconfigure při importu by minul cíl.
    """
    force_utf8(sys.stdout)
    force_utf8(sys.stderr)
    yield
