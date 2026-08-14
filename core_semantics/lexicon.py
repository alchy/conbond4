"""Jazykový program `LEX` — § 3.7 zadání.

> „Učením se mění program, nikdy jazyk." Dialog učí, KTERÉ slovo spouští
> KTEROU už existující operaci jádra — nikdy nevyrábí novou sémantiku
> (I‑15, I‑16).

**Menu se nepřenáší, přenáší se mechanismus.** Třída a životní cyklus
(`StructuralSignature` → `Trigger` → `LearnedPattern` s proveniencí
a statusem) jsou převzaté; obsah menu je odvozený z toho, co `core_semantics`
skutečně umí. Portovat cizí menu doslova by znamenalo mapovat česká slova
na operace, které jádro nemá.

**Shoda vrací KANDIDÁTY, ne jedno mapování.** Tohle je rozdíl proti
předloze a plyne přímo z toho, co odemkla termová algebra: české „nebo"
je **dvě různé operace jádra** podle toho, jestli jde o tvrzení, nebo
o alternativní otázku.

```
„Petr má psa nebo kočku."      → member(Petr, pes OR kočka)   objektové OR
„Je citron ovoce, nebo zelenina?" → alt{…}                    epistemická alternativa
```

Kdyby `match()` vracel jedno mapování, musel by mezi nimi tiše vybrat —
a tichá volba měnící význam není cesta nikdy (I‑1). Rozhoduje kaskáda
§ 5.2 podle struktury; když nerozhodne, patří sem **doptání**, ne
heuristika.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class Operation(Enum):
    """Uzavřené menu (I‑15). Každá položka JE operace, kterou jádro umí —
    nic víc a nic jiného se naučit nedá."""

    # algebra termů (§ 2)
    GROUP_AND = "group_and"
    GROUP_OR = "group_or"
    GROUP_DIFF = "group_diff"
    # kvantifikátor na roli (§ 5.2)
    FOR_ALL = "for_all"
    EXISTS = "exists"
    # komparátory (§ 6)
    LESS_EQUAL = "le"
    LESS = "lt"
    GREATER_EQUAL = "ge"
    GREATER = "gt"
    # strukturní predikáty (§ 5.1, 5.3)
    MEMBER = "member"
    SUBSET = "subset"
    DISJOINT = "disjoint"
    SAME_AS = "same_as"
    COMPLETE = "complete"
    # epistemická vrstva (§ 4) — druhá tvář „nebo"
    ALTERNATIVE = "alt"
    NEGATION = "negation"


#: Lidský popis pro učicí doptání. `clarify` nabízí VÝHRADNĚ tyhle položky,
#: takže dialog nemůže vyrobit novou sémantiku (§ 7 zadání).
MENU: tuple[tuple[Operation, str], ...] = (
    (Operation.GROUP_AND, "obojí zároveň — průnik skupin"),
    (Operation.GROUP_OR, "jedno nebo druhé, nevíme které — sjednocení"),
    (Operation.GROUP_DIFF, "to první kromě toho druhého — rozdíl"),
    (Operation.FOR_ALL, "platí o každém členu skupiny"),
    (Operation.EXISTS, "platí o některém členu, ale nevíme o kterém"),
    (Operation.LESS_EQUAL, "nejvýše tolik"),
    (Operation.LESS, "míň než tolik"),
    (Operation.GREATER_EQUAL, "aspoň tolik"),
    (Operation.GREATER, "víc než tolik"),
    (Operation.MEMBER, "je prvkem skupiny"),
    (Operation.SUBSET, "je podskupinou"),
    (Operation.DISJOINT, "tyhle dvě skupiny se vylučují"),
    (Operation.SAME_AS, "je to týž uzel pod jiným jménem"),
    (Operation.COMPLETE, "to jsou všichni, které skupina má"),
    (Operation.ALTERNATIVE, "otázka, který z členů platí"),
    (Operation.NEGATION, "doložené popření, ne pouhá nevědomost"),
)


class Mood(Enum):
    """Tah dialogu, ve kterém slovo zaznělo. Jediný strukturní rozlišovač,
    který odděluje objektové `OR` od epistemické alternativy."""

    ASSERTION = "!"
    QUESTION = "?"
    UNKNOWN = "?!"


class PatternStatus(Enum):
    HYPOTHESIS = "hypothesis"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    REVOKED = "revoked"


ACTIVE_STATUSES = (PatternStatus.HYPOTHESIS, PatternStatus.CONFIRMED)


@dataclass(frozen=True, slots=True)
class StructuralSignature:
    """Strukturní popis konstrukce **nezávislý na entitách a predikátech**.

    Na tom stojí renaming test z § 10: přejmenuj entity a vzor musí sedět
    dál. Proto tu nejsou žádné konkrétní lemma podstatných jmen — jen
    spouštěcí slovo, jeho tvar a tah, ve kterém zaznělo.
    """

    lemma: str
    mood: Mood = Mood.UNKNOWN
    upos: str = ""
    deprel: str = ""

    def key(self) -> str:
        return f"{self.lemma}|{self.mood.value}"


@dataclass(frozen=True, slots=True)
class Trigger:
    """Spouštěč. `mood=UNKNOWN` znamená „na tahu nezáleží"."""

    lemma: str
    mood: Mood = Mood.UNKNOWN
    deprel: str = ""

    def matches(self, signature: StructuralSignature) -> bool:
        if self.lemma != signature.lemma:
            return False
        if self.mood is not Mood.UNKNOWN and signature.mood is not Mood.UNKNOWN:
            if self.mood is not signature.mood:
                return False
        if self.deprel and signature.deprel and self.deprel != signature.deprel:
            return False
        return True

    def key(self) -> str:
        return f"{self.lemma}|{self.mood.value}|{self.deprel}"


