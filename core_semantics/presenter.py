"""Renderování odpovědi — Core Semantics 0.1, § 8.

> „Renderování z podgrafu do češtiny je samostatná úloha se šablonami
> odděleně od logiky (jazyk v profilech, ne v kódu) — a je to JEDINÝ
> výstupní kanál: co nejde vyrenderovat z reálné struktury, nesmí se říct."

Z toho plynou dvě pravidla, která tenhle modul vynucuje strojově:

1. **Renderuje se výhradně z kanonického důkazu** (I‑14). Každý řádek
   vysvětlení má oporu v uzlu `Proof`; `AuditReport.cited` obsahuje přesně
   ty id výroků, které důkaz použil, a `verify()` to kontroluje.
2. **Chybějící šablona je hlasitá chyba**, ne tichý fallback na syrová id.
   Vypsat lékaři `rule(R5)` je horší než render odmítnout.

Jazyk je **data**, ne kód: `TemplateProfile` se dá postavit z obyčejného
slovníku nebo načíst z JSON. `CZECH_PROFILE` níže je výchozí profil, ne
zadrátovaný text.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .ast import Atom, Proof, ProofKind, QueryResult, QueryStatus, Rule
from .storage import KnowledgeBase

_REFL = "/refl"


class MissingTemplate(RuntimeError):
    """Profil nezná uzel, který se v důkazu objevil.

    Selhat nahlas je záměr: tichý fallback by vydal za vysvětlení něco,
    co vysvětlení není (§ 8, I‑1)."""


#: Výchozí český profil. Je to DATA — dá se nahradit bez zásahu do kódu.
CZECH_PROFILE: dict[str, Any] = {
    "verdict": {
        "A": "ANO",
        "N": "NE",
        "U": "NEVÍM",
        "CONFLICT": "SPOR V BÁZI",
    },
    "section": {
        "question": "Otázka",
        "verdict": "Verdikt",
        "reason": "Důvod",
        "gap": "Co k tomu chybí",
        "conflict_positive": "Důkaz pro",
        "conflict_negative": "Důkaz proti",
        "cited": "Použité výroky",
    },
    "node": {
        "fact": "řekls: {statement}",
        "rule": "pravidlo {ref}: {statement}",
        "witness": "svědek: {ref}",
        "distribute": "shoda dotazu s faktem (distribuce rolí)",
        "constraint": "omezení {ref}",
        "countermodel": "protipříklad {ref}",
        "closure:subset*": "podtřída je i nadtřídou",
        "closure:member*": "prvek podtřídy je prvkem nadtřídy",
        "closure:member̄*": "co není v nadtřídě, není ani v podtřídě",
        "closure:complete*": "skupina je uzavřená, a tenhle prvek v ní není",
        "closure:contains*": "místo leží uvnitř jiného místa",
        "closure:within*": "interval leží uvnitř jiného intervalu",
        "closure:same_as*": "jde o týž uzel pod jiným jménem",
        "closure:subset*/alg": "podmnožina plyne ze stavby výrazu",
        "closure:member*/alg": "členství plyne ze stavby výrazu",
        "closure:disjoint": "tyhle skupiny se vzájemně vylučují",
        "closure:reify": "vztah rozložený na role",
        "closure:reflexive": "triviálně, jde o tutéž věc",
    },
}


@dataclass(frozen=True, slots=True)
class TemplateProfile:
    """Šablony mimo kód. `strict` se nedá vypnout — je to invariant, ne volba."""

    verdict: Mapping[str, str]
    section: Mapping[str, str]
    node: Mapping[str, str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "TemplateProfile":
        missing = {"verdict", "section", "node"} - set(data)
        if missing:
            raise MissingTemplate(
                f"profil nemá sekce {sorted(missing)}; renderer bez nich "
                f"nemůže nic vyrenderovat"
            )
        return cls(
            verdict=dict(data["verdict"]),
            section=dict(data["section"]),
            node=dict(data["node"]),
        )

    @classmethod
    def from_json(cls, path: Path) -> "TemplateProfile":
        return cls.from_mapping(json.loads(path.read_text(encoding="utf-8")))

    def for_verdict(self, status: QueryStatus) -> str:
        try:
            return self.verdict[status.value]
        except KeyError as exc:
            raise MissingTemplate(
                f"profil nezná verdikt {status.value!r}"
            ) from exc

    def for_section(self, key: str) -> str:
        try:
            return self.section[key]
        except KeyError as exc:
            raise MissingTemplate(f"profil nezná sekci {key!r}") from exc

    def for_node(self, proof: Proof) -> str:
        for key in _node_keys(proof):
            if key in self.node:
                return self.node[key]
        raise MissingTemplate(
            f"profil nezná uzel důkazu {proof.kind.value}({proof.ref!r}); "
            f"vypsat syrové id místo vysvětlení je horší než render odmítnout"
        )


def _node_keys(proof: Proof) -> list[str]:
    """Klíče od nejkonkrétnějšího po nejobecnější. Žádný z nich není
    „obecný fallback" — profil musí každý z nich vědomě definovat."""
    if proof.kind is not ProofKind.CLOSURE:
        return [proof.kind.value]
    if proof.ref.endswith(_REFL):
        return [f"closure:{proof.ref}", "closure:reflexive"]
    return [f"closure:{proof.ref}"]


DEFAULT_PROFILE = TemplateProfile.from_mapping(CZECH_PROFILE)


@dataclass(frozen=True, slots=True)
class ReasonLine:
    depth: int
    text: str
    statement: str | None = None

    def render(self) -> str:
        return f"{'  ' * self.depth}- {self.text}"


