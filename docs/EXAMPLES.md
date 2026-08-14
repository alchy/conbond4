# Praktická ukázka vyhodnocení — doména dopravy a rychlostních limitů

**Status:** akceptační dialog, generovaný ze skutečného běhu.
**Pinning:** `core_semantics/tests/test_examples_transport.py` — každé
tvrzení v tomto dokumentu je zafixované testem, takže dokumentace nemůže
zestárnout nezávisle na kódu.
**Proč tak přísně:** § 8 a I‑14 říkají, že vysvětlení se renderuje
**výhradně ze skutečně použité struktury**. Ukázkový důkazní strom, který
engine nevyprodukuje, by tenhle invariant porušil právě v dokumentu, který
ho má demonstrovat. Všechny stromy níže jsou doslovný výstup
`QueryResult.proof_tree`.

---

## 1 · Případová studie: neúplný text

> „Značka automobilu je Ford, Škoda. Maximální rychlost na dálnici je
> 130 km/h. Dálnice je silnice. Jak rychle může jet Ford po dálnici?"

Přeloženo tak, jak text leží a běží:

```
member(Ford, ZnačkaAutomobilu)
member(Škoda, ZnačkaAutomobilu)
max_rychlost(of:∀Dálnice, quantity:rychlost, limit:130 km/h)
subset(Dálnice, Silnice)
```

**Verdikt: `UNKNOWN`.** Důvody, seřazené od nejtriviálnějšího:

1. **Chybí relace pohybu.** V bázi není jediný vztah, který by cokoli
   spojoval se silnicí. Žádné pravidlo nemá na co sáhnout.
2. **Značka není vozidlo.** `Ford` je v tomhle čtení abstrakce (třída
   značek), ne třída fyzických vozidel. To je táž záměna, kterou § 1
   odděluje sorty.
3. **Chybí můstek „limit místa omezuje jízdu".** Že dálnice má limit, je
   fakt o dálnici; že se jím řídí to, co po ní jede, je samostatné
   tvrzení (dialog A zadání).
4. **Otevřený svět.** Implicitní lidská znalost se nedomýšlí. Chybí‑li
   spojující článek, je stav nedoložitelný — a `U` je odpověď, ne selhání.

## 2 · Nález: navržené rozšíření nestačí

Navrhované doplnění zní:

```
subset(Ford, Automobil);  subset(Automobil, Vozidlo)
same_as(Automobil, Auto)
jezdí_po(who:∀Vozidlo, via:∃Silnice)          ← pozor sem
max_rychlost(of:∀Dálnice, quantity:rychlost, limit:130 km/h)
R1: měř(r) ≤ V  <-  r ∈ jezdí_po, role_exists(r, via, P), max_rychlost(of:∀P, limit:V)
```

**Engine na tuhle bázi odpoví pořád `UNKNOWN`** — ověřeno testem
`test_limit_does_not_reach_across_a_superclass`. Není to mezera
v implementaci; plyne to přímo z per‑roli kvantifikace, kterou § 5.2
zavádí:

```
D2   relation(n; r:∃B, …) ∧ subset*(B,C)  ⇒  relation(n; r:∃C, …)
     ∃ se šíří jen NAHORU, k nadmnožinám
```

Fakt říká, že vozidla jezdí po **nějaké silnici** (`∃Silnice`). Limit je
vlastnost **dálnice**, což je *pod*třída. Aby pravidlo `R1` sedlo, musela
by se `∃Silnice` zúžit na `∃Dálnice` — tedy `∃` směrem dolů, což by byla
právě ta tichá skolemizace, kterou celý návrh zakazuje. Z „vozidla jezdí
po silnicích" a „dálnice mají limit 130" prostě neplyne „vozidla jedou
nejvýš 130": vozidlo mohlo celý život jezdit po okreskách.

**Dvě legální opravy báze:**

| Oprava | Zápis | Význam |
|---|---|---|
| zúžit premisu | `jezdí_po(who:∀Vozidlo, via:∃Dálnice)` | „vozidla jezdí (i) po dálnicích" |
| doložit konkrétní jízdu | instance `jezdí_po` s `via:Dálnice` | „tahle jízda vede po dálnici" |

Obojí je tvrzení, které musí někdo vyslovit. Chybějící článek se nehádá —
nabídne se k potvrzení (§ 6.6 zadání).

## 3 · Úplná báze a odvození limitu

Po zúžení premisy (`via:∃Dálnice`) vypadá báze takto — id výroků jsou ta,
která přiděluje `attach`, a reifikace vztahů je vidět jako řádky
`s0009`–`s0011`:

```
R1   : measure_le(limit:V, of:R) <- member(elem:R, group:·jezdí_po)
                                AND role_exists(filler:·P, name:via, of:R)
                                AND max_rychlost(limit:V, of:∀P, quantity:rychlost)
p0001: ¬member(elem:x, group:·Člověk)  <- member(elem:x, group:·Vozidlo)
p0002: ¬member(elem:x, group:·Vozidlo) <- member(elem:x, group:·Člověk)
s0001: subset(sub:·Ford, sup:·Automobil)
s0002: subset(sub:·Automobil, sup:·Auto)
s0003: subset(sub:·Auto, sup:·Vozidlo)
s0004: subset(sub:·Dálnice, sup:·Silnice)
s0005: subset(sub:·Cestující, sup:·Člověk)
s0006: same_as(left:·Automobil, right:·Auto)
s0007: disjoint(a:·Vozidlo, b:·Člověk)
s0008: jezdí_po(via:∃Dálnice, who:∀Vozidlo)
s0009: member(elem:s0008, group:·jezdí_po)          @reifikace s0008
s0010: role_exists(filler:·Dálnice, name:via, of:s0008)   @reifikace s0008
s0011: role_forall(filler:·Vozidlo, name:who, of:s0008)   @reifikace s0008
s0012: max_rychlost(limit:130_km/h, of:∀Dálnice, quantity:rychlost)
s0021: member(elem:Mondeo, group:·Ford)
s0022: member(elem:Jan_Novák, group:·Člověk)
```

