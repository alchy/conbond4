# conBond4 — vývojářská mapa

**K čemu tenhle dokument je.** `CORE-SEMANTICS-0.1.md` říká, **co** systém
znamená — sorty, denotaci, verdikty, uzávěry, invarianty. Tenhle dokument
říká, **kam sáhnout a jak**, když se to má změnit: který soubor, která
funkce, v jakém pořadí to běží, co je povinné doplnit, aby změna prošla
sadou, a co se v tomhle projektu **nesmí** udělat, i když by to fungovalo.

**Pravidlo, které platí nad vším ostatním:** systém nesmí tvrdit nic, co
není pravda — ani o světě, ani o vlastním vstupu, ani o vlastním stavu.
Radši otázka než dohad, radši přiznaná mez než tichý default. Většina
divně vypadajících rozhodnutí v kódu je právě tohle.

**Vrstvy podle priority** (když jsou v konfliktu, rozhoduje pořadí):

```
správnost  →  úplnost  →  pokrytí přirozeného jazyka  →  pohodlí a výkon
```

---

## 1 · Mapa modulů

Vše je v `core_semantics/`. Nic jiného v repu běhový kód není.

| soubor | za co odpovídá | sáhni sem, když… |
|---|---|---|
| `ast.py` | termy, atomy, role, kvantifikátory, `Rule`, sorty, `KERNEL_PREDICATES`, výjimky (`SortError`, `UnquantifiedRole`, `CycleDetected`, `AttachError`) | …měníš **tvar formule** nebo přidáváš jádrový konstruktor. Nejtěžší místo v repu — mění se výjimečně a vždy s doložkou. |
| `storage.py` | `KnowledgeBase` (`attach`, `revoke`, `revoke_utterance`, `inspect`), `ResolvedGraphView`, reifikace vztahů, stratifikace pravidel | …se mění **co a jak se zapisuje**, identita, provenience, odvolávání. **Jediné místo, kde vznikají individua.** |
| `closures.py` | jádrové uzávěry `subset*`, `member*`, `contains*`, `within*`, `before*`, `same_as*`, `complete*` | …se mění uzavírání grafu. Jediné místo v systému, kde je rekurze. Každý krok vrací `Proof`, ne `bool`. |
| `engine.py` | evaluátor: shoda `⪯`, distribuce, pravidla, `derivation()` | …se mění **odvozování**. Engine je **čistě čtecí** — nikdy nezakládá uzel. |
| `epistemics.py` | verdikty `A / N / U / CONFLICT`, kombinace, extenze, výčty | …se mění, co znamená „vím / nevím / je to spor“. Kleeneho tabulky platí **jen pro kombinaci hotových verdiktů**, nikdy pro objektové spojky. |
| `gaps.py` | `GapFinder` — „proč nevíš?“, otevřené podcíle | …chceš zlepšit rozklad mezery. Nedělá abdukci a nemá ji dělat. |
| `oracle.py` | `ParseOracle`, `UDPipeOracle`, `RecordedOracle`, `CachingOracle`, `Token`, `Reading`, `Utterance`, `SegmentationError` | …se mění styk s parserem. Rozbor je **návrh**, ne pravda; nese provenienci s verzí modelu. |
| `cascade.py` | čtení české věty: `generate()` → **patra** → `Verdict`; `Mention`, `RoleReading`, `Predication`; všechny otázky o větě | …**tady se odehrává většina práce.** Nová jazyková konstrukce = nové patro tady. |
| `grounding.py` | zmínka → uzel; sort **plyne z role**, ne ze slova | …se mění, jak se z přečtené věty stává formule. Nic nezapisuje — složí formuli a vrátí ji. |
| `lexicon.py` | `Lexicon`, `Trigger`, `LearnedPattern`, `RoleMapping`, `RelationMapping`, `ScopeOperator`, `MENU`, `czech_seed()` | …se mění, **co se dialog učí**. Učením se mění program, nikdy jazyk. |
| `session.py` | `Session`, `Turn`, `TurnKind`, `TurnResult`, žurnál, `replay`, skládání otázky, zápis do báze | …přidáváš **druh tahu**, měníš pořadí otázek, měníš co se zapíše. |
| `presenter.py` | render odpovědi z důkazu, jazykové profily jako **data** | …měníš výstupní texty odpovědí. Chybějící šablona je hlasitá chyba, ne fallback. |
| `contracts.py` | matice doložek na hranicích vrstev | …**po každé změně chování.** Viz § 9. |
| `metrics.py` | tahy do naučení, informace na tah, znovupoužití, míra oprav | …měříš dialog. Vše se počítá ze žurnálu a báze, nic se nemasíruje průběžně. |
| `unknown_precision.py` | rozklad, **proč** padlo `U`; `RECALL_FAILURE` jako vada | …zkoumáš, jestli bylo `U` na místě. Není tu skóre k minimalizaci — schválně. |
| `parity.py`, `live_check.py` | shoda nahrávek se živým parserem | …ověřuješ, že zlatá sada měří to, co si myslí. **Není to test.** |

