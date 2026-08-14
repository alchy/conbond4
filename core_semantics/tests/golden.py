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
PROVENANCE = "udpipe2 model=czech-pdt-ud-2.12 tokenizer=czech-pdt-2.12"


def tok(
    index: int,
    form: str,
    lemma: str,
    upos: str,
    head: int,
    deprel: str,
    **feats: str,
) -> Token:
    return Token(
        index=index,
        form=form,
        lemma=lemma,
        upos=upos,
        head=head,
        deprel=deprel,
        feats=tuple(sorted(feats.items())),
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
        tok(1, "Auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "je", "být", "AUX", 4, "cop", Number="Sing"),
        tok(3, "dopravní", "dopravní", "ADJ", 4, "amod", Case="Nom"),
        tok(4, "prostředek", "prostředek", "NOUN", 0, "root", Case="Nom", Number="Sing"),
    ),
    predication="být(co:·prostředek, jak:·dopravní, kdo:∀auto)",
    point=(
        "spona: lemma přísudku nese `cop`, obsahem je jmenná část — "
        "jedno pravidlo, ne zvláštní větev na sponovou větu"
    ),
)

A2 = Golden(
    dialogue="A",
    text="Auta jezdí po dálnici.",
    tokens=(
        tok(1, "Auta", "auto", "NOUN", 2, "nsubj", Case="Nom", Number="Plur"),
        tok(2, "jezdí", "jezdit", "VERB", 0, "root", Number="Plur"),
        tok(3, "po", "po", "ADP", 4, "case"),
        tok(4, "dálnici", "dálnice", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
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
        # Parser NEDÁ podmět: „citron" je tvarově Nom i Acc. Tohle je ta
        # reálná zeď ze zadání, ne vymyšlený případ.
        tok(1, "Obsahuje", "obsahovat", "VERB", 0, "root", Number="Sing"),
        tok(2, "citron", "citron", "NOUN", 1, "obj", Number="Sing"),
        tok(3, "vitamíny", "vitamín", "NOUN", 1, "obj", Case="Acc", Number="Plur"),
    ),
    predication="obsahovat(co:∃vitamín, kdo:citron)",
    notes=("shoda čísla",),
    point="tvrdý filtr rozhodne BEZ učení: „obsahuje“ je Sing, „vitamíny“ Plur",
    asks=(
        "u „citron“ se ptá na kvantifikátor, A JE TO SPRÁVNĚ: parser tomu "
        "slovu nedal pád, takže tvar je jen NOUN/Sing/obj a žádný potvrzený "
        "vzor na něj nesedí. Systém si pád nedosadí, aby vzor sedl — to by "
        "byl dohad postavený na dohadu"
    ),
)

# --------------------------------------------------------------------------
# Dialog C — sylogismus a svědek
# --------------------------------------------------------------------------

C1 = Golden(
    dialogue="C",
    text="Karel napsal Postřižiny.",
    tokens=(
        tok(1, "Karel", "Karel", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "napsal", "napsat", "VERB", 0, "root", Number="Sing"),
        tok(3, "Postřižiny", "Postřižiny", "PROPN", 2, "obj", Case="Acc", Number="Plur"),
    ),
    predication="napsat(co:·Postřižiny, kdo:·Karel)",
    point="svědek dialogu C vstupuje jako obyčejná věta se dvěma jádrovými rolemi",
)

# --------------------------------------------------------------------------
# Dialog D — prostor a čas (věta, kvůli které vznikl blocker B‑9)
# --------------------------------------------------------------------------

D1 = Golden(
    dialogue="D",
    text="Petr jel v pondělí do Prahy.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "jel", "jet", "VERB", 0, "root", Number="Sing"),
        tok(3, "v", "v", "ADP", 4, "case"),
        tok(4, "pondělí", "pondělí", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
        tok(5, "do", "do", "ADP", 6, "case"),
        tok(6, "Prahy", "Praha", "PROPN", 2, "obl", Case="Gen", Number="Sing"),
    ),
    predication="jet(kam:Praha, kdo:·Petr, v+Loc:∃pondělí)",
    notes=("v+Loc může být kde nebo kdy",),
    point=(
        "dvě určení v jedné větě: `do`+Gen je jednoznačně `kam`, ale "
        "`v`+Loc je `kde` i `kdy` — a to se PŘIZNÁ, nehádá"
    ),
)

D2 = Golden(
    dialogue="D",
    text="Petr jel v úterý do Brna.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "jel", "jet", "VERB", 0, "root", Number="Sing"),
        tok(3, "v", "v", "ADP", 4, "case"),
        tok(4, "úterý", "úterý", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
        tok(5, "do", "do", "ADP", 6, "case"),
        tok(6, "Brna", "Brno", "PROPN", 2, "obl", Case="Gen", Number="Sing"),
    ),
    predication="jet(kam:Brno, kdo:·Petr, v+Loc:∃úterý)",
    notes=("v+Loc může být kde nebo kdy",),
    point="druhý děj dialogu D — bez něj není co uspořádat přes `before*`",
)

D3 = Golden(
    dialogue="D",
    text="Petr byl v pondělí v Praze.",
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "byl", "být", "VERB", 0, "root", Number="Sing"),
        tok(3, "v", "v", "ADP", 4, "case"),
        tok(4, "pondělí", "pondělí", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
        tok(5, "v", "v", "ADP", 6, "case"),
        tok(6, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Number="Sing"),
    ),
    predication=None,
    refuses=True,
    notes=("v+Loc",),
    point=(
        "DVĚ URČENÍ TÉHOŽ TVARU. Rozlišit „kdy“ od „kde“ by šlo jen podle "
        "významu nominálu — a ten se nehádá (INV‑11). Poctivá odpověď je "
        "otázka, ne tip a ne pád."
    ),
)

