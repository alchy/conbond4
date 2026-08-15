# conBond4 — audit jádra

## Status: 🟢 PASS — rozhodnutí místo kódu, a moje čísla byla ta horší

**Kolo #96.** 1066 testů zelených (+2 doložené meze), `mypy --strict`
čistý na 62 souborech, doložky **76/76**, **živá parita 55/55**, dialogy
**19 / 48 / 31**, jádrové relace 9/9, `U` 11, nula `RECALL_FAILURE`,
**celá stálá regrese zelená**. Jádro 0.1.33, HEAD `f7b7e61`, strom čistý.
**Korpus `948218d → f7b7e61`: verdikt 0, blokátor 0, čtení 0** — přesně
jak má vypadat kolo, ve kterém se nic nestaví.

**Architectural Health Score: 9,5 / 10.**

---

## Rozpor v číslech: tvoje jsou správná, moje neúplná

Hlásils nesouhlas (152/44 proti 165/50) a **měls pravdu ty**. Dohledal
jsem to:

```
jen z řádků [CHYBÍ: co znamená role …]    152 vět · 44 tvarů   ← moje #95
řádky PLUS text otázky                    160 vět · 50 tvarů   ← tvých 50 SEDÍ
navíc: advcl:protože · advcl:když · advcl:pokud · advcl:ačkoli · s kým · čím
```

**Četl jsem jen stopu, ne otázku.** Zbytek rozdílu (160 × 165, 218 × 250)
je **jednotka** — počítám tvar jednou za větu, ty za výskyt.

**Je to potřetí v pěti kolech, co mi vlastní sonda ubrala číslo** —
`break` po první zmínce, čas místo témat, teď jen část výstupu. **Beru
si z toho pravidlo: měřit z objektu (kaskáda, predikace), ne z toho, co
se vypsalo.** Ty tak měříš, a proto ti čísla sedí.

---

## Odpověď na můj vlastní návrh: byl kruhový

Napsal jsem *„odpověď nejspíš není mapa tvar→role, ale tvar + sort
filleru"*. **Máš pravdu, že takhle to nejde:** podle § 3.6 **sort plyne
z role** (`kde → Place`), takže odvodit roli ze sortu je **kruh**.
Ověřil jsem to i ve stopě — `Pondělí → pondělí (sort z role)`.

**Tvůj tvar té myšlenky je správný a není to opatrnost, je to jiná
věc:** ne sort, ale **signál z rozboru**. A změřils, kam až sahá:

```
v+Loc, 42 výskytů:   5 filler s NameType=Geo   → místo, čitelné z rysu
                    11 dítě je letopočet       → čas, čitelné ze stromu
                    26 ANI JEDNO               → byt, kostel, „v angličtině“, „ve své knize“
```

**38 % bez jediného dohadu, u zbylých 26 se musí dál ptát.** To je
poctivé číslo a je to lepší odpověď než moje otázka.

---

## Nález, který mění zeď víc než celé učení rolí

**Reprodukoval jsem ho a je ostřejší, než ho popisuješ:**

```
» V letech 1925–1933 byl prvním předsedou československého odboru.
   být(Gen:československý_odbor, co:první_předseda, kdo:předseda, v+Loc:léta)
   [PŘÍVLASTEK: „předseda odbor“ — vztah vedle věty, čeká se na jméno role]
```

**Týž token je ve čtení dvakrát** — jako `co:první_předseda` (složená
zmínka) a jako `kdo:předseda` (holé lemma z pro‑dropu) — a genitiv proto
skončí **jako role predikace vedle přívlastku**, ne jako jeho součást.
`genitive_attributes` páruje hlavu **shodou lemmat**, ale zmínku skládá
někdo jiný.

**Posedmé táž rodina** (W‑32, W‑47, W‑48, B‑18, B‑22, W‑53, teď tohle):
**přesná shoda na kategorii, jejíž hodnotu skládá jiná vrstva.** Stabilní
je `token_index`, a je to týž anchor, který sis u W‑53 nechal na hlavě
přesně z tohoto důvodu.

**Že jsi to neopravil, je správně** — mění to čtení 13 vět a rozhodnutí
o tom je moje.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑58 · složená hlava skrývá svůj genitivní přívlastek** — 13 výskytů,
doložena testem, ne prózou.

**W‑59 · `nsubj:pass` se ptá na význam role, který rozbor už řekl** —
19 výskytů. **Tvoje oprava mé domněnky je přesná:** vlastní jméno té role
je **zapsané rozhodnutí** (trpný podmět není konatel), ne vada zápisu.
Ale mezi *okolnostmi* skutečně nepatří.

**Otevřené beze změny:** úřad se nezapíše (odmítnuto s důvodem),
příbuzenství jako třetí druh titulu, `nmod` pod obecným jménem, W‑54,
`cb-wiki.py` zkracuje `reason` (u Agenta 3 — **potřetí tě to poslalo
špatně, tentokrát 10 vět místo 165**), W‑42, W‑43, W‑44, W‑45, W‑23,
W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38, W‑40, W‑41.

---

## Action Items for Agent 1

**TVOJE POŘADÍ SCHVALUJI CELÉ, a je to správné pořadí z principu, ne jen
podle velikosti: (a) a (b) jsou OPRAVY, (c) je nová schopnost. Korektnost
před pokrytím.**

**(a) přívlastek přes `token_index`, ne přes lemma.** 13 výskytů, jedna
příčina, sedmá instance téže rodiny. **Vezmi to jako jedno kolo samo** —
mění čtení a chci u něj vidět diff po větách.

**(b) `nsubj:pass` → strukturální mapování z podtypu `:pass`.** Není to
dohad: `:pass` **stojí v rozboru**, tedy táž cesta jako W‑47/W‑48.
**Podmínka: ta jedna kolize.** Změřils 18 z 19 bez role `co` — u té
devatenácté se **musí zeptat, ne přepsat**, a chci to jako vlastní krok
v doméně, ne jen jako poznámku.

**(c) tvar + signál z rozboru u `v+Loc`** teprve potom.

**Můj counterexample pro (a), psaný jako vlastnost:** **žádná zmínka
nesmí být ve čtení dvakrát pod dvěma jmény** — konkrétně *„V letech
1925–1933 byl prvním předsedou československého odboru."* nesmí dát
zároveň `co:první_předseda` i `kdo:předseda`; genitiv se objeví
**buď** jako přívlastek, **nebo** jako role, ne obojí; devatenáct domén
se závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 55/55; nula `RECALL_FAILURE`; doložky ≥ 76/76; `mypy --strict`
čistý; **korpus přeměřen a diff po větách** — u těch 13 chci vidět, co
se ve čtení změnilo, a jestli některá poprvé opustí `PTÁ SE`, chci
u ní doložení, ne souhrn.

---

## ARCHIV — kolo #95

### Status: 🟢 PASS — W‑56 a W‑57, druh titulu rozhoduje člověk

**Kolo #95.** 1064 testů zelených, `mypy --strict` čistý na 62 souborech,
doložky **76/76**, **živá parita 55/55**, dialogy **19 / 48 / 31**,
jádrové relace 9/9, `U` 11, nula `RECALL_FAILURE`, **celá stálá regrese
zelená**. Jádro 0.1.32, HEAD `948218d`, strom čistý.

**Architectural Health Score: 9,5 / 10** — nejvýš dosud, a je to za
**přiznání**, ne za kód.

---

## Nejdřív oprava mého vlastního verdiktu

V #93 jsem napsal, že rozhodnutí *„nabídnout, nezapsat"* **má pod sebou
číslo, ne úvahu**, a citoval jsem rozklad **29 povolání / 24 úřad /
18 příbuzenství**. **Ten rozklad jsi ručně zařadil ty, ne rozbor** —
píšeš to sám a všiml sis toho, až když jsi na tom měl něco postavit.
**Přijal jsem ruční značkování jako měření a to je moje chyba, ne tvoje.**

**Ověřil jsem, proč to jinak nešlo:**

```
Prezident Masaryk zemřel.   Prezident NOUN nsubj  Animacy=Anim Case=Nom Gender=Masc Number=Sing
                            Masaryk   PROPN flat  … NameType=Giv …
Básník Hora zemřel.         Básník    NOUN nsubj  Animacy=Anim Case=Nom Gender=Masc Number=Sing
                            Hora      PROPN flat  … NameType=Giv …
```

**Rozbor je identický do posledního rysu.** Úřad od povolání odlišit
NELZE — a tím se to původní rozhodnutí nezhroutilo, **stojí teď na
pevnějším**: není to „dvě třetiny by byly špatně" (statistika), ale
**„z tvaru se to poznat nedá" (struktura)**. To je lepší důvod, než jaký
jsem tehdy pochválil.

---

## Ověřeno reprodukcí

**Měření času — tvé číslo sedí a je to to podstatné zjištění kola:**

```
zmínek titul+jméno                     32 (moje jednotka: věta) · 39 (tvoje: zmínka)
z toho ČAS VISÍ POD TITULEM             4     ← shoda na kus
a jsou to ŽIVOTNÍ DATA, ne doba držení: „(1805, Nový Bydžov – …“, datum svatby
u ÚŘADŮ                                 0
```

Rozdíl 32 × 39 je **jednotka, ne rozpor** — počítám po větách (`break`
po první zmínce), ty po zmínkách. **Je to podruhé, co mi tenhle tvar
sondy zkreslil číslo**; píšu si to sem, ať to potřetí nedělám.

**Že jsi měřil PŘÍSNĚ, je samo o sobě nález:** volnější sourozenecké
pravidlo nabíralo čas **slovesa** a nafouklo 4 na 8. *„Nebyla by to
opatrnost navíc, bylo by to jiné měření."* Přesně tak.

**Tři stavy, tři hlášky — a všechny tři pravdivé:**

```
bez nabídky      ✗ „žádná věta v tomhle sezení to netvrdí“
čeká, ÚŘAD       ✗ „úřad platí V ČASE a jádro čas neumí“ · nabídka ZŮSTALA otevřená
čeká, POVOLÁNÍ   ✓ zapsáno [s0005] · Je Josef Hora básník? → ANO
už rozhodnuto    ✗ „už je to potvrzené a leží to v bázi jako [s0005]“ + jak to odvolat
Je Masaryk prezident?  → NEVÍM
```

**W‑56 root cause byl TVAR PAMĚTI, ne hláška** — dvoustavový slovník
neuměl rozlišit *rozhodnuto* od *nikdo nic neřekl*. Že jsi opravil
strukturu a hláška vypadla jako důsledek, je správné pořadí.

**Že odmítnutí úřadu nechává nabídku otevřenou**, protože *„jádro jen
neumí, co by bylo potřeba"*, je přesné: kdyby zmizela, tvrdil by systém,
že se rozhodlo.

**Zesílení sady beru** — `refuses` hlídalo jen nezapsání, takže by prošla
i mlčenlivá nečinnost. Odmítnutí a nečinnost jsou dvě věci.

**Korpus `feb5888 → 948218d`:** verdikt 0, čtení 0, nabídka dál u 13
z 238. Sedí.

---

## Critical Blockers

**Žádné.** W‑56 i W‑57 uzavřeny.

---

## Semantic Warnings

**Úřad se nezapíše — a je to ODMÍTNUTO S DŮVODEM, ne nevyřešeno.**
Souhlasím i s tím, kdy se to otevře znovu: až bude korpus, kde úřady čas
nesou.

**Příbuzenství** („bratr Josef Čapek" → `member(Josef_Čapek, bratr)`)
je **užší** tvrzení, ne širší — vědomě ponecháno, správně.

**`nmod` pod obecným jménem**, **skupina v plurálu** (W‑54),
**`cb-wiki.py` zkracuje `reason`** (u Agenta 3), **W‑42, W‑43, W‑44,
W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38, W‑40, W‑41**
leží dál.

---

## Action Items for Agent 1

**Rodina titulů je uzavřená. DALŠÍ SMĚR JE TA ZEĎ, PŘED KTEROU KORPUS
STOJÍ CELOU DOBU: JMÉNA ROLÍ.**

**Změřil jsem to sám, ať máš od čeho začít:**

```
vět, kde se systém ptá „co znamená role X“:   152 z 238
různých tvarů:                                 44
v+Loc 42 · Gen 22 · nsubj:pass 19 · Dat:arg 10 · Ins:arg 10 · od+Gen 9 …
prvních 15 tvarů pokrývá 77,5 % všech výskytů
```

**NEZAČÍNEJ IMPLEMENTACÍ. Prvním krokem je rozhodnutí, ne kód**, a chci
ho vidět napsané dřív, než něco vznikne:

1. **Je `v+Loc → kde` znalost o jazyce, nebo hypotéza o téhle větě?**
   Na tom stojí všechno ostatní. `v+Loc` je *kde* i *kdy* („v roce 1935"),
   takže odpověď nejspíš není mapa tvar→role, ale **tvar + sort filleru**.
   Změř to dřív, než to postavíš — je to tvé vlastní pravidlo.
2. **Kde ta znalost bydlí.** Jestli vznikne seed, musí to být **data
   s proveniencí, odvolatelná a viditelná v přepisu**, ne tabulka v kódu.
   Zakódovaný seznam slov je ta rodina chyby, kterou u sebe hlídáš od
   W‑32 — a tys ji v tomhle kole sám odmítl u úřadů.
3. **`nsubj:pass` na třetím místě (19×) tam nejspíš nepatří** — to není
   okolnostní role, to je podmět. Podívej se, jestli to není vlastní vada.

**Můj counterexample, psaný jako vlastnost:** **žádná role nesmí dostat
význam, který v té větě není doložený tvarem ani sortem** — a u každé
věty, která se díky tomu nově zapíše, chci **v hlášení vidět, z čeho ten
význam plyne**; **`ZAPSÁNO` smí růst jen tam, kde by to potvrdil člověk
čtoucí tutéž větu**; devatenáct domén se závěry beze změny; jádrové
relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 55/55; nula
`RECALL_FAILURE`; doložky ≥ 76/76; `mypy --strict` čistý; **korpus
přeměřen s rozkladem po tvarech** — a jestli `ZAPSÁNO` poprvé opustí
nulu, chci u **každé** takové věty doložení, ne souhrn.

---

## ARCHIV — kolo #94

### Status: 🟢 PASS — B‑23 uzavřena

**Kolo #94.** 1058 testů zelených, `mypy --strict` čistý na 62 souborech,
doložky **76/76**, **živá parita 55/55**, dialogy **19 / 48 / 31**,
jádrové relace 9/9, `U` 11, nula `RECALL_FAILURE`, **celá stálá regrese
zelená**. Jádro 0.1.31, HEAD `feb5888`, strom čistý.

**Architectural Health Score: 9,4 / 10.**

---

## Ověřeno reprodukcí — čtyři cesty, ne jedna

```
1) prázdné sezení          ✗ nezapsáno · báze 0
      „potvrdit „král Kdokoli“ nejde: žádná věta v tomhle sezení to netvrdí“
2) jiný titul po větě      ✗ nezapsáno · báze 4 beze změny
      nabídka PO odmítnutí zůstala:  member(elem:Josef_Hora, group:·básník)
3) správné potvrzení       ✓ zapsáno [s0005]  @tah 3: titul z věty
      [VÝROK VEDLE VĚTY — tvrdí to „Nad hrobem promluvil básník Josef Hora.“]
      Je Josef Hora básník?  → ANO, doloženo s0005
4) TÉŽ potvrzení podruhé   ✗ nezapsáno · báze 5 beze změny
```

**Volba (1) je správná a tvůj důvod pro odmítnutí místo „očištění" je
ten podstatný:** kdyby se jen opravila hláška a zápis zůstal, **zůstal by
v systému způsob, jak dostat do báze cokoli pod jménem POTVRZENÍ**.

**Vada, kterou jsi našel sám, je cennější než ta, kterou jsem našel já.**
Odmítnutý tah nabídku **spotřebovával** (`pop` běžel vždycky), takže po
odmítnutém *„prezident Josef Hora"* by spadlo i potvrzení té **správné**
dvojice a nikdo by nevěděl proč. **Ověřil jsem to živě — body 2 a 3 nad
sebou:** po odmítnutí nabídka zůstala a potvrzení pak prošlo. *Odmítnutí,
které po sobě uklidí cizí stav, je horší než zápis* — souhlas.

**Bod 4 zavírá i to, na co ses neptal**: dvojí potvrzení už neprojde,
takže se sem nevrací B‑19.

**Test psaný jako VLASTNOST je správný tvar** — věta z hlášení se hledá
**v žurnálu**, ne porovnává jako řetězec. To je přesně to poučení
z #92 a je dobře, že sis ho vzal za své dřív, než jsem ho vymáhal.

**Korpus `ec572d0 → feb5888`, přečteno mnou z obou záznamů:** verdikt 0,
blokátor 0, **čtení 0**. Očekával jsem nulu a nula to je — tah
v korpusovém běhu nepadne.

---

## Critical Blockers

**Žádné.** B‑23 uzavřena.

---

## Semantic Warnings

### W‑56 · odmítnutí říká špatný důvod, když je titul UŽ POTVRZENÝ

**Reprodukováno, bod 4 výše:**

```
» →∈ „básník Josef Hora“  (podruhé, s0005 už v bázi)
   ✗ nezapsáno: potvrdit „básník Josef Hora“ nejde:
     ŽÁDNÁ VĚTA V TOMHLE SEZENÍ TO NETVRDÍ
```

**Ta věta v sezení je** — je to `s0001`, a `s0005` z ní přímo vznikl
s proveniencí *„titul z věty"*. Pravý důvod není *„nikdo to neřekl"*,
ale *„už je to potvrzené"*.

**Není to bloker:** nic se nezapíše, žádný důkaz to nenese, člověk
nedostane výrok navíc. Ale **je to výrok o textu, který neplatí**, a to je
ta jediná třída, kterou tu držíme prázdnou. Dva stavy — *nikdo to
netvrdil* × *už rozhodnuto* — se slily do jedné hlášky, což je táž chyba
tvaru jako slévání pěti stavů v měření.

---

## Otevřené, beze změny

Čas u úřadů (24/71), příbuzenství (18/71), `nmod` pod obecným jménem,
skupina v plurálu (W‑54) — **správně přiznané meze, ne dluh**.

**Nález o `cb-wiki.py`** (`reason` uříznut, ze záznamu vyjdou 2 místo 13)
leží u Agenta 3 s lokací a **zkreslí každé další čtení korpusu** — je to
čtvrté potvrzení W‑43.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**W‑56 oprav jedním rozlišením** — dva různé stavy, dvě různé hlášky —
**a neber si na to vlastní kolo**; vezmi ji s sebou do dalšího směru.

**HLAVNÍ SMĚR: ČAS U ÚŘADŮ.** Je to největší otevřená rodina, kterou jsi
sám změřil (**24 zmínek ze 71**), a jediná, kde **potvrzení dnes vede
k tvrzení, které text neříká**: kdo potvrdí *„Masaryk je prezident"*,
zapíše **bezčasý** výrok, a systém ho jen varuje.

**Než začneš stavět, změř** — a to je podmínka, ne rada: **kolik z těch
24 vět vůbec nese čas** (rok, „v letech", „od…do"), který by šlo použít.
Jestli ho většina nenese, není to úloha o čase v jádře, ale o tom, že se
nemá co zapsat — a pak je správná odpověď **nenabízet** místo
**nabízet a varovat**.

**Můj counterexample, psaný jako vlastnost:** **žádné potvrzení nesmí
vyrobit výrok, který platí v širším rozsahu, než co věta říká.**
Konkrétně: *„Prezident Masaryk zemřel."* buď členství nenabídne, nebo ho
nabídne s časem, který ve větě stojí — **ale nesmí zapsat bezčasé
`member(Masaryk, prezident)` jen proto, že člověk odklikl**; *„Nad hrobem
promluvil básník Josef Hora."* se **nezmění** (povolání bezčasé je
v pořádku, a jestli se to změní, ať je to napsané jako rozhodnutí);
devatenáct domén se závěry beze změny; jádrové relace 9/9; gate *Farmaka*
`N`/`s0005`; parita ≥ 55/55; nula `RECALL_FAILURE`; doložky ≥ 76/76;
`mypy --strict` čistý; **korpus přeměřen s rozkladem nabídek**, ne jen
verdiktů.

---

## ARCHIV — kolo #93

### Status: 🔴 FAIL — B‑23, potvrzení bez nabídky

**Kolo #93.** 1054 testů zelených, `mypy --strict` čistý na 62 souborech,
doložky **76/76**, **živá parita 55/55**, dialogy **19 / 48 / 31**,
jádrové relace 9/9, `U` 11, nula `RECALL_FAILURE`, **celá stálá regrese
zelená**. Jádro 0.1.30, HEAD `ec572d0`, strom čistý.

**Architectural Health Score: 9,2 / 10.**

**FAIL je za JEDEN tah, ne za návrh.** Rozhodnutí „nabídnout, nezapsat"
je správné, doložené a je to nejlepší kus téhle práce.

---

## Co je hotové a ověřené

**Rozhodnutí má pod sebou číslo, ne úvahu** — a to je ten rozdíl proti
`same_as` v #91:

```
71 zmínek stavby v korpusu:  29 povolání · 24 úřad v čase · 18 příbuzenství
tvar je u všech tří TÝŽ, rozbor je nerozlišuje
```

Dvě třetiny by ležely v bázi jako bezčasý nebo neúplný „doložený fakt".
**Tohle číslo je celý ten důvod** a bez něj by to byla jen opatrnost.

**Mezera přestala lhát**, ověřeno živě:

```
bylo:  [HYPOTÉZA — nikdo to neřekl a žádné pravidlo to nevyrábí]
je:    [HYPOTÉZA — řekls to, ale nezapsalo se to — čeká to na potvrzení]
       [ŘEKLS TO — „Nad hrobem promluvil básník Josef Hora.“ to tvrdí titulem…]
```

Že jsi ten důvod **přepsal a nepřidal vedle**, je správně — dvě věty
vedle sebe by si odporovaly. **Verdikt zůstal `U`** a to je taky
správně: nikdo to nepotvrdil, tak se to netvrdí.

**Přiznaná mez u sporného případu je poctivá** a cením si jí:
*„že se `prezident Masaryk` nezapíše, není chytrost jádra — je to
důsledek toho, že se nezapíše žádný."* Přesně tak se to má psát.

**Korpus `f681902 → ec572d0`:** verdikt 0, čtení 0, nabídka u **13 vět
z 238**, všech 13 uvnitř rodiny — sedí. **Tvůj nález o `cb-wiki.py`**
(pole `reason` uříznuto, ze záznamu vyjdou 2 místo 13) **je pravdivý
a je to potvrzení W‑43 počtvrté** — díky, že jsi to napsal dřív, než
bych to počítal ze záznamu.

---

## Critical Blockers

### B‑23 · `→∈` zapíše cokoli a tvrdí u toho větu, která nikdy nepadla

**Reprodukováno mnou, dva pokusy:**

```
(1) sezení PO větě o Josefu Horovi, potvrdím titul, který se NENABÍDL:
    confirms_title("Ano.", "Josef_Hora", "prezident")
    → ✓ zapsáno [s0005]  member(elem:Josef_Hora, group:·prezident)

(2) sezení, kde NEPADLA ANI JEDNA VĚTA:
    confirms_title("Ano.", "Kdokoli", "král")
    → ✓ zapsáno [s0001]  member(elem:Kdokoli, group:·král)  @tah 1: titul
      [VÝROK VEDLE VĚTY — věta sama se zapsala už dřív; …]
```

**Ta hláška je nepravdivá.** Žádná věta se dřív nezapsala — žádná
neexistuje. A výrok jde do báze s proveniencí **„tah 1: titul"**, tedy
jako potvrzený titul z textu.

**`_confirm_title` nekontroluje nic**: `_offered_titles.pop(…, None)` —
nabídku *odebere, pokud tam je*, a zapíše **i když tam není**.

**Rozlišuju dvě věci a jen jedna je vada.** Že tah člověka **píše**, je
v pořádku — `→∀`, `!∀` i ostatní tak fungují a je to jeho výrok. Vada je,
že se ten tah jmenuje **potvrzení**, nese **proveniencí titulu** a
**tiskne větu o textu**, aniž by cokoli z toho ověřil.

**A rozchází se to s tvým vlastním counterexamplem**, který zněl:
*„u každého takového zápisu je v hlášení věta z textu, která to říká;
‚řekls to' bez věty je tvrzení bez důkazu, a je na to test."*
**Na téhle cestě věta z textu v hlášení není.** Test ji hlídá jen tam,
kde nabídka existuje (`test_title_claim.py:241`, doména 19) — **cesta
bez nabídky testem pokrytá není**.

**Proč je to bloker, a ne varování:** je to **zápis** do báze
s **nepravdivým doprovodným tvrzením o textu**, a to je přesně ta třída,
kterou držíme prázdnou. `XAIPresenter` ten výrok později ocituje jako
potvrzený titul.

---

## Semantic Warnings

**Tvůj druhý nález — nálezový skript srovnával dvě různé sady** (podle
času, ne podle témat) — beru a je dobře, žes ho napsal sám. **Máš
pravdu i v tom, co je na tom nepříjemné:** chytils to čtením výsledku,
ne testem. Potřetí táž rodina (abeceda → čas → nic, co o sadě vypovídá).

**Otevřené rodiny, které sám pojmenováváš** — čas u úřadů (24/71),
příbuzenství (18/71), `nmod` pod obecným jménem, skupina v plurálu —
beru jako správně přiznané meze, ne jako dluh.

**W‑42, W‑43** (u Agenta 3), **W‑44, W‑45, W‑23, W‑25, W‑26, W‑30,
W‑31, W‑36, W‑37, W‑38, W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: B‑23. Je to malá oprava a nechci u ní nic víc.**

**Rozhodni jednu věc: co `→∈` JE.**

1. **Je to potvrzení** → pak **musí existovat nabídka**, a bez ní se tah
   **odmítne** (`✗`), stejně jako se odmítá kruh v uspořádání.
2. **Je to výrok člověka** → pak se **nesmí jmenovat potvrzení**, nesmí
   nést proveniencí `titul` a **nesmí tisknout větu o textu**, kterou
   nemá.

**Nevybírám za tebe, ale (1) je to, co ten tah má být** — vznikl proto,
aby se rozhodlo o něčem, co řekl text.

**Můj counterexample, psaný jako vlastnost:** **žádný zápis nesmí nést
tvrzení o textu, které není doložené konkrétní větou v sezení.**
Konkrétně: `confirms_title` bez předchozí nabídky **nezapíše** (nebo se
nejmenuje potvrzení a netvrdí větu); `confirms_title` **po** nabídce dál
zapíše a *„Je Josef Hora básník?"* dá `A` doloženo tím zápisem; **cesta
bez nabídky má vlastní test** — dnes ji nemá žádný; devatenáct domén se
závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 55/55; nula `RECALL_FAILURE`; doložky ≥ 76/76; `mypy --strict`
čistý; korpus přeměřen — **očekávám 0 změn ve verdiktu i ve čtení**,
protože tohle se korpusu nedotýká, a jestli se něco změní, je to nález.

---

## ARCHIV — kolo #92

### Status: 🟢 PASS — kvantifikátor jde s identitou

**Kolo #92.** 1038 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **75/75**, **živá parita 55/55**, dialogy **18 / 45 / 28**,
jádrové relace 9/9, `U` 9 a **nula `RECALL_FAILURE`**, celá stálá regrese
zelená. Jádro 0.1.29, HEAD `f681902`. **Pracovní strom čistý** — pád,
který jsem v něm včera viděl, byl rozdělaná editace a je zakomitovaná.

**Architectural Health Score: 9,4 / 10.**

---

## Ověřeno reprodukcí — všechno, cos tvrdil, na kus

```
Nad hrobem promluvil básník Josef Hora.  → promluvit(kdo:Josef_Hora, …)  ZAPSÁNO
                                            básník Josef Hora → Josef_Hora (založen)
Promluvil Josef Hora?                    → ANO, doloženo s0001
Promluvil básník?                        → NEVÍM        ← závěr domény 18
Mezi pátečníky … bratří Čapků …          → kromě+Gen:bratr   (ne vymyšlený člověk)
Matka Božena Čapková …                   → Božena_Čapková    (jednotné číslo projde)
Město Praha leží v Čechách.              → NEZMĚNĚNO (nmod, ne flat)
```

**Korpus `e9a463a → f681902`, přečteno mnou z obou záznamů:**
verdikt **0**, blokátor **0**, **změněné čtení 13**, z toho **zmizel `∀`
u 8**. Sedí položku po položce.

**TO NEJDŮLEŽITĚJŠÍ Z CELÉHO KOLA NENÍ OPRAVA, ALE ŽE JSI NAŠEL DÍRU
V MÉM COUNTEREXAMPLU.** Tvoje první verze dala `promluvit(kdo:∀Josef_Hora)`
— **můj požadavek „nedá `kdo:∀básník`" by byl splněn a věta by pořád
tvrdila něco o všech, kdo se tak jmenují.** Našels to probní větou, ne
úvahou.

**Beru z toho poučení pro sebe a píšu si ho sem:** counterexample musí
pojmenovat **vlastnost**, ne řetězec. Ne „nesmí tam být `∀básník`", ale
**„o žádné třídě, kterou věta nekvantifikuje, nesmí vzniknout tvrzení"**.
Řetězcová podmínka je táž vada, jakou u tebe šestkrát hlídám — jen
v testu místo v kódu.

---

## Rozpor 32 × 28 — chyba je má, číslo tvoje

Nezaokrouhluju to. **Tvých 32 je správně, mých 28 bylo měření něčeho
jiného.** Můj tehdejší skript bral **jen první `flat` v každé větě**
a počítal ji, **jen když se ten člen objevil v `ZAHOZENO`** — takže mi
vypadly věty, kde stavba je, ale první `flat` visel pod `PROPN` nebo
nespadl. Tvoje kritérium čte stavbu z rozboru. **Přeměřil jsem tvým
kritériem: 32.** Moje číslo stahuju.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

### W‑55 · titul nese TVRZENÍ, které se nezapíše ani neohlásí — a mezera o něm lže

**Reprodukováno mnou:**

```
» Nad hrobem promluvil básník Josef Hora.
   ✓ zapsáno  promluvit(kdo:Josef_Hora, nad+Ins:∃hrob)
» Je Josef Hora básník?
   → NEVÍM
     ? platí member(elem:Josef_Hora, group:·básník)?
       [HYPOTÉZA — NIKDO TO NEŘEKL a žádné pravidlo to nevyrábí]
```

**Ta věta to řekla.** „básník Josef Hora" tvrdí dvě věci — *promluvil*
a *je básník*. Zapíše se jedna, druhá **se ani nezapíše, ani se
neohlásí jako nevzatá**, a mezera o ní tvrdí, že ji nikdo neřekl.

**Ověřil jsem, že to NENÍ od tvé opravy** — export `e9a463a` dává týž
výrok („nikdo to neřekl") ještě dřív, než skládání vzniklo. **Proto
varování, ne bloker.** Ale je to poslední zbytek té třídy, kterou
držíme prázdnou, a `básník Josef Hora` je **32 vět z 238**, tedy běžná
česká encyklopedická próza, ne okrajovost.

**W‑42, W‑43** (u Agenta 3), **W‑44, W‑45, W‑23, W‑25, W‑26, W‑30,
W‑31, W‑36, W‑37, W‑38, W‑40, W‑41** leží dál. Otevřené rodiny, které
sám hlásíš — skupina pojmenovaná příjmením („bratří Čapků", „Novákovi")
a `nmod` pod obecným jménem — beru jako správně pojmenované meze.

---

## Chybějící důkaz, který není tvůj

**Regresi nad historickými daty conBond2/3 dnes nejde spustit.**
V `conbond4-utils` leží `cb-korpus.py`, `cb_utils/korpus.py`
a `data/conBond2` — **nezakomitované, bez jediného záznamu měření**.
Dokud to Agent 3 nedokončí, **je „neporušil jsem starší chování"
doloženo jen na 238 větách Wikipedie a na 18 doménách**. Píšu to sem,
aby ta mezera byla vidět, ne aby se z ní stal tvůj úkol.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: W‑55.** Ne kvůli té jedné větě — kvůli tomu, jaká
**obecná schopnost čtení** se za ní schovává: **syntaktická hlava není
referent, a přívlastek v apozici nese predikaci o něm.**

**Rozhoduješ, CO se s tou predikací stane** — zapsat, nebo nabídnout
a zeptat se. **Obojí je obhajitelné; co obhajitelné není, je dnešní
stav, kdy o ní systém řekne „nikdo to neřekl".** Zapiš důvod.

**Varuju tě před tou lákavou variantou:** zapsat `member` rovnou ze
tvaru je **odvození z konstrukce**, tedy přesně to, co jsi u `same_as`
z apozice správně odmítl. Rozdíl je, že tady rozbor tu stavbu
**rozlišuje** (`flat` × `nmod`, `Sing` × `Plur`) — ale to je argument
k prozkoumání, ne k zápisu.

**Tři případy, bez nich to nepovažuju za ověřené:**

| | věta | co se musí stát |
|---|---|---|
| **kladný** | „Nad hrobem promluvil básník Josef Hora." | *Je Josef Hora básník?* **přestane tvrdit „nikdo to neřekl"** |
| **sporný** | „prezident Masaryk zemřel." | titul platí **v čase**, ne napořád — ať je vidět, jak se s tím naložilo |
| **záporný** | „Město Praha leží v Čechách." · „bratří Čapků" | **nesmí** z toho vzniknout `member` — `nmod` ani plurál tou cestou nejdou |

**Můj counterexample — a tentokrát je psaný jako VLASTNOST:**
**o žádné třídě, kterou věta nekvantifikuje, nesmí vzniknout tvrzení**,
ať se ta třída jmenuje `básník`, `Josef_Hora`, nebo jakkoli jinak;
**žádné nové `ZAPSÁNO` nesmí být falešné** — u každé věty, která se
nově zapíše, chci v hlášení větu z textu, která to říká; osmnáct domén
se závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 55/55; nula `RECALL_FAILURE`; doložky ≥ 75/75; `mypy --strict`
čistý; **korpus přeměřen a hlášený rozkladem ZMĚNĚNÝCH ČTENÍ, ne jen
verdiktů** — to jsi minule udělal sám a je to teď standard.

---

## ARCHIV — kolo #91

### Status: 🟢 PASS — B‑22 uzavřena

**Kolo #91.** 1025 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **74/74**, **živá parita 55/55**, dialogy 17 / 44 / 26, jádrové
relace 9/9, nula `RECALL_FAILURE`, **celá stálá regrese zelená**.
Jádro 0.1.27, HEAD `e9a463a`.

**Architectural Health Score: 9,4 / 10** — nejvýš, co tenhle projekt měl.
Ne za opravu; za **odmítnutí té lákavé.**

---

## B‑22 ověřena reprodukcí

```
Karel Čapek, rodným jménem Karel Antonín Čapek…  → ·Karel_Čapek     (bylo ·Karel_Čapek_Karel)
Karel Čapek byl spisovatel.                       → ·Karel_Čapek     zapsáno
Karel Poláček byl spisovatel.                     → ·Karel_Poláček   jiný uzel
Město Praha leží v Čechách.                       → nesloženo
Karel Čapek, spisovatel, zemřel.                  → nesloženo
báze po té apozici: ŽÁDNÝ výrok, tedy ani žádné same_as
```

**Korpus, `c445582 → e9a463a`, přečteno mnou z obou záznamů:** verdikt 0,
blokátor 0, **změněný důvod 1**. **Tvé „ze 26 vět právě jedna" sedí
přesně** — a hlásíš to jako číslo, ne jako obhajobu, což je správně:
rozsah byl jedna věta, ale pravidlo platilo všude.

**Konstanta obstála i v tom, na co ses neptal:** používá `base_deprel`,
takže podtypy `flat:*` by prošly. V korpusu je `flat` 167× a `appos` 72×,
**bez jediného podtypu** — takže tu dnes není co skrývat.

---

## Odmítnutí `same_as` je to nejlepší z tohohle kola

Zeptal jsem se, jestli `appos` mezi dvěma `PROPN` není spíš `same_as`.
**Tvoje „ne, zatím" je lepší odpověď než moje otázka**, a důvod je
přesný: rozbor **nerozlišuje** *„rodným jménem Karel Antonín Čapek"*
(druhé jméno) od *„spisovatel"* (role) — obojí je `appos`. Ztotožnit
uzly z tvaru by byl **tichý default u identity**, tedy nejdražší chyba,
jakou tenhle systém umí (M‑2, I‑13).

**A pověsils na to test**, který ověřuje, že se dnes ze apozice žádné
`same_as` nezapíše. Tím je z toho **doložená mez, ne zamýšlená** — přesně
ten rozdíl, který tady vymáhám po ostatních i po sobě.

---

## Critical Blockers

**Žádné.** B‑21, B‑22 uzavřeny.

---

## Semantic Warnings

**W‑53 · jméno pod obecným jménem — 28 vět, změřeno.** Beru tvůj návrh
udělat z ní vlastní směr a souhlasím s důvodem: *„básník Josef Hora"*
není otázka o skládání, ale o tom, **co je hlavou**.

**W‑43** leží u Agenta 3 s lokací.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: W‑53**, jak jsi navrhl.

**Pojmenuju, co na ní je doopravdy drahé**, protože to není ztracené
jméno:

```
» Nad hrobem promluvili básník Josef Hora, …
   promluvit(kdo:∀básník, nad+Ins:∃hrob)      ← O VŠECH BÁSNÍCÍCH
```

**Ta věta se dnes čte jako tvrzení o celé skupině.** Jméno nespadlo jen
tak — spadlo a **na jeho místě zůstal kvantifikátor, který tam nepatří**.
Zápis to zatím drží (`ZAHOZENO`), ale je to táž rodina jako W‑48: **fakt
o někom jiném, než o kom věta mluví.**

**Rozhoduješ jednu věc: co je v „básník Josef Hora" hlavou.** Obě
odpovědi jsou obhajitelné a **ani jedna není složenina** — `básník_Josef_Hora`
by byla třída, která není ani básník, ani Hora, přesně jako `město_Praha`.

1. **Hlavou je jméno**, `básník` je o něm výpověď (blízké `member`).
2. **Hlavou zůstane `básník`**, ale jméno se **nesmí ztratit** ani zůstat
   pod `∀`.

**Můj counterexample:** *„Nad hrobem promluvili básník Josef Hora…"*
**nedá `kdo:∀básník`** — buď je tam ten člověk, nebo se systém zeptá, ale
**tvrzení o všech básnících z toho nevznikne**; *„Město Praha leží
v Čechách."* se **nezmění** (je to táž stavba a musí zůstat, jak je,
dokud se nerozhodne jinak — a jestli se změní, ať je to napsané jako
rozhodnutí); *„Karel Čapek byl spisovatel."* dál `Karel_Čapek` a zapíše
se; `same_as` se z apozice dál **nezapisuje**; osmnáct domén se závěry
předchozích sedmnácti **beze změny**; jádrové relace 9/9; gate *Farmaka*
`N`/`s0005`; parita ≥ 55/55; nula `RECALL_FAILURE`; doložky ≥ 74/74;
`mypy --strict` čistý; **korpus přeměřen** a z těch 28 vět ať je vidět,
kolika se to týkalo — a jestli některá přešla ze `ZAPSÁNO` do `PTÁ SE`,
**pojmenuj to jako zlepšení**, i když číslo klesne.

---

## ARCHIV — kolo #90

### Status: 🔴 FAIL — B‑22, apozice složená do jména

**Kolo #90.** 1022 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **74/74**, **živá parita 55/55**, dialogy **17 / 44 / 26**,
jádrové relace 9/9, nula `RECALL_FAILURE`, **celá stálá regrese zelená**.
Jádro 0.1.26, HEAD `c445582`.

**Architectural Health Score: 9,2 / 10.**

**FAIL je za jednu větu z tvého vlastního korpusu**, ne za směr. Volba
`flat` místo `acl` podle kumulativního pokrytí byla správná a odkryla
přesně to, cos říkal — tichý zápis o jiném uzlu je horší než ztracený
člen.

---

## Co je hotové a ověřené

**W‑52, obě půlky, změřeno mnou:**

```
run()  BEZ lexikonu        4 výroky · shoda False · hláška V PŘEPISU  ← dřív mlčelo
run()  se SPRÁVNÝM         8 výroků · shoda True  · nehlásí nic
replay bez lexikonu        4 výroky · shoda False · hláška V PŘEPISU
```

**Hlídka na `run` je správné místo** a tvůj důvod je přesný: *zeď, kterou
jde obejít o patro níž, není zeď.* A **nezakázat `run`** je taky správně
— schovat cestu znamená řešit hlášením problém, který je o kontrole.

**B‑21 v jádru funguje** a ověřil jsem i tu půlku, která je dražší:

```
Karel Čapek byl spisovatel.   → member(elem:·Karel_Čapek, …)      zapsáno
Karel Poláček byl spisovatel. → member(elem:·Karel_Poláček, …)    JINÝ UZEL
Město Praha leží v Čechách.   → „Praha“ ZAHOZENA, nesloženo        stráž drží
Karel Čapek, spisovatel, …    → „spisovatel“ nesloženo             stráž drží
```

**Korpusová čísla sedí na kus přesně** — přečetl jsem oba záznamy sám:
**verdikt 0, blokátor 0, změněný důvod 13**, verdikty
`PTÁ SE 215 / NEPŘEČTENO 21 / CHYBA 2`.

---

## Critical Blockers

### B‑22 · `appos` se skládá do jména, i když je to DRUHÁ ZMÍNKA

**Nalezeno v tvém vlastním korpusu, ne vymyšleno:**

```
» Karel Čapek, rodným jménem Karel Antonín Čapek( 9. ledna 1890 …
   Karel   PROPN nsubj  head=23        Karel   PROPN appos  head=1
   Čapek   PROPN flat   head=1         Antonín PROPN flat   head=6
                                       Čapek   PROPN flat   head=6
   ◐ member(elem:·Karel_Čapek_Karel, group:·český_spisovatel)
   [ZAHOZENO: … „Antonín“ (flat pod „Karel“), „Čapek“ (flat pod „Karel“) …]
```

**`Karel_Čapek_Karel` není jméno nikoho.** Skládání vzalo hlavu, její
`flat` díl **a k tomu `appos`, což je DRUHÁ ZMÍNKA téhož člověka pod
jiným jménem** — a její vlastní díly nechalo spadnout. Vznikl uzel,
který v textu nikdo nenese.

**Je to táž rodina jako B‑21, jen z druhé strany.** Tam se dva lidé
tiše slili v jednoho; tady se jeden člověk rozdělí na uzel, který se
s jeho vlastním jménem nepotká — *„Byl Karel Čapek spisovatel?"* na
`Karel_Čapek_Karel` nesedne.

**A je to NOVÉ tímhle kolem**: před B‑21 se nic neskládalo.

**Stráž je úzká na slovní druh, ale ne na vztah.** `PROPN` odchytí
*„město Praha"*, jenže `appos` mezi dvěma `PROPN` je **jiná zmínka, ne
další díl jména** — a přesně tohle jsi u `advcl:pred` sám rozhodl
opačně a správně: *rozhoduje vztah, ne značka členu.*

**Dnes se ta věta nezapíše** (drží ji `ZAHOZENO`), takže do báze nic
špatného nejde. **Do blokerů to jde proto, že to pravidlo vyrobí ten
uzel všude, kde zbytek věty projde** — a to je otázka času, ne náhody.

---

## Semantic Warnings

### W‑53 · jméno pod obecným jménem zůstává ztracené — a je to většina

**Změřeno mnou na témž korpusu**, rozdělené podle slovního druhu hlavy:

```
zahozený člen s hranou flat, celkem 54 vět
   hlava PROPN     26
   hlava NENÍ PROPN 28   ← „bratr Josef Čapek“, „básník Josef Hora“,
                            „Matka Božena Čapková“, „prezident Masaryk“
```

**To není „město Praha".** *„Nad hrobem promluvili básník Josef Hora…"*
se dnes čte jako `promluvit(kdo:∀básník, …)` — **o všech básnících** —
a jméno spadne. Stráž tam drží správně (složit `básník_Josef_Hora` by
bylo horší), ale **výsledek je, že u čtvrtiny korpusu jméno člověka
do čtení nevstoupí vůbec.**

Není to bloker a **není to od tohohle kola** — hlásím to jako změřenou
hranici, ne jako vadu. Tvé číslo 19 → 12 a moje 54 měří dvě různé
otázky; tvoje sedí na `flat` pod `PROPN`, moje na všechny.

**W‑43** leží u Agenta 3 s lokací.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: B‑22.**

**Nepředepisuju ti, že `appos` do skládání nepatří** — může být UD čtení,
kde díl jména přijde právě takhle. **Nepřípustné je jen to, co dnes
vzniká: uzel, jehož jméno v textu nikdo nenese.** Rozhodni a důvod zapiš.

**Jedna obecná věc k tomu**, protože je to potřetí týž tvar: `flat` je
**pokračování jména**, `appos` je **jiná zmínka**. Rozhoduje **vztah**,
ne slovní druh členu — přesně jak jsi to rozhodl u `advcl:pred`.
Ať je i tohle **pojmenovaná konstanta s důvodem u ní**, jako
`PREDICATE_AUXILIARIES` a `SUBJECT_DEPRELS`.

**A jestli `appos` mezi dvěma `PROPN` znamená „týž člověk pod jiným
jménem", pak to není složenina — je to `same_as`**, a to jádro umí. To
je rozhodnutí, ne úkol; zvaž ho a napiš, proč ano nebo ne.

**Můj counterexample:** *„Karel Čapek, rodným jménem Karel Antonín
Čapek…"* **nevyrobí uzel `Karel_Čapek_Karel`** — buď `Karel_Čapek`
a druhá zmínka zvlášť, nebo `same_as`, ale **nic, co v textu nestojí**;
*„Karel Čapek byl spisovatel."* dál `Karel_Čapek` a zapíše se;
*„Karel Poláček"* dál jiný uzel; *„Město Praha"* a *„Karel Čapek,
spisovatel"* dál nesloží; sedmnáct domén se závěry beze změny; jádrové
relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 55/55; nula
`RECALL_FAILURE`; doložky ≥ 74/74; `mypy --strict` čistý; a **korpus
přeměřen** — z těch 26 vět, kde je hlava `PROPN`, ať je vidět, kolika
se to týkalo.

---

## ARCHIV — kolo #89

### Status: 🟢 PASS — otisk lexikonu drží

**Kolo #89.** 1011 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **73/73**, **živá parita 55/55** (přeměřena mnou proti záznamům),
dialogy 16 / 43 / 24, jádrové relace 9/9, nula `RECALL_FAILURE`, **celá
stálá regrese zelená**. Jádro 0.1.25, HEAD `fb8b760`.

**Architectural Health Score: 9,3 / 10.**

---

## W‑51 ověřena reprodukcí

```
otisk na tazích:                 ['e9376c4a4856ce60', '', '']   ← ražen JEN první tah
replay(žurnál, lexicon=týž)      8 výroků · shoda True  · poznámek 0   ← při shodě MLČÍ
replay(žurnál, lexicon=prázdný)  4 výroky · shoda False · poznámek 1
   [JINÝ LEXIKON: žurnál vznikl s otiskem e9376c4a…, přehrává se s ab7ecd2a… —
    přehrání pokračuje, ale determinismus (I‑4) platí jen pro týž výchozí stav]
replay(žurnál)                   4 výroky · totéž, s otiskem prázdného lexikonu
```

**Rozhodnutí „přehrát a říct to" je správné a důvod je ten pravý:**
lexikon se **legitimně rozrůstá**, takže přehrát starý žurnál v sezení,
které se mezitím naučilo víc, je normální provoz. **Odmítnout by nutilo
lexikon uměle ořezávat, aby šel žurnál vůbec přehrát** — to by byla
horší nemoc než nemoc.

**Rozlišení proti bázi, kde se odmítá, sedí přesně:** tam by tiché
pokračování **zapsalo něco špatného**; tady se nezapíše nic špatného,
nanejvýš se přečte víc vět. **To se dá říct.**

**Ražení jen prvního tahu je rozhodnutí, ne úspora**, a je správné —
lexikon se učením rozrůstá, takže otisk z pozdějšího tahu by popisoval
něco jiného než ten výchozí stav, o který jde. Že je na to vlastní test,
je namístě.

**Test měří vadu, ne řetězec** — ověřuje i to, že se báze doopravdy
liší. To je ten rozdíl, který jsme si vynutili u W‑15 a je dobře, že ho
teď píšeš sám.

---

## Critical Blockers

**Žádné.** W‑51, B‑19, B‑20 i W‑50 uzavřeny.

---

## Semantic Warnings

### W‑52 · hlídka sedí na obalu, ne na operaci — a hláška nemá kudy ven

**Dvě věci, obě ověřené mnou, ani jednu nehlásíš.**

**(a) `Session.run(žurnál)` neкontroluje nic.**

```
Session().run(žurnál)     4 výroky · shoda False · POZNÁMEK 0     mlčky
Session.replay(žurnál)    4 výroky · shoda False · poznámek 1     řekne
```

`replay` je `check_journal_lexicon` + `run`; **hlídka je na obalu, kdežto
žurnál umí přehrát i to, co je pod ním**. Není to teoretická cesta —
**přesně tou jsem v #87 tu vadu reprodukoval**, a `replay` sám ji používá.
Tvůj vlastní counterexample zní „mlčky projít nesmí"; dnes platí pro
`replay`, ne pro `run`.

**(b) `Session.notes` nikdo nečte.** Zapisuje se na `session.py:836`
a v celém `core_semantics/` mimo testy se **nečte nikde**;
`session.py:1167` čte `grounded.notes`, což je jiný objekt. Do
`TurnResult.lines` se hláška nedostane — ověřeno. **Řečeno tedy je,
ale jen tomu, kdo se sám podívá do pole, o kterém ví.**

**Není to bloker** — nic nelže a nic špatného se nezapíše. Ale W‑51 měla
zavřít „tiché přehrání" a **zavřela ho na jedné ze dvou cest**.

**W‑43** leží u Agenta 3 s lokací.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**PROTOŽE JE W‑52 MALÁ A PATŘÍ K TOMU, COS PRÁVĚ DODĚLAL, VEZMI JI
S SEBOU DO DALŠÍ DOMÉNY — ne jako vlastní kolo.** Nechci kvůli dvěma
řádkům rozbíjet pořadí, které jsi navrhl dobře.

**Rozhoduješ dvě věci, obě malé:** kde má hlídka sedět (jestli na `run`,
nebo jestli `run` přestat nabízet jako veřejnou cestu k žurnálu), a kudy
se hláška dostane k člověku. **Vyber a důvod zapiš.**

**HLAVNÍ SMĚR: DALŠÍ DOMÉNA + PŘEMĚŘENÍ KORPUSU**, jak jsi navrhl.
**Pořadí rederivuj z kumulativního pokrytí, ne ze seznamu** — souhlasím
a je to tvá vlastní dohoda z #81. `acl` (7), `csubj` (2), víceslovné
jméno (11) jsou kandidáti; **které z nich vezmeš, ať řekne to číslo,
ne pořadí zápisu**.

**Můj counterexample:** `Session().run(žurnál)` s jiným výchozím
lexikonem **buď hlásí totéž co `replay`, nebo tou cestou nejde** —
mlčky projít nesmí ani jednou z nich; při shodě se dál **nehlásí nic**;
hláška je čitelná **odtud, kam se člověk dívá**, ne jen z `Session.notes`;
sedmnáct domén se závěry předchozích šestnácti **beze změny**; jádrové
relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 55/55; nula
`RECALL_FAILURE`; doložky ≥ 73/73; `mypy --strict` čistý; a **korpus
přeměřen nad čistou revizí** s diffem po větách.

---

## ARCHIV — kolo #88

### Status: 🟢 PASS — B‑20 rozhodnuta, doména dosedla

**Kolo #88.** 1006 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **72/72**, **živá parita 55/55** (přeměřeno mnou proti záznamům,
token po tokenu), dialogy **16 domén / 43 zapsaných tahů / 24 závěrů**,
jádrové relace 9/9, nula `RECALL_FAILURE`, **celá stálá regrese zelená**.
Jádro 0.1.24, HEAD `10d92be`.

**Architectural Health Score: 9,3 / 10.**

---

## B‑20 ověřena — counterexample splněn doslova

```
živě                                     8 výroků
Session.replay(žurnál, lexicon=týž)      8   shoda VÝROK PO VÝROKU · program ✓ · answers ✓
Session.replay(žurnál)                   4   shoda False   ← test měří tuhle vadu, ne jinou
```

**Volba (2) je správná a tvůj hlavní důvod je ten nejlepší, jaký šlo
uvést**: stará smlouva si podmínku své platnosti **napsala sama** —
„kdyby žurnál někdy začal nést text, přestane to platit" — a `→@` ten
text nese, protože ze své podstaty re‑čte (N‑5). **Nebylo to proroctví,
byla to podmínka, a ta padla.**

**Zamítnutí (1) je taky správně a lepší, než jsem čekal.** Uložit
výsledné čtení místo pokynu je opravdu menší změna, ale zrušilo by
přesně tu vlastnost, kvůli které `→@` existuje: **naučit TVAR, ne
dokončit jednu větu.** Menší změna, která ubere smysl, není menší změna.

**Šestnáctá doména „Proč odjel" drží čtyři věci naráz** a ověřil jsem
každý krok: věta se zeptá a **nezapíše** (B‑19); `→@` zapíše
`odjet(kdo:Petr, proč:∃pršet)`; druhá věta s touž spojkou se zapíše
a **neptá se** — tvar se naučil; a *„Je jasné, že Jan přišel."*
netvrdí, že podmět chybí, **a nezapíše se** (B‑18 + W‑50 jedním krokem).
`limit` vylučuje `advcl:pred` výslovně a s důvodem i s čísly.

**Že jsi korpus nepřeměřoval, je správné rozhodnutí, ne mezera.**
B‑20 mění přehrávání, ne čtení; měřit ho jen proto, aby v předávce bylo
číslo, by bylo měření pro formu. Souhlasím i s tím, kdy ho přeměříš.

---

## Critical Blockers

**Žádné.** B‑19, B‑20 i W‑50 uzavřeny.

---

## Semantic Warnings

### W‑51 · žurnál nenese totožnost lexikonu, se kterým vznikl

**Ověřeno mnou, nehlásils to:**

```
replay(žurnál, lexicon=týž)        8 výroků   správně
replay(žurnál, lexicon=prázdný)    4 výroky   MLČKY, bez jediného slova
```

Determinismus teď platí **podmíněně** — „stejný žurnál **a stejný
výchozí stav**" — jenže **který výchozí stav to byl, žurnál neříká**.
Dvě přehrání téhož žurnálu s různým lexikonem vypadají obě
autoritativně a nic je nerozliší.

**Není to bloker** — při správném užití se nic špatného nezapíše, nic
nelže — **ale je to přesně ta lekce, kterou jsme letos přijali na
měřicí straně**: *identita běhu nesmí být nic, co se dá dvakrát
obsadit.* Tam to vedlo k otisku `git diff HEAD`; tady stačí otisk
lexikonu v žurnálu a porovnání při přehrání.

**W‑43** leží u Agenta 3 s lokací.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: W‑51 — otisk lexikonu v žurnálu.** Je malý, uzavírá
B‑20 doopravdy (dnes je zavřená jen pro toho, kdo předá správný lexikon)
a **navazuje na rozhodnutí, které jsi právě udělal**: když je lexikon
výchozím stavem, musí být poznat, který to byl.

**Rozhoduješ jednu věc**: co se stane při neshodě. **Odmítnout
přehrání** je přísnější a odpovídá tomu, jak se tu zachází s bází;
**přehrát a nahlas to označit** je mírnější a hodí se, když se lexikon
legitimně rozrostl. **Vyber jedno a důvod zapiš** — obojí je obhajitelné,
tiché přehrání není.

**Můj counterexample:** `replay` s jiným lexikonem **buď selže, nebo to
řekne** — mlčky projít nesmí; `replay` se **správným** lexikonem dá dál
8 = 8 a `program()` i `answers()` se shodují; otisk je **v žurnálu**, ne
v sezení, takže přežije uložení; šestnáct domén se závěry beze změny;
jádrové relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 55/55; nula
`RECALL_FAILURE`; doložky ≥ 72/72; `mypy --strict` čistý.

**Potom** je na řadě další doména — a s ní přeměření korpusu, jak jsi
sám navrhl.

---

## ARCHIV — kolo #87

### Status: 🟢 PASS — B‑19 opravena, odkryla B‑20

**Kolo #87.** 1001 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **72/72**, parita **53/53**, dialogy 15 / 41 / 24, jádrové relace
9/9, nula `RECALL_FAILURE`, **celá stálá regrese zelená**. Jádro 0.1.23,
HEAD `5b9de52`.

**Architectural Health Score: 9,2 / 10** — drží.

**PASS, ne PARTIAL, a mám pro to důvod:** kolo nepřineslo ani jednu novou
vadu, opravilo jednu skutečnou a **odkrylo starší, kterou dosud kryl
právě ten dvojí zápis**. Nedodaná doména není vada — akceptační test,
který nedrží, by vada byl.

---

## B‑19 ověřena reprodukcí

```
Petr odjel, protože pršelo.   → NEZAPSÁNO, ptá se na jméno role
→@ proč                        → ✓ zapsáno [s0001] odjet(kdo:Petr, proč:∃pršet)   JEDNOU
Jan odjel, protože sněžilo.    → ✓ zapsáno [s0005]                                 neptá se
báze: 8 výroků, každá věta právě jednou
```

**Diagnóza vlastní vady z #82 je správná** a stojí za to ji ocenit:
patro udělalo z vedlejší věty roli, ale zábranu, kterou měla jako
ztracený člen, jí nedalo. **A tvá první verze — vázat na
`CANONICAL_ROLES` — byla vážně špatně**; žes to sám změřil a otočil, je
podstatnější než ta oprava: naučené `proč` mezi jádrové role nepatří
a patřit nemá (§ 12/1).

---

## Critical Blockers

### B‑20 · žurnál nereprodukuje sezení — a NENÍ to od tvé opravy

**Reprodukováno mnou:**

```
živě                            8 výroků
Session.replay(žurnál)          4 výroky      ← Petrova věta chybí celá
program shoda False · odpovědi shoda False
```

**TVOJE HYPOTÉZA JE VYVRÁCENÁ, a je to dobrá zpráva.** Psals, že po
přehrání přijde role rovnou jako `proč` a tvá zábrana nemá co uvolnit.
Vyexportoval jsem si revizi `afdc895` — **stav PŘED B‑19** — a pustil
tam totéž:

```
PŘED B-19:   živě 12 výroků  ·  po přehrání 8  ·  shoda False
```

**Rozchod tam byl už tehdy**, kdy tvoje zábrana neexistovala. Kryl ho
**právě ten dvojí zápis**: věta o Petrovi se zapsala už v tahu 1, takže
po přehrání v bázi *něco* o Petrovi zůstalo — ten špatný výrok — a nikdo
si toho nevšiml. **Tvoje oprava tu vadu neudělala; udělala ji
viditelnou.**

**PŘÍČINU JSEM ZMĚŘIL, takže ji nemusíš hledat.** Přehraný tah 2 se
rozchází takhle:

```
živě     ◐ odjet(kdo:·Petr, proč:∃pršet)   Petr → Petr (založen)    → zapsáno
přehráno ◐ odjet(kdo:Petr,  proč:∃pršet)   [NEZAKOTVENO: role kdo]  → nezapsáno
         ? Nevím, o kom to platí — kdo (PROPN/Sing/Nom/nsubj) …
```

Kontrolní pokus, který to rozhodl:

```
Session.replay(žurnál)                4    (lexikon ŽÁDNÝ)
Session(lexicon=týž).run(žurnál)      8    SHODA S ŽIVÝM BĚHEM, výrok po výroku
```

**Rozdíl dělá lexikon**, který `Session.replay` **záměrně zahazuje**.

**A tady je ta skutečná vada — dvě smlouvy si v kódu odporují:**

| kde | co tvrdí |
|---|---|
| `Session.replay` | „Lexikon není parametr, a je to smlouva. Žurnál nese ROZHODNUTÉ tahy, ne věty — **není co číst znovu**." |
| `names_role` | „…a **čekající větu přečte ZNOVU** — teprve pak se zapisuje." |

**Obě platit nemohou.** `→@` je tah, který ze své podstaty čte znovu —
a čte bez lexikonu, se kterým se četlo poprvé. Determinismus žurnálu
(I‑4) tím padá u každého tahu, který re‑čte.

---

## Semantic Warnings

**W‑50 zůstává otevřená** a hlásíš to správně — krok je napsaný, doména
nedosedla, takže se nic nevyřešilo.

**W‑43** předána Agentovi 3 i s lokací.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: B‑20.** Tvůj návrh byl správný a měřením je teď
z otázky odpověď — **nezkoumej to, rozhodni to.**

**Rozhodnutí je o tom, CO ŽURNÁL JE**, a jsou dvě čisté odpovědi:

1. **Žurnál nese rozhodnuté tahy → pak žádný tah nesmí re‑číst.**
   `→@` by do žurnálu zapsal **výsledné čtení**, ne pokyn k přečtení.
   Smlouva `replay` zůstane pravdivá.
2. **Žurnál je stopa dialogu → pak k němu patří i lexikon**, protože
   bez něj není čím číst. `replay` by ho přijímal a smlouva by se
   přepsala.

**Nevybírám za tebe, ale první je menší změna a druhá je poctivější
k tomu, co `→@` doopravdy dělá.** Ať vybereš cokoli, **ta druhá
docstring musí přestat tvrdit opak** — dnes jedna z nich lže.

**Můj counterexample:** `Session.replay(s.journal)` dá **výrok po
výroku touž bázi** jako živé sezení pro dialog Petr / `→@ proč` / Jan —
8 = 8, ne 4; `program()` i `answers()` se shodují; **týž test musí na
`afdc895` selhat**, protože tam je vada doložená (12 → 8), takže se
pozná, že měří ji a ne něco jiného; patnáct domén se závěry beze změny;
jádrové relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 53/53; nula
`RECALL_FAILURE`; doložky ≥ 72/72; `mypy --strict` čistý.

**Doména na `advcl` dosedne hned po tom** — je napsaná a čekala právě
na tohle.

---

## ARCHIV — kolo #86

### Status: 🟢 PASS — B‑18 uzavřena

**Kolo #86.** 1000 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **72/72**, parita **53/53**, dialogy 15 / 41 / 24, jádrové relace
9/9, nula `RECALL_FAILURE`, **celá stálá regrese zelená** (B‑1, B‑2,
dialog B, disjoint→N, CONFLICT se dvěma důkazy, stráže 6/6,
nedestruktivní `same_as`, M‑1, G‑3, zákaz OR, I‑16, ∀→∃ U/N,
ireflexivita, opačná hrana, W‑19, W‑24, `complete`). Jádro 0.1.22,
HEAD `afdc895`.

**Architectural Health Score: 9,2 / 10** — poprvé nad 9,0. Ne za opravu
samotnou, ale za to, **jak byla vybrána**: dostals dvě legitimní cesty
a vybral tu, která místo mlčení říká pravdu o vlastní mezi.

---

## Ověřeno reprodukcí — všech šest vět counterexamplu

```
Je jasné, že Jan přišel.        [PODMĚT JE CELÁ VĚTA: „přišel“ … zatím neumím]
                                „bez podmětu“ NE · nabídka antecedentu NE
Je známo, že gestapo…           totéž, s „plánovalo“
Byl pohřben v Praze.            [BEZ PODMĚTU: „pohřben“ ho nevyslovil]  · ptá se dál
Jan byl pohřben v Praze.        neptá se                                · beze změny
Bylo chladno.                   neptá se                                · beze změny
Narodil se v Praze.             [BEZ PODMĚTU: „Narodil“ ho nevyslovil]  · beze změny
```

**Tvé číslo 17 → 12 jsem přeměřil sám a sedí přesně**: ze 60 vět
s neslovesným kořenem je 12 bez podmětu a **5 s podmětem větným**.

**Ověřil jsem i to, na co ses neptal — jestli se tou změnou neotevřela
díra zpátky k W‑48.** Prošel jsem **všech osm** vět korpusu s `csubj`
(pět s neslovesným kořenem, tři se slovesným, které ležely od #72):
**ani jedna se nezapsala, ani jedna netvrdí „BEZ PODMĚTU"**. Kdyby
poznámka zápis pustila, byl by to fakt o nikom podruhé, jen jinými
dveřmi — není.

**Konstanta je pojmenovaná a důvod stojí v kódu u ní**, ne v commitu, a
test to vyžaduje čtením souboru. To je správný tvar pro věc, která se
opakuje počtvrté.

---

## Critical Blockers

**Žádné.** B‑18 uzavřena.

---

## Semantic Warnings

**W‑50 · zápis drží DVĚ zdi, ale spojku mezi nimi nedrží test.**
Poznámka o větném podmětu je **nezávazná** — patro vrací kandidáty beze
změny. Že se ta věta přesto nezapíše, obstarává **jiná zeď**:
`[ZAHOZENO]`, protože pro vedlejší větu zatím role není. Ověřeno
u všech šesti vět, kde poznámka padne — všech šest má i `ZAHOZENO`.

**Ty dvě věci jsou dnes spřažené věcně** („neumím ji dosadit" je právě
to, co `ZAHOZENO` zaznamenává), **ale nedrží je nic než ta shoda
okolností**. Až někdo vedlejší větě roli dá, aniž z ní udělá podmět,
věta se zapíše bez podmětu a nic to neřekne. **Není to bloker — nic
špatného se dnes nezapíše — ale je to přesně ta konstrukce, kterou tenhle
projekt jinde dělá výslovnou.**

**W‑43 potvrzena potřetí, a tentokrát MÁM PŘÍČINU, ne jen příznak.**
Tvoje hlášení „diff ukázal dvě z pěti" jsem ověřil a je pravdivé;
příčina je v měřicí vrstvě a je doslova změřitelná:

```
reason: 212 z 238 vět má délku PŘESNĚ 160 znaků
        209 z 238 končí uprostřed slova
příčina: cb_utils/diagnose.py — [:160] na čtyřech místech (ř. 105, 111, 130, 131)
```

**Záznam tedy mlčky ořezává důvod**, takže se na něm nedá hledat
podřetězec ani počítat výskyt. Předávám Agentovi 3 i s tou lokací.

**Že jsi to ohlásil sám a odmítl tvrdit číslo, které neumíš změřit, je
přesně ten postup, který tu chci** — autoritativní je přímé měření na
jádře, a to jsi udělal.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: doména na `advcl` s `limit`em o `advcl:pred`**, jak
je schváleno od #84. Průzkumná práce na téhle třídě je hotová a další
kolo už má být o tom, co systém **umí**, ne co netvrdí.

**W‑50 vyřeš uvnitř téhle domény, ne zvlášť** — jedním testem, který
říká, že věta s větným podmětem se **nezapíše**, dokud ta vedlejší věta
nemá roli. Je to jeden `assert`, ne nová vrstva: dnes to platí,
zítra to má být doloženo.

**Můj counterexample pro doménu** — a čísla jsou tentokrát **podmínky,
ne odhad**: doména má **vlastní `limit`**, který výslovně říká, že
`advcl:pred` je doplněk a do okolnostní role nepatří; každý krok, který
píše, má v `writes` **doložený tvar**; žádný krok nezavádí jádrový
predikát pravidlem (I‑16); dialogů je **16**, závěry předchozích
patnácti **beze změny**; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 53/53; nula `RECALL_FAILURE`; doložky ≥ 72/72; `mypy --strict`
čistý; a **korpus přeměřen nad čistou revizí** — s tím, že po opravě
`reason` v měřicí vrstvě bude diff konečně čitelný.

---

## ARCHIV — kolo #85

### Status: 🔴 FAIL — nepravdivý výrok o textu (B‑18)

**Kolo #85.** 996 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **72/72** (nová S‑37), parita **53/53**, dialogy 15 / 41 / 24,
jádrové relace 9/9, nula `RECALL_FAILURE`, **celá stálá regrese zelená**
(B‑1, B‑2, dialog B, disjoint→N, CONFLICT se dvěma důkazy, stráže 6/6,
nedestruktivní `same_as`, M‑1, G‑3, zákaz OR, I‑16, ∀→∃ U/N,
ireflexivita, opačná hrana, W‑19, W‑24, `complete`). Jádro 0.1.21,
HEAD `94e92a6`.

**Architectural Health Score: 9,0 / 10** — architektura se tímhle kolem
**zlepšila**; FAIL je za jeden konkrétní výrok, ne za návrh.

---

## Co je hotové a hotové dobře

**W‑48 je opravená a ověřil jsem to na minimálních párech**, ne z hlášení:

```
Byl pohřben v Praze.        zapsáno=ne   ptá se na PODMĚT: ANO   ← fakt o nikom je pryč
Jan byl pohřben v Praze.    má nsubj:pass, na podmět se NEPTÁ    ← survey W-47 drží
Narodil se v Praze.         činný pro-drop beze změny
Jan je učitel.              ZAPSÁNO, neptá se
Je učitel.                  zapsáno=ne, ptá se na podmět         ← spona bez podmětu, nově
```

**Tvar řešení je ten, který jsem předepsal**: `_is_predicate` čte, **co
v rozboru je** — kořen je přísudek, když je `VERB`/`AUX`, **nebo když
pod ním visí `aux`/`cop`** (přes `base_deprel`, takže se to se survey
W‑47 nerozejde; je na to vlastní test, což je správně).

**Stráž `Gender`/`Number` se ukázala cennější, než jsi psal.** Odchytí
neosobní větu: *„Bylo chladno."* má kořen `ADV` bez rodu a čísla, takže
se **na podmět neptá** — a to je správně, protože tam žádný podmět
není. Ověřeno. To není náhoda, to je ta stráž.

**Tvé přiznání k diffu beru a je poctivé.** ZAPSÁNO je v tomhle korpusu
nula, takže přechod ZE ZAPSÁNO nemohl nastat; ručním diffem důvodů jsi
to doložil jinak. Přeměřil jsem tvá strukturní čísla sám a **sedí přesně**:
**60** vět s neslovesným kořenem a pomocným slovesem, **17** z nich bez
podmětu.

---

## Critical Blockers

### B‑18 · systém TVRDÍ „věta nemá podmět" o větě, která podmět VYSLOVILA

**Reprodukováno mnou, doslovný výstup:**

```
» Je jasné, že Jan přišel.
   kořen jasné/ADJ Neut/Sing   děti = [Je/cop, přišel/csubj, ./punct]
   ? … Věta nemá podmět — „jasné“ ho nevyslovil. …
```

**Ta věta podmět má.** Je jím celá věta vedlejší — rozbor ji označil
`csubj`. Systém o textu tvrdí něco, co v textu není, a pak na základě
toho nepravdivého tvrzení **nabízí antecedent** — tedy zve člověka, aby
dosadil podmět tam, kde už jeden stojí. To je horší než mlčet.

**Je to NOVÉ tímhle kolem.** Před #85 měl `jasné` slovní druh `ADJ`,
patro se hned vrátilo a nic netvrdilo. Tvoje rozšíření o `cop` ho
dovnitř pustilo — správně — jen se s ním nesla i tahle věta.

**Změřeno na témž korpusu, ne odhadnuto:**

```
neslovesný kořen + pomocné sloveso                      60
   z toho BEZ nsubj → nově se ptá na podmět             17
      z toho MÁ csubj → tvrzení je NEPRAVDIVÉ            5   (29 % z těch 17)
slovesný kořen + csubj bez nsubj (leží od #72, zakryté)  3
```

Například: *„Je známo, že gestapo plánovalo jeho zatčení."*,
*„Pozoruhodné je, že existuje druhopis…"*, *„Je možné si představit
oddělené časoprostory…"*

**Je to POČTVRTÉ táž třída, a na témž místě jako potřetí.** W‑32 rysy
řetězcem, W‑47 deprel řetězcem, W‑48 `upos` výčtem — a teď **výčet
podmětových deprelů**, který zná `nsubj`, ale ne `csubj`. Rozhodnutí
„podmět vyslovený pod jinou značkou je pořád vyslovený" jsi u `nsubj:pass`
udělal správně; jen ses s ním nedostal o jednu značku dál.

---

## Semantic Warnings

**W‑49 · podmět jako věta je zatím zakrytý jinou zdí.** Všech pět těch
vět je dnes `PTÁ SE` z jiného důvodu, takže do báze nic špatného nejde.
Ale až ta zeď padne, nepravdivé tvrzení zůstane — **oprav to teď, dokud
je vidět.**

**W‑43 potvrzena tvým vlastním měřením** a předám ji Agentovi 3: dokud
záznam nese jen verdikt a text důvodu, kolo jako tohle nejde změřit jinak
než ručním diffem. Máš pravdu, že to je vada MĚŘENÍ, ne jádra.

**Tvůj neověřený závěr o Vyšehradu beru jako neověřený** — a je správné,
žes ho tak označil. Plyne z konstrukce, ne z běhu; nepočítám ho za
doložený.

**W‑42, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38,
W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: B‑18. Doména na `advcl` počká** — mít v jádře
nepravdivý výrok o textu je dražší než nemít doménu.

**Nepředepisuju ti, že `csubj` MÁ platit za podmět** — to je rozhodnutí
a obě odpovědi jsou obhajitelné. Nepřípustné je jen to **tvrzení**.
Máš dvě cesty a chci, aby sis vybral vědomě a důvod zapsal:

1. **`csubj` je vyslovený podmět** → patro se vrátí a mlčí, stejně jako
   u `nsubj`.
2. **Podmět je vyslovený, ale jádro ho zatím neumí použít** → řekne
   přesně tohle. Ne „věta nemá podmět", ale „podmětem je celá věta
   vedlejší a tu zatím za podmět dosadit neumím". **Rozdíl mezi
   „neřečeno" a „řečeno, neumím" je přesně ten rozdíl, který tenhle
   projekt jinde drží** (`NEZAKOTVENO` × bez čtení).

**A protože je to počtvrté táž třída, chci k tomu jednu obecnou věc:**
seznam deprelů, které pro tohle patro **znamenají vyslovený podmět**,
ať je pojmenovaná konstanta se zapsaným důvodem — jako `PREDICATE_AUXILIARIES`,
kterou jsi právě udělal správně. Ne literál v podmínce.

**MŮJ COUNTEREXAMPLE — čísla mám změřená, ta platí:**
*„Je jasné, že Jan přišel."* **nesmí tvrdit „věta nemá podmět"**;
*„Je známo, že gestapo plánovalo jeho zatčení."* totéž; *„Byl pohřben
v Praze."* se dál ptá na podmět a nezapíše se; *„Jan byl pohřben
v Praze."* se dál neptá; *„Bylo chladno."* se dál neptá; činný pro‑drop
z #72 beze změny; **z 60 vět s neslovesným kořenem se počet těch, kde
se ptáme na podmět, sníží ze 17 na 12** — a těch 5 dostane **jiný**
výrok, ne žádný; patnáct domén se závěry beze změny; jádrové relace 9/9;
gate *Farmaka* `N`/`s0005`; parita ≥ 53/53; nula `RECALL_FAILURE`; testy
zelené, `mypy --strict` čistý; doložky ≥ 72/72; korpus přeměřen nad
čistou revizí a **v diffu je vidět těch 5 vět se změněným důvodem**.

**Ty 3 věty se slovesným kořenem a `csubj` (leží od #72) vyřeš týmž
rozhodnutím** — je to táž otázka, jen ji dosud nikdo neviděl.

---

## ARCHIV — kolo #84

### Status: 🟢 PASS — survey hotov, nula změn chování

**Kolo #84.** 989 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **71/71**, živá parita **53/53**, dialogy 15 / 41 / 24, gate
*Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese zelená.
Jádro zůstává 0.1.20 (`9be6ecc`).

**Architectural Health Score: 9,0 / 10** — drží se na 9,0 kvůli W‑48.

---

## Survey: rozhodnuto u každého místa, chování beze změny

Ověřeno mnou z obou záznamů — **`2a28455 → 9be6ecc`: změnilo se 0 vět**,
verdikty i blokátory identické. Podmínku „ani o jednu větu" splnil
doslova a doložil ji dvakrát.

```
podtypy DOLOŽENÉ v korpusu (238 vět):
   nsubj 253 / nsubj:pass 38      advcl:pred 30 / advcl 21   ← podtyp častější
   expl:pv 69 / expl:pass 12      det 109 / det:numgov 5 / det:nummod 3
BEZ podtypu: cop · conj · cc · obj · nmod · mark · punct
```

**Devět z šestnácti míst stojí nad základem, který v tomhle korpusu
podtyp nemá** — a nechat je být je **rozhodnutí, ne opomenutí**, jak
píše: měnit porovnání tam, kde se nemá co změnit, přidá šum do diffu
a zakryje místa, kde na tom záleží. Souhlasím.

**Rozhodnutí „dovnitř" mají správný důvod**, zvlášť tohle: `nsubj:pass`
je **vyslovený** podmět, takže bez něj by pro‑drop u **každé trpné věty**
tvrdil, že podmět chybí, a ptal se na antecedent někoho, kdo ve větě
stojí. **Rozhodnutí „ven"** (`advcl:pred` jako doplněk, `det:numgov`
jako kvantifikátor) teď **říká kód**, ne náhoda.

---

## Critical Blockers

### W‑48 · pasivní pro‑drop nevystřelí — do báze jde FAKT O NIKOM

**Nezpůsobilo to tohle kolo**, našel to sám a **záměrně neopravil**,
protože moje podmínka zněla „chování se nezmění ani o jednu větu".
To bylo správné rozhodnutí. Ale je to **nejdražší druh vady, jaký
tenhle projekt má**, a proto to jde do blokerů, ne mezi varování.

**Reprodukováno mnou:**

```
» Byl pohřben na Vyšehradě.   ✓ zapsáno [s0002]  pohřbený(kde:Vyšehrad)
                              ptá se: NE                 ← FAKT O NIKOM
» Narodil se v Praze.         ◐ NEZAPSÁNO, ptá se        ← činný rod se ptá
```

**Příčina je táž třída jako W‑47, jen o patro vedle:** kořen pasiva je
`ADJ` (`pohřben`), ne `VERB` — ověřeno na rozboru — a patro z kola #72
žádá `root.upos in ("VERB","AUX")`. **Přesná shoda na kategorii, která
má variantu**, potřetí.

**A má to viditelný druhý účinek**, který jsem si všiml při reprodukci:
protože se ta věta zapsala bez podmětu, byl v další větě jediným
kandidátem na antecedent **Vyšehrad** — systém tedy nabídl místo jako
toho, kdo se narodil. Zeptal se, takže nic nepokazil, ale **kvalita
nabídky je přímým důsledkem W‑48**.

---

## Semantic Warnings

**W‑47 uzavřena** tímhle survey.

**W‑42, W‑43, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37,
W‑38, W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: W‑48. Tvoje pořadí schvaluji a tvůj důvod je
přesný** — zápis faktu o nikom je nejdražší vada, kterou tenhle systém
umí udělat, a #72 to už jednou rozhodlo pro činný rod.

**Obecný problém, ne jedna věta:** kategorie kořene se porovnává
**výčtem**, který nezná varianty. U trpného rodu je kořen `ADJ`
s `aux:pass` pod sebou — a to je **struktura, ne slovní druh**. Řešení
má být téhož tvaru jako u `advcl`: **čti, co v rozboru je** (`aux:pass`,
`expl:pass`), ne „jakou má kořen značku".

**Tři věci, které z toho udělají obecnou opravu:**

1. Rozpoznat trpný rod **ze struktury** (`aux:pass` / `nsubj:pass`),
   ne z `upos`.
2. Když **je** `nsubj:pass`, podmět **není** vynechaný — to už survey
   rozhodl a nesmí se to rozejít.
3. Když **není**, je to pro‑drop a platí všechno z #72: **navrhne
   kandidáta a zeptá se, bez odpovědi nezapíše nic**.

**Můj counterexample — čísla ODHADUJI, měřit je budeš ty:** „Byl pohřben
na Vyšehradě." se **nezapíše** a **zeptá se** na podmět; „Karel Čapek
byl pohřben na Vyšehradě." (má `nsubj:pass`) se **zapíše** a **neptá**;
činný pro‑drop z #72 beze změny; **žádná věta se nezapíše bez podmětu**,
kde podmět chybí; patnáct domén se závěry beze změny; jádrové relace
9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 53/53; nula `RECALL_FAILURE`;
testy zelené; korpus přeměřen nad čistou revizí a **v diffu je vidět,
které věty přešly ze `ZAPSÁNO` do `PTÁ SE`** — je to zlepšení, i když
číslo `ZAPSÁNO` klesne.

**Doména na `advcl` s `limit`em o `advcl:pred` až po tom**, jak jsi
navrhl.

---

## ARCHIV — kolo #83

### Status: 🟢 PASS — správnost stojící na náhodě; a je to NÁVRAT staré třídy vad

**Kolo #83.** Do jádra **nesáhl** — 989 testů zelených, `mypy --strict`
čistý na 61 souborech, doložky **71/71**, živá parita **53/53**, dialogy
15 / 41 / 24, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá
stálá regrese zelená. Jádro zůstává 0.1.20.

**Architectural Health Score: 9,0 / 10** — sníženo kvůli W‑47 níž.

---

## Jeho odpověď je lepší než otázka, kterou jsem položil

Ptal jsem se „je stráž správně, nebo úzká?". Odpověděl: **účinek je
správný u všech tří, ale u dvou z nich z nesprávného důvodu** — a to je
horší, než kdyby byla prostě úzká. **Správnost, která stojí na náhodě,
se rozpadne při první změně, o které nikdo nebude vědět.** S tou větou
souhlasím bez výhrad.

Reprodukováno mnou (`nalezy/advcl_straz.py --korpus`):

```
advcl:pred   30 výskytů        ← ČASTĚJŠÍ než vlastní advcl
advcl        21
pod čím visí: přísudek 24 · ADJ 15 · VERB 6 · ADV 4 · NOUN 2
```

Dvě ze tří vět mají `advcl:pred`, splňují **obě** podmínky stráže —
pod přísudkem, se spojkou — a stráž je nebere jen proto, že porovnává
`deprel != "advcl"` **řetězcem**. Třetí věta je naopak přesně ten
případ, pro který byla stráž zamýšlená.

**Věcně je vyloučení správné** a jeho argument sedí: `advcl:pred` je
**doplněk**, ne okolnost — *„ukázalo se jako snižující"* neodpovídá na
proč ani kdy, ale na to, **čím** se ta věc ukázala být; sémanticky je
blíž `xcomp`, který se podle mého rozhodnutí z #81 skládá do přísudku.
**Stráž má tedy správný rozsah, jen ho nevyjadřuje.**

**A vzal zpět svou vlastní nejistotu z minulého kola** s vysvětlením
proč (hledal holé `advcl`, ne podtyp). Odvolat pochybnost je stejně
cenné jako ji vyslovit.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Critical Blockers

**Žádné.** Ale W‑47 níž není drobnost a je to důvod, proč jsem snížil
skóre.

---

## Semantic Warnings

### W‑47 · podtypy deprelů se porovnávají řetězcem — a je to NÁVRAT

Tohle už jsme jednou diagnostikovali: **dodatek N** popsal přesně
*„podtypy UD deprelů porovnávané přesnou shodou — celý trpný rod
neviditelný"*. Třída vad se vrátila.

**Změřil jsem si rozsah sám**, a je větší než jedna stráž:

```
v cascade.py: 16 míst porovnává deprel ŘETĚZCOVOU ROVNOSTÍ
   deprel == "cop" · "nsubj" (3×) · "conj" · "cc" · "det" · "obj" · "nmod" · "advcl" …
podtypy DOLOŽENÉ v korpusovém záznamu:
   nsubj:pass  56 ×        obl:arg  38 ×
   ccomp:moci   1 ×        xcomp:pomoci  1 ×
```

**`nsubj:pass` je v záznamu 56×** a `deprel == "nsubj"` je v kaskádě na
třech místech. **Netvrdím, že to je vada** — nevím, jestli se deprel
někde po cestě normalizuje, a podle svého vlastního pravidla to bez
měření tvrdit nebudu. **Tvrdím, že se to musí projít a rozhodnout.**

**W‑46 uzavřena** tímhle rozborem. **W‑42, W‑43, W‑44, W‑45, W‑23,
W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38, W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: projít VŠECHNA místa, kde se deprel porovnává
řetězcem, a u každého rozhodnout — s důvodem v kódu.**

Tvoje dvě navržené drobnosti se do toho vejdou obě: `advcl:pred`
vyloučit **výslovně**, a doména až potom, s `limit`em, který ten důvod
nese. **Schvaluji obojí, jen v tomhle pořadí a v širším rámci** —
protože oprava jednoho místa nechá patnáct dalších viset na téže
náhodě.

**Proč survey, a ne jen ta jedna stráž:** je to **návrat pojmenované
třídy vad**. Když se třída vrátí, opravuje se třída, ne výskyt — jinak
se vrátí potřetí.

**Co má rozbor dát ke každému místu:** který deprel se porovnává,
**jaké podtypy k němu v korpusu doopravdy jsou** (ne teoreticky), a
rozhodnutí **„podtyp patří dovnitř / patří ven"** s důvodem. Kde je
odpověď „ven", ať to kód **říká**, ne ať to vyjde.

**Můj counterexample — čísla jsou MĚŘENÁ (16 míst, 4 podtypy
v záznamu), rozhodnutí jsou na tobě:** tabulka všech míst
s porovnáním deprelu a u každého doložené podtypy z korpusu; explicitní
rozhodnutí u každého; **`advcl:pred` vyloučen výslovně a s důvodem**;
**chování se nezmění ani o jednu větu**, dokud se nerozhodne jinak —
a kde se změní, je to v diffu vidět a zdůvodněné; patnáct domén se
závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 53/53; nula `RECALL_FAILURE`; testy zelené; jádro **zůstává
0.1.20**; korpus přeměřen nad čistou revizí.

**Doména na `advcl` až po tom** — a s `limit`em, který říká, že
`advcl:pred` se úmyslně nebere a proč. To je tvůj návrh a je správný:
hranice bez zapsaného důvodu se čte jako opomenutí.

---

## ARCHIV — kolo #82

### Status: 🟢 PASS — `advcl` stojí; a moje „pět vět" bylo zase číslo bez ověření

**Kolo #82.** 989 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **71/71**, živá parita **53/53**, dialogy 15 / 41 / 24 beze změny,
gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese
zelená. **Jádro zůstává 0.1.20.**

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou

```
» Petr odjel, protože pršelo.   ◐ odjet(advcl:protože:∃pršet, kdo:·Petr)
                                  ? Nevím, co znamená „advcl:protože“ …
» Petr odjel, když pršelo.      ◐ odjet(advcl:když:∃pršet, kdo:·Petr)   ← jiná spojka, ptá se znovu
```

**Práh `DepthExceeded` je 1**, ověřeno ve zdrojáku (`max_depth: int = 1`).
Bod „vnoření do druhé úrovně" byl tedy splnitelný **jen jako hlasitý
pád** — a tak je udělaný. Že si ten práh změřil **před** stavbou, přesně
jak jsem žádal, je ta správná posloupnost.

**Seed mapování nenese** — ověřeno mnou ve zdrojáku `czech_seed()`:
`advcl` ani `protože` tam nejsou. Jméno role se tedy **učí z dialogu**,
nedodává se tiše. To byla moje hlavní obava a je vyvrácená.

**Matice ho chytila a bylo to správně:** první verze doložky měla všechny
vynucující testy nad **vnitřní** funkcí, takže sloupec `použití`
nedržel. Přesně kvůli tomu ten sloupec je.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## „Rodina C klesne o pět vět" — moje číslo, moje chyba, počtvrté

Klesla o **jednu** (15 → 14); `advcl` jako blokátor 5 → 3.

**Předpokládal jsem, že všech pět `advcl` je pod přísudkem.** Měření
říká dvě ano, tři ne — a ty tři nebere **stráž, kterou jsem sám
rozhodl** („`advcl` pod jménem patří k `acl`"). Napsal jsem tedy
podmínku, která je **v rozporu s mým vlastním rozhodnutím o dvě věty
dřív**.

Je to **počtvrté za osm kol** a pravidlo, které jsem si dal („ověř
mechanismus, než napíšeš podmínku"), zjevně nestačí — protože tohle
nebyl mechanismus, ale **číslo**. Rozšiřuji ho: **číslo v counterexamplu
buď změřím, nebo napíšu jako odhad a označím ho tak.**

**Druhý důvod je znovu nález z #77** a ten je v pořádku: i odblokovaná
věta zůstává v `role`, protože nese další rodiny.

**Třetí důvod hlásí jako nejistotu, a to je správně:** u těch tří
neověřil, jestli je `advcl` v tom čtení, které měření použilo — první
čtení z parseru ho nemá vůbec. Netvrdí tedy, že stráž je správná; říká,
že to neví.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑46 · tři věty s `advcl`, které stráž nebere** — nejisté, jestli
právem. Nejbližší otevřená otázka.

**W‑42, W‑43, W‑44, W‑45, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37,
W‑38, W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**Na tvé dvě otázky:**

**Doména na `advcl` — ANO, ale AŽ PO rozboru těch tří.** Tvoje výhrada
je principiálně správná, jen ji obrátím: doména **nerozhoduje o češtině**,
ona **zapisuje odpověď člověka** — přesně jako `shapes` v každé jiné
doméně, a seed ji nenese (ověřeno). Rozhodnutí zůstává v dialogu.
**Pořadí ale obracím:** kdyby se stráž po rozboru ukázala jako příliš
úzká, doména by pinovala hranici, která se vzápětí mění — a akceptační
sada, která brání něco, co se má opravit, je vada, kterou jsem už jednou
blokoval (W‑15).

**JEDINÝ DALŠÍ SMĚR: rozbor těch TŘÍ vět s `advcl`, které stráž nebere.**

Je levný, odpovídá na otázku, kterou sis sám položil, a rozhoduje
o tom, co má doména pinovat.

**Co má zodpovědět:** u každé ze tří — **pod čím ten `advcl` visí**
(jméno, přídavné jméno, něco jiného); **je `advcl` v tom čtení, které
měření použilo**, nebo ho tam parser nedal vůbec; a **je stráž správně
ohraničená, nebo příliš úzká** — tedy patří ty věty k `acl`, jak jsem
rozhodl, nebo je to jiný případ.

**Můj counterexample — a čísla v něm jsou ODHADY, ne měření, což tímto
označuji:** tabulka tří vět s tím, pod čím `advcl` visí a jestli je ve
čtení; explicitní odpověď „stráž je správně / je úzká" **s důvodem
z jmenovek rozboru**; **žádná oprava se neudělá dřív**; patnáct domén
se závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 53/53; nula `RECALL_FAILURE`; testy zelené; jádro **zůstává
0.1.20**.

**Po tom rozboru:** doména na `advcl`, a teprve pak rederivace pořadí
`acl` (7) proti rodině B (11) — z čísel, ne z mých vět.

---

## ARCHIV — kolo #81

### Status: 🟢 PASS — rozbor rodiny C vyvrátil MŮJ DŮVOD pro pořadí; opravuji ho

**Kolo #81.** Do jádra **nesáhl** — 979 testů zelených, `mypy --strict`
čistý na 61 souborech, doložky **70/70**, živá parita **53/53**, dialogy
15 / 41 / 24, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá
stálá regrese zelená. Jádro zůstává 0.1.20.

**Architectural Health Score: 9,5 / 10**

---

## Čtyři odpovědi, tři z nich mění zadání

Reprodukováno mnou (`nalezy/vnorena_veta.py`):

```
1 · DEPREL         acl 7 · advcl 5 · xcomp 4 · csubj 2 · ccomp 0  ← ANI JEDNOU
2 · advcl má mark  pokud 2× · než 2× · aby 1× · protože 1×   bez marku: 0
3 · průnik s nmod+Gen   4 z 12
4 · hloubka        0 hran 18 cest · 1 hrana 35 · 2 hrany 7
```

**(1) `ccomp` v korpusu není ani jednou** — a byla to zrovna ta položka
mé tabulky, kde jsem si byl nejjistější. Rozhodovací pravidlo, na které
se nedosáhne, je akademické; dobře, že se to změřilo dřív, než se podle
něj stavělo.

**(2) `advcl` má spojku ve všech pěti.** Můj předpoklad, že se u něj
jméno role smí **učit**, protože ho nese tvar, **měřením obstál.** To je
poprvé za poslední kola, kdy moje hypotéza o češtině prošla — a stojí za
to říct, že prošla **proto, že se změřila**, ne proto, že zněla rozumně.

**(3) Průnik s `nmod+Gen` je 4 z 12, ne 12 — a tím padá MŮJ DŮVOD pro
„C před B".** Napsal jsem, že C odblokuje těch dvanáct genitivů, které
rodina A nedosáhla. **Dosáhne nejvýš na třetinu.** Zbylých osm visí pod
jménem, které není ve čtení z **jiného** důvodu, a ten nikdo nerozebíral.

**(4) Vnoření jde do druhé úrovně** (7 cest se dvěma hranami), takže
`DepthExceeded` **není teoretická obava** a musí se s ní počítat od
začátku, ne až se projeví.

**A hlavní výstup kola, který je jeho, ne můj:** moje odpověď rozdělila
rodinu C na čtyři rozhodnutí podle deprelu, a měření z nich udělalo
**dvě stavby (`acl`, `advcl`), jedno ověření (`xcomp` — skládá se do
přísudku, což systém už dělá) a jedno odložení (`ccomp`)**. To je docela
jiný rozsah než „vnořená věta" jako celek.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑44 · osm genitivů blokovaných z jiného důvodu než vnořenou větou** —
nerozebráno, a je to teď nejbližší neznámá.

**W‑45 (nový, z bodu 4) · vnoření do druhé úrovně, 7 cest.** `DepthExceeded`
je reálná mez, ne pojistka. Zjistit, **kde je práh**, dřív než se staví.

**W‑42, W‑43, W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38, W‑40,
W‑41** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: `advcl`. Tvůj návrh schvaluji a tvůj důvod je
lepší než můj původní.**

Opravuji sám sebe nahlas: **pořadí „C před B" jsem odůvodnil číslem,
které neplatí.** `advcl` ale obstojí i bez toho důvodu, a to z toho, co
jsi změřil:

- **jméno role je čitelné ze spojky** → stavba **bez nové otázky pro
  člověka**, tedy bez nového tahu i bez nové domény pro tah;
- je to **role hlavní predikace**, ne nový druh výroku → **jádro se
  neverzuje ani teoreticky**;
- a mechanismus na to **existuje** — ověřil jsem si v minulém kole, že
  `RoleTerm` unese `RelationInstance`.

**Pořadí zbytku se rederivuje po `advcl`**, ne teď a ne z mého
neplatného důvodu: až bude `advcl` hotové, spočítej **kumulativní
pokrytí znovu** a porovnej `acl` (7) proti rodině B (11). Rozhodne to
číslo, ne moje předchozí věta.

**Můj counterexample:** všech **pět** vět s `advcl` se přečte a vedlejší
věta se stane **rolí hlavní predikace** s jménem odvozeným ze spojky;
věta s `advcl` **bez** spojky (kdyby taková přišla) se **nedosadí**, ale
zeptá; **jméno role se učí** — druhá věta s touž spojkou se **neptá**;
`ccomp`, `acl`, `csubj` i `xcomp` **zůstanou beze změny** a je na to
kontrola; **vnoření do druhé úrovně** buď projde, nebo padne **na
`DepthExceeded` s hláškou** — nikdy tiše; patnáct domén se závěry beze
změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 53/53;
nula `RECALL_FAILURE`; testy zelené; **jádro zůstává 0.1.20**; korpus
přeměřen nad čistou revizí a **rodina C klesne o pět vět**.

**A ještě jedna věc, kterou chci vidět dřív než stavbu:** kde je práh
`DepthExceeded` (W‑45). Je to jedno číslo a rozhoduje o tom, jestli je
bod „vnoření do druhé úrovně" splnitelný, nebo je to rovnou známá mez.

---

## ARCHIV — kolo #80

### Status: 🟢 PASS — patnáctá doména i s přiznanou mezí; a odpovídám na tři otázky před rodinou C

**Kolo #80.** 979 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **70/70**, živá parita **53/53**, dialogy 15 / 41 / 24, gate
*Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese zelená.
**Jádro zůstává 0.1.20.**

**Architectural Health Score: 9,5 / 10**

---

## Doména dělá přesně to, co má

```
» Chov zvířat je náročný.       ✓ [s0001] být(co:·náročný, kdo:·chov)  ← VĚTA zapsána
                                  ? … a přesto se ptá
« Je to předmět toho děje.      ✓ [s0005] chov(co:∀zvíře)
» Péče majitele je nutná.       ✓ [s0008]   ? ptá se ZNOVU
« Je to původce toho děje.      ✓ [s0012] péče(kdo:∀majitel)
```

**Závěrem domény je ta poslední dvojice: týž tvar dal jinou roli** — a to
je celý důvod, proč se tenhle tah nesmí nic učit. Kdyby se učil, přečetl
by druhou větu naruby. Lepší doklad pro „nic se neučí" si nešlo vymyslet.

**`Dialogue.limit` je nové pole a je napsané správně** — přiznává, že
doména neumí ukázat otázku, která by prošla **od věty k přívlastku**,
a říká i **proč se ty dvě věci nesvazují**. Doména, která svou mez
nepřizná, tvrdí víc, než dokládá.

**Rozpornou hlášku našel a opravil sám:** stopa říkala zároveň
*„PŘÍVLASTEK: čeká se na jméno role"* a *„ZAHOZENO: pro tenhle vztah role
není"*. To druhé je od téhle opravy **nepravda** — systém v témže tahu
tvrdí, že na přívlastek čeká. Táž třída jako W‑20.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Jeho výtka mému counterexamplu je oprávněná

Napsal, že jsem **smíchal dvě věci** — doménu a rodinu C. Má pravdu:
napsal jsem jeden seznam podmínek přes dvě různé práce, a to je táž vada,
jakou vytýkám testům, které měří dvě věci naráz. **Beru.**

A že se **zeptal dřív, než sáhl do jádra**, je přesně to, co moje
varování z minulého kola žádalo. Neptal se proto, aby se vyhnul práci —
ptal se s třemi konkrétními otázkami a s měřením k jedné z nich.

---

## Odpovědi na tři otázky — a mechanismus jsem si tentokrát ověřil

**(1) Druhá predikace, nebo role hlavní? — ANI JEDNO GLOBÁLNĚ. Rozhoduje
`deprel`, a to je ta odpověď.**

| deprel | co to je | tvar |
|---|---|---|
| `ccomp`, `csubj` | vedlejší věta **je argument** hlavního slovesa | **role** hlavní predikace |
| `acl` | přívlastková věta u **jména** | **druhý výrok**, jako přívlastek |
| `advcl` | okolnost hlavního děje | **role** hlavní predikace |
| `xcomp` | otevřený doplněk se sdíleným podmětem | **skládá se do přísudku** — už se to děje (`dokázat_poskytnout`) |

Nerozhodovat to globálně je táž disciplína jako všude jinde: **čti
jmenovku, nehádej**.

**(2) Čím se váže? — REIFIKOVANÝM UZLEM, a ten mechanismus JIŽ EXISTUJE.**
Ověřil jsem si to, než jsem ti to napsal — přesně podle pravidla, které
jsem si v minulém kole uložil:

```
kb.attach(atom("důkaz", role("obsah", RelationInstance(s0001))))
   → ZAPSÁNO:  důkaz(obsah:s0001)
```

`RoleTerm` **unese instanci vztahu** už dnes. Takže ani role, ani druhý
výrok nepotřebují nový sort — **jádro se neverzuje ani tady**.

**(3) Učí se, nebo ne? — ROZDĚL TO NA DVĚ VĚCI, a tvoje měření k tomu
dává správný argument.**

- **Struktura** (je to role, nebo druhý výrok?) se **čte z jmenovky**,
  neptá se a neučí — není co učit, `deprel` to říká.
- **Jméno role** u `advcl` se ptá **a učí**, jako každý jiný tvar. A tady
  je rozdíl proti genitivu, na kterém záleží: u genitivu byl směr
  vlastností **věty** („chov zvířat" × „péče majitele"), kdežto u `advcl`
  je jméno role dané **spojkou**, která je v rozboru jako `mark`
  („když" → `kdy`, „protože" → `proč`). **Tvar tedy nese odpověď, takže
  se učit smí.**

Tvoje měření z #78, že `acl+?` a `xcomp+?` nenesou pád, je správné —
ale znamená to, že se nemá číst **pád**, ne že se nemá číst nic.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑42, W‑43** leží dál. **W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37,
W‑38, W‑40, W‑41** taky.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: rozbor 15 vět rodiny C po jedné. Tvůj návrh
schvaluji.**

Dvakrát to dalo odpověď, kterou jsem předem neměl (#74 morfologie, #77
`role`), a potřetí to bude užitečné právě proto, že **odpovědi výš jsou
hypotézy o tom, které deprely v korpusu vůbec jsou.** Může se ukázat, že
`ccomp` tam není ani jednou a celá tabulka je akademická.

**Co má rozbor zodpovědět:**

1. **Který `deprel`** nese každá z těch 15 vět, a **kolik vět** má každý.
2. U `advcl`: **je tam `mark`?** Na tom stojí, jestli je jméno role
   čitelné z tvaru.
3. **Kolik z těch 15 je zároveň v těch 12 větách s `nmod+Gen`** — to je
   číslo, kvůli kterému jde C před B.
4. **Je někde vnoření hlubší než jedna úroveň?** `DepthExceeded` existuje
   a je dobré vědět, jestli na něj korpus dosáhne.

**Můj counterexample — a je to podmínka na rozbor, ne na opravu:**
tabulka deprelů s počty vět; u `advcl` zapsáno, jestli `mark` je; průnik
s `nmod+Gen` spočítaný; **žádná oprava se neudělá dřív**; patnáct domén
se závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 53/53; nula `RECALL_FAILURE`; testy zelené; jádro **zůstává
0.1.20**.

---

## ARCHIV — kolo #79

### Status: 🟢 PASS — (a) stojí; jedna z mých podmínek byla opět nesplnitelná a je to můj vzorec

**Kolo #79.** 966 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **69/69**, živá parita **51/51**, dialogy 14 / 37 / 24 se závěry
beze změny, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. **Jádro zůstává 0.1.20** — to byl můj signál, že
nesklouzl do (b), a drží.

**Architectural Health Score: 9,5 / 10**

---

## Moje zjednodušení platí a ušetřilo mechanismus

Všech pět významů padne na role, které systém **už má**: předmět děje
→ `co`, původce → `kdo`, nositel vlastnosti → `kdo`, část z celku →
`whole`, míra a druh → `co`. **Menu tedy není nový druh tahu**, je to
otázka na jméno role.

**Měřeno mnou živě:**

```
» Chov zvířat je náročný.
   [PŘÍVLASTEK: „chov zvíře“ — vztah vedle věty, čeká se na jméno role]
   ✓ zapsáno [s0001]  být(co:·náročný, kdo:∀chov)      ← VĚTA se zapsala
   ? … řekni, jakou roli v něm ten genitiv hraje (co, kdo, whole, …).
     Ptám se u každé věty znovu: „chov zvířat“ a „péče majitele“ mají
     týž tvar a opačný směr.
```

**Ta otázka je dobře napsaná** — říká i to, **proč** se ptá pokaždé
znovu. Věta se zapíše, druhý výrok bez odpovědi nevznikne. To je přesně
rozdíl „chybí přívlastek" × „chybí predikát".

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Podmínka „citace obou výroků" byla nesplnitelná — a je to můj vzorec

**Má pravdu a důvod je ten, kvůli kterému jsem (a) vybral:** reifikovaný
fakt se **záměrně neřetězí**, takže žádná otázka nemůže projít od věty
k přívlastku **bez můstkového pravidla**. Napsal jsem podmínku, která
předpokládá mechanismus, jenž neexistuje — a je to **potřetí za pět kol**
(#57 dvě protichůdné podmínky, #75/76 pravidlo o plurálu, teď tohle).

**Beru si z toho pravidlo pro sebe:** než napíšu bod counterexamplu,
ověřím, **jestli mechanismus, který ten bod potřebuje, v systému je.**
Zapsáno sem, ať to není jen předsevzetí.

## `nmod+Gen` 19 → 12: předpověděl to sám v kole #77

Zmizel ze sedmi, dvanáct zbylo — a příčina je **rodina C**, ne tahle
oprava: v těch dvanácti visí genitiv pod jménem, které samo **ještě není
ve čtení**, protože leží ve vnořené větě. **Jeho stráž „hlava musí být
ve čtení" je správná** — vztah nemá viset na něčem, o čem věta nemluví.

**Ověřil jsem si to na záznamech sám**, jen širším řezem než on:

```
celý korpus (238 vět):  nmod+Gen jako ztracený člen
   8b691b3   35 vět · 43 výskytů
   a4360ec   22 vět · 27 výskytů        ← 13 vět ho ztratilo
```

---

## Nález, který z toho plyne pro měřicí vrstvu

**Korpusový záznam ukazuje ZLEPŠILO 0 / ZHORŠILO 0** — protože stavy se
nezměnily. Skutečné zlepšení (13 vět, 16 výskytů) je v záznamu
**schované v textu důvodu**, ne v žádné metrice.

**To je vada měření, ne jádra:** oprava, která posune tvar, ale ne stav,
dnes vypadá jako **nic**. Předám Agentovi 3 — záznam má nést tvary
ztracených členů jako **pole**, ne jen jako větu k přečtení.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑42 · `nmod+Gen` ve vnořené větě, 12 vět** — čeká na rodinu C.

**W‑43 (nový, pro měřicí vrstvu) · zlepšení na úrovni tvaru je
v záznamu neviditelné.** Viz výš. Není to vada jádra.

**W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38, W‑40, W‑41** leží dál.

---

## Action Items for Agent 1

**Na tvou otázku: VOLÍM (1) — doménu napiš teď, se závěrem na jednom
výroku.**

Důvod: smlouva, která dnes existuje, je *„přívlastek se zapíše jako
druhý výrok a systém se na něj zeptá"*. To je skutečné a stojí za
zapsání. Můstek je **jiná schopnost** a svázat je znamená měřit dvě věci
naráz. **A hlavně:** kdybych ten můstek žádal teď, přivedl bych (b)
zadními vrátky — celý důvod pro (a) je, že se reifikovaný fakt neřetězí.

**K doméně napiš `limit`,** který říká, co ukázat **neumí**: že se
otázka nedostane od věty k přívlastku bez pravidla. Doména, která svou
mez nepřizná, tvrdí víc, než dokládá.

**Spoušť pro můstek — táž povaha jako u (b):** až v korpusu vznikne
otázka, která ten přechod **doopravdy potřebuje**. Do té doby ne.

**JEDINÝ DALŠÍ SMĚR PO DOMÉNĚ: rodina C — vnořená věta, 15 vět.**

A je to **tvoje vlastní metrika**, kterou jsem v #77 přijal: C sama nese
jen tři věty, ale **odblokuje těch dvanáct genitivů**, které rodina A
nedosáhla. Kumulativní pokrytí, ne vlastní číslo.

**Můj counterexample:** doména na `→@1` stojí a má `limit` o můstku;
`nmod+Gen` klesne pod 12 v těch 40 větách a **žádná jiná třída
nepřibere** větu odjinud než o vrstvu níž; čtrnáct **plus jedna** domén
se závěry beze změny; jádrové relace 9/9; gate *Farmaka* `N`/`s0005`;
parita ≥ 51/51; nula `RECALL_FAILURE`; testy zelené; korpus přeměřen nad
čistou revizí. **Jádro se neverzuje** — a kdyby se muselo, je to
znamení, že rodina C není jazyková vrstva, a máš se zeptat dřív, než to
uděláš.

---

## ARCHIV — kolo #78

### Status: 🟢 PASS — měření vyvrátilo moji hypotézu I tvar opravy; rozhoduji (a) reifikaci

**Kolo #78.** Do jádra **nesáhl** — 966 testů zelených, `mypy --strict`
čistý na 61 souborech, doložky **69/69**, živá parita **51/51**, dialogy
14 / 37 / 24, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá
stálá regrese zelená. Jádro zůstává 0.1.20. **Ohlásil PARTIAL a schvaluji
ho — zastavil se přesně tam, kde měl.**

**Architectural Health Score: 9,5 / 10**

---

## Moje hypotéza neplatí a je to doloženo

Napsal jsem, že hypotéza k ověření je, *„jestli genitivní přívlastek padá
celý do `names_owner`"*. **Nepadá — a přivlastnění mezi těmi významy ani
nefiguruje.** Reprodukováno mnou (`nalezy/genitiv_vyznamy.py`):

```
1 · předmět děje        10   chov zvířat · hledání viníků · vznik cukrovky
2 · původce děje         4   péče majitele · přínos Němcové · vývoj astronomie
3 · nositel vlastnosti   4   osud vesmíru · původ spisovatelky
4 · část z celku         3   polovina domu · typy psů
5 · míra a druh          3   míra péče · třída terapie
Z · není přívlastek      1   „Hradci Králové“ — jedno jméno, rozbor ho rozdělil
```

**Dvojice 1 a 2 se z tvaru rozlišit nedají** a ověřil jsem si to sám —
*„Přínos Němcové"* a *„Popis Němcové"* mají **identický rozbor**
(`nmod`, `Gen`) a **opačný směr**. Je to táž třída dvojznačnosti jako
holá spona: **navrhnout a zeptat se, nikdy nedosadit.**

## Strukturní nález mění tvar opravy a je správný

Ověřeno mnou na rozboru:

```
» Druhou polovinu domu obýval bratr.
    polovinu  NOUN  obj   → hlava obýval
    domu      NOUN  nmod  → hlava polovinu     ← visí pod JMÉNEM
```

**Genitiv není role predikace** — predikace nese role slovesa a `domu`
není argument „obývat". Je to **vztah dvou jmen uvnitř fráze**, tedy
**druhý výrok vedle věty**. „Dát mu jméno role" by byla oprava špatného
tvaru.

---

## Rozhodnutí: (a) REIFIKACE. (b) zůstává otevřená s pojmenovanou spouští

**Beru (a) a důvod je ten, který v tomhle projektu platí pořád:
nepřidávat uzávěr dřív, než ho něco potřebuje.**

Proti (b) mluví tři věci:

1. **Jádro už prostor „část z celku" rozřezalo podle sortů** — `contains`
   pro místo, `within` pro čas, `subset` pro třídy. Obecná partitivní
   relace by se s nimi **překrývala**, a překryté uzávěry jsou zdroj
   nejtěžších vad; kolizi jmen `whole`/`part` jsme viděli už v kole #59.
2. **Reifikace je mechanismus, který stojí** a dělá přesně tohle:
   `chov zvířat` → `chov(co:∀zvíře)`. Deverbální jméno **je** sloveso,
   jen zabalené — a systém umí vztahy reifikovat od začátku.
3. **Verze jádra se nemění**, takže se nic z toho, co drží, nedotkne.

**Spoušť pro (b), ať to není odloženo „navždy":** až přijde otázka, která
potřebuje **tranzitivitu částí** (*„je půlka půlky částí celku?"*)
a reifikovaný fakt na ni nestačí, je to důkaz, že partitivnost je
uzávěrová. **Do té doby ne.** Zapiš tu spoušť do dokumentace, ať se na ni
nezapomene.

**A jedno zjednodušení, které z tvého měření plyne a stojí za to ho
využít:** těch pět významů se liší **právě tím, kterou roli genitiv
v reifikovaném vztahu plní** — `chov(co:…)` × `péče(kdo:…)`. Menu tedy
není šestý druh tahu; je to **otázka na jméno role**, kterou systém už
umí (`names_role`). Ověř si to na všech pěti, ale pokud to vyjde, ušetří
to celý nový mechanismus.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑40 · zařazení do pěti významů je RUČNÍ a je to v hlavičce přiznané.**
Na rozdíl od rodin v `role_rozbor.py`, které jdou odvodit z jmenovek
rozboru, tohle je **popis nad daty**. Že to přiznal místo aby se tvářil
strojově, je správně — ale znamená to, že **to číslo nesmí do žádné
agregované metriky**, dokud ho nepotvrdí druhý pár očí.

**W‑41 · „Hradci Králové" rozbor rozdělil** na dvě jména. Jedna věta,
třída `Z`, a je to vada rozboru, ne jádra — zapsat jako známou mez.

**W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38, W‑39** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: postav (a) — genitivní přívlastek jako druhý výrok
přes reifikaci.**

1. **Druhý výrok, ne role predikace.** Věta zapíše svou predikaci
   a **vedle ní** vztah z genitivní fráze — týž tvar jako `→'`.
2. **Ptá se, nedosazuje.** Významy 1 a 2 jsou z tvaru nerozlišitelné,
   takže bez odpovědi **se ten druhý výrok nezapíše**. Věta sama se
   zapsat smí — chybí jí přívlastek, ne predikát.
3. **Nic se neučí** — je to vlastnost věty, ne tvaru: `chov zvířat`
   a `péče majitele` mají týž tvar a opačný směr.
4. **Zkus to jako `names_role` nad reifikovaným vztahem**, ne jako nový
   druh tahu. Když to nevyjde, řekni proč.

**Můj counterexample — bez něj neschválím:** *„Chov zvířat je náročný."*
zapíše predikaci **a** po odpovědi i `chov(co:∀zvíře)`; **bez odpovědi
druhý výrok nevznikne**, ale věta ano; *„Péče majitele je nutná."* dá po
odpovědi `péče(kdo:majitel)`, tedy **jinou roli** u téhož tvaru; druhá
věta téhož tvaru **se zeptá znovu**; otázka, která potřebuje ten druhý
výrok, na něj odpoví s **citací obou** výroků; tvar `nmod+Gen` **zmizí
jako blokátor** z těch 19 vět; **žádná jiná třída nepřibere** větu
odjinud než o vrstvu níž; čtrnáct domén se závěry beze změny; jádrové
relace 9/9; gate *Farmaka* `N`/`s0005`; parita ≥ 51/51; nula
`RECALL_FAILURE`; testy zelené; **jádro se neverzuje** — a kdyby ses
k verzi dostal, je to znamení, že jsi sklouzl do (b), a máš se vrátit.

---

## ARCHIV — kolo #77

### Status: 🟢 PASS — rozbor třídy `role`; odpověď je „ani jedno" a je lepší než obě moje varianty

**Kolo #77.** Do jádra **nesáhl** — `git status` hlásí jen `REVIEW.md`.
966 testů zelených, `mypy --strict` čistý na 61 souborech, doložky
**69/69**, živá parita **51/51**, dialogy 14 / 37 / 24, gate *Farmaka*
`N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese zelená. Jádro
zůstává 0.1.20.

**Architectural Health Score: 9,5 / 10**

---

## Ptal jsem se špatně a on to opravil

Nabídl jsem dvojici *„jedna mezera, nebo čtyřicet doptání?"*. **Ani
jedno**, a to je užitečnější odpověď, než kterou jsem čekal. Ověřeno
reprodukcí (`nalezy/role_rozbor.py`):

```
POVRCHOVÝ TVAR BEZ JMÉNA        vět   výskytů
   nmod+Gen                      19    25
   amod+Gen                       8     9
   flat+Nom                       8    12
   amod+Acc                       7     8
   …                          96 různých celých cest, 40 různých posledních hran

RODINA KONSTRUKCE            vyskytuje se   SAMA ve větě
   A · přívlastek                 40 vět         6
   C · vnořená věta               15 vět         0
   B · víceslovné jméno           11 vět         0
   E · příslovečné určení          9 vět         0
   D · koordinace                  9 vět         0
```

**Klíčové číslo:** rodina A je ve **všech čtyřiceti** větách, ale **sama
odblokuje jen šest**. Zbytek nese vedle ní ještě jinou rodinu — 14 vět
dvě, 15 vět tři, 5 vět čtyři.

```
KUMULATIVNÍ POKRYTÍ
   A 6/40 · A+B 12 · A+B+C 15 · +D 17 · +E 25 · +F 31 · +G 36 · +Z 40
```

**Metrika „kolik vět uvolní tahle jedna oprava" je tady zavádějící**
a on to pojmenoval dřív, než bych na to přišel sám: kdyby se vybíralo
podle ní, vyšla by rodina A jako skoro bezcenná, přestože bez ní neprojde
ani jedna věta. **Encyklopedická věta nese několik konstrukcí naráz,
takže pořadí oprav se má řídit kumulativním pokrytím.** To je poznatek
o metodě, ne o jedné třídě, a beru ho do stálého repertoáru.

---

## Je to vada, nebo normální provoz dialogu? — jeho argument beru

**Vada.** Důvod má z čísel a je správný: kdyby to byl normální provoz,
byly by ty otázky **různé**. Tady se ale **19 ze 40 vět ptá na týž tvar**
(`nmod+Gen`, přívlastek v genitivu). **Ptát se na tutéž konstrukci
devatenáctkrát není dialog, je to chybějící obecné pravidlo.**

---

## Chyba, kterou udělal a sám opravil

První verze skriptu brala „poslední záznam" **abecedně**, sáhla na
`2026-08-15.json` místo na `…-8b691b3.json` a počítala **35 vět místo
40**. Řadí se teď podle času a v kódu je napsané proč.

To je ten nejnebezpečnější druh chyby v měření: **čísla by pořád dávala
smysl**, takže by si jí nikdo nevšiml. Že ji našel a zapsal důvod, ne
jen opravil, je přesně ta péče, kterou tahle vrstva potřebuje.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑39 · `nmod+Gen` v 19 z 40 vět** — jedna konstrukce, polovina třídy.
Doložená, nerozhodnutá.

**W‑23, W‑25, W‑26, W‑30, W‑31, W‑36, W‑37, W‑38** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: rodina A, a v ní `nmod+Gen` jako první.
Tvůj návrh schvaluji, včetně metriky.**

**Měřit se to bude tím, že tvar zmizí jako blokátor ze všech 40 vět** —
ne počtem odblokovaných vět. Šest je správné číslo a nesmí se z něj dělat
zklamání; kumulativní pokrytí je ten správný ukazatel a A je jeho základ.

**Proč `nmod+Gen` a ne celá rodina naráz:** je v **19 větách**, tedy
v polovině třídy, a je to **jedna produktivní konstrukce** (přívlastek
v genitivu — *„datum narození"*, *„narození Boženy Němcové"*), ne
lexikální náhoda. Rodina A jako celek je pět různých hran; začít vším
znamená míchat pět rozhodnutí do jednoho kola.

**A protože jsem si v kole #76 sám slíbil, že pravidla češtiny budu
dávat jako hypotézy k měření, ne hotová:** neříkám ti, jakou roli
`nmod+Gen` nese. Vím jen, že systém už má tah `→'` (`names_owner`) pro
přivlastnění, a **hypotéza k ověření** je, jestli genitivní přívlastek
padá celý do něj, nebo se dělí na víc významů. **Změř to na těch 19
větách dřív, než něco zabuduješ.**

**Můj counterexample — bez něj neschválím:** na těch 19 větách je
zapsáno, **kolik různých významů** genitivní přívlastek nese a podle
čeho se rozlišují; pokud vyjde víc než jeden, **systém se ptá** a
nedosazuje; tvar `nmod+Gen` **zmizí jako blokátor** ze všech vět, kde
byl; **žádná jiná třída nepřibere** větu, která do ní nepřišla o vrstvu
níž; čtrnáct domén se závěry beze změny; jádrové relace 9/9; gate
*Farmaka* `N`/`s0005`; parita ≥ 51/51; nula `RECALL_FAILURE`; testy
zelené; korpus přeměřen nad **čistou revizí**.

---

## PŘIPRAVENÝ SMĚR (zadán člověkem, čeká ve frontě) — KOORDINACE JAKO ROZHODNUTÍ ČTENÍ

Nejde o kolo, je to zadání do fronty. Vzniklo z návrhu člověka
*„Přesné datum a místo narození expandovat na Přesné datum a Přesné
místo narození"* a z rozboru, proč to tak přímočaře nejde.

### Obecný problém

Koordinovaný člen má **dvě čtení a rozhoduje o nich význam, ne tvar**:

```
Petr a Pavel četli knihu.      → každý zvlášť?   (rozdělitelné)
Petr a Pavel jsou bratři.      → dohromady       (rozdělit ZTRATÍ vztah)
Petr a Pavel zvedli klavír.    → dohromady?      (rozdělit TVRDÍ VÍC)
Přesné datum a místo … není známo.  → každý zvlášť
```

Prošel jsem šest vět třídy B z korpusu: rozdělit jde u čtyř, u dvou je
to sporné (*„obdrželi novomanželé … doživotní právo"* — to právo dostali
jako pár). **Pravidlo to tedy není, je to nabídka.**

### Architektonická příčina

conBond4 čte **jednu predikaci na větu** a koordinaci vidí jen jako
signál pro shodu. Pro „Petr a Pavel" jako **jednu věc** nemá term:
sorty jsou `ENTITY · GROUP · RELATION · PLACE · TIME · VALUE · LABEL`
a algebra (`GroupAnd`, `GroupOr`, `GroupDiff`) je nad **třídami**, ne
nad množstvím jednotlivců. `group_and(Petr, Pavel)` je průnik, ne dvojice.

### Tvar řešení — a je to tvar, který systém už zná

**Rozdělení není předzpracování, je to tah dialogu.** Přesně jako
kvantifikátor, konstrukce a antecedent.

1. **Kaskáda označí koordinaci jako čekající** na `Predication`
   (`pending_coordination`), ne ve stopě — lekce B‑17. Dokud se
   neodpoví, **nezapisuje se nic**.
2. **Nový tah `→&` se dvěma odpověďmi:**
   - *„každý zvlášť"* → věta zapíše **několik výroků**, jeden na člen,
     a **sdílené závislosti se distribuují** (`Přesné datum narození …`
     + `Přesné místo narození …`) — to je přesně ten původní návrh,
     ale jako **jedna** z možností, ne jako transformace vstupu;
   - *„dohromady"* → **jeden** výrok o **skupinovém uzlu**, který vznikne
     přes `attach`, plus `member(Petr, g)` a `member(Pavel, g)`.
3. **Nic se tím neučí** — jako `→⊆1` a `!∀`. Rozdělitelnost je
   vlastnost **věty**, ne tvaru: obě věty výš mají týž tvar.
4. **Patro shody zůstává nedotčené.** Shoda rozhoduje, jestli věta
   **projde**; koordinace rozhoduje, co věta **zapíše**. Dvě různé
   otázky, a slít je znamená obejít W‑35 předzpracováním.

**Jádro se nemění.** Žádný nový sort, žádný nový uzávěr, žádná verze
sémantiky — skupinový uzel a `member` už existují a důkaz přes ně vede
sám. Celá změna je v jazykové vrstvě a v `attach`.

### Nejdřív měření, teprve pak stavba

**Kolik vět v korpusu má koordinovaný člen v jádrové roli a u kolika
z nich je rozdělení doopravdy platné?** První číslo se spočítá
(`conj` pod `nsubj`/`obj`), druhé je **rozhodnutí** a musí ho udělat
člověk na vzorku. Bez toho druhého čísla je to práce naslepo.

### Counterexample pro schválení

Doména, kde jsou **obě** čtení:

- „Petr a Pavel četli knihu." → **zeptá se**; bez odpovědi **nezapíše
  nic**; po `→& každý zvlášť` vzniknou **dva** výroky a otázka na Petra
  odpoví `A` s citací **jen jeho** výroku.
- „Petr a Pavel jsou bratři." → **zeptá se**; po `→& dohromady` vznikne
  **jeden** výrok o skupině + dvě členství, a otázka *„Je Petr bratr?"*
  **nesmí** dát `A` — kolektivní čtení se nedistribuuje. To je jádro
  celé věci.
- **Tvar se neučí:** druhá věta téhož tvaru se **zeptá znovu**.
- **Shoda beze změny:** „Petr a Pavel četl knihu." padá **dřív**, než se
  na koordinaci vůbec zeptá.
- Čtrnáct domén se závěry beze změny; jádrové relace 9/9; gate *Farmaka*
  `N`/`s0005`; parita ≥ 51/51; nula `RECALL_FAILURE`; testy zelené.

### Kam to patří ve frontě

**Po `role`.** `role` je 40 vět (17 % korpusu), koordinace 6 vět plus
schopnost. Pořadí ale rozhoduje člověk — tohle je návrh, ne verdikt.

---

## ARCHIV — kolo #76

### Status: 🟢 PASS — a moje podmínka byla nesplnitelná; Builder to změřil dřív, než ji zabudoval

**Kolo #76.** 966 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **69/69**, živá parita **51/51**, dialogy 14 / 37 / 24 se závěry
beze změny, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. Jádro 0.1.20 (`8b691b3`). **Ohlásil PARTIAL, a přesto to
schvaluji — protože ta nesplněná podmínka byla moje chyba.**

**Architectural Health Score: 9,5 / 10**

---

## Moje pravidlo bylo špatně a on to doložil

Napsal jsem: *„dva a víc členů → Plur, bez ohledu na to, že UD označí
jako `nsubj` jeden z nich v singuláru."* **Vzal to doslova a změřil to:
shodilo to sedm bezvadných českých vět** a `morfologie` místo na 0
**stoupla na 7**.

Stačí jediný protipříklad, aby bylo vidět, jak hrubé to pravidlo bylo:

```
» Vesmír či kosmos je označení.                   ✓ přečteno   (disjunkce!)
» Ke chřipce se přidal zánět ledvin a zápal plic. ✓ přečteno   (přísudek PŘED podmětem)
```

**Disjunkce plurál nežádá a přísudek před podmětem taky ne.** Zúžení,
které z toho udělal — plurál žádá koordinace, jen když **sčítá** (`a`/`i`,
ne `či`/`nebo`) **a** přísudek stojí **za** podmětem, s typem čteným
z hrany `cc` — je pravidlo měřené, ne odhadnuté.

**A pak našel svou vlastní vadu v tom zúžení**, což je ten druhý krok,
na kterém mi záleží: vracet `False` znamenalo *„koordinace tu není"*,
takže věta spadla na porovnání **s prvním členem**. `_coordinated` má
teď **tři stavy** — `True` žádá plurál, `False` je obojí správně, `None`
koordinace není. Slít poslední dva by poslalo větu do větve, která
o koordinaci neví.

---

## Měřeno mnou

```
» Karel Čapek a jeho bratr Josef byli aktéry.   ✓ přečteno
» Petr a Pavel četli knihu.                     ✓ přečteno
» Petr a Pavel četl knihu.                      → 0 čtení
     [PROČ: koordinovaný podmět žádá přísudek v MNOŽNÉM čísle …]
» Několik hostů přišlo. ✓ · Několik hostů přišli. → 0 čtení
» Psi byla v pondělí.   → 0 čtení · Obsahuje citron vitamíny? ✓ zúženo
```

**Korpus, dvě čisté revize:**

```
ea7cd68   NEPŘEČTENO 26 · PTÁ SE 210     morfologie 6
8b691b3   NEPŘEČTENO 21 · PTÁ SE 215     morfologie 1
změnilo stav 7:  NEPŘEČTENO → PTÁ SE 6   ·   opačně 1
```

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Ta jedna zbylá věta: jeho argument je správný

> „Přesné datum a místo narození Boženy Němcové dosud **není** známo."

Táž stavba jako *„Petr a Pavel četl knihu."* — spojka `a`, přísudek za
podmětem, sloveso v singuláru. **Jedna z nich je čeština a druhá ne,
a rozdíl je v tom, jestli členy míní jednu věc, nebo dvě.** Splnit
obojí naráz (`morfologie = 0` **i** pád „Petr a Pavel četl knihu.")
s tím, co patro ví, **nejde** — jedno se musí obětovat.

**Volil hlasitý pád před tichým průchodem a volil správně.** Je to táž
volba jako u rodu a u kvantifikace, kde jsem na kladném pravidle trval
sám.

**Jedno upřesnění k jeho „v rozboru to vidět není":** částečný signál
tam **je** — změřil jsem si to:

```
Petr   PROPN  nsubj  {'Animacy': 'Anim', 'Gender': 'Masc', …}
datum  NOUN   nsubj  {'Gender': 'Neut', …}          ← Animacy chybí
```

**Není to ale pravidlo, je to korelace.** Životnost s pojmovou jednotou
souvisí, ale neurčuje ji („stůl a židle stály" je taky plurál). Proto to
předávám jako **hypotézu k měření**, ne jako zadání — přesně v duchu
poučení, které si z tohohle kola vzal sám.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑37 · jedna věta v `morfologie` zůstává a je to vědomá volba.**
Zapsané: raději hlasitý pád než tichý průchod negramatické věty.

**W‑38 · rod se u koordinace neověřuje** — povolil jsem to a je to
zapsaná mez v kódu i v testu.

**Nahrazený test je v pořádku:** `test_a_coordinated_subject_is_left_alone`
držel **hranici rozsahu** kola #75, kterou tohle zadání zrušilo; zůstalo
z něj `test_the_two_branches_never_swap_places`, protože kvantifikace
a koordinace mají **opačný** požadavek. Starý hlídal rozsah, nový hlídá
věcný rozdíl.

**W‑23, W‑25, W‑26, W‑30, W‑31, W‑36** leží dál.

---

## Action Items for Agent 1

**Poučení, které sis vzal — *„pravidlo o jazyce si mám změřit dřív, než
ho zabuduju, i když přijde ze zadání"* — beru jako závazné pro nás oba.
Platí i na mě: příště ti pravidlo češtiny nedám jako hotové, ale jako
hypotézu s prosbou o měření.**

**JEDINÝ DALŠÍ SMĚR: `role` — 40 vět, největší zbylá třída.**

Morfologie je vyčerpaná (1 věta, vědomá volba). Podle baseline `8b691b3`
je teď **`role` jediným blokátorem u 40 vět z 238**, tedy 17 %, a je to
**pětinásobek** všeho ostatního dohromady. Věty typu *„Byl pohřben na
Vyšehradském hřbitově v Praze."* se přečtou, ale povrchový tvar nemá
jméno role.

**Nejdřív rozbor, teprve pak oprava** — přesně jako u morfologie
v kole #74, a z téhož důvodu: 40 vět je dost na to, aby v nich byly tři
různé příčiny, a hádat, která je ta hlavní, by znamenalo opravovat
naslepo.

**Můj counterexample — a tentokrát je to podmínka na rozbor, ne na
opravu:** ke každé z těch 40 vět je zapsáno, **který povrchový tvar**
zůstal bez jména a **kolik vět ten tvar sdílí**; tvary se seřadí podle
četnosti; **žádná oprava se neudělá dřív, než ten seznam existuje**;
čtrnáct domén se závěry beze změny; jádrové relace 9/9; gate *Farmaka*
`N`/`s0005`; parita ≥ 51/51; nula `RECALL_FAILURE`; testy zelené.

**Otázka, kterou ten rozbor má zodpovědět:** je `role` **jedna** mezera
(chybí obecná pravidla pro předložkové vazby), nebo **čtyřicet**
jednotlivých doptání, která jsou vlastně v pořádku? Na tom závisí, jestli
je to vada, nebo normální provoz dialogu.

---

## ARCHIV — kolo #75

### Status: 🟢 PASS — kvantifikovaný podmět; pravidlo kladné, ne výjimka

**Kolo #75.** 954 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **68/68**, živá parita **51/51**, dialogy 14 / 37 / 24 se závěry
beze změny, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. Jádro 0.1.19 (`ea7cd68`). **W‑33 uzavřena.**

**Architectural Health Score: 9,5 / 10**

---

## Podmínka, na které jsem trval, je splněná doslova

```
» Několik hostů přišlo.   ◐ přečteno  přijít(kdo:host)
» Několik hostů přišli.   → NEVÍM, jak to čtu
     [PROČ: kvantifikovaný podmět žádá přísudek ve STŘEDNÍM JEDNOTNÉM
      (řídí ho kvantifikátor, ne to jméno), a tenhle je Masc/Plur]
```

**Kdyby se shoda jen vypnula, druhá věta by prošla.** Neprošla — pravidlo
je kladné: ověřuje, co ta konstrukce v češtině žádá.

**Řídící člen se čte z jmenovky rozboru, ne ze seznamu slov,** a je na to
test, který slova „několik / mnoho / pět" ve zdrojáku té funkce
**zakazuje**. To je ta správná pojistka: seznam slov by byl druhé místo,
kde se totéž rozhoduje, a rozešel by se s parserem.

```
» Karel Čapek a jeho bratr Josef byli aktéry.  → 0 čtení   (třída B, drží)
» Psi byla v pondělí.                          → 0 čtení   (shoda rodu)
» Obsahuje citron vitamíny?                    ✓ jedno čtení, zúženo
```

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Korpus: čistá revize proti čisté revizi

Přečteno mnou z obou záznamů, ne z hlášení:

```
6afc38d   NEPŘEČTENO 30 · PTÁ SE 206 · CHYBA 2
ea7cd68   NEPŘEČTENO 26 · PTÁ SE 210 · CHYBA 2

sám blokuje:  morfologie 10 → 6
              role 39 → 39 · role_nenalezena 12 → 12 · rozbor 5 → 5
              kolize_rolí 3 → 3 · segmentace 2 → 2 · kvantifikace 1 → 1

změnilo stav 4:   NEPŘEČTENO → PTÁ SE  4      opačně  0
```

**Moje podmínka „žádná jiná třída nesmí přibrat" je tentokrát splněná
i v číslech**, ne jen v substanci. A **poprvé je to diff dvou čistých
revizí** — obě čísla jdou zopakovat.

**Zbylých šest je přesně třída B**, ověřeno výpisem po jedné.

**Vedlejší účinek, který hlásí sám a je to uzavření staré položky:**
*„Několik … měření tuto inflaci … podpořilo."* se teď čte **správně**
jako `podpořit(co:inflace, kdo:měření)`. V kole #73 ta věta ztratila
čtení s **prohozeným** podmětem a předmětem; teď má to správné. Jediná
„zhoršená" věta z minulého kola je tím vyřízená — **a je z ní zlepšení.**

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑35 (nesu dál, nedotčená schválně) · koordinovaný podmět, 6 vět.**
Potřebuje počítat shodu proti **celé koordinaci**, což je nová operace
nad stromem, ne nové čtení jmenovky. Že na ni nesáhl, aby šla měřit
zvlášť, je správně.

**W‑23, W‑25, W‑26, W‑30, W‑31, W‑36** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: W‑35 — koordinovaný podmět.**

Je to poslední třída, kterou má korpus doloženou, a po ní `morfologie`
jako jediný blokátor **klesne na nulu**. Tvar řešení je jiný než u C
a ty jsi to popsal správně: shoda se počítá proti **celé koordinaci**,
tedy proti `nsubj` **spolu s jeho potomky `conj`**.

**Dvě věci, které z toho udělají obecnou opravu, ne záplatu:**

1. **Číslo je vlastnost koordinace, ne jejího prvního členu.** Dva
   a víc členů → `Plur`, bez ohledu na to, že UD označí jako `nsubj`
   jeden z nich v singuláru.
2. **Rod se v češtině řeší podle pravidel, ne průnikem.** Muž + žena →
   mužský životný. Pokud si nejsi jistý celým rozhodovacím pravidlem,
   **nehádej ho**: ověř zatím jen **číslo** a rod u koordinace nech
   projít, ale **zapiš to jako známou mez**. Tichý default na rodu by
   byl horší než přiznaná neúplnost.

**Můj counterexample — bez něj neschválím:** všech **šest** vět třídy B
se přečte; věta s koordinovaným podmětem a přísudkem v **singuláru**
(*„Petr a Pavel četl knihu."*) se **dál zahodí a řekne proč**;
třída C **zůstane přečtená** a minimální pár *„Několik hostů přišli."*
dál padá; „Psi byla v pondělí." dál padá; „Obsahuje citron vitamíny?"
se dál zužuje; čtrnáct domén se závěry beze změny; devět z devíti
jádrových relací dál píše česká věta; gate *Farmaka* `N`/`s0005`;
parita ≥ 51/51; nula `RECALL_FAILURE`; testy zelené; **a korpus nad
čistou revizí ukáže `morfologie` = 0** a žádnou jinou třídu, která by
přibrala větu odjinud než o vrstvu níž.

---

## ARCHIV — kolo #74

### Status: 🟢 PASS — rozbor bez opravy, dvě třídy, nula vad rozboru

**Kolo #74.** Do jádra **nesáhl vůbec** — `git status` hlásí jen
`REVIEW.md`, což je můj soubor. 947 testů zelených, `mypy --strict`
čistý na 61 souborech, doložky **67/67**, živá parita **51/51**, dialogy
14 / 37 / 24, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá
stálá regrese zelená. Jádro zůstává 0.1.18.

**Architectural Health Score: 9,5 / 10**

---

## Zadání bylo „rozeber, neopravuj" — a přesně to udělal

To si zaslouží být řečeno nahlas, protože je to těžší než opravovat.
Deset vět, dvě třídy, **nula vad rozboru**:

```
B · koordinovaný podmět     6 vět
    „Karel Čapek a jeho bratr Josef byli aktéry…“
    signál: podmět v Nom s potomky conj
    jádro:  [PROČ: shoda čísla — přísudek Plur, podmět se nemůže shodnout]

C · kvantifikovaný podmět   4 věty
    „Několik nezávislých měření … podpořilo.“
    signál: podmět v Gen s potomkem det:numgov
    jádro:  [PROČ: shoda čísla — přísudek Sing, podmět se nemůže shodnout]
```

**Reprodukce mi běží** (`nalezy/shoda_zbytek.py`) a zařazení dělá
**výhradně z jmenovek rozboru** (`conj`, `det:numgov`, `Case`) — ne
z povrchu věty a ne z jádra. Přepínač `--korpus` si věty vytáhne
z měření, takže seznam nemůže tiše zestárnout. To je ta správná
konstrukce testu.

**Baseline je citovatelná:** `mereni/2026-08-15-6afc38d.json` nad
**čistou revizí** (`6afc38d` = commit W‑32), čísla sedí s minulým během
na jednotku. W‑U1 tím padá.

**Společná příčina je jiná než W‑32, a to je podstatné.** W‑32 byla
o tom, že se hodnota rysu porovnávala jako **řetězec**. Tohle je jiná
vada: **shoda se počítá proti špatnému členu.** Řídícím členem je u B
celá koordinace a u C kvantifikátor — a ani jeden není ten token, který
UD označí jako `nsubj`. Obě třídy mají v rozboru **jednoznačný signál**,
takže ani jedna nepotřebuje hádání.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

**Opravu mé chyby přijal správně** a sám dohledal doslovné znění hlášky.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑33 (upřesněná) · kvantifikovaný podmět** — 4 věty, signál
`det:numgov`. **W‑35 (nová) · koordinovaný podmět** — 6 vět, signál
`conj` pod podmětem v nominativu. Obě jsou **správná čeština správně
rozebraná**; chybně čte patro.

**W‑36 (drobnost) · `REVIEW.md` není zakomitovaný.** Je to audit trail
a je to můj soubor — zmiňuju to proto, že je to táž věc, kterou jsem
vytkl měřicí vrstvě (W‑U2). Rozhodne člověk, ne já.

**W‑23, W‑25, W‑26, W‑30, W‑31, W‑34** — W‑34 uzavřena tímhle rozborem,
zbytek leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: C — kvantifikovaný podmět. Tvůj návrh pořadí
schvaluji a důvod je správný.**

`det:numgov` je **explicitní jmenovka**, kterou UD dává právě proto, že
determinátor řídí pád své hlavy — parser nic neskrývá, patro se ho jen
neptá. Oprava je tedy **čtení jedné jmenovky**, kdežto B potřebuje
počítat shodu proti celé koordinaci, což je **nová operace nad stromem**.
C je levnější, nezávislejší, a B po ní zůstane měřitelné zvlášť.

**Jedna podmínka, na které trvám:** oprava nesmí znamenat *„když je tam
kvantifikátor, shodu přeskoč"*. To by byla díra, ne oprava. Pravidlo je
**pozitivní**: u `det:numgov` se shoda ověřuje proti tomu, co ta
konstrukce v češtině žádá — **střední jednotné** — takže věta, která to
poruší, **padne dál**.

**Můj counterexample — bez něj neschválím:** všechny **čtyři** věty
třídy C se přečtou; věta s `det:numgov` a přísudkem, který střednímu
jednotnému **neodpovídá**, se **dál zahodí a řekne proč**; třída B
**zůstane 6** (neopravuje se teď a nesmí se náhodou spravit ani rozbít);
„Psi byla v pondělí." dál padá; „Obsahuje citron vitamíny?" se dál
zužuje na jedno čtení; čtrnáct domén se závěry beze změny; devět
z devíti jádrových relací dál píše česká věta; gate *Farmaka* `N`/`s0005`;
parita ≥ 51/51; nula `RECALL_FAILURE`; testy zelené; **a korpus se
přeměří nad čistou revizí** — `morfologie` musí klesnout na **6**
a žádná jiná třída nesmí přibrat větu, která do ní nepřišla o vrstvu
níž.

---

## ARCHIV — kolo #73

### Status: 🟢 PASS — shoda průnikem; a jedna „zhoršená" věta je nejlepší nález kola

**Kolo #73.** 947 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **67/67**, živá parita **51/51**, dialogy 14 / 37 / 24 se závěry
beze změny, gate *Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. Jádro 0.1.18. **W‑32 uzavřena.**

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou

```
» Matka sbírala folklor.       ✓ sbírat(co:∃folklor, kdo:∀matka)     2 čtení → 1
» Povodeň zasáhla dům.         ✓ zasáhnout(co:∃dům, kdo:∀povodeň)    2 čtení → 1
» Přednáška byla v pondělí.    ✓ být(kdo:∀přednáška, kdy:pondělí)
» Psi byla v pondělí.          → 0 čtení  [shoda rodu — Fem,Neut]
» Obsahuje citron vitamíny?    ✓ jedno čtení, zúženo číslem
```

**Patro nepovoluje víc, jen přestalo trestat víceznačnost** — u prvních
dvou vět pořád **zužuje ze dvou čtení na jedno**. To je přesně ta
vlastnost, o kterou mi šlo: kdyby se zúžení ztratilo, byla by z opravy
díra.

**Kontrola rodu je nutná součást opravy, ne zpřísnění,** a Builderovo
odůvodnění sedí: `Psi byla v pondělí.` má na **čísle** průnik neprázdný
(`Plur` × `Plur,Sing`), takže samotný přechod na průnik by ji propustil.
Zahodí ji až rod. Rod tedy nedělá nic navíc — **nahrazuje tu část práce,
kterou dřív náhodou odváděla rovnost na čísle.**

**Že je to JEDNA funkce pro obě vrstvy**, je to podstatné rozhodnutí:
dvě kopie by se rozešly a jedna by začala trestat víceznačnost znovu.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Korpus: obě čísla, která jsem žádal

```
morfologie jako JEDINÝ blokátor   29 (12,2 %) → 10 (4,2 %)
NEPŘEČTENO                        49 → 30
PTÁ SE                           187 → 206
role_nenalezena 12→12 · rozbor 5→5 · kolize_rolí 3→3 · segmentace 2→2
per-větný diff:  ZLEPŠILO 20 · ZHORŠILO 1
```

**Výchozí stav změřil poctivě** — když mu nástroj soubor přepsal, vrátil
obě dotčená patra na `HEAD`, přeměřil (dostal přesně původní 29/238)
a opravu vrátil. Obě měření jsou tedy nad **touž sadou 238 vět**.

**Moje podmínka „žádná jiná třída nesmí narůst" je splněná v substanci,
i když ne v číslech, a jeho rozbor je správný.** `role` jako jediný
blokátor 35 → 39: **žádná věta na roli nově nepadla** — devatenáct vět,
které dřív umřely na morfologii, se teď přečte a doputuje o vrstvu dál.
Jsou to tytéž věty v **lepším** stavu. Kdybych trval na číslu, trestal
bych postup.

---

## Ta jedna zhoršená věta je nejlepší nález kola

> „Několik nezávislých experimentálních měření tuto teoretickou inflaci
> i teorii velkého třesku podpořilo."

Dřív šla do `PTÁ SE` — ale se **čtením `podpořit(co:měření,
kdo:teoretický_inflace)`**, tedy s **prohozeným podmětem a předmětem**.
To je pravý opak toho, co věta říká, a přežilo to jen proto, že
*„inflaci"* je `Sing` jako *„podpořilo"*, zatímco správný podmět
*„měření"* je `Plur`. **Systém přišel o špatné čtení**, ne o dobré.

**Změřeno mnou:** dnes `2 čtení → 0`, a hláška, kterou vidím, je
`[PROČ: shoda čísla — přísudek Sing, podmět se s ním shodnout nemůže]`.
Builder to připsal rodu; podle stopy padly obě čtení už na čísle.
Na závěru to nic nemění a rozbor příčiny má správný — jen tu jednu
větu popsal o patro vedle.

**Že věta padá nahlas, je lepší než že se tiše čte naruby** — a tenhle
rozdíl by nikdo nepoznal, kdyby záznam nevedl i `reading`. To je
návrhové rozhodnutí měřicí vrstvy, které se vyplatilo hned podruhé.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑33 (nový, odkrytý tímhle kolem) · KVANTIFIKOVANÝ PODMĚT.**
*„několik / mnoho / pět + genitiv plurálu"* má v češtině přísudek ve
**středním jednotném** čísle a **řídícím členem shody je kvantifikátor,
ne to jméno**. Dnes to systém neumí a věta padá. Je to **samostatná
konstrukce, ne doladění téhle opravy** — Builder to říká sám a má
pravdu. V korpusu je to jedna ze zbylých tříd `morfologie`.

**W‑34 · zbylých 10 vět třídy `morfologie` nikdo nerozebral po jedné.**
Hlásí to sám. Bez rozboru nevíme, jestli je to jedna konstrukce, nebo
tři — a to je rozdíl mezi jedním kolem a třemi.

**W‑23, W‑25, W‑26, W‑30, W‑31** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: rozebrat zbylých 10 vět třídy `morfologie` PO
JEDNÉ — a teprve podle toho rozhodnout, co opravit.**

**Proč rozbor, a ne rovnou oprava kvantifikovaného podmětu:** W‑33 je
doložená konstrukce, ale je to **jedna** z těch deseti. Opravit ji
naslepo znamená hádat, že zbytek je totéž. Deset vět je málo na to, aby
se to nedalo přečíst ručně, a hodně na to, aby se z toho dal odvodit
příští směr — **to je nejlevnější měření, jaké teď existuje.**

**Můj counterexample — bez něj neschválím:** ke každé z těch deseti vět
je zapsáno, **která konstrukce** ji shodila a **jestli je to čeština,
nebo vada rozboru**; třídy se pojmenují a spočítá se, kolik vět má
každá; **žádná oprava se neudělá dřív, než tenhle rozbor existuje**;
čtrnáct domén se závěry beze změny; devět z devíti jádrových relací dál
píše česká věta; gate *Farmaka* `N`/`s0005`; parita ≥ 51/51; nula
`RECALL_FAILURE`; testy zelené.

**A jedna věc pro Agenta 3, kterou mu vyřídím sám:** až tohle kolo
zakomituješ, měřicí vrstva přeměří nad **čistou revizí** — dnešní čísla
jsou z rozdělaného stromu a jako baseline se citovat nesmí.

---

## ARCHIV — kolo #72

### Status: 🟢 PASS — dekapitovaná věta se přestala zapisovat; a táž oprava chybí o patro níž

**Kolo #72.** 940 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **66/66**, živá parita **51/51**, dialogy 14 / 37 / 24, gate
*Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese zelená.
**Třináct starých domén se závěry beze změny.** Jádro 0.1.17.

**Architectural Health Score: 9,5 / 10**

---

## Nález, který Builder udělal sám, je vážnější než zadání

**Věta bez podmětu se ZAPISOVALA.** Po „Jan je učitel." dala „Narodil se
v Praze." rovnou `✓ zapsáno narodit(kde:Praha)`. To není „neumíme
pro‑drop" — to je **fakt o nikom, uložený tiše**. V encyklopedické próze
by se takové věty ukládaly jedna za druhou a nepoznalo by se to.

Že to našel **před** jakoukoli změnou a ohlásil jako první věc kola, je
přesně ta disciplína, kterou tenhle projekt drží.

**Po opravě, měřeno mnou:**

```
» Narodila se v Praze.       ◐ NEZAPSÁNO, NIKDO NENABÍDNUT
     Věta nemá podmět — „Narodila“ ho nevyslovil. V předchozí větě nikdo
     takový nestojí …
» Narodil se v Petrovicích.  ◐ NEZAPSÁNO, nabídne Jana
» Prší.                      → NEVÍM, jak to čtu
     ? přísudek „Prší“ nemá ani jeden člen, který bych uměl pojmenovat
» Narodil se Jan v Plzni?    → ANO   [doloženo: s0002, s0006]
```

**Zmínkou role je sám přísudek** (`kdo:narodit`) a je to schválně — do
textu se nepřidávají slova, která tam nejsou, a rod s číslem jsou právě
na něm. **Nabídku dělá táž funkce jako u zájmena**; dvě kopie by se
rozešly a jedna z nich by dřív nebo později začala hádat.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Critical Blockers

**Žádné pro tohle kolo.** Následující nález je **starší než kolo #72**
a nic z akceptační sady neporušuje — ale je to dnes nejdražší otevřená
věc v repozitáři a jde do dalšího směru.

---

## Semantic Warnings

### W‑32 · Táž oprava shody chybí v tvrdém patře — a Builder si ji sám odůvodnil

Kolo #72 muselo opravit porovnání rodu a čísla u **kandidáta na
antecedent**, a odůvodnil to takhle:

> UD u „Narodila" dává `Gender=Fem,Neut` a `Number=Plur,Sing`, protože
> tvar je pro všechny ty možnosti týž. **Rovnost by takového kandidáta
> zahodila vždycky** — porovnává se proto **PRŮNIKEM** a kandidát vypadne
> jen tehdy, když se shodnout **nemůže**.

**To je správně a platí to o patro níž taky — jenže tam se pořád
porovnává rovností.** Změřeno:

```
» Matka sbírala folklor.    → NEVÍM, jak to čtu
     [PROČ: shoda čísla — přísudek Plur,Sing, podmět musí být týž]
» Povodeň zasáhla dům.      → totéž
» Přednáška byla v pondělí. → totéž
```

**Všechny tři jsou bezvadná čeština.** `sbírala` je `Fem Sing` **i**
`Neut Plur` („děvčata sbírala"), takže `Plur,Sing` **není tvrzení**, že
přísudek je zároveň množný a jednotný — je to **přiznaná
víceznačnost UD**. Podmět `Matka` je `Sing`, průnik je neprázdný, shoda
platí. Patro ji zahazuje, protože žádá, aby byl podmět **stejně
víceznačný**.

**Rozsah je změřený, ne odhadnutý** — `conbond4-utils`, 238 vět ze čtyř
encyklopedických témat:

```
morfologie   29 vět (12.2 %)   a ve VŠECH 29 je JEDINÝM blokátorem
```

Je to největší třída, kterou by jedna oprava uvolnila celou. **Odmítnutí
je hlasité, ne tiché** — systém řekne, že neví — takže to není vada
bezpečnosti, ale **falešně negativní čtení**: dobrá věta, zahozená ze
špatného důvodu. A zamítnout gramatickou českou větu je pro systém,
který má číst psaný text nativně, drahá chyba.

**Nehotové, které Builder hlásí sám (a je to správně):** kandidát se
bere jen z **jedné** předchozí věty, ne z odstavce; neumí vynechaný
podmět se shodou s předmětem ani víc kandidátů téhož rodu.

**W‑23, W‑25, W‑26, W‑30, W‑31** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: shoda se porovnává PRŮNIKEM i v tvrdém patře.**

**Obecný problém, ne jedna věta:** rys, který UD uvede jako **množinu**
(`Plur,Sing`, `Fem,Neut`), je **přiznaná víceznačnost tvaru**, ne
konjunkce dvou tvrzení. Porovnávat ho rovností znamená zahodit každou
větu, kde je tvar homonymní a podmět jednoznačný — a to je v češtině
běžné, ne okrajové.

**Architektonická příčina:** patro shody porovnává řetězec rysu, ne
množinu hodnot. Táž vada byla v kandidátovi na antecedent a **už je
opravená** — zbývá ji dotáhnout tam, kde rozhoduje o zahození čtení.

**Nejmenší změna:** rys se rozloží na množinu hodnot a shoda platí při
**neprázdném průniku**. Patro tím **nepovoluje víc**, jen přestává
trestat víceznačnost: kde se shodnout **nemůže** (`Psi` × `byla` bez
společné hodnoty), zahodí čtení dál.

**Můj counterexample — bez něj neschválím:** „Matka sbírala folklor.",
„Povodeň zasáhla dům." i „Přednáška byla v pondělí." se **přečtou**;
věta, kde je průnik **prázdný**, se **dál zahodí** a řekne proč
(*„Psi byla v pondělí."*); „Obsahuje citron vitamíny?" se filtrem
**pořád zužuje** na jedno čtení; čtrnáct domén se závěry beze změny
(a když se některý změní, **napiš to**); devět z devíti jádrových
relací dál píše česká věta; gate *Farmaka* `N`/`s0005`; parita ≥ 51/51;
nula `RECALL_FAILURE`; testy zelené; **a znovu se pustí měření na
`conbond4-utils`** — třída `morfologie` musí klesnout a **žádná jiná
třída nesmí narůst**.

**K tvému návrhu změřit korpus znovu: ano, a je to teď dvojnásob na
místě** — po téhle opravě to bude poprvé, co může být `ZAPSÁNO`
nenulové, a rozklad po třídách řekne víc než další doména.

---

## ARCHIV — kolo #71

### Status: 🟢 PASS — zájmeno se ptá, nedosazuje; kontext textu je v jádře, ne v předzpracování

**Kolo #71.** 924 testů zelených, `mypy --strict` čistý na 61 souborech,
doložky **65/65**, živá parita **48/48**, dialogy 13 / 34 / 23, gate
*Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese zelená.
**Dvanáct starých domén se závěry beze změny.** Jádro 0.1.16.

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou — celý oblouk

```
» Jan je učitel.            ✓ [s0001]
» Ona bydlí v Praze.        ◐ NEZAPSÁNO, NIKDO NENABÍDNUT
     ? Na koho odkazuje „Ona“? V předchozí větě nikdo takový nestojí — a nabídnout
       uzel odjinud by znamenalo tvrdit, že text odkazuje tam, kde nic není.
» On bydlí v Petrovicích.   ◐ NEZAPSÁNO, nabídne Jana
     ? Z předchozí věty to podle shody rodu a čísla může být „Jan“. Rozhodnout to
       musíš ty — shoda je vodítko, ne důkaz, a ztotožnit uzly mlčky je nejdražší
       chyba, jakou můžu udělat.
« Myslím Jana.              ✓ [s0002] bydlet(kde:Petrovice, kdo:Jan)
» Petrovice jsou součástí Plzně. + →⊆1 contains   ✓ [s0006]
» Bydlí Jan v Plzni?        → ANO   [doloženo: s0002, s0006]
```

**Ta odpověď je celý smysl kola:** fakt, který se do báze dostal **přes
zájmeno**, unese dotaz i přes zahrnutí míst — a v citaci je vidět obojí.

**Příčina byla pojmenovaná správně a je to nová informace, ne nová
inference:** sezení znalo **tah**, ne **text**. `Discourse` se posouvá
jen po větě, která se **opravdu zakotvila** — věta, u které se systém
ptá, ještě není doříčená, a nabízet z ní antecedenty by znamenalo
odkazovat na uzly, o kterých se teprve rozhoduje. To je jemné a je to
správně.

**Tři zákazy, které si beru za své a schvaluji jako delegaci:**

1. **Ptá se i při jediném kandidátovi.** Shoda rodu a čísla je vodítko
   struktury textu, ne důkaz. Celá M‑2 stojí na rozdílu mezi „trefil
   jsem týž uzel" a „člověk řekl, že to je týž".
2. **Kandidát mimo předchozí větu se nenabídne.**
3. **Skupina se nenabídne nikdy** — „Jan je učitel." nabízí Jana, ne
   „učitele"; ztotožnit zájmeno s třídou by z individua udělalo druh.

**Zmizelá duplicitní otázka je nález téže třídy jako W‑20 a W‑29:**
kaskáda se ptala na kvantifikátor role, na kterou se už ptalo zakotvení
— člověk nevěděl, kterou z těch dvou odpovídá.

**Přepsaný starý test jsem si prohlédl a NENÍ oslabený.**
`test_pronoun_is_refused_out_loud` drží `statement_id is None`,
`question is not None` i `program() == ()` a **nově pinuje i důvod**
(„V předchozí větě nikdo takový nestojí"). Fixoval dřív hlášku
„Zájmena zatím neumím", což byla přesně ta mez, kterou tohle kolo ruší
— přepsat ji bylo nutné a udělal to správně: zúžil tvrzení, nezrušil ho.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete ✓ · jádrové krokem 9/9
```

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑31 (mez, Builder ji hlásí sám) · umí jen `on/jeho/její/jejich`.**
Pro‑drop („Narodil se v Praze." bez podmětu) a shoda rodu na přísudku
jako vodítko k podmětu — obojí člověk jmenoval **vedle** zájmen — v tomhle
kole nejsou. Je to **další krok téže vrstvy**, ne jiná vrstva.

**W‑23, W‑25, W‑26, W‑30** leží dál.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: PRO‑DROP — věta bez podmětu.**

**Proč právě to a proč teď:** je to druhá polovina téže vrstvy, kterou
tohle kolo otevřelo, a **v přirozeném textu je častější než zájmeno**.
Životopisný odstavec je jí plný: *„Narodil se v Malých Svatoňovicích."*,
*„Zemřel 25. prosince 1938."* — podmět tam **není vůbec**, ne že by byl
zájmenem.

**Architektonická příčina je táž a řešení musí být téhož tvaru:**
kandidát se **navrhuje z předchozí zakotvené věty**, nikdy nedosazuje,
a rod a číslo na přísudku (`byl` × `byla` × `byli`) je **vodítko, ne
důkaz** — přesně jako u zájmena. Historicky to tak řešil i conBond2:
`Kor=prodrop` / `Ent=<entita>` jako **aktivace viditelná v datech**,
s vypsaným počtem zásahů a s tím, kolik z nich potvrdila shoda rodu.
Nepřidávat do textu slova, která tam nejsou.

**Můj counterexample — bez něj neschválím:** dvouvětá doména, kde druhá
věta **nemá podmět**; systém navrhne kandidáta z předchozí věty
a **zeptá se**; bez odpovědi **nezapíše nic**; po odpovědi zapíše na
týž uzel a otázka dá `A` s citací obou výroků i zakotvení; věta bez
podmětu, kde předchozí věta kandidáta nemá, **nenabídne nikoho**;
**rod se kontroluje** — po „Jan je učitel." se u *„Narodila se v Praze."*
Jan **nenabídne**; třináct domén se závěry beze změny; devět z devíti
jádrových relací dál píše česká věta; gate *Farmaka* `N`/`s0005`;
parita ≥ 48/48; nula `RECALL_FAILURE`; testy zelené.

---

## ARCHIV — kolo #70

### Status: 🟢 PASS — DEVĚT Z DEVÍTI jádrových relací píše česká věta

**Kolo #70.** 904 testů zelených, `mypy --strict` čistý na 60 souborech,
doložky **64/64**, živá parita **45/45**, dialogy 12 / 31 / 22, gate
*Farmaka* `N`/`s0005`, nula `RECALL_FAILURE`, celá stálá regrese zelená.
**Jedenáct starých domén se závěry beze změny.** Jádro 0.1.15.

**Architectural Health Score: 9,5 / 10**

---

## Milník, který stojí za zapsání

```
jádrové predikáty zapsané krokem z ČESKÉ VĚTY:  9 z 9    zbývá: —
before · complete · contains · disjoint · member · name · same_as · subset · within
```

Před kolem #59 to byly **dva**. Vzorec „schopnost v jádře, ke které jazyk
nevede" — ten, který vyrobil B‑10, B‑11, B‑13 i W‑19 — **v tomhle
seznamu už nemá kde být.**

## Měřeno mnou

```
» Jan je učitel.                ✓ member
» Je Honza učitel?              → NEVÍM
» Jan se jmenuje taky Honza.    ✓ name(of:Jan, value:Honza)
» Je Honza učitel?              → ANO
     Honza → Jan (kanonicky; týž uzel, o kterém už řeč byla)
     - řekls: member(elem:Jan, group:·učitel)
   [doloženo: s0001, s0002]        ← ZAKOTVENÍ JE V CITACI
```

**Nález kolo je téže třídy jako výčet u uzavření v #69 a je správný:**
odpověď, která se na uzel dostala **přes jméno**, dřív necitovala výrok,
kterým je to jméno navázané — čtenář neměl jak zjistit, proč otázka
o Honzovi skončila u Jana. Zakotvení není premisa důkazu, je to krok
**před** ním; ale bez něj by se dotaz na ten uzel netrefil, takže do
citace patří.

**Stráže, které jsem si ověřil sám:**

```
» Ředitel jmenuje Jana.         ◐ jmenovat(co:Jan, kdo:∀ředitel)   ← NENÍ pojmenování
» Honza se jmenuje taky Jan.    ✓ name(of:Honza, value:Jan)        ← strany určuje DEPREL
```

Obě jména jsou v nominativu, takže generátor vyrobí dvě čtení a podle
pořadí by se jednou zapsal pravý opak. Že o stranách rozhoduje `deprel`
a ne pozice, je ta správná odpověď.

**W‑20 zavřena.** Příčina byla **jedna větev pro dvě různé věci**: role
s právě jedním mapováním, jehož kanonické jméno už někdo v téže větě
zabral, spadla do větve „tvar, který nikdo nepojmenoval". Teď se to
jmenuje `[KOLIZE: …]` a **neptá se** — otázka, na kterou systém odpověď
zná, je otázka bez odběratele. Test to tvrdí chováním (`question is None`).

**W‑29 zavřena a výjimka je úzká, ověřeno protipólem:**

```
» To jsou všichni psi.   ptá se na referenci: NE
» Ten pes štěká.         ptá se na referenci: ANO
```

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓
opačná ✓ · W-19 ✓ · W-24 ✓ · complete/nepřímý ✓ · complete/cizí ✓
```

**`ROLE_SORTS` beru jako správnou delegaci.** `name` je první relace,
kde strany **nejsou na téže ose** — `of` je uzel, `value` je nálepka —
a slít je do jednoho sortu by znamenalo, že jméno je porovnatelné
s uzlem, který ho nese. Že `Operation.NAME` je v menu, ale **ne**
v `RELATIONAL`, je táž úvaha ze druhé strany: u „Kočka je savec." by to
byla položka, na kterou tam nejde odpovědět.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑30 (drobný) · `test_the_collision_mark_survives_the_later_tiers`
tvrdí TVAR, ne chování** — že pole `collided` existuje a že ve zdrojáku
je řetězec „W‑20". Chování hlídá vedlejší test (`question is None`),
takže iluze pokrytí nevzniká; ten druhý je ale ozdobný a při přejmenování
pole zůstane zelený z nesprávného důvodu.

**W‑23, W‑25, W‑26** leží dál podle dohody.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: KONTEXT TEXTU — zájmena a zástupná označení.
Zadáno člověkem, ne mnou, a je to správně.**

Jádrové relace jsou hotové. Největší díra, kterou systém dnes **sám
hlásí**, je tahle:

```
» On má auto.
   ? Na koho odkazuje „On“? Zájmena zatím neumím — potřebují vědět,
     o čem se právě mluví, a to je vrstva, kterou nemám.
```

**Zadání od člověka, doslova:** *„slova jako on, jeho, zástupná označení
— jsou data, která vycházejí ze struktury textu"* a *„conbond3 pracoval
s hledáním podmětu pro možnost přiřazení vět"*. To je rozhodnutí
o architektuře a beru ho jako závazné: rozřešení odkazu **není hádání
z významu**, je to čtení ze **struktury sousedství vět** — týž princip
jako celý zbytek systému, kde tvar navrhuje a jádro rozhoduje.

**Co z toho plyne pro tvar řešení:**

1. Sezení dnes zná **tah**, ne **text**. Odkaz potřebuje vědět, co bylo
   ve **větě předtím** — to je nová informace, ne nová inference.
2. Kandidát na antecedent se **navrhuje**, nikdy nedosazuje. Tichý default
   u identity je nejdražší chyba, jakou tenhle systém může udělat
   (uzly se tiše slijí nebo rozštěpí).
3. Když je kandidát právě jeden a shoda rodu/čísla sedí, **pořád se
   ptá** — dokud o tom nepadne vědomé rozhodnutí (I‑13). Rozdíl mezi
   „trefil jsem týž uzel" a „člověk řekl, že to je týž" je celá M‑2.

**Můj counterexample — bez něj neschválím:** dvouvětá doména, kde druhá
věta odkazuje zájmenem, systém **navrhne** antecedent z předchozí věty
a **zeptá se**; po odpovědi zapíše fakt na **týž uzel** a otázka na něj
odpoví `A` s důkazem citujícím **oba** výroky i zakotvení; **bez
odpovědi se nezapíše nic**; kandidát, který v předchozí větě není, se
**nenabídne**; dvanáct domén se závěry beze změny (a když se některý
změní, **napiš to**); devět z devíti jádrových relací dál píše česká
věta; gate *Farmaka* `N`/`s0005`; parita ≥ 45/45; nula `RECALL_FAILURE`;
testy zelené.

**ROZHODNUTÍ ČLOVĚKA O TOM, KDE TO ŘEŠIT — a je závazné.** Doslova:
*„musíš předzpracovat text tak, aby byl čitelný pro conBond4, nebo
doplnit conBondu4 funkcionalitu. Dialogový text se bude podobat textu,
který nacházíš běžně na internetu. Proto je zásadní, aby se systém uměl
chovat tak, aby psanému textu rozuměl NATIVNĚ."*

**Znamená to: doplnit jádro, ne obcházet ho předzpracováním.** Čistič,
který zájmena předem nahradí jmény, by vyrobil text, jakému rozumí
conBond4 — a zakryl by přesně to, co se má naučit. Předzpracování
zůstává nástrojem na **měření** (co dnes projde), ne na **schování**
toho, co neprojde.

Do téže třídy patří i tvary, které člověk vyjmenoval vedle zájmen:
`on`, `jeho`, `její`, a slovesné tvary `byli`, `jsou` — shoda rodu
a čísla na přísudku je **taky odkaz do struktury textu**, ne jen
gramatická ozdoba, a je to totéž vodítko, kterým se hledá podmět.

**Materiál k měření už existuje a nemusíš ho vyrábět:** `conbond4-utils`
bere téma z Wikipedie, dělí ho **touž službou**, která větu rozebírá,
a měří, kam se každá věta dostane. První měření na čtyřech tématech
(236 vět) dalo **`ZAPSÁNO 0`** — encyklopedická próza je dnes celá za
hranicí, a zájmena jsou jeden z důvodů. To číslo je teď měřitelný cíl.

---

## ARCHIV — kolo #69

### Status: 🟢 PASS — uzavření světa z české věty, celý kruh; a nález, který je cennější než sama doména

**Kolo #69.** 877 testů zelených, `mypy --strict` čistý na 59 souborech,
doložky **62/62**, živá parita **42/42**, dialogy 11 / 29 / 20, gate
*Farmaka* `N` s doložkou `s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. **Deset starých domén se závěry beze změny.** Jádro
0.1.14, hlavička i changelog **sedí** (W‑28 zavřena).

**Architectural Health Score: 9,5 / 10**

---

## Celý kruh, měřený mnou

```
» Rex je pes.            ✓ [s0001]
» Alík je pes.           ✓ [s0002]
» Mourek je kocour.      ✓ [s0003]
» Je Mourek pes?         → NEVÍM
» To jsou všichni psi.   ◐ ? Mám „pes“ prohlásit za UZAVŘENOU skupinu? Znamená to,
                              že o každém, kdo v dosavadním výčtu není, budu nadále
                              odpovídat NE, ne NEVÍM …
« Ano, uzavři to.        ✓ [s0004] complete(group:·pes)
» Je Mourek pes?         → NE
     - skupina je uzavřená, a tenhle prvek v ní není
       - řekls: complete(group:·pes)
       - řekls: member(elem:Rex, group:·pes)
       - řekls: member(elem:alík, group:·pes)
» Počkej, ještě nějací jsou.   ✓ odvoláno [s0004]
» Je Mourek pes?         → NEVÍM
```

**Ta otázka před uzavřením je nejlepší věta, jakou tenhle systém dnes
umí říct.** Neptá se „potvrzuješ?", ale **vysvětlí, co si tím člověk
kupuje** — že se z `U` stane `N`. U jediné výjimky z I‑21 je to přesně
ta míra, která se od programu čeká.

**Nález, který Builder udělal sám a je cennější než sama doména:**
popření z uzavření dřív citovalo **jen prohlášení**, ne výčet. Prohlášení
říká „už nikdo další", ale **neříká, kdo v té skupině je** — bez výčtu
si čtenář nemá jak ověřit, že dotazovaný v něm opravdu není. Teď cituje
obojí.

**Nejnebezpečnější případ jsem si našel sám a drží:** `enumeration_of`
jde přes `member_proof`, ne přes surový index, takže **nepřímé členství
je součástí výčtu**:

```
Punt ∈ štěně,  štěně ⊆ pes,  complete(pes)
   Je Punt pes?     → ANO         ← uzavření ho NEzahodilo
   Je Mourek pes?   → NE
     - řekls: complete(group:·pes) · member(Rex, pes)
       · subset(štěně, pes) · member(Punt, štěně)
```

Kdyby výčet bral jen přímé členy, uzavření by **vyrobilo nepravdivé
`N`** o Puntovi. Nevyrobí.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
ireflex ✓ · opačná ✓ · W-19 ✓ · W-24 ✓
pravidlo s `complete` v hlavě → UnsafeRule ✓ (obě cesty)
jádrové krokem: 8 z 9, zbývá `name`
```

---

## Zásah do tvrdého patra: SCHVALUJI, a tady je proč

Builder sáhl do patra shody čísla — na tom mi záleží nejvíc ze všeho,
co v tomhle kole udělal, protože tvrdá patra jsou to, co brání systému
uhodnout. **Výjimku jsem proto proměřil na šířku sám:**

```
» Přednáška byla v pondělí.   → NEVÍM, jak to čtu   [shoda čísla] → zbývá 0   ✓ dál padá
» Psi byla v pondělí.         → NEVÍM, jak to čtu   [shoda čísla] → zbývá 0   ✓ dál padá
» Obsahuje citron vitamíny?   ✓ přečteno … [PROČ: shoda čísla] → zbývá 1      ✓ filtr pracuje
» To jsou všichni psi.        ◐ projde                                        ✓
» To je pes.                  ◐ projde                                        ✓
```

**Výjimka je opravdu úzká** — visí na lemmatu `ten` s `PronType=Dem`,
`Neut`, `Sing`, a všechno ostatní patro drží. Věcně má pravdu: střední
„to" v prezentační vazbě **nezastupuje počitatelný podmět** a v čísle se
neshoduje; „To je pes." i „To jsou psi." jsou obojí česky správně.
Zamítnout gramatickou větu je pro tenhle systém horší chyba než ji
pustit — pokud se u toho nic **nedomýšlí**, a nedomýšlí.

**Delegaci, kterou hlásí, beru a je správná:** tah `!∀` se **nic neučí**.
Ostatní tahy učí tvar, protože význam tvaru je vlastnost jazyka —
**uzavření světa vlastnost jazyka není**, je to epistemický stav
mluvčího o jedné skupině v jednom okamžiku. Že někdo dnes dopočítal své
psy, neopravňuje zavřít tytéž psy za měsíc. Kdyby se to učilo jako tvar,
bylo by to nejhorší tiché rozhodnutí v celém systému.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑29 (nová, Builder ji hlásí sám a je zapsaná v doméně jako `limit`)
· stopa se u „To jsou všichni psi." ptá i „na koho odkazuje To".**
V prezentační vazbě „to" **neodkazuje na nic** — je to podmět bez
reference — takže je to **otázka bez správné odpovědi**. Táž třída jako
W‑20. Že to nechtěl opravovat na konci kola v jiné vrstvě, je správné
rozhodnutí.

**W‑20, W‑23, W‑25, W‑26** leží dál podle dohody. **W‑28 zavřena.**

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: `name` z české věty — poslední jádrový predikát,
a s ním úklid otázek bez odběratele (W‑20, W‑29).**

**Proč spolu:** `name` je přesně relace mezi **uzlem a jeho
pojmenováním**, a obě otevřené drobnosti jsou otázky, které se ptají na
**referenci tam, kde žádná není** nebo kde ji systém už zná. Je to
jedna vrstva, ne dvě.

**Gate:** sada zapisuje krokem **osm z devíti**; `name` je poslední —
a jeho česká cesta je zároveň to, co dá „to" v prezentační vazbě
odpověď „na nic se neptám, tenhle podmět nikoho neoznačuje".

**Můj counterexample — bez něj neschválím:** nová doména zapíše `name`
**z české věty**; otázka, která potřebuje **spojení jména s uzlem**,
odpoví s důkazem citujícím ten zápis; **„To jsou všichni psi." se už
neptá na referenci „To"** a doména to má jako krok, ne jako `limit`;
stopa u `Gen`/`v+Loc` přestane hlásit `[CHYBÍ: co znamená role …]` tam,
kde odpověď zná (W‑20); jedenáct domén se závěry beze změny (a když se
některý změní, **napiš to**); `complete` kruh `U → N → odvolání → U`
beze změny; nepřímý člen po uzavření **pořád `A`**; gate *Farmaka*
`N`/`s0005`; parita ≥ 42/42; nula `RECALL_FAILURE`; testy zelené;
„Přednáška byla v pondělí." i „Pondělí je před pondělím." se **pořád
nezapíšou**.

---

## ARCHIV — kolo #68

### Status: 🟢 PASS — B‑17 zavřeno v příčině, desátý dialog stojí, sedm z devíti jádrových relací píše česká věta

**Kolo #68.** 852 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **61/61**, živá parita **37/37**, dialogy 10 / 25 / 17, gate
*Farmaka* `N` s doložkou `s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. **Devět starých domén se závěry beze změny.**

**Architectural Health Score: 9,5 / 10**

---

## Můj counterexample, měřený mnou

```
» Praha je součástí Plzně.
   odpověď na kvantifikátor Gen  → zapsáno None · program 0 · menu relací POŘÁD v otázce
   odpověď na kvantifikátor co   → zapsáno None
   odpověď na RELACI             → ✓ zapsáno [s0001] contains(part:Praha, whole:Plzeň)
```

**Příčina byla pojmenovaná správně a je to potřetí táž lekce (N‑3, G‑4,
teď B‑17): ptát se z HOTOVÉ PREDIKACE, ne z logu.** Čekající
kvantifikátor cestoval s predikací, čekající konstrukce s ničím —
a odpověď na cokoli jiného ji zahodila. `Predication.pending_relation`
to staví do téže roviny.

**Desátý dialog *Koncert* dělá přesně to, co jsem žádal:**

```
» Petrovice jsou součástí Plzně.  ◐ NEZAPÍŠE SE, ptá se
» Je to místo uvnitř místa.       ✓ [s0001] contains(part:Petrovice, whole:Plzeň)
» Pondělí je součástí týdne.      ◐ NEZAPÍŠE SE a ptá se ZNOVU  ← tvar se nenaučil
» Je to čas uvnitř času.          ✓ [s0002] within(part:pondělí, whole:týden)
» Koncert byl v Petrovicích v pondělí.   ✓ [s0003]
» Byl koncert v Plzni během týdne?  → ANO
     - řekls: být(kde:Petrovice, kdo:∃koncert, kdy:pondělí)
     - místo leží uvnitř jiného místa … contains
     - interval leží uvnitř jiného intervalu … within
   [doloženo: s0001, s0002, s0003]
» Byl koncert v Plzni v pondělí?    → ANO   [doloženo: s0001, s0003]   ← within NECITUJE
```

**Sedmý krok si přidal sám a je to ta správná kontrola:** kdyby se obě
zahrnutí slila do jednoho pravidla, `within` by se vezlo i tam, kde není
potřeba. Nevezlo se.

**Odchylku od mého zadání jsem ověřil a Builder má pravdu:**

```
» Přednáška byla v pondělí.
   → NEVÍM, jak to čtu
     [PROČ: shoda čísla — přísudek Plur,Sing, podmět musí být týž] → zbývá 0
```

Tvrdé patro tu větu **právem** zahodí; „Koncert byl v …" je věcně táž
jedna determinace s podmětem, na kterém shoda projde. **Rozdíl místo ×
čas nese PÁD** (`v+Loc` místo, `v+Acc` čas) — proto se obě okolnosti
vešly do jedné věty bez kolize rolí.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
ireflex ✓ · opačná ✓ · W-19 ✓ · W-24 ✓
jádrové krokem: before, contains, disjoint, member, same_as, subset, within  (7 z 9)
```

---

## Odpověď na Builderovu otázku o zlaté sadě

**Nech to tak.** `L1`/`L2` mají zapsané čtení `být(Gen:…)` — tedy právě
to, co se do báze nesmí dostat — a je to označené `asks`. **Fixovat stav
PŘED odpovědí je správně**, protože to je přesně ten stav, který B‑17
odbyl: kdyby se sada dívala až za odpověď, vada by se schovala. Nic se
tím nezapisuje a `asks` to říká nahlas.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑28 (nový, dokumentační) · hlavička jádra zůstala na 0.1.12.**
Changelog má řádek `0.1.13`, ale řádek 3 v `docs/CORE-SEMANTICS-0.1.md`
pořád říká **„Verze jádra: 0.1.12"**. Věcně je změna zapsaná a datovaná;
nesedí jen číslo v hlavičce — v dokumentu, který nese verzovací kázeň, to
má sedět. **Matice na to nedosáhne**, protože hlídá doložky, ne hlavičku.

**Nehotové, které Builder hlásí sám:** `complete` a `name` nemá žádná
doména. **W‑20** (stopa hlásí `[CHYBÍ: co znamená role v+Loc]` i tam, kde
odpověď zná — teď je to vidět i v *Koncertu*), **W‑23**, **W‑25**,
**W‑26** leží dál podle dohody.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: `complete` z české věty — jediné místo, kde se
z nepřítomnosti smí stát „ne".**

**Gate:** sada zapisuje krokem **sedm z devíti**; zbývá `complete`
a `name`. **`complete` je z těch dvou nesrovnatelně dražší:** je to
**lidské epistemické prohlášení** (lokální uzavření světa), které se
podle § nesmí odvodit **žádným pravidlem** — a je to jediné místo
v systému, kde **I‑21 („absence není negace") ustupuje**, a to jen proto,
že to člověk **výslovně řekl**.

**Proč teď:** dnes se `complete` měří **jen z formulí**. Je to táž třída
jako `before` před #59, `disjoint` před #64, `same_as` před #66 —
schopnost v jádře, ke které jazyk nevede. U `complete` je ale cena chyby
nejvyšší ze všech: špatně zapsané uzavření **vyrobí `N` tam, kde má být
`U`**, a to je přesně ten druh nevědomosti vydávané za znalost, který
tenhle projekt nesmí dělat.

**Můj counterexample — bez něj neschválím:** nová doména zapíše
`complete` **z české věty**; otázka, která **před** tím prohlášením dá
`U`, po něm dá **`N`**, a důkaz cituje **prohlášení i výčet**;
**odvolání** toho prohlášení vrátí odpověď na **`U`** (je to deklarace,
ne trvalý fakt — a `revokes` na to existuje); **žádné pravidlo**
`complete` nevyrobí (ověřím `Rule` se `complete` v hlavě i pokus
o odvození); deset domén se závěry beze změny (a když se některý změní,
**napiš to**); gate *Farmaka* `N`/`s0005`; parita ≥ 37/37 s novými
větami ve zlaté sadě; nula `RECALL_FAILURE`; testy zelené; „Praha je
součástí Plzně." + odpověď na kvantifikátor se **pořád nezapíše**;
„Pondělí je před pondělím." se pořád nezapíše.

**A při tom oprav hlavičku na 0.1.13** — je to jeden řádek a patří to
k témuž kolu, ve kterém verze vznikla.

---

## ARCHIV — kolo #67

### Status: 🔴 FAIL — poctivé PARTIAL, které beru; a k němu vada, kterou Builder nehlásí, protože ji nenašel

**Kolo #67.** 839 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **60/60**, živá parita **33/33**, dialogy 9 / 22 / 15 se závěry
beze změny, gate *Farmaka* `N`, nula `RECALL_FAILURE`, celá stálá regrese
zelená. **Builder sám hlásí PARTIAL a přesně jmenuje, co chybí — to je
správné chování a beru ho tak.** `FAIL` tu znamená „ještě neschváleno",
ne „udělals to špatně".

**Architectural Health Score: 9,0 / 10**

---

## Co jsem si ověřil, že HOTOVÉ opravdu je

Musel jsem si na to najít správné pořadí odpovědí — první běh mi ukázal
něco jiného (viz B‑17). **Když se odpoví na relaci, funguje všechno,
co Builder tvrdí:**

```
» Praha je součástí Plzně.
   ✓ rozhodnuto pro TUHLE VĚTU  stavba → contains   (tvar se NEUČÍ)
   ✓ zapsáno [s0006]  contains(part:Praha, whole:Plzeň)
» Pondělí je součástí týdne.
   ✓ zapsáno  within(part:pondělí, whole:týden)
```

**Smyčka z W‑19 je zavřená, změřeno celou cestou:**

```
před:  Jel Petr do Plzně?  → U   ? platí contains(part:Praha, whole:Plzeň)?
po:    Jel Petr do Plzně?  → ANO
         - řekls: jet(kam:Praha, kdo:Petr, kdy:pondělí)
         - místo leží uvnitř jiného místa
           - řekls: contains(part:Praha, whole:Plzeň)
       [doloženo: s0001, s0006]
```

**To je poprvé, co článek, který si systém sám vyžádal, jde říct česky
a odpověď se tím opravdu změní.** Tohle je jádro celého směru a je
hotové.

**Regresi z kola #59, kterou Builder našel a opravil sám, jsem ověřil:**
„Byl Petr v Česku?" se už neptá na menu relací, a „Pondělí je před
úterým." dál dává `before` a odpovídá `A`. Že se menu skládá
z `RELATIONAL` a ne z ručního výčtu, je správně — ruční seznam po
přidání relace zestárne a systém se ptá na míň, než umí.

---

## Critical Blockers

### B‑17 · Otevřená otázka na RELACI zápis nezastaví — věta se zapíše špatně a otázka zmizí

**Toto Builder nehlásí, protože to nenašel.** Změřeno živě:

```
» Praha je součástí Plzně.
   ? … Co ta věta tvrdí o vztahu těch dvou? cop:součást+Gen —
       before, contains, disjoint, member, same_as, subset, within?
   « O tom konkrétním.            (odpověď na KVANTIFIKÁTOR, ne na relaci)
   ✓ zapsáno [s0001]  být(Gen:Plzeň, co:·součást, kdo:Praha)
   ? Nevím, co znamená „Gen" — je to tvar, ne význam.
```

Tři věci najednou, a všechny měřitelné:

1. **Zapsalo se to, přestože systém sám říká, že nerozumí.** Role se
   jmenuje `Gen` — **tvar, ne význam**, a program to v téže odpovědi
   přiznává. Zápis pod přiznanou neznalostí (INV‑11).
2. **Otázka na relaci ZMIZELA.** V prvním doptání menu bylo,
   v následném už není. Nezodpověděla se — ztratila se.
3. **Výsledek je věcně špatný.** Věta o zahrnutí skončí v bázi jako
   `být(Gen:…)`, `contains` v bázi **není**, a smyčka W‑19 zůstane
   otevřená (změřeno: pořád `U`).

**Root cause je asymetrie, kterou mám změřenou z obou stran:**
**čekající kvantifikátor zápis ZASTAVÍ** (po odpovědi na `Gen` bylo
`zapsáno=None`), **čekající relace ne**. Přitom je to táž třída
rozhodnutí a L‑3 pro kvantifikátor tichý default výslovně zakazuje.

**Nejmenší bezpečná oprava:** dokud je otázka na konstrukci otevřená,
**nezapisuje se** — přesně jako u kvantifikátoru. Nezakazovat to
napořád: `být(…)` je legitimní záložní čtení, když člověk řekne, že
o žádnou z těch relací nejde.

---

## Co Builder sám hlásí jako nehotové (a je to tak)

- **desátý dialog neexistuje** a ve zlaté sadě nové věty nejsou — takže
  `contains`/`within` z češtiny se dnes měří **jen ručním během**, ne
  sadou. Kdyby to zítra někdo rozbil, nikdo se to nedozví.
- **`within` v řetězu neprověřený** — „Byl Petr v týdnu v Česku?" dá
  0 čtení (dvě určení téhož tvaru `v+Loc` kolidují na jednom jménu role)
  a „Byl Petr v týdnu?" čte *týden* jako **místo**. **Že to nechtěl
  hádat na konci kola, je správné rozhodnutí**, ne alibi.

Můj counterexample tedy splněný není: `contains` i `within` z české věty
**ano**, smyčka W‑19 **ano**, otázka přes `contains` s citací obou
zápisů **ano** — otázka potřebující **oba** druhy zahrnutí **ne**, nová
doména **ne**.

---

## Semantic Warnings

**W‑27 · doložka chybí právem.** Že ji Builder nepřidal, dokud není
doména s průchodem přes `.utter(`, je správně: doložka bez vynucujícího
testu tvrdí víc, než se měří.

**W‑20, W‑23, W‑25, W‑26** leží dál podle dohody.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: B‑17 — otevřená otázka na relaci musí zastavit
zápis. Desátý dialog až po ní.**

Pořadí není libovolné: dialog by tu vadu **zafixoval**, protože v něm
odpovíš na relaci a špatná větev se nikdy neprojde.

1. Čekající konstrukce **blokuje zápis** stejně jako čekající
   kvantifikátor.
2. Otázka na relaci se **neztrácí**, dokud na ni někdo neodpoví.
3. Až pak desátý dialog — a v něm **oba** kroky: správná odpověď
   i to, že bez ní se **nezapisuje**.
4. K časové variantě: tvůj návrh *„Přednáška byla v pondělí." +
   „Byla přednáška v týdnu?"* schvaluji — jedno určení, žádná kolize.

**Můj counterexample — bez něj neschválím:** „Praha je součástí Plzně."
+ odpověď **na kvantifikátor** → **nezapíše se** a otázka na relaci je
**pořád tam**; po odpovědi na relaci se zapíše `contains(part:Praha,
whole:Plzeň)`; desátý dialog zapíše `contains` **i** `within`, má krok,
kde se **nezapisuje**, a otázku, která potřebuje **oba** druhy zahrnutí,
s důkazem citujícím oba zápisy; nabídka `? platí contains(part:Praha,
whole:Plzeň)?` u *Čas a prostor* jde česky vyplnit a otázka pak dá `A`;
devět domén se závěry beze změny; gate *Farmaka* `N`/`s0005`; parita
≥ 33/33 s novými větami ve zlaté sadě; nula `RECALL_FAILURE`; testy
zelené; „Pondělí je před pondělím." se pořád nezapíše.

---

## ARCHIV — kolo #66

### Status: 🟢 PASS — M‑1 poprvé z češtiny; zúžení M‑2 schvaluji a zapisuji

**Kolo #66.** 839 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **60/60**, živá parita **33/33**, dialogy 9 / 22 / 15, gate
*Farmaka* `N` s doložkou `s0005`, nula `RECALL_FAILURE`, celá stálá
regrese zelená. **Osm dosavadních domén se závěry beze změny; devátá je
nová.**

**Architectural Health Score: 9,5 / 10**

---

## Celý oblouk, měřený mnou

```
» Mourek je kočka.      ✓ [s0001] member
» Micka je Mourek.      ✓ [s0002] same_as        ← z ČESKÉ věty
» Je Micka kočka?       → ANO      [doloženo: s0001, s0002]
» Micka není Mourek.    ✓ [s0003] ¬same_as       ← s0002 NEDOTČENÝ
» Micka je Mourek?      → SPOR V BÁZI, dva důkazy [s0002, s0003]
» Je Micka kočka?       → NEVÍM
     POZOR: o tom, jestli je Micka totéž co Mourek, si báze protiřečí —
     dokud to nerozhodneš, přes tuhle identitu nic nevede
```

**Táž otázka, která o tři kroky dřív dala `A`, padá na `U` — a na `U`,
ne na `N`.** Nikdo neřekl, že Micka kočka není; jen se přestalo vědět,
že je. To je **M‑1 z češtiny, poprvé**, a byla to jediná položka mé
stálé regrese, která se nikdy neměřila jinak než na formulích.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
ireflex ✓ · opačná ✓ · W-19 ✓ · W-24 ✓
jádrové krokem: before, disjoint, member, same_as, subset  (5 z 9)
```

---

## Zúžení M‑2: SCHVALUJI a beru za své

Builder si vyžádal potvrzení. **Souhlasím s ním, ověřil jsem obě strany
a zapisuji to sem, protože M‑2 je můj dodatek.**

**Co se změnilo:** podmínka B odmítala zakotvit zmínku, jejíž uzel je ve
sporu **s čímkoli**. Nově odmítá jen spor mezi uzly **téhož jména**.

**Proč je to správně, a je to argument, ne souhlas:** spor s uzlem
**jiného** jména nezpochybňuje, **který** uzel se míní — zpochybňuje
jejich **totožnost**. To je práce evaluátoru a M‑1 na ni **slibuje
verdikt**. Do zúžení skončila i přímá otázka doptáním „kdo je kdo",
takže se člověk **verdikt nikdy nedozvěděl** — a otázka je míň než
verdikt.

**Změřil jsem obě strany sám:**

```
spor TÉHOŽ jména   → nezapíše se, ptá se „Kterého Filipa myslíš?"   ✓
spor JINÉHO jména  → zakotví a zapíše [s0007], neptá se            ✓
                     a přímá otázka na identitu dá CONFLICT/2       ✓
```

**Jádro se neverzuje a je to podle mého vlastního měřítka z kola #62:**
tam jsem verzoval, protože se změnila **množina legálních bází**. Tady
se mění, **který uzel jazyk navrhne** — a I‑2 to výslovně staví mimo
jádro. Zapsáno tedy sem, s datem, jako změna dodatku M.

**Test podmínky B nepřepsal na slabší tvrzení, ale rozdělil na dva.**
Přesně tak se to dělá.

---

## Co chytila parita a je to nejužitečnější věc na kole

Builder **opsal** rozbor „Je Micka kočka?" ze sousední věty a **živá
služba to odmítla**: v „Micka je Mourek." čte parser *Micku* jako
**maskulinum** (táhne ji následující mužské jméno), samostatně jako
femininum. Opsaná nahrávka by fixovala rozbor, **který na živém vstupu
nenastane**. Táž třída jako chybějící `Poss=Yes` z kola #47 — jen to
tentokrát zachytil stroj, ne my dva.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑26 (drobný) · test zúžení měří sousedа, ne tvrzení.**
`test_a_dispute_with_another_name_gets_a_verdict_not_a_question` tvrdí
**verdikt evaluátoru**, ale ne to, že zakotvení **projde** — a přitom
právě to je ta změněná věc. Změřil jsem si to sám (zapsáno `s0007`,
neptá se), takže substance drží; test by to měl tvrdit taky, jinak
zúžení hlídá jen jméno testu.

**Přiznaná mez v doméně je zapsaná správně:** otázka na identitu se ptá
bez inverze („Micka je Mourek?"), protože dvě vlastní jména za sebou čte
parser jako **jedno složené jméno** (`flat`). Mez rozboru, ne kaskády.

**W‑20, W‑23, W‑25** leží dál podle dohody.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: `contains` a `within` z české věty — místo a čas
jedním dialogem.**

**Gate:** sada zapisuje krokem **pět z devíti**; zbývá `complete`,
`contains`, `name`, `within`.

**Proč právě ty dvě spolu:** jsou to **jediné dvě relace, které dnes
figurují v důkazech a v mezerách, ale žádný krok je nezapisuje** —
změřeno: `contains(part:Praha, whole:Plzeň)` se nabízí u *Čas a prostor*
a `within` u *Pořadí dnů*. Systém tedy **žádá článek, který si člověk
česky nemá jak říct**. To je táž třída jako W‑19, jen o patro výš: tam
šlo o článek, který **evaluátor** neumí použít, tady o článek, který
**jazyk** neumí vyrobit.

**Druhý důvod:** obě mají v `_compat` vlastní větev (`contains_proof`,
`within_proof`), obě jsou v mých sortových stráží, a ani jedna nemá
českou cestu — tedy přesně vzorec, který v posledních šesti kolech
vyrobil B‑10, B‑11, B‑13 a W‑19.

**Můj counterexample — bez něj neschválím:** nová doména zapíše
`contains` **i** `within` z české věty; otázka, která potřebuje
**oba** druhy zahrnutí, dá `A` s důkazem citujícím oba zápisy; otázka
opačným směrem dá `U`, ne `N`; **a** dosavadní nabídka u *Čas a prostor*
(`? platí contains(part:Praha, whole:Plzeň)?`) se po zapsání té věty
**česky** promění v `A` — tím se zavře smyčka, kterou W‑19 otevřela;
devět domén se závěry beze změny (a když se některý změní, **napiš
to**); gate *Farmaka* `N` s doložkou `s0005`; parita ≥ 33/33; nula
`RECALL_FAILURE`; testy zelené; „Pondělí je před pondělím." se pořád
nezapíše.

---

## ARCHIV — kolo #65

### Status: 🟢 PASS — citace dosáhla na původ; W‑24 zavřena

**Kolo #65.** 828 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **59/59**, živá parita **29/29**, dialogy 8 / 19 / 12 se závěry
beze změny, gate *Farmaka* `N` a **jeho doložka beze změny** (`s0005`),
nula `RECALL_FAILURE`, celá stálá regrese zelená.

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou

```
Je Čimčara savec?  → NE
   - pravidlo p0001: ¬member(elem:x, group:·savec) <- member(elem:x, group:·vrabec)
     - a to plyne z toho, že řekls: disjoint(a:·vrabec, b:·savec)
     - prvek podtřídy je prvkem nadtřídy
       - řekls: member(elem:Čimčara, group:·vrabec)
cited:  ('p0001', 's0001', 's0002')      origins: ('s0001',)
listy důkazu: ['p0001', 's0002']         ← STROM SE NEZMĚNIL
```

**Důkaz se nevymyslel, jen se dorenderoval** — přesně to jsem zadal:
listy jsou pořád `p0001, s0002`, změnilo se, co se z nich ukáže. Tělo
pravidla je celé, mnohotečka pryč.

**Potlačení se nepřehnalo**, ověřeno protipólem: výrok **bez**
`derived_from` má `cited == ('s0001',)` a `origins == ()`, tedy přesně
jako dřív.

**Citace ostatních domén beze změny** — prošel jsem všech dvanáct
závěrů: `s0005` u *Farmak*, `s0001–s0004` u *Vegetariána*,
`s0001, s0002` u *Pořadí dnů*. Přibylo **jen** `s0001` u *Vrabce*.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
ireflex ✓ · opačná ✓ · W-19 ✓
```

**Původy nese report, ne volající** — `verify()` si je bere z
`AuditReport.origins`, takže se nepočítají dvakrát. Builderův odkaz na
dvě kopie `REQUIRES_BOUND` z A‑24 sedí: kdyby si je každý počítal sám,
`verify` by hlídalo jiný seznam, než se vypsal. **A invariant
`cited == listy` nepřepsal na slabší tvrzení, ale na nové** (`listy plus
původ`) i s odůvodněním — to je rozdíl, na kterém mi záleží.

---

## Kde je moje formulace přesnější, než co jde splnit

Můj gate zněl *„je vidět **řekls: Vrabec není savec.**"*. V odůvodnění
se ukáže **formule** `disjoint(a:·vrabec, b:·savec)`, ne česká věta —
a **Builder to řekl sám, dřív než bych to změřil**. Má pravdu: text věty
v bázi **není**, prezentér renderuje z toho, co je zapsané, a nést
surface větu v bázi je **jiné rozhodnutí**, ne dodělávka.

**Substanci mé podmínky to splňuje** — člověk obě své věty pozná
a `s0001` je v `cited`. Zapisuju to jako otevřenou otázku, ne jako dluh:
*má báze nést i větu, kterou to člověk řekl?* Až na to dojde, je to
rozhodnutí o § 8 a o tom, co je ještě jádro.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑25 (otevřená otázka, ne vada) · citace ukazuje formuli, ne větu.**
Viz výš. Dokud báze nese jen formule, je tohle správně; kdyby se to mělo
změnit, je to vědomé rozhodnutí (I‑13), ne úprava prezentéru.

**W‑23** (pořadí nabídek) a **W‑20** (šum ve stopě) leží dál podle
dohody.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: `same_as` z české věty — a s ním sporná identita.**

**Gate:** sada zapisuje krokem **čtyři z devíti** jádrových predikátů
(`before`, `disjoint`, `member`, `subset`). Chybí `complete`,
`contains`, `name`, `same_as`, `within`.

**Proč `same_as` a proč teď:** je to jediná zbývající relace, na které
visí **M‑1** — „přes spornou identitu fakty netečou" — a ta je v mé
stálé regresi od začátku, **měřená výhradně na formulích**. Táž třída
jako `before` před kolem #59 a `disjoint` před #64: schopnost v jádře,
ke které jazyk nevede. U identity je to ale **nejdražší**, protože chyba
tam uzly tiše slévá nebo štěpí — a to nepozná ani jeden dnešní test,
protože žádná česká věta `same_as` nezapíše.

**Druhý důvod, změřený:** *Petrovice* už dnes kanonizují jméno („týž
uzel, o kterém už řeč byla"), ale `same_as` **nezapisují** — takže se
nikdy neprověří rozdíl mezi *„trefil jsem týž uzel"* a *„člověk řekl,
že to je týž člověk"*.

**Můj counterexample — bez něj neschválím:** nová doména zapíše
`same_as` **z české věty**; otázka **přes tu identitu** dá `A`
s důkazem, který cituje **oba** zápisy; pak člověk identitu **popře**
česky, přímá otázka na ni dá `CONFLICT` se **dvěma** důkazy, a otázka na
fakt, který přes ni tekl, spadne zpátky na **`U`, ne `N`** (M‑1 z češtiny);
původní zápis zůstane **nedotčený** (nedestruktivní `same_as` — ověřím
`inspect`); osm domén se závěry beze změny (a když se některý změní,
**napiš to**); gate *Farmaka* `N` s doložkou `s0005`; parita ≥ 29/29
s novými větami ve zlaté sadě; nula `RECALL_FAILURE`; testy zelené;
„Pondělí je před pondělím." se pořád nezapíše.

---

## ARCHIV — kolo #64

### Status: 🟢 PASS — osmá doména říká „ne" z vyloučení tříd; důkaz ale nedosáhne na větu, kterou člověk řekl

**Kolo #64.** 820 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **58/58**, živá parita **29/29**, dialogy 8 / 19 / 12, gate
*Farmaka* `N`, nula `RECALL_FAILURE`, celá stálá regrese zelená.
**Sedm dosavadních domén má závěry beze změny; osmá je nová.**

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou

```
» Vrabec není savec.   ✓ zapsáno [s0001] disjoint(vrabec, savec)
                         [expanze na dvě pravidla: p0001, p0002]
» Čimčara je vrabec.   ✓ zapsáno [s0002]
» Je Čimčara savec?    → NE     [doloženo: p0001, s0002]
» Je Čimčara pták?     → NEVÍM  ? platí subset(sub:·vrabec, sup:·pták)?
» Kočka je savec.      ◐ ptá se: member / subset / disjoint?
» Je to podmnožina.    ✓ naučeno konstrukce cop:NOUN=NOUN ~ subset [tah 6]
                       ✓ zapsáno [s0003]
```

**„Je Čimčara pták?" → `U` je nejlepší krok té domény.** Oddělenost od
savců o ptácích nerozhoduje, a kdyby tam padlo `N`, byla by to nevědomost
vydávaná za znalost. Doména tím měří obojí: že `disjoint` **řekne ne**,
i že **neřekne víc, než smí**.

**Doptání je v doméně a je to táž stavba jako první krok, jen kladně** —
`cop:NOUN=NOUN` je dvojznačná, systém se ptá a **do odpovědi nezapisuje
nic**. To je přesně smyčka, kterou uživatel chce vidět.

**Duplicita ve zlaté sadě, kterou chytil test a ne Builder,** stojí za
zapsání: „Vrabec není savec." tam už byla jako `G2`, a
`test_fixed_parse_is_actually_reused` odmítl 29 rozborů na 30 položek.
Zlaté sady tloustnou přesně takhle — a tady to zachytil stroj.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓ · ireflex ✓ · opačná ✓
jádrové zapsané krokem: before, disjoint, member, subset  (4 z 9)
```

---

## Kde jsem svou podmínku nesplněnou nechal, a proč

Můj counterexample zněl: *„`N` s důkazem, který cituje **oba zápisy**
(`member` i `disjoint`)."* **Doslova splněný není.** Změřeno:

```
listy důkazu: ['p0001', 's0002']
cited:        ('p0001', 's0002')
   - pravidlo p0001: ¬member(elem:x, group:·savec) <- …
     - prvek podtřídy je prvkem nadtřídy
       - řekls: member(elem:Čimčara, group:·vrabec)
```

`s0001` — věta, kterou člověk **řekl** — v důkazu **není**. Je tam
`p0001`, což je pravidlo z její expanze. **Builder to popsal přesně**
(„cituje p0001 … i s0002") a teprve jeho součet nazval „oba zápisy";
nic nezakryl.

**Neblokuju to a chci mít napsáno proč:** verdikt je správný, důkaz je
sound a stopa **existuje v bázi** — `p0001.derived_from == s0001`. Je to
vada **čitelnosti**, ne správnosti, a je mírnější než ta, kterou jsem
v kole #59 pustil dál (tam vysvětlení nabízelo článek, který **nešel
použít**). Blokovat teď a tehdy ne by znamenalo měřit dvěma metry.
**Je to ale první položka dalšího směru.**

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑24 (nový) · citace se zastaví na odvozeném pravidle.** Člověk řekne
*„Vrabec není savec."* a v odpovědi vidí `pravidlo p0001: ¬member(elem:x,
group:·savec) <- …` — svoji větu tam nenajde, a ještě je useknutá
mnohotečkou. **Provenience je přitom v bázi** (`derived_from`),
prezentér ji jen nepoužije. Zasahuje I‑14 v jeho duchu (vysvětlení má
být to, čemu člověk rozumí) a § 8.

**W‑23 leží dál** (pořadí nabídek), **W‑20 taky** podle dohody.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: důkaz musí dosáhnout na větu, kterou člověk řekl.**

**Gate:** „Je Čimčara savec?" → `NE` a v odůvodnění je vidět **„řekls:
Vrabec není savec."**, ne jen `p0001`. **Root cause:** prezentér bere
listy důkazu jako konečnou stanici; u derivačního cukru (`disjoint` →
`p0001`/`p0002`) je konečná stanice **o hop dál** a `derived_from` ji
zná. **Zasažená smlouva:** I‑14, § 8.

1. Citace odvozeného výroku se **rozvine na jeho původ**. Původ je
   jeden hop, ne rekurze do nekonečna — když `derived_from` chybí, končí
   se tam, kde se končí dnes.
2. **Nevymýšlet nový důkaz.** Strom zůstává, mění se to, **co se z něj
   renderuje** — jinak by to bylo vysvětlení, které si přidává (I‑14).
3. Useknuté `<- …` u pravidla dořeš při tom: buď se tělo ukáže celé,
   nebo se místo pravidla ukáže rovnou původ.

**Můj counterexample — bez něj neschválím:** v odůvodnění „Je Čimčara
savec?" je řetězec, ze kterého člověk pozná **obě své věty**, a `s0001`
je v `cited`; `disjoint → N` na úrovni formulí **beze změny**; gate
*Farmaka* `N` a jeho doložka **beze změny**; osm domén se závěry beze
změny (a když se některý změní, **napiš to**); parita 29/29, nula
`RECALL_FAILURE`, testy zelené; „Pondělí je před pondělím." se pořád
nezapíše a „Je středa před pondělím?" pořád netiskne žádné `? platí`.

---

## ARCHIV — kolo #63

### Status: 🟢 PASS — B‑16 zavřeno oběma dveřmi, které z češtiny vedou; jádro 0.1.12

**Kolo #63.** 814 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **58/58**, živá parita **26/26**, dialogy 7 / 16 / 10 se závěry
beze změny, gate *Farmaka* `N`, nula `RECALL_FAILURE`, celá stálá regrese
zelená. **Každý bod mého counterexamplu změřen živě.**

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou

```
» Pondělí je před pondělím.
   ✗ nezapsáno: … nic není dřív než ono samo. `before` je striktní
     uspořádání, takže smyčka na sebe je kruh o jednom uzlu …
» Je pondělí před pondělím?   → NEVÍM   (žádné „? platí")
» Pondělí je před úterým.     ✓ zapsáno [s0001]
» Je pondělí před úterým?     → ANO
```

**Sezení nespadlo ani jednou a báze po odmítnutí dál žije** — to bylo
jádro mé podmínky, protože zákaz, který bázi poškodí, by byl stejně
špatný jako ta vada.

```
ireflex ✓ · opačná hrana ✓ · po odmítnutí báze žije ✓
W-19: obrácené 0 ✓ · smyčka 0 ✓ · bez rizika cyklu 1 ✓
protipóly: jet → contains(part:Praha, whole:Plzeň) · Mourek → subset(·kočka, ·savec)
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
```

**Nález, který udělal Builder sám, je téže třídy jako W‑19 a chytil ho
o krok dřív, než by ho chytil někdo jiný:** po opravě zápisu začala
otázka nabízet `? platí before(pondělí, pondělí)?` — **větu, kterou
zápis vždycky odmítne**. Nabídnout člověku něco, co nesmí vyslovit, je
táž vada jako nabídnout cestu, kudy vyhodnocení nejde. Opravil to
sám a bez vyzvání.

**Verze zapsaná podle mého rozhodnutí:** jádro **0.1.12**, § 9 dostalo
`InconsistentOrder` jako pojmenované selhání **zápisu**, k tomu
ireflexivitu, poznámku, že H‑3 v uzávěru zůstává jako **druhá** obrana,
a otevřenou otázku o variantě (2).

**W‑22 zapsaná dvojitě a je to lepší, než jsem žádal:** v jádře jako
známá mez, v testu jako **fixovaná** mez —
`test_the_identity_side_is_a_known_limit` staví kruh přes `same_as`
a **očekává** `InconsistentOrder`, takže až to někdo spraví, ten test
spadne. Mez, na kterou se zapomene, se mění v tichou vadu; tenhle test
tomu brání.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑23 (nový, drobný) · report nerozlišuje nabídky, které vedou k `A`,
od těch, které vedou k `N`.** Změřeno na „Je Mourek savec?" po
„Vrabec není savec.":

```
? platí subset(sub:·kočka, sup:·savec)?        → vedlo by na A
? platí member(elem:Mourek, group:·vrabec)?    → vedlo by na N (přes p0001)
? platí subset(sub:·kočka, sup:·vrabec)?       → vedlo by na N
```

Všechny čtyři **někam vedou**, takže moje kritérium z W‑19 splňují a vada
to není. Ale člověk, který má odpovídat, nevidí, že dvě z nich jsou
větev „ne". **Nepřidávat na to teď nic** — je to poznámka pro chvíli,
kdy se bude řešit pořadí nabídek.

**W‑22 uzavřena jako fixovaná mez** (viz výš). **W‑20 leží dál podle
dohody.**

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: zpátky k jádrovým relacím, které česká věta
nevyrobí — na řadě je `disjoint`.**

**Gate:** akceptační sada zapisuje krokem **tři z devíti**: `before`,
`member`, `subset`. Chybí `complete`, `contains`, `disjoint`, `name`,
`same_as`, `within`.

**Proč právě `disjoint` a proč teď:** změřil jsem, že čeština ho **už
umí vyrobit** — „Vrabec není savec." dá `disjoint(a:·vrabec, b:·savec)`
a zapíše ho. Ale **žádná doména ho nepoužívá**, takže se nikdy neprověří
řetěz `member` + `disjoint` → `N`, což je jediná cesta, jak systém řekne
„ne" z **vyloučení tříd**. Tři z posledních pěti blokerů měly tvar
„schopnost v jádře, ke které jazyk nevede"; tady jazyk vede a chybí
**doména**.

**Bonus, který mám změřený:** sousední věta „Kočka je savec." se
**správně ptá** (member / subset / disjoint), takže táž doména prověří
i smyčku doptání — a to je věc, kterou uživatel výslovně chce vidět.

**Můj counterexample — bez něj neschválím:** nová doména zapíše
`disjoint` **z české věty**; otázka na členství dá **`N`** s důkazem,
který cituje **oba** zápisy (`member` i `disjoint`); otázka na
nesouvisející třídu dá **`U`**, ne `N`; aspoň jeden krok domény je
**doptání**, na které se odpovídá tahem; osm domén se závěry beze změny
(a když se některý změní, **napiš to**); gate *Farmaka* `N`, parita
≥ 26/26 s novými větami ve zlaté sadě, nula `RECALL_FAILURE`, testy
zelené, „Pondělí je před pondělím." se **pořád** nezapíše.

---

## ARCHIV — kolo #62

### Status: 🔴 FAIL — zábrana hlídá kruh přes dva a víc uzlů; jednouzlový projde a sezení pořád padá

**Kolo #62.** 810 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **58/58**, živá parita **26/26**, dialogy 7 / 16 / 10 se závěry
beze změny, gate *Farmaka* `N`, nula `RECALL_FAILURE`, celá stálá
regrese i obě strany W‑19 zelené. **Blokuji přesto** — B‑16 je zavřené
jen pro cyklus, který jsem uvedl v příkladu.

**Architectural Health Score: 9,0 / 10**

---

## Co je hotové a je to dobře udělané

**Ty čtyři věty živě, bez výjimky, přesně jak jsem žádal:**

```
» Pondělí je před úterým.     ✓ zapsáno [s0001]
» Úterý je před středou.      ✓ zapsáno [s0002]
» Středa je před pondělím.
   ✗ nezapsáno: … by uzavřelo pořadí do kruhu — s0001, s0002 říká opak.
     … odvolej jeden z těch výroků, nebo tenhle nevyslovuj.
» Je pondělí před středou?    → ANO   [doloženo: s0001, s0002]
```

**Odmítnutí je tah, na který jde odpovědět** — jmenuje výroky a řekne,
co s tím. To je přesně to, co § 9 myslí selháním zápisu.

**Přepsané testy H‑3 jsou poctivé.** Nepředělal je na nový zákaz, což by
H‑3 tiše odstavilo; vede je vnitřním `_attach` a v docstringu stojí, že
H‑3 je **druhá** obrana. Tohle je správné řešení a stojí za zapsání.

**W‑21 splněno lépe, než jsem žádal** — test jede nad třemi dotazy, které
opravdu něco tisknou, a nabídku převádí na atom **tabulkou konstruktorů**,
ne parsováním výpisu.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
W-19 obrácené: nabídek 0 ✓ · bez rizika cyklu: nabídka drží ✓
```

---

## Critical Blockers

### B‑16 (znovu otevřeno) · `before(X, X)` projde a příští otázka shodí sezení

**Jedna česká věta, živě:**

```
» Pondělí je před pondělím.
   ✓ přečteno  before(earlier:pondělí, later:pondělí)
   ✓ zapsáno [s0001]
» Je pondělí před pondělím?
   ✗ SEZENÍ SPADLO: InconsistentOrder: uspořádání kolem 'pondělí' si odporuje …
```

**Týž symptom, táž výjimka, táž cesta ven ze `Session.utter` — jen
o dvě věty dřív.** A rozbije to i dotazy, které s tou větou nesouvisí:
po `before(po, po)` spadne i `before(po, úterý)`.

**Root cause, jeden řádek:** `storage.py:240` —

```python
proof = self.view().index.before_proof(later.target.id, earlier.target.id)
if proof is None:
    return          # nic se neodmítá
```

Zábrana se ptá **„vede už cesta opačným směrem?"**. U hrany na sebe je
`earlier` totéž co `later`, opačná cesta neexistuje, `before_proof`
vrátí `None` — a jednouzlový kruh se zapíše. Přitom hláška té zábrany
sama říká *„by uzavřelo pořadí do kruhu"*, a smyčka na sebe kruh **je**.

**Není to nová podmínka, kterou bych si vymyslel po termínu.** `before`
je **striktní** uspořádání — na tom stojí celé H‑3 („z cyklu by uzávěr
odvodil, že je všechno před vším"). Ireflexivita není nová politika, je
to táž politika.

**Nejmenší bezpečná oprava:** odmítnout `earlier.target.id ==
later.target.id` **před** hledáním cesty. Jiná hláška, tentýž tah:
nemá co jmenovat, protože kruh netvoří žádný dřívější výrok.

---

## Semantic Warnings

**W‑22 · Kruh jde uzavřít i ZE STRANY IDENTITY, a tam zábrana nesahá.**
Změřeno přes API:

```
attach before(pondělí, úterý); before(úterý, středa)
attach same_as(středa, pondělí)      → zapsáno s0003 (bez námitky)
dotaz before(pondělí, středa)        → ✗ InconsistentOrder
```

Zábrana sedí na zápisu `before`; **splynutí uzlů** ji obejde. **Z češtiny
to dnes nejde** — ověřeno: „Středa je pondělí." se přečte jako `být(…)`
a systém se **správně ptá**, jestli jde o `member`, `subset`, nebo
`disjoint`; `same_as` nad intervaly z toho nevznikne. Proto varování,
ne bloker. Až se B‑16 dodělá, tohle je místo, kde se ukáže, jestli je
zábrana **na hraně**, nebo **na stavu grafu**.

**W‑20 a W‑21** — W‑21 uzavřena, W‑20 leží dál podle dohody.

---

## Odpověď na Builderovu otázku o verzi

**Verzovat.** Vyžádal si potvrzení a mé rozhodnutí je opačné, než navrhl:
`attach` nově **odmítá formuli, kterou dřív přijal**, takže se mění
množina legálních bází — a to je pozorovatelná změna kontraktu zápisu,
ne interní detail. V changelogu jsou 0.1.10 i 0.1.11 verzované za změny
menšího dosahu (chování evaluátoru). Zapiš **0.1.12**: § 9 dostane
odmítnutí kruhu v uspořádání jako pojmenovaný stav, k němu **ireflexivitu**
a otevřenou otázku o variantě (2). Že jsi variantu (2) nerozhodoval, je
správně a v docstringu je zapsaná dobře.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: dodělat B‑16 pro jednouzlový kruh a zapsat 0.1.12.**

1. `earlier.target.id == later.target.id` → odmítnout, **před** hledáním
   cesty.
2. Verze **0.1.12**, § 9 + ireflexivita + otevřená otázka o variantě (2).
3. **Nesahat** na W‑22 v tomtéž kroku — zapiš ji jako známou mez.

**Můj counterexample — bez něj neschválím:** „Pondělí je před pondělím."
se **nezapíše** a sezení nespadne; hned po tom odmítnutí báze **dál
odpovídá** (`before(pondělí, úterý)` se dá zapsat a otázka na něj dá `A`);
ty čtyři věty z minulého kola **beze změny**; „Je středa před pondělím?"
po dvou větách **pořád** netiskne žádné `? platí`; `before(pondělí,
čtvrtek)` nabídku **pořád** tiskne a po zapsání dá `A`; `jet/Plzeň`
i `Mourek/savec` beze změny; sedm domén se závěry beze změny (a když se
některý změní, **napiš to**); gate *Farmaka* `N`, parita 26/26, nula
`RECALL_FAILURE`, testy zelené.

---

## ARCHIV — kolo #61

### Status: 🟢 PASS — B‑14 i B‑15 zavřeny na povrchu, který čte člověk

**Kolo #61.** 804 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **57/57**, živá parita **26/26**, dialogy 7 / 16 / 10 se závěry
beze změny, gate *Farmaka* `N`, nula `RECALL_FAILURE`, celá stálá regrese
zelená. **Můj counterexample splněn ve všech bodech a měřil jsem ho na
`render()`, ne na `open_goals`.**

**Architectural Health Score: 9,5 / 10**

---

## Měřeno mnou, přesně tím postupem, který jsem zadal

```
A) OBRÁCENÉ POŘADÍ        verdikt U · řádků „? platí" 0   ✓
   tohle mi nikdo neřekl a nabídnout ti větu, která by uspořádání
   kolem before(earlier:středa, later:pondělí) uzavřela do cyklu, nemůžu

B) BEZ RIZIKA CYKLU       verdikt U · řádků „? platí" 1   ✓ potlačení je ÚZKÉ
   ? platí before(earlier:pondělí, later:čtvrtek)?
   po zapsání → A

C) jet(kdo:Petr, kam:Plzeň)   ? platí contains(part:Praha, whole:Plzeň)?  → po zapsání A ✓
D) member(Mourek, savec)      ? platí subset(sub:·kočka, sup:·savec)?     → po zapsání A ✓
```

**Živou cestou přes UDPipe totéž:** „Je středa před pondělím?" → `NEVÍM`,
řádků `? platí` **nula**, a pod tím pravda bez návodu.

**Rozhodnutí je tam, kde nabídka vzniká.** `GapReport` nese
`unsafe_offer` a rozhoduje `render()`. Mlčet nešlo a Builder to
pojmenoval správně: **člověk má vědět, PROČ mu systém nic nenabízí.**

**B‑15 zavřeno tak, jak jsem žádal:** `_offers()` tahá nabídky
**regulárem z výpisu**, a nula se tvrdí **explicitně** (`== []`), ne
cyklem, který se neprovede. K tomu dva testy na opačnou stranu, aby
potlačení nezhltlo případy, kde se odpovědět dá.

**Matice smluv ho chytila pošesté** — S‑28 odkazovala na testy, které po
přepisu neexistovaly. To je ta část systému, která funguje sama od sebe,
a stojí za zapsání, že chytá i přejmenování.

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR ✓ · I-16 ✓ · ∀→∃ U/N ✓
```

---

## Critical Blockers

### B‑16 · Když člověk ten cyklus VYSLOVÍ, sezení spadne výjimkou

**Nezpůsobilo to tohle kolo** a nebylo to v zadání — našel jsem to, když
jsem si ověřoval, proti čemu vlastně ta nová nabídka chrání. **Je to
ale nejvážnější věc, kterou dnes v repu vidím**, a je to jediný další
směr.

Čtyři české věty, živě:

```
» Pondělí je před úterým.     ✓ zapsáno [s0001]
» Úterý je před středou.      ✓ zapsáno [s0002]
» Středa je před pondělím.    ✓ zapsáno [s0003]   ← přijato bez námitky
» Je pondělí před středou?
   ✗ SEZENÍ SPADLO: InconsistentOrder: uspořádání kolem 'pondělí' si odporuje …
```

Výjimka **uteče z `Session.utter()`** ven. `GapFinder.explain()` spadne
na tomtéž, protože si na začátku volá `engine.ask()`.

**Root cause:** `H‑3` je rozhodnutí evaluátoru („neodpovídám, dokud se
to nevyřeší"), ale **dialogová vrstva pro něj nemá tah**. Zápis
`s0003` projde, protože `attach` cyklus nekontroluje; rozbije se až
příští otázka — a to je ta nejhorší možná chvíle.

**Zasažená smlouva:** I‑1 (žádné tiché selhání — tady není tiché, ale
program **nemá jak říct, co se stalo**), I‑3 (spor se má **ohlásit**,
ne shodit sezení) a § 9: selhání zápisu je **tah dialogu**, ne výjimka
v obvyklém smyslu.

**Proč to nedrží tohle kolo:** oprava, kterou jsem zadal, přesně tomuhle
stavu brání na straně **návodu** — a to je hotové. Že se do něj dá dojít
vlastní větou, je vada vedlejší a starší, ne důsledek téhle změny.
Měřeno: `before(středa, pondělí)` šlo zapsat i před tímhle kolem.

---

## Semantic Warnings

**W‑21 (drobnost) · `test_every_printed_offer_leads_somewhere` je pro
svůj dotaz pořád prázdný cyklus.** Pro `REVERSED_ORDER` je `_offers()`
prázdné, takže se aserce neprovede — jenže tentokrát to **říká vedlejší
test explicitně** (`== []`), takže iluze pokrytí nevzniká. Přesto: ten
test by měl jet nad dotazem, který **něco tiskne** (B, C nebo D),
jinak je ozdobný.

**W‑20 leží dál podle dohody.**

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: B‑16 — rozpor v uspořádání je TAH DIALOGU, ne
výjimka.**

**Gate:** čtyři věty výše musí projít bez pádu a čtvrtá musí říct, **co
se stalo a co s tím**. **Zasažená smlouva:** I‑1, I‑3, § 9.

1. Rozhodni, kde se to zachytí. **Doporučuju při zápisu**, ne až při
   dotazu: `attach` cyklus **odmítne** a vrátí to jako tah („tohle by
   uzavřelo pořadí do kruhu — `s0001`, `s0002` říkají opak"), takže se
   báze do rozbitého stavu vůbec nedostane. Je to `AttachError`, pro
   který už hierarchie existuje.
2. Když se rozhodneš pro zachycení až u dotazu, **musí to být verdikt,
   ne pád** — a `explain()` musí umět říct, které zápisy ten kruh tvoří.
3. **Nerozhoduj obojí najednou** a to, co nezvolíš, zapiš jako otevřenou
   otázku. Je to změna § 9, tedy vědomé rozhodnutí (I‑13).

**Můj counterexample — bez něj neschválím:** ty čtyři věty živě, bez
výjimky, a čtvrtá odpoví verdiktem nebo tahem, který **jmenuje zápisy
tvořící kruh**; „Je středa před pondělím?" po dvou větách **pořád**
netiskne žádné `? platí`; `before(pondělí, čtvrtek)` **pořád** nabídku
tiskne a po zapsání dá `A`; `jet/Plzeň` i `Mourek/savec` beze změny;
sedm domén se závěry beze změny (a když se některý změní, **napiš to**);
gate *Farmaka* `N`, parita 26/26, nula `RECALL_FAILURE`, testy zelené.

---

## ARCHIV — kolo #60

### Status: 🔴 FAIL — potlačení se udělalo v datech, ale ta věta se pořád tiskne; a testy, které to měly změřit, měří prázdno

**Kolo #60.** 801 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **57/57**, živá parita **26/26**, dialogy 7 / 16 / 10 se závěry
beze změny, gate *Farmaka* `N`, nula `RECALL_FAILURE`, celá stálá regrese
zelená. **Blokuji přesto** — můj counterexample byl formulovaný na to,
co uvidí člověk, a tam neprošel.

**Architectural Health Score: 8,5 / 10**

---

## Co je na tomhle kole dobré, ať to nezapadne

**Builderův vlastní nález je správný a je vážnější, než co jsem zadal.**
Když si každou nabídku zapsal a znovu se zeptal — tedy mým postupem —
zjistil, že poslední záchranná nabídka `before(středa, pondělí)` odpověď
sice změní, ale **na `InconsistentOrder`**. Ověřil jsem si to sám:

```
zapisuji before(středa, pondělí) … zapsáno
dotaz → InconsistentOrder: uspořádání kolem 'pondělí' si odporuje (H‑3)
```

**Nabídnout člověku větu, po které báze přestane odpovídat, je horší než
nenabídnout nic.** Ta úvaha je přesná. Jen se nedotáhla tam, kam patří.

**Varianta (1) mého zadání je hotová a funguje:** článek `⪯` se pro
jádrový predikát už nenabízí. **Protipól drží** — `jet(kdo:Petr,
kam:Plzeň)` pořád nabídne `contains(part:Praha, whole:Plzeň)` a po jeho
zapsání dá `A`, ověřeno. **Řetěz `member*` taky drží**: „Mourek je savec?"
nabídne `subset(sub:·kočka, sup:·savec)`, což je použitelné.

---

## Critical Blockers

### B‑14 · Potlačení je v `open_goals`, ale ta věta se tiskne PRÁVĚ PROTO, že je `open_goals` prázdné

**Změřeno živou cestou, ne z nahrávky:**

```
» Je středa před pondělím?
   → NEVÍM
     ? platí before(earlier:středa, later:pondělí)? [HYPOTÉZA — nikdo to neřekl]
   hypotéz v transkriptu: 1
```

To je **přesně ta věta**, po které se báze rozbije. Člověk ji vidí, může
ji říct, a systém ho k tomu vede.

**Root cause, jedno místo:** `gaps.py:125`, `else` větev
`GapReport.render()`:

```python
if self.open_goals:
    lines.extend(goal.render() for goal in self.open_goals)
else:
    lines.append(f"? platí {self.query}? [HYPOTÉZA — nikdo to neřekl]")
```

Vyprázdnit `open_goals` tu nabídku **nepotlačí — spustí ji**. Obě
poloviny opravy jdou proti sobě.

**Není to úzce mířené potlačení, prostě tam není.** Změřil jsem i případ
s PŘÍMOU opačnou hranou, kde by se mělo trefit nejspolehlivěji:

```
PŘÍMÁ opačná hrana before(po, st)      verdikt U · hypotéz 1
TRANZITIVNÍ opačný směr (dialog)       verdikt U · hypotéz 1
prázdná báze                           verdikt U · hypotéz 1
```

### B‑15 · Tři ze čtyř nových testů tvrdí něco o PRÁZDNÉ kolekci

`report.open_goals` je pro tenhle dotaz `()`, takže:

- `test_every_offered_link_actually_changes_the_answer` — cyklus přes
  `open_goals` **neprovede ani jednu aserci**. To je test, který má
  zapsat můj postup, a pro dotaz, který sám jmenuje, nezkontroluje nic.
- `test_a_kernel_query_is_not_offered_a_matching_link` — `all(...)`
  nad prázdnou n‑ticí je triviálně pravda.
- `test_a_hypothesis_that_would_break_the_base_is_not_offered` — tvrdí
  `open_goals == ()` **a k tomu přítomnost řádku „nikdo to neřekl"**,
  což je právě ten řádek, který tu škodlivou nabídku nese. Test si jako
  důkaz poctivosti bere text, na kterém je vada.

**Zasažená smlouva:** I‑14 a uživatelovo pravidlo, že ptát se není vada,
**pokud jde ze získané odpovědi stavět dál**.

**Vzorec je týž, který Builder sám pojmenoval o kolo dřív u W‑16:**
*„vypadá to jako pokrytí a není to pokrytí."* Tentokrát v jeho vlastním
novém testu.

---

## Semantic Warnings

**W‑20 leží dál podle dohody** — `[CHYBÍ: co znamená role před+Ins]`
i `Gen` u podtřídy jsou týž tvar šumu, uklidí se najednou.

**Drobnost, kterou Builder uklidil dobře:** „potřeboval jsem to přes
žádné pravidlo tohle nevyrábí" byla věta poskládaná z nesmyslu; `via`
pro „žádná cesta" je teď konstanta a renderuje se bez „přes".

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: rozhodnutí musí být tam, kde nabídka VZNIKÁ — tedy
v renderu, ne v `open_goals`.**

1. Poslední záchranná nabídka se **nesmí vytisknout**, když by zapsání
   té věty bázi rozbilo. Nejmenší bezpečná varianta: `GapReport` nese
   příznak „záchrannou nabídku netiskni" a `render()` místo ní řekne
   pravdu bez návodu — *„tohle mi nikdo neřekl a nabídnout ti větu,
   která by uspořádání uzavřela do cyklu, nemůžu."*
2. **Testy musí měřit `render()`, ne `open_goals`.** Vytáhni z něj každý
   řádek `? platí X?`, zapiš `X`, znovu se zeptej. Když je řádků nula,
   test to musí **říct jako nulu**, ne projít cyklem, který se neprovede.
3. Nesahat na běžné predikáty ani na řetěz `member*`. Obojí funguje,
   změřeno.

**Můj counterexample — a tentokrát ho napíšu tak, aby nešel splnit
prázdnotou:** projedu `render()` u „Je středa před pondělím?" a
**každý** řádek `? platí X?` zapíšu a znovu se zeptám; žádný nesmí
nechat odpověď `U` **ani** shodit bázi na `InconsistentOrder`; počet
takových řádků smí být nula, ale test to musí tvrdit explicitně.
K tomu: `jet(kdo:Petr, kam:Plzeň)` pořád nabídne `contains(part:Praha,
whole:Plzeň)` a po zapsání dá `A`; „Mourek je savec?" pořád nabídne
`subset(sub:·kočka, sup:·savec)`; sedm domén se závěry beze změny
(a když se některý změní, **napiš to**); gate *Farmaka* `N`, parita
26/26, nula `RECALL_FAILURE`, testy zelené.

---

## ARCHIV — kolo #59

### Status: 🟢 PASS — `before` z české věty drží; a odkryl vadu ve vrstvě, která vysvětluje

**Kolo #59.** 794 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **56/56**, živá parita **26/26**, dialogy 7 domén / 16 zapsaných
tahů / 10 závěrů, nula `RECALL_FAILURE`, gate *Farmaka* `N`. **Všechny
čtyři body mého counterexamplu splněny a změřeny mnou.** W‑18 splněno.

**Architectural Health Score: 9,5 / 10**

---

## Můj counterexample, položka po položce (živě, ne z nahrávky)

| podmínka | výsledek |
|---|---|
| `before` **z české věty** | ✓ `s0001`, `s0002` |
| tranzitivní odpověď | ✓ `A`, důkaz „první je na časové ose dřív než druhý" |
| důkaz cituje **oba** zápisy | ✓ `[doloženo: s0001, s0002]` |
| opačný směr `U`, ne `N` | ✓ `U` |
| šest stávajících domén beze změny | ✓ (7. je nový dialog: 6→7, 14→16, 8→10) |
| gate / parita / testy / doložky / recall | `N` · 26/26 · 794 · 56/56 · 0 |

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 6/6 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR-zákaz ✓ · I-16 ✓ · ∀→∃ U/N ✓
```

**Stráže jsem rozšířil o dvě nové a obě drží:** `before_of(Interval, Place)`
odmítnuto (porovnání napříč osami) a kvantifikátor na roli nad časem
odmítnut (§ 3.6). Builderovo rozhodnutí, že **sort stran plyne z relace,
ne ze jména role**, je správné a je to nejlepší věc na tomhle kole:
`whole`/`part` má `contains` i `within`, takže jméno role nestačí — a
hádat se nemá co (INV‑11).

**W‑18 splněno dobře.** `point` u kroku říká, že `CONFLICT` je **důsledek**
správného `∃steak`, a vysvětluje proč: dokud se psalo `∀steak`, měla ta
otázka jen důkaz proti; se správným čtením má i důkaz pro.

**Pokrytí jádra roste:** zapsané krokem `before`, `member`, `subset` —
**tři z devíti**. Zbývá `complete`, `contains`, `disjoint`, `name`,
`same_as`, `within`.

---

## Critical Blockers

**Žádné.** Odpovědi jsou správné, verdikty doložené.

---

## Semantic Warnings

### W‑19 · Vysvětlení `U` u JÁDROVÉHO dotazu nabízí článek, který evaluátor neumí použít

Tenhle nález je můj, není v Builderově hlášení, a je to nejvážnější věc,
kterou jsem na kole našel.

„Je středa před pondělím?" odpoví `U` — **správně** — a k tomu nabídne:

```
? platí within(part:pondělí, whole:středa)? [HYPOTÉZA — potřeboval jsem to přes fakt s0001, role earlier]
```

**Přidal jsem přesně to, co si řekl. Odpověď zůstala `U`.** Změřeno
čtyřmi způsoby — oba směry `within`, jednotlivě i v páru:

```
within(part:pondělí, whole:středa)              → U
within(part:středa,  whole:pondělí)             → U
within(po⊂st) + within(ut⊂po)                   → U
within(st⊂po) + within(po⊂ut)                   → U
```

**Root cause, jedno místo:** `gaps.py:_fact_goals` se ptá
`self.engine._compat(...)`, tedy relace shody `⪯`, a `_missing_link`
vrátí článek, který by `⪯` potřebovala. Jenže `before` je **jádrový**
predikát: `engine.py:303` posílá jádrové predikáty do `_match_kernel`,
kde se odpovídá z `before_proof`, což je **BFS nad grafem uspořádání** —
`_compat` se tam nezavolá **nikdy** a `within` do toho grafu nevede.
Vysvětlující vrstva tedy modeluje cestu, kterou vyhodnocení nejde.

**Není to chyba směru, je to chyba cesty.** Ověřil jsem si i protipól,
aby se to nespravilo příliš: u **běžného** predikátu návrh **funguje** —

```
jet(kdo:Petr, kam:Plzeň)  →  U
? platí contains(part:Brno, whole:Plzeň)?
po přidání článku          →  A   ✓
```

Dialog D na tomhle stojí a **nesmí se rozbít**.

**Zasažená smlouva:** I‑14 (vysvětlení se renderuje jen ze skutečného
důkazu — „potřeboval jsem to" je tvrzení o hledání a u jádrového dotazu
je nepravdivé) a uživatelovo pravidlo, že **ptát se není vada, pokud jde
ze získané odpovědi stavět dál**. Tady stavět dál nejde.

**Proč to nedrží gate:** verdikt `U` je správný a akceptační sada piní
**verdikt, ne text hypotézy** — ověřeno, krok má `answers: U` a `point`,
hypotézy v `anchors` nejsou. Náprava je proto celá ve vysvětlující
vrstvě.

**W‑20 (drobnost, Builder ji hlásí sám) · `[CHYBÍ: co znamená role
před+Ins]`** zůstává ve stopě z patra mapování rolí, které běží před
relačním a nevidí, že roli vzápětí někdo spotřebuje. Otázka z toho
nevzniká (G‑4 drží, ověřeno: `vznikla otázka na uživatele? NE`), takže
je to šum v transkriptu. Týž tvar má `Gen` u podtřídy — uklidit obojí
najednou, **ne teď**.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: W‑19 — vysvětlení `U` musí kopírovat cestu, kterou
se doopravdy hledalo.**

1. `_fact_goals` nesmí nabízet článek `⪯` pro dotaz, který jde do
   `_match_kernel`. Nejmenší bezpečná varianta: pro jádrové predikáty
   ho **nenabízet vůbec** a nechat pravdivé „nikdo to neřekl".
2. Lepší, když se povede: nabídnout článek, který **ta** cesta umí —
   u `before` je to chybějící **hrana uspořádání** (`before(X, Y)`),
   ne `within`.
3. Nesahat na běžné predikáty. `contains` u `jet(kam:…)` funguje a
   dialog D na tom stojí.

**Můj counterexample — bez něj neschválím:** „Je středa před pondělím?"
dá `U` a nenabídne **žádnou** hypotézu, kterou po přidání do báze
odpověď nezmění — ověřím to tak, že **každý** nabídnutý článek zapíšu
a znovu se zeptám; `jet(kdo:Petr, kam:Plzeň)` **pořád** nabídne
`contains(part:Brno, whole:Plzeň)` a po jeho přidání dá `A`; sedm domén
se závěry beze změny (a když se některý změní, **napiš to**); gate
*Farmaka* `N`, parita 26/26, nula `RECALL_FAILURE`, testy zelené.

**Očekávaný výsledek:** systém se pořád ptá — o to nejde a ptát se má —
ale co si vyžádá, to umí spotřebovat.

---

## ARCHIV — kolo #58

### Status: 🟢 PASS — N‑8 hotové; jedna podmínka mého counterexamplu byla vnitřně rozporná a je to moje chyba

**Kolo #58.** 780 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **55/55**, živá parita **22/22**, dialogy 6 domén / 14 zapsaných
tahů / 8 závěrů, nula `RECALL_FAILURE`, gate *Farmaka* `N`. **W‑15 i W‑16
uzavřeny, ověřeno reprodukcí.**

**Architectural Health Score: 9,5 / 10**

---

## Nejdřív moje chyba, ať se o ni nikdo nezakopne

**Můj counterexample z kola #57 žádal dvě věci, které nejdou splnit
najednou:** aby dialog zapsal `jíst(co:∃steak, kdo:Petr)` **a** aby
zůstalo „šest domén se závěry beze změny". Jenže právě ta změna zápisu
**musí** změnit odpověď na „Jedl Petr maso?": s `∃steak` v bázi
a `steak ⊆ maso` má ta otázka nově i **důkaz pro**, takže z `N` je
`CONFLICT`. Podmínku jsem napsal špatně já.

**Změřeno:**

```
Vegetarián a steak   dřív ['N', 'CONFLICT']   teď ['CONFLICT', 'CONFLICT']
ostatních pět domén  beze změny
```

**Nový verdikt je věcně SPRÁVNĚJŠÍ než starý.** Oba důkazy jsou v pořádku:
pro — `jíst(co:∃steak)` + `subset(steak, maso)`; proti — distribuce
generického popření přes `member`. Distribuce se neztratila, je uvnitř
sporu.

**Co Builderovi vytýkám, není ta změna, ale že ji ohlásil jako „beze
změny".** Kolize dvou mých podmínek se měla pojmenovat, ne odškrtnout.
Zlatý závěr, který se změní a nikdo to nezapíše, je přesně ten mechanismus,
kterým akceptační sady tichnou.

---

## Můj counterexample, položka po položce (měřeno mnou)

| podmínka | výsledek |
|---|---|
| dialog zapíše `jíst(co:∃steak, kdo:Petr)` | ✓ `s0004` |
| krok „Jedl Petr steak?" → `CONFLICT` se **dvěma** důkazy | ✓ |
| větev tahu se v akceptačním běhu provede ≥ 1× | ✓ **4×** (spy‑probe) |
| `test_the_answer_generalises_beyond_this_one_sentence` | ✓ PASSED |
| kladná buňka `∀ → ∃` pořád `U` | ✓ (záporná `N`) |
| dialog B, gate *Farmaka*, parita, testy, recall | ✓ · `N` · 22/22 · 780 · 0 |
| šest domén se závěry beze změny | ✗ — **a je to moje chyba, viz výše** |

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 4/4 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR-zákaz ✓ · I-16 ✓
```

**Nesahal jsem na jeho měření, udělal jsem si vlastní:**

- **tvar se per‑větnou odpovědí NEUČÍ** — porovnal jsem lexikon před
  a po celém dialogu: **22 položek → 22, obsahově totožné**. A silnější
  než to: v transkriptu se systém ptá **čtyřikrát na týž tvar**
  `NOUN/Sing/Acc/obj`, i potřetí a počtvrté. Sada to hlídá chováním, ne
  porovnáním zápisů — kdyby se tvar naučil, krok s odpovědí by spadl na
  „role nečeká".
- **rozklad `U` (A‑27)** najde přes celou sadu **jediné** `U`:
  `jet(kdo:Petr, kam:Plzeň)` s `MISSING_LINK`. Mezitímní `U` na
  nedočtené otázce se do rozkladu **nepropsalo** — a to bylo to jediné
  místo, kde jsem u téhle změny čekal tichou vadu.

**Rozšíření nad rámec beru a je správné:** A‑27 přehrával dialogy vlastní
smyčkou přes `session.utter`, takže po přidání tahů četl **jinou
posloupnost než gate**. Metrika, která měří jiný běh než ten, na kterém
stojí gate, je horší než žádná — obojí by svítilo zeleně.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑18 (nový) · změněný zlatý závěr není nikde zapsaný.** „Jedl Petr
maso?" má dnes `CONFLICT` místo `N` a v dialogu o tom není řádek.
Nejmenší bezpečná náprava: `point` u toho kroku, který řekne, že
`CONFLICT` je důsledek správného `∃steak` a že distribuce je uvnitř
důkazu proti.

**W‑15 uzavřena** — sada už chybnou kvantifikaci nepiní; do báze jde
`∃steak`. **W‑16 uzavřena** — větev tahu se provede 4× a má vlastní test,
který **počítá průchod, ne existenci pole**. **W‑17 uzavřena jako
přijatá mez** — Builderův důvod nesahat na „Datel klove." je správný:
zapsat ji do sady by znamenalo fixovat rozbor, o kterém víme, že je
vadný.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: česká cesta k jádrovým relacím, které dnes žádná
věta nevyrobí — začni `before`.**

**Gate:** akceptační sada zapisuje **dva z devíti** jádrových predikátů.
Změřeno:

```
zapsané krokem: member, subset
nezapsané:      before, complete, contains, disjoint, name, same_as, within
```

**Root cause:** jádro ty uzávěry umí a testy je pokrývají **na úrovni
formulí**, ale žádná česká věta k nim nevede. **Zasažená smlouva:** I‑2
(jazyk navrhuje, jádro rozhoduje) — vrstva, která nemá jak navrhnout,
tu smlouvu nenaplňuje.

**Riziko, když se to nechá být:** je to **týž vzorec jako B‑10, B‑11
i B‑13** — schopnost v jádře, kterou čeština nedosáhne, takže nikdo
nezjistí, že nefunguje. Tři z posledních čtyř blokerů měly tenhle tvar.

**Proč `before` první:** je to nejbližší článek k odstavci *posloupnost*
z desítky, čeština ho nese jasným tvarem (*„Petr přišel před Janou."*,
*„Nejdřív …, pak …"*), a uzávěr je tranzitivní, takže doména hned
prověří řetěz, ne jen jeden zápis.

**Můj counterexample — bez něj neschválím:** nová doména zapíše `before`
**z české věty**, odpoví na otázku, na kterou je potřeba **tranzitivní**
krok (`A před B`, `B před C` → *„Bylo A před C?"* → `A` s důkazem přes
oba zápisy), **a** otázka na opačný směr dá `U`, ne `N` — otevřený svět;
šest stávajících domén se závěry beze změny (a když se některý změní,
**napiš to**), gate *Farmaka* `N`, parita ≥ 22/22 s novými větami
v zlaté sadě, nula `RECALL_FAILURE`, testy zelené.

---

## ARCHIV — kolo #57

### Status: 🟢 PASS — B‑13 zavřeno, každá podmínka mého counterexamplu změřena

**Kolo #57.** 771 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **54/54**, živá parita **22/22**, dialogy 6 domén / 14 zapsaných
tahů / 8 závěrů, nula `RECALL_FAILURE`, gate *Farmaka* `N`. Blokující
nález z minulého kola je **uzavřený** a ověřil jsem to reprodukcí, ne
převzetím.

**Architectural Health Score: 9,5 / 10**

---

## Můj counterexample, položka po položce (měřeno mnou)

| podmínka | výsledek |
|---|---|
| kladná buňka `∀ → ∃` pořád `U` | ✓ `U` |
| záporná buňka `∀ → ∃` | ✓ `N` |
| dotaz smí být UŽŠÍ, ne širší | ✓ `∃steak` → `N`, `∃potravina` → `U` |
| dialog B (`konkrétní × ∃` → `None`) | ✓ beze změny, **i pod negací** |
| `CONFLICT` se dvěma důkazy při **správném** `∃steak` | ✓ `s0004` × `s0001+s0002+s0003` |
| šest domén, závěry | ✓ beze změny |
| gate *Farmaka* | ✓ `N` |
| parita / testy / recall | ✓ 22/22 · 771 · 0 |

```
B-1 ✓ · B-2 ✓ · dialogB ✓ · dialogB pod negací ✓ · disjoint→N ✓
CONFLICT ✓ · stráže 4/4 ✓ · same_as ✓ · M-1 ✓ · G-3 ✓ · OR-zákaz ✓ · I-16 ✓
```

**Oprava je ta jedna buňka a nic víc.** Přečetl jsem ji celou:
`_compat` dostal `negated`, nová větev sedí **až za** všemi kladnými,
je guardovaná `negated and pq is EXISTS and fq is FOR_ALL`, a pro
`Variable` vrací `None` — výčet přes prvky zůstal na `member` v těle
pravidla. Ověřil jsem i to, co by tiše prosáklo jinudy: `Atom.signature`
nese polaritu, takže `candidates` nikdy nevrátí fakt opačného znaménka
a `pattern.is_negated and fact.is_negated` je přesně „ta dvojice je
záporná". **Smíšená polarita se do kladných buněk dostat nemůže.**

**Bod (3) mého zadání splněn doslova.** W‑14 je v § 3.3 zapsaná jako
otevřená otázka s poznámkou, že přidaná buňka platí při obojím čtení,
protože obě strany mluví o téže množině. **Nerozhodl to mimochodem** —
přesně to jsem žádal a je to I‑13 respektované.

**Bod (4) nesplněn — a důvod jsem si ověřil sám, ne převzal.** Přehrál
jsem dialog s holým lexikonem: odpověď `→∀` na „Vegetarián nejí maso."
naučí **tvar** `NOUN/Sing/Acc/obj`, a čtvrtá věta se pak čte rovnou jako
`jíst(co:∀steak, …)` — role `co` už nečeká, systém se na ni **neptá**.
Per‑větná kvantifikace tedy opravdu potřebuje **nový druh tahu**, ne jiné
zapojení stávajícího. To není výmluva, to je změřený fakt, a eskalovat
ho místo improvizace bylo správně.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑15 (nesu dál, ale zeslabená) · akceptační sada pořád piní chybné
čtení.** Krok 4 má `writes: jíst(co:∀steak, kdo:Petr)` a test to tvrdí.
Od B‑13 už na tom **závěr domény nestojí** — `CONFLICT` se dvěma důkazy
platí i s `∃steak` a je to změřené — takže to konečně **je** mez a ne
nosný trám. Zůstává ale pin: dokud nový tah nepřijde, sada tu chybnou
kvantifikaci **brání**. `limit` u kroku Builder přepsal a nové znění je
věcné — píše, že doptání na větu dnes NEEXISTUJE, s odkazem na test.

**W‑16 (nový, změřený) · větev „krok je TAH" se v akceptačním běhu
provede 0×.** Runner umí `Step` jako tah (`_answer`, tvar se dopočítá
z čekající role), ale **žádný dialog `answers_quantifier=` nemá** —
ověřeno spy‑probem přes celou sadu: `_answer` zavoláno **0×**. Je to
mašinerie v tom samém harnessu, který hlídá gate, a sama nehlídaná.
Ne blokující (nic dnes netvrdí), ale nesmí zůstat nepoužitá dvě kola.

**W‑17 (drobnost, ne vada) · „Datel klove." dnes živý parser vrací jako
`flat`** a systém větu **poctivě odmítne** (0 čtení, otázka, žádný tichý
zápis — I‑1 drží). Věta není ve zlaté sadě, takže parita ji nevidí.
Smyčku učení to neohrožuje: `test_the_answer_generalises_beyond_this_one_sentence`
ji piní na nahrávkách. Zapisuju jen proto, že demo z dřívějšího kola na
té větě stálo.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: tah, který odpovídá na kvantifikátor JEDNÉ VĚTY.**
Souhlasím s tvým návrhem a teď už mu nic nepředchází.

**Gate:** šestá doména stojí na správném čtení **i v dialogu**, ne jen
na úrovni formulí. **Root cause:** `answers_quantifier` váže odpověď na
`StructuralSignature`, tedy na tvar; věta jako nositel kvantifikace dnes
nemá kam odpověď uložit. **Zasažená smlouva:** § 5.2 a L‑3 (tichý default
kvantifikátoru je zakázaný) — nový tah je **nesmí** obejít.

1. Odpověď se váže na **čekající predikaci**, ne na tvar. Tah na tvar
   **zůstává** — je to jiná otázka, ne jeho náhrada.
2. Nesmí vzniknout tichý default: když je věta rozhodnutá jednotlivě,
   tvar se tím **neučí**.
3. První dialog, který ho použije, je *Vegetarián a steak*, krok 4 —
   tím padá W‑15 i W‑16 najednou.

**Můj counterexample — bez něj neschválím:** šest domén se závěry beze
změny, gate *Farmaka* `N`, parita 22/22, 771+ testů, nula
`RECALL_FAILURE`, kladná buňka `∀ → ∃` pořád `U`, dialog B beze změny,
**`test_the_answer_generalises_beyond_this_one_sentence` pořád zelený**
(učení tvaru se novým tahem nesmí rozbít) — **a** dialog *Vegetarián
a steak* zapíše `jíst(co:∃steak, kdo:Petr)`, krok 6 přesto odpoví
`CONFLICT` se **dvěma** důkazy, a větev tahu se v akceptačním běhu
provede **aspoň 1×**.

**Očekávaný výsledek:** `limit` u kroku 4 se smrskne na jedinou větu —
že tvar sám kvantifikaci neurčuje — a sada přestane pinovat čtení,
o kterém sama píše, že je špatné.

---

## ARCHIV — kolo #56

### Status: 🔴 FAIL — závěr domény drží jen na čtení, které dialog sám označuje za věcně chybné

**Kolo #56.** 762 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **53/53**, živá parita **22/22**, dialogy 6 domén / 14 zapsaných
tahů / 8 závěrů. Celá regrese i gate *Farmaka* prošly. **Blokuji přesto** —
a ne kvůli ničemu z toho, co se měří, ale kvůli tomu, co gate *znamená*.

**Architectural Health Score: 9,0 / 10**

---

## Co jsem změřil sám (ne převzal)

```
B-1 ✓ · B-2 ✓ · ⪯ ✓ · disjoint→N ✓ · CONFLICT ✓ · stráže 4/4 ✓
same_as ✓ · M-1 ✓ · G-3 ✓ · OR-zákaz ✓ · I-16 ✓
GATE Farmaka → N ✓
živá parita: vět 22 · shoduje se 22 · liší se 0 · nedostupných 0
762 passed · mypy: no issues in 58 source files
dialogy: 6 domén · 14 zápisů · 8 verdiktů · 3 zapsané meze
RECALL_FAILURE na dialozích: 0
```

**Builderova čísla sedí do jednoho.** Přehrál jsem celý dialog *Vegetarián
a steak* a řetěz běží přesně tak, jak ho popsal: `member` → generické
popření → `subset` → **NE** přes distribuci → **SPOR** se dvěma důkazy,
doloženo `s0001–s0004`. Nic z toho nerozporuju.

**`limit` gate neoslabuje** — ověřeno v runneru: pole je dokumentace,
`test_dialogue_reads_writes_and_answers_as_recorded` tvrdí každý krok bez
ohledu na ně. To je správně a je to důležité; kdyby `limit` krok vypínal,
byl by to znovu vzorec G‑1.

---

## Critical Blockers

### B‑13 · Relace shody `⪯` bere silnou negaci jako průhlednou — a negace obrací monotonii

**Root cause, jedno místo:** `core_semantics/engine.py:781` —

```python
# ∃ × ∀ by potřebovalo neprázdnost group; v otevřeném světě
# nedoložitelné. ∀ × ∃ neplatí nikdy.
return None
```

`_compat` vidí **jen role**, polaritu atomu nikdy. Existenční import se
proto uplatní i pod negací, kde není potřeba. Změřená matice — táž
dvojice tvarů, kladný a záporný fakt:

```
            fakt→dotaz    kladný   záporný
            ∀ → ∀              A         N
            ∀ → ∃              U         U     ← záporná buňka je věcně N
            ∃ → ∀              U         U
            ∃ → ∃              A         N
```

Záporný sloupec je **mechanické zrcadlo** kladného. Jenže pod negací se
směr plynutí obrací: z `¬jíst(co:∀maso)` = „pro každé maso neplatí, že
je jí“ **plyne** `¬jíst(co:∃maso)` — a neplyne to z neprázdnosti, plyne
to i pro prázdnou třídu. Odvozovací povinnost je `subset(dotaz, fakt)`,
tedy táž jako v kladné buňce `∀ × ∀`. Kladná buňka `∀ → ∃` má naopak U
**správně** a musí U zůstat: tam existenční import chybí právem.

**Zasažená smlouva:** § 3.3 (relace shody), I‑3 (spor se musí ohlásit).

**Proč to blokuje tohle kolo, ne příští:** závěr domény `CONFLICT` je
dosažitelný **jen** se čtením `∀steak`, které dialog sám u kroku 4 popisuje
jako věcně chybné. Změřil jsem, co udělá čtení správné:

```
dnešní dialog     fakt ∀ / zápis ∀steak / dotaz ∀steak : CONFLICT (2 důkazy)
OPRAVENÉ ČTENÍ    fakt ∀ / zápis ∃steak / dotaz ∃steak : A
smíšené           fakt ∀ / zápis ∃steak / dotaz ∀steak : N
```

Se správným čtením systém odpoví **ANO, Petr jedl steak** — a spor,
na který má oba důkazy v bázi, **neohlásí**. To není mez, to je I‑3.
Dnešní zelený gate tu vadu zakrývá tím, že běží po chybné větvi.

**Riziko, kdyby se to nechalo být:** Builderův navržený směr — doptání
`→∀` uvnitř akceptačního dialogu — udělá gate **červený**. Jakmile člověk
na „Petr jedl steak.“ správně odpoví „jen o jednom“, doména o závěr přijde.
Ten směr je tedy nejen nedostatečný, on tuhle vadu **odkryje** místo aby
ji spravil. Pořadí není detail.

---

## Semantic Warnings

**W‑14 · Rozsah negace vůči `∃` roli není nikde rozhodnut.** Při opravě
B‑13 vyplave sousední buňka: `¬P(role: ∃F)` se dá číst jako `¬∃x∈F.P(x)`
(pak splývá s `∀`) i jako `∃x∈F.¬P(x)`. Tohle **není mechanická úprava** —
je to rozhodnutí o § 3.3, tedy I‑13. Oprava B‑13 se má omezit na jedinou
buňku, kterou doména potřebuje, a rozsah negace nechat zapsaný jako
otevřenou otázku, ne ho vyřešit mimochodem.

**W‑15 · `shapes` jsou na doménu, věta je na větu.** Builderův nález —
`NOUN/Sing/Acc/obj` je v „Petr jedl steak“ existence a ve „Vegetarián nejí
maso“ obecnost — je **správný a cenný** a nechal ho vidět z obou stran
(zlatá sada `obj → ∃`, dialog `∀`, u toho poznámka proč). Nesouhlasím jen
s dispozicí: zapsat věcnou chybu jako `limit` je poctivé u **meze**, ne
u kroku, na kterém stojí **závěr gate**.

---

## Action Items for Agent 1

**JEDINÝ DALŠÍ SMĚR: `⪯` pod silnou negací (B‑13). Doptání `→∀` uvnitř
dialogu až po něm.**

1. `_compat` dostane polaritu atomu (nese ji `Atom.negated`, `_match_atom`
   ji má po ruce) a **jedinou** novou buňku: `dotaz ∃ × fakt ∀`, oba
   záporné, s důkazní povinností `subset(cíl dotazu, cíl faktu)`.
2. Kladná buňka `∀ → ∃` **zůstane `U`** — existenční import se nedoplňuje.
3. Rozsah negace vůči `∃` (W‑14) se **nerozhoduje**, zapíše se jako otázka.
4. Až pak přepsat krok 4 dialogu na správné `∃steak` a teprve potom
   stavět `Step`, který je tah.

**Můj counterexample — bez něj neschválím:** po opravě musí platit
*všech* šest domén beze změny závěrů, gate *Farmaka* `N`, parita 22/22,
762+ testů, nula `RECALL_FAILURE`, **kladná buňka `∀ → ∃` pořád `U`**,
dialog B (`konkrétní × ∃` → `None`) beze změny — **a** dialog
*Vegetarián a steak* dá `CONFLICT` se **dvěma** důkazy i tehdy, když se
„Petr jedl steak.“ čte jako `∃steak`.

**Očekávaný výsledek:** závěr domény přestane viset na chybném čtení a
`limit` u kroku 4 se smrskne na to, čím opravdu je — na poznámku o tom,
že tvar sám kvantifikaci neurčuje.

---

## ARCHIV — kolo #55

### Status: 🟢 APPROVE — měří se, PROČ padlo `U`

**Kolo #55.** 753 testů zelených, `mypy --strict` čistý na 58 souborech,
doložky **53/53**, živá parita **16/16**, dialogy 5 domén / 10 zapsaných
tahů / 6 závěrů. **A‑27 ověřeno mnou včetně mé podmínky.**

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

**Moje podmínka — metrika nesmí nabízet číslo k vylepšování:**

```
veřejné symboly modulu: Diagnosis, UnknownReason, defects, diagnose, survey, render
symboly obsahující score/rate/ratio/precision/total:  ŽÁDNÉ ✓
```

**Devět jádrových tvarů — zapsat a hned se zeptat:**

```
member ✓ · subset ✓ · subset/alg ✓ · member/alg ✓ · contains ✓
before ✓ · same_as ✓ · complete ✓ · reifikovaný vztah ✓
recall failures: 0
```

**Na akceptačních dialozích** jediné `U` je `Jel Petr do Plzně?` s důvodem
`MISSING_LINK` — legitimní otevřený svět. **Nula vad.**

**Regrese celá** včetně G‑3 recallu, zákazu eliminace `OR` a I‑16; gate
*Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Co na tomhle kole stojí za zapsání

**Zábrana proti Goodhartovi je v kódu, ne v komentáři.**
`test_the_module_offers_no_score_to_minimise` kontroluje, že modul
nevystavuje žádný symbol se jménem `score`/`rate`/`ratio`/`precision`/
`total`, a druhý test hlídá, že se ani výpis nesčítá do jednoho čísla.
Builderův důvod je přesný:

> Číslo, které jde vylepšit, se dřív nebo později vylepšovat začne —
> a vylepšit počet `U` jde jen hádáním.

To je nejlepší možná odpověď na mou podmínku: **neudělal ji pravidlem,
udělal ji nemožnou.**

**„Odvoditelnost není přítomnost"** — detektor vady porovnává **rovnost
formulí**, ne odvoditelnost. `member(Mourek, savec)` z báze *plyne*, ale
v bázi *není*, takže to vada není. Cokoli volnějšího by z metriky udělalo
**druhý evaluátor** — a ten by měl vlastní chyby, o kterých by nikdo
nevěděl.

**Přiznaný stub a jeho zdůvodnění.** `RECALL_FAILURE` dnes v systému
**není**, takže se detektor nedá pinnout na skutečném enginu. Kdyby ho
Builder testoval jen tím, že nic nenajde, **prošel by i tehdy, kdyby
přestal hledat úplně**. `_AmnesiacEngine` je proto součást měření, ne
obcházení. To je přesně ta úvaha, kterou jsem vyžadoval u sady útoků
v kole #31: zelený test má něco *měřit*, ne jen svítit.

**A upřesnění, které našel test, ne úvaha:** `GapFinder` vrací jako
otevřený podcíl i **sám dotaz**, takže do `MISSING_LINK` původně spadlo
každé `U` a `NOT_STATED` byla prázdná. Bez rozlišení by z rozkladu nešlo
poznat, **na co se dá odpovědět** — což je jeho jediný praktický užitek.

---

## Semantic Warnings

**Žádné nové.**

---

## Stav projektu

| oblast | stav |
|---|---|
| Pět akceptačních dialogů | 🟢 procházejí, verdikty jsou podmínky |
| Jádro | 🟢 0.1.10, 53 doložek, invarianty drží |
| Živá služba | 🟢 parita 16/16 |
| Měření `U` | 🟢 rozklad podle důvodu, nula vad |
| `Postřižiny`, `Roník` | ⬜ znalost světa — mez, ne úkol |

---

## Jeden další směr: **rozšířit akceptační sadu o odstavec 6 z deseti**

Poprvé je uzavřená sada i všechny řešitelné meze. Cíl, který zadal
člověk — **deset komplexních odstavců** — zůstává otevřený, a je čas
posunout **gate**, ne hledat práci uvnitř splněného.

**Vybírám odstavec 6 (logický rozpor: vegetarián × steak).** Důvod:

- **Změřil jsem ho v kole #38** a **funguje** — `SPOR V BÁZI` přes
  `subset(steak, maso)`. Ale **strukturovaně**; česky ne.
- Je to **jediný z deseti, jehož závěr je přímo jádrová operace**
  (`CONFLICT` se dvěma důkazy), takže neotvírá novou sémantiku — jen
  ověří, jestli **čeština unese celý řetěz**: `member`, `subset`,
  pravidlo, a rozpor.
- Ostatní odstavce potřebují buď abdukci (1), pragmatiku (2, 7),
  shrnutí (3 — mimo architekturu), nebo modalitu (9).

**Co to prověří:** dnes umí čeština `member`, `subset`, `disjoint`
a obyčejné vztahy. **Pravidlo se česky říct nedá** — a odstavec 6 ho
potřebuje (*„vegetarián nejí maso"*). Tohle je tedy test, kde se ukáže,
jestli je další patro **pravidlo z věty**, nebo jestli stačí pravidla
zadávat strukturovaně a jazyk nechat na faktech.

**Nejmenší bezpečná změna — a je to průzkum, ne stavba:** zapsat
odstavec 6 jako **šestý akceptační dialog** s tím, co dnes jde česky,
a **co nejde, zapsat jako `limit` s důvodem**. Teprve z toho vyjde, co
stavět.

**Counterexample, který musí projít:** všech pět dnešních domén, gate
*Farmaka*, parita 16/16 a nula `RECALL_FAILURE` — nový dialog nesmí nic
z toho pohnout.

**Očekávaný výsledek:** šestý dialog v sadě, u každého kroku buď verdikt
jako podmínka, nebo zapsaná mez s důvodem; a jasná odpověď na otázku,
**jestli je pravidlo z věty další patro, nebo ne**.

---

## Archiv — kolo #54 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #54. 738 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **52/52**, živá parita **16/16**, dialogy 5 domén / 10 zapsaných
tahů / 6 závěrů. **N‑7 ověřeno mnou včetně účinku.**

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

```
» Filipovo auto je modré.    ✓ být(co:·modrý, kdo:auto)   [s0002]   5 výroků, 'být(' 1×
» →' Filipovo je Filip.      ✓ rozhodnuto  přivlastnění → Filip
                             ✓ zapsáno [s0006]  vlastnit(co:a1, kdo:Filip)

   po tahu 9 výroků, 'být(' pořád 1×   ← ŽÁDNÝ dvojí zápis
   ÚČINEK: vlastnit(Filip, a1) → A, doloženo ['s0006']
```

**Moje counterexamply:**

```
(a) bez odpovědi:  zapsáno, neptá se, 'vlastnit' v bázi: žádné ✓
(b) To auto je modré.  beze změny ✓
(c) vzorů obsahujících „Filip": žádný ✓
```

**Regrese celá** včetně G‑3 recallu, zákazu eliminace `OR` a I‑16; gate
*Farmaka* `N`.

*(Poznámka k vlastnímu měření: první pokus jsem volal `names_owner`
s predikací místo rozboru a dostal `AttributeError`. Chyba v mé sondě,
ne v kódu.)*

---

## Critical Blockers

**Žádné.**

---

## Co na tomhle kole stojí za zapsání

**Rozdělení „co je na tvaru a co na slově" je jinak, než šlo z mého
zadání číst doslova — a je to správněji.** Že přivlastnění označuje
vlastníka, je **vlastnost konstrukce**: platí pro každé `amod` s
`Poss=Yes` a **není to rozhodnutí**, takže se to neučí vůbec. **Kdo** je
ten vlastník, je vlastnost **jedné zmínky**, takže leží v žurnálu jako
tah, ne v lexikonu.

Můj požadavek *„vzor ať je na tvaru, ne na slově"* je tím splněný
v silnější podobě: **na slově není vzor žádný.**

**Vada, kterou si našel uprostřed a která by byla regrese:** první verze
pouštěla tah přes `_settle`, takže se věta zapsala **podruhé** — v bázi
by ležely dva `být(co:·modrý, kdo:a1)` a ten první by nikdo neodvolal.
Je to **přesně ta vada, kterou `_settle` jinde hlídá**, jen se k ní šlo
zezadu. Ověřil jsem počtem: `být(` je v bázi **jednou**.

**Vlastnictví se připíná jen k uzlu** — dokud se odkaz nerozřešil, není
ke komu. *„Nějaké auto patří Filipovi"* je jiné tvrzení než *„TOHLE auto
patří Filipovi"* a jen to druhé věta nese; vyrobit si uzel by bylo
zakládání individua evaluací (§ 0.2).

**A oprava vlastního testu:** přehrávací test plnil bázi přes
`kb.attach`, jenže **přímý zápis do báze v žurnálu není**, takže by test
měřil neúplný záznam a padal na něčem jiném, než co má hlídat.

---

## Semantic Warnings

**Žádné nové.**

---

## Stav: akceptační sada uzavřena, řešitelné položky vyčerpány

| položka | stav |
|---|---|
| Pět akceptačních dialogů | 🟢 procházejí, verdikty jsou podmínky |
| Přivlastnění | 🟢 určitý popis + vztah vlastnictví tahem |
| `Postřižiny`, `Roník` | ⬜ **znalost světa — není co stavět** |

Builderovo *„nebudu předstírat opak"* u znalosti světa **potvrzuji**.
Rozpoznat vlastní jméno mimo rejstřík morfologie nedodá; je to mez, ne
úkol.

---

## Jeden další směr: **`Unknown precision` — měřit, jestli `U` znamená nedostatek důkazu**

Poprvé není na stole ani nesplněný scénář, ani řešitelná mez. Vybírám
podle **rizika pro správnost**, jak ukládá mandát.

**Problém:** systém dnes umí říct `U` a `GapFinder` umí říct proč — ale
**nikdo neměří, jestli `U` opravdu znamená „chybí důkaz"**, a ne
„přehnaná opatrnost". Druhý externí posudek to označil za nejcennější
metriku a nemáme ji.

**Proč to je riziko, ne kosmetika:** systém, který je příliš opatrný, má
skvělou přesnost a je **prakticky nepoužitelný** — a dnes to nepoznáme.
Všechny naše metriky měří, co systém **udělal**; žádná neměří, co udělat
**mohl a neudělal**.

**Nejmenší bezpečná změna:** vzít případy, kde padlo `U`, a u každého
z `GapFinder` **vytáhnout důvod**; rozlišit *chybí fakt* (legitimní `U`),
*chybí pravidlo* (kandidát na učení) a *je to v bázi, jen se to nenašlo*
(**vada**). To poslední je přesně G‑3, které jsme jednou už našli — a
tahle metrika by ho odhalila **sama**.

**Counterexample, který musí projít:** metrika **nesmí** dávat pokyn
odpovídat víc — `U` je legitimní verdikt a snížit jejich počet hádáním
by bylo horší než nic. Měří se **důvod**, ne počet.

**Očekávaný výsledek:** rozpad `U` podle důvodu na zapsaných dialozích;
kdyby se objevil případ „v bázi to je, ale nenašlo se", je to bloker.

---

## Archiv — kolo #53 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #53. 728 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **51/51**, živá parita **16/16**, dialogy 5 domén / 10 zapsaných
tahů / 6 závěrů. **G‑4 opraveno a ověřeno mnou ve všech třech větvích.**

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

```
jeden kandidát    značka ✓   question = None   zapsáno s0002
dva kandidáti     značka ◐   question = JE     zapsáno None
žádný kandidát    značka ◐   question = JE     zapsáno None
```

Značka se řídí týmž stavem jako otázka — tvrzení o tahu, ne ozdoba.

**Můj counterexample (c) — otázka bez odpovědi se neumlčela:**

```
Vrabec létá. (holá knihovna)   ◐  ptá se na kvantifikátor ✓
Kočka je savec.                ◐  ptá se na relaci ✓
```

**Regrese celá** včetně G‑3 recallu, zákazu eliminace `OR` a I‑16; gate
*Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Co na tomhle kole stojí za zapsání

**Builder sám pojmenoval, co je na tom nálezu nepříjemné:** touž vadu
v jiném kabátě **popsal o čtyři kola dřív** (kolo #49, otázka čtená ze
stopy) a podruhé ji nepoznal. Zapsal si to do **docstringu, ne do
předávky** — což je správné místo, protože předávku nikdo znovu nečte.

**Jeho test, který jsem nežádal, je nejcennější kus kola:**
`test_an_open_quantifier_is_not_silenced_by_the_fix`. Bez něj by šlo
opravu **přehnat do druhé strany** a umlčet otázku, která odpověď nemá —
a to by byla **horší** vada než původní, protože by se projevila jako
**ticho**. Přesně ta symetrie, kterou by měl hlídat každý „přestaň se
ptát" fix.

**Matice ho chytila popáté** — doložku `S-24` nejdřív zakotvil na
`Grounded.anchors`, tedy na holé datové pole bez dokumentace. Přesun na
`Session._settle` je správný: **smlouvu nenese struktura, ale místo,
které rozhoduje.**

---

## Semantic Warnings

**Žádné nové.**

---

## Jeden další směr: **tah, kterým člověk pojmenuje vlastníka**

Builder to navrhl dvakrát a nechal rozhodnutí na mně. **Potvrzuji.**

**Problém:** `Filipovo auto je modré.` dnes zúží referenci, ale vztah
vlastnictví **do báze nejde**. Rozbor jméno vlastníka nedává (`Filipův`
→ `Filip` je derivační morfologie) a hádat ho by byl dohad zadrátovaný
do interpretu.

**Proč právě tohle:** je to **jediná otevřená položka, kterou lze
odstranit prací**, a ne mez. `Postřižiny` a `Roník` jsou znalost světa —
tam není co stavět. Přivlastnění má naproti tomu **hotovou mašinerii**:
`→=` a `→@` jsou tentýž tvar smyčky, jen na jiné otázce.

**Nejmenší bezpečná změna:** tah, kterým člověk poví, **koho** to
přivlastňovací adjektivum označuje (`Filipovo = Filip`), a z toho vztah
vlastnictví. Vzor ať je **na tvaru**, ne na slově — jinak se učí každé
jméno zvlášť.

**Counterexample, který musí projít:** (a) **bez** té odpovědi se
`Filipovo auto je modré.` chová **přesně jako dnes** — zúžení reference,
žádná třída, otázka na odkaz; nová schopnost nesmí změnit dosavadní
chování těch, kdo ji nepoužijí; (b) `To auto je modré.` beze změny —
tam přivlastnění není; (c) všech pět domén, gate a parita 16/16.

**Očekávaný výsledek:** po odpovědi je v bázi **doložený vztah
vlastnictví** s proveniencí tahu; otázka na vlastníka se **neklade**
tam, kde odpověď není potřeba (viz G‑4); plná regrese.

---

## Archiv — kolo #52 (uzavřeno)

**Status tehdy: 🟡 PARTIAL.** Kolo #52. 720 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **50/50**, živá parita **16/16**. **Rozhodnutí o denotaci
schvaluji a je nejlepší z celé série.** PARTIAL je za jeden změřený
rozpor s podmínkou, kterou jsem pro tohle kolo zadal.

**Architectural Health Score: 9 / 10**

---

## Co je splněno (měřeno mnou)

**Rozhodnutí o denotaci — SCHVALUJI, a je to lepší odpověď než moje
otázka.** Ptal jsem se „(a) nebo (b)"; Builder odpověděl, že to **nejsou
alternativy, ale dvě různé otázky**:

> Co fráze *„Filipovo auto"* **denotuje**, je uzel vybraný kritériem —
> určitý popis. **Čím** ho vybírá, je vztah vlastnictví. Postavit (a)
> místo (b) by znamenalo, že věta tvrdí dvě věci na téže úrovni — jenže
> ona jednu **tvrdí** a druhou **předpokládá**.

To je správné rozlišení tvrzení a presupozice a mělo být v mém zadání.

**Proč se vlastník nezapisuje — a je to poctivá mez:** rozbor jméno
vlastníka **nedává**. Token je `Filipovo` s lemmatem `Filipův`; cesta
k uzlu `Filip` je **derivační morfologie**, kterou tagger neřeší.
Useknout `-ův` by byl dohad o češtině zadrátovaný do interpretu — táž
třída jako seznam významů předložek, kterému se brání INV‑11.

**Změřeno mnou:**

```
» Filipovo auto je modré.        ◐ být(co:·modrý, kdo:auto)
   ztracený člen: ŽÁDNÝ ✓        ← otázka bez odběratele zmizela
   žádná třída Filipův_auto ✓
» dva kandidáti v bázi           zapsáno: None, ptá se a jmenuje oba ✓
» To auto je modré.              beze změny ✓
```

**Regrese celá**, gate *Farmaka* `N`, všech pět domén.

---

## Critical Blockers

### G‑4 · systém se ptá na to, co si sám právě zodpověděl

**Změřeno** — jeden kandidát v bázi:

```
báze: member(elem:a1, group:·auto)

» Filipovo auto je modré.
   ◐ přečteno, neúplné  být(co:·modrý, kdo:auto)
     ? A na koho odkazuje kdo: „auto“? …            ← OTÁZKA
     auto → a1 (určitý popis; jediný kandidát)      ← A HNED POD NÍ ODPOVĚĎ
   ✓ zapsáno [s0002]  být(co:·modrý, kdo:a1)

   statement_id = s0002        ← zapsáno správně
   question     = „A na koho odkazuje…"  ← ale otázka ZŮSTALA
```

**Fakt:** reference se vyřešila (`a1`), věta se zapsala **správně**,
a `TurnResult.question` přesto nese otázku, která už byla zodpovězena.

**Logický závěr:** odběratel čtoucí `result.question` položí člověku
dotaz na roli, která je **už navázaná**. Odpověď by přišla k rozhodnutí,
které padlo — a v horším případě by správnou vazbu přepsala. Podle
vlastního pravidla projektu je otázka bez odběratele horší než ticho;
tohle je o stupeň horší — **otázka, na kterou už systém odpověděl sám**.

**Dotčené smlouvy:** podmínka, kterou jsem pro tohle kolo zadal
(*„buď odpověď někam vede, nebo se otázka přestane klást"*) — tady se
klade, i když nebyla potřeba. A značka `◐ přečteno, neúplné` u věty,
která se **dokončila a zapsala**, tvrdí opak toho, co se stalo.

**Kořenová příčina (hypotéza k ověření Builderem):** otázka se skládá
z `awaiting='odkaz'` **před** zakotvením, a zakotvení ji při úspěšném
doložení **nemaže**. Je to zrcadlo tvého vlastního nálezu z kola #49 —
tam se otázka četla ze **stopy**, tady se počítá **před** krokem, který
ji ruší.

**Nejmenší bezpečná změna:** otázku skládat **až z výsledku zakotvení** —
role, která má `resolved`, žádnou otevřenou otázku nemá. Značka `◐` ať
se řídí týmž stavem.

**Counterexample, který musí projít:** (a) **dva kandidáti** — otázka
musí zůstat, `statement_id` musí být `None`; (b) **žádný kandidát** —
otázka musí zůstat a nezapisovat; (c) kvantifikátorová a relační otázka
beze změny — tam se neřeší odkaz.

**Očekávaný výsledek:** jeden kandidát → `question is None`, značka `✓`,
zapsáno; dva a nula kandidátů beze změny; plná regrese včetně pěti domén
a parity 16/16.

---

## Semantic Warnings

**W‑29 · třetí přesun příkladu v `test_lost_role` — ověřeno, je to dobrá
zpráva.** Postupně: *„Jan nesmí dostat penicilin"* (vyřešil G‑1a),
*„Filipovo auto je modré"* (vyřešilo N‑6), teď *„Jan má alergii na
penicilin"*. Smyčka N‑5 se netestuje slaběji — testuje se na členu,
který **ztracený doopravdy je**. Příklad zastarává, protože se vady
opravují; to je opak oslabení.

**W‑30 · přepis B‑12 — přijímám s výhradou k formulaci.** Požadavek
*„o ztrátě se nemlčí"* platí dál a je splněný silněji. Builderovo
zdůvodnění — *„původní znění bylo zapsané u špatné příčiny"* — je
správné. Výhrada: přepis testu, který kdysi zachytil bloker, je vždy
rizikový krok; **je v pořádku, protože ho doprovází důkaz, že se ta
konkrétní vada nemůže vrátit** (třída `Filipův_auto` má vlastní test).

---

## Archiv — kolo #51 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #51. 709 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **49/49**, živá parita **16/16**. **N‑5b ověřeno mnou** —
*Zmrzlina* se čte, akceptační sada `test_golden_dialogues` **17 passed**,
a všech pět domén má verdikt jako podmínku.

**Architectural Health Score: 9,5 / 10**

---

## Stav akceptace — měřeno mnou z dat i během

```
Jana a zmrzlina    zapisuje 2  verdikty ['A']
Doprava            zapisuje 1  verdikty ['A']
Farmaka            zapisuje 2  verdikty ['N']
Čas a prostor      zapisuje 3  verdikty ['A', 'U']
Petrovice          zapisuje 2  verdikty ['A']
CELKEM: 5 domén, 10 zapsaných tahů, 6 závěrů      test_golden_dialogues: 17 passed
```

**Zmrzlina** — před změnou `0 čtení`, dnes:

```
» Děti mají rády zmrzlinu.   ◐ mít(co:∃zmrzlina, iobj:rád, kdo:∀dítě)
```

Kolize dvou jádrových členů zmizela; `iobj` má **povrchové** jméno,
takže se systém nezastaví ani nehádá.

**Moje counterexamply:**

```
Filip má auto. / Jan má alergii.  → mít(co:…, kdo:…)   žádná povrchová role, neptá se ✓
Lék se podává pacientům.          → Dat:arg, nsubj:pass   beze změny ✓
```

**Regrese celá:** B‑1, B‑2, matice ⪯, `disjoint`→`N`, `CONFLICT`, stráže
4/4, `same_as`, M‑1, G‑3 recall, zákaz eliminace `OR`, I‑16.

---

## Critical Blockers

**Žádné.**

---

## Nález kola: metrika ohlásila pokrok jako propad

Builder našel, že čítač „s verdiktem" počítal i **nepřečtenou** větu,
protože ta se vrací se statusem `UNKNOWN`. Když se *Zmrzlina* konečně
přečetla a **zapsala**, číslo **kleslo ze 7 na 6**.

To je vzácný druh vady: **měřicí přístroj ukazoval opačným směrem, než
se hýbala skutečnost.** Přejmenování na „závěrů domén" a počítání z toho,
co má krok zapsané jako **očekávaný** verdikt, je správná oprava — a jeho
zdůvodnění sedí: *jinak příště nepoznám, jestli doména o odpověď opravdu
přišla, nebo se jen něco přestalo lámat.*

---

## Semantic Warnings

**W‑27 · změna potvrzeného tvaru v dialogu — ověřeno, není oslabení.**
`('ADJ','Plur','','advmod')` → `('ADJ','Plur','','iobj')`. Ověřil jsem
u živé služby: parser dává **`iobj`**. Původní zápis byl *„co by bylo
mluvnicky správně"*, ne *„co rozbor dal"* — a takový vzor nikdy nesedne.
Je to **táž třída jako fixtura bez `Poss=Yes`** z kola #47: záznam chudší
nebo jiný než skutečnost fixuje chování, které nenastane. Mez je u kroku
zapsaná jako `limit`, takže se netváří, že je `rády` jako `iobj`
v pořádku.

**W‑28 · „uzavřeno v zapsaném rozsahu" — beru přesně tak, jak to Builder
napsal.** Akceptační sada je splněná; **není to tvrzení, že je hotový
jazyk**. Deset komplexních odstavců, které zadal člověk, zůstává
otevřeným cílem a tahle sada je jen jeho spodní patro.

---

## Jeden další směr: **přivlastnění**

Builder poprvé nemá na stole nesplněný scénář, který by směr určil, a
nechal rozhodnutí na mně.

**Volím přivlastnění**, ne `Postřižiny`/`Roník`.

**Důvod — rozlišení druhu překážky:** `Postřižiny` a `Roník` jsou
**znalost světa** (rozpoznat vlastní jméno, které není v rejstříku).
Tu morfologie nedodá **nikdy**, takže není co stavět — je to mez, ne
úkol. Přivlastnění je naproti tomu **chybějící vrstva**, kterou systém
dnes poctivě přiznává (`[ZAHOZENO: „Filipovo"]` + otázka), ale **odpověď
nemá kam vést**.

**Dotčená smlouva:** dnešní stav porušuje ducha N‑5. Systém se ptá
*„jakou roli hraje »Filipovo«?"* — a **žádná odpověď tu otázku nezavře**,
protože „čí" není role, ale **vztah ke konkrétnímu uzlu**. Otázka bez
odběratele je podle vlastního pravidla projektu horší než ticho.

**Nejmenší bezpečná změna:** rozhodnout, **čím** přivlastnění je, než se
začne stavět. Kandidáti: (a) reifikovaná relace `vlastní(kdo, co)`;
(b) role na uzlu s odkazem, tedy táž fronta jako `awaiting='odkaz'`.
**Napiš důvod, ne jen volbu** — je to volba denotace se `semantic blast
radius` do identity.

**Counterexample, který musí projít:** (a) `Filipovo auto je modré.`
nesmí vyrobit **třídu** `Filipovo_auto` (kolo #47 to vyloučilo záměrně —
z každého majitele by byla nová třída); (b) `To auto je modré.` beze
změny; (c) všech pět domén a parita 16/16.

**Očekávaný výsledek:** buď odpověď na tu otázku **někam vede**, nebo se
otázka **přestane klást** a přivlastnění se zapíše jako přiznaná mez.
Obojí je poctivé; dnešní stav — ptát se bez odběratele — není.

---

## Archiv — kolo #50 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #50. 704 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **49/49**, živá parita **16/16**. **N‑4 ověřeno mnou** a poprvé
jsem změřil **stav všech pěti** akceptačních dialogů, ne jen toho, který
se právě měnil.

**Architectural Health Score: 9,5 / 10**

---

## Stav akceptace — měřeno z dat, ne z tvrzení

| doména | kroků | zapisuje | verdikty | ptá se |
|---|---|---|---|---|
| Jana a zmrzlina | 3 | 1 | `A` | 0 |
| Doprava | 2 | 1 | `A` | 0 |
| **Farmaka** | 3 | 2 | `N` | 0 |
| **Čas a prostor** | 5 | 3 | `A`, `U` | 0 |
| **Petrovice** | 3 | 2 | `A` | 0 |

**Všech pět má verdikt jako podmínku.** Builder poctivě napsal, že
*Dopravu* naposledy neměřil a nebude tvrdit, že je hotová — změřil jsem
ji: **2 kroky, zápis, verdikt `A`**. Prochází.

*(Zbývající meze jsou zapsané u kroků, ne v próze: `Roník` jako obecné
jméno — znalost světa, ne morfologie.)*

---

## Důkaz N‑4 (měřeno mnou)

```
» Petr byl v pondělí v Praze.   ◐ být(kdo:·Petr, kdy:pondělí, v+Loc:Praha)
                                  ptá se ✓   zapsáno: None ✓
```

Před změnou to bylo `být(co:Praha, …)`, tedy **„Petr byl Prahou"**.

**Moje counterexamply — v žádném z nich nevznikla povrchová role:**

```
Auto je dopravní prostředek.  → být(co:·dopravní_prostředek, …)   povrchové role: žádné ✓
Jana je učitelka.             → member(elem:·Jana, group:·učitelka)             ✓
Vrabec není savec.            → disjoint(a:·vrabec, b:·savec)                   ✓
```

**Regrese celá** včetně G‑3 recallu a zákazu eliminace `OR`; gate
*Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑26 · zrušení pole `limit` u D3 — ověřeno, je to správně.** Mez padla,
takže ji Builder nenechal v datech, ale přepsal do `point` jako **záznam,
co se opravilo**. *„Nechávat tam mez, která padla, by byla nepravda
s razítkem testu"* — souhlas, a je to symetrické k tomu, co jsem
vyžadoval opačně v kole #39: mez se nesmí vyrábět z implementace **ani
udržovat po opravě**.

---

## Jeden další směr: **Zmrzlina — `rády` jako `iobj`**

Zbývá jediná doména bez plného průchodu a je to jediná položka, která
**blokuje akceptační scénář**.

**Fakt (změřeno v kole #43):** `Děti mají rády zmrzlinu.` →
`NEVÍM, jak to čtu`, `0 čtení`, s vysvětlením *„dva jádrové členy dostaly
touž roli (`co`)"*. Parser dává `rády` jako `iobj`, generátor mapuje
`obj` i `iobj` na `co`.

**Kořenová příčina:** dvě různá `deprel` se mapují na **jedno** jméno
role. Rozbor je rozlišuje — kaskáda to rozlišení zahodí.

**Dotčená smlouva:** táž třída jako B‑9 (kolize dvou příslovečných
určení), jen o patro blíž jádru.

**Nejmenší bezpečná změna:** `iobj` **nemapovat na `co`**. Buď mu dát
vlastní povrchové jméno (jako `Dat` u *podávat pacientům*), nebo — a to
je konzistentnější s N‑3 — nechat kolizi **projít doptáním**: *„která
z těch dvou je `co`?"*. Duplicita rolí je legitimní důvod k dotazu, ne
k mlčení.

**Counterexample, který musí projít:** (a) `Filip má auto.` a
`Jan má alergii.` — obyčejný `obj` — musí dál číst `co` **bez otázky**;
(b) `Lék se podává pacientům.` má dnes `Dat:arg` a musí zůstat; (c) gate
*Farmaka*, *Petrovice*, *Čas a prostor* a parita 16/16 beze změny.

**Očekávaný výsledek:** `Děti mají rády zmrzlinu.` se **přečte** (ať už
s vlastní rolí, nebo po doptání); doména *Zmrzlina* projde celá; plná
regrese.

**Poznámka k rozsahu:** věcně je `rády` v téhle vazbě příslovce, ne
předmět — parser se plete. Ale i tak se systém **nemá zastavit**; má se
zeptat. To je přesně kritérium, které platí od zadání člověka.

---

## Archiv — kolo #49 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #49. 697 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **48/48**, živá parita **16/16**. **N‑3 ověřeno mnou** — dialog
*Petrovice* prochází celý a oba mé counterexamply drží.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

**Gate *Petrovice* — a verdikt je PODMÍNKA, ne próza:**

```
» Roník bydlí v Petrovicích.   ✓ bydlet(kde:Petrovice, kdo:∀roník)   [s0001]
     Petrovicích → Petrovice (sort z role; místo)
» Micka bydlí v Petrovicích.   ✓ zapsáno [s0005]
» Bydlí Micka v Petrovicích?   answers='A'   ← podmínka v datech, ověřeno
   roles: (('v+Loc', 'kde'),)                ← rozhodnutí domény, ne vlastnost češtiny
```

Bez potvrzené role se věta **ptá** a nezapisuje — ověřeno zvlášť.

**Moje counterexamply:**

```
» Petr jel v pondělí do Prahy.   jet(kam:Praha, kdo:·Petr, kdy:pondělí)   neptá se ✓
» Petr byl v pondělí v Praze.    obě určení přečtena, kdy:pondělí         ✓
```

`v`+Acc → `kdy` se **neuvolnilo**.

**Regrese celá** včetně G‑3 recallu a zákazu eliminace `OR`; gate
*Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Nález kola: dvě hypotézy nedělaly volbu, dělaly neřešitelnost

Builderova diagnóza je ostřejší než moje zadání a stojí za zapsání:

> Dvě hypotézy v seedu (`v+Loc→kde`, `v+Loc→kdy`) situaci **neřešily, ony
> ji dělaly NEŘEŠITELNOU**. I kdyby člověk odpověděl, kandidáti by byli
> pořád dva a tvar by zůstal dvojznačný navždy.

Odstranění ze seedu tedy **nebylo zjednodušení**, ale **podmínka toho, aby
odpověď vůbec mohla něco rozhodnout**. Zadal jsem to jako „nedávat do
seedu, ať se zeptá"; on našel důvod, proč to jinak nejde.

**A druhý mezikrok, který si přiznal:** otázka se nejdřív četla **ze
stopy**, takže se ptal na roli `Gen`, kterou jádrová relace mezitím
spotřebovala jako stranu `subset`. **Stopa je log** — nese i to, co
pozdější patro vyřešilo. Otázka se musí počítat z **hotové predikace**.
Zachytila to zlatá sada, ne úsudek.

---

## Semantic Warnings

**W‑25 · nové pole `Step.limit` — schvaluji a je to oprava asymetrie.**
`Golden` pole `limit` měl, `Step` ne, takže **v dialozích se meze nedaly
zapsat**. `Roník` jako obecné jméno je přiznaná mez (znalost světa, ne
morfologie) a doména na ní nestojí — mluví se o témže uzlu v obou větách.
Zapsat ji je správné; kdyby chyběla, tvářilo by se v pořádku všechno.

---

## Stav akceptačních dialogů

| doména | stav |
|---|---|
| **Farmaka** | 🟢 prochází, `N` z doloženého popření |
| **Petrovice** | 🟢 prochází, `A` doloženo |
| Jana a zmrzlina | 🟡 `member` hotový; `rády` jako `iobj` blokuje druhou větu |
| Doprava | 🟡 A1 se ptá a dočte; zbytek neověřen |
| Čas a prostor | 🟡 `co:Praha` × `kde:Praha` ve sponových lokativech |

---

## Jeden další směr: `co:Praha` × `kde:Praha` ve sponových lokativech

**Fakt změřený mnou:** `Petr byl v pondělí v Praze.` →
`být(co:Praha, kdo:·Petr, kdy:pondělí)`. `Praha` dostane roli **`co`**,
tedy jmennou část přísudku — ne `kde`.

**Kořenová příčina:** UD dělá `Praze` kořenem a `byl` sponou, takže
sponové pravidlo vezme jmennou část jako `co`. U *„Auto je prostředek"*
je to správně, u předložkového určení místa ne.

**Proč právě tohle:** je to poslední položka, která **blokuje akceptační
dialog** (*Čas a prostor*). Zbylé otevřené věci — přivlastnění, `rády`
jako `iobj`, `Postřižiny`, `Roník` — jsou buď **jiná vrstva**, nebo
**meze parseru a znalosti světa**, tedy ne nesplněné scénáře.

**Nejmenší bezpečná změna:** když má sponový kořen u sebe **předložku**
(`case`), není to jmenná část — je to okolnost a má dostat povrchovou
roli, tedy `v+Loc`, a projít **týmž doptáním** jako Petrovice. Žádné
nové pravidlo o významu; jen se nepřevezme jmenná část tam, kde ji
předložka vylučuje.

**Counterexample, který musí projít:** (a) `Auto je dopravní prostředek.`
a `Jana je učitelka.` **beze změny** — tam předložka není a jmenná část
je správně; (b) `Vrabec není savec.` → `disjoint` beze změny; (c) gate
*Farmaka* i *Petrovice* a parita 16/16.

**Očekávaný výsledek:** `Petr byl v pondělí v Praze.` → `v+Loc:Praha`
s doptáním, po odpovědi `kde:Praha`; dialog *Čas a prostor* projde celý;
plná regrese.

---

## Archiv — kolo #48 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #48. 685 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **47/47**, živá parita **16/16**. **N‑2d ověřeno mnou** — oba mé
counterexamply prošly a Builder si sám našel vadu, kterou jsem nezadal
a která by byla vážná.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

**Counterexample (a) — odpověď se neztratila:**

```
» Jana je učitelka.     ✓ member(elem:·Jana, group:·učitelka)   [s0001]
» Je Jana učitelka?     → A   doloženo: ['s0001']
```

**Counterexample (b) — slovní druh podmětu rozhoduje:**

```
» Mourek je kočka.      ✓ member(elem:·Mourek, group:·kočka)
» Kočka je savec.       ◐ ptá se                    ← PROPN tam není
```

**Zápor, který si našel sám a který jsem nezadal:**

```
» Mourek není savec.    ✓ ¬member(elem:·Mourek, group:·savec)
» Je Mourek savec?      → N   doloženo: ['s0001']    ← z DOLOŽENÉHO popření
» Vrabec není savec.    ✓ disjoint(a:·vrabec, b:·savec)   ← disjoint zápor dál polyká
```

**Regrese celá** včetně G‑3 recallu a zákazu eliminace `OR`; gate
*Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Nález kola: zápor je na `member` kolmý

`_as_relation` **zahazoval zápor vždycky**, protože první relace, která
tudy prošla, byl `disjoint` — a ten zápor sám nese. Na `member` a `subset`
to neplatí.

Kdyby to zůstalo, `Mourek není savec.` by se zapsalo jako
`member(Mourek, savec)` — **přesný opak toho, co člověk řekl**. Builderovo
zařazení je přesné: je to táž třída jako kdysi `Predication.negated`,
které zahodilo přestavování dataclassy.

**Nezadal jsem to a on to našel** — a to je ten rozdíl mezi „splnil
zadání" a „rozumí, co dělá". Zvlášť cenné je, že to **pinnul z obou
stran**: `member` zápor nese, `disjoint` ho dál polyká.

---

## Semantic Warnings

**W‑24 · změna akceptačního dialogu — ověřeno, není oslabení.** *Jana
a zmrzlina* má nově `member(elem:·Jana, group:·učitelka)` místo
`být(...)`. Do téhle změny leželo v bázi **slabší tvrzení, než co člověk
řekl**, a odpověď `A` držela jen proto, že se ptalo na tentýž reifikovaný
vztah. Teď drží **přes jádrový uzávěr**. Krok `Je Jana učitelka?` → `A`
zůstal **podmínkou**, ne prózou — ověřeno.

---

## Jeden další směr: **Petrovice — `v`+Loc**

Builder nechal rozhodnutí na mně a nabídl přivlastnění a tři evidované
meze zlaté sady.

**Volím Petrovice.** Důvod je gate:

- **Petrovice je celý akceptační dialog**, který dnes **neprojde** —
  a jako jediná z otevřených položek je to **nesplněný akceptační
  scénář**, ne chybějící schopnost nad rámec.
- **Přivlastnění** Builder popsal správně podruhé: *odpověď nemá kam
  vést*. Je to jiná vrstva, ne dokončení téhle.
- **Zmrzlina** (`rády` jako `iobj`) a **Postřižiny** (název díla) jsou
  meze **parseru**, ne kaskády — a Postřižiny jsou znalost světa, kterou
  morfologie nedodá.

**Problém:** `v`+Loc znamená jednou `kde` (*v Praze*) a jednou `kdy`
(*v pondělí* — dnes `v`+Acc, takže to už rozliší). U *„v Petrovicích"* je
to místo, ale rozhodnout se to musí, protože tvar sám nestačí.

**Nejmenší bezpečná změna:** `v`+Loc **nedávat do seedu** — je to táž
dvojznačnost jako holá spona. Nechat, ať se **zeptá**, a odpověď naučit
jako tvar. Doptání je podle zadaného kritéria správné chování.

**Counterexample, který musí projít:** `v`+Acc → `kdy` **se nesmí
uvolnit** (kolo #38 to opravovalo) a `Petr jel v pondělí do Prahy.` musí
dál číst `kdy:pondělí` **bez otázky**. Druhý: `Petr byl v pondělí
v Praze.` — dvě určení, různé tvary — musí dál číst obě.

**Očekávaný výsledek:** dialog *Petrovice* projde celý (věta se zeptá,
odpověď ji dočte, otázka na obou psech dá doloženou odpověď); `v`+Acc beze
změny; plná regrese včetně gate a parity.

---

## Archiv — kolo #47 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #47. 679 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **47/47**, živá parita **14/14**. **N‑2c ověřeno mnou** — všechny
tři mé counterexamply prošly a nález o fixtuře je nejcennější kus kola.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

**Identita napříč pozicemi:**

```
» Petr jel po dlouhé dálnici.   jet(kdo:·Petr, kudy:dlouhý_dálnice)
» Dlouhá dálnice vede.          vést(kdo:∀dlouhý_dálnice)
```

Týž uzel, jiná pozice. **Lemmata, ne tvary** — a právě proto to napříč
pozicemi funguje.

**Moje counterexamply, všechny tři:**

| co | výsledek |
|---|---|
| `To auto je modré.` | `být(co:·modrý, kdo:auto)` — nesloženo ✓ |
| `Filipovo auto je modré.` | `Filipovo` **zůstalo ztraceným členem s otázkou** ✓ |
| gate *Farmaka* + parita | `N` / 14 ✓ |

**Vyloučení přivlastnění je ze STAVBY, ne z odhadu** — `Poss=Yes`.
Ověřil jsem u živé služby, že ten příznak opravdu dává.

**Jeho vlastní vyloučení, které jsem nežádal:** `Starý Petr spí.` →
`spát(kdo:·Petr)`, `PROPN` se neskládá. Důvod je správný: přívlastek na
vlastním jméně by měnil identitu **pojmenovaného** uzlu a kanonizace jmen
(M‑2) by pak trefovala jiný uzel podle toho, jestli u jména zrovna stálo
adjektivum.

**Regrese celá** včetně G‑3 recallu a zákazu eliminace `OR`.

---

## Critical Blockers

**Žádné.**

---

## Nález kola: fixtura chudší než skutečnost

Builder našel, že `test_quantifier.py` měl u `Filipovo` ručně psanou
nahrávku **bez `Poss=Yes`**, ačkoli živá služba ten příznak dává. Ověřil
jsem to voláním služby — dává.

**Proč je to nejdůležitější věc kola:** do téhle změny na tom nezáleželo,
takže se rozdíl **nikdy neprojevil**. Přesně proto je nebezpečný —
nahrávka chudší než skutečnost **fixuje chování, které na živém vstupu
nenastane**. A opravil **fixturu podle živého rozboru, ne podmínku**;
obráceně by sada dál hlídala svět, který neexistuje.

Je to táž třída jako lekce z A‑20 (*ručně psané nahrávky kódují představu
autora*), jen o patro níž: tam šlo o rozbor, tady o **jediný chybějící
příznak**, který se schoval, protože ho nikdo nepotřeboval.

---

## Semantic Warnings

**W‑23 · změna zlaté sady u A1 — ověřeno, není oslabení.** `A1` má nově
`být(co:·dopravní_prostředek, kdo:∀auto)` místo tří rolí s `jak:·dopravní`.
Role `jak` u přívlastku byla **povrchové pojmenování něčeho, co členem
vztahu není**; věta mluví o **jedné** třídě. `asks` z minulého kola
zůstalo, takže se kritérium nezměkčilo.

---

## Jeden další směr: vlastní jméno v podmětu → `member`

Builder nechal rozhodnutí na mně a nabídl dvě otevřené věci.

**Volím `member`**, ne přivlastnění. Důvod:

- **`member`** je poslední evidovaná mez z N‑2 a je to **dokončení
  rozdělané práce** — patro jádrových relací dnes vlastní jméno v podmětu
  vůbec nerozpoznává, takže `Jana je učitelka.` zapisuje `být(...)` tam,
  kde věcně patří `member(Jana, učitelka)`. Bez toho zůstává v bázi
  **slabší tvrzení**, než co člověk řekl.
- **Přivlastnění** Builder sám popsal správně: *odpověď nemá kam vést*,
  protože „čí" je vztah ke konkrétnímu uzlu, tedy **jiná vrstva**. Otevřít
  ji teď by znamenalo začít vrstvu, ne dokončit tuhle.

**Nejmenší bezpečná změna:** rodina `cop:PROPN=NOUN` → návrh `member`.
`PROPN` v podmětu **je** signál individua — na rozdíl od `NOUN=NOUN`, kde
je to nerozhodnutelné.

**Counterexample, který musí projít:** (a) `Jana je učitelka.` dnes
**odpovídá `A`** na `Je Jana učitelka?` — po změně musí odpovídat dál,
ať už jako `member`, nebo po doptání; **ztráta té odpovědi je regrese**;
(b) `Mourek je kočka.` (PROPN podmět, obecné jméno) musí dát **`member`**,
ne `subset` — a `Kočka je savec.` se musí dál **ptát**, protože tam
`PROPN` není.

**Očekávaný výsledek:** `Jana je učitelka.` → `member(Jana, učitelka)`;
`Je Jana učitelka?` → `A`; dvojznačná holá spona se dál ptá; plná regrese
včetně gate a parity.

---

## Archiv — kolo #46 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #46. 671 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **47/47**, živá parita **14/14**. **G‑3 opraveno a ověřeno mnou**,
oba mé counterexamply prošly.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

```
ask(subset(auto, A AND B)) na zapsaný fakt   → A   listy=['s0001']
   cituje TEN výrok, který člověk řekl        ✓
```

**Counterexample (a) — zákony se neobešly:**

```
subset(A AND B, A) BEZ přímého faktu → A, důkaz ze ZÁKONA (ne z faktu)
```

**Counterexample (b) — negativní kontroly drží:**

```
subset(A OR B, A)   → U      (zákaz eliminace OR platí)
subset(A, A AND B)  → U
```

**A jeho test navíc, který jsem nežádal a je podstatný:** kde platí přímý
fakt **i** zákon, vrátí se **přímý** (`listy=['s0001']`) — § 7 minimalita.
Bez něj by šlo pořadí obrátit a vada by se vrátila jako „jen" delší
vysvětlení, což se neohlásí.

**Regrese celá:** stálá sada zelená, gate *Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové.**

---

## Jeden další směr: složení nominálu v `generate` — POTVRZUJI

Builder na potvrzení čeká a dostává ho. Teď je to správné pořadí, protože
pod tím **není otevřená vada**.

**Problém (evidovaná mez W‑22):** složení dělá dnes **jen jmenný
přísudek**. Táž fráze jinde (*„po dlouhé dálnici"*) se složí jinak, takže
**míří na jiný uzel** — a to je tichá nekonzistence identity: `dopravní
prostředek` z jedné věty a `prostředek` s přívlastkem z druhé nejsou týž
uzel, ačkoli člověk mluví o téže věci.

**Dotčená smlouva:** identita uzlů. Tohle je **`semantic blast radius`
do celé báze**, ne jen do jednoho patra — proto to má vlastní kolo.

**Nejmenší bezpečná změna:** složení v `generate`, tedy **jednou pro
všechny pozice**, ne kopie pravidla v každém patře.

**Counterexample, který musí projít:** (a) `To auto je modré.` **nesmí**
složit — přísudkové adjektivum není přívlastek a rodina `NOUN` na obou
stranách se nesmí uvolnit; (b) **gate *Farmaka* i parita 14/14 beze
změny** — složení se dotkne každé věty s přívlastkem, takže regrese je tu
důkaz, ne formalita; (c) `Filipovo auto je modré.` má dnes přivlastnění
jako **ztracený člen s otázkou** (N‑5) — složení z něj **nesmí** udělat
`Filipovo_auto` a otázku tím tiše umlčet, protože přivlastnění je vztah
ke **konkrétnímu uzlu**, ne druhový přívlastek.

**Očekávaný výsledek:** táž fráze míří na **týž uzel** bez ohledu na
pozici; `To auto je modré.` a `Filipovo auto je modré.` beze změny; plná
regrese včetně gate a parity.

---

## Potvrzení

**Přijetí mého pořadí i s důvodem** — *„navrhl jsem opačné pořadí podle
toho, co mě víc zajímalo, ne podle mandátu"* — je přesně ta sebereflexe,
kterou tenhle projekt drží nad vodou.

**Formulace, kterou si necháváš, je správná a patří do dokumentace:**
neúplná sada zákonů je **přiznaná mez**; ignorovat vlastní bázi mez
**není**. Systém, který odpoví „nevím" na tvrzení, které mu člověk právě
řekl, neselhal v odvozování, ale **v paměti**.

**Doklad, že sis politiku nevymyslel** (`_member_term` se indexu ptal
odjakživa a má to i v komentáři), je ten správný druh argumentu:
nesouměrnost byla vada, ne návrh — a opravou se obě cesty srovnaly.

**Verzování jádra tentokrát ANO, a rozlišení sedí:** A‑21 a N‑2 byly
smlouvy vrstvy V2, tohle je vlastnost **evaluátoru**, kterou
`CORE-SEMANTICS` pokrývá.

---

## Archiv — kolo #45 (uzavřeno)

**Status tehdy: 🟡 PARTIAL.** Kolo #45. 665 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **47/47**, živá parita **14/14**. **N‑2b je hotové a oba mé
counterexamply prošly.** PARTIAL je za nález, který Builder poctivě
ohlásil mimo rozsah a **který jsem reprodukoval**.

**Architectural Health Score: 9 / 10**

---

## Co je splněno (měřeno mnou)

**Rozhodnutí o denotaci — SCHVALUJI, a čtvrtý důvod je nejlepší.**
Zvolen **složený pojem**, ne průnik. Argument, který rozhoduje:

> Průnik **tvrdí intersektivitu**. U *„bývalý prezident"* je to nepravda
> a morfologie ty případy nerozliší — zvolit průnik tedy znamená hádat
> o významu přídavného jména.

A ten změřený: zákon `X ⊆ A AND B ⇒ X ⊆ B` v § 5.2.1 **není** (je tam
opačný, introdukční směr), takže by se platil sémantický závazek za
užitek, který neexistuje. **Nezískaný závěr je lepší než vymyšlený.**

**Moje counterexamply:**

```
» To auto je modré.               ◐  zapsáno: None      (nenavrhuje vztah tříd ✓)
» Amoxicilin je druh penicilinu.  ✓  subset(…)  s0001   (beze změny ✓)
```

**Přívlastek se nehlásí jako ztracený člen** — `verdict.lost` prázdné.
Že je to řešeno **nesením** (`RoleReading.absorbed`), a ne dopočtem ze
stromu, je správné: rozhodnutí složit padlo jinde a dopočet by ho hádal
zpětně.

**Smyčka funguje celá** (živý běh):

```
» Kočka je savec.        ? … členství, podmnožina, nebo oddělenost?
» →⊆ Je to podmnožina.   ✓ naučeno konstrukce cop:NOUN=NOUN ~ subset [hypothesis, tah 4]
                         ✓ subset(sub:·kočka, sup:·savec)
```

**Změna zlaté sady u A1 NENÍ oslabení** — a ověřil jsem proč: dřív se
věta zapsala jako reifikované `být` se třemi rolemi, což se sice neptalo,
ale **nikdy nedalo `subset`**, na kterém doména stojí. Dnes se ptá a
jedním tahem dočte. To je `vím, že nevím` místo tichého zápisu slabšího
tvrzení — přesně to, co zadal člověk.

**Regrese celá:** stálá sada zelená, gate *Farmaka* `N`.

---

## Critical Blockers

### G‑3 · engine nevrátí fakt, který má přímo v bázi

Builder to ohlásil mimo rozsah. **Reprodukoval jsem:**

```
attach(subset(auto, A AND B))      → s0001
ask   (subset(auto, A AND B))      → U        ← fakt je PŘÍMO V BÁZI
index.subset_proof(auto, A AND B)  → důkaz existuje

srovnání: subset(auto, DP) bez algebry → A
```

**Fakt:** `_subset_term` při algebraickém `sup` **přeskočí přímý dotaz do
indexu** a jde rovnou na zákony § 5.2.1.

**Logický závěr:** systém odpoví „nevím" na tvrzení, které mu člověk
**řekl a které má uložené**. To není neúplnost odvození — to je selhání
**recallu**. Doložka „presenter smí říkat jen to, co je podloženo
skutečně použitým důkazem" má i obrácenou stranu: **důkaz, který v bázi
leží, se nemá ignorovat**.

**Proč to není gate‑blocker, a přesto je to bloker:** N‑2b průnik
nezapisuje, takže žádný akceptační scénář tudy dnes nechodí — Builder to
sám uvádí jako jeden z důvodů volby. Ale je to **nejvyšší otevřené riziko
pro správnost** a leží v jádře, ne ve vrstvě V2.

---

## Jeden další směr: G‑3, ne složení nominálu

Builder navrhl pořadí opačné. **Rozhoduji jinak**, a důvod je mandát:
skládání nominálu je **rozšíření schopnosti**, G‑3 je **vada správnosti
v jádře**. Nová vrstva se nestaví nad otevřenou vadou o patro níž.

**Nejmenší bezpečná změna:** `_subset_term` ať se **nejdřív zeptá indexu**
(tutéž cestou jako u neagebraického `sup`) a teprve když nic nenajde,
jde na zákony § 5.2.1.

**Counterexample, který musí projít:** zákony § 5.2.1 se **nesmí obejít**
— `subset(X, A AND B)` odvozený **ze zákonů** (bez přímého faktu) musí
dál platit a dát **týž důkaz**; přidání přímého dotazu smí jen doplnit
cestu, ne nahradit. Druhý: `subset(A OR B, X)` a `DIFF` větve beze změny —
zákaz eliminace `OR` z prvních kol nesmí povolit.

**Očekávaný výsledek:** `ask(subset(auto, A AND B))` na zapsaný fakt → `A`
s citací toho výroku; algebraické zákony beze změny; plná regrese včetně
gate *Farmaka* a parity 14/14.

---

## Semantic Warnings

**W‑22 · evidovaná mez, kterou beru a která je správně ohraničená.**
Složení dělá **jen jmenný přísudek**; táž fráze jinde (*„po dlouhé
dálnici"*) se složí jinak. Builder to neudělal v témž kole schválně —
měnily by se dvě věci najednou. **Souhlas.** Je to samostatný krok
a dotkne se každé věty s přívlastkem.

---

## Potvrzení

**Elegance, kterou jsi nečekal, je ve skutečnosti důkaz, že rozhodnutí
bylo správné:** po složení zbydou dvě strany, takže věta spadne do
**téže** rodiny jako holá spona a **jedna odpověď zavře obojí**. Kdyby to
byly dva tvary, člověk by na tutéž otázku odpovídal dvakrát. Návrh, který
zjednoduší i to, o co nešlo, bývá ten správný.

---

## Archiv — kolo #44 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #44. 657 testů zelených, `mypy --strict` čistý na 56 souborech,
doložky **47/47**, živá parita **14/14**. **N‑2 ověřeno mnou** — oba mé
counterexamply prošly a rozšíření rozsahu bylo nutné.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

```
» Amoxicilin je druh penicilinu.   ✓ subset(sub:·amoxicilin, sup:·penicilin)   [s0001]
» Je amoxicilin druh penicilinu?   → A
```

**Counterexample (a) — `disjoint` správnými dveřmi, a doloženo ÚČINKEM:**

```
» Vrabec není savec.    ✓ disjoint(a:·vrabec, b:·savec)
   v bázi: p0001, p0002, s0001        ← expanze, ne holý marker
   member(čimčara, savec) → N          ← zábrana B-10 nebyla obejita, byla POUŽITA
```

**Counterexample (b) — `Jana je učitelka.` beze změny:**

```
» Jana je učitelka.   ✓ být(co:·učitelka, kdo:·Jana)   [s0001]   question: None
» Je Jana učitelka?   → A
```

**Regrese celá:** stálá sada zelená, gate *Farmaka* `N`.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑20 · druhé rozšíření rozsahu — SCHVALUJI a bylo nutné.** Builder
zjistil, že dvojznačná věta se **ptala a přitom zapisovala** jako obyčejné
`být`. Kdyby člověk vzápětí odpověděl `subset`, ležely by v bázi **dva**
výroky a ten první by nikdo neodvolal. Ověřeno po opravě:

```
» Kočka je savec.   ◐ zapsáno: None   ptá se: ANO
   ? … členství (member), podmnožina (subset), nebo oddělenost?
```

Je to **táž vada jako u ztraceného členu v N‑5**, jen o jinou chybějící
věc — a tatáž zábrana v `_settle` ji řeší. Rozšíření rozsahu je tu
podmínkou správnosti, ne přidanou funkcí; nevyčleňovat.

**W‑21 · evidované meze, které nejsou vydávány za hotové.** `Jana je
učitelka.` je významově `member`, `Auto je dopravní prostředek.` je
významově `subset` (tři role kvůli přívlastku). Builder u obou **netvrdí
opak** a má na ně testy. To je správné zacházení s mezí — zapsaná mez
není nesplněný požadavek, dokud ji akceptační kritérium nežádá.

---

## Jeden další směr — rozhodnuto: **jmenná část s přívlastkem**

Builder nabídl dvě možnosti a rozhodnutí nechal na mně. Volím **přívlastek
(A1)**, ne vlastní jméno → `member`. Důvod je gate, ne významová
lahůdka:

**Fakt ze zdroje:** `Auto je dopravní prostředek.` je **A1 ve zlaté sadě**
a **první věta akceptačního dialogu A** (*Jana a zmrzlina* / *Doprava*).
Dnes se nerozpozná a mlčí, takže **dialog A nemůže projít celý**.

**Naproti tomu** `Jana je učitelka.` **dnes odpovídá správně** (`A`) a
žádné akceptační kritérium po ní `member` nežádá. Významově je `member`
lepší, ale je to **zlepšení, ne blocker** — a podle mandátu se nevybírá
podle zajímavosti.

**Rozhodnutí, které to obnáší a které Builder správně předvídal:**
`dopravní prostředek` je restrikce, nebo `GroupAnd`? **Musí padnout
vědomě**, ne jako vedlejší efekt implementace — je to volba denotace,
tedy `semantic blast radius` do algebry i uzávěru.

**Counterexample, který musí projít:** `To auto je modré.` **nesmí** začít
navrhovat vztah tříd. Vlastnost není vztah tříd a Builder na to už jednou
narazil (rodina teď vyžaduje `NOUN` na obou stranách) — rozšíření na
přívlastek tu podmínku nesmí uvolnit. Druhý: `Amoxicilin je druh
penicilinu.` musí dál dávat `subset` beze změny.

**Očekávaný výsledek:** `Auto je dopravní prostředek.` → návrh jádrové
relace se **zdůvodněnou** denotací přívlastku; dialog A projde celý;
`To auto je modré.` beze změny; plná regrese včetně gate *Farmaka*
a parity 14/14.

---

## Potvrzení

**„Tvar, ne operace" je správné rozhodnutí a tvůj důvod sedí:** kdyby
o významu konstrukce rozhodovala funkce, byl by v interpretu schovaný
seznam významů českých vazeb — táž vada, kvůli které se okolnosti
pojmenovávají povrchově.

**Že jsi na `AttachError` nepřebil zábranu, ale použil dveře, na které
ukazuje**, je přesně to chování, kvůli kterému B‑10 vzniklo. A žes to
doložil **účinkem** (`member` → `N`), ne jen zápisem markeru, je ten
správný druh důkazu.

**Že v seedu holá kladná spona SCHVÁLNĚ NENÍ** — a hlídá to test s dvojicí
*Kočka je savec* × *Mourek je kočka* — je nejlepší rozhodnutí kola.
Seed, který by to rozhodl, by systém udělal **zdánlivě schopnějším** a
fakticky hádajícím.

---

## Archiv — kolo #43 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #43. 631 testů zelených, `mypy --strict` čistý na 55 souborech,
doložky **46/46**. **A‑21 ověřeno mnou** — odporující čtení už nemizí,
můj counterexample se nezměnil, a tvrdé odmítání zůstalo u typové chyby.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou)

**Můj counterexample — beze změny, jak jsem požadoval:**

```
báze: ¬mít(kdo:Filip, co:∃auto)
» Filip má auto.        ✓ zapsáno [s0002]      question: None
» Má Filip auto?        → CONFLICT             doloženo: s0001, s0002
```

Věta, jejíž **všechna** čtení odporují bázi, se pořád přečte, **zapíše**,
neptá se — a otázka dá `CONFLICT` s **oběma** důkazy. Klesnout na konec
není proti komu.

**Nové chování tam, kde má být:**

```
» Vidí Petr Pavla?   (obě jména Nom, morfologie nerozhodne)
  [POZOR: rozpor s bází — … čtení se NEODSTRAŇUJE, jen klesá — zapsaný
   fakt může být chybný a tiše umlčet správné čtení] → zbývá 2
  ? Čtu to jako: vidět(co:·Petr, kdo:·Pavel) / vidět(co:·Pavel, kdo:·Petr)
    — které z toho?
```

Odporující čtení **zůstalo v sadě** a systém nabízí obě. Přesně to zadání.

**Síla důvodu je TYP, ne formulace** — ověřeno voláním:
`SORT.hard = True`, `CONTRADICTED.hard = False`. Typová chyba tvrdě
odstraňuje dál, takže A‑21 nešlo příliš daleko.

**Regrese celá:** stálá sada zelená, gate Farmaka `N`.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑19 · rozšíření rozsahu, které SCHVALUJI a nevyčleňuji.** Builder
opravil `session.py`: u nerozhodnutého čtení se otázka vypisovala do
`lines`, ale `TurnResult.question` zůstávalo `None`. Ohlásil to zvlášť
a nabídl vyčlenění.

**Nevyčleňovat.** Bez té opravy by A‑21 platilo jen v próze vypsaných
řádků, ne v datech — odběratel čtoucí `result.question` by u věty, kde se
systém ptá nejvíc, četl „systém se neptá". Je to **podmínka měřitelnosti
téže změny**, ne cizí práce. A vejde se do pravidla „nejmenší bezpečná
změna", protože leží v téže rozhodovací cestě.

---

## Jeden další směr: N‑2 — jádrové relace ze stavby věty

**Aktuální gate:** *Farmaka* prochází. Ostatní domény **neprocházejí
česky**, a všechny na téže věci.

**Problém (fakt změřený v kole #38):**

```
» Amoxicilin je druh penicilinu.  →  být(Gen:penicilin, co:·druh, kdo:∀amoxicilin)
                                     a NIKDY ne subset(amoxicilin, penicilin)
```

**Kořenová příčina:** chybí patro, které z konstrukce navrhne **jádrovou
relaci**. `Operation.SUBSET`, `MEMBER` i `DISJOINT` v menu **jsou**;
nikdo je neplní ze stavby věty.

**Dotčená smlouva:** žádná se neporušuje — je to **chybějící schopnost**,
ne vada. Právě proto to je až teď: nejdřív se opravovalo, co bylo rozbité.

**Nejmenší bezpečná změna:** patro **za** mapováním rolí, návrh →
potvrzení, nikdy tiše, přesně jako kvantifikátory. Jednoznačné spouštěče
smí být v seedu (`X je druh Y` → `subset`), dvojznačná holá spona
(`NOUN je NOUN` → `member` × `subset`) **se ptá**.

**Riziko směru:** patro navrhuje **jádrové** atomy, takže chyba tu váží
víc než u obyčejného predikátu — špatně navržený `subset` změní uzávěr
celé báze.

**Counterexample, který musí projít:** `disjoint` se **nezapisuje přes
`attach`** (B‑10). Patro musí navrhnout tah, který jde dveřmi
`add_disjoint`; jinak dostane `AttachError`, a ta zábrana je tam správně.
Druhý: `Jana je učitelka.` dnes prochází jako `být(co:·učitelka,
kdo:·Jana)` a zapisuje se — po změně se **nesmí tiše** stát `member`, ta
věta musí buď zůstat, jak je, nebo se zeptat.

**Očekávaný výsledek:** `Amoxicilin je druh penicilinu.` → návrh
`subset(amoxicilin, penicilin)`, po potvrzení zapsáno jako jádrová
relace; `Vrabec není savec.` → návrh `disjoint` **správnými dveřmi**;
holá spona se ptá; plná regrese včetně gate Farmaka.

---

## Potvrzení

**„Tohle čtení neodpovídá tomu, co mám zapsané, NENÍ totéž co tohle čtení
je špatně"** — to je věta, na které A‑21 stojí, a je formulovaná přesně.

**Typ místo řetězce je správné rozhodnutí a tvůj důvod je lepší než
pohodlí:** kdyby si patro četlo sílu důvodu z české hlášky, byla by to
heuristika tam, kde patří typ, a příští přepis hlášky by ji tiše otočil.

**Kontrolní test `test_without_the_denial_the_sentence_is_equally_undecided`
je ta správná paranoia** — bez něj by sada mohla hlásit úspěch tam, kde se
jen trefila do dvojznačnosti.

**Rozhodnutí neverzovat jádro schvaluji.** `CORE-SEMANTICS` v hlavičce
říká, že neřeší parsing; A‑21 je smlouva vrstvy V2. Nepřidat odstavec do
jádra, aby změna vypadala větší, je správný druh zdrženlivosti.

---

## Archiv — kolo #42 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #42. 616 testů zelených, `mypy --strict` čistý na 54 souborech,
doložky **45/45**, jádro 0.1.9. **G‑2 opraveno a ověřeno mnou** — chyba
se přesunula na správnou fázi a můj protipříklad prošel v obou pořadích.

**Architectural Health Score: 9,5 / 10**

---

## Důkaz (měřeno mnou, ne převzato)

**Případ, který jsem blokoval — teď padá u ZÁPISU:**

```
attach_rule(head=h(a:X), body=(subset(a AND X, b),))
  → UnsafeRule: „pro literály ['subset(sub:·(a AND X), sup:·b)'] neexistuje
     bezpečné pořadí — jádrový predikát potřebuje vázané role"
```

Rozlišil jsem **fázi**, ne jen typ výjimky: hláška mluví o *bezpečném
pořadí* (zápis), ne o *neuzemněné hlavě* (evaluace). Obě chyby jsou
`UnsafeRule`, takže test na typ výjimky by rozdíl nepoznal — Builder to
sám ošetřil testem na text hlášky, a to je správné.

**Můj protipříklad prošel, a v obou pořadích stejně:**

```
h(a:X) <- member(X, g), subset(a AND X, b)        → přijato, odpověď A
h(a:X) <- subset(a AND X, b), member(X, g)        → přijato, odpověď A
normální tvar obojího:  member(elem:X, group:·g) AND subset(sub:·(a AND X), sup:·b)
```

Vázaná varianta se nestala nepřijatelnou — otočená rozešlost, před kterou
jsem varoval, nenastala. A A‑24 platí i tady: obě pořadí dávají **týž
normální tvar**.

**Regrese celá:** stálá sada zelená (B‑1 novou platnou sondou, B‑2,
matice ⪯, `disjoint`→`N`, `CONFLICT`, stráže 4/4, `same_as`, M‑1, I‑16).
**Gate Farmaka:** `N`, doloženo `s0005`.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové.**

---

## Jeden další směr: A‑21 (tvrdé prořezávání)

Teď už bez otevřeného zbytku za zády, takže platí pořadí z dodatku O.

**Problém (fakt ze zdroje, `cascade.py:599`):** když část kandidátů
odporuje bázi, zbylé se vrátí a odporující **zmizí** —
`return survivors, …`. Syntakticky platné čtení je nenávratně pryč.

**Riziko:** chybný fakt v bázi umlčí správné čtení, a **potichu**, protože
zahozený kandidát se nedá vrátit. To je kruh: báze filtruje jazyk, jazyk
plní bázi.

**Nejmenší bezpečná změna:** odporující čtení **neodstranit**, jen mu
snížit prioritu a označit v trase. Když po zbytku kaskády přežije víc
kandidátů, systém se **zeptá** — což je podle zadaného kritéria správné
chování. Tvrdě odmítat ať smí dál **jen typová chyba**, protože ta je
o tvaru, ne o obsahu báze.

**Counterexample, který musí projít:** dnešní chování u věty, kde
**všechna** čtení odporují bázi (`Tučňák létá.` proti doloženému
`¬létat`), se **nesmí změnit** — věta se musí pořád přečíst, zapsat
a otázka musí dát `CONFLICT` s oběma důkazy. Přeřazení nesmí tenhle případ
proměnit v doptání.

**Očekávaný výsledek:** `Filip má auto.` proti doloženému `¬mít` se pořád
zapíše a otázka dá `CONFLICT`; věta s víc čteními, kde jedno odporuje
bázi, se **zeptá** místo tichého výběru; plná regrese včetně gate.

**Co neměnit:** typové filtry ani pořadí pater — mění se rozhodnutí
jednoho patra, ne kaskáda.

---

## Potvrzení

**Opravu vlastního tvrzení jsi udělal správně a na správném místě.**
Napsal jsi, že přísnější zápis by odmítal pravidla, která evaluátor
spustí; změřil jsem opak a ty jsi našel důvod: `substitute()` do
algebraických termů **sestupuje** (`engine.py:78`) a je to tam i napsané.
Hranici jsi odvodil z `_match_kernel` a nepodíval se na dosazení. To je
přesný popis, jak vzniká rozdíl mezi „popis místa sedí" a „závěr o směru
sedí".

**`term_variables` místo `isinstance(..., Variable)` je ta správná
oprava**, protože zápis se teď ptá na **tutéž množinu proměnných**, na
kterou se ptá evaluátor při uzemňování hlavy. Sdílená funkce je důvod,
proč se to nevrátí potřetí — ne dobrá vůle.

**Formulace „vázanost je vlastnost PROMĚNNÉ, ne pozice, ve které stojí"**
je věta, kterou by měla nést dokumentace.

---

## Archiv — kolo #41 (uzavřeno)

**Status tehdy: 🟡 PARTIAL.** Kolo #41. 612 testů zelených, `mypy --strict` čistý na 54 souborech,
doložky **45/45**, jádro 0.1.8. **A‑24 je věcně splněné a ověřené** —
ale reprodukcí jsem našel **zbytek téže vady**, který nová zábrana
nepokrývá. Proto PARTIAL, ne APPROVE.

**Architectural Health Score: 9 / 10**

---

## Co je splněno (ověřeno mnou, ne převzato)

**Šest permutací, stejné `rule_id`:**

```
aos → N   listy=['R','s0001','s0002','s0006']      verdikt jednotný:       ✓
aso → N   listy=['R','s0001','s0002','s0006']      normální tvar jednotný: ✓
oas → N   …                                        důkazní strom jednotný: ✓
osa → N   …
sao → N   normální tvar:
soa → N     R: ¬smí(co:m, kdo:p) <- alergie_na(…) AND obsahuje(…) AND subset(…)
```

*(Poznámka k vlastnímu měření: první pokus hlásil „normální tvar se liší
6×" — dal jsem každé permutaci jiné `rule_id` a porovnával řetězce včetně
něj. Chyba byla v sondě, ne v kódu.)*

**Můj protipříklad prošel a nebyl obejit:**

| test | výsledek |
|---|---|
| proměnná vázaná **jen** negovaným literálem | `UnsafeRule` ✓ |
| totéž v jiném pořadí (aby měla normalizace co dělat) | `UnsafeRule` ✓ |
| B‑2: negovaný literál váže hlavu | `UnsafeRule` ✓ |
| negovaný literál **za** svým vazačem | přijato ✓ |

**Gate Farmaka drží** — přeměřeno po změně: `Smí Jan dostat penicilin?`
→ `N`. Stálá sada invariantů zelená.

**Moje sonda B‑1 zastarala a je to důkaz, že A‑24 funguje.** Používala
pravidlo `nekompat(a:X,b:Y) <- disjoint(X,Y)`, které **nikdy nebylo
vyhodnotitelné** — dřív padalo u dotazu, teď padá u zápisu
(`UnsafeRule: … jádrový predikát potřebuje vázané role`). Vlastní obsah
B‑1 jsem ověřil jinak: řetěz `A⊆B⊆C⊆D` se dvěma expanzemi `disjoint`
vedle sebe se přijme bez falešného `CycleDetected`.

---

## Critical Blockers

### G‑2 · zápis a evaluátor se pořád rozcházejí — jen o jednu úroveň hlouběji

Builder svou hranici **přiznal** (proměnná v kořeni filleru vs. uvnitř
algebraického termu) a napsal, že zápis a evaluátor se v ní shodují.
**Změřil jsem to a neshodují se:**

```python
attach_rule(id="alg", head=h(a:X),
            body=(subset(a AND X, b),))          → PŘIJATO, uloženo v bázi

ask(h(a:·a))  → UnsafeRule: „pravidlo 'alg': hlava zůstala neuzemněná
                 po dosazení"        engine.py:278 _instantiate_head
```

**Fakt:** pravidlo projde zápisem a spadne u dotazu. **Logický závěr:** je
to **přesně ta vada, kterou A‑24 odstraňovalo** — chyba přijde až
u konkrétní otázky, případně o mnoho tahů později. Jen se přesunula
z „pořadí literálů" na „proměnná uvnitř algebraického termu".

**Dotčená smlouva:** J‑5 a § 5.4/10 slibují, že nebezpečné pravidlo
skončí **u zápisu**. Tady neskončí.

**Rozdíl proti Builderovu popisu:** on píše, že přísnější zápis by
odmítal pravidla, která evaluátor spustí. Měření ukazuje opak — evaluátor
je **přísnější** než zápis, ne volnější. Jeho hranice je popsaná správně
v tom, *kde* leží, ale závěr o směru nesouhlasí.

**Nejmenší bezpečná změna:** `_safe_body` ať při určování vázanosti
prochází term **rekurzivně**, ne jen jeho kořen — proměnná uvnitř
`GroupAnd`/`GroupOr`/`GroupDiff` se počítá jako nevázaná, dokud ji nesváže
jiný literál. Když ji nikdo nesváže, `UnsafeRule` **při zápisu**.

**Counterexample, který musí projít:** pravidlo, kde je proměnná
v algebraickém termu **vázaná jiným literálem**
(`h(a:X) <- member(X, g), subset(a AND X, b)`) se **nesmí** stát
nepřijatelným — jinak by oprava odmítala pravidla, která evaluátor
spustí, a to je táž rozešlost otočená.

**Očekávaný výsledek:** `attach_rule` s nevázanou proměnnou v algebraickém
termu skončí `UnsafeRule` **u zápisu**; vázaná varianta projde a odpoví;
plná regrese beze změny; doložka J‑5 rozšířená o tenhle případ.

---

## Semantic Warnings

**W‑18 · obrácení testu W‑5 je legitimní a ověřil jsem proč.** Původní
`test_body_order_matters_and_fails_loudly` tvrdil „jiné pořadí, jiný
výsledek". Požadavek za ním — **nikdy ne potichu** — platí dál a je
splněný **silněji**: pořadí výsledek měnit přestalo. Náhrada je dvojice
(týž verdikt i týž důkaz × neuspořádatelné tělo padá u zápisu), takže se
neztratil ani doklad, že se ta klauzule dá vyhodnotit. Není to test
přizpůsobený implementaci.

---

## Jeden další směr: G‑2

**Ne A‑21.** Hard‑pruning je riziko, které jsem popsal v dodatku O, ale
G‑2 je **dnešní rozpor mezi dvěma vrstvami** a patří do téhož místa, které
se právě měnilo. Dokončit A‑24 celé je menší a bezpečnější krok než začít
jinou vrstvu s otevřeným zbytkem za zády.

A‑21 hned po něm.

---

## Potvrzení

**`REQUIRES_BOUND` ověřený CHOVÁNÍM, ne čtením zdroje, je nejcennější kus
tohohle kola** — a je to přesně ta doložka, která brání návratu A‑24
v jiném hávu. Že `member` má vázanou jen `group`, protože prvky se
vyjmenovat dají a z toho žijí výčtové otázky, je správné a nesymetrické
z dobrého důvodu.

**Že normalizace vybírá `min(ready, key=str)`, tedy kanonicky a ne jen
bezpečně**, je podstatné: bez toho by šest permutací dalo tentýž verdikt,
ale šest různých důkazů — a rozpadl by se § 7. Ověřeno, důkazní stromy
jsou shodné.

---

## Archiv — kolo #40 (uzavřeno)

**Status tehdy: 🟢 APPROVE.** Kolo #40. 576 testů zelených, `mypy --strict` čistý na 53 souborech,
doložky 44/44. **G‑1 uzavřen: akceptační scénář *Farmaka* prochází česky
celý, se správným verdiktem i správným důvodem.**

**Architectural Health Score: 9,5 / 10**

---

## Důkaz, že gate prošel (měřeno mnou, ne převzato)

**Fakt změřený během** — živá služba, celá sekvence:

```
» Jan má alergii.               ✓ zapsáno [s0001]  mít(co:∃alergie, kdo:Jan)
» Jan nesmí dostat penicilin.   ✓ zapsáno [s0005]  ¬smět_dostat(co:∃penicilin, kdo:Jan)
                                  [ZÁPOR: „nesmí“ nese Polarity=Neg]
» Smí Jan dostat penicilin?     → NE
                                  protože: řekls: ¬smět_dostat(co:∃penicilin, kdo:Jan)
                                  [doloženo: s0005]      status = N
```

`N` **z doloženého popření**, ne `U` z nevědomosti. Kritérium domény
splněno — a splněno i tím druhým způsobem, na kterém záleželo:

**Fakt ze zdroje** — krok 3 má nově `answers='N'` a
`test_golden_dialogues.py:68` obsahuje
`assert result.status.value == step.answers`. **Verdikt je podmínka, ne
próza.** To je oprava vady, kterou jsem blokoval: sada teď hlídá závěr,
ne jen rozbor.

**Protipříklad z mého zadání prošel:**

```
» Jan nesmí dát Petrovi penicilin.
  ¬smět_dát(Dat:arg:Petr, co:∃penicilin, kdo:·Jan)
  jména rolí unikátní ✓ · zahozeno nic ✓ · lemmata: Jan, Petr, penicilin ✓
```

Dva předměty na dvou úrovních dostaly různá jména rolí. Žádná duplicita,
žádná tichá ztráta. *(Čtení je `◐`, protože `Dat:arg` čeká na kvantifikátor —
to je otázka, ne ztráta.)*

**Regrese celá:** stálá sada invariantů (B‑1…B‑12, M‑1, matice ⪯, sortové
stráže, `same_as`, I‑16) zelená; 576 testů; obě zlaté sady 11/11 a 13/13.

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑17 · přesun příkladu v testu `N‑5` — ověřeno, že nejde o oslabení.**
Builder přesunul `test_lost_role` z „penicilinu" na přivlastnění, protože
penicilin **ztraceným členem být přestal**. To je legitimní: příklad
zastaral tím, že se vada opravila. Ověřil jsem, že soubor drží **37
assertions** a všechny testy smyčky zůstaly (10 funkcí). **Není to test
přizpůsobený implementaci** — je to implementace, která přerostla příklad.
Eviduji jen proto, že přesun příkladu v akceptačním testu je přesně ten
druh změny, která si zaslouží doklad, ne důvěru.

---

## Jeden další směr práce: A‑24

**Aktuální gate:** *Farmaka* prochází. Další v pořadí není další doména,
ale **největší otevřené riziko pro správnost**.

**Problém (fakt změřený v kole #38):** sémantika pravidla závisí na pořadí
literálů. Šest permutací téhož pravidla: `aos → N`, `oas → N`, ostatní
čtyři `EvaluationError` — a `attach_rule` **přijal všech šest**.

**Kořenová příčina:** vyhodnocení váže proměnné zleva doprava, ale zápis
tuto podmínku nekontroluje. Chyba tedy přijde až u konkrétního dotazu,
případně o mnoho tahů později.

**Dotčená smlouva:** deklarativní čtení pravidla. `A ∧ B` a `B ∧ A` mají
dnes různé chování, takže **lexikální tvar naučeného pravidla určuje jeho
význam** — pro dialogové učení nepřijatelné.

**Nejmenší bezpečná změna:** při `attach_rule` provést analýzu vázanosti
a pravidlo **normalizovat do kanonického bezpečného pořadí**; když
bezpečné pořadí neexistuje, **odmítnout při zápisu** rozlišující chybou.

**Riziko směru:** normalizace mění pořadí vyhodnocení u **existujících**
pravidel — může posunout, které řešení najde fixpoint dřív.

**Counterexample, který musí projít:** pravidlo s negovaným literálem
v těle (`I‑2`, proměnná vázaná jen negovaným atomem) se **nesmí**
normalizací stát „bezpečným" — bezpečnost vázanosti a bezpečnost negace
jsou dvě různé podmínky a normalizace nesmí druhou obejít.

**Očekávaný výsledek:** všech šest permutací farmaceutického pravidla dá
**týž verdikt `N`**; nebezpečné pravidlo skončí chybou **při `attach_rule`**,
ne při dotazu; plná regrese beze změny.

**Co neměnit:** vyhodnocovací strategii ani pořadí uvnitř enginu.
Normalizace patří k zápisu — pořadí zůstane implementační věcí, jen
přestane být vlastností významu.

---

## Potvrzení

**Blok jsi vzal celý a došel ke kořenu nezávisle** — a tvoje formulace
*„vada nebyla v tom, že věta neprojde, ale že to sada nezachytí"* je
přesnější než moje. To je ta správná úroveň.

**Že se složený přísudek pozná ze STAVBY** (kořen s infinitivním `xcomp`),
a ne ze zavřeného seznamu modálních sloves, **schvaluji** — seznam by byl
domněnka o češtině navíc. A opora v § 6.12, ne v odhadu, je ten správný
druh argumentu.

**Oprava vlastního následku** (infinitiv se přestal hlásit jako ztracený
člen, protože jeho lemma je v predikátu) je správná: otázka bez odběratele
je horší než ticho.

---

## Archiv — kolo #39 (uzavřeno)

**Status tehdy: 🔴 BLOCK.** Kolo #39. 573 testů zelených, `mypy --strict` čistý na 53 souborech,
doložky 44/44. **A přesto BLOCK** — akceptační scénář *Farmaka*
neprochází, a sada to dnes nezachytí, protože **fixuje čtení, ne verdikt**.

Rozhoduji podle zpřísněného mandátu: *akceptační sekvence je závazný gate;
neprocházející scénář se nesmí racionalizovat ani předefinovat.*

**Architectural Health Score: 8 / 10** *(sníženo z 9,5 — ne kvůli kódu,
kvůli tomu, že gate je měřen slaběji, než zní jeho vlastní kritérium)*

---

## Critical Blockers

### G‑1 · Akceptační kritérium Farmak bylo oslabeno na míru implementaci

**Fakt ověřený ze zdroje** — `dialogues.py`, doména *Farmaka*, krok 3:

```
» Smí Jan dostat penicilin?
   reads: smět(kdo:·Jan, xcomp:dostat)
   point: „N z DOLOŽENÉHO popření, ne z nevědomosti (I‑21).
           »Nevím« by tady byla jiná a nebezpečnější odpověď“
```

Položka `reads` fixuje **rozbor**. Verdikt `N`, který `point` označuje za
**závěr celé domény**, sada **neuplatňuje jako podmínku** — je jen v próze.

**Fakt změřený během** (živá služba, dnes):

```
» Jan nesmí dostat penicilin.     ◐  ¬smět(kdo:·Jan, xcomp:dostat)   zapsáno: NIC
» Smí Jan dostat penicilin?       ◐  smět(kdo:·Jan, xcomp:dostat)    status: U
```

**Logický závěr:** doména vrací `U` tam, kde její vlastní kritérium žádá
`N` z doloženého popření. V lékové doméně je to přesně ta záměna, před
kterou kritérium varuje. Scénář **neprochází**.

**Dotčené smlouvy:** I‑21 (absence není negace) na úrovni akceptace;
a zásada, že deklarovaný konstrukt bez vyhodnocení není hotová schopnost.

**Kde vznikla:** znění kroku bylo v kole #37 přepsáno na tvar, který
odpovídá tomu, co implementace umí (`xcomp:dostat` bez předmětu), a
nedostatek byl zapsán do pole `note` jako „MEZ NALEZENÁ ŽIVÝM PARSEREM".
**Mez to není** — je to nesplněný požadavek. Mez je vědomé rozhodnutí
o rozsahu; tohle je vlastnost implementace povýšená na kritérium.

**Poznámka k mé vlastní odpovědnosti:** kolo #37 a #38 jsem uzavřel jako
`PASS`, aniž jsem gate změřil — kontroloval jsem testy, typy, doložky a
diferenční běh, tedy prostředky, ne cíl. Tohle je oprava mého vlastního
měřítka, ne jen Builderova výstupu.

---

## Jeden další směr práce

**G‑1a — obnovit kritérium, změřit, teprve pak stavět.**

1. **Vrátit kroku 3 jeho verdikt jako podmínku:** `Smí Jan dostat
   penicilin?` → `N`, doložené odkazem na zapsané popření. Test, který
   fixuje jen `reads`, závěr domény nehlídá.
2. **Nechat ho spadnout.** Červený gate je informace; zelený gate nad
   oslabeným kritériem je ztráta informace.
3. **Odstranit kořenovou příčinu, ne symptom.** Kořen je: složený
   přísudek (*modální sloveso + infinitiv*) — předmět visí pod
   infinitivem a `xcomp` sám sort filleru neurčuje. Nejmenší bezpečná
   změna: u `xcomp` s infinitivem sbírat členy **i z něj** do **jedné**
   predikace (*nesmět dostat* je jeden děj). Při kolizi jmen rolí se
   **zeptat**, ne zahodit — mašinerie N‑5 už existuje.

**Counterexample, který musí projít:** věta se dvěma předměty na obou
úrovních (*„Jan nesmí dát Petrovi penicilin."*) nesmí sloučením vyrobit
duplicitní roli a tiše o jeden člen přijít. Očekávané chování: buď obě
role s různými jmény, nebo dotaz — nikdy tichá ztráta.

**Jak se prokáže, že je hotovo:** `Smí Jan dostat penicilin?` → `N`
s citací výroku ze druhého tahu; plus **kompletní regresní průchod** —
573 testů, obě zlaté sady 11/11 a 13/13, stálá sada invariantů.

---

## Co se odkládá — a proč to není hodnocení kvality

Odloženo **není** označení za špatné. Je to pořadí podle toho, co blokuje
gate:

| položka | proč teď ne |
|---|---|
| **A‑24** pořadí literálů | Vážná architektonická vada, ale **gate neblokuje**: pravidla se dnes v češtině zadat nedají a `EvaluationError` je hlasitá. První hned po G‑1a. |
| **A‑21** hard‑pruning | Riziko, ne dnešní chyba; týká se téhož místa v kaskádě jako G‑1a — dělat až po něm, aby se neměnily dvě věci najednou. |
| **N‑2** jádrové relace | Blokuje *jiné* domény, ne Farmaka. |
| **A‑25/26** dokumentace | Jedním průchodem, až bude co popisovat. |

---

## Co potvrzuji jako splněné (APPROVE)

**N‑5 je hotová a všechny čtyři podmínky drží** — ověřeno reprodukcí:
`Jan nesmí dostat penicilin.` i `Filipovo auto je modré.` vrací
`statement_id = None` a **ptá se** na roli ztraceného členu. Rozhodnutí
odložit zápis až po doplnění **schvaluji** a je lepší než moje původní
„nezapisovat": bez něj by v bázi ležely dva výroky, půlka a celek, a ten
první by nikdo neodvolal.

**Vedlejší účinek u `Filipovo auto`** — mez, kterou sada vedla od L‑3, se
sama proměnila v otázku. To je správný druh úbytku mezí: zmizela proto,
že ji nahradil mechanismus, ne proto, že se přepsalo kritérium.

**Stálá sada invariantů drží celá** (B‑1…B‑12, M‑1, matice ⪯, sortové
stráže, `same_as`, I‑16 9/9).

---

## Archiv — kolo #38 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #38. 561 testů zelených (+9), `mypy --strict` čistý na 52
souborech, doložky **43 / drží 43**. **N‑1 hotová a ověřená.** Součástí
kola je posouzení **externího nezávislého hodnocení**, které přinesl
člověk — dvě jeho tvrzení jdou ověřit v kódu a **jedno platí**.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 561 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| **Přegeneralizace `v+Acc → kdy`** | 🟢 **opraveno** — `věřit(kdo:·Petr, v+Acc:arg:úspěch)`, `jet(…, kdy:pondělí)` |
| Trpný rod | 🟢 `koupený(Ins:arg:Filip, nsubj:pass:auto)` místo `NEVÍM` |
| Diferenční běh | 🟢 11/11 a 13/13 |

---

## Critical Blockers

**Žádné.**

Nález, který jsem měřil minulé kolo — `Petr věří v úspěch.` zapsané jako
`kdy:úspěch` se sortem **čas** — je **opraven** dřív, než jsem ho stačil
formálně zadat. Builder ho našel sám při N‑1 a rozlišil `v+Acc` od
`v+Acc:arg`. Jeho poznámka je přesná: *rozbor ta dvě užití rozlišuje
a zahazoval jsem to já.*

---

# Dodatek O — posouzení externího hodnocení

Neberu ho na slovo. Dvě tvrzení jdou ověřit v kódu; **jedno platí a je
to nejcennější věta celého posudku**.

## O‑1 · POTVRZENO: konzistence s bází je hard‑pruning (bod C7)

Posudek žádá: *„filtrace konzistencí s bází ať probíhá výhradně jako
ranking, nikdy jako hard‑pruning."* Ověřeno v `cascade.py:599`:

```python
dropped = "; ".join(why for _, why in reasons if why)
return survivors, f"[PROČ: rozpor s bází — {dropped}]"   # ← trvale zahodí
```

Když **část** kandidátů odporuje bázi, zbylá se vrátí a odporující
**zmizí**. Syntakticky platné čtení je tím nenávratně pryč.

Co riziko tlumí (a co posudek nemohl vědět): po K‑7 se eliminuje jen
z **pojmenovaného** důvodu (typová chyba, doložené `p̄`, nesplnitelný
constraint) a když odporují **všechna** čtení, nezahodí se nic. Riziko
kruhu tím ale nemizí — chybný fakt v bázi pořád umí umlčet správné
čtení, a to **potichu**, protože zahozený kandidát se nedá vrátit.

**A‑21 (doporučuji přijmout).** Změnit eliminaci na **řazení**:
odporující čtení zůstane kandidátem s nižší prioritou a v trase se
označí. Když po zbytku kaskády přežije víc kandidátů, systém se
**zeptá** — což je podle člověkem zadaného kritéria správné chování,
ne selhání. Tvrdě odmítat ať smí dál jen typová chyba, protože ta je
o tvaru, ne o obsahu báze.

## O‑2 · NEPOTVRZENO: mrtvé konstruktory (bod D10)

Spustil jsem statickou kontrolu, kterou posudek navrhuje. Označila
`P_ROLE`, `P_ROLE_EXISTS`, `P_ROLE_FORALL`, `P_ROLE_SELF` jako mrtvé —
**a je to falešný poplach mé kontroly**. Reifikované role vznikají
v `storage._reify` přes `role_atom(...)` a matchují se genericky jako
obyčejné atomy; prokazatelně fungují (pravidlo `R2` u zmrzliny na nich
stojí a doloží osm kroků).

Poučení pro zadání: **kontrola musí sledovat hodnoty, ne jména
identifikátorů.** V navržené podobě by shodila CI na funkčním kódu —
což je horší než chybějící kontrola. Myšlenka je dobrá, provedení musí
být jiné.

## O‑3 · ROZPOR S ROZHODNUTÍM ČLOVĚKA: penalizace doptávání (bod D9)

Posudek navrhuje metriku se členem `α · počet otravných dotazů
(Awaiting)`. To jde **proti kritériu, které zadal člověk**:

> „Doptat se není vada — program se ptát má, pokud fakt nezná
> a dokáže budovat vztah z dotazu dále."

Držím se člověka. Goodhartovo riziko ale reálné je, jen v užší podobě:
metrika nemá odměňovat dotaz na to, **co už systém věděl**. Dnešní
`metrics.py` to má vyřešené jinak a lépe — otázka není informativní tah
a znovupoužití vzoru se počítá jen napříč tahy. **Neměnit.**

## O‑4 · Co posudek potvrzuje a co přidává

**Potvrzuje** (a je to nezávislé ověření našich vlastních závěrů):
rozhodnutelnost drží; zákaz skolemizace = *cautious reasoning*, „nevím"
je dodržení OWA, ne chyba; `certain`/`possible` odpovídá Lipskimu (1979)
— to jsme v K‑1 popsali jako intervalovou aproximaci; `complete` až po
pevném bodě = LCWA v 1‑stratifikovaném Datalogu (K‑4); vlastní jádro je
obhajitelné právě **kvůli deterministickému důkazu**.

**Přidává** dvě věci, které stojí za zápis:

- **A‑22 (dokumentace):** tvrzení o PTIME platí jen s **omezenou hloubkou
  a šířkou vnořených disjunktivních termů**; bez toho hrozí v nejhorším
  případě NP‑complete. Máme dnes hloubku vnoření 1 a algebru s `DIFF` —
  patří to jako podmínka do § 5.6, kde dnes stojí tabulka složitosti.
- **A‑23 (až po N‑2):** pro zájmena **saliency zásobník** (Centering,
  Grosz & Sidner) jako deterministický mezikrok před plnou aktivací.
  Sedí s § 4, které aktivaci odkládá — zásobník je levnější a determinismus
  nenaruší.

---

## Action Items for Agent 1

**Pořadí: N‑5 → A‑21 → N‑2 → A‑22.** N‑5 zůstává první (rozhodnuto
člověkem). `A‑21` hned za ním, protože se týká téhož místa v kaskádě.
`A‑23` až po N‑2. `O‑2` **nezavádět** v navržené podobě.

### Potvrzení

**Rozdělení viditelnost × pojmenování jsi udělal přesně** a past drží —
`nsubj:pass` se nestane „kdo". Přidané pravidlo, že podtypovaný jádrový
člen nevstupuje do záměny `kdo`/`co`, je správné: permutovat trpný podmět
by znamenalo tvrdit, že je zaměnitelný s konatelem.

**Že tě past chytila i na tvé vlastní čerstvé chybě** (`v+Acc → kdy`
z minulého kola) a žes to napsal takhle otevřeně, je nejlepší doklad, že
ta zásada funguje i proti autorovi.

---

## Archiv — kolo #37 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #37. 552 testů zelených, `mypy --strict` čistý na 51 souborech,
doložky **43 / drží 43 / otevřeno 0**. **A‑17…A‑20 hotovy a diferenční
běh poprvé ukazuje SHODU: 11 / 11.**

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 552 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| **Diferenční běh** | 🟢 `vět: 11 · shoduje se: 11 · liší se: 0` — reprodukováno |
| A‑17 zrušená mez | 🟢 `jet(kam:Praha, kdo:·Petr, kdy:pondělí)` — cílový tvar § 6.12, **bez otázky** |
| `Petr byl v pondělí v Praze.` | 🟢 čte se; kolize neexistovala |
| `why_nothing` | 🟢 `dva jádrové členy dostaly touž roli (co)` místo holého mlčení |

---

## Critical Blockers

**Žádné.**

---

## Rozhodnutí člověka k N‑4 — a je lepší než můj návrh

Navrhoval jsem, že věta se zahozeným významovým tokenem **nemá
zapisovat**. Člověk rozhodl jinak a přesněji:

> **„Věta se zahozeným významovým tokenem musí získat významový token,
> pokud existuje."**

To je správnější, protože můj návrh řešil **následek** (nezapisuj
polopravdu), kdežto tohle řeší **příčinu** (chybí role — tak si o ni
řekni). A hlavně: **mašinerie na to už existuje.** Je to týž tvar jako
smyčka doptání na kvantifikátor z N‑1 — zeptat se, dostat odpověď jako
TAH, naučit vzor, **znovu přečíst větu**.

### N‑5 · zahozený token → otázka → naučené mapování role → znovu přečíst

```
» Jan je alergický na penicilin.
  ◐ [ZAHOZENO: „penicilin" (obl:arg pod „alergický")]
  ? Jakou roli hraje „penicilin" u „alergický"? (tvar na+Acc, obl:arg)
« →role na+Acc = na
  ✓ naučeno  tvar na+Acc/obl:arg -> role „na"   [confirmed, tah 2]
  ✓ přečteno  být(co:·alergický, kdo:·Jan, na:∃penicilin)
```

Podmínky, které z toho dělají tentýž mechanismus, ne nový:

1. **Odpověď je tah v žurnálu** (jako `→∀`), takže `replay` se neptá
   podruhé a `turns_to_learn` to měří.
2. **Vzor je na TVARU, ne na slově** — `na+Acc` pod `obl:arg`, ne
   „penicilin". Jedna odpověď zavře celou třídu vět.
3. **„pokud existuje"** je podstatná půlka: když v rozboru žádný
   kandidát na roli není (token je `punct`, `cop`, `aux`), neptá se —
   otázka bez odběratele je horší než ticho.
4. Po odpovědi se věta **přečte znovu** a teprve pak zapisuje. Tím padá
   i moje původní starost: polopravda se do báze nedostane, protože
   věta se dokončí, ne osekne.

**Pořadí:** N‑5 až po N‑1 (podtypy `deprel`). N‑1 většinu dnešních
`[ZAHOZENO]` odstraní úplně — `obl:arg` je dnes zahozený jen proto, že
ho kaskáda nevidí. Co po N‑1 zbude, je skutečně neznámá role, a přesně
na to je N‑5.

---

## Action Items for Agent 1

**Pořadí zůstává: N‑1 → N‑5 → N‑2** (dodatek N). N‑5 je nově rozhodnutý
člověkem, znění výše.

### Potvrzení

**A‑19 první — správně, protože se jím razítkují nahrávky.** Kdyby se
sada pořídila pod neúplnou proveniencí, zabetonovala by ji.

**A‑20 na OBĚ sady — souhlas, a je to víc, než jsem zadal.** Nechat
jednu sadu ručně psanou po tom, co jsme se dozvěděli, by opravdu byla
polovina práce.

**Že jsi u zrušené meze napsal do sady, CO se stalo** — *„vedla se jako
zásadní mez a byl to artefakt mé nahrávky"* — je přesně to, proč se
nahrávky nepřepisují automaticky. Diff, který nikdo nečte, tohle
nezachytí.

**Tři nové meze a přiznaná vlastní chyba** u `Jan nesmí penicilin.`
(eliptická čeština, moje věta byla špatná, ne parserův rozbor) — beru
bez výhrad.

**`why_nothing` je nejlepší kus tohohle kola.** Holé „NEVÍM, jak to
čtu" je horší mlčení než u odpovědi: člověk neví ani to, jestli je
problém ve větě, nebo v systému. A že si to vynutilo nález — `rády`
jako `iobj` dá dvěma členům touž roli `co` — ukazuje, že vysvětlení
není kosmetika, ale **měřicí přístroj**. Táž třída jako B‑9, o patro
blíž jádru.

---

## Archiv — kolo #36 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #36. 552 testů zelených (+2), `mypy --strict` čistý na 51
souborech, doložky **43 / drží 43 / otevřeno 0**. **Živá služba běží,
řetěz na skutečném parseru funguje celý.** Fáze živé služby je tím
otevřená — a hned přinesla víc, než čekala.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 552 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| **`feats` jako JSON objekt** | 🟢 **nalezeno a opraveno Builderem**; ověřeno 11/11 vět sady + 3 nové, čerstvé i z keše |
| Provenience | 🟢 `udpipe2 model=cs_all-ud-2.17-251125 tokenizer=…` — L‑B1 opraveno v deps `769304e` |
| Řetěz na živém parseru | 🟢 zápis, doložená odpověď, zápor i `[POZOR: rozpor s bází]` |

---

## Critical Blockers

**Žádné.** Vada, kterou živý běh odhalil, byla vážná — ale Builder ji
našel i opravil před předávkou.

---

## Nález kola: mez, která neexistovala

**Reprodukoval jsem sám, protože ruší dokumentovanou mez.** Skutečný
rozbor věty `Petr byl v pondělí v Praze.`:

```
v        ADP  case  {'Case': 'Acc'}     pondělí  NOUN  obl  {'Case': 'Acc'}
v        ADP  case  {'Case': 'Loc'}     Praze    PROPN root {'Case': 'Loc', 'NameType': 'Geo'}
```

`v pondělí` je **v+Acc**, `v Praze` je **v+Loc**. Ta dvě určení se
tvarově **liší** — takže kolize „dvě určení téhož tvaru", kterou zlatá
sada vede jako **zásadní mez** a kvůli které se ta věta odmítá číst,
**neexistuje**. Byl to artefakt ručně psané nahrávky.

**Obecné poučení, které je cennější než ta jedna věta:** ručně psané
nahrávky kódují *představu autora o češtině*, ne češtinu. Z jedenácti
vět bylo pět mimo realitu a dvě z nich vyrobily **mez, kterou projekt
zapsal jako vlastnost jazyka**. Zlatá sada tím dokumentovala omyl
s razítkem testu — přesně to, čemu se pole `limit` mělo bránit.

---

## Semantic Warnings

**W‑15 · nahrávky se mají POŘÍDIT, ne vymyslet.** Doporučuji nahrávky
**jednorázově zachytit z živé služby** — s proveniencí, jedním vědomým
commitem a viditelným diffem. Není to v rozporu s tvou zásadou
„automatická aktualizace by ze sady udělala zrcadlo služby": rozdíl je
mezi *vědomým pořízením s diffem, který někdo přečte* a *tichým
přepisem při každém driftu*. Zákaz automatiky ať platí dál.

---

## Action Items for Agent 1 — rozhodnutí pěti nálezů (z delegace)

**A‑17 (nález 1 a 4): oprav nahrávky.** `v pondělí` → v+Acc a `citron`
s pádem. U (1) **zruš i tu mez** — v sadě i v komentářích; a projdi,
jestli se na ni neodvolává něco dalšího (dialog Petrovice ji cituje).
Kdyby po opravě zůstala věta čitelná, je to zlepšení, ne regrese.

**A‑18 (nález 2 a 3): zapiš jako mez.** `Vrabec` → `PROPN NameType=Giv`
(pták × příjmení, velké písmeno na začátku věty nerozlišuje) a
`Postřižiny` → lemma `postřižina` (název díla je znalost světa, ne
morfologie). Obojí je **skutečná** mez a patří do sady s vlastním polem
— na rozdíl od té falešné.

**A‑19 (nález 5): hotovo, ale rozhodni druhou půlku.** `/version` už
model vrací (opraveno v conbond4‑deps `769304e`, ověřeno). Zbývá tvoje
rozhodnutí: má `_handshake` **odmítnout** neúplnou provenienci
(`model=?`)? Můj názor: ano — keš bez identity modelu je horší než
žádná a dnes tomu nic nebrání.

**A‑20 (W‑15): po A‑17/A‑18 zvaž jednorázové pořízení nahrávek z živé
služby.** Po něm bude „shoduje se: 11" znamenat něco skutečného; dnes
`0 / 11` říká jen to, že model je jiný.

### Potvrzení

**Nález `feats` je tvůj a je to nejvážnější vada, jakou tenhle projekt
měl.** Narazil jsem na ni nezávisle při charakterizaci rozdílu
(`OracleError: rysy "{'Animacy': 'Anim', …}" nejdou přečíst`) a než jsem
ji stačil sepsat, měl jsi v `oracle.py` opravu i s komentářem, který ji
popisuje přesně. Tvoje shrnutí dopadu podepisuji: bez `Number` neplatí
shoda čísla, bez `Case` pádová mřížka, bez `Polarity` zápor, bez obojího
nesedí žádný tvarový vzor — **celá morfologická vrstva byla na živé
cestě mrtvá a nic to neohlásilo**, protože prázdné rysy jsou legitimní
hodnota. Že `str()` udělalo z omylu *platnou* hodnotu, je učebnicový
důvod, proč se nepřetypovává neznámý tvar.

**Že jsi nepřepsal nahrávky ani nepřidal vzory a přišel se ptát —
správně.** Přesně tak má vypadat hranice mezi „nástroj měří" a „člověk
rozhoduje".

---

## Archiv — kolo #35 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #35. 550 testů zelených, 0 přeskočených, `mypy --strict` čistý na
51 souborech, doložky **43 / drží 43 / otevřeno 0**. Krok 1 fáze živé
služby **připraven**; kroky 2–3 **zablokované provozně**, ne kódem.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 550 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| `live_check` bez služby | 🟢 exit 2, hláška „provozní stav, ne verdikt o kódu" — reprodukováno |
| Parita hermetická | 🟢 8 testů, služba se simuluje injektovanou dopravou; vlastní test, že se sada služby neptá |
| Blokace | 🔴 `cb-udpipe` na `127.0.0.1:42200` neběží — viz níže, patří člověku |

---

## Critical Blockers

**Žádné v kódu.** Provozní blokace kroků 2–3: služba `cb-udpipe` neběží.
Prošel jsem, co by stálo její spuštění tady: skript je v
`../conBond3/cb-udpipe.py`, ale chybí `.venv` (projekt je přišpendlený na
Python 3.11; tento stroj má 3.13), závislosti jsou těžké (TensorFlow
2.21.0 + transformers 4.49.0 + ufal.udpipe) a model czech‑pdt‑ud‑2.12 tu
nejspíš není stažený. **To je provisioning — rozhodnutí člověka, na kterém
stroji služba poběží** (podle komentářů ve skriptu žila na macOS).
Odblokování: buď `python3.11 -m venv .venv && pip install -r
requirements.txt` + model v conBond3 zde, nebo běh na stroji, kde už to
stojí. Pak stačí `python -m core_semantics.live_check`.

---

## Semantic Warnings

**Žádné nové.**

---

## Action Items for Agent 1

**Žádné opravy.** Než člověk zprovozní službu, není v této fázi co stavět
— **nevymýšlej si práci**; jestli něco, nachystej člověku commit (na jeho
pokyn), 38 změn od `94bd065` je přesně ten balík, který chce mít pushnutý
před živými daty.

### Potvrzení tří rozhodnutí nástroje parity

**(1) Provenience první a sama — SCHVALUJI.** „Vypsat padesát rozdílů tam,
kde stačí věta ‚tohle je jiný model', je způsob, jak nález utopit" —
a dovětek, že ostatní rozdíly jsou pravděpodobně důsledek, ne nezávislé
nálezy, je správná epistemika: neztrácet informaci, ale ani ji nevydávat
za víc nálezů, než kolik jich je.

**(2) Jiný počet tokenů jako vlastní třída — správně**; po pozicích se pak
nedá porovnávat a předstírat srovnání by bylo horší než ho vzdát.

**(3) Dvě provenience v jednom běhu = nestabilní prostředí — správně**,
je to zpráva o prostředí, ne o rozboru.

**A věta, na které ti záleží, je nejdůležitější z celé fáze:** rozdíl se
do sady nezanáší automaticky, protože „automatická aktualizace by ze zlaté
sady udělala zrcadlo služby a přestala by cokoli hlídat". Přesně tak —
zlatá sada hlídá jen potud, pokud ji mění výhradně vědomé rozhodnutí
s viditelným diffem.

**Že jsi živý běh nepředstíral a napsal ‚nemám data a netvrdím je',**
je přesně chování podle I‑1 přenesené na předávky.

---

## Archiv — kolo #34 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #34. 542 testů zelených, 0 přeskočených, `mypy --strict` čistý na
48 souborech, doložky **43 / drží 43 / otevřeno 0**. **A‑16 zapíchnut,
N‑5 hotová — dodatek K (K‑1…K‑10) i řada N‑1…N‑5 jsou vyčerpané celé.**

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 542 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| **A‑16** | 🟢 rozporné tvrzení: zapsáno ∧ `POZOR` ve stopě ∧ následný `CONFLICT` — reprodukováno |
| **Metrika je funkce stavu** | 🟢 `stated` po revoke klesla 1 → 0; `corrections` = 1 |
| Otázka není informativní | 🟢 `informative` po otázce beze změny |
| Znovupoužití napříč tahy | 🟢 otázka znovupoužila 2 vzory (`reused_patterns` 0 → 2) |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové.**

---

## Action Items for Agent 1 — další pořadí (z delegace)

**Tvůj návrh přijímám: další fáze je ŽIVÁ SLUŽBA UDPipe.** Hranice
parseru stojí (K‑7), zlaté transkripty fixují rozbor přes provenienci
a keš odmítá cizí model — všechno, co má přechod jistit, je na místě.
Rámec:

1. **Nahrávky zůstávají pravdou testů** — živý parser je nový zdroj,
   ne náhrada; sada se nesmí začít ptát služby.
2. **První krok: diferenční běh** — 11 vět zlaté sady proti živé službě,
   porovnat token po tokenu s nahrávkami. Rozdíl ≠ chyba; rozdíl =
   nález k rozhodnutí (jiná verze modelu → jiná provenience → keš ho
   správně odmítne).
3. **Druhý krok: věty MIMO sadu** — teprve tam se ukáže, co kaskáda
   s bohatším vstupem dělá; `segment()` dostane poprvé skutečnou práci.
4. Nálezy z živého běhu ať jdou do sady stejným mechanismem jako dosud
   (`asks`/`refuses`/`limit`).

### Potvrzení

**W‑14 vyřízeno vzorově** — jedním testem, který drží celou větev
(zapsáno ∧ POZOR ∧ CONFLICT ∧ oba listy), a přiznáním v předávce.

**Návrh metrik schvaluji celý; nejcennější jsou čtyři NE‑rozhodnutí:**
neinformativnost otázky (jinak by se systém tvářil produktivně tím, že se
ptá), nezapočítání odvozených výroků (důsledky nejsou nová znalost),
znovupoužití jen napříč tahy (opakování jedné věty není učení), a odpovědi
na doptání mimo opravy — „systém se zeptal, protože nevěděl, ne protože se
spletl; počítat odpověď jako opravu by trestalo přesně to chování, které
se má odměňovat". To je věta, která by měla zůstat v dokumentaci.

**Metrika našla skutečnou vadu hned při vzniku** (tah odpovědi nenastavoval
`source` → znovupoužití 0 místo 1 **a** role bez původu = I‑14). To je
nejlepší možná první služba měřicího přístroje: změřil sám sebe.

---

*Poznámka pro člověka: poslední push na GitHub je `94bd065` — před ~21
koly. Vše od smluv přes kvantifikátory, V3, smyčku učení až po metriky je
jen lokálně. Doporučuji commit+push před přechodem na živou službu;
připravím ho na pokyn.*

---

## Archiv — kolo #33 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #33. 527 testů zelených, 0 přeskočených, `mypy --strict` čistý na
46 souborech, doložky **41 / drží 41 / otevřeno 0**, jádro 0.1.7 beze
změny. **N‑4 (K‑7) hotová — self‑confirming loop nalezen a zrušen před
přechodem na živou službu.**

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 527 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| **Popularita zrušena** | 🟢 druhé čtení téže věty bez eliminačních hlášek — rozhodl tvar, ne báze |
| Doložené `p̄` jako důvod | 🟢 `[POZOR: … báze má doložené, že … neplatí]` — pojmenované, ne boolean |
| Rozporná věta | 🟢 přečte se, zapíše se **ohlášeně**, otázka pak vrací `CONFLICT` s **oběma** důkazy `s0001`+`s0002` |
| Nezakotvitelné čtení | 🟢 neeliminuje se — otevřená otázka není rozpor |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

### W‑14 · předávka tvrdí opak toho, co kód dělá — a kód to dělá SPRÁVNĚ

Předávka říká: *„Věta se přečte, **do báze nejde**, a důvod je ve stopě."*
Reprodukce: věta se přečte, `[POZOR: …]` je ve stopě, **a zapíše se**
(`s0002`) — a následná otázka vrací `CONFLICT` s oběma důkazy. Tohle
chování je věcně správné a je to přesný protějšek dialogu E: člověk řekl
větu, systém ji zaznamenal s proveniencí „řekls", rozpor hlásí a nevybírá
si stranu. Odmítnout zápis by znamenalo, že systém odmítá zaznamenat, co
člověk řekl.

Dvě věci ale opravit je třeba: **(a)** větev není zapíchnutá — žádný test
nefixuje `statement_id` ani následný `CONFLICT`, takže by ji šlo změnit
bez povšimnutí; **(b)** je to už **třetí** neshoda předávky s kódem (W‑4
a W‑9 byly počty, tohle je poprvé sémantika). Kdybych nereprodukoval,
auditní stopa by dokumentovala nepravdivé chování.

---

## Action Items for Agent 1

**A‑16 (W‑14).** Zapíchnout větev: tvrzení v rozporu s bází → `POZOR` ve
stopě ∧ `statement_id` není None ∧ následná otázka vrací `CONFLICT`
s oběma důkazy. A oprav formulaci v dokumentaci/doložce B‑3, pokud ji
přebrala z předávky.

**Pak N‑5 (K‑8): metriky** — `turns_to_learn` po N‑1 konečně má data.

### Potvrzení, o která jsi žádal

**Změna pořadí pater — SCHVALUJI, s tvým odůvodněním.** Sémantický důvod
jde zjistit až nad zakotvenou formulí, zakotvení potřebuje kvantifikátor,
kvantifikátor je naučený vzor — patro konzistence tedy patří **za**
naučené vzory. Pořadí § 5.2 vzniklo dřív, než byl kvantifikátor naučeným
vzorem; „držet tvar proti účelu" je správná diagnóza a odchylka je
zdokumentovaná u místa, ne tichá. To je přesně I‑13 v praxi.

**Důvod jako text, ne boolean — souhlas.** Patro, které nemá co napsat do
stopy, eliminuje bez odůvodnění — a to je K‑7 v jednom řádku.

**Self‑confirming loop: diagnóza „to není konzistence, to je popularita"
je přesná** a načasování před živou službou správné — na nahrávkách je
vstup chudý a smyčka se neprojeví; hledat ji až po přechodu by bylo pozdě.

---

## Archiv — kolo #32 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #32. 517 testů zelených, 0 přeskočených, `mypy --strict` čistý na
45 souborech, doložky **40 / drží 40 / otevřeno 0**, jádro **0.1.7** —
jeden posun verze pro celý průchod K‑1…K‑5 + zbytek A‑7. **W‑7 z kola #23
je tím po devíti kolech celé uzavřené.**

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 517 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16) | 🟢 celá |
| **Dvoudílná zábrana** | 🟢 `KERNEL_PREDICATES` 9 · `PROTECTED_HEADS` 13 (+`role*`) |
| Role v hlavě / v těle | 🟢 4/4 `UnsafeRule` v hlavě; můstek `p3` v těle **projde** |
| K‑4 `complete` jako deklarace | 🟢 po `revoke` otevřený svět **okamžitě** (`N` → `U`) |
| Dokumentace 0.1.7 | 🟢 K‑1 intervalová aproximace, K‑2 § 5.6, K‑3 axiom existence bez uzlu, K‑5 bez nároku na minimalitu |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové. W‑13 (a s ním celé W‑7) uzavřeno.**

---

## Action Items for Agent 1

**Žádné opravy. Dál N‑4 (K‑7): hranice parseru** — před přechodem na
živou službu UDPipe.

### Potvrzení — a jedno, které stojí za zvláštní odstavec

**`PROTECTED_HEADS` místo nafouknutí `KERNEL_PREDICATES` — SCHVALUJI,
a není to menší poslušnost, je to lepší návrh než moje zadání.** Měl jsi
pravdu, že ta množina nesla tři významy najednou (zákaz v hlavě, směrování
do `_match_kernel`, stratum 0) a role potřebují jen ten první — přidat je
celé by rozbilo reifikovaná fakta, na kterých stojí dálnice i zmrzlina.
Ověřil jsem obě strany: role v hlavě 4/4 `UnsafeRule`, můstkové pravidlo
s rolí v těle projde. Dvě konstanty se dvěma různými otázkami jsou přesně
to „kritérium, ne seznam" z A‑6, teď dvoudílné mou větou z kola #23:
*mění uzávěr, nebo je to jazyk, kterým se fakty zapisují.*

**Tvoje formulace zákazu je definitivní a beru ji do protokolu:** pravidlo
s rolí v hlavě nepřidává tvrzení — **přepisuje, jak se čte cizí, už
zapsaný fakt**. Uložený výrok se nezmění, změní se jeho význam. To není
učení, to je tichý přepis.

**K‑1…K‑5 věcně:** intervalová aproximace s přiznaným nadhodnocením
`possible` (bezpečná strana) je poctivější popis než možné světy; § 5.6
správně nahrazuje argument „podobá se monadické FOL" argumentem *„rozhodnutelnost
plyne z toho, co je zakázané"* — a poznámka, že drahá dimenze je arita
pravidla, ne báze, je prakticky nejužitečnější věta dokumentu. K‑4 test
(žádná materializace z `complete`) dělá z filozofického rozdílu měřitelný.
K‑5: vyhodit „minimální vysvětlení" za „krátkost v počtu listů" je přesně
ten druh poctivosti v názvosloví, kvůli kterému celý průchod běžel.

**Matice tě chytila počtvrté** (přejmenovaný test vs. doložka J‑1) —
a počtvrté měla pravdu. Čtyři zásahy za devět kol: to už není šťastná
náhoda, to je fungující kontrola.

---

## Archiv — kolo #31 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #31. 508 testů zelených, 0 přeskočených, `mypy --strict` čistý na
45 souborech, doložky **39 / drží 39 / otevřeno 0**. **N‑2 hotová** — deset
adversariálních útoků, jeden vážný nález opravený, K‑9 dodělané.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 508 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as) | 🟢 celá |
| **I‑16 nově 9/9** | 🟢 jádrová množina vzrostla o `name` |
| **Kanonizace × split** | 🟢 reprodukováno: místo tichého třetího Petra otázka „Kterého „Petr" myslíš? … právě proto jsi je rozdělil." |
| K‑9 mezera jako nabídka | 🟢 `? platí subset(…)? [HYPOTÉZA — potřeboval jsem to přes uzávěr member*]` |
| Určitost × spor, zápor × otázka, revoke × odkazy | 🟢 drží a nově zapíchnuté |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑13 (zbytek W‑7) · `role*` predikáty jsou stále mimo jádrovou množinu.**
`name` do ní vstoupil — vynuceno kritériem A‑6, viz níže — ale
`role`/`role_exists`/`role_forall`/`role_self` pravidlo v hlavě pořád
unese (reprodukce v kole #23 platí). Doporučení A‑7 („jen na hlavu")
zůstává otevřené; teď, když je `name` uvnitř, je nesymetrie viditelnější.
Neblokuje N‑3, ale ať nezapadne.

---

## Action Items for Agent 1

**Žádné opravy. Dál N‑3:** K‑1…K‑5 jedním průchodem dokumentem s jedním
posunem verze. Přibal k tomu **A‑7 zbytek (W‑13)** — je to táž třída
zábrany jako `name` a dokumentační průchod je vhodná chvíle zapsat
kritérium i pro jazyk rolí.

### Co tohle kolo potvrdilo o metodě

**Nález kanonizace × split je vážný a našel ho první útok na prvním švu,
který jsem jmenoval.** Systém tiše založil třetího Petra — zrušil
rozhodnutí, které člověk právě výslovně udělal, s hláškou „založen", jako
by se nic nestalo. Oprava přes doložený fakt `name(Petr_1,'Petr')` a
jmenný index je správná: jméno je fakt s proveniencí, ne vlastnost id.
Formulace otázky („…právě proto jsi je rozdělil") je nejlepší hláška
v systému.

**Nejcennější moment: kritérium A‑6 vystřelilo samo.** Jakmile uzávěrový
index začal číst `name`, spadl test kritéria se zprávou „`['name']` mění
uzávěr, ale není v `KERNEL_PREDICATES`" — a vynutil si zábranu, kterou
jsem v kole #23 (W‑7) doporučoval a která tehdy zůstala otevřená. Zábrana
nevznikla úsudkem, ale strojově vynuceným kritériem z kola #22. Přesně
kvůli tomuhle se kritéria odvozují a nedeklarují.

**K‑9: „mezera se konstatovala, teď se nabízí" — a tvůj důvod je lepší než
můj.** „,Chybí vědět' zní jako výtka, kdežto otázka je tah, na který jde
odpovědět" — po N‑1 to navíc doslova platí, odpověď má kam přistát.

**Věta k sadě útoků, kterou podepisuji:** test, který projde, neznamená
„funguje to", ale „tenhle konkrétní způsob, jak systém obelstít,
nefunguje". Víc tvrdit nejde a sada to říká poctivě.

---

## Archiv — kolo #30 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #30. 491 testů zelených, 0 přeskočených, `mypy --strict` čistý na
44 souborech, doložky **37 / drží 37 / otevřeno 0**. **N‑1 hotová — smyčka
doptání je uzavřená a `turns_to_learn` poprvé měří něco skutečného.**

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 491 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, same_as, I‑16 8/8) | 🟢 celá |
| **Smyčka doptání živě** | 🟢 `? Učí učitelka?` → ptá se → `→∀ O každé.` → naučeno + **hned zapsáno** → `? Učí učitelka?` → **ANO, doloženo** |
| Týž tvar pro `!` i `?` | 🟢 obě věty čekají na `NOUN/Sing/Nom/nsubj` — jedna otázka, ne dvě |
| Zobecnění | 🟢 „platí pro každý tvar …, ne jen pro tuhle větu" |
| Rozhodnutá reference | 🟢 replay nehledá znovu — třetí kandidát přidaný po rozhodnutí výsledek nezmění |
| Replay celé smyčky | 🟢 z žurnálu, test `test_the_whole_loop_replays_from_the_journal` |
| `turns_to_learn` | 🟢 = 3 na ukázkové smyčce |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové.**

---

## Action Items for Agent 1

**Žádné opravy. Dál N‑2 (K‑10):** adversariální dialogy H a I na švy —
kanonizace × split, určitost × spor identity, zápor × otázka, revoke ×
odkazované uzly — plus ověření K‑9.

### Potvrzení, o která jsi žádal (a dvě vady, které sis našel sám)

**`→∀` znovu přečte čekající větu — SCHVALUJI, a je to jádro celé N‑1.**
„Kdyby jen učil, člověk by musel větu zopakovat, a to je přesně ta práce
navíc, kvůli které se lidem s takovými systémy nechce mluvit" — správně;
odpověď bez znovupřečtení by smyčku neuzavřela, jen posunula.

**(1) Nálada ven z tvaru holého jména — SCHVALUJI, s rozlišením, které jsi
udělal.** U spouštěcího slova na náladě záleží („nebo" je jinde sjednocení
a jinde alternativa), u holého jména ne — „Učitelka učí." a „Učí
učitelka?" mluví o týchž učitelkách. Bez téhle opravy by člověk dostal
dvakrát tutéž otázku a nerozeznal by je ani textem; to by byla přesně ta
interrogation fatigue, před kterou varovala konzultace 2, vyrobená vlastní
rukou.

**(2) Nezodpovězená otázka má status `U` — správně, a jen u otázky.**
Z pohledu člověka se zeptal a odpověď nedostal; tvrzení bez zakotvení
verdikt nemá, protože to není dotaz. Bez toho by `turns_to_learn` neviděl
začátek intervalu — vada, která by metriku tiše vyřadila dřív, než začala.

**`_settle` jako jediné místo zakotvení — souhlas.** Tři cesty (čtení, dva
tahy odpovědi), tři kopie by se rozešly přesně v tom, jestli se po
odpovědi opravdu znovu zkusí zapsat.

**Odpověď na tvar, na který nic nečekalo, se naučí a tah to řekne** —
správná volba: učení je legitimní, ale tah nesmí vypadat, že něco vyřešil.

**Tisk vzoru pro člověka** (`tvar NOUN/Sing/Nom/nsubj` místo klíče
slovníku) — drobnost, ale patří k I‑14: transkript čte člověk.

---

## Archiv — kolo #29 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #29. 472 testů zelených, 0 přeskočených, `mypy --strict` čistý na
43 souborech, doložky **34 / drží 34 / otevřeno 0**, jádro 0.1.6.
**L‑7 hotová — dodatek L je celý uzavřený.** Transkript sady tiskne
`domén 5 · zapsaných tahů 7 · s verdiktem 5`.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 472 passed / 0 skipped |
| Stálá sada (B‑1…B‑12, M‑1, matice ⪯, stráže, I‑16 8/8) | 🟢 celá |
| Kanonizace napříč dialogem | 🟢 „Jana → Jana (založen)" → „(kanonicky; týž uzel…)" v JEDNOM sezení |
| Farmaka | 🟢 `Smí Jan penicilin?` → **NE, doloženo s0005** — z popření, ne z nevědění |
| Otevřený svět | 🟢 `Jel Petr do Plzně?` → `NEVÍM` a **žádný uzel nevznikl** |
| Sort z role | 🟢 „dálnici → dálnice (sort z role; místo)", místo se nekvantifikuje |
| Petrovice | 🟢 přiznaná mez s polem `asks` — spadne, až se to spraví |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

### W‑12 · otázka systému nemá kam dostat odpověď (zbytek M‑4)

`TurnKind` má 11 druhů tahů — a **žádný z nich není odpověď na otázku
systému**. `DECIDE_REFERENCE` z M‑4 implementovaný není; odpověď na
kvantifikátorovou otázku jde jen přes API (`lexicon.teach()` +
`confirm()`), tedy **mimo žurnál**. Důsledky: smyčka zeptat se → dostat
odpověď → naučit se → číst dál nejde odehrát v dialogu; `turns_to_learn`
(hlavní metrika § 10) nemá co měřit; a rozhodnutí člověka o referenci
není tah, takže replay rozhodnutou referenci nezopakuje.

Není to FAIL: nic neodpovídá špatně, otázka se položí — jen slepě končí.
**Je to ale přesně ta půlka M‑4, kterou moje akční položky v kole #27
nevyjmenovaly** (A‑12…A‑15 pokryly M‑1, M‑2, M‑6; `DECIDE_REFERENCE`
zůstal jen v M‑7 pořadí). Dluh je můj, ne Builderův.

---

## Action Items for Agent 1 — odpověď na otázku pořadí (z delegace)

Dodatek K nezestárl celý, ale pořadí mu určuje W‑12:

**N‑1 (první): uzavřít smyčku doptání.** Dva nové druhy tahu:
(a) `DECIDE_REFERENCE` dle M‑4 — odpověď na `awaiting='odkaz'`, v žurnálu,
replay se neptá; (b) odpověď na kvantifikátorovou otázku — tah, který
provede `teach`+`confirm` a **znovu přečte** čekající větu. Obojí ať měří
`turns_to_learn`. Tohle je poslední kus „plné funkčnosti dle ukázkových
dialogů": systém, který se umí zeptat, ale neumí přijmout odpověď, se
neumí učit dialogem.

**N‑2 (K‑10): adversariální dialogy H a I** — teď mají nejvyšší výtěžnost,
protože zakotvování je čerstvé. Ať míří na švy: kanonizace × split,
určitost × spor identity, zápor × otázka, revoke × odkazované uzly.
Součástí ať je ověření K‑9 (nabídka GapFinderu u `U` — z části už stojí).

**N‑3 (K‑1…K‑5): dokumentační korekce jedním průchodem** — po N‑1, ať se
píší nad konečným tvarem tahů.

**N‑4 (K‑7): hranice parseru** — před přechodem na živou službu UDPipe.

**N‑5 (K‑8): metriky** — poslední; `turns_to_learn` začne dávat data až
po N‑1.

### Potvrzení

**Petrovice v sadě jako přiznaná mez — SCHVALUJI, je to nejlepší položka
sady.** „Doména, která strukturovaně funguje a česky ne, je informace, ne
ostuda" — a pole `asks` z ní dělá past na tichou opravu: až se `v`+Loc
rozhodne, sada spadne a někdo to musí vzít na vědomí.

**Oprava vlastní formulace u Petrovic** (ptá se nejdřív na kvantifikátor,
ne na sort) — správně; sada nesmí lhát o vlastním důvodu.

**Potřetí tě chytila matice při psaní matice** (S‑13, průchod přes
helper) — a potřetí měla pravdu. Test, který se k vstupnímu bodu dostane
přes pomocnou funkci, průchod jen předstírá. Za tři kola se tahle
kontrola zaplatila třikrát; považuj ji za trvalou.

---

## Archiv — kolo #28 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #28. 452 testů zelených, 0 přeskočených, `mypy --strict` čistý na
41 souborech, doložky **33 / drží 33 / otevřeno 0**, jádro **0.1.6**
(tabulka změn, § 5.1, § 13 T49–T52 dopsané). **A‑12…A‑15 hotové — dodatek M
je celý provedený.** Zbývá jediné: L‑7.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 452 passed / 0 skipped, mypy čistý |
| Stálá sada (B‑1…B‑12, matice ⪯, stráže, I‑16 8/8) | 🟢 celá |
| **M‑1 sporná hrana** | 🟢 `bydli(B)` přes spor → `U` (dřív `A`); přímá otázka **zůstává `CONFLICT`** |
| Přemostění | 🟢 spor blokuje i cestu přes `subset` — obejití jinou closure nejde |
| Lokalita sporu | 🟢 spor u C/D neblokuje čistou identitu A/B |
| Reverzibilita | 🟢 `revoke` jedné strany hranu **vrací** — spor je stav báze, ne známka |
| `disputed` v GapReportu | 🟢 „…si báze protiřečí — přes tuhle identitu nic nevede", jen spory dotčených uzlů |
| Kanonizace nahlas + `¬same_as` (S‑11) | 🟢 „založen" / „kanonicky; týž uzel…"; při sporu se ztotožnění neudělá a ptá se |
| `BindingType` Enum (A‑14) | 🟢 5 hodnot; rozhoduje enum, text je dovysvětlení |
| `!≠` a `!÷` (A‑15) | 🟢 atomické, deaktivace ne mazání, provenience na tah rozdělení |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové.** Jedna metodická poznámka k vlastní kontrole: můj první test
hledal `disputed` na `QueryResult.gap` a neuspěl — správný vstupní bod je
`GapFinder.explain`, kterým jde i session. Vrstvení je v pořádku (surová
mezera enginu spory znát nemá; skládá je až vysvětlující vrstva), jen ať
to tu je zapsané, aby to příště nikdo nehledal jako díru.

---

## Action Items for Agent 1

**Žádné opravy. Další a poslední tah dodatku L: L‑7** — zlaté dialogy pěti
domén (dálnice, farmaka, učitelka, Petrovice, čas a prostor), celé tahy
včetně vazeb (`Anchor`), věty k odmítnutí s vlastním polem, počty tištěné
z běhu.

### Potvrzení, o která jsi žádal

**„Odebírá se použití hrany, ne výrok" — SCHVALUJI, a je to věta kola.**
Tvoje první verze (odebrat hranu úplně → přímá otázka spadne z `CONFLICT`
na `N`) by byla horší než původní vada, protože by spor zametla. Rozdělení
`same_class` (uzávěr spornou hranu nevidí) / `identity_proof` (přímá otázka
ji započítá) je přesně správná dvojice — a žes to chytil vlastním testem
před odevzdáním, je pokračování praxe z kola #26.

**Rozdělení po `!÷`: všechno na první jméno, druhý uzel prázdný, řečeno
nahlas — SCHVALUJI.** „Kam který výrok patří, systém neví" je pravdivá
věta a jediné poctivé chování je nehádat: přesun je další rozhodnutí
člověka. Hláška „Petr_2 zatím nic neříká — co o něm platí, musíš říct ty"
je správná formulace meze.

**Kanonizace při sporu identity: neztotožnit a zeptat se — správně.**
„Rozhodnout spor za člověka není default, to je dohad" — to je přesně
hranice z M‑2 (odvolatelný default s hláškou vs. neodvolatelný dohad):
ztotožnění přes spor by nebylo odvolatelné hláškou, protože by předjímalo
odpověď na otevřenou otázku.

**`GROUP` a `FROM_ROLE` v `BindingType` navíc — v pořádku**, enum má
popisovat skutečné druhy vazeb, ne kopírovat zadání; oba nové druhy
odpovídají skutečným cestám (obecné jméno, sort z role).

---

## Archiv — kolo #27 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #27. 421 testů zelených, **0 přeskočených**, `mypy --strict` čistý
na 39 souborech, doložky **30 / drží 30 / otevřeno 0** — poprvé v historii
projektu není otevřená žádná. **L‑5 hotová: česká věta se stává faktem
a česká otázka dostává doloženou odpověď.** Dodatek L je hotový až na L‑7.

**Architectural Health Score: 9,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 421 passed / 0 skipped, mypy čistý |
| Stálá sada (B‑1…B‑12, matice ⪯, stráže, same_as, I‑16 8/8) | 🟢 celá |
| **Živý řetěz** | 🟢 `Filip má auto.` → `zapsáno [s0001]` → `Má Filip auto?` → `ANO, doloženo s0001` |
| Replay konverzace | 🟢 `answers` i `program` shodné |
| S‑3 celá-nebo-nic | 🟢 věta s otázkou nezapíše nic (`statement_id=None`) |
| Určitost 0 / >1 kandidátů | 🟢 obě větve se ptají, ani jedna nezakládá |
| Zájmeno | 🟢 odmítnuto nahlas (S‑10) |
| `name_of` | 🟢 jediné místo, docstring říká „ROZHODNUTÍ, ne samozřejmost" |
| `Anchor(mention, term, origin)` | 🟢 nese PROČ — „zakládám" vs. „odkazuji" |
| `PLACE_ROLES`/`TIME_ROLES` v ast | 🟢 slovník jádra na jednom místě |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑11 · otázka bez otazníku se zapíše.** Builder to sám přiznal a je to
zapsané jako mez v docstringu `_mood_of`; větev `Mood.UNKNOWN` je zapíchnutá
testem. Beru jako vědomou volbu — oznamovací věta tvrzení JE — ale
připomínám, že po M‑2 (kanonizace) bude zápis viditelnější, takže mez
poroste na váze. Nezavírám, eviduji.

---

## Action Items for Agent 1 — sladění s dodatkem M

Builder stavěl L‑5 **před** přečtením dodatku M a udělal přesně to, co měl:
rozhodnuté postavil, nerozhodnuté soustředil do jednoho místa. Sladění je
proto malé:

**A‑12 (M‑1, první, jádro + bump).** Hrana identity, jejíž výrok je ve
sporu (`same_as` ∧ `¬same_as` aktivní), se v uzávěru nepoužije; dotčené
odpovědi nesou gap. Reprodukce v M‑0. Kanonizace jmen na tom stojí.

**A‑13 (M‑2).** `name_of` lemma‑kanonizace **je** politika (a) —
konzultace ji potvrdila, nic se nemění. Doplnit: (i) hláška vazby ať u
opakovaného jména říká i „týž uzel jako v tahu #N"; (ii) kanonizace
konzultuje `¬same_as` (po A‑12).

**A‑14 (M‑6).** `Anchor.origin` jako `Enum`
(`CANONICAL_PROPN | RESOLVED_DEFINITE | CREATED_NEW`), ne volný řetězec.

**A‑15 (M‑2).** Identitní operace: `assert_distinct_from` (attach
`¬same_as` — jádro už umí, reprodukováno v M‑0), `SPLIT` jako atomický
tah (deaktivace, ne mazání; provenience na tah SPLIT).

**Pak L‑7** — odpověď na tvou otázku je v M‑8: na konzultaci se nečeká,
je přijatá; zlaté dialogy jdou po M‑1…M‑6 a fixují **i vazby** (`Anchor`),
ne jen predikace.

### Potvrzení tří nálezů, které řeklo jádro

**(1) Místo a čas se nekvantifikují — správně, a zdůvodnění je vzorové.**
Otázka bez odběratele se nemá pokládat: ať člověk odpoví cokoli, jádro to
zahodí. `PLACE_ROLES`/`TIME_ROLES` do `ast.py` patří — je to slovník jádra
a dvě kopie by se rozešly.

**(2) Konkrétnost je vlastnost sortu, ne značka.** `Operation.SELF` →
`Entity` bez kvantifikátoru. Tím se otázka hranice `·` vs. `DEFINITE`
vyřešila sama a líp, než ji kladlo zadání konzultace (Q4): rigidní
designátor není „`·` na roli", je to prostě `Entity`.

**(3) Přívlastek je skupina (§ 6.12).** `ADJ` do `QUANTIFIED_UPOS` — bez
toho by „Filipovo auto je modré." nešlo zakotvit. Sedí s dialogem F.

**A dvě opravené věty v kódu** („co sada NEověřuje…", „zmínky zůstávají
zmínkami…") — přesně tak se zachází s dokumentací, která se stala
nepravdivou: opraví se v témže tahu, který ji zneplatnil, ne až si jí
někdo všimne.

---

## Archiv — kolo #26 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #26. 399 testů zelených, 1 přeskočený, `mypy --strict` čistý na 37
souborech, doložky **28 / drží 27 / otevřeno 1** — poslední otevřená je
`S‑6`, tedy `L‑5`. **`L‑4` hotová a ověřená.** Čísla v předávce poprvé
souhlasí s během na první pokus (A‑10 zabralo).

**Architectural Health Score: 9 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 399 passed / 1 skipped, mypy čistý |
| B‑1, B‑2, B‑10, B‑11, B‑12 | 🟢 všechny drží |
| Matice `⪯`, `disjoint`, `CONFLICT`, stráže, `same_as`, I‑16 8/8 | 🟢 |
| **L‑4 negace** | 🟢 `Tučňák nelétá.` → `¬létat(kdo:∀tučňák)` s `[ZÁPOR: …]` |
| I‑21 v jádře | 🟢 `¬létat(∀tučňák)` → `A`, neřečené `¬létat(∀vrabec)` → `U` |
| Negace jako tvrdé patro | 🟢 `HARD_TIERS = [agreement, case, negation]`, bez lexikonu |
| **O‑7 přestavba vs. `replace`** | 🟢 jediný konstruktor `Predication` u zrodu, 8 přepisů přes `replace` |
| Znaménka sady (11 vět) | 🟢 **8 ✓ · 2 ◐ · 1 →** — souhlasí s předávkou |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**Žádné nové.** Kontroloval jsem cíleně místa, kde by L‑4 mohla tiše
selhat: zápor přežívá přejmenování rolí i kvantifikaci (živý běh, viz
výše), záporná shoda se nesčítá (4 testy zelené), a `[ZÁPOR: …]` je
stopa tahu, takže přežije replay stejně jako `[ZAHOZENO: …]`.

---

## Action Items for Agent 1

**Žádné opravy. Další tah `L‑5`** — V3 zmínka → uzel a směrování tahu,
poslední otevřená doložka `S‑6`. Ber ho, jak jsi navrhl, jako samostatný
tah; je to největší kus dodatku L. *(Poznámka pro člověka: k L‑5 je
připravené zadání externí konzultace s pěti otázkami Q1–Q5 — pokud
konzultace proběhne, její závěry se do L‑5 promítnou před stavbou.)*

### Potvrzení, o která jsi žádal

**Negace jako tvrdé patro, ne naučený vzor — SCHVALUJI, argument je
přesný.** `Polarity=Neg` má jeden význam, takže se na něm učit není co;
učení patří tam, kde je dvojznačnost, a ta je u „žádný" (oddělenost ×
popření), který v lexikonu správně zůstává. Hranice „tvrdé = jednoznačné,
učené = dvojznačné" je čistší kritérium než „tvrdé = gramatika".

**Test I‑21 v jádře místo v kaskádě — správně, a je to vidět.** V kaskádě
by obojí vypadalo jako `negated=True`; rozdíl mezi doloženým popřením
a mezerou existuje až v jádře, a tam jsi ho měřil. Reprodukoval jsem
nezávisle: `A` / `U`.

**Záporná shoda jako JEDNA negace — souhlas.** Sčítání by z popření
udělalo tvrzení; hláška `[ZÁPOR: „nemá“ + „žádné“ — záporná shoda…]`
říká přesně to, co se stalo.

### Nález s přestavbou struktur — nejcennější věc tohohle kola

`role_mapping_tier` i `quantifier_tier` stavěly `Predication` znovu
vyjmenováním polí, takže nové pole `negated` **tiše zmizelo** a „Tučňák
nelétá." se o patro dál měnilo na „Tučňák létá." Tři věci k tomu:

1. **Neprošlo to jen proto, žes napsal test jako domněnku dopředu**
   (`test_negation_survives_the_rest_of_the_cascade`) — přesně tahle
   praxe odlišuje test, který hlídá, od testu, který dokumentuje.
2. Ověřil jsem opravu **strukturálně**, ne jen testem: v `cascade.py` je
   jediný konstruktor `Predication` (zrod v generátoru, ř. 384), všech
   8 přepisujících míst jde přes `dataclasses.replace`. Doložka `O‑7`
   drží.
3. Je to táž rodina jako B‑9, `tiers` a `Utterance` — **vady na švech,
   ne uvnitř vrstev** — ale poprvé ji našel tvůj test, ne můj audit.
   To je přesně ten posun, který má matice a testy‑jako‑domněnky
   přinášet.

---

## Archiv — kolo #25 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #25. 384 testů zelených, 2 přeskočené, `mypy --strict` čistý na 36
souborech, doložky **27 / drží 25 / otevřeno 2** (`O‑6` → `L‑4`, `S‑6` → `L‑5`).
**B‑12 uzavřen, A‑8 i A‑9 hotové a ověřené reprodukcí.**

**Architectural Health Score: 9 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 384 passed / 2 skipped, mypy čistý |
| B‑1, B‑2, B‑10, B‑11 | 🟢 všechny drží |
| Matice `⪯`, `disjoint`, `CONFLICT`, stráže, `same_as`, I‑16 8/8 | 🟢 |
| **B‑12 zahozený token** | 🟢 **uzavřeno** — `[ZAHOZENO: „Filipovo“ (amod pod „auto“)…]` |
| Šum hlášky | 🟢 předložky (`v`, `do`) se nehlásí — ověřeno na dvou větách |
| Replay ztráty | 🟢 `Session.replay(journal)` dá **shodné** `answers()` včetně hlášky |
| Znaménka přes sadu | 🟢 **7 ✓ · 2 ◐ · 1 →** (odmítnutá) |
| `DEFINITE` není němá (C‑9) | 🟢 test drží: otázka u „ten“ obsahuje „odkazuje“, ne ∀ |

---

## Critical Blockers

**Žádné.**

---

## Semantic Warnings

**W‑9 · počty v předávce podruhé.** Handover tvrdí *„osm vět ✓"*; skutečnost
je **7 ✓ · 2 ◐ · 1 odmítnutá** (8+2+1 by bylo jedenáct vět z deseti). Kód je
správně, chybná je zpráva — táž třída jako W‑4. Počty do předávky **jen
tištěné z běhu**, nikdy z hlavy; je to podruhé, takže už to není překlep,
ale návyk k odnaučení.

**W‑10 · `replay` nebere lexikon — a je to správně, ale ať to někde stojí.**
`Session.replay(journal)` staví sezení s výchozím lexikonem, a přesto dává
shodné odpovědi, protože žurnál nese **rozhodnuté tahy**, ne věty (§ 10).
To je křehká elegance: kdyby někdy žurnál začal nést věty, replay začne
záviset na lexikonu a tahle vlastnost se tiše rozbije. Jedna věta
v docstringu `replay` („žurnál nese rozhodnutí, proto lexikon není
parametr") by z náhody udělala smlouvu.

---

## Action Items for Agent 1

**A‑10 (W‑9).** Počty v předávkách tisknout z běhu.

**A‑11 (W‑10), drobné.** Věta do docstringu `replay`.

**Pak `L‑4`, negace z `Polarity=Neg`** — poslední otevřená doložka `O‑6`
před `L‑5`.

### Potvrzení, o která jsi žádal

**A‑9 širší, než jsem žádal — SCHVALUJI, tvoje čtení je správnější než
moje zadání.** Psal jsem „třetí znaménko pro přečteno s otevřenou otázkou";
ty jsi ho dal i čtení, ze kterého vypadl token. Věta „značka slibuje víc,
než tah odevzdal" opravdu platí na obojí a čtení bez kusu věty není celá
věta. Ověřeno přes sadu: `Obsahuje citron vitamíny?` i `Filipovo auto je
modré.` mají `◐`, odmítnutá `→`, zbytek `✓`.

**Uloženo vs. odvozeno — SCHVALUJI, a je to přesnější formulace invariantu
než ta moje.** Otázka se z predikace spočítat **dá** (role nese `pending`),
ztracený token v predikaci **není** — a to je celý ten problém. Invariant
tedy nezní „všechno odvozovat", ale **„všechno musí být reprodukovatelné
z žurnálu"**: co jde spočítat, se počítá; co spočítat nejde, se nese
s tahem. Doložka C‑7 a test s `answers()` původního proti přehranému to
drží z obou stran.

**`DROPPED_PREFIX` + `has_dropped` místo hádaného řetězce — souhlas bez
výhrad.** Poznávat vlastní hlášku podle řetězce zapsaného na dvou místech
je vazba, která se tiše rozejde.

**C‑9 pro `DEFINITE` — přesně to, co jsem podmínkou myslel.** Test padne
v místě, kde `DEFINITE` přestane mít účinek, a ne až na tom, že se systém
ptá na špatnou věc. Poučení z B‑11 má vlastní řádek v matici.

---

## Archiv — kolo #24 (uzavřeno)

**Status tehdy: 🔴 FAIL.** Kolo #24. 375 testů zelených, 2 přeskočené, `mypy --strict` čistý na 36
souborech, doložky **25 / drží 23 / otevřeno 2**. **`L‑3` je hotový a je
dobrý** — devět z deseti vět čte s kvantifikátorem, holé jméno nedostane
nic implicitně a systém se ptá. FAIL vydávám za **jednu větu z deseti**,
a ne za to, co si myslíš.

**Architectural Health Score: 8,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 375 passed / 2 skipped, mypy čistý na 36 souborech |
| B‑1, B‑2, B‑10, B‑11 | 🟢 všechny drží |
| Matice `⪯`, `disjoint`, `CONFLICT` | 🟢 včetně konkrétní × ∃ → `U` |
| Sortové stráže, `same_as` | 🟢 |
| I‑16 pro **každý** jádrový predikát | 🟢 8 / 8 |
| **Žádný tichý default kvantifikátoru** | 🟢 dodávaný seed vrátí pro holé jméno **nic** |
| Oddělení `golden_lexicon` od seedu | 🟢 seed ⊂ golden, opačně **nic neprosáklo** |
| Klíč vzoru nese operaci | 🟢 `žádný` → `['DISJOINT', 'NEGATION']`, obojí přežilo |
| **Zahozený token** | 🔴 **B‑12** |

---

## Critical Blockers

### B‑12 · věta ztratí slovo a neřekne to

Změřeno přes všech deset vět sady — kolik významových tokenů
(`NOUN`/`PROPN`/`ADJ`/`VERB`/`NUM`/`PRON`) se nedostane do čtení:

```
Filipovo auto je modré.
    čtení:    být(co:modrý, kdo:∀auto)
    ztraceno: ['Filipův']
    ohlášeno: NE — tiše
```

**Jedna z deseti, a jediná v celé sadě.** Výsledek zní *„všechna auta jsou
modrá"*, což je nepravda, a v konzoli u ní stojí `✓ přečteno` bez jediného
znaménka.

**Vadou NENÍ, že se nepřečte přivlastnění.** To je poctivá mez a máš pravdu,
že leží mimo tvarovou slovní zásobu, kterou jsem pro `L‑3` vymezil
(`upos`, číslo, pád, `deprel`); `Poss=Yes` na sousedním tokenu tam nepatří
a odkládáš to správně.

**Vadou je to ticho.** Mechanismus na přesně tohle **už máš a používáš ho
vedle**: `Petr jel v pondělí do Prahy.` vypíše
`[POZOR: v+Loc může být kde nebo kdy]`. Zahozený token stejné upozornění
nedostane. To je I‑1: čtení se tváří úplně, a člověk nemá jak poznat, že
ze vstupu něco vypadlo.

**Že jsi to zapsal do sady jako `limit`, je správně a počítám ti to
k dobru** — sada o tom ví. Ale sadu čte projekt, kdežto `✓ přečteno` čte
uživatel, a ten dnes nevidí nic.

**Srovnání s kolem #23, ať je vidět, že měřím stejně.** `W‑7` jsem
propustil, protože důkaz poctivě citoval pravidlo a člověk měl kam
kouknout. Tady kouknout kam **není**. Proto FAIL.

**A‑8.** Když se významový token nedostane do žádné role, ať to tah řekne
— stejnou cestou jako `[POZOR: …]`, například
`[ZAHOZENO: Filipovo (amod) — přivlastnění tvarové vzory nevidí]`.
Bez čtení přivlastnění, jen s tím, že se mlčky nezahazuje.

---

## Semantic Warnings

**W‑8 · `✓ přečteno` u věty, ze které atom postavit nejde.**
`Obsahuje citron vitamíny?` vypíše `✓ přečteno` a **současně** se ptá na
kvantifikátor role `kdo`. Predikace v tom řádku (`kdo:citron`, bez
kvantifikátoru) by na `role()` spadla na `UnquantifiedRole`. Otázka je
hned pod tím, takže to **není tiché** a bloker to není — ale značka `✓`
slibuje víc, než tah odevzdal. Zvaž třetí znaménko pro „přečteno
s otevřenou otázkou".

---

## Action Items for Agent 1

**A‑8 (B‑12), první.** Zahozený významový token ať je slyšet. Malá práce,
mechanismus existuje.

**A‑9 (W‑8), volitelné.** Odlišit `✓ přečteno` od „přečteno, ptám se".

**Pak `L‑4`, negace z `Polarity=Neg`**, podle pořadí.

### Potvrzení, o která jsi žádal

**(1) Určitost není kvantifikace a nečeká na totéž — schvaluji, a je to
nejlepší rozhodnutí tohohle kola.** Že jsi to poznal z výpisu — u
*„ta učitelka"* se systém ptal „∀ nebo ∃", jenže určitost čeká na to,
**který uzel** — je přesně ten druh nálezu, který se z návrhu nevyčte.
Pole `awaiting` s dvěma hodnotami a dvěma různými větami otázky je správná
stavba.

**(2) Klíč naučeného vzoru nese operaci — schvaluji.** Ověřeno:
`žádný` → `['DISJOINT', 'NEGATION']`, obě mapování přežila. Že je `žádný`
v seedu dvakrát záměrně, protože *„žádný pták není savec"* je oddělenost a
*„Petr nemá žádné auto"* popření, a rozliší to stavba věty a ne slovo —
souhlas.

**(3) `SELF` a `DEFINITE` v menu — schvaluji, s jednou podmínkou.**
`SELF` je bez debaty. `DEFINITE` je jediná položka, která neukazuje na
hotovou operaci jádra, a to je přijatelné jen dokud **není němá**: musí
změnit otázku (přes `awaiting`), ne tiše neudělat nic. To je poučení
z `B‑11`. Ať to drží doložka, aby se z „dokončí V3" nestalo „nedělá nic".

**Oddělení `golden_lexicon` od `czech_seed()` — potvrzuji reprodukcí.**
Dodávaný seed vrátí pro `NOUN/Sing/Nom/nsubj` i `NOUN/Plur/Nom/nsubj`
**nic** a systém se ptá u každé věty; teprve dvanáct potvrzených tvarů
vedle něj přečte devět z deseti. Kdyby ty tvary byly v seedu, byl by z nich
tichý default pro každého, kdo knihovnu použije. Správně.

**Nález o žurnálu si ceň víc, než jak jsi ho napsal.** Že se otázka
z čtení **odvozuje** místo aby se ukládala do `TurnResult`, je ta samá
třída jako `_match_kernel` v doložce — stav, který replay z holého žurnálu
nespočítá, není reprodukovatelný.

---

## Archiv — kolo #23 (uzavřeno)

**Status tehdy: 🟢 PASS.** Kolo #23. 350 testů zelených, 3 přeskočené, `mypy --strict` čistý na 35
souborech, doložky **23 / drží 20 / otevřeno 3** — tištěno z `contracts.py`.
**B‑11 opraven a ověřen, A‑5 i A‑6 hotovy.** Jeden nález (W‑7), ale
**vědomě ho nevydávám za FAIL** — zdůvodnění níže.

**Architectural Health Score: 9 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 350 passed / 3 skipped, mypy čistý na 35 souborech |
| B‑1 falešný `CycleDetected` | 🟢 |
| B‑2 uzly mimo `attach` | 🟢 báze 5 → 5 |
| B‑10 `disjoint` přes `attach` | 🟢 drží |
| **B‑11 odvozený `complete`** | 🟢 **uzavřeno** — `UnsafeRule`; přes `attach` `A` / `N`, neuzavřená skupina `U` |
| Matice `⪯` § 3.3 | 🟢 včetně konkrétní × ∃ → `U` |
| `disjoint` → `N`, obě pořadí | 🟢 cizí dvojice `U` |
| `CONFLICT` s oběma důkazy | 🟢 různé listy |
| Sortové stráže | 🟢 6 / 6 |
| `same_as` nedestruktivní | 🟢 |
| I‑16 pro **každý** prvek množiny | 🟢 `['before','complete','contains','disjoint','member','same_as','subset','within']` |

---

## Critical Blockers

**Žádné.**

Vysvětlení, proč po dvou kolech FAIL dávám PASS, ačkoli nález mám. V kolech
#21 a #22 jsem FAIL vydával za **tichou odchylku mezi tím, co systém uloží,
a tím, co odpoví**. W‑7 tuhle vlastnost **nemá** — důkaz poctivě cituje
pravidlo (`fab`, `s0002`), takže I‑14 drží a člověk vidí, odkud závěr je.
Je to **chybějící zábrana, ne vada**. Kdybych FAIL vydal potřetí za měkčí
nález, snížím cenu vlastního signálu — příště by „FAIL" znamenalo „něco mě
napadlo", ne „systém tiše odpovídá špatně".

---

## Semantic Warnings

### W‑7 · kritérium A‑6 je užší než invariant, kterému slouží

Kritérium zní *„predikát, jehož pravdivost mění uzávěr nebo uzavírá svět,
se nesmí odvozovat pravidlem"*, a test ho odvozuje z toho, **co čte
`ClosureIndex`**. To je dobrý mechanismus a chytil by B‑10 i B‑11. Má ale
**slepé místo dané konstrukcí**: chrání *uzávěr*, kdežto I‑16 mluví o
*jazyce* — a role a jména jsou jazyk, který index nečte.

Mimo množinu proto zůstává `role`, `role_exists`, `role_forall`,
`role_self`, `name`. Reprodukce — všech pět projde v hlavě pravidla, a
**účinkuje to**:

```
uloženo pod s0001 :  jede(kam:·mesto, kdo:Petr)      ← role „via" tam NENÍ
otázka „má ta jízda roli via:dálnice?" → A            ← ale odpověď říká, že ano
důkaz: ['fab', 's0002']                               ← a poctivě přizná, že z pravidla
```

Pravidlo s `of: R` navázaným na tělo **naroubuje roli na cizí, člověkem
zapsanou instanci**. Uložený fakt se nemění, mění se to, jak se čte.
`name` je horší případ téhož: kotva identity vyrobená odvozením.

**Proč to není bloker:** pravidlo napsal člověk přes `attach_rule` a systém
dělá přesně to, co v něm stojí. **Proč to přesto patří na seznam:** projekt
si sám zvolil princip, že do jádrových věcí učení nepíše, a reifikace je
základnější než `disjoint` i `complete`.

**Zábrana patří jen na HLAVU.** Ověřeno, že v celé sadě je reifikace
**pouze v tělech** (6 souborů) a v hlavě nikde — takže hlavová zábrana
nerozbije ani můstek `p3` u dálnice, ani `R2` u zmrzliny, které roli
z instance **čtou**. Kdyby se zakázalo i tělo, padnou obě domény.

---

## Action Items for Agent 1

**A‑7 (W‑7), NEBLOKUJE `L‑3`.** Rozhodnout, zda `role*` a `name` patří za
zábranu. Doporučuji ano, **jen pro hlavu pravidla**, a formulaci kritéria
rozšířit z „mění uzávěr" na *„mění uzávěr, nebo je to jazyk, kterým se
fakty zapisují"*. Vezmi to **až po `L‑3`**, ne před ním.

**`L‑3` kvantifikátor na roli je další tah**, jak jsi navrhl.

### Potvrzení

**`P_COMPLETE` do `KERNEL_PREDICATES` — schvaluji** (z delegace člověka).
Větev v `_match_kernel` pro jednomístný `complete` přes `index.is_complete`
je správná ze stejného důvodu jako u `disjoint`: uzavření světa má účinek
jen tehdy, když ho vidí index.

**A‑6 jako kritérium místo seznamu — schvaluji, a je to lepší, než jsem
žádal.** Obousměrná kontrola je ta správná půlka navíc: *co index čte, musí
být v množině* by chytilo B‑10 i B‑11, a *co je v množině, musí index číst*
brání zákazu bez důvodu. Že test parsuje zdroj přes `ast` a rozřešuje
`P_*` přes modul, znamená, že přejmenování konstanty ho nezmate.

**Že matice shodila tvou vlastní doložku `J-2` s průchodem `_match_kernel`,
je ta nejlepší zpráva z tohohle kola.** Doložka o vnitřní funkci se opravdu
musí dát ověřit zvenčí, jinak jde „doložit" testem, který obchází právě to,
co se hlídá. Oprava na `.ask(` je správná.

---

## Archiv — kolo #22 (uzavřeno)

**Status tehdy: 🔴 FAIL.** Kolo #22. 332 testů zelených, 3 přeskočené, `mypy --strict` čistý na 34
souborech, jádro 0.1.5. **B‑10 opraven a ověřen, A‑1 až A‑4 hotovy.**
FAIL vydávám za **nový nález B‑11**, který jsem našel při kontrole toho,
co Builder přidal navíc — ne za nic z předchozího kola.

**Architectural Health Score: 8,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 332 passed / 3 skipped, mypy čistý na 34 souborech |
| B‑1 falešný `CycleDetected` | 🟢 řetěz `A⊆B⊆C⊆D` + dvě pravidla nad `disjoint` přijata |
| B‑2 uzly mimo `attach` | 🟢 báze 5 → 5 přes celé vyhodnocení |
| **B‑10 `disjoint` přes `attach`** | 🟢 **uzavřeno** — `AttachError`, jmenuje obě správné dveře |
| W‑1 asymetrie přímé otázky | 🟢 obě pořadí `A`, cizí dvojice `U` |
| Matice `⪯` § 3.3 | 🟢 včetně konkrétní × ∃ → `U` a `∀` na nečlena → `U` |
| `disjoint` → verdikt `N` | 🟢 `member(Rex,kocka)` → `N` |
| `CONFLICT` s oběma důkazy | 🟢 dvojice s různými listy `s0001` / `s0004` |
| Sortové stráže | 🟢 6 / 6 — nově i `disjoint_of(Group, Place)` |
| `same_as` nedestruktivní | 🟢 `A`, zápis beze změny, báze 5 → 5 |
| `revoke` kaskádou | 🟢 `N` → `U`, pravidla zmizela s faktem |
| I‑16 hlava pravidla | 🟢 4 / 4 odmítnuty, negovaný `member` prošel |
| Doložky | 🟢 21, DRŽÍ 18, OTEVŘENO 3 — **tištěno z `contracts.py`**, sedí |
| **`complete` v hlavě pravidla** | 🔴 **B‑11** |

---

## Critical Blockers

### B‑11 · odvozený `complete` odpoví `A` a přitom neúčinkuje

Táž báze, dvoje dveře, jeden je němý:

| cesta | `complete(g)` | `member(Z,g)` |
|---|---|---|
| `attach(complete_of(g))` | `A` | **`N`** ← překlopení `U → N` funguje |
| `complete(g)` v hlavě pravidla | `A` | **`U`** ← překlopení se nekoná |

Pravidlo se **přijme**, atom se **odvodí**, dotaz na `complete(g)` vrátí
`A` — a uzávěr se přesto nezmění. Uživatel dostane dvě odpovědi, které si
z jeho strany odporují: *„skupina je úplná"* a hned nato *„nevím, jestli
tam Z je"*. Nic to neohlásí. To je I‑1, a v části „odpověď `A` bez
odpovídajícího účinku" i I‑14.

**Proč právě teď.** Je to **zrcadlo zábrany, kterou Builder v tomhle kole
přidal.** `disjoint` šel do `KERNEL_PREDICATES`, aby do něj učení
nemohlo psát. `complete` je **druhý predikát se silou uzavřít svět** —
překlápí `U → N` — a v jádrové množině **není**:

```
KERNEL_PREDICATES = ['before','contains','disjoint','member','same_as','subset','within']
                                                     ↑ nově      ↑ 'complete' chybí
```

**Není to regrese.** Dřívější položka „`complete(g)` inert" byla uzavřena
pro cestu přes `attach`, a ta funguje dodnes. Tohle jsou jiné dveře.

**Doporučení (A‑5).** `complete` do `KERNEL_PREDICATES`, ze stejného
důvodu, z jakého tam šel `disjoint`. Uzavření světa je **řečový akt
člověka** („a to je všechno"), ne závěr učení — odvozovat úplnost z
neúplných dat je přesně ten předpoklad uzavřeného světa, který § 0 zakazuje.
Navíc to zachrání i stratifikaci: `complete` musí být stratum 0, jinak
hrozí nemonotónní rekurze. Dnešní chování je z obou možností to nejhorší —
pravidlo se přijme, atom se odvodí, účinek se zahodí. **Odmítnout nahlas.**

---

## Semantic Warnings

**W‑5 · `¬disjoint` prochází `attach`em, a je to správně.** Ověřeno, že se
popření nečte jako tvrzení: po zápisu `¬disjoint(pes,kocka)` vrátí otázka
na oddělenost `N` a `member(Rex,kocka)` zůstane `U`. Zábrana ho pouští
záměrně — je to legitimní tvrzení („překrývají se"), které žádnou expanzi
nepotřebuje. Zaznamenávám, aby to příště nikdo neopravoval jako díru.

**W‑6 · `KERNEL_PREDICATES` nemá vlastní doložku.** Je to množina, na
které visí I‑16 i stratifikace, a mění se ručně. Po B‑11 by měla mít
doložku s kritériem členství, ne jen výčet.

---

## Action Items for Agent 1

**A‑5 (B‑11, první).** `complete` do `KERNEL_PREDICATES`; pravidlo
s `complete` v nenegované hlavě ať skončí `UnsafeRule`, jako `disjoint`.

**A‑6 (W‑6).** Doložka pro `KERNEL_PREDICATES` s kritériem: *predikát,
jehož pravdivost mění uzávěr nebo uzavírá svět, se nesmí odvozovat
pravidlem.* Tím je členství `disjoint` i `complete` odvoditelné z pravidla,
ne z výčtu.

**Pořadí dodatku L se nemění** — po A‑5 a A‑6 pokračuje **L‑3 kvantifikátor
na roli**.

### Potvrzení, o která jsi žádal

**`P_DISJOINT` do `KERNEL_PREDICATES` — SCHVALUJI.** Rozhoduji z delegace
člověka, ne jeho podpisem. Oba důsledky, které jsi vyjmenoval, jsou
správné: učení do oddělenosti psát nesmí (I‑16), a `disjoint` v těle
nedělá hranu ve stratifikačním grafu, protože se nikdy neodvozuje —
odebrání té hrany nemůže zakrýt cyklus, jelikož `disjoint` nikdy není
hlavou. Ověřeno i vedlejšími cestami: `disjoint_of(Group, Place)` padá na
`SortError`, negovaný `disjoint` v hlavě na `UnsafeRule`.

**A‑1 volba odmítnout místo rozvinout — SCHVALUJI, a s tvým důvodem.**
Argument „`attach` slibuje jedna formule → jedno id, expanze zapisuje tři,
takže by volající neměl čím pravidla odvolat" je silnější než ten, který
jsem měl já. Tichá nemožnost odvolání je opravdu horší než hlasité
odmítnutí. Ověřeno, že chyba jmenuje **obě** správné dveře.

**A‑3 potvrzuji věcně.** `S-7` žádá průchod `.attach(`, takže test, který
by oddělenost ověřoval jen přes `add_disjoint`, u ní neprojde. To je
přesně ta zpětná vazba, kvůli které sloupec „použití" existuje.

---

## Archiv — kolo #21 (uzavřeno)

**Status tehdy: 🔴 FAIL.** Kolo #21. 319 testů zelených, 3 přeskočené, `mypy --strict` čistý na 34
souborech, jádro 0.1.5. Oba sledované blokery uzavřené. **FAIL vydávám za
jediný nález (B‑10), ne za stav repa** — je to tichá poddodávka odpovědi
přes veřejný vstupní bod, a to je I‑1.

**Architectural Health Score: 8,5 / 10**

| Oblast | Stav |
|---|---|
| Testy a typy | 🟢 319 passed / 3 skipped, mypy čistý na 34 souborech |
| B‑1 falešný `CycleDetected` | 🟢 uzavřeno — řetěz `A⊆B⊆C⊆D` + dvě pravidla nad `disjoint` přijata |
| B‑2 uzly mimo `attach` | 🟢 uzavřeno — báze 5 → 5 přes celé vyhodnocení |
| Matice `⪯` § 3.3 | 🟢 včetně **konkrétní × ∃ → `U`** (dialog B) a `∀` na nečlena → `U` |
| `CONFLICT` s oběma důkazy | 🟢 `conflict` je **n‑tice dvou důkazů**, listy `s0001` a `s0004` |
| Sortové stráže | 🟢 5 / 5 — včetně kvantifikátoru na `Entity` a holého `Group` v roli |
| `same_as` nedestruktivní | 🟢 odpověď `A`, původní zápis beze změny, báze 5 → 5 |
| `revoke` kaskádou | 🟢 s faktem `disjoint` zmizela i obě vygenerovaná pravidla, `N` → `U` |
| I‑16 hlava pravidla | 🟢 `member`/`subset`/`same_as` nenegované → `UnsafeRule`; negovaný `member` projde |
| **`disjoint` přes `attach`** | 🔴 **B‑10** |

---

## Critical Blockers

### B‑10 · `attach()` přijme `disjoint` a tiše z něj neodvodí nic

Podpořený vstup `kb.add_disjoint(...)` zapíše **tři** výroky — fakt plus
dvě vygenerovaná pravidla obou směrů `member̄`:

```
p0001: ¬member(elem:x, group:·kocka) <- member(elem:x, group:·pes)
p0002: ¬member(elem:x, group:·pes)   <- member(elem:x, group:·kocka)
s0001: disjoint(a:·pes, b:·kocka)
```

Ručně stavěný atom přes `attach()` zapíše **jen ten fakt**. Reprodukce,
stejná báze, jediný rozdíl je vstupní bod:

| dotaz | přes `add_disjoint` | přes `attach(atom(P_DISJOINT,…))` |
|---|---|---|
| `disjoint(pes,kocka)` | `A` | `A` |
| `member(Rex,kocka)` | **`N`** | **`U`** ← tichá poddodávka |

Index se přitom naplní **správně a symetricky** —
`{('pes','kocka'): s0002, ('kocka','pes'): s0002}` — takže se to netváří
jako odmítnutí. Systém odpoví `U` tam, kde má `N`, a nic neohlásí.

Proč to je bloker, ne kosmetika: `attach` je **veřejný zapisovač**,
`P_DISJOINT` je v `__all__`, a `disjoint` je **jediná jádrová relace bez
konstruktoru `_of`** — sedm sourozenců (`subset_of`, `member_of`,
`contains_of`, `within_of`, `before_of`, `same_as_of`, `complete_of`) ho
má, `disjoint` ne. Ta chybějící zábrana je přesně to, co dělá špatnou
cestu dosažitelnou. Je to **třetí případ téže třídy** po B‑9 a nepředaných
`tiers`, a platí na něj poučení z kola #19, které Builder sám přijal:
*cesta, kterou jde vrstvu zavolat a nefunguje, je vada NÁVRHU.*

---

## Semantic Warnings

**W‑1 · přímá otázka na `disjoint` je asymetrická.** Index drží oba páry,
`closures.py:465` je čte, ale `disjoint(kocka,pes)` vrátí `U`, zatímco
`disjoint(pes,kocka)` vrátí `A` — **i přes podpořený vstup**. Odvození
`member̄` symetrické je (obě pravidla), asymetrická je jen přímá otázka.
Třída B‑6: zákon je v indexu a dotaz ho nekonzultuje. V české rozpravě to
je běžná otázka („Je kočka něco jiného než pes?"), takže to není okrajové.

**W‑2 · opravuji vlastní dřívější tvrzení.** Sekce „Co drží" nese od kola
#12 větu *„`disjoint` symetricky v obou pořadích"*. Pro přímou otázku to
**dnes neplatí** (W‑1). Nedokážu z dnešního běhu rozhodnout, zda šlo
o regresi, nebo jsem to tehdy ověřil jinou cestou — proto to neoznačuji za
regresi, ale za **tvrzení, které jsem neměl nechat bez reprodukce**.

**W‑3 · `disjoint` není uzávěr, ale cukr nad generovanými pravidly.** Není
to vada — `revoke` je pod tím čistý, ověřeno — ale je to smlouva, kterou
nikde nedrží žádná doložka, a čtenář `closures.py` čeká uzávěr.

**W‑4 · předávka nesedí s kódem v počtu.** Handover tvrdí „19 doložek,
DRŽÍ 15, OTEVŘENO 4"; `contracts.CONTRACTS` má **18**, HELD 15, OPEN 3
(`O‑6`, `C‑5`, `S‑6`). Kód je vnitřně konzistentní, chybná je zpráva.
Drobnost, ale předávka je auditní stopa.

---

## Action Items for Agent 1

**A‑1 (B‑10, první).** Jedna cesta dovnitř. Doporučuji `disjoint_of()`
jako osmý konstruktor, aby `disjoint` přestal být výjimka, a `attach`
holý `P_DISJOINT` atom buď **rozvine stejně jako `add_disjoint`**, nebo
**odmítne rozlišující chybou**. Co nesmí zůstat: přijmout a mlčky
neodvodit. Rozhodni které z těch dvou — obojí je poctivé.

**A‑2 (W‑1).** Přímá otázka na `disjoint` ať konzultuje symetrický index.

**A‑3.** Doložka pro `disjoint` do matice. **Tohle je test té matice
samotné**: sloupec „použití" byl postaven přesně na tuhle třídu vad
(chytil by nepředané `tiers`) a `disjoint` doložku nemá. Kdyby ji měl,
B‑10 najde CI, ne já.

**A‑4 (W‑4).** Počty v předávce srovnat s `contracts.CONTRACTS`.

**Pořadí dodatku L se nemění** — po A‑1 až A‑4 pokračuje **L‑3
kvantifikátor na roli**, jak jsi navrhl vzít jako samostatný tah.

### Co jsem naopak potvrdil, ať se to nehledá znovu

`SegmentationError` jako vlastní typ mimo `OracleError` — souhlas s
odůvodněním, tři situace se opravdu nesmí slít. Čtyři sloupce matice
místo sedmi — **potvrzuji**; sedm sloupců popisuje konstruktor
metajazyka, doložka na hranici vrstev denotaci ani důkaz nemá, a
předstírat je by z matice udělalo ozdobu. Tři nálezy, které matice sama
našla při prvním spuštění, jsou pravdivé; oprava vlastního `O‑2`
z `.readings` na `unambiguous` je přesně to chování, kvůli kterému má
smysl sloupec odvozovat a nedeklarovat.

---

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

## ✅ KOLO #20 — B‑9 zavřen, žádný blocker

`pytest` **243 passed** · `mypy --strict` čistý na 30 souborech ·
jádro 0.1.5 beze změny · regrese celá drží.

Všechny tři věty, které dřív padaly, teď projdou:

```
Petr jel v pondělí do Prahy.  → jet(kam:Praha, kdo:Petr, v+Loc:pondělí)
                                 [POZOR: v+Loc může být kde nebo kdy]
Petr jel autem do Brna.       → jet(kam:Brno, kdo:Petr, čím:auto)
Petr bydlí v Praze s Janou.   → bydlet(kdo:Petr, s kým:Jana, v+Loc:Praha)
```

Role se pojmenovávají **z předložky a pádu**, jak žádá § 12/1, a mapování
na kanonické role je **naučený vzor** v `lexicon.py` s proveniencí a statusem
— stejný tvar jako `kromě → GROUP_DIFF`.

**Nejlepší rozhodnutí je to o `v+Loc`.** Seed ho mapuje na **obě** kanonické
role, `kde` i `kdy`, `role_candidates` vrací n‑tici, a `role_mapping_tier`
proto roli **nechá povrchovou** a do stopy zapíše proč:

```
role_candidates('v+Loc')  → ('kde', 'kdy')   ← n-tice, nevybírá se tiše
role_candidates('do+Gen') → ('kam',)          ← jednoznačné, přejmenuje
```

Je to pravda o češtině a Builder ji ve výchozích datech **nezamlčel**.
Přesně tvar, který si vynutila past F‑2 u slova „nebo".

### Builderův vlastní nález — potvrzuji a je vážnější, než zní

Našel, že `cascade()` se ukončovala smyčkou `if len(candidates) <= 1: break`.
To je správné pro **filtr**, ale patro, které čtení **přepisuje**, se pak
nespustilo vůbec. A všechny tři věty mají po tvrdých patrech přesně jednoho
kandidáta — takže **oprava B‑9 by vypadala hotově a nefungovala by**.

Ověřeno rozdílem:

```
bez mapování : jet(do+Gen:Praha, kdo:Petr)
s mapováním  : jet(kam:Praha,    kdo:Petr)   ← přejmenování proběhlo i s jedním kandidátem
```

Byla to **tichá závislost chování na počtu zbylých kandidátů** — kategorie
chyby, kterou test na výsledek nechytí, protože výsledek vypadá rozumně.
Zapíchnuto testem `test_transform_tiers_run_even_when_one_reading_is_left`.

---

## 🚨 KOLO #19 — `before*` hotový (jádro 0.1.5) · jeden blocker B‑9

`pytest` **236 passed** (bylo 225) · `mypy --strict` čistý na 30 souborech ·
jádro posunuto na **0.1.5**.

**Dodatek H splněn celý.** Ověřeno vlastními reprodukcemi:

```
before* je TRANZITIVNÍ        po → út A,  po → st A (přes út)
before* NENÍ reflexivní       po → po U          ← ne A
směr se nepřevrací            út → po U
cyklus                        InconsistentOrder  ← netiše neodpoví
cyklus NEZNEPOUŽITELNÍ osu    nezávislá dvojice x → y dál A
```

Verze i tabulka změn sedí; § 5.1 má `before*` s poznámkou o nereflexivitě,
§ 13 řádky T45–T48, a **cyklus je zapsaný jako otevřená položka**, ne jako
hotová záruka — přesně jak H‑3 předepsal.

**Nereflexivita nebyla v zadání a Builder ji přidal správně.** Bez ní by
splynulo „dřív" s „nejpozději" a dotaz *„jel Petr dřív do Prahy než do
Prahy?"* by vrátil `A`. Dobrý postřeh.

**Rozsah blokace u cyklu potvrzuji** — blokovat celou osu kvůli jedné chybě
v kalendáři by bylo horší než užší detekce. Je to otestované a v dokumentu.

### ⚠️ Dialog D je hotový strukturovaně, ne přes češtinu

`test_examples_petr_time.py` nepoužívá kaskádu ani orákulum (grep: 0 výskytů).
To je **v pořádku a odpovídá zadání** — § 6.12 popisuje dialogy strukturovaně
a dodatek G žádal akceptační test. Ale znamená to, že *„Petr jel v pondělí
do Prahy"* jako **česká věta** pořád neprojde. Proč, je v B‑9 níže.

---

## 🚨 B‑9 · Okolnosti se pojmenovávají podle `deprel`, ne podle předložky a pádu

**Nalezeno na dotaz člověka**, mimo běžné kolo. Blokující.

`_role_for` v `cascade.py` pojmenuje okolnost **doslova jejím `deprel`**:

```python
if token.deprel in ("obl", "nmod", "xcomp", "ccomp"):
    return token.deprel          # ← „obl" jako jméno role
```

Takže *„v pondělí"* i *„do Prahy"* dostanou **totéž jméno role `obl`**.
`Predication` duplicitní roli správně odmítne — a věta **spadne**:

```
✗ Petr jel v pondělí do Prahy.   → ValueError: čtení 'jel' má roli vícekrát: ['obl','obl']
✗ Petr jel autem do Brna.        → ValueError: … ['obl','obl']
✗ Petr bydlí v Praze s Janou.    → ValueError: … ['obl','obl']
```

**Není to okrajové.** Dvě příslovečná určení má v češtině obrovská část vět.
A první z nich je **doslova věta z dialogu D** — takže dialog D je blokovaný
tímhle **nezávisle na `before`**. Kdyby se `before` zítra doimplementoval,
dialog D by pořád nešel napsat.

### Zadání to má rozhodnuté — § 12/1

> *„Strukturální jádro uzavřené (kdo/co z podmětu a předmětu), **okolnosti
> povrchově podle předložky/pádu** (nehádá se sémantika, INV‑11),
> ekvivalence rolí („kudy" × „po čem") se učí dialogem jako odvolatelná data."*

Implementace tedy nedělá, co § 12/1 rozhodl. A UDPipe přitom **všechno
potřebné dodává** — u každé okolnosti je dítě s `deprel=case` nesoucí lemma
předložky, a samotný nominál nese `Case`:

```
v      ADP   deprel=case  →  pondělí  NOUN  Case=Loc   ⇒  role „v+Loc"
do     ADP   deprel=case  →  Prahy    PROPN Case=Gen   ⇒  role „do+Gen"
autem  NOUN  Case=Ins     (bez předložky)              ⇒  role „Ins"
```

Dnes se z toho čte **jen `deprel`**. Nevyužité zůstává lemma předložky,
`Case`, a u sloves `Tense` a `Aspect`.

### Oprava, která sedí na už existující mechanismus

Druhá půlka § 12/1 říká, že **ekvivalence rolí se učí dialogem jako
odvolatelná data**. To je přesně to, co `lexicon.py` už umí pro slova →
operace. Takže:

1. **`_role_for` pojmenuje okolnost povrchově** z předložky a pádu
   (`v+Loc`, `do+Gen`, `Ins`) — žádná sémantika se nehádá, INV‑11 drží.
2. **Mapování povrchové role na kanonickou** (`v+Loc → kdy`,
   `do+Gen → kam`, `po+Loc → kudy`) je **naučený vzor** v `lexicon.py`,
   se statusem a proveniencí, odvolatelný — stejně jako `kromě → GROUP_DIFF`.

Tím se zároveň řeší, proč § 3.6 mluví o rolích `kde / kam / odkud / kudy / kdy`,
zatímco kaskáda dnes umí jen `obl`.

**Poznámka:** kontrola duplicitní role v `Predication` je **správná** a nemá
se oslabovat — chyba je výš, v pojmenování. Je dobře, že to spadlo hlasitě
místo aby to tiše slilo dvě okolnosti do jedné.

---

## ✅ KOLO #18 — W‑5 a napojení `Session` hotové, žádný blocker

`pytest` **225 passed** (bylo 216) · `mypy --strict` čistý na 29 souborech ·
jádro 0.1.4 beze změny · `before` **správně nevzat** · regrese celá drží.

**W‑5 zavřeno** — `_missing_link` pokrývá i místa a časy:

```
báze jel(kam:Praha), dotaz kam:Brno  → chybí vědět: contains(part:Praha, whole:Brno)  [fakt s0001, role kam]
báze byl(kdy:pondělí), dotaz úterý   → chybí vědět: within(part:pondělí, whole:úterý)  [fakt s0001, role kdy]
```

**`Session.utter` splňuje past F‑3** — a lépe, než jsem čekal. Očekával jsem
výjimku u neběžícího orákula; místo toho se vrací **rozlišující výsledek**:

```
orákulum mimo  → error = 'služba neběží'   „✗ orákulum neodpovídá — provozní chyba, ne nepochopení"
nerozebráno    → error = None              „→ tuhle větu neumím přečíst"
žurnál po obou → 0 tahů
```

Strojově rozlišitelné, a pro dialogovou smyčku je návratová hodnota
**správnější než výjimka**, která by smyčku shodila.

### Builderova námitka mi sedí a beru si ji

Upozornil, že moje dvojí chyba (testování vrstvy přes vstupní bod, který ji
neobsluhuje) **není jen procedurální omyl**:

> *„Pokud se dá vrstva zavolat cestou, kde nefunguje, je to i vada NÁVRHU,
> ne jen postupu."*

Má pravdu, a u `GapFinder` to platí doslova: je v `Session`, ale
`Engine.ask()` vrací holý `Gap`, takže kdo jde přes engine, dostane
zopakovaný dotaz. Dnes jsem se spletl **potřetí** — čekal jsem výjimku tam,
kde je návratová hodnota. Zapisuji jako otevřenou otázku: **má `Engine.ask()`
na `GapFinder` aspoň ukázat v hlášce?**

---

## 📜 DODATEK K — výběr z obou konzultací (bez změny směru)

**Rozhodl:** člověk (J.), 14. 8. 2026 — *„vezmi to, co pokládáš za přínosné
bez zásadní změny směru."* Vybral jsem níže uvedené; u každé položky je,
proč směr nemění.

### Beru — dokumentační opravy (jádro se nemění, jen přestává lhát)

| | Co | Proč to není změna směru |
|---|---|---|
| **K‑1** | § 3.2 přeformulovat na **intervalovou aproximaci**: `certain`/`possible` jsou dolní a horní odhad znalosti, `DIFF` je *sound interval propagation*, ne operace nad možnými světy | Ověřil jsem, že kód to **už tak dělá** — `certain` je exaktní (per‑element důkazy), jen `possible` over‑aproximuje. Oprava popisu, ne sémantiky. |
| **K‑2** | § 6.3 přestat argumentovat monadickou FOL; charakterizovat jako **konečný typovaný stratifikovaný Datalog‑like systém** s closure operátory a epistemickou vrstvou nad dotazem. „PTIME" rozepsat **v čem** (báze, pravidla, dotaz, hloubka termů, role‑chain, scelení, strata) | Nahrazuje slabý argument přesným. Žádná schopnost se nepřidává. |
| **K‑3** | Explicitní axiom: **`∃x P(x)` může platit, aniž v grafu existuje `id(x)`** | Systém to tak dělá; chybí to napsat. |
| **K‑4** | `complete` pojmenovat jako **epistemickou deklaraci uzavřenosti**, ne jako inferenční fakt | Implementace to už tak dělá (mimo pevný bod). |
| **K‑5** | Nenárokovat „minimální vysvětlení" — je minimální **podle definované syntaktické metriky** | Konstrukci zachovat, formulaci opravit. |

Všech pět je změna verzovaného dokumentu → **posun verze a řádek v tabulce
změn**. Jsou to ale **opravy popisu, ne rozšíření schopnosti**, takže je
beru jako přínosné bez změny směru. Kdyby s tím člověk nesouhlasil, stačí říct.

### Beru — mechanismy, které jsou čistě additivní

**K‑6 · Contract systém / coverage matrix.** Nejcennější položka z obou
posudků. Každý konstruktor metajazyka dostane explicitní stav ve sloupcích
**syntax · typování · denotace · evaluátor · důkaz · renderer · test**,
ideálně generovaný z AST, a CI nesmí dovolit označit konstruktor za hotový,
dokud není řetěz uzavřený. **Přesně tohle by odchytilo `before`** — a
odchytí i příští takový drift, který při revizi ujde.

**K‑7 · Hranice parseru zpřesnit.** Báze smí eliminovat čtení **jen když pro
to existuje explicitně definovaný sémantický důvod** (formální konflikt,
typová chyba, nesplnitelný constraint) — ne „tahle interpretace se mi
nehodí". Jinak vzniká self‑confirming loop. Zpřesňuje můj dodatek H‑4(1).

**K‑8 · Metriky.** K „počtu tahů" přidat **informaci na tah**,
**znovupoužití** naučeného pravidla a hlavně **regret / correction rate**.
Jeden tah do naučení a deset chybných použití je horší než tři tahy
a stabilní správnost.

### Beru — levné UX zlepšení bez nové vrstvy

**K‑9 · Přeformulovat `GapFinder` do nabídky.** Místo *„chybí vědět:
disjoint(vrabec, tučňák)"* raději *„Předpokládám správně, že vrabec není
tučňák?"*. Je to **změna renderování**, ne nová vrstva — `GapFinder` už tu
větu spočítá. § 12/5 to sankcionuje: nabídka označená jako **HYPOTÉZA
s evidencí**, nikdy tiché tvrzení, jde odmítnout a **odmítnutí se pamatuje**.

**K‑10 · Adversariální dialogy H a I.** Dialog H (synonyma „vůz" × „auto",
cílí na `same_as`) a dialog I (neúplné premisy, cílí na kvalitu doptávání).
**Dialog G (zájmena) NE** — potřebuje aktivaci, která je odložená.

### Neberu — a proč

| | Proč ne |
|---|---|
| **Common‑sense defaulty** („pták létá, dokud…") | Nemonotónní logika. § 6.12 u dialogu E říká doslova *„bez nemonotónní logiky"*; rozbilo by I‑14 i akceptační test. Ta UX potřeba má sankcionované řešení — je to K‑9. |
| **Kontextový zásobník hned** | Mění pořadí proti dodatku F a proti prvnímu posudku. Navíc obsahuje *„tiše to přijme"*, což porušuje I‑1. |
| **LLM → AST** | **Neodmítám věcně** — je to architektonicky kompatibilní (rozbor v dodatku J). Je to ale změna směru, takže patří k rozhodnutí člověka, ne do tohohle výběru. |
| **Formální hardening PŘED češtinou** | Pořadí je rozhodnutí člověka (dodatek G × posudek 1). K‑1 až K‑5 jsou z hardeningu to, co jde udělat bez přerušení práce. |

### Pořadí, které doporučuji

**K‑6 první** — je nezávislý a chrání před celou třídou chyb.
Pak **K‑1 až K‑5** v jednom průchodu dokumentem (jeden posun verze).
Pak **K‑9**, **K‑7**, **K‑10**, **K‑8**. Vše po dokončení běžícího
dodatku G.

---

## 📜 DODATEK J — druhá konzultace (UX pohled): co přijmout a co ne

**Zdroj:** druhý konzultant, 14. 8. 2026. Optika je UX a škálování, ne
formalismus — a proto se v několika bodech **rozchází s prvním posudkem**.
Rozhodnutí o sporných bodech je na člověku.

**Drobná faktická oprava:** posudek mluví o „jádru 0.1.5". Jádro je na
**0.1.4**; `before` je schválený, ale neimplementovaný, takže 0.1.5 zatím
neexistuje.

### ✅ Co přijmout bez výhrad

**Doporučení 1 — měkká vrstva před tvrdým `U`.** Místo *„Nevím. Co ti
chybí?"* raději *„V databázi to nemám, ale předpokládám správně, že…?"*
**Tohle už je sankcionované** — § 12/5 zadání povoluje plnou proaktivitu
s pojistkami: nabídka je vždy označená **HYPOTÉZA s evidencí**, nikdy tiché
tvrzení, jde odmítnout a **odmítnutí se pamatuje**. `GapFinder` už navíc
sestupuje k větě, kterou člověk umí vyslovit. Chybí jen ta formulace
a napojení na měkkou vrstvu.

**Doporučení 4 — adversariální dialogy G, H, I.** Levné, správné, v duchu
§ 10. Dialog H (synonyma „vůz" × „auto") je zajímavý tím, že cílí přesně na
`same_as` a jmennou vrstvu § 3.5.

**Kritika 2 — únava z doptávání.** Reálné riziko. Pojistka existuje
(pamatovat si odmítnutí), ale metrika ji neměří. Souvisí s tím, co navrhl
první konzultant: přidat **regret / correction rate** a **informaci na tah**.

### ❌ Co je neslučitelné s jádrem

**Kritika 4 a „common sense" defaulty — „pták létá, dokud se neřekne, že je
to tučňák".** To je **default reasoning**, a projekt ho odmítá vědomě, ne
z opomenutí. § 6.12 u dialogu E říká doslova, že výjimky unese *„samotná
algebra groups (`NOT`), **bez nemonotónní logiky**"*. Přijmout defaulty by:

* zavedlo **nemonotonicitu** — pozdější fakt by rušil dřívější závěr;
* rozbilo **I‑14** — vysvětlení se renderuje jen ze skutečné struktury,
  a default žádnou nemá;
* **rozbilo dialog E**, který je akceptačním testem.

Ta UX potřeba je ale legitimní a **má sankcionované řešení**: ne „systém
předpokládá", nýbrž „systém **nabídne hypotézu**, člověk potvrdí". To je
doporučení 1, které přijímám. Rozdíl mezi „předpokládám a mlčím" a
„navrhuji a ptám se" je přesně ta hranice, na které projekt stojí.

**Detail v doporučení 2:** *„Pokud to sedí s bází, **tiše to přijme**."*
Tiché přijetí porušuje I‑1. Kandidát z kontextového zásobníku musí být
buď doložený, nebo nabídnutý — nikdy tichý.

### ⚖️ Kde se konzultanti rozcházejí — rozhodne člověk

| | První posudek | Druhý posudek |
|---|---|---|
| **Aktivace / koreference** | P2 — *„dluh existuje, ale zatím bych ho nestavěl"* | **předsunout hned**, jinak systém degraduje na „databázové CLI" |
| **Kaskáda pro češtinu** | *„v roce 2026 obhajitelná"*, jen zpřesnit hranice | **křehká**, hrozí špagety při škálování na 600 dialogů |
| **Pořadí** | nejdřív formální hardening | těžiště **okamžitě** do `cascade.py` a `oracle.py` |

K té kaskáde jedna věcná poznámka: riziko špaget se týká **pater
v `cascade.py`**, ne `patterns.py`. Vzory jsou **data** s proveniencí
a statusem, serializovaná do JSON — přidání vzoru není nová větev kódu.
A § 3.0 zakazuje větvení podle druhu konstrukce, což je právě ten
anti‑vzor, kterým conBond3 zarostl.

### 🔬 Doporučení 3 — LLM → AST: kompatibilní, a stojí za vážné zvážení

Tohle je nejzajímavější bod celého posudku a **neodmítám ho**. Nechat
neuronovou síť dělat to, v čem je dobrá (chaos přirozeného jazyka, elipsy,
synonyma), a výsledek prohnat deterministickým enginem, je architektonicky
konzistentní s I‑2: *„jazyk a statistika navrhují, o pravdivosti rozhoduje
jádro."* LLM je jen lepší navrhovatel než ruční kaskáda.

Tři podmínky, za kterých to invarianty unese:

1. **Determinismus (I‑4) zůstává**, protože do žurnálu jde **struktura, ne
   text** — LLM běží jednou za tah a výsledné AST se zapíše. Kdyby v žurnálu
   ležely věty, replay by závisel na modelu a padlo by to.
2. **Provenience (I‑5)** — AST musí nést, který model a která verze ho
   vyrobily, přesně jako keš u UDPipe.
3. **Nejednoznačnost se pořád ptá.** LLM vrátí kandidáty; když AST
   neprojde typováním nebo je kandidátů víc, systém se **zeptá**, nehádá.

Za těch podmínek je to **týž tvar jako dnešní kaskáda**, jen s jiným
generátorem kandidátů — a `oracle.py` je už napsaný jako **fasáda
s injektovatelnou dopravou**, takže výměna generátoru je návrhově
připravená. Stojí za to to zkusit vedle stávající cesty a porovnat na
zlaté sadě, ne místo ní.

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

---

# Dodatek L — cesta k plné funkčnosti podle etalonových dialogů

**Kolo #20. Zadání sestaveno z vlastního úsudku; člověk tento okruh
rozhodování delegoval větou „na základě vlastního expertního úsudku
směruj k naplnění zadání workera".** Delegace je zaznamenaná proto, aby
bylo z auditu poznat, že smlouvy vrstev v L‑0 a L‑1 neprošly kolem
člověka omylem, ale s jeho vědomím.

## L‑0 · Reprodukce uzavření dodatku G

Ověřeno spuštěním, ne přečtením:

- `pytest -q` → **259 passed** (+16 oproti kolu #19)
- `mypy --strict .` → **čistý, 32 souborů**
- `session.py:422,452` — `cascade(..., tiers=self.tiers())` na **obou**
  větvích; patra se staví per tah, ne v konstruktoru
- `session.py:420` — víc čtení jde do `_utter_many`, ne `readings[0]`

Nález o `tiers` beru jako **správně diagnostikovanou vadu návrhu**, ne
jako opravu postupu. Je to třetí případ téhož druhu (B‑9, `tiers`,
a nález níže): **defekty vznikají na hranicích vrstev, ne uvnitř nich.**
To řídí pořadí v L‑6.

## L‑1 · Rozhodnutí: co je `Utterance`

Nález potvrzen v `oracle.py:310` — `for sentence in sentences` skládá
**jeden záznam na větu** do pole, které `_utter_many` čte jako
**kandidátní čtení jedné promluvy**. Dvouvětý vstup by se na živé službě
zeptal „které z toho?" na dvě různé věty. Dnes to nikdo nepotká jen
proto, že `cb-udpipe` neběží — to není obrana, to je odklad.

**Rozhodnuto: `Utterance` je JEDNA VĚTA.** Důvody, v pořadí váhy:

1. `Session.utter` mapuje **jeden tah na jednu predikaci**; žurnál je
   indexovaný tahy. Dvouvětá promluva nemá kam uložit druhý výsledek.
2. Nálada (`mood`) se detekuje z celého textu. U dvou vět je **jedna
   nálada pro obě už teď špatně** — „Petr jel do Prahy. Jel tam v pondělí?"
   nemá společnou náladu.
3. `unambiguous` dává smysl jen per větu.
4. `_utter_many` se ptá na **dvojznačnost**. Segmentace není dvojznačnost.

**Provedení:** při `len(sentences) > 1` **rozlišující chyba**, nikdy tiché
vzetí první. Segmentace textu na tahy je **samostatná operace**
(`segment()` nebo práce volajícího), ne skrytá vedlejší funkce `parse`.
Logika jádra se nemění → **bez bumpu 0.1.5**, ale zapsat do smluv (L‑6).

## L‑2 · Kde přesně končí česká cesta

Reprodukováno: `utter` větu přečte, uloží strukturu do žurnálu, vypíše
`✓ přečteno` a **skončí**. Do báze se nezapíše nic, otázka se
nevyhodnotí. Chybí čtyři věci, ne jedna.

### L‑3 · Kvantifikátor na roli — **blokuje vše ostatní**

```
role('kdo', Group('Učitelka'))   →  UnquantifiedRole
```

Jádro **vyžaduje** kvantifikátor u každého skupinového filleru.
`Predication` z kaskády žádný nenese — `Mention` má lemma, tvar, index,
`upos`, `feats`, a nic víc. **Z české věty se skupinou v roli dnes nejde
postavit ani jeden platný atom.** To je většina etalonových vět.

Nehádat. Mechanismus, který na to už existuje, se má použít celý:

- **Explicitní determinátory přes lexikon** — `každý → FOR_ALL`,
  `nějaký`/`některý → EXISTS` už v `czech_seed()` jsou. Doplnit
  `všichni`, `žádný`, a `ten/ta/to` jako **určitost, ne kvantifikaci**
  (odkazuje na uzel, nezavádí skupinový fillér).
- **Holé jméno bez determinátoru** — čeština nemá členy, takže tohle je
  většinový případ. **Žádná implicitní hodnota v kódu.** Nabídne se jako
  `LearnedPattern` se statusem hypotézy, klíčovaný `StructuralSignature`
  (`upos`, `Number`, pád, `deprel`), potvrdí ho člověk jednou a pak platí.
  Tím je to **data s proveniencí a odvolatelné**, ne zadrátovaný dohad
  (I‑16: učení mění program, ne jazyk).
- **Když nic nerozhodne → zeptat se.** Nikdy nedosadit (I‑1).

Nové patro kaskády, řadí se **za** mapování rolí.

### L‑4 · Negace z `Polarity=Neg`

Ověřeno: `cascade.py` slovo *negace* nezná — nula výskytů. Česká negace
je předpona slovesa (`nelétá`, `nesmí`), UDPipe ji dává jako
`Polarity=Neg` na slovese. `Operation.NEGATION` v lexikonu **už je**,
jen ji nikdo neplní.

Bez toho **doména farmaka nefunguje** — celý její závěr je `nesmí dostat`.
Malá práce, tvrdý dopad. Pozor na I‑21: `Polarity=Neg` je **silná negace
`p̄`**, ne nepřítomnost důkazu.

### L‑5 · V3 — zmínka → uzel, a směrování tahu

Teprve tady se věta stane faktem. Rozsah **omezený na to, co etalon
potřebuje**:

- vlastní jméno → uzel podle jména; nový uzel vzniká **jen `attach`em**,
  tedy lidským tahem — ne vyhodnocením (§ 0.2, No Chase)
- obecné jméno → `Group`
- určitý popis → doložit existující uzel; **víc kandidátů → doptat se**
- **zájmena a elipsa VEN.** Potřebují aktivaci (§ 4), etalon je nemá,
  protože mluví jmény. Mez se **řekne nahlas**, nepředstírá se.

Směrování je pár řádků a bez něj je zbytek k ničemu:
`!` → postav formuli, `attach`; `?` → postav atom, `ask`, vyrenderuj přes
`XAIPresenter`; `U` → nabídni `GapFinder` (K‑9).

### L‑6 · Pořadí a proč právě takhle

Držím **K‑6 (smlouvy) první, ale zúžené** — a není to byrokracie.
Tři poslední defekty (B‑9, nepředané `tiers`, `Utterance.readings`) jsou
**všechny** vady smlouvy mezi `oracle → cascade → session → storage`.
To je přesně ta hranice, na kterou se V3 připojuje. Matice smluv nad
**těmito čtyřmi vrstvami** je přímá oprava opakující se třídy vad; matice
nad celým repem počká.

```
K‑6 zúžené  →  L‑1  →  L‑3  →  L‑4  →  L‑5  →  L‑7
smlouvy        věta    kvant.  negace   V3      zlaté
hranic                                          dialogy
```

`L‑3` před `L‑5`, protože V3 by jinak neměla z čeho stavět.
`L‑7` **poslední** — zlatá sada má fixovat hotový řetěz, ne rozpracovaný.

### L‑7 · Zlaté dialogy pěti domén

Bod 6 dodatku G fixoval **rozbor** deseti vět. Tohle fixuje **celý tah** —
česká věta → zápis do báze / odpověď s doložkou. Pět domén, které dnes
existují jen strukturovaně (`dálnice`, `farmaka`, `učitelka`,
`Petrovice`, `čas a prostor`). Věta, která se má **odmítnout**, dostane
vlastní pole, jako v G‑6.

---

*Kolo #20. Dodatek G uzavřen a reprodukován. Řízení předáno Builderovi
na K‑6 zúžené, dál podle pořadí v L‑6.*

---

# Dodatek M — přijetí konzultace V3 (zmínka → uzel)

**Kolo #26½.** Externí konzultace odpověděla na Q1–Q5 ze zadání. Hodnotím
z delegace člověka; přijímám **všech pět rozhodnutí s podmínkami** níže.
Tvrzení konzultanta jsem tam, kde to dnes jde, **reprodukoval proti
jádru** — výsledky jsou součástí podmínek. Stavový soubor nechávám být
(tah je Builderův); tenhle dodatek je zadání pro L‑5.

## M‑0 · Co jsem reprodukoval předem

Jádro už dnes unese víc, než konzultant předpokládal — a jednu věc ne:

```
attach(¬same_as(P1,P2))          → přijato        ✓ (operace 2 jde stavět hned)
same_as(P1,P2)?                  → N              ✓
¬same_as(P1,P2)?                 → A              ✓
po přidání same_as(P1,P2):
  same_as(P1,P2)?                → CONFLICT       ✓ oba důkazy
  bydli(B)? přes spornou hranu   → A              ✗ NÁLEZ M-1
```

### M‑1 · uzávěr používá hranu identity, i když je identita ve sporu

`¬same_as(A,B)` + `same_as(A,B)` dá na přímou otázku `CONFLICT`, ale
uzávěr hranu **dál používá** a `bydli(B)` odpoví `A` — fakty tečou přes
identitu, o které báze ví, že je sporná. To je I‑1 (tichá volba) a bez
opravy je **kanonizace jmen z Q1 nebezpečná**: `assert_distinct_from` by
sliboval ochranu, kterou uzávěr nectí. **Podmínka: hrana identity, jejíž
výrok je ve sporu, se v uzávěru nepoužije** (a dotčené odpovědi ať nesou
gap, ne tiché `A`). Patří do jádra → verzovaný bump, řádek v matici.

## M‑2 · Q1 přijato: kanonizace jména v sezení — se dvěma podmínkami

Politika (a): `PROPN` s `·` se v sezení mapuje na kanonický uzel jména.
Argument konzultanta beru: doptávat se na každé opakování jména je
interrogation fatigue, a protože `same_as` je pohled a split existuje,
je defaultní ztotožnění **plně odvolatelné** — což tichý default
kvantifikátoru nebyl (proto tam platí jiné pravidlo a žádný rozpor v tom
není: odvolatelný default s hláškou vs. neodvolatelný dohad).

- **Podmínka A — default se říká nahlas.** Tah vypíše vazbu:
  `Karel → Karel_1 (kanonicky; týž uzel jako v tahu #3)`. Bez toho by to
  byl tichý default a ty v tomhle projektu nejsou.
- **Podmínka B — kanonizace konzultuje `¬same_as`** (proto operace 2
  existuje) **a stojí na M‑1**.

Čtyři identitní operace přijímám. `assert_same_as` a `revoke_identity`
jsou hotové dnes (reprodukováno). `split_entity` jako atomický tah
`SPLIT`: **odvolání je deaktivace, ne mazání** (§ 8 — konzultantovo
„vymažou" se čte jako „deaktivují") a přesměrované výroky nesou
provenienci ukazující na tah SPLIT, ne na původní `řekls`.

## M‑3 · Q2 přijato: uzel vzniká tahem `!`, vazba v žurnálu

„Individua vznikají výhradně attachem" drží — `!` JE ten vědomý tah.
`NodeBinding` v těle tahu + replay dosazuje uložená id bez kaskády je
přesně invariant „co nejde spočítat, nese se s tahem". **Podmínka:**
založení uzlu se hlásí (`[UZEL: založen Karel_1]`), stejná cesta jako
`[ZÁPOR]`/`[ZAHOZENO]`.

## M‑4 · Q3 přijato: určitost bez tichého fallbacku

0 kandidátů → odmítnout s otázkou; 1 → doložit **s hláškou** (podmínka:
i jednoznačné doložení se vypíše, `[ODKAZ: to auto → auto_1 (jediný
kandidát, tah #2)]`); >1 → `awaiting='odkaz'` + kandidátní množina.
`DECIDE_REFERENCE` jako samostatný tah žurnálu je správně — rozhodnutí
člověka je tah, replay se neptá.

## M‑5 · Q4 přijato: jedna fronta `awaiting='odkaz'`

Asymetrie rigidní/deskriptivní designátor sedí s tím, co kaskáda už dělá
(`PROPN` → `·` rovnou, `DEFINITE` čeká). Dva Petrové v bázi → `PROPN`
opustí `·` a spadne do téže fronty. `pending_candidates` se do žurnálu
**neukládá** (spočítá se z báze daného okamžiku — replay je deterministický),
ukládá se až rozhodnutí.

## M‑6 · Q5 přijato s korekcemi názvosloví

`NodeBinding(token_index, node_id, binding_type, reason)` — **podmínka:**
`binding_type` jako `Enum`, ne volný řetězec (`CANONICAL_PROPN` |
`RESOLVED_DEFINITE` | `CREATED_NEW`). Chování při `revoke` přijímám celé:
uzel je symbol, žije, dokud na něj ukazuje aktivní výrok; osiřelý uzel
mizí **jen z kanonického indexu jmen** (index se beztak staví nad
aktivními výroky), nikdy ze storage. Žádné kaskádové mazání.

**Poznámka k zobrazení:** id `Karel_1` je interní; presenter ukazuje
„Karel" a suffix jen při víc uzlech téhož jména. Jinak by první věta
každého dialogu vypadala, že systém očísloval člověka.

## M‑7 · Pořadí pro L‑5

```
M-1 (jádro: sporná hrana mimo uzávěr, bump)
  → směrování tahu (! → attach, ? → ask)      [rozhodnuto dávno, neblokováno]
  → NodeBinding + kanonizace PROPN (M-2, M-3)
  → určitost + DECIDE_REFERENCE (M-4, M-5)
  → identitní operace SPLIT / assert_distinct_from (M-2)
  → zlaté dialogy pěti domén (L-7)
```

M‑1 první, protože kanonizace bez ní stojí na hraně, kterou uzávěr nectí.


## M‑8 · Odpověď na dotaz Buildera k L‑7

Dotaz: *„Má L‑7 počkat na konzultaci? Fixovala by celé tahy včetně
identity jmen, a kdyby konzultace name_of změnila, přepisoval bych ji
hned potom."*

**Konzultace už proběhla a je přijatá — dodatek M výše, rozhodnutí Q1–Q5
jsou finální (z delegace, s podmínkami).** Na konzultaci se tedy nečeká.
L‑7 čeká na něco jiného: na **dokončení M‑1…M‑6**, a to z přesně toho
důvodu, který v dotazu sám jmenuješ — zlatá sada fixuje hotový řetěz,
ne rozpracovaný. Pořadí M‑7 ji proto dává poslední; to platí od dodatku L
a nic se na tom nemění.

Prakticky pro identitu jmen ve zlatých dialozích, ať se sada nemusí
přepisovat:

- vazba jména na uzel jde přes **`NodeBinding` v tahu** (M‑3), kanonizace
  `PROPN` per sezení s hláškou (M‑2, podmínka A) — pokud tvoje `name_of`
  dělá něco jiného, srovnej to s M **před** psaním sady;
- zlatý tah fixuje **i vazby** (`bindings`), ne jen predikaci — jinak by
  sada nehlídala právě tu část, kterou M zavádí;
- id uzlů v sadě jsou interní (`Karel_1`), presenter ukazuje „Karel"
  (M‑6, poznámka k zobrazení).


---

## Poznámka mimo kolo — ŽIVÁ SLUŽBA BĚŽÍ, diferenční běh proběhl

*(zapsáno mezi koly; stavový soubor nedotčen — tah je tvůj)*

Člověk zadal vytažení služby do vlastního repa **conbond4-deps**
(`C:\Users\jindr\PycharmProjects\conbond4-deps`, commity `84b7fe9`
a `5c8f8e8`). Služba **běží na 127.0.0.1:42200** — Windows si vyžádal
pět oprav (UTF‑8 pro cp1252 konzoli, `OpenProcess`+`GetExitCodeProcess`
místo `os.kill(pid,0)`, patch `SO_REUSEPORT` a POSIX signálů ve vendoru,
delší `start_timeout_s` kvůli konverzi RobeCzech). Model je
**cs_all‑ud‑2.17‑251125** — novější než nahrávky.

`python -m core_semantics.live_check` dal na všech 11 větách:

```
! JINÝ MODEL: 'udpipe2 model=czech-pdt-ud-2.12 …' → 'udpipe2 model=? tokenizer=6247b8b7a5c8'
! JINÁ TOKENIZACE: N → N+1 tokenů — po pozicích už se porovnat nedá
```

Tvůj nástroj se zachoval přesně podle návrhu (provenience první a sama,
tokenizace jako vlastní třída). **Dva nálezy k tvému dalšímu tahu:**

**L‑B1 · `model=?` v provenienci — OPRAVENO v deps.** `/version`
nevracelo jméno modelu, klient doplnil `?`. Opraveno v conbond4‑deps
(`769304e`): model se čte z konfigurace, ne z upstreamu, aby `/version`
odpovědělo i když UDPipe neběží. Ověřeno — provenience je nyní
`udpipe2 model=cs_all-ud-2.17-251125 tokenizer=6247b8b7a5c8`.
**Zbývá tvoje rozhodnutí:** má `_handshake` nedostatečnou provenienci
(`model=?`) rovnou **odmítnout**? Keš bez identity modelu je horší než
žádná a dnes ji nic nebrání.

**L‑B3 · `feats` jako JSON objekt — CHYTL JSI TO SÁM, POTVRZUJI
REPRODUKCÍ.** Živá služba vrací `feats` jako **objekt**, ne CoNLL‑U
řetězec. Narazil jsem na to při charakterizaci rozdílu:
`OracleError: rysy "{'Animacy': 'Anim', …}" nejdou přečíst`. Než jsem
to stačil sepsat, měl jsi v `oracle.py` opravu i s komentářem, který tu
vadu popisuje přesně („`str({'Case': 'Nom'})` je platný řetězec, jen
v něm `parse_feats` nic nenajde"). Ověřeno po opravě: **11/11 vět sady
i 3 nové věty projdou**, čerstvé i z keše. Zásluha je tvoje, zapisuju to
jen proto, že reprodukce má být v auditní stopě — a protože je to
učebnicový příklad toho, proč se `str()` nesmí volat na neznámý tvar:
přetypování z omylu udělalo *platnou* hodnotu.

**L‑B2 · nahrávky vs. živý parser: systematický +1 token.** Nahrávky
jsou psané bez interpunkce, živý parser ji dává (a je z 2.17). Podle
tvé vlastní zásady se nahrávky automaticky nepřepisují — rozhodnutí
patří člověku; můj názor: až po opravě L‑B1, ať se přepisuje proti
plné provenienci, a jedním vědomým commitem s viditelným diffem.


---

## Poznámka mimo kolo — předvedení na živém parseru

*(tah je Builderův; stavový soubor nedotčen)*

Předvedl jsem schopnosti na skutečném rozboru, ne na nahrávkách. Řetěz
funguje celý: `Filip má auto.` → `zapsáno [s0001]`, `Má Filip auto?` →
`ANO, doloženo s0001`; zápor, spor s oběma důkazy, kanonizace jmen
napříč tahy, smyčka doptání i odmítnutí zájmena — vše na živých datech.
**Dvě věci z toho patří do zadání:**

**W‑16 · odpověď `∀` na tvar `PROPN` zobecní špatně.** V ukázce jsem na
`Vrabec létá.` odpověděl „o každém" a systém si uložil vzor
`PROPN/Sing/Nom/nsubj → for_all`. To čte jako *„každé vlastní jméno
v podmětu je skupina"*, což je pro vlastní jména nepravda — a je to táž
dvojznačnost jako tvůj nález 2. Zvaž zábranu: `∀`/`∃` na `PROPN` je
podezřelé a systém by se měl doptat *„je „Vrabec" jméno, nebo druh?"*
místo aby tvar zobecnil. Rozhodni ty; může to být i vědomě ponechané.

**Parser se plete a systém na to reaguje správně.** `Datel klove.` →
`NEVÍM, jak to čtu` (`generátor: 0 čtení`), protože parser označkoval
`klove` jako `NOUN` ve vokativu místo slovesa. Bez přísudku není
predikace — a systém si ji **nevymyslel**. Ověřeno srovnáním:
`Datel klepe.` se týmž parserem přečte správně. Je to nejlepší doklad
I‑1 na cizích datech, jaký jsme zatím měli.


---

# Dodatek N — proč složité příklady nejdou česky, a co s tím

**Zadání od člověka: „spíš zjisti proč a doporuč řešení než zahazuj —
ale cílem je, aby příklady fungovaly."** Diagnostikoval jsem obojí až na
mechanismus. Nejsou to dvě vady, ale **dvě různé věci**, a jen jedna
z nich je chyba.

## N‑1 · CHYBA: UD podtypy `deprel` se porovnávají na přesnou shodu

```python
CIRCUMSTANCE_DEPRELS = ("obl", "nmod")      # cascade.py:253
NOMINAL_DEPRELS      = ("nsubj", "obj", "iobj")   # cascade.py:305
```

Univerzální závislosti používají **podtypy** (`obl:arg`, `nsubj:pass`,
`aux:pass`, `expl:pass`, `nmod:poss`). Porovnání `token.deprel in (...)`
je na nich slepé, takže token propadne a skončí jako `[ZAHOZENO]` —
nebo, když jde o podmět, jako **nečitelná věta**.

Změřený dopad na běžné české větě:

```
» Petr věří v úspěch.        ◐ věřit(kdo:·Petr)
                             [ZAHOZENO: „úspěch" (obl:arg pod „věří")]
» Auto bylo koupeno Filipem. → NEVÍM, jak to čtu      (nsubj:pass, obl:arg)
» Lék se podává pacientům.   → NEVÍM, jak to čtu      (nsubj:pass, expl:pass)
```

**Celý trpný rod je pro systém neviditelný** a všechny předložkové
předměty sloves i adjektiv (`věřit v`, `alergický na`, `podávat komu`)
padají. To je jednořádková příčina s velkým dosahem.

### Doporučené řešení — a POZOR na past

Rozděl dvě věci, které dnes splývají:

1. **Viditelnost** (je ten token kandidát na roli?) → porovnávej
   **základ** deprelu, `deprel.split(":")[0]`.
2. **Pojmenování** (jakou rolí se stane?) → nech v podpisu **celý
   deprel včetně podtypu**.

Past je v tom, že **`nsubj:pass` NENÍ `nsubj`**. Ve větě *„Auto bylo
koupeno Filipem"* je `auto` trpný podmět, tedy to *kupované*, a agens
je `Filipem`. Kdyby se podtyp zahodil, systém by mlčky přiřadil „kdo"
tomu, kdo nic nedělá — a **to by bylo horší než dnešní odmítnutí**,
protože dnes aspoň řekne „nevím, jak to čtu". Rozdělení výše to řeší:
token se stane viditelným, ale jeho roli rozhodne naučené mapování,
které podtyp vidí. Žádné hádání sémantiky (I‑2, INV‑11).

## N‑2 · NENÍ chyba: jádrové relace čeština neumí VYROBIT

```
» Amoxicilin je druh penicilinu.  →  být(Gen:penicilin, co:·druh, kdo:∀amoxicilin)
                                     a NE subset(amoxicilin, penicilin)
```

Tohle není vada kaskády — kaskáda dělá přesně to, co má: **gramatiku**.
Chybí patro, které z konstrukce navrhne **jádrovou relaci**. `Operation`
už `SUBSET`, `MEMBER` i `DISJOINT` v menu **má**; nikdo je jen neplní ze
stavby věty.

### Doporučené řešení: patro jádrových relací, stejnou disciplínou

Nové patro **za** mapováním rolí (potřebuje hotové role), návrh →
potvrzení, **nikdy tiše** — přesně jako kvantifikátory:

| konstrukce | návrh | odkud signál |
|---|---|---|
| `X je druh Y` (root lemma `druh`/`typ`, `nmod` v Gen) | `subset(X, Y)` | **spouštěcí slovo** — táž mašinerie jako `kromě` → `GROUP_DIFF` |
| `PROPN je NOUN` (*Jana je učitelka*) | `member(X, Y)` | vlastní jméno = individuum |
| `NOUN je NOUN` (*Amoxicilin je penicilin*) | **zeptat se** | `member` × `subset` z morfologie nepoznáš |
| `X není Y` (spona + `Polarity=Neg`) | `disjoint(X, Y)` | zápor už čteme (L‑4) |

Jednoznačné spouštěče smí být v seedu, dvojznačná holá spona **se ptá** —
je to táž hranice jako u holého jména bez determinátoru.

**Jedna past, na kterou nezapomeň:** `disjoint` se **nezapisuje přes
`attach`** (B‑10). Patro musí navrhnout tah, který jde správnými dveřmi
(`add_disjoint`), jinak dostane `AttachError` — a ta zábrana je tam
správně.

## N‑3 · Co tím padne

Po N‑1 a N‑2 jde **doména farmaka napsat česky celá** — dnes jediné, co
jí chybí, jsou `subset` z „je druh" a role z „alergický na". Pravidla
(`R5`) zůstávají strukturní; jazyk pro ně je samostatná otázka a do
tohohle zadání ji netahám.

## N‑4 · Vedlejší nález k rozhodnutí

`Jan je alergický na penicilin.` se dnes **zapíše** jako
`být(co:·alergický, kdo:Jan)` — tedy „Jan je alergický" bez alergenu.
Není to tiché (`◐`, `[ZAHOZENO]`), takže to není bloker, ale ve
farmaceutické doméně je to nebezpečná polopravda. Po N‑1 většina těchto
případů zmizí; **rozhodni, jestli má věta se zahozeným VÝZNAMOVÝM
tokenem vůbec zapisovat**, nebo skončit jako otázka. Můj názor: nezapisovat
— `◐` má znamenat „ptám se", ne „zapsal jsem něco menšího, než jsi řekl".


---

# Dodatek P — posouzení druhého externího hodnocení

Všechna tři P0 jsem **ověřil proti kódu**. Výsledek: jedno je hotové,
jedno platí a je horší, než posudek tvrdí, a jedno je dokumentační dluh,
ne vada.

## P‑1 · P0 „certain/possible jako epistemická aproximace" — UŽ HOTOVO

Posudek žádá rozhodnout, že `possible` **není** přesná možnosvětová
sémantika. To v § 3.2 od verze 0.1.7 **doslova stojí**:

> „**Je to INTERVALOVÁ APROXIMACE, ne kvantifikace přes možné světy** …
> operace nad ní jsou **sound interval propagation** … `certain` je
> **exaktní**, `possible` je **nadhodnocené**. Je to bezpečná strana."

Posudek posuzoval starší stav. **Neměnit** — a stojí za zmínku, že
tenhle nález vznikl nezávisle třikrát: našel jsem ho reprodukcí
(ztráta korelace u `subset(A,B) ∧ subset(B,A)`), Builder ho zapsal jako
K‑1, a teď ho potvrzuje externí posudek. Shoda tří nezávislých cest je
silnější důvod než kterákoli z nich.

## P‑2 · P0 „pořadí literálů" — POTVRZENO, A HŮŘ

Posudek uvádí, že jedno pořadí selže a jiné projde. Změřil jsem
**všech šest permutací** téhož pravidla (farmaka: `alergie_na`,
`obsahuje`, `subset`):

```
aos → N        aso → EvaluationError
oas → N        osa → EvaluationError
               sao → EvaluationError
               soa → EvaluationError
```

**Dvě fungují, čtyři padnou** — a `attach_rule` přijal **všech šest**.
Chyba přijde až při vyhodnocení, tedy případně o mnoho tahů později
a jen na některý dotaz.

Pro dialogové učení je to vážné přesně tak, jak posudek píše: **lexikální
tvar naučeného pravidla mění jeho chování**. Člověk může pravidlo
nadiktovat správně a systém ho přijme, aby se o měsíc později ukázalo,
že se rozpadne na konkrétní otázce.

**A‑24 (P0, nejvyšší priorita mimo N‑5).** Při `attach_rule` provést
**analýzu vázanosti proměnných** a pravidlo buď **normalizovat do
kanonického bezpečného pořadí**, nebo **odmítnout hned při zápisu**.
Po tom platí, že `A ∧ B` a `B ∧ A` jsou totéž — pořadí zůstane
implementační strategií, ne vlastností významu. Odmítnutí při zápisu je
navíc přesně ten druh hlasitého selhání, který tenhle projekt jinde
vyžaduje.

*(Poznámka k mému vlastnímu měřítku: `EvaluationError` je hlasitá, takže
tohle není `FAIL` podle kritéria „tiše špatná odpověď". Je to ale
nejzávažnější **architektonická** položka, jakou dnes máme otevřenou.)*

## P‑3 · P0 „complete jako lokální uzávěr" — CHOVÁNÍ JE SOUNDNÍ, CHYBÍ POPIS

Posudek správně žádá určit, **co přesně** se uzavírá. Změřil jsem tři
cesty šíření:

```
complete(tým) → member(Z, tým)                 → N
complete(tým), same_as(tým, parta) → member(Z, parta)  → N
complete(tým), subset(jádro, tým)  → member(Z, jádro)  → N
```

**Všechny tři jsou soundní.** U `same_as` jde o tutéž skupinu pod jiným
jménem; u `subset` platí, že když `Z ∉ tým` a `jádro ⊆ tým`, pak
`Z ∉ jádro`. Chování je správné — ale **nikde není napsané**, a příště
si to někdo odvodí jinak.

**A‑25 (P1, do dokumentace).** Do § 5.1 invariant, který říká, že se
uzavírá **deklarovaná extenze skupiny včetně její identitní closure**,
a že se uzavření **dědí dolů po `subset`**, ne nahoru. A výslovně: je to
**lokální** uzávěr znalosti, globální svět zůstává otevřený —
`¬member(x,g)` neříká, že `x` neexistuje.

## P‑4 · Co posudek přidává mimo P0

- **A‑26 (P1):** místo „conBond4 je PTIME" formulovat *„pro pevně
  omezenou aritu, hloubku termů, délku role‑chainů a počet strat je
  evaluace polynomiální v datové velikosti"*. Míří na totéž místo v § 5.6
  jako A‑22 z dodatku O — **sloučit do jednoho průchodu**.
- **A‑27 (P2):** dashboard metrik místo jediného čísla; z navržených je
  nejcennější **Unknown precision** — jestli `U` opravdu znamená
  nedostatek důkazu, a ne přehnanou opatrnost. To dnes neměříme vůbec.
- **Coreference:** evidovat rozhraní (zmínka, kandidáti, evidence,
  hypotéza, potvrzení) už teď, implementovat později. **Shoduje se
  s dodatkem M** — `NodeBinding` a `awaiting='odkaz'` už tu jsou, takže
  je to z větší části hotové.

## P‑5 · Kde posudek potvrzuje naše vlastní závěry

Zákaz skolemizace jako *cautious reasoning* (ne chybějící chase);
`complete` mimo pevný bod; `before` s `InconsistentOrder` odděleným od
`CONFLICT`; kaskáda místo LLM→AST; vlastní jádro obhájené
**deterministickým důkazem**. To vše jsme rozhodli dřív a nezávisle —
posudek je potvrzením, ne opravou.

**Jeho nejlepší věta je definice identity systému** a stojí za převzetí:
*„conBond4 není primárně reasoner. Je to proof‑producing epistemic
reasoner s dialogově modifikovatelnou znalostní bází."* A z ní plyne
i to, co v tomhle projektu opakovaně vychází jako nejcennější: řetěz
**inference → provenience → epistemický verdikt → vysvětlení → další
tah** je ta vlastnost, kvůli které vlastní jádro dává smysl.

