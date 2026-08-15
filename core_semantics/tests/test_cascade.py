"""V2 — kaskáda výběru čtení (§ 5.2).

Testuje se hlavně to, co je na kaskádě podstatné: že **negeneruje jedno
čtení**, že každé patro umí říct PROČ, a že při nerozhodnutém stavu vrací
OTÁZKU, ne favorita (I‑1).

Rozbory jsou nahrané ručně, ne z běžící služby — hermetičnost je záměr.
"""

from __future__ import annotations

from core_semantics.cascade import (
    HARD_TIERS,
    dropped_tokens,
    role_question,
    surface_roles,
    ROLE_OBJECT,
    ROLE_SUBJECT,
    agreement_tier,
    feature_values,
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
    assert "v+Loc" in roles
    assert "co" not in roles


def test_the_role_stays_surface_and_is_asked_about() -> None:
    """Nepřevzít jmennou část NENÍ totéž co vědět, o co jde. `v+Loc` je
    místo i čas — rozhodnout to tady by byla táž tichá volba, jen o patro
    jinde."""
    verdict = cascade(_copula_with_preposition())
    assert verdict.decided is not None
    assert surface_roles(verdict.decided.predication) == ("v+Loc",)
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
    lexicon.teach_role("v+Loc", "kde", learned_from="test")
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
        assert _coordinated(subject, reading) is je_koordinace


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
