"""V2 — kaskáda výběru čtení, § 5.2 zadání.

> „generátor kandidátních čtení → tvrdé filtry → konzistence s bází →
> naučené vzory čtení → [volitelný ranker] → doptání"

**Není to překladač.** Kaskáda čtení nevyrábí, ona z nich VYBÍRÁ, a každé
patro umí říct PROČ. Když po všech patrech zůstane víc než jedno čtení,
výsledkem je **otázka**, ne zvolený favorit: tichá volba měnící význam není
cesta nikdy (I‑1).

Motivační případ ze zadání, reálná zeď z dialogů:

```
„Obsahuje citron vitamíny?"
  čtení A: obsahovat(kdo:citron, co:vitamíny)
  čtení B: obsahovat(kdo:vitamíny, co:citron)
  filtr shody: sloveso Sing, „vitamíny" Plur ⇒ B padá   [PROČ: shoda čísla]
```

Morfologie češtiny nese tvrdé signály, které jeden vybraný strom zahazuje —
proto se generují obě čtení a teprve pak se filtruje.

**Proč to není `_lower_copular` / `_verbal` / `_operator`.** Zvláštní větev
na každý druh věty je anti‑vzor, který § 3.0 jmenuje jako důvod existence
conbond4. Tady je jedno pravidlo: najdi hlavu predikace a její závislé
členy. Že sponu nese `cop` a plnovýznamové sloveso `root`, je rozdíl
v tom, KDE je lemma přísudku — ne dvě různé cesty ke dvěma různým
strukturám.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from .lexicon import Lexicon, Mood, StructuralSignature
from .oracle import Reading, Token
from .storage import ResolvedGraphView

#: Strukturní jádro rolí je uzavřené (§ 12/1): `kdo` a `co` z podmětu
#: a předmětu. Bez něj nejde psát algebra restrikcí.
ROLE_SUBJECT = "kdo"
ROLE_OBJECT = "co"
#: Okolnosti se pojmenovávají POVRCHOVĚ podle předložky nebo pádu —
#: sémantika se nehádá (INV‑11). Ekvivalence rolí („kudy" × „po čem") se
#: učí dialogem jako odvolatelná data, ne zadrátovaným seznamem.
ROLE_MANNER = "jak"


@dataclass(frozen=True, slots=True)
class Mention:
    """Úsek promluvy s proveniencí — nezpochybnitelná kotva (§ 3.2).

    Tvrzení se kotví na zmínku, ne přímo na uzel; převod zmínky na term
    je práce V3, ne kaskády."""

    lemma: str
    form: str
    token_index: int
    upos: str
    feats: tuple[tuple[str, str], ...] = ()

    def feat(self, name: str) -> str | None:
        for key, value in self.feats:
            if key == name:
                return value
        return None

    def __str__(self) -> str:
        return f"zmínka „{self.form}“ (token {self.token_index})"


@dataclass(frozen=True, slots=True)
class Predication:
    """Čtení převedené na strukturu: lemma přísudku a role → zmínka.

    Role jsou kanonicky setříděné, aby dvě stejná čtení byla týž objekt
    (determinismus, I‑22)."""

    predicate: str
    roles: tuple[tuple[str, Mention], ...]
    mood: Mood = Mood.UNKNOWN

    def __post_init__(self) -> None:
        names = [name for name, _ in self.roles]
        if len(names) != len(set(names)):
            # Táž kontrola jako v `Atom`. Bez ní by V2 vyrobila čtení,
            # které V3 nikdy nepřevede na platný atom — jádro duplicitní
            # roli odmítá, takže by se chyba objevila až o vrstvu dál.
            raise ValueError(
                f"čtení {self.predicate!r} má roli vícekrát: "
                f"{sorted(n for n in names if names.count(n) > 1)}"
            )

    def role(self, name: str) -> Mention | None:
        for role_name, mention in self.roles:
            if role_name == name:
                return mention
        return None

    def signature(self) -> str:
        names = ",".join(name for name, _ in self.roles)
        return f"{self.predicate}({names})"

    def __str__(self) -> str:
        body = ", ".join(
            f"{name}:{mention.lemma}" for name, mention in self.roles
        )
        return f"{self.predicate}({body})"


@dataclass(frozen=True, slots=True)
class Candidate:
    """Kandidátní čtení plus záznam, odkud se vzalo."""

    predication: Predication
    origin: str

    def __str__(self) -> str:
        return f"{self.predication}  [{self.origin}]"


@dataclass(frozen=True, slots=True)
class Verdict:
    """Výsledek kaskády.

    `survivors` může být prázdné (nic nepřežilo → poctivé „tuhle větu
    neumím přečíst") nebo delší než jedno (→ `question`). Jedno čtení
    znamená rozhodnuto — a `trace` říká, které patro to rozhodlo."""

    survivors: tuple[Candidate, ...]
    trace: tuple[str, ...]
    question: str | None = None

    @property
    def decided(self) -> Candidate | None:
        return self.survivors[0] if len(self.survivors) == 1 else None

    def render(self) -> tuple[str, ...]:
        lines = [f"kandidátů: {len(self.survivors)}"]
        lines.extend(f"  - {candidate}" for candidate in self.survivors)
        lines.extend(f"  {step}" for step in self.trace)
        if self.question:
            lines.append(f"  ? {self.question}")
        return tuple(lines)


# --------------------------------------------------------------------------
# Generátor kandidátních čtení
# --------------------------------------------------------------------------


def _mention(token: Token) -> Mention:
    return Mention(
        lemma=token.lemma,
        form=token.form,
        token_index=token.index,
        upos=token.upos,
        feats=token.feats,
    )


def _predicate_head(reading: Reading) -> tuple[Token, Token] | None:
    """Vrátí `(nositel lemmatu přísudku, hlava predikace)`.

    Jedno pravidlo pro obě stavby: u plnovýznamového slovesa je to týž
    token, u spony nese lemma `cop` a hlavou je jmenná část. Není to
    zvláštní větev na druh věty — je to jen otázka, KDE lemma leží.
    """
    root = reading.root()
    if root is None:
        return None
    copulas = [t for t in reading.children(root.index) if t.deprel == "cop"]
    if copulas:
        return copulas[0], root
    return root, root


def _role_for(token: Token) -> str | None:
    """Povrchové pojmenování role (§ 12/1). Sémantika se nehádá."""
    if token.deprel == "nsubj":
        return ROLE_SUBJECT
    if token.deprel in ("obj", "iobj"):
        return ROLE_OBJECT
    if token.deprel in ("amod", "advmod"):
        return ROLE_MANNER
    if token.deprel in ("obl", "nmod", "xcomp", "ccomp"):
        return token.deprel
    return None


#: Deprel, které nesou jádrové nominály. Jen z nich se skládají dvojice
#: `kdo`/`co` — okolnosti se nepermutují.
NOMINAL_DEPRELS = ("nsubj", "obj", "iobj")


def generate(reading: Reading, *, mood: Mood = Mood.UNKNOWN) -> tuple[Candidate, ...]:
    """Kombinatorický generátor kandidátních čtení.

    **Role se skládají z NOMINÁLNÍCH KANDIDÁTŮ, ne z toho, co parser
    označil za podmět.** To je celý smysl § 5.2: reálná zeď z dialogů je,
    že „Obsahuje citron vitamíny?" dostane rozbor **bez podmětu** — oba
    nominály jako `obj`, protože nominativ je tvarově shodný s akuzativem.
    Kdyby se záměna generovala jen tam, kde už podmět je, případ ze zadání
    by neprošel a přeživší čtení by mělo dvě role téhož jména.

    Pro **dva** jádrové nominály se generují obě přiřazení; parserovo
    vlastní čtení je první. Pro tři a víc se drží, co dal parser —
    permutovat cokoli by přestalo být „generátor kandidátů" a začalo být
    hádání, a jeden nominál by se přiřazením dvojice ztratil.
    """
    head = _predicate_head(reading)
    if head is None:
        return ()
    carrier, anchor = head

    nominals: list[Token] = []
    fixed: list[tuple[str, Mention]] = []
    for token in reading.children(anchor.index):
        if token.deprel == "cop":
            continue
        if token.deprel in NOMINAL_DEPRELS:
            nominals.append(token)
            continue
        role = _role_for(token)
        if role is not None:
            fixed.append((role, _mention(token)))

    variants: list[tuple[tuple[str, Mention], ...]] = []
    if carrier is not anchor:
        # Spona: jmenná část JE obsah — to říká stavba věty, ne odhad.
        # Nominály tedy plní jen podmět.
        fixed.append((ROLE_OBJECT, _mention(anchor)))
        variants = [((ROLE_SUBJECT, _mention(token)),) for token in nominals] or [()]
    elif len(nominals) == 2:
        first, second = nominals
        variants = [
            ((ROLE_SUBJECT, _mention(a)), (ROLE_OBJECT, _mention(b)))
            for a, b in ((first, second), (second, first))
        ]
    else:
        kept = tuple(
            (_role_for(token) or ROLE_SUBJECT, _mention(token))
            for token in nominals
        )
        variants = [kept]

    candidates: list[Candidate] = []
    for variant in variants:
        if not variant and not fixed:
            continue
        roles = tuple(sorted((*fixed, *variant), key=lambda pair: pair[0]))
        follows_parser = all(
            _role_for(
                next(t for t in nominals if t.index == mention.token_index)
            )
            in (role, None)
            for role, mention in variant
        )
        if follows_parser:
            origin = "rozbor parseru"
        elif any(token.deprel == "nsubj" for token in nominals):
            origin = "záměna kdo/co (nominativ = akuzativ)"
        else:
            # Parser podmět vůbec nedal, takže není co zaměňovat — čtení
            # ho doplňuje. Popisek to musí říct, jinak trace lže o tom,
            # odkud se role vzala.
            origin = "doplnění podmětu (parser ho nedal)"
        candidates.append(
            Candidate(Predication(carrier.lemma, roles, mood), origin=origin)
        )
    # Parserovo čtení jde první — orákulum navrhuje, kaskáda rozhoduje.
    candidates.sort(key=lambda c: (c.origin != "rozbor parseru", str(c.predication)))
    return tuple(candidates)


# --------------------------------------------------------------------------
# Patra kaskády
# --------------------------------------------------------------------------

#: Patro dostane přeživší kandidáty a vrátí přeživší plus vysvětlení, když
#: někoho vyřadilo. `None` znamená „nerozhodlo jsem nic".
Tier = Callable[[tuple[Candidate, ...], Reading], tuple[tuple[Candidate, ...], str | None]]


def agreement_tier(
    candidates: tuple[Candidate, ...], reading: Reading
) -> tuple[tuple[Candidate, ...], str | None]:
    """Tvrdý filtr: shoda podmětu s přísudkem v čísle.

    Tohle je patro, které rozhodne motivační případ **bez jakéhokoli
    učení** — „obsahuje" je singulár, „vitamíny" plurál, takže vitamíny
    podmět být nemohou.
    """
    head = _predicate_head(reading)
    if head is None:
        return candidates, None
    verb_number = head[0].feat("Number")
    if verb_number is None:
        return candidates, None
    survivors = []
    for candidate in candidates:
        subject = candidate.predication.role(ROLE_SUBJECT)
        number = subject.feat("Number") if subject else None
        if number is None or number == verb_number:
            survivors.append(candidate)
    if len(survivors) == len(candidates):
        return candidates, None
    return tuple(survivors), (
        f"[PROČ: shoda čísla — přísudek {verb_number}, "
        f"podmět musí být týž]"
    )


def case_tier(
    candidates: tuple[Candidate, ...], reading: Reading
) -> tuple[tuple[Candidate, ...], str | None]:
    """Tvrdý filtr: pádová mřížka. Podmět nominativ, předmět akuzativ."""
    expected = {ROLE_SUBJECT: "Nom", ROLE_OBJECT: "Acc"}
    survivors = []
    for candidate in candidates:
        ok = True
        for role, want in expected.items():
            mention = candidate.predication.role(role)
            case = mention.feat("Case") if mention else None
            if case is not None and case != want:
                ok = False
                break
        if ok:
            survivors.append(candidate)
    if len(survivors) == len(candidates) or not survivors:
        return candidates, None
    return tuple(survivors), "[PROČ: pádová mřížka — podmět Nom, předmět Acc]"


def base_consistency_tier(view: ResolvedGraphView) -> Tier:
    """Konzistence s bází: přednost má čtení, jehož vztahová signatura
    v grafu už existuje.

    Statistika a báze **navrhují**, nerozhodují (I‑2) — patro proto smí
    jen zúžit množinu, nikdy ji doplnit.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        known = [
            candidate
            for candidate in candidates
            if view.known_members(candidate.predication.predicate)
        ]
        if not known or len(known) == len(candidates):
            return candidates, None
        return tuple(known), (
            "[PROČ: vztah téhož jména už v bázi je]"
        )

    return tier


def lexicon_tier(lexicon: Lexicon) -> Tier:
    """Naučené vzory čtení — data s proveniencí a statusem, odvolatelná.

    Nerozhoduje sama: když má spouštěcí slovo víc kandidátních operací,
    patro to **zapíše do trace** a nechá rozhodnutí na doptání.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        for token in reading.tokens:
            signature = StructuralSignature(
                lemma=token.lemma,
                mood=candidates[0].predication.mood if candidates else Mood.UNKNOWN,
                upos=token.upos,
                deprel=token.deprel,
            )
            matches = lexicon.candidates(signature)
            if len(matches) > 1:
                notes.append(
                    f"[POZOR: {token.lemma!r} má víc čtení — "
                    + ", ".join(m.operation.value for m in matches)
                    + "]"
                )
        return candidates, "; ".join(notes) if notes else None

    return tier


# --------------------------------------------------------------------------
# Kaskáda
# --------------------------------------------------------------------------

#: Tvrdá patra, která nepotřebují bázi ani naučené vzory. Pořadí je pořadí
#: ze § 5.2: morfologie dřív než cokoli statistického.
HARD_TIERS: tuple[Tier, ...] = (agreement_tier, case_tier)


def cascade(
    reading: Reading,
    *,
    mood: Mood = Mood.UNKNOWN,
    tiers: Sequence[Tier] = HARD_TIERS,
) -> Verdict:
    """Projde patra a vrátí verdikt s tím, které patro co rozhodlo.

    Vrací **otázku**, ne favorita, když po všech patrech zbývá víc čtení.
    Doptání je plnohodnotný tah dialogu a zdroj učení (I‑7).
    """
    candidates = generate(reading, mood=mood)
    trace: list[str] = [f"generátor: {len(candidates)} čtení"]
    if not candidates:
        return Verdict(
            survivors=(),
            trace=tuple(trace),
            question=None,
        )
    for tier in tiers:
        candidates, why = tier(candidates, reading)
        if why:
            trace.append(f"{why} → zbývá {len(candidates)}")
        if len(candidates) <= 1:
            break
    question = None
    if len(candidates) > 1:
        options = " / ".join(str(c.predication) for c in candidates)
        question = f"Čtu to jako: {options} — které z toho?"
    return Verdict(survivors=candidates, trace=tuple(trace), question=question)
