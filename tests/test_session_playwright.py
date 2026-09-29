"""Offline test af delt Playwright-instans // Offline test of a shared Playwright instance.

Starter rigtige browsere, men logger ikke ind: _login erstattes, så ØS ikke kontaktes.
"""

import pytest
from playwright.sync_api import sync_playwright

from oes_client.session import OESSession


@pytest.fixture(autouse=True)
def uden_login(monkeypatch):
    monkeypatch.setattr(OESSession, "_login", lambda self: self._ensure_browser())


def test_uden_injektion_starter_og_stopper_egen_playwright():
    session = OESSession("", "", "", headless=True)
    assert session._playwright is not None
    session.close()
    assert session._playwright is None


def test_delt_playwright_giver_hver_session_sin_browser():
    with sync_playwright() as pw:
        a = OESSession("", "", "", headless=True, playwright=pw)
        b = OESSession("", "", "", headless=True, playwright=pw)
        assert a._browser is not b._browser

        # den delte instans overlever, at én session lukkes
        a.close()
        b.page.goto("about:blank")
        pw.chromium.launch(headless=True).close()
        b.close()