---

## 2 · Cesta jedné věty systémem

Tohle je celý běh `Session.utter(text, oracle)`. Když něco nefunguje,
najdi nejdřív **v kterém z těch kroků** se to stalo — chyby vypadají
úplně jinak podle toho, kde vznikly.

```
text  ──1──►  Utterance/Reading  ──2──►  Candidate*  ──3──►  Verdict
                                                                │
                                                                4
                                                                ▼
        zápis do KB  ◄──6──  Grounded (formule)  ◄──5──  Predication + otázky
```

1. **Rozbor.** `oracle.parse(text)` → `Utterance.readings` (n-tice, i když
   dnešní orákulum vrací jedno čtení). Selhání jsou tři různé věci a
   nesmějí splynout: orákulum neodpovídá (provozní chyba, **do žurnálu
   nejde nic**), věta se nerozebrala, věta nese dvě věty
   (`SegmentationError` — **přiznané odmítnutí, ne pád**).
2. **Generátor čtení.** `cascade.generate(reading, mood=…)` → kandidáti.
   Tady vzniká `Predication`: lemma přísudku, role, zmínky. Tady se
   skládají víceslovná jména, data, pohlcené přívlastky.
3. **Patra (§ 3).** `cascade.cascade(reading, tiers=session.tiers())`.
   Každé patro dostane kandidáty a vrátí kandidáty + větu do stopy.
   Smyčka se po rozhodnutí **neukončuje** — patra, která čtení přepisují,
   musí proběhnout i nad jedním kandidátem.
4. **Verdikt.** `Verdict.decided` je čtení **jen když zbylo právě jedno**.
   Nula = „tuhle větu neumím přečíst“ **s důvodem** (`why_nothing`), dva
   a víc = otázka. Nikdy favorit.
5. **Usazení.** `Session._settle(...)` — poskládá otázku (§ 6), doplní
   naučené tvary, rozhodne značku `✓ přečteno` × `◐ přečteno, neúplné`
   a spočítá, jestli se **smí** zapsat.
6. **Zakotvení a zápis.** `grounding` složí formuli (uzel podle jména,
   `Group` u obecného jména, doložení existujícího uzlu u určitého
   popisu), `KnowledgeBase.attach` ji zapíše. **Nový uzel vzniká jen
   `attach`em, nikdy vyhodnocením.**

### Co zápis blokuje

Zapsat se nesmí věta, u které platí kterákoli z těchto věcí (a je to
záměrně přísné — zapsat půlku a mlčet je horší než nezapsat):

* **ztracený člen** — významové slovo, které se do čtení nedostalo a
  systém pro ně roli nemá;
* **role, jejíž jméno je pořád TVAR** (`v+Loc/Geo`, `Dat:arg`) — zapsat
  teď a po odpovědi znovu by uložilo dva výroky o téže větě a ten první
  by nikdo neodvolal (B‑19);
