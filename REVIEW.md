# 🛡️ Code Review & Semantic Verification Log

**Kolo:** #12 · 2026-08-14 · **F0.7 uzavřena**, konsolidace pro další fázi
**Rozsah:** `core_semantics/*.py` + `core_semantics/tests/*.py` (20 souborů)
**Jádro:** `docs/CORE-SEMANTICS-0.1.md` **v0.1.4**

## Status: 🟢 PASS — F0.7 termová algebra dokončena

Blocker B‑6 zavřen, žádný otevřený nález, žádné otevřené varování.
Protokol po dvanácti kolech přepsán načisto; historie je v `.agent_state.json`.

### Spouštěcí protokol

| Krok | Výsledek |
|---|---|
| `python -m pytest -q` | ✅ **168 passed** |
| `python -m mypy core_semantics/` | ✅ 20 souborů bez nálezu |
| `pytest test_dialogue_console.py -s` | ✅ transkripty se vypisují (i na cp1252) |

### Architectural Health Score

| Pilíř | Stav |
|---|---|
| Zákaz Skolemizace / No Chase (Cíl 1) | **PASSED** — evaluace nezaloží uzel mimo bázi |
| Per‑role kvantifikace, Dialog A × B (Cíl 2) | **PASSED** — `konkrétní × ∃ → U`, `∃ × ∃ → A` |
| Silná negace, `disjoint`, kontrapozice (Cíl 3) | **PASSED** — `N` i na podtřídu |
| `CONFLICT` jako stav, ne 4. hodnota (Cíl 4) | **PASSED** — oba důkazy |
| Epistemická izolace `K`/`U` (Cíl 5) | **PASSED** — `alt{φ,φ̄} → U` |
| `same_as` jako nedestruktivní pohled (Cíl 6) | **PASSED** |
| I‑16, `DepthExceeded`, determinismus `replay` | **PASSED** |
| Otevřený svět a `complete(g)` | **PASSED** — `U → N` jen s doložením |
| **Termová algebra § 3.0 / § 5.2.1** | **PASSED** — 9 zákonů, dosažitelných dotazem i pravidlem |

---

## 🚨 Critical Blockers

*Žádné.*

**Zavřeno v tomto kole — B‑6.** Devět zákonů `subset*` bylo implementováno,
ale `_match_kernel` směroval `P_SUBSET` na atomickou cestu, takže se z dotazu
ani z těla pravidla nevolaly. Nejhorší důsledek byl tichý: **pravidlo
s algebraickou premisou validací prošlo a nikdy se nespárovalo.**
Opraveno vlastní větví, která bere termy z rolí a jde na `_subset_term`;
nevázaná role hlásí `EvaluationError` jako u ostatních jádrových predikátů.

Builder doplnil právě ty dva testy, které chyběly — přímý dotaz na zákony
a algebraická premisa v těle pravidla. Původní sada testovala jen vnitřní
cestu přes distribuci, proto nález nechytila.

## ⚠️ Semantic Warnings

*Žádné otevřené.* Výkonové položky W‑1 až W‑4 Builder zavřel v kole #8.

---

## 📋 Action Items for Agent 1

## 📜 DODATEK F — pořadí potvrzeno: čeština první, měkká vrstva druhá

**Rozhodl:** člověk (J.), 2026-08-14. **Status:** ZÁVAZNÉ.

Pořadí se nemění: **Priorita 1 čeština, Priorita 2 měkká vrstva a aktivace
(§ 4 / `GapFinder`)**. Odůvodnění člověka — a druhý bod je argument, který
v protokolu nezazněl:

1. **Bottom‑up.** Čeština staví most mezi člověkem a hotovým jádrem. Měkká
   vrstva je naopak rozšíření *vyhodnocování*; stavět epistemickou
   heuristiku nad rozhraním dostupným jen ručně psaným AST je předčasné.
2. **Testovatelnost.** Až budou zlaté transkripty z reálných českých
   konverzací, bude na čem chování aktivace **měřit a ladit**. V opačném
   pořadí by ta data chyběla.
3. **Rozsah.** Měkká vrstva skrývá otevřené koncepční otázky (tlumení,
   prahy, odklon od striktní dedukce). Čeština má hranice narýsované.

### ⚠️ Tři pasti, které F0.7 nově odkryla

**F‑1 · Menu operací se NEPŘENÁŠÍ, přenáší se mechanismus.**
`patterns.py` z conBond3 je cenný kvůli `Operation` jako **uzavřenému menu**
— ale jeho *obsah* je conBond3ový (modalita `possible / necessary /
impossible`). Menu conbond4 je jiné a širší:

