# oes-client

Playwright-baseret Python-klient til OES (økonomi- og regnskabssystem) — giver automatiseret adgang til brugeradministration og bilagshåndtering via ØS Indsigt-webgrænsefladen.

> Denne klient er ikke officielt støttet eller godkendt af leverandøren bag OES. Brug på eget ansvar.

## Nuværende funktionalitet

- Autentificering via Microsoft/Azure AD SSO med kommunalt brugernavn og adgangskode
- **Brugere** (`oes.brugere`): søg bruger og spær bruger/fjern al adgang
- **Bilag** (`oes.bilag`): søg, hent XML, konter, varemodtag og ret bemærkning på bilag
- **Fakturaer** (`oes.fakturaer`): søg debitorfakturaer på et cpr-nummer
- Understøtter brug som kontekst-manager (`with`-sætning)

## Installation

```bash
uv add git+https://github.com/odense-rpa/oes-client
```

## Forudsætninger

- Python ≥ 3.13
- Adgang til OES-webgrænsefladen
- Gyldige Microsoft SSO-legitimationsoplysninger til kommunens brugerkonto

## Brug

```python
from oes_client import OESClient

with OESClient(base_url, username, password) as oes:
    oes.brugere.fremsoeg_bruger("ABC")
    oes.brugere.slet_bruger()

    bilag = oes.bilag.udsoeg_bilag(2025, 2026, "4514800302")
```

`base_url` bestemmer miljøet, fx `https://odensetest.osi-local.dk/mod-core` for test og
`https://odense.osi-local.dk/mod-core` for produktion.

### Brugere (`oes.brugere`)

- `fremsoeg_bruger(bruger_id)` — søg bruger og husk den til næste kald
- `slet_bruger()` — nulstiller kassefelter, sætter bruger-spærret, fjerner adgangsgrupper,
  afdelings- og institutionsnumre

### Bilag (`oes.bilag`)

Port af Blue Prism objektet "ØS Indsigt (Chrome) VBO", som bruges af betalingsprocesserne:

- `udsoeg_bilag(regnskabsaar_fra, regnskabsaar_til, afdelingsnummer, ...)` — søg bilag på bilagsoversigten; statusfiltre som bool-parametre (`ubehandlet` og `kladde` er `True`, øvrige `False` som standard)
- `hent_bilags_xml(bilagsid)` — hent den originale faktura-XML (OIOUBL)
- `parse_konteringslinjer(xml)` — udtræk fakturalinjer fra XML (kræver ingen browser)
- `opret_konteringslinjer(bilagsid, linjer, bemaerkning)` — linjerne skal summe til bilagets beløb
- `varemodtag_bilag(bilagsid, bemaerkning)` — skriver bemærkning og varemodtager; konteringslinjer oprettes med `opret_konteringslinjer`
- `aendre_bemaerkning(bilagsid, bemaerkning)`

### Fakturaer (`oes.fakturaer`)

Port af Blue Prism-handlingen "Søg fakturaer" (Regningsdebitor > Faktura, "Debitor posteringer"):

- `soeg_fakturaer(cpr, art="258", bilagstype="Alle")` — finder alle fakturaer af en given art i alle
  institutioner for et cpr-nummer (med eller uden bindestreg). Returnerer en liste af dicts med
  `cpr`, `faktura_dato`, `fakturanr`, `rest_beloeb`, `forfaldsdato`, `type` ("Faktura" eller
  "Kreditnota"), `art` og `institution`. Tom liste hvis ØS ingen posteringer har. Søgningen læser kun.

```python
fakturaer = oes.fakturaer.soeg_fakturaer("000000-0000")
```

- `opret_faktura(cpr, varetekst, varenummer="401", antal=1, institution="281", art="258", ...)` — opretter
  en faktura med én linje på et cpr-nummer (port af "Opret faktura-flyttebøde"). Pris og kontonummer
  udfyldes af ØS ud fra varenummeret. Returnerer `True` når fakturaen er oprettet og `False` hvis ØS
  melder, at den allerede findes. **Ændrer data i ØS.** Personen skal findes i ØS (ellers `OESFejl`).

Fejl: `OESFejl` for forretningsfejl fra ØS (fx valideringsfejl), `BilagIkkeFundet` når bilaget
ikke findes. Playwright `TimeoutError` betyder, at ØS ikke svarede eller siden ikke så ud som
forventet.

### Flere browserklienter i samme proces

Playwrights sync-API tillader kun én instans pr. tråd. Skal OESClient køre sammen med
andre Playwright-baserede klienter (fx nfs-client), så start én instans og giv den til
dem alle. Hver klient får stadig sin egen browser, sit eget vindue og sit eget login.
Den delte instans stoppes ikke, når klienten lukkes; det gør `with`-blokken.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    with OESClient(base_url, username, password, playwright=pw) as oes, \
         NFSClient(anden_url, username, password, playwright=pw) as nfs:
        ...
