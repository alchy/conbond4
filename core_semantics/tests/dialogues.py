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

PROVENANCE = "udpipe2 model=czech-pdt-ud-2.12 tokenizer=czech-pdt-2.12"


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
                w("Roník", "Roník", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
                w("bydlí", "bydlet", "VERB", 0, "root", Number="Sing"),
                w("v", "v", "ADP", 4, "case"),
                w("Petrovicích", "Petrovice", "PROPN", 2, "obl", Case="Loc", Number="Plur"),
            ),
            reads="bydlet(kdo:·Roník, v+Loc:Petrovice)",
            asks="`v`+Loc je `kde` i `kdy`, takže role zůstane POVRCHOVÁ. "
            "Ptá se proto nejdřív na kvantifikátor (povrchová role není "
            "místní role, takže se kvantifikuje jako každá jiná) a věta "
            "se nezakotví. Obojí má týž kořen: dokud se nerozhodne, co "
            "`v`+Loc znamená, není z čeho určit ani sort filleru",
            point="doména, kterou dnes česky NEPŘEČTEME celou, a je to vidět",
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
                w("Jana", "Jana", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
                w("je", "být", "AUX", 3, "cop", Number="Sing"),
                w("učitelka", "učitelka", "NOUN", 0, "root", Case="Nom", Number="Sing"),
            ),
            reads="být(co:·učitelka, kdo:·Jana)",
            anchors=("Jana → Jana (založen)", "učitelka → učitelka (obecné jméno)"),
            writes="být(co:·učitelka, kdo:Jana)",
            point="spona: vlastní jméno je uzel, jmenná část je skupina",
        ),
        Step(
            text="Děti mají rády zmrzlinu.",
            reading=sentence(
                w("Děti", "dítě", "NOUN", 2, "nsubj", Case="Nom", Number="Plur"),
                w("mají", "mít", "VERB", 0, "root", Number="Plur"),
                w("rády", "rád", "ADJ", 2, "advmod", Number="Plur"),
                w("zmrzlinu", "zmrzlina", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
            ),
            reads="mít(co:∃zmrzlina, jak:·rád, kdo:∀dítě)",
            writes="mít(co:∃zmrzlina, jak:·rád, kdo:∀dítě)",
            point="∀ na podmětu, ∃ na předmětu — a `jak` je taky skupina",
        ),
        Step(
            text="Je Jana učitelka?",
            reading=sentence(
                w("Je", "být", "AUX", 3, "cop", Number="Sing"),
                w("Jana", "Jana", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
                w("učitelka", "učitelka", "NOUN", 0, "root", Case="Nom", Number="Sing"),
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
                w("Auta", "auto", "NOUN", 2, "nsubj", Case="Nom", Number="Plur"),
                w("jezdí", "jezdit", "VERB", 0, "root", Number="Plur"),
                w("po", "po", "ADP", 4, "case"),
                w("dálnici", "dálnice", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
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
                w("Jezdí", "jezdit", "VERB", 0, "root", Number="Plur"),
                w("auta", "auto", "NOUN", 1, "nsubj", Case="Nom", Number="Plur"),
                w("po", "po", "ADP", 4, "case"),
                w("dálnici", "dálnice", "NOUN", 1, "obl", Case="Loc", Number="Sing"),
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
    source="„Pacient Jan má alergii. Jan nesmí penicilin.“",
    shapes=(PROPN_SUBJ, NOUN_OBJ_SG),
    steps=(
        Step(
            text="Jan má alergii.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
                w("má", "mít", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
                w("alergii", "alergie", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
            ),
            reads="mít(co:∃alergie, kdo:·Jan)",
            writes="mít(co:∃alergie, kdo:Jan)",
        ),
        Step(
            text="Jan nesmí penicilin.",
            reading=sentence(
                w("Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
                w("nesmí", "smět", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
                w("penicilin", "penicilin", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
            ),
            reads="¬smět(co:∃penicilin, kdo:·Jan)",
            writes="¬smět(co:∃penicilin, kdo:Jan)",
            point="ZÁVĚR CELÉ DOMÉNY. Bez čtení `Polarity=Neg` by věta "
            "znamenala pravý opak — a to je v téhle doméně rozdíl, "
            "který se nepočítá v bodech",
        ),
        Step(
            text="Smí Jan penicilin?",
            reading=sentence(
                w("Smí", "smět", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
                w("Jan", "Jan", "PROPN", 1, "nsubj", Case="Nom", Number="Sing"),
                w("penicilin", "penicilin", "NOUN", 1, "obj", Case="Acc", Number="Sing"),
            ),
            reads="smět(co:∃penicilin, kdo:·Jan)",
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
                w("Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
                w("jel", "jet", "VERB", 0, "root", Number="Sing"),
                w("do", "do", "ADP", 4, "case"),
                w("Prahy", "Praha", "PROPN", 2, "obl", Case="Gen", Number="Sing"),
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
                w("Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
                w("jel", "jet", "VERB", 0, "root", Number="Sing"),
                w("do", "do", "ADP", 4, "case"),
                w("Brna", "Brno", "PROPN", 2, "obl", Case="Gen", Number="Sing"),
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
                w("Jel", "jet", "VERB", 0, "root", Number="Sing"),
                w("Petr", "Petr", "PROPN", 1, "nsubj", Case="Nom", Number="Sing"),
                w("do", "do", "ADP", 4, "case"),
                w("Prahy", "Praha", "PROPN", 1, "obl", Case="Gen", Number="Sing"),
            ),
            reads="jet(kam:Praha, kdo:·Petr)",
            answers="A",
        ),
        Step(
            text="Jel Petr do Plzně?",
            reading=sentence(
                w("Jel", "jet", "VERB", 0, "root", Number="Sing"),
                w("Petr", "Petr", "PROPN", 1, "nsubj", Case="Nom", Number="Sing"),
                w("do", "do", "ADP", 4, "case"),
                w("Plzně", "Plzeň", "PROPN", 1, "obl", Case="Gen", Number="Sing"),
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
