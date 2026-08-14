"""Pořadí literálů v těle není význam — A‑24.

**Problém.** Hornova klauzule je konjunkce a `A ∧ B` znamená totéž co
`B ∧ A`. Vyhodnocení ale váže proměnné zleva doprava, takže šest
permutací téhož pravidla dalo dvakrát `N` a čtyřikrát `EvaluationError`
— a `attach_rule` přijal všech šest. Chyba tedy přišla **až u dotazu**,
případně o mnoho tahů později a jen na některou otázku.

**Proč to nejde nechat být.** Pro dialogové učení je to nepřijatelné:
tvar, v jakém člověk pravidlo vysloví, by určoval jeho význam. „Kdo je
alergický na látku, nesmí dostat lék, který ji obsahuje" a táž věta
s přehozenými dvěma vedlejšími větami je JEDNO pravidlo.

**Kde se to opravuje.** U zápisu, ne v evaluátoru. Vyhodnocovací
strategie zůstává, jak byla; jen přestává být vlastností významu.

**Co se tím NESMÍ obejít.** Bezpečnost vázanosti a bezpečnost negace
jsou dvě různé podmínky (B‑2). Normalizace smí přeuspořádat, nesmí
prohlásit za bezpečné pravidlo, jehož proměnná je vázaná jen negovaným
literálem — negovaný literál neváže nic, a kdyby ho normalizace posunula
dopředu, kvantifikoval by přes celou otevřenou doménu.

**Zbytek téže třídy** *(G‑2)*. První verze se ptala jen na kořen fillera,
protože tak se ptá `_match_kernel`. Změřeno bylo něco jiného: `substitute`
do algebraických termů **sestupuje**, takže `h(a:X) ← subset(a AND X, b)`
zápisem prošlo a spadlo až u dotazu na neuzemněnou hlavu. Evaluátor je
v tomhle místě přísnější než zápis, ne volnější. Vázanost se proto hledá
rekurzivně — ale **algebraický term jako takový se nezakazuje**: rozhoduje
vázanost, ne tvar.
"""

from __future__ import annotations

from itertools import permutations
from typing import Callable

import pytest

from core_semantics.ast import (
    REQUIRES_BOUND,
    Atom,
    Entity,
    Group,
    Interval,
    Label,
    P_BEFORE,
    P_COMPLETE,
    P_CONTAINS,
    P_DISJOINT,
    P_MEMBER,
    P_NAME,
    P_SAME_AS,
    P_SUBSET,
    P_WITHIN,
    Place,
    Quantifier,
    QueryStatus,
    Sort,
    UnsafeRule,
    Variable,
    atom,
    before_of,
    complete_of,
    contains_of,
    disjoint_of,
    group_and,
    member_of,
    role,
    subset_of,
    within_of,
)
from core_semantics.engine import Engine, EvaluationError
from core_semantics.storage import KnowledgeBase

SELF = Quantifier.SELF


# --------------------------------------------------------------------------
# Doména: lékařská kontraindikace, tři literály v těle
# --------------------------------------------------------------------------

PATIENT = Variable("P")
MEDICINE = Variable("M", expects=Sort.GROUP)
ALLERGEN = Variable("L1", expects=Sort.GROUP)
INGREDIENT = Variable("L2", expects=Sort.GROUP)

ALLERGY = atom("alergie_na", role("who", PATIENT), role("what", ALLERGEN, SELF))
CONTAINS = atom(
    "obsahuje", role("what", MEDICINE, SELF), role("látka", INGREDIENT, SELF)
)
NARROWER = subset_of(INGREDIENT, ALLERGEN)

HEAD = atom(
    "smí_dostat",
    role("who", PATIENT),
    role("what", MEDICINE, SELF),
    negated=True,
)


def _facts() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(
        atom(
            "alergie_na",
            role("who", Entity("Jan")),
            role("what", Group("Penicilin"), SELF),
        )
    )
    kb.attach(subset_of(Group("Amoxicilin"), Group("Penicilin")))
    kb.attach(
        atom(
            "obsahuje",
            role("what", Group("Curam"), SELF),
            role("látka", Group("Amoxicilin"), SELF),
        )
    )
    return kb


