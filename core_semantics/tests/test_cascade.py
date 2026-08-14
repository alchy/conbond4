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
    Predication,
    RoleReading,
    lexicon_tier,
    negation_tier,
    quantifier_tier,
    role_mapping_tier,
    surface_role,
)
from core_semantics.ast import Entity, Group, Quantifier, member_of
from core_semantics.lexicon import (
    LearnedPattern,
    Mood,
    Operation,
    Trigger,
    czech_seed,
)
from core_semantics.oracle import Reading, Token
from core_semantics.engine import Engine
from core_semantics.grounding import semantic_rejection
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
        roles = [r.name for r in candidate.predication.roles]
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
        Predication(
            "obsahovat",
            (
                RoleReading(ROLE_OBJECT, mention),
                RoleReading(ROLE_OBJECT, mention),
            ),
        )


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
    tier = base_consistency_tier(semantic_rejection(Engine(kb)))
    survivors, why = tier(generate(ambiguous), ambiguous)
    # Ani jedno čtení není s bází v rozporu, takže patro NEROZHODNE.
    # Dřív by rozhodlo — vztah `vidět` v bázi je — a to byla popularita,
    # ne konzistence (K‑7).
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


# „Petr jel v pondělí do Prahy." — DVĚ příslovečná určení, oba `obl`
TWO_CIRCUMSTANCES = _reading(
    _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Number="Sing", Case="Nom"),
    _token(2, "jel", "jet", "VERB", 0, "root", Number="Sing"),
    _token(3, "v", "v", "ADP", 4, "case"),
    _token(4, "pondělí", "pondělí", "NOUN", 2, "obl", Number="Sing", Case="Loc"),
    _token(5, "do", "do", "ADP", 6, "case"),
    _token(6, "Prahy", "Praha", "PROPN", 2, "obl", Number="Sing", Case="Gen"),
)


def test_two_circumstances_do_not_collide() -> None:
    """B‑9: pojmenovat okolnost jejím `deprel` nestačí — „v pondělí"
    i „do Prahy" jsou obě `obl`, takže by dostaly totéž jméno role a věta
    by spadla na duplicitě. A dvě určení má v češtině obrovská část vět;
    tahle je doslova z dialogu D."""
    candidates = generate(TWO_CIRCUMSTANCES)
    assert candidates
    roles = [r.name for r in candidates[0].predication.roles]
    assert "v+Loc" in roles and "do+Gen" in roles
    assert len(roles) == len(set(roles))


def test_surface_role_reads_preposition_and_case_not_semantics() -> None:
    """`v+Loc` je popis TVARU, ne významu (INV‑11)."""
    assert surface_role(TWO_CIRCUMSTANCES.tokens[3], TWO_CIRCUMSTANCES) == "v+Loc"
    assert surface_role(TWO_CIRCUMSTANCES.tokens[5], TWO_CIRCUMSTANCES) == "do+Gen"
    # bez předložky rozhoduje pád
    instrumental = _reading(
        _token(1, "jel", "jet", "VERB", 0, "root", Number="Sing"),
        _token(2, "autem", "auto", "NOUN", 1, "obl", Case="Ins"),
    )
    assert surface_role(instrumental.tokens[1], instrumental) == "Ins"


def test_learned_mapping_renames_an_unambiguous_surface_role() -> None:
    """Že `do+Gen` znamená `kam`, je naučené a odvolatelné tvrzení, ne
    vlastnost kódu (§ 3.7, § 12/1)."""
    tier = role_mapping_tier(czech_seed())
    renamed, _ = tier(generate(TWO_CIRCUMSTANCES), TWO_CIRCUMSTANCES)
    roles = [r.name for r in renamed[0].predication.roles]
    assert "kam" in roles


