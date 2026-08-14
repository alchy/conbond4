# CORE SEMANTICS 0.1 — podklad: tři rozhodnutí před F0

**Status:** návrh k odsouhlasení. Není to Core Semantics 0.1 — je to text
tří rozhodnutí, bez kterých ji nemá smysl psát, protože každé z nich mění
gramatiku i akceptační sadu.
**Vztah k dokumentům:** doplňuje `ZADANI-CONBOND4.md` a „matematickou
kostru" (F0 v0.1). Kde se s kostrou rozchází, je to označeno.
**Konvence zápisu:** dle rozhodnutí J. (§ 3.7 zadání) — klíčová slova,
role a operace anglicky, lexikální materiál z dialogu česky v uvozovkách,
komentáře česky.

---

## 0 · Proč právě tyto tři

Kostra F0 v0.1 uzavírá pět otevřených věcí správně (rozštěpení `NOT`,
`complete(g)`, dvojí evaluator, sorty, statická validace). Zbývají tři,
které se v ní obcházejí — a každá z nich je taková, že když se rozhodne
až při implementaci, rozhodne se implicitně:

1. **Jaká je sémantika a co je doména.** Kostra míchá důkazovou
   sémantiku (§ 7), Kleeneho tabulky (§ 7) a prostor modelů (§ 16, § 18).
2. **Kvantifikátor na roli.** Bez něj se dialogy A a B navzájem vylučují.
3. **Rekurze.** Plošný zákaz (§ 9/5) zakazuje tranzitivitu `⊆`.

Vazba mezi nimi není náhodná: rozhodnutí 2 je bezpečné (nezavádí
skolemizaci ani nová individua) jen díky rozhodnutí 1, a rozhodnutí 1
je vyhodnotitelné jen díky uzávěrům z rozhodnutí 3.

---

## 1 · ROZHODNUTÍ 1 — sémantika, doména, UNA

### 1.1 Doména je otevřená

```
D  ⊇  { d | d je denotace pojmenované konstanty }
```

`D` **smí obsahovat individua, která báze nepojmenovává.** To je formální
obsah věty „extenze group je dolní odhad" (I‑11). Důsledky:

- `complete(g, source)` z kostry § 14 je nutný konstrukt, ne pohodlí:
  jen on zužuje `M(g)` na `K(g)`.
- Univerzální tvrzení se nikdy neověřuje projitím známých prvků
  (§ 6.3 zadání) — to je teď důsledek definice, ne disciplína.
- Uzavřený svět je **lokální ostrůvek**, viz `closed_context` (§ 5.3).

### 1.2 UNA neplatí globálně

Různá `id` mohou denotovat totéž individuum. To je vyžádané identitní
vrstvou (`e17` se může ukázat totožné s `e31`, I‑10) a má příjemný
vedlejší efekt: počítací otázky vycházejí poctivě samy od sebe.

```
a1, a2 ∈ group("auto"),  oba ve vztahu mít s e_filip
? „Kolik má Filip aut?"
→ „Znám dvě — pokud to není totéž auto dvakrát."
```

Rozlišenost vzniká **jen explicitně**:

```
neg_atom(equal(a1, a2)).          # „to je jiné auto"
distinct{e_petr, e_pavel, e_jana} # zkratka pro po dvou; jen v closed_context
```

> **Rozchod s kostrou:** § 13 mlčí, § 18 (enumerace modelů) UNA tiše
> předpokládá. Bez tohoto odstavce by orákulum bylo nekorektní.

### 1.3 Dotazovací jazyk je dvouvrstvý

Tohle je jádro rozhodnutí 1 a zdroj rozporu, který kostra měla.

**Objektová vrstva** — formule o světě, vyhodnocuje se **vyplýváním**:

```
member(t, g) · equal(t1, t2) · relation_atom(r) · comparator(v1, op, v2)
  a jejich konjunkce
```

**Epistemická vrstva** — operátory o tom, co je *doložitelné*;
vyhodnocují se nad derivací, ne nad modely:

```
K φ        „je doloženo, že φ"
K ¬φ       „je doloženo, že ne-φ"      (přes neg_atom, viz 1.4)
U φ        „ani jedno"                 ≡ ¬K φ ∧ ¬K ¬φ
A DIFF B   „prvky A, o kterých je doloženo, že nejsou v B"
enum(g)    „doložení členové g"
```