```
komparátory  ≤ < = > ≥ ≠          kvantifikátory  ∀ ∃ ·
algebra      AND OR DIFF          strukturní      complete, disjoint, same_as
```

Portovat menu doslova by znamenalo naučit se mapovat česká slova na
operace, které jádro nemá. **Ber třídu a životní cyklus
(`StructuralSignature`, `Trigger`, `LearnedPattern` s proveniencí
a statusem), obsah odvoď z `core_semantics`.**

**F‑2 · „nebo" je v češtině dvě různé jádrové operace.**
Teprve F0.7 dala LEX vrstvě `OR` jako cíl — a tím vznikla nejednoznačnost,
která dřív nemohla nastat:

```
„Petr má psa nebo kočku."        → member(Petr, pes OR kočka)     objektové OR
„Je citron ovoce, nebo zelenina?" → alt{member(c,ovoce), member(c,zelenina)}
                                                                  epistemická alt
```

Totéž slovo, **dvě různé operace jádra**, a rozdíl je v tom, jestli jde
o tvrzení nebo o alternativní otázku. Sem patří kaskáda § 5.2 a při
nerozhodnutém skóre **doptání**, ne heuristika. Analogicky *„kromě / mimo /
až na"* → `DIFF`, *„a / i"* → `AND` — to jsou nové cíle, které před F0.7
neexistovaly.

**F‑3 · Neběžící parser není „nerozumím větě".**
`cb-udpipe` je samostatný proces. Když neběží nebo spadne, `Session` to
**nesmí splynout s neúspěšným rozborem** — první je provozní chyba, druhé
je poctivé „tuhle větu neumím přečíst" a vede na doptání. Splynutí by bylo
tiché selhání vrstvy (I‑1). Dvě různé hlášky, dvě různé cesty.

---

### 🎯 Priorita 1 — česká konverzační vrstva

Rozhodnuto: **má přednost před F0.5 i AML.** Je to klíčové rozhraní systému.

- [ ] **Klient `cb-udpipe`** jako tenká fasáda vracející kandidátní rozbory.
- [ ] **V2 kaskáda čtení** a **V3 rozřešení zmínek**, přecílené na `core_semantics`.
- [ ] **Zlaté transkripty** s fixovaným rozborem.

> **Rozhodnutí, které udělej hned na začátku:** do žurnálu jde **struktura,
> ne text**. Věta se rozloží na kandidáty a stane se z ní týž strukturovaný
> tah, jaký `Session` zpracovává dnes. Kdyby v žurnálu ležely věty, `replay`
> by závisel na verzi parseru a přehratelnost z § 10 by padla — a na té
> stojí měření učitelnosti. `Session` musí umět **oba vstupy**.

### Odloženo — nezačínej

- [ ] **F0.5 `closed_context`** (dodatek B‑III) — nejdřív specifikace, pak kód.
- [ ] **Doména AML** v omezené podobě (dodatek B‑II).
- [ ] **Etapa 2 DIA** — `awaiting_reference`, elipsa (§ 6.11); čeká na V3.

---

## 🇨🇿 conBond3 — mapa znovupoužití

`cb-udpipe` je **vnější orákulum z § 5.1, které reálně běží**: vendorovaný
UDPipe 2 jako samostatný proces, REST na `127.0.0.1:42200`, model 357 MB.
Klient je čistá stdlib — *„hranice vede po procesu, ne po prostředí"* —
takže **TensorFlow se do závislostí conbond4 nedostane**.

| Modul | ř. | Verdikt |
|---|---|---|
| `patterns.py` | 162 | ✅✅ **nejcennější** — `Operation` jako **uzavřené menu**, `LearnedPattern` s proveniencí a statusem. I‑15 a I‑16 hotové; conbond4 pro to nemá protějšek (LEX vrstva neexistuje) |
| `predication.py` | 165 | ✅ čistá extrakce ze stromu závislostí, bez vazby na logiku |
| `clarify.py` | 58 | ✅ doptání nabídne **jen operace z menu**; užitečné až s generátorem můstků |
| `console.py` | 193 | ✅ **vzor** — injektovatelné I/O, díky němuž jde dialog testovat bez člověka |
| `tests/fake_upstream.py` | — | ✅ **hermetické testy bez běžící služby** |
| `cache.py` | — | ✅ klíč nese **model i verzi tokenizéru** → determinismus napříč upgrady |
| `interpret.py` | 488 | ❌ **neportovat** — viz past |
| `learner.py` | 367 | ⚠️ přecílit, ne kopírovat |
| `render.py`, `profiles/cs.json` | 54 | ❌ nahrazeno `presenter.py` |

