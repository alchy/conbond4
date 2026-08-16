# PROTOKOL — statefile, tah, předávka

## 1 · Statefile

Každé repo má v kořeni `.agent_state.json`. **Je to jediný kanál
předávky.** Nic se nepředává „v hlavě sezení" ani komentářem v kódu.

```json
{
  "current_turn": "BUILDER" | "REVIEWER" | "BUILDER_UTILS",
  "status": "READY_FOR_REVIEW" | "PASS_NEXT_PHASE" | "FAIL",
  "last_action": "…celý text předávky…"
}
```

| pole | kdo ho píše | co znamená |
|---|---|---|
| `current_turn` | ten, kdo tah **odevzdává** | čí je tah TEĎ |
| `status` | odevzdávající | `READY_FOR_REVIEW` = hotovo, zkontroluj · `PASS_NEXT_PHASE` = prošlo, pokračuj · `FAIL` = nález, oprav |
| `last_action` | odevzdávající | **celá** předávka: co, proč, čím doloženo, co dál |

**Pravidla, která už jednou zachránila kolo:**

* **Statefile se čte znovu těsně před zápisem.** Mezi tvým prvním
  přečtením a zápisem mohl tah převzít někdo jiný.
* **`last_action` není nadpis, je to zpráva.** Píše se tak, aby druhá
  strana **nemusela nic dohledávat**: čísla, výpisy, jména vět.
* **V `conbond4` je statefile v `.gitignore`, v `conbond4-utils` je
  verzovaný.** Je to nedůslednost — **sjednoťte ji vědomě**, ne mlčky;
  než se tak stane, počítejte s tím, že stav jádra se pullem nepřenese.

## 2 · Tah

**Tah má v jednu chvíli právě jeden agent.** Kdo ho nemá, **monitoruje
a mlčí**.

```
BUILDER  ──[READY_FOR_REVIEW]──►  REVIEWER  ──[PASS_NEXT_PHASE]──►  BUILDER
                                       │
                                       └────[FAIL]────►  BUILDER (oprava)
```

**Reviewer nikdy neopravuje.** Najde, doloží, pojmenuje vlastnost,
kterou chce vidět splněnou — a vrátí tah. **Builder nikdy nepíše
verdikt.** Jsou to dvě různé role a jejich smíchání je konec kontroly.

## 3 · Co musí být v předávce od Buildera

1. **Co jsi rozhodl a PROČ** — u každé volby, kde byly aspoň dvě cesty.
   *„Rozhodl jsem X"* bez důvodu je pro Reviewera nedoložitelné.
2. **Root cause**, ne popis symptomu.
3. **Výpis z běhu** u každého tvrzení. **Žádné „ověřeno úvahou".**
4. **Zkoušky, které tu vadu prokazatelně chytí** — nejlíp doloženo
   **mutací**: vrať vadu, ukaž, že test spadl, vrať opravu.
5. **Předpověď na projev PŘED kódem** a po běhu **rozdíl mezi
   předpovědí a skutečností**. Odchylka je cennější než trefa.
6. **Celá stálá podlaha** (viz [PODLAHA.md](PODLAHA.md)) a **běh před
   předávkou**, ne z paměti.
7. **Co zůstává otevřené**, jmenovitě.

## 4 · Co musí být ve verdiktu od Reviewera

Formát `REVIEW.md` (nový verdikt se **předsazuje**, starý se archivuje):

```markdown
## Status: 🟢 PASS | 🔴 FAIL — jedna věta, o co jde
**Architectural Health Score: x,y / 10.**
## Co jsem ověřil sám            ← reprodukce, ne převzatá čísla
## Critical Blockers             ← s výpisem a s rozsahem
## Semantic Warnings
## Action Items for Agent 1|3    ← vlastnost jako PROTIPŘÍKLAD + přejímací čísla
```

**Reviewer smí zapisovat výhradně do `REVIEW.md`, `REVIEW-UTILS.md`
a statefile.** Ani řádek v `core_semantics/`, `tests/`, `cb_utils/`.

## 5 · Commit a push

* Zpráva commitu je **detailní** — uživatel pulluje napříč Windows,
  macOS i Linuxem a chce po pullu rozumět **bez doptávání**.
* Commituje se **až po zeleném běhu**, ne před ním.
* Verdikt Reviewera se commituje **spolu** s prací, které se týká.

## 6 · Když si dva agenti nesedí v číslech

**Neopravuj cizí číslo dopočítáním. Zeptej se na definici.**
V tomhle projektu to už dvakrát rozhodlo spor a **v obou případech se
mýlil ten, kdo si to dopočítal sám.** Formulace, která funguje:

> „Vychází mi N, tobě M. Počítám to jako *…definice…*. Kterou definici
> jsi použil? Doměřím to."