**Pravidlo, které rozpor odstraňuje:** přirozeně-jazyková spojka
v otázce se překládá do **epistemické** vrstvy, nikoli do objektové
disjunkce. Proto:

```
? „Je citron zelenina, nebo není?"
   ≠  member(citron, zelenina) OR neg_atom(member(citron, zelenina))   [objektově: platí vždy]
   =  K member(citron,zelenina)  ∨  K ¬member(citron,zelenina)         [epistemicky: U]
→ „Nevím."
```

Kleeneho tabulky z kostry § 7 tedy **platí — ale jen pro kombinaci už
spočtených verdiktů v epistemické vrstvě.** Na objektové spojky se
nevztahují. Tím zmizí rozpor s orákulem: tertium non datur je pravda
o modelech, ne o tom, co víme, a systém se na modely takhle nikdy neptá.

**Alternativní otázka** (§ 6.2 zadání) se stává explicitně epistemickou
a svědek z ní padá zadarmo:

```
? „Je citron ovoce, nebo zelenina?"
   alt{ member(citron,"ovoce"), member(citron,"zelenina") }
   právě jeden K ⇒ odpověz tím členem + jeho proof
   oba K ⇒ CONFLICT;  žádný ⇒ U
```

### 1.4 Věta, kterou musí referenční evaluator splňovat

Negace je **silná (explicitní)**: `neg_atom(p)` je samostatný predikát
`p̄`, ne klasické ¬. Báze proto zůstává definitní (Hornova) a má nejmenší
Herbrandův model.

> **Korektnost pozitivního fragmentu.** Je‑li KB množina definitních
> klauzulí a `φ` dotaz z pozitivního existenčního fragmentu, pak
> `KB ⊨ φ` právě tehdy, když `φ` platí v nejmenším Herbrandově modelu KB.

To je věta, o kterou se opírá § 11 kostry: **least‑closure evaluace je
korektní i úplná — na pozitivním fragmentu.** Mimo něj (DIFF, enum,
K‑operátory) se systém na vyplývání neptá, takže se s ní nedostane do
sporu. Tuhle dvojici — *co je vyplývání a kde už se neptáme* — považuju
za nejdůležitější větu celé Core Semantics.

