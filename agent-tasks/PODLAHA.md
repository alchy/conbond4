# PODLAHA — čísla, která nesmí klesnout

**Stav ke kolu #129** (jádro 0.1.62, `d64d63e`). Každé číslo je
**naměřené během**, ne odhad. Kdo odevzdává tah, měří **celou** tuhle
tabulku a přikládá výpis.

## Jádro — technická podlaha

| co | hodnota | čím |
|---|---|---|
| zkoušky | **≥ 1215** zelených | `python -m pytest -q` |
| typy | **čistý** na 62 souborech | `python -m mypy --strict core_semantics/` |
| doložky | **≥ 92/92** držených | `core_semantics.contracts.CONTRACTS` |
| parita s živým rozborem | **55/55** token po tokenu | `tests/test_parity.py` + živý běh |
| `standing_metrics()` | **21 / 107 / 51 / 33 / 26** | `tests/dialogues.py` |
| jádrové relace | **9/9** | `before, complete, contains, disjoint, member, name, same_as, subset, within` |
| gate *Farmaka* | zelený (`N` / `s0005`) | zlatá sada |
| `RECALL_FAILURE` | **0**, `U` = 11 | běh domén |

## Jádro — sémantická podlaha

| vlastnost | hodnota | odkud |
|---|---|---|
| řetěz disjoint expanzí | **žádný falešný `CycleDetected`**, verdikt `N` | B‑1 |
| dotaz nezaloží uzel | `derivation()` **nezakládá** nic mimo `attach()` | B‑2 |
| matice ⪯ | `∀ × konkrétní → A`, **`konkrétní × ∃ → U`** | § 3.3, dialog B |
| disjoint / absence | `N` / **`U`** (absence ≠ negace) | I‑21 |
| CONFLICT | nese **oba** důkazy | § 5 |
| sortové stráže | **6/6** zabírají | § 9 |
| `before(t,t)` | odmítnuto, **báze to přežije** | contracts |
| `same_as` | přenáší **oběma směry**, **nic nemaže** | M‑1 |
| I‑16 | blokuje **9/9** jádrových predikátů | `Rule.__post_init__` |
| kvantifikátor | **jen** na `RoleTerm` | § 2 |

## Dialog — podlaha, kterou hlídá Reviewerova sonda

| vlastnost | hodnota |
|---|---|
| vět s víc než jedním čekajícím členem | **180** |
| po odpovědi na jeden tvar se **mlčí o někom** | **0** |
| překlop `◐ → ✓` po odpovědi | **0** |
| hlášení „ČTENÍ SE NEZMĚNILO" u změněné značky | **0** |
| W‑71 (zmlklý závislý člen) | **0** |
| tvarů, které se po odpovědi ptají znovu | **0 ze 150** |
| kolektivní čtení prosakuje na jednotlivce | **ne** (`zvedl klavír Petr?` = `U`) |
| `revoke_utterance` vezme zpět celou větu | **ano**, na obou cestách |
| `revoke_utterance` strhne cizí promluvu | **ne** |
| `·Hradec_Králové` se složí · `Rožnov pod Radhoštěm` se nezapíše a nese `◐` | **ano** |

## Korpus

| korpus | stav |
|---|---|
| Wikipedie, **238 vět** | běh **bez pádu**; `219 PTÁ SE / 14 NEPŘEČTENO / 2 DVOJZNAČNÉ / 1 ZAPSÁNO / 2 CHYBA` |
| conBond2 `@418d7f7`, **836 vět** | `31 ZAPSÁNO / 669 PTÁ SE / 7 DVOJZNAČNÉ / 124 NEPŘEČTENO / 5 CHYBA / 0 ODMÍTNUTO` |
| dialog do konce, 20 vět | **1 zapsaná**, 2 tahy — 19 stojí na **jmenné frázi** |

## Největší otevřená věc

```
ztracené členy podle toho, POD ČÍM visí (238 vět)
  pod JMÉNEM     937    nmod 289 · amod 276 · conj 102 · flat 85 · acl:relcl 47
  pod SLOVESEM   184    nsubj 43 · obl 39 · obj 36
```

**Čtení jmenné fráze je pětkrát větší než všechno na slovese
dohromady** a je to **chybějící schopnost**, ne vada.

> **Když některé číslo klesne, není to samo o sobě FAIL — je to
> povinnost vysvětlit to MĚŘENÍM, ne dodatečným příběhem.** Práh se
> smí posunout (stalo se to u „178 → 174"), ale pak se musí ukázat
> vlastnost, která posun nahrazuje.
