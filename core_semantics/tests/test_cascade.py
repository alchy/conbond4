"""V2 — kaskáda výběru čtení (§ 5.2).

Testuje se hlavně to, co je na kaskádě podstatné: že **negeneruje jedno
čtení**, že každé patro umí říct PROČ, a že při nerozhodnutém stavu vrací
OTÁZKU, ne favorita (I‑1).

Rozbory jsou nahrané ručně, ne z běžící služby — hermetičnost je záměr.
"""

from __future__ import annotations

from dataclasses import replace

from core_semantics.cascade import (
    HARD_TIERS,
    dropped_tokens,
    role_question,
    surface_roles,
    ROLE_OBJECT,
    ROLE_SUBJECT,
    agreement_tier,
    attribute_tier,
    prodrop_tier,
    feature_values,
    base_consistency_tier,
    cascade,
    case_tier,
    generate,
    Predication,
    RoleReading,
    lexicon_tier,
    negation_tier,
    passive_tier,
    quantifier_tier,
    role_mapping_tier,
    surface_role,
)
from core_semantics.ast import Entity, Group, Quantifier, member_of
from core_semantics.lexicon import (
    LearnedPattern,
    Mood,
    Operation,
    PatternStatus,
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


# --------------------------------------------------------------------------
# Předložka vylučuje jmennou část — N‑4
# --------------------------------------------------------------------------
#
# „Petr byl v Praze." má v UD kořen `Praze` a sponu `byl`, takže sponové
# pravidlo dělalo z Prahy jmennou část přísudku: `co:Praha`, tedy „Petr
# BYL Prahou". Předložka u kořene je tvrdý strukturní signál, že jmenná
# část to není — „být prostředek" ji nemá, „být v Praze" ji má vždycky.
#
# Není to nové pravidlo o významu: role zůstane POVRCHOVÁ (`v+Loc`) a co
# znamená, se učí odpovědí. Jen se nepřevezme jmenná část tam, kde ji
# stavba vylučuje.


def _copula_with_preposition() -> Reading:
    return _reading(
        _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing"),
        _token(2, "byl", "být", "AUX", 4, "cop", Number="Sing", Polarity="Pos"),
        _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
        _token(4, "Praze", "Praha", "PROPN", 0, "root", Case="Loc", NameType="Geo", Number="Sing"),
    )


def _copula_without_preposition() -> Reading:
    return _reading(
        _token(1, "Auto", "auto", "NOUN", 3, "nsubj", Case="Nom", Number="Sing"),
        _token(2, "je", "být", "AUX", 3, "cop", Number="Sing", Polarity="Pos"),
        _token(3, "prostředek", "prostředek", "NOUN", 0, "root", Case="Nom", Number="Sing"),
    )


def _roles_of(reading: Reading) -> list[str]:
    verdict = cascade(reading)
    assert verdict.decided is not None
    return [r.name for r in verdict.decided.predication.roles]


def test_a_preposition_at_the_root_means_it_is_not_the_nominal_predicate() -> None:
    """JÁDRO N‑4. „Petr BYL Prahou" je nesmysl, který se tvářil jako čtení."""
    roles = _roles_of(_copula_with_preposition())
    # Tvar nese SIGNÁL Z ROZBORU *(W‑61)*: „Praze" má `NameType=Geo`.
    assert "v+Loc/Geo" in roles
    assert "co" not in roles


def test_the_role_stays_surface_and_is_asked_about() -> None:
    """Nepřevzít jmennou část NENÍ totéž co vědět, o co jde. `v+Loc` je
    místo i čas — rozhodnout to tady by byla táž tichá volba, jen o patro
    jinde."""
    verdict = cascade(_copula_with_preposition())
    assert verdict.decided is not None
    assert surface_roles(verdict.decided.predication) == ("v+Loc/Geo",)
    assert role_question(verdict.decided.predication) is not None


def test_a_nominal_predicate_without_a_preposition_is_untouched() -> None:
    """PROTIPŘÍKLAD REVIEWERA (a). Tam, kde předložka NENÍ, je jmenná
    část správně — a „Auto je dopravní prostředek" na ní stojí."""
    roles = _roles_of(_copula_without_preposition())
    assert "co" in roles
    assert not any("+" in name for name in roles)


def test_the_answer_turns_the_shape_into_a_place() -> None:
    """A po odpovědi je to `kde`, takže se fillér zakotví jako `Place`
    (§ 3.6) — sort z ROLE, ne ze slova."""
    lexicon = czech_seed()
    lexicon.teach_role("v+Loc/Geo", "kde", learned_from="test")
    verdict = cascade(
        _copula_with_preposition(), tiers=(*HARD_TIERS, role_mapping_tier(lexicon))
    )
    assert verdict.decided is not None
    assert "kde" in [r.name for r in verdict.decided.predication.roles]


# --------------------------------------------------------------------------
# `iobj` není `obj` — N‑5b
# --------------------------------------------------------------------------
#
# „Děti mají rády zmrzlinu." se dlouho nepřečetla VŮBEC: parser označí
# „rády" jako `iobj`, kaskáda to slévala s `obj` na roli `co`, dva členy
# tak dostaly touž roli, čtení s duplicitou se nesmí vyrobit a nezbylo
# ani jedno.
#
# Rozbor ta dvě místa ROZLIŠUJE — zahazovala to kaskáda, ne čeština. Táž
# třída jako B‑9, jen o patro blíž jádru.


def _two_objects() -> Reading:
    return _reading(
        _token(1, "Děti", "dítě", "NOUN", 2, "nsubj", Case="Nom", Number="Plur"),
        _token(2, "mají", "mít", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
        _token(3, "rády", "rád", "ADJ", 2, "iobj", Number="Plur", Variant="Short"),
        _token(4, "zmrzlinu", "zmrzlina", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )


def test_an_indirect_object_does_not_collide_with_the_direct_one() -> None:
    """JÁDRO N‑5b. Dřív z téhle věty nezbylo ani jedno čtení."""
    verdict = cascade(_two_objects())
    assert verdict.decided is not None
    roles = [r.name for r in verdict.decided.predication.roles]
    assert sorted(roles) == ["co", "iobj", "kdo"]


def test_nothing_from_the_sentence_is_dropped() -> None:
    """Přečíst ji tak, že by „rády" vypadlo, by bylo horší než ji
    nepřečíst — tichá ztráta se nepozná."""
    reading = _two_objects()
    verdict = cascade(reading)
    assert verdict.decided is not None
    assert verdict.lost == ()
    assert dropped_tokens(reading, verdict.decided.predication) == ()


def test_the_new_name_is_surface_so_the_system_asks_what_it_means() -> None:
    """Nepředstírá se, že se ví, o co jde: `iobj` je tady CHYBNÝ ROZBOR
    („rády" je příslovce), kdežto skutečný nepřímý předmět dá čeština
    jako `obl:arg`. Uhodnout jedno jméno pro obojí by byl dohad
    o významu — a od N‑3 na to existuje otázka."""
    verdict = cascade(_two_objects())
    assert verdict.decided is not None
    assert surface_roles(verdict.decided.predication) == ("iobj",)
    assert role_question(verdict.decided.predication) is not None


def test_a_plain_direct_object_is_untouched() -> None:
    """PROTIPŘÍKLAD REVIEWERA (a). „Filip má auto." je obyčejný `obj`
    a musí dál číst `co` bez otázky."""
    plain = _reading(
        _token(1, "Filip", "Filip", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        _token(2, "má", "mít", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
        _token(3, "auto", "auto", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )
    verdict = cascade(plain)
    assert verdict.decided is not None
    assert [r.name for r in verdict.decided.predication.roles] == ["co", "kdo"]
    assert surface_roles(verdict.decided.predication) == ()


def test_a_real_indirect_object_keeps_its_own_shape() -> None:
    """PROTIPŘÍKLAD REVIEWERA (b). Skutečný nepřímý předmět je v češtině
    `obl:arg`, tedy `Dat:arg` — a ten se téhle změny nedotkl."""
    dative = _reading(
        _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        _token(2, "dal", "dát", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
        _token(3, "Pavlovi", "Pavel", "PROPN", 2, "obl:arg", Case="Dat", Number="Sing"),
        _token(4, "knihu", "kniha", "NOUN", 2, "obj", Case="Acc", Number="Sing"),
    )
    verdict = cascade(dative)
    assert verdict.decided is not None
    assert "Dat:arg" in [r.name for r in verdict.decided.predication.roles]


# --------------------------------------------------------------------------
# Shoda se porovnává PRŮNIKEM hodnot — W‑32
# --------------------------------------------------------------------------
#
# UD píše víceznačný tvar výčtem: „sbírala" nese `Gender=Fem,Neut`
# a `Number=Plur,Sing`, protože týž tvar je ženský jednotný („matka
# sbírala") i střední množný („děvčata sbírala"). Není to konjunkce dvou
# tvrzení, je to PŘIZNANÁ VÍCEZNAČNOST — a porovnávat ji rovností znamená
# žádat, aby byl podmět stejně víceznačný jako přísudek.
#
# Odmítnutí bylo hlasité, takže to nebyla vada bezpečnosti. Bylo to
# FALEŠNĚ NEGATIVNÍ ČTENÍ: dobrá věta zahozená ze špatného důvodu. Na
# encyklopedickém korpusu (238 vět) blokovala tahle jediná záměna 29 vět,
# ve všech jako JEDINÝ blokátor.


def _clause(subject: str, subject_feats: dict[str, str], verb: str,
            verb_feats: dict[str, str]) -> Reading:
    return Reading(
        tokens=(
            _token(1, subject, subject.lower(), "NOUN", 2, "nsubj", Case="Nom", **subject_feats),
            _token(2, verb, verb.lower(), "VERB", 0, "root", **verb_feats),
            _token(3, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )


def test_a_homonymous_predicate_no_longer_rejects_an_unambiguous_subject() -> None:
    """„Matka sbírala." — podmět je jednoznačně `Sing`, přísudek přiznává
    `Plur,Sing`. Průnik je neprázdný, takže se shodnout MOHOU a věta
    projde."""
    reading = _clause(
        "Matka", {"Number": "Sing", "Gender": "Fem"},
        "sbírala", {"Number": "Plur,Sing", "Gender": "Fem,Neut"},
    )
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors, why


def test_an_impossible_agreement_is_still_rejected_out_loud() -> None:
    """„Psi byla." — na ČÍSLE je průnik neprázdný (`Plur` × `Plur,Sing`),
    takže samotné číslo by tu větu pustilo. Zahodí ji až ROD: `Masc`
    proti `Fem,Neut` se shodnout nemůže. Bez kontroly rodu by přechod na
    průnik tuhle větu propustil — proto rod patro nezpřísňuje nad rámec
    toho, co dělalo, jen nahrazuje práci, kterou dřív odváděla rovnost."""
    reading = _clause(
        "Psi", {"Number": "Plur", "Gender": "Masc"},
        "byla", {"Number": "Plur,Sing", "Gender": "Fem,Neut"},
    )
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors == ()
    assert why is not None and "shoda rodu" in why


def test_a_missing_feature_never_breaks_the_agreement() -> None:
    """Co se neříká, se nedá popřít. Přísudek bez rodu (přítomný čas)
    o rodu podmětu netvrdí nic, takže na něm shoda padnout nesmí."""
    reading = _clause(
        "Citron", {"Number": "Sing", "Gender": "Masc"},
        "obsahuje", {"Number": "Sing"},
    )
    survivors, _ = agreement_tier(generate(reading), reading)
    assert survivors


def test_the_intersection_is_computed_from_one_shared_helper() -> None:
    """Táž úvaha rozhoduje o kandidátovi na antecedent i o zahození
    čtení. Dvě kopie by se rozešly a jedna z nich by dřív nebo později
    začala trestat víceznačnost znovu."""
    import inspect

    from core_semantics import grounding

    assert feature_values("Fem,Neut") == {"Fem", "Neut"}
    assert not (feature_values("Masc") & feature_values("Fem,Neut"))
    assert "feature_values" in inspect.getsource(grounding.Discourse.candidates)


# --------------------------------------------------------------------------
# Kvantifikovaný podmět — W‑33
# --------------------------------------------------------------------------
#
# „Několik měření … podpořilo." Čeština má u počitatelných výrazů přísudek
# v NEUTRU SINGULÁRU a jméno v genitivu plurálu; řídícím členem shody je
# ten kvantifikátor, ne to jméno.
#
# **Pravidlo je KLADNÉ, ne výjimka.** Kdyby patro u `det:numgov` shodu jen
# vyplo, byla by to díra: prošlo by i „Několik hostů přišli." Ověřuje se
# proto, že přísudek odpovídá tomu, co ta konstrukce žádá — a věta, která
# to poruší, padne dál.


def _quantified_clause(verb: str, verb_feats: dict[str, str]) -> Reading:
    """„Několik hostů <sloveso>." — podmět v genitivu, řízený `det:numgov`."""
    return Reading(
        tokens=(
            _token(1, "Několik", "několik", "DET", 2, "det:numgov", Case="Nom"),
            _token(2, "hostů", "host", "NOUN", 3, "nsubj", Case="Gen", Number="Plur", Gender="Masc"),
            _token(3, verb, verb.lower(), "VERB", 0, "root", **verb_feats),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )


def test_a_quantified_subject_no_longer_blocks_the_reading() -> None:
    """Podmět je `Plur`, přísudek `Sing` — a přesto je to bezvadná čeština,
    protože shodu řídí kvantifikátor. Dokud se počítala proti tomu jménu,
    padla každá věta typu „několik / mnoho / pět"."""
    reading = _quantified_clause("přišlo", {"Number": "Sing", "Gender": "Neut"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors, why


def test_a_quantified_subject_with_a_plural_predicate_still_falls() -> None:
    """PROTIPŘÍKLAD, a je to celý rozdíl mezi opravou a dírou. Kdyby se
    u `det:numgov` shoda jen VYPNULA, prošlo by „Několik hostů přišli."
    Pravidlo je kladné: ověřuje se, co konstrukce v češtině ŽÁDÁ."""
    reading = _quantified_clause("přišli", {"Number": "Plur", "Gender": "Masc"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors == ()
    assert why is not None and "STŘEDNÍM JEDNOTNÉM" in why


def test_the_controller_is_read_from_the_parse_label_not_from_a_word_list() -> None:
    """`det:numgov` dává UD právě proto, že ten determinátor ŘÍDÍ PÁD své
    hlavy — parser nic neskrývá. Seznam slov („několik", „mnoho", „pět")
    by byl druhé místo, kde se to rozhoduje, a rozešel by se s parserem."""
    import inspect

    from core_semantics.cascade import _quantified

    source = inspect.getsource(_quantified)
    assert "det:numgov" in source
    for word in ("několik", "mnoho", "pět"):
        assert f'"{word}"' not in source


def test_the_two_branches_never_swap_places() -> None:
    """Kvantifikace a koordinace jsou DVĚ RŮZNÉ konstrukce s OPAČNÝM
    požadavkem: první žádá střední jednotné, druhá množné číslo. Kdyby si
    ty větve prohodily místo, prošlo by „Několik hostů přišli." i „Petr
    a Pavel četl knihu." — obojí je špatně česky.

    Do #75 tady stál test, který držel, že koordinace PADÁ, protože se
    tehdy záměrně neopravovala. Tu hranici zrušilo zadání #76; zůstává
    z ní to, co platí dál — že se ty dvě větve nesmí plést.
    """
    from core_semantics.cascade import _coordinated, _quantified

    quantified = _quantified_clause("přišlo", {"Number": "Sing", "Gender": "Neut"})
    coordinated = _coordinated_clause("četli", {"Number": "Plur", "Gender": "Masc"})
    for reading, je_kvantifikace, je_koordinace in (
        (quantified, True, False),
        (coordinated, False, True),
    ):
        subject = generate(reading)[0].predication.role(ROLE_SUBJECT)
        assert subject is not None
        assert _quantified(subject, reading) is je_kvantifikace
        # `_coordinated` má TŘI stavy; tady stačí, že u kvantifikace
        # koordinaci nenajde vůbec (`None`) a u koordinace ano.
        assert (_coordinated(subject, reading) is not None) is je_koordinace


# --------------------------------------------------------------------------
# Koordinovaný podmět — W‑35
# --------------------------------------------------------------------------
#
# „Karel Čapek a jeho bratr Josef **byli** aktéry…" Přísudek je v plurálu
# podle CELÉ koordinace, ale UD dává jako `nsubj` první člen v singuláru
# a zbytek věší na něj jako `conj`.
#
# ROD SE TU NEOVĚŘUJE a je to PŘIZNANÁ MEZ, ne opomenutí: čeština ho
# u koordinace neřeší průnikem, ale pravidly (muž + žena → mužský
# životný), a tohle patro to pravidlo celé nemá. Hádat ho by byl tichý
# default tam, kde se rozhoduje o zahození čtení.


def _coordinated_clause(verb: str, verb_feats: dict[str, str]) -> Reading:
    """„Petr a Pavel <sloveso> knihu."

    Spojka `a` visí jako `cc` pod druhým členem — přesně jak ji dává UD,
    a je to podstatné: typ koordinace se čte Z TÉ HRANY, ne z pořadí slov.
    """
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, "a", "a", "CCONJ", 3, "cc"),
            _token(3, "Pavel", "Pavel", "PROPN", 1, "conj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(4, verb, verb.lower(), "VERB", 0, "root", **verb_feats),
            _token(5, "knihu", "kniha", "NOUN", 4, "obj", Case="Acc", Number="Sing", Gender="Fem"),
            _token(6, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )


def _coordination_with(mark: str, verb: str, verb_feats: dict[str, str]) -> Reading:
    """Táž stavba, jiná spojka — minimální pár na typ koordinace."""
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, mark, mark, "CCONJ", 3, "cc"),
            _token(3, "Pavel", "Pavel", "PROPN", 1, "conj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(4, verb, verb.lower(), "VERB", 0, "root", **verb_feats),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )


def test_a_coordinated_subject_no_longer_blocks_the_reading() -> None:
    """Podmět je `Sing`, přísudek `Plur` — a přesto je to bezvadná čeština,
    protože číslo je vlastnost CELÉ koordinace, ne jejího prvního členu."""
    reading = _coordinated_clause("četli", {"Number": "Plur", "Gender": "Masc"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors, why


def test_a_coordinated_subject_with_a_singular_predicate_still_falls() -> None:
    """PROTIPŘÍKLAD. Pravidlo je kladné: dva a víc členů ŽÁDÁ plurál,
    takže „Petr a Pavel četl knihu." padne a řekne proč. Kdyby se shoda
    u koordinace jen vypnula, prošlo by to."""
    reading = _coordinated_clause("četl", {"Number": "Sing", "Gender": "Masc"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors == ()
    assert why is not None and "MNOŽNÉM" in why


def test_a_disjunction_does_not_demand_the_plural() -> None:
    """„Vesmír **či** kosmos JE…" — disjunkce nabízí ALTERNATIVU, ne
    součet, takže jednotné číslo je správně. Verze pravidla „dva a víc
    členů → plurál" tuhle větu shodila; zúžilo ho MĚŘENÍ na korpusu, ne
    úvaha od stolu."""
    reading = _coordination_with("či", "četl", {"Number": "Sing", "Gender": "Masc"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors, why


def test_a_conjunction_still_demands_the_plural() -> None:
    """Druhá půlka téhož minimálního páru: táž stavba se spojkou „a"
    plurál ŽÁDÁ. Kdyby zúžení spolklo i tenhle případ, byla by z opravy
    díra."""
    reading = _coordination_with("a", "četl", {"Number": "Sing", "Gender": "Masc"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors == ()
    assert why is not None and "MNOŽNÉM" in why


def test_a_predicate_before_the_subject_may_agree_with_the_nearest() -> None:
    """„Ke chřipce **se přidal** zánět ledvin a zápal plic." — když
    přísudek stojí PŘED podmětem, čeština připouští shodu s nejbližším
    členem. Žádat tu plurál znamená zahodit bezvadnou větu."""
    reading = Reading(
        tokens=(
            _token(1, "přidal", "přidat", "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(2, "zánět", "zánět", "NOUN", 1, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(3, "a", "a", "CCONJ", 4, "cc"),
            _token(4, "zápal", "zápal", "NOUN", 2, "conj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors, why


def test_the_gender_of_a_coordination_is_a_declared_limit() -> None:
    """MEZ SE ŘÍKÁ NAHLAS. „Petr a Marie četli." má rod, který čeština
    počítá pravidly (muž + žena → mužský životný), ne průnikem. Patro to
    pravidlo nemá, takže rod u koordinace NEOVĚŘUJE — a je to napsané
    v kódu, ne mlčky."""
    import inspect

    from core_semantics.cascade import agreement_tier as tier

    assert "PŘIZNANÁ MEZ" in inspect.getsource(tier)

    mixed = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, "a", "a", "CCONJ", 3, "cc"),
            _token(3, "Marie", "Marie", "PROPN", 1, "conj", Case="Nom", Number="Sing", Gender="Fem"),
            _token(4, "četli", "číst", "VERB", 0, "root", Number="Plur", Gender="Masc"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )
    survivors, _ = agreement_tier(generate(mixed), mixed)
    assert survivors, "smíšený rod projde — ověřuje se jen číslo"


def test_a_quantified_subject_is_not_treated_as_a_coordination() -> None:
    """Obě větve mají OPAČNÝ požadavek a nesmí se plést. „Několik hostů
    přišli." má kvantifikátor a padá na STŘEDNÍM JEDNOTNÉM — kdyby ho
    chytila koordinační větev, prošlo by to, protože přísudek je
    v plurálu."""
    reading = _quantified_clause("přišli", {"Number": "Plur", "Gender": "Masc"})
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors == ()
    assert why is not None and "STŘEDNÍM JEDNOTNÉM" in why


def test_a_coordination_that_does_not_demand_the_plural_still_accepts_it() -> None:
    """TŘI STAVY, NE DVA. Když koordinace plurál NEŽÁDÁ (disjunkce nebo
    přísudek před podmětem), nesmí věta spadnout na obyčejné porovnání
    s PRVNÍM ČLENEM — „Nad hrobem **promluvili** básník Josef Hora, …" má
    plurál a je správně. Přijímá se obojí; odmítá se jen to, co není ani
    jedno.

    Přesně tenhle případ vyrobilo první zúžení a našlo ho až měření na
    korpusu, ne úvaha."""
    reading = Reading(
        tokens=(
            _token(1, "promluvili", "promluvit", "VERB", 0, "root", Number="Plur", Gender="Masc"),
            _token(2, "básník", "básník", "NOUN", 1, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(3, "a", "a", "CCONJ", 4, "cc"),
            _token(4, "spisovatel", "spisovatel", "NOUN", 2, "conj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    survivors, why = agreement_tier(generate(reading), reading)
    assert survivors, why


def test_the_three_states_are_distinguishable() -> None:
    """`None` (koordinace tu není) se nesmí slít s `False` (je tu, ale
    plurál nežádá). Kdyby se slily, spadne druhý případ na porovnání
    s prvním členem — a to je ta vada, kterou tenhle stav odděluje."""
    from core_semantics.cascade import _coordinated

    zada = _coordinated_clause("četli", {"Number": "Plur", "Gender": "Masc"})
    nezada = _coordination_with("či", "četl", {"Number": "Sing", "Gender": "Masc"})
    bez = _quantified_clause("přišlo", {"Number": "Sing", "Gender": "Neut"})
    for reading, ocekavano in ((zada, True), (nezada, False), (bez, None)):
        subject = generate(reading)[0].predication.role(ROLE_SUBJECT)
        assert subject is not None
        assert _coordinated(subject, reading) is ocekavano


# --------------------------------------------------------------------------
# Vedlejší věta jako role hlavní predikace — W‑45
# --------------------------------------------------------------------------
#
# „Odjel, PROTOŽE pršelo." Vedlejší věta je okolnost hlavního děje, tedy
# jeho ROLE, a jméno té role nese SPOJKA. Tím se liší od genitivního
# přívlastku: tam byl směr vlastností VĚTY a naučit se nedal, tady je
# odpověď v TVARU, takže se naučit smí.


def _subordinate(mark: str | None, verb: str = "pršet") -> Reading:
    tokens = [
        _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
        _token(2, "odjel", "odjet", "VERB", 0, "root", Number="Sing", Gender="Masc"),
        _token(4, "pršelo", verb, "VERB", 2, "advcl", Number="Sing", Gender="Neut"),
        _token(5, ".", ".", "PUNCT", 2, "punct"),
    ]
    if mark is not None:
        tokens.insert(2, _token(3, mark, mark, "SCONJ", 4, "mark"))
    return Reading(tokens=tuple(tokens), provenance="test")


def test_a_subordinate_clause_becomes_a_role_of_the_main_predication() -> None:
    """Vedlejší věta se přestane ztrácet: stane se rolí hlavní predikace,
    jejímž fillerem je DĚJ té vedlejší věty."""
    from core_semantics.cascade import subordinate_clauses

    reading = _subordinate("protože")
    assert subordinate_clauses(reading) == (("protože", "pršet", 4),)


def test_without_a_conjunction_nothing_is_substituted() -> None:
    """Bez spojky není z čeho jméno role přečíst. Hádat ho z pořadí slov
    by znamenalo vymyslet si význam (INV‑11), takže se nedosadí nic
    a člen zůstane ztracený — tedy se na něj ZEPTÁ."""
    from core_semantics.cascade import subordinate_clauses

    assert subordinate_clauses(_subordinate(None)) == ()


def test_the_conjunction_is_returned_not_the_role_name() -> None:
    """Co ta spojka znamená, je NAUČENÉ a odvolatelné tvrzení v lexikonu.
    Kdyby to rozhodovala tahle funkce, byl by v interpretu schovaný
    seznam českých spojek — táž vada jako u seznamu kvantifikátorů."""
    import inspect

    from core_semantics.cascade import subordinate_clauses

    source = inspect.getsource(subordinate_clauses)
    for spojka in ("protože", "když", "aby", "pokud"):
        assert f'"{spojka}"' not in source


def test_a_clause_under_a_noun_is_not_taken() -> None:
    """`advcl` pod JMÉNEM není okolnost hlavního děje, ale přívlastek toho
    jména — jiný vztah, který patří k `acl`, ne sem."""
    from core_semantics.cascade import subordinate_clauses

    pod_jmenem = Reading(
        tokens=(
            _token(1, "programy", "program", "NOUN", 2, "nsubj", Case="Nom", Number="Plur", Gender="Masc"),
            _token(2, "existují", "existovat", "VERB", 0, "root", Number="Plur"),
            _token(3, "pokud", "pokud", "SCONJ", 4, "mark"),
            _token(4, "jedná", "jednat", "VERB", 1, "advcl", Number="Sing", Gender="Neut"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    assert subordinate_clauses(pod_jmenem) == ()


def test_the_other_embedded_relations_are_untouched() -> None:
    """`acl`, `csubj`, `xcomp` ani `ccomp` tahle větev nechytá — každý
    z nich je jiné rozhodnutí a míchat je znamená měřit několik věcí
    naráz."""
    from core_semantics.cascade import subordinate_clauses

    for deprel in ("acl", "csubj", "xcomp", "ccomp"):
        jiny = Reading(
            tokens=(
                _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
                _token(2, "odjel", "odjet", "VERB", 0, "root", Number="Sing", Gender="Masc"),
                _token(3, "aby", "aby", "SCONJ", 4, "mark"),
                _token(4, "pršelo", "pršet", "VERB", 2, deprel, Number="Sing", Gender="Neut"),
                _token(5, ".", ".", "PUNCT", 2, "punct"),
            ),
            provenance="test",
        )
        assert subordinate_clauses(jiny) == (), deprel


def test_the_second_level_of_nesting_falls_out_loud() -> None:
    """Vnoření do DRUHÉ úrovně je nad mez `max_depth=1` a padá s hláškou,
    nikdy tiše. Korpus na tu hloubku dosáhne (7 cest ze 60), takže to
    není teoretická obava."""
    import pytest as _pytest

    from core_semantics.ast import (
        DepthExceeded,
        Entity,
        Group,
        Quantifier,
        RelationInstance,
        atom,
        role,
    )
    from core_semantics.storage import KnowledgeBase

    kb = KnowledgeBase()
    vnitrni = kb.attach(atom("pršet", role("kde", Group("Praha"), Quantifier.SELF)))
    prvni = kb.attach(
        atom("odjet", role("kdo", Entity("Petr")), role("proč", RelationInstance(vnitrni)))
    )
    with _pytest.raises(DepthExceeded) as chyba:
        kb.attach(
            atom("říct", role("kdo", Entity("Jan")), role("co", RelationInstance(prvni)))
        )
    assert "hloubku vnoření 2" in str(chyba.value)


def test_the_learned_conjunction_stops_asking_on_the_next_sentence() -> None:
    """PRŮCHOD VEŘEJNÝM VSTUPEM. Dokud spojku nikdo nepojmenoval, zůstane
    role povrchová (`advcl:protože`) a systém se ptá; po odpovědi je z ní
    `proč` a DRUHÁ VĚTA S TOUŽ SPOJKOU se už neptá — to je celý rozdíl
    proti genitivnímu přívlastku, kde se význam učit nesmí."""
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation,
        PatternStatus,
        Trigger,
        czech_seed,
    )
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session, names_role

    prvni = _subordinate("protože")
    druha = Reading(
        tokens=(
            _token(1, "Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, "odjel", "odjet", "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(3, "protože", "protože", "SCONJ", 4, "mark"),
            _token(4, "sněžilo", "sněžit", "VERB", 2, "advcl", Number="Sing", Gender="Neut"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )

    class _Rec:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(
                text=text, readings=(prvni if "Petr" in text else druha,)
            )

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="PROPN", number="Sing", case="Nom", deprel="nsubj"
            ),
            operation=Operation.SELF,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    prvni_vysledek = session.utter("Petr odjel, protože pršelo.", _Rec())
    assert prvni_vysledek.predication is not None
    assert "advcl:protože" in str(prvni_vysledek.predication)

    session.play(names_role("Je to důvod.", prvni, "advcl:protože", "proč"))
    druhy = session.utter("Jan odjel, protože sněžilo.", _Rec())
    assert druhy.predication is not None
    assert "proč:∃sněžit" in str(druhy.predication)
    assert "advcl:" not in str(druhy.predication)


def test_a_sentence_with_an_unnamed_subordinate_role_is_not_written() -> None:
    """B‑19. Než vzniklo patro `subordinate_tier`, byla vedlejší věta
    ZTRACENÝM ČLENEM a zápis blokovala. Patro z ní udělalo ROLI, ale tu
    zábranu jí zapomnělo dát — a odpověď `→@` pak větu zapsala PODRUHÉ,
    jednou s povrchovým jménem role a podruhé s naučeným. V bázi by
    ležely dva výroky o téže větě a ten první by nikdo neodvolal.

    Je to táž vada, kterou u ztraceného členu hlídá zábrana nad
    `turn.lost`; patro ji jen obešlo zezadu."""
    from core_semantics.lexicon import (
        LearnedPattern,
        Operation,
        PatternStatus,
        Trigger,
        czech_seed,
    )
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session, names_role

    reading = _subordinate("protože")

    class _Rec:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(text=text, readings=(reading,))

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="PROPN", number="Sing", case="Nom", deprel="nsubj"
            ),
            operation=Operation.SELF,
            learned_from="test",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    prvni = session.utter("Petr odjel, protože pršelo.", _Rec())
    assert prvni.statement_id is None, (
        "dokud role nemá jméno, věta se nezapisuje — jinak ji odpověď "
        "zapíše podruhé"
    )
    odpoved = session.play(
        names_role("Je to důvod.", reading, "advcl:protože", "proč")
    )
    assert odpoved.statement_id is not None
    napsane = [
        statement
        for statement in session.kb.active()
        if getattr(statement.formula, "predicate", "") == "odjet"
    ]
    assert len(napsane) == 1, f"věta smí být v bázi JEDNOU, je {len(napsane)}×"
    assert "proč:∃pršet" in str(napsane[0].formula)


# --------------------------------------------------------------------------
# Víceslovné jméno — B‑21
# --------------------------------------------------------------------------
#
# „Josef Hora" není hlava s přívlastkem, je to JEDNO JMÉNO; UD to říká
# hranou `flat`. Dokud se ta hrana zahazovala, četla se věta jako fakt
# o uzlu `Josef` — a to nebyla ztráta členu, byl to ZÁPIS O JINÉM UZLU.


def _full_name(first: str, second: str, verb: str = "zemřít") -> Reading:
    return Reading(
        tokens=(
            _token(1, first, first, "PROPN", 3, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, second, second, "PROPN", 1, "flat", Case="Nom", Number="Sing", Gender="Masc"),
            _token(3, verb, verb, "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )


def test_a_multiword_name_is_one_node() -> None:
    """Příjmení se skládá do lemmatu uzlu, ne zahazuje."""
    reading = _full_name("Josef", "Hora")
    predication = generate(reading)[0].predication
    subject = predication.role(ROLE_SUBJECT)
    assert subject is not None
    assert subject.lemma == "Josef_Hora"


def test_two_people_sharing_a_first_name_do_not_merge() -> None:
    """NEJDRAŽŠÍ PŮLKA TÉHLE VADY. „Karel Čapek" a „Karel Poláček" by
    tiše splynuli v jeden uzel a nepoznalo by se to — obojí by vypadalo
    jako doložený fakt o Karlovi."""
    prvni = generate(_full_name("Karel", "Čapek"))[0].predication
    druhy = generate(_full_name("Karel", "Poláček"))[0].predication
    a = prvni.role(ROLE_SUBJECT)
    b = druhy.role(ROLE_SUBJECT)
    assert a is not None and b is not None
    assert a.lemma != b.lemma
    assert {a.lemma, b.lemma} == {"Karel_Čapek", "Karel_Poláček"}


def test_the_name_parts_are_absorbed_not_dropped() -> None:
    """Díly jména jsou v LEMMATU uzlu, takže hlásit je jako zahozené by
    byla nepravda vedle vlastního čtení — táž třída jako W‑20."""
    from core_semantics.cascade import dropped_tokens

    reading = _full_name("Josef", "Hora")
    predication = generate(reading)[0].predication
    assert dropped_tokens(reading, predication) == ()


def test_the_order_of_name_parts_follows_the_text() -> None:
    """„Josef Hora" a „Hora Josef" nejsou totéž a identifikátor uzlu se
    tím řídit musí."""
    from core_semantics.cascade import name_parts_of

    reading = _full_name("Josef", "Hora")
    parts = name_parts_of(reading.tokens[0], reading)
    assert [t.form for t in parts] == ["Hora"]


def test_a_flat_under_a_common_noun_is_not_a_name() -> None:
    """Stráž zůstává úzká: `flat` pod obecným jménem není jméno, ale
    seznam, a to je jiná operace."""
    from core_semantics.cascade import name_parts_of

    seznam = Reading(
        tokens=(
            _token(1, "město", "město", "NOUN", 3, "nsubj", Case="Nom", Number="Sing", Gender="Neut"),
            _token(2, "Praha", "Praha", "PROPN", 1, "flat", Case="Nom", Number="Sing", Gender="Fem"),
            _token(3, "leží", "ležet", "VERB", 0, "root", Number="Sing"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    assert name_parts_of(seznam.tokens[0], seznam) == ()


def test_an_apposition_is_not_a_name_part() -> None:
    """B‑22. „Karel Čapek, rodným jménem Karel Antonín Čapek…" vyrobilo
    uzel `Karel_Čapek_Karel` — JMÉNO, KTERÉ V TEXTU NIKDO NENESE. Je to
    táž rodina jako B‑21, jen z druhé strany: tam se dva lidé slili
    v jednoho, tady se jeden rozdělil na uzel, se kterým se jeho vlastní
    jméno nepotká."""
    from core_semantics.cascade import name_parts_of

    apozice = Reading(
        tokens=(
            _token(1, "Karel", "Karel", "PROPN", 6, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, "Čapek", "Čapek", "PROPN", 1, "flat", Case="Nom", Number="Sing", Gender="Masc"),
            _token(3, "Karel", "Karel", "PROPN", 1, "appos", Case="Nom", Number="Sing", Gender="Masc"),
            _token(4, "Antonín", "Antonín", "PROPN", 3, "flat", Case="Nom", Number="Sing", Gender="Masc"),
            _token(5, "Čapek", "Čapek", "PROPN", 3, "flat", Case="Nom", Number="Sing", Gender="Masc"),
            _token(6, "spisovatel", "spisovatel", "NOUN", 0, "root", Case="Nom", Number="Sing", Gender="Masc"),
            _token(7, ".", ".", "PUNCT", 6, "punct"),
        ),
        provenance="test",
    )
    parts = name_parts_of(apozice.tokens[0], apozice)
    assert [t.form for t in parts] == ["Čapek"], "apozice není díl jména"

    predication = generate(apozice)[0].predication
    subject = predication.role(ROLE_SUBJECT)
    assert subject is not None
    assert subject.lemma == "Karel_Čapek"


def test_the_name_continuation_is_a_named_constant() -> None:
    """POTŘETÍ TÝŽ TVAR ROZHODNUTÍ, takže pojmenovaná konstanta s důvodem
    U NÍ — jako `PREDICATE_AUXILIARIES` a `SUBJECT_DEPRELS`. Rozhoduje
    VZTAH (`flat` je pokračování jména, `appos` jiná zmínka), ne slovní
    druh členu."""
    from pathlib import Path

    from core_semantics.cascade import NAME_CONTINUATION, name_parts_of

    assert set(NAME_CONTINUATION) == {"flat"}
    zdroj = Path(name_parts_of.__globals__["__file__"]).read_text(encoding="utf-8")
    misto = zdroj.index("NAME_CONTINUATION = ")
    okoli = zdroj[max(0, misto - 1600) : misto]
    assert "B‑22" in okoli
    assert "same_as" in okoli, "proč z toho není same_as, má být zapsané"


def test_the_apposition_could_be_identity_but_is_not_guessed() -> None:
    """PROČ Z TOHO NENÍ `same_as`. Nabízí se — „Karel Čapek" a „Karel
    Antonín Čapek" je týž člověk a jádro `same_as` umí. Jenže `appos`
    mezi dvěma `PROPN` neznamená vždy totéž („Karel Čapek, spisovatel"
    je role), a rozbor ty případy nerozlišuje. Ztotožnit uzly z tvaru by
    byl TICHÝ DEFAULT U IDENTITY, tedy nejdražší chyba tohohle systému
    (M‑2, I‑13)."""
    from core_semantics.ast import Atom, P_SAME_AS
    from core_semantics.lexicon import czech_seed
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session

    apozice = Reading(
        tokens=(
            _token(1, "Karel", "Karel", "PROPN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Masc"),
            _token(2, "Čapek", "Čapek", "PROPN", 1, "flat", Case="Nom", Number="Sing", Gender="Masc"),
            _token(3, "spisovatel", "spisovatel", "NOUN", 1, "appos", Case="Nom", Number="Sing", Gender="Masc"),
            _token(4, "zemřel", "zemřít", "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )
    text = "Karel Čapek, spisovatel, zemřel."

    class _Rec:
        provenance = "test"

        def parse(self, _: str) -> Utterance:
            return Utterance(text=text, readings=(apozice,))

    session = Session(lexicon=czech_seed())
    session.utter(text, _Rec())
    assert not any(
        isinstance(statement.formula, Atom)
        and statement.formula.predicate == P_SAME_AS
        for statement in session.kb.active()
    ), "identita se z apozice NEDOSAZUJE"


# --------------------------------------------------------------------------
# Jméno pod titulem — W‑53
# --------------------------------------------------------------------------
#
# „Nad hrobem promluvil básník Josef Hora." se četla jako
# `promluvit(kdo:∀básník)` — O VŠECH BÁSNÍCÍCH. Jméno nespadlo jen tak:
# spadlo a NA JEHO MÍSTĚ ZŮSTAL KVANTIFIKÁTOR, který tam nepatří. Táž
# rodina jako W‑48 — fakt o někom jiném, než o kom věta mluví.


def _titled(title: str, first: str, second: str, deprel: str = "flat") -> Reading:
    return Reading(
        tokens=(
            _token(1, title, title, "NOUN", 4, "nsubj", Case="Nom", Number="Sing", Gender="Masc", Animacy="Anim"),
            _token(2, first, first, "PROPN", 1, deprel, Case="Nom", Number="Sing", Gender="Masc"),
            _token(3, second, second, "PROPN", 1, deprel, Case="Nom", Number="Sing", Gender="Masc"),
            _token(4, "promluvil", "promluvit", "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )


def test_the_person_is_the_node_not_the_title() -> None:
    """Hlavou je JMÉNO. Věta mluví o jednom člověku, ne o všech básnících."""
    reading = _titled("básník", "Josef", "Hora")
    subject = generate(reading)[0].predication.role(ROLE_SUBJECT)
    assert subject is not None
    assert subject.lemma == "Josef_Hora"


def test_the_title_does_not_become_a_class() -> None:
    """`básník_Josef_Hora` by byla třída, která není ani básník, ani
    Hora — přesně jako `město_Praha`."""
    reading = _titled("básník", "Josef", "Hora")
    subject = generate(reading)[0].predication.role(ROLE_SUBJECT)
    assert subject is not None
    assert "básník" not in subject.lemma


def test_a_modifier_name_is_left_alone() -> None:
    """PROTIPŘÍKLAD, a rozbor ho rozlišuje sám: „Město **Praha**" má
    jméno jako `nmod`, ne `flat`. `flat` znamená JEDNU ZMÍNKU (titul
    a jméno míří na jednoho člověka), `nmod` je samostatný přívlastek —
    takže „Město Praha" se tímhle nemění a nemusí se hlídat zvlášť."""
    from core_semantics.cascade import titled_name_of

    reading = _titled("město", "Praha", "Praha", deprel="nmod")
    assert titled_name_of(reading.tokens[0], reading) == ()


def test_the_title_is_absorbed_not_dropped() -> None:
    """Titul se do lemmatu neskládá, ale ani nemizí: je v `form`, takže
    je v přepisu vidět, o čí titul šlo, a nehlásí se jako ztracený."""
    from core_semantics.cascade import dropped_tokens

    reading = _titled("básník", "Josef", "Hora")
    predication = generate(reading)[0].predication
    assert dropped_tokens(reading, predication) == ()
    subject = predication.role(ROLE_SUBJECT)
    assert subject is not None
    assert "básník" in subject.form


def test_the_quantifier_moves_with_the_identity() -> None:
    """DRUHÁ PŮLKA OPRAVY, a bez ní by ta první jen předstírala, že se
    stalo dost: jméno by bylo v uzlu, ale kdyby ze zmínky zůstal `upos`
    hlavy (`NOUN`), vyšlo by `∀Josef_Hora` — tvrzení o VŠECH, kdo se tak
    jmenují. Vada by se z „všichni básníci" přesunula na „všichni Horové"
    a nikdo by si toho nevšiml, protože uzel by se jmenoval správně.

    Jde to celou cestou přes `.utter(`, ne přes `generate`: hlásí se tím
    stav BÁZE, a to je jediné místo, kde je vidět, že se ta věta nezapsala
    o všech.
    """
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session
    from core_semantics.ast import QueryStatus

    veta = _titled("básník", "Josef", "Hora")
    otazka = Reading(
        tokens=(
            _token(1, "Promluvil", "promluvit", "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(2, "básník", "básník", "NOUN", 1, "nsubj", Case="Nom", Number="Sing", Gender="Masc", Animacy="Anim"),
            _token(3, "?", "?", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )

    o_nem = Reading(
        tokens=(
            _token(1, "Promluvil", "promluvit", "VERB", 0, "root", Number="Sing", Gender="Masc"),
            _token(2, "Josef", "Josef", "PROPN", 1, "nsubj", Case="Nom", Number="Sing", Gender="Masc", Animacy="Anim"),
            _token(3, "Hora", "Hora", "PROPN", 2, "flat", Case="Nom", Number="Sing", Gender="Masc", Animacy="Anim"),
            _token(4, "?", "?", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    nahrano = {
        "Nad hrobem promluvil básník Josef Hora.": veta,
        "Promluvil básník?": otazka,
        "Promluvil Josef Hora?": o_nem,
    }

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(text=text, readings=(nahrano[text],))

    # Tvar `PROPN/Sing/Nom/nsubj` je POTVRZENÝ ČLOVĚKEM, ne v seedu:
    # bez něj by se systém právem ptal na kvantifikátor a věta by se
    # nezapsala — a test by pak měřil to doptání, ne opravu.
    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="PROPN", number="Sing", case="Nom", deprel="nsubj"
            ),
            operation=Operation.SELF,
            learned_from="test W‑53",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    session.utter("Nad hrobem promluvil básník Josef Hora.", _Recorded())
    # Obě půlky v jednom testu ZÁMĚRNĚ: samotné `U` na druhé otázce by
    # prošlo i tehdy, kdyby se věta nezapsala vůbec.
    assert session.utter("Promluvil Josef Hora?", _Recorded()).status is (
        QueryStatus.PROVEN_TRUE
    ), "o tom člověku se to řeklo, takže se to o něm musí vědět"
    assert session.utter("Promluvil básník?", _Recorded()).status is (
        QueryStatus.UNKNOWN
    ), "věta o jednom člověku nesmí doložit tvrzení o všech básnících"


def test_a_plural_title_is_not_one_person() -> None:
    """„bratří **Čapků**" má touž stavbu, ale nejsou to jedni bratři
    jménem Čapka — je to SKUPINA dvou lidí, kteří to příjmení nesou.
    Uzel `·Čapka` by byl člověk, který neexistuje: vada vyměněná za
    jinou. Skupinu z téhle stavby systém dnes vyrobit neumí, a než ji
    vyrobí špatně, je lepší, aby ji nevyráběl (W‑54).

    NALEZENO MĚŘENÍM, ne opatrností: v korpusu jsou to 3 zmínky ze 74
    a všechny tři jsou „bratří Čapků“."""
    from core_semantics.cascade import titled_name_of

    hlava = _token(
        1, "bratří", "bratr", "NOUN", 3, "nsubj",
        Case="Nom", Number="Plur", Gender="Masc", Animacy="Anim",
    )
    reading = Reading(
        tokens=(
            hlava,
            _token(2, "Čapků", "Čapka", "PROPN", 1, "flat", Case="Gen", Number="Plur", Gender="Masc"),
            _token(3, "patřili", "patřit", "VERB", 0, "root", Number="Plur", Gender="Masc"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    assert titled_name_of(hlava, reading) == ()


def test_an_ambiguous_number_still_counts_as_singular() -> None:
    """W‑32 znovu, a je to důvod, proč se rys čte PRŮNIKEM: UD píše
    homonymní tvar výčtem (`Number=Plur,Sing`). Kdyby se porovnávala
    rovnost, spadla by pod stráž každá věta s víceznačným tvarem — a to
    je v češtině běžné, ne okrajové."""
    from core_semantics.cascade import titled_name_of

    hlava = _token(
        1, "matka", "matka", "NOUN", 3, "nsubj", Case="Nom", Number="Plur,Sing", Gender="Fem",
    )
    reading = Reading(
        tokens=(
            hlava,
            _token(2, "Božena", "Božena", "PROPN", 1, "flat", Case="Nom", Number="Sing", Gender="Fem"),
            _token(3, "sbírala", "sbírat", "VERB", 0, "root", Number="Sing", Gender="Fem"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    assert [t.form for t in titled_name_of(hlava, reading)] == ["Božena"]


# --------------------------------------------------------------------------
# ZEĎ JMEN ROLÍ — dvě DOLOŽENÉ MEZE, ne zamýšlené *(kolo #96)*
# --------------------------------------------------------------------------
#
# Obojí je NÁLEZ Z MĚŘENÍ, ne oprava: rozhodnutí, co se s tím udělá,
# patří dalšímu kolu. Testy tu jsou proto, aby ta mez byla DOLOŽENÁ —
# a aby se dalo poznat, kdy přestane platit.


def test_a_composed_head_keeps_its_genitive_attribute() -> None:
    """PŘEHLÉDNUTÝ PŘÍVLASTEK — bylo to 13 z 22 výskytů tvaru `Gen`.

    `genitive_attributes` pároval hlavu SHODOU LEMMAT, jenže zmínka ve
    čtení je SLOŽENÁ: „prvním předsedou **odboru**" má v rozboru hlavu
    `předseda`, ale ve čtení leží `první_předseda`. Shoda selhala a
    genitiv skončil jako ROLE PREDIKACE, na kterou se systém ptal „co
    znamená".

    **Bylo to posedmé táž rodina** (W‑32, W‑47, W‑48, B‑18, B‑22, W‑53):
    kategorie porovnaná přesnou shodou tam, kde hodnotu skládá někdo
    jiný. Stabilní identita je `token_index`, ne lemma.

    A přívlastek visí na LEMMATU ZMÍNKY (`první_předseda`), ne na lemmatu
    tokenu: má být o tom uzlu, o kterém věta mluví.
    """
    from core_semantics.cascade import genitive_attributes

    reading = Reading(
        tokens=(
            _token(1, "Byl", "být", "AUX", 3, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "prvním", "první", "ADJ", 3, "amod", Case="Ins", Gender="Masc", Number="Sing"),
            _token(3, "předsedou", "předseda", "NOUN", 0, "root", Animacy="Anim", Case="Ins", Gender="Masc", Number="Sing"),
            _token(4, "odboru", "odbor", "NOUN", 3, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    predication = generate(reading)[0].predication
    assert "první_předseda" in {r.mention.lemma for r in predication.roles}
    assert genitive_attributes(reading, predication) == (
        ("první_předseda", "odbor", 4, "", 3),
    )


def test_no_mention_is_in_the_reading_twice() -> None:
    """COUNTEREXAMPLE REVIEWERA JAKO VLASTNOST *(W‑58)*: žádná zmínka
    nesmí být ve čtení DVAKRÁT POD DVĚMA JMÉNY.

    „byl prvním předsedou odboru" dávalo `co:první_předseda` (složená
    zmínka) i `kdo:předseda` (holé lemma) — TÝŽ TOKEN, dvě jména, dvě
    různá lemmata. Příčina: pro‑drop bral jako zmínku KOŘEN, jenže
    u spony je kořenem JMENNÁ ČÁST, která už ve čtení leží.

    Porovnává se `token_index`, ne lemma: lemma se skládá jinde, takže
    dvě jména téhož tokenu by se lišila a shoda by je neodhalila.
    """
    reading = Reading(
        tokens=(
            _token(1, "Byl", "být", "AUX", 3, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "prvním", "první", "ADJ", 3, "amod", Case="Ins", Gender="Masc", Number="Sing"),
            _token(3, "předsedou", "předseda", "NOUN", 0, "root", Animacy="Anim", Case="Ins", Gender="Masc", Number="Sing"),
            _token(4, "odboru", "odbor", "NOUN", 3, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    verdict = cascade(
        reading, tiers=(*HARD_TIERS, prodrop_tier(), attribute_tier())
    )
    for candidate in verdict.survivors:
        indexy = [r.mention.token_index for r in candidate.predication.roles]
        assert len(indexy) == len(set(indexy)), (
            f"týž token pod dvěma jmény: {candidate.predication}"
        )


def test_a_genitive_is_either_an_attribute_or_a_role() -> None:
    """Druhá půlka téhož *(W‑58)*. U SLOVESNÉ věty je genitiv VNUK kořene
    („chov **zvířat** je náročný") a rolí se nestane. U SPONY je jmenná
    část kořenem, takže její genitiv je jeho DÍTĚ a rolí se stane —
    ačkoli je to týž vztah dvou jmen uvnitř fráze. Stavba se liší,
    zacházení se lišit nesmí."""
    reading = Reading(
        tokens=(
            _token(1, "Byl", "být", "AUX", 3, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "prvním", "první", "ADJ", 3, "amod", Case="Ins", Gender="Masc", Number="Sing"),
            _token(3, "předsedou", "předseda", "NOUN", 0, "root", Animacy="Anim", Case="Ins", Gender="Masc", Number="Sing"),
            _token(4, "odboru", "odbor", "NOUN", 3, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    verdict = cascade(reading, tiers=(*HARD_TIERS, attribute_tier()))
    predication = verdict.survivors[0].predication
    assert predication.pending_attribute == (("první_předseda", "odbor", 4, "", 3),)
    assert 4 not in {r.mention.token_index for r in predication.roles}
    assert "Gen" not in surface_roles(predication)


def test_a_pending_kernel_relation_keeps_its_genitive() -> None:
    """PROTIPŘÍKLAD, bez kterého by ta oprava rozbila `contains`.

    „Petrovice jsou součástí **Plzně**." má stavbu IDENTICKOU s „byl
    prvním předsedou **odboru**" — u spony je jmenná část kořenem
    a genitiv jejím dítětem. Rozlišit je ze STROMU nejde; rozlišuje je
    STAV, který nastavilo patro jádrové relace: tady čeká odpověď `→⊆`
    a ten genitiv je JEDNA JEJÍ STRANA. Vzít mu ho znamená, že odpověď
    nemá s čím pracovat."""
    from core_semantics.cascade import genitive_attributes
    from dataclasses import replace as _replace

    reading = Reading(
        tokens=(
            _token(1, "Petrovice", "Petrovice", "PROPN", 3, "nsubj", Case="Nom", Number="Plur"),
            _token(2, "jsou", "být", "AUX", 3, "cop", Number="Plur", Polarity="Pos"),
            _token(3, "součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
            _token(4, "Plzně", "Plzeň", "PROPN", 3, "nmod", Case="Gen", Gender="Fem", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    predication = generate(reading)[0].predication
    assert genitive_attributes(reading, predication), (
        "bez čekající relace je to normální přívlastek"
    )
    ceka = _replace(predication, pending_relation="cop:součást+Gen")
    assert genitive_attributes(reading, ceka) == (), (
        "s čekající relací si ten genitiv nárokuje ona"
    )


def test_a_passive_subject_is_still_asked_about() -> None:
    """TRPNÝ PODMĚT MEZI OKOLNOSTMI — 19 výskytů, třetí nejčastější tvar.

    Vlastní jméno dostává ZÁMĚRNĚ (I‑2, INV‑11): trpný podmět není
    konatel a ztotožnit ho s `kdo` by byl dohad. Otázka „co ta role
    znamená" se ale ptá na něco, co rozbor ŘÍKÁ — v trpném rodě je
    podmět PATIENS. Změřeno: 18 z 19 vět nemá roli `co`, takže by
    nekolidovala.
    """
    reading = Reading(
        tokens=(
            _token(1, "Úmysly", "úmysl", "NOUN", 3, "nsubj:pass", Case="Nom", Gender="Masc", Number="Plur"),
            _token(2, "byly", "být", "AUX", 3, "aux:pass", Number="Plur", Polarity="Pos"),
            _token(3, "popsány", "popsaný", "ADJ", 0, "root", Number="Plur", Polarity="Pos", Voice="Pass"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    predication = generate(reading)[0].predication
    assert "nsubj:pass" in surface_roles(predication)
    assert "co" not in {r.name for r in predication.roles}


def test_a_prepositional_genitive_is_not_an_attribute() -> None:
    """„Další synonyma **vesmíru** u starověkých **filozofů**" *(W‑58)*.

    První genitiv je přívlastek, druhý je PŘEDLOŽKOVÁ FRÁZE — „synonyma
    filozofů" ta věta netvrdí. Rozdíl je v rozboru: u předložkové fráze
    visí dítě s `deprel=case`. Nálezeno DIFFEM KORPUSU po opravě W‑58,
    ne úvahou: dokud se přívlastek přehlížel kvůli shodě lemmat, tahle
    přeexponovaná stráž se nikdy neuplatnila.
    """
    from core_semantics.cascade import genitive_attributes

    reading = Reading(
        tokens=(
            _token(1, "Synonyma", "synonymum", "NOUN", 5, "nsubj", Case="Nom", Number="Plur"),
            _token(2, "vesmíru", "vesmír", "NOUN", 1, "nmod", Case="Gen", Number="Sing"),
            _token(3, "u", "u", "ADP", 4, "case", Case="Gen"),
            _token(4, "filozofů", "filozof", "NOUN", 1, "nmod", Case="Gen", Number="Plur"),
            _token(5, "byla", "být", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(6, ".", ".", "PUNCT", 5, "punct"),
        ),
        provenance="test",
    )
    predication = generate(reading)[0].predication
    from core_semantics.cascade import attribute_label

    najdene = genitive_attributes(reading, predication)
    # PO W‑84 JE PŘÍVLASTEK I TEN PŘEDLOŽKOVÝ — ale to, co tenhle test
    # hlídal, DRŽÍ DÁL: nepravda byla „synonyma filozofů“ se zahozenou
    # předložkou, a ta se nesmí objevit ani teď.
    assert [(g, tvar) for _, g, _, tvar, _ in najdene] == [
        ("vesmír", ""),
        ("filozof", "nmod:u+Gen"),
    ], "holý genitiv i předložkový jsou vztah vedle věty, každý svým tvarem"
    popisy = [attribute_label(h, g, tvar) for h, g, _, tvar, _ in najdene]
    assert popisy == ["synonymum vesmír", "synonymum u filozof"], (
        "„synonyma filozofů“ bez předložky je o té větě nepravda a "
        "nesmí vzniknout ani jako popis"
    )
    assert all("+" not in p for p in popisy), (
        "popis je věta, ne tvar — tvar se do něj nesmí propsat"
    )


def test_a_prepositional_genitive_does_not_hide_the_construction() -> None:
    """TÁŽ PODMÍNKA NA DRUHÉM MÍSTĚ, a proto je to jedna funkce.

    „**Podle** některých teorií je vesmír součástí **systému**." má dva
    genitivy, ale jen jeden HOLÝ. Konstrukce „X je součástí Y" počítá,
    kolik jich věta má — a když se do počtu vzala i předložková fráze,
    věta o konstrukci přišla jen proto, že nesla okolnost navíc. Cesta
    ke `contains` tím byla zavřená a nikdo to nevěděl.
    """
    from core_semantics.cascade import relation_shape

    reading = Reading(
        tokens=(
            _token(1, "Podle", "podle", "ADP", 2, "case", Case="Gen"),
            _token(2, "teorií", "teorie", "NOUN", 5, "obl", Case="Gen", Number="Plur"),
            _token(3, "vesmír", "vesmír", "NOUN", 5, "nsubj", Case="Nom", Number="Sing"),
            _token(4, "je", "být", "AUX", 5, "cop", Number="Sing", Polarity="Pos"),
            _token(5, "součástí", "součást", "NOUN", 0, "root", Case="Ins", Gender="Fem", Number="Sing"),
            _token(6, "systému", "systém", "NOUN", 5, "nmod", Case="Gen", Number="Sing"),
            _token(7, ".", ".", "PUNCT", 5, "punct"),
        ),
        provenance="test",
    )
    predication = generate(reading)[0].predication
    found = relation_shape(predication, reading)
    assert found is not None and found.shape == "cop:součást+Gen"


# --------------------------------------------------------------------------
# TRPNÝ PODMĚT je PATIENS *(W‑59)*
# --------------------------------------------------------------------------


def _passive(*, with_object: bool = False) -> Reading:
    tokens = [
        _token(1, "Úmysly", "úmysl", "NOUN", 3, "nsubj:pass", Case="Nom", Gender="Masc", Number="Plur"),
        _token(2, "byly", "být", "AUX", 3, "aux:pass", Number="Plur", Polarity="Pos"),
        _token(3, "popsány", "popsaný", "ADJ", 0, "root", Number="Plur", Polarity="Pos", Voice="Pass"),
    ]
    if with_object:
        tokens.append(
            _token(4, "změnu", "změna", "NOUN", 3, "obj", Case="Acc", Gender="Fem", Number="Sing")
        )
    tokens.append(_token(len(tokens) + 1, ".", ".", "PUNCT", 3, "punct"))
    return Reading(tokens=tuple(tokens), provenance="test")


def test_a_passive_subject_is_the_patient() -> None:
    """„Úmysly byly popsány." — úmysly nic nepopisují, jsou to ty
    POPISOVANÉ. Bylo to TŘETÍ NEJČASTĚJŠÍ „co znamená role X" v korpusu
    (19 z 250) a přitom to nikdy nebyla otázka o významu."""
    from core_semantics.cascade import passive_tier

    verdict = cascade(_passive(), tiers=(*HARD_TIERS, passive_tier()))
    predication = verdict.survivors[0].predication
    assert {r.name for r in predication.roles} == {ROLE_OBJECT}
    assert "nsubj:pass" not in surface_roles(predication)


def test_the_passive_role_comes_from_the_subtype_not_from_learning() -> None:
    """V HLÁŠENÍ MUSÍ BÝT VIDĚT, ODKUD to plyne. Kdyby to vypadalo jako
    naučený vzor, čekal by člověk, že to jde odvolat — a nejde, protože
    `:pass` je vlastnost ROZBORU, ne lexikonu."""
    from core_semantics.cascade import passive_tier

    verdict = cascade(_passive(), tiers=(*HARD_TIERS, passive_tier()))
    stopa = "\n".join(verdict.trace)
    assert "nsubj:pass" in stopa and "PODTYPU" in stopa
    role = verdict.survivors[0].predication.reading(ROLE_OBJECT)
    assert role is not None and "podtyp" in role.source


def test_a_taken_object_makes_the_passive_ask() -> None:
    """JEDINÁ KOLIZE, a je změřená: 18 z 19 vět korpusu roli `co` volnou
    má, u devatenácté („Celá kolekce se označuje mnohovesmír.") jsou obě
    strany VYSLOVENÉ. Dosadit `co` z `:pass` by znamenalo zahodit člen,
    který ve větě stojí — a poznat by to nešlo, protože obě jsou `co`."""
    from core_semantics.cascade import passive_question, passive_tier

    verdict = cascade(
        _passive(with_object=True), tiers=(*HARD_TIERS, passive_tier())
    )
    predication = verdict.survivors[0].predication
    assert {r.name for r in predication.roles} == {ROLE_OBJECT, "nsubj:pass"}
    otazka = passive_question(predication)
    assert otazka is not None and "Která z nich" in otazka
    assert "nsubj:pass" not in surface_roles(predication), (
        "„co znamená nsubj:pass“ systém VÍ — ptát se na to je nepravda "
        "o vlastním stavu (W‑20)"
    )


def test_a_collided_passive_does_not_write() -> None:
    """Zápis se ZASTAVÍ (B‑19): jinak by se věta zapsala s povrchovým
    jménem role a po rozhodnutí podruhé — a ten první výrok by nikdo
    neodvolal."""
    from core_semantics.cascade import AWAITING_ROLE_NAME, passive_tier

    verdict = cascade(
        _passive(with_object=True), tiers=(*HARD_TIERS, passive_tier())
    )
    predication = verdict.survivors[0].predication
    assert any(r.awaiting == AWAITING_ROLE_NAME for r in predication.roles)


def test_a_passive_without_a_subject_still_asks_for_one() -> None:
    """PROTIPŘÍKLAD PROTI REGRESI W‑48. „Byl pohřben na Vyšehradě." nemá
    `nsubj:pass` vůbec — patro trpného rodu nemá co přejmenovat a věta se
    dál ptá, o KOM to platí."""
    from core_semantics.cascade import passive_tier

    reading = Reading(
        tokens=(
            _token(1, "Byl", "být", "AUX", 2, "aux:pass", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "pohřben", "pohřbený", "ADJ", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos", Voice="Pass"),
            _token(3, "na", "na", "ADP", 4, "case", Case="Loc"),
            _token(4, "Vyšehradě", "Vyšehrad", "PROPN", 2, "obl", Case="Loc", Gender="Masc", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    verdict = cascade(
        reading, tiers=(*HARD_TIERS, passive_tier(), prodrop_tier())
    )
    predication = verdict.survivors[0].predication
    # ROLE SE OD W‑79 JMENUJE `co`, ne `kdo`: trpný podmět je PATIENS,
    # ať ho text vysloví, nebo ne. Mění se JMÉNO role, ne to, že se na ni
    # systém ptá — dvě jména pro touž roli rozpadala bázi na dvě poloviny.
    assert predication.role(ROLE_OBJECT) is not None
    assert predication.role(ROLE_SUBJECT) is None
    assert "BEZ PODMĚTU" in "\n".join(verdict.trace)


def test_a_passive_sentence_goes_all_the_way_into_the_base() -> None:
    """CELOU CESTOU PŘES `.utter(`, ne přes patro *(W‑59)*. Bez toho by
    doložka měla vynucení jen nad vnitřní funkcí a nikdo by neověřil, že
    se ta role dostane až do BÁZE — tam, kde na ní stojí odpověď."""
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session, answers_here
    from core_semantics.ast import QueryStatus

    veta = _passive()
    otazka = Reading(
        tokens=(
            _token(1, "Byly", "být", "AUX", 3, "aux:pass", Number="Plur", Polarity="Pos"),
            _token(2, "úmysly", "úmysl", "NOUN", 3, "nsubj:pass", Case="Nom", Gender="Masc", Number="Plur"),
            _token(3, "popsány", "popsaný", "ADJ", 0, "root", Number="Plur", Polarity="Pos", Voice="Pass"),
            _token(4, "?", "?", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(
                text=text, readings=(otazka if text.endswith("?") else veta,)
            )

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="NOUN", number="Plur", case="Nom", deprel="nsubj:pass"
            ),
            operation=Operation.FOR_ALL,
            learned_from="test W‑59",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    precteno = session.utter("Úmysly byly popsány.", _Recorded())
    # `∀` ZE SEEDU ZÁPIS NELICENCUJE *(W‑103)*, takže dialog je o tah
    # delší: člověk potvrdí právě to, co dosud osivo HÁDALO. Zkouška se
    # tím nezeslabuje — tvrdí se v ní totéž, jen se k tomu dojde
    # odpovědí místo domněnky.
    assert precteno.predication is not None
    zapsano = session.play(
        answers_here("O každém.", precteno.predication, "co", Operation.FOR_ALL)
    )
    assert zapsano.statement_id is not None
    assert session.utter("Byly úmysly popsány?", _Recorded()).status is (
        QueryStatus.PROVEN_TRUE
    ), "role z `:pass` musí dojít až do báze, jinak se na ni nedá odpovědět"


# --------------------------------------------------------------------------
# SIGNÁL Z ROZBORU dělí tvar, neurčuje jméno role *(W‑61)*
# --------------------------------------------------------------------------


def _in_place(filler: str, lemma: str, *, geo: bool, year: bool) -> Reading:
    tokens = [
        _token(1, "Petr", "Petr", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
        _token(2, "byl", "být", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
        _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
    ]
    tokens[1] = _token(2, "byl", "být", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos")
    feats = {"Case": "Loc", "Number": "Sing"}
    if geo:
        feats["NameType"] = "Geo"
    tokens.append(_token(4, filler, lemma, "PROPN" if geo else "NOUN", 2, "obl", **feats))
    if year:
        tokens.append(_token(5, "1935", "1935", "NUM", 4, "nummod", NumForm="Digit", NumType="Card"))
    tokens[2] = _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc")
    return Reading(tokens=tuple(tokens), provenance="test")


def test_a_geographic_filler_splits_the_shape() -> None:
    """`NameType=Geo` dává PARSER, ne seznam slov — nemá se kde rozejít
    s korpusem."""
    from core_semantics.cascade import surface_role

    reading = _in_place("Praze", "Praha", geo=True, year=False)
    assert surface_role(reading.tokens[3], reading) == "v+Loc/Geo"


def test_a_year_under_the_filler_splits_the_shape() -> None:
    """Letopočet je STAVBA (`NumType=Card`, čtyři číslice jako dítě), ne
    lemma `rok` — to by byl seznam slov."""
    from core_semantics.cascade import surface_role

    reading = _in_place("roce", "rok", geo=False, year=True)
    assert surface_role(reading.tokens[3], reading) == "v+Loc/rok"


def test_without_a_signal_the_shape_stays_bare() -> None:
    """26 ze 42 výskytů `v+Loc` signál NEMÁ — „v bytě", „v tomto smyslu",
    „v angličtině". **Je to správná odpověď, ne mez k dohnání**:
    rozhodnout je z tvaru by šlo jen seznamem slov."""
    from core_semantics.cascade import surface_role

    reading = _in_place("smyslu", "smysl", geo=False, year=False)
    assert surface_role(reading.tokens[3], reading) == "v+Loc"


def test_place_and_time_no_longer_collide_under_one_shape() -> None:
    """CO TO KOUPILO: „Petr byl v roce 1935 v Praze." má DVĚ okolnosti
    s TOUŽ předložkou a pádem. Dokud byl tvar jeden, dostaly by totéž
    jméno role — a čtení s duplicitou se nesmí vyrobit, takže věta byla
    NEČITELNÁ."""
    reading = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing"),
            _token(2, "byl", "být", "AUX", 4, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            _token(4, "roce", "rok", "NOUN", 0, "root", Case="Loc", Gender="Masc", Number="Sing"),
            _token(5, "1935", "1935", "NUM", 4, "nummod", NumForm="Digit", NumType="Card"),
            _token(6, "v", "v", "ADP", 7, "case", AdpType="Prep", Case="Loc"),
            _token(7, "Praze", "Praha", "PROPN", 4, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
            _token(8, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )
    jmena = {r.name for r in generate(reading)[0].predication.roles}
    assert "v+Loc/Geo" in jmena and "v+Loc/rok" in jmena


def test_the_signal_does_not_name_the_role() -> None:
    """SIGNÁL NEURČUJE JMÉNO a určovat ho nesmí: že „v Praze" je `kde`
    a „do Prahy" `kam`, plyne z PŘEDLOŽKY A PÁDU, ne z toho, že je Praha
    místo. Bez naučeného mapování zůstane tvar povrchový."""
    reading = _in_place("Praze", "Praha", geo=True, year=False)
    predication = generate(reading)[0].predication
    assert "v+Loc/Geo" in surface_roles(predication)
    assert "kde" not in {r.name for r in predication.roles}


def test_the_question_says_where_the_signal_came_from() -> None:
    """Tvar `v+Loc/Geo` sám o sobě vypadá jako vymyšlená kategorie. Věta
    pod ním musí říct, že to četl PARSER — a že za jinou odpovědí
    u „v roce 1935" není nedůslednost, ale JINÝ TVAR."""
    reading = _in_place("roce", "rok", geo=False, year=True)
    otazka = role_question(generate(reading)[0].predication)
    assert otazka is not None
    assert "SIGNÁL Z ROZBORU" in otazka and "letopočet" in otazka


def test_a_year_does_not_inherit_the_bare_mapping() -> None:
    """NEJDŮLEŽITĚJŠÍ PŮLKA. V seedu je `po+Loc → kudy` a dokud byl tvar
    jeden, platilo to i pro „Po roce 1990 byly nahrávky digitalizovány."
    — v korpusu z toho vyšlo `digitalizovaný(kudy:rok)`, tedy CESTA
    MÍSTO ČASU. Signálovaný tvar obecný NEDĚDÍ, takže se systém zeptá."""
    lexicon = czech_seed()
    assert lexicon.role_candidates("po+Loc"), "seed „po+Loc → kudy“ tu být má"
    assert not lexicon.role_candidates("po+Loc/rok"), (
        "kdyby se dědilo, vrátila by se vada „kudy:rok“"
    )


def test_the_split_shape_reaches_the_base() -> None:
    """CELOU CESTOU PŘES `.utter(` *(W‑61)*. Bez toho by doložka měla
    vynucení jen nad `surface_role` a nikdo by neověřil, že se rozdělený
    tvar dostane až tam, kde na něm stojí odpověď — a že týž tvar ve
    větě i v dotazu míří na týž výrok."""
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session
    from core_semantics.ast import QueryStatus
    from core_semantics.lexicon import RoleMapping

    veta = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing"),
            _token(2, "byl", "být", "AUX", 4, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            _token(4, "Praze", "Praha", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )
    otazka = Reading(
        tokens=(
            _token(1, "Byl", "být", "AUX", 4, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "Petr", "Petr", "PROPN", 4, "nsubj", Case="Nom", Number="Sing"),
            _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            _token(4, "Praze", "Praha", "PROPN", 0, "root", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
            _token(5, "?", "?", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(
                text=text, readings=(otazka if text.endswith("?") else veta,)
            )

    lexicon = czech_seed()
    lexicon.add_role(
        RoleMapping(
            surface="v+Loc/Geo",
            canonical="kde",
            learned_from="test W‑61",
            status=PatternStatus.CONFIRMED,
        )
    )
    for case, deprel in (("Nom", "nsubj"), ("Loc", "root")):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos="PROPN", number="Sing", case=case, deprel=deprel
                ),
                operation=Operation.SELF,
                learned_from="test W‑61",
                status=PatternStatus.CONFIRMED,
            )
        )
    session = Session(lexicon=lexicon)
    assert session.utter("Petr byl v Praze.", _Recorded()).statement_id is not None
    assert session.utter("Byl Petr v Praze?", _Recorded()).status is (
        QueryStatus.PROVEN_TRUE
    )


# --------------------------------------------------------------------------
# JEDNA PODMÍNKA, JEDNA ODPOVĚĎ *(W‑62)*
# --------------------------------------------------------------------------


def _lives_in_prague() -> Reading:
    return Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
            _token(2, "bydlí", "bydlet", "VERB", 0, "root", Number="Sing", Person="3", Polarity="Pos"),
            _token(3, "v", "v", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            _token(4, "Praze", "Praha", "PROPN", 2, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )


def test_a_learned_role_name_is_not_asked_about_again() -> None:
    """NAUČENÉ JMÉNO NENÍ TVAR *(W‑62)*. „proč" mezi kanonické role jádra
    nepatří a patřit nemusí — okolnosti jsou povrchové (§ 12/1) — ale
    NĚKDO HO UŽ POJMENOVAL. Systém se na `proč` ptal a přitom to jméno
    sám dostal jako odpověď o krok dřív.

    Rozhoduje značka `shaped`, ne podoba řetězce: hádat z toho, že jméno
    obsahuje `+` nebo `/`, je heuristika nad textem a rozejde se, jakmile
    někdo pojmenuje roli tak, že se to trefí."""
    from core_semantics.cascade import Mention, RoleReading

    naucena = Predication(
        predicate="odjet",
        roles=(
            RoleReading("proč", Mention(lemma="pršet", form="pršelo", token_index=4, upos="VERB")),
        ),
    )
    assert surface_roles(naucena) == ()
    assert role_question(naucena) is None


def test_a_shape_named_role_stops_the_write_wherever_it_is() -> None:
    """JEDNA PODMÍNKA, JEDNA ODPOVĚĎ. Zábrana platila jen pro vedlejší
    větu, ačkoli DŮVOD platí pro každou roli, jejíž jméno zůstalo tvarem:
    „Petr bydlí v Praze." se zapsala jako `bydlet(kdo:Petr,
    v+Loc/Geo:Praha)` a po odpovědi `→@` ZNOVU jako `bydlet(kde:Praha,
    kdo:Petr)` — DVA VÝROKY o téže větě a ten první nikdo neodvolal."""
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session, names_role

    veta = _lives_in_prague()

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(text=text, readings=(veta,))

    lexicon = czech_seed()
    for case, deprel in (("Nom", "nsubj"), ("Loc", "obl")):
        lexicon.add(
            LearnedPattern(
                trigger=Trigger(
                    lemma="", upos="PROPN", number="Sing", case=case, deprel=deprel
                ),
                operation=Operation.SELF,
                learned_from="test W‑62",
                status=PatternStatus.CONFIRMED,
            )
        )
    session = Session(lexicon=lexicon)
    session.utter("Petr bydlí v Praze.", _Recorded())
    # OD W‑79 SE VĚTA ZAPÍŠE ČÁSTEČNĚ. To, co tahle zkouška hlídá od
    # W‑62, PLATÍ DÁL A JE PŘÍSNĚJŠÍ: role s tvarem místo jména se do
    # báze nedostane teď, a po doplnění tam neleží DVAKRÁT.
    castecne = [
        str(st.formula)
        for st in session.kb.active()
        if str(st.formula).startswith("bydlet(")
    ]
    assert castecne == ["bydlet(kdo:Petr)"], (
        f"zapíše se jen to, čemu systém rozumí, ale bylo {castecne}"
    )

    session.play(names_role("Je to místo.", veta, "v+Loc/Geo", "kde"))
    zapsane = [
        str(s.formula)
        for s in session.kb.active()
        if str(s.formula).startswith("bydlet(")
    ]
    assert zapsane == ["bydlet(kde:Praha, kdo:Petr)"], (
        "po odpovědi leží v bázi PRÁVĚ JEDEN výrok o té větě"
    )


def test_no_role_named_by_its_form_reaches_the_base() -> None:
    """COUNTEREXAMPLE REVIEWERA JAKO VLASTNOST: na tutéž podmínku dává
    systém tutéž odpověď. Prochází se CELÁ akceptační sada — kdyby se
    kontrolovaly dvě věty, prošlo by pravidlo, které platí jen pro ně."""
    from core_semantics.tests.dialogues import DIALOGUES
    from core_semantics.tests.test_golden_dialogues import play

    for dialogue in DIALOGUES:
        done, _ = play(dialogue)
        for step, result in done:
            if result.statement_id is None or result.predication is None:
                continue
            assert surface_roles(result.predication) == (), (
                f"{dialogue.name} / {step.text!r}: zapsáno s rolí, "
                f"jejíž jméno je tvar — {result.predication}"
            )


# --------------------------------------------------------------------------
# DVA ČLENY, JEDNO JMÉNO *(W‑63)*
# --------------------------------------------------------------------------


def _two_adverbs(second: str) -> Reading:
    """«Interpretace byla ovšem zcela podřízena.» — dvě příslovce."""
    return Reading(
        tokens=(
            _token(1, "interpretace", "interpretace", "NOUN", 5, "nsubj:pass", Case="Nom", Gender="Fem", Number="Sing"),
            _token(2, "byla", "být", "AUX", 5, "aux:pass", Number="Sing", Polarity="Pos"),
            _token(3, "ovšem", "ovšem", "PART", 5, second),
            _token(4, "zcela", "zcela", "ADV", 5, "advmod"),
            _token(5, "podřízena", "podřízený", "ADJ", 0, "root", Gender="Fem", Number="Sing", Polarity="Pos", Voice="Pass"),
            _token(6, ".", ".", "PUNCT", 5, "punct"),
        ),
        provenance="test",
    )


def test_two_members_with_one_name_both_fall_back_to_their_shape() -> None:
    """VĚTA MĚLA VŠECHNO — podmět, okolnost i argument — a nezbylo z ní
    ani jedno čtení, protože „ovšem" (`advmod:emph`) a „zcela"
    (`advmod`) dostaly oba roli `jak`.

    Vybrat jeden z nich by byl tichý default u role, kterou věta
    VYSLOVILA dvakrát. Oba proto padnou zpátky na SVŮJ TVAR — a rozbor
    je rozlišuje, i když jméno role ne."""
    candidates = generate(_two_adverbs("advmod:emph"))
    assert candidates, "věta se čte, ne že se zahodí"
    jmena = {r.name for r in candidates[0].predication.roles}
    assert {"advmod", "advmod:emph"} <= jmena
    assert "jak" not in jmena


def test_the_fallback_asks_and_does_not_write() -> None:
    """Mezistav PTÁ SE je VÝSLEDEK, ne slabina: role má za jméno tvar,
    takže se systém ptá a NEZAPISUJE (W‑62)."""
    predication = generate(_two_adverbs("advmod:emph"))[0].predication
    assert {"advmod", "advmod:emph"} <= set(surface_roles(predication))
    assert role_question(predication) is not None


def test_an_unresolvable_collision_says_so_instead_of_lying() -> None:
    """DVĚ HOLÁ `advmod` nerozliší ani pád zpátky na tvar — „často"
    i „služebně" mají tvar `advmod`. Věta se přečíst nedá, ALE hlásit
    u ní „nemá ani jeden člen, který bych uměl pojmenovat" je NEPRAVDA
    O TEXTU: členy má a umí je pojmenovat, a právě to je ten problém."""
    from core_semantics.cascade import why_nothing

    reading = _two_adverbs("advmod")
    assert generate(reading) == ()
    duvod = why_nothing(reading)
    assert "týž tvar" in duvod and "advmod" in duvod
    assert "ani jeden člen" not in duvod
    assert "„ovšem“" in duvod and "„zcela“" in duvod


def test_a_nominal_phrase_is_not_a_predicate_without_members() -> None:
    """„Úrazy způsobené pády." má jediné dítě `amod` — jenže to je
    PŘÍVLASTEK a `generate` ho SKLÁDÁ DO ZMÍNKY hlavy. Hlásit „neumím ho
    pojmenovat" je nepravda o vlastní práci: roli z něj udělat nejde,
    protože rolí není."""
    from core_semantics.cascade import why_nothing

    reading = Reading(
        tokens=(
            _token(1, "Úrazy", "úraz", "NOUN", 0, "root", Case="Nom", Gender="Masc", Number="Plur"),
            _token(2, "způsobené", "způsobený", "ADJ", 1, "amod", Case="Nom", Number="Plur"),
            _token(3, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert generate(reading) == ()
    duvod = why_nothing(reading)
    assert "JMENNÁ FRÁZE" in duvod
    assert "neumím" not in duvod


def test_a_heading_glued_to_a_sentence_is_named_as_such() -> None:
    """NADPIS SPLYNULÝ S VĚTOU *(W‑64)*. „Obezita: Domácí mazlíčci trpí
    nadváhou." má kořenem NADPIS a skutečná věta pod ním visí jako
    `appos` — se svým podmětem i přísudkem. Říct u ní „nemá ani jeden
    člen, který bych uměl pojmenovat" je NEPRAVDA O TEXTU: členy tam
    jsou, jen ne pod tím kořenem.

    **Číst se to nezačne, a je to rozhodnutí, ne mez.** Přesadit kořen by
    znamenalo rozhodnout, že nadpis do promluvy nepatří — a to je výrok
    o TEXTU, ne o rozboru.
    """
    from core_semantics.cascade import why_nothing

    reading = Reading(
        tokens=(
            _token(1, "Obezita", "obezita", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
            _token(2, ":", ":", "PUNCT", 4, "punct"),
            _token(3, "mazlíčci", "mazlíček", "NOUN", 4, "nsubj", Case="Nom", Gender="Masc", Number="Plur"),
            _token(4, "trpí", "trpět", "VERB", 1, "appos", Number="Plur", Person="3", Polarity="Pos"),
            _token(5, "nadváhou", "nadváha", "NOUN", 4, "obl:arg", Case="Ins", Gender="Fem", Number="Sing"),
            _token(6, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert generate(reading) == (), "kořen se nepřesazuje — to je výrok o textu"
    duvod = why_nothing(reading)
    assert "NADPIS" in duvod and "APOZICE" in duvod
    assert "ani jeden člen" not in duvod
    assert "segmentace" in duvod


def test_a_nominal_apposition_is_not_a_heading() -> None:
    """PROTIPŘÍKLAD, bez kterého by hláška o nadpisu spadla na každou
    apozici: „Karel Čapek, spisovatel, zemřel." má `appos` TAKY, jenže
    JMENNOU — bez vlastního přísudku. Rozlišuje to rozbor, ne dvojtečka
    v textu."""
    from core_semantics.cascade import why_nothing

    reading = Reading(
        tokens=(
            _token(1, "Obezita", "obezita", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
            _token(2, "nemoc", "nemoc", "NOUN", 1, "appos", Case="Nom", Gender="Fem", Number="Sing"),
            _token(3, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert "NADPIS" not in why_nothing(reading)


def test_the_heading_guard_asks_the_one_place_that_knows() -> None:
    """DEVÁTÁ INSTANCE TÉŽE RODINY *(W‑65)*. Stráž nadpisu si napsala
    UŽŠÍ KOPII `_is_predicate` a nesla obě staré vady naráz:
    `upos == "VERB"` minulo TRPNÝ ROD (kořen `ADJ` + `aux:pass`, W‑48)
    a `deprel == "cop"` porovnávalo deprel ŘETĚZCEM (W‑47).

    „Obezita: Zvířata byla vyšetřena veterinářem." je TÁŽ VĚTA, kterou
    W‑64 odstraňovalo, jen s trpnou apozicí — a hlásila zase, že nemá
    ani jeden pojmenovatelný člen."""
    from core_semantics.cascade import why_nothing

    reading = Reading(
        tokens=(
            _token(1, "Obezita", "obezita", "NOUN", 0, "root", Case="Nom", Gender="Fem", Number="Sing"),
            _token(2, ":", ":", "PUNCT", 5, "punct"),
            _token(3, "Zvířata", "zvíře", "NOUN", 5, "nsubj:pass", Case="Nom", Gender="Neut", Number="Plur"),
            _token(4, "byla", "být", "AUX", 5, "aux:pass", Number="Plur", Polarity="Pos"),
            _token(5, "vyšetřena", "vyšetřený", "ADJ", 1, "appos", Number="Plur", Polarity="Pos", Voice="Pass"),
            _token(6, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    duvod = why_nothing(reading)
    assert "NADPIS" in duvod and "ani jeden člen" not in duvod


def test_the_heading_guard_has_no_second_copy() -> None:
    """A ať se ta kopie nevrátí: stráž se ptá `_is_predicate`, ne
    slovního druhu. Kontroluje se ZDROJ, protože chování by prošlo
    i s kopií — dokud by někdo nepřidal třetí tvar přísudku."""
    import inspect

    from core_semantics.cascade import why_nothing

    # KOMENTÁŘE SE ODSTŘIHNOU. Vysvětlení, PROČ ta kopie byla špatně,
    # tu slovo „VERB" nést musí — a test, který by na něj spadl, by
    # trestal právě to, kvůli čemu se ta oprava dá pochopit.
    kod = chr(10).join(
        radek
        for radek in inspect.getsource(why_nothing).splitlines()
        if not radek.lstrip().startswith("#")
    )
    assert "_is_predicate(" in kod
    assert "upos ==" not in kod


# --------------------------------------------------------------------------
# SOUŘADNÝ DRUHÝ PŘÍSUDEK je DRUHÁ VĚTA *(W‑70)*
# --------------------------------------------------------------------------


def _two_clauses() -> Reading:
    """«Stav se zlepšil, ale musel ulehnout.»"""
    return Reading(
        tokens=(
            _token(1, "Stav", "stav", "NOUN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "zlepšil", "zlepšit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, ",", ",", "PUNCT", 5, "punct"),
            _token(4, "ale", "ale", "CCONJ", 5, "cc"),
            _token(5, "musel", "muset", "VERB", 2, "conj", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(6, "ulehnout", "ulehnout", "VERB", 5, "xcomp", Polarity="Pos"),
            _token(7, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )


def test_a_coordinated_predicate_is_a_second_sentence() -> None:
    """„Jeho stav se přechodně zlepšil, **ale brzy musel znovu
    ulehnout**." Ta druhá část NENÍ člen první věty — je to DRUHÁ
    PREDIKACE téže promluvy. Hlásit ji jako ztracený člen je nepravda
    o tom, co ta část textu je, a ptát se „jak se ta role jmenuje" je
    výzva, aby člověk dosadil druhou větu jako člen první.

    **Změřeno: 35 vět z 238 (15 %)** — největší otevřená rodina korpusu.
    """
    from core_semantics.cascade import second_predications

    reading = _two_clauses()
    assert [t.form for t in second_predications(reading)] == ["musel"]


def test_a_coordinated_noun_is_still_a_member() -> None:
    """PROTIPŘÍKLAD: „psi a kočky" je SOUŘADNÉ JMÉNO, tedy člen věty —
    a členem zůstat musí. Rozhoduje `_is_predicate`, ne spojka: kdyby se
    bralo `conj` bez té otázky, zmizel by z věty podmět."""
    from core_semantics.cascade import second_predications

    reading = Reading(
        tokens=(
            _token(1, "Psi", "pes", "NOUN", 2, "nsubj", Case="Nom", Number="Plur"),
            _token(2, "štěkají", "štěkat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(3, "a", "a", "CCONJ", 4, "cc"),
            _token(4, "kočky", "kočka", "NOUN", 1, "conj", Case="Nom", Number="Plur"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    assert second_predications(reading) == ()


def test_the_second_sentence_is_not_reported_as_a_lost_member() -> None:
    """A CELÝ PODSTROM S NÍ: členy druhé věty jsou JEJÍ, ne ztracené
    členy první."""
    verdict = cascade(_two_clauses())
    formy = {form for form, _ in verdict.lost}
    assert "musel" not in formy and "ulehnout" not in formy


def test_the_second_sentence_is_named_in_the_trace() -> None:
    """Přiznaná mez je něco jiného než mlčení: „ztracený člen" tvrdil
    o té části textu něco, co není.

    **Hlásí se JEN ta, kterou neumíme** *(W-71)*: druhá věta se SDÍLENÝM
    podmětem se od té chvíle čte, takže tvrdit u ní „číst ji zatím
    neumím" by byly dvě hlášky o jedné věci, které si odporují."""
    vlastni = Reading(
        tokens=(
            _token(1, "Stav", "stav", "NOUN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "zlepšil", "zlepšit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "ale", "ale", "CCONJ", 5, "cc"),
            _token(4, "lékař", "lékař", "NOUN", 5, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(5, "váhal", "váhat", "VERB", 2, "conj", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(6, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    stopa = chr(10).join(cascade(vlastni).trace)
    assert "DRUHÁ VĚTA" in stopa and "váhal" in stopa
    assert "číst ji zatím neumím" in stopa
    # A u SDÍLENÉHO podmětu se to NEŘÍKÁ — tam se čte. Bez patra
    # souřadnosti se ale čte i tady, takže se zkouší s ním *(B‑24)*.
    from core_semantics.cascade import coordination_tier

    sdileny = chr(10).join(
        cascade(_two_clauses(), tiers=(*HARD_TIERS, coordination_tier(czech_seed()))).trace
    )
    assert "číst ji zatím neumím" not in sdileny


def test_the_second_sentence_borrows_the_subject_from_the_first() -> None:
    """DRUHÁ VĚTA SE SDÍLENÝM PODMĚTEM *(W‑71)*. „Stav se zlepšil, ale
    musel ulehnout." — druhá věta podmět NEVYSLOVILA a nemusela: řekla ho
    první. Systém si ho tedy NEDOMÝŠLÍ, BERE HO Z TÉŽE PROMLUVY.

    Podmět se KOPÍRUJE, nezakládá: je to táž zmínka, takže musí padnout
    na týž uzel — vyrobit druhou by riskovalo dva uzly pro jednoho
    člověka (M‑2)."""
    from core_semantics.cascade import coordination_tier

    verdict = cascade(_two_clauses(), tiers=(*HARD_TIERS, coordination_tier(czech_seed())))
    first = verdict.survivors[0].predication
    assert first.second is not None
    assert first.second.predicate == "muset"
    podmet = first.second.role(ROLE_SUBJECT)
    assert podmet is not None and podmet.lemma == "stav"
    assert podmet is first.role(ROLE_SUBJECT), "táž zmínka, ne druhá kopie"


def test_a_second_sentence_with_its_own_subject_keeps_it() -> None:
    """PODMĚT VYSLOVENÝ PODRUHÉ *(W‑73)*. „Stav se zlepšil, ale lékař
    váhal." — druhá věta si nic nepůjčuje, řekla si o kom je sama.

    **Uzel se ZAKLÁDÁ, nekopíruje**, a proto to musí být v hlášení vidět:
    u sdíleného podmětu se přenáší TÁŽ zmínka, tady vzniká DRUHÁ — a dva
    uzly pro jednoho člověka jsou nejdražší chyba, jakou tenhle systém
    umí (M‑2)."""
    from core_semantics.cascade import coordination_tier

    reading = Reading(
        tokens=(
            _token(1, "Stav", "stav", "NOUN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "zlepšil", "zlepšit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "ale", "ale", "CCONJ", 5, "cc"),
            _token(4, "lékař", "lékař", "NOUN", 5, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(5, "váhal", "váhat", "VERB", 2, "conj", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(6, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    verdict = cascade(reading, tiers=(*HARD_TIERS, coordination_tier(czech_seed())))
    druha = verdict.survivors[0].predication.second
    assert druha is not None and druha.predicate == "váhat"
    podmet = druha.role(ROLE_SUBJECT)
    assert podmet is not None and podmet.lemma == "lékař", (
        "podmět je VYSLOVENÝ, ne převzatý z první věty"
    )
    stopa = chr(10).join(verdict.trace)
    assert "VLASTNÍ PODMĚT" in stopa and "NEPŘEBÍRÁ" in stopa


def test_a_written_sentence_always_names_its_unread_half() -> None:
    """B‑24. Zúžení hlášení na druhé věty s VLASTNÍM podmětem propustilo
    TŘETÍ PŘÍPAD: větu, u které druhá predikace nevznikla z jiného důvodu
    — první čtení je JÁDROVÁ RELACE a `kdo` v ní není, takže se podmět
    nemá o co opřít.

    **Ta věta se ZAPISUJE**, takže mlčení o její druhé půlce je TICHÝ
    ČÁSTEČNÝ ZÁPIS: do báze jde fakt a část téže věty zmizí beze slova
    (I‑1). U nezapsané věty by chybějící poznámka byla kosmetika.

    Jde celou cestou přes `.utter(`, protože jádrovou relaci dosazuje až
    patro relace — na holé kaskádě ta věta `kdo` ještě má a případ by
    vůbec nenastal."""
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session
    from core_semantics.tests import golden

    veta = Reading(
        tokens=(
            _token(1, "Němec", "Němec", "PROPN", 4, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "byl", "být", "AUX", 4, "cop", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "český", "český", "ADJ", 4, "amod", Case="Nom", Gender="Masc", Number="Sing"),
            _token(4, "vlastenec", "vlastenec", "NOUN", 0, "root", Case="Nom", Gender="Masc", Number="Sing"),
            _token(5, "a", "a", "CCONJ", 6, "cc"),
            _token(6, "publikoval", "publikovat", "VERB", 4, "conj", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(7, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(text=text, readings=(veta,))

    session = Session(lexicon=golden.golden_lexicon())
    result = session.utter("Němec byl český vlastenec a publikoval.", _Recorded())
    assert result.statement_id is not None, "ta věta se zapisuje"
    hlaseni = chr(10).join((*result.lines, *result.trace))
    assert "DRUHÁ VĚTA" in hlaseni and "publikoval" in hlaseni, (
        "a právě proto se druhá půlka MUSÍ pojmenovat"
    )


def test_one_utterance_can_write_two_statements() -> None:
    """W‑72 — reviewer chtěl VIDĚT dva výroky z jedné promluvy, ne test,
    který tvrdí, že by mohly být.

    Chytilo se tím i POŘADÍ PATER: patro souřadnosti běželo PŘED
    kvantifikátorem, takže si druhá věta půjčovala roli BEZ
    kvantifikátoru — a role bez kvantifikátoru se do jádra nedostane
    (`UnquantifiedRole`), takže druhý zápis nikdy nevznikl."""
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session

    veta = Reading(
        tokens=(
            _token(1, "Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "zpíval", "zpívat", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "a", "a", "CCONJ", 4, "cc"),
            _token(4, "tančil", "tančit", "VERB", 2, "conj", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(text=text, readings=(veta,))

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="PROPN", number="Sing", case="Nom", deprel="nsubj"
            ),
            operation=Operation.SELF,
            learned_from="test W‑72",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    session.utter("Jan zpíval a tančil.", _Recorded())
    zapsane = [
        str(s.formula)
        for s in session.kb.active()
        if not str(s.formula).startswith(("member(", "role("))
    ]
    assert zapsane == ["zpívat(kdo:Jan)", "tančit(kdo:Jan)"], (
        "dva výroky z JEDNÉ promluvy, oba o TÉMŽE uzlu"
    )


def test_a_spoken_second_subject_makes_its_own_node() -> None:
    """W‑73 a COUNTEREXAMPLE REVIEWERA: žádný uzel nevznikne dvakrát pro
    totéž jméno v jedné promluvě — ale dvě RŮZNÁ jména dají dva uzly.

    „Petr přišel a Jana odešla." zapíše dva výroky o DVOU uzlech, kdežto
    „Jan zpíval a tančil." o JEDNOM. Rozdíl je vidět i v hlášení, a to je
    ta půlka, na které záleží: u sdíleného podmětu se přenáší TÁŽ zmínka,
    u vysloveného vzniká NOVÝ uzel — a to je místo, kde se dva uzly pro
    jednoho člověka vyrábějí nejsnáz (M‑2)."""
    from core_semantics.oracle import Utterance
    from core_semantics.session import Session

    veta = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "přišel", "přijít", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "a", "a", "CCONJ", 5, "cc"),
            _token(4, "Jana", "Jana", "PROPN", 5, "nsubj", Case="Nom", Gender="Fem", Number="Sing"),
            _token(5, "odešla", "odejít", "VERB", 2, "conj", Gender="Fem", Number="Sing", Polarity="Pos"),
            _token(6, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )

    class _Recorded:
        provenance = "test"

        def parse(self, text: str) -> Utterance:
            return Utterance(text=text, readings=(veta,))

    lexicon = czech_seed()
    lexicon.add(
        LearnedPattern(
            trigger=Trigger(
                lemma="", upos="PROPN", number="Sing", case="Nom", deprel="nsubj"
            ),
            operation=Operation.SELF,
            learned_from="test W‑73",
            status=PatternStatus.CONFIRMED,
        )
    )
    session = Session(lexicon=lexicon)
    result = session.utter("Petr přišel a Jana odešla.", _Recorded())
    zapsane = [
        str(s.formula)
        for s in session.kb.active()
        if not str(s.formula).startswith(("member(", "role("))
    ]
    assert zapsane == ["přijít(kdo:Petr)", "odejít(kdo:Jana)"]
    hlaseni = chr(10).join(result.lines)
    assert "VLASTNÍ PODMĚT" in hlaseni and "VYSLOVENÝ podruhé" in hlaseni, (
        "že uzel VZNIKÁ a nepřebírá se, musí být vidět"
    )


def test_a_second_sentence_with_two_same_named_members_does_not_crash() -> None:
    """REGRESE Z KOLA #110, nalezená BĚHEM NAD KORPUSEM, ne testem:
    „Zvířata lze chovat doma i venku." dá v druhé větě dvakrát `jak`
    a `Predication` duplicitní roli ODMÍTÁ — patro ji tedy nesmí ani
    postavit.

    Táž úvaha jako W‑63, jen uvnitř druhé věty: oba členy padnou na SVŮJ
    TVAR, a když je nerozliší ani ten, druhá věta se nepřečte a ohlásí se
    (W‑70). Spadnout nesmí ani v jednom případě."""
    from core_semantics.cascade import coordination_tier

    reading = Reading(
        tokens=(
            _token(1, "Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "přišel", "přijít", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "a", "a", "CCONJ", 4, "cc"),
            _token(4, "zpíval", "zpívat", "VERB", 2, "conj", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(5, "doma", "doma", "ADV", 4, "advmod"),
            _token(6, "venku", "venku", "ADV", 4, "advmod"),
            _token(7, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    verdict = cascade(reading, tiers=(*HARD_TIERS, coordination_tier(czech_seed())))
    assert verdict.survivors, "věta se čte dál, jen druhá půlka nevznikne"


def test_a_year_is_part_of_the_mention_not_a_lost_member() -> None:
    """W‑74. „v roce **1986**" hlásilo 1986 jako ZTRACENÝ ČLEN — jenže
    z té věty nevypadlo, patří ke „roku". A obě věty *„V roce 1986…"*
    i *„V roce 1990…"* dávaly TÝŽ uzel `rok`, tedy jeden uzel pro
    všechny roky. Obojí byla nepravda a obojí spravuje složení."""
    from core_semantics.cascade import year_under

    def _v_roce(rok: str) -> Reading:
        return Reading(
            tokens=(
                _token(1, "V", "v", "ADP", 2, "case", AdpType="Prep", Case="Loc"),
                _token(2, "roce", "rok", "NOUN", 4, "obl", Case="Loc", Gender="Masc", Number="Sing"),
                _token(3, rok, rok, "NUM", 2, "nummod", NumForm="Digit", NumType="Card"),
                _token(4, "pršelo", "pršet", "VERB", 0, "root", Gender="Neut", Number="Sing", Polarity="Pos"),
                _token(5, ".", ".", "PUNCT", 4, "punct"),
            ),
            provenance="test",
        )

    reading = _v_roce("1986")
    assert year_under(reading.tokens[1], reading) is reading.tokens[2]
    role = generate(reading)[0].predication.role("v+Loc/rok")
    assert role is not None and role.lemma == "rok_1986"
    assert dropped_tokens(reading, generate(reading)[0].predication) == ()
    # DVA RŮZNÉ ROKY NEJSOU TÝŽ UZEL.
    jiny = generate(_v_roce("1990"))[0].predication.role("v+Loc/rok")
    assert jiny is not None and jiny.lemma == "rok_1990"


def test_a_count_is_not_a_year() -> None:
    """PROTIPŘÍKLAD: „s **92** lidmi" je POČET, ne letopočet, a hlásí se
    dál jako ztracený člen — dokud se o počtech nerozhodne zvlášť.
    Rozlišuje to STAVBA (čtyřciferné `NumType=Card`), ne seznam časových
    jmen; ten by byl druhý slovník vedle parserova."""
    from core_semantics.cascade import year_under

    reading = Reading(
        tokens=(
            _token(1, "s", "s", "ADP", 3, "case", AdpType="Prep", Case="Ins"),
            _token(2, "92", "92", "NUM", 3, "nummod", NumForm="Digit", NumType="Card"),
            _token(3, "lidmi", "člověk", "NOUN", 4, "obl", Case="Ins", Number="Plur"),
            _token(4, "mluvil", "mluvit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance="test",
    )
    assert year_under(reading.tokens[2], reading) is None


def test_the_year_is_recognised_in_one_place_only() -> None:
    """`role_signal` se ptá `year_under`, nepíše si vlastní kopii — dvě
    kopie téže podmínky se rozejdou a nikdo nepozná, která platí. Táž
    úvaha jako u `is_bare_genitive` a `titled_name_of`."""
    import inspect

    from core_semantics.cascade import role_signal

    kod = chr(10).join(
        radek
        for radek in inspect.getsource(role_signal).splitlines()
        if not radek.lstrip().startswith("#")
    )
    assert "year_under(" in kod
    assert "NumType" not in kod


def test_a_date_is_one_mention() -> None:
    """W‑75. „9. ledna 1890" je JEDEN časový údaj — dokud se „9." hlásila
    jako ztracený člen, tvrdil systém o textu totéž, co tvrdil
    o letopočtu před W‑74."""
    from core_semantics.cascade import date_parts_under

    reading = Reading(
        tokens=(
            _token(1, "narodil", "narodit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "9.", "9.", "NUM", 3, "nummod", NumForm="Digit", NumType="Card"),
            _token(3, "ledna", "leden", "NOUN", 1, "obl", Case="Gen", Gender="Masc", Number="Sing"),
            _token(4, "1890", "1890", "NUM", 3, "nummod", NumForm="Digit", NumType="Card"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert [t.form for t in date_parts_under(reading.tokens[2], reading)] == ["9.", "1890"]
    predication = generate(reading)[0].predication
    zminky = {r.mention.lemma for r in predication.roles}
    assert "9._leden_1890" in zminky
    assert dropped_tokens(reading, predication) == ()


def test_a_count_is_not_a_date_part() -> None:
    """PROTIPŘÍKLAD, a je to celý důvod, proč se stráž kouká na TEČKU
    a ne na hlavu: rozbor „9." a „92" NEROZLIŠÍ ničím jiným — obě jsou
    `NumForm=Digit`, `NumType=Card`, `nummod`. Rozeznat je podle toho,
    že nad jednou stojí měsíc, by znamenalo mít v kódu SEZNAM MĚSÍCŮ."""
    from core_semantics.cascade import date_parts_under

    reading = Reading(
        tokens=(
            _token(1, "mluvil", "mluvit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "s", "s", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
            _token(3, "92", "92", "NUM", 4, "nummod", NumForm="Digit", NumType="Card"),
            _token(4, "lidmi", "člověk", "NOUN", 1, "obl", Case="Ins", Number="Plur"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert date_parts_under(reading.tokens[3], reading) == ()


def test_a_quantity_word_is_not_a_date_part() -> None:
    """A množství SLOVEM („tři typy", „pět měsíců") taky ne — je to
    vlastní úloha a do složení zmínky nepatří."""
    from core_semantics.cascade import date_parts_under

    reading = Reading(
        tokens=(
            _token(1, "Existují", "existovat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(2, "tři", "tři", "NUM", 3, "nummod", Case="Nom", NumForm="Word", NumType="Card"),
            _token(3, "typy", "typ", "NOUN", 1, "nsubj", Case="Nom", Gender="Masc", Number="Plur"),
            _token(4, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert date_parts_under(reading.tokens[2], reading) == ()


def test_a_nested_date_is_one_mention_too() -> None:
    """W‑77. „dne **25. prosince 1938**" má měsíc jako `nmod` pod „dne",
    takže se dosud nesložilo NIC — ani řadová číslovka, ani letopočet —
    a obojí se hlásilo jako ztracený člen věty, jejímž členem není."""
    from core_semantics.cascade import date_parts_under

    reading = Reading(
        tokens=(
            _token(1, "Zemřel", "zemřít", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "dne", "den", "NOUN", 1, "obl", Case="Gen", Gender="Masc", Number="Sing"),
            _token(3, "25.", "25.", "NUM", 4, "nummod", NumForm="Digit", NumType="Card"),
            _token(4, "prosince", "prosinec", "NOUN", 2, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(5, "1938", "1938", "NUM", 4, "nummod", NumForm="Digit", NumType="Card"),
            _token(6, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert [t.form for t in date_parts_under(reading.tokens[1], reading)] == [
        "25.",
        "prosince",
        "1938",
    ]
    predication = generate(reading)[0].predication
    assert "den_25._prosinec_1938" in {r.mention.lemma for r in predication.roles}
    assert dropped_tokens(reading, predication) == ()


def test_a_plain_modifier_is_not_a_nested_date() -> None:
    """PROTIPŘÍKLAD, a je to celá stráž: skládat `nmod` obecně by sáhlo
    na „ulice Karla Čapka" i „Město Praha", kde je `nmod` něco úplně
    jiného. Rozlišuje se BEZ SEZNAMU MĚSÍCŮ — ne podle toho, jak se ta
    hlava jmenuje, ale podle toho, CO POD NÍ VISÍ. V měřeném korpusu je
    takových `nmod` uzlů 12, ostatních 481."""
    from core_semantics.cascade import date_parts_under

    reading = Reading(
        tokens=(
            _token(1, "Bydlel", "bydlet", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "v", "v", "ADP", 3, "case", AdpType="Prep", Case="Loc"),
            _token(3, "ulici", "ulice", "NOUN", 1, "obl", Case="Loc", Gender="Fem", Number="Sing"),
            _token(4, "Karla", "Karel", "PROPN", 3, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    assert date_parts_under(reading.tokens[2], reading) == ()


def test_a_proper_name_is_concrete_in_any_role() -> None:
    """W‑78, DESÁTÁ INSTANCE TÉŽE RODINY. Že `PROPN` je signál individua,
    je rozhodnuté od N‑2d — jenže to byl NAUČENÝ VZOR vázaný na (upos,
    číslo, pád, deprel), takže „Karel Čapek" dostal `·` jako `nsubj`
    a jako `nsubj:pass` nebo `Ins:arg` se na něj systém ptal znovu.

    **Důsledek byl na straně ODPOVÍDÁNÍ, ne čtení:** „Byl Karel Čapek
    pohřben na Vyšehradě?" nedostalo odpověď, ačkoli ten fakt v bázi
    ležel. Otázka, na kterou báze odpověď MÁ a nedá ji, je horší než
    chybějící zápis."""
    for deprel, case in (("nsubj:pass", "Nom"), ("obl:arg", "Ins")):
        reading = Reading(
            tokens=(
                _token(1, "Karel", "Karel", "PROPN", 3, deprel, Case=case, Gender="Masc", Number="Sing"),
                _token(2, "byl", "být", "AUX", 3, "aux:pass", Gender="Masc", Number="Sing", Polarity="Pos"),
                _token(3, "pohřben", "pohřbený", "ADJ", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos", Voice="Pass"),
                _token(4, ".", ".", "PUNCT", 3, "punct"),
            ),
            provenance="test",
        )
        verdict = cascade(
            reading, tiers=(*HARD_TIERS, quantifier_tier(czech_seed()))
        )
        role = next(
            r
            for r in verdict.survivors[0].predication.roles
            if r.mention.upos == "PROPN"
        )
        assert role.quantifier is Quantifier.SELF, deprel
        assert "vlastní jméno" in role.source


def test_a_common_noun_is_still_asked_about() -> None:
    """PROTIPŘÍKLAD: „Byla kniha napsána?" se dál ptá. Je to VLASTNOST
    JMÉNA, ne role — proto se nedoplňoval seznam deprelů, který by tutéž
    otázku vrátil u jedenáctého tvaru."""
    reading = Reading(
        tokens=(
            _token(1, "kniha", "kniha", "NOUN", 3, "nsubj:pass", Case="Nom", Gender="Fem", Number="Sing"),
            _token(2, "byla", "být", "AUX", 3, "aux:pass", Gender="Fem", Number="Sing", Polarity="Pos"),
            _token(3, "napsána", "napsaný", "ADJ", 0, "root", Gender="Fem", Number="Sing", Polarity="Pos", Voice="Pass"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    verdict = cascade(reading, tiers=(*HARD_TIERS, quantifier_tier(czech_seed())))
    role = next(
        r for r in verdict.survivors[0].predication.roles if r.mention.upos == "NOUN"
    )
    assert role.quantifier is None


def test_a_passive_has_one_role_name_spoken_or_not() -> None:
    """W‑79 a COUNTEREXAMPLE REVIEWERA: TÁŽ VĚTA MÁ TOUŽ ROLI, ať text
    podmět zopakuje, nebo ne.

    Trpný rod psal `kdo`, když byl podmět vynechaný, a četl `co`, když
    byl vyslovený — DVĚ JMÉNA PRO TOUŽ ROLI podle toho, jestli text
    podmět zopakoval. Báze se tím rozpadala na dvě poloviny, které se
    nepotkají, a mezera pak tvrdila „nikdo to neřekl" o výroku, který
    v ní ležel."""
    from core_semantics.cascade import passive_tier, prodrop_tier

    vysloveny = Reading(
        tokens=(
            _token(1, "Karel", "Karel", "PROPN", 3, "nsubj:pass", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "byl", "být", "AUX", 3, "aux:pass", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, "pohřben", "pohřbený", "ADJ", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos", Voice="Pass"),
            _token(4, "na", "na", "ADP", 5, "case", AdpType="Prep", Case="Loc"),
            _token(5, "Vyšehradě", "Vyšehrad", "PROPN", 3, "obl", Case="Loc", Gender="Masc", NameType="Geo", Number="Sing"),
            _token(6, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    vynechany = Reading(
        tokens=(
            _token(1, "Byl", "být", "AUX", 2, "aux:pass", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "pohřben", "pohřbený", "ADJ", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos", Voice="Pass"),
            _token(3, "na", "na", "ADP", 4, "case", AdpType="Prep", Case="Loc"),
            _token(4, "Vyšehradě", "Vyšehrad", "PROPN", 2, "obl", Case="Loc", Gender="Masc", NameType="Geo", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    patra = (*HARD_TIERS, passive_tier(), prodrop_tier())
    jmena = {
        r.name
        for reading in (vysloveny, vynechany)
        for r in cascade(reading, tiers=patra).survivors[0].predication.roles
        if r.mention.upos != "PROPN" or r.name == ROLE_OBJECT
    }
    assert jmena == {ROLE_OBJECT}, "jedno jméno, ať text podmět zopakuje nebo ne"


def _trpna_veta(instrumental: str, deprel: str, *, predlozka: str | None = None) -> Reading:
    """„Kniha byla napsána <X>." — jediná proměnná je značka u X."""
    tokens = [
        _token(1, "Kniha", "kniha", "NOUN", 3, "nsubj:pass", Case="Nom", Gender="Fem", Number="Sing"),
        _token(2, "byla", "být", "AUX", 3, "aux:pass", Number="Sing", Voice="Act"),
        _token(3, "napsána", "napsaný", "VERB", 0, "root", Gender="Fem", Number="Sing", Polarity="Pos", Voice="Pass"),
        _token(5, instrumental, instrumental.lower(), "NOUN", 3, deprel, Case="Ins", Gender="Masc", Number="Sing"),
        _token(6, ".", ".", "PUNCT", 3, "punct"),
    ]
    if predlozka is not None:
        tokens.insert(3, _token(4, predlozka, predlozka, "ADP", 5, "case", AdpType="Prep", Case="Ins"))
    return Reading(tokens=tuple(tokens), provenance="test")


def _trpny_rozbor(reading: Reading) -> Predication:
    return cascade(
        reading, tiers=(*HARD_TIERS, passive_tier())
    ).survivors[0].predication


def test_the_agent_of_a_passive_gets_a_name() -> None:
    """KONATEL *(W‑80)*: holý `Ins:arg` pod TRPNÝM přísudkem je „kdo".

    Patiens dostal jméno v W‑59, konatel do dneška ne — „Kniha byla
    napsána Čapkem." dávala `Ins:arg:Čapek`, tedy TVAR místo jména,
    a věta se kvůli povrchové roli nezapsala."""
    predication = _trpny_rozbor(_trpna_veta("Čapkem", "obl:arg"))
    konatel = next(r for r in predication.roles if r.name == ROLE_SUBJECT)
    assert konatel.mention.lemma == "čapkem"
    assert not konatel.shaped
    assert konatel.source == "konatel trpné věty — holý `Ins:arg`"
    assert predication.role(ROLE_OBJECT) is not None


def test_an_instrument_under_a_passive_is_not_the_agent() -> None:
    """PROTIPŘÍKLAD, KTERÝ JE CELÁ PAST: „napsána PEREM" je taky trpná.

    Instrumentál sám o sobě konatele neznamená; rozliší to `obl` proti
    `obl:arg` — volná okolnost proti valenčnímu doplnění."""
    predication = _trpny_rozbor(_trpna_veta("perem", "obl"))
    assert predication.role(ROLE_SUBJECT) is None


def test_a_prepositional_instrumental_under_a_passive_is_not_the_agent() -> None:
    """PROTIPŘÍKLAD Z KORPUSU: „Je spojována S emancipačními snahami."

    Má `obl:arg` i instrumentál, ale předložku — konatel je HOLÝ."""
    predication = _trpny_rozbor(_trpna_veta("snahami", "obl:arg", predlozka="s"))
    assert predication.role(ROLE_SUBJECT) is None


def test_an_active_instrumental_argument_is_not_the_agent() -> None:
    """PROTIPŘÍKLAD ZMĚŘENÝ NA KORPUSU: holý `Ins:arg` je v deseti větách
    a ANI JEDNA není trpná („stal se redaktorem", „zabývá se zkoumáním").
    Bez `Voice=Pass` na přísudku se nepřejmenovává nic."""
    reading = _trpna_veta("redaktorem", "obl:arg")
    cinne = tuple(
        replace(t, feats=tuple((k, v) for k, v in t.feats if k != "Voice"))
        if t.deprel == "root"
        else t
        for t in reading.tokens
    )
    predication = _trpny_rozbor(Reading(tokens=cinne, provenance="test"))
    assert predication.role(ROLE_SUBJECT) is None


def test_an_active_prodrop_still_gets_a_subject() -> None:
    """PROTIPŘÍKLAD: v ČINNÉM rodě je vynechaný podmět dál `kdo`.
    Rozhoduje `Voice=Pass` na přísudku, ne to, že podmět chybí."""
    from core_semantics.cascade import prodrop_tier

    reading = Reading(
        tokens=(
            _token(1, "Narodil", "narodit", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(2, "v", "v", "ADP", 3, "case", AdpType="Prep", Case="Loc"),
            _token(3, "Praze", "Praha", "PROPN", 1, "obl", Case="Loc", Gender="Fem", NameType="Geo", Number="Sing"),
            _token(4, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(
        reading, tiers=(*HARD_TIERS, prodrop_tier())
    ).survivors[0].predication
    assert predication.role(ROLE_SUBJECT) is not None


def _pronoun_predicate(form: str, lemma: str, upos: str, prontype: str) -> Reading:
    """„Vesmír je <zájmeno>." — `PronType` je jediná proměnná."""
    return Reading(
        tokens=(
            _token(1, "Vesmír", "vesmír", "NOUN", 3, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "je", "být", "AUX", 3, "cop", Number="Sing", Polarity="Pos"),
            _token(3, form, lemma, upos, 0, "root", Case="Nom", Gender="Neut", Number="Sing", PronType=prontype),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )


def _quantifier_of(reading: Reading, name: str) -> Quantifier | None:
    from core_semantics.tests import golden

    predication = cascade(
        reading, tiers=(*HARD_TIERS, quantifier_tier(golden.golden_lexicon()))
    ).survivors[0].predication
    return next(r.quantifier for r in predication.roles if r.name == name)


def test_a_total_pronoun_carries_its_own_quantifier() -> None:
    """KVANTIFIKÁTOR SI NESE SAMO SLOVO *(W‑81)*: „vše" znamená totalitu,
    takže ptát se „o každém, nebo o některém?" je otázka, jejíž odpověď
    v textu už stojí. Táž úvaha jako u vlastního jména (W‑78).

    Dosud role s `DET` propadla první podmínkou patra (`DET` není
    v `QUANTIFIED_UPOS`), takže se na ni nikdo neptal — a zakotvení pak
    sáhlo po zbytkové větvi a řeklo o ní nepravdu."""
    assert _quantifier_of(_pronoun_predicate("vše", "všechen", "DET", "Tot"), "co") is Quantifier.FOR_ALL


def test_an_indefinite_pronoun_is_existential() -> None:
    """„něco" je existence — táž značka, jiná hodnota *(W‑81)*."""
    assert _quantifier_of(_pronoun_predicate("něco", "něco", "PRON", "Ind"), "co") is Quantifier.EXISTS


def test_a_negative_pronoun_gets_no_quantifier() -> None:
    """PROTIPŘÍKLAD A POJMENOVANÁ MEZ: zápor NENÍ třetí kvantifikátor.
    „nikdo" je popření existence a to jádro nese na PREDIKACI (silná
    negace), ne na roli; kvantifikátor by z toho udělal výrok „platí
    o žádném", který nejde ověřit *(W‑81)*."""
    assert _quantifier_of(_pronoun_predicate("nic", "nic", "PRON", "Neg"), "co") is None


def _copula_sentence(deprel: str) -> Reading:
    """„Jan je učitel." — jediná proměnná je deprel spony."""
    return Reading(
        tokens=(
            _token(1, "Jan", "Jan", "PROPN", 3, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "je", "být", "AUX", 3, deprel, Number="Sing", Polarity="Pos"),
            _token(3, "učitel", "učitel", "NOUN", 0, "root", Case="Nom", Gender="Masc", Number="Sing"),
            _token(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )


def test_a_subtyped_copula_is_still_a_copula() -> None:
    """JEDNO MÍSTO ODPOVÍDÁ NA OTÁZKU „JE TOHLE SPONA?" *(W‑66)*.

    Čtyři místa kaskády se ptala PŘESNÝM ŘETĚZCEM, takže `cop:expl` by
    propadlo a věta by přišla o přísudek — tedy o to, čím vůbec je.
    V korpusu je 61 spon a NULA podtypů: opravuje se RIZIKO, ne dnešní
    chování, a tahle zkouška je proto jediné místo, kde se podtyp
    vůbec ukáže."""
    from core_semantics.cascade import is_copula

    assert is_copula(_copula_sentence("cop:expl").tokens[1])
    assert is_copula(_copula_sentence("cop").tokens[1])


def test_something_that_is_not_a_copula_is_not_mistaken_for_one() -> None:
    """PROTIPŘÍKLAD: základ se bere celý, ne jako předpona. `copula`
    ani `aux` spona nejsou a `base_deprel` je nesmí propustit."""
    from core_semantics.cascade import is_copula

    assert not is_copula(_copula_sentence("aux").tokens[1])
    assert not is_copula(_copula_sentence("copula").tokens[1])


def test_a_subtyped_copula_reads_the_same_sentence() -> None:
    """CELOU CESTOU, VŠECHNA ČTYŘI MÍSTA NARÁZ: věta se sponou `cop:expl`
    dá TOTÉŽ čtení jako se sponou `cop`. Kdyby kterékoli z těch míst
    zůstalo na přesné shodě, rozejdou se."""
    podtyp = generate(_copula_sentence("cop:expl"))[0].predication
    holy = generate(_copula_sentence("cop"))[0].predication
    assert str(podtyp) == str(holy)


def _name_with_second_part(deprel: str, case: str, *, preposition: bool = False) -> Reading:
    """„Bydlí v Hradci Králové." — jediné, co se mění, je vazba druhého
    dílu jména a jeho pád."""
    tokens = [
        _token(1, "Bydlí", "bydlet", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
        _token(2, "v", "v", "ADP", 3, "case", AdpType="Prep", Case="Loc"),
        _token(3, "Hradci", "Hradec", "PROPN", 1, "obl", Case="Loc", Gender="Masc", NameType="Geo", Number="Sing"),
        _token(5, "Králové", "Králové", "PROPN", 3, deprel, Case=case, Gender="Fem", NameType="Geo", Number="Sing"),
        _token(6, ".", ".", "PUNCT", 1, "punct"),
    ]
    if preposition:
        tokens.insert(3, _token(4, "pod", "pod", "ADP", 5, "case", AdpType="Prep", Case="Ins"))
    return Reading(tokens=tuple(tokens), provenance="test")


def test_a_name_in_the_genitive_is_part_of_the_name() -> None:
    """UZEL SE NEJMENUJE ZKRÁCENĚ *(W‑72)*. „v **Hradci Králové**"
    dávalo `·Hradec` — vlastní jméno, které v textu takhle NESTOJÍ.

    UD ten díl váže `nmod`, ne `flat`, protože se neshoduje v pádě:
    `Hradci` je `Loc`, `Králové` `Gen`. Rozliší se to STAVBOU, ne
    seznamem měst: hlava i díl jsou `PROPN` a genitiv je HOLÝ."""
    predication = cascade(
        _name_with_second_part("nmod", "Gen"), tiers=HARD_TIERS
    ).survivors[0].predication
    jmena = [r.mention.lemma for r in predication.roles]
    assert "Hradec_Králové" in jmena
    assert "Hradec" not in jmena, "zkrácené jméno nesmí zůstat ani jako mezistav"


def test_a_prepositional_second_part_is_not_composed() -> None:
    """POJMENOVANÁ MEZ: „Rožnov **pod** Radhoštěm" holý genitiv nemá,
    takže se neskládá — a hlásí se dál. Je to mez, ne tichý default."""
    predication = cascade(
        _name_with_second_part("nmod", "Ins", preposition=True), tiers=HARD_TIERS
    ).survivors[0].predication
    assert all("Králové" not in r.mention.lemma for r in predication.roles)


def test_a_flat_second_part_still_composes() -> None:
    """PROTIPŘÍKLAD, KTERÝ HLÍDÁ, ŽE SE NIC NEROZBILO: `flat` se skládal
    od B‑21 a skládá se dál — „Čapka Josefa" i „Ludvíku Rittersberka"
    jdou touhle větví, ne tou novou."""
    predication = cascade(
        _name_with_second_part("flat", "Loc"), tiers=HARD_TIERS
    ).survivors[0].predication
    assert any(r.mention.lemma == "Hradec_Králové" for r in predication.roles)


def test_a_composed_name_part_is_not_reported_as_an_attribute() -> None:
    """CO SE SLOŽILO DO JMÉNA, PŘÍVLASTEK UŽ NENÍ *(W‑72)*. Ohlásit
    k jednomu uzlu ještě vztah „Hradec_Králové Králové" znamená tvrdit,
    že vedle věty stojí druhý výrok o části toho jména."""
    from core_semantics.cascade import genitive_attributes

    reading = _name_with_second_part("nmod", "Gen")
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    assert genitive_attributes(reading, predication) == ()


def test_a_name_the_node_carries_only_partly_is_said_out_loud() -> None:
    """UZEL, JEHOŽ JMÉNO JE VLASTNÍM PREFIXEM JMÉNA V TEXTU *(W‑75)*.
    „v Rožnově **pod Radhoštěm**" dá `·Rožnov` — vlastní jméno, které
    v textu takhle nestojí. Složit to nejde (druhý díl má PŘEDLOŽKU,
    takže od genitivního dílu W‑72 se liší), ale mlčet se nesmí."""
    from core_semantics.cascade import partial_name_tier

    reading = _name_with_second_part("nmod", "Ins", preposition=True)
    predication = cascade(
        reading, tiers=(*HARD_TIERS, partial_name_tier())
    ).survivors[0].predication
    assert predication.pending_name, "neúplné jméno se musí ohlásit"
    uzel, cele, _ = predication.pending_name[0]
    assert uzel == "Hradec"
    assert "Králové" in cele


def test_a_composed_name_is_not_reported_as_partial() -> None:
    """PROTIPŘÍKLAD: co se složilo (holý genitiv, W‑72), neúplné není."""
    from core_semantics.cascade import partial_name_tier

    reading = _name_with_second_part("nmod", "Gen")
    predication = cascade(
        reading, tiers=(*HARD_TIERS, partial_name_tier())
    ).survivors[0].predication
    assert predication.pending_name == ()


def test_a_part_of_a_name_is_not_asked_about_as_a_role() -> None:
    """OTÁZKA, NA KTEROU PRAVDIVÁ ODPOVĚĎ NEEXISTUJE, SE NEPTÁ *(W‑75)*.
    „Radhoštěm" není účastník děje; vyzvat člověka, ať mu dá roli, znamená
    přilepit k větě tvrzení, které v ní není — táž rodina jako W‑73."""
    from core_semantics.cascade import dropped_tokens, partial_name_tier

    reading = _name_with_second_part("nmod", "Ins", preposition=True)
    predication = cascade(
        reading, tiers=(*HARD_TIERS, partial_name_tier())
    ).survivors[0].predication
    assert all(
        token.form != "Králové" for token in dropped_tokens(reading, predication)
    )


def _adjective_in_a_name(form: str, *, first: bool) -> Reading:
    """„(Bydlí v) Malých Svatoňovicích." — přívlastek pod VLASTNÍM
    jménem. Proměnná je jen to, jestli stojí na začátku věty."""
    tokens = [
        _token(1, form, "malý", "ADJ", 2, "amod", Case="Nom", Degree="Pos", Gender="Fem", Number="Plur"),
        _token(2, "Svatoňovice", "Svatoňovice", "PROPN", 3, "nsubj", Case="Nom", Gender="Fem", NameType="Geo", Number="Plur"),
        _token(3, "leží", "ležet", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
        _token(4, ".", ".", "PUNCT", 3, "punct"),
    ]
    if not first:
        tokens.insert(0, _token(0, "Tam", "tam", "ADV", 3, "advmod"))
    return Reading(tokens=tuple(tokens), provenance="test")


def test_a_capitalised_adjective_is_part_of_the_name() -> None:
    """PŘÍVLASTEK PSANÝ VELKÝM PÍSMENEM JE ČÁST JMÉNA *(W‑78)*. „Malé
    Svatoňovice" nejsou „Svatoňovice, které jsou malé" — a uzel proto
    nese CELÉ jméno a zůstává INDIVIDUEM, ne třídou."""
    predication = cascade(
        _adjective_in_a_name("Malých", first=False), tiers=HARD_TIERS
    ).survivors[0].predication
    jmena = [r.mention.lemma for r in predication.roles]
    assert "malý_Svatoňovice" in jmena
    assert "Svatoňovice" not in jmena, "zkrácené jméno nesmí zůstat"


def test_a_lowercase_adjective_under_a_name_is_not_part_of_it() -> None:
    """PROTIPŘÍKLAD: „anglická Wikipedie" nebo „starověké Řecko" jsou
    PŘÍVLASTKY, ne části jména — dělí je VELKÉ PÍSMENO, a to je v textu,
    ne v odhadu."""
    predication = cascade(
        _adjective_in_a_name("malých", first=False), tiers=HARD_TIERS
    ).survivors[0].predication
    assert all("malý" not in r.mention.lemma for r in predication.roles)


def test_a_sentence_initial_adjective_is_a_named_limit() -> None:
    """POJMENOVANÁ MEZ *(W‑78)*: na ZAČÁTKU VĚTY velké písmeno neznamená
    nic — „Malé Svatoňovice" a „Krásná Praha" mají tam rozbor znak za
    znakem týž. Neskládá se tedy, a ten člen se HLÁSÍ; složit ho mlčky
    by znamenalo rozhodnout něco, co v rozboru není."""
    reading = _adjective_in_a_name("Malé", first=True)
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    assert all("malý" not in r.mention.lemma for r in predication.roles)
    assert any(t.form == "Malé" for t in dropped_tokens(reading, predication))


def test_an_attribute_under_a_lost_head_is_not_asked_about() -> None:
    """PŘÍVLASTEK SE SKLÁDÁ I POD ZTRACENOU HLAVOU *(W‑78)*. „…s
    **domácími** zvířaty" — `domácími` není člen věty, je to část jména
    třídy; ptát se na jeho ROLI znamená vyzvat člověka, ať z něj udělá
    účastníka děje, kterým není."""
    reading = Reading(
        tokens=(
            _token(1, "Rizika", "riziko", "NOUN", 6, "nsubj", Case="Nom", Gender="Neut", Number="Plur"),
            _token(2, "s", "s", "ADP", 3, "case", AdpType="Prep", Case="Ins"),
            _token(3, "zvířaty", "zvíře", "NOUN", 1, "nmod", Case="Ins", Gender="Neut", Number="Plur"),
            _token(5, "domácími", "domácí", "ADJ", 3, "amod", Case="Ins", Degree="Pos", Gender="Neut", Number="Plur"),
            _token(6, "rostou", "růst", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(7, ".", ".", "PUNCT", 6, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    ztracene = {t.form for t in dropped_tokens(reading, predication)}
    assert "domácími" not in ztracene, "část jména třídy není člen věty"


def test_a_composed_class_name_claims_no_subset() -> None:
    """NEUTRALITA JE CELÝ DŮVOD, PROČ SE TO SMÍ SKLÁDAT MLČKY *(W‑78)*.
    Rozbor „terapeutický pes" a „bývalý prezident" NEROZLIŠÍ, takže
    jakékoli čtení, které by o vztahu k holému jménu něco tvrdilo, by
    u jedné z nich LHALO. Složené jméno netvrdí ani u jedné."""
    from core_semantics.ast import Group, Quantifier, QueryStatus, atom, role
    from core_semantics.engine import Engine
    from core_semantics.storage import KnowledgeBase

    engine = Engine(KnowledgeBase())
    for sub, sup in (
        ("bývalý_prezident", "prezident"),
        ("prezident", "bývalý_prezident"),
        ("terapeutický_pes", "pes"),
    ):
        dotaz = atom(
            "subset",
            role("sub", Group(sub), Quantifier.SELF),
            role("sup", Group(sup), Quantifier.SELF),
        )
        assert engine.ask(dotaz).status is QueryStatus.UNKNOWN


def _possessed_noun() -> Reading:
    """„Filipovo auto stojí venku." — přivlastnění jako `amod` s
    `Poss=Yes`."""
    return Reading(
        tokens=(
            _token(1, "Filipovo", "Filipův", "ADJ", 2, "amod", Case="Nom", Gender="Neut", Number="Sing", Poss="Yes"),
            _token(2, "auto", "auto", "NOUN", 3, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
            _token(3, "stojí", "stát", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
            _token(4, "venku", "venku", "ADV", 3, "advmod"),
            _token(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )


def test_a_possessive_is_visible_in_the_mention() -> None:
    """PŘIVLASTNĚNÍ JE VIDĚT VE TVARU, NE V LEMMATU *(B‑28)*. Otázka
    „O kterém „auto" mluvíš?" NEŘÍKALA, co tu referenci zužuje, a slovo
    „Filipovo" se v celém přepisu neobjevilo ani jednou — čtenář pak
    nepozná větu o Filipově autě od věty o nějakém autě."""
    predication = cascade(_possessed_noun(), tiers=HARD_TIERS).survivors[0].predication
    role = next(r for r in predication.roles if r.name == ROLE_SUBJECT)
    assert role.mention.form == "Filipovo auto", "tvar nese, co se přivlastnilo"
    assert role.mention.lemma == "auto", "uzel `Filipův_auto` vzniknout NESMÍ"


def test_a_bare_noun_carries_no_possessive() -> None:
    """PROTIPŘÍKLAD: „Auto stojí venku." žádný takový záznam nemá —
    tvar zmínky je holý a role na odkaz nečeká."""
    reading = Reading(
        tokens=(
            _token(1, "Auto", "auto", "NOUN", 2, "nsubj", Case="Nom", Gender="Neut", Number="Sing"),
            _token(2, "stojí", "stát", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
            _token(3, "venku", "venku", "ADV", 2, "advmod"),
            _token(4, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    role = next(r for r in predication.roles if r.name == ROLE_SUBJECT)
    assert role.mention.form == "Auto"
    assert role.awaiting == ""


def test_a_lost_head_is_reported_with_what_was_composed_into_it() -> None:
    """ZTRACENÝ ČLEN SE HLÁSÍ I S TÍM, CO SE DO NĚJ SLOŽILO *(B‑28)*.
    Od W‑78 se přívlastek skládá i pod ztracenou hlavou — jenže když je
    ztracená i ta hlava, nikde se to jméno neobjevilo a o 277 slovech
    korpusu přestalo hlášení mluvit ÚPLNĚ. Ubrat otázku je pokrok jen
    tehdy, když se ten materiál ohlásí jinde."""
    from core_semantics.cascade import _dropped_note

    reading = Reading(
        tokens=(
            _token(1, "Rizika", "riziko", "NOUN", 6, "nsubj", Case="Nom", Gender="Neut", Number="Plur"),
            _token(2, "s", "s", "ADP", 4, "case", AdpType="Prep", Case="Ins"),
            _token(3, "domácími", "domácí", "ADJ", 4, "amod", Case="Ins", Degree="Pos", Gender="Neut", Number="Plur"),
            _token(4, "zvířaty", "zvíře", "NOUN", 1, "nmod", Case="Ins", Gender="Neut", Number="Plur"),
            _token(6, "rostou", "růst", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(7, ".", ".", "PUNCT", 6, "punct"),
        ),
        provenance="test",
    )
    from dataclasses import replace as _replace_field

    from core_semantics.cascade import genitive_attributes, unaccounted_note

    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication

    # PO W‑84 UŽ TO NENÍ ZTRÁTA, JE TO PŘÍVLASTEK — „zvířaty" visí pod
    # „Rizika", které je ve čtení. Tvrzení testu se tím ale nemění:
    # UBRAT OTÁZKU JE POKROK JEN TEHDY, KDYŽ SE MATERIÁL OHLÁSÍ JINDE,
    # a tady se hlásí ve dvou kanálech najednou.
    assert [g for _, g, _, _, _ in genitive_attributes(reading, predication)] == [
        "zvíře"
    ], "jméno pod jménem je vztah vedle věty"
    ucet = unaccounted_note(reading, predication)
    assert ucet is not None and "domácími" in ucet, (
        "co se do přívlastku nesložilo, musí být vidět v účtu — jinak "
        "o 277 slovech korpusu přestane hlášení mluvit úplně"
    )

    # A PŮVODNÍ TVRZENÍ SE MĚŘÍ DÁL, na téže větě: jakmile hlava ve
    # čtení není, přívlastek nevzniká, ztráta se vrátí — a musí přijít
    # se složeným jménem, ne jen s holou hlavou.
    bez_hlavy = _replace_field(predication, roles=())
    note = _dropped_note(reading, bez_hlavy)
    assert note is not None
    assert "domácími zvířaty" in note, "složené jméno musí být v hlášení vidět"


def test_a_word_with_no_role_is_named_not_silenced() -> None:
    """JEDNO MÍSTO MÍSTO ČTVRTÉ ZÁPLATY *(B‑28)*. Materiál z věty mizel
    mlčky postupně na třech místech a pokaždé se to opravovalo tam, kde
    se to zrovna našlo. Účet říká, co systém VIDĚL — „jejich" roli
    nedostane a ptát se na ni nelze, ale zamlčet se nesmí."""
    from core_semantics.cascade import unaccounted_note

    reading = Reading(
        tokens=(
            _token(1, "Chov", "chov", "NOUN", 3, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "jejich", "jeho", "DET", 4, "det", Poss="Yes", PronType="Prs"),
            _token(3, "ovlivňuje", "ovlivňovat", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
            _token(4, "zdraví", "zdraví", "NOUN", 3, "obj", Case="Acc", Gender="Neut", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    note = unaccounted_note(reading, predication)
    assert note is not None and "„jejich“" in note


def test_a_word_that_is_in_the_reading_is_not_reported_twice() -> None:
    """PROTIPŘÍKLAD: co ve čtení JE, do účtu nepatří — dvě hlášky
    o jednom slově jsou horší než jedna (W‑20)."""
    from core_semantics.cascade import unaccounted_tokens

    reading = Reading(
        tokens=(
            _token(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Sing"),
            _token(2, "přišel", "přijít", "VERB", 0, "root", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(3, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    assert unaccounted_tokens(reading, predication) == ()


def test_the_ledger_and_the_report_read_the_same_list() -> None:
    """ÚČET SE STAVÍ NA TOM, CO SE OPRAVDU VYPÍŠE *(B‑28)*. Postavený na
    `dropped_tokens` prohlásil 233 slov za zaznamenaná, ačkoli je nikdo
    nevypsal: hlášení z toho seznamu ještě odečítá genitivní přívlastek
    a druhou větu. Dva seznamy by se rozešly přesně tam, kde to není
    vidět."""
    from core_semantics.cascade import _dropped_note, _reported_lost

    reading = Reading(
        tokens=(
            _token(1, "psi", "pes", "NOUN", 2, "nsubj", Case="Nom", Gender="Masc", Number="Plur"),
            _token(2, "štěkají", "štěkat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(3, "návštěv", "návštěva", "NOUN", 1, "nmod", Case="Gen", Gender="Fem", Number="Plur"),
            _token(4, ".", ".", "PUNCT", 2, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    note = _dropped_note(reading, predication)
    hlasene = {t.form for t in _reported_lost(reading, predication)}
    if note is None:
        assert not hlasene
    else:
        assert all(form in note for form in hlasene)


def test_a_word_the_parser_could_not_classify_is_still_material() -> None:
    """ÚČET SE PTÁ NA DOPLNĚK ZNAČEK, NE NA VÝČET SLOVNÍCH DRUHŮ
    *(B‑28)*. Výčet materiálu tu jednou byl a minul 30 slov: „aloe
    vera" je `X` (rozbor ho nezařadil) a „μ" je `SYM` — oboje ve větě
    STOJÍ. Dvanáctá instance rodiny W‑32 … W‑81: kategorie s variantami
    porovnaná VÝČTEM."""
    from core_semantics.cascade import unaccounted_tokens

    reading = Reading(
        tokens=(
            _token(1, "Zahrnují", "zahrnovat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(2, "begonie", "begonie", "NOUN", 1, "obj", Case="Acc", Gender="Fem", Number="Plur"),
            _token(3, "a", "a", "CCONJ", 4, "cc"),
            _token(4, "aloe", "aloe", "X", 2, "conj"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    zbyle = {t.form for t in unaccounted_tokens(reading, predication)}
    assert "aloe" in zbyle, "co rozbor nezařadil, není proto beze stopy"
    assert "a" not in zbyle, "spojka je značka, ne materiál"


def _genitive_chain() -> Reading:
    """„Vyžadují péči lékaře pacienta." — genitiv POD genitivem: `lékaře`
    visí pod `péči` (role) a `pacienta` pod `lékaře`, tedy pod členem,
    který sám ve čtení NENÍ."""
    return Reading(
        tokens=(
            _token(1, "Vyžadují", "vyžadovat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(2, "péči", "péče", "NOUN", 1, "obj", Case="Acc", Gender="Fem", Number="Sing"),
            _token(3, "lékaře", "lékař", "NOUN", 2, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(4, "pacienta", "pacient", "NOUN", 3, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(5, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )


def test_a_genitive_under_a_genitive_is_reported_too() -> None:
    """ŘETĚZ, NE JEDNA HRANA *(W‑80)*. `pacienta` visí pod `lékaře`, tedy
    pod členem, který ve čtení NENÍ — a dokud se ptalo jen rolí, zůstal
    venku a žádná odpověď se k němu nedostala, protože jeho hlava byla
    taky venku. Změřeno v #140: 80 % zbylých jmenných slov visí pod
    členem, který je sám venku."""
    from core_semantics.cascade import genitive_attributes

    reading = _genitive_chain()
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    hlavy = {genitiv for _, genitiv, _, _, _ in genitive_attributes(reading, predication)}
    assert "lékař" in hlavy, "první patro se hlásilo už dřív"
    assert "pacient" in hlavy, "druhé patro se musí ohlásit taky"


def test_the_chain_stops_at_a_clause() -> None:
    """REKURZE SE ZASTAVÍ NA HRANICI VĚTY *(W‑70)*. Vtáhnout členy
    vedlejší věty znamená tvrdit, že jsou účastníky téhle — hranice je
    ve STAVBĚ: přidávají se jen hlavy spojené `nmod` s HOLÝM genitivem,
    a klauzální hrana taková není."""
    from core_semantics.cascade import genitive_attributes

    reading = Reading(
        tokens=(
            _token(1, "Vyžadují", "vyžadovat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(2, "péči", "péče", "NOUN", 1, "obj", Case="Acc", Gender="Fem", Number="Sing"),
            _token(3, "kterou", "který", "PRON", 4, "obj", Case="Acc", Gender="Fem", Number="Sing", PronType="Rel"),
            _token(4, "doporučil", "doporučit", "VERB", 2, "acl:relcl", Gender="Masc", Number="Sing", Polarity="Pos"),
            _token(5, "lékaře", "lékař", "NOUN", 4, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(6, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    hlavy = {genitiv for _, genitiv, _, _, _ in genitive_attributes(reading, predication)}
    assert "lékař" not in hlavy, "přes vedlejší větu se řetěz nepřenese"


def _attribute_with_two_members() -> Reading:
    """„Vyžadují péči lékaře a pacienta." — dva genitivy pod jednou
    hlavou."""
    return Reading(
        tokens=(
            _token(1, "Vyžadují", "vyžadovat", "VERB", 0, "root", Number="Plur", Polarity="Pos"),
            _token(2, "péči", "péče", "NOUN", 1, "obj", Case="Acc", Gender="Fem", Number="Sing"),
            _token(3, "lékaře", "lékař", "NOUN", 2, "nmod", Case="Gen", Gender="Masc", Number="Sing"),
            _token(4, "a", "a", "CCONJ", 5, "cc"),
            _token(5, "pacienta", "pacient", "NOUN", 3, "conj", Case="Gen", Gender="Masc", Number="Sing"),
            _token(6, ".", ".", "PUNCT", 1, "punct"),
        ),
        provenance="test",
    )


def test_the_second_member_of_an_attribute_is_an_attribute() -> None:
    """DRUHÝ ČLEN PŘÍVLASTKU NENÍ ČLEN VĚTY *(W‑81)*. „…péči lékaře
    a **pacienta**" se ptalo „jakou roli hraje „pacienta“?" — otázka,
    na kterou pravdivá odpověď NEEXISTUJE, protože `pacienta` účastník
    děje není; je to druhé jméno TÉHOŽ vztahu vedle věty (W‑75)."""
    from core_semantics.cascade import _reported_lost, genitive_attributes

    reading = _attribute_with_two_members()
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    privlastky = {g for _, g, _, _, _ in genitive_attributes(reading, predication)}
    assert privlastky == {"lékař", "pacient"}
    assert all(
        t.form != "pacienta" for t in _reported_lost(reading, predication)
    ), "druhý člen se nesmí ptát jako role"


def test_an_attribute_does_not_ask_about_sharing() -> None:
    """NEPTÁ SE NA SDÍLENÍ, A JE TO ROZHODNUTÍ S DŮVODEM *(W‑81)*.
    Otázka „o každém zvlášť, nebo dohromady?" (W‑73) se klade u ROLE,
    tedy u MÍSTA VE TVRZENÍ, kde odpověď mění, co se zapíše. Přívlastek
    ale tvrzení ještě NENÍ — čeká na jméno role a teprve tou odpovědí
    se z něj vztah stane; ptát se na rozdělení něčeho, co nikde
    nestojí, je táž past jako W‑75."""
    reading = _attribute_with_two_members()
    predication = cascade(reading, tiers=HARD_TIERS).survivors[0].predication
    assert predication.pending_share == ()
