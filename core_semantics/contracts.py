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
        id="S-45",
        boundary=SESSION_STORAGE,
        promise=(
            "ZAPÍŠE SE TO, ČEMU SYSTÉM ROZUMÍ; ZBYTEK ZŮSTANE OTEVŘENÝ "
            "*(W‑79)*. Zápis byl VŠECHNO NEBO NIC: ze 238 vět mělo 220 "
            "čtení a zapsaná byla JEDNA, protože 154 z nich drží "
            "nepojmenovaná role. VE VŠECH 154 JE TA ROLE JEN OKOLNOST — "
            "ani jednou `kdo`, `co` nebo `jak`; přísudek a jádroví "
            "účastníci jsou přečtení. Vynechat okolnost znamená říct "
            "MÍŇ: z „působil **pouze** pět měsíců“ plyne „působil“, "
            "a slabší tvrzení není nepravda. DŮVOD Z B‑19 („uložilo by "
            "DVA výroky a ten první by nikdo neodvolal“) PADL v B‑26: "
            "promluva má rukojeť a doplnění ten částečný výrok ODVOLÁ "
            "s důvodem „doplněno“ — nepřepíše ho, protože báze je "
            "append‑only a auditovatelnost stojí na tom, že se nic "
            "nemaže; v HISTORII proto stojí OBOJÍ. NEPLATÍ TO TAM, KDE "
            "OKOLNOST PRAVDIVOST OBRACÍ NEBO PODMIŇUJE — a rozhoduje "
            "o tom TŘÍDA OPERÁTORŮ z lexikonu (zápor, náhrada, "
            "podmínka, modalita, skoro‑ne), tedy ODVOLATELNÁ DATA "
            "S PROVENIENCÍ, ne seznam vět a ne podmínka v kódu: seznam "
            "vět je vlastnost korpusu, třída je vlastnost jazyka. "
            "Modalita a „skoro‑ne“ jsou v ní PREVENTIVNĚ — v tomhle "
            "korpusu dnes nevadí, ale „téměř zemřel“ neimplikuje "
            "„zemřel“. Nepojmenovaná role se do báze NEDOSTANE ani "
            "částečně, a dotaz na ni dá `U`, ne `A` a ne `N`"
        ),
        anchor="core_semantics.cascade:partial_write",
        entry=".utter(",
        enforced_by=(
            "test_what_is_understood_is_written_and_the_rest_stays_open",
            "test_the_omitted_role_is_unknown_not_false",
            "test_an_operator_that_changes_truth_blocks_the_partial_write",
            "test_completing_a_sentence_leaves_one_statement_and_a_history",
        ),
    ),
    Clause(
        id="S-44",
        boundary=SESSION_STORAGE,
        promise=(
            "CO SE NAUČÍ, MUSÍ JÍT NAJÍT — SPOUŠTĚČ SE STAVÍ Z TÉŽE "
            "SIGNATURY, KTEROU SE PAK HLEDÁ *(B‑27)*. Tah hlásil „✓ "
            "naučeno … platí pro každý tvar `DET/det`“ a TÁŽ VĚTA "
            "v témž sezení se zeptala ZNOVU. Příčina: `lemma` se při "
            "učení ZAHAZOVALO, takže vzor vznikl jako STRUKTURNÍ — a "
            "`Trigger.matches` strukturní vzor se signaturou, která "
            "lemma NESE, z principu nepáruje („dvě různé otázky mají "
            "zůstat oddělené“). Naučené se pak nenašlo; ne špatně "
            "použilo, NENAŠLO SE VŮBEC. Je to nepravda o vlastním stavu "
            "na KANÁLU UČENÍ, o stupeň silnější než S‑39, protože ta "
            "věta slibuje CELOU TŘÍDU a neplatila ani pro doslovné "
            "zopakování téže věty. Lemma se proto nese dál a JE TO "
            "I VÝZNAMOVĚ SPRÁVNĚ: u role s determinátorem kvantifikuje "
            "PRÁVĚ TO SLOVO — „některé“, „jejich“ a „každý“ nejsou "
            "totéž, takže `DET/det → ∃` pro všechny determinátory by byl "
            "tichý default s razítkem naučeného. HLÁŠENÍ ŘÍKÁ, CO SE "
            "OPRAVDU NAUČILO („`DET/det` se slovem „jeho““), a slib se "
            "dokazuje na DRUHÉ větě téhož tvaru. Signatura BEZ lemmatu "
            "se dál učí strukturně a zobecňuje jako dřív — změřeno: "
            "38 tvarů z 38 (32 strukturních, 6 lexikálních) po odpovědi "
            "znovu neptá"
        ),
        anchor="core_semantics.session:Session._answer_quantifier",
        entry=".play(",
        enforced_by=(
            "test_what_was_learned_is_found_again_in_the_same_session",
            "test_the_promise_of_a_class_holds_on_a_second_sentence",
            "test_the_report_says_what_it_actually_learned",
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
            "o téže větě, z nichž ten první nikdo neodvolá (W‑45, B‑19). "
            "A PLATÍ TO PRO KAŽDOU ROLI, JEJÍŽ JMÉNO ZŮSTALO TVAREM, ne "
            "jen pro vedlejší větu: „Petr bydlí v Praze.“ se zapisovala "
            "jako `bydlet(kdo:Petr, v+Loc/Geo:Praha)` a po odpovědi ZNOVU "
            "— v bázi ležely DVA výroky o téže větě a `role(filler:Praha, "
            "name:v+Loc/Geo, of:s0001)`, tedy role POJMENOVANÁ FORMOU, "
            "kterou `XAIPresenter` cituje. Jedna podmínka, jedna odpověď. "
            "NAUČENÉ JMÉNO („proč“) TVAR NENÍ a zapisuje se dál — tam už "
            "někdo odpověděl; rozhoduje značka `shaped` od toho, kdo roli "
            "vyrobil, ne podoba řetězce. A v hlášení je VIDĚT, které "
            "pravidlo zápis zastavilo (W‑62)"
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
            "test_a_learned_role_name_is_not_asked_about_again",
            "test_a_shape_named_role_stops_the_write_wherever_it_is",
            "test_no_role_named_by_its_form_reaches_the_base",
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
            "není nový druh rozhodnutí (W‑39). PÁRUJE SE PŘES TOKEN, NE "
            "PŘES LEMMA: zmínka ve čtení je SLOŽENÁ („první_předseda“ "
            "proti `předseda` v rozboru), takže shoda lemmat přívlastek "
            "přehlédne — posedmé táž rodina (W‑32, W‑47, W‑48, B‑18, "
            "B‑22, W‑53). BUĎ PŘÍVLASTEK, NEBO ROLE, NE OBOJÍ: u SPONY "
            "je jmenná část KOŘENEM, takže její genitiv je jeho DÍTĚ a "
            "rolí se stane, ačkoli u slovesné věty je vnukem a nestane; "
            "stavba se liší, zacházení se lišit nesmí. VÝJIMKA JE JEDNA "
            "a je čitelná ze STAVU, ne ze stromu: genitiv, který si "
            "nárokuje ČEKAJÍCÍ JÁDROVÁ RELACE („Petrovice jsou součástí "
            "Plzně.“), přívlastek NENÍ — je to jedna její strana a bez "
            "něj by odpověď `→⊆` neměla s čím pracovat. A přívlastek je "
            "jen HOLÝ GENITIV: „u starověkých filozofů“ je předložková "
            "fráze, tedy okolnost, a „synonyma filozofů“ ta věta netvrdí "
            "— rozdíl je v rozboru (`deprel=case`). Táž podmínka platí "
            "i v konstrukci jádrové relace, kde se počítá, kolik genitivů "
            "věta má: jedna funkce pro obě místa, protože dvě kopie by se "
            "rozešly (W‑58)"
        ),
        anchor="core_semantics.cascade:genitive_attributes",
        entry=".utter(",
        enforced_by=(
            "test_the_sentence_is_written_even_though_the_attribute_waits",
            "test_the_attribute_is_not_reported_as_a_dropped_member",
            "test_the_second_statement_needs_the_answer",
            "test_the_same_form_can_take_a_different_role",
            "test_nothing_is_learned_so_the_next_sentence_asks_again",
            "test_a_composed_head_keeps_its_genitive_attribute",
            "test_a_genitive_is_either_an_attribute_or_a_role",
            "test_a_pending_kernel_relation_keeps_its_genitive",
            "test_no_mention_is_in_the_reading_twice",
            "test_a_prepositional_genitive_is_not_an_attribute",
            "test_a_prepositional_genitive_does_not_hide_the_construction",
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
            "Skládá se JEN `flat`: `appos` je JINÁ ZMÍNKA téže "
            "věci, ne další díl jména, a když se skládala, vznikl uzel "
            "`Karel_Čapek_Karel` — jméno, které v textu NIKDO NENESE. "
            "Rozhoduje VZTAH, ne slovní druh členu. Identita se z apozice "
            "NEDOSAZUJE: „Karel Čapek, spisovatel“ je role, ne druhé "
            "jméno, a ztotožnit uzly z tvaru by byl tichý default "
            "u identity (M‑2, I‑13) — až se `same_as` z apozice zapisovat "
            "bude, musí se navrhnout a zeptat (B‑21, B‑22)"
        ),
        anchor="core_semantics.cascade:name_parts_of",
        entry="generate(",
        enforced_by=(
            "test_an_apposition_is_not_a_name_part",
            "test_the_name_continuation_is_a_named_constant",
            "test_the_apposition_could_be_identity_but_is_not_guessed",
            "test_a_multiword_name_is_one_node",
            "test_two_people_sharing_a_first_name_do_not_merge",
            "test_the_name_parts_are_absorbed_not_dropped",
            "test_the_order_of_name_parts_follows_the_text",
            "test_a_flat_under_a_common_noun_is_not_a_name",
        ),
    ),
    Clause(
        id="O-12",
        boundary=CASCADE_SESSION,
        promise=(
            "JMÉNO POD TITULEM je TEN ČLOVĚK, ne jeho třída. „básník "
            "Josef Hora“ má jméno jako `flat` pod obecným jménem — a "
            "`flat` znamená JEDNU ZMÍNKU, takže zmínka je `Josef_Hora` "
            "a „básník“ zůstává jen v `form`. NESKLÁDÁ SE: "
            "`básník_Josef_Hora` by byla třída, která není ani básník, "
            "ani Hora, přesně jako `město_Praha` (O‑11). S identitou se "
            "přesouvá i KVANTIFIKÁTOR — `upos` zmínky je `PROPN` podle "
            "JMÉNA, ne `NOUN` podle hlavy: jinak by z věty o jednom "
            "člověku vyšlo `∀Josef_Hora`, tvrzení o všech, kdo se tak "
            "jmenují, a vada by se jen přestěhovala. Pád, číslo a kotva "
            "do rozboru zůstávají HLAVĚ: tu pozici ve větě drží ona. "
            "PROTIPŘÍKLAD JE V ROZBORU, ne ve stráži: „Město Praha“ má "
            "`nmod`, ne `flat`, takže se tím nemění a dál se ptá, jakou "
            "roli „Praha“ hraje (W‑53). JEN JEDNOTNÉ ČÍSLO na titulu: „bratří "
            "**Čapků**“ má touž stavbu, ale je to SKUPINA dvou lidí, ne "
            "jedni bratři jménem Čapka — a `·Čapka` by byla vada vyměněná "
            "za jinou. Skupinu z téhle stavby systém neumí, a než ji "
            "vyrobí špatně, nevyrobí ji (W‑54). Rys se čte PRŮNIKEM, ne "
            "rovností (W‑32), a když chybí, stráž nespustí"
        ),
        anchor="core_semantics.cascade:titled_name_of",
        entry=".utter(",
        enforced_by=(
            "test_the_person_is_the_node_not_the_title",
            "test_the_title_does_not_become_a_class",
            "test_a_modifier_name_is_left_alone",
            "test_the_title_is_absorbed_not_dropped",
            "test_the_quantifier_moves_with_the_identity",
            "test_a_plural_title_is_not_one_person",
            "test_an_ambiguous_number_still_counts_as_singular",
        ),
    ),
    Clause(
        id="O-13",
        boundary=CASCADE_SESSION,
        promise=(
            "TITUL NESE TVRZENÍ a to tvrzení se NABÍDNE, NEZAPÍŠE. "
            "„básník Josef Hora“ říká dvě věci — že promluvil a že je "
            "básník; věta se zapíše, členství se OHLÁSÍ jako výrok vedle "
            "ní a čeká na tah `→∈`. Zapsat ho ze tvaru je ODVOZENÍ "
            "Z KONSTRUKCE, tedy totéž, co se odmítlo u `same_as` "
            "z apozice (B‑22) — a tady je to DOLOŽENÉ ČÍSLEM, ne jen "
            "obhájené: ze 71 zmínek v měřeném korpusu je 29 POVOLÁNÍ, 24 "
            "ÚŘAD DRŽENÝ V ČASE („prezident Masaryk“ zemřel roku 1937) "
            "a 18 PŘÍBUZENSTVÍ („bratr“ KOHO?). Tvar je u všech tří TÝŽ. "
            "DRUHÁ PŮLKA JE HLÁŠENÍ: dokud se nepotvrdí, je verdikt `U` "
            "a to je správně, ale DŮVOD nesmí být „nikdo to neřekl“ — "
            "ta věta to řekla, a mezera, která o sobě lže, je horší než "
            "mezera. Rozbor mezery o titulech nic neví; co je "
            "nerozhodnuté, mu řekne sezení, a páruje se přes ATOM, ne "
            "přes vykreslení. Nic se tím NEUČÍ: „prezident Masaryk“ "
            "v další větě znamená totéž a zeptá se znovu. Stráže se "
            "neopisují — ptá se `titled_name_of`, takže `nmod` („Město "
            "Praha“) ani plurál („bratří Čapků“) tudy nejdou (W‑55). "
            "A `→∈` JE POTVRZENÍ, takže BEZ NABÍDKY SE ODMÍTNE: bez věty "
            "by šel do báze výrok s proveniencí titulu a s hláškou „věta "
            "sama se zapsala už dřív“, ačkoli žádná taková věta "
            "neexistuje — a `XAIPresenter` by ho pak citoval jako "
            "potvrzený titul z textu. ŽÁDNÝ ZÁPIS NESMÍ NÉST TVRZENÍ "
            "O TEXTU, KTERÉ NENÍ DOLOŽENÉ KONKRÉTNÍ VĚTOU V SEZENÍ; "
            "u potvrzeného titulu je proto ta věta PŘÍMO V HLÁŠENÍ. "
            "Odmítnutý tah nabídku NESPOTŘEBUJE (B‑23). TŘI STAVY, TŘI "
            "HLÁŠKY: chybí nabídka („nikdo to netvrdil“) × už rozhodnuto "
            "(„leží to v bázi jako sXXXX“) — slít je znamená říct o textu "
            "něco, co neplatí (W‑56). A POTVRZENÍ SE NEPTÁ „ANO/NE“, "
            "PTÁ SE NA DRUH: POVOLÁNÍ se zapíše, ÚŘAD DRŽENÝ V ČASE NE, "
            "protože bezčasé `member` by platilo ŠÍŘ, než co věta říká — "
            "„prezident Masaryk“ držel úřad NĚJAKÉ OBDOBÍ. Čas by to "
            "spravil, jenže v korpusu žádný použitelný není: ze 39 zmínek "
            "visí čas na titulu u čtyř a všechny čtyři jsou ŽIVOTNÍ DATA "
            "v závorce, u úřadů je to NULA — není to úloha o čase "
            "v jádře, nemá se co zapsat. Z rozboru se povolání od úřadu "
            "rozeznat NEDÁ, takže to rozhoduje ČLOVĚK (W‑57)"
        ),
        anchor="core_semantics.cascade:title_claims",
        entry=".utter(",
        enforced_by=(
            "test_the_title_is_read_as_a_claim",
            "test_a_modifier_is_not_a_claim",
            "test_a_plural_family_is_not_a_claim",
            "test_a_claim_about_someone_outside_the_reading_is_not_taken",
            "test_the_sentence_is_written_and_the_claim_is_not",
            "test_the_claim_is_reported_not_swallowed",
            "test_the_gap_stops_claiming_nobody_said_it",
            "test_a_question_nobody_touched_still_says_nobody_said_it",
            "test_confirming_writes_the_claim_and_closes_the_offer",
            "test_the_breakdown_has_its_own_reason_for_this",
            "test_a_confirmation_without_any_sentence_is_refused",
            "test_a_confirmation_of_a_title_nobody_said_is_refused",
            "test_the_refusal_does_not_eat_the_offer",
            "test_every_written_title_cites_a_sentence_that_was_really_said",
            "test_a_second_confirmation_does_not_claim_nobody_said_it",
            "test_the_two_refusals_do_not_share_a_reason",
            "test_an_office_is_not_written_however_hard_you_click",
            "test_refusing_an_office_leaves_the_offer_open",
            "test_a_trade_is_written",
            "test_the_question_asks_which_kind_not_yes_or_no",
        ),
    ),
    Clause(
        id="O-14",
        boundary=CASCADE_SESSION,
        promise=(
            "TRPNÝ PODMĚT JE PATIENS a role `co` z něj plyne "
            "STRUKTURÁLNĚ, z podtypu `nsubj:pass`, ne z naučeného vzoru: "
            "`:pass` STOJÍ V ROZBORU a říká, že podmět té věty NENÍ "
            "konatel („Úmysly byly popsány.“ — úmysly nic nepopisují). "
            "Ptát se „co znamená role nsubj:pass“ znamenalo ptát se na "
            "něco, co rozbor právě řekl, a byla to TŘETÍ NEJČASTĚJŠÍ "
            "otázka korpusu (19 z 250). Vlastní jméno té role bylo "
            "ZAPSANÉ ROZHODNUTÍ (I‑2, INV‑11), ne vada — patro ten důvod "
            "neruší, dosazuje OPAČNOU stranu. KDYŽ JE `co` OBSAZENÉ, "
            "PATRO SE ZEPTÁ, NEPŘEPÍŠE: obě strany jsou vyslovené a "
            "zahodit jednu znamená zahodit člen, který ve větě stojí "
            "(změřeno: 1 věta z 19). Ta srážka MLČÍ K FALEŠNÉ OTÁZCE "
            "(`collided`, W‑20 — význam se ví) a ZASTAVUJE ZÁPIS "
            "(`AWAITING_ROLE_NAME`, B‑19 — jinak by se věta zapsala "
            "s povrchovým jménem a po rozhodnutí podruhé); ptá se "
            "VLASTNÍ otázkou, která se ptá KTERÁ ZE DVOU STRAN, ne co "
            "ten tvar znamená. KONATEL DOSTANE JMÉNO *(W‑80)*: HOLÝ "
            "`Ins:arg` pod TRPNÝM přísudkem je „kdo“ — „Kniha byla "
            "napsána Čapkem.“ dávala `Ins:arg:Čapek`, tedy TVAR místo "
            "jména. Poznávají to DVĚ ZNAČKY NARÁZ a ani jedna sama "
            "nestačí: instrumentál je taky NÁSTROJ („napsána perem“ je "
            "stejně trpná), takže rozhoduje `obl:arg` proti `obl` "
            "(valenční doplnění proti volné okolnosti) A NEPŘÍTOMNOST "
            "PŘEDLOŽKY („spojována **s** emancipačními snahami“ má "
            "obojí ostatní). Bez `Voice=Pass` se nepřejmenuje nic: holý "
            "`Ins:arg` je v korpusu 10× a ANI JEDNOU u trpného rodu "
            "(„stal se redaktorem“, „zabývá se zkoumáním“). TÁŽ ROLE, AŤ JE "
            "PODMĚT VYSLOVENÝ, NEBO NE *(W‑79)*: pro‑drop u trpného rodu "
            "vyrábí taky `co`, protože trpný podmět je PATIENS bez ohledu "
            "na to, jestli ho text zopakoval. Dvě jména pro touž roli "
            "rozpadala bázi na dvě poloviny, které se nepotkají — „Byl "
            "pohřben na Vyšehradě.“ + `→=` zapsalo `kdo:Karel_Čapek`, "
            "kdežto otázka se ptala na `co:Karel_Čapek` a mezera tvrdila "
            "„nikdo to neřekl“ o výroku, který v bázi ležel. Rozhoduje "
            "`Voice=Pass` na PŘÍSUDKU, ne deprel: `nsubj:pass` tu "
            "z definice není. Činný pro‑drop dál dává `kdo`"
        ),
        anchor="core_semantics.cascade:passive_tier",
        entry=".utter(",
        enforced_by=(
            "test_a_passive_subject_is_the_patient",
            "test_the_passive_role_comes_from_the_subtype_not_from_learning",
            "test_a_taken_object_makes_the_passive_ask",
            "test_a_collided_passive_does_not_write",
            "test_a_passive_without_a_subject_still_asks_for_one",
            "test_a_passive_sentence_goes_all_the_way_into_the_base",
            "test_a_passive_has_one_role_name_spoken_or_not",
            "test_an_active_prodrop_still_gets_a_subject",
            "test_the_agent_of_a_passive_gets_a_name",
            "test_an_instrument_under_a_passive_is_not_the_agent",
            "test_a_prepositional_instrumental_under_a_passive_is_not_the_agent",
            "test_an_active_instrumental_argument_is_not_the_agent",
        ),
    ),
    Clause(
        id="O-15",
        boundary=ORACLE_CASCADE,
        promise=(
            "SIGNÁL Z ROZBORU DĚLÍ TVAR, NEURČUJE JMÉNO ROLE *(W‑61)*. "
            "`v+Loc` byl NEJČASTĚJŠÍ tvar bez významu (42 z 250) a "
            "slepoval dvě různé věci — „v Praze“ je místo, „v roce 1935“ "
            "čas — takže jedno naučené mapování muselo být u jedné z nich "
            "špatně a nebylo poznat u které. Tvar se proto dělí podle "
            "toho, co o filleru říká ROZBOR: `NameType=Geo` a LETOPOČET "
            "jako dítě (`NumType=Card`, čtyři číslice). Ani jedno není "
            "seznam slov — obojí dává parser. ŽE „v Praze“ je `kde` a "
            "„do Prahy“ `kam`, PLYNE Z PŘEDLOŽKY A PÁDU, ne ze signálu; "
            "signál dělá jen to menší. SORT FILLERU POUŽÍT NELZE, a je "
            "to strukturální důvod: podle § 3.6 sort PLYNE Z ROLE, takže "
            "odvodit roli ze sortu je KRUH. SIGNÁLOVANÝ TVAR NEDĚDÍ "
            "OBECNÝ: seed má `po+Loc → kudy` a dokud byl tvar jeden, "
            "vycházelo z „Po roce 1990 byly nahrávky digitalizovány.“ "
            "`digitalizovaný(kudy:rok)`, tedy CESTA MÍSTO ČASU. Jen "
            "u PŘEDLOŽKOVÉ okolnosti — holý pád do měřené rodiny "
            "nepatří. A 26 ze 42 výskytů signál NEMÁ („v bytě“, "
            "„v tomto smyslu“, „v angličtině“); ty se dál PTAJÍ a je to "
            "SPRÁVNÁ ODPOVĚĎ, ne mez"
        ),
        anchor="core_semantics.cascade:role_signal",
        entry=".utter(",
        enforced_by=(
            "test_a_geographic_filler_splits_the_shape",
            "test_a_year_under_the_filler_splits_the_shape",
            "test_without_a_signal_the_shape_stays_bare",
            "test_place_and_time_no_longer_collide_under_one_shape",
            "test_the_signal_does_not_name_the_role",
            "test_the_question_says_where_the_signal_came_from",
            "test_a_year_does_not_inherit_the_bare_mapping",
            "test_the_split_shape_reaches_the_base",
            "test_a_year_is_part_of_the_mention_not_a_lost_member",
            "test_a_count_is_not_a_year",
            "test_the_year_is_recognised_in_one_place_only",
            "test_a_date_is_one_mention",
            "test_a_count_is_not_a_date_part",
            "test_a_quantity_word_is_not_a_date_part",
            "test_a_nested_date_is_one_mention_too",
            "test_a_plain_modifier_is_not_a_nested_date",
        ),
    ),
    Clause(
        id="O-16",
        boundary=ORACLE_CASCADE,
        promise=(
            "DVA ČLENY, JEDNO JMÉNO — ANI JEDEN HO NEDOSTANE *(W‑63)*. "
            "„Od 50. let byla ovšem interpretace zcela podřízena "
            "ideologii.“ dává `ovšem` (`advmod:emph`) i `zcela` "
            "(`advmod`) roli `jak`; čtení s duplicitou se nesmí vyrobit "
            "a NEZBYLO ANI JEDNO, ačkoli věta měla podmět, okolnost "
            "i argument. Vybrat jeden by byl TICHÝ DEFAULT u role, "
            "kterou věta vyslovila dvakrát — oba proto padnou zpátky na "
            "SVŮJ TVAR, systém se zeptá a NEZAPÍŠE (W‑62). Táž úvaha "
            "jako `collided` (W‑20), jen o patro dřív. KDYŽ TVARY "
            "NEROZLIŠÍ ANI TO (dvě holá `advmod`), věta se přečíst nedá "
            "— ale hlášení MUSÍ ŘÍCT PROČ: „nemá ani jeden člen, který "
            "bych uměl pojmenovat“ je NEPRAVDA O TEXTU, protože členy má "
            "a umí je pojmenovat. A POHLCENÝ PŘÍVLASTEK NENÍ "
            "NEPOJMENOVANÝ ČLEN: „Úrazy způsobené pády.“ je JMENNÁ "
            "FRÁZE, ne věta. A NADPIS SPLYNULÝ S VĚTOU se pojmenuje: "
            "„Obezita: Domácí mazlíčci trpí nadváhou.“ má kořenem NADPIS "
            "a skutečná věta pod ním visí jako `appos` se svým podmětem "
            "i přísudkem — členy tam JSOU, jen ne pod tím kořenem. Číst "
            "se to nezačne a je to ROZHODNUTÍ: přesadit kořen by "
            "znamenalo rozhodnout, že nadpis do promluvy nepatří, a to "
            "je výrok o TEXTU, ne o rozboru; rozdělit dvojí text je práce "
            "SEGMENTACE. Jmenná apozice bez přísudku sem NEPATŘÍ — "
            "rozlišuje to rozbor, ne dvojtečka (W‑64). NA OTÁZKU „JE "
            "TOHLE PŘÍSUDEK?“ ODPOVÍDÁ JEDNO MÍSTO: stráž se ptá "
            "`_is_predicate`, nepíše si vlastní užší kopii. Ta kopie "
            "nesla obě staré rodiny naráz — `upos == „VERB“` minulo "
            "TRPNÝ ROD (W‑48) a `deprel == „cop“` porovnávalo deprel "
            "řetězcem (W‑47) — takže „Obezita: Zvířata byla vyšetřena "
            "veterinářem.“ hlásila zase, že nemá ani jeden pojmenovatelný "
            "člen. Dvě kopie stráže se rozejdou a nikdo nepozná, která "
            "platí (W‑65)"
        ),
        anchor="core_semantics.cascade:why_nothing",
        entry="generate(",
        enforced_by=(
            "test_two_members_with_one_name_both_fall_back_to_their_shape",
            "test_the_fallback_asks_and_does_not_write",
            "test_an_unresolvable_collision_says_so_instead_of_lying",
            "test_a_nominal_phrase_is_not_a_predicate_without_members",
            "test_a_heading_glued_to_a_sentence_is_named_as_such",
            "test_a_nominal_apposition_is_not_a_heading",
            "test_the_heading_guard_asks_the_one_place_that_knows",
            "test_the_heading_guard_has_no_second_copy",
        ),
    ),
    Clause(
        id="G-9",
        boundary=CASCADE_SESSION,
        promise=(
            "ZVRATNÉ ZÁJMENO NEODKAZUJE VEN Z VĚTY *(W‑68)*. „V prosinci "
            "1938 **si** Karel Čapek přivodil chřipku.“ — `si` míří na "
            "podmět TÉŽE věty. Systém se přesto ptal „Na koho odkazuje? "
            "Řekni to prosím jménem“ a pak tu odpověď NEMĚL KAM PŘIJMOUT: "
            "role čeká na KVANTIFIKÁTOR, takže `→=` vrátí „role na odkaz "
            "nečeká, není co rozhodovat“. OTÁZKA, NA KTEROU NEEXISTUJE "
            "TAH, JE HORŠÍ NEŽ MLČENÍ — a když je dialog jediný kanál "
            "významu, je to slepý konec jediné cesty vpřed. Táž úvaha "
            "jako u prezentačního „to“ (W‑29), jen tady DOLOŽENÁ tím, že "
            "tah odpověď odmítá. Rozhoduje RYS Z ROZBORU (`Reflex=Yes`), "
            "ne výčet tvarů — ten by byl druhý slovník vedle parserova. "
            "Kvantifikátorovou otázku klade dál kaskáda a ta tah MÁ; "
            "obyčejné zájmeno se dál ptá"
        ),
        anchor="core_semantics.grounding:_reflexive",
        entry="ground(",
        enforced_by=(
            "test_a_reflexive_is_not_asked_about_as_an_anaphor",
            "test_a_plain_pronoun_is_still_asked_about",
            "test_the_reflexive_sentence_asks_only_what_it_can_answer",
        ),
    ),
    Clause(
        id="O-19",
        boundary=ORACLE_CASCADE,
        promise=(
            "NA OTÁZKU „JE TOHLE SPONA?“ ODPOVÍDÁ JEDNO MÍSTO *(W‑66)*. "
            "Čtyři místa kaskády se ptala PŘESNÝM ŘETĚZCEM "
            "(`deprel == \"cop\"`) — hledání přísudku, záměna `kdo`/`co`, "
            "tvar úplnosti a stráž srážky. UD u spony podtypy připouští "
            "a porovnání na shodu je na nich slepé: `cop:expl` propadne "
            "a věta přijde o PŘÍSUDEK, tedy o to, čím vůbec je. "
            "OPRAVUJE SE RIZIKO, NE DNEŠNÍ CHOVÁNÍ, a je to řečeno "
            "nahlas: v korpusu je 61 spon a NULA podtypů (změřeno v #103 "
            "i dnes), takže projev je 0 a doloží to jen zkouška. Důvod "
            "je jinde — táž rodina (kategorie s variantami, porovnávaná "
            "výčtem nebo shodou) padla od W‑32 jedenáctkrát a pokaždé "
            "stálo kolo ji najít; tohle jsou POSLEDNÍ ČTYŘI MÍSTA, "
            "o kterých se ví dopředu. PODTYP SE NEZAHAZUJE (N‑1): ptá se "
            "„je to KANDIDÁT na sponu“, ne co ta spona znamená. `aux` "
            "spona není a základ se bere celý, ne jako předpona"
        ),
        anchor="core_semantics.cascade:is_copula",
        entry="generate(",
        enforced_by=(
            "test_a_subtyped_copula_is_still_a_copula",
            "test_something_that_is_not_a_copula_is_not_mistaken_for_one",
            "test_a_subtyped_copula_reads_the_same_sentence",
        ),
    ),
    Clause(
        id="G-10",
        boundary=CASCADE_SESSION,
        promise=(
            "KVANTIFIKÁTOROVÉ ZÁJMENO KVANTIFIKUJE, NEODKAZUJE *(W‑81)*. "
            "„Podle definice je vesmír **vše**, co se nachází "
            "v prostoru.“ dostávala „Na koho odkazuje „vše“? Tohle "
            "zájmeno neumím navázat — ODKAZUJE MIMO TEXT, ne do něj.“ — "
            "a ta věta o tom zájmenu TVRDÍ NEPRAVDU: „vše“ neodkazuje "
            "ven ani dovnitř. Vzniklo to ZBYTKOVOU VĚTVÍ: co nebylo "
            "v `ANAPHORIC_LEMMAS`, dostalo jedno vysvětlení pro všechno "
            "ostatní — jedenáctá instance téže rodiny (W‑32 … W‑80). "
            "Rozhoduje `PronType` z ROZBORU, ne výčet slov: `Tot` je "
            "totalita (`∀`), `Ind` existence (`∃`), a KVANTIFIKÁTOR SI "
            "NESE SAMO SLOVO, takže se na něj nikdo neptá — táž úvaha "
            "jako u vlastního jména (W‑78), kde odpověď taky stojí "
            "v textu. ZÁPOR JE POJMENOVANÁ MEZ, NE TŘETÍ KVANTIFIKÁTOR: "
            "`Neg` („nikdo“, „nic“) kvantifikátor NEDOSTANE, protože "
            "popření existence nese jádro na PREDIKACI (silná negace), "
            "a „platí o žádném“ není výrok, který by šel ověřit — lhát "
            "se o něm ale nesmí stejně, proto se zbytkové větvi vyhýbá "
            "taky. Zájmeno s `PronType=Prs` ODKAZUJE a ptá se dál"
        ),
        anchor="core_semantics.cascade:quantifying_pronoun",
        entry="ground(",
        enforced_by=(
            "test_a_quantifying_pronoun_is_not_told_it_refers_outside_the_text",
            "test_a_negative_pronoun_is_not_told_it_refers_either",
            "test_a_referring_pronoun_is_still_asked_about",
            "test_a_total_pronoun_carries_its_own_quantifier",
            "test_an_indefinite_pronoun_is_existential",
            "test_a_negative_pronoun_gets_no_quantifier",
        ),
    ),
    Clause(
        id="O-17",
        boundary=ORACLE_CASCADE,
        promise=(
            "SOUŘADNÝ DRUHÝ PŘÍSUDEK JE DRUHÁ VĚTA, ne ztracený člen "
            "*(W‑70)*. „Jeho stav se přechodně zlepšil, ALE BRZY MUSEL "
            "ZNOVU ULEHNOUT.“ — ta druhá část není člen první věty; "
            "hlásit ji jako ztrátu je nepravda o tom, co ta část textu "
            "je, a ptát se „jak se ta role jmenuje“ je výzva, aby člověk "
            "dosadil druhou větu jako člen první. Čte se ze STAVBY, ne "
            "ze spojky: `conj` pod kořenem, který je sám PŘÍSUDEK — ptá "
            "se `_is_predicate`, takže platí i pro trpný rod a nepíše se "
            "druhá kopie té otázky (W‑65). SOUŘADNÉ JMÉNO („psi a "
            "kočky“) tudy NEPROJDE a projít nesmí — to člen věty je. "
            "Vyjímá se CELÝ PODSTROM: členy druhé věty jsou její. ČÍST "
            "SE TO ZATÍM NEZAČNE a je to PŘIZNANÁ MEZ, ne rozhodnutí "
            "o textu — udělat z druhé věty ROLI by byla táž vada jako "
            "u titulu a u apozice. Změřeno: 35 vět z 238 (15 %), z toho "
            "18 SDÍLÍ PODMĚT a 17 má VLASTNÍ, tedy dvě různé úlohy "
            "skoro stejné velikosti. DRUHÁ VĚTA SE SDÍLENÝM PODMĚTEM SE "
            "OD W‑71 ČTE A ZAPISUJE ZVLÁŠŤ: podmět NEVYSLOVILA a "
            "nemusela — řekla ho první — takže se BERE Z TÉŽE PROMLUVY "
            "a v hlášení je řečeno, ODKUD. Kopíruje se táž zmínka, "
            "nezakládá se druhá: dva uzly pro jednoho člověka jsou "
            "nejdražší chyba, jakou tenhle systém umí (M‑2). Jsou to DVĚ "
            "PREDIKACE a platí OBĚ — slít je do jedné formule by "
            "tvrdilo, že „zlepšil se“ a „musel ulehnout“ je jeden děj. "
            "Zábrany platí na obě stejně (B‑19) a hlásí se JEN ta druhá "
            "věta, kterou číst NEUMÍME — jinak by systém o jedné věci "
            "řekl dvě věci, které si odporují (W‑20). PODMÍNKA JE „NENÍ "
            "PŘEČTENÁ“, NE „MÁ VLASTNÍ PODMĚT“: zúžení na vlastní podmět "
            "propustilo třetí případ — větu, u které druhá predikace "
            "nevznikla, protože první čtení je JÁDROVÁ RELACE a `kdo` "
            "v ní není. Ta věta se ZAPISUJE, takže mlčení o její druhé "
            "půlce je TICHÝ ČÁSTEČNÝ ZÁPIS (I‑1); u nezapsané věty by to "
            "byla kosmetika (B‑24). A patro souřadnosti běží AŽ ZA "
            "KVANTIFIKÁTOREM: půjčuje se HOTOVÁ role, protože role bez "
            "kvantifikátoru se do jádra nedostane a druhý zápis by nikdy "
            "nevznikl (W‑72). DRUHÁ VĚTA S VLASTNÍM PODMĚTEM si nic "
            "nepůjčuje — text řekl podruhé, o kom je — a UZEL VZNIKÁ "
            "Z NĚJ. V hlášení to MUSÍ být vidět: u sdíleného podmětu se "
            "přenáší TÁŽ zmínka, tady vzniká DRUHÁ, a to je místo, kde "
            "se dva uzly pro jednoho člověka vyrábějí nejsnáz (M‑2). "
            "Porovnává se TOTOŽNOST ROLE, ne jméno — kopie a nový uzel "
            "se stejným lemmatem by se jménem nerozlišily. Role, které "
            "patro vyrobí, dostanou KVANTIFIKÁTOR: kvantifikátorové "
            "patro už proběhlo, a NESMÍ POSTAVIT PREDIKACI S DUPLICITNÍ "
            "ROLÍ: dva `advmod` uvnitř druhé věty chtějí oba `jak`, "
            "`Predication` to odmítá, takže oba padnou na SVŮJ TVAR "
            "a když je nerozliší ani ten, druhá věta se nepřečte a jen "
            "ohlásí — táž úvaha jako W‑63, jen o patro dál (W‑73)"
        ),
        anchor="core_semantics.cascade:second_predications",
        entry="cascade(",
        enforced_by=(
            "test_a_coordinated_predicate_is_a_second_sentence",
            "test_a_coordinated_noun_is_still_a_member",
            "test_the_second_sentence_is_not_reported_as_a_lost_member",
            "test_the_second_sentence_is_named_in_the_trace",
            "test_the_second_sentence_borrows_the_subject_from_the_first",
            "test_a_second_sentence_with_its_own_subject_keeps_it",
            "test_a_written_sentence_always_names_its_unread_half",
            "test_one_utterance_can_write_two_statements",
            "test_a_spoken_second_subject_makes_its_own_node",
            "test_a_second_sentence_with_two_same_named_members_does_not_crash",
        ),
    ),
    Clause(
        id="O-18",
        boundary=CASCADE_SESSION,
        promise=(
            "VLASTNÍ JMÉNO JE KONKRÉTNÍ, AŤ STOJÍ KDEKOLI *(W‑78)*. Že "
            "`PROPN` je signál individua, je rozhodnuté od N‑2d — jenže "
            "to byl NAUČENÝ VZOR vázaný na (upos, číslo, pád, deprel), "
            "takže „Karel Čapek“ dostal `·` jako `nsubj`, ale jako "
            "`nsubj:pass` nebo `Ins:arg` se na něj systém ptal znovu. "
            "DESÁTÁ INSTANCE TÉŽE RODINY (W‑32 … W‑65): kategorie, která "
            "má varianty, porovnávaná výčtem. DŮSLEDEK BYL NA STRANĚ "
            "ODPOVÍDÁNÍ, ne čtení — „Byl Karel Čapek pohřben na "
            "Vyšehradě?“ nedostalo odpověď, ačkoli ten fakt v bázi ležel, "
            "a otázka, na kterou báze odpověď MÁ a nedá ji, je horší než "
            "chybějící zápis. Je to VLASTNOST JMÉNA, ne role: doplnit "
            "`nsubj:pass` do seznamu deprelů by tutéž otázku vrátilo "
            "u jedenáctého tvaru. OBECNÉ JMÉNO se dál ptá"
        ),
        anchor="core_semantics.cascade:quantifier_tier",
        entry="cascade(",
        enforced_by=(
            "test_a_proper_name_is_concrete_in_any_role",
            "test_a_common_noun_is_still_asked_about",
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
        id="O-24",
        boundary=ORACLE_CASCADE,
        promise=(
            "ÚČET: ŽÁDNÉ SLOVO PŘEČTENÉ VĚTY NEZMIZÍ BEZE STOPY "
            "*(B‑28)*. Materiál mizel mlčky na TŘECH místech "
            "(složený přívlastek pod ztracenou hlavou, přivlastnění, "
            "přívlastek pod genitivním přívlastkem) a pokaždé se to "
            "opravovalo tam, kde se to zrovna našlo — čtvrtá záplata "
            "by byla pátá. JEDNO MÍSTO to proto sečte: co není ani ve "
            "čtení, ani pohlcené, ani v přísudku, ani mezi čekajícími "
            "vztahy, ani mezi VYPSANÝMI ztracenými členy, se JMENUJE. "
            "NENÍ TO OTÁZKA — na „jakou roli hraje `jejich`“ pravdivá "
            "odpověď neexistuje (W‑75); účet jen říká, že to systém "
            "VIDĚL. ÚČET ČTE TÝŽ SEZNAM, KTERÝ SE VYPISUJE: postavený "
            "na `dropped_tokens` prohlásil 233 slov za zaznamenaná, "
            "ačkoli je nikdo nevypsal — hlášení z toho seznamu ještě "
            "odečítá genitivní přívlastek a druhou větu. ZMĚŘENO: "
            "němých slov v přečtených větách 471 → 28 (kritériem "
            "reviewera, tedy VŠE KROMĚ ZNAČEK; první verze účtu jich "
            "minula 30, protože vyjmenovávala materiál místo aby se "
            "ptala na doplněk — „aloe vera“ je `X`, „μ“ je `SYM`). "
            "DOLOŽKA NEDRŽÍ CELEK A DRŽÍ TYHLE DVĚ RODINY: 26 slov "
            "v podstromu DRUHÉ VĚTY, kterou hlášení hlásí jako celek "
            "(„číst ji zatím neumím“) — rozepsat je znamená tvrdit, že "
            "jsou členy TÉHLE věty (W‑70) — a 2 slova uvnitř fráze, "
            "která je sama hlášena jen zčásti. Slovo, které ve čtení "
            "JE, se do účtu nedostane: dvojí hlášení 0 z 220 vět"
        ),
        anchor="core_semantics.cascade:unaccounted_tokens",
        entry="cascade(",
        enforced_by=(
            "test_a_word_with_no_role_is_named_not_silenced",
            "test_a_word_that_is_in_the_reading_is_not_reported_twice",
            "test_the_ledger_and_the_report_read_the_same_list",
        ),
    ),
    Clause(
        id="O-23",
        boundary=ORACLE_CASCADE,
        promise=(
            "MATERIÁL Z VĚTY SE NESMÍ ZTRATIT MLČKY *(B‑28)*, ani když "
            "se ho patro vědomě vzdá. DVĚ MÍSTA, JEDNA PŘÍČINA. "
            "(1) PŘIVLASTNĚNÍ: „Filipovo auto stojí venku.“ se čte jako "
            "věta o NĚJAKÉM autě a slovo „Filipovo“ se v celém přepisu "
            "neobjevilo ANI JEDNOU — role sice čeká na odkaz a systém se "
            "ptá „O kterém „auto“ mluvíš?“, ale NEŘÍKÁ, CO TU REFERENCI "
            "ZUŽUJE. Přivlastnění je proto vidět ve TVARU zmínky "
            "(„Filipovo auto“), ne v lemmatu: uzel `Filipův_auto` "
            "vzniknout nesmí (z každého majitele by byla nová třída, "
            "N‑2c), a právě proto jsou `form` a `lemma` dvě pole. "
            "(2) SLOŽENÝ PŘÍVLASTEK POD ZTRACENOU HLAVOU: od W‑78 se "
            "skládá i tam, jenže když je ztracená i ta hlava, nikde se "
            "to jméno neobjevilo a o 277 slovech korpusu přestalo "
            "hlášení mluvit ÚPLNĚ. Ztracený člen se proto hlásí I S TÍM, "
            "CO SE DO NĚJ SLOŽILO („domácími zvířaty“, ne „zvířaty“). "
            "UBRAT OTÁZKU JE POKROK JEN TEHDY, KDYŽ SE TEN MATERIÁL "
            "OHLÁSÍ JINDE — jinak je to tichá ztráta kusu věty (I‑1), "
            "táž třída jako B‑25, jen o patro níž. Holé jméno bez "
            "přivlastnění takový záznam NEMÁ a na odkaz nečeká. "
            "ROZSAH: tahle doložka drží TY DVĚ RODINY, ne celek — "
            "celek hlídá O‑24 (účet). Doložka, která slibuje víc než "
            "kód, je horší než žádná, protože se o ni příští kolo opře"
        ),
        anchor="core_semantics.cascade:_nominal",
        entry="cascade(",
        enforced_by=(
            "test_a_possessive_is_visible_in_the_mention",
            "test_a_bare_noun_carries_no_possessive",
            "test_a_lost_head_is_reported_with_what_was_composed_into_it",
        ),
    ),
    Clause(
        id="O-22",
        boundary=ORACLE_CASCADE,
        promise=(
            "PŘÍVLASTEK SE SKLÁDÁ DO JMÉNA I POD ZTRACENOU HLAVOU "
            "*(W‑78)*. „…s **domácími** zvířaty“ — `domácími` není člen "
            "věty, je to část jména třídy; ptát se na jeho ROLI znamená "
            "vyzvat člověka, ať z něj udělá účastníka děje, kterým "
            "není. Je to TÁŽ schopnost, jakou `attributes_of` dělá pro "
            "frázi přímo pod rolí (182 z 542 v korpusu), jen O PATRO "
            "NÍŽ — a proto se drží i obě její vyloučení: hlava musí být "
            "`NOUN` a přivlastnění (`Poss=Yes`) se neskládá, protože "
            "„Filipovo auto“ je vztah ke KONKRÉTNÍMU uzlu, ne druh "
            "auta. SKLÁDÁNÍ NETVRDÍ NIC, a to je celý důvod, proč se "
            "smí dělat mlčky: rozbor „terapeutický pes“ a „bývalý "
            "prezident“ NEROZLIŠÍ (znak za znakem táž morfologie), "
            "takže čtení, které by o vztahu k holému jménu něco "
            "tvrdilo, by u jedné z nich LHALO — `subset(složená ⊆ "
            "holá)` proto zůstává `U` OBĚMA směry. „Je to pes“ se "
            "zapisuje vlastním tahem `→⊆`. PŘÍVLASTEK PSANÝ VELKÝM "
            "PÍSMENEM je ČÁST JMÉNA („Malé Svatoňovice“, „Severní "
            "Amerika“), ne přívlastek („anglická Wikipedie“) — dělí to "
            "velikost písmene, shoda v pádě/čísle/rodě a to, že díl "
            "NESTOJÍ NA ZAČÁTKU VĚTY. Sentence‑initial je POJMENOVANÁ "
            "MEZ: tam velké písmeno neznamená nic („Krásná Praha“ má "
            "týž rozbor), takže se neskládá a ten člen se HLÁSÍ. Díly "
            "jména se řadí podle POZICE V TEXTU, ne podle toho, kdo je "
            "hlava"
        ),
        anchor="core_semantics.cascade:dropped_tokens",
        entry="cascade(",
        enforced_by=(
            "test_an_attribute_under_a_lost_head_is_not_asked_about",
            "test_a_composed_class_name_claims_no_subset",
            "test_a_capitalised_adjective_is_part_of_the_name",
            "test_a_lowercase_adjective_under_a_name_is_not_part_of_it",
            "test_a_sentence_initial_adjective_is_a_named_limit",
        ),
    ),
    Clause(
        id="O-21",
        boundary=ORACLE_CASCADE,
        promise=(
            "UZEL, JEHOŽ JMÉNO JE VLASTNÍM PREFIXEM JMÉNA V TEXTU, SE "
            "NEZAPÍŠE MLČKY *(W‑75)*. „Bydlí v Rožnově **pod "
            "Radhoštěm**.“ dá `·Rožnov` — vlastní jméno, které v textu "
            "takhle NESTOJÍ; je to táž třída jako W‑72, jen z druhé "
            "strany. SLOŽIT TO NEJDE: druhý díl má PŘEDLOŽKU, takže se "
            "od genitivního dílu („Hradec Králové“) liší a spojit ho "
            "znamená koupit si jméno domněnkou. MLČET SE ALE TAKY "
            "NESMÍ, a zvlášť ne mlčet ŠPATNOU OTÁZKOU: dosud se systém "
            "ptal „jakou roli hraje „Radhoštěm““ — výzva, ať člověk "
            "k větě přilepí ÚČASTNÍKA, KTERÝ V NÍ NENÍ, tedy táž rodina "
            "jako W‑73 („vypadá to jako odpověď a není“). Díl jména se "
            "proto jako ztracený člen NEHLÁSÍ, hlásí se JMÉNO NEÚPLNÉ "
            "i s tím, co by uzel nesl, a zápis to BLOKUJE — uzel se "
            "zkráceným jménem je tvrzení o textu, ne mez. Co se "
            "složilo (holý genitiv, O‑20), neúplné NENÍ. ZNAČKA TO "
            "NESE TAKY *(W‑76)*: `✓` slibuje, že CELÁ VĚTA je ve čtení, "
            "a díl jména v něm není — „Rožnov pod Radhoštěm je město.“ "
            "má proto `◐`, i když ji od zápisu drží tenhle guard jako "
            "jediný. Že se to do báze nedostane, je JINÁ otázka než co "
            "ta značka o ČTENÍ tvrdí"
        ),
        anchor="core_semantics.cascade:partial_name_tier",
        entry="cascade(",
        enforced_by=(
            "test_a_name_the_node_carries_only_partly_is_said_out_loud",
            "test_a_composed_name_is_not_reported_as_partial",
            "test_a_part_of_a_name_is_not_asked_about_as_a_role",
            "test_an_incomplete_name_keeps_the_partial_mark",
        ),
    ),
    Clause(
        id="O-20",
        boundary=ORACLE_CASCADE,
        promise=(
            "UZEL SE NEJMENUJE ZKRÁCENĚ *(W‑72)*. „Bydlí v **Hradci "
            "Králové**.“ dávalo uzel `·Hradec` — VLASTNÍ JMÉNO, KTERÉ "
            "V TEXTU TAKHLE NESTOJÍ. Je to zrcadlo W‑73: tam měla role "
            "víc členů, tady má jméno víc slov. UD ten díl váže `nmod`, "
            "ne `flat`, protože se NESHODUJE V PÁDĚ (`Hradci` je `Loc`, "
            "`Králové` `Gen`) — a proto ho `NAME_CONTINUATION` míjelo. "
            "ROZLIŠUJE TO STAVBA, NE SEZNAM MĚST: hlava i díl jsou "
            "`PROPN` a genitiv je HOLÝ. Ptát se nemusí, a je to "
            "ZMĚŘENO, ne předpokládáno: „Čapka Josefa“ i „Ludvíku "
            "Rittersberka“ váže rozbor `flat`, tedy tou větví, která je "
            "skládá správně od B‑21 — nejsou to tři případy téže věci, "
            "jak se zdálo z celého stromu, ale dva různé tvary. "
            "PŘEDLOŽKOVÉ JMÉNO („Rožnov **pod** Radhoštěm“) JE "
            "POJMENOVANÁ MEZ: holý genitiv to není, takže se neskládá "
            "a hlásí se dál. Co se do jména složilo, PŘÍVLASTEK UŽ "
            "NENÍ — jinak by vedle věty stál druhý výrok o části "
            "toho jména. V korpusu je projev 0 (43 `flat` se skládá "
            "správně a `nmod` pod zmínkou role tam není ani jednou), "
            "takže tohle drží JEN zkouška"
        ),
        anchor="core_semantics.cascade:name_parts_of",
        entry="cascade(",
        enforced_by=(
            "test_a_name_in_the_genitive_is_part_of_the_name",
            "test_a_prepositional_second_part_is_not_composed",
            "test_a_flat_second_part_still_composes",
            "test_a_composed_name_part_is_not_reported_as_an_attribute",
        ),
    ),
    Clause(
        id="S-43",
        boundary=SESSION_STORAGE,
        promise=(
            "ODVOLAT VĚTU JDE CELOU — JEDNOTKOU ODVOLÁNÍ JE PROMLUVA "
            "*(B‑26)*. Jedna věta umí zapsat VÍC výroků: „Petr a Jana "
            "přišli.“ po `→&` uloží dvě tvrzení o dvou uzlech, „Petr "
            "přišel a odešel.“ (T94) taky. `revoke` po jednom id strhlo "
            "jen půlku a báze druhou polovinu tvrdila DÁL — po odvolání "
            "věty odpovídalo „přišla Jana?“ pořád `A`. Není to vada "
            "zápisu (báze byla správně), je to vada ODVOLATELNOSTI, a "
            "u systému, který stojí na „všechno jde vzít zpět“, je to "
            "táž úroveň jako správnost zápisu — je to přesně ta vada, "
            "kterou B‑19 pojmenovala z druhé strany („uložilo by DVA "
            "výroky a ten první by nikdo neodvolal“). ROZHODNUTO PRO "
            "PROMLUVU, ne pro výrok, protože JEDNOTKOU ZÁPISU JE "
            "PROMLUVA TAKY: výroky z jedné věty jsou SOUROZENCI, ani "
            "jeden z druhého neplyne, takže je `derived_from` nespojí a "
            "ohnout ho by znamenalo tvrdit odvození, které není. "
            "Rukojeť je VLASTNÍ POLE, ne text čtený z provenience: "
            "provenience je poznámka pro člověka, rukojeť je hodnota, "
            "kterou kód porovnává. Odvozené výroky ji DĚDÍ. VÝROK "
            "Z JINÉ PROMLUVY SE NESTRHNE, ani když sdílí uzel — uzel "
            "není důvod k odvolání. A tah, který zapsal víc výroků, je "
            "VŠECHNY ohlásí; bere se to z báze, ne se sbírá po cestě"
        ),
        anchor="core_semantics.storage:KnowledgeBase.revoke_utterance",
        entry=".play(",
        enforced_by=(
            "test_a_turn_reports_every_statement_it_wrote",
            "test_revoking_an_utterance_takes_back_both_halves",
            "test_revoking_an_utterance_spares_another_that_shares_a_node",
        ),
    ),
    Clause(
        id="S-42",
        boundary=SESSION_STORAGE,
        promise=(
            "VÍC ČLENŮ V JEDNÉ ROLI SE NEROZDĚLÍ MLČKY *(W‑73)*. „Petr "
            "a **Jana** přišli.“ — obě jména jsou `kdo`, ne `kdo` a něco "
            "jiného; pojmenovat druhý konjunkt jinou rolí je ÚČINNOST "
            "KOUPENÁ NEPRAVDIVÝM JMÉNEM (změřeno: u 50 z 65 přímých "
            "souřadných členů je pravdivé jméno role obsazené). Je to "
            "tedy DRUHÝ UZEL TÉŽE ROLE. JENŽE JESTLI TO PLATÍ O KAŽDÉM "
            "ZVLÁŠŤ, TO ROZBOR NENESE: „Petr a Jana přišli.“ ano, „Petr "
            "a Jana zvedli klavír.“ ne — a obě věty mají stavbu "
            "IDENTICKOU (`nsubj` + `cc` + `conj`, přísudek v plurálu). "
            "Rozdíl je ve SLOVESE, ne ve stavbě. Rozdělit mlčky vyrobí "
            "tvrzení, které ve větě není; nerozdělit mlčky taky, jen "
            "opačné. Systém se proto PTÁ a zápis to BLOKUJE jako "
            "`pending_relation` (B‑17). Odpověď `→&` je ROZHODNUTÍ, ne "
            "naučený tvar — „zvedli“ a „přišli“ mají týž tvar a opačnou "
            "odpověď, takže naučit ji jako tvar znamená přečíst druhou "
            "větu naruby (táž úvaha jako u genitivního přívlastku, "
            "W‑39). „Každý zvlášť“ dá DRUHÉ TVRZENÍ se sdíleným "
            "přísudkem (jádro drží jeden term na roli a to se nemění); "
            "„dohromady“ dá JEDEN uzel a žádnou skupinu neuzavírá. Věta "
            "s jedním členem v roli se na sdílení neptá"
        ),
        anchor="core_semantics.cascade:sharing_tier",
        entry=".play(",
        enforced_by=(
            "test_two_names_in_one_role_are_not_split_silently",
            "test_the_distributive_answer_writes_two_statements",
            "test_the_collective_answer_writes_one_node",
            "test_a_single_filler_asks_nothing_about_sharing",
        ),
    ),
    Clause(
        id="S-41",
        boundary=SESSION_STORAGE,
        promise=(
            "PO ODPOVĚDI NESMÍ ZMLKNOUT ZÁVISLÝ ČLEN TOHO, CO BYLO PRÁVĚ "
            "POJMENOVÁNO *(W‑71)*. Patro genitivního přívlastku běželo "
            "PŘED patrem ztracené role, takže role, která teprve vznikla "
            "z odpovědi člověka, svůj přívlastek nikdy nedostala: "
            "„zánět ledvin a **zápal plic**“ ohlásilo „zánět ledvina“ a "
            "o „plic“ ani slovo. Je to táž vada jako B‑25, jen o patro "
            "níž — mlčet o členu, který ve větě stojí, je stejné jako "
            "ohlásit ho špatně. Pořadí je věcné a je to týž důvod, proč "
            "`subordinate_tier` běží dřív, než se počítají ztracené "
            "členy: CO PŘIDÁVÁ ROLI, MUSÍ PŘEDCHÁZET TOMU, CO ROLE "
            "ZPRACOVÁVÁ. Změřeno stejnou sondou před i po: vět, kde po "
            "odpovědi zůstal někdo venku a systém o něm MLČÍ, bylo 5 "
            "(„Králové“, „plic“, „bratra“, „senátu“, „světla“) a je 0. "
            "Přívlastek členu, který ve čtení JEŠTĚ NENÍ, se dál "
            "nehlásí — visel by na něčem, o čem věta nemluví"
        ),
        anchor="core_semantics.session:Session.tiers",
        entry=".play(",
        enforced_by=(
            "test_a_member_named_by_an_answer_gets_its_own_attribute",
            "test_an_attribute_of_a_member_outside_the_reading_is_not_claimed",
        ),
    ),
    Clause(
        id="S-40",
        boundary=SESSION_STORAGE,
        promise=(
            "CO O VĚTĚ PLATÍ, SE NEČTE Z TAHU, KTERÝ NA NI ODPOVÍDÁ "
            "*(B‑25)*. Ztracené členy a stopa se braly z `turn`, jenže "
            "tah ODPOVĚDI je vlastní tah a obojí má PRÁZDNÉ — takže "
            "odpověď na JEDNU otázku zrušila ostatní a věta se prohlásila "
            "za přečtenou. „Státy, města a obce…“ se ptala na 15 členů; "
            "po odpovědi na JEDEN stálo `✓ přečteno` s TOUŽ formulí a "
            "otázka ŽÁDNÁ — čtrnáct členů zůstalo venku a systém o nich "
            "mlčel. ZNAČKA VZNIKALA Z NEPŘÍTOMNOSTI DŮKAZU: `has_dropped` "
            "se ptala stopy, která na tahové cestě nebyla. Do báze přitom "
            "nešlo nic — nepravdivé bylo HLÁŠENÍ O VLASTNÍM STAVU, a to "
            "je na jediném kanálu, kterým do systému vstupuje význam, "
            "dost. Tah, který větu čte ZNOVU, proto dodá nový verdikt; "
            "tah, který ji jen DOPLŇUJE (kvantifikátor, odkaz), zdědí "
            "poslední známý stav, protože rozborem se ztracený člen "
            "ztraceným být nepřestal. `✓` jen tehdy, když venku nezůstal "
            "NIKDO; `[ZAHOZENO: …]` přežije tah; hlášení „ČTENÍ SE "
            "NEZMĚNILO“ (S‑39) tím pádem nemůže stát u věty, které se "
            "značka změnila — obojí plyne z TÉHOŽ verdiktu. Věta, ze "
            "které venku nezůstal nikdo, značku `✓` dostane dál"
        ),
        anchor="core_semantics.session:Session._settle",
        entry=".play(",
        enforced_by=(
            "test_answering_one_question_does_not_cancel_the_others",
            "test_a_sentence_with_a_member_left_out_is_not_marked_read",
            "test_the_dropped_note_survives_the_turn",
            "test_a_finished_sentence_still_gets_the_read_mark",
        ),
    ),
    Clause(
        id="S-39",
        boundary=SESSION_STORAGE,
        promise=(
            "ŽÁDNÝ TAH NEPOTVRDÍ, ŽE SE NĚCO NAUČILO, ANIŽ ŘEKNE, CO SE "
            "TÍM VE VĚTĚ ZMĚNILO *(N‑1)*. „Ke chřipce se přidal zánět "
            "ledvin a **zápal** plic.“ — systém se na `zápal` ptá, člověk "
            "odpoví „podmět“, tah ohlásí „✓ naučeno role nsubj>conj+Nom ~ "
            "kdo“ a ČTENÍ ZŮSTANE `přidat(k+Dat:chřipka, kdo:∀zánět)`. "
            "Odpověď se přijala a neudělala NIC. Je to horší než otázka "
            "bez tahu: u chybějícího tahu člověk ví, že stojí — tady si "
            "myslí, že postoupil, a je to nepravda o VLASTNÍM STAVU na "
            "jediném kanálu, kterým do systému vstupuje význam. TAH SE "
            "NEODMÍTÁ, a to je to rozhodnutí: mapování je naučené správně "
            "pro CELOU TŘÍDU tvarů a v každé větě, kde je ta role volná, "
            "zabere — odmítnout ho kvůli jedné větě znamená zahodit "
            "platné zobecnění, což `→∈` bez nabídky (B‑23) nedělá, "
            "protože tam se učit nemá co. PŘÍČINA JE JEDINÁ A ZMĚŘENÁ: "
            "SRÁŽKA. Ze 1388 ztracených členů korpusu neudělá odpověď nic "
            "ve 212 případech, když se role pojmenuje `jak` napevno, a "
            "v NULE, vezme‑li se pro každou větu jméno, které v ní volné "
            "je. Hlášení proto jmenuje OBOJE — kdo tu roli drží i který "
            "člen zůstal mimo — a dodá, že mapování platí dál; kdyby "
            "člen chyběl z JINÉHO důvodu, řekne se i to, že se neví "
            "proč. Tah, který zabral, o nezměněném čtení MLČÍ"
        ),
        anchor="core_semantics.session:_pointless_answer",
        entry=".play(",
        enforced_by=(
            "test_an_answer_that_changes_nothing_says_so",
            "test_an_answer_that_works_stays_silent_about_it",
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
