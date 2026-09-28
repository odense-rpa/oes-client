"""Playwright-klient til ØS Indsigt // Playwright client for ØS Indsigt.

Brug:
    from oes_client import OESClient

    with OESClient(base_url, username, password) as oes:
        oes.bilag.udsoeg_bilag(...)
"""

from .bilag import BilagClient
from .bilag_xml import parse_konteringslinjer
from .brugere import BrugerClient
from .client import OESClient
from .exceptions import BilagIkkeFundet, OESFejl
from .session import OESSession

__all__ = [
    "BilagClient",
    "BilagIkkeFundet",
    "BrugerClient",
    "OESClient",
    "OESFejl",
    "OESSession",
    "parse_konteringslinjer",
]
