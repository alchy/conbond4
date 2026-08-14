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

from dataclasses import dataclass, replace
from typing import Callable, Sequence

from .ast import UNQUANTIFIED_ROLES, Quantifier
from .lexicon import (
    Lexicon,
    Mood,
    Operation,
    StructuralSignature,
)
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
class RoleReading:
    """Role čtení: jméno, zmínka, a **jak je fillér kvantifikovaný**.

    Kvantifikátor je vlastní pole, ne součást `Mention`, schválně. Zmínka
    je nezpochybnitelná kotva — úsek promluvy, který tam prostě je.
    Kvantifikátor je oproti tomu **výklad** té zmínky, a ten se může
    ukázat jako špatný a jde odvolat. Kdyby seděly v jednom objektu,
    nešlo by z čtení poznat, co dal rozbor a co dovodila kaskáda.

    `quantifier is None` znamená „ještě nerozhodnuto", ne „žádný". Jádro
    bez kvantifikátoru skupinu do role nepustí (`UnquantifiedRole`), takže
    tenhle stav je otevřená otázka, kterou musí někdo zodpovědět — ne
    hodnota, se kterou se dá počítat.
    """

    name: str
    mention: Mention
    quantifier: Quantifier | None = None
    #: Slovo, ze kterého kvantifikátor plyne. `None` = plyne z tvaru.
    determiner: Mention | None = None
    #: Odkud se kvantifikátor vzal — do stopy a do vysvětlení (I‑14).
    source: str = ""
    #: Tvar, na který se čeká odpověď, dokud `quantifier` chybí.
    pending: StructuralSignature | None = None
    #: NA CO se čeká. Dvě otevřené role nemusí čekat na totéž: holé jméno
    #: čeká na kvantifikátor, „ta učitelka" na to, KTERÝ uzel to je. Slít
    #: obojí do jedné otázky by znamenalo ptát se na špatnou věc.
    awaiting: str = ""
    #: Uzel, který na otevřenou referenci ROZHODL ČLOVĚK (tah `?→`).
    #: Nese se v roli, takže je součástí žurnálu — a `replay` se proto
    #: neptá podruhé (M‑4).
    resolved: str = ""

    def rendered(self) -> str:
        mark = self.quantifier.value if self.quantifier else ""
        return f"{self.name}:{mark}{self.mention.lemma}"


@dataclass(frozen=True, slots=True)
class Predication:
    """Čtení převedené na strukturu: lemma přísudku a role → zmínka.

    Role jsou kanonicky setříděné, aby dvě stejná čtení byla týž objekt
    (determinismus, I‑22)."""

    predicate: str
    roles: tuple[RoleReading, ...]
    mood: Mood = Mood.UNKNOWN
    #: SILNÁ negace `p̄` (§ 4), ne nepřítomnost důkazu. „Tučňák nelétá"
    #: je doložené tvrzení o tučňácích, ne přiznání, že o nich nic nevíme —
    #: a splynout to nesmí (I‑21).
    negated: bool = False

    def __post_init__(self) -> None:
        names = [r.name for r in self.roles]
        if len(names) != len(set(names)):
            # Táž kontrola jako v `Atom`. Bez ní by V2 vyrobila čtení,
            # které V3 nikdy nepřevede na platný atom — jádro duplicitní
            # roli odmítá, takže by se chyba objevila až o vrstvu dál.
            raise ValueError(
                f"čtení {self.predicate!r} má roli vícekrát: "
                f"{sorted(n for n in names if names.count(n) > 1)}"
            )

    def role(self, name: str) -> Mention | None:
        found = self.reading(name)
        return found.mention if found else None

    def reading(self, name: str) -> RoleReading | None:
        for role in self.roles:
            if role.name == name:
                return role
        return None

    def open_roles(self) -> tuple[RoleReading, ...]:
        """Role, které na něco teprve čekají — na kvantifikátor nebo na
        rozřešení odkazu."""
        return tuple(r for r in self.roles if r.awaiting)

    def signature(self) -> str:
        names = ",".join(r.name for r in self.roles)
        return f"{self.predicate}({names})"

    def __str__(self) -> str:
        bar = "¬" if self.negated else ""
        return f"{bar}{self.predicate}({', '.join(r.rendered() for r in self.roles)})"


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
    #: Role, které čekají na kvantifikátor, jako `(jméno role, tvar)`.
    #: Prázdné neznamená „vše rozhodnuto" u nerozhodnutého čtení — počítá
    #: se jen z jediného přeživšího, protože ptát se na kvantifikátor
    #: v čtení, které možná není to pravé, je otázka na špatnou věc.
    pending: tuple[tuple[str, StructuralSignature], ...] = ()
    #: Významové členy, které nedostaly roli, jako `(tvar slova, tvar role)`.
    #: „Pokud existuje" z N‑5: ptá se jen na to, co v rozboru SKUTEČNĚ je.
    lost: tuple[tuple[str, str], ...] = ()

    @property
    def decided(self) -> Candidate | None:
        """Vybrané čtení, **a jen když zbylo právě jedno**.

        Nula znamená „tuhle větu neumím přečíst", dva a víc znamená otázku.
        Vracet v obou případech `survivors[0]` by z kaskády udělalo hadače
        s dobrým vysvětlením — a tichá volba měnící význam není cesta
        nikdy (I‑1)."""
        return self.survivors[0] if len(self.survivors) == 1 else None

    @property
    def complete(self) -> bool:
        """Rozhodnuto A bez otevřených rolí — teprve tohle jde poslat V3."""
        decided = self.decided
        return decided is not None and not decided.predication.open_roles()

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


