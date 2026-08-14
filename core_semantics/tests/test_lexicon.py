"""Jazykový program `LEX` (§ 3.7) — uzavřené menu a životní cyklus vzoru.

Dvě věci se testují nejpřísněji: že se menu nedá obejít (I‑15) a že se
nejednoznačné slovo nerozhodne tiše (I‑1).
"""

from __future__ import annotations

from core_semantics.ast import Comparator, Quantifier
from core_semantics.lexicon import (
    MENU,
    Lexicon,
    LearnedPattern,
    Mood,
    Operation,
    PatternStatus,
    StructuralSignature,
    Trigger,
    czech_seed,
    menu_prompt,
)


# --------------------------------------------------------------------------
# Menu je uzavřené a odvozené z jádra
# --------------------------------------------------------------------------


def test_menu_covers_every_operation() -> None:
    """Kdyby menu nepokrývalo celou sadu, doptání by nabídlo míň, než jádro
    umí — a chybějící položka by se doplňovala mimo menu."""
    assert {operation for operation, _ in MENU} == set(Operation)


def test_menu_targets_exist_in_the_kernel() -> None:
    """Menu se nepřenáší z předlohy, odvozuje se z toho, co jádro umí.
    Tenhle test je pojistka proti mapování na neexistující operaci."""
    assert {c.name for c in Comparator} >= {"LE", "LT", "GE", "GT"}
    assert {q.name for q in Quantifier} >= {"FOR_ALL", "EXISTS", "SELF"}


def test_clarification_offers_only_menu_items() -> None:
    prompt = menu_prompt((Operation.GROUP_OR, Operation.ALTERNATIVE))
    assert len(prompt) == 2
    assert all(line.split(":")[0] in {o.value for o in Operation} for line in prompt)


# --------------------------------------------------------------------------
# „nebo" je dvě různé operace jádra
# --------------------------------------------------------------------------


def test_or_maps_to_two_different_kernel_operations() -> None:
    """„Petr má psa nebo kočku" je objektové `OR`; „Je citron ovoce, nebo
    zelenina?" je epistemická alternativa. Totéž slovo, dvě operace."""
    lexicon = czech_seed()
    assertion = lexicon.candidates(
        StructuralSignature(lemma="nebo", mood=Mood.ASSERTION)
    )
    question = lexicon.candidates(
        StructuralSignature(lemma="nebo", mood=Mood.QUESTION)
    )
    assert [p.operation for p in assertion] == [Operation.GROUP_OR]
    assert [p.operation for p in question] == [Operation.ALTERNATIVE]


def test_unknown_mood_yields_both_candidates_not_a_silent_pick() -> None:
    """Když struktura nerozhodne, vrací se OBĚ možnosti — kaskáda § 5.2 se
    pak musí zeptat. Tiše vybrat by bylo porušení I‑1."""
    lexicon = czech_seed()
    candidates = lexicon.candidates(
        StructuralSignature(lemma="nebo", mood=Mood.UNKNOWN)
    )
    assert {p.operation for p in candidates} == {
        Operation.GROUP_OR,
        Operation.ALTERNATIVE,
    }


def test_difference_triggers_exist() -> None:
    """`kromě / mimo / vyjma` jsou cíle, které před termovou algebrou
    neexistovaly."""
    lexicon = czech_seed()
    for lemma in ("kromě", "mimo", "vyjma"):
        candidates = lexicon.candidates(StructuralSignature(lemma=lemma))
        assert [p.operation for p in candidates] == [Operation.GROUP_DIFF]


# --------------------------------------------------------------------------
# Životní cyklus vzoru
# --------------------------------------------------------------------------


def test_pattern_starts_as_hypothesis_and_can_be_confirmed() -> None:
    lexicon = Lexicon()
    trigger = Trigger(lemma="výhradně", mood=Mood.UNKNOWN)
    pattern = lexicon.teach(trigger, Operation.COMPLETE, learned_from="tah 7")
    assert pattern.status is PatternStatus.HYPOTHESIS
    assert lexicon.candidates(StructuralSignature(lemma="výhradně"))

    confirmed = lexicon.confirm(trigger.key())
    assert confirmed is not None and confirmed.status is PatternStatus.CONFIRMED


def test_revoking_removes_the_mapping_not_the_operation() -> None:
    """Odvolání maže mapování; operace v jádru zůstává nedotčená (I‑16)."""
    lexicon = czech_seed()
    key = Trigger(lemma="kromě", mood=Mood.UNKNOWN).key()
    lexicon.revoke(key)
    assert lexicon.candidates(StructuralSignature(lemma="kromě")) == ()
    assert Operation.GROUP_DIFF in {operation for operation, _ in MENU}
    # výrok zůstává v programu se statusem, nemizí
    assert any(p.trigger.key() == key for p in lexicon.all())


def test_signature_is_independent_of_entities() -> None:
    """Renaming test § 10: vzor sedí na strukturu, ne na konkrétní slova
    věty. Signatura proto nese jen spouštěč, tvar a tah."""
    first = StructuralSignature(lemma="každý", mood=Mood.ASSERTION, deprel="det")
    second = StructuralSignature(lemma="každý", mood=Mood.ASSERTION, deprel="det")
    assert first == second
    lexicon = czech_seed()
    assert lexicon.candidates(first) == lexicon.candidates(second)


def test_lex_program_round_trips_through_json() -> None:
    """§ 3.7: `LEX` je program — čitelný, diffovatelný, verzovatelný."""
    lexicon = czech_seed()
    lexicon.confirm(Trigger(lemma="nebo", mood=Mood.ASSERTION).key())
    restored = Lexicon.from_json(lexicon.to_json())
    assert [str(p) for p in restored.all()] == [str(p) for p in lexicon.all()]
    assert any(
        p.status is PatternStatus.CONFIRMED for p in restored.all()
    )


def test_seed_is_hypothesis_only() -> None:
    """Startovní profil je nabídka, ne pravda. Nic z něj není potvrzené,
    dokud to člověk nepotvrdí."""
    assert all(p.status is PatternStatus.HYPOTHESIS for p in czech_seed().all())


def test_deprel_narrows_a_trigger() -> None:
    lexicon = Lexicon(
        [
            LearnedPattern(
                trigger=Trigger(lemma="a", mood=Mood.UNKNOWN, deprel="cc"),
                operation=Operation.GROUP_AND,
                learned_from="test",
            )
        ]
    )
    assert lexicon.candidates(StructuralSignature(lemma="a", deprel="cc"))
    assert lexicon.candidates(StructuralSignature(lemma="a", deprel="advmod")) == ()
