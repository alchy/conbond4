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
    roles=(("v+Loc", "kde"),),
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
    roles=(("v+Loc", "kde"),),
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


DIALOGUES: tuple[Dialogue, ...] = (
    ICE_CREAM,
    TRANSPORT,
    PHARMA,
    TIME_AND_PLACE,
    PETROVICE,
    VEGETARIAN,
    ORDER,
    EXCLUSION,
)
