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
    KERNEL_PREDICATES,
    P_BEFORE,
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

#: `via` pro cíl, ke kterému NEVEDLA ŽÁDNÁ cesta. Konstanta, protože ji
#: píše `_goals_for` a čte renderování — a hláška poskládaná do věty
#: („potřeboval jsem to přes žádné pravidlo tohle nevyrábí") je nesmysl,
#: který si nikdo nevšimne, dokud ho neuvidí v transkriptu.
NO_PATH = "nikdo to neřekl a žádné pravidlo to nevyrábí"


@dataclass(frozen=True, slots=True)
class OpenGoal:
    """Podcíl, který prohledávání potřebovalo a nenašlo."""

    atom: Atom
    via: str
    depth: int = 0

    def render(self) -> str:
        """Mezera jako NABÍDKA, ne jako konstatování (K‑9).

        „Chybí vědět: subset(vrabec, tučňák)" po člověku chce, aby si sám
        domyslel, co s tím — a hlavně to vypadá jako výtka. Táž informace
        položená jako otázka je tah dialogu, na který jde odpovědět, a
        odpověď je přesně to, co systému chybí.

        **Je to změna RENDEROVÁNÍ, ne nové inference.** Nabízí se to, co
        prohledávání skutečně potřebovalo a nenašlo — nic se nedomýšlí.
        Označení HYPOTÉZA je povinné (§ 12/5): systém se ptá, netvrdí.
        """
        # „potřeboval jsem to přes X" dává smysl jen tam, kde X je CESTA.
        # U cíle, který je sám dotaz, žádná cesta nevedla — a tvrdit ji by
        # bylo vysvětlení, které si vymýšlí (I‑14).
        if self.via == NO_PATH:
            return f"? platí {self.atom}? [HYPOTÉZA — {NO_PATH}]"
        return f"? platí {self.atom}? [HYPOTÉZA — potřeboval jsem to přes {self.via}]"


@dataclass(frozen=True, slots=True)
class GapReport:
    query: Atom
    open_goals: tuple[OpenGoal, ...]
    known: tuple[str, ...] = ()
    exhausted: bool = False
    #: Nabídka, po které by se báze ROZBILA, se netiskne *(B‑14)*.
    #:
    #: Rozhodnutí patří sem, do RENDERU, a ne do `open_goals`: poslední
    #: záchranná nabídka se tiskne PRÁVĚ TEHDY, když je `open_goals`
    #: prázdné, takže vyprázdnit ji tu nabídku nepotlačí — SPUSTÍ ji.
    #: Obě poloviny opravy by šly proti sobě a testy nad prázdnou kolekcí
    #: by to nezachytily, protože by neprovedly ani jednu aserci.
    unsafe_offer: bool = False
    #: Identity, které jsou ve sporu a kvůli tomu se hrana nepoužila (M‑1).
    #: Bez tohohle by odpověď spadla z `A` na `U` a nikdo by se nedozvěděl
    #: proč — a mezera, kterou nejde vysvětlit, je skoro tak špatná jako
    #: tichá odpověď (I‑14).
    disputed: tuple[tuple[str, str], ...] = ()

    def render(self) -> tuple[str, ...]:
        lines: list[str] = []
        lines.extend(f"vím: {item}" for item in self.known)
        lines.extend(
            f"POZOR: o tom, jestli je {a} totéž co {b}, si báze protiřečí — "
            f"dokud to nerozhodneš, přes tuhle identitu nic nevede"
            for a, b in self.disputed
        )
        if self.open_goals:
            lines.extend(goal.render() for goal in self.open_goals)
        elif self.unsafe_offer:
            # PRAVDA BEZ NÁVODU. Nabídnout „řekni tohle a budeš to vědět"
            # by tady byla léčka: opačná hrana uspořádání uzavře cyklus
            # a báze na tu otázku přestane odpovídat vůbec (H‑3). Mlčet
            # taky nejde — člověk má vědět, PROČ mu systém nic nenabízí.
            lines.append(
                f"tohle mi nikdo neřekl a nabídnout ti větu, která by "
                f"uspořádání kolem {self.query} uzavřela do cyklu, nemůžu"
            )
        else:
            # Ani tady se neříká „chybí vědět". Když se nenašel žádný
            # konkrétní podcíl, je poctivá odpověď „tohle mi nikdo neřekl
            # a neplyne to" — ne výčitka, že to člověk zapomněl.
            lines.append(f"? platí {self.query}? [HYPOTÉZA — nikdo to neřekl]")
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
            unsafe_offer=self._contradicts_base(query, derivation),
            disputed=self._disputed_for(query, derivation),
        )

    def _disputed_for(
        self, query: Atom, derivation: Derivation
    ) -> tuple[tuple[str, str], ...]:
        """Sporné identity, které se dotýkají uzlů z dotazu.

        Hlásí se JEN ty, o které jde. Vypsat všechny spory v bázi by
        znamenalo, že u velké báze zanikne ten jediný, na kterém odpověď
        opravdu ztroskotala."""
        if derivation.index is None:  # pragma: no cover
            return ()
        touched = {
            r.target.id for r in query.roles if r.target.SORT is not Sort.VARIABLE
        }
        return tuple(
            pair
            for pair in derivation.index.disputed_identities()
            if touched & set(pair)
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

        if not produced and not goals and not self._contradicts_base(
            query, derivation
        ):
            goals.append(OpenGoal(atom=query, via=NO_PATH, depth=depth))
        return goals

    def _contradicts_base(self, query: Atom, derivation: Derivation) -> bool:
        """Vyrobilo by přidání dotazu SPOR? Pak se nenabízí *(W‑19)*.

        Poslední záchranná nabídka zní „řekni tohle a budeš to vědět".
        U uspořádání to ale nemusí být pravda: když je doložený OPAČNÝ
        směr, opačná hrana by uzavřela cyklus a báze by na tu otázku
        přestala odpovídat vůbec (H‑3). Nabídnout člověku větu, po které
        se systém rozbije, je horší než mu nenabídnout nic.

        Ptá se jen na to, co uzávěr UŽ VÍ — nedomýšlí se, jestli by se
        spor objevil někde jinde.
        """
        if query.predicate != P_BEFORE or derivation.index is None:
            return False
        earlier = query.get_role("earlier")
        later = query.get_role("later")
        if earlier is None or later is None:
            return False
        if isinstance(earlier.target, Variable) or isinstance(
            later.target, Variable
        ):
            return False
        return (
            derivation.index.before_proof(later.target.id, earlier.target.id)
            is not None
        )

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
        se konkrétní role a to, co by ji uzavřelo.

        **Jen pro BĚŽNÉ predikáty** *(W‑19)*. Článek se hledá přes
        `⪯`, tedy přes relaci shody rolí — jenže na JÁDROVÝ predikát se
        `⪯` nikdy nezavolá: `_match` posílá jádrové predikáty rovnou do
        `_match_kernel`, kde se odpovídá z uzávěrového indexu. Nabídnout
        tam článek `⪯` znamenalo nabídnout cestu, kterou vyhodnocení
        NEJDE: „Je středa před pondělím?" se ptalo na `within(pondělí,
        středa)`, člověk to mohl zapsat a odpověď zůstala `U`.

        Vysvětlení, ze kterého se nedá stavět dál, je horší než poctivé
        „nikdo to neřekl" — a `via` u něj navíc TVRDÍ („potřeboval jsem
        to přes…") něco, co není pravda (I‑14).
        """
        if query.predicate in KERNEL_PREDICATES:
            return []
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
