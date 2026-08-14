# conBond4 — Core Semantics 0.1

**Verze jádra:** 0.1.4 · 14. 8. 2026
**Status:** návrh finálního znění formálního jádra. Verzované; změna
gramatiky nebo evaluace jen vědomým rozhodnutím (I‑13, I‑16).

| Verze | Změna | Schváleno |
|---|---|---|
| 0.1.0 | výchozí znění | 13. 8. 2026 |
| 0.1.1 | § 7 — třístupňový `canonical_key`; listy jsou fakta i pravidla | 14. 8. 2026 |
| 0.1.2 | § 5.1 — kontrapozice `member̄*` přes `subset*`; § 13 T32–T34 | 14. 8. 2026 |
| 0.1.3 | § 5.1 — uzávěr `complete*` (`U → N`); § 5.4 — scelení identity je odmítnutelné, pořadí těla; § 13 T35–T39 | 14. 8. 2026 |
| 0.1.4 | § 2 — konstruktory `AND` / `OR` / `DIFF` jako termy; § 5.2.1 — distribuce `D1`/`D2` nad algebraickými termy; § 13 T40–T44 | 14. 8. 2026 |
**Rozsah:** definuje jazyk, typování, denotaci, epistemický status,
pravidla, modalitu, důkaz a identitu. Neřeší parsing, renderování,
vnitřek doménových specialistů ani optimalizace.
**Předchůdci:** `ZADANI-CONBOND4.md`, matematická kostra F0 v0.1,
`CORE-SEMANTICS-0.1-PODKLAD.md` (tři rozhodnutí).
**Konvence:** klíčová slova a role anglicky, lexikální materiál
z dialogu česky v uvozovkách, komentáře česky (rozhodnutí J.).

---

## 0 · Tři věty, na kterých stojí zbytek

1. **Doména je otevřená, UNA neplatí.** Model smí obsahovat individua,
   která báze nepojmenovává; různá `id` mohou denotovat totéž.
2. **Individua vytváří jen člověk tahem dialogu.** `attach` smí založit
   uzel; **evaluace nikdy**. Proto je nejmenší pevný bod konečný a
   terminace je vlastnost konstrukce, ne slib.
3. **Objektová vrstva se ptá na vyplývání, epistemická na doložitelnost.**
   Přirozeně‑jazyková spojka v otázce jde vždy do epistemické vrstvy.

---

## 1 · Sorty a typování

```
E   Entity              jednotlivina
G   Group[T]            množina termů sortu T
R   RelationInstance    reifikovaná instance vztahu
P   Place               místo
T   Time                bod/interval na časové ose
V   Value[q]            hodnota veličiny q (s jednotkou)
C   Constraint
X   proměnná (jen v pravidlech)
```

`Place` a `Time` jsou vlastní sorty, **ne podtypy Group** — „Praha ⊆
Česko" není podmnožina, ale `contains*`. (Odděleno záměrně: hranice,
překryvy a části území nejsou množinové operace.)

Typová pravidla:

```
member(x, g)          τ(g) = Group[T],  τ(x) = T
subset(a, b)          τ(a) = τ(b) = Group[T]
contains(p, q)        τ(p) = τ(q) = Place
role filler = Group   ⇒ povinný kvantifikátor q ∈ {∀, ∃, ·}
role filler ≠ Group   ⇒ kvantifikátor se nepíše
comparator(v1,op,v2)  τ(v1) = τ(v2) = Value[q]  — táž osa, jinak typová chyba
```

**Žádné implicitní přetypování.** `RelationType` není samostatný sort:
typ vztahu je `Group[RelationInstance]`, čímž na něj platí táž algebra.

---

## 2 · Syntaxe

```
term ::= entity(id)
       | group{t1, …, tn}
       | group[x | φ(x)]
       | relation(name; role1:q1 t1, …, rolek:qk tk)
       | restriction(t; role:t)
       | t AND t | t OR t | t DIFF t

q    ::= ∀ | ∃ | ·

atom ::= member(t, g) | subset(a, b) | equal(t1, t2)
       | contains(p, q) | before(t1, t2) | within(t1, t2)
       | comparator(v1, op, v2)
       | role(r, name, t)            # konkrétní filler
       | role_q(r, name, q, g)       # kvantifikovaný filler
       | rel_atom(name; role:t, …)

lit  ::= atom | neg_atom(atom)

φ    ::= lit | φ AND φ                       # objektová vrstva, jen konjunkce

query ::= φ                                   # vyplývání
        | K φ | U φ                           # epistemická vrstva
        | alt{ φ1, …, φn }                    # alternativní otázka
        | enum(g) | count(g)
        | modal(MUST|MAYBE|IMPOSSIBLE, φ)
        | bound(r, quantity, op)              # „jak rychle nejvýš…"

rule       ::= head <- lit1 AND … AND litn
constraint ::= body -> ⊥ | disjoint(a, b) | body -> bound(op, value)
```