@dataclass(frozen=True, slots=True)
class AuditReport:
    question: str
    status: QueryStatus
    verdict: str
    reason: tuple[ReasonLine, ...]
    conflict: tuple[tuple[ReasonLine, ...], tuple[ReasonLine, ...]] | None
    gap: tuple[str, ...]
    cited: tuple[str, ...]
    #: Hranice kontextu, ve kterém závěr platí. Prázdné dokud neexistuje
    #: `closed_context` (§ 12) — až bude, výsledky z uzavřeného světa se
    #: sem musí přiznat a nesmí vystupovat jako nepodložené faktické důkazy.
    scope: tuple[str, ...] = ()

    def verify(self, proof: Proof | None) -> None:
        """`cited` musí přesně odpovídat listům důkazu — ani víc, ani míň."""
        expected = proof.leaves() if proof is not None else frozenset()
        if set(self.cited) != set(expected):
            raise MissingTemplate(
                f"report cituje {sorted(self.cited)}, důkaz stojí na "
                f"{sorted(expected)}; vysvětlení neodpovídá struktuře (I‑14)"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "status": self.status.value,
            "verdict": self.verdict,
            "reason": [
                {"depth": line.depth, "text": line.text, "statement": line.statement}
                for line in self.reason
            ],
            "conflict": (
                None
                if self.conflict is None
                else {
                    "positive": [line.render() for line in self.conflict[0]],
                    "negative": [line.render() for line in self.conflict[1]],
                }
            ),
            "gap": list(self.gap),
            "cited": list(self.cited),
            "scope": list(self.scope),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class XAIPresenter:
    """Jediný výstupní kanál. Nesahá na jádro a nic nedopočítává —
    dostane `QueryResult` a přeloží ho, nebo selže."""

    def __init__(
        self,
        kb: KnowledgeBase,
        profile: TemplateProfile = DEFAULT_PROFILE,
    ) -> None:
        self.kb = kb
        self.profile = profile

    # -- veřejné API -------------------------------------------------------

    def render_audit_report(
        self, question: Atom, result: QueryResult, *, scope: tuple[str, ...] = ()
    ) -> AuditReport:
        proof = result.proof
        conflict: tuple[tuple[ReasonLine, ...], tuple[ReasonLine, ...]] | None = None
        reason: tuple[ReasonLine, ...] = ()
        cited: frozenset[str] = frozenset()

        if result.conflict is not None:
            positive, negative = result.conflict
            conflict = (self._walk(positive, 0), self._walk(negative, 0))
            cited = positive.leaves() | negative.leaves()
        elif proof is not None:
            reason = self._walk(proof, 0)
            cited = proof.leaves()

        report = AuditReport(
            question=str(question),
            status=result.status,
            verdict=self.profile.for_verdict(result.status),
            reason=reason,
            conflict=conflict,
            gap=tuple(result.gap.render()) if result.gap is not None else (),
            cited=tuple(sorted(cited)),
            scope=scope,
        )
        if result.conflict is None:
            report.verify(proof)
        return report

    def to_markdown(self, report: AuditReport) -> str:
        section = self.profile.for_section
        lines = [
            f"**{section('question')}:** {report.question}",
            "",
            f"**{section('verdict')}:** {report.verdict}",
        ]
        if report.scope:
            lines += ["", "> " + " · ".join(report.scope)]
        if report.reason:
            lines += ["", f"**{section('reason')}:**", ""]
            lines += [line.render() for line in report.reason]
        if report.conflict is not None:
            positive, negative = report.conflict
            lines += ["", f"**{section('conflict_positive')}:**", ""]
            lines += [line.render() for line in positive]
            lines += ["", f"**{section('conflict_negative')}:**", ""]
            lines += [line.render() for line in negative]
        if report.gap:
            lines += ["", f"**{section('gap')}:**", ""]
            lines += [f"- {item}" for item in report.gap]
        if report.cited:
            lines += ["", f"**{section('cited')}:** " + ", ".join(report.cited)]
        return "\n".join(lines)

    def render_proof(self, proof: Proof) -> tuple[ReasonLine, ...]:
        """Samotný důkazní strom bez obalu reportu — pro odpovědi, které
        nejsou verdikt (např. mez veličiny)."""
        return self._walk(proof, 0)

    # -- vnitřnosti --------------------------------------------------------

    def _walk(self, proof: Proof, depth: int) -> tuple[ReasonLine, ...]:
        template = self.profile.for_node(proof)
        statement = self._statement_text(proof)
        text = template.format(ref=proof.ref, statement=statement or proof.ref)
        lines = [ReasonLine(depth=depth, text=text, statement=statement)]
        for premise in proof.premises:
            lines.extend(self._walk(premise, depth + 1))
        return tuple(lines)

    def _statement_text(self, proof: Proof) -> str | None:
        """Text výroku se bere z BÁZE, ne ze šablony — šablona smí okolo
        napsat větu, ale obsah musí pocházet z toho, co je zapsané."""
        if proof.kind not in (ProofKind.FACT, ProofKind.RULE):
            return None
        try:
            statement, active, _ = self.kb.inspect(proof.ref)
        except KeyError:
            raise MissingTemplate(
                f"důkaz cituje výrok {proof.ref!r}, který v bázi není"
            ) from None
        if not active:
            raise MissingTemplate(
                f"důkaz cituje odvolaný výrok {proof.ref!r}"
            )
        formula = statement.formula
        return str(formula.head) + " <- …" if isinstance(formula, Rule) else str(
            formula
        )
