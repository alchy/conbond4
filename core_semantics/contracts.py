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
        id="J-2",
        boundary=KERNEL_LEARNING,
        promise=(
            "uzávěrový index se staví nad ZÁKLADNÍMI fakty, takže odvozený "
            "jádrový atom by dal `A` bez účinku — proto se na jádrové "
            "predikáty ptá index, ne shoda s faktem"
        ),
        anchor="core_semantics.engine:Engine._match_kernel",
        # Průchod je `ask`, ne `_match_kernel`. Doložka o vnitřní funkci se
        # musí dát ověřit zvenčí, jinak by ji šlo „doložit" testem, který
        # obchází právě to, co se má hlídat.
        entry=".ask(",
        enforced_by=(
            "test_completeness_has_one_door_too",
            "test_direct_question_about_disjointness_ignores_the_stated_order",
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
            "test_canonisation_refuses_when_identity_is_disputed",
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
