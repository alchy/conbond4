"""Vztažná věta jako druhá predikace s čekajícím odkazem — W‑85.

Klauze se dosud celá zahodila: 58 vztažných vět v korpusu, 210 hlášených
ztrát uvnitř nich. Připojit ji a nechat její podmět nerozhodnutý by ale
znamenalo přilepit k větě predikaci, o které nevíme, o kom je — a to je
horší než ji zahodit. **Obojí proto přichází spolu.**
"""

from __future__ import annotations

from core_semantics.ast import Entity, QueryStatus, atom, role
from core_semantics.cascade import AWAITING_REFERENCE, is_relative_pronoun
from core_semantics.engine import Engine
from core_semantics.lexicon import (
    LearnedPattern,
    Operation,
    PatternStatus,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token, Utterance
from core_semantics.session import Session, decides_reference

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


def sentence(
    podmet_form: str,
    podmet_lemma: str,
    podmet_gender: str,
    hlava_form: str,
    hlava_lemma: str,
) -> Reading:
    """«<Podmět> potkal(a) <hlavu>, který odešel.»"""
    return Reading(
        tokens=(
            tok(1, podmet_form, podmet_lemma, "NOUN", 2, "nsubj",
                Case="Nom", Gender=podmet_gender, Number="Sing"),
            tok(2, "potkal", "potkat", "VERB", 0, "root",
                Gender=podmet_gender, Number="Sing", Polarity="Pos"),
            tok(3, hlava_form, hlava_lemma, "NOUN", 2, "obj",
                Case="Acc", Gender="Masc", Number="Sing"),
            tok(4, ",", ",", "PUNCT", 6, "punct"),
            tok(5, "který", "který", "DET", 6, "nsubj",
                Case="Nom", Gender="Masc", Number="Sing", PronType="Int,Rel"),
            tok(6, "odešel", "odejít", "VERB", 3, "acl:relcl",
                Gender="Masc", Number="Sing", Polarity="Pos"),
            tok(7, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


TEXT = "Sestra potkala souseda, který odešel."


class _Oracle:
    provenance = STAMP

    def __init__(self, reading: Reading) -> None:
        self._reading = reading

    def parse(self, text: str) -> Utterance:
        return Utterance(text=text, readings=(self._reading,))


def _session(reading: Reading) -> tuple[Session, _Oracle]:
    lexicon = czech_seed()
    for case, deprel in (("Nom", "nsubj"), ("Acc", "obj")):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos="NOUN", number="Sing", case=case,
                    deprel=deprel,
                ),
                operation=Operation.EXISTS,
                learned_from="test",
                status=PatternStatus.CONFIRMED,
            )
        )
    return Session(lexicon=lexicon), _Oracle(reading)


def _default() -> tuple[Session, _Oracle]:
    return _session(sentence("Sestra", "sestra", "Fem", "souseda", "soused"))


def test_the_relative_pronoun_is_recognised_by_its_feature() -> None:
    """VÝČET LEMMAT BY BYL TŘINÁCTÁ INSTANCE TÉŽE VADY (W‑32 … W‑83).

    `PronType` u „který" je `Int,Rel` — dva rysy najednou — a čte se
    PRŮNIKEM jako všude jinde."""
    reading = sentence("Sestra", "sestra", "Fem", "souseda", "soused")
    assert is_relative_pronoun(reading.tokens[4])
    assert not is_relative_pronoun(reading.tokens[0])


def test_the_clause_is_attached_as_a_second_predication() -> None:
    """Není to člen první věty a není to ani ztráta — je to DRUHÁ
    PREDIKACE téže promluvy, týmž mechanismem jako souřadný přísudek."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    druha = result.predication.second
    assert druha is not None and druha.predicate == "odejít"
    assert any("VZTAŽNÁ VĚTA" in line for line in result.lines)


def test_the_attached_clause_is_not_reported_as_lost_as_well() -> None:
    """JEDEN SEZNAM PRO HLÁŠENÍ I PRO ÚČET *(B‑28)*.

    Připojená klauze se nesmí zároveň hlásit jako ztracený člen ani jako
    `[BEZ ZÁZNAMU]`. Dvě hlášky o jedné věci, které si odporují, jsou
    horší než jedna — a při stavbě W‑85 se to stalo, protože filtr
    ztrát existoval ve dvou kopiích."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert not any(
        "odešel" in line and "ZAHOZENO" in line for line in result.lines
    )
    assert not any(
        "odešel" in line and "BEZ ZÁZNAMU" in line for line in result.lines
    )