@dataclass(frozen=True, slots=True)
class LearnedPattern:
    """Mapování spouštěč → operace, s proveniencí a statusem.

    Odvolání maže **mapování, ne operaci** — jádro zůstává nedotčené."""

    trigger: Trigger
    operation: Operation
    learned_from: str
    status: PatternStatus = PatternStatus.HYPOTHESIS

    def with_status(self, status: PatternStatus) -> "LearnedPattern":
        return LearnedPattern(
            self.trigger, self.operation, self.learned_from, status
        )

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def to_json_object(self) -> dict[str, Any]:
        return {
            "trigger": {
                "lemma": self.trigger.lemma,
                "mood": self.trigger.mood.value,
                "deprel": self.trigger.deprel,
            },
            "operation": self.operation.value,
            "learned_from": self.learned_from,
            "status": self.status.value,
        }

    @staticmethod
    def from_json_object(raw: Mapping[str, Any]) -> "LearnedPattern":
        trigger = raw["trigger"]
        return LearnedPattern(
            trigger=Trigger(
                lemma=trigger["lemma"],
                mood=Mood(trigger.get("mood", Mood.UNKNOWN.value)),
                deprel=trigger.get("deprel", ""),
            ),
            operation=Operation(raw["operation"]),
            learned_from=raw["learned_from"],
            status=PatternStatus(raw.get("status", "hypothesis")),
        )

    def __str__(self) -> str:
        return (
            f"{self.trigger.key()} -> {self.operation.value} "
            f"[{self.status.value}, {self.learned_from}]"
        )


