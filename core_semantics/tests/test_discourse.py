"""KONTEXT TEXTU — zájmeno odkazuje do předchozí věty (0.1.16).

**Sezení dosud znalo TAH, ne TEXT.** Každá věta se zakotvovala sama za
sebe, protože etalon mluvil jmény a odkaz nepotřeboval. Souvislý psaný
text — takový, jaký se běžně čte — ale odkazuje pořád: „Jan je učitel.
**On** bydlí v Praze." Bez paměti předchozí věty není zájmeno na co
navázat.

**Je to nová INFORMACE, ne nová inference.** Nic se z kontextu neodvozuje;
jen se z něj NABÍZEJÍ kandidáti. Shoda rodu a čísla je vodítko struktury
textu, ne důkaz, a proto kandidáty jen zužuje.

**Předzpracování by tuhle mezeru zakrylo.** Čistič, který zájmena předem
nahradí jmény, vyrobí text, jakému systém rozumí, a schová právě to, co se
má naučit. Proto je kontext ve vrstvě, která zmínky na uzly váže.

**A ptá se i tehdy, když je kandidát jediný** (I‑13). Tichý default
u identity je nejdražší chyba, jakou tenhle systém může udělat: uzly se
tiše slijí nebo rozštěpí a nepozná to žádný test, ke kterému jazyk nevede.
Rozdíl mezi „trefil jsem týž uzel" a „ČLOVĚK ŘEKL, že to je týž" je celá
M‑2.
"""

from __future__ import annotations

from core_semantics.ast import Entity, QueryStatus
from core_semantics.grounding import Discourse
from core_semantics.lexicon import Lexicon
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session, decides_reference
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


VERB = dict(
    Aspect="Imp", Mood="Ind", Number="Sing", Person="3", Polarity="Pos",
    Tense="Pres", VerbForm="Fin", Voice="Act",
)