def test_the_pronoun_waits_for_a_reference_and_the_system_asks() -> None:
    """Odkaz je OTÁZKA S NABÍDKOU, ne odvození."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    druha = result.predication.second
    assert druha is not None
    ceka = [r for r in druha.roles if r.awaiting == AWAITING_REFERENCE]
    assert ceka and ceka[0].mention.form == "který"
    assert result.question is not None and "vztažná věta" in result.question


def test_agreement_narrows_the_offer_but_never_decides() -> None:
    """„dcera souseda, KTERÝ …" je přesně ten případ, kde by automat lhal.

    Shoda v rodě a čísle kandidáty ZUŽUJE — a když jich zbude víc,
    systém se ptá dál."""
    session, oracle = _default()
    zuzena = session.utter(TEXT, oracle).predication
    assert zuzena is not None and zuzena.second is not None
    nabidka = [r for r in zuzena.second.roles if r.awaiting][0].offered
    assert nabidka == ("soused",), (
        "ženský podmět s mužským zájmenem se nenabízí"
    )

    session2, oracle2 = _session(
        sentence("Muž", "muž", "Masc", "souseda", "soused")
    )
    oba = session2.utter(TEXT, oracle2).predication
    assert oba is not None and oba.second is not None
    nabidka2 = [r for r in oba.second.roles if r.awaiting][0].offered
    assert set(nabidka2) == {"soused", "muž"}, (
        "dva kandidáti téhož rodu zůstanou oba a rozhodne člověk"
    )


def test_the_offer_is_a_field_not_a_sentence_in_the_question() -> None:
    """NABÍDKA JE STAV, NE VĚTA *(W‑86)*.

    Číst kandidáty zpátky z textu otázky znamená psát parser na vlastní
    výstup — táž vada jako N‑10 u dokumentového běhu. Měření „kolik
    odkazů má jednoho kandidáta a kolik víc" na tom pak stojí."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert result.predication is not None and result.predication.second is not None
    ceka = [r for r in result.predication.second.roles if r.awaiting][0]
    assert ceka.offered == ("soused",)
    # A otázka se skládá Z POLE, ne pole z otázky.
    assert result.question is not None
    for kandidat in ceka.offered:
        assert kandidat in result.question


def test_without_the_reference_the_clause_does_not_reach_the_base() -> None:
    """PROTIPŘÍKLAD, KTERÝ TU MUSÍ BÝT JMENOVITĚ.

    Hlavní věta se zapíše — je celá i bez klauze — ale klauze do báze
    NEJDE, dokud se neví, o kom je. Zapsat ji dřív znamená uložit
    tvrzení o uzlu `·který`, tedy o individuu, které nikdo nezaložil."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert result.statement_id is not None, "hlavní věta se zapisuje dál"
    assert any("VZTAŽNÁ VĚTA NEZAPSÁNA" in line for line in result.lines)
    assert all(
        "odejít" not in str(st.formula) for st in session.kb.active()
    )


def test_the_answer_writes_the_clause_onto_the_named_node() -> None:
    """Po odpovědi klauze do báze jde — a na TEN uzel, který člověk řekl.
    Doloženo DOTAZEM, ne formulí."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    session.play(
        decides_reference("Ten soused.", result.predication, "kdo", "soused")
    )

    engine = Engine(session.kb)
    assert engine.ask(
        atom("odejít", role("kdo", Entity("soused")))
    ).status is QueryStatus.PROVEN_TRUE
    assert engine.ask(
        atom("odejít", role("kdo", Entity("sestra")))
    ).status is QueryStatus.UNKNOWN, "o sestře ta věta nic neříká"


