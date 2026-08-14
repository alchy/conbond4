"""`GapFinder` — „Proč nevíš?", § 6.8 zadání a § 12 dokumentu.

> „Proč nevíš?" → chybějící premisy („chybí vědět: …", bez duplicit).

Dosud vracel evaluátor `Gap((query,))`, tedy **zopakovanou otázku**. To
není rozbor mezery a § 6.8 tím splněný nebyl.

**Co tenhle modul dělá:** goal‑directed průchod, který vrací **otevřené
podcíle** — co prohledávání potřebovalo a nenašlo. Dvě cesty:

* **přes pravidla** — pro každé pravidlo, jehož hlava se s dotazem
  unifikuje, se projde tělo a nahlásí se literál, na kterém se zaseklo.
  „Pravidlo `p3` by to dalo, ale chybí `role_exists(…)`" je použitelná
  informace; „chybí vědět: <dotaz>" není.
* **přes uzávěry** — u `member` a `subset` se z báze odvodí, který
  chybějící článek by řetěz uzavřel: „vím, že Hrabal je spisovatel;
  chybí vědět: spisovatel ⊆ dramatik".

**Co tenhle modul NEDĚLÁ:** neslibuje **minimální množinu faktů, které by
verdikt překlopily**. To je abdukce, ne dedukce — řešení nemusí být jediné
a hledání je nad pravidlovou bází drahé. § 12 popisuje `GapFinder` jako
top‑down SLD vracející otevřené podcíle, a to je přesně tohle a nic víc.

**Přiznaná mez.** Prohledávání je omezené hloubkou i počtem větví na
literál. Nahlásí se podcíl, který se dostal nejdál; když se mez vyčerpá,
je to v reportu vidět (`exhausted`), ne zamlčené.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .ast import (
    Atom,
    GroupDiff,
    P_DISJOINT,
    P_MEMBER,
    P_SUBSET,
    Quantifier,
    QueryStatus,
    RoleTerm,
    Sort,
    Variable,
    atom,
    contains_of,
    member_of,
    role,
    subset_of,
    within_of,
)
from .engine import Binding, Derivation, Engine, instantiate

#: Kolik pravidel do hloubky se rozbaluje. Dvě stačí na „pravidlo chce
#: premisu, kterou by dalo jiné pravidlo"; hlouběji přestává být report
#: čitelný pro člověka, což je jeho jediný účel.
MAX_DEPTH = 2
#: Kolik vazeb na literál se zkouší, než se hledání zastaví. Bez stropu by
#: se z rozboru mezery stalo úplné prohledávání.
MAX_BRANCHES = 8


@dataclass(frozen=True, slots=True)
class OpenGoal:
    """Podcíl, který prohledávání potřebovalo a nenašlo."""

    atom: Atom
    via: str
    depth: int = 0

    def render(self) -> str:
        return f"chybí vědět: {self.atom}   [{self.via}]"


@dataclass(frozen=True, slots=True)
class GapReport:
    query: Atom
    open_goals: tuple[OpenGoal, ...]
    known: tuple[str, ...] = ()
    exhausted: bool = False

    def render(self) -> tuple[str, ...]:
        lines: list[str] = []
        lines.extend(f"vím: {item}" for item in self.known)
        if self.open_goals:
            lines.extend(goal.render() for goal in self.open_goals)
        else:
            lines.append(f"chybí vědět: {self.query}")
        if self.exhausted:
            lines.append(
                "(hledání jsem zastavil na mezi hloubky — můžou být další)"
            )
        return tuple(lines)


class GapFinder:
    """Rozbor mezery. Nesahá na bázi ani na evaluátor — jen se ptá."""

    def __init__(
        self,
        engine: Engine,
        *,
        max_depth: int = MAX_DEPTH,
        max_branches: int = MAX_BRANCHES,
    ) -> None:
        self.engine = engine
        self.max_depth = max_depth
        self.max_branches = max_branches

    # -- veřejné API -------------------------------------------------------

    def explain(self, query: Atom) -> GapReport:
        derivation = self.engine.derivation()
        if self.engine.ask(query).status is not QueryStatus.UNKNOWN:
            return GapReport(query=query, open_goals=())
        self._exhausted = False
        goals = self._goals_for(query, derivation, depth=0)
        return GapReport(
            query=query,
            open_goals=self._dedupe(goals),
            known=self._what_is_known(query, derivation),
            exhausted=self._exhausted,
        )

    # -- vnitřnosti --------------------------------------------------------

    def _goals_for(
        self, query: Atom, derivation: Derivation, *, depth: int
    ) -> list[OpenGoal]:
        if depth > self.max_depth:
            self._exhausted = True
            return []
        goals: list[OpenGoal] = []
        immediate = [
            *self._closure_goals(query, derivation, depth),
            *self._fact_goals(query, derivation, depth),
        ]
        goals.extend(immediate)
        # Zanoření: „chybí subset(vrabec, pták DIFF tučňák)" je pravda, ale
        # člověk umí doplnit až to, co z toho plyne — `disjoint(vrabec,
        # tučňák)`. Report proto sestupuje o úroveň dál, dokud přidává nový
        # cíl.
        for goal in immediate:
            for deeper in self._goals_for(goal.atom, derivation, depth=depth + 1):
                if str(deeper.atom) != str(goal.atom):
                    goals.append(deeper)

        produced = False
        for rule in self.engine.kb.view().rules:
            outcome = self.engine._match_atom(  # noqa: SLF001
                rule.head, query, {}, derivation
            )
            if outcome is None:
                continue
            produced = True
            binding, _ = outcome
            blocked = self._blocked_literal(rule.body, binding, derivation)
            if blocked is None:
                continue
            # Atribuce k pravidlu je ta užitečná půlka: „pravidlo p3 by to
            # dalo, ale chybí omezení". Zanoření ji nesmí přepsat — přidává
            # se K NÍ, ne místo ní, a jen pokud nese nový cíl.
            goals.append(
                OpenGoal(atom=blocked, via=f"pravidlo {rule.id}", depth=depth)
            )
            for deeper in self._goals_for(blocked, derivation, depth=depth + 1):
                if str(deeper.atom) != str(blocked):
                    goals.append(deeper)

        if not produced and not goals:
            goals.append(
                OpenGoal(
                    atom=query,
                    via="žádné pravidlo tohle nevyrábí",
                    depth=depth,
                )
            )
        return goals

    def _blocked_literal(
        self, body: Sequence[Atom], binding: Binding, derivation: Derivation
    ) -> Atom | None:
        """Literál, na kterém se tělo zaseklo — ten, který se dostal nejdál.

        Zkouší se víc vazeb, ne jen první: literál může selhat pod jednou
        vazbou a projít pod jinou, a nahlásit ten první by ukázalo na
        nepravé místo. Prohledávání je ale zastropované."""
        if not body:
            return None
        head, rest = body[0], tuple(body[1:])
        try:
            solutions = list(self.engine._match(head, binding, derivation))  # noqa: SLF001
        except Exception:  # noqa: BLE001 — diagnostika nesmí shodit odpověď
            solutions = []
        if not solutions:
            return instantiate(head, binding)
        deepest: Atom | None = None
        for next_binding, _ in solutions[: self.max_branches]:
            blocked = self._blocked_literal(rest, next_binding, derivation)
            if blocked is None:
                return None  # tahle větev projde celá, tělo tedy neblokuje
            deepest = blocked
        if len(solutions) > self.max_branches:
            self._exhausted = True
        return deepest

    def _fact_goals(
        self, query: Atom, derivation: Derivation, depth: int
    ) -> list[OpenGoal]:
        """Fakt téhož jména v bázi JE, jen některá role nesedí.

        Bez tohohle patra hlásí report „žádné pravidlo tohle nevyrábí"
        i tam, kde odpověď leží na dosah a chybí jediný článek. Nahlásí
        se konkrétní role a to, co by ji uzavřelo."""
        goals: list[OpenGoal] = []
        for fact in derivation.candidates(query):
            if fact == query:
                continue
            for prole in query.canonical_roles():
                frole = fact.get_role(prole.name)
                if frole is None:
                    continue
                if self.engine._compat(prole, frole, {}, derivation) is not None:  # noqa: SLF001
                    continue
                missing = _missing_link(prole, frole)
                if missing is not None:
                    source = ", ".join(sorted(derivation.facts[fact].leaves()))
                    goals.append(
                        OpenGoal(
                            atom=missing,
                            via=f"fakt {source}, role {prole.name}",
                            depth=depth,
                        )
                    )
                break
        return goals

    def _closure_goals(
        self, query: Atom, derivation: Derivation, depth: int
    ) -> list[OpenGoal]:
        """Chybějící článek řetězu u `member` a `subset`.

        Tohle je ta část, která dělá z „chybí vědět: <dotaz>" použitelnou
        odpověď: z báze se odvodí, co by řetěz uzavřelo."""
        if query.is_negated or derivation.index is None:
            return []
        index = derivation.index
        if query.predicate == P_MEMBER:
            elem = query.get_role("elem")
            group = query.get_role("group")
            if elem is None or group is None:
                return []
            if isinstance(elem.target, Variable) or isinstance(
                group.target, Variable
            ):
                return []
            declared = [
                declared_group
                for declared_group, _ in index.declared_memberships(elem.target.id)
            ]
            return [
                OpenGoal(
                    atom=subset_of_ids(declared_group, group.target.id),
                    via="uzávěr member*",
                    depth=depth,
                )
                for declared_group in sorted(set(declared))
                if declared_group != group.target.id
            ]
        if query.predicate == P_SUBSET:
            sub = query.get_role("sub")
            sup = query.get_role("sup")
            if sub is None or sup is None:
                return []
            # Zákon 9 (§ 5.2.1, dodatek E): `X ⊆ A ∧ disjoint(X,B) ⇒
            # X ⊆ A DIFF B`. Když levá polovina platí, chybí přesně ta
            # oddělenost — a to je odpověď, kterou člověk umí doplnit.
            if isinstance(sup.target, GroupDiff):
                left = self.engine._subset_term(  # noqa: SLF001
                    sub.target, sup.target.left, derivation
                )
                if left is not None:
                    return [
                        OpenGoal(
                            atom=atom(
                                P_DISJOINT,
                                role("a", sub.target, Quantifier.SELF),
                                role("b", sup.target.right, Quantifier.SELF),
                            ),
                            via="zákon X ⊆ A ∧ disjoint(X,B)",
                            depth=depth,
                        )
                    ]
            return []
        return []

    def _what_is_known(
        self, query: Atom, derivation: Derivation
    ) -> tuple[str, ...]:
        """Co o subjektu dotazu doloženo JE.

        Není to měkká vrstva ze § 4 — žádná aktivace, žádná blízkost. Jen
        doložená členství toho uzlu, na který se dotaz ptá."""
        if derivation.index is None:
            return ()
        elem = query.get_role("elem")
        if elem is None or isinstance(elem.target, Variable):
            return ()
        groups = derivation.index.known_groups_of(elem.target.id)
        return tuple(f"{elem.target.id} patří do {group}" for group in groups)

    @staticmethod
    def _dedupe(goals: Sequence[OpenGoal]) -> tuple[OpenGoal, ...]:
        """§ 6.8 žádá chybějící premisy **bez duplicit**."""
        seen: set[tuple[str, str]] = set()
        unique: list[OpenGoal] = []
        for goal in sorted(goals, key=lambda g: (g.depth, str(g.atom), g.via)):
            key = (str(goal.atom), goal.via)
            if key in seen:
                continue
            seen.add(key)
            unique.append(goal)
        return tuple(unique)


def _missing_link(pattern: RoleTerm, fact: RoleTerm) -> Atom | None:
    """Co by roli uzavřelo. Směry jsou tytéž jako v `⪯` (§ 3.3).

    Pokrývá i **místa a časy**: bez nich by báze „jel(kdo:Petr, kam:Praha)"
    a dotaz „jel(kdo:Petr, kam:Brno)" spadly na obecné „žádné pravidlo
    tohle nevyrábí", místo aby ukázaly na roli `kam` a na `contains*`.
    Report by zůstal poctivý, ale málo užitečný — a dialog D je právě
    o místech a časech.
    """
    pq, fq = pattern.quantifier, fact.quantifier
    sorts = (pattern.target.SORT, fact.target.SORT)
    if sorts == (Sort.GROUP, Sort.GROUP):
        if pq is Quantifier.FOR_ALL and fq is Quantifier.FOR_ALL:
            return subset_of(pattern.target, fact.target)  # type: ignore[arg-type]
        if pq is Quantifier.EXISTS and fq is Quantifier.EXISTS:
            return subset_of(fact.target, pattern.target)  # type: ignore[arg-type]
    if pq is None and fq is Quantifier.FOR_ALL and fact.target.SORT is Sort.GROUP:
        return member_of(pattern.target, fact.target)  # type: ignore[arg-type]
    # Prostor a čas: dotaz je širší místo/interval, fakt užší — uzavřelo by
    # to obsažení. Směr je týž jako v `_compat`: dotaz obsahuje fakt.
    if pq is None and fq is None:
        if sorts == (Sort.PLACE, Sort.PLACE):
            return contains_of(pattern.target, fact.target)  # type: ignore[arg-type]
        if sorts == (Sort.TIME, Sort.TIME):
            return within_of(pattern.target, fact.target)  # type: ignore[arg-type]
    return None


def subset_of_ids(sub_id: str, sup_id: str) -> Atom:
    """`subset(sub, sup)` z holých id — mezera se hlásí o skupinách, které
    v bázi jsou, takže jejich termy nemusíme rekonstruovat."""
    from .ast import Group

    return subset_of(Group(sub_id), Group(sup_id))
