"""Zlatá sada — české věty dialogů A–F s FIXOVANÝM rozborem.

Dodatek G, bod 6. Smysl je jediný a je to smysl akceptačního testu:
**napsat českou větu a očekávanou strukturu dřív, než se ta cesta postaví**,
a pak ji držet.

**Proč je rozbor tady jako data, a ne z běžící služby.** Kdyby si sada
sáhla na `cb-udpipe`, měřila by dvě věci najednou — jestli conbond4 čte
větu správně, a jestli je zrovna nasazený týž model. Upgrade UDPipe by
rozbil všech šest dialogů naráz a nebylo by z výstupu poznat, co se
vlastně změnilo. Rozbor se proto fixuje a nese `PROVENANCE`; až se model
změní, přepíše se sada **vědomě**, s viditelným diffem CoNLL‑U.

**Co sada od L‑5 ověřuje navíc.** Že se z věty stane FAKT. Do L‑5 končila
u vybraného čtení, protože převod zmínky na uzel nestál; teď devět z
jedenácti vět projde až do báze a zbylé dvě neprojdou z důvodu, který
sada pojmenovává (`asks`, `refuses`). Přesné znění zapsaných formulí
fixuje až L‑7 — tady jde o to, ŽE se zapsalo, ne o pět domén.

Rozbory jsou psané ručně podle UD pro češtinu (PDT). Kde je tvar
homonymní, drží se sada toho, co skutečný parser dělá — u „Obsahuje
citron vitamíny?" **nedá podmět**, protože nominativ je tvarově shodný
s akuzativem. Právě proto ta věta v zadání je.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core_semantics.lexicon import (
    LearnedPattern,
    Lexicon,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Token, Utterance, recorded

#: Jedna provenience pro celou sadu. `RecordedOracle` míchání odmítá —
#: transkript, který nese dva rozbory, není čím fixovaný.
PROVENANCE = "udpipe2 model=cs_all-ud-2.17-251125 tokenizer=6247b8b7a5c8"


def tok(
    index: int,
    form: str,
    lemma: str,
    upos: str,
    head: int,
    deprel: str,
    *,
    extra: dict[str, str] | None = None,
    **feats: str,
) -> Token:
    """Token nahrávky. `extra` je pro rysy, jejichž jméno není platný
    identifikátor — UD má například `Gender[psor]` u přivlastňovacích
    tvarů, a ten se jako pojmenovaný argument předat nedá."""
    return Token(
        index=index,
        form=form,
        lemma=lemma,
        upos=upos,
        head=head,
        deprel=deprel,
        feats=tuple(sorted({**(extra or {}), **feats}.items())),
    )


@dataclass(frozen=True, slots=True)
class Golden:
    """Jedna zlatá věta.

    `predication` je očekávaný **řetězec** čtení, ne objekt: kdyby se
    porovnávaly objekty, test by prošel i tehdy, kdyby se rozbil `__str__`,
    a právě ten je to, co uvidí člověk v transkriptu.

    `notes` jsou úryvky, které MUSÍ být ve stopě. Drží slib, že kaskáda
    umí říct proč — u vět, kde tvrdé patro skutečně rozhodlo, nebo kde
    naučené mapování rolí přiznalo nejednoznačnost.
    """

    dialogue: str
    text: str
    tokens: tuple[Token, ...]
    predication: str | None
    notes: tuple[str, ...] = ()
    #: Co na téhle větě stojí — píše se do transkriptu, aby zlatá sada
    #: byla čitelná i pro člověka, který nezná § 6.12.
    point: str = ""
    #: Věty, které se dnes číst NEMAJÍ. Prázdný `predication` bez tohohle
    #: pole by byl nerozeznatelný od regrese.
    refuses: bool = field(default=False)
    #: Věta, u které je dnešní čtení VĚCNĚ ŠPATNĚ a ví se proč. Zlatá sada
    #: takový výsledek fixuje jako mez, ne jako správnou odpověď — kdyby
    #: se tvářil jako v pořádku, byla by to nepravda s razítkem testu.
    limit: str = ""
    #: Věta, u které systém právem doptává. Otázka je plnohodnotná odpověď
    #: (I‑7), takže patří do zlaté sady stejně jako hotové čtení.
    asks: str = ""

    def utterance(self) -> Utterance:
        return recorded(self.text, self.tokens, provenance=PROVENANCE)


# --------------------------------------------------------------------------
# Dialog A — řetěz s můstkem a veličinou
# --------------------------------------------------------------------------

A1 = Golden(
    dialogue="A",
    text="Auto je dopravní prostředek.",
    tokens=(
        tok(1, "Auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        tok(2, "je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "dopravní", "dopravní", "ADJ", 4, "amod", Animacy="Inan", Case="Nom", Degree="Pos", Gender="Masc", Number="Sing", Polarity="Pos"),
        tok(4, "prostředek", "prostředek", "NOUN", 0, "root", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="být(co:·dopravní_prostředek, kdo:∀auto)",
    asks=(
        "od N‑2b spadá i tahle věta do rodiny holé spony: „dopravní "
        "prostředek“ je JEDEN POJEM, ne dva členy, takže po složení "
        "lemmatu zbydou dvě strany a otázka je táž jako u „Kočka je "
        "savec“ — je to členství, nebo podmnožina? Dřív se věta zapsala "
        "jako reifikovaný vztah `být` se třemi rolemi, což SE NEPTALO, "
        "ale taky to nikdy nedalo `subset`, a doména na `subset` stojí. "
        "Otázka je tu tedy POKROK, ne regrese: fixuje se stav, kdy "
        "systém ví, že neví, místo aby tiše zapsal slabší tvrzení. "
        "Odpověď na ni je tah `→⊆` a zavře celou třídu vět naráz."
    ),
    point=(
        "spona: lemma přísudku nese `cop`, obsahem je jmenná část — "
        "jedno pravidlo, ne zvláštní větev na sponovou větu"
    ),
)

A2 = Golden(
    dialogue="A",
    text="Auta jezdí po dálnici.",
    tokens=(
        tok(1, "Auta", "auto", "NOUN", 2, "nsubj", Case="Nom", Gender="Neut", Number="Plur"),
        tok(2, "jezdí", "jezdit", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "po", "po", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "dálnici", "dálnice", "NOUN", 2, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="jezdit(kdo:∀auto, kudy:dálnice)",
    point="`po`+Loc → `kudy` je NAUČENÉ mapování role, jednoznačné, takže přejmenuje",
)

# --------------------------------------------------------------------------
# Dialog B — co neplyne (a motivační případ § 5.2)
# --------------------------------------------------------------------------

B1 = Golden(
    dialogue="B",
    text="Obsahuje citron vitamíny?",
    tokens=(
        tok(1, "Obsahuje", "obsahovat", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "citron", "citron", "NOUN", 1, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
        tok(3, "vitamíny", "vitamín", "NOUN", 1, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Plur"),
        tok(4, "?", "?", "PUNCT", 1, "punct"),
    ),
    predication="obsahovat(co:∃vitamín, kdo:∃citron)",
    notes=("shoda čísla",),
    point=(
        "tvrdý filtr rozhodne BEZ učení: „obsahuje“ je Sing, „vitamíny“ Plur. "
        "Parser oba nominály označí jako `obj` (nominativ je tvarově shodný "
        "s akuzativem), takže se generují obě čtení a rozhodne morfologie"
    ),
)

# --------------------------------------------------------------------------
# Dialog C — sylogismus a svědek
# --------------------------------------------------------------------------

C1 = Golden(
    dialogue="C",
    text="Karel napsal Postřižiny.",
    tokens=(
        tok(1, "Karel", "Karel", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "napsal", "napsat", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(3, "Postřižiny", "postřižina", "NOUN", 2, "obj", Case="Acc", Gender="Fem", Number="Plur"),
        tok(4, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="napsat(co:∃postřižina, kdo:·Karel)",
    point="svědek dialogu C vstupuje jako obyčejná věta se dvěma jádrovými rolemi",
    limit=(
        "„Postřižiny“ je NÁZEV DÍLA, parser z něj udělá obecné jméno "
        "s lemmatem „postřižina“ a systém pak mluví o ∃postřižina místo "
        "o konkrétní knize. Není to vada parseru ani kaskády: rozpoznat "
        "název díla je ZNALOST SVĚTA, ne morfologie, a v rozboru pro ni "
        "není z čeho vyjít. Zavře to buď jmenný rejstřík děl, nebo tah, "
        "kterým člověk řekne, že jde o jméno."
    ),
)

# --------------------------------------------------------------------------
# Dialog D — prostor a čas (věta, kvůli které vznikl blocker B‑9)
# --------------------------------------------------------------------------

D1 = Golden(
    dialogue="D",
    text="Petr jel v pondělí do Prahy.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "jel", "jet", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Acc"),
        tok(4, "pondělí", "pondělí", "NOUN", 2, "obl", Case="Acc", Gender="Neut", Number="Sing"),
        tok(5, "do", "do", "ADP", 6, "case", AdpType="Prep", Case="Gen"),
        tok(6, "Prahy", "Praha", "PROPN", 2, "obl", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(7, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="jet(kam:Praha, kdo:·Petr, kdy:pondělí)",
    point=(
        "dvě určení v jedné větě, obě zakotvená: `do`+Gen → `kam`, "
        "`v`+Acc → `kdy`. Sort určí ROLE, takže ani jedno nenese "
        "kvantifikátor — místo a čas se nekvantifikují"
    ),
)

D2 = Golden(
    dialogue="D",
    text="Petr jel v úterý do Brna.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "jel", "jet", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Acc"),
        tok(4, "úterý", "úterý", "NOUN", 2, "obl", Case="Acc", Gender="Neut", Number="Sing"),
        tok(5, "do", "do", "ADP", 6, "case", AdpType="Prep", Case="Gen"),
        tok(6, "Brna", "Brno", "PROPN", 2, "obl", Case="Gen", Gender="Neut", NameType="Geo", Number="Sing"),
        tok(7, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="jet(kam:Brno, kdo:·Petr, kdy:úterý)",
    point="druhý děj dialogu D — bez něj není co uspořádat přes `before*`",
)

D3 = Golden(
    dialogue="D",
    text="Petr byl v pondělí v Praze.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 6, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "byl", "být", "AUX", 6, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Acc"),
        tok(4, "pondělí", "pondělí", "NOUN", 6, "obl", Case="Acc", Gender="Neut", Number="Sing"),
        tok(5, "v", "v", "ADP", 6, "case", AdpType="Prep", Case="Loc"),
        tok(6, "Praze", "Praha", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(7, ".", ".", "PUNCT", 6, "punct"),
    ),
    predication="být(kdo:·Petr, kdy:pondělí, v+Loc:Praha)",
    point=(
        "VĚTA, KTERÁ SADU OPRAVILA. Vedla se tu jako zásadní mez — „dvě "
        "určení téhož tvaru, rozlišit je nejde“ — a byl to artefakt ručně "
        "psané nahrávky. Skutečný parser dá „v pondělí“ AKUZATIV a „v "
        "Praze“ LOKÁL, takže se ta určení tvarově LIŠÍ a žádná kolize "
        "není. Mez, kterou projekt zapsal jako vlastnost češtiny, byla "
        "vlastnost mého omylu. "
        "DRUHÁ VĚC, KTEROU TAHLE VĚTA OPRAVILA (N‑4): dávala `co:Praha`, "
        "tedy „Petr BYL Prahou“. UD dělá „Praze“ kořenem a „byl“ sponou, "
        "takže sponové pravidlo vzalo kořen jako jmennou část. PŘEDLOŽKA "
        "u kořene je ale tvrdý strukturní signál, že jmenná část to není: "
        "„být prostředek“ předložku nemá, „být v Praze“ ji má vždycky. "
        "Není to nové pravidlo o významu — role zůstane POVRCHOVÁ a co "
        "znamená, se učí."
    ),
    asks=(
        "ptá se, co znamená tvar `v`+Loc — a je to TÁŽ otázka jako "
        "u Petrovic, takže jedna odpověď zavře obojí. Doptání je tu "
        "správná odpověď: `v`+Loc je místo i čas a rozliší to jen člověk."
    ),
)


# --------------------------------------------------------------------------
# Dialog E — konflikt a výjimka
# --------------------------------------------------------------------------

E1 = Golden(
    dialogue="E",
    text="Vrabec létá.",
    tokens=(
        tok(1, "Vrabec", "Vrabec", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "létá", "létat", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="létat(kdo:·Vrabec)",
    point="jednomístná predikace — po odvolání p1 je to věta, která má vyjít A",
    limit=(
        "Parser čte „Vrabec“ jako VLASTNÍ JMÉNO (PROPN, NameType=Giv), "
        "takže věta mluví o panu Vrabcovi, ne o ptácích. Je to skutečná "
        "mez, ne omyl: „Vrabec“ je v češtině pták i příjmení a velké "
        "písmeno na začátku věty ta dvě čtení nerozlišuje. Rozhodnout to "
        "může jen kontext nebo člověk — z téhle jedné věty to nejde."
    ),
)

E2 = Golden(
    dialogue="E",
    text="Tučňák nelétá.",
    tokens=(
        tok(1, "Tučňák", "tučňák", "NOUN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "nelétá", "létat", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="¬létat(kdo:∀tučňák)",
    notes=("ZÁPOR",),
    point=(
        "tah, na kterém stojí celý dialog E: bez čtení záporu je to TÁŽ "
        "věta jako „Tučňák létá“, takže by nevznikl `CONFLICT` a nebylo "
        "by co zužovat"
    ),
)

# --------------------------------------------------------------------------
# Dialog F — instance, vršení popisu, jméno
# --------------------------------------------------------------------------

F1 = Golden(
    dialogue="F",
    text="Filip má auto.",
    tokens=(
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Gender="Neut", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="mít(co:∃auto, kdo:·Filip)",
    notes=("pádová mřížka",),
    point=(
        "obě jména jsou Sing, takže shoda čísla NEROZHODNE — rozhodne až "
        "pádová mřížka; dvě tvrdá patra nejsou jedno patro dvakrát"
    ),
)

F2 = Golden(
    dialogue="F",
    text="Filipovo auto je modré.",
    tokens=(
        tok(1, "Filipovo", "Filipův", "ADJ", 2, "amod", extra={"Gender[psor]": "Masc"}, Case="Nom", Gender="Neut", NameType="Giv", Number="Sing", Poss="Yes"),
        tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        tok(3, "je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Degree="Pos", Gender="Neut", Number="Sing", Polarity="Pos"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="být(co:·modrý, kdo:auto)",
    point=(
        "PŘIVLASTNĚNÍ DĚLÁ ZE JMÉNA URČITÝ POPIS (N‑6). „Filipovo“ visí "
        "pod „auto“, ne pod přísudkem, takže roli ve vztahu nedostane — "
        "ale nezmizí: je to ono, co říká, že řeč je o JEDNOM autě. Podmět "
        "proto čeká na ODKAZ, ne na kvantifikátor, a `∀auto`, které tu "
        "sada dřív fixovala jako mez, se přestalo vyrábět."
    ),
    asks=(
        "ptá se, KTERÝ uzel se míní — a to je otázka, na kterou existuje "
        "odpověď (tah `→=`). Do N‑6 se ptala, jakou ROLI hraje "
        "„Filipovo“, a tu otázku nezavřela žádná odpověď, protože „čí“ "
        "není role, ale vztah ke konkrétnímu uzlu. Otázka bez odběratele "
        "je podle vlastního pravidla projektu horší než ticho."
    ),
    limit=(
        "VLASTNÍK SE NEZAPISUJE. Že auto patří Filipovi, by mělo skončit "
        "v bázi jako vztah — jenže ROZBOR JMÉNO VLASTNÍKA NEDÁVÁ: token "
        "je „Filipovo“ s lemmatem „Filipův“ a cesta odtud k uzlu „Filip“ "
        "je derivační morfologie, kterou tagger neřeší. Useknout „‑ův“ by "
        "byl dohad o češtině zadrátovaný do interpretu. Přivlastnění tedy "
        "dnes ZUŽUJE REFERENCI, ale vlastníka nezapíše; zavře to buď "
        "jmenná vrstva, nebo tah, kterým člověk vlastníka pojmenuje."
    ),
)


# --------------------------------------------------------------------------
# Dialog G — jádrová relace ze stavby věty (N‑2)
# --------------------------------------------------------------------------

G1 = Golden(
    dialogue="G",
    text="Amoxicilin je druh penicilinu.",
    tokens=(
        tok(1, "Amoxicilin", "amoxicilin", "NOUN", 3, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "druh", "druh", "NOUN", 0, "root", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, "penicilinu", "penicilin", "NOUN", 3, "nmod", Animacy="Inan", Case="Gen", Gender="Masc", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="subset(sub:·amoxicilin, sup:·penicilin)",
    notes=("cop:druh+Gen",),
    point=(
        "věta, kvůli které N‑2 vzniklo: dřív z ní bylo "
        "být(Gen:penicilin, co:druh, kdo:amoxicilin) a nikdy subset, "
        "takže kaskáda subset* neměla čeho se chytit"
    ),
)

G2 = Golden(
    dialogue="G",
    text="Vrabec není savec.",
    tokens=(
        tok(1, "Vrabec", "vrabec", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "není", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="disjoint(a:·vrabec, b:·savec)",
    notes=("cop:NOUN≠NOUN",),
    point=(
        "záporná spona mezi dvěma OBECNÝMI jmény je oddělenost tříd — "
        "a zapisuje se `add_disjoint`em, protože s markerem musí vzniknout "
        "i dvojice pravidel se silnou negací"
    ),
)

G3 = Golden(
    dialogue="G",
    text="Kočka je savec.",
    tokens=(
        tok(1, "Kočka", "kočka", "NOUN", 3, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="být(co:·savec, kdo:∀kočka)",
    asks=(
        "holá kladná spona je DVOJZNAČNÁ: „Kočka je savec“ je subset, "
        "„Mourek je kočka“ member, a tvar je týž. Systém se proto ptá "
        "a DO ODPOVĚDI NEZAPISUJE NIC: zapsat to teď jako obyčejný vztah "
        "`být` a po odpovědi znovu jako `subset` by uložilo dva výroky "
        "a ten první by nikdo neodvolal — táž vada jako u ztraceného "
        "členu (N‑5), jen o jinou chybějící věc. Fixuje se tu OTÁZKA, "
        "ne uhodnutá relace."
    ),
    point="dvojznačnost, kterou N‑2 schválně NEROZHODUJE za člověka",
)


G4 = Golden(
    dialogue="G",
    text="Mourek je kočka.",
    tokens=(
        tok(1, "Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "kočka", "kočka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Mourek, group:·kočka)",
    notes=("cop:PROPN=NOUN",),
    point=(
        "TÝŽ TVAR jako „Kočka je savec“, jiný slovní druh podmětu — a tím "
        "jiná relace. `PROPN` je signál individua, takže je to členství; "
        "tvrdit o vlastním jméně podmnožinu by z Mourka udělalo třídu"
    ),
)

G5 = Golden(
    dialogue="G",
    text="Mourek není savec.",
    tokens=(
        tok(1, "Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "není", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="¬member(elem:·Mourek, group:·savec)",
    notes=("cop:PROPN≠NOUN",),
    point=(
        "ASYMETRIE ZÁPORU: `disjoint` zápor SAMA nese, takže ho pohltí, "
        "kdežto na `member` je kolmý a musí se přenést. Táž věta s obecným "
        "jménem („Vrabec není savec“) dá oddělenost tříd, tahle dá DOLOŽENÉ "
        "POPŘENÍ členství — a Mourek zůstane individuem"
    ),
)


#: **Zlatá sada čte předmět jako `∃`, dialog Vegetarián jako `∀` — a je to
#: TÝŽ TVAR.** Není to nesrovnalost, je to NÁLEZ: `NOUN/Sing/Acc/obj`
#: nese v „Petr jedl steak" existenci a v „Vegetarián nejí maso" obecnost,
#: a rozliší to jen VĚTA, ne tvar. Sada tu fixuje, co dá JEJÍ potvrzený
#: tvar; závěr domény (rozpor) na tom stojí a je zapsaný v dialogu, kde je
#: potvrzený tvar jiný. Správné řešení není třetí tvar, ale doptání na
#: větu — to systém dělá sám, když potvrzený tvar není.

# --------------------------------------------------------------------------
# Dialog H — logický rozpor (odstavec 6 z deseti)
# --------------------------------------------------------------------------
#
# Do zlaté sady jdou proto, že `live_check` kontroluje JEN tuhle sadu:
# nahrávky v `dialogues.py` by se s parserem mohly rozejít a nikdo by se
# to nedozvěděl. Šestý dialog stojí na generickém popření a na distribuci
# rolí, tedy na tvarech, které se dřív neměřily živě vůbec.

H1 = Golden(
    dialogue="H",
    text="Petr je vegetarián.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "vegetarián", "vegetarián", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Petr, group:·vegetarián)",
)

H2 = Golden(
    dialogue="H",
    text="Vegetarián nejí maso.",
    tokens=(
        tok(1, "Vegetarián", "vegetarián", "NOUN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "nejí", "jíst", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "maso", "maso", "NOUN", 2, "obj", Case="Acc", Gender="Neut", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="¬jíst(co:∃maso, kdo:∀vegetarián)",
)

H3 = Golden(
    dialogue="H",
    text="Steak je druh masa.",
    tokens=(
        tok(1, "Steak", "steak", "NOUN", 3, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "druh", "druh", "NOUN", 0, "root", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, "masa", "maso", "NOUN", 3, "nmod", Case="Gen", Gender="Neut", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="subset(sub:·steak, sup:·maso)",
)

H4 = Golden(
    dialogue="H",
    text="Petr jedl steak.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "jedl", "jíst", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(3, "steak", "steak", "NOUN", 2, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="jíst(co:∃steak, kdo:·Petr)",
)

H5 = Golden(
    dialogue="H",
    text="Jedl Petr maso?",
    tokens=(
        tok(1, "Jedl", "jíst", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(2, "Petr", "Petr", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "maso", "maso", "NOUN", 1, "obj", Case="Acc", Gender="Neut", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 1, "punct"),
    ),
    predication="jíst(co:∃maso, kdo:·Petr)",
)

H6 = Golden(
    dialogue="H",
    text="Jedl Petr steak?",
    tokens=(
        tok(1, "Jedl", "jíst", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(2, "Petr", "Petr", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "steak", "steak", "NOUN", 1, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 1, "punct"),
    ),
    predication="jíst(co:∃steak, kdo:·Petr)",
)


# --------------------------------------------------------------------------
# Dialog I — `before` z české věty (N‑9)
# --------------------------------------------------------------------------
#
# Vazba `před`+Ins se dosud živě neměřila vůbec a je to jediná cesta, kterou
# čeština k uspořádání na časové ose dnes vede.

I1 = Golden(
    dialogue="I",
    text="Pondělí je před úterým.",
    tokens=(
        tok(1, "Pondělí", "pondělí", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        tok(2, "je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
        tok(4, "úterým", "úterý", "NOUN", 0, "root", Case="Ins", Gender="Neut", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="before(earlier:pondělí, later:úterý)",
)

I2 = Golden(
    dialogue="I",
    text="Úterý je před středou.",
    tokens=(
        tok(1, "Úterý", "úterý", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        tok(2, "je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
        tok(4, "středou", "středa", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="before(earlier:úterý, later:středa)",
)

I3 = Golden(
    dialogue="I",
    text="Je pondělí před středou?",
    tokens=(
        tok(1, "Je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "pondělí", "pondělí", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        tok(3, "před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
        tok(4, "středou", "středa", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
        tok(5, "?", "?", "PUNCT", 4, "punct"),
    ),
    predication="before(earlier:pondělí, later:středa)",
)

I4 = Golden(
    dialogue="I",
    text="Je středa před pondělím?",
    tokens=(
        tok(1, "Je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "středa", "středa", "NOUN", 4, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
        tok(3, "před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
        tok(4, "pondělím", "pondělí", "NOUN", 0, "root", Case="Ins", Gender="Neut", Number="Sing"),
        tok(5, "?", "?", "PUNCT", 4, "punct"),
    ),
    predication="before(earlier:středa, later:pondělí)",
)


# --------------------------------------------------------------------------
# Dialog J — `disjoint` a `ne` z vyloučení tříd
# --------------------------------------------------------------------------
#
# „Vrabec není savec." tu SCHVÁLNĚ NENÍ podruhé — v sadě je jako G2 a
# druhý záznam téže věty by jen zdvojil, co se měří. Přibývá k ní
# individuum a dvě otázky: jedna, na kterou se odpovídá přes expanzi
# oddělenosti, a jedna, kde otevřený svět drží `U`.

J2 = Golden(
    dialogue="J",
    text="Čimčara je vrabec.",
    tokens=(
        tok(1, "Čimčara", "Čimčara", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "vrabec", "vrabec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Čimčara, group:·vrabec)",
)

J3 = Golden(
    dialogue="J",
    text="Je Čimčara savec?",
    tokens=(
        tok(1, "Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "Čimčara", "Čimčara", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Čimčara, group:·savec)",
)

J4 = Golden(
    dialogue="J",
    text="Je Čimčara pták?",
    tokens=(
        tok(1, "Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "Čimčara", "Čimčara", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "pták", "pták", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Čimčara, group:·pták)",
)


#: Celá sada v pořadí dialogů. Pořadí je součást zlatého transkriptu.
CORPUS: tuple[Golden, ...] = (
    A1, A2, B1, C1, D1, D2, D3, E1, E2, F1, F2, G1, G2, G3, G4, G5,
    H1, H2, H3, H4, H5, H6,
    I1, I2, I3, I4,
    J2, J3, J4,
)


def recordings() -> dict[str, Utterance]:
    return {item.text: item.utterance() for item in CORPUS}


# --------------------------------------------------------------------------
# Kvantifikátory holých jmen — ROZHODNUTÍ ČLOVĚKA, zapsané, ne skryté
# --------------------------------------------------------------------------

#: Ani jedna věta v sadě nemá determinátor, protože čeština nemá členy.
#: Bez těchhle vzorů by se systém u KAŽDÉ z nich zeptal, co je naprosto
#: správně — a zlatá sada by fixovala jen otázky.
#:
#: Že jsou tady, je proto **rozhodnutí, ne konfigurace**. Každý řádek říká
#: „takhle tvarované jméno čteme takhle", má provenienci a jde odvolat.
#: Do `czech_seed()` nepatří: tam by z něj byl tichý default pro každého,
#: kdo knihovnu použije, a přesně to L‑3 zakazuje.
_SHAPES: tuple[tuple[str, str, str, str, Operation], ...] = (
    # podmět v nominativu — „auta jezdí", „vrabec létá": obecná tvrzení
    ("NOUN", "Sing", "Nom", "nsubj", Operation.FOR_ALL),
    ("NOUN", "Plur", "Nom", "nsubj", Operation.FOR_ALL),
    # předmět v akuzativu — „Filip má auto": o nějakém, ne o každém
    ("NOUN", "Sing", "Acc", "obj", Operation.EXISTS),
    ("NOUN", "Plur", "Acc", "obj", Operation.EXISTS),
    # jmenná část přísudku — „auto je prostředek": o skupině samotné
    ("NOUN", "Sing", "Nom", "root", Operation.SELF),
    # vlastní jméno je konkrétní uzel, ať stojí kdekoli
    ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),
    ("PROPN", "Sing", "Gen", "obl", Operation.SELF),
    ("PROPN", "Plur", "Acc", "obj", Operation.SELF),
    ("PROPN", "Sing", "Loc", "obl", Operation.SELF),
    ("PROPN", "Sing", "Ins", "obl", Operation.SELF),
    # okolnosti obecným jménem — „v pondělí", „autem", „po dálnici"
    ("NOUN", "Sing", "Loc", "obl", Operation.EXISTS),
    ("NOUN", "Sing", "Ins", "obl", Operation.EXISTS),
    # přívlastek a jmenná část přísudku jsou SKUPINY (§ 6.12, dialog F:
    # `member(a1, group("modrý"))`), a mluví se o té skupině samotné
    ("ADJ", "", "Nom", "amod", Operation.SELF),
    ("ADJ", "Sing", "Nom", "root", Operation.SELF),
)


def golden_lexicon() -> Lexicon:
    """Lexikon zlaté sady: český seed plus **potvrzené** tvary."""
    lexicon = czech_seed()
    for upos, number, case, deprel, operation in _SHAPES:
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number=number, case=case, deprel=deprel
                ),
                operation=operation,
                learned_from="zlatá sada, potvrzeno člověkem",
                status=PatternStatus.CONFIRMED,
            )
        )
    return lexicon
