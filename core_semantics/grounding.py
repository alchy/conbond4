"""V3 — zmínka na uzel, § 3.2 a dodatek L‑5.

Tady se česká věta teprve stává faktem. Do L‑5 kaskáda vybrala čtení,
vypsala `✓ přečteno` a **skončila** — do báze nešlo nic a otázka se
nevyhodnotila.

**Rozsah je vymezený tím, co etalon potřebuje, a mez se říká nahlas.**

* vlastní jméno → uzel podle jména
* obecné jméno → `Group`
* určitý popis → **doložit existující** uzel; víc kandidátů → doptat se
* zájmena a elipsa **VEN** — potřebují aktivaci (§ 4), etalon je nemá,
  protože mluví jmény. Neumíme to a předstírat se to nebude.

**Nový uzel vzniká jen `attach`em, nikdy vyhodnocením** (§ 0.2, No Chase).
Tenhle modul proto **nic nezapisuje**: složí formuli a vrátí ji. Kdo ji
zapíše, je tah `!`; otázka `?` z ní jen čte, a ptát se na neznámé jméno
je legitimní `U`, ne chyba.

**Sort plyne z ROLE, ne ze slova.** „Praha" je `Place` v roli `kam`,
protože `kam` je prostorová role slovníku jádra (§ 3.6) — ne proto, že by
si tenhle modul o Praze něco myslel. Role, která zůstala povrchová
(`v+Loc`, protože je `kde` i `kdy`), sort neurčí a **věta se nezakotví**;
je to táž nerozhodnutost o patro dřív, ne nová.

---

**Co je tu vědomě NEROZHODNUTÉ a čeká na člověka.** Identita jmen bez UNA
— zda „Praha" ve dvou větách je týž uzel — je otázka, kterou tenhle modul
**neřeší tím, že by ji odpověděl**: uzel je pojmenovaný lemmatem, takže
dvě stejná lemmata splynou, a to je ROZHODNUTÍ, ne vlastnost. Kdyby mělo
padnout jinak, mění se `name_of` a nic víc — proto je to jedna funkce
a ne rozsypaná logika.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable

from .ast import (
    PLACE_ROLES,
    RELATION_SORTS,
    ROLE_SORTS,
    TIME_ROLES,
    UNQUANTIFIED_ROLES,
    Atom,
    Entity,
    Group,
    Interval,
    Label,
    Place,
    Quantifier,
    QueryStatus,
    Sort,
    SortError,
    Term,
    UnquantifiedRole,
    atom,
    role,
)
from .cascade import (
    AWAITING_QUANTIFIER,
    ROLE_SUBJECT,
    AWAITING_REFERENCE,
    Mention,
    Predication,
    Rejection,
    RejectionKind,
    RoleReading,
)
from .storage import ResolvedGraphView

if TYPE_CHECKING:  # pragma: no cover — jen pro typy
    from .engine import Engine

#: Slovní druhy, které tenhle modul zakotvit NEUMÍ. Zájmeno potřebuje
#: aktivaci (§ 4) — vědět, o čem se zrovna mluví — a to je celá vrstva,
#: kterou etalon nepotřebuje, protože mluví jmény.
UNSUPPORTED_UPOS = ("PRON", "DET")


class BindingType(Enum):
    """Jak zmínka přistála na uzlu (M‑6).

    **Enum, ne volný řetězec.** Na tomhle poli visí rozdíl mezi
    „zakládám nový uzel" a „odkazuji na existující", tedy věc, kterou
    hlídá § 0.2 — a rozlišovat ji porovnáváním vět je způsob, jak si
    jednoho dne odpovědět špatně kvůli překlepu.
    """

    #: Vlastní jméno na kanonický uzel téhož jména (politika Q1/M‑2).
    CANONICAL_PROPN = "kanonicky"
    #: Určitý popis doložený na existující uzel (M‑4).
    RESOLVED_DEFINITE = "určitý popis"
    #: Nový uzel — vzniká JEN tahem `!` (§ 0.2, M‑3).
    CREATED_NEW = "založen"
    #: Obecné jméno jako skupina; žádný uzel se nezakládá ani nehledá.
    GROUP = "obecné jméno"
    #: Místo nebo čas, jejichž sort určila role (§ 3.6).
    FROM_ROLE = "sort z role"


@dataclass(frozen=True, slots=True)
class Anchor:
    """Zmínka a uzel, na kterém přistála, i s tím PROČ.

    Bez `binding` by se nedalo poznat, jestli uzel vznikl z vlastního
    jména, nebo se doložil jako určitý popis — a to je rozdíl mezi
    „zakládám" a „odkazuji", tedy přesně ta věc, kterou § 0.2 hlídá.

    `detail` je dovysvětlení pro člověka („týž uzel jako v tahu #3"),
    ne nosič rozhodnutí. Rozhoduje `binding`.
    """

    mention: Mention
    term: Term
    binding: BindingType
    detail: str = ""
    #: Výroky, kterými je TOHLE ztotožnění doložené. U kanonizace jmen je
    #: to výrok `name(of, value)`: bez něj by odpověď na otázku o „Honzovi"
    #: citovala fakt o „Janovi" a spojnice mezi nimi by nikde nebyla.
    cited: tuple[str, ...] = ()

    def __str__(self) -> str:
        note = f"{self.binding.value}{'; ' + self.detail if self.detail else ''}"
        return f"{self.mention.form} → {self.term.id} ({note})"


@dataclass(frozen=True, slots=True)
class Grounded:
    """Výsledek zakotvení. `formula is None` znamená OTÁZKU, ne chybu."""

    formula: Atom | None = None
    anchors: tuple[Anchor, ...] = ()
    notes: tuple[str, ...] = ()
    question: str | None = None
    #: Tokeny, na které se ZEPTALO ZAKOTVENÍ. Kaskáda se na tytéž role
    #: může ptát po kvantifikátoru — jenže u zájmena ho rozhodne až
    #: antecedent, takže by to byla otázka na něco, co ta druhá odpověď
    #: stejně nastaví. Dvě otázky na tutéž věc jsou horší než jedna:
    #: člověk neví, kterou z nich odpovídá.
    asked: tuple[int, ...] = ()

    @property
    def cited(self) -> tuple[str, ...]:
        """Výroky, které zakotvení POUŽILO. Nejsou to premisy důkazu —
        jsou to fakty, bez kterých by se dotaz vůbec netrefil na tenhle
        uzel, a v citaci proto chybět nesmějí."""
        found: list[str] = []
        for anchor in self.anchors:
            found.extend(anchor.cited)
        return tuple(sorted(set(found)))

    @property
    def ok(self) -> bool:
        return self.formula is not None


@dataclass(frozen=True, slots=True)
class Discourse:
    """Co bylo řečeno ve VĚTĚ PŘEDTÍM — kontext textu *(0.1.16)*.

    **Je to nová INFORMACE, ne nová inference.** Sezení dosud znalo TAH,
    ne TEXT: každá věta se zakotvovala sama za sebe, protože etalon mluvil
    jmény a odkaz nepotřeboval. Souvislý psaný text ale odkazuje pořád —
    „Jan je učitel. **On** bydlí v Praze." — a bez paměti předchozí věty
    není zájmeno na co navázat.

    **Předzpracování by to zakrylo.** Čistič, který zájmena předem nahradí
    jmény, vyrobí text, jakému systém rozumí, a schová právě to, co se má
    naučit. Proto je kontext tady, ve vrstvě, která zmínky na uzly váže.

    Drží se ZMÍNKA i UZEL: jméno samo by nestačilo, protože kandidát se
    musí umět shodnout v rodě a čísle, a to je vlastnost zmínky.
    """

    #: `(zmínka, uzel)` z poslední zakotvené věty, v pořadí výskytu.
    mentions: tuple[tuple[Mention, Term], ...] = ()

    def candidates(self, pronoun: Mention) -> tuple[tuple[Mention, Term], ...]:
        """Antecedenti, kteří se se zájmenem SHODUJÍ v rodě a čísle.

        Shoda je vodítko struktury textu, ne důkaz — proto se jí kandidáti
        jen ZUŽUJÍ, nikdy nevybírá. Kandidát, který v předchozí větě není,
        se nenabídne vůbec: nabídnout uzel odjinud znamená tvrdit, že text
        odkazuje tam, kde nic nestojí.
        """
        want = dict(pronoun.feats)
        found: list[tuple[Mention, Term]] = []
        for mention, term in self.mentions:
            if term.SORT is Sort.GROUP:
                # Skupina není uzel. „Jan je učitel." nabízí Jana, ne
                # „učitele": zájmeno odkazuje na TOHO, o kom byla řeč,
                # a ztotožnit ho s celou třídou by z individua udělalo
                # druh.
                continue
            feats = dict(mention.feats)
            if any(
                key in want and key in feats and want[key] != feats[key]
                for key in ("Gender", "Number")
            ):
                continue
            found.append((mention, term))
        return tuple(found)


#: Zájmena, která odkazují do PŘEDCHOZÍHO textu. Osobní a přivlastňovací
#: ve 3. osobě — první a druhá osoba míří na účastníky rozhovoru, ne do
#: textu, a tam by antecedent hledat nešlo.
ANAPHORIC_LEMMAS = ("on", "jeho", "její", "jejich", "ten", "tento")


def name_of(mention: Mention) -> str:
    """Jméno uzlu ze zmínky.

    **Jediné místo, kde se rozhoduje identita jmen.** Dnes je to lemma,
    takže „Praha" ve dvou větách je týž uzel — v otevřeném světě bez UNA
    je to ROZHODNUTÍ, ne samozřejmost, a bude‑li se měnit, mění se tady
    a nikde jinde. Rozsypat tuhle úvahu po modulu by znamenalo, že se
    příště nedá vzít zpátky.
    """
    return mention.lemma


def _quantifier_for(term: Term, chosen: Quantifier | None) -> Quantifier | None:
    return chosen if term.SORT is Sort.GROUP else None


def _sort_for(
    role_name: str, term_id: str, concrete: bool, relation: Sort | None = None
) -> Term:
    """Sort filleru. `relation` má PŘEDNOST před jménem role (N‑9).

    Jádrová relace určuje sort svých stran sama: `before(earlier, later)`
    mluví o časové ose, ať se ty role jmenují jakkoli. Odvozovat to ze
    jména by nešlo — `whole`/`part` má `contains` (místo) i `within`
    (čas), takže by to bylo hádání.
    """
    if relation is Sort.TIME:
        return Interval(term_id)
    if relation is Sort.PLACE:
        return Place(term_id)
    if relation is Sort.LABEL:
        return Label(term_id)
    if relation is Sort.ENTITY:
        return Entity(term_id)
    if role_name in PLACE_ROLES:
        return Place(term_id)
    if role_name in TIME_ROLES:
        return Interval(term_id)
    return Entity(term_id) if concrete else Group(term_id)


def _presentational_subject(reading: RoleReading) -> bool:
    """Prezentační „to" — podmět BEZ REFERENCE *(W‑29)*.

    Táž vazba, kvůli které má shoda čísla úzkou výjimku („To je pes." i
    „To jsou psi."): střední „to" tam nezastupuje počitatelný podmět a
    neukazuje na uzel. Nemá tedy co zakotvit — a ptát se na to je otázka
    bez odběratele, protože ať člověk odpoví cokoli, žádný uzel z toho
    nevznikne.

    Ohraničení je stejně tvrdé jako u té shody, a schválně: `ten` v jiné
    pozici („ten pes") uzel MÍNÍ a doptat se na něj správné je.
    """
    mention = reading.mention
    feats = dict(mention.feats)
    return (
        reading.name == ROLE_SUBJECT
        and mention.lemma == "ten"
        and feats.get("PronType") == "Dem"
        and feats.get("Gender") == "Neut"
        and feats.get("Number") == "Sing"
    )


def _resolve_anaphor(reading: RoleReading, discourse: Discourse) -> _Resolution:
    """Zájmeno na antecedent z PŘEDCHOZÍ věty — NÁVRH, nikdy dosazení.

    **Ptá se i tehdy, když je kandidát právě jeden.** Shoda rodu a čísla
    je vodítko struktury textu, ne důkaz: „Jan je učitel. On bydlí
    v Praze." má jediného kandidáta, ale „trefil jsem týž uzel" a „ČLOVĚK
    ŘEKL, že to je týž" jsou dvě různé věci a celá M‑2 stojí na tom
    rozdílu. Tichý default u identity je nejdražší chyba, jakou tenhle
    systém může udělat — uzly se tiše slijí nebo rozštěpí a nepozná to
    žádný test, ke kterému jazyk nevede.

    **Kandidát, který v předchozí větě není, se NENABÍDNE.** Nabídnout uzel
    odjinud znamená tvrdit, že text odkazuje tam, kde nic nestojí.
    """
    mention = reading.mention
    if mention.lemma not in ANAPHORIC_LEMMAS:
        return (
            None,
            BindingType.GROUP,
            "",
            f"Na koho odkazuje „{mention.form}“? Tohle zájmeno neumím "
            f"navázat — odkazuje mimo text, ne do něj. Řekni to prosím "
            f"jménem.",
        )
    offered = discourse.candidates(mention)
    if not offered:
        return (
            None,
            BindingType.GROUP,
            "",
            f"Na koho odkazuje „{mention.form}“? V předchozí větě nikdo "
            f"takový nestojí — a nabídnout uzel odjinud by znamenalo "
            f"tvrdit, že text odkazuje tam, kde nic není. Řekni to prosím "
            f"jménem.",
        )
    which = ", ".join(f"„{m.form}“ ({t.id})" for m, t in offered)
    return (
        None,
        BindingType.GROUP,
        "",
        f"Na koho odkazuje „{mention.form}“? Z předchozí věty to podle "
        f"shody rodu a čísla může být {which}. Rozhodnout to musíš ty — "
        f"shoda je vodítko, ne důkaz, a ztotožnit uzly mlčky je "
        f"nejdražší chyba, jakou můžu udělat.",
    )


#: `(uzel, druh vazby, dovysvětlení, otázka)`. Uzel `None` znamená doptání.
_Resolution = tuple[Term | None, BindingType, str, str | None]

_UNRESOLVED: _Resolution = (None, BindingType.GROUP, "", None)


def _ground_role(
    reading: RoleReading,
    view: ResolvedGraphView,
    relation: Sort | None = None,
    discourse: "Discourse | None" = None,
) -> _Resolution:
    mention = reading.mention

    if reading.resolved:
        # Reference, kterou ROZHODL ČLOVĚK. Nehledá se znovu: rozhodnutí
        # je tah v žurnálu, takže se při přehrání nesmí ptát podruhé —
        # a nesmí ani vyjít jinak, kdyby mezitím v bázi přibyl další
        # kandidát.
        return (
            _sort_for(reading.name, reading.resolved, concrete=True),
            BindingType.RESOLVED_DEFINITE,
            "rozhodl jsi ty",
            None,
        )

    if _presentational_subject(reading):
        # W‑29. Prezentační „to" ve větě „To jsou všichni psi." NEODKAZUJE
        # na nic — je to podmět bez reference, ne zájmeno, u kterého by
        # aktivace pomohla. Ptát se na něj byla otázka BEZ ODBĚRATELE:
        # ať člověk odpoví cokoli, žádný uzel z toho nevznikne a věta se
        # tím nedokončí. Otázka, na kterou neexistuje správná odpověď, je
        # horší než mlčení: říká člověku, že něco chybí, a přitom nechybí.
        return _UNRESOLVED

    if mention.upos in UNSUPPORTED_UPOS:
        return _resolve_anaphor(reading, discourse or Discourse())

    if reading.awaiting == AWAITING_QUANTIFIER:
        return _UNRESOLVED  # otázku už položila kaskáda; nedublovat ji

    if reading.awaiting == AWAITING_REFERENCE:
        return _resolve_definite(reading, view)

    if relation is not None:
        # Strana jádrové relace: sort plyne z RELACE a kvantifikátor se
        # u ní nedrží (§ 3.6), takže se tu neptáme ani na jedno.
        return (
            _sort_for(reading.name, name_of(mention), concrete=False, relation=relation),
            BindingType.FROM_ROLE,
            "sort z jádrové relace",
            None,
        )

    if reading.name in UNQUANTIFIED_ROLES:
        # Místo a čas kvantifikátor nemají a mít nesmí — role sama určuje
        # sort, takže se tu není na co ptát.
        return (
            _sort_for(reading.name, name_of(mention), concrete=False),
            BindingType.FROM_ROLE,
            "místo" if reading.name in PLACE_ROLES else "čas",
            None,
        )

    if reading.quantifier is None:
        return _UNRESOLVED

    if reading.quantifier is Quantifier.SELF and mention.upos == "PROPN":
        return _canonical_name(reading, view)
    return (
        _sort_for(reading.name, name_of(mention), concrete=False),
        BindingType.GROUP,
        "",
        None,
    )


def _canonical_name(reading: RoleReading, view: ResolvedGraphView) -> _Resolution:
    """Vlastní jméno na KANONICKÝ uzel téhož jména (politika Q1, M‑2).

    Doptávat se u každého opakování jména by byl výslech, a protože
    `same_as` je jen pohled a rozdělení uzlu existuje, je tohle ztotožnění
    **plně odvolatelné** — proto tu smí být default, který u kvantifikátoru
    nesmí. Rozdíl je přesně v tom: odvolatelný default s hláškou versus
    neodvolatelný dohad.

    **Řekne se to nahlas** (podmínka A z M‑2). Tichý default by z toho
    udělal přesně tu věc, které se tenhle projekt vyhýbá.

    **Konzultuje se `¬same_as`** (podmínka B). Když je o uzlu řečeno, že
    NENÍ týž jako jiný uzel téhož jména, ztotožnění se nesmí udělat mlčky.
    """
    name = name_of(reading.mention)
    bearers = view.nodes_named(name)
    if len(bearers) > 1:
        # Jméno doloženě nese víc uzlů — typicky po rozdělení. Ztotožnit
        # další zmínku s kterýmkoli z nich by bylo rozhodnutí, které
        # člověk PRÁVĚ VÝSLOVNĚ ODMÍTL udělat; založit třetí uzel by bylo
        # ještě horší, protože by to vypadalo, že se nic nestalo.
        return (
            None,
            BindingType.CANONICAL_PROPN,
            "",
            f"Kterého „{reading.mention.form}“ myslíš? To jméno nese víc "
            f"uzlů: " + ", ".join(bearers) + ". Sám to rozhodnout nemůžu — "
            f"právě proto jsi je rozdělil.",
        )
    node = _sort_for(reading.name, bearers[0] if bearers else name, concrete=True)
    known = view.is_known(node.id)
    # **Jen spor o uzly TÉHOŽ JMÉNA** *(N‑10)*. Podmínka B z M‑2 mluví
    # o případu, kdy je řečeno, že uzel NENÍ týž jako jiný uzel TÉHOŽ
    # JMÉNA — tam ztotožnit mlčky opravdu nejde, protože se neví, který
    # z nich zmínka trefila.
    #
    # Spor s uzlem JINÉHO jména je něco jiného: „Micka není Mourek."
    # nezpochybňuje, KTERÝ uzel se jménem „Micka" se míní — zpochybňuje
    # jejich TOTOŽNOST, a to je práce evaluátoru (M‑1: přes spornou
    # identitu fakty netečou). Odmítnout tu zakotvení znamenalo, že se
    # člověk na spornou identitu nikdy nedozvěděl verdikt: přímá otázka
    # nedala `CONFLICT` a otázka na fakt nedala `U`, obojí skončilo
    # doptáním na to, kdo je kdo.
    disputed = [
        other
        for other in view.index.disputed_with(node.id)
        if other in bearers or other in view.nodes_named(name)
    ]
    if disputed:
        return (
            None,
            BindingType.CANONICAL_PROPN,
            "",
            f"Je „{reading.mention.form}“ týž {node.id}, o kterém už řeč "
            f"byla? Báze si o jeho totožnosti s "
            + ", ".join(disputed)
            + " protiřečí, takže to mlčky ztotožnit nemůžu.",
        )
    if known:
        return (node, BindingType.CANONICAL_PROPN, "týž uzel, o kterém už řeč byla", None)
    return (node, BindingType.CREATED_NEW, "", None)


def _resolve_definite(reading: RoleReading, view: ResolvedGraphView) -> _Resolution:
    """Určitý popis se **dokládá**, nezakládá.

    „To auto" mluví o autě, které už v bázi je. Kdyby se z určitého popisu
    zakládal nový uzel, systém by si na každé zopakování téže věci vyrobil
    dalšího dvojníka a nikdy by se nedozvěděl, že jsou to tíž.

    **I jednoznačné doložení se vypíše** (podmínka z M‑4): odkaz, který
    vyšel na jediného kandidáta, je pořád rozhodnutí systému, ne fakt
    z věty.
    """
    group = name_of(reading.mention)
    found = view.known_members(group)
    if not found:
        return (
            None,
            BindingType.RESOLVED_DEFINITE,
            "",
            f"O kterém „{reading.mention.form}“ mluvíš? V bázi žádný není, "
            f"a určitý popis nezakládá — jen odkazuje.",
        )
    if len(found) > 1:
        return (
            None,
            BindingType.RESOLVED_DEFINITE,
            "",
            f"O kterém „{reading.mention.form}“ mluvíš? Znám jich víc: "
            + ", ".join(sorted(found))
            + ".",
        )
    return (
        Entity(found[0]),
        BindingType.RESOLVED_DEFINITE,
        "jediný kandidát",
        None,
    )


def semantic_rejection(engine: "Engine") -> Callable[[Predication], Rejection | None]:
    """Důvod, proč báze čtení odmítá — nebo `None` (K‑7).

    Vrací se **pojmenovaný** důvod, ne pravdivostní hodnota. Kdyby patro
    dostalo jen `True`/`False`, nemělo by co napsat do stopy, a
    eliminace bez důvodu je přesně to, čemu se K‑7 brání.

    Odmítá se ze tří důvodů a z žádných jiných:

    1. **typová chyba** — zakotvení spadne na sortu nebo kvantifikátoru;
    2. **formální konflikt** — v bázi je doložené `p̄` k tomu, co by
       čtení tvrdilo;
    3. **nesplnitelný constraint** — dotaz na výslednou formuli vyjde
       `CONFLICT`, tedy báze by po zápisu tvrdila `p` i `p̄`.

    **Nezakotvitelné čtení se neodmítá.** Chybějící kvantifikátor není
    rozpor, je to otevřená otázka — a smíchat obojí by znamenalo vyhodit
    čtení za to, že se na ně systém ještě nezeptal.

    **Důvod nese i svou SÍLU** *(A‑21)*. Vrací se `Rejection`, ne řetězec,
    protože první důvod je jiného druhu než zbylé dva: typová chyba mluví
    o TVARU čtení, rozpor a nesplnitelnost o OBSAHU BÁZE. Podle prvního se
    smí čtení zahodit, podle druhých jen snížit priorita — báze se plní
    týmiž větami, které se přes ni filtrují, takže zapsaný omyl nesmí
    umlčet správné čtení. Kdyby síla zůstala schovaná v české větě, musel
    by ji odběratel číst z textu — a to je heuristika tam, kde patří
    typ.
    """

    def reject(predication: Predication) -> Rejection | None:
        try:
            grounded = ground(predication, engine.kb.view())
        except SortError as exc:
            return Rejection(RejectionKind.SORT, f"typová chyba: {exc}")
        if grounded.formula is None:
            return None  # nedá se posoudit, tedy se neodmítá
        result = engine.ask(grounded.formula)
        if result.status is QueryStatus.CONFLICT:
            return Rejection(
                RejectionKind.CONTRADICTED, f"báze tvrdí i opak: {grounded.formula}"
            )
        if result.status is QueryStatus.PROVEN_FALSE:
            return Rejection(
                RejectionKind.CONTRADICTED,
                f"báze má doložené, že {grounded.formula} neplatí",
            )
        return None

    return reject


def ground(
    predication: Predication,
    view: ResolvedGraphView,
    discourse: "Discourse | None" = None,
) -> Grounded:
    """Zmínky na uzly a čtení na formuli.

    **Nic nezapisuje.** Vrátí formuli; zapsat ji je tah `!`, a jen tam smí
    vzniknout nový uzel (§ 0.2).
    """
    anchors: list[Anchor] = []
    notes: list[str] = []
    questions: list[str] = []
    asked: list[int] = []
    fillers = []

    relation_sort = (
        RELATION_SORTS.get(predication.predicate)
        if predication.relation is not None
        else None
    )
    # Sort podle ROLE má přednost před sortem celé relace: `name` je
    # první relace, jejíž strany nejsou na téže ose (uzel × nálepka).
    per_role = ROLE_SORTS.get(predication.predicate, {})
    for reading in predication.roles:
        term, binding, detail, question = _ground_role(
            reading,
            view,
            per_role.get(reading.name, relation_sort),
            discourse or Discourse(),
        )
        if question:
            questions.append(question)
            asked.append(reading.mention.token_index)
        if term is None:
            if not question:
                notes.append(
                    f"[NEZAKOTVENO: role {reading.name} — "
                    + (
                        "čeká na kvantifikátor"
                        if reading.awaiting == AWAITING_QUANTIFIER
                        else "role zůstala povrchová, takže neurčuje sort "
                        "filleru"
                    )
                    + "]"
                )
            continue
        # ČÍM je ztotožnění doložené. Kanonizace jmen je odvolatelný
        # default (M‑2) a říká se nahlas; od chvíle, kdy jméno může přijít
        # z české věty („X se jmenuje Y"), ale nestačí to říct — musí být
        # vidět, KTERÝ výrok tu spojnici nese, jinak se odpověď na otázku
        # o „Honzovi" doloží faktem o „Janovi" a mezi nimi zeje díra.
        justification = view.naming_statement(name_of(reading.mention), term.id)
        anchors.append(
            Anchor(
                reading.mention,
                term,
                binding,
                detail,
                cited=(justification,) if justification else (),
            )
        )
        # Kvantifikátor nese JEN skupina. Individuum, místo ani čas ho
        # `RoleTerm` nepřipustí a je to správně: `∀` nad jedním uzlem nic
        # neznamená a `·` u vlastního jména taky ne — konkrétnost je
        # vlastnost sortu, ne značka navíc. `Operation.SELF` z L‑3 tedy
        # říká „tohle je individuum", a odpověď na to je Entity BEZ
        # kvantifikátoru, ne Entity se značkou `·`.
        fillers.append(
            role(reading.name, term, _quantifier_for(term, reading.quantifier))
        )

    if questions or notes or len(fillers) != len(predication.roles):
        return Grounded(
            anchors=tuple(anchors),
            notes=tuple(notes),
            question=" ".join(questions) if questions else None,
            asked=tuple(asked),
        )

    try:
        formula = atom(
            predication.predicate, *fillers, negated=predication.negated
        )
    except UnquantifiedRole as exc:  # pragma: no cover — pojistka, ne cesta
        return Grounded(
            anchors=tuple(anchors),
            notes=(f"[NEZAKOTVENO: {exc}]",),
        )
    return Grounded(formula=formula, anchors=tuple(anchors))
