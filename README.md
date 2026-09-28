# oes-client

Playwright-baseret Python-klient til OES (økonomi- og regnskabssystem) — giver automatiseret adgang til brugeradministration via OES-webgrænsefladen.

> Denne klient er ikke officielt støttet eller godkendt af leverandøren bag OES. Brug på eget ansvar.

## Nuværende funktionalitet

- Autentificering via Microsoft/Azure AD SSO med kommunalt brugernavn og adgangskode
- Søg efter bruger med `fremsoeg_bruger(bruger_id)`
- Bloker bruger og fjern al adgang med `slet_bruger()` — nulstiller kassefelter, sætter bruger-blokeret-flag, fjerner adgangsgrupper, afdelingstalstildelinger og institutionsnummertildelinger
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

with OESClient() as client:
    client.authenticate(email="bruger@odense.dk", password="hemmeligt")
    client.fremsoeg_bruger("12345")
    client.slet_bruger()
```

## Bilagshåndtering (ØS Indsigt)

`OESBilagClient` (i `oes_client.bilag`) udvider `OESClient` med de ØS-handlinger, der bruges af
betalingsprocesserne (port af Blue Prism objektet "ØS Indsigt (Chrome) VBO"):

- `udsoeg_bilag(regnskabsaar_fra, regnskabsaar_til, afdelingsnummer, ...)` — søg bilag på bilagsoversigten
- `hent_bilags_xml(bilagsid)` — hent den originale faktura-XML (OIOUBL)
- `parse_konteringslinjer(xml)` — udtræk fakturalinjer fra XML (kræver ingen browser)
- `opret_konteringslinjer(bilagsid, linjer, bemaerkning)`
- `varemodtag_bilag(bilagsid, cpr, kontonummer, posteringstekst, bemaerkning, b_skat)`
- `varemodtag_bilag_konteret(bilagsid, bemaerkning)`
- `aendre_bemaerkning(bilagsid, bemaerkning)`

`BASE_URL` bestemmer miljøet, fx `https://odensetest.osi-local.dk/mod-core` for test.

## Test

Kopier `.env.example` til `.env` og udfyld. `tests/conftest.py` indlæser `.env` selv, så testene
opfører sig ens i terminal, VS Code og CI. Tests mod ØS springes over, hvis `BASE_URL`,
`OES_USERNAME` eller `OES_PASSWORD` mangler.

```bash
uv run python -m pytest tests/test_bilag_xml.py   # offline
uv run python -m pytest tests/test_bilag.py       # mod ØS
```

`tests/test_bilag.py` kræver `TEST_AFDELINGSNUMMER` / `TEST_BILAGSID`; tests der ændrer bilag kræver
desuden `OES_ALLOW_WRITE=1` (og evt. `TEST_CPR`, `TEST_KONTONUMMER`).

## Licens

MIT
