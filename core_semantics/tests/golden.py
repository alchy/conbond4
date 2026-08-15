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


# --------------------------------------------------------------------------
# Dialog K — identita a její spor
# --------------------------------------------------------------------------
#
# Spona mezi dvěma VLASTNÍMI JMÉNY se živě neměřila vůbec. „Je Micka
# kočka?" je v sadě jen jednou, i když se v doméně ptá dvakrát — podruhé
# se liší BÁZE, ne rozbor, a zlatá sada měří rozbor. „Mourek je kočka."
# tu není podruhé, je to G4.
#
# Rozbor „Je Micka kočka?" jsem nejdřív OPSAL ze sousední věty a parita
# to odmítla: v „Micka je Mourek." čte parser „Micku" jako MASKULINUM
# (táhne to následující mužské jméno), kdežto samostatně jako femininum.
# Přesně kvůli tomuhle se nahrávky měří proti živé službě.

K2 = Golden(
    dialogue="K",
    text="Micka je Mourek.",
    tokens=(
        tok(1, "Micka", "Micka", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "Mourek", "Mourek", "PROPN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="same_as(left:·Micka, right:·Mourek)",
)

K3 = Golden(
    dialogue="K",
    text="Je Micka kočka?",
    tokens=(
        tok(1, "Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "Micka", "Micka", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Giv", Number="Sing"),
        tok(3, "kočka", "kočka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Micka, group:·kočka)",
)

K4 = Golden(
    dialogue="K",
    text="Micka není Mourek.",
    tokens=(
        tok(1, "Micka", "Micka", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "není", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "Mourek", "Mourek", "PROPN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="¬same_as(left:·Micka, right:·Mourek)",
)

K5 = Golden(
    dialogue="K",
    text="Micka je Mourek?",
    tokens=(
        tok(1, "Micka", "Micka", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "Mourek", "Mourek", "PROPN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    predication="same_as(left:·Micka, right:·Mourek)",
)


# --------------------------------------------------------------------------
# L · zahrnutí v místě i v čase (desátý akceptační dialog)
# --------------------------------------------------------------------------
#
# Tvar „být součástí“ je v obou prvních větách TÝŽ a znamená pokaždé něco
# jiného (`contains` × `within`), takže se tu ZÁMĚRNĚ zapisuje čtení, které
# ještě relaci nezná: `být(Gen:…)`. Není to omyl v sadě — je to stav PŘED
# odpovědí člověka a přesně to, co se nesmí zapsat do báze (B‑17).

L1 = Golden(
    dialogue="L",
    text="Petrovice jsou součástí Plzně.",
    tokens=(
        tok(1, "Petrovice", "Petrovice", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Geo", Number="Plur"),
        tok(2, "jsou", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
        tok(4, "Plzně", "Plzeň", "PROPN", 3, "nmod", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="být(Gen:Plzeň, co:součást, kdo:Petrovice)",
    asks=(
        "ptá se na relaci: „být součástí“ je TVAR, ne význam, a bez "
        "odpovědi člověka se tahle věta nesmí zapsat (B‑17)"
    ),
)

L2 = Golden(
    dialogue="L",
    text="Pondělí je součástí týdne.",
    tokens=(
        tok(1, "Pondělí", "pondělí", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
        tok(4, "týdne", "týden", "NOUN", 3, "nmod", Animacy="Inan", Case="Gen", Gender="Masc", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="být(Gen:týden, co:součást, kdo:∀pondělí)",
    asks=(
        "ptá se ZNOVU a na týž tvar — protože odpověď u L1 platila jen "
        "pro tu jednu větu (`→⊆1`), a tady je správně jiná relace"
    ),
)

L3 = Golden(
    dialogue="L",
    text="Koncert byl v Petrovicích v pondělí.",
    tokens=(
        tok(1, "Koncert", "koncert", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Petrovicích", "Petrovice", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
        tok(5, "v", "v", "ADP", 6, "case", AdpType="Prep", Case="Acc"),
        tok(6, "pondělí", "pondělí", "NOUN", 4, "obl", Case="Acc", Gender="Neut", Number="Sing"),
        tok(7, ".", ".", "PUNCT", 4, "punct"),
    ),
    #: DVĚ OKOLNOSTI, ROZLIŠENÉ PÁDEM, ne předložkou: „v+Loc" je místo,
    #: „v+Acc" čas. Že je tu jedna pojmenovaná (`kdy`) a druhá ne, drží
    #: rozdíl mezi tvarem a významem viditelný i ve zlatém záznamu.
    predication="být(kdo:∀koncert, kdy:pondělí, v+Loc:Petrovice)",
    asks="ptá se, co znamená role „v+Loc“ — tvar zná, význam ne",
)

L4 = Golden(
    dialogue="L",
    text="Byl koncert v Plzni během týdne?",
    tokens=(
        tok(1, "Byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(2, "koncert", "koncert", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Plzni", "Plzeň", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(5, "během", "během", "ADP", 6, "case", AdpType="Prep", Case="Gen"),
        tok(6, "týdne", "týden", "NOUN", 4, "obl", Animacy="Inan", Case="Gen", Gender="Masc", Number="Sing"),
        tok(7, "?", "?", "PUNCT", 4, "punct"),
    ),
    predication="být(během+Gen:týden, kdo:∀koncert, v+Loc:Plzeň)",
    asks="ptá se na obě okolnostní role — „v+Loc“ i „během+Gen“",
)


# --------------------------------------------------------------------------
# M · uzavření světa (jedenáctý akceptační dialog)
# --------------------------------------------------------------------------
#
# Věta M5 je jediná v celé sadě, po které se z NEPŘÍTOMNOSTI stane „ne" —
# a proto se z ní taky jako z jediné nesmí nic zapsat samo. Zlatá sada tu
# fixuje ČTENÍ a otázku; co z toho čtení bude v jádře, rozhoduje člověk
# tahem `!∀`, a to už sada dialogů, ne tahle.

M1 = Golden(
    dialogue="M",
    text="Rex je pes.",
    tokens=(
        tok(1, "Rex", "Rex", "PROPN", 3, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", NameType="Oth", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "pes", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Rex, group:·pes)",
    point="`PROPN` v podmětu činí relaci rozhodnutelnou — členství, ne podmnožina (N‑2d)",
)

M2 = Golden(
    dialogue="M",
    text="Alík je pes.",
    tokens=(
        tok(1, "Alík", "alík", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "pes", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    #: Parser lemmatizuje „Alík" malým písmenem. Sada to FIXUJE tak, jak
    #: to skutečný parser dělá — opravovat to tady by znamenalo měřit
    #: vlastní představu místo nasazeného modelu.
    predication="member(elem:·alík, group:·pes)",
)

M3 = Golden(
    dialogue="M",
    text="Mourek je kocour.",
    tokens=(
        tok(1, "Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "kocour", "kocour", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Mourek, group:·kocour)",
)

M4 = Golden(
    dialogue="M",
    text="Je Mourek pes?",
    tokens=(
        tok(1, "Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "pes", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Mourek, group:·pes)",
)

M5 = Golden(
    dialogue="M",
    text="To jsou všichni psi.",
    tokens=(
        tok(1, "To", "ten", "DET", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing", PronType="Dem"),
        tok(2, "jsou", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "všichni", "všechen", "DET", 4, "det", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur", PronType="Tot"),
        tok(4, "psi", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="být(co:∀pes, kdo:ten)",
    asks=(
        "navrhuje UZAVŘENÍ SVĚTA a čeká — jediná otázka v systému, která "
        "upozorňuje na DŮSLEDEK, ne na neznalost"
    ),
    point=(
        "shoda čísla tu NEPLATÍ: podmět „to“ je Sing, spona Plur, a věta "
        "je přesto správně česky. Prezentační „to“ nezastupuje počitatelný "
        "podmět, takže má tvrdý filtr úzkou výjimku — kdyby ji neměl, "
        "zahodil by gramatickou větu"
    ),
)


# --------------------------------------------------------------------------
# N · pojmenování (dvanáctý akceptační dialog)
# --------------------------------------------------------------------------
#
# N2 je jediná věta v sadě, u které generátor vyrobí DVĚ čtení a rozhodne
# je DEPREL, ne pořadí: obě jména jsou v nominativu, takže „kdo" a „co" si
# je mezi sebou prohodí. Kdyby se strany braly podle pořadí kandidátů,
# zapsalo by se jednou `name(Jan, Honza)` a podruhé pravý opak.

N1 = Golden(
    dialogue="N",
    text="Jan je učitel.",
    tokens=(
        tok(1, "Jan", "Jan", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="member(elem:·Jan, group:·učitel)",
)

N2 = Golden(
    dialogue="N",
    text="Jan se jmenuje taky Honza.",
    tokens=(
        tok(1, "Jan", "Jan", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(2, "se", "se", "PRON", 3, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
        tok(3, "jmenuje", "jmenovat", "VERB", 0, "root", Aspect="Imp,Perf", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(4, "taky", "taky", "PART", 5, "advmod:emph"),
        tok(5, "Honza", "Honza", "PROPN", 3, "obj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(6, ".", ".", "PUNCT", 3, "punct"),
    ),
    predication="name(of:Jan, value:Honza)",
    point=(
        "zvratné „jmenovat se“ je lexikálně o pojmenování a druhé čtení "
        "nemá, takže se konstrukce DOSAZUJE — táž úvaha jako `PROPN` "
        "v podmětu holé spony (N‑2d). Ptát se „co ta věta tvrdí?“ by byla "
        "otázka bez odběratele: v nabídce vztahů dvou tříd správná "
        "odpověď není"
    ),
)

N3 = Golden(
    dialogue="N",
    text="Je Honza učitel?",
    tokens=(
        tok(1, "Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "Honza", "Honza", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        tok(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    #: V PRÁZDNÉ bázi je „Honza" prostě uzel „Honza". Že se v doméně
    #: ztotožní s Janem, není vlastnost rozboru — je to důsledek toho, co
    #: v bázi leží, a měří to sada dialogů.
    predication="member(elem:·Honza, group:·učitel)",
)


# --------------------------------------------------------------------------
# O · kontext textu (třináctý akceptační dialog)
# --------------------------------------------------------------------------
#
# V PRÁZDNÉ bázi nemá zájmeno kam ukázat — sada proto fixuje, že se systém
# ptá a nic si nedomýšlí. Že v doméně kandidát z předchozí věty JE, měří
# sada dialogů; tady se drží ta druhá půlka, bez které by první nedávala
# smysl: bez kontextu se NEHÁDÁ.

O1 = Golden(
    dialogue="O",
    text="On bydlí v Petrovicích.",
    tokens=(
        tok(1, "On", "on", "PRON", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing", Person="3", PronType="Prs"),
        tok(2, "bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Petrovicích", "Petrovice", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
        tok(5, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="bydlet(kdo:on, v+Loc:Petrovice)",
    asks=(
        "zájmeno čeká na ODKAZ. Bez předchozí věty není koho nabídnout — "
        "a nabídnout uzel odjinud by znamenalo tvrdit, že text odkazuje "
        "tam, kde nic nestojí"
    ),
)

O2 = Golden(
    dialogue="O",
    text="Ona bydlí v Praze.",
    tokens=(
        tok(1, "Ona", "on", "PRON", 2, "nsubj", Case="Nom", Gender="Fem", Number="Sing", Person="3", PronType="Prs"),
        tok(2, "bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 2, "punct"),
    ),
    predication="bydlet(kdo:on, v+Loc:·Praha)",
    asks="týž tvar, ženský rod — shoda je vodítko, kterým se kandidáti ZUŽUJÍ",
)

O3 = Golden(
    dialogue="O",
    text="Bydlí Jan v Plzni?",
    tokens=(
        tok(1, "Bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(2, "Jan", "Jan", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Plzni", "Plzeň", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(5, "?", "?", "PUNCT", 1, "punct"),
    ),
    predication="bydlet(kdo:·Jan, v+Loc:·Plzeň)",
    asks="„v+Loc“ je v prázdném lexikonu pořád jen tvar, ne význam",
)


# --------------------------------------------------------------------------
# P · věta bez podmětu (čtrnáctý akceptační dialog)
# --------------------------------------------------------------------------
#
# Podmět se v predikaci OBJEVÍ, přestože ho věta nevyslovila — a jeho
# zmínkou je sám PŘÍSUDEK, protože rod a číslo jsou na něm. Proto se ve
# čtení píše `kdo:narodit`: do textu se nepřidávají slova, která tam
# nejsou. Že se ta role musí NAJÍT, je celý rozdíl proti stavu, kdy se
# věta zapsala bez podmětu jako fakt o nikom.

P1 = Golden(
    dialogue="P",
    text="Narodil se v Petrovicích.",
    tokens=(
        tok(1, "Narodil", "narodit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(2, "se", "se", "PRON", 1, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Petrovicích", "Petrovice", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
        tok(5, ".", ".", "PUNCT", 1, "punct"),
    ),
    predication="narodit(kdo:narodit, v+Loc:Petrovice)",
    asks=(
        "podmět věta NEVYSLOVILA a v prázdné bázi není koho nabídnout — "
        "systém to řekne a nic si nedomýšlí"
    ),
)

P2 = Golden(
    dialogue="P",
    text="Narodila se v Praze.",
    tokens=(
        tok(1, "Narodila", "narodit", "VERB", 0, "root", Aspect="Perf", Gender="Fem,Neut", Number="Plur,Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(2, "se", "se", "PRON", 1, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
        tok(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        tok(4, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 1, "punct"),
    ),
    predication="narodit(kdo:narodit, v+Loc:·Praha)",
    asks="týž tvar v ženském rodě — rys nese VÍC hodnot („Fem,Neut“)",
    point=(
        "parser dává u tohohle tvaru `Gender=Fem,Neut` a "
        "`Number=Plur,Sing`, protože tvar je pro všechny ty možnosti týž. "
        "Sada to FIXUJE tak, jak to skutečný parser dělá — a shoda se "
        "proto porovnává průnikem, ne rovností"
    ),
)

P3 = Golden(
    dialogue="P",
    text="Narodil se Jan v Plzni?",
    tokens=(
        tok(1, "Narodil", "narodit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        tok(2, "se", "se", "PRON", 1, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
        tok(3, "Jan", "Jan", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
        tok(4, "v", "v", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
        tok(5, "Plzni", "Plzeň", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        tok(6, "?", "?", "PUNCT", 1, "punct"),
    ),
    #: TÁŽ SLOVESNÁ STAVBA, ale podmět VYSLOVENÝ — patro pro‑drop se sem
    #: nesmí plést. Kdyby přidalo roli i tady, vznikl by druhý podmět.
    predication="narodit(kdo:·Jan, v+Loc:·Plzeň)",
    asks="„v+Loc“ je v prázdném lexikonu pořád jen tvar, ne význam",
)


# --------------------------------------------------------------------------
# R · genitivní přívlastek (patnáctý akceptační dialog)
# --------------------------------------------------------------------------
#
# Obě věty se ZAPÍŠOU a přesto se systém ptá — a to je na nich to
# podstatné. Genitiv visí pod JMÉNEM, ne pod přísudkem, takže větě
# nechybí predikát; chybí jí přívlastek, a ten je druhý výrok vedle věty.

R1 = Golden(
    dialogue="R",
    text="Chov zvířat je náročný.",
    tokens=(
        tok(1, "Chov", "chov", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        tok(2, "zvířat", "zvíře", "NOUN", 1, "nmod", Case="Gen", Gender="Neut", Number="Plur"),
        tok(3, "je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(4, "náročný", "náročný", "ADJ", 0, "root", Animacy="Inan", Case="Nom", Degree="Pos", Gender="Masc", Number="Sing", Polarity="Pos"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="být(co:·náročný, kdo:∀chov)",
    asks=(
        "ptá se na význam genitivního přívlastku — a VĚTA SE PŘESTO "
        "ZAPÍŠE, protože přívlastek není role přísudku"
    ),
)

R2 = Golden(
    dialogue="R",
    text="Péče majitele je nutná.",
    tokens=(
        tok(1, "Péče", "péče", "NOUN", 4, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
        tok(2, "majitele", "majitel", "NOUN", 1, "nmod", Animacy="Anim", Case="Gen", Gender="Masc", Number="Sing"),
        tok(3, "je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
        tok(4, "nutná", "nutný", "ADJ", 0, "root", Case="Nom", Degree="Pos", Gender="Fem", Number="Sing", Polarity="Pos"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    predication="být(co:·nutný, kdo:∀péče)",
    asks="TÝŽ TVAR jako R1, a ptá se ZNOVU — význam genitivu se neučí",
    point=(
        "„chov zvířat“ a „péče majitele“ mají identický rozbor a OPAČNÝ "
        "SMĚR: zvířata se chovají, kdežto majitel pečuje. Naučit ten tvar "
        "by znamenalo přečíst druhou větu naruby"
    ),
)


#: Celá sada v pořadí dialogů. Pořadí je součást zlatého transkriptu.
CORPUS: tuple[Golden, ...] = (
    A1, A2, B1, C1, D1, D2, D3, E1, E2, F1, F2, G1, G2, G3, G4, G5,
    H1, H2, H3, H4, H5, H6,
    I1, I2, I3, I4,
    J2, J3, J4,
    K2, K3, K4, K5,
    L1, L2, L3, L4,
    M1, M2, M3, M4, M5,
    N1, N2, N3,
    O1, O2, O3,
    P1, P2, P3,
    R1, R2,
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
