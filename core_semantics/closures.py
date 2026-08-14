"""Jádrové uzávěry — Core Semantics 0.1, § 5.1.

Jediné místo v systému, kde je rekurze. Uzávěry jsou nativní algoritmy
jádra nad konečným grafem; pro evaluátor naučených pravidel jsou to
primitivní predikáty stratu 0, ne uzly dependency grafu (§ 5.4/5).

Terminace je vlastnost konstrukce: uzávěry jsou monotónní, běží nad
konečnou množinou deklarovaných uzlů a NEGENERUJÍ nová individua (§ 0/2).

Každý použitý krok uzávěru je hrana v důkazu, ne skrytá normalizace
(§ 3.3) — proto všechny dotazovací metody vracejí `Proof`, ne `bool`.

**Identita se nesléva.** Index staví nad SUROVÝMI id; hrany `same_as` se
přidávají do grafů uzávěrů jako obousměrné hrany, takže cesta, která jimi
prošla, je cituje jako běžné fakty. Kdyby se id kolabovala na kanonického
zástupce už při stavbě, důkaz by o použité identitní hraně mlčel (§ 8).

Předpoklad: `id` uzlů jsou v bázi globálně jedinečná napříč sorty.
"""

from __future__ import annotations

from typing import Iterable, Mapping

import networkx as nx

from .ast import (
    Atom,
    GroupAnd,
    GroupDiff,
    P_COMPLETE,
    P_BEFORE,
    P_CONTAINS,
    P_DISJOINT,
    P_MEMBER,
    P_NAME,
    P_SAME_AS,
    P_SUBSET,
    P_WITHIN,
    Proof,
    ProofKind,
    Sort,
    Term,
    select_canonical,
)

_REFL_SUFFIX = "/refl"


class InconsistentOrder(RuntimeError):
    """Uspořádání na časové ose si odporuje.

    `before(a,b)` a `before(b,a)` dají tranzitivním uzávěrem `before(a,a)`
    — a pak je všechno před vším. Dotaz „jel dřív do Prahy?" i „…do Brna?"
    by oba vrátily `A` a nebylo by na tom nic vidět.

    **Konzervativní default (dodatek H‑3):** uzávěr cyklus detekuje a
    NETIŠE NEODPOVÍ. Zapojení na `CONFLICT` s oběma důkazy je nový druh
    inference v jádře a čeká na rozhodnutí člověka; do té doby je to
    hlášená chyba, jako u nevázaných rolí.
    """


# --------------------------------------------------------------------------
# Deterministické hledání cesty
# --------------------------------------------------------------------------


def _neighbors(graph: nx.Graph | nx.DiGraph, node: str) -> list[str]:
    it = graph.successors(node) if graph.is_directed() else graph.neighbors(node)
    return sorted(it)


#: Krok cesty: id výroku a druh hrany (`subset` / `contains` / `within`
#: / `same_as`). Druh se nese proto, aby identitní krok šel v důkazu
#: pojmenovat vlastním uzlem místo aby se vydával za podmnožinový (§ 3.3).
Step = tuple[str, str]


def _bfs_path(graph: nx.Graph | nx.DiGraph, src: str, dst: str) -> list[Step] | None:
    """Nejkratší cesta jako seznam kroků.

    Determinismus (I‑4): sousedé i fronta se procházejí setříděně, takže
    mezi stejně dlouhými cestami vyhraje vždy táž.
    Vrací `[]` pro `src == dst`, `None` když cesta neexistuje.
    """
    if src == dst:
        return []
    if src not in graph or dst not in graph:
        return None
    prev: dict[str, tuple[str, Step] | None] = {src: None}
    frontier = [src]
    while frontier:
        nxt: list[str] = []
        for u in frontier:
            for v in _neighbors(graph, u):
                if v in prev:
                    continue
                edge = graph.edges[u, v]
                prev[v] = (u, (edge["stmt"], edge["kind"]))
                if v == dst:
                    return _reconstruct(prev, dst)
                nxt.append(v)
        frontier = sorted(nxt)
    return None


