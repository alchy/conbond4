"""Evaluátor — Core Semantics 0.1, § 3.3 (shoda), § 5.2 (distribuce),
§ 5.5 (least closure), § 4 (verdikty).

Engine je **čistě čtecí**. Nezakládá individua ani nezapisuje do báze:
reifikace vztahů se odehrává v `KnowledgeBase.attach` (§ 0/2), takže každý
uzel má id výroku, provenienci a dosáhne na něj `inspect` i `revoke`.

Dvě konstrukční rozhodnutí, která stojí za vysvětlení:

1. **D1/D2 nejsou v pevném bodě, ale v relaci shody `⪯`.** Dopředná
   materializace by pro každou ∀-roli vyrobila fakt pro KAŽDOU podmnožinu —
   u více ∀-rolí součin. § 3.3 distribuci definuje přesně jako součást
   párování, takže se aplikuje na vyžádání, výsledek je týž a důkaz cituje
   jen skutečně použité kroky.

2. **Pořadí pravidel se sem nepočítá.** Stratifikované pořadí dodává
   `ResolvedGraphView.rules`; § 5.4/5 a § 5.4/6 tak žijí na jednom místě
   (storage.py), ne na dvou, která se můžou rozejít.
"""

from __future__ import annotations

from typing import Iterator

from .ast import (
    ALGEBRAIC,
    Atom,
    AttachError,
    Gap,
    GroupAnd,
    GroupDiff,
    GroupOr,
    Interval,
    KERNEL_PREDICATES,
    Label,
    P_BEFORE,
    P_CONTAINS,
    P_MEMBER,
    P_COMPLETE,
    P_DISJOINT,
    P_NAME,
    P_SAME_AS,
    P_SUBSET,
    P_WITHIN,
    Place,
    Proof,
    ProofKind,
    Quantifier,
    QueryResult,
    QueryStatus,
    RoleTerm,
    Rule,
    Term,
    UnsafeRule,
    Variable,
    as_group_terms,
    group_and,
    group_diff,
    group_or,
    member_of,
    select_canonical,
)
from .closures import ClosureIndex
from .storage import KnowledgeBase

Binding = dict[str, Term]


class EvaluationError(RuntimeError):
    """Selhání evaluace, které se nesmí projevit tiše (I‑1)."""


# --------------------------------------------------------------------------
# Substituce
# --------------------------------------------------------------------------


def substitute(term: Term, binding: Binding) -> Term:
    """Dosazení sestupuje i do algebraických termů — jinak by proměnná
    uvnitř `A DIFF V` zůstala nedosazená a hlava by prošla jako uzemněná."""
    if isinstance(term, Variable):
        return binding.get(term.id, term)
    if isinstance(term, (GroupAnd, GroupOr)):
        parts = tuple(substitute(part, binding) for part in term.operands)
        if parts == term.operands:
            return term
        checked = as_group_terms(parts, f"dosazení do {term.id}")
        return group_and(*checked) if isinstance(term, GroupAnd) else group_or(
            *checked
        )
    if isinstance(term, GroupDiff):
        left = substitute(term.left, binding)
        right = substitute(term.right, binding)
        if left is term.left and right is term.right:
            return term
        pair = as_group_terms((left, right), f"dosazení do {term.id}")
        return group_diff(pair[0], pair[1])
    return term


def instantiate(a: Atom, binding: Binding) -> Atom:
    return Atom(
        a.predicate,
        frozenset(
            RoleTerm(r.name, substitute(r.target, binding), r.quantifier)
            for r in a.roles
        ),
        a.is_negated,
    )


def render_binding(binding: Binding) -> str:
    return ", ".join(f"{name}={term.id}" for name, term in sorted(binding.items()))


def _combine(label: str, steps: list[Proof | None]) -> Proof:
    """Uzávěrový uzel nad kroky; reflexivní kroky se zahazují, protože
    nenesou žádný výrok a jen by zaplevelily vysvětlení (§ 8)."""
    premises = tuple(step for step in steps if step is not None and step.leaves())
    return Proof(ProofKind.CLOSURE, label, premises)


# --------------------------------------------------------------------------
# Materializace
# --------------------------------------------------------------------------


