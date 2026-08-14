"""V2 — kaskáda výběru čtení (§ 5.2).

Testuje se hlavně to, co je na kaskádě podstatné: že **negeneruje jedno
čtení**, že každé patro umí říct PROČ, a že při nerozhodnutém stavu vrací
OTÁZKU, ne favorita (I‑1).

Rozbory jsou nahrané ručně, ne z běžící služby — hermetičnost je záměr.
"""

from __future__ import annotations

from core_semantics.cascade import (
    HARD_TIERS,
    ROLE_OBJECT,
    ROLE_SUBJECT,
    agreement_tier,
    base_consistency_tier,
    cascade,
    case_tier,
    generate,
    lexicon_tier,
)
from core_semantics.ast import Entity, Group, member_of
from core_semantics.lexicon import Mood, czech_seed
from core_semantics.oracle import Reading, Token
from core_semantics.storage import KnowledgeBase

STAMP = "test"


def _token(
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


def _reading(*tokens: Token) -> Reading:
    return Reading(tokens=tokens, provenance=STAMP)


# „Obsahuje citron vitamíny?" — DOSLOVNÝ vstup ze § 5.2: parser podmět
# NEDAL, oba nominály označil jako `obj`, protože nominativ je tvarově
# shodný s akuzativem. Tohle je ta reálná zeď z dialogů.
LEMON = _reading(
    _token(1, "Obsahuje", "obsahovat", "VERB", 0, "root", Number="Sing", Person="3"),
    _token(2, "citron", "citron", "NOUN", 1, "obj", Number="Sing", Case="Nom"),
    _token(3, "vitamíny", "vitamín", "NOUN", 1, "obj", Number="Plur", Case="Acc"),
)

# Táž věta, ale s podmětem od parseru — snazší případ, který problém nemá.
LEMON_WITH_SUBJECT = _reading(
    _token(1, "Obsahuje", "obsahovat", "VERB", 0, "root", Number="Sing", Person="3"),
    _token(2, "citron", "citron", "NOUN", 1, "nsubj", Number="Sing", Case="Nom"),
    _token(3, "vitamíny", "vitamín", "NOUN", 1, "obj", Number="Plur", Case="Acc"),
)

# „Citron je ovoce." — spona
COPULA = _reading(
    _token(1, "Citron", "citron", "NOUN", 3, "nsubj", Number="Sing", Case="Nom"),
    _token(2, "je", "být", "AUX", 3, "cop", Number="Sing", Person="3"),
    _token(3, "ovoce", "ovoce", "NOUN", 0, "root", Number="Sing", Case="Nom"),
)


# --------------------------------------------------------------------------
# Generátor
# --------------------------------------------------------------------------


def test_generator_builds_roles_even_when_the_parser_gave_no_subject() -> None:
    """B‑8: tohle je motivační případ § 5.2 a dřív ho kaskáda neřešila.

    Role se skládají z nominálních kandidátů, ne z toho, co parser označil
    za podmět. Kdyby se záměna generovala jen tam, kde už podmět je, vzniklo
    by jedno čtení se DVĚMA rolemi `co` a bez podmětu — a takové čtení by
    jádro odmítlo, protože duplicitní role je chyba.
    """
    candidates = generate(LEMON)
    assert len(candidates) == 2
    for candidate in candidates:
        roles = [name for name, _ in candidate.predication.roles]
        assert roles == [ROLE_OBJECT, ROLE_SUBJECT]  # kanonicky setříděné
    subjects = {
        c.predication.role(ROLE_SUBJECT).lemma  # type: ignore[union-attr]
        for c in candidates
    }
    assert subjects == {"citron", "vitamín"}
    # Popisek nesmí tvrdit „záměna" tam, kde nebylo co zaměňovat.
    assert all(c.origin == "doplnění podmětu (parser ho nedal)" for c in candidates)


def test_duplicate_role_cannot_be_constructed() -> None:
    """Táž kontrola jako v `Atom`: čtení s dvěma rolemi téhož jména by
    V3 nikdy nepřevedla na platný atom, takže nesmí vzniknout."""
    import pytest

    from core_semantics.cascade import Mention, Predication

    mention = Mention(lemma="x", form="x", token_index=1, upos="NOUN")
    with pytest.raises(ValueError, match="vícekrát"):
        Predication("obsahovat", ((ROLE_OBJECT, mention), (ROLE_OBJECT, mention)))


def test_parser_reading_comes_first() -> None:
    """Orákulum navrhuje, kaskáda rozhoduje — parserovo čtení jde první."""
    candidates = generate(LEMON_WITH_SUBJECT)
    assert candidates[0].origin == "rozbor parseru"
    subject = candidates[0].predication.role(ROLE_SUBJECT)
    assert subject is not None and subject.lemma == "citron"


def test_copula_is_not_a_separate_lowering_branch() -> None:
    """Lemma přísudku nese spona, hlavou predikace je jmenná část — je to
    jedno pravidlo o tom, KDE lemma leží, ne druhá cesta ke druhé
    struktuře (§ 3.0)."""
    candidates = generate(COPULA)
    assert candidates
    predication = candidates[0].predication
    assert predication.predicate == "být"
    assert predication.role(ROLE_SUBJECT) is not None
    subject = predication.role(ROLE_SUBJECT)
    obj = predication.role(ROLE_OBJECT)
    assert subject is not None and subject.lemma == "citron"
    assert obj is not None and obj.lemma == "ovoce"


def test_generator_returns_nothing_for_an_unreadable_tree() -> None:
    """Prázdný výsledek je poctivá odpověď — «tuhle větu neumím přečíst»."""
    assert generate(_reading()) == ()


# --------------------------------------------------------------------------
# Tvrdá patra
# --------------------------------------------------------------------------


def test_agreement_decides_the_motivating_case_without_learning() -> None:
    """Reálná zeď z dialogů: „obsahuje" je Sing, „vitamíny" Plur, takže
    vitamíny podmět být nemohou. Rozhodne to morfologie, bez učení."""
    survivors, why = agreement_tier(generate(LEMON), LEMON)
    assert len(survivors) == 1
    assert why is not None and "shoda čísla" in why
    subject = survivors[0].predication.role(ROLE_SUBJECT)
    assert subject is not None and subject.lemma == "citron"


def test_case_grid_is_a_second_hard_signal() -> None:
    survivors, why = case_tier(generate(LEMON), LEMON)
    assert len(survivors) == 1
    assert why is not None and "pádová mřížka" in why


def test_cascade_reports_which_tier_decided() -> None:
    verdict = cascade(LEMON, mood=Mood.QUESTION)
    decided = verdict.decided
    assert decided is not None
    assert str(decided.predication) == "obsahovat(co:vitamín, kdo:citron)"
    assert verdict.question is None
    assert any("shoda čísla" in step for step in verdict.trace)


# --------------------------------------------------------------------------
# Nerozhodnuto ⇒ otázka, ne favorit
# --------------------------------------------------------------------------


def test_undecided_reading_produces_a_question() -> None:
    """Když tvrdé signály chybí, kaskáda se PTÁ. Tichá volba měnící význam
    není cesta nikdy (I‑1)."""
    # obě jména Sing i Nom — morfologie nerozhodne
    ambiguous = _reading(
        _token(1, "Vidí", "vidět", "VERB", 0, "root", Number="Sing"),
        _token(2, "Petr", "Petr", "PROPN", 1, "nsubj", Number="Sing", Case="Nom"),
        _token(3, "Pavel", "Pavel", "PROPN", 1, "obj", Number="Sing", Case="Nom"),
    )
    verdict = cascade(ambiguous)
    assert len(verdict.survivors) == 2
    assert verdict.decided is None
    assert verdict.question is not None
    assert "které z toho" in verdict.question


def test_base_consistency_narrows_but_never_adds() -> None:
    """Báze navrhuje, nerozhoduje (I‑2) — patro smí jen zúžit."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("r1"), Group("vidět")))
    ambiguous = _reading(
        _token(1, "Vidí", "vidět", "VERB", 0, "root", Number="Sing"),
        _token(2, "Petr", "Petr", "PROPN", 1, "nsubj", Number="Sing", Case="Nom"),
        _token(3, "Pavel", "Pavel", "PROPN", 1, "obj", Number="Sing", Case="Nom"),
    )
    tier = base_consistency_tier(kb.view())
    survivors, why = tier(generate(ambiguous), ambiguous)
    # oba kandidáti mají týž predikát, takže patro nerozhodne — a to je
    # správně: signatura vztahu je u obou čtení stejná
    assert len(survivors) == 2
    assert why is None


def test_lexicon_tier_reports_ambiguity_instead_of_resolving_it() -> None:
    """„nebo" má dvě čtení; patro to zapíše do trace a rozhodnutí nechá
    na doptání."""
    with_or = _reading(
        _token(1, "má", "mít", "VERB", 0, "root", Number="Sing"),
        _token(2, "Petr", "Petr", "PROPN", 1, "nsubj", Number="Sing", Case="Nom"),
        _token(3, "psa", "pes", "NOUN", 1, "obj", Number="Sing", Case="Acc"),
        _token(4, "nebo", "nebo", "CCONJ", 5, "cc"),
        _token(5, "kočku", "kočka", "NOUN", 3, "conj", Number="Sing", Case="Acc"),
    )
    tier = lexicon_tier(czech_seed())
    survivors, why = tier(generate(with_or), with_or)
    assert len(survivors) == len(generate(with_or))  # nic nevyřadilo
    assert why is not None and "nebo" in why
    assert "group_or" in why and "alt" in why


def test_verdict_renders_its_reasoning() -> None:
    verdict = cascade(LEMON, mood=Mood.QUESTION)
    rendered = verdict.render()
    assert rendered[0].startswith("kandidátů:")
    assert any("PROČ" in line for line in rendered)


def test_hard_tiers_run_morphology_before_anything_statistical() -> None:
    """§ 5.2: statistika je až za tvrdými filtry, protože dialogový objem
    anotací jsou desítky, ne tisíce."""
    assert HARD_TIERS == (agreement_tier, case_tier)
