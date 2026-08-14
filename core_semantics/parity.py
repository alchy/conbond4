"""Shoda nahrávky se živým rozborem — první krok k živé službě.

Zlaté transkripty fixují rozbor jako **data** (`golden.py`), aby se
neměřily dvě věci najednou. Až se zapojí běžící `cb-udpipe`, je první
otázka jednoduchá a nepříjemná: **čte skutečný parser ty věty stejně?**

**Rozdíl NENÍ chyba.** Je to nález k rozhodnutí. Jiný model čte jinak,
a protože je model součástí provenience, keš starý záznam správně
odmítne — systém se nerozejde tiše, rozejde se hlasitě. Tenhle modul jen
ukáže KDE.

**Nahrávky zůstávají pravdou testů.** Živý parser je nový zdroj, ne
náhrada: sada se nesmí začít ptát služby, jinak přestane být hermetická
a začne padat podle toho, co je zrovna spuštěné. Porovnání je proto
samostatná operace, kterou si někdo pustí, ne něco, co se děje v testech.

**Provenience se hlásí první.** Když se liší model, liší se skoro jistě
i tokeny, a vypsat padesát rozdílů tam, kde stačí jedna věta „tohle je
jiný model", je způsob, jak nález utopit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .oracle import OracleError, ParseOracle, Token, Utterance


@dataclass(frozen=True, slots=True)
class TokenDiff:
    """Jeden rozdíl v jednom tokenu."""

    index: int
    field: str
    recorded: str
    live: str

    def __str__(self) -> str:
        return f"token {self.index}, {self.field}: {self.recorded!r} → {self.live!r}"


@dataclass(frozen=True, slots=True)
class SentenceParity:
    """Výsledek porovnání jedné věty."""

    text: str
    recorded_provenance: str
    live_provenance: str
    differences: tuple[TokenDiff, ...] = ()
    #: Rozdíl v POČTU tokenů — jiná tokenizace je vážnější než jiný rys,
    #: protože se pak nedá porovnávat po pozicích vůbec.
    recorded_tokens: int = 0
    live_tokens: int = 0
    error: str = ""

    @property
    def same_model(self) -> bool:
        return self.recorded_provenance == self.live_provenance

    @property
    def agrees(self) -> bool:
        return (
            not self.error
            and not self.differences
            and self.recorded_tokens == self.live_tokens
        )

    def render(self) -> tuple[str, ...]:
        if self.error:
            return (f"» {self.text}", f"   ✗ {self.error}")
        if self.agrees:
            return (f"» {self.text}", "   ✓ rozbor se shoduje")
        lines = [f"» {self.text}"]
        if not self.same_model:
            # Hlásí se PRVNÍ a samo o sobě: liší-li se model, liší se
            # skoro jistě i tokeny, a vypsat je všechny by nález utopilo.
            lines.append(
                f"   ! JINÝ MODEL: {self.recorded_provenance!r} "
                f"→ {self.live_provenance!r}"
            )
            lines.append(
                "     (rozdíly níž jsou pravděpodobně jeho důsledek, "
                "ne nezávislé nálezy)"
            )
        if self.recorded_tokens != self.live_tokens:
            lines.append(
                f"   ! JINÁ TOKENIZACE: {self.recorded_tokens} → "
                f"{self.live_tokens} tokenů — po pozicích už se porovnat nedá"
            )
            return tuple(lines)
        lines.extend(f"   · {diff}" for diff in self.differences)
        return tuple(lines)


#: Pole tokenu, která se porovnávají. `form` schválně taky: kdyby se
#: lišila, nejde o rozbor, ale o tokenizaci, a to je jiná třída nálezu.
COMPARED = ("form", "lemma", "upos", "head", "deprel")


def _token_diffs(recorded: Token, live: Token) -> tuple[TokenDiff, ...]:
    found = [
        TokenDiff(recorded.index, field, str(getattr(recorded, field)), str(getattr(live, field)))
        for field in COMPARED
        if getattr(recorded, field) != getattr(live, field)
    ]
    keys = {k for k, _ in recorded.feats} | {k for k, _ in live.feats}
    for key in sorted(keys):
        was, now = recorded.feat(key), live.feat(key)
        if was != now:
            found.append(
                TokenDiff(recorded.index, key, str(was), str(now))
            )
    return tuple(found)


def compare(recorded: Utterance, live: Utterance) -> SentenceParity:
    """Porovná nahraný rozbor se živým, token po tokenu."""
    if not recorded.readings or not live.readings:
        return SentenceParity(
            text=recorded.text,
            recorded_provenance="",
            live_provenance="",
            error="jedna ze stran nemá žádné čtení",
        )
    was, now = recorded.readings[0], live.readings[0]
    parity = SentenceParity(
        text=recorded.text,
        recorded_provenance=was.provenance,
        live_provenance=now.provenance,
        recorded_tokens=len(was.tokens),
        live_tokens=len(now.tokens),
    )
    if len(was.tokens) != len(now.tokens):
        return parity
    differences: list[TokenDiff] = []
    for old, new in zip(was.tokens, now.tokens):
        differences.extend(_token_diffs(old, new))
    return SentenceParity(
        text=parity.text,
        recorded_provenance=parity.recorded_provenance,
        live_provenance=parity.live_provenance,
        differences=tuple(differences),
        recorded_tokens=parity.recorded_tokens,
        live_tokens=parity.live_tokens,
    )


def compare_all(
    recordings: Mapping[str, Utterance], live: ParseOracle
) -> tuple[SentenceParity, ...]:
    """Diferenční běh přes celou sadu.

    Selhání JEDNÉ věty běh nezastaví — cílem je úplný obrázek, ne první
    problém. Provozní chyba se zaznamená u té věty a pokračuje se.
    """
    out: list[SentenceParity] = []
    for text in sorted(recordings):
        recorded = recordings[text]
        try:
            out.append(compare(recorded, live.parse(text)))
        except OracleError as exc:
            out.append(
                SentenceParity(
                    text=text,
                    recorded_provenance=(
                        recorded.readings[0].provenance if recorded.readings else ""
                    ),
                    live_provenance="",
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return tuple(out)


def summarise(results: tuple[SentenceParity, ...]) -> tuple[str, ...]:
    agree = sum(1 for r in results if r.agrees)
    failed = sum(1 for r in results if r.error)
    models = {r.live_provenance for r in results if r.live_provenance}
    lines = [
        f"vět: {len(results)} · shoduje se: {agree} · liší se: "
        f"{len(results) - agree - failed} · nedostupných: {failed}",
    ]
    if len(models) > 1:
        lines.append(
            f"! živá služba vrátila VÍC proveniencí {sorted(models)} — "
            f"to není rozdíl v rozboru, to je nestabilní prostředí"
        )
    return tuple(lines)
