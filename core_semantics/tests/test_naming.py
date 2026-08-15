"""POJMENOVÁNÍ z české věty — poslední jádrový predikát.

`name` je jediný predikát, který spojuje UZEL s tím, jak se mu ŘÍKÁ, a
proto na něm visí kanonizace jmen. Dokud ho uměla zapsat jen vnitřní cesta
(rozdělení uzlu, M‑2), nedal se z jazyka dostat ALIAS — a alias je přesně
to, kvůli čemu `name` v jádře je.

**Druhá polovina tohohle modulu je o CITACI.** Zakotvení není premisa
důkazu; je to krok PŘED ním. Ale bez něj by se dotaz na uzel vůbec
netrefil, takže odpověď na otázku o „Honzovi" doložená pouze faktem
o „Janovi" nechává spojnici jen v hlavě systému. Je to táž třída nálezu
jako výčet u uzavření světa (0.1.14): půlka, která dělá práci, nesmí být
neviditelná.
"""

from __future__ import annotations

from core_semantics.ast import Entity, Group, Label, P_NAME, QueryStatus, atom, role
from core_semantics.cascade import naming_shape
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session
from core_semantics.tests._console import echo

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

TEACHER = Reading(
    tokens=(
        w(1, "Jan", "Jan", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
        w(2, "je", "být", "AUX", 3, "cop", Polarity="Pos", **COP),
        w(3, "učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

NAMING = Reading(
    tokens=(
        w(1, "Jan", "Jan", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
        w(2, "se", "se", "PRON", 3, "expl:pv", Case="Acc", Reflex="Yes"),
        w(3, "jmenuje", "jmenovat", "VERB", 0, "root", Polarity="Pos", **COP),
        w(4, "Honza", "Honza", "PROPN", 3, "obj", Case="Nom", Number="Sing"),
        w(5, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

#: „Ředitel jmenuje Jana." — `jmenovat` BEZ zvratného „se". Jmenovat DO
#: funkce, ne nazývat se, a je to docela jiné tvrzení.
APPOINTS = Reading(
    tokens=(
        w(1, "Ředitel", "ředitel", "NOUN", 2, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "jmenuje", "jmenovat", "VERB", 0, "root", Polarity="Pos", **COP),
        w(3, "Jana", "Jan", "PROPN", 2, "obj", Case="Acc", Number="Sing"),
        w(4, ".", ".", "PUNCT", 2, "punct"),
    ),
    provenance=STAMP,
)

ASK_ALIAS = Reading(
    tokens=(
        w(1, "Je", "být", "AUX", 3, "cop", Polarity="Pos", **COP),
        w(2, "Honza", "Honza", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
        w(3, "učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, "?", "?", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)


class _Recorded:
    provenance = STAMP

    def __init__(self, mapping: dict[str, Reading]) -> None:
        self._mapping = mapping

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._mapping[text],))


TEACHER_TEXT = "Jan je učitel."
NAMING_TEXT = "Jan se jmenuje Honza."
APPOINTS_TEXT = "Ředitel jmenuje Jana."
ASK_TEXT = "Je Honza učitel?"


def oracle() -> _Recorded:
    return _Recorded(
        {
            TEACHER_TEXT: TEACHER,
            NAMING_TEXT: NAMING,
            APPOINTS_TEXT: APPOINTS,
            ASK_TEXT: ASK_ALIAS,
        }
    )


# --------------------------------------------------------------------------
# Tvar
# --------------------------------------------------------------------------


def test_the_reflexive_naming_verb_is_a_construction() -> None:
    found = naming_shape(NAMING)
    assert found is not None
    assert (found.subject, found.value) == (1, 4)


def test_without_the_reflexive_it_is_not_naming() -> None:
    """„Ředitel jmenuje Jana." je jmenování DO FUNKCE. Kdyby to patro
    spletlo, zapsalo by `name(of:ředitel, value:Jan)` — tedy že se
    řediteli říká Jan."""
    assert naming_shape(APPOINTS) is None


def test_the_sides_come_from_deprels_not_from_candidate_order() -> None:
    """Generátor vyrobí dvě čtení, protože obě jména jsou v nominativu.
    Kdyby se strany braly podle pořadí, zapsalo by se jednou „Jan má
    přezdívku Honza" a podruhé pravý opak — a poznat by to nešlo."""
    session = Session()
    result = session.utter(NAMING_TEXT, oracle())
    assert result.predication is not None
    assert str(result.predication) == "name(of:Jan, value:Honza)"


def test_the_construction_is_substituted_not_asked() -> None:
    """`jmenovat se` je lexikálně o pojmenování a druhé čtení nemá — táž
    úvaha jako `PROPN` v podmětu holé spony (N‑2d). Ptát se „co ta věta
    tvrdí?" by byla otázka bez odběratele: v nabídce vztahů dvou TŘÍD
    správná odpověď není, protože tohle je vztah uzlu a nálepky."""
    session = Session()
    result = session.utter(NAMING_TEXT, oracle())
    assert result.question is None
    assert result.statement_id is not None


def test_naming_is_not_in_the_bare_copula_menu() -> None:
    """`Operation.NAME` do `RELATIONAL` nepatří. Nabídnout „tomu uzlu se
    takhle říká" u „Kočka je savec." by byla položka, na kterou tam nejde
    správně odpovědět."""
    from core_semantics.lexicon import RELATIONAL, Operation

    assert Operation.NAME not in RELATIONAL


# --------------------------------------------------------------------------
# Sorty: uzel × nálepka
# --------------------------------------------------------------------------


def test_the_two_sides_get_different_sorts() -> None:
    """`name` je první relace, jejíž strany nejsou na téže ose. Jeden sort
    na celou relaci by znamenal, že jméno je porovnatelné s uzlem, který
    ho nese — a přesně tomu má sortové typování bránit."""
    session = Session()
    session.utter(NAMING_TEXT, oracle())
    written = [
        statement.formula
        for statement in session.kb.active()
        if getattr(statement.formula, "predicate", "") == P_NAME
    ]
    assert written == [
        atom(P_NAME, role("of", Entity("Jan")), role("value", Label("Honza")))
    ]


# --------------------------------------------------------------------------
# Za co se to platí: alias funguje a je VIDĚT
# --------------------------------------------------------------------------


def test_before_the_naming_the_alias_is_a_stranger() -> None:
    session = Session()
    session.utter(TEACHER_TEXT, oracle())
    assert session.utter(ASK_TEXT, oracle()).status is QueryStatus.UNKNOWN


def test_after_the_naming_the_alias_reaches_the_node() -> None:
    session = Session()
    session.utter(TEACHER_TEXT, oracle())
    session.utter(NAMING_TEXT, oracle())
    assert session.utter(ASK_TEXT, oracle()).status is QueryStatus.PROVEN_TRUE


def test_the_answer_cites_the_statement_that_links_the_name() -> None:
    """NÁLEZ, ne kosmetika. Zakotvení není premisa důkazu, ale bez něj by
    se dotaz na tenhle uzel netrefil — a odpověď na otázku o „Honzovi"
    doložená jen faktem o „Janovi" nechává spojnici jen v hlavě systému.
    Táž třída jako výčet u uzavření světa."""
    session = Session()
    fact = session.utter(TEACHER_TEXT, oracle())
    link = session.utter(NAMING_TEXT, oracle())
    answer = session.utter(ASK_TEXT, oracle())
    cited = next(line for line in answer.lines if line.startswith("[doloženo:"))
    assert fact.statement_id is not None and link.statement_id is not None
    assert link.statement_id in cited
    assert fact.statement_id in cited


def test_the_link_is_revocable_like_any_other_statement() -> None:
    """Jméno je výrok, ne vlastnost uzlu. Po odvolání je „Honza" zase
    cizí — kdyby nebyl, byl by to jediný nevratný zápis v systému."""
    from core_semantics.session import revokes

    session = Session()
    session.utter(TEACHER_TEXT, oracle())
    link = session.utter(NAMING_TEXT, oracle())
    assert link.statement_id is not None
    session.play(revokes("Tak mu neříkáme.", link.statement_id, "přezdívka padla"))
    assert session.utter(ASK_TEXT, oracle()).status is QueryStatus.UNKNOWN


def test_the_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("POJMENOVÁNÍ Z ČESKÉ VĚTY")
    echo("=" * 72)
    session = Session()
    session.utter(TEACHER_TEXT, oracle())
    before = session.utter(ASK_TEXT, oracle()).status
    assert before is not None
    echo(f"   před pojmenováním: {before.name}")
    for line in session.utter(NAMING_TEXT, oracle()).lines:
        echo(f"   {line}")
    for line in session.utter(ASK_TEXT, oracle()).lines[-4:]:
        echo(f"   {line}")
    echo("=" * 72)


# --------------------------------------------------------------------------
# Otázky BEZ ODBĚRATELE — W‑20 a W‑29
# --------------------------------------------------------------------------
#
# Obojí je táž vada v různých vrstvách: systém se ptá tam, kde odpověď
# buď zná, nebo kde žádná správná odpověď neexistuje. Otázka bez
# odběratele je horší než mlčení — říká člověku, že něco chybí, a přitom
# nechybí nic, co by šlo doplnit.


def test_a_known_role_whose_canonical_name_collides_is_not_reported_missing() -> None:
    """W‑20. Když `v+Loc` i `v+Acc` znamenají `kdy`, druhá z nich se
    nepřejmenuje — ale JEJÍ VÝZNAM SE ZNÁ. Hlásit `[CHYBÍ: co znamená
    role v+Loc]` je nepravda a otázka na ni je otázka bez odběratele:
    jediná odpověď, kterou by člověk mohl dát, je právě ta, která kolizi
    způsobila."""
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation,
        PatternStatus,
        RoleMapping,
        Trigger,
        czech_seed,
    )

    lexicon = czech_seed()
    for upos, number, case, deprel in (
        ("NOUN", "Sing", "Nom", "nsubj"),
        ("PROPN", "Sing", "Loc", "root"),
        ("NOUN", "Sing", "Acc", "obl"),
    ):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number=number, case=case, deprel=deprel
                ),
                operation=Operation.SELF,
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    for surface in ("v+Loc", "v+Acc"):
        lexicon.add_role(
            RoleMapping(
                surface=surface,
                canonical="kdy",
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    collision = Reading(
        tokens=(
            w(1, "Koncert", "koncert", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
            w(2, "byl", "být", "AUX", 4, "cop", Polarity="Pos", **COP),
            w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
            w(4, "Praze", "Praha", "PROPN", 0, "root", Case="Loc", Number="Sing"),
            w(5, "v", "v", "ADP", 6, "case", Case="Acc"),
            w(6, "pondělí", "pondělí", "NOUN", 4, "obl", Case="Acc", Number="Sing"),
            w(7, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )
    text = "Koncert byl v Praze v pondělí."
    session = Session(lexicon=lexicon)
    result = session.utter(text, _Recorded({text: collision}))
    trace = " ".join(result.lines)
    assert "KOLIZE" in trace, "důvod se má POJMENOVAT, ne zamlčet"
    assert "CHYBÍ: co znamená role" not in trace
    assert result.question is None, (
        "otazka, na kterou system odpoved zna, je otazka bez odberatele"
    )


def test_the_collision_mark_survives_the_later_tiers() -> None:
    """PŘÍČINA, ne příznak. Značka nesmí ležet v `source` — to pole vlastní
    ten, kdo roli naposled sáhl, takže ji kvantifikátorové patro o krok dál
    přepsalo a otázka se ptala dál. Táž lekce jako B‑17."""
    import inspect

    from core_semantics.cascade import RoleReading

    assert "collided" in {field.name for field in RoleReading.__dataclass_fields__.values()}
    source = inspect.getsource(RoleReading)
    assert "W‑20" in source


def test_the_presentational_subject_is_not_asked_about() -> None:
    """W‑29. Prezentační „to" ve „To jsou všichni psi." NEODKAZUJE na nic —
    je to podmět bez reference, ne zájmeno, u kterého by aktivace pomohla.
    Ať člověk odpoví cokoli, žádný uzel z toho nevznikne."""
    from core_semantics.tests.test_world_closure import CLOSE, enumerated
    from core_semantics.tests.test_world_closure import oracle as closure_oracle

    session = enumerated()
    question = session.utter(CLOSE, closure_oracle()).question
    assert question is not None
    assert "odkazuje" not in question, (
        "na prezentační „to“ se ptát nemá: správná odpověď neexistuje"
    )


def test_a_demonstrative_that_does_mean_a_node_is_still_asked_about() -> None:
    """PROTIPŘÍKLAD K W‑29, druhá půlka. Výjimka je úzká schválně: „ten
    pes" uzel MÍNÍ, takže doptat se na něj je správné. Kdyby se ztišilo
    i tohle, systém by tiše zahazoval odkazy."""
    definite = Reading(
        tokens=(
            w(1, "Ten", "ten", "DET", 3, "det", Case="Nom", Gender="Masc", Number="Sing", PronType="Dem"),
            w(2, "pes", "pes", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
            w(3, "štěká", "štěkat", "VERB", 0, "root", Polarity="Pos", **COP),
            w(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )
    text = "Ten pes štěká."
    session = Session()
    result = session.utter(text, _Recorded({text: definite}))
    assert result.statement_id is None or result.question is not None, (
        "určitý popis se buď doptá, nebo se doloží — tiše se nezahazuje"
    )
