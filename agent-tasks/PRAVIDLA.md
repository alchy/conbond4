# PRAVIDLA — pasti, do kterých už někdo spadl

**Každý řádek tady stál jedno kolo auditu.** Nejsou to zásady pro
inspiraci; jsou to popisy konkrétních vad, které se opakují.

## O měření

**Účinnost koupená nepravdivým jménem není účinnost.**
Když se něco „uchytí" jen proto, že se to pojmenovalo jinak, než co ve
větě stojí, změřilo se něco jiného, než se mělo. *(#121)*

**Kolo, které měří, se nemíchá s kolem, které opravuje.**
Narazíš‑li při měření na vadu, **zapiš ji a měř dál**. Opravovat
uprostřed měření znamená, že se výsledek nedá přiřadit ani k jednomu.
*(#124, #128)*

**Předpověď na projev PŘED kódem.**
A po běhu **rozdíl proti předpovědi**. Dvakrát v tomhle projektu byla
odchylka cennější než všechno ostatní v předávce. *(#124, #128)*

**Číslo, které si nikdo neprošel po položkách, tvrdí víc, než ukazuje.**
Součet skryje, že deset věcí přibylo a deset ubylo. Porovnávej **po
větách**, ne procentem. *(kolo #2 utils)*

**Když měříš vlastním nástrojem, ověř nejdřív nástroj.**
Reviewerovi vyšlo 185 místo 180, protože jeho sonda počítala jméno role
`kdo` jako člen; Builderovi vyšlo 5 místo 0, protože porovnával TVAR
proti LEMMATU. **Obojí byla vada měřidla, ne měřeného.** *(#125, #127)*

## O hlášení a stavu

**Značka nesmí vzniknout z nepřítomnosti důkazu.**
`✓ přečteno` počítané z prázdné stopy tvrdí „celá věta je ve čtení",
i když z ní vypadlo čtrnáct členů. *(B‑25)*

**Žádný tah nepotvrdí, že se něco naučilo, aniž řekne, co se tím ve
větě změnilo.**
Odpověď, která se přijme a nic neudělá, je horší než chybějící tah:
u chybějícího člověk ví, že stojí. *(S‑39)*

**Co se naučí, musí jít najít.**
Spouštěč se staví z **téže signatury**, kterou se pak hledá. Učit se
pod jiným klíčem znamená slibovat třídu a neuložit nic. *(B‑27, S‑44)*

**Odpověď na jednu otázku nesmí zrušit ostatní.** *(B‑25)*

**Odvolat větu jde celou.** Jednotkou odvolání je **promluva**, protože
jednotkou zápisu je promluva. Tah, který zapsal víc výroků, je všechny
ohlásí. *(B‑26, S‑43)*

**Uzel se nejmenuje zkráceně.** `·Hradec` u věty, kde stojí „Hradci
Králové", je vlastní jméno, které v textu nestojí. *(W‑72, O‑20/O‑21)*

## O významu

**Rozbor rozhoduje o stavbě, ne o významu.**
„Petr a Jana přišli." a „Petr a Jana zvedli klavír." mají **identickou**
stavbu a opačné čtení. Kde rozbor odpověď nemá, **ptá se systém** —
nehádá. *(W‑73, S‑42)*

**Sort plyne z role, ne role ze sortu.** Odvozovat role ze sortu filleru
je kruh. *(§ 3.6)*

**Absence není negace.** *(I‑21)* **Pět stavů znalosti se neslévá** —
`ZAPSÁNO / PTÁ SE / DVOJZNAČNÉ / NEPŘEČTENO / ODMÍTNUTO / CHYBA`.
Raději 215 legitimních *PTÁ SE* než jedno falešné *ZAPSÁNO*; ale
bezpečné *NEVÍM* není omluva pro to nikdy se nic nenaučit.

**Přesnost před agresivním recallem.** Rostoucí *PTÁ SE* není samo
o sobě regrese.

## O práci

**Ptej se na obecnou schopnost, ne na konkrétní pád.**
Ne *„jak opravit tuhle větu"*, ale *„jakou čtenářskou schopnost tenhle
pád odhaluje"*. Hledej **jeden mechanismus**, ne dvacet výjimek.

**Každý nový mechanismus má případ kladný, sporný a záporný.**

**Seed a lexikon jsou DATA, ne kód.** Explicitní, s proveniencí,
odvolatelná. Podmínka v kódu je skrytá znalost.

**Doložka odvozená z měření nese ROZSAH toho měření.**
Jedna věta o tom, **na čem to stojí a co tím pádem ověřené NENÍ**.
*(#137: pravidlo „vynechat okolnost dá tvrzení slabší" bylo odvozeno
z KLADNÝCH čtení, doložka to zopakovala jako obecnou větu — a tím tu
nadgeneralizaci nezachytila, nýbrž rozšířila. Pod negací se monotonie
obrací a do báze se dostala nepravda. Kdyby u doložky stálo „odvozeno
z kladných čtení", byla by mezera vidět při čtení, ne až na zápisu.)*

**Doptat se je levnější než dopočítat si cizí kritérium.** *(#125)*

**Kdo přizná vlastní chybu dřív, než se na ni někdo zeptá, ušetří kolo.**
V tomhle projektu to platilo doslova — pětkrát.
