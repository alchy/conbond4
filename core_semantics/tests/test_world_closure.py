"""UZAVŘENÍ SVĚTA z české věty — jediné místo, kde absence dá „ne".

**Proč to má vlastní soubor.** `complete(g)` není další jádrový predikát
v řadě. Je to jediný výrok v systému, který mění, co znamená TICHO: do něj
platí I‑21 („absence není negace") bez výjimky, od něj se o každém, kdo ve
výčtu není, odpovídá `N` místo `U`.

**Cena chyby je tu nejvyšší v celém projektu.** Špatně zapsané uzavření
vyrobí `N` tam, kde má být `U` — nevědomost vydávaná za znalost, tedy
právě to, co tenhle systém dělat nesmí. Proto se `complete` nedosadí
NIKDY, ani při jednoznačném tvaru, a proto se sem měří i cesta zpátky:
prohlášení je DEKLARACE, ne trvalá vlastnost světa.

Do dneška se `complete` měřilo jen z formulí — táž třída jako `before`
před #59, `disjoint` před #64 a `same_as` před #66. Schopnost v jádře, ke
které jazyk nevede, se nedá odlišit od schopnosti, která nefunguje.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    Entity,
    Group,
    QueryStatus,
    UnsafeRule,
    Variable,
    atom,
    role,
    complete_of,
    member_of,
)
from core_semantics.cascade import ROLE_SUBJECT, completeness_shape
from core_semantics.engine import Engine
from core_semantics.oracle import Reading, RecordedOracle, Token, Utterance
from core_semantics.session import Session, Turn, TurnResult, declares_complete, revokes
from core_semantics.storage import KnowledgeBase
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


COP = dict(Aspect="Imp", Mood="Ind", Person="3", Tense="Pres", VerbForm="Fin", Voice="Act")


def member(name: str, group: str) -> Reading:
    return Reading(
        tokens=(
            w(1, name, name, "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
            w(2, "je", "být", "AUX", 3, "cop", Number="Sing", Polarity="Pos", **COP),
            w(3, group, group, "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
            w(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )


def query(name: str, group: str) -> Reading:
    return Reading(
        tokens=(
            w(1, "Je", "být", "AUX", 3, "cop", Number="Sing", Polarity="Pos", **COP),
            w(2, name, name, "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
            w(3, group, group, "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
            w(4, "?", "?", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )


ALL_DOGS = Reading(
    tokens=(
        w(1, "To", "ten", "DET", 4, "nsubj", Case="Nom", Gender="Neut", Number="Sing", PronType="Dem"),
        w(2, "jsou", "být", "AUX", 4, "cop", Number="Plur", Polarity="Pos", **COP),
        w(3, "všichni", "všechen", "DET", 4, "det", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur", PronType="Tot"),
        w(4, "psi", "pes", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur"),
        w(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)

#: „Všichni psi štěkají." — totalizace BEZ demonstrativa. Obecné tvrzení
#: o psech, ne prohlášení o tom, KTEŘÍ psi jsou.
ALL_DOGS_BARK = Reading(
    tokens=(
        w(1, "Všichni", "všechen", "DET", 3, "det", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur", PronType="Tot"),
        w(2, "psi", "pes", "NOUN", 3, "nsubj", Animacy="Anim", Case="Nom", Gender="Masc", Number="Plur"),
        w(3, "štěkají", "štěkat", "VERB", 0, "root", Number="Plur", Polarity="Pos", **COP),
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


REX = "Rex je pes."
ALIK = "Alík je pes."
MOUREK = "Mourek je kocour."
ASK = "Je Mourek pes?"
CLOSE = "To jsou všichni psi."
BARK = "Všichni psi štěkají."


def oracle() -> _Recorded:
    return _Recorded(
        {
            REX: member("Rex", "pes"),
            ALIK: member("Alík", "pes"),
            MOUREK: member("Mourek", "kocour"),
            ASK: query("Mourek", "pes"),
            CLOSE: ALL_DOGS,
            BARK: ALL_DOGS_BARK,
        }
    )


def enumerated() -> Session:
    """Sezení s výčtem dvou psů a s uzlem mimo něj."""
    session = Session()
    for text in (REX, ALIK, MOUREK):
        session.utter(text, oracle())
    return session


# --------------------------------------------------------------------------
# Tvar: co uzavření NAVRHUJE a co ne
# --------------------------------------------------------------------------


def test_the_presentational_total_construction_proposes_a_closure() -> None:
    """„To jsou všichni psi." — demonstrativum v podmětu plus totalizující
    determinátor. Nese to gramatika, ne slovník."""
    session = enumerated()
    result = session.utter(CLOSE, oracle())
    assert result.predication is not None
    assert result.predication.pending_complete == "pes"


def test_a_general_claim_about_all_dogs_closes_nothing() -> None:
    """„Všichni psi štěkají." má TÝŽ determinátor a uzavírat nesmí. Mluví
    O psech, ne o tom, KTEŘÍ psi jsou — a zavřít svět na základě věty,
    která o výčtu vůbec nemluví, by bylo to nejhorší, co tenhle tvar může
    udělat."""
    session = enumerated()
    result = session.utter(BARK, oracle())
    assert result.predication is not None
    assert result.predication.pending_complete == ""


def test_the_shape_returns_a_group_not_a_kernel_atom() -> None:
    """Vrací se SKUPINA, ne `complete(g)`. Co ten tvar znamená v jádře,
    rozhoduje člověk tahem — kdyby to rozhodovala tahle funkce, byl by
    v interpretu schovaný seznam, kdy se smí zavřít svět."""
    session = enumerated()
    predication = session.utter(CLOSE, oracle()).predication
    assert predication is not None
    assert completeness_shape(predication, ALL_DOGS) == "pes"


# --------------------------------------------------------------------------
# Návrh NIKDY nezapisuje
# --------------------------------------------------------------------------


def test_nothing_is_written_while_the_closure_is_only_proposed() -> None:
    """Táž zábrana jako u nerozhodnuté relace (B‑17), jen naléhavější:
    bez ní by se zapsal obyčejný vztah `být` o množině psů — tvrzení,
    které nikdo neřekl — a `complete(pes)`, tedy to, co člověk MYSLEL, by
    v bázi nebylo."""
    session = enumerated()
    before = len(session.program())
    result = session.utter(CLOSE, oracle())
    assert result.statement_id is None
    assert len(session.program()) == before


def test_the_question_names_the_consequence_not_the_ignorance() -> None:
    """Jediná otázka v systému, která člověka upozorňuje na DŮSLEDEK.
    U ostatních systém neví a ptá se; tady ví přesně, co se stane."""
    session = enumerated()
    question = session.utter(CLOSE, oracle()).question
    assert question is not None
    assert "NE" in question and "NEVÍM" in question


def test_the_closure_teaches_nothing_so_the_next_one_asks_again() -> None:
    """Uzavření světa NENÍ vlastnost jazyka. Že mluvčí dopočítal své psy,
    neopravňuje zavřít tytéž psy podruhé bez zeptání — a kdyby se tvar
    naučil, druhá věta by se už neptala."""
    session = enumerated()
    session.utter(CLOSE, oracle())
    session.play(declares_complete("Ano.", Group("pes")))
    again = session.utter(CLOSE, oracle())
    assert again.predication is not None
    assert again.predication.pending_complete == "pes", (
        "tvar se nesmí naučit: uzavření je epistemický stav mluvčího, "
        "ne konstrukce češtiny"
    )
    assert again.statement_id is None


# --------------------------------------------------------------------------
# Celý kruh: U → prohlášení → N → odvolání → U
# --------------------------------------------------------------------------


def test_before_the_declaration_the_answer_is_unknown() -> None:
    """Otevřený svět. Že Mourek v seznamu psů není, o něm NEROZHODUJE."""
    session = enumerated()
    assert session.utter(ASK, oracle()).status is QueryStatus.UNKNOWN


def test_after_the_declaration_the_absence_becomes_a_denial() -> None:
    session = enumerated()
    session.utter(CLOSE, oracle())
    session.play(declares_complete("Ano.", Group("pes")))
    assert session.utter(ASK, oracle()).status is QueryStatus.PROVEN_FALSE


def test_the_denial_cites_the_declaration_and_the_enumeration() -> None:
    """OBĚ půlky. Důkaz, který cituje jen prohlášení, se nedá
    zkontrolovat — čtenář nevidí, NAD ČÍM se zavíralo, a přitom právě to
    rozhoduje o tom, jestli dotazovaný ve výčtu je."""
    session = enumerated()
    session.utter(CLOSE, oracle())
    declared = session.play(declares_complete("Ano.", Group("pes")))
    session.utter(ASK, oracle())
    found = Engine(session.kb).ask(member_of(Entity("Mourek"), Group("pes")))
    assert found.status is QueryStatus.PROVEN_FALSE
    assert found.proof is not None
    cited = set(found.proof.leaves())
    assert declared.statement_id in cited, "prohlášení musí být vidět"
    stated = {
        statement.id
        for statement in session.kb.active()
        if statement.formula == member_of(Entity("Rex"), Group("pes"))
        or statement.formula == member_of(Entity("Alík"), Group("pes"))
    }
    assert stated <= cited, "VÝČET taky — bez něj se závěr nedá ověřit"


def test_revoking_the_declaration_returns_the_answer_to_unknown() -> None:
    """Prohlášení je DEKLARACE, ne trvalá vlastnost světa. Kdyby nešlo
    odvolat, byl by to jediný nevratný krok v systému."""
    session = enumerated()
    session.utter(CLOSE, oracle())
    declared = session.play(declares_complete("Ano.", Group("pes")))
    assert declared.statement_id is not None
    session.play(revokes("Počkej.", declared.statement_id, "výčet nebyl hotový"))
    assert session.utter(ASK, oracle()).status is QueryStatus.UNKNOWN


def test_a_member_of_the_closed_group_is_still_proven() -> None:
    """Uzavření popírá jen ty, kdo ve výčtu NEJSOU. Kdyby popřelo i členy,
    bylo by to obrácené naruby a nikdo by si toho nemusel všimnout — obě
    odpovědi by se jen změnily z `A` na `N`."""
    session = enumerated()
    session.utter(CLOSE, oracle())
    session.play(declares_complete("Ano.", Group("pes")))
    engine = Engine(session.kb)
    found = engine.ask(member_of(Entity("Rex"), Group("pes")))
    assert found.status is QueryStatus.PROVEN_TRUE


# --------------------------------------------------------------------------
# Co uzavření NESMÍ: vzniknout jinak než prohlášením
# --------------------------------------------------------------------------


def test_no_rule_may_produce_a_closure() -> None:
    """`complete` je v `PROTECTED_HEADS`, takže pravidlo, které by ho
    vyrábělo, se odmítne U ZÁPISU. Uzavření světa je lidské prohlášení;
    odvozené uzavření by znamenalo, že si systém sám rozhodl, že už nic
    dalšího neexistuje."""
    kb = KnowledgeBase()
    with pytest.raises(UnsafeRule):
        kb.attach_rule(
            complete_of(Group("pes")),
            (member_of(Variable("x"), Group("pes")),),
            rule_id="uzavri_kdyz_nekdo_je",
        )


def test_a_closure_never_appears_without_someone_declaring_it() -> None:
    """Celá doména bez tahu `!∀`: ať se řekne cokoli, `complete` v bázi
    není. Tohle je ta kontrola, která by chytila tichý default."""
    session = enumerated()
    session.utter(CLOSE, oracle())
    session.utter(BARK, oracle())
    assert all(
        not (isinstance(statement.formula, type(complete_of(Group("x"))))
             and statement.formula.predicate == "complete")
        for statement in session.kb.active()
    )


def test_the_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("UZAVŘENÍ SVĚTA Z ČESKÉ VĚTY")
    echo("=" * 72)
    session = enumerated()
    echo("» výčet: Rex, Alík · mimo výčet: Mourek")
    before = session.utter(ASK, oracle()).status
    assert before is not None
    echo(f"   před prohlášením:  {before.name}")
    session.utter(CLOSE, oracle())
    declared = session.play(declares_complete("Ano, uzavři to.", Group("pes")))
    for line in declared.lines:
        echo(f"   {line}")
    after = session.utter(ASK, oracle()).status
    assert after is not None
    echo(f"   po prohlášení:     {after.name}")
    assert declared.statement_id is not None
    session.play(revokes("Počkej.", declared.statement_id, "výčet nebyl hotový"))
    back = session.utter(ASK, oracle()).status
    assert back is not None
    echo(f"   po odvolání:       {back.name}")
    echo("=" * 72)


def _shared_reading(predicate: str, lemma: str) -> Reading:
    """„Petr a Jana <přišli>." — dvě jména v jedné roli."""
    return Reading(
        tokens=(
            w(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            w(2, "a", "a", "CCONJ", 3, "cc"),
            w(3, "Jana", "Jana", "PROPN", 1, "conj", Case="Nom", Gender="Fem", Number="Sing"),
            w(4, predicate, lemma, "VERB", 0, "root", Gender="Masc", Number="Plur", Polarity="Pos"),
            w(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )


def _one_reading(subject: str, predicate: str, lemma: str) -> Reading:
    return Reading(
        tokens=(
            w(1, subject, subject, "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            w(2, predicate, lemma, "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            w(3, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


def _two_sentence_session() -> tuple[Session, Turn, RecordedOracle, str]:
    """Sezení, ve kterém věta se dvěma členy v jedné roli čeká na `→&`;
    druhá promluva o TÉMŽE uzlu se dohraje až v samotné zkoušce."""
    from core_semantics.session import decides_sharing
    from core_semantics.tests import golden

    first, second = "Petr a Jana přišli.", "Petr odešel."
    oracle = RecordedOracle(
        {
            first: Utterance(text=first, readings=(_shared_reading("přišli", "přijít"),)),
            second: Utterance(text=second, readings=(_one_reading("Petr", "odešel", "odejít"),)),
        }
    )
    session = Session(lexicon=golden.golden_lexicon())
    asked = session.utter(first, oracle)
    assert asked.predication is not None
    rozhodnuti = decides_sharing(
        "Každý zvlášť.",
        asked.predication,
        _shared_reading("přišli", "přijít"),
        distributive=True,
    )
    return session, rozhodnuti, oracle, second


def test_a_turn_reports_every_statement_it_wrote() -> None:
    """TAH, KTERÝ ZAPSAL VÍC VÝROKŮ, JE VŠECHNY OHLÁSÍ *(B‑26)*.
    `statement_id` nese jen ten první; kdo tu větu chce vzít zpět, neměl
    podle čeho."""
    session, rozhodnuti, _, _ = _two_sentence_session()
    written = session.play(rozhodnuti)
    assert len(written.statements) > 1
    assert written.statement_id in written.statements
    assert written.utterance, "promluva musí mít rukojeť"


def test_revoking_an_utterance_takes_back_both_halves() -> None:
    """ODVOLAT VĚTU JDE CELOU *(B‑26)*. „Petr a Jana přišli." zapsala dvě
    tvrzení; `revoke` po jednom id strhlo jen půlku a báze druhou
    polovinu tvrdila dál — „přišla Jana?" odpovídalo `A` na větu, kterou
    nikdo nedržel."""
    session, rozhodnuti, oracle, druha = _two_sentence_session()
    written = session.play(rozhodnuti)
    session.utter(druha, oracle)
    engine = Engine(session.kb)
    jana = atom("přijít", role(ROLE_SUBJECT, Entity("Jana")))
    assert engine.ask(jana).status is QueryStatus.PROVEN_TRUE
    session.kb.revoke_utterance(written.utterance, "zkouška")
    assert engine.ask(jana).status is QueryStatus.UNKNOWN
    petr = atom("přijít", role(ROLE_SUBJECT, Entity("Petr")))
    assert engine.ask(petr).status is QueryStatus.UNKNOWN


def test_revoking_an_utterance_spares_another_that_shares_a_node() -> None:
    """PROTIPŘÍKLAD: odvolání NESMÍ strhnout výrok z JINÉ promluvy, který
    jen sdílí uzel. Uzel není důvod k odvolání — kdyby byl, vzalo by
    „vezmi zpět tu větu" zpátky i věty, které nikdo neodvolával."""
    session, rozhodnuti, oracle, druha = _two_sentence_session()
    written = session.play(rozhodnuti)
    session.utter(druha, oracle)
    engine = Engine(session.kb)
    odesel = atom("odejít", role(ROLE_SUBJECT, Entity("Petr")))
    assert engine.ask(odesel).status is QueryStatus.PROVEN_TRUE
    session.kb.revoke_utterance(written.utterance, "zkouška")
    assert engine.ask(odesel).status is QueryStatus.PROVEN_TRUE, "cizí promluva zůstává"


def _partial_reading(with_operator: bool) -> Reading:
    """„Petr bydlel (pokud) v Praze." — okolnost bez jména, volitelně
    s operátorem, který pravdivost PODMIŇUJE."""
    tokens = [
        w(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "bydlel", "bydlet", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
        w(4, "v", "v", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
        w(5, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
        w(6, ".", ".", "PUNCT", 2, "punct"),
    ]
    if with_operator:
        tokens.insert(2, w(3, "pokud", "pokud", "SCONJ", 5, "mark"))
    return Reading(tokens=tuple(tokens), provenance=STAMP)


def _partial_setup(
    with_operator: bool = False,
) -> tuple[Session, Reading, RecordedOracle, str]:
    """Sezení připravené k `.utter(` — samotné čtení si každá zkouška
    zahraje sama, aby vstupním bodem prošla ONA, ne pomocná funkce."""
    from core_semantics.tests import golden

    text = "Petr bydlel v Praze."
    reading = _partial_reading(with_operator)
    oracle = RecordedOracle({text: Utterance(text=text, readings=(reading,))})
    return Session(lexicon=golden.golden_lexicon()), reading, oracle, text


def test_what_is_understood_is_written_and_the_rest_stays_open() -> None:
    """ZAPÍŠE SE TO, ČEMU SYSTÉM ROZUMÍ *(W‑79)*. Ve všech 154 větách
    korpusu, které dnes zákaz drží, je nepojmenovaná role JEN OKOLNOST —
    ani jednou `kdo`/`co`/`jak`. Vynechat ji znamená říct MÍŇ, a slabší
    tvrzení není nepravda."""
    session, _, oracle, text = _partial_setup()
    result = session.utter(text, oracle)
    assert result.statement_id is not None, "jádro věty se zapíše"
    ulozene = [str(st.formula) for st in session.kb.active() if str(st.formula).startswith("bydlet(")]
    assert ulozene == ["bydlet(kdo:Petr)"], f"bez okolnosti, ale bylo {ulozene}"
    assert "v+Loc" in (result.question or ""), "co se nezapsalo, zůstane otevřené"


def test_the_omitted_role_is_unknown_not_false() -> None:
    """NEGATIVNÍ KONTROLA: dotaz na vynechané dá `U`, ne `A` a ne `N`."""
    from core_semantics.ast import Place

    session, _, oracle, text = _partial_setup()
    session.utter(text, oracle)
    engine = Engine(session.kb)
    kde = atom(
        "bydlet",
        role(ROLE_SUBJECT, Entity("Petr")),
        role("kde", Place("Praha")),
    )
    assert engine.ask(kde).status is QueryStatus.UNKNOWN


def test_an_operator_that_changes_truth_blocks_the_partial_write() -> None:
    """PROTIPŘÍKLAD *(W‑79)*: věta, jejíž vynechaná část PODMIŇUJE
    pravdivost, se částečně NEZAPÍŠE — a řekne se proč. Rozhoduje TŘÍDA
    OPERÁTORŮ z lexikonu, tedy odvolatelná data, ne seznam vět."""
    session, _, oracle, text = _partial_setup(with_operator=True)
    result = session.utter(text, oracle)
    assert result.statement_id is None
    assert not [st for st in session.kb.active() if str(st.formula).startswith("bydlet(")]


def test_completing_a_sentence_leaves_one_statement_and_a_history() -> None:
    """DOPLNĚNÍ NEZALOŽÍ DRUHÝ VÝROK *(W‑79)*: částečný se ODVOLÁ, ne
    přepíše — báze je append‑only a auditovatelnost stojí na tom, že se
    nic nemaže. V historii proto stojí OBOJÍ."""
    from core_semantics.session import names_role

    session, reading, oracle, text = _partial_setup()
    session.utter(text, oracle)
    session.play(names_role("Je to místo.", reading, "v+Loc/Geo", "kde"))
    aktivni = [str(st.formula) for st in session.kb.active() if str(st.formula).startswith("bydlet(")]
    assert aktivni == ["bydlet(kde:Praha, kdo:Petr)"]
    duvody = [
        session.kb.inspect(st.id)[2]
        for st in session.kb.history()
        if str(st.formula).startswith("bydlet(")
    ]
    assert "doplněno" in duvody, "historie ukáže, že tam částečný výrok byl"