class Lexicon:
    """Sbírka naučených vzorů. Žádný globální stav, všechno je to data."""

    def __init__(self, patterns: Iterable[LearnedPattern] = ()) -> None:
        self._by_key: dict[str, LearnedPattern] = {}
        for pattern in patterns:
            self.add(pattern)

    def add(self, pattern: LearnedPattern) -> None:
        self._by_key[pattern.trigger.key()] = pattern

    def teach(
        self,
        trigger: Trigger,
        operation: Operation,
        *,
        learned_from: str,
    ) -> LearnedPattern:
        """Naučí mapování jako HYPOTÉZU. Potvrzení je samostatný tah (I‑7)."""
        pattern = LearnedPattern(trigger, operation, learned_from)
        self.add(pattern)
        return pattern

    def candidates(
        self, signature: StructuralSignature
    ) -> tuple[LearnedPattern, ...]:
        """**Kandidáti, ne jedno mapování.**

        Vrací všechna aktivní mapování, která na strukturu sedí, seřazená
        deterministicky. Když jich je víc než jedno, kaskáda § 5.2 buď
        rozhodne strukturou, nebo se zeptá — vybrat tiše nesmí.
        """
        found = [
            pattern
            for pattern in self._by_key.values()
            if pattern.active and pattern.trigger.matches(signature)
        ]
        return tuple(sorted(found, key=lambda p: p.trigger.key()))

    def confirm(self, key: str) -> LearnedPattern | None:
        return self._set_status(key, PatternStatus.CONFIRMED)

    def reject(self, key: str) -> LearnedPattern | None:
        return self._set_status(key, PatternStatus.REJECTED)

    def revoke(self, key: str) -> LearnedPattern | None:
        return self._set_status(key, PatternStatus.REVOKED)

    def _set_status(
        self, key: str, status: PatternStatus
    ) -> LearnedPattern | None:
        pattern = self._by_key.get(key)
        if pattern is None:
            return None
        updated = pattern.with_status(status)
        self._by_key[key] = updated
        return updated

    def all(self) -> tuple[LearnedPattern, ...]:
        return tuple(
            sorted(self._by_key.values(), key=lambda p: p.trigger.key())
        )

    def to_json(self) -> str:
        return json.dumps(
            [pattern.to_json_object() for pattern in self.all()],
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def from_json(text: str) -> "Lexicon":
        raw = json.loads(text)
        if not isinstance(raw, list):
            raise ValueError("LEX program musí být seznam vzorů")
        return Lexicon(LearnedPattern.from_json_object(item) for item in raw)


# --------------------------------------------------------------------------
# Výchozí český profil
# --------------------------------------------------------------------------

#: Startovní mapování. Je to **data se statusem HYPOTÉZA**, ne zadrátovaný
#: jazyk: každý řádek jde potvrdit i odvolat a nic z toho se nepovažuje za
#: jisté, dokud to člověk nepotvrdí (I‑5, I‑7).
_SEED: tuple[tuple[str, Mood, Operation], ...] = (
    # „nebo" — DVĚ různé operace jádra podle tahu dialogu
    ("nebo", Mood.ASSERTION, Operation.GROUP_OR),
    ("nebo", Mood.QUESTION, Operation.ALTERNATIVE),
    ("anebo", Mood.ASSERTION, Operation.GROUP_OR),
    # průnik
    ("a", Mood.UNKNOWN, Operation.GROUP_AND),
    ("i", Mood.UNKNOWN, Operation.GROUP_AND),
    # rozdíl — nové cíle, které před termovou algebrou neexistovaly
    ("kromě", Mood.UNKNOWN, Operation.GROUP_DIFF),
    ("mimo", Mood.UNKNOWN, Operation.GROUP_DIFF),
    ("vyjma", Mood.UNKNOWN, Operation.GROUP_DIFF),
    # kvantifikátory na roli
    ("každý", Mood.UNKNOWN, Operation.FOR_ALL),
    ("všechen", Mood.UNKNOWN, Operation.FOR_ALL),
    ("nějaký", Mood.UNKNOWN, Operation.EXISTS),
    ("některý", Mood.UNKNOWN, Operation.EXISTS),
    # komparátory
    ("nejvýše", Mood.UNKNOWN, Operation.LESS_EQUAL),
    ("nanejvýš", Mood.UNKNOWN, Operation.LESS_EQUAL),
    ("aspoň", Mood.UNKNOWN, Operation.GREATER_EQUAL),
    ("minimálně", Mood.UNKNOWN, Operation.GREATER_EQUAL),
    # strukturní
    ("žádný", Mood.UNKNOWN, Operation.DISJOINT),
)


def czech_seed(*, learned_from: str = "seed") -> Lexicon:
    """Výchozí český lexikon — všechno jako hypotézy."""
    return Lexicon(
        LearnedPattern(
            trigger=Trigger(lemma=lemma, mood=mood),
            operation=operation,
            learned_from=learned_from,
        )
        for lemma, mood, operation in _SEED
    )


def menu_prompt(options: Sequence[Operation] = ()) -> tuple[str, ...]:
    """Nabídka pro učicí doptání. Obsahuje VÝHRADNĚ operace z menu, takže
    dialog nemůže vyrobit novou sémantiku."""
    allowed = set(options) if options else {operation for operation, _ in MENU}
    return tuple(
        f"{operation.value}: {description}"
        for operation, description in MENU
        if operation in allowed
    )
