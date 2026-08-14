"""Jádrová relace ze STAVBY věty — N‑2.

**Problém.** „Amoxicilin je druh penicilinu." se přečetlo jako
`být(Gen:penicilin, co:druh, kdo:amoxicilin)` a nikdy jako `subset`.
Operace `MEMBER`/`SUBSET`/`DISJOINT` v menu byly, ale nikdo je ze stavby
věty neplnil — chybělo patro, které konstrukci rozpozná. Není to porušená
smlouva, je to CHYBĚJÍCÍ SCHOPNOST.

**Proč to blokovalo domény.** Kaskáda `subset*` je to, na čem stojí
lékařská kontraindikace: bez `subset(amoxicilin, penicilin)` se nemá
čeho chytit a doména neprojde česky, i když v jádře funguje.

**Tohle patro váží víc než ostatní.** Ostatní naučené vzory mění, jak se
věta ČTE. Tenhle mění, co se z ní zapíše do JÁDRA: špatně navržený
`subset` změní uzávěr celé báze a projeví se to na odpovědích, které
s tou větou nemají nic společného. Proto **návrh → potvrzení, nikdy
tiše**, přesně jako u kvantifikátoru.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    Entity,
    Group,
    QueryStatus,
    Quantifier,
    member_of,
    subset_of,
)
from core_semantics.cascade import cascade, relation_shape
from core_semantics.engine import Engine
from core_semantics.lexicon import Operation, RelationMapping, czech_seed
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session, names_relation

STAMP = "test"


def w(
    index: int, form: str, lemma: str, upos: str, head: int, deprel: str, **feats: str
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


COP = dict(
    Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Tense="Pres",
    VerbForm="Fin", Voice="Act",
)


SUBSET_SENTENCE = Reading(
    tokens=(
        w(1, "Amoxicilin", "amoxicilin", "NOUN", 3, "nsubj", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "je", "být", "AUX", 3, "cop", Polarity="Pos", **COP),
        w(3, "druh", "druh", "NOUN", 0, "root", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, "penicilinu", "penicilin", "NOUN", 3, "nmod", Animacy="Inan", Case="Gen", Gender="Masc", Number="Sing"),
        w(5, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

DISJOINT_SENTENCE = Reading(
    tokens=(
        w(1, "Vrabec", "vrabec", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "není", "být", "AUX", 3, "cop", Polarity="Neg", **COP),
        w(3, "savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)


def bare(
    subject: str, subject_lemma: str, upos: str = "NOUN", *, negated: bool = False
) -> Reading:
    """«<X> je savec.» — holá spona; kladná je ta dvojznačná."""
    return Reading(
        tokens=(
            w(1, subject, subject_lemma, upos, 3, "nsubj", Case="Nom", Number="Sing"),
            w(
                2,
                "není" if negated else "je",
                "být",
                "AUX",
                3,
                "cop",
                Polarity="Neg" if negated else "Pos",
                **COP,
            ),
            w(3, "savec", "savec", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
            w(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )


PROPERTY_SENTENCE = Reading(
    tokens=(
        w(1, "Auto", "auto", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        w(2, "je", "být", "AUX", 3, "cop", Polarity="Pos", **COP),
        w(3, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Gender="Neut", Number="Sing"),
        w(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)


class _Recorded:
    provenance = STAMP

    def __init__(self, mapping: dict[str, Reading]) -> None:
        self._mapping = mapping

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._mapping[text],))


SUBSET_TEXT = "Amoxicilin je druh penicilinu."
DISJOINT_TEXT = "Vrabec není savec."
CAT = "Kočka je savec."
DOG = "Pes je savec."
NAMED = "Mourek je savec."
NOT_NAMED = "Mourek není savec."
PROPERTY = "Auto je modré."

BARE_SHAPE = "cop:NOUN=NOUN"


def oracle() -> _Recorded:
    return _Recorded(
        {
            SUBSET_TEXT: SUBSET_SENTENCE,
            DISJOINT_TEXT: DISJOINT_SENTENCE,
            CAT: bare("Kočka", "kočka"),
            DOG: bare("Pes", "pes"),
            NAMED: bare("Mourek", "Mourek", upos="PROPN"),
            NOT_NAMED: bare("Mourek", "Mourek", upos="PROPN", negated=True),
            PROPERTY: PROPERTY_SENTENCE,
        }
    )


def _predication(reading: Reading):  # type: ignore[no-untyped-def]
    verdict = cascade(reading)
    assert verdict.decided is not None
    return verdict.decided.predication


# --------------------------------------------------------------------------
# Tvar konstrukce
# --------------------------------------------------------------------------


def test_the_shape_is_a_construction_not_a_word() -> None:
    """Učí se STAVBA, ne věta — jedna odpověď má zavřít celou třídu vět."""
    found = relation_shape(_predication(bare("Kočka", "kočka")), bare("Kočka", "kočka"))
    assert found is not None
    assert (found.shape, found.left, found.right) == (BARE_SHAPE, "kdo", "co")


def test_the_marker_construction_points_at_the_genitive() -> None:
    """„X je DRUH Y" — pravá strana relace je přívlastek v genitivu, ne
    jmenná část. Kdyby to patro spletlo, vyrobilo by `subset(amoxicilin,
    druh)`, což je nesmysl, který by se v bázi tvářil jako fakt."""
    found = relation_shape(_predication(SUBSET_SENTENCE), SUBSET_SENTENCE)
    assert found is not None
    assert found.shape == "cop:druh+Gen"
    assert (found.left, found.right) == ("kdo", "Gen")


def test_a_property_is_not_a_class_relation() -> None:
    """„Auto je modré." je VLASTNOST. Ptát se u ní na členství nebo
    podmnožinu je otázka bez odběratele — ať člověk odpoví cokoli, do
    jádrové relace se to nepřevede."""
    assert relation_shape(_predication(PROPERTY_SENTENCE), PROPERTY_SENTENCE) is None


def test_a_proper_name_subject_means_membership() -> None:
    """N‑2d. Poslední evidovaná mez z N‑2, zavřená.

    `PROPN` v podmětu **je** signál individua, takže tady je relace
    rozhodnutelná — na rozdíl od `NOUN=NOUN`, kde „Kočka je savec"
    (podmnožina) a „Mourek je kočka" (členství) mají týž tvar. Tvrdit
    o vlastním jméně podmnožinu by udělalo z individua třídu."""
    reading = bare("Mourek", "Mourek", upos="PROPN")
    found = relation_shape(_predication(reading), reading)
    assert found is not None
    assert found.shape == "cop:PROPN=NOUN"

    session = Session()
    result = session.utter(NAMED, oracle())
    assert result.predication is not None
    assert str(result.predication) == "member(elem:·Mourek, group:·savec)"
    assert result.statement_id is not None


def test_the_bare_noun_copula_still_asks_even_now() -> None:
    """PROTIPŘÍKLAD REVIEWERA (b), druhá půlka: `PROPN` rozhodl jen tam,
    kde JE. „Kočka je savec." se musí dál ptát — jinak by se z jednoho
    rozhodnutelného případu stal tichý default pro oba."""
    session = Session()
    result = session.utter(CAT, oracle())
    assert result.question is not None
    assert BARE_SHAPE in result.question
    assert result.statement_id is None


def test_a_named_individual_is_never_a_subclass() -> None:
    """Kdyby seed přiřadil `PROPN=NOUN` podmnožinu, „Mourek" by se stal
    TŘÍDOU — a uzávěr by pak přenášel na jeho „členy" tvrzení o kočkách."""
    session = Session()
    session.utter(NAMED, oracle())
    assert all("subset" not in line for line in session.program())


