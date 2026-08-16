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
from core_semantics.session import Session, answers_here

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
    # DVA ZÁKAZY NAJEDNOU *(B‑31 a W‑103)*: restrikce i `∀` z osiva.
    # Test měří ten první, takže se `∀` nejdřív potvrdí — a věta se
    # PŘESTO nezapíše, protože přívlastek zužuje doménu.
    potvrzeno = session.play(
        answers_here("O každém.", result.predication, "kdo", Operation.FOR_ALL)
    ) if result.predication is not None else result
    assert potvrzeno.statement_id is None
    assert any("ZUŽUJE DOMÉNU" in line for line in potvrzeno.lines)
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


# --------------------------------------------------------------------------
# Původ kvantifikátoru — W‑103
# --------------------------------------------------------------------------


def test_the_quantifier_carries_its_authority() -> None:
    """`source` říká, KTERÝ TVAR se trefil; autorita říká, NA ČÍ
    ZODPOVĚDNOST to je *(W‑103)*.

    Po odpovědi na tuhle větu, u jiné věty téhož tvaru i u čistého osiva
    stojí v `source` týž řetězec — rozlišit se to podle něj nedá."""
    from core_semantics.cascade import AUTHORITY_SEED

    session, oracle = _session(podmet=Operation.FOR_ALL)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    role = result.predication.role("kdo")
    assert role is not None
    kdo = result.predication.reading("kdo")
    assert kdo is not None
    assert kdo.quantifier_authority == AUTHORITY_SEED
    assert kdo.source == "tvar NOUN/Sing/Nom/nsubj", (
        "a `source` mluví dál o tvaru — ta dvě pole odpovídají na jiné otázky"
    )


def test_an_answer_marks_the_role_as_affirmed() -> None:
    """Odpověď `→∀` je jediné místo, kde kvantifikátor stojí na tom, že
    ho někdo pro TU věc řekl."""
    from core_semantics.cascade import AUTHORITY_AFFIRMED
    from core_semantics.lexicon import czech_seed
    from core_semantics.session import answers_quantifier

    session = Session(lexicon=czech_seed())
    oracle = _Oracle(sentence())
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    ceka = [
        r for r in result.predication.roles
        if r.pending is not None and r.name == "kdo"
    ]
    assert ceka, "bez naučeného tvaru se systém ptá"
    signatura = ceka[0].pending
    assert signatura is not None

    po = session.play(
        answers_quantifier(
            "O každém.", result.predication, signatura, Operation.FOR_ALL
        )
    )
    assert po.predication is not None
    kdo = po.predication.reading("kdo")
    assert kdo is not None and kdo.quantifier_authority == AUTHORITY_AFFIRMED


def test_a_seed_forall_does_not_reach_the_base() -> None:
    """`∀` Z OSIVA SE NEZAPISUJE *(W‑103)*.

    „Vesmír se rozšířil do dnešní podoby." dostalo `∀vesmír` jen proto,
    že se trefil tvar — a po `subset(paralelní_vesmír, vesmír)` z toho
    plyne tvrzení, které v té větě není. Čtení se nemění a systém se
    PTÁ; bez té otázky by zákaz byl díra místo otázky."""
    session, oracle = _session(podmet=Operation.FOR_ALL)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    assert result.statement_id is None
    assert result.question is not None and "KAŽDÉM" in result.question
    assert "∀chov" in str(result.predication), "čtení `∀` má dál"


def test_an_affirmation_opens_the_write() -> None:
    """`→∀1` zápis ODEMYKÁ — jinak by to byla díra místo otázky."""
    session, oracle = _session(podmet=Operation.FOR_ALL)
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    po = session.play(
        answers_here("O každém.", result.predication, "kdo", Operation.FOR_ALL)
    )
    # Věta má i restriktivní přívlastek (B‑31), takže se pořád nezapíše —
    # ale důvod se změnil a je vidět, že licence `∀` už platí.
    assert not any("je z OSIVA" in line for line in po.lines)


def test_a_determiner_licenses_the_write() -> None:
    """DETERMINÁTOR JE VYSLOVENÝ, NE UHODNUTÝ *(W‑103)*. „KAŽDÝ chov…"
    říká `∀` slovem, takže licence nestojí na tvaru."""
    from core_semantics.cascade import AUTHORITY_DETERMINER

    s_determinatorem = Reading(
        tokens=(
            tok(1, "Každý", "každý", "DET", 2, "det",
                Case="Nom", Gender="Masc", Number="Sing", PronType="Tot"),
            tok(2, "chov", "chov", "NOUN", 3, "nsubj",
                Case="Nom", Gender="Masc", Number="Sing"),
            tok(3, "vyvolává", "vyvolávat", "VERB", 0, "root",
                Number="Sing", Polarity="Pos"),
            tok(4, "obavy", "obava", "NOUN", 3, "obj",
                Case="Acc", Gender="Fem", Number="Plur"),
            tok(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )
    session, _ = _session(podmet=Operation.FOR_ALL)
    result = session.utter(TEXT, _Oracle(s_determinatorem))
    assert result.predication is not None
    kdo = result.predication.reading("kdo")
    assert kdo is not None and kdo.quantifier_authority == AUTHORITY_DETERMINER
    assert result.statement_id is not None, "vyslovené `∀` zápis licencuje"


def test_a_query_is_answered_even_when_the_forall_came_from_seed() -> None:
    """ZÁKAZ SE TÝKÁ TVRZENÍ, NE DOTAZU *(B‑32)*.

    Licence stojí na jediné větě: `∀` je jediný kvantifikátor, jehož
    chyba TVRZENÍ zesiluje. Otázka ale netvrdí nic — dotaz bázi nemění
    (I‑12) — takže na ní není co zesilovat a verdikt musí přijít.

    Do B‑32 zůstalo „Štěká jezevčík?" bez verdiktu, zatímco „Štěká
    KAŽDÝ jezevčík?" odpovědělo ANO; to jedno slovo je přitom v DOTAZU,
    ne v tom, co se zapisuje."""
    from core_semantics.ast import Quantifier, QueryStatus, atom, role
    from core_semantics.engine import Engine

    # „Každý pes štěká." — `∀` řečené SLOVEM, tedy zapsatelné.
    veta = Reading(
        tokens=(
            tok(1, "Každý", "každý", "DET", 2, "det",
                Case="Nom", Gender="Masc", Number="Sing", PronType="Tot"),
            tok(2, "pes", "pes", "NOUN", 3, "nsubj",
                Case="Nom", Gender="Masc", Number="Sing"),
            tok(3, "štěká", "štěkat", "VERB", 0, "root",
                Number="Sing", Polarity="Pos"),
            tok(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )
    session, _ = _session(podmet=Operation.FOR_ALL)
    zapsano = session.utter("Každý pes štěká.", _Oracle(veta))
    assert zapsano.statement_id is not None, "`∀` řečené slovem se zapíše"

    session.kb.attach(
        subset_of(Group("jezevčík"), Group("pes")),
        provenance="test: jezevčík je druh psa",
    )
    verdikt = Engine(session.kb).ask(
        atom("štěkat", role("kdo", Group("jezevčík"), Quantifier.FOR_ALL))
    )
    assert verdikt.status is QueryStatus.PROVEN_TRUE
    assert verdikt.proof is not None and verdikt.proof.leaves(), (
        "a odpověď má důkaz — to je ta schopnost, kterou zákaz bral"
    )