TEACHER = Reading(
    tokens=(
        w(1, "Jan", "Jan", "PROPN", 3, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "je", "být", "AUX", 3, "cop", Number="Sing", Polarity="Pos"),
        w(3, "učitel", "učitel", "NOUN", 0, "root", Animacy="Anim", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

HE_LIVES = Reading(
    tokens=(
        w(1, "On", "on", "PRON", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing", Person="3", PronType="Prs"),
        w(2, "bydlí", "bydlet", "VERB", 0, "root", **VERB),
        w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
        w(4, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(5, ".", ".", "PUNCT", 2, "punct"),
    ),
    provenance=STAMP,
)

SHE_LIVES = Reading(
    tokens=(
        w(1, "Ona", "on", "PRON", 2, "nsubj", Case="Nom", Gender="Fem", Number="Sing", Person="3", PronType="Prs"),
        w(2, "bydlí", "bydlet", "VERB", 0, "root", **VERB),
        w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
        w(4, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(5, ".", ".", "PUNCT", 2, "punct"),
    ),
    provenance=STAMP,
)

ASK = Reading(
    tokens=(
        w(1, "Bydlí", "bydlet", "VERB", 0, "root", **VERB),
        w(2, "Jan", "Jan", "PROPN", 1, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
        w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
        w(4, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(5, "?", "?", "PUNCT", 1, "punct"),
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
HE_TEXT = "On bydlí v Praze."
SHE_TEXT = "Ona bydlí v Praze."
ASK_TEXT = "Bydlí Jan v Praze?"


def oracle() -> _Recorded:
    return _Recorded(
        {
            TEACHER_TEXT: TEACHER,
            HE_TEXT: HE_LIVES,
            SHE_TEXT: SHE_LIVES,
            ASK_TEXT: ASK,
        }
    )


def lexicon() -> "Lexicon":
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation,
        PatternStatus,
        RoleMapping,
        Trigger,
        czech_seed,
    )

    found = czech_seed()
    for upos, number, case, deprel in (
        ("PROPN", "Sing", "Nom", "nsubj"),
        ("PROPN", "Sing", "Loc", "obl"),
        ("NOUN", "Sing", "Nom", "root"),
    ):
        found.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos=upos, number=number, case=case, deprel=deprel
                ),
                operation=Operation.SELF,
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    found.add_role(
        RoleMapping(
            surface="v+Loc",
            canonical="kde",
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    return found


def opened() -> Session:
    """Sezení po první větě — kontext nese Jana."""
    session = Session(lexicon=lexicon())
    session.utter(TEACHER_TEXT, oracle())
    return session


# --------------------------------------------------------------------------
# Návrh z předchozí věty
# --------------------------------------------------------------------------


def test_the_antecedent_is_offered_from_the_previous_sentence() -> None:
    session = opened()
    question = session.utter(HE_TEXT, oracle()).question
    assert question is not None
    assert "Jan" in question


def test_nothing_is_written_before_the_reference_is_decided() -> None:
    """Táž zábrana jako u čekající konstrukce (B‑17) a uzavření světa,
    jen o identitu: zapsat větu na uzel, o kterém se teprve rozhoduje, by
    znamenalo zapsat něco jiného, než člověk řekl."""
    session = opened()
    before = len(session.program())
    result = session.utter(HE_TEXT, oracle())
    assert result.statement_id is None
    assert len(session.program()) == before


def test_it_asks_even_when_the_candidate_is_the_only_one() -> None:
    """I‑13. Shoda rodu a čísla je vodítko STRUKTURY TEXTU, ne důkaz.
    „Trefil jsem týž uzel" a „člověk řekl, že to je týž" jsou dvě různé
    věci a celá M‑2 stojí na tom rozdílu."""
    session = opened()
    result = session.utter(HE_TEXT, oracle())
    assert result.question is not None
    predication = result.predication
    assert predication is not None
    role = predication.reading("kdo")
    assert role is not None and role.awaiting, (
        "role musí ČEKAT na odkaz v PREDIKACI, ne jen v otázce — jinak "
        "odpověď `→=` nemá kam přistát (táž lekce jako B‑17)"
    )


def test_a_candidate_that_is_not_in_the_previous_sentence_is_not_offered() -> None:
    """„Ona" je ženského rodu a v předchozí větě stojí jen Jan. Nabídnout
    uzel odjinud znamená tvrdit, že text odkazuje tam, kde nic nestojí."""
    session = opened()
    question = session.utter(SHE_TEXT, oracle()).question
    assert question is not None
    assert "Jan" not in question
    assert "nikdo takový nestojí" in question


def test_a_group_is_never_offered_as_an_antecedent() -> None:
    """„Jan je učitel." nabízí Jana, ne „učitele": zájmeno odkazuje na
    TOHO, o kom byla řeč, a ztotožnit ho s celou třídou by z individua
    udělalo druh."""
    session = opened()
    question = session.utter(HE_TEXT, oracle()).question
    assert question is not None
    assert "učitel" not in question


# --------------------------------------------------------------------------
# Rozhodnutí a jeho následky
# --------------------------------------------------------------------------


def test_after_the_decision_the_fact_lands_on_the_same_node() -> None:
    session = opened()
    pending = session.utter(HE_TEXT, oracle())
    assert pending.predication is not None
    answer = session.play(
        decides_reference("Myslím Jana.", pending.predication, "kdo", "Jan")
    )
    assert answer.statement_id is not None
    assert any("kdo:Jan" in line for line in answer.lines)


def test_the_question_about_that_node_is_then_answered() -> None:
    session = opened()
    pending = session.utter(HE_TEXT, oracle())
    assert pending.predication is not None
    session.play(decides_reference("Myslím Jana.", pending.predication, "kdo", "Jan"))
    assert session.utter(ASK_TEXT, oracle()).status is QueryStatus.PROVEN_TRUE


def test_without_the_answer_the_question_stays_unknown() -> None:
    """Půlka měření, bez které by se nedalo poznat, jestli `A` způsobilo
    rozhodnutí o odkazu, nebo jestli tam bylo pořád."""
    session = opened()
    session.utter(HE_TEXT, oracle())
    assert session.utter(ASK_TEXT, oracle()).status is QueryStatus.UNKNOWN


# --------------------------------------------------------------------------
# Co kontext NESMÍ
# --------------------------------------------------------------------------


def test_the_context_moves_only_after_a_sentence_that_grounded() -> None:
    """Věta, u které se systém ptá, ještě není řečená do konce — nabízet
    z ní antecedenty by znamenalo odkazovat na uzly, o kterých se teprve
    rozhoduje."""
    session = opened()
    session.utter(SHE_TEXT, oracle())  # nezakotví se
    question = session.utter(HE_TEXT, oracle()).question
    assert question is not None
    assert "Jan" in question, "kontext má pořád držet PRVNÍ větu"


def test_agreement_only_narrows_it_never_decides() -> None:
    """Shoda je filtr kandidátů, ne výběr. Kdyby vybírala, byl by z ní
    tichý default u identity — a to je ta nejdražší chyba."""
    from core_semantics.cascade import Mention

    context = Discourse(
        mentions=(
            (
                Mention(lemma="Jan", form="Jan", token_index=1, upos="PROPN",
                        feats=(("Gender", "Masc"), ("Number", "Sing"))),
                Entity("Jan"),
            ),
        )
    )
    masculine = Mention(
        lemma="on", form="On", token_index=1, upos="PRON",
        feats=(("Gender", "Masc"), ("Number", "Sing")),
    )
    feminine = Mention(
        lemma="on", form="Ona", token_index=1, upos="PRON",
        feats=(("Gender", "Fem"), ("Number", "Sing")),
    )
    assert len(context.candidates(masculine)) == 1
    assert context.candidates(feminine) == ()


def test_the_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("KONTEXT TEXTU — zájmeno odkazuje do předchozí věty")
    echo("=" * 72)
    session = opened()
    echo(f"» {TEACHER_TEXT}")
    pending = session.utter(HE_TEXT, oracle())
    echo(f"» {HE_TEXT}  → zapsáno: {pending.statement_id}")
    echo(f"   ? {pending.question}")
    assert pending.predication is not None
    answer = session.play(
        decides_reference("Myslím Jana.", pending.predication, "kdo", "Jan")
    )
    for line in answer.lines[-2:]:
        echo(f"   {line}")
    status = session.utter(ASK_TEXT, oracle()).status
    assert status is not None
    echo(f"» {ASK_TEXT}  → {status.name}")
    echo("=" * 72)