def test_a_negated_naming_is_documented_denial_not_disjointness() -> None:
    """Zápor je na `member` KOLMÝ, takže se přenáší. „Mourek není savec"
    je `member̄(Mourek, savec)`, tedy DOLOŽENÉ POPŘENÍ (§ 4) — ne
    oddělenost tříd, protože Mourek třída není, a ne mezera, protože
    o tom se něco ví (I‑21).

    U `disjoint` je to naopak a ta asymetrie je celý ten rozdíl: „tyhle
    dvě třídy se nepřekrývají" zápor už samo obsahuje."""
    session = Session()
    result = session.utter(NOT_NAMED, oracle())
    assert result.predication is not None
    assert result.predication.negated
    assert str(result.predication) == "¬member(elem:·Mourek, group:·savec)"

    denied = Engine(session.kb).ask(
        member_of(Entity("Mourek"), Group("savec"))
    )
    assert denied.status is QueryStatus.PROVEN_FALSE


def test_the_disjoint_relation_still_swallows_its_negation() -> None:
    """Druhá strana téže asymetrie — kdyby se zápor přenesl i sem,
    „Vrabec není savec" by tvrdilo `¬disjoint`, tedy pravý opak."""
    session = Session()
    result = session.utter(DISJOINT_TEXT, oracle())
    assert result.predication is not None
    assert not result.predication.negated