def complex_predicate(reading: Reading, anchor: Token) -> Token | None:
    """Infinitiv, který s řídicím slovesem tvoří JEDEN přísudek.

    Třetí tvar přísudku vedle plnovýznamového slovesa a spony — a je to
    táž otázka, kde leží lemma: „nesmí dostat penicilin" nese modalitu
    v kořeni a OBSAH v infinitivu. Bez tohohle se `dostat` odsune do
    role `xcomp`, `penicilin` zůstane viset pod ním a věta se nezakotví,
    protože sloveso není uzel žádného sortu.

    **Že je to jeden přísudek, říká specifikace, ne odhad.** Doména
    farmaka (§ 6.12) modeluje závěr jako JEDEN predikát
    `smí_dostat(who, what)` se silnou negací — ne jako `smět` s vnořeným
    dějem. Modalita je součástí jména vztahu.

    **Nic se nezahazuje.** Složené lemma nese obě části (`smět_dostat`),
    takže se z věty neztrácí ani modalita, ani obsah; mění se jen to,
    KDE je systém hledá.

    Rozpoznává se **ze stavby, ne ze seznamu sloves**: kořen má
    infinitivní `xcomp`. Zavřený seznam modálních sloves by byl domněnka
    o češtině navíc, a tahle podmínka je přímo v rozboru.
    """
    for child in reading.children(anchor.index):
        if (
            base_deprel(child.deprel) == "xcomp"
            and child.feat("VerbForm") == "Inf"
        ):
            return child
    return None


#: Deprel okolností, které se pojmenovávají povrchově z předložky a pádu.
#: Porovnává se ZÁKLAD, ne celý řetězec — viz `base_deprel`.
CIRCUMSTANCE_DEPRELS = ("obl", "nmod")

#: Závislosti, které NEJSOU ztracený člen, i když je slovní druh
#: významový. `expl` je zvratná částice („se" v „myje se") — patří ke
#: slovesu, ne do role, a hlásit ji jako ztrátu by byl šum.
NOT_A_LOST_MEMBER = ("expl", "cop", "aux", "punct", "case", "det")


def base_deprel(deprel: str) -> str:
    """Základ závislosti bez UD podtypu: `obl:arg` → `obl`.

    **Odděluje VIDITELNOST od POJMENOVÁNÍ** (N‑1). Univerzální závislosti
    používají podtypy (`obl:arg`, `nsubj:pass`, `nmod:poss`) a porovnání
    na přesnou shodu je na nich slepé — token propadl a skončil jako
    `[ZAHOZENO]`, u podmětu rovnou jako nečitelná věta. Celý trpný rod
    byl pro systém neviditelný.

    **Podtyp se tím ale NEZAHAZUJE**, a to je ta podstatná půlka.
    `nsubj:pass` NENÍ `nsubj`: v „Auto bylo koupeno Filipem" je `auto`
    trpný podmět, tedy to KUPOVANÉ, a agens je `Filipem`. Kdyby se
    podtyp ztratil, systém by mlčky přiřadil „kdo" tomu, kdo nic nedělá
    — a to je horší než dnešní odmítnutí, protože dnes aspoň řekne, že
    neví. Základ tedy rozhoduje, jestli je token KANDIDÁT na roli;
    jméno role dostane až z celého deprelu, a co znamená, se učí.
    """
    return deprel.split(":", 1)[0]


def surface_role(token: Token, reading: Reading) -> str:
    """Povrchové pojmenování okolnosti z PŘEDLOŽKY A PÁDU (§ 12/1).

    Pojmenovat okolnost jejím `deprel` nestačí: „v pondělí" i „do Prahy"
    jsou obě `obl`, takže by dostaly totéž jméno role a věta by spadla na
    duplicitě — a dvě příslovečná určení má v češtině obrovská část vět.

    Rozbor všechno potřebné dodává: u okolnosti visí dítě s `deprel=case`
    nesoucí lemma předložky a nominál nese `Case`. Sémantika se přitom
    nehádá (INV‑11) — `v+Loc` je popis tvaru, ne významu. Že `v+Loc`
    znamená jednou `kde` a jednou `kdy`, řeší naučené mapování rolí, ne
    tenhle kód.
    """
    preposition = next(
        (
            child.lemma
            for child in reading.children(token.index)
            if base_deprel(child.deprel) == "case"
        ),
        None,
    )
    case = token.feat("Case")
    # PODTYP JE SOUČÁST TVARU, ne ozdoba. „v pondělí" je `obl`, tedy
    # volné určení, kdežto „věří v úspěch" je `obl:arg`, tedy PŘEDMĚT
    # slovesa — a rozbor to rozlišuje. Kdyby se obojí jmenovalo `v+Acc`,
    # naučené mapování `v+Acc → kdy` by z „věří v úspěch" udělalo časový
    # údaj. Tu chybu jsem si vyrobil sám, než se podtyp začal brát v potaz.
    _, _, subtype = token.deprel.partition(":")
    suffix = f":{subtype}" if subtype else ""
    if preposition and case:
        return f"{preposition}+{case}{suffix}"
    if preposition:
        return f"{preposition}{suffix}"
    if case:
        return f"{case}{suffix}"
    return token.deprel