* **čekající konstrukce** — `pending_relation`, `pending_complete`,
  `pending_share`, `pending_name`;
* **role bez kvantifikátoru** — jádro ji do role nepustí
  (`UnquantifiedRole`).

Naproti tomu **otevřená otázka sama o sobě zápis neblokuje** — od
částečného zápisu (0.1.69/0.1.70) se zapíše to, čemu systém rozumí, a
nepojmenovaná okolnost zůstane otevřená. Výjimky, kde se částečně
nezapisuje, jsou čtyři: **negace, podmínka, náhrada** (lexikální
`ScopeOperator`) a **`:arg`** (strukturní). Důvod: pod záporem se
monotonie obrací, takže vynechání by z tvrzení udělalo nepravdu, ne
slabší pravdu.

---

## 3 · Kaskáda: 22 pater v běhovém pořadí

Sestavuje je `Session.tiers()` **při každém tahu znovu** — báze i lexikon
se mezi tahy mění a zamrazit patra v konstruktoru by znamenalo ptát se
staré báze. Test `test_tiers_follow_the_base_between_turns` to hlídá
včetně počtu (`len(first) == 22`), takže **přidání patra ten test
rozbije a to je správně** — je to pojistka proti tichému přibývání.

| # | patro | co dělá |
|---|---|---|
| 1 | `agreement_tier` | shoda rodu/čísla podmětu s přísudkem; **průnikem hodnot**, ne rovností řetězce |
| 2 | `case_tier` | pádová mřížka (podmět Nom, předmět Acc) |
| 3 | `negation_tier` | silná negace `p̄` — jiná věc než nepřítomnost důkazu (I‑21) |
| 4 | `lexicon_tier` | naučené vzory z `Lexicon` |
| 5 | `passive_tier` | trpný podmět je patiens (`nsubj:pass` → `co`); **před** mapováním rolí |
| 6 | `role_mapping_tier` | tvar role → jádrové jméno role z lexikonu |
| 7 | `relation_tier` | jádrová relace ze stavby věty (`subset`, `member`, …) |
| 8 | `naming_tier` | „X se jmenuje Y“ → `name` |
| 9 | `anaphora_tier` | odkaz zájmena; **před** kvantifikátorem (rozhodne ho antecedent) |
| 10 | `prodrop_tier` | nevyslovený podmět; **až za** anaforou |
| 11 | `title_tier` | „básník Josef Hora“ — titul nese tvrzení, **nabídne se a nezapíše** |
| 12 | `subordinate_tier` | vedlejší věta jako role hlavní predikace |
| 13 | `completeness_tier` | návrh na uzavření světa; nikdy nedosazuje |
| 14 | `relative_tier` | vztažná věta jako druhá predikace (o svém uzlu **tvrdí**) |
| 15 | `argument_clause_tier` | předmětová klauze — **čte se, ale nezapisuje** (tvrdí to sloveso, ne věta) |
| 16 | `lost_role_tier` | doplnění ztracené role po odpovědi; **před** kvantifikátorem |
| 17 | `attribute_tier` | přívlastek jako vztah **vedle** věty (druhý výrok) |
| 18 | `quantifier_tier` | `∀ / ∃ / ·`; **až po** přejmenování rolí |
| 19 | `sharing_tier` | druhá věta se sdíleným podmětem; půjčuje si **hotovou** roli |
| 20 | `partial_name_tier` | neúplné jméno uzlu („Rožnov **pod Radhoštěm**“) |
| 21 | `coordination_tier` | souřadné členy |
| 22 | `base_consistency_tier` | konzistence s bází — **vědomě až tady** (potřebuje zakotvenou formuli, a ta potřebuje kvantifikátor, což je naučený vzor) |

### Pravidla pořadí (nejsou kosmetická)

* **Co PŘIDÁVÁ ROLI, musí běžet dřív než to, co role zpracovává** — jinak
  se nová role nestihne zkvantifikovat a věta se nezakotví.