# --------------------------------------------------------------------------
# Jednoznačné konstrukce ze seedu
# --------------------------------------------------------------------------


def test_the_subset_sentence_finally_says_subset() -> None:
    """JÁDRO N‑2. Dřív z téhle věty bylo `být(Gen:…, co:druh, kdo:…)`."""
    session = Session()
    result = session.utter(SUBSET_TEXT, oracle())
    assert result.predication is not None
    assert str(result.predication) == "subset(sub:·amoxicilin, sup:·penicilin)"
    assert result.statement_id is not None
    assert any("STAVBA" in step for step in result.trace)


def test_the_written_subset_actually_works_as_a_closure() -> None:
    """Nestačí, aby se to tak JMENOVALO. `subset` je jádrový uzávěr —
    pokud se zapsal správně, musí se z něj dát odvodit členství, a přesně
    o to lékařské doméně jde."""
    session = Session()
    session.utter(SUBSET_TEXT, oracle())
    session.kb.attach(member_of(Group("curam"), Group("amoxicilin")))
    result = Engine(session.kb).ask(
        member_of(Group("curam"), Group("penicilin"))
    )
    assert result.status is QueryStatus.PROVEN_TRUE


def test_the_negated_bare_copula_goes_through_the_right_door() -> None:
    """PROTIPŘÍKLAD REVIEWERA (a). `disjoint` se nezapisuje přes `attach` —
    s markerem musí vzniknout i dvojice pravidel se silnou negací, jinak
    by se oddělenost dostala do indexu a NEODVODILO by se z ní nic.
    Ta zábrana je v `attach` správně, takže se neobchází; patro musí
    navrhnout tah, který jde `add_disjoint`em."""
    session = Session()
    result = session.utter(DISJOINT_TEXT, oracle())
    assert result.error is None, "přes `attach` by to skončilo AttachError"
    assert result.statement_id is not None
    assert any("expanze" in line for line in result.lines)


def test_the_disjointness_actually_denies_membership() -> None:
    """Táž kontrola jako u `subset`: expanze musí být k něčemu, ne jen
    zapsaná. Bez ní by `disjoint` dal `U` tam, kde má dát `N`."""
    session = Session()
    session.utter(DISJOINT_TEXT, oracle())
    session.kb.attach(member_of(Entity("čimčara"), Group("vrabec")))
    result = Engine(session.kb).ask(member_of(Entity("čimčara"), Group("savec")))
    assert result.status is QueryStatus.PROVEN_FALSE


def test_the_negation_is_carried_by_the_relation_not_by_a_bar() -> None:
    """`disjoint` sám nese, že se třídy nepřekrývají. Ponechat na něm
    `negated=True` by tvrdilo `¬disjoint`, tedy pravý opak."""
    predication = _predication(DISJOINT_SENTENCE)
    session = Session()
    result = session.utter(DISJOINT_TEXT, oracle())
    assert predication.negated, "před patrem to negované je"
    assert result.predication is not None
    assert not result.predication.negated
    assert result.predication.relation is Operation.DISJOINT


def test_the_relation_arguments_are_the_classes_themselves() -> None:
    """Kvantifikátor `·` není dohad: `subset(amoxicilin, penicilin)` mluví
    o dvou SKUPINÁCH, ne o jejich členech, a jádrové konstruktory to tak
    i vyžadují. Ptát se tu na kvantifikátor by byla otázka, na kterou má
    každá odpověď týž výsledek."""
    session = Session()
    result = session.utter(SUBSET_TEXT, oracle())
    assert result.predication is not None
    assert all(
        r.quantifier is Quantifier.SELF for r in result.predication.roles
    )
    assert result.predication.open_roles() == ()


# --------------------------------------------------------------------------
# Dvojznačná holá spona: ptá se, nehádá
# --------------------------------------------------------------------------


def test_the_bare_copula_asks_instead_of_guessing() -> None:
    """„Kočka je savec" je `subset`, „Mourek je kočka" `member`, a tvar je
    týž. Rozhodnout to za člověka by změnilo UZÁVĚR báze podle dohadu."""
    session = Session()
    result = session.utter(CAT, oracle())
    assert result.question is not None
    assert BARE_SHAPE in result.question
    for name in ("member", "subset", "disjoint"):
        assert name in result.question, "nabídka je uzavřené menu (I‑15)"