def _reconstruct(
    prev: Mapping[str, tuple[str, Step] | None], dst: str
) -> list[Step]:
    out: list[Step] = []
    cur = dst
    while (step := prev[cur]) is not None:
        u, edge = step
        out.append(edge)
        cur = u
    out.reverse()
    return out


def _cyclic_nodes(graph: nx.DiGraph) -> frozenset[str]:
    """Uzly ležící na cyklu — silně souvislé komponenty > 1 plus smyčky."""
    found: set[str] = set()
    for component in nx.strongly_connected_components(graph):
        if len(component) > 1:
            found |= component
    found |= {node for node in graph.nodes if graph.has_edge(node, node)}
    return frozenset(found)


def _closure(label: str, steps: list[Step]) -> Proof:
    """Sestaví důkaz uzávěru. Identitní krok dostane VLASTNÍ uzel
    `closure(same_as*)` — cesta smí vést přes rovnost, ale nesmí se
    tvářit, že to byl podmnožinový krok (I‑14)."""
    if not steps:
        return Proof(ProofKind.CLOSURE, label + _REFL_SUFFIX)
    premises: list[Proof] = []
    for stmt, kind in steps:
        fact = Proof(ProofKind.FACT, stmt)
        premises.append(
            Proof(ProofKind.CLOSURE, "same_as*", (fact,))
            if kind == P_SAME_AS
            else fact
        )
    return Proof(ProofKind.CLOSURE, label, tuple(premises))


def _is_reflexive(proof: Proof | None) -> bool:
    return proof is not None and proof.ref.endswith(_REFL_SUFFIX)


# --------------------------------------------------------------------------
# Index uzávěrů
# --------------------------------------------------------------------------