def test_an_unnamed_surface_role_is_asked_about_not_resolved() -> None:
    """`v+Loc` je „v Praze" i „v pondělí". Rozliší to jen význam nominálu,
    a ten se nehádá — jméno zůstane povrchové a systém se ZEPTÁ.

    Od N‑3 v seedu `v+Loc` NENÍ. Dvě hypotézy tam situaci neřešily:
    mapování zůstalo dvojznačné navždy, protože i po odpovědi člověka by
    kandidáti byli pořád dva. Teď tvar nemá význam žádný, odpověď ho dá
    a je jednoznačný."""
    tier = role_mapping_tier(czech_seed())
    renamed, why = tier(generate(TWO_CIRCUMSTANCES), TWO_CIRCUMSTANCES)
    assert why is not None and "v+Loc" in why
    roles = [r.name for r in renamed[0].predication.roles]
    assert "v+Loc" in roles  # nepřejmenováno


def test_two_candidates_are_reported_as_ambiguity_not_as_a_gap() -> None:
    """Druhá půlka: kdyby někdo naučil DVA významy téhož tvaru, hláška to
    musí říct jako dvojznačnost, ne jako mezeru — jsou to různé stavy
    a člověk na ně odpovídá jinak."""
    lexicon = czech_seed()
    lexicon.teach_role("v+Loc", "kde", learned_from="test")
    lexicon.teach_role("v+Loc", "kdy", learned_from="test")
    _, why = role_mapping_tier(lexicon)(
        generate(TWO_CIRCUMSTANCES), TWO_CIRCUMSTANCES
    )
    assert why is not None
    assert "kde" in why and "kdy" in why


def test_one_answer_names_the_shape_for_good() -> None:
    """A ta odpověď zavře celou třídu vět, ne jednu větu."""
    lexicon = czech_seed()
    lexicon.teach_role("v+Loc", "kde", learned_from="test")
    renamed, why = role_mapping_tier(lexicon)(
        generate(TWO_CIRCUMSTANCES), TWO_CIRCUMSTANCES
    )
    roles = [r.name for r in renamed[0].predication.roles]
    assert "kde" in roles and "v+Loc" not in roles


def test_revoking_a_role_mapping_leaves_the_surface_name() -> None:
    lexicon = czech_seed()
    lexicon.revoke_role("do+Gen->kam")
    renamed, _ = role_mapping_tier(lexicon)(
        generate(TWO_CIRCUMSTANCES), TWO_CIRCUMSTANCES
    )
    roles = [r.name for r in renamed[0].predication.roles]
    assert "do+Gen" in roles and "kam" not in roles


def test_identical_surface_forms_lead_to_a_question() -> None:
    """„v Praze v pondělí" — dvě určení téhož tvaru. Rozlišit by je šlo jen
    podle významu nominálu, takže se kaskáda ptá, místo aby hádala."""
    ambiguous = _reading(
        _token(1, "bydlí", "bydlet", "VERB", 0, "root", Number="Sing"),
        _token(2, "v", "v", "ADP", 3, "case"),
        _token(3, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc"),
        _token(4, "v", "v", "ADP", 5, "case"),
        _token(5, "pondělí", "pondělí", "NOUN", 1, "obl", Case="Loc"),
    )
    verdict = cascade(ambiguous)
    assert verdict.survivors == ()
    assert verdict.question is not None and "v+Loc" in verdict.question


def test_transform_tiers_run_even_when_one_reading_is_left() -> None:
    """Kaskáda se po rozhodnutí NESMÍ ukončit.

    Ukončení je správné pro filtry, ale patro, které čtení PŘEPISUJE, by
    se pak nespustilo vůbec — a to je tichá závislost na tom, kolik
    kandidátů zbylo. Věta s jedním čtením přejmenování rolí potřebuje
    stejně jako věta s pěti.
    """
    tiers = (*HARD_TIERS, role_mapping_tier(czech_seed()))
    verdict = cascade(TWO_CIRCUMSTANCES, tiers=tiers)
    decided = verdict.decided
    assert decided is not None
    roles = [r.name for r in decided.predication.roles]
    assert "kam" in roles  # přejmenováno i při jediném kandidátovi
    assert any("v+Loc" in step for step in verdict.trace)


def test_hard_tiers_run_morphology_before_anything_statistical() -> None:
    """§ 5.2: statistika je až za tvrdými filtry, protože dialogový objem
    anotací jsou desítky, ne tisíce."""
    assert HARD_TIERS == (agreement_tier, case_tier, negation_tier)