* **Co PŘEPISUJE JMÉNO ROLE, musí běžet dřív než to, co se na jméno ptá**
  — jinak systém na dvou řádcích řekne, že roli nezná a že ji zná.
* **Co jen NAVRHUJE a nikdy nedosazuje** (uzavření světa, titul,
  přívlastek) může jít dozadu; mění to jen pořadí otázek, ne čtení.
* Každá odchylka od pořadí v § 5.2 spec **musí být v kódu odůvodněná
  komentářem** — jedna taková tam je (`base_consistency_tier`) a je
  popsaná i tady.

### Jak vypadá patro

```python
def moje_patro(lexicon: Lexicon) -> Tier:          # nebo bez argumentu
    def tier(
        candidates: tuple[Candidate, ...], reading: Reading
    ) -> tuple[tuple[Candidate, ...], str]:
        ...
        return novi_kandidati, "[ZNAČKA: co se stalo]"   # "" = mlčky nic
    return tier
```

Návratová věta jde do `Verdict.trace` a odtud do výstupu pro člověka.
**Patro, které něco zahodí a nic neřekne, je vada** (I‑1).

---

## 4 · `Predication` — co smí patro zapsat

`Predication` je nosič mezi patry. Každé pole má vlastníka a **stav, na
kterém někdo staví, musí mít vlastní pole** — ne poznámku v cizím
řetězci. (Tahle věta stála projekt tři samostatné vady: `collided`,
`shaped`, `pending_relation`.)

| pole | význam | blokuje zápis? |
|---|---|---|
| `predicate`, `roles` | lemma přísudku a role | — |
| `negated` | **silná** negace, ne absence důkazu | — |
| `relation` | jádrová relace, kterou stavba tvrdí | — |
| `pending_relation` | čeká se na význam konstrukce | **ano** |
| `pending_complete` | věta navrhuje uzavřít svět | **ano** |
| `pending_share` | „o každém zvlášť, nebo dohromady?“ | **ano** |
| `pending_name` | uzel by nesl zkrácené jméno | **ano** |
| `pending_attribute` | přívlastek jako vztah vedle věty | ne |
| `pending_title` | titul nese tvrzení | ne |
| `second` | druhá predikace téže promluvy | — |

Na roli (`RoleReading`) jsou vlastní pole pro: `quantifier` (`None` =
**nerozhodnuto**, ne „žádný“), `dropped` (pro‑drop), `collided` (jméno
role zabral někdo jiný v téže větě), `shaped` (jméno je pořád tvar),
`pending` (tvar, na který se čeká), `awaiting` (**na co** se čeká),
`offered` (nabídnutí kandidáti — je to stav, ne věta v otázce),
`resolved` (rozhodl člověk), `absorbed` (tokeny složené do lemmatu).

**Nikdy nedopočítávej zpětně to, co někdo rozhodl.** Dopočet hádá — a
příště hádá jinak.

---

## 5 · Jádro: co se nesmí

* **Individua vznikají výhradně přes `KnowledgeBase.attach()`.** Ani
  dotaz, ani `Engine.derivation()`, ani grounding nesmí založit uzel.
  Reifikace vztahu patří do `storage`, ne do evaluátoru — uzel musí mít
  id výroku, provenienci a `derived_from`, aby na něj dosáhl `inspect`
  i kaskádové `revoke`.
* **Kvantifikátor sedí na `RoleTerm`, ne na termu.** `Group` ani `Entity`
  kvantifikátor nemají a mít nesmějí.
* **`Rule.__post_init__` brání zápisu do nenegovaných jádrových
  predikátů** (I‑16). Naučené pravidlo nesmí psát do `member`, `subset`,
  `contains`, `within`, `before`, `name`, `same_as`, `complete`,
  `disjoint`.
* **`same_as` nemergeuje fyzicky.** Fakta si drží původní `resolved_id`;
  kolaps do tříd dělá `ResolvedGraphView` při čtení. Proto je `revoke`
  identity nedestruktivní — jen se postaví jiný pohled.
