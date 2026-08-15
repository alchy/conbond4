"""Akceptační sada — `XAIPresenter` (§ 8).

Dvě vlastnosti, které se testují strojově, protože na nich stojí I‑14:
render vzniká výhradně z kanonického důkazu, a chybějící šablona je
hlasitá chyba.
"""

from __future__ import annotations

import json

import pytest

from core_semantics.ast import (
    Entity,
    Group,
    QueryStatus,
    member_of,
    subset_of,
)
from core_semantics.engine import Engine
from core_semantics.presenter import (
    CZECH_PROFILE,
    AuditReport,
    MissingTemplate,
    TemplateProfile,
    XAIPresenter,
)
from core_semantics.storage import KnowledgeBase


def _dialog_c() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.attach(subset_of(Group("spisovatel"), Group("člověk")))
    kb.add_disjoint(Group("stroj"), Group("člověk"))
    kb.attach(subset_of(Group("parní_stroj"), Group("stroj")))
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    return kb


def test_report_is_rendered_from_the_canonical_proof() -> None:
    kb = _dialog_c()
    question = member_of(Entity("e17"), Group("parní_stroj"))
    result = Engine(kb).ask(question)
    report = XAIPresenter(kb).render_audit_report(question, result)

    assert report.status is QueryStatus.PROVEN_FALSE
    assert report.verdict == "NE"
    # `verify` běží uvnitř renderu; tady se kontroluje i explicitně.
    assert result.proof is not None
    report.verify(result.proof)
    assert set(report.cited) == set(result.proof.leaves()) | set(report.origins), (
        "citace jsou listy důkazu PLUS věty, ze kterých odvozené výroky "
        "vznikly (W‑24) — nic víc a nic míň"
    )


def test_every_cited_statement_comes_from_the_base() -> None:
    kb = _dialog_c()
    question = member_of(Entity("e17"), Group("parní_stroj"))
    report = XAIPresenter(kb).render_audit_report(question, Engine(kb).ask(question))
    for sid in report.cited:
        statement, active, _ = kb.inspect(sid)
        assert active
        assert statement.id == sid


def test_missing_template_is_loud() -> None:
    """Tichý fallback na syrová id by vydal za vysvětlení něco, co
    vysvětlení není."""
    crippled = dict(CZECH_PROFILE)
    crippled["node"] = {
        key: value
        for key, value in CZECH_PROFILE["node"].items()
        if key != "closure:member̄*"
    }
    profile = TemplateProfile.from_mapping(crippled)

    kb = _dialog_c()
    question = member_of(Entity("e17"), Group("parní_stroj"))
    result = Engine(kb).ask(question)
    with pytest.raises(MissingTemplate, match="member̄"):
        XAIPresenter(kb, profile).render_audit_report(question, result)


def test_profile_without_a_section_is_rejected() -> None:
    with pytest.raises(MissingTemplate):
        TemplateProfile.from_mapping({"verdict": {}, "node": {}})


def test_conflict_renders_both_trees() -> None:
    kb = _dialog_c()
    kb.attach(member_of(Entity("e17"), Group("parní_stroj")))
    question = member_of(Entity("e17"), Group("parní_stroj"))
    result = Engine(kb).ask(question)
    report = XAIPresenter(kb).render_audit_report(question, result)

    assert report.status is QueryStatus.CONFLICT
    assert report.conflict is not None
    positive, negative = report.conflict
    assert positive and negative
    markdown = XAIPresenter(kb).to_markdown(report)
    assert "Důkaz pro" in markdown and "Důkaz proti" in markdown


def test_unknown_renders_the_gap_not_an_invented_reason() -> None:
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("e17"), Group("spisovatel")))
    question = member_of(Entity("e17"), Group("stroj"))
    result = Engine(kb).ask(question)
    report = XAIPresenter(kb).render_audit_report(question, result)

    assert report.status is QueryStatus.UNKNOWN
    assert report.reason == ()
    assert report.cited == ()
    assert report.gap and "chybí vědět" in report.gap[0]


