"""Metriky dialogu — § 10 a K‑8.

Hlavní číslo projektu je „kolik tahů dialogu potřebuje, aby se naučil
odpovídat správně" (`Session.turns_to_learn`). Samo o sobě ale **může
lhát oběma směry**, a K‑8 to říká přesně:

> Jeden tah do naučení a deset chybných použití je horší než tři tahy
> a stabilní správnost.

Rychlé učení, které se pořád opravuje, není učení — je to hádání
s dobrou pamětí. Proto se k počtu tahů měří ještě troje:

* **informace na tah** — co po tahu v bázi přibylo;
* **znovupoužití** — jestli se naučený vzor uplatnil i jinde než tam,
  kde vznikl;
* **míra oprav** — kolik tahů muselo něco vzít zpátky.

**Všechno se počítá ze ŽURNÁLU a z BÁZE, nic se nemasuje průběžně.**
Kdyby si vrstvy vedly čítače, měřily by samy sebe a čísla by přežila
`revoke`. Takhle je metrika funkcí stavu, takže po odvolání klesne — což
je přesně to, co má dělat.

**Co tahle čísla NEJSOU.** Nejsou to skóre kvality. Neříkají, jestli
systém odpovídá správně — na to je akceptační sada. Říkají, jestli se
učí lacino, nebo draho.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .ast import QueryStatus

if TYPE_CHECKING:  # pragma: no cover — jen pro typy
    from .session import Session, TurnKind

#: Tahy, kterými se něco BERE ZPÁTKY. Odpověď na doptání (`→∀`, `→=`)
#: mezi ně nepatří — to není oprava, to je doplnění: systém se zeptal,
#: protože nevěděl, ne protože se spletl.
CORRECTIVE = ("REVOKE", "SPLIT", "DISTINCT")


@dataclass(frozen=True, slots=True)
class Metrics:
    """Změřený dialog. Každé pole má u sebe, co znamená a co ne."""

    turns: int
    #: Tahy, po kterých v bázi něco přibylo NEBO padla doložená odpověď.
    #: Tah, který skončil jen otázkou, informativní není — a je správně,
    #: že se to pozná.
    informative: int
    #: Výroky, které přibyly přímo z tahů (bez odvozených a reifikovaných).
    #: Odvozené se nepočítají schválně: jsou to důsledky, ne nová znalost,
    #: a jejich počet se řídí tvarem vztahu, ne tím, co člověk řekl.
    stated: int
    #: Tahy, které něco vzaly zpátky.
    corrections: int
    #: Naučené vzory, které se uplatnily i mimo tah, kde vznikly.
    reused_patterns: int
    #: Naučené vzory celkem.
    learned_patterns: int
    #: Odpovědi podle verdiktu.
    answered: int
    unknown: int
    conflicts: int
    #: Otevřené otázky, na které nikdo neodpověděl.
    open_questions: int

    @property
    def information_per_turn(self) -> float:
        return self.stated / self.turns if self.turns else 0.0

    @property
    def correction_rate(self) -> float:
        """Podíl tahů, které něco opravovaly.

        Tohle je to číslo, které drží `turns_to_learn` u země. Bez něj by
        vyhrálo řešení, které se naučí na první pokus cokoli a pak to
        deset tahů odvolává."""
        return self.corrections / self.turns if self.turns else 0.0

    @property
    def reuse_rate(self) -> float:
        """Podíl naučených vzorů, které se uplatnily i jinde.

        Vzor použitý jen tam, kde vznikl, je zapamatovaná odpověď na jednu
        větu — ne naučené pravidlo. Nízké číslo neznamená chybu, ale
        znamená, že se učení zatím nevyplácí."""
        if not self.learned_patterns:
            return 0.0
        return self.reused_patterns / self.learned_patterns

    def render(self) -> tuple[str, ...]:
        return (
            f"tahů:                {self.turns}",
            f"informativních:      {self.informative}"
            f"  ({self.informative / self.turns:.0%})" if self.turns else "",
            f"výroků z tahů:       {self.stated}"
            f"   → informace na tah {self.information_per_turn:.2f}",
            f"odpovědí A/N:        {self.answered}"
            f"   nevím: {self.unknown}   spor: {self.conflicts}",
            f"otevřených otázek:   {self.open_questions}",
            f"naučených vzorů:     {self.learned_patterns}"
            f"   znovupoužitých: {self.reused_patterns}"
            f"   ({self.reuse_rate:.0%})",
            f"oprav:               {self.corrections}"
            f"   míra oprav {self.correction_rate:.0%}",
        )


def measure(session: "Session") -> Metrics:
    """Změří sezení z jeho žurnálu a báze.

    Nic si nepamatuje a nic nemasuje — proto se dá zavolat kdykoli
    a po `revoke` vyjde jinak.
    """
    results = session.results
    turns = len(results)

    stated = sum(
        1
        for statement in session.kb.active()
        if statement.derived_from is None
    )
    answered = sum(
        1
        for r in results
        if r.status in (QueryStatus.PROVEN_TRUE, QueryStatus.PROVEN_FALSE)
    )
    unknown = sum(1 for r in results if r.status is QueryStatus.UNKNOWN)
    conflicts = sum(1 for r in results if r.status is QueryStatus.CONFLICT)
    informative = sum(
        1
        for r in results
        if r.statement_id is not None
        or r.status in (QueryStatus.PROVEN_TRUE, QueryStatus.PROVEN_FALSE)
    )
    corrections = sum(1 for r in results if r.turn.kind.name in CORRECTIVE)
    open_questions = sum(1 for r in results if r.question is not None)

    learned, reused = _pattern_reuse(session)
    return Metrics(
        turns=turns,
        informative=informative,
        stated=stated,
        corrections=corrections,
        reused_patterns=reused,
        learned_patterns=learned,
        answered=answered,
        unknown=unknown,
        conflicts=conflicts,
        open_questions=open_questions,
    )


def _pattern_reuse(session: "Session") -> tuple[int, int]:
    """Kolik vzorů se naučilo a kolik z nich se uplatnilo i jinde.

    Počítá se z toho, co role o sobě **říká**: `RoleReading.source` nese
    tvar, ze kterého kvantifikátor plyne. Vzor se považuje za
    znovupoužitý, když takový tvar rozhodl roli ve VÍC než jednom tahu.

    Je to podhodnocené a je to schválně: vzor, který se uplatnil dvakrát
    v jednom tahu, se nepočítá. Nadhodnocená metrika učení by tvrdila
    úspěch tam, kde se jen opakovala jedna věta.
    """
    learned = [p for p in session.lexicon.all() if p.trigger.structural and p.active]
    if not learned:
        return 0, 0
    seen: dict[str, set[int]] = {}
    for result in session.results:
        if result.predication is None:
            continue
        for role in result.predication.roles:
            if role.source.startswith("tvar "):
                seen.setdefault(role.source, set()).add(result.index)
    reused = sum(1 for turns in seen.values() if len(turns) > 1)
    return len(learned), reused