def _with_body(body: tuple[Atom, ...]) -> KnowledgeBase:
    kb = _facts()
    kb.attach_rule(rule_id="R5", head=HEAD, body=body)
    return kb


QUERY = atom(
    "smí_dostat", role("who", Entity("Jan")), role("what", Group("Curam"), SELF)
)

PERMUTATIONS = list(permutations((ALLERGY, CONTAINS, NARROWER)))


def test_there_really_are_six_of_them() -> None:
    """Kdyby se `permutations` někdy změnily, zbytek souboru by tiše
    testoval míň, než tvrdí."""
    assert len(PERMUTATIONS) == 6


@pytest.mark.parametrize("body", PERMUTATIONS, ids=lambda b: "".join(
    a.predicate[0] for a in b
))
def test_every_permutation_answers_the_same(body: tuple[Atom, ...]) -> None:
    """JÁDRO A‑24. Dřív: dvě permutace daly `N`, čtyři spadly na
    `EvaluationError`. Teď dá `N` všech šest."""
    result = Engine(_with_body(body)).ask(QUERY)
    assert result.status is QueryStatus.PROVEN_FALSE


@pytest.mark.parametrize("body", PERMUTATIONS, ids=lambda b: "".join(
    a.predicate[0] for a in b
))
def test_every_permutation_normalises_to_the_same_body(
    body: tuple[Atom, ...],
) -> None:
    """Nestačí, aby každá permutace FUNGOVALA — musí dát TÝŽ normální
    tvar. Jinak by se šest zápisů téhož pravidla lišilo v důkazech, a to
    je kanonický důkaz (§ 7) pryč: na tutéž otázku by systém odpověděl
    stejně, ale zdůvodnil ji šesti různými způsoby."""
    rules = _with_body(body).view().rules
    assert len(rules) == 1
    assert rules[0].body == _with_body(PERMUTATIONS[0]).view().rules[0].body


def test_the_normal_form_is_actually_a_reordering() -> None:
    """Normalizace smí PŘEHÁZET, nesmí přidat, ubrat ani změnit literál —
    jinak by se z uspořádání stala tichá úprava významu."""
    rules = _with_body(PERMUTATIONS[0]).view().rules
    assert sorted(map(str, rules[0].body)) == sorted(
        map(str, (ALLERGY, CONTAINS, NARROWER))
    )


def test_the_proof_is_the_same_too() -> None:
    """Táž odpověď z jiného důkazu by pořád znamenala, že na pořadí
    záleží — jen o patro níž, tam, kde se to hůř pozná."""
    trees = {
        tuple(Engine(_with_body(body)).ask(QUERY).proof_tree)
        for body in PERMUTATIONS
    }
    assert len(trees) == 1


# --------------------------------------------------------------------------
# Když bezpečné pořadí neexistuje
# --------------------------------------------------------------------------


def test_an_unorderable_rule_is_refused_at_write_time() -> None:
    """`subset(X, Y)` s oběma stranami volnými nejde uspořádat nijak —
    žádný jiný literál je neváže. Dřív to prošlo zápisem a spadlo u
    dotazu; chyba u zápisu je tah dialogu, na který jde odpovědět, chyba
    u dotazu je překvapení."""
    x = Variable("X", expects=Sort.GROUP)
    y = Variable("Y", expects=Sort.GROUP)
    kb = _facts()
    with pytest.raises(UnsafeRule, match="bezpečné pořadí"):
        kb.attach_rule(
            rule_id="RX",
            head=atom("nesmysl", role("what", x, SELF)),
            body=(subset_of(x, y),),
        )


def test_the_refusal_names_the_literal_that_cannot_be_ordered() -> None:
    """Rozlišující chyba: „pravidlo je nebezpečné" se nedá opravit,
    „tenhle literál nemá čím navázat `Y`" ano."""
    x = Variable("X", expects=Sort.GROUP)
    y = Variable("Y", expects=Sort.GROUP)
    kb = _facts()
    with pytest.raises(UnsafeRule) as exc:
        kb.attach_rule(
            rule_id="RX",
            head=atom("nesmysl", role("what", x, SELF)),
            body=(subset_of(x, y),),
        )
    assert "subset" in str(exc.value)


