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

import collections
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Sequence

from .ast import UNQUANTIFIED_ROLES, Quantifier
from .lexicon import (
    RELATIONAL,
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
    Operation.BEFORE: ("earlier", "later"),
    Operation.SAME_AS: ("left", "right"),
    Operation.CONTAINS: ("part", "whole"),
    Operation.WITHIN: ("part", "whole"),
    Operation.NAME: ("of", "value"),
}

#: Relace, jejichž fillery NEJSOU skupiny, takže kvantifikátor nenesou
#: (§ 3.6). `RoleTerm` by ho u nich ani nepřipustil.
UNQUANTIFIED_RELATIONS: frozenset[Operation] = frozenset(
    {Operation.BEFORE, Operation.CONTAINS, Operation.WITHIN, Operation.NAME}
)


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
    #: Role, kterou věta VŮBEC NEVYSLOVILA — český pro‑drop *(0.1.17)*.
    #: Zmínkou je PŘÍSUDEK, protože rod a číslo jsou na něm; je to
    #: vodítko, ne důkaz, stejně jako u zájmena. Vlastní pole ze stejného
    #: důvodu jako `collided`: značka, na které někdo staví, nesmí ležet
    #: v poli, které vlastní jiný krok.
    dropped: bool = False
    #: Role, jejíž význam je ZNÁMÝ, ale kanonické jméno už v téhle větě
    #: někdo zabral *(W‑20)*. Vlastní pole, ne poznámka v `source`:
    #: `source` vlastní ten, kdo roli naposled sáhl, takže kvantifikátorové
    #: patro značku o krok dál přepsalo a otázka se ptala dál. Táž lekce
    #: jako B‑17 — stav, na kterém někdo staví, musí mít vlastní místo.
    #:
    #: Není to táž věc jako povrchová role bez významu, a splynout to
    #: nesmí: u téhle se ptát nemá na co — odpověď systém zná a je to
    #: právě ta, která koliduje.
    collided: bool = False
    #: Role, jejíž JMÉNO JE POŘÁD TVAR *(W‑62)*. Vlastní pole, protože
    #: poznat to jinak nejde: „proč“ je NAUČENÉ jméno, tedy taky mimo
    #: uzavřené jádro rolí (§ 12/1), a přesto se na ně ptát nemá — někdo
    #: ho už pojmenoval. Rozdíl „jméno = tvar“ × „jméno naučené“ zná jen
    #: ten, kdo roli vyrobil; kdo ji čte později, vidí jen řetězec.
    #:
    #: Táž lekce jako `collided` a B‑17: značka, na které někdo staví,
    #: musí mít vlastní místo. Zkoušet to z podoby řetězce (obsahuje `+`,
    #: obsahuje `/`) je heuristika nad textem a rozejde se, jakmile někdo
    #: pojmenuje roli tak, že se to trefí.
    shaped: bool = False
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
    #: Tvar konstrukce, na jejíž význam se ČEKÁ *(B‑17)*. Nese to
    #: PREDIKACE, ne stopa: stopa je log jednoho tahu, takže odpověď na
    #: kvantifikátor ji zahodila a otázka na relaci se tím ZTRATILA —
    #: věta se pak zapsala jako obyčejný vztah, přestože systém v téže
    #: odpovědi říkal, že tomu tvaru nerozumí. Je to táž lekce jako N‑3:
    #: ptát se z HOTOVÉ predikace, ne z logu.
    pending_relation: str = ""
    #: Skupina, jejíž UZAVŘENÍ SVĚTA věta navrhuje *(„To jsou všichni
    #: psi.")*. Prázdné = nenavrhuje. Nese to predikace ze stejného
    #: důvodu jako `pending_relation` (B‑17), a zápis to blokuje stejně:
    #: `complete(g)` je jediné místo, kde se z NEPŘÍTOMNOSTI stane „ne",
    #: takže tiše se nezapíše nikdy.
    pending_complete: str = ""
    #: GENITIVNÍ PŘÍVLASTEK, jehož význam se ČEKÁ *(W‑39)*, jako
    #: `(hlava, genitiv, token)`. Není to role predikace a blokovat větu
    #: proto NESMÍ: „Druhou polovinu domu obýval bratr." má `domu` jako
    #: `nmod` pod `polovinu`, tedy pod JMÉNEM — predikace nese role
    #: SLOVESA a `domu` není argument „obývat". Je to vztah dvou jmen
    #: uvnitř fráze, tedy DRUHÝ VÝROK vedle věty; větě samotné chybí
    #: přívlastek, ne predikát.
    pending_attribute: tuple[tuple[str, str, int], ...] = ()
    #: TVRZENÍ, KTERÉ NESE TITUL *(W‑55)*, jako `(jméno, titul, token)`.
    #: „básník Josef Hora“ tvrdí DVĚ věci — že promluvil a že je básník.
    #: Zapisovala se jedna a o druhé systém říkal „nikdo to neřekl“, což
    #: byla nepravda o tom, co ve větě stálo.
    #:
    #: Blokovat větu NESMÍ, ze stejného důvodu jako `pending_attribute`:
    #: je to druhý výrok VEDLE věty, ne chybějící role. Věta „Nad hrobem
    #: promluvil básník Josef Hora.“ je celá i bez něj.
    pending_title: tuple[tuple[str, str, int], ...] = ()

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


#: Hrany, které jsou POKRAČOVÁNÍM TÉHOŽ JMÉNA *(B‑22)*. Pojmenovaná
#: konstanta s důvodem u ní, jako `PREDICATE_AUXILIARIES` a
#: `SUBJECT_DEPRELS` — je to potřetí týž tvar rozhodnutí.
#:
#: **`flat` ano, `appos` NE, a rozhoduje VZTAH, ne slovní druh členu.**
#: `flat` je druhý díl jednoho jména („Karel **Čapek**"); `appos` je JINÁ
#: ZMÍNKA téže věci („Karel Čapek, **rodným jménem Karel Antonín
#: Čapek**"). Když se skládal i `appos`, vznikl uzel `Karel_Čapek_Karel`
#: — jméno, které v textu NIKDO NENESE, a otázka „Byl Karel Čapek
#: spisovatel?" na něj nesedla. Je to táž rodina jako B‑21, jen z druhé
#: strany: tam se dva lidé slili v jednoho, tady se jeden rozdělil na
#: uzel, se kterým se jeho vlastní jméno nepotká.
#:
#: **Proč z toho není rovnou `same_as`.** Nabízí se: „Karel Čapek" a
#: „Karel Antonín Čapek" je týž člověk a jádro `same_as` umí. Jenže
#: `appos` mezi dvěma `PROPN` neznamená VŽDY totéž — „Karel Čapek,
#: spisovatel" je role, ne druhé jméno — a rozbor ty dva případy
#: nerozlišuje. Ztotožnit uzly z tvaru by byl TICHÝ DEFAULT U IDENTITY,
#: tedy nejdražší chyba, jakou tenhle systém dělá (M‑2, I‑13): uzly se
#: tiše slijí a nepozná to žádný test, ke kterému jazyk nevede. Až se
#: `same_as` z apozice zapisovat bude, musí se NAVRHNOUT A ZEPTAT, ne
#: dosadit — a to je vlastní tah, ne tahle konstanta.
NAME_CONTINUATION = ("flat",)


def name_parts_of(token: Token, reading: Reading) -> tuple[Token, ...]:
    """Další díly VÍCESLOVNÉHO JMÉNA — `flat` *(B‑21)*.

    „Josef Hora" není hlava s přívlastkem, je to JEDNO JMÉNO; UD to říká
    hranou `flat`. Dokud se ta hrana zahazovala, četla se ta věta jako
    fakt o uzlu `Josef` a příjmení se ohlásilo jako ztracený člen — ale
    ztráta to nebyla, byl to ZÁPIS O JINÉM UZLU. Dva různí lidé s týmž
    křestním jménem („Karel Čapek", „Karel Poláček") by tiše splynuli
    v jeden, a nepoznalo by se to: obojí by vypadalo jako doložený fakt
    o Karlovi.

    Skládá se JEN `flat` pod vlastním jménem, ne `appos` — viz
    `NAME_CONTINUATION`. Vylučuje se i `flat` pod obecným jménem: to není
    jméno, ale seznam, a to je jiná operace.

    Pořadí se drží podle POZICE v textu, ne podle pořadí hran: „Josef
    Hora" a „Hora Josef" nejsou totéž a identifikátor uzlu se tím řídit
    musí.
    """
    if token.upos != "PROPN":
        return ()
    return tuple(
        sorted(
            (
                child
                for child in reading.children(token.index)
                if base_deprel(child.deprel) in NAME_CONTINUATION
                and child.upos == "PROPN"
            ),
            key=lambda t: t.index,
        )
    )


def titled_name_of(token: Token, reading: Reading) -> tuple[Token, ...]:
    """Jméno osoby pod OBECNÝM jménem — „básník **Josef Hora**" *(W‑53)*.

    **Rozbor to rozlišuje a je to celý klíč.** „básník Josef Hora" má
    jméno jako `flat` pod obecným jménem, kdežto „Město **Praha**" má
    `nmod`. `flat` znamená, že ty tokeny tvoří JEDNU ZMÍNKU — titul
    a jméno odkazují na jednoho člověka — zatímco `nmod` je samostatný
    přívlastek. „Město Praha" se tedy tímhle nemění, a nemusí se to
    hlídat zvlášť.

    **Hlavou je JMÉNO, ne titul.** „Nad hrobem promluvil básník Josef
    Hora." mluví o JEDNOM člověku; dokud jméno padalo, četla se ta věta
    jako `promluvit(kdo:∀básník)`, tedy o VŠECH BÁSNÍCÍCH. Jméno
    nespadlo jen tak — spadlo a na jeho místě zůstal kvantifikátor,
    který tam nepatří. Je to táž rodina jako W‑48: fakt o někom jiném,
    než o kom věta mluví.

    **A NENÍ TO SLOŽENINA.** `básník_Josef_Hora` by byla třída, která
    není ani básník, ani Hora — přesně jako `město_Praha`.

    **JEN JEDNOTNÉ ČÍSLO, a je to nalezené měřením, ne opatrností.**
    „bratří **Čapků**" má touž stavbu, ale nejsou to jedni bratři jménem
    Čapka — je to SKUPINA dvou lidí, kteří to příjmení nesou. Bez téhle
    stráže by z toho vyšel uzel `·Čapka`, tedy jeden člověk, který
    neexistuje: vada by se jen vyměnila za jinou. Skupinu systém dnes
    z téhle stavby vyrobit neumí, a než ji vyrobí špatně, je lepší, aby
    ji nevyráběl (W‑54). V měřeném korpusu je to 3 zmínky ze 74 a
    VŠECHNY tři jsou „bratří Čapků"; `Number` na hlavě přitom nechyběl
    ani jednou, takže se stráž o nic nedohaduje.
    """
    # Titul je OBECNÉ jméno — `NOUN`. Na `PROPN` se ta stavba nevztahuje:
    # tam už jde o víceslovné jméno („Karel Čapek") a to skládá
    # `name_parts_of`. Zájmeno ani sloveso titul nést nemůže.
    cislo = token.feat("Number")
    # Průnikem, ne rovností (W‑32): `Number=Plur,Sing` je PŘIZNANÁ
    # VÍCEZNAČNOST, ne dvě tvrzení. Chybějící rys stráž nespustí — o čísle
    # se pak neví nic a vyrobit z toho jednoho člověka by byl tichý default.
    if token.upos == "NOUN" and cislo is not None and "Sing" in feature_values(cislo):
        jmena = tuple(
            child
            for child in reading.children(token.index)
            if base_deprel(child.deprel) in NAME_CONTINUATION
            and child.upos == "PROPN"
        )
        if jmena:
            return tuple(sorted(jmena, key=lambda t: t.index))
    return ()


