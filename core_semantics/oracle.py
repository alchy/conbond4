"""Vnější orákulum morfologie a syntaxe — § 5.1 zadání.

> „Parser je vnější orákulum morfologie a syntaxe, ale jeho výstup se bere
> jako **návrh**. Kde je rozbor tvarově nejednoznačný, pracuje se
> s množinou kandidátních čtení."

Tři vlastnosti, které z toho plynou a které tenhle modul drží:

1. **Výstupem NENÍ jeden strom.** `Utterance.readings` je n-tice od prvního
   dne, i když dnešní orákulum vrací jedno čtení. Typ nesmí lhát o tom, co
   § 5.2 (kaskáda výběru) bude potřebovat — jinak by se pluralita dodělávala
   později přes celou vrstvu.
2. **Hranice vede po procesu, ne po prostředí.** Klient je čistá stdlib
   a mluví s běžící službou přes HTTP. Model ani jeho běhové závislosti se
   do `conbond4` nedostanou.
3. **Rozbor nese provenienci s verzí modelu i tokenizéru.** Zlaté
   transkripty (§ 10, přehratelnost) fixují rozbor; kdyby se model
   upgradoval potichu, transkripty by tiše driftovaly. S proveniencí
   selžou nahlas.

Co tenhle modul NEDĚLÁ: nepřekládá strom na strukturu. To je V2 (kaskáda
čtení, § 5.2) a je to samostatný krok — orákulum jen navrhuje.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol, Sequence

#: Základní adresa modulu `cb-udpipe` (samostatný proces, REST).
DEFAULT_ENDPOINT = "http://127.0.0.1:42200"
#: Ověřovací dotaz v konstruktoru je krátký schválně — `GET /version` nesahá
#: na data, takže na místní smyčce odchází v jednotkách milisekund.
CHECK_TIMEOUT_S = 2.0
PARSE_TIMEOUT_S = 30.0


class OracleError(RuntimeError):
    """Orákulum nedokázalo odpovědět. Nikdy se nenahrazuje odhadem (I‑1)."""


class OracleUnavailable(OracleError):
    """Služba neběží nebo neodpovídá."""


# --------------------------------------------------------------------------
# Tvar rozboru
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Token:
    """Jeden token závislostního rozboru. Imutabilní a hashovatelný, aby
    šel rozbor uložit do zlatého transkriptu a porovnat."""

    index: int
    form: str
    lemma: str
    upos: str
    head: int
    deprel: str
    feats: tuple[tuple[str, str], ...] = ()

    def feat(self, name: str) -> str | None:
        for key, value in self.feats:
            if key == name:
                return value
        return None

    def __str__(self) -> str:
        marks = "|".join(f"{k}={v}" for k, v in self.feats) or "_"
        return (
            f"{self.index}\t{self.form}\t{self.lemma}\t{self.upos}\t"
            f"{marks}\t{self.head}\t{self.deprel}"
        )


@dataclass(frozen=True, slots=True)
class Reading:
    """Jedno kandidátní čtení věty."""

    tokens: tuple[Token, ...]
    #: Model a verze tokenizéru, ze kterých rozbor pochází.
    provenance: str

    def root(self) -> Token | None:
        for token in self.tokens:
            if token.head == 0:
                return token
        return None

    def children(self, index: int) -> tuple[Token, ...]:
        return tuple(token for token in self.tokens if token.head == index)

    def by_deprel(self, deprel: str) -> tuple[Token, ...]:
        return tuple(token for token in self.tokens if token.deprel == deprel)

    def render(self) -> str:
        return "\n".join(str(token) for token in self.tokens)


@dataclass(frozen=True, slots=True)
class Utterance:
    """Promluva a její kandidátní čtení (§ 5.1).

    Prázdná n-tice čtení je legitimní výsledek — orákulum smí říct „neumím",
    a je to poctivější než vrátit dohad."""

    text: str
    readings: tuple[Reading, ...]

    @property
    def unambiguous(self) -> Reading | None:
        return self.readings[0] if len(self.readings) == 1 else None


class ParseOracle(Protocol):
    """Smlouva orákula. `Session` ani kaskáda čtení nesmí vědět, jestli
    za tím je HTTP služba, nahraný transkript nebo keš.

    `provenance` je součást smlouvy, ne pohodlí implementace: kdo staví keš
    nebo zlatý transkript, musí umět zjistit **před** voláním, z jakého
    modelu rozbory pocházejí. Prázdný řetězec znamená „nevím" a je to
    legitimní odpověď — jen se pod ním nesmí nic kešovat.
    """

    @property
    def provenance(self) -> str: ...

    def parse(self, text: str) -> Utterance: ...


# --------------------------------------------------------------------------
# CoNLL-U / JSON → tokeny
# --------------------------------------------------------------------------


def parse_feats(raw: str | None) -> tuple[tuple[str, str], ...]:
    """`Case=Nom|Gender=Masc` → setříděné dvojice.

    Setřídění je kvůli determinismu: pořadí rysů ve výstupu modelu není
    smluvně dané a zlatý transkript by na něm neměl viset (I‑4).
    """
    if not raw or raw == "_":
        return ()
    pairs: list[tuple[str, str]] = []
    for item in raw.split("|"):
        key, _, value = item.partition("=")
        if key and value:
            pairs.append((key, value))
    return tuple(sorted(pairs))


def token_from_json(raw: Mapping[str, object]) -> Token:
    return Token(
        index=int(str(raw.get("id", 0))),
        form=str(raw.get("form", "")),
        lemma=str(raw.get("lemma") or raw.get("form", "")),
        upos=str(raw.get("upos") or "X"),
        head=int(str(raw.get("head") or 0)),
        deprel=str(raw.get("deprel") or "dep"),
        feats=parse_feats(
            None if raw.get("feats") is None else str(raw.get("feats"))
        ),
    )


# --------------------------------------------------------------------------
# Orákula
# --------------------------------------------------------------------------


class RecordedOracle:
    """Nahrané rozbory — základ zlatých transkriptů a hermetických testů.

    Neznámý text je **hlasitá chyba**, ne tichý průchod na síť: test, který
    si nepozorovaně sáhne na běžící službu, přestane být hermetický a začne
    padat podle toho, co je zrovna spuštěné.
    """

    def __init__(
        self, recordings: Mapping[str, Utterance], *, provenance: str = ""
    ) -> None:
        self._recordings = dict(recordings)
        stamps = {
            reading.provenance
            for utterance in self._recordings.values()
            for reading in utterance.readings
        }
        if len(stamps) > 1:
            raise OracleError(
                f"nahrané rozbory míchají dvě provenience {sorted(stamps)}; "
                f"zlatý transkript musí fixovat JEDEN rozbor, jinak není čím "
                f"poznat, kdy se model změnil"
            )
        self.provenance = stamps.pop() if stamps else provenance

    def parse(self, text: str) -> Utterance:
        try:
            return self._recordings[text]
        except KeyError:
            raise OracleError(
                f"pro text {text!r} není nahraný rozbor; nahrané: "
                f"{sorted(self._recordings)}"
            ) from None

    def known(self) -> tuple[str, ...]:
        return tuple(sorted(self._recordings))


class CachingOracle:
    """Keš klíčovaná **proveniencí i textem**.

    Kdyby klíč nesl jen text, upgrade modelu by se schoval za starý záznam
    a systém by odpovídal podle rozboru, který už nikdo nedokáže zopakovat.

    Klíč zápisu i čtení pochází z **jednoho zdroje** — z provenience
    vnitřního orákula. Když se lišily (zápis z rozboru, čtení z objektu),
    keš míjela úspěchy a přitom trvale ukládala selhání pod zástupný klíč;
    to je horší než žádná keš, protože se to nedá poznat z výstupu.

    Dvě věci se nekešují nikdy: **neznámá provenience** (pod „nevím" by se
    slily rozbory z různých modelů) a **promluva bez čtení** (prázdný
    výsledek může být i důsledek přechodné poruchy, a trvale zapamatované
    „neumím přečíst" by systém udrželo tvrdošíjně vedle).
    """

    def __init__(self, inner: ParseOracle) -> None:
        self._inner = inner
        self._store: dict[tuple[str, str], Utterance] = {}
        self.hits = 0
        self.misses = 0

    @property
    def provenance(self) -> str:
        return getattr(self._inner, "provenance", "") or ""

    def parse(self, text: str) -> Utterance:
        stamp = self.provenance
        key = (stamp, text)
        if stamp:
            cached = self._store.get(key)
            if cached is not None:
                self.hits += 1
                return cached
        self.misses += 1
        utterance = self._inner.parse(text)
        if stamp and utterance.readings:
            self._store[key] = utterance
        return utterance

    def stored(self) -> int:
        return len(self._store)


Transport = Callable[[str, bytes | None, float], bytes]


def _urllib_transport(url: str, body: bytes | None, timeout: float) -> bytes:
    request = urllib.request.Request(
        url,
        data=body,
        method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json"} if body else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return bytes(response.read())
    except urllib.error.URLError as exc:  # pragma: no cover — síťová cesta
        raise OracleUnavailable(f"{url}: {exc}") from exc


class UDPipeOracle:
    """Tenká fasáda nad běžící službou `cb-udpipe`.

    **Selže při vytvoření, ne při prvním volání.** Klient nad neběžící
    službou je tikající chyba: ukázala by se uprostřed dialogu, s polovinou
    tahů už zapsaných.

    Doprava se injektuje, aby šly testy vést bez sítě i bez služby.
    """

    def __init__(
        self,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        transport: Transport = _urllib_transport,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self._transport = transport
        self.provenance = self._handshake()

    def _handshake(self) -> str:
        payload = self._call("/version", None, CHECK_TIMEOUT_S)
        model = str(payload.get("model", "?"))
        tokenizer = str(payload.get("tokenizer", payload.get("version", "?")))
        return f"udpipe2 model={model} tokenizer={tokenizer}"

    def parse(self, text: str) -> Utterance:
        payload = self._call(
            "/v1/parse", {"text": text, "trace": None}, PARSE_TIMEOUT_S
        )
        sentences = payload.get("sentences", [])
        if not isinstance(sentences, list):
            raise OracleError(f"neočekávaný tvar odpovědi pro {text!r}")
        readings: list[Reading] = []
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            tokens = sentence.get("tokens", [])
            if not isinstance(tokens, list):
                continue
            readings.append(
                Reading(
                    tokens=tuple(
                        token_from_json(item)
                        for item in tokens
                        if isinstance(item, dict)
                    ),
                    provenance=self.provenance,
                )
            )
        return Utterance(text=text, readings=tuple(readings))

    def _call(
        self, path: str, body: Mapping[str, object] | None, timeout: float
    ) -> Mapping[str, object]:
        encoded = None if body is None else json.dumps(body).encode("utf-8")
        raw = self._transport(f"{self.endpoint}{path}", encoded, timeout)
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise OracleError(f"{path}: odpověď nejde přečíst — {exc}") from exc
        if not isinstance(decoded, dict):
            raise OracleError(f"{path}: očekáván objekt, přišlo {type(decoded)}")
        return decoded


def recorded(text: str, tokens: Sequence[Token], *, provenance: str) -> Utterance:
    """Pohodlný konstruktor nahraného rozboru pro zlaté transkripty."""
    return Utterance(
        text=text,
        readings=(Reading(tokens=tuple(tokens), provenance=provenance),),
    )