**CONFLICT tím přestává být čtvrtou pravdivostní hodnotou.** Je to stav
dotazu: odvodí se `p` i `p̄`, koherenční constraint `p ∧ p̄ → ⊥` se poruší.
Tabulky zůstávají 3×3, CONFLICT se propaguje jako **anotace odpovědi**
s oběma důkazy. (Řeší bod „CONFLICT nemá kombinační tabulky".)

### 1.5 Modální dotazy = konzistence, ne enumerace

```
NUTNĚ φ     ≡  KB ⊨ φ                       (vyplývání)
MOŽNÁ φ     ≡  KB ∪ {φ} je konzistentní     (žádný constraint neporušen)
NEMOŽNÉ φ   ≡  KB ∪ {φ} je nekonzistentní
grounded    ≡  NUTNĚ, ne pouze MOŽNÁ        (guard z conBond3, I‑6)
```

Obojí je spočitatelné toutéž mašinerií (least closure + kontrola
constraintů), takže § 6.7 zadání nepotřebuje žádný druhý mechanismus a
prostor modelů se nikdy nekonstruuje. Odpověď „Nic, co vím, tomu
nebrání" je přesně `MOŽNÁ ∧ ¬NUTNĚ`.

### 1.6 Orákulum je asymetrické — a musí se tak používat

Hledání konečného protimodelu je **korektní pro vyvrácení** verdiktu,
nikdy pro jeho potvrzení:

```
systém řekl A, existuje model KB s ¬φ        → CHYBA v evaluátoru
systém řekl U, ve všech zkoumaných modelech φ → PODEZŘENÍ, ne důkaz
systém řekl A, protimodel se nenašel          → nic to nedokazuje
```

Testy „neodvození" (§ 22/15 kostry) jsou přesně ten směr, kde orákulum
funguje — což je dobře, protože je jich nejvíc. Potvrzení `A`/`N` dělá
proof objekt, ne orákulum.

### 1.7 Co rozhodnutí 1 zavírá

Body kritiky: tři sémantiky, nedefinované `D`, chybějící UNA, CONFLICT
bez tabulek, `DIFF` bez epistemické verze (viz též 2.3).

---

## 2 · ROZHODNUTÍ 2 — kvantifikátor na roli

### 2.1 Syntaxe a typování

```
term ::= … | relation(name; role1:q1 t1, …, rolek:qk tk)
q    ::= ∀ | ∃ | ·          # · = o group-uzlu samotném
```

Typové pravidlo:

```
τ(t) = Group[T]   ⇒  q ∈ {∀, ∃, ·}   (povinné, žádný default v jádru)
τ(t) = Entity     ⇒  q se nepíše     (ekvivalent ∃ nad singletonem)
```

**Pořadí rolí je kanonické a nese rozsah** — `∀x∃y` ≠ `∃y∀x`. Kanonické
pořadí je součást normalizace termu (I‑22).

### 2.2 Sémantika

Tvrzení s kvantifikovanými rolemi je formule s prefixem v kanonickém
pořadí rolí:

```
relation(name; r1:∀A, r2:∃B)   ≡   ∀x∈A ∃y∈B. name(r1:x, r2:y)
relation(name; r1:·A, r2:…)    ≡   tvrzení o uzlu A samotném
```

**Klíčové omezení, které drží rozhodnutelnost:** `∃`-role se **nikdy
neskolemizuje**. Existenční svědek se do grafu nezapisuje jako nový uzel;
tvrzení podporuje jen dotazy, které samy nesou `∃` na téže roli, nebo
dotazy s **doloženým svědkem**. Žádný chase, žádná nová individua,
materializace zůstává konečná. (Tohle je možné jen díky 1.1 — v otevřené
doméně nemusí mít svědek jméno.)

### 2.3 Odvozovací pravidla

```
D1  distribuce ∀ dolů:
      relation(n; r:∀A, …) ∧ subset*(B, A)  ⇒  relation(n; r:∀B, …)
      relation(n; r:∀A, …) ∧ member(x, A)   ⇒  relation(n; r:x,  …)

D2  ∃ se nedistribuuje dolů, jen nahoru:
      relation(n; r:∃B, …) ∧ subset*(B, C)  ⇒  relation(n; r:∃C, …)
      member(y, B) ⇏ relation(n; r:y, …)

D3  shoda dotazu s tvrzením (rozšíření ⪯ z kostry § 6):
      ∀-role tvrzení uspokojí ∀-dotaz nad podmnožinou i konkrétní prvek
      ∃-role tvrzení uspokojí pouze ∃-dotaz nad nadmnožinou
      hodnoty se párují přes uzávěry (subset*, contains*), ne rovností

D4  DIFF pod ∀:
      relation(n; r:∀(A DIFF B), …) se na x ∈ B nevztahuje
```

`DIFF` v D4 je epistemický (1.3): jistý je jen tam, kde je členství
v subtrahendu rozhodnuté pro každý prvek minuendu — tedy přes
`complete(B)` nebo `neg_atom(member(x,B))` pro každý uvažovaný `x`.
Extenze proto vrací **dvojici**:

```
eval_group(g) → ( certain: {…}, possible: {…} )     certain ⊆ possible
```

a výčtová odpověď rozliší „vím, že není" od „nevím, že je" (§ 6.4 zadání).

### 2.4 Proč to potřebují oba vlajkové dialogy — a dialog B dvakrát

```
# Dialog A  (musí projít distribuce)
relation("jezdit"; who:∀group_DP, via:∃group("dálnice")).
subset*(group("auto"), group_DP).
⇒ D1 ⇒ relation("jezdit"; who:∀group("auto"), via:∃group("dálnice"))
   — „auta jezdí po dálnici", pak teprve můstkové pravidlo

# Dialog B  (nesmí projít distribuce na členy cíle)
relation("obsahovat"; who:∀group("ovoce"), what:∃group("vitamín")).
member(e_citron, group("ovoce")).
⇒ D1 ⇒ relation("obsahovat"; who:e_citron, what:∃group("vitamín"))

? „Obsahuje citron vitamín C?"   what:e_c, e_c ∈ group("vitamín")
   D2/D3 ⇒ ∃-role neuspokojí konkrétní svědek        → U   ✓
? „Obsahuje citron nějaký vitamín?"   what:∃group("vitamín")
   D3 ⇒ ∃-dotaz na ∃-roli sedí                       → A   ✓
```

Druhá otázka dialogu B (řádek 961 zadání) je test, který kostra
v současné podobě **taky neprojde** — § 5 by ji zamítla spolu s první.
Per‑roli kvantifikace je tedy jediné místo, kde se obě odpovědi rozdělí
správně.

Bonus, dialog E se tím vyčistí:

```
relation("létat"; who:∀group("pták")).
# po konfliktu:
relation("létat"; who:∀(group("pták") DIFF group("tučňák"))).
```

### 2.5 Mez řečená nahlas: `∃∀` není v v1

Čtení „existuje jeden vitamín, který obsahuje všechno ovoce" (`∃` vně
`∀`) **není vyjádřitelné**. Pokus o jeho zápis se odmítne s důvodem, ne
tiše přeloží na `∀∃`. Je to čára, ne mezera — a je to důvod, proč nejsou
potřeba střídavé prefixy a s nimi Skolemova třída.

