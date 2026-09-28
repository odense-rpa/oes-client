import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from oes_client import OESClient

# testindstillinger læses eksplicit fra .env i projektroden
# // test settings are loaded explicitly from .env in the project root
load_dotenv(Path(__file__).parent.parent / ".env")


def _oes_login() -> dict:
    """Login-indstillinger til ØS - springer testen over hvis de mangler."""
    manglende = [
        navn
        for navn in ("BASE_URL", "OES_USERNAME", "OES_PASSWORD")
        if not os.getenv(navn)
    ]
    if manglende:
        pytest.skip(f"Mangler i .env: {', '.join(manglende)}")
    return {
        "base_url": os.environ["BASE_URL"],
        "username": os.environ["OES_USERNAME"],
        "password": os.environ["OES_PASSWORD"],
    }


@pytest.fixture(scope="session")
def oes():
    """Én indlogget OESClient for hele testkørslen // One login per test run."""
    client = OESClient(**_oes_login(), headless=False)
    yield client
    client.close()


@pytest.fixture
def tillad_skriv():
    """Springer tests over der ændrer data i ØS, medmindre OES_ALLOW_WRITE=1."""
    if os.getenv("OES_ALLOW_WRITE") != "1":
        pytest.skip("ændrer data i ØS - sæt OES_ALLOW_WRITE=1")


@pytest.fixture
def test_bruger_id():
    bruger_id = os.getenv("TEST_BRUGER_ID")
    if not bruger_id:
        pytest.skip("TEST_BRUGER_ID er ikke sat")
    return bruger_id


@pytest.fixture
def test_bilagsid():
    bilagsid = os.getenv("TEST_BILAGSID")
    if not bilagsid:
        pytest.skip("TEST_BILAGSID er ikke sat")
    return bilagsid


@pytest.fixture
def test_afdelingsnummer():
    afdelingsnummer = os.getenv("TEST_AFDELINGSNUMMER")
    if not afdelingsnummer:
        pytest.skip("TEST_AFDELINGSNUMMER er ikke sat")
    return afdelingsnummer