# --------------------------------------------------------------------------
# Dialog E — konflikt a výjimka
# --------------------------------------------------------------------------

E1 = Golden(
    dialogue="E",
    text="Vrabec létá.",
    tokens=(
        tok(1, "Vrabec", "vrabec", "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "létá", "létat", "VERB", 0, "root", Number="Sing"),
    ),
    predication="létat(kdo:∀vrabec)",
    point="jednomístná predikace — po odvolání p1 je to věta, která má vyjít A",
)

E2 = Golden(
    dialogue="E",
    text="Tučňák nelétá.",
    tokens=(
        tok(1, "Tučňák", "tučňák", "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "nelétá", "létat", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
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
        tok(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
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
        tok(1, "Filipovo", "Filipův", "ADJ", 2, "amod", Case="Nom"),
        tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
        tok(3, "je", "být", "AUX", 4, "cop", Number="Sing"),
        tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
    ),
    predication="být(co:·modrý, kdo:∀auto)",
    point=(
        "vršení popisu: `Filipovo` visí pod `auto`, ne pod přísudkem, "
        "takže se do rolí predikace nedostane — přivlastnění je práce V3"
    ),
    limit=(
        "∀auto JE ŠPATNĚ. Věta mluví o Filipově autě, tedy o jednom "
        "konkrétním, ne o všech. Potvrzený vzor `NOUN/Sing/Nom/nsubj → ∀` "
        "na to nemůže přijít, protože vidí jen tvar podstatného jména "
        "a přivlastnění je na SOUSEDNÍM tokenu. Sada to fixuje jako mez, "
        "ne jako správnou odpověď: kdyby se tvářila, že je to v pořádku, "
        "byla by to nepravda s razítkem testu. Zavře to buď rozšíření "
        "tvaru o přivlastnění (`Poss=Yes` u `amod`), nebo V3, která určitý "
        "popis rozřeší na uzel a kvantifikátor tím přebije."
    ),
)


#: Celá sada v pořadí dialogů. Pořadí je součást zlatého transkriptu.
CORPUS: tuple[Golden, ...] = (A1, A2, B1, C1, D1, D2, D3, E1, E2, F1, F2)


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
