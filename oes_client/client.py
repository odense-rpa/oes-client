from .selectors import LoginSelectors as ls
from .selectors import OESSelectors as oss
from .selectors import OESCommands as osc
from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Page,
    Frame,
    Error as PlaywrightError,
    TimeoutError,
)
import logging


class OESClient:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url or "about:blank"
        self.username = username or ""
        self.password = password or ""

        self._playwright: Playwright | None = None
        self._browser = None
        self._context = None
        self._page: Page | None = None
        self._frame: Frame | None = None

        self._login()

    def _ensure_browser(self) -> None:
        if self._page is not None:
            return

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=False, args=["--force-renderer-accessibility", "--new-window"]
        )

        self._context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            accept_downloads=False,
            ignore_https_errors=True,
            locale="da-DK",
            http_credentials={"username": self.username, "password": self.password},
        )
        self._page = (
            self._context.pages[0] if self._context.pages else self._context.new_page()
        )

    def _login(self):
        self._ensure_browser()
        if self._page is None:
            return None

        self._page.goto(self.base_url, wait_until="domcontentloaded")
        print(self._page.url)
        self._page.wait_for_timeout(5000)

        try:
            self._page.wait_for_selector(ls.KOMMUNE_EMAIL, timeout=2000)
            self._page.fill(ls.KOMMUNE_EMAIL, self.username)
            self._page.click(ls.NAESTE_BTN)

            self._page.wait_for_selector(ls.PASSWORD_FIELD, timeout=2000)
            self._page.fill(ls.PASSWORD_FIELD, self.password)
            self._page.click(ls.LOGIN_BTN)

        except Exception as e:
            self.logger.error(f"[login] Failed: {e}")
            raise

        return self._page

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
        self._page = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def fremsoeg_bruger(self, bruger_id: str):
        self._ensure_browser()

        if self._page is None:
            return None

        bruger_id = (bruger_id or self.bruger_id or "").upper().strip()
        if not bruger_id:
            raise ValueError("A valid user id must be provided to fremsoeg_bruger")

        self._page.wait_for_load_state("domcontentloaded")

        # håndtering af iframe med flere frames vha for loop  // handling of iframe with several framesets with a "for loop"
        frame = None
        for _ in range(20):  # retry loop
            frame = self._page.frame(name="midt")
            if frame:
                print(frame)
                self._frame = frame  # gem frame til de næste metoder
                break
            self._page.wait_for_timeout(2000)
        if not frame:
            raise Exception("Frame 'midt' not found")

        # søg på bruger // search for user
        try:
            bruger_input = frame.locator(oss.BRUGER_ID)
            bruger_input.wait_for(state="visible", timeout=3000)
            bruger_input.fill(bruger_id)
            bruger_input.press(osc.VIS_BRUGER)
            frame.locator(oss.BRUGER_DETALJER_OVERSKRIFT).wait_for(timeout=3000)
        except Exception as e:
            raise Exception(
                f"[fremsoeg_bruger] søgning fejlede"
            ) from e

        # valider rigtige brugerdetaljer // validate correct userdetails
        bruger_detaljer_id = self._frame.locator(oss.BRUGER_DETALJER_ID).text_content()
        if bruger_detaljer_id != bruger_id:
           raise AssertionError(
               f"[fremsoeg_bruger] Forventede bruger '{bruger_id}', "
               f"men fandt '{bruger_detaljer_id}'"
           )


    def _slet_i_bruger_fane(self):
        # håndter sletning i bogføringskasser // handle deletion in accounting fields
        kasser = [
            oss.KASSE_ET,
            oss.KASSE_TO,
            oss.KASSE_TRE,
            oss.KASSE_FIRE,
            oss.KASSE_FEM,
            oss.KASSE_SEKS,
        ]

        for kasse in kasser:
            try:
                felt = self._frame.locator(kasse)

                value = felt.input_value()

                if value.strip():  # tjekker at der er tekst
                    felt.fill("")

            except Exception as e:
                raise ValueError(f"Problem med {kasse}: {e}")

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
        afdeling_slet_raekke = self._frame.locator(oss.AFDELINGSNUMMER_TABLE_SLET)
        while afdeling_slet_raekke.count() > 0:
            afdeling_slet_raekke.click()
            self._page.wait_for_timeout(2000)
            afdeling_fra = self._frame.locator(oss.AFDELINGSNUMMER_TABLE_FRA).input_value()
            afdeling_til = self._frame.locator(oss.AFDELINGSNUMMER_TABLE_TIL).input_value()
            if afdeling_fra == "" + afdeling_til == "":
                break

    def _slet_i_institution_fane(self):
        self._frame.click(oss.INSTITUTION_FANE)
        self._frame.wait_for_selector(oss.INSTITUTION_TABLE, timeout=2000)

        # slet linje så længe slet knappen findes // delete line as long as delete btn exists
        institution_slet_raekke = self._frame.locator(oss.INSTITUTION_TABLE_SLET)
        while institution_slet_raekke.count() > 0:
            institution_slet_raekke.click()
            self._page.wait_for_timeout(2000)
            institution_fra = self._frame.locator(oss.INSTITUTION_TABLE_FRA).input_value()
            institution_til = self._frame.locator(oss.INSTITUTION_TABLE_TIL).input_value()
            if institution_fra == "" + institution_til == "":
                break


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

        assert_bruger_spaerret = self._frame.locator(oss.BRUGER_SPAERRET_EFTER_REDIGERING).text_content()
        if assert_bruger_spaerret != "J   (Bruger er spærret administativt)" and assert_bruger_spaerret != "J":
           raise AssertionError(
                f"[slet_bruger] Forventede 'J' i 'bruger spærret', "
                f"men fandt '{assert_bruger_spaerret}'"
                f"fejl i [slet_bruger]"
           )

        self._page.click(oss.OES_LOGO)
        self._page.wait_for_timeout(3000)