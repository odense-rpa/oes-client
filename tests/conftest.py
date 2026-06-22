import pytest
import os

from oes_client.client import OESClient


@pytest.fixture
def oes_client():
    return OESClient(
        base_url=os.getenv("BASE_URL", "about:blank"),
        username=os.getenv("USERNAME", ""),
        password=os.getenv("PASSWORD", ""),
    )

@pytest.fixture
def test_bruger_id():
    return os.getenv("TEST_BRUGER_ID")
    

