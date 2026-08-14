"""Konzolové akceptační dialogy — fáze F0.6, § 6.12 zadání a § 10.

Každý test má **dvojí aserci** podle § 10: vyrenderované odpovědi a
výsledný program („diff kódu je diff naučeného"). A každý test
**bezpodmínečně vypíše celý transkript na stdout** — viditelné přes
`pytest -s`, i když test projde. Není to kosmetika: je to ochrana proti
tomu, aby dialogový test degradoval na porovnávání neprůhledných řetězců.

Tahy jsou **strukturované**, ne surový text: parser je vnější orákulum
(§ 5.1) a vrstvy V1–V3 ve F0 nejsou. `text` u tahu je popis pro člověka,
obsah nese formule.
"""

from __future__ import annotations

import io
import sys
from decimal import Decimal

from core_semantics.tests._console import echo

from core_semantics.ast import (
    Comparator,
    Entity,
    Group,
    Label,
    P_NAME,
    P_ROLE_EXISTS,
    Quantifier,
    QueryStatus,
    RelationInstance,
    Rule,
    Sort,
    Value,
    Variable,
    atom,
    group_diff,
    measure_of,
    member_of,
    role,
    subset_of,
)
from core_semantics.session import (
    Session,
    Turn,
    asks,
    declares_disjoint,
    asks_bound,
    asks_for,
    confirms,
    revokes,
    says,
)

FOR_ALL = Quantifier.FOR_ALL
EXISTS = Quantifier.EXISTS
SELF = Quantifier.SELF
V130 = Value("v130", "rychlost", Decimal(130), "km/h")


def _render(title: str, session: Session, *, footer: str = "") -> str:
    parts = [f"\n{'=' * 72}\n{title}\n{'=' * 72}", session.transcript()]
    if footer:
        parts.append(f"\n{footer}")
    parts.append(
        f"\n--- výsledný program ({len(session.program())} aktivních výroků) ---"
    )
    parts.extend(f"    {line}" for line in session.program())
    return "\n".join(parts)


def _print(title: str, session: Session, *, footer: str = "") -> None:
    """Bezpodmínečný výpis transkriptu (požadavek člověka).

    Přes `echo` z `conftest`, aby výpis neshodil sadu na konzoli, která
    češtinu neumí zakódovat — což je přesně režim `pytest -s`, kvůli
    kterému výpis existuje.
    """
    echo(_render(title, session, footer=footer))


# --------------------------------------------------------------------------
# Dialog A — chybějící můstek se nehádá, nabídne se k potvrzení
# --------------------------------------------------------------------------


def _bridge_rule() -> Rule:
    relation = Variable("R")
    road = Variable("P", expects=Sort.GROUP)
    limit = Variable("V")
    return Rule(
        id="p3",
        head=measure_of(relation, Comparator.LE, limit),
        body=(
            member_of(relation, Group("jezdit")),
            atom(
                P_ROLE_EXISTS,
                role("of", relation),
                role("name", Label("via")),
                role("filler", road, SELF),
            ),
            atom(
                "omezení",
                role("of", road, FOR_ALL),
                role("quantity", Label("rychlost")),
                role("limit", limit),
            ),
        ),
    )


def _dialog_a_turns() -> list[Turn]:
    question = "Jak rychle může jezdit auto po dálnici?"
    return [
        says("Auto je dopravní prostředek.", subset_of(Group("auto"), Group("DP"))),
        says(
            "Dopravní prostředek jezdí po dálnici.",
            atom(
                "jezdit",
                role("who", Group("DP"), FOR_ALL),
                role("via", Group("dálnice"), EXISTS),
            ),
        ),
        says(
            "Dálnice má omezenou rychlost na 130 km/h.",
            atom(
                "omezení",
                role("of", Group("dálnice"), FOR_ALL),
                role("quantity", Label("rychlost")),
                role("limit", V130),
            ),
        ),
        asks_bound(
            question,
            RelationInstance("s0002"),
            "rychlost",
            bridge=_bridge_rule(),
        ),
        confirms("Ano."),
        asks_bound(question, RelationInstance("s0002"), "rychlost"),
    ]


def test_dialog_a_learns_the_bridge_and_changes_its_answer() -> None:
    session = Session()
    results = session.run(_dialog_a_turns())
    question = "Jak rychle může jezdit auto po dálnici?"
    cost = session.turns_to_learn(question)
    _print(
        "DIALOG A — můstek se nehádá, nabídne se k potvrzení",
        session,
        footer=f"*** Učitelnost (§ 10): od NEVÍM ke správné odpovědi {cost} tahy ***",
    )

    # 1) odpovědi
    assert results[3].status is QueryStatus.UNKNOWN
    assert results[3].offered is not None and results[3].offered.id == "p3"
    assert results[5].status is QueryStatus.PROVEN_TRUE
    assert "130" in "\n".join(results[5].lines)
    assert cost == 2

    # 2) výsledný program — pravidlo přibylo, a s proveniencí na tah
    program = session.program()
    assert any("p3" in line and "potvrzeno tahem 5" in line for line in program)


# --------------------------------------------------------------------------
# Dialog E — konflikt jako tah, oprava, konzistentní odpovědi
# --------------------------------------------------------------------------