def _composed_mention(token: Token, reading: Reading) -> Mention:
    titul = titled_name_of(token, reading)
    if titul:
        # HLAVOU JE JMÉNO. Titul se do lemmatu NESKLÁDÁ — byla by z něj
        # třída, která není ani básník, ani Hora — ale ani nemizí: nese
        # ho `form`, takže je v přepisu vidět, o čí titul šlo.
        #
        # KAŽDÝ DÍL ZMÍNKY MÁ SVŮJ DŮVOD, ODKUD SE BERE:
        #   `token_index` … HLAVY. Je to kotva do rozboru; na hlavě visí
        #       vztah ke slovesu, takže role a pád se počítají z ní.
        #   `feats` … HLAVY. Pád a číslo přiděluje VĚTA té pozici, a tu
        #       pozici drží hlava („s básníkem Josefem Horou" — Ins).
        #   `upos` … JMÉNA. Tohle je ta druhá půlka opravy: `upos`
        #       neříká, kde zmínka stojí, ale CO JE ZAČ, a rozhoduje se
        #       podle něj kvantifikátor. S `NOUN` by z „básník Josef
        #       Hora" vyšlo `∀Josef_Hora`, tedy tvrzení o VŠECH, kdo se
        #       tak jmenují — jméno by sice bylo v uzlu, ale kvantifikátor
        #       by na jeho místě zůstal ten původní, což je přesně ta
        #       vada, ne její oprava.
        #   `lemma` … JMÉNA. Identita uzlu.
        return Mention(
            lemma="_".join(p.lemma for p in titul),
            form=" ".join([token.form, *(p.form for p in titul)]),
            token_index=token.index,
            upos=titul[0].upos,
            feats=token.feats,
        )
    jmeno = name_parts_of(token, reading)
    if jmeno:
        # VÍCESLOVNÉ JMÉNO. Díly stojí ZA hlavou, protože tak stojí
        # v textu — „Josef Hora", ne „Hora Josef".
        return Mention(
            lemma="_".join([token.lemma, *(p.lemma for p in jmeno)]),
            form=" ".join([token.form, *(p.form for p in jmeno)]),
            token_index=token.index,
            upos=token.upos,
            feats=token.feats,
        )
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


def possessive_of(token: Token, reading: Reading) -> Token | None:
    """Přivlastňovací přívlastek nominálu — nebo `None` (N‑6).

    Rozlišuje se `Poss=Yes`, tedy z ROZBORU, ne z podoby slova.
    """
    for child in reading.children(token.index):
        if base_deprel(child.deprel) == "amod" and child.feat("Poss") == "Yes":
            return child
    return None


