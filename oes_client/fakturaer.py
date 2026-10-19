"""Fakturaer (debitorposteringer) i ØS Indsigt // Debtor invoices in ØS Indsigt.

Port af Blue Prism-handlingen "Søg fakturaer" i objektet "ØS Indsigt (Chrome) VBO".
"""

import re

from playwright.sync_api import TimeoutError

from .bilag import _dansk_dato, _dansk_tal
from .selectors import BilagFrames as bf
from .selectors import BilagSelectors as bs
from .selectors import FakturaFrames as ff
from .selectors import FakturaSelectors as fs
from .session import OESSession

# kolonner i en fakturarække (11 celler) // columns of an invoice row (11 cells)
KOL_CPR, KOL_DATO, KOL_NR, KOL_REST, KOL_FORFALD, KOL_TYPE, KOL_ART, KOL_INST = (
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
)
ANTAL_CELLER = 11


def udtraek_cpr(tekst: str) -> str:
    """Udtrækker et cpr-nummer (10 cifre, med eller uden bindestreg) fra en tekst."""
    match = re.search(r"(?<!\d)(\d{6})-?(\d{4})(?!\d)", tekst)
    if not match:
        raise ValueError("Teksten indeholder ikke et cpr-nummer")
    return "".join(match.groups())


def parse_fakturarader(raekker: list[list[str]]) -> list[dict]:
    """Omsætter resultatrækker til fakturaer. Overskrifts- og sumrækker (som ikke har
    institutionsnummer) springes over. Kræver ingen browser."""
    fakturaer = []
    for raekke in raekker:
        if len(raekke) != ANTAL_CELLER or not raekke[KOL_INST].strip():
            continue
        fakturanr = raekke[KOL_NR].strip()
        fakturaer.append(
            {
                "cpr": raekke[KOL_CPR].replace("-", "").strip(),
                "faktura_dato": _dansk_dato(raekke[KOL_DATO]),
                "fakturanr": int(fakturanr) if fakturanr.isdigit() else None,
                "rest_beloeb": _dansk_tal(raekke[KOL_REST]),
                "forfaldsdato": _dansk_dato(raekke[KOL_FORFALD]),
                "type": raekke[KOL_TYPE].strip(),
                "art": raekke[KOL_ART].strip(),
                "institution": raekke[KOL_INST].strip(),
            }
        )
    return fakturaer


class FakturaClient:
    """Fakturaer (debitorposteringer) // Debtor invoices.

    Oprettes af OESClient og tilgås som oes.fakturaer.
    """

    def __init__(self, session: OESSession):
        self._session = session

    def soeg_fakturaer(
        self, cpr: str, art: str = "258", bilagstype: str = "Alle"
    ) -> list[dict]:
        """Finder alle fakturaer af en given art i alle institutioner for et cpr-nummer.

        Svarer til Blue Prism-handlingen "Søg fakturaer". Søgningen ændrer intet i ØS.

        Args:
            cpr: Cpr-nummer, med eller uden bindestreg.
            art: Fordringsart (standard "258", som i Blue Prism).
            bilagstype: "Alle", "Faktura", "Kreditnota", "Faktura/Kreditnota" eller
                "Tilbagevendende".

        Returns:
            Liste af dicts med nøglerne cpr, faktura_dato (date), fakturanr (int),
            rest_beloeb (float), forfaldsdato (date), type ("Faktura"/"Kreditnota"),
            art og institution. Tom liste hvis ØS ikke har nogen posteringer.

        Raises:
            ValueError: Hvis cpr ikke er et gyldigt cpr-format.
            OESFejl: Hvis ØS svarer med en anden fejl.
            TimeoutError: Hvis ØS ikke svarer, eller siden ikke ser ud som forventet.
        """
        cpr = udtraek_cpr(cpr)

        self._session.naviger(fs.LINK)
        frame = self._session.frame_med(fs.INSTITUTION, ff.FAKTURAOVERSIGT)
        frame.locator(fs.INSTITUTION).select_option(label="Alle institutioner")
        frame.locator(fs.BILAGSTYPE).select_option(label=bilagstype)
        frame.locator(fs.SOEGETYPE).select_option(label="Art")
        frame.locator(fs.DEBITOR_FRA).fill(cpr)
        frame.locator(fs.ART_FRA).fill(art)

        self._session.klik(bs.VIS_KNAP, ff.FAKTURAOVERSIGT_BTM)
        self._session.vent_paa_loading()

        # ved kun ét resultat åbner ØS fakturaen direkte - gå tilbage til listen
        # // with a single hit ØS opens the invoice directly - go back to the list
        try:
            i, _ = self._session.vent_paa_en_af(
                [
                    (bs.TILBAGE_KNAP, bf.BTM),
                    (bs.SIDETALSVAELGER, None),
                    (bs.FEJLLISTE, None),
                ],
                20_000,
            )
        except TimeoutError:
            raise TimeoutError(
                "Søgning efter fakturaer lykkedes ikke: hverken resultat eller fejlbesked fra ØS"
            ) from None
        if i == 0:
            self._session.klik(bs.TILBAGE_KNAP, bf.BTM)
            self._session.vent_paa_loading()

        return parse_fakturarader(self._session.hent_resultattabel())