def test_a_refused_rule_is_not_in_the_base() -> None:
    """Odmítnutí u zápisu, které by pravidlo přesto uložilo, by bylo horší
    než mlčení — báze by nesla něco, co se nedá vyhodnotit."""
    x = Variable("X", expects=Sort.GROUP)
    y = Variable("Y", expects=Sort.GROUP)
    kb = _facts()
    with pytest.raises(UnsafeRule):
        kb.attach_rule(
            rule_id="RX",
            head=atom("nesmysl", role("what", x, SELF)),
            body=(subset_of(x, y),),
        )
    assert kb.view().rules == ()


# --------------------------------------------------------------------------
# G‑2: vázanost se hledá i UVNITŘ algebraického termu
# --------------------------------------------------------------------------
#
# Zbytek téže třídy, který první verze A‑24 nepokryla. `_evaluable` se
# ptalo jen na kořen fillera, protože tak se ptá `_match_kernel`. Jenže
# `substitute` do algebraických termů SESTUPUJE, takže evaluátor je tu
# přísnější než zápis — přesně naopak, než jsem to popsal. Pravidlo
# `h(a:X) ← subset(a AND X, b)` prošlo zápisem a spadlo až u dotazu na
# „hlava zůstala neuzemněná po dosazení". Táž vada jako A‑24, jen
# přesunutá z pořadí literálů na proměnnou uvnitř termu.


def _algebraic_head(x: Variable) -> Atom:
    return atom("h", role("a", x, SELF))


def _algebraic_premise(x: Variable) -> Atom:
    return subset_of(group_and(Group("a"), x), Group("b"))


def _member_binding(x: Variable) -> Atom:
    return atom(
        P_MEMBER, role("elem", x, SELF), role("group", Group("g"), SELF)
    )


def _algebraic_base() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("a"), Group("b")))
    kb.attach(
        atom(P_MEMBER, role("elem", Group("a"), SELF), role("group", Group("g"), SELF))
    )
    return kb


def test_a_variable_hidden_in_an_algebraic_term_is_not_bound() -> None:
    """`a AND X` s volným `X` není vázané o nic víc než holé `X`.
    Odmítnout se to musí U ZÁPISU — dřív to prošlo a spadlo u dotazu."""
    kb = _algebraic_base()
    with pytest.raises(UnsafeRule, match="bezpečné pořadí"):
        kb.attach_rule(
            rule_id="alg",
            head=_algebraic_head(Variable("X", expects=Sort.GROUP)),
            body=(_algebraic_premise(Variable("X", expects=Sort.GROUP)),),
        )
    assert kb.view().rules == ()


def test_the_algebraic_rule_used_to_pass_the_write_and_die_at_the_query() -> None:
    """Doklad, že se opravila TA vada, a ne něco vedle: chyba, která dřív
    přišla od `_instantiate_head` při dotazu, teď přijde od `attach_rule`.
    Obě jsou `UnsafeRule`, takže kdyby se test ptal jen na typ, nepoznal
    by rozdíl — ptá se proto na FÁZI."""
    kb = _algebraic_base()
    x = Variable("X", expects=Sort.GROUP)
    with pytest.raises(UnsafeRule) as exc:
        kb.attach_rule(rule_id="alg", head=_algebraic_head(x), body=(_algebraic_premise(x),))
    assert "neuzemněná" not in str(exc.value)
    assert "bezpečné pořadí" in str(exc.value)


def test_a_bound_variable_in_an_algebraic_term_is_still_allowed() -> None:
    """PROTIPŘÍKLAD REVIEWERA. Kdyby oprava zakázala algebraický term
    v jádrovém literálu vůbec, odmítala by pravidla, která evaluátor
    spustí — táž rozešlost, jen otočená. `member` naváže `X`, `subset`
    přijde na řadu až po něm."""
    x = Variable("X", expects=Sort.GROUP)
    kb = _algebraic_base()
    kb.attach_rule(
        rule_id="ok",
        head=_algebraic_head(x),
        body=(_algebraic_premise(x), _member_binding(x)),
    )
    body = kb.view().rules[0].body
    assert [a.predicate for a in body] == ["member", "subset"]
    result = Engine(kb).ask(atom("h", role("a", Group("a"), SELF)))
    assert result.status is QueryStatus.PROVEN_TRUE


