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

import hashlib
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
    #: `·` — role mluví o TOM konkrétním uzlu, ne o skupině. Jádro to zná
    #: jako `Quantifier.SELF` a bez něj nejde do role dosadit individuum.
    SELF = "self"
    #: `name(of, value)` — POJMENOVÁNÍ uzlu. Do `RELATIONAL` ZÁMĚRNĚ
    #: nepatří: menu holé spony nabízí vztahy dvou TŘÍD, kdežto tohle je
    #: vztah uzlu a jeho nálepky. Nabídnout ho u „Kočka je savec." by byla
    #: položka, na kterou tam nejde správně odpovědět.
    NAME = "name"
    #: Určitost, NE kvantifikace. „to auto" neotvírá skupinový fillér, ale
    #: odkazuje na už existující uzel — a rozřešit ten odkaz je práce V3
    #: (§ 6.12, dialog F: „určitý popis rozřešen při attach").
    DEFINITE = "definite"
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
    #: Uspořádání na časové ose (§ 5.1). Do menu přibylo, až když k němu
    #: vedla česká věta — dřív by to byla položka, kterou nikdo nedosáhne.
    BEFORE = "before"
    #: Zahrnutí MÍSTA a zahrnutí ČASU. Čeština je jedním tvarem nerozliší
    #: („Praha je součástí Česka." × „Pondělí je součástí týdne."), takže
    #: v menu musí být obě a rozhodne se VĚTA po větě.
    CONTAINS = "contains"
    WITHIN = "within"
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
    (Operation.SELF, "mluví o tom konkrétním, ne o skupině"),
    (Operation.DEFINITE, "odkazuje na už zmíněný uzel, žádnou skupinu neotvírá"),
    (Operation.LESS_EQUAL, "nejvýše tolik"),
    (Operation.LESS, "míň než tolik"),
    (Operation.GREATER_EQUAL, "aspoň tolik"),
    (Operation.GREATER, "víc než tolik"),
    (Operation.MEMBER, "je prvkem skupiny"),
    (Operation.SUBSET, "je podskupinou"),
    (Operation.DISJOINT, "tyhle dvě skupiny se vylučují"),
    (Operation.SAME_AS, "je to týž uzel pod jiným jménem"),
    (Operation.NAME, "tomu uzlu se takhle říká"),
    (Operation.COMPLETE, "to jsou všichni, které skupina má"),
    (Operation.BEFORE, "to první je na časové ose dřív"),
    (Operation.CONTAINS, "to druhé zahrnuje to první jako MÍSTO"),
    (Operation.WITHIN, "to druhé zahrnuje to první jako ČAS"),
    (Operation.ALTERNATIVE, "otázka, který z členů platí"),
    (Operation.NEGATION, "doložené popření, ne pouhá nevědomost"),
)


