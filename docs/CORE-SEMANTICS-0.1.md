# conBond4 — Core Semantics 0.1

**Verze jádra:** 0.1.70 · 16. 8. 2026
**Status:** návrh finálního znění formálního jádra. Verzované; změna
gramatiky nebo evaluace jen vědomým rozhodnutím (I‑13, I‑16).

| Verze | Změna | Schváleno |
|---|---|---|
| 0.1.0 | výchozí znění | 13. 8. 2026 |
| 0.1.1 | § 7 — třístupňový `canonical_key`; listy jsou fakta i pravidla | 14. 8. 2026 |
| 0.1.2 | § 5.1 — kontrapozice `member̄*` přes `subset*`; § 13 T32–T34 | 14. 8. 2026 |
| 0.1.3 | § 5.1 — uzávěr `complete*` (`U → N`); § 5.4 — scelení identity je odmítnutelné, pořadí těla; § 13 T35–T39 | 14. 8. 2026 |
| 0.1.4 | § 2 — konstruktory `AND` / `OR` / `DIFF` jako termy; § 5.2.1 — distribuce `D1`/`D2` nad algebraickými termy; § 13 T40–T44 | 14. 8. 2026 |
| 0.1.5 | § 5.1 — uzávěr `before*` nad `Time` (nereflexivní), cyklus v uspořádání jako otevřená položka; § 13 T45–T48 | 14. 8. 2026 |
| 0.1.6 | § 5.1 — hrana identity ve SPORU se v uzávěru nepoužije (`same_as*` i přemostění ostatních uzávěrů); přímá otázka dál vrací `CONFLICT`; § 13 T49–T52 | 14. 8. 2026 |
| 0.1.7 | § 5.4 — `PROTECTED_HEADS`: zákaz v hlavě širší než jádrová množina, přibyly `name` a role; § 3.2 intervalová aproximace + axiom o existenci bez uzlu; § 5.1 `complete` jako epistemická deklarace; § 5.6 charakteristika systému; § 7 minimalita podle definované metriky; § 13 T53–T55 | 14. 8. 2026 |
| 0.1.8 | § 5.4/10 — tělo se při `attach` normalizuje do kanonického bezpečného pořadí, jinak `UnsafeRule` u ZÁPISU; `REQUIRES_BOUND` jako jeden seznam pro zápis i evaluátor; normalizace neobchází bod 7; § 13 T56–T58 | 14. 8. 2026 |
| 0.1.9 | § 5.4/10 — vázanost se hledá REKURZIVNĚ i uvnitř algebraického termu (`substitute` do něj sestupuje), zakázat algebraický term jako takový by ale bylo přestřelené: rozhoduje vázanost, ne tvar; § 13 T59 | 14. 8. 2026 |
| 0.1.10 | § 5.2.1 — napřed RECALL z uzávěrového indexu, teprve pak zákony: zapsaný `subset` s algebraickou stranou se přeskakoval a přímá otázka na vlastní fakt vracela `U`; § 13 T60 | 14. 8. 2026 |
| 0.1.11 | § 3.3 — NEGACE OBRACÍ MONOTONII: pod negací sedne dotaz `∃` na fakt `∀` s touž povinností `subset` jako kladné `∀×∀`; kladná buňka `∀→∃` zůstává `U`, protože by potřebovala existenční import; § 13 T61 | 14. 8. 2026 |
| 0.1.70 | § 5.2 — částečný zápis se ptá OBOJÍHO, co vynechávám i ODKUD: pod záporným přísudkem se monotonie obrací (`¬(P∧Q)` ⊬ `¬P`), takže záporná věta se částečně nezapíše; § 13 T117 |
| 0.1.69 | § 5.2 — ČÁSTEČNÝ ZÁPIS: zapíše se to, čemu systém rozumí, nepojmenovaná okolnost zůstane otevřená; vylučuje TŘÍDA OPERÁTORŮ z lexikonu (odvolatelná data), doplnění částečný výrok ODVOLÁ; § 13 T116 |
| 0.1.68 | § 12 — W-79 přeměřena PŘES VYNECHANOU ČÁST: rizikové jsou 3 věty ze 154 (zápor, podmínka, náhrada), ne 15 — slučovací okolnost dává po vynechání tvrzení SLABŠÍ, a to není nepravda |
| 0.1.67 | § 5.2 — účet se ptá na DOPLNĚK značek, ne na výčet slovních druhů (výčet minul 30 slov: `X`, `SYM`); § 12 — podklad k otázce, jestli se smí zapsat to, čemu systém rozumí |
| 0.1.66 | § 5.2 — ÚČET: jedno místo místo čtvrté záplaty. Němých slov v přečtených větách 471 → 28 (zbytek leží v podstromu druhé věty); doložka O-23 sjednocena s tím, co kód drží; § 13 T115 |
| 0.1.65 | § 5.2 — MATERIÁL Z VĚTY SE NESMÍ ZTRATIT MLČKY: přivlastnění je vidět ve TVARU zmínky a ztracený člen se hlásí i s tím, co se do něj složilo (282 tokenů korpusu bylo úplně bez zmínky); § 13 T114 |
| 0.1.64 | § 5.2 — PŘÍVLASTEK SE SKLÁDÁ I POD ZTRACENOU HLAVOU (257 členů ve 126 větách přestalo být falešnou otázkou) a velkým písmenem psaný přívlastek je ČÁST JMÉNA; skládání netvrdí `subset`; § 13 T113 |
| 0.1.63 | § 12 — ROZKLAD PŘÍVLASTKU VE JMENNÉ FRÁZI: tři různé věci (část jména 18, přivlastnění 11, přívlastek třídy ~513), a u té třetí rozbor odpověď NEMÁ — „terapeutický pes“ a „bývalý prezident“ jsou znak za znakem stejné |
| 0.1.62 | § 5.2 — CO SE NAUČÍ, MUSÍ JÍT NAJÍT: spouštěč se stavěl bez `lemma`, takže se vzor uložil jako strukturní a signatura s lemmatem ho nenašla — táž věta se ptala podruhé. 47 tvarů z 206 se tím nikdy nenaučilo natrvalo; § 13 T112 |
| 0.1.61 | § 5.2 — UZEL SE ZKRÁCENÝM JMÉNEM SE NEZAPÍŠE MLČKY: předložkový druhý díl („Rožnov pod Radhoštěm“) se složit nedá, ale hlásí se jako NEÚPLNÉ JMÉNO a zápis blokuje; falešná otázka na roli dílu zmizela; § 13 T111 |
| 0.1.60 | § 5.2 — UZEL SE NEJMENUJE ZKRÁCENĚ: druhý díl jména v holém genitivu (`nmod` pod `PROPN`) se skládá, takže „v Hradci Králové“ dá `·Hradec_Králové`, ne `·Hradec`; § 13 T110 |
| 0.1.59 | § 5.2 — ODVOLAT VĚTU JDE CELOU: jednotkou odvolání je PROMLUVA, ne výrok. Věta, která zapsala dvě tvrzení, se odvolávala po půlkách a báze druhou tvrdila dál; § 13 T109 |
| 0.1.58 | § 5.2 — VÍC ČLENŮ V JEDNÉ ROLI SE NEROZDĚLÍ MLČKY: souřadný člen je druhý uzel téže role, ale distributivní čtení v rozboru NENÍ, takže se systém ptá (`→&`). 58 vět dostalo tu otázku; § 13 T108 |
| 0.1.57 | § 5.2 — PO ODPOVĚDI NESMÍ ZMLKNOUT ZÁVISLÝ ČLEN TOHO, CO BYLO PRÁVĚ POJMENOVÁNO: patro přívlastku běželo před patrem ztracené role. Změřeno 5 → 0; § 12 (rozklad souřadného členu), § 13 T107 |
| 0.1.56 | § 5.2 — CO O VĚTĚ PLATÍ, SE NEČTE Z TAHU, KTERÝ NA NI ODPOVÍDÁ: odpověď na jednu otázku rušila ostatní a značka `✓` vznikala z prázdné stopy. Změřeno: 178 vět se ptá dál (bylo 21), překlop ◐→✓ nula (bylo 9); § 13 T106 |
| 0.1.55 | § 5.2 — ŽÁDNÝ TAH NEPOTVRDÍ UČENÍ, ANIŽ ŘEKNE, CO SE VE VĚTĚ ZMĚNILO: `→@` se přijímal s „✓ naučeno“ i tam, kde čtení zůstalo beze změny. Příčina je jediná a změřená — SRÁŽKA s obsazenou rolí; § 13 T105 |
| 0.1.54 | § 12 — ODSTAVEC PŘEMĚŘEN (7 tahů / 3 bez tahu, bylo 7/6): tři překážky z #105 zavřené, dvacátá druhá doména se přesto NEPÍŠE. Nový nález: `si` zůstává rolí s uzlem „se“, takže věta neprojde zakotvením ani po odpovědi na všechno |
| 0.1.53 | § 5.2 — NA OTÁZKU „JE TOHLE SPONA?“ ODPOVÍDÁ JEDNO MÍSTO: čtyři porovnání `cop` přesným řetězcem svedena do `is_copula`. Projev 0 (61 spon, 0 podtypů) — oprava RIZIKA, ne chování; § 13 T104 |
| 0.1.52 | § 5.2 — KVANTIFIKÁTOROVÉ ZÁJMENO KVANTIFIKUJE, NEODKAZUJE: „vše“ dostávalo otázku „na koho odkazuje“, která o něm tvrdila nepravdu. `PronType` z rozboru: `Tot`→`∀`, `Ind`→`∃`, `Neg` je pojmenovaná mez; § 13 T103 |
| 0.1.51 | § 5.2 — KONATEL TRPNÉ VĚTY DOSTANE JMÉNO: holý `Ins:arg` pod `Voice=Pass` je `kdo`. Rozhodují DVĚ značky naráz, protože instrumentál je taky NÁSTROJ; § 12, § 13 T102 |
| 0.1.50 | § 5.2 — TÁŽ ROLE, AŤ JE PODMĚT VYSLOVENÝ, NEBO NE: pro‑drop u trpného rodu vyrábí `co`, ne `kdo`. Dvě jména pro touž roli rozpadala bázi na dvě poloviny a mezera tvrdila „nikdo to neřekl“ o výroku, který v ní ležel; § 13 T101
| 0.1.49 | § 5.2 — VLASTNÍ JMÉNO JE KONKRÉTNÍ, AŤ STOJÍ KDEKOLI: `·` dostávalo jen jako `nsubj`, u `nsubj:pass` a `Ins:arg` se systém ptal znovu, takže „Byl Karel Čapek pohřben na Vyšehradě?“ nedostalo odpověď, ačkoli fakt v bázi ležel. Je to vlastnost JMÉNA, ne role; obecné jméno se dál ptá; § 13 T100
| 0.1.48 | § 3.2 — DATUM VNOŘENÉ POD JINÝM JMÉNEM se skládá taky („dne 25. prosince 1938“ → `den_25._prosinec_1938`), ale JEN takový `nmod`, který sám nese datové části — rozlišuje se podle toho, CO pod hlavou visí, ne jak se jmenuje. A pravidlo je O ŘADOVÉ ČÍSLOVCE, ne jen o datu: „1. místo“ → `1._místo`, což slovem systém dělal vždycky; § 13 T99
| 0.1.47 | § 3.2 — CELÝ ČASOVÝ ÚDAJ JE JEDNA ZMÍNKA: „9. ledna 1890“ dá `9._leden_1890`. Řadovou číslovku pozná TEČKA V ZÁPISU — rozbor „9.“ a „92“ nerozliší ničím jiným, takže rozeznat je podle hlavy by znamenalo mít v kódu seznam měsíců. Počet ani množství slovem tudy neprojdou; § 13 T98
| 0.1.46 | § 3.2 — LETOPOČET JE SOUČÁST ZMÍNKY: „v roce 1986“ a „v roce 1990“ dávaly OBĚ uzel `rok`, tedy jeden uzel pro všechny roky, a číslo se hlásilo jako ztracený člen, ačkoli z věty nevypadlo. Skládá se do `rok_1986`; POČET („92 lidmi“) tudy neprojde; § 13 T97
| 0.1.45 | § 5.2 — DRUHÁ VĚTA S VLASTNÍM PODMĚTEM si nic nepůjčuje a UZEL VZNIKÁ Z NĚJ; v hlášení je to vidět, protože u sdíleného podmětu se přenáší TÁŽ zmínka a tady vzniká DRUHÁ (M‑2). Role, které patro vyrobí, dostanou kvantifikátor — jinak se druhá věta nezakotví; § 13 T96
| 0.1.44 | § 5.2 — ZAPSANÁ VĚTA VŽDY POJMENUJE SVOU NEVZATOU PŮLKU: podmínka je „není přečtená“, ne „má vlastní podmět“ — jinak vznikne TICHÝ ČÁSTEČNÝ ZÁPIS. A patro souřadnosti běží AŽ ZA kvantifikátorem, protože se půjčuje HOTOVÁ role; do té doby se druhá věta nikdy nezapsala; § 13 T95
| 0.1.43 | § 5.2 — DRUHÁ VĚTA SE SDÍLENÝM PODMĚTEM se čte a zapisuje ZVLÁŠŤ: podmět se BERE z první věty téže promluvy a v hlášení je řečeno odkud; kopíruje se táž zmínka, nezakládá se druhá. Věty, kde má druhá vlastní podmět (17 z 35), se dál jen hlásí; § 13 T94
| 0.1.42 | § 5.2 — SOUŘADNÝ DRUHÝ PŘÍSUDEK je DRUHÁ VĚTA, ne ztracený člen: „a brzy musel znovu ulehnout“ není člen první věty a ptát se na jeho roli je výzva dosadit druhou větu jako člen první. Číst se to zatím nezačne — PŘIZNANÁ MEZ. Změřeno 35 vět z 238, z toho 18 sdílí podmět a 17 má vlastní; § 13 T93
| 0.1.41 | § 6.8 — ZVRATNÉ ZÁJMENO neodkazuje ven z věty: systém se u „si“ ptal na odkaz a pak tu odpověď neměl kam přijmout, protože role čeká na kvantifikátor. Otázka bez tahu je horší než mlčení; rozhoduje `Reflex=Yes` z rozboru; § 13 T92
| 0.1.40 | § 5.2 — na otázku „je tohle přísudek?“ odpovídá v kaskádě JEDNO místo: stráž nadpisu se ptá `_is_predicate` místo vlastní užší kopie, která nesla W‑48 i W‑47 naráz. Devátá instance téže rodiny; § 13 T91
| 0.1.39 | § 5.2 — NADPIS SPLYNULÝ S VĚTOU se pojmenuje: „Obezita: Domácí mazlíčci trpí nadváhou.“ má kořenem nadpis a skutečná věta pod ním visí jako `appos`. Číst se to nezačne — přesadit kořen je výrok o TEXTU, ne o rozboru, a rozdělit dvojí text je práce segmentace; § 13 T90
| 0.1.38 | § 5.2 — DVA ČLENY, JEDNO JMÉNO: srazí‑li se dvě okolnosti na téže roli, ani jedna ji nedostane a obě padnou na svůj TVAR — věta se čte a ptá místo aby zmizela. Když tvary nerozliší ani to, hlášení řekne PROČ; „nemá ani jeden člen“ byla nepravda o textu. Pohlcený přívlastek není nepojmenovaný člen — „Úrazy způsobené pády.“ je JMENNÁ FRÁZE; § 13 T89 | 15. 8. 2026 |
| 0.1.37 | § 12/1 — JEDNA PODMÍNKA, JEDNA ODPOVĚĎ: role, jejíž jméno zůstalo TVAREM, zastaví zápis VŽDY, ne jen u vedlejší věty. „Petr bydlí v Praze.“ se zapisovala i s rolí `v+Loc/Geo` a po odpovědi `→@` znovu — dva výroky o téže větě. Naučené jméno („proč“) tvar není a zapisuje se dál; rozhoduje značka od toho, kdo roli vyrobil, ne podoba řetězce; § 13 T88 | 15. 8. 2026 |
| 0.1.36 | § 12/1 — SIGNÁL Z ROZBORU DĚLÍ TVAR: `v+Loc` slepoval „v Praze“ (místo) a „v roce 1935“ (čas), takže jedno naučené mapování muselo být u jedné z nich špatně. Tvar se dělí podle `NameType=Geo` a letopočtu jako dítěte — obojí z parseru, ne ze seznamu slov. Signál NEURČUJE jméno role (to plyne z předložky a pádu) a signálovaný tvar NEDĚDÍ obecný, čímž mizí `digitalizovaný(kudy:rok)`. 26 ze 42 signál nemá a dál se ptají; § 13 T87 | 15. 8. 2026 |
| 0.1.35 | § 12/1 — TRPNÝ PODMĚT JE PATIENS: role `co` plyne STRUKTURÁLNĚ z podtypu `nsubj:pass`, který stojí v rozboru, ne z naučeného vzoru. Byla to třetí nejčastější otázka „co znamená role X“ (19 z 250) a nikdy to nebyla otázka o významu. Když je `co` obsazené, patro se ZEPTÁ vlastní otázkou a ZASTAVÍ ZÁPIS (1 věta z 19); agens se rolí nestává; § 13 T86 | 15. 8. 2026 |
| 0.1.34 | § 3.2 — přívlastek je jen HOLÝ genitiv (předložková fráze je okolnost) a táž podmínka platí i v konstrukci jádrové relace; § 3.2 — genitivní přívlastek se páruje PŘES TOKEN, ne přes lemma (zmínka ve čtení je složená), a je BUĎ přívlastek, NEBO role, ne obojí: u spony je jmenná část kořenem, takže její genitiv je jeho dítě. Výjimkou je genitiv, který si nárokuje ČEKAJÍCÍ jádrová relace. A pro‑drop bere jako zmínku NOSITELE LEMMATU PŘÍSUDKU, ne kořen — u spony byl kořenem jmenná část a týž token ležel ve čtení dvakrát pod dvěma jmény; § 13 T84 | 15. 8. 2026 |
| 0.1.33 | § 12 — ROZHODNUTÍ PŘED STAVBOU u jmen rolí, změřené: „`v+Loc` → `kde`“ rozbor rozhodne jen ve 38 % (5× `NameType=Geo`, 11× letopočet, 26× nic); sort filleru použít nejde, protože plyne z role (kruh); z prvních tří tvarů zdi je 32 z 83 výskytů něco jiného než jméno role — 13 nerozpoznaných genitivních přívlastků a 19 trpných podmětů. ŽÁDNÁ ZMĚNA CHOVÁNÍ | 15. 8. 2026 |
| 0.1.32 | § 6.8 — `→∈` se NEPTÁ „ano/ne“, ptá se na DRUH: POVOLÁNÍ se zapíše, ÚŘAD DRŽENÝ V ČASE ne, protože bezčasé `member` by platilo šíř, než co věta říká. Z rozboru se to rozeznat nedá, rozhoduje ČLOVĚK. Změřeno: ze 39 zmínek titulu visí čas na titulu u čtyř a všechny čtyři jsou životní data v závorce, u úřadů NULA — není to úloha o čase v jádře. Tři stavy nabídky mají tři různé hlášky; § 13 T82, T83 | 15. 8. 2026 |
| 0.1.31 | § 6.8 — `→∈` je POTVRZENÍ, takže BEZ NABÍDKY SE ODMÍTNE (`✗`). Bez věty by v bázi ležel výrok s proveniencí titulu a s hláškou o textu, který nikdo neřekl. Potvrzený titul teď CITUJE VĚTU přímo v hlášení; odmítnutý tah nabídku nespotřebuje; § 13 T81 | 15. 8. 2026 |
| 0.1.30 | § 3.2, § 6.8 — TITUL NESE TVRZENÍ: „básník Josef Hora“ říká i to, že je básník. NABÍDNE SE a nezapíše — ze 71 zmínek v korpusu je 29 povolání, 24 úřad držený v čase a 18 příbuzenství, a tvar je u všech tří týž. Dokud se nepotvrdí, je verdikt `U`, ale důvod už není „nikdo to neřekl“; nový tah `→∈` a nový důvod `STATED_UNDECIDED` v rozkladu `U`; § 13 T80 | 15. 8. 2026 |
| 0.1.29 | § 3.2 — titul musí být v JEDNOTNÉM čísle: „bratří **Čapků**“ je SKUPINA dvou lidí, ne jedni bratři jménem Čapka, a uzel `·Čapka` by byl člověk, který neexistuje. Skupinu z téhle stavby jádro neumí a nevyrobí ji (W‑54); § 13 T79 | 15. 8. 2026 |
| 0.1.28 | § 3.2 — jméno pod OBECNÝM jménem („básník **Josef Hora**“) je TEN ČLOVĚK: zmínka je `Josef_Hora`, titul zůstává v `form` a NESKLÁDÁ SE. S identitou se přesouvá i KVANTIFIKÁTOR — jinak by z věty o jednom člověku vyšlo `∀Josef_Hora` a vada by se jen přestěhovala. „Město Praha“ má `nmod`, ne `flat`, takže se nemění; § 13 T78 | 15. 8. 2026 |
| 0.1.27 | § 3.2 — do jména se skládá JEN `flat`: `appos` je JINÁ ZMÍNKA téže věci, a když se skládala, vznikl uzel `Karel_Čapek_Karel` — jméno, které v textu nikdo nenese. Identita se z apozice NEDOSAZUJE („Karel Čapek, spisovatel“ je role, ne druhé jméno); § 13 T77 | 15. 8. 2026 |
| 0.1.26 | § 3.2 — VÍCESLOVNÉ JMÉNO je JEDEN UZEL: „Karel Čapek“ se skládá do lemmatu, ne zahazuje. Dřív se věta zapsala o uzlu `Karel` — nebyla to ztráta členu, byl to ZÁPIS O JINÉM UZLU, a „Karel Čapek“ s „Karlem Poláčkem“ tiše splývali. K tomu hlídka výchozího lexikonu sedí na `run`, ne na `replay`, a hláška jde do přepisu; § 13 T76 | 15. 8. 2026 |
| 0.1.25 | § 10 — ŽURNÁL NESE OTISK VÝCHOZÍHO LEXIKONU: determinismus platí od 0.1.24 jen podmíněně (týž žurnál a týž výchozí stav), ale který to byl, žurnál neříkal. Otisk se razí na PRVNÍ tah a při neshodě se přehrání NEZASTAVÍ — lexikon se legitimně rozrůstá — ale ŘEKNE SE to; tiché přehrání je zakázané; § 13 T75 | 15. 8. 2026 |
| 0.1.24 | § 10 — ŽURNÁL NEREPRODUKUJE SEZENÍ SÁM: tahy, které RE-ČTOU (`→@`), nesou text a čtou ho lexikonem, který v tu chvíli platí, ale potvrzené tvary domény v žurnálu nikdy nebyly. `Session.replay` proto bere LEXIKON jako pojmenovaný parametr a stará smlouva „lexikon není parametr“ se přepisuje — předpověděla si to sama; § 13 T74 | 15. 8. 2026 |
| 0.1.23 | § 9 — ROLE BEZ JÁDROVÉHO JMÉNA ZASTAVÍ ZÁPIS: patro pro vedlejší větu udělalo ze ztraceného členu ROLI, ale zábranu zápisu mu nedalo, takže odpověď `→@` zapsala větu PODRUHÉ — jednou s povrchovým jménem role, podruhé s naučeným, a ten první výrok by nikdo neodvolal; § 13 T73 | 15. 8. 2026 |
| 0.1.22 | § 5.2 — PODMĚT VYJÁDŘENÝ CELOU VĚTOU (`csubj`) je VYSLOVENÝ podmět: tvrdit o „Je jasné, že Jan přišel.“, že podmět nemá, je nepravdivý výrok o textu, a systém na jeho základě zval člověka dosadit podmět tam, kde jeden stojí. Mlčet by bylo taky nepřesné, takže se řekne PŘESNĚ TO — rozdíl mezi „neřečeno“ a „řečeno, neumím“; § 13 T72 | 15. 8. 2026 |
| 0.1.21 | § 5.2 — PŘÍSUDEK SE POZNÁ ZE STRUKTURY, ne ze slovního druhu: trpná věta má kořen `ADJ` a pomocné sloveso pod ním jako `aux:pass`, takže výčet `(VERB, AUX)` na ni byl slepý a zapisovala se BEZ PODMĚTU — jako fakt o nikom. Potřetí táž třída jako 0.1.18 (rysy řetězcem) a W‑47 (deprel řetězcem); § 13 T71 | 15. 8. 2026 |
| 0.1.20 | § 5.2 — u KOORDINOVANÉHO PODMĚTU je řídícím členem CELÁ KOORDINACE: koordinace, která SČÍTÁ a jejíž přísudek stojí ZA podmětem, žádá MNOŽNÉ číslo. Pravidlo zúžilo MĚŘENÍ — disjunkce („či“) a přísudek před podmětem mají jednotné číslo právem. Pravidlo je kladné — „Petr a Pavel četl knihu.“ padá dál. ROD SE U KOORDINACE NEOVĚŘUJE a je to PŘIZNANÁ MEZ: čeština ho řeší pravidly (muž + žena → mužský životný), ne průnikem; § 13 T70 | 15. 8. 2026 |
| 0.1.19 | § 5.2 — u KVANTIFIKOVANÉHO PODMĚTU se shoda počítá proti KVANTIFIKÁTORU, ne proti jménu: „několik měření … podpořilo“ žádá přísudek ve STŘEDNÍM JEDNOTNÉM. Pravidlo je KLADNÉ, ne výjimka — „Několik hostů přišli.“ padá dál. Řídící člen se čte z jmenovky `det:numgov`, ne ze seznamu slov; § 13 T69 | 15. 8. 2026 |
| 0.1.18 | § 5.2 — SHODA SE POROVNÁVÁ PRŮNIKEM HODNOT, ne rovností řetězce: rys, který UD uvede jako množinu (`Plur,Sing`), je přiznaná víceznačnost tvaru, ne konjunkce dvou tvrzení. Kontroluje se číslo I ROD — bez rodu by průnik propustil „Psi byla“. Na encyklopedickém korpusu klesla třída morfologie z 29/238 na 10/238; § 13 T68 | 15. 8. 2026 |
| 0.1.17 | § 3.2 — VĚTA BEZ PODMĚTU se nezapíše DEKAPITOVANÁ: podmět v predikaci vznikne a ČEKÁ, zmínkou je sám přísudek (rod a číslo jsou na něm) a kandidát se navrhuje z předchozí zakotvené věty. Rys s víc hodnotami (`Gender=Fem,Neut`) se porovnává PRŮNIKEM, ne rovností — vodítko kandidáty zužuje, nerozhoduje; § 13 T67 | 15. 8. 2026 |
| 0.1.16 | § 3.2 — KONTEXT TEXTU: sezení si pamatuje, co bylo zakotveno ve větě PŘEDTÍM, a z toho NAVRHUJE antecedenty zájmen. Je to nová INFORMACE, ne nová inference — shoda rodu a čísla kandidáty jen zužuje a systém se ptá i tehdy, když je kandidát jediný (I‑13). Dokud rozhodnutí nepadne, nezapisuje se nic; § 13 T66 | 15. 8. 2026 |
| 0.1.15 | § 8 — CITACE SAHÁ I NA ZAKOTVENÍ: odpověď, která se na uzel dostala přes JMÉNO, cituje i výrok, kterým je to jméno navázané. Zakotvení není premisa důkazu, ale bez něj by se dotaz netrefil, takže „odpověď o Honzovi doložená faktem o Janovi“ nechává spojnici jen v hlavě systému. K tomu `name` z české věty („X se jmenuje Y“) se stranami z DEPRELŮ a `ROLE_SORTS` pro relace, jejichž strany nejsou na téže ose; § 13 T65 | 15. 8. 2026 |
| 0.1.14 | § 5.1 — POPŘENÍ Z UZAVŘENÍ CITUJE I VÝČET, ne jen prohlášení: u jediné výjimky z I‑21 je „nad čím se zavíralo“ ta půlka, kterou čtenář potřebuje k ověření, a bez ní se závěr zkontrolovat nedá. K tomu uzavření světa Z ČESKÉ VĚTY jako NÁVRH (nikdy dosazení) a tah `!∀`, který se nic neučí a jde odvolat; § 13 T64 | 15. 8. 2026 |
| 0.1.13 | § 9 — ČEKAJÍCÍ KONSTRUKCE ZASTAVÍ ZÁPIS stejně jako čekající kvantifikátor, a tvar, na jehož význam se čeká, visí na PREDIKACI, ne ve stopě: stopa je log jednoho tahu, takže odpověď na cokoli jiného otázku zahodila a věta se zapsala jako obyčejný vztah `být` — zápis pod přiznanou neznalostí (INV‑11); § 13 T63 | 15. 8. 2026 |
| 0.1.12 | § 9 — `InconsistentOrder` jako pojmenované selhání ZÁPISU: hrana, která by uzavřela uspořádání do kruhu, se odmítá u `attach`, ne až u dotazu; k tomu IREFLEXIVITA `before` (smyčka na sebe je kruh o jednom uzlu) a otevřená otázka o `CONFLICT` variantě; § 13 T62 | 15. 8. 2026 |
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