class Derivation:
    """Nejmenší uzávěr pro jednu verzi báze. Zahoditelný — otázka nemění
    bázi (I‑12), takže se dá kdykoli postavit znovu."""

    def __init__(self, version: int) -> None:
        self.version = version
        #: Počet kol pevného bodu. Pro program v bezpečném fragmentu má být
        #: 2 (jedno produktivní + jedno potvrzovací) NEZÁVISLE na pořadí
        #: zápisu pravidel — jinak `max_rounds` přestal být pojistkou.
        self.rounds = 0
        self.facts: dict[Atom, Proof] = {}
        #: Index `(predikát, znaménko) → fakta`. Bez něj se pro každý atom
        #: těla skenovala a třídila celá báze.
        self.by_predicate: dict[tuple[str, bool], list[Atom]] = {}
        self.index: ClosureIndex | None = None
        self.terms: dict[str, Term] = {}

    def add(self, a: Atom, proof: Proof) -> bool:
        """True, když se něco změnilo — nový atom NEBO kanoničtější důkaz.

        Zlepšení musí spustit další kolo: důkazy, které atom už použily jako
        premisu, jinak citují starou verzi a `normalize_proof(reference) ==
        normalize_proof(production)` z § 7 přestane platit. Terminace drží,
        protože `canonical_key` při zlepšení ostře klesá a množina
        odvoditelných důkazů nad konečnou bází je konečná.
        """
        existing = self.facts.get(a)
        if existing is None:
            self.facts[a] = proof
            self.by_predicate.setdefault(a.signature, []).append(a)
            return True
        if proof.canonical_key() < existing.canonical_key():
            self.facts[a] = proof
            return True
        return False

    def candidates(self, pattern: Atom) -> list[Atom]:
        return self.by_predicate.get(pattern.signature, [])

    def register_terms(self, a: Atom) -> None:
        for r in a.roles:
            if not isinstance(r.target, Variable):
                self.terms.setdefault(r.target.id, r.target)


