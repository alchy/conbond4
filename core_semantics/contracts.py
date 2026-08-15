"""Matice smluv na hranicích vrstev — K‑6 zúžené (dodatek L, L‑6).

**Proč zúžené a proč vůbec.** Poslední tři vážné vady — B‑9 (jméno role),
nepředaná `tiers` a `Utterance.readings` — nebyly vady uvnitř vrstev. Byly
to vady **smlouvy mezi nimi**: jedna vrstva něco slíbila, druhá to četla
jinak, a nikde nestálo, čí to je závazek a co ho hlídá. Matice proto
pokrývá právě ten pruh, na který se napojuje V3:

```
oracle  →  cascade  →  session  →  storage
```

**Sloupce jsou jiné než v původním K‑6, a je to schválně.** Původní
sloupce (syntax · typování · denotace · evaluátor · důkaz · renderer ·
test) popisují **konstruktor metajazyka**. Doložka na hranici vrstev není
konstruktor — nemá denotaci ani důkaz. Má typ, má smysl, někdo ji musí
skutečně **projít** veřejným vstupním bodem, a něco ji musí hlídat.
Předstírat sedm sloupců tam, kde jsou čtyři, by z matice udělalo ozdobu.

**Sloupec `použití` je ten, který by chytil nepředanou `tiers`.** Test nad
`cascade()` volanou napřímo byl zelený, zatímco `Session.utter` patra
nepředávala. Doložka proto říká, PŘES CO se musí jít, a kontrola čte
**zdrojový kód** vynucujících testů a trvá na tom, že tam ten průchod je.

**`OPEN` není hanba, `OPEN` bez důvodu ano.** Doložka, která dnes neplatí,
smí být zapsaná — ale musí říct, co ji zavře. Tichá díra je horší než
zapsaná.

---

**Poučení, které platí na každou dataclass v řetězu, ne jen na tu, kde se
to poprvé projevilo** (doložka O‑7):

> Kdo staví imutabilní strukturu ZNOVU místo `dataclasses.replace`, ztratí
> každé pole, které mezitím přibylo — a ztratí ho BEZ HLÁŠKY.

Vzniklo to na `Predication`: dvě patra ji přestavovala vyjmenováním polí,
takže nově přidaný `negated` tiše zmizel a „Tučňák nelétá" se přejmenováním
rolí měnilo na „Tučňák létá". Konstruktor patří ke ZRODU struktury; každý
další krok ji jen mění, a mění se `replace`. Kdo přidá do řetězu další
vrstvu, dědí tenhle závazek s ní.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from enum import Enum


class Column(Enum):
    """Sloupec matice. Každý je **strojově ověřitelný** — sloupec, který
    se dá jen prohlásit, by měřil dobrou vůli, ne kód."""

    #: Doložku nese skutečný symbol, který jde najít. Chytá přejmenování.
    TYPE = "typ"
    #: U toho symbolu je napsané, co doložka znamená.
    MEANING = "smysl"
    #: Vynucující test jde **veřejným vstupním bodem**, ne obchvatem.
    REACHED = "použití"
    #: Existuje test, který doložku poruší, když se poruší.
    TEST = "test"


class Status(Enum):
    HELD = "drží"
    OPEN = "otevřeno"


@dataclass(frozen=True, slots=True)
class Clause:
    """Jedna doložka smlouvy mezi dvěma vrstvami."""

    id: str
    boundary: str
    promise: str
    #: `modul:atribut.podatribut` — musí jít rozřešit.
    anchor: str
    #: Doslovný úsek, který musí být ve zdroji vynucujícího testu. Tím se
    #: pozná obchvat: „ověřeno" přes vnitřní funkci není ověřeno.
    entry: str
    enforced_by: tuple[str, ...] = ()
    status: Status = Status.HELD
    #: Povinné u `OPEN`: co doložku zavře.
    closes_with: str = ""

    def resolve(self) -> object:
        """Najde symbol, na kterém doložka visí. `AttributeError` znamená,
        že se něco přejmenovalo a matice zestárla."""
        module_name, _, path = self.anchor.partition(":")
        target: object = importlib.import_module(module_name)
        for part in path.split("."):
            target = getattr(target, part)
        return target

    def documented(self) -> bool:
        doc = getattr(self.resolve(), "__doc__", None)
        return bool(doc and doc.strip())


KERNEL_LEARNING = "jádro → učení"
ORACLE_CASCADE = "oracle → cascade"
CASCADE_SESSION = "cascade → session"
SESSION_STORAGE = "session → storage"
STORAGE_CASCADE = "storage → cascade"

BOUNDARIES: tuple[str, ...] = (
    KERNEL_LEARNING,
    ORACLE_CASCADE,
    CASCADE_SESSION,
    SESSION_STORAGE,
    STORAGE_CASCADE,
)


CONTRACTS: tuple[Clause, ...] = (
    # -- jádro → učení -----------------------------------------------------
    Clause(
        id="J-1",
        boundary=KERNEL_LEARNING,
        promise=(
            "predikát, jehož pravdivost MĚNÍ UZÁVĚR nebo UZAVÍRÁ SVĚT, se "
            "nesmí odvozovat pravidlem — členství v `KERNEL_PREDICATES` plyne "
            "z tohohle kritéria, ne z výčtu"
        ),
        anchor="core_semantics.ast:KERNEL_PREDICATES",
        entry="KERNEL_PREDICATES",
        enforced_by=(
            "test_every_predicate_the_index_reads_is_a_kernel_predicate",
            "test_the_criterion_covers_the_whole_set",
            "test_no_learned_rule_may_write_a_protected_predicate",
        ),
    ),
    Clause(
        id="J-4",
        boundary=KERNEL_LEARNING,
        promise=(
            "zákaz v hlavě je ŠIRŠÍ než jádrová množina: co mění uzávěr, "
            "NEBO je to jazyk, kterým se fakty zapisují (role). Jen na "
            "hlavu — pravidlo smí roli číst, nesmí ji vyrábět"
        ),
        anchor="core_semantics.ast:PROTECTED_HEADS",
        entry="PROTECTED_HEADS",
        enforced_by=(
            "test_the_head_guard_is_wider_than_the_closure_criterion",
            "test_a_rule_may_read_a_role_but_not_produce_one",
        ),
    ),
    Clause(
        id="J-5",
        boundary=KERNEL_LEARNING,
        promise=(
            "POŘADÍ literálů v těle není význam: `attach_rule` tělo "
            "normalizuje do KANONICKÉHO bezpečného pořadí, a když bezpečné "
            "pořadí neexistuje, odmítne pravidlo U ZÁPISU. Které role musí "
            "být vázané, čte zápis i evaluátor z JEDNOHO seznamu — dvě kopie "
            "by se rozešly a zápis by pustil, co vyhodnocení odmítne. "
            "Vázanost se hledá REKURZIVNĚ i uvnitř algebraického termu, "
            "protože `substitute` do něj sestupuje (G‑2)"
        ),
        anchor="core_semantics.ast:REQUIRES_BOUND",
        # Průchod je `attach_rule`, ne `_safe_body`. Doložka o normalizaci
        # ověřená voláním vnitřní funkce by netvrdila nic o tom, co se
        # doopravdy zapíše do báze.
        entry="attach_rule(",
        enforced_by=(
            "test_every_permutation_normalises_to_the_same_body",
            "test_an_unorderable_rule_is_refused_at_write_time",
            "test_normalisation_does_not_let_a_negated_literal_bind",
            "test_requires_bound_agrees_with_the_engine",
            "test_a_variable_hidden_in_an_algebraic_term_is_not_bound",
            "test_a_bound_variable_in_an_algebraic_term_is_still_allowed",
        ),
    ),
    Clause(
        id="J-6",
        boundary=KERNEL_LEARNING,
        promise=(
            "jádrová relace se čte ze STAVBY věty, ale nikdy se nedosazuje "
            "potichu: jednoznačná konstrukce se použije a zapíše do stopy, "
            "dvojznačná se ZEPTÁ a do odpovědi se nezapisuje NIC. `disjoint` "
            "jde `add_disjoint`em, ne `attach`em — jinak by se marker dostal "
            "do indexu a neodvodilo by se z něj nic (N‑2). Jmenná část "
            "s přívlastkem je JEDEN POJEM se složeným lemmatem, ne průnik: "
            "průnik tvrdí intersektivitu, kterou morfologie nerozliší od "
            "lexikalizovaného sousloví (N‑2b). Skládá se v `generate`, tedy "
            "JEDNOU PRO VŠECHNY POZICE — táž fráze musí mířit na týž uzel "
            "bez ohledu na to, kde ve větě stojí; přivlastnění se NESKLÁDÁ, "
            "protože je to vztah ke konkrétnímu uzlu, ne druh (N‑2c). "
            "Slovní druh podmětu je součást tvaru: `PROPN` JE signál "
            "individua, takže tam je relace rozhodnutelná (`member`), "
            "kdežto `NOUN=NOUN` rozhodnutelné není a ptá se. Zápor pohltí "
            "jen `disjoint`, protože ho sama nese; na `member` je kolmý "
            "a přenáší se jako doložené popření (N‑2d)"
        ),
        anchor="core_semantics.cascade:relation_tier",
        # Průchod je `.utter(`, ne `relation_tier`. Patro samo o sobě
        # neříká nic o tom, co se doopravdy zapíše do báze — a právě to
        # je na téhle doložce to podstatné.
        entry=".utter(",
        enforced_by=(
            "test_the_subset_sentence_finally_says_subset",
            "test_the_written_subset_actually_works_as_a_closure",
            "test_the_negated_bare_copula_goes_through_the_right_door",
            "test_the_bare_copula_asks_instead_of_guessing",
            "test_nothing_is_written_while_the_relation_is_undecided",
            "test_the_menu_is_closed",
            "test_an_attribute_makes_one_concept_not_two",
            "test_the_composed_class_is_not_an_intersection",
            "test_the_attribute_is_not_reported_as_a_lost_member",
            "test_the_same_phrase_points_at_the_same_node_in_any_position",
            "test_a_possessive_attribute_is_not_composed",
            "test_a_proper_name_subject_means_membership",
            "test_the_bare_noun_copula_still_asks_even_now",
            "test_a_negated_naming_is_documented_denial_not_disjointness",
            "test_the_disjoint_relation_still_swallows_its_negation",
        ),
    ),
    Clause(
        id="J-3",
        boundary=KERNEL_LEARNING,
        promise=(
            "hrana identity, jejíž výrok je ve SPORU, se v uzávěru "
            "nepoužije — ale přímá otázka dál vrací `CONFLICT`; odebírá se "
            "použití hrany, ne výrok (jádro 0.1.6)"
        ),
        anchor="core_semantics.closures:ClosureIndex.identity_proof",
        entry=".ask(",
        enforced_by=(
            "test_facts_do_not_flow_through_a_disputed_identity",
            "test_the_direct_question_still_reports_the_conflict",
            "test_dispute_also_stops_the_bridge_through_other_closures",
        ),
    ),
    Clause(
        id="J-7",
        boundary=KERNEL_LEARNING,
        promise=(
            "POLARITA patří do shody rolí, ne jen nad ni: negace obrací "
            "monotonii, takže pod negací sedne dotaz `∃` na fakt `∀` "
            "s touž povinností `subset` jako kladné `∀×∀`. Kladná buňka "
            "`∀→∃` zůstává `U` — doplnit ji by byl existenční import, "
            "který § 3.2 zakazuje (B‑13)"
        ),
        anchor="core_semantics.engine:Engine._compat",
        entry=".ask(",
        enforced_by=(
            "test_a_negated_universal_answers_the_existential_question",
            "test_the_positive_cell_still_needs_a_nonempty_class",
            "test_the_query_may_go_narrower_but_never_wider",
            "test_the_vegetarian_conflict_survives_the_correct_reading",
            "test_a_concrete_filler_against_existential_is_still_never_a_match",
        ),
    ),
    Clause(
        id="J-10",
        boundary=KERNEL_LEARNING,
        promise=(
            "IDENTITU vyrobí česká věta: spona mezi dvěma VLASTNÍMI JMÉNY "
            "netvrdí členství (jméno není třída), tvrdí `same_as`; záporná "
            "varianta je táž relace se silnou negací. Kanonizace jmen "
            "(M‑2) odmítá zakotvit jen spor mezi uzly TÉHOŽ JMÉNA — spor "
            "s uzlem JINÉHO jména patří evaluátoru, protože M‑1 na něj "
            "slibuje verdikt (`CONFLICT`, a fakt přes tu identitu padá na "
            "`U`), a otázka je míň než verdikt (N‑10)"
        ),
        anchor="core_semantics.grounding:_canonical_name",
        entry=".utter(",
        enforced_by=(
            "test_canonisation_refuses_when_the_same_name_is_disputed",
            "test_a_dispute_with_another_name_gets_a_verdict_not_a_question",
        ),
    ),
    Clause(
        id="J-8",
        boundary=KERNEL_LEARNING,
        promise=(
            "jádrová relace nad ČASEM nebo MÍSTEM se dá vyrobit ČESKOU "
            "VĚTOU a její strany dostanou sort Z RELACE, ne ze jména role "
            "(`whole`/`part` má `contains` i `within`, takže jméno "
            "nestačí). Kvantifikátor takové strany nenesou (§ 3.6). "
            "Schopnost, ke které jazyk nevede, se nedá odlišit od "
            "schopnosti, která nefunguje (N‑9)"
        ),
        anchor="core_semantics.ast:RELATION_SORTS",
        entry=".utter(",
        enforced_by=(
            "test_a_czech_sentence_finally_produces_before",
            "test_the_sides_are_intervals_not_groups",
            "test_the_answer_needs_a_transitive_step",
            "test_the_opposite_direction_is_unknown_not_false",
        ),
    ),
    Clause(
        id="J-9",
        boundary=KERNEL_LEARNING,
        promise=(
            "hrana, která by uzavřela uspořádání do KRUHU, se odmítá "
            "U ZÁPISU a hláška JMENUJE výroky, které ten kruh tvoří. "
            "Selhání zápisu je tah dialogu (§ 9); rozbít se až u příští "
            "otázky, a výjimkou, která uteče ze sezení ven, je nejhorší "
            "možná chvíle. Konzervativní default H‑3 v uzávěru ZŮSTÁVÁ "
            "jako druhá obrana. Varianta „nechat zápis projít a odpovídat "
            "CONFLICT se dvěma důkazy` zůstává OTEVŘENÁ (I‑13) — tenhle "
            "guard ji nevylučuje. `before` je STRIKTNÍ, takže smyčka na "
            "sebe je kruh o jednom uzlu a odmítá se stejně (B‑16). ZNÁMÁ "
            "MEZ: ze strany IDENTITY jde kruh uzavřít dál — `same_as` "
            "zábranu na hraně obejde (W‑22)"
        ),
        anchor="core_semantics.storage:KnowledgeBase._refuse_ordering_cycle",
        entry="attach(",
        enforced_by=(
            "test_the_cycle_is_refused_at_the_door",
            "test_the_refusal_names_the_statements_that_form_the_circle",
            "test_the_base_stays_answerable_after_a_refusal",
            "test_contradictory_ordering_refuses_to_answer",
            "test_a_self_loop_is_a_circle_of_one_node",
            "test_the_base_survives_a_refused_self_loop",
            "test_the_identity_side_is_a_known_limit",
        ),
    ),
    Clause(
        id="J-2",
        boundary=KERNEL_LEARNING,
        promise=(
            "uzávěrový index se staví nad ZÁKLADNÍMI fakty, takže odvozený "
            "jádrový atom by dal `A` bez účinku — proto se na jádrové "
            "predikáty ptá index, ne shoda s faktem. A ptá se ho VŽDYCKY, "
            "než začne odvozovat: zapsaný výrok, který index má, se nesmí "
            "přeskočit ve prospěch zákonů, jinak systém odpoví `U` na "
            "tvrzení, které mu člověk právě řekl (G‑3)"
        ),
        anchor="core_semantics.engine:Engine._match_kernel",
        # Průchod je `ask`, ne `_match_kernel`. Doložka o vnitřní funkci se
        # musí dát ověřit zvenčí, jinak by ji šlo „doložit" testem, který
        # obchází právě to, co se má hlídat.
        entry=".ask(",
        enforced_by=(
            "test_completeness_has_one_door_too",
            "test_direct_question_about_disjointness_ignores_the_stated_order",
            "test_a_stated_fact_about_an_algebraic_term_is_recalled",
            "test_the_recall_cites_the_statement_the_person_made",
            "test_recall_does_not_replace_the_laws",
        ),
    ),
    # -- oracle → cascade --------------------------------------------------
    Clause(
        id="O-1",
        boundary=ORACLE_CASCADE,
        promise=(
            "`Utterance` je JEDNA VĚTA; víc vět je chyba segmentace, "
            "ne dvojznačnost"
        ),
        anchor="core_semantics.oracle:UDPipeOracle.parse",
        entry=".parse(",
        enforced_by=(
            "test_two_sentences_are_a_segmentation_error_not_two_readings",
            "test_segment_is_a_separate_operation",
        ),
    ),
    Clause(
        id="O-2",
        boundary=ORACLE_CASCADE,
        promise="čtení jsou MNOŽNÁ od prvního dne, i když model vrací jedno",
        anchor="core_semantics.oracle:Utterance",
        entry="unambiguous",
        enforced_by=("test_readings_are_plural_from_the_start",),
    ),
    Clause(
        id="O-3",
        boundary=ORACLE_CASCADE,
        promise="`provenance` je součást protokolu a je částí klíče keše",
        anchor="core_semantics.oracle:ParseOracle",
        entry=".provenance",
        enforced_by=(
            "test_cache_is_keyed_by_provenance_too",
            "test_cache_stays_out_of_the_way_without_provenance",
            "test_model_upgrade_does_not_hide_behind_the_cache",
        ),
    ),
    Clause(
        id="O-4",
        boundary=ORACLE_CASCADE,
        promise=(
            "prázdná čtení jsou legitimní odpověď („neumím přečíst“), "
            "odlišná od výpadku služby"
        ),
        anchor="core_semantics.oracle:OracleUnavailable",
        entry=".readings",
        enforced_by=(
            "test_service_failure_and_unreadable_sentence_are_different_signals",
        ),
    ),
    Clause(
        id="O-5",
        boundary=ORACLE_CASCADE,
        promise=(
            "kaskáda vidí morfologii JEN přes `Reading`; nerozebírá text znovu "
            "a nedomýšlí rysy"
        ),
        anchor="core_semantics.oracle:Reading.children",
        entry=".children(",
        enforced_by=("test_reading_exposes_the_dependency_tree",),
    ),
    Clause(
        id="O-6",
        boundary=ORACLE_CASCADE,
        promise=(
            "`Polarity=Neg` se čte jako SILNÁ negace `p̄` — ne jako "
            "nepřítomnost důkazu (I‑21)"
        ),
        anchor="core_semantics.cascade:negation_tier",
        # Průchod je `cascade`, ne řetězec „Polarity" — ten je ve fixtuře,
        # ne v testu, a doložka se má ověřovat tím, kudy se jde.
        entry="cascade(",
        enforced_by=(
            "test_strong_negation_is_not_absence_of_proof",
            "test_negative_concord_is_one_negation_not_two",
        ),
    ),
    Clause(
        id="O-7",
        boundary=ORACLE_CASCADE,
        promise=(
            "krok, který imutabilní strukturu MĚNÍ, používá `replace`, ne "
            "konstruktor — co se při vyjmenování polí zapomene, tiše zmizí; "
            "konstruktor patří ke ZRODU struktury a nikam jinam"
        ),
        anchor="core_semantics.cascade:Predication",
        entry="negated",
        enforced_by=("test_negation_survives_the_rest_of_the_cascade",),
    ),
    # -- cascade → session -------------------------------------------------
    Clause(
        id="C-1",
        boundary=CASCADE_SESSION,
        promise=(
            "nezbyl‑li právě jeden kandidát, `decided` je `None` a odpovědí "
            "je OTÁZKA, ne favorit (I‑1)"
        ),
        anchor="core_semantics.cascade:Verdict.decided",
        entry=".utter(",
        enforced_by=("test_undecided_cascade_asks_instead_of_choosing",),
    ),
    Clause(
        id="C-2",
        boundary=CASCADE_SESSION,
        promise=(
            "role v `Predication` jsou jedinečné; okolnost se jmenuje "
            "POVRCHOVĚ z předložky a pádu, sémantika se nehádá (INV‑11)"
        ),
        anchor="core_semantics.cascade:surface_role",
        entry="surface_role",
        enforced_by=(
            "test_surface_role_reads_preposition_and_case_not_semantics",
            "test_two_circumstances_do_not_collide",
        ),
    ),
    Clause(
        id="C-3",
        boundary=CASCADE_SESSION,
        promise=(
            "patra, která čtení PŘEPISUJÍ, běží bez ohledu na to, kolik "
            "kandidátů zbylo"
        ),
        anchor="core_semantics.cascade:cascade",
        entry="cascade(",
        enforced_by=("test_transform_tiers_run_even_when_one_reading_is_left",),
    ),
    Clause(
        id="C-4",
        boundary=CASCADE_SESSION,
        promise="pořadí pater je pořadí § 5.2: morfologie dřív než cokoli statistického",
        anchor="core_semantics.cascade:HARD_TIERS",
        entry="HARD_TIERS",
        enforced_by=("test_hard_tiers_run_morphology_before_anything_statistical",),
    ),
    Clause(
        id="C-5",
        boundary=CASCADE_SESSION,
        promise=(
            "`Predication` nese u skupinového filleru KVANTIFIKÁTOR, jinak "
            "z ní nejde postavit platný atom"
        ),
        anchor="core_semantics.cascade:RoleReading",
        entry="quantifier",
        enforced_by=(
            "test_a_quantified_reading_builds_a_valid_atom",
            "test_explicit_determiner_decides_the_quantifier",
        ),
    ),
    Clause(
        id="C-6",
        boundary=CASCADE_SESSION,
        promise=(
            "holé jméno NEDOSTANE kvantifikátor implicitně — buď je "
            "z naučeného vzoru s proveniencí, nebo se systém zeptá (I‑1, I‑16)"
        ),
        anchor="core_semantics.cascade:quantifier_tier",
        entry=".utter(",
        enforced_by=(
            "test_session_asks_about_the_quantifier_and_replay_repeats_it",
            "test_session_stops_asking_once_the_pattern_is_confirmed",
        ),
    ),
    Clause(
        id="C-8",
        boundary=CASCADE_SESSION,
        promise=(
            "významový token, který se nedostal do žádné role, se HLÁSÍ — "
            "mlčky zahodit kus věty je horší než ji nepřečíst"
        ),
        anchor="core_semantics.cascade:dropped_tokens",
        entry=".utter(",
        enforced_by=("test_dropped_token_is_reported_not_swallowed",),
    ),
    Clause(
        id="C-9",
        boundary=CASCADE_SESSION,
        promise=(
            "`DEFINITE` NENÍ NĚMÁ — mění otázku přes `awaiting`. Položka "
            "menu bez hotové operace jádra je přípustná jen tehdy, když má "
            "viditelný účinek (poučení z B‑11)"
        ),
        anchor="core_semantics.lexicon:Operation",
        entry="ten",
        enforced_by=("test_definiteness_is_not_quantification",),
    ),
    Clause(
        id="C-7",
        boundary=CASCADE_SESSION,
        promise=(
            "otevřená role se z čtení ODVOZUJE, neukládá — proto ji `replay` "
            "zopakuje doslova a žurnál dál drží strukturu, ne odpověď (§ 10)"
        ),
        anchor="core_semantics.cascade:Predication.open_roles",
        entry="replay",
        enforced_by=(
            "test_session_asks_about_the_quantifier_and_replay_repeats_it",
        ),
    ),
    # -- session → storage -------------------------------------------------
    Clause(
        id="S-1",
        boundary=SESSION_STORAGE,
        promise=(
            "`Session` si NAUČENÁ PATRA zapojuje sama — kdo jde veřejným "
            "vstupním bodem, dostane celou kaskádu, ne jen tvrdé filtry"
        ),
        anchor="core_semantics.session:Session.tiers",
        entry=".utter(",
        enforced_by=("test_session_wires_the_learned_role_mappings",),
    ),
    Clause(
        id="S-2",
        boundary=SESSION_STORAGE,
        promise=(
            "patra se staví PŘI KAŽDÉM TAHU znovu, protože báze i lexikon "
            "se mezi tahy mění"
        ),
        anchor="core_semantics.session:Session.tiers",
        entry=".tiers()",
        enforced_by=("test_tiers_follow_the_base_between_turns",),
    ),
    Clause(
        id="S-3",
        boundary=SESSION_STORAGE,
        promise=(
            "do báze se zapíše jen věta zakotvená CELÁ — půlka čtení by "
            "zapsala něco jiného, než člověk řekl"
        ),
        anchor="core_semantics.session:Session.utter",
        entry=".utter(",
        enforced_by=("test_unfinished_reading_writes_nothing_to_the_base",),
    ),
    Clause(
        id="S-4",
        boundary=SESSION_STORAGE,
        promise=(
            "věta, na kterou se systém zeptal, NEJDE do žurnálu — přehrávat "
            "mlčení nedává smysl"
        ),
        anchor="core_semantics.session:Session.utter",
        entry=".journal",
        enforced_by=("test_golden_transcript_prints",),
    ),
    Clause(
        id="S-5",
        boundary=SESSION_STORAGE,
        promise="nové individuum zakládá JEN `attach`, nikdy vyhodnocení (§ 0.2)",
        anchor="core_semantics.storage:KnowledgeBase.attach",
        entry="attach",
        enforced_by=("test_evaluation_creates_no_individuals",),
    ),
    Clause(
        id="S-6",
        boundary=SESSION_STORAGE,
        promise=(
            "z přečtené věty vznikne fakt v bázi (`!`) nebo doložená "
            "odpověď (`?`)"
        ),
        anchor="core_semantics.grounding:ground",
        entry=".utter(",
        enforced_by=(
            "test_assertion_becomes_a_fact_in_the_base",
            "test_question_is_answered_not_written",
        ),
    ),
    Clause(
        id="S-9",
        boundary=SESSION_STORAGE,
        promise=(
            "nový uzel zakládá jen tah `!`; otázka na neznámé jméno je `U`, "
            "ne zápis (§ 0.2, No Chase)"
        ),
        anchor="core_semantics.grounding:Grounded",
        entry=".utter(",
        enforced_by=("test_question_about_an_unknown_name_creates_nothing",),
    ),
    Clause(
        id="S-10",
        boundary=SESSION_STORAGE,
        promise=(
            "zájmena a elipsa jsou VĚDOMĚ venku — potřebují aktivaci (§ 4) "
            "a mez se říká nahlas, nepředstírá se"
        ),
        anchor="core_semantics.grounding:UNSUPPORTED_UPOS",
        entry=".utter(",
        enforced_by=("test_pronoun_is_refused_out_loud",),
    ),
    Clause(
        id="S-7",
        boundary=SESSION_STORAGE,
        promise=(
            "oddělenost má JEDNY dveře: `add_disjoint`, protože se s ní musí "
            "zapsat i dvojice pravidel se silnou negací (§ 5.3); holý marker "
            "`attach` odmítne"
        ),
        anchor="core_semantics.storage:KnowledgeBase.attach",
        entry=".attach(",
        enforced_by=(
            "test_bare_disjoint_marker_cannot_be_attached",
            "test_both_doors_to_disjointness_give_the_same_answer",
        ),
    ),
    Clause(
        id="S-8",
        boundary=SESSION_STORAGE,
        promise=(
            "`disjoint` NENÍ uzávěr, ale derivační cukr nad generovanými "
            "pravidly — odvolání markeru proto smete i je"
        ),
        anchor="core_semantics.storage:KnowledgeBase.add_disjoint",
        entry="add_disjoint",
        enforced_by=(
            "test_disjoint_expands_to_two_strongly_negated_rules",
            "test_revoking_disjoint_cascades_to_derived_rules",
        ),
    ),
    Clause(
        id="S-11",
        boundary=SESSION_STORAGE,
        promise=(
            "kanonizace jména se ŘÍKÁ NAHLAS a konzultuje `¬same_as` — "
            "odvolatelný default s hláškou smí být, neodvolatelný dohad ne"
        ),
        anchor="core_semantics.grounding:BindingType",
        entry=".utter(",
        enforced_by=(
            "test_repeated_name_says_it_is_the_same_node",
            "test_canonisation_refuses_when_the_same_name_is_disputed",
            "test_a_dispute_with_another_name_gets_a_verdict_not_a_question",
        ),
    ),
    Clause(
        id="S-12",
        boundary=SESSION_STORAGE,
        promise=(
            "rozdělení uzlu je ATOMICKÝ tah, deaktivace místo mazání, a "
            "přesměrovaný výrok nese provenienci tahu `!÷`, ne původní „řekls“"
        ),
        anchor="core_semantics.session:Session._split",
        entry="splits(",
        enforced_by=(
            "test_split_provenance_points_at_the_split_turn_not_at_the_person",
            "test_split_moves_the_statements_and_keeps_the_originals_in_history",
        ),
    ),
    Clause(
        id="S-13",
        boundary=SESSION_STORAGE,
        promise=(
            "zlatá sada fixuje CELÝ TAH včetně vazeb zmínek na uzly — "
            "predikace řekne, o kom se mluví, teprve `Anchor` řekne, na "
            "který uzel to přistálo a proč"
        ),
        anchor="core_semantics.grounding:Anchor",
        entry=".utter(",
        enforced_by=(
            "test_dialogue_reads_writes_and_answers_as_recorded",
            "test_dialogue_is_replayable",
        ),
    ),
    Clause(
        id="S-14",
        boundary=SESSION_STORAGE,
        promise=(
            "na otázku systému existuje ODPOVĚĎ jako tah — naučí se z ní "
            "a čekající věta se PŘEČTE ZNOVU; systém, který se umí zeptat "
            "a neumí přijmout odpověď, se neumí učit dialogem"
        ),
        anchor="core_semantics.session:Session._answer_quantifier",
        entry="answers_quantifier(",
        enforced_by=(
            "test_answer_closes_the_question_and_reads_the_sentence_again",
            "test_the_answer_generalises_beyond_this_one_sentence",
        ),
    ),
    Clause(
        id="S-15",
        boundary=SESSION_STORAGE,
        promise=(
            "rozhodnutá reference je TAH v žurnálu — `replay` se neptá "
            "podruhé a nevyjde jinak, když v bázi mezitím přibude kandidát"
        ),
        anchor="core_semantics.session:Session._decide_reference",
        entry="decides_reference(",
        enforced_by=(
            "test_reference_decision_closes_an_ambiguous_definite",
            "test_a_decided_reference_is_not_looked_up_again",
        ),
    ),
    Clause(
        id="S-16",
        boundary=SESSION_STORAGE,
        promise=(
            "`turns_to_learn` (§ 10) má co měřit: nezodpovězená otázka je "
            "`U`, i když ztroskotala už na čtení"
        ),
        anchor="core_semantics.session:Session.turns_to_learn",
        entry="turns_to_learn(",
        enforced_by=("test_turns_to_learn_finally_has_something_to_measure",),
    ),
    Clause(
        id="S-17",
        boundary=SESSION_STORAGE,
        promise=(
            "kanonizace se ptá JMENNÉHO INDEXU, ne shody id s lemmatem — "
            "po rozdělení nese jméno víc uzlů a systém si třetího nevyrobí"
        ),
        anchor="core_semantics.closures:ClosureIndex.nodes_named",
        entry=".utter(",
        enforced_by=(
            "test_h1_a_name_split_apart_is_not_quietly_put_back_together",
        ),
    ),
    Clause(
        id="S-18",
        boundary=SESSION_STORAGE,
        promise=(
            "mezera se NABÍZÍ, ne konstatuje (K‑9) — a je označená jako "
            "HYPOTÉZA, protože systém se ptá, netvrdí (§ 12/5)"
        ),
        anchor="core_semantics.gaps:OpenGoal.render",
        entry="explain(",
        enforced_by=("test_i5_the_gap_is_an_offer_not_a_reproach",),
    ),
    Clause(
        id="S-29",
        boundary=SESSION_STORAGE,
        promise=(
            "důkaz musí DOSÁHNOUT NA VĚTU, kterou člověk řekl: citace "
            "odvozeného výroku (expanze `disjoint` na dvojici pravidel) se "
            "rozvine na jeho PŮVOD — jeden hop přes `derived_from`, ne "
            "rekurze. Nový důkaz se nevymýšlí, strom zůstává; mění se, co "
            "se z něj renderuje. Tělo pravidla se ukáže CELÉ, protože "
            "právě ono spojuje odpověď s tou větou (W‑24)"
        ),
        anchor="core_semantics.presenter:XAIPresenter._origins",
        entry="render_audit_report(",
        enforced_by=(
            "test_the_answer_reaches_the_sentence_the_person_said",
            "test_the_origin_is_cited_not_just_printed",
            "test_the_expansion_is_one_hop_not_a_recursion",
            "test_the_rule_body_is_not_truncated",
            "test_a_fact_without_an_origin_is_unchanged",
        ),
    ),
    Clause(
        id="S-28",
        boundary=SESSION_STORAGE,
        promise=(
            "mezera nabízí JEN články, které evaluátor umí použít: na "
            "jádrový predikát se `⪯` nikdy nezavolá (jde do "
            "`_match_kernel`), takže článek pro ni je nabídka cesty, "
            "kterou vyhodnocení nejde. A NETISKNE se ani hypotéza, po "
            "které by se báze rozbila — opačná hrana uspořádání by "
            "uzavřela cyklus (H‑3); rozhodnutí je v RENDERU, protože "
            "poslední záchranná nabídka se tiskne právě tehdy, když je "
            "`open_goals` prázdné, takže vyprázdnit ji by ji SPUSTILO "
            "(B‑14). U běžného predikátu i u řetězu `member*` návrh "
            "zůstává (W‑19)"
        ),
        anchor="core_semantics.gaps:GapFinder._fact_goals",
        entry="explain(",
        enforced_by=(
            "test_the_reversed_order_offers_nothing_at_all",
            "test_the_silence_says_why",
            "test_every_printed_offer_leads_somewhere",
            "test_a_kernel_query_is_not_offered_a_matching_link",
            "test_a_safe_last_resort_offer_is_still_printed",
            "test_an_ordinary_predicate_still_gets_its_link",
            "test_the_member_chain_still_gets_its_link",
        ),
    ),
    Clause(
        id="S-19",
        boundary=SESSION_STORAGE,
        promise=(
            "metriky § 10 se počítají ze ŽURNÁLU a BÁZE, nemasují se "
            "průběžně — po `revoke` proto klesnou; čítač by chválil práci, "
            "která už neplatí"
        ),
        anchor="core_semantics.metrics:measure",
        entry="measure(",
        enforced_by=(
            "test_metrics_fall_after_a_revoke_because_they_are_a_function_of_state",
            "test_fast_learning_with_many_corrections_does_not_look_good",
        ),
    ),
    Clause(
        id="S-20",
        boundary=SESSION_STORAGE,
        promise=(
            "na ZTRACENÝ významový člen se systém ZEPTÁ a věta se do "
            "doplnění NEZAPÍŠE — zapsat ji oseknutou a po odpovědi znovu "
            "by uložilo dva výroky, z nichž ten první by nikdo neodvolal"
        ),
        anchor="core_semantics.cascade:lost_role_tier",
        entry="names_role(",
        enforced_by=(
            "test_an_incomplete_sentence_is_not_written",
            "test_one_answer_closes_the_whole_class",
        ),
    ),
    Clause(
        id="S-21",
        boundary=SESSION_STORAGE,
        promise=(
            "povrchová role bez naučeného významu je OTÁZKA, ne poznámka: "
            "`v+Loc` je místo (v Praze) i čas (v pondělí) a rozliší to jen "
            "člověk. "
            "V seedu proto NENÍ ani jedna hypotéza — dvě by zůstaly "
            "dvojznačné navždy a jedna by byla tichý default. Otázka se "
            "počítá z HOTOVÉ predikace, ne ze stopy, aby se neptala na "
            "tvary, které pozdější patro spotřebovalo (N‑3)"
        ),
        anchor="core_semantics.cascade:role_question",
        entry=".utter(",
        enforced_by=(
            "test_a_surface_role_without_a_meaning_is_asked_about",
            "test_the_seed_does_not_decide_it_for_anyone",
            "test_one_answer_closes_the_whole_class_of_shapes",
            "test_the_learned_meaning_of_a_shape_is_revocable",
        ),
    ),
    Clause(
        id="S-22",
        boundary=SESSION_STORAGE,
        promise=(
            "PŘEDLOŽKA u sponového kořene vylučuje jmennou část: být "
            "v Praze není být Prahou. Není to pravidlo o významu — role "
            "zůstane POVRCHOVÁ a co znamená, se učí; jen se nepřevezme "
            "jmenná část tam, kde ji stavba vylučuje (N‑4). Ze stejného "
            "důvodu se `iobj` neslévá s `obj`: rozbor ta dvě místa "
            "rozlišuje a slít je znamenalo, že dva členy dostaly touž "
            "roli a věta se nepřečetla vůbec (N‑5b)"
        ),
        anchor="core_semantics.cascade:generate",
        entry="cascade(",
        enforced_by=(
            "test_a_preposition_at_the_root_means_it_is_not_the_nominal_predicate",
            "test_a_nominal_predicate_without_a_preposition_is_untouched",
            "test_the_role_stays_surface_and_is_asked_about",
            "test_an_indirect_object_does_not_collide_with_the_direct_one",
            "test_a_plain_direct_object_is_untouched",
            "test_a_real_indirect_object_keeps_its_own_shape",
        ),
    ),
    Clause(
        id="S-23",
        boundary=SESSION_STORAGE,
        promise=(
            "PŘIVLASTNĚNÍ dělá ze jména URČITÝ POPIS, ne ztracený člen "
            "a ne třídu: věta pak nemluví o všech autech a systém se ptá, "
            "KTERÝ uzel se míní — na to existuje odpověď, kdežto na otázku "
            "po JMÉNU ROLE přivlastnění nezavře žádná. Vlastník se "
            "NEODVOZUJE ze slova: rozbor dá lemma `Filipův`, cesta k uzlu "
            "`Filip` je derivační morfologie, kterou tagger neřeší (N‑6)"
        ),
        anchor="core_semantics.cascade:possessive_of",
        entry=".utter(",
        enforced_by=(
            "test_a_possessive_is_no_longer_a_lost_member",
            "test_the_sentence_stops_being_about_all_cars",
            "test_the_question_now_has_an_answer",
            "test_the_owner_is_not_guessed_from_the_word",
            "test_a_possessive_does_not_become_a_class",
        ),
    ),
    Clause(
        id="S-24",
        boundary=SESSION_STORAGE,
        promise=(
            "otázka se skládá AŽ Z VÝSLEDKU ZAKOTVENÍ: role, kterou "
            "zakotvení doložilo, otevřenou otázku nemá a značka `◐` se "
            "řídí týmž stavem. Ptát se na to, co si systém právě sám "
            "zodpověděl, je horší než otázka bez odběratele — odpověď by "
            "přišla k rozhodnutí, které padlo, a mohla by správnou vazbu "
            "přepsat (G‑4)"
        ),
        anchor="core_semantics.session:Session._settle",
        entry=".utter(",
        enforced_by=(
            "test_a_resolved_reference_leaves_no_question",
            "test_a_completed_sentence_is_not_marked_incomplete",
            "test_two_candidates_still_ask_and_do_not_write",
            "test_an_open_quantifier_is_not_silenced_by_the_fix",
        ),
    ),
    Clause(
        id="S-27",
        boundary=SESSION_STORAGE,
        promise=(
            "kvantifikátor jde rozhodnout PRO JEDNU VĚTU, a takový tah se "
            "NIC NEUČÍ: týž tvar znamená v jedné větě `∀` a v druhé `∃` "
            "(vegetarián nejí maso × Petr jedl steak), takže tvarová "
            "odpověď by druhou větu přečetla špatně a nezeptala se. Tah na "
            "TVAR zůstává — jsou to dvě různé otázky, ne náhrada (N‑8)"
        ),
        anchor="core_semantics.session:Session._answer_here",
        entry="answers_here(",
        enforced_by=(
            "test_the_sentence_level_answer_closes_the_role",
            "test_the_sentence_level_answer_teaches_nothing",
            "test_the_shape_level_answer_still_teaches",
            "test_answering_a_role_that_does_not_wait_is_refused",
            "test_a_sentence_level_answer_does_not_leak_into_the_next_sentence",
        ),
    ),
    Clause(
        id="O-8",
        boundary=ORACLE_CASCADE,
        promise=(
            "MORFOLOGICKÝ RYS SE POROVNÁVÁ PRŮNIKEM HODNOT, ne rovností "
            "řetězce. UD píše víceznačný tvar výčtem („sbírala“ nese "
            "`Gender=Fem,Neut`, `Number=Plur,Sing“), a to je PŘIZNANÁ "
            "VÍCEZNAČNOST, ne konjunkce dvou tvrzení; rovnost by žádala, "
            "aby byl podmět stejně víceznačný jako přísudek, a zahodila "
            "by každou větu s homonymním tvarem a jednoznačným podmětem — "
            "v češtině běžný případ. Chybějící rys shodu NERUŠÍ (co se "
            "neříká, nedá se popřít). Shoda se kontroluje v ČÍSLE i "
            "RODĚ: bez rodu by po přechodu na průnik prošlo „Psi byla“, "
            "protože na čísle je průnik neprázdný. Táž funkce rozhoduje "
            "i o kandidátovi na antecedent — dvě kopie by se rozešly "
            "(W‑32)"
        ),
        anchor="core_semantics.cascade:feature_values",
        # Průchod je patro, ne funkce: co se doopravdy zahodí, se na
        # porovnání dvou množin nepozná.
        entry="agreement_tier(",
        enforced_by=(
            "test_a_homonymous_predicate_no_longer_rejects_an_unambiguous_subject",
            "test_an_impossible_agreement_is_still_rejected_out_loud",
            "test_a_missing_feature_never_breaks_the_agreement",
            "test_the_intersection_is_computed_from_one_shared_helper",
            "test_agreement_decides_the_motivating_case_without_learning",
        ),
    ),
    Clause(
        id="O-9",
        boundary=ORACLE_CASCADE,
        promise=(
            "u KVANTIFIKOVANÉHO PODMĚTU se shoda počítá proti "
            "KVANTIFIKÁTORU, ne proti tomu jménu: „několik měření … "
            "podpořilo“ má přísudek ve STŘEDNÍM JEDNOTNÉM a jméno "
            "v genitivu plurálu. Pravidlo je KLADNÉ, ne výjimka — kdyby "
            "patro u `det:numgov` shodu jen vyplo, byla by to díra "
            "a prošlo by i „Několik hostů přišli.“; ověřuje se, co ta "
            "konstrukce v češtině ŽÁDÁ, takže věta, která to poruší, PADNE "
            "DÁL. Řídící člen se čte z JMENOVKY ROZBORU (`det:numgov` — UD "
            "jím říká, že determinátor řídí pád své hlavy), ne ze seznamu "
            "slov: seznam by byl druhé místo, kde se to rozhoduje, a "
            "rozešel by se s parserem. KOORDINOVANÝ podmět má "
            "vlastní větev s OPAČNÝM požadavkem (W‑35) a ty dvě se nesmí "
            "plést"
        ),
        anchor="core_semantics.cascade:_quantified",
        entry="agreement_tier(",
        enforced_by=(
            "test_a_quantified_subject_no_longer_blocks_the_reading",
            "test_a_quantified_subject_with_a_plural_predicate_still_falls",
            "test_the_controller_is_read_from_the_parse_label_not_from_a_word_list",
            "test_the_two_branches_never_swap_places",
        ),
    ),
    Clause(
        id="O-10",
        boundary=ORACLE_CASCADE,
        promise=(
            "u KOORDINOVANÉHO PODMĚTU je řídícím členem CELÁ KOORDINACE: "
            "„Karel a jeho bratr Josef BYLI…“ — koordinace, která SČÍTÁ "
            "a jejíž přísudek stojí ZA podmětem, žádá MNOŽNÉ číslo, ať UD "
            "označí jako `nsubj` kohokoli. Pravidlo ZÚŽILO MĚŘENÍ, ne "
            "úvaha: verze „dva a víc členů → plurál“ shodila na korpusu "
            "sedm bezvadných vět. Disjunkce („či“) nabízí ALTERNATIVU, ne "
            "součet, a přísudek PŘED podmětem se smí shodovat "
            "s nejbližším členem — obojí je legitimní jednotné číslo. Pravidlo je "
            "KLADNÉ jako u kvantifikace: „Petr a Pavel četl knihu.“ padne "
            "a řekne proč. Koordinace se pozná z hrany `conj`, ne ze "
            "spojky — „a“ spojuje i dvě věty nebo dva přívlastky. ROD SE "
            "U KOORDINACE NEOVĚŘUJE a je to PŘIZNANÁ MEZ: čeština ho "
            "neřeší průnikem, ale pravidly (muž + žena → mužský životný), "
            "a tohle patro to pravidlo celé nemá; tichý default na místě, "
            "kde se rozhoduje o zahození čtení, by byl horší než přiznaná "
            "neúplnost (W‑35)"
        ),
        anchor="core_semantics.cascade:_coordinated",
        entry="agreement_tier(",
        enforced_by=(
            "test_a_coordinated_subject_no_longer_blocks_the_reading",
            "test_a_disjunction_does_not_demand_the_plural",
            "test_a_conjunction_still_demands_the_plural",
            "test_a_predicate_before_the_subject_may_agree_with_the_nearest",
            "test_a_coordination_that_does_not_demand_the_plural_still_accepts_it",
            "test_the_three_states_are_distinguishable",
            "test_a_coordinated_subject_with_a_singular_predicate_still_falls",
            "test_the_gender_of_a_coordination_is_a_declared_limit",
            "test_a_quantified_subject_is_not_treated_as_a_coordination",
            "test_the_two_branches_never_swap_places",
        ),
    ),
    Clause(
        id="C-10",
        boundary=CASCADE_SESSION,
        promise=(
            "VEDLEJŠÍ VĚTA se spojkou je ROLE hlavní predikace a jméno té "
            "role nese SPOJKA — „Odjel, PROTOŽE pršelo“ je `proč`. Tím se "
            "liší od genitivního přívlastku: tam byl směr vlastností VĚTY "
            "a naučit se nedal, tady je odpověď v TVARU, takže se NAUČIT "
            "SMÍ a druhá věta s touž spojkou se neptá. Bere se jen `advcl` "
            "POD PŘÍSUDKEM a jen SE SPOJKOU: `advcl` pod jménem je "
            "přívlastek toho jména (patří k `acl`), a bez spojky není "
            "z čeho jméno role přečíst — hádat ho z pořadí slov by "
            "znamenalo vymyslet si význam (INV‑11). Vrací se SPOJKA, ne "
            "jméno role: co znamená, je naučené a odvolatelné tvrzení "
            "v lexikonu, ne seznam schovaný v interpretu. Fillerem je DĚJ, "
            "ne vnořená predikace — reifikovat, neřetězit, jádro "
            "neverzovat. Dokud role nemá jméno, VĚTA SE NEZAPISUJE: jinak "
            "ji odpověď `→@` zapíše podruhé a v bázi leží dva výroky "
            "o téže větě, z nichž ten první nikdo neodvolá (W‑45, B‑19)"
        ),
        anchor="core_semantics.cascade:subordinate_clauses",
        entry=".utter(",
        enforced_by=(
            "test_a_subordinate_clause_becomes_a_role_of_the_main_predication",
            "test_without_a_conjunction_nothing_is_substituted",
            "test_the_conjunction_is_returned_not_the_role_name",
            "test_a_clause_under_a_noun_is_not_taken",
            "test_the_other_embedded_relations_are_untouched",
            "test_the_second_level_of_nesting_falls_out_loud",
            "test_the_learned_conjunction_stops_asking_on_the_next_sentence",
            "test_a_sentence_with_an_unnamed_subordinate_role_is_not_written",
        ),
    ),
    Clause(
        id="S-36",
        boundary=SESSION_STORAGE,
        promise=(
            "GENITIVNÍ PŘÍVLASTEK je DRUHÝ VÝROK vedle věty, ne role "
            "predikace: „zvířat“ visí jako `nmod` pod „chov“, tedy pod "
            "JMÉNEM, a predikace nese role PŘÍSUDKU. Větě proto nechybí "
            "predikát a zápis se kvůli němu NEBLOKUJE — blokovat by "
            "znamenalo zadržet větu kvůli něčemu, co v ní není. Mezi "
            "ZTRACENÉ ČLENY nepatří a nehlásí se jako zahozený: dvě "
            "hlášky o jedné věci, které si odporují, jsou horší než "
            "jedna. Tah `→@1` zapíše vztah po odpovědi a NIC SE JÍM "
            "NEUČÍ — „chov zvířat“ a „péče majitele“ mají týž tvar "
            "a opačný směr, takže naučit ho jako tvar by znamenalo "
            "přečíst druhou větu naruby; druhá věta se ptá znovu. "
            "Pět měřených významů se liší PRÁVĚ jménem role, takže menu "
            "není nový druh rozhodnutí (W‑39)"
        ),
        anchor="core_semantics.cascade:genitive_attributes",
        entry=".utter(",
        enforced_by=(
            "test_the_sentence_is_written_even_though_the_attribute_waits",
            "test_the_attribute_is_not_reported_as_a_dropped_member",
            "test_the_second_statement_needs_the_answer",
            "test_the_same_form_can_take_a_different_role",
            "test_nothing_is_learned_so_the_next_sentence_asks_again",
        ),
    ),
    Clause(
        id="O-11",
        boundary=ORACLE_CASCADE,
        promise=(
            "VÍCESLOVNÉ JMÉNO je JEDEN UZEL. „Josef Hora“ není hlava "
            "s přívlastkem — UD to říká hranou `flat` — a dokud se ta "
            "hrana zahazovala, četla se věta jako fakt o uzlu `Josef`. "
            "Nebyla to ztráta členu, byl to ZÁPIS O JINÉM UZLU: „Karel "
            "Čapek“ a „Karel Poláček“ by tiše splynuli v jeden a "
            "nepoznalo by se to, protože obojí by vypadalo jako doložený "
            "fakt o Karlovi. Díly se skládají do LEMMATU v pořadí podle "
            "POZICE v textu a hlásí se jako POHLCENÉ, ne zahozené. Stráž "
            "je úzká: `flat` pod OBECNÝM jménem není jméno, ale seznam "
            "(B‑21)"
        ),
        anchor="core_semantics.cascade:name_parts_of",
        entry="generate(",
        enforced_by=(
            "test_a_multiword_name_is_one_node",
            "test_two_people_sharing_a_first_name_do_not_merge",
            "test_the_name_parts_are_absorbed_not_dropped",
            "test_the_order_of_name_parts_follows_the_text",
            "test_a_flat_under_a_common_noun_is_not_a_name",
        ),
    ),
    Clause(
        id="S-38",
        boundary=SESSION_STORAGE,
        promise=(
            "ŽURNÁL NESE OTISK VÝCHOZÍHO LEXIKONU. Od chvíle, kdy je "
            "lexikon výchozím stavem přehrání (B‑20), platí determinismus "
            "jen PODMÍNĚNĚ (týž žurnál a týž výchozí stav) a KTERÝ to "
            "byl, žurnál dosud neříkal: dvě přehrání téhož žurnálu "
            "s různým lexikonem vypadala obě autoritativně a nic je "
            "nerozlišilo. Otisk leží v ŽURNÁLU, ne v sezení, takže "
            "přežije uložení, a razí se na PRVNÍ tah — lexikon se během "
            "dialogu učením rozrůstá, takže pozdější otisk by říkal něco "
            "jiného než to, s čím se začínalo. Neshoda přehrání NEZASTAVÍ "
            "(lexikon se legitimně rozrůstá a odmítnutí by nutilo ořezávat "
            "ho uměle), ale TIŠE PROJÍT NESMÍ: identita běhu nesmí být "
            "nic, co se dá dvakrát obsadit (W‑51)"
        ),
        anchor="core_semantics.session:Session.check_journal_lexicon",
        entry="replay(",
        enforced_by=(
            "test_replay_with_a_different_lexicon_says_so",
            "test_the_fingerprint_lives_in_the_journal_not_in_the_session",
            "test_dialogue_is_replayable",
        ),
    ),
    Clause(
        id="S-37",
        boundary=SESSION_STORAGE,
        promise=(
            "PŘÍSUDEK SE POZNÁ ZE STRUKTURY, ne ze slovního druhu. Trpná "
            "věta má kořen `ADJ` (příčestí „pohřben“) a pomocné sloveso "
            "pod ním jako `aux:pass`; výčet `(\"VERB\", \"AUX\")` na to "
            "byl slepý, takže se trpná věta BEZ PODMĚTU zapsala BEZ "
            "PODMĚTU — jako fakt o nikom, a nic to neřeklo. Je to potřetí "
            "táž třída jako W‑32 (rysy řetězcem) a W‑47 (deprel řetězcem): "
            "kategorie, která má variantu. Když `nsubj:pass` JE, podmět "
            "vynechaný NENÍ a patro se neptá — nesmí se to rozejít se "
            "survey W‑47. Jméno bez pomocného slovesa přísudek není. "
            "PODMĚT VYJÁDŘENÝ CELOU VĚTOU (`csubj`) je VYSLOVENÝ podmět: "
            "tvrdit o takové větě, že podmět nemá, je nepravdivý výrok "
            "o textu, a na jeho základě by systém zval člověka, aby "
            "dosadil podmět tam, kde jeden stojí. Mlčet by ale bylo taky "
            "nepřesné — dosadit větu za fillér zatím neumíme — takže se "
            "řekne PŘESNĚ TO. Rozdíl mezi „neřečeno“ a „řečeno, neumím“ "
            "drží projekt i jinde (W‑48, B‑18)"
        ),
        anchor="core_semantics.cascade:_is_predicate",
        entry=".utter(",
        enforced_by=(
            "test_a_subjectless_passive_no_longer_writes_a_fact_about_nobody",
            "test_a_passive_with_a_subject_is_not_treated_as_pro_drop",
            "test_the_predicate_is_recognised_from_structure_not_from_upos",
            "test_a_nominal_root_without_an_auxiliary_is_not_a_predicate",
            "test_a_clausal_subject_is_not_reported_as_missing",
            "test_it_says_what_it_cannot_do_instead_of_staying_silent",
            "test_the_subject_deprels_are_a_named_constant",
            "test_a_genuinely_subjectless_sentence_still_asks",
        ),
    ),
    Clause(
        id="S-35",
        boundary=CASCADE_SESSION,
        promise=(
            "VĚTA BEZ PODMĚTU (český pro‑drop) se NEZAPÍŠE DEKAPITOVANÁ. "
            "Dřív se „Narodil se v Praze.“ uložila jako `narodit(kde:…)`, "
            "tedy jako fakt O NIKOM, a nic to neřeklo — v encyklopedické "
            "próze by se takové věty ukládaly jedna za druhou. Podmět "
            "v predikaci VZNIKNE a ČEKÁ na rozhodnutí; zmínkou je sám "
            "PŘÍSUDEK, protože rod a číslo jsou na něm a do textu se "
            "nepřidávají slova, která tam nejsou. Kandidát se NAVRHUJE "
            "z předchozí zakotvené věty a rod se KONTROLUJE: rys s víc "
            "hodnotami („Fem,Neut“) se porovnává PRŮNIKEM, ne rovností, "
            "takže vodítko kandidáty zužuje a nerozhoduje. Přísudek, "
            "který o podmětu neříká nic, nenabídne nikoho"
        ),
        anchor="core_semantics.cascade:prodrop_tier",
        entry=".utter(",
        enforced_by=(
            "test_a_subjectless_sentence_is_no_longer_written_headless",
            "test_the_candidate_is_offered_from_the_previous_sentence",
            "test_the_gender_on_the_predicate_is_checked",
            "test_a_multi_valued_feature_is_compared_by_intersection",
            "test_nothing_is_written_before_the_subject_is_decided",
            "test_after_the_decision_the_fact_lands_on_that_node",
            "test_a_predicate_that_says_nothing_about_the_subject_offers_nobody",
        ),
    ),
    Clause(
        id="S-34",
        boundary=CASCADE_SESSION,
        promise=(
            "KONTEXT TEXTU: sezení si pamatuje, co bylo zakotveno ve větě "
            "PŘEDTÍM, a z toho NAVRHUJE antecedenty zájmen. Je to nová "
            "INFORMACE, ne nová inference — nic se z ní neodvozuje, jen "
            "se z ní nabízí. Shoda rodu a čísla kandidáty jen ZUŽUJE, "
            "nikdy nevybírá, a systém se ptá i tehdy, když je kandidát "
            "JEDINÝ (I‑13): rozdíl mezi „trefil jsem týž uzel“ a „člověk "
            "řekl, že to je týž“ je celá M‑2 a tichý default u identity "
            "uzly tiše slije nebo rozštěpí. Dokud rozhodnutí nepadne, "
            "NEZAPISUJE SE NIC. Kandidát, který v předchozí větě není, se "
            "NENABÍDNE, a skupina se nenabídne nikdy — zájmeno odkazuje "
            "na uzel, ne na třídu. Kontext se posouvá jen po větě, která "
            "se opravdu zakotvila"
        ),
        anchor="core_semantics.grounding:Discourse",
        entry=".utter(",
        enforced_by=(
            "test_the_antecedent_is_offered_from_the_previous_sentence",
            "test_nothing_is_written_before_the_reference_is_decided",
            "test_it_asks_even_when_the_candidate_is_the_only_one",
            "test_a_candidate_that_is_not_in_the_previous_sentence_is_not_offered",
            "test_a_group_is_never_offered_as_an_antecedent",
            "test_after_the_decision_the_fact_lands_on_the_same_node",
            "test_the_question_about_that_node_is_then_answered",
            "test_without_the_answer_the_question_stays_unknown",
            "test_the_context_moves_only_after_a_sentence_that_grounded",
        ),
    ),
    Clause(
        id="S-32",
        boundary=SESSION_STORAGE,
        promise=(
            "POJMENOVÁNÍ se čte ze stavby „X se jmenuje Y“ a strany určuje "
            "DEPREL, ne pořadí kandidátů: obě jména jsou v nominativu, "
            "takže podle pořadí by se jednou zapsalo `name(Jan, Honza)` "
            "a podruhé pravý opak. Bez zvratného „se“ to pojmenování NENÍ "
            "(jmenovat DO funkce). Konstrukce se DOSAZUJE, neptá se — "
            "`jmenovat se` druhé čtení nemá (táž úvaha jako N‑2d) — a do "
            "menu holé spony `name` NEPATŘÍ, protože to je vztah uzlu "
            "a nálepky, ne dvou tříd. Strany mají RŮZNÝ sort (`of` uzel, "
            "`value` nálepka), takže jeden sort na celou relaci nestačí. "
            "Odpověď, která se na uzel dostala přes jméno, CITUJE i výrok, "
            "kterým je to jméno na uzel navázané: zakotvení není premisa, "
            "ale bez něj by se dotaz netrefil"
        ),
        anchor="core_semantics.cascade:naming_tier",
        entry=".utter(",
        enforced_by=(
            "test_the_sides_come_from_deprels_not_from_candidate_order",
            "test_without_the_reflexive_it_is_not_naming",
            "test_the_construction_is_substituted_not_asked",
            "test_naming_is_not_in_the_bare_copula_menu",
            "test_the_two_sides_get_different_sorts",
            "test_before_the_naming_the_alias_is_a_stranger",
            "test_after_the_naming_the_alias_reaches_the_node",
            "test_the_answer_cites_the_statement_that_links_the_name",
            "test_the_link_is_revocable_like_any_other_statement",
        ),
    ),
    Clause(
        id="S-33",
        boundary=CASCADE_SESSION,
        promise=(
            "OTÁZKA BEZ ODBĚRATELE SE NEPTÁ. Role, jejíž význam je znám a "
            "jen se kanonickým jménem srazila s jinou toutéž, se NEHLÁSÍ "
            "jako neznámá — je to kolize, ne neznalost, a jediná odpověď, "
            "kterou by člověk mohl dát, je právě ta, která ji způsobila "
            "(W‑20). Prezentační „to“ ve „To jsou všichni psi.“ NEODKAZUJE "
            "na nic, takže se na jeho referenci neptá (W‑29); určitý popis "
            "(„ten pes“) uzel MÍNÍ a doptat se na něj správné zůstává. "
            "Značka kolize má VLASTNÍ pole, ne poznámku v `source`: to "
            "pole vlastní ten, kdo roli naposled sáhl, a přepsal by ji "
            "(táž lekce jako B‑17)"
        ),
        anchor="core_semantics.cascade:surface_roles",
        entry=".utter(",
        enforced_by=(
            "test_a_known_role_whose_canonical_name_collides_is_not_reported_missing",
            "test_the_collision_mark_survives_the_later_tiers",
            "test_the_presentational_subject_is_not_asked_about",
            "test_a_demonstrative_that_does_mean_a_node_is_still_asked_about",
        ),
    ),
    Clause(
        id="S-31",
        boundary=SESSION_STORAGE,
        promise=(
            "UZAVŘENÍ SVĚTA se z české věty jen NAVRHUJE, nikdy nedosadí — "
            "ani při jednoznačném tvaru. `complete(g)` je jediný výrok, "
            "který mění, co znamená TICHO: do něj platí I‑21 („absence "
            "není negace“) bez výjimky, od něj se o každém mimo výčet "
            "odpovídá `N` místo `U`. Tah `!∀` se proto NIC NEUČÍ — "
            "uzavření není vlastnost jazyka, ale epistemický stav "
            "mluvčího o jedné skupině v jednom okamžiku — a je "
            "ODVOLATELNÝ. Popření cituje OBĚ půlky, prohlášení i VÝČET, "
            "nad kterým se zavíralo; bez výčtu se závěr nedá zkontrolovat. "
            "Žádné pravidlo `complete` nevyrobí (`PROTECTED_HEADS`)"
        ),
        anchor="core_semantics.cascade:completeness_tier",
        entry=".utter(",
        enforced_by=(
            "test_the_presentational_total_construction_proposes_a_closure",
            "test_a_general_claim_about_all_dogs_closes_nothing",
            "test_nothing_is_written_while_the_closure_is_only_proposed",
            "test_the_closure_teaches_nothing_so_the_next_one_asks_again",
            "test_before_the_declaration_the_answer_is_unknown",
            "test_after_the_declaration_the_absence_becomes_a_denial",
            "test_the_denial_cites_the_declaration_and_the_enumeration",
            "test_revoking_the_declaration_returns_the_answer_to_unknown",
            "test_a_member_of_the_closed_group_is_still_proven",
            "test_a_closure_never_appears_without_someone_declaring_it",
        ),
    ),
    Clause(
        id="S-30",
        boundary=SESSION_STORAGE,
        promise=(
            "čekající KONSTRUKCE zastaví zápis stejně jako čekající "
            "kvantifikátor — je to táž třída rozhodnutí a tichý default je "
            "u ní zakázaný stejně (L‑3). Tvar, na jehož význam se čeká, "
            "visí na PREDIKACI, ne ve stopě: stopa je log jednoho tahu, "
            "takže odpověď na cokoli jiného ji zahodí a otázka se ZTRATÍ — "
            "věta se pak zapíše jako obyčejný vztah `být`, přestože systém "
            "v téže odpovědi říká, že tomu tvaru nerozumí, což je zápis "
            "pod přiznanou neznalostí (INV‑11). Táž lekce jako N‑3 a G‑4: "
            "ptát se z HOTOVÉ predikace, ne z logu (B‑17)"
        ),
        # Kotva je FUNKCE, ne pole `Predication.pending_relation`:
        # u pole není co číst jako smysl a doložka by tvrdila víc, než se
        # dá doložit. `relation_question` je místo, kde se ta čekající
        # konstrukce mění v otázku pro člověka.
        anchor="core_semantics.cascade:relation_question",
        # Průchod je `.utter(`: co se doopravdy zapíše do báze, se na
        # samotné funkci nepozná — a právě to je na téhle doložce podstatné.
        entry=".utter(",
        enforced_by=(
            "test_answering_the_quantifier_does_not_write_while_the_relation_waits",
            "test_the_relation_question_survives_an_answer_to_something_else",
            "test_the_waiting_shape_is_carried_by_the_predication_not_the_trace",
            "test_nothing_is_written_while_the_relation_is_undecided",
        ),
    ),
    Clause(
        id="S-25",
        boundary=SESSION_STORAGE,
        promise=(
            "VLASTNÍKA pojmenuje člověk tahem, ne morfologie: z lemmatu "
            "`Filipův` se uzel `Filip` neodvozuje. Co je na TVARU (že "
            "přivlastnění označuje vlastníka) není rozhodnutí a neučí se; "
            "KDO to je, je vlastnost jedné zmínky, takže leží v žurnálu "
            "jako tah, ne v lexikonu jako vzor. Tah PŘIDÁVÁ fakt, "
            "nezapisuje větu znovu, a vlastnictví se připne jen k UZLU "
            "(N‑7)"
        ),
        anchor="core_semantics.session:Session._name_owner",
        entry="names_owner(",
        enforced_by=(
            "test_the_owner_turn_writes_the_ownership",
            "test_the_sentence_is_not_written_twice",
            "test_the_ownership_is_pinned_to_the_node_not_to_the_class",
            "test_without_a_resolved_reference_nothing_is_written",
            "test_the_owner_is_a_decision_not_a_pattern",
            "test_someone_who_never_answers_sees_no_change",
        ),
    ),
    Clause(
        id="S-26",
        boundary=SESSION_STORAGE,
        promise=(
            "`U` se rozkládá podle DŮVODU, ne podle počtu: modul nemá "
            "žádné skóre k minimalizaci, protože vylepšit počet `U` jde "
            "jen hádáním. Kategorie `RECALL_FAILURE` je VADA, ne nález — "
            "tvrzení v bázi JE a systém ho nenašel; přesně to byla G‑3. "
            "Rozklad stojí jen na tom, co `GapFinder` vrátil a co v bázi "
            "leží; nic se nedomýšlí (A‑27)"
        ),
        anchor="core_semantics.unknown_precision:diagnose",
        entry="diagnose(",
        enforced_by=(
            "test_a_stated_fact_answered_unknown_is_a_defect",
            "test_the_defect_check_compares_formulas_not_derivability",
            "test_no_stated_fact_is_forgotten_in_any_kernel_shape",
            "test_the_module_offers_no_score_to_minimise",
            "test_no_dialogue_answer_is_a_recall_failure",
        ),
    ),
    # -- storage → cascade (zpětná hrana) ----------------------------------
    Clause(
        id="B-1",
        boundary=STORAGE_CASCADE,
        promise=(
            "báze smí množinu čtení jen ZÚŽIT, nikdy doplnit — statistika "
            "a báze navrhují, nerozhodují (I‑2)"
        ),
        anchor="core_semantics.cascade:base_consistency_tier",
        entry="base_consistency_tier",
        enforced_by=("test_base_consistency_narrows_but_never_adds",),
    ),
    Clause(
        id="B-5",
        boundary=STORAGE_CASCADE,
        promise=(
            "rozpor s bází čtení NEODSTRAŇUJE, jen mu snižuje prioritu a "
            "pojmenuje ho ve stopě — báze se plní týmiž větami, které se "
            "přes ni filtrují, takže zapsaný omyl nesmí umlčet správné "
            "čtení. Tvrdě odmítat smí JEN typová chyba, protože ta je "
            "o tvaru čtení, ne o obsahu báze (A‑21)"
        ),
        anchor="core_semantics.cascade:Rejection.hard",
        # Průchod je `tier_over`, tedy patro jako celek — stejně jako
        # u B‑3. Doložka ověřená voláním `Rejection.hard` by netvrdila
        # nic o tom, co patro s tím rozlišením doopravdy udělá.
        entry="tier_over(",
        enforced_by=(
            "test_a_contradicting_reading_is_kept_not_dropped",
            "test_the_contradicting_reading_drops_to_the_back",
            "test_a_wholly_contradictory_sentence_is_still_written",
            "test_only_a_sort_error_is_hard",
            "test_a_mistyped_reading_is_still_removed",
        ),
    ),
    Clause(
        id="B-3",
        boundary=STORAGE_CASCADE,
        promise=(
            "báze smí čtení eliminovat JEN z pojmenovaného sémantického "
            "důvodu (K‑7) — známost vztahu důvod NENÍ, to je popularita "
            "a self‑confirming loop"
        ),
        anchor="core_semantics.grounding:semantic_rejection",
        # Průchod je `tier_over`, protože patro je uzávěr nad injektovanou
        # kontrolou — testy ho volají tudy a jinudy k němu vést nemá.
        entry="tier_over(",
        enforced_by=(
            "test_familiarity_is_not_a_reason_to_eliminate_a_reading",
            "test_an_ungroundable_reading_is_not_eliminated_either",
        ),
    ),
    Clause(
        id="B-4",
        boundary=STORAGE_CASCADE,
        promise=(
            "rozporná věta se PŘEČTE, ZAPÍŠE a rozpor se OHLÁSÍ — systém "
            "si stranu nevybírá; nezapsat by znamenalo mlčky rozhodnout "
            "ve prospěch toho, kdo mluvil dřív (I‑3)"
        ),
        anchor="core_semantics.cascade:base_consistency_tier",
        entry=".utter(",
        enforced_by=(
            "test_a_contradictory_sentence_is_recorded_warned_about_and_not_arbitrated",
        ),
    ),
    Clause(
        id="B-2",
        boundary=STORAGE_CASCADE,
        promise=(
            "na PŘÍMOU otázku po oddělenosti odpovídá index, ne shoda "
            "s faktem — marker je jednosměrný, relace symetrická"
        ),
        anchor="core_semantics.closures:ClosureIndex.disjoint_proof",
        entry="disjoint_of",
        enforced_by=(
            "test_direct_question_about_disjointness_ignores_the_stated_order",
        ),
    ),
)


def by_boundary(boundary: str) -> tuple[Clause, ...]:
    return tuple(c for c in CONTRACTS if c.boundary == boundary)


def open_clauses() -> tuple[Clause, ...]:
    return tuple(c for c in CONTRACTS if c.status is Status.OPEN)
