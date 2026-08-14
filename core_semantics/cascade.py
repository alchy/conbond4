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
from enum import Enum
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

#: Role, ze kterých se skládá jádrová relace navržená konstrukcí, podle
#: operace: `(levá, pravá)`. Jména jsou jádrová (§ 5.1), takže se z nich
#: dá postavit atom bez dalšího překladu.
RELATION_ROLES: dict[Operation, tuple[str, str]] = {
    Operation.MEMBER: ("elem", "group"),
    Operation.SUBSET: ("sub", "sup"),
    Operation.DISJOINT: ("a", "b"),
}


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
    #: Tokeny, které se do TÉHLE role dostaly složením lemmatu, ne vlastní
    #: rolí („dopravní“ v „dopravní prostředek“, N‑2b). Nese se to v roli,
    #: a ne dopočítává ze stromu, protože rozhodnutí složit padlo jinde —
    #: dopočet by ho hádal zpětně a hádal by ho příště jinak. Bez tohohle
    #: pole hlásí `dropped_tokens` složený přívlastek jako ZTRACENÝ ČLEN
    #: a systém se ptá na roli něčeho, co roli mít nemá.
    absorbed: tuple[int, ...] = ()

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
    #: JÁDROVÁ RELACE, kterou konstrukce tvrdí (N‑2) — `None` znamená
    #: „obyčejný vztah, reifikuje se". Není to jen jiné jméno predikátu:
    #: `subset` mění UZÁVĚR báze, kdežto vztah `být` je fakt jako každý
    #: jiný. Proto se sem nikdy nedosazuje potichu.
    relation: Operation | None = None

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


def attributes_of(token: Token, reading: Reading) -> tuple[Token, ...]:
    """Přívlastky, které se do jména třídy SKLÁDAJÍ — N‑2c.

    „Dopravní prostředek" je JEDEN POJEM, ne dvě věci. Skládá se proto
    lemma, přesně jako u složeného přísudku (G‑1a), jen na jmenné straně.

    **Skládá se v `generate`, tedy JEDNOU PRO VŠECHNY POZICE.** Dřív to
    dělalo patro jádrových relací, takže se fráze složila ve jmenném
    přísudku a nikde jinde — „dopravní prostředek" z jedné věty a týž
    přívlastek z druhé mířily na RŮZNÉ UZLY, ačkoli člověk mluvil o téže
    věci. Tichá nekonzistence identity je horší než chybějící schopnost:
    nedá se o ní poznat, že nastala.

    **Lemmata, ne tvary** — a proto to funguje napříč pozicemi: „dlouhá
    dálnice" i „po dlouhé dálnici" dají `dlouhý_dálnice`. Je to
    identifikátor uzlu, ne text pro člověka.

    Dvě vyloučení, obě ze STAVBY, ne z odhadu:

    * **jen `NOUN`** nese třídu. Přívlastek na vlastním jméně by měnil
      identitu pojmenovaného uzlu, a to je jiná operace než pojmenovat
      třídu;
    * **přivlastnění NE** (`Poss=Yes`). „Filipovo auto" není druh auta,
      je to vztah ke KONKRÉTNÍMU uzlu. Složit ho na `Filipův_auto` by
      z každého majitele udělalo novou třídu a **umlčelo by to otázku**,
      kterou na přivlastnění systém právem klade (N‑5).
    """
    if token.upos != "NOUN":
        return ()
    return tuple(
        child
        for child in reading.children(token.index)
        if base_deprel(child.deprel) == "amod" and child.feat("Poss") != "Yes"
    )


def _composed_mention(token: Token, reading: Reading) -> Mention:
    parts = attributes_of(token, reading)
    if not parts:
        return _mention(token)
    lemma = "_".join([*(p.lemma for p in parts), token.lemma])
    return Mention(
        lemma=lemma,
        form=" ".join([*(p.form for p in parts), token.form]),
        token_index=token.index,
        upos=token.upos,
        feats=token.feats,
    )


