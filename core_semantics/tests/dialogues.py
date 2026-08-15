"""Zlaté dialogy pěti domén — L‑7.

Bod 6 dodatku G fixoval **rozbor** deseti vět. Tohle fixuje **celý tah**:
česká věta → čtení → vazby zmínek na uzly → zápis do báze nebo doložená
odpověď. Pět domén, které do L‑5 existovaly jen strukturovaně.

**Proč se fixují i vazby.** Predikace řekne, že se mluví o „Filipovi";
teprve `Anchor` řekne, na KTERÝ uzel to přistálo a proč — jestli se
zakládal nový, nebo se použil ten z předchozího tahu. Právě tady se
láme kanonizace jmen z M‑2, takže sada, která by fixovala jen predikaci,
by tu vrstvu minula.

**Co v dialozích NENÍ česky.** Můstková pravidla. § 6.12 je nezavádí
větou, ale nabídkou a potvrzením, takže patří do strukturovaných tahů —
předstírat, že je systém přečte z věty, by bylo tvrzení navíc.

Rozbory jsou psané ručně podle UD‑PDT pod jednou proveniencí, ze stejného
důvodu jako v `golden.py`: fixovat rozbor a rozbor modelu jsou dvě různé
věci a nesmí se měřit najednou.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core_semantics.lexicon import (
    LearnedPattern,
    Lexicon,
    Operation,
    PatternStatus,
    RoleMapping,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance

PROVENANCE = "udpipe2 model=cs_all-ud-2.17-251125 tokenizer=6247b8b7a5c8"


def w(
    form: str, lemma: str, upos: str, head: int, deprel: str, **feats: str
) -> tuple[str, str, str, int, str, tuple[tuple[str, str], ...]]:
    """Slovo bez indexu — ten se dopočítá z pořadí."""
    return (form, lemma, upos, head, deprel, tuple(sorted(feats.items())))


def sentence(*words: tuple[str, str, str, int, str, tuple[tuple[str, str], ...]]) -> Reading:
    return Reading(
        tokens=tuple(
            Token(
                index=i,
                form=form,
                lemma=lemma,
                upos=upos,
                head=head,
                deprel=deprel,
                feats=feats,
            )
            for i, (form, lemma, upos, head, deprel, feats) in enumerate(words, 1)
        ),
        provenance=PROVENANCE,
    )


@dataclass(frozen=True, slots=True)
class Step:
    """Jeden tah dialogu, i s tím, co se od něj čeká.

    Prázdné pole znamená „na tomhle netrvám", ale `refuses` a `asks`
    prázdné nejsou nikdy zbytečně: bez nich by odmítnutí a doptání
    nešlo odlišit od regrese.
    """

    text: str
    #: Rozbor věty. `None` znamená, že krok NENÍ VĚTA, ale TAH — odpověď
    #: na otázku, kterou systém položil o krok dřív.
    reading: Reading | None = None
    reads: str = ""
    #: Očekávané vazby zmínek na uzly, jako `„tvar“ → uzel`.
    anchors: tuple[str, ...] = ()
    #: Formule, která má skončit v bázi. Prázdné = tah nic nezapisuje.
    writes: str = ""
    #: Očekávaný verdikt otázky (`A` / `N` / `U` / `CONFLICT`).
    answers: str = ""
    asks: str = ""
    refuses: str = ""
    #: `(jméno role, operace)` — krok je ODPOVĚĎ `→∀` na otázku po
    #: kvantifikátoru role z PŘEDCHOZÍHO kroku. Tvar se dopočítá z té
    #: čekající role, neopisuje se: opsaný tvar by se mohl rozejít s tím,
    #: na co se systém doopravdy ptal.
    #:
    answers_quantifier: tuple[str, Operation] | None = None
    #: `(jméno role, operace)` — krok je ODPOVĚĎ `→∀1` na tutéž otázku,
    #: ale JEN PRO TU JEDNU VĚTU. Tvar se tím NEUČÍ, takže se další věta
    #: téhož tvaru zeptá znovu — a přesně to čeština u některých tvarů
    #: potřebuje (N‑8).
    answers_here: tuple[str, Operation] | None = None
    #: Operace — krok je ODPOVĚĎ `→⊆` na otázku, KTEROU JÁDROVOU RELACI
    #: stavba věty tvrdí (N‑2). Tvar konstrukce se dopočítá z předchozího
    #: kroku, neopisuje se.
    answers_relation: Operation | None = None
    #: Operace — krok je ODPOVĚĎ `→⊆1`, tedy jádrová relace JEN PRO TU
    #: JEDNU VĚTU. Tvar se tím neučí: „Praha je součástí Česka." a
    #: „Pondělí je součástí týdne." mají týž tvar a různé relace (N‑11).
    answers_relation_here: Operation | None = None
    #: Jméno skupiny — krok je POTVRZENÍ uzavření světa (`!∀`). Vlastní
    #: pole, a ne jedna z odpovědí: `complete(g)` se ničím neučí a je to
    #: jediný výrok, který mění, co znamená TICHO.
    declares_complete: str = ""
    #: `(jméno role, uzel)` — krok ROZHODUJE, na koho zájmeno odkazuje
    #: (`→=`). Vlastní pole: shoda rodu a čísla je vodítko struktury
    #: textu, ne důkaz, takže antecedent vybírá ČLOVĚK i tehdy, když je
    #: kandidát jediný.
    decides_reference: tuple[str, str] | None = None
    #: `(hlava, genitiv, jméno role)` — krok POJMENUJE roli genitivního
    #: přívlastku (`→@1`) a zapíše DRUHÝ VÝROK vedle věty. Vlastní pole:
    #: není to role predikace, a nic se tím neučí.
    names_attribute: tuple[str, str, str] | None = None
    #: `(tvar, jméno role)` — krok POJMENUJE ztracenou roli (`→@`). Na
    #: rozdíl od `→@1` se tím TVAR UČÍ: u vedlejší věty je odpověď
    #: v rozboru (spojka jako `mark`), takže druhá věta s touž spojkou
    #: se už neptá.
    names_role: tuple[str, str] | None = None
    #: `(jméno, titul, druh)` — krok POTVRZUJE, co tvrdí TITUL (`→∈`), a
    #: zapíše DRUHÝ VÝROK vedle věty. Vlastní pole, ne jedna z odpovědí:
    #: není to role predikace ani tvar, který by se učil — „prezident
    #: Masaryk“ v jiné větě znamená totéž a bude se ptát znovu.
    #: Druh je „povolání“ nebo „úřad“ a rozhoduje ho ČLOVĚK: z rozboru
    #: se přečíst nedá a rozdíl není nuance — u úřadu by bezčasé členství
    #: platilo šíř, než co věta říká *(W‑57)*.
    confirms_title: tuple[str, str, str] | None = None
    #: Důvod — krok ODVOLÁVÁ výrok zapsaný krokem `declares_complete`.
    #: Uzavření světa je DEKLARACE, ne trvalá vlastnost, a sada to musí
    #: umět projít celou cestou tam i zpět.
    revokes_complete: str = ""
    #: Věc, která je na tomhle kroku VĚCNĚ ŠPATNĚ a ví se proč. Zapsaná
    #: mez není totéž co selhání: krok projde, ale nepředstírá se, že je
    #: v pořádku všechno.
    limit: str = ""
    point: str = ""


@dataclass(frozen=True, slots=True)
class Dialogue:
    name: str
    source: str
    steps: tuple[Step, ...]
    #: Tvary potvrzené člověkem pro tuhle doménu. Do `czech_seed()` nepatří
    #: — tam by z nich byl tichý default pro každého, kdo knihovnu použije.
    shapes: tuple[tuple[str, str, str, str, Operation], ...] = ()
    #: Významy POVRCHOVÝCH ROLÍ, které člověk pro tuhle doménu potvrdil
    #: (`v+Loc → kde`). Týž důvod jako u `shapes`: `v+Loc` je „v Praze"
    #: i „v pondělí", takže do seedu nepatří — je to rozhodnutí, ne
    #: vlastnost češtiny, a v záznamu domény má být vidět, že padlo.
    roles: tuple[tuple[str, str], ...] = ()
    note: str = ""
    #: Co doména ukázat NEUMÍ. Doména, která svou mez nepřizná, tvrdí
    #: víc, než dokládá — a zrovna u akceptační sady je to nebezpečné,
    #: protože ta sada JE smlouva.
    limit: str = ""

    def lexicon(self) -> Lexicon:
        lexicon = czech_seed()
        for surface, canonical in self.roles:
            lexicon.add_role(
                RoleMapping(
                    surface=surface,
                    canonical=canonical,
                    learned_from=f"dialog {self.name}, potvrzeno člověkem",
                    status=PatternStatus.CONFIRMED,
                )
            )
        for upos, number, case, deprel, operation in self.shapes:
            lexicon.add(
                LearnedPattern(
                    trigger=Trigger(
                        lemma="", upos=upos, number=number, case=case, deprel=deprel
                    ),
                    operation=operation,
                    learned_from=f"dialog {self.name}, potvrzeno člověkem",
                    status=PatternStatus.CONFIRMED,
                )
            )
        return lexicon

    def recordings(self) -> dict[str, Utterance]:
        return {
            step.text: Utterance(text=step.text, readings=(step.reading,))
            for step in self.steps
            if step.reading is not None
        }


# Tvary, které potřebuje skoro každá doména. Vypisují se u dialogů znovu,
# protože „co člověk potvrdil" je součást zlatého záznamu, ne konfigurace.
PROPN_SUBJ = ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF)
PROPN_OBJ = ("PROPN", "Sing", "Acc", "obj", Operation.SELF)
PROPN_LOC = ("PROPN", "Sing", "Loc", "obl", Operation.SELF)
NOUN_SUBJ_SG = ("NOUN", "Sing", "Nom", "nsubj", Operation.FOR_ALL)
NOUN_SUBJ_PL = ("NOUN", "Plur", "Nom", "nsubj", Operation.FOR_ALL)
NOUN_OBJ_SG = ("NOUN", "Sing", "Acc", "obj", Operation.EXISTS)
NOUN_OBJ_PL = ("NOUN", "Plur", "Acc", "obj", Operation.EXISTS)
NOUN_ROOT = ("NOUN", "Sing", "Nom", "root", Operation.SELF)


# --------------------------------------------------------------------------
# 1 · Petrovice — dvě zvířata na témže místě
# --------------------------------------------------------------------------

PETROVICE = Dialogue(
    name="Petrovice",
    source="„Pes Roník bydlí ve vesničce Petrovice. Kočka Micka bydlí též "
    "ve vesničce Petrovice.“",
    shapes=(PROPN_SUBJ, NOUN_SUBJ_SG),
    # Rozhodnutí člověka, ne vlastnost češtiny: `v`+Loc je „v Praze"
    # i „v pondělí". Do seedu proto nepatří — systém se na něj PTÁ
    # (N‑3) a tohle je zapsaná odpověď pro tuhle doménu.
    roles=(("v+Loc/Geo", "kde"),),
    steps=(
        Step(
            text="Roník bydlí v Petrovicích.",
            reading=sentence(
                w("Roník", "roník", "NOUN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Petrovicích", "Petrovice", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="bydlet(kde:Petrovice, kdo:∀roník)",
            anchors=("Petrovicích → Petrovice (sort z role; místo)",),
            writes="bydlet(kde:Petrovice, kdo:∀roník)",
            point=(
                "MÍSTNÍ URČENÍ SE ZAKOTVÍ, jakmile je rozhodnuté, co `v`+Loc "
                "znamená. Sort filleru plyne z ROLE (§ 3.6), ne ze slova — "
                "„Petrovice“ je `Place`, protože `kde` je prostorová role"
            ),
            limit=(
                "„Roník“ je JMÉNO PSA, parser z něj udělá obecné jméno "
                "s lemmatem „roník“. Táž třída jako „Postřižiny“: rozpoznat "
                "vlastní jméno, které není v žádném rejstříku, je znalost "
                "světa, ne morfologie. Doména na tom nestojí — mluví se "
                "o TÉMŽ uzlu v obou větách, ať se jmenuje jakkoli"
            ),
        ),
        Step(
            text="Micka bydlí v Petrovicích.",
            reading=sentence(
                w("Micka", "Micka", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Petrovicích", "Petrovice", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="bydlet(kde:Petrovice, kdo:·Micka)",
            writes="bydlet(kde:Petrovice, kdo:Micka)",
            point=(
                "JEDNA ODPOVĚĎ ZAVŘELA CELOU TŘÍDU VĚT: `v`+Loc se "
                "nepojmenovává znovu, tvar už význam má"
            ),
        ),
        Step(
            text="Bydlí Micka v Petrovicích?",
            reading=sentence(
                w("Bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Micka", "Micka", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Petrovicích", "Petrovice", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="bydlet(kde:Petrovice, kdo:·Micka)",
            anchors=("Micka → Micka (kanonicky; týž uzel, o kterém už řeč byla)",),
            answers="A",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Tohle je krok, kvůli "
                "kterému dialog existuje: dvě zvířata na TÉMŽE místě a "
                "odpověď doložená zapsaným výrokem"
            ),
        ),
    ),
    note=(
        "Petrovice byly dlouho MEZ: bez rozhodnutí `v`+Loc → `kde` se "
        "místní určení nezakotvilo a dialog neprošel. Od N‑3 se systém "
        "na význam tvaru PTÁ a odpověď je tah, takže mez zmizela — ne "
        "tím, že by se význam uhodl, ale tím, že se na něj někdo zeptal."
    ),
)


# --------------------------------------------------------------------------
# 2 · Jana a zmrzlina — řetěz dvou ∃-relací
# --------------------------------------------------------------------------

ICE_CREAM = Dialogue(
    name="Jana a zmrzlina",
    source="„Jana je učitelka. Děti mají rády zmrzlinu.“",
    # `iobj` je tvar bez významu (viz mez u druhého kroku) — a co znamená
    # v TÉHLE doméně, je rozhodnutí člověka, ne vlastnost češtiny.
    roles=(("iobj", "jak"),),
    shapes=(
        PROPN_SUBJ,
        NOUN_ROOT,
        NOUN_SUBJ_PL,
        NOUN_OBJ_SG,
        # „rády" je podle § 6.12 SKUPINA jako každá jiná, takže
        # kvantifikátor potřebuje. Tvar říká `iobj`, ne `advmod`: tady se
        # zapisuje, co dal PARSER, ne co by bylo mluvnicky správně —
        # jinak by vzor nikdy nesedl a věta by se dál nedopočítala.
        ("ADJ", "Plur", "", "iobj", Operation.SELF),
    ),
    steps=(
        Step(
            text="Jana je učitelka.",
            reading=sentence(
                w("Jana", "Jana", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("učitelka", "učitelka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Jana, group:·učitelka)",
            anchors=("Jana → Jana (založen)", "učitelka → učitelka (obecné jméno)"),
            writes="member(elem:Jana, group:·učitelka)",
            point=(
                "spona: vlastní jméno je uzel, jmenná část je skupina — "
                "a od N‑2d je to ČLENSTVÍ, ne reifikovaný vztah `být`. "
                "`PROPN` v podmětu JE signál individua, takže tady je to "
                "rozhodnutelné; u `NOUN=NOUN` (Kočka je savec / Mourek "
                "je kočka) není a systém se ptá. Do téhle změny v bázi "
                "leželo SLABŠÍ tvrzení, než co člověk řekl"
            ),
        ),
        Step(
            text="Děti mají rády zmrzlinu.",
            reading=sentence(
                w("Děti", "dítě", "NOUN", 2, "nsubj", Case="Nom", Gender="Fem", Number="Plur"),
                w("mají", "mít", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("rády", "rád", "ADJ", 2, "iobj", Animacy="Inan", Degree="Pos", Gender="Fem,Masc", Number="Plur", Polarity="Pos", Variant="Short"),
                w("zmrzlinu", "zmrzlina", "NOUN", 2, "obj", Case="Acc", Gender="Fem", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="mít(co:∃zmrzlina, jak:·rád, kdo:∀dítě)",
            writes="mít(co:∃zmrzlina, jak:·rád, kdo:∀dítě)",
            point=(
                "VĚTA, KTERÁ SE DLOUHO NEPŘEČETLA VŮBEC. Parser označí "
                "„rády“ jako `iobj`; kaskáda to slévala s `obj` na roli "
                "`co`, takže dva členy dostaly touž roli, čtení "
                "s duplicitou se nesmí vyrobit a nezbylo ani jedno. Rozbor "
                "ta dvě místa ROZLIŠUJE — zahazovala to kaskáda, ne "
                "čeština. Táž třída jako B‑9, jen o patro blíž jádru"
            ),
            limit=(
                "`iobj` je tu VĚCNĚ CHYBNÝ ROZBOR: „rády“ je v téhle vazbě "
                "příslovce, ne nepřímý předmět (skutečný nepřímý předmět "
                "dá čeština jako `obl:arg`, tedy `Dat:arg` — „Petr dal "
                "Pavlovi knihu“). Systém se tím ale nemá zastavit: tvar "
                "dostane povrchové jméno, zeptá se, co znamená, a člověk "
                "odpoví `jak`. Chybu parseru neopravíme, jen ji "
                "nepřevezmeme jako významové rozhodnutí"
            ),
        ),
        Step(
            text="Je Jana učitelka?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Jana", "Jana", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Giv", Number="Sing"),
                w("učitelka", "učitelka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Jana, group:·učitelka)",
            anchors=(
                "Jana → Jana (kanonicky; týž uzel, o kterém už řeč byla)",
            ),
            answers="A",
            point="KANONIZACE: druhá zmínka „Jany“ míří na týž uzel, a "
            "říká se to nahlas (M‑2)",
        ),
    ),
)


# --------------------------------------------------------------------------
# 3 · Doprava — obecné tvrzení a otázka na ně
# --------------------------------------------------------------------------

TRANSPORT = Dialogue(
    name="Doprava",
    source="„Auta jezdí po dálnici.“",
    shapes=(NOUN_SUBJ_PL,),
    steps=(
        Step(
            text="Auta jezdí po dálnici.",
            reading=sentence(
                w("Auta", "auto", "NOUN", 2, "nsubj", Case="Nom", Gender="Neut", Number="Plur"),
                w("jezdí", "jezdit", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("po", "po", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("dálnici", "dálnice", "NOUN", 2, "obl", Case="Loc", Gender="Fem", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="jezdit(kdo:∀auto, kudy:dálnice)",
            anchors=(
                "Auta → auto (obecné jméno)",
                "dálnici → dálnice (sort z role; místo)",
            ),
            writes="jezdit(kdo:∀auto, kudy:dálnice)",
            point="`po`+Loc → `kudy` je naučené mapování; sort určí ROLE, "
            "ne slovo, a místo se nekvantifikuje",
        ),
        Step(
            text="Jezdí auta po dálnici?",
            reading=sentence(
                w("Jezdí", "jezdit", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("auta", "auto", "NOUN", 1, "nsubj", Case="Nom", Gender="Neut", Number="Plur"),
                w("po", "po", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("dálnici", "dálnice", "NOUN", 1, "obl", Case="Loc", Gender="Fem", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="jezdit(kdo:∀auto, kudy:dálnice)",
            answers="A",
            point="táž věta s otazníkem: `?` → `ask`, ne `attach`",
        ),
    ),
)


# --------------------------------------------------------------------------
# 4 · Farmaka — negace, na které stojí celý závěr domény
# --------------------------------------------------------------------------

PHARMA = Dialogue(
    name="Farmaka",
    source="„Pacient Jan má alergii. Jan nesmí dostat penicilin.“",
    shapes=(PROPN_SUBJ, NOUN_OBJ_SG),
    note=(
        "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Krok 3 fixuje verdikt `N` "
        "s citací zapsaného popření — právě to je kritérium téhle "
        "domény: `N` z DOLOŽENÉHO popření, ne z nevědomosti (I‑21). "
        "Dokud tu stálo jen `reads`, hlídala sada ROZBOR a závěr "
        "nechávala bez dozoru; doména vracela `U` tam, kde její "
        "vlastní kritérium žádá `N` — a v lékové doméně je to přesně "
        "ta záměna, před kterou to kritérium varuje. "
        "Že věta prochází, umožnil SLOŽENÝ PŘÍSUDEK: „nesmí dostat“ je "
        "jeden děj, ne modální sloveso s vnořenou rolí. Předtím visel "
        "`penicilin` pod infinitivem a věta se nezakotvila."
    ),
    steps=(
        Step(
            text="Jan má alergii.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("má", "mít", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("alergii", "alergie", "NOUN", 2, "obj", Case="Acc", Gender="Fem", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="mít(co:∃alergie, kdo:·Jan)",
            writes="mít(co:∃alergie, kdo:Jan)",
            point="jediný tah téhle domény, který dnes projde až do báze",
        ),
        Step(
            text="Jan nesmí dostat penicilin.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("nesmí", "smět", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("dostat", "dostat", "VERB", 2, "xcomp", Aspect="Perf", Polarity="Pos", VerbForm="Inf"),
                w("penicilin", "penicilin", "NOUN", 3, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="¬smět_dostat(co:∃penicilin, kdo:·Jan)",
            writes="¬smět_dostat(co:∃penicilin, kdo:Jan)",
            point="ZÁVĚR CELÉ DOMÉNY. Bez čtení `Polarity=Neg` by věta "
            "znamenala pravý opak — a to je v téhle doméně rozdíl, "
            "který se nepočítá v bodech",
        ),
        Step(
            text="Smí Jan dostat penicilin?",
            reading=sentence(
                w("Smí", "smět", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Jan", "Jan", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("dostat", "dostat", "VERB", 1, "xcomp", Aspect="Perf", Polarity="Pos", VerbForm="Inf"),
                w("penicilin", "penicilin", "NOUN", 3, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="smět_dostat(co:∃penicilin, kdo:·Jan)",
            # VERDIKT JAKO PODMÍNKA, ne jako próza. Test, který fixuje jen
            # `reads`, hlídá ROZBOR — a závěr domény nechá bez dozoru.
            answers="N",
            point="`N` z DOLOŽENÉHO popření, ne z nevědomosti (I‑21). "
            "„Nevím“ by tady byla jiná a nebezpečnější odpověď",
        ),
    ),
)


# --------------------------------------------------------------------------
# 5 · Čas a prostor — dialog D složený na fakta
# --------------------------------------------------------------------------

TIME_AND_PLACE = Dialogue(
    name="Čas a prostor",
    source="„Petr jel v pondělí do Prahy. V úterý jel Petr do Brna.“",
    shapes=(PROPN_SUBJ, ("NOUN", "Sing", "Loc", "obl", Operation.EXISTS)),
    # Táž odpověď jako u Petrovic, a je to TÝŽ tvar: jedna věta člověka
    # zavírá `v`+Loc pro obě domény.
    roles=(("v+Loc/Geo", "kde"),),
    steps=(
        Step(
            text="Petr jel do Prahy.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("jel", "jet", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("do", "do", "ADP", 4, "case", AdpType="Prep", Case="Gen"),
                w("Prahy", "Praha", "PROPN", 2, "obl", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="jet(kam:Praha, kdo:·Petr)",
            anchors=(
                "Petr → Petr (založen)",
                "Prahy → Praha (sort z role; místo)",
            ),
            writes="jet(kam:Praha, kdo:Petr)",
        ),
        Step(
            text="Petr jel do Brna.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("jel", "jet", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("do", "do", "ADP", 4, "case", AdpType="Prep", Case="Gen"),
                w("Brna", "Brno", "PROPN", 2, "obl", Case="Gen", Gender="Neut", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="jet(kam:Brno, kdo:·Petr)",
            anchors=("Petr → Petr (kanonicky; týž uzel, o kterém už řeč byla)",),
            writes="jet(kam:Brno, kdo:Petr)",
            point="druhá zmínka „Petra“ míří na týž uzel — bez toho by "
            "dialog D mluvil o dvou různých lidech",
        ),
        Step(
            text="Jel Petr do Prahy?",
            reading=sentence(
                w("Jel", "jet", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Petr", "Petr", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("do", "do", "ADP", 4, "case", AdpType="Prep", Case="Gen"),
                w("Prahy", "Praha", "PROPN", 1, "obl", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="jet(kam:Praha, kdo:·Petr)",
            answers="A",
        ),
        Step(
            text="Jel Petr do Plzně?",
            reading=sentence(
                w("Jel", "jet", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Petr", "Petr", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("do", "do", "ADP", 4, "case", AdpType="Prep", Case="Gen"),
                w("Plzně", "Plzeň", "PROPN", 1, "obl", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="jet(kam:Plzeň, kdo:·Petr)",
            answers="U",
            point="otevřený svět: o Plzni nikdo nic neřekl, takže `U` — "
            "a otázka na neznámé místo ŽÁDNÝ uzel nezaloží (§ 0.2)",
        ),
        Step(
            text="Petr byl v pondělí v Praze.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 6, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("byl", "být", "AUX", 6, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Acc"),
                w("pondělí", "pondělí", "NOUN", 6, "obl", Case="Acc", Gender="Neut", Number="Sing"),
                w("v", "v", "ADP", 6, "case", AdpType="Prep", Case="Loc"),
                w("Praze", "Praha", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 6, "punct"),
            ),
            reads="být(kde:Praha, kdo:·Petr, kdy:pondělí)",
            anchors=(
                "Praze → Praha (sort z role; místo)",
                "pondělí → pondělí (sort z role; čas)",
            ),
            writes="být(kde:Praha, kdo:Petr, kdy:pondělí)",
            point=(
                "ČAS A MÍSTO V JEDNÉ VĚTĚ, oba ze SPONY. Do N‑4 dávala "
                "tahle věta `co:Praha`, tedy „Petr BYL Prahou“: UD dělá "
                "„Praze“ kořenem a „byl“ sponou, takže sponové pravidlo "
                "vzalo kořen jako jmennou část. PŘEDLOŽKA u kořene je "
                "tvrdý signál, že jmenná část to není — „být prostředek“ "
                "ji nemá, „být v Praze“ ji má vždycky"
            ),
        ),
    ),
)



# --------------------------------------------------------------------------
# 6 · Vegetarián a steak — logický rozpor (odstavec 6 z deseti)
# --------------------------------------------------------------------------

VEGETARIAN = Dialogue(
    name="Vegetarián a steak",
    source="„Petr je vegetarián. Vegetarián nejí maso. Steak je druh masa. "
    "Petr jedl steak.“",
    shapes=(
        PROPN_SUBJ,
        NOUN_SUBJ_SG,
        # Předmět v akuzativu tu POTVRZENÝ TVAR NEMÁ, a je to jádro téhle
        # domény: ve „Vegetarián nejí maso" je `∀`, v „Petr jedl steak"
        # `∃`, a je to týž tvar. Rozhoduje se proto VĚTA PO VĚTĚ tahem
        # `→∀1`, který se nic neučí (N‑8).
    ),
    steps=(
        Step(
            text="Petr je vegetarián.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("vegetarián", "vegetarián", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Petr, group:·vegetarián)",
            writes="member(elem:Petr, group:·vegetarián)",
            point="členství — první článek řetězu",
        ),
        Step(
            text="Vegetarián nejí maso.",
            reading=sentence(
                w("Vegetarián", "vegetarián", "NOUN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("nejí", "jíst", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("maso", "maso", "NOUN", 2, "obj", Case="Acc", Gender="Neut", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            asks=(
                "ptá se na kvantifikátor předmětu — potvrzený tvar tahle "
                "doména nemá a mít nemůže, viz krok o dva dál"
            ),
            point=(
                "ODPOVĚĎ NA OTÁZKU, KVŮLI KTERÉ TENHLE DIALOG VZNIKL. "
                "Vypadá to jako PRAVIDLO (kdo je vegetarián, nejí maso), "
                "a česky se pravidlo zapsat neumí — jenže tady se nemusí. "
                "Je to FAKT o třídě se SILNOU NEGACÍ a s ∀ na obou rolích; "
                "co dělá práci pravidla, je DISTRIBUCE KVANTIFIKOVANÝCH "
                "ROLÍ (§ 5.2). Pravidlo z věty tedy NENÍ další patro, aspoň "
                "ne kvůli tomuhle odstavci"
            ),
        ),
        Step(
            text="Jde o maso obecně.",
            answers_here=("co", Operation.FOR_ALL),
            reads="¬jíst(co:∀maso, kdo:∀vegetarián)",
            writes="¬jíst(co:∀maso, kdo:∀vegetarián)",
            point=(
                "ODPOVĚĎ JE TAH, A PLATÍ JEN PRO TUHLE VĚTU. Generické "
                "popření mluví o KAŽDÉM masu; bez `∀` by z něj bylo "
                "„nějaké maso nejí“, což je mnohem slabší tvrzení, ze "
                "kterého závěr domény neplyne"
            ),
        ),
        Step(
            text="Steak je druh masa.",
            reading=sentence(
                w("Steak", "steak", "NOUN", 3, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("druh", "druh", "NOUN", 0, "root", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w("masa", "maso", "NOUN", 3, "nmod", Case="Gen", Gender="Neut", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="subset(sub:·steak, sup:·maso)",
            writes="subset(sub:·steak, sup:·maso)",
            point="podtřída — druhý článek, týž tvar jako u Amoxicilinu",
        ),
        Step(
            text="Petr jedl steak.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("jedl", "jíst", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("steak", "steak", "NOUN", 2, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            asks=(
                "TÁŽ OTÁZKA JAKO O TŘI KROKY DŘÍV — a to je důkaz, že se "
                "tvar předchozí odpovědí nenaučil. Kdyby ano, věta by se "
                "přečetla jako `∀steak` a nikdo by se nezeptal"
            ),
            point=(
                "věta, která rozpor způsobí — systém ji ZAPÍŠE (až po "
                "odpovědi), i když hlásí, že odporuje bázi: stranu sporu "
                "si nevybírá (I‑3)"
            ),
        ),
        Step(
            text="Šlo o jeden steak.",
            answers_here=("co", Operation.EXISTS),
            reads="jíst(co:∃steak, kdo:·Petr)",
            writes="jíst(co:∃steak, kdo:Petr)",
            point=(
                "TÝŽ TVAR, JINÁ ODPOVĚĎ — celý důvod, proč je tenhle krok "
                "tahem a ne řádkem v `shapes`. Petr snědl JEDEN steak; "
                "`∀steak` by bylo věcně špatně a závěr domény by stál na "
                "chybném čtení"
            ),
        ),
        Step(
            text="Jedl Petr maso?",
            reading=sentence(
                w("Jedl", "jíst", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Petr", "Petr", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("maso", "maso", "NOUN", 1, "obj", Case="Acc", Gender="Neut", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            asks="i otázka potřebuje kvantifikátor — tvar pořád naučený není",
            point="ptát se musí i u otázky; jinak by se dotaz četl jinak než věta",
        ),
        Step(
            text="Ptám se na nějaké maso.",
            answers_here=("co", Operation.EXISTS),
            reads="jíst(co:∃maso, kdo:·Petr)",
            answers="CONFLICT",
            point=(
                "MEZIKROK, na kterém je vidět, že řetěz drží: protidůkaz "
                "neplyne z ničeho zapsaného o Petrovi a mase, ale "
                "z DISTRIBUCE generického popření přes členství — a od "
                "B‑13 sedne i na `∃` dotaz, protože negace obrací "
                "monotonii. "
                "VERDIKT SE TU ZMĚNIL Z `N` NA `CONFLICT` A JE TO "
                "DŮSLEDEK SPRÁVNÉHO ČTENÍ. Dokud se „Petr jedl steak“ "
                "zapisovalo jako `∀steak`, měla tahle otázka jen důkaz "
                "PROTI. Se správným `∃steak` a `steak ⊆ maso` má i důkaz "
                "PRO, takže spor je věcně na místě: Petr snědl něco, co "
                "je maso, a o mase je doložené popření. Distribuce se "
                "neztratila — je uvnitř toho sporu"
            ),
        ),
        Step(
            text="Jedl Petr steak?",
            reading=sentence(
                w("Jedl", "jíst", "VERB", 0, "root", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Petr", "Petr", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("steak", "steak", "NOUN", 1, "obj", Animacy="Inan", Case="Acc", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            asks="a naposledy totéž — tvar zůstal nenaučený celou dobu",
            point="poslední doklad, že `→∀1` opravdu nic neučí",
        ),
        Step(
            text="Ptám se na nějaký steak.",
            answers_here=("co", Operation.EXISTS),
            reads="jíst(co:∃steak, kdo:·Petr)",
            answers="CONFLICT",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. `CONFLICT` se DVĚMA "
                "důkazy: pro z toho, co Petr udělal, proti přes tři články "
                "(členství → podtřída → distribuce). Systém stranu "
                "NEVYBÍRÁ a obě větve pojmenuje — právě to odstavec 6 "
                "z deseti požaduje"
            ),
        ),
    ),
    note=(
        "Šestý akceptační dialog a první z DESETI ODSTAVCŮ, který jde "
        "česky celý. Odpovídá na otázku, jestli je pravidlo z věty další "
        "patro: NENÍ — generické popření je fakt o třídě a práci pravidla "
        "odvede distribuce rolí. Zbylé odstavce potřebují abdukci, "
        "pragmatiku, shrnutí nebo modalitu, tedy vrstvy, ne patra."
    ),
)



# --------------------------------------------------------------------------
# 7 · Pořadí dnů — jádrová relace `before` z české věty
# --------------------------------------------------------------------------

ORDER = Dialogue(
    name="Pořadí dnů",
    source="„Pondělí je před úterým. Úterý je před středou.“",
    steps=(
        Step(
            text="Pondělí je před úterým.",
            reading=sentence(
                w("Pondělí", "pondělí", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
                w("je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
                w("úterým", "úterý", "NOUN", 0, "root", Case="Ins", Gender="Neut", Number="Sing"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="before(earlier:pondělí, later:úterý)",
            anchors=("Pondělí → pondělí (sort z role; sort z jádrové relace)",),
            writes="before(earlier:pondělí, later:úterý)",
            point=(
                "PRVNÍ JÁDROVÁ RELACE NAD ČASEM, KTEROU VYROBÍ ČESKÁ VĚTA. "
                "Do N‑9 zapisovala akceptační sada z devíti jádrových "
                "predikátů jen dva; `before` uměl evaluátor, ale žádná věta "
                "k němu nevedla — a schopnost, kterou jazyk nedosáhne, se "
                "nedá odlišit od schopnosti, která nefunguje"
            ),
        ),
        Step(
            text="Úterý je před středou.",
            reading=sentence(
                w("Úterý", "úterý", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
                w("je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
                w("středou", "středa", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="before(earlier:úterý, later:středa)",
            writes="before(earlier:úterý, later:středa)",
            point="druhý článek — bez něj by se tranzitivita neměla na čem ukázat",
        ),
        Step(
            text="Je pondělí před středou?",
            reading=sentence(
                w("Je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("pondělí", "pondělí", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
                w("před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
                w("středou", "středa", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="before(earlier:pondělí, later:středa)",
            answers="A",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA — a je TRANZITIVNÍ: "
                "tenhle vztah nikdo nezapsal, plyne z OBOU zapsaných "
                "a důkaz cituje oba. Jediný zápis by uzávěr neprověřil"
            ),
        ),
        Step(
            text="Je středa před pondělím?",
            reading=sentence(
                w("Je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("středa", "středa", "NOUN", 4, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
                w("před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
                w("pondělím", "pondělí", "NOUN", 0, "root", Case="Ins", Gender="Neut", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="before(earlier:středa, later:pondělí)",
            answers="U",
            point=(
                "OPAČNÝ SMĚR DÁ `U`, NE `N`, a to je celý otevřený svět: "
                "z „pondělí je před středou“ NEPLYNE, že středa před "
                "pondělím není — plynulo by to teprve z uzavření osy, "
                "které nikdo nevyslovil. `N` by tu bylo tvrzení navíc"
            ),
        ),
    ),
    note=(
        "Sedmý akceptační dialog. Otevírá českou cestu k jádrovým relacím, "
        "ke kterým dosud žádná věta nevedla: uzávěr `before*` je "
        "tranzitivní, takže doména prověří ŘETĚZ, ne jeden zápis."
    ),
)



# --------------------------------------------------------------------------
# 8 · Vrabec a savec — `disjoint` a `ne` z VYLOUČENÍ TŘÍD
# --------------------------------------------------------------------------

EXCLUSION = Dialogue(
    name="Vrabec a savec",
    source="„Vrabec není savec. Čimčara je vrabec.“",
    shapes=(PROPN_SUBJ,),
    steps=(
        Step(
            text="Vrabec není savec.",
            reading=sentence(
                w("Vrabec", "vrabec", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("není", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="disjoint(a:·vrabec, b:·savec)",
            writes="disjoint(a:·vrabec, b:·savec)",
            point=(
                "ODDĚLENOST TŘÍD Z ČESKÉ VĚTY — a zapisuje se SPRÁVNÝMI "
                "DVEŘMI: `add_disjoint` k markeru vygeneruje dvojici "
                "pravidel se silnou negací, bez kterých by `disjoint` "
                "v indexu ležel a NEODVODILO by se z něj nic"
            ),
        ),
        Step(
            text="Čimčara je vrabec.",
            reading=sentence(
                w("Čimčara", "Čimčara", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("vrabec", "vrabec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Čimčara, group:·vrabec)",
            writes="member(elem:Čimčara, group:·vrabec)",
            point="druhý článek — bez individua se vyloučení nemá na čem ukázat",
        ),
        Step(
            text="Je Čimčara savec?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Čimčara", "Čimčara", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Čimčara, group:·savec)",
            answers="N",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. `N` Z VYLOUČENÍ "
                "TŘÍD — nikdo neřekl, že Čimčara savec není; plyne to "
                "z členství a z oddělenosti, a důkaz cituje OBOJE. Je to "
                "jediná cesta, kterou systém řekne „ne“ jinak než "
                "z přímého popření"
            ),
        ),
        Step(
            text="Je Čimčara pták?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Čimčara", "Čimčara", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("pták", "pták", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Čimčara, group:·pták)",
            answers="U",
            point=(
                "OTEVŘENÝ SVĚT. O ptácích nikdo nic neřekl, takže `U` — "
                "oddělenost od savců o nich NEROZHODUJE. Kdyby tu padlo "
                "`N`, byla by to nevědomost vydávaná za znalost"
            ),
        ),
        Step(
            text="Kočka je savec.",
            reading=sentence(
                w("Kočka", "kočka", "NOUN", 3, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            asks=(
                "HOLÁ KLADNÁ SPONA je dvojznačná: „Kočka je savec“ je "
                "podmnožina, „Mourek je kočka“ členství, a tvar je týž. "
                "Systém se ptá a do odpovědi NEZAPISUJE nic"
            ),
            point="táž stavba jako první krok, jen kladně — a rozhodnutá není",
        ),
        Step(
            text="Je to podmnožina.",
            answers_relation=Operation.SUBSET,
            reads="subset(sub:·kočka, sup:·savec)",
            writes="subset(sub:·kočka, sup:·savec)",
            point=(
                "ODPOVĚĎ JE TAH a učí KONSTRUKCI, ne větu: `cop:NOUN=NOUN` "
                "od téhle chvíle znamená podmnožinu pro celou doménu"
            ),
        ),
    ),
    note=(
        "Osmý akceptační dialog. `disjoint` uměla čeština vyrobit už dřív, "
        "ale ŽÁDNÁ DOMÉNA ho nepoužívala — takže se nikdy neprověřil řetěz "
        "member + disjoint → `N`, jediná cesta, kterou systém řekne „ne“ "
        "z VYLOUČENÍ TŘÍD. Schopnost, kterou nikdo neprojde, se nedá "
        "odlišit od schopnosti, která nefunguje."
    ),
)



# --------------------------------------------------------------------------
# 9 · Micka a Mourek — identita a její SPOR
# --------------------------------------------------------------------------

IDENTITY = Dialogue(
    name="Micka a Mourek",
    source="„Mourek je kočka. Micka je Mourek. … Micka není Mourek.“",
    steps=(
        Step(
            text="Mourek je kočka.",
            reading=sentence(
                w("Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("kočka", "kočka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Mourek, group:·kočka)",
            writes="member(elem:Mourek, group:·kočka)",
            point="fakt, který bude téct přes identitu — a pak přestane",
        ),
        Step(
            text="Micka je Mourek.",
            reading=sentence(
                w("Micka", "Micka", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Mourek", "Mourek", "PROPN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="same_as(left:·Micka, right:·Mourek)",
            writes="same_as(left:Micka, right:Mourek)",
            point=(
                "IDENTITA Z ČESKÉ VĚTY. Dvě VLASTNÍ JMÉNA spojená sponou "
                "netvrdí členství — „Mourek“ není třída, do které by Micka "
                "patřila. Slovní druh OBOU stran je proto součást tvaru"
            ),
        ),
        Step(
            text="Je Micka kočka?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Micka", "Micka", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Giv", Number="Sing"),
                w("kočka", "kočka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Micka, group:·kočka)",
            answers="A",
            point=(
                "FAKT TEČE PŘES IDENTITU a důkaz cituje OBA zápisy — "
                "o Micce samotné nikdo neřekl nic"
            ),
        ),
        Step(
            text="Micka není Mourek.",
            reading=sentence(
                w("Micka", "Micka", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("není", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Neg", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Mourek", "Mourek", "PROPN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="¬same_as(left:·Micka, right:·Mourek)",
            writes="¬same_as(left:Micka, right:Mourek)",
            point=(
                "POPŘENÍ SE ZAPÍŠE VEDLE, původní výrok zůstává NEDOTČENÝ "
                "— systém si stranu sporu nevybírá (I‑3)"
            ),
        ),
        Step(
            text="Micka je Mourek?",
            reading=sentence(
                w("Micka", "Micka", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Mourek", "Mourek", "PROPN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="same_as(left:·Micka, right:·Mourek)",
            answers="CONFLICT",
            point=(
                "PŘÍMÁ OTÁZKA NA SPORNOU IDENTITU dá `CONFLICT` se DVĚMA "
                "důkazy. Otázka se ptá bez inverze („Micka je Mourek?“), "
                "protože dvě vlastní jména za sebou parser čte jako JEDNO "
                "složené jméno (`flat`) — je to mez rozboru, ne kaskády"
            ),
        ),
        Step(
            text="Je Micka kočka?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Micka", "Micka", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Giv", Number="Sing"),
                w("kočka", "kočka", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Micka, group:·kočka)",
            answers="U",
            point=(
                "ZÁVĚR DOMÉNY: M‑1 Z ČEŠTINY. Táž otázka, která o tři "
                "kroky dřív dala `A`, padá zpátky na `U` — přes spornou "
                "identitu fakty NETEČOU. A `U`, ne `N`: nikdo neřekl, že "
                "Micka kočka není; jen se přestalo vědět, že je"
            ),
        ),
    ),
    note=(
        "Devátý akceptační dialog. `same_as` byla poslední jádrová relace, "
        "na které visí M‑1, a ta byla ve stálé regresi měřená VÝHRADNĚ NA "
        "FORMULÍCH. U identity je to nejdražší druh mezery: chyba tam uzly "
        "tiše slévá nebo štěpí, a to nepozná žádný test, ke kterému jazyk "
        "nevede."
    ),
)


# --------------------------------------------------------------------------
# 10 · Koncert — ZAHRNUTÍ V MÍSTĚ I V ČASE
# --------------------------------------------------------------------------

INCLUSION = Dialogue(
    name="Koncert",
    source=(
        "„Petrovice jsou součástí Plzně. Pondělí je součástí týdne. "
        "Koncert byl v Petrovicích v pondělí. … Byl koncert v Plzni "
        "během týdne?“"
    ),
    shapes=(
        ("PROPN", "Plur", "Nom", "nsubj", Operation.SELF),
        ("PROPN", "Plur", "Loc", "root", Operation.SELF),
        ("PROPN", "Sing", "Loc", "root", Operation.SELF),
        ("PROPN", "Sing", "Gen", "nmod", Operation.SELF),
        ("NOUN", "Sing", "Ins", "root", Operation.SELF),
        ("NOUN", "Sing", "Gen", "nmod", Operation.SELF),
        ("NOUN", "Sing", "Acc", "obl", Operation.SELF),
        ("NOUN", "Sing", "Gen", "obl", Operation.SELF),
        ("NOUN", "Sing", "Nom", "nsubj", Operation.EXISTS),
    ),
    roles=(("v+Loc/Geo", "kde"), ("během+Gen", "kdy")),
    steps=(
        Step(
            text="Petrovice jsou součástí Plzně.",
            reading=sentence(
                w("Petrovice", "Petrovice", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Geo", Number="Plur"),
                w("jsou", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
                w("Plzně", "Plzeň", "PROPN", 3, "nmod", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            asks=(
                "„být součástí“ NENÍ jádrová relace — je to tvar. Systém "
                "se ptá, kterou relaci ta stavba tvrdí, a MENU JE CELÉ "
                "RELATIONAL, ne ruční výčet"
            ),
            point=(
                "KROK, KTERÝ NIC NEZAPÍŠE — B‑17. Dokud je otázka na "
                "konstrukci otevřená, věta se NEZAPISUJE, přesně jako "
                "u čekajícího kvantifikátoru: je to táž třída rozhodnutí "
                "a tichý default je u ní zakázaný stejně (L‑3). Dřív se "
                "tu zapsalo být(Gen:Plzeň, co:·součást, kdo:Petrovice) — "
                "zápis pod přiznanou neznalostí (INV‑11), a otázka se "
                "přitom ZTRATILA"
            ),
        ),
        Step(
            text="Je to místo uvnitř místa.",
            answers_relation_here=Operation.CONTAINS,
            writes="contains(part:Petrovice, whole:Plzeň)",
            point=(
                "ODPOVĚĎ JE TAH, a `→⊆1` učí JEN TUHLE VĚTU: týž tvar "
                "znamená o dva kroky dál `within`, takže naučit ho pro "
                "celou doménu by bylo věcně špatně (N‑11)"
            ),
        ),
        Step(
            text="Pondělí je součástí týdne.",
            reading=sentence(
                w("Pondělí", "pondělí", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
                w("týdne", "týden", "NOUN", 3, "nmod", Animacy="Inan", Case="Gen", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            asks=(
                "PTÁ SE ZNOVU, a je to důkaz, že se tvar minule NENAUČIL. "
                "Kdyby `→⊆1` tvar zapsala, tenhle krok by se nezeptal — "
                "a odpověděl by `contains` o čase"
            ),
            point="druhý krok, který nic nezapíše, a z jiného důvodu než z neznalosti tvaru",
        ),
        Step(
            text="Je to čas uvnitř času.",
            answers_relation_here=Operation.WITHIN,
            writes="within(part:pondělí, whole:týden)",
            point=(
                "TÝŽ TVAR, JINÁ RELACE. `contains` a `within` se liší "
                "sortem, ne stavbou — a rozhodnout to umí jen člověk"
            ),
        ),
        Step(
            text="Koncert byl v Petrovicích v pondělí.",
            reading=sentence(
                w("Koncert", "koncert", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w("byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Petrovicích", "Petrovice", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w("v", "v", "ADP", 6, "case", AdpType="Prep", Case="Acc"),
                w("pondělí", "pondělí", "NOUN", 4, "obl", Case="Acc", Gender="Neut", Number="Sing"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="být(kde:Petrovice, kdo:∃koncert, kdy:pondělí)",
            writes="být(kde:Petrovice, kdo:∃koncert, kdy:pondělí)",
            anchors=("Petrovicích → Petrovice",),
            point=(
                "TENHLE krok se zapíše — žádná otázka otevřená není. "
                "„v+Loc“ je místo a „v+Acc“ čas, a rozdíl nese PÁD, ne "
                "předložka"
            ),
        ),
        Step(
            text="Byl koncert v Plzni během týdne?",
            reading=sentence(
                w("Byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("koncert", "koncert", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Plzni", "Plzeň", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w("během", "během", "ADP", 6, "case", AdpType="Prep", Case="Gen"),
                w("týdne", "týden", "NOUN", 4, "obl", Animacy="Inan", Case="Gen", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="být(kde:Plzeň, kdo:∃koncert, kdy:týden)",
            answers="A",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Jedna otázka, která "
                "potřebuje OBA DRUHY ZAHRNUTÍ najednou: nikdo neřekl, že "
                "koncert byl v Plzni, ani že byl v týdnu — plyne to "
                "z faktu a ze DVOU různých zahrnutí, a důkaz cituje "
                "všechny tři zápisy. Ani jeden z nich by sám nestačil"
            ),
        ),
        Step(
            text="Byl koncert v Plzni v pondělí?",
            reading=sentence(
                w("Byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("koncert", "koncert", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Plzni", "Plzeň", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w("v", "v", "ADP", 6, "case", AdpType="Prep", Case="Acc"),
                w("pondělí", "pondělí", "NOUN", 4, "obl", Case="Acc", Gender="Neut", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="být(kde:Plzeň, kdo:∃koncert, kdy:pondělí)",
            answers="A",
            point=(
                "KONTROLA, ŽE SE TA DVĚ ZAHRNUTÍ NESLILA: tady stačí "
                "`contains` samo a důkaz `within` NECITUJE. Kdyby ho "
                "citoval, byl by to důkaz, který se veze"
            ),
        ),
    ),
    note=(
        "Desátý akceptační dialog. `contains` a `within` uměla čeština "
        "vyrobit od N‑2, ale ŽÁDNÁ DOMÉNA je nezapisovala — měřily se jen "
        "ručním během, takže kdyby to zítra někdo rozbil, nikdo by se to "
        "nedozvěděl. Doména zároveň drží B‑17: dva kroky, které NIC "
        "NEZAPÍŠOU, protože je otevřená otázka na konstrukci. Pořadí není "
        "libovolné — kdyby dialog vznikl PŘED tou opravou, ZAFIXOVAL by "
        "vadu, protože odpověď na relaci špatnou větev nikdy neprojde."
    ),
)


# --------------------------------------------------------------------------
# 11 · Naši psi — UZAVŘENÍ SVĚTA, jediné místo, kde absence dá „ne"
# --------------------------------------------------------------------------

CLOSURE = Dialogue(
    name="Naši psi",
    source="„Rex je pes. Alík je pes. … To jsou všichni psi. … Je Mourek pes?“",
    shapes=(
        ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),
        ("NOUN", "Sing", "Nom", "root", Operation.SELF),
        ("NOUN", "Plur", "Nom", "root", Operation.SELF),
    ),
    steps=(
        Step(
            text="Rex je pes.",
            reading=sentence(
                w("Rex", "Rex", "PROPN", 3, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", NameType="Oth", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("pes", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Rex, group:·pes)",
            writes="member(elem:Rex, group:·pes)",
            point="výčet, nad kterým se bude zavírat — první z dvou členů",
        ),
        Step(
            text="Alík je pes.",
            reading=sentence(
                w("Alík", "alík", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("pes", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·alík, group:·pes)",
            writes="member(elem:alík, group:·pes)",
            point="druhý člen. Uzavření je až tah — dva výroky samy o sobě nezavírají nic",
        ),
        Step(
            text="Mourek je kocour.",
            reading=sentence(
                w("Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("kocour", "kocour", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Mourek, group:·kocour)",
            writes="member(elem:Mourek, group:·kocour)",
            point=(
                "uzel MIMO výčet. Bez něj by se nebylo koho zeptat — a "
                "otázka na uzel, o kterém nikdo nic neřekl, měří něco "
                "jiného než uzavření"
            ),
        ),
        Step(
            text="Je Mourek pes?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Mourek", "Mourek", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("pes", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Mourek, group:·pes)",
            answers="U",
            point=(
                "OTEVŘENÝ SVĚT, PŘED prohlášením. Nikdo neřekl, že Mourek "
                "pes není, a to, že v seznamu není, o něm zatím "
                "NEROZHODUJE (I‑21). Tenhle krok je půlka měření: bez něj "
                "by se nedalo poznat, jestli `N` o dva kroky dál způsobilo "
                "prohlášení, nebo jestli tam bylo pořád"
            ),
        ),
        Step(
            text="To jsou všichni psi.",
            reading=sentence(
                w("To", "ten", "DET", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing", PronType="Dem"),
                w("jsou", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("všichni", "všechen", "DET", 4, "det", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur", PronType="Tot"),
                w("psi", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            asks=(
                "NEZAPÍŠE SE NIC a systém se ptá — a jako jediná otázka "
                "v systému upozorňuje na DŮSLEDEK, ne na neznalost: od "
                "prohlášení přestane na kohokoli mimo výčet odpovídat "
                "„nevím“ a začne odpovídat „ne“"
            ),
            limit=(
                "stopa se u téhle věty ptá i „na koho odkazuje To“ — "
                "v prezentační vazbě „to“ NEODKAZUJE na nic, je to podmět "
                "bez reference, takže je to otázka bez správné odpovědi "
                "(táž třída jako W‑20). Doména na ni neodpovídá a projde; "
                "zapsaná mez, ne v pořádku"
            ),
            point=(
                "shoda čísla tu NEPLATÍ a je to fakt o češtině: „To je "
                "pes.“ i „To jsou psi.“ jsou obojí správně, protože "
                "střední „to“ v prezentační vazbě nezastupuje počitatelný "
                "podmět. Filtr má úzkou výjimku, ne úlevu"
            ),
        ),
        Step(
            text="Ano, uzavři to.",
            declares_complete="pes",
            writes="complete(group:·pes)",
            point=(
                "TAH VLASTNÍHO DRUHU (`!∀`), a NIC SE JÍM NEUČÍ. Ostatní "
                "tahy učí tvar a jedna odpověď zavře celou třídu vět; "
                "tady by to bylo věcně špatně — že mluvčí dopočítal své "
                "psy, neopravňuje zavřít ani kočky, ani tytéž psy za "
                "měsíc. Uzavření světa není vlastnost jazyka, ale "
                "epistemický stav mluvčího"
            ),
        ),
        Step(
            text="Je Mourek pes?",
            reads="member(elem:·Mourek, group:·pes)",
            answers="N",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Táž otázka jako "
                "o tři kroky dřív dá teď `N` — a je to JEDINÉ místo "
                "v jádře, kde závěr plyne z ABSENCE. Důkaz proto cituje "
                "OBĚ půlky: prohlášení i VÝČET, nad kterým se zavíralo. "
                "Bez výčtu se závěr nedá zkontrolovat — čtenář nevidí, že "
                "dotazovaný v něm opravdu není"
            ),
        ),
        Step(
            text="Počkej, ještě nějací jsou.",
            revokes_complete="výčet nebyl hotový",
            point=(
                "PROHLÁŠENÍ JE DEKLARACE, NE TRVALÁ VLASTNOST SVĚTA. "
                "Uzavření se odvolává jako každý jiný výrok — a kdyby "
                "nešlo, byl by to jediný nevratný krok v systému"
            ),
        ),
        Step(
            text="Je Mourek pes?",
            reads="member(elem:·Mourek, group:·pes)",
            answers="U",
            point=(
                "ZPÁTKY NA `U`, a to je druhá půlka závěru domény. Kdyby "
                "tu zůstalo `N`, znamenalo by to, že se uzávěr někde "
                "materializoval do pevného bodu — přesně to, co § 5.1 "
                "zakazuje, a poznat by to nešlo jinak než tímhle krokem"
            ),
        ),
    ),
    note=(
        "Jedenáctý akceptační dialog. `complete` bylo do dneška JEDINÝ "
        "jádrový predikát, ke kterému čeština nevedla — měřilo se jen "
        "z formulí, tedy táž třída jako `before` před #59, `disjoint` před "
        "#64 a `same_as` před #66. Cena chyby je tu ale nejvyšší v celém "
        "systému: špatně zapsané uzavření vyrobí `N` tam, kde má být `U`, "
        "a to je nevědomost vydávaná za znalost. Proto se `complete` "
        "nedosadí nikdy, ani při jednoznačném tvaru, a proto tahle doména "
        "prochází celý kruh — otevřený svět, prohlášení, uzavřený svět, "
        "odvolání, zase otevřený."
    ),
)


# --------------------------------------------------------------------------
# 12 · Jan a Honza — POJMENOVÁNÍ, poslední jádrový predikát
# --------------------------------------------------------------------------

NAMING = Dialogue(
    name="Jan a Honza",
    source="„Jan je učitel. Jan se jmenuje taky Honza. … Je Honza učitel?“",
    shapes=(
        ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),
        ("PROPN", "Sing", "Nom", "obj", Operation.SELF),
        ("NOUN", "Sing", "Nom", "root", Operation.SELF),
    ),
    steps=(
        Step(
            text="Jan je učitel.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Jan, group:·učitel)",
            writes="member(elem:Jan, group:·učitel)",
            point="fakt o uzlu, na který se doména bude ptát JINÝM jménem",
        ),
        Step(
            text="Je Honza učitel?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Honza", "Honza", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Honza, group:·učitel)",
            answers="U",
            point=(
                "PŘED pojmenováním. „Honza“ je zatím CIZÍ uzel — kanonizace "
                "jmen ho s Janem neztotožní, protože nemá čím. Bez tohohle "
                "kroku by se nedalo poznat, jestli `A` o dva kroky dál "
                "způsobil zápis jména, nebo jestli tam bylo pořád"
            ),
        ),
        Step(
            text="Jan se jmenuje taky Honza.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("se", "se", "PRON", 3, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
                w("jmenuje", "jmenovat", "VERB", 0, "root", Aspect="Imp,Perf", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("taky", "taky", "PART", 5, "advmod:emph"),
                w("Honza", "Honza", "PROPN", 3, "obj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="name(of:Jan, value:Honza)",
            writes="name(of:Jan, value:Honza)",
            point=(
                "POSLEDNÍ JÁDROVÝ PREDIKÁT, KTERÝ SE NAUČIL PSÁT ČESKY. "
                "Generátor vyrobí DVĚ čtení, protože obě jména jsou "
                "v nominativu — strany rozhoduje DEPREL, ne pořadí: kdyby "
                "se braly podle pořadí, zapsalo by se jednou „Jan má "
                "přezdívku Honza“ a podruhé pravý opak. Konstrukce se "
                "DOSAZUJE, nezeptá se: `jmenovat se` je lexikálně "
                "o pojmenování a druhé čtení nemá (táž úvaha jako N‑2d)"
            ),
        ),
        Step(
            text="Je Honza učitel?",
            reads="member(elem:·Honza, group:·učitel)",
            answers="A",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Táž otázka jako "
                "o dva kroky dřív dá teď `A` — a důkaz cituje OBOJE: fakt "
                "o Janovi i VÝROK, kterým se „Honza“ na Jana váže. Bez té "
                "druhé citace by čtenář viděl odpověď na otázku o Honzovi "
                "doloženou faktem o Janovi a spojnici by nikde nenašel"
            ),
        ),
    ),
    note=(
        "Dvanáctý akceptační dialog a poslední jádrový predikát. `name` "
        "uměla dosud zapsat jen VNITŘNÍ cesta — rozdělení uzlu — takže se "
        "z jazyka nedal dostat alias, přestože alias je přesně to, kvůli "
        "čemu `name` v jádře je. Doména zároveň měří, že se citace "
        "nezastavuje na premisách důkazu: zakotvení není premisa, ale bez "
        "něj by se dotaz na tenhle uzel vůbec netrefil."
    ),
)


# --------------------------------------------------------------------------
# 13 · Jan a Plzeň — KONTEXT TEXTU, zájmeno odkazuje do předchozí věty
# --------------------------------------------------------------------------

DISCOURSE = Dialogue(
    name="Jan a Plzeň",
    source="„Jan je učitel. … On bydlí v Petrovicích. … Bydlí Jan v Plzni?“",
    shapes=(
        ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),
        ("PROPN", "Plur", "Nom", "nsubj", Operation.SELF),
        ("PROPN", "Plur", "Loc", "obl", Operation.SELF),
        ("PROPN", "Sing", "Loc", "obl", Operation.SELF),
        ("PROPN", "Sing", "Gen", "nmod", Operation.SELF),
        ("NOUN", "Sing", "Nom", "root", Operation.SELF),
        ("NOUN", "Sing", "Ins", "root", Operation.SELF),
    ),
    roles=(("v+Loc/Geo", "kde"),),
    steps=(
        Step(
            text="Jan je učitel.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Jan, group:·učitel)",
            writes="member(elem:Jan, group:·učitel)",
            point="věta, do které bude další věta ODKAZOVAT — kontext, ne jen fakt",
        ),
        Step(
            text="Ona bydlí v Praze.",
            reading=sentence(
                w("Ona", "on", "PRON", 2, "nsubj", Case="Nom", Gender="Fem", Number="Sing", Person="3", PronType="Prs"),
                w("bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            asks=(
                "KANDIDÁT, KTERÝ V PŘEDCHOZÍ VĚTĚ NENÍ, SE NENABÍDNE. "
                "„Ona“ je ženského rodu, v předchozí větě stojí jen Jan — "
                "systém proto nenabídne nikoho a řekne proč. Nabídnout "
                "uzel odjinud by znamenalo tvrdit, že text odkazuje tam, "
                "kde nic nestojí"
            ),
            point="krok, který NIC NEZAPÍŠE, a je to správně",
        ),
        Step(
            text="On bydlí v Petrovicích.",
            reading=sentence(
                w("On", "on", "PRON", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing", Person="3", PronType="Prs"),
                w("bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Petrovicích", "Petrovice", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            asks=(
                "NAVRHNE antecedent z předchozí věty a ZEPTÁ SE — i když "
                "je kandidát JEDINÝ a shoda rodu a čísla sedí. Shoda je "
                "vodítko struktury textu, ne důkaz: „trefil jsem týž "
                "uzel“ a „člověk řekl, že to je týž“ jsou dvě různé věci "
                "a celá M‑2 stojí na tom rozdílu"
            ),
            point=(
                "DRUHÝ krok, který nic nezapíše. Tichý default u identity "
                "je nejdražší chyba, jakou tenhle systém může udělat: uzly "
                "se tiše slijí nebo rozštěpí a nepozná to žádný test, "
                "ke kterému jazyk nevede"
            ),
        ),
        Step(
            text="Myslím Jana.",
            decides_reference=("kdo", "Jan"),
            reads="bydlet(kde:Petrovice, kdo:on)",
            writes="bydlet(kde:Petrovice, kdo:Jan)",
            point=(
                "ODPOVĚĎ JE TAH (`→=`) a teprve po ní se zapisuje — na "
                "TÝŽ uzel, o kterém byla řeč v první větě. Rozhodnutí leží "
                "v žurnálu, takže se `replay` neptá podruhé a nevyjde ani "
                "jinak, kdyby mezitím v bázi přibyl další kandidát"
            ),
        ),
        Step(
            text="Petrovice jsou součástí Plzně.",
            reading=sentence(
                w("Petrovice", "Petrovice", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Geo", Number="Plur"),
                w("jsou", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
                w("Plzně", "Plzeň", "PROPN", 3, "nmod", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            asks="tvar „být součástí“ je dvojznačný a ptá se (B‑17)",
            point="článek, bez kterého by závěr domény neplynul",
        ),
        Step(
            text="Je to místo uvnitř místa.",
            answers_relation_here=Operation.CONTAINS,
            writes="contains(part:Petrovice, whole:Plzeň)",
            point="`→⊆1` — per‑větná relace, tvar se neučí (N‑11)",
        ),
        Step(
            text="Bydlí Jan v Plzni?",
            reading=sentence(
                w("Bydlí", "bydlet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Jan", "Jan", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Plzni", "Plzeň", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="bydlet(kde:Plzeň, kdo:·Jan)",
            answers="A",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Nikdo neřekl, že Jan "
                "bydlí v Plzni — plyne to z faktu, který se do báze dostal "
                "PŘES ZÁJMENO, a ze zahrnutí míst. Důkaz cituje OBA "
                "zápisy, a ten první by bez rozhodnutí o odkazu vůbec "
                "nevznikl"
            ),
        ),
    ),
    note=(
        "Třináctý akceptační dialog a první, který potřebuje KONTEXT "
        "TEXTU. Sezení dosud znalo TAH, ne TEXT: každá věta se zakotvovala "
        "sama za sebe, protože etalon mluvil jmény. Souvislý psaný text "
        "ale odkazuje pořád, a bez paměti předchozí věty není zájmeno na "
        "co navázat. Je to nová INFORMACE, ne nová inference — nic se "
        "z ní neodvozuje, jen se z ní NABÍZEJÍ kandidáti. Předzpracování "
        "by tuhle mezeru zakrylo: čistič, který zájmena předem nahradí "
        "jmény, vyrobí text, jakému systém rozumí, a schová právě to, co "
        "se má naučit."
    ),
)


# --------------------------------------------------------------------------
# 14 · Jan se narodil — VĚTA BEZ PODMĚTU (český pro‑drop)
# --------------------------------------------------------------------------

PRODROP = Dialogue(
    name="Jan se narodil",
    source="„Jan je učitel. … Narodil se v Petrovicích. … Narodil se Jan v Plzni?“",
    shapes=(
        ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),
        ("PROPN", "Plur", "Nom", "nsubj", Operation.SELF),
        ("PROPN", "Plur", "Loc", "obl", Operation.SELF),
        ("PROPN", "Sing", "Loc", "obl", Operation.SELF),
        ("PROPN", "Sing", "Gen", "nmod", Operation.SELF),
        ("NOUN", "Sing", "Nom", "root", Operation.SELF),
        ("NOUN", "Sing", "Ins", "root", Operation.SELF),
    ),
    roles=(("v+Loc/Geo", "kde"),),
    steps=(
        Step(
            text="Jan je učitel.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Jan, group:·učitel)",
            writes="member(elem:Jan, group:·učitel)",
            point="jediná věta domény, která podmět VYSLOVÍ",
        ),
        Step(
            text="Narodila se v Praze.",
            reading=sentence(
                w("Narodila", "narodit", "VERB", 0, "root", Aspect="Perf", Gender="Fem,Neut", Number="Plur,Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("se", "se", "PRON", 1, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 1, "punct"),
            ),
            asks=(
                "ROD SE KONTROLUJE. „Narodila“ nese `Gender=Fem,Neut`, "
                "v předchozí větě stojí Jan v mužském rodě — průnik je "
                "prázdný, takže se NENABÍDNE NIKDO. Kdyby se rod "
                "nekontroloval, systém by tu Jana nabídl a člověk by "
                "odpověď jen odklepl"
            ),
            point=(
                "rys může nést VÍC hodnot („Fem,Neut“), protože tvar je "
                "pro obojí týž — porovnává se PRŮNIKEM, ne rovností. "
                "Rovnost by zahodila kandidáta, který se shodnout MŮŽE, "
                "a z vodítka by udělala filtr, který rozhoduje"
            ),
        ),
        Step(
            text="Narodil se v Petrovicích.",
            reading=sentence(
                w("Narodil", "narodit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("se", "se", "PRON", 1, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Petrovicích", "Petrovice", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w(".", ".", "PUNCT", 1, "punct"),
            ),
            asks=(
                "PODMĚT VE VĚTĚ NENÍ VŮBEC — ne že by byl zájmenem. "
                "Systém navrhne Jana z předchozí věty a ZEPTÁ SE; do "
                "textu se nepřidávají slova, která tam nejsou, takže "
                "zmínkou té role je sám PŘÍSUDEK: rod a číslo jsou na něm"
            ),
            point=(
                "DŘÍV SE TAHLE VĚTA ZAPSALA jako `narodit(kde:Petrovice)`, "
                "tedy jako fakt O NIKOM, a nic to neřeklo. To je horší "
                "vada než neumět pro‑drop: v encyklopedické próze by se "
                "do báze ukládaly dekapitované věty jedna za druhou"
            ),
        ),
        Step(
            text="Myslím Jana.",
            decides_reference=("kdo", "Jan"),
            writes="narodit(kde:Petrovice, kdo:Jan)",
            point=(
                "TÁŽ ODPOVĚĎ (`→=`) jako u zájmena, protože je to TÁŽ "
                "otázka: o kom to platí. Řešení má týž tvar, protože "
                "příčina je táž — sezení zná text, ne jen tah"
            ),
        ),
        Step(
            text="Petrovice jsou součástí Plzně.",
            reading=sentence(
                w("Petrovice", "Petrovice", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Geo", Number="Plur"),
                w("jsou", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Plur", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
                w("Plzně", "Plzeň", "PROPN", 3, "nmod", Case="Gen", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            asks="tvar „být součástí“ je dvojznačný a ptá se (B‑17)",
            point="článek, bez kterého by závěr domény neplynul",
        ),
        Step(
            text="Je to místo uvnitř místa.",
            answers_relation_here=Operation.CONTAINS,
            writes="contains(part:Petrovice, whole:Plzeň)",
            point="`→⊆1` — per‑větná relace, tvar se neučí (N‑11)",
        ),
        Step(
            text="Narodil se Jan v Plzni?",
            reading=sentence(
                w("Narodil", "narodit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("se", "se", "PRON", 1, "expl:pv", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
                w("Jan", "Jan", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("v", "v", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
                w("Plzni", "Plzeň", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="narodit(kde:Plzeň, kdo:·Jan)",
            answers="A",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Nikdo neřekl, že se "
                "Jan narodil v Plzni — plyne to z faktu, který se do báze "
                "dostal PŘES VĚTU BEZ PODMĚTU, a ze zahrnutí míst. Důkaz "
                "cituje OBA zápisy, a ten první by bez rozhodnutí o tom, "
                "o kom věta mluví, vůbec nevznikl"
            ),
        ),
    ),
    note=(
        "Čtrnáctý akceptační dialog a druhá polovina téže vrstvy jako "
        "třináctý. V přirozeném textu je věta bez podmětu ČASTĚJŠÍ NEŽ "
        "ZÁJMENO — životopisný odstavec je jí plný. Do tohohle kola se "
        "taková věta zapisovala BEZ PODMĚTU, tedy jako fakt o nikom, a "
        "nic to neřeklo; to je horší vada než neumět pro‑drop. Řešení má "
        "týž tvar jako u zájmena, protože příčina je táž: kandidát se "
        "navrhuje z předchozí zakotvené věty, nikdy nedosazuje, a rod "
        "a číslo na přísudku je VODÍTKO, NE DŮKAZ."
    ),
)


# --------------------------------------------------------------------------
# 15 · Chov a péče — GENITIVNÍ PŘÍVLASTEK jako druhý výrok vedle věty
# --------------------------------------------------------------------------

ATTRIBUTE = Dialogue(
    name="Chov a péče",
    source="„Chov zvířat je náročný. … Péče majitele je nutná.“",
    shapes=(
        ("NOUN", "Sing", "Nom", "nsubj", Operation.SELF),
        ("ADJ", "Sing", "Nom", "root", Operation.SELF),
    ),
    steps=(
        Step(
            text="Chov zvířat je náročný.",
            reading=sentence(
                w("Chov", "chov", "NOUN", 4, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w("zvířat", "zvíře", "NOUN", 1, "nmod", Case="Gen", Gender="Neut", Number="Plur"),
                w("je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("náročný", "náročný", "ADJ", 0, "root", Animacy="Inan", Case="Nom", Degree="Pos", Gender="Masc", Number="Sing", Polarity="Pos"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="být(co:·náročný, kdo:·chov)",
            writes="být(co:·náročný, kdo:·chov)",
            asks=(
                "VĚTA SE ZAPÍŠE A PŘESTO SE SYSTÉM PTÁ. Genitivní "
                "přívlastek není role slovesa — „zvířat“ visí jako `nmod` "
                "pod „chov“, tedy pod JMÉNEM, a predikace nese role "
                "PŘÍSUDKU. Větě proto nechybí predikát, chybí jí "
                "přívlastek, a blokovat kvůli němu zápis by bylo zadržet "
                "větu kvůli něčemu, co v ní vůbec není"
            ),
            point=(
                "DŘÍV SE TENHLE GENITIV HLÁSIL JAKO ZTRACENÝ ČLEN a věta "
                "se kvůli němu nezapsala. Ztracený člen je role, která "
                "vypadla; tohle je vztah dvou jmen uvnitř fráze"
            ),
        ),
        Step(
            text="Je to předmět toho děje.",
            names_attribute=("chov", "zvíře", "co"),
            writes="chov(co:∀zvíře)",
            point=(
                "DRUHÝ VÝROK VEDLE VĚTY, týž tvar jako `→'`. Věta se tím "
                "NEZAPISUJE ZNOVU — zapsala se, když se dočetla; kdyby "
                "tenhle tah šel přes `_settle`, ležel by v bázi týž výrok "
                "dvakrát"
            ),
        ),
        Step(
            text="Péče majitele je nutná.",
            reading=sentence(
                w("Péče", "péče", "NOUN", 4, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
                w("majitele", "majitel", "NOUN", 1, "nmod", Animacy="Anim", Case="Gen", Gender="Masc", Number="Sing"),
                w("je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("nutná", "nutný", "ADJ", 0, "root", Case="Nom", Degree="Pos", Gender="Fem", Number="Sing", Polarity="Pos"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="být(co:·nutný, kdo:·péče)",
            writes="být(co:·nutný, kdo:·péče)",
            asks=(
                "PTÁ SE ZNOVU, a je to důkaz, že se tvar NENAUČIL. Kdyby "
                "se učil, přečetl by tuhle větu podle předchozí odpovědi "
                "— tedy NARUBY"
            ),
            point=(
                "„chov zvířat“ a „péče majitele“ mají TÝŽ TVAR a OPAČNÝ "
                "SMĚR: zvířata se chovají, kdežto majitel pečuje. Význam "
                "genitivu je vlastnost VĚTY, ne tvaru"
            ),
        ),
        Step(
            text="Je to původce toho děje.",
            names_attribute=("péče", "majitel", "kdo"),
            writes="péče(kdo:∀majitel)",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Týž tvar dal JINOU "
                "ROLI — `kdo` proti `co` o dva kroky výš — a to je celý "
                "důvod, proč se tenhle tah nesmí nic učit"
            ),
        ),
    ),
    note=(
        "Patnáctý akceptační dialog. Genitivní přívlastek nese pět měřením "
        "doložených významů (předmět děje, původce děje, nositel "
        "vlastnosti, část z celku, míra a druh) a liší se PRÁVĚ TÍM, "
        "kterou roli genitiv v reifikovaném vztahu plní. Menu proto není "
        "nový druh rozhodnutí — je to otázka na jméno role, kterou systém "
        "už uměl."
    ),
    limit=(
        "CO TAHLE DOMÉNA UKÁZAT NEUMÍ: otázku, která by prošla OD VĚTY "
        "K PŘÍVLASTKU. Reifikovaný fakt se ZÁMĚRNĚ neřetězí — nevytváří "
        "uzávěr — takže „Je náročné to, co se týká zvířat?“ by potřebovala "
        "můstkové pravidlo, a to je jiná schopnost. Doména proto končí na "
        "JEDNOM výroku: dokládá, že přívlastek se zapíše a systém se na "
        "něj zeptá, ne že se dá s větou spojit. Svázat obojí by znamenalo "
        "měřit dvě věci naráz a přivést partitivní uzávěr zadními vrátky."
    ),
)


# --------------------------------------------------------------------------
# 16 · Proč odjel — VEDLEJŠÍ VĚTA jako role hlavní predikace
# --------------------------------------------------------------------------

SUBORDINATE = Dialogue(
    name="Proč odjel",
    source="„Petr odjel, protože pršelo. … Jan odjel, protože sněžilo.“",
    shapes=(("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),),
    steps=(
        Step(
            text="Petr odjel, protože pršelo.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("odjel", "odjet", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w(",", ",", "PUNCT", 5, "punct"),
                w("protože", "protože", "SCONJ", 5, "mark"),
                w("pršelo", "pršet", "VERB", 2, "advcl", Aspect="Imp", Gender="Neut", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="odjet(advcl:protože:∃pršet, kdo:·Petr)",
            asks=(
                "VEDLEJŠÍ VĚTA SE PŘESTALA ZTRÁCET: je z ní ROLE hlavní "
                "predikace, jejímž fillerem je DĚJ. Jméno té role ale "
                "systém zatím nezná, takže zůstane povrchové "
                "(`advcl:protože`) a ZEPTÁ SE — dosadit ho z pořadí slov "
                "by znamenalo vymyslet si význam (INV‑11)"
            ),
            point=(
                "A NEZAPÍŠE SE *(B‑19)*. Dřív se „pršelo“ hlásilo jako "
                "ZTRACENÝ ČLEN a zápis blokovalo; patro z něj udělalo "
                "roli, ale tu zábranu mu zapomnělo dát — a odpověď `→@` "
                "pak větu zapsala PODRUHÉ, jednou s povrchovým jménem "
                "a podruhé s naučeným. Ten první výrok by nikdo neodvolal"
            ),
        ),
        Step(
            text="Je to důvod.",
            names_role=("advcl:protože", "proč"),
            reads="odjet(kdo:·Petr, proč:∃pršet)",
            writes="odjet(kdo:Petr, proč:∃pršet)",
            point=(
                "ODPOVĚĎ JE TAH `→@` a UČÍ TVAR — tady je rozdíl proti "
                "genitivnímu přívlastku, na kterém záleží: tam byl směr "
                "vlastností VĚTY („chov zvířat“ × „péče majitele“), kdežto "
                "spojka je v ROZBORU jako `mark`, takže odpověď je v tvaru. "
                "Tenhle tah taky RE-ČTE, a proto potřebuje `replay` "
                "výchozí lexikon (B‑20)"
            ),
        ),
        Step(
            text="Jan odjel, protože sněžilo.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("odjel", "odjet", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w(",", ",", "PUNCT", 5, "punct"),
                w("protože", "protože", "SCONJ", 5, "mark"),
                w("sněžilo", "sněžit", "VERB", 2, "advcl", Aspect="Imp", Gender="Neut", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="odjet(kdo:·Jan, proč:∃sněžit)",
            writes="odjet(kdo:Jan, proč:∃sněžit)",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA. Táž spojka podruhé "
                "se UŽ NEPTÁ — jedna odpověď zavřela celou třídu vět. "
                "Kdyby se tvar neučil, byl by z dialogu výslech"
            ),
        ),
        Step(
            text="Je jasné, že Jan přišel.",
            reading=sentence(
                w("Je", "být", "AUX", 2, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("jasné", "jasný", "ADJ", 0, "root", Case="Nom", Degree="Pos", Gender="Neut", Number="Sing", Polarity="Pos"),
                w(",", ",", "PUNCT", 6, "punct"),
                w("že", "že", "SCONJ", 6, "mark"),
                w("Jan", "Jan", "PROPN", 6, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("přišel", "přijít", "VERB", 2, "csubj", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            asks=(
                "PODMĚTEM JE CELÁ VĚTA VEDLEJŠÍ (`csubj`) a systém to "
                "ŘEKNE: netvrdí, že věta podmět nemá, ani nemlčí — říká, "
                "že ho dosadit zatím neumí. Rozdíl mezi „neřečeno“ "
                "a „řečeno, neumím“ (B‑18)"
            ),
            point=(
                "A NEZAPÍŠE SE, dokud ta vedlejší věta nemá roli *(W‑50)*. "
                "Dnes to drží druhá zeď — pro vedlejší větu role není, "
                "takže se ohlásí jako ZAHOZENÁ — a tenhle krok to DOKLÁDÁ. "
                "Kdyby jí někdo roli dal, aniž z ní udělá podmět, zapsala "
                "by se věta bez podmětu a nic by to neřeklo"
            ),
        ),
    ),
    note=(
        "Šestnáctý akceptační dialog. Vedlejší věta se spojkou je "
        "OKOLNOST hlavního děje, tedy jeho role, a jméno té role nese "
        "SPOJKA. Doména drží tři věci naráz: že se tvar UČÍ (druhá věta "
        "se neptá), že se věta NEZAPÍŠE dřív, než role dostane jméno "
        "(B‑19), a že věta s VĚTNÝM PODMĚTEM se nezapíše, dokud ta "
        "vedlejší věta nemá roli (W‑50)."
    ),
    limit=(
        "CO TAHLE DOMÉNA NEBERE: `advcl:pred`. Je to DOPLNĚK — „ukázalo "
        "se JAKO snižující“ — a ne okolnost: neodpovídá na proč ani kdy, "
        "ale na to, ČÍM se ta věc ukázala být. Do okolnostní role tedy "
        "nepatří a sémanticky je blíž `xcomp`, který se skládá do "
        "přísudku. V měřeném korpusu je ho 30 výskytů proti 21 holým "
        "`advcl`, takže to není okrajová výjimka — a právě proto se "
        "vylučuje VÝSLOVNĚ, ne řetězcovou shodou. Hranice bez zapsaného "
        "důvodu se čte jako opomenutí."
    ),
)


# --------------------------------------------------------------------------
# 17 · Dva Karlové — VÍCESLOVNÉ JMÉNO je jeden uzel
# --------------------------------------------------------------------------

FULL_NAME = Dialogue(
    name="Dva Karlové",
    source="„Karel Čapek byl spisovatel. … Byl Karel Poláček spisovatel?“",
    shapes=(
        ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF),
        ("NOUN", "Sing", "Nom", "root", Operation.SELF),
    ),
    steps=(
        Step(
            text="Karel Čapek byl spisovatel.",
            reading=sentence(
                w("Karel", "Karel", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Čapek", "Čapek", "PROPN", 1, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("spisovatel", "spisovatel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="member(elem:·Karel_Čapek, group:·spisovatel)",
            writes="member(elem:Karel_Čapek, group:·spisovatel)",
            point=(
                "PŘÍJMENÍ JE V UZLU, ne ztracené. Dřív se tahle věta "
                "zapsala o uzlu `Karel` a „Čapek“ se ohlásil jako "
                "ZAHOZENÝ — jenže to nebyla ztráta členu, byl to ZÁPIS "
                "O JINÉM UZLU"
            ),
        ),
        Step(
            text="Byl Karel Čapek spisovatel?",
            reading=sentence(
                w("Byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Karel", "Karel", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Čapek", "Čapek", "PROPN", 2, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("spisovatel", "spisovatel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="member(elem:·Karel_Čapek, group:·spisovatel)",
            answers="A",
            point=(
                "celé jméno se trefí na TÝŽ uzel — složení běží "
                "v `generate`, tedy JEDNOU PRO VŠECHNY POZICE, takže "
                "podmět oznamovací věty a podmět otázky míří na totéž"
            ),
        ),
        Step(
            text="Byl Karel Poláček spisovatel?",
            reading=sentence(
                w("Byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Karel", "Karel", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Poláček", "Poláček", "PROPN", 2, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("spisovatel", "spisovatel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="member(elem:·Karel_Poláček, group:·spisovatel)",
            answers="U",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA, a je to ta NEJDRAŽŠÍ "
                "půlka celé vady: o Poláčkovi nikdo nic neřekl, takže `U`. "
                "Dokud se příjmení zahazovalo, dala tahle otázka `A` — oba "
                "Karlové splynuli v jeden uzel a nepoznalo by se to, "
                "protože odpověď by vypadala jako doložený fakt"
            ),
        ),
    ),
    note=(
        "Sedmnáctý akceptační dialog. „Josef Hora“ není hlava "
        "s přívlastkem, je to JEDNO JMÉNO — UD to říká hranou `flat`. "
        "Pořadí kola určilo KUMULATIVNÍ POKRYTÍ, ne pořadí v seznamu: "
        "rodina víceslovných jmen přidávala k rodině A šest vět, kdežto "
        "zbytek vnořených vět jen dvě."
    ),
    limit=(
        "CO SE TÍM NEŘEŠÍ: `flat` pod OBECNÝM jménem. „město Praha“ není "
        "víceslovné jméno, ale seznam nebo apozice k obecnému jménu, a to "
        "je jiná operace — složit to do lemmatu by vyrobilo třídu "
        "`město_Praha`, která není ani město, ani Praha. Stráž je proto "
        "úzká na `PROPN` a je na to test."
    ),
)


# --------------------------------------------------------------------------
# 18 · Básník Josef Hora — JMÉNO POD TITULEM a kvantifikátor, který po něm zbyl
# --------------------------------------------------------------------------

TITLED_NAME = Dialogue(
    name="Básník Josef Hora",
    source="„Nad hrobem promluvil básník Josef Hora. … Promluvil básník?“",
    shapes=(
        PROPN_SUBJ,
        NOUN_SUBJ_SG,
        ("NOUN", "Sing", "Ins", "obl", Operation.EXISTS),
        ("PROPN", "Plur", "Loc", "obl", Operation.SELF),
    ),
    # Rozhodnutí člověka, ne vlastnost češtiny — týž důvod jako u `v`+Loc
    # v Petrovicích: „nad hrobem“ je místo, „nad ránem“ je čas.
    roles=(("nad+Ins", "kde"), ("v+Loc/Geo", "kde")),
    steps=(
        Step(
            text="Nad hrobem promluvil básník Josef Hora.",
            reading=sentence(
                w("Nad", "nad", "ADP", 2, "case", AdpType="Prep", Case="Ins"),
                w("hrobem", "hrob", "NOUN", 3, "obl", Animacy="Inan", Case="Ins", Gender="Masc", Number="Sing"),
                w("promluvil", "promluvit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("básník", "básník", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("Josef", "Josef", "PROPN", 4, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Hora", "Hora", "PROPN", 4, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="promluvit(kde:hrob, kdo:·Josef_Hora)",
            anchors=("básník Josef Hora → Josef_Hora (založen)",),
            writes="promluvit(kde:hrob, kdo:Josef_Hora)",
            # VĚTA SE ZAPÍŠE A PŘESTO SE PTÁ, a není to rozpor: co se
            # zapisuje, je predikace, a co se ptá, je výrok VEDLE ní
            # (W‑55). Doména 19 na tom stojí celá.
            asks="básník Josef Hora",
            point=(
                "ZMÍNKA JE ČLOVĚK, NE TITUL. Dokud jméno padalo, četla se "
                "tahle věta jako `promluvit(kdo:∀básník)` — o VŠECH "
                "BÁSNÍCÍCH. Jméno nespadlo jen tak: spadlo a NA JEHO MÍSTĚ "
                "ZŮSTAL KVANTIFIKÁTOR, který tam nepatří. „básník“ přitom "
                "nemizí — je v `form`, takže je v přepisu vidět, o čí "
                "titul šlo"
            ),
        ),
        Step(
            text="Promluvil Josef Hora?",
            reading=sentence(
                w("Promluvil", "promluvit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Josef", "Josef", "PROPN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Hora", "Hora", "PROPN", 2, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="promluvit(kdo:·Josef_Hora)",
            anchors=("Josef Hora → Josef_Hora (kanonicky; týž uzel, o kterém už řeč byla)",),
            answers="A",
            point=(
                "TÝŽ UZEL bez titulu — a to je půlka opravy, kterou by "
                "samotné složení lemmatu nedalo: kdyby ze zmínky zůstal "
                "`upos` hlavy, byl by v bázi `∀Josef_Hora`, tvrzení o "
                "VŠECH, kdo se tak jmenují, a tahle otázka by dala `U`"
            ),
        ),
        Step(
            text="Promluvil básník?",
            reading=sentence(
                w("Promluvil", "promluvit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("básník", "básník", "NOUN", 1, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 1, "punct"),
            ),
            reads="promluvit(kdo:∀básník)",
            answers="U",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA, a je to ta NEJDRAŽŠÍ "
                "půlka celé vady: o VŠECH BÁSNÍCÍCH nikdo nic neřekl, "
                "takže `U`. Dokud se jméno zahazovalo, dala tahle otázka "
                "`A` — a vypadala by jako doložený fakt, doložený větou, "
                "která mluvila o jednom člověku"
            ),
        ),
        Step(
            text="Město Praha leží v Čechách.",
            reading=sentence(
                w("Město", "město", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
                w("Praha", "Praha", "PROPN", 1, "nmod", Case="Nom", Gender="Fem", NameType="Geo", Number="Sing"),
                w("leží", "ležet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("v", "v", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
                w("Čechách", "Čechy", "PROPN", 3, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="ležet(kde:Čechy, kdo:∀město)",
            asks="Praha",
            point=(
                "PROTIPŘÍKLAD PŘÍMO V SADĚ, a rozbor ho rozlišuje sám: "
                "„Praha“ visí pod „Město“ jako `nmod`, ne `flat`. `flat` "
                "znamená JEDNU ZMÍNKU (titul a jméno míří na jednoho "
                "člověka), `nmod` je samostatný přívlastek — takže tahle "
                "věta se opravou NEMĚNÍ a dál se ptá, jakou roli „Praha“ "
                "hraje. Kdyby se změnila, byla by to tichá vedlejší škoda"
            ),
            limit=(
                "Krok je ZÁMĚRNĚ POSLEDNÍ: nechává otevřenou otázku po "
                "roli a další věta by se četla jako odpověď na ni"
            ),
        ),
    ),
    note=(
        "Osmnáctý akceptační dialog, a je o TŘECH VĚCECH NAJEDNOU, které "
        "vypadají jako jedna. Že je jméno v uzlu, je jen první: druhá je, "
        "že se titul NESKLÁDÁ (`básník_Josef_Hora` by byla třída, která "
        "není ani básník, ani Hora, přesně jako `město_Praha`), a třetí, "
        "že se s identitou musí přesunout i KVANTIFIKÁTOR. Samotné složení "
        "lemmatu opravu jen předstírá: uzel by se jmenoval správně a věta "
        "by pořád tvrdila něco o všech."
    ),
    limit=(
        "CO SE TÍM NEŘEŠÍ: `nmod` pod obecným jménem — „Město Praha“. "
        "Rozbor ho dává jinou hranou, takže se opravou nemění (poslední "
        "krok), ale co ta hrana znamená, se tím nerozhodlo. Systém se dál "
        "ptá a je to správně: „město Praha“ je apozice, kdežto „ulice "
        "Karla Čapka“ je přívlastek o někom úplně jiném."
    ),
)


# --------------------------------------------------------------------------
# 19 · Co tvrdí titul — DRUHÝ VÝROK, který se nabídne a nezapíše sám
# --------------------------------------------------------------------------

TITLE_CLAIM = Dialogue(
    name="Co tvrdí titul",
    source="„Nad hrobem promluvil básník Josef Hora. … Prezident Masaryk "
    "zemřel.“",
    shapes=(
        PROPN_SUBJ,
        NOUN_SUBJ_SG,
        NOUN_ROOT,
        ("NOUN", "Sing", "Ins", "obl", Operation.EXISTS),
        ("PROPN", "Plur", "Loc", "obl", Operation.SELF),
    ),
    roles=(("nad+Ins", "kde"), ("v+Loc/Geo", "kde")),
    steps=(
        Step(
            text="Nad hrobem promluvil básník Josef Hora.",
            reading=sentence(
                w("Nad", "nad", "ADP", 2, "case", AdpType="Prep", Case="Ins"),
                w("hrobem", "hrob", "NOUN", 3, "obl", Animacy="Inan", Case="Ins", Gender="Masc", Number="Sing"),
                w("promluvil", "promluvit", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("básník", "básník", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("Josef", "Josef", "PROPN", 4, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Hora", "Hora", "PROPN", 4, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="promluvit(kde:hrob, kdo:·Josef_Hora)",
            writes="promluvit(kde:hrob, kdo:Josef_Hora)",
            asks="básník Josef Hora",
            point=(
                "VĚTA TVRDÍ DVĚ VĚCI — že promluvil a že je básník. "
                "Zapíše se jedna a druhá se OHLÁSÍ. Nezapsat ji je "
                "rozhodnutí, ne opomenutí; neohlásit ji bylo opomenutí"
            ),
        ),
        Step(
            text="Je Josef Hora básník?",
            reading=sentence(
                w("Je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Josef", "Josef", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Hora", "Hora", "PROPN", 2, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("básník", "básník", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="member(elem:·Josef_Hora, group:·básník)",
            answers="U",
            point=(
                "`U` JE POŘÁD SPRÁVNĚ — nikdo to nepotvrdil, takže se to "
                "netvrdí. Co se změnilo, je DŮVOD: bylo tu „nikdo to "
                "neřekl“, a to byla nepravda o vlastním vstupu systému. "
                "Verdikt se tím nezlepšil ani nezhoršil; přestal lhát"
            ),
        ),
        Step(
            text="Ano, Josef Hora byl básník.",
            confirms_title=("Josef_Hora", "básník", "povolání"),
            writes="member(elem:Josef_Hora, group:·básník)",
            point=(
                "TAH, NE VĚTA. Věta sama se zapsala už při čtení; tenhle "
                "tah přidává výrok, který v ní stál vedle predikace — týž "
                "tvar jako `→@1` u genitivního přívlastku"
            ),
        ),
        Step(
            text="Je Josef Hora básník?",
            reading=sentence(
                w("Je", "být", "AUX", 4, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Josef", "Josef", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("Hora", "Hora", "PROPN", 2, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("básník", "básník", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="member(elem:·Josef_Hora, group:·básník)",
            answers="A",
            point="KLADNÝ PŘÍPAD UZAVŘEN — a doložený tím tahem, ne tvarem",
        ),
        Step(
            text="Prezident Masaryk zemřel.",
            reading=sentence(
                w("Prezident", "prezident", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("Masaryk", "Masaryk", "PROPN", 1, "flat", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("zemřel", "zemřít", "VERB", 0, "root", Aspect="Perf", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="zemřít(kdo:·Masaryk)",
            writes="zemřít(kdo:Masaryk)",
            asks="prezident Masaryk",
            point=(
                "SPORNÝ PŘÍPAD, a je vidět, jak se s ním naloží: TÝŽ TVAR "
                "jako u básníka, ale „prezident“ je úřad DRŽENÝ V ČASE — "
                "Masaryk zemřel v roce 1937. Systém to proto NEZAPÍŠE a "
                "ohlásí to; čas jádro neumí, a tvrdit bezčasé členství "
                "tam, kde jazyk mluví o období, by byl doložený nesmysl"
            ),
        ),
        Step(
            text="Byl to úřad, ne povolání.",
            confirms_title=("Masaryk", "prezident", "úřad"),
            refuses="úřad platí v čase a jádro čas neumí",
            point=(
                "POTVRZENÍ, KTERÉ NEZAPÍŠE. Člověk řekl, čím ten titul "
                "je — a právě proto se nic nezapsalo: bezčasé "
                "`member(Masaryk, prezident)` by platilo ŠÍŘ, než co ta "
                "věta říká. Odkliknout „ano“ nestačí a systém se na "
                "„ano/ne“ ani neptá; ptá se na DRUH, protože z rozboru "
                "se povolání od úřadu rozeznat nedá"
            ),
            limit=(
                "Čas by to spravil, jenže V KORPUSU ŽÁDNÝ POUŽITELNÝ "
                "NENÍ: ze 39 zmínek titulu visí čas na titulu u čtyř a "
                "všechny čtyři jsou ŽIVOTNÍ DATA v závorce (1902–1968), "
                "ne doba držení funkce; u úřadů je to nula. Není to tedy "
                "úloha o čase v jádře — nemá se co zapsat"
            ),
        ),
        Step(
            text="Je Masaryk prezident?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("Masaryk", "Masaryk", "PROPN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("prezident", "prezident", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="member(elem:·Masaryk, group:·prezident)",
            answers="U",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA: sporný titul zůstane "
                "`U`, dokud ho člověk nepotvrdí. Kdyby se zapisoval ze "
                "tvaru, ležel by tu `A` — a bylo by to doložené tvrzení, "
                "že Masaryk je prezident"
            ),
            limit=(
                "Systém NEVÍ, že „prezident“ je úřad a „básník“ povolání. "
                "Nerozlišuje je — proto se ptá na OBOJÍ. Že se sporný "
                "případ nezapíše, není chytrost jádra, je to důsledek "
                "toho, že se nezapíše ŽÁDNÝ"
            ),
        ),
        Step(
            text="Město Praha leží v Čechách.",
            reading=sentence(
                w("Město", "město", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
                w("Praha", "Praha", "PROPN", 1, "nmod", Case="Nom", Gender="Fem", NameType="Geo", Number="Sing"),
                w("leží", "ležet", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("v", "v", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
                w("Čechách", "Čechy", "PROPN", 3, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Plur"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="ležet(kde:Čechy, kdo:∀město)",
            asks="Praha",
            point=(
                "ZÁPORNÝ PŘÍPAD: `nmod`, ne `flat` — tudy žádné tvrzení "
                "nevzniká. Ptá se se na roli „Prahy“, tedy na TOTÉŽ co "
                "před W‑55; nabídka členství tu není žádná"
            ),
            limit=(
                "Krok je ZÁMĚRNĚ POSLEDNÍ: nechává otevřenou otázku po "
                "roli a další věta by se četla jako odpověď na ni"
            ),
        ),
    ),
    note=(
        "Devatenáctý akceptační dialog. Za jednou větou se schovává "
        "OBECNÁ SCHOPNOST ČTENÍ: syntaktická hlava není referent a "
        "přívlastek v apozici nese PREDIKACI o něm. Je to 32 vět z 238 "
        "měřeného korpusu, tedy běžná encyklopedická próza. Rozhodnutí "
        "znělo NABÍDNOUT, ne zapsat, a stojí na měření, ne na opatrnosti: "
        "ze 71 zmínek je 29 povolání, 24 úřad držený v čase a 18 "
        "příbuzenství — TÝŽ TVAR a tři různá tvrzení. Kdyby se zapisovalo "
        "ze tvaru, byly by dvě třetiny zápisů buď bezčasé o něčem "
        "časovém, nebo neúplné o vztahu, a ležely by v bázi jako "
        "doložený fakt."
    ),
    limit=(
        "CO SE TÍM NEŘEŠÍ: čas. „prezident Masaryk“ se nezapíše proto, že "
        "se nezapíše nic, ne proto, že by jádro poznalo úřad od povolání. "
        "Ta rodina zůstává otevřená a nabídka ji jen zviditelňuje — "
        "člověk, který potvrdí „Masaryk je prezident“, zapíše bezčasé "
        "tvrzení a systém ho před tím jen VARUJE, nezabrání mu."
    ),
)


# --------------------------------------------------------------------------
# 20 · Trpný rod — podmět, který nic nedělá
# --------------------------------------------------------------------------

PASSIVE = Dialogue(
    name="Trpný rod",
    source="„Úmysly byly popsány. … Kolekce se označuje mnohovesmír.“",
    shapes=(
        ("NOUN", "Plur", "Nom", "nsubj:pass", Operation.FOR_ALL),
        ("NOUN", "Sing", "Nom", "nsubj:pass", Operation.SELF),
        ("NOUN", "Sing", "Nom", "obj", Operation.SELF),
        ("PROPN", "Sing", "Loc", "obl", Operation.SELF),
    ),
    roles=(("na+Loc/Geo", "kde"),),
    steps=(
        Step(
            text="Úmysly byly popsány.",
            reading=sentence(
                w("Úmysly", "úmysl", "NOUN", 3, "nsubj:pass", Animacy="Inan", Case="Nom", Gender="Masc", Number="Plur"),
                w("byly", "být", "AUX", 3, "aux:pass", Animacy="Inan", Aspect="Imp", Gender="Fem,Masc", Number="Plur", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("popsány", "popsaný", "ADJ", 0, "root", Animacy="Inan", Aspect="Perf", Degree="Pos", Gender="Fem,Masc", Number="Plur", Polarity="Pos", Variant="Short", VerbForm="Part", Voice="Pass"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="popsaný(co:∀úmysl)",
            writes="popsaný(co:∀úmysl)",
            point=(
                "PODMĚT, KTERÝ NIC NEDĚLÁ. „Úmysly“ nic nepopisují — jsou "
                "to ty POPISOVANÉ, tedy `co`. Neplyne to z naučeného "
                "vzoru, ale z PODTYPU `:pass`, který STOJÍ V ROZBORU; "
                "ptát se „co znamená role nsubj:pass“ znamenalo ptát se "
                "na něco, co rozbor právě řekl, a byla to TŘETÍ "
                "NEJČASTĚJŠÍ otázka korpusu"
            ),
        ),
        Step(
            text="Byly úmysly popsány?",
            reading=sentence(
                w("Byly", "být", "AUX", 3, "aux:pass", Animacy="Inan", Aspect="Imp", Gender="Fem,Masc", Number="Plur", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("úmysly", "úmysl", "NOUN", 3, "nsubj:pass", Animacy="Inan", Case="Nom", Gender="Masc", Number="Plur"),
                w("popsány", "popsaný", "ADJ", 0, "root", Animacy="Inan", Aspect="Perf", Degree="Pos", Gender="Fem,Masc", Number="Plur", Polarity="Pos", Variant="Short", VerbForm="Part", Voice="Pass"),
                w("?", "?", "PUNCT", 3, "punct"),
            ),
            reads="popsaný(co:∀úmysl)",
            answers="A",
            point=(
                "OTÁZKA SE TREFÍ NA TÝŽ VÝROK — mapování běží v patře, "
                "tedy JEDNOU PRO VĚTU I PRO DOTAZ. Kdyby se dosazovalo "
                "jen u oznamovací věty, otázka by se ptala na jinou roli "
                "a odpověď by byla `U` u něčeho, co v bázi leží"
            ),
        ),
        Step(
            text="Kolekce se označuje mnohovesmír.",
            reading=sentence(
                w("Kolekce", "kolekce", "NOUN", 3, "nsubj:pass", Case="Nom", Gender="Fem", Number="Sing"),
                w("se", "se", "PRON", 3, "expl:pass", Case="Acc", PronType="Prs", Reflex="Yes", Variant="Short"),
                w("označuje", "označovat", "VERB", 0, "root", Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos", Tense="Pres", VerbForm="Fin", Voice="Act"),
                w("mnohovesmír", "mnohovesmír", "NOUN", 3, "obj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
                w(".", ".", "PUNCT", 3, "punct"),
            ),
            reads="označovat(co:·mnohovesmír, nsubj:pass:·kolekce)",
            asks="nsubj:pass",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA: obě strany jsou "
                "VYSLOVENÉ a systém se ZEPTÁ, nepřepíše. Dosadit `co` "
                "z `:pass` by znamenalo zahodit člen, který ve větě "
                "stojí — a poznat by to nešlo, protože obě jsou `co`. "
                "Změřeno: v korpusu je to 1 věta z 19, zbylých 18 má `co` "
                "volné"
            ),
        ),
        Step(
            text="Byl pohřben na Vyšehradě.",
            reading=sentence(
                w("Byl", "být", "AUX", 2, "aux:pass", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("pohřben", "pohřbený", "ADJ", 0, "root", Aspect="Perf", Degree="Pos", Gender="Masc", Number="Sing", Polarity="Pos", Variant="Short", VerbForm="Part", Voice="Pass"),
                w("na", "na", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Vyšehradě", "Vyšehrad", "PROPN", 2, "obl", Animacy="Inan", Case="Loc", Gender="Masc", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 2, "punct"),
            ),
            reads="pohřbený(kde:Vyšehrad, kdo:pohřbený)",
            asks="podmět",
            point=(
                "PROTIPŘÍKLAD PROTI REGRESI W‑48: trpná věta BEZ "
                "vysloveného podmětu se dál ptá, o KOM to platí. Patro "
                "trpného rodu se jí nedotýká — nemá co přejmenovat, "
                "`nsubj:pass` v ní není"
            ),
            limit=(
                "Krok je ZÁMĚRNĚ POSLEDNÍ: nechává otevřenou otázku po "
                "podmětu a další věta by se četla jako odpověď na ni"
            ),
        ),
    ),
    note=(
        "Dvacátý akceptační dialog. `nsubj:pass` byl TŘETÍ NEJČASTĚJŠÍ "
        "tvar, na který se systém ptal „co znamená“ (19 výskytů z 250) — "
        "a přitom to nikdy nebyla otázka o významu: podtyp `:pass` je "
        "V ROZBORU a říká, že podmět té věty NENÍ konatel. Vlastní jméno "
        "té role bylo ZAPSANÉ ROZHODNUTÍ (I‑2, INV‑11), ne vada; tohle "
        "patro ten důvod neruší, jen dosazuje OPAČNOU stranu, tu, kterou "
        "`:pass` doopravdy říká."
    ),
    limit=(
        "CO SE TÍM NEŘEŠÍ: AGENS. „Auto bylo koupeno Filipem.“ — kdo to "
        "udělal, stojí v instrumentálu a rolí se nestává. V korpusu má "
        "instrumentál pod přísudkem 2 z 19 trpných vět, takže to není "
        "okrajové ani časté; je to vlastní rodina a nemíchá se sem."
    ),
)


# --------------------------------------------------------------------------
# 21 · Kde a kdy — týž tvar, dva různé signály z rozboru
# --------------------------------------------------------------------------

SIGNAL = Dialogue(
    name="Kde a kdy",
    source="„Petr byl v roce 1935 v Praze.“",
    shapes=(PROPN_SUBJ, ("NOUN", "Sing", "Loc", "root", Operation.SELF),
            ("PROPN", "Sing", "Loc", "obl", Operation.SELF),
            ("PROPN", "Sing", "Loc", "root", Operation.SELF)),
    roles=(("v+Loc/Geo", "kde"), ("v+Loc/rok", "kdy")),
    steps=(
        Step(
            text="Petr byl v roce 1935 v Praze.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("roce", "rok", "NOUN", 0, "root", Animacy="Inan", Case="Loc", Gender="Masc", Number="Sing"),
                w("1935", "1935", "NUM", 4, "nummod", NumForm="Digit", NumType="Card"),
                w("v", "v", "ADP", 7, "case", AdpType="Prep", Case="Loc"),
                w("Praze", "Praha", "PROPN", 4, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="být(kde:Praha, kdo:·Petr, kdy:rok)",
            asks="1935",
            point=(
                "MÍSTO A ČAS V JEDNÉ VĚTĚ POD TOUŽ PŘEDLOŽKOU. Dokud byl "
                "tvar jeden (`v+Loc`), byla tahle věta NEČITELNÁ: dva "
                "členy by dostaly totéž jméno role a čtení s duplicitou "
                "se nesmí vyrobit. Rozdělil je SIGNÁL Z ROZBORU — "
                "`NameType=Geo` na „Praze“ a letopočet pod „roce“ — ne "
                "seznam slov"
            ),
            limit=(
                "VĚTA SE NEZAPÍŠE, a není to kvůli rolím: „1935“ visí "
                "jako `nummod` pod „roce“ a rolí se nestává, takže se "
                "hlásí jako ztracený člen. Je to PŘEDCHOZÍ mez, kterou "
                "tahle změna nezvětšila ani nezmenšila — číslovka jako "
                "součást časového údaje je vlastní rodina"
            ),
        ),
        Step(
            text="Petr byl v Praze.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Praze", "Praha", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w(".", ".", "PUNCT", 4, "punct"),
            ),
            reads="být(kde:Praha, kdo:·Petr)",
            writes="být(kde:Praha, kdo:Petr)",
            point=(
                "TÝŽ SIGNÁL DOJDE AŽ DO BÁZE. Bez tohohle kroku by "
                "doména ukazovala jen rozdělení tvaru a nikdo by "
                "neověřil, že se z něj stane zapsaný fakt"
            ),
        ),
        Step(
            text="Byl Petr v Praze?",
            reading=sentence(
                w("Byl", "být", "AUX", 4, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("Petr", "Petr", "PROPN", 4, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
                w("Praze", "Praha", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
                w("?", "?", "PUNCT", 4, "punct"),
            ),
            reads="být(kde:Praha, kdo:·Petr)",
            answers="A",
            point=(
                "DOLOŽENO ZÁPISEM z předchozího kroku — a je to týž "
                "tvar `v+Loc/Geo` ve větě i v dotazu, takže se trefí na "
                "týž výrok"
            ),
        ),
        Step(
            text="Petr byl v tomto smyslu první.",
            reading=sentence(
                w("Petr", "Petr", "PROPN", 6, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", NameType="Giv", Number="Sing"),
                w("byl", "být", "AUX", 6, "cop", Aspect="Imp", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
                w("v", "v", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
                w("tomto", "tento", "DET", 5, "det", Case="Loc", Gender="Masc,Neut", Number="Sing", PronType="Dem"),
                w("smyslu", "smysl", "NOUN", 6, "obl", Animacy="Inan", Case="Loc", Gender="Masc", Number="Sing"),
                w("první", "první", "ADJ", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", NumType="Ord", Number="Sing"),
                w(".", ".", "PUNCT", 6, "punct"),
            ),
            reads="být(co:první, kdo:·Petr, v+Loc:smysl)",
            asks="v+Loc",
            point=(
                "ZÁVĚR DOMÉNY JE PODMÍNKA, NE PRÓZA: „v tomto smyslu“ "
                "NEMÁ SIGNÁL, takže tvar zůstane holý `v+Loc` a systém "
                "se dál PTÁ. Těch 26 vět z 42 je SPRÁVNÁ ODPOVĚĎ, ne mez, "
                "kterou je potřeba dohnat — rozhodnout je z tvaru by šlo "
                "jen seznamem slov"
            ),
            limit=(
                "Krok je ZÁMĚRNĚ POSLEDNÍ: nechává otevřenou otázku po "
                "významu tvaru a další věta by se četla jako odpověď"
            ),
        ),
    ),
    note=(
        "Dvacátý první akceptační dialog. `v+Loc` byl NEJČASTĚJŠÍ tvar "
        "bez významu (42 výskytů z 250) a slepoval dvě různé věci: "
        "„v Praze“ je místo, „v roce 1935“ čas. Jedno naučené mapování "
        "proto muselo být u jedné z nich špatně — a nebylo poznat u které. "
        "SIGNÁL NEURČUJE JMÉNO ROLE a určovat ho nesmí: že „v Praze“ je "
        "`kde` a „do Prahy“ `kam`, plyne z PŘEDLOŽKY A PÁDU. Signál dělá "
        "něco menšího — ROZDĚLUJE TVAR, o kterém se pak rozhoduje zvlášť."
    ),
    limit=(
        "CO SE TÍM NEŘEŠÍ: 26 ze 42 výskytů `v+Loc` nemá signál žádný "
        "(„v bytě“, „v kostele“, „v tomto smyslu“, „v angličtině“, „ve "
        "své knize“) a jsou mezi nimi místa i časy. Sort filleru použít "
        "NEJDE — podle § 3.6 plyne sort Z ROLE, takže odvodit roli ze "
        "sortu je kruh."
    ),
)


DIALOGUES: tuple[Dialogue, ...] = (
    ICE_CREAM,
    TRANSPORT,
    PHARMA,
    TIME_AND_PLACE,
    PETROVICE,
    VEGETARIAN,
    ORDER,
    EXCLUSION,
    IDENTITY,
    INCLUSION,
    CLOSURE,
    NAMING,
    DISCOURSE,
    PRODROP,
    ATTRIBUTE,
    SUBORDINATE,
    FULL_NAME,
    TITLED_NAME,
    TITLE_CLAIM,
    PASSIVE,
    SIGNAL,
)
