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

## ✅ KOLO #16 — B‑8 zavřen, žádný blocker

`pytest` **207 passed** · `mypy --strict` čistý na 26 souborech ·
regrese celá drží · LEX beze změny.

Motivační případ § 5.2 teď prochází **doslova tak, jak ho zadání popisuje**:

```
Obsahuje citron vitamíny?   (parser NEDAL podmět, oba nominály obj)
  generátor: 2 čtení
    obsahovat(co:citron,  kdo:vitamín)   [doplnění podmětu (parser ho nedal)]
    obsahovat(co:vitamín, kdo:citron)    [doplnění podmětu (parser ho nedal)]
  [PROČ: shoda čísla — přísudek Sing, podmět musí být týž] → zbývá 1
  → obsahovat(co:vitamín, kdo:citron)
```

Hláška je doslova ta ze zadání. Výsledek nemá duplicitní role a **jde
převést na `Atom`** — ověřeno. Fixture v testu už má oba nominály jako `obj`,
takže komentář a data si neprotiřečí.

**Vedlejší zisk:** zmizela i přestřelená nejednoznačnost u spony. „Citron je
ovoce." dává teď **1 čtení**, ne dvě s otázkou — když parser `nsubj` označil,
záměna se negeneruje. Nezadával jsem to; je to správně.

**Nerozhodnutelný případ** (dvě jména, obě Sing i Nom) dál vrací
**2 přeživší + otázku**, `decided is None`. ✓

---

## 📜 DODATEK I — externí konzultace: verdikt a co z něj plyne

**Zdroj:** nezávislý konzultant, 14. 8. 2026. **Status:** ZÁVAZNÉ pro P0.

Celkový verdikt: **jádro nepřepisovat.** Zákaz skolemizace, otevřená doména,
oddělení inference od jazyka, provenience důkazů a deterministické
vysvětlení jsou označeny za dobrá rozhodnutí. Vlastní engine je obhajitelný;
ASP jako základ ne; skolemizaci nezavádět.

> *„Největší riziko není, že je engine špatně implementovaný. Největší riziko
> je, že některé pojmy mají jinou sémantiku, než jakou dokumentace naznačuje."*

### 🔴 I‑P0‑a · `certain` / `possible` / `DIFF` — POTVRZENO A REPRODUKOVÁNO

Konzultant tvrdí, že dvojice `certain`/`possible` neuchovává **korelace mezi
nejistotami**, takže `possible(A) \ certain(B)` označí za možné i to, co
možné není. **Ověřil jsem to a je to pravda** — ale dosah je užší, než by
se z popisu zdálo. Tři zjištění:

**(1) Korelaci nejde vyslovit pravidly nad `member`.** Blokuje to I‑16:

```
member(x,B) <- member(x,A)   → UnsafeRule: přepsalo by jádrový predikát
```

**(2) Přes `subset` obousměrně ale ano — a jev se reprodukuje:**

```
subset(A,B) ∧ subset(B,A)          # tedy A = B, rozdíl MUSÍ být prázdný
certain(A DIFF B)  → []            ✓ správně
possible(A DIFF B) → ['Petr']      ✗ Petr možný být nemůže, A = B
```

**(3) `certain` strana je ale EXAKTNÍ, ne intervalová.** `query_diff` se
neptá přes `possible(B)`, ale **na každý prvek zvlášť** přes
`member*(x, A DIFF B)`:

```
certain  : ['Hrabal']    ← jen doložený nečlen
uncertain: ['Seifert']   ← o něm se neví
```

**Z toho plyne přesná míra rizika:** chyba je jen v `possible`, a je
v **bezpečném směru** — over‑approximace. Systém nikdy neřekne `A` ani `N`
tam, kde nemá; jen řekne „možná" tam, kde by přesnější sémantika řekla „ne".
**Engine je korektní, nekompletní.** Vadná je formulace § 3.2, ne kód.

**Rozhodnutí: přijmout konzultantovu variantu A** — popsat `certain`/`possible`
jako **dolní a horní aproximaci znalosti**, ne jako přesnou sémantiku možných
světů, a `DIFF` jako **sound interval propagation**, ne jako obecnou
operaci nad možnými světy. Je to změna § 3.2 dokumentu, tedy verzované
jádro → podpis a posun verze.

### 🔴 I‑P0‑b · Argument o rozhodnutelnosti je příliš slabý