def test_the_bound_algebraic_rule_does_not_care_about_written_order() -> None:
    """A‑24 platí i tady: vazač smí být v zápisu až druhý."""
    x = Variable("X", expects=Sort.GROUP)
    kb = _algebraic_base()
    kb.attach_rule(
        rule_id="ok",
        head=_algebraic_head(x),
        body=(_member_binding(x), _algebraic_premise(x)),
    )
    assert [a.predicate for a in kb.view().rules[0].body] == ["member", "subset"]


# --------------------------------------------------------------------------
# B‑2: normalizace neobchází bezpečnost negace
# --------------------------------------------------------------------------


def test_normalisation_does_not_let_a_negated_literal_bind() -> None:
    """PROTIPŘÍKLAD REVIEWERA. `X` se vyskytuje jen v NEGOVANÉM literálu
    a v roli, kterou `member` potřebuje vázanou. Kdyby normalizace brala
    negovaný literál jako vazač, posunula by ho dopředu a pravidlo by
    „prošlo" — jenže `¬q(A, X)` neváže nic, jen se ptá, takže by se
    ptalo přes celou otevřenou doménu.

    Bezpečnost vázanosti a bezpečnost negace jsou dvě různé podmínky
    a jedna nesmí být obcházena tou druhou."""
    a = Variable("A")
    x = Variable("X")
    g = Variable("G", expects=Sort.GROUP)
    kb = _facts()
    with pytest.raises(UnsafeRule, match="bezpečné pořadí"):
        kb.attach_rule(
            rule_id="RN",
            head=atom("závěr", role("who", a)),
            body=(
                atom("premisa", role("who", a)),
                atom("q", role("who", a), role("co", x), negated=True),
                member_of(x, g),
            ),
        )


def test_a_negated_literal_still_may_not_bind_the_head() -> None:
    """B‑2 z prvních kol beze změny — kontrola hlavy běží PŘED
    normalizací a normalizace na ni nesahá."""
    a = Variable("A")
    with pytest.raises(UnsafeRule):
        KnowledgeBase().attach_rule(
            rule_id="RH",
            head=atom("závěr", role("who", a)),
            body=(atom("q", role("who", a), negated=True),),
        )


def test_a_negated_literal_is_ordered_after_its_binder() -> None:
    """Druhá půlka téhož: když proměnnou váže POZITIVNÍ literál,
    negovaný se za něj smí zařadit, i když byl v zápisu první. Odmítání
    všeho negovaného by bylo bezpečné a k ničemu."""
    a = Variable("A")
    kb = KnowledgeBase()
    kb.attach_rule(
        rule_id="ROK",
        head=atom("závěr", role("who", a)),
        body=(
            atom("q", role("who", a), negated=True),
            atom("premisa", role("who", a)),
        ),
    )
    body = kb.view().rules[0].body
    assert body[0].predicate == "premisa"
    assert body[1].is_negated


# --------------------------------------------------------------------------
# Zápis a vyhodnocení čtou TÝŽ seznam
# --------------------------------------------------------------------------

#: Jádrový predikát → role → term, který tam smí stát.
KERNEL_SHAPES: dict[str, tuple[tuple[str, object], ...]] = {
    P_MEMBER: (("elem", Entity("e")), ("group", Group("g"))),
    P_SUBSET: (("sub", Group("a")), ("sup", Group("b"))),
    P_CONTAINS: (("whole", Place("p")), ("part", Place("q"))),
    P_WITHIN: (("whole", Interval("i")), ("part", Interval("j"))),
    P_BEFORE: (("earlier", Interval("i")), ("later", Interval("j"))),
    P_SAME_AS: (("left", Entity("e")), ("right", Entity("f"))),
    P_DISJOINT: (("a", Group("a")), ("b", Group("b"))),
    P_COMPLETE: (("group", Group("g")),),
    P_NAME: (("of", Entity("e")), ("value", Label("Jan"))),
}

