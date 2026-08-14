"""UD podtypy závislostí — N‑1.

Kaskáda porovnávala `deprel` na přesnou shodu, takže byla slepá na
`obl:arg`, `nsubj:pass`, `nmod:poss` a spol. Token propadl a skončil
jako `[ZAHOZENO]`; u podmětu rovnou jako nečitelná věta. **Celý trpný
rod byl pro systém neviditelný** a s ním všechny předložkové předměty.

Oprava rozděluje dvě věci, které splývaly:

* **viditelnost** — je ten token kandidát na roli? → podle ZÁKLADU
* **pojmenování** — jakou rolí se stane? → podle CELÉHO deprelu

Past, kvůli které to nejde udělat jen tím prvním: **`nsubj:pass` NENÍ
`nsubj`.** V „Auto bylo koupeno Filipem" je `auto` to KUPOVANÉ. Kdyby
se podtyp zahodil, systém by přiřadil „kdo" tomu, kdo nic nedělá — a to
je horší než dnešní odmítnutí, protože dnes aspoň řekne, že neví.
"""

from __future__ import annotations

from core_semantics.cascade import (
    ROLE_SUBJECT,
    base_deprel,
    cascade,
    dropped_tokens,
    generate,
    surface_role,
)
from core_semantics.lexicon import Mood, czech_seed
from core_semantics.oracle import Reading, Token

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


def reading(*tokens: Token) -> Reading:
    return Reading(tokens=tokens, provenance=STAMP)


