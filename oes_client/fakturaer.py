"""Fakturaer (debitorposteringer) i ØS Indsigt // Debtor invoices in ØS Indsigt.

Port af Blue Prism-handlingen "Søg fakturaer" i objektet "ØS Indsigt (Chrome) VBO".
"""

import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import TimeoutError

from .bilag import _dansk_dato, _dansk_tal
from .exceptions import OESFejl
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

# ØS' advarsel når fakturaen allerede findes // ØS warning when the invoice already exists
FINDES_ALLEREDE = "findes allerede en faktura"
MAKS_VARETEKST = 254


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


def _er_positivt_tal(tekst: str) -> bool:
    """Læser både "650.00" og "1.950,00" (dansk) og svarer, om tallet er over 0."""
    if "," in tekst:
        tekst = tekst.replace(".", "").replace(",", ".")
    try:
        return float(tekst) > 0
    except ValueError:
        return False


def _ddmmyyyy(dato) -> str:
    return dato.strftime("%d%m%Y")


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

    def opret_faktura(
        self,
        cpr: str,
        varetekst: str,
        varenummer: str = "401",
        antal: int = 1,
        institution: str = "281",
        art: str = "258",
        intern_tekst: str = "Folkeregisterbøde",
        behandler_tlf: str = "66131372",
        forfald_om_dage: int = 30,
        maks_forsoeg: int = 2,
    ) -> bool:
        """Opretter en faktura med én linje på et cpr-nummer.

        Svarer til Blue Prism-handlingen "Opret faktura-flyttebøde". Pris og kontonummer
        udfyldes af ØS ud fra varenummeret (401 giver bødens pris), og skal ikke angives.

        ÆNDRER DATA I ØS: opretter en faktura.

        Args:
            cpr: Debitorens cpr-nummer, med eller uden bindestreg.
            varetekst: Teksten på fakturalinjen (maks 254 tegn).
            varenummer: Varenummeret hos institutionen (standard "401").
            antal: Antal (standard 1).
            institution: Institutionsnummeret fakturaen oprettes på (standard "281").
            art: Betalingsart/fordringsart (standard "258").
            intern_tekst: Intern tekst på fakturaen.
            behandler_tlf: Telefonnummer på behandleren.
            forfald_om_dage: Forfaldsdato er i dag plus dette antal dage.
            maks_forsoeg: Antal gange der trykkes på Gem, før der gives op.

        Returns:
            True hvis fakturaen blev oprettet, False hvis ØS meldte, at den allerede findes
            (så der ikke oprettes en dublet).

        Raises:
            ValueError: Hvis cpr eller varetekst er ugyldigt.
            OESFejl: Hvis personen ikke findes i ØS, varenummeret ikke giver en pris, eller
                ØS afviser fakturaen.
            TimeoutError: Hvis ØS ikke svarer, eller siden ikke ser ud som forventet.
        """
        cpr = udtraek_cpr(cpr)
        if not varetekst.strip() or len(varetekst) > MAKS_VARETEKST:
            raise ValueError(f"Varetekst skal være 1-{MAKS_VARETEKST} tegn")

        # 1) åbn opret-siden på den rigtige institution
        self._session.naviger(fs.LINK)
        oversigt = self._session.frame_med(fs.INSTITUTION, ff.FAKTURAOVERSIGT)
        oversigt.locator(fs.INSTITUTIONSNR).fill(institution)
        self._session.klik(fs.OPRET_KNAP, ff.FAKTURAOVERSIGT_BTM)
        self._session.vent_paa_loading()
        try:
            self._session.frame_med(bs.GEM_KNAP, bf.BTM, timeout=20_000)
        except TimeoutError:
            raise TimeoutError(
                "Gem-knappen blev ikke fundet - ØS åbnede ikke opret-siden"
            ) from None
        side = self._session.frame_med(fs.DEBITORTYPE, ff.FAKTURADETALJER)

        # 2) debitor og bilagsinfo
        forfald = datetime.now(ZoneInfo("Europe/Copenhagen")).date() + timedelta(
            days=forfald_om_dage
        )
        side.locator(fs.DEBITORTYPE).select_option(label="CPR")
        side.locator(fs.DEBITOR).fill(cpr)
        side.locator(fs.FORFALDSDATO).fill(_ddmmyyyy(forfald))
        side.locator(fs.BETALINGSART).fill(art)
        side.locator(fs.INTERN_TEKST).fill(intern_tekst)
        side.locator(fs.BEHANDLER_TLF).fill(behandler_tlf)
        # change-hændelserne får ØS til at slå personen op
        # // the change events make ØS look up the person
        for felt in (fs.DEBITOR, fs.BETALINGSART):
            side.locator(felt).dispatch_event("change")
        self._session.vent_paa_loading()
        if not self._vent_paa_vaerdi(side, fs.DEBITORNAVN, 10_000):
            raise OESFejl("Fandt ikke adressehistorik for givet cpr")

        # 3) fakturalinje
        self._session.vent_paa_loading()
        side.locator(fs.LINJER_FANE).first.click()
        self._session.vent_paa_loading()
        side = self._session.frame_med(fs.VARENR, ff.FAKTURADETALJER, timeout=60_000)
        side.locator(fs.VARETEKST).fill(varetekst)
        side.locator(fs.ANTAL).fill(str(antal))
        side.locator(fs.VARENR).fill(varenummer)
        side.locator(fs.VARENR).dispatch_event("change")
        # ØS udfylder prisen ud fra varenummeret - uden pris ville fakturaen blive på 0 kr.
        # Feltet står på "0,00" fra start, så et tal er ikke nok: prisen skal være over 0
        # // the field starts at "0,00", so any value is not enough: the price must be > 0
        self._session.vent_paa_loading()
        if not self._vent_paa_vaerdi(side, fs.STYKPRIS, 10_000, kraev_positiv=True):
            raise OESFejl(f"Varenummer {varenummer} gav ingen pris i ØS")

        # 4) gem
        return self._gem(maks_forsoeg)

    def _vent_paa_vaerdi(
        self, frame, selector: str, timeout: float, kraev_positiv: bool = False
    ) -> bool:
        """Venter på at et felt får en værdi (fx efter et opslag i ØS).

        Med kraev_positiv skal værdien være et tal over 0 ("0,00" tæller som tom).
        """
        faerdig = time.monotonic() + timeout / 1000
        while True:
            vaerdi = frame.locator(selector).input_value().strip()
            if vaerdi and (not kraev_positiv or _er_positivt_tal(vaerdi)):
                return True
            if time.monotonic() > faerdig:
                return False
            self._session.page.wait_for_timeout(200)

    def _gem(self, maks_forsoeg: int) -> bool:
        """Trykker Gem og venter på, at siden genindlæses med Rediger-knappen (gemt)."""
        for forsoeg in range(maks_forsoeg):
            if forsoeg and self._session.soeg_frame(bs.REDIGER_KNAP, bf.BTM):
                return True  # den forrige Gem nåede at gemme
            gem = self._session.frame_med(bs.GEM_KNAP, bf.BTM).locator(bs.GEM_KNAP).first
            # den gamle Gem-knap står på siden lidt endnu - vent til ØS har genindlæst
            # // the old Gem button stays on the page for a moment - wait for ØS to reload
            try:
                self._session.klik_og_vent_paa_genindlaesning(gem, 30_000)
            except TimeoutError:
                continue
            self._session.vent_paa_loading()
            try:
                i, _ = self._session.vent_paa_en_af(
                    [(bs.REDIGER_KNAP, bf.BTM), (bs.GEM_KNAP, bf.BTM)], 10_000
                )
            except TimeoutError:
                continue
            if i == 0:
                return True  # Rediger-knappen vises, når fakturaen er gemt

        fejl = " ".join(self._session.laes_fejlbeskeder())
        if FINDES_ALLEREDE in fejl:
            return False
        raise OESFejl(f"Fejl kunne ikke oprette fakturalinje\n{fejl}".strip())
