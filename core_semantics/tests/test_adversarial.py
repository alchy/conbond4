"""Adversariální dialogy H a I — N‑2 (K‑10).

Ostatní sady ověřují, že systém dělá, co má. Tahle se ho snaží
**přistihnout**: mířit ne doprostřed vrstev, ale na ŠVY mezi nimi,
protože tam vznikly úplně všechny vážné vady tohohle projektu (B‑9,
nepředaná `tiers`, `Utterance.readings`, `disjoint`, `complete`, sporná
identita).

Čtyři švy, které si N‑2 vytkla:

* **kanonizace × rozdělení** — po `!÷` už jméno nese víc uzlů
* **určitost × spor identity** — kandidáti, o jejichž totožnosti se báze hádá
* **zápor × otázka** — doložené popření se nesmí splést s nevědomostí
* **odvolání × odkazované uzly** — co zbude, když premisa zmizí

Test, který projde, tu neznamená „funguje to". Znamená „tenhle konkrétní
způsob, jak systém obelstít, nefunguje" — a to je jediné, co jde tvrdit.
"""

from __future__ import annotations

from core_semantics.ast import (
    Entity,
    Group,
    QueryStatus,
    Quantifier,
    atom,
    member_of,
    role,
    same_as_of,
)
from core_semantics.engine import Engine
from core_semantics.gaps import GapFinder
from core_semantics.lexicon import (
    LearnedPattern,
    Lexicon,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import (
    Session,
    TurnResult,
    declares_distinct,
    says,
    splits,
)
from core_semantics.storage import KnowledgeBase
from core_semantics.tests._console import echo

STAMP = "test"


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


class _Say:
    provenance = STAMP

    def __init__(self, *tokens: Token) -> None:
        self._tokens = tokens

    def parse(self, text: str) -> Utterance:
        return Utterance(
            text=text,
            readings=(Reading(tokens=self._tokens, provenance=STAMP),),
        )


def lexicon(*shapes: tuple[str, str, str, str, Operation]) -> Lexicon:
    lex = czech_seed()
    for upos, number, case, deprel, operation in shapes:
        lex.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number=number, case=case, deprel=deprel
                ),
                operation=operation,
                learned_from="adversariální sada",
                status=PatternStatus.CONFIRMED,
            )
        )
    return lex


PROPN_SUBJ = ("PROPN", "Sing", "Nom", "nsubj", Operation.SELF)
NOUN_OBJ = ("NOUN", "Sing", "Acc", "obj", Operation.EXISTS)
ADJ_ROOT = ("ADJ", "Sing", "Nom", "root", Operation.SELF)


def petr_has_car() -> _Say:
    return _Say(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "má", "mít", "VERB", 0, "root", Number="Sing"),
        tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )


def that_car_is_blue() -> _Say:
    return _Say(
        tok(1, "To", "ten", "DET", 2, "det", Case="Nom"),
        tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
        tok(3, "je", "být", "AUX", 4, "cop", Number="Sing"),
        tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
    )


# --------------------------------------------------------------------------
# Dialog H — identita
# --------------------------------------------------------------------------


def test_h1_a_name_split_apart_is_not_quietly_put_back_together() -> None:
    """ÚTOK: řeknu „Petr má auto.", pak Petra rozdělím, pak to řeknu znovu.

    Slabé místo je v tom, že kanonizace jmen mapovala jméno na uzel podle
    LEMMATU. Po rozdělení uzel `Petr` v bázi není — takže by se založil
    ZNOVU, jako by se nic nestalo, a vznikl by třetí Petr. Systém by tím
    zrušil rozhodnutí, které člověk právě výslovně udělal.
    """
    session = Session(lexicon=lexicon(PROPN_SUBJ, NOUN_OBJ))
    session.utter("Petr má auto.", petr_has_car())
    session.play(splits("Byli to dva.", Entity("Petr"), ("Petr_1", "Petr_2"), "dva"))

    again = session.utter("Petr má auto.", petr_has_car())
    assert again.statement_id is None, "systém si vyrobil třetího Petra"
    assert again.question is not None
    assert "nese víc uzlů" in again.question
    assert "Petr_1" in again.question and "Petr_2" in again.question


def test_h2_a_definite_description_over_disputed_identity_refuses() -> None:
    """ÚTOK: dvě auta, o kterých báze tvrdí, že jsou i nejsou táž.

    Kdyby určitý popis počítal sporné uzly za jeden, „to auto" by se
    tiše rozhodlo pro jeden z nich — a spor by se tím zametl."""
    session = Session(lexicon=lexicon(ADJ_ROOT))
    session.kb.attach(member_of(Entity("a1"), Group("auto")))
    session.kb.attach(member_of(Entity("a2"), Group("auto")))
    session.kb.attach(same_as_of(Entity("a1"), Entity("a2")))
    session.kb.attach(same_as_of(Entity("a1"), Entity("a2")).complement())

    result = session.utter("To auto je modré.", that_car_is_blue())
    assert result.statement_id is None
    assert result.question is not None
    assert "Znám jich víc" in result.question


def test_h3_facts_do_not_survive_the_split_under_the_old_name() -> None:
    """ÚTOK: po rozdělení se zeptám na PŮVODNÍ uzel.

    Kdyby o něm něco zůstalo platit, rozdělení by bylo jen kosmetické."""
    session = Session()
    session.play(says("Petr má auto.", atom("mít", role("kdo", Entity("Petr")))))
    session.play(splits("Byli to dva.", Entity("Petr"), ("Petr_1", "Petr_2"), "dva"))
    engine = Engine(session.kb)
    assert engine.ask(atom("mít", role("kdo", Entity("Petr")))).status is (
        QueryStatus.UNKNOWN
    )
    assert engine.ask(atom("mít", role("kdo", Entity("Petr_1")))).status is (
        QueryStatus.PROVEN_TRUE
    )