#: „Petr věří v úspěch." — předložkový PŘEDMĚT, tedy `obl:arg`.
BELIEVES = reading(
    tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
    tok(2, "věří", "věřit", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
    tok(3, "v", "v", "ADP", 4, "case", Case="Acc"),
    tok(4, "úspěch", "úspěch", "NOUN", 2, "obl:arg", Case="Acc", Number="Sing"),
    tok(5, ".", ".", "PUNCT", 2, "punct"),
)

#: „Auto bylo koupeno Filipem." — trpný rod: `nsubj:pass` + `obl:arg`.
BOUGHT = reading(
    tok(1, "Auto", "auto", "NOUN", 3, "nsubj:pass", Case="Nom", Number="Sing"),
    tok(2, "bylo", "být", "AUX", 3, "aux:pass", Number="Sing"),
    tok(3, "koupeno", "koupený", "ADJ", 0, "root", Case="Nom", Number="Sing"),
    tok(4, "Filipem", "Filip", "PROPN", 3, "obl:arg", Case="Ins", Number="Sing"),
    tok(5, ".", ".", "PUNCT", 3, "punct"),
)

#: „Lék se podává pacientům." — zvratná částice `expl:pv`.
GIVEN = reading(
    tok(1, "Lék", "lék", "NOUN", 3, "nsubj:pass", Case="Nom", Number="Sing"),
    tok(2, "se", "se", "PRON", 3, "expl:pv"),
    tok(3, "podává", "podávat", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
    tok(4, "pacientům", "pacient", "NOUN", 3, "obl:arg", Case="Dat", Number="Plur"),
    tok(5, ".", ".", "PUNCT", 3, "punct"),
)


# --------------------------------------------------------------------------
# Viditelnost
# --------------------------------------------------------------------------


def test_base_strips_the_subtype_and_nothing_else() -> None:
    assert base_deprel("obl:arg") == "obl"
    assert base_deprel("nsubj:pass") == "nsubj"
    assert base_deprel("obl") == "obl"
    assert base_deprel("") == ""


def test_a_subtyped_argument_is_no_longer_dropped() -> None:
    """Dřív `[ZAHOZENO: „úspěch" (obl:arg)]`, protože kaskáda viděla jen
    přesné `obl`. Jednořádková příčina s velkým dosahem."""
    verdict = cascade(BELIEVES)
    assert verdict.decided is not None
    assert dropped_tokens(BELIEVES, verdict.decided.predication) == ()
    assert verdict.decided.predication.role("v+Acc:arg") is not None


def test_the_passive_is_readable_at_all() -> None:
    """Celý trpný rod byl neviditelný — `nsubj:pass` propadl a věta
    skončila jako „NEVÍM, jak to čtu"."""
    verdict = cascade(BOUGHT)
    assert verdict.decided is not None
    names = {r.name for r in verdict.decided.predication.roles}
    assert "nsubj:pass" in names
    assert "Ins:arg" in names


# --------------------------------------------------------------------------
# Past: podtyp se NESMÍ zahodit
# --------------------------------------------------------------------------


def test_a_passive_subject_never_becomes_the_doer() -> None:
    """JÁDRO PASTI. `nsubj:pass` se nesmí stát `kdo`.

    „Auto bylo koupeno Filipem" — kdyby se podtyp zahodil, systém by
    tvrdil, že auto kupovalo. Tichá záměna konatele je horší než
    odmítnutí, protože odmítnutí je vidět."""
    verdict = cascade(BOUGHT)
    assert verdict.decided is not None
    assert verdict.decided.predication.role(ROLE_SUBJECT) is None, (
        "trpný podmět není konatel a nesmí dostat roli `kdo`"
    )


def test_a_subtyped_core_member_does_not_join_the_swap() -> None:
    """Záměna kdo/co je pro HOLÉ jádrové členy. Permutovat trpný podmět
    by znamenalo tvrdit, že je zaměnitelný s konatelem."""
    assert len(generate(BOUGHT)) == 1


def test_the_subtype_survives_in_the_surface_role_name() -> None:
    """MOJE CHYBA, kterou tenhle rozdíl opravil.

    Naučil jsem systém `v+Acc → kdy` („v pondělí"), jenže bez podtypu se
    tak jmenovalo i „věří v úspěch" — a z předmětu se stal časový údaj.
    Rozbor ta dvě užití ROZLIŠUJE (`obl` × `obl:arg`); zahazoval jsem to
    já.
    """
    argument = surface_role(BELIEVES.tokens[3], BELIEVES)
    assert argument == "v+Acc:arg"

    adjunct = reading(
        tok(1, "jel", "jet", "VERB", 0, "root", Number="Sing"),
        tok(2, "v", "v", "ADP", 3, "case", Case="Acc"),
        tok(3, "pondělí", "pondělí", "NOUN", 1, "obl", Case="Acc", Number="Sing"),
    )
    assert surface_role(adjunct.tokens[2], adjunct) == "v+Acc"


def test_the_temporal_pattern_does_not_leak_onto_an_argument() -> None:
    """Totéž měřeno přes celou kaskádu: `v pondělí` je čas, `v úspěch` ne."""
    from core_semantics.cascade import HARD_TIERS, quantifier_tier, role_mapping_tier

    lexicon = czech_seed()
    tiers = (*HARD_TIERS, role_mapping_tier(lexicon), quantifier_tier(lexicon))
    verdict = cascade(BELIEVES, tiers=tiers)
    assert verdict.decided is not None
    assert verdict.decided.predication.role("kdy") is None, (
        "„věří v úspěch“ není časový údaj"
    )


# --------------------------------------------------------------------------
# Co ztráta NENÍ
# --------------------------------------------------------------------------


def test_a_reflexive_particle_is_not_reported_as_a_loss() -> None:
    """„se" v „podává se" patří ke slovesu, ne do role. Hlásit ji jako
    ztracený člen by byl šum, ve kterém by zanikla ztráta skutečná."""
    verdict = cascade(GIVEN)
    assert verdict.decided is not None
    lost = {t.form for t in dropped_tokens(GIVEN, verdict.decided.predication)}
    assert "se" not in lost


def test_subtype_transcript_prints() -> None:
    from core_semantics.tests._console import echo

    echo("\n" + "=" * 72)
    echo("UD PODTYPY ZÁVISLOSTÍ — N‑1")
    echo("=" * 72)
    for label, source in (
        ("Petr věří v úspěch.", BELIEVES),
        ("Auto bylo koupeno Filipem.", BOUGHT),
        ("Lék se podává pacientům.", GIVEN),
    ):
        verdict = cascade(source, mood=Mood.ASSERTION)
        echo(f"\n» {label}")
        for line in verdict.render():
            echo(f"   {line}")
    echo("=" * 72)


# --------------------------------------------------------------------------
# Složený přísudek — G‑1a
# --------------------------------------------------------------------------


def modal(*extra: Token) -> Reading:
    """«Jan nesmí dostat penicilin.» — modální sloveso s infinitivem."""
    return reading(
        tok(1, "Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "nesmí", "smět", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
        tok(3, "dostat", "dostat", "VERB", 2, "xcomp", VerbForm="Inf"),
        *extra,
        tok(9, ".", ".", "PUNCT", 2, "punct"),
    )


ONE_OBJECT = modal(
    tok(4, "penicilin", "penicilin", "NOUN", 3, "obj", Case="Acc", Number="Sing"),
)

#: PROTIPŘÍKLAD z G‑1a: dva předměty na DVOU úrovních. Sloučením nesmí
#: vzniknout duplicitní role ani tichá ztráta členu.
TWO_OBJECTS = reading(
    tok(1, "Jan", "Jan", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
    tok(2, "nesmí", "smět", "VERB", 0, "root", Number="Sing", Polarity="Neg"),
    tok(3, "dát", "dát", "VERB", 2, "xcomp", VerbForm="Inf"),
    tok(4, "Petrovi", "Petr", "PROPN", 3, "obl:arg", Case="Dat", Number="Sing"),
    tok(5, "penicilin", "penicilin", "NOUN", 3, "obj", Case="Acc", Number="Sing"),
    tok(6, ".", ".", "PUNCT", 2, "punct"),
)


def test_a_modal_and_its_infinitive_are_one_predicate() -> None:
    """Třetí tvar přísudku vedle slovesa a spony.

    Že je to JEDEN děj, říká specifikace: doména farmaka (§ 6.12)
    modeluje závěr jako `smí_dostat(who, what)` se silnou negací, ne jako
    `smět` s vnořenou rolí. Modalita je součástí jména vztahu.
    """
    verdict = cascade(ONE_OBJECT)
    assert verdict.decided is not None
    predication = verdict.decided.predication
    assert predication.predicate == "smět_dostat", "obě lemmata musí zůstat"
    assert predication.negated is True, "modalita nese zápor"
    assert predication.role("co") is not None, "předmět visel pod infinitivem"


def test_the_infinitive_is_not_reported_as_a_lost_member() -> None:
    """Infinitiv NENÍ ztracený člen — jeho lemma je v predikátu. Hlásit
    ho by poslalo člověka pojmenovat roli něčemu, co roli mít nemá."""
    verdict = cascade(ONE_OBJECT)
    assert verdict.decided is not None
    assert dropped_tokens(ONE_OBJECT, verdict.decided.predication) == ()


def test_two_objects_on_two_levels_never_collide_or_vanish() -> None:
    """PROTIPŘÍKLAD z G‑1a, který musí projít.

    „Jan nesmí dát Petrovi penicilin." má předmět i nepřímý předmět, a
    každý na jiné úrovni stromu. Sloučení do jedné predikace je nesmí
    srazit do jednoho jména role ani o jeden z nich tiše připravit —
    buď dvě různá jména, nebo dotaz, nikdy tichá ztráta.
    """
    verdict = cascade(TWO_OBJECTS)
    assert verdict.decided is not None
    predication = verdict.decided.predication
    names = [r.name for r in predication.roles]
    assert len(names) == len(set(names)), "duplicitní role by čtení zabila"
    assert dropped_tokens(TWO_OBJECTS, predication) == (), "nic se neztratilo"
    lemmas = {r.mention.lemma for r in predication.roles}
    assert {"Jan", "Petr", "penicilin"} <= lemmas


# --------------------------------------------------------------------------
# Složený nominál — N‑2c
# --------------------------------------------------------------------------
#
# Protějšek složeného přísudku (G‑1a) na jmenné straně: „dopravní
# prostředek" je JEDEN POJEM, ne dvě věci.
#
# Skládá se v `generate`, tedy JEDNOU PRO VŠECHNY POZICE. Předtím to
# dělalo patro jádrových relací, takže se fráze složila ve jmenném
# přísudku a nikde jinde — a táž fráze pak mířila na RŮZNÉ UZLY podle
# toho, kde ve větě stála. Tichá nekonzistence identity je horší než
# chybějící schopnost: nedá se o ní poznat, že nastala.


def _copula(*attribute: Token) -> Reading:
    """«<X> je (dopravní) stavba.»"""
    return Reading(
        tokens=(
            tok(1, "Dálnice", "dálnice", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "je", "být", "AUX", 4, "cop", Number="Sing", Polarity="Pos"),
            *attribute,
            tok(4, "stavba", "stavba", "NOUN", 0, "root", Case="Nom", Number="Sing"),
            tok(5, ".", ".", "PUNCT", 4, "punct"),
        ),
        provenance=STAMP,
    )


ATTRIBUTE = tok(
    3, "dopravní", "dopravní", "ADJ", 4, "amod", Case="Nom", Degree="Pos", Number="Sing"
)

#: Táž fráze v OBLIKVNÍ pozici — jiné místo ve větě, týž pojem.
OBLIQUE = Reading(
    tokens=(
        tok(1, "Petr", "Petr", "PROPN", 2, "nsubj", Case="Nom", Number="Sing"),
        tok(2, "jel", "jet", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
        tok(3, "po", "po", "ADP", 5, "case", Case="Loc"),
        tok(4, "dlouhé", "dlouhý", "ADJ", 5, "amod", Case="Loc", Degree="Pos", Number="Sing"),
        tok(5, "dálnici", "dálnice", "NOUN", 2, "obl", Case="Loc", Number="Sing"),
        tok(6, ".", ".", "PUNCT", 2, "punct"),
    ),
    provenance=STAMP,
)

SUBJECT = Reading(
    tokens=(
        tok(1, "Dlouhá", "dlouhý", "ADJ", 2, "amod", Case="Nom", Degree="Pos", Number="Sing"),
        tok(2, "dálnice", "dálnice", "NOUN", 3, "nsubj", Case="Nom", Number="Sing"),
        tok(3, "vede", "vést", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
        tok(4, ".", ".", "PUNCT", 3, "punct"),
    ),
    provenance=STAMP,
)

POSSESSIVE = Reading(
    tokens=(
        tok(1, "Filipovo", "Filipův", "ADJ", 2, "amod", Case="Nom", Poss="Yes"),
        tok(2, "auto", "auto", "NOUN", 4, "nsubj", Case="Nom", Number="Sing"),
        tok(3, "je", "být", "AUX", 4, "cop", Number="Sing", Polarity="Pos"),
        tok(4, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
        tok(5, ".", ".", "PUNCT", 4, "punct"),
    ),
    provenance=STAMP,
)


def _read(reading: Reading) -> str:
    verdict = cascade(reading)
    assert verdict.decided is not None
    return str(verdict.decided.predication)


def test_an_attribute_composes_into_the_name_of_the_class() -> None:
    assert _read(_copula(ATTRIBUTE)) == "být(co:dopravní_stavba, kdo:dálnice)"


def test_without_the_attribute_the_name_is_the_bare_noun() -> None:
    """Kontrola, že se neskládá pokaždé — jinak by test výš neměřil nic."""
    assert _read(_copula()) == "být(co:stavba, kdo:dálnice)"


def test_the_same_phrase_points_at_the_same_node_in_any_position() -> None:
    """JÁDRO N‑2c. Kdyby se skládalo jen ve jmenném přísudku, mluvil by
    člověk o téže dálnici a systém by měl dva různé uzly — a nepoznal by
    to nikdo, protože obě věty by vypadaly přečteně."""
    assert "dlouhý_dálnice" in _read(OBLIQUE)
    assert "dlouhý_dálnice" in _read(SUBJECT)


def test_lemmata_not_surface_forms() -> None:
    """Proto to napříč pozicemi vůbec funguje: „dlouhá dálnice"
    a „po dlouhé dálnici" mají různé TVARY a táž LEMMATA. Je to
    identifikátor uzlu, ne text pro člověka."""
    assert "dlouhé_dálnici" not in _read(OBLIQUE)


def test_the_attribute_is_not_a_lost_member_once_composed() -> None:
    """Do významu se dostal, jen ne vlastní rolí — hlásit ho jako ztrátu
    by poslalo člověka pojmenovat roli něčemu, co roli mít nemá (N‑5)."""
    verdict = cascade(_copula(ATTRIBUTE))
    assert verdict.decided is not None
    assert verdict.lost == ()
    assert dropped_tokens(_copula(ATTRIBUTE), verdict.decided.predication) == ()


def test_a_possessive_attribute_is_not_composed() -> None:
    """PROTIPŘÍKLAD REVIEWERA (c). „Filipovo auto" NENÍ druh auta — je to
    vztah ke KONKRÉTNÍMU uzlu. Složit ho na `Filipův_auto` by z každého
    majitele udělalo novou třídu a hlavně by to UMLČELO otázku, kterou na
    přivlastnění systém právem klade."""
    verdict = cascade(POSSESSIVE)
    assert verdict.decided is not None
    assert "Filipův" not in str(verdict.decided.predication)
    assert verdict.lost == (("Filipovo", "nsubj>amod+Nom"),)


def test_a_predicative_adjective_is_not_composed() -> None:
    """PROTIPŘÍKLAD REVIEWERA (a). „To auto je modré." — přísudkové
    adjektivum není přívlastek, visí jako kořen, ne jako `amod`."""
    predicative = Reading(
        tokens=(
            tok(1, "Auto", "auto", "NOUN", 3, "nsubj", Case="Nom", Number="Sing"),
            tok(2, "je", "být", "AUX", 3, "cop", Number="Sing", Polarity="Pos"),
            tok(3, "modré", "modrý", "ADJ", 0, "root", Case="Nom", Number="Sing"),
            tok(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )
    assert _read(predicative) == "být(co:modrý, kdo:auto)"


def test_an_attribute_on_a_proper_name_is_not_composed() -> None:
    """Přívlastek na vlastním jméně by měnil identitu POJMENOVANÉHO uzlu,
    a to je jiná operace než pojmenovat třídu. Skládá se jen `NOUN`."""
    named = Reading(
        tokens=(
            tok(1, "starý", "starý", "ADJ", 2, "amod", Case="Nom", Degree="Pos", Number="Sing"),
            tok(2, "Petr", "Petr", "PROPN", 3, "nsubj", Case="Nom", Number="Sing"),
            tok(3, "spí", "spát", "VERB", 0, "root", Number="Sing", Polarity="Pos"),
            tok(4, ".", ".", "PUNCT", 3, "punct"),
        ),
        provenance=STAMP,
    )
    assert "starý_Petr" not in _read(named)