Konzultant má pravdu: § 6.3 argumentuje přes monadickou predikátovou logiku,
ale skutečná konstrukce má reifikované vztahy, vícemístné predikáty,
pravidla, tranzitivní uzávěry, silnou negaci, stratifikaci, algebraické
termy, `complete` a identitní ekvivalence. **Monadická FOL to neunese.**

Skutečným základem terminace je bezpečný fragment z § 5.4 — žádné funkční
symboly, žádná existence v hlavě, konečná množina konstant, omezená hloubka,
acyklický dependency graf. Navrhovaná charakterizace:

> **konečný, typovaný, stratifikovaný Datalog‑like deduktivní systém
> s několika vestavěnými relačními closure operátory a epistemickou vrstvou
> nad dotazem**

A tvrzení „systém je PTIME" nesmí zůstat holé — musí říct **PTIME v čem**:
velikost báze, počet pravidel, velikost dotazu, hloubka termů, délka
role‑chain, počet scelení identity, počet strat.

**Terminologie:** nepoužívat `Datalog±` jako hlavní analogii — právě
existenční hlavy a chase jsou to, čemu se conBond4 vyhýbá.

### 🔴 I‑P0‑c · Oddělit existenci od identity svědka

Povýšit na **explicitní axiom sémantiky**: `∃x P(x)` může platit, aniž by
v grafu existovalo `id(x)`. Dnes to systém dělá správně, ale nikde to není
napsané jako axiom.

### 🟠 P1 — čtyři položky

1. **`complete` jako epistemická deklarace uzavřenosti**, ne jako inferenční
   fakt. Implementace to už tak dělá (vyhodnocuje se mimo pevný bod);
   chybí to takhle **pojmenovat** v dokumentu.
2. **Contract systém.** Odpověď na moji otázku 10 a je lepší než co jsem
   navrhoval: **coverage matrix metajazyka** — každý konstruktor má
   explicitní stav ve sloupcích *syntax · typování · denotace · evaluátor ·
   důkaz · renderer · test*, a CI nesmí dovolit označit feature za hotovou,
   dokud není řetěz uzavřený. Ideálně generováno z AST. Přesně to by
   odchytilo `before`.
3. **Hranice parseru.** Zpřesnění mého dodatku H‑4(1): báze smí eliminovat
   čtení **jen když pro to existuje explicitně definovaný sémantický důvod**
   (formální konflikt, typová chyba, nesplnitelný constraint) — ne „tahle
   interpretace se mi nehodí". Jinak vzniká self‑confirming loop.
4. **Nenárokovat „minimální vysvětlení".** Kanonický důkaz je minimální
   podle **definované syntaktické metriky**, což není totéž co minimální
   lidsky srozumitelné vysvětlení. Konstrukci zachovat, formulaci opravit.

### 🟡 P2 — dvě položky

5. **Coreference:** pořadí ponechat, ale **připravit rozhraní už teď** —
   `zmínka → kandidátní referenti → evidence → status → potvrzení člověkem
   → identitní operace`. Aktivaci neimplementovat, dokud nebudou reálné
   české dialogy, na kterých půjde poznat, jestli stačí recency, sdílený
   vlastník, vzdálenost v grafu nebo učené řazení.
6. **Metriky:** „počet tahů" je dobrá **sekundární** metrika, špatná hlavní —
   dá se gamingovat jedním tahem „potvrď mi celou interpretaci". Doplnit
   **informaci na tah**, **znovupoužití** naučeného pravidla a hlavně
   **regret / correction rate**: jeden tah do naučení a deset chybných
   použití je horší než tři tahy a stabilní správnost.

### Pořadí, které konzultant doporučuje

**Nejdřív formální hardening, teprve pak čeština.** Fáze 1 (P0): formalizovat
výpočetní model, rozhodnout význam `certain`/`possible`, oddělit existenci od
identity svědka. Fáze 2 (P1): contract systém, hranice parseru, zlatá sada,
a teprve potom aktivace.

**To je v rozporu s dodatkem G**, který stanovil „nejdřív dokončit, co máme".
Není to ale spor věcný — hardening je z velké části **práce v dokumentu**,
ne v kódu, a dodatek G už obsahuje dvě položky (`before`, dialog D), které
jsou přesně o tom, aby dokument nelhal. **Rozhodnutí o pořadí je na člověku.**

---

## ✅ KOLO #17 — `GapFinder` hotový, žádný blocker

`pytest` **216 passed** (bylo 207) · `mypy --strict` čistý na 28 souborech ·
jádro 0.1.4 beze změny · `before` správně **nezačat**, čeká na podpis ·
regrese celá drží.