### 2.6 LEX defaulty a doptání

Jádro dodává uzavřené menu `{∀, ∃, ·}` (I‑15). Dialog se učí **jen to,
které čtení daná věta má**:

```
# LEX — návrhy, ne sémantika
reading "holý plurál v subjektu"  -> ∀      @hypothesis
reading "holý plurál v objektu"   -> ∃      @hypothesis

# DIA
state awaiting_quantifier(relation, role, candidates):
    ask "Mám to číst: {každý|některý} {group}?"
    answer -> attach_quantifier(relation, role)
```

Doptání se spouští, jen když je návrh nepotvrzený a rozdíl mění odpověď
na aktuální dotaz — jinak se čte podle vzoru s odkazem v provenienci.

### 2.7 Co rozhodnutí 2 zavírá

Rozpor dialogů A × B, druhá otázka dialogu B, nedefinované „hodnoty jsou
kompatibilní" v `⪯` (přes D3), `DIFF` bez epistemické verze (přes 2.3).

---

## 3 · ROZHODNUTÍ 3 — rekurze v jádru ano, v naučených pravidlech ne

### 3.1 Uzavřená sada jádrových uzávěrů

Implementované **jednou v interpretu**, verzované s gramatikou, nikdy
rozšiřitelné učením:

```
subset*      reflexivně-tranzitivní uzávěr subset            (Group)
member*      member(x,A) ∧ subset*(A,B) ⇒ member(x,B)        (E × Group)
contains*    reflexivně-tranzitivní uzávěr contains          (Place)
within*      obsažení intervalů                              (Time)
same_as*     reflex.-symetr.-tranzitivní uzávěr same_as      (pohled, viz 3.4)
distribute   D1/D2 z rozhodnutí 2
```

Pro evaluátor naučených pravidel jsou to **primitivní predikáty**
(stratum 0), ne uzly dependency grafu. Pravidlo `p3` tedy smí použít
`contains*`, aniž by vznikl cyklus.

### 3.2 Terminace

Každý uzávěr je monotónní, operuje nad konečnou množinou deklarovaných
uzlů a **negeneruje nová individua** (spolu s 2.2: ani `∃` je negeneruje).
Nejmenší pevný bod se dosáhne v ≤ |V|² krocích. Terminace je tedy
vlastnost konstrukce, nikoli slib — na rozdíl od formulace v § 3.7
zadání, kde totéž tvrdil zákaz rekurze.

### 3.3 Co zůstává zakázané v naučených pravidlech

Z § 9 kostry zůstává **všechno kromě restrikce 5**:

```
1. bezpečnost proměnných             ✔ zůstává
2. žádné generativní funkční symboly ✔ zůstává  ← skutečný zdroj rizika
3. konečná množina konstant          ✔ zůstává
4. konečná délka role-chain          ✔ zůstává
5. žádná rekurze                     ✘ RUŠÍ SE pro jádro, platí pro naučená
6. negace přes nižší stratum         ✔ zůstává
7. žádná volná proměnná v negaci     ✔ zůstává
8. omezená hloubka termů             ✔ zůstává
```