* **Absence ≠ negace** (I‑21). Jediná výjimka je `complete(g)`, a i ta
  cituje, **nad čím** se zavíralo.
* **`CONFLICT` nese OBA důkazy.** Není to chyba, je to stav dotazu.
* **Sort plyne z ROLE, ne ze slova.** „Praha“ je `Place` v roli `kam`,
  protože `kam` je prostorová role slovníku jádra — ne proto, že by si
  o Praze někdo něco myslel.
* **Determinismus** (I‑4): „teď“ je pořadové číslo tahu, ne čas stroje.
  Žádné hodiny, žádná neseedovaná náhoda — `replay(žurnál)` musí dát týž
  program i tytéž odpovědi.

---

## 6 · Otázky — kdo je staví a v jakém pořadí

Otázka je **plnohodnotný tah dialogu a zdroj učení**, ne selhání. Skládá
se v `Session._settle` v tomhle pořadí a pořadí je věcné:

```
open_roles_question      role, které čekají na kvantifikátor / odkaz
lost_question            ztracený člen
role_question            význam povrchové role  (z HOTOVÉ predikace, ne ze stopy)
passive_question         srážka dvou patiensů
relation_question        co ta stavba tvrdí
complete_question        má se zavřít svět?
attribute_question       co tvrdí přívlastek        ← vztah vedle věty, neblokuje
title_question           co tvrdí titul             ← totéž
share_question           každý zvlášť, nebo dohromady?
relative_question        koho se týká vztažná věta
grounded.question        který uzel se míní
```

**Pravidla, která se u otázek porušují nejsnáz:**

* Ptej se z **hotové predikace**, ne ze stopy. Stopa je log jednoho tahu
  — odpověď na cokoli jiného ji zahodí a otázka se ztratí.
* Otázka nesmí tvrdit o vstupu nic, co není pravda. Když se nálepka
  (pád, druh, tvar) nedá z rozboru přečíst, **nálepky se vzdej** a mluv
  jen o tom, co je vidět. Hádat ji z lemmatu je táž vada o patro níž.
* Otázka, na kterou neexistuje tah, jak ji zodpovědět, je horší než
  mlčení.
* Nabízené možnosti musí pokrývat, co věta může znamenat. Otázka se
  dvěma odpověďmi u konstrukce, která má tři čtení, nutí člověka říct
  nepravdu.

---

## 7 · Tahy dialogu

`TurnKind` v `session.py`. Vlastní druh tahu si zaslouží to, co má
**jinou váhu** — ne to, co se jen jinak jmenuje.

| tah | co dělá | učí se? |
|---|---|---|
| `!` `ASSERT` | zapíše formuli | — |
| `«` `READING` | česká věta | podle odpovědí |
| `?` `?~` `?=` `?∃` | otázky (bound / describe / enumerate) | ne (I‑12: otázka bázi nemění) |
| `✗` `REVOKE` | odvolá výrok; `revoke_utterance` odvolá **celou promluvu** | — |
| `!∦` `!≠` `!÷` | disjunkce skupin, různost, rozdělení uzlu (M‑1, M‑2) | — |
| `→∀` | odpověď na kvantifikátor — **naučí TVAR** | **ano** |
| `→∀1` | kvantifikátor **téhle jedné věty** | **ne** |
| `→⊆` | která jádrová relace — naučí tvar | **ano** |
| `→⊆1` | relace **téhle jedné věty** | **ne** |
| `→@` | jméno role ztraceného členu | **ano** |
| `→@1` | co tvrdí genitivní přívlastek | **ne** (týž tvar, opačný směr) |
| `→=` | který uzel se míní | ne |
| `→&` | každý zvlášť × dohromady | ne |
| `→'` | koho označuje přivlastňovací přívlastek — **přidá FAKT** | ne |
| `→∈` | potvrzení titulu; **bez nabídky se odmítne** | ne |
| `!∀` | uzavření světa nad skupinou | ne |