Ověřeno přes `GapFinder.explain()`. Všechna čtyři patra fungují:

```
dialog E   chybí vědět: subset(vrabec, (pták DIFF tučňák))  [fakt s0003, role kdo]
           chybí vědět: disjoint(vrabec, tučňák)            [zákon X ⊆ A ∧ disjoint(X,B)]
řetěz      vím: Hrabal patří do spisovatel
           chybí vědět: subset(spisovatel, dramatik)        [uzávěr member*]
pravidlo   chybí vědět: member(Jan, prověřený)              [pravidlo p3]
```

**Nejcennější je ten sestup.** Report u dialogu E nekončí na
`subset(vrabec, pták DIFF tučňák)` — což je pravda, ale nedoplnitelná —
nýbrž dojde přes zákon 9 k **`disjoint(vrabec, tučňák)`**, tedy doslova
k větě, kterou člověk v příštím tahu řekne. To je rozdíl mezi rozborem,
který popisuje mezeru, a rozborem, který ji **umí zavřít**.

Builderovo odůvodnění pořadí 4‑5‑6 je navíc lepší než moje: až bude
`Session` napojená na češtinu, bude `U` nejčastější odpověď, takže
`GapFinder` vracející zopakovaný dotaz by vrstvu shodil při prvním reálném
dialogu.

**Přiznané meze jsou v pořádku:** hloubka i počet větví zastropované,
vyčerpání se hlásí jako `exhausted`, a je řečeno, že introspekci má jen
zákon 9.

### ⚠️ W‑5 · `_missing_link` nepokrývá role sortu `Place` a `Time`

Ověřeno v `gaps.py:324`: uzavírající článek se odvodí jen pro role se
sortem `Group` (`∀×∀`, `∃×∃`, `konkrétní×∀`). Pro místa a časy vrací `None`,
takže report spadne na obecné *„žádné pravidlo tohle nevyrábí"*:

```
báze:  jel(kdo:Petr, kam:Praha)
dotaz: jel(kdo:Petr, kam:Brno)
report: chybí vědět: jel(kam:Brno, kdo:Petr)  [žádné pravidlo tohle nevyrábí]
        ← užitečnější by bylo ukázat na roli `kam` a na contains*
```

Report zůstává **poctivý**, jen málo užitečný. Dnes to skoro nevadí —
**ale dialog D je právě o místech a časech**, takže to udeří přesně ve chvíli,
kdy `before` dostane podpis a dialog D se bude psát. Přidat `contains*`
a `within*` do `_missing_link` je pár řádků a je lepší to udělat před
dialogem D než po něm.

### Moje chyba v postupu, znovu táž