def test_nothing_is_written_while_the_relation_is_undecided() -> None:
    """Táž úvaha jako u ztraceného členu (N‑5): zapsat to teď jako
    obyčejný vztah `být` a po odpovědi znovu jako `subset` by uložilo DVA
    výroky a ten první by nikdo neodvolal."""
    session = Session()
    result = session.utter(CAT, oracle())
    assert result.statement_id is None
    assert session.program() == ()


def test_the_answer_completes_the_very_sentence_that_asked() -> None:
    """Odpověď je TAH: naučí tvar a čekající větu přečte ZNOVU."""
    session = Session()
    session.utter(CAT, oracle())
    answer = session.play(
        names_relation(
            "Je to podmnožina.", bare("Kočka", "kočka"), BARE_SHAPE, Operation.SUBSET
        )
    )
    assert answer.predication is not None
    assert str(answer.predication) == "subset(sub:·kočka, sup:·savec)"
    assert answer.statement_id is not None
    assert any("naučeno" in line for line in answer.lines)


def test_one_answer_closes_the_whole_class() -> None:
    """JINÁ věta téže stavby se přečte sama — rozdíl mezi naučenou
    konstrukcí a zapamatovanou odpovědí."""
    session = Session()
    session.utter(CAT, oracle())
    session.play(
        names_relation(
            "Je to podmnožina.", bare("Kočka", "kočka"), BARE_SHAPE, Operation.SUBSET
        )
    )
    again = session.utter(DOG, oracle())
    assert again.predication is not None
    assert str(again.predication) == "subset(sub:·pes, sup:·savec)"
    assert again.question is None


def test_the_learned_construction_is_revocable_data() -> None:
    """I‑16: co se naučí odpovědí, jde odvolat stejně jako cokoli jiného —
    a u patra, které mění uzávěr báze, to platí dvojnásob."""
    session = Session()
    session.utter(CAT, oracle())
    session.play(
        names_relation(
            "Je to podmnožina.", bare("Kočka", "kočka"), BARE_SHAPE, Operation.SUBSET
        )
    )
    learned = [m for m in session.lexicon.all_relations() if m.shape == BARE_SHAPE]
    assert learned and "tah" in learned[0].learned_from

    session.lexicon.revoke_relation(learned[0].key())
    assert session.utter(DOG, oracle()).question is not None


def test_the_whole_loop_replays_from_the_journal() -> None:
    """Odpověď je TAH, takže leží v žurnálu a přehrání se neptá podruhé."""
    session = Session()
    session.utter(CAT, oracle())
    session.play(
        names_relation(
            "Je to podmnožina.", bare("Kočka", "kočka"), BARE_SHAPE, Operation.SUBSET
        )
    )
    replayed = Session.replay(session.journal)
    assert replayed.program() == session.program()
    assert replayed.answers() == session.answers()


# --------------------------------------------------------------------------
# Uzavřené menu
# --------------------------------------------------------------------------


def test_the_menu_is_closed() -> None:
    """Dialog nesmí vyrobit relaci, kterou jádro nezná (I‑15). Selhat má
    ZÁPIS vzoru, ne čtení věty o tři tahy později."""
    with pytest.raises(ValueError, match="není jádrová relace"):
        RelationMapping(BARE_SHAPE, Operation.FOR_ALL, learned_from="test")


def test_an_answer_outside_the_menu_fails_as_a_turn() -> None:
    """A ten samý zákaz musí být slyšet i z DIALOGU, ne jen z knihovny."""
    session = Session()
    session.utter(CAT, oracle())
    answer = session.play(
        names_relation(
            "Je to o každém.", bare("Kočka", "kočka"), BARE_SHAPE, Operation.FOR_ALL
        )
    )
    assert answer.error is not None
    assert any("nenaučeno" in line for line in answer.lines)


def test_the_seed_only_contains_what_is_really_unambiguous() -> None:
    """Kdyby v seedu ležela holá kladná spona, systém by přestal doptávat
    a začal hádat — a nikdo by si toho nevšiml, protože by to vypadalo
    schopněji."""
    shapes = {m.shape for m in czech_seed().all_relations()}
    assert "cop:druh+Gen" in shapes
    assert "cop:NOUN≠NOUN" in shapes
    assert BARE_SHAPE not in shapes


