# AGENT 3 — Builder měřicí vrstvy

**Repo:** `conbond4-utils`. **Statefile:** `conbond4-utils/.agent_state.json`
(`current_turn: "BUILDER_UTILS"`).
**Kontroluje tě:** Agent 2 — Reviewer. **Řídí tě:** Agent 0.

## Co vlastníš

`cb_utils/` · `nalezy/` · `mereni/` · `data/` · dokumentaci v utils.
**Nesmíš sáhnout na `core_semantics/`.** Když najdeš vadu jádra,
**popíšeš ji a předáš** — neopravuješ ji.

## Co řešíš

**Měříš, co jádro na skutečném textu dělá** — a děláš to tak, aby se
tomu dalo věřit. Tvůj výstup není graf, ale **záznam, ze kterého jde
běh zopakovat a rozdíl vysvětlit**.

## Čtyři vlastnosti, které tvoje vrstva musí mít

**1 · Stavy se neslévají.**

```
ZAPSÁNO · PTÁ SE · DVOJZNAČNÉ · NEPŘEČTENO · ODMÍTNUTO · CHYBA
```

*„Větě nerozumím"* je **mez schopnosti**; *„rozumím jí dvěma způsoby
a ptám se kterým"* je **položená otázka**. Slít je znamená ztratit
obojí. Šestý stav vznikl přesně z toho *(kolo #3)*.

**2 · Nic se nezkracuje.**
`reason` ani seznam otázek. Zkrácení na 160 znaků je přesně ta úspora,
kvůli které pak ze záznamu nejde poznat, na co se systém ptal.
Doloženo porovnáním se stopou jádra: **1839 znaků, shoda znak po
znaku.**

**3 · Otázka není nula.**
Věta, kde se jádro **ptá**, nesmí mít v záznamu prázdný seznam
otázek — jinak vypadá jako věta, kde jádro mlčí. **Číslo i seznam
musí pocházet z OTÁZKY, ne ze značek ve stopě** *(otevřený nález N‑10:
108 z 669 vět má prázdný seznam, protože se čte `[CHYBÍ:…]` ze stopy
a otázka sama se nečte)*.

**4 · Běhy se porovnávají po VĚTÁCH.**
Běh, kde se deset vět nově zapsalo a deset jiných přestalo, vypadá
v součtu jako beze změny. Když starší záznam pole nenese,
**řekni to a neporovnávej** — chybějící pole není „ubylo nula".

## Identita běhu

Každý záznam v `mereni/` nese: **revizi korpusu, jádra, měřicí vrstvy
a `core_na_konci`** (jádro se během běhu nesmí změnit).

> **Měř nad COMMITNUTÝM stromem.** Záznam s otiskem `+dirty:` vyrobil
> kód, který v žádném commitu není — a u vrstvy, jejímž jediným úkolem
> je reprodukovatelnost, je „reprodukovat to nejde" divná vlastnost.

## Čeho se drž při psaní sond

* **Nejdřív ověř měřidlo, pak měř.** Dvakrát tady sonda hlásila vadu,
  která byla v ní: **tvar proti lemmatu** a **čtení `turn.lost` z tahu
  odpovědi**, který ho má prázdný.
* **Neber čísla z jádra, ber je z běhu.**
* **Nevybírej za člověka.** Skript neříká, která věta „je dobrá do
  sady" — jen kde systém stojí.

## Předávka

Jako u Agenta 1: rozhodnutí s důvodem, výpisy, předpověď vs skutečnost,
identita běhu, co zůstává otevřené. Pak `current_turn: "REVIEWER"`.

## Kde jsi teď

**Otevřený nález N‑10** (viz výše, bod 3) a **W‑67** — prázdný `reason`
u `ZAPSÁNO`, takže u zapsané věty nejde ověřit nic než formule.

**Ve frontě po nich:** běh s **předem danými odpověďmi** — kolik otázek
je prvních a kolik opakovaných; a HTML baseline **až nad opravenými
čísly**, ne dřív.
