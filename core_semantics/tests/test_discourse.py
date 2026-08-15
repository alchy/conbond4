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


# --------------------------------------------------------------------------
# PRO‑DROP — věta bez podmětu (0.1.17)
# --------------------------------------------------------------------------
#
# Druhá polovina téže vrstvy, a v přirozeném textu ČASTĚJŠÍ NEŽ ZÁJMENO:
# životopisný odstavec je jí plný. Podmět tam NENÍ VŮBEC — ne že by byl
# zájmenem.
#
# Co se dělo předtím, byla horší vada než neumět pro‑drop: věta se zapsala
# jako `narodit(kde:Praha)`, tedy jako fakt O NIKOM, a nic to neřeklo.

BORN_M = Reading(
    tokens=(
        w(1, "Narodil", "narodit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        w(2, "se", "se", "PRON", 1, "expl:pv", Case="Acc", Reflex="Yes"),
        w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
        w(4, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(5, ".", ".", "PUNCT", 1, "punct"),
    ),
    provenance=STAMP,
)

BORN_F = Reading(
    tokens=(
        w(1, "Narodila", "narodit", "VERB", 0, "root", Gender="Fem,Neut", Number="Plur,Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        w(2, "se", "se", "PRON", 1, "expl:pv", Case="Acc", Reflex="Yes"),
        w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
        w(4, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(5, ".", ".", "PUNCT", 1, "punct"),
    ),
    provenance=STAMP,
)

ASK_BORN = Reading(
    tokens=(
        w(1, "Narodil", "narodit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos", Tense="Past", VerbForm="Part", Voice="Act"),
        w(2, "se", "se", "PRON", 1, "expl:pv", Case="Acc", Reflex="Yes"),
        w(3, "Jan", "Jan", "PROPN", 1, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
        w(4, "v", "v", "ADP", 5, "case", Case="Loc"),
        w(5, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(6, "?", "?", "PUNCT", 1, "punct"),
    ),
    provenance=STAMP,
)

BORN_M_TEXT = "Narodil se v Praze."
BORN_F_TEXT = "Narodila se v Praze."
ASK_BORN_TEXT = "Narodil se Jan v Praze?"


def prodrop_oracle() -> _Recorded:
    return _Recorded(
        {
            TEACHER_TEXT: TEACHER,
            BORN_M_TEXT: BORN_M,
            BORN_F_TEXT: BORN_F,
            ASK_BORN_TEXT: ASK_BORN,
        }
    )


def prodrop_session() -> Session:
    session = Session(lexicon=lexicon())
    session.utter(TEACHER_TEXT, prodrop_oracle())
    return session


def test_a_subjectless_sentence_is_no_longer_written_headless() -> None:
    """PŮVODNÍ VADA. Věta se zapsala jako `narodit(kde:Praha)` — fakt
    o nikom — a nic to neřeklo. V encyklopedické próze by se do báze
    ukládaly dekapitované věty jedna za druhou a poznat by to nešlo."""
    session = prodrop_session()
    result = session.utter(BORN_M_TEXT, prodrop_oracle())
    assert result.statement_id is None
    assert result.predication is not None
    role = result.predication.role("kdo")
    assert role is not None, "podmět musí v predikaci VZNIKNOUT, i když ho věta nevyslovila"


def test_the_candidate_is_offered_from_the_previous_sentence() -> None:
    session = prodrop_session()
    question = session.utter(BORN_M_TEXT, prodrop_oracle()).question
    assert question is not None
    assert "nemá podmět" in question and "Jan" in question


def test_the_gender_on_the_predicate_is_checked() -> None:
    """PROTIPŘÍKLAD. „Narodila" nese `Gender=Fem,Neut`, Jan je Masc —
    průnik je prázdný, takže se nenabídne nikdo. Kdyby se rod
    nekontroloval, systém by Jana nabídl a člověk by odpověď jen odklepl."""
    session = prodrop_session()
    question = session.utter(BORN_F_TEXT, prodrop_oracle()).question
    assert question is not None
    assert "Jan" not in question
    assert "nikdo takový nestojí" in question


def test_a_multi_valued_feature_is_compared_by_intersection() -> None:
    """Rys může nést VÍC hodnot, protože tvar je pro obojí týž. Rovnost by
    zahodila kandidáta, který se shodnout MŮŽE, a z vodítka by udělala
    filtr, který rozhoduje."""
    from core_semantics.cascade import Mention

    context = Discourse(
        mentions=(
            (
                Mention(lemma="Marie", form="Marie", token_index=1, upos="PROPN",
                        feats=(("Gender", "Fem"), ("Number", "Sing"))),
                Entity("Marie"),
            ),
        )
    )
    ambiguous = Mention(
        lemma="narodit", form="Narodila", token_index=1, upos="VERB",
        feats=(("Gender", "Fem,Neut"), ("Number", "Plur,Sing")),
    )
    assert len(context.candidates(ambiguous)) == 1


def test_nothing_is_written_before_the_subject_is_decided() -> None:
    session = prodrop_session()
    before = len(session.program())
    session.utter(BORN_M_TEXT, prodrop_oracle())
    assert len(session.program()) == before


def test_after_the_decision_the_fact_lands_on_that_node() -> None:
    session = prodrop_session()
    pending = session.utter(BORN_M_TEXT, prodrop_oracle())
    assert pending.predication is not None
    answer = session.play(
        decides_reference("Myslím Jana.", pending.predication, "kdo", "Jan")
    )
    assert answer.statement_id is not None
    assert any("kdo:Jan" in line for line in answer.lines)
    assert (
        session.utter(ASK_BORN_TEXT, prodrop_oracle()).status
        is QueryStatus.PROVEN_TRUE
    )


def test_a_predicate_that_says_nothing_about_the_subject_offers_nobody() -> None:
    """Přísudek bez rodu a čísla nedává ani vodítko. Nabízet bez něj
    kohokoli by bylo hádání, ne návrh."""
    bare = Reading(
        tokens=(
            w(1, "Prší", "pršet", "VERB", 0, "root", Polarity="Pos"),
            w(2, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance=STAMP,
    )
    text = "Prší."
    session = prodrop_session()
    result = session.utter(text, _Recorded({text: bare}))
    assert result.predication is None or result.predication.role("kdo") is None


# --------------------------------------------------------------------------
# Trpný rod se pozná ZE STRUKTURY — W‑48
# --------------------------------------------------------------------------
#
# „Byl pohřben na Vyšehradě." nemá podmět a přesto se zapsala BEZ NĚJ,
# tedy jako fakt o nikom, a nic to neřeklo. Příčina: kořen trpné věty je
# `ADJ` (příčestí `pohřben`), pomocné sloveso visí pod ním jako `aux:pass`,
# a patro se ptalo na SLOVNÍ DRUH kořene výčtem `("VERB", "AUX")`.
#
# Potřetí táž třída vad: W‑32 porovnávala rysy řetězcem, W‑47 deprel
# řetězcem, tohle `upos` výčtem. Pokaždé kategorie, která má variantu.

PASSIVE_NO_SUBJECT = Reading(
    tokens=(
        w(1, "Byl", "být", "AUX", 2, "aux:pass", Gender="Masc", Number="Sing"),
        w(2, "pohřben", "pohřbený", "ADJ", 0, "root", Gender="Masc", Number="Sing", Voice="Pass"),
        w(3, "v", "v", "ADP", 4, "case", Case="Loc"),
        w(4, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(5, ".", ".", "PUNCT", 2, "punct"),
    ),
    provenance=STAMP,
)

PASSIVE_WITH_SUBJECT = Reading(
    tokens=(
        w(1, "Jan", "Jan", "PROPN", 3, "nsubj:pass", Case="Nom", Gender="Masc", Number="Sing"),
        w(2, "byl", "být", "AUX", 3, "aux:pass", Gender="Masc", Number="Sing"),
        w(3, "pohřben", "pohřbený", "ADJ", 0, "root", Gender="Masc", Number="Sing", Voice="Pass"),
        w(4, "v", "v", "ADP", 5, "case", Case="Loc"),
        w(5, "Praze", "Praha", "PROPN", 3, "obl", Case="Loc", Gender="Fem", Number="Sing"),
        w(6, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

PASSIVE_NO_SUBJECT_TEXT = "Byl pohřben v Praze."
PASSIVE_WITH_SUBJECT_TEXT = "Jan byl pohřben v Praze."


def _passive_oracle() -> _Recorded:
    return _Recorded(
        {
            TEACHER_TEXT: TEACHER,
            PASSIVE_NO_SUBJECT_TEXT: PASSIVE_NO_SUBJECT,
            PASSIVE_WITH_SUBJECT_TEXT: PASSIVE_WITH_SUBJECT,
        }
    )


def test_a_subjectless_passive_no_longer_writes_a_fact_about_nobody() -> None:
    """CRITICAL. Věta bez podmětu se nesmí zapsat dekapitovaná, ať je
    kořen VERB, nebo ADJ. Trpný rod na tom nic nemění."""
    session = Session(lexicon=lexicon())
    session.utter(TEACHER_TEXT, _passive_oracle())
    result = session.utter(PASSIVE_NO_SUBJECT_TEXT, _passive_oracle())
    assert result.statement_id is None
    assert result.question is not None
    assert result.predication is not None
    # Od W‑79 se ta role jmenuje `co`: trpný podmět je PATIENS, ať ho
    # text vysloví, nebo ne. Test drží TOTÉŽ tvrzení — role vzniknout
    # musí a věta se nesmí zapsat dekapitovaná — jen pod jménem, které
    # se s vysloveným trpným podmětem potká.
    role = result.predication.role("co")
    assert role is not None, "role musí vzniknout i u trpné věty"


def test_a_passive_with_a_subject_is_not_treated_as_pro_drop() -> None:
    """`nsubj:pass` je VYSLOVENÝ podmět. Kdyby se sem nezapočítal, patro
    by u každé trpné věty tvrdilo, že podmět chybí, a ptalo se na
    antecedent někoho, kdo ve větě stojí. Survey W‑47 to rozhodl a tohle
    se s ním nesmí rozejít."""
    session = Session(lexicon=lexicon())
    session.utter(TEACHER_TEXT, _passive_oracle())
    result = session.utter(PASSIVE_WITH_SUBJECT_TEXT, _passive_oracle())
    assert result.predication is not None
    assert result.predication.role("kdo") is None
    otazka = result.question or ""
    assert "nemá podmět" not in otazka


def test_the_predicate_is_recognised_from_structure_not_from_upos() -> None:
    """PŘÍČINA, ne příznak. Kdyby se zase začal číst výčet slovních druhů,
    tenhle test padne dřív, než se to projeví zápisem faktu o nikom."""
    import inspect

    from core_semantics.cascade import PREDICATE_AUXILIARIES, _is_predicate

    # Rozhoduje STRUKTURA: pomocné sloveso pod kořenem, ne značka kořene.
    assert set(PREDICATE_AUXILIARIES) == {"aux", "cop"}
    source = inspect.getsource(_is_predicate)
    assert "PREDICATE_AUXILIARIES" in source
    assert "W‑48" in source, "důvod má být v kódu, ne jen v commitu"
    assert _is_predicate(PASSIVE_NO_SUBJECT.tokens[1], PASSIVE_NO_SUBJECT)


def test_a_nominal_root_without_an_auxiliary_is_not_a_predicate() -> None:
    """Stráž zůstává úzká: jméno bez pomocného slovesa přísudek NENÍ,
    takže se u něj podmět nedoplňuje. Jinak by patro vyrábělo otázku
    u každé jmenné fráze."""
    from core_semantics.cascade import _is_predicate

    holy = Reading(
        tokens=(
            w(1, "Praha", "Praha", "PROPN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
            w(2, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance=STAMP,
    )
    assert not _is_predicate(holy.tokens[0], holy)


# --------------------------------------------------------------------------
# Podmět vyjádřený celou větou — B‑18
# --------------------------------------------------------------------------
#
# „Je jasné, že Jan přišel." podmět MÁ: je jím celá věta vedlejší, kterou
# rozbor označil `csubj`. Systém o ní přesto tvrdil, že podmět
# nevyslovila, a na základě toho nepravdivého výroku NABÍZEL ANTECEDENT —
# zval člověka, aby dosadil podmět tam, kde už jeden stojí.
#
# Mlčet by ale bylo taky nepřesné: dosadit větu za fillér zatím neumíme.
# Rozdíl mezi „NEŘEČENO" a „ŘEČENO, NEUMÍM" je přesně ten, který tenhle
# projekt drží jinde (`NEZAKOTVENO` × `bez čtení`).

CLAUSAL_SUBJECT = Reading(
    tokens=(
        w(1, "Je", "být", "AUX", 2, "cop", Number="Sing", Polarity="Pos"),
        w(2, "jasné", "jasný", "ADJ", 0, "root", Gender="Neut", Number="Sing"),
        w(3, "že", "že", "SCONJ", 5, "mark"),
        w(4, "Jan", "Jan", "PROPN", 5, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
        w(5, "přišel", "přijít", "VERB", 2, "csubj", Gender="Masc", Number="Sing"),
        w(6, ".", ".", "PUNCT", 2, "punct"),
    ),
    provenance=STAMP,
)

CLAUSAL_SUBJECT_TEXT = "Je jasné, že Jan přišel."


def test_a_clausal_subject_is_not_reported_as_missing() -> None:
    """NEPRAVDIVÝ VÝROK O TEXTU. Ta věta podmět MÁ — je jím celá věta
    vedlejší. Tvrdit o ní, že ho nevyslovila, a pak nabízet antecedent
    znamená zvát člověka, aby dosadil podmět tam, kde jeden stojí."""
    session = Session(lexicon=lexicon())
    session.utter(TEACHER_TEXT, _passive_oracle())
    result = session.utter(
        CLAUSAL_SUBJECT_TEXT,
        _Recorded({CLAUSAL_SUBJECT_TEXT: CLAUSAL_SUBJECT, TEACHER_TEXT: TEACHER}),
    )
    stopa = " ".join(result.lines)
    assert "BEZ PODMĚTU" not in stopa
    assert "nemá podmět" not in (result.question or "")


def test_it_says_what_it_cannot_do_instead_of_staying_silent() -> None:
    """Mlčet by bylo taky nepřesné: podmět tam JE, jen ho neumíme dosadit.
    Rozdíl mezi „neřečeno" a „řečeno, neumím" tenhle projekt drží jinde
    a má ho držet i tady."""
    session = Session(lexicon=lexicon())
    result = session.utter(
        CLAUSAL_SUBJECT_TEXT,
        _Recorded({CLAUSAL_SUBJECT_TEXT: CLAUSAL_SUBJECT}),
    )
    stopa = " ".join(result.lines)
    assert "PODMĚT JE CELÁ VĚTA" in stopa
    assert "zatím neumím" in stopa


def test_the_subject_deprels_are_a_named_constant() -> None:
    """POČTVRTÉ TÁŽ TŘÍDA: W‑32 rysy řetězcem, W‑47 deprel řetězcem,
    W‑48 `upos` výčtem, B‑18 výčet podmětových závislostí. Seznam je proto
    POJMENOVANÁ KONSTANTA se zapsaným důvodem, ne literál v podmínce."""
    import inspect

    from core_semantics.cascade import SUBJECT_DEPRELS, prodrop_tier

    assert set(SUBJECT_DEPRELS) == {"nsubj", "csubj"}
    assert "SUBJECT_DEPRELS" in inspect.getsource(prodrop_tier)
    # Důvod má být v kódu U TÉ KONSTANTY, ne jen v commitu. Čte se
    # soubor, ne `inspect.getsource(modul)`: `core_semantics.cascade` je
    # kvůli reexportu FUNKCE, ne modul, a vrátilo by to zdroj funkce.
    from pathlib import Path

    zdroj = Path(prodrop_tier.__globals__["__file__"]).read_text(encoding="utf-8")
    misto = zdroj.index("SUBJECT_DEPRELS = ")
    assert "B‑18" in zdroj[max(0, misto - 900) : misto]


def test_a_genuinely_subjectless_sentence_still_asks() -> None:
    """Stráž se nesmí rozšířit tak, že přestane ptát tam, kde podmět
    doopravdy chybí — to by z opravy udělalo díru."""
    session = Session(lexicon=lexicon())
    session.utter(TEACHER_TEXT, _passive_oracle())
    result = session.utter(PASSIVE_NO_SUBJECT_TEXT, _passive_oracle())
    assert "BEZ PODMĚTU" in " ".join(result.lines)
    assert result.statement_id is None
