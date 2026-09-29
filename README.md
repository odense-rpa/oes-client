# oes-client

Playwright-baseret Python-klient til OES (økonomi- og regnskabssystem) — giver automatiseret adgang til brugeradministration og bilagshåndtering via ØS Indsigt-webgrænsefladen.

> Denne klient er ikke officielt støttet eller godkendt af leverandøren bag OES. Brug på eget ansvar.

## Nuværende funktionalitet

- Autentificering via Microsoft/Azure AD SSO med kommunalt brugernavn og adgangskode
- **Brugere** (`oes.brugere`): søg bruger og spær bruger/fjern al adgang
- **Bilag** (`oes.bilag`): søg, hent XML, konter, varemodtag og ret bemærkning på bilag
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

- `udsoeg_bilag(regnskabsaar_fra, regnskabsaar_til, afdelingsnummer, ...)` — søg bilag på bilagsoversigten
- `hent_bilags_xml(bilagsid)` — hent den originale faktura-XML (OIOUBL)
- `parse_konteringslinjer(xml)` — udtræk fakturalinjer fra XML (kræver ingen browser)
- `opret_konteringslinjer(bilagsid, linjer, bemaerkning)` — linjerne skal summe til bilagets beløb
- `varemodtag_bilag(bilagsid, cpr, kontonummer, posteringstekst, bemaerkning, b_skat)`
- `varemodtag_bilag_konteret(bilagsid, bemaerkning)`
- `aendre_bemaerkning(bilagsid, bemaerkning)`

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