# --------------------------------------------------------------------------
# Přepis
# --------------------------------------------------------------------------


def test_relation_from_structure_transcript_prints() -> None:
    from core_semantics.tests._console import echo

    echo("\n" + "=" * 72)
    echo("JÁDROVÁ RELACE ZE STAVBY VĚTY — N‑2")
    echo("=" * 72)
    session = Session()
    steps = [
        (SUBSET_TEXT, session.utter(SUBSET_TEXT, oracle())),
        (DISJOINT_TEXT, session.utter(DISJOINT_TEXT, oracle())),
        (CAT + "   (DVOJZNAČNÉ — ptá se)", session.utter(CAT, oracle())),
        (
            "→⊆ Je to podmnožina.",
            session.play(
                names_relation(
                    "Je to podmnožina.",
                    bare("Kočka", "kočka"),
                    BARE_SHAPE,
                    Operation.SUBSET,
                )
            ),
        ),
        (DOG + "   (JINÁ věta téže stavby)", session.utter(DOG, oracle())),
    ]
    for label, result in steps:
        echo(f"\n» {label}")
        for line in result.lines:
            echo(f"   {line}")
    echo("=" * 72)


# --------------------------------------------------------------------------
# Jmenná část s PŘÍVLASTKEM — N‑2b
# --------------------------------------------------------------------------
#
# „Auto je dopravní prostředek." je PRVNÍ věta akceptačního dialogu A
# a do N‑2b se nerozpoznávala vůbec: přívlastek dostal vlastní roli `jak`,
# věta měla tři členy a patro na ni mlčelo.
#
# DENOTACE PŘÍVLASTKU JE VĚDOMÉ ROZHODNUTÍ, ne vedlejší efekt. Zvolen je
# SLOŽENÝ POJEM (`dopravní_prostředek`), ne průnik `dopravní AND
# prostředek`. Důvody jsou v docstringu `relation_shape`; ten
# nejpodstatnější je, že průnik tvrdí INTERSEKTIVITU, která u „bývalý
# prezident" ani u lexikalizovaného sousloví neplatí — a morfologie ty
# případy nerozliší. Co se tím neplyne, jde doříct tahem; vymyslet to
# nejde vzít zpět.