Zdůvodnění: Datalog se stratifikovanou negací nad konečnou doménou
terminuje a je v PTIME. Nerozhodnutelnost přináší vynález individuí
(restrikce 2 a existence v hlavě), ne cyklus v dependency grafu.
§ 10 kostry se tedy nemění, jen se aplikuje na graf **naučených**
pravidel s jádrovými uzávěry jako listy.

### 3.4 `same_as` je pohled, ne slévání

```
attach:   same_as(e17, e31) @hypothesis|confirmed     — jen hrana
eval:     1. z aktivních same_as hran se sestaví třídy ekvivalence
          2. kanonický zástupce = deterministicky nejnižší id
          3. dotaz i porovnávaná fakta se přečtou přes zástupce
          4. proof nese id použitých same_as hran
uložená fakta si ponechají svá původní resolved_id — nikdy se nepřepisují
revoke:   odebrání hrany změní jen příští pohled; není co opravovat
```

Tím padá scénář `A=B, B=C ⇒ A=C`, pak `revoke(B=C)`: nebyla uložena
žádná odvozená rovnost, takže se nic nesbírá zpátky. Řeší bod 6 kritiky
(„resolved view pouze pro konkrétní dotaz"), který se do kostry
nedostal, a je konzistentní s § 13 (historický fakt nedriftuje).

### 3.5 Co rozhodnutí 3 zavírá

Nemožnost tranzitivity `⊆` (dialogy C, D), `same_as` nepoužité
v evaluaci, terminace jako tvrzení místo důsledku.

---

## 4 · Dopad na akceptační sadu

K T1–T15 z kostry přibývá:

| ID  | Oblast              | Test                                              | Očekávání |
|-----|---------------------|---------------------------------------------------|-----------|
| T16 | ∀-distribuce        | dialog A, krok `auto ⊆ DP`                        | A + proof (D1) |
| T17 | ∃-nedistribuce      | dialog B, „vitamín C"                             | U |
| T18 | ∃-dotaz             | dialog B, „nějaký vitamín"                        | A + proof (D3) |
| T19 | mez výrazivosti     | pokus o `∃∀` čtení                                | odmítnuto s důvodem |
| T20 | uzávěr `⊆`          | Praha ⊆ Česko ⊆ Evropa, dotaz na Evropu           | A, hloubka 3 |
| T21 | `same_as` pohled    | A=B, B=C, dotaz; pak revoke(B=C), týž dotaz       | A → U, žádný uložený fakt změněn |
| T22 | bez UNA             | a1, a2 bez `distinct`, „kolik aut?"               | „dvě, pokud nejsou totéž" |
| T23 | epistemická vrstva  | „je citron zelenina, nebo není?"                  | U (ne A) |
| T24 | modalita            | `MOŽNÁ` bez constraintu × `NEMOŽNÉ` s ním         | MOŽNÁ ¬grounded / NEMOŽNÉ |
| T25 | orákulum            | protimodel k verdiktu A                           | test selže (evaluator má chybu) |
| T26 | CONFLICT anotace    | `p` i `p̄` odvozeno                                | verdikt + oba proofy, tabulky beze změny |

T19, T22, T23 jsou **negativní testy na výrazivost a poctivost** — právě
ty, které v kostře chyběly úplně.

## 5 · Co zůstává otevřené i po těchto třech

Vědomě neřešeno, k rozhodnutí zvlášť:

1. **`closed_context`** — uzavřený ostrůvek pro úlohy § 6.9 (potřebuje
   `complete` + UNA + kardinalitní menu `EXACTLY_ONE / AT_MOST_ONE /
   AT_LEAST_ONE / ALL_DIFFERENT`). Doporučuju odložit za F0 a napsat proč.
2. **`Proof` × `Gap`** — oddělené typy; `missing(premise)` nepatří do
   gramatiky důkazu.
3. **Dvojí režim evaluace** — bottom-up pro uzávěr, top-down (SLD) pro
   „co chybí"; bez druhého nelze naplnit § 6.8 zadání.
4. **Kanonický výběr důkazu** — `normalize_proof(A) == normalize_proof(B)`
   z § 18 kostry vyžaduje deterministické pravidlo volby mezi několika
   minimálními důkazy.
5. **`attach` smí selhat** — typová chyba, překročení hloubky; čtyřoperační
   rozhraní ze zadání selhání nezná.
