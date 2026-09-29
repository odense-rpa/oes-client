"""Browsersession til ØS Indsigt // Browser session for ØS Indsigt.

OESSession ejer browseren, login og de fælles hjælpere (frames, ventetider, navigation,
fejlbeskeder), som områdeklienterne (bilag, brugere, ...) bruger.
"""

import logging
import re
import time
from urllib.parse import urlsplit

from playwright.sync_api import (
    BrowserContext,
    Dialog,
    Error,
    Frame,
    Locator,
    Page,
    Playwright,
    TimeoutError,
    sync_playwright,
)

from .selectors import BilagFrames as bf
from .selectors import BilagSelectors as bs
from .selectors import LoginSelectors as ls

# interval for polling af ØS // polling interval for ØS
POLL_MS = 100

INGEN_RESULTATER = "der passede til de indtastede søgekriterier"


class OESSession:
    """Én browser og ét login, delt af alle områdeklienter."""

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        headless: bool = False,
        playwright: Playwright | None = None,
    ):
        """playwright: en delt Playwright-instans. Er den None, starter sessionen sin
        egen og stopper den igen ved close(). En delt instans stoppes aldrig her.
        // a shared Playwright instance. If None, the session starts and stops its own.
        """
        self.base_url = base_url or "about:blank"
        self.username = username or ""
        self.password = password or ""
        self.headless = headless

        self._playwright: Playwright | None = playwright
        self._ejer_playwright = playwright is None
        self._browser = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._root = self._mod_core_root(self.base_url)

        # ryd op hvis login fejler, så Playwright ikke efterlades kørende
        # // clean up if login fails so Playwright is not left running
        try:
            self._login()
        except Exception:
            self.close()
            raise
        self.page.on("dialog", self._haandter_dialog)

    # ------------------------------ Browser og login // Browser and login -------------

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("ØS-sessionen er lukket")
        return self._page

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            raise RuntimeError("ØS-sessionen er lukket")
        return self._context

    @property
    def root(self) -> str:
        """ØS' rod-URL, fx https://odensetest.osi-local.dk/mod-core."""
        return self._root

    @staticmethod
    def _mod_core_root(base_url: str) -> str:
        # fx https://odensetest.osi-local.dk/mod-core - virker både på test og prod
        # // e.g. https://odensetest.osi-local.dk/mod-core - works on test and prod
        if "/mod-core" in base_url:
            return base_url[: base_url.index("/mod-core") + len("/mod-core")]
        parts = urlsplit(base_url)
        return f"{parts.scheme}://{parts.netloc}/mod-core"

    def _ensure_browser(self) -> None:
        if self._page is not None:
            return

        if self._playwright is None:
            self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=["--force-renderer-accessibility", "--new-window"],
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

    def _login(self) -> None:
        self._ensure_browser()

        self.page.goto(self.base_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(5000)

        try:
            self.page.wait_for_selector(ls.KOMMUNE_EMAIL, timeout=2000)
            self.page.fill(ls.KOMMUNE_EMAIL, self.username)
            self.page.click(ls.NAESTE_BTN)

            self.page.wait_for_selector(ls.PASSWORD_FIELD, timeout=2000)
            self.page.fill(ls.PASSWORD_FIELD, self.password)
            self.page.click(ls.LOGIN_BTN)

        except Exception as e:
            self.logger.error(f"[login] Failed: {e}")
            raise

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        # en delt Playwright-instans ejes af kalderen og stoppes ikke her
        # // a shared Playwright instance is owned by the caller and not stopped here
        if self._playwright is not None and self._ejer_playwright:
            self._playwright.stop()
            self._playwright = None
        self._page = None

    def _haandter_dialog(self, dialog: Dialog) -> None:
        self.logger.warning(f"[dialog] {dialog.type}: {dialog.message}")
        dialog.accept()

    # ------------------------------ Fælles hjælpere // Shared helpers -----------------

    def soeg_frame(
        self,
        selector: str,
        frame_pattern: str | None = None,
        has_text: str | re.Pattern | None = None,
    ) -> Frame | None:
        """Finder den frame der indeholder selector (ét gennemløb)."""
        regex = re.compile(frame_pattern) if frame_pattern else None
        # nyeste frames først, da ØS kan have gamle faner liggende
        # // newest frames first, ØS may keep old tabs around
        for frame in reversed(self.page.frames):
            if regex and not regex.search(frame.url):
                continue
            try:
                if frame.locator(selector, has_text=has_text).count() > 0:
                    return frame
            except Error:
                continue  # frame blev fjernet undervejs // frame detached
        return None

    def vent_paa_en_af(
        self, muligheder: list[tuple[str, str | None]], timeout: float = 30_000
    ) -> tuple[int, Frame]:
        """Venter på den første af (selector, frame_pattern) der findes."""
        deadline = time.monotonic() + timeout / 1000
        while True:
            for i, (selector, frame_pattern) in enumerate(muligheder):
                frame = self.soeg_frame(selector, frame_pattern)
                if frame is not None:
                    return i, frame
            if time.monotonic() > deadline:
                raise TimeoutError(f"Fandt ingen af {[m[0] for m in muligheder]}")
            self.page.wait_for_timeout(POLL_MS)

    def frame_med(
        self,
        selector: str,
        frame_pattern: str | None = None,
        timeout: float = 30_000,
        has_text: str | re.Pattern | None = None,
    ) -> Frame:
        """Venter på og returnerer den frame der indeholder selector."""
        deadline = time.monotonic() + timeout / 1000
        while True:
            frame = self.soeg_frame(selector, frame_pattern, has_text)
            if frame is not None:
                return frame
            if time.monotonic() > deadline:
                raise TimeoutError(f"Fandt ikke '{selector}' i ØS")
            self.page.wait_for_timeout(POLL_MS)

    def klik(
        self, selector: str, frame_pattern: str | None = None, timeout: float = 30_000
    ) -> Locator:
        knap = self.frame_med(selector, frame_pattern, timeout).locator(selector).first
        knap.click()
        return knap

    def vent_paa_genindlaesning(self, locator: Locator, timeout: float) -> None:
        """Venter til elementet er fjernet fra DOM'en, fx fordi framen genindlæses."""
        handle = locator.element_handle()
        deadline = time.monotonic() + timeout / 1000
        while time.monotonic() < deadline:
            try:
                if not handle.evaluate("e => e.isConnected"):
                    return
            except Error:
                return  # framen er genindlæst // frame reloaded
            self.page.wait_for_timeout(POLL_MS)
        raise TimeoutError("ØS genindlæste ikke siden")

    def vent_paa_loading(self, timeout: float = 60_000) -> None:
        self.page.wait_for_timeout(500)
        frame = self.soeg_frame(bs.LOADING_ANIMATION, bf.LOADING)
        if frame is None:
            return
        try:
            frame.locator(bs.LOADING_ANIMATION).first.wait_for(
                state="hidden", timeout=timeout
            )
        except TimeoutError:
            raise TimeoutError(
                "ØS loadede i meget lang tid. Måske noget er galt?"
            ) from None
        except Error:
            pass  # framen blev fjernet // frame detached

    def naviger(self, link: str) -> None:
        """Går til startsiden, logger ind via SSO hvis nødvendigt, og derefter til link."""
        for forsoeg in range(3):
            try:
                self.page.goto(f"{self._root}/#/", wait_until="domcontentloaded")
                i, frame = self.vent_paa_en_af(
                    [(bs.SSO_KNAP, None), (bs.OPSAETNING_OVERSKRIFT, None)], 30_000
                )
                if i == 0:
                    frame.locator(bs.SSO_KNAP).first.click()
                    self.frame_med(bs.OPSAETNING_OVERSKRIFT, timeout=30_000)
                self.page.goto(f"{self._root}/#/{link}", wait_until="domcontentloaded")
                return
            except Error as e:
                if forsoeg == 2:
                    raise
                self.logger.warning(f"[naviger] forsøg {forsoeg + 1} fejlede: {e}")

    def laes_fejlbeskeder(self) -> list[str]:
        """Returnerer ØS' fejlbeskeder, eller [] hvis der ingen er."""
        try:
            frame = self.frame_med(bs.FEJLLISTE, timeout=5_000)
        except TimeoutError:
            return []
        tekster = frame.locator(bs.FEJLLISTE).first.locator("option").all_inner_texts()
        return [t.strip() for t in tekster if t.strip()]