def _dialog_e_turns() -> list[Turn]:
    """§ 6.12 dialog E — výjimka unese samotná algebra groups, bez
    nemonotónní logiky. Od F0.7 se zúžení píše `pták DIFF tučňák`, ne
    ruční deklarací pomocné skupiny."""
    flies_penguin = atom("létat", role("who", Group("tučňák"), FOR_ALL))
    flies_sparrow = atom("létat", role("who", Group("vrabec"), FOR_ALL))
    return [
        says("Ptáci létají.", atom("létat", role("who", Group("pták"), FOR_ALL))),
        says("Tučňák je pták.", subset_of(Group("tučňák"), Group("pták"))),
        asks("Létá tučňák?", flies_penguin),
        says(
            "Tučňák nelétá.",
            atom("létat", role("who", Group("tučňák"), FOR_ALL), negated=True),
        ),
        asks("Létá tučňák?", flies_penguin),
        revokes("Zúžit.", "s0001", "výjimka: tučňák"),
        says(
            "Létají ptáci kromě tučňáka.",
            atom(
                "létat",
                role("who", group_diff(Group("pták"), Group("tučňák")), FOR_ALL),
            ),
        ),
        says("Vrabec je pták.", subset_of(Group("vrabec"), Group("pták"))),
        asks("Létá vrabec?", flies_sparrow),
        declares_disjoint("Vrabec není tučňák.", Group("vrabec"), Group("tučňák")),
        asks("Létá vrabec?", flies_sparrow),
        asks("Létá tučňák?", flies_penguin),
    ]


def test_dialog_e_reports_conflict_and_stays_consistent_after_the_fix() -> None:
    session = Session()
    results = session.run(_dialog_e_turns())
    _print("DIALOG E — výjimka přes algebru, ne přes pomocnou skupinu", session)

    assert results[2].status is QueryStatus.PROVEN_TRUE  # zatím plyne z pravidla
    assert results[4].status is QueryStatus.CONFLICT  # tvrzení × odvození
    assert results[4].report is not None
    assert results[4].report.conflict is not None  # oba důkazy ukazatelné

    # Bez doložené oddělenosti je „létá vrabec?" poctivě NEVÍM: vrabec
    # v `possible(tučňák)` je, dokud to něco nevyvrátí (I‑21).
    assert results[8].status is QueryStatus.UNKNOWN
    assert results[10].status is QueryStatus.PROVEN_TRUE  # po doložení oddělenosti
    assert results[11].status is QueryStatus.PROVEN_FALSE  # tučňák ne, a bez sporu

    program = session.program()
    assert not any(line.startswith("s0001:") for line in program)  # odvoláno
    assert any("DIFF" in line for line in program)
    assert not any("létavý_pták" in line for line in program)


# --------------------------------------------------------------------------
# Dialog F — znalost se vrší napříč tahy, odpověď je syntéza
# --------------------------------------------------------------------------


def _dialog_f_turns() -> list[Turn]:
    car = Entity("a1")
    return [
        says("Filip má auto.", member_of(car, Group("auto"))),
        says(
            "…a to auto je jeho.",
            atom("mít", role("who", Entity("e_filip")), role("what", car)),
        ),
        says("Filipovo auto je modré.", member_of(car, Group("modrý"))),
        says(
            "Je to Ford.",
            atom(P_NAME, role("of", car), role("value", Label("Ford"))),
        ),
        asks_for(
            "Co má Filip?",
            atom("mít", role("who", Entity("e_filip")), role("what", Variable("X"))),
            "X",
        ),
    ]


def test_dialog_f_synthesises_the_accumulated_description() -> None:
    session = Session()
    results = session.run(_dialog_f_turns())
    _print("DIALOG F — vršení popisu a syntéza", session)

    answer = "\n".join(results[4].lines)
    assert results[4].status is QueryStatus.PROVEN_TRUE
    # Syntéza, ne echo jedné věty: členství + vlastnost + jméno pohromadě.
    for fragment in ("auto", "modrý", "Ford"):
        assert fragment in answer

    program = session.program()
    assert sum(1 for line in program if "a1" in line) >= 3


# --------------------------------------------------------------------------
# Replay — týž žurnál ⇒ týž program ⇒ tytéž odpovědi
# --------------------------------------------------------------------------


def test_transcript_survives_a_legacy_codepage_console() -> None:
    """B‑4: `pytest -s` na Windows psal do `cp1252` a padal na `ě`.

    Test simuluje takovou konzoli přímo, aby nález nebyl závislý na tom,
    v jakém prostředí sada zrovna běží: pod `-q` se chyba neprojevila,
    protože pytest stdout zachytává, takže testy byly zelené a funkce
    přitom nefungovala.
    """
    session = Session()
    session.run(_dialog_e_turns())
    text = _render("DIALOG E — kontrola kódování", session)
    assert "ů" in text or "ě" in text, "transkript musí obsahovat českou diakritiku"

    legacy = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="strict")
    original = sys.stdout
    sys.stdout = legacy
    try:
        echo(text)  # nesmí vyhodit UnicodeEncodeError
    finally:
        sys.stdout = original
    legacy.flush()
    echo("\n*** Kódování: transkript prošel i na cp1252 konzoli ***")


def test_replay_is_deterministic() -> None:
    """§ 10 a I‑4. „Teď" je pořadové číslo tahu, ne čas stroje."""
    journals = {
        "A": _dialog_a_turns(),
        "E": _dialog_e_turns(),
        "F": _dialog_f_turns(),
    }
    for name, journal in journals.items():
        first = Session.replay(journal)
        second = Session.replay(journal)
        assert first.program() == second.program(), f"program dialogu {name}"
        assert first.answers() == second.answers(), f"odpovědi dialogu {name}"
    echo(
        "\n*** Replay: 3 žurnály, shodný program i shodné odpovědi "
        "při opakovaném běhu ***"
    )
