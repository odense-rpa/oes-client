from .selectors import LoginSelectors as ls
from .selectors import OESSelectors as oss
from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Page,
    Error as PlaywrightError
)
import logging



class OESClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url or "about:blank"
        self.username = username or ""
        self.password = password or ""

        self._playwright: Playwright | None = None
        self._browser = None
        self._context = None
        self._page: Page | None = None

        self._login()

    def _ensure_browser(self) -> None:
        if self._page is not None:
            return

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=False,
            args=[
             "--force-renderer-accessibility",
             "--new-window"
            ]
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
            self._page.wait_for_selector(ls.KOMMUNE_EMAIL, timeout=3000)
            self._page.fill(ls.KOMMUNE_EMAIL, self.username)
            self._page.click(ls.NAESTE_BTN)
            
            self._page.wait_for_selector(ls.PASSWORD_FIELD, timeout=3000)
            self._page.fill(ls.PASSWORD_FIELD, self.password)
            self._page.click(ls.LOGIN_BTN)
        except: 
            self.logger.debug("login failed")

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

        bruger_id = (bruger_id or self.bruger_id or "").strip()
        if not bruger_id:
            raise ValueError("A valid user id must be provided to fremsoeg_bruger")
        

        self._page.wait_for_load_state("domcontentloaded")

        # håndtering af iframe med flere frames vha for loop
        frame = None
        for _ in range(20):  # retry loop (max ~2 sek)
            frame = self._page.frame(name="midt")
            if frame:
                print(frame)
                break
            self._page.wait_for_timeout(100)
        if not frame:
            raise Exception("Frame 'midt' not found")
        
        # søg på bruger 
        try:
            bruger_input = frame.locator(oss.BRUGER_ID)
            bruger_input.wait_for(state="visible", timeout=10000)
            bruger_input.fill(bruger_id)
            bruger_input.press("Enter")

        except PlaywrightError:
            raise ValueError(f"ingen bruger fundet med id {bruger_id}")
        



    def slet_bruger(self):
        pass