**Rozdíl `→∀` × `→∀1` je celá filozofie projektu v jedné dvojici:** „jak
se čte tenhle tvar“ a „jak se čte tahle věta“ jsou dvě různé otázky a
splynout nesmějí. Když si nejsi jistý, do které kategorie tvůj nový tah
patří, je to skoro jistě ta druhá — učit se smí jen to, co v jiné větě
znamená totéž.

---

## 8 · Lexikon a učení

> Učením se mění **program**, nikdy **jazyk**. Dialog učí, které slovo
> spouští kterou **už existující** operaci jádra — nikdy nevyrábí novou
> sémantiku (I‑15, I‑16).

* `StructuralSignature` → `Trigger` → `LearnedPattern` (s proveniencí a
  statusem `PatternStatus`).
* `RoleMapping` — tvar role → jádrové jméno role.
* `RelationMapping` — tvar konstrukce → jádrová relace. **Váží víc než
  ostatní vzory**, protože mění, co se ZAPÍŠE, ne jak se věta čte;
  špatný `subset` změní uzávěr celé báze.
* `ScopeOperator` — negace / podmínka / náhrada jako **odvolatelná data**,
  ne seznam v kódu.
* Shoda vrací **kandidáty**, ne jedno mapování: české „nebo“ jsou dvě
  různé operace jádra podle toho, jestli jde o tvrzení, nebo o otázku.

**Co se nikdy nesmí naučit jako tvar:** cokoli, co má při identickém
rozboru opačný směr nebo jiný význam. Kanonický příklad — „chov zvířat“
a „péče majitele“ mají týž tvar a opačný směr, takže genitivní přívlastek
se **neučí** a ptá se u každé věty znovu. Když si to říkáš jako „ale to
je skoro vždycky…“, je to signál, že se učí něco, co se učit nemá.

**Kdykoli přidáváš tvar, ověř, že se dá NAJÍT.** Vzor uložený bez
`lemma` se ukládá jako strukturní a signatura s lemmatem ho nenajde —
táž věta se pak zeptá podruhé. (Stálo to 47 tvarů z 206.)

---

## 9 · Doložky (`contracts.py`) — povinná část každé změny

Matice pokrývá hranice mezi vrstvami, protože poslední vážné vady nebyly
uvnitř vrstev, ale ve **smlouvě mezi nimi**: jedna vrstva něco slíbila,
druhá to četla jinak, a nikde nestálo, čí to je závazek.

Hranice: `jádro → učení`, `oracle → cascade`, `cascade → session`,
`session → storage`, `storage → cascade`.

```python
Clause(
    id="S-54",
    boundary=CASCADE_SESSION,
    promise="CO se slibuje, a PROČ zrovna takhle",
    anchor="core_semantics.cascade:jmeno_symbolu",   # musí jít rozřešit
    entry=".utter(",                                 # VEŘEJNÝ vstupní bod
    enforced_by=("test_…", "test_…"),
)
```

Čtyři sloupce, všechny **odvozené, ne deklarované**:

| sloupec | co se ověřuje | co chytí |
|---|---|---|
| `typ` | `anchor` jde rozřešit | přejmenování symbolu |
| `smysl` | u symbolu je docstring | doložku bez významu |
| `použití` | ve zdroji vynucujícího testu je doslovný `entry` | **obchvat** — test nad vnitřní funkcí není ověření |
| `test` | všechny testy z `enforced_by` existují | vymyšlené jméno testu |

Doložka označená jako **držená musí mít všechny čtyři**. Otevřená doložka
(`Status.OPEN`) musí říct `closes_with` a nesmí tvrdit, že ji něco
vynucuje. Sloupec `použití` existuje kvůli konkrétní vadě: test nad
`cascade()` volanou napřímo byl zelený, zatímco `Session.utter` patra
nepředávala.