> ### ⚠️ PAST: conbond4 je „nový koncept, ne úprava"
>
> `interpret.py` dispatchuje `_lower_copular` / `_verbal` / `_operator` —
> **zvláštní větev na každý druh věty**. To je doslova anti‑vzor, který
> § 3.0 jmenuje jako důvod existence conbond4.
> **Beru vzory a menu, nechávám kaskádu.**

---

## 🗺️ Backlog — co engine neumí

### Rozhodnuté a nenaplánované
`F0.5 closed_context` (bez něj nejdou úlohy § 6.9) · `AML doména` · `etapa 2 DIA`

### Slíbené zadáním, ověřeno že chybí

**Měkká vrstva a aktivace (§ 4) — NEEXISTUJE.** Chybí celý průřezový řádek
`G GRAF` z mapy vrstev § 2 a je to odpověď na **pátou zeď** z § 1
(*„propady: když formální vrstva nevěděla, mlčela"*). § 4 slibuje, že místo
mlčení systém nabídne okolí uzlu; dnes při `U` řekne jen „chybí vědět".
**Builder sám označil za nejzajímavější položku backlogu — souhlasím.**

**`GapFinder` je útržek** (`engine.py`, `Gap((query,))` vrací dotaz zpátky).
§ 6.8 („Proč nevíš?") tím splněný není. Builder to potvrdil jako své
vědomé provizorium.

**Časové predikáty § 3.6** — `před / po / během / překrývá` chybí;
`within*` a komparátory hotové jsou.

### Vědomé meze v1 — nejsou to mezery
Žádná aritmetika (a je to *podmínka evaluovatelnosti* `bound`) · žádná plná
temporální logika · žádné vícevětné dokumenty · koreference jen aktivací ·
čeština šablonami.

---

## 💡 Návrhy člověka k rozhodnutí (nejsou zadání)

| | Verdikt |
|---|---|
| **Gaps Ledger** | ✅✅ nejlepší z šesti; musí rozlišit **tři důvody** `U` — chybí fakt / záměrná neúplnost pravidel / mez v1. Jen prostřední je kandidát na rozšíření. Je to měřicí přístroj učitelnosti (§ 10) |
| Dvouúrovňová doložka | ✅ přes `TemplateProfile`; zjednodušení nesmí zaměnit **druh** nejistoty |
| Zlaté transkripty | ✅ musí **fixovat rozbor**, ne ho počítat |
| Missing Link Assistant | ⚠️ je to `GapFinder`; dodat **otevřené podcíle**, ne slibovat abduktivní minimalitu |
| Překladač UD → AST | ⚠️ kaskáda s doptáním, ne přímý překladač (§ 5.2, I‑1) |
| „A to je všechno" → `complete(g)` | ⚠️ **jen přes potvrzení** — `complete` překlápí `U → N` |

---

## Co drží a je pod regresní ochranou

Ověřeno vlastními reprodukcemi v kole #12:

- **9 zákonů `subset*`** dosažitelných **přímým dotazem** i **z těla pravidla**; `disjoint` symetricky v obou pořadích.
- **Negativní kontroly čisté** — `A ⊆ A AND B`, `A OR B ⊆ A`, `X ⊆ A DIFF B` bez `disjoint` neprošly.
- **Zákaz eliminace `OR`** — `member(P, pes OR kočka)` → `A`, `member(P, pes)` → `U`.
- **Dialog E druhově** — bez `disjoint` `U`, po něm `A`; `DIFF` neoslaben.
- **Matice `⪯`**, `disjoint → N`, kontrapozice, `CONFLICT` s oběma důkazy.
- **`complete(g)`** mimo pevný bod, bez falešného `CONFLICT`.
- **Sortové stráže**, **`same_as` jako pohled**, **I‑16**, **No Chase**.
- **Detekce rekurze** i nad algebraickými termy a po scelení identity.
- **Transkripty** se vypíšou i na cp1252 konzoli.

---

*Kolo #12. Všechna potvrzení jsou reprodukovaná spuštěným kódem.
F0.7 uzavřena, řízení předáno Builderovi pro českou konverzační vrstvu.*
