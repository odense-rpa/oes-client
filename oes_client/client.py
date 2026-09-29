"""Samlet indgang til ØS Indsigt // Single entry point to ØS Indsigt."""

from playwright.sync_api import Playwright

from .bilag import BilagClient
from .brugere import BrugerClient
from .session import OESSession


class OESClient:
    """Logger ind i ØS og giver adgang til områderne.

    Eksempel:
        with OESClient(base_url, username, password) as oes:
            oes.bilag.udsoeg_bilag(...)
            oes.brugere.fremsoeg_bruger("ABC")
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        headless: bool = False,
        playwright: Playwright | None = None,
    ):
        self.session = OESSession(base_url, username, password, headless, playwright)
        self.bilag = BilagClient(self.session)
        self.brugere = BrugerClient(self.session)

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