**Doložka nese i změřená čísla.** Když jsi měřil dopad, patří to do
`promise` — čísla se citují a musí sedět. Když se ukáže, že bylo změřené
špatně, oprav ho i s poznámkou, odkud oprava je.

---

## 10 · Testy

```bash
python -m pytest -q
```

```bash
python -m mypy --strict core_semantics/
```

**Sada je hermetická a musí zůstat.** Testy nesmějí sáhnout na běžící
službu — jinak začnou padat podle toho, co je zrovna spuštěné, a měří
dvě věci najednou.

| soubor | co drží |
|---|---|
| `golden.py` | zlaté transkripty: česká věta + **fixovaný rozbor jako data**, s `PROVENANCE` |
| `dialogues.py` | domény a kroky dialogu; `standing_metrics()` vrací `21 domén / 107 kroků / 51 zápisů / 33 odpovědí / 26 otázek` |
| `test_contracts.py` | matice doložek + počet pater |
| `test_cascade.py`, `test_naming.py`, … | jednotlivé rodiny konstrukcí |
| `test_adversarial.py` | pokusy systém přinutit tvrdit nepravdu |
| `test_parity.py` | shoda nahrávky s živým rozborem |

**Živý běh proti službě** (není test, pouští se ručně):

```bash
python -m core_semantics.live_check
```

Rozdíl proti nahrávce **není chyba, je to nález k rozhodnutí**: buď se
změnil model (řekne to provenience), nebo parser čte jinak, než jsme si
mysleli, když jsme rozbor psali rukou. Do sady se to **nezanáší
automaticky**.

### Když ti test spadne po změně chování

Spadlý zlatý přepis znamená **jednu ze dvou věcí** a spletení je drahé:

* změna je špatně → oprav změnu;
* přepis byl špatně → **oprav přepis, ale zvlášť a s odůvodněním**.

Co se **nikdy** nesmí: upravit zlatý přepis, aby prošla změna, kterou
zrovna píšeš, v témže kroku a bez zmínky. Je to nejrychlejší způsob, jak
z regresní sady udělat dekoraci.

---

## 11 · Měření: jak zjistit, co změna udělala

Tohle je oddíl, který v tomhle projektu stál nejvíc omylů, takže je
psaný jako postup.

**1 · Změř cíl PŘED stavbou.** Kolik případů v korpusu ta rodina má a co
s nimi systém **dnes** dělá. Deprel je hypotéza, ne míra: rozklad podle
jmenovky rozboru nadsadil rodinu proti skutečnosti už dvakrát (např. ze
75 `xcomp` jich 44 visí pod „moci“/„muset“ a jsou dávno obsloužené).

**2 · Změř účinek TOUŽ POPULACÍ NA OBOU REVIZÍCH.** Ne „před“ na jedné
definici a „po“ na jiné — rozdíl dvou populací není účinek ničeho.

```bash
git archive --format=tar -o /tmp/pred.tar <předchozí-sha>
```

Rozbal, pusť **identickou** sondu s `PYTHONPATH` na starý strom a na
nový, a porovnej. Korpus je v sesterském repu:
`conbond4-utils/mereni/2026-08-15.json` (238 vět).

**3 · Napiš předpověď tak, aby šla vyvrátit.** „Mělo by se to zlepšit“
není předpověď. „Počet odkazů s prázdnou nabídkou klesne, počet odkazů
nutně ne“ ano.

**4 · Když předpověď mine, je rozbor důležitější než ta změna.** Odchylka
je informace o tom, že populace nebo model účinku byl špatně — a to je
cennější než hotová funkce.

**5 · Sonda, která neumí odpovědět na všechno, měří sebe.** Napiš ji tak,
aby uměla ukázat i jednotlivé případy, ne jen číslo, a **podívej se na
pár řádků**. Reálná past z tohohle projektu: hlášení má tvar
`„dítě“ (deprel pod „hlava“)` — regulární výraz, který bere všechny
uvozovky, započítá i jméno hlavy jako ztrátu.