#: Operace, které odpovídají na otázku „jak je fillér v roli kvantifikovaný".
#: `DEFINITE` je mezi nimi schválně: je to legitimní odpověď („žádnou skupinu
#: neotvírá, odkazuje na uzel"), jen ji dokončí až V3.
QUANTIFYING: frozenset["Operation"] = frozenset(
    {Operation.FOR_ALL, Operation.EXISTS, Operation.SELF, Operation.DEFINITE}
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

    `number` a `case` přibyly kvůli kvantifikátoru na roli (L‑3): holé
    jméno se pozná **jen tvarem**, protože žádné spouštěcí slovo u sebe
    nemá. Signatura pro ně nese `lemma=""` — a to je přesně ten tvar,
    který renaming test vyžaduje, protože na slově nezávisí vůbec.
    """

    lemma: str
    mood: Mood = Mood.UNKNOWN
    upos: str = ""
    deprel: str = ""
    number: str = ""
    case: str = ""

    def key(self) -> str:
        return f"{self.lemma}|{self.mood.value}"

    def shape(self) -> str:
        """Popis tvaru pro člověka — do doptání a do transkriptu."""
        parts = [p for p in (self.upos, self.number, self.case, self.deprel) if p]
        return "/".join(parts) if parts else "?"


@dataclass(frozen=True, slots=True)
class Trigger:
    """Spouštěč. `mood=UNKNOWN` znamená „na tahu nezáleží".

    **Prázdné `lemma` je zástupný znak, ne chybějící údaj.** Spouštěč bez
    slova sedí na každé slovo daného TVARU — a je to jediný způsob, jak
    popsat holé jméno, které u sebe žádný determinátor nemá. Ostatní pole
    se porovnávají stejně: prázdné znamená „na tomhle nezáleží".
    """

    lemma: str
    mood: Mood = Mood.UNKNOWN
    deprel: str = ""
    upos: str = ""
    number: str = ""
    case: str = ""

    @property
    def structural(self) -> bool:
        """Spouštěč bez slova — sedí na tvar, ne na lexikum."""
        return not self.lemma

    def matches(self, signature: StructuralSignature) -> bool:
        if self.structural and not (
            self.upos or self.number or self.case or self.deprel
        ):
            # Spouštěč bez slova I bez tvaru by sedl na cokoli. To není
            # vzor, to je tichý default s razítkem naučeného.
            return False
        if self.lemma and self.lemma != signature.lemma:
            return False
        if self.structural and signature.lemma:
            # Lexikální signatura se strukturním vzorem nepáruje. Dvě
            # různé otázky („co znamená tohle slovo" × „co znamená tenhle
            # tvar") mají zůstat oddělené, jinak by šlo jedno doložit
            # odpovědí na druhé.
            return False
        if self.mood is not Mood.UNKNOWN and signature.mood is not Mood.UNKNOWN:
            if self.mood is not signature.mood:
                return False
        for mine, theirs in (
            (self.deprel, signature.deprel),
            (self.upos, signature.upos),
            (self.number, signature.number),
            (self.case, signature.case),
        ):
            if mine and theirs and mine != theirs:
                return False
            if mine and not theirs:
                # Rozbor ten údaj nedal. Tvrdit shodu by znamenalo dosadit
                # si ho — a to je právě to hádání, kterému se vzor vyhýbá.
                return False
        return True

    def key(self) -> str:
        base = f"{self.lemma}|{self.mood.value}|{self.deprel}"
        if self.upos or self.number or self.case:
            return f"{base}|{self.upos}|{self.number}|{self.case}"
        return base


@dataclass(frozen=True, slots=True)
class LearnedPattern:
    """Mapování spouštěč → operace, s proveniencí a statusem.

    Odvolání maže **mapování, ne operaci** — jádro zůstává nedotčené."""

    trigger: Trigger
    operation: Operation
    learned_from: str
    status: PatternStatus = PatternStatus.HYPOTHESIS

    def key(self) -> str:
        """Klíč nese SPOUŠTĚČ **i OPERACI**.

        Kdyby nesl jen spouštěč, druhé mapování téhož slova by to první
        tiše přepsalo — a právě dvojznačná slova jsou ta zajímavá:
        „žádný" je oddělenost skupin i doložené popření, „nebo" je
        sjednocení i alternativa. Tichý zápis nad zápisem by tu
        dvojznačnost odstranil, aniž by se kdokoli zeptal (I‑1). `RoleMapping`
        to má stejně a ze stejného důvodu.
        """
        return f"{self.trigger.key()}->{self.operation.value}"

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
                "upos": self.trigger.upos,
                "number": self.trigger.number,
                "case": self.trigger.case,
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
                upos=trigger.get("upos", ""),
                number=trigger.get("number", ""),
                case=trigger.get("case", ""),
            ),
            operation=Operation(raw["operation"]),
            learned_from=raw["learned_from"],
            status=PatternStatus(raw.get("status", "hypothesis")),
        )

    def __str__(self) -> str:
        # Strukturní vzor se popisuje TVAREM, ne klíčem. Klíč je pro
        # slovník; `|?!|nsubj|NOUN|Sing|Nom` je v transkriptu, který má
        # číst člověk, jen šum.
        what = (
            "tvar " + "/".join(
                p
                for p in (
                    self.trigger.upos,
                    self.trigger.number,
                    self.trigger.case,
                    self.trigger.deprel,
                )
                if p
            )
            if self.trigger.structural
            else self.trigger.key()
        )
        return (
            f"{what} -> {self.operation.value} "
            f"[{self.status.value}, {self.learned_from}]"
        )


@dataclass(frozen=True, slots=True)
class RoleMapping:
    """Ekvivalence rolí — § 3.7 (`role "kudy" ~ prep("po")+Loc`) a § 12/1.

    Kaskáda pojmenuje okolnost povrchově (`do+Gen`), protože sémantiku
    hádat nesmí. Že `do+Gen` znamená `kam`, je **naučené a odvolatelné
    tvrzení**, ne vlastnost kódu — jinak by se do interpretu propašoval
    seznam významů předložek.

    Není to `Operation`: neukazuje na operaci jádra, ale přejmenovává roli.
    Proto vlastní druh řádku programu se stejným životním cyklem.
    """

    surface: str
    canonical: str
    learned_from: str
    status: PatternStatus = PatternStatus.HYPOTHESIS

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def with_status(self, status: PatternStatus) -> "RoleMapping":
        return RoleMapping(self.surface, self.canonical, self.learned_from, status)

    def key(self) -> str:
        return f"{self.surface}->{self.canonical}"

    def to_json_object(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "canonical": self.canonical,
            "learned_from": self.learned_from,
            "status": self.status.value,
        }

    @staticmethod
    def from_json_object(raw: Mapping[str, Any]) -> "RoleMapping":
        return RoleMapping(
            surface=raw["surface"],
            canonical=raw["canonical"],
            learned_from=raw["learned_from"],
            status=PatternStatus(raw.get("status", "hypothesis")),
        )

    def __str__(self) -> str:
        return (
            f"role {self.surface} ~ {self.canonical} "
            f"[{self.status.value}, {self.learned_from}]"
        )


#: Operace, které odpovídají na otázku „kterou JÁDROVOU RELACI ta věta
#: tvrdí". Filtruje se tady ze stejného důvodu jako `QUANTIFYING`: spouštěč
#: nemá vědět, na co se zrovna ptáme.
RELATIONAL: frozenset["Operation"] = frozenset(
    {
        Operation.MEMBER,
        Operation.SUBSET,
        Operation.DISJOINT,
        Operation.BEFORE,
        Operation.SAME_AS,
        Operation.CONTAINS,
        Operation.WITHIN,
    }
)


@dataclass(frozen=True, slots=True)
class RelationMapping:
    """Konstrukce → jádrová relace — N‑2.

    „Amoxicilin je druh penicilinu" tvrdí `subset`, ne vztah `být` se třemi
    rolemi. Že to tvrdí, plyne ze **STAVBY věty**, a stavba se popisuje
    tvarem (`cop:druh+Gen`), ne slovem — proto vlastní druh řádku programu,
    stejně jako `RoleMapping`.

    **Není to `LearnedPattern`.** Ten se spouští jedním TOKENEM a jeho
    signatura je popis jednoho slova. Relaci ale nenese slovo, nese ji
    konstrukce přes několik členů — spona, podmět, jmenná část, případně
    přívlastek v genitivu. Nacpat to do `Trigger` by znamenalo přetížit
    pole `upos` něčím, co upos není, a to je ten druh úspory, po které se
    za měsíc nedá poznat, co která hodnota znamená.

    **Váží víc než ostatní vzory a je poctivé to říct.** Ostatní naučené
    vzory mění, jak se věta ČTE. Tenhle mění, co se z ní ZAPÍŠE do jádra:
    špatně navržený `subset` změní uzávěr celé báze. Proto se navrhuje
    a potvrzuje, nikdy nedosazuje potichu.
    """

    shape: str
    operation: Operation
    learned_from: str
    status: PatternStatus = PatternStatus.HYPOTHESIS

    def __post_init__(self) -> None:
        if self.operation not in RELATIONAL:
            # Bez téhle kontroly by šlo tvarem „naučit" cokoli z menu —
            # třeba kvantifikátor — a patro by pak dosadilo operaci, se
            # kterou neumí nic udělat. Selhat má zápis, ne čtení.
            raise ValueError(
                f"{self.operation.value!r} není jádrová relace; "
                f"na výběr je {sorted(o.value for o in RELATIONAL)}"
            )

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def with_status(self, status: PatternStatus) -> "RelationMapping":
        return RelationMapping(
            self.shape, self.operation, self.learned_from, status
        )

    def key(self) -> str:
        return f"{self.shape}=>{self.operation.value}"

    def __str__(self) -> str:
        return (
            f"konstrukce {self.shape} ~ {self.operation.value} "
            f"[{self.status.value}, {self.learned_from}]"
        )


class Lexicon:
    """Sbírka naučených vzorů. Žádný globální stav, všechno je to data."""

    def __init__(
        self,
        patterns: Iterable[LearnedPattern] = (),
        roles: Iterable[RoleMapping] = (),
        relations: Iterable[RelationMapping] = (),
    ) -> None:
        self._by_key: dict[str, LearnedPattern] = {}
        self._roles: dict[str, RoleMapping] = {}
        self._relations: dict[str, RelationMapping] = {}
        for pattern in patterns:
            self.add(pattern)
        for mapping in roles:
            self.add_role(mapping)
        for relation in relations:
            self.add_relation(relation)

    def add(self, pattern: LearnedPattern) -> None:
        self._by_key[pattern.key()] = pattern

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
        return tuple(sorted(found, key=lambda p: p.key()))

    def quantifier_candidates(
        self, signature: StructuralSignature
    ) -> tuple[LearnedPattern, ...]:
        """Kandidáti na kvantifikátor role — podmnožina `candidates`.

        Filtruje se až tady, ne v `matches`: spouštěč nemá vědět, na co se
        zrovna ptáme. „žádný" sedí na tutéž signaturu jako kvantifikátor
        i jako oddělenost skupin, a která z těch dvou odpovědí dává v roli
        smysl, ví kaskáda, ne lexikon.
        """
        return tuple(
            pattern
            for pattern in self.candidates(signature)
            if pattern.operation in QUANTIFYING
        )

    # -- ekvivalence rolí --------------------------------------------------

    def add_role(self, mapping: RoleMapping) -> None:
        self._roles[mapping.key()] = mapping

    def teach_role(
        self, surface: str, canonical: str, *, learned_from: str
    ) -> RoleMapping:
        mapping = RoleMapping(surface, canonical, learned_from)
        self.add_role(mapping)
        return mapping

    def role_candidates(self, surface: str) -> tuple[RoleMapping, ...]:
        """**Kandidáti, ne jedno mapování.**

        `v+Loc` je v češtině `kde` i `kdy` („v Praze" × „v pondělí") a
        rozliší to jen význam nominálu, který se nehádá. Dvě možnosti se
        proto vrátí obě a rozhoduje doptání."""
        found = [
            mapping
            for mapping in self._roles.values()
            if mapping.active and mapping.surface == surface
        ]
        return tuple(sorted(found, key=lambda m: m.canonical))

    def revoke_role(self, key: str) -> RoleMapping | None:
        mapping = self._roles.get(key)
        if mapping is None:
            return None
        updated = mapping.with_status(PatternStatus.REVOKED)
        self._roles[key] = updated
        return updated

    def all_roles(self) -> tuple[RoleMapping, ...]:
        return tuple(sorted(self._roles.values(), key=lambda m: m.key()))

    # -- konstrukce → jádrová relace (N‑2) ---------------------------------

    def add_relation(self, mapping: RelationMapping) -> None:
        self._relations[mapping.key()] = mapping

    def teach_relation(
        self, shape: str, operation: Operation, *, learned_from: str
    ) -> RelationMapping:
        mapping = RelationMapping(shape, operation, learned_from)
        self.add_relation(mapping)
        return mapping

    def relation_candidates(self, shape: str) -> tuple[RelationMapping, ...]:
        """**Kandidáti, ne jedno mapování** — přesně jako u kvantifikátoru.

        Holá spona (`cop:NOUN=NOUN`) připouští `member` i `subset` a která
        z nich platí, věta neříká: „Kočka je savec" je podmnožina, „Mourek
        je kočka" členství, a tvar je týž. Vrátit obě a zeptat se je jediná
        poctivá odpověď; vybrat tiše by změnilo, co se zapíše do JÁDRA.
        """
        found = [m for m in self._relations.values() if m.active and m.shape == shape]
        return tuple(sorted(found, key=lambda m: m.key()))

    def revoke_relation(self, key: str) -> RelationMapping | None:
        mapping = self._relations.get(key)
        if mapping is None:
            return None
        updated = mapping.with_status(PatternStatus.REVOKED)
        self._relations[key] = updated
        return updated

    def all_relations(self) -> tuple[RelationMapping, ...]:
        return tuple(sorted(self._relations.values(), key=lambda m: m.key()))

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
            sorted(self._by_key.values(), key=lambda p: p.key())
        )

    def fingerprint(self) -> str:
        """Otisk VÝCHOZÍHO STAVU lexikonu *(W‑51)*.

        Od chvíle, kdy je lexikon výchozím stavem přehrání (B‑20), platí
        determinismus jen PODMÍNĚNĚ: „týž žurnál a týž výchozí stav".
        Který to byl, ale žurnál dosud neříkal — dvě přehrání téhož
        žurnálu s různým lexikonem vypadala obě autoritativně a nic je
        nerozlišilo.

        **Identita běhu nesmí být nic, co se dá dvakrát obsadit.** Táž
        lekce, kterou měřicí vrstva přijala u otisku revize; tady stačí
        otisk lexikonu.

        Počítá se ze `to_json()`, které je setříděné a deterministické —
        druhá serializace by se s ním dřív nebo později rozešla.
        """
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()[:16]

    def to_json(self) -> str:
        return json.dumps(
            {
                "patterns": [p.to_json_object() for p in self.all()],
                "roles": [m.to_json_object() for m in self.all_roles()],
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def from_json(text: str) -> "Lexicon":
        raw = json.loads(text)
        if isinstance(raw, list):  # starší tvar: jen vzory
            return Lexicon(LearnedPattern.from_json_object(i) for i in raw)
        if not isinstance(raw, dict):
            raise ValueError("LEX program musí být objekt se vzory a rolemi")
        return Lexicon(
            (LearnedPattern.from_json_object(i) for i in raw.get("patterns", ())),
            (RoleMapping.from_json_object(i) for i in raw.get("roles", ())),
        )


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
    ("všichni", Mood.UNKNOWN, Operation.FOR_ALL),
    ("nějaký", Mood.UNKNOWN, Operation.EXISTS),
    ("některý", Mood.UNKNOWN, Operation.EXISTS),
    # určitost, NE kvantifikace — „ten" je lemma i pro „ta"/„to"
    ("ten", Mood.UNKNOWN, Operation.DEFINITE),
    # komparátory
    ("nejvýše", Mood.UNKNOWN, Operation.LESS_EQUAL),
    ("nanejvýš", Mood.UNKNOWN, Operation.LESS_EQUAL),
    ("aspoň", Mood.UNKNOWN, Operation.GREATER_EQUAL),
    ("minimálně", Mood.UNKNOWN, Operation.GREATER_EQUAL),
    # strukturní
    ("žádný", Mood.UNKNOWN, Operation.DISJOINT),
    # „žádný" je ZÁMĚRNĚ dvakrát. „Žádný pták není savec" je oddělenost
    # skupin, „Petr nemá žádné auto" je doložené popření o jednom uzlu —
    # a rozliší to stavba věty, ne slovo. Dvě možnosti se proto vrátí obě
    # a rozhoduje doptání; tiše vybrat by znamenalo změnit význam (I‑1).
    ("žádný", Mood.UNKNOWN, Operation.NEGATION),
)


#: Ekvivalence rolí (§ 3.7, § 12/1). Povrchový tvar vlevo, kanonická role
#: vpravo. `v+Loc` je záměrně dvakrát: „v Praze" je `kde`, „v pondělí" je
#: `kdy`, a rozliší to jen význam nominálu, který se nehádá (INV‑11).
_ROLE_SEED: tuple[tuple[str, str], ...] = (
    ("do+Gen", "kam"),
    ("z+Gen", "odkud"),
    ("ze+Gen", "odkud"),
    ("po+Loc", "kudy"),
    # SIGNÁL Z ROZBORU DĚLÁ VLASTNÍ TVAR a ten se NEDĚDÍ *(W‑61)*.
    # Zeměpisné jméno u těchhle předložek znamená totéž co bez signálu —
    # „do Prahy" i „do kina" je `kam` — takže se to tu říká zvlášť.
    #
    # ALE `/rok` SE TU NEOBJEVÍ ANI JEDNOU, A JE TO CELÝ SMYSL TÉHLE
    # ZMĚNY. Dokud byl tvar jeden, platilo `po+Loc → kudy` i pro „Po roce
    # 1990 byly nahrávky digitalizovány." a v korpusu z toho vyšlo
    # `digitalizovaný(kudy:rok)` — cesta místo času. Dědit obecný tvar
    # na signálovaný by tu vadu vrátilo; `po+Loc/rok` proto ŽÁDNÉ
    # mapování nemá a systém se na něj ZEPTÁ.
    ("do+Gen/Geo", "kam"),
    ("z+Gen/Geo", "odkud"),
    ("ze+Gen/Geo", "odkud"),
    # `v+Loc` tu SCHVÁLNĚ NENÍ. „v Praze" je místo, „v pondělí" čas,
    # a tvar je týž — je to táž dvojznačnost jako u holé spony. Dvě
    # hypotézy v seedu situaci NEŘEŠILY: mapování zůstalo dvojznačné
    # navždy, protože i po odpovědi člověka by kandidáti byli pořád dva.
    # Bez nich se systém ZEPTÁ a odpověď tvar rozhodne (N‑3).
    # „v pondělí" je AKUZATIV, ne lokál — a na rozdíl od `v+Loc` je
    # jednoznačný, protože místo se předložkou `v` s akuzativem neurčuje.
    # Doplněno po prvním běhu proti živé službě: ručně psaná nahrávka
    # tvrdila lokál a kvůli tomu projekt vedl jako zásadní mez kolizi
    # dvou určení, která ve skutečnosti neexistuje.
    ("v+Acc", "kdy"),
    ("na+Loc", "kde"),
    ("na+Loc/Geo", "kde"),
    ("Ins", "čím"),
    ("s+Ins", "s kým"),
)


#: Konstrukce, u kterých je jádrová relace JEDNOZNAČNÁ (N‑2).
#:
#: Je tu jen to, co jednoznačné doopravdy je. Holá kladná spona
#: `cop:NOUN=NOUN` tu SCHVÁLNĚ NENÍ: „Kočka je savec" je `subset`, „Mourek
#: je kočka" je `member`, tvar je týž a rozhodnout to za člověka by
#: znamenalo měnit uzávěr báze podle dohadu. Ta se doptá.
#:
#: `cop:NOUN≠NOUN` — záporná spona mezi dvěma OBECNÝMI jmény — jednoznačná
#: je: mluví se o dvou třídách a tvrdí se, že se nepřekrývají. U vlastního
#: jména by to bylo něco jiného (`¬member` o jednom uzlu), a proto je
#: v tvaru slovní druh podmětu.
_RELATION_SEED: tuple[tuple[str, Operation], ...] = (
    ("cop:druh+Gen", Operation.SUBSET),
    ("cop:poddruh+Gen", Operation.SUBSET),
    ("cop:NOUN≠NOUN", Operation.DISJOINT),
    # Vlastní jméno v podmětu JE signál individua, takže členství je tu
    # rozhodnutelné — na rozdíl od `NOUN=NOUN`. Záporná varianta je táž
    # relace se silnou negací (`member̄`), ne oddělenost: oddělenost je
    # vztah dvou TŘÍD a Jana třída není.
    ("cop:PROPN=NOUN", Operation.MEMBER),
    ("cop:PROPN≠NOUN", Operation.MEMBER),
    # „Pondělí je před úterým." Předložka `před` s instrumentálem je
    # v téhle vazbě jednoznačná: mluví o pořadí, ne o místě („před domem"
    # má týž tvar, ale tam je kořen MÍSTO, ne druhý člen uspořádání —
    # rozliší to sort filleru, ne tvar předložky).
    ("cop:před+Ins", Operation.BEFORE),
    # „Micka je Mourek." Dvě VLASTNÍ JMÉNA spojená sponou jsou tvrzení
    # o IDENTITĚ, ne o členství: „Mourek" není třída, do které by Micka
    # patřila. Záporná varianta je táž relace se silnou negací — sporná
    # hrana, přes kterou od M‑1 fakty netečou.
    ("cop:PROPN=PROPN", Operation.SAME_AS),
    ("cop:PROPN≠PROPN", Operation.SAME_AS),
)


def czech_seed(*, learned_from: str = "seed") -> Lexicon:
    """Výchozí český lexikon — všechno jako hypotézy."""
    return Lexicon(
        (
            LearnedPattern(
                trigger=Trigger(lemma=lemma, mood=mood),
                operation=operation,
                learned_from=learned_from,
            )
            for lemma, mood, operation in _SEED
        ),
        (
            RoleMapping(
                surface=surface, canonical=canonical, learned_from=learned_from
            )
            for surface, canonical in _ROLE_SEED
        ),
        (
            RelationMapping(
                shape=shape, operation=operation, learned_from=learned_from
            )
            for shape, operation in _RELATION_SEED
        ),
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