**Je to INTERVALOVÁ APROXIMACE, ne kvantifikace přes možné světy**
*(upřesněno 14. 8. 2026, 0.1.7 — K‑1)*. Dvojice `(certain, possible)` je
dolní a horní odhad znalosti o jedné skupině a operace nad ní jsou
**sound interval propagation**: výsledek nikdy netvrdí víc, než z báze
plyne, a nikdy nevyloučí prvek, který v ní vyloučen není. Modální čtení
(„ve všech / v některém možném světě") by slibovalo víc — muselo by
kvantifikovat přes doplnění báze, a nic takového se tu nepočítá.

Přesnost obou mezí není stejná a je poctivé to říct:

* `certain` je **exaktní** — každý prvek v něm má vlastní důkaz.
* `possible` je **nadhodnocené**. Je to bezpečná strana: „možná tam je"
  smí být širší, než skutečnost, protože z toho neplyne žádné tvrzení.
  Opačná chyba by byla vážná.

`DIFF` je tím epistemický: prvek je *jistě* v rozdílu, jen když je
doloženo, že v subtrahendu není. Bez `complete(B)` nebo `neg_atom` na
konkrétní prvek zůstává jen v `possible` — a odpověď to musí říct
(I‑11): „vím, že není" × „nevím, že je".

**Existence nepotřebuje uzel** *(axiom, K‑3)*. `∃x P(x)` může platit,
aniž je v grafu `id(x)`. Existenční závěr říká „něco takového je", ne
„tenhle konkrétní uzel to je"; vyrobit uzel by byla skolemizace
v inferenci, kterou § 0/2 zakazuje. Individua vznikají **výhradně**
`attach`em, tedy lidským tahem. Proto taky `konkrétní × ∃G` v § 3.3
nesedí nikdy: dotaz na jmenovaný uzel se nedá uspokojit odpovědí
„nějaký existuje".

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

**Negace OBRACÍ MONOTONII** *(0.1.11 — B‑13)*. Tabulka výš popisuje
KLADNÉ atomy. Pod negací se jedna buňka mění:

```
¬P(∃Q)  ⪯  ¬P(∀F)      ⟸  subset*(Q, F)
```

Kladně by táž buňka potřebovala **neprázdnost** třídy — „platí to
o všech, tedy o nějakém" mlčky předpokládá, že nějaký je, a existenční
import § 3.2 nedovoluje. Pod negací ten předpoklad **mizí**: „o žádném
prvku `F` to neplatí" dává „o nějakém prvku `Q` to neplatí" i pro
prázdné `Q`, protože obě strany tvrdí NEPLATNOST, ne existenci. Důkazní
povinnost je táž jako u kladného `∀ × ∀` — dotaz smí být UŽŠÍ, nikdy
širší.

**Kladná buňka `∀ → ∃` zůstává `U`.** Doplnit ji by byl přesně ten
existenční import, který se tady zakazuje.

**Rozsah negace vůči `∃` roli je OTEVŘENÁ OTÁZKA** *(W‑14)*. `¬P(∃F)` jde
číst jako `¬∃x. P(x)` i jako `∃x. ¬P(x)`; tenhle dodatek to
**nerozhoduje** a rozhodovat mimochodem nesmí — je to změna § 3.3, tedy
věc vědomého rozhodnutí (I‑13). Zapsaná buňka platí při obojím čtení,
protože obě strany mluví o TÉŽE množině.


### 5.1 Jádrové uzávěry — jediné místo s rekurzí

Implementované jednou v interpretu, neroszšiřitelné učením:

```
subset*    reflex.-tranz. uzávěr subset                    Group
member*    member(x,A) ∧ subset*(A,B) ⇒ member(x,B)        E × Group
member̄*    member̄(x,B) ∧ subset*(A,B) ⇒ member̄(x,A)        E × Group
contains*  reflex.-tranz. uzávěr contains                  Place
within*    obsažení intervalů                              Time
before*    TRANZITIVNÍ uzávěr before, NEreflexivní          Time
same_as*   reflex.-symetr.-tranz. uzávěr (jen pohled, § 8) E
           — hrana ve SPORU se nepoužije (viz níž)
distribute D1/D2 (§ 5.2)
```

Pro naučená pravidla jsou to **primitivní predikáty stratu 0**, ne uzly
dependency grafu. Monotónní, nad konečnou množinou uzlů, negenerující —
pevný bod v ≤ |V|² krocích.

**Sporná hrana identity se nepoužije** *(doplněno 14. 8. 2026, 0.1.6)*.
Je‑li aktivní `same_as(A,B)` **i** `¬same_as(A,B)`, hrana `A—B` do
uzávěru nevstoupí — ani do `same_as*`, ani do přemostění `subset*`,
`contains*`, `within*` a `before*`.

Důvod je epistemický, ne technický. Dokud spor trvá, **báze neví**,
jestli jsou `A` a `B` tíž; pustit fakty přes takovou hranu znamená
vybrat si mezi dvěma neslučitelnými tvrzeními a nikomu to neříct, což je
přesně tichá volba měnící význam (I‑1). Odpověď má proto vyjít `U` a nést
mezeru, která spor pojmenuje (I‑14).

Dvě vlastnosti, které se nesmí ztratit:

1. **Odebírá se POUŽITÍ hrany, ne výrok.** Přímá otázka `same_as(A,B)?`
   dál vrací `CONFLICT` s oběma důkazy — spor je skutečný a hlásí se
   (I‑3). Kdyby zmizel i z přímé odpovědi, systém by ho zametl.
2. **Nezáleží na pořadí zápisu** (I‑4): popření smí ležet až za tvrzením.
   Symetrie platí — `¬same_as(A,B)` popírá i `same_as(B,A)`.

Odvolání jedné strany sporu hranu **vrací do hry**; spor je stav báze,
ne trvalá známka.

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

**`complete(g)` je EPISTEMICKÁ DEKLARACE, ne odvozený fakt**
*(upřesněno 14. 8. 2026, 0.1.7 — K‑4)*. Neříká nic o světě; říká, že
mluvčí o té skupině **ví všechno**. Je to řečový akt („a to je všechno"),
tedy tvrzení o stavu znalosti, ne o množině — a proto:

* zapisuje se výhradně `attach`em, tedy lidským tahem;
* naučené pravidlo ho nesmí mít v hlavě (`PROTECTED_HEADS`, I‑16) —
  odvodit úplnost z neúplných dat je právě ten předpoklad uzavřeného
  světa, který § 0 zakazuje;
* vyhodnocuje se **při dotazu**, ne v pevném bodě, viz níž.

Rozdíl je vidět na tom, co se stane po odvolání: `revoke(complete(g))`
vrátí skupinu do otevřeného stavu okamžitě, protože se z ní nikdy nic
nematerializovalo. Kdyby byl `complete` odvozený fakt, zůstaly by po něm
závěry, které už nemají oporu.

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

**Uzávěr `before*`** *(doplněno 14. 8. 2026)* — uspořádání na časové ose
(§ 3.6), striktně nad sortem `Time`. Na rozdíl od ostatních uzávěrů
**není reflexivní**: „pondělí je před pondělím" neplatí, a kdyby uzávěr
reflexivitu přidal, splynulo by „dřív" s „nejpozději".

„Po" je `before` obráceně, „během" je `within`. **`překrývá` zůstává mimo**
— vyžadoval by intervaly s koncovými body, což je jiná a větší věc.

> **OTEVŘENÁ POLOŽKA — cyklus v uspořádání.** `before(a,b)` a `before(b,a)`
> jsou nekonzistentní a tranzitivní uzávěr z nich odvodí `before(a,a)`,
> tedy „všechno je před vším". Zapojení na `CONFLICT` s oběma důkazy je
> **nový druh inference v jádře a čeká na rozhodnutí**.
>
> Do té doby platí konzervativní default: uzávěr cyklus **detekuje**
> (silně souvislé komponenty grafu uspořádání) a na dotaz o uzlu, který na
> cyklu leží, **netiše neodpoví** — hlásí `InconsistentOrder` s důvodem,
> jako `EvaluationError` u nevázaných rolí. Cyklus jinde na ose
> nesouvisející otázku neblokuje; jedna chyba v kalendáři nemá
> znepoužitelnit celou osu.

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

**Napřed RECALL, teprve pak odvození** *(0.1.10 — G‑3)*. Zákony z bodu
(b) se použijí teprve tehdy, když se `sub ⊆ sup` nenajde přímo
v uzávěrovém indexu. Do téhle opravy se index při algebraické straně
přeskakoval úplně, takže `attach(subset(auto, A AND B))` se uložil, index
tu hranu měl — a přímá otázka na týž fakt vrátila `U`.

Rozdíl, na kterém to stojí: **neúplná sada zákonů je přiznaná mez**
(nedokážu odvodit všechno, a chybějící důkaz dá `U`, nikdy falešné `A`).
**Ignorovat vlastní bázi mez není.** Systém, který odpoví „nevím" na
tvrzení, které mu člověk právě řekl a které má uložené, neselhal
v odvozování, ale v paměti.

Zákony se tím neobcházejí — přímý dotaz jen předchází. Kde platí obojí,
vrací se ten přímý, protože je kratší a minimalita důkazu je § 7.
`member*` se indexu ptal odjakživa; nesouměrný byl `subset*`.

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
znamenala rozhodovací proceduru nad celou algebrou; ta je při konečnosti
z § 6.3 možná, ale je to samostatné rozhodnutí, ne vedlejší efekt této
změny.

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
8. omezená hloubka termů a vnoření vztahů (parametr gramatiky, default 1);
9. **hlava nesmí být chráněný predikát** (`PROTECTED_HEADS`, I‑16).

**Co se nesmí odvozovat** *(rozšířeno 14. 8. 2026, 0.1.7 — A‑7)*.
Zákaz v hlavě je **širší** než množina jádrových uzávěrů a stojí na
dvoudílném kritériu:

> Predikát, který **mění uzávěr** nebo **uzavírá svět**, a k tomu
> **jazyk, kterým se fakty zapisují**, nesmí stát v nenegované hlavě
> naučeného pravidla.

První část je `KERNEL_PREDICATES` (`member`, `subset`, `contains`,
`within`, `before`, `same_as`, `disjoint`, `complete`, `name`) a je
**strojově odvozená**: je to přesně to, na co se ptá stavba uzávěrového
indexu. Druhá část jsou role (`role`, `role_∀`, `role_∃`, `role_·`) —
ty vznikají reifikací z toho, co člověk řekl, takže pravidlo s rolí
v hlavě nepřidává tvrzení, ale **přepisuje, jak se čte cizí, už
zapsaný fakt**. Uložený výrok se nezmění; změní se jeho význam.

**Jen na hlavu.** Role v TĚLE pravidla zůstávají povolené a stojí na nich
můstková pravidla dialogů A i „zmrzlina" — pravidlo smí roli **číst**,
nesmí ji vyrábět.

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

**Pořadí literálů v těle je implementační věc, ne význam**
*(14. 8. 2026, 0.1.8 — A‑24)*.

Jádrový predikát v těle vyžaduje, aby jeho vázanostní role byly vázané
v okamžiku, kdy na ně dojde řada — enumerace nad uzávěry ve F0 není
(§ 5.1). `subset(L2, L1)` se dvěma dosud nevázanými proměnnými skončí
chybou. Dokud se tělo bralo, jak bylo napsáno, znamenalo to, že **šest
permutací téhož pravidla dalo dvakrát `N` a čtyřikrát `EvaluationError`**
— a `attach_rule` přijal všech šest, takže chyba přišla až u některého
pozdějšího dotazu.

To je pro pravidlo naučené z dialogu neudržitelné: konjunkce je
komutativní, takže tvar, v jakém člověk pravidlo vysloví, nesmí určovat
jeho význam.

10. **tělo se při `attach` normalizuje do kanonického bezpečného
    pořadí**; neexistuje‑li takové pořadí, pravidlo se **odmítne při
    zápisu** (`UnsafeRule`), ne až při dotazu.

Normalizace je hladová a **kanonická, ne jen bezpečná**: mezi literály,
které lze v daném kroku vyhodnotit, se vybírá deterministicky podle
zápisu. Kdyby se bral první, který projde, lišily by se normální tvary
a s nimi kanonické důkazy (§ 7) — odpověď by byla táž, ale zdůvodněná
šesti způsoby.

**Které role musí být vázané, je jeden seznam** (`REQUIRES_BOUND`),
který čte zápis i evaluátor. Dvě kopie by se rozešly a poznalo by se to
na tom, že zápis pustí pravidlo, které vyhodnocení odmítne. `member` má
vázanou jen `group` — prvky skupiny se vyjmenovat **dají**, a právě
z toho žijí výčtové otázky.

**Vázanost se hledá i uvnitř algebraického termu** *(0.1.9 — G‑2)*.
Dosazení do `A AND X` **sestupuje** (§ 2), takže proměnná schovaná
v algebraickém termu potřebuje navázat úplně stejně jako proměnná
v kořeni fillera; jinak zůstane po dosazení neuzemněná hlava. Ptát se
jen na kořen znamenalo, že `h(a:X) ← subset(a AND X, b)` prošlo zápisem
a spadlo až u dotazu — táž vada jako výše, jen přesunutá z pořadí
literálů na tvar termu. **Zakázat algebraický term v jádrovém literálu
by ale bylo přestřelené**: `h(a:X) ← member(X, g) ∧ subset(a AND X, b)`
je v pořádku a projít musí. Rozhoduje vázanost, ne tvar.

**Normalizace neobchází bod 7.** Bezpečnost vázanosti a bezpečnost
negace jsou dvě různé podmínky. Negovaný literál **neváže nic**, takže
při uspořádávání smí přijít na řadu až tehdy, když jsou všechny jeho
proměnné vázané odjinud; pravidlo, jehož proměnná nemá jiného vazače než
negovaný literál, se přeuspořádáním „bezpečným" nestává a odmítne se.

Vyhodnocovací strategie se tím nemění. Pořadí uvnitř enginu zůstává
implementační věcí — jen přestává být vlastností významu.

### 5.5 Evaluace

```
K0    = aktivní explicitní fakta
K(i+1)= K(i) ∪ Consequences(jádrové uzávěry ∪ naučená pravidla, K(i))
K*    = nejmenší pevný bod
```

Bottom‑up pro uzávěr a verdikty. Top‑down (SLD) běží jako oddělený
modul `GapFinder` pro dotaz „Proč nevíš?" — vrací otevřené podcíle, ne
důkaz (§ 7).

### 5.6 Čím ten systém vlastně je *(doplněno 14. 8. 2026, 0.1.7 — K‑2)*

Dřívější odůvodnění rozhodnutelnosti se opíralo o příbuznost s monadickou
predikátovou logikou. **To se tímhle odstavcem nahrazuje**, protože je to
argument slabý i zbytečný: rozhodnutelnost tady neplyne z toho, čemu se
jazyk podobá, ale z toho, co má zakázané.

Přesná charakteristika:

> **Konečný typovaný stratifikovaný Datalog‑like systém** s uzávěrovými
> operátory stratu 0 a epistemickou vrstvou nad dotazem.

Rozhodnutelnost stojí na § 5.4: **žádné funkční symboly, žádná existence
v hlavě, konečná množina konstant.** Herbrandovo univerzum je tedy
konečné a pevný bod se v konečně mnoha krocích uzavře. Nic z toho není
vlastnost „monadičnosti"; role jsou vícemístné a systém přesto terminuje.

**„PTIME" má smysl jen s uvedeným parametrem**, jinak je to slogan.
Vzhledem k čemu:

| parametr | v čem roste |
|---|---|
| velikost báze `|K|` | polynomiálně — pevný bod přidává fakta, neubírá |
| počet pravidel | lineárně na kolo |
| **arita pravidla** | `|K|^v`, kde `v` je počet proměnných v těle — to je ta drahá dimenze, ne báze |
| hloubka termů | omezená parametrem gramatiky (default 1) |
| délka role‑chain | omezená, viz § 5.4/4 |
| scelení identity | uzávěr nad grafem `same_as`, `O(|V|·|E|)` |
| počet strat | konstantní násobek kol |

Epistemická vrstva (`K`, `U`, `DIFF`, `alt`, `bound`) běží **nad hotovým
pevným bodem** a nepřidává inferenci — proto se do téhle tabulky nepromítá
jinak než jedním průchodem výsledkem.

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
minimum podle třístupňového klíče.

**Nenárokuje se „minimální vysvětlení" v absolutním smyslu**
*(upřesněno 14. 8. 2026, 0.1.7 — K‑5)*. Kanonický důkaz je minimální
**podle níže definované syntaktické metriky** — počet listů, pak jejich
id, pak velikost stromu. Není to nutně to vysvětlení, které by člověk
označil za nejlepší, ani nejkratší v nějakém sémantickém smyslu; taková
metrika by musela vážit srozumitelnost jednotlivých kroků a nic
takového tu není definované.

Co se tedy tvrdí, a co ne:

* **tvrdí se** — výběr je deterministický (I‑4), nezávislý na pořadí
  zápisu i na pořadí průchodu pamětí, a nikdy nevybere důkaz, který
  obsahuje krok navíc oproti jinému dostupnému;
* **netvrdí se** — že je to pro čtenáře nejsrozumitelnější z možných
  vysvětlení.

Klíč:

```
canonical_key(P) = ( |listy(P)| , seřazená n-tice id listů , velikost stromu )
```

Pořadí stupňů není libovolné. Kdyby rozhodovalo jen lexikografické pořadí
id, vyhrával by důkaz s nižšími id bez ohledu na délku — „citron je citron
a citron je ovoce" by porazilo „citron je ovoce", pokud se přímý fakt
připojil později. To je právnicky platné a lidsky absurdní; první stupeň
proto vynucuje **krátkost v počtu listů**, druhý a třetí drží
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
InconsistentOrder odmítnutí hrany, která uzavírá pořadí do kruhu (§ 5.1)
```
**`InconsistentOrder` je selhání ZÁPISU, ne pád u dotazu** *(0.1.12 —
B‑16)*. `before` je STRIKTNÍ uspořádání; hrana, po které by vznikl
cyklus, se odmítá při `attach` a odmítnutí **jmenuje výroky, které ten
kruh tvoří**. Do téhle změny se taková hrana zapsala bez námitky
a rozbila se až PŘÍŠTÍ otázka — výjimkou, která utekla ze sezení ven.
To je nejhorší možná chvíle: báze je už v rozbitém stavu, člověk netuší
proč, a program nemá jak říct, co se stalo (I‑1). Selhání zápisu je
naproti tomu **tah dialogu**, na který jde odpovědět — třeba odvoláním
jednoho z výroků.

**Ireflexivita.** `before(X, X)` je kruh o jednom uzlu a odmítá se
stejně. Není to nová politika: celé H‑3 stojí na tom, že *„z cyklu by
uzávěr odvodil, že je všechno před vším"*.

**Konzervativní default H‑3 v uzávěru ZŮSTÁVÁ** jako druhá obrana —
dovnitř se dá dostat vnitřním zápisem, který používá `add_disjoint` pro
svou expanzi.

**Otevřená otázka** *(I‑13)*: druhá varianta — nechat zápis projít
a odpovídat na dotaz `CONFLICT` se dvěma důkazy — se **nerozhoduje**.
Odmítnutí u zápisu ji nevylučuje; jen brání tomu, aby se do toho stavu
dalo dojít nechtěně.

**Známá mez** *(W‑22)*: kruh jde uzavřít i **ze strany identity** —
`same_as`, které dva uzly sceluje, zábranu na hraně obejde. Z češtiny se
tam dnes dojít nedá (věta typu „Středa je pondělí." se čte jako spona
a systém se ptá, jestli jde o `member`, `subset`, nebo `disjoint`), a je
to zapsané jako mez, ne jako hotové: až se na to sáhne, ukáže se, jestli
zábrana patří NA HRANU, nebo NA STAV GRAFU.


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

**SMÍ SE ZAPSAT TO, ČEMU SYSTÉM ROZUMÍ? — PODKLAD, NE ROZHODNUTÍ**
*(kolo #134, 16. 8. 2026)*. Zápis je dnes VŠECHNO NEBO NIC: dokud ve
větě zbývá jediná otevřená věc, neuloží se nic. Ze 238 vět má 220
čtení a zapsaná je **1**; ze 219 nezapsaných nese 154 výslovný zákaz
`[NEZAPSÁNO: … (B‑19)]`.

**(a) CO TEN ZÁKAZ DRŽÍ — jedna příčina, ne pět.** Všech 154 drží
POVRCHOVÁ ROLE, tedy tvar bez jména. A rozhoduje tohle:

> **Ve všech 154 je nepojmenovaná role JEN OKOLNOST — ani jednou
> `kdo`, `co` nebo `jak`.** Nejčastěji `v+Loc` (50), `Gen` (18),
> `Dat:arg` (11), `k+Dat` (10), `na+Acc` (10).

Přísudek a jeho jádroví účastníci jsou tedy PŘEČTENÍ; chybí jméno
příslovečného určení.

**(b) DŮVOD Z B‑19 UŽ NEPLATÍ.** B‑19 zněla „zapsat teď a po odpovědi
znovu by uložilo DVA výroky o téže větě a ten první by nikdo
neodvolal". Od B‑26 (#125) má promluva RUKOJEŤ a `revoke_utterance`
bere zpět všechno, co ta promluva založila — ověřeno: „Karel Čapek
zemřel v Praze." po `→@` uloží 4 výroky, dotaz na celé tvrzení dá `A`,
`revoke_utterance` je vezme všechny a dotaz je zpátky na `U`, báze
prázdná. Překážku odstranilo jiné kolo a nikdo si toho nevšiml.

**(c) KDY BY ČÁSTEČNÝ ZÁPIS TVRDIL VÍC, NEŽ V TEXTU STOJÍ.** Vynechat
okolnost obvykle znamená říct MÍŇ, ne víc — a to je bezpečné. Není to
ale prázdná množina: **3 ze 154** nesou v té okolnosti slovo, které
MĚNÍ ROZSAH tvrzení („**kromě** bratří Čapků", „**jen** v tomhle
smyslu"). U nich by částečný zápis tvrdil něco silnějšího, než věta
říká.

> Podklad tedy zní: příležitost je velká (154 vět), překážka z B‑19
> padla, a riziko je malé, ale NENULOVÉ a má tvar — slovo měnící
> rozsah. **Rozhodnutí to nepředjímá**; kdyby se stavělo, musí se
> ta trojice řešit dřív než ostatních 151.

**PŘEMĚŘENO PŘES VYNECHANOU ČÁST** *(kolo #135)*. Reviewer chtěl SEZNAM,
ne číslo, a měřeno správně — tedy nad PODSTROMEM role, která by se
nezapsala — vychází jinak než z hrubého hledání po celé větě:

| co v té vynechané části stojí | kolik | co to udělá |
|---|---|---|
| slovo měnící rozsah (`pouze`, `kromě`, `také`, `i`, `již`…) | 15 | **nic** |
| z toho OMEZUJÍCÍ (`pouze`, `kromě`, `mimo`, `jen`) | 5 | **nic** |
| zápor, podmínka nebo náhrada (`nikoliv`, `pokud`, `místo`) | **3** | **mění pravdivost** |

**A tady se opravil i vlastní odhad.** Slovník „slov měnících rozsah"
byl špatné kritérium: „působil **pouze** pět měsíců" ENTAILUJE „působil",
a „patřili **kromě** bratří Čapků Masaryk…" entailuje „Masaryk patřil".
Vynechat okolnost u SLUČOVACÍHO čtení dá vždy tvrzení SLABŠÍ — a slabší
tvrzení není nepravda.

Nebezpečné je jen to, co pravdivost **obrací nebo podmiňuje**:

  · **zápor uvnitř okolnosti** — „…je dobré zdraví, **nikoliv** vlastnictví";
  · **podmínka** — „může mít dopad, **pokud** nejsou dobře chována";
  · **náhrada** — „pochází z ruského `ves mir`, **místo**…".

> Rizikové jsou tedy **3 věty ze 154**, ne 15 a ne 13. Ty tři se ze
> zápisu vylučují JMENOVITĚ; zbylých 151 vynechává okolnost, jejíž
> vypuštění dává slabší, ale pravdivé tvrzení.


**PŘÍVLASTEK VE JMENNÉ FRÁZI — ROZKLAD PŘED NÁVRHEM** *(kolo #130,
16. 8. 2026)*. Po měření z #128 je jmenná fráze JEDINÁ zbývající
překážka: pod jménem visí 937 členů proti 184 pod slovesem. Otázka
„co `amod` JE" se rozhodnout nedá; přeložená na **co z něj smí plynout**
ano — a rozpadá se na tři různé věci, ne na jednu:

| co to je | kolik | pozná to rozbor? |
|---|---|---|
| ČÁST JMÉNA — „**Malé** Svatoňovice" | 18 | **ANO**, hlava je `PROPN` |
| PŘIVLASTNĚNÍ — „**Čapkova** rodina" | 11 | **ANO**, `Poss=Yes` |
| PŘÍVLASTEK TŘÍDY — „terapeutický pes" | ~513 | **NE** |

**Ta třetí je ta podstatná a rozbor na ni odpověď nemá.** „Terapeutický
pes" a „bývalý prezident" mají rozbor ZNAK ZA ZNAKEM TÝŽ
(`Animacy=Anim, Case=Nom, Degree=Pos, Gender=Masc, Number=Sing,
Polarity=Pos`) — a přitom z prvního plyne, že je to pes, a z druhého, že
to prezident NENÍ. `Degree` je vlastnost SLOVA, ne toho vztahu:
„starší lidé" je `Cmp`, ale o podtypu to neříká nic.

**Co z toho plyne pro návrh** (a je to teprve návrh, ne rozhodnutí):
složit přívlastek do JMÉNA TŘÍDY (`terapeutický_pes`) NETVRDÍ nic — je
to jen jméno uzlu. Tvrzení „je to pes" je `subset`, tedy VLASTNÍ TAH
(`→⊆`), který už existuje. Mez by tím byla poctivá: čte se, co ve větě
stojí, a co z toho plyne, se neodvozuje mlčky.

**Doloženo měřením, kde ta hranice dnes leží:** ze 542 `amod` pod jménem
je 182 už POHLCENÝCH do zmínky (fráze přímo pod rolí), 277 ZTRACENÝCH
(fráze vnořená hlouběji) a 59 jinde. Skládání tedy není nová schopnost,
je to TÁŽ schopnost o patro níž.

> **Předpověď na projev bude potřeba PŘED kódem a po položkách**: 277
> ztracených členů, které by se začaly číst, mění čtení u desítek vět
> naráz — je to největší jediná změna za dlouho.

**SOUŘADNÝ ČLEN — DRUHÝ UZEL TÉŽE ROLE, NE DRUHÁ ROLE** *(rozklad
kola #123, 16. 8. 2026)*. Je to největší jediná věc, která v korpusu
zbývá, a otázka zněla: má souřadný člen dostat DRUHOU ROLI, nebo být
DRUHÝM UZLEM téže role? **Rozklad rodiny nad 238 větami** (120 vět, 248
zahozených souřadných členů):

| co to je | kolik |
|---|---|
| konjunkt členu, který rolí NENÍ (visí hlouběji) | 160 |
| konjunkt ROLE, TÝŽ PÁD — pravý druhý filler | **85** |
| konjunkt role v JINÉM pádě (šum rozboru, souřadné věty) | 3 |

**Rozhodnutí: druhý uzel téže role.** „Příklady zahrnují filodendrony
a **lilie**." — obě jména jsou `co`, ne `co` a něco jiného. Pojmenovat
druhý konjunkt jinou rolí je *účinnost koupená nepravdivým jménem*:
odpověď se uchytí, ale tvrdí o té větě něco, co v ní není. Měřením
doloženo z druhé strany: **u 50 z 65 přímých souřadných členů je
PRAVDIVÉ jméno role obsazené**, takže „pojmenuj to jinak" není odpověď,
je to obcházení.

**Realizace: DRUHÁ PREDIKACE, ne druhý filler v jedné roli.** Jádro drží
jeden term na roli a to se nemění — druhý uzel proto dostane vlastní
výrok se sdíleným přísudkem: `zahrnovat(kdo:příklad, co:filodendron)`
a `zahrnovat(kdo:příklad, co:lilie)`. Není to nová konstrukce: přesně
tohle už dělá `coordination_tier` pro souřadný druhý PŘÍSUDEK (W‑72/73,
T94, T96) — tady se sdílí predikát a liší se filler, tam naopak.

> **Nestaví se to v témž kole jako rozklad.** Změní to čtení u 85 členů,
> takže si to zaslouží vlastní předpověď na projev a vlastní kolo — ne
> přílepek k opravě W‑71.

**Konatel trpné věty — ROZLIŠITELNÝ JE, ALE NE INSTRUMENTÁLEM SAMÝM**
*(W‑80, rozhodnuto 15. 8. 2026)*. Otázka zněla: je `Ins:arg` u trpného
rodu konatel, nebo se to z rozboru poznat nedá? **Poznat se to dá, ale
až ze TŘÍ značek naráz** — a to je celý obsah rozhodnutí, protože každá
sama vede k jinému, doložitelně špatnému čtení:

| značka | co sama nestačí |
|---|---|
| instrumentál (`Case=Ins`) | „psal **perem**“ je NÁSTROJ, ne konatel |
| `Voice=Pass` na přísudku | „napsána **perem**“ je stejně trpná |
| `obl:arg` (valenční doplnění) | v korpusu 10× a **ani jednou** u trpného rodu — „stal se **redaktorem**“, „zabývá se **zkoumáním**“ |

K nim přistupuje čtvrtá podmínka, kterou vynutil korpus: konatel je
**HOLÝ** instrumentál. „Je spojována **s** emancipačními snahami.“ má
`obl:arg`, instrumentál i `Voice=Pass`, a konatel to není — dělá to
předložka.

**Změřeno předem a na projev:** 22 trpných vět v korpusu, z toho 4
s instrumentálem pod přísudkem, a **projev 0** — ani jedna z těch čtyř
není holý `Ins:arg` (dvě mají předložku, dvě prostý `obl`). Pravidlo se
proto v korpusu nemá kde ukázat a je doloženo **jen zkouškami**; to se
říká rovnou, aby se z nuly nedalo číst „nic se nezměnilo“.

**Co se tím napravilo.** Patiens dostal jméno v W‑59, konatel ne — „Kniha
byla napsána Čapkem.“ dávala `napsaný(Ins:arg:·Čapek, co:kniha)`, tedy
TVAR místo jména, a věta se kvůli povrchové roli podle B‑19 nezapsala.
Rodina trpného rodu je tím uzavřená z obou stran jedné věty.

**Partitivní relace v jádře — ODLOŽENA, A JE ZAPSANÁ SPOUŠŤ** *(W‑39,
rozhodnuto 15. 8. 2026)*. Genitivní přívlastek nese pět měřením
doložených významů a jeden z nich je „část z celku" („polovina domu").
Nabízelo se přidat obecnou partitivní relaci do jádra; nepřidala se, a to
ze tří důvodů:

1. jádro už prostor „část z celku" **rozřezalo podle sortů** — `contains`
   pro místo, `within` pro čas, `subset` pro třídy — a obecná partitivní
   relace by se s nimi překrývala; překryté uzávěry jsou zdroj nejtěžších
   vad;
2. **reifikace stojí a dělá přesně tohle**: deverbální jméno JE sloveso,
   jen zabalené, takže „chov zvířat" je `chov(co:∀zvíře)` bez jakékoli
   změny jádra;
3. neměnit jádro znamená nedotknout se ničeho, co drží.

> **Spoušť, po které se to má přehodnotit:** až přijde otázka, která
> potřebuje **tranzitivitu částí** („je půlka půlky částí celku?") a
> reifikovaný fakt na ni nestačí. To je důkaz, že partitivnost je
> uzávěrová vlastnost, ne jen popisná. Do té doby ne — reifikovaný fakt
> se ZÁMĚRNĚ neřetězí, a právě to je na něm to bezpečné.


| Téma | Proč mimo | Co bude potřebovat |
|---|---|---|
| `closed_context` (§ 6.9 zadání) | uzavřený svět uvnitř otevřeného | lokální doména + UNA + `EXACTLY_ONE`/`AT_MOST_ONE`/`AT_LEAST_ONE`/`ALL_DIFFERENT` |
| `GapFinder` | jiný režim evaluace | samostatný SLD modul nad týmž programem |
| perzistence stavů, kauzalita | plná temporální logika | mimo v1 |
| aritmetika | nad rámec mohutnosti a porovnání | mimo v1 |
| ranker čtení | až na důkaz saturace vzorů | § 12/4 zadání |

**JMÉNA ROLÍ — ROZHODNUTÍ PŘED STAVBOU** *(změřeno 15. 8. 2026, kolo #96)*.
Doptání „co znamená role *X*" je největší zeď korpusu: **165 vět z 238**,
**50 různých tvarů**, **250 výskytů**. Než se na to cokoli postavilo,
změřily se tři otázky. Odpovědi mění, co se vůbec má stavět.

**(1) „`v+Loc` → `kde`" NENÍ ani znalost o jazyce, ani hypotéza o větě.**
Je to otázka, která má víc správných odpovědí, a **rozbor ji rozhodne
jen ve 38 % případů**. Ze 42 výskytů `v+Loc`:

| co je v rozboru | kolik | co z toho plyne |
|---|---|---|
| `NameType=Geo` na filleru | 5 | místo, čitelné z rysu |
| letopočet (`NumType=Card`, 4 číslice) jako dítě | 11 | čas, čitelné ze stromu |
| **ani jedno** | **26** | *„v bytě", „v kostele", „ve století", „v smyslu", „v angličtině"* |

Těch 26 obsahuje místa (`byt`, `dům`, `kostel`), časy (`století`,
`polovina roku`) i věci, které nejsou ani jedno (`smysl`, `význam`,
`přístup`, `kniha`). **Rozhodnout je z tvaru by šlo jen seznamem slov**
(„rok je čas, byt je místo") — a to je rodina chyby, kterou tenhle projekt
odmítá od W‑32 a naposledy v kole #95 u úřadů.

> **SORT FILLERU SE POUŽÍT NEDÁ, A JE TO STRUKTURÁLNÍ DŮVOD, NE
> OPATRNOST.** Podle § 3.6 **sort plyne z ROLE** (`kde` → `Place`).
> Kdyby role plynula ze sortu, byl by to **kruh**. Před rozhodnutím je
> k dispozici jen to, co stojí v rozboru: lemma, `upos`, rysy.

**Závěr (1):** mapa `tvar → role` je věcně špatně; **tvar + signál
z rozboru** rozhodne 16 ze 42 a u zbylých 26 se **musí dál ptát** — a to
je správně, ne mez. Zeď se dá snížit o 38 % bez jediného dohadu.

**(2) Kde ta znalost bydlí.** `RoleMapping` už existuje a je to **data
s proveniencí, odvolatelná a viditelná v přepisu**. Nový seed se
nezakládá: co se naučí z jedné věty, se učí tam, a signál z rozboru
(Geo, letopočet) je **odvození, ne uložený seznam**.

**(3) `nsubj:pass` mezi okolnostmi NENÍ vada zápisu — ale nepatří tam.**
Vlastní jméno dostává **záměrně** (`_role_for`, důvod I‑2/INV‑11: trpný
podmět není konatel). Jenže **19 výskytů, třetí nejčastější tvar**, a
otázka „co ta role znamená" se ptá na něco, co rozbor říká: v trpném rodě
je podmět **patiens**. Změřeno: **18 z 19** vět nemá roli `co`, takže by
nekolidovala; agens v instrumentálu má **2**.

**A DRUHÝ NÁLEZ, KTERÝ TU ZEĎ MĚNÍ VÍC NEŽ CELÉ UČENÍ ROLÍ:** z 22
výskytů tvaru `Gen` je **13 nerozpoznaných genitivních přívlastků**.
`genitive_attributes` páruje hlavu **shodou LEMMAT**, jenže zmínka ve
čtení je **složená** — „prvním předsedou **odboru**" má v rozboru hlavu
`předseda`, ale ve čtení leží `první_předseda`, takže shoda selže a
genitiv skončí jako **role predikace**. Je to posedmé táž rodina:
**kategorie porovnaná přesnou shodou tam, kde hodnotu skládá někdo
jiný.** Stabilní identita je `token_index`, ne lemma.

> **Kolik z té zdi vůbec není o jménech rolí:** z prvních tří tvarů
> (83 výskytů, 33 %) je **32 něco jiného** — 13 přehlédnutých přívlastků
> a 19 trpných podmětů. Učit jména rolí je tedy **až třetí krok**, ne
> první.

**RODINA `rozbor` — SMĚR OPUŠTĚN, A JE TO ZÁVĚR MĚŘENÍ** *(kolo #104,
15. 8. 2026)*. Jedenáct vět, které si korpus blokuje sám „rozborem", se
rozpadá na čtyři skupiny a **ani jedna z nich není vada čtení**:

| skupina | vět | co to je |
|---|---|---|
| nadpis splynulý s větou | 4 | vlastnost TEXTU — segmentace, W‑64 |
| jmenný fragment | 2 | *„Úrazy způsobené pády."* — není věta |
| kolize dvou `advmod` | 3 | z rozboru NEROZLIŠITELNÉ, W‑63 |
| dvě čtení, systém se PTÁ | 2 | **správné chování**, ne mez |

Devět z jedenácti je tedy vlastnost textu nebo už pojmenovaná mez a dvě
jsou doptání. **Dotlačit tenhle směr by znamenalo opravovat texty, ne
čtení** — a jediné, co by z toho vzniklo, je systém, který přečte
nadpis jako větu.

> **Co z toho plyne pro měření.** Ty dvě věty, u kterých se systém ptá
> *„které z těch dvou čtení?"*, jsou v záznamu vedené jako `NEPŘEČTENO`
> s `open_questions=0`, ačkoli jádro otázku VRACÍ. Je to vada MĚŘICÍ
> VRSTVY, ne jádra — ale zkresluje právě tu metriku, která má `ZAPSÁNO`
> nahradit.

**KOLIK TAHŮ STOJÍ SKUTEČNÝ ODSTAVEC — ZMĚŘENO, DOMÉNA SE NEPÍŠE**
*(kolo #105, 15. 8. 2026)*. Čtyři DOSLOVNÉ věty z korpusu, v pořadí,
v jednom sezení. **Výsledek není číslo, je to `NE`:**

| co | kolik |
|---|---|
| tahů, které mají odpověď (`→@`, `→∀`, `→=`) | 7 |
| otázek BEZ TAHU | 6 |
| vět zapsaných | 0 |

**Tři důvody, a sčítají se:**

1. **Některé otázky tah nemají.** „1938" visí jako `nummod` uvnitř
   časového údaje; „musel"/„ulehnout" jsou SOUŘADNÝ DRUHÝ PŘÍSUDEK.
   Pojmenovat je rolí by znamenalo tvrdit, že jsou členy té věty.
2. **Jedna otázka odmítá vlastní odpověď.** U „si" se systém ptá *„Na
   koho odkazuje? Řekni to prosím jménem"*, ale role `komu` čeká na
   **kvantifikátor** — `decides_reference` proto odpoví *„role na odkaz
   nečeká"*. Otázka a stav se rozešly.
3. **Odstavec se nerozběhne sám.** Poslední věta nemá vyslovený podmět
   a v souvislém sezení pro něj není kandidát: předchozí věty se
   nezapsaly (visí na nepojmenovaných rolích), takže v kontextu textu
   nic neleží.

> **Proto se dvacátá druhá doména nepíše.** Každý krok v ní má být
> odpovědí na otázku, kterou systém sám položil. Kroky, které by tam
> byly „aby to vyšlo", by z akceptační sady udělaly zkoušku napsanou
> podle výsledku — a to je přesně to, čemu má ta sada bránit.

**PŘEMĚŘENO PO PATNÁCTI KOLECH — POŘÁD `NE`, ALE Z JINÝCH DŮVODŮ**
*(kolo #120, 15. 8. 2026)*. Tři překážky z #105 jsou zavřené: souřadný
druhý přísudek (W‑70/71/73), časový údaj (W‑74/75/77) i zvratné zájmeno
(W‑68). Číslo se proto pohnulo — a pořád není nula:

| co | #105 | #120 |
|---|---|---|
| otázek, které TAH MAJÍ | 7 | 7 |
| otázek BEZ TAHU | 6 | **3** |
| vět zapsaných | 0 | **0** |

**Zbyly dva důvody a druhý je nový:**

1. **Tři otázky tah nemají** a obě příčiny jsou pojmenované meze:
   souřadné JMÉNO („zápal plic") a `nmod` pod obecným jménem („v Praze"
   pod „hřbitově"). U obou `names_role` tah PŘIJME — ohlásí
   *„✓ naučeno"* — ale **ČTENÍ SE NEZMĚNÍ**. To je horší než chybějící
   tah: vypadá to jako odpověď.
2. **Odstavec se nezapíše, ani když se odpoví na všechno.** První věta
   projde na *„✓ přečteno"* a skončí na *„(zakotvení neproběhlo — do
   báze nejde nic)"*: `si` se stane rolí s fillerem a ta role dostane za
   uzel „se". Zvratné zájmeno ale ÚČASTNÍK NENÍ — je to část tvaru
   slovesa („přivodit si"). W‑68 odstranila nepravdivou OTÁZKU; ROLE
   ZŮSTALA.

> **Doména se proto nepíše ani teď** — a je to táž úvaha jako v #105,
> jen podložená novým měřením. Doména, ve které by bylo `writes` všude
> prázdné, nedokládá nic; a kroky, které by ji k zápisu dotlačily, tam
> nesmějí být.

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
| T45 | `before*` je tranzitivní | pondělí → úterý → středa dá `A` na pondělí/středa |
| T46 | `before*` není reflexivní ani symetrický | `before(x,x)` a obrácený směr → U |
| T47 | alternativa nad osou (dialog D) | „kam jel dřív?" vrátí člen, ne ano/ne |
| T48 | cyklus v uspořádání | dotaz o uzlu na cyklu → `InconsistentOrder`, cyklus jinde neblokuje |
| T49 | fakty netečou přes spornou identitu | `same_as(A,B)` ∧ `¬same_as(A,B)` ∧ `p(A)` ⇒ `p(B)` → `U` |
| T50 | spor se přesto hlásí | přímá otázka `same_as(A,B)` → `CONFLICT`, ne `N` |
| T51 | spor neblokuje identitu jinde | nesporná dvojice v téže bázi dál dává `A`; obchvat přes `subset*` taky neprojde |
| T52 | odvolání jedné strany hranu vrací | po `revoke(¬same_as)` je `p(B)` zase `A`; mezera do té doby spor pojmenuje |
| T53 | zákaz v hlavě je širší než jádro | pravidlo s `role` v hlavě → `UnsafeRule`; s `role` v TĚLE projde |
| T54 | kritérium se odvozuje, nedeklaruje | co čte uzávěrový index, je v `KERNEL_PREDICATES`, a naopak |
| T55 | odpověď na doptání je tah | `→∀` naučí tvar a znovu přečte větu; `turns_to_learn` to změří |
| T56 | pořadí těla neurčuje význam | všech 6 permutací téhož pravidla dá `N`, TÝŽ normální tvar i TÝŽ důkaz |
| T57 | neuspořádatelné pravidlo padne u zápisu | `subset(X,Y)` bez vazače → `UnsafeRule` při `attach_rule`, ne `EvaluationError` při dotazu; báze zůstane bez pravidla |
| T83 | úřad se nezapíše, povolání ano | `confirms_title(..., OFFICE)` NEZAPÍŠE a nabídku nechá otevřenou; `TRADE` zapíše `member`; otázka nabízí obě možnosti a říká, která se nezapíše |
| T82 | tři stavy nabídky, tři hlášky | druhé potvrzení téhož titulu neřekne „žádná věta to netvrdí“, ale „už je to potvrzené a leží to v bázi jako sXXXX“ — a obě odmítnutí mají různý důvod |
| T81 | potvrdit jde jen to, co někdo řekl | `confirms_title` bez nabídky NEZAPÍŠE a vrátí `✗` — ani v prázdném sezení („Kdokoli je král“), ani na jiný titul téhož člověka („prezident Josef Hora“ po větě o básníkovi); po nabídce zapíše a v hlášení je VĚTA Z TEXTU, která to tvrdí |
| T117 | zápor obrací monotonii | „Manželství nebylo od počátku šťastné.“ se částečně NEZAPÍŠE a řekne proč; táž věta bez záporu se zapíše jako `být(co:·šťastný, kdo:∀manželství)` |
| T116 | částečný zápis | „Petr bydlel v Praze.“ zapíše `bydlet(kdo:Petr)` a dál se ptá na `v+Loc`; dotaz na `kde` dá `U`; po `→@` leží v bázi JEDEN výrok a v historii je odvolaný částečný s důvodem „doplněno“; věta s `pokud` se částečně NEZAPÍŠE |
| T115 | účet slov věty | „Chov jejich ovlivňuje zdraví.“ hlásí `[BEZ ZÁZNAMU: „jejich“ (det pod „zdraví“)]`; „Petr přišel.“ účet prázdný a nic se nehlásí dvakrát |
| T114 | nic nezmizí beze stopy | „Filipovo auto stojí venku.“ se ptá „O kterém **Filipovo auto** mluvíš?“ a uzel zůstává `auto`; „…s domácími zvířaty“ hlásí `[ZAHOZENO: „domácími zvířaty“]`; „Auto stojí venku.“ takový záznam nemá |
| T113 | přívlastek ve jmenné frázi | „…s domácími zvířaty“ se na „domácími“ neptá; „Malých Svatoňovicích“ dá `·malý_Svatoňovice`, „anglickou Wikipedii“ ne; `subset(bývalý_prezident ⊆ prezident)` zůstává `U` |
| T112 | naučené se najde | „Lékaři sledovali jejich stav.“ + `→∀` se v témž sezení nezeptá podruhé a „…jejich případ.“ se neptá vůbec; hlášení říká „`DET/det` se slovem „jeho““; strukturní tvary se učí jako dřív |
| T111 | zkrácené jméno se řekne nahlas | „Bydlí v Rožnově pod Radhoštěm.“ hlásí `[JMÉNO NEÚPLNÉ: … uzel by nesl jen „Rožnov“]`, NEPTÁ se, jakou roli hraje „Radhoštěm“, a nezapíše se; „v Hradci Králové“ se složí a neúplné není |
| T110 | jméno se neskládá zkráceně | „Bydlí v Hradci Králové.“ dá `·Hradec_Králové` a NEHLÁSÍ k tomu přívlastek; „Rožnov pod Radhoštěm“ (předložka) se neskládá a hlásí se dál; `flat` („Čapka Josefa“) se skládá jako dřív |
| T109 | odvolat větu jde celou | „Petr a Jana přišli.“ + `→&` zvlášť zapíše DVA výroky a tah je OBA ohlásí; `revoke_utterance` vezme zpět obojí („přišla Jana?“ → `U`), ale „Petr odešel.“ z jiné promluvy zůstane `A` |
| T108 | víc členů v jedné roli | „Petr a Jana přišli.“ se PTÁ „o každém zvlášť, nebo dohromady?“ a nezapisuje; `→&` distributivně dá DVA výroky (`přijít(kdo:Petr)`, `přijít(kdo:Jana)`), kolektivně JEDEN uzel `Petr_a_Jana`; „Petr přišel.“ se neptá |
| T107 | přívlastek nově pojmenovaného členu | „Přidal se zánět ledvin a zápal plic.“ po `→@` na „zápal“ hlásí OBA přívlastky („zánět ledvina“, „zápal plíce“); dokud ten člen ve čtení není, jeho přívlastek se nehlásí |
| T106 | odpověď nezruší ostatní otázky | „Petr a Jana viděli psa a kočku.“ se po `→@` na jeden člen ptá na zbylý, drží `◐`, `[ZAHOZENO: …]` přežije tah; „Petr přišel.“ dál dostane `✓ přečteno` |
| T105 | odpověď, která nic neudělá, to řekne | `→@` „nsubj>conj+Nom → kdo“ v „Petr a Jana přišli.“ ohlásí, že roli `kdo` drží „Petr“, že „Jana“ zůstává mimo čtení a že mapování platí dál; `→@` na `jak` zabere a o nezměněném čtení MLČÍ |
| T104 | spona s podtypem je spona | „Jan je učitel.“ se sponou `cop:expl` dá TOTÉŽ čtení jako s `cop`; `aux` ani `copula` sponou nejsou |
| T103 | kvantifikátorové zájmeno neodkazuje | „Vesmír je vše, co existuje.“ dá `co:∀všechen` a NEŘEKNE „odkazuje mimo text“; „Něco spadlo.“ dá `∃něco`; „Nikdo nepřišel.“ dá `¬přijít(kdo:nikdo)` bez kvantifikátoru a taky bez té věty; „On bydlí v Praze.“ se dál ptá na odkaz |
| T102 | konatel trpné věty | „Kniha byla napsána Čapkem.“ dá `kdo:·Čapek`; „Kniha byla napsána perem.“ dál `čím`; „Je spojována s emancipačními snahami.“ se nemění; činný `Ins:arg` („stal se redaktorem“) se nemění |
| T101 | trpný rod má jedno jméno role | „Byl pohřben na Vyšehradě.“ + `→=` zapíše `co:Karel_Čapek` a otázka „Byl Karel Čapek pohřben na Vyšehradě?“ dá `A`; činný pro‑drop dál dává `kdo` |
| T100 | vlastní jméno je konkrétní všude | „Byl Karel Čapek pohřben?“ i „Byla kniha napsána Karlem Čapkem?“ dají `·Karel_Čapek` bez doptání; „Byla kniha napsána?“ se dál ptá |
| T99 | vnořené datum a řadová číslovka obecně | „Zemřel dne 25. prosince 1938.“ nehlásí „25.“ ani „1938“; „ulice Karla Čapka“ a „Město Praha“ se nemění; „Obsadil 1. místo.“ dá `1._místo` — ZÁMĚR, ne vedlejší účinek |
| T98 | celý datum je jedna zmínka | „Karel Čapek se narodil 9. ledna 1890.“ nehlásí ani „9.“, ani „1890“; „s 92 lidmi“, „21 let“ i „tři typy“ se hlásí dál |
| T97 | letopočet je součást zmínky | „V roce 1986…“ dá `rok_1986` a nic nehlásí jako ztrátu; „V roce 1990…“ dá JINÝ uzel; „s 92 lidmi“ se nemění a hlásí se dál |
| T96 | vyslovený druhý podmět má vlastní uzel | „Petr přišel a Jana odešla.“ uloží dva výroky o DVOU uzlech a hlásí, že druhý podmět je VYSLOVENÝ; „Jan zpíval a tančil.“ dál o JEDNOM |
| T95 | zapsaná věta pojmenuje nevzatou půlku | „Němec byl český vlastenec a publikoval.“ se zapíše A ŘEKNE, co s druhou větou; „Jan zpíval a tančil.“ uloží do báze DVA výroky z jedné promluvy, oba o témž uzlu |
| T94 | druhá věta si půjčí podmět | „Stav se zlepšil, ale musel ulehnout.“ dá DVĚ predikace, druhá má `kdo` z první a je to v hlášení řečeno; „Stav se zlepšil, ale lékař váhal.“ se nezmění; „Psi štěkají a kočky.“ se nezmění |
| T93 | druhý přísudek je druhá věta | „Stav se zlepšil, ale musel ulehnout.“ nehlásí „musel“ jako ztracený člen a v přepisu stojí, že je to DRUHÁ VĚTA, kterou zatím neumíme číst; „Psi štěkají a kočky.“ hlásí „kočky“ jako člen dál |
| T92 | zvratné zájmeno není anafora | „V prosinci 1938 si Karel Čapek přivodil chřipku.“ se už neptá „na koho odkazuje si“ — zbude jen otázka na kvantifikátor, která tah MÁ; „Byl pohřben…“ se dál ptá na podmět |
| T91 | jedna odpověď na „je to přísudek?“ | „Obezita: Zvířata byla vyšetřena veterinářem.“ dostane hlášku o NADPISU i s trpnou apozicí (kořen `ADJ` + `aux:pass`); „Obezita, nemoc.“ ji dál nedostane |
| T90 | nadpis splynulý s větou | „Obezita: Domácí mazlíčci trpí nadváhou.“ se NEČTE, ale hlášení mluví o NADPISU a APOZICI, ne o chybějících členech; jmenná apozice bez přísudku hlášku o nadpisu nespustí |
| T89 | dva členy, jedno jméno | „…byla ovšem interpretace zcela podřízena…“ se ČTE (`advmod` i `advmod:emph`) místo aby zmizela; dvě holá `advmod` se přečíst nedají, ale hlášení jmenuje OBĚ SLOVA; „Úrazy způsobené pády.“ se ohlásí jako JMENNÁ FRÁZE |
| T88 | jméno = tvar zastaví zápis všude | „Petr bydlí v Praze.“ se NEZAPÍŠE, dokud `v+Loc/Geo` nedostane jméno — stejně jako „Petr odjel, protože pršelo.“; po odpovědi `→@` leží v bázi PRÁVĚ JEDEN výrok o té větě; na `proč` se systém už neptá |
| T87 | signál dělí tvar, nepojmenovává roli | „Petr byl v roce 1935 v Praze.“ dá `v+Loc/Geo` i `v+Loc/rok` v jedné větě (dřív by se srazily); „v tomto smyslu“ zůstane `v+Loc` bez jména; `po+Loc/rok` NEDĚDÍ `po+Loc → kudy`; v hlášení je vidět, který signál to byl |
| T86 | trpný podmět je patiens | „Úmysly byly popsány.“ dá `popsaný(co:∀úmysl)` a zapíše se; „Byly úmysly popsány?“ dá `A`; „Kolekce se označuje mnohovesmír.“ se ZEPTÁ, která ze dvou stran je popisovaná, a NEZAPÍŠE; „Byl pohřben na Vyšehradě.“ se dál ptá na podmět |
| T85 | přívlastek je jen HOLÝ genitiv | „Další synonyma vesmíru u starověkých filozofů“ dá přívlastek jen na „vesmír“; „Podle některých teorií je vesmír součástí systému.“ konstrukci `cop:součást+Gen` NEZTRATÍ kvůli předložkovému genitivu navíc |
| T84 | jedna zmínka, jedno jméno | „byl prvním předsedou odboru“ nedá zároveň `co:první_předseda` a `kdo:předseda`; genitiv je přívlastek A NENÍ role; „Petrovice jsou součástí Plzně.“ si genitiv PONECHÁ, protože ho nárokuje čekající `→⊆` |
| T80 | titul se nabídne, nezapíše | „Nad hrobem promluvil básník Josef Hora.“ zapíše větu a OHLÁSÍ členství; „Je Josef Hora básník?“ dá `U`, ale s důvodem „řekls to, čeká to na potvrzení“; po tahu `→∈` dá `A`; „prezident Masaryk zemřel.“ se sám nezapíše (úřad v čase); „Město Praha“ ani „bratří Čapků“ tou cestou member nevyrobí |
| T79 | plurálový titul se nesloží | „Mezi pátečníky patřili kromě bratří Čapků…“ nedá uzel `·Čapka`; „matka Božena“ s víceznačným `Number=Plur,Sing` se složí dál — rys se čte průnikem (W‑32) |
| T78 | titul není třída a kvantifikátor jde s identitou | „Nad hrobem promluvil básník Josef Hora.“ zapíše `promluvit(kdo:Josef_Hora)`, ne `∀básník` ani `∀Josef_Hora`; „Promluvil Josef Hora?“ dá `A`, „Promluvil básník?“ dá `U`; „Město Praha leží v Čechách.“ se nemění a dál se ptá na roli „Prahy“ |
| T77 | apozice není díl jména | „Karel Čapek, rodným jménem Karel Antonín Čapek…“ dá uzel `Karel_Čapek`, ne `Karel_Čapek_Karel`; „Karel Čapek, spisovatel, zemřel.“ nezapíše `same_as`; `flat` dál skládá, `Město Praha` dál ne |
| T76 | víceslovné jméno je jeden uzel | „Karel Čapek byl spisovatel.“ zapíše `member(elem:Karel_Čapek, …)`; táž otázka dá `A`, ale „Byl Karel Poláček spisovatel?“ dá `U` — dva Karlové nesplynou; díly jména se hlásí jako POHLCENÉ, ne zahozené; `flat` pod obecným jménem se nebere |
| T75 | žurnál nese otisk výchozího lexikonu | přehrání se SHODNÝM lexikonem dá 8 = 8 a mlčí; přehrání s JINÝM projde, ale ohlásí „[JINÝ LEXIKON: … determinismus platí jen pro týž výchozí stav]“; otisk leží na prvním tahu žurnálu, ne v sezení |
| T74 | žurnál se přehraje s výchozím lexikonem | dialog Petr/`→@` proč/Jan dá po `Session.replay(žurnál, lexicon=…)` TOUŽ bázi výrok po výroku (8 = 8) i tytéž odpovědi; bez lexikonu 4 a Petrova věta chybí — takže test měří právě tuhle vadu |
| T73 | role bez jádrového jména zastaví zápis | „Petr odjel, protože pršelo.“ se NEZAPÍŠE, dokud se `advcl:protože` nepojmenuje; po `→@` je věta v bázi PRÁVĚ JEDNOU, s naučeným jménem role |
| T72 | podmět vyjádřený celou větou | „Je jasné, že Jan přišel.“ NETVRDÍ, že podmět nemá, a nenabízí antecedent; řekne, že podmětem je celá věta vedlejší a že ji zatím dosadit neumí; „Byl pohřben v Praze.“ se dál ptá; „Bylo chladno.“ se dál neptá |
| T71 | trpný rod se pozná ze struktury | „Byl pohřben v Praze.“ se NEZAPÍŠE a zeptá se na podmět; „Jan byl pohřben v Praze.“ (má `nsubj:pass`) se na podmět neptá; činný pro‑drop beze změny; jméno bez pomocného slovesa přísudek není |
| T70 | koordinovaný podmět | „Petr a Pavel četli knihu.“ se přečte, „Petr a Pavel četl knihu.“ padne a řekne proč; koordinace se pozná z hrany `conj`, ne ze spojky; rod se u koordinace NEOVĚŘUJE a je to zapsaná mez; kvantifikovaný podmět se s koordinací neplete |
| T69 | kvantifikovaný podmět | „Několik hostů přišlo.“ se přečte, „Několik hostů přišli.“ padne a řekne proč; řídící člen se bere z `det:numgov`, ne ze seznamu slov; koordinovaný podmět tahle větev nechytá a padá dál |
| T68 | shoda průnikem, ne rovností | „Matka sbírala folklor.“, „Povodeň zasáhla dům.“ i „Přednáška byla v pondělí.“ se PŘEČTOU; „Psi byla v pondělí.“ se dál zahodí a řekne proč (rod); „Obsahuje citron vitamíny?“ se pořád zužuje na jedno čtení; chybějící rys shodu neruší |
| T67 | věta bez podmětu | „Narodil se v Petrovicích.“ po „Jan je učitel.“ NEZAPÍŠE nic a nabídne Jana; po `→=` zapsáno na týž uzel; „Narodil se Jan v Plzni?“ dá `A` s citací obou zápisů; „Narodila se …“ po téže větě nenabídne nikoho; přísudek bez rodu a čísla nenabídne nikoho |
| T66 | zájmeno odkazuje do předchozí věty | „Jan je učitel. On bydlí v Petrovicích.“ NEZAPÍŠE nic a nabídne Jana; po `→=` zapsáno na TÝŽ uzel; „Bydlí Jan v Plzni?“ dá `A` s citací obou zápisů; „Ona …“ po téže větě nenabídne nikoho; skupina se nenabídne nikdy |
| T65 | pojmenování z české věty | „Jan se jmenuje taky Honza.“ zapíše `name(of:Jan, value:Honza)`, strany podle DEPRELŮ (dvě čtení, jeden výsledek); „Je Honza učitel?“ dá před tím `U` a po něm `A` s citací faktu I výroku o jménu; bez zvratného „se“ to pojmenování není; odvolání jména vrátí `U` |
| T64 | uzavření světa z české věty | „To jsou všichni psi.“ NEZAPÍŠE nic a ptá se; po tahu `!∀` je `complete(pes)` v bázi; „Je Mourek pes?“ dá před tím `U` a po něm `N` s důkazem citujícím PROHLÁŠENÍ I VÝČET; odvolání vrátí `U`; člen uzavřené skupiny dál `A`; žádné pravidlo `complete` nevyrobí |
| T63 | otevřená otázka na konstrukci zastaví zápis | „Praha je součástí Plzně.“ + odpověď na KVANTIFIKÁTOR → nezapsáno a otázka na relaci POŘÁD TAM; po odpovědi na relaci zapsáno `contains(part:Praha, whole:Plzeň)`; desátý dialog zapíše `contains` i `within` a jedna otázka potřebuje OBA s důkazem citujícím oba zápisy |
| T62 | kruh v uspořádání se odmítá u zápisu | `before(b,a)` po `before(a,b)` → `AttachError`, který JMENUJE výroky kruhu; `before(a,a)` odmítnuto vždy; báze po odmítnutí dál odpovídá; H‑3 v uzávěru zůstává jako druhá obrana |
| T61 | negace obrací monotonii | `¬P(∀maso)` odpoví na `¬P(∃maso)`; kladné `∀→∃` zůstává `U`; dotaz smí být užší, ne širší |
| T60 | zapsaný výrok se nepřehlíží | `attach(subset(auto, A AND B))` → přímá otázka dá `A` s citací TOHO výroku; zákony § 5.2.1 běží dál beze změny a negativní kontroly (`A OR B ⊆ A`) drží |
| T59 | vázanost i uvnitř algebraického termu | `h(a:X) ← subset(a AND X, b)` → `UnsafeRule` u ZÁPISU (dřív prošlo a padlo u dotazu na neuzemněnou hlavu); s `member(X,g)` jako vazačem projde a odpoví `A` |
| T58 | normalizace neobchází bezpečnost negace | proměnná vázaná jen negovaným literálem se přeuspořádáním „bezpečnou" nestane; pozitivní vazač ji naopak povolí |

F0 je hotové, když projdou všechny **a** referenční i produkční
evaluator dají shodný verdikt i shodný `normalize_proof`.