Pozn.: `role(r, name, t)` je **predikát, ne funkce**. Funkční zápis
`via(r)` z kostry porušuje její vlastní restrikci „žádné funkční
symboly"; predikátový tvar zachovává Hornovu bezpečnost.

`op ∈ { < , ≤ , = , ≥ , > , ≠ }` — uzavřené menu (I‑15). Dialog učí
jen mapování slova na komparátor, nikdy nový komparátor.

---

## 3 · Denotace a evaluace

### 3.1 Dvojí extenze

Každá group má **skutečnou** a **známou** extenzi:

```
K(g) ⊆ M(g)          obecně bez rovnosti
complete(g, source)  ⇒  K(g) = M(g)
```

Evaluace vrací dvojici, ne množinu:

```
eval_group(g) → ( certain, possible )        certain ⊆ possible
```

### 3.2 Algebra

```
⟦group{a,…}⟧      certain = {a,…}                     possible = {a,…}
⟦A AND B⟧         certain(A) ∩ certain(B)             possible(A) ∩ possible(B)
⟦A OR B⟧          certain(A) ∪ certain(B)             possible(A) ∪ possible(B)
⟦A DIFF B⟧        certain(A) \ possible(B)            possible(A) \ certain(B)
⟦group[x | φ]⟧    { d | K φ(d) }                      { d | ¬K ¬φ(d) }
⟦restriction(t;r:s)⟧  filtr instancí přes role, hodnoty párovány dle 3.3
```

`DIFF` je tím epistemický: prvek je *jistě* v rozdílu, jen když je
doloženo, že v subtrahendu není. Bez `complete(B)` nebo `neg_atom` na
konkrétní prvek zůstává jen v `possible` — a odpověď to musí říct
(I‑11): „vím, že není" × „nevím, že je".

### 3.3 Shoda vztahu s dotazem

```
q ⪯ r   ⟺   name(q) = name(r)
            ∧ ∀ role ∈ q:  filler_q(role) ⊑ filler_r(role)
```

kde `⊑` **není rovnost**, ale párování přes jádrové uzávěry:

```
konkrétní × konkrétní   equal nebo same_as*
konkrétní × Place       contains*(dotaz, fakt)      „kam ⊆ Česko" ⊑ „kam:Praha"
konkrétní × Time        within*(fakt, dotaz)
konkrétní × Group       member*(fakt, dotaz)
∃G × ∃H                 subset*(H, G)               ∃ jde jen nahoru
∀G × ∀H                 subset*(G, H)               ∀ jde jen dolů
konkrétní × ∃G          NEsedí                      ← dialog B
```

Role navíc v `r` nevadí (§ 3.4 zadání). Každý použitý krok uzávěru je
hrana v důkazu, ne skrytá normalizace.

---

## 4 · Epistemický status

```
A  (ANO)     existuje důkaz φ
N  (NE)      existuje důkaz neg_atom(φ)
U  (NEVÍM)   ani jedno
```

**CONFLICT není čtvrtá pravdivostní hodnota.** Je to stav dotazu:
odvodí se `p` i `p̄` a poruší se koherenční constraint `p ∧ p̄ → ⊥`.
Nese se jako anotace odpovědi s oběma důkazy; tabulky zůstávají 3×3.

Kombinace platí **jen v epistemické vrstvě**, nad už spočtenými verdikty
(silná Kleeneho logika):

```
AND    A  U  N          OR     A  U  N
  A    A  U  N            A    A  A  A
  U    U  U  N            U    A  U  U
  N    N  N  N            N    A  U  N
```

Objektové spojky se takto **nevyhodnocují**. Otázka „Je citron zelenina,
nebo není?" je `K φ ∨ K ¬φ` = `U`, nikoli objektová tautologie.

**Věta o korektnosti (pozitivní fragment).** Je‑li báze množina
definitních klauzulí (negace je silná — `neg_atom(p)` je samostatný
predikát `p̄`) a dotaz z pozitivního existenčního fragmentu, pak
`KB ⊨ φ` právě tehdy, když `φ` platí v nejmenším Herbrandově modelu.
Least‑closure evaluace je tam tedy korektní i úplná. Mimo tento fragment
se systém na vyplývání neptá.

**Absence není negace** (I‑21): `N` vzniká výhradně z explicitního
`neg_atom`, z **derivační formy constraintu** (§ 5.3) nebo z doloženého
protipříkladu.

---

## 5 · Pravidla, uzávěry, constrainty

### 5.1 Jádrové uzávěry — jediné místo s rekurzí

Implementované jednou v interpretu, neroszšiřitelné učením:

```
subset*    reflex.-tranz. uzávěr subset                    Group
member*    member(x,A) ∧ subset*(A,B) ⇒ member(x,B)        E × Group
member̄*    member̄(x,B) ∧ subset*(A,B) ⇒ member̄(x,A)        E × Group
contains*  reflex.-tranz. uzávěr contains                  Place
within*    obsažení intervalů                              Time
same_as*   reflex.-symetr.-tranz. uzávěr (jen pohled, § 8) E
distribute D1/D2 (§ 5.2)
```