#: Konstruktory. `Callable[..., Atom]`, protože `complete` je jednomístný
#: a zbytek dvoumístný — jednotná signatura by tu byla lež.
BUILDERS: dict[str, Callable[..., Atom]] = {
    P_MEMBER: member_of,
    P_SUBSET: subset_of,
    P_CONTAINS: contains_of,
    P_WITHIN: within_of,
    P_BEFORE: before_of,
    # `same_as` a `name` se skládají přímo: `same_as_of` odmítá operand
    # jiného sortu a proměnná ŽÁDNÝ sort nemá, takže by konstruktor spadl
    # dřív, než se engine vůbec dostane ke slovu. Ta kontrola je správně
    # (identita napříč sorty by slila třídy ekvivalence) — jen tady měříme
    # něco jiného.
    P_SAME_AS: lambda left, right: atom(
        P_SAME_AS, role("left", left), role("right", right)
    ),
    P_DISJOINT: disjoint_of,
    P_COMPLETE: complete_of,
    P_NAME: lambda of, value: atom(P_NAME, role("of", of), role("value", value)),
}


def _kernel_atom(predicate: str, free: str) -> Atom:
    """Jádrový literál, v němž je role `free` volná proměnná."""
    args = [
        Variable(f"V_{name}", expects=None) if name == free else term
        for name, term in KERNEL_SHAPES[predicate]
    ]
    return BUILDERS[predicate](*args)


def test_the_shapes_cover_every_kernel_predicate() -> None:
    """Bez toho by seznam mohl zestárnout a test by dál hlásil zeleně."""
    assert set(KERNEL_SHAPES) == set(REQUIRES_BOUND)


@pytest.mark.parametrize("predicate", sorted(KERNEL_SHAPES))
def test_requires_bound_agrees_with_the_engine(predicate: str) -> None:
    """DOKLAD, ne tvrzení. `REQUIRES_BOUND` je seznam v `ast.py`, ale
    pravdu o tom, co jde enumerovat, má evaluátor. Kdyby se rozešly,
    zápis by pustil pravidlo, které vyhodnocení odmítne — a A‑24 by se
    vrátilo v jiném hávu.

    Měří se to CHOVÁNÍM: každá role se postupně nechá volná a ptá se, zda
    engine vyhodnocení odmítne. Zdrojový text se nečte, takže test
    nepřežije přepis evaluátoru omylem."""
    engine = Engine(_facts())
    for name, _ in KERNEL_SHAPES[predicate]:
        pattern = _kernel_atom(predicate, name)
        must_be_bound = name in REQUIRES_BOUND[predicate]
        if must_be_bound:
            with pytest.raises(EvaluationError):
                engine.solutions(pattern)
        else:
            engine.solutions(pattern)  # nesmí padnout — právě tohle se enumeruje


def test_rule_order_transcript_prints() -> None:
    from core_semantics.tests._console import echo

    echo("\n" + "=" * 72)
    echo("POŘADÍ LITERÁLŮ V TĚLE NENÍ VÝZNAM — A‑24")
    echo("=" * 72)
    echo("pravidlo: ¬smí_dostat(P, M) ← alergie_na(P,L1) ∧ obsahuje(M,L2)")
    echo("                              ∧ subset(L2, L1)")
    echo("otázka:   Smí Jan dostat Curam?")
    echo("")
    for body in PERMUTATIONS:
        written = " ∧ ".join(a.predicate for a in body)
        kb = _with_body(body)
        normal = " ∧ ".join(a.predicate for a in kb.view().rules[0].body)
        status = Engine(kb).ask(QUERY).status.value
        echo(f"» zapsáno {written}")
        echo(f"   normalizováno {normal}   → {status}")
    echo("")
    echo("Dřív: dvě permutace daly N, čtyři spadly na EvaluationError.")
    echo("A `attach_rule` přijal všech šest — chyba přišla až u dotazu.")
    echo("=" * 72)
