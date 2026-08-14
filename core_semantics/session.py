"""Dialogová vrstva — Core Semantics 0.1, § 2 (V0), § 3.7 (`DIA`), § 10.

Dialog není nadstavba nad hotovým jádrem: `DIA` je třetí program vedle
`ONTO` a `LEX` a hlavní metrika projektu — *„kolik tahů dialogu potřebuje,
aby se naučil odpovídat správně"* (§ 10) — je bez téhle vrstvy neměřitelná.

**Tah je STRUKTUROVANÝ, ne surový text.** Parser je vnější orákulum
(§ 5.1) a vrstvy V1–V3 ve F0 nejsou; `Session` proto dostává rovnou
formuli nebo dotaz, a `text` je jen lidský popis pro transkript. Testuje
se, co systém s posloupností tahů udělá a co odpoví — ne jak větu rozebral.

**Můstková pravidla se nevymýšlejí.** Vrátí‑li dotaz `U`, tah smí nabídnout
pravidlo, které s sebou nese jako návrh (`awaiting_rule_confirmation`,
§ 3.7). Generátor návrhů — tedy schopnost odvodit z mezery, JAKÉ pravidlo
chybí — je v F0 mimo rozsah a je to vědomá díra, ne opomenutí: nabídnout
smí jen to, co někdo navrhl.

**Determinismus** (I‑4): „teď" je pořadové číslo tahu, ne čas stroje.
Žádné hodiny, žádná neseedovaná náhoda — `replay(žurnál)` proto dá týž
program i tytéž odpovědi (§ 10).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .ast import (
    Atom,
    AttachError,
    Comparator,
    Formula,
    GroupTerm,
    P_NAME,
    Proof,
    QueryResult,
    QueryStatus,
    Rule,
    Term,
)
from .engine import Engine
from .epistemics import BoundResult, query_bound
from .gaps import GapFinder
from .presenter import DEFAULT_PROFILE, AuditReport, TemplateProfile, XAIPresenter
from .storage import KnowledgeBase


class TurnKind(Enum):
    ASSERT = "!"
    READING = "«"
    DISJOINT = "!∦"
    REVOKE = "✗"
    QUESTION = "?"
    BOUND = "?~"
    DESCRIBE = "?="
    ENUMERATE = "?∃"
    CONFIRM = "→"


@dataclass(frozen=True, slots=True)
class Turn:
    """Jeden tah dialogu. `text` je pro člověka, ostatní pole pro jádro."""

    kind: TurnKind
    text: str
    formula: Formula | None = None
    query: Atom | None = None
    bridge: Rule | None = None
    subject: Term | None = None
    quantity: str | None = None
    comparator: Comparator = Comparator.LE
    accepted: bool = True
    statement_id: str | None = None
    reason: str = ""
    variable: str = ""
    pair: tuple[GroupTerm, GroupTerm] | None = None
    #: Vybrané čtení. Do žurnálu jde STRUKTURA, ne text — kdyby v žurnálu
    #: ležely věty, `replay` by závisel na verzi parseru a přehratelnost
    #: z § 10 by padla (a na té stojí měření učitelnosti).
    predication: Predication | None = None
    trace: tuple[str, ...] = ()


def says(text: str, formula: Formula) -> Turn:
    return Turn(TurnKind.ASSERT, text, formula=formula)


def asks(text: str, query: Atom, *, bridge: Rule | None = None) -> Turn:
    return Turn(TurnKind.QUESTION, text, query=query, bridge=bridge)


def asks_bound(
    text: str,
    subject: Term,
    quantity: str,
    *,
    comparator: Comparator = Comparator.LE,
    bridge: Rule | None = None,
) -> Turn:
    return Turn(
        TurnKind.BOUND,
        text,
        subject=subject,
        quantity=quantity,
        comparator=comparator,
        bridge=bridge,
    )


def asks_about(text: str, subject: Term) -> Turn:
    return Turn(TurnKind.DESCRIBE, text, subject=subject)


def asks_for(text: str, pattern: Atom, variable: str) -> Turn:
    """Výčtová otázka se syntézou — „Co má Filip?" nevrací echo jedné věty,
    ale složený popis nalezeného uzlu (§ 6.5, dialog F)."""
    return Turn(TurnKind.ENUMERATE, text, query=pattern, variable=variable)


def declares_disjoint(text: str, first: GroupTerm, second: GroupTerm) -> Turn:
    """„Žádný stroj není člověk." Vlastní druh tahu, protože se neukládá
    jeden atom, ale marker plus derivační expanze na dvě pravidla se
    silnou negací (§ 5.3)."""
    return Turn(TurnKind.DISJOINT, text, pair=(first, second))


def revokes(text: str, statement_id: str, reason: str) -> Turn:
    """Odvolání je plnohodnotný tah — učení má jen `attach` a `revoke`
    (§ 3.7). Výrok zůstává v historii s důvodem."""
    return Turn(TurnKind.REVOKE, text, statement_id=statement_id, reason=reason)


def confirms(text: str, *, accepted: bool = True) -> Turn:
    return Turn(TurnKind.CONFIRM, text, accepted=accepted)


@dataclass(frozen=True, slots=True)
class TurnResult:
    index: int
    turn: Turn
    lines: tuple[str, ...] = ()
    statement_id: str | None = None
    derived: tuple[str, ...] = ()
    status: QueryStatus | None = None
    report: AuditReport | None = None
    offered: Rule | None = None
    error: str | None = None

    def render(self) -> str:
        head = f"»  {self.turn.kind.value} {self.turn.text}"
        return "\n".join([head, *[f"    {line}" for line in self.lines]])


class Session:
    """Drží bázi, evaluátor a renderer a zpracovává tahy."""

    def __init__(
        self,
        *,
        profile: TemplateProfile = DEFAULT_PROFILE,
        max_depth: int = 1,
    ) -> None:
        self.kb = KnowledgeBase(max_depth=max_depth)
        self.presenter = XAIPresenter(self.kb, profile)
        self.journal: list[Turn] = []
        self.results: list[TurnResult] = []
        self._pending: Rule | None = None

    # -- běh ---------------------------------------------------------------

    def engine(self) -> Engine:
        """Nový evaluátor nad aktuální bází. Otázka bázi nemění (I‑12),
        takže je zahoditelný."""
        return Engine(self.kb)

    def play(self, turn: Turn) -> TurnResult:
        index = len(self.journal) + 1
        self.journal.append(turn)
        handler = {
            TurnKind.ASSERT: self._assert,
            TurnKind.DISJOINT: self._declare_disjoint,
            TurnKind.REVOKE: self._revoke,
            TurnKind.QUESTION: self._question,
            TurnKind.BOUND: self._bound,
            TurnKind.DESCRIBE: self._describe,
            TurnKind.ENUMERATE: self._enumerate,
            TurnKind.CONFIRM: self._confirm,
        }[turn.kind]
        result = handler(index, turn)
        self.results.append(result)
        return result

    def run(self, turns: Sequence[Turn]) -> list[TurnResult]:
        return [self.play(turn) for turn in turns]

    @classmethod
    def replay(
        cls, journal: Sequence[Turn], *, profile: TemplateProfile = DEFAULT_PROFILE
    ) -> "Session":
        session = cls(profile=profile)
        session.run(journal)
        return session

    # -- výstup ------------------------------------------------------------

    def transcript(self) -> str:
        return "\n\n".join(result.render() for result in self.results)

    def program(self) -> tuple[str, ...]:
        """Aktivní výroky jako text — „diff kódu je diff naučeného" (§ 10)."""
        return tuple(str(statement) for statement in self.kb.active())

    def answers(self) -> tuple[str, ...]:
        return tuple(result.render() for result in self.results)

    def turns_to_learn(self, text: str) -> int | None:
        """Hlavní metrika § 10 — kolik tahů uplynulo od prvního `NEVÍM` na
        danou otázku po první doloženou odpověď na tutéž otázku."""
        unknown_at: int | None = None
        for result in self.results:
            if result.turn.text != text or result.status is None:
                continue
            if result.status is QueryStatus.UNKNOWN:
                if unknown_at is None:
                    unknown_at = result.index
            elif unknown_at is not None:
                return result.index - unknown_at
        return None

    # -- jednotlivé druhy tahu ---------------------------------------------

    def _assert(self, index: int, turn: Turn) -> TurnResult:
        assert turn.formula is not None
        try:
            sid = self.kb.attach(turn.formula, provenance=f"tah {index}")
        except AttachError as exc:
            return TurnResult(
                index=index,
                turn=turn,
                lines=(f"✗ nezapsáno: {exc}",),
                error=str(exc),
            )
        statement, _, _ = self.kb.inspect(sid)
        derived = tuple(item.id for item in self.kb.derived_from(sid))
        lines = [f"✓ zapsáno [{sid}]  {statement.formula}"]
        if derived:
            lines.append(f"[odvozeno: {', '.join(derived)}]")
        return TurnResult(
            index=index, turn=turn, lines=tuple(lines), statement_id=sid,
            derived=derived,
        )

    def _question(self, index: int, turn: Turn) -> TurnResult:
        assert turn.query is not None
        engine = self.engine()
        result = engine.ask(turn.query)
        report = self.presenter.render_audit_report(turn.query, result)
        # Na `U` se místo zopakované otázky vypíše ROZBOR mezery (§ 6.8).
        # „Chybí vědět: <dotaz>" člověku neřekne, co má doplnit.
        gap_lines = (
            GapFinder(engine).explain(turn.query).render()
            if result.status is QueryStatus.UNKNOWN
            else ()
        )
        lines = list(self._render_answer(report, gap_lines=gap_lines))
        offered = self._offer_bridge(turn, result, lines)
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=result.status,
            report=report,
            offered=offered,
        )

    def _bound(self, index: int, turn: Turn) -> TurnResult:
        assert turn.subject is not None and turn.quantity is not None
        bound: BoundResult = query_bound(
            self.engine(), turn.subject, turn.quantity, turn.comparator
        )
        lines: list[str] = []
        if bound.status is QueryStatus.PROVEN_TRUE and bound.value is not None:
            lines.append(
                f"→ {turn.comparator.value} {bound.value.magnitude} "
                f"{bound.value.unit}"
            )
            lines.extend(self._render_reason(bound.proof))
        else:
            lines.append("→ NEVÍM")
            lines.append(
                f"  chybí vědět: mez veličiny {turn.quantity!r} "
                f"pro {turn.subject.id}"
            )
        synthetic = QueryResult(status=bound.status, proof=bound.proof)
        offered = self._offer_bridge(turn, synthetic, lines)
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=bound.status,
            offered=offered,
        )

    def _declare_disjoint(self, index: int, turn: Turn) -> TurnResult:
        assert turn.pair is not None
        first, second = turn.pair
        try:
            marker, left, right = self.kb.add_disjoint(
                first, second, provenance=f"tah {index}"
            )
        except AttachError as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ nezapsáno: {exc}",), error=str(exc)
            )
        return TurnResult(
            index=index,
            turn=turn,
            lines=(
                f"✓ zapsáno [{marker}]  disjoint({first.id}, {second.id})",
                f"[expanze na dvě pravidla se silnou negací: {left}, {right}]",
            ),
            statement_id=marker,
            derived=(left, right),
        )

    def _revoke(self, index: int, turn: Turn) -> TurnResult:
        assert turn.statement_id is not None
        try:
            revoked = self.kb.revoke(turn.statement_id, turn.reason)
        except KeyError as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ {exc}",), error=str(exc)
            )
        lines = [f"✓ odvoláno [{', '.join(revoked)}]  důvod: {turn.reason}"]
        lines.append("  (výroky zůstávají v historii, jen neplatí)")
        return TurnResult(index=index, turn=turn, lines=tuple(lines), derived=tuple(revoked))

    def _synthesis(self, subject: Term) -> tuple[list[str], list[str]]:
        """§ 6.5 — složený popis uzlu z doložených členství a jmen.

        Odpověď na „Co má Filip?" má být SYNTÉZA nashromážděného popisu
        (členství + vlastnost + jméno), ne echo jedné věty. Vše se bere
        z doložených struktur, takže každý údaj má citovatelný výrok.
        """
        view = self.kb.view()
        traits: list[str] = []
        cited: list[str] = []
        for group_id in view.known_groups_of(subject.id):
            proof = view.member_proof(subject.id, group_id)
            if proof is None:
                continue
            traits.append(group_id)
            cited.extend(proof.leaves())
        canonical = view.canonical(subject.id)
        for statement in self.kb.active():
            formula = statement.formula
            if isinstance(formula, Rule) or formula.predicate != P_NAME:
                continue
            target = formula.get_role("of")
            value = formula.get_role("value")
            if target is None or value is None:
                continue
            if view.canonical(target.target.id) == canonical:
                traits.append(f"jménem {value.target.id}")
                cited.append(statement.id)
        return traits, sorted(set(cited))

    def _describe(self, index: int, turn: Turn) -> TurnResult:
        assert turn.subject is not None
        traits, cited = self._synthesis(turn.subject)
        lines = (
            [f"→ {turn.subject.id}: " + ", ".join(traits)]
            if traits
            else ["→ NEVÍM", f"  chybí vědět: cokoli o {turn.subject.id}"]
        )
        if cited:
            lines.append(f"[doloženo: {', '.join(cited)}]")
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=QueryStatus.PROVEN_TRUE if traits else QueryStatus.UNKNOWN,
        )

    def _enumerate(self, index: int, turn: Turn) -> TurnResult:
        assert turn.query is not None
        solutions = self.engine().solutions(turn.query)
        lines: list[str] = []
        cited: set[str] = set()
        found: list[str] = []
        for binding, proof in solutions:
            term = binding.get(turn.variable)
            if term is None:
                continue
            traits, node_cited = self._synthesis(term)
            found.append(term.id)
            lines.append(
                f"→ {term.id}: " + (", ".join(traits) if traits else "(bez popisu)")
            )
            cited.update(node_cited)
            cited.update(proof.leaves())
        if not found:
            lines = ["→ NEVÍM", f"  chybí vědět: {turn.query}"]
        elif cited:
            lines.append(f"[doloženo: {', '.join(sorted(cited))}]")
        return TurnResult(
            index=index,
            turn=turn,
            lines=tuple(lines),
            status=QueryStatus.PROVEN_TRUE if found else QueryStatus.UNKNOWN,
        )

    def _confirm(self, index: int, turn: Turn) -> TurnResult:
        if self._pending is None:
            return TurnResult(
                index=index,
                turn=turn,
                lines=("(nebylo na co odpovědět)",),
                error="žádná nabídka nečeká na potvrzení",
            )
        rule = self._pending
        self._pending = None
        if not turn.accepted:
            return TurnResult(
                index=index, turn=turn, lines=(f"✓ nabídka {rule.id} odmítnuta",)
            )
        try:
            sid = self.kb.attach(rule, provenance=f"potvrzeno tahem {index}")
        except AttachError as exc:
            return TurnResult(
                index=index, turn=turn, lines=(f"✗ nezapsáno: {exc}",), error=str(exc)
            )
        return TurnResult(
            index=index,
            turn=turn,
            lines=(f"✓ zapsáno [{sid}]  {rule}",),
            statement_id=sid,
        )

    # -- renderování -------------------------------------------------------

    def _offer_bridge(
        self, turn: Turn, result: QueryResult, lines: list[str]
    ) -> Rule | None:
        """`awaiting_rule_confirmation` — chybějící článek se nehádá,
        nabídne se k potvrzení (§ 6.6 zadání, I‑7)."""
        if turn.bridge is None or result.status is not QueryStatus.UNKNOWN:
            return None
        self._pending = turn.bridge
        lines.append(f"  mám z toho usoudit pravidlo {turn.bridge.id}?")
        lines.append(f"    {turn.bridge}")
        return turn.bridge

    def _render_answer(
        self, report: AuditReport, *, gap_lines: Sequence[str] = ()
    ) -> list[str]:
        lines = [f"→ {report.verdict}"]
        if report.reason:
            lines.append("  protože:")
            lines.extend(f"  {line.render()}" for line in report.reason)
        if report.conflict is not None:
            positive, negative = report.conflict
            lines.append("  důkaz pro:")
            lines.extend(f"  {line.render()}" for line in positive)
            lines.append("  důkaz proti:")
            lines.extend(f"  {line.render()}" for line in negative)
        for item in gap_lines or report.gap:
            lines.append(f"  {item}")
        if report.cited:
            lines.append(f"[doloženo: {', '.join(report.cited)}]")
        return lines

    def _render_reason(self, proof: Proof | None) -> list[str]:
        if proof is None:
            return []
        lines = ["  protože:"]
        lines.extend(
            f"  {line.render()}" for line in self.presenter.render_proof(proof)
        )
        lines.append(f"[doloženo: {', '.join(sorted(proof.leaves()))}]")
        return lines