def test_the_message_does_not_claim_the_node_came_from_the_parse() -> None:
    """„který" není podmět vyslovený podruhé — uzel určila ODPOVĚĎ.

    Napsat u něj „uzel vzniká z něj" by bylo tvrzení o textu, které
    neplatí (táž třída jako W‑73)."""
    session, oracle = _default()
    result = session.utter(TEXT, oracle)
    assert result.predication is not None
    po = session.play(
        decides_reference("Ten soused.", result.predication, "kdo", "soused")
    )
    radek = [line for line in po.lines if "DRUHÁ VĚTA téže promluvy" in line]
    assert radek and "určila ODPOVĚĎ" in radek[0]
    assert "vzniká z něj" not in radek[0]


# --------------------------------------------------------------------------
# Vztažné příslovce — W‑87
# --------------------------------------------------------------------------


def _with_adverb(lemma: str, upos: str = "ADV", **feats: str) -> Reading:
    """«Sestra potkala souseda, <slovo> odešel.» — místo zájmena příslovce."""
    return Reading(
        tokens=(
            tok(1, "Sestra", "sestra", "NOUN", 2, "nsubj",
                Case="Nom", Gender="Fem", Number="Sing"),
            tok(2, "potkala", "potkat", "VERB", 0, "root",
                Gender="Fem", Number="Sing", Polarity="Pos"),
            tok(3, "souseda", "soused", "NOUN", 2, "obj",
                Case="Acc", Gender="Masc", Number="Sing"),
            tok(4, ",", ",", "PUNCT", 6, "punct"),
            tok(5, lemma, lemma, upos, 6, "advmod", **feats),
            tok(6, "odešel", "odejít", "VERB", 3, "acl:relcl",
                Gender="Masc", Number="Sing", Polarity="Pos"),
            tok(7, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )


def test_an_interrogative_adverb_names_its_own_role() -> None:
    """PŘÍSLOVCE „kde" NENÍ ZPŮSOB *(W‑87)*.

    Každé `advmod` dostávalo roli `jak`, takže „…do Josefova, **kde** se
    manželům narodilo dítě." tvrdilo, že „kde" je způsob děje. To o té
    větě NEPLATÍ — a je to nepravda vedle vlastní otázky, protože systém
    se pak ptal na odkaz role „jak".

    Jméno se nebere ze seznamu slov (to by byla čtrnáctá instance
    W‑32 … W‑83), ale z RYSU `PronType`: české tázací příslovce JE jméno
    té okolnosti."""
    session, oracle = _session(_with_adverb("kde", PronType="Int,Rel"))
    result = session.utter(TEXT, oracle)
    assert result.predication is not None and result.predication.second is not None
    assert result.predication.second.role("kde") is not None
    assert result.predication.second.role("jak") is None


def test_an_ordinary_adverb_is_still_manner() -> None:
    """PROTIPŘÍKLAD: „rychle" `PronType` nemá a zůstává `jak`. Kdyby se
    změnilo obojí, změna by nebyla oprava, ale jiné pravidlo.

    Měří se na HLAVNÍ větě: bez vztažného zájmena se klauze nepřipojí
    (W‑85), takže druhá predikace by ani nevznikla a test by měřil něco
    jiného, než co tvrdí."""
    obycejne = Reading(
        tokens=(
            tok(1, "Sestra", "sestra", "NOUN", 2, "nsubj",
                Case="Nom", Gender="Fem", Number="Sing"),
            tok(2, "odešla", "odejít", "VERB", 0, "root",
                Gender="Fem", Number="Sing", Polarity="Pos"),
            tok(3, "rychle", "rychle", "ADV", 2, "advmod", Degree="Pos"),
            tok(4, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance=STAMP,
    )
    session, oracle = _session(obycejne)
    result = session.utter("Sestra odešla rychle.", oracle)
    assert result.predication is not None
    assert result.predication.role("jak") is not None
    assert result.predication.role("rychle") is None