def test_h4_denying_identity_does_not_poison_unrelated_names() -> None:
    """ÚTOK: popřu identitu dvou uzlů a zkusím, jestli tím rozbiju
    kanonizaci jména, které s tím nemá co dělat."""
    session = Session(lexicon=lexicon(PROPN_SUBJ, NOUN_OBJ))
    session.utter("Petr má auto.", petr_has_car())
    session.play(
        declares_distinct("Nejsou tíž.", Entity("Jan"), Entity("Jan_z_Brna"))
    )
    again = session.utter("Petr má auto.", petr_has_car())
    assert again.statement_id is not None
    assert any("kanonicky" in line for line in again.lines)


# --------------------------------------------------------------------------
# Dialog I — neúplné premisy a zápor
# --------------------------------------------------------------------------


def test_i1_absence_is_never_read_as_denial() -> None:
    """ÚTOK: řeknu, že tučňák nelétá, a zeptám se na vrabce.

    I‑21 v nejostřejší podobě. Kdyby se mlčení četlo jako popření,
    systém by o vrabci tvrdil něco, co nikdo neřekl."""
    kb = KnowledgeBase()
    flies = atom("létat", role("kdo", Group("tučňák"), Quantifier.FOR_ALL))
    kb.attach(flies.complement())
    engine = Engine(kb)
    assert engine.ask(flies).status is QueryStatus.PROVEN_FALSE
    sparrow = atom("létat", role("kdo", Group("vrabec"), Quantifier.FOR_ALL))
    assert engine.ask(sparrow).status is QueryStatus.UNKNOWN
    assert engine.ask(sparrow.complement()).status is QueryStatus.UNKNOWN


def test_i2_a_negated_sentence_that_cannot_be_grounded_writes_nothing() -> None:
    """ÚTOK: záporná věta s rolí bez kvantifikátoru.

    Nejnebezpečnější možný tichý zápis: kdyby se zapsala půlka záporné
    věty, báze by tvrdila opak toho, co člověk řekl."""
    session = Session()  # bez potvrzených tvarů → role zůstane otevřená
    result = session.utter(
        "Petr nemá auto.",
        _Say(
            tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "nemá", "mít", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
            tok(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
        ),
    )
    assert result.predication is not None and result.predication.negated
    assert result.statement_id is None
    assert session.program() == ()


def test_i3_revoking_the_premise_takes_the_answer_with_it() -> None:
    """ÚTOK: doložím odpověď, pak odvolám premisu a zeptám se znovu.

    Odpověď, která přežije odvolání, je odpověď z ničeho."""
    kb = KnowledgeBase()
    sid = kb.attach(member_of(Entity("a1"), Group("auto")))
    asked = member_of(Entity("a1"), Group("auto"))
    assert Engine(kb).ask(asked).status is QueryStatus.PROVEN_TRUE
    kb.revoke(sid, "spletl jsem se")
    assert Engine(kb).ask(asked).status is QueryStatus.UNKNOWN


def test_i4_a_definite_description_over_a_revoked_node_refuses() -> None:
    """ÚTOK: odvolám jediné členství a pak řeknu „to auto".

    Uzel v úložišti zůstal (§ 8 — deaktivace, ne mazání), takže je
    v pokušení se na něj odkázat. Nesmí: aktivní výrok o něm žádný není."""
    session = Session(lexicon=lexicon(ADJ_ROOT))
    sid = session.kb.attach(member_of(Entity("a1"), Group("auto")))
    session.kb.revoke(sid, "spletl jsem se")
    result = session.utter("To auto je modré.", that_car_is_blue())
    assert result.statement_id is None
    assert result.question is not None
    assert "nezakládá" in result.question


def test_i5_the_gap_is_an_offer_not_a_reproach() -> None:
    """K‑9, ověření. „Chybí vědět: X" po člověku chce, aby si sám domyslel,
    co s tím, a hlavně to zní jako výtka. Táž informace položená jako
    otázka je tah, na který jde odpovědět."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("v1"), Group("vrabec")))
    engine = Engine(kb)
    asked = member_of(Entity("v1"), Group("tučňák"))
    report = GapFinder(engine).explain(asked)
    rendered = report.render()
    assert any(line.startswith("?") for line in rendered), rendered
    assert any("HYPOTÉZA" in line for line in rendered), rendered
    assert not any("chybí vědět" in line for line in rendered), (
        "K‑9: mezera se má NABÍZET, ne konstatovat"
    )


def test_adversarial_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("ADVERSARIÁLNÍ DIALOGY H a I — N‑2")
    echo("=" * 72)
    echo("\n### H — kanonizace × rozdělení")
    session = Session(lexicon=lexicon(PROPN_SUBJ, NOUN_OBJ))
    steps: list[tuple[str, TurnResult]] = [
        ("Petr má auto.", session.utter("Petr má auto.", petr_has_car())),
        (
            "!÷ Byli to dva Petrové.",
            session.play(
                splits("Byli to dva.", Entity("Petr"), ("Petr_1", "Petr_2"), "dva")
            ),
        ),
        ("Petr má auto.", session.utter("Petr má auto.", petr_has_car())),
    ]
    for label, result in steps:
        echo(f"\n» {label}")
        for line in result.lines:
            echo(f"   {line}")
    echo("\n### I — mezera jako nabídka (K‑9)")
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("v1"), Group("vrabec")))
    engine = Engine(kb)
    asked = member_of(Entity("v1"), Group("tučňák"))
    echo(f"\n» ? {asked}   → {engine.ask(asked).status.value}")
    for line in GapFinder(engine).explain(asked).render():
        echo(f"   {line}")
    echo("\n" + "=" * 72)
