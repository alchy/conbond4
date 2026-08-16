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
from core_semantics.ast import Quantifier
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


# --------------------------------------------------------------------------
# GENITIVNÍ PŘÍVLASTEK — druhý výrok vedle věty (W‑39)
# --------------------------------------------------------------------------
#
# „Chov zvířat je náročný." Genitiv visí jako `nmod` pod JMÉNEM, ne pod
# přísudkem, takže to není role predikace — predikace nese role slovesa
# a „zvířat" není argument „být". Je to vztah dvou jmen uvnitř fráze,
# tedy druhý výrok vedle věty; týž tvar, jaký má přivlastnění (`→'`).
#
# Měřením doložených významů je PĚT (předmět děje, původce, nositel
# vlastnosti, část z celku, míra a druh) a liší se PRÁVĚ TÍM, kterou roli
# genitiv v reifikovaném vztahu plní. Menu proto není nový druh
# rozhodnutí — je to otázka na jméno role.

BREEDING = Reading(
    tokens=(
        w(1, "Chov", "chov", "NOUN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
        w(2, "zvířat", "zvíře", "NOUN", 1, "nmod", Case="Gen", Number="Plur", Gender="Neut"),
        w(3, "je", "být", "AUX", 4, "cop", Polarity="Pos", **COP),
        w(4, "náročný", "náročný", "ADJ", 0, "root", Case="Nom", Number="Sing", Gender="Masc"),
        w(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)

CARE = Reading(
    tokens=(
        w(1, "Péče", "péče", "NOUN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Fem"),
        w(2, "majitele", "majitel", "NOUN", 1, "nmod", Case="Gen", Number="Sing", Gender="Masc"),
        w(3, "je", "být", "AUX", 4, "cop", Polarity="Pos", **COP),
        w(4, "nutná", "nutný", "ADJ", 0, "root", Case="Nom", Number="Sing", Gender="Fem"),
        w(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)

BREEDING_TEXT = "Chov zvířat je náročný."
CARE_TEXT = "Péče majitele je nutná."


def _attribute_session() -> tuple[Session, _Recorded]:
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation,
        PatternStatus,
        Trigger,
        czech_seed,
    )

    lexicon = czech_seed()
    for upos, deprel in (("NOUN", "nsubj"), ("ADJ", "root")):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number="Sing", case="Nom", deprel=deprel
                ),
                operation=Operation.SELF,
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    return Session(lexicon=lexicon), _Recorded(
        {BREEDING_TEXT: BREEDING, CARE_TEXT: CARE}
    )


def test_the_sentence_is_written_even_though_the_attribute_waits() -> None:
    """Větě nechybí PREDIKÁT, chybí jí PŘÍVLASTEK. Blokovat kvůli němu
    zápis by znamenalo zadržet větu kvůli něčemu, co v ní není."""
    session, oracle = _attribute_session()
    result = session.utter(BREEDING_TEXT, oracle)
    assert result.statement_id is not None
    assert result.question is not None
    assert result.predication is not None
    assert result.predication.pending_attribute == (("chov", "zvíře", 2, ""),)


def test_the_attribute_is_not_reported_as_a_dropped_member() -> None:
    """Dvě hlášky o jedné věci, které si odporují, jsou horší než jedna:
    systém v témže tahu říká, že na přívlastek ČEKÁ, takže hlásit u něj
    „pro tenhle vztah role není" je nepravda (táž třída jako W‑20)."""
    session, oracle = _attribute_session()
    trace = " ".join(session.utter(BREEDING_TEXT, oracle).lines)
    assert "PŘÍVLASTEK" in trace
    assert "zvířat" not in trace.split("ZAHOZENO")[-1] if "ZAHOZENO" in trace else True


def test_the_second_statement_needs_the_answer() -> None:
    """Bez odpovědi druhý výrok NEVZNIKNE — a věta přesto stojí."""
    from core_semantics.ast import Atom

    session, oracle = _attribute_session()
    session.utter(BREEDING_TEXT, oracle)
    assert not any(
        isinstance(statement.formula, Atom)
        and statement.formula.predicate == "chov"
        for statement in session.kb.active()
    )


def test_the_same_form_can_take_a_different_role() -> None:
    """„chov zvířat" a „péče majitele" mají TÝŽ TVAR a OPAČNÝ SMĚR:
    zvířata se chovají, kdežto majitel pečuje."""
    from core_semantics.session import names_attribute

    session, oracle = _attribute_session()
    session.utter(BREEDING_TEXT, oracle)
    first = session.play(names_attribute("Předmět.", "chov", "zvíře", "co"))
    session.utter(CARE_TEXT, oracle)
    second = session.play(names_attribute("Původce.", "péče", "majitel", "kdo"))
    assert any("chov(co:∀zvíře)" in line for line in first.lines)
    assert any("péče(kdo:∀majitel)" in line for line in second.lines)


def test_nothing_is_learned_so_the_next_sentence_asks_again() -> None:
    """Kdyby se tvar naučil, druhá věta by se nezeptala — a přečetla by
    se podle první odpovědi, tedy NARUBY."""
    from core_semantics.session import names_attribute

    session, oracle = _attribute_session()
    session.utter(BREEDING_TEXT, oracle)
    session.play(names_attribute("Předmět.", "chov", "zvíře", "co"))
    again = session.utter(CARE_TEXT, oracle)
    assert again.predication is not None
    assert again.predication.pending_attribute == (("péče", "majitel", 2, ""),)
    assert again.question is not None and "přívlastek" in again.question


# --------------------------------------------------------------------------
# Předložkový přívlastek jména — W‑84
# --------------------------------------------------------------------------
#
# Rozhodnutí je o VÝZNAMU, ne o kódu: doplněk jména je vztah TOHO JMÉNA,
# ne role přísudku. „Petr má alergii na penicilin." netvrdí, že Petr „má
# na penicilin" — tvrdí, že má alergii, a ta alergie je na penicilin.
#
# Rozdíl mezi VAZBOU jména („alergie na penicilin") a jeho URČENÍM
# („pobyt v Berlíně") je skutečný, ale Z ROZBORU NEROZHODNUTELNÝ: `nmod`
# s `case` v obou. Systém ho proto NEROZHODUJE — obojí je vztah vedle
# věty a KTERÝ vztah to je, řekne dialog. Výčtem předložek se to
# rozhodnout nesmí (dvanáct instancí W‑32 … W‑83).

ALLERGY = "Petr má alergii na penicilin."
MEDICINE = "Jan má lék na bolest."


def _prepositional(subject: str, verb: str, head: str, head_form: str,
                   filler: str, filler_form: str) -> Reading:
    """«<Kdo> <sloveso> <jméno> na <doplněk>.» — doplněk visí pod JMÉNEM."""
    return Reading(
        tokens=(
            w(1, subject, subject, "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
            w(2, verb, verb, "VERB", 0, "root", Number="Sing", Polarity="Pos"),
            w(3, head_form, head, "NOUN", 2, "obj", Case="Acc", Number="Sing"),
            w(4, "na", "na", "ADP", 5, "case", AdpType="Prep", Case="Acc"),
            w(5, filler_form, filler, "NOUN", 3, "nmod", Case="Acc", Number="Sing"),
            w(6, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


def _prepositional_session() -> tuple[Session, _Recorded]:
    readings = {
        ALLERGY: _prepositional("Petr", "mít", "alergie", "alergii",
                                "penicilin", "penicilin"),
        MEDICINE: _prepositional("Jan", "mít", "lék", "lék",
                                 "bolest", "bolest"),
    }

    from core_semantics.lexicon import (
        LearnedPattern,
        Operation as _Operation,
        PatternStatus,
        Trigger,
        czech_seed,
    )

    # Kvantifikátor podmětu a předmětu není předmětem tohohle testu —
    # bez něj by se věta nezapsala a měřilo by se něco jiného.
    lexicon = czech_seed()
    for upos, case, deprel in (
        ("NOUN", "Nom", "nsubj"),
        ("NOUN", "Acc", "obj"),
    ):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number="Sing", case=case, deprel=deprel
                ),
                operation=_Operation.EXISTS,
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    return Session(lexicon=lexicon), _Recorded(readings)


def test_a_prepositional_complement_of_a_noun_is_not_a_role_of_the_verb() -> None:
    """NOVÉ ČTENÍ SE DOKLÁDÁ DOTAZEM, NE FORMULÍ *(W‑84)*.

    Do W‑84 se „na penicilin" pojmenovalo jako role věty a v bázi ležel
    výrok, že Petr něco „má na penicilin". Ta věta to netvrdí."""
    from core_semantics.engine import Engine
    from core_semantics.session import names_attribute

    session, oracle = _prepositional_session()
    result = session.utter(ALLERGY, oracle)
    assert result.predication is not None
    assert result.predication.pending_attribute == (
        ("alergie", "penicilin", 5, "nmod:na+Acc"),
    )
    session.play(
        names_attribute("Je to na co.", "alergie", "penicilin", "na co",
                        "nmod:na+Acc")
    )

    engine = Engine(session.kb)
    veta = atom("mít", role("co", Group("alergie"), Quantifier.EXISTS),
                role("kdo", Entity("Petr")))
    vztah = atom("alergie", role("na co", Group("penicilin"),
                                 Quantifier.FOR_ALL))
    jako_role = atom("mít", role("kdo", Entity("Petr")),
                     role("na co", Group("penicilin"), Quantifier.EXISTS))
    assert engine.ask(veta).status is QueryStatus.PROVEN_TRUE
    assert engine.ask(vztah).status is QueryStatus.PROVEN_TRUE, (
        "vztah vedle věty v bázi LEŽÍ — schopnost se přesunula"
    )
    assert engine.ask(jako_role).status is QueryStatus.UNKNOWN, (
        "penicilin jako role slovesa „mít“ je tvrzení, které ve větě není"
    )


def test_one_answer_closes_the_whole_class_of_shaped_attributes() -> None:
    """TŘÍDA SE MUSÍ ZAVÍRAT I V NOVÉM KANÁLU *(W‑84)*.

    I‑16 se odvolávala na třídu „lék na X, recept na Y". Kdyby se tvar
    přívlastku neučil, přesunutím pod vztah vedle věty by systém
    schopnost zavřít celou třídu ZTRATIL — a to je jiná změna než ta,
    která se schválila."""
    from core_semantics.engine import Engine
    from core_semantics.session import names_attribute

    session, oracle = _prepositional_session()
    session.utter(ALLERGY, oracle)
    session.play(
        names_attribute("Je to na co.", "alergie", "penicilin", "na co",
                        "nmod:na+Acc")
    )

    again = session.utter(MEDICINE, oracle)
    assert again.predication is not None
    assert again.predication.pending_attribute == (), "druhá věta se neptá"
    assert again.question is None or "přívlastek" not in again.question
    assert any("DOPLNĚNO" in line for line in again.lines)
    assert Engine(session.kb).ask(
        atom("lék", role("na co", Group("bolest"), Quantifier.FOR_ALL))
    ).status is QueryStatus.PROVEN_TRUE, (
        "druhá věta téže třídy zapsala vztah sama"
    )


def test_the_learned_attribute_shape_is_revocable_data() -> None:
    """Co se naučí odpovědí, jde odvolat — stejně jako u role (I‑16)."""
    from core_semantics.session import names_attribute

    session, oracle = _prepositional_session()
    session.utter(ALLERGY, oracle)
    session.play(
        names_attribute("Je to na co.", "alergie", "penicilin", "na co",
                        "nmod:na+Acc")
    )
    naucene = [m for m in session.lexicon.all_roles()
               if m.surface == "nmod:na+Acc"]
    assert naucene and "tah" in naucene[0].learned_from

    session.lexicon.revoke_role(naucene[0].key())
    znovu = session.utter(MEDICINE, oracle)
    assert znovu.predication is not None
    assert znovu.predication.pending_attribute != (), (
        "po odvolání se systém ptá zas — jinak by to nebyla data"
    )


def test_a_shaped_attribute_never_borrows_the_name_of_a_circumstance() -> None:
    """VLASTNÍ JMENNÝ PROSTOR *(W‑84)*. `na+Acc` u přísudku je okolnost
    slovesa, `nmod:na+Acc` je vztah jména. Kdyby splynuly, naučené jméno
    okolnosti by pojmenovalo přívlastek — a naopak."""
    from core_semantics.cascade import attribute_shape

    reading = _prepositional("Petr", "mít", "alergie", "alergii",
                             "penicilin", "penicilin")
    assert attribute_shape(reading.tokens[4], reading) == "nmod:na+Acc"
    session, oracle = _prepositional_session()
    session.lexicon.teach_role("na+Acc", "kam", learned_from="test")
    result = session.utter(ALLERGY, oracle)
    assert result.predication is not None
    assert result.predication.pending_attribute != (), (
        "jméno okolnosti se na přívlastek nesmí přenést"
    )


# --------------------------------------------------------------------------
# Povrchový tvar složeného uzlu — W‑77
# --------------------------------------------------------------------------


def _composed(head_form: str, head_lemma: str, attr_form: str,
              attr_lemma: str, *, attribute_first: bool) -> Reading:
    """«<fráze> roste.» — přívlastek stojí před hlavou, nebo za ní."""
    hlava, privlastek = (3, 2) if attribute_first else (2, 3)
    return Reading(
        tokens=tuple(sorted((
            w(hlava, head_form, head_lemma, "NOUN", 1, "nsubj",
              Case="Nom", Gender="Neut", Number="Plur"),
            w(privlastek, attr_form, attr_lemma, "ADJ", hlava, "amod",
              Case="Nom", Degree="Pos", Gender="Neut", Number="Plur"),
            w(1, "rostou", "růst", "VERB", 0, "root",
              Number="Plur", Polarity="Pos"),
            w(4, ".", ".", "PUNCT", 1, "punct"),
        ), key=lambda t: t.index)),
        provenance=STAMP,
    )


def _composed_session(reading: Reading) -> tuple[Session, _Recorded]:
    """Sezení, ve kterém se věta se složeným uzlem opravdu ZAPÍŠE."""
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation as _Operation,
        PatternStatus,
        Trigger,
        czech_seed,
    )

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="NOUN", number="Plur", case="Nom",
                deprel="nsubj"
            ),
            operation=_Operation.FOR_ALL,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    return Session(lexicon=lexicon), _Recorded({COMPOSED_TEXT: reading})


COMPOSED_TEXT = "Zdravotní rizika rostou."


def test_a_composed_node_keeps_the_word_order_of_the_sentence() -> None:
    """POŘADÍ JE POŘADÍ TEXTU *(W‑77)*.

    Pravidlo je napsané u data (W‑74) i u víceslovného jména (B‑21,
    W‑78) a u přívlastku se nedrželo: lepil se PŘED hlavu bez ohledu na
    to, kde stojí. „Zdravotní rizika **spojená** s domácími zvířaty"
    tak dávalo uzel `zdravotní_spojený_riziko` a zmínku „Zdravotní
    spojená rizika" — slovosled, který v té větě není. Změřeno na
    korpusu: 20 zmínek z 215."""
    from core_semantics.cascade import _composed_mention

    za = _composed("rizika", "riziko", "spojená", "spojený",
                   attribute_first=False)
    zmínka = _composed_mention(za.tokens[1], za)
    assert zmínka.lemma == "riziko_spojený"
    assert zmínka.form == "rizika spojená"

    pred = _composed("rizika", "riziko", "zdravotní", "zdravotní",
                     attribute_first=True)
    assert _composed_mention(pred.tokens[2], pred).form == "zdravotní rizika"


def test_what_the_composed_node_was_in_the_sentence_is_retrievable() -> None:
    """CO SE DÁ O SLOŽENÉM UZLU ZJISTIT *(W‑77)*. Dosud nic než jméno —
    a `∀různý_míra` je to jediné, co člověk v bázi čte."""
    reading = _composed("rizika", "riziko", "zdravotní", "zdravotní",
                        attribute_first=True)
    session, oracle = _composed_session(reading)
    session.utter(COMPOSED_TEXT, oracle)
    assert session.surface_of("riziko") is None, (
        "nesložený uzel se nepamatuje — byla by to kopie textu"
    )
    povrch = session.surface_of("zdravotní_riziko")
    assert povrch is not None
    assert povrch == ("zdravotní rizika", COMPOSED_TEXT)


def test_the_written_statement_says_what_its_composed_nodes_were() -> None:
    """Řádek `[UZLY: …]` je u ZAPSANÉHO výroku, ne u nezapsané věty —
    jinak by sliboval dohledatelnost něčeho, co v bázi není."""
    reading = _composed("rizika", "riziko", "zdravotní", "zdravotní",
                        attribute_first=True)
    session, oracle = _composed_session(reading)
    result = session.utter(COMPOSED_TEXT, oracle)
    assert result.statement_id is not None, (
        "test, který měří jen nezapsanou větu, tuhle větev nikdy nespustí"
    )
    uzly = [line for line in result.lines if "[UZLY:" in line]
    assert uzly and "„zdravotní rizika“" in uzly[0]
    assert "zdravotní_riziko" in uzly[0], "uzel i povrch, ne jen jeden"

    # A PROTIPŘÍKLAD: věta, která se nezapsala, dohledatelnost neslibuje.
    ceka, ceka_oracle = _prepositional_session()
    ceka_vysledek = ceka.utter(ALLERGY, ceka_oracle)
    assert ceka_vysledek.statement_id is not None
    assert not [line for line in ceka_vysledek.lines if "[UZLY:" in line], (
        "věta bez složeného uzlu ten řádek nemá"
    )


# --------------------------------------------------------------------------
# Doplnění pohlceného příčestí — W‑92
# --------------------------------------------------------------------------


def _participle(bez_predlozky: bool = False) -> Reading:
    """«Rizika spojená s domácími zvířaty rostou.» — `obl` pod příčestím."""
    tokens = [
        w(1, "Rizika", "riziko", "NOUN", 5, "nsubj",
          Case="Nom", Gender="Neut", Number="Plur"),
        w(2, "spojená", "spojený", "ADJ", 1, "amod",
          Case="Nom", Degree="Pos", Gender="Neut", Number="Plur",
          VerbForm="Part", Voice="Pass"),
        w(4, "zvířaty", "zvíře", "NOUN", 2, "obl:arg",
          Case="Ins", Gender="Neut", Number="Plur"),
        w(5, "rostou", "růst", "VERB", 0, "root",
          Number="Plur", Polarity="Pos"),
        w(6, ".", ".", "PUNCT", 5, "punct"),
    ]
    if not bez_predlozky:
        tokens.append(
            w(3, "s", "s", "ADP", 4, "case", AdpType="Prep", Case="Ins")
        )
    return Reading(
        tokens=tuple(sorted(tokens, key=lambda t: t.index)), provenance=STAMP
    )


def _participle_session(reading: Reading) -> tuple[Session, _Recorded]:
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation as _Operation,
        PatternStatus,
        Trigger,
        czech_seed,
    )

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(lemma="", upos="NOUN", number="Plur", case="Nom",
                            deprel="nsubj"),
            operation=_Operation.FOR_ALL,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    return Session(lexicon=lexicon), _Recorded({PARTICIPLE_TEXT: reading})


PARTICIPLE_TEXT = "Rizika spojená s domácími zvířaty rostou."


def test_a_complement_of_an_absorbed_participle_is_an_attribute() -> None:
    """POD JMÉNEM JE `nmod`, POD PŘÍČESTÍM `obl` *(W‑92)*.

    „Rizika **spojená** s domácími zvířaty" — `spojená` se pohltilo do
    uzlu `riziko_spojený`, ale jeho vlastní doplnění pod ním zůstalo
    viset a zahodilo se. Je to týž vztah vedle věty jako u W‑84, jen
    hlavou není samo jméno, ale díl složeného uzlu."""
    from core_semantics.cascade import genitive_attributes

    reading = _participle()
    session, oracle = _participle_session(reading)
    result = session.utter(PARTICIPLE_TEXT, oracle)
    assert result.predication is not None
    najdene = genitive_attributes(reading, result.predication)
    assert [(h, g, tvar) for h, g, _, tvar in najdene] == [
        ("riziko_spojený", "zvíře", "nmod:s+Ins:arg")
    ]
    assert not any(
        "zvířaty" in line and "ZAHOZENO" in line for line in result.lines
    )


def test_a_bare_case_under_a_participle_counts_but_is_not_learned() -> None:
    """„Studie provedená **institutem**" předložku nemá a genitiv to
    není. Bere se — je to týž vztah — ale TVAR ZŮSTÁVÁ PRÁZDNÝ, takže se
    neučí a ptá se u každé věty znovu. Že je holý instrumentál u trpného
    příčestí původce, je pravděpodobné, ale rozhodnout to v kódu by bylo
    rozhodnutí o významu (W‑84)."""
    from core_semantics.cascade import genitive_attributes

    reading = _participle(bez_predlozky=True)
    session, oracle = _participle_session(reading)
    result = session.utter(PARTICIPLE_TEXT, oracle)
    assert result.predication is not None
    najdene = genitive_attributes(reading, result.predication)
    assert [tvar for *_, tvar in najdene] == [""], "neučí se"


def test_an_obl_under_the_predicate_is_still_a_circumstance() -> None:
    """PROTIPŘÍKLAD, KTERÝ TU MUSÍ BÝT. `obl` pod PŘÍSUDKEM je okolnost,
    tedy role věty; vzít ji jako přívlastek by udělalo z místa a času
    vztah vedle věty."""
    from core_semantics.cascade import genitive_attributes

    reading = Reading(
        tokens=(
            w(1, "Petr", "Petr", "PROPN", 2, "nsubj",
              Case="Nom", Gender="Masc", Number="Sing"),
            w(2, "bydlí", "bydlet", "VERB", 0, "root",
              Number="Sing", Polarity="Pos"),
            w(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            w(4, "Praze", "Praha", "PROPN", 2, "obl",
              Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
            w(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )
    session, oracle = _participle_session(reading)
    result = session.utter(PARTICIPLE_TEXT, oracle)
    assert result.predication is not None
    assert genitive_attributes(reading, result.predication) == ()


def test_the_question_does_not_call_an_instrumental_a_genitive() -> None:
    """SYSTÉM NESMÍ ŘÍKAT O SVÉM VSTUPU NĚCO, CO NENÍ PRAVDA *(W‑93)*.

    Do W‑92 mohl být prázdný tvar jen holý genitiv pod jménem, takže si
    ta větev mohla dovolit mluvit o genitivu. W‑92 otevřela druhou cestu
    dovnitř — holý pád pod příčestím, typicky instrumentál původce — a
    text se nezměnil, takže se instrumentálu říkalo genitiv a odůvodnilo
    se to argumentem („chov zvířat" × „péče majitele"), který na něj
    neplatí."""
    from core_semantics.cascade import attribute_question

    reading = _participle(bez_predlozky=True)
    session, oracle = _participle_session(reading)
    result = session.utter(PARTICIPLE_TEXT, oracle)
    assert result.predication is not None
    otazka = attribute_question(result.predication, reading)
    assert otazka is not None
    assert "genitiv" not in otazka, "instrumentál není genitiv"
    assert "Ins" in otazka, "pád se čte z rozboru a je vidět"


def test_the_bare_genitive_keeps_its_own_sentence() -> None:
    """PROTIPŘÍKLAD: holý genitiv pod jménem si svou větu PONECHÁ i se
    svým důvodem. Kdyby se změnilo obojí, nebyla by to oprava nepravdy,
    ale nové pravidlo."""
    from core_semantics.cascade import attribute_question

    session, oracle = _attribute_session()
    result = session.utter(BREEDING_TEXT, oracle)
    assert result.predication is not None
    otazka = attribute_question(
        result.predication, oracle.parse(BREEDING_TEXT).readings[0]
    )
    assert otazka is not None
    assert "v genitivu" in otazka
    assert "„chov zvířat“" in otazka and "„péče majitele“" in otazka


def test_without_the_parse_the_question_claims_no_case_at_all() -> None:
    """Bez rozboru se otázka nálepky VZDÁ. Hádat pád z lemmatu by byla
    táž vada o patro níž."""
    from core_semantics.cascade import attribute_question

    reading = _participle(bez_predlozky=True)
    session, oracle = _participle_session(reading)
    result = session.utter(PARTICIPLE_TEXT, oracle)
    assert result.predication is not None
    otazka = attribute_question(result.predication)
    assert otazka is not None
    assert "genitiv" not in otazka and "pád Ins" not in otazka


# --------------------------------------------------------------------------
# Přívlastek se ukazuje tvarem z věty — W‑96
# --------------------------------------------------------------------------


def test_the_attribute_shows_the_form_from_the_sentence() -> None:
    """„Cesta do PRAHA" V ŽÁDNÉ VĚTĚ NESTOJÍ *(W‑96)*.

    Hlava se od W‑77 ukazuje povrchem, doplněk se ukazoval LEMMATEM.
    Je to táž třída jako W‑93: systém říká o vlastním vstupu něco, co
    není pravda. Změřeno: 178 z 211 přívlastků korpusu, tedy 84 %."""
    from core_semantics.cascade import attribute_question

    reading = _participle()
    session, oracle = _participle_session(reading)
    result = session.utter(PARTICIPLE_TEXT, oracle)
    assert result.predication is not None
    otazka = attribute_question(result.predication, reading)
    assert otazka is not None
    assert "„Rizika spojená s zvířaty“" in otazka
    assert "zvíře" not in otazka, "lemma do popisu nepatří"


def test_the_node_keeps_the_lemma_even_though_the_report_shows_the_form() -> None:
    """IDENTITA UZLU SE TÍM NEHNE *(W‑96)*. „alergii na penicilin"
    i „alergie na penicilinu" musí padnout na TÝŽ uzel, jinak by se báze
    rozpadla po pádech. Mění se to, co systém ŘÍKÁ, ne co dělá."""
    from core_semantics.session import names_attribute

    session, oracle = _prepositional_session()
    result = session.utter(ALLERGY, oracle)
    assert result.predication is not None
    session.play(
        names_attribute("Je to na co.", "alergie", "penicilin", "na co",
                        "nmod:na+Acc")
    )
    zapsane = [str(st.formula) for st in session.kb.active()]
    assert any("alergie(na co:∀penicilin)" in f for f in zapsane)


def test_without_the_parse_the_report_keeps_the_lemma() -> None:
    """Bez rozboru se tvar NEHÁDÁ — volající si nechá lemma. Odvodit tvar
    z lemmatu by byla táž vada o patro níž (týž závěr jako u pádu
    v W‑93)."""
    from core_semantics.cascade import attribute_filler_surface

    assert attribute_filler_surface(5, None) == ""
