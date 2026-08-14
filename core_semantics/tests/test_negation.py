"""Negace z `Polarity=Neg` — L‑4.

Bez tohohle patra kaskáda slovo *negace* neznala vůbec, takže „Tučňák
nelétá" a „Tučňák létá" daly totéž čtení. Doména farmaka na tom stojí
celá — její závěr je `nesmí dostat`.

**Testuje se hlavně to, co se nesmí splést**: silná negace `p̄` není
nepřítomnost důkazu (I‑21), a záporná shoda se nesčítá.
"""

from __future__ import annotations

import pytest

from core_semantics.ast import (
    Entity,
    Group,
    Quantifier,
    QueryStatus,
    atom,
    member_of,
    role,
)
from core_semantics.cascade import (
    HARD_TIERS,
    ROLE_OBJECT,
    ROLE_SUBJECT,
    cascade,
    negation_tier,
    quantifier_tier,
)
from core_semantics.engine import Engine
from core_semantics.lexicon import czech_seed
from core_semantics.oracle import Reading, Token
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


def flies(negated: bool) -> Reading:
    """«Tučňák (ne)létá.» — věta dialogu E."""
    return Reading(
        tokens=(
            tok(1, "Tučňák", "tučňák", "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
            tok(
                2,
                "nelétá" if negated else "létá",
                "létat",
                "VERB",
                0,
                "root",
                Number="Sing",
                **({"Polarity": "Neg"} if negated else {"Polarity": "Pos"}),
            ),
        ),
        provenance=STAMP,
    )


#: «Petr nemá žádné auto.» — zápor je na SLOVESE i na determinátoru
#: a je to JEDNA negace. Čeština to tak dělá vždycky.
CONCORD = Reading(
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "nemá", "mít", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
        tok(3, "žádné", "žádný", "DET", 4, "det", Case="Acc"),
        tok(4, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    ),
    provenance=STAMP,
)

#: «Pacient s alergií nesmí dostat penicilin.» — zkráceně na to, co
#: doména farmaka opravdu potřebuje: záporný přísudek s předmětem.
PHARMA = Reading(
    tokens=(
        tok(1, "Pacient", "pacient", "NOUN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "nesmí", "smět", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
        tok(3, "penicilin", "penicilin", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    ),
    provenance=STAMP,
)


def read(reading: Reading) -> object:
    return cascade(reading, tiers=(*HARD_TIERS, quantifier_tier(czech_seed())))


# --------------------------------------------------------------------------
# Základ
# --------------------------------------------------------------------------


def test_negated_verb_negates_the_reading() -> None:
    verdict = cascade(flies(True))
    assert verdict.decided is not None
    assert verdict.decided.predication.negated is True
    assert str(verdict.decided.predication).startswith("¬")


def test_positive_verb_stays_positive() -> None:
    verdict = cascade(flies(False))
    assert verdict.decided is not None
    assert verdict.decided.predication.negated is False
    assert "¬" not in str(verdict.decided.predication)


def test_the_two_sentences_do_not_collapse_into_one_reading() -> None:
    """Před L‑4 daly „Tučňák létá" a „Tučňák nelétá" TOTÉŽ čtení, protože
    kaskáda slovo negace neznala."""
    positive = cascade(flies(False)).decided
    negative = cascade(flies(True)).decided
    assert positive is not None and negative is not None
    assert positive.predication != negative.predication


def test_the_tier_says_why() -> None:
    verdict = cascade(flies(True))
    assert any("ZÁPOR" in step for step in verdict.trace)
    assert any("Polarity=Neg" in step for step in verdict.trace)


def test_negation_is_a_hard_tier_not_a_learned_pattern() -> None:
    """`Polarity=Neg` má jeden význam, takže se na něm učit není co —
    patří ke shodě a pádu, ne k naučeným vzorům."""
    assert negation_tier in HARD_TIERS
    # A funguje BEZ lexikonu, což je ta zkouška.
    assert cascade(flies(True), tiers=(negation_tier,)).decided is not None


# --------------------------------------------------------------------------
# Co se nesmí splést
# --------------------------------------------------------------------------


def test_negative_concord_is_one_negation_not_two() -> None:
    """„Petr nemá žádné auto." má zápor dvakrát a znamená ho jednou.
    Sčítat je by z popření udělalo tvrzení — přesně opačný význam."""
    verdict = cascade(CONCORD)
    assert verdict.decided is not None
    assert verdict.decided.predication.negated is True
    assert any("shoda" in step for step in verdict.trace)
    assert any("JEDNA negace" in step for step in verdict.trace)


def test_strong_negation_is_not_absence_of_proof() -> None:
    """I‑21. „Tučňák nelétá" je DOLOŽENÉ tvrzení; „o tučňácích nic nevím"
    je něco jiného a jádro to drží jako dva různé stavy.

    Test jde až do jádra, protože právě tam se to musí lišit — v kaskádě
    by šlo obojí zapsat jako `negated=True` a vypadalo by to stejně.
    """
    kb = KnowledgeBase()
    verdict = cascade(flies(True))
    assert verdict.decided is not None
    predication = verdict.decided.predication

    negated = atom(
        predication.predicate,
        role(ROLE_SUBJECT, Group("tučňák"), Quantifier.FOR_ALL),
        negated=predication.negated,
    )
    kb.attach(negated)
    engine = Engine(kb)
    assert engine.ask(negated).status is QueryStatus.PROVEN_TRUE
    # Nic o vrabcích řečeno nebylo — a to NENÍ totéž jako popření.
    about_sparrow = atom(
        predication.predicate,
        role(ROLE_SUBJECT, Group("vrabec"), Quantifier.FOR_ALL),
        negated=True,
    )
    assert engine.ask(about_sparrow).status is QueryStatus.UNKNOWN


def test_pharma_conclusion_can_be_read_at_all() -> None:
    """Doména farmaka stojí na `nesmí dostat`. Bez L‑4 se ta věta přečetla
    jako `smět`, tedy s opačným závěrem."""
    verdict = cascade(PHARMA)
    assert verdict.decided is not None
    predication = verdict.decided.predication
    assert predication.predicate == "smět"
    assert predication.negated is True
    assert predication.role(ROLE_OBJECT) is not None


def test_negation_survives_the_rest_of_the_cascade() -> None:
    """Patra za negací čtení přepisují (přejmenování rolí, kvantifikátor).
    Kdyby některé z nich stavělo `Predication` znovu a zápor zapomnělo,
    věta by tiše změnila význam."""
    verdict = read(flies(True))
    decided = verdict.decided  # type: ignore[attr-defined]
    assert decided is not None
    assert decided.predication.negated is True


def test_negation_transcript_prints() -> None:
    echo("\n" + "=" * 72)
    echo("NEGACE Z Polarity=Neg — L‑4")
    echo("=" * 72)
    for label, reading in (
        ("Tučňák létá.", flies(False)),
        ("Tučňák nelétá.", flies(True)),
        ("Petr nemá žádné auto.", CONCORD),
        ("Pacient nesmí penicilin.", PHARMA),
    ):
        echo(f"\n» {label}")
        for line in cascade(reading).render():
            echo(f"   {line}")
    echo("\n" + "=" * 72)