class Engine:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb
        self._derivation: Derivation | None = None

    # -- veřejné API -------------------------------------------------------

    def derivation(self) -> Derivation:
        view = self.kb.view()
        if self._derivation is None or self._derivation.version != view.version:
            self._derivation = self._materialize()
        return self._derivation

    def ask(self, query: Atom) -> QueryResult:
        """Verdikt nad jedním atomem (§ 4). `CONFLICT` NENÍ čtvrtá pravdivostní
        hodnota — je to stav dotazu, kdy se odvodí `p` i `p̄`."""
        d = self.derivation()
        if not query.is_ground():
            return self._ask_open(query, d)
        positive = self._prove(query, d)
        negative = self._prove(query.complement(), d)
        if positive is not None and negative is not None:
            return QueryResult(QueryStatus.CONFLICT, conflict=(positive, negative))
        if positive is not None:
            return QueryResult(QueryStatus.PROVEN_TRUE, proof=positive)
        if negative is not None:
            return QueryResult(QueryStatus.PROVEN_FALSE, proof=negative)
        # Skutečný GapFinder (top-down SLD) je samostatný modul; zde jen
        # poctivé „na tohle nemám důkaz ani protidůkaz".
        return QueryResult(QueryStatus.UNKNOWN, gap=Gap((query,)))

    def _ask_open(self, query: Atom, d: Derivation) -> QueryResult:
        """Dotaz s proměnnou je existenční: „Napsal Postřižiny spisovatel?"
        Odpověď musí nést SVĚDKA (§ 6.3, dialog C), jinak by `ANO` mlčky
        existenčně kvantifikovalo.

        Záporná větev se tu ZÁMĚRNĚ nepočítá: svědek pro `¬φ(x)` dokládá
        „existuje x, pro které neplatí φ", což neodporuje „existuje x, pro
        které φ platí". Hlásit z toho `CONFLICT` by byla chyba.
        """
        matches = list(self._match(query, {}, d))
        if not matches:
            return QueryResult(QueryStatus.UNKNOWN, gap=Gap((query,)))
        binding, proof = min(
            matches, key=lambda m: (m[1].canonical_key(), render_binding(m[0]))
        )
        witness = Proof(ProofKind.WITNESS, render_binding(binding), (proof,))
        return QueryResult(
            QueryStatus.PROVEN_TRUE, proof=witness, payload=dict(binding)
        )

    def solutions(self, pattern: Atom) -> list[tuple[Binding, Proof]]:
        """Všechna doložená rozřešení vzoru — základ pro výčtové dotazy."""
        d = self.derivation()
        return sorted(
            self._match(pattern, {}, d),
            key=lambda item: (render_binding(item[0]), sorted(item[1].leaves())),
        )

    # -- materializace -----------------------------------------------------

    def _materialize(self) -> Derivation:
        view = self.kb.view()
        d = Derivation(view.version)

        base: list[tuple[str, Atom]] = []
        for st in self.kb.active():
            if isinstance(st.formula, Rule):
                continue
            base.append((st.id, st.formula))
            d.add(st.formula, Proof(ProofKind.FACT, st.id))
            d.register_terms(st.formula)

        d.index = ClosureIndex(base)

        rules = view.rules
        max_rounds = max(16, 4 * (len(rules) + 1))
        for _ in range(max_rounds):
            d.rounds += 1
            changed = False
            for rule in rules:
                for binding, premises in self._match_body(rule.body, {}, d):
                    head = self._instantiate_head(rule, binding)
                    proof = Proof(ProofKind.RULE, rule.id, tuple(premises))
                    if d.add(head, proof):
                        changed = True
                        d.register_terms(head)
            if not changed:
                break
        else:  # pragma: no cover — pojistka, nerekurzivní program sem nedojde
            raise EvaluationError(
                "pevný bod nekonverguje; program není v bezpečném fragmentu"
            )
        return d

    @staticmethod
    def _instantiate_head(rule: Rule, binding: Binding) -> Atom:
        try:
            head = instantiate(rule.head, binding)
        except AttachError as exc:  # mistypovaný rule — hlásí se nahlas (I‑1)
            raise UnsafeRule(
                f"pravidlo {rule.id!r}: dosazení {render_binding(binding)} "
                f"dává neplatnou hlavu — {exc}"
            ) from exc
        if not head.is_ground():
            raise UnsafeRule(
                f"pravidlo {rule.id!r}: hlava zůstala neuzemněná po dosazení "
                f"{render_binding(binding)}"
            )
        return head

    # -- dokazování --------------------------------------------------------

    def _prove(self, query: Atom, d: Derivation) -> Proof | None:
        return select_canonical([proof for _, proof in self._match(query, {}, d)])

    def _match_body(
        self, body: tuple[Atom, ...], binding: Binding, d: Derivation
    ) -> Iterator[tuple[Binding, list[Proof]]]:
        if not body:
            yield binding, []
            return
        head, rest = body[0], body[1:]
        for next_binding, proof in self._match(head, binding, d):
            for final, proofs in self._match_body(rest, next_binding, d):
                yield final, [proof, *proofs]

    def _match(
        self, pattern: Atom, binding: Binding, d: Derivation
    ) -> Iterator[tuple[Binding, Proof]]:
        if pattern.predicate in KERNEL_PREDICATES and not pattern.is_negated:
            yield from self._match_kernel(pattern, binding, d)
            return
        if pattern.predicate == P_MEMBER and pattern.is_negated:
            yield from self._match_negative_member(pattern, binding, d)
            return
        for fact in d.candidates(pattern):
            outcome = self._match_atom(pattern, fact, binding, d)
            if outcome is None:
                continue
            new_binding, steps = outcome
            base = d.facts[fact]
            proof = (
                base
                if not steps
                else Proof(ProofKind.DISTRIBUTE, "⪯", (base, *steps))
            )
            yield new_binding, proof

    def _match_kernel(
        self, pattern: Atom, binding: Binding, d: Derivation
    ) -> Iterator[tuple[Binding, Proof]]:
        """Jádrové uzávěry odpovídají přímo z indexu — jsou to primitivní
        predikáty stratu 0 (§ 5.1), ne fakta v pevném bodě."""
        if d.index is None:  # pragma: no cover
            raise EvaluationError("index uzávěrů není postavený")
        index = d.index
        p = pattern.predicate

        if p == P_MEMBER:
            elem = substitute(self._role(pattern, "elem").target, binding)
            group = substitute(self._role(pattern, "group").target, binding)
            if isinstance(group, Variable):
                raise EvaluationError(
                    f"{pattern}: enumerace přes všechny groups není ve F0; "
                    f"role `group` musí být v okamžiku vyhodnocení vázaná"
                )
            if isinstance(group, ALGEBRAIC) and not isinstance(elem, Variable):
                proof = self._member_term(elem, group, d)
                if proof is not None:
                    yield binding, proof
                return
            if isinstance(elem, Variable):
                for candidate in index.known_members(group.id):
                    term = d.terms.get(candidate)
                    proof = index.member_proof(candidate, group.id)
                    if term is None or proof is None:
                        # Tiché vypadnutí prvku z výčtu je porušení I‑1 —
                        # odpověď by byla o prvek chudší bez jediné stopy.
                        raise EvaluationError(
                            f"prvek {candidate!r} je členem {group.id!r}, ale "
                            f"{'nemá term' if term is None else 'nemá důkaz'}; "
                            f"výčet by tiše selhal"
                        )
                    yield {**binding, elem.id: term}, proof
            else:
                # Termová cesta, ne holé `index.member_proof` — členství
                # může být doložené pod algebraickým termem (§ 5.2.1).
                proof = self._member_term(elem, group, d)
                if proof is not None:
                    yield binding, proof
            return

        if p == P_SUBSET:
            # Termová cesta, ne `index.subset_proof`. Atomické směrování
            # dělalo zákony § 5.2.1 nedosažitelnými dotazem i tělem pravidla:
            # engine si `subset*` nad algebraickým termem vnitřně dokázal
            # (distribuce D1 ho volá), ale na přímou otázku odpověděl `U`
            # a pravidlo s algebraickou premisou se TIŠE nespustilo — bez
            # chyby a bez varování, tedy porušení I‑1. `member` přitom
            # routovaný byl, takže to nebyla volba, ale opomenutí.
            sub = substitute(self._role(pattern, "sub").target, binding)
            sup = substitute(self._role(pattern, "sup").target, binding)
            if isinstance(sub, Variable) or isinstance(sup, Variable):
                raise EvaluationError(
                    f"{pattern}: enumerace nad uzávěry není ve F0; obě role "
                    f"musí být v okamžiku vyhodnocení vázané"
                )
            proof = self._subset_term(sub, sup, d)
            if proof is not None:
                yield binding, proof
            return

        if p == P_NAME:
            # Ptá se indexu ze stejného důvodu jako `disjoint` a `complete`:
            # jméno se stalo hranou uzávěru (rozhoduje, který uzel zmínka
            # trefí), takže odvozený `name` by dal `A` bez účinku.
            bearer = substitute(self._role(pattern, "of").target, binding)
            label = substitute(self._role(pattern, "value").target, binding)
            if isinstance(bearer, Variable) or isinstance(label, Variable):
                raise EvaluationError(
                    f"{pattern}: enumerace přes jména není ve F0; obě role "
                    f"musí být v okamžiku vyhodnocení vázané"
                )
            if bearer.id in index.nodes_named(label.id):
                yield binding, Proof(ProofKind.CLOSURE, "name", ())
            return

        if p == P_COMPLETE:
            # Jednomístný, takže mimo tabulku dvojic. Ptá se indexu ze
            # stejného důvodu jako `disjoint`: uzavření světa má účinek jen
            # tehdy, když ho index vidí, a index se staví nad ZÁKLADNÍMI
            # fakty. Odvozený `complete` by dal `A` bez jediného účinku na
            # členství — a to je odpověď, která si sama odporuje.
            group = substitute(self._role(pattern, "group").target, binding)
            if isinstance(group, Variable):
                raise EvaluationError(
                    f"{pattern}: enumerace uzavřených skupin není ve F0; "
                    f"role `group` musí být v okamžiku vyhodnocení vázaná"
                )
            sid = index.is_complete(group.id)
            if sid is not None:
                yield binding, Proof(
                    ProofKind.CLOSURE, "complete", (Proof(ProofKind.FACT, sid),)
                )
            return

        pairs = {
            P_CONTAINS: ("whole", "part", index.contains_proof),
            P_WITHIN: ("whole", "part", index.within_proof),
            P_BEFORE: ("earlier", "later", index.before_proof),
            # `identity_proof`, ne `same_class`: sporná hrana se v uzávěru
            # nepoužívá (M‑1), ale na PŘÍMOU otázku se započítá, protože
            # ten výrok v bázi pořád je a odpovědí má být `CONFLICT`, ne `N`.
            P_SAME_AS: ("left", "right", index.identity_proof),
            # `disjoint` se ptá indexu, ne shody s faktem. Marker je v bázi
            # jednosměrný (`a:kočka, b:pes`), ale relace symetrická je —
            # shoda s faktem by tedy dala `N` na jedno pořadí a `U` na druhé,
            # a závěr by visel na tom, jak to člověk kdysi vyslovil.
            # Odvození `member̄` symetrické bylo od začátku; asymetrická byla
            # jen přímá otázka, což je táž třída vady jako B‑6.
            P_DISJOINT: ("a", "b", index.disjoint_proof),
        }
        left_name, right_name, prover = pairs[p]
        left = substitute(self._role(pattern, left_name).target, binding)
        right = substitute(self._role(pattern, right_name).target, binding)
        if isinstance(left, Variable) or isinstance(right, Variable):
            raise EvaluationError(
                f"{pattern}: enumerace nad uzávěry není ve F0; obě role musí "
                f"být v okamžiku vyhodnocení vázané"
            )
        proof = prover(left.id, right.id)
        if proof is not None:
            yield binding, proof

    def _match_negative_member(
        self, pattern: Atom, binding: Binding, d: Derivation
    ) -> Iterator[tuple[Binding, Proof]]:
        """Kontrapozice silné negace přes `subset*` — § 5.1, schváleno
        14. 8. 2026:

            member̄(x, B) ∧ subset*(A, B) ⇒ member̄(x, A)

        **Proč tady a ne v `ClosureIndex`.** Premisa vlajkového případu
        v bázi vůbec neexistuje: `member̄(e17,"stroj")` vzniká až expanzí
        `disjoint`, tedy pravidlem, zatímco index se staví jen nad
        základními fakty. Uzávěr postavený vedle `subset*`/`member*` by se
        na dialogu C nespustil a `member(e17,"parní_stroj")` by zůstalo `U`
        — tedy přesně ten výsledek, kvůli kterému se pravidlo doplňuje.
        Saturuje se proto uvnitř pevného bodu, nad odvozenými fakty.

        **Směr je nesymetrický.** Premisa mluví o NADMNOŽINĚ `B`, závěr
        o PODMNOŽINĚ `A`: „Hrabal není stroj" ⇒ „Hrabal není parní stroj".
        Opačný směr („není parní stroj ⇒ není stroj") je nekorektní a
        nesmí vzniknout — proto `subset_proof(dotaz, fakt)`, ne naopak.

        Rovnost skupin je zvláštní případ přes reflexivitu `subset*`, takže
        tahle větev nahrazuje i původní přímou shodu.
        """
        if d.index is None:  # pragma: no cover
            raise EvaluationError("index uzávěrů není postavený")
        index = d.index
        elem = substitute(self._role(pattern, "elem").target, binding)
        group = substitute(self._role(pattern, "group").target, binding)

        for fact in d.candidates(pattern):
            fact_elem = self._role(fact, "elem").target
            fact_group = self._role(fact, "group").target
            current = binding
            extra: list[Proof] = []

            if isinstance(elem, Variable):
                current = {**current, elem.id: fact_elem}
            else:
                link = index.same_class(elem.id, fact_elem.id)
                if link is None:
                    continue
                if link.leaves():
                    extra.append(link)

            if isinstance(group, Variable):
                current = {**current, group.id: fact_group}
            else:
                step = self._subset_term(group, fact_group, d)
                if step is None:
                    continue
                if step.leaves():
                    extra.append(step)

            base = d.facts[fact]
            proof = (
                base
                if not extra
                else Proof(ProofKind.CLOSURE, "member̄*", (base, *extra))
            )
            yield current, proof

        yield from self._complete_denials(elem, group, binding, d)

    def _complete_denials(
        self, elem: Term, group: Term, binding: Binding, d: Derivation
    ) -> Iterator[tuple[Binding, Proof]]:
        """`complete(g) ∧ x ∉ certain(g) ⇒ member̄(x, g)` — § 5.1, schváleno
        14. 8. 2026.

        **Jediné místo v jádře, kde závěr plyne z ABSENCE.** Všechno ostatní
        drží I‑21 („absence není negace"); tohle je schválená výjimka a musí
        být pevně ohrazená.

        Ohrazení spočívá v tom, že se uzávěr vyhodnocuje **až při dotazu** a
        nikdy se nematerializuje do pevného bodu. Uvnitř evaluační smyčky by
        se `member̄(x,g)` odvodilo z neúplného stavu — a pravidlo, které
        doběhne později, může `member(x,g)` teprve vyrobit. Vznikl by `p`
        i `p̄`, tedy falešný `CONFLICT`, a pevný bod by přestal být monotónní.
        Takhle nemůže uzávěr nic zpětně zneplatnit a nevzniká nové stratum.

        Skládá se s kontrapozicí: uzavření NADskupiny uzavře i podskupiny,
        protože `x ∉ g` a `A ⊆ g` dává `x ∉ A`.
        """
        if d.index is None:  # pragma: no cover
            raise EvaluationError("index uzávěrů není postavený")
        index = d.index
        if isinstance(elem, Variable) or isinstance(group, Variable):
            # Enumerace „všech, kdo do uzavřené skupiny nepatří" by musela
            # projít celou doménu; ve F0 se nedělá.
            return
        for complete_group, complete_sid in index.complete_groups():
            if index.member_proof(elem.id, complete_group) is not None:
                continue  # prvek ve skupině JE — není co popírat
            step = index.subset_proof(group.id, complete_group)
            if step is None:
                continue
            premises: list[Proof] = [Proof(ProofKind.FACT, complete_sid)]
            if step.leaves():
                premises.append(step)
            yield binding, Proof(ProofKind.CLOSURE, "complete*", tuple(premises))

    @staticmethod
    def _role(a: Atom, name: str) -> RoleTerm:
        found = a.get_role(name)
        if found is None:  # pragma: no cover — strukturní atomy role mají
            raise EvaluationError(f"{a}: chybí role {name!r}")
        return found

    # -- algebraické termy (§ 5.2.1) ---------------------------------------

    def _subset_term(
        self, sub: Term, sup: Term, d: Derivation
    ) -> Proof | None:
        """`subset*` nad algebraickými termy — **cíleně, ne dopředně**.

        Zákony se používají výhradně k zodpovězení dotazu `sub ⊆ sup`
        a rekurze jde po **struktuře porovnávaných termů**. Dopředné
        řetězení by neterminovalo: `X ⊆ A ⇒ X ⊆ A OR B` má vpravo volné
        `B`. Cílené použití je konečné, protože každý krok sestoupí
        do podtermu.

        Sada je záměrně neúplná — chybějící důkaz dá `U`, nikdy falešné
        `A`. Úplná rozhodovací procedura nad algebrou je samostatné
        rozhodnutí (§ 5.2.1).

        **Napřed se hledá ZAPSANÝ výrok, teprve pak se odvozuje** *(G‑3)*.
        Do téhle opravy se index ptal jen tehdy, když ani jedna strana
        nebyla algebraická; s algebraickým `sup` se šlo rovnou na zákony.
        Důsledek: `attach(subset(auto, A AND B))` se uložil, uzávěrový
        index tu hranu MĚL, a přímá otázka na týž fakt vrátila `U`.

        To není neúplnost odvození, to je **selhání recallu** — systém
        odpověděl „nevím" na tvrzení, které mu člověk řekl a které má
        uložené. Neúplná sada zákonů je přiznaná mez (nedokážu odvodit
        všechno); ignorovat vlastní bázi mez není, to je vada.

        Zákony se tím **neobcházejí**: přímý dotaz jen předchází, a když
        nic nenajde, běží dál přesně jako dřív. Kde platí obojí, vrací se
        ten přímý — je kratší, a minimalita důkazu je § 7.
        """
        assert d.index is not None
        if sub.id == sup.id:
            return Proof(ProofKind.CLOSURE, "subset*/refl")
        recalled = d.index.subset_proof(sub.id, sup.id)
        if recalled is not None:
            return recalled
        if not isinstance(sub, ALGEBRAIC) and not isinstance(sup, ALGEBRAIC):
            return None

        label = "subset*/alg"
        # sup = A AND B   ⟸  sub ⊆ A ∧ sub ⊆ B
        if isinstance(sup, GroupAnd):
            steps = [self._subset_term(sub, part, d) for part in sup.operands]
            if all(step is not None for step in steps):
                return _combine(label, steps)
        # sup = A OR B    ⟸  sub ⊆ některý operand
        if isinstance(sup, GroupOr):
            for part in sup.operands:
                step = self._subset_term(sub, part, d)
                if step is not None:
                    return _combine(label, [step])
        # sub = A AND B   ⟸  některý operand ⊆ sup
        if isinstance(sub, GroupAnd):
            for part in sub.operands:
                step = self._subset_term(part, sup, d)
                if step is not None:
                    return _combine(label, [step])
        # sub = A OR B    ⟸  každý operand ⊆ sup
        if isinstance(sub, GroupOr):
            steps = [self._subset_term(part, sup, d) for part in sub.operands]
            if all(step is not None for step in steps):
                return _combine(label, steps)
        # sub = A DIFF B  ⟸  A ⊆ sup
        if isinstance(sub, GroupDiff):
            step = self._subset_term(sub.left, sup, d)
            if step is not None:
                return _combine(label, [step])
        # sup = A DIFF B  ⟸  sub ⊆ A ∧ disjoint(sub, B)   (dodatek E)
        # Bez tohohle zákona by druhová reprezentace neměla protějšek
        # k pravidlu, které `member*` pro `DIFF` má: „vrabec je pták kromě
        # tučňáka" by nešlo doložit na úrovni tříd, jen po jednotlivcích.
        if isinstance(sup, GroupDiff):
            inside = self._subset_term(sub, sup.left, d)
            if inside is not None:
                separate = d.index.disjoint_proof(sub.id, sup.right.id)
                if separate is not None:
                    return _combine(label, [inside, separate])
        return None

    def _member_term(
        self, elem: Term, group: Term, d: Derivation
    ) -> Proof | None:
        """`member*` nad algebraickými termy podle § 5.2.1(a).

        Pravidla jsou implikace **jen zprava doleva**. U `OR` je směr
        podstatný: ekvivalence by znamenala, že z členství ve sjednocení
        plyne členství v některém členu — a to je zákaz z dialogu A,
        „z disjunkce se nesmí tiše vybrat člen".
        """
        assert d.index is not None
        # Přímo uložené členství — i pod algebraickým id. Disjunktivní
        # členství je legitimní vstup, jen se z něj nesmí vybírat člen.
        direct = d.index.member_proof(elem.id, group.id)
        if direct is not None:
            return direct

        # Členství doložené pod ALGEBRAICKÝM termem se přenese na jeho
        # nadmnožinu. Id-graf uzávěrů algebraické termy jako uzly nezná,
        # takže tenhle krok musí projít zákony z § 5.2.1(b) — díky tomu
        # `member(x, A AND B)` dá `member(x, A)`, ale `member(x, A OR B)`
        # NEDÁ `member(x, A)`, protože `A OR B ⊆ A` mezi zákony není.
        for declared_id, sid in d.index.declared_memberships(elem.id):
            declared = d.terms.get(declared_id)
            if declared is None or not isinstance(declared, ALGEBRAIC):
                continue
            if declared.id == group.id:
                continue
            step = self._subset_term(declared, group, d)
            if step is not None:
                return _combine(
                    "member*/alg", [Proof(ProofKind.FACT, sid), step]
                )

        if not isinstance(group, ALGEBRAIC):
            return None

        label = "member*/alg"
        if isinstance(group, GroupAnd):
            steps = [self._member_term(elem, part, d) for part in group.operands]
            if all(step is not None for step in steps):
                return _combine(label, steps)
            return None
        if isinstance(group, GroupOr):
            for part in group.operands:
                step = self._member_term(elem, part, d)
                if step is not None:
                    return _combine(label, [step])
            return None
        # A DIFF B: člen A, o kterém je DOLOŽENO, že v B není.
        # `x ∉ possible(B)`, ne `x ∉ certain(B)` — slabší varianta by
        # tvrdila „prokazatelně nepatří" z pouhé nevědomosti (I‑21).
        inside = self._member_term(elem, group.left, d)
        if inside is None:
            return None
        outside = self._prove(member_of(elem, group.right).complement(), d)
        if outside is None:
            return None
        return _combine(label, [inside, outside])

    # -- relace shody ⪯ (§ 3.3) -------------------------------------------

    def _match_atom(
        self, pattern: Atom, fact: Atom, binding: Binding, d: Derivation
    ) -> tuple[Binding, list[Proof]] | None:
        steps: list[Proof] = []
        current = binding
        for prole in pattern.canonical_roles():
            frole = fact.get_role(prole.name)
            if frole is None:
                return None  # role dotazu ve faktu chybí
            outcome = self._compat(
                prole,
                frole,
                current,
                d,
                # POLARITA PATŘÍ DO SHODY ROLÍ, ne jen nad ni (B‑13).
                # Negace obrací monotonii, takže záporný sloupec nesmí
                # být mechanickým zrcadlem kladného.
                negated=pattern.is_negated and fact.is_negated,
            )
            if outcome is None:
                return None
            current, step = outcome
            # Reflexivní kroky (`subset*/refl`, `same_as*/refl`) nenesou žádný
            # výrok — do vysvětlení nepatří, jen by ho zaplevelily (§ 8).
            steps.extend(s for s in step if s.leaves())
        # Role navíc ve faktu nevadí — „jede rychle po dálnici" odpovídá
        # i na „jede po dálnici?" (§ 3.4 zadání).
        return current, steps

    def _compat(
        self,
        prole: RoleTerm,
        frole: RoleTerm,
        binding: Binding,
        d: Derivation,
        *,
        negated: bool = False,
    ) -> tuple[Binding, list[Proof]] | None:
        """Sedne role dotazu na roli faktu? — § 3.3.

        **`negated` není ozdoba: negace OBRACÍ MONOTONII** *(B‑13)*.
        Kladné `P(∀F)` říká, že P platí o každém prvku `F`, takže dotaz
        smí jít DOLŮ (užší třída). Záporné `¬P(∀F)` říká totéž o
        neplatnosti — a z „o žádném prvku masa to neplatí" plyne i „o
        nějakém prvku masa to neplatí", protože obojí je tvrzení O TÉŽE
        MNOŽINĚ, jen jinak kvantifikované.

        Do opravy vidělo tohle porovnání jen role, nikdy polaritu atomu,
        takže záporný sloupec byl mechanickým zrcadlem kladného. Důsledek
        byl měřitelný: `¬jíst(co:∀maso)` proti dotazu `¬jíst(co:∃maso)`
        dalo `U` tam, kde věcně platí `N`.
        """
        if d.index is None:  # pragma: no cover
            raise EvaluationError("index uzávěrů není postavený")
        index = d.index
        pq, fq = prole.quantifier, frole.quantifier
        pt = substitute(prole.target, binding)
        ft = frole.target

        def bind() -> tuple[Binding, list[Proof]]:
            return {**binding, pt.id: ft}, []

        # ∀ × ∀ — dotaz smí být UŽŠÍ (D1: ∀ jde dolů)
        if pq is Quantifier.FOR_ALL and fq is Quantifier.FOR_ALL:
            if isinstance(pt, Variable):
                return bind()
            proof = self._subset_term(pt, ft, d)
            return (binding, [proof]) if proof else None

        # ∃ × ∃ — dotaz smí být ŠIRŠÍ (D2: ∃ jde jen nahoru)
        if pq is Quantifier.EXISTS and fq is Quantifier.EXISTS:
            if isinstance(pt, Variable):
                return bind()
            proof = self._subset_term(ft, pt, d)
            return (binding, [proof]) if proof else None

        # · × · — týž uzel (group jako objekt)
        if pq is Quantifier.SELF and fq is Quantifier.SELF:
            if isinstance(pt, Variable):
                return bind()
            proof = index.same_class(pt.id, ft.id)
            return (binding, [proof]) if proof else None

        # konkrétní × ∀ — D1 na prvek
        if pq is None and fq is Quantifier.FOR_ALL:
            if isinstance(pt, Variable):
                return None  # enumeraci členů dělá `member` v těle pravidla
            proof = self._member_term(pt, ft, d)
            return (binding, [proof]) if proof else None

        # konkrétní × ∃ — NIKDY. Tady se láme dialog B: „obsahuje citron
        # vitamín C?" nesmí sednout na „obsahuje ∃vitamín".
        if pq is None and fq is Quantifier.EXISTS:
            return None

        # konkrétní × konkrétní
        if pq is None and fq is None:
            if isinstance(pt, Variable):
                return bind()
            if isinstance(pt, Place) and isinstance(ft, Place):
                proof = index.contains_proof(pt.id, ft.id)
                return (binding, [proof]) if proof else None
            if isinstance(pt, Interval) and isinstance(ft, Interval):
                proof = index.within_proof(pt.id, ft.id)
                return (binding, [proof]) if proof else None
            if isinstance(pt, Label) or isinstance(ft, Label):
                return (binding, []) if pt == ft else None
            proof = index.same_class(pt.id, ft.id)
            return (binding, [proof]) if proof else None

        # ∃ × ∀ POD NEGACÍ — jediná buňka, kterou přidává B‑13.
        #
        # Kladně by ∃ × ∀ potřebovalo NEPRÁZDNOST třídy („platí to o všech,
        # tedy o nějakém" mlčky předpokládá, že nějaký je), a ta se
        # v otevřeném světě nedoloží. Pod negací se to obrací a předpoklad
        # MIZÍ: „o žádném prvku masa to neplatí" dává „o nějakém prvku masa
        # to neplatí" i pro PRÁZDNOU třídu, protože obě strany tvrdí
        # neplatnost, ne existenci.
        #
        # Důkazní povinnost je táž jako u kladného ∀ × ∀ — dotaz smí být
        # UŽŠÍ. Ne širší: z „vegetarián nejí maso" neplyne, že nejí
        # potraviny.
        if negated and pq is Quantifier.EXISTS and fq is Quantifier.FOR_ALL:
            if isinstance(pt, Variable):
                return None  # výčet přes prvky dělá `member` v těle pravidla
            proof = self._subset_term(pt, ft, d)
            return (binding, [proof]) if proof else None

        # Zbytek: ∃ × ∀ KLADNĚ by potřebovalo neprázdnost group; v otevřeném
        # světě nedoložitelné, a doplnit ji by byl existenční import, který
        # § 3.2 zakazuje. ∀ × ∃ neplatí nikdy.
        return None