ATTRIBUTE_SENTENCE = Reading(
    tokens=(
        w(1, "Auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
        w(2, "je", "být", "AUX", 4, "cop", Polarity="Pos", **COP),
        w(3, "dopravní", "dopravní", "ADJ", 4, "amod", Animacy="Inan", Case="Nom", Degree="Pos", Gender="Masc", Number="Sing", Polarity="Pos"),
        w(4, "prostředek", "prostředek", "NOUN", 0, "root", Animacy="Inan", Case="Nom", Gender="Masc", Number="Sing"),
        w(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)

ATTRIBUTE_TEXT = "Auto je dopravní prostředek."


def _with_attribute() -> _Recorded:
    mapping = dict(oracle()._mapping)
    mapping[ATTRIBUTE_TEXT] = ATTRIBUTE_SENTENCE
    return _Recorded(mapping)


def test_an_attribute_makes_one_concept_not_two() -> None:
    """Po složení lemmatu zbydou DVĚ strany, takže věta spadne do TÉŽE
    rodiny jako holá spona. Jedna otázka, jedna odpověď, obě třídy vět.

    Od N‑2c skládá `generate`, ne tohle patro — sem už fráze přichází
    složená. Test se proto ptá na PŘEČTENOU predikaci, ne na pole
    konstrukce: kdyby se skládalo na dvou místech podle dvou předpisů,
    rozešly by se."""
    predication = _predication(ATTRIBUTE_SENTENCE)
    assert str(predication) == "být(co:dopravní_prostředek, kdo:auto)"
    found = relation_shape(predication, ATTRIBUTE_SENTENCE)
    assert found is not None
    assert found.shape == BARE_SHAPE


def test_the_attribute_is_not_reported_as_a_lost_member() -> None:
    """Přívlastek se do významu DOSTAL, jen ne vlastní rolí. Hlásit ho
    jako ztrátu (N‑5) by poslalo člověka pojmenovat roli něčemu, co roli
    mít nemá — táž vada, kterou u složeného přísudku řeší G‑1a."""
    session = Session()
    session.lexicon.teach_relation(
        BARE_SHAPE, Operation.SUBSET, learned_from="test"
    )
    verdict = cascade(ATTRIBUTE_SENTENCE, tiers=session.tiers())
    assert verdict.decided is not None
    assert str(verdict.decided.predication) == (
        "subset(sub:·auto, sup:·dopravní_prostředek)"
    )
    assert verdict.lost == ()


def test_the_first_sentence_of_dialogue_a_completes() -> None:
    """Celý tah: zeptá se, odpověď ho dokončí, a do báze jde `subset`."""
    session = Session()
    asked = session.utter(ATTRIBUTE_TEXT, _with_attribute())
    assert asked.question is not None and BARE_SHAPE in asked.question
    assert asked.statement_id is None

    answer = session.play(
        names_relation(
            "Je to podmnožina.", ATTRIBUTE_SENTENCE, BARE_SHAPE, Operation.SUBSET
        )
    )
    assert answer.predication is not None
    assert str(answer.predication) == "subset(sub:·auto, sup:·dopravní_prostředek)"
    assert answer.statement_id is not None


def test_one_answer_closes_both_families_at_once() -> None:
    """Že je to JEDNA rodina, není kosmetika: odpověď daná na „Kočka je
    savec" dočte i „Auto je dopravní prostředek". Kdyby to byly dva tvary,
    musel by člověk odpovídat dvakrát na tutéž otázku."""
    session = Session()
    session.utter(CAT, _with_attribute())
    session.play(
        names_relation(
            "Je to podmnožina.", bare("Kočka", "kočka"), BARE_SHAPE, Operation.SUBSET
        )
    )
    again = session.utter(ATTRIBUTE_TEXT, _with_attribute())
    assert again.predication is not None
    assert str(again.predication) == "subset(sub:·auto, sup:·dopravní_prostředek)"
    assert again.question is None


def test_the_property_sentence_did_not_start_proposing_classes() -> None:
    """PROTIPŘÍKLAD REVIEWERA (a). Rozšíření na přívlastek nesmí uvolnit
    podmínku, že jmenná část je NOUN — „To auto je modré." je vlastnost."""
    assert relation_shape(_predication(PROPERTY_SENTENCE), PROPERTY_SENTENCE) is None


def test_the_marker_construction_is_unchanged() -> None:
    """PROTIPŘÍKLAD REVIEWERA (b). Genitivní větev běží PŘED složením,
    takže „X je druh Y" se rozšířením nezměnilo."""
    session = Session()
    result = session.utter(SUBSET_TEXT, _with_attribute())
    assert result.predication is not None
    assert str(result.predication) == "subset(sub:·amoxicilin, sup:·penicilin)"
    assert result.statement_id is not None


def test_the_composed_class_is_not_an_intersection() -> None:
    """DOKLAD ZVOLENÉ DENOTACE. Kdyby se přívlastek zapsal jako průnik,
    byl by `dopravní` samostatnou třídou v bázi — a systém by tím tvrdil
    něco, co věta neříká a co u „bývalý prezident" neplatí."""
    session = Session()
    session.lexicon.teach_relation(
        BARE_SHAPE, Operation.SUBSET, learned_from="test"
    )
    session.utter(ATTRIBUTE_TEXT, _with_attribute())
    written = " ".join(session.program())
    assert "dopravní_prostředek" in written
    assert " AND " not in written


def test_what_the_composition_does_not_claim_can_be_said_by_a_turn() -> None:
    """Druhá půlka téhož rozhodnutí: `dopravní prostředek ⊆ prostředek`
    z ničeho neplyne, ale NENÍ ztracené — člověk to smí doříct, a už
    dnešní genitivní konstrukcí."""
    session = Session()
    session.lexicon.teach_relation(
        BARE_SHAPE, Operation.SUBSET, learned_from="test"
    )
    session.utter(ATTRIBUTE_TEXT, _with_attribute())
    session.kb.attach(
        subset_of(Group("dopravní_prostředek"), Group("prostředek"))
    )
    result = Engine(session.kb).ask(
        subset_of(Group("auto"), Group("prostředek"))
    )
    assert result.status is QueryStatus.PROVEN_TRUE


# --------------------------------------------------------------------------
# `before` z české věty — N‑9
# --------------------------------------------------------------------------
#
# Akceptační sada zapisovala z DEVÍTI jádrových predikátů jen DVA
# (`member`, `subset`). Zbytek evaluátor umí a testy ho pokrývají na
# úrovni formulí, ale žádná česká věta k němu nevedla — a schopnost,
# kterou jazyk nedosáhne, se nedá odlišit od schopnosti, která
# nefunguje. Byl to týž vzorec jako B‑10, B‑11 i B‑13.

COP_INS = dict(
    Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Tense="Pres",
    VerbForm="Fin", Voice="Act", Polarity="Pos",
)


def order(earlier: str, later: str, *, question: bool = False) -> Reading:
    """«<X> je před <Y>.» / «Je <X> před <Y>?»"""
    # Pořadí slov se v otázce obrací („Je pondělí…" × „Pondělí je…"),
    # a je to jediné, co se mezi tvrzením a otázkou liší — proto se
    # skládají oba tvary z týchž dílů.
    order_of = (
        (("Je", "být", "AUX", "cop"), (earlier, earlier, "NOUN", "nsubj"))
        if question
        else ((earlier, earlier, "NOUN", "nsubj"), ("je", "být", "AUX", "cop"))
    )
    first, second = order_of
    return Reading(
        tokens=(
            w(1, first[0], first[1], first[2], 4, first[3], **(
                COP_INS if first[3] == "cop" else {"Case": "Nom", "Number": "Sing"}
            )),
            w(2, second[0], second[1], second[2], 4, second[3], **(
                COP_INS if second[3] == "cop" else {"Case": "Nom", "Number": "Sing"}
            )),
            w(3, "před", "před", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
            w(4, later, later, "NOUN", 0, "root", Case="Ins", Number="Sing"),
            w(5, "?" if question else ".", "?" if question else ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )


def test_a_czech_sentence_finally_produces_before() -> None:
    """JÁDRO N‑9. Předložka s pádem říká, JAKÝ vztah se tvrdí — přesně
    jako `druh` u podtřídy."""
    reading = order("pondělí", "úterý")
    found = relation_shape(_predication(reading), reading)
    assert found is not None
    assert found.shape == "cop:před+Ins"
    assert (found.left, found.right) == ("kdo", "před+Ins")


def test_the_sides_are_intervals_not_groups() -> None:
    """SORT PLYNE Z RELACE, ne ze jména role: `before` mluví o časové ose,
    ať se ty role jmenují jakkoli. Odvozovat to ze jména by nešlo —
    `whole`/`part` má `contains` (místo) i `within` (čas)."""
    session = Session()
    result = session.utter("Pondělí je před úterým.", _order_oracle())
    assert result.predication is not None
    assert str(result.predication) == "before(earlier:pondělí, later:úterý)"
    assert result.statement_id is not None
    assert all(r.quantifier is None for r in result.predication.roles), (
        "čas se nekvantifikuje (§ 3.6) — ptát se na to by byla otázka "
        "bez odběratele"
    )


def _order_oracle() -> _Recorded:
    return _Recorded(
        {
            "Pondělí je před úterým.": order("pondělí", "úterý"),
            "Úterý je před středou.": order("úterý", "středa"),
            "Je pondělí před středou?": order("pondělí", "středa", question=True),
            "Je středa před pondělím?": order("středa", "pondělí", question=True),
        }
    )


def _ordered_session() -> Session:
    session = Session()
    oracle = _order_oracle()
    session.utter("Pondělí je před úterým.", oracle)
    session.utter("Úterý je před středou.", oracle)
    return session


def test_the_answer_needs_a_transitive_step() -> None:
    """COUNTEREXAMPLE REVIEWERA. Ten vztah nikdo nezapsal — plyne z OBOU
    zapsaných, a důkaz je cituje. Jediný zápis by uzávěr neprověřil."""
    result = _ordered_session().utter("Je pondělí před středou?", _order_oracle())
    assert result.status is QueryStatus.PROVEN_TRUE
    cited = [line for line in result.lines if "řekls" in line]
    assert len(cited) == 2, f"důkaz musí citovat OBA zápisy: {result.lines}"


def test_the_opposite_direction_is_unknown_not_false() -> None:
    """OTEVŘENÝ SVĚT. Z „pondělí je před středou" NEPLYNE, že středa před
    pondělím není — plynulo by to teprve z uzavření osy, které nikdo
    nevyslovil. `N` by tu bylo tvrzení navíc."""
    result = _ordered_session().utter("Je středa před pondělím?", _order_oracle())
    assert result.status is QueryStatus.UNKNOWN