První sondu jsem vedl přes `Engine.ask()`, kam `GapFinder` napojený není —
je v `Session`. Dostal jsem zopakovaný dotaz a málem to označil za nález.
**Je to podruhé týž omyl** (poprvé u `subset*` v kole #15): testuju vrstvu
přes vstupní bod, který ji neobsluhuje. Opatření: než něco označím za
chybějící, ověřím si, **kudy se to volá**, ne jestli to vidím z API, které
mám zrovna po ruce.

---

## 📜 DODATEK H — `before*` SCHVÁLEN (varianta A) + tři doporučení k české vrstvě

**Rozhodl:** člověk (J.), 2026-08-14. **Status:** ZÁVAZNÉ.
Ruší sekci „Rozhodnutí k podpisu" níže.

### H‑1 · Zadání (doslovně)

- `P_BEFORE` / `before_of` pro sort `Time`
- `closures.py`: **tranzitivní uzávěr `before*`, striktně nad sortem `Time`**
- `engine.py`: propojit dotaz `before(t1, t2)` na uzávěr
- Dokumentace: verze **0.1.4 → 0.1.5**, `before*` do tabulky § 5.1, řádky do § 13
- Test: **akceptační dialog D** — `? Kam jel Petr dřív — do Prahy, nebo do Brna?`
  přes `before(kdy(r7), kdy(r8))`, s ověřením `A` / `N` / `U` podle § 4

**Drobnost:** zadání zmiňuje `engine.py / matching.py`. **`matching.py`
v projektu neexistuje** — párování je v `engine.py` (`_match_kernel`).
Nezakládej nový soubor.

### H‑2 · `během` a `překrývá` zůstávají mimo

Zadání mluví jen o `before`, což odpovídá doporučení: „po" je `before`
obráceně, „během" je `within`, a „překrývá" by vyžadoval intervaly
s koncovými body — to je jiná, větší věc a dialog D ji nepotřebuje.

### ⚠️ H‑3 · JEDNA PODOTÁZKA ZŮSTALA NEZODPOVĚZENÁ — cyklus v uspořádání

Ptal jsem se, jestli se má rozpor hlásit. Zadání na to neodpovídá, takže
**to zůstává otevřené a Builder to nesmí rozhodnout sám** (byl by to nový
druh inference v jádře).

Proč na tom záleží: `before(a,b)` a `before(b,a)` jsou nekonzistentní.
Tranzitivní uzávěr z toho odvodí `before(a,a)` — a pak **je všechno před
vším**. Dotaz „Jel Petr dřív do Prahy?" i „…dřív do Brna?" by oba vrátily
`A`, aniž by na tom bylo něco vidět. To je přesně ta tichá nekonzistence,
kterou systém jinde (`p ∧ p̄` → `CONFLICT`) hlásí.

**Konzervativní default do doby, než člověk rozhodne:** uzávěr cyklus
**detekuje** (reflexivní dosažitelnost `before*(x,x)` už z výpočtu plyne)
a **netiše neodpoví** — hlásí chybu s důvodem, jako to dělá
`EvaluationError` u nevázaných rolí. Zapojení na `CONFLICT` s oběma důkazy
počká na podpis. Do § 5.1 to zapiš jako **otevřenou položku**, ne jako
hotovou záruku.

### H‑4 · Tři doporučení k české vrstvě

**(1) Jednosměrnost vlivu — ale POZOR na formulaci.** Doporučení znělo, že
parser nesmí mít přístup k bázi. **Tak to nejde** — § 5.2 zadání
(řádky 597‑602) vede *„konzistence s bází (signatury známých vztahů;
aktivované uzly)"* jako **patro kaskády**, a `base_consistency_tier` je už
implementované. Odstřihnout bázi by vypustilo patro, které zadání předepisuje.

Správná formulace téhož záměru:

> **Báze smí kandidátní čtení jen ZÚŽIT nebo SEŘADIT. Nesmí strukturu
> doplnit ani vytvořit** (I‑2).

Přesně to je v docstringu `base_consistency_tier` a ověřoval jsem to
v kole #15. Detekce `U` se tím neruší: báze rozhoduje, **která otázka byla
položena**, ne jaká je odpověď — čtení je pevné dřív, než začne evaluace.

Co z původní obavy platí: kaskáda čtoucí bázi může u téže věty dát v různých
okamžicích jiné čtení, protože báze mezitím vyrostla. Pro dialog je to
správné a je to **další důvod, proč do žurnálu jde struktura, ne text**.

**(2) Rozhraní pro doptávání — UŽ EXISTUJE, nestavět znovu.**
`Verdict` nese `survivors`, `trace` i `question`; při víc čteních je
`decided is None` a `question` vyplněná; `lexicon_tier` nerozhoduje.
Ověřeno v kolech #15 a #16. **Chybí jen propojit tu otázku s
`XAIPresenter`em**, až se bude `Session` napojovat.

**(3) Zlaté větičky pro dialogy A–F — přijato bez výhrad.**
Napsat české věty a očekávané AST **dřív než kód** je psaní akceptačního
testu před implementací. Dvě upřesnění: rozbor se musí fixovat přes keš
klíčovanou modelem a verzí tokenizéru, jinak upgrade UDPipe rozbije všech
šest naráz; a **dialog D jde napsat teprve po H‑1**.

---

## ~~❓ ROZHODNUTÍ K PODPISU~~ — vyřešeno dodatkem H

**Moje chyba v dodatku G, kterou napravuji.** Napsal jsem tam „implementuj
`before`" a připojil jen poznámku o posunu verze. Jenže je to zásah do
**verzovaného jádra**, a v tomhle protokolu prošla každá taková změna
explicitním schválením — dodatky A, B‑I, D i E. Buildera jsem za čekání na
schválení sám chválil, takže **stojí právem**; zadal jsem mu práci, kterou
podle pravidel nesmí začít. Tady je to ve správném tvaru.

### Co se přidává

```
před  §2 (řádek 82):  atom ::= … | before(t1, t2) | within(t1, t2)   ← už deklarováno
teď   §5.1 uzávěry:   before*   tranzitivní uzávěr nad Time          ← CHYBÍ
```

`before` je v gramatice od začátku; chybí mu vyhodnocení. Bez něj nejde
zapsat ani položit otázku z dialogu D.

### Návrh: `before*` jako jádrový uzávěr, kalendář jako DATA

**(a) Uzávěr.** `before` je tranzitivní: `before(a,b) ∧ before(b,c) ⇒
before(a,c)`. Tranzitivní uzávěr nad sortem `Time` je **týž vzor jako
`within*`**, který v § 5.1 už je — žádný nový druh inference, jen další osa.

**(b) Kalendář se NEPROGRAMUJE.** § 12/6 zadání to říká přímo:

> *„Interní osa je abstraktní uspořádání; **kalendář je profil**
> («pondělí < úterý»)."*

Takže „pondělí je před úterým" je **deklarovaný fakt**, ne zabudovaná
znalost. Dialog D pak vypadá takhle a nic v kódu o dnech v týdnu neví:

```
! before(pondělí, úterý).                  ← profil, data s proveniencí
? alt{ before(kdy(r7), kdy(r8)),
       before(kdy(r8), kdy(r7)) }          → „Do Prahy."
```

**Soundness:** tranzitivita uspořádání, stejná vlastnost jako u `within*`.
**Terminace:** reflexivně‑tranzitivní uzávěr nad konečnou množinou
deklarovaných intervalů, tedy `≤ |V|²` kroků — táž mez, jakou má § 5.1 dnes.

### Dvě věci, které je potřeba rozhodnout spolu s tím

1. **Má se rozpor v uspořádání hlásit?** Odvodí‑li se `before(a,b)`
   i `before(b,a)`, je báze nekonzistentní. Nabízí se to řešit jako
   `disjoint`, tedy derivační formou na silnou negaci → `CONFLICT`
   s oběma důkazy. **Doporučuji ano** — mlčky přijatý cyklus v čase by
   byl přesně ten druh tiché nekonzistence, které systém jinde brání.
2. **Zůstává `during` a `překrývá` mimo?** § 3.6 zmiňuje čtyři predikáty
   (`před / po / během / překrývá`), § 2 gramatiky má jen `before`
   a `within`. **Doporučuji zůstat u dvou** — `po` je `before` obráceně
   a `během` je `within`; `překrývá` by potřeboval intervaly s koncovými
   body, což je větší věc a dialog D ji nepotřebuje.

### Rozsah po schválení

`P_BEFORE` + `before_of` v `ast.py`, `before_proof` v `closures.py`,
routování v `_match_kernel`, doplnění § 5.1 a § 13, **posun verze
0.1.4 → 0.1.5** s řádkem v tabulce změn.

**Bez tvého podpisu Builder na jádro nesahá** — a je to tak správně.

---

## 📜 DODATEK G — ZÁVAZNÉ: nejdřív dokončit, teprve pak další patro

**Rozhodl:** člověk (J.), 2026-08-14. **Status:** ZÁVAZNÉ.
*„Nejdřív perfektní funkčnost toho, co máme, pak další patro."*

**V3 rozřešení zmínek se ODKLÁDÁ.** Tím padá i Builderova otázka na aktivaci —
neřeší se, dokud není hotové to pod ní. Odložené zůstávají i měkká vrstva,
F0.5, AML a etapa 2 DIA.

### Měřitelné kritérium, ne dojem

„Perfektní funkčnost" má v zadání definici — § 10 vede jako metriku
**akceptační dialogy**: *„Úloha projde, když odpověď obsahuje správný
verdikt I správný důvod."* Stav pokrytí šesti dialogů z § 6.12:

| Dialog | Co ověřuje | Stav |
|---|---|---|
| **A** můstek a mez | `bound`, učení pravidla dialogem | ✅ pokryt |
| **B** co neplyne | `∃`-role nejmenuje svědka | ✅ pokryt |
| **C** sylogismus | řetěz `⊆` + disjunktnost → `N` | ✅ pokryt |
| **D** prostor a čas | obsažení míst **a pořadí na časové ose** | ❌ **CHYBÍ CELÝ** |
| **E** výjimka | `DIFF` místo nemonotónní logiky | ✅ pokryt |
| **F** vršení popisu | znalost se hromadí napříč tahy | ✅ pokryt |

**Hotovo znamená: projde všech šest.**

### Proč dialog D chybí — a je to nález, ne opomenutí

§ 2 verzované gramatiky **deklaruje atom, který jádro neumí vyhodnotit**:

```
řádek  82:  atom ::= … | contains(p, q) | before(t1, t2) | within(t1, t2)
řádek 218:  § 5.1 uzávěry:  within*  obsažení intervalů   ← before* CHYBÍ
řádek 670:  § 10 dialog D:  alt{ before(kdy(r7), kdy(r8)), … }
```

Ověřeno: `before_of` ani `P_BEFORE` v `ast.py` **neexistují**; je jen
`within_of` / `P_WITHIN`. Dialog D přitom potřebuje
*„Kam jel Petr dřív — do Prahy, nebo do Brna?"*, což je `alt` nad dvěma
`before`. Bez toho ho nejde ani zapsat — proto je jediný ze šesti bez testu.

Dokument tedy slibuje víc, než jádro umí, a to je přesně ta nesrovnalost,
kterou I‑13 hlídá.

### Co „dokončit" konkrétně obnáší

Pořadí je moje doporučení, závazný je jen rozsah.

1. **B‑8** — motivační případ § 5.2 (rozpracované).
2. **`before` a uspořádání časové osy** (§ 3.6, § 2, § 5.1) — odemkne
   dialog D. Pozor: je to **zásah do § 5.1**, tedy verzované jádro →
   posun verze a řádek v tabulce změn (I‑13).
3. **Dialog D jako akceptační test** — všechny tři otázky včetně poctivého
   `NEVÍM` u středy s vysloveným důvodem („trvání stavů neumím" — hranice v1).
4. **`GapFinder`** — dnes útržek, `Gap((query,))` jen vrací dotaz zpátky,
   takže § 6.8 („Proč nevíš?") **není splněný**. Otevřené podcíle z SLD,
   ne abduktivní minimalita.
5. **Napojit `Session` na orákulum a kaskádu** — všechny díly existují,
   nejsou spojené.
6. **Zlaté transkripty** s fixovaným rozborem přes keš.

Body 1–3 jsou o tom, aby dokumentace nelhala. Body 4–6 o tom, aby vrstvy,
které existují, spolu skutečně mluvily.

---

## 🚨 KOLO #15 — V2 kaskáda · jeden blocker

`pytest` **205 passed** (bylo 194) · `mypy --strict` čistý na 26 souborech ·
jádro 0.1.4 beze změny.

### B‑8 · Motivační případ § 5.2 kaskáda NEŘEŠÍ — a test tvrdí, že ano

Zadání § 5.2 staví celou kaskádu na jednom případu:

> *„Obsahuje citron vitamíny?" dostal od parseru rozbor **bez podmětu**
> (nominativ = akuzativ, oba nominály `obj`)."*

`generate()` to ve svém vlastním docstringu cituje. Ale záměna se generuje
**jen když podmět už existuje**:

```python
if subject is not None and obj is not None:   # cascade.py, generate()
```

Když parser podmět nedal, `subject is None` → **žádné alternativní čtení
nevznikne**. Naměřeno na doslovném vstupu ze zadání (oba nominály `obj`):

```
kandidátů: 1        (§ 5.2 čeká 2 — čtení A i B)
  obsahovat(co:citron, co:vitamín)   [rozbor parseru]
role výsledku: ['co', 'co']
má podmět?     None
```

Přeživší čtení má **dvě role téhož jména a žádný podmět**. Zeď z § 1
zadání (*„parser dostal rozbor bez podmětu"*) tím stojí dál.

**Downstream to nejde použít ani teoreticky.** Jádro duplicitní roli
odmítá:

```
atom("obsahovat", role("co", …), role("co", …))
  → SortError: atom 'obsahovat' má roli vícekrát: ['co', 'co']
```

V2 tedy vyrábí `Predication`, kterou V3 nikdy nepřevede na platný `Atom`.

### ⚠️ Test dává falešnou jistotu — komentář si protiřečí s daty

```python
# „Obsahuje citron vitamíny?" — parser nedal podmět, oba nominály jsou obj
LEMON = _reading(
    _token(1, "Obsahuje", "obsahovat", "VERB", 0, "root", …),
    _token(2, "citron",  "citron",  "NOUN", 1, "nsubj", …),   # ← nsubj, ne obj
    _token(3, "vitamíny","vitamín", "NOUN", 1, "obj",   …),
)
```

Komentář tvrdí „oba nominály jsou obj", fixture dává `citron` jako
**`nsubj`**. Test proto prochází, ale zkouší případ, kde parser podmět
**dal** — tedy přesně ten, který problém nemá. To je horší než chybějící
test: vypadá jako pokrytí § 5.2 a není jím.

**Oprava:** generovat záměnu i tehdy, když podmět chybí — z kandidátů na
podmět (nominály v `obj`/`nsubj`) sestavit dvojice `kdo`/`co` a nechat je
projít tvrdými patry. Pro dva nominály to jsou dvě čtení, `agreement_tier`
pak jedno zabije na shodě čísla, přesně jak § 5.2 popisuje. A `Predication`
by neměla duplicitní roli vůbec připustit — stejná kontrola jako v `Atom`
by tenhle stav zachytila při vzniku.

### Co jsem ověřil jako správné

| | |
|---|---|
| nerozhodnuto → **otázka**, ne favorit | dvě čtení → `question` vyplněná, `decided is None` ✓ |
| nerozebratelné → prázdno | `survivors=0`, `question=None`, žádný dohad ✓ |
| **spona není zvláštní větev** | jedno `_predicate_head`, lemma z `cop`, hlavou jmenná část ✓ |
| trace je součást výsledku | každé patro hlásí, co vyřadilo ✓ |
| `lexicon_tier` nerozhoduje | při víc kandidátech zapíše do trace a nechá doptání ✓ |

Rozdělení vrstev — **V2 vyrábí `Predication` se zmínkami, ne `Atom`** —
je správné a souhlasím s odůvodněním: zmínka je kotva s proveniencí (§ 3.2)
a převod na term je práce V3 s vlastní kaskádou.

### 🧩 Builderova otázka k V3 — odpovídám a předávám člověku

Ptá se, jestli má V3 postavit **bez patra aktivace** (backlog C‑1 neexistuje)
a nahlas to přiznat, nebo jestli se má nejdřív udělat měkká vrstva.

**Doporučuji stavět V3 bez aktivace a mez přiznat.** § 5.3 vede aktivaci
jako jedno patro z několika; rozhoduje skoro sama jen **u zájmen**. Jména,
částečné shody a určité popisy mají patra vlastní a fungují bez ní. V3 tedy
pokryje všechno kromě zájmen a elipsy — a ty stejně čekají na **etapu 2 DIA**,
která je za V3 v pořadí tak jako tak. Otočit pořadí by znamenalo postavit
měkkou vrstvu dřív, než bude na čem měřit, což je právě ten důvod, kvůli
kterému člověk v dodatku F rozhodl opačně.

**Rozhodnutí je na člověku** (mění pořadí milníků).

---

## ✅ KOLO #14 — B‑7 zavřen, žádný blocker

`pytest` **194 passed** (bylo 190) · `mypy --strict` čistý na 24 souborech ·
jádro 0.1.4 beze změny · regrese celá drží · LEX beze změny.

Ověřeno vlastními reprodukcemi:

```
keš přes RecordedOracle (zlatá cesta)  hits=1 misses=1 stored=1   ✓
selhání se nekešuje                    volání=2 hits=0 stored=0   ✓
bez provenience se nekešuje            volání=2 hits=0 stored=0   ✓
míchané provenience v nahrávce         OracleError                ✓
reálná cesta (UDPipe-like)             volání=1 hits=1            ✓
změna modelu invaliduje keš            hits=0 misses=2            ✓
```

**Oprava má lepší tvar, než jsem navrhoval.** Doporučoval jsem použít
`self._provenance()` pro zápis i čtení — to by odstranilo falešná minutí,
ale `RecordedOracle` atribut nemá, takže by se na zlaté cestě **nekešovalo
nikdy**. Builder místo toho udělal `provenance` **součástí smlouvy
`ParseOracle`**: kdo staví keš nebo zlatý transkript, musí umět zjistit
předem, z jakého modelu rozbory pocházejí. To je změna smlouvy, ne záplata
ve výpočtu klíče, a řeší to i případ, který můj návrh míjel.

**Vedlejší zisk:** `RecordedOracle` nově odmítne nahrávku míchající dvě
provenience. Zlatý transkript musí fixovat **jeden** rozbor — jinak není
čím poznat, že se model změnil. Lepší to říct při stavbě než po upgradu.

### ⚠️ Oprava mého tvrzení z kola #13

Napsal jsem, že na `hits`/`misses` **žádný test nesahá**. To bylo **chybné**.
V commitnuté verzi `test_oracle.py` na řádku 181 stálo:

```python
assert (cache.hits, cache.misses) == (1, 1)
```

Aserce existovala v `test_cache_is_keyed_by_provenance_too`; pokrývala jen
**funkční** cestu přes `UDPipeOracle`. Builderovo přeformulování poučení je
přesnější než moje: *„testuj počítadla pro každý druh orákula, který má keš
obsluhovat"*, ne „testuj počítadla".

---

## 🚨 KOLO #13 — orákulum a LEX · jeden blocker (VYŘEŠENO)

`pytest` **190 passed** (bylo 168) · `mypy --strict` čistý na **24** souborech ·
jádro 0.1.4 beze změny. Regrese „Co drží" celá drží.

**Všechny tři pasti F‑1 až F‑3 jsou zapracované správně** — ověřeno vlastními
reprodukcemi, viz níže. Zvlášť dobré je, že F‑2 se řešila **změnou tvaru API**
(`candidates()` vrací n‑tici), ne poznámkou v komentáři.

### B‑7 · `CachingOracle` míjí úspěchy a keší selhání

Keš zapisuje pod jiným klíčem, než pod jakým čte:

```python
# zápis  — provenience ze ČTENÍ
stamp = utterance.readings[0].provenance if utterance.readings else "?"
self._store[(stamp, text)] = utterance
# čtení  — provenience z OBJEKTU orákula
if cached_text == text and provenance == self._provenance():
```

`_provenance()` bere `getattr(self._inner, "provenance", None)`, jinak `"?"`.
`UDPipeOracle` si `Reading.provenance` nastavuje ze sebe, takže **na reálné
cestě se klíče shodují a keš funguje**. `RecordedOracle` ale `.provenance`
nemá. Naměřeno:

```
A) vnitřek MÁ .provenance (UDPipe)     → hits=1 misses=1     ✓ funguje
B) vnitřek .provenance NEMÁ (Recorded) → hits=0 misses=2     ✗ NIKDY netrefí
C) nerozebraná věta (prázdná čtení)    → hits=1              ✗ selhání SE keší
```

Chování je **přesně obrácené, než má být**: úspěšný rozbor se uloží a už se
nikdy nenajde (keš roste a neslouží), zatímco neúspěch — kde je stamp `"?"`
a `_provenance()` taky `"?"` — se trefí a drží natrvalo.

**Proč to vedu jako blocker.** Rozbitá je právě ta cesta, kvůli které keš
podle **dodatku D** vznikla: zlaté transkripty a hermetické testy jedou přes
`RecordedOracle`. Požadavek zněl, že transkript musí **fixovat rozbor**, aby
upgrade modelu nerozbil zlaté soubory — keš, která na téhle cestě nikdy
netrefí, tu práci nedělá. A **selhává tiše**: `hits`/`misses` existují, ale
žádný test na ně nesahá, takže je 190 zelených testů nechytilo.

**Oprava:** odvodit klíč zápisu i čtení **z téhož zdroje**. Nejčistší je
`self._provenance()` pro obojí a **nekešovat vůbec, když je provenience
neznámá** (`"?"`) — místo ukládání pod zástupný klíč. Tím zmizí i C.
Doporučuju k tomu test, který po druhém `parse` téhož textu tvrdí
`hits == 1`; přesně ten by nález chytil.

Drobnost k témuž místu: lookup je lineární průchod `self._store.items()`
místo `dict`ového přístupu. Dnes je to jedno (nula zásahů), po opravě to
bude na hot path.

### Co jsem ověřil jako správné

| | |
|---|---|
| **F‑3** dva různé signály | neznámý text → `OracleError`; nerozebraná věta → `readings=()`, `unambiguous=None` ✓ |
| `readings` je n‑tice od začátku | `tuple[Reading, ...]` — typ o pluralitě nelže ✓ |
| **F‑1** menu z jádra | 16 operací, **žádná** conBond3ová modalita; `GROUP_AND/OR/DIFF`, `FOR_ALL/EXISTS`, `MEMBER/SUBSET/DISJOINT/SAME_AS/COMPLETE`, `ALTERNATIVE` — nic nechybí ✓ |
| **F‑2** „nebo" nevybírá tiše | `ASSERTION → [GROUP_OR]`, `QUESTION → [ALTERNATIVE]`, `UNKNOWN → [GROUP_OR, ALTERNATIVE]` ✓ |
| nové cíle po F0.7 | `kromě/mimo/vyjma → GROUP_DIFF`, `a/i → GROUP_AND` ✓ |
| seed je hypotéza | všechny vzory `HYPOTHESIS`, nic potvrzené ✓ |
| hermetičnost | `test_oracle.py` 10 passed; žádné `urlopen`/`requests`/`socket` ✓ |
| klient selže při vytvoření | `__init__` volá `_handshake()`, ne až `parse()` ✓ |

Souhlasím i s tím, že V2/V3 **nezačal v témž tahu** — kaskáda má vlastní
návrhové otázky a improvizovat ji nad čerstvou vrstvou by bylo horší než
počkat.

---

## 🚨 Critical Blockers (starší)

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
