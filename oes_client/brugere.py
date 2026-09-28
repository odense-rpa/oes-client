"""Brugeradministration i ØS Indsigt // User administration in ØS Indsigt."""

from playwright.sync_api import Frame, Page, TimeoutError

from .exceptions import OESFejl
from .selectors import OESCommands as osc
from .selectors import OESSelectors as oss
from .session import OESSession

# link til brugeradministration (fra Blue Prism "NV: Brugeroversigt")
# // link to user admin (from Blue Prism "NV: Brugeroversigt")
BRUGEROVERSIGT = "administration/sikkerhed/bruger"


class BrugerClient:
    """Brugerhandlinger i ØS Indsigt // User actions in ØS Indsigt.

    Oprettes af OESClient og tilgås som oes.brugere.
    """

    def __init__(self, session: OESSession):
        self._session = session
        self._frame: Frame | None = None

    @property
    def _page(self) -> Page:
        return self._session.page

    def fremsoeg_bruger(self, bruger_id: str) -> None:
        """Fremsøger en bruger og husker brugerens frame til slet_bruger."""
        bruger_id = (bruger_id or "").upper().strip()
        if not bruger_id:
            raise ValueError(
                "Et gyldigt bruger_id skal angives for at fremsøge en bruger"
            )

        # gå direkte til brugeradministration i stedet for at afhænge af startsiden
        # // go straight to user admin instead of relying on the start page
        self._session.naviger(BRUGEROVERSIGT)
        self._page.wait_for_timeout(3000)

        # frame med brugersøgningen (tidligere frame "midt")
        # // frame with the user search (previously frame "midt")
        frame = self._session.frame_med(oss.BRUGER_ID, timeout=40_000)
        self._frame = frame  # gem frame til de næste metoder

        # søg på bruger // search for user
        try:
            bruger_input = frame.locator(oss.BRUGER_ID)
            bruger_input.wait_for(state="visible", timeout=3000)
            bruger_input.fill(bruger_id)
            bruger_input.press(osc.VIS_BRUGER)
            frame.locator(oss.BRUGER_DETALJER_OVERSKRIFT).wait_for(timeout=3000)
        except Exception as e:
            raise ValueError("Kunne ikke fremsøge bruger") from e

        # valider rigtige brugerdetaljer // validate correct userdetails
        bruger_detaljer_id = self._frame.locator(oss.BRUGER_DETALJER_ID).text_content()
        if bruger_detaljer_id != bruger_id:
            raise OESFejl(
                f"Forventede bruger '{bruger_id}', men fandt '{bruger_detaljer_id}'"
            )

    def _slet_i_bruger_fane(self):
        # alm. felter der skal blankes:

        # håndter sletning i bogføringskasser // handle deletion in accounting fields
        felter = [
            oss.KASSE_ET,
            oss.KASSE_TO,
            oss.KASSE_TRE,
            oss.KASSE_FIRE,
            oss.KASSE_FEM,
            oss.KASSE_SEKS,
            oss.CPR_NUMMER_VIS,
            oss.AD_USER_ID,
            oss.AFDELING_NUMMER,
            oss.INSTITUTION_NUMMER,
            oss.SD_USER_ID,
        ]

        for kasse in felter:
            felt = self._frame.locator(kasse)
            value = felt.input_value()

            if value.strip():  # tjekker at der er tekst
                felt.fill("")

        # skriv J i 'bruger spærret' // write J in 'user blocked'
        bruger_spaerret_input = self._frame.locator(oss.BRUGER_SPAERRET)
        bruger_spaerret_input.fill("J")

        # tjek betalingsgodkendelse og fjern check // assert the payment approval and remove check
        betaling_godkendt_box = self._frame.locator(oss.BETALING_GODKENDT)
        if betaling_godkendt_box.is_checked():
            betaling_godkendt_box.click()

        self._frame.locator(oss.ADGANGSGRUPPE_TABLE)
        adgangsgruppe_slet_raekke = self._frame.locator(oss.ADGANGSGRUPPE_TABLE_SLET)
        while adgangsgruppe_slet_raekke.count() > 0:
            adgangsgruppe_slet_raekke.click()
            self._page.wait_for_timeout(2000)

    def _slet_i_afdeling_fane(self):
        self._frame.click(oss.AFDELING_FANE)
        self._frame.wait_for_selector(oss.AFDELINGSNUMMER_TABLE, timeout=2000)

        # slet linje så længe slet knappen findes // delete line as long as delete btn exists
        # Håndterer sletning med tilfælde af flere rækker // Handle deletion with cases of multiple rows
        for attempt in range(5):
            try:
                afdeling_slet_raekke = self._frame.locator(
                    f"{oss.AFDELINGSNUMMER_TABLE_SLET}, {oss.AFDELINGSNUMMER_TABLE_SLET_TO}"
                )
                self._page.wait_for_timeout(2000)
                afdeling_fra = self._frame.locator(
                    oss.AFDELINGSNUMMER_TABLE_FRA
                ).input_value()
                afdeling_til = self._frame.locator(
                    oss.AFDELINGSNUMMER_TABLE_TIL
                ).input_value()
                if afdeling_fra == "" and afdeling_til == "":
                    break
                afdeling_slet_raekke.first.click()
            except Exception as e:
                raise ValueError("Kunne ikke slette afdelingsnummer") from e

    def _slet_i_institution_fane(self):
        self._frame.click(oss.INSTITUTION_FANE)
        self._frame.wait_for_selector(oss.INSTITUTION_TABLE, timeout=2000)

        # slet linje så længe slet knappen findes // delete line as long as delete btn exists
        # Håndterer sletning med tilfælde af flere rækker // Handle deletion with cases of multiple rows
        for attempt in range(5):
            try:
                institution_slet_raekke = self._frame.locator(
                    f"{oss.INSTITUTION_TABLE_SLET}, {oss.INSTITUTION_TABLE_SLET_TO}"
                )
                self._page.wait_for_timeout(2000)
                institution_fra = self._frame.locator(
                    oss.INSTITUTION_TABLE_FRA
                ).input_value()
                institution_til = self._frame.locator(
                    oss.INSTITUTION_TABLE_TIL
                ).input_value()
                if institution_fra == "" and institution_til == "":
                    break
                institution_slet_raekke.first.click()
            except Exception as e:
                raise ValueError("Kunne ikke slette institutionnummer") from e

    def slet_bruger(self):
        for attempt in range(3):
            try:
                with self._page.expect_response(lambda r: "tom.html" in r.url):
                    self._page.bring_to_front()
                    self._frame.locator("body").click()
                    self._page.keyboard.press(osc.REDIGER_BRUGER)
                break
            except TimeoutError:
                if attempt == 2:
                    raise

        self._frame.wait_for_selector(oss.KASSE_ET, state="visible")

        self._slet_i_bruger_fane()
        self._slet_i_afdeling_fane()
        self._slet_i_institution_fane()

        self._page.keyboard.press(osc.GEM_BRUGER)
        self._page.wait_for_timeout(2000)

        assert_bruger_spaerret = " ".join(
            self._frame.locator(oss.BRUGER_SPAERRET_EFTER_REDIGERING)
            .text_content()
            .split()
        )
        if (
            assert_bruger_spaerret != "J (Bruger er spærret administativt)"
            and assert_bruger_spaerret != "J"
        ):
            raise ValueError(
                f"Forventede 'J' i 'bruger spærret', men fandt '{assert_bruger_spaerret}'"
            )

        self._page.goto(f"{self._session.root}/#")
        self._page.wait_for_timeout(3000)