class ClosureIndex:
    """Postavený nad AKTIVNÍMI výroky. Revoke nemění uložená fakta — jen se
    index při další evaluaci postaví znovu bez odvolané hrany (§ 8)."""

    def __init__(self, facts: Iterable[tuple[str, Atom]]) -> None:
        self._same_as = nx.Graph()
        self._subset = nx.DiGraph()  # hrana sub -> sup
        self._contains = nx.DiGraph()  # hrana whole -> part (Place)
        self._within = nx.DiGraph()  # hrana whole -> part (Time)
        self._before = nx.DiGraph()  # hrana earlier -> later (Time)
        self._member: dict[str, dict[str, str]] = {}  # elem -> {group: stmt}
        self._complete: dict[str, str] = {}  # group -> stmt
        self._sorts: dict[str, Sort] = {}  # id -> sort, pro sortové stráže
        # Marker `disjoint` je v bázi uložený JEDNOSMĚRNĚ, ale relace
        # symetrická je — indexuje se proto v obou směrech. Jinak by
        # `vrabec ⊆ pták DIFF tučňák` platilo jen podle toho, v jakém
        # pořadí člověk oddělenost vyslovil (§ 5.2.1, dodatek E).
        self._disjoint: dict[tuple[str, str], str] = {}

        #: Termy podle id — algebraický term není uzel grafu, takže se
        #: k jeho struktuře jinak nelze dostat.
        self._terms_by_id: dict[str, Term] = {}
        for _, a in facts:
            for r in a.roles:
                if r.target.SORT is not Sort.VARIABLE:
                    self._sorts.setdefault(r.target.id, r.target.SORT)
                    self._terms_by_id.setdefault(r.target.id, r.target)

        #: Dvojice, u kterých je identita POPŘENÁ. Sbírá se předem, protože
        #: `¬same_as` může v bázi ležet až za `same_as` a pořadí zápisu
        #: nesmí měnit, co uzávěr udělá (I‑4).
        self._denied_identity: set[frozenset[str]] = set()
        for sid, a in facts:
            if a.predicate == P_SAME_AS and a.is_negated:
                left, right = a.get_role("left"), a.get_role("right")
                if left and right:
                    self._denied_identity.add(
                        frozenset((left.target.id, right.target.id))
                    )
        #: Dvojice, o kterých báze tvrdí obojí — `p` i `p̄`.
        self._disputed_identity: dict[frozenset[str], tuple[str, ...]] = {}

        #: Jméno → uzly, které ho doloženě nesou.
        self._named: dict[str, set[str]] = {}
        for sid, a in facts:
            if a.predicate == P_NAME and not a.is_negated:
                bearer, label = a.get_role("of"), a.get_role("value")
                if bearer and label:
                    self._named.setdefault(label.target.id, set()).add(
                        bearer.target.id
                    )

        for sid, a in facts:
            if a.is_negated:
                continue  # negovaný atom není hrana uzávěru
            if a.predicate == P_SAME_AS:
                left, right = a.get_role("left"), a.get_role("right")
                if left and right:
                    u, v = left.target.id, right.target.id
                    if frozenset((u, v)) in self._denied_identity:
                        # M‑1. Přímá otázka na tuhle identitu vrací
                        # `CONFLICT`, ale uzávěr ji dosud používal DÁL —
                        # fakty tekly přes hranu, o které báze ví, že je
                        # sporná, a odpověď vycházela jako tiché `A`.
                        # To je tichá volba měnící význam (I‑1): systém se
                        # rozhodl, které z dvou neslučitelných tvrzení
                        # platí, a nikomu to neřekl.
                        #
                        # Sporná hrana se proto NEPOUŽIJE. Odpověď tím
                        # spadne na `U` — tedy na „nevím", což je pravda:
                        # dokud spor trvá, nevíme, jestli jsou to tíž.
                        self._disputed_identity.setdefault(
                            frozenset((u, v)), ()
                        )
                        self._disputed_identity[frozenset((u, v))] += (sid,)
                        continue
                    self._add_edge(self._same_as, u, v, sid, P_SAME_AS)
                    # Rovnost musí umět přemostit řetěz UPROSTŘED:
                    # `Ford ⊆ Automobil ≡ Auto ⊆ Vozidlo`. Kolaps tříd jen
                    # na koncích cesty by tenhle případ minul. Hrana se
                    # proto vkládá i do grafů uzávěrů — ale se svým DRUHEM,
                    # takže se v důkazu pojmenuje `closure(same_as*)` a
                    # nevydává se za podmnožinový krok (§ 3.3, I‑14).
                    for graph in (
                        self._subset,
                        self._contains,
                        self._within,
                        self._before,
                    ):
                        self._add_edge(graph, u, v, sid, P_SAME_AS)
                        self._add_edge(graph, v, u, sid, P_SAME_AS)
            elif a.predicate == P_SUBSET:
                sub, sup = a.get_role("sub"), a.get_role("sup")
                if sub and sup:
                    self._add_edge(
                        self._subset, sub.target.id, sup.target.id, sid, P_SUBSET
                    )
            elif a.predicate in (P_CONTAINS, P_WITHIN):
                whole, part = a.get_role("whole"), a.get_role("part")
                if whole and part:
                    graph = (
                        self._contains if a.predicate == P_CONTAINS else self._within
                    )
                    self._add_edge(
                        graph, whole.target.id, part.target.id, sid, a.predicate
                    )
            elif a.predicate == P_MEMBER:
                elem, group = a.get_role("elem"), a.get_role("group")
                if elem and group:
                    slot = self._member.setdefault(elem.target.id, {})
                    g = group.target.id
                    if g not in slot or sid < slot[g]:
                        slot[g] = sid
            elif a.predicate == P_BEFORE:
                earlier, later = a.get_role("earlier"), a.get_role("later")
                if earlier and later:
                    self._add_edge(
                        self._before,
                        earlier.target.id,
                        later.target.id,
                        sid,
                        P_BEFORE,
                    )
            elif a.predicate == P_DISJOINT:
                first, second = a.get_role("a"), a.get_role("b")
                if first and second:
                    u, v = first.target.id, second.target.id
                    for pair in ((u, v), (v, u)):
                        if pair not in self._disjoint or sid < self._disjoint[pair]:
                            self._disjoint[pair] = sid
            elif a.predicate == P_COMPLETE:
                group = a.get_role("group")
                if group:
                    g = group.target.id
                    if g not in self._complete or sid < self._complete[g]:
                        self._complete[g] = sid

        # Obrácený index členství: skupina → prvky, včetně nadskupin a skupin
        # scelených přes `same_as` (ty jsou v `_subset` jako obousměrné hrany).
        # `known_members` je hot path výčtových otázek (§ 6.4) a bez tohohle
        # indexu stál BFS na každý deklarovaný pár prvek–skupina.
        self._members_of: dict[str, set[str]] = {}
        for element, declared_groups in self._member.items():
            for declared in declared_groups:
                targets = {declared} | self._implied_supersets(declared)
                for direct in list(targets):
                    if direct in self._subset:
                        targets |= nx.descendants(self._subset, direct)
                for target in targets:
                    self._members_of.setdefault(target, set()).add(element)

        # Uzly, které leží na cyklu uspořádání. Detekce je při stavbě, ale
        # dopad je jen na dotazy o těchto uzlech — cyklus jinde na ose
        # nemá blokovat nesouvisející otázku (dodatek H‑3).
        self._ordering_cycles: frozenset[str] = _cyclic_nodes(self._before)

        self._canon: dict[str, str] = {}
        self._classes: dict[str, list[str]] = {}
        for component in nx.connected_components(self._same_as):
            representative = min(component)  # § 8: kanonický = nejnižší id
            self._classes[representative] = sorted(component)
            for node in component:
                self._canon[node] = representative

    def _implied_supersets(self, group_id: str) -> set[str]:
        """Nadmnožiny, které plynou ze STRUKTURY algebraického termu.

        Jen sound směr ze zákonů § 5.2.1(b): `A AND B ⊆ A` i `⊆ B`,
        `A DIFF B ⊆ A`. Pro `OR` se nepropaguje nic — `A OR B ⊆ A`
        neplatí a propagace by byla právě ta zakázaná eliminace disjunkce.
        """
        term = self._terms_by_id.get(group_id)
        if term is None:
            return set()
        found: set[str] = set()
        stack: list[Term] = [term]
        while stack:
            current = stack.pop()
            if isinstance(current, GroupAnd):
                for operand in current.operands:
                    found.add(operand.id)
                    stack.append(operand)
            elif isinstance(current, GroupDiff):
                found.add(current.left.id)
                stack.append(current.left)
        return found

    @staticmethod
    def _add_edge(
        graph: nx.Graph | nx.DiGraph, u: str, v: str, sid: str, kind: str
    ) -> None:
        # Při dvojím doložení téže hrany držíme lexikograficky nižší id výroku
        # — jinak by kanonický důkaz závisel na pořadí vkládání. Přímá hrana
        # má přednost před identitní: je to kratší a přesnější vysvětlení.
        if graph.has_edge(u, v):
            existing = graph.edges[u, v]
            if existing["kind"] != P_SAME_AS and kind == P_SAME_AS:
                return
            if existing["kind"] == kind and existing["stmt"] <= sid:
                return
        graph.add_edge(u, v, stmt=sid, kind=kind)

    # -- identita ----------------------------------------------------------

    def canonical(self, node_id: str) -> str:
        """Zástupce třídy ekvivalence. Slouží k počítání a k deduplikaci,
        NE k přepsání uložených faktů."""
        return self._canon.get(node_id, node_id)

    def class_of(self, node_id: str) -> list[str]:
        return self._classes.get(self.canonical(node_id), [node_id])

    def sort_of(self, node_id: str) -> Sort | None:
        return self._sorts.get(node_id)

    def _sort_ok(self, node_id: str, expected: Sort) -> bool:
        """Sortová stráž uzávěru. Neznámé id projde — reflexivita musí platit
        i pro uzly, o kterých báze zatím nic neví."""
        actual = self._sorts.get(node_id)
        return actual is None or actual is expected

    def same_class(self, a_id: str, b_id: str) -> Proof | None:
        edges = _bfs_path(self._same_as, a_id, b_id)
        if edges is None:
            return None
        return _closure("same_as*", edges)

    def identity_proof(self, a_id: str, b_id: str) -> Proof | None:
        """Odpověď na PŘÍMOU otázku „je to týž uzel?".

        Liší se od `same_class` v jediné, ale podstatné věci: **sporná
        hrana se tu započítá.** Výrok `same_as(A,B)` v bázi je, a když
        vedle něj leží `¬same_as(A,B)`, je správná odpověď `CONFLICT` —
        ne `N`. Odebírá se POUŽITÍ hrany v uzávěru, ne sám výrok; kdyby
        zmizel i z přímé odpovědi, systém by spor zametl místo aby ho
        ohlásil (I‑3).
        """
        direct = self.same_class(a_id, b_id)
        if direct is not None:
            return direct
        sids = self._disputed_identity.get(frozenset((a_id, b_id)))
        if not sids:
            return None
        return Proof(ProofKind.FACT, min(sids))

    def equivalence_classes(self) -> dict[str, list[str]]:
        classes: dict[str, list[str]] = {}
        for node, rep in self._canon.items():
            classes.setdefault(rep, []).append(node)
        return {rep: sorted(members) for rep, members in sorted(classes.items())}

    # -- uzávěry -----------------------------------------------------------

    def _closure_proof(
        self,
        graph: nx.Graph | nx.DiGraph,
        src_id: str,
        dst_id: str,
        label: str,
        expected: Sort,
    ) -> Proof | None:
        """Uzávěr počítaný PŘES třídy ekvivalence.

        Identita se aplikuje tady, na dotaz, a v důkazu se vede samostatným
        uzlem `closure(same_as*)` — ne jako podmnožinový či prostorový krok.
        """
        if not self._sort_ok(src_id, expected) or not self._sort_ok(dst_id, expected):
            return None
        steps = _bfs_path(graph, src_id, dst_id)
        return None if steps is None else _closure(label, steps)

    def subset_proof(self, sub_id: str, sup_id: str) -> Proof | None:
        """`subset*` — reflexivně-tranzitivní uzávěr nad sortem Group."""
        return self._closure_proof(
            self._subset, sub_id, sup_id, "subset*", Sort.GROUP
        )

    def contains_proof(self, whole_id: str, part_id: str) -> Proof | None:
        """`contains*` nad sortem Place. NENÍ to `subset*` — místa nejsou
        množiny (§ 1); grafy i sortové stráže jsou proto oddělené."""
        return self._closure_proof(
            self._contains, whole_id, part_id, "contains*", Sort.PLACE
        )

    def within_proof(self, whole_id: str, part_id: str) -> Proof | None:
        """`within*` nad sortem Time — obsažení intervalů."""
        return self._closure_proof(
            self._within, whole_id, part_id, "within*", Sort.TIME
        )

    def before_proof(self, earlier_id: str, later_id: str) -> Proof | None:
        """`before*` — tranzitivní uzávěr uspořádání, striktně nad `Time`.

        **Není reflexivní.** „Pondělí je před pondělím" neplatí, a kdyby
        uzávěr reflexivitu přidal, splynulo by „dřív" s „nejpozději".
        """
        for node in (earlier_id, later_id):
            if node in self._ordering_cycles:
                raise InconsistentOrder(
                    f"uspořádání kolem {node!r} si odporuje — z cyklu by "
                    f"tranzitivní uzávěr odvodil, že je všechno před vším; "
                    f"neodpovídám, dokud se to nevyřeší (dodatek H‑3)"
                )
        if not self._sort_ok(earlier_id, Sort.TIME) or not self._sort_ok(
            later_id, Sort.TIME
        ):
            return None
        if earlier_id == later_id:
            return None
        steps = _bfs_path(self._before, earlier_id, later_id)
        return None if steps is None else _closure("before*", steps)

    def ordering_cycles(self) -> frozenset[str]:
        return self._ordering_cycles

    def member_proof(self, elem_id: str, group_id: str) -> Proof | None:
        """`member*`: member(x,A) ∧ subset*(A,B) ⇒ member(x,B).

        Prochází i členství doložená o jiném prvku téže třídy ekvivalence —
        a identitní hranu pak cituje v důkazu."""
        candidates: list[Proof] = []
        for raw_elem in self.class_of(elem_id):
            link = self.same_class(elem_id, raw_elem)
            for declared, sid in sorted(self._member.get(raw_elem, {}).items()):
                step = self.subset_proof(declared, group_id)
                if step is None:
                    continue
                premises = [Proof(ProofKind.FACT, sid)]
                # Reflexivní kroky nenesou žádný výrok — do vysvětlení
                # nepatří, jen by ho zaplevelily („triviálně, jde o tutéž
                # věc" pod každým členstvím).
                if step.leaves():
                    premises.append(step)
                if link is not None and not _is_reflexive(link):
                    premises.append(link)
                candidates.append(
                    Proof(ProofKind.CLOSURE, "member*", tuple(premises))
                )
        return select_canonical(candidates)

    # -- extenze -----------------------------------------------------------

    def known_members(self, group_id: str) -> list[str]:
        """Doložení členové jako KANONIČTÍ ZÁSTUPCI tříd — dolní odhad
        `K(g)`, ne `M(g)` (§ 3.1).

        Bez UNA (§ 1.2 podkladu) je počet tříd tím, co lze poctivě
        spočítat: „znám dvě, pokud to není totéž dvakrát."
        """
        return sorted(
            {self.canonical(elem) for elem in self._members_of.get(group_id, ())}
        )

    def nodes_named(self, name: str) -> list[str]:
        """Uzly, které to jméno DOLOŽENĚ nesou (`name(of, value)`).

        Kanonizace jmen se ptá sem, ne na shodu id s lemmatem. Rozdíl je
        vidět po rozdělení uzlu: jméno „Petr" pak nese víc uzlů, a
        ztotožnit další zmínku s kterýmkoli z nich by bylo rozhodnutí,
        které člověk právě VÝSLOVNĚ odmítl udělat."""
        return sorted(self._named.get(name, set()))

    def knows(self, node_id: str) -> bool:
        """Vystupuje ten uzel v nějakém aktivním výroku?

        Neptá se na členství ani na typ — jen na to, jestli o něm už řeč
        byla. Na tom stojí rozlišení „zakládám nový uzel" × „mluvím o tom,
        co znám", a to je rozdíl, který § 0.2 hlídá."""
        return node_id in self._terms_by_id

    def disputed_identities(self) -> tuple[tuple[str, str], ...]:
        """Dvojice, jejichž identita je ve SPORU, takže se hrana nepoužila.

        Není to jen účetnictví: bez tohohle by odpověď spadla z `A` na `U`
        a nikdo by se nedozvěděl PROČ. Mezera, kterou nejde vysvětlit, je
        skoro tak špatná jako tichá odpověď (I‑14)."""
        return tuple(
            sorted(tuple(sorted(pair)) for pair in self._disputed_identity)  # type: ignore[misc]
        )

    def identity_is_disputed(self, first_id: str, second_id: str) -> bool:
        return frozenset((first_id, second_id)) in self._disputed_identity

    def disputed_with(self, node_id: str) -> tuple[str, ...]:
        """Uzly, se kterými je identita daného uzlu ve sporu."""
        found = [
            next(iter(pair - {node_id}), node_id)
            for pair in self._disputed_identity
            if node_id in pair
        ]
        return tuple(sorted(found))

    def disjoint_proof(self, first_id: str, second_id: str) -> Proof | None:
        """Doložená oddělenost dvou skupin, hledaná v OBOU směrech.

        Marker `disjoint(a:g1, b:g2)` je v bázi jednosměrný, ale relace
        symetrická je. Kdyby se hledal jen jeden směr, závisel by závěr na
        pořadí, ve kterém člověk oddělenost vyslovil — přesně ta tichá
        závislost na formulaci, které má systém bránit.

        **Přijatá neúplnost:** hledá se doložený marker, ne odvozená
        oddělenost. Tranzitivní tvary (`X ⊆ C ∧ disjoint(C,B)`, případně
        `disjoint(X,C) ∧ B ⊆ C`) marker v bázi nemají, takže vyjdou `U` —
        bezpečná strana, konzistentní se záměrnou neúplností celé sady.
        """
        for first in self.class_of(first_id):
            for second in self.class_of(second_id):
                sid = self._disjoint.get((first, second))
                if sid is not None:
                    return Proof(
                        ProofKind.CLOSURE, "disjoint", (Proof(ProofKind.FACT, sid),)
                    )
        return None

    def declared_memberships(self, elem_id: str) -> list[tuple[str, str]]:
        """Přímo deklarovaná členství prvku jako `(skupina, výrok)`, včetně
        těch zapsaných o jiném prvku téže třídy ekvivalence.

        Slouží k tomu, aby se členství doložené pod ALGEBRAICKÝM termem
        dalo přenést na jeho nadmnožinu — id-graf uzávěrů algebraické termy
        jako uzly nezná."""
        found: list[tuple[str, str]] = []
        for raw in self.class_of(elem_id):
            found.extend(sorted(self._member.get(raw, {}).items()))
        return found

    def known_groups_of(self, elem_id: str) -> list[str]:
        """Skupiny, ve kterých je prvek doloženě členem — včetně nadskupin
        a skupin scelených přes `same_as`. Podklad pro definiční otázku
        „Co je X?" (§ 6.5), jejíž odpověď je syntéza okolí uzlu."""
        found: set[str] = set()
        for raw in self.class_of(elem_id):
            for declared in self._member.get(raw, {}):
                found.add(declared)
                if declared in self._subset:
                    found.update(nx.descendants(self._subset, declared))
        return sorted(found)

    def element_sorts(self, group_id: str) -> frozenset[Sort]:
        """Sorty prvků, které ve skupině doloženě JSOU.

        § 1 zavádí `Group[T]`, ale term `Group` v kódu parametr nenese —
        identita skupiny je jen její `id` a přidat sort do termu by
        rozbilo rovnost `Group("x") == Group("x")` napříč místy, kde se
        sort neuvádí. Sort se proto vede jako **vlastnost skupiny
        odvozená z báze**, ne jako součást termu.

        Používá se k zúžení kandidátů ve výčtu: do `group("pacient")`
        nemá co kandidovat instance vztahu. Naopak `group("jezdí_po")`
        instance vztahů obsahuje zcela legitimně (§ 3.4 „typ vztahu =
        group jeho instancí"), takže filtr podle pevného seznamu sortů
        by tuhle schopnost zabil.

        Mez: skupina se smíšenými sorty se pozná až podle toho, co v ní
        už doloženo je; prázdná skupina nevrací nic a odpověď to musí
        přiznat, místo aby nabídla celou doménu.
        """
        sorts = {
            self._sorts[member]
            for member in self.known_members(group_id)
            if member in self._sorts
        }
        return frozenset(sorts)

    def complete_groups(self) -> list[tuple[str, str]]:
        """Skupiny, o kterých je doložena úplnost, jako `(id, výrok)`."""
        return sorted(self._complete.items())

    def is_complete(self, group_id: str) -> str | None:
        """Id výroku `complete(g)`, pokud existuje. Jen s ním smí evaluace
        prohlásit `K(g) = M(g)` (§ 3.1)."""
        for node in self.class_of(group_id):
            if node in self._complete:
                return self._complete[node]
        return None