def _nominal(token: Token, reading: Reading, name: str) -> RoleReading:
    """Role s **složeným** fillérem a se zapsanými pohlcenými tokeny.

    **Přivlastnění dělá ze jména URČITÝ POPIS** *(N‑6)*. „Filipovo auto"
    nemluví o autech obecně, mluví o JEDNOM autě a přivlastnění je to,
    co ho vybírá. Role proto čeká na ODKAZ, ne na kvantifikátor — a co
    z toho plyne prakticky: „O kterém „auto" mluvíš?" je otázka, na
    kterou existuje odpověď (tah `→=`), kdežto dosavadní „jakou roli
    hraje „Filipovo"?" byla otázka bez odběratele. Podle vlastního
    pravidla projektu je taková otázka horší než ticho.

    **Co se tím schválně NEDĚLÁ.** Nevzniká třída `Filipův_auto`
    (z každého majitele by byla nová třída, N‑2c to vyloučilo záměrně)
    a nevzniká ani vztah `vlastnit(Filip, auto)`. Ten druhý by byl
    významově správný, jenže **rozbor jméno vlastníka NEDÁVÁ**: token je
    `Filipovo` s lemmatem `Filipův`, a dostat se odtud k uzlu `Filip` je
    derivační morfologie, kterou tagger neřeší. Odvodit ji useknutím
    „‑ův" by byl dohad o češtině zadrátovaný do interpretu.

    Přivlastnění tedy dnes **zužuje referenci, ale nezapisuje vlastníka**.
    Je to přiznaná mez, ne tvrzení, že o vlastníkovi nic říct nejde —
    a hlavně už to není otázka, na kterou se nedá odpovědět.
    """
    possessive = possessive_of(token, reading)
    return RoleReading(
        name,
        _composed_mention(token, reading),
        # JMÉNO JE POŘÁD TVAR, dokud ho nějaké patro nepřejmenuje *(W‑62)*.
        # Značka vzniká TADY, protože tady je to jediné místo, kde se ví
        # obojí — jméno i to, jestli je z uzavřeného jádra rolí.
        #
        # Ptá se `CANONICAL_ROLES`, ne `surface_role`: tvar okolnosti dá
        # `surface_role` („v+Loc/Geo"), ale tvar podmětu a předmětu dává
        # `_role_for` z DEPRELU („nsubj:pass"), a porovnávat jméno s jednou
        # z těch dvou funkcí by druhou rodinu tiše minulo. Uzavřené jádro
        # zná obě.
        shaped=name not in CANONICAL_ROLES,
        # Díly víceslovného jména jsou POHLCENÉ, ne ztracené *(B‑21)*:
        # jsou v lemmatu uzlu. Hlásit je jako zahozené by byla nepravda
        # vedle vlastního čtení — táž třída jako W‑20.
        absorbed=tuple(t.index for t in attributes_of(token, reading))
        + tuple(t.index for t in name_parts_of(token, reading))
        + tuple(t.index for t in titled_name_of(token, reading))
        + ((possessive.index,) if possessive else ()),
        awaiting=AWAITING_REFERENCE if possessive else "",
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


def is_bare_genitive(token: Token, reading: Reading) -> bool:
    """Genitiv BEZ PŘEDLOŽKY — jediný, který je přívlastkem *(W‑58)*.

    „synonyma **vesmíru**" je přívlastek; „**u** starověkých filozofů" je
    předložková fráze, tedy okolnost, a tvrdit „synonyma filozofů" je
    o té větě nepravda. Rozdíl je v ROZBORU: u předložkové fráze visí
    dítě s `deprel=case`.

    **Jedno pravidlo pro dvě místa.** Táž otázka padá u přívlastku
    i u konstrukce jádrové relace („X je druh Y"), kde se počítá, kolik
    genitivů věta má — a „podle některých teorií" tam počítat nemá, jinak
    věta o konstrukci přijde jen proto, že nese okolnost navíc. Dvě kopie
    téhle podmínky by se rozešly a nikdo by nevěděl která platí.
    """
    if token.feat("Case") != "Gen":
        return False
    return _preposition_of(token, reading) is None


def _preposition_of(token: Token, reading: Reading) -> Token | None:
    """Předložka závislá na tokenu (`deprel=case`) — nebo `None`."""
    for child in reading.children(token.index):
        if base_deprel(child.deprel) == "case":
            return child
    return None


#: Jak se v tvaru role píše SIGNÁL z rozboru *(W‑61)*. Lomítko, protože
#: `+` už drží předložku s pádem a `:` podtyp — třetí oddělovač dělá
#: z tvaru čitelnou trojici `předložka+pád/signál`.
SIGNAL_MARK = "/"

#: Rys, kterým UD samo odlišuje ZEMĚPISNÉ jméno. Není to seznam slov:
#: `NameType=Geo` dává parser, takže se nemá kde rozejít s korpusem.
GEO_SIGNAL = "Geo"

#: Signál pro LETOPOČET. Taky z rozboru: čtyřciferné `NumType=Card` jako
#: dítě („v roce **1935**", „v letech **1910** – 1911"). Lemma `rok` by
#: byl seznam slov; číslo pod ním je stavba.
YEAR_SIGNAL = "rok"


def role_signal(token: Token, reading: Reading) -> str:
    """Co o filleru říká ROZBOR — `Geo`, `rok`, nebo nic *(W‑61)*.

    **Neurčuje jméno role a určovat ho nesmí.** Že „v Praze" je `kde`
    a „do Prahy" `kam`, plyne z PŘEDLOŽKY A PÁDU, ne z toho, že je Praha
    místo. Signál dělá něco jiného a menšího: ROZDĚLUJE TVAR, který
    dosud slepoval dvě různé věci. `v+Loc` je „v Praze" i „v roce 1935",
    takže jedno naučené mapování muselo být u jedné z nich špatně —
    a nebylo poznat, u které.

    **Sort filleru se použít nedá a je to strukturální důvod** *(§ 3.6)*:
    sort PLYNE Z ROLE (`kde` → `Place`), takže odvodit roli ze sortu je
    kruh. K dispozici je jen to, co stojí v rozboru.

    **Změřeno, ne odhadnuto** (238 vět, kolo #96): ze 42 výskytů `v+Loc`
    má 5 filler s `NameType=Geo`, 11 má za dítě letopočet a **26 nemá
    ani jedno** — „v bytě", „v kostele", „v tomto smyslu", „v angličtině",
    „ve své knize". Těch 26 se dál PTÁ a je to správná odpověď, ne mez:
    rozhodnout je by šlo jen seznamem slov.
    """
    if token.feat("NameType") == GEO_SIGNAL:
        return GEO_SIGNAL
    for child in reading.children(token.index):
        feats = dict(child.feats)
        if (
            feats.get("NumType") == "Card"
            and child.lemma.isdigit()
            and len(child.lemma) == 4
        ):
            return YEAR_SIGNAL
    return ""


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
    # SIGNÁL Z ROZBORU JE SOUČÁST TVARU, ze stejného důvodu jako podtyp
    # *(W‑61)*. `v+Loc` slepoval „v Praze" a „v roce 1935" do jednoho
    # tvaru, takže jedno naučené mapování muselo být u jedné z nich
    # špatně — a nebylo poznat u které. Rozdělený tvar to rozhoduje
    # ZVLÁŠŤ a v jeho jménu je VIDĚT, čím: `v+Loc/Geo`, `v+Loc/rok`.
    # JEN U PŘEDLOŽKOVÉ OKOLNOSTI, a je to hranice měření, ne pohodlí:
    # rozdělovalo se to, co slepovalo MÍSTO A ČAS („v Praze" × „v roce
    # 1935"), a ta rodina je předložková. Holý pád (`Gen`, `Ins`) do ní
    # nepatří a přidat mu signál by znamenalo rozšířit pravidlo tam, kde
    # se nic neměřilo — a rozštěpit tvar, o kterém nikdo neřekl, že je
    # dvojznačný.
    signal = role_signal(token, reading) if preposition else ""
    if signal:
        suffix += f"{SIGNAL_MARK}{signal}"
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

    # DVA ČLENY, JEDNO JMÉNO — ANI JEDEN HO NEDOSTANE *(W‑63)*.
    # „Od 50. let byla ovšem interpretace zcela podřízena ideologii."
    # dává `ovšem` (`advmod:emph`) i `zcela` (`advmod`) roli `jak`,
    # čtení s duplicitou se nesmí vyrobit a NEZBYLO ANI JEDNO — věta
    # skončila jako nepřečtená, ačkoli měla podmět, okolnost i argument.
    #
    # Vybrat jeden z nich by byl tichý default u role, kterou věta
    # VYSLOVILA dvakrát. Oba proto padnou zpátky na SVŮJ TVAR a systém
    # se zeptá — je to táž úvaha jako u `collided` (W‑20), jen o patro
    # dřív: odpověď systém nezná a ptát se na ni je poctivé.
    obsazena = collections.Counter(r.name for r in fixed)
    if any(kolik > 1 for kolik in obsazena.values()):
        fixed = [
            _nominal(
                next(t for t in members if t.index == r.mention.token_index),
                reading,
                surface_role(
                    next(t for t in members if t.index == r.mention.token_index),
                    reading,
                ),
            )
            if obsazena[r.name] > 1
            else r
            for r in fixed
        ]

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
        elif any(base_deprel(token.deprel) == "nsubj" for token in nominals):
            # ZÁKLAD, ne přesná shoda: `nsubj:pass` JE podmět (38× v
            # korpusu), jen trpný. Popisek původu čtení o něm mlčet nemá.
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


def feature_values(feature: str) -> frozenset[str]:
    """Hodnoty jednoho morfologického rysu jako MNOŽINA *(W‑32)*.

    UD píše víceznačný tvar výčtem: „sbírala" nese `Gender=Fem,Neut` a
    `Number=Plur,Sing`, protože týž tvar je ženský jednotný („matka
    sbírala") i střední množný („děvčata sbírala"). **Není to konjunkce
    dvou tvrzení, je to PŘIZNANÁ VÍCEZNAČNOST.**

    Proto se rysy porovnávají PRŮNIKEM, ne rovností. Rovnost žádá, aby byl
    podmět stejně víceznačný jako přísudek — a tím zahodí každou větu,
    kde je tvar homonymní a podmět jednoznačný. To je v češtině běžné,
    ne okrajové.

    **Jedna funkce pro obě vrstvy.** Táž úvaha rozhoduje o kandidátovi na
    antecedent i o zahození čtení; dvě kopie by se rozešly a jedna z nich
    by dřív nebo později začala trestat víceznačnost znovu.
    """
    return frozenset(feature.split(","))


def agrees(left: str | None, right: str | None) -> bool:
    """Shodnou se ty dva tvary v jednom rysu?

    Chybějící rys shodu NERUŠÍ: co se neříká, se nedá popřít (I‑21 v malém).
    Rozhodne až NEPRÁZDNÝ PRŮNIK — tvary se vylučují jen tehdy, když se
    shodnout NEMOHOU.
    """
    if left is None or right is None:
        return True
    return bool(feature_values(left) & feature_values(right))


def _quantified(subject: "Mention", reading: Reading) -> bool:
    """Je podmět řízený KVANTIFIKÁTOREM? *(W‑33)*

    „Několik měření … podpořilo." — čeština má u počitatelných výrazů
    přísudek v neutru singuláru a jméno v genitivu plurálu. Řídícím členem
    shody je ten kvantifikátor, ne to jméno.

    **Rozhoduje jmenovka rozboru, ne slovník.** UD dává `det:numgov`
    právě proto, že ten determinátor ŘÍDÍ PÁD své hlavy — parser to tedy
    neskrývá a není co hádat. Seznam slov („několik", „mnoho", „pět") by
    byl druhé místo, kde se to rozhoduje, a rozešel by se s parserem.
    """
    return any(
        token.head == subject.token_index and token.deprel.startswith("det:numgov")
        for token in reading.tokens
    )


#: Spojky, u kterých koordinace SČÍTÁ. „či" a „nebo" nabízejí alternativu,
#: takže „Vesmír či kosmos JE…" je správně v jednotném čísle; „ale" uvozuje
#: doplnění, ne druhý podmět.
CONJUNCTIVE_LEMMAS = ("a", "i")


def _coordinated(subject: "Mention", reading: Reading) -> bool | None:
    """Koordinace podmětu: `True` = ŽÁDÁ plurál, `False` = plurál i shoda
    s členem jsou obojí správně, `None` = koordinace tu není *(W‑35)*.

    **Tři stavy, ne dva, a je to nutné.** Kdyby se „koordinace, která
    plurál nežádá" slila s „žádná koordinace", spadla by taková věta na
    obyčejné porovnání s PRVNÍM ČLENEM — a „Nad hrobem **promluvili**
    básník Josef Hora, …" by padla na tom, že „básník" je singulár.
    Přesně to se stalo při prvním zúžení a měření to ukázalo.

    „Karel Čapek **a** jeho bratr Josef **byli** aktéry…" Přísudek je
    v plurálu podle CELÉ koordinace, ale UD dává jako `nsubj` první člen
    v singuláru a zbytek věší na něj jako `conj`. Shoda se pak počítá
    proti jednomu členu místo proti celé skupině.

    **Pravidlo je užší, než se na první pohled zdá, a zúžilo ho MĚŘENÍ.**
    Verze „dva a víc členů → plurál" shodila na korpusu sedm vět, které
    jsou bezvadná čeština. Plurál žádá koordinace jen tehdy, když
    SČÍTÁ a přísudek stojí ZA podmětem:

    * **disjunkce** nabízí alternativu, ne součet — „Vesmír **či** kosmos
      **je**…" je správně v jednotném čísle;
    * **přísudek před podmětem** se v češtině smí shodovat s NEJBLIŽŠÍM
      členem — „Ke chřipce **se přidal** zánět ledvin a zápal plic.";
    * `ale` uvozuje doplnění, ne druhý podmět.

    Rozhoduje jmenovka rozboru, ne spojka sama: `conj` je hrana
    koordinace, kdežto „a" spojuje i dvě věty nebo dva přívlastky. Lemma
    spojky se čte až Z TÉ HRANY (`cc` pod členem koordinace).
    """
    members = [
        token
        for token in reading.tokens
        if token.head == subject.token_index and token.deprel == "conj"
    ]
    if not members:
        return None
    marks = [
        token.lemma
        for member in members
        for token in reading.tokens
        if token.head == member.index and token.deprel == "cc"
    ]
    scita = bool(marks) and all(mark in CONJUNCTIVE_LEMMAS for mark in marks)
    head = _predicate_head(reading)
    predikat_vzadu = head is None or head[1].index > subject.token_index
    return scita and predikat_vzadu


def agreement_tier(
    candidates: tuple[Candidate, ...], reading: Reading
) -> tuple[tuple[Candidate, ...], str | None]:
    """Tvrdý filtr: shoda podmětu s přísudkem v ČÍSLE a RODĚ.

    Tohle je patro, které rozhodne motivační případ **bez jakéhokoli
    učení** — „obsahuje" je singulár, „vitamíny" plurál, takže vitamíny
    podmět být nemohou.

    **Porovnává se průnikem hodnot, ne rovností řetězců** *(W‑32)*. Dokud
    se porovnávala rovnost, patro zahazovalo bezvadné české věty:
    „Matka sbírala folklor." padla na tom, že „sbírala" je `Plur,Sing`
    a „matka" jen `Sing`. Odmítnutí bylo hlasité, takže to nebyla vada
    bezpečnosti — ale FALEŠNĚ NEGATIVNÍ ČTENÍ, tedy dobrá věta zahozená
    ze špatného důvodu, a pro systém, který má číst psaný text nativně,
    je to drahá chyba.

    **Rod se kontroluje spolu s číslem, a je to nutné.** Bez něj by po
    přechodu na průnik prošlo „Psi byla v pondělí.": `Psi` je `Plur`
    a `byla` je `Plur,Sing`, takže na čísle je průnik neprázdný.
    Zahazuje to až rod — `Masc` proti `Fem,Neut`. Přidat rod tedy patro
    nezpřísňuje nad rámec toho, co dělalo; nahrazuje jím tu část práce,
    kterou dřív náhodou odváděla rovnost na čísle.

    **U koordinovaného podmětu je řídícím členem CELÁ KOORDINACE**
    *(W‑35)*. „Karel a jeho bratr Josef **byli**…" — dva a víc členů dá
    plurál, ať UD označí jako `nsubj` kohokoli. ROD SE TU NEOVĚŘUJE
    a je to PŘIZNANÁ MEZ: čeština ho u koordinace neřeší průnikem, ale
    pravidly (muž + žena → mužský životný), a tohle patro to pravidlo
    celé nemá. Hádat ho by byl tichý default tam, kde se rozhoduje
    o zahození čtení.

    **U kvantifikovaného podmětu se shoda POČÍTÁ PROTI JINÉMU ČLENU, ne
    přeskakuje** *(W‑33)*. „Několik měření … podpořilo." má přísudek
    v neutru singuláru a jméno v genitivu plurálu; řídícím členem je
    kvantifikátor. Kdyby patro u `det:numgov` shodu jen VYPNULO, byla by
    to díra — prošlo by i „Několik hostů přišli.". Pravidlo je proto
    kladné: ověřuje se, že přísudek odpovídá tomu, co ta konstrukce
    v češtině žádá.
    """
    head = _predicate_head(reading)
    if head is None:
        return candidates, None
    verb_number = head[0].feat("Number")
    verb_gender = head[0].feat("Gender")
    if verb_number is None and verb_gender is None:
        return candidates, None
    survivors = []
    mismatched: list[str] = []
    for candidate in candidates:
        subject = candidate.predication.role(ROLE_SUBJECT)
        if subject is None or _presentational(subject):
            survivors.append(candidate)
            continue
        if _quantified(subject, reading):
            # KVANTIFIKOVANÝ PODMĚT. Řídícím členem shody je kvantifikátor,
            # ne to jméno — a žádá STŘEDNÍ JEDNOTNÉ. Není to výjimka ze
            # shody, je to shoda proti SPRÁVNÉMU členu.
            number_ok = agrees("Sing", verb_number)
            gender_ok = agrees("Neut", verb_gender)
            if not (number_ok and gender_ok):
                mismatched.append("kvantifikovaného podmětu")
                continue
        elif (koordinace := _coordinated(subject, reading)) is not None:
            # KOORDINOVANÝ PODMĚT. Číslo je vlastnost CELÉ koordinace, ne
            # jejího prvního členu — a co přesně žádá, závisí na tom, jestli
            # koordinace SČÍTÁ a kde stojí přísudek.
            #
            # ROD SE TU NEOVĚŘUJE, A JE TO PŘIZNANÁ MEZ, ne opomenutí.
            # Čeština ho u koordinace neřeší průnikem, ale pravidly
            # (muž + žena → mužský životný), a to pravidlo celé nemám.
            # Hádat ho by znamenalo tichý default na místě, kde se
            # rozhoduje o zahození čtení — horší než přiznaná neúplnost.
            gender_ok = True
            if koordinace:
                number_ok = agrees("Plur", verb_number)
            else:
                # Disjunkce nebo přísudek před podmětem: čeština připouští
                # OBOJÍ — plurál podle celku i shodu s členem. Přijímá se
                # tedy obojí a odmítá se jen to, co není ani jedno.
                number_ok = agrees("Plur", verb_number) or agrees(
                    subject.feat("Number"), verb_number
                )
            if not number_ok:
                mismatched.append("koordinovaného podmětu")
                continue
        else:
            number_ok = agrees(subject.feat("Number"), verb_number)
            gender_ok = agrees(subject.feat("Gender"), verb_gender)
        if number_ok and gender_ok:
            survivors.append(candidate)
            continue
        mismatched.append("čísla" if not number_ok else "rodu")
    if len(survivors) == len(candidates):
        return candidates, None
    if "koordinovaného podmětu" in mismatched:
        return tuple(survivors), (
            f"[PROČ: koordinovaný podmět žádá přísudek v MNOŽNÉM čísle "
            f"(shoda se počítá proti celé koordinaci, ne proti jejímu "
            f"prvnímu členu), a tenhle je {verb_number or '?'}]"
        )
    if "kvantifikovaného podmětu" in mismatched:
        return tuple(survivors), (
            f"[PROČ: kvantifikovaný podmět žádá přísudek ve STŘEDNÍM "
            f"JEDNOTNÉM (řídí ho kvantifikátor, ne to jméno), a tenhle je "
            f"{verb_gender or '?'}/{verb_number or '?'}]"
        )
    what = "čísla" if "čísla" in mismatched else "rodu"
    shown = verb_number if what == "čísla" else verb_gender
    return tuple(survivors), (
        f"[PROČ: shoda {what} — přísudek {shown}, "
        f"podmět se s ním shodnout nemůže]"
    )


def _presentational(subject: "Mention | None") -> bool:
    """Ukazovací „to" v prezentační vazbě — „**To** jsou psi."

    ÚZKÁ VÝJIMKA ZE SHODY, a je to fakt o češtině, ne úleva testu. Střední
    „to" v téhle vazbě nezastupuje počitatelný podmět, takže se s
    přísudkem v čísle neshoduje: „To je pes." i „To jsou psi." jsou obojí
    správně, a filtr, který druhou zahodí, zahodí gramatickou větu.

    Ohraničení je záměrně tvrdé — lemma `ten`, `PronType=Dem`, střední
    rod, jednotné číslo. Kdyby se pustilo cokoli šiřšího, přestal by
    filtr chytat motivační případ, kvůli kterému vznikl („Obsahuje citron
    vitamíny?"), a to je horší než neumět jednu vazbu.
    """
    if subject is None:
        return False
    return (
        subject.lemma == "ten"
        and subject.feat("PronType") == "Dem"
        and subject.feat("Gender") == "Neut"
        and subject.feat("Number") == "Sing"
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
    """Role, které zůstaly POVRCHOVÉ — tvar BEZ VÝZNAMU.

    Role, jejíž význam se ví a jen se srazila s jinou toutéž (`v+Loc`
    i `v+Acc` → `kdy`), sem NEPATŘÍ *(W‑20)*. Ptát se na ni znamená ptát
    se na něco, co systém zná, a jediná odpověď, kterou by člověk mohl
    dát, je ta, která kolizi způsobila — otázka bez odběratele.

    **Rozhoduje `shaped`, ne členství v uzavřeném jádru** *(W‑62)*.
    Naučené jméno („proč" u vedlejší věty) mezi kanonické role jádra
    nepatří a patřit nemusí — okolnosti jsou povrchové (§ 12/1) — ale
    NĚKDO HO UŽ POJMENOVAL, takže se na ně ptát je nepravda o vlastním
    stavu. Systém se na `proč` ptal a přitom to jméno sám dostal jako
    odpověď o krok dřív.
    """
    return tuple(
        sorted({r.name for r in predication.roles if r.shaped and not r.collided})
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
    # ODKUD SIGNÁL JE, MUSÍ BÝT VIDĚT *(W‑61)*. Tvar `v+Loc/Geo` sám
    # o sobě vypadá jako vymyšlená kategorie; věta pod ním říká, že to
    # četl PARSER, ne interpret — a že za jinou odpovědí u „v roce 1935“
    # není nedůslednost, ale JINÝ TVAR.
    signaly = sorted(
        {shape.split(SIGNAL_MARK, 1)[1] for shape in shapes if SIGNAL_MARK in shape}
    )
    odkud = ""
    if signaly:
        popis = {
            GEO_SIGNAL: "`NameType=Geo` na filleru",
            YEAR_SIGNAL: "letopočet jako dítě filleru",
        }
        odkud = (
            " (to za lomítkem je SIGNÁL Z ROZBORU — "
            + ", ".join(f"`{sig}` = {popis.get(sig, sig)}" for sig in signaly)
            + " — takže „v Praze“ a „v roce 1935“ jsou DVA RŮZNÉ TVARY "
            "a odpověď na jeden neplatí pro druhý)"
        )
    return (
        f"Nevím, co znamená {which} — je to tvar, ne význam{odkud}. Jak se "
        f"ta role jmenuje (kde, kdy, kudy, odkud, …)?"
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
                    # PŘEJMENOVÁNA — jméno už není tvar *(W‑62)*.
                    roles.append(
                        replace(role, name=options[0].canonical, shaped=False)
                    )
                    continue
                if len(options) == 1:
                    # ZNÁMÁ role, jejíž kanonické jméno už někdo v téhle
                    # větě zabral *(W‑20)*. Není to neznalost a hlásit ji
                    # jako neznalost je nepravda: systém odpověď zná a je
                    # to právě ta, která koliduje. Věta se stejně
                    # nezakotví — ale z jiného důvodu, a ten se má říct.
                    notes.append(
                        f"[KOLIZE: „{role.name}“ i jiná role téže věty "
                        f"znamenají „{options[0].canonical}“ — jedna věta "
                        f"nemůže mít tutéž roli dvakrát]"
                    )
                    roles.append(replace(role, collided=True))
                    continue
                if role.collided:
                    # ZNÁMÁ role, která se srazila UŽ DŘÍV — dnes ji tak
                    # označí patro trpného rodu *(W‑59)*. Hlásit u ní
                    # „[CHYBÍ: co znamená]“ je nepravda: systém odpověď
                    # zná a důvod, proč se nedosadila, právě řekl. Je to
                    # táž úvaha jako o pár řádků výš u kolize naučeného
                    # mapování (W‑20) — jen ta kolize vznikla jinde.
                    roles.append(role)
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


#: Podtyp, kterým UD označuje TRPNÝ PODMĚT. Pojmenovaná konstanta se
#: zdůvodněním vedle *(W‑59)*: `:pass` není nálepka navíc, je to jediné
#: místo, kde rozbor říká, že podmět té věty NENÍ konatel.
PASSIVE_SUBJECT = "nsubj:pass"


def passive_tier() -> Tier:
    """Trpný podmět je PATIENS — přejmenuje `nsubj:pass` na `co` *(W‑59)*.

    **Není to naučený vzor a nesmí jím být.** `:pass` STOJÍ V ROZBORU:
    „Úmysly byly popsány." má podmět, který nic nepopisuje — je to to
    POPISOVANÉ. Ptát se „co znamená role `nsubj:pass`" znamená ptát se na
    něco, co rozbor právě řekl, a byla to třetí nejčastější otázka
    korpusu (19 výskytů). Je to táž cesta jako u W‑47 a W‑48: co je
    v rozboru, se nečte jako neznámé.

    **Vlastní jméno té role bylo ZAPSANÉ ROZHODNUTÍ, ne vada** *(I‑2,
    INV‑11)*: ztotožnit trpný podmět s `kdo` by byl dohad o významu,
    protože konatel to není. Tohle patro ten důvod neruší — dosazuje
    OPAČNOU stranu, tu, kterou `:pass` doopravdy říká.

    **KDYŽ JE `co` OBSAZENÉ, PATRO SE ZEPTÁ, NEPŘEPÍŠE.** „Celá kolekce
    těchto oddělených prostorů se označuje mnohovesmír." má obojí a
    vybrat tiše by znamenalo zahodit roli, kterou věta vyslovila. Změřeno,
    ne odhadnuto: v korpusu je to 1 věta z 19, zbylých 18 `co` volné má.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        out: list[Candidate] = []
        for candidate in candidates:
            roles = candidate.predication.roles
            passive = next((r for r in roles if r.name == PASSIVE_SUBJECT), None)
            if passive is None:
                out.append(candidate)
                continue
            if any(r.name == ROLE_OBJECT for r in roles):
                # OBĚ STRANY VYSLOVENÉ. Přepsat jednu druhou znamená
                # zahodit člen, který ve větě stojí — a poznat by to
                # nešlo, protože obě jsou `co`.
                notes.append(
                    f"[KOLIZE: „{PASSIVE_SUBJECT}“ je trpný podmět, tedy "
                    f"„{ROLE_OBJECT}“, ale „{ROLE_OBJECT}“ už v téhle "
                    f"větě někdo zabral — která z těch dvou je která, "
                    f"z tvaru nepoznám]"
                )
                out.append(
                    Candidate(
                        replace(
                            candidate.predication,
                            roles=tuple(
                                # `collided` UMLČÍ FALEŠNOU OTÁZKU (W‑20):
                                # „co znamená nsubj:pass“ systém ví.
                                # `AWAITING_ROLE_NAME` ZASTAVÍ ZÁPIS
                                # (B‑19): dokud se neví, která ze dvou
                                # stran je `co`, zapsat větu znamená
                                # zapsat roli s povrchovým jménem a po
                                # rozhodnutí ji zapsat podruhé.
                                replace(
                                    r, collided=True, awaiting=AWAITING_ROLE_NAME
                                )
                                if r is passive
                                else r
                                for r in roles
                            ),
                        ),
                        origin=candidate.origin,
                    )
                )
                continue
            notes.append(
                f"[TRPNÝ ROD: „{passive.mention.form}“ je `{PASSIVE_SUBJECT}`, "
                f"tedy PATIENS — role „{ROLE_OBJECT}“ plyne z PODTYPU "
                f"rozboru, ne z naučeného vzoru]"
            )
            out.append(
                Candidate(
                    replace(
                        candidate.predication,
                        roles=tuple(
                            sorted(
                                (
                                    replace(
                                        r,
                                        name=ROLE_OBJECT,
                                        shaped=False,
                                        source=f"trpný rod — podtyp `{PASSIVE_SUBJECT}`",
                                    )
                                    if r is passive
                                    else r
                                    for r in roles
                                ),
                                key=lambda r: r.name,
                            )
                        ),
                    ),
                    origin=candidate.origin,
                )
            )
        return tuple(out), "; ".join(notes) if notes else None

    return tier


def passive_question(predication: Predication) -> str | None:
    """Otázka u SRÁŽKY dvou patiensů *(W‑59)*.

    Vlastní otázka, ne „co znamená role `nsubj:pass`“: TO SYSTÉM VÍ a
    ptát se na to je nepravda o vlastním stavu (W‑20). Neví se něco
    jiného — KTERÁ ZE DVOU VYSLOVENÝCH STRAN je ta popisovaná.
    """
    srazky = [
        role
        for role in predication.roles
        if role.name == PASSIVE_SUBJECT and role.collided
    ]
    if not srazky:
        return None
    druhy = next(
        (r.mention.form for r in predication.roles if r.name == ROLE_OBJECT), "?"
    )
    prvni = srazky[0].mention.form
    return (
        f"Ta věta má DVĚ strany, které obě vypadají jako „{ROLE_OBJECT}“ — "
        f"„{prvni}“ je trpný podmět (`{PASSIVE_SUBJECT}`) a „{druhy}“ stojí "
        f"jako předmět. Která z nich je ta popisovaná? Vybrat sám nemůžu: "
        f"z tvaru se to nepozná a zahodit jednu znamená zahodit člen, "
        f"který ve větě stojí."
    )


#: Na co otevřená role čeká.
AWAITING_QUANTIFIER = "kvantifikátor"
AWAITING_REFERENCE = "odkaz"
#: Role, která na sebe má JÁDROVÉ JMÉNO, ale zatím ho nemá *(B‑19)*.
#: Dokud ho nedostane, věta se NEZAPISUJE: jinak by ji odpověď zapsala
#: podruhé a v bázi by ležely dva výroky o téže větě.
AWAITING_ROLE_NAME = "jméno role"

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
            # PŘESNÁ SHODA ZÁMĚRNĚ: `det:numgov` a `det:nummod` jsou
            # KVANTIFIKÁTORY („několik psů"), ne přívlastky. Složit je do
            # lemmatu by z „několik psů" udělalo druh psa *(W‑47)*.
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
    #: Rodina, která se ptá JEN KDYŽ tvar někdo pojmenoval *(N‑11)*.
    #: Předložková spona je většinou obyčejný lokativní fakt („Petr byl
    #: v Česku."), ne vztah dvou tříd; ptát se u každé by byl výslech
    #: a nabídka by u většiny z nich neměla správnou odpověď.
    only_if_known: bool = False
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
    if subject is None:
        return None
    complement = predication.reading(ROLE_OBJECT)
    if complement is None:
        # Sponový kořen s PŘEDLOŽKOU nedostal jmennou část (N‑4), ale
        # konstrukce to je: „Pondělí je PŘED úterým." Předložka s pádem
        # říká, JAKÝ vztah se tvrdí — přesně jako `druh` u podtřídy.
        others = [r for r in predication.roles if r is not subject]
        if len(others) != 1:
            return None
        other = others[0]
        token = _token_at(other.mention.token_index, reading)
        preposition = _preposition_of(token, reading) if token else None
        case = other.mention.feat("Case")
        if preposition is None or not case:
            return None
        return Construction(
            shape=f"cop:{preposition.lemma}+{case}",
            left=subject.name,
            right=other.name,
            only_if_known=True,
        )

    genitive = [
        role
        for role in predication.roles
        if role is not subject
        and role is not complement
        and (token := _token_at(role.mention.token_index, reading)) is not None
        and is_bare_genitive(token, reading)
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
    if complement.mention.upos not in ("NOUN", "PROPN"):
        # JMENNÝ přísudek, ne jakýkoli. „To auto je modré." je VLASTNOST,
        # ne vztah tříd — ptát se u ní na členství nebo podmnožinu je
        # otázka bez odběratele, ať člověk odpoví cokoli.
        #
        # `PROPN` na pravé straně je ale VLASTNÍ JMÉNO, ne vlastnost:
        # „Micka je Mourek." netvrdí členství (Mourek není třída), tvrdí
        # IDENTITU. Slovní druh obou stran je proto součást tvaru
        # a rozhoduje o tom, která relace to je (N‑10).
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


#: Zájmena, která odkazují do PŘEDCHOZÍHO textu. Osobní a přivlastňovací
#: ve 3. osobě; první a druhá osoba míří na účastníky rozhovoru, ne do
#: textu, a tam by antecedent hledat nešlo.
ANAPHORIC_LEMMAS = ("on", "jeho", "její", "jejich")


#: Závislosti, kterými čeština PODMĚT VYSLOVUJE. Pojmenovaná konstanta,
#: ne literál v podmínce, a je to POČTVRTÉ táž lekce *(B‑18)*: W‑32
#: porovnávala rysy řetězcem, W‑47 deprel řetězcem, W‑48 `upos` výčtem,
#: a tohle byl výčet podmětových závislostí, který znal `nsubj`, ale ne
#: `csubj`.
#:
#: `csubj` je podmět vyjádřený CELOU VĚTOU — „**Je jasné**, že Jan
#: přišel." Rozhodnutí, jestli se z něj dá udělat fillér, je jiná otázka;
#: tohle je jen o tom, co v textu STOJÍ, a stát tam vedlejší věta jako
#: podmět může.
SUBJECT_DEPRELS = ("nsubj", "csubj")

#: Pomocná slovesa, která z kořene dělají PŘÍSUDEK, i když jeho slovní
#: druh je jiný. `aux:pass` je trpný rod („byl pohřben"), `cop` jmenný
#: přísudek („je učitel"), `aux` složený čas.
PREDICATE_AUXILIARIES = ("aux", "cop")


def _is_predicate(root: Token, reading: Reading) -> bool:
    """Je kořen PŘÍSUDEK? Čte se STRUKTURA, ne slovní druh *(W‑48)*.

    Trpný rod má kořen `ADJ` — „Byl **pohřben** na Vyšehradě." je
    příčestí — a pomocné sloveso visí pod ním jako `aux:pass`. Výčet
    slovních druhů (`VERB`, `AUX`) na to byl slepý, takže se celá trpná
    věta bez podmětu zapsala BEZ PODMĚTU, tedy jako fakt o nikom, a nic
    to neřeklo.

    **Potřetí táž třída vad**: W‑32 porovnávala rysy řetězcem, W‑47
    deprel řetězcem, tohle porovnávalo `upos` výčtem. Pokaždé to byla
    kategorie, která má variantu, a pokaždé pomohlo totéž — číst, CO
    V ROZBORU JE, ne jakou to má značku.
    """
    if root.upos in ("VERB", "AUX"):
        return True
    return any(
        token.head == root.index
        and base_deprel(token.deprel) in PREDICATE_AUXILIARIES
        for token in reading.tokens
    )


def prodrop_tier() -> Tier:
    """VĚTA BEZ PODMĚTU — český pro‑drop *(0.1.17)*.

    **V přirozeném textu je to častější než zájmeno.** Životopisný odstavec
    je toho plný: „Narodil se v Malých Svatoňovicích." Podmět tam NENÍ
    VŮBEC — ne že by byl zájmenem.

    **Co se dělo předtím, byla horší vada než neumět pro‑drop.** Věta se
    zapsala jako `narodit(kde:Praha)`, tedy jako fakt O NIKOM, a nic to
    neřeklo. V encyklopedické próze by se do báze ukládaly dekapitované
    věty jedna za druhou a poznat by to nešlo.

    **Řešení je téhož tvaru jako u zájmena, protože příčina je táž.**
    Kandidát se NAVRHUJE z předchozí zakotvené věty, nikdy nedosazuje, a
    rod a číslo na přísudku (byl × byla × byli) je VODÍTKO, NE DŮKAZ.
    Do textu se nepřidávají slova, která tam nejsou: zmínkou role je sám
    přísudek, protože právě on tu shodu nese.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        root = next((t for t in reading.tokens if t.head == 0), None)
        if root is None or not _is_predicate(root, reading):
            return candidates, None
        # ZÁKLAD, ne přesná shoda *(W‑47)*. `nsubj:pass` JE vyslovený
        # podmět — „Karel Čapek byl pohřben…" ho má. Kdyby se sem
        # nezapočítal, patro by u KAŽDÉ trpné věty tvrdilo, že podmět
        # chybí, a ptalo se na antecedent někoho, kdo ve větě stojí.
        vyslovene = [
            t
            for t in reading.tokens
            if t.head == root.index and base_deprel(t.deprel) in SUBJECT_DEPRELS
        ]
        if vyslovene:
            # ROZDÍL MEZI „NEŘEČENO" A „ŘEČENO, NEUMÍM" *(B‑18)*. Věta
            # s podmětem vyjádřeným celou vedlejší větou podmět MÁ; tvrdit
            # o ní, že ho nevyslovila, je nepravdivý výrok o textu — a na
            # jeho základě by systém zval člověka, aby dosadil podmět tam,
            # kde jeden stojí. Mlčet by ale bylo taky nepřesné: dosadit
            # větu za fillér zatím neumíme. Řekne se tedy PŘESNĚ TO.
            vetny = [t for t in vyslovene if base_deprel(t.deprel) == "csubj"]
            if vetny:
                return candidates, (
                    f"[PODMĚT JE CELÁ VĚTA: „{vetny[0].form}“ — věta ho "
                    f"vyslovila, ale dosadit vedlejší větu za podmět "
                    f"zatím neumím]"
                )
            return candidates, None
        # ZMÍNKOU JE NOSITEL LEMMATU PŘÍSUDKU, NE KOŘEN *(W‑58)*.
        # U slovesné věty je to totéž. U SPONY ale kořenem je JMENNÁ
        # ČÁST („byl prvním **předsedou**“) a ta už ve čtení leží jako
        # role `co` — dosadit ji ještě jako `kdo` znamená mít TÝŽ TOKEN
        # VE ČTENÍ DVAKRÁT POD DVĚMA JMÉNY, jednou složeně
        # (`první_předseda`) a jednou holý (`předseda`). Shodu, která je
        # tu vodítkem, nese u spony `cop` („byl“ — Masc Sing), takže
        # správná zmínka je právě on. `_predicate_head` to rozlišení už
        # dělá; patro se ho jen neptalo.
        hlavy = _predicate_head(reading)
        nositel = hlavy[0] if hlavy else root
        feats = dict(nositel.feats)
        if "Gender" not in feats and "Number" not in feats:
            # Přísudek, který o podmětu nic neříká, nedává ani vodítko.
            # Nabízet bez něj kohokoli by bylo hádání.
            return candidates, None
        marked: list[Candidate] = []
        for candidate in candidates:
            if candidate.predication.role(ROLE_SUBJECT) is not None:
                marked.append(candidate)
                continue
            gap = RoleReading(
                ROLE_SUBJECT,
                Mention(
                    lemma=nositel.lemma,
                    form=nositel.form,
                    token_index=nositel.index,
                    upos=nositel.upos,
                    feats=nositel.feats,
                ),
                awaiting=AWAITING_REFERENCE,
                dropped=True,
                source="podmět věta nevyslovila; rod a číslo nese přísudek",
            )
            marked.append(
                Candidate(
                    replace(
                        candidate.predication,
                        # Kanonické setřídění podle JMÉNA role — dvě
                        # stejná čtení musí být týž objekt (I‑22).
                        roles=tuple(
                            sorted(
                                (*candidate.predication.roles, gap),
                                key=lambda role: role.name,
                            )
                        ),
                    ),
                    origin=candidate.origin,
                )
            )
        return marked and tuple(marked) or candidates, (
            f"[BEZ PODMĚTU: „{nositel.form}“ ho nevyslovil — čeká se na "
            f"rozhodnutí, o kom to platí]"
        )

    return tier


def anaphora_tier() -> Tier:
    """Zájmeno ČEKÁ NA ODKAZ — kontext textu *(0.1.16)*.

    Patro nic nerozhoduje a nic nenavrhuje; jen označí roli, jejíž zmínka
    je anaforické zájmeno, jako čekající na rozhodnutí o odkazu. Kandidáty
    nabízí až zakotvení, protože jen ono zná předchozí větu.

    **Proč to musí být tady, a ne jen v otázce.** Otázku umí položit
    zakotvení, ale ODPOVĚĎ (`→=`) hledá roli, která na odkaz čeká — a
    hledá ji v PREDIKACI. Kdyby značka zůstala jen u otázky, systém by se
    zeptal a vzápětí odmítl odpověď se slovy „role na odkaz nečeká". Je to
    táž lekce jako B‑17: stav, na kterém někdo staví, musí mít vlastní
    místo v predikaci, ne jen ve výstupu jednoho kroku.

    **Kvantifikátor se u zájmena neptá.** Rozhodne ho antecedent, takže by
    to byla otázka na něco, co druhá odpověď stejně nastaví.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        marked: list[Candidate] = []
        for candidate in candidates:
            roles = []
            for role in candidate.predication.roles:
                if (
                    role.mention.lemma in ANAPHORIC_LEMMAS
                    and role.mention.upos in ("PRON", "DET")
                    and not role.resolved
                ):
                    notes.append(
                        f"[ODKAZ: „{role.mention.form}“ ukazuje do "
                        f"předchozí věty — čeká se na rozhodnutí]"
                    )
                    roles.append(
                        replace(role, awaiting=AWAITING_REFERENCE, pending=None)
                    )
                    continue
                roles.append(role)
            marked.append(
                Candidate(
                    replace(candidate.predication, roles=tuple(roles)),
                    origin=candidate.origin,
                )
            )
        return tuple(marked), "; ".join(notes) if notes else None

    return tier


def naming_shape(reading: Reading) -> "_Naming | None":
    """Konstrukce „X **se jmenuje** Y" — nebo `None`.

    Rozhodnutelná ze stavby, a proto se DOSAZUJE, ne ptá. Je to táž úvaha
    jako u `PROPN` v podmětu holé spony (N‑2d): tam je slovní druh signál
    individua, tady je zvratné `jmenovat se` lexikálně o pojmenování a
    druhé čtení nemá. Ptát se „co ta věta tvrdí?" by byla otázka bez
    odběratele — v nabídce vztahů dvou tříd správná odpověď není.

    **Strany se berou z DEPRELŮ, ne z pořadí kandidátů.** Generátor u téhle
    věty vyrobí dvě čtení, protože obě jména jsou v nominativu; kdyby se
    tvar rozhodoval podle toho, které přišlo první, zapsalo by se jednou
    `name(Jan, Honza)` a podruhé `name(Honza, Jan)` — a to je rozdíl mezi
    „Jan má přezdívku Honza" a opakem.
    """
    root = next((t for t in reading.tokens if t.head == 0), None)
    if root is None or root.lemma != "jmenovat":
        return None
    children = [t for t in reading.tokens if t.head == root.index]
    if not any(t.deprel.startswith("expl") for t in children):
        # Bez zvratného „se" je „jmenovat" jmenovat DO funkce, ne nazývat
        # se — a to je docela jiné tvrzení.
        return None
    # ZÁKLAD u obou: „Jan se jmenuje Honza." je aktivní, ale trpná
    # varianta („byl nazván…") je táž konstrukce s `nsubj:pass`.
    subject = next(
        (t for t in children if base_deprel(t.deprel) == "nsubj"), None
    )
    obj = next((t for t in children if base_deprel(t.deprel) == "obj"), None)
    if subject is None or obj is None:
        return None
    return _Naming(subject=subject.index, value=obj.index)


@dataclass(frozen=True, slots=True)
class _Naming:
    """Tokeny, které v pojmenování tvoří strany. Drží se INDEXY, ne jména
    rolí: která role se jmenuje `kdo`, se mezi kandidáty liší, a právě
    v tom je celá dvojznačnost, kterou tohle patro rozhoduje."""

    subject: int
    value: int


def naming_tier() -> Tier:
    """POJMENOVÁNÍ ze stavby věty — poslední jádrový predikát, ke kterému
    čeština nevedla.

    `name` není další relace v řadě: je to jediný predikát, který spojuje
    UZEL s tím, jak se mu ŘÍKÁ, a proto na něm visí kanonizace jmen. Dokud
    ho uměla zapsat jen vnitřní cesta (rozdělení uzlu), nedal se z jazyka
    dostat alias — a alias je přesně to, kvůli čemu `name` v jádře je.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        found = naming_shape(reading)
        if found is None:
            return candidates, None
        decided: list[Candidate] = []
        for candidate in candidates:
            by_token = {
                role.mention.token_index: role.name
                for role in candidate.predication.roles
            }
            left = by_token.get(found.subject)
            right = by_token.get(found.value)
            if left is None or right is None:
                continue
            construction = Construction(
                shape="jmenovat_se", left=left, right=right
            )
            decided.append(
                Candidate(
                    as_relation(candidate.predication, Operation.NAME, construction),
                    origin=candidate.origin,
                )
            )
        if not decided:
            return candidates, None
        # Kandidáti, kteří si role `kdo`/`co` prohodili, se přepíší na TÝŽ
        # atom — protože strany určuje DEPREL, ne pořadí čtení. Zůstat
        # dvojznačná by věta neměla: dvojznačná není.
        unique: dict[str, Candidate] = {}
        for candidate in decided:
            unique.setdefault(str(candidate.predication), candidate)
        return tuple(unique.values()), "[STAVBA: „jmenovat se“ → jádrová relace name]"

    return tier


#: Otázka, kterou se uzavření světa POTVRZUJE. Není to menu jako
#: u relace — je jen jedna možnost a jde o to, jestli ji člověk MYSLÍ VÁŽNĚ.
COMPLETE_QUESTION_MARK = "→!∀"


def completeness_shape(predication: Predication, reading: Reading) -> str | None:
    """Skupina, jejíž úplnost věta NAVRHUJE — nebo `None`.

    Tvar je „**to** + spona + **všechen** + jméno v množném čísle": „To
    jsou všichni psi." Nese ho gramatika, ne slovník — `PronType=Tot` na
    determinátoru je totalizace a demonstrativum v podmětu ukazuje na
    dosavadní výčet, ne na nový prvek.

    **Vrací se skupina, ne rovnou `complete(g)`.** Rozdíl je celý smysl
    téhle funkce: co ten tvar znamená v jádře, rozhoduje ČLOVĚK tahem, ne
    interpret. `complete(g)` je LIDSKÉ EPISTEMICKÉ PROHLÁŠENÍ — jediné
    místo, kde I‑21 („absence není negace") ustupuje — a ustupuje jen
    proto, že to někdo výslovně řekl.
    """
    if predication.negated:
        return None
    tokens = reading.tokens
    root = next((t for t in tokens if t.head == 0), None)
    if root is None or root.upos != "NOUN":
        return None
    feats = dict(root.feats)
    if feats.get("Number") != "Plur" or feats.get("Case") != "Nom":
        return None
    children = [t for t in tokens if t.head == root.index]
    if not any(t.deprel == "cop" and t.lemma == "být" for t in children):
        return None
    if not any(
        t.deprel == "det" and dict(t.feats).get("PronType") == "Tot" for t in children
    ):
        return None
    # Demonstrativum v podmětu. Bez něj je „Všichni psi štěkají." obecné
    # tvrzení O psech, ne prohlášení o tom, KTEŘÍ psi jsou — a uzavřít
    # svět na základě věty, která o výčtu vůbec nemluví, by bylo přesně
    # to, co dělat nesmí.
    if not any(
        base_deprel(t.deprel) == "nsubj"
        and dict(t.feats).get("PronType") == "Dem"
        for t in children
    ):
        return None
    return root.lemma


def completeness_tier() -> Tier:
    """UZAVŘENÍ SVĚTA z české věty — a vždycky jen jako NÁVRH.

    **Tohle patro se nikdy nic nenaučí, a je to schválně.** Ostatní tahy
    učí TVAR: jedna odpověď na „Kočka je savec." zavře celou třídu vět,
    protože „jak se čte tahle stavba" je vlastnost jazyka. Uzavření světa
    ale vlastnost jazyka není — je to epistemický stav MLUVČÍHO v jednom
    okamžiku o jedné skupině. Že dnes někdo dopočítal své psy, neopravňuje
    zavřít příště kočky, ani tytéž psy za měsíc.

    Cena chyby je tu navíc nejvyšší v celém systému: špatně zapsané
    uzavření vyrobí `N` tam, kde má být `U` — nevědomost vydávaná za
    znalost, tedy právě to, co tenhle projekt dělat nesmí. Proto se
    `complete` nedosadí NIKDY, ani při jednoznačném tvaru.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        notes: list[str] = []
        decided: list[Candidate] = []
        for candidate in candidates:
            predication = candidate.predication
            group = completeness_shape(predication, reading)
            if group is None:
                decided.append(candidate)
                continue
            notes.append(
                f"[UZAVŘENÍ SVĚTA: navrženo pro „{group}“ — "
                f"{COMPLETE_QUESTION_MARK}, nikdy tiše]"
            )
            decided.append(
                Candidate(
                    replace(predication, pending_complete=group),
                    origin=candidate.origin,
                )
            )
        return tuple(decided), "; ".join(notes) if notes else None

    return tier


def complete_question(predication: Predication) -> str | None:
    """Otázka na uzavření světa — jediná otázka systému, která člověka
    upozorňuje na DŮSLEDEK, ne na neznalost.

    U ostatních otázek systém neví a ptá se. Tady ví přesně, co se stane,
    a ptá se, jestli to člověk chce: od téhle chvíle přestane na kohokoli
    mimo výčet odpovídat „nevím" a začne odpovídat „ne".
    """
    group = predication.pending_complete
    if not group:
        return None
    return (
        f"Mám „{group}“ prohlásit za UZAVŘENOU skupinu? Znamená to, že "
        f"o každém, kdo v dosavadním výčtu není, budu nadále odpovídat NE, "
        f"ne NEVÍM — a je to jediné místo, kde z nepřítomnosti dělám závěr."
    )


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
        return replace(predication, pending_relation=shape), (
            f"[POZOR: tvar {shape} připouští "
            + " nebo ".join(m.operation.value for m in matches)
            + f" — {RELATION_QUESTION_MARK}{shape}]"
        )
    if not matches:
        if found.only_if_known:
            # Tvar, který nikdo nepojmenoval, a rodina, kde je to
            # NORMÁLNÍ. Ptát se tu by znamenalo nabízet menu, ve kterém
            # správná odpověď není: „Petr byl v Česku." není vztah dvou
            # tříd, je to fakt o Petrovi.
            return predication, None
        return replace(predication, pending_relation=shape), (
            f"[CHYBÍ: co ta stavba tvrdí — tvar {shape} "
            f"{RELATION_QUESTION_MARK}{shape}]"
        )
    operation = matches[0].operation
    return (
        as_relation(predication, operation, found),
        f"[STAVBA: tvar {shape} → jádrová relace {operation.value}]",
    )


def as_relation(
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

    quantifier = (
        None if operation in UNQUANTIFIED_RELATIONS else Quantifier.SELF
    )

    def as_class(role: RoleReading, name: str) -> RoleReading:
        # `absorbed` se ZÁMĚRNĚ nepředává: `replace` ho zdědí z role, kterou
        # složil `generate`. Přepsat ho tady na prázdno by přivlastnilo
        # skládání téhle funkci — a přívlastek by se vzápětí ohlásil jako
        # ztracený člen, ačkoli v lemmatu je.
        return replace(
            role,
            name=name,
            shaped=False,
            quantifier=quantifier,
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


def relation_question(predication: Predication) -> str | None:
    """Otázka na to, co konstrukce tvrdí — nebo `None`.

    Počítá se z HOTOVÉ predikace, ne ze stopy *(B‑17)*. Stopa je log
    jednoho tahu: odpověď na kvantifikátor ji zahodila a otázka na relaci
    se tím ztratila — věta se zapsala jako obyčejný vztah, přestože se
    o její konstrukci pořád nevědělo. Táž lekce jako N‑3 a G‑4.
    """
    shape = predication.pending_relation
    if not shape:
        return None
    # Nabídka se skládá z `RELATIONAL`, ne z ručního výčtu: ručně psaný
    # seznam by po přidání relace zůstal starý a systém by se ptal na
    # míň, než umí — a nikdo by si toho nevšiml, protože otázka by pořád
    # dávala smysl.
    menu = ", ".join(sorted(op.value for op in RELATIONAL))
    return f"Co ta věta tvrdí o vztahu těch dvou? Tvar je {shape} — {menu}?"


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
                    # Role, která čeká na ODKAZ, kvantifikátor nepotřebuje:
                    # určitý popis žádnou skupinu neotvírá, ukazuje na uzel.
                    # Bez téhle podmínky by patro přepsalo `awaiting`
                    # a z „Filipovo auto" by se zase ptalo na kvantifikátor
                    # — tedy na něco, co se u určitého popisu neurčuje.
                    or role.awaiting == AWAITING_REFERENCE
                    # Strany jádrové relace nad ČASEM nebo MÍSTEM
                    # kvantifikátor nenesou (§ 3.6) — `RoleTerm` by ho
                    # u nich ani nepřipustil, takže by to byla otázka
                    # bez odběratele.
                    or candidate.predication.relation in UNQUANTIFIED_RELATIONS
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


def genitive_attributes(
    reading: Reading, predication: Predication
) -> tuple[tuple[str, str, int], ...]:
    """Genitivní přívlastky jako `(hlava, genitiv, token)` *(W‑39)*.

    Hlava musí být JMÉNO, které je ve čtení — jinak by vztah visel na
    něčem, o čem věta nemluví. Genitiv sám ve čtení není a ani být nemá:
    není to role slovesa.

    **Měřením doložených významů je pět** (předmět děje, původce děje,
    nositel vlastnosti, část z celku, míra a druh) a liší se PRÁVĚ TÍM,
    kterou roli genitiv v reifikovaném vztahu plní — `chov(co:zvíře)`
    proti `péče(kdo:majitel)`. Menu tedy není nový druh rozhodnutí, je to
    otázka na JMÉNO ROLE; a protože „přínos Němcové" a „popis Němcové"
    mají identický rozbor, rozhodnout ji musí člověk.
    """
    # PÁRUJE SE PŘES TOKEN, NE PŘES LEMMA *(W‑58)*. Zmínka ve čtení je
    # SLOŽENÁ: „prvním předsedou odboru“ má v rozboru hlavu `předseda`,
    # ale ve čtení leží `první_předseda`, takže shoda lemmat selže a
    # přívlastek se přehlédne. Je to POSEDMÉ táž rodina (W‑32, W‑47,
    # W‑48, B‑18, B‑22, W‑53): kategorie porovnaná přesnou shodou tam,
    # kde hodnotu skládá jiná vrstva. Index tokenu je kotva, kterou
    # skládání nemění — a přesně proto si ji W‑53 nechala na hlavě.
    #
    # A vrací se LEMMA ZMÍNKY, ne lemma tokenu: přívlastek má viset na
    # tom uzlu, o kterém věta mluví, tedy na `první_předseda`.
    ve_cteni = {
        role.mention.token_index: role.mention.lemma
        for role in predication.roles
    }
    # GENITIV, KTERÝ SI UŽ NÁROKUJE JÁDROVÁ RELACE, PŘÍVLASTEK NENÍ
    # *(W‑58)*. „Petrovice jsou součástí **Plzně**." a „byl prvním
    # předsedou **odboru**." mají STAVBU IDENTICKOU — u spony je jmenná
    # část kořenem a genitiv jejím dítětem. Rozlišit je ze stromu nejde;
    # rozlišuje je STAV, který o kus výš nastavilo patro jádrové relace:
    # u první věty čeká odpověď `→⊆` a ten genitiv je JEDNA JEJÍ STRANA.
    # Vzít mu ho znamená, že odpověď nemá s čím pracovat.
    root = reading.root()
    narokovany = (
        root.index if predication.pending_relation and root is not None else None
    )
    najdene: list[tuple[str, str, int]] = []
    for token in reading.tokens:
        if token.deprel != "nmod" or not is_bare_genitive(token, reading):
            continue
        head = _token_at(token.head, reading)
        if head is None or head.upos not in ("NOUN", "PROPN"):
            continue
        if head.index not in ve_cteni or head.index == narokovany:
            continue
        najdene.append((ve_cteni[head.index], token.lemma, token.index))
    return tuple(najdene)


def attribute_question(predication: Predication) -> str | None:
    """Otázka na význam genitivního přívlastku *(W‑39)*.

    Ptá se na JMÉNO ROLE, protože právě jím se ty významy liší. A ptá se
    U KAŽDÉ VĚTY ZNOVU: „chov zvířat" a „péče majitele" mají týž tvar
    a opačný směr, takže naučit ho jako tvar by znamenalo přečíst druhou
    větu naruby.
    """
    if not predication.pending_attribute:
        return None
    parts = [
        f"„{hlava} {genitiv}“"
        for hlava, genitiv, _ in predication.pending_attribute
    ]
    return (
        "Co ten přívlastek v genitivu tvrdí — " + ", ".join(parts) + "? "
        "Zapíšu to jako vztah vedle věty; řekni, jakou roli v něm ten "
        "genitiv hraje (co, kdo, whole, …). Ptám se u každé věty znovu: "
        "„chov zvířat“ a „péče majitele“ mají týž tvar a opačný směr."
    )


def subordinate_clauses(reading: Reading) -> tuple[tuple[str, str, int], ...]:
    """Vedlejší věty jako `(spojka, sloveso, token)` *(W‑45)*.

    Bere se JEN `advcl` pod PŘÍSUDKEM hlavní věty a JEN se spojkou
    (`mark`). Obojí je stráž, ne zúžení z pohodlí:

    * `advcl` pod jménem („programy, pokud se jedná o psa") není
      okolnost hlavního děje, ale přívlastek toho jména — jiný vztah,
      který patří k `acl`, ne sem;
    * bez spojky není z čeho jméno role přečíst, a hádat ho z pořadí slov
      by znamenalo vymyslet si význam (INV‑11).

    Vrací se SPOJKA, ne rovnou jméno role: co ta spojka znamená, je
    naučené a odvolatelné tvrzení v lexikonu. Kdyby to rozhodovala tahle
    funkce, byl by v interpretu schovaný seznam českých spojek.
    """
    head = _predicate_head(reading)
    if head is None:
        return ()
    najdene: list[tuple[str, str, int]] = []
    for token in reading.tokens:
        if token.head != head[1].index:
            continue
        if token.deprel != "advcl":
            # PODTYP SE VYLUČUJE VÝSLOVNĚ *(W‑47)*, ne řetězcovou shodou.
            # `advcl:pred` je DOPLNĚK („ukázalo se JAKO snižující"), ne
            # okolnost: neodpovídá na proč ani kdy, ale na to, ČÍM se ta
            # věc ukázala být. Sémanticky patří k `xcomp`, který se
            # skládá do přísudku, ne přidává roli. V korpusu je ho 30
            # výskytů proti 21 holým `advcl`, takže na náhodě stát nesmí.
            continue
        marks = [
            t.lemma
            for t in reading.tokens
            if t.head == token.index and t.deprel == "mark"
        ]
        if not marks:
            continue
        najdene.append((marks[0], token.lemma, token.index))
    return tuple(najdene)


def subordinate_tier(lexicon: Lexicon) -> Tier:
    """Vedlejší věta jako ROLE hlavní predikace *(W‑45)*.

    „Odjel, **protože** pršelo." — vedlejší věta je okolnost hlavního
    děje, tedy jeho role, a jméno té role nese SPOJKA. Tím se liší od
    genitivního přívlastku: tam byl směr vlastností VĚTY a nešlo se ho
    naučit, tady je odpověď v TVARU, takže naučit se smí a druhá věta
    s touž spojkou se neptá.

    **Fillerem je DĚJ, ne celá vnořená predikace.** Vedlejší věta se
    reifikuje svým slovesem — `odjet(proč:∃pršet)` — a její vlastní
    členy zůstávají ztracené, dokud je někdo nepojmenuje. Je to táž
    volba jako u přívlastku: reifikovat, neřetězit, jádro neverzovat.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        found = subordinate_clauses(reading)
        if not found:
            return candidates, None
        notes: list[str] = []
        out: list[Candidate] = []
        for candidate in candidates:
            roles = list(candidate.predication.roles)
            taken = {r.name for r in roles}
            for spojka, sloveso, token_index in found:
                shape = f"advcl:{spojka}"
                options = lexicon.role_candidates(shape)
                name = options[0].canonical if len(options) == 1 else shape
                if name in taken:
                    continue
                taken.add(name)
                notes.append(
                    f"[VEDLEJŠÍ VĚTA: „{spojka}“ → role {name}"
                    + ("" if len(options) == 1 else " — tvar bez významu")
                    + "]"
                )
                roles.append(
                    RoleReading(
                        name,
                        Mention(
                            lemma=sloveso,
                            form=sloveso,
                            token_index=token_index,
                            upos="VERB",
                        ),
                        quantifier=Quantifier.EXISTS,
                        source=f"vedlejší věta se spojkou „{spojka}“",
                        # Dokud role nemá JÁDROVÉ jméno, věta se nesmí
                        # zapsat *(B‑19)*. Než tohle patro vzniklo, byla
                        # vedlejší věta ZTRACENÝ ČLEN a zápis blokovala;
                        # patro z ní udělalo roli, ale tu zábranu jí
                        # nedalo — a odpověď `→@` pak větu zapsala
                        # PODRUHÉ, jednou s povrchovým jménem a podruhé
                        # s jádrovým. Ten první výrok by nikdo neodvolal.
                        # Čeká se jen tehdy, když jméno role zůstalo
                        # POVRCHOVÝM TVAREM. Naučené jméno („proč") mezi
                        # kanonické role jádra nepatří a patřit nemusí —
                        # okolnosti jsou povrchové (§ 12/1) — takže test
                        # na `CANONICAL_ROLES` by blokoval napořád.
                        awaiting=AWAITING_ROLE_NAME if name == shape else "",
                        # TÁŽ PODMÍNKA, TÁŽ ZNAČKA *(W‑62)*. Roli tady
                        # nevyrábí `_nominal`, takže se značka musí
                        # nastavit i tady — a je to přesně to, co ji
                        # dělá spolehlivou: kdo roli vyrobí, ten ví,
                        # jestli jí dal jméno, nebo tvar.
                        shaped=name == shape,
                    )
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


def title_claims(
    reading: Reading, predication: Predication
) -> tuple[tuple[str, str, int], ...]:
    """Co titul TVRDÍ o tom, koho pojmenovává *(W‑55)*.

    Vrací `(jméno, titul, token)`. „básník Josef Hora“ tvrdí DVĚ věci —
    že promluvil a že je básník. Zapisovala se jedna a o druhé systém
    říkal „nikdo to neřekl“; jenže **ta věta to řekla**. Mezera, která
    o sobě lže, je horší než mezera.

    **Stráže se NEOPISUJÍ, ptá se `titled_name_of`.** Tím platí i tady
    všechno, co se u W‑53 a W‑54 změřilo: `flat` (ne `nmod`, takže „Město
    Praha“ tudy nejde), `PROPN` pod `NOUN` a JEDNOTNÉ ČÍSLO (takže „bratří
    Čapků“ tudy nejde taky). Druhá kopie těch podmínek by se s první
    rozešla a nikdo by nevěděl která.

    **Jméno musí být VE ČTENÍ**, stejně jako u genitivního přívlastku:
    tvrzení o někom, o kom věta nemluví, by viselo na uzlu, který se
    v predikaci nevyskytuje.
    """
    ve_cteni = {role.mention.lemma for role in predication.roles}
    najdene: list[tuple[str, str, int]] = []
    for token in reading.tokens:
        jmena = titled_name_of(token, reading)
        if not jmena:
            continue
        jmeno = "_".join(part.lemma for part in jmena)
        if jmeno not in ve_cteni:
            continue
        najdene.append((jmeno, token.lemma, token.index))
    return tuple(najdene)


def title_question(predication: Predication) -> str | None:
    """Otázka na to, co titul tvrdí *(W‑55)*.

    **PTÁ SE, NEDOSAZUJE — a je to změřené rozhodnutí, ne opatrnost.**
    Zapsat `member` rovnou z tvaru je odvození z konstrukce, tedy totéž,
    co se u `same_as` z apozice odmítlo. Rozdíl je, že rozbor tuhle
    stavbu rozlišuje… jenže **měření říká, že tvar sám o významu
    nerozhoduje**. Ze 71 zmínek v měřeném korpusu:

      * 29 je POVOLÁNÍ — „básník", „spisovatel", „historik", „astronom".
        Tam je `member` přesně to, co věta tvrdí.
      * 24 je ÚŘAD DRŽENÝ V ČASE — „prezident Masaryk", „ministr",
        „předseda", „primátor". `member(Masaryk, prezident)` bez času
        tvrdí, že jím je pořád; Masaryk zemřel v roce 1937.
      * 18 je PŘÍBUZENSTVÍ — „bratr Josef Čapek", „matka", „dcera".
        „bratr" není třída, do které se patří: je to vztah K NĚKOMU,
        a ten druhý ve větě často není. `member(Josef_Čapek, bratr)`
        tvrdí „Josef Čapek je bratr", což není, co věta říká.

    Tvar je u všech tří TÝŽ. Kdyby se zapisovalo ze tvaru, byly by dvě
    třetiny zápisů buď bezčasé o něčem časovém, nebo neúplné o vztahu —
    a byly by v bázi jako doložený fakt. Proto se **nabízí a ptá**: to,
    co věta říká, se ohlásí, a rozhodne člověk.

    **A ptá se na DRUH, ne na „ano/ne"** *(W‑57)*. Kdyby stačilo
    odkliknout, vyrobilo by potvrzení u úřadu tvrzení, které platí ŠÍŘ,
    než co věta říká — a šířku nikdo neřekl, jen ji nikdo nezastavil.
    Čas by to spravil, jenže **v korpusu žádný použitelný není**: ze 39
    zmínek visí čas na titulu u čtyř a všechny čtyři jsou ŽIVOTNÍ DATA
    v závorce (1902–1968), ne doba držení funkce; u úřadů je to NULA.
    Není to tedy úloha o čase v jádře — nemá se co zapsat.
    """
    if not predication.pending_title:
        return None
    parts = [
        f"„{titul} {jmeno.replace('_', ' ')}“"
        for jmeno, titul, _ in predication.pending_title
    ]
    return (
        "Ta věta tvrdí ještě tohle: " + ", ".join(parts) + ". Zapíšu to "
        "jako členství vedle věty, ale sám to neudělám a NEPTÁM SE JEN "
        "„ano/ne“ — potřebuju vědět, ČÍM ten titul je. POVOLÁNÍ („básník "
        "Josef Hora“) zapíšu; ÚŘAD DRŽENÝ V ČASE („prezident Masaryk“) "
        "nezapíšu, protože bezčasé členství by platilo šíř, než co ta "
        "věta říká — Masaryk byl prezident v nějakém období, ne pořád. "
        "Z rozboru se to rozeznat nedá: „prezident“ a „básník“ v něm "
        "vypadají stejně. Povolání, nebo úřad?"
    )


def title_tier() -> Tier:
    """Tvrzení titulu jako ČEKAJÍCÍ DRUHÝ VÝROK *(W‑55)*.

    Patro nic nedosazuje a nic neblokuje — jen označí, že vedle věty leží
    tvrzení, které věta vyslovila a jádro ho samo zapsat nesmí.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        oznacene: list[Candidate] = []
        notes: list[str] = []
        for candidate in candidates:
            found = title_claims(reading, candidate.predication)
            if not found:
                oznacene.append(candidate)
                continue
            notes.append(
                "[TITUL TVRDÍ: "
                + ", ".join(
                    f"„{t} {j.replace('_', ' ')}“" for j, t, _ in found
                )
                + " — výrok vedle věty, čeká se na potvrzení]"
            )
            oznacene.append(
                Candidate(
                    replace(candidate.predication, pending_title=found),
                    origin=candidate.origin,
                )
            )
        return tuple(oznacene), "; ".join(notes) if notes else None

    return tier


def attribute_tier() -> Tier:
    """Genitivní přívlastek jako ČEKAJÍCÍ DRUHÝ VÝROK *(W‑39)*.

    Patro nic nedosazuje a nic neblokuje — jen označí, že vedle věty leží
    vztah, jehož význam zná až člověk.
    """

    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str | None]:
        oznacene: list[Candidate] = []
        notes: list[str] = []
        for candidate in candidates:
            found = genitive_attributes(reading, candidate.predication)
            if not found:
                oznacene.append(candidate)
                continue
            notes.append(
                "[PŘÍVLASTEK: "
                + ", ".join(f"„{h} {g}“" for h, g, _ in found)
                + " — vztah vedle věty, čeká se na jméno role]"
            )
            # BUĎ PŘÍVLASTEK, NEBO ROLE — NE OBOJÍ *(W‑58)*. U slovesné
            # věty je genitiv VNUK kořene („chov **zvířat** je náročný“)
            # a rolí se nestane sám od sebe. U SPONY je ale jmenná část
            # KOŘENEM, takže její genitiv je jeho DÍTĚ — a stane se rolí
            # predikace, ačkoli je to týž vztah dvou jmen uvnitř fráze.
            # Stavba se liší, zacházení se lišit nesmí: věta by jinak
            # o jednom členu tvrdila dvě věci najednou a na tu roli by se
            # ptala „co znamená“, ačkoli právě řekla, že je to přívlastek.
            prislovecne = {token_index for _, _, token_index in found}
            oznacene.append(
                Candidate(
                    replace(
                        candidate.predication,
                        roles=tuple(
                            role
                            for role in candidate.predication.roles
                            if role.mention.token_index not in prislovecne
                        ),
                        pending_attribute=found,
                    ),
                    origin=candidate.origin,
                )
            )
        return tuple(oznacene), "; ".join(notes) if notes else None

    return tier


def lost_members(
    reading: Reading, predication: Predication
) -> tuple[tuple[Token, str], ...]:
    """Ztracené významové členy i s jejich tvarem.

    **Genitivní přívlastek mezi ně NEPATŘÍ** *(W‑39)*. Není to role
    slovesa, která by z věty vypadla — je to vztah dvou jmen uvnitř
    fráze, tedy druhý výrok vedle věty. Hlásit ho jako ztrátu znamenalo
    zablokovat zápis věty, které nechybí predikát, ale přívlastek.
    """
    attribute_tokens = {token for _, _, token in genitive_attributes(reading, predication)}
    return tuple(
        (token, lost_shape(token, reading))
        for token in dropped_tokens(reading, predication)
        if token.index not in attribute_tokens
    )


def _dropped_note(reading: Reading, predication: Predication) -> str | None:
    """Co z věty vypadlo — a genitivní přívlastek mezi to NEPATŘÍ.

    Hlásit u něj „pro tenhle vztah role není" by bylo NEPRAVDA vedle
    vlastní otázky: systém v témže tahu říká, že na ten přívlastek čeká
    a ptá se na jeho roli. Dvě hlášky o jedné věci, které si odporují,
    jsou horší než jedna — je to táž třída jako W‑20.
    """
    attribute_tokens = {
        token for _, _, token in genitive_attributes(reading, predication)
    }
    lost = [
        token
        for token in dropped_tokens(reading, predication)
        if token.index not in attribute_tokens
    ]
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
    # KOLIZE I MEZI OKOLNOSTMI, NE JEN MEZI JÁDROVÝMI ČLENY *(W‑63)*.
    # „byl často služebně překládán" má dva `advmod`, oba dostanou `jak`
    # a oba mají TÝŽ TVAR, takže je nerozliší ani pád zpátky na tvar.
    # Věta se přečíst nedá — ale hlásit u ní „nemá ani jeden člen, který
    # bych uměl pojmenovat" je NEPRAVDA O TEXTU: členy má, umí je
    # pojmenovat, a právě to je ten problém. Je to táž rodina jako W‑20,
    # jen o patro dřív.
    okolnosti = [
        token
        for token in reading.children(anchor.index)
        if token.deprel not in NOMINAL_DEPRELS
        and token.deprel != "cop"
        and _role_for(token, reading) is not None
    ]
    tvary = [surface_role(token, reading) for token in okolnosti]
    srazene = sorted({t for t in tvary if tvary.count(t) > 1})
    if srazene:
        slova = ", ".join(
            f"„{token.form}“"
            for token in okolnosti
            if surface_role(token, reading) in srazene
        )
        return (
            "dva členy mají týž tvar ("
            + ", ".join(srazene)
            + f") a chtějí touž roli — {slova}. Který je který, "
            "z rozboru nepoznám"
        )
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
        # POHLCENÝ PŘÍVLASTEK NENÍ NEPOJMENOVANÝ ČLEN *(W‑63)*. „Úrazy
        # způsobené pády." má jediné dítě `amod`, jenže to je PŘÍVLASTEK
        # a `generate` ho SKLÁDÁ DO ZMÍNKY hlavy. Hlásit u něj „neumím ho
        # pojmenovat" je nepravda o vlastní práci: neumí se z něj udělat
        # ROLE, protože rolí není — je to část jména.
        pohlcene = {
            attribute.index
            for attribute in attributes_of(anchor, reading)
        }
        unmapped = sorted(
            {
                t.deprel
                for t in reading.children(anchor.index)
                if t.deprel != "punct" and t.index not in pohlcene
            }
        )
        # NADPIS SPLYNULÝ S VĚTOU *(W‑64)*. „Obezita: Domácí mazlíčci trpí
        # nadváhou." má kořenem NADPIS a skutečná věta pod ním visí jako
        # `appos` — se svým podmětem i přísudkem. Říct u ní „nemá ani
        # jeden člen, který bych uměl pojmenovat" je NEPRAVDA O TEXTU:
        # členy tam jsou, jen ne pod tím kořenem.
        #
        # ČÍST SE TO NEZAČNE, a je to rozhodnutí, ne mez. Přesadit kořen
        # by znamenalo rozhodnout, že nadpis do promluvy nepatří — a to
        # je výrok o TEXTU, ne o rozboru. Rozdělit dvojí text je práce
        # SEGMENTACE, tedy měřicí vrstvy; jádro to jen PŘIZNÁ, místo aby
        # o sobě tvrdilo nepravdu. Táž volba jako u B‑18.
        veta_v_apozici = [
            token
            for token in reading.children(anchor.index)
            if base_deprel(token.deprel) == "appos"
            and (
                token.upos == "VERB"
                or any(
                    child.deprel == "cop" for child in reading.children(token.index)
                )
            )
        ]
        if veta_v_apozici:
            uvnitr = veta_v_apozici[0]
            return (
                f"„{head[0].form}“ vypadá jako NADPIS: skutečná věta "
                f"(„{uvnitr.form}“ i s vlastními členy) pod ním visí jako "
                f"APOZICE, takže kořenem rozboru není přísudek. Rozdělit "
                f"nadpis od věty je práce segmentace, ne čtení"
            )
        if not unmapped and pohlcene:
            return (
                f"„{head[0].form}“ je JMENNÁ FRÁZE, ne věta: jediné, co "
                f"pod ním visí, je přívlastek, a ten se skládá do zmínky "
                f"— role z něj nevzniká"
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