**Metriky, které systém umí sám:** `metrics.measure` (tahy do naučení,
informace na tah, znovupoužití, míra oprav), `unknown_precision.survey`
(proč padlo `U`; `RECALL_FAILURE` je **vada**, ne nález).

---

## 12 · Podlaha před commitem

Nic z tohohle se nesmí zhoršit — a když ano, musí to být pojmenované
rozhodnutí, ne vedlejší účinek:

- [ ] `python -m pytest -q` — vše zelené
- [ ] `python -m mypy --strict core_semantics/` — čisté
- [ ] doložky: všechny držené mají čtyři sloupce, žádná otevřená bez
      `closes_with`
- [ ] `standing_metrics()` = 21 / 107 / 51 / 33 / 26
- [ ] zlaté přepisy drží, nebo je změna přepisu odůvodněná zvlášť
- [ ] korpus proběhne bez pádu (dvě věty se odmítnou pojmenovanou
      `SegmentationError` — to je v pořádku)
- [ ] počet zapsaných korpusových vět neklesl **a žádná není nepravdivá**
- [ ] nová doložka pro nové chování, s číslem, které jsi opravdu změřil
- [ ] verze jádra a řádek v changelogu `docs/CORE-SEMANTICS-0.1.md`

---

## 13 · Vady, které se v tomhle projektu opakují

**1 · Přesná shoda na kategorii, která má varianty.** Zdaleka nejčastější
— přes deset instancí. Porovnání `deprel == "obl"` mine `obl:arg`;
`feats["Number"] == "Plur"` mine `Plur,Sing` (což je **přiznaná
víceznačnost tvaru**, ne konjunkce dvou tvrzení); výčet
`{kde, kam, kdy}` mine sedmé tázací příslovce. **Rozhoduj podle rysu
z rozboru, ne podle výčtu**, a když výčet být musí, napiš k němu, co do
něj nepatří a proč.

**2 · Populace, která nesedí na to, co stavíš.** Změříš děti pod
pohlceným `amod`, ale postavíš pro děti pod pohlceným **příčestím** — a
pak porovnáváš dvě různá čísla. Definice rodiny se ověřuje stejně jako
její velikost.

**3 · Stav v cizím poli.** Značka, na které někdo staví, musí mít vlastní
pole. Poznámka nacpaná do `source` nebo do textu otázky se o krok dál
přepíše a nikdo si toho nevšimne.

**4 · Zpětný dopočet rozhodnutí.** Co někdo rozhodl, se nese; co se
dopočítává ze stromu, se hádá — a příště se hádá jinak.

**5 · Tichý default tam, kde je otevřená otázka.** `None` u kvantifikátoru
znamená „nerozhodnuto“, ne „žádný“. Jakmile se s tím začne počítat jako
s hodnotou, vyrobí se tvrzení, které nikdo neřekl.

**6 · Ochrana cizím pravidlem.** Když se něco nezapíše špatně jen proto,
že to blokuje **jiná** podmínka, není to ochrana — vydrží přesně do
chvíle, kdy se to druhé pravidlo z nesouvisejícího důvodu uvolní. Napiš
pojistku tam, kam patří.

---

## 14 · Kam se dívat dál

* `docs/CORE-SEMANTICS-0.1.md` — formální jádro; **§ 12** je průběžný
  záznam rozhodnutí „změřeno, nepostaveno“ a **§ 13** akceptační sada.
* `docs/CORE-SEMANTICS-0.1-PODKLAD.md` — tři rozhodnutí, ze kterých
  jádro vzniklo.
* `docs/ZADANI-CONBOND4.md` — původní zadání.
* `docs/EXAMPLES.md` — příklady dialogů.
* `REVIEW.md` — poslední audit: co drží, co je otevřené, co se právě
  měří. Než něco začneš stavět, podívej se sem, jestli to už není
  změřené jako prázdné.
* `agent-tasks/` — rozdělení práce, protokol a pravidla pro agentický
  workflow.
