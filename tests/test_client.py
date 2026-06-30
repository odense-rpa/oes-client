import pytest
from oes_client.selectors import OESCommands as osc
from oes_client.selectors import OESSelectors as oss



def test_login(oes_client):
    oes_client._login()
    breakpoint = ""


def test_failed_login(oes_client):
    fake_test_mail = "hovhovhov@odense.dk"
    try:
        oes_client._login(fake_test_mail)
    except Exception as e:
        pytest.fail(f"login raised unexpected exception as {e}")


def test_fremsoeg_bruger(oes_client, test_bruger_id):
    try:
        oes_client.fremsoeg_bruger(test_bruger_id)
    except Exception as e:
        pytest.fail(f"fremsoeg_bruger raised unexpected exception: {e}")

# virker lige nu med debug, men ikke med fuld speed
def test_slet_bruger_uden_at_gemme(oes_client, test_bruger_id):
    oes_client.fremsoeg_bruger(test_bruger_id)
    oes_client.slet_bruger()
