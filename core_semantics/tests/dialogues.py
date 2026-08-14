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
    reading: Reading
    reads: str = ""
    #: Očekávané vazby zmínek na uzly, jako `„tvar“ → uzel`.
    anchors: tuple[str, ...] = ()
    #: Formule, která má skončit v bázi. Prázdné = tah nic nezapisuje.
    writes: str = ""
    #: Očekávaný verdikt otázky (`A` / `N` / `U` / `CONFLICT`).
    answers: str = ""
    asks: str = ""
    refuses: str = ""
    point: str = ""


@dataclass(frozen=True, slots=True)
class Dialogue:
    name: str
    source: str
    steps: tuple[Step, ...]
    #: Tvary potvrzené člověkem pro tuhle doménu. Do `czech_seed()` nepatří
    #: — tam by z nich byl tichý default pro každého, kdo knihovnu použije.
    shapes: tuple[tuple[str, str, str, str, Operation], ...] = ()
    note: str = ""

    def lexicon(self) -> Lexicon:
        lexicon = czech_seed()
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
    shapes=(PROPN_SUBJ,),
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
            reads="bydlet(kdo:roník, v+Loc:Petrovice)",
            asks="`v`+Loc je `kde` i `kdy`, takže role zůstane POVRCHOVÁ. "
            "Ptá se proto nejdřív na kvantifikátor (povrchová role není "
            "místní role, takže se kvantifikuje jako každá jiná) a věta "
            "se nezakotví. Obojí má týž kořen: dokud se nerozhodne, co "
            "`v`+Loc znamená, není z čeho určit ani sort filleru",
            point="doména, kterou dnes česky NEPŘEČTEME celou, a je to vidět",
            refuses="",
        ),
    ),
    note="Petrovice ukazují MEZ: bez rozhodnutí `v`+Loc → `kde` se místní "
    "určení nezakotví. Dialog je v sadě schválně — doména, která "
    "strukturovaně funguje a česky ne, je informace, ne ostuda.",
)


# --------------------------------------------------------------------------
# 2 · Jana a zmrzlina — řetěz dvou ∃-relací
# --------------------------------------------------------------------------

ICE_CREAM = Dialogue(
    name="Jana a zmrzlina",
    source="„Jana je učitelka. Děti mají rády zmrzlinu.“",
    shapes=(
        PROPN_SUBJ,
        NOUN_ROOT,
        NOUN_SUBJ_PL,
        NOUN_OBJ_SG,
        # „rády" je přívlastkové příslovce v roli `jak` — podle § 6.12
        # je i tohle SKUPINA, takže kvantifikátor potřebuje.
        ("ADJ", "Plur", "", "advmod", Operation.SELF),
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
            reads="být(co:·učitelka, kdo:·Jana)",
            anchors=("Jana → Jana (založen)", "učitelka → učitelka (obecné jméno)"),
            writes="být(co:·učitelka, kdo:Jana)",
            point="spona: vlastní jméno je uzel, jmenná část je skupina",
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
            refuses=(
                "parser označí „rády“ jako `iobj`, tedy jako druhý PŘEDMĚT. "
                "„rády“ i „zmrzlinu“ pak dostanou touž roli `co`, čtení "
                "s duplicitní rolí se nesmí vyrobit a nezbyde ani jedno. "
                "Systém to ŘEKNE: „dva jádrové členy dostaly touž roli (co)“."
            ),
            point=(
                "táž třída jako B‑9, jen o patro blíž jádru: tam kolidovala "
                "dvě příslovečná určení, tady dva jádrové členy"
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
            reads="být(co:·učitelka, kdo:·Jana)",
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
    ),
)


DIALOGUES: tuple[Dialogue, ...] = (
    ICE_CREAM,
    TRANSPORT,
    PHARMA,
    TIME_AND_PLACE,
    PETROVICE,
)