def _role_for(token: Token, reading: Reading) -> str | None:
    """Jméno role pro závislý člen. Jádro rolí je uzavřené, okolnosti
    povrchové (§ 12/1).

    **Podtyp mění jméno.** Holé `nsubj` je `kdo`; `nsubj:pass` dostane
    své vlastní, povrchové jméno, protože trpný podmět není konatel a
    ztotožnit je by byl dohad o významu (I‑2, INV‑11). Co takové jméno
    znamená, se učí jako `RoleMapping` — stejně jako u `do+Gen → kam`.
    """
    base = base_deprel(token.deprel)
    subtyped = token.deprel != base

    if base == "nsubj":
        return token.deprel if subtyped else ROLE_SUBJECT
    if base in ("obj", "iobj"):
        return token.deprel if subtyped else ROLE_OBJECT
    if base in ("amod", "advmod"):
        return ROLE_MANNER
    if base in CIRCUMSTANCE_DEPRELS:
        # Okolnost se jmenuje z předložky a pádu, takže je na podtypu
        # nezávislá sama od sebe: `obl` i `obl:arg` dají „v+Acc".
        return surface_role(token, reading)
    if base in ("xcomp", "ccomp"):
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

    # Složený přísudek: lemma nese kořen I infinitiv, a členy se sbírají
    # z OBOU. Předmět „nesmí dostat penicilin" visí pod infinitivem, ne
    # pod kořenem — brát jen kořenové děti by ho ztratilo.
    inner = complex_predicate(reading, anchor)
    lemma = f"{carrier.lemma}_{inner.lemma}" if inner else carrier.lemma
    members = list(reading.children(anchor.index))
    if inner is not None:
        members = [t for t in members if t.index != inner.index]
        members.extend(reading.children(inner.index))

    nominals: list[Token] = []
    fixed: list[RoleReading] = []
    for token in members:
        if token.deprel == "cop":
            continue
        # Do ZÁMĚNY kdo/co jdou jen HOLÉ jádrové členy. Podtypovaný
        # (`nsubj:pass`) je sice vidět, ale permutovat ho by znamenalo
        # tvrdit, že je zaměnitelný s konatelem — a právě to o trpném
        # podmětu neplatí.
        if token.deprel in NOMINAL_DEPRELS:
            nominals.append(token)
            continue
        role = _role_for(token, reading)
        if role is not None:
            fixed.append(RoleReading(role, _mention(token)))

    variants: list[tuple[RoleReading, ...]] = []
    if carrier is not anchor:
        # Spona: jmenná část JE obsah — to říká stavba věty, ne odhad.
        # Nominály tedy plní jen podmět.
        fixed.append(RoleReading(ROLE_OBJECT, _mention(anchor)))
        variants = [(RoleReading(ROLE_SUBJECT, _mention(t)),) for t in nominals] or [()]
    elif len(nominals) == 2:
        first, second = nominals
        variants = [
            (RoleReading(ROLE_SUBJECT, _mention(a)), RoleReading(ROLE_OBJECT, _mention(b)))
            for a, b in ((first, second), (second, first))
        ]
    else:
        kept = tuple(
            RoleReading(_role_for(token, reading) or ROLE_SUBJECT, _mention(token))
            for token in nominals
        )
        variants = [kept]

    candidates: list[Candidate] = []
    for variant in variants:
        if not variant and not fixed:
            continue
        roles = tuple(sorted((*fixed, *variant), key=lambda r: r.name))
        names = [r.name for r in roles]
        if len(names) != len(set(names)):
            # Dvě určení se stejným povrchovým tvarem („v Praze v pondělí").
            # Rozlišit by je šlo jen podle významu nominálu, a ten se nehádá
            # (INV‑11). Tahle varianta se proto negeneruje a kaskáda se ptá.
            continue
        follows_parser = all(
            _role_for(
                next(t for t in nominals if t.index == r.mention.token_index),
                reading,
            )
            in (r.name, None)
            for r in variant
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
            Candidate(Predication(lemma, roles, mood), origin=origin)
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
        number = subject.feat("Number") if subject is not None else None
        if number is None or number == verb_number:
            survivors.append(candidate)
    if len(survivors) == len(candidates):
        return candidates, None
    return tuple(survivors), (
        f"[PROČ: shoda čísla — přísudek {verb_number}, "
        f"podmět musí být týž]"
    )


#: Determinátory, které v češtině nesou zápornou shodu. Sloveso je u nich
#: záporné taky, a přesto je to JEDNA negace.
NEGATIVE_CONCORD_LEMMAS = ("žádný", "nikdo", "nic", "nijaký")


def negation_tier(
    candidates: tuple[Candidate, ...], reading: Reading
) -> tuple[tuple[Candidate, ...], str | None]:
    """Negace z `Polarity=Neg` — L‑4. Tvrdý signál, žádné učení.

    Česká negace je předpona přísudku (`nelétá`, `nesmí`) a rozbor ji dává
    jako `Polarity=Neg`. Je to morfologie stejně jako shoda čísla nebo pád,
    takže se sem nic neučí — není co, `Polarity=Neg` má jeden význam.

    **Je to SILNÁ negace `p̄`, ne nepřítomnost důkazu (I‑21).** „Tučňák
    nelétá" je doložené tvrzení o tučňácích; „o tučňácích nic nevím" je
    něco úplně jiného a jádro to drží jako dva různé stavy. Kdyby se
    zápor přečetl jako mezera, dialog E by přestal dávat `CONFLICT` a
    začal dávat „nevím".

    **Záporná shoda se nesčítá.** „Petr nemá žádné auto" má zápor dvakrát
    — na slovese i na determinátoru — a je to JEDNA negace, ne dvě. Sčítat
    je by z popření udělalo tvrzení, což je přesně opačný význam.
    """
    head = _predicate_head(reading)
    if head is None or head[0].feat("Polarity") != "Neg":
        return candidates, None
    concord = [
        token.form
        for token in reading.tokens
        if token.lemma in NEGATIVE_CONCORD_LEMMAS
    ]
    note = f"[ZÁPOR: „{head[0].form}“ nese Polarity=Neg — silná negace p̄]"
    if concord:
        note = (
            f"[ZÁPOR: „{head[0].form}“ + „{'“, „'.join(concord)}“ — záporná "
            f"shoda, tedy JEDNA negace, ne dvě]"
        )
    return (
        tuple(
            Candidate(
                replace(candidate.predication, negated=True),
                origin=candidate.origin,
            )
            for candidate in candidates
        ),
        note,
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


#: Důvod, proč báze čtení odmítá — nebo `None`, když žádný nemá.
#: Injektuje se zvenčí, protože rozhodnout se dá až nad ZAKOTVENOU
#: formulí, a zakotvení je V3. Kaskáda o něm nemá vědět.
SemanticCheck = Callable[[Predication], str | None]


def base_consistency_tier(reject: SemanticCheck) -> Tier:
    """Konzistence s bází — **jen z DEFINOVANÉHO sémantického důvodu** (K‑7).

    Dřív tohle patro nechávalo čtení, jejichž vztah už v bázi je, a
    ostatní vyhazovalo. To ale není konzistence, to je POPULARITA: báze
    dává přednost tomu, co už jednou přečetla, čímž si své dřívější
    čtení potvrzuje. Self‑confirming loop — čím víc se systém splete
    stejným směrem, tím jistěji se splete znovu, a nikdy se to
    neprojeví jako chyba, protože každý další krok „sedí".

    Báze proto smí čtení eliminovat jen z důvodu, který jde pojmenovat:

    * **formální konflikt** — zakotvená formule by tvrdila `p` tam, kde
      je doložené `p̄`;
    * **typová chyba** — fillér nesedí do sortu role;
    * **nesplnitelný constraint** — třeba porušená oddělenost skupin.

    „Tahle interpretace se mi nehodí" mezi ně nepatří.

    **Nejde‑li čtení zakotvit, NEELIMINUJE SE.** Nedá se o něm nic
    tvrdit, a mlčky ho vyřadit by byla táž tichá volba v jiném kabátě.
    Praktický důsledek: dokud role čekají na kvantifikátor, tohle patro
    většinou neudělá nic — a je to poctivější než dřívější aktivita,
    která rozhodovala z nesprávného důvodu.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        reasons = [(c, reject(c.predication)) for c in candidates]
        survivors = tuple(c for c, why in reasons if why is None)
        if len(survivors) == len(candidates):
            return candidates, None
        if not survivors:
            # Odmítnout VŠECHNO by znamenalo tvrdit, že věta nedává smysl,
            # jenže rozporná věta smysl dává — jen se s bází neshoduje.
            # To je nález pro člověka, ne důvod k mlčení.
            note = "; ".join(why for _, why in reasons if why)
            what = "čtení je" if len(candidates) == 1 else "každé čtení je"
            return candidates, f"[POZOR: {what} v rozporu s bází — {note}]"
        dropped = "; ".join(why for _, why in reasons if why)
        return survivors, f"[PROČ: rozpor s bází — {dropped}]"

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

def role_mapping_tier(lexicon: Lexicon) -> Tier:
    """Přejmenuje povrchovou roli na kanonickou podle NAUČENÉHO mapování.

    Přepisuje jen tam, kde je mapování **jednoznačné** a kde nové jméno
    nekoliduje. Má‑li povrchový tvar víc kandidátů (`v+Loc` je `kde` i
    `kdy`), patro to zapíše do trace a jméno nechá povrchové — vybrat tiše
    by znamenalo uhádnout význam nominálu, což INV‑11 zakazuje.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        renamed: list[Candidate] = []
        for candidate in candidates:
            roles: list[RoleReading] = []
            taken = {r.name for r in candidate.predication.roles}
            for role in candidate.predication.roles:
                options = lexicon.role_candidates(role.name)
                if len(options) > 1:
                    notes.append(
                        f"[POZOR: {role.name} může být "
                        + " nebo ".join(o.canonical for o in options)
                        + "]"
                    )
                    roles.append(role)
                    continue
                if len(options) == 1 and options[0].canonical not in taken:
                    taken.discard(role.name)
                    taken.add(options[0].canonical)
                    roles.append(replace(role, name=options[0].canonical))
                    continue
                roles.append(role)
            renamed.append(
                Candidate(
                    # `replace`, ne nový `Predication`. Stavět ho znovu
                    # znamená vyjmenovat všechna pole — a co se zapomene,
                    # tiše zmizí. Takhle zmizel zápor, dokud to nechytil
                    # test: „Tučňák nelétá" se přejmenováním rolí změnilo
                    # na „Tučňák létá".
                    replace(
                        candidate.predication,
                        roles=tuple(sorted(roles, key=lambda r: r.name)),
                    ),
                    origin=candidate.origin,
                )
            )
        return tuple(renamed), "; ".join(notes) if notes else None

    return tier


#: Na co otevřená role čeká.
AWAITING_QUANTIFIER = "kvantifikátor"
AWAITING_REFERENCE = "odkaz"

#: Zmínky, které se v roli stanou uzlem nebo skupinou, a potřebují proto
#: kvantifikátor. **Přívlastek je mezi nimi**: „modrý" je podle § 6.12
#: (dialog F) `group("modrý")`, tedy skupina jako každá jiná — a skupina
#: bez kvantifikátoru se do role nedostane.
QUANTIFIED_UPOS = ("NOUN", "PROPN", "PRON", "ADJ")

#: Překlad z uzavřeného menu do jádra. `DEFINITE` tu ZÁMĚRNĚ není: určitost
#: není kvantifikace, odkazuje na už existující uzel a rozřešit ten odkaz
#: je práce V3. Kvantifikátor se z ní proto neodvozuje — vyplyne až z toho,
#: který uzel to je.
QUANTIFIER_OF: dict[Operation, Quantifier] = {
    Operation.FOR_ALL: Quantifier.FOR_ALL,
    Operation.EXISTS: Quantifier.EXISTS,
    Operation.SELF: Quantifier.SELF,
}


def _determiner_of(mention: Mention, reading: Reading) -> Token | None:
    """Determinátor zmínky — dítě s `deprel=det`."""
    return next(
        (
            child
            for child in reading.children(mention.token_index)
            if child.deprel == "det"
        ),
        None,
    )


def _token_at(index: int, reading: Reading) -> Token | None:
    return next((t for t in reading.tokens if t.index == index), None)


def lost_role_tier(lexicon: Lexicon) -> Tier:
    """Doplní roli ztracenému členu, **je‑li pro jeho tvar naučená** (N‑5).

    Jediné patro, které čtení ROZŠIŘUJE. Ostatní vybírají nebo
    přejmenovávají; tohle přidá roli, která v rozboru nemá jméno, ale
    člověk jí jméno dal.

    Je to táž smyčka jako u kvantifikátoru: **zeptat se → dostat odpověď
    jako tah → naučit tvar → přečíst větu znovu.** A ze stejného důvodu:
    věta, ze které vypadl předmět, se nemá zapsat oseknutá — má se
    dokončit.

    **Bez naučeného tvaru se nic nedoplňuje.** Uhádnout roli z cesty
    v rozboru by znamenalo vymyslet si význam (INV‑11); ztráta se pak
    jen ohlásí a zeptá.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        out: list[Candidate] = []
        for candidate in candidates:
            roles = list(candidate.predication.roles)
            taken = {r.name for r in roles}
            for token, shape in lost_members(reading, candidate.predication):
                options = lexicon.role_candidates(shape)
                if len(options) > 1:
                    notes.append(
                        f"[POZOR: tvar {shape} může být "
                        + " nebo ".join(o.canonical for o in options)
                        + "]"
                    )
                    continue
                if not options or options[0].canonical in taken:
                    continue
                roles.append(RoleReading(options[0].canonical, _mention(token)))
                taken.add(options[0].canonical)
                notes.append(
                    f"[DOPLNĚNO: „{token.form}“ → role {options[0].canonical} "
                    f"(naučený tvar {shape})]"
                )
            out.append(
                Candidate(
                    replace(
                        candidate.predication,
                        roles=tuple(sorted(roles, key=lambda r: r.name)),
                    ),
                    origin=candidate.origin,
                )
            )
        return tuple(out), "; ".join(notes) if notes else None

    return tier


def quantifier_tier(lexicon: Lexicon) -> Tier:
    """Kvantifikátor na roli — L‑3. Řadí se **za** mapování rolí.

    Jádro vyžaduje kvantifikátor u každého skupinového filleru; bez něj
    padá `role('kdo', Group('Učitelka'))` na `UnquantifiedRole` a z české
    věty se skupinou v roli nejde postavit ani jeden platný atom.

    Rozhoduje se ve dvou krocích a **žádný z nich není dohad**:

    1. **Explicitní determinátor** — „každý", „nějaký", „ten". Slovo se
       najde v lexikonu jako naučený vzor s proveniencí a statusem.
    2. **Holé jméno** — čeština nemá členy, takže tohle je většinový
       případ. Rozhoduje se podle TVARU (`upos`, číslo, pád, `deprel`),
       a i to je naučený vzor, jen se spouštěčem bez slova.

    **Když nerozhodne ani jeden krok, nedosadí se nic.** Role zůstane
    s `quantifier=None` a nese `pending` — tvar, na který se čeká
    odpověď. Implicitní hodnota v kódu by byla tichá volba měnící význam:
    „Kočka je savec" je o každé kočce, „Kočka spí na gauči" o jedné
    konkrétní, a rozhodnout to podle tvaru bez potvrzení znamená hádat
    (I‑1). Dvojznačnost se hlásí stejně — víc kandidátů znamená otázku,
    ne favorita.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        decided: list[Candidate] = []
        for candidate in candidates:
            roles: list[RoleReading] = []
            for role in candidate.predication.roles:
                if (
                    role.quantifier is not None
                    or role.mention.upos not in QUANTIFIED_UPOS
                    # Místo a čas se NEKVANTIFIKUJÍ — `RoleTerm` to u nich
                    # ani nepřipustí. Ptát se na kvantifikátor role `kam`
                    # by byla otázka bez odběratele: ať člověk odpoví
                    # cokoli, jádro to zahodí.
                    or role.name in UNQUANTIFIED_ROLES
                ):
                    roles.append(role)
                    continue
                resolved, note = _quantify(role, candidate.predication.mood, reading, lexicon)
                if note:
                    notes.append(note)
                roles.append(resolved)
            decided.append(
                Candidate(
                    replace(candidate.predication, roles=tuple(roles)),
                    origin=candidate.origin,
                )
            )
        return tuple(decided), "; ".join(notes) if notes else None

    return tier


def _quantify(
    role: RoleReading, mood: Mood, reading: Reading, lexicon: Lexicon
) -> tuple[RoleReading, str | None]:
    determiner = _determiner_of(role.mention, reading)
    if determiner is not None:
        signature = StructuralSignature(
            lemma=determiner.lemma,
            mood=mood,
            upos=determiner.upos,
            deprel=determiner.deprel,
        )
        origin = f"determinátor „{determiner.form}“"
    else:
        token = _token_at(role.mention.token_index, reading)
        signature = StructuralSignature(
            lemma="",
            # NÁLADA SE DO TVARU NEDÁVÁ, a je to podstatné. U spouštěcího
            # SLOVA na ní záleží („nebo" je v tvrzení sjednocení a v otázce
            # alternativa), ale jak je kvantifikované holé jméno, na tahu
            # dialogu nezávisí: „Učitelka učí." a „Učí učitelka?" mluví
            # o týchž učitelkách. Kdyby tam nálada byla, člověk by dostal
            # DVAKRÁT TUTÉŽ otázku — jednou za větu, jednou za otázku —
            # a druhá by se od první nedala rozeznat ani textem.
            mood=Mood.UNKNOWN,
            upos=role.mention.upos,
            deprel=token.deprel if token else "",
            number=role.mention.feat("Number") or "",
            case=role.mention.feat("Case") or "",
        )
        origin = f"tvar {signature.shape()}"

    matches = lexicon.quantifier_candidates(signature)
    if len(matches) > 1:
        return (
            replace(role, pending=signature, awaiting=AWAITING_QUANTIFIER),
            f"[POZOR: {role.name} — {origin} připouští "
            + " nebo ".join(m.operation.value for m in matches)
            + "]",
        )
    if not matches:
        return (
            replace(role, pending=signature, awaiting=AWAITING_QUANTIFIER),
            f"[CHYBÍ: kvantifikátor role {role.name} ({origin})]",
        )
    quantifier = QUANTIFIER_OF.get(matches[0].operation)
    if quantifier is None:
        # `DEFINITE`. Poctivá odpověď, jen se čeká na NĚCO JINÉHO —
        # kvantifikátor z určitosti plyne teprve tehdy, až se ví, na který
        # uzel se odkazuje, a to je V3.
        return (
            replace(
                role,
                determiner=_mention(determiner) if determiner else None,
                source=f"{origin} → určitost",
                awaiting=AWAITING_REFERENCE,
            ),
            f"[URČITOST: {role.name} odkazuje na už zmíněný uzel; "
            f"rozřešení je V3]",
        )
    return (
        replace(
            role,
            quantifier=quantifier,
            determiner=_mention(determiner) if determiner else None,
            source=origin,
        ),
        None,
    )


#: Slovní druhy, které něco znamenají. Předložka nebo spojka se do role
#: nedostane nikdy a hlásit ji jako ztrátu by byl šum, ve kterém by
#: skutečná ztráta zanikla.
MEANINGFUL_UPOS = ("NOUN", "PROPN", "ADJ", "VERB", "NUM", "PRON")

#: Značka ztráty ve stopě. Je to konstanta, protože ji píše kaskáda a čte
#: `Session` — a poznávat vlastní hlášku podle uhodnutého prefixu je přesně
#: ten druh vazby, který se tiše rozejde.
DROPPED_PREFIX = "[ZAHOZENO:"


def has_dropped(trace: Sequence[str]) -> bool:
    return any(step.startswith(DROPPED_PREFIX) for step in trace)


def dropped_tokens(reading: Reading, predication: Predication) -> tuple[Token, ...]:
    """Významové tokeny, které se nedostaly do žádné role ani do přísudku.

    **Mlčky zahodit kus věty je horší než ji nepřečíst.** Čtení, ze
    kterého něco vypadlo, se tváří úplně — a „Filipovo auto je modré"
    tak vyjde jako tvrzení o všech autech, se značkou „přečteno" a bez
    jediného znaménka, že se něco ztratilo. Neschopnost přečíst
    přivlastnění je poctivá mez; **nepřiznat ji** je vada.
    """
    used = {role.mention.token_index for role in predication.roles}
    head = _predicate_head(reading)
    if head is not None:
        used |= {head[0].index, head[1].index}
        # Infinitiv složeného přísudku NENÍ ztracený člen — jeho lemma je
        # v predikátu (`smět_dostat`). Hlásit ho jako ztrátu by poslalo
        # člověka pojmenovat roli něčemu, co roli mít nemá.
        inner = complex_predicate(reading, head[1])
        if inner is not None:
            used.add(inner.index)
    return tuple(
        token
        for token in reading.tokens
        if token.upos in MEANINGFUL_UPOS
        and token.index not in used
        and base_deprel(token.deprel) not in NOT_A_LOST_MEMBER
    )


def lost_shape(token: Token, reading: Reading) -> str:
    """Tvar ztraceného členu — **cesta od přísudku plus povrchové značení**.

    Je to obdoba `surface_role` o patro dál. Zatímco okolnost visí přímo
    na přísudku a stačí jí předložka s pádem, ztracený člen visí někde
    hlouběji: `penicilin` v „nesmí dostat penicilin" je `obj` pod
    `xcomp`. Tvar proto nese CESTU, aby jedna odpověď zavřela celou
    třídu vět, ne jednu větu — `xcomp>obj+Acc` platí pro „smí dostat",
    „chce koupit" i „musí vrátit".

    **Nic se z toho nehádá.** Cesta i pád jsou v rozboru; co ta role
    znamená, se neurčuje tady, ale učí se odpovědí člověka.
    """
    head = _predicate_head(reading)
    anchor = head[1].index if head else 0
    path: list[str] = []
    current: Token | None = token
    seen: set[int] = set()
    while current is not None and current.index != anchor:
        if current.index in seen:  # pragma: no cover — pojistka proti cyklu
            break
        seen.add(current.index)
        path.append(base_deprel(current.deprel))
        current = _token_at(current.head, reading)
    return ">".join(reversed(path)) + "+" + (token.feat("Case") or "?")


def lost_members(
    reading: Reading, predication: Predication
) -> tuple[tuple[Token, str], ...]:
    """Ztracené významové členy i s jejich tvarem."""
    return tuple(
        (token, lost_shape(token, reading))
        for token in dropped_tokens(reading, predication)
    )


def _dropped_note(reading: Reading, predication: Predication) -> str | None:
    lost = dropped_tokens(reading, predication)
    if not lost:
        return None
    parts = []
    for token in lost:
        head = _token_at(token.head, reading)
        under = f" pod „{head.form}“" if head is not None else ""
        parts.append(f"„{token.form}“ ({token.deprel}{under})")
    return (
        DROPPED_PREFIX + " " + ", ".join(parts) + " — pro tenhle vztah role "
        "není, takže se do čtení nedostalo]"
    )


def _colliding_circumstances(reading: Reading) -> str | None:
    """Povrchový tvar, který ve větě nese víc než jedno určení."""
    head = _predicate_head(reading)
    if head is None:
        return None
    seen: dict[str, int] = {}
    for token in reading.children(head[1].index):
        if token.deprel in CIRCUMSTANCE_DEPRELS:
            name = surface_role(token, reading)
            seen[name] = seen.get(name, 0) + 1
    duplicates = sorted(name for name, count in seen.items() if count > 1)
    return ", ".join(duplicates) if duplicates else None


def why_nothing(reading: Reading) -> str:
    """PROČ z věty nevzniklo ani jedno čtení.

    Přidáno po prvním běhu proti živé službě: dvě věty skončily holým
    „NEVÍM, jak to čtu" **bez jediného slova o důvodu**. Mlčení je tu
    horší než u odpovědi — u odpovědi aspoň víme, na co se ptalo, kdežto
    tady člověk neví ani to, jestli je problém ve větě, nebo v systému.

    Vysvětluje se JEN z toho, co v rozboru je. Nic se nedomýšlí; když se
    důvod najít nedá, řekne se i to.
    """
    head = _predicate_head(reading)
    if head is None:
        return "rozbor nemá kořen, ze kterého by šlo postavit přísudek"

    collision = _colliding_circumstances(reading)
    if collision:
        return (
            f"dvě určení mají týž tvar ({collision}) — které z nich je "
            f"které, tvarově nepoznám"
        )

    anchor = head[1]
    nominals = [
        token
        for token in reading.children(anchor.index)
        if token.deprel in NOMINAL_DEPRELS
    ]
    names = [_role_for(token, reading) for token in nominals]
    duplicated = sorted({n for n in names if n and names.count(n) > 1})
    if duplicated:
        # Táž třída jako kolize určení, jen o patro blíž jádru: `obj`
        # i `iobj` se mapují na roli `co`, takže věta se třemi jádrovými
        # nominály vyrobí dvakrát totéž jméno role. Rozlišit je by
        # znamenalo hádat, který z nich je „ten pravý" předmět.
        return (
            "dva jádrové členy dostaly touž roli ("
            + ", ".join(duplicated)
            + ") — rozbor je rozlišuje jinak, než umím pojmenovat"
        )

    if not nominals:
        unmapped = sorted(
            {t.deprel for t in reading.children(anchor.index) if t.deprel != "punct"}
        )
        return (
            f"přísudek „{head[0].form}“ nemá ani jeden člen, který bych "
            f"uměl pojmenovat" + (f" (rozbor dal {', '.join(unmapped)})" if unmapped else "")
        )
    return "z rozboru nevzniklo čtení a nedokážu říct proč — to je nález"


#: Tvrdá patra, která nepotřebují bázi ani naučené vzory. Pořadí je pořadí
#: ze § 5.2: morfologie dřív než cokoli statistického. `negation_tier` sem
#: patří ze stejného důvodu jako shoda a pád — `Polarity=Neg` je tvar, ne
#: dohad, a učit se na něm není co.
HARD_TIERS: tuple[Tier, ...] = (agreement_tier, case_tier, negation_tier)


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
        # Vždycky s DŮVODEM. Holé „neumím to přečíst" nechává člověka
        # hádat, jestli je problém ve větě, nebo v systému — a to je
        # jediná otázka, kterou v tu chvíli má.
        return Verdict(
            survivors=(),
            trace=tuple(trace),
            question=f"Tuhle větu přečíst neumím: {why_nothing(reading)}.",
        )
    for tier in tiers:
        candidates, why = tier(candidates, reading)
        if why:
            trace.append(f"{why} → zbývá {len(candidates)}")
        if not candidates:
            break
        # Smyčka se po rozhodnutí NEUKONČUJE. Ukončení by bylo správné pro
        # filtry, ale patra, která čtení PŘEPISUJÍ (přejmenování rolí),
        # by se pak nespustila vůbec — a to je tichá závislost na tom,
        # kolik kandidátů zbylo. Filtry nad jedním kandidátem nic nedělají.
    if len(candidates) > 1:
        options = " / ".join(str(c.predication) for c in candidates)
        return Verdict(
            survivors=candidates,
            trace=tuple(trace),
            question=f"Čtu to jako: {options} — které z toho?",
        )
    # Ztráta se hlásí jen u rozhodnutého čtení: u dvou kandidátů se liší,
    # a hlásit ztrátu z čtení, které možná není to pravé, mate.
    if len(candidates) == 1:
        note = _dropped_note(reading, candidates[0].predication)
        if note:
            # Do STOPY, ne odvozením z predikace. Ztracený token v predikaci
            # nikde není — to je celý ten problém — takže na rozdíl od
            # otázky na kvantifikátor se tohle spočítat zpětně nedá a musí
            # se to nést s tahem.
            trace.append(note)
    lost = tuple(
        (token.form, shape)
        for candidate in candidates
        for token, shape in lost_members(reading, candidate.predication)
    )
    open_roles = tuple(
        role
        for candidate in candidates
        for role in candidate.predication.open_roles()
    )
    pending = tuple(
        (role.name, role.pending) for role in open_roles if role.pending is not None
    )
    return Verdict(
        survivors=candidates,
        trace=tuple(trace),
        question=" ".join(
            part
            for part in (open_roles_question(open_roles), lost_question(lost))
            if part
        )
        or None,
        pending=pending,
        lost=lost,
    )


def lost_question(lost: Sequence[tuple[str, str]]) -> str | None:
    """Doptání na ZTRACENÝ ČLEN (N‑5).

    Dřív se ztráta jen ohlásila do stopy a věta se zapsala oseknutá.
    Ohlásit ztrátu je lepší než mlčet, ale pořád je to konstatování —
    a systém, který ví, že mu něco chybí, se má **zeptat**, ne si to
    poznamenat.

    Ptá se na TVAR, ne na slovo: odpověď zavře celou třídu vět."""
    if not lost:
        return None
    parts = [f"„{form}“ ({shape})" for form, shape in lost]
    return (
        "Nevím, jakou roli hraje " + ", ".join(parts) + " — do čtení se "
        "nedostalo. Jak se ta role jmenuje?"
    )


def open_roles_question(roles: Sequence[RoleReading]) -> str | None:
    """Doptání na otevřené role.

    Dvě věty, ne jedna: role bez kvantifikátoru a role čekající na odkaz
    jsou různé otázky a odpověď na jednu tu druhou nezodpoví. Nabídka
    kvantifikátorů je z UZAVŘENÉHO menu, takže odpověď nemůže vyrobit
    novou sémantiku (I‑15).
    """
    quantifier = [r for r in roles if r.awaiting == AWAITING_QUANTIFIER]
    reference = [r for r in roles if r.awaiting == AWAITING_REFERENCE]
    parts: list[str] = []
    if quantifier:
        shapes = ", ".join(
            f"{r.name} ({r.pending.shape() if r.pending else '?'})"
            for r in quantifier
        )
        parts.append(
            f"Nevím, o kom to platí — {shapes}. "
            f"O každém (∀), o některém (∃), nebo o tom konkrétním (·)?"
        )
    if reference:
        named = ", ".join(f"{r.name}: „{r.mention.form}“" for r in reference)
        parts.append(
            f"A na koho odkazuje {named}? Určitost říká, že to je někdo "
            f"už zmíněný, ale kdo, z věty nepoznám."
        )
    return " ".join(parts) if parts else None