Pro naučená pravidla jsou to **primitivní predikáty stratu 0**, ne uzly
dependency grafu. Monotónní, nad konečnou množinou uzlů, negenerující —
pevný bod v ≤ |V|² krocích.

**Kontrapozice `member̄*`** *(doplněno 14. 8. 2026)*. Silná negace se šíří
po hierarchii tříd DOLŮ: z `A ⊆ B` plyne `B̄ ⊆ Ā`, takže „Hrabal není
stroj" implikuje „Hrabal není parní stroj". Bez ní by systém na dotaz po
podtřídě vracel `U`, přestože subjekt už byl z nadtřídy vyloučen —
sémantická úplnost silné negace nad hierarchií skupin by zůstala
poloviční a dialog C by na podtřídě zhavaroval.

Tři vlastnosti, které z toho plynou a nesmí se ztratit:

1. **Směr je nesymetrický.** Premisa mluví o nadmnožině, závěr o
   podmnožině. Opačné čtení („není parní stroj ⇒ není stroj") je
   nekorektní.
2. **Saturuje se uvnitř pevného bodu, ne nad základními fakty.** Premisa
   typicky v bázi vůbec není — `member̄(x,B)` vzniká až derivační formou
   constraintu (§ 5.3), tedy pravidlem. Uzávěr postavený jen nad
   deklarovanými fakty by se na vlajkovém případu nespustil. Z téhož
   důvodu zůstává `member̄` uzlem dependency grafu, ne listem stratu 0:
   na rozdíl od `member` ho naučená pravidla **produkují**.
3. **Zvyšuje počet dosažitelných stavů `CONFLICT`** — báze, která tvrdí
   členství v podtřídě vyloučené třídy, je nekonzistentní a nově to
   ohlásí. Je to správný důsledek úplnějšího uzávěru; oslabit uzávěr
   kvůli tomu by znamenalo vrátit se k tichému nesouladu.

Čtení přes třídy ekvivalence `same_as*` platí i tady, stejně jako
u `member*`.

**Uzávěr `complete*`** *(doplněno 14. 8. 2026)*:

```
complete*   complete(g) ∧ x ∉ certain(g) ⇒ member̄(x, g)
```

Bez něj je `complete(g)` deklarace bez důsledku a uzavření světa nemá
v systému žádnou páku (§ 3.1: `K(g) = M(g)`).

**Je to jediné místo v jádře, kde závěr plyne z ABSENCE.** Všechno ostatní
drží I‑21 („absence není negace"); tohle je vědomá výjimka a musí být
ohrazená dvěma způsoby:

1. **Vyhodnocuje se až při dotazu, nikdy se nematerializuje do pevného
   bodu.** Uvnitř evaluační smyčky by se `member̄(x,g)` odvodilo
   z neúplného stavu — a pravidlo, které doběhne později, může `member(x,g)`
   teprve vyrobit. Vznikl by `p` i `p̄`, tedy falešný `CONFLICT`, a pevný
   bod by přestal být monotónní. Takhle nemůže uzávěr nic zpětně
   zneplatnit a nevzniká nové stratum.
2. **Nesmí popřít doložený prvek.** Je‑li `member*(x,g)`, uzávěr mlčí.

Skládá se s kontrapozicí: uzavření nadskupiny uzavře i podskupiny
(`x ∉ g` a `A ⊆ g` dává `x ∉ A`). Čte se přes `same_as*` jako `member*`.

### 5.2 Distribuce kvantifikovaných rolí

```
D1  relation(n; r:∀A, …) ∧ subset*(B,A)  ⇒  relation(n; r:∀B, …)
    relation(n; r:∀A, …) ∧ member*(x,A)  ⇒  relation(n; r:x,  …)
D2  relation(n; r:∃B, …) ∧ subset*(B,C)  ⇒  relation(n; r:∃C, …)
    member(y,B) ⇏ relation(n; r:y, …)
```

`∃` se **nikdy neskolemizuje** — svědek se do grafu nezapíše. To je
možné jen díky otevřené doméně (§ 0/1) a je to důvod, proč nevzniká
chase a proč není potřeba střídavý prefix.

**Mez:** čtení `∃∀` („existuje jeden vitamín, který obsahuje všechno
ovoce") není vyjádřitelné a odmítá se s důvodem. Čára, ne mezera.

### 5.2.1 Distribuce nad algebraickými termy

*(schváleno člověkem 14. 8. 2026 podle I‑13; jádro v0.1.4)*

**Nepřidává se žádné nové distribuční pravidlo.** `D1` a `D2`
zůstávají doslova, jak jsou; rozšíří se jen **doména dvou uzávěrů**, na
které se odvolávají:

**(a) `member*` nad algebraickým termem** — odvozovací pravidla, tedy
implikace **jen zprava doleva**:

```
member*(x, A AND B)   ⟸  member*(x,A) ∧ member*(x,B)
member*(x, A OR  B)   ⟸  member*(x,A) ∨ member*(x,B)
member*(x, A DIFF B)  ⟸  member*(x,A) ∧ „doloženo, že x ∉ B"
```

Směr šipky je podstatný, ne kosmetický. Ekvivalence by u `OR` znamenala,
že z členství ve sjednocení plyne členství v některém členu — a to je
právě zákaz z dialogu A: **z disjunkce se nesmí tiše vybrat člen.**

Disjunktivní členství **je legitimní vstup a je připojitelné**: jakmile je
`A OR B` platný term, je `member(x, A OR B)` dobře utvořený fakt a nic
nebrání ho zapsat. Z uloženého `member(x, A OR B)` ale **neplyne
`member(x,A)` ani `member(x,B)`** — obojí je `U`, dokud to nedoloží něco
dalšího.

U `AND` a `DIFF` se opačný směr **neztrácí**, jen se bere odjinud: zákony
`A AND B ⊆ A` a `A DIFF B ⊆ A` z bodu (b) dají `member(x, A AND B) ⇒
member(x, A)` přes běžné `member*`. Nesoundní je tedy jen eliminace `OR`,
a tu návrh neobsahuje.

Třetí řádek je klíčový a je to táž disciplína jako u `query_diff`:
`x ∉ possible(B)`, ne `x ∉ certain(B)`. Slabší varianta by tvrdila
„prokazatelně nepatří" z pouhé nevědomosti (I‑21).

**(b) `subset*` nad algebraickým termem** se rozšíří o uzavřenou sadu
monotonních zákonů:

```
A AND B  ⊆ A          A AND B ⊆ B
A        ⊆ A OR B     B       ⊆ A OR B
A DIFF B ⊆ A
X ⊆ A  ⇒  X ⊆ A OR B          A ⊆ Y  ⇒  A AND B ⊆ Y
X ⊆ A  ∧  X ⊆ B  ⇒  X ⊆ A AND B
X ⊆ A  ∧  disjoint(X, B)  ⇒  X ⊆ A DIFF B
```

Poslední řádek dělá sadu symetrickou pro entitní i druhovou reprezentaci:
`member*` má pravidlo pro `DIFF` a `subset*` nově taky. Bez něj by
„vrabec je pták kromě tučňáka" nešlo doložit na úrovni tříd, jen po
jednotlivcích.

**`disjoint` se hledá v OBOU směrech.** Marker je v bázi uložený
jednosměrně (`disjoint(a:g1, b:g2)`), ale relace symetrická je — jinak by
závěr závisel na pořadí, ve kterém člověk oddělenost vyslovil.

**Přijatá neúplnost.** Zákon se ptá na doložený marker, ne na odvozenou
oddělenost. Tranzitivní tvary (`X ⊆ C ∧ disjoint(C,B)`, resp.
`disjoint(X,C) ∧ B ⊆ C`) marker v bázi nemají, takže vyjdou `U` —
bezpečná strana, konzistentní se záměrnou neúplností celé sady.

**Zákony jsou CÍLENÉ, ne dopředné.** Používají se výhradně k zodpovězení
dotazu `X ⊆ Y` a rekurze jde po **struktuře porovnávaných termů**, ne po
bázi. Dopředné řetězení by nebylo možné: `X ⊆ A ⇒ X ⊆ A OR B` má na pravé
straně volné `B`, takže by generovalo neomezeně. Cílené použití je
konečné, protože každý krok sestoupí do podtermu. Je to rozdíl mezi
terminací a jejím opakem, ne stylistická poznámka.

**Sada je záměrně neúplná** — neprokáže každou platnou inkluzi. Je to
bezpečná strana: chybějící důkaz dá `U`, nikdy falešné `A`. Úplnost by
znamenala rozhodovací proceduru nad celou algebrou; ta je díky § 6.3
možná, ale je to samostatné rozhodnutí, ne vedlejší efekt této změny.

**Co z návrhu plyne pro dialog E.** Po zavedení konstruktorů odpoví
systém na „Létá vrabec?" **`U`, ne `A`**, dokud báze nedoloží, že vrabec
není tučňák — `certain(pták DIFF tučňák) = certain(pták) \ possible(tučňák)`
a vrabec v `possible(tučňák)` je. Je to **správné chování**, ne vada:
oslabit `DIFF` na `certain(A) \ certain(B)` by z nevědomosti udělalo
tvrzení. Dialog proto musí oddělenost doložit (`disjoint(vrabec, tučňák)`).

### 5.3 Constrainty mají derivační formu, ne jen kontrolní

Kontrolní tvar `body -> ⊥` umí jen ohlásit konflikt — nikdy z něj
nevznikne verdikt `N`. Proto každý constraint disjunktnosti a
neslučitelnosti **expanduje jádro na dvojici pravidel se silnou negací**:

```
disjoint(A, B)  ⇒  neg_atom(member(x,B)) <- member*(x,A)
                   neg_atom(member(x,A)) <- member*(x,B)

incompatible(u, v)  na ose q  ⇒
                   neg_atom(measure(r,q,v)) <- measure(r,q,u)
```

Bez toho nelze odvodit „Hrabal není stroj" (dialog C) ani „Petr nejede
pomalu" (T6) — obojí akceptační sada vyžaduje jako `N`.

### 5.4 Naučená pravidla — bezpečný fragment

```
head <- lit1 AND … AND litn
```

1. každá proměnná v hlavě bezpečně vázaná v pozitivním těle;
2. **žádné funkční symboly a žádná existence v hlavě** (skutečný zdroj
   nerozhodnutelnosti);
3. konečná množina konstant;
4. omezená délka role‑chain;
5. **nerekurzivní** — pozitivní dependency graf naučených pravidel
   acyklický (jádrové uzávěry jsou listy, ne uzly);
6. negace jen přes nižší stratum;
7. žádná volná proměnná pod negací;
8. omezená hloubka termů a vnoření vztahů (parametr gramatiky, default 1).

Validace probíhá při `attach`; nevyhovující program se **odmítne**, ne
„zkusí vyhodnotit". Hrany dependency grafu se stavějí **unifikací**, ne
rovností klíčů uzlů: literál v těle závisí na každém pravidle, jehož
hlava by ho mohla splnit, a proměnná v roli se snoubí s libovolnou
konstantou. Rovnost klíčů by z proměnné udělala samostatný uzel a
rekurze schovaná za proměnnou by prošla validací.

**Scelení identity je odmítnutelná operace** *(rozhodnuto 14. 8. 2026)*.
Konstanty se v unifikaci porovnávají **přes aktuální třídy ekvivalence**,
ne syntakticky, a `attach(same_as)` proto validuje pravidla proti
navrženým třídám ještě před zápisem — dvě dosud různé konstanty se
scelením stanou jednou a hrana, která do té chvíle nevznikla, vzniknout
může. `attach(same_as)` tím smí selhat `CycleDetected`; odmítnutá hrana
se do báze nezapíše. Samotné zopakování validace by nestačilo: bez
kanonizace v `_unifies` by se pořád porovnávala syrová id a mez by
zůstala tam, kde byla.

**Pořadí literálů v těle není lhostejné** *(14. 8. 2026)*. Jádrový
predikát v těle vyžaduje, aby **obě** jeho role byly vázané v okamžiku,
kdy na ně dojde řada — enumerace nad uzávěry ve F0 není (§ 5.1).
`subset(L2, L1)` se dvěma dosud nevázanými proměnnými skončí chybou.
Tělo se proto musí uspořádat tak, aby jádrové literály přišly až po
navázání svých rolí:

```
tělo (alergie_na, subset, obsahuje)   → EvaluationError
tělo (alergie_na, obsahuje, subset)   → N, důkaz v pořádku
```

V deklarativním čtení Hornovy klauzule je pořadí konjunktů lhostejné, tady
lhostejné není — autor pravidla musí znát vyhodnocovací strategii. Selhává
to **hlasitě, ne tiše** (I‑1). Automatické přeuspořádání těla při `attach`
je vedeno jako samostatný úkol, ne jako součást bezpečného fragmentu.

### 5.5 Evaluace

```
K0    = aktivní explicitní fakta
K(i+1)= K(i) ∪ Consequences(jádrové uzávěry ∪ naučená pravidla, K(i))
K*    = nejmenší pevný bod
```

Bottom‑up pro uzávěr a verdikty. Top‑down (SLD) běží jako oddělený
modul `GapFinder` pro dotaz „Proč nevíš?" — vrací otevřené podcíle, ne
důkaz (§ 7).

---

## 6 · Modalita a veličiny

```
MUST φ        ≡  KB ⊨ φ
MAYBE φ       ≡  KB ∪ {φ} konzistentní (žádný constraint porušen)
IMPOSSIBLE φ  ≡  KB ∪ {φ} nekonzistentní
grounded      ≡  MUST, ne pouze MAYBE
```

Prostor modelů se nikdy nekonstruuje — obojí je konzistenční kontrola
nad toutéž mašinerií. „Nic, co vím, tomu nebrání" = `MAYBE ∧ ¬MUST`.

**Bound query** — čtvrtý druh dotazu, odpovědí je mez, ne verdikt:

```
bound(r, q, ≤)  =  inf { V | KB ⊨ measure(r,q) ≤ V }
```

Nutný pro „Jak rychle může jezdit auto po dálnici?" (dialog A). Ani
zadání, ani kostra ho neměly; bez něj nemá vlajkový dialog odpověď
svého typu.

**Dobrá definovanost.** Infimum nad `V` je nad nekonečnou množinou
hodnot osy, tedy nespočitatelné enumerací. Evaluovatelné je proto, že
**v1 nemá aritmetiku** (§ 11 zadání): žádné pravidlo neumí vyrobit
hodnotu, která v bázi není. Odvoditelné meze jsou tedy podmnožinou
konečné množiny literálů vyskytujících se v aktivních výrocích a platí:

```
bound(r,q,≤)  =  min { V ∈ literals(KB, q) | KB ⊨ measure(r,q) ≤ V }
Proof         =  důkaz právě té meze, na které se minimum nabývá
```

Zákaz aritmetiky tedy není jen zúžení rozsahu — je to podmínka
evaluovatelnosti `bound`. Jakmile by v1 uměla převádět jednotky nebo
počítat s hodnotami, `bound` přestane být minimem nad konečnou množinou
a stane se optimalizační úlohou nad osou. To je hranice, kterou je
potřeba hlídat spolu s ostatními (I‑13).

Veličiny obsluhují specialisté za jednotnou smlouvou (`normalize`,
`compare`, `named_interval`, `render`). Specialista dodává **jen
primitivní predikáty své osy** a nesmí přidat druh inference.

---

## 7 · Důkaz a mezera

```
Proof ::= fact(id)
        | rule(rule_id, Proof…)
        | closure(kind, Proof…)          # subset*, contains*, same_as*, …
        | distribute(D1|D2, Proof)
        | witness(element, Proof)
        | constraint(id, Proof…)
        | countermodel(fragment)

Gap   ::= open_goal(atom) | alternatives(Gap…)
```

`Proof` **jen** pro `A`/`N`. `U` nese `Gap` — otevřené podcíle z SLD,
nikdy „důkaz s chybějící premisou" (to by rozbilo minimalitu).

Listy jsou **fakta i pravidla**: uzel `rule` se do množiny započítá a
zároveň se sestoupí do jeho premis. Jinak by vysvětlení („seznam id výroků,
které se použily", § 3.7/1 zadání) zamlčelo fakta pod pravidlem.

Minimalita: `P` je minimální, když žádná vlastní podmnožina jeho listů
verdikt neodvodí. Minimálních důkazů může být víc; **kanonický** je
minimum podle třístupňového klíče:

```
canonical_key(P) = ( |listy(P)| , seřazená n-tice id listů , velikost stromu )
```

Pořadí stupňů není libovolné. Kdyby rozhodovalo jen lexikografické pořadí
id, vyhrával by důkaz s nižšími id bez ohledu na délku — „citron je citron
a citron je ovoce" by porazilo „citron je ovoce", pokud se přímý fakt
připojil později. To je právnicky platné a lidsky absurdní; první stupeň
proto vynucuje **princip minimálního vysvětlení**, druhý a třetí drží
determinismus. Žádný stupeň nezávisí na pořadí průchodu pamětí, takže
I‑13 platí a `normalize_proof(reference) == normalize_proof(production)`
zůstává v platnosti.

*(Zjemnění klíče schváleno 14. 8. 2026; předchozí znění mělo jen stupně
2 a 3.)*

Vysvětlení se renderuje **výhradně z kanonického důkazu** (I‑14).
Aktivace, spoluvýskyt, skóre a podobnost nesmí být uzlem `Proof` —
jejich role končí u výběru a řazení kandidátů.

---

## 8 · Identita

```
mention m                         úsek promluvy s proveniencí
assign(m, e, hypothesis|confirmed|revoked)
same_as(e1, e2, hypothesis|confirmed)
```

Fakt ukládá **resolved id** a `source_mention`. Referent nedriftuje:
určitý popis se rozřeší při `attach` a do faktu se uloží výsledek, ne
popis.

`same_as` je **pohled, ne slévání**:

```
eval:  1. z aktivních same_as hran se sestaví třídy ekvivalence
       2. kanonický zástupce = nejnižší id (deterministicky)
       3. dotaz i porovnávaná fakta se čtou přes zástupce
       4. použité hrany jsou uzly Proof
revoke: mění jen příští pohled — žádná odvozená rovnost nebyla uložena
```

Oprava identity = `revoke` + `attach` s důvodem; historie zůstává.
Bez UNA vychází počítání poctivě samo: `count(g)` vrací počet tříd
ekvivalence známých svědků s doložkou „pokud nejsou totéž".

---

## 9 · Rozhraní

```
attach(výrok)    → id | Error      jediný zápis; rozřeší popisy, validuje
revoke(id, důvod)→ ok              jediné mazání; hrana zůstává v historii
eval(query)      → verdikt + Proof | Gap        nezapisuje nic (I‑12)
inspect(id)      → okolí + provenience
```

`attach` **smí selhat** — a selhání je tah dialogu, ne výjimka:

```
TypeError        role dostala jiný sort, porovnání napříč osami
DepthExceeded    hloubka vnoření nad parametr gramatiky
UnsafeRule       porušení § 5.4/1–7
CycleDetected    cyklus v dependency grafu naučených pravidel
Unquantified     group ve filleru bez kvantifikátoru → doptání, ne default
```

---

## 10 · Přepis dialogů § 6.12 do jádra

### Dialog A — řetěz s můstkem a veličinou

```
subset(group("auto"), G_DP).
G_DP := group[x | member(x,group("prostředek")) AND member(x,group("dopravní"))].
   # subset do intenzionální group je cukr pro pravidlo:
   #   member(x,group("prostředek")) AND member(x,group("dopravní"))
   #     <- member(x,group("auto"))

r2 = relation("sloužit"; who:∀G_DP, to:∃(group("náklad") OR group("osoba"))).
r3 = relation("jezdit";  who:∀G_DP, via:∃group("dálnice")).
r4 = relation("omezení"; of:∀group("dálnice"), quantity:"rychlost", limit:v130).

? bound(jízdy aut po dálnici, "rychlost", ≤)
   D1: subset*(auto, G_DP) ∧ r3  ⇒ relation("jezdit"; who:∀auto, via:∃dálnice)
   MEZERA: r4 mluví o dálnicích, ne o jízdách  → Gap → nabídka pravidla
! Ano.
rule p3: measure(r,"rychlost") ≤ V
      <- member(r, group("jezdit")),
         role_q(r, via, ∃, P),                    # ∃-role nese group, ne svědka
         rel_atom("omezení"; of:∀P, quantity:"rychlost", limit:V).
→ bound = 130 km/h      Proof: closure(subset*), distribute(D1), fact(r3),
                               fact(r4), rule(p3)

? rel_atom("sloužit"; who:auto, to:∃group("osoba"))
   ∃(náklad OR osoba) ⊭ ∃osoba          (D2 jde jen nahoru)
→ U          — z disjunkce se nesmí vybrat člen ✓
```

### Dialog B — co neplyne

```
r5 = relation("obsahovat"; who:∀group("ovoce"), what:∃group("vitamín")).
member(e_citron, group("ovoce")).  member(e_c, group("vitamín")).

? rel_atom("obsahovat"; who:e_citron, what:e_c)
   D1 dá what:∃vitamín;  „konkrétní × ∃G NEsedí" (§ 3.3)   → U   ✓
? rel_atom("obsahovat"; who:e_citron, what:∃group("vitamín"))
   D1 + ∃×∃                                                → A   ✓
```

### Dialog C — sylogismus a svědek

```
subset(group("spisovatel"), group("člověk")).
disjoint(group("stroj"), group("člověk")).      # expanduje dle § 5.3
member(e17, group("spisovatel")).
relation("napsat"; who:e17, what:e_postriziny).

? member(e17, group("stroj"))
   member* ⇒ member(e17,"člověk");  derivační forma disjoint
   ⇒ neg_atom(member(e17,"stroj"))                          → N   ✓
? enum(group[x | member(x,"spisovatel") AND ∃ napsat(x, Postřižiny)])
   certain {e17}                                            → A + witness ✓
? rel_atom("napsat"; who:∃group("stroj"), what:e_postriziny)
   žádný důkaz ani neg_atom                                 → U   ✓
```

### Dialog D — prostor a čas

```
r7 = relation("jet"; who:e_petr, kam:e_praha, kdy:t_pondeli).
r8 = relation("jet"; who:e_petr, kam:e_brno,  kdy:t_utery).
contains(e_cesko, e_praha).  contains(e_cesko, e_brno).

? „Byl Petr v pondělí v Česku?"
   vyžaduje projekci role: „jel kam:X" ⇒ „byl kde:X"
   — NENÍ zadarmo, je to naučené pravidlo (rule kind: role-projection)
rule rp1: rel_atom("být"; who:W, kde:X) <- role(R,who,W), role(R,kam,X),
                                           member(R, group("jet")).
   pak: contains*(e_cesko, e_praha) ⊑ kam:e_praha              → A ✓
? alt{ before(kdy(r7), kdy(r8)), before(kdy(r8), kdy(r7)) }    → „do Prahy" ✓
? „Byl Petr ve středu v Česku?"    žádný děj s kdy ⊆ středa    → U + Gap ✓
```

### Dialog E — konflikt a výjimka

```
p1  = relation("létat"; who:∀group("pták")).
member(e_tucnak_druh …)  ⇒ subset(group("tučňák"), group("pták")).
? létá tučňák      D1 ⇒ A
! Tučňák nelétá.   neg_atom(rel_atom("létat"; who:∀group("tučňák")))
   ⇒ p i p̄  → CONFLICT + oba Proof, nabídka: revoke | zúžit
! Zúžit.
revoke(p1, "výjimka k7").
p1b = relation("létat"; who:∀(group("pták") DIFF group("tučňák"))).
? létá vrabec  → A ;  ? létá tučňák → N (z neg_atom)                 ✓
```

Pozn.: „tučňák" je **druh**, tedy `Group`, ne entita — zadání ho na
dvou místech zapisuje neslučitelně (`group{e_tucnak}` × `group(tučňák)`).
Jádro připouští jen druhou variantu.

### Dialog F — instance, vršení popisu, jméno

```
# ! Filip má auto.        „auto" neurčitě → attach zakládá individuum
entity a1.  member(a1, group("auto")).
relation("mít"; who:e_filip, what:a1).            @instantiate(t1)

# ! Filipovo auto je modré.   určitý popis rozřešen při attach
member(a1, group("modrý")).                       @stated(t2, resolved:a1)

# ! Filip má Ford.   zmínka bez uzlu → nic se nezakládá → doptání
# ! Je to to auto.
name(a1, +{"Ford"}).                              @assign(t4, confirmed)

? enum(group[x | rel_atom("mít"; who:e_filip, what:x)])
   certain {a1} → syntéza okolí: auto, modrý, "Ford"                 ✓
? „Co je Ford?"   name → a1 → okolí                                  ✓
   „Ford je auto" nebylo nikdy vyřčeno — plyne z name + member
```

---

## 11 · Co přepis dialogů změnil proti podkladu

1. **`role(r,name,t)` je predikát, ne funkce.** Zápis `via(r)` z kostry
   porušuje její vlastní zákaz funkčních symbolů. Navíc je potřeba
   varianta `role_q(r,name,q,g)` — bez ní nemá můstkové pravidlo
   dialogu A na co sáhnout, protože `∃`-role nemá konkrétního svědka.
2. **Constrainty potřebují derivační formu** (§ 5.3). Kontrolní tvar
   `body -> ⊥` neumí vyprodukovat `N`; dialog C i test T6 ho vyžadují.
   Bez toho má `N` v celém systému jediný zdroj — explicitní `neg_atom`.
3. **`bound` je čtvrtý druh dotazu** (§ 6). Odpovědí je mez, ne verdikt;
   bez něj nemá dialog A odpověď svého typu.
4. **Hranice skolemizace je `attach`, ne evaluace.** Neurčitá zmínka
   v tvrzení individuum **vytváří** (dialog F), `∃`-role ho nikdy
   nevytvoří (dialog B). Táž „existence" na dvou stranách hranice —
   a právě tahle čára drží konečnost pevného bodu.
5. **Dialog D není zadarmo.** „Jel kam:X ⇒ byl kde:X" je projekce role,
   tedy naučené pravidlo s vlastním uzlem v důkazu, ne vlastnost `kam`.

---

## 12 · Mimo F0 (rozhodnuto, ne opomenuto)

| Téma | Proč mimo | Co bude potřebovat |
|---|---|---|
| `closed_context` (§ 6.9 zadání) | uzavřený svět uvnitř otevřeného | lokální doména + UNA + `EXACTLY_ONE`/`AT_MOST_ONE`/`AT_LEAST_ONE`/`ALL_DIFFERENT` |
| `GapFinder` | jiný režim evaluace | samostatný SLD modul nad týmž programem |
| perzistence stavů, kauzalita | plná temporální logika | mimo v1 |
| aritmetika | nad rámec mohutnosti a porovnání | mimo v1 |
| ranker čtení | až na důkaz saturace vzorů | § 12/4 zadání |

## 13 · Akceptační sada

T1–T15 z kostry F0 v0.1, T16–T26 z podkladu. Nově přibývá:

| ID | Test | Očekávání |
|---|---|---|
| T27 | `disjoint` → derivace `N` (dialog C) | N + Proof s `constraint` uzlem |
| T28 | `bound` query (dialog A) | 130 km/h + Proof |
| T29 | `role_q` v těle pravidla nad `∃`-rolí | pravidlo se spustí |
| T30 | `∃`-role nezakládá uzel; `attach` ano | počet uzlů po evaluaci beze změny |
| T31 | kanonický důkaz při dvou minimálních | menší množina listů, pak lexikograficky |
| T32 | `member̄*` na podtřídě (dialog C) | `member(e17,"stroj")` → N **a** `member(e17,"parní_stroj")` → N |
| T33 | `member̄*` opačným směrem | „není parní stroj" ⇏ „není stroj" → U |
| T34 | `member̄*` rozšiřuje `CONFLICT` | členství v podtřídě vyloučené třídy → CONFLICT s oběma důkazy |
| T35 | `complete*` vyvrací nečlena | `member(x,g)` → N s výrokem `complete(g)` v důkazu |
| T36 | `complete*` uzavírá podskupiny | uzavření nadskupiny dá N i pro podskupinu |
| T37 | `complete*` nepopře doloženého člena | žádný falešný `CONFLICT` |
| T38 | scelení uzavírající cyklus | `attach(same_as)` → CycleDetected, hrana se nezapíše |
| T39 | doložka nikdy netvrdí úplnost, dokud je co otevřeného | `caveat()` bez „to jsou všichni" |
| T40 | `AND` a `OR` jsou kanonické | `A AND B` a `B AND A` je týž term; `DIFF` naopak ne |
| T41 | algebraický term v roli | `vztah(létat · kdo:∀(pták DIFF tučňák))` je dobře utvořený |
| T42 | **neeliminace `OR`** | z `member(x, A OR B)` neplyne `member(x,A)` ani `member(x,B)` → U |
| T43 | `DIFF` přes `possible` | dialog E: „létá vrabec?" → U bez `disjoint`, A s ním |
| T44 | detekce rekurze nad algebraickým termem | cyklus přes `A DIFF B` se zachytí |

F0 je hotové, když projdou všechny **a** referenční i produkční
evaluator dají shodný verdikt i shodný `normalize_proof`.