def _nominal(token: Token, reading: Reading, name: str) -> RoleReading:
    """Role s **složeným** fillérem a se zapsanými pohlcenými tokeny."""
    return RoleReading(
        name,
        _composed_mention(token, reading),
        absorbed=tuple(t.index for t in attributes_of(token, reading)),
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


def _preposition_of(token: Token, reading: Reading) -> Token | None:
    """Předložka závislá na tokenu (`deprel=case`) — nebo `None`."""
    for child in reading.children(token.index):
        if base_deprel(child.deprel) == "case":
            return child
    return None


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
    found = _preposition_of(token, reading)
    preposition = found.lemma if found else None
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
    if base == "obj":
        return token.deprel if subtyped else ROLE_OBJECT
    if base == "iobj":
        # `iobj` NENÍ `obj` *(N‑5b)*. Slít je znamenalo, že „Děti mají rády
        # zmrzlinu" dalo DVĚMA členům touž roli `co`, čtení s duplicitou
        # se nesmí vyrobit a nezbylo ani jedno — věta se nepřečetla vůbec.
        # Rozbor ta dvě místa rozlišuje; kaskáda to rozlišení zahazovala.
        # Je to táž třída jako B‑9, jen o patro blíž jádru.
        #
        # Jméno je proto POVRCHOVÉ a co znamená, se učí. Nepředstírá se
        # tím, že se ví, o co jde: v „Petr dal Pavlovi knihu" je skutečný
        # nepřímý předmět `obl:arg` (`Dat:arg`), kdežto tenhle `iobj` je
        # u „rády" chybný rozbor příslovce. Uhodnout jedno jméno pro obojí
        # by byl dohad o významu — a od N‑3 na to existuje otázka.
        return surface_role(token, reading)
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

    # Přívlastky se do jmen tříd SKLÁDAJÍ, takže se nesmí zároveň stát
    # samostatnými členy. Sbírá se to PŘED smyčkou, protože přívlastek
    # jmenné části visí na kořeni, tedy mezi `members` — a bez tohohle
    # kroku by „dopravní" bylo i složené, i vlastní rolí.
    absorbed = {
        attribute.index
        for token in (anchor, *members)
        for attribute in attributes_of(token, reading)
    }

    nominals: list[Token] = []
    fixed: list[RoleReading] = []
    for token in members:
        if token.deprel == "cop" or token.index in absorbed:
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
            fixed.append(_nominal(token, reading, role))

    variants: list[tuple[RoleReading, ...]] = []
    if carrier is not anchor:
        # Spona: jmenná část JE obsah — to říká stavba věty, ne odhad.
        # Nominály tedy plní jen podmět.
        #
        # **PŘEDLOŽKA JMENNOU ČÁST VYLUČUJE** *(N‑4)*. „Petr byl v Praze"
        # má v UD kořen `Praze` a sponu `byl`, takže sponové pravidlo
        # dosud udělalo z Prahy jmennou část přísudku — `co:Praha`, jako
        # by Petr Prahou BYL. Předložka u kořene je ale tvrdý strukturní
        # signál, že jde o OKOLNOST: „být prostředek" předložku nemá,
        # „být v Praze" ji má vždycky.
        #
        # Není to nové pravidlo o významu — sémantika okolnosti se dál
        # nehádá a role zůstane POVRCHOVÁ (`v+Loc`). Jen se nepřevezme
        # jmenná část tam, kde ji stavba vylučuje.
        anchor_role = (
            surface_role(anchor, reading)
            if _preposition_of(anchor, reading) is not None
            else ROLE_OBJECT
        )
        fixed.append(_nominal(anchor, reading, anchor_role))
        variants = [(_nominal(t, reading, ROLE_SUBJECT),) for t in nominals] or [()]
    elif len(nominals) == 2:
        first, second = nominals
        variants = [
            (
                _nominal(a, reading, ROLE_SUBJECT),
                _nominal(b, reading, ROLE_OBJECT),
            )
            for a, b in ((first, second), (second, first))
        ]
    else:
        kept = tuple(
            _nominal(token, reading, _role_for(token, reading) or ROLE_SUBJECT)
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


class RejectionKind(Enum):
    """Proč báze čtení odmítá — a tím i **jak silně** (A‑21).

    Rozdíl není odstín, je to hranice mezi dvěma druhy tvrzení:

    * `SORT` je o **TVARU** čtení. Fillér nesedí do sortu role, takže
      z toho čtení žádná formule nevznikne. Není co ztratit a není se
      nač ptát — odmítá se tvrdě.
    * `CONTRADICTED` je o **OBSAHU BÁZE**. Čtení je syntakticky i typově
      v pořádku, jen se neshoduje s tím, co už je zapsané. Jenže zapsané
      může být špatně — a tvrdě takové čtení vyhodit znamená nechat
      chybný fakt umlčet správnou větu, potichu.
    """

    SORT = "typová chyba"
    CONTRADICTED = "rozpor s bází"


@dataclass(frozen=True, slots=True)
class Rejection:
    """Pojmenovaný důvod odmítnutí. Nikdy holé `True`/`False` — eliminace
    bez důvodu je přesně to, čemu se K‑7 brání."""

    kind: RejectionKind
    detail: str

    @property
    def hard(self) -> bool:
        """Smí se podle toho čtení ODSTRANIT, nebo jen snížit priorita?"""
        return self.kind is RejectionKind.SORT

    def __str__(self) -> str:
        return self.detail


#: Důvod, proč báze čtení odmítá — nebo `None`, když žádný nemá.
#: Injektuje se zvenčí, protože rozhodnout se dá až nad ZAKOTVENOU
#: formulí, a zakotvení je V3. Kaskáda o něm nemá vědět.
SemanticCheck = Callable[[Predication], Rejection | None]


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

    **Rozpor s bází ČTENÍ NEODSTRAŇUJE, jen mu snižuje prioritu** *(A‑21)*.
    Do téhle změny patro vracelo jen ty, které bázi neodporovaly, a
    odporující mizely nenávratně. Syntakticky i typově platné čtení bylo
    pryč, aniž se kdo zeptal — a jsou to dvě různá tvrzení:

    > „tohle čtení neodpovídá tomu, co mám zapsané" ≠ „tohle čtení je
    > špatně".

    Rozdíl by nevadil, kdyby báze byla neomylná. Není: plní ji tytéž věty,
    které tohle patro filtruje. Chybný fakt tedy umlčí správné čtení, to
    upevní chybu, a **potichu** — z každého dalšího kroku bude vypadat,
    že „sedí". Je to táž smyčka, kterou ruší K‑7, jen postavená na rozporu
    místo na známosti.

    Odporující čtení proto zůstává v sadě, klesne na konec a rozpor se
    zapíše do stopy. Když po zbytku kaskády zbude víc kandidátů, systém
    se **zeptá** — a to je tah dialogu, ne prohra.

    **Tvrdě odmítat smí jen typová chyba** (`RejectionKind.SORT`), protože
    ta je o tvaru čtení, ne o obsahu báze. Z takového čtení žádná formule
    nevznikne, takže není co upřednostňovat a nač se ptát.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        reasons = [(c, reject(c.predication)) for c in candidates]
        kept = [(c, why) for c, why in reasons if why is None or not why.hard]
        notes: list[str] = []

        mistyped = [why for _, why in reasons if why is not None and why.hard]
        if mistyped:
            notes.append(
                "[PROČ: typová chyba — " + "; ".join(map(str, mistyped)) + "]"
            )
        if not kept:
            # Typová chyba na VŠECH čteních. Vrátit prázdno je tady
            # poctivé: není co upřednostnit ani na co se zeptat.
            return (), "; ".join(notes) or None

        clean = tuple(c for c, why in kept if why is None)
        demoted = [(c, why) for c, why in kept if why is not None]
        if not demoted:
            return tuple(c for c, _ in kept), "; ".join(notes) or None

        detail = "; ".join(str(why) for _, why in demoted)
        if not clean:
            # Odmítnout VŠECHNO by znamenalo tvrdit, že věta nedává smysl,
            # jenže rozporná věta smysl dává — jen se s bází neshoduje.
            # To je nález pro člověka, ne důvod k mlčení. Tahle větev se
            # A‑21 NEMĚNÍ: klesnout na konec proti komu, když je rozporné
            # všechno? Věta se přečte, zapíše a rozpor se ohlásí (I‑3).
            what = "čtení je" if len(kept) == 1 else "každé čtení je"
            notes.append(f"[POZOR: {what} v rozporu s bází — {detail}]")
            return tuple(c for c, _ in kept), "; ".join(notes)

        # Priorita, ne eliminace: čisté dopředu, rozporné dozadu, obojí
        # v sadě. `Verdict.decided` vrací čtení jen tehdy, zbylo‑li právě
        # jedno, takže víc kandidátů znamená OTÁZKU, ne favorita.
        notes.append(
            f"[POZOR: rozpor s bází — {detail}; čtení se NEODSTRAŇUJE, "
            f"jen klesá — zapsaný fakt může být chybný a tiše umlčet "
            f"správné čtení]"
        )
        return clean + tuple(c for c, _ in demoted), "; ".join(notes)

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

#: Role, které jméno NEPOTŘEBUJÍ, protože ho už mají. Jádro rolí je
#: uzavřené (§ 12/1) a místo s časem mají vlastní slovník; všechno ostatní,
#: co `_role_for` vrátí, je POVRCHOVÉ pojmenování tvaru (`v+Loc`,
#: `nsubj:pass`) a co znamená, se musí NAUČIT.
#:
#: Je to členství v uzavřeném slovníku jádra, ne odhad z podoby řetězce.
#: Poznávat povrchovou roli podle toho, že v ní je `+`, by byla heuristika
#: nad textem — a ta by se rozešla, jakmile by někdo tvar přejmenoval.
#: Jádrová jména rolí (`elem`, `sub`, `a`, …) jsou mezi nimi taky: jsou
#: kanonická v témž smyslu, jen ve slovníku JÁDRA místo kaskády. Berou se
#: z `RELATION_ROLES`, ne z druhého seznamu — dvě kopie by se rozešly.
CANONICAL_ROLES: frozenset[str] = (
    frozenset({ROLE_SUBJECT, ROLE_OBJECT, ROLE_MANNER})
    | UNQUANTIFIED_ROLES
    | {name for pair in RELATION_ROLES.values() for name in pair}
)

def surface_roles(predication: Predication) -> tuple[str, ...]:
    """Role, které zůstaly POVRCHOVÉ — tvar bez významu."""
    return tuple(
        sorted({r.name for r in predication.roles if r.name not in CANONICAL_ROLES})
    )


def role_question(predication: Predication) -> str | None:
    """Otázka na to, co povrchová role znamená — nebo `None`.

    Počítá se z HOTOVÉ predikace, ne ze stopy, a je to podstatné: stopa
    je log, takže by nesla i tvary, které pozdější patro mezitím
    spotřebovalo. `Gen` v „Amoxicilin je druh penicilinu" povrchová role
    JE, ale jádrová relace ji vezme jako stranu `subset` — ptát se na ni
    by bylo doptání na něco, co už je rozhodnuté.
    """
    shapes = surface_roles(predication)
    if not shapes:
        return None
    which = ", ".join(f"„{shape}“" for shape in shapes)
    return (
        f"Nevím, co znamená {which} — je to tvar, ne význam. Jak se ta "
        f"role jmenuje (kde, kdy, kudy, odkud, …)?"
    )


def role_mapping_tier(lexicon: Lexicon) -> Tier:
    """Přejmenuje povrchovou roli na kanonickou podle NAUČENÉHO mapování.

    Přepisuje jen tam, kde je mapování **jednoznačné** a kde nové jméno
    nekoliduje. Má‑li povrchový tvar víc kandidátů, patro to zapíše do
    trace a jméno nechá povrchové — vybrat tiše by znamenalo uhádnout
    význam nominálu, což INV‑11 zakazuje.

    **Nerozhodnutá povrchová role je OTÁZKA, ne poznámka** *(N‑3)*. Do
    téhle změny se dvojznačnost jen ohlásila do stopy a věta skončila
    nezakotvená: povrchová role neurčuje sort, takže se nedalo pokračovat
    a člověk neměl co odpovědět. Ohlásit je lepší než mlčet, ale pořád je
    to konstatování — systém, který ví, že mu chybí význam tvaru, se má
    **zeptat**. Odpověď je tah `→@` a naučí TVAR, takže jedna odpověď
    zavře celou třídu vět.
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
                if role.name not in CANONICAL_ROLES:
                    # Tvar, který nikdo nepojmenoval. Mlčet by znamenalo
                    # nechat větu nezakotvenou bez jediného vodítka, co
                    # s tím — povrchová role neurčuje sort, takže se dál
                    # nedá pokračovat ani se zeptat na kvantifikátor.
                    notes.append(f"[CHYBÍ: co znamená role {role.name}]")
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


#: Lemma spony. Konstrukce se pozná podle NÍ, ne podle seznamu sloves.
COPULA_LEMMA = "být"



@dataclass(frozen=True, slots=True)
class Construction:
    """Rozpoznaná konstrukce: TVAR a to, které role tvoří strany relace.

    Skládání jmenné části tu NENÍ a je to od N‑2c záměr: dělá ho
    `generate` jednou pro všechny pozice, takže sem už fráze přichází
    složená. Kopie pravidla v patře by znamenala, že se táž fráze skládá
    dvakrát podle dvou předpisů — a ty se dřív nebo později rozejdou.
    """

    shape: str
    left: str
    right: str
    #: Tokeny, které konstrukce POHLTILA — nejsou ztracené členy (N‑5),
    #: protože se do významu dostaly, jen ne vlastní rolí.
    absorbed: tuple[int, ...] = ()


def relation_shape(
    predication: Predication, reading: Reading
) -> Construction | None:
    """Rozpoznaná konstrukce — nebo `None`.

    Vrací se **tvar**, ne rovnou operace. Co ten tvar znamená, je naučené
    a odvolatelné tvrzení v lexikonu; kdyby to rozhodovala tahle funkce,
    byl by v interpretu schovaný seznam významů českých konstrukcí — táž
    vada, kvůli které se okolnosti pojmenovávají povrchově (INV‑11).

    Rozeznávají se dvě rodiny:

    * **s lexikálním markerem** — „X je DRUH Y": jmenná část je slovo,
      které samo mluví o třídách, a pravá strana relace je jeho přívlastek
      v genitivu. Tvar nese lemma markeru, protože právě to slovo tu nese
      význam;
    * **holá spona** — „X je Y" / „X není Y": tvar nese slovní druhy obou
      stran a polaritu, protože na nich to celé visí. `Mourek je kočka`
      (PROPN) a `Kočka je savec` (NOUN) jsou různé relace.

    **Jmenná část s přívlastkem je JEDEN POJEM, ne dva** *(N‑2b)*.
    „Auto je dopravní prostředek" mluví o třídě „dopravní prostředek";
    `dopravní` není samostatný člen vztahu. Skládá se proto lemma —
    přesně jako u složeného přísudku (G‑1a), jen na jmenné straně — a věta
    tím spadne do TÉŽE rodiny jako holá spona. Jedna odpověď tak zavře
    „Kočka je savec" i „Auto je dopravní prostředek", protože je to jedna
    a tatáž otázka: co ta spona tvrdí.

    **Proč složený POJEM, a ne průnik `dopravní AND prostředek`.**
    Rozhodnuto vědomě, je to volba denotace:

    1. `restriction(t; role:t)` je vyloučená stavbou — filtruje instance
       přes ROLE a přívlastek fillér role není;
    2. průnik tvrdí **intersektivitu**: `X ⊆ A AND B` znamená, že věc je
       zvlášť `A` a zvlášť `B`. U „bývalý prezident" je to nepravda a
       u lexikalizovaného sousloví („dopravní prostředek") taky —
       a **morfologie ty případy nerozliší**. Zvolit průnik proto znamená
       hádat o významu přídavného jména;
    3. změřeno, ne odhadnuto: průnik by dnes nekoupil ani ten závěr, kvůli
       kterému by se vyplatil. Zákon `X ⊆ A AND B ⇒ X ⊆ B` v § 5.2.1 NENÍ
       (je tam opačný směr), takže `dopravní prostředek ⊆ prostředek` by
       z něj stejně neplynulo;
    4. co se tím ztrácí, jde **doříct tahem**: „Dopravní prostředek je druh
       prostředku." už dnes dá `subset`. Nezískaný závěr je lepší než
       vymyšlený.

    Slabší závazek je v otevřeném světě ta správná výchozí volba: netvrdí
    nic nepravdivého, jen netvrdí víc, než věta říká.

    **Slovní druh podmětu je v tvaru schválně** *(N‑2d)*. `PROPN` JE
    signál individua, takže „Jana je učitelka" je členství — a to je
    rozhodnutelné, na rozdíl od `NOUN=NOUN`, kde „Kočka je savec"
    (podmnožina) a „Mourek je kočka" (členství) mají týž tvar. Tvrdit
    o vlastním jméně podmnožinu by znamenalo udělat z individua třídu.
    """
    if predication.predicate != COPULA_LEMMA:
        return None
    subject = predication.reading(ROLE_SUBJECT)
    complement = predication.reading(ROLE_OBJECT)
    if subject is None or complement is None:
        return None

    genitive = [
        role
        for role in predication.roles
        if role is not subject
        and role is not complement
        and role.mention.feat("Case") == "Gen"
    ]
    if len(genitive) == 1:
        # „X je druh Y" — pravá strana je přívlastek, ne jmenná část.
        return Construction(
            shape=f"cop:{complement.mention.lemma}+Gen",
            left=subject.name,
            right=genitive[0].name,
            absorbed=(complement.mention.token_index,),
        )

    others = [
        role
        for role in predication.roles
        if role is not subject and role is not complement
    ]
    if others:
        # Další členy, kterým konstrukce nerozumí. Mlčet je tu správně —
        # navrhnout relaci z něčeho, čemu nerozumím, by bylo horší než
        # nenavrhnout nic.
        return None
    if complement.mention.upos != "NOUN":
        # JMENNÝ přísudek, ne jakýkoli. „To auto je modré." je VLASTNOST,
        # ne vztah tříd — ptát se u ní na členství nebo podmnožinu je
        # otázka bez odběratele, ať člověk odpoví cokoli.
        return None
    if subject.mention.upos not in ("NOUN", "PROPN"):
        return None
    link = "≠" if predication.negated else "="
    return Construction(
        shape=f"cop:{subject.mention.upos}{link}{complement.mention.upos}",
        left=subject.name,
        right=complement.name,
    )


def relation_tier(lexicon: Lexicon) -> Tier:
    """Jádrová relace ze STAVBY věty — N‑2. Řadí se **za** mapování rolí.

    **Problém.** „Amoxicilin je druh penicilinu." se přečetlo jako
    `být(Gen:penicilin, co:druh, kdo:amoxicilin)` a nikdy jako `subset`.
    Operace `MEMBER`/`SUBSET`/`DISJOINT` v menu byly, ale nikdo je ze
    stavby věty neplnil — chybělo patro, které konstrukci rozpozná.
    Doména kontraindikace na tom stojí celá: bez `subset` se kaskáda
    `subset*` nemá čeho chytit.

    **Návrh, ne dosazení.** Tohle patro váží víc než ostatní, a proto je
    opatrnější: ostatní vzory mění, jak se věta ČTE, tenhle mění, co se
    z ní zapíše do JÁDRA. Špatně navržený `subset` změní uzávěr celé báze
    a projeví se to na odpovědích, které s tou větou nemají nic
    společného. Rozhoduje se proto stejně jako u kvantifikátoru:

    * právě jeden aktivní vzor na daný tvar → **dosadí se** a je to ve stopě;
    * víc vzorů nebo žádný → **nedosadí se nic**, tvar se ohlásí a čeká se
      na odpověď člověka.

    Holá kladná spona je ten druhý případ a je to jádro věci: „Kočka je
    savec" je `subset`, „Mourek je kočka" je `member`, a tvar je týž.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        decided: list[Candidate] = []
        for candidate in candidates:
            proposed, note = _propose_relation(candidate.predication, reading, lexicon)
            if note:
                notes.append(note)
            decided.append(Candidate(proposed, origin=candidate.origin))
        return tuple(decided), "; ".join(notes) if notes else None

    return tier


def _propose_relation(
    predication: Predication, reading: Reading, lexicon: Lexicon
) -> tuple[Predication, str | None]:
    if predication.relation is not None:
        return predication, None  # už rozhodnuto (odpovědí člověka)
    found = relation_shape(predication, reading)
    if found is None:
        return predication, None
    shape = found.shape
    matches = lexicon.relation_candidates(shape)
    if len(matches) > 1:
        return predication, (
            f"[POZOR: tvar {shape} připouští "
            + " nebo ".join(m.operation.value for m in matches)
            + f" — {RELATION_QUESTION_MARK}{shape}]"
        )
    if not matches:
        return predication, (
            f"[CHYBÍ: co ta stavba tvrdí — tvar {shape} "
            f"{RELATION_QUESTION_MARK}{shape}]"
        )
    operation = matches[0].operation
    return (
        _as_relation(predication, operation, found),
        f"[STAVBA: tvar {shape} → jádrová relace {operation.value}]",
    )


def _as_relation(
    predication: Predication, operation: Operation, found: Construction
) -> Predication:
    """Přepíše čtení na jádrovou relaci s JÁDROVÝMI jmény rolí.

    Přejmenování je podstatné: `subset(sub:…, sup:…)` se dá zakotvit
    přímo konstruktorem jádra, kdežto `subset(kdo:…, co:…)` by musel někdo
    o vrstvu níž překládat — a ten překlad by byl druhé místo, kde se
    rozhoduje, která strana je která.

    **Negaci pohltí jen ta relace, která ji SAMA NESE.** `disjoint`
    znamená „tyhle dvě třídy se nepřekrývají", takže zápor je v ní už
    obsažený; ponechat na ní `negated=True` by tvrdilo `¬disjoint`, tedy
    pravý opak toho, co člověk řekl.

    U `member` a `subset` je to naopak: zápor je na nich **kolmý**
    a musí se přenést. „Jana není učitelka" je `member̄(Jana, učitelka)`,
    tedy DOLOŽENÉ POPŘENÍ členství (§ 4) — ne oddělenost tříd, protože
    Jana třída není, a ne mezera, protože o tom se něco ví (I‑21).

    **Kvantifikátor je `·` a není to dohad.** Argumenty jádrové relace jsou
    TY TŘÍDY SAMY — `subset(amoxicilin, penicilin)` mluví o dvou skupinách,
    ne o jejich členech, a jádrové konstruktory to tak i vyžadují. Ptát se
    tu „o každém, o některém, nebo o tom konkrétním?" by byla otázka bez
    odběratele: ať člověk odpoví cokoli, atom by vypadal stejně.
    """
    left_role, right_role = RELATION_ROLES[operation]
    by_name = {role.name: role for role in predication.roles}

    def as_class(role: RoleReading, name: str) -> RoleReading:
        # `absorbed` se ZÁMĚRNĚ nepředává: `replace` ho zdědí z role, kterou
        # složil `generate`. Přepsat ho tady na prázdno by přivlastnilo
        # skládání téhle funkci — a přívlastek by se vzápětí ohlásil jako
        # ztracený člen, ačkoli v lemmatu je.
        return replace(
            role,
            name=name,
            quantifier=Quantifier.SELF,
            pending=None,
            awaiting="",
            source=f"jádrová relace {operation.value}",
        )

    return Predication(
        predicate=operation.value,
        roles=tuple(
            sorted(
                (
                    as_class(by_name[found.left], left_role),
                    as_class(by_name[found.right], right_role),
                ),
                key=lambda r: r.name,
            )
        ),
        mood=predication.mood,
        negated=predication.negated and operation is not Operation.DISJOINT,
        relation=operation,
    )


#: Značka doptání na relaci ve stopě. Konstanta, protože ji píše kaskáda
#: a čte `Session` — poznávat vlastní hlášku podle uhodnutého prefixu je
#: přesně ta křehkost, kvůli které existují ostatní značky.
RELATION_QUESTION_MARK = "?stavba="


def relation_question(trace: Sequence[str]) -> str | None:
    """Otázka na to, co konstrukce tvrdí — nebo `None`."""
    for step in trace:
        if RELATION_QUESTION_MARK in step:
            # Po značce následuje tvar a pak `]`, za kterým už kaskáda
            # připsala svoje „→ zbývá N". Číst do konce řádku by do otázky
            # vtáhlo cizí text.
            shape = step.split(RELATION_QUESTION_MARK, 1)[1].split("]", 1)[0]
            return (
                f"Co ta věta tvrdí o vztahu těch dvou? Tvar je {shape} — "
                f"členství (member), podmnožina (subset), nebo oddělenost "
                f"skupin (disjoint)?"
            )
    return None


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
    for role in predication.roles:
        used |= set(role.absorbed)
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
