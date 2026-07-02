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

## Licens

MIT
