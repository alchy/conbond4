"""Báze a pohled — Core Semantics 0.1, § 8 (identita) a § 9 (rozhraní).

Celé rozhraní jsou čtyři operace: `attach`, `revoke`, `eval`, `inspect`.
Zde jsou tři z nich; `eval` patří do enginu.

Zásady, které tenhle modul vynucuje:

* **Individua vytváří jen `attach`** (§ 0/2) — a to VČETNĚ reifikovaných
  uzlů vztahů. Reifikace tedy patří sem, ne do evaluátoru: uzel vzniká
  z výroku, který zapsal člověk, dostane vlastní id, provenienci a
  `derived_from` na zdroj, takže na něj dosáhne `inspect` i kaskádové
  `revoke` (§ 3.7/1). Engine zůstane čistě čtecí.
* **`same_as` nemergeuje fyzicky** (§ 8). Uložená fakta si drží původní
  `resolved_id`; kolaps do tříd ekvivalence dělá `ResolvedGraphView` při
  čtení. `revoke` proto nemá co opravovat — jen se postaví jiný pohled.
* **Mez vnoření je strojově hlídaná** (§ 12/3 zadání, I‑13).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Mapping

import networkx as nx

from .ast import (
    P_BEFORE,
    Atom,
    AttachError,
    CycleDetected,
    DepthExceeded,
    Formula,
    Group,
    GroupTerm,
    KERNEL_PREDICATES,
    P_DISJOINT,
    P_SAME_AS,
    disjoint_of,
    Proof,
    Quantifier,
    RESERVED_PREDICATES,
    RelationInstance,
    Rule,
    Sort,
    UnsafeRule,
    Variable,
    atom,
    member_of,
    role,
    role_atom,
)
from .closures import ClosureIndex

#: Uzel dependency grafu — viz `Atom.dependency_key`.
DependencyKey = tuple[str, bool, tuple[tuple[str, str], ...]]

#: Klíč zapamatované stavby: množina pravidel × třídy ekvivalence.
_GraphKey = tuple[tuple[str, ...], tuple[tuple[str, str], ...]]


@dataclass
class _GraphCache:
    """Zapamatovaná stavba. `levels` se počítají až když je někdo potřebuje —
    validace acykličnosti je nepotřebuje, řazení pravidel ano."""

    key: _GraphKey
    positive: nx.DiGraph
    strata: nx.DiGraph
    levels: dict[DependencyKey, int] | None = None


@dataclass(frozen=True, slots=True)
class Statement:
    """Řádek meta-kódu. Každý JE delta grafu (§ 3.7 zadání), má id výroku
    a provenienci; `derived_from` drží řádky, které vznikly expanzí jiného
    výroku (reifikace vztahu, expanze `disjoint`) — odvolání zdroje je
    strhne s sebou."""

    id: str
    formula: Formula
    provenance: str = ""
    derived_from: str | None = None

    def __str__(self) -> str:
        origin = f" @from({self.derived_from})" if self.derived_from else ""
        prov = f" @{self.provenance}" if self.provenance else ""
        # `Rule.__str__` už své id nese — neopakovat ho.
        body = str(self.formula)
        prefix = "" if body.startswith(f"{self.id}:") else f"{self.id}: "
        return f"{prefix}{body}{prov}{origin}"


class ResolvedGraphView:
    """Virtuální pohled na bázi v jednom okamžiku. Nedrží vlastní data —
    staví se z aktivních výroků a je zahoditelný."""

    def __init__(
        self,
        version: int,
        facts: Iterable[tuple[str, Atom]],
        rules: Iterable[Rule],
    ) -> None:
        self.version = version
        self.index = ClosureIndex(facts)
        #: Pravidla už ve stratifikovaném pořadí — engine si žádné vlastní
        #: řazení nestaví (jinak by se § 5.4/5 a § 5.4/6 rozešly na dvou
        #: místech, jak upozornilo kolo #2).
        self.rules: tuple[Rule, ...] = tuple(rules)

    def canonical(self, node_id: str) -> str:
        return self.index.canonical(node_id)

    def class_of(self, node_id: str) -> list[str]:
        return self.index.class_of(node_id)

    def equivalence_classes(self) -> dict[str, list[str]]:
        return self.index.equivalence_classes()

    def same_class(self, a_id: str, b_id: str) -> Proof | None:
        return self.index.same_class(a_id, b_id)

    def subset_proof(self, sub_id: str, sup_id: str) -> Proof | None:
        return self.index.subset_proof(sub_id, sup_id)

    def contains_proof(self, whole_id: str, part_id: str) -> Proof | None:
        return self.index.contains_proof(whole_id, part_id)

    def within_proof(self, whole_id: str, part_id: str) -> Proof | None:
        return self.index.within_proof(whole_id, part_id)

    def before_proof(self, earlier_id: str, later_id: str) -> Proof | None:
        return self.index.before_proof(earlier_id, later_id)

    def ordering_cycles(self) -> frozenset[str]:
        return self.index.ordering_cycles()

    def member_proof(self, elem_id: str, group_id: str) -> Proof | None:
        return self.index.member_proof(elem_id, group_id)

    def is_known(self, node_id: str) -> bool:
        return self.index.knows(node_id)

    def nodes_named(self, name: str) -> list[str]:
        return self.index.nodes_named(name)

    def naming_statement(self, name: str, node_id: str) -> str | None:
        return self.index.naming_statement(name, node_id)

    def known_members(self, group_id: str) -> list[str]:
        return self.index.known_members(group_id)

    def is_complete(self, group_id: str) -> str | None:
        return self.index.is_complete(group_id)

    def element_sorts(self, group_id: str) -> frozenset[Sort]:
        return self.index.element_sorts(group_id)

    def known_groups_of(self, elem_id: str) -> list[str]:
        return self.index.known_groups_of(elem_id)


class KnowledgeBase:
    def __init__(self, *, max_depth: int = 1) -> None:
        self._statements: dict[str, Statement] = {}
        self._revoked: dict[str, str] = {}
        self._fact_counter = 0
        self._rule_counter = 0
        self._version = 0
        self._view: ResolvedGraphView | None = None
        #: Hloubka vnoření vztah(vztah) na reifikovaný uzel.
        self._depth: dict[str, int] = {}
        #: Zapamatovaná stavba dependency grafů, klíčovaná množinou pravidel
        #: a třídami ekvivalence — na ničem jiném grafy nezávisí.
        self._graph_cache: _GraphCache | None = None
        #: Kolik staveb proběhlo. Sleduje se testem, ne časem: „stavíme míň"
        #: je tvrzení o počtu, ne o rychlosti stroje (I‑4).
        self.graph_builds = 0
        #: Mez z § 12/3 zadání — modifikovatelný parametr, ne konstanta kódu.
        #: 0 = jen ploché vztahy, 1 = postoje o faktech.
        self.max_depth = max_depth

    # -- attach ------------------------------------------------------------

    def attach(
        self,
        formula: Formula,
        *,
        provenance: str = "",
        derived_from: str | None = None,
    ) -> str:
        """Jediný zápis. Smí selhat — a selhání je tah dialogu (§ 9).

        **Holý `disjoint` se odmítá.** Zapsat oddělenost znamená vygenerovat
        i dvojici pravidel se silnou negací (§ 5.3), tedy TŘI výroky. Kdyby
        se to dělo tady, vrátilo by `attach` jedno id a zapsalo tři —
        volající by neměl čím ta pravidla odvolat. Horší varianta byla ale
        ta dosavadní: marker se zapsal, index se naplnil, a NEODVODILO SE
        NIC. Táž báze pak odpovídala `N` nebo `U` podle toho, kterými
        dveřmi se do ní psalo. Jedny dveře jsou `add_disjoint`.
        """
        if (
            isinstance(formula, Atom)
            and formula.predicate == P_DISJOINT
            and not formula.is_negated
        ):
            raise AttachError(
                f"{formula} se nezapisuje přes `attach` — oddělenost je "
                f"derivační cukr a musí s ní vzniknout i dvojice pravidel "
                f"se silnou negací; použij `add_disjoint(a, b)`. Na OTÁZKU "
                f"„jsou oddělené?“ slouží `disjoint_of(a, b)`."
            )
        self._refuse_ordering_cycle(formula)
        return self._attach(formula, provenance=provenance, derived_from=derived_from)

    def _refuse_ordering_cycle(self, formula: Formula) -> None:
        """Hrana, která by uzavřela uspořádání do kruhu, se ODMÍTÁ (B‑16).

        **Chytá se to u ZÁPISU, ne u dotazu**, a je to vědomé rozhodnutí.
        Do téhle změny šla věta „Středa je před pondělím." zapsat bez
        námitky a rozbila se až PŘÍŠTÍ otázka — výjimkou, která utekla ze
        `Session.utter` ven. To je nejhorší možná chvíle: báze už je
        v rozbitém stavu, člověk netuší proč, a program nemá jak říct, co
        se stalo (I‑1). Selhání zápisu je přitom TAH DIALOGU (§ 9), na
        který jde odpovědět — třeba odvoláním jednoho z výroků.

        Hláška proto JMENUJE VÝROKY, které kruh tvoří. „Tohle nejde" bez
        nich by po člověku chtělo, aby si bázi prošel sám.

        **Co se tím NEROZHODUJE.** Druhá varianta — nechat zápis projít
        a odpovídat na dotaz `CONFLICT` s oběma důkazy — zůstává OTEVŘENÁ
        (§ 9, I‑13). Tenhle guard ji nevylučuje; jen brání tomu, aby se do
        toho stavu dalo dojít nechtěně. Rozhodnout obojí najednou by
        znamenalo změnit § 9 mimochodem.
        """
        if not isinstance(formula, Atom) or formula.predicate != P_BEFORE:
            return
        if formula.is_negated:
            return
        earlier = formula.get_role("earlier")
        later = formula.get_role("later")
        if earlier is None or later is None:
            return
        if earlier.target.id == later.target.id:
            # SMYČKA NA SEBE JE TAKY KRUH, jen jednouzlový. Hledání
            # „vede už cesta opačným směrem?" ji minulo, protože opačná
            # cesta u hrany na sebe neexistuje — a jednouzlový cyklus se
            # tím zapsal a shodil příští otázku, i tu, která s ním
            # nesouvisela.
            #
            # Není to nová politika: `before` je STRIKTNÍ uspořádání
            # a celé H‑3 na tom stojí („z cyklu by uzávěr odvodil, že je
            # všechno před vším"). Ireflexivita je táž věta, jen
            # o jednom uzlu.
            #
            # Hláška nemá co jmenovat — kruh netvoří žádný dřívější
            # výrok, tvoří ho tenhle sám se sebou.
            raise AttachError(
                f"{formula}: nic není dřív než ono samo. `before` je "
                f"striktní uspořádání, takže smyčka na sebe je kruh "
                f"o jednom uzlu a z cyklu by tranzitivní uzávěr odvodil, "
                f"že je všechno před vším (dodatek H‑3)."
            )
        proof = self.view().index.before_proof(later.target.id, earlier.target.id)
        if proof is None:
            return
        raise AttachError(
            f"{formula} by uzavřelo pořadí do kruhu — "
            f"{', '.join(sorted(proof.leaves()))} říká opak. Z cyklu by "
            f"tranzitivní uzávěr odvodil, že je všechno před vším "
            f"(dodatek H‑3), takže se to nezapisuje; odvolej jeden "
            f"z těch výroků, nebo tenhle nevyslovuj."
        )

    def _attach(
        self,
        formula: Formula,
        *,
        provenance: str = "",
        derived_from: str | None = None,
    ) -> str:
        """Zápis bez zábran u vchodu. Volá se **jen** z `attach` a z
        `add_disjoint`, která marker zapisuje jako součást své expanze."""
        if isinstance(formula, Rule):
            sid = formula.id
            if sid in self._statements:
                raise AttachError(f"pravidlo {sid!r} už v bázi je")
            self._validate_rules(formula)
            self._store(sid, formula, provenance, derived_from)
            return sid

        if not formula.is_ground():
            raise UnsafeRule(
                f"fakt {formula} obsahuje proměnné "
                f"{sorted(v.id for v in formula.variables())}; "
                f"proměnné patří jen do pravidel"
            )
        depth = self._nesting_depth(formula)
        if depth > self.max_depth:
            raise DepthExceeded(
                f"vztah {formula.predicate!r} má hloubku vnoření {depth}, "
                f"mez je {self.max_depth} (§ 12/3 zadání)"
            )
        if formula.predicate == P_SAME_AS and not formula.is_negated:
            self._validate_identity(formula)
        self._fact_counter += 1
        sid = f"s{self._fact_counter:04d}"
        self._store(sid, formula, provenance, derived_from)

        if not formula.is_negated and formula.predicate not in RESERVED_PREDICATES:
            self._depth[sid] = depth
            self._reify(sid, formula)
        return sid

    def attach_rule(
        self,
        head: Atom,
        body: tuple[Atom, ...],
        *,
        provenance: str = "",
        rule_id: str | None = None,
        derived_from: str | None = None,
    ) -> str:
        if rule_id is None:
            self._rule_counter += 1
            rule_id = f"p{self._rule_counter:04d}"
        return self.attach(
            Rule(id=rule_id, head=head, body=body),
            provenance=provenance,
            derived_from=derived_from,
        )

    def _store(
        self,
        sid: str,
        formula: Formula,
        provenance: str,
        derived_from: str | None,
    ) -> None:
        self._statements[sid] = Statement(
            id=sid, formula=formula, provenance=provenance, derived_from=derived_from
        )
        self._version += 1

    # -- reifikace (§ 2, dekompozice vztahu) -------------------------------

    def _reify(self, sid: str, a: Atom) -> None:
        """Fakt s nevyhrazeným predikátem JE vztah: založí se uzel
        `RelationInstance(sid)`, členství v `group(jméno)` a dekompozice
        rolí. Bez dekompozice nemá můstkové pravidlo `p3` na co sáhnout —
        `∃`-role nemá konkrétního svědka, takže se musí dát adresovat
        predikátem `role_exists`, ne funkcí."""
        instance = RelationInstance(sid)
        origin = f"reifikace {sid}"
        self._derived(member_of(instance, Group(a.predicate)), origin, sid)
        for r in a.canonical_roles():
            self._derived(role_atom(instance, r.name, r), origin, sid)

    def _derived(self, formula: Atom, provenance: str, source: str) -> None:
        self._fact_counter += 1
        self._store(
            f"s{self._fact_counter:04d}", formula, provenance, derived_from=source
        )

    def _nesting_depth(self, a: Atom) -> int:
        """0 = plochý vztah, 1 = postoj o faktu (`chtít(co: vztah(…))`)."""
        depth = 0
        for r in a.roles:
            if isinstance(r.target, RelationInstance):
                depth = max(depth, self._depth.get(r.target.id, 0) + 1)
        return depth

    # -- revoke ------------------------------------------------------------

    def revoke(self, sid: str, reason: str) -> list[str]:
        """Jediné mazání. Výrok zůstává v historii s důvodem; strhne s sebou
        vše, co z něj bylo odvozeno — tranzitivně."""
        if sid not in self._statements:
            raise KeyError(f"neznámý výrok {sid!r}")
        if sid in self._revoked:
            return []
        revoked = [sid]
        self._revoked[sid] = reason
        pending = [sid]
        while pending:
            source = pending.pop()
            for other in sorted(self._statements):
                st = self._statements[other]
                if st.derived_from == source and other not in self._revoked:
                    self._revoked[other] = f"odvozeno z {source}: {reason}"
                    revoked.append(other)
                    pending.append(other)
        self._version += 1
        return revoked

    # -- inspect -----------------------------------------------------------

    def inspect(self, sid: str) -> tuple[Statement, bool, str | None]:
        st = self._statements[sid]
        return st, sid not in self._revoked, self._revoked.get(sid)

    def derived_from(self, sid: str) -> list[Statement]:
        """Výroky, které z daného vznikly — reifikace, expanze `disjoint`."""
        return [st for st in self.active() if st.derived_from == sid]

    def active(self) -> Iterator[Statement]:
        for sid in sorted(self._statements):
            if sid not in self._revoked:
                yield self._statements[sid]

    def history(self) -> list[Statement]:
        return [self._statements[sid] for sid in sorted(self._statements)]

    def node_ids(self) -> frozenset[str]:
        """Všechna individua, která kdy vznikla zápisem. Evaluace k téhle
        množině nesmí přidat nic (§ 0/2)."""
        out: set[str] = set()
        for st in self.active():
            formulas = (
                [st.formula] if isinstance(st.formula, Atom)
                else [st.formula.head, *st.formula.body]
            )
            for f in formulas:
                for r in f.roles:
                    if not isinstance(r.target, Variable):
                        out.add(r.target.id)
        return frozenset(out)

    # -- pohled ------------------------------------------------------------

    def view(self) -> ResolvedGraphView:
        if self._view is None or self._view.version != self._version:
            facts: list[tuple[str, Atom]] = []
            rules: list[Rule] = []
            for st in self.active():
                if isinstance(st.formula, Rule):
                    rules.append(st.formula)
                else:
                    facts.append((st.id, st.formula))
            self._view = ResolvedGraphView(
                self._version, facts, self._stratified_order(rules)
            )
        return self._view

    # -- derivační constrainty (§ 5.3) -------------------------------------

    def add_disjoint(
        self, g1: GroupTerm, g2: GroupTerm, *, provenance: str = ""
    ) -> tuple[str, str, str]:
        """`disjoint(A,B)` se NEUKLÁDÁ jen jako kontrola `body -> ⊥`.

        Kontrolní tvar umí ohlásit konflikt, ale nikdy z něj nevznikne
        verdikt `N` — a dialog C („Je Hrabal stroj?" → NE) i test T7 ho
        vyžadují. Proto expanze na dvojici pravidel se silnou negací:

            ¬member(x, B) <- member(x, A)
            ¬member(x, A) <- member(x, B)
        """
        sid = self._attach(disjoint_of(g1, g2), provenance=provenance)
        x = Variable("x", expects=Sort.ENTITY)
        left = self.attach_rule(
            head=member_of(x, g2, negated=True),
            body=(member_of(x, g1),),
            provenance=f"expanze disjoint {sid}",
            derived_from=sid,
        )
        right = self.attach_rule(
            head=member_of(x, g1, negated=True),
            body=(member_of(x, g2),),
            provenance=f"expanze disjoint {sid}",
            derived_from=sid,
        )
        return sid, left, right

    # -- validace pravidel (§ 5.4/5, § 5.4/6) ------------------------------

    def _active_rules(self) -> list[Rule]:
        return [st.formula for st in self.active() if isinstance(st.formula, Rule)]

    def _canonical_map(
        self, extra: tuple[str, str] | None = None
    ) -> dict[str, str]:
        """Třídy ekvivalence z aktivních `same_as` hran, volitelně s jednou
        navrženou hranou navíc — pro validaci ještě před zápisem."""
        graph = nx.Graph()
        for statement in self.active():
            formula = statement.formula
            if not isinstance(formula, Atom):
                continue
            if formula.predicate != P_SAME_AS or formula.is_negated:
                continue
            left, right = formula.get_role("left"), formula.get_role("right")
            if left and right:
                graph.add_edge(left.target.id, right.target.id)
        if extra is not None:
            graph.add_edge(*extra)
        canon: dict[str, str] = {}
        for component in nx.connected_components(graph):
            representative = min(component)
            for node in component:
                canon[node] = representative
        return canon

    @staticmethod
    def _build_graphs(
        rules: Iterable[Rule], canon: Mapping[str, str]
    ) -> tuple[nx.DiGraph, nx.DiGraph]:
        """Dva grafy, ne jeden.

        * **pozitivní** — jen nenegované literály; jeho acykličnost je
          § 5.4/5 („rekurze patří jen do jádra").
        * **stratifikační** — všechny literály; negovaná hrana žádá
          STRIKTNĚ nižší stratum (§ 5.4/6). Z něj plyne i pořadí
          vyhodnocení, aby se negovaný literál četl až po dokončení
          nižšího strata.

        Hrany se stavějí **unifikací, ne rovností klíčů**. Literál v těle je
        závislý na každém pravidle, jehož hlava by ho mohla splnit — a `*`
        (proměnná) se snoubí s libovolnou konstantou. Rovnost klíčů by
        `p(out:*)` a `p(out:a)` prohlásila za různé uzly, hrana by nevznikla
        a rekurze by prošla validací.

        Nenegovaný jádrový predikát v těle je stratum 0 — list, ne uzel.
        """
        rules = list(rules)
        heads = [(rule, rule.head.dependency_key()) for rule in rules]
        positive = nx.DiGraph()
        strata = nx.DiGraph()
        for _, head in heads:
            positive.add_node(head)
            strata.add_node(head)

        for rule in rules:
            target = rule.head.dependency_key()
            for body_atom in rule.body:
                if (
                    body_atom.predicate in KERNEL_PREDICATES
                    and not body_atom.is_negated
                ):
                    continue
                key = body_atom.dependency_key()
                producers = [
                    head for _, head in heads if _unifies(key, head, canon)
                ]
                if not producers:
                    # Literál, který žádné pravidlo nevyrábí — základní fakta,
                    # tedy list bez příchozí hrany.
                    strata.add_node(key)
                    if not body_atom.is_negated:
                        positive.add_node(key)
                    continue
                for source in producers:
                    if strata.has_edge(source, target):
                        strata.edges[source, target]["strict"] |= body_atom.is_negated
                    else:
                        strata.add_edge(source, target, strict=body_atom.is_negated)
                    if not body_atom.is_negated:
                        positive.add_edge(source, target)
        return positive, strata

    @staticmethod
    def _strata_levels(strata: nx.DiGraph) -> dict[DependencyKey, int]:
        levels: dict[DependencyKey, int] = {node: 0 for node in strata}
        edges = sorted(
            strata.edges(data=True), key=lambda e: (str(e[0]), str(e[1]))
        )
        for _ in range(len(levels) + 1):
            changed = False
            for source, target, data in edges:
                want = levels[source] + (1 if data["strict"] else 0)
                if want > levels[target]:
                    levels[target] = want
                    changed = True
            if not changed:
                return levels
        raise CycleDetected(
            "stratifikace neexistuje: cyklus obsahující negovaný literál "
            "(§ 5.4/6)"
        )

    def _cache(self, rules: list[Rule], canon: Mapping[str, str]) -> _GraphCache:
        """Stavba grafů se zapamatuje.

        Grafy závisí **jen** na množině pravidel a na třídách ekvivalence,
        takže zápis faktu je nemění — a faktů je v dialogu řádově víc než
        pravidel. Bez toho se oba grafy stavěly od nuly při každém `attach`
        pravidla i při každém scelení identity, což bylo jediné místo, kde
        náklad rostl kvadraticky s délkou rozhovoru.
        """
        key: _GraphKey = (
            tuple(rule.id for rule in rules),
            tuple(sorted(canon.items())),
        )
        cached = self._graph_cache
        if cached is not None and cached.key == key:
            return cached
        self.graph_builds += 1
        positive, strata = self._build_graphs(rules, canon)
        fresh = _GraphCache(key=key, positive=positive, strata=strata)
        self._graph_cache = fresh
        return fresh

    def _levels(self, cache: _GraphCache) -> dict[DependencyKey, int]:
        if cache.levels is None:
            cache.levels = self._strata_levels(cache.strata)
        return cache.levels

    def _validate_rules(
        self,
        candidate: Rule | None = None,
        *,
        canon: Mapping[str, str] | None = None,
        because: str = "",
    ) -> None:
        rules = self._active_rules()
        if candidate is not None:
            rules = [*rules, candidate]
        if canon is None:
            canon = self._canonical_map()
        cache = self._cache(rules, canon)
        # Acykličnost pozitivního grafu se kontroluje PŘED stratifikací, aby
        # hláška ukázala na cyklus, ne na chybějící strata.
        if not nx.is_directed_acyclic_graph(cache.positive):
            subject = (
                f"pravidlo {candidate.id!r}" if candidate is not None else because
            )
            cycle = nx.find_cycle(cache.positive)
            path = " -> ".join(_render_key(edge[0]) for edge in cycle)
            self._graph_cache = None  # odmítnutý stav si nepamatujeme
            raise CycleDetected(
                f"{subject} by uzavřel(o) pozitivní cyklus: {path}; "
                f"rekurze patří jen do jádra (§ 5.4/5)"
            )
        try:
            self._levels(cache)
        except CycleDetected:
            self._graph_cache = None
            raise

    def _validate_identity(self, formula: Atom) -> None:
        """Scelení identity je **odmítnutelná operace** (rozhodnutí B‑IV).

        Dvě dosud různé konstanty se scelením stanou jednou, takže hrana
        dependency grafu, která do té chvíle nevznikla, vzniknout může —
        a s ní cyklus. Validuje se proti NAVRŽENÝM třídám ještě před
        zápisem, aby odmítnutá hrana v bázi nezůstala.
        """
        left, right = formula.get_role("left"), formula.get_role("right")
        if left is None or right is None:
            return
        pair = (left.target.id, right.target.id)
        self._validate_rules(
            canon=self._canonical_map(pair),
            because=f"scelení {pair[0]!r} a {pair[1]!r}",
        )

    def _stratified_order(self, rules: list[Rule]) -> list[Rule]:
        """Pořadí, ve kterém jeden průchod stačí.

        Stratum samo nestačí: nestriktní hrany stratum nezvyšují, takže
        pozitivní řetěz `a0 → a1 → … → aN` by měl všechna pravidla ve
        stratu 0 a jejich pořadí by rozhodlo id — při nešťastném pořadí
        zápisu by pevný bod potřeboval jedno kolo na článek. Řadí se proto
        topologicky nad CELÝM stratifikačním grafem; ten je DAG, protože
        pozitivní cykly odmítá `_validate_rules` a cykly se striktní hranou
        neprojdou stratifikací.
        """
        if not rules:
            return []
        cache = self._cache(rules, self._canonical_map())
        levels = self._levels(cache)
        position = {
            key: index
            for index, key in enumerate(
                nx.lexicographical_topological_sort(cache.strata, key=lambda k: k)
            )
        }
        return sorted(
            rules,
            key=lambda r: (
                levels.get(r.head.dependency_key(), 0),
                position.get(r.head.dependency_key(), 0),
                r.id,
            ),
        )


def _unifies(
    left: DependencyKey, right: DependencyKey, canon: Mapping[str, str]
) -> bool:
    """Mohl by literál s klíčem `left` být splněn faktem s klíčem `right`?

    `*` (proměnná) se snoubí s čímkoli; dvě různé konstanty v téže roli
    kolidují. Role, kterou nese jen jedna strana, se neporovnává — role
    navíc ve faktu shodě nevadí (§ 3.4 zadání).

    Konstanty se porovnávají **přes aktuální třídy ekvivalence**, ne
    syntakticky. Bez toho by `ga` a `gb` zůstaly různé i poté, co je
    `same_as` scelí, a cyklus schovaný za identitou by prošel validací —
    samotné zopakování validace po `attach(same_as)` by na tom nic
    nezměnilo, protože by pořád porovnávalo syrová id.
    """
    if left[0] != right[0] or left[1] != right[1]:
        return False
    left_roles = dict(left[2])
    right_roles = dict(right[2])
    for name in left_roles.keys() & right_roles.keys():
        a, b = left_roles[name], right_roles[name]
        if a == "*" or b == "*":
            continue
        if canon.get(a, a) != canon.get(b, b):
            return False
    return True


def _render_key(key: DependencyKey) -> str:
    predicate, negated, fillers = key
    args = ",".join(f"{name}:{value}" for name, value in fillers)
    return f"{'¬' if negated else ''}{predicate}({args})"