```

Uden `playwright` (standard) starter og stopper klienten sin egen instans som hidtil.

### Fejlsøgning af en proces der hænger

```python
with OESClient(base_url, username, password, hang_dump_sekunder=600) as oes:
    ...
```

Sker der ingen ny navigation i 600 sekunder, skriver Python stacktrace for alle tråde til
stderr (og igen hvert 600. sekund). Processen kører videre. Stacktracen viser hvilken linje
i `oes_client` den hænger i.

## Arkitektur

- `OESSession` (`session.py`) ejer browseren, login og de fælles hjælpere: frames, ventetider,
  navigation og fejlbeskeder.
- Hvert område er en lille klient, der får sessionen: `BilagClient` (`bilag.py`),
  `BrugerClient` (`brugere.py`).
- `OESClient` (`client.py`) opretter sessionen og områderne og samler dem som `oes.bilag`,
  `oes.brugere`, ...

Nyt område: opret `oes_client/<omraade>.py` med `class XClient: def __init__(self, session)`,
læg selectors i `selectors.py`, tilføj `self.<omraade> = XClient(self.session)` i `OESClient`, og
skriv `tests/test_<omraade>.py` med `oes`-fixturen.

## Ændringer i 0.6.4

- `udsoeg_bilag` tager bilagsstatus som bool-parametre (`ubehandlet`, `behandles`,
  `foranvises`, `konteret`, `bogfoeres`, `efteranvises`, `bogfoert`, `sendte`, `kladde`,
  `varemodtaget`, `inaktiveret`). `ubehandlet` og `kladde` er `True` som standard, de
  øvrige `False`.
- `opret_konteringslinjer` håndterer bilag med mere end 100 linjer (maks 1000).
- `aendre_bemaerkning` kan også ændre bilag under behandling.
- Playwright er låst til 1.54.0 for at matche produktion.
- `varemodtag_bilag(bilagsid, bemaerkning)` skriver kun bemærkning og varemodtager.
  Konteringslinjer (inkl. b-skat) oprettes med `opret_konteringslinjer`.
- `varemodtag_bilag_konteret` er fjernet - brug `varemodtag_bilag`.
- `varemodtag_bilag` bruger bilaget direkte, hvis det allerede er åbent (fx lige efter
  `opret_konteringslinjer`), i stedet for at søge det frem igen.
- Gem registrerer nu et gem, der lykkedes, også når ØS er langsom eller kun viser
  "E-Bilaget er gemt". Retter fejlen "Fandt ikke 'input[alt^="Gem - Alt+2"]'".
- Ventetiden på genindlæsning efter klik gav timeout, selvom siden var indlæst.
  `OESSession.vent_paa_genindlaesning` er erstattet af `klik_og_vent_paa_genindlaesning`.

## Ændringer i 0.6.1

- Retter `opret_faktura`: ventede ikke på at ØS slog prisen op ud fra varenummeret, så
  fakturaen kunne blive gemt med pris 0. Venter nu på en pris over 0 og rejser `OESFejl`
  før Gem, hvis den udebliver. Ingen brud på API'et.

## Ændringer i 0.5.0

- `OESClient(..., playwright=pw)` tager en valgfri, delt Playwright-instans, så
  flere browserklienter kan køre i samme proces. Uden den opfører klienten sig
  som før. Ingen brud på API'et.

## Ændringer i 0.4.0

Brud på API'et:

- `OESClient(...).fremsoeg_bruger(x)` → `oes.brugere.fremsoeg_bruger(x)` (tilsvarende
  `slet_bruger`)
- `OESBilagClient(...)` → `OESClient(...).bilag`
- `fremsoeg_bruger` går nu direkte til brugeradministration og bruger `base_url` i stedet for
  en fast produktions-URL

## Test

Kopier `.env.example` til `.env` og udfyld. `tests/conftest.py` indlæser `.env` selv, så testene
opfører sig ens i terminal, VS Code og CI. Tests mod ØS springes over, hvis `BASE_URL`,
`OES_USERNAME` eller `OES_PASSWORD` mangler.

```bash
uv run pytest tests/test_bilag_xml.py   # offline
uv run pytest                           # alle, mod ØS (logger ind én gang)
```

`tests/test_bilag.py` kræver `TEST_AFDELINGSNUMMER` / `TEST_BILAGSID`, `tests/test_brugere.py`
kræver `TEST_BRUGER_ID`. Tests der ændrer data i ØS kræver desuden `OES_ALLOW_WRITE=1` (og evt.
`TEST_KONTERING_BILAGSID`, `TEST_CPR`, `TEST_KONTONUMMER`).

## Licens

MIT
