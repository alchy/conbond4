"""Pod `∀` zužuje přívlastek doménu — B‑31.

Čtyři obyčejné české věty a poslední odpověď byla nepravda, kterou nikdo
neřekl:

    „Chov zvířat jako domácích mazlíčků může vyvolávat obavy."
        → ✓ zapsáno  moci_vyvolávat(co:∃obava, kdo:**∀chov**)
    „Velkochov je druh chovu."      → subset(velkochov, chov)
    „Může velkochov vyvolávat obavy?"  → **ANO**

Věta mluví o chovu zvířat JAKO DOMÁCÍCH MAZLÍČKŮ; do báze šlo `∀chov`,
tedy o všem chovu. O velkochovu neřekl nikdo nic a ta odpověď stojí jen
na tom, že restrikce vypadla.

**Pod `∀` není přívlastek vztah vedle věty, je to ZÚŽENÍ DOMÉNY.** Je to
táž monotonie naruby jako u záporu (B‑29), jen se na ni žádná stráž
nedívala: stráž částečného zápisu hlídá vynechané ROLE a přívlastek rolí
není.
"""

from __future__ import annotations

from core_semantics.ast import Group, Quantifier, QueryStatus, atom, role, subset_of
from core_semantics.cascade import restrictive_attributes
from core_semantics.engine import Engine
from core_semantics.lexicon import (
    LearnedPattern,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session

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


def sentence(kvantifikator_case: str = "Nom") -> Reading:
    """«Chov zvířat vyvolává obavy.» — `zvířat` zužuje doménu `chovu`."""
    return Reading(
        tokens=(
            tok(1, "Chov", "chov", "NOUN", 3, "nsubj",
                Case=kvantifikator_case, Gender="Masc", Number="Sing"),
            tok(2, "zvířat", "zvíře", "NOUN", 1, "nmod",
                Case="Gen", Gender="Neut", Number="Plur"),
            tok(3, "vyvolává", "vyvolávat", "VERB", 0, "root",
                Number="Sing", Polarity="Pos"),
            tok(4, "obavy", "obava", "NOUN", 3, "obj",
                Case="Acc", Gender="Fem", Number="Plur"),
            tok(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )


TEXT = "Chov zvířat vyvolává obavy."


class _Oracle:
    provenance = STAMP

    def __init__(self, reading: Reading) -> None:
        self._reading = reading

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._reading,))


def _session(*, podmet: Operation) -> tuple[Session, _Oracle]:
    """Sezení, kde podmět dostane `∀` (nebo `∃` u protipříkladu)."""
    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(lemma="", upos="NOUN", number="Sing", case="Nom",
                            deprel="nsubj"),
            operation=podmet,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(lemma="", upos="NOUN", number="Plur", case="Acc",
                            deprel="obj"),
            operation=Operation.EXISTS,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    return Session(lexicon=lexicon), _Oracle(sentence())


def test_a_restrictive_attribute_on_a_forall_role_is_seen() -> None:
    """Rozpozná se to z KVANTIFIKÁTORU role, ne z podoby přívlastku."""
    session, oracle = _session(podmet=Operation.FOR_ALL)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    assert restrictive_attributes(result.predication) == ("kdo",)


def test_under_forall_the_sentence_is_not_written(  # noqa: D401
) -> None:
    """PÁTÁ POLOŽKA ZÁKAZU. Věta se nezapíše a je vidět PROČ."""
    session, oracle = _session(podmet=Operation.FOR_ALL)
    result = session.utter(TEXT, oracle)
    assert result.statement_id is None
    assert any("ZUŽUJE DOMÉNU" in line for line in result.lines)
    assert list(session.kb.active()) == [], "do báze nejde nic"


def test_the_four_sentence_sequence_ends_in_unknown() -> None:
    """TA REPRODUKCE, KTERÁ MĚLA SKONČIT NEVÍM.

    Do B‑31 vyšlo ANO: věta o chovu ZVÍŘAT se zapsala jako tvrzení
    o VŠEM chovu a `subset(velkochov, chov)` z něj pak odvodil něco,
    co nikdo neřekl."""
    session, oracle = _session(podmet=Operation.FOR_ALL)
    session.utter(TEXT, oracle)

    # „Velkochov je druh chovu." — zapsáno rovnou, aby zkouška měřila
    # B‑31 a ne cestu, kterou se ta věta do báze dostane.
    session.kb.attach(
        subset_of(Group("velkochov"), Group("chov")),
        provenance="test: velkochov je druh chovu",
    )

    otazka = atom(
        "vyvolávat",
        role("kdo", Group("velkochov"), Quantifier.FOR_ALL),
        role("co", Group("obava"), Quantifier.EXISTS),
    )
    assert Engine(session.kb).ask(otazka).status is QueryStatus.UNKNOWN, (
        "o velkochovu neřekl nikdo nic a ta věta mluvila o chovu ZVÍŘAT"
    )


def test_under_exists_the_sentence_is_written_as_before() -> None:
    """PROTIPŘÍKLAD, BEZ KTERÉHO BY SE ZÁKAZ PŘEČETL NARUBY.

    `∃` a konkrétní uzel se NEMĚNÍ: tam vynechání přívlastku tvrzení
    OSLABUJE a slabší tvrzení není nepravda. Kdo si B‑31 přečte jako
    „přívlastek blokuje zápis", zablokuje i tohle."""
    session, oracle = _session(podmet=Operation.EXISTS)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    assert restrictive_attributes(result.predication) == ()
    assert result.statement_id is not None, "∃ se zapisuje dál"