`p0001` a `p0002` nikdo nepsal — vznikly derivační expanzí `disjoint`
(§ 5.3). Bez nich by z neslučitelnosti nikdy nevznikl verdikt `N`.

**Dotaz:** mez rychlosti pro jízdy po dálnici.
**Verdikt: `PROVEN_TRUE`, 130 km/h.**

```
rule(R1)
  closure(member*)
    fact(s0009)
    closure(subset*/refl)
  fact(s0010)
  fact(s0012)
```

Čtení: `R1` se spustilo, protože `s0008` je instance vztahu `jezdí_po`
(`s0009`), jeho `∃`-role `via` nese skupinu `Dálnice` (`s0010`) a o té
platí omezení 130 km/h (`s0012`). Že `∃`-role **nemá konkrétního svědka**,
nevadí — pravidlo na ni sahá predikátem `role_exists`, ne funkcí.

## 4 · Dialog nad úplnou bází

### Otázka 1 — dědičnost vztahu na instanci podtřídy

> „Jezdí Mondeo po dálnici?"

**`PROVEN_TRUE`.** Mondeo ∈ Ford ⊆ Automobil ⊆ Auto ⊆ Vozidlo, a fakt
`s0008` má `who:∀Vozidlo`, takže se distribuuje dolů (D1) až na prvek.

### Otázka 2 — existenční role nepojmenovává svědka

> „Přepravuje Mondeo konkrétně Jana Nováka?" → **`UNKNOWN`**
> „Přepravuje Mondeo nějakého cestujícího?" → **`PROVEN_TRUE`**

Táž báze, opačné odpovědi — a přesně v tom je smysl per‑roli
kvantifikace. `přepravuje(who:∀Auto, what:∃Cestující)` tvrdí, že auta
někoho vozí; **koho**, z toho neplyne. Engine odmítá vyrobit anonymního
svědka i ztotožnit obecný existenční výrok s konkrétním prvkem domény.

### Otázka 3 — silná negace přes hierarchii

> „Je Jan Novák automobil?"

**`PROVEN_FALSE`.**

```
closure(member̄*)
  rule(p0002)
    closure(member*)
      fact(s0022)
      closure(subset*/refl)
  closure(subset*)
    fact(s0002)
    fact(s0003)
```

Čtení: Jan Novák je člověk (`s0022`), z expanze `disjoint` plyne, že
člověk není vozidlo (`p0002`), a kontrapozice `member̄*` to donese po
řetězu `Automobil ⊆ Auto ⊆ Vozidlo` (`s0002`, `s0003`) až na automobil.
Opačný směr neplatí: „není automobil" neznamená „není vozidlo".

### Otázka 4 — spor v bázi

> „Jan Novák je Mondeo." → uloženo jako `s0023: same_as(Jan_Novák, Mondeo)`
> „Je Jan Novák člověk?"

**`CONFLICT`** — se dvěma nezávislými důkazy:

```
p:
  closure(member*)
    fact(s0022)
    closure(subset*/refl)
p̄:
  rule(p0001)
    closure(member*)
      fact(s0021)
      closure(subset*)
        fact(s0001)
        fact(s0002)
        fact(s0003)
      closure(same_as*)
        fact(s0023)
```

Pro: přímý fakt. Proti: Jan Novák ≡ Mondeo (`s0023`), Mondeo ∈ Ford ⊆ …
⊆ Vozidlo, a vozidlo není člověk (`p0001`). Konflikt se **hlásí, ne
přepisuje** (I‑3); obě větve zůstávají ukazatelné, aby se člověk mohl
rozhodnout, kterou odvolat.

**Typová poznámka.** „Jan Novák je Mondeo" nelze zapsat jako
`member(Jan_Novák, Mondeo)`: `Mondeo` je jednotlivina (`s0021` z něj dělá
prvek skupiny `Ford`), ne skupina, takže konstruktor to odmítne se
`SortError`. Dobře utvořené čtení je identita — a ta spor skutečně
vyrobí.

## 5 · Notace důkazních uzlů

Engine emituje jen tyhle druhy uzlů; ilustrativní jména jako
`role_inheritance` nebo `edge(same_as: …)` mezi ně nepatří:

| Uzel | Význam |
|---|---|
| `fact(id)` | výrok v bázi |
| `rule(id)` | naučené pravidlo (včetně expanzí `disjoint`) |
| `closure(subset*)` · `closure(member*)` | jádrové uzávěry nad hierarchií |
| `closure(member̄*)` | kontrapozice silné negace (§ 5.1) |
| `closure(contains*)` · `closure(within*)` | prostor a čas |
| `closure(same_as*)` | identitní krok — vlastní uzel, ne skrytá normalizace |
| `closure(reify)` | dekompozice vztahu na role |
| `distribute(⪯)` | shoda dotazu s faktem přes D1/D2 |
| `witness(vazba)` | svědek u neuzemněného dotazu |

Přípona `/refl` značí reflexivní krok, který nenese žádný výrok.