def test_json_export_round_trips() -> None:
    kb = _dialog_c()
    question = member_of(Entity("e17"), Group("parní_stroj"))
    report = XAIPresenter(kb).render_audit_report(question, Engine(kb).ask(question))
    payload = json.loads(report.to_json())
    assert payload["status"] == "N"
    assert payload["cited"] == list(report.cited)
    assert payload["reason"][0]["depth"] == 0


def test_scope_is_carried_into_the_report() -> None:
    """Připraveno pro `closed_context` (§ 12): závěr z uzavřeného světa
    musí mít přiznané hranice a nesmí vystupovat jako holý fakt."""
    kb = _dialog_c()
    question = member_of(Entity("e17"), Group("parní_stroj"))
    report = XAIPresenter(kb).render_audit_report(
        question, Engine(kb).ask(question), scope=("platí v kontextu: dialog #1",)
    )
    assert "dialog #1" in XAIPresenter(kb).to_markdown(report)
    assert report.to_dict()["scope"] == ["platí v kontextu: dialog #1"]


# --------------------------------------------------------------------------
# Důkaz musí dosáhnout na větu, kterou člověk řekl — W‑24
# --------------------------------------------------------------------------
#
# Člověk řekne „Vrabec není savec." a v odpovědi vidí „pravidlo p0001:
# ¬member(…) <- …" — svoji větu tam nenajde, a ještě je useknutá
# mnohotečkou. Provenience je přitom v bázi (`p0001.derived_from ==
# s0001`), prezentér ji jen nepoužil.
#
# NEVYMÝŠLÍ SE NOVÝ DŮKAZ. Strom zůstává, mění se to, co se z něj
# renderuje — jinak by to bylo vysvětlení, které si přidává (I‑14).


def _exclusion() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.add_disjoint(Group("vrabec"), Group("savec"))
    kb.attach(member_of(Entity("Čimčara"), Group("vrabec")))
    return kb


def _report() -> AuditReport:
    kb = _exclusion()
    question = member_of(Entity("Čimčara"), Group("savec"))
    return XAIPresenter(kb).render_audit_report(question, Engine(kb).ask(question))


def test_the_answer_reaches_the_sentence_the_person_said() -> None:
    """JÁDRO W‑24. Bez toho končí odůvodnění na `p0001`, což je výrok,
    který člověk nikdy nevyslovil."""
    report = _report()
    assert report.status is QueryStatus.PROVEN_FALSE
    assert any(
        "disjoint(a:·vrabec, b:·savec)" in line.text for line in report.reason
    ), [line.text for line in report.reason]


def test_the_origin_is_cited_not_just_printed() -> None:
    """Vypsat a necitovat by znamenalo, že `cited` pořád tvrdí, že
    odpověď stojí jen na odvozeném pravidle."""
    report = _report()
    kb = _exclusion()
    origin = kb.inspect("p0001")[0].derived_from
    assert origin is not None
    assert origin in report.cited


def test_the_expansion_is_one_hop_not_a_recursion() -> None:
    """`derived_from` je řetěz o JEDNOM článku. Hlubší cesta by z citace
    udělala výpis půlky báze."""
    report = _report()
    assert len(report.origins) == 1


def test_the_rule_body_is_not_truncated() -> None:
    """`<- …` po člověku chtělo, aby si domyslel, ZA JAKÝCH PODMÍNEK to
    pravidlo platí — a u expanze oddělenosti je právě tělo tím, co
    spojuje odpověď s jeho větou."""
    report = _report()
    rule_lines = [line.text for line in report.reason if "pravidlo" in line.text]
    assert rule_lines
    assert all("…" not in line for line in rule_lines), rule_lines
    assert any("member(elem:x, group:·vrabec)" in line for line in rule_lines)


def test_a_fact_without_an_origin_is_unchanged() -> None:
    """Potlačení je ÚZKÉ: výrok, který člověk řekl přímo, žádný původ
    nemá a nic se k němu nepřidává."""
    kb = KnowledgeBase()
    kb.attach(member_of(Entity("Mourek"), Group("kočka")))
    question = member_of(Entity("Mourek"), Group("kočka"))
    report = XAIPresenter(kb).render_audit_report(question, Engine(kb).ask(question))
    assert report.origins == ()
    assert not any("plyne z toho" in line.text for line in report.reason)